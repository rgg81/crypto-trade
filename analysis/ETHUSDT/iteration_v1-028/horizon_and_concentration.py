"""iter-v1/028 Phase 2 — Where does iter-027's concentration COME FROM, and how to fix it.

Hypothesis from eth_edge_structure.py: the trend-state DIRECTION is broad (52.6% hit-rate
at 14d), so the OOS concentration is an EXECUTION artifact of let-winners-run (non-binding
TP + 14d timeout) — a few trades capture huge moves, the rest decay.

Test, IS-ONLY, the trend-state-direction realized return under DIFFERENT exit horizons +
a BINDING take-profit, and report the concentration (top1/top2 share, winner count, WR) of
each. A shorter horizon / binding TP should produce MANY more, SMALLER, MORE-NUMEROUS wins
=> de-concentration, at the cost of total return (Sharpe-first, per user mandate).

We model the executed trade simply: enter in trend-state direction at close[t], exit at the
FIRST of {+tp move, -sl move, h-candle timeout}, return net of round-trip cost (0.1% fee +
0.04% slippage = 0.14%). This is a labelling-grade approximation of the engine, IS-only.

Outputs: horizon_and_concentration.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    OOS_CUTOFF_MS,
    annualized_sharpe_from_trade_pnls,
    concentration_stats,
    load_full_for_label_horizon,
    trend_state_dir,
    trend_strength_atr_norm,
)

OUT = Path(__file__).parent
ROUND_TRIP_COST = 0.0014  # 0.1% fee + 2*2bps slippage


def simulate_barrier(
    df: pd.DataFrame,
    entry_idx: np.ndarray,
    direction: np.ndarray,
    horizon: int,
    tp_pct: float | None,
    sl_pct: float | None,
) -> np.ndarray:
    """First-touch triple-barrier net return per entry. Vectorized-ish over entries.

    tp_pct/sl_pct in fractional move (e.g. 0.06 = 6%). None => that barrier non-binding.
    Forward window uses high/low/close from entry+1..entry+horizon. Entries are pre-filtered
    so entry+horizon stays inside IS (no OOS price used).
    """
    close = df["close"].values
    high = df["high"].values
    low = df["low"].values
    out = np.empty(len(entry_idx), dtype=float)
    for k, i in enumerate(entry_idx):
        e = close[i]
        d = direction[k]
        hit = None
        for j in range(i + 1, i + 1 + horizon):
            hi = high[j]
            lo = low[j]
            if d > 0:
                up = (hi - e) / e
                dn = (lo - e) / e
                if sl_pct is not None and dn <= -sl_pct:
                    hit = -sl_pct
                    break
                if tp_pct is not None and up >= tp_pct:
                    hit = tp_pct
                    break
            else:
                up = (e - lo) / e  # favorable for short
                dn = (e - hi) / e  # adverse for short
                if sl_pct is not None and dn <= -sl_pct:
                    hit = -sl_pct
                    break
                if tp_pct is not None and up >= tp_pct:
                    hit = tp_pct
                    break
        if hit is None:
            exit_close = close[min(i + horizon, len(close) - 1)]
            hit = d * (exit_close / e - 1.0)
        out[k] = hit - ROUND_TRIP_COST
    return out


def main() -> None:
    full = load_full_for_label_horizon()
    n = len(full)
    ts = trend_state_dir(full, 200).astype(int)
    # conviction gate q=0.40 (baseline): require strength >= IS-quantile(0.40)
    strength = trend_strength_atr_norm(full, 200, 14).values
    is_mask = full["open_time"].values < OOS_CUTOFF_MS
    q40 = np.nanquantile(strength[is_mask & np.isfinite(strength)], 0.40)

    pd.set_option("display.width", 230)
    pd.set_option("display.max_columns", 30)

    configs = [
        # (name, horizon_candles, tp_pct, sl_pct) ; sl 1.45-ATR ~ approximated as fixed pct band
        ("baseline_14d_noTP_sl_open", 42, None, None),       # pure 14d timeout, no barriers
        ("14d_TP6_SL4", 42, 0.06, 0.04),
        ("7d_TP5_SL3", 21, 0.05, 0.03),
        ("5d_TP4_SL3", 15, 0.04, 0.03),
        ("3d_TP3_SL2", 9, 0.03, 0.02),
        ("2d_TP2p5_SL2", 6, 0.025, 0.02),
    ]
    rows = []
    for name, h, tp, sl in configs:
        # entries: every IS candle that passes conviction gate AND horizon-safe within IS
        fut_open = pd.Series(full["open_time"].values).shift(-h).values
        horizon_safe = (full["open_time"].values < OOS_CUTOFF_MS) & (fut_open < OOS_CUTOFF_MS)
        conv = np.isfinite(strength) & (strength >= q40)
        entry = np.where(is_mask & horizon_safe & conv & (ts != 0))[0]
        # cap to first valid 200-SMA warmup
        entry = entry[entry >= 200]
        if len(entry) < 20:
            continue
        dirs = ts[entry]
        nets = simulate_barrier(full, entry, dirs, h, tp, sl)
        cs = concentration_stats(nets)
        tpy = 365.0 / (h / 3.0)
        rows.append({
            "config": name,
            "horizon_d": h / 3.0,
            "n_entries": len(entry),
            "win_rate": cs["win_rate"],
            "n_winners": cs["n_winners"],
            "mean_net": float(nets.mean()),
            "sum_net": float(nets.sum()),
            "per_trade_sharpe_ann": annualized_sharpe_from_trade_pnls(nets, tpy),
            "top1_share_of_net": cs["top1_share_of_net"],
            "top2_share_of_net": cs["top2_share_of_net"],
        })
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "horizon_and_concentration.csv", index=False)
    print("=== Trend-state direction under different exit regimes (IS-only, conviction q40) ===")
    print(f"conviction q40 threshold = {q40:.4f}")
    print(out.to_string(index=False))
    print("\nKEY: shorter horizon + binding TP -> more entries, more winners, LOWER top1/top2 share.")
    print("Sharpe-first: pick the regime that keeps per-trade Sharpe healthy while top2_share drops far below the iter-027 OOS 4.38.")


if __name__ == "__main__":
    main()
