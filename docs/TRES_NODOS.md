# Prueba funcional con tres nodos

El lanzador inicia tres procesos localhost: A:5000, B:5001 y C:5002. Cada uno
comparte su reloj y registro entre servidor y cliente. Un coordinador controla
las fases, sin ser un nodo de mensajes. TCP y gRPC se ejecutan por separado.

```bash
python analysis/run_lamport_experiment.py --mechanism tcp --run-id tcp-r01 --output data/lamport_tcp_r01
python analysis/run_lamport_experiment.py --mechanism grpc --run-id grpc-r01 --output data/lamport_grpc_r01
```

Requiere Python 3.11+ y las dependencias de `requirements.txt`. Los puertos deben
estar libres. Las carpetas de salida deben ser nuevas.

## Protocolo

- Anillo A→B→C→A, acuses en sentido inverso.
- Veinte solicitudes por defecto, repartidas 7/7/6 entre tres clientes activos.
- Para la carga concurrente, `--messages 300`: cien solicitudes por cliente.
- Carga ASCII de 100 bytes; `--size-bytes 10240` selecciona 10 KB de carga útil.
- Barreras para servidores listos, primeros envíos registrados antes de transmitir
  y finalización. La segunda barrera permite observar eventos concurrentes de
  marca 1 con un orden de arranque controlado; no es tráfico espontáneo.
- No hay ediciones de relojes ni de datos después de registrar los eventos.
- Cada solicitud completada debe dejar cuatro eventos reales. El verificador
  evalúa el contenido, no da por aprobadas las cantidades esperadas.

## Archivos por ejecución

| Archivo | Contenido |
|---|---|
| `events_nodo-A.csv`, `events_nodo-B.csv`, `events_nodo-C.csv` | Eventos crudos |
| `environment.json` | Entorno y configuración; campos no disponibles quedan indicados |
| `run_result.json` | Estado, PID, puerto y solicitudes por nodo |
| `verification.json` | Comprobación del reloj y ejemplo de marcas iguales |
| `SHA256SUMS` | Hashes de los archivos de esa captura |

Un retorno distinto de cero significa error. Conservar los archivos parciales
para diagnóstico y repetir en otra carpeta; no presentar una captura fallida
como validada. Si un nodo falla antes de terminar, puede no haber verificación
ni manifiesto de hashes completo. No se implementan recuperación ni reintentos.

Para comprobar hashes en Linux, desde la raíz del repositorio:

```bash
cd data/lamport_tcp_r01
sha256sum -c SHA256SUMS
```

## Compatibilidad

Las llamadas existentes a `ClienteTCP(timeout=...)` y `ClienteGRPC(timeout=...)`
siguen disponibles. El registro completo solo se activa al pasar `clock` y
`event_log` explícitamente. No llamar al reloj otra vez por un evento registrado.

TCP añade ID y corrida al JSON en este modo. gRPC usa metadata `x-message-id`
y `x-run-id`, sin cambiar `.proto` ni regenerar stubs. No se infieren IDs por
orden de llegada. Los campos adicionales tienen sobrecarga distinta según el
mecanismo; 100/10240 bytes no son el tamaño completo transmitido.

## Alcance

Este comando no genera las mediciones oficiales de latencia y rendimiento ni
las cinco repeticiones del benchmark. Tampoco sustituye pruebas de caída de nodo,
capturas personales, video o demostración. Las ejecuciones de los tests usan
puertos libres y datos temporales, separados de las evidencias del equipo.

Código y documentación preparados con asistencia de inteligencia artificial.

## Resultados para el análisis de concurrencia

Las cuatro capturas `data/concurrencia/*-r01` contienen ejecuciones reales
automatizadas con 300 solicitudes por condición, dos mecanismos y dos cargas.
`PROCEDENCIA.md` conserva sus comandos y origen. No son capturas personales ni
se presentan como trabajo manual realizado sin asistencia.

El script `analysis/summarize_concurrency.py` verifica hashes, vuelve a ejecutar
el validador y genera conteos, tablas y ejemplos desde los CSV. El resumen
publicado está en `docs/tablas/concurrencia/resumen_concurrencia.md`. No se
escriben resultados a mano ni se modifican los CSV del benchmark.

Para que un integrante documente la metodología, debe recibir estos elementos:
comandos de cada ejecución, método de barreras, entorno registrado, CSV crudos,
SHA256SUMS, informes de verificación y resumen generado. Las capturas con usuario,
máquina y hora deben añadirse cuando el integrante ejecute personalmente la prueba.
