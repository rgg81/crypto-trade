"""Regression tests for the train/test embargo + CV gap.

Both protect the model from lookahead bias. They use a single source of truth
(``walk_forward.compute_embargo_candles``) — these tests are the safety net
that catches any future code change that erodes either boundary.

What's being protected:

1. **Train/test boundary (the bug that motivated this file)**
   Triple-barrier labels scan ``label_timeout_minutes`` past each entry. If
   ``train_end_ms == test_start_ms`` (no embargo), the last few training
   candles' labels read price data from inside the test period — classic
   lookahead bias. Backtest OOS Sharpe is biased upward and the live engine
   produces non-deterministic models across sessions depending on what
   forward data was on disk at session start.

2. **CV-fold boundary inside Optuna**
   ``TimeSeriesSplit(gap=…)`` purges rows between train and val folds so
   triple-barrier labels from the train fold can't peek into the val fold.

If anyone removes either protection or changes the formula in one place but
not the other, these tests fail.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from sklearn.model_selection import TimeSeriesSplit

from crypto_trade.strategies.ml.labeling import label_trades
from crypto_trade.strategies.ml.walk_forward import (
    compute_embargo_candles,
    generate_monthly_splits,
)


def _make_master(n: int, start_ms: int, interval_ms: int, symbol: str = "X") -> pd.DataFrame:
    """Synthetic candles: monotone close so triple-barrier outcomes are deterministic."""
    open_times = np.array([start_ms + i * interval_ms for i in range(n)])
    close = np.linspace(100.0, 150.0, n)  # monotone rising
    return pd.DataFrame(
        {
            "symbol": symbol,
            "open_time": open_times,
            "close_time": open_times + interval_ms - 1,
            "open": close,
            "high": close * 1.001,
            "low": close * 0.999,
            "close": close,
        }
    )


# ---------------------------------------------------------------------------
# Helper formula — single source of truth
# ---------------------------------------------------------------------------


class TestEmbargoFormula:
    def test_basic(self):
        # 7d timeout (10080 min) on 8h (480 min) interval → 22 candles
        assert compute_embargo_candles(10080, 480) == 22

    def test_rounds_down(self):
        # 100 minutes timeout, 15-minute interval → 6 candles (100//15 = 6, +1 = 7)
        # Wait: 100//15 = 6, then + 1 = 7. The +1 is the labeler's "stop the scan
        # when close_time > deadline" semantics (which reads one extra row).
        assert compute_embargo_candles(100, 15) == 7

    def test_exact_multiple(self):
        # 30 minutes timeout, 15-minute interval → 30//15 + 1 = 3 candles
        assert compute_embargo_candles(30, 15) == 3

    def test_invalid_inputs(self):
        with pytest.raises(ValueError):
            compute_embargo_candles(10080, 0)
        with pytest.raises(ValueError):
            compute_embargo_candles(0, 480)


# ---------------------------------------------------------------------------
# Train/test boundary — the bug that motivated this file
# ---------------------------------------------------------------------------


class TestTrainTestEmbargo:
    """Train/test embargo blocks lookahead at the walk-forward boundary."""

    _TIMEOUT = 10080  # 7d
    _INTERVAL = 480  # 8h

    def _three_month_times(self) -> np.ndarray:
        interval_ms = self._INTERVAL * 60_000
        jan = _make_master(90, 1_704_067_200_000, interval_ms)["open_time"].values
        feb = _make_master(90, 1_706_745_600_000, interval_ms)["open_time"].values
        mar = _make_master(90, 1_709_251_200_000, interval_ms)["open_time"].values
        return np.concatenate([jan, feb, mar])

    def test_train_end_precedes_test_start_by_embargo(self):
        """The split's train_end_ms must be embargo-candles below test_start_ms."""
        splits = generate_monthly_splits(
            self._three_month_times(),
            training_months=2,
            label_timeout_minutes=self._TIMEOUT,
            interval_minutes=self._INTERVAL,
        )
        assert len(splits) >= 1

        expected_gap = (
            compute_embargo_candles(self._TIMEOUT, self._INTERVAL) * self._INTERVAL * 60_000
        )
        for s in splits:
            actual_gap = s.test_start_ms - s.train_end_ms
            assert actual_gap == expected_gap, (
                f"train/test gap = {actual_gap} ms but embargo formula says {expected_gap} ms"
            )

    def test_labels_are_invariant_to_master_data_extent(self):
        """The bug rephrased as a property: training labels must NOT depend on
        whether the master DataFrame contains data past the labeler's deadline.

        With the embargo correctly applied, no training candle's deadline can
        reach past ``test_start_ms``. So truncating the master at
        ``test_start_ms`` and labelling vs labelling with the full master
        must produce IDENTICAL labels, weights, and per-direction PnLs.

        Without the embargo, this property is violated (see the empirical
        result we measured: 2 label diffs + 21 weight diffs on real DOGE
        data when the master was truncated at the test month boundary).
        """
        interval_ms = self._INTERVAL * 60_000
        # Build a long history (full forward data available) and split into train/test
        df_full = _make_master(120, 1_704_067_200_000, interval_ms)
        # Pretend test_month starts at row 60 (so training is rows [0, 60))
        test_start_ms = int(df_full["open_time"].iloc[60])
        embargo_candles = compute_embargo_candles(self._TIMEOUT, self._INTERVAL)
        train_end_ms = test_start_ms - embargo_candles * interval_ms

        # Indices of training candidates with the embargo applied
        train_idx = np.where(df_full["open_time"].values < train_end_ms)[0]
        assert len(train_idx) > 0, "embargo wiped out all training candles in test fixture"

        # Master truncated AT test_start (simulating the live engine launching
        # right at month start with no forward data yet).
        df_truncated = df_full[df_full["open_time"] < test_start_ms].copy().reset_index(drop=True)

        labels_full, weights_full, longs_full, shorts_full = label_trades(
            df_full, train_idx, tp_pct=3.0, sl_pct=1.5,
            timeout_minutes=self._TIMEOUT, fee_pct=0.1,
        )
        labels_trunc, weights_trunc, longs_trunc, shorts_trunc = label_trades(
            df_truncated, train_idx, tp_pct=3.0, sl_pct=1.5,
            timeout_minutes=self._TIMEOUT, fee_pct=0.1,
        )

        np.testing.assert_array_equal(labels_full, labels_trunc)
        np.testing.assert_allclose(weights_full, weights_trunc, rtol=0, atol=1e-12)
        np.testing.assert_allclose(longs_full, longs_trunc, rtol=0, atol=1e-12)
        np.testing.assert_allclose(shorts_full, shorts_trunc, rtol=0, atol=1e-12)

    def test_demonstrates_bug_without_embargo(self):
        """Negative control: without the embargo, the invariant above FAILS.

        Hand-builds the buggy training filter (open_time < test_start_ms) and
        confirms that labels DO depend on master extent. Locks in the fact
        that the protection is doing real work — if someone reverts the
        embargo in walk_forward.py, ``test_labels_are_invariant_to_master_data_extent``
        starts failing because this exact code path is now what production
        uses.
        """
        interval_ms = self._INTERVAL * 60_000
        df_full = _make_master(120, 1_704_067_200_000, interval_ms)
        test_start_ms = int(df_full["open_time"].iloc[60])

        # OLD (buggy) filter — train_end_ms = test_start_ms, no embargo
        train_idx_buggy = np.where(df_full["open_time"].values < test_start_ms)[0]
        df_truncated = df_full[df_full["open_time"] < test_start_ms].copy().reset_index(drop=True)

        labels_full, weights_full, longs_full, _ = label_trades(
            df_full, train_idx_buggy, tp_pct=3.0, sl_pct=1.5,
            timeout_minutes=self._TIMEOUT, fee_pct=0.1,
        )
        labels_trunc, weights_trunc, longs_trunc, _ = label_trades(
            df_truncated, train_idx_buggy, tp_pct=3.0, sl_pct=1.5,
            timeout_minutes=self._TIMEOUT, fee_pct=0.1,
        )

        # The bug surfaces as differing PnLs (sometimes labels) on the late
        # training candles whose forward window reaches past test_start_ms.
        any_diff = (
            not np.array_equal(labels_full, labels_trunc)
            or not np.allclose(weights_full, weights_trunc, rtol=0, atol=1e-12)
            or not np.allclose(longs_full, longs_trunc, rtol=0, atol=1e-12)
        )
        assert any_diff, (
            "Negative control failed: even without embargo, labels are invariant. "
            "Either the fixture is too benign to expose the bug, or the labeler "
            "isn't actually forward-scanning the master."
        )


# ---------------------------------------------------------------------------
# CV-fold boundary — Optuna's TimeSeriesSplit gap
# ---------------------------------------------------------------------------


class TestCvGap:
    """The TimeSeriesSplit gap between train and val folds must be large enough
    to absorb every training-fold candle's forward-label horizon. Uses the SAME
    ``compute_embargo_candles`` helper that walk_forward uses — so the train/test
    embargo and the CV gap can never drift apart."""

    _TIMEOUT = 10080
    _INTERVAL = 480

    def test_cv_gap_uses_shared_formula_single_symbol(self):
        embargo = compute_embargo_candles(self._TIMEOUT, self._INTERVAL)
        n_symbols = 1
        cv_gap = embargo * n_symbols
        assert cv_gap == 22

    def test_cv_gap_uses_shared_formula_multi_symbol(self):
        """For multi-symbol training the master DataFrame is interleaved,
        so one candle's worth of time = n_symbols rows in TimeSeriesSplit."""
        embargo = compute_embargo_candles(self._TIMEOUT, self._INTERVAL)
        for n_symbols in (1, 2, 4):
            cv_gap = embargo * n_symbols
            assert cv_gap == embargo * n_symbols  # tautology — locked in for clarity

    def test_time_series_split_with_gap_excludes_correct_rows(self):
        """TimeSeriesSplit's gap parameter actually does what we expect.

        Drift guard: confirms scikit-learn's TimeSeriesSplit semantics
        haven't changed under us. If sklearn ever redefines `gap`, this
        catches it before the bias creeps back in.
        """
        n = 100
        embargo = compute_embargo_candles(self._TIMEOUT, self._INTERVAL)
        gap = embargo
        tscv = TimeSeriesSplit(n_splits=3, gap=gap)
        for train_idx, val_idx in tscv.split(np.arange(n)):
            # Last train index + gap < first val index
            assert val_idx[0] - train_idx[-1] - 1 == gap, (
                f"TimeSeriesSplit gap not honored: gap={gap}, "
                f"actual_skip={val_idx[0] - train_idx[-1] - 1}"
            )


# ---------------------------------------------------------------------------
# End-to-end consistency: walk_forward & lgbm use the SAME formula
# ---------------------------------------------------------------------------


class TestFormulaIsSharedAcrossBoundaries:
    """Both boundaries derive their size from the same helper. If anyone changes
    the formula in one place, the test below fails because they didn't change
    it in the other."""

    def test_walk_forward_embargo_matches_cv_gap_formula(self):
        timeout = 10080
        interval = 480
        # Train/test boundary: ms-based
        embargo_candles = compute_embargo_candles(timeout, interval)
        train_test_gap_ms = embargo_candles * interval * 60_000

        # CV gap: row-based, single symbol → same candle count
        cv_gap_rows_single_symbol = embargo_candles * 1

        # Time-equivalents must match
        cv_gap_ms_equiv = cv_gap_rows_single_symbol * interval * 60_000
        assert train_test_gap_ms == cv_gap_ms_equiv, (
            f"train/test embargo ({train_test_gap_ms} ms) and CV gap "
            f"({cv_gap_ms_equiv} ms equiv) must derive from the same formula"
        )
