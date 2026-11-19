"""Componentes compartidos por los transportes TCP y gRPC."""

from .lamport import LamportClock

__all__ = ["LamportClock"]
