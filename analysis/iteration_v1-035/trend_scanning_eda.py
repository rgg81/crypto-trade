"""iter-v1/035 — Trend-scanning label EDA (IS-only).

Compares the trend-scanning labeling primitive (López de Prado AFML Ch.5 §5.5)
against the v1 baseline triple-barrier σ_t labeling primitive on the in-sample
window (2020-01-01 → 2025-03-23) for the V1_BASELINE_UNIVERSE.

Trend-scanning rule:
- For each candidate bar t, fit OLS slope on close[t : t+h+1] for each
  h ∈ trend_scan_grid = (5, 8, 13, 21).
- Select h* = argmax_h |t_statistic(slope)|.
- Label = +1 if slope >= 0 else -1.
- PnL = (close[t+h*] - close[t]) / close[t] * 100% − fee_pct (per side).

Reports per symbol:
- Label distribution (+1, -1, 0 share)
- Selected horizon distribution (5/8/13/21 share)
- Realized forward-return statistics
- Comparison to triple-barrier label distribution (LightGBM weight implications)

IS-only: master kline frames trimmed at OOS_CUTOFF_MS = 1742774400000 (2025-03-24).
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from crypto_trade.config import OOS_CUTOFF_MS
from crypto_trade.strategies.ml.labeling import _trend_scan_label, label_trades

V1_BASELINE_UNIVERSE = ("BTCUSDT", "ETHUSDT", "LINKUSDT", "LTCUSDT", "DOTUSDT")
DATA_DIR = Path("data")
GRID = (5, 8, 13, 21)
TIMEOUT_MINUTES = 480 * 21  # 21 candles × 8h
INTERVAL_MINUTES = 480
FEE_PCT = 0.1
OUTPUT_DIR = Path("analysis/iteration_v1-035")


def load_kline(symbol: str) -> pd.DataFrame:
    path = DATA_DIR / symbol / "8h.csv"
    if not path.exists():
        raise FileNotFoundError(f"Missing kline CSV: {path}")
    cols = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_volume", "taker_buy_quote_volume", "ignore",
    ]
    df = pd.read_csv(path)
    # CSV may or may not have a header — normalize column names
    if "open_time" not in df.columns:
        df = pd.read_csv(path, header=None, names=cols)
    df["symbol"] = symbol
    df["open_time"] = df["open_time"].astype(np.int64)
    df["close_time"] = df["close_time"].astype(np.int64)
    for c in ("open", "high", "low", "close", "volume"):
        df[c] = df[c].astype(np.float64)
    return df


def build_master(symbols: tuple[str, ...]) -> pd.DataFrame:
    frames = []
    for sym in symbols:
        df = load_kline(sym)
        # IS-only window: open_time < OOS_CUTOFF_MS
        df = df[df["open_time"] < OOS_CUTOFF_MS].copy()
        frames.append(df[["symbol", "open_time", "close_time",
                          "open", "high", "low", "close", "volume"]])
    master = pd.concat(frames, ignore_index=True)
    master = master.sort_values(["symbol", "open_time"]).reset_index(drop=True)
    return master


def compute_ts_labels_per_symbol(master: pd.DataFrame, symbol: str) -> dict:
    """Run trend-scanning labels on first IS month (2020-01) for `symbol`."""
    sym_master = master[master["symbol"] == symbol].reset_index(drop=True)
    n = len(sym_master)
    if n < 100:
        return {"symbol": symbol, "n_bars": n, "note": "INSUFFICIENT"}

    # Use full IS-only frame: candidates = all bars with at least max(grid)+1 forward bars
    max_h = max(GRID)
    candidate_indices = np.arange(0, n - max_h - 1, dtype=np.intp)

    # Reset symbol-index for trend_scan_label (expects per-symbol sym_idx array)
    # label_trades expects a master with all symbols; we feed just this one.
    one_sym_master = sym_master.copy()
    # Convert to dtype expected by label_trades
    one_sym_master = one_sym_master.astype(
        {"open_time": np.int64, "close_time": np.int64}
    )

    labels, weights, long_pnls, short_pnls = label_trades(
        one_sym_master,
        candidate_indices,
        tp_pct=4.0,
        sl_pct=2.0,
        timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        label_mode="trend_scanning",
        trend_scan_grid=GRID,
        interval_minutes=INTERVAL_MINUTES,
    )

    # Re-run baseline label_trades (triple-barrier with σ_t fixed values for comparison)
    # Using simple ATR-style barriers proxy via tp_pct/sl_pct (4.0/2.0) since
    # σ_t computation requires full feature pipeline.
    tb_labels, tb_weights, tb_long, tb_short = label_trades(
        one_sym_master,
        candidate_indices,
        tp_pct=4.0,
        sl_pct=2.0,
        timeout_minutes=TIMEOUT_MINUTES,
        fee_pct=FEE_PCT,
        label_mode="triple_barrier",
    )

    # TS label distribution
    ts_pos_share = float(np.mean(labels == 1))
    ts_neg_share = float(np.mean(labels == -1))
    ts_zero_share = float(np.mean(labels == 0))

    # Triple-barrier label distribution
    tb_pos_share = float(np.mean(tb_labels == 1))
    tb_neg_share = float(np.mean(tb_labels == -1))
    tb_zero_share = float(np.mean(tb_labels == 0))

    # Forward-return / weight stats
    # For TS, the per-bar weight = abs(labeled forward return)
    ts_weight_mean = float(np.mean(weights))
    ts_weight_std = float(np.std(weights))
    tb_weight_mean = float(np.mean(tb_weights))
    tb_weight_std = float(np.std(tb_weights))

    # Selected-horizon distribution (re-derive via _trend_scan_label loop)
    close_arr = one_sym_master["close"].values
    sym_idx = np.arange(n, dtype=np.intp)
    horizons = np.zeros(len(candidate_indices), dtype=np.int32)
    for k, pos in enumerate(candidate_indices):
        _, best_h, _ = _trend_scan_label(close_arr, sym_idx, int(pos), GRID)
        horizons[k] = best_h

    h_dist = {h: int((horizons == h).sum()) for h in GRID}
    h_pct = {h: float((horizons == h).mean()) for h in GRID}

    # Class balance (sign-agreement with triple-barrier)
    # Note: where both labelers produce ±1, count agreement.
    nonzero_mask = (labels != 0) & (tb_labels != 0)
    if nonzero_mask.sum() > 0:
        agreement_rate = float(
            ((labels == tb_labels) & nonzero_mask).sum() / nonzero_mask.sum()
        )
    else:
        agreement_rate = float("nan")

    return {
        "symbol": symbol,
        "n_bars": n,
        "n_candidates": len(candidate_indices),
        "ts_pos_share": ts_pos_share,
        "ts_neg_share": ts_neg_share,
        "ts_zero_share": ts_zero_share,
        "ts_weight_mean": ts_weight_mean,
        "ts_weight_std": ts_weight_std,
        "tb_pos_share": tb_pos_share,
        "tb_neg_share": tb_neg_share,
        "tb_zero_share": tb_zero_share,
        "tb_weight_mean": tb_weight_mean,
        "tb_weight_std": tb_weight_std,
        "h5_share": h_pct[5],
        "h8_share": h_pct[8],
        "h13_share": h_pct[13],
        "h21_share": h_pct[21],
        "sign_agreement_rate": agreement_rate,
    }


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Loading IS-only master for V1_BASELINE_UNIVERSE ...")
    master = build_master(V1_BASELINE_UNIVERSE)
    print(f"  master rows = {len(master):,}")
    print(f"  IS_END = {master['open_time'].max()} (< OOS_CUTOFF_MS = {OOS_CUTOFF_MS})")

    rows = []
    for sym in V1_BASELINE_UNIVERSE:
        print(f"\n=== {sym} ===")
        row = compute_ts_labels_per_symbol(master, sym)
        rows.append(row)
        if "note" in row:
            print(f"  {row['note']}")
            continue
        print(f"  candidates: {row['n_candidates']:,}")
        print(f"  TS label distribution: +1={row['ts_pos_share']:.3f} "
              f"-1={row['ts_neg_share']:.3f} 0={row['ts_zero_share']:.3f}")
        print(f"  TB label distribution: +1={row['tb_pos_share']:.3f} "
              f"-1={row['tb_neg_share']:.3f} 0={row['tb_zero_share']:.3f}")
        print(f"  TS weight mean={row['ts_weight_mean']:.3f}% std={row['ts_weight_std']:.3f}%")
        print(f"  TB weight mean={row['tb_weight_mean']:.3f}% std={row['tb_weight_std']:.3f}%")
        print(f"  horizon shares: 5={row['h5_share']:.3f} 8={row['h8_share']:.3f} "
              f"13={row['h13_share']:.3f} 21={row['h21_share']:.3f}")
        print(f"  sign-agreement TS↔TB on nonzero: {row['sign_agreement_rate']:.3f}")

    # Write CSV
    fieldnames = list(rows[0].keys()) if rows and "note" not in rows[0] else []
    if fieldnames:
        out = OUTPUT_DIR / "trend_scanning_label_distribution.csv"
        with open(out, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                # Only write rows that have full fields
                if "note" not in r:
                    writer.writerow(r)
        print(f"\nWrote {out}")


if __name__ == "__main__":
    sys.exit(main())
