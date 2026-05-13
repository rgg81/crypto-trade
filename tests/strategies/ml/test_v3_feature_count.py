"""Assertion test for V3_FEATURE_COLUMNS_TOP_N count — iter-v3/063.

Verifies that V3_FEATURE_COLUMNS_TOP_N has exactly 48 entries after the
MASS FEATURE EXPANSION at iter-v3/063 (EDA SHA c833f48; Path B).

Background:
    iter-v3/063 expands the feature set from 14 to 48:
    - 14 BASELINE_V3 features preserved
    - 34 promoted from parquet (already computed; zero compute cost)
    - 9 NEW feature implementations (adx_14, candle_dow_sin, candle_dow_cos,
      ret_1d, sym_vs_btc_ret_3d, sym_vs_btc_vol_14d, taker_buy_imbalance_20,
      trend_efficiency_signed, vol_regime_x_momentum)

    User-approved deviation from the "50 minimum" mandate: 48 is the maximum
    orthogonal set at IC<0.70 with all 14 BASELINE_V3 features preserved.
    Padding to 50 risks INERT-feature-at-higher-budget failure mode per
    feedback_v3_inert_features_at_higher_budget.md.

Tests:
1. Count is exactly 48.
2. All 14 BASELINE_V3 features present.
3. All 9 NEW features present.
4. Prohibited features absent (vol_adj_autocorr, efficiency_ratio_50,
   regime_momentum_signed_3d).
5. No duplicates in the feature list.
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

# 9 NEW features implemented at iter-v3/063 — MUST be present
_NEW_063_FEATURES = frozenset(
    [
        "adx_14",
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

# Features that must NOT be in the list
_PROHIBITED_FEATURES = frozenset(
    [
        "vol_adj_autocorr",  # catastrophic IS collapse at iter-v3/026
        "efficiency_ratio_50",  # DISASTROUS NEGATIVE at iter-v3/043 (unsigned ER)
        "regime_momentum_signed_3d",  # PARKED per iter-v3/053 PATH C-suspicious
        "vwap_dev_50",  # dropped per Critic FINAL SHA a544621
    ]
)


def test_feature_count_48():
    """V3_FEATURE_COLUMNS_TOP_N must have exactly 48 entries."""
    n = len(V3_FEATURE_COLUMNS_TOP_N)
    assert n == 48, (
        f"V3_FEATURE_COLUMNS_TOP_N has {n} features — expected 48. "
        "iter-v3/063 MASS FEATURE EXPANSION (Path B): 14 BASELINE_V3 + 34 promoted. "
        "Update V3_FEATURE_COLUMNS_TOP_N in src/crypto_trade/features_v3/__init__.py."
    )


def test_baseline_v3_features_present():
    """All 14 BASELINE_V3 features must be present."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    missing = _BASELINE_V3_FEATURES - feature_set
    assert not missing, (
        f"BASELINE_V3 features missing from V3_FEATURE_COLUMNS_TOP_N: {sorted(missing)}. "
        "All 14 BASELINE_V3 features must be preserved in the 48-feature expansion."
    )


def test_new_063_features_present():
    """All 9 NEW iter-v3/063 features must be present."""
    feature_set = set(V3_FEATURE_COLUMNS_TOP_N)
    missing = _NEW_063_FEATURES - feature_set
    assert not missing, (
        f"iter-v3/063 NEW features missing from V3_FEATURE_COLUMNS_TOP_N: {sorted(missing)}. "
        "All 9 NEW features must be implemented and listed."
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
        "vwap_dev_50 (dropped Critic /008)."
    )


def test_no_duplicates():
    """V3_FEATURE_COLUMNS_TOP_N must have no duplicate entries."""
    feature_list = list(V3_FEATURE_COLUMNS_TOP_N)
    feature_set = set(feature_list)
    assert len(feature_list) == len(feature_set), (
        f"Duplicate features in V3_FEATURE_COLUMNS_TOP_N: "
        f"{[f for f in feature_list if feature_list.count(f) > 1]}"
    )
