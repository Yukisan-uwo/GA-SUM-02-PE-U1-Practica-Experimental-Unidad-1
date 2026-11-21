# Evidencias de los veinte intercambios

Corridas seleccionadas, ejecutadas por Roger desde la terminal y verificadas
sobre sus CSV originales:

- gRPC: `grpc20-20261121-002802`, inicio registrado el 21/11/2026 a las
  00:28:09, UTC−05:00.
- TCP: `tcp20-20261121-003058`, inicio registrado el 21/11/2026 a las
  00:31:03, UTC−05:00.

El código y la preparación/verificación tuvieron asistencia de IA. A diferencia
de las capturas automatizadas de carga de 300 solicitudes, estas dos ejecuciones
se documentaron con capturas de la terminal de Roger. No corresponden al benchmark
de 2000 mediciones RTT.

## Imágenes y logs

En `docs/evidencias/Roger/lamport20/`:

| Archivo | Contenido revisado |
|---|---|
| `grpc20_arranque.png` | Comando gRPC, fecha, usuario, máquina, tres PID y verificación aprobada |
| `grpc20_hashes.png` | Comprobación de los hashes de gRPC con resultados OK |
| `tcp20_arranque.png` | Comando TCP, fecha, usuario, máquina, tres PID y verificación aprobada |
| `tcp20_arranque_notificacion.png` | Otra captura del arranque TCP, con notificación del sistema conservada |
| `tcp20_verificacion.png` | Consulta del informe TCP, no una ejecución nueva |
| `tcp20_hashes.png` | Comprobación de hashes TCP con resultados OK |
| `grpc20-20261121-002802.log` | Salida original de la ejecución gRPC |
| `tcp20-20261121-003058.log` | Salida original de la ejecución TCP |

Las imágenes son copias byte a byte de los archivos aportados, sin recortes,
retoques ni reconstrucciones. Se asignaron nombres acordes con su contenido en
una subcarpeta nueva; los originales no fueron modificados. El manifiesto
`SHA256SUMS` de esa subcarpeta incluye las seis imágenes y los dos logs.

## Datos y comprobaciones

- Datos seleccionados: `data/lamport20/grpc-20261121-002802/` y
  `data/lamport20/tcp-20261121-003058/`.
- Cada carpeta conserva sus tres CSV, entorno, resultado, verificación y hashes.
- `data/lamport20/SHA256SUMS` cubre únicamente esas dos corridas seleccionadas.
- Los intentos previos no seleccionados no se presentan como resultados de estas
  corridas. No se borraron los archivos de diagnóstico del equipo local.
- El reporte con fechas, roles, nombres exactos de CSV y conteos se genera en
  `docs/tablas/lamport20/resumen.md` mediante `analysis/report_twenty_exchanges.py`.

Comprobar desde la raíz del repositorio, en terminal fish:

```fish
pushd data/lamport20
sha256sum --check SHA256SUMS
popd
pushd docs/evidencias/Roger/lamport20
sha256sum --check SHA256SUMS
popd
```

Estos datos documentan veinte intercambios totales por mecanismo, distribuidos
7/7/6 entre los tres clientes. No deben describirse como veinte envíos A→B
exclusivamente, aunque el contrato gRPC y el tamaño de carga sean los mismos.
