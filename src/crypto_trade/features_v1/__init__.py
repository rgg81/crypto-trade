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
    "dot_vs_btc_ret_ratio_30",  # iter-v1/050: NEW — DOT idiosyncratic return vs BTC 30d z-scored (DOT-only; NaN for other syms)  # noqa: E501
    "funding_rate_zscore_30",  # iter-v1/023: NEW — funding-rate z-score 30-bar (10-day)
    "funding_rate_zscore_90",  # iter-v1/023: NEW — funding-rate z-score 90-bar (30-day)
    "interact_natr_x_adx",
    "interact_ret1_x_natr",
    "interact_ret1_x_ret3",
    "interact_rsi_x_adx",
    "interact_rsi_x_natr",
    "interact_stoch_x_adx",
    "long_short_zscore_30",  # iter-v1/049: NEW — top-trader long/short ratio z-score (30-bar)
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
    "regime_momentum_signed_5d",  # iter-v1/040: composed momentum; replaces basis_zscore_30
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

# Sanity guard: confirm the pruned set has exactly 46 features.
# iter-v1/023: extended 40 → 42 by adding funding_rate_zscore_30 + funding_rate_zscore_90.
# iter-v1/025: extended 42 → 43 by adding oi_delta_30_z90 (open-interest delta z-score).
# iter-v1/034: extended 43 → 44 by adding basis_zscore_30 (perp-spot basis z-score).
# iter-v1/040: SWAP basis_zscore_30 (3-consec INERT DROP) → regime_momentum_signed_5d (ADD).
#              Count stays at 44 (DROP 1 + ADD 1).
# iter-v1/047: NEG-CLEAN-PRE-EDA — pre-launch F5 IC orthogonality gate FAILED
#              (|IC|=0.8132 vs stat_skew_20; ABORT threshold 0.60). skew_zscore_21
#              REVERTED. Count restored 45 → 44. statistical_v1 group de-registered
#              from GROUP_REGISTRY but the module file kept for future-iter reuse.
# iter-v1/048: NEG-CLEAN-PRE-EDA — pre-launch F5 IC orthogonality gate FAILED
#              (|IC|=0.9063 vs vol_volume_rel_20; ABORT threshold 0.60). The
#              "UNUSED-primitive" defense REFUTED: number_of_trades is empirically
#              tied to the volume cluster (rank-1 vol_volume_rel_20 0.9063, rank-2
#              vol_range_spike_24 0.7908, rank-3 vol_range_spike_72 0.7322).
#              trade_count_zscore_30 REVERTED. Count restored 45 → 44.
#              microstructure_v1 group de-registered from GROUP_REGISTRY but the
#              module file kept for future-iter reuse.
# iter-v1/049: extended 44 → 45 by adding long_short_zscore_30 (top-trader long/short
#              account ratio z-score, 30-bar window; non-kline data class from OI cache).
# iter-v1/050: extended 45 → 46 by adding dot_vs_btc_ret_ratio_30 (DOT idiosyncratic
#              return vs BTC 30d, z-scored 90-bar; DOT-only cross-asset signal; NaN for
#              other symbols; loaded from data/BTCUSDT/8h.csv at feature-gen time).
assert len(V1_FEATURE_COLUMNS_PRUNED) == 46, (
    f"V1_FEATURE_COLUMNS_PRUNED must have exactly 46 features; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
)

# Columns explicitly NOT in V1_FEATURE_COLUMNS_PRUNED but which may still appear in
# legacy parquet files (from older iterations that included them). The runner must
# NOT pick these up as training features.
# iter-v1/040: basis_zscore_30 DROPPED from V1_FEATURE_COLUMNS_PRUNED (3-consec INERT per
#              /034, /037, /038 importance audits; mean rank 27.67/44). Added here so any
#              residual basis_zscore_30 column in legacy parquets is explicitly NOT treated
#              as a training feature by the runner.
V1_RETIRED_FEATURE_COLUMNS: tuple[str, ...] = (
    "basis_zscore_30",  # iter-v1/040: retired (3-consec INERT; replaced by regime_momentum_signed_5d)  # noqa: E501
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

V1_ITER036_UNIVERSE: tuple[str, ...] = ("LINKUSDT", "DOTUSDT")
"""iter-v1/036 cohort: LINK + DOT 2-specialist bundle with trend-scanning labels.

Cycle-5 EXPLORATION #3 of 10. Axis family: per-cohort-specialization (REPEAT-JUSTIFIED;
directly isolates /035's bimodal finding: LINK +74.68pp / DOT +111.67pp OOS at
trend-scanning in 5-cohort dispatch).

Architecture: Model C' (LINK only, R1+R3 ON, atr_tp=3.5, atr_sl=1.75) +
Model E (DOT only, R1+R2+R3 ON, atr_tp=3.5, atr_sl=1.75). BOTH use trend-scanning
labels. Model A pool, Model D LTC, Model G ETH SKIPPED.

HIGH-RISK declaration: 2-mechanism stack — (1) per-cohort isolation (universe
substitution 5→2 cohort, removing large-cap Optuna averaging) + (2) trend-scanning
labels (already HIGH-RISK at /035; training-objective domain change). Single-seed
OPT-OUT per cycle-5 EXPLORATION standard. ENSEMBLE_SIZE=3, n_trials=18, seed=42.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"LINKUSDT", "DOTUSDT"} guard fires in dispatch branch.
assert label_mode_arg == "trend_scanning" guard fires in dispatch branch.
"""

V1_ITER039_UNIVERSE: tuple[str, ...] = ("LINKUSDT", "DOTUSDT")
"""iter-v1/039 cohort: LINK + DOT 2-specialist bundle with trend-scanning labels +
Sortino Optuna objective (DOUBLE-REPEAT COMBO: loss-function × per-cohort-specialization).

Cycle-5 EXPLORATION #6 of 10. Axis family: loss-function × per-cohort-specialization
(stacking-interaction-probe of /036 per-cohort-specialization + /037 loss-function).
Load-bearing /044 CONFIRMATION routing decision: resolves whether Sortino and per-cohort
trend-scanning COMPOUND on the same substrate or COMPETE (basin collision).

Architecture: Model C' (LINK only, R1+R3 ON, atr_tp=3.5, atr_sl=1.75) +
Model E (DOT only, R1+R2+R3 ON, atr_tp=3.5, atr_sl=1.75). BOTH use trend-scanning
labels AND Sortino Optuna objective. Model A pool, Model D LTC SKIPPED.

HIGH-RISK declaration: rotation-rule HIGH-RISK (double-REPEAT COMBO with NEG-DOMINANT
60% prior); NORMAL-RISK by mechanism (NO Optuna training-objective domain change;
only per-trial scalar aggregate changes from Sharpe to Sortino). Single-seed OPT-OUT
per cycle-5 EXPLORATION standard. ENSEMBLE_SIZE=3, n_trials=18, seed=42.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"LINKUSDT", "DOTUSDT"} guard fires in dispatch branch.
assert label_mode_arg == "trend_scanning" guard fires in dispatch branch.
assert optuna_objective_arg == "sortino" guard fires in dispatch branch.
assert vol_ceiling_mode_arg == "none" guard fires in dispatch branch (/038 NO carry-over).
"""

V1_ITER043_UNIVERSE: tuple[str, ...] = ("LINKUSDT",)
"""iter-v1/043 cohort: LINK-only 1-specialist with trend-scanning labels.

Cycle-5 EXPLORATION #10 of 10 (CADENCE COMPLETE — /044 CONFIRMATION can launch after
/043 closeout). Axis family: per-cohort-specialization × labeling REPEAT-COMBO.

Architecture: Model C' LINK only (R1+R3 ON, atr_tp=3.5, atr_sl=1.75). LINK uses
trend-scanning labels with grid (5, 8, 13, 21). Model A pool, Model D LTC, Model E DOT,
Model G ETH SKIPPED.

NORMAL-RISK declaration: composition of two previously-shipped, audited mechanisms
(/036 per-cohort isolation + /035 trend-scanning). No new Optuna training-objective
domain change. No new src/ helper modules. ENSEMBLE_SIZE=3, n_trials=18, seed=42.

LOAD-BEARING PURPOSE: /044 substrate-composition diagnostic. Resolves whether /036's
LINK+DOT OOS lift (+1.7465) is LINK-carried (DOT was passenger) or pairing-carried
(DOT provides essential risk-diversification at portfolio σ level). Cannot be answered
without single-cohort LINK isolation at /036's exact config.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"LINKUSDT"} guard fires in dispatch branch.
assert label_mode_arg == "trend_scanning" guard fires in dispatch branch.
assert optuna_objective_arg in ("sharpe", None) guard fires in dispatch branch.
assert model_type_arg == "lgbm" guard fires in dispatch branch (/042 XGBoost NO carry-over).
"""


V1_ITER050_UNIVERSE: tuple[str, ...] = ("DOTUSDT",)
"""iter-v1/050 cohort: DOT-only regime-gated specialist.

Cycle-6 EXPLORATION #5 of 10. Axis family: feature-family + risk-primitive (compound;
single DOT-specialist mechanism). NEW feature dot_vs_btc_ret_ratio_30 (cross-asset
idiosyncratic ratio) + vol-spike regime gate (post-prediction, stateless).

NORMAL-RISK declaration: additive feature (no Optuna domain change) + post-prediction
stateless gate (no Optuna domain change). Single-seed OPT-OUT per EXPLORATION standard.
ENSEMBLE_SIZE=3, n_trials=18, seed=42.

BTC klines loaded for feature computation only (BTCUSDT is NOT traded).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"DOTUSDT"} guard fires in dispatch branch.
assert "dot_vs_btc_ret_ratio_30" in active_feature_columns guard fires in dispatch branch.
"""


__all__ = [
    "V1_EXCLUDED_SYMBOLS",
    "V1_BASELINE_UNIVERSE",
    "V1_FEATURE_COLUMNS",
    "V1_FEATURE_COLUMNS_PRUNED",
    "V1_OOD_FEATURE_COLUMNS",
    "V1_RETIRED_FEATURE_COLUMNS",
    "assert_v1_universe",
    "V1_ITER028_UNIVERSE",
    "V1_ITER029_UNIVERSE",
    "V1_ITER036_UNIVERSE",
    "V1_ITER039_UNIVERSE",
    "V1_ITER043_UNIVERSE",
    "V1_ITER050_UNIVERSE",
    # iter-v1/023: funding-rate feature family (add_funding_v1_features imported on demand)
    # iter-v1/025: OI delta feature family (add_oi_delta_v1_features imported on demand)
    # iter-v1/040: composed feature family (add_composed_v1_features imported on demand)
    # iter-v1/048: microstructure_v1 group was DE-REGISTERED from GROUP_REGISTRY at
    #              closeout (NEG-CLEAN-PRE-EDA: |IC|=0.9063 vs vol_volume_rel_20).
    #              Module file kept on disk as dead code for future-iter reuse.
    # iter-v1/049: long/short positioning feature family (add_longshort_v1_features imported
    #              on demand via features/__init__.py GROUP_REGISTRY longshort_v1 entry).
    # iter-v1/050: cross-BTC idiosyncratic ratio feature family (add_cross_btc_v1_features
    #              imported on demand via features/__init__.py GROUP_REGISTRY cross_btc_v1 entry).
]
