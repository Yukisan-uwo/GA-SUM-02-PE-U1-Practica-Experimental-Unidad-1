"""Reloj lógico por proceso, independiente del transporte y seguro entre hilos.

Python >= 3.11. No requiere dependencias externas.
"""

from threading import Lock


def _validate_timestamp(value: int) -> None:
    # bool hereda de int en Python, pero no es un timestamp válido.
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("El timestamp debe ser un entero (no booleano)")
    if value < 0:
        raise ValueError("El timestamp no puede ser negativo")


class LamportClock:
    """Una instancia por nodo/proceso, compartida por sus hilos.

    Cada operación devuelve su timestamp atómico. Registrar ese retorno,
    no consultar value después: otro hilo podría haber avanzado el reloj.
    El bloqueo no ordena por sí solo la escritura de archivos de registro.
    """

    def __init__(self, initial: int = 0) -> None:
        _validate_timestamp(initial)
        self._value = initial
        self._lock = Lock()

    @property
    def value(self) -> int:
        """Consulta sin incrementar; propiedad de solo lectura."""
        with self._lock:
            return self._value

    @property
    def valor(self) -> int:
        """Alias de value para el código gRPC existente."""
        return self.value

    def tick(self) -> int:
        """Registra un evento local o un envío y devuelve su timestamp."""
        with self._lock:
            self._value += 1
            return self._value

    def send(self) -> int:
        """Incrementa inmediatamente antes de un envío."""
        return self.tick()

    def receive(self, remote: int) -> int:
        """Registra una recepción: max(local, remoto) + 1."""
        _validate_timestamp(remote)
        with self._lock:
            self._value = max(self._value, remote) + 1
            return self._value

    def enviar(self) -> int:
        """Alias de send para el código gRPC existente."""
        return self.send()

    def recibir(self, recibido: int) -> int:
        """Alias de receive para el código gRPC existente."""
        return self.receive(recibido)
