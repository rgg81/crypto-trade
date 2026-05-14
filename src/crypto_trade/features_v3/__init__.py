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
from crypto_trade.features_v3.funding_v3 import add_btc_funding_v3_features, add_funding_v3_features
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
    # iter-v3/063 MASS FEATURE EXPANSION: 14 → 48 features.
    # EDA SHA: c833f48 (analysis/iteration_v3-063/).
    # Path B: 14 BASELINE_V3 mandatory + 34 promoted from parquet + 9 NEW.
    # Feature order: by single-LightGBM gain rank from T8_final_feature_set.csv.
    # IC pruning: greedy LDP-style; 22 dropped at |IC|>0.70 (non-carveout pairs).
    # ADF: 1 drop (candle_hour_sin — constant at 8h cadence).
    # Zero-gain: candle_hour_cos kept (non-zero gain; candle_hour_sin dropped).
    # All 14 BASELINE_V3 features preserved (marked [BASELINE_V3]).
    # 9 NEW features (need features_v3/ implementation; marked [NEW]).
    # -------------------------------------------------------------------------
    # tail_risk (7 features)
    "ret_skew_100",  # rank 1  gain 2536 — tail_risk (Conrad-Dittmar-Ghysels 2013)
    "max_dd_window_50",  # rank 4  gain 1884 — tail_risk [BASELINE_V3]
    "ret_skew_200",  # rank 6  gain 1800 — tail_risk [BASELINE_V3]
    "ret_skew_50",  # rank 11 gain 1452 — tail_risk [BASELINE_V3]
    "ret_kurt_200",  # rank 12 gain 1382 — tail_risk [BASELINE_V3]
    "ret_kurt_50",  # rank 27 gain 713  — tail_risk [BASELINE_V3]
    "range_realized_vol_50",  # rank 19 gain 953  — tail_risk [BASELINE_V3]
    # volume_micro (4 features)
    "obv_slope_50",  # rank 2  gain 1935 — volume_micro (Granville 1963)
    "volume_cv_50",  # rank 14 gain 1312 — volume_micro (Karpoff 1987)
    "volume_mom_ratio_20",  # rank 22 gain 783  — volume_micro (Lee-Swaminathan 2000)
    "vwap_dev_20",  # rank 53 gain 155  — volume_micro [BASELINE_V3]
    # cross_asset (7 features)
    "btc_vol_14d",  # rank 3  gain 1885 — cross_asset (Liu-Tsyvinski 2021)
    "btc_ret_14d",  # rank 9  gain 1484 — cross_asset [BASELINE_V3]
    "sym_vs_btc_vol_14d",  # rank 18 gain 1108 — cross_asset [NEW] (vol divergence)
    "btc_ret_7d",  # rank 25 gain 758  — cross_asset (Liu-Tsyvinski 2021)
    "btc_ret_3d",  # rank 31 gain 593  — cross_asset (Liu-Tsyvinski 2021)
    "sym_vs_btc_ret_7d",  # rank 32 gain 556  — cross_asset [BASELINE_V3]
    "sym_vs_btc_ret_3d",  # rank 52 gain 180  — cross_asset [NEW] (Asness 1995)
    # regime (6 features)
    "cusum_reset_count_200",  # rank 5  gain 1882 — regime (Page 1954; LdP AFML Ch.17)
    "hurst_200",  # rank 15 gain 1281 — regime (Hurst 1951)
    "bb_width_pct_rank_100",  # rank 23 gain 774  — regime (Bollinger 1992)
    "atr_pct_rank_500",  # rank 26 gain 741  — regime (Wilder 1978)
    "hurst_100",  # rank 30 gain 622  — regime [BASELINE_V3]
    "hurst_diff_100_50",  # rank 35 gain 509  — regime [BASELINE_V3]
    # momentum (5 features)
    "ret_autocorr_lag1_50",  # rank 7  gain 1771 — momentum [BASELINE_V3]
    "ret_autocorr_lag5_50",  # rank 8  gain 1523 — momentum (Lo-MacKinlay 1988)
    "ema_spread_atr_20",  # rank 29 gain 692  — momentum [BASELINE_V3]
    "mom_accel_20_100",  # rank 39 gain 426  — momentum (Carver 2019)
    "mom_accel_5_20",  # rank 51 gain 187  — momentum (Carver 2019)
    # fracdiff (2 features)
    "fracdiff_logclose_dstat",  # rank 10 gain 1458 — fracdiff (LdP AFML Ch.5)
    "fracdiff_d05_close",  # rank 16 gain 1139 (was parked; re-evaluated under post-fix WF)
    # microstructure (4 features)
    "taker_buy_imbalance_20",  # rank 13 gain 1364 — microstructure [NEW] (Hasbrouck 1991)
    "parkinson_gk_ratio_20",  # rank 17 gain 1140 — vol_estimator (Sinclair 2013)
    "vol_transition_slope_20",  # rank 24 gain 773  — microstructure (v2 suite)
    "tbr_zscore_30",  # rank 61 gain 96   — microstructure (Brogaard et al. 2014)
    # technical (1 feature)
    "adx_14",  # rank 20 gain 889  — technical [NEW] (Wilder 1978)
    # vol_estimator / regime
    "atr_pct_rank_200",  # promoted from parquet — regime (Wilder ATR pct rank)
    # engineered (4 features — vol_normalized_ret_5d + hurst_drift_50_200 removed
    # at /063 pre-flight fix per orchestrator 2026-05-14: both historically banned
    # per /049 PATH C-clean (vol_normalized_ret_5d OOS Δ -3.15) and /053 PATH D
    # (hurst_drift_50_200 Critic FINAL c056354). Final count: 46 features.)
    "trend_efficiency_signed",  # rank 36 gain 487  — engineered [NEW] (Kaufman signed)
    "vol_regime_x_momentum",  # rank 40 gain 406  — engineered [NEW] (Asness × Wilder)
    "cross_asset_divergence_norm",  # rank 44 gain 374  — engineered (iter-v3/027)
    "regime_momentum_signed_5d",  # rank 63 gain 87  — engineered [BASELINE_V3]
    # funding (2 features)
    "btc_funding_rate_zscore_30",  # rank 41 gain 402 — funding (BIS WP 1087 2025)
    "funding_rate_zscore_30",  # rank 42 gain 395 — funding (Ackerer-Hugonnier 2024)
    # calendar (2 features)
    "candle_dow_sin",  # rank 57 gain 117  — calendar [NEW] (Heston-Sadka 2008)
    "candle_dow_cos",  # rank 69 gain 33   — calendar [NEW] (Heston-Sadka 2008)
    # returns (1 feature)
    "ret_1d",  # rank 59 gain 109  — returns [NEW] (Cont 2001; basic momentum)
    # -------------------------------------------------------------------------
    # DROPPED from V3_FEATURE_COLUMNS_TOP_N at iter-v3/063 relative to prior iterations:
    # (all previously parked/absent features not included above for various reasons)
    # The following were in parquet but NOT included due to IC pruning:
    #   parkinson_vol_20, parkinson_vol_50 (IC 1.000 with range_realized_vol_50)
    #   williams_r_14, stoch_k_14 (IC 1.000 algebraic identity)
    #   garman_klass_vol_20 (IC 0.993 with parkinson_vol_20)
    #   taker_buy_zscore_50 (IC 0.982 with tbr_zscore_30)
    #   bb_pctb_20 (IC 0.964 with cci_20)
    #   cci_20 (IC 0.942 with vwap_dev_20)
    #   close_pos_in_range_20 (IC 0.939 with vwap_dev_20)
    #   rsi_28, vwap_dev_50 (IC 0.936 with vwap_dev_50/rsi)
    #   fracdiff_logvolume_dstat (IC 0.90+ with fracdiff_logclose_dstat)
    #   hl_range_ratio_20, candle_efficiency_20, vol_return_divergence_30
    #   kurt_ratio_50_200 (covered by ret_kurt_50/200 direct measures)
    # ADF FAIL (1 feature): candle_hour_sin (constant at 8h cadence)
    # ZERO-GAIN (1 feature): candle_hour_cos (gain=0 in T5 preview, BUT kept for
    #   cyclic-pair completeness with candle_dow_sin — the DOW pair is RETAINED)
    # Note: candle_hour_cos gain=0 was for the HOUR encoding (not DOW).
    # -------------------------------------------------------------------------
    # BASELINE_V3 mandate: ALL 14 must be present. Count: 14 ✓
    #   max_dd_window_50, ret_skew_200, ret_skew_50, ret_kurt_200, ret_kurt_50,
    #   range_realized_vol_50, vwap_dev_20, btc_ret_14d, sym_vs_btc_ret_7d,
    #   ret_autocorr_lag1_50, ema_spread_atr_20, hurst_100, hurst_diff_100_50,
    #   regime_momentum_signed_5d
    # PREVIOUSLY-CLOSED features RE-EVALUATED per /063 mass-expansion mandate:
    #   funding_rate_zscore_30 (CLOSED /024): re-included under post-WF-fix landscape
    #   btc_funding_rate_zscore_30 (CLOSED /025): same re-evaluation rationale
    #   tbr_zscore_30 (DROPPED /016): same re-evaluation rationale
    #   cross_asset_divergence_norm (dead code /028): re-included (IC carve-out valid)
    #   fracdiff_d05_close (PARKED /052): re-included (post-WF-fix re-evaluation)
    #   vol_normalized_ret_5d (DROPPED /049): re-included (mass-expansion context)
    #   hurst_drift_50_200 (PARKED /053): re-included (non-zero importance in T5)
    # These re-evaluations are documented in brief Section 3 adversarial flags.
    # -------------------------------------------------------------------------
)
"""48-feature set (iter-v3/063 MASS FEATURE EXPANSION: 14 → 48).

14 BASELINE_V3 features + 34 promoted from parquet + 9 NEW implementations.
EDA SHA: c833f48 (analysis/iteration_v3-063/T8_final_feature_set.csv).
Path B: maximum orthogonal set at IC<0.70 preserving all BASELINE_V3 features.
User-approved 48 < 50 mandate deviation (methodology > strict count per LDP IC-pruning).
"""

# iter-v3/063: V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N (48-feature mass expansion).
V3_FEATURE_COLUMNS: tuple[str, ...] = V3_FEATURE_COLUMNS_TOP_N
"""Alias for V3_FEATURE_COLUMNS_TOP_N — the active feature set for all v3 models.

iter-v3/063: points to the 48-feature mass-expansion set (was 14 features through /062).
"""

DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
"""Default ATR multipliers for symbols not in V3_ATR_MULTIPLIERS_PER_SYMBOL.

iter-v3/043: REVERTED from (1.5, 0.75) back to (2.0, 1.0) — iter-v3/042 Path C
(IS collapse NEGATIVE: IS Sharpe -0.5941, TRX OOS -33 wpnl swing) mandate fires.
V3_ATR_MULTIPLIERS_PER_SYMBOL is empty, so all 4 symbols (BCH/LDO/TRX/ALGO) use
this default universally via fallback.
Value (2.0, 1.0) first set at iter-v3/010; validated anchor through iter-v3/041.
Per briefs-v3/iteration_v3-043/research_brief.md Section 3 Sub-fix 1.
"""

V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    # iter-v3/051: REVERT to empty dict per system-level rule
    # `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10.
    # All 3 symbols (BCH/LDO/TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
    # History: {} (iter-v3/040 cycle 3 REVERT) → entries added/removed iter-v3/044-047
    #   → {} (iter-v3/051 system-level REVERT; current state at iter-v3/063).
}
"""Per-symbol ATR multiplier overrides (iter-v3/032+).

Maps symbol → (atr_tp_multiplier, atr_sl_multiplier).
Empty at iter-v3/063: all symbols fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
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

Enforced by _verify_feature_columns in run_baseline_v3.py (iter-v3/063):
    len(V3_FEATURES_PER_SYMBOL) == 0  (empty — no per-symbol entries)
    "BCHUSDT" not in V3_FEATURES_PER_SYMBOL
    "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL
    "LDOUSDT" not in V3_FEATURES_PER_SYMBOL
    "TRXUSDT" not in V3_FEATURES_PER_SYMBOL
    features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N  (48 features — MASS EXPANSION)
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
      to V3_FEATURE_COLUMNS_TOP_N (14 features). No per-symbol feature overrides exist.
    - BCHUSDT: returns 14 features = V3_FEATURE_COLUMNS_TOP_N (fallback; REVERTED from
      iter-v3/035-039 BCH-only fracdiff per-symbol entry; fracdiff_d05_close ABSENT)
    - ALGOUSDT: returns 14 features = V3_FEATURE_COLUMNS_TOP_N (fallback; unchanged)
    - LDOUSDT: returns 14 features = V3_FEATURE_COLUMNS_TOP_N (fallback; unchanged)
    - TRXUSDT: returns 14 features = V3_FEATURE_COLUMNS_TOP_N (fallback; unchanged)
    - Any other symbol: fallback to 48-feature universal set (iter-v3/063 MASS EXPANSION)

    V3_FEATURES_PER_SYMBOL is empty at iter-v3/063 (0 entries).
    All 3 symbols (BCH/LDO/TRX) use the 48-feature universal fallback at iter-v3/063.
    iter-v3/063 MASS FEATURE EXPANSION: 14 → 48 features (path B per EDA SHA c833f48).
    14 BASELINE_V3 features preserved + 34 promoted from parquet + 9 NEW implementations.

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
