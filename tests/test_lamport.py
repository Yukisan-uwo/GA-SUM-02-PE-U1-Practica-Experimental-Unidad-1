"""Pruebas funcionales; NO son mediciones de la práctica TCP/gRPC."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import unittest

from src.common.lamport import LamportClock


class LamportTests(unittest.TestCase):
    def test_initial_and_read(self):
        clock = LamportClock()
        self.assertEqual(clock.value, 0)
        self.assertEqual(clock.value, 0)
        self.assertEqual(LamportClock(8).value, 8)

    def test_tick_and_send(self):
        clock = LamportClock()
        self.assertEqual(clock.tick(), 1)
        self.assertEqual(clock.send(), 2)

    def test_receive_greater_equal_and_smaller(self):
        clock = LamportClock()
        self.assertEqual(clock.receive(10), 11)
        self.assertEqual(clock.receive(11), 12)
        self.assertEqual(clock.receive(2), 13)

    def test_round_trip(self):
        a, b = LamportClock(), LamportClock()
        sent = a.send()
        received = b.receive(sent)
        ack = b.send()
        completed = a.receive(ack)
        self.assertLess(sent, received)
        self.assertLess(received, ack)
        self.assertLess(ack, completed)

    def test_aliases(self):
        clock = LamportClock()
        self.assertEqual(clock.enviar(), 1)
        self.assertEqual(clock.recibir(4), 5)
        self.assertEqual(clock.valor, clock.value)

    def test_invalid_inputs_do_not_change_clock(self):
        clock = LamportClock(3)
        for value in (True, False, 1.5, "2", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    clock.receive(value)
                with self.assertRaises(TypeError):
                    LamportClock(value)
                self.assertEqual(clock.value, 3)
        with self.assertRaises(ValueError):
            clock.receive(-1)
        with self.assertRaises(ValueError):
            LamportClock(-1)
        self.assertEqual(clock.value, 3)

    def test_readonly(self):
        clock = LamportClock()
        for name in ("value", "valor"):
            with self.assertRaises(AttributeError):
                setattr(clock, name, 50)

    def test_independent_nodes(self):
        a, b = LamportClock(), LamportClock()
        a.send()
        self.assertEqual(b.value, 0)

    def test_concurrent_sends_no_lost_updates(self):
        clock = LamportClock()
        barrier = Barrier(3)

        def worker():
            barrier.wait(timeout=10)
            return [clock.send() for _ in range(1000)]

        with ThreadPoolExecutor(max_workers=3) as pool:
            results = list(pool.map(lambda _: worker(), range(3)))
        values = [value for group in results for value in group]
        self.assertEqual(sorted(values), list(range(1, 3001)))
        self.assertEqual(clock.value, 3000)

    def test_concurrent_receives_no_lost_updates(self):
        clock = LamportClock()
        with ThreadPoolExecutor(max_workers=3) as pool:
            values = list(pool.map(clock.receive, [10] * 300))
        self.assertEqual(sorted(values), list(range(11, 311)))
        self.assertEqual(clock.value, 310)


if __name__ == "__main__":
    unittest.main()
