"""Registro en CSV de eventos y latencias del mecanismo gRPC.

Usa las mismas columnas que el registro TCP para que el analisis lea
los dos mecanismos igual. Los archivos quedan en /data/.
"""
import csv
import threading
from datetime import datetime
from pathlib import Path

CARPETA_DATOS = Path(__file__).resolve().parents[2] / "data"
CAMPOS_EVENTO = ("mecanismo", "nodo", "evento", "reloj", "hora_real",
                 "id_mensaje", "origen", "destino")
CAMPOS_LATENCIA = ("mecanismo", "tamano_bytes", "corrida", "intento",
                   "latencia_ms", "ok", "error")

# El servidor atiende varias peticiones en hilos distintos; sin este
# candado dos hilos podrian escribir en el mismo CSV a la vez.
_candado = threading.Lock()


def _agregar_fila(ruta, campos, fila):
    with _candado:
        CARPETA_DATOS.mkdir(parents=True, exist_ok=True)
        poner_encabezado = not ruta.exists() or ruta.stat().st_size == 0
        with ruta.open("a", newline="", encoding="utf-8") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=campos)
            if poner_encabezado:
                escritor.writeheader()
            escritor.writerow(fila)


def registrar_evento(nodo, evento, reloj, id_mensaje, origen, destino):
    ruta = CARPETA_DATOS / f"eventos_grpc_{nodo}.csv"
    _agregar_fila(ruta, CAMPOS_EVENTO, {
        "mecanismo": "gRPC",
        "nodo": nodo,
        "evento": evento,
        "reloj": reloj,
        "hora_real": datetime.now().astimezone().isoformat(timespec="milliseconds"),
        "id_mensaje": id_mensaje,
        "origen": origen,
        "destino": destino,
    })


def registrar_latencia(tamano_bytes, corrida, intento, latencia_ms, ok, error=""):
    ruta = CARPETA_DATOS / "latencias_grpc.csv"
    _agregar_fila(ruta, CAMPOS_LATENCIA, {
        "mecanismo": "gRPC",
        "tamano_bytes": tamano_bytes,
        "corrida": corrida,
        "intento": intento,
        "latencia_ms": f"{latencia_ms:.6f}",
        "ok": str(ok).lower(),
        "error": error,
    })