"""Conversion between text messages and 8-bit ASCII streams."""

from __future__ import annotations

import numpy as np


def text_to_bits(message: str) -> np.ndarray:
    """Encode a message as one unsigned bit per ASCII byte."""
    try:
        encoded = message.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("A mensagem deve conter apenas caracteres ASCII.") from exc
    return np.unpackbits(np.frombuffer(encoded, dtype=np.uint8)).astype(np.uint8)


def bits_to_text(bits: np.ndarray) -> str:
    """Decode a multiple-of-eight bit array as ASCII text."""
    values = np.asarray(bits, dtype=np.uint8).reshape(-1)
    if values.size % 8:
        raise ValueError("A quantidade de bits deve ser múltipla de 8.")
    if np.any(values > 1):
        raise ValueError("Os bits devem conter somente 0 ou 1.")
    return np.packbits(values).tobytes().decode("ascii", errors="replace")
