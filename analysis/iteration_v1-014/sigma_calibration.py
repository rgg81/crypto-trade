"""iter-v1/014 — EWMA sigma_t calibration analysis (IS-only).

Purpose: compute past-only EWMA sigma_t at 14-day window for each baseline
symbol on IS data and calibrate k_tp / k_sl multipliers so the proposed
EWMA-sigma_t-scaled triple-barrier produces a barrier distance distribution
comparable to the current fixed-fraction ATR barriers (atr_tp / atr_sl).

NOTHING IS COMPUTED OUT-OF-SAMPLE. The OOS data is read only to detect the
cutoff boundary, then masked out. All sigma_t / barrier statistics are
computed from IS rows ONLY.

Outputs (written to analysis/iteration_v1-014/):
- sigma_calibration.csv — per-symbol distribution stats for sigma_t, NATR_21,
  and ATR-current vs EWMA-sigma barrier distances.
- calibration_report.md — markdown summary of stats + k_tp / k_sl
  recommendation per López de Prado AFML Ch. 3.

Key formulas (past-only):
- sigma_t (per-candle EWMA std of close-to-close returns):
    returns_t = log(close_t / close_{t-1})  (computed at t, available at t)
    EWMA_var_t = lambda * EWMA_var_{t-1} + (1-lambda) * returns_t^2
    lambda = exp(-1 / half_life_candles)
    half_life_candles = 14 days * 3 (8h candles per day) = 42

  Then SHIFT BY 1: at candle t, the sigma_t USED FOR DECISION = sigma_{t-1}
  (the EWMA value computed BEFORE candle t's return arrived). This makes
  sigma_t strictly past-only.

- Triple-barrier distance:
    timeout = 7 days = 21 candles
    barrier_distance_pct = k * sigma_t_per_candle * sqrt(timeout_candles)
  where sigma_t_per_candle is the EWMA stdev computed above (single-candle
  return std).

  TP_price = entry + entry * (k_tp * sigma_t_per_candle * sqrt(21))
  SL_price = entry - entry * (k_sl * sigma_t_per_candle * sqrt(21))

The current ATR-multiplier scheme writes:
    tp_dist = close * NATR_21 / 100 * atr_tp_mult
    sl_dist = close * NATR_21 / 100 * atr_sl_mult

For Model A (BTC/ETH) atr_tp=2.9, atr_sl=1.45.
For Models C/D/E (LINK/LTC/DOT) atr_tp=3.5, atr_sl=1.75.

NATR_21 measures the average 1-candle range (high-low/close) over 21 candles.
This is NOT the same as the std of returns — NATR is a high-low range proxy.

Calibration target (per AFML Ch. 3): typical k_tp ≈ 2, k_sl ≈ 1 for sigma_t-
scaled barriers when sigma_t is per-candle return-std and timeout adjustment
uses sqrt(N_candles). We computed the current-scheme equivalent barriers and
will choose k_tp / k_sl so the median per-symbol barrier-distance-pct lands
within ±20% of the current scheme — to keep the IS trade count change bounded.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import NamedTuple

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

# Sacred constants
OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = int(pd.Timestamp(OOS_CUTOFF_DATE).timestamp() * 1000)

INTERVAL = "8h"
CANDLES_PER_DAY = 3  # 24h / 8h
TIMEOUT_DAYS = 7
TIMEOUT_CANDLES = TIMEOUT_DAYS * CANDLES_PER_DAY  # 21

EWMA_HALFLIFE_DAYS = 14
EWMA_HALFLIFE_CANDLES = EWMA_HALFLIFE_DAYS * CANDLES_PER_DAY  # 42

# Current ATR multipliers per Model
MODEL_ATR_MULTIPLIERS = {
    "BTCUSDT": (2.9, 1.45),   # Model A
    "ETHUSDT": (2.9, 1.45),   # Model A
    "LINKUSDT": (3.5, 1.75),  # Model C
    "LTCUSDT": (3.5, 1.75),   # Model D
    "DOTUSDT": (3.5, 1.75),   # Model E
}

V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")


class SymbolStats(NamedTuple):
    symbol: str
    n_is: int
    sigma_per_candle_p10: float
    sigma_per_candle_p25: float
    sigma_per_candle_p50: float
    sigma_per_candle_p75: float
    sigma_per_candle_p90: float
    natr21_p10: float
    natr21_p25: float
    natr21_p50: float
    natr21_p75: float
    natr21_p90: float
    # Per-candle barrier distance (% of price) — current ATR scheme
    cur_tp_dist_pct_p10: float
    cur_tp_dist_pct_p50: float
    cur_tp_dist_pct_p90: float
    cur_sl_dist_pct_p10: float
    cur_sl_dist_pct_p50: float
    cur_sl_dist_pct_p90: float
    # EWMA-sigma_t scheme (using calibrated k_tp / k_sl)
    ewma_tp_dist_pct_p10: float
    ewma_tp_dist_pct_p50: float
    ewma_tp_dist_pct_p90: float
    ewma_sl_dist_pct_p10: float
    ewma_sl_dist_pct_p50: float
    ewma_sl_dist_pct_p90: float
    # Calibration suggestion (per-symbol; final k is portfolio-mean)
    suggested_k_tp_local: float
    suggested_k_sl_local: float
    # Predicted barrier-hit characterization
    cur_tp_over_sigma_p50: float
    ewma_tp_over_sigma_p50: float
    median_ratio_ewma_to_atr: float


def compute_ewma_sigma_per_candle(close: np.ndarray, halflife_candles: int) -> np.ndarray:
    """Compute past-only EWMA std of close-to-close log returns at given half-life.

    Returns array of same length as close.  Index t holds sigma USABLE at t —
    i.e. computed from returns up to candle t-1 (strictly past-only).
    """
    n = len(close)
    sigma = np.full(n, np.nan, dtype=np.float64)
    if n < 2:
        return sigma

    # log returns
    log_close = np.log(close.astype(np.float64))
    returns = np.empty(n, dtype=np.float64)
    returns[0] = np.nan
    returns[1:] = log_close[1:] - log_close[:-1]

    # EWMA variance with half-life — use pandas for span-style decay
    # halflife in samples => alpha = 1 - exp(-ln(2)/halflife)
    s = pd.Series(returns)
    ewma_var = s.pow(2).ewm(halflife=halflife_candles, adjust=False).mean()
    ewma_std = ewma_var.pow(0.5).to_numpy()

    # Strictly past-only: at candle t, the sigma we may use is the EWMA
    # computed from returns up to and including return_{t} which was observed
    # at t.  But return_t = log(close_t/close_{t-1}) requires close_t — i.e.
    # available only at close_t timestamp.  Since we use sigma to set barriers
    # at entry on candle t (decision made on close of t), it is fair to use
    # ewma_std[t] which incorporates return_t.  But to be conservative against
    # any look-ahead audit, we SHIFT by 1: sigma[t] := ewma_std[t-1].
    sigma[0] = np.nan
    sigma[1:] = ewma_std[:-1]
    return sigma


def load_symbol_data(features_dir: Path, symbol: str) -> pd.DataFrame:
    """Load close + open_time + vol_natr_21 + vol_atr_21 for a symbol."""
    path = features_dir / f"{symbol}_{INTERVAL}_features.parquet"
    if not path.exists():
        raise FileNotFoundError(path)
    cols = ["open_time", "close", "high", "low", "vol_natr_21", "vol_atr_21"]
    tbl = pq.read_table(path, columns=cols)
    df = tbl.to_pandas()
    df = df.sort_values("open_time").reset_index(drop=True)
    return df


def per_symbol_stats(
    symbol: str,
    df: pd.DataFrame,
    k_tp_global: float,
    k_sl_global: float,
) -> SymbolStats:
    """Compute IS-only sigma_t and barrier distance distributions."""
    # Filter to IS (open_time < OOS cutoff)
    mask_is = df["open_time"].values < OOS_CUTOFF_MS
    df_is = df.loc[mask_is].copy()

    close = df_is["close"].values.astype(np.float64)
    natr21 = df_is["vol_natr_21"].values.astype(np.float64)

    # Past-only EWMA sigma at 14-day half-life (single-candle return std)
    sigma_per_candle = compute_ewma_sigma_per_candle(close, EWMA_HALFLIFE_CANDLES)

    # Mask out NaN sigma (early candles before EWMA warm-up)
    valid = ~np.isnan(sigma_per_candle) & ~np.isnan(natr21) & (natr21 > 0)
    n_is = int(valid.sum())

    sigma_v = sigma_per_candle[valid]  # per-candle log-return std (decimal)
    natr_v = natr21[valid]  # NATR is in pct units (close-relative)
    close_v = close[valid]

    # Current ATR scheme barrier distance in % of price
    atr_tp_mult, atr_sl_mult = MODEL_ATR_MULTIPLIERS[symbol]
    # tp_dist_price = close * NATR/100 * mult  ==>  tp_dist_pct = NATR * mult
    cur_tp_dist_pct = natr_v * atr_tp_mult
    cur_sl_dist_pct = natr_v * atr_sl_mult

    # EWMA-sigma_t scheme:
    # barrier_distance_decimal = k * sigma_per_candle * sqrt(TIMEOUT_CANDLES)
    # barrier_distance_pct = barrier_distance_decimal * 100
    sqrt_T = math.sqrt(TIMEOUT_CANDLES)
    ewma_tp_dist_pct = k_tp_global * sigma_v * sqrt_T * 100.0
    ewma_sl_dist_pct = k_sl_global * sigma_v * sqrt_T * 100.0

    # Per-symbol-local calibration: choose k so median EWMA barrier ≈ median ATR barrier
    median_cur_tp_pct = float(np.median(cur_tp_dist_pct))
    median_cur_sl_pct = float(np.median(cur_sl_dist_pct))
    median_sigma_times_sqrtT_pct = float(np.median(sigma_v) * sqrt_T * 100.0)

    if median_sigma_times_sqrtT_pct > 0:
        suggested_k_tp_local = median_cur_tp_pct / median_sigma_times_sqrtT_pct
        suggested_k_sl_local = median_cur_sl_pct / median_sigma_times_sqrtT_pct
    else:
        suggested_k_tp_local = float("nan")
        suggested_k_sl_local = float("nan")

    # Ratio of EWMA / ATR barriers (at global k)
    ratio_arr = ewma_tp_dist_pct / cur_tp_dist_pct
    ratio_arr = ratio_arr[~np.isnan(ratio_arr) & np.isfinite(ratio_arr)]
    median_ratio_ewma_to_atr = float(np.median(ratio_arr)) if len(ratio_arr) else float("nan")

    # Median ratio TP-barrier / sigma_t — a proxy for "how many σ deep is the barrier"
    cur_tp_over_sigma_p50 = float(np.median(cur_tp_dist_pct / (sigma_v * sqrt_T * 100.0)))
    ewma_tp_over_sigma_p50 = float(np.median(ewma_tp_dist_pct / (sigma_v * sqrt_T * 100.0)))

    return SymbolStats(
        symbol=symbol,
        n_is=n_is,
        sigma_per_candle_p10=float(np.percentile(sigma_v, 10)),
        sigma_per_candle_p25=float(np.percentile(sigma_v, 25)),
        sigma_per_candle_p50=float(np.percentile(sigma_v, 50)),
        sigma_per_candle_p75=float(np.percentile(sigma_v, 75)),
        sigma_per_candle_p90=float(np.percentile(sigma_v, 90)),
        natr21_p10=float(np.percentile(natr_v, 10)),
        natr21_p25=float(np.percentile(natr_v, 25)),
        natr21_p50=float(np.percentile(natr_v, 50)),
        natr21_p75=float(np.percentile(natr_v, 75)),
        natr21_p90=float(np.percentile(natr_v, 90)),
        cur_tp_dist_pct_p10=float(np.percentile(cur_tp_dist_pct, 10)),
        cur_tp_dist_pct_p50=float(np.percentile(cur_tp_dist_pct, 50)),
        cur_tp_dist_pct_p90=float(np.percentile(cur_tp_dist_pct, 90)),
        cur_sl_dist_pct_p10=float(np.percentile(cur_sl_dist_pct, 10)),
        cur_sl_dist_pct_p50=float(np.percentile(cur_sl_dist_pct, 50)),
        cur_sl_dist_pct_p90=float(np.percentile(cur_sl_dist_pct, 90)),
        ewma_tp_dist_pct_p10=float(np.percentile(ewma_tp_dist_pct, 10)),
        ewma_tp_dist_pct_p50=float(np.percentile(ewma_tp_dist_pct, 50)),
        ewma_tp_dist_pct_p90=float(np.percentile(ewma_tp_dist_pct, 90)),
        ewma_sl_dist_pct_p10=float(np.percentile(ewma_sl_dist_pct, 10)),
        ewma_sl_dist_pct_p50=float(np.percentile(ewma_sl_dist_pct, 50)),
        ewma_sl_dist_pct_p90=float(np.percentile(ewma_sl_dist_pct, 90)),
        suggested_k_tp_local=suggested_k_tp_local,
        suggested_k_sl_local=suggested_k_sl_local,
        cur_tp_over_sigma_p50=cur_tp_over_sigma_p50,
        ewma_tp_over_sigma_p50=ewma_tp_over_sigma_p50,
        median_ratio_ewma_to_atr=median_ratio_ewma_to_atr,
    )


def main() -> None:
    out_dir = Path("analysis/iteration_v1-014")
    out_dir.mkdir(parents=True, exist_ok=True)
    features_dir = Path("data/features")

    # Pass 1: compute per-symbol local k_tp / k_sl, then average across portfolio
    # to derive global k recommendation.  We bootstrap with k=2 / k=1 (AFML
    # default) to compute the EWMA stats; the local suggestion comes from
    # matching median barrier-pct.
    k_tp_bootstrap = 2.0
    k_sl_bootstrap = 1.0

    rows: list[SymbolStats] = []
    for sym in V1_BASELINE_UNIVERSE:
        df = load_symbol_data(features_dir, sym)
        stats = per_symbol_stats(sym, df, k_tp_bootstrap, k_sl_bootstrap)
        rows.append(stats)
        print(
            f"{sym}: n_is={stats.n_is:5d}  σ_p50={stats.sigma_per_candle_p50:.5f}  "
            f"NATR21_p50={stats.natr21_p50:.3f}  "
            f"cur_tp_p50={stats.cur_tp_dist_pct_p50:.2f}%  "
            f"cur_sl_p50={stats.cur_sl_dist_pct_p50:.2f}%  "
            f"sugg_k_tp={stats.suggested_k_tp_local:.3f}  "
            f"sugg_k_sl={stats.suggested_k_sl_local:.3f}"
        )

    # Compute portfolio-mean and portfolio-median k recommendations
    # Use volume-weighting by IS sample count (longer histories carry more weight)
    weights = np.array([r.n_is for r in rows], dtype=np.float64)
    weights = weights / weights.sum()
    sugg_k_tps = np.array([r.suggested_k_tp_local for r in rows])
    sugg_k_sls = np.array([r.suggested_k_sl_local for r in rows])
    portfolio_k_tp_mean = float(np.sum(weights * sugg_k_tps))
    portfolio_k_sl_mean = float(np.sum(weights * sugg_k_sls))
    portfolio_k_tp_median = float(np.median(sugg_k_tps))
    portfolio_k_sl_median = float(np.median(sugg_k_sls))

    # Recompute stats at the chosen global k for the final table
    # We adopt the volume-weighted MEAN as primary (smooths outlier symbols)
    global_k_tp = round(portfolio_k_tp_mean, 2)
    global_k_sl = round(portfolio_k_sl_mean, 2)
    print()
    print(f"Suggested global k_tp = {global_k_tp:.2f} (mean-weighted by IS rows)")
    print(f"Suggested global k_sl = {global_k_sl:.2f} (mean-weighted by IS rows)")
    print(f"Per-symbol median k_tp = {portfolio_k_tp_median:.2f}")
    print(f"Per-symbol median k_sl = {portfolio_k_sl_median:.2f}")

    # Re-pass with global k for final stats
    final_rows: list[SymbolStats] = []
    for sym in V1_BASELINE_UNIVERSE:
        df = load_symbol_data(features_dir, sym)
        stats = per_symbol_stats(sym, df, global_k_tp, global_k_sl)
        final_rows.append(stats)

    # Write CSV
    df_out = pd.DataFrame(final_rows)
    out_csv = out_dir / "sigma_calibration.csv"
    df_out.to_csv(out_csv, index=False)
    print(f"\nWrote {out_csv}")

    # Write markdown report
    out_md = out_dir / "calibration_report.md"
    with open(out_md, "w") as f:
        f.write("# iter-v1/014 — EWMA σ_t Calibration Report (IS-only)\n\n")
        f.write(f"Data: features in `data/features/` filtered to `open_time < {OOS_CUTOFF_DATE}`.\n\n")
        f.write(f"EWMA half-life: **{EWMA_HALFLIFE_DAYS} days** ({EWMA_HALFLIFE_CANDLES} candles at 8h).\n")
        f.write(f"Timeout horizon: **{TIMEOUT_DAYS} days** ({TIMEOUT_CANDLES} candles).\n\n")
        f.write("σ_t = past-only EWMA std of log-returns (per-candle), SHIFTED BY 1 candle to be strictly past-only.\n\n")
        f.write("Barrier distance = `k × σ_t_per_candle × √timeout_candles` (decimal; ×100 for pct).\n\n")

        f.write("## Suggested global k\n\n")
        f.write(f"- **k_tp = {global_k_tp:.2f}** (volume-weighted portfolio mean; per-symbol "
                f"median = {portfolio_k_tp_median:.2f})\n")
        f.write(f"- **k_sl = {global_k_sl:.2f}** (volume-weighted portfolio mean; per-symbol "
                f"median = {portfolio_k_sl_median:.2f})\n\n")
        f.write("Calibration target: median EWMA barrier distance ≈ median ATR-current barrier distance per symbol.\n\n")

        f.write("## Per-symbol σ_t distribution (single-candle log-return std, decimal)\n\n")
        f.write("| Symbol | n_IS | p10 | p25 | p50 | p75 | p90 |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in final_rows:
            f.write(
                f"| {r.symbol} | {r.n_is} | {r.sigma_per_candle_p10:.5f} | "
                f"{r.sigma_per_candle_p25:.5f} | {r.sigma_per_candle_p50:.5f} | "
                f"{r.sigma_per_candle_p75:.5f} | {r.sigma_per_candle_p90:.5f} |\n"
            )

        f.write("\n## Per-symbol NATR_21 distribution (% of close)\n\n")
        f.write("| Symbol | p10 | p25 | p50 | p75 | p90 |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in final_rows:
            f.write(
                f"| {r.symbol} | {r.natr21_p10:.3f} | {r.natr21_p25:.3f} | "
                f"{r.natr21_p50:.3f} | {r.natr21_p75:.3f} | {r.natr21_p90:.3f} |\n"
            )

        f.write("\n## Barrier distance distribution — CURRENT scheme (NATR_21 × atr_mult)\n\n")
        f.write("| Symbol | atr_tp | atr_sl | cur_tp p10 | cur_tp p50 | cur_tp p90 | cur_sl p10 | cur_sl p50 | cur_sl p90 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for r in final_rows:
            atr_tp_mult, atr_sl_mult = MODEL_ATR_MULTIPLIERS[r.symbol]
            f.write(
                f"| {r.symbol} | {atr_tp_mult} | {atr_sl_mult} | "
                f"{r.cur_tp_dist_pct_p10:.2f}% | {r.cur_tp_dist_pct_p50:.2f}% | "
                f"{r.cur_tp_dist_pct_p90:.2f}% | "
                f"{r.cur_sl_dist_pct_p10:.2f}% | {r.cur_sl_dist_pct_p50:.2f}% | "
                f"{r.cur_sl_dist_pct_p90:.2f}% |\n"
            )

        f.write(
            f"\n## Barrier distance distribution — PROPOSED scheme "
            f"(k_tp={global_k_tp:.2f}, k_sl={global_k_sl:.2f} × EWMA σ_t × √{TIMEOUT_CANDLES})\n\n"
        )
        f.write("| Symbol | ewma_tp p10 | ewma_tp p50 | ewma_tp p90 | ewma_sl p10 | ewma_sl p50 | ewma_sl p90 |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in final_rows:
            f.write(
                f"| {r.symbol} | "
                f"{r.ewma_tp_dist_pct_p10:.2f}% | {r.ewma_tp_dist_pct_p50:.2f}% | "
                f"{r.ewma_tp_dist_pct_p90:.2f}% | "
                f"{r.ewma_sl_dist_pct_p10:.2f}% | {r.ewma_sl_dist_pct_p50:.2f}% | "
                f"{r.ewma_sl_dist_pct_p90:.2f}% |\n"
            )

        f.write("\n## EWMA vs current — median ratio\n\n")
        f.write("Ratio = ewma_tp_dist_pct / cur_tp_dist_pct (1.0 = identical, >1 = wider, <1 = tighter).\n\n")
        f.write("| Symbol | median ratio EWMA/ATR | suggested k_tp local | suggested k_sl local |\n")
        f.write("|---|---|---|---|\n")
        for r in final_rows:
            f.write(
                f"| {r.symbol} | {r.median_ratio_ewma_to_atr:.3f} | "
                f"{r.suggested_k_tp_local:.3f} | {r.suggested_k_sl_local:.3f} |\n"
            )

        f.write("\n## Pre-registered prediction (will land in brief F8 falsifier)\n\n")
        f.write(
            "At global k_tp / k_sl chosen to match median barrier distance per symbol, the "
            "predicted **IS trade count is within ±25% of baseline 621**. This is the F8-NEW "
            "mechanical falsifier — if observed IS trade count is outside ±25%, the σ_t scheme "
            "is mis-calibrated (the EWMA distribution is wider/narrower than ATR's distribution "
            "at the chosen k, so more/fewer barriers get hit before the 7-day timeout).\n\n"
        )
        f.write("Per-symbol predicted hit-rate change:\n\n")
        f.write("- **Low-vol periods** (sigma_t < p25): EWMA barriers SHRINK relative to historical NATR_21 "
                "(which is range-based and lags). More TP/SL hits expected, fewer timeouts.\n")
        f.write("- **High-vol periods** (sigma_t > p75): EWMA barriers EXPAND. Fewer TP/SL hits, more timeouts.\n\n")
        f.write("Baseline exit-mix from `reports-v1/iteration_v1-baseline/in_sample/comparison.csv`:\n")
        f.write("- stop_loss 53.8%, timeout 24.5%, take_profit 21.7% (621 trades).\n\n")
        f.write("**F7-NEW falsifier** (mechanical): per-symbol barrier hit-rate distribution must shift in the "
                "predicted direction (more TP/SL hits in low-vol regimes; more timeouts in high-vol regimes). "
                "If the regime-conditional barrier-hit distribution does NOT shift, the σ_t mechanism is not "
                "functioning (likely a wiring bug).\n")

    print(f"Wrote {out_md}")


if __name__ == "__main__":
    main()
