"""Resumen sobre capturas TCP temporales realmente ejecutadas, no fixtures de resultados."""

from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from analysis.summarize_concurrency import summarize


ROOT = Path(__file__).resolve().parents[1]


class ConcurrencySummaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.capture = self.root / "capture"
        result = subprocess.run([
            sys.executable, "-B", str(ROOT / "analysis/run_lamport_experiment.py"),
            "--mechanism", "tcp", "--run-id", "summary-test", "--output", str(self.capture),
            "--base-port", "0"], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_generated_summary_and_tables(self):
        output = self.root / "summary"
        rows = summarize([self.capture], output)
        self.assertEqual(rows[0]["solicitudes"], 20)
        self.assertEqual(rows[0]["acuses"], 20)
        self.assertEqual(rows[0]["eventos"], 80)
        self.assertEqual(rows[0]["errores_causales"], 0)
        for filename in ("resumen.csv", "concurrencia_resumen.tex", "concurrencia_ejemplos.tex",
                         "resumen_concurrencia.md"):
            self.assertTrue((output / filename).is_file())
        with self.assertRaises(FileExistsError):
            summarize([self.capture], output)

    def test_modified_raw_data_rejected(self):
        with (self.capture / "events_nodo-A.csv").open("a") as stream:
            stream.write("alteración de prueba\n")
        with self.assertRaises(ValueError):
            summarize([self.capture], self.root / "bad-summary")
        self.assertFalse((self.root / "bad-summary").exists())

    def test_duplicate_capture_rejected(self):
        with self.assertRaises(ValueError):
            summarize([self.capture, self.capture], self.root / "duplicate-summary")

    def test_empty_input_rejected(self):
        with self.assertRaises(ValueError):
            summarize([], self.root / "empty-summary")


if __name__ == "__main__":
    unittest.main()
