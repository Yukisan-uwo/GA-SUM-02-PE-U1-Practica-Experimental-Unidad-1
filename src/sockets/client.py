"""Reusable TCP client for the PE-U1 local milestone.

Run from the repository root:
    python src/sockets/client.py --sender nodo-A --port 5001 --message Hola --count 5

One TCP connection is opened and reused for all messages in the run.
"""

from __future__ import annotations

import argparse
import json
import socket
import time
from typing import Any

from csv_logs import append_event, append_latency


def generar_mensaje(tamano_bytes: int) -> str:
    """Genera una carga ASCII de tamaño exacto para las pruebas TCP."""
    if not isinstance(tamano_bytes, int) or isinstance(tamano_bytes, bool):
        raise TypeError("tamano_bytes debe ser un entero")
    if tamano_bytes < 0:
        raise ValueError("tamano_bytes no puede ser negativo")
    return "x" * tamano_bytes


class LamportClock:
    """Per-process logical clock; align the shared implementation with Roger."""

    def __init__(self) -> None:
        self.value = 0

    def tick(self) -> int:
        self.value += 1
        return self.value

    def receive(self, remote: int) -> int:
        self.value = max(self.value, remote) + 1
        return self.value


def receive_json_line(reader: Any) -> dict[str, Any]:
    line = reader.readline()
    if not line:
        raise ConnectionError("El servidor cerró la conexión sin enviar un acuse")
    response = json.loads(line)
    if not isinstance(response, dict):
        raise ValueError("El acuse JSON debe ser un objeto")
    return response


class ClienteTCP:
    """Transport adapter with the common connect/send/close interface."""

    def __init__(self, timeout: float = 2.0) -> None:
        self.timeout = timeout
        self.connection: socket.socket | None = None
        self.reader: Any = None
        self.writer: Any = None
        self.clock = LamportClock()

    def conectar(self, host: str, puerto: int) -> None:
        if self.connection is not None:
            raise RuntimeError("El cliente ya tiene una conexión abierta")
        self.connection = socket.create_connection((host, puerto), timeout=self.timeout)
        self.connection.settimeout(self.timeout)
        self.reader = self.connection.makefile("r", encoding="utf-8", newline="\n")
        self.writer = self.connection.makefile("w", encoding="utf-8", newline="\n")

    def enviar(
        self,
        sender: str,
        destination: str,
        message: str,
        attempt: int,
        run_number: int,
    ) -> tuple[dict[str, Any], float]:
        if self.connection is None or self.reader is None or self.writer is None:
            raise RuntimeError("Primero debes llamar a conectar()")

        request = {"sender": sender, "timestamp": self.clock.tick(), "message": message}
        message_id = f"{sender}-{attempt:06d}"
        started = time.perf_counter()
        append_event(sender, "envio_solicitud", request["timestamp"], message_id, sender, destination)
        try:
            self.writer.write(json.dumps(request, ensure_ascii=False, separators=(",", ":")) + "\n")
            self.writer.flush()
            response = receive_json_line(self.reader)
        except (socket.timeout, ConnectionError, OSError, json.JSONDecodeError) as error:
            elapsed_ms = (time.perf_counter() - started) * 1000
            append_latency(
                len(message.encode("utf-8")),
                run_number,
                attempt,
                elapsed_ms,
                False,
                type(error).__name__,
            )
            raise
        elapsed_ms = (time.perf_counter() - started) * 1000

        receiver = response.get("receiver")
        remote_clock = response.get("timestamp")
        ok = response.get("ok")
        if (
            not isinstance(receiver, str)
            or not isinstance(remote_clock, int)
            or isinstance(remote_clock, bool)
            or not isinstance(ok, bool)
        ):
            raise ValueError("El acuse requiere receiver, timestamp entero y ok booleano")
        self.clock.receive(remote_clock)
        append_event(sender, "recepcion_acuse", self.clock.value, message_id, receiver, sender)
        append_latency(len(message.encode("utf-8")), run_number, attempt, elapsed_ms, ok)
        return response, elapsed_ms

    def cerrar(self) -> None:
        if self.reader is not None:
            self.reader.close()
            self.reader = None
        if self.writer is not None:
            self.writer.close()
            self.writer = None
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def __enter__(self) -> "ClienteTCP":
        return self

    def __exit__(self, *_: object) -> None:
        self.cerrar()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cliente TCP reutilizable de la PE-U1")
    parser.add_argument("--sender", default="nodo-A", help="Nombre del nodo emisor")
    parser.add_argument("--receiver", default="nodo-B", help="Nombre del nodo destino")
    parser.add_argument("--host", default="127.0.0.1", help="Dirección del servidor")
    parser.add_argument("--port", type=int, default=5001, help="Puerto TCP")
    parser.add_argument("--message", help="Texto fijo para una prueba funcional")
    parser.add_argument("--size-bytes", type=int, help="Genera un mensaje ASCII de este tamaño exacto")
    parser.add_argument("--count", type=int, default=1, help="Cantidad de mensajes por una conexión")
    parser.add_argument("--timeout", type=float, default=2.0, help="Tiempo máximo en segundos")
    parser.add_argument("--run", type=int, default=1, help="Número de corrida para el CSV")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count debe ser al menos 1")
    if args.run < 0:
        parser.error("--run no puede ser negativo; usa 0 para calentamiento")
    if args.message is not None and args.size_bytes is not None:
        parser.error("elige --message o --size-bytes, no ambos")
    if args.size_bytes is not None:
        try:
            message = generar_mensaje(args.size_bytes)
        except (TypeError, ValueError) as error:
            parser.error(str(error))
    else:
        message = args.message if args.message is not None else "Hola"

    with ClienteTCP(timeout=args.timeout) as client:
        client.conectar(args.host, args.port)
        for index in range(1, args.count + 1):
            response, elapsed_ms = client.enviar(
                args.sender, args.receiver, message, index, args.run
            )
            print(
                f"{index}/{args.count} | acuse={response} | "
                f"reloj_local={client.clock.value} | RTT={elapsed_ms:.3f} ms"
            )


if __name__ == "__main__":
    main()
