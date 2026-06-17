"""Look-ahead safety regression tests for the iter-v1/028 META-LABELING (M2) layer.

The M2 classifier (``MetaLabelingStrategy._train_m2_for_month``) is trained on
whether PAST M1 trades won or lost.  The load-bearing look-ahead concern: M2 must
train ONLY on M1 outcomes whose labels resolved BEFORE the test window.  This is
guaranteed by two mechanisms that these tests pin:

1. **M2 training-index selection** uses exactly the M1 walk-forward split window
   ``[split.train_start_ms, split.train_end_ms)`` — the SAME purged+embargoed
   boundary as M1 (lgbm.py ``_train_m2_for_month`` Step 1).  Appending FUTURE
   candles (test-window rows and beyond) must NOT change the selected training
   set, and no selected row may reach into the embargo gap or the test window.

2. **The embargo equation** ``train_end_ms = test_start_ms - embargo_ms`` holds on
   every walk-forward split the inner M1 builds (walk_forward.py:113).  Because the
   embargo equals the label forward-scan horizon, an M1 trade entered at the last
   training candle cannot have its win/loss label resolved by data inside the test
   month — so the M2 target (did this M1 trade win?) is leak-free.

3. **M2 feature values are the test-month parquet rows the engine reads at decision
   time** (``_get_m2_features`` reads ``_m2_test_month_features``, loaded over the
   disjoint test window).  M2 is never trained on test-window rows.

These tests intentionally avoid a full backtest: they exercise the boundary
arithmetic directly and the real ``generate_monthly_splits`` / wiring config.
"""

from __future__ import annotations

import numpy as np
import pytest

from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy
from crypto_trade.strategies.ml.walk_forward import (
    compute_embargo_candles,
    generate_monthly_splits,
)

# 8h candle geometry (matches the real ETH parquet origin used by iter-028).
INTERVAL_MIN = 8 * 60  # 480
INTERVAL_MS = INTERVAL_MIN * 60 * 1000  # 28_800_000
START_MS = 1_577_836_800_000  # 2020-01-01 00:00:00 UTC

# iter-v1/028 M1 config: fixed_horizon N=42 (14d) let-winners-run.
LABEL_TIMEOUT_MIN = 20160  # 14d at 8h == 42 candles

# iter-v1/028 M2 feature set (the 15-col positioning/leverage/regime set, brief §3.2).
M2_FEATURES = [
    "funding_rate_zscore_30",
    "funding_rate_zscore_90",
    "btc_funding_spread_30_90",
    "oi_delta_30_z90",
    "oi_price_divergence_30",
    "basis_zscore_30",
    "long_short_zscore_30",
    "vol_taker_buy_ratio",
    "hurst_100",
    "trend_adx_14",
    "vol_natr_21",
    "mom_rsi_9",
    "regime_momentum_signed_5d",
    "stat_autocorr_lag1",
    "mr_pct_from_high_5",
]
# iter-v1/028 M1 19-col HYBRID (V1_BTC_ITER009_FEATURES).
M1_FEATURES = [
    "trend_adx_7",
    "vol_garman_klass_10",
    "vol_atr_5",
    "vol_taker_buy_ratio",
    "vol_taker_buy_ratio_sma_5",
    "vol_mfi_7",
    "mom_rsi_9",
    "stat_autocorr_lag1",
    "mr_pct_from_high_5",
    "vol_cmf_10",
    "ent_shannon_10",
    "trend_adx_14",
    "trend_supertrend_14_3",
    "btc_funding_spread_30_90",
    "funding_rate_zscore_30",
    "stat_autocorr_lag5",
    "vol_range_spike_72",
    "mr_rsi_extreme_14",
    "stat_kurtosis_20",
]


def _select_m2_train_indices(
    open_time_arr: np.ndarray, train_start_ms: int, train_end_ms: int
) -> np.ndarray:
    """Mirror lgbm.py _train_m2_for_month Step 1 index selection EXACTLY.

    train_indices = where(open_time >= train_start_ms AND open_time < train_end_ms)
    """
    return np.where((open_time_arr >= train_start_ms) & (open_time_arr < train_end_ms))[0]


class TestM2TrainingBoundaryPastOnly:
    """The M2 training window selection is past-only w.r.t. the test month."""

    def test_appending_future_candles_does_not_change_m2_training_set(self):
        """THE M2 look-ahead test: appending FUTURE candles (test-window rows +
        beyond) must NOT change which rows M2 trains on.  If the selection ever
        peeked at >= train_end_ms, this set would grow."""
        # 30 months of 8h candles so a 24-month-train split exists.
        n = 30 * 90  # ~90 candles/month
        open_times = START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS

        splits = generate_monthly_splits(
            open_times,
            training_months=24,
            label_timeout_minutes=LABEL_TIMEOUT_MIN,
            interval_minutes=INTERVAL_MIN,
        )
        assert splits, "expected at least one walk-forward split"
        split = splits[0]

        before = _select_m2_train_indices(open_times, split.train_start_ms, split.train_end_ms)
        assert len(before) > 0

        # Append 500 FUTURE candles (well into and past the test window).
        future = open_times[-1] + np.arange(1, 501, dtype=np.int64) * INTERVAL_MS
        open_times_ext = np.concatenate([open_times, future])
        after = _select_m2_train_indices(open_times_ext, split.train_start_ms, split.train_end_ms)

        np.testing.assert_array_equal(
            before,
            after,
            err_msg=(
                "LOOK-AHEAD LEAK: M2 training-index set changed after appending "
                "future candles — the selection peeked at open_time >= train_end_ms."
            ),
        )

    def test_no_m2_training_row_reaches_train_end(self):
        """Every selected M2 training row has open_time < train_end_ms (strict)."""
        n = 30 * 90
        open_times = START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS
        splits = generate_monthly_splits(
            open_times, 24, label_timeout_minutes=LABEL_TIMEOUT_MIN, interval_minutes=INTERVAL_MIN
        )
        for split in splits:
            idx = _select_m2_train_indices(open_times, split.train_start_ms, split.train_end_ms)
            if len(idx) == 0:
                continue
            assert open_times[idx].max() < split.train_end_ms
            # And none reach into the test window.
            assert open_times[idx].max() < split.test_start_ms

    def test_embargo_gap_rows_excluded_from_m2_training(self):
        """Rows in the embargo gap [train_end_ms, test_start_ms) are NEVER used by
        M2 training — they are the purged label-leakage buffer."""
        n = 30 * 90
        open_times = START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS
        splits = generate_monthly_splits(
            open_times, 24, label_timeout_minutes=LABEL_TIMEOUT_MIN, interval_minutes=INTERVAL_MIN
        )
        split = splits[0]
        idx = _select_m2_train_indices(open_times, split.train_start_ms, split.train_end_ms)
        selected_ot = set(open_times[idx].tolist())
        gap_mask = (open_times >= split.train_end_ms) & (open_times < split.test_start_ms)
        gap_ot = set(open_times[gap_mask].tolist())
        assert selected_ot.isdisjoint(gap_ot), (
            "LOOK-AHEAD LEAK: M2 training set overlaps the embargo gap "
            "[train_end_ms, test_start_ms) — purged labels would peek into the test month."
        )
        # The embargo gap must be non-empty for a 14d label horizon (sanity).
        assert len(gap_ot) > 0


class TestM2EmbargoEquation:
    """The embargo equation that makes the M2 target leak-free."""

    def test_train_end_equals_test_start_minus_embargo(self):
        """walk_forward.py:113 — train_end_ms = test_start_ms - embargo_ms on EVERY
        split.  This is the boundary M2 trains against (lgbm.py Step 1)."""
        n = 30 * 90
        open_times = START_MS + np.arange(n, dtype=np.int64) * INTERVAL_MS
        embargo_candles = compute_embargo_candles(LABEL_TIMEOUT_MIN, INTERVAL_MIN)
        embargo_ms = embargo_candles * INTERVAL_MS
        # 14d / 8h = 42, + 1 = 43 candles of embargo.
        assert embargo_candles == LABEL_TIMEOUT_MIN // INTERVAL_MIN + 1 == 43

        splits = generate_monthly_splits(
            open_times, 24, label_timeout_minutes=LABEL_TIMEOUT_MIN, interval_minutes=INTERVAL_MIN
        )
        assert splits
        for split in splits:
            assert split.train_end_ms == split.test_start_ms - embargo_ms, (
                f"EMBARGO REGRESSION on {split.test_month}: "
                f"train_end_ms={split.train_end_ms} != "
                f"test_start_ms - embargo_ms={split.test_start_ms - embargo_ms}"
            )

    def test_embargo_covers_full_label_horizon(self):
        """The embargo span (in candles) >= the label forward-scan horizon (42),
        so an M1 trade at the last training candle cannot resolve inside the test
        month — its M2 win/loss target is leak-free."""
        embargo_candles = compute_embargo_candles(LABEL_TIMEOUT_MIN, INTERVAL_MIN)
        label_horizon_candles = LABEL_TIMEOUT_MIN // INTERVAL_MIN  # 42
        assert embargo_candles >= label_horizon_candles


class TestM2WiringConfig:
    """The iter-028 wiring config is threaded correctly (the #1 risk: M2 must
    filter the trend-state primary, not the LightGbm-learned direction)."""

    def _make_iter028_strategy(self) -> MetaLabelingStrategy:
        return MetaLabelingStrategy(
            training_months=24,
            n_trials=2,
            ensemble_seeds=[42],
            feature_columns=list(M1_FEATURES),  # M1 19-col HYBRID
            m2_feature_columns=list(M2_FEATURES),  # M2 15-col positioning set
            m2_veto_threshold=0.45,
            include_m1_direction=True,
            use_atr_labeling=False,
            label_mode="fixed_horizon",
            label_timeout_minutes=LABEL_TIMEOUT_MIN,
            atr_tp_multiplier=100.0,
            atr_sl_multiplier=1.45,
            features_dir="data/features",
            # The iter-027 trend-state primary threaded into the inner M1:
            enable_trend_state_dir=True,
            trend_state_sma_window=200,
            trend_state_symbol="ETHUSDT",
            enable_trend_strength_gate=True,
            trend_strength_atr_window=14,
            trend_strength_quantile=0.40,
            specialist_mode=True,
            specialist_seed_count=5,
            verbose=0,
        )

    def test_m2_veto_threshold_is_configurable_045(self):
        """The M2 veto threshold is 0.45 (NOT the hardcoded 0.50 default)."""
        strat = self._make_iter028_strategy()
        assert strat._m2_veto_threshold == 0.45

    def test_m2_base_cols_are_the_distinct_positioning_set(self):
        """M2 reads the 15-col positioning set, NOT M1's 19-col HYBRID."""
        strat = self._make_iter028_strategy()
        assert strat._m2_base_cols == list(M2_FEATURES)
        assert len(strat._m2_base_cols) == 15
        # M2 input vector = 15 base + m1_confidence + m1_direction = 17.
        assert strat._m2_feature_cols == [*M2_FEATURES, "m1_confidence", "m1_direction"]
        assert len(strat._m2_feature_cols) == 17

    def test_m1_runs_the_trend_state_primary_not_learned_direction(self):
        """THE #1-risk guard: the inner M1 has the deterministic trend-state
        direction + conviction gate enabled, on ETH's own close — so M2 filters
        the merged iter-027 primary, not a LightGbm-learned sign."""
        strat = self._make_iter028_strategy()
        m1 = strat._m1
        assert m1._enable_trend_state_dir is True
        assert m1._trend_state_sma_window == 200
        assert m1._trend_state_symbol == "ETHUSDT"
        assert m1._enable_trend_strength_gate is True
        assert m1._trend_strength_quantile == 0.40
        # M1 uses the 19-col HYBRID (NOT the M2 set) + the let-winners-run label.
        assert list(m1.feature_columns) == list(M1_FEATURES)
        assert m1.use_atr_labeling is False
        # Specialist bagging stack (K independent Optuna studies), like iter-027.
        assert m1._specialist_mode is True
        assert m1._specialist_seed_count == 5

    def test_m1_and_m2_feature_sets_are_distinct(self):
        """M1 and M2 read DIFFERENT feature sets (wiring-flag #3)."""
        strat = self._make_iter028_strategy()
        assert list(strat._m1.feature_columns) != strat._m2_base_cols


class TestMetaPathOffIsBackwardCompatible:
    """When meta-labeling is configured the iter-v3/017 / iter-v1/030 way
    (no separate M2 set, threshold 0.5, no trend-state), behaviour is preserved."""

    def test_defaults_preserve_v3_017_behaviour(self):
        strat = MetaLabelingStrategy(
            training_months=24,
            n_trials=2,
            ensemble_seeds=[42],
            feature_columns=list(M1_FEATURES),
            verbose=0,
        )
        # No separate M2 set → M2 reuses M1's columns (backwards-compat).
        assert strat._m2_base_cols == list(M1_FEATURES)
        # Default veto threshold 0.5 (Bayes-optimal).
        assert strat._m2_veto_threshold == 0.5
        # Trend-state OFF by default (the inner M1 is a plain LightGbm).
        assert strat._m1._enable_trend_state_dir is False
        assert strat._m1._specialist_mode is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
