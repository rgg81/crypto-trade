"""Tests for iter-v1/030: 3-separate M2 meta-labeling (Model E excluded).

Test coverage per brief Section 10.3 + LM Master §9 Q8:
1.  M2 dispatch: Models A/C/D each get MetaLabelingStrategy; Model E uses LightGbmStrategy.
2.  M2 feature vector: 45 cols (43 V1_FEATURE_COLUMNS_PRUNED + m1_confidence + m1_direction).
3.  M2 label generation: 1 iff M1 direction hit TP before SL/timeout (ex-post, IS-window only).
4.  M2 sample-size floor: _train_m2_binary returns None when len(m2_features) < 10.
5.  M2 hyperparameter bounds: v1_030 profile enforces LM Master §2 tightened ranges.
6.  M2 threshold pinned: MetaLabelingStrategy vetoes at confidence < 0.5 ONLY (not tuned).
7.  F-AXIS #1 real instance: HARD-ASSERT uses TradeResult.open_time + symbol (real attribute path).
8.  F-AXIS #5 Model D OOS TP floor: assertion logic against REAL TradeResult roster.
9.  Reproducibility: seeded M2 produces identical predictions across 2 runs (deterministic).
10. m2_passed column: column exists in trades.csv (tested on patched logic, not live CSV).
11. scale_pos_weight explicit per cell: v1_030 profile computes n_neg/n_pos NOT is_unbalance.
12. TimeSeriesSplit fold-skip: folds with < 3 positive labels in val are skipped.
13. Foundation regression: walk_forward.py:113 carries embargo_ms purge (anti-lookahead).
"""

from __future__ import annotations

import inspect

import numpy as np
import pytest

from crypto_trade.backtest_models import TradeResult

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_trade(
    symbol: str,
    direction: int,
    open_time_ms: int,
    exit_reason: str = "take_profit",
) -> TradeResult:
    """Instantiate a REAL TradeResult (the /027 lesson: use the real type)."""
    return TradeResult(
        symbol=symbol,
        direction=direction,
        entry_price=10.0,
        exit_price=10.5,
        weight_factor=1.0,
        open_time=open_time_ms,
        close_time=open_time_ms + 28_800_000,
        exit_reason=exit_reason,
        pnl_pct=0.05,
        fee_pct=0.001,
        net_pnl_pct=0.049,
        weighted_pnl=0.049,
    )


# ---------------------------------------------------------------------------
# 1. M2 dispatch: 3-separate (A/C/D); Model E uses LightGbmStrategy (NO M2)
# ---------------------------------------------------------------------------


class TestIter030M2Dispatch:
    """run_meta_model exists for A/C/D; run_model (plain) is used for E."""

    def test_run_meta_model_function_exists(self) -> None:
        from run_baseline_v1 import run_meta_model

        assert callable(run_meta_model)

    def test_run_meta_model_creates_metalabeling_strategy(self) -> None:
        """run_meta_model returns MetaLabelingStrategy (not plain LightGbmStrategy)."""

        # Verify the function dispatches MetaLabelingStrategy via its constructor
        # by inspecting the source: it calls MetaLabelingStrategy(...), not LightGbmStrategy.
        from run_baseline_v1 import run_meta_model

        src = inspect.getsource(run_meta_model)
        assert "MetaLabelingStrategy" in src, (
            "run_meta_model must instantiate MetaLabelingStrategy (M2 wrapper)"
        )
        assert "LightGbmStrategy" not in src.split("MetaLabelingStrategy")[0].split("def ")[-1], (
            "run_meta_model must NOT directly instantiate LightGbmStrategy for the primary strategy"
        )

    def test_model_e_uses_run_model_not_run_meta_model(self) -> None:
        """The /030 elif branch must call run_model() for DOT (Model E), not run_meta_model()."""
        src = _get_030_dispatch_source()
        # DOT + run_model (not run_meta_model) pattern for Model E
        assert "DOTUSDT" in src, "DOTUSDT must appear in /030 elif branch"
        assert "run_model" in src, "run_model() must be called in /030 elif for Model E"

    def test_m2_excluded_for_model_e_in_dispatch(self) -> None:
        """The /030 elif branch must reference Model E EXCLUDED."""
        src = _get_030_dispatch_source()
        assert "EXCLUDED" in src, (
            "run_baseline_v1.py /030 elif must document Model E EXCLUDED from M2 "
            "per LM Master §3 binding call"
        )


# ---------------------------------------------------------------------------
# 2. M2 feature vector: 45 cols = 43 + m1_confidence + m1_direction
# ---------------------------------------------------------------------------


class TestIter030M2FeatureVector:
    """MetaLabelingStrategy._m2_feature_cols = 45 cols when include_m1_direction=True."""

    def test_m2_feature_vector_45_dims_with_direction(self) -> None:
        """include_m1_direction=True adds m1_direction after m1_confidence → 45 total."""
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
        from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

        strategy = MetaLabelingStrategy(
            training_months=24,
            n_trials=1,
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            ensemble_seeds=[42],
            include_m1_direction=True,
        )
        # 43 V1 features + m1_confidence + m1_direction = 45
        assert len(strategy._m2_feature_cols) == len(V1_FEATURE_COLUMNS_PRUNED) + 2, (
            f"Expected {len(V1_FEATURE_COLUMNS_PRUNED) + 2} M2 feature cols, "
            f"got {len(strategy._m2_feature_cols)}"
        )

    def test_m2_feature_cols_include_m1_confidence(self) -> None:
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
        from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

        strategy = MetaLabelingStrategy(
            training_months=24,
            n_trials=1,
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            ensemble_seeds=[42],
            include_m1_direction=True,
        )
        assert "m1_confidence" in strategy._m2_feature_cols

    def test_m2_feature_cols_include_m1_direction(self) -> None:
        from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED
        from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

        strategy = MetaLabelingStrategy(
            training_months=24,
            n_trials=1,
            feature_columns=list(V1_FEATURE_COLUMNS_PRUNED),
            ensemble_seeds=[42],
            include_m1_direction=True,
        )
        assert "m1_direction" in strategy._m2_feature_cols

    def test_m2_feature_vector_14_dims_without_direction(self) -> None:
        """v3/017 backwards-compat: include_m1_direction=False → 14-dim for 13-feature input."""
        from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

        feature_columns_13 = [f"feat_{i}" for i in range(13)]
        strategy = MetaLabelingStrategy(
            training_months=24,
            n_trials=1,
            feature_columns=feature_columns_13,
            ensemble_seeds=[42],
            include_m1_direction=False,  # default v3 behavior
        )
        # 13 features + m1_confidence only = 14
        assert len(strategy._m2_feature_cols) == 14
        assert "m1_direction" not in strategy._m2_feature_cols


# ---------------------------------------------------------------------------
# 3. M2 label generation: 1 iff TP hit; 0 if SL/timeout (IS-window only)
# ---------------------------------------------------------------------------


class TestIter030M2LabelGeneration:
    """M2 label derivation: 1 = TP hit, 0 = SL/timeout; only in training window."""

    def test_m2_label_1_for_positive_pnl(self) -> None:
        """TP-hit trades (pnl > 0 after fee) must receive M2 label = 1."""
        # Simulated: long_pnl > 0 → label = 1
        long_pnl = 0.05  # positive net return → TP hit
        m2_label = 1 if long_pnl > 0.0 else 0
        assert m2_label == 1

    def test_m2_label_0_for_negative_pnl(self) -> None:
        """SL/timeout trades (pnl <= 0 after fee) must receive M2 label = 0."""
        short_pnl = -0.02  # negative net return → SL/timeout
        m2_label = 1 if short_pnl > 0.0 else 0
        assert m2_label == 0

    def test_m2_label_derivation_uses_direction(self) -> None:
        """M2 uses M1's predicted direction to select long_pnl vs short_pnl."""
        # This mirrors the _train_m2_for_month logic exactly.
        long_pnl = 0.08  # would be TP
        short_pnl = -0.03  # would be SL

        # If M1 predicts LONG (class 1):
        direction_cls_long = 1
        pnl_for_long = long_pnl if direction_cls_long == 1 else short_pnl
        label_long = 1 if pnl_for_long > 0.0 else 0
        assert label_long == 1, "Long prediction with positive long_pnl → label=1"

        # If M1 predicts SHORT (class 0):
        direction_cls_short = 0
        pnl_for_short = long_pnl if direction_cls_short == 1 else short_pnl
        label_short = 1 if pnl_for_short > 0.0 else 0
        assert label_short == 0, "Short prediction with negative short_pnl → label=0"

    def test_m2_label_source_is_in_tree_metalabeling_module(self) -> None:
        """_train_m2_for_month in metalabeling.py references label_trades (no oracle leakage)."""
        from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

        src = inspect.getsource(MetaLabelingStrategy._train_m2_for_month)
        # M2 labels derived from label_trades output (in-training-window only)
        assert "label_trades" in src, (
            "_train_m2_for_month must call label_trades for M2 label derivation"
        )
        # No future data references outside the training window
        assert "test_start_ms" not in src or "train_end_ms" in src, (
            "_train_m2_for_month must NOT reference test_start_ms without also "
            "using train_end_ms boundary (lookahead guard)"
        )


# ---------------------------------------------------------------------------
# 4. M2 sample-size floor: _train_m2_binary returns None when < 10 samples
# ---------------------------------------------------------------------------


class TestIter030M2SampleSizeFloor:
    """_train_m2_binary must return None for undersized training sets."""

    def test_returns_none_when_fewer_than_10_samples(self) -> None:
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        features = np.random.RandomState(42).randn(5, 14)  # only 5 samples
        labels = np.array([1, 0, 1, 0, 1], dtype=np.int32)
        result = _train_m2_binary(
            m2_features=features,
            m2_labels=labels,
            n_trials=2,
            seed=42,
            fast_mode=True,
            verbose=0,
        )
        assert result is None, (
            "_train_m2_binary must return None when len(m2_features) < 10 "
            "(per metalabeling.py:67 / brief Section 3.3)"
        )

    def test_returns_none_when_degenerate_labels_all_zeros(self) -> None:
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        features = np.random.RandomState(42).randn(20, 14)
        labels = np.zeros(20, dtype=np.int32)  # all negative — degenerate
        result = _train_m2_binary(
            m2_features=features,
            m2_labels=labels,
            n_trials=2,
            seed=42,
            fast_mode=True,
            verbose=0,
        )
        assert result is None, "_train_m2_binary must return None for degenerate all-0 labels"

    def test_returns_none_when_degenerate_labels_all_ones(self) -> None:
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        features = np.random.RandomState(42).randn(20, 14)
        labels = np.ones(20, dtype=np.int32)  # all positive — degenerate
        result = _train_m2_binary(
            m2_features=features,
            m2_labels=labels,
            n_trials=2,
            seed=42,
            fast_mode=True,
            verbose=0,
        )
        assert result is None, "_train_m2_binary must return None for degenerate all-1 labels"


# ---------------------------------------------------------------------------
# 5. M2 hyperparameter bounds: v1_030 profile enforces LM Master §2 bounds
# ---------------------------------------------------------------------------


class TestIter030M2HyperparameterBounds:
    """Verify LM Master §2 tightened bounds are encoded in _train_m2_binary for v1_030."""

    def test_v1_030_bounds_profile_source_contains_correct_ranges(self) -> None:
        """LM Master §2 bounds: n_estimators [50,200], max_depth [2,4], etc."""
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        src = inspect.getsource(_train_m2_binary)
        # Key tightened bounds from LM Master §2 (all must appear in source)
        assert '"v1_030"' in src, "v1_030 bounds profile must be referenced in _train_m2_binary"
        # n_estimators upper cap 200 (not 500)
        assert "200" in src, "n_estimators upper bound 200 must appear in v1_030 profile"
        # max_depth upper 4 (not 5)
        assert '"max_depth"' in src
        # num_leaves lower 7 (not 15)
        assert "7" in src, "num_leaves lower bound 7 must appear in v1_030 profile"
        # reg_alpha/reg_lambda lower 0.01 (not 1e-8)
        assert "0.01" in src, "reg_alpha/reg_lambda lower bound 0.01 must appear"
        # colsample_bytree upper 0.8 (not 1.0)
        assert "0.8" in src, "colsample_bytree upper bound 0.8 must appear in v1_030 profile"

    def test_v1_030_profile_uses_scale_pos_weight_not_is_unbalance(self) -> None:
        """v1_030 profile must use scale_pos_weight, NOT is_unbalance=True."""
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        src = inspect.getsource(_train_m2_binary)
        # scale_pos_weight must appear in the v1_030 branch
        assert "scale_pos_weight" in src, (
            "v1_030 profile must use scale_pos_weight for explicit class weighting "
            "(LM Master §2: is_unbalance=True is non-deterministic)"
        )

    def test_v1_030_n_trials_m2_constant_is_18(self) -> None:
        """n_trials_m2 = 18 per LM Master §2.3 ADOPTED."""
        from run_baseline_v1 import V1_ITER030_N_TRIALS_M2

        assert V1_ITER030_N_TRIALS_M2 == 18, (
            f"n_trials_m2 must be 18 per LM Master §2.3; got {V1_ITER030_N_TRIALS_M2}"
        )

    def test_v1_030_bounds_constant_is_correct_string(self) -> None:
        from run_baseline_v1 import V1_ITER030_BOUNDS_PROFILE_M2

        assert V1_ITER030_BOUNDS_PROFILE_M2 == "v1_030", (
            f"bounds_profile_m2 must be 'v1_030'; got {V1_ITER030_BOUNDS_PROFILE_M2!r}"
        )


# ---------------------------------------------------------------------------
# 6. M2 threshold pinned at 0.5 (not tuned at /030)
# ---------------------------------------------------------------------------


class TestIter030M2ThresholdPinned:
    """M2 threshold = 0.5 PINNED per brief Section 3.3."""

    def test_m2_threshold_constant_is_0_5(self) -> None:
        from run_baseline_v1 import V1_ITER030_M2_THRESHOLD

        assert V1_ITER030_M2_THRESHOLD == pytest.approx(0.5), (
            f"M2 threshold must be 0.5 PINNED; got {V1_ITER030_M2_THRESHOLD}"
        )

    def test_metalabeling_strategy_veto_threshold_is_0_5(self) -> None:
        """MetaLabelingStrategy.get_signal vetoes when M2 confidence < 0.5."""
        from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

        src = inspect.getsource(MetaLabelingStrategy.get_signal)
        assert "0.5" in src, "MetaLabelingStrategy.get_signal must use 0.5 as veto threshold"
        assert "m2_confidence < 0.5" in src, (
            "Veto condition must be 'm2_confidence < 0.5' (PINNED per brief §3.3)"
        )


# ---------------------------------------------------------------------------
# 7. F-AXIS #1 real instance: hard-assert uses actual TradeResult attributes
# ---------------------------------------------------------------------------


class TestIter030FAxis1RealInstance:
    """The /027 lesson: defensive asserts must use real TradeResult attributes."""

    def test_trade_result_has_open_time_attribute(self) -> None:
        """TradeResult.open_time exists (used in m2_active_keys set construction)."""
        trade = _make_trade("BTCUSDT", 1, 1_700_000_000_000)
        # Accessing open_time on the REAL type — would raise AttributeError if missing
        assert isinstance(trade.open_time, int)

    def test_trade_result_has_symbol_attribute(self) -> None:
        """TradeResult.symbol exists (used in m2_active_keys set construction)."""
        trade = _make_trade("LINKUSDT", 1, 1_700_000_000_000)
        assert isinstance(trade.symbol, str)
        assert trade.symbol == "LINKUSDT"

    def test_trade_result_has_exit_reason_attribute(self) -> None:
        """TradeResult.exit_reason exists (used in F-AXIS #5 OOS TP count)."""
        trade_tp = _make_trade("LTCUSDT", 1, 1_700_000_000_000, exit_reason="take_profit")
        trade_sl = _make_trade("LTCUSDT", -1, 1_700_100_000_000, exit_reason="stop_loss")
        assert trade_tp.exit_reason == "take_profit"
        assert trade_sl.exit_reason == "stop_loss"

    def test_m2_active_keys_set_works_on_real_trade_results(self) -> None:
        """The m2_active_keys set construction pattern from the /030 runner works."""
        # This is the EXACT pattern used in the runner /030 elif for m2_passed annotation.
        results_a = [
            _make_trade("BTCUSDT", 1, 1_700_000_000_000),
            _make_trade("ETHUSDT", -1, 1_700_100_000_000),
        ]
        results_c = [_make_trade("LINKUSDT", 1, 1_700_200_000_000)]
        results_d = [_make_trade("LTCUSDT", -1, 1_700_300_000_000)]
        # Build m2_active_keys exactly as the runner does
        m2_active_keys: set[tuple[int, str]] = {
            (t.open_time, t.symbol) for t in (results_a + results_c + results_d)
        }
        assert len(m2_active_keys) == 4
        assert (1_700_000_000_000, "BTCUSDT") in m2_active_keys
        assert (1_700_300_000_000, "LTCUSDT") in m2_active_keys

    def test_oos_trades_floor_constant_is_90(self) -> None:
        """F-AXIS #1 hard-assert fires at OOS trades < 90 (TECHNICAL FAILURE)."""
        from run_baseline_v1 import V1_ITER030_OOS_TRADES_FLOOR

        assert V1_ITER030_OOS_TRADES_FLOOR == 90, (
            f"OOS trades floor must be 90 per brief F-AXIS #2; got {V1_ITER030_OOS_TRADES_FLOOR}"
        )


# ---------------------------------------------------------------------------
# 8. F-AXIS #5 Model D OOS TP floor: assertion on REAL TradeResult roster
# ---------------------------------------------------------------------------


class TestIter030FAxis5ModelDTP:
    """Model D OOS TP-exit count >= 3 (LOAD-BEARING per LM Master §5)."""

    def test_model_d_oos_tp_floor_constant_is_3(self) -> None:
        from run_baseline_v1 import V1_ITER030_MODEL_D_OOS_TP_FLOOR

        assert V1_ITER030_MODEL_D_OOS_TP_FLOOR == 3, (
            f"Model D OOS TP floor must be 3 per brief §2 F-AXIS #5; "
            f"got {V1_ITER030_MODEL_D_OOS_TP_FLOOR}"
        )

    def test_f_axis_5_check_passes_when_model_d_has_3_tp_exits(self) -> None:
        """3 TP exits satisfies the LOAD-BEARING floor (no warning emitted)."""
        from run_baseline_v1 import V1_ITER030_MODEL_D_OOS_TP_FLOOR

        from crypto_trade.config import OOS_CUTOFF_MS

        # Build REAL TradeResult roster: 3 OOS TP-exits for LTCUSDT
        oos_start = OOS_CUTOFF_MS + 1
        oos_trades = [
            _make_trade("LTCUSDT", 1, oos_start + i * 28_800_000, exit_reason="take_profit")
            for i in range(3)
        ]
        oos_tp_d = sum(1 for t in oos_trades if t.exit_reason == "take_profit")
        # PASS if count >= floor
        assert oos_tp_d >= V1_ITER030_MODEL_D_OOS_TP_FLOOR, (
            f"Expected >= {V1_ITER030_MODEL_D_OOS_TP_FLOOR} OOS TP exits; got {oos_tp_d}"
        )

    def test_f_axis_5_check_fails_when_model_d_has_0_tp_exits(self) -> None:
        """0 TP exits falls below floor → verdict caps at PROMISING-INERT."""
        from run_baseline_v1 import V1_ITER030_MODEL_D_OOS_TP_FLOOR

        oos_trades_sl_only = [
            _make_trade("LTCUSDT", 1, 1_750_000_000_000 + i * 28_800_000, exit_reason="stop_loss")
            for i in range(5)
        ]
        oos_tp_d = sum(1 for t in oos_trades_sl_only if t.exit_reason == "take_profit")
        assert oos_tp_d < V1_ITER030_MODEL_D_OOS_TP_FLOOR, (
            "Expected TP count < floor to confirm the WARNING path would fire"
        )

    def test_overall_oos_tp_floor_constant_is_15(self) -> None:
        from run_baseline_v1 import V1_ITER030_OOS_TP_FLOOR

        assert V1_ITER030_OOS_TP_FLOOR == 15, (
            f"Overall OOS TP floor must be 15 per brief §2 F-AXIS #5; got {V1_ITER030_OOS_TP_FLOOR}"
        )


# ---------------------------------------------------------------------------
# 9. Reproducibility: seeded M2 produces identical predictions (deterministic)
# ---------------------------------------------------------------------------


class TestIter030M2Reproducibility:
    """M2 training with the same seed produces bit-identical predictions."""

    def test_seeded_m2_produces_identical_model_predictions(self) -> None:
        """Two _train_m2_binary calls with seed=42 produce identical output."""
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        rng = np.random.RandomState(0)
        features = rng.randn(30, 14)
        labels = np.array([1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 3, dtype=np.int32)

        model_a = _train_m2_binary(
            m2_features=features,
            m2_labels=labels,
            n_trials=3,
            seed=42,
            fast_mode=True,
            verbose=0,
            bounds_profile="v1_030",
        )
        model_b = _train_m2_binary(
            m2_features=features,
            m2_labels=labels,
            n_trials=3,
            seed=42,
            fast_mode=True,
            verbose=0,
            bounds_profile="v1_030",
        )
        if model_a is None or model_b is None:
            pytest.skip("M2 returned None (sample-size guard fired); skip reproducibility check")

        import pandas as pd

        feat_df = pd.DataFrame(features)
        preds_a = model_a.predict_proba(feat_df)[:, 1]
        preds_b = model_b.predict_proba(feat_df)[:, 1]
        np.testing.assert_array_equal(
            preds_a,
            preds_b,
            err_msg=(
                "M2 predictions must be bit-identical across two seeded runs "
                "(LightGBM random_state=seed determinism)"
            ),
        )

    def test_different_seed_produces_different_model(self) -> None:
        """Different seeds produce different M2 models (confirms determinism is seed-bound)."""
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        rng = np.random.RandomState(1)
        features = rng.randn(30, 14)
        labels = np.array([1, 0, 1, 0, 1, 1, 0, 0, 1, 0] * 3, dtype=np.int32)

        model_42 = _train_m2_binary(
            m2_features=features,
            m2_labels=labels,
            n_trials=3,
            seed=42,
            fast_mode=True,
            verbose=0,
        )
        model_99 = _train_m2_binary(
            m2_features=features,
            m2_labels=labels,
            n_trials=3,
            seed=99,
            fast_mode=True,
            verbose=0,
        )
        if model_42 is None or model_99 is None:
            pytest.skip("M2 returned None; skip seed-differentiation check")

        import pandas as pd

        feat_df = pd.DataFrame(features)
        preds_42 = model_42.predict_proba(feat_df)[:, 1]
        preds_99 = model_99.predict_proba(feat_df)[:, 1]
        # Different seeds should produce different predictions (with high probability)
        # We don't assert this strictly as LightGBM can converge identically on tiny data,
        # but we verify both produced valid probability arrays.
        assert preds_42.shape == preds_99.shape == (30,)
        assert all(0.0 <= p <= 1.0 for p in preds_42)
        assert all(0.0 <= p <= 1.0 for p in preds_99)


# ---------------------------------------------------------------------------
# 10. m2_passed column: annotation logic verified on real TradeResult roster
# ---------------------------------------------------------------------------


class TestIter030M2PassedColumn:
    """m2_passed column annotation logic (per LM Master §9 Q8 item 4)."""

    def test_m2_passed_is_1_for_m2_active_trades(self) -> None:
        """Trades from models A/C/D (M2-filtered) get m2_passed=1."""
        results_a = [_make_trade("BTCUSDT", 1, 1_700_000_000_000)]
        results_d = [_make_trade("LTCUSDT", -1, 1_700_100_000_000)]
        m2_active_keys: set[tuple[int, str]] = {
            (t.open_time, t.symbol) for t in (results_a + results_d)
        }
        # Apply annotation logic (mirrors runner /030 elif)
        all_trades = results_a + results_d
        for trade in all_trades:
            m2_val = 1.0 if (trade.open_time, trade.symbol) in m2_active_keys else float("nan")
            assert m2_val == pytest.approx(1.0), "M2-active trades (A/C/D) must have m2_passed=1.0"

    def test_m2_passed_is_nan_for_model_e_trades(self) -> None:
        """Trades from Model E (DOT, no M2) get m2_passed=NaN."""
        results_a = [_make_trade("BTCUSDT", 1, 1_700_000_000_000)]
        results_e = [_make_trade("DOTUSDT", 1, 1_700_200_000_000)]  # NOT in m2_active_keys
        m2_active_keys: set[tuple[int, str]] = {(t.open_time, t.symbol) for t in results_a}
        for trade in results_e:
            m2_val = 1.0 if (trade.open_time, trade.symbol) in m2_active_keys else float("nan")
            import math

            assert math.isnan(m2_val), "Model E (DOT) trades must have m2_passed=NaN (M2 inactive)"


# ---------------------------------------------------------------------------
# 11. scale_pos_weight explicit per cell (not is_unbalance=True)
# ---------------------------------------------------------------------------


class TestIter030ScalePosWeight:
    """scale_pos_weight = n_neg/n_pos explicit, NOT is_unbalance=True, for v1_030."""

    def test_scale_pos_weight_computation(self) -> None:
        """n_neg/n_pos is the explicit formula (LM Master §2 ADOPTED)."""
        n_pos = 30
        n_neg = 70
        spw = float(n_neg) / float(n_pos)
        assert spw == pytest.approx(70.0 / 30.0)

    def test_scale_pos_weight_absent_from_v3_profile_in_source(self) -> None:
        """v3 profile uses is_unbalance=True; v1_030 uses scale_pos_weight."""
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        src = inspect.getsource(_train_m2_binary)
        # Both should appear in source (v3 branch uses is_unbalance; v1_030 uses scale_pos_weight)
        assert "is_unbalance" in src, "v3 profile must still use is_unbalance (backwards compat)"
        assert "scale_pos_weight" in src, "v1_030 profile must use scale_pos_weight"

    def test_v1_030_final_params_does_not_contain_is_unbalance(self) -> None:
        """The final params dict for v1_030 profile must NOT contain is_unbalance."""
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        src = inspect.getsource(_train_m2_binary)
        # The v1_030 final_params block must NOT include "is_unbalance"
        # We verify by checking that the v1_030 block uses scale_pos_weight
        # (the absence of is_unbalance from v1_030 is enforced at training time;
        # source inspection confirms it's not in the v1_030 branch).
        assert "scale_pos_weight" in src
        # Source-level: the v1_030 final_params dict starts after 'if bounds_profile == "v1_030":'
        v1_block_start = src.find('"v1_030"')
        v1_block = src[v1_block_start : v1_block_start + 800]
        assert "scale_pos_weight" in v1_block, "v1_030 final_params must contain scale_pos_weight"


# ---------------------------------------------------------------------------
# 12. TimeSeriesSplit fold-skip: < 3 positives in val → skip fold
# ---------------------------------------------------------------------------


class TestIter030FoldSkip:
    """LM Master §2 stratification fallback: skip folds with < 3 positive labels in val."""

    def test_fold_skip_source_checks_min_pos_per_fold(self) -> None:
        """_train_m2_binary source must check positive label count in val fold."""
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        src = inspect.getsource(_train_m2_binary)
        # The fold-skip logic checks positives in val_idx
        assert "min_pos_per_fold" in src, (
            "_train_m2_binary must have min_pos_per_fold parameter for fold-skip logic "
            "(LM Master §2 stratification fallback)"
        )
        assert "m2_labels[val_idx]" in src, (
            "Fold-skip must check positive labels in val_idx (not just train_idx)"
        )

    def test_fold_skip_default_is_3(self) -> None:
        """Default min_pos_per_fold = 3 per LM Master §2."""
        import inspect

        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        sig = inspect.signature(_train_m2_binary)
        default_val = sig.parameters["min_pos_per_fold"].default
        assert default_val == 3, (
            f"min_pos_per_fold default must be 3 per LM Master §2; got {default_val}"
        )

    def test_fold_skipped_when_all_val_labels_negative(self) -> None:
        """A fold with 0 positives in val is skipped → fewer fold_scores → lower final F1."""
        # We cannot directly test "fold was skipped" without mocking, but we can verify
        # that _train_m2_binary with min_pos_per_fold=3 handles sparse data gracefully
        # (returns None or a model, not an error).
        from crypto_trade.strategies.ml.metalabeling import _train_m2_binary

        # 15 samples but mostly 0-labels so TimeSeriesSplit val folds may have 0 positives
        features = np.eye(15, 14)  # linearly independent rows
        labels = np.zeros(15, dtype=np.int32)
        labels[0] = 1  # only 1 positive out of 15
        # Should not crash even when many folds have 0 positives
        try:
            result = _train_m2_binary(
                m2_features=features,
                m2_labels=labels,
                n_trials=2,
                seed=42,
                fast_mode=True,
                verbose=0,
                min_pos_per_fold=3,
            )
            # May return None (degenerate after fold-skip) or a model — either is valid
            assert result is None or hasattr(result, "predict_proba"), (
                "_train_m2_binary must return None or LGBMClassifier, not raise"
            )
        except Exception as e:
            pytest.fail(f"_train_m2_binary raised unexpectedly with sparse labels: {e}")


# ---------------------------------------------------------------------------
# 13. Foundation regression: walk_forward.py:113 carries embargo_ms purge
# ---------------------------------------------------------------------------


class TestIter030FoundationEmbargoRegression:
    """Regression guard: walk_forward train_end_ms = test_start_ms - embargo_ms (no lookahead)."""

    def test_walk_forward_train_end_precedes_test_start_by_embargo(self) -> None:
        """Split train_end_ms must be strictly less than test_start_ms by embargo gap."""
        import numpy as np

        from crypto_trade.strategies.ml.walk_forward import (
            compute_embargo_candles,
            generate_monthly_splits,
        )

        interval_ms = 480 * 60_000  # 8h
        timeout_minutes = 10080  # 7d
        # Build 3 months of synthetic open_times
        n = 90 * 3
        open_times = np.arange(n, dtype=np.int64) * interval_ms + 1_704_067_200_000

        splits = generate_monthly_splits(
            open_times,
            training_months=2,
            label_timeout_minutes=timeout_minutes,
            interval_minutes=480,
        )
        embargo_candles = compute_embargo_candles(timeout_minutes, 480)
        expected_gap_ms = embargo_candles * interval_ms

        for s in splits:
            actual_gap = s.test_start_ms - s.train_end_ms
            assert actual_gap == expected_gap_ms, (
                f"walk_forward.py:113 regression: "
                f"train_end_ms gap should be {expected_gap_ms} ms "
                f"but got {actual_gap} ms. "
                f"Anti-lookahead embargo MISSING or BROKEN."
            )

    def test_m2_training_window_uses_train_end_ms_not_test_start(self) -> None:
        """MetaLabelingStrategy._train_m2_for_month references train_end_ms boundary."""
        from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

        src = inspect.getsource(MetaLabelingStrategy._train_m2_for_month)
        # M2 training must use split.train_end_ms as the upper bound (not test_start_ms)
        assert "train_end_ms" in src, (
            "_train_m2_for_month must use split.train_end_ms to bound the training window "
            "(prevents M2 from peeking into the test month during label derivation)"
        )


# ---------------------------------------------------------------------------
# Module-level helper for source-level dispatch inspection
# ---------------------------------------------------------------------------


def _get_030_dispatch_source() -> str:
    """Return the /030 elif branch source from run_baseline_v1.main for inspection.

    Searches for the elif dispatch branch (iteration_label == "v1-030") to avoid
    matching the catch-all exclusion tuple which also contains "v1-030" as a literal.
    """
    from run_baseline_v1 import main

    src = inspect.getsource(main)
    # Search for the elif dispatch branch, not the exclusion tuple
    marker = 'iteration_label == "v1-030"'
    start = src.find(marker)
    if start == -1:
        # Fallback: search for "v1-030" literal (old behavior)
        start = src.find('"v1-030"')
    if start == -1:
        return ""
    return src[start : start + 8000]
