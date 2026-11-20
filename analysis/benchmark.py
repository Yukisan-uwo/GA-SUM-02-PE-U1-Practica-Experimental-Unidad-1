"""Planificador y ejecutor de mediciones TCP/gRPC para la PE-U1.

Uso desde la raíz del repositorio:
    python analysis/benchmark.py
    python analysis/benchmark.py --probar --mecanismo grpc --tamano 100
    python analysis/benchmark.py --ejecutar --mecanismo tcp

Las pruebas cortas NO generan los CSV consolidados del experimento.
ATENCIÓN: los clientes del equipo sí crean sus propios logs en data/.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
import time
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MECANISMOS = ("tcp", "grpc")
TAMANOS_BYTES = (100, 10 * 1024)
PUERTOS_NODOS = {"nodo-A": 5000, "nodo-B": 5001, "nodo-C": 5002}
COLUMNAS_LATENCIA = (
    "mecanismo", "tamano_bytes", "corrida", "intento", "latencia_ms", "ok", "error", "fecha_hora"
)
COLUMNAS_RENDIMIENTO = (
    "mecanismo", "tamano_bytes", "corrida", "mensajes", "duracion_s", "mensajes_por_segundo"
)


def construir_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Planificar, probar la integración o medir TCP/gRPC por separado."
    )
    parser.add_argument("--mecanismo", choices=("ambos", *MECANISMOS), default="ambos")
    parser.add_argument("--tamano", choices=("ambos", "100", "10240"), default="ambos")
    parser.add_argument("--repeticiones", type=int, default=5)
    parser.add_argument("--envios", type=int, default=100)
    parser.add_argument("--calentamiento", type=int, default=1)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--emisor", choices=tuple(PUERTOS_NODOS), default="nodo-A")
    parser.add_argument("--receptor", choices=tuple(PUERTOS_NODOS), default="nodo-B")
    parser.add_argument("--puerto", type=int, default=None,
                        help="Puerto de destino; por defecto, el del nodo receptor.")
    parser.add_argument("--timeout", type=float, default=2.0)
    modos = parser.add_mutually_exclusive_group()
    modos.add_argument("--probar", action="store_true",
                       help="Envia 3 mensajes reales (corrida 0); sin CSV consolidado.")
    modos.add_argument("--ejecutar", action="store_true",
                       help="Ejecuta las corridas completas y escribe CSV consolidados.")
    return parser


def cargar_cliente(mecanismo: str):
    """Importa el cliente existente sin copiar ni alterar archivos de compañeros."""
    carpeta = RAIZ / "src" / ("sockets" if mecanismo == "tcp" else "grpc")
    if not carpeta.is_dir():
        raise FileNotFoundError(f"No existe la carpeta del cliente: {carpeta}")
    if str(carpeta) not in sys.path:
        sys.path.insert(0, str(carpeta))
    if mecanismo == "tcp":
        from client import ClienteTCP
        return ClienteTCP
    from client_grpc import ClienteGRPC
    return ClienteGRPC

def comprobar_acuse(acuse: dict, rtt_ms: float, destino: str) -> None:
    if not isinstance(acuse, dict) or acuse.get("ok") is not True:
        raise RuntimeError(f"El servidor no confirmó el mensaje: {acuse!r}")
    if acuse.get("receiver") != destino:
        raise RuntimeError(f"Acuse del nodo incorrecto: {acuse!r}")
    if not isinstance(rtt_ms, (int, float)) or not math.isfinite(rtt_ms) or rtt_ms < 0:
        raise RuntimeError(f"Latencia devuelta no válida: {rtt_ms!r}")


def mostrar_plan(args: argparse.Namespace) -> None:
    mecanismos = MECANISMOS if args.mecanismo == "ambos" else (args.mecanismo,)
    tamanos = TAMANOS_BYTES if args.tamano == "ambos" else (int(args.tamano),)
    print("PLAN EXPERIMENTAL — SOLO CONFIGURACIÓN (SIN MEDICIONES)")
    print("Nodos:", ", ".join(f"{n}:{p}" for n, p in PUERTOS_NODOS.items()))
    print("RTT tomado del cliente con time.perf_counter().")
    print("Tamaños en bytes de carga útil, NO del mensaje serializado.\n")
    for m in mecanismos:
        for t in tamanos:
            print(f"- {m.upper():4} | {t:5} bytes | "
                  f"{args.repeticiones} corridas x {args.envios} envíos | "
                  f"{args.calentamiento} corrida(s) de calentamiento")
    condiciones = len(mecanismos) * len(tamanos)
    print(f"\nTotal de envíos planificados para medición: "
          f"{condiciones * args.repeticiones * args.envios}")
    print(f"Envíos de calentamiento (no contabilizados): "
          f"{condiciones * args.calentamiento * args.envios}")
    print("Para una prueba real corta, usar --probar con un mecanismo y tamaño.")
    print("Para las mediciones completas, usar --ejecutar; una tecnología a la vez.")

def probar_cliente(args: argparse.Namespace, puerto: int) -> None:
    cliente_clase = cargar_cliente(args.mecanismo)
    carga = "x" * int(args.tamano)
    cliente = cliente_clase(timeout=args.timeout)
    print(f"PRUEBA DE INTEGRACIÓN — {args.mecanismo.upper()} -> "
          f"{args.receptor}:{puerto}, {len(carga)} bytes")
    print("Se enviarán 3 mensajes reales; no son mediciones oficiales.")
    try:
        cliente.conectar(args.host, puerto)
        for intento in range(1, 4):
            acuse, rtt_ms = cliente.enviar(
                args.emisor, args.receptor, carga, intento, 0
            )
            comprobar_acuse(acuse, rtt_ms, args.receptor)
            print(f"{intento}/3 | ok={acuse['ok']} | "
                  f"receiver={acuse['receiver']} | RTT={rtt_ms:.3f} ms")
    finally:
        cliente.cerrar()
    print("PRUEBA SUPERADA. Los clientes generan sus propios logs en data/ (corrida 0).")
    print("No se generaron archivos CSV consolidados del experimento.")
def medir_condicion(args: argparse.Namespace, puerto: int, tamano: int):
    """Ejecuta calentamiento y repeticiones con una conexión reutilizada."""
    cliente_clase = cargar_cliente(args.mecanismo)
    cliente = cliente_clase(timeout=args.timeout)
    carga = "x" * tamano
    filas_latencia = []
    filas_rendimiento = []
    intento_global = 0  # Evita IDs repetidos en una misma conexión.
    try:
        cliente.conectar(args.host, puerto)
        for _ in range(args.calentamiento):
            for _ in range(args.envios):
                intento_global += 1
                acuse, rtt_ms = cliente.enviar(
                    args.emisor, args.receptor, carga, intento_global, 0
                )
                comprobar_acuse(acuse, rtt_ms, args.receptor)
        print(f"Calentamiento completado: {args.calentamiento * args.envios} envíos descartados.")

        for corrida in range(1, args.repeticiones + 1):
            inicio_corrida = time.perf_counter()
            for _ in range(args.envios):
                intento_global += 1
                acuse, rtt_ms = cliente.enviar(
                    args.emisor, args.receptor, carga, intento_global, corrida
                )
                comprobar_acuse(acuse, rtt_ms, args.receptor)
                filas_latencia.append({
                    "mecanismo": args.mecanismo.upper(),
                    "tamano_bytes": tamano,
                    "corrida": corrida,
                    "intento": intento_global,
                    "latencia_ms": f"{rtt_ms:.6f}",
                    "ok": "true",
                    "error": "",
                    "fecha_hora": datetime.now().astimezone().isoformat(timespec="milliseconds"),
                })
            duracion = time.perf_counter() - inicio_corrida
            rendimiento = args.envios / duracion
            filas_rendimiento.append({
                "mecanismo": args.mecanismo.upper(),
                "tamano_bytes": tamano,
                "corrida": corrida,
                "mensajes": args.envios,
                "duracion_s": f"{duracion:.6f}",
                "mensajes_por_segundo": f"{rendimiento:.6f}",
            })
            print(f"{args.mecanismo.upper()} {tamano} B | corrida {corrida}/"
                  f"{args.repeticiones} | {args.envios} acuses | "
                  f"{rendimiento:.2f} mensajes/s")
    finally:
        cliente.cerrar()
    return filas_latencia, filas_rendimiento


def escribir_csv(ruta: Path, columnas: tuple[str, ...], filas: list[dict]) -> None:
    with ruta.open("x", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas)
        escritor.writeheader()
        escritor.writerows(filas)

def ejecutar_experimento(args: argparse.Namespace, puerto: int, tamanos: tuple[int, ...]) -> None:
    sufijo = "sockets" if args.mecanismo == "tcp" else "grpc"
    carpeta = RAIZ / "data"
    ruta_latencia = carpeta / f"latency_{sufijo}.csv"
    ruta_rendimiento = carpeta / f"runs_{sufijo}.csv"
    existentes = [str(r) for r in (ruta_latencia, ruta_rendimiento) if r.exists()]
    if existentes:
        raise FileExistsError("Se protege la evidencia cruda: ya existe(n) "
                              + ", ".join(existentes)
                              + ". Conserva o archiva esos archivos antes de repetir.")
    latencias = []
    rendimientos = []
    print(f"EXPERIMENTO REAL: {args.mecanismo.upper()}, receptor "
          f"{args.receptor}:{puerto}")
    for tamano in tamanos:
        filas_l, filas_r = medir_condicion(args, puerto, tamano)
        latencias.extend(filas_l)
        rendimientos.extend(filas_r)
    carpeta.mkdir(parents=True, exist_ok=True)
    escribir_csv(ruta_latencia, COLUMNAS_LATENCIA, latencias)
    escribir_csv(ruta_rendimiento, COLUMNAS_RENDIMIENTO, rendimientos)
    print(f"Se guardaron {len(latencias)} mediciones y {len(rendimientos)} corridas:")
    print(f"  {ruta_latencia}\n  {ruta_rendimiento}")
    print("No confundir estos CSV con los logs automáticos latencias_*.csv de los clientes.")

def main() -> None:
    parser = construir_parser()
    args = parser.parse_args()
    if args.repeticiones < 5:
        parser.error("La rúbrica exige al menos 5 repeticiones medidas.")
    if args.envios < 100:
        parser.error("La rúbrica exige como mínimo 100 envíos por corrida.")
    if args.calentamiento < 1:
        parser.error("Se requiere al menos una corrida previa de calentamiento.")
    if args.timeout <= 0:
        parser.error("--timeout debe ser mayor que 0.")
    if args.emisor == args.receptor and (args.probar or args.ejecutar):
        parser.error("Emisor y receptor deben identificar nodos distintos.")
    puerto = args.puerto if args.puerto is not None else PUERTOS_NODOS[args.receptor]
    if not 1 <= puerto <= 65535:
        parser.error("El puerto debe estar entre 1 y 65535.")
    if not (args.probar or args.ejecutar):
        mostrar_plan(args)
        return
    if args.mecanismo == "ambos":
        parser.error("Para ejecutar, selecciona --mecanismo tcp o grpc (puertos compartidos).")
    if args.probar and args.tamano == "ambos":
        parser.error("La prueba corta requiere --tamano 100 o --tamano 10240.")
    tamanos = TAMANOS_BYTES if args.tamano == "ambos" else (int(args.tamano),)
    try:
        if args.probar:
            probar_cliente(args, puerto)
        else:
            ejecutar_experimento(args, puerto, tamanos)
    except Exception as exc:
        parser.exit(1, f"ERROR: {type(exc).__name__}: {exc}\n"
                    "Verifica que el servidor esté encendido y las dependencias instaladas.\n")


if __name__ == "__main__":
    main()