"""Genera el reporte de veinte intercambios desde capturas verificadas, sin editar datos."""

import argparse
import csv
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

if __package__:
    from .summarize_concurrency import analyze_capture, tex
else:
    from summarize_concurrency import analyze_capture, tex


def generate(grpc_capture, tcp_capture, output):
    captures = []
    for directory, expected in ((Path(grpc_capture), "gRPC"), (Path(tcp_capture), "TCP")):
        row, witness, environment = analyze_capture(directory)
        if row["mecanismo"] != expected or row["solicitudes"] != 20 or row["carga_bytes"] != 100:
            raise ValueError(f"Se requiere {expected}, veinte solicitudes y 100 bytes: {directory}")
        result = json.loads((directory / "run_result.json").read_text())
        rows = []
        for node in result["nodes"]:
            with (directory / f"events_{node['node']}.csv").open(newline="", encoding="utf-8") as stream:
                events = list(csv.DictReader(stream))
            sent = [e for e in events if e["evento"] == "envio_solicitud"]
            received = [e for e in events if e["evento"] == "recepcion_solicitud"]
            last = max(events, key=lambda e: int(e["secuencia"]))
            if int(last["reloj"]) != node["clock"] or len(sent) != node["requests_sent"]:
                raise ValueError("El estado final del nodo no coincide con su CSV")
            rows.append({"mecanismo": expected, "nodo": node["node"], "pid": node["pid"],
                         "puerto": node["port"], "solicitudes_enviadas": len(sent),
                         "destino_cliente": ", ".join(sorted({e["destino"] for e in sent})),
                         "solicitudes_recibidas": len(received),
                         "origen_servidor": ", ".join(sorted({e["origen"] for e in received})),
                         "reloj_final": node["clock"]})
        captures.append((directory, row, witness, environment, rows))
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    summaries = [capture[1] for capture in captures]
    nodes = [node for capture in captures for node in capture[4]]
    for filename, rows in (("resumen.csv", summaries), ("nodos.csv", nodes)):
        with (output / filename).open("x", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    table = [r"\begin{tabular}{lrrrrr}", r"\toprule",
             r"Mecanismo & Solicitudes & Acuses & Eventos & Pares & Errores \\", r"\midrule"]
    for row in summaries:
        table.append(" & ".join(tex(row[key]) for key in
                     ("mecanismo", "solicitudes", "acuses", "eventos", "pares", "errores_causales")) + r" \\")
    table += [r"\bottomrule", r"\end{tabular}"]
    (output / "lamport20_resumen.tex").write_text("\n".join(table) + "\n")
    examples = []
    lines = ["# Corridas de veinte intercambios: gRPC y TCP", "",
             "Reporte generado por `analysis/report_twenty_exchanges.py` a partir de CSV reales.",
             "Se recalcularon los hashes y las reglas de Lamport antes de generar los resultados.", "",
             "Los nombres son los del lanzador integrado, no los CSV acumulativos de los scripts antiguos.",
             "Veinte intercambios significa veinte solicitudes con sus acuses entre los tres nodos,",
             "no veinte solicitudes por cliente ni veinte solicitudes exclusivamente A→B.", ""]
    for directory, row, witness, environment, node_rows in captures:
        utc = datetime.fromisoformat(environment["utc"])
        local = utc.astimezone(timezone(timedelta(hours=-5)))
        mechanism = environment["configuration"]["mechanism"]
        lines += [f"## {row['mecanismo']}", "",
                  f"- Corrida: `{row['corrida']}`.",
                  f"- Inicio registrado: **{local.isoformat()} (UTC−05:00)**; UTC: `{utc.isoformat()}`.",
                  f"- Equipo: `{environment['user']}@{environment['hostname']}`; "
                  f"{environment['os']}; Python {environment['python'].split()[0]}.",
                  f"- Carga útil: {row['carga_bytes']} bytes ASCII por solicitud.",
                  f"- Resultado: {row['solicitudes']} solicitudes, {row['acuses']} acuses, "
                  f"{row['eventos']} eventos, {row['pares']} pares y {row['errores_causales']} errores causales.",
                  "", "### CSV exactos", ""]
        lines += [f"- `{(directory / ('events_' + node + '.csv')).as_posix()}`."
                  for node in ("nodo-A", "nodo-B", "nodo-C")]
        lines += ["", "### Participación de los nodos", "",
                  "| Nodo | Puerto | Cliente: solicitudes → destino | Servidor: solicitudes ← origen | Reloj final |",
                  "|---|---:|---|---|---:|"]
        for node in node_rows:
            lines.append(f"| {node['nodo']} | {node['puerto']} | {node['solicitudes_enviadas']} → "
                         f"{node['destino_cliente']} | {node['solicitudes_recibidas']} ← "
                         f"{node['origen_servidor']} | {node['reloj_final']} |")
        lines += ["", "Cada proceso actúa como servidor y cliente con el mismo reloj local.",
                  "El anillo es A→B→C→A; los acuses regresan en sentido inverso.", "",
                  f"Los tres CSV están incluidos y comprobados en `{directory.as_posix()}/SHA256SUMS`.",
                  "No se mezclan con el manifiesto de las mediciones de latencia.", "",
                  "### Comando equivalente con variables expandidas", "",
                  "Comando descriptivo de la corrida ya realizada: para repetir, elegir otro ID y carpeta.",
                  "```fish",
                  f'.venv/bin/python analysis/run_lamport_experiment.py --mechanism {mechanism} '
                  f'--run-id "{row["corrida"]}" --messages 20 --size-bytes 100 --output "{directory.as_posix()}"',
                  "```", ""]
        a, b = witness["eventos"]
        examples.append("En \\path{" + row["corrida"] + "}, " + tex(a["nodo"]) + " y " +
                        tex(b["nodo"]) + " registran eventos de envío con marca $L=" +
                        tex(witness["reloj"]) + "$; sus IDs son \\path{" + a["id_mensaje"] +
                        "} y \\path{" + b["id_mensaje"] + "}.")
    lines += ["## Método y límites", "",
              "Las barreras sincronizan servidores disponibles, primeros envíos registrados antes de",
              "transmitir y finalización. Las marcas iguales provienen de eventos reales con arranque",
              "controlado; no significan simultaneidad física exacta.", "",
              "Son pruebas funcionales independientes de las capturas de carga de 300 solicitudes y de",
              "las 2000 mediciones secuenciales de RTT. No se usan para comparar latencias.", "",
              "Las capturas y los logs asociados se documentan en `docs/EVIDENCIAS_20_INTERCAMBIOS.md`."]
    (output / "resumen.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (output / "lamport20_ejemplos.tex").write_text("\n\n".join(examples) + "\n")
    print("Reporte de veinte intercambios generado en", output)
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grpc-capture", required=True, type=Path)
    parser.add_argument("--tcp-capture", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        generate(args.grpc_capture, args.tcp_capture, args.output)
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"ERROR: {exc}\nNo editar datos ni sobrescribir capturas para resolverlo.\n")


if __name__ == "__main__":
    main()
