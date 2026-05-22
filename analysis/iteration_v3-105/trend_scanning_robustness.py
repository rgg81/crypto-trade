"""iter-v3/105 robustness EDA — does the trend-scanning F-IC GO survive scrutiny?

Three adversarial checks on the gating-EDA GO verdict. Strictly IS-only.

  R1 - EXTENDED-GRID degeneracy probe. The gating grid {5,8,13,21,34} put 43-46%
       of mass on the longest horizon h=34. Concern: longer OLS windows have more
       dof and can score a higher |t-stat| on pure noise (a mechanical artifact),
       in which case trend-scanning would just always pick the longest grid member
       -> collapse to a single fixed horizon = the F-HORIZON failure in disguise.
       R1 adds h=55 to the grid. If trend-scanning genuinely data-selects, the new
       longest member should NOT instantly absorb ~all mass; if it is a mechanical
       longest-wins artifact, h=55 should grab a share comparable to what h=34 had.

  R2 - PER-SYMBOL F-IC decomposition. The aggregate ratio 1.52 must not be carried
       by one symbol. R2 reports the per-symbol IC ratio and the per-symbol count
       of features whose |IC| improves under trend-scanning.

  R3 - SIGNIFICANCE of the IC lift. A paired test (per feature x symbol, the 42
       cells) of |IC_trend_scan| vs |IC_triple_barrier|: Wilcoxon signed-rank +
       the fraction of cells improved. A GO needs the lift to be broad, not 2-3
       lucky cells.

Run:  uv run python analysis/iteration_v3-105/trend_scanning_robustness.py
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

GATING_GRID = [5, 8, 13, 21, 34]
EXTENDED_GRID = [5, 8, 13, 21, 34, 55]


def _ols_slope_tstat(y: np.ndarray) -> tuple[float, float]:
    n = len(y)
    if n < 3:
        return 0.0, 0.0
    x = np.arange(n, dtype=np.float64)
    x_mean = x.mean()
    y_mean = y.mean()
    sxx = np.sum((x - x_mean) ** 2)
    if sxx <= 0:
        return 0.0, 0.0
    sxy = np.sum((x - x_mean) * (y - y_mean))
    slope = sxy / sxx
    intercept = y_mean - slope * x_mean
    resid = y - (intercept + slope * x)
    dof = n - 2
    if dof <= 0:
        return 0.0, 0.0
    sigma2 = np.sum(resid ** 2) / dof
    if sigma2 <= 0:
        return slope, np.sign(slope) * 1e6
    se_slope = np.sqrt(sigma2 / sxx)
    if se_slope <= 0:
        return slope, np.sign(slope) * 1e6
    return slope, slope / se_slope


def trend_scanning_label(close: np.ndarray, grid: list[int]):
    n = len(close)
    label = np.zeros(n, dtype=np.intp)
    sel_h = np.zeros(n, dtype=np.intp)
    for t in range(n):
        best_abs_t = -1.0
        best_slope = 0.0
        best_h = 0
        for h in grid:
            end = t + h + 1
            if end > n:
                continue
            slope, tstat = _ols_slope_tstat(close[t:end])
            if abs(tstat) > best_abs_t:
                best_abs_t = abs(tstat)
                best_slope = slope
                best_h = h
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
    df = pq.read_table(path, columns=cols).to_pandas()
    return df.sort_values("open_time").reset_index(drop=True)


def incumbent_labels(df: pd.DataFrame):
    close = df["close"].to_numpy(dtype=np.float64)
    natr = df[ATR_COLUMN].to_numpy(dtype=np.float64)
    atr_price = close * natr / 100.0
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
        if ok.sum() < 100:
            out[col] = np.nan
            continue
        ic, _ = spearmanr(x[ok], lab[ok])
        out[col] = float(ic)
    return out


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("=" * 78)
    print("iter-v3/105 ROBUSTNESS EDA — adversarial checks on the F-IC GO")
    print("=" * 78)

    r1_rows: list[dict] = []
    r2_rows: list[dict] = []
    paired_ts: list[float] = []  # |IC| under trend-scanning, per cell
    paired_tb: list[float] = []  # |IC| under triple-barrier, per cell

    for sym in SYMBOLS:
        df = load_symbol(sym)
        close = df["close"].to_numpy(dtype=np.float64)
        open_time = df["open_time"].to_numpy(dtype=np.int64)
        is_window = open_time < OOS_CUTOFF_MS

        tb_label, tb_valid = incumbent_labels(df)

        # ---- R1: extended-grid degeneracy probe ---------------------------------
        lab_g, h_g = trend_scanning_label(close, GATING_GRID)
        lab_e, h_e = trend_scanning_label(close, EXTENDED_GRID)
        m_g = is_window & (lab_g != 0)
        m_e = is_window & (lab_e != 0)
        share_g_34 = float((h_g[m_g] == 34).mean()) if m_g.sum() else np.nan
        share_e_34 = float((h_e[m_e] == 34).mean()) if m_e.sum() else np.nan
        share_e_55 = float((h_e[m_e] == 55).mean()) if m_e.sum() else np.nan
        # if mechanical-longest-wins: h=55 would absorb ~the old h=34 share AND
        # h=34 would collapse. If genuine: h=55 takes a moderate share and h=34
        # only partially yields.
        r1_rows.append(
            {
                "symbol": sym,
                "gating_grid_h34_share": round(share_g_34, 4),
                "extended_grid_h34_share": round(share_e_34, 4),
                "extended_grid_h55_share": round(share_e_55, 4),
                "h34_share_retained_after_h55_added": round(share_e_34 / share_g_34, 4)
                if share_g_34
                else np.nan,
            }
        )
        print(f"\n[{sym}] R1 extended-grid probe:")
        print(
            f"  h=34 share: gating-grid {share_g_34*100:.1f}%  ->  "
            f"extended-grid {share_e_34*100:.1f}%  "
            f"(retained {share_e_34/share_g_34*100:.0f}%)"
        )
        print(f"  h=55 (new longest) share in extended grid: {share_e_55*100:.1f}%")

        # ---- R2/R3: per-symbol F-IC + paired cells ------------------------------
        shared = is_window & (lab_g != 0) & tb_valid
        ic_ts = ic_vec(df, lab_g, shared)
        ic_tb = ic_vec(df, tb_label, shared)
        abs_ts = [abs(ic_ts[c]) for c in V3_FEATURE_COLUMNS if np.isfinite(ic_ts[c])]
        abs_tb = [abs(ic_tb[c]) for c in V3_FEATURE_COLUMNS if np.isfinite(ic_tb[c])]
        n_improved = 0
        for c in V3_FEATURE_COLUMNS:
            a, b = ic_ts[c], ic_tb[c]
            if np.isfinite(a) and np.isfinite(b):
                paired_ts.append(abs(a))
                paired_tb.append(abs(b))
                if abs(a) > abs(b):
                    n_improved += 1
        mean_ts = float(np.mean(abs_ts))
        mean_tb = float(np.mean(abs_tb))
        r2_rows.append(
            {
                "symbol": sym,
                "mean_abs_ic_trend_scan": round(mean_ts, 5),
                "mean_abs_ic_triple_barrier": round(mean_tb, 5),
                "ratio": round(mean_ts / mean_tb, 4) if mean_tb > 0 else np.nan,
                "n_features_improved_of_14": n_improved,
            }
        )
        print(
            f"  R2 per-symbol F-IC: ratio {mean_ts/mean_tb:.3f}  "
            f"({n_improved}/14 features improve under trend-scanning)"
        )

    # ---- R3: paired significance over all 42 cells ------------------------------
    a = np.array(paired_ts)
    b = np.array(paired_tb)
    diff = a - b
    n_cells = len(diff)
    n_improved_total = int((diff > 0).sum())
    try:
        w_stat, w_p = wilcoxon(a, b, alternative="greater")
    except ValueError:
        w_stat, w_p = np.nan, np.nan
    mean_diff = float(diff.mean())

    pd.DataFrame(r1_rows).to_csv(OUT_DIR / "R1_extended_grid_degeneracy.csv", index=False)
    pd.DataFrame(r2_rows).to_csv(OUT_DIR / "R2_per_symbol_fic.csv", index=False)
    pd.DataFrame(
        [
            {
                "n_cells": n_cells,
                "n_cells_improved": n_improved_total,
                "frac_cells_improved": round(n_improved_total / n_cells, 4),
                "mean_abs_ic_delta": round(mean_diff, 5),
                "wilcoxon_stat": round(float(w_stat), 4) if np.isfinite(w_stat) else np.nan,
                "wilcoxon_p_greater": round(float(w_p), 6) if np.isfinite(w_p) else np.nan,
            }
        ]
    ).to_csv(OUT_DIR / "R3_paired_ic_significance.csv", index=False)

    print("\n" + "=" * 78)
    print("R3 paired IC-lift significance (42 feature x symbol cells)")
    print(f"  cells improved under trend-scanning: {n_improved_total}/{n_cells} "
          f"({n_improved_total/n_cells*100:.1f}%)")
    print(f"  mean |IC| delta (trend-scan - triple-barrier): {mean_diff:+.5f}")
    print(f"  Wilcoxon signed-rank (H1: trend-scan > triple-barrier): "
          f"stat={w_stat:.2f}  p={w_p:.6f}")
    print("=" * 78)
    print(f"\nWrote 3 CSVs to {OUT_DIR}/")


if __name__ == "__main__":
    main()
