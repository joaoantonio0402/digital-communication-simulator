"""Generate BER versus Eb/N0 plots from experiment summary results."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt


REQUIRED_FIELDS = {
    "line_code",
    "modulation",
    "channel",
    "ebn0_db",
    "spectral_eff",
    "ber_mean",
    "ber_ci95",
}
BER_FLOOR = 1e-12


def load_summary(path: Path) -> list[dict[str, str]]:
    """Load and validate the aggregated experiment CSV."""
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        missing = REQUIRED_FIELDS - fields
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(f"O resumo não contém as colunas obrigatórias: {names}.")
        rows = list(reader)
    if not rows:
        raise ValueError("O arquivo de resumo não contém resultados.")
    return rows


def _plot_group(rows: list[dict[str, str]], title: str, output: Path) -> None:
    """Plot all modulation curves for one line-code/channel combination."""
    modulations = sorted({row["modulation"] for row in rows})
    figure, axis = plt.subplots(figsize=(8, 5))
    for modulation in modulations:
        selected = [row for row in rows if row["modulation"] == modulation]
        selected.sort(key=lambda row: float(row["ebn0_db"]))
        x = [float(row["ebn0_db"]) for row in selected]
        y = [max(float(row["ber_mean"]), BER_FLOOR) for row in selected]
        errors = [float(row["ber_ci95"]) for row in selected]
        lower = [max(mean - error, BER_FLOOR) for mean, error in zip(y, errors)]
        upper = [min(mean + error, 1.0) for mean, error in zip(y, errors)]
        axis.plot(x, y, marker="o", label=modulation)
        axis.fill_between(x, lower, upper, alpha=0.15)

    axis.set_yscale("log")
    axis.set_ylim(bottom=BER_FLOOR, top=1.0)
    axis.set_xlabel("Eb/N0 (dB)")
    axis.set_ylabel("BER")
    axis.set_title(title)
    axis.grid(True, which="both", alpha=0.3)
    axis.legend(title="Modulação")
    axis.text(
        0.01,
        0.01,
        "BER = 0 é exibida no piso 10⁻¹²",
        transform=axis.transAxes,
        fontsize=8,
        alpha=0.7,
    )
    figure.tight_layout()
    figure.savefig(output, dpi=150)
    plt.close(figure)


def generate_plots(summary_path: Path, output_dir: Path) -> list[Path]:
    """Generate one BER curve per line-code/channel combination."""
    rows = load_summary(summary_path)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[Path] = []
    groups = sorted({(row["line_code"], row["channel"]) for row in rows})
    for line_code, channel in groups:
        selected = [
            row for row in rows
            if row["line_code"] == line_code and row["channel"] == channel
        ]
        filename = f"ber_{channel.lower()}_{line_code.lower()}.png"
        output = output_dir / filename
        _plot_group(
            selected,
            f"BER x Eb/N0 — {line_code} — {channel}",
            output,
        )
        generated.append(output)
    return generated


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--summary", type=Path, default=Path("results/summary.csv"))
    parser.add_argument("--out", type=Path, default=Path("results/plots"))
    args = parser.parse_args()

    generated = generate_plots(args.summary, args.out)
    for path in generated:
        print(f"Gráfico salvo em {path}")


if __name__ == "__main__":
    main()
