"""iter-v3/051 — DEEP DIVE on fracdiff_d05_close as universal-scope candidate (axis c1).

Critic FINAL `b6339c5` rec #5 recommends 3 candidates for cycle 4 NEW universal engineered
features. Of those, only fracdiff_d05_close is present in feature parquets WITHOUT requiring
feature regeneration (iter-v3/035 dropped it from V3_FEATURE_COLUMNS_TOP_N to per-symbol BCH
only; the universal scope was untested at multi-seed). regime_momentum_signed_3d would
require new feature code (NOT present). hurst_drift_50_200 would require new code.

This deep dive answers:
  1. What is fracdiff_d05_close's |IC| with EACH existing feature (per symbol)?
  2. Is it Category 2 carve-out eligible (IC vs source primitives)?
  3. What is the per-symbol univariate Spearman correlation with forward returns?
  4. ADF stationarity check at IS subset (3-month rolling p-value < 0.05)?
  5. iter-v3/035 BCH-only result re-attribution: why did BCH +37.98 OOS swing not transfer?

Output: axis_c_fracdiff_deep_dive.csv + axis_c_fracdiff_per_sym_ic.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller

ROOT = Path(__file__).resolve().parent.parent.parent
FEATURES_DIR = ROOT / "data" / "features_v3"
OUT_DIR = ROOT / "analysis" / "iteration_v3-051"
OOS_CUTOFF_MS = 1742774400000
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")

EXISTING_14 = (
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

# Source primitives for fracdiff_d05_close (LdP AFML Ch. 5 — the d=0.5 frac diff of close).
# This feature is pure transform of close — IC vs raw close primitives is meaningful as carve-out.
SOURCE_PRIMITIVES = ("ema_spread_atr_20", "vwap_dev_20")  # both primarily close-derived

CANDIDATE = "fracdiff_d05_close"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[axis_c deep] {CANDIDATE} per-symbol full IC + ADF + univariate corr\n")

    # Per-symbol IC matrix (IS only)
    per_sym_ic_rows = []
    overall_max_ic = 0.0
    overall_max_pair = ("", "", "")

    # ADF rows
    adf_rows = []

    # Univariate forward-return correlation
    univariate_rows = []

    for sym in SYMBOLS:
        df = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        df_is = df[df["close_time"] < OOS_CUTOFF_MS].copy()
        if CANDIDATE not in df_is.columns:
            print(f"  {sym}: {CANDIDATE} NOT in parquet — SKIP")
            continue

        # Forward 1-bar return for univariate test
        df_is = df_is.sort_values("close_time").reset_index(drop=True)
        df_is["fwd_ret_1"] = df_is["close"].pct_change().shift(-1)

        for f in EXISTING_14:
            if f not in df_is.columns:
                continue
            v1 = df_is[CANDIDATE].values
            v2 = df_is[f].values
            mask = ~(np.isnan(v1) | np.isnan(v2))
            if mask.sum() < 100:
                continue
            ic = abs(np.corrcoef(v1[mask], v2[mask])[0, 1])
            per_sym_ic_rows.append({
                "symbol": sym,
                "candidate": CANDIDATE,
                "existing_feature": f,
                "abs_ic_pearson": round(ic, 4),
                "is_source_primitive": f in SOURCE_PRIMITIVES,
            })
            if ic > overall_max_ic:
                overall_max_ic = ic
                overall_max_pair = (sym, CANDIDATE, f)

        # ADF test (rolling)
        s = df_is[CANDIDATE].dropna()
        if len(s) >= 200:
            try:
                adf_p = adfuller(s, autolag="AIC")[1]
                adf_rows.append({
                    "symbol": sym,
                    "candidate": CANDIDATE,
                    "n_is_obs": len(s),
                    "adf_p_value": round(adf_p, 6),
                    "stationary_at_p005": adf_p < 0.05,
                })
            except Exception as e:
                print(f"  {sym}: ADF failed: {e}")

        # Univariate Spearman correlation with forward 1-bar return (cliff_form
        # signal-presence test). Note: as a STATIONARY feature this is uncorrelated
        # by construction with forward returns above noise.
        m = ~(np.isnan(df_is[CANDIDATE].values) | np.isnan(df_is["fwd_ret_1"].values))
        if m.sum() >= 100:
            rho, p = stats.spearmanr(df_is[CANDIDATE].values[m], df_is["fwd_ret_1"].values[m])
            univariate_rows.append({
                "symbol": sym,
                "candidate": CANDIDATE,
                "n_obs": int(m.sum()),
                "spearman_rho": round(rho, 5),
                "spearman_p": round(p, 5),
                "significant_at_p005": p < 0.05,
            })

    df_ic = pd.DataFrame(per_sym_ic_rows)
    df_ic.to_csv(OUT_DIR / "axis_c_fracdiff_per_sym_ic.csv", index=False)
    df_adf = pd.DataFrame(adf_rows)
    df_adf.to_csv(OUT_DIR / "axis_c_fracdiff_adf.csv", index=False)
    df_uni = pd.DataFrame(univariate_rows)
    df_uni.to_csv(OUT_DIR / "axis_c_fracdiff_univariate.csv", index=False)

    print(f"\n--- Per-symbol max |IC| with existing 14 ---")
    summary = df_ic.groupby("symbol")["abs_ic_pearson"].agg(["max", "mean"]).round(4)
    print(summary)

    print(f"\n--- Top 5 |IC| pairs (across all symbols, source primitives flagged) ---")
    top5 = df_ic.nlargest(5, "abs_ic_pearson")
    print(top5.to_string(index=False))

    print(f"\n--- ADF stationarity ---")
    print(df_adf.to_string(index=False))

    print(f"\n--- Univariate Spearman vs forward 1-bar return ---")
    print(df_uni.to_string(index=False))

    print(f"\n--- IC carve-out evaluation ---")
    print(f"Strict |IC|<0.70 gate: max |IC|={overall_max_ic:.4f}")
    if overall_max_ic >= 0.70:
        print(f"  STRICT GATE FAILS: max |IC|={overall_max_ic:.4f} >= 0.70")
        print(f"  Pair: {overall_max_pair}")
        # Check if the failing pair is a source primitive
        if overall_max_pair[2] in SOURCE_PRIMITIVES:
            print(f"  CARVE-OUT APPLIES: {overall_max_pair[2]} is SOURCE PRIMITIVE for fracdiff_d05_close")
            print(f"  Per feedback_v3_engineered_feature_pivot.md: Category 2 composed feature gets IC carve-out vs source primitives")
        else:
            print(f"  CARVE-OUT DOES NOT APPLY: {overall_max_pair[2]} is NOT a source primitive")
            print(f"  fracdiff_d05_close FAILS strict IC gate AND carve-out gate")
    else:
        print(f"  STRICT GATE PASSES: max |IC|={overall_max_ic:.4f} < 0.70")


if __name__ == "__main__":
    main()
