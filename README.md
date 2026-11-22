# GA-SUM-02-PE-U1-Practica-Experimental-Unidad-1
Creacion del repositorio para la practica experimental de la unidad 1, semana 4

## Preparación

Python 3.11 o superior. Desde la raíz del repositorio:

```bash
python -m venv .venv
```

Activar con `source .venv/bin/activate` en Linux o `.venv\Scripts\activate.bat`
en Windows cmd.exe. Después:

```bash
python -m pip install -r requirements.txt
```

## Tres nodos y verificación de Lamport

No iniciar otros servidores en 5000, 5001 o 5002 durante estas pruebas.
Cada comando inicia tres procesos con servidor y cliente por nodo:

```bash
python analysis/run_lamport_experiment.py --mechanism tcp --run-id tcp-r01 --output data/lamport_tcp_r01
python analysis/run_lamport_experiment.py --mechanism grpc --run-id grpc-r01 --output data/lamport_grpc_r01
```

Ejecutarlos por separado. Cada prueba distribuye veinte solicitudes entre los
tres clientes concurrentes y guarda los eventos, entorno, resultado, verificación
y `SHA256SUMS`. Una carpeta existente nunca se sobrescribe: para repetir, elegir
otro `--run-id` y otra ruta `--output`. Para una carga de 10 KB añadir
`--size-bytes 10240`.

Son pruebas funcionales de causalidad y concurrencia, **no** las cinco corridas
de cien envíos por tamaño del benchmark. Uso y límites:
[docs/TRES_NODOS.md](docs/TRES_NODOS.md).

### Carga concurrente y resultados

Para cien solicitudes por cliente, usar `--messages 300`. Las cuatro condiciones
se ejecutan separadamente y en carpetas nuevas:

```bash
python analysis/run_lamport_experiment.py --mechanism tcp --run-id tcp-c100-r02 --messages 300 --size-bytes 100 --output data/concurrencia/tcp-c100-r02
python analysis/run_lamport_experiment.py --mechanism tcp --run-id tcp-c10240-r02 --messages 300 --size-bytes 10240 --output data/concurrencia/tcp-c10240-r02
python analysis/run_lamport_experiment.py --mechanism grpc --run-id grpc-c100-r02 --messages 300 --size-bytes 100 --output data/concurrencia/grpc-c100-r02
python analysis/run_lamport_experiment.py --mechanism grpc --run-id grpc-c10240-r02 --messages 300 --size-bytes 10240 --output data/concurrencia/grpc-c10240-r02
```

Los CSV publicados de `r01` proceden de ejecuciones automatizadas asistidas;
su origen y comandos están en [data/concurrencia/PROCEDENCIA.md](data/concurrencia/PROCEDENCIA.md).
No se atribuyen a una ejecución manual ni sustituyen las capturas personales.
El entorno Linux de concurrencia es distinto del Windows del benchmark.

Para recalcular sus resultados sin editar CSV ni sobrescribir tablas:

```bash
python analysis/summarize_concurrency.py data/concurrencia/tcp-c100-r01 data/concurrencia/tcp-c10240-r01 data/concurrencia/grpc-c100-r01 data/concurrencia/grpc-c10240-r01 --output analysis/concurrencia_recalculada
```

Resumen generado: [docs/tablas/concurrencia/resumen_concurrencia.md](docs/tablas/concurrencia/resumen_concurrencia.md).
Las tablas y ejemplos de la sección 13 provienen del mismo script. Esta prueba
adicional no cambia las 2000 mediciones de RTT ni sus CSV.

## Pruebas automatizadas

```bash
python -B -m unittest discover -s tests -v
```

Los datos temporales de los tests no se incluyen como evidencia experimental.

## Informe LaTeX

Compilador: pdfLaTeX; principal: `docs/main.tex`; bibliografía: Biber.
Con una distribución TeX que incluya los paquetes del preámbulo de `main.tex`
(en particular newtx, babel-spanish, TikZ, listings, biblatex-ieee y xurl):

```bash
cd docs
pdflatex main.tex
biber main
pdflatex main.tex
pdflatex main.tex
```

La versión final compilada del informe está en `docs/main.pdf`.

## Video

Video de respaldo con la participación de los cuatro integrantes: <https://www.youtube.com/watch?v=V7xLDmiJep4>

## Corridas personales de veinte intercambios

Las corridas seleccionadas de Roger, con TCP y gRPC, tienen 20 solicitudes y
100 bytes de carga por solicitud. Reporte de fechas, CSV, roles y hashes:
[docs/tablas/lamport20/resumen.md](docs/tablas/lamport20/resumen.md).
Capturas y procedencia: [docs/EVIDENCIAS_20_INTERCAMBIOS.md](docs/EVIDENCIAS_20_INTERCAMBIOS.md).

Para regenerar el reporte desde los CSV sin sobrescribir el ya entregado:

```bash
python analysis/report_twenty_exchanges.py --grpc-capture data/lamport20/grpc-20261121-002802 --tcp-capture data/lamport20/tcp-20261121-003058 --output analysis/lamport20_recalculado
```

Si la carpeta de salida existe, elegir otra. Estas corridas no sustituyen ni se
agregan a las 2000 mediciones RTT ni a las capturas de carga de 300 solicitudes.

## Caída controlada y número de nodos

Los protocolos, alcances y comandos están en
[docs/PRUEBAS_CONTROLADAS.md](docs/PRUEBAS_CONTROLADAS.md).
Resultados generados desde la sesión personal documentada:
[docs/tablas/controlados/resumen.md](docs/tablas/controlados/resumen.md).
Capturas y procedencia: [docs/EVIDENCIAS_CONTROLADAS.md](docs/EVIDENCIAS_CONTROLADAS.md).
Los registros asistidos anteriores se conservan como conjunto separado, sin mezclarlos.

Para una nueva ejecución personal, con carpeta todavía inexistente:

```bash
python analysis/run_controlled_checks.py --output data/controlados/personal-r02 --origin personal
python analysis/analyze_controlled_checks.py data/controlados/personal-r02 --output analysis/controlados_personal_r02
```

La prueba termina deliberadamente el proceso C de su propio grupo de prueba;
no termina servidores ajenos. Usa puertos libres y nuevos procesos. No modificar
los CSV incompletos: el envío fallido es parte de la evidencia, no un dato a borrar.


## Carga personal de Roger: 300 solicitudes

Sesión `personal300-20261121-175920`: TCP/gRPC con 100 y 10240 bytes;
300 solicitudes totales por condición, cien por cada uno de los tres nodos.
Datos en `data/concurrencia/personal300-20261121-175920/`; resúmenes derivados en
`docs/tablas/concurrencia_personal/personal300-20261121-175920/`.
Las cinco capturas, logs, procedencia y reproducción se describen en
[Evidencias personales de carga](docs/EVIDENCIAS_CARGA_300.md).
Las corridas asistidas anteriores permanecen separadas. Esta sesión no sustituye
el video grupal, cuyo enlace está en la sección [Video](#video).
