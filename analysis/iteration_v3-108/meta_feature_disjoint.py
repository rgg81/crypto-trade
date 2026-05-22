"""iter-v3/108 — Gating EDA Script 1 of 2.

Constructs the candidate DISJOINT meta-feature set for the meta-labeling
secondary model (M2) and machine-checks two properties versus the 14
primary features in `V3_FEATURE_COLUMNS`:

  (G1) ZERO column-name overlap   — the /017-correction, hard.
  (G2) LOW aggregate redundancy   — max |Pearson rho| between any meta-feature
       and any primary feature, measured on the IS feature rows.

This is the F-DISJOINT falsifier: if a genuinely disjoint, non-redundant
secondary feature set cannot be assembled, the axis is NO-GO before any build.

STRICTLY IS-ONLY. Every feature row entering any computation has
`close_time < OOS_CUTOFF_MS`. The post-cutoff OOS feature data is never read.

Outputs (committed):
  T1_meta_feature_catalog.csv   — the disjoint meta-feature set + family + rationale
  T2_overlap_check.csv          — G1: name-overlap audit vs V3_FEATURE_COLUMNS
  T3_redundancy_matrix.csv      — G2: |rho| of each meta-feature vs each primary feature
  T3b_redundancy_summary.csv    — G2: per-meta-feature max |rho| vs the primary stack
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

# --- sacred constant -------------------------------------------------------
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 ; IMMUTABLE

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
FEAT_DIR = REPO / "data" / "features_v3"
V3_SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]

# The 14 primary features the primary LightGBM (M1) trains on — /059 spec,
# BASELINE_V3.md "Code Configuration". M2 must share ZERO columns with this.
V3_FEATURE_COLUMNS = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
)

# --- candidate DISJOINT meta-feature set -----------------------------------
# Design principle (the /017-correction): the meta-feature set answers
# "is this a HARD call to make" (the precision residual), NOT "which way price
# goes" (the directional signal the primary model already extracts).
#
# Every column below is verified present in the 85-column features_v3 parquet
# and verified NOT in V3_FEATURE_COLUMNS. Each is causal — bar t uses only
# data <= t (the feature pipeline is the production pipeline; all features are
# trailing-window).
#
# (entropy / 5-seed ensemble-disagreement is NOT included here because it
#  requires retraining the 10-seed ensemble to reconstruct per-bar inference
#  predictions — a QE Phase 6 task, not reconstructable from /059 artifacts.
#  It is carried into the brief as a CANDIDATE M2 feature; this EDA establishes
#  the GO/NO-GO from the parquet-derivable disjoint set, the conservative test.)
#
# PRUNING PASS (the /017-correction enforced): the first-pass 22-candidate set
# had 4 features with max|rho| > 0.70 vs the primary stack — they MEASURE the
# same thing the primary already sees, which is exactly the /017 redundancy
# failure. They are DROPPED here so the secondary model trains only on genuinely
# orthogonal information:
#   close_pos_in_range_20  rho=0.91 vs vwap_dev_20            DROPPED
#   hurst_drift_50_200     rho=0.87 vs hurst_diff_100_50      DROPPED
#   sym_vs_btc_vol_14d     rho=0.76 vs range_realized_vol_50  DROPPED
#   candle_efficiency_20   rho=0.72 vs vwap_dev_20            DROPPED
# The retained 18 have max|rho| = 0.57 (volume_cv_50 vs ret_kurt_50) < 0.70.
META_FEATURE_CATALOG = [
    # family A — regime context the 14-feature primary stack under-weights
    ("hurst_200", "regime", "Hurst at 200-bar lookback; primary uses hurst_100/diff only"),
    ("adx_14", "regime", "Wilder trend-strength; a gate input, not an M1 feature"),
    ("btc_vol_14d", "regime", "BTC realized vol regime; primary uses btc_ret only"),
    ("cross_asset_divergence_norm", "regime", "normalized cross-asset divergence"),
    ("vol_regime_x_momentum", "regime", "vol-regime x momentum interaction"),
    ("vol_transition_slope_20", "regime", "vol-regime transition slope (regime change rate)"),
    # family B — volatility / dispersion state ("how noisy is right now")
    ("atr_pct_rank_200", "vol_state", "ATR percentile rank; dispersion regime"),
    ("bb_width_pct_rank_100", "vol_state", "Bollinger-width percentile rank"),
    ("parkinson_gk_ratio_20", "vol_state", "Parkinson/Garman-Klass ratio (jump-vs-diffusion)"),
    ("volume_cv_50", "vol_state", "volume coefficient of variation (flow stability)"),
    ("range_efficiency_50", "vol_state", "range efficiency (trendiness of the path)"),
    # family C — microstructure / order-flow context (M1 sees none of this)
    ("taker_buy_imbalance_20", "microstructure", "taker buy/sell imbalance"),
    ("obv_slope_50", "microstructure", "on-balance-volume slope"),
    # family D — funding / derivative context (crypto-native; M1 sees none)
    ("funding_rate_zscore_30", "funding", "funding-rate z-score (positioning crowding)"),
    ("funding_sign_persist_9", "funding", "funding-sign persistence (regime crowding)"),
    ("basis_zscore_30", "funding", "perp-spot basis z-score"),
    # family E — calendar context ("what kind of bar is this")
    ("candle_dow_sin", "calendar", "day-of-week sine encoding"),
    ("candle_dow_cos", "calendar", "day-of-week cosine encoding"),
]


def load_is_features() -> pd.DataFrame:
    """Concatenate IS-only feature rows across the 3 v3 symbols."""
    frames = []
    for sym in V3_SYMBOLS:
        path = FEAT_DIR / f"{sym}_8h_features.parquet"
        df = pd.read_parquet(path)
        # IS-ONLY INVARIANT — hard assert.
        df = df[df["close_time"] < OOS_CUTOFF_MS].copy()
        assert (df["close_time"] < OOS_CUTOFF_MS).all(), f"{sym}: OOS leak"
        df["symbol"] = sym
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    print(f"[load] IS feature rows: {len(out)} across {V3_SYMBOLS}")
    print(f"[load] close_time max = {out['close_time'].max()} < {OOS_CUTOFF_MS} (cutoff)")
    return out


def main() -> int:
    feats = load_is_features()
    available = set(feats.columns)

    meta_cols = [c for c, _, _ in META_FEATURE_CATALOG]
    primary_cols = list(V3_FEATURE_COLUMNS)

    # ---- catalog table ----------------------------------------------------
    cat_rows = []
    for col, family, rationale in META_FEATURE_CATALOG:
        present = col in available
        cat_rows.append(
            {
                "meta_feature": col,
                "family": family,
                "rationale": rationale,
                "present_in_parquet": present,
            }
        )
    cat = pd.DataFrame(cat_rows)
    cat.to_csv(OUT / "T1_meta_feature_catalog.csv", index=False)
    missing = cat[~cat["present_in_parquet"]]["meta_feature"].tolist()
    if missing:
        print(f"[FATAL] meta-features absent from parquet: {missing}")
        return 1
    print(f"[T1] meta-feature catalog: {len(cat)} features, all present in parquet")

    # ---- G1: zero name-overlap (the /017-correction) ---------------------
    overlap = sorted(set(meta_cols) & set(primary_cols))
    ovr_rows = []
    for col in meta_cols:
        ovr_rows.append(
            {
                "meta_feature": col,
                "in_V3_FEATURE_COLUMNS": col in primary_cols,
            }
        )
    ovr = pd.DataFrame(ovr_rows)
    ovr.to_csv(OUT / "T2_overlap_check.csv", index=False)
    g1_pass = len(overlap) == 0
    print(f"[T2] G1 name-overlap: {len(overlap)} overlapping columns -> "
          f"{'PASS (disjoint)' if g1_pass else f'FAIL {overlap}'}")

    # ---- G2: redundancy matrix (|Pearson rho| on IS rows) ----------------
    # NaN rows dropped pairwise; rho on the common-support window.
    rho_rows = []
    summary_rows = []
    for m in meta_cols:
        max_abs = 0.0
        argmax = None
        for p in primary_cols:
            pair = feats[[m, p]].dropna()
            if len(pair) < 200:
                rho = np.nan
            else:
                rho = pair[m].corr(pair[p])
            rho_rows.append(
                {"meta_feature": m, "primary_feature": p, "abs_rho": abs(rho)}
            )
            if pd.notna(rho) and abs(rho) > max_abs:
                max_abs = abs(rho)
                argmax = p
        summary_rows.append(
            {
                "meta_feature": m,
                "max_abs_rho_vs_primary": round(max_abs, 4),
                "most_correlated_primary": argmax,
            }
        )
    rho_df = pd.DataFrame(rho_rows)
    rho_df["abs_rho"] = rho_df["abs_rho"].round(4)
    rho_df.to_csv(OUT / "T3_redundancy_matrix.csv", index=False)
    summ = pd.DataFrame(summary_rows).sort_values(
        "max_abs_rho_vs_primary", ascending=False
    )
    summ.to_csv(OUT / "T3b_redundancy_summary.csv", index=False)

    worst = summ.iloc[0]
    redundancy_gate = 0.70  # v3 IC < 0.7 family-redundancy convention
    g2_pass = worst["max_abs_rho_vs_primary"] < redundancy_gate
    print(f"[T3b] G2 redundancy: worst meta-feature = {worst['meta_feature']} "
          f"max|rho|={worst['max_abs_rho_vs_primary']} vs "
          f"{worst['most_correlated_primary']}")
    print(f"[T3b] G2 redundancy gate (<{redundancy_gate}): "
          f"{'PASS' if g2_pass else 'FAIL'}")

    # ---- F-DISJOINT verdict ----------------------------------------------
    print()
    print("=" * 64)
    print("F-DISJOINT falsifier:")
    print(f"  G1 zero name-overlap : {'PASS' if g1_pass else 'FAIL'}")
    print(f"  G2 low redundancy    : {'PASS' if g2_pass else 'FAIL'}")
    if g1_pass and g2_pass:
        print(f"  -> F-DISJOINT does NOT fire. {len(meta_cols)} disjoint, "
              f"non-redundant meta-features assembled.")
    else:
        print("  -> F-DISJOINT FIRES. Disjoint set could not be assembled. NO-GO.")
    print("=" * 64)
    return 0


if __name__ == "__main__":
    sys.exit(main())
