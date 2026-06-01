"""iter-v1/034 Phase 2 — basis (perp-spot) z-score EDA on IS-only window.

Feature definition (canonical):
    basis_bps[t]            = (perp_close[t] - spot_close[t]) / spot_close[t] * 1e4
    basis_zscore_30[t]      = (basis_bps[t] - mean(basis_bps[t-30..t-1])) /
                               std(basis_bps[t-30..t-1])

Past-only discipline: rolling stats use shift(1) — same convention as funding_v1.

Outputs (committed to analysis/iteration_v1-034/):
  1. distribution_per_symbol.csv   — IS-only distribution stats
  2. ic_vs_pruned_features.csv     — Pearson IC vs each V1_FEATURE_COLUMNS_PRUNED
  3. adf_stationarity.csv          — ADF test on basis_zscore_30 per symbol
  4. quintile_trade_attribution.csv — Per-quintile baseline-trade outcome
  5. signed_pnl_pearson.csv        — Per-symbol Pearson with signed_pnl_pct

Run from worktree root:
    uv run python analysis/iteration_v1-034/basis_zscore_eda.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from statsmodels.tsa.stattools import adfuller

V1_SYMBOLS = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
DATA_DIR = Path("data")
OUT_DIR = Path("analysis/iteration_v1-034")
IS_START_MS = 1577836800000  # 2020-01-01 — full IS window
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24

# Feature parameters (canonical)
BASIS_ZSCORE_WINDOW = 30  # 30 bars (~10 days) — matches funding_v1 short window

# Pruned feature columns (43; copied verbatim from features_v1/__init__.py)
V1_FEATURE_COLUMNS_PRUNED = (
    "cal_dow_norm",
    "cal_hour_norm",
    "funding_rate_zscore_30",
    "funding_rate_zscore_90",
    "interact_natr_x_adx",
    "interact_ret1_x_natr",
    "interact_ret1_x_ret3",
    "interact_rsi_x_adx",
    "interact_rsi_x_natr",
    "interact_stoch_x_adx",
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
    "oi_delta_30_z90",
    "stat_autocorr_lag5",
    "stat_kurtosis_20",
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


def compute_basis_zscore(perp_path: Path, spot_path: Path, window: int) -> pd.DataFrame:
    """Past-only basis z-score on aligned perp+spot closes."""
    perp = pd.read_csv(perp_path)[["open_time", "close"]].rename(columns={"close": "perp"})
    spot = pd.read_csv(spot_path)[["open_time", "close"]].rename(columns={"close": "spot"})
    merged = perp.merge(spot, on="open_time", how="inner").sort_values("open_time").reset_index(drop=True)
    merged["basis_bps"] = (merged["perp"] - merged["spot"]) / merged["spot"] * 10_000.0
    # past-only z-score
    s = merged["basis_bps"].astype(float)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)
    merged["basis_zscore_30"] = ((s - rmean) / rstd.replace(0, np.nan)).clip(-10.0, 10.0)
    return merged


def main() -> None:
    print("\n=== iter-v1/034 Phase 2 EDA — basis_zscore_30 ===\n")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Compute basis feature per symbol (IS-only)
    # ------------------------------------------------------------------
    basis_by_sym: dict[str, pd.DataFrame] = {}
    for sym in V1_SYMBOLS:
        perp_p = DATA_DIR / sym / "8h.csv"
        spot_p = DATA_DIR / "spot" / sym / "8h.csv"
        bdf = compute_basis_zscore(perp_p, spot_p, BASIS_ZSCORE_WINDOW)
        bdf_is = bdf[(bdf["open_time"] >= IS_START_MS) & (bdf["open_time"] < OOS_CUTOFF_MS)].copy()
        basis_by_sym[sym] = bdf_is

    # ------------------------------------------------------------------
    # 1. Distribution per symbol
    # ------------------------------------------------------------------
    dist_rows = []
    for sym, bdf in basis_by_sym.items():
        z = bdf["basis_zscore_30"].dropna()
        bp = bdf["basis_bps"].dropna()
        dist_rows.append({
            "symbol": sym,
            "rows_IS": len(bdf),
            "valid_z_IS": int(z.notna().sum()),
            "z_mean": round(z.mean(), 4),
            "z_std": round(z.std(), 4),
            "z_skew": round(z.skew(), 3),
            "z_kurt": round(z.kurt(), 3),
            "z_p01": round(z.quantile(0.01), 3),
            "z_p99": round(z.quantile(0.99), 3),
            "z_abs_pct_above_2": round((z.abs() > 2).mean() * 100, 2),
            "raw_basis_mean_bps": round(bp.mean(), 2),
            "raw_basis_std_bps": round(bp.std(), 2),
        })
    dist_df = pd.DataFrame(dist_rows)
    dist_df.to_csv(OUT_DIR / "distribution_per_symbol.csv", index=False)
    print("1. Distribution per symbol (IS-only):\n")
    print(dist_df.to_string(index=False))

    # ------------------------------------------------------------------
    # 2. Cross-correlation (Pearson) with each V1_FEATURE_COLUMNS_PRUNED feature
    # ------------------------------------------------------------------
    print("\n\n2. Pearson IC vs V1_FEATURE_COLUMNS_PRUNED (per symbol):\n")
    ic_records = []
    for sym in V1_SYMBOLS:
        bdf = basis_by_sym[sym]
        # load features parquet IS window
        feat_path = DATA_DIR / "features" / f"{sym}_8h_features.parquet"
        feat = pd.read_parquet(feat_path)
        feat_is = feat[(feat["open_time"] >= IS_START_MS) & (feat["open_time"] < OOS_CUTOFF_MS)]
        merged = bdf[["open_time", "basis_zscore_30"]].merge(
            feat_is, on="open_time", how="inner"
        )
        merged = merged.dropna(subset=["basis_zscore_30"])
        per_feat = []
        for col in V1_FEATURE_COLUMNS_PRUNED:
            if col not in merged.columns:
                per_feat.append({"symbol": sym, "feature": col, "pearson": np.nan, "n": 0})
                continue
            sub = merged[["basis_zscore_30", col]].dropna()
            if len(sub) < 50:
                per_feat.append({"symbol": sym, "feature": col, "pearson": np.nan, "n": len(sub)})
                continue
            r, _ = pearsonr(sub["basis_zscore_30"], sub[col])
            per_feat.append({"symbol": sym, "feature": col, "pearson": round(r, 4), "n": len(sub)})
        ic_records.extend(per_feat)

    ic_df = pd.DataFrame(ic_records)
    ic_df.to_csv(OUT_DIR / "ic_vs_pruned_features.csv", index=False)

    # Print top |IC| pairs per symbol
    for sym in V1_SYMBOLS:
        sub = ic_df[ic_df["symbol"] == sym].dropna(subset=["pearson"]).copy()
        sub["abs_r"] = sub["pearson"].abs()
        top5 = sub.nlargest(5, "abs_r")[["feature", "pearson"]]
        print(f"  {sym} top |Pearson| with V1_FEATURE_COLUMNS_PRUNED:")
        for _, row in top5.iterrows():
            print(f"    {row['feature']:<30s}  {row['pearson']:+.4f}")

    # Global max |IC|
    max_ic = ic_df.dropna(subset=["pearson"]).reindex(
        ic_df.dropna(subset=["pearson"])["pearson"].abs().sort_values(ascending=False).index
    ).iloc[0]
    print(
        f"\n  GLOBAL max |Pearson|: {max_ic['symbol']}/{max_ic['feature']} = {max_ic['pearson']:+.4f}"
    )

    # ------------------------------------------------------------------
    # 3. ADF stationarity test
    # ------------------------------------------------------------------
    print("\n\n3. ADF stationarity test on basis_zscore_30:\n")
    adf_rows = []
    for sym in V1_SYMBOLS:
        z = basis_by_sym[sym]["basis_zscore_30"].dropna()
        result = adfuller(z, autolag="AIC", regression="c")
        adf_rows.append({
            "symbol": sym,
            "n_obs": len(z),
            "adf_stat": round(result[0], 4),
            "p_value": round(result[1], 6),
            "stationary_at_5%": bool(result[1] < 0.05),
        })
    adf_df = pd.DataFrame(adf_rows)
    adf_df.to_csv(OUT_DIR / "adf_stationarity.csv", index=False)
    print(adf_df.to_string(index=False))

    # ------------------------------------------------------------------
    # 4. Per-quintile baseline trade attribution
    # ------------------------------------------------------------------
    print("\n\n4. Per-quintile baseline-trade outcome:\n")
    trades = pd.read_csv("reports-v1/iteration_v1-baseline/in_sample/trades.csv")
    quintile_records = []
    for sym in V1_SYMBOLS:
        bdf = basis_by_sym[sym][["open_time", "basis_zscore_30"]].dropna()
        # baseline trades open_time = candle close_time-1ms; merge_asof BACKWARD onto bar
        sym_trades = trades[trades["symbol"] == sym].copy()
        sym_trades["open_time_ms"] = sym_trades["open_time"].astype("int64")
        # closest past-or-equal bar to entry candle: subtract 1 ms then floor to bar
        sym_trades = sym_trades.sort_values("open_time_ms")
        bdf = bdf.sort_values("open_time")
        # align on the candle bar whose open_time == trade.open_time - 28799999 (the close of that bar is entry time)
        # baseline open_time = close_time of entry candle = (bar_open + 8h - 1ms)
        sym_trades["bar_open_ms"] = sym_trades["open_time_ms"] - 28_799_999
        merged_tr = sym_trades.merge(
            bdf.rename(columns={"open_time": "bar_open_ms"}),
            on="bar_open_ms", how="left"
        )
        merged_tr["signed_pnl"] = merged_tr["net_pnl_pct"]
        # quintile labels
        z = merged_tr["basis_zscore_30"].dropna()
        if len(z) < 20:
            continue
        qcuts = pd.qcut(z, 5, labels=["Q1_low", "Q2", "Q3", "Q4", "Q5_high"], duplicates="drop")
        merged_tr.loc[z.index, "quintile"] = qcuts.values
        for q in ["Q1_low", "Q2", "Q3", "Q4", "Q5_high"]:
            sub = merged_tr[merged_tr["quintile"] == q]
            quintile_records.append({
                "symbol": sym,
                "quintile": q,
                "n_trades": len(sub),
                "win_rate_%": round((sub["signed_pnl"] > 0).mean() * 100, 1) if len(sub) > 0 else None,
                "mean_pnl_%": round(sub["signed_pnl"].mean(), 3) if len(sub) > 0 else None,
                "median_pnl_%": round(sub["signed_pnl"].median(), 3) if len(sub) > 0 else None,
            })
    quint_df = pd.DataFrame(quintile_records)
    quint_df.to_csv(OUT_DIR / "quintile_trade_attribution.csv", index=False)
    print(quint_df.to_string(index=False))

    # ------------------------------------------------------------------
    # 5. Per-symbol Pearson with signed_pnl (baseline trade outcomes)
    # ------------------------------------------------------------------
    print("\n\n5. Per-symbol Pearson with baseline trade signed_pnl_%:\n")
    pearson_rows = []
    for sym in V1_SYMBOLS:
        bdf = basis_by_sym[sym][["open_time", "basis_zscore_30"]].dropna()
        sym_trades = trades[trades["symbol"] == sym].copy()
        sym_trades["bar_open_ms"] = sym_trades["open_time"].astype("int64") - 28_799_999
        merged_tr = sym_trades.merge(
            bdf.rename(columns={"open_time": "bar_open_ms"}),
            on="bar_open_ms", how="left"
        ).dropna(subset=["basis_zscore_30"])
        if len(merged_tr) < 20:
            pearson_rows.append({"symbol": sym, "n": len(merged_tr), "pearson_signed": None, "spearman_signed": None})
            continue
        r_p, _ = pearsonr(merged_tr["basis_zscore_30"], merged_tr["net_pnl_pct"])
        r_s, _ = spearmanr(merged_tr["basis_zscore_30"], merged_tr["net_pnl_pct"])
        # direction-conditioned: when feature is HIGH (Q5) what fraction are LONG?
        merged_tr["is_long"] = (merged_tr["direction"] == 1).astype(int)
        q5_long_share = merged_tr[merged_tr["basis_zscore_30"] > merged_tr["basis_zscore_30"].quantile(0.8)]["is_long"].mean()
        q1_long_share = merged_tr[merged_tr["basis_zscore_30"] < merged_tr["basis_zscore_30"].quantile(0.2)]["is_long"].mean()
        pearson_rows.append({
            "symbol": sym,
            "n": len(merged_tr),
            "pearson_signed": round(r_p, 4),
            "spearman_signed": round(r_s, 4),
            "q5_long_share": round(q5_long_share, 3),
            "q1_long_share": round(q1_long_share, 3),
        })
    pearson_df = pd.DataFrame(pearson_rows)
    pearson_df.to_csv(OUT_DIR / "signed_pnl_pearson.csv", index=False)
    print(pearson_df.to_string(index=False))

    print("\n\n=== Phase 2 EDA complete. Artifacts in analysis/iteration_v1-034/ ===\n")


if __name__ == "__main__":
    main()
