# Reloj de Lamport

Componente para TCP y gRPC. Requiere Python 3.11 o superior, sin dependencias externas.

## Uso

Ubicar el módulo en `src/common/lamport.py` e importar desde la raíz del proyecto:

```python
from src.common.lamport import LamportClock

clock = LamportClock()
sent = clock.send()                   # local + 1
received = clock.receive(timestamp)   # max(local, timestamp) + 1
current = clock.value                # Consulta sin incrementar
```

Crear **una instancia por nodo/proceso**, compartida entre sus hilos de servidor
y cliente. Las operaciones están protegidas por un bloqueo.

| Operación | Métodos equivalentes |
|---|---|
| Evento local o envío | `tick()`, `send()`, `enviar()` |
| Recepción | `receive(timestamp)`, `recibir(timestamp)` |
| Consulta de solo lectura | `value`, `valor` |

## Reglas de integración

- Incrementar una sola vez por evento; el envío de un acuse es un evento nuevo.
- Registrar el timestamp devuelto por la operación, no una consulta posterior.
- Los timestamps deben ser enteros no negativos; se rechazan booleanos.
- El bloqueo del reloj no protege conexiones ni archivos CSV: requieren su propia sincronización.
- Procesos distintos no comparten esta instancia, aunque usen el mismo nombre de nodo.

## Pruebas

Con `tests/test_lamport.py` en el proyecto, ejecutar desde la raíz:

```bash
python -m unittest discover -s tests -v
```

Las diez pruebas cubren actualización, validación, compatibilidad de interfaces
y concurrencia entre hilos. No sustituyen las pruebas experimentales TCP/gRPC.

## Uso de IA

Componente preparado con asistencia de inteligencia artificial.
