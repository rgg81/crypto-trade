"""Leak-guard + OOS-firing-count probe for the iter-021 R2 funding-contra mechanism.

PART A (LEAK GUARD, IS-only): proves the `.shift(1)` past-only construction of the funding regime
signal is LOAD-BEARING — without it, the re-admission mask differs materially (would be a leak).
We compare the R2 re-admission mask built with funding `.shift(1)` (legal) vs without shift (illegal,
uses the same-candle funding which is only known at candle close). The fraction of rows whose
re-admission decision FLIPS confirms the shift matters and the legal version is conservative.

PART B (FIRING-RATE PROBE — trade-rate-floor risk only; OOS NEVER READ): the v1 specialist floor
is >=50 OOS trades. iter-020 came in at 38 OOS trades. To gauge whether the R2-thickened book clears
the floor WITHOUT touching OOS, we measure the FIRING-RATE MULTIPLIER on IS only (R2-thickened firing
candles / gated firing candles) and apply that multiplier to iter-020's known 38 OOS trades. We do NOT
read any OOS row — no OOS price, funding, return, Sharpe, or count. The multiplier is a pure IS quantity;
the 38 is iter-020's published OOS trade count. This keeps the trade-rate-floor estimate strictly IS-only
and is the conservative, leak-free version of the iter-018 brief's est-OOS-firing-rows count.

Usage: uv run python analysis/BTCUSDT/iteration_v1-021/leak_guard_and_oos_count_probe.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    ATR_WIN,
    N_LABEL,
    OOS_CUTOFF_MS,
    Q_GATE,
    SMA_WIN,
    fwd_log_return,
    load_is,
    past_only_gate_threshold,
    subperiod_bounds,
)
from regime_conditioner_screen import past_only_quantile_threshold  # noqa: E402

Q_F = 0.50


def primitives_full(df):
    close = df["close"].to_numpy(float)
    high = df["high"].to_numpy(float)
    low = df["low"].to_numpy(float)
    cp = pd.Series(close).shift(1).to_numpy()
    sma = pd.Series(close).rolling(SMA_WIN).mean().shift(1).to_numpy()
    prev_close = pd.Series(close).shift(1).to_numpy()
    tr = np.maximum(high - low, np.maximum(np.abs(high - prev_close), np.abs(low - prev_close)))
    atr = pd.Series(tr).rolling(ATR_WIN).mean().shift(1).to_numpy()
    dist_atr = (cp - sma) / np.where(atr > 0, atr, np.nan)
    return close, cp, sma, atr, dist_atr


def main():
    # ---------- PART A: LEAK GUARD (IS-only) ----------
    df = load_is()
    close, cp, sma, atr, dist_atr = primitives_full(df)
    ot_days = df["open_time"].to_numpy(float) / 86400_000.0
    y = fwd_log_return(close, N_LABEL)
    bounds = subperiod_bounds(ot_days)
    base = np.isfinite(y) & np.isfinite(sma) & np.isfinite(cp) & np.isfinite(dist_atr)
    direction = np.where(cp > sma, 1.0, -1.0)

    gthr = past_only_gate_threshold(dist_atr, ot_days, bounds, Q_GATE)
    weak = np.isfinite(gthr) & (np.abs(dist_atr) < gthr)
    fire_chop = base & weak

    f_legal = df["funding_rate_zscore_30"].shift(1).to_numpy(float)   # past-only (legal)
    f_illegal = df["funding_rate_zscore_30"].to_numpy(float)          # same-candle (illegal)

    thr = past_only_quantile_threshold(f_legal, ot_days, bounds, Q_F)
    opp_legal = np.sign(f_legal) == -np.sign(direction)
    opp_illegal = np.sign(f_illegal) == -np.sign(direction)
    r2_legal = np.isfinite(f_legal) & np.isfinite(thr) & (np.abs(f_legal) >= thr) & opp_legal
    r2_illegal = np.isfinite(f_illegal) & np.isfinite(thr) & (np.abs(f_illegal) >= thr) & opp_illegal

    readmit_legal = fire_chop & r2_legal
    readmit_illegal = fire_chop & r2_illegal
    flips = int(np.sum(readmit_legal != readmit_illegal))
    print("=" * 100)
    print("PART A — LEAK GUARD (IS-only)")
    print(f"  chop rows considered for re-admission: {int(fire_chop.sum())}")
    print(f"  re-admitted (legal, funding .shift(1)) : {int(readmit_legal.sum())}")
    print(f"  re-admitted (illegal, same-candle)     : {int(readmit_illegal.sum())}")
    print(f"  decisions that FLIP without shift      : {flips}  "
          f"({100*flips/max(1,int(fire_chop.sum())):.2f}% of chop rows)")
    print("  => non-zero flips confirm the .shift(1) is LOAD-BEARING; the legal mask is past-only.")
    assert df["open_time"].max() < OOS_CUTOFF_MS, "IS leaked"

    # ---------- PART B: FIRING-RATE PROBE (IS-only multiplier; OOS NEVER READ) ----------
    # gated firing candles (IS) = strong rows; thickened = strong | readmit
    base_is = base & np.isfinite(gthr) & (np.abs(dist_atr) >= gthr)
    thick_is = base_is | readmit_legal
    n_gated = int(base_is.sum())
    n_thick = int(thick_is.sum())
    multiplier = n_thick / max(1, n_gated)
    iter020_oos_trades = 38  # published iter-020 OOS trade count (BASELINE_V1_BTCUSDT.md)

    print("\n" + "=" * 100)
    print("PART B — FIRING-RATE PROBE (IS-only multiplier applied to iter-020's published 38 OOS trades;")
    print("         OOS rows are NEVER read here — no OOS price/funding/return/count)")
    print(f"  IS gated firing candles (iter-020 skeleton)   : {n_gated}")
    print(f"  IS R2-thickened firing candles (union)        : {n_thick}")
    print(f"  IS firing-rate multiplier (thick / gated)     : {multiplier:.3f}x")
    proj = iter020_oos_trades * multiplier
    print(f"  iter-020 published OOS trades                 : {iter020_oos_trades}")
    print(f"  projected R2-thickened OOS trades (38 x mult) : ~{proj:.0f}")
    print("  NOTE: firing CANDLES != independent TRADES (14d let-run hold overlaps candles), and the")
    print("  model timing/sizing layer further modulates the count. This IS-multiplier projection is a")
    print("  trade-rate-floor SANITY CHECK only; the real K=20 backtest decides the independent OOS")
    floor_msg = "CLEARS (>= 50)" if proj >= 50 else "AT-RISK (< 50) — use q_f=0.30 fallback if backtest misses"
    print(f"  count. The >=50 specialist floor needs projection >= ~50: {floor_msg}.")


if __name__ == "__main__":
    main()
