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
    "ret_skew_50",  # rank 10 (mean 12.5) — tail_risk
    "vwap_dev_20",  # rank 11 (mean 13.0) — volume_micro
    "ret_autocorr_lag1_50",  # rank 12 (mean 13.5) — momentum_accel
    "sym_vs_btc_ret_7d",  # rank 13 (mean 14.5) — cross_btc
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
    "regime_momentum_signed_5d",  # rank TBD — engineered_v3 (Category 2 composed feature)
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
)
"""Top-14 feature subset: iter-v3/028 drop — cross_asset_divergence_norm removed
(revert 15→14; matches iter-v3/025 anchor exactly). iter-v3/027 was: atomic swap
vol_adj_autocorr dropped, cross_asset_divergence_norm added.

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
"""

V3_NON_FEATURE_COLUMNS: tuple[str, ...] = ("natr_21_raw", "tbr_raw")
"""Columns computed by the v3 pipeline that are NOT model inputs.

``natr_21_raw``: raw NATR used for dynamic ATR barriers (not a signal feature).
``tbr_raw``:     raw tick-bar ratio before z-score normalization; Critic
                 Clarification 4 of iter-v3/015 identified this as excluded from
                 model input regardless (added iter-v3/016, §3.5 sub-fix #2).
"""

V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]] = {
    # iter-v3/030: LDO per-symbol 7-feature subset.
    # Source: analysis/iteration_v3-030/ldo_feature_subset_analysis.py (SHA 36aaacd).
    # Top-7 by iter-v3/028 multi-seed IS importance (canonical multi-seed BASELINE read-out).
    # BCH+TRX+ALGO are NOT listed here — they fall back to V3_FEATURE_COLUMNS_TOP_N (14 features).
    # NEVER add a feature here that is absent from V3_FEATURE_COLUMNS_TOP_N.
    "LDOUSDT": (
        "ret_skew_200",
        "ret_kurt_50",
        "ret_kurt_200",
        "vwap_dev_20",
        "hurst_diff_100_50",
        "btc_ret_14d",
        "range_realized_vol_50",
    ),
}
"""Per-symbol feature subsets for v3 models (iter-v3/030+).

Maps symbol → tuple of feature column names to pass to LightGbmStrategy.
Symbols absent from this dict fall back to V3_FEATURE_COLUMNS_TOP_N (14 features).

Invariant (enforced by _verify_feature_columns in run_baseline_v3.py and by the
adversarial test tests/features_v3/test_features_for_symbol.py):
    every tuple in V3_FEATURES_PER_SYMBOL.values() is a strict subset of
    V3_FEATURE_COLUMNS_TOP_N.
"""


def features_for_symbol(symbol: str) -> tuple[str, ...]:
    """Return per-symbol feature tuple, falling back to V3_FEATURE_COLUMNS_TOP_N.

    Introduced in iter-v3/030 to support per-symbol model heterogeneity.
    LDO returns its 7-feature top-7 from iter-v3/028 multi-seed importance.
    BCH, TRX, ALGO, and any other symbol not in V3_FEATURES_PER_SYMBOL get
    the full 14-feature V3_FEATURE_COLUMNS_TOP_N.

    Callers MUST pass ``feature_columns=list(features_for_symbol(symbol))``
    to LightGbmStrategy — never None, never empty, never the global default.
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
)
"""Symbols traded by v1 or v2. v3 runners MUST exclude these at startup."""


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
    "GROUP_REGISTRY",
    "V3_EXCLUDED_SYMBOLS",
    "V3_FEATURE_COLUMNS",
    "V3_FEATURE_COLUMNS_FULL",
    "V3_FEATURE_COLUMNS_TOP_N",
    "V3_FEATURES_PER_SYMBOL",
    "V3_NON_FEATURE_COLUMNS",
    "add_btc_funding_v3_features",
    "add_engineered_v3_features",
    "add_funding_v3_features",
    "features_for_symbol",
    "generate_features_v3",
    "list_groups",
    "process_symbol_v3",
    "run_features_v3",
]
