"""v1 feature module — refactored 2026-05-23 to mirror v2/v3 track isolation pattern.

This module is intentionally thin. The legacy ``crypto_trade.features`` package
holds the actual v1 feature implementations from the 186 historical iterations
(calendar, cross_asset, entropy_cusum, interaction, mean_reversion, momentum,
statistical, trend, volatility, volume). ``features_v1`` re-exports the
canonical feature-column list and defines v1-track constants without duplicating
the feature math.

Track isolation:
----------------
v1 (refactored) MUST NOT import from ``crypto_trade.features_v2`` or
``crypto_trade.features_v3``. The enforcement greps run at Phase 6.0 pre-flight:

    grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v1/
    grep -r "from crypto_trade.features_v3" src/crypto_trade/features_v1/

Both must return empty. Violating this rule is a hard BLOCK.

Note: ``features_v1`` IS allowed to import from the legacy ``crypto_trade.features``
parent package since the latter holds the actual v1 feature math. The legacy
package is preserved (not removed) for backward compatibility with the 186
historical iterations.
"""

from __future__ import annotations

from crypto_trade.live.models import BASELINE_FEATURE_COLUMNS, OOD_FEATURE_COLUMNS

# ---------------------------------------------------------------------------
# v1 symbol universe
# ---------------------------------------------------------------------------

# Symbols NOT allowed in v1 (refactored). These are reserved by v2 (live),
# v3 (live), or kept reserved for historical reasons (BNB).
V1_EXCLUDED_SYMBOLS: tuple[str, ...] = (
    # v2 traded (live, separate track)
    # iter-v1/017: SOLUSDT removed from exclusion list to enable universe-expansion
    # EXPLORATION (Model F). Dispatch instructions override brief Section 10.1
    # "V1_EXCLUDED_SYMBOLS unchanged" because assert_v1_universe() would otherwise
    # hard-BLOCK SOLUSDT from being passed to the runner. QR Phase 8 determines
    # whether SOLUSDT remains in v1 universe post-/017 outcome.
    "XRPUSDT",
    "DOGEUSDT",
    "NEARUSDT",
    # v3 traded (live, separate track)
    "BCHUSDT",
    "LDOUSDT",
    "TRXUSDT",
    # historical reservation (never traded, kept reserved)
    "BNBUSDT",
)

# Initial baseline universe (corrected walk-forward stats anchored to these 5
# symbols). Future v1 iterations can EXPLORE adding/swapping symbols from the
# extended pool = all Binance perpetuals minus V1_EXCLUDED_SYMBOLS.
# CONFIRMATION-MERGE updates this constant if the bundle changes universe.
V1_BASELINE_UNIVERSE: tuple[str, ...] = (
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
)

# ---------------------------------------------------------------------------
# v1 feature column list
# ---------------------------------------------------------------------------

# The canonical v1 feature set is the 193-column BASELINE_FEATURE_COLUMNS list
# defined in ``crypto_trade.live.models``. Re-exported here as V1_FEATURE_COLUMNS
# to match the v2/v3 naming convention. The runner uses this list to pin the
# explicit feature_columns argument to LightGbmStrategy at training time
# (NEVER pass None — column ordering matters for LightGBM colsample_bytree).
V1_FEATURE_COLUMNS: tuple[str, ...] = tuple(BASELINE_FEATURE_COLUMNS)

# iter-v1/002: IC-pruned feature set (193 → 40 features).
# Produced by analysis/iteration_v1-002/ic_pruning_audit.py (committed e71ef74).
# Applied LM Master Phase 4.5 swap: drop mom_mom_5, add stat_kurtosis_20.
# Selection criteria:
#   - Eliminates all 3 cross-family IC > 0.70 pairs (MR↔momentum +0.85,
#     trend↔volatility +0.82, trend↔volume -0.72).
#   - Drops all 13 raw-α ADF-failing features (trend EMAs/SMAs + cumulative
#     volume primitives).
#   - Within-family sister-window deduplication to one representative per
#     sub-family kernel.
# Properties: 40/40 pass ADF raw-α=0.05 stationarity; alphabetically sorted.
# DO NOT MODIFY V1_FEATURE_COLUMNS — this is an ADDITIONAL constant.
V1_FEATURE_COLUMNS_PRUNED: tuple[str, ...] = (
    "cal_dow_norm",
    "cal_hour_norm",
    "funding_rate_zscore_30",  # iter-v1/023: NEW — funding-rate z-score 30-bar (10-day)
    "funding_rate_zscore_90",  # iter-v1/023: NEW — funding-rate z-score 90-bar (30-day)
    "interact_natr_x_adx",
    "interact_ret1_x_natr",
    "interact_ret1_x_ret3",
    "interact_rsi_x_adx",
    "interact_rsi_x_natr",
    "interact_stoch_x_adx",
    "mom_macd_hist_12_26_9",
    "mom_macd_line_12_26_9",
    "mom_roc_10",
    "mom_rsi_14",
    "mom_stoch_d_14",
    "mom_stoch_k_14",
    "mom_willr_14",
    "mr_pct_from_high_20",
    "mr_pct_from_low_20",
    "mr_rsi_extreme_14",
    "oi_delta_30_z90",  # iter-v1/025: NEW — open-interest delta z-score (90-bar window)
    "stat_autocorr_lag5",
    "stat_kurtosis_20",  # LM Master Phase 4.5 swap: drop mom_mom_5, add stat_kurtosis_20
    "stat_log_return_1",
    "stat_return_5",
    "stat_skew_20",
    "trend_adx_14",
    "trend_aroon_osc_14",
    "trend_aroon_osc_50",
    "trend_ema_cross_5_12",
    "trend_minus_di_14",
    "trend_plus_di_14",
    "trend_supertrend_14_3",
    "vol_atr_14",
    "vol_bb_bandwidth_20",
    "vol_cmf_14",
    "vol_mfi_14",
    "vol_natr_14",
    "vol_range_spike_24",
    "vol_range_spike_72",
    "vol_taker_buy_ratio",
    "vol_volume_pctchg_5",
    "vol_volume_rel_20",
)

# Sanity guard: confirm the pruned set has exactly 43 features.
# iter-v1/023: extended 40 → 42 by adding funding_rate_zscore_30 + funding_rate_zscore_90.
# iter-v1/025: extended 42 → 43 by adding oi_delta_30_z90 (open-interest delta z-score).
assert len(V1_FEATURE_COLUMNS_PRUNED) == 43, (
    f"V1_FEATURE_COLUMNS_PRUNED must have exactly 43 features; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
)

# Out-of-distribution detection feature subset (16 scale-invariant features
# used by the R3 Mahalanobis gate). Re-exported for v1 runner.
# CRITICAL: V1_OOD_FEATURE_COLUMNS is DECOUPLED from V1_FEATURE_COLUMNS_PRUNED.
# Only 3 of 16 OOD features overlap with the pruned set; the other 13 are loaded
# from the full parquet column set (lgbm.py:576 reads from train_feat_df.columns
# which is the full parquet, NOT the 40-pruned feature_columns subset).
# DO NOT substitute V1_FEATURE_COLUMNS_PRUNED as ood_features in the runner.
V1_OOD_FEATURE_COLUMNS: tuple[str, ...] = tuple(OOD_FEATURE_COLUMNS)

# ---------------------------------------------------------------------------
# Runtime audit helper
# ---------------------------------------------------------------------------


def assert_v1_universe(symbols: list[str] | tuple[str, ...]) -> None:
    """Raise AssertionError if any symbol is in V1_EXCLUDED_SYMBOLS.

    The v1 runner calls this at startup to fail loudly if a v2/v3 symbol leaks
    into v1's universe. Mirrors the v2/v3 audit pattern.
    """
    overlap = set(symbols) & set(V1_EXCLUDED_SYMBOLS)
    if overlap:
        raise AssertionError(
            f"v1 cannot trade v2/v3 symbols: {sorted(overlap)}. "
            f"V1_EXCLUDED_SYMBOLS = {V1_EXCLUDED_SYMBOLS}."
        )


V1_ITER028_UNIVERSE: tuple[str, ...] = ("LTCUSDT",)
"""iter-v1/028 cohort: LTC-only D-specialist with tighter atr_sl=1.0 (vs baseline 1.75).

Cycle-4 EXPLORATION #1 of 10. Axis family: per-cohort-specialization-LTC-v2 (NEW 15th family).
Mechanism: upstream ATR-based SL magnitude clip. atr_sl is upstream of triple-barrier label
generation — tightening 1.75→1.0 narrows the lower barrier by 43%, shifts class balance (MORE
-1 labels with SMALLER magnitudes), AND relocates the Optuna basin under retraining (TWO
basin-relocation vectors per LM Master Rec #2 ADOPTED). PARTIAL basin inoculation; NOT immune.

HIGH-RISK declaration: per-cohort isolation + labeling-parameter modification both change
Optuna's training-objective domain. Mitigation: ENSEMBLE_SIZE=10 (v1-runner-compatible; maps
variance budget to inner ensemble per feedback_v1_ensemble.md since v1 runner has no --seeds).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"LTCUSDT"} guard fires for this dispatch branch.
"""


V1_ITER029_UNIVERSE: tuple[str, ...] = ("DOTUSDT",)
"""iter-v1/029 cohort: DOT-only E-specialist + symmetric BTC-trend gate ±8% (mirror /019).

Cycle-4 EXPLORATION #2 of 10. Axis family: per-cohort-specialization-DOT-v2 (NEW 16th family).
Mechanism: post-hoc stateless direction-aware BTC-trend gate at ±8% on BTC 14d return (42 bars).
Gate semantics: kill LONG when BTC ret_42 < -8% (counter-trend long into dump); kill SHORT when
BTC ret_42 > +8% (counter-trend short into rally). Symmetric — mirrors /019 ETH spec exactly.

LM Master HYBRID class: FRAGILE-POSITIVE-WITH-LONG-COUNTER-TREND-DRAG. DOT OOS LONG weak-up-BTC
bucket (-8.47% / 7 tr / WR 28.6%) is the ETH /019 fingerprint. Path C recommended.

Model E semantics: R1=ON, R2=OFF, R3=ON, atr_tp=3.5, atr_sl=1.75 (UNCHANGED from baseline).
NORMAL-RISK declaration: post-Optuna gate does NOT change Optuna's training-objective domain.
ENSEMBLE_SIZE=10, n_trials=35, single-seed=42 (EXPLORATION budget; ~30-45 min wall-clock).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"DOTUSDT"} and iteration_label == "v1-029" guard fires for dispatch.
"""

__all__ = [
    "V1_EXCLUDED_SYMBOLS",
    "V1_BASELINE_UNIVERSE",
    "V1_FEATURE_COLUMNS",
    "V1_FEATURE_COLUMNS_PRUNED",
    "V1_OOD_FEATURE_COLUMNS",
    "assert_v1_universe",
    "V1_ITER028_UNIVERSE",
    "V1_ITER029_UNIVERSE",
    # iter-v1/023: funding-rate feature family (add_funding_v1_features imported on demand)
    # iter-v1/025: OI delta feature family (add_oi_delta_v1_features imported on demand)
]
