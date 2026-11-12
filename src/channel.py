"""AWGN channel model."""

from __future__ import annotations

import numpy as np


def awgn(signal: np.ndarray, snr_db: float, seed: int | None = None) -> np.ndarray:
    """Add complex Gaussian noise with P_signal/P_noise equal to the SNR."""
    if not np.isfinite(snr_db):
        raise ValueError("A SNR deve ser um número finito.")
    values = np.asarray(signal, dtype=complex)
    power = float(np.mean(np.abs(values) ** 2))
    if power == 0:
        return values.copy()
    noise_power = power / (10.0 ** (snr_db / 10.0))
    rng = np.random.default_rng(seed)
    noise = np.sqrt(noise_power / 2.0) * (
        rng.standard_normal(values.shape) + 1j * rng.standard_normal(values.shape)
    )
    return values + noise
