"""Servidor gRPC de un nodo (nodo-A, nodo-B o nodo-C)."""
import argparse
import threading
import time
from concurrent import futures
from datetime import datetime

import grpc

import messaging_pb2
import messaging_pb2_grpc

PUERTOS = {"nodo-A": 5000, "nodo-B": 5001, "nodo-C": 5002}


class RelojTemporal:
    """Reloj de Lamport provisional, se reemplaza por el modulo de Roger."""

    def __init__(self):
        self.valor = 0
        self._lock = threading.Lock()

    def enviar(self):
        with self._lock:
            self.valor += 1
            return self.valor

    def recibir(self, recibido):
        with self._lock:
            self.valor = max(self.valor, recibido) + 1
            return self.valor


class MessagingServicer(messaging_pb2_grpc.MessagingServiceServicer):
    def __init__(self, nombre, reloj, mostrar=True):
        self.nombre = nombre
        self.reloj = reloj
        self.mostrar = mostrar

    def EnviarMensaje(self, request, context):
        nuevo = self.reloj.recibir(request.timestamp)
        if self.mostrar:
            hora = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            print(f"[{self.nombre}] {hora} recepcion de {request.sender} "
                  f"ts={request.timestamp} -> reloj={nuevo} "
                  f"({len(request.message)} bytes)")
        return messaging_pb2.Response(receiver=self.nombre, timestamp=nuevo, ok=True)


def iniciar_servidor(nombre, reloj, mostrar=True):
    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    messaging_pb2_grpc.add_MessagingServiceServicer_to_server(
        MessagingServicer(nombre, reloj, mostrar), servidor)
    servidor.add_insecure_port(f"127.0.0.1:{PUERTOS[nombre]}")
    servidor.start()
    return servidor


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("nodo", choices=list(PUERTOS))
    parser.add_argument("--silencioso", action="store_true",
                        help="no imprime cada mensaje (para medir latencia)")
    args = parser.parse_args()

    servidor = iniciar_servidor(args.nodo, RelojTemporal(), not args.silencioso)
    print(f"[{args.nodo}] servidor gRPC escuchando en 127.0.0.1:{PUERTOS[args.nodo]}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"[{args.nodo}] deteniendo servidor")
        servidor.stop(grace=1)


if __name__ == "__main__":
    main()