# Registro y verificación de Lamport

Requiere Python 3.11+ y `src/common/lamport.py`. Sin dependencias adicionales.

## Registro por nodo

```python
from src.common.lamport import LamportClock
from src.common.event_log import EventLog

clock = LamportClock()
with EventLog("data/eventos_tcp_r01_A.csv", "nodo-A", "TCP", "r01", clock) as log:
    ts = log.record("envio_solicitud", "r01-A-0001", "nodo-A", "nodo-B")
    # Enviar ts en el campo timestamp del mensaje real.
```

Tipos: `envio_solicitud`, `recepcion_solicitud`, `envio_acuse`, `recepcion_acuse`.
En una recepción, pasar `remote=timestamp` del mensaje recibido. El método ya
actualiza el reloj: no llamar además a `tick`, `send` ni `receive`.

- Una instancia de registro y reloj por nodo, compartida entre sus hilos.
- Archivo exclusivo por proceso y corrida; no se sobrescriben registros.
- Misma corrida e ID de solicitud en ambos extremos y en el acuse.
- El transporte debe transmitir el ID (campo o metadata) y el timestamp.
- CSV con mecanismo, corrida, nodo, secuencia local, evento, reloj local/remoto,
  hora UTC, ID, origen y destino. La secuencia, no la hora física, ordena el nodo.
- Comenzar con reloj cero y registrar todos sus eventos desde el inicio.
- Si falla la escritura, abortar la corrida; no continuar con registros incompletos.

## Verificación

Pasar explícitamente los CSV de los tres nodos de una o varias corridas:

```bash
python analysis/verify_lamport.py data/eventos_tcp_r01_A.csv data/eventos_tcp_r01_B.csv data/eventos_tcp_r01_C.csv --require-concurrent --output analysis/verificacion_tcp_r01.json
```

Comprueba secuencias completas, reglas exactas del reloj, unicidad del ID por
intercambio, extremos de mensajes y parejas de envío/recepción de solicitudes
y acuses. Retorna código 0 si es válido y 1 si encuentra errores. No modifica
los CSV. El informe JSON tampoco se sobrescribe.

`--require-concurrent` exige un par de eventos de nodos distintos con igual
reloj dentro de la misma corrida y mecanismo. Bajo las reglas de Lamport
verificadas, ese par no tiene relación causal registrada; no prueba simultaneidad
física. Relojes diferentes tampoco prueban causalidad.

El verificador exige intercambios completos: un envío fallido se conserva en los
datos, pero no aprobará esta validación de éxito. Analizar fallos por separado.
Los CSV TCP antiguos carecen de corrida, secuencia y reloj remoto: no deben
completarse a mano ni presentarse como compatibles; se necesitan nuevas ejecuciones.

## Pruebas

```bash
python -B -m unittest discover -s tests -v
```

Los datos temporales de las pruebas son fixtures, no mediciones experimentales.
La integración y ejecución real de ambos transportes deben validarse por separado.

Componente preparado con asistencia de inteligencia artificial.
