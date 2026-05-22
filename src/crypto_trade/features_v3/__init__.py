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

Groups in the v3 registry (BASELINE_V3 /121-MINIMAL — 2026-05-22):
-----------------------------------------------------------------
Only feature groups that produce a column in ``V3_FEATURE_COLUMNS_TOP_N``
(the 14-feature /121 baseline) are registered. ``microstructure_v3`` is
also kept because ``engineered_v3.compute_ret5d_signed_tbi`` reads
``taker_buy_imbalance_20`` from it during dispatch (museum call retained
for parity with /121's canonical feature parquet).

- ``regime``            — hurst_100, hurst_diff_100_50
- ``tail_risk``         — max_dd_window_50, ret_skew_50/200, ret_kurt_50/200,
                          range_realized_vol_50
- ``momentum_accel``    — ema_spread_atr_20, ret_autocorr_lag1_50
- ``volume_micro``      — vwap_dev_20
- ``cross_btc``         — btc_ret_14d, sym_vs_btc_ret_7d
                          (requires BTCUSDT + ETHUSDT 8h klines)
- ``microstructure_v3`` — taker_buy_imbalance_20 (dependency of engineered_v3)
- ``engineered_v3``     — regime_momentum_signed_5d (composed)

Groups removed from the registry on 2026-05-22 because their output is
not in ``V3_FEATURE_COLUMNS_TOP_N`` AND they require external data sources
that the /121 baseline does not need:
  - ``basis_v3`` (needed ``data/spot/<SYM>/8h.csv``)
  - ``funding_v3``, ``btc_funding_v3``, ``funding_family_v3``,
    ``funding_regime_momentum_v3`` (needed ``data/funding_rates/<SYM>.csv``)
  - ``multifreq_v3_24h`` (needed ``data/features_v3_24h/<SYM>_24h_features.parquet``)
  - ``price_efficient_vol``, ``fracdiff``, ``technical_v3``,
    ``calendar_v3``, ``multifreq_v3`` (produced columns dropped from
    V3_FEATURE_COLUMNS_TOP_N at various closeouts; no /121 dependency)

The module files are RETAINED as research museum code (analysis/* scripts
in past iteration directories reference them). To re-add a group, restore
its import + GROUP_REGISTRY entry in a future iteration that brings the
feature back into V3_FEATURE_COLUMNS_TOP_N.
"""

from __future__ import annotations

from collections.abc import Callable
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# /121-MINIMAL imports — only modules registered in GROUP_REGISTRY below.
# Removed modules (basis_v3, calendar_v3, fracdiff_v3, funding_v3,
# multifreq_v3, price_efficient_vol_v3, technical_v3, formulaic_v3,
# engineered_v3.add_funding_regime_momentum_v3_features) are RETAINED
# on disk as research museum code but NOT imported at runtime.
from crypto_trade.features_v3.cross_btc_v3 import add_cross_btc_v3_features
from crypto_trade.features_v3.engineered_v3 import add_engineered_v3_features
from crypto_trade.features_v3.microstructure_v3 import add_microstructure_v3_features
from crypto_trade.features_v3.momentum_accel_v3 import add_momentum_accel_v3_features
from crypto_trade.features_v3.regime_v3 import add_regime_v3_features
from crypto_trade.features_v3.tail_risk_v3 import add_tail_risk_v3_features
from crypto_trade.features_v3.volume_micro_v3 import add_volume_micro_v3_features
from crypto_trade.kline_array import load_kline_array
from crypto_trade.storage import csv_path

GROUP_REGISTRY: dict[str, Callable[[pd.DataFrame], pd.DataFrame]] = {
    # /121-MINIMAL registry — only groups whose output appears in
    # V3_FEATURE_COLUMNS_TOP_N, plus dependencies. See module docstring for
    # the full list of groups removed 2026-05-22 and the rationale.
    #
    # Order is significant: each group may read columns added by earlier
    # groups (e.g. engineered_v3 consumes hurst_100 from regime,
    # range_realized_vol_50 from tail_risk, and taker_buy_imbalance_20 from
    # microstructure_v3 via compute_ret5d_signed_tbi).
    "regime": add_regime_v3_features,
    "tail_risk": add_tail_risk_v3_features,
    "momentum_accel": add_momentum_accel_v3_features,
    "volume_micro": add_volume_micro_v3_features,
    "cross_btc": add_cross_btc_v3_features,
    "microstructure_v3": add_microstructure_v3_features,
    "engineered_v3": add_engineered_v3_features,
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
    # iter-v3/127: d24_ret_autocorr_lag1_50 REMOVED — /126 NEGATIVE-catastrophic closeout.
    # EDA methodology FALSIFIED at 3-occurrence pattern (/122 eth_ret_3d INERT, /123
    # eth_vs_sym_rv_50 NEGATIVE-catastrophic, /126 d24_ret_autocorr_lag1_50 NEGATIVE-catastrophic).
    # Walk-forward production disagreed with 5-fold AUC EDA prediction 3/3 times.
    # d24_ret_autocorr_lag1_50 joins the ABSENT-assertion ban (runner pre-flight verified).
    # The multifreq_v3_24h infrastructure (multifreq_v3.py, data/features_v3_24h/) is RETAINED
    # as museum code — function NOT deleted, GROUP_REGISTRY entry remains for future use.
    # V3_FEATURE_COLUMNS_TOP_N reverts to /121-canonical 14-feature anchor.
    # iter-v3/126 cycle-7 EXPLORATION #5 reference: EDA SHA dd9fc2d (ARCHIVED).
    # eth_vs_sym_rv_50 REMOVED at iter-v3/124 — /123 NEGATIVE-catastrophic closeout.
    # cycle-7 cross-asset OHLCV axis CLOSED at 6th consecutive failure (/082/085/086/119/122/123).
    # eth_vs_sym_rv_50 code in cross_btc_v3.py is MUSEUM (not deleted; not in columns).
    # eth_ret_3d (iter-v3/122 cycle-7 EXPLORATION axis-1) REMOVED — /122 NEGATIVE-INERT
    # (Critic FINAL `9e0eeb6`: IC=0.5613 with vwap_dev_20; importance rank 11-15/15 all syms).
    # _load_eth_v3_features() infrastructure is RETAINED (museum; revived if eth features return).
    # ret5d_signed_tbi REMOVED at iter-v3/121-METHODOLOGY — Component B REVERTED.
    # /119 added this as 15th feature; /120 CONFIRMATION-NO-MERGE (F3 sister-redistribution
    # + F4 IS regime-cost fired). Per /120 F3-DROP binding pre-commitment + diary §6 Q4:
    # Component B DROPPED; V3_FEATURE_COLUMNS_TOP_N reverts to /059 canonical 14-feature stack.
    # compute_ret5d_signed_tbi REMAINS in engineered_v3.py (code-museum value per /118//119
    # precedent — function RETAINED, export in __all__ RETAINED, call-site RETAINED at line 1055).
    # DO NOT add ret5d_signed_tbi back to this tuple without a new EXPLORATION brief.
    # -------------------------------------------------------------------------
    # iter-v3/087 (cycle-3 EXPLORATION #6) REVERTS /086's perp-spot BASIS FEATURE
    # FAMILY — V3_FEATURE_COLUMNS_TOP_N returns 17 -> 14, the BASELINE_V3 /059
    # anchor stack. /086 (the 3-member basis family basis_zscore_30 /
    # basis_momentum_3 / basis_extreme_flag) was INERT and NON-ADVANCING: the
    # family ranked 15/16/17 of 17 by importance (combined share 0.04265, a
    # 2.15x gap below the weakest anchor regime_momentum_signed_5d). Per
    # `feedback_v3_inert_features_at_higher_budget.md` an INERT feature family
    # must NOT be carried forward and must NOT be retested at higher budget. The
    # /086 basis feed is the 7th non-OHLCV crypto-native feature family v3 has
    # tried — ALL 7 INERT-by-importance (the 7-FEED STRUCTURAL VERDICT) — so
    # /087+ pivots away from feature families entirely (Direction 2: WHOLESALE
    # universe-breadth expansion). This revert is the established "mandatory
    # secondary baseline-restore edit" pattern (cf. /083 reverting /082's funding
    # family, /077 reverting /076's range_efficiency_50) — it restores the
    # canonical 14-feature anchor so the SOLE /087 axis is the V3_MODELS 3->6
    # WHOLESALE expansion. The fetch-spot subcommand, basis_v3.py, and the
    # data/spot/ cache are RETAINED as reusable infrastructure at zero revert
    # cost; only the 3 basis feature columns are dropped. basis_zscore_30 /
    # basis_momentum_3 / basis_extreme_flag join the runner ABSENT-assertion
    # ban (the funding_regime_momentum_5d pattern).
    # -------------------------------------------------------------------------
    # iter-v3/083 (cycle-3 EXPLORATION #2) REVERTS /082's funding-rate FEATURE
    # FAMILY — V3_FEATURE_COLUMNS_TOP_N returns 18 -> 14, the BASELINE_V3 /059
    # anchor stack. /082 (the 4-member funding family funding_sign_persist_9 /
    # funding_momentum_3 / funding_accel_3 / funding_price_divergence_6) was
    # SUSPICIOUS-OOS-DOMINANT and NON-ADVANCING: the family ranked bottom-4/18 by
    # importance (combined 9.90%, below the 5.56% uniform-parity baseline). Per
    # `feedback_v3_inert_features_at_higher_budget.md` an INERT feature family
    # must NOT be carried forward and must NOT be retested at higher budget. The
    # v3 funding axis is CLOSED at 4 data points (/019/023/024/082). This revert
    # is the established "mandatory secondary edit" pattern (cf. /077 reverting
    # /076's range_efficiency_50, /079 reverting /078's ADA swap) — it restores
    # the canonical baseline so iter-v3/083's SOLE declared delta vs /059 is the
    # universe expansion. `compute_funding_family` (funding_v3.py) and the
    # `funding_family_v3` GROUP_REGISTRY entry are left as harmless unreferenced
    # infrastructure at zero revert cost. The funding_rate_zscore_30 /
    # btc_funding_rate_zscore_30 literal-name bans stay intact.
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
    # iter-v3/102 (cycle-5 EXPLORATION #2) REVERTS: WorldQuant Alpha#32 DROPPED.
    # alpha032 collapsed IS monthly Sharpe to +0.3993 (fired F2 falsifier IS < +0.60).
    # OOS +1.55 confirmed overfitting/regime-luck by Critic (not look-ahead).
    # Per `feedback_v3_inert_features_at_higher_budget.md` pattern: NO-MERGE axes
    # do not carry forward. V3_FEATURE_COLUMNS_TOP_N returns 15 → 14 (the /059 anchor).
    # formulaic_v3.py + test_formulaic_v3.py RETAINED as reusable infrastructure.
    # alpha032 joins the runner ABSENT-assertion ban (see run_baseline_v3.py).
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
    # iter-v3/114 (cycle-6 EXPLORATION #5): REVERT the /113 multi-frequency daily
    # features (d_ret_5d, d_ret_10d, d_trend_slope_10, d_realvol_10,
    # d_realvol_ratio, d_atr_pctrank_60, d_efficiency_10, d_close_pos_20) —
    # mandatory /113-closeout housekeeping (Critic /113 Recommendation 2).
    # /113 was NEGATIVE (INERT). V3_FEATURE_COLUMNS_TOP_N returns 22 → 14,
    # restoring the /059-canonical BASELINE_V3 14-feature stack.
    # The multifreq_v3 module + its GROUP_REGISTRY registration are RETAINED as
    # dormant infrastructure (zero revert cost — the established v3 dead-code pattern).
    # The 8 d_* features join the runner ABSENT-assertion ban below.
    # -------------------------------------------------------------------------
    # BANNED features (MUST remain absent):
    #   vol_normalized_ret_5d  — /049 PATH C-clean (OOS Δ -3.15)
    #   hurst_drift_50_200     — /053 PATH D + Critic FINAL `c056354`
    #   regime_momentum_signed_3d — /052 PATH C-suspicious + Critic `34cc46f`
    #   efficiency_ratio_50    — /043 DISASTROUS NEGATIVE (IS -0.84 / OOS -0.90)
    #   vol_adj_autocorr       — /026 catastrophic IS collapse + /036 NEGATIVE
    #   vwap_dev_50            — Critic FINAL `a544621` Rec #1 (IC 0.875 with ema_spread_atr_20)
    #   funding_regime_momentum_5d — /085 INERT-by-importance (rank 13/14/15-of-15)
    #                                + SUSPICIOUS (trade-selection sub-channel)
    #   basis_zscore_30        — /086 INERT-by-importance (rank 15/17)
    #   basis_momentum_3       — /086 INERT-by-importance (rank 16/17)
    #   basis_extreme_flag     — /086 INERT-by-importance (rank 17/17)
    #   alpha032               — /102 NEGATIVE (IS collapsed +0.3993; F2 falsifier fired)
    #   ema_signed_volregime   — /118 NEGATIVE catastrophic (IS Δ -0.4543; broader
    #                            `value × sign(vol-regime-classifier)` Category-2
    #                            lineage CLOSED at single-seed budget; Critic FINAL `80caafd`
    #                            + /118 closeout Critic Rec 3). Function STAYS in
    #                            engineered_v3.py for code-museum value; MUST NOT appear
    #                            in V3_FEATURE_COLUMNS_TOP_N.
    # -------------------------------------------------------------------------
)
"""15-feature set — BASELINE_V3 /059/060 canonical anchor + iter-v3/126 24h multi-frequency.

iter-v3/126: d24_ret_autocorr_lag1_50 ADDED as 15th feature (cycle-7 EXPLORATION axis-5).
24h-cadence 1-bar lag autocorrelation of log returns over 50 daily bars. Sourced from
data/features_v3_24h/<SYM>_24h_features.parquet offset_id=0. Causally merged onto 8h
decision grid via merge_asof(direction='backward'). EDA SHA dd9fc2d. Count: 14 → 15.

iter-v3/123: eth_vs_sym_rv_50 ADDED as 15th feature (cycle-7 EXPLORATION axis-2).
ETH-vs-symbol 50-bar realized-vol regime ratio = eth_rv_50 / (sym_rv_50 + EPS).
Past-only: rolling(50, min_periods=50).std() of 1-bar log returns (ETH and symbol).
Pairwise IC: 0.069 with vwap_dev_20; 0.021 with regime_momentum_signed_5d — 8-26×
cleaner than /122's eth_ret_3d (which had IC 0.56/0.53 with those same anchors).
ADF: p<0.01 on all 3 symbols. EDA SHA `dbc2993`. Replaces eth_ret_3d (/122 NEGATIVE-INERT).
Count: 14 → 15.

iter-v3/122: eth_ret_3d ADDED (15th) — cycle-7 EXPLORATION axis-1. NEGATIVE-INERT
(Critic FINAL `9e0eeb6`: IC=0.5613 with vwap_dev_20, IC=0.5280 with
regime_momentum_signed_5d — substantially spanned by 2 incumbents). REMOVED at /123.
eth_ret_3d joins the runner ABSENT-assertion ban (same pattern as /082 funding family,
/086 basis family, /064 adx_14). _load_eth_v3_features() infrastructure RETAINED
(needed by eth_vs_sym_rv_50's eth_rv_50 intermediate computation).

iter-v3/121-METHODOLOGY: Component B (ret5d_signed_tbi, /119's 15th feature) DROPPED.
V3_FEATURE_COLUMNS_TOP_N reverts from 15 → 14 (/059 canonical 14-feature stack).
Per /120 F3-DROP binding pre-commitment + diary §6 Q4 + Critic FINAL `a49dd17`.

History:
  /065+: 14-feature /060 anchor (adx_14 dropped at /064 NEGATIVE).
  /076 : range_efficiency_50 ADDED (15th) — EXPLORATION #6 axis;
         SUSPICIOUS-OOS-DOMINANT, NON-ADVANCING (Kaufman path-efficiency axis
         CLOSED across /043 + /076 — BASELINE_V3.md Dead Ideas).
  /077 : range_efficiency_50 REVERTED — back to the 14-feature anchor.
  /085 : funding_regime_momentum_5d ADDED (15th) — cycle-3 EXPLORATION #4 axis;
         INERT-by-importance + SUSPICIOUS (trade-selection sub-channel).
  /086 : funding_regime_momentum_5d DROPPED (Critic /085 Rec #1; an INERT
         feature is not carried forward). The 3-feature perp-spot basis family
         ADDED (15th/16th/17th) — cycle-3 EXPLORATION #5 axis, a NEW data feed.
         Verdict INERT (the 7th INERT crypto-native feed — the 7-FEED
         STRUCTURAL VERDICT).
  /087 : the 3 basis features DROPPED (Critic /086 Rec #3; an INERT feature
         family is not carried forward) — back to the 14-feature /059 anchor.
         The /087 axis is the WHOLESALE V3_MODELS 3 -> 6 expansion.
  /088-101: various non-feature axes (cross-sectional re-architecture, BCH signal
         filter, etc.) — V3_FEATURE_COLUMNS_TOP_N stayed at 14.
  /102 : alpha032 ADDED (15th) — cycle-5 EXPLORATION #2 axis;
         NEGATIVE (IS collapsed to +0.3993, fired F2 falsifier IS < +0.60);
         OOS +1.55 confirmed overfitting/regime-luck. REVERTED at /102 closeout.
         formulaic_v3.py + test_formulaic_v3.py RETAINED as infrastructure.
  /113 : 8 coarser-frequency (1d daily) features ADDED (15th–22nd) — cycle-6
         EXPLORATION #4 axis. Features: d_ret_5d, d_ret_10d, d_trend_slope_10,
         d_realvol_10, d_realvol_ratio, d_atr_pctrank_60, d_efficiency_10,
         d_close_pos_20. No new data fetch. EDA SHA ebd84e2. Count: 14 → 22.
         NEGATIVE (INERT). REVERTED at /114 closeout housekeeping.
         multifreq_v3 module RETAINED as dormant infrastructure.
  /114 : 8 d_* daily features DROPPED (mandatory /113-closeout housekeeping;
         Critic /113 Recommendation 2; /113 NEGATIVE-INERT). V3_FEATURE_COLUMNS_TOP_N
         returns 22 → 14 (the /059-canonical BASELINE_V3 14-feature stack). The
         /114 sole axis is the LDO-realvol kill_LOW gate (primitive 9 variant).
  /118 : ema_signed_volregime ADDED (15th) — cycle-6 EXPLORATION #9 axis.
         Category-2 composed feature: ema_spread_atr_20 × sign(range_realized_vol_50
         − rolling_median_200). Vol-regime-conditioned momentum at ~67-day
         rolling-median timescale — slower than /025's ~33-day Hurst regime.
         T9 POOLED multivariate-lift +0.0081 > 0.005 gate; importance rank 8-10/15,
         gain 38-63% across all 3 symbols. EDA SHA `60a45e8`. /025 PROMISING lineage.
         Count: 14 → 15. NEGATIVE catastrophic (IS Δ -0.4543); `value ×
         sign(vol-regime-classifier)` Category-2 lineage CLOSED at /118 closeout.
         REVERTED at /119 (Critic /118 Rec 3; function retained for code-museum value).
  /119 : ema_signed_volregime REMOVED (mandatory /118-closeout housekeeping) AND
         ret5d_signed_tbi ADDED (15th) — cycle-6 EXPLORATION #10 (FINAL) axis.
         Category-2 composed feature: ret_5d × sign(taker_buy_imbalance_20).
         Order-flow-regime-conditioned momentum at ~7-day microstructure timescale
         (20-bar taker-buy imbalance window). Structurally orthogonal to /025
         Hurst regime and /118 vol regime. T7 POOLED multivariate-lift +0.0083
         (broad-based: BCH +0.0057 / LDO +0.0123 / TRX +0.0053; all positive).
         T9 SSC-RISK gate: 1.48× < 2.0 (sole candidate clearing the new gate).
         EDA SHA `7aa5cc5`. Net count: 15 → 15 (C3 → C6 swap).
  /121 : ret5d_signed_tbi REMOVED (Component B DROPPED per /120 F3-DROP binding
         pre-commitment + diary §6 Q4 + Critic FINAL `a49dd17`). V3_FEATURE_COLUMNS_TOP_N
         reverts 15 → 14 (the /059 canonical BASELINE_V3 anchor).
         compute_ret5d_signed_tbi RETAINED in engineered_v3.py (code-museum value).
         /121-METHODOLOGY isolates Component A (/116 no_confirm) at 10-seed CONFIRMATION.
  /122 : eth_ret_3d ADDED (15th) — cycle-7 EXPLORATION axis-1. NEGATIVE-INERT.
         REMOVED at /123 — eth_vs_sym_rv_50 replaces it per /122 Critic Rec 1.
  /123 : eth_vs_sym_rv_50 ADDED (15th) — cycle-7 EXPLORATION axis-2. See top.

The iter-v3/064 phased mass-expansion #1 (+adx_14, briefly 15 features) was
NEGATIVE; the runner pre-flight still asserts adx_14 ABSENT.
"""

# iter-v3/127: V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N (14 features — REVERTED).
# d24_ret_autocorr_lag1_50 REMOVED (/126 NEGATIVE-catastrophic; EDA methodology FALSIFIED).
# V3_MODELS BCH/LDO/TRX UNCHANGED from /121 (reverted at /126; verified PASS).
V3_FEATURE_COLUMNS: tuple[str, ...] = V3_FEATURE_COLUMNS_TOP_N
"""Alias for V3_FEATURE_COLUMNS_TOP_N — the active feature set for all v3 models.

Points to the 14-feature /121-canonical anchor at iter-v3/127:
  14-feature BASELINE_V3 /059/060/121 canonical anchor.
  d24_ret_autocorr_lag1_50 (/126 NEGATIVE-catastrophic) ABSENT.
  eth_vs_sym_rv_50 (/123 NEGATIVE-catastrophic) ABSENT. eth_ret_3d (/122 INERT) ABSENT.
  Component A (/116 no_confirm) ENABLED (locked constraint per /121 CONFIRMATION).
  Per-symbol drawdown brake ENABLED at T=7.0/T_R=6.0/N=45/M=21 (/127 sole axis).
"""

DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
"""Default ATR multipliers for symbols not in V3_ATR_MULTIPLIERS_PER_SYMBOL.

iter-v3/125: REVERT (3.4641, 1.7321) → (2.0, 1.0). /124 NEGATIVE-catastrophic
(K=63 Branch B longer-cadence labels axis); /124 closed bilaterally per brief Section
3. /125 WILD CYCLE-7 axis-4 uses /121-canonical (2.0, 1.0) ATR multipliers.

History:
  iter-v3/043: REVERTED from (1.5, 0.75) back to (2.0, 1.0) — iter-v3/042 Path C.
  Value (2.0, 1.0) first set at iter-v3/010; validated anchor through iter-v3/041.
  iter-v3/065: (2.0, 1.0) → (2.0, 1.5) — UNIVERSAL SL widening (Path D).
  iter-v3/066: (2.0, 1.5) → (2.0, 1.0) — REVERT for axis isolation (Path E0.8).
  iter-v3/067-069: (2.0, 1.0) — carry-forward (non-labeling axes).
  iter-v3/070: (2.0, 1.0) → (2.0, 1.5) — RE-APPLIED /065 Component A at CONFIRMATION.
  iter-v3/070 CLOSEOUT: (2.0, 1.5) → (2.0, 1.0) — Component A REJECTED; restored /059 canonical.
  iter-v3/071–123: (2.0, 1.0) — carry-forward across 53 iterations (canonical baseline).
  iter-v3/124: (2.0, 1.0) → (3.4641, 1.7321) — Branch B sqrt(3) scaling (K=63 axis). NEGATIVE.
  iter-v3/125: (3.4641, 1.7321) → (2.0, 1.0) — REVERT /124 (NEGATIVE-catastrophic); /121 canonical.
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
    features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N  (14 features at /127)
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
    """Load klines for *symbol*, run the /121-minimal v3 feature pipeline,
    write parquet.

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
    # iter-v3/132 live-track parity: invalidate cross-asset caches on every
    # call. Without this, live ticks see stale BTC/ETH frames after the first
    # invocation and cross_btc_v3 merges go silently NaN — divergence from
    # backtest. Mirrors features_v2 post-62d56dc hygiene. Zero-cost in
    # backtest (which calls this once at startup); critical for live.
    from crypto_trade.features_v3.cross_btc_v3 import (
        clear_btc_cache_v3,
        clear_eth_cache_v3,
    )

    clear_btc_cache_v3()
    clear_eth_cache_v3()

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
    "add_engineered_v3_features",
    "atr_multipliers_for_symbol",
    "features_for_symbol",
    "generate_features_v3",
    "list_groups",
    "process_symbol_v3",
    "run_features_v3",
]
