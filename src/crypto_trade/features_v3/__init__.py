"""v3 feature registry and orchestrator — rigor arm (iter-v3/001+).

Isolated from ``crypto_trade.features`` (v1) and ``crypto_trade.features_v2``
(v2). v3 code MUST NEVER import from either parent package. Track isolation is
enforced by the Phase 6 pre-flight grep check:

    grep -r "from crypto_trade.features " src/crypto_trade/features_v3/
    grep -r "from crypto_trade.features_v2" src/crypto_trade/features_v3/

Both must return empty. Violating this rule is a hard BLOCK.

Feature columns (V3_FEATURE_COLUMNS):
--------------------------------------
Initial V3 feature set = V2_FEATURE_COLUMNS (34 columns) with two renames
to mark the FracdiffStat substitution (iter-v3/001 brief Section 3.4):

    fracdiff_logclose_d04  → fracdiff_logclose_dstat
    fracdiff_logvolume_d04 → fracdiff_logvolume_dstat

Net column count: 34 (unchanged). No new feature families in iter-v3/001.

Groups in the v3 registry:
---------------------------
- ``regime``           — Hurst, ATR percentile ranks, BB width rank, CUSUM
                         reset count, natr_21_raw helper
- ``tail_risk``        — rolling skew/kurt, range realized vol, max drawdown
- ``price_efficient_vol`` — Parkinson, GK, Rogers-Satchell estimators
- ``momentum_accel``   — momentum acceleration, EMA spread, return autocorr
- ``volume_micro``     — VWAP deviation, volume CV, OBV slope, HL range ratio
- ``fracdiff``         — FracdiffStat-auto-d* fracdiff (v3 — replaces fixed d=0.4)
- ``cross_btc``        — BTC cross-asset features
- ``microstructure_v2`` — candle efficiency, vol transition, vol-return divergence

Cross-v2sym features (``cross_v2sym``) are omitted from v3: in v2 they produced
IS −70% / OOS −69% (iter-v2/043), and v3 uses a different peer universe.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from crypto_trade.features_v3.calendar_v3 import add_calendar_v3_features
from crypto_trade.features_v3.cross_btc_v3 import add_cross_btc_v3_features
from crypto_trade.features_v3.engineered_v3 import add_engineered_v3_features
from crypto_trade.features_v3.fracdiff_v3 import add_fracdiff_v3_features
from crypto_trade.features_v3.funding_v3 import (
    add_btc_funding_v3_features,
    add_funding_family_v3_features,
    add_funding_v3_features,
)
from crypto_trade.features_v3.microstructure_v3 import add_microstructure_v3_features
from crypto_trade.features_v3.momentum_accel_v3 import add_momentum_accel_v3_features
from crypto_trade.features_v3.price_efficient_vol_v3 import add_price_efficient_vol_v3_features
from crypto_trade.features_v3.regime_v3 import add_regime_v3_features
from crypto_trade.features_v3.tail_risk_v3 import add_tail_risk_v3_features
from crypto_trade.features_v3.technical_v3 import add_technical_v3_features
from crypto_trade.features_v3.volume_micro_v3 import add_volume_micro_v3_features
from crypto_trade.kline_array import load_kline_array
from crypto_trade.storage import csv_path

GROUP_REGISTRY: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    "regime": add_regime_v3_features,
    "tail_risk": add_tail_risk_v3_features,
    "price_efficient_vol": add_price_efficient_vol_v3_features,
    "momentum_accel": add_momentum_accel_v3_features,
    "volume_micro": add_volume_micro_v3_features,
    "cross_btc": add_cross_btc_v3_features,
    # iter-v3/025: Category 2 composed features; AFTER regime (needs hurst_100)
    # iter-v3/063: trend_efficiency_signed + vol_regime_x_momentum ADDED to dispatch
    "engineered_v3": add_engineered_v3_features,
    "fracdiff": add_fracdiff_v3_features,
    "microstructure_v3": add_microstructure_v3_features,
    # iter-v3/019: NEW external-data-source feature family; infrastructure PRESERVED
    "funding_v3": add_funding_v3_features,
    # iter-v3/024: cross-asset BTC funding broadcast; infrastructure PRESERVED
    "btc_funding_v3": add_btc_funding_v3_features,
    # iter-v3/082: funding-rate FEATURE FAMILY (cycle-3 EXPLORATION #1) — a
    # DIFFERENT axis from the closed single funding_rate_zscore_30. Builds the 4
    # FUNDING_FAMILY_COLUMNS (sign-persistence, momentum, acceleration,
    # funding-price divergence). Needs `close` — no ordering constraint vs the
    # other groups.
    "funding_family_v3": add_funding_family_v3_features,
    # iter-v3/063: NEW technical indicators (ADX); AFTER regime (shares ATR dependency)
    "technical_v3": add_technical_v3_features,
    # iter-v3/063: NEW calendar/temporal features (DOW cyclic encoding); no dependencies
    "calendar_v3": add_calendar_v3_features,
}

V3_FEATURE_COLUMNS_FULL: tuple[str, ...] = (
    # Regime
    "hurst_100",
    "hurst_200",
    "hurst_diff_100_50",
    "atr_pct_rank_200",
    "atr_pct_rank_500",
    "bb_width_pct_rank_100",
    "cusum_reset_count_200",
    # Tail risk
    "ret_skew_50",
    "ret_skew_100",
    "ret_skew_200",
    "ret_kurt_50",
    "ret_kurt_200",
    "range_realized_vol_50",
    "max_dd_window_50",
    # Efficient OHLC vol
    "parkinson_vol_20",
    "parkinson_gk_ratio_20",
    # Momentum acceleration
    "mom_accel_5_20",
    "mom_accel_20_100",
    "ema_spread_atr_20",
    "ret_autocorr_lag1_50",
    "ret_autocorr_lag5_50",
    # Volume microstructure
    "vwap_dev_20",
    "vwap_dev_50",
    "volume_mom_ratio_20",
    "volume_cv_50",
    "obv_slope_50",
    "hl_range_ratio_20",
    # Fracdiff — renamed from d04 to dstat (FracdiffStat auto-d* substitution)
    "fracdiff_logclose_dstat",
    "fracdiff_logvolume_dstat",
    # BTC cross-asset
    "btc_ret_3d",
    "btc_ret_7d",
    "btc_ret_14d",
    "btc_vol_14d",
    "sym_vs_btc_ret_7d",
)
"""34-feature full set from iter-v3/001 through iter-v3/006.

Preserved as a named constant so iter-v3/008+ can restore via reassignment:
    V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_FULL
"""

V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
    # -------------------------------------------------------------------------
    # iter-v3/064 PHASED MASS-EXPANSION #1: REVERT to 14-feature anchor + ADD adx_14.
    # = 15 features total.
    #
    # Rationale: iter-v3/063 mass expansion (14 → 46) at single-seed n_trials=35
    # EXPLORATION mode FAILED with SUSPICIOUS-OOS-DOMINANT + IS-COLLAPSE (Critic FINAL
    # `7cbc136`; diary `937f7d6`). IS Sharpe collapsed -1.38 from /060 anchor +0.83
    # to -0.55. Per amended `feedback_v3_mass_feature_expansion.md` (2026-05-14):
    # phased single-feature expansion at single-seed EXPLORATION is the path forward
    # for CYCLE-5 mass-feature expansion mandate.
    #
    # adx_14 selected as phased-mass-expansion #1 per:
    # - Highest /063 last-month importance at LDO (rank 5/46, gain 161.0)
    # - Moderate at BCH (rank 11/46, gain 42.3)
    # - Mid at TRX (rank 25/46, gain 19.3)
    # - In leaner 15-feature stack (per iter-v3/064 EDA SHA <eda_sha>):
    #   LDO rank 2/15 (gain 227), TRX rank 7/15 (gain 186), BCH rank 12/15 (gain 146)
    # - Off-the-shelf Wilder (1978) ADX trend-strength indicator; walk-forward-safe
    #   per /063 Critic Check 1 verified past-only at `technical_v3.py:71-167`
    # - Clean orthogonality to 14-feature anchor: max |IC|=0.162 with
    #   range_realized_vol_50 (per /064 EDA T3 + /063 IC matrix). No carve-out needed.
    # - ADF stationary across all 3 IS symbols (p < 1e-15)
    #
    # EDA-implementation parity gate (per /063 Critic Rec #2): V3_FEATURE_COLUMNS_TOP_N
    # is BIT-IDENTICAL to the 15-feature set declared in iter-v3/064 brief Section 3.
    # No silent additions or substitutions.
    # -------------------------------------------------------------------------
    # BASELINE_V3 14 features (anchor — order matches BASELINE_V3.md /059 spec):
    "max_dd_window_50",  # tail_risk [BASELINE_V3]
    "ema_spread_atr_20",  # momentum [BASELINE_V3]
    "ret_kurt_50",  # tail_risk [BASELINE_V3]
    "ret_skew_200",  # tail_risk [BASELINE_V3]
    "range_realized_vol_50",  # tail_risk [BASELINE_V3]
    "hurst_diff_100_50",  # regime [BASELINE_V3]
    "ret_kurt_200",  # tail_risk [BASELINE_V3]
    "hurst_100",  # regime [BASELINE_V3]
    "btc_ret_14d",  # cross_btc [BASELINE_V3]
    "ret_skew_50",  # tail_risk [BASELINE_V3]
    "vwap_dev_20",  # volume_micro [BASELINE_V3]
    "ret_autocorr_lag1_50",  # momentum [BASELINE_V3]
    "sym_vs_btc_ret_7d",  # cross_btc [BASELINE_V3]
    "regime_momentum_signed_5d",  # engineered [BASELINE_V3, /025 PROMISING]
    # -------------------------------------------------------------------------
    # iter-v3/082 (cycle-3 EXPLORATION #1) — funding-rate FEATURE FAMILY.
    # 14 -> 18 features. A NEW crypto-native feature family (Direction 1 of
    # briefs-v3/cycle3_plan.md). DIFFERENT axis from the PERMANENTLY-CLOSED
    # single funding_rate_zscore_30 (/019/023/024 — a mean-zero rolling z-score
    # discards sign + level + the price leg). These 4 encode the four funding
    # channels the 2023-2025 literature identifies (sign-persistence/crowding,
    # momentum, acceleration/carry-shock per BIS WP 1087, funding-price
    # divergence per CFB/the crowding-reversal literature). Brief
    # briefs-v3/iteration_v3-082/research_brief.md Section 3; EDA SHA 37d4da8.
    "funding_sign_persist_9",  # funding_family_v3 [iter-v3/082]
    "funding_momentum_3",  # funding_family_v3 [iter-v3/082]
    "funding_accel_3",  # funding_family_v3 [iter-v3/082]
    "funding_price_divergence_6",  # funding_family_v3 [iter-v3/082]
    # -------------------------------------------------------------------------
    # iter-v3/077 (cycle-2 EXPLORATION #7) REVERTS /076's range_efficiency_50 —
    # the feature set returns to the BASELINE_V3 /059/060 14-feature anchor.
    # /076 (NEW feature range_efficiency_50, the Kaufman path-efficiency math)
    # was SUSPICIOUS-OOS-DOMINANT (OOS/IS ratio 15.04; IS edge destroyed) and
    # NON-ADVANCING; the Kaufman path-efficiency axis is CLOSED across 2 data
    # points (/043 DISASTROUS + /076 SUSPICIOUS — BASELINE_V3.md Dead Ideas).
    # iter-v3/077 is a PASSIVE-DIAGNOSTIC iteration (conditional-orthogonality
    # report instrumentation; brief Section 3) — it adds NO feature and reverts
    # /076's so the diagnostic measures the canonical /060 anchor.
    # adx_14 REMOVED at /064 closeout (NEGATIVE per Critic `452fcf2`).
    # Cycle 1 #6+ pivots to NON-FEATURE axes per Critic /064 Rec #4.
    # -------------------------------------------------------------------------
    # REVERTED at iter-v3/064 (relative to iter-v3/063 46-feature set):
    # All 31 NON-baseline features from /063 REMOVED. The /063 mass-expansion
    # at single-seed n_trials=35 produced IS Sharpe collapse -1.38.
    # Removed features (in /063 order, with reason for non-re-addition at /064):
    #   ret_skew_100, obv_slope_50, btc_vol_14d, cusum_reset_count_200,
    #   ret_autocorr_lag5_50, fracdiff_logclose_dstat, volume_cv_50, hurst_200,
    #   fracdiff_d05_close, parkinson_gk_ratio_20, sym_vs_btc_vol_14d,
    #   kurt_ratio_50_200, volume_mom_ratio_20, bb_width_pct_rank_100,
    #   vol_transition_slope_20, btc_ret_7d, atr_pct_rank_500, atr_pct_rank_200,
    #   btc_ret_3d, ret_20d, mom_accel_20_100, trend_efficiency_signed,
    #   btc_funding_rate_zscore_30, funding_rate_zscore_30, vol_regime_x_momentum,
    #   cross_asset_divergence_norm, mom_accel_5_20, taker_buy_imbalance_20,
    #   sym_vs_btc_ret_3d, candle_dow_sin, candle_dow_cos, ret_1d, tbr_zscore_30
    # These features remain implemented in features_v3/ modules and parquets
    # (zero revert cost). They can be considered for phased-mass-expansion #2+
    # individually with full EDA backing per `feedback_v3_axis_selection_quant_discipline.md`.
    # -------------------------------------------------------------------------
    # BANNED features (MUST remain absent):
    #   vol_normalized_ret_5d  — /049 PATH C-clean (OOS Δ -3.15)
    #   hurst_drift_50_200     — /053 PATH D + Critic FINAL `c056354`
    #   regime_momentum_signed_3d — /052 PATH C-suspicious + Critic `34cc46f`
    #   efficiency_ratio_50    — /043 DISASTROUS NEGATIVE (IS -0.84 / OOS -0.90)
    #   vol_adj_autocorr       — /026 catastrophic IS collapse + /036 NEGATIVE
    #   vwap_dev_50            — Critic FINAL `a544621` Rec #1 (IC 0.875 with ema_spread_atr_20)
    # -------------------------------------------------------------------------
)
"""14-feature set — the BASELINE_V3 /059 anchor stack.

iter-v3/077 (cycle-2 EXPLORATION #7) REVERTS /076's range_efficiency_50; the
feature set returns to the BASELINE_V3 /059/060 14-feature anchor (unchanged
from the /028 spec).

History:
  /065+: 14-feature /060 anchor (adx_14 dropped at /064 NEGATIVE).
  /076 : range_efficiency_50 ADDED (15th) — EXPLORATION #6 axis;
         SUSPICIOUS-OOS-DOMINANT, NON-ADVANCING (Kaufman path-efficiency axis
         CLOSED across /043 + /076 — BASELINE_V3.md Dead Ideas).
  /077 : range_efficiency_50 REVERTED — back to the 14-feature anchor. /077 is
         a PASSIVE-DIAGNOSTIC iteration (conditional-orthogonality report
         instrumentation) and adds no feature.

The iter-v3/064 phased mass-expansion #1 (+adx_14, briefly 15 features) was
NEGATIVE; the runner pre-flight still asserts adx_14 ABSENT.
"""

# iter-v3/077: V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N (14-feature
# BASELINE_V3 /059/060 anchor — /076's range_efficiency_50 reverted).
V3_FEATURE_COLUMNS: tuple[str, ...] = V3_FEATURE_COLUMNS_TOP_N
"""Alias for V3_FEATURE_COLUMNS_TOP_N — the active feature set for all v3 models.

Points to the 14-feature BASELINE_V3 /059/060 anchor stack (iter-v3/077 reverted
/076's range_efficiency_50; /077 is a PASSIVE-DIAGNOSTIC iteration, no feature
change).
"""

DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
"""Default ATR multipliers for symbols not in V3_ATR_MULTIPLIERS_PER_SYMBOL.

iter-v3/070 CYCLE 1 CONFIRMATION CLOSEOUT: REVERTED (2.0, 1.5) → (2.0, 1.0).
Component A (/065 universal SL widening) was REJECTED at the /070 CONFIRMATION —
the IS-collapse + OOS-soar pattern persisted and amplified at multi-seed (IS Sharpe
collapsed -0.97; OOS/IS ratio 10.81 — regime exposure, not robust edge). Leaving
(2.0, 1.5) would mean cycle 2 silently inherits a CONFIRMATION-rejected axis, which
violates `feedback_no_cheating.md` and the anti-drift discipline. The canonical /059
baseline (BASELINE_V3.md) documents (atr_tp=2.0, atr_sl=1.0); the code now matches.
V3_ATR_MULTIPLIERS_PER_SYMBOL stays empty {} — universal value, no per-symbol overrides.
See diary-v3/iteration_v3-070.md Section 6 (Component A REJECT) + Section 7.

History:
  iter-v3/043: REVERTED from (1.5, 0.75) back to (2.0, 1.0) — iter-v3/042 Path C
  (IS collapse NEGATIVE: IS Sharpe -0.5941, TRX OOS -33 wpnl swing) mandate fires.
  Value (2.0, 1.0) first set at iter-v3/010; validated anchor through iter-v3/041.
  iter-v3/065: (2.0, 1.0) → (2.0, 1.5) — UNIVERSAL SL widening (Path D).
  iter-v3/066: (2.0, 1.5) → (2.0, 1.0) — REVERT for axis isolation (Path E0.8).
  iter-v3/067-069: (2.0, 1.0) — carry-forward (non-labeling axes).
  iter-v3/070: (2.0, 1.0) → (2.0, 1.5) — RE-APPLIED /065 Component A at CONFIRMATION.
  iter-v3/070 CLOSEOUT: (2.0, 1.5) → (2.0, 1.0) — Component A REJECTED; SL widening
  is regime exposure not edge. /059 canonical anchor value restored.
"""

V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    # iter-v3/074 — CYCLE 2 EXPLORATION #4: REVERTED to {} (empty).
    # The iter-v3/073 per-symbol triple-barrier asymmetry axis — BCH (2.0, 1.25),
    # LDO (1.5, 1.25) — classified SUSPICIOUS-OOS-DOMINANT (OOS/IS monthly Sharpe
    # ratio 6.85, the most extreme in v3 history; per-symbol SL widening is a
    # holding-time-extension axis loading the IS/OOS regime factor). The axis was
    # CLOSED at catalog level and did NOT advance to the cycle-2 CONFIRMATION.
    # Per `feedback_no_cheating.md` anti-drift discipline, /074 must not silently
    # inherit a catalog-closed axis — V3_ATR_MULTIPLIERS_PER_SYMBOL is reverted to
    # empty so all symbols use DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0), the canonical
    # /059 baseline labeling. /074's axis is the regime-conditional kill switch
    # (primitive 9), orthogonal to labeling. See diary-v3/iteration_v3-073.md.
    # History: {} (iter-v3/051-072) -> BCH/LDO (iter-v3/073) -> {} (iter-v3/074).
}
"""Per-symbol ATR multiplier overrides (iter-v3/032+).

Maps symbol → (atr_tp_multiplier, atr_sl_multiplier).
iter-v3/074: EMPTY — all symbols (BCH/LDO/TRX) fall back to
DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0). The iter-v3/073 per-symbol axis was
SUSPICIOUS-OOS-DOMINANT and is reverted here per anti-drift discipline.
"""


def atr_multipliers_for_symbol(symbol: str) -> tuple[float, float]:
    """Return per-symbol ATR multipliers, falling back to DEFAULT_ATR_MULTIPLIERS.

    Introduced in iter-v3/032 to support per-symbol labeling-layer heterogeneity.

    iter-v3/043: DEFAULT_ATR_MULTIPLIERS REVERTED to (2.0, 1.0). iter-v3/042's
    (1.5, 0.75) universal tightening caused IS collapse (IS Sharpe -0.5941; TRX
    OOS -33 wpnl swing) — Path C mandate fires. V3_ATR_MULTIPLIERS_PER_SYMBOL is
    empty — ALL symbols (BCH/LDO/TRX/ALGO) fall back to DEFAULT = (2.0, 1.0).
    Prior value (1.5, 0.75) was in effect only at iter-v3/042.
    Default (2.0, 1.0) first set at iter-v3/010; validated anchor through iter-v3/041.

    Callers pass the returned tuple to LightGbmStrategy as
    ``atr_tp_multiplier=tp, atr_sl_multiplier=sl``.
    """
    return V3_ATR_MULTIPLIERS_PER_SYMBOL.get(symbol, DEFAULT_ATR_MULTIPLIERS)


V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {}
"""Per-symbol feature overrides for v3 models (iter-v3/030+).

Maps symbol → tuple of feature column names to pass to LightGbmStrategy.
Symbols absent from this dict fall back to V3_FEATURE_COLUMNS_TOP_N.

iter-v3/030: populated with LDO → 7-feature top-7 subset (REDUCTION of 14-feature universal).
iter-v3/031: CLEARED (LDOUSDT dropped from V3_MODELS). Dict empty.
iter-v3/034: Dict empty. All symbols fall back to 15-feature V3_FEATURE_COLUMNS_TOP_N.
iter-v3/035: BCH entry ADDED as EXTENSION of universal list (14 + fracdiff_d05_close = 15).
             TRX/ALGO/LDO: 14-feature fallback (no fracdiff_d05_close).
iter-v3/036: TRX entry ADDED as EXTENSION of universal list (14 + vol_adj_autocorr = 15).
             BCH unchanged (15 features: 14 + fracdiff_d05_close).
             LDO/ALGO: 14-feature fallback (no vol_adj_autocorr).
             RESULT: NEGATIVE — TRX vol_adj_autocorr hurt TRX (~-15 OOS wpnl swing).
iter-v3/037: TRX entry REMOVED (iter-v3/036 NEGATIVE reverted). LDO entry ADDED as EXTENSION
             of universal list (14 + cross_asset_divergence_norm = 15). BCH unchanged.
             TRX/ALGO: 14-feature fallback (no cross_asset_divergence_norm, no vol_adj_autocorr).
             RESULT: NEGATIVE — LDO cross_asset_divergence_norm OOS swing ~-33. REVERTED.
iter-v3/038: LDO entry REMOVED (iter-v3/037 NEGATIVE reverted). ALGO entry ADDED as EXTENSION
             of universal list (14 + fracdiff_d05_close = 15). BCH unchanged.
             LDO/TRX: 14-feature fallback. BCH and ALGO both get fracdiff_d05_close (15 features).
             Scientific purpose: tests fracdiff SPECIFICITY (BCH-specific vs broadly useful).
             RESULT: NEGATIVE — ALGO does NOT benefit from fracdiff; BCH-SPECIFIC confirmed.
iter-v3/039: ALGO entry REMOVED (iter-v3/038 NEGATIVE reverted). Dict has 1 entry (BCHUSDT only).
             ALGO returns to 14-feature fallback. BCH unchanged (15 features: 14 + fracdiff).
             LDO/TRX/ALGO: 14-feature fallback. BCH is the ONLY per-symbol fracdiff beneficiary.
             CONFIRMATION of iter-v3/035 bundle — NO-MERGE: per-symbol customizations broke IS.
iter-v3/040: CLEARED (empty dict). Cycle 3 EXPLORATION #1 — REVERT all per-symbol feature
             overrides. BCH reverts to 14-feature V3_FEATURE_COLUMNS_TOP_N fallback (same as
             ALGO/LDO/TRX). Architecture (this dict + features_for_symbol helper) is KEPT;
             only the dict contents are emptied. Rationale: iter-v3/039 NO-MERGE — cumulative
             per-symbol customizations caused ~-0.55 IS Sharpe swing from iter-v3/029 anchor.
             iter-v3/040 verifies that clearing per-symbol customizations restores IS anchor.

Enforced by _verify_feature_columns in run_baseline_v3.py (iter-v3/064):
    len(V3_FEATURES_PER_SYMBOL) == 0  (empty — no per-symbol entries)
    "BCHUSDT" not in V3_FEATURES_PER_SYMBOL
    "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL
    "LDOUSDT" not in V3_FEATURES_PER_SYMBOL
    "TRXUSDT" not in V3_FEATURES_PER_SYMBOL
    features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N  (14 features — /060 anchor)
    "adx_14" not in V3_FEATURE_COLUMNS_TOP_N  (/064 phased-mass-expansion #1 NEGATIVE)
    "range_efficiency_50" not in V3_FEATURE_COLUMNS_TOP_N  (/076 SUSPICIOUS; reverted /077)
    "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N  (dead code; catastrophic at /026)
    "efficiency_ratio_50" not in V3_FEATURE_COLUMNS_TOP_N  (DISASTROUS NEGATIVE /043)
    "regime_momentum_signed_3d" not in V3_FEATURE_COLUMNS_TOP_N  (PARKED /053)
    "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N  (BASELINE_V3; mandate ACTIVE)
"""


def features_for_symbol(symbol: str) -> tuple[str, ...]:
    """Return per-symbol feature tuple, falling back to V3_FEATURE_COLUMNS_TOP_N.

    Introduced in iter-v3/030 to support per-symbol model heterogeneity.

    iter-v3/040 (EXPLORATION — cycle 3 #1 — REVERT all per-symbol customizations):
    - V3_FEATURES_PER_SYMBOL is EMPTY (cleared at iter-v3/040). All symbols fall back
      to V3_FEATURE_COLUMNS_TOP_N. No per-symbol feature overrides exist.

    iter-v3/077 (cycle-2 EXPLORATION #7 — PASSIVE-DIAGNOSTIC; REVERT /076's
    range_efficiency_50):
    - V3_FEATURES_PER_SYMBOL still EMPTY (0 entries).
    - BCHUSDT/LDOUSDT/TRXUSDT: each returns the 14-feature BASELINE_V3 /059/060
      anchor = V3_FEATURE_COLUMNS_TOP_N (fallback).
    - Any other symbol: same 14-feature fallback (universal).
    - /076 briefly added range_efficiency_50 (15th); reverted at /077 — the
      Kaufman path-efficiency axis is CLOSED (BASELINE_V3.md Dead Ideas).

    Callers MUST pass ``feature_columns=list(features_for_symbol(symbol))``
    to LightGbmStrategy/XgboostStrategy — never None, never empty, never the global default.
    This preserves the ``feedback_explicit_feature_columns.md`` invariant while
    enabling per-symbol feature-set discipline.
    """
    return V3_FEATURES_PER_SYMBOL.get(symbol, V3_FEATURE_COLUMNS_TOP_N)


V3_EXCLUDED_SYMBOLS: tuple[str, ...] = (
    # v1 traded
    "BTCUSDT",
    "ETHUSDT",
    "LINKUSDT",
    "LTCUSDT",
    "DOTUSDT",
    # historical reservation
    "BNBUSDT",
    # v2 traded
    "SOLUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "NEARUSDT",
    # v3 dropped per iter-v3/013 universe-axis EXPLORATION
    "MKRUSDT",
)
"""Symbols traded by v1 or v2, plus v3-dropped symbols. v3 runners MUST exclude at startup."""


def list_groups() -> list[str]:
    return sorted(GROUP_REGISTRY.keys())


def generate_features_v3(df: pd.DataFrame, groups: list[str] | None = None) -> pd.DataFrame:
    """Run the selected v3 feature groups on *df* and return the augmented frame."""
    if groups is None:
        groups = list(GROUP_REGISTRY.keys())
    for group_name in groups:
        fn = GROUP_REGISTRY[group_name]
        df = fn(df)
        df = df.copy()
    return df


def process_symbol_v3(
    symbol: str,
    interval: str,
    data_dir: str,
    output_dir: str,
    start_ms: int | None = None,
    end_ms: int | None = None,
) -> tuple[str, int, int]:
    """Load klines for *symbol*, run the full v3 feature pipeline, write parquet.

    Returns ``(symbol, n_rows, n_feature_columns)``.
    """
    path = csv_path(Path(data_dir), symbol, interval)
    ka = load_kline_array(path)
    if len(ka) == 0:
        return (symbol, 0, 0)

    if start_ms is not None or end_ms is not None:
        ka = ka.time_slice(start_ms, end_ms)
    if len(ka) == 0:
        return (symbol, 0, 0)

    df = ka.df.copy()
    df["symbol"] = symbol
    before_cols = set(df.columns)
    df = generate_features_v3(df, list(GROUP_REGISTRY.keys()))
    added = [c for c in df.columns if c not in before_cols]

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{symbol}_{interval}_features.parquet"
    df.to_parquet(out_path, index=False)

    return (symbol, len(df), len(added))


def run_features_v3(
    symbols: list[str],
    interval: str,
    data_dir: str,
    output_dir: str,
    start_ms: int | None = None,
    end_ms: int | None = None,
    workers: int = 1,
) -> list[tuple[str, int, int]]:
    """Batch generate v3 features across *symbols* with optional multiprocessing."""
    results: list[tuple[str, int, int]] = []
    if workers <= 1:
        for symbol in tqdm(symbols, desc="v3 features", unit="sym"):
            results.append(
                process_symbol_v3(symbol, interval, data_dir, output_dir, start_ms, end_ms)
            )
        return results

    with ProcessPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(process_symbol_v3, s, interval, data_dir, output_dir, start_ms, end_ms): s
            for s in symbols
        }
        for fut in tqdm(as_completed(futures), total=len(futures), desc="v3 features", unit="sym"):
            results.append(fut.result())
    return results


__all__ = [
    "DEFAULT_ATR_MULTIPLIERS",
    "GROUP_REGISTRY",
    "V3_ATR_MULTIPLIERS_PER_SYMBOL",
    "V3_EXCLUDED_SYMBOLS",
    "V3_FEATURE_COLUMNS",
    "V3_FEATURE_COLUMNS_FULL",
    "V3_FEATURE_COLUMNS_TOP_N",
    "V3_FEATURES_PER_SYMBOL",
    "V3_NON_FEATURE_COLUMNS",
    "add_btc_funding_v3_features",
    "add_calendar_v3_features",
    "add_engineered_v3_features",
    "add_funding_v3_features",
    "add_technical_v3_features",
    "atr_multipliers_for_symbol",
    "features_for_symbol",
    "generate_features_v3",
    "list_groups",
    "process_symbol_v3",
    "run_features_v3",
]
