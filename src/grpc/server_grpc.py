"""Servidor gRPC de un nodo (nodo-A, nodo-B o nodo-C).

Ejecutar desde la raiz del repositorio:
    python src/grpc/server_grpc.py nodo-B
"""
import argparse
import sys
import threading
import time
from concurrent import futures
from pathlib import Path

import grpc

import messaging_pb2
import messaging_pb2_grpc
from registro_grpc import registrar_evento

# Se agrega la raiz del repo al path para usar el reloj compartido de Roger.
RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
from src.common.lamport import LamportClock  # noqa: E402

PUERTOS = {"nodo-A": 5000, "nodo-B": 5001, "nodo-C": 5002}


class MessagingServicer(messaging_pb2_grpc.MessagingServiceServicer):
    def __init__(self, nombre, reloj, silencioso=False, *, event_log=None):
        self.nombre = nombre
        self.reloj = reloj
        self.silencioso = silencioso
        self.event_log = event_log
        if event_log is not None and event_log.clock is not reloj:
            raise ValueError("Servidor y registro deben compartir la misma instancia de reloj")
        # Numero de mensaje por conexion y emisor, igual que en TCP,
        # para que el id_mensaje coincida con el del cliente.
        self.contadores = {}
        self.candado = threading.Lock()

    def _siguiente_id(self, peer, sender):
        with self.candado:
            clave = (peer, sender)
            self.contadores[clave] = self.contadores.get(clave, 0) + 1
            return f"{sender}-{self.contadores[clave]:06d}"

    def EnviarMensaje(self, request, context):
        try:
            if self.event_log is not None:
                metadata = dict(context.invocation_metadata())
                id_mensaje = metadata.get("x-message-id")
                if metadata.get("x-run-id") != self.event_log.run:
                    raise ValueError("La corrida no corresponde al servidor")
                ts_recepcion = self.event_log.record(
                    "recepcion_solicitud", id_mensaje, request.sender, self.nombre,
                    remote=request.timestamp)
            else:
                ts_recepcion = self.reloj.receive(request.timestamp)
        except (TypeError, ValueError) as error:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(error))

        if self.event_log is None:
            id_mensaje = self._siguiente_id(context.peer(), request.sender)
        if not self.silencioso and self.event_log is None:
            registrar_evento(self.nombre, "recepcion_solicitud", ts_recepcion,
                             id_mensaje, request.sender, self.nombre)
            print(f"RECEPCION {request.sender} -> {self.nombre}: reloj={ts_recepcion}, "
                  f"bytes={len(request.message.encode('utf-8'))}")

        # Enviar el acuse es un evento nuevo, por eso se incrementa el reloj.
        ts_acuse = (self.event_log.record("envio_acuse", id_mensaje, self.nombre, request.sender)
                    if self.event_log is not None else self.reloj.tick())
        if not self.silencioso and self.event_log is None:
            registrar_evento(self.nombre, "envio_acuse", ts_acuse,
                             id_mensaje, self.nombre, request.sender)
            print(f"ENVIO_ACUSE {self.nombre} -> {request.sender}: reloj={ts_acuse}")

        return messaging_pb2.Response(receiver=self.nombre, timestamp=ts_acuse, ok=True)


def iniciar_servidor(nombre, reloj, silencioso=False):
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messaging_pb2_grpc.add_MessagingServiceServicer_to_server(
        MessagingServicer(nombre, reloj, silencioso), servidor)
    servidor.add_insecure_port(f"127.0.0.1:{PUERTOS[nombre]}")
    servidor.start()
    return servidor


def main():
    parser = argparse.ArgumentParser(description="Servidor gRPC de la PE-U1")
    parser.add_argument("nodo", choices=list(PUERTOS))
    parser.add_argument("--silencioso", action="store_true",
                        help="no imprime ni registra eventos (para medir latencia)")
    args = parser.parse_args()

    servidor = iniciar_servidor(args.nodo, LamportClock(), args.silencioso)
    print(f"[{args.nodo}] servidor gRPC escuchando en 127.0.0.1:{PUERTOS[args.nodo]}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"[{args.nodo}] deteniendo servidor")
        servidor.stop(grace=1)


if __name__ == "__main__":
    main()
