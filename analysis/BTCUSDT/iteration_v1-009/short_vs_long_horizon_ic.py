"""IS-ONLY multi-horizon IC: short-window vs long-window features — BTCUSDT iter-v1/009.

FE Phase 4. iter-009 axis = FREQUENCY EMULATION within the 8h sacred constant:
higher-frequency (short-lookback) features + expanded label horizon. This script
answers Question 1 of the mandate:

  Do SHORT-window features (lookback <= ~14 bars) carry more univariate signal than
  the LONG-window prune columns, and does the signal-to-horizon relationship FAVOR
  short features at LONGER holds (i.e. a fast read that anticipates a multi-day move)?

We compute the IS-only univariate Information Coefficient (Spearman rank corr) of each
candidate feature vs the forward LOG return at SEVERAL horizons h in {3, 6, 9, 21}
candles (1d / 2d / 3d / 7d on 8h bars). Two families:
  * SHORT  — short-lookback features (momentum/MR/vol/microstructure/taker-flow), the
             "higher-frequency" set the long-skewed 48-col prune misses.
  * LONG   — representative members of the current V1_FEATURE_COLUMNS_PRUNED that skew
             to >=20-bar windows (the incumbent set).

We report, per feature, signed IC at each horizon, |IC| averaged across horizons, the
horizon of peak |IC|, and ADF stationarity (informational). We then contrast the two
families' best-|IC| distributions and the SHORT-set's IC trend across horizons.

CRYPTO framing: this is NOT an efficient-market test. BTC has retail flow, perpetual
funding, reflexive trends and liquidation cascades; a fast taker-flow / short-momentum
read can lead a multi-day persistent move. We judge contribution by IC magnitude and
its persistence across horizons, NOT by whether BTC "should" be unpredictable.

OOS-VIGILANCE (HARD): every quantity is computed AFTER the strict
`open_time < OOS_CUTOFF_MS` filter. Forward returns are built on the IS slice ONLY;
the tail NaN-masks (no OOS candle is in the frame). An explicit leak-guard assert
verifies the IS max. Reads ONLY the BTC 8h parquet. Never modifies src/. Never OOS.

Usage:
    uv run python analysis/BTCUSDT/iteration_v1-009/short_vs_long_horizon_ic.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from statsmodels.tsa.stattools import adfuller

# --------------------------------------------------------------------------- #
# Sacred constants — IS-only, single-symbol, no look-ahead.
# --------------------------------------------------------------------------- #
OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC (config.OOS_CUTOFF_MS)
SYMBOL = "BTCUSDT"
INTERVAL = "8h"
PARQUET = Path("data/features") / f"{SYMBOL}_{INTERVAL}_features.parquet"
OUTDIR = Path("analysis") / SYMBOL / "iteration_v1-009"
HORIZONS = (3, 6, 9, 21)  # candles: 1d / 2d / 3d / 7d on 8h bars

# Short-lookback ("higher-frequency") candidates, grouped by family. All lookbacks
# <= ~14 bars; these capture fast dynamics the long-skewed prune omits.
SHORT_FEATURES: tuple[str, ...] = (
    # fast momentum
    "mom_rsi_5", "mom_rsi_7", "mom_rsi_9", "mom_roc_3", "mom_roc_5", "mom_mom_5",
    "mom_stoch_k_5", "mom_stoch_d_5", "mom_macd_hist_5_13_3", "mom_willr_7",
    # fast statistical returns / autocorr
    "stat_return_1", "stat_return_2", "stat_return_3", "stat_log_return_1",
    "stat_autocorr_lag1",
    # fast mean-reversion
    "mr_zscore_10", "mr_bb_pctb_10", "mr_rsi_extreme_7", "mr_pct_from_high_5",
    "mr_pct_from_low_5", "mr_dist_sma_10",
    # fast volatility / realized-vol
    "vol_atr_5", "vol_natr_7", "vol_range_spike_12", "vol_garman_klass_10",
    "vol_parkinson_10", "vol_hist_5", "vol_bb_pctb_10",
    # microstructure / taker-flow (fast)
    "vol_taker_buy_ratio", "vol_taker_buy_ratio_sma_5", "vol_volume_pctchg_3",
    "vol_volume_rel_5", "vol_cmf_10", "vol_mfi_7",
    # fast trend / regime
    "trend_adx_7", "cusum_norm_1s", "ent_shannon_10",
)

# Long-window incumbents (members of V1_FEATURE_COLUMNS_PRUNED skewing to >=20-bar
# windows). The set the current BTC specialist relies on — the contrast group.
LONG_FEATURES: tuple[str, ...] = (
    "mom_rsi_14", "mom_roc_10", "mom_macd_hist_12_26_9", "mom_macd_line_12_26_9",
    "mom_stoch_k_14", "mom_stoch_d_14", "mom_willr_14",
    "mr_pct_from_high_20", "mr_pct_from_low_20", "mr_rsi_extreme_14",
    "stat_return_5", "stat_autocorr_lag5", "stat_skew_20", "stat_kurtosis_20",
    "trend_adx_14", "trend_aroon_osc_14", "trend_aroon_osc_50", "trend_minus_di_14",
    "trend_plus_di_14", "trend_supertrend_14_3",
    "vol_atr_14", "vol_natr_14", "vol_bb_bandwidth_20", "vol_cmf_14", "vol_mfi_14",
    "vol_range_spike_24", "vol_range_spike_72", "vol_volume_rel_20",
    "regime_momentum_signed_5d", "funding_rate_zscore_30", "funding_rate_zscore_90",
    "oi_delta_30_z90", "long_short_zscore_30", "btc_funding_spread_30_90",
)


def _fwd_log_return(close: np.ndarray, h: int) -> np.ndarray:
    """Forward h-candle log return (%). NaN-masks the last h rows (no OOS peek)."""
    n = len(close)
    out = np.full(n, np.nan, dtype=np.float64)
    if h < n:
        out[: n - h] = (np.log(close[h:]) - np.log(close[: n - h])) * 100.0
    return out


def _ic(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman IC over rows where both are finite."""
    m = np.isfinite(x) & np.isfinite(y)
    if m.sum() < 200 or np.nanstd(x[m]) == 0:
        return np.nan
    return float(spearmanr(x[m], y[m]).correlation)


def _adf_p(x: np.ndarray) -> float:
    """ADF p-value (informational stationarity check) on finite rows."""
    xf = x[np.isfinite(x)]
    if len(xf) < 200 or np.std(xf) == 0:
        return np.nan
    try:
        return float(adfuller(xf, autolag="AIC")[1])
    except Exception:
        return np.nan


def main() -> None:
    assert PARQUET.exists(), f"parquet not found: {PARQUET}"
    df_full = pd.read_parquet(PARQUET)
    assert "open_time" in df_full.columns, "open_time column missing"

    # ---- IS-only filter (HARD leak guard) ----
    df = df_full[df_full["open_time"] < OOS_CUTOFF_MS].copy().reset_index(drop=True)
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS filter leaked OOS rows"
    n_is = len(df)

    close = df["close"].to_numpy(dtype=np.float64)
    fwd = {h: _fwd_log_return(close, h) for h in HORIZONS}

    print("=" * 88)
    print(f"IS-ONLY short-vs-long horizon IC — {SYMBOL} {INTERVAL}")
    print(f"IS rows (open_time < {OOS_CUTOFF_MS} = 2025-03-24): {n_is}")
    print(f"IS window: {pd.to_datetime(df['open_time'].min(), unit='ms')} .. "
          f"{pd.to_datetime(df['open_time'].max(), unit='ms')}")
    print(f"Forward LOG-return horizons (candles): {HORIZONS}  (1d/2d/3d/7d on 8h)")
    print("=" * 88)

    rows = []
    for fam, cols in (("SHORT", SHORT_FEATURES), ("LONG", LONG_FEATURES)):
        for c in cols:
            if c not in df.columns:
                rows.append({"family": fam, "feature": c, "present": False})
                continue
            x = df[c].to_numpy(dtype=np.float64)
            rec = {"family": fam, "feature": c, "present": True,
                   "adf_p": _adf_p(x), "nan%": float(np.isnan(x).mean() * 100)}
            ics = {}
            for h in HORIZONS:
                ic = _ic(x, fwd[h])
                rec[f"ic_h{h}"] = ic
                ics[h] = ic
            abs_ics = [abs(v) for v in ics.values() if np.isfinite(v)]
            rec["abs_ic_mean"] = float(np.mean(abs_ics)) if abs_ics else np.nan
            rec["abs_ic_max"] = float(np.max(abs_ics)) if abs_ics else np.nan
            finite_h = {h: v for h, v in ics.items() if np.isfinite(v)}
            rec["peak_h"] = (max(finite_h, key=lambda h: abs(finite_h[h]))
                             if finite_h else np.nan)
            # IC-vs-horizon slope sign: does |IC| GROW toward longer holds?
            if len(finite_h) >= 2:
                hs = np.array(sorted(finite_h))
                av = np.array([abs(finite_h[h]) for h in hs])
                rec["abs_ic_slope_per_h"] = float(np.polyfit(hs, av, 1)[0])
            else:
                rec["abs_ic_slope_per_h"] = np.nan
            rows.append(rec)

    res = pd.DataFrame(rows)
    present = res[res["present"]].copy()

    print("\n[A] PER-FEATURE signed IC by horizon (Spearman; |IC|>~0.03 = above noise)")
    print("-" * 88)
    show_cols = ["family", "feature", "ic_h3", "ic_h6", "ic_h9", "ic_h21",
                 "abs_ic_mean", "abs_ic_max", "peak_h", "abs_ic_slope_per_h", "adf_p"]
    with pd.option_context("display.width", 220, "display.max_rows", 100,
                           "display.float_format", lambda v: f"{v:+.4f}"):
        print(present[show_cols].sort_values(["family", "abs_ic_mean"],
                                             ascending=[True, False]).to_string(index=False))

    print("\n[B] FAMILY-LEVEL summary — does the short set carry more signal?")
    print("-" * 88)
    for fam in ("SHORT", "LONG"):
        sub = present[present["family"] == fam]
        for h in HORIZONS:
            col = f"ic_h{h}"
            print(f"  {fam:5s} h={h:2d}: mean|IC|={sub[col].abs().mean():.4f}  "
                  f"max|IC|={sub[col].abs().max():.4f}  "
                  f"#(|IC|>0.03)={int((sub[col].abs() > 0.03).sum())}/{len(sub)}")
        print(f"  {fam:5s} ALL : mean abs_ic_mean={sub['abs_ic_mean'].mean():.4f}  "
              f"median peak_h={sub['peak_h'].median():.1f}  "
              f"frac slope>0 (|IC| grows w/ horizon)={float((sub['abs_ic_slope_per_h'] > 0).mean()):.2f}")
        print("-" * 88)

    print("\n[C] TOP-12 features by mean |IC| across horizons (the iter-009 shortlist seed)")
    print("-" * 88)
    top = present.sort_values("abs_ic_mean", ascending=False).head(12)
    with pd.option_context("display.width", 220,
                           "display.float_format", lambda v: f"{v:+.4f}"):
        print(top[["family", "feature", "abs_ic_mean", "abs_ic_max", "peak_h",
                   "abs_ic_slope_per_h"]].to_string(index=False))

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "short_vs_long_horizon_ic.csv"
    res.to_csv(out, index=False)
    print(f"\nWrote: {out}")


if __name__ == "__main__":
    main()
