"""Nodo de prueba controlado por IPC; servidor y cliente comparten reloj real."""

from concurrent.futures import ThreadPoolExecutor
import importlib
import os
from pathlib import Path
import socket
import threading
import time

from .event_log import EventLog
from .lamport import LamportClock
from .node_experiment import _load


def node_worker(name, mechanism, run_id, output, timeout, control):
    listener = server = log = None
    accept_thread = None
    stop = threading.Event()
    connections, threads, clients = [], [], {}
    errors = []
    try:
        clock = LamportClock()
        log = EventLog(Path(output) / f"events_{name}.csv", name,
                       "TCP" if mechanism == "tcp" else "gRPC", run_id, clock)
        client_module, server_module = _load(mechanism)
        if mechanism == "tcp":
            client_class = client_module.ClienteTCP
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            listener.settimeout(0.1)
            port = listener.getsockname()[1]

            def serve(connection):
                try:
                    connection.settimeout(timeout * 10)
                    server_module.serve_client(connection, name, clock, quiet=True,
                                               log_events=False, event_log=log)
                except Exception as exc:
                    errors.append(str(exc))

            def accept():
                while not stop.is_set():
                    try:
                        connection, _ = listener.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        return
                    connections.append(connection)
                    worker = threading.Thread(target=serve, args=(connection,), daemon=True)
                    threads.append(worker)
                    worker.start()

            accept_thread = threading.Thread(target=accept, daemon=True)
            accept_thread.start()
        else:
            import grpc
            client_class = client_module.ClienteGRPC
            pb_grpc = importlib.import_module("messaging_pb2_grpc")
            server = grpc.server(ThreadPoolExecutor(max_workers=10),
                                 options=(("grpc.so_reuseport", 0),))
            pb_grpc.add_MessagingServiceServicer_to_server(
                server_module.MessagingServicer(name, clock, silencioso=True, event_log=log), server)
            port = server.add_insecure_port("127.0.0.1:0")
            if not port:
                raise OSError("No se pudo reservar un puerto")
            server.start()
        control.send({"ok": True, "node": name, "pid": os.getpid(), "port": port})
        while True:
            command = control.recv()
            if command["action"] == "stop":
                control.send({"ok": not errors, "node": name, "clock": clock.value,
                              "server_errors": errors})
                break
            if command["action"] != "send":
                raise ValueError("Acción de control desconocida")
            before = clock.value
            started = time.perf_counter_ns()
            phase = "connect"
            try:
                key = command["to"]
                if key not in clients:
                    client = client_class(timeout=timeout, clock=clock, event_log=log)
                    clients[key] = client
                    client.conectar("127.0.0.1", command["port"])
                phase = "send"
                ack, _ = clients[key].enviar(name, key, "x" * 100, command["attempt"], 0)
                control.send({"ok": True, "node": name, "clock_before": before,
                              "clock_after": clock.value, "receiver": ack["receiver"],
                              "ack_clock": ack["timestamp"],
                              "elapsed_ns": time.perf_counter_ns() - started})
            except Exception as exc:
                code = getattr(exc, "code", None)
                status = code().name if callable(code) else ""
                control.send({"ok": False, "node": name, "phase": phase,
                              "clock_before": before, "clock_after": clock.value,
                              "error": type(exc).__name__, "status": status, "detail": str(exc),
                              "elapsed_ns": time.perf_counter_ns() - started})
    except Exception as exc:
        try:
            control.send({"ok": False, "node": name, "error": repr(exc)})
        except (OSError, EOFError):
            pass
    finally:
        for client in clients.values():
            client.cerrar()
        stop.set()
        if accept_thread:
            accept_thread.join(timeout=1)
        if listener:
            listener.close()
        for connection in connections:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            connection.close()
        for worker in threads:
            worker.join(timeout=1)
        if server:
            server.stop(grace=0).wait(timeout=5)
        if log:
            log.close()
        control.close()
