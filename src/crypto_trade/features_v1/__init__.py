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
    # "btc_funding_rate_8h_impulse" — iter-v1/054: DROPPED (rank >30/48 in 3/3 seeds at /053;
    #   INERT-by-importance multi-seed confirmed; 48 → 47 cols). Code preserved in funding_v1.py.
    "btc_funding_spread_30_90",  # iter-v1/052: NEW — funding term-structure slope (z30 minus z90)  # noqa: E501
    # "btc_oi_delta_5_z30" — iter-v1/058: REVERTED (multi-seed n=3: per-seed IS Sharpe
    #   [-0.372, +0.2153, -0.6842]; mean Δ +0.5697 IS lands in MULTI-SEED-SPECIALIST band
    #   ≥+0.50 BUT max-min spread 0.8995 > 0.50 → BASIN-LOTTERY downgrade per brief §8;
    #   49 → 48 cols). Feature computation code preserved in open_interest_v1.py.
    "cal_dow_norm",
    "cal_hour_norm",
    "dot_vs_btc_ret_ratio_30",  # iter-v1/050: NEW — DOT idiosyncratic return vs BTC 30d z-scored (DOT-only; NaN for other syms)  # noqa: E501
    "eth_vs_btc_ret_ratio_30",  # iter-v1/055: NEW — ETH idiosyncratic return vs BTC 30d z-scored (ETH-only; NaN for other syms)  # noqa: E501
    "funding_rate_zscore_30",  # iter-v1/023: NEW — funding-rate z-score 30-bar (10-day)
    "funding_rate_zscore_90",  # iter-v1/023: NEW — funding-rate z-score 90-bar (30-day)
    "interact_natr_x_adx",
    "interact_ret1_x_natr",
    "interact_ret1_x_ret3",
    "interact_rsi_x_adx",
    "interact_rsi_x_natr",
    "interact_stoch_x_adx",
    "long_short_zscore_30",  # iter-v1/049: NEW — top-trader long/short ratio z-score (30-bar)
    # "ltc_vs_btc_ret_ratio_30" — iter-v1/057: REVERTED (multi-seed mean Δ +0.1082 IS,
    #   max-min spread 0.765 → BASIN-LOTTERY downgrade; importance rank 13-15/49 fails
    #   LEARNED gate ≤10; 49 → 48 cols). Feature computation code preserved in cross_btc_v1.py.
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

# Sanity guard: confirm the pruned set has exactly 49 features.
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
# iter-v1/052: extended 46 → 48 by adding btc_funding_rate_8h_impulse (funding shock
#              detector; normalized 1st-diff of funding_rate over 90-bar rolling std) and
#              btc_funding_spread_30_90 (term-structure slope; z30 minus z90). Both are
#              non-OHLCV funding-rate derived features for the BTC-specialist head.
#              Inserted alphabetically at positions 0 and 1.
# iter-v1/054: DROP btc_funding_rate_8h_impulse (rank >30/48 in 3/3 outer seeds at /053;
#              INERT-by-importance multi-seed confirmed). btc_funding_spread_30_90 RETAINED
#              (rank 4-10/48 in 3/3 seeds at /053; STABLE confirmed). Count: 48 → 47.
#              Feature computation code preserved in funding_v1.py (restore path if needed).
# iter-v1/055: ADD eth_vs_btc_ret_ratio_30 (ETH idiosyncratic return vs BTC 30d, z-scored
#              90-bar; ETH-only specialist head; direct algebraic mirror of /050
#              dot_vs_btc_ret_ratio_30; cycle-6 EXPLORATION 10/10 FINAL). Count: 47 → 48.
#              Inserted alphabetically between dot_vs_btc_ret_ratio_30 and
#              funding_rate_zscore_30.
# iter-v1/057: ADD ltc_vs_btc_ret_ratio_30 (LTC idiosyncratic return vs BTC 30d, z-scored
#              90-bar; LTC-only specialist head; direct algebraic mirror of /055
#              eth_vs_btc_ret_ratio_30; cycle-7 EXPLORATION 1/N). Count: 48 → 49.
#              Inserted alphabetically between long_short_zscore_30 and mom_macd_hist_12_26_9.
# iter-v1/057 CLOSEOUT: REVERT ltc_vs_btc_ret_ratio_30 (multi-seed n=3: per-seed IS Sharpe
#              [0.736, 0.1276, -0.029]; mean Δ +0.1082 IS lands in MULTI-SEED-WEAK band
#              [+0.05, +0.20); max-min spread 0.765 > 0.50 → BASIN-LOTTERY downgrade per
#              brief §4.3; importance rank 13-15/49 fails LEARNED gate ≤10; mean OOS -0.5163
#              with per-seed [-1.6307, +0.0988, -0.0171]). Count: 49 → 48. Feature
#              computation code preserved in cross_btc_v1.py for potential future re-use.
# iter-v1/058: ADD btc_oi_delta_5_z30 (OI 5-bar delta 40h, z-scored 30-bar 10d; short-
#              window companion to oi_delta_30_z90; BTC specialist cycle-7 EXP-2/N).
#              Count: 48 → 49. Inserted alphabetically after btc_funding_spread_30_90.
# iter-v1/058 CLOSEOUT: REVERT btc_oi_delta_5_z30 (multi-seed n=3: per-seed IS Sharpe
#              [-0.372, +0.2153, -0.6842]; mean Δ +0.5697 IS lands in MULTI-SEED-SPECIALIST
#              band ≥+0.50 BUT max-min spread 0.8995 > 0.50 → BASIN-LOTTERY downgrade per
#              brief §8; importance rank [10, 11, 10]/49 across 3 seeds passes LEARNED gate
#              ≤10 borderline but stability gate dominates; mean OOS -0.599 with per-seed
#              [-0.9069, +0.413, -1.303]). Count: 49 → 48. Feature computation code
#              preserved in open_interest_v1.py for potential future re-use at different
#              window pair.
assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
    f"V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
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


V1_ITER051_UNIVERSE: tuple[str, ...] = ("DOTUSDT",)
"""iter-v1/051 cohort: DOT-only multi-seed re-validation of iter-v1/050.

Cycle-6 EXPLORATION #6 of 10. Axis family: validation (multi-seed re-validation sub-type).
Same cohort as /050: DOTUSDT only. NO new feature; NO vol-spike regime gate (was 0% fire
rate / INERT at /050 — dropped for simplicity). V1_FEATURE_COLUMNS_PRUNED (46 cols) unchanged.

NORMAL-RISK declaration: seed variation does not change Optuna training-objective domain.
Multi-seed validation: --seeds 4 (outer seed offsets 0, 5, 10, 15 from ENSEMBLE_SEEDS roster).
ENSEMBLE_SIZE=3, n_trials=18.

BTC klines loaded for cross-asset feature computation only (BTCUSDT is NOT traded).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"DOTUSDT"} guard fires in dispatch branch.
assert "dot_vs_btc_ret_ratio_30" in active_feature_columns guard fires in dispatch branch.
assert len(active_feature_columns) == 46 guard fires in dispatch branch.
"""


V1_ITER052_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/052 cohort: BTC-only specialist head.

Cycle-6 EXPLORATION #7 of 10. Axis family: feature-family (funding-rate derived transforms;
non-OHLCV primitive class). NEW features: btc_funding_rate_8h_impulse (shock detector) +
btc_funding_spread_30_90 (term-structure slope; z30 minus z90). V1_FEATURE_COLUMNS_PRUNED
extended 46 → 48 cols.

NORMAL-RISK declaration: additive features + cohort isolation (no Optuna domain change).
Single-seed=42 (EXPLORATION standard). ENSEMBLE_SIZE=3, n_trials=18.

Per-symbol architecture mandate: BTC-only specialist replacing pooled Model A for BTCUSDT.
R3=ON, R1=OFF, R2=OFF (same as baseline Model A for BTC).

BTC klines are the TRADED symbol (BTCUSDT). Funding-rate cache loaded from
data/funding_rates/BTCUSDT.csv at feature-gen time.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"BTCUSDT"} guard fires in dispatch branch.
assert "btc_funding_rate_8h_impulse" in active_feature_columns guard fires in dispatch branch.
assert "btc_funding_spread_30_90" in active_feature_columns guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER053_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/053 cohort: BTC-only specialist head (multi-seed re-validation of /052).

Cycle-6 EXPLORATION #8 of 10. Axis family: validation (multi-seed re-validation sub-type;
no new feature or gate axis). Features UNCHANGED from /052: btc_funding_rate_8h_impulse
(rank 38/48 INERT) + btc_funding_spread_30_90 (rank 4/48 STRONGLY LEARNED).
V1_FEATURE_COLUMNS_PRUNED = 48 cols (UNCHANGED).

NORMAL-RISK declaration: seed variation only (no Optuna training-objective domain change).
Multi-seed: --seeds 3, _OUTER_SEED_OFFSETS=(0,3,6), ENSEMBLE_SIZE=3, n_trials=18.
Outer seed pools (fully disjoint): offset0=[42,123,456], offset3=[789,1001,2002],
offset6=[3003,4004,5005].

Architecture: Model A_BTC_specialist (BTC only). R3=ON, R1=OFF, R2=OFF. atr_tp=3.5,
atr_sl=1.75 (unchanged from /052 and baseline Model A).

Both-or-neither revert rule (from LM Master Rec 1 at /052) BINDING:
  SPECIALIST-CONFIRMED or PARTIAL-CONFIRMED → RETAIN both features.
  NEG-CLEAN-MULTI-SEED or BASIN-LOTTERY → REVERT both features.

Defined INDEPENDENTLY from V1_ITER052_UNIVERSE (per LM Master Flag C at /053 Phase 4.5) to
allow independent revert/keep decisions without coupling /052 and /053 constants.
assert set(symbols) == {"BTCUSDT"} guard fires in dispatch branch.
assert "btc_funding_rate_8h_impulse" in active_feature_columns guard fires in dispatch branch.
assert "btc_funding_spread_30_90" in active_feature_columns guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER054_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/054 cohort: BTC-only specialist head (impulse-drop attribution test).

Cycle-6 EXPLORATION #9 of 10. Axis family: feature-family (feature-pruning sub-axis;
DROP btc_funding_rate_8h_impulse from V1_FEATURE_COLUMNS_PRUNED; KEEP btc_funding_spread_30_90).
V1_FEATURE_COLUMNS_PRUNED extended: 48 → 47 cols (impulse DROPPED; spread RETAINED).

Triggering mandate: /053 PARTIAL-CONFIRMED (mean IS Δ +0.8102; impulse rank >30/48 in 3/3
seeds; spread rank 4-10/48 in 3/3 seeds). /053 LM Master Rec 1 conditional FIRES: impulse-drop
revaluation at /054.

NORMAL-RISK declaration: dropping one INERT feature (rank >30 multi-seed confirmed) does NOT
change Optuna's training-objective domain. Single-seed=42 (EXPLORATION standard).
ENSEMBLE_SIZE=3, n_trials=18.

Decision tree (brief Section 4 F-AXIS #1):
  Spread IS ≥ +0.16 → IMPULSE-DROP-CONFIRMED (impulse permanently removed; 47-col stack)
  Spread IS ∈ [0, +0.16) → IMPULSE-DROP-MARGINAL (retain both; /055 CONFIRMATION at 48 cols)
  Spread IS < 0 → IMPULSE-DROP-DEGRADES (restore impulse; /055 CONFIRMATION at 48 cols)

Feature computation code for btc_funding_rate_8h_impulse is PRESERVED in funding_v1.py.
The runner does NOT pass it to LightGBM feature_columns (47-col V1_FEATURE_COLUMNS_PRUNED).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"BTCUSDT"} guard fires in dispatch branch.
assert "btc_funding_spread_30_90" in active_feature_columns guard fires.
assert "btc_funding_rate_8h_impulse" not in active_feature_columns guard fires.
assert len(active_feature_columns) == 47 guard fires in dispatch branch.
"""


V1_ITER056_C1_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/056 C1-BTC: CONFIRMATION-budget BTC specialist sub-run.

Cycle-6 CONFIRMATION 1/1. Re-measures /054 impulse-drop-confirmed at ens-size=10, n_trials=35.
Feature stack: V1_FEATURE_COLUMNS_PRUNED (47 cols; btc_funding_spread_30_90 RETAINED,
btc_funding_rate_8h_impulse DROPPED per /054).
Architecture: Model A_BTC_specialist (R3=ON, R1=OFF, R2=OFF). atr_tp=3.5, atr_sl=1.75.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"BTCUSDT"} guard fires in dispatch branch.
assert "btc_funding_spread_30_90" in active_feature_columns guard fires.
assert "btc_funding_rate_8h_impulse" not in active_feature_columns guard fires.
assert len(active_feature_columns) == 47 guard fires in dispatch branch.
"""


V1_ITER056_C2_UNIVERSE: tuple[str, ...] = ("ETHUSDT",)
"""iter-v1/056 C2-ETH: CONFIRMATION-budget ETH specialist sub-run.

Cycle-6 CONFIRMATION 1/1. Re-measures /055 ETH specialist at ens-size=10, n_trials=35.
Feature stack: V1_FEATURE_COLUMNS_PRUNED (48 cols; eth_vs_btc_ret_ratio_30 ADDED per /055).
Architecture: Model A_ETH_specialist (R3=ON, R1=OFF, R2=OFF). atr_tp=3.5, atr_sl=1.75.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"ETHUSDT"} guard fires in dispatch branch.
assert "eth_vs_btc_ret_ratio_30" in active_feature_columns guard fires.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER056_C3_UNIVERSE: tuple[str, ...] = ("DOTUSDT",)
"""iter-v1/056 C3-DOT: CONFIRMATION-budget DOT specialist sub-run.

Cycle-6 CONFIRMATION 1/1. Re-measures /050-/051 DOT specialist at ens-size=10, n_trials=35.
Feature stack: V1_FEATURE_COLUMNS_PRUNED (48 cols; dot_vs_btc_ret_ratio_30 present;
eth_vs_btc_ret_ratio_30 NaN for DOTUSDT — LightGBM handles NaN natively).
Architecture: Model E_DOT_specialist (R3=ON, R1=ON K=3/C=27, R2=ON 7%/15%/0.33).
atr_tp=3.5, atr_sl=1.75 (same as BASELINE_V1 Model E).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"DOTUSDT"} guard fires in dispatch branch.
assert "dot_vs_btc_ret_ratio_30" in active_feature_columns guard fires.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER055_UNIVERSE: tuple[str, ...] = ("ETHUSDT",)
"""iter-v1/055 cohort: ETH-only specialist head.

Cycle-6 EXPLORATION #10 of 10 FINAL. Axis family: feature-family (ADD eth_vs_btc_ret_ratio_30;
direct algebraic mirror of /050 dot_vs_btc_ret_ratio_30 for ETH-only specialist head).
V1_FEATURE_COLUMNS_PRUNED extended: 47 → 48 cols (eth_vs_btc_ret_ratio_30 ADDED).

ETH baseline IS Sharpe: -0.61 (second-worst of 5 symbols; 145 IS trades).
Mandate: /054 catalog row pre-registered ETH specialist as the /055 mandate
  ("biggest unexplored IS-negative remaining; mirror /050-/052 cross-asset feature design").

NORMAL-RISK declaration: additive feature + cohort isolation — no Optuna training-objective
domain change. Single-seed=42 (EXPLORATION standard). ENSEMBLE_SIZE=3, n_trials=18.

Architecture: Model_A_ETH_specialist (ETH only).
  R3=ON, R1=OFF, R2=OFF (same as baseline Model A for ETH).
  atr_tp=3.5, atr_sl=1.75 (UNCHANGED from baseline Model A + /050-/054 specialist convention).

BTC klines are loaded for cross-asset feature computation only (BTCUSDT is NOT traded).

Verdict bands (brief Section 4 F-AXIS #1):
  IS ≥ 0.00 (Δ ≥ +0.61) → SPECIALIST-CANDIDATE; pre-register /057 ETH multi-seed
  IS ∈ [-0.31, 0.00) (Δ ∈ [+0.30, +0.61)) → PARTIAL; pre-register /057 ETH multi-seed
  IS ∈ [-0.56, -0.31) (Δ ∈ [+0.05, +0.30)) → WEAK; no multi-seed; ETH stays pooled
  IS ∈ (-0.66, -0.56) (Δ ∈ (-0.05, +0.05)) → NEG-INERT; no signal added
  IS < -0.66 (Δ < -0.05) → NEG-CLEAN; feature reverted from V1_FEATURE_COLUMNS_PRUNED

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"ETHUSDT"} guard fires in dispatch branch.
assert "eth_vs_btc_ret_ratio_30" in active_feature_columns guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER064_UNIVERSE: tuple[str, ...] = ("ETHUSDT",)
"""iter-v1/064 cohort: ETH-only SPECIALIST (second under SPECIALIST + BUNDLE methodology).

Cycle-7 SPECIALIST 2/10. Axis family: methodology (continued from /063 — generalization test
across a second cohort with a different baseline IS profile).

50-seed independent-Optuna bagging on ETHUSDT:
    V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30,
    max_depth=5 FIXED, num_leaves=31 FIXED, min_child_samples REMOVED,
    ENSEMBLE_SIZE=1 per study, mean-of-signed-weights aggregator.

Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED).
Risk config: R1=OFF (Model A baseline — BTC/ETH mean-reverting WR at late streaks),
             R2=OFF (Model A baseline — R2 is Model E DOT-only disposition),
             R3=ON-SHARED (cutoff=0.70, 16-feature V1_OOD_FEATURE_COLUMNS),
             R5=ON (vt_target_vol=0.3, vt_lookback_days=45).
atr_tp=2.9, atr_sl=1.45 (matched to Model A ETH cell in run_baseline_v1.py:3296-3308).

Baseline ETH IS Sharpe: -0.61 (per-symbol attribution, BASELINE_V1.md:113).
F-AXIS #1 (load-bearing): mean IS Sharpe >= -0.61 (i.e. delta >= 0 vs baseline).
F-AXIS #2 (informational): per-candle ensemble dispersion mean sigma_pop <= 0.30.
NORMAL-RISK: cohort change (DOT->ETH) does NOT alter Optuna training-objective domain.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"ETHUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER063_UNIVERSE: tuple[str, ...] = ("DOTUSDT",)
"""iter-v1/063 cohort: DOT-only SPECIALIST (first SPECIALIST under SPECIALIST + BUNDLE methodology).

Cycle-7 SPECIALIST 1/10. Axis family: methodology (SPECIALIST + BUNDLE design).
50-seed independent-Optuna bagging on DOTUSDT:
    V1_SPECIALIST_SEED_COUNT=50, V1_SPECIALIST_OPTUNA_TRIALS=30,
    max_depth=5 FIXED, num_leaves=31 FIXED, min_child_samples REMOVED,
    ENSEMBLE_SIZE=1 per study, mean-of-signed-weights aggregator.

Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED).
Risk config: R1=ON (K=3, C=27), R2=ON (trigger=7%, anchor=15%, floor=0.33),
             R3=ON-SHARED (cutoff=0.70, 16-feature V1_OOD_FEATURE_COLUMNS),
             R5=ON (vt_target_vol=0.3, vt_lookback_days=45).
atr_tp=3.5, atr_sl=1.75 (UNCHANGED from BASELINE_V1 Model E DOT).

Methodology validates: σ_pop ≤ 0.30 (F-AXIS #2 load-bearing gate).
NORMAL-RISK: bagging dimensionality change, NOT Optuna training-objective domain change.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"DOTUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER061_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/061 cohort: BTC-only zero-randomness diagnostic.

Cycle-7 EXPLORATION #4/N. Axis family: methodology (zero-randomness diagnostic; pipeline
reproducibility test). Tests whether the v1 BTC-only specialist pipeline is bit-exactly
reproducible when ALL sources of randomness are eliminated:
    n_trials=1, seeds=1, subsample=1.0, colsample_bytree=1.0, bagging_freq=0,
    deterministic=True, num_threads=1, is_unbalance=False, force_col_wise=True.

V1_FEATURE_COLUMNS_PRUNED: 48 cols UNCHANGED (no feature add/drop at /061).
Architecture: Model A_BTC_specialist (BTC only).
    R1=OFF (same as /052-/054 BTC specialist convention).
    R2=OFF (same as /052-/054 BTC specialist convention).
    R3=OFF (LM Master §"Other Randomness Sources" #9 — disabled to eliminate
            covariance-inversion non-determinism from the experiment).
    atr_tp=3.5, atr_sl=1.75 (UNCHANGED from BTC specialist convention).

LM Master Phase 4.5 hardcoded HP dict (ADOPTED VERBATIM):
    n_estimators=300, max_depth=4, num_leaves=31, learning_rate=0.05,
    min_child_samples=50, reg_alpha=0.1, reg_lambda=0.1, confidence_threshold=0.7,
    training_days=360 — central-tendency HPs from /054 trial analysis.

NORMAL-RISK: methodology-only axis; no Optuna domain change; no feature change.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"BTCUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER058_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/058 cohort: BTC-only specialist head (btc_oi_delta_5_z30 short-window OI feature).

Cycle-7 EXPLORATION #2/N. Axis family: feature-family (ADD btc_oi_delta_5_z30; 5-bar OI %
change z-scored over 30 bars = 10 calendar days; algebraic sister of oi_delta_30_z90 at 6×
higher frequency; targets rapid institutional positioning shifts at 40h horizon).
V1_FEATURE_COLUMNS_PRUNED extended: 48 → 49 cols (btc_oi_delta_5_z30 ADDED).

BTC baseline IS Sharpe: −0.85 (biggest IS-headroom symbol in the bundle).
Mandate: /057 BASIN-LOTTERY on cross-asset return ratio family; pivot to OI-delta family
per LM Master Phase 4.5 advisory (axis-adjacent to existing oi_delta_30_z90 signal).

Multi-seed design (built-in from start; per /056 + /057 basin-lottery lessons):
    --seeds 3, ENSEMBLE_SIZE=3, _OUTER_SEED_OFFSETS=(0, 3, 6)
    → 9 disjoint inner seeds: [42,123,456] / [789,1001,2002] / [3003,4004,5005]
    Verdict basis: MULTI-SEED MEAN (n=3 outer seeds). Single-seed=42 informational only.

Architecture: Model A_BTC_specialist (BTC only).
    R3=ON (OOD Mahalanobis gate, cutoff=0.70, 16-feature V1_OOD_FEATURE_COLUMNS).
    R1=OFF (no consecutive-SL cooldown — same as /052-/054 BTC specialist convention).
    R2=OFF (no drawdown scaling — same as /052-/054 BTC specialist convention).
    atr_tp=3.5, atr_sl=1.75 (UNCHANGED from BASELINE_V1 Model A BTC specialist).

NORMAL-RISK declaration: additive feature + cohort isolation — no Optuna training-objective
domain change. Single-seed=42 informational only at multi-seed EXPLORATION budget.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"BTCUSDT"} guard fires in dispatch branch.
assert "btc_oi_delta_5_z30" in active_feature_columns guard fires in dispatch branch.
assert len(active_feature_columns) == 49 guard fires in dispatch branch.
"""


V1_ITER057_UNIVERSE: tuple[str, ...] = ("LTCUSDT",)
"""iter-v1/057 cohort: LTC-only specialist head.

Cycle-7 EXPLORATION #1/N. Axis family: feature-family (ADD ltc_vs_btc_ret_ratio_30;
direct algebraic mirror of /055 eth_vs_btc_ret_ratio_30 for LTC-only specialist head).
V1_FEATURE_COLUMNS_PRUNED extended: 48 → 49 cols (ltc_vs_btc_ret_ratio_30 ADDED).

LTC baseline IS Sharpe: +0.17 (second-worst IS; worst OOS OOD divergence: OOS -4.27).
Mandate: /056 CONFIRMATION-BLOCK established cycle-7 EXP-1 mandate for LTC specialist.
Multi-seed BUILT IN from start: --seeds 3, ensemble_size=3, _OUTER_SEED_OFFSETS=(0,3,6).
Verdict basis: MULTI-SEED MEAN (n=3 outer seeds). Single-seed=42 is informational only.

NORMAL-RISK declaration: additive feature + cohort isolation — no Optuna training-objective
domain change. Multi-seed: --seeds 3 at ENSEMBLE_SIZE=3. n_trials=18.

Architecture: Model_D_LTC_specialist (LTC only).
  R1=ON (K=3 consecutive SL limit, C=27 candle cooldown — same as BASELINE_V1 Model D)
  R2=OFF (no drawdown scaling — same as BASELINE_V1 Model D)
  R3=ON (OOD Mahalanobis gate, cutoff=0.70, 16-feature V1_OOD_FEATURE_COLUMNS)
  atr_tp=3.5, atr_sl=1.75 (UNCHANGED from BASELINE_V1 Model D specialist convention).

BTC klines loaded for cross-asset feature computation only (BTCUSDT is NOT traded).

Verdict bands (brief Section 4 F-AXIS #1, multi-seed MEAN):
  Mean IS Δ ≥ +0.50 → MULTI-SEED-SPECIALIST-CANDIDATE; pre-register cycle-7 CONFIRMATION
  Mean IS Δ ∈ [+0.20, +0.50) → MULTI-SEED-PARTIAL-CONFIRMED; pre-register cycle-7 CONFIRMATION
  Mean IS Δ ∈ [+0.05, +0.20) → MULTI-SEED-WEAK; no CONFIRMATION; LTC stays pooled
  Mean IS Δ ∈ (-0.05, +0.05) → NEG-INERT; no signal; ltc_vs_btc_ret_ratio_30 stays in pruned
  Mean IS Δ < -0.05 → NEG-CLEAN; ltc_vs_btc_ret_ratio_30 reverted from V1_FEATURE_COLUMNS_PRUNED

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"LTCUSDT"} guard fires in dispatch branch.
assert "ltc_vs_btc_ret_ratio_30" in active_feature_columns guard fires in dispatch branch.
assert len(active_feature_columns) == 49 guard fires in dispatch branch.
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
    "V1_ITER051_UNIVERSE",
    "V1_ITER052_UNIVERSE",
    "V1_ITER053_UNIVERSE",
    "V1_ITER054_UNIVERSE",
    "V1_ITER055_UNIVERSE",
    "V1_ITER056_C1_UNIVERSE",
    "V1_ITER056_C2_UNIVERSE",
    "V1_ITER056_C3_UNIVERSE",
    "V1_ITER057_UNIVERSE",
    "V1_ITER058_UNIVERSE",
    "V1_ITER061_UNIVERSE",
    "V1_ITER063_UNIVERSE",
    "V1_ITER064_UNIVERSE",
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
