"""Interactive terminal entry point for the digital communication simulator."""

from __future__ import annotations

import numpy as np

from src.channel import awgn
from src.decoding import bits_to_received_text, receive
from src.line_coding import manchester_encode, nrz_encode
from src.message import text_to_bits
from src.metrics import bit_metrics
from src.modulation import modulate


def _choose(prompt: str, options: tuple[str, ...]) -> str:
    while True:
        print(prompt)
        for index, option in enumerate(options, 1):
            print(f"{index}. {option}")
        choice = input("Escolha: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        print("Opção inválida.\n")


def _snr() -> float:
    while True:
        try:
            value = float(input("SNR (dB): ").strip())
            if np.isfinite(value):
                return value
        except ValueError:
            pass
        print("Informe um número finito.\n")


def run() -> None:
    message = input("Mensagem ASCII: ")
    line_code = _choose("Codificação de linha:", ("NRZ", "Manchester"))
    modulation = _choose("Modulação:", ("BPSK", "QPSK", "16-QAM"))
    snr_db = _snr()
    seed_text = input("Seed (vazio para aleatória): ").strip()
    seed = int(seed_text) if seed_text else None

    bits = text_to_bits(message)
    levels = nrz_encode(bits) if line_code == "NRZ" else manchester_encode(bits)
    chip_bits = (levels > 0).astype(np.uint8)
    symbols = modulate(chip_bits, modulation)
    received_symbols = awgn(symbols, snr_db, seed)
    received_bits = receive(received_symbols, line_code, modulation, chip_bits.size)
    metrics = bit_metrics(bits, received_bits)

    print("\n--- Resultado ---")
    print(f"Original: {message}")
    print(f"Recebida: {bits_to_received_text(received_bits)}")
    print(f"Bits transmitidos: {metrics['total_bits']}")
    print(f"Bits incorretos: {metrics['incorrect_bits']}")
    print(f"BER: {metrics['ber']:.6f}")


if __name__ == "__main__":
    run()
