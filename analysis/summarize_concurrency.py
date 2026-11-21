"""Resume capturas reales de concurrencia sin mezclarlas con el benchmark RTT."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

if __package__:
    from .verify_lamport import verify
else:
    from verify_lamport import verify


NODES = ("nodo-A", "nodo-B", "nodo-C")


def check_hashes(directory):
    seen = set()
    for line in (directory / "SHA256SUMS").read_text(encoding="ascii").splitlines():
        digest, name = line.split("  ", 1)
        if Path(name).name != name or name in seen or len(digest) != 64:
            raise ValueError(f"Manifiesto inválido en {directory}")
        seen.add(name)
        if hashlib.sha256((directory / name).read_bytes()).hexdigest() != digest:
            raise ValueError(f"Hash incorrecto: {directory / name}")
    required = {f"events_{node}.csv" for node in NODES} | {
        "environment.json", "run_result.json", "verification.json"}
    if not required <= seen:
        raise ValueError(f"Faltan hashes obligatorios: {directory}")


def analyze_capture(directory):
    directory = Path(directory)
    check_hashes(directory)
    environment = json.loads((directory / "environment.json").read_text())
    result = json.loads((directory / "run_result.json").read_text())
    stored = json.loads((directory / "verification.json").read_text())
    report = verify([directory / f"events_{node}.csv" for node in NODES])
    if not report["valido"] or stored != report:
        raise ValueError(f"Verificación inválida o informe no reproducible: {directory}")
    if report["ejemplo_relojes_iguales"] is None:
        raise ValueError(f"Falta ejemplo con marcas iguales: {directory}")
    nodes = result.get("nodes", [])
    if (not result.get("ok") or len(nodes) != 3 or
            {n["node"] for n in nodes} != set(NODES) or
            len({n["pid"] for n in nodes}) != 3 or not all(n["ok"] for n in nodes)):
        raise ValueError(f"La ejecución no confirma tres procesos correctos: {directory}")
    events = []
    for node in NODES:
        with (directory / f"events_{node}.csv").open(newline="", encoding="utf-8") as stream:
            events.extend(csv.DictReader(stream))
    config = environment["configuration"]
    mechanism = {"tcp": "TCP", "grpc": "gRPC"}[config["mechanism"]]
    if any(r["corrida"] != config["run_id"] or r["mecanismo"] != mechanism for r in events):
        raise ValueError(f"CSV no corresponden al entorno registrado: {directory}")
    requests = sum(r["evento"] == "envio_solicitud" for r in events)
    acks = sum(r["evento"] == "recepcion_acuse" for r in events)
    if (requests != config["messages"] or acks != requests or len(events) != 4 * requests or
            sum(n["requests_sent"] for n in nodes) != requests):
        raise ValueError(f"Cantidad incompleta de solicitudes o acuses: {directory}")
    record = {"corrida": config["run_id"], "mecanismo": mechanism,
              "carga_bytes": config["size_bytes"], "solicitudes": requests,
              "acuses": acks, "eventos": len(events), "pares": report["pares_evaluados"],
              "errores_causales": len(report["errores"]), "procesos": 3,
              "fuente": str(directory)}
    witness = report["ejemplo_relojes_iguales"]
    return record, witness, environment


def tex(value):
    replacements = {"\\": r"\textbackslash{}", "_": r"\_", "%": r"\%", "&": r"\&",
                    "#": r"\#", "$": r"\$", "{": r"\{", "}": r"\}",
                    "~": r"\textasciitilde{}", "^": r"\textasciicircum{}"}
    return "".join(replacements.get(c, c) for c in str(value))


def summarize(directories, output):
    if not directories:
        raise ValueError("Se requiere al menos una captura")
    captures = [analyze_capture(p) for p in directories]
    keys = [(r[0]["mecanismo"], r[0]["corrida"]) for r in captures]
    if len(keys) != len(set(keys)):
        raise ValueError("No se debe contar dos veces una misma corrida")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    records = [capture[0] for capture in captures]
    with (output / "resumen.csv").open("x", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    table = [r"\begin{tabular}{lrrrrrr}", r"\toprule",
             r"Mecanismo & Bytes & Solicitudes & Acuses & Eventos & Pares & Errores \\",
             r"\midrule"]
    for row in records:
        table.append(" & ".join(tex(row[k]) for k in
                     ("mecanismo", "carga_bytes", "solicitudes", "acuses", "eventos", "pares",
                      "errores_causales")) + r" \\")
    table += [r"\bottomrule", r"\end{tabular}"]
    (output / "concurrencia_resumen.tex").write_text("\n".join(table) + "\n")
    witnesses = []
    for row, witness, _ in captures:
        a, b = witness["eventos"]
        witnesses.append(
            "En " + tex(row["corrida"]) + ", los eventos " + tex(a["evento"]) + " de " +
            tex(a["nodo"]) + " (secuencia " + tex(a["secuencia"]) + ", ID " +
            tex(a["id_mensaje"]) + ") y " + tex(b["evento"]) + " de " + tex(b["nodo"]) +
            " (secuencia " + tex(b["secuencia"]) + ", ID " + tex(b["id_mensaje"]) +
            ") tienen marca $L=" + tex(witness["reloj"]) + "$.")
    (output / "concurrencia_ejemplos.tex").write_text("\n\n".join(witnesses) + "\n")
    lines = ["# Resultados verificados de concurrencia", "",
             "Generado desde CSV reales; hashes y reglas de Lamport comprobados nuevamente.",
             "No son las 2000 mediciones secuenciales de RTT del benchmark.", "",
             "| Corrida | Mecanismo | Bytes | Solicitudes | Acuses | Eventos | Pares | Errores |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for row, witness, environment in captures:
        lines.append("| " + " | ".join(str(row[k]) for k in
                     ("corrida", "mecanismo", "carga_bytes", "solicitudes", "acuses", "eventos",
                      "pares", "errores_causales")) + " |")
    lines += ["", "## Método", "",
              "Tres procesos con reloj y registro por nodo; solicitudes en anillo A→B→C→A.",
              "Barreras de servidores listos, primeros envíos registrados antes de transmitir y finalización.",
              "La marca igual inicial es consecuencia de un arranque controlado, no simultaneidad física probada.",
              "No se comparan latencias ni rendimiento entre estas capturas y otros equipos.", "",
              "## Procedencia y archivos", ""]
    for row, witness, environment in captures:
        lines += [f"- `{row['fuente']}`: {environment['user']}@{environment['hostname']}; "
                  f"{environment['os']}; Python {environment['python'].split()[0]}; "
                  f"UTC {environment['utc']}. Ejemplo: reloj {witness['reloj']} entre "
                  + " y ".join(e["nodo"] for e in witness["eventos"]) + "."]
    lines += ["", "Las capturas personales, el video y la participación humana se acreditan por separado."]
    (output / "resumen_concurrencia.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Resumen reproducible generado en", output)
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("captures", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        summarize(args.captures, args.output)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\nNo se han validado resultados para el informe.\n")


if __name__ == "__main__":
    main()
