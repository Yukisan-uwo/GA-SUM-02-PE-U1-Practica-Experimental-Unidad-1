"""Pruebas de integración temporales; no son datos experimentales de la práctica."""

import importlib.util
import csv
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import socket
import subprocess
import sys
import threading
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from src.common.lamport import LamportClock


ROOT = Path(__file__).resolve().parents[1]
SOCKETS = ROOT / "src/sockets"


def load_transport(name, filename):
    sys.path.insert(0, str(SOCKETS))
    try:
        spec = importlib.util.spec_from_file_location(name, SOCKETS / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.pop(0)


client_module = load_transport("tested_tcp_client", "client.py")
server_module = load_transport("tested_tcp_server", "server.py")


class TCPSharedClockTests(unittest.TestCase):
    def test_both_transports_import_common_class(self):
        self.assertIs(client_module.LamportClock, LamportClock)
        self.assertIs(server_module.LamportClock, LamportClock)

    def test_reception_rejects_invalid_timestamp(self):
        for module in (client_module, server_module):
            with self.assertRaises(ValueError):
                module.LamportClock().receive(-1)

    def test_twenty_loopback_exchanges(self):
        errors, events = [], []
        server_clock = LamportClock()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            listener.settimeout(5)
            port = listener.getsockname()[1]

            def worker():
                try:
                    connection, _ = listener.accept()
                    connection.settimeout(5)
                    server_module.serve_client(connection, "nodo-B", server_clock,
                                               quiet=True, log_events=False)
                except Exception as exc:
                    errors.append(exc)

            thread = threading.Thread(target=worker, daemon=True)
            thread.start()
            try:
                with patch.object(client_module, "append_event", side_effect=lambda *a: events.append(a)), \
                        patch.object(client_module, "append_latency"):
                    with client_module.ClienteTCP(timeout=5) as client:
                        client.conectar("127.0.0.1", port)
                        for attempt in range(1, 21):
                            ack, elapsed = client.enviar("nodo-A", "nodo-B", "x" * 100,
                                                         attempt, 0)
                            self.assertTrue(ack["ok"])
                            self.assertEqual(ack["timestamp"], 4 * attempt - 1)
                            self.assertEqual(client.clock.value, 4 * attempt)
                            self.assertGreaterEqual(elapsed, 0)
                        self.assertEqual(client.clock.value, 80)
            finally:
                thread.join(timeout=6)
            self.assertFalse(thread.is_alive(), "El servidor de prueba no terminó")
        self.assertFalse(errors, errors)
        self.assertEqual(server_clock.value, 79)
        self.assertEqual(len(events), 40)
        self.assertEqual(events[-1][2], 80)

    def test_existing_script_entrypoints(self):
        for script in ("client.py", "server.py"):
            result = subprocess.run([sys.executable, "-B", str(SOCKETS / script), "--help"],
                                    cwd=ROOT, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_tcp_csv_has_single_header_with_concurrent_writers(self):
        logger = sys.modules["csv_logs"]
        with TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with patch.object(logger, "DATA_DIRECTORY", directory):
                def append(i):
                    logger.append_event("nodo-B", "recepcion_solicitud", i + 1,
                                        f"m{i}", "nodo-A", "nodo-B")
                with ThreadPoolExecutor(max_workers=3) as pool:
                    list(pool.map(append, range(300)))
            with (directory / "eventos_tcp_nodo-B.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 300)
            self.assertEqual({r["id_mensaje"] for r in rows}, {f"m{i}" for i in range(300)})


if __name__ == "__main__":
    unittest.main()
