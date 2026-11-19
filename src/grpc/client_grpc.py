"""Cliente gRPC con la misma interfaz que ClienteTCP (conectar/enviar/cerrar).

Ejecutar desde la raiz del repositorio:
    python src/grpc/client_grpc.py --sender nodo-A --receiver nodo-B --size-bytes 100 --count 20 --run 0
"""
import argparse
import sys
import time
from pathlib import Path

import grpc

import messaging_pb2
import messaging_pb2_grpc
from registro_grpc import registrar_evento, registrar_latencia

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
from src.common.lamport import LamportClock  # noqa: E402

PUERTOS = {"nodo-A": 5000, "nodo-B": 5001, "nodo-C": 5002}

# Codigos de gRPC traducidos a los tipos de error acordados con TCP.
ERRORES = {
    grpc.StatusCode.DEADLINE_EXCEEDED: "timeout",
    grpc.StatusCode.UNAVAILABLE: "conexion_rechazada",
}


def generar_mensaje(tamano_bytes):
    """Misma carga que en TCP: tamano_bytes caracteres ASCII."""
    return "x" * tamano_bytes


class ClienteGRPC:
    def __init__(self, timeout=2.0, registrar_eventos=True):
        self.timeout = timeout
        self.registrar_eventos = registrar_eventos
        self.canal = None
        self.stub = None
        self.clock = LamportClock()

    def conectar(self, host, puerto):
        if self.canal is not None:
            raise RuntimeError("El cliente ya tiene un canal abierto")
        self.canal = grpc.insecure_channel(f"{host}:{puerto}")
        # Se espera a que el canal este listo para que la conexion
        # no se cuente dentro de la latencia del primer envio.
        grpc.channel_ready_future(self.canal).result(timeout=self.timeout)
        self.stub = messaging_pb2_grpc.MessagingServiceStub(self.canal)

    def enviar(self, sender, destination, message, attempt, run_number):
        if self.stub is None:
            raise RuntimeError("Primero debes llamar a conectar()")

        ts_envio = self.clock.send()
        id_mensaje = f"{sender}-{attempt:06d}"
        tamano = len(message.encode("utf-8"))
        if self.registrar_eventos:
            registrar_evento(sender, "envio_solicitud", ts_envio, id_mensaje, sender, destination)
        solicitud = messaging_pb2.Request(sender=sender, timestamp=ts_envio, message=message)

        inicio = time.perf_counter()
        try:
            acuse = self.stub.EnviarMensaje(solicitud, timeout=self.timeout)
        except grpc.RpcError as error:
            latencia_ms = (time.perf_counter() - inicio) * 1000
            tipo = ERRORES.get(error.code(), "otro")
            registrar_latencia(tamano, run_number, attempt, latencia_ms, False, tipo)
            raise
        latencia_ms = (time.perf_counter() - inicio) * 1000

        ts_recepcion = self.clock.receive(acuse.timestamp)
        if self.registrar_eventos:
            registrar_evento(sender, "recepcion_acuse", ts_recepcion, id_mensaje,
                             acuse.receiver, sender)
        registrar_latencia(tamano, run_number, attempt, latencia_ms, acuse.ok)
        respuesta = {"receiver": acuse.receiver, "timestamp": acuse.timestamp, "ok": acuse.ok}
        return respuesta, latencia_ms

    def cerrar(self):
        if self.canal is not None:
            self.canal.close()
            self.canal = None
            self.stub = None

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.cerrar()


def main():
    parser = argparse.ArgumentParser(description="Cliente gRPC de la PE-U1")
    parser.add_argument("--sender", default="nodo-A", choices=list(PUERTOS))
    parser.add_argument("--receiver", default="nodo-B", choices=list(PUERTOS))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--message", help="texto fijo para una prueba funcional")
    parser.add_argument("--size-bytes", type=int, help="genera un mensaje de este tamano")
    parser.add_argument("--count", type=int, default=1, help="cantidad de envios")
    parser.add_argument("--timeout", type=float, default=2.0)
    parser.add_argument("--run", type=int, default=1, help="corrida (0 = calentamiento)")
    args = parser.parse_args()

    if args.message is not None and args.size_bytes is not None:
        parser.error("elige --message o --size-bytes, no ambos")
    if args.size_bytes is not None:
        mensaje = generar_mensaje(args.size_bytes)
    else:
        mensaje = args.message if args.message is not None else "Hola"

    puerto = PUERTOS[args.receiver]
    with ClienteGRPC(timeout=args.timeout) as cliente:
        try:
            cliente.conectar(args.host, puerto)
        except grpc.FutureTimeoutError:
            print(f"No se pudo conectar con {args.receiver} en {args.host}:{puerto}")
            sys.exit(1)
        for i in range(1, args.count + 1):
            try:
                acuse, latencia = cliente.enviar(args.sender, args.receiver, mensaje, i, args.run)
            except grpc.RpcError as error:
                print(f"{i}/{args.count} | ERROR {error.code().name}: {error.details()}")
                continue
            print(f"{i}/{args.count} | acuse={acuse} | "
                  f"reloj_local={cliente.clock.value} | RTT={latencia:.3f} ms")


if __name__ == "__main__":
    main()