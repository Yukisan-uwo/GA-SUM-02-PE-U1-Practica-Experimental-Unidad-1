# Resultados verificados de concurrencia

Generado desde CSV reales; hashes y reglas de Lamport comprobados nuevamente.
No son las 2000 mediciones secuenciales de RTT del benchmark.

| Corrida | Mecanismo | Bytes | Solicitudes | Acuses | Eventos | Pares | Errores |
|---|---|---:|---:|---:|---:|---:|---:|
| tcp-c100-r01 | TCP | 100 | 300 | 300 | 1200 | 600 | 0 |
| tcp-c10240-r01 | TCP | 10240 | 300 | 300 | 1200 | 600 | 0 |
| grpc-c100-r01 | gRPC | 100 | 300 | 300 | 1200 | 600 | 0 |
| grpc-c10240-r01 | gRPC | 10240 | 300 | 300 | 1200 | 600 | 0 |

## Método

Tres procesos con reloj y registro por nodo; solicitudes en anillo A→B→C→A.
Barreras de servidores listos, primeros envíos registrados antes de transmitir y finalización.
La marca igual inicial es consecuencia de un arranque controlado, no simultaneidad física probada.
No se comparan latencias ni rendimiento entre estas capturas y otros equipos.

## Procedencia y archivos

- `data/concurrencia/tcp-c100-r01`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T04:40:09.958642+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.
- `data/concurrencia/tcp-c10240-r01`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T04:40:10.465881+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.
- `data/concurrencia/grpc-c100-r01`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T04:40:11.046873+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.
- `data/concurrencia/grpc-c10240-r01`: roger@omarchy; Linux-7.2.15-1-omarchy-x86_64-with-glibc2.44; Python 3.14.8; UTC 2026-11-21T04:40:11.660171+00:00. Ejemplo: reloj 1 entre nodo-A y nodo-B.

Las capturas personales, el video y la participación humana se acreditan por separado.
