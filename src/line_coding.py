"""Baseband line coding and decoding."""

from __future__ import annotations

import numpy as np


def _validate_bits(bits: np.ndarray) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8).reshape(-1)
    if np.any(values > 1):
        raise ValueError("Os bits devem conter somente 0 ou 1.")
    return values


def nrz_encode(bits: np.ndarray) -> np.ndarray:
    """NRZ-L: bit 1 is +1 and bit 0 is -1."""
    values = _validate_bits(bits)
    return np.where(values == 1, 1.0, -1.0)


def nrz_decode(levels: np.ndarray) -> np.ndarray:
    """Hard-decode NRZ-L levels using zero as the decision threshold."""
    return (np.asarray(levels).reshape(-1) >= 0).astype(np.uint8)


def manchester_encode(bits: np.ndarray) -> np.ndarray:
    """Manchester coding with 0 -> (+1, -1) and 1 -> (-1, +1)."""
    values = _validate_bits(bits)
    levels = np.where(values[:, None] == 0, [1.0, -1.0], [-1.0, 1.0])
    return levels.reshape(-1)


def manchester_decode(levels: np.ndarray) -> np.ndarray:
    """Decode Manchester pairs, rejecting invalid equal-level pairs."""
    values = np.asarray(levels).reshape(-1)
    if values.size % 2:
        raise ValueError("A sequência Manchester deve ter número par de níveis.")
    pairs = values.reshape(-1, 2)
    signs = pairs >= 0
    valid = np.logical_xor(signs[:, 0], signs[:, 1])
    if not np.all(valid):
        raise ValueError("Níveis inválidos para Manchester: transição ausente.")
    return (~signs[:, 0]).astype(np.uint8)
