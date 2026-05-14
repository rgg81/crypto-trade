"""Assertion test for V3_FEATURE_COLUMNS_TOP_N count — iter-v3/064.

Verifies that V3_FEATURE_COLUMNS_TOP_N has exactly 15 entries after the
PHASED MASS-EXPANSION #1 at iter-v3/064 (REVERT to 14-feature anchor + ADD adx_14).

Background:
    iter-v3/063 attempted MASS FEATURE EXPANSION 14 → 46 at single-seed n_trials=35
    EXPLORATION mode and FAILED with SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (Critic
    FINAL `7cbc136`; diary `937f7d6`). IS Sharpe collapsed -1.38 from /060 anchor.

    iter-v3/064 per amended `feedback_v3_mass_feature_expansion.md` (2026-05-14):
    - REVERT to /060 14-feature anchor
    - ADD adx_14 as PHASED MASS-EXPANSION #1 single-feature axis
    - Result: 15 features total

    8 of 9 iter-v3/063 NEW features (candle_dow_sin/cos, ret_1d, sym_vs_btc_ret_3d,
    sym_vs_btc_vol_14d, taker_buy_imbalance_20, trend_efficiency_signed,
    vol_regime_x_momentum) are REVERTED (kept-implemented; ABSENT from feature list).
    They can be considered for phased-mass-expansion #2+ individually.

Tests:
1. Count is exactly 15.
2. All 14 BASELINE_V3 features present.
3. adx_14 present (PHASED MASS-EXPANSION #1 single feature).
4. 8 reverted /063 NEW features absent.
5. Prohibited features absent (vol_adj_autocorr, efficiency_ratio_50,
   regime_momentum_signed_3d, vwap_dev_50, hurst_drift_50_200, vol_normalized_ret_5d).
6. No duplicates in the feature list.
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

# iter-v3/064 PHASED MASS-EXPANSION #1: adx_14 is the single-feature addition.
_NEW_064_FEATURES = frozenset(["adx_14"])

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


def test_feature_count_15():
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 15 entries."""
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 15, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected 15. "
        "iter-v3/064 PHASED MASS-EXPANSION #1: REVERT to 14-feature anchor + ADD adx_14. "
        "Update V3_FEATURE_COLUMNS_TOP_N in src/crypto_trade/features_v3/__init__.py."
    )


def test_baseline_v3_features_present():
    """All 14 BASELINE_V3 features must be present."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    missing = _BASELINE_V3_FEATURES - feature_set
    assert not missing, (
        f"BASELINE_V3 features missing from V3_FEATURE_COLUMNS_TOP_N: {sorted(missing)}. "
        "All 14 BASELINE_V3 features must be preserved in the 15-feature phased-expansion set."
    )


def test_new_064_features_present():
    """adx_14 (PHASED MASS-EXPANSION #1 single feature) must be present."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    missing = _NEW_064_FEATURES - feature_set
    assert not missing, (
        f"iter-v3/064 NEW features missing from V3_FEATURE_COLUMNS_TOP_N: {sorted(missing)}. "
        "PHASED MASS-EXPANSION #1: adx_14 is the single-feature axis at /064."
    )


def test_reverted_063_new_features_absent():
    """8 of 9 iter-v3/063 NEW features must be ABSENT at /064 (REVERTED with mass-expansion)."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    found = _REVERTED_063_NEW_FEATURES & feature_set
    assert not found, (
        f"iter-v3/063 NEW features FOUND in V3_FEATURE_COLUMNS_TOP_N at /064: {sorted(found)}. "
        "These 8 features should be REVERTED (kept-implemented; ABSENT from feature list) at "
        "iter-v3/064 PHASED MASS-EXPANSION #1. Only adx_14 is retained. "
        "Per amended `feedback_v3_mass_feature_expansion.md` (2026-05-14)."
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
