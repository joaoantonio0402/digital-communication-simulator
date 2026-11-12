import numpy as np
import pytest

from src.channel import awgn
from src.decoding import receive
from src.line_coding import manchester_decode, manchester_encode, nrz_decode, nrz_encode
from src.message import bits_to_text, text_to_bits
from src.metrics import bit_metrics
from src.modulation import (
    bpsk_demodulate,
    bpsk_modulate,
    qam16_demodulate,
    qam16_modulate,
    qpsk_demodulate,
    qpsk_modulate,
)


def test_ascii_round_trip():
    assert bits_to_text(text_to_bits("Rede 2")) == "Rede 2"


@pytest.mark.parametrize("encode, decode", [(nrz_encode, nrz_decode), (manchester_encode, manchester_decode)])
def test_line_code_round_trip(encode, decode):
    bits = np.array([0, 1, 1, 0, 1], dtype=np.uint8)
    assert np.array_equal(decode(encode(bits)), bits)


@pytest.mark.parametrize("modulate, demodulate, width", [
    (bpsk_modulate, bpsk_demodulate, 1),
    (qpsk_modulate, qpsk_demodulate, 2),
    (qam16_modulate, qam16_demodulate, 4),
])
def test_modulation_round_trip(modulate, demodulate, width):
    bits = np.arange(32, dtype=np.uint8) % 2
    bits = bits[: len(bits) - len(bits) % width]
    assert np.array_equal(demodulate(modulate(bits)), bits)


@pytest.mark.parametrize("modulation, width", [("BPSK", 1), ("QPSK", 2), ("16-QAM", 4)])
def test_ideal_transmission(modulation, width):
    message_bits = text_to_bits("OK")
    line = manchester_encode(message_bits)
    chips = (line > 0).astype(np.uint8)
    chips = np.pad(chips, (0, (-len(chips)) % width))
    symbols = {"BPSK": bpsk_modulate, "QPSK": qpsk_modulate, "16-QAM": qam16_modulate}[modulation](chips)
    recovered = receive(symbols, "Manchester", modulation, len(line))
    assert bits_to_text(recovered) == "OK"


def test_awgn_is_reproducible_and_changes_signal():
    signal = np.ones(1000, dtype=complex)
    first = awgn(signal, 10, seed=7)
    second = awgn(signal, 10, seed=7)
    assert np.array_equal(first, second)
    assert not np.array_equal(first, signal)


def test_metrics():
    assert bit_metrics(np.array([0, 1, 1]), np.array([0, 0, 1])) == {
        "total_bits": 3, "incorrect_bits": 1, "ber": pytest.approx(1 / 3)
    }
