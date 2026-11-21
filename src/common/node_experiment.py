"""Ejecución funcional concurrente: tres procesos, un reloj por nodo."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import getpass
import hashlib
import importlib
from importlib.metadata import PackageNotFoundError, version
import json
import multiprocessing as mp
from pathlib import Path
import platform
import queue
import re
import socket
import sys
import threading
import time
import uuid

from .event_log import EventLog
from .lamport import LamportClock


ROOT = Path(__file__).resolve().parents[2]
NODES = ("nodo-A", "nodo-B", "nodo-C")


def _load(mechanism):
    folder = ROOT / "src" / ("sockets" if mechanism == "tcp" else "grpc")
    sys.path.insert(0, str(folder))
    if mechanism == "tcp":
        return importlib.import_module("client"), importlib.import_module("server")
    return importlib.import_module("client_grpc"), importlib.import_module("server_grpc")


def _worker(rank, config, ports, ready, first_send, finished, results):
    listener = grpc_server = log = client = None
    stop = threading.Event()
    tcp_workers, failures = [], []
    accept_thread = None
    try:
        import os
        node = NODES[rank]
        clock = LamportClock()
        log = EventLog(Path(config["output"]) / f"events_{node}.csv", node,
                       "TCP" if config["mechanism"] == "tcp" else "gRPC",
                       config["run_id"], clock)
        client_module, server_module = _load(config["mechanism"])
        requested_port = config["base_port"] + rank if config["base_port"] else 0
        if config["mechanism"] == "tcp":
            listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listener.bind(("127.0.0.1", requested_port))
            listener.listen()
            listener.settimeout(0.2)
            ports[rank] = listener.getsockname()[1]

            def serve(connection):
                try:
                    connection.settimeout(config["timeout"] * 4)
                    server_module.serve_client(connection, node, clock, quiet=True,
                                               log_events=False, event_log=log)
                except Exception as exc:
                    failures.append(str(exc))

            def accept():
                while not stop.is_set():
                    try:
                        connection, _ = listener.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        if not stop.is_set():
                            failures.append("Error en accept")
                        return
                    thread = threading.Thread(target=serve, args=(connection,), daemon=True)
                    tcp_workers.append(thread)
                    thread.start()

            accept_thread = threading.Thread(target=accept, daemon=True)
            accept_thread.start()
            client_class = client_module.ClienteTCP
        else:
            import grpc
            pb_grpc = importlib.import_module("messaging_pb2_grpc")
            grpc_server = grpc.server(ThreadPoolExecutor(max_workers=10),
                                      options=(("grpc.so_reuseport", 0),))
            pb_grpc.add_MessagingServiceServicer_to_server(
                server_module.MessagingServicer(node, clock, silencioso=True, event_log=log),
                grpc_server)
            ports[rank] = grpc_server.add_insecure_port(f"127.0.0.1:{requested_port}")
            if not ports[rank]:
                raise OSError("No se pudo reservar el puerto gRPC")
            grpc_server.start()
            client_class = client_module.ClienteGRPC

        print(f"{node} | PID={os.getpid()} | {getpass.getuser()}@{socket.gethostname()} | "
              f"{datetime.now(timezone.utc).isoformat()} | puerto={ports[rank]}", flush=True)
        ready.wait()
        peer = (rank + 1) % 3
        count = config["messages"] // 3 + (rank < config["messages"] % 3)
        client = client_class(timeout=config["timeout"], clock=clock, event_log=log,
                              first_send_barrier=first_send)
        client.conectar("127.0.0.1", ports[peer])
        for attempt in range(1, count + 1):
            ack, _ = client.enviar(node, NODES[peer], "x" * config["size_bytes"], attempt, 0)
            if ack["ok"] is not True:
                raise RuntimeError("Solicitud no confirmada")
        client.cerrar()
        client = None
        # Nadie detiene su servidor mientras otro nodo pueda esperar un acuse.
        finished.wait()
        if failures:
            raise RuntimeError("; ".join(failures))
        results.put({"node": node, "pid": os.getpid(), "port": ports[rank],
                     "requests_sent": count, "clock": clock.value, "ok": True})
    except Exception as exc:
        results.put({"node": NODES[rank], "ok": False,
                     "error": f"{type(exc).__name__}: {exc}"})
        for barrier in (ready, first_send, finished):
            try:
                barrier.abort()
            except Exception:
                pass
    finally:
        if client is not None:
            client.cerrar()
        stop.set()
        if accept_thread:
            accept_thread.join(timeout=1)
        if listener:
            listener.close()
        for thread in tcp_workers:
            thread.join(timeout=config["timeout"] * 4 + 1)
        if grpc_server:
            grpc_server.stop(grace=0).wait(timeout=5)
        if log:
            log.close()


def _write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def run(config):
    output = Path(config["output"]).resolve()
    output.mkdir(parents=True, exist_ok=False)
    config = dict(config, output=str(output))
    environment = {
        "utc": datetime.now(timezone.utc).isoformat(), "user": getpass.getuser(),
        "hostname": socket.gethostname(), "os": platform.platform(),
        "processor": platform.processor() or "no informado por platform.processor",
        "python": sys.version, "execution": "tres procesos localhost; hilos por servidor",
        "configuration": config,
        "purpose": "prueba funcional concurrente; no benchmark de latencia",
    }
    environment["libraries"] = {}
    for name in ("grpcio", "grpcio-tools", "protobuf", "pandas", "matplotlib"):
        try:
            environment["libraries"][name] = version(name)
        except PackageNotFoundError:
            environment["libraries"][name] = None
    if not platform.processor() and Path("/proc/cpuinfo").is_file():
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                environment["processor"] = line.split(":", 1)[1].strip()
                break
    try:
        import os
        environment["memory_bytes"] = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, ValueError, OSError):
        environment["memory_bytes"] = None
    _write_json(output / "environment.json", environment)
    context = mp.get_context("spawn")
    ports = context.Array("i", 3)
    barrier_timeout = config["timeout"] * (config["messages"] + 5)
    barriers = [context.Barrier(3, timeout=barrier_timeout) for _ in range(3)]
    results_queue = context.Queue()
    processes = [context.Process(target=_worker, args=(rank, config, ports, *barriers, results_queue),
                                 name=NODES[rank]) for rank in range(3)]
    outcomes = []
    try:
        for process in processes:
            process.start()
        deadline = time.monotonic() + barrier_timeout + 15
        for process in processes:
            process.join(timeout=max(0, deadline - time.monotonic()))
        for _ in processes:
            try:
                outcomes.append(results_queue.get(timeout=2))
            except queue.Empty:
                break
    finally:
        for process in processes:
            if process.pid and process.is_alive():
                process.terminate()
                process.join(timeout=5)
        results_queue.close()
    ok = (len(outcomes) == 3 and all(x["ok"] for x in outcomes)
          and all(p.exitcode == 0 for p in processes))
    result = {"ok": ok, "nodes": sorted(outcomes, key=lambda r: r["node"]),
              "exitcodes": [p.exitcode for p in processes]}
    _write_json(output / "run_result.json", result)
    if not ok:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    # Importación tardía para que los hijos no dependan del analizador.
    from analysis.verify_lamport import verify
    report = verify([output / f"events_{node}.csv" for node in NODES])
    if report["ejemplo_relojes_iguales"] is None:
        report["valido"] = False
        report["errores"].append("No se encontró el ejemplo de marcas iguales")
    _write_json(output / "verification.json", report)
    with (output / "SHA256SUMS").open("x", encoding="ascii") as stream:
        for path in sorted(output.iterdir()):
            if path.name != "SHA256SUMS" and path.is_file():
                stream.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"Datos de ejecución: {output}")
    return 0 if report["valido"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mechanism", required=True, choices=("tcp", "grpc"))
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--run-id", default="r-" + uuid.uuid4().hex)
    parser.add_argument("--messages", type=int, default=20, help="Total entre los tres nodos")
    parser.add_argument("--size-bytes", type=int, default=100, help="Carga ASCII, no bytes en cable")
    parser.add_argument("--base-port", type=int, default=5000, help="0 usa puertos libres para tests")
    parser.add_argument("--timeout", type=float, default=5)
    args = parser.parse_args()
    if args.messages < 3 or args.size_bytes < 1 or not 0 < args.timeout <= 60:
        parser.error("Se requieren >=3 mensajes, tamaño positivo y timeout en (0, 60]")
    if args.base_port != 0 and not 1 <= args.base_port <= 65533:
        parser.error("El puerto base debe permitir tres puertos consecutivos")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_id):
        parser.error("run-id admite letras ASCII, dígitos, guion y guion bajo")
    try:
        return run(vars(args))
    except (OSError, ImportError) as exc:
        parser.exit(1, f"ERROR: {exc}\nNo sobrescribas la carpeta; usa otra para repetir.\n")


if __name__ == "__main__":
    raise SystemExit(main())
