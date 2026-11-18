"""Complementary analysis: theory, AWGN x bursts, CER, constellations, trade-off
table and the consistency test."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .channel import awgn, burst_noise
from .decoding import receive
from .experiments import BURST, ENCODERS
from .link import BITS_PER_SYMBOL, ber_theory, ebn0_to_snr_db, spectral_efficiency
from .message import bits_to_text, text_to_bits
from .metrics import bit_metrics
from .modulation import modulate
from .plot_results import load_summary

LINES = ("NRZ", "Manchester")
MODS = ("BPSK", "QPSK", "16-QAM")
COLORS = {"BPSK": "tab:orange", "QPSK": "tab:green", "16-QAM": "tab:blue"}
TARGET_BER = 1e-3
REFERENCE_EBN0 = (6.0, 10.0)
FLOOR_EBN0 = 16.0
DEFAULT_MESSAGE = "Redes de Computadores - UNISINOS - Trabalho II"
# (label, channel, Eb/N0 in dB) used by the consistency test
SCENARIOS = (
    ("Canal ideal (sem ruído)", None, None),
    ("AWGN, Eb/N0 = 30 dB", "AWGN", 30.0),
    ("AWGN, Eb/N0 = 6 dB", "AWGN", 6.0),
    ("Rajadas, Eb/N0 = 16 dB", "Rajadas", 16.0),
)
USO = {
    ("NRZ", "BPSK"): "Enlaces ruidosos ou de baixa energia: é a mais robusta, mas usa a banda de forma pouco eficiente.",
    ("NRZ", "QPSK"): "Melhor compromisso geral: dobra a eficiência do BPSK com a mesma BER para o mesmo Eb/N0.",
    ("NRZ", "16-QAM"): "Enlaces limpos (Eb/N0 alto) em que a banda é escassa: maior taxa, menor robustez.",
    ("Manchester", "BPSK"): "Quando o sincronismo por transição pesa mais que banda e energia: custa 3 dB e metade da eficiência.",
    ("Manchester", "QPSK"): "Mesmo caso do Manchester + BPSK, com o dobro da eficiência.",
    ("Manchester", "16-QAM"): "Sincronismo por transição em enlace limpo; ainda assim exige muito mais Eb/N0 que o NRZ.",
}


# ---------------------------------------------------------------- plot helpers
def detection_limit(rows) -> float:
    """Smallest measurable BER: one error in all bits of all repetitions."""
    n_reps = int(float(rows[0].get("n_reps", 5)))
    n_bits = int(float(rows[0].get("n_bits_per_rep", 100_000)))
    return 1.0 / (n_reps * n_bits)


def axis_bottom(limit: float) -> float:
    return 10.0 ** math.floor(math.log10(limit))


def plot_measured(axis, x, y, color, label, limit, *, linestyle="-", marker="o"):
    """Log-axis curve; a measured 0 means 'below the limit' and is drawn hollow."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    clipped = np.maximum(y, limit)
    axis.plot(x, clipped, linestyle=linestyle, color=color, label=label)
    for mask, face in ((y > 0, color), (y == 0, "white")):
        axis.plot(x[mask], clipped[mask], linestyle="none", marker=marker,
                  color=color, markerfacecolor=face)


def style_log_axis(axis, limit, ylabel="BER"):
    axis.set_yscale("log")
    axis.set_ylim(bottom=axis_bottom(limit), top=1.0)
    axis.axhline(limit, color="gray", linestyle="--", linewidth=1)
    axis.text(0.99, limit * 1.15, f"limite de detecção ≈ {limit:.0e}", fontsize=8,
              color="gray", ha="right", transform=axis.get_yaxis_transform())
    axis.set_xlabel("Eb/N0 (dB)")
    axis.set_ylabel(ylabel)
    axis.grid(True, which="both", alpha=0.3)


def _curve(rows, line, mod, channel, key):
    selected = sorted(
        (r for r in rows if r["line_code"] == line and r["modulation"] == mod and r["channel"] == channel),
        key=lambda r: float(r["ebn0_db"]),
    )
    return (np.array([float(r["ebn0_db"]) for r in selected]),
            np.array([float(r[key]) for r in selected]))


def _save(figure, output: Path) -> None:
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


# ---------------------------------------------------------------------- figures
def plot_awgn_vs_bursts(rows, output: Path) -> None:
    limit = detection_limit(rows)
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for axis, line in zip(axes, LINES):
        for mod in MODS:
            x, y = _curve(rows, line, mod, "AWGN", "ber_mean")
            plot_measured(axis, x, y, COLORS[mod], f"{mod} AWGN", limit)
            x, y = _curve(rows, line, mod, "Rajadas", "ber_mean")
            plot_measured(axis, x, y, COLORS[mod], f"{mod} rajadas", limit, linestyle="--", marker="s")
        style_log_axis(axis, limit)
        axis.set_title(f"{line}: AWGN (linha cheia) x rajadas (tracejada)")
    axes[0].legend(fontsize=8, ncol=2)
    _save(figure, output)


def plot_vs_theory(rows, output: Path) -> None:
    limit = detection_limit(rows)
    grid = np.arange(0, 16.01, 0.25)
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for axis, line in zip(axes, LINES):
        for mod in MODS:
            x, y = _curve(rows, line, mod, "AWGN", "ber_mean")
            theory = np.maximum([ber_theory(line, mod, v) for v in grid], 1e-300)
            axis.plot(grid, theory, linestyle="--", color=COLORS[mod], alpha=0.8)
            axis.plot(x[y > 0], y[y > 0], linestyle="none", marker="o", color=COLORS[mod],
                      label=f"{mod} simulado")
        style_log_axis(axis, limit)
        axis.set_title(f"{line}: simulação (pontos) x teoria (tracejado), AWGN")
    axes[0].legend(fontsize=8)
    _save(figure, output)


def plot_cer(rows, output: Path) -> None:
    limit = 8.0 * detection_limit(rows)  # one wrong character among all characters
    figure, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    for axis, channel in zip(axes, ("AWGN", "Rajadas")):
        for line, style in (("NRZ", "-"), ("Manchester", ":")):
            for mod in MODS:
                x, y = _curve(rows, line, mod, channel, "cer_mean")
                plot_measured(axis, x, y, COLORS[mod], f"{line} {mod}", limit, linestyle=style)
        style_log_axis(axis, limit, "Taxa de erro de caractere")
        axis.set_title(f"Mensagem não recuperada (caractere com ≥ 1 bit errado), {channel}")
    axes[0].legend(fontsize=8, ncol=2)
    _save(figure, output)


def plot_constellations(output: Path, ebn0_db: float = 10.0, seed: int = 7) -> None:
    rng = np.random.default_rng(seed)
    figure, axes = plt.subplots(3, 3, figsize=(11, 10), sharex=True, sharey=True)
    for col, mod in enumerate(MODS):
        symbols = modulate(rng.integers(0, 2, 1500 * BITS_PER_SYMBOL[mod]).astype(np.uint8), mod)
        snr = ebn0_to_snr_db(ebn0_db, "NRZ", mod)
        panels = (
            ("Transmitido", symbols),
            (f"Após AWGN (Eb/N0 = {ebn0_db:.0f} dB)", awgn(symbols, snr, seed)),
            (f"Após rajadas (Eb/N0 = {ebn0_db:.0f} dB)", burst_noise(symbols, snr, seed=seed, **BURST)),
        )
        for row, (name, points) in enumerate(panels):
            axis = axes[row][col]
            axis.scatter(points.real, points.imag, s=4, alpha=0.5, color=COLORS[mod])
            axis.set_title(f"{mod}: {name}", fontsize=9)
            axis.set_aspect("equal")
            axis.grid(True, alpha=0.3)
            axis.set_xlim(-2, 2)
            axis.set_ylim(-2, 2)
    for axis in axes[-1]:
        axis.set_xlabel("Em fase (I)")
    for axis in axes[:, 0]:
        axis.set_ylabel("Quadratura (Q)")
    _save(figure, output)


# ----------------------------------------------------------------- trade-off table
def ebn0_for_ber(x, y, target: float, limit: float):
    """Eb/N0 where the log-interpolated BER curve first reaches ``target``; None if never."""
    logs = np.log10(np.maximum(y, limit))
    goal = math.log10(target)
    for i in range(len(x) - 1):
        if logs[i] > goal >= logs[i + 1]:
            fraction = (logs[i] - goal) / (logs[i] - logs[i + 1])
            return float(x[i] + fraction * (x[i + 1] - x[i]))
    return float(x[0]) if logs[0] <= goal else None


def _fmt_ber(value: float, limit: float) -> str:
    return f"< {limit:.0e}" if value == 0 else f"{value:.1e}"


def build_tradeoff(rows) -> list[dict]:
    limit = detection_limit(rows)
    table = []
    for line in LINES:
        for mod in MODS:
            x, awgn_ber = _curve(rows, line, mod, "AWGN", "ber_mean")
            _, burst_ber = _curve(rows, line, mod, "Rajadas", "ber_mean")
            needed = ebn0_for_ber(x, awgn_ber, TARGET_BER, limit)
            entry = {"Codificação": line, "Modulação": mod,
                     "Eficiência (bits/s/Hz)": spectral_efficiency(line, mod)}
            for ref in REFERENCE_EBN0:
                entry[f"BER AWGN @ {ref:.0f} dB"] = _fmt_ber(float(awgn_ber[list(x).index(ref)]), limit)
            entry[f"Eb/N0 p/ BER ≤ {TARGET_BER:.0e} (dB)"] = "—" if needed is None else f"{needed:.1f}"
            entry[f"BER rajadas @ {FLOOR_EBN0:.0f} dB"] = _fmt_ber(float(burst_ber[list(x).index(FLOOR_EBN0)]), limit)
            entry["Uso mais adequado"] = USO[(line, mod)]
            table.append(entry)
    return table


def write_tradeoff(table: list[dict], csv_path: Path, md_path: Path) -> None:
    fields = list(table[0])
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(table)
    lines = ["| " + " | ".join(fields) + " |", "|" + "|".join("---" for _ in fields) + "|"]
    lines += ["| " + " | ".join(str(row[f]) for f in fields) + " |" for row in table]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ------------------------------------------------------------- consistency test
def printable(text: str) -> str:
    return "".join(c if c.isprintable() and c != "\ufffd" else "?" for c in text)


def transmit(message: str, line_code: str, modulation: str, channel, ebn0_db, seed: int) -> dict:
    bits = text_to_bits(message)
    chips = (ENCODERS[line_code](bits) > 0).astype(np.uint8)
    symbols = modulate(chips, modulation)
    if channel is None:
        received = symbols
    else:
        snr = ebn0_to_snr_db(ebn0_db, line_code, modulation)
        received = awgn(symbols, snr, seed) if channel == "AWGN" else burst_noise(symbols, snr, seed=seed, **BURST)
    out = receive(received, line_code, modulation, chips.size)
    m = bit_metrics(bits, out)
    return {
        "text": printable(bits_to_text(out)), "errors": m["incorrect_bits"], "ber": m["ber"],
        "positions": m["incorrect_positions"],
        "wrong_chars": sorted({p // 8 for p in m["incorrect_positions"]}),
        "ok": m["incorrect_bits"] == 0,
    }


def build_consistency_report(message: str, seed: int) -> str:
    lines = [
        "# Teste de consistência", "",
        f"Mensagem enviada ({len(message)} caracteres, {8 * len(message)} bits): `{message}`",
        f"Seed: {seed}. Rajadas: {BURST}.", "",
        "| Cenário | Codificação | Modulação | Bits errados | BER | Caracteres afetados | Mensagem recuperada |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    details = []
    for label, channel, ebn0 in SCENARIOS:
        for line_code in LINES:
            for modulation in MODS:
                r = transmit(message, line_code, modulation, channel, ebn0, seed)
                lines.append(f"| {label} | {line_code} | {modulation} | {r['errors']} | {r['ber']:.4f} "
                             f"| {len(r['wrong_chars'])} | {'sim' if r['ok'] else 'NÃO'} |")
                if not r["ok"] and modulation in ("BPSK", "16-QAM") and line_code == "NRZ":
                    details.append(f"- {label}, {line_code} + {modulation}: recebido `{r['text']}`; "
                                   f"primeiros bits incorretos (base 0): {r['positions'][:10]}")
    lines += ["", "## Exemplos de divergência", "", *details, "", "## Interpretação", "",
              "- Em canal ideal e em AWGN com Eb/N0 alto, a mensagem é recuperada sem erros: o pipeline "
              "(ASCII, linha, modulação, demodulação, decodificação) é consistente.",
              "- Em Eb/N0 baixo surgem bits errados; o ruído aproxima os símbolos dos limites de decisão, "
              "e o 16-QAM erra mais por ter pontos mais próximos.",
              "- No canal com rajadas, mesmo com Eb/N0 alto podem restar erros: as rajadas de ruído forte "
              "não diminuem quando o ruído de fundo diminui (piso de erro).",
              "- Uma mensagem curta tem poucos bits, então a contagem de erros é só ilustrativa; as "
              "estatísticas confiáveis vêm do experimento com 100.000 bits e 5 repetições.", ""]
    return "\n".join(lines)


# ------------------------------------------------------------------------- main
def run_all(summary: Path, plots_dir: Path, results_dir: Path,
            message: str = DEFAULT_MESSAGE, seed: int = 2026) -> list[Path]:
    rows = load_summary(summary)
    plots_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    outputs = [plots_dir / name for name in
               ("ber_awgn_vs_rajadas.png", "ber_vs_teoria.png", "cer_vs_ebn0.png", "constelacoes.png")]
    plot_awgn_vs_bursts(rows, outputs[0])
    plot_vs_theory(rows, outputs[1])
    plot_cer(rows, outputs[2])
    plot_constellations(outputs[3])
    csv_path, md_path = results_dir / "tabela_compromisso.csv", results_dir / "tabela_compromisso.md"
    write_tradeoff(build_tradeoff(rows), csv_path, md_path)
    report = results_dir / "consistencia.md"
    report.write_text(build_consistency_report(message, seed), encoding="utf-8")
    return [*outputs, csv_path, md_path, report]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--summary", type=Path, default=Path("results/summary.csv"))
    parser.add_argument("--plots", type=Path, default=Path("results/plots"))
    parser.add_argument("--results", type=Path, default=Path("results"))
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    for path in run_all(args.summary, args.plots, args.results, args.message, args.seed):
        print(f"Salvo: {path}")


if __name__ == "__main__":
    main()