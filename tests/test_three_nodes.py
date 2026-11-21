"""Integración en red real con datos temporales; no es benchmark ni evidencia final."""

import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analysis/run_lamport_experiment.py"


class ThreeNodesTests(unittest.TestCase):
    def execute(self, mechanism, size):
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "capture"
            command = [sys.executable, "-B", str(SCRIPT), "--mechanism", mechanism,
                       "--output", str(output), "--run-id", "unit-r01", "--base-port", "0",
                       "--size-bytes", str(size)]
            result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            report = json.loads((output / "verification.json").read_text())
            nodes = json.loads((output / "run_result.json").read_text())
            self.assertTrue(report["valido"], report)
            self.assertEqual(report["eventos"], 80)
            self.assertEqual(report["pares_evaluados"], 40)
            self.assertIsNotNone(report["ejemplo_relojes_iguales"])
            self.assertEqual(len({node["pid"] for node in nodes["nodes"]}), 3)
            self.assertEqual([n["requests_sent"] for n in nodes["nodes"]], [7, 7, 6])
            self.assertEqual(len({node["port"] for node in nodes["nodes"]}), 3)
            for line in (output / "SHA256SUMS").read_text().splitlines():
                expected, filename = line.split("  ", 1)
                self.assertEqual(hashlib.sha256((output / filename).read_bytes()).hexdigest(), expected)
            with (output / "events_nodo-A.csv").open(newline="", encoding="utf-8") as stream:
                first = next(csv.DictReader(stream))
            self.assertEqual(first["reloj"], "1")
            # El segundo intento no puede sobrescribir datos de una ejecución.
            old_hash = hashlib.sha256((output / "events_nodo-A.csv").read_bytes()).hexdigest()
            repeated = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(hashlib.sha256((output / "events_nodo-A.csv").read_bytes()).hexdigest(), old_hash)

    def test_tcp_short(self):
        self.execute("tcp", 100)

    def test_tcp_long(self):
        self.execute("tcp", 10240)

    @unittest.skipUnless(importlib.util.find_spec("grpc"), "grpcio no instalado")
    def test_grpc_short(self):
        self.execute("grpc", 100)

    @unittest.skipUnless(importlib.util.find_spec("grpc"), "grpcio no instalado")
    def test_grpc_long(self):
        self.execute("grpc", 10240)

    def test_invalid_arguments_do_not_start_capture(self):
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "invalid"
            command = [sys.executable, "-B", str(SCRIPT), "--mechanism", "tcp",
                       "--output", str(output), "--messages", "2"]
            result = subprocess.run(command, capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
