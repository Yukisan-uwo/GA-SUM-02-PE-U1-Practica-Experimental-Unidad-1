# Corridas de veinte intercambios: gRPC y TCP

Reporte generado por `analysis/report_twenty_exchanges.py` a partir de CSV reales.
Se recalcularon los hashes y las reglas de Lamport antes de generar los resultados.

Los nombres son los del lanzador integrado, no los CSV acumulativos de los scripts antiguos.
Veinte intercambios significa veinte solicitudes con sus acuses entre los tres nodos,
no veinte solicitudes por cliente ni veinte solicitudes exclusivamente A→B.

## gRPC

- Corrida: `grpc20-20261121-002802`.
- Inicio registrado: **2026-11-21T00:28:09.183222-05:00 (UTC−05:00)**; UTC: `2026-11-21T05:28:09.183222+00:00`.
- Equipo: `roger@omarchy`; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8.
- Carga útil: 100 bytes ASCII por solicitud.
- Resultado: 20 solicitudes, 20 acuses, 80 eventos, 40 pares y 0 errores causales.

### CSV exactos

- `data/lamport20/grpc-20261121-002802/events_nodo-A.csv`.
- `data/lamport20/grpc-20261121-002802/events_nodo-B.csv`.
- `data/lamport20/grpc-20261121-002802/events_nodo-C.csv`.

### Participación de los nodos

| Nodo | Puerto | Cliente: solicitudes → destino | Servidor: solicitudes ← origen | Reloj final |
|---|---:|---|---|---:|
| nodo-A | 5000 | 7 → nodo-B | 6 ← nodo-C | 28 |
| nodo-B | 5001 | 7 → nodo-C | 7 ← nodo-A | 28 |
| nodo-C | 5002 | 6 → nodo-A | 7 ← nodo-B | 27 |

Cada proceso actúa como servidor y cliente con el mismo reloj local.
El anillo es A→B→C→A; los acuses regresan en sentido inverso.

Los tres CSV están incluidos y comprobados en `data/lamport20/grpc-20261121-002802/SHA256SUMS`.
No se mezclan con el manifiesto de las mediciones de latencia.

### Comando equivalente con variables expandidas

Comando descriptivo de la corrida ya realizada: para repetir, elegir otro ID y carpeta.
```fish
.venv/bin/python analysis/run_lamport_experiment.py --mechanism grpc --run-id "grpc20-20261121-002802" --messages 20 --size-bytes 100 --output "data/lamport20/grpc-20261121-002802"
```

## TCP

- Corrida: `tcp20-20261121-003058`.
- Inicio registrado: **2026-11-21T00:31:03.289075-05:00 (UTC−05:00)**; UTC: `2026-11-21T05:31:03.289075+00:00`.
- Equipo: `roger@omarchy`; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8.
- Carga útil: 100 bytes ASCII por solicitud.
- Resultado: 20 solicitudes, 20 acuses, 80 eventos, 40 pares y 0 errores causales.

### CSV exactos

- `data/lamport20/tcp-20261121-003058/events_nodo-A.csv`.
- `data/lamport20/tcp-20261121-003058/events_nodo-B.csv`.
- `data/lamport20/tcp-20261121-003058/events_nodo-C.csv`.

### Participación de los nodos

| Nodo | Puerto | Cliente: solicitudes → destino | Servidor: solicitudes ← origen | Reloj final |
|---|---:|---|---|---:|
| nodo-A | 5000 | 7 → nodo-B | 6 ← nodo-C | 28 |
| nodo-B | 5001 | 7 → nodo-C | 7 ← nodo-A | 28 |
| nodo-C | 5002 | 6 → nodo-A | 7 ← nodo-B | 27 |

Cada proceso actúa como servidor y cliente con el mismo reloj local.
El anillo es A→B→C→A; los acuses regresan en sentido inverso.

Los tres CSV están incluidos y comprobados en `data/lamport20/tcp-20261121-003058/SHA256SUMS`.
No se mezclan con el manifiesto de las mediciones de latencia.

### Comando equivalente con variables expandidas

Comando descriptivo de la corrida ya realizada: para repetir, elegir otro ID y carpeta.
```fish
.venv/bin/python analysis/run_lamport_experiment.py --mechanism tcp --run-id "tcp20-20261121-003058" --messages 20 --size-bytes 100 --output "data/lamport20/tcp-20261121-003058"
```

## Método y límites

Las barreras sincronizan servidores disponibles, primeros envíos registrados antes de
transmitir y finalización. Las marcas iguales provienen de eventos reales con arranque
controlado; no significan simultaneidad física exacta.

Son pruebas funcionales independientes de las capturas de carga de 300 solicitudes y de
las 2000 mediciones secuenciales de RTT. No se usan para comparar latencias.

Las capturas y los logs asociados se documentan en `docs/EVIDENCIAS_20_INTERCAMBIOS.md`.
