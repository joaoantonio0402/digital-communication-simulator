"""Experimental plan: BER x Eb/N0 for every line code, modulation and channel."""

from __future__ import annotations

import argparse
import csv
import json
import math
import platform
import time
from pathlib import Path

import numpy as np

from src.channel import awgn, burst_noise
from src.decoding import decode_line
from src.line_coding import manchester_encode, manchester_violations, nrz_encode
from src.link import ebn0_to_snr_db, spectral_efficiency
from src.metrics import bit_metrics
from src.modulation import demodulate, modulate

EBN0_DB = [0, 2, 4, 6, 8, 10, 12, 14, 16]   # >= 8 values
N_BITS = 100_000                              # information bits per trial
N_REPS = 5                                    # independent random repetitions
BASE_SEED = 2026
LINE_CODES = ("NRZ", "Manchester")
MODULATIONS = ("BPSK", "QPSK", "16-QAM")
CHANNELS = ("AWGN", "Rajadas")
BURST = {"burst_probability": 0.01, "burst_length": 8, "burst_snr_db": 0.0}

ENCODERS = {"NRZ": nrz_encode, "Manchester": manchester_encode}
RAW_FIELDS = [
    "rep", "line_code", "modulation", "channel", "ebn0_db", "snr_es_db",
    "spectral_eff", "n_bits", "errors", "ber", "char_error_rate",
    "manchester_violations", "seed",
]
# Student t, 97.5% quantile, by degrees of freedom (n_reps - 1).
T975 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447,
        7: 2.365, 8: 2.306, 9: 2.262}


def trial_seed(*parts: int) -> int:
    """Deterministic, independent seed for each (rep, line, mod, channel, snr)."""
    return int(np.random.SeedSequence([BASE_SEED, *parts]).generate_state(1)[0])


def char_error_rate(sent: np.ndarray, got: np.ndarray) -> float:
    """Fraction of 8-bit characters that contain at least one wrong bit."""
    usable = (sent.size // 8) * 8
    wrong = np.any(sent[:usable].reshape(-1, 8) != got[:usable].reshape(-1, 8), axis=1)
    return float(np.mean(wrong))


def run_experiments(n_bits: int, n_reps: int, ebn0_values: list[float]) -> list[dict]:
    rows: list[dict] = []
    for rep in range(n_reps):
        bits = np.random.default_rng(trial_seed(rep)).integers(0, 2, n_bits).astype(np.uint8)
        for li, line_code in enumerate(LINE_CODES):
            levels = ENCODERS[line_code](bits)
            chips = (levels > 0).astype(np.uint8)
            for mi, modulation in enumerate(MODULATIONS):
                symbols = modulate(chips, modulation)   # independent of SNR and channel
                for ci, channel in enumerate(CHANNELS):
                    for si, ebn0 in enumerate(ebn0_values):
                        snr_es = ebn0_to_snr_db(ebn0, line_code, modulation)
                        seed = trial_seed(rep, 1 + li, 1 + mi, 1 + ci, 1 + si)
                        if channel == "AWGN":
                            rx = awgn(symbols, snr_es, seed)
                        else:
                            rx = burst_noise(symbols, snr_es, seed=seed, **BURST)
                        chips_rx = demodulate(rx, modulation)[: chips.size]
                        levels_rx = np.where(chips_rx == 1, 1.0, -1.0)
                        out = decode_line(levels_rx, line_code)
                        m = bit_metrics(bits, out)
                        violations = (
                            manchester_violations(levels_rx) if line_code == "Manchester" else 0
                        )
                        rows.append({
                            "rep": rep, "line_code": line_code, "modulation": modulation,
                            "channel": channel, "ebn0_db": ebn0, "snr_es_db": round(snr_es, 4),
                            "spectral_eff": spectral_efficiency(line_code, modulation),
                            "n_bits": m["total_bits"], "errors": m["incorrect_bits"],
                            "ber": m["ber"], "char_error_rate": char_error_rate(bits, out),
                            "manchester_violations": violations, "seed": seed,
                        })
        print(f"repetição {rep + 1}/{n_reps} concluída", flush=True)
    return rows


def summarize(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = {}
    for r in rows:
        key = (r["line_code"], r["modulation"], r["channel"], r["ebn0_db"])
        groups.setdefault(key, []).append(r)
    summary = []
    for (line_code, modulation, channel, ebn0), g in groups.items():
        ber = np.array([r["ber"] for r in g])
        cer = np.array([r["char_error_rate"] for r in g])
        n = len(g)
        std = float(np.std(ber, ddof=1)) if n > 1 else 0.0
        ci = T975.get(n - 1, 1.96) * std / math.sqrt(n) if n > 1 else 0.0
        summary.append({
            "line_code": line_code, "modulation": modulation, "channel": channel,
            "ebn0_db": ebn0, "spectral_eff": g[0]["spectral_eff"], "n_reps": n,
            "n_bits_per_rep": g[0]["n_bits"], "ber_mean": float(ber.mean()), "ber_std": std,
            "ber_min": float(ber.min()), "ber_max": float(ber.max()), "ber_ci95": ci,
            "cer_mean": float(cer.mean()),
        })
    return summary


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields or list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bits", type=int, default=N_BITS)
    parser.add_argument("--reps", type=int, default=N_REPS)
    parser.add_argument("--out", default="results")
    parser.add_argument("--quick", action="store_true", help="10 000 bits, 2 reps")
    args = parser.parse_args()
    n_bits, n_reps = (10_000, 2) if args.quick else (args.bits, args.reps)
    if n_bits % 8:
        parser.error("--bits deve ser múltiplo de 8")

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    rows = run_experiments(n_bits, n_reps, EBN0_DB)
    write_csv(out_dir / "raw_results.csv", rows, RAW_FIELDS)
    write_csv(out_dir / "summary.csv", summarize(rows))
    (out_dir / "config.json").write_text(json.dumps({
        "ebn0_db": EBN0_DB, "n_bits": n_bits, "n_reps": n_reps, "base_seed": BASE_SEED,
        "line_codes": LINE_CODES, "modulations": MODULATIONS, "channels": CHANNELS,
        "burst": BURST, "numpy": np.__version__, "python": platform.python_version(),
        "seconds": round(time.time() - started, 1),
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(rows)} ensaios salvos em {out_dir}/ ({time.time() - started:.0f} s)")


if __name__ == "__main__":
    main()