"""Basic transmission metrics."""

from __future__ import annotations

import numpy as np


def bit_metrics(original: np.ndarray, received: np.ndarray) -> dict[str, float | int | list[int]]:
    sent = np.asarray(original, dtype=np.uint8).reshape(-1)
    got = np.asarray(received, dtype=np.uint8).reshape(-1)
    if sent.size != got.size:
        raise ValueError("As sequências devem ter o mesmo tamanho.")
    incorrect_positions = np.flatnonzero(sent != got).tolist()
    errors = len(incorrect_positions)
    return {
        "total_bits": int(sent.size),
        "incorrect_bits": errors,
        "incorrect_positions": incorrect_positions,
        "ber": errors / sent.size if sent.size else 0.0,
    }
