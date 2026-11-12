"""Receiver pipeline and line-code dispatch."""

from __future__ import annotations

import numpy as np

from .line_coding import manchester_decode, nrz_decode
from .message import bits_to_text
from .modulation import demodulate


def decode_line(levels: np.ndarray, name: str) -> np.ndarray:
    if name == "NRZ":
        return nrz_decode(levels)
    if name == "Manchester":
        return manchester_decode(levels)
    raise ValueError(f"Codificação desconhecida: {name}")


def receive(symbols: np.ndarray, line_code: str, modulation: str, chip_count: int) -> np.ndarray:
    """Demodulate, remove modulation padding, line-decode, and return message bits."""
    chips = demodulate(symbols, modulation)[:chip_count]
    levels = np.where(chips == 1, 1.0, -1.0)
    return decode_line(levels, line_code)


def bits_to_received_text(bits: np.ndarray) -> str:
    return bits_to_text(bits)
