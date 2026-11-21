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

El informe continúa en borrador mientras haya apartados y resultados pendientes.

## Video

Pendiente: enlace al video del equipo con participación de todos los integrantes.
