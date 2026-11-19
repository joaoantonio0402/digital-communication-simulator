import csv
import sys
from pathlib import Path

# Allow `python src/experiments.py` as well as `python -m src.experiments`.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import numpy as np

from src import experiments
from src.plot_results import generate_plots, load_summary


def test_experiments_shape_and_reproducibility():
    a = experiments.run_experiments(800, 2, [4, 12])
    b = experiments.run_experiments(800, 2, [4, 12])
    # 2 reps x 2 linhas x 3 modulações x 2 canais x 2 valores de Eb/N0
    assert len(a) == 2 * 2 * 3 * 2 * 2
    assert [r["errors"] for r in a] == [r["errors"] for r in b]
    assert all(r["n_bits"] == 800 for r in a)


def test_high_snr_is_nearly_error_free_in_awgn():
    rows = experiments.run_experiments(8000, 1, [16])
    awgn_nrz_bpsk = [r for r in rows if r["channel"] == "AWGN"
                     and r["line_code"] == "NRZ" and r["modulation"] == "BPSK"]
    assert awgn_nrz_bpsk[0]["ber"] == 0.0


def test_summary_and_csv(tmp_path):
    rows = experiments.run_experiments(800, 3, [4])
    summary = experiments.summarize(rows)
    assert len(summary) == 2 * 3 * 2 * 1
    assert all(s["n_reps"] == 3 and 0.0 <= s["ber_mean"] <= 1.0 for s in summary)
    path = tmp_path / "raw.csv"
    experiments.write_csv(path, rows, experiments.RAW_FIELDS)
    with path.open(encoding="utf-8") as handle:
        assert len(list(csv.DictReader(handle))) == len(rows)


def test_plot_generation(tmp_path):
    rows = experiments.run_experiments(800, 3, [4])
    summary_path = tmp_path / "summary.csv"
    experiments.write_csv(summary_path, experiments.summarize(rows))
    assert len(load_summary(summary_path)) == 12
    plots = generate_plots(summary_path, tmp_path / "plots")
    assert len(plots) == 4
    assert all(path.is_file() and path.stat().st_size > 0 for path in plots)

def test_theory_matches_simulation():
    import math

    import pytest

    from src.link import ber_theory, q_function

    expected = q_function(math.sqrt(2 * 10 ** 0.6))
    assert ber_theory("NRZ", "BPSK", 6) == pytest.approx(expected)
    assert ber_theory("NRZ", "16-QAM", 6) == pytest.approx(0.0279, abs=5e-4)
    rows = experiments.run_experiments(100_000, 1, [6])
    for r in rows:
        if r["channel"] == "AWGN":
            theory = ber_theory(r["line_code"], r["modulation"], r["ebn0_db"])
            assert r["ber"] == pytest.approx(theory, rel=0.15), (r["line_code"], r["modulation"])


def test_consistency_message_recovered_when_ideal_or_high_snr():
    from src.analysis import DEFAULT_MESSAGE, build_consistency_report, transmit

    for line in ("NRZ", "Manchester"):
        for mod in ("BPSK", "QPSK", "16-QAM"):
            assert transmit(DEFAULT_MESSAGE, line, mod, None, None, 1)["ok"]
            assert transmit(DEFAULT_MESSAGE, line, mod, "AWGN", 30.0, 1)["ok"]
    report = build_consistency_report(DEFAULT_MESSAGE, 2026)
    assert "Canal ideal" in report and "NÃO" in report


def test_analysis_outputs(tmp_path):
    import pytest

    from src import analysis

    rows = experiments.run_experiments(800, 3, list(experiments.EBN0_DB))
    summary = tmp_path / "summary.csv"
    experiments.write_csv(summary, experiments.summarize(rows))
    outputs = analysis.run_all(summary, tmp_path / "plots", tmp_path)
    assert len(outputs) == 7
    assert all(p.is_file() and p.stat().st_size > 0 for p in outputs)
    x, y = np.array([0.0, 2.0, 4.0]), np.array([1e-1, 1e-3, 1e-5])
    assert analysis.ebn0_for_ber(x, y, 1e-2, 1e-6) == pytest.approx(1.0)