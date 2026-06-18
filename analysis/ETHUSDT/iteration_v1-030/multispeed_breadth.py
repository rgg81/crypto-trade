"""iter-v1/030 (ETHUSDT) — IS-ONLY core evidence: does a MULTI-SPEED deterministic
trend-state ensemble DE-CONCENTRATE the let-winners-run book vs the single SMA200 anchor?

HARD RULES (user mandate 2026-06-18):
  - open_time < OOS_CUTOFF_MS hard filter on EVERY entry, with leak-guard assert.
  - Direction primitives are DETERMINISTIC / parameter-free / past-only (shift(1)).
    The campaign lesson: a LEARNED direction overfits; only deterministic direction
    generalizes. The ensemble must stay stateless.
  - We additionally DROP IS entries whose 14d label horizon would cross the OOS wall
    (drop_horizon_crossing_oos) so NO OOS price enters any reported statistic.

The "book" simulated here is the iter-027 let-winners-run model, IS-only, deterministic:
  - direction d(t) in {+1,-1} from a trend-state rule (single SMA OR multi-speed ensemble)
  - conviction gate: enter only when |close-SMA200|/ATR14 >= past-only quantile q
  - net trade pnl = d(t) * fwd_ret_14d(t) - costs  (signless fwd return * direction)
This is the SAME book abstraction iter-028 used to measure concentration; we reuse its
helpers verbatim. We do NOT re-run the backtest; this is a design diagnostic.

We compare:
  ANCHOR : single SMA200 trend-state (the iter-027/028 primary direction)
  (A)    : signed-MAJORITY vote over SMA windows {100,150,200,300}
  (A')   : signed-AVERAGE (continuous) over the same windows, sign taken for direction,
           magnitude available as a conviction/agreement score
  (B)    : TS-momentum multi-horizon: sign of return over {21,42,84} candles, majority
  (C)    : signal-family ensemble: MA-cross(50/200) + Donchian(55) breakout + TSMOM(42),
           majority vote

For each: signal-level direction-correctness, trade count at the SAME conviction gate,
and concentration (top-1 / top-2 trade share of net, Herfindahl of |pnl|).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _common import (  # noqa: E402
    OOS_CUTOFF_MS,
    add_forward_return,
    annualized_sharpe_from_trade_pnls,
    concentration_stats,
    drop_horizon_crossing_oos,
    load_full_for_label_horizon,
    trend_strength_atr_norm,
)

HORIZON = 42          # 14d in 8h candles
CANDLES_PER_YEAR = 365 * 3
FEE_BPS = 10.0        # 0.1% per side round-trip approximated as one cost cut
SLIP_BPS = 2.0        # 2 bps/side
COST = (FEE_BPS + SLIP_BPS) / 10000.0 * 2.0  # round-trip fraction
CONV_Q = 0.40         # iter-027 conviction-gate quantile

SMA_WINDOWS = [100, 150, 200, 300]
TSMOM_HORIZONS = [21, 42, 84]


# ----------------------------- deterministic direction primitives -----------------------------
def sma_sign(df: pd.DataFrame, window: int) -> np.ndarray:
    """+1 if close[t-1] > SMA_window[t-1] else -1. Past-only (shift(1))."""
    sma = df["close"].rolling(window).mean()
    prev_close = df["close"].shift(1)
    prev_sma = sma.shift(1)
    return np.where(prev_close > prev_sma, 1.0, -1.0)


def tsmom_sign(df: pd.DataFrame, horizon: int) -> np.ndarray:
    """sign of trailing return over `horizon` candles, measured to t-1 (past-only)."""
    prev_close = df["close"].shift(1)
    ret = prev_close / prev_close.shift(horizon) - 1.0
    return np.where(ret > 0, 1.0, -1.0)


def donchian_breakout_sign(df: pd.DataFrame, window: int) -> np.ndarray:
    """+1 if prev close is in the upper half of the trailing Donchian channel, else -1.
    Past-only: channel built from highs/lows up to t-1.
    """
    hi = df["high"].shift(1).rolling(window).max()
    lo = df["low"].shift(1).rolling(window).min()
    mid = (hi + lo) / 2.0
    prev_close = df["close"].shift(1)
    return np.where(prev_close >= mid, 1.0, -1.0)


def ma_cross_sign(df: pd.DataFrame, fast: int, slow: int) -> np.ndarray:
    """+1 if EMA_fast > EMA_slow at t-1, else -1. Past-only."""
    ef = df["close"].ewm(span=fast, adjust=False).mean().shift(1)
    es = df["close"].ewm(span=slow, adjust=False).mean().shift(1)
    return np.where(ef > es, 1.0, -1.0)


def majority(signs: list[np.ndarray]) -> np.ndarray:
    """Signed majority vote; ties (== 0) broken toward +1 (long-bias matches a 24/7
    upward-drifting risk asset; recorded as a design choice, tested below)."""
    s = np.sum(np.vstack(signs), axis=0)
    return np.where(s > 0, 1.0, np.where(s < 0, -1.0, 1.0))


def signed_average(signs: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Continuous mean of {+1,-1} votes in [-1,1]; returns (sign, |agreement|).
    |agreement| = |mean| is an extra conviction score (1.0 = unanimous)."""
    m = np.mean(np.vstack(signs), axis=0)
    return np.where(m >= 0, 1.0, -1.0), np.abs(m)


# ----------------------------- book simulation (IS-only) -----------------------------
def build_book(df_is: pd.DataFrame, direction: np.ndarray, conv: np.ndarray, q: float):
    """Simulate the let-winners-run book on IS entries that pass the conviction gate.

    direction : {+1,-1} per row
    conv      : conviction quantity (|close-SMA200|/ATR14), past-only, per row
    Returns the net per-trade pnls (signless fwd_ret * direction - cost) for gated entries.
    """
    fwd = df_is["fwd_ret_h"].to_numpy()
    # past-only conviction threshold: quantile of conv over the IS window (training-window
    # analogue; iter-027 uses the per-month training-window quantile — here a single IS
    # quantile is the design proxy, computed on IS only).
    valid = np.isfinite(conv) & np.isfinite(fwd) & np.isfinite(direction)
    thr = np.nanquantile(conv[valid], q)
    gate = valid & (conv >= thr)
    d = direction[gate]
    f = fwd[gate]
    net = d * f - COST
    return net, int(gate.sum())


def summarize(name: str, direction: np.ndarray, conv: np.ndarray, df_is: pd.DataFrame) -> dict:
    net, n_gate = build_book(df_is, direction, conv, CONV_Q)
    cs = concentration_stats(net)
    # Herfindahl of |pnl| (concentration index; 1/n = perfectly even, 1.0 = single trade)
    ap = np.abs(net)
    hhi = float(np.sum((ap / ap.sum()) ** 2)) if ap.sum() > 0 else np.nan
    shp = annualized_sharpe_from_trade_pnls(net, CANDLES_PER_YEAR / HORIZON)
    # signal-level direction-correctness on ALL IS rows (not gated): fraction where
    # sign(direction) == sign(fwd_ret) — the "is the deterministic direction right" test.
    fwd = df_is["fwd_ret_h"].to_numpy()
    ok = np.isfinite(fwd) & np.isfinite(direction)
    hit = float(np.mean((np.sign(direction[ok]) == np.sign(fwd[ok])))) if ok.any() else np.nan
    return {
        "name": name,
        "n_gated_trades": n_gate,
        "signal_hit_rate_all_rows": round(hit, 4),
        "gated_win_rate": round(cs["win_rate"], 4),
        "gated_n_winners": cs["n_winners"],
        "per_trade_sharpe_ann": round(shp, 4),
        "net_sum": round(cs["net_sum"], 4),
        "top1_share_of_net": round(cs["top1_share_of_net"], 4)
        if np.isfinite(cs["top1_share_of_net"]) else np.nan,
        "top2_share_of_net": round(cs["top2_share_of_net"], 4)
        if np.isfinite(cs["top2_share_of_net"]) else np.nan,
        "herfindahl_abs_pnl": round(hhi, 5),
    }


def main() -> None:
    full = load_full_for_label_horizon()
    full = add_forward_return(full, HORIZON)
    df_is = drop_horizon_crossing_oos(full, HORIZON)
    assert df_is["open_time"].max() < OOS_CUTOFF_MS, "LEAK GUARD FAILED"
    print(f"IS rows (horizon-safe): {len(df_is)}  "
          f"max open_time {int(df_is['open_time'].max())} < cutoff {OOS_CUTOFF_MS}")

    # shared conviction quantity = iter-027's |close-SMA200|/ATR14 (UNCHANGED across configs
    # so the gate is held fixed and only the DIRECTION axis varies — single-axis discipline).
    conv = trend_strength_atr_norm(df_is, sma_window=200, atr_window=14).to_numpy()

    rows = []

    # ANCHOR — single SMA200
    rows.append(summarize("ANCHOR_sma200", sma_sign(df_is, 200), conv, df_is))

    # (A) signed-MAJORITY over SMA {100,150,200,300}
    sma_signs = [sma_sign(df_is, w) for w in SMA_WINDOWS]
    rows.append(summarize("A_sma_majority_100_150_200_300", majority(sma_signs), conv, df_is))

    # (A') signed-AVERAGE over the same SMA windows (sign for dir)
    a_sign, a_agree = signed_average(sma_signs)
    rows.append(summarize("Aprime_sma_signed_avg", a_sign, conv, df_is))

    # (A'') signed-AVERAGE but ALSO require agreement>=0.5 (>=3/4 windows agree) as an
    # extra conviction filter ON TOP of the existing gate (still single-axis: direction is
    # the multi-speed average; agreement is part of that primitive's own conviction).
    a_agree_gate = np.where(a_agree >= 0.5, conv, -np.inf)  # gate out low-agreement rows
    rows.append(summarize("Aprime2_signed_avg_agree50", a_sign, a_agree_gate, df_is))

    # (B) TSMOM multi-horizon {21,42,84} majority
    tsmom_signs = [tsmom_sign(df_is, h) for h in TSMOM_HORIZONS]
    rows.append(summarize("B_tsmom_majority_21_42_84", majority(tsmom_signs), conv, df_is))

    # (C) signal-FAMILY ensemble: MA-cross(50/200) + Donchian(55) + TSMOM(42) majority
    fam = [ma_cross_sign(df_is, 50, 200), donchian_breakout_sign(df_is, 55), tsmom_sign(df_is, 42)]
    rows.append(summarize("C_family_macross_donchian_tsmom", majority(fam), conv, df_is))

    # (D) GRAND ensemble — all SMA speeds + TSMOM horizons + family, signed-average sign
    grand = sma_signs + tsmom_signs + fam
    g_sign, g_agree = signed_average(grand)
    rows.append(summarize("D_grand_signed_avg", g_sign, conv, df_is))

    out = pd.DataFrame(rows)
    csv = Path(__file__).resolve().parent / "multispeed_breadth.csv"
    out.to_csv(csv, index=False)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    print(out.to_string(index=False))
    print(f"\nwrote {csv}")


if __name__ == "__main__":
    main()
