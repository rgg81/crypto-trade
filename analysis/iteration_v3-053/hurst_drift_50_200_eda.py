"""iter-v3/053 — hurst_drift_50_200 NEW engineered feature EDA (cycle 4 #3 of 10).

Per Critic FINAL `34cc46f` of iter-v3/052 Recommendation #2 + iter-v3/050 closeout HIGH-priority
axis carry-forward, the cycle 4 #3 axis MUST pivot to a structurally distinct NEW feature
family per `feedback_v3_structural_over_knob_exploration.md` (Category 1 NEW feature family).

Top recommendation from /052 closeout: `hurst_drift_50_200` — UNTESTED engineered feature
named in /051 EDA candidate #4.

This EDA quantifies the AXIS for /053 and tests for the standard cycle-4 falsifiers:

  AXIS 1: hurst_drift_50_200 compute function (reconstructed from existing parquet columns)
          Formula: hurst_50 − hurst_200 (per /052 closeout EDA Axis 1 candidate; sign indicates
          regime-drift direction: positive = short-horizon trending stronger than long-horizon,
          mean-reversion entering; negative = long-horizon trending stronger, momentum
          building).

          CRITICAL EDA finding to test: hurst_50 = hurst_100 − hurst_diff_100_50 (algebraic
          rearrangement of the existing parquet derivation). Therefore:
              hurst_drift_50_200 = hurst_100 − hurst_diff_100_50 − hurst_200
          The new feature is a LINEAR COMBINATION of 3 existing V3_FEATURE_COLUMNS_TOP_N
          features (hurst_100, hurst_diff_100_50, hurst_200). Tree models can ALREADY
          express this combination via depth-3 splits on the 3 sources.

  AXIS 2: ADF stationarity per symbol (BCH, LDO, TRX). Expected stationary by construction
          (bounded difference of two bounded R/S Hurst measurements; standard Sinclair
          1986-style stationarity).

  AXIS 3: IC matrix vs existing 14 features (V3_FEATURE_COLUMNS_TOP_N minus regime_momentum_
          signed_3d which will be DROPPED at /053 setup; net 14-feature stack).

          Strict |IC|<0.70 gate per ITERATION_PLAN_8H_V3.md. Per `feedback_v3_engineered_
          feature_pivot.md`, Category 2 composed features get IC carve-out vs source primitives
          (here: hurst_100, hurst_200, hurst_diff_100_50). Track each carve-out invocation
          explicitly — multiple high-IC overlaps with source primitives is a structural
          REDUNDANCY warning even when carve-outs apply.

  AXIS 4: Univariate Spearman ρ vs forward 1-bar return per symbol. Compares effect size to
          regime_momentum_signed_5d baseline edge ingredient and hurst_diff_100_50 (the
          structurally similar feature already in V3_FEATURE_COLUMNS_TOP_N).

  AXIS 5: Linear-redundancy diagnostic — what split structure on (hurst_100, hurst_200,
          hurst_diff_100_50) reproduces hurst_drift_50_200 exactly? Quantify the additional
          information the feature would bring vs. tree models combining 3 sources at depth 3.

  AXIS 6: Per-symbol time-series properties: mean, std, skewness, kurtosis, autocorrelation.
          Sanity-check distribution shapes; flag if symbol-specific scaling is needed.

Inputs:
  - data/features_v3/{BCH,LDO,TRX,ALGO}_8h_features.parquet  (V3 feature parquets)

Outputs:
  - axis1_compute_and_distribution.csv  hurst_drift_50_200 distribution stats per symbol
  - axis2_adf_per_symbol.csv            ADF stationarity per symbol
  - axis3_ic_matrix.csv                 Full IC matrix vs existing 14 features
  - axis3_top_ic_pairs.csv              Top 10 |IC| pairs (carve-out check)
  - axis4_univariate_spearman.csv       Per-symbol univariate ρ vs forward 1-bar return
  - axis5_linear_redundancy.csv         Linear regression hurst_drift = a·H100 + b·HDIFF + c·H200
  - axis6_per_symbol_distribution.csv   Per-symbol mean/std/skew/kurt
  - synthesis.md                        Markdown summary + axis ranking
  - candidate_axes_ranking.md           Final ranking for /053 (sister doc)

Methodology mirror:
  - analysis/iteration_v3-051/axis_c_regime_3d_compute.py (regime feature on-the-fly EDA)
  - analysis/iteration_v3-051/axis_c_fracdiff_deep_dive.py (fracdiff IC + ADF + univariate)
  - analysis/iteration_v3-052/ldo_removal_eda.py (counterfactual + supersession structure)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.tsa.stattools import adfuller

ROOT = Path(__file__).resolve().parent.parent.parent
PARQUET_DIR = ROOT / "data" / "features_v3"
OUT_DIR = ROOT / "analysis" / "iteration_v3-053"
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00 UTC

# Current V3_FEATURE_COLUMNS_TOP_N at /052 head with regime_momentum_signed_3d (which
# will be DROPPED at /053 setup per /052 closeout). Net 14-feature stack for IC comparison:
EXISTING_14_FEATURES = [
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",  # SOURCE PRIMITIVE for hurst_drift_50_200
    "ret_kurt_200",
    "hurst_100",  # SOURCE PRIMITIVE for hurst_drift_50_200
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
    "regime_momentum_signed_5d",
]
# hurst_200 is NOT in V3_FEATURE_COLUMNS_TOP_N but IS in the parquet (computed by
# regime_v3.add_regime_v3_features). It IS a source primitive for hurst_drift_50_200.
HURST_DRIFT_SOURCE_PRIMITIVES = ["hurst_100", "hurst_diff_100_50", "hurst_200"]

SYMBOLS_3 = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
SYMBOLS_4 = ["BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT"]  # ALGO available for future re-inclusion


def load_features(symbol: str) -> pd.DataFrame:
    path = PARQUET_DIR / f"{symbol}_8h_features.parquet"
    df = pd.read_parquet(path)
    if "close_time" not in df.columns:
        # Some parquets use index for time; canonicalize
        df = df.reset_index()
    # Reconstruct hurst_50 from existing primitives (hurst_diff_100_50 = hurst_100 - hurst_50)
    df["hurst_50"] = df["hurst_100"] - df["hurst_diff_100_50"]
    # Compute the candidate feature
    df["hurst_drift_50_200"] = df["hurst_50"] - df["hurst_200"]
    # Forward 1-bar return for univariate test
    df["fwd_ret_1"] = np.log(df["close"]).diff().shift(-1)
    return df


def axis1_compute_and_distribution() -> pd.DataFrame:
    """Per-symbol distribution stats of hurst_drift_50_200 = hurst_50 - hurst_200."""
    rows = []
    for sym in SYMBOLS_4:
        df = load_features(sym)
        is_mask = df["close_time"] < OOS_CUTOFF_MS
        series = df.loc[is_mask, "hurst_drift_50_200"].dropna()
        rows.append({
            "symbol": sym,
            "n_is_obs": len(series),
            "mean": float(series.mean()),
            "std": float(series.std()),
            "min": float(series.min()),
            "p5": float(series.quantile(0.05)),
            "p25": float(series.quantile(0.25)),
            "median": float(series.median()),
            "p75": float(series.quantile(0.75)),
            "p95": float(series.quantile(0.95)),
            "max": float(series.max()),
            "skewness": float(stats.skew(series)),
            "kurtosis": float(stats.kurtosis(series)),
            "pct_negative": float((series < 0).sum() / len(series)),
            "pct_positive": float((series > 0).sum() / len(series)),
        })
    return pd.DataFrame(rows)


def axis2_adf_per_symbol() -> pd.DataFrame:
    """ADF stationarity per symbol on IS subset."""
    rows = []
    for sym in SYMBOLS_4:
        df = load_features(sym)
        is_mask = df["close_time"] < OOS_CUTOFF_MS
        series = df.loc[is_mask, "hurst_drift_50_200"].dropna()
        try:
            adf_result = adfuller(series, regression="c", autolag="AIC")
            adf_stat, adf_p = adf_result[0], adf_result[1]
        except Exception as exc:
            adf_stat, adf_p = float("nan"), float("nan")
            print(f"ADF failed for {sym}: {exc}")
        rows.append({
            "symbol": sym,
            "n_is_obs": len(series),
            "adf_stat": float(adf_stat),
            "adf_p_value": float(adf_p),
            "stationary_at_p005": bool(adf_p < 0.05) if not np.isnan(adf_p) else False,
        })
    return pd.DataFrame(rows)


def axis3_ic_matrix() -> tuple[pd.DataFrame, pd.DataFrame]:
    """IC matrix vs existing 14 features + hurst_200 source primitive.

    Returns:
      ic_matrix: rows = symbol, cols = existing features + hurst_200
      top_ic_pairs: top 10 |IC| pairs across all symbols
    """
    rows = []
    all_pairs = []
    # Also include hurst_200 in IC matrix (source primitive, not in V3_FEATURE_COLUMNS_TOP_N)
    features_for_ic = EXISTING_14_FEATURES + ["hurst_200"]
    for sym in SYMBOLS_4:
        df = load_features(sym)
        is_mask = df["close_time"] < OOS_CUTOFF_MS
        sub = df.loc[is_mask, ["hurst_drift_50_200"] + features_for_ic].dropna()
        if sub.empty:
            print(f"WARNING: no IS data for {sym} after dropna")
            continue
        row = {"symbol": sym, "n_is_obs": len(sub)}
        for feat in features_for_ic:
            if feat not in sub.columns:
                row[feat] = float("nan")
                continue
            ic = sub["hurst_drift_50_200"].corr(sub[feat], method="pearson")
            row[feat] = float(ic)
            all_pairs.append({
                "symbol": sym,
                "existing_feature": feat,
                "ic_pearson": float(ic),
                "abs_ic": float(abs(ic)) if not np.isnan(ic) else float("nan"),
                "is_source_primitive": feat in HURST_DRIFT_SOURCE_PRIMITIVES,
            })
        rows.append(row)
    ic_matrix = pd.DataFrame(rows)
    pairs_df = pd.DataFrame(all_pairs).sort_values("abs_ic", ascending=False).reset_index(drop=True)
    top_pairs = pairs_df.head(20)
    return ic_matrix, top_pairs


def axis4_univariate_spearman() -> pd.DataFrame:
    """Per-symbol Spearman ρ vs forward 1-bar return.

    Compares hurst_drift_50_200 to: regime_momentum_signed_5d (baseline edge), and
    hurst_diff_100_50 (sister Hurst-derived feature in feature set).
    """
    rows = []
    for sym in SYMBOLS_4:
        df = load_features(sym)
        is_mask = df["close_time"] < OOS_CUTOFF_MS
        cmp_cols = ["hurst_drift_50_200", "regime_momentum_signed_5d", "hurst_diff_100_50", "hurst_100"]
        sub = df.loc[is_mask, cmp_cols + ["fwd_ret_1"]].dropna()
        if sub.empty:
            continue
        for col in cmp_cols:
            rho, p = stats.spearmanr(sub[col], sub["fwd_ret_1"])
            rows.append({
                "symbol": sym,
                "feature": col,
                "n_obs": len(sub),
                "spearman_rho": float(rho),
                "spearman_p": float(p),
                "significant_at_p005": bool(p < 0.05),
            })
    return pd.DataFrame(rows)


def axis5_linear_redundancy() -> pd.DataFrame:
    """Linear regression: hurst_drift = a·H100 + b·HDIFF + c·H200 + intercept.

    By construction, the candidate feature equals exactly:
        hurst_drift_50_200 = hurst_100 - hurst_diff_100_50 - hurst_200

    So R² should be ~1.0 with coefficients (a, b, c) ≈ (1, -1, -1). This documents
    the LINEAR REDUNDANCY: a tree model using (H100, HDIFF, H200) as features can
    express the same linear combination by composing splits at depth 3. The
    composed feature provides NO NEW information that the 3 primitives don't carry.
    """
    rows = []
    for sym in SYMBOLS_4:
        df = load_features(sym)
        is_mask = df["close_time"] < OOS_CUTOFF_MS
        sub = df.loc[is_mask, HURST_DRIFT_SOURCE_PRIMITIVES + ["hurst_drift_50_200"]].dropna()
        if sub.empty:
            continue
        X = sub[HURST_DRIFT_SOURCE_PRIMITIVES].to_numpy()
        y = sub["hurst_drift_50_200"].to_numpy()
        # OLS without intercept (we expect zero intercept by construction)
        X_with_const = np.column_stack([np.ones(len(X)), X])
        beta, _, _, _ = np.linalg.lstsq(X_with_const, y, rcond=None)
        y_pred = X_with_const @ beta
        residuals = y - y_pred
        ss_res = (residuals ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
        rows.append({
            "symbol": sym,
            "n_is_obs": len(sub),
            "intercept": float(beta[0]),
            "coef_hurst_100": float(beta[1]),
            "coef_hurst_diff_100_50": float(beta[2]),
            "coef_hurst_200": float(beta[3]),
            "r_squared": float(r2),
            "rmse": float(np.sqrt(ss_res / len(sub))),
            "max_abs_residual": float(np.abs(residuals).max()),
        })
    return pd.DataFrame(rows)


def axis6_per_symbol_distribution() -> pd.DataFrame:
    """Compare hurst_drift_50_200 distribution to source primitives per symbol."""
    rows = []
    for sym in SYMBOLS_4:
        df = load_features(sym)
        is_mask = df["close_time"] < OOS_CUTOFF_MS
        for col in ["hurst_drift_50_200", "hurst_100", "hurst_200", "hurst_diff_100_50"]:
            series = df.loc[is_mask, col].dropna()
            if series.empty:
                continue
            rows.append({
                "symbol": sym,
                "feature": col,
                "n_obs": len(series),
                "mean": float(series.mean()),
                "std": float(series.std()),
                "skewness": float(stats.skew(series)),
                "kurtosis": float(stats.kurtosis(series)),
                "autocorr_lag1": float(series.autocorr(lag=1)) if len(series) > 1 else float("nan"),
            })
    return pd.DataFrame(rows)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== AXIS 1: hurst_drift_50_200 distribution stats per symbol ===")
    a1 = axis1_compute_and_distribution()
    a1.to_csv(OUT_DIR / "axis1_compute_and_distribution.csv", index=False)
    print(a1.to_string(index=False))
    print()

    print("=== AXIS 2: ADF stationarity per symbol (IS subset) ===")
    a2 = axis2_adf_per_symbol()
    a2.to_csv(OUT_DIR / "axis2_adf_per_symbol.csv", index=False)
    print(a2.to_string(index=False))
    print()

    print("=== AXIS 3: IC matrix vs existing 14 features + hurst_200 source primitive ===")
    a3_matrix, a3_top = axis3_ic_matrix()
    a3_matrix.to_csv(OUT_DIR / "axis3_ic_matrix.csv", index=False)
    a3_top.to_csv(OUT_DIR / "axis3_top_ic_pairs.csv", index=False)
    print("Per-symbol max |IC|:")
    print(a3_matrix.set_index("symbol").drop(columns=["n_is_obs"]).abs().max(axis=1))
    print()
    print("Top 20 |IC| pairs across all symbols:")
    print(a3_top.head(20).to_string(index=False))
    print()

    print("=== AXIS 4: Univariate Spearman ρ vs forward 1-bar return ===")
    a4 = axis4_univariate_spearman()
    a4.to_csv(OUT_DIR / "axis4_univariate_spearman.csv", index=False)
    print(a4.to_string(index=False))
    print()

    print("=== AXIS 5: Linear redundancy diagnostic ===")
    a5 = axis5_linear_redundancy()
    a5.to_csv(OUT_DIR / "axis5_linear_redundancy.csv", index=False)
    print(a5.to_string(index=False))
    print()

    print("=== AXIS 6: Per-symbol distribution stats ===")
    a6 = axis6_per_symbol_distribution()
    a6.to_csv(OUT_DIR / "axis6_per_symbol_distribution.csv", index=False)
    print(a6.to_string(index=False))
    print()

    print("DONE. CSV outputs at:", OUT_DIR)


if __name__ == "__main__":
    main()
