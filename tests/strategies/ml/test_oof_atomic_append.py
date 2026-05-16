"""Atomic-append correctness test for OOF parquet persistence (iter-v3/082).

Root-cause: to_parquet() in-place truncates then streams; a mid-write
interruption leaves no Parquet footer.  Fix: write-to-temp + os.replace().

This test exercises the append path under the worst-case concurrency the
runner actually produces: N sequential callers sharing one path, each
flushing a disjoint batch of rows.  (True multi-process races are
impossible in the runner — outer symbol loop + serial walk-forward months +
study.optimize n_jobs=1 — so thread-based concurrency is the correct model
for a stress test.)

Assertions:
  1. The final parquet is readable (no corrupt footer).
  2. Row count == sum of all batch sizes (no row lost, no row duplicated).
  3. The 6 required columns are present.
"""

from __future__ import annotations

import threading
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from crypto_trade.strategies.ml.optimization import optimize_and_train

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

N_CANDLES = 120
N_FEATURES = 4
N_TRIALS = 3
CV_SPLITS = 2
REQUIRED_COLUMNS = {
    "trial_id",
    "symbol",
    "train_month",
    "fold_idx",
    "candle_open_time_ms",
    "oof_return",
}


def _make_data(seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    n = N_CANDLES
    return {
        "features": rng.standard_normal((n, N_FEATURES)).astype(np.float32),
        "labels": rng.choice([-1, 1], size=n).astype(np.intp),
        "weights": np.ones(n, dtype=np.float64),
        "long_pnls": rng.uniform(-0.02, 0.02, size=n).astype(np.float64),
        "short_pnls": rng.uniform(-0.02, 0.02, size=n).astype(np.float64),
        "open_times": np.arange(
            1_600_000_000_000,
            1_600_000_000_000 + n * 28_800_000,
            28_800_000,
            dtype=np.int64,
        )[:n],
        "symbols_arr": np.full(n, "TSTUSDT", dtype=object),
        "columns": [f"f{i}" for i in range(N_FEATURES)],
    }


def _run_one_append(data: dict, path: Path, month: str, seed: int) -> None:
    """Call optimize_and_train once, appending to shared path."""
    optimize_and_train(
        train_features=data["features"],
        train_labels=data["labels"],
        all_columns=data["columns"],
        long_pnls=data["long_pnls"],
        short_pnls=data["short_pnls"],
        n_trials=N_TRIALS,
        cv_splits=CV_SPLITS,
        seed=seed,
        verbose=0,
        sample_weights=data["weights"],
        open_times=data["open_times"],
        ternary=False,
        cv_gap=0,
        oof_persist_path=path,
        train_month=month,
        symbols_arr=data["symbols_arr"],
    )


# ---------------------------------------------------------------------------
# Test 1 — sequential append: N calls accumulate rows correctly
# ---------------------------------------------------------------------------


def test_sequential_append_row_count(tmp_path: Path) -> None:
    """N sequential appends must produce exactly N × rows_per_call rows."""
    out_path = tmp_path / "trial_oof_returns.parquet"
    data = _make_data()
    n_calls = 4

    # Run first call to measure rows_per_call
    _run_one_append(data, out_path, month="2024-01", seed=1)
    rows_per_call = len(pd.read_parquet(out_path))

    # Run remaining calls
    for i in range(1, n_calls):
        _run_one_append(data, out_path, month=f"2024-0{i + 1}", seed=i + 1)

    final = pd.read_parquet(out_path)
    expected = rows_per_call * n_calls
    assert len(final) == expected, (
        f"Sequential append: expected {expected} rows ({n_calls} calls × {rows_per_call}), "
        f"got {len(final)}.  Rows lost = {expected - len(final)}."
    )
    missing_cols = REQUIRED_COLUMNS - set(final.columns)
    assert not missing_cols, f"Missing columns after sequential append: {missing_cols}"


# ---------------------------------------------------------------------------
# Test 2 — concurrent append: threads sharing one path, row count exact
# ---------------------------------------------------------------------------


def test_concurrent_append_row_count(tmp_path: Path) -> None:
    """N concurrent thread-appenders must produce exactly N × rows_per_call rows.

    This is a stress test for the atomic-write fix.  Without os.replace(),
    threads racing to_parquet() in-place produce corrupt footers.
    """
    out_path = tmp_path / "trial_oof_returns.parquet"
    data = _make_data()
    n_threads = 5

    # Calibrate rows_per_call with a single serial call first.
    calibrate_path = tmp_path / "calibrate.parquet"
    _run_one_append(data, calibrate_path, month="2024-01", seed=99)
    rows_per_call = len(pd.read_parquet(calibrate_path))
    assert rows_per_call > 0, "Calibration call produced 0 rows — data too small?"

    errors: list[str] = []

    def worker(idx: int) -> None:
        try:
            _run_one_append(data, out_path, month=f"2024-{idx + 1:02d}", seed=idx)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"Thread {idx}: {exc}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, "Thread errors:\n" + "\n".join(errors)

    # The parquet must be readable (no corrupt footer).
    try:
        final = pd.read_parquet(out_path)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(f"Parquet unreadable after concurrent appends: {exc}")

    expected = rows_per_call * n_threads
    assert len(final) == expected, (
        f"Concurrent append: expected {expected} rows ({n_threads} threads × {rows_per_call}), "
        f"got {len(final)}.  Rows lost = {expected - len(final)}."
    )
    missing_cols = REQUIRED_COLUMNS - set(final.columns)
    assert not missing_cols, f"Missing columns after concurrent append: {missing_cols}"
