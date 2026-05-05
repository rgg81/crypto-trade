"""Adversarial tests for per-trial OOF return persistence (iter-v3/003).

Section 3.6.1 specification — 4 mandatory assertions:
(a) calling optimize_and_train with oof_persist_path set creates the parquet.
(b) parquet has the 6 prescribed columns.
(c) trial_id cardinality equals n_trials.
(d) per-trial row count ≈ cv_splits × ~val_set_size (within ±20%).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.strategies.ml.optimization import optimize_and_train

# ---------------------------------------------------------------------------
# Helpers — synthetic data sized for fast CI execution
# ---------------------------------------------------------------------------

N_CANDLES = 200  # small enough to run in <30s
N_FEATURES = 5
N_TRIALS = 5
CV_SPLITS = 3


def _make_synthetic_data(seed: int = 42) -> dict:
    rng = np.random.default_rng(seed)
    n = N_CANDLES
    features = rng.standard_normal((n, N_FEATURES)).astype(np.float32)
    # Binary labels: 50/50 random
    labels = rng.choice([-1, 1], size=n).astype(np.intp)
    # PnL: small random returns ±0.5–2%
    long_pnls = rng.uniform(-0.02, 0.02, size=n).astype(np.float64)
    short_pnls = rng.uniform(-0.02, 0.02, size=n).astype(np.float64)
    weights = np.ones(n, dtype=np.float64)
    open_times = np.arange(
        1_600_000_000_000,  # start epoch ms
        1_600_000_000_000 + n * 28_800_000,  # 8h candles
        28_800_000,
        dtype=np.int64,
    )[:n]
    symbols_arr = np.where(np.arange(n) < n // 2, "AAAUSDT", "BBBUSDT").astype(str)
    columns = [f"feat_{i}" for i in range(N_FEATURES)]
    return {
        "features": features,
        "labels": labels,
        "weights": weights,
        "long_pnls": long_pnls,
        "short_pnls": short_pnls,
        "open_times": open_times,
        "symbols_arr": symbols_arr,
        "columns": columns,
    }


# ---------------------------------------------------------------------------
# (a) parquet file is created when oof_persist_path is set
# ---------------------------------------------------------------------------


def test_oof_parquet_created(tmp_path: Path) -> None:
    """(a) optimize_and_train with oof_persist_path set must create the parquet."""
    data = _make_synthetic_data()
    out_path = tmp_path / "trial_oof_returns.parquet"

    assert not out_path.exists(), "Precondition: file must not exist before call"

    _call_optimize_and_train(data, out_path)

    assert out_path.exists(), (
        "FAIL (a): trial_oof_returns.parquet not created — sub-fix 1b not implemented"
    )


# ---------------------------------------------------------------------------
# (b) parquet has the 6 prescribed columns
# ---------------------------------------------------------------------------

REQUIRED_COLUMNS = {
    "trial_id",
    "symbol",
    "train_month",
    "fold_idx",
    "candle_open_time_ms",
    "oof_return",
}


def test_oof_parquet_schema(tmp_path: Path) -> None:
    """(b) parquet must contain exactly the 6 columns from persistence_schema.csv."""
    data = _make_synthetic_data()
    out_path = tmp_path / "trial_oof_returns.parquet"

    _call_optimize_and_train(data, out_path)

    df = pd.read_parquet(out_path)
    missing = REQUIRED_COLUMNS - set(df.columns)
    assert not missing, (
        f"FAIL (b): parquet missing columns: {missing}. "
        f"Got columns: {list(df.columns)}. "
        "Check sub-fix 1a (buffer dicts) or sub-fix 1b (flush)."
    )


# ---------------------------------------------------------------------------
# (c) trial_id cardinality equals n_trials
# ---------------------------------------------------------------------------


def test_oof_trial_id_cardinality(tmp_path: Path) -> None:
    """(c) number of unique trial_id values must equal n_trials."""
    data = _make_synthetic_data()
    out_path = tmp_path / "trial_oof_returns.parquet"

    _call_optimize_and_train(data, out_path)

    df = pd.read_parquet(out_path)
    n_unique = df["trial_id"].nunique()
    assert n_unique == N_TRIALS, (
        f"FAIL (c): expected trial_id cardinality={N_TRIALS}, got {n_unique}. "
        "Every Optuna trial must contribute at least one row — check sub-fix 1a."
    )


# ---------------------------------------------------------------------------
# (d) per-trial row count ≈ cv_splits × ~val_set_size (within ±20%)
# ---------------------------------------------------------------------------


def test_oof_per_trial_row_count(tmp_path: Path) -> None:
    """(d) per-trial row count must be within ±20% of cv_splits × expected_val_size."""
    data = _make_synthetic_data()
    out_path = tmp_path / "trial_oof_returns.parquet"

    _call_optimize_and_train(data, out_path)

    df = pd.read_parquet(out_path)

    # Expected: each trial sees ~(N_CANDLES / (CV_SPLITS + 1)) validation candles per fold
    # Using TimeSeriesSplit heuristic: val_size ≈ N_CANDLES // (CV_SPLITS + 1)
    expected_val_per_fold = N_CANDLES // (CV_SPLITS + 1)
    expected_rows_per_trial = CV_SPLITS * expected_val_per_fold
    lo = int(expected_rows_per_trial * 0.80)
    hi = int(expected_rows_per_trial * 1.20)

    trial_counts = df.groupby("trial_id").size()
    for tid, cnt in trial_counts.items():
        assert lo <= cnt <= hi, (
            f"FAIL (d): trial_id={tid} has {cnt} rows; "
            f"expected [{lo}, {hi}] (cv_splits={CV_SPLITS} × val_size≈{expected_val_per_fold}). "
            "Check sub-fix 1a — every fold's validation slice must be captured."
        )


# ---------------------------------------------------------------------------
# (e) backwards compatibility: None oof_persist_path produces no parquet
# ---------------------------------------------------------------------------


def test_oof_persist_path_none_no_file(tmp_path: Path) -> None:
    """Backwards compat: oof_persist_path=None must not create any parquet."""
    data = _make_synthetic_data()

    _call_optimize_and_train(data, oof_persist_path=None)

    # No parquet anywhere in tmp_path
    parquets = list(tmp_path.glob("*.parquet"))
    assert not parquets, (
        f"FAIL (e): unexpected parquet files found: {parquets}. "
        "oof_persist_path=None must be a no-op."
    )


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------


def _call_optimize_and_train(data: dict, oof_persist_path: Path | None) -> None:
    """Call optimize_and_train with synthetic data and the supplied persist path."""
    optimize_and_train(
        train_features=data["features"],
        train_labels=data["labels"],
        all_columns=data["columns"],
        long_pnls=data["long_pnls"],
        short_pnls=data["short_pnls"],
        n_trials=N_TRIALS,
        cv_splits=CV_SPLITS,
        seed=42,
        verbose=0,
        sample_weights=data["weights"],
        open_times=data["open_times"],
        ternary=False,
        cv_gap=0,
        oof_persist_path=oof_persist_path,
        train_month="2024-01",
        symbols_arr=data["symbols_arr"],
    )
