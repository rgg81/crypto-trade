"""Assertion test for V3_FEATURE_COLUMNS_TOP_N count — iter-v3/077 (14 features).

Verifies that V3_FEATURE_COLUMNS_TOP_N has exactly 14 entries: the BASELINE_V3
/059/060 anchor stack. iter-v3/077 REVERTS /076's range_efficiency_50.

Background:
    iter-v3/063 attempted MASS FEATURE EXPANSION 14 → 46 at single-seed n_trials=35
    EXPLORATION mode and FAILED with SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (Critic
    FINAL `7cbc136`). iter-v3/064 PHASED MASS-EXPANSION #1 (added adx_14 only) ALSO
    NEGATIVE per Critic `452fcf2`. The 14-feature /060 anchor was carried /065-/075.

    iter-v3/076 (cycle-2 EXPLORATION #6) added range_efficiency_50 as a 15th
    feature; it was SUSPICIOUS-OOS-DOMINANT and NON-ADVANCING. The Kaufman
    path-efficiency axis is now CLOSED across 2 data points (/043 DISASTROUS +
    /076 SUSPICIOUS — BASELINE_V3.md Dead Ideas).

    iter-v3/077 (cycle-2 EXPLORATION #7) is a PASSIVE-DIAGNOSTIC iteration
    (conditional-orthogonality report instrumentation; research brief Section 3).
    It adds NO feature and REVERTS /076's range_efficiency_50 — the feature set
    returns to the 14-feature BASELINE_V3 /059/060 anchor.

    range_efficiency_50 uses the same Kaufman path-efficiency MATH as the BANNED
    efficiency_ratio_50; both must stay absent. The literal name
    efficiency_ratio_50 stays in the prohibited set.

Tests:
1. Count is exactly 14.
2. All 14 BASELINE_V3 features present.
3. range_efficiency_50 ABSENT (reverted at /077; Kaufman axis CLOSED).
4. adx_14 ABSENT (iter-v3/064 NEGATIVE; DROPPED at /065 revert).
5. All 9 /063 NEW features absent (reverted at /064 revert).
6. Prohibited features absent (vol_adj_autocorr, efficiency_ratio_50,
   regime_momentum_signed_3d, vwap_dev_50, hurst_drift_50_200, vol_normalized_ret_5d).
7. No duplicates in the feature list.
"""

from __future__ import annotations

from crypto_trade.features_v3 import V3_FEATURE_COLUMNS_TOP_N

# 14 BASELINE_V3 features — MUST be present
_BASELINE_V3_FEATURES = frozenset(
    [
        "max_dd_window_50",
        "ret_skew_200",
        "ret_skew_50",
        "ret_kurt_200",
        "ret_kurt_50",
        "range_realized_vol_50",
        "vwap_dev_20",
        "btc_ret_14d",
        "sym_vs_btc_ret_7d",
        "ret_autocorr_lag1_50",
        "ema_spread_atr_20",
        "hurst_100",
        "hurst_diff_100_50",
        "regime_momentum_signed_5d",
    ]
)

# iter-v3/064 PHASED MASS-EXPANSION #1 NEGATIVE: adx_14 DROPPED at /065 revert.
_REVERTED_064_FEATURES = frozenset(["adx_14"])

# 8 of 9 iter-v3/063 NEW features REVERTED at /064 (kept-implemented; ABSENT from feature list).
_REVERTED_063_NEW_FEATURES = frozenset(
    [
        "candle_dow_sin",
        "candle_dow_cos",
        "ret_1d",
        "sym_vs_btc_ret_3d",
        "sym_vs_btc_vol_14d",
        "taker_buy_imbalance_20",
        "trend_efficiency_signed",
        "vol_regime_x_momentum",
    ]
)

# Features that must NOT be in the list (catastrophic-dead / PARKED)
_PROHIBITED_FEATURES = frozenset(
    [
        "vol_adj_autocorr",  # catastrophic IS collapse at iter-v3/026
        "efficiency_ratio_50",  # DISASTROUS NEGATIVE at iter-v3/043 (unsigned ER)
        "regime_momentum_signed_3d",  # PARKED per iter-v3/053 PATH C-suspicious
        "vwap_dev_50",  # dropped per Critic FINAL SHA a544621
        "hurst_drift_50_200",  # PARKED per iter-v3/053 PATH D
        "vol_normalized_ret_5d",  # DROPPED per iter-v3/049 PATH C-clean
    ]
)


def test_feature_count_14():
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 14 entries at iter-v3/077."""
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 14, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected 14. "
        "iter-v3/077: the BASELINE_V3 /059/060 14-feature anchor stack "
        "(/076's range_efficiency_50 reverted; PASSIVE-DIAGNOSTIC iteration). "
        "Update V3_FEATURE_COLUMNS_TOP_N in src/crypto_trade/features_v3/__init__.py."
    )


def test_baseline_v3_features_present():
    """All 14 BASELINE_V3 features must be present."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    missing = _BASELINE_V3_FEATURES - feature_set
    assert not missing, (
        f"BASELINE_V3 features missing from V3_FEATURE_COLUMNS_TOP_N: {sorted(missing)}. "
        "All 14 BASELINE_V3 features must be preserved in the 15-feature /076 set."
    )


def test_range_efficiency_50_absent():
    """range_efficiency_50 MUST be ABSENT at iter-v3/077 (REVERTED — /076 SUSPICIOUS)."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    assert "range_efficiency_50" not in feature_set, (
        "range_efficiency_50 FOUND in V3_FEATURE_COLUMNS_TOP_N — must be ABSENT "
        "at iter-v3/077. /076 added it (15th feature) and was "
        "SUSPICIOUS-OOS-DOMINANT (NON-ADVANCING); the Kaufman path-efficiency "
        "axis is CLOSED across /043 + /076 (BASELINE_V3.md Dead Ideas). /077 is a "
        "PASSIVE-DIAGNOSTIC iteration on the 14-feature anchor. "
        "Remove 'range_efficiency_50' from V3_FEATURE_COLUMNS_TOP_N."
    )


def test_new_064_features_present():
    """adx_14 MUST BE ABSENT at iter-v3/065+ (iter-v3/064 NEGATIVE — DROPPED at /065 revert)."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    found = _REVERTED_064_FEATURES & feature_set
    assert not found, (
        f"iter-v3/064 REVERTED features FOUND in V3_FEATURE_COLUMNS_TOP_N: {sorted(found)}. "
        "iter-v3/064 PHASED MASS-EXPANSION #1 was NEGATIVE per Critic `452fcf2`; adx_14 DROPPED. "
        "Critic /064 Rec #4 mandates NON-FEATURE PIVOT for /065-/068 (zero new features). "
        "Remove from V3_FEATURE_COLUMNS_TOP_N in src/crypto_trade/features_v3/__init__.py."
    )


def test_reverted_063_new_features_absent():
    """All 9 iter-v3/063 NEW features must be ABSENT at /065+ (all reverted)."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    found = _REVERTED_063_NEW_FEATURES & feature_set
    assert not found, (
        f"iter-v3/063 NEW features FOUND in V3_FEATURE_COLUMNS_TOP_N at /065+: {sorted(found)}. "
        "These features should be REVERTED (kept-implemented; ABSENT from feature list) at "
        "iter-v3/065+ (post-/064 NEGATIVE; NON-FEATURE PIVOT per Critic /064 Rec #4). "
        "Per `feedback_v3_iter064_process_lessons.md` Rule 5."
    )


def test_prohibited_features_absent():
    """Prohibited features must not be in V3_FEATURE_COLUMNS_TOP_N."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    found = _PROHIBITED_FEATURES & feature_set
    assert not found, (
        f"Prohibited features found in V3_FEATURE_COLUMNS_TOP_N: {sorted(found)}. "
        "Remove these features: vol_adj_autocorr (catastrophic /026), "
        "efficiency_ratio_50 (DISASTROUS /043), "
        "regime_momentum_signed_3d (PARKED /053), "
        "vwap_dev_50 (dropped Critic), "
        "hurst_drift_50_200 (PARKED /053 PATH D), "
        "vol_normalized_ret_5d (DROPPED /049 PATH C-clean)."
    )


def test_no_duplicates():
    """V3_FEATURE_COLUMNS_TOP_N must have no duplicate entries."""
    feature_list = list(V3_FEATURE_COLUMNS_TOP_N)
    feature_set = set(feature_list)
    assert len(feature_list) == len(feature_set), (
        f"Duplicate features in V3_FEATURE_COLUMNS_TOP_N: "
        f"{[f for f in feature_list if feature_list.count(f) > 1]}"
    )
