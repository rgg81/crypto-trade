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

from crypto_trade.features_v3.cross_btc_v3 import add_cross_btc_v3_features
from crypto_trade.features_v3.engineered_v3 import add_engineered_v3_features
from crypto_trade.features_v3.fracdiff_v3 import add_fracdiff_v3_features
from crypto_trade.features_v3.funding_v3 import add_btc_funding_v3_features, add_funding_v3_features
from crypto_trade.features_v3.microstructure_v3 import add_microstructure_v3_features
from crypto_trade.features_v3.momentum_accel_v3 import add_momentum_accel_v3_features
from crypto_trade.features_v3.price_efficient_vol_v3 import add_price_efficient_vol_v3_features
from crypto_trade.features_v3.regime_v3 import add_regime_v3_features
from crypto_trade.features_v3.tail_risk_v3 import add_tail_risk_v3_features
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
    "engineered_v3": add_engineered_v3_features,
    "fracdiff": add_fracdiff_v3_features,
    "microstructure_v3": add_microstructure_v3_features,
    # iter-v3/019: NEW external-data-source feature family; infrastructure PRESERVED
    "funding_v3": add_funding_v3_features,
    # iter-v3/024: cross-asset BTC funding broadcast; infrastructure PRESERVED
    "btc_funding_v3": add_btc_funding_v3_features,
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
    # Top-13 feature subset for iter-v3/008 CONFIRMATION run.
    # vwap_dev_50 dropped per Critic FINAL SHA a544621 (Recommendation 1):
    #   vwap_dev_50 had IC 0.875 with ema_spread_atr_20 AND IC 0.794 with
    #   vwap_dev_20 — dropping it kills both redundant pairs in one move.
    # Source: analysis/iteration_v3-008/ic_redundancy_drop_demo.py (SHA 003a21e).
    # Groups: tail_risk (6), momentum_accel (2), volume_micro (1),
    #         regime (2), cross_btc (2).
    # iter-v3/016: tbr_zscore_30 DROPPED (reverted to 13 features; iter-v3/013 baseline).
    # Per Critic FINAL Rec 3 of iter-v3/015 + iter-v3/016 brief §3.3.
    "max_dd_window_50",  # rank 1 (mean 2.5)  — tail_risk
    "ema_spread_atr_20",  # rank 2 (mean 3.0)  — momentum_accel
    "ret_kurt_50",  # rank 3 (mean 5.0)  — tail_risk
    "ret_skew_200",  # rank 4 (mean 5.0)  — tail_risk
    "range_realized_vol_50",  # rank 5 (mean 6.5)  — tail_risk
    "hurst_diff_100_50",  # rank 6 (mean 11.5) — regime
    "ret_kurt_200",  # rank 7 (mean 11.5) — tail_risk
    "hurst_100",  # rank 8 (mean 11.5) — regime
    "btc_ret_14d",  # rank 9 (mean 12.5) — cross_btc
    # iter-v3/041: ret_skew_50 DROPPED (universal feature pruning EXPLORATION).
    # iter-v3/028 portfolio importance rank 12/14, importance 412.8 (68.30% of top).
    # Bottom-3 by canonical multi-seed iter-v3/028 portfolio split-importance.
    # Per analysis/iteration_v3-041/bottom3_features_eda.py SHA c2e2712.
    # iter-v3/042: ret_skew_50 RESTORED (iter-v3/041 Path C mandate — OOS dropped
    # below +1.55 falsifier; prune REVERTED per research_brief.md Section 3 Sub-fix 1).
    # iter-v3/057: ret_skew_50 SWAPPED for parkinson_gk_ratio_20 (A4 base-stack reordering).
    # Per analysis/iteration_v3-057/synthesis.md SHA `8160e3a`:
    # - ret_skew_50 was rank 12/14 portfolio importance at /056; bottom-3 BCH+TRX, mid LDO.
    # - parkinson_gk_ratio_20 (family `price_efficient_vol`) is FIRST-IN-CATEGORY for v3 base stack.
    # - All 3 syms univariate Spearman rho p<0.005 (BCH 0.001, LDO 0.0002, TRX 0.003).
    # - max |IC| with remaining V3_BASE_14 = 0.245 (well below 0.50 strict gate).
    # - Was in V3_FEATURE_COLUMNS_FULL (34) at /001-006; dropped at /007 top-N reduction
    #   (rank 17/34).
    # - Never tested at dedicated EXPLORATION axis. Also in V2_FEATURE_COLUMNS (v0.v2-069 active).
    "parkinson_gk_ratio_20",  # SWAP iter-v3/057 — price_efficient_vol family
    "vwap_dev_20",  # rank 11 (mean 13.0) — volume_micro
    "ret_autocorr_lag1_50",  # rank 12 (mean 13.5) — momentum_accel
    # iter-v3/041: sym_vs_btc_ret_7d DROPPED (universal feature pruning EXPLORATION).
    # iter-v3/028 portfolio importance rank 13/14, importance 398.0 (65.85% of top).
    # ALSO bottom-3 in iter-v3/040 single-seed cross-check (rank 12, importance 606.0).
    # Per analysis/iteration_v3-041/bottom3_features_eda.py SHA c2e2712.
    # iter-v3/042: sym_vs_btc_ret_7d RESTORED (iter-v3/041 Path C mandate — prune REVERTED).
    # iter-v3/020: funding_rate_zscore_30 DROPPED (reverted to 13 features).
    # Per Critic FINAL Rec 2 of iter-v3/019 review: rank 14/14 across all 3
    # symbols; feature did not contribute signal. Infrastructure (funding_v3.py,
    # GROUP_REGISTRY entry, fetch-funding CLI, data/funding_rates/ cache) is
    # PRESERVED for possible iter-v3/028+ CONFIRMATION retest.
    # iter-v3/023: funding_rate_zscore_30 RE-ADDED (13 → 14; budget-disambiguation
    # RETEST at n_trials=35 per Critic FINAL `3b3cc41` of iter-v3/022 Rec #1).
    # iter-v3/019 was PROMISING-INERT at n_trials=10; retest disambiguates
    # "feature genuinely INERT" vs "n_trials=10 budget too small".
    # iter-v3/024: funding_rate_zscore_30 DROPPED (14 → 13; INERT-CONFIRMED at
    # n_trials=35 per Critic FINAL `c4574af` of iter-v3/023 Rec #1).
    # Per-symbol funding family PERMANENTLY-CLOSED in v3 (2 EXPLORATION data
    # points at n_trials=10 AND n_trials=35 both rank 14/14).
    # btc_funding_rate_zscore_30 ADDED (13 → 14): cross-asset BTC funding rate
    # z-score broadcast to all 3 per-symbol models. STRUCTURALLY DISTINCT from
    # per-symbol funding: BTC's funding stress is a system-level signal shared
    # across BCH/LDO/TRX training datasets at any given timestamp.
    # iter-v3/025: btc_funding_rate_zscore_30 DROPPED (14 → 13; BTC cross-asset
    # funding family PERMANENTLY-CLOSED per Critic FINAL `5a47f5d` of iter-v3/024;
    # OOS Sharpe −0.82, rank 14/14 across BCH+LDO portfolio cuts + 9/14 TRX).
    # regime_momentum_signed_5d ADDED (13 → 14): composed feature = ret_5d ×
    # sign(hurst_100 − 0.5). Category 2 axis (genuine feature engineering pivot
    # per user directive 2026-05-08 + Critic FINAL `5a47f5d` of iter-v3/024).
    # IC hard gate BYPASSED with carve-out (see phase5p5_gate.md §IC-Gate Carve-Out
    # + feedback_v3_engineered_feature_pivot.md).
    # iter-v3/041: regime_momentum_signed_5d DROPPED — see end-of-tuple comment
    # block for full rationale + 3-path classification.
    # iter-v3/034: fracdiff_d05_close ADDED (14 → 15): LdP AFML Ch. 5 FFD at d=0.5.
    # iter-v3/035: fracdiff_d05_close DROPPED from universal list (15 → 14 revert).
    # Moved to V3_FEATURES_PER_SYMBOL["BCHUSDT"] only (BCH-only per-symbol targeting).
    # iter-v3/034 showed BCH +37.98 OOS wpnl swing but TRX -20.11 / ALGO -8.24 / LDO -6.81
    # regression — universal application creates per-symbol drag.  BCH-only targeting via
    # V3_FEATURES_PER_SYMBOL preserves BCH lift while restoring TRX/ALGO/LDO anchor.
    # iter-v3/026: vol_adj_autocorr ADDED (14 → 15): composed feature =
    # ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6). Second Category 2
    # axis: stacked NEGATIVE-SUSPICIOUS-OOS — IS Sharpe collapse to +0.0493 +
    # OOS spike to +1.4501 (27× IS/OOS ratio absurd; stacking-falsified at
    # single-seed n_trials=35).
    # iter-v3/027: vol_adj_autocorr DROPPED (15 → 14 transitional) per
    # `feedback_v3_engineered_features_dont_stack.md`. cross_asset_divergence_norm
    # ADDED (14 → 15): composed feature = (sym_ret_7d - btc_ret_14d) /
    # (|vwap_dev_20| + 1e-6). Third Category 2 axis: alt-vs-BTC return divergence
    # normalized by mean-reversion intensity — relative-strength signal. Source
    # primitives NON-OVERLAPPING with regime_momentum's (sym_ret_7d/btc_ret_14d/
    # vwap_dev_20 vs close-derived ret_5d/hurst_100). IC hard gate bypassed per
    # Category 2 carve-out (IC 0.756 vs source primitive sym_vs_btc_ret_7d is
    # expected for a composed feature; see phase5p5_gate.md §IC-Gate Carve-Out).
    # Per Critic FINAL Rec of iter-v3/026 (SHA `8839bbb`) + user directive 2026-05-08.
    # iter-v3/028: cross_asset_divergence_norm DROPPED (15 → 14 revert). Mini-
    # validation of iter-v3/025 ALONE at --seeds 2; stacking FALSIFIED at
    # iter-v3/027 (IS Sharpe collapse -0.2817 + OOS spike +1.6786; TRX 91.57%
    # concentration regression). Per Critic FINAL `966f4c1` of iter-v3/027 +
    # user directive 2026-05-08. compute_cross_asset_divergence_norm retained as
    # dead code in engineered_v3.py at zero revert cost.
    # iter-v3/041: regime_momentum_signed_5d DROPPED (universal feature pruning
    # EXPLORATION).  iter-v3/028 portfolio importance rank 14/14, importance 390.4
    # (64.59% of top). ALSO rank 14/14 in iter-v3/040 single-seed cross-check
    # (importance 454.0). Strongest evidence of consistent bottom rank — both the
    # canonical multi-seed and the single-seed cycle 3 anchor place this engineered
    # feature at the bottom of the importance distribution.
    #
    # MUST-be-present mandate from feedback_v3_engineered_features_proven.md
    # (established iter-v3/025 closeout) is being REVISITED at iter-v3/041
    # EXPLORATION. EXPLORATIONs can falsify any prior assumption. Three classification
    # paths (per briefs-v3/iteration_v3-041/research_brief.md Section 8):
    #   PATH A (PROMISING):       IS lift ≥ +0.10 AND OOS ≥ +1.55 → mandate FALSIFIED
    #   PATH B (PROMISING-INERT): |IS delta| ≤ 0.10 AND OOS ≥ +1.55 → parsimony-neutral
    #   PATH C (NEGATIVE):        OOS < +1.55 → mandate UPHELD; restore at iter-v3/042
    #                                                                               FIRED.
    # Per analysis/iteration_v3-041/bottom3_features_eda.py SHA c2e2712.
    # iter-v3/042: regime_momentum_signed_5d RESTORED (Path C mandate fired;
    # OOS < +1.55 at iter-v3/041; mandate UPHELD per
    # feedback_v3_engineered_features_proven.md; prune REVERTED;
    # per briefs-v3/iteration_v3-042/research_brief.md Section 3 Sub-fix 1).
    "sym_vs_btc_ret_7d",  # rank 13/14 importance 398.0 — cross_btc  [RESTORED iter-v3/042]
    # rank 14/14 importance 390.4 — engineered_v3  [RESTORED iter-v3/042]
    "regime_momentum_signed_5d",
    # iter-v3/043: efficiency_ratio_50 ADDED (14 → 15). Kaufman 1995 efficiency ratio:
    # abs(close - close.shift(50)) / sum(abs(close.diff()).rolling(50)) — unsigned [0,1].
    # Regime-quality signal: measures HOW EFFICIENTLY price moves, not direction.
    # Orthogonal mechanism to regime_momentum_signed_5d (signed direction-flip).
    # IC gate: Category 1 indicator (NOT engineered composition); standard |IC|<0.70 applies.
    # Past-only via shift(1) applied to ER series; warmup 51 bars (50-bar window + 1 shift).
    # Implemented via compute_efficiency_ratio_50 in engineered_v3.py.
    # Per briefs-v3/iteration_v3-043/research_brief.md Section 3 Sub-fix 2.
    # iter-v3/044: efficiency_ratio_50 DROPPED (15 → 14 REVERT). iter-v3/043 DISASTROUS
    # NEGATIVE (IS -0.8445 / OOS -0.8990; all 4 symbols broken by Kaufman ER).
    # compute_efficiency_ratio_50 retained as dead code in engineered_v3.py; NOT dispatched.
    # Per briefs-v3/iteration_v3-044/research_brief.md Section 3 Sub-fix 1.
    # iter-v3/044: regime_momentum_signed_3d UNIVERSAL ADDITION REVERTED before backtest
    # (orchestrator's ad-hoc setup commit 1f56c72 superseded by QR EDA-driven axis selection
    # at SHA `eff841e`).
    # cycle3_is_diagnosis.py SHA `eff841e`: IS bottleneck is direction-asymmetric per-symbol
    # (ALGO LONG 33 trades, -53.26 PnL, 18.2% IS WR / 11.1% OOS WR — single largest IS attribution
    # loss; counterfactual block of 3 bad direction-buckets lifts IS Sharpe +0.79 → +1.95).
    # The 3d variant does NOT discriminate ALGO LONG WR (22.2% > 0, 13.3% <=0) and ranks
    # 14/14 in ALGO model — universal addition would dilute colsample picks without
    # addressing the bottleneck. compute_regime_momentum_signed_3d retained as dead code in
    # engineered_v3.py; NOT dispatched (per Sub-fix 1 of Section 3 in rewritten brief).
    # New axis: per-symbol ATR widening for ALGOUSDT only (V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"]
    # = (2.0, 1.5)). Targets ALGO long SL/TP exit asymmetry (27/6 = 4.5:1) directly; proven
    # mechanism per iter-v3/032 LDO ATR success.
    # iter-v3/048: vol_normalized_ret_5d ADDED (14 → 15; cycle 3 plan Axis 1 NEW engineered
    # feature). Composed feature: ret_5d / (range_realized_vol_50 + 1e-6). Canonical Sharpe-
    # like risk-normalized momentum (Sinclair, Vol Trading; LdP AFML Ch. 8). range_realized_
    # vol_50 is rank-1 TRX importance (313/313; mean rank 3.00 across all 4 symbols). TRX has
    # flat importance distribution (2.5× top:bottom ratio) — model can't discriminate signal.
    # IC carve-out applies per feedback_v3_engineered_feature_pivot.md (Category 2 composed
    # feature; |IC| with ret_5d ~0.7+ expected by construction). Binding gate: importance >=30
    # in at least 2 of 4 symbols. QR EDA SHA a230cd1; cycle 3 #9 of 10.
    # iter-v3/049: vol_normalized_ret_5d DROPPED (15 → 14) per iter-v3/048 PATH C-clean
    # closeout. iter-v3/048 result: vol_normalized_ret_5d ranked 13-15/15 across all 4
    # symbols (IS Sharpe Δ -0.43 + OOS Sharpe Δ -3.15 vs iter-v3/045 anchor). Per pre-
    # registered saturation rule (brief §4 PATH C action), NEW universal engineered feature
    # axis CLOSED for cycle 3 (5 attempts: iter-v3/035, /041, /042, /043, /044+/048).
    # compute_vol_normalized_ret_5d retained as dead code in engineered_v3.py (zero revert
    # cost; available for future per-symbol experiments per iter-v3/048 diary §Architectural
    # Decisions). NOT dispatched when absent from V3_FEATURE_COLUMNS_TOP_N.
    # iter-v3/051: fracdiff_d05_close ADDED at universal scope (14 → 15) — cycle 4 #1
    # EXPLORATION axis. EXPLORATION-NULL-RESULT (PARKED): fracdiff LEARNED (ranks 11-13/15)
    # but no decisive IS lift; OOS lift within single-seed=42 lottery noise.
    # Per Critic FINAL `32cc46f` rec #2: DROP fracdiff_d05_close from V3_FEATURE_COLUMNS_TOP_N
    # at iter-v3/052 setup. compute_fracdiff_d05_close RETAINED in dispatch (parquet column
    # still generated) + 5 adversarial tests RETAINED — zero revert cost.
    # iter-v3/052: SWAP — regime_momentum_signed_3d REPLACES fracdiff_d05_close as 15th element.
    # PIVOT from orchestrator-mandated LDO-removal axis (pre-falsified by /052 EDA SHA `0a10581`):
    #   orchestrator premise "LDO IS PnL share -14.96%" misread net_pnl_pct (ignores weight_factor);
    #   LDO actual weighted_pnl at /051 IS = +11.155 (+36.78% bundle share) — IS CONTRIBUTOR.
    #   2-sym counterfactual: IS Δ -0.16 BREAKS BOTH-must-improve gate; IS-OOS ratio 3.58 OOB.
    # QR EDA supersedes per `feedback_v3_axis_selection_quant_discipline.md` rule 4.
    # PIVOTED axis = regime_momentum_signed_3d UNIVERSAL — /051 EDA RANKED #2 queued for /052
    # (SHA `290f37b` synthesis.md §c3 + candidate_axes_ranking.md §Candidate 2).
    # Mechanism: ret_3d × sign(hurst_100 − 0.5). Orthogonal time-scale variant of
    # regime_momentum_signed_5d (iter-v3/028 baseline edge ingredient; multi-seed validated).
    # EDA evidence (analysis/iteration_v3-051/axis_c_regime_3d_*.csv SHA `290f37b`):
    # - ADF stationary p=0 all 4 syms (axis_c_regime_3d_adf.csv); structurally stationary
    #   by construction (bounded sign factor × stationary ret_3d)
    # - IC strict-gate PASS: max |IC| = 0.6192 with vwap_dev_20 < 0.70 (NO carve-out needed;
    #   CLEANER than fracdiff which required Category-2 carve-out at LDO 0.7381)
    # - Univariate Spearman ρ -0.044 to -0.068 significant all 4 syms (mean -0.057;
    #   STRONGER than fracdiff -0.044); negative = mean-reversion signal
    # - IC with sister 5d feature 0.43-0.47 (below 0.50 stacking-risk threshold from /026)
    # - /044 ALGO LONG falsification CONDITIONAL on ALGO universe; ALGO REVERTED at /051+/052
    # - compute_regime_momentum_signed_3d dead code at engineered_v3.py:330 ACTIVATED at /052
    # Per `feedback_v3_engineered_features_proven.md`: composed engineered features CAN work
    # at universal scope (iter-v3/025 PROMISING + /028 CONFIRMATION-MERGE precedent).
    # System-level REVERT to iter-v3/028 architecture (V3_MODELS=3-sym; V3_ATR_MULTIPLIERS_
    # PER_SYMBOL={}; block_long_for=(); REQUIRED_GAP=66) UNCHANGED from /051.
    # iter-v3/053: regime_momentum_signed_3d DROPPED (PARKED per /052 closeout PATH C-suspicious;
    #   saturation rank 14-15/15 across all 3 symbols; IS-OOS daily ratio 2.327 OUT-OF-BAND;
    #   Critic FINAL `34cc46f` rec #2 mandate pivot to structurally distinct feature family).
    #   compute_regime_momentum_signed_3d RETAINED in dispatch as dead code (zero revert cost).
    # iter-v3/053: hurst_drift_50_200 ADDED as 15th element (NEW Category 1 engineered feature).
    #   Mechanism: hurst_50 - hurst_200 = hurst_100 - hurst_diff_100_50 - hurst_200.
    #   REFRAMED HYPOTHESIS B: R^2=1.0 linear redundancy with 3 source primitives
    #   (EDA SHA `1fc6d55` axis5_linear_redundancy.csv). Primary value: DOCUMENT
    #   Linear Redundancy Pre-Falsifier (LR-PF) methodology for future Category 2
    #   composed-feature axis selections (path B 55% predicted).
    #   Univariate rho NOT significant p<0.05 in all 4 syms (mean +0.0114; weakest).
    #   Feature computable from existing parquet columns -- NO parquet regen required.
    # iter-v3/054: hurst_drift_50_200 DROPPED (PARKED per /053 closeout PATH D NULL-RESULT;
    #   15th-slot SWAP family STRUCTURALLY EXHAUSTED at single-seed EXPLORATION per Critic
    #   FINAL `c056354` Recommendation #1: CPCV 29/45 positive, median +0.3351, Q25 -0.243
    #   IDENTICAL across /051/052/053 to 4 decimals). compute_hurst_drift_50_200 RETAINED in
    #   engineered_v3.py as dead code (zero revert cost). 5 adversarial tests RETAINED.
    #   Net count: 15 → 14 (system-mandated REVERT to iter-v3/028 base stack).
)
"""Top-14 feature subset (as of iter-v3/054): hurst_drift_50_200 DROPPED (PARKED per /053
closeout PATH D; 15th-slot SWAP family exhausted per Critic FINAL `c056354`). Net 14 features.
iter-v3/051: fracdiff_d05_close ADDED at universal scope per cycle 4 #1 EXPLORATION axis.
iter-v3/052: fracdiff_d05_close PARKED (EXPLORATION-NULL-RESULT; SWAP to 3d per Critic
`32cc46f` rec #2).
iter-v3/053: regime_momentum_signed_3d DROPPED (PARKED per /052 PATH C-suspicious closeout;
Critic FINAL `34cc46f` rec #2).
System-level REVERT to iter-v3/028 architecture (V3_MODELS=3-sym BCH+LDO+TRX; ALGO REVERTED;
V3_ATR_MULTIPLIERS_PER_SYMBOL={}; block_long_for=(); REQUIRED_GAP=66).
iter-v3/049: vol_normalized_ret_5d DROPPED per iter-v3/048 PATH C-clean closeout.
iter-v3/048 ranked vol_normalized_ret_5d 13-15/15 across all 4 symbols (IS Sharpe Δ -0.43
+ OOS Sharpe Δ -3.15 vs iter-v3/045 anchor); saturation rule fires — NEW universal
engineered feature axis CLOSED for cycle 3.

Top-14 context (iter-v3/044): reverts iter-v3/043's DISASTROUS efficiency_ratio_50
(IS -0.8445 / OOS -0.8990; all 4 symbols broken). The 3d variant universal addition was
ALSO REVERTED before backtest (orchestrator's ad-hoc setup superseded by QR EDA-driven
axis selection per feedback_v3_axis_selection_quant_discipline.md).

iter-v3/042 restored 3 features (ret_skew_50, sym_vs_btc_ret_7d,
regime_momentum_signed_5d) from iter-v3/041 Path C NEGATIVE mandate.
The MUST-be-present mandate for regime_momentum_signed_5d from
feedback_v3_engineered_features_proven.md remains ACTIVE at iter-v3/049.

iter-v3/043: efficiency_ratio_50 ADDED (14 → 15) — DISASTROUS NEGATIVE.
iter-v3/044: efficiency_ratio_50 DROPPED (reverted to 14 base). compute_efficiency_ratio_50
retained as dead code in engineered_v3.py; NOT dispatched from add_engineered_v3_features.
Per briefs-v3/iteration_v3-044/research_brief.md Section 3 Sub-fix 1.
iter-v3/044: regime_momentum_signed_3d UNIVERSAL ADDITION REVERTED (15 → 14). The orchestrator's
setup commit `1f56c72` added 3d as a 15th universal feature ad-hoc; QR EDA at SHA `eff841e`
established that the IS bottleneck is direction-asymmetric per-symbol (ALGO LONG single largest
attribution loss) and 3d does NOT discriminate ALGO LONG WR. compute_regime_momentum_signed_3d
retained as dead code in engineered_v3.py; NOT dispatched. Per Sub-fix 2 of Section 3.
Replacement axis: per-symbol ATR widening for ALGOUSDT only.

Top-N history (last 8 entries):
  iter-v3/041: pruned 14 → 11 (dropped ret_skew_50, sym_vs_btc_ret_7d, regime_momentum)
  iter-v3/042: RESTORED 11 → 14 (Path C NEGATIVE mandate at iter-v3/041 fired)
  iter-v3/043: ADDED 14 → 15 (efficiency_ratio_50 Kaufman 1995 ER — DISASTROUS NEGATIVE)
  iter-v3/044: REVERT 15 → 14 (drop both efficiency_ratio_50 AND regime_momentum_signed_3d
              universal addition; new axis = per-symbol ATR for ALGO).
  iter-v3/048: ADDED 14 → 15 (vol_normalized_ret_5d NEW; cycle 3 #9 of 10).
  iter-v3/049: REVERT 15 → 14 (vol_normalized_ret_5d DROPPED; iter-v3/048 PATH C-clean).
  iter-v3/051: ADDED 14 → 15 (fracdiff_d05_close UNIVERSAL; cycle 4 #1 EXPLORATION).
  iter-v3/052: SWAP 15 → 15 (fracdiff_d05_close PARKED; regime_momentum_signed_3d ACTIVATED
              — PIVOT from orchestrator LDO-removal axis; QR-EDA-backed /051 RANKED #2).

iter-v3/035 revert — fracdiff_d05_close removed from universal list (15→14; moved
to V3_FEATURES_PER_SYMBOL["BCHUSDT"] for BCH-only per-symbol targeting); cleared
again at iter-v3/040 cycle 3 baseline restore.  iter-v3/034 add: fracdiff_d05_close
added (14→15) then dropped here at iter-v3/035 (15→14).
iter-v3/028 drop: cross_asset_divergence_norm removed (revert 15→14; matches
iter-v3/025 anchor exactly). iter-v3/027 was: atomic swap vol_adj_autocorr dropped,
cross_asset_divergence_norm added.

``tbr_zscore_30`` DROPPED per iter-v3/016 brief §3.3 (Critic FINAL Rec 3 of
iter-v3/015 mandated revert before XGBoost axis exploration).

Top-N history:
vwap_dev_50 dropped per Critic FINAL SHA a544621 (Recommendation 1).
Dropping it removed both IC-redundant pairs in the 14-feature subset:
  - vwap_dev_50 x ema_spread_atr_20: IC 0.875 (above 0.70 threshold)
  - vwap_dev_50 x vwap_dev_20:       IC 0.794 (above 0.70 threshold)
Residual max |IC| in the 13-feature subset: 0.6602.  No pair above 0.70.
See analysis/iteration_v3-008/ic_redundancy_drop_demo.py (SHA 003a21e).

``tbr_zscore_30`` was added in iter-v3/015 (rank 14/14 in LightGBM importance
across all 3 symbols, determined mechanically inert per EXPLORATION-NEGATIVE-no-effect
verdict).  Reverted here per iter-v3/016 brief §3.3.  ``tbr_raw`` is now in
V3_NON_FEATURE_COLUMNS (hygiene; Critic Clarification 4 from iter-v3/015).

``funding_rate_zscore_30`` was added in iter-v3/019 (NEW external-data-source
feature family; 30-cycle z-score of Binance Futures funding rate).  Rank 14/14
across all 3 symbols per Critic FINAL Rec 2 of iter-v3/019 review — DROPPED
at iter-v3/020 to revert to the 13-feature iter-v3/018 anchor surface.
The funding infrastructure is KEPT (GROUP_REGISTRY, fetch-funding CLI,
data/funding_rates/ cache) so the column remains in generated parquets
but is NOT fed to LightGBM.
RE-ADDED at iter-v3/023 for budget-disambiguation RETEST at n_trials=35
per Critic FINAL Rec #1 of iter-v3/022 (SHA ``3b3cc41``).
INERT-CONFIRMED at n_trials=35 per Critic FINAL ``c4574af`` of iter-v3/023
Rec #1 — OOS Sharpe -1.07 (worst single-seed OOS in v3 history).  Per-symbol
funding family PERMANENTLY-CLOSED in v3 (2 EXPLORATION data points).

``btc_funding_rate_zscore_30`` ADDED at iter-v3/024 (cross-asset variant):
BTC funding rate z-score broadcast identically to all 3 per-symbol models
(BCH/LDO/TRX get the same column value at any given timestamp).
Mechanism: market-wide leveraged-positioning stress indicator (system-level),
distinct from per-symbol micro-signal.  IC vs existing 14 features: max 0.1921
(< 0.50 brief target, < 0.70 hard gate) per EDA SHA ``afdb8bc``.
Implemented via ``add_btc_funding_v3_features`` in ``funding_v3.py``;
registered as ``btc_funding_v3`` entry in GROUP_REGISTRY.
DROPPED at iter-v3/025: funding family PERMANENTLY-CLOSED (both per-symbol +
cross-asset variants); rank 14/14 across BCH+LDO portfolio cuts + 9/14 TRX;
OOS Sharpe −0.82 per Critic FINAL ``5a47f5d`` of iter-v3/024.  Infrastructure
(funding_v3.py, btc_funding_v3.py, GROUP_REGISTRY entries, data/funding_rates/
cache) PRESERVED at zero revert cost.

``regime_momentum_signed_5d`` ADDED at iter-v3/025 (Category 2 composed feature):
ret_5d × sign(hurst_100 − 0.5).  Momentum 5-day log return sign-flipped by the
Hurst regime classifier: +ret_5d in trending regimes (hurst > 0.5 → momentum
continues), −ret_5d in mean-reverting regimes (hurst < 0.5 → momentum reverses).
Per user directive 2026-05-08 + Critic FINAL `5a47f5d` of iter-v3/024 Rec.
IC vs source primitives: max |IC| 0.887 (vs vwap_dev_20) — EXPECTED for a
composed feature; IC gate bypassed per Category 2 carve-out in phase5p5_gate.md
+ feedback_v3_engineered_feature_pivot.md.  First Category 2 axis in v3 catalog.
Implemented via ``compute_regime_momentum_signed_5d`` in ``engineered_v3.py``;
registered as ``engineered_v3`` entry in GROUP_REGISTRY (after ``cross_btc``,
before ``fracdiff``; dependency on ``hurst_100`` from ``regime`` group satisfied).

``vol_adj_autocorr`` ADDED at iter-v3/026 (Category 2 composed feature) then
DROPPED at iter-v3/027: stacked NEGATIVE-SUSPICIOUS-OOS — IS Sharpe collapse to
+0.0493 (lowest IS in any post-bootstrap iteration) + OOS spike to +1.4501 (27×
IS/OOS ratio structurally absurd; single-seed-lottery suspect). Stacking two
engineered features at single-seed n_trials=35 expands Optuna search space beyond
depth-3-5 LightGBM representational capacity. Per `feedback_v3_engineered_features_dont_stack.md`.
Function ``compute_vol_adj_autocorr`` retained as dead code in ``engineered_v3.py``
at zero revert cost; NOT dispatched from ``add_engineered_v3_features``.

``cross_asset_divergence_norm`` ADDED at iter-v3/027 (Category 2 composed feature):
(sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6).  Alt-vs-BTC return divergence
normalized by mean-reversion intensity: same alt-BTC divergence has different
implications depending on local VWAP deviation (Robert Carver *Systematic Trading*
+ Ernest Chan *Quantitative Trading*).  Output clipped to [−100, +100] to prevent
infinity on near-zero denominator.  Per Critic FINAL Rec of iter-v3/026 (SHA
`8839bbb`) + user directive 2026-05-08 + `feedback_v3_engineered_features_dont_stack.md`.
Max |IC| vs source primitive sym_vs_btc_ret_7d: 0.756 — EXPECTED for a composed
feature; IC gate bypassed per Category 2 carve-out.  Max |IC|_rm vs
regime_momentum_signed_5d: 0.464 (LDO worst) — informational only; reflects shared
sym_vs_btc_ret_7d variance pathway, NOT regime_momentum mechanism overlap.
Source primitives NON-OVERLAPPING with regime_momentum's (sym_ret_7d/btc_ret_14d/
vwap_dev_20 vs close-derived ret_5d/hurst_100).  Implemented via
``compute_cross_asset_divergence_norm`` in ``engineered_v3.py``; dispatched from
``add_engineered_v3_features`` AFTER regime_momentum_signed_5d.  All 3 source
primitives (close, btc_ret_14d, vwap_dev_20) upstream in GROUP_REGISTRY.
Third Category 2 axis in v3 catalog.  IS rank-IC: max 0.109 (LDO h7) — STRONGEST
predictive signal among 4 EDA candidates × 3 symbols × 3 horizons.

``cross_asset_divergence_norm`` DROPPED at iter-v3/028 (15 → 14 revert).  MINI-
VALIDATION of iter-v3/025 ALONE at ``--seeds 2``; cross_asset_divergence_norm
stacking FALSIFIED at single-seed iter-v3/027 (IS Sharpe collapse -0.2817, OOS
spike +1.6786; TRX 91.57% concentration regression; 3-iter monotonic IS degradation
pattern).  Matches iter-v3/025 anchor exactly (14 features).  Per Critic FINAL
``966f4c1`` of iter-v3/027 + user directive 2026-05-08.  ``compute_cross_asset_divergence_norm``
retained as dead code in ``engineered_v3.py`` at zero revert cost; NOT dispatched
from ``add_engineered_v3_features`` at iter-v3/028.
"""

# iter-v3/007-008: reassign to top-N subset for EXPLORATION/CONFIRMATION run.
# iter-v3/007: top-14; iter-v3/008: top-13 (vwap_dev_50 dropped per Critic Rec 1).
# iter-v3/015: top-14 (tbr_zscore_30 added as NEW microstructure feature family).
# iter-v3/016: top-13 (tbr_zscore_30 DROPPED; reverted to iter-v3/013 baseline).
# iter-v3/019: top-14 (funding_rate_zscore_30 added — NEW external-data-source feature family).
# iter-v3/020: top-13 (funding_rate_zscore_30 DROPPED per Critic FINAL Rec 2 of iter-v3/019).
# iter-v3/023: top-14 (funding_rate_zscore_30 RE-ADDED — budget-disambiguation RETEST at
#              n_trials=35; per Critic FINAL `3b3cc41` of iter-v3/022 Rec #1).
# iter-v3/024: top-14 (funding_rate_zscore_30 DROPPED — INERT-CONFIRMED at n_trials=35;
#              btc_funding_rate_zscore_30 ADDED — cross-asset BTC funding broadcast to all 3
#              per-symbol models; per Critic FINAL `c4574af` of iter-v3/023 Rec #1).
# iter-v3/025: top-14 (btc_funding_rate_zscore_30 DROPPED — BTC cross-asset funding family
#              PERMANENTLY-CLOSED per Critic FINAL `5a47f5d` of iter-v3/024; OOS -0.82;
#              regime_momentum_signed_5d ADDED — Category 2 composed feature: ret_5d ×
#              sign(hurst_100 - 0.5); per user directive 2026-05-08 + Critic `5a47f5d` Rec).
# iter-v3/026: top-15 (vol_adj_autocorr ADDED — Category 2 composed feature:
#              ret_autocorr_lag1_50 / (range_realized_vol_50 + 1e-6); second Category 2 axis;
#              per Critic FINAL Rec of iter-v3/025 SHA `402643d` + user directive 2026-05-08.
#              NEGATIVE-SUSPICIOUS-OOS: IS Sharpe collapse +0.0493 + OOS spike +1.4501;
#              27× IS/OOS ratio; stacking-falsified at single-seed n_trials=35).
# iter-v3/027: top-15 (vol_adj_autocorr DROPPED — stacking FALSIFIED at single-seed per
#              `feedback_v3_engineered_features_dont_stack.md`; cross_asset_divergence_norm
#              ADDED (14 → 15; net unchanged at 15): Category 2 composed feature:
#              (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6); third Category 2 axis;
#              per Critic FINAL Rec of iter-v3/026 SHA `8839bbb` + user directive 2026-05-08.
#              regime_momentum_signed_5d KEPT (iter-v3/025 PROMISING; mandated by
#              `feedback_v3_engineered_features_proven.md`).
# iter-v3/028: top-14 (cross_asset_divergence_norm DROPPED — revert 15 → 14; matches
#              iter-v3/025 anchor exactly; MINI-VALIDATION of iter-v3/025 at --seeds 2;
#              stacking FALSIFIED at iter-v3/027; per Critic FINAL `966f4c1` + user
#              directive 2026-05-08. regime_momentum_signed_5d KEPT — MINI-VALIDATION
#              target; mandated by `feedback_v3_engineered_features_proven.md`).
# iter-v3/034: top-15 (fracdiff_d05_close ADDED — LdP AFML Ch. 5 FFD at d=0.5; 14 → 15.
#              Fixed-window fractional differentiation of log(close); memory-preserving
#              stationary feature complementary to regime_momentum_signed_5d.  V3_MODELS:
#              DROP VETUSDT (5 → 4; EXPLORATION-NEGATIVE per Critic FINAL 93d2b85; alignment
#              necessary but not sufficient for IS lift).  REQUIRED_GAP 110 → 88.
#              RESULT: BCH +37.98 OOS wpnl swing; TRX -20.11 / ALGO -8.24 / LDO -6.81
#              regressions.  Universal IS Sharpe -0.1636 (worst post-bootstrap).  BCH lift
#              is real but universal application creates per-symbol drag.)
# iter-v3/035: top-14 (fracdiff_d05_close DROPPED from universal list — per-symbol
#              targeting via V3_FEATURES_PER_SYMBOL["BCHUSDT"] instead.  BCH receives
#              15 features (14 universal + fracdiff_d05_close); TRX/ALGO/LDO receive
#              14 features via fallback.  Net: universal list reverts to iter-v3/032/028
#              anchor.  Atomic operation: revert universal + add BCH per-symbol entry.)
# To restore full set: V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_FULL
V3_FEATURE_COLUMNS: tuple[str, ...] = V3_FEATURE_COLUMNS_TOP_N
"""Active feature columns fed to LightGBM / XGBoost.

iter-v3/001-006: V3_FEATURE_COLUMNS_FULL (34 features).
iter-v3/007:     V3_FEATURE_COLUMNS_TOP_N (14 features, EXPLORATION).
iter-v3/008:     V3_FEATURE_COLUMNS_TOP_N (13 features, CONFIRMATION;
                 vwap_dev_50 dropped per Critic FINAL SHA a544621).
iter-v3/009-014: V3_FEATURE_COLUMNS_TOP_N (13 features, unchanged).
iter-v3/015:     V3_FEATURE_COLUMNS_TOP_N (14 features; tbr_zscore_30 added
                 per iter-v3/015 brief Section 3.3 — NEW microstructure family).
iter-v3/016:     V3_FEATURE_COLUMNS_TOP_N (13 features; tbr_zscore_30 DROPPED
                 per Critic FINAL Rec 3 + iter-v3/016 brief §3.3 revert).
iter-v3/017-018: V3_FEATURE_COLUMNS_TOP_N (13 features, unchanged).
iter-v3/019:     V3_FEATURE_COLUMNS_TOP_N (14 features; funding_rate_zscore_30
                 added per iter-v3/019 brief §3.3 — NEW external-data-source
                 feature family; 30-cycle z-score of Binance Futures funding rate).
iter-v3/020:     V3_FEATURE_COLUMNS_TOP_N (13 features; funding_rate_zscore_30
                 DROPPED per Critic FINAL Rec 2 of iter-v3/019 review — rank
                 14/14 across all 3 symbols; reverts to iter-v3/018 anchor surface).
iter-v3/021-022: V3_FEATURE_COLUMNS_TOP_N (13 features, unchanged).
iter-v3/023:     V3_FEATURE_COLUMNS_TOP_N (14 features; funding_rate_zscore_30
                 RE-ADDED per Critic FINAL Rec #1 of iter-v3/022 (SHA ``3b3cc41``)
                 — budget-disambiguation RETEST at n_trials=35; was PROMISING-INERT
                 at n_trials=10 in iter-v3/019).
iter-v3/024:     V3_FEATURE_COLUMNS_TOP_N (14 features; funding_rate_zscore_30
                 DROPPED (INERT-CONFIRMED at n_trials=35; per Critic FINAL
                 ``c4574af`` of iter-v3/023 Rec #1 — per-symbol funding family
                 PERMANENTLY-CLOSED); btc_funding_rate_zscore_30 ADDED as cross-asset
                 BTC funding z-score broadcast to all 3 per-symbol models.
                 Registered as ``btc_funding_v3`` in GROUP_REGISTRY.)
iter-v3/025:     V3_FEATURE_COLUMNS_TOP_N (14 features; btc_funding_rate_zscore_30
                 DROPPED (BTC cross-asset funding family PERMANENTLY-CLOSED per
                 Critic FINAL ``5a47f5d`` of iter-v3/024 — OOS Sharpe -0.82, rank
                 14/14 on BCH+LDO portfolio cuts + 9/14 TRX); regime_momentum_signed_5d
                 ADDED as Category 2 composed feature: ret_5d × sign(hurst_100 - 0.5).
                 User directive 2026-05-08 + Critic ``5a47f5d`` Rec mandated pivot
                 to genuine feature engineering.  First Category 2 axis in v3 catalog.
                 Registered as ``engineered_v3`` in GROUP_REGISTRY, after ``cross_btc``
                 and before ``fracdiff`` to satisfy hurst_100 dependency ordering.)
iter-v3/026:     V3_FEATURE_COLUMNS_TOP_N (15 features; vol_adj_autocorr ADDED as
                 Category 2 composed feature: ret_autocorr_lag1_50 / (range_realized_vol_50
                 + 1e-6).  Second Category 2 axis in v3 catalog.  IC gate bypassed per
                 Category 2 carve-out (IC 0.985 vs source primitive expected for a composed
                 feature).  Structurally orthogonal to regime_momentum_signed_5d: max
                 |IC|_rm 0.075.  Per Critic FINAL Rec ``402643d`` of iter-v3/025 +
                 user directive 2026-05-08.  Output clipped to [-100, +100].
                 RESULT: NEGATIVE-SUSPICIOUS-OOS — IS Sharpe +0.0493 (collapse; lowest
                 IS in post-bootstrap cycle) + OOS +1.4501 (27× IS/OOS ratio absurd).
                 Stacking two engineered features at single-seed n_trials=35 FALSIFIED.)
iter-v3/027:     V3_FEATURE_COLUMNS_TOP_N (15 features; vol_adj_autocorr DROPPED —
                 stacking falsified per `feedback_v3_engineered_features_dont_stack.md`;
                 cross_asset_divergence_norm ADDED as Category 2 composed feature:
                 (sym_ret_7d - btc_ret_14d) / (|vwap_dev_20| + 1e-6).  Third Category 2
                 axis in v3 catalog.  IC gate bypassed per Category 2 carve-out (IC 0.756
                 vs source primitive sym_vs_btc_ret_7d expected for a composed feature).
                 regime_momentum_signed_5d KEPT (iter-v3/025 PROMISING; mandated by
                 `feedback_v3_engineered_features_proven.md`).  Net column count UNCHANGED
                 at 15 (atomic swap: drop vol_adj_autocorr + add cross_asset_divergence_norm).
                 Per Critic FINAL Rec ``8839bbb`` of iter-v3/026 + user directive 2026-05-08.)
iter-v3/028:     V3_FEATURE_COLUMNS_TOP_N (14 features; cross_asset_divergence_norm DROPPED —
                 revert 15 → 14; matches iter-v3/025 anchor exactly.  MINI-VALIDATION of
                 iter-v3/025 ALONE at --seeds 2 (SPECIAL EXPLORATION cadence #10/10).
                 Stacking FALSIFIED at iter-v3/027 (IS Sharpe collapse -0.2817; OOS spike
                 +1.6786; TRX 91.57% concentration regression; 3-iter monotonic IS degradation).
                 ``compute_cross_asset_divergence_norm`` retained as dead code in
                 ``engineered_v3.py`` at zero revert cost; NOT dispatched from
                 ``add_engineered_v3_features``.  regime_momentum_signed_5d KEPT — MINI-
                 VALIDATION target; mandated by `feedback_v3_engineered_features_proven.md`.
                 Per Critic FINAL ``966f4c1`` of iter-v3/027 + user directive 2026-05-08.)
iter-v3/034:     V3_FEATURE_COLUMNS_TOP_N (15 features; fracdiff_d05_close ADDED —
                 LdP AFML Ch. 5 FFD at d=0.5; fixed-window fractional differentiation
                 of log(close); memory-preserving stationary feature complementary to
                 regime_momentum_signed_5d.  Pure-numpy implementation in engineered_v3.py;
                 weights truncated at |w_k| < 1e-4 (~120-150 bars).  Dispatched after
                 regime_momentum_signed_5d in add_engineered_v3_features.  V3_MODELS:
                 VETUSDT DROPPED (5 → 4; EXPLORATION-NEGATIVE per Critic FINAL 93d2b85;
                 reverts to iter-v3/032 4-symbol anchor BCH+LDO+TRX+ALGO).
                 REQUIRED_GAP 110 → 88 = (21+1)×4.  Atomic swap: DROP VET + ADD feature.
                 RESULT: BCH +37.98 OOS wpnl swing; TRX -20.11 / ALGO -8.24 / LDO -6.81
                 regressions.  IS Sharpe -0.1636 (worst post-bootstrap; universal drag).)
iter-v3/035:     V3_FEATURE_COLUMNS_TOP_N (14 features; fracdiff_d05_close DROPPED from
                 universal list — per-symbol targeting via V3_FEATURES_PER_SYMBOL["BCHUSDT"].
                 BCH receives 15 features (14 universal + fracdiff_d05_close via per-symbol
                 dict); TRX/ALGO/LDO receive 14 features via fallback (same as iter-v3/032/028
                 anchor).  Universal list reverts to iter-v3/028 anchor.  Atomic: revert
                 universal list (15→14) + add BCH per-symbol entry.)
iter-v3/041:     V3_FEATURE_COLUMNS_TOP_N (11 features; pruned 3 lowest-importance:
                 ret_skew_50, sym_vs_btc_ret_7d, regime_momentum_signed_5d DROPPED.
                 NEGATIVE result: OOS < +1.55 falsifier threshold — Path C fired.)
iter-v3/042:     V3_FEATURE_COLUMNS_TOP_N (14 features; RESTORED all 3 pruned features
                 per iter-v3/041 Path C mandate. feedback_v3_engineered_features_proven.md
                 mandate for regime_momentum_signed_5d REINSTATED. DEFAULT_ATR_MULTIPLIERS
                 changed (2.0,1.0)→(1.5,0.75) universal tightening. NEGATIVE by IS collapse:
                 IS Sharpe -0.5941, TRX OOS -33 wpnl swing.)
iter-v3/043:     V3_FEATURE_COLUMNS_TOP_N (15 features; efficiency_ratio_50 ADDED —
                 Kaufman 1995 unsigned [0,1] regime-quality signal. DEFAULT_ATR_MULTIPLIERS
                 REVERTED (1.5,0.75)→(2.0,1.0) per iter-v3/042 IS-collapse mandate.
                 Category 1 indicator; standard IC gate applies.
                 RESULT: DISASTROUS NEGATIVE — IS -0.8445 / OOS -0.8990; all 4 symbols broken.)
iter-v3/044:     V3_FEATURE_COLUMNS_TOP_N (15 features; efficiency_ratio_50 DROPPED
                 (15 → 14 REVERT; iter-v3/043 DISASTROUS NEGATIVE mandate;
                 compute_efficiency_ratio_50 retained as dead code; NOT dispatched).
                 regime_momentum_signed_3d ADDED (14 → 15): 3-bar sign-flip variant;
                 ret_3d = close.shift(1)/close.shift(4) - 1.0 * sign(hurst_100[t-1] - 0.5).
                 Category 2 composed feature; IC carve-out applies.
                 Net: 15 = 13 original + regime_momentum_signed_5d + regime_momentum_signed_3d.)
"""

V3_NON_FEATURE_COLUMNS: tuple[str, ...] = ("natr_21_raw", "tbr_raw")
"""Columns computed by the v3 pipeline that are NOT model inputs.

``natr_21_raw``: raw NATR used for dynamic ATR barriers (not a signal feature).
``tbr_raw``:     raw tick-bar ratio before z-score normalization; Critic
                 Clarification 4 of iter-v3/015 identified this as excluded from
                 model input regardless (added iter-v3/016, §3.5 sub-fix #2).
"""

V3_ATR_MULTIPLIERS_PER_SYMBOL: dict[str, tuple[float, float]] = {
    # iter-v3/051: REVERT to empty dict per system-level rule
    # `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle
    # confirmation of per-symbol-customization anti-pattern at iter-v3/039 + iter-v3/050
    # CONFIRMATION-NO-MERGE). All 3 symbols (BCH/LDO/TRX) fall back to
    # DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0). ALGOUSDT and LDOUSDT per-symbol entries
    # REVERTED. Cycle 4 starting baseline = iter-v3/028 architecture exactly.
    # Per `analysis/iteration_v3-051/synthesis.md` SHA `290f37b`.
    # History: {} (iter-v3/040 cycle 3 REVERT) → ALGOUSDT (2.0,1.5) added iter-v3/044
    #   → LDOUSDT (2.0,1.5) added iter-v3/045 → BCHUSDT added+removed iter-v3/046/047
    #   → {} (iter-v3/051 system-level REVERT; current state).
}
"""Per-symbol ATR multiplier overrides for iter-v3/032+ labeling architecture.

Maps symbol → (atr_tp_multiplier, atr_sl_multiplier).
Symbols absent from this dict fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).

iter-v3/032: LDOUSDT entry added (1.5, 0.75) — LDO natr_21_raw median 5.01 vs peer
  median 3.70 (1.35× higher); (1.5, 0.75) aligns LDO effective barriers with peer
  aggregate. Source: analysis/iteration_v3-032/per_symbol_atr_eda.py (SHA 9834e84).
iter-v3/040: CLEARED (empty dict). Cycle 3 EXPLORATION #1 — REVERT all per-symbol
  ATR customizations. LDO reverts to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) via fallback.
  Architecture (this dict + atr_multipliers_for_symbol helper) is KEPT; only emptied.
  Rationale: iter-v3/039 CONFIRMATION NO-MERGE — per-symbol customizations broke IS
  aggregate (-0.55 IS Sharpe swing from iter-v3/029 clean-4-symbol anchor).
iter-v3/044: ALGOUSDT entry added (2.0, 1.5) — QR EDA-driven per-symbol axis selection.
  ALGO LONG SL/TP asymmetry 4.5:1 with mean SL pnl_pct -5.24 (vs -8.40 stop barrier);
  widening SL by 50% gives ALGO longs more breathing room without changing entry signal.
  Source: analysis/iteration_v3-044/cycle3_is_diagnosis.py SHA `eff841e`.
iter-v3/045: LDOUSDT entry added (2.0, 1.5) — QR EDA-driven per-symbol axis selection,
  cycle 3 #6. LDO IS->OOS exit-composition shift (SL:TP 1.14 -> 2.33; SL rate 53.3%
  -> 63.6%); wider SL targets the IS->OOS regime-shift directly, mirroring iter-v3/044
  ALGO mechanism. Predecessor (1.5, 0.75) at iter-v3/032 was MULTI-SEED-FALSIFIED at
  iter-v3/039 — this is the OPPOSITE direction (wider not tighter) per QR EDA
  candidate-ranking. Source: analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py
  SHA `ed949fe`.
iter-v3/046: BCHUSDT entry added (2.0, 1.5) — QR EDA-driven per-symbol axis selection,
  cycle 3 #7. BCH direction asymmetry: LONG IS -25.07% (39 trades, 30.8% WR — toxic),
  SHORT IS +48.69% (55 trades, 43.6% WR). BCH IS=OOS SL:TP=1.93 (regime-stable, no
  IS->OOS shift) — wider SL helps IS AND OOS SYMMETRICALLY, distinct mechanism from
  iter-v3/045 LDO which addressed an asymmetric IS->OOS regime shift. Third application
  of validated wider-SL mechanism (ALGO at iter-v3/044, LDO at iter-v3/045, BCH at
  iter-v3/046). Source: analysis/iteration_v3-046/bch_trx_bottleneck_diagnosis.py
  SHA `d86b1f9`. RESULT: NEGATIVE — iter-v3/046 caused BCH IS-axis collapse (Δ -0.54
  IS Sharpe) + OOS -45 swing (BCH OOS PnL +10.75 → -34.54). Critic FINAL `5dae6d6`:
  mirror mechanism failed on stable-SL:TP symbols. Memory rule established: per-symbol
  ATR widening only applies to symbols with regime mismatch (IS->OOS SL:TP shift > 30%
  OR extreme direction asymmetry > 4:1).
iter-v3/047: BCHUSDT entry REMOVED — REVERT iter-v3/046 per Critic FINAL recommendation.
  BCH falls back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0). State after revert =
  iter-v3/045 config (ALGO + LDO entries only). The BCH IS-axis bottleneck (LONG IS
  -25% toxic / SHORT IS +49% positive) requires a DIRECTION-ASYMMETRIC mechanism, not
  a symmetric labeling-layer adjustment. iter-v3/047 axis = QR EDA-driven BCH direction
  axis (specific axis chosen by QR EDA at SHA TBD).
iter-v3/051: CLEARED (empty dict) — SYSTEM-LEVEL REVERT to iter-v3/028 architecture.
  Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` UPDATED 2026-05-10 (second-cycle
  confirmation of per-symbol-customization anti-pattern; iter-v3/039 + iter-v3/050 both
  CONFIRMATION-NO-MERGE on per-symbol bundle). ALGOUSDT and LDOUSDT entries REVERTED.
  All 3 symbols (BCH/LDO/TRX) fall back to DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0).
  Architecture (this dict + atr_multipliers_for_symbol helper) is KEPT; only emptied.
  Cycle 4 starting baseline = iter-v3/028 architecture exactly.
  Per analysis/iteration_v3-051/synthesis.md SHA `290f37b`.
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

Enforced by _verify_feature_columns in run_baseline_v3.py (iter-v3/044):
    len(V3_FEATURES_PER_SYMBOL) == 0  (empty — no per-symbol entries)
    "BCHUSDT" not in V3_FEATURES_PER_SYMBOL
    "ALGOUSDT" not in V3_FEATURES_PER_SYMBOL
    "LDOUSDT" not in V3_FEATURES_PER_SYMBOL
    "TRXUSDT" not in V3_FEATURES_PER_SYMBOL
    features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N  (15 features, no fracdiff, no ER)
    "fracdiff_d05_close" not in V3_FEATURE_COLUMNS_TOP_N
    "cross_asset_divergence_norm" not in V3_FEATURE_COLUMNS_TOP_N
    "vol_adj_autocorr" not in V3_FEATURE_COLUMNS_TOP_N
    "efficiency_ratio_50" not in V3_FEATURE_COLUMNS_TOP_N  (DROPPED iter-v3/044 revert)
    "regime_momentum_signed_3d" in V3_FEATURE_COLUMNS_TOP_N  (ADDED iter-v3/044)
    "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS_TOP_N  (PRESENT; mandate ACTIVE)
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
    - Any other symbol: fallback to 14-feature universal set

    V3_FEATURES_PER_SYMBOL is empty at iter-v3/040/041/042/043/044 (0 entries).
    All 4 symbols (BCH/LDO/TRX/ALGO) use the 15-feature universal fallback at iter-v3/044.
    iter-v3/041 temporarily pruned to 11 features; iter-v3/042 RESTORED to 14;
    iter-v3/043 ADDED efficiency_ratio_50 to reach 15 — DISASTROUS NEGATIVE;
    iter-v3/044 DROPPED efficiency_ratio_50 (reverted to 14) + ADDED
    regime_momentum_signed_3d (14 → 15).
    fracdiff_d05_close is NOT a model input for any symbol at iter-v3/040-044
    (column still computed in parquets but excluded from all feature_columns lists).

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
    "add_engineered_v3_features",
    "add_funding_v3_features",
    "atr_multipliers_for_symbol",
    "features_for_symbol",
    "generate_features_v3",
    "list_groups",
    "process_symbol_v3",
    "run_features_v3",
]
