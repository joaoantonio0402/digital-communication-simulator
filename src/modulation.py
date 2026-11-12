"""Gray-coded digital modulation and hard demodulation."""

from __future__ import annotations

import numpy as np


def _bits(bits: np.ndarray) -> np.ndarray:
    values = np.asarray(bits, dtype=np.uint8).reshape(-1)
    if np.any(values > 1):
        raise ValueError("Os bits devem conter somente 0 ou 1.")
    return values


def _group(values: np.ndarray, width: int) -> np.ndarray:
    if values.size % width:
        raise ValueError("A sequência precisa ter comprimento múltiplo da modulação.")
    return values.reshape(-1, width)


def bpsk_modulate(bits: np.ndarray) -> np.ndarray:
    return (2.0 * _bits(bits) - 1.0).astype(complex)


def bpsk_demodulate(symbols: np.ndarray) -> np.ndarray:
    return (np.real(np.asarray(symbols).reshape(-1)) >= 0).astype(np.uint8)


def qpsk_modulate(bits: np.ndarray) -> np.ndarray:
    """Gray QPSK: 00, 01, 11, 10 around the unit circle."""
    pairs = _group(_bits(bits), 2)
    mapping = {(0, 0): 1 + 1j, (0, 1): -1 + 1j, (1, 1): -1 - 1j, (1, 0): 1 - 1j}
    return np.array([mapping[tuple(pair)] for pair in pairs]) / np.sqrt(2)


def qpsk_demodulate(symbols: np.ndarray) -> np.ndarray:
    values = np.asarray(symbols).reshape(-1)
    real_negative = (np.real(values) < 0).astype(np.uint8)
    imag_negative = (np.imag(values) < 0).astype(np.uint8)
    # The table uses the Gray order 00, 01, 11, 10 around the constellation.
    return np.column_stack((imag_negative, real_negative)).reshape(-1).astype(np.uint8)


def qam16_modulate(bits: np.ndarray) -> np.ndarray:
    """Normalized Gray 16-QAM using amplitudes -3, -1, +1, +3."""
    groups = _group(_bits(bits), 4)
    axis = {(0, 0): -3, (0, 1): -1, (1, 1): 1, (1, 0): 3}
    return np.array([axis[tuple(g[:2])] + 1j * axis[tuple(g[2:])] for g in groups]) / np.sqrt(10)


def qam16_demodulate(symbols: np.ndarray) -> np.ndarray:
    values = np.asarray(symbols).reshape(-1) * np.sqrt(10)

    def axis_bits(axis: np.ndarray) -> np.ndarray:
        magnitude = np.where(axis < -2, 0, np.where(axis < 0, 1, np.where(axis < 2, 2, 3)))
        # Index order is Gray labels: -3=00, -1=01, +1=11, +3=10.
        return np.array([[0, 0], [0, 1], [1, 1], [1, 0]], dtype=np.uint8)[magnitude]

    return np.column_stack((axis_bits(np.real(values)), axis_bits(np.imag(values)))).reshape(-1)


def modulate(bits: np.ndarray, name: str) -> np.ndarray:
    functions = {"BPSK": bpsk_modulate, "QPSK": qpsk_modulate, "16-QAM": qam16_modulate}
    try:
        return functions[name](bits)
    except KeyError as exc:
        raise ValueError(f"Modulação desconhecida: {name}") from exc


def demodulate(symbols: np.ndarray, name: str) -> np.ndarray:
    functions = {"BPSK": bpsk_demodulate, "QPSK": qpsk_demodulate, "16-QAM": qam16_demodulate}
    try:
        return functions[name](symbols)
    except KeyError as exc:
        raise ValueError(f"Modulação desconhecida: {name}") from exc
