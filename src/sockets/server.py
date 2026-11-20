"""Small line-delimited JSON TCP server for the PE-U1 first local milestone.

Run from the repository root:
    python src/sockets/server.py --node nodo-B --port 5001
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
import threading
from pathlib import Path
from typing import Any

from csv_logs import append_event

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.common.lamport import LamportClock  # noqa: E402


def read_json_line(reader: Any) -> dict[str, Any] | None:
    line = reader.readline()
    if not line:
        return None
    value = json.loads(line)
    if not isinstance(value, dict):
        raise ValueError("El mensaje JSON debe ser un objeto")
    return value


def serve_client(
    connection: socket.socket,
    node: str,
    clock: LamportClock,
    quiet: bool = False,
    log_events: bool = True,
) -> None:
    message_number = 0
    with connection, connection.makefile("r", encoding="utf-8", newline="\n") as reader:
        writer = connection.makefile("w", encoding="utf-8", newline="\n")
        with writer:
            while True:
                request = read_json_line(reader)
                if request is None:
                    return
                sender = request.get("sender")
                message = request.get("message")
                timestamp = request.get("timestamp")
                if not isinstance(sender, str) or not isinstance(message, str):
                    raise ValueError("La solicitud requiere sender y message de texto")
                if not isinstance(timestamp, int) or isinstance(timestamp, bool):
                    raise ValueError("timestamp debe ser un entero")

                message_number += 1
                message_id = f"{sender}-{message_number:06d}"
                received_clock = clock.receive(timestamp)
                if log_events:
                    append_event(node, "recepcion_solicitud", received_clock, message_id, sender, node)
                if not quiet:
                    print(f"RECEPCION {sender} -> {node}: reloj={received_clock}, bytes={len(message.encode('utf-8'))}")

                # The acknowledgment is a new send event, so tick before sending it.
                ack_clock = clock.tick()
                response = {"receiver": node, "timestamp": ack_clock, "ok": True}
                if log_events:
                    append_event(node, "envio_acuse", ack_clock, message_id, node, sender)
                writer.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
                writer.flush()
                if not quiet:
                    print(f"ENVIO_ACUSE {node} -> {sender}: reloj={ack_clock}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Servidor TCP de prueba PE-U1")
    parser.add_argument("--node", default="nodo-B", help="Nombre del nodo servidor")
    parser.add_argument("--host", default="127.0.0.1", help="Dirección de escucha")
    parser.add_argument("--port", type=int, default=5001, help="Puerto TCP")
    parser.add_argument("--quiet", action="store_true", help="Reduce la salida de consola durante mediciones")
    parser.add_argument("--no-event-log", action="store_true", help="Desactiva CSV de eventos para el benchmark")
    args = parser.parse_args()

    clock = LamportClock()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((args.host, args.port))
        server.listen()
        print(f"{args.node} escuchando en {args.host}:{args.port}")
        while True:
            connection, address = server.accept()
            if not args.quiet:
                print(f"Conexión desde {address}")
            worker = threading.Thread(
                target=serve_client,
                args=(connection, args.node, clock, args.quiet, not args.no_event_log),
                daemon=True,
            )
            worker.start()


if __name__ == "__main__":
    main()
