# Resultados verificados de concurrencia

Generado desde CSV reales; hashes y reglas de Lamport comprobados nuevamente.
No son las 2000 mediciones secuenciales de RTT del benchmark.

| Corrida | Mecanismo | Bytes | Solicitudes | Acuses | Eventos | Pares | Errores |
|---|---|---:|---:|---:|---:|---:|---:|
| personal300-20261121-175920-tcp-100 | TCP | 100 | 300 | 300 | 1200 | 600 | 0 |
| personal300-20261121-175920-tcp-10240 | TCP | 10240 | 300 | 300 | 1200 | 600 | 0 |
| personal300-20261121-175920-grpc-100 | gRPC | 100 | 300 | 300 | 1200 | 600 | 0 |
| personal300-20261121-175920-grpc-10240 | gRPC | 10240 | 300 | 300 | 1200 | 600 | 0 |

## Método

Tres procesos con reloj y registro por nodo; solicitudes en anillo A→B→C→A.
Barreras de servidores listos, primeros envíos registrados antes de transmitir y finalización.
La marca igual inicial es consecuencia de un arranque controlado, no simultaneidad física probada.
No se comparan latencias ni rendimiento entre estas capturas y otros equipos.

## Procedencia y archivos

- `data/concurrencia/personal300-20261121-175920/tcp-100`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T22:59:50.799114+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.
- `data/concurrencia/personal300-20261121-175920/tcp-10240`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T23:00:27.266335+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.
- `data/concurrencia/personal300-20261121-175920/grpc-100`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T23:01:35.052419+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.
- `data/concurrencia/personal300-20261121-175920/grpc-10240`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T23:01:51.549662+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.

Las capturas personales, el video y la participación humana se acreditan por separado.
