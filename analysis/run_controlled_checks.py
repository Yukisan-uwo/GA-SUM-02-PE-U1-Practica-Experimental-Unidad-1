"""Pruebas reales de caída y recorrido causal; no altera el benchmark del equipo."""

import argparse
from datetime import datetime, timezone
import getpass
import hashlib
from importlib.metadata import PackageNotFoundError, version
import json
import multiprocessing as mp
import os
from pathlib import Path
import platform
import socket
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from src.common.controlled_node import node_worker


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def seal(directory):
    with (directory / "SHA256SUMS").open("x", encoding="ascii") as stream:
        for path in sorted(directory.iterdir()):
            if path.is_file() and path.name != "SHA256SUMS":
                stream.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n")


class Cluster:
    def __init__(self, mechanism, count, run_id, directory, timeout):
        self.processes, self.controls, self.info = {}, {}, {}
        self.timeout = timeout
        self.context = mp.get_context("spawn")
        self.mechanism, self.count, self.run_id = mechanism, count, run_id
        self.directory = directory

    def receive(self, node):
        if not self.controls[node].poll(self.timeout + 15):
            raise TimeoutError(f"No respondió el proceso de {node}")
        return self.controls[node].recv()

    def __enter__(self):
        try:
            for rank in range(self.count):
                name = "nodo-" + chr(ord("A") + rank)
                parent, child = self.context.Pipe()
                process = self.context.Process(target=node_worker,
                    args=(name, self.mechanism, self.run_id, str(self.directory), self.timeout, child))
                process.start()
                child.close()
                self.processes[name], self.controls[name] = process, parent
            for name in self.processes:
                info = self.receive(name)
                if not info.get("ok"):
                    raise RuntimeError(str(info))
                self.info[name] = info
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def send(self, origin, destination, attempt):
        self.controls[origin].send({"action": "send", "to": destination,
                                   "port": self.info[destination]["port"], "attempt": attempt})
        result = self.receive(origin)
        result.update(origin=origin, destination=destination, attempt=attempt)
        return result

    def kill(self, node):
        process = self.processes[node]
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            raise RuntimeError("El nodo no terminó")
        return {"node": node, "pid": process.pid, "exitcode": process.exitcode,
                "utc": datetime.now(timezone.utc).isoformat()}

    def __exit__(self, *_):
        for name, process in self.processes.items():
            if process.is_alive():
                try:
                    self.controls[name].send({"action": "stop"})
                except (OSError, EOFError):
                    pass
        for name, process in self.processes.items():
            process.join(timeout=self.timeout + 3)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
            self.controls[name].close()


def run_case(mechanism, count, repetition, mode, root, timeout):
    run_id = f"{mode}-{mechanism}-n{count}-r{repetition:02d}"
    directory = root / run_id
    directory.mkdir(exist_ok=False)
    commands = []
    with Cluster(mechanism, count, run_id, directory, timeout) as cluster:
        if mode == "failure":
            commands += [cluster.send("nodo-A", "nodo-B", 1), cluster.send("nodo-B", "nodo-C", 1)]
            if not all(c["ok"] for c in commands):
                raise RuntimeError("Falló la comunicación previa a la caída")
            killed = cluster.kill("nodo-C")
            commands.append(cluster.send("nodo-B", "nodo-C", 2))
            commands.append(cluster.send("nodo-A", "nodo-B", 2))
            ok = (not commands[2]["ok"] and commands[2].get("phase") == "send" and commands[3]["ok"])
            result = {"ok": ok, "mode": mode, "run_id": run_id, "mechanism": mechanism,
                      "nodes": cluster.info, "killed": killed, "commands": commands,
                      "expected_orphan": f"{run_id}:nodo-B-000002"}
        else:
            names = list(cluster.info)
            started = time.perf_counter_ns()
            for origin, destination in zip(names, names[1:]):
                commands.append(cluster.send(origin, destination, 1))
            elapsed = time.perf_counter_ns() - started
            result = {"ok": all(c["ok"] for c in commands), "mode": mode, "run_id": run_id,
                      "mechanism": mechanism, "nodes": cluster.info, "commands": commands,
                      "node_count": count, "repetition": repetition, "chain_elapsed_ns": elapsed,
                      "metric": "N-1 intercambios secuenciales coordinados; incluye IPC, conexiones y acuses"}
    write_json(directory / "result.json", result)
    seal(directory)
    print(run_id, "OK" if result["ok"] else "ERROR", flush=True)
    if not result["ok"]:
        raise RuntimeError(f"Caso incompleto: {directory}")
    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--mode", choices=("all", "failure", "propagation"), default="all")
    parser.add_argument("--mechanism", choices=("both", "tcp", "grpc"), default="both")
    parser.add_argument("--nodes", nargs="+", type=int, default=[2, 3, 5])
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=2)
    parser.add_argument("--origin", choices=("assisted", "personal", "test"), required=True)
    args = parser.parse_args()
    if (not 0 < args.timeout <= 30 or args.repetitions < 1 or
            any(not 2 <= n <= 10 for n in args.nodes) or len(set(args.nodes)) != len(args.nodes)):
        parser.error("Se requieren timeout (0,30], repeticiones positivas y nodos únicos entre 2 y 10")
    args.output.mkdir(parents=True, exist_ok=False)
    libraries = {}
    for name in ("grpcio", "grpcio-tools", "protobuf", "pandas", "matplotlib"):
        try:
            libraries[name] = version(name)
        except PackageNotFoundError:
            libraries[name] = None
    machine = {"processor": platform.processor() or "no informado", "memory_bytes": None}
    if machine["processor"] == "no informado" and Path("/proc/cpuinfo").is_file():
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                machine["processor"] = line.split(":", 1)[1].strip()
                break
    try:
        machine["memory_bytes"] = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (AttributeError, OSError, ValueError):
        pass
    write_json(args.output / "environment.json", {
        "utc": datetime.now(timezone.utc).isoformat(), "user": getpass.getuser(),
        "hostname": socket.gethostname(), "os": platform.platform(), "python": sys.version,
        "origin_declaration": args.origin, "libraries": libraries, **machine,
        "warning": "Origen declarado, no certificación de participación humana",
        "configuration": dict(vars(args), output=str(args.output))})
    mechanisms = ("tcp", "grpc") if args.mechanism == "both" else (args.mechanism,)
    for mechanism in mechanisms:
        if args.mode in ("all", "failure"):
            run_case(mechanism, 3, 1, "failure", args.output, args.timeout)
        if args.mode in ("all", "propagation"):
            for count in args.nodes:
                for repetition in range(1, args.repetitions + 1):
                    run_case(mechanism, count, repetition, "propagation", args.output, args.timeout)
    with (args.output / "SHA256SUMS").open("x", encoding="ascii") as stream:
        for path in sorted(p for p in args.output.rglob("*") if p.is_file() and p != args.output / "SHA256SUMS"):
            stream.write(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(args.output).as_posix()}\n")
    print("Capturas conservadas en", args.output)


if __name__ == "__main__":
    main()
