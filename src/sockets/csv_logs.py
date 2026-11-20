"""CSV append helpers for the PE-U1 TCP process logs."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Iterable


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = REPOSITORY_ROOT / "data"
_WRITE_LOCK = Lock()
EVENT_FIELDS = (
    "mecanismo",
    "nodo",
    "evento",
    "reloj",
    "hora_real",
    "id_mensaje",
    "origen",
    "destino",
)
LATENCY_FIELDS = (
    "mecanismo",
    "tamano_bytes",
    "corrida",
    "intento",
    "latencia_ms",
    "ok",
    "error",
)


def _append_csv(path: Path, fields: Iterable[str], row: dict[str, object]) -> None:
    with _WRITE_LOCK:
        DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)
        write_header = not path.exists() or path.stat().st_size == 0
        with path.open("a", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(fields))
            if write_header:
                writer.writeheader()
            writer.writerow(row)


def append_event(
    node: str,
    event: str,
    clock: int,
    message_id: str,
    origin: str,
    destination: str,
) -> None:
    safe_node = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in node)
    path = DATA_DIRECTORY / f"eventos_tcp_{safe_node}.csv"
    _append_csv(
        path,
        EVENT_FIELDS,
        {
            "mecanismo": "TCP",
            "nodo": node,
            "evento": event,
            "reloj": clock,
            "hora_real": datetime.now().astimezone().isoformat(timespec="milliseconds"),
            "id_mensaje": message_id,
            "origen": origin,
            "destino": destination,
        },
    )


def append_latency(
    message_size_bytes: int,
    run_number: int,
    attempt: int,
    latency_ms: float,
    ok: bool,
    error: str = "",
) -> None:
    path = DATA_DIRECTORY / "latencias_tcp.csv"
    _append_csv(
        path,
        LATENCY_FIELDS,
        {
            "mecanismo": "TCP",
            "tamano_bytes": message_size_bytes,
            "corrida": run_number,
            "intento": attempt,
            "latencia_ms": f"{latency_ms:.6f}",
            "ok": str(ok).lower(),
            "error": error,
        },
    )
