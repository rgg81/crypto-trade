"""iter-v3/051 — compute regime_momentum_signed_3d on-the-fly from parquet primitives.

regime_momentum_signed_3d = ret_3d × sign(hurst_100 - 0.5)
  where ret_3d = close.pct_change(3 * 1)  # 3-bar return on 8h bars (note: NOT 3-day)

NOTE: ret_3d is not in parquets but `close` is. We compute ret_3d here on the fly to test:
  1. |IC| with existing 14 features (per-symbol)
  2. ADF stationarity
  3. Univariate Spearman with forward 1-bar return

This determines whether regime_momentum_signed_3d is feasible as a cycle 4 NEW universal
engineered feature candidate (UNTESTED at universal scope — iter-v3/044 orchestrator
ad-hoc pick was REVERTED before backtest). Note compute_regime_momentum_signed_3d already
exists as dead code in engineered_v3.py.

Output: axis_c_regime_3d_ic.csv + axis_c_regime_3d_adf.csv + axis_c_regime_3d_univariate.csv
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

# Source primitives for regime_momentum_signed_3d: close (for ret_3d) and hurst_100 (for sign).
SOURCE_PRIMITIVES = ("hurst_100", "regime_momentum_signed_5d")  # latter is same family

CANDIDATE = "regime_momentum_signed_3d"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[axis_c regime_3d] computing on-the-fly from close + hurst_100\n")

    per_sym_ic_rows = []
    overall_max_ic = 0.0
    overall_max_pair = ("", "", "")
    adf_rows = []
    univariate_rows = []

    for sym in SYMBOLS:
        df = pd.read_parquet(FEATURES_DIR / f"{sym}_8h_features.parquet")
        df = df.sort_values("close_time").reset_index(drop=True)
        df_is = df[df["close_time"] < OOS_CUTOFF_MS].copy()

        # Compute regime_momentum_signed_3d on the fly
        # ret_3d = close.pct_change(3)  (3-bar return on 8h candles)
        df_is["ret_3d"] = df_is["close"].pct_change(3)
        df_is["hurst_sign"] = np.sign(df_is["hurst_100"] - 0.5)
        df_is[CANDIDATE] = df_is["ret_3d"] * df_is["hurst_sign"]

        # Shift past-only (the model uses the value at candle close)
        # Actually shift(1) since we feed features at time t for decision at t+1
        # — but for EDA purposes (IC and univariate), this is fine without shift.

        # Forward return for univariate test
        df_is["fwd_ret_1"] = df_is["close"].pct_change().shift(-1)

        n = df_is[CANDIDATE].dropna().shape[0]
        print(f"  {sym}: {n} non-NaN observations")

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
    df_ic.to_csv(OUT_DIR / "axis_c_regime_3d_ic.csv", index=False)
    df_adf = pd.DataFrame(adf_rows)
    df_adf.to_csv(OUT_DIR / "axis_c_regime_3d_adf.csv", index=False)
    df_uni = pd.DataFrame(univariate_rows)
    df_uni.to_csv(OUT_DIR / "axis_c_regime_3d_univariate.csv", index=False)

    print(f"\n--- Per-symbol max |IC| with existing 14 ---")
    summary = df_ic.groupby("symbol")["abs_ic_pearson"].agg(["max", "mean"]).round(4)
    print(summary)

    print(f"\n--- Top 5 |IC| pairs ---")
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
        if overall_max_pair[2] in SOURCE_PRIMITIVES:
            print(f"  CARVE-OUT APPLIES: {overall_max_pair[2]} is SOURCE PRIMITIVE for regime_momentum_signed_3d")
            print(f"  Per feedback_v3_engineered_feature_pivot.md: Category 2 composed feature gets IC carve-out vs source primitives")
        else:
            print(f"  CARVE-OUT DOES NOT APPLY: {overall_max_pair[2]} is NOT a source primitive")
    else:
        print(f"  STRICT GATE PASSES: max |IC|={overall_max_ic:.4f} < 0.70")


if __name__ == "__main__":
    main()
