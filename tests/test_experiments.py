import csv

import numpy as np

import experiments


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