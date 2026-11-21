"""Lanzador de tres nodos TCP/gRPC con registro de Lamport."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.common.node_experiment import main


if __name__ == "__main__":
    raise SystemExit(main())
