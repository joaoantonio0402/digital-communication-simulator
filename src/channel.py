"""AWGN and burst-noise channel models."""

from __future__ import annotations

import numpy as np


def _validate_snr(snr_db: float) -> None:
    if not np.isfinite(snr_db):
        raise ValueError("A SNR deve ser um número finito.")


def _signal_power(values: np.ndarray) -> float:
    return float(np.mean(np.abs(values) ** 2))


def awgn(signal: np.ndarray, snr_db: float, seed: int | None = None) -> np.ndarray:
    """Add complex Gaussian noise with P_signal/P_noise equal to the SNR."""
    _validate_snr(snr_db)
    values = np.asarray(signal, dtype=complex)
    power = _signal_power(values)
    if power == 0:
        return values.copy()
    noise_power = power / (10.0 ** (snr_db / 10.0))
    rng = np.random.default_rng(seed)
    noise = np.sqrt(noise_power / 2.0) * (
        rng.standard_normal(values.shape) + 1j * rng.standard_normal(values.shape)
    )
    return values + noise


def burst_noise(
    signal: np.ndarray,
    snr_db: float,
    burst_probability: float = 0.01,
    burst_length: int = 8,
    burst_snr_db: float = 0.0,
    seed: int | None = None,
) -> np.ndarray:
    """Add AWGN plus high-power noise in randomly started bursts.

    ``snr_db`` controls the background AWGN. Each burst has
    ``burst_snr_db`` relative to the signal power and lasts up to
    ``burst_length`` samples. A burst starts at each sample selected by
    ``burst_probability``; overlapping bursts are merged.
    """
    _validate_snr(snr_db)
    _validate_snr(burst_snr_db)
    if not 0.0 <= burst_probability <= 1.0:
        raise ValueError("A probabilidade da rajada deve estar entre 0 e 1.")
    if not isinstance(burst_length, (int, np.integer)) or burst_length < 1:
        raise ValueError("O comprimento da rajada deve ser um inteiro positivo.")

    values = np.asarray(signal, dtype=complex)
    power = _signal_power(values)
    if power == 0:
        return values.copy()

    rng = np.random.default_rng(seed)
    background_power = power / (10.0 ** (snr_db / 10.0))
    background = np.sqrt(background_power / 2.0) * (
        rng.standard_normal(values.shape) + 1j * rng.standard_normal(values.shape)
    )

    flat_size = values.size
    starts = rng.random(flat_size) < burst_probability
    burst_mask = np.zeros(flat_size, dtype=bool)
    for start in np.flatnonzero(starts):
        burst_mask[start : start + burst_length] = True

    burst_power = power / (10.0 ** (burst_snr_db / 10.0))
    burst = np.sqrt(burst_power / 2.0) * (
        rng.standard_normal(flat_size) + 1j * rng.standard_normal(flat_size)
    )
    burst = burst.reshape(values.shape)
    burst *= burst_mask.reshape(values.shape)
    return values + background + burst
