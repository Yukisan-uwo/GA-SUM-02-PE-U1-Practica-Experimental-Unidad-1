"""Comprueba el reporte contra las capturas publicadas, sin modificar los originales."""

from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from analysis.report_twenty_exchanges import generate


ROOT = Path(__file__).resolve().parents[1]
GRPC = ROOT / "data/lamport20/grpc-20261121-002802"
TCP = ROOT / "data/lamport20/tcp-20261121-003058"


class TwentyExchangeReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_reproduces_actual_capture_counts(self):
        output = self.root / "report"
        rows = generate(GRPC, TCP, output)
        self.assertEqual([r["mecanismo"] for r in rows], ["gRPC", "TCP"])
        for row in rows:
            self.assertEqual((row["solicitudes"], row["acuses"], row["eventos"], row["pares"]),
                             (20, 20, 80, 40))
        report = (output / "resumen.md").read_text()
        self.assertIn("2026-11-21T00:28:09", report)
        self.assertIn("2026-11-21T00:31:03", report)
        self.assertTrue((output / "nodos.csv").exists())

    def test_does_not_overwrite_report(self):
        output = self.root / "report"
        generate(GRPC, TCP, output)
        with self.assertRaises(FileExistsError):
            generate(GRPC, TCP, output)

    def test_wrong_mechanism_rejected(self):
        with self.assertRaises(ValueError):
            generate(TCP, GRPC, self.root / "invalid")
        self.assertFalse((self.root / "invalid").exists())

    def test_modified_copy_rejected(self):
        copy = self.root / "modified"
        shutil.copytree(GRPC, copy)
        with (copy / "events_nodo-A.csv").open("a") as stream:
            stream.write("alteración de prueba\n")
        with self.assertRaises(ValueError):
            generate(copy, TCP, self.root / "invalid")


if __name__ == "__main__":
    unittest.main()
