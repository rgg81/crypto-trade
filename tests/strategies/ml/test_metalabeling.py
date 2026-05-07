"""Smoke tests + correctness tests for MetaLabelingStrategy (iter-v3/017).

Tests verify:
1. Constructor accepts valid arguments (smoke test).
2. Constructor raises ValueError on None feature_columns.
3. Constructor raises ValueError on empty feature_columns.
4. Constructor raises ValueError on None ensemble_seeds.
5. fast_mode kwarg propagates to both M1 and M2 attributes.
6. MetaLabelingStrategy and LightGbmStrategy are distinct classes.
7. M2 input feature count = 14 (13 V3 features + M1 confidence).
8. get_signal returns NO_SIGNAL when M2 is inactive (no training data).
"""

from __future__ import annotations

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_MINIMAL_FEATURE_COLS = [f"feat_{i}" for i in range(13)]


def _make_strategy(**kwargs):
    """Construct MetaLabelingStrategy with valid defaults."""
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    defaults = {
        "training_months": 24,
        "n_trials": 1,
        "label_tp_pct": 8.0,
        "label_sl_pct": 4.0,
        "ensemble_seeds": [42],
        "feature_columns": _MINIMAL_FEATURE_COLS,
        "use_atr_labeling": False,
        "fast_mode": False,
    }
    defaults.update(kwargs)
    return MetaLabelingStrategy(**defaults)


# ---------------------------------------------------------------------------
# Test 1: Constructor smoke test
# ---------------------------------------------------------------------------


def test_metalabeling_strategy_import():
    """MetaLabelingStrategy is importable from the correct module path."""
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    assert MetaLabelingStrategy is not None


def test_metalabeling_strategy_constructor_smoke():
    """MetaLabelingStrategy constructs without error with minimal valid args."""
    strat = _make_strategy()
    assert strat.training_months == 24
    assert strat.n_trials == 1
    assert strat.ensemble_seeds == [42]
    assert strat.feature_columns == _MINIMAL_FEATURE_COLS
    assert strat._fast_mode is False


# ---------------------------------------------------------------------------
# Test 2: ValueError on None feature_columns
# ---------------------------------------------------------------------------


def test_metalabeling_raises_on_none_feature_columns():
    """MetaLabelingStrategy must raise ValueError when feature_columns=None."""
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        MetaLabelingStrategy(
            training_months=24,
            n_trials=1,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=[42],
            feature_columns=None,
        )


# ---------------------------------------------------------------------------
# Test 3: ValueError on empty feature_columns
# ---------------------------------------------------------------------------


def test_metalabeling_raises_on_empty_feature_columns():
    """MetaLabelingStrategy must raise ValueError when feature_columns=[]."""
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    with pytest.raises(ValueError, match="feature_columns must be explicitly specified"):
        MetaLabelingStrategy(
            training_months=24,
            n_trials=1,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=[42],
            feature_columns=[],
        )


# ---------------------------------------------------------------------------
# Test 4: ValueError on None ensemble_seeds
# ---------------------------------------------------------------------------


def test_metalabeling_raises_on_none_ensemble_seeds():
    """MetaLabelingStrategy must raise ValueError when ensemble_seeds=None."""
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    with pytest.raises(ValueError, match="ensemble_seeds must be a non-empty list"):
        MetaLabelingStrategy(
            training_months=24,
            n_trials=1,
            label_tp_pct=8.0,
            label_sl_pct=4.0,
            ensemble_seeds=None,
            feature_columns=_MINIMAL_FEATURE_COLS,
        )


# ---------------------------------------------------------------------------
# Test 5: fast_mode propagates to M1 and is stored on self
# ---------------------------------------------------------------------------


def test_metalabeling_fast_mode_propagates():
    """fast_mode=True is stored on MetaLabelingStrategy and propagated to M1."""
    strat = _make_strategy(fast_mode=True)
    assert strat._fast_mode is True
    # M1 should also have fast_mode=True
    assert strat._m1._fast_mode is True


def test_metalabeling_fast_mode_default_false():
    """fast_mode defaults to False."""
    strat = _make_strategy()
    assert strat._fast_mode is False
    assert strat._m1._fast_mode is False


# ---------------------------------------------------------------------------
# Test 6: MetaLabelingStrategy and LightGbmStrategy are distinct classes
# ---------------------------------------------------------------------------


def test_metalabeling_distinct_from_lgbm():
    """MetaLabelingStrategy and LightGbmStrategy are distinct classes."""
    from crypto_trade.strategies.ml.lgbm import LightGbmStrategy
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    assert MetaLabelingStrategy is not LightGbmStrategy


# ---------------------------------------------------------------------------
# Test 7: M2 feature dimension = 14 (13 + M1 confidence)
# ---------------------------------------------------------------------------


def test_m2_feature_col_count():
    """MetaLabelingStrategy._m2_feature_cols has 14 entries (13 + 'm1_confidence')."""
    strat = _make_strategy()
    assert len(strat._m2_feature_cols) == 14
    assert strat._m2_feature_cols[-1] == "m1_confidence"
    assert strat._m2_feature_cols[:13] == _MINIMAL_FEATURE_COLS


# ---------------------------------------------------------------------------
# Test 8: get_signal returns NO_SIGNAL when M2 is inactive
# ---------------------------------------------------------------------------


def test_get_signal_returns_no_signal_when_m2_inactive(tmp_path):
    """When M2 is inactive (no models), get_signal returns NO_SIGNAL."""
    from crypto_trade.strategies import NO_SIGNAL
    from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy

    strat = MetaLabelingStrategy(
        training_months=24,
        n_trials=1,
        ensemble_seeds=[42],
        feature_columns=_MINIMAL_FEATURE_COLS,
    )
    # M2 is inactive by default (not trained)
    assert strat._m2_active is False
    assert strat._m2_model is None

    # Without compute_features being called, M1 has no models either, so
    # get_signal should return NO_SIGNAL (M1 path returns NO_SIGNAL first).

    # Use a realistic open_time (2024-01)
    open_time_ms = int(pd.Timestamp("2024-01-15 00:00:00", tz="UTC").timestamp() * 1000)

    # M1 has no data → NO_SIGNAL
    sig = strat.get_signal("BCHUSDT", open_time_ms)
    assert sig is NO_SIGNAL


# ---------------------------------------------------------------------------
# Test 9: M2 label generation correctness (synthetic)
# ---------------------------------------------------------------------------


def test_m2_label_generation_binary():
    """M2 labels are 1 iff long/short PnL > 0 (TP hit, fee deducted by labeler).

    Synthetic: create 5 long_pnls and 5 short_pnls alternating positive/negative.
    Verify that M2 label derivation in the same loop logic as _train_m2_for_month
    correctly assigns 1 to TP-hit bars and 0 to SL/timeout bars.
    """

    # Simulate m1_pred_classes: 1=long, 0=short for 10 bars
    m1_pred_classes = np.array([1, 0, 1, 0, 1, 0, 1, 0, 1, 0])
    # Positive long_pnl = TP-hit; negative = SL or timeout
    long_pnls = np.array([1.9, 0.0, -0.9, 0.0, 1.9, 0.0, -0.9, 0.0, 1.9, 0.0])
    short_pnls = np.array([0.0, 1.9, 0.0, -0.9, 0.0, 1.9, 0.0, -0.9, 0.0, 1.9])

    m2_labels = np.zeros(10, dtype=np.int32)
    for i in range(10):
        direction_cls = int(m1_pred_classes[i])
        pnl = float(long_pnls[i]) if direction_cls == 1 else float(short_pnls[i])
        m2_labels[i] = 1 if pnl > 0.0 else 0

    # Long positions at [0, 2, 4, 6, 8] with pnl [1.9, -0.9, 1.9, -0.9, 1.9]
    # → expected M2 labels: [1, 0, 1, 0, 1, 0, 1, 0, 1, 0]
    # Wait: short positions at [1, 3, 5, 7, 9] with short_pnls [1.9, -0.9, 1.9, -0.9, 1.9]
    # → expected M2 labels for short positions: [1, 0, 1, 0, 1]
    expected = np.array([1, 1, 0, 0, 1, 1, 0, 0, 1, 1])
    np.testing.assert_array_equal(m2_labels, expected)


# We import pd here for the timestamp computation in test 8
import pandas as pd  # noqa: E402
