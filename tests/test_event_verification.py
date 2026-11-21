"""Fixtures temporales: no son evidencia experimental TCP/gRPC."""

import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from analysis.verify_lamport import verify
from src.common.event_log import EVENT_FIELDS, EventLog
from src.common.lamport import LamportClock


class EventVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def fixture(self, mechanism="TCP"):
        """Tres emisores con reloj independiente; intercambio funcional local."""
        names = ["nodo-A", "nodo-B", "nodo-C"]
        paths = [self.root / f"{mechanism}-{node}.csv" for node in names]
        logs = [EventLog(path, node, mechanism, "r01", LamportClock())
                for node, path in zip(names, paths)]
        try:
            sent, acks = [], []
            for i in range(3):
                sent.append(logs[i].record("envio_solicitud", f"m{i}",
                                          names[i], names[(i + 1) % 3]))
            for i in range(3):
                j = (i + 1) % 3
                logs[j].record("recepcion_solicitud", f"m{i}", names[i], names[j], sent[i])
                acks.append(logs[j].record("envio_acuse", f"m{i}", names[j], names[i]))
            for i in range(3):
                logs[i].record("recepcion_acuse", f"m{i}", names[(i + 1) % 3],
                               names[i], acks[i])
        finally:
            for log in logs:
                log.close()
        return paths

    def edit(self, path, change):
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        change(rows)
        with path.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=EVENT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)

    def test_complete_both_mechanisms(self):
        paths = self.fixture() + self.fixture("gRPC")
        report = verify(paths)
        self.assertTrue(report["valido"], report)
        self.assertEqual(report["eventos"], 24)
        self.assertEqual(report["pares_evaluados"], 12)
        self.assertIsNotNone(report["ejemplo_relojes_iguales"])

    def test_missing_event(self):
        paths = self.fixture()
        self.edit(paths[0], lambda rows: rows.pop())
        self.assertFalse(verify(paths)["valido"])

    def test_duplicate_file(self):
        paths = self.fixture()
        self.assertFalse(verify(paths + [paths[0]])["valido"])

    def test_wrong_clock(self):
        paths = self.fixture()
        self.edit(paths[0], lambda rows: rows[0].update(reloj="9"))
        report = verify(paths)
        self.assertFalse(report["valido"])
        self.assertIsNone(report["ejemplo_relojes_iguales"])

    def test_wrong_remote_timestamp(self):
        paths = self.fixture()
        self.edit(paths[0], lambda rows: rows[1].update(reloj_remoto="99"))
        self.assertFalse(verify(paths)["valido"])

    def test_wrong_endpoint(self):
        paths = self.fixture()
        self.edit(paths[0], lambda rows: rows[0].update(origen="otro"))
        self.assertFalse(verify(paths)["valido"])

    def test_duplicate_sequence(self):
        paths = self.fixture()
        self.edit(paths[0], lambda rows: rows[1].update(secuencia="1"))
        self.assertFalse(verify(paths)["valido"])

    def test_invalid_clock_value(self):
        for invalid in ("True", "-1", "1.5", ""):
            paths = self.fixture_unique(invalid)
            self.edit(paths[0], lambda rows: rows[0].update(reloj=invalid))
            self.assertFalse(verify(paths)["valido"])

    def fixture_unique(self, suffix):
        # Cada subcaso crea archivos nuevos, sin sobrescribir el registro.
        original = self.root
        self.root = original / ("case-" + str(len(list(original.iterdir()))))
        self.root.mkdir()
        try:
            return self.fixture()
        finally:
            self.root = original

    def test_legacy_header_empty_and_missing_file(self):
        legacy = self.root / "legacy.csv"
        legacy.write_text("nodo,evento,reloj\nnodo-A,envio,1\n", encoding="utf-8")
        self.assertFalse(verify([legacy])["valido"])
        self.assertFalse(verify([])["valido"])
        self.assertFalse(verify([self.root / "missing.csv"])["valido"])

    def test_no_overwrite_or_nonzero_initial_clock(self):
        path = self.root / "events.csv"
        with EventLog(path, "nodo-A", "TCP", "r1", LamportClock()):
            pass
        with self.assertRaises(FileExistsError):
            EventLog(path, "nodo-A", "TCP", "r1", LamportClock())
        with self.assertRaises(ValueError):
            EventLog(self.root / "new.csv", "nodo-A", "TCP", "r1", LamportClock(1))

    def test_invalid_record_does_not_increment(self):
        clock = LamportClock()
        with EventLog(self.root / "events.csv", "nodo-A", "TCP", "r1", clock) as log:
            for event, remote in (("otro", None), ("recepcion_acuse", None),
                                  ("envio_solicitud", 1)):
                with self.assertRaises(ValueError):
                    log.record(event, "m1", "nodo-A", "nodo-B", remote)
            self.assertEqual(clock.value, 0)

    def test_concurrent_recording_has_ordered_complete_rows(self):
        path = self.root / "concurrent.csv"
        clock = LamportClock()
        with EventLog(path, "nodo-A", "TCP", "r1", clock) as log:
            def send(i):
                return log.record("envio_solicitud", f"m{i}", "nodo-A", "nodo-B")
            with ThreadPoolExecutor(max_workers=3) as pool:
                values = list(pool.map(send, range(300)))
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(sorted(values), list(range(1, 301)))
        self.assertEqual([int(r["secuencia"]) for r in rows], list(range(1, 301)))
        self.assertEqual([int(r["reloj"]) for r in rows], list(range(1, 301)))

    def test_cli_exit_codes_and_output(self):
        paths = self.fixture()
        script = Path(__file__).resolve().parents[1] / "analysis/verify_lamport.py"
        output = self.root / "report.json"
        result = subprocess.run([sys.executable, "-B", str(script),
                                 *map(str, paths), "--require-concurrent",
                                 "--output", str(output)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(output.exists())
        self.edit(paths[0], lambda rows: rows.pop())
        result = subprocess.run([sys.executable, "-B", str(script), *map(str, paths)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)


if __name__ == "__main__":
    unittest.main()
