"""Link parameters: spectral efficiency and Eb/N0 <-> channel SNR conversion."""

from __future__ import annotations

import math

BITS_PER_SYMBOL = {"BPSK": 1, "QPSK": 2, "16-QAM": 4}
CHIPS_PER_BIT = {"NRZ": 1, "Manchester": 2}


def _check(line_code: str, modulation: str) -> None:
    if line_code not in CHIPS_PER_BIT:
        raise ValueError(f"Codificação desconhecida: {line_code}")
    if modulation not in BITS_PER_SYMBOL:
        raise ValueError(f"Modulação desconhecida: {modulation}")


def info_bits_per_symbol(line_code: str, modulation: str) -> float:
    """Information bits carried by one symbol: log2(M) / chips per bit."""
    _check(line_code, modulation)
    return BITS_PER_SYMBOL[modulation] / CHIPS_PER_BIT[line_code]


def spectral_efficiency(line_code: str, modulation: str) -> float:
    """Nominal spectral efficiency in bits/s/Hz.

    Ideal Nyquist signalling (roll-off 0): one symbol per second per Hz, so
    the efficiency equals the information bits per symbol. Manchester sends
    two chips per bit and therefore halves it. No error-correcting code is
    used (code rate 1).
    """
    return info_bits_per_symbol(line_code, modulation)


def ebn0_to_snr_db(ebn0_db: float, line_code: str, modulation: str) -> float:
    """Convert Eb/N0 (dB) to the per-symbol SNR (Es/N0, dB) used by the channel."""
    return ebn0_db + 10.0 * math.log10(info_bits_per_symbol(line_code, modulation))


def snr_to_ebn0_db(snr_db: float, line_code: str, modulation: str) -> float:
    """Inverse of ``ebn0_to_snr_db``."""
    return snr_db - 10.0 * math.log10(info_bits_per_symbol(line_code, modulation))