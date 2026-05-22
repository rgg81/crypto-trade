"""iter-v3/105 grid-sensitivity EDA — is the F-IC GO an artifact of the grid?

R1 found the OLS t-stat mechanically favours the longest grid horizon (add h=55,
it grabs ~44% just as h=34 did). This script asks the two questions that decide
whether the trend-scanning AXIS survives that finding:

  G1 - GRID-CAPPED-AT-INCUMBENT. Restrict the grid to {5,8,13,21} -- the longest
       member is now 21, identical to the incumbent triple-barrier timeout. This
       removes the "longest-wins beyond the incumbent" confound entirely: every
       horizon trend-scanning can pick is <= the incumbent's fixed horizon. If the
       F-IC lift SURVIVES here, the lift is NOT just "label by the longest-window
       trend" -- it is the per-bar data-selection itself. If it VANISHES, the axis
       is a longest-horizon relabel and should be NO-GO.

  G2 - The lift decomposed: is a capped-grid trend-scanning label still materially
       better than the incumbent, per symbol and in aggregate? Same F-IC machinery.

  G3 - HORIZON-vs-INCUMBENT contrast. Even under the capped grid, what fraction of
       bars pick a horizon STRICTLY SHORTER than the incumbent 21? That fraction is
       the bars where trend-scanning genuinely re-frames the estimand to a shorter,
       more-resolvable horizon -- the structural mechanism the /104 diary posited.

Strictly IS-only. Run:
  uv run python analysis/iteration_v3-105/trend_scanning_grid_sensitivity.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.stats import spearmanr, wilcoxon

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.features_v3 import V3_FEATURE_COLUMNS
from crypto_trade.strategies.ml.labeling import label_trades

SYMBOLS = ["BCHUSDT", "LDOUSDT", "TRXUSDT"]
FEATURES_DIR = Path("data/features_v3")
OUT_DIR = Path("analysis/iteration_v3-105")
ATR_COLUMN = "natr_21_raw"
ATR_TP, ATR_SL = 2.0, 1.0
INCUMBENT_TIMEOUT_CANDLES = 21
INTERVAL_MINUTES = 8 * 60
FEE_PCT = 0.1
INCUMBENT_TIMEOUT_MINUTES = INCUMBENT_TIMEOUT_CANDLES * INTERVAL_MINUTES

# the grid CAPPED at the incumbent horizon -- longest member == incumbent 21
CAPPED_GRID = [5, 8, 13, 21]
# the gating grid, for the side-by-side
GATING_GRID = [5, 8, 13, 21, 34]


def _ols_slope_tstat(y: np.ndarray) -> tuple[float, float]:
    n = len(y)
    if n < 3:
        return 0.0, 0.0
    x = np.arange(n, dtype=np.float64)
    xm, ym = x.mean(), y.mean()
    sxx = np.sum((x - xm) ** 2)
    if sxx <= 0:
        return 0.0, 0.0
    slope = np.sum((x - xm) * (y - ym)) / sxx
    resid = y - ((ym - slope * xm) + slope * x)
    dof = n - 2
    if dof <= 0:
        return 0.0, 0.0
    sigma2 = np.sum(resid ** 2) / dof
    if sigma2 <= 0:
        return slope, np.sign(slope) * 1e6
    se = np.sqrt(sigma2 / sxx)
    if se <= 0:
        return slope, np.sign(slope) * 1e6
    return slope, slope / se


def trend_scanning_label(close: np.ndarray, grid: list[int]):
    n = len(close)
    label = np.zeros(n, dtype=np.intp)
    sel_h = np.zeros(n, dtype=np.intp)
    for t in range(n):
        best_abs_t, best_slope, best_h = -1.0, 0.0, 0
        for h in grid:
            end = t + h + 1
            if end > n:
                continue
            slope, tstat = _ols_slope_tstat(close[t:end])
            if abs(tstat) > best_abs_t:
                best_abs_t, best_slope, best_h = abs(tstat), slope, h
        if best_h == 0:
            continue
        sel_h[t] = best_h
        label[t] = 1 if best_slope >= 0 else -1
    return label, sel_h


def load_symbol(sym: str) -> pd.DataFrame:
    path = FEATURES_DIR / f"{sym}_8h_features.parquet"
    cols = (
        ["symbol", "open_time", "close_time", "open", "high", "low", "close", ATR_COLUMN]
        + list(V3_FEATURE_COLUMNS)
    )
    return pq.read_table(path, columns=cols).to_pandas().sort_values(
        "open_time"
    ).reset_index(drop=True)


def incumbent_labels(df: pd.DataFrame):
    close = df["close"].to_numpy(dtype=np.float64)
    atr_price = close * df[ATR_COLUMN].to_numpy(dtype=np.float64) / 100.0
    n = len(df)
    labels, _w, _lp, _sp = label_trades(
        df, np.arange(n, dtype=np.intp), ATR_TP, ATR_SL,
        INCUMBENT_TIMEOUT_MINUTES, fee_pct=FEE_PCT, atr_values=atr_price, verbose=0,
    )
    valid = np.ones(n, dtype=bool)
    if n > INCUMBENT_TIMEOUT_CANDLES:
        valid[-INCUMBENT_TIMEOUT_CANDLES:] = False
    return labels, valid


def ic_vec(feats: pd.DataFrame, label: np.ndarray, mask: np.ndarray) -> dict[str, float]:
    out: dict[str, float] = {}
    lab = label[mask].astype(np.float64)
    for col in V3_FEATURE_COLUMNS:
        x = feats[col].to_numpy(dtype=np.float64)[mask]
        ok = np.isfinite(x) & np.isfinite(lab)
        out[col] = float(spearmanr(x[ok], lab[ok])[0]) if ok.sum() >= 100 else np.nan
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/105 GRID-SENSITIVITY EDA — F-IC GO under a grid CAPPED at the incumbent")
    print(f"capped grid = {CAPPED_GRID} (longest member 21 == incumbent timeout)")
    print("=" * 78)

    g_rows: list[dict] = []
    paired_capped_ts: list[float] = []
    paired_capped_tb: list[float] = []

    for sym in SYMBOLS:
        df = load_symbol(sym)
        close = df["close"].to_numpy(dtype=np.float64)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        is_window = open_time < OOS_CUTOFF_MS
        tb_label, tb_valid = incumbent_labels(df)

        lab_cap, h_cap = trend_scanning_label(close, CAPPED_GRID)
        m_cap = is_window & (lab_cap != 0)

        # G3: horizon distribution under the capped grid
        sel = h_cap[m_cap]
        share = {h: float((sel == h).mean()) for h in CAPPED_GRID}
        share_below_21 = float((sel < 21).mean())
        # G2: F-IC under the capped grid
        shared = is_window & (lab_cap != 0) & tb_valid
        ic_ts = ic_vec(df, lab_cap, shared)
        ic_tb = ic_vec(df, tb_label, shared)
        abs_ts = [abs(ic_ts[c]) for c in V3_FEATURE_COLUMNS if np.isfinite(ic_ts[c])]
        abs_tb = [abs(ic_tb[c]) for c in V3_FEATURE_COLUMNS if np.isfinite(ic_tb[c])]
        n_imp = 0
        for c in V3_FEATURE_COLUMNS:
            a, b = ic_ts[c], ic_tb[c]
            if np.isfinite(a) and np.isfinite(b):
                paired_capped_ts.append(abs(a))
                paired_capped_tb.append(abs(b))
                if abs(a) > abs(b):
                    n_imp += 1
        mean_ts, mean_tb = float(np.mean(abs_ts)), float(np.mean(abs_tb))
        g_rows.append(
            {
                "symbol": sym,
                "capped_h5_share": round(share[5], 4),
                "capped_h8_share": round(share[8], 4),
                "capped_h13_share": round(share[13], 4),
                "capped_h21_share": round(share[21], 4),
                "frac_bars_horizon_below_incumbent_21": round(share_below_21, 4),
                "capped_mean_abs_ic_trend_scan": round(mean_ts, 5),
                "capped_mean_abs_ic_triple_barrier": round(mean_tb, 5),
                "capped_fic_ratio": round(mean_ts / mean_tb, 4) if mean_tb > 0 else np.nan,
                "capped_n_features_improved_of_14": n_imp,
            }
        )
        print(f"\n[{sym}] capped-grid horizon distribution (IS):")
        for h in CAPPED_GRID:
            bar = "#" * int(round(share[h] * 50))
            print(f"    h={h:>3}: {share[h]*100:6.2f}%  {bar}")
        print(f"    fraction of bars choosing a horizon SHORTER than incumbent 21: "
              f"{share_below_21*100:.1f}%")
        print(f"  G2 capped-grid F-IC ratio: {mean_ts/mean_tb:.3f}  "
              f"({n_imp}/14 features improve)")

    a = np.array(paired_capped_ts)
    b = np.array(paired_capped_tb)
    diff = a - b
    n_imp_total = int((diff > 0).sum())
    try:
        w_stat, w_p = wilcoxon(a, b, alternative="greater")
    except ValueError:
        w_stat, w_p = np.nan, np.nan

    agg_ts = float(a.mean())
    agg_tb = float(b.mean())
    pd.DataFrame(g_rows).to_csv(OUT_DIR / "G1_capped_grid_sensitivity.csv", index=False)
    pd.DataFrame(
        [
            {
                "grid": "capped_5_8_13_21",
                "agg_abs_ic_trend_scan": round(agg_ts, 5),
                "agg_abs_ic_triple_barrier": round(agg_tb, 5),
                "agg_abs_ic_ratio": round(agg_ts / agg_tb, 4) if agg_tb > 0 else np.nan,
                "n_cells": len(diff),
                "n_cells_improved": n_imp_total,
                "frac_cells_improved": round(n_imp_total / len(diff), 4),
                "wilcoxon_p_greater": round(float(w_p), 6) if np.isfinite(w_p) else np.nan,
            }
        ]
    ).to_csv(OUT_DIR / "G2_capped_grid_fic_verdict.csv", index=False)

    print("\n" + "=" * 78)
    print("CAPPED-GRID AGGREGATE F-IC (longest grid member == incumbent 21)")
    print(f"  agg mean |IC| trend-scan (capped)   = {agg_ts:.5f}")
    print(f"  agg mean |IC| triple-barrier        = {agg_tb:.5f}")
    print(f"  ratio                               = {agg_ts/agg_tb:.4f}")
    print(f"  cells improved                      = {n_imp_total}/{len(diff)} "
          f"({n_imp_total/len(diff)*100:.1f}%)")
    print(f"  Wilcoxon p (H1 trend-scan > tb)      = {w_p:.6f}")
    print("=" * 78)
    print(f"\nWrote 2 CSVs to {OUT_DIR}/")


if __name__ == "__main__":
    main()
