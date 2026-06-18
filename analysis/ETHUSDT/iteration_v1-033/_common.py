"""Shared IS-only data loading + leak guards for iter-v1/028 (ETHUSDT) analysis.

HARD RULE (user mandate 2026-06-18): every script that touches feature/label data
MUST hard-filter open_time < OOS_CUTOFF_MS BEFORE any fitting/calibration, and assert
the leak guard. OOS is NEVER read for design. The functions here centralise that.

All forward-looking quantities (labels, forward returns) are derived from arrays that
are themselves sliced to IS rows; the triple-barrier/forward-return horizon can extend
PAST the last IS candle into would-be-OOS candles ONLY when computing the *label of an
IS entry* (that is legitimate — at training time the label of an entry near the IS edge
uses future candles that were, at that historical moment, in-sample relative to the
walk-forward train window). To stay strictly conservative for *design diagnostics* we
additionally DROP IS entries whose label horizon would cross the OOS wall, so no OOS
price information enters any reported statistic.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

OOS_CUTOFF_MS = 1742774400000  # 2025-03-24 00:00:00 UTC — IMMUTABLE
ETH_PARQUET = "data/features/ETHUSDT_8h_features.parquet"
CANDLES_PER_DAY = 3  # 8h candles
HORIZON_CANDLES = 42  # 14d == the iter-027 fixed_horizon label / let-winners-run timeout


def load_is_only(parquet: str = ETH_PARQUET) -> pd.DataFrame:
    """Load the ETH feature parquet, return ONLY rows with open_time < OOS_CUTOFF_MS.

    Asserts the leak guard: the returned frame's max open_time must be strictly less
    than OOS_CUTOFF_MS.
    """
    df = pd.read_parquet(parquet)
    df = df.sort_values("open_time").reset_index(drop=True)
    is_df = df[df["open_time"] < OOS_CUTOFF_MS].reset_index(drop=True)
    assert is_df["open_time"].max() < OOS_CUTOFF_MS, "LEAK GUARD FAILED: OOS row in IS frame"
    assert len(is_df) > 0, "no IS rows"
    return is_df


def load_full_for_label_horizon(parquet: str = ETH_PARQUET) -> pd.DataFrame:
    """Load full frame (sorted) — used ONLY to compute forward returns of IS entries.

    The caller MUST restrict *entries* to IS rows whose horizon does not cross the OOS
    wall (see drop_horizon_crossing_oos). This function exists so forward-return windows
    of late-IS entries do not silently truncate; we instead DROP those entries.
    """
    df = pd.read_parquet(parquet)
    return df.sort_values("open_time").reset_index(drop=True)


def add_forward_return(df_full: pd.DataFrame, horizon: int = HORIZON_CANDLES) -> pd.DataFrame:
    """Append fwd_ret_h = close[t+h]/close[t]-1 (raw, signless) on the FULL frame.

    NOTE: callers restrict entries to IS afterwards. shift(-h) is forward-looking by
    construction (it IS the label); the leak guard is enforced at the ENTRY level, not here.
    """
    df = df_full.copy()
    df["fwd_ret_h"] = df["close"].shift(-horizon) / df["close"] - 1.0
    return df


def drop_horizon_crossing_oos(df: pd.DataFrame, horizon: int = HORIZON_CANDLES) -> pd.DataFrame:
    """Keep IS entries whose entry close_time + horizon stays strictly inside IS.

    Conservative design guard: an IS entry at index i uses close[i+horizon]. If that
    candle is at/after the OOS wall, we drop the entry so NO OOS price enters a reported
    statistic. (At true walk-forward training time these entries WOULD be labellable, so
    this is a strictly-tighter-than-necessary diagnostic guard — by design.)
    """
    df = df.sort_values("open_time").reset_index(drop=True)
    # the candle h steps ahead
    fut_open = df["open_time"].shift(-horizon)
    keep = (df["open_time"] < OOS_CUTOFF_MS) & (fut_open < OOS_CUTOFF_MS) & fut_open.notna()
    out = df[keep].reset_index(drop=True)
    assert out["open_time"].max() < OOS_CUTOFF_MS
    return out


def trend_state_dir(df: pd.DataFrame, sma_window: int = 200) -> pd.Series:
    """The iter-027 deterministic direction: +1 if close[t-1] > SMA200[t-1] else -1.

    PAST-ONLY: uses shift(1) so the bar-close value is excluded from its own decision.
    """
    sma = df["close"].rolling(sma_window).mean()
    prev_close = df["close"].shift(1)
    prev_sma = sma.shift(1)
    return np.where(prev_close > prev_sma, 1, -1)


def trend_strength_atr_norm(
    df: pd.DataFrame, sma_window: int = 200, atr_window: int = 14
) -> pd.Series:
    """|close[t-1]-SMA[t-1]| / ATR14[t-1], past-only (the conviction-gate quantity)."""
    sma = df["close"].rolling(sma_window).mean()
    # simple ATR proxy from high/low/close (Wilder-ish), past-only
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift(1)).abs()
    lc = (df["low"] - df["close"].shift(1)).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    atr = tr.rolling(atr_window).mean()
    num = (df["close"].shift(1) - sma.shift(1)).abs()
    return num / atr.shift(1)


def annualized_sharpe_from_trade_pnls(pnls: np.ndarray, trades_per_year: float) -> float:
    """Crude per-trade Sharpe annualized — diagnostic only (not the canonical daily metric)."""
    pnls = np.asarray(pnls, dtype=float)
    if len(pnls) < 2 or pnls.std(ddof=1) == 0:
        return 0.0
    return float(pnls.mean() / pnls.std(ddof=1) * np.sqrt(trades_per_year))


def concentration_stats(net_pnls: np.ndarray) -> dict:
    """Top-1 / top-2 trade share of NET positive PnL + winner count + Gini-ish.

    Mirrors the OOS-concentration falsifier: top-1 or top-2 winners as a fraction of
    total NET pnl. We report against (a) sum of POSITIVE pnl and (b) net sum.
    """
    p = np.asarray(net_pnls, dtype=float)
    n = len(p)
    wins = p[p > 0]
    n_win = int((p > 0).sum())
    net = float(p.sum())
    pos_sum = float(wins.sum()) if len(wins) else 0.0
    srt = np.sort(p)[::-1]
    top1 = float(srt[0]) if n >= 1 else 0.0
    top2 = float(srt[:2].sum()) if n >= 2 else top1
    return {
        "n_trades": n,
        "n_winners": n_win,
        "win_rate": n_win / n if n else 0.0,
        "net_sum": net,
        "pos_sum": pos_sum,
        "top1_share_of_net": top1 / net if net > 0 else np.nan,
        "top2_share_of_net": top2 / net if net > 0 else np.nan,
        "top1_share_of_pos": top1 / pos_sum if pos_sum > 0 else np.nan,
        "top2_share_of_pos": top2 / pos_sum if pos_sum > 0 else np.nan,
    }
