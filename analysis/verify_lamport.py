"""Verifica registros completos de solicitudes y acuses, sin alterar los CSV."""

import argparse
import csv
from datetime import datetime
import json
from pathlib import Path


FIELDS = {
    "mecanismo", "corrida", "nodo", "secuencia", "evento", "reloj",
    "reloj_remoto", "hora_real", "id_mensaje", "origen", "destino",
}
EVENTS = {"envio_solicitud", "recepcion_solicitud",
          "envio_acuse", "recepcion_acuse"}


def verify(paths: list[Path]) -> dict:
    errors, rows = [], []
    for path in paths:
        try:
            with path.open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                headers = reader.fieldnames or []
                if len(headers) != len(set(headers)) or not FIELDS <= set(headers):
                    errors.append(f"{path}: cabecera incompleta o duplicada")
                    continue
                count = 0
                for line, row in enumerate(reader, 2):
                    count += 1
                    try:
                        if None in row or any(row.get(k) is None for k in FIELDS):
                            raise ValueError("cantidad de columnas incorrecta")
                        if any(not row[k].strip() for k in FIELDS - {"reloj_remoto"}):
                            raise ValueError("campo obligatorio vacío")
                        if row["evento"] not in EVENTS:
                            raise ValueError("evento desconocido")
                        if row["mecanismo"] not in {"TCP", "gRPC"}:
                            raise ValueError("mecanismo desconocido")
                        for key in ("secuencia", "reloj"):
                            row[key] = int(row[key])
                            if row[key] < 1:
                                raise ValueError(f"{key} debe ser positivo")
                        receiving = row["evento"].startswith("recepcion_")
                        if receiving:
                            row["reloj_remoto"] = int(row["reloj_remoto"])
                            if row["reloj_remoto"] < 0:
                                raise ValueError("reloj remoto negativo")
                        elif row["reloj_remoto"] != "":
                            raise ValueError("envío con reloj remoto")
                        expected_node = row["destino"] if receiving else row["origen"]
                        if row["nodo"] != expected_node:
                            raise ValueError("nodo distinto del extremo del mensaje")
                        real_time = datetime.fromisoformat(row["hora_real"])
                        if real_time.utcoffset() is None:
                            raise ValueError("hora real sin zona horaria")
                        rows.append(row)
                    except (ValueError, TypeError) as exc:
                        errors.append(f"{path}:{line}: {exc}")
                if not count:
                    errors.append(f"{path}: no contiene eventos")
        except (OSError, UnicodeError, csv.Error) as exc:
            errors.append(f"{path}: {exc}")
    if not rows:
        errors.append("No hay eventos válidos")

    nodes, messages = {}, {}
    for row in rows:
        group = (row["mecanismo"], row["corrida"])
        nodes.setdefault((*group, row["nodo"]), []).append(row)
        messages.setdefault((*group, row["id_mensaje"]), []).append(row)

    for key, events in nodes.items():
        previous = 0
        for expected_sequence, row in enumerate(
                sorted(events, key=lambda r: r["secuencia"]), 1):
            if row["secuencia"] != expected_sequence:
                errors.append(f"{key}: secuencia duplicada o incompleta")
            expected = (max(previous, row["reloj_remoto"]) + 1
                        if row["evento"].startswith("recepcion_") else previous + 1)
            if row["reloj"] != expected:
                errors.append(f"{key}: actualización incorrecta en secuencia {row['secuencia']}")
            previous = row["reloj"]

    pairs = 0
    for key, events in messages.items():
        by_type = {}
        for row in events:
            by_type.setdefault(row["evento"], []).append(row)
        if set(by_type) != EVENTS or any(len(v) != 1 for v in by_type.values()):
            errors.append(f"{key}: solicitud/acuse incompleto o duplicado")
            continue
        request = by_type["envio_solicitud"][0]
        ack = by_type["envio_acuse"][0]
        if (request["origen"], request["destino"]) != (ack["destino"], ack["origen"]):
            errors.append(f"{key}: el acuse no invierte los extremos")
        received_request = by_type["recepcion_solicitud"][0]
        if ack["secuencia"] <= received_request["secuencia"]:
            errors.append(f"{key}: acuse anterior a la recepción de solicitud")
        for leg in ("solicitud", "acuse"):
            sent = by_type[f"envio_{leg}"][0]
            received = by_type[f"recepcion_{leg}"][0]
            if (sent["origen"], sent["destino"]) != (received["origen"], received["destino"]):
                errors.append(f"{key}: extremos inconsistentes en {leg}")
            if received["reloj_remoto"] != sent["reloj"]:
                errors.append(f"{key}: timestamp transmitido inconsistente en {leg}")
            if received["reloj"] <= sent["reloj"]:
                errors.append(f"{key}: recepción no posterior al envío en {leg}")
            pairs += 1

    # Un ejemplo entre nodos distintos de la MISMA corrida y mecanismo.
    equal_clock, witness = {}, None
    if not errors:
        for row in rows:
            key = (row["mecanismo"], row["corrida"], row["reloj"])
            other = equal_clock.get(key)
            if other and other["nodo"] != row["nodo"]:
                witness = {"mecanismo": key[0], "corrida": key[1], "reloj": key[2],
                           "eventos": [{k: r[k] for k in
                                        ("nodo", "secuencia", "evento", "id_mensaje")}
                                       for r in (other, row)]}
                break
            equal_clock[key] = row

    return {"valido": not errors, "archivos": len(paths), "eventos": len(rows),
            "pares_evaluados": pairs, "errores": errors,
            "ejemplo_relojes_iguales": witness}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, help="Informe JSON nuevo; no sobrescribe")
    parser.add_argument("--require-concurrent", action="store_true",
                        help="Exige un ejemplo con igual reloj entre nodos distintos")
    args = parser.parse_args()
    report = verify(args.csv)
    if args.require_concurrent and report["ejemplo_relojes_iguales"] is None:
        report["errores"].append("No se encontró un ejemplo válido con relojes iguales")
        report["valido"] = False
    content = json.dumps(report, ensure_ascii=False, indent=2)
    print(content)
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(content + "\n")
    return 0 if report["valido"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
