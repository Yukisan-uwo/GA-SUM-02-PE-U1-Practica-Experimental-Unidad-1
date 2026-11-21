"""Registro por nodo/corrida. Usar una instancia por proceso y archivo."""

import csv
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

from .lamport import LamportClock


EVENT_FIELDS = (
    "mecanismo", "corrida", "nodo", "secuencia", "evento", "reloj",
    "reloj_remoto", "hora_real", "id_mensaje", "origen", "destino",
)
EVENT_TYPES = {
    "envio_solicitud", "recepcion_solicitud", "envio_acuse", "recepcion_acuse",
}


class EventLog:
    """Serializa actualización del reloj y registro dentro del mismo proceso.

    El archivo se crea exclusivamente: nunca se mezcla con corridas anteriores.
    No compartir el archivo con otros procesos. Todos los eventos del reloj
    deben pasar por esta instancia durante la prueba registrada.
    """

    def __init__(self, path: str | Path, node: str, mechanism: str,
                 run: str, clock: LamportClock) -> None:
        if not all(isinstance(x, str) and x.strip()
                   for x in (node, mechanism, run)):
            raise ValueError("Nodo, mecanismo y corrida deben ser textos no vacíos")
        if mechanism not in {"TCP", "gRPC"}:
            raise ValueError("El mecanismo debe ser TCP o gRPC")
        if clock.value != 0:
            raise ValueError("La captura completa debe comenzar con reloj en cero")
        self.node, self.mechanism, self.run = node, mechanism, run
        self.clock = clock
        self._lock = Lock()
        self._sequence = 0
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = path.open("x", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=EVENT_FIELDS)
        self._writer.writeheader()
        self._stream.flush()

    def record(self, event: str, message_id: str, origin: str,
               destination: str, remote: int | None = None) -> int:
        if event not in EVENT_TYPES:
            raise ValueError("Tipo de evento no reconocido")
        if not all(isinstance(x, str) and x.strip()
                   for x in (message_id, origin, destination)):
            raise ValueError("ID, origen y destino deben ser textos no vacíos")
        receiving = event.startswith("recepcion_")
        if self.node != (destination if receiving else origin):
            raise ValueError("El nodo no corresponde al extremo del evento")
        if not receiving and remote is not None:
            raise ValueError("Un envío no debe incluir reloj remoto")
        if receiving and remote is None:
            raise ValueError("Una recepción requiere reloj remoto")
        with self._lock:
            if self._stream.closed:
                raise ValueError("El registro está cerrado")
            timestamp = (self.clock.receive(remote) if receiving
                         else self.clock.send())
            self._sequence += 1
            self._writer.writerow({
                "mecanismo": self.mechanism, "corrida": self.run,
                "nodo": self.node, "secuencia": self._sequence,
                "evento": event, "reloj": timestamp,
                "reloj_remoto": remote if receiving else "",
                "hora_real": datetime.now(timezone.utc).isoformat(),
                "id_mensaje": message_id, "origen": origin,
                "destino": destination,
            })
            self._stream.flush()
            return timestamp

    def close(self) -> None:
        with self._lock:
            self._stream.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()
