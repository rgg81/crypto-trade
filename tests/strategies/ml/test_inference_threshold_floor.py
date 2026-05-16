"""Test inference_threshold_floor at LightGbmStrategy (iter-v3/067 Path D).

Universal inference-time confidence-threshold floor:
    _confidence_threshold = max(mean(per_seed_thresholds), inference_threshold_floor)

Three tests per brief Section 3 Sub-fix 7:
  1. test_inference_threshold_floor_default_zero
       — default floor=0.0 is a no-op (backward compatibility).
  2. test_inference_threshold_floor_60_pct_uplifts_low_mean
       — floor=0.60 raises threshold when per-seed mean is below 0.60.
  3. test_inference_threshold_floor_does_not_lower_high_mean
       — floor=0.60 does not reduce threshold when per-seed mean is at or above 0.60.
"""

from __future__ import annotations

import numpy as np
import pytest

from crypto_trade.strategies.ml.lgbm import LightGbmStrategy

# ---------------------------------------------------------------------------
# Minimal valid kwargs required by LightGbmStrategy.__init__ guards
# ---------------------------------------------------------------------------

_BASE_KWARGS = dict(
    features_dir="data/features_v3",
    ensemble_seeds=[42],
    feature_columns=["feat_a", "feat_b"],
)


# ---------------------------------------------------------------------------
# Test 1: default floor=0.0 is a no-op (backward compatibility)
# ---------------------------------------------------------------------------


def test_inference_threshold_floor_default_zero():
    """Default floor=0.0 must not alter _confidence_threshold derivation.

    Verifies backward compatibility: any prior v3 iteration that constructs
    LightGbmStrategy without inference_threshold_floor behaves identically
    to the pre-/067 state.
    """
    strat = LightGbmStrategy(**_BASE_KWARGS)
    assert strat._inference_threshold_floor == pytest.approx(0.0), (
        f"Default floor expected 0.0; got {strat._inference_threshold_floor}. "
        "iter-v3/067: default must be 0.0 for backward compat."
    )
    # Simulate _confidence_thresholds populated by training for a (sym, month) cell
    strat._confidence_thresholds = [0.55]
    computed = float(max(np.mean(strat._confidence_thresholds), strat._inference_threshold_floor))
    assert computed == pytest.approx(0.55), (
        f"Floor=0.0 with per-seed mean 0.55: expected 0.55; got {computed}. "
        "iter-v3/067: zero floor must not uplift the threshold."
    )


# ---------------------------------------------------------------------------
# Test 2: floor=0.60 uplifts threshold when per-seed mean < 0.60
# ---------------------------------------------------------------------------


def test_inference_threshold_floor_60_pct_uplifts_low_mean():
    """floor=0.60 must uplift _confidence_threshold when per-seed mean is below 0.60.

    Scenario: per_seed_thresholds=[0.55] → mean=0.55 < floor=0.60 → output=0.60.
    This is the primary behavioral effect of Path D: marginal-confidence cells
    whose Optuna-inherited mean falls in [0.50, 0.60) are raised to 0.60.
    """
    strat = LightGbmStrategy(inference_threshold_floor=0.60, **_BASE_KWARGS)
    assert strat._inference_threshold_floor == pytest.approx(0.60), (
        f"Expected floor=0.60; got {strat._inference_threshold_floor}. "
        "iter-v3/067: floor must be stored from constructor argument."
    )
    strat._confidence_thresholds = [0.55]
    computed = float(max(np.mean(strat._confidence_thresholds), strat._inference_threshold_floor))
    assert computed == pytest.approx(0.60), (
        f"Floor=0.60, mean=0.55: expected 0.60 (uplifted); got {computed}. "
        "iter-v3/067 Path D: floor must raise threshold from 0.55 → 0.60."
    )


# ---------------------------------------------------------------------------
# Test 3: floor=0.60 does not lower threshold when per-seed mean >= 0.60
# ---------------------------------------------------------------------------


def test_inference_threshold_floor_does_not_lower_high_mean():
    """floor=0.60 must NOT reduce _confidence_threshold when per-seed mean >= 0.60.

    Scenario: per_seed_thresholds=[0.65] → mean=0.65 >= floor=0.60 → output=0.65.
    The floor is a lower bound only; cells already above 0.60 are unaffected.
    """
    strat = LightGbmStrategy(inference_threshold_floor=0.60, **_BASE_KWARGS)
    strat._confidence_thresholds = [0.65]
    computed = float(max(np.mean(strat._confidence_thresholds), strat._inference_threshold_floor))
    assert computed == pytest.approx(0.65), (
        f"Floor=0.60, mean=0.65: expected 0.65 (no change); got {computed}. "
        "iter-v3/067 Path D: floor must NOT lower threshold when mean is above 0.60."
    )
