"""Pruebas con procesos y TCP/gRPC reales; todos los datos son temporales."""

import csv
import hashlib
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from analysis.analyze_controlled_checks import analyze, read_case


ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(importlib.util.find_spec("grpc"), "grpcio no instalado")
class ControlledChecksTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.data = cls.root / "captures"
        result = subprocess.run([sys.executable, "-B", str(ROOT / "analysis/run_controlled_checks.py"),
            "--output", str(cls.data), "--origin", "test", "--nodes", "2", "3",
            "--repetitions", "1"], cwd=ROOT, capture_output=True, text=True, timeout=90)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)

    def test_failure_keeps_orphan_and_healthy_nodes_continue(self):
        for mechanism in ("tcp", "grpc"):
            row = read_case(self.data / f"failure-{mechanism}-n3-r01")
            self.assertEqual(row["eventos"], 13)
            self.assertEqual(row["envios_sin_recepcion"], 1)
            self.assertEqual((row["reloj_antes"], row["reloj_despues"]), (7, 8))
            self.assertTrue(row["canal_sano_posterior"])

    def test_chains_are_complete_for_both_node_counts(self):
        for mechanism in ("tcp", "grpc"):
            for count in (2, 3):
                row = read_case(self.data / f"propagation-{mechanism}-n{count}-r01")
                self.assertEqual(row["intercambios"], count - 1)
                self.assertEqual(row["eventos"], 4 * (count - 1))
                self.assertGreater(row["duracion_ms"], 0)

    def test_summary_is_generated(self):
        measurements, failures = analyze(self.data, self.root / "summary")
        self.assertEqual(len(measurements), 4)
        self.assertEqual(len(failures), 2)
        self.assertTrue((self.root / "summary/propagacion.tex").exists())
        with self.assertRaises(FileExistsError):
            analyze(self.data, self.root / "summary")

    def test_hash_change_rejected(self):
        with TemporaryDirectory() as temporary:
            target = Path(temporary) / "failure-tcp-n3-r01"
            shutil.copytree(self.data / "failure-tcp-n3-r01", target)
            with (target / "events_nodo-B.csv").open("a") as stream:
                stream.write("alteración de prueba\n")
            with self.assertRaises(ValueError):
                read_case(target)

    def test_additional_clock_error_rejected_even_with_recomputed_hash(self):
        with TemporaryDirectory() as temporary:
            target = Path(temporary) / "failure-tcp-n3-r01"
            shutil.copytree(self.data / "failure-tcp-n3-r01", target)
            path = target / "events_nodo-B.csv"
            with path.open(newline="", encoding="utf-8") as stream:
                reader = csv.DictReader(stream)
                fields, rows = reader.fieldnames, list(reader)
            rows[0]["reloj"] = "999"
            with path.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)
            manifest = target / "SHA256SUMS"
            lines = []
            for line in manifest.read_text().splitlines():
                digest, name = line.split("  ", 1)
                if name == path.name:
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                lines.append(f"{digest}  {name}\n")
            manifest.write_text("".join(lines))
            with self.assertRaises(ValueError):
                read_case(target)

    def test_unplanned_incomplete_case_not_ignored(self):
        with TemporaryDirectory() as temporary:
            data = Path(temporary) / "data"
            shutil.copytree(self.data, data)
            (data / "propagation-tcp-n5-r01").mkdir()
            with self.assertRaises(ValueError):
                analyze(data, Path(temporary) / "summary")


if __name__ == "__main__":
    unittest.main()
