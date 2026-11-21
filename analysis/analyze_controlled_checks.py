"""Valida pruebas controladas y genera tablas sin editar datos crudos."""

import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import statistics

if __package__:
    from .verify_lamport import verify
    from .summarize_concurrency import tex
else:
    from verify_lamport import verify
    from summarize_concurrency import tex


def read_case(directory):
    directory = Path(directory)
    seen = set()
    for line in (directory / "SHA256SUMS").read_text().splitlines():
        digest, name = line.split("  ", 1)
        if Path(name).name != name or name in seen:
            raise ValueError("Manifiesto ambiguo")
        seen.add(name)
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Hash incorrecto: {directory / name}")
    result = json.loads((directory / "result.json").read_text())
    if result["run_id"] != directory.name:
        raise ValueError("El resultado no corresponde a la carpeta del caso")
    paths = [directory / f"events_{name}.csv" for name in result["nodes"]]
    if not {p.name for p in paths} | {"result.json"} <= seen or not result["ok"]:
        raise ValueError("Captura incompleta o no aprobada")
    if len({n["pid"] for n in result["nodes"].values()}) != len(paths):
        raise ValueError("Los nodos no tienen PID distintos")
    report = verify(paths)
    events = []
    for path in paths:
        with path.open(newline="", encoding="utf-8") as stream:
            events.extend(csv.DictReader(stream))
    mechanism = "TCP" if result["mechanism"] == "tcp" else "gRPC"
    if any(e["corrida"] != result["run_id"] or e["mecanismo"] != mechanism for e in events):
        raise ValueError("Los CSV no corresponden al caso")
    if result["mode"] == "propagation":
        count = result["node_count"]
        if (not report["valido"] or len(events) != 4 * (count - 1) or
                len(result["commands"]) != count - 1 or result["chain_elapsed_ns"] <= 0 or
                not all(c["ok"] for c in result["commands"])):
            raise ValueError("Cadena causal incompleta")
        names = list(result["nodes"])
        expected_pairs = list(zip(names, names[1:]))
        if [(c["origin"], c["destination"]) for c in result["commands"]] != expected_pairs:
            raise ValueError("Los comandos no forman la cadena declarada")
        sends = [e for e in events if e["evento"] == "envio_solicitud"]
        if sorted((e["origen"], e["destino"]) for e in sends) != sorted(expected_pairs):
            raise ValueError("Los CSV no forman la cadena declarada")
        for name in names[1:-1]:
            incoming = next(e for e in events if e["nodo"] == name and e["evento"] == "recepcion_solicitud")
            outgoing = next(e for e in sends if e["nodo"] == name)
            if int(outgoing["secuencia"]) <= int(incoming["secuencia"]):
                raise ValueError("El siguiente salto no es posterior a la recepción")
        return {"mecanismo": mechanism, "nodos": count, "repeticion": result["repetition"],
                "intercambios": count - 1, "eventos": len(events),
                "duracion_ms": result["chain_elapsed_ns"] / 1e6, "fuente": str(directory)}
    if result["mode"] != "failure":
        raise ValueError("Modo desconocido")
    expected = result["expected_orphan"]
    # Se exige el informe completo exacto: cualquier error adicional invalida el caso.
    # El verificador estricto NO se presenta como aprobado para una captura incompleta.
    expected_error = f"{(mechanism, result['run_id'], expected)}: solicitud/acuse incompleto o duplicado"
    orphan = [e for e in events if e["id_mensaje"] == expected]
    commands = result["commands"]
    if (report["errores"] != [expected_error] or len(orphan) != 1 or
            orphan[0]["evento"] != "envio_solicitud" or
            (orphan[0]["origen"], orphan[0]["destino"]) != ("nodo-B", "nodo-C") or
            len(commands) != 4 or not commands[0]["ok"] or not commands[1]["ok"] or
            commands[2]["ok"] or commands[2].get("phase") != "send" or not commands[3]["ok"] or
            commands[2]["clock_after"] != commands[2]["clock_before"] + 1 or
            int(orphan[0]["reloj"]) != commands[2]["clock_after"] or
            result["killed"]["exitcode"] in (None, 0) or len(events) != 13):
        raise ValueError("La captura no demuestra únicamente el fallo controlado previsto")
    return {"mecanismo": mechanism, "solicitudes_completas": 3, "intento_fallido": 1,
            "envios_sin_recepcion": len(orphan), "eventos": len(events),
            "reloj_antes": commands[2]["clock_before"], "reloj_despues": commands[2]["clock_after"],
            "error": commands[2].get("status") or commands[2]["error"],
            "canal_sano_posterior": commands[3]["ok"], "fuente": str(directory)}


def percentile95(values):
    values = sorted(values)
    position = 0.95 * (len(values) - 1)
    low = int(position)
    return values[low] + (values[min(low + 1, len(values) - 1)] - values[low]) * (position - low)


def write_csv(path, rows):
    if not rows:
        return
    with path.open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyze(source, output):
    source, output = Path(source), Path(output)
    if (source / "SHA256SUMS").exists():
        for line in (source / "SHA256SUMS").read_text().splitlines():
            digest, name = line.split("  ", 1)
            relative = Path(name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Ruta inválida en manifiesto agregado")
            if hashlib.sha256((source / relative).read_bytes()).hexdigest() != digest:
                raise ValueError(f"Hash agregado incorrecto: {name}")
    environment = json.loads((source / "environment.json").read_text())
    config = environment["configuration"]
    mechanisms = ("tcp", "grpc") if config["mechanism"] == "both" else (config["mechanism"],)
    expected = set()
    for mechanism in mechanisms:
        if config["mode"] in ("all", "failure"):
            expected.add(f"failure-{mechanism}-n3-r01")
        if config["mode"] in ("all", "propagation"):
            for count in config["nodes"]:
                for repetition in range(1, config["repetitions"] + 1):
                    expected.add(f"propagation-{mechanism}-n{count}-r{repetition:02d}")
    cases = sorted(p for p in source.iterdir() if p.is_dir())
    if {p.name for p in cases} != expected or any(not (p / "result.json").is_file() for p in cases):
        raise ValueError("Faltan casos previstos o hay carpetas no declaradas; no omitir intentos fallidos")
    if not cases:
        raise ValueError("No hay casos completos")
    measurements, failures = [], []
    for directory in cases:
        row = read_case(directory)
        (measurements if "duracion_ms" in row else failures).append(row)
    groups = defaultdict(list)
    for row in measurements:
        groups[row["mecanismo"], row["nodos"]].append(row["duracion_ms"])
    summary = []
    for (mechanism, count), values in sorted(groups.items()):
        summary.append({"mecanismo": mechanism, "nodos": count, "repeticiones": len(values),
                        "intercambios_por_cadena": count - 1, "media_ms": statistics.mean(values),
                        "mediana_ms": statistics.median(values),
                        "desviacion_ms": statistics.stdev(values) if len(values) > 1 else 0,
                        "p95_ms": percentile95(values)})
    output.mkdir(parents=True, exist_ok=False)
    write_csv(output / "cadenas.csv", measurements)
    write_csv(output / "propagacion_resumen.csv", summary)
    write_csv(output / "fallos.csv", failures)
    table = [r"\begin{tabular}{llrrrr}", r"\toprule",
             r"Mecanismo & Nodos & Corridas & Media (ms) & Mediana (ms) & P95 (ms) \\", r"\midrule"]
    for row in summary:
        table.append(f"{row['mecanismo']} & {row['nodos']} & {row['repeticiones']} & "
                     f"{row['media_ms']:.3f} & {row['mediana_ms']:.3f} & {row['p95_ms']:.3f}" + r" \\")
    table += [r"\bottomrule", r"\end{tabular}"]
    (output / "propagacion.tex").write_text("\n".join(table) + "\n")
    failure_table = [r"\begin{tabular}{lrrrrr}", r"\toprule",
                     r"Mecanismo & Completas & Fallidas & Huérfanas & $L_B$ antes & $L_B$ después \\",
                     r"\midrule"]
    for row in failures:
        failure_table.append(" & ".join(tex(row[key]) for key in
                             ("mecanismo", "solicitudes_completas", "intento_fallido",
                              "envios_sin_recepcion", "reloj_antes", "reloj_despues")) + r" \\")
    failure_table += [r"\bottomrule", r"\end{tabular}"]
    (output / "fallos.tex").write_text("\n".join(failure_table) + "\n")
    lines = ["# Pruebas controladas: caída y recorrido causal", "",
             "Resultados generados desde CSV y mediciones reales con hashes comprobados.",
             "No son las 2000 mediciones RTT ni una medición de sincronización física.", "",
             "## Caída", ""]
    for row in failures:
        lines.append(f"- {row['mecanismo']}: {row['solicitudes_completas']} solicitudes completas, "
                     f"{row['intento_fallido']} intento fallido, {row['envios_sin_recepcion']} envío "
                     f"sin recepción; reloj {row['reloj_antes']}→{row['reloj_despues']}; "
                     f"error {row['error']}; canal sano posterior: {row['canal_sano_posterior']}.")
    lines += ["", "La verificación estricta de intercambios completos rechaza ese envío huérfano,",
              "como corresponde. La comprobación específica acepta solo ese caso previsto y exige",
              "que no exista ningún otro error. No inventa la recepción ni elimina el envío fallido.", "",
              "## Número de nodos", "",
              "Se mide completar N−1 intercambios secuenciales de una cadena causal, desde el",
              "coordinador. Incluye IPC, creación/reutilización de conexiones y acuses, no solo red.",
              "El intervalo comienza cuando todos los servidores ya están listos. Los procesos y",
              "relojes se crean de nuevo por repetición. No se afirma convergencia de los contadores.", "",
              "| Mecanismo | Nodos | Corridas | Media ms | Mediana ms | P95 ms |",
              "|---|---:|---:|---:|---:|---:|"]
    for row in summary:
        lines.append(f"| {row['mecanismo']} | {row['nodos']} | {row['repeticiones']} | "
                     f"{row['media_ms']:.3f} | {row['mediana_ms']:.3f} | {row['p95_ms']:.3f} |")
    lines += ["", "La cantidad de saltos varía con N: esta prueba describe esa topología y ese",
              "procedimiento. No aísla el efecto del transporte ni garantiza crecimiento lineal.",
              "El P95 utiliza interpolación lineal sobre el ordenamiento de las observaciones.",
              "Consultar environment.json para origen declarado, sistema, versiones y fecha."]
    (output / "resumen.md").write_text("\n".join(lines) + "\n")
    print("Casos validados:", len(cases), "resumen en", output)
    return measurements, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        analyze(args.source, args.output)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\nNo editar datos ni hashes para resolver la validación.\n")


if __name__ == "__main__":
    main()
