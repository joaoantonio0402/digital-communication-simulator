"""Public demodulation API kept separate from modulation choices."""

from __future__ import annotations

import numpy as np

from .modulation import bpsk_demodulate, demodulate, qam16_demodulate, qpsk_demodulate

__all__ = [
    "bpsk_demodulate",
    "qpsk_demodulate",
    "qam16_demodulate",
    "demodulate",
]


def demodulate_symbols(symbols: np.ndarray, name: str) -> np.ndarray:
    """Alias with an explicit name for callers implementing a receiver."""
    return demodulate(symbols, name)
