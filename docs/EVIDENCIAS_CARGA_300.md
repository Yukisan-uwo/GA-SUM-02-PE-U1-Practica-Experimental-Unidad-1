# Evidencias personales de carga de 300 solicitudes

Sesión: `personal300-20261121-175920`, iniciada por Roger el 21/11/2026 a las
17:59:20 UTC−05:00. Código, preparación y verificación con asistencia de IA;
las corridas fueron iniciadas por Roger en su terminal mediante un guion interactivo.

## Condiciones y resultados

| Transporte | Bytes de carga útil | Solicitudes | Acuses | Eventos | Pares | Errores detectados |
|---|---:|---:|---:|---:|---:|---:|
| TCP | 100 | 300 | 300 | 1200 | 600 | 0 |
| TCP | 10240 | 300 | 300 | 1200 | 600 | 0 |
| gRPC | 100 | 300 | 300 | 1200 | 600 | 0 |
| gRPC | 10240 | 300 | 300 | 1200 | 600 | 0 |

Son 300 solicitudes **totales por condición**, cien por nodo, con tres procesos
que alojan servidor, cliente y reloj local compartido entre sus hilos. Las cuatro
condiciones se ejecutaron secuencialmente; dentro de cada una los tres clientes
son concurrentes. El lanzador seleccionó puertos libres con `--base-port 0`.
El tamaño indicado es la carga útil, no el tamaño del mensaje en la red.

Datos originales: `data/concurrencia/personal300-20261121-175920/`.
Cada condición conserva tres CSV, entorno, resultado, verificación y SHA-256.
Los resúmenes se generaron desde esos CSV en
`docs/tablas/concurrencia_personal/personal300-20261121-175920/`.

## Capturas y logs

Carpeta: `docs/evidencias/Roger/carga300/personal300-20261121-175920/`.

| Captura | Condición documentada |
|---|---|
| `01_tcp_100.png` | TCP con 100 bytes |
| `02_tcp_10240.png` | TCP con 10240 bytes |
| `03_grpc_100.png` | gRPC con 100 bytes |
| `04_grpc_10240.png` | gRPC con 10240 bytes |
| `05_resumen_hashes.png` | Consulta posterior del resumen y comprobación de 24 archivos |

Se conservan cinco logs y `session.json` originales. Las imágenes aportadas por
Roger se copiaron sin modificar su contenido, con nombres descriptivos; no se
reconstruyeron ni retocaron. El manifiesto de evidencia incluye imágenes, logs
y metadatos. El texto de alcance de `session.json` es el generado durante la
preparación y se conserva sin reescribirlo retrospectivamente.

## Reproducción del resumen

Desde la raíz del repositorio, con el entorno de dependencias instalado, usar
una carpeta de salida que todavía no exista:

```fish
.venv/bin/python analysis/summarize_concurrency.py data/concurrencia/personal300-20261121-175920/tcp-100 data/concurrencia/personal300-20261121-175920/tcp-10240 data/concurrencia/personal300-20261121-175920/grpc-100 data/concurrencia/personal300-20261121-175920/grpc-10240 --output analysis/resumen_personal300_reproducido
```

Para comprobar los manifiestos, situarse dentro de cada carpeta de sesión
citada y ejecutar `sha256sum --check SHA256SUMS`.

## Límites

Esta sesión personal es adicional a las corridas asistidas anteriores, que se
conservan separadas y mantienen su procedencia. Hay una corrida por condición;
no se infieren estadísticas de rendimiento ni se agregan al benchmark de 2000 RTT.
La quinta captura es una consulta posterior, no una quinta corrida. Estos datos
no sustituyen el video grupal, todavía pendiente, ni la explicación individual.
