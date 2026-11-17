import numpy as np
import pytest

from src.channel import awgn, burst_noise
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


def test_burst_noise_is_reproducible_and_changes_signal():
    signal = np.ones(1000, dtype=complex)
    first = burst_noise(signal, 10, burst_probability=0.1, burst_length=4, seed=7)
    second = burst_noise(signal, 10, burst_probability=0.1, burst_length=4, seed=7)
    assert np.array_equal(first, second)
    assert not np.array_equal(first, signal)


def test_burst_noise_rejects_invalid_parameters():
    signal = np.ones(4, dtype=complex)
    with pytest.raises(ValueError):
        burst_noise(signal, 10, burst_probability=1.1)
    with pytest.raises(ValueError):
        burst_noise(signal, 10, burst_length=0)


def test_metrics():
    assert bit_metrics(np.array([0, 1, 1]), np.array([0, 0, 1])) == {
        "total_bits": 3,
        "incorrect_bits": 1,
        "incorrect_positions": [1],
        "ber": pytest.approx(1 / 3),
    }

def test_manchester_decode_tolerates_invalid_pairs():
    from src.line_coding import manchester_violations

    # 2o par (+1,+1) e 3o par (-1,-1) não têm transição no meio do bit.
    levels = np.array([1.0, -1.0, 1.0, 1.0, -1.0, -1.0, -1.0, 1.0])
    assert manchester_violations(levels) == 2
    assert np.array_equal(manchester_decode(levels), np.array([0, 0, 1, 1], dtype=np.uint8))
    with pytest.raises(ValueError):
        manchester_decode(levels, strict=True)


def test_manchester_noisy_channel_does_not_crash():
    bits = text_to_bits("Teste de Manchester com ruido")
    chips = (manchester_encode(bits) > 0).astype(np.uint8)
    received = awgn(qpsk_modulate(chips), 0, seed=3)
    recovered = receive(received, "Manchester", "QPSK", chips.size)
    assert recovered.size == bits.size

def test_spectral_efficiency_table():
    from src.link import spectral_efficiency

    esperado = {
        ("NRZ", "BPSK"): 1, ("NRZ", "QPSK"): 2, ("NRZ", "16-QAM"): 4,
        ("Manchester", "BPSK"): 0.5, ("Manchester", "QPSK"): 1, ("Manchester", "16-QAM"): 2,
    }
    for (linha, mod), valor in esperado.items():
        assert spectral_efficiency(linha, mod) == pytest.approx(valor)


def test_ebn0_snr_conversion_round_trip():
    from src.link import ebn0_to_snr_db, snr_to_ebn0_db

    assert ebn0_to_snr_db(6, "NRZ", "BPSK") == pytest.approx(6)
    assert ebn0_to_snr_db(6, "NRZ", "QPSK") == pytest.approx(6 + 3.0103, abs=1e-3)
    assert ebn0_to_snr_db(6, "Manchester", "BPSK") == pytest.approx(6 - 3.0103, abs=1e-3)
    assert snr_to_ebn0_db(ebn0_to_snr_db(8, "NRZ", "16-QAM"), "NRZ", "16-QAM") == pytest.approx(8)