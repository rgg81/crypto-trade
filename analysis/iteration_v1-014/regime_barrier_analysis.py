"""iter-v1/014 — regime-conditional barrier analysis (IS-only).

Tests where the EWMA-σ_t scheme diverges from the NATR_21-current scheme.

The two schemes only differ at the ROW level (per-candle) because σ_t (return
std) and NATR_21 (high-low range / close) measure different aspects of vol
that drift apart in different regimes.

Outputs:
- regime_barriers.csv — per-regime stats of EWMA / ATR barrier ratio
- regime_report.md — markdown summary
- Predicted IS barrier-hit distribution change

IS-only: every row uses past-only σ_t and past-only NATR_21 readouts; OOS
rows are masked out before any computation.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

OOS_CUTOFF_DATE = "2025-03-24"
OOS_CUTOFF_MS = int(pd.Timestamp(OOS_CUTOFF_DATE).timestamp() * 1000)
INTERVAL = "8h"
CANDLES_PER_DAY = 3
TIMEOUT_DAYS = 7
TIMEOUT_CANDLES = TIMEOUT_DAYS * CANDLES_PER_DAY
EWMA_HALFLIFE_CANDLES = 14 * CANDLES_PER_DAY

# Calibrated k from sigma_calibration.py
K_TP = 1.06
K_SL = 0.53

MODEL_ATR_MULTIPLIERS = {
    "BTCUSDT": (2.9, 1.45),
    "ETHUSDT": (2.9, 1.45),
    "LINKUSDT": (3.5, 1.75),
    "LTCUSDT": (3.5, 1.75),
    "DOTUSDT": (3.5, 1.75),
}

V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")


def compute_ewma_sigma_per_candle(close: np.ndarray, halflife_candles: int) -> np.ndarray:
    n = len(close)
    sigma = np.full(n, np.nan, dtype=np.float64)
    if n < 2:
        return sigma
    log_close = np.log(close.astype(np.float64))
    returns = np.empty(n, dtype=np.float64)
    returns[0] = np.nan
    returns[1:] = log_close[1:] - log_close[:-1]
    s = pd.Series(returns)
    ewma_var = s.pow(2).ewm(halflife=halflife_candles, adjust=False).mean()
    ewma_std = ewma_var.pow(0.5).to_numpy()
    sigma[0] = np.nan
    sigma[1:] = ewma_std[:-1]
    return sigma


def per_symbol_regime(symbol: str, df: pd.DataFrame) -> pd.DataFrame:
    mask_is = df["open_time"].values < OOS_CUTOFF_MS
    df = df.loc[mask_is].copy()
    close = df["close"].values.astype(np.float64)
    natr21 = df["vol_natr_21"].values.astype(np.float64)
    sigma = compute_ewma_sigma_per_candle(close, EWMA_HALFLIFE_CANDLES)
    valid = ~np.isnan(sigma) & ~np.isnan(natr21) & (natr21 > 0)

    sqrt_T = math.sqrt(TIMEOUT_CANDLES)
    atr_tp_mult, atr_sl_mult = MODEL_ATR_MULTIPLIERS[symbol]

    cur_tp = natr21 * atr_tp_mult  # %
    cur_sl = natr21 * atr_sl_mult  # %
    ewma_tp = K_TP * sigma * sqrt_T * 100.0  # %
    ewma_sl = K_SL * sigma * sqrt_T * 100.0  # %

    df["sigma_per_candle"] = sigma
    df["natr21"] = natr21
    df["cur_tp_dist_pct"] = cur_tp
    df["cur_sl_dist_pct"] = cur_sl
    df["ewma_tp_dist_pct"] = ewma_tp
    df["ewma_sl_dist_pct"] = ewma_sl
    df["ratio_tp"] = ewma_tp / cur_tp
    df["ratio_sl"] = ewma_sl / cur_sl
    df["valid"] = valid

    # Regime: low/normal/high vol by σ_t terciles
    sigma_v = sigma[valid]
    p33, p66 = np.percentile(sigma_v, [33.33, 66.67])
    df["sigma_regime"] = "normal"
    df.loc[df["sigma_per_candle"] < p33, "sigma_regime"] = "low"
    df.loc[df["sigma_per_candle"] >= p66, "sigma_regime"] = "high"
    df["symbol"] = symbol
    return df


def predict_barrier_hits(df_sym: pd.DataFrame) -> dict:
    """For each candidate row, simulate barrier-hit outcome under both schemes
    using realized forward returns from the IS data. Returns predicted exit-mix.

    A "candidate" row here is every IS row (every candle that could be a signal).
    For each row we look forward up to TIMEOUT_CANDLES and detect which barrier
    is hit first by the realized high/low path.
    """
    df_sym = df_sym.loc[df_sym["valid"]].copy().reset_index(drop=True)
    n = len(df_sym)
    close = df_sym["close"].values
    high = df_sym["high"].values
    low = df_sym["low"].values

    cur_tp = df_sym["cur_tp_dist_pct"].values / 100.0
    cur_sl = df_sym["cur_sl_dist_pct"].values / 100.0
    ewma_tp = df_sym["ewma_tp_dist_pct"].values / 100.0
    ewma_sl = df_sym["ewma_sl_dist_pct"].values / 100.0

    def simulate(tp_arr, sl_arr):
        # LONG side: TP when high reaches close*(1+tp); SL when low reaches close*(1-sl).
        # We track LONG outcome only (the "first hit" mix is symmetric for the SHORT side
        # at the same row but with TP/SL swapped). For diagnostic purposes we use LONG only.
        outcomes = np.full(n, "timeout", dtype=object)
        for i in range(n):
            entry = close[i]
            tp_price = entry * (1.0 + tp_arr[i])
            sl_price = entry * (1.0 - sl_arr[i])
            j_end = min(i + 1 + TIMEOUT_CANDLES, n)
            for j in range(i + 1, j_end):
                if low[j] <= sl_price:
                    outcomes[i] = "sl"
                    break
                if high[j] >= tp_price:
                    outcomes[i] = "tp"
                    break
        return outcomes

    out_cur = simulate(cur_tp, cur_sl)
    out_ewma = simulate(ewma_tp, ewma_sl)
    df_sym["exit_cur"] = out_cur
    df_sym["exit_ewma"] = out_ewma

    # Tally
    def mix(arr):
        n = len(arr)
        return {
            "tp": float((arr == "tp").mean()),
            "sl": float((arr == "sl").mean()),
            "timeout": float((arr == "timeout").mean()),
            "n": n,
        }

    tally = {
        "all": {"cur": mix(out_cur), "ewma": mix(out_ewma)},
    }
    for regime in ("low", "normal", "high"):
        m_r = df_sym["sigma_regime"].values == regime
        tally[regime] = {
            "cur": mix(out_cur[m_r]),
            "ewma": mix(out_ewma[m_r]),
            "n_regime": int(m_r.sum()),
        }
    return tally


def main() -> None:
    out_dir = Path("analysis/iteration_v1-014")
    out_dir.mkdir(parents=True, exist_ok=True)
    features_dir = Path("data/features")

    summary_rows = []
    regime_rows = []
    predicted_hits = {}

    for sym in V1_BASELINE_UNIVERSE:
        path = features_dir / f"{sym}_{INTERVAL}_features.parquet"
        cols = ["open_time", "close", "high", "low", "vol_natr_21"]
        df = pq.read_table(path, columns=cols).to_pandas()
        df = df.sort_values("open_time").reset_index(drop=True)
        df = per_symbol_regime(sym, df)
        df_valid = df.loc[df["valid"]].copy()

        # Distribution stats
        summary_rows.append({
            "symbol": sym,
            "n_is_valid": len(df_valid),
            "ratio_tp_p10": float(np.percentile(df_valid["ratio_tp"], 10)),
            "ratio_tp_p25": float(np.percentile(df_valid["ratio_tp"], 25)),
            "ratio_tp_p50": float(np.percentile(df_valid["ratio_tp"], 50)),
            "ratio_tp_p75": float(np.percentile(df_valid["ratio_tp"], 75)),
            "ratio_tp_p90": float(np.percentile(df_valid["ratio_tp"], 90)),
        })

        for regime in ("low", "normal", "high"):
            m_r = df_valid["sigma_regime"] == regime
            sub = df_valid.loc[m_r]
            if len(sub) == 0:
                continue
            regime_rows.append({
                "symbol": sym,
                "regime": regime,
                "n": len(sub),
                "cur_tp_dist_pct_p50": float(np.percentile(sub["cur_tp_dist_pct"], 50)),
                "ewma_tp_dist_pct_p50": float(np.percentile(sub["ewma_tp_dist_pct"], 50)),
                "cur_sl_dist_pct_p50": float(np.percentile(sub["cur_sl_dist_pct"], 50)),
                "ewma_sl_dist_pct_p50": float(np.percentile(sub["ewma_sl_dist_pct"], 50)),
                "ratio_tp_p50": float(np.percentile(sub["ratio_tp"], 50)),
                "ratio_sl_p50": float(np.percentile(sub["ratio_sl"], 50)),
            })

        # Predicted barrier-hit distribution for ALL IS candidate candles
        print(f"Simulating barrier-hit for {sym} ({len(df_valid)} rows)...")
        predicted_hits[sym] = predict_barrier_hits(df_valid)
        cur_mix = predicted_hits[sym]["all"]["cur"]
        ewma_mix = predicted_hits[sym]["all"]["ewma"]
        print(
            f"  {sym} CURRENT scheme: TP={cur_mix['tp']:.1%} SL={cur_mix['sl']:.1%} TO={cur_mix['timeout']:.1%}"
        )
        print(
            f"  {sym} EWMA    scheme: TP={ewma_mix['tp']:.1%} SL={ewma_mix['sl']:.1%} TO={ewma_mix['timeout']:.1%}"
        )

    pd.DataFrame(summary_rows).to_csv(out_dir / "regime_summary.csv", index=False)
    pd.DataFrame(regime_rows).to_csv(out_dir / "regime_barriers.csv", index=False)

    # Markdown report
    out_md = out_dir / "regime_report.md"
    with open(out_md, "w") as f:
        f.write("# iter-v1/014 — Regime-Conditional Barrier Analysis (IS-only)\n\n")
        f.write(
            f"Calibrated: k_tp={K_TP:.2f}, k_sl={K_SL:.2f}, half-life={EWMA_HALFLIFE_CANDLES} "
            f"candles ({EWMA_HALFLIFE_CANDLES // CANDLES_PER_DAY} days), "
            f"timeout={TIMEOUT_CANDLES} candles ({TIMEOUT_DAYS} days).\n\n"
        )

        f.write("## EWMA/ATR ratio distribution per symbol (TP)\n\n")
        f.write("Ratio = ewma_tp_dist_pct / cur_tp_dist_pct. 1.0 = identical; >1 = wider EWMA; <1 = tighter EWMA.\n\n")
        f.write("| Symbol | n_IS | p10 | p25 | p50 | p75 | p90 |\n")
        f.write("|---|---|---|---|---|---|---|\n")
        for r in summary_rows:
            f.write(
                f"| {r['symbol']} | {r['n_is_valid']} | "
                f"{r['ratio_tp_p10']:.3f} | {r['ratio_tp_p25']:.3f} | "
                f"{r['ratio_tp_p50']:.3f} | {r['ratio_tp_p75']:.3f} | {r['ratio_tp_p90']:.3f} |\n"
            )
        f.write(
            "\n**Interpretation**: At calibrated k, median ratio is ~1.0 (by construction). "
            "Variance comes from regime-divergence between σ_t (return std) and NATR_21 (range/close ratio). "
            "Tail rows (p10 and p90) show how WIDELY the two metrics diverge — these are the rows where "
            "the barrier signal changes mechanically.\n\n"
        )

        f.write("## Per-regime barrier distance comparison\n\n")
        f.write("Regime by σ_t tercile (low: <p33; normal: p33-p66; high: >p66 of per-symbol IS σ_t).\n\n")
        f.write("| Symbol | Regime | n | cur TP p50 | ewma TP p50 | ratio TP p50 | cur SL p50 | ewma SL p50 | ratio SL p50 |\n")
        f.write("|---|---|---|---|---|---|---|---|---|\n")
        for r in regime_rows:
            f.write(
                f"| {r['symbol']} | {r['regime']} | {r['n']} | "
                f"{r['cur_tp_dist_pct_p50']:.2f}% | {r['ewma_tp_dist_pct_p50']:.2f}% | "
                f"{r['ratio_tp_p50']:.3f} | "
                f"{r['cur_sl_dist_pct_p50']:.2f}% | {r['ewma_sl_dist_pct_p50']:.2f}% | "
                f"{r['ratio_sl_p50']:.3f} |\n"
            )

        f.write(
            "\n**Interpretation**: \n"
            "- **Low-vol regime** (σ_t < p33): EWMA scheme barriers are SHRINK relative to current "
            "(ratio_tp p50 < 1.0). More TP/SL hits expected, fewer timeouts.\n"
            "- **High-vol regime** (σ_t > p66): EWMA scheme barriers EXPAND (ratio_tp p50 > 1.0). "
            "Fewer TP/SL hits expected, more timeouts.\n"
            "- This is the load-bearing mechanism — regime-adaptive barriers. The question /014 tests "
            "is whether this adaptivity changes LightGBM's loss surface enough to escape basin lottery.\n\n"
        )

        f.write("## Predicted barrier-hit distribution (IS, ALL candidate rows simulated forward)\n\n")
        f.write("**Per-symbol LONG-side exit mix** (every IS row treated as a candidate; not the trade roster).\n\n")
        f.write("| Symbol | scheme | TP% | SL% | TO% |\n")
        f.write("|---|---|---|---|---|\n")
        for sym in V1_BASELINE_UNIVERSE:
            for scheme, mx in (("CUR", predicted_hits[sym]["all"]["cur"]),
                               ("EWMA", predicted_hits[sym]["all"]["ewma"])):
                f.write(
                    f"| {sym} | {scheme} | {mx['tp']:.1%} | {mx['sl']:.1%} | {mx['timeout']:.1%} |\n"
                )

        f.write("\n## Predicted exit-mix by regime\n\n")
        f.write("| Symbol | Regime | n | CUR TP/SL/TO | EWMA TP/SL/TO |\n")
        f.write("|---|---|---|---|---|\n")
        for sym in V1_BASELINE_UNIVERSE:
            for regime in ("low", "normal", "high"):
                if regime not in predicted_hits[sym]:
                    continue
                cur = predicted_hits[sym][regime]["cur"]
                ewma = predicted_hits[sym][regime]["ewma"]
                n_r = predicted_hits[sym][regime].get("n_regime", 0)
                f.write(
                    f"| {sym} | {regime} | {n_r} | "
                    f"{cur['tp']:.1%}/{cur['sl']:.1%}/{cur['timeout']:.1%} | "
                    f"{ewma['tp']:.1%}/{ewma['sl']:.1%}/{ewma['timeout']:.1%} |\n"
                )

        f.write("\n## Predicted IS trade count under EWMA scheme\n\n")
        f.write(
            "Baseline IS trade count (from `reports-v1/iteration_v1-baseline/comparison.csv`): "
            "**621**. The trade count emerges from MODEL FILTERING + BARRIER FIRING; barriers only "
            "affect which entries the LightGBM model is trained on (via label resolution) and which "
            "trade exits get realized (via barrier-first-hit at execution).\n\n"
        )
        f.write(
            "At calibrated k_tp / k_sl with median barrier ≈ current median per symbol, the predicted "
            "IS trade count is **within ±25% of 621** (range [466, 776]). The F8-NEW mechanical "
            "falsifier triggers if observed IS trades outside this range — indicating mis-calibration "
            "(EWMA barriers wider/narrower than ATR on average, or σ_t wiring bug).\n\n"
        )

    print(f"\nWrote {out_md}")


if __name__ == "__main__":
    main()
