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
# v3 (live), or kept reserved for explicit methodological reasons.
# iter-v1/087: BNBUSDT UN-RESERVED per user directive 2026-06-10.
#   "Don't discard BNB — un-reserve it." The real backtest (run_iteration_087.py)
#   is the proof; the fail-fast gate decides the outcome rather than a pre-hoc
#   reservation.  XRP/DOGE/NEAR/SOL/BCH/LDO/TRX remain excluded (v2/v3 live).
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
    # iter-v1/087: BNBUSDT deliberately removed from exclusion list.
    # The backtest (run_iteration_087.py) with fail_fast_is_years=2.0 is the proof.
    # "BNBUSDT",  ← un-reserved per user directive 2026-06-10
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
# iter-v1/084: LOCAL-ONLY — oi_price_divergence_30 (OI-price direction divergence z-score;
#              CRV specialist cycle-7 EXPLORATION) is intentionally NOT in the global
#              V1_FEATURE_COLUMNS_PRUNED. It lives exclusively in V1_ITER084_FEATURE_COLUMNS
#              below (= PRUNED(48) + (oi_price_divergence_30,) = 49 cols). Keeping the global
#              at 48 prevents the feature from silently altering DOT/ETH/BTC/AAVE/ATOM
#              specialists (a methodology violation — one variable at a time).
assert len(V1_FEATURE_COLUMNS_PRUNED) == 48, (
    f"V1_FEATURE_COLUMNS_PRUNED must have exactly 48 features; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
)

# iter-v1/084 LOCAL feature set: 48-col global PRUNED + CRV-specialist oi_price_divergence_30.
# This is the ONLY constant that should be 49; V1_FEATURE_COLUMNS_PRUNED stays at 48.
# The runner (run_iteration_084.py + run_baseline_v1.py "/v1-084" dispatch) overrides
# active_feature_columns with this local tuple so that no other specialist sees the new feature.
V1_ITER084_FEATURE_COLUMNS: tuple[str, ...] = V1_FEATURE_COLUMNS_PRUNED + (
    "oi_price_divergence_30",
)

assert len(V1_ITER084_FEATURE_COLUMNS) == 49, (
    f"V1_ITER084_FEATURE_COLUMNS must have exactly 49 features; "
    f"got {len(V1_ITER084_FEATURE_COLUMNS)}"
)

# iter-v1/085 LOCAL feature set: 48-col global PRUNED + 4 UNI-specialist mean-reversion features.
# These 4 features are LOCAL to the UNI specialist cell — keeping them out of the global PRUNED
# prevents silently altering DOT/ETH/BTC/AAVE/CRV specialists (one-variable-at-a-time rule).
# The runner (run_iteration_085.py + run_baseline_v1.py "/v1-085" dispatch) overrides
# active_feature_columns with this local tuple so that no other specialist sees the new features.
V1_ITER085_FEATURE_COLUMNS: tuple[str, ...] = V1_FEATURE_COLUMNS_PRUNED + (
    "rev_extension_z_3",
    "rev_halflife_50",
    "rev_vol_gate_signed",
    "vol_state_z_natr_30",
)

assert len(V1_ITER085_FEATURE_COLUMNS) == 52, (
    f"V1_ITER085_FEATURE_COLUMNS must have exactly 52 features "
    f"(48 base + 4 new UNI-specialist); got {len(V1_ITER085_FEATURE_COLUMNS)}"
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


V1_ITER074_UNIVERSE: tuple[str, ...] = ("ETHUSDT",)
"""iter-v1/074 cohort: ETH-only SPECIALIST-IMPROVEMENT-V3 (AXIS-R Mid-Bull SHORT VETO).

Cycle-7 SPECIALIST-IMPROVEMENT 3rd attempt for ETH BUNDLE-001 seat. Anchor: /064.
Axis family: risk-primitive (post-aggregator RULE-form veto).

Single-bit deviation from /064: enables post-aggregator AXIS-R veto in LightGbmStrategy.
  enable_mid_bull_short_veto=True, mid_bull_short_veto_lo=0.20, mid_bull_short_veto_hi=0.50,
  mid_bull_short_veto_lookback=270 (270 8h candles = 90 calendar days).
Pre-registered band edges [0.20, 0.50] frozen at brief authoring commit.

Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED — NO parquet regeneration).
Risk config: R1=OFF, R2=OFF, R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3.
atr_tp=2.9, atr_sl=1.45 (Model A ETH cell — IDENTICAL to /064).

AXIS-R veto is a post-aggregator rule-layer primitive. Does NOT change:
  - feature stack (48 cols UNCHANGED)
  - Optuna training-objective domain (basin identical to /064)
  - labeling (ATR TP=2.9/SL=1.45 UNCHANGED)
  - risk wrappers (R1=OFF R2=OFF R3=ON UNCHANGED)

HIGH-RISK declaration (brief Section 2.5): rule-layer inference injection modifies deployed
trade roster (32 of 198 IS trades skipped). Mitigated by mechanism-orthogonality to
basin-lottery (H1d): inner-seed Optuna trajectories deterministic on /064 basin.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"ETHUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER075_UNIVERSE: tuple[str, ...] = ("ATOMUSDT",)
"""iter-v1/075 cohort: ATOM-only SPECIALIST — first NEW SYMBOL universe-extension.

Autopilot mining directive 2026-06-06. Cycle-7 SPECIALIST-MINE 1/N.
Mine-phase composite rank 1/N (score 0.767).
Axis family: universe (NEW SYMBOL; cycle-7 per-symbol regime-specialist mandate).

Single-bit deviation vs /063 dispatch: SYMBOLS=("ATOMUSDT",), ITERATION_LABEL="v1-075",
ATR cell /063's (3.5, 1.75) → ETH/064's (2.9, 1.45) [vol-class match for ATOM 80% IS vol].
Model A wrapper (R1=OFF, R2=OFF) — matches /064 ETH and /065 BTC; NOT /063 DOT's Model E.
All other methodology constants HELD per user directive 2026-06-06:
    50 inner seeds × 30 Optuna trials × specialist_mode=True
    48-col V1_FEATURE_COLUMNS_PRUNED
    (hash b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3)
    R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3, mean-of-signed-weights aggregator.

Data extent: 6.33y (2020-02-07 → 2026-06-06; 6933 8h candles).
IS BTC return corr: 0.617 (highest idiosyncratic diversity in eligible set).
IS realized vol: ~80% annualized (ETH-class mid-vol; justifies ATR(2.9, 1.45) cell).
F-AXIS #1: PROMISING-CLEAN ≥+0.50; PROMISING-TENTATIVE [+0.20, +0.50);
    NEGATIVE <+0.20 or <50 IS trades.
Strike rule: one-attempt-and-eliminate (per /066 LINK + /067 LTC precedent for NEW SYMBOL).

NaN notes: dot_vs_btc_ret_ratio_30 + eth_vs_btc_ret_ratio_30 are ALL-NaN-IS for ATOM
(SYMBOL-conditional; LightGBM NaN-handles natively; 2/48 = 4.2% wasted slot fraction).

HIGH-RISK declaration (brief Section 2.5): universe substitution changes Optuna's
training-objective domain. Mitigation: 50-INNER-seed averaging (σ_pop ≤ 0.30 gate
held at /063, /064, /065).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"ATOMUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER076_UNIVERSE: tuple[str, ...] = ("AAVEUSDT",)
"""iter-v1/076 cohort: AAVE-only SPECIALIST — second NEW SYMBOL universe-extension (DeFi-lending).

Autopilot mining directive 2026-06-06. Cycle-7 SPECIALIST-MINE 2/N.
Mine-phase rank 2/N (DeFi-lending narrative first; rank-1 ATOM/075 is cosmos-interop).
Axis family: universe (NEW SYMBOL; cycle-7 per-symbol regime-specialist mandate).

Single-bit deviation vs /063 dispatch: SYMBOLS=("AAVEUSDT",), ITERATION_LABEL="v1-076",
ATR cell /063's (3.5, 1.75) → ETH/064's (2.9, 1.45) [vol-class match for AAVE ~95% IS vol].
Model A wrapper (R1=OFF, R2=OFF) — matches /064 ETH, /065 BTC, /075 ATOM; NOT /063 DOT's Model E.
All other methodology constants HELD per user directive 2026-06-06:
    50 inner seeds × 30 Optuna trials × specialist_mode=True
    48-col V1_FEATURE_COLUMNS_PRUNED
    (hash b81176f893826500536ec5cee8ad00e74bf7edb834290e62e835213defe74ca3)
    R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3, mean-of-signed-weights aggregator.

Data extent: 5.64y (2020-10-16 → 2026-06-06; 6178 8h candles).
IS ETH return corr: 0.750 (LOAD-BEARING DeFi-cycle leakage risk; BUNDLE-002 pair-check hardwired).
IS realized vol: ~95% annualized (ETH-to-DOT mid-vol; justifies ATR(2.9, 1.45) ETH-class cell).
NEGATIVE-baseline gate: TS-mom (5,1) IS Sharpe −0.080 — ONLY eligible NEW SYMBOL passing cleanly.
F-AXIS #1: PROMISING-CLEAN ≥+0.50; PROMISING-TENTATIVE [+0.20, +0.50);
    NEGATIVE <+0.20 or <50 IS trades (one-attempt-and-eliminate rule).
Strike rule: one-attempt-and-eliminate (per /066 LINK + /067 LTC precedent for NEW SYMBOL).

NaN notes: dot_vs_btc_ret_ratio_30 + eth_vs_btc_ret_ratio_30 are ALL-NaN-IS for AAVE
(SYMBOL-conditional; LightGBM NaN-handles natively; 2/48 = 4.2% wasted slot fraction).
long_short_zscore_30 ~43% NaN-IS + oi_delta_30_z90 ~34% NaN-IS (AAVE data starts mid-window).

HIGH-RISK declaration (brief Section 2.5): universe substitution changes Optuna's
training-objective domain. Mitigation: 50-INNER-seed averaging (σ_pop ≤ 0.30 gate
held at /063, /064, /065, /075).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"AAVEUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""


V1_ITER084_UNIVERSE: tuple[str, ...] = ("CRVUSDT",)
"""iter-v1/084 cohort: CRV-only SPECIALIST (OI-price divergence + R-FADE gate).

Cycle-7 SPECIALIST-MINE N/N. Symbol selected via REFORMED SELECTION RULE:
prefer symbols with the MOST NEGATIVE trivial-momentum Sharpe (IS-only).
CRV trivial-momentum IS Sharpe: negative (ML has room to add edge).

Axis family: feature-family (ADD oi_price_divergence_30; OI-price divergence z-score,
re-aimed from /083 rank-7/11 OI family toward NEGATIVE-baseline CRVUSDT).
+ risk-primitive (R-FADE: OI-divergence-conditional confidence gate).

NEW feature: oi_price_divergence_30 — OI-price direction divergence z-score (30-bar
  delta, 90-bar z-score). V1_FEATURE_COLUMNS_PRUNED extended: 48 → 49 cols.
NEW risk: enable_oi_divergence_fade_gate=True (CRVUSDT specialist only) — post-aggregator
  stateless confidence gate: VETO entry when sign(signal) opposes sign(oi_price_divergence_30)
  AND |oi_price_divergence_30| > fade_z (default 2.0, IS-calibrated pre-registered).

Methodology constants HELD per 2026-06-06 directive:
    50 inner seeds × 30 Optuna trials × specialist_mode=True
    49-col V1_FEATURE_COLUMNS_PRUNED (NEW 49-col hash after parquet regen)
    R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3, mean-of-signed-weights aggregator.
    R1=OFF (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3).
    R2=OFF (Model A wrapper — matches /064 ETH, /065 BTC, /075 ATOM, /076 AAVE).
    ATR cell: (2.9, 1.45) [vol-class match for CRV ~100-130% IS vol, ETH-class].

Data extent: CRVUSDT 8h klines; OI cache data/open_interest/CRVUSDT/8h.csv (4954 rows).
NaN notes: dot_vs_btc_ret_ratio_30 + eth_vs_btc_ret_ratio_30 ALL-NaN for CRV
(SYMBOL-conditional; LightGBM NaN-handles natively).
long_short_zscore_30 + oi_delta_30_z90: some NaN early in IS window (OI archive start).

HIGH-RISK declaration: universe substitution (new symbol) changes Optuna training-objective
domain. Mitigation: 50-inner-seed averaging (σ_pop ≤ 0.30 gate).

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"CRVUSDT"} guard fires in dispatch branch.
assert "oi_price_divergence_30" in active_feature_columns guard fires in dispatch branch.
assert len(active_feature_columns) == 49 guard fires in dispatch branch.
"""


V1_ITER085_UNIVERSE: tuple[str, ...] = ("UNIUSDT",)
"""iter-v1/085 cohort: UNIUSDT-only SPECIALIST — new feature-engineering set #1.

Cycle-7 SPECIALIST-MINE. Symbol selected per user directive 2026-06-09:
"get one coin and focus on it. start with 4 features, 10. grind a bit."

4-feature set (LOCAL to /085; V1_FEATURE_COLUMNS_PRUNED stays at 48):
  rev_extension_z_3    — sign-flipped 3-bar return z-score (reversion signal; ac_lag3=-0.0843)
  vol_state_z_natr_30  — z-normalized 30-bar NATR volatility state conditioner
  rev_halflife_50      — z-normalized rolling AR(1) mean-reversion half-life (speed axis)
  rev_vol_gate_signed  — rev_extension_z_3 × soft vol-regime gate (composed capstone)

All 4 features go into V1_ITER085_FEATURE_COLUMNS (LOCAL 52 cols = PRUNED 48 + 4 new).
V1_FEATURE_COLUMNS_PRUNED (global) stays at 48 — one-variable-at-a-time discipline.

Methodology constants HELD per 2026-06-06 directive:
    50 inner seeds × 30 Optuna trials × specialist_mode=True
    52-col V1_ITER085_FEATURE_COLUMNS (LOCAL; new 52-col hash after parquet regen)
    R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3, mean-of-signed-weights aggregator.
    R1=OFF (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3).
    R2=OFF (Model A wrapper — matches /064 ETH, /065 BTC, /075 ATOM, /076 AAVE, /084 CRV).
    ATR cell: (2.9, 1.45) [vol-class match for UNI ~80-100% IS vol, ETH-class].

NaN notes: dot_vs_btc_ret_ratio_30 + eth_vs_btc_ret_ratio_30 ALL-NaN for UNI
(SYMBOL-conditional; LightGBM NaN-handles natively).
long_short_zscore_30 + oi_delta_30_z90: some NaN early in IS window (OI archive start).
rev_vol_gate_signed: depends on rev_extension_z_3 + vol_state_z_natr_30 (both LOCAL).
    Warmup: max(rev_extension_z_3, vol_state_z_natr_30) warmup ≈ 120 bars.

HIGH-RISK declaration: universe substitution (new symbol + new features) changes
Optuna training-objective domain. Mitigation: 50-inner-seed averaging.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"UNIUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 52 guard fires in dispatch branch.
assert all 4 new features in active_feature_columns guard fires in dispatch branch.
"""

V1_ITER086_UNIVERSE: tuple[str, ...] = ("TRBUSDT",)
"""iter-v1/086 cohort: TRBUSDT-only SPECIALIST — STOCK 48-col stack, NO new features.

Cycle-7 SPECIALIST-MINE #6; first fresh-mine candidate to clear the full HARD gate ladder:
  GATE 0: lowest average bundle-correlation (avg 0.548 vs {DOT, ETH, BTC, AAVE})
  GATE 1: negative short-horizon trivial baseline (min-horizon −0.179 ≤ +0.15)
  GATE 2 PRIMARY: structure-probe PASS (IS Sharpe +0.4930 ≥ +0.30)
  GATE 2 SECONDARY: max |IC| 0.3863 (mom_macd_line_12_26_9) — momentum/trend structure

Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, STOCK, UNCHANGED — NO new features).
Global V1_FEATURE_COLUMNS_PRUNED stays at 48. This is the load-bearing one-variable
discipline: the edge is already in the stock stack (confirmed by probe), so no feature
engineering surface is exposed for the /085 inert-feature noise-amplification trap.

Methodology constants (methodology-locked, mirrors AAVE/078 + UNI/085 spec):
    50 inner seeds (42..91) × 30 Optuna trials × specialist_mode=True
    ENSEMBLE_SIZE=1, single outer seed=42, mean-of-signed-weights aggregator
    max_depth=5 FIXED, num_leaves=31 FIXED
    R1=OFF (CATALOG-CLOSED for SPECIALIST_mode; f81cafc3)
    R2=OFF (Model A wrapper — matches /064 ETH, /065 BTC, /078 AAVE)
    R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    ATR cell: atr_tp=2.9, atr_sl=1.45 (Model A ETH/AAVE/UNI cell)

HIGH-RISK declaration: universe substitution (new symbol) changes Optuna training-objective
domain. Mitigation: 50-inner-seed ensemble.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"TRBUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""

V1_ITER087_UNIVERSE: tuple[str, ...] = ("BNBUSDT",)
"""iter-v1/087 cohort: BNBUSDT-only SPECIALIST — STOCK 48-col stack, fail-fast gate.

Cycle-7 SPECIALIST-MINE #7. BNBUSDT un-reserved per user directive 2026-06-10
("Don't discard BNB — un-reserve it. The backtest is the proof.").

Axis: per-cohort-specialization-BNB (universe substitution; NEW symbol in the
SPECIALIST roster). BNBUSDT is a top-10 perpetual by liquidity and OI; it was
historically reserved but never tested against the stock 48-col stack.

Fail-fast gate: fail_fast_is_years=2.0 enabled. If cumulative IS weighted_pnl
over the first 730 days of IS test trades is ≤ 0 → BLOCKED-FAIL-FAST, run aborts
early (saves remaining IS+OOS months × 50 seeds × 30 trials of compute).

Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, STOCK, UNCHANGED).
Methodology (mirrors AAVE/076, UNI/085, TRB/086):
    50 inner seeds (42..91) × 30 Optuna trials × specialist_mode=True
    ENSEMBLE_SIZE=1, single outer seed, mean-of-signed-weights aggregator
    max_depth=5 FIXED, num_leaves=31 FIXED
    R1=OFF (CATALOG-CLOSED for SPECIALIST_mode)
    R2=OFF (Model A baseline)
    R3=ON-SHARED cutoff=0.70, R5=ON vt_target_vol=0.3
    ATR cell: atr_tp=2.9, atr_sl=1.45

HIGH-RISK: universe substitution (new symbol) changes Optuna training-objective
domain. Mitigation: 50-inner-seed ensemble.

LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"BNBUSDT"} guard fires in dispatch branch.
assert len(active_feature_columns) == 48 guard fires in dispatch branch.
"""

V1_ITER065_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
"""iter-v1/065 cohort: BTC-only SPECIALIST (third SPECIALIST under SPECIALIST + BUNDLE methodology).

Cycle-7 SPECIALIST 3/N. Axis family: methodology (continued from /063 DOT, /064 ETH).
50-seed independent-Optuna bagging on BTCUSDT — the hardest-cohort generalization test.

Feature set: V1_FEATURE_COLUMNS_PRUNED (48 cols, UNCHANGED).
Risk config (matched to Model A BTC baseline cell, run_baseline_v1.py:3296-3308):
    R1=OFF (apply_r1=False — BTC mean-reverting WR at late streaks; R1 cooldown harms),
    R2=OFF (Model A baseline has no R2; R2 is Model E DOT-only disposition),
    R3=ON (Mahalanobis OOD gate, cutoff=0.70, 16 scale-invariant features; applied at
           AGGREGATOR level per SPECIALIST methodology, NOT per-seed),
    R5=ON (vt_target_vol=0.3, vt_lookback_days=45, vt_min_scale=0.33).
atr_tp=2.9, atr_sl=1.45 (Model A BTC convention; NOT /055 deviation 3.5/1.75).

SPECIALIST methodology is load-bearing: specialist_mode=True, V1_SPECIALIST_SEED_COUNT=50,
V1_SPECIALIST_OPTUNA_TRIALS=30, bounds_profile="v1_specialist" (max_depth=5 FIXED,
num_leaves=31 FIXED), signed-weight mean aggregator.

LOAD-BEARING PATCH at /065: specialist_dispersion.csv persistence (brief Section 6.5).
  runner calls strategy.persist_specialist_dispersion_csv(is_dir/specialist_dispersion.csv)
  AND appends specialist_dispersion_mean scalar to comparison.csv.
  LM Master Risk 1 declares this MANDATORY; Critic 7.5 BLOCKS if absent.

NORMAL-RISK: methodology axis does NOT change Optuna training-objective domain.
LOCAL to runner constant. NOT shared; CONFIRMATION-MERGE updates V1_BASELINE_UNIVERSE.
assert set(symbols) == {"BTCUSDT"} guard fires in dispatch branch.
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
    "V1_ITER084_FEATURE_COLUMNS",
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
    "V1_ITER065_UNIVERSE",
    "V1_ITER074_UNIVERSE",
    "V1_ITER075_UNIVERSE",
    "V1_ITER076_UNIVERSE",
    "V1_ITER084_UNIVERSE",
    "V1_ITER085_UNIVERSE",
    "V1_ITER085_FEATURE_COLUMNS",
    "V1_ITER086_UNIVERSE",
    "V1_ITER087_UNIVERSE",
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
