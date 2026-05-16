"""Axis (d) drawdown brake EDA WITH primitive 10 carry-forward.

Per the iter-v3/048 forensic correction: iter-v3/045 trades predate primitive 10.
With primitive 10 ON (BCH LONG blocked), the per-symbol drawdown trajectories shift.
Re-do the brake threshold sweep with primitive 10 simulation.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ANCHOR_REPORT = Path("reports-v3/iteration_v3-045")
OUT_DIR = Path("analysis/iteration_v3-049")
SYMBOLS = ("BCHUSDT", "LDOUSDT", "TRXUSDT", "ALGOUSDT")


def main() -> int:
    is_t = pd.read_csv(ANCHOR_REPORT / "in_sample" / "trades.csv")
    is_t["sample"] = "IS"
    # Primitive 10: drop BCH LONG
    trades = is_t[~((is_t["symbol"] == "BCHUSDT") & (is_t["direction"] == 1))].copy()
    n_dropped = len(is_t) - len(trades)
    print(f"Dropped {n_dropped} BCH LONG IS trades (primitive 10 simulation)")
    print()

    BRAKE_DURATION_CANDLES = 27
    BRAKE_DURATION_MS = BRAKE_DURATION_CANDLES * 8 * 3600 * 1000

    rows = []
    for sym in SYMBOLS:
        sub = trades[trades["symbol"] == sym].copy()
        if len(sub) < 5:
            continue
        sub = sub.sort_values("close_time").reset_index(drop=True)
        wpnl = sub["weighted_pnl"].values
        ts = sub["close_time"].values
        cumpnl = np.cumsum(wpnl)
        peak = np.maximum.accumulate(cumpnl)
        dd = peak - cumpnl

        for thr_wpnl in [3, 5, 10, 15, 20]:
            modified = wpnl.copy()
            i = 0
            n_braked = 0
            n_brake_fires = 0
            while i < len(wpnl):
                if dd[i] >= thr_wpnl:
                    fire_t = ts[i]
                    n_brake_fires += 1
                    j = i + 1
                    while j < len(wpnl) and (ts[j] - fire_t) <= BRAKE_DURATION_MS:
                        modified[j] = wpnl[j] * 0.5
                        n_braked += 1
                        j += 1
                    i = j
                else:
                    i += 1
            sum_orig = wpnl.sum()
            sum_mod = modified.sum()
            std_orig = np.std(wpnl) if len(wpnl) > 1 else 1.0
            std_mod = np.std(modified) if len(modified) > 1 else 1.0
            sharpe_proxy_orig = wpnl.mean() / std_orig if std_orig > 0 else 0
            sharpe_proxy_mod = modified.mean() / std_mod if std_mod > 0 else 0
            rows.append({
                "symbol": sym,
                "threshold_wpnl": thr_wpnl,
                "n_brake_fires": n_brake_fires,
                "n_braked_trades": n_braked,
                "n_braked_pct": round(n_braked / len(wpnl) * 100, 1),
                "wpnl_orig": round(sum_orig, 2),
                "wpnl_modified": round(sum_mod, 2),
                "wpnl_delta": round(sum_mod - sum_orig, 2),
                "sharpe_proxy_orig": round(sharpe_proxy_orig, 3),
                "sharpe_proxy_modified": round(sharpe_proxy_mod, 3),
                "max_dd_observed_wpnl": round(dd.max(), 2),
            })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_DIR / "axis_d_drawdown_brake_with_primitive10.csv", index=False)
    print("=== Per-symbol drawdown brake (with primitive 10) ===")
    print(df.to_string())
    print()
    # Aggregate
    print("Aggregate IS PnL impact by threshold (sum across syms):")
    agg = df.groupby("threshold_wpnl").agg({"wpnl_orig": "sum", "wpnl_modified": "sum", "wpnl_delta": "sum"})
    print(agg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
