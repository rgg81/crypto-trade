"""iter-v1/028 Phase 1 — Characterize ETH's IS-only edge structure.

Question: what should ETH's PRIMARY signal be? Compare, IS-ONLY, the forward-return
profiles of three candidate primary signals over the 14d (42-candle) horizon used by the
baseline:
  (A) TREND-STATE  : long if close>SMA200 (the iter-027 baseline direction)
  (B) MEAN-REVERSION: fade RSI / Bollinger %B extremes (short-horizon, higher-WR candidate)
  (C) FUNDING-CARRY : fade extreme funding z-score (positioning-crowd contrarian)

For each, report over IS entries (horizon-non-crossing): n, directional hit-rate (sign of
realized fwd return == signal), mean fwd return, a crude per-trade Sharpe, and the
top-1/top-2 concentration of the resulting signed-return distribution.

The goal is to find a primary whose WINNER BASE IS BROADER (higher hit-rate, lower
concentration) than the trend book — the de-concentration the user wants.

ALL data IS-only (open_time < OOS_CUTOFF_MS). Leak guard asserted in _common.
Outputs: eth_edge_structure.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    HORIZON_CANDLES,
    add_forward_return,
    annualized_sharpe_from_trade_pnls,
    concentration_stats,
    drop_horizon_crossing_oos,
    load_full_for_label_horizon,
    trend_state_dir,
)

OUT = Path(__file__).parent
TRADES_PER_YEAR_42 = 365.0 / 14.0  # if one entry per 14d horizon


def signed_profile(df: pd.DataFrame, signal: np.ndarray, name: str, mask: np.ndarray) -> dict:
    """signal in {-1,0,+1}; mask selects entry rows. Return profile of signal*fwd_ret."""
    sel = mask & (signal != 0) & df["fwd_ret_h"].notna().values
    sig = signal[sel]
    fr = df["fwd_ret_h"].values[sel]
    signed = sig * fr  # the realized per-trade return of taking `sig` direction
    n = len(signed)
    if n < 10:
        return {"signal": name, "n": n}
    hit = float((signed > 0).mean())
    cs = concentration_stats(signed)
    return {
        "signal": name,
        "n": n,
        "hit_rate": hit,
        "mean_ret": float(signed.mean()),
        "median_ret": float(np.median(signed)),
        "per_trade_sharpe_ann": annualized_sharpe_from_trade_pnls(signed, TRADES_PER_YEAR_42),
        "top1_share_of_pos": cs["top1_share_of_pos"],
        "top2_share_of_pos": cs["top2_share_of_pos"],
        "n_winners": cs["n_winners"],
    }


def main() -> None:
    full = load_full_for_label_horizon()
    full = add_forward_return(full, HORIZON_CANDLES)
    # restrict to IS entries whose horizon stays inside IS
    df = drop_horizon_crossing_oos(full, HORIZON_CANDLES)
    n_is = len(df)
    print(f"IS entries (horizon-safe): {n_is}  span "
          f"{pd.to_datetime(df.open_time.min(), unit='ms').date()} .. "
          f"{pd.to_datetime(df.open_time.max(), unit='ms').date()}")

    rows = []
    allmask = np.ones(n_is, dtype=bool)

    # (A) TREND-STATE direction (the baseline)
    ts = trend_state_dir(df, 200).astype(int)
    rows.append(signed_profile(df, ts, "A_trend_state_sma200", allmask))

    # (B) MEAN-REVERSION: fade RSI extremes. mom_rsi_9 (short) past-only already in parquet.
    # signal = +1 (long) when RSI<30 (oversold), -1 (short) when RSI>70, else 0.
    rsi = df["mom_rsi_9"].values if "mom_rsi_9" in df else df["mom_rsi_14"].values
    mr = np.zeros(n_is, dtype=int)
    mr[rsi < 30] = 1
    mr[rsi > 70] = -1
    rows.append(signed_profile(df, mr, "B_meanrev_rsi9_30_70", allmask))

    # (B2) MEAN-REVERSION via Bollinger %B if present; else z-score from mr_zscore.
    bb_col = next((c for c in df.columns if "bb_pctb" in c or "bb_percent_b" in c), None)
    if bb_col is not None:
        bb = df[bb_col].values
        mr2 = np.zeros(n_is, dtype=int)
        mr2[bb < 0.05] = 1
        mr2[bb > 0.95] = -1
        rows.append(signed_profile(df, mr2, f"B2_meanrev_{bb_col}", allmask))

    # (B3) distance-from-high mean reversion (mr_pct_from_high_5 in baseline set)
    if "mr_pct_from_high_5" in df:
        pfh = df["mr_pct_from_high_5"].values  # how far below recent high (negative)
        q_lo = np.nanquantile(pfh, 0.10)
        mr3 = np.zeros(n_is, dtype=int)
        mr3[pfh <= q_lo] = 1  # deeply below high => bounce long
        rows.append(signed_profile(df, mr3, "B3_meanrev_pct_from_high_5_q10_long", allmask))

    # (C) FUNDING-CARRY contrarian: fade extreme funding z-score (crowded longs pay => short).
    if "funding_rate_zscore_30" in df:
        fz = df["funding_rate_zscore_30"].values
        q_hi = np.nanquantile(fz, 0.80)
        q_lo = np.nanquantile(fz, 0.20)
        fc = np.zeros(n_is, dtype=int)
        fc[fz >= q_hi] = -1   # crowded longs (high positive funding) => fade short
        fc[fz <= q_lo] = 1    # crowded shorts => fade long
        rows.append(signed_profile(df, fc, "C_funding_contra_z30_q20_80", allmask))

    # (C2) CARRY DIRECTIONAL (momentum of funding regime, not contrarian): align with funding sign
    if "funding_rate_zscore_30" in df:
        fz = df["funding_rate_zscore_30"].values
        fcm = np.sign(fz).astype(int)  # +1 when funding positive (longs pay => trend-up bias)
        rows.append(signed_profile(df, fcm, "C2_funding_align_sign_z30", allmask))

    out = pd.DataFrame(rows)
    out.to_csv(OUT / "eth_edge_structure.csv", index=False)
    pd.set_option("display.width", 220)
    pd.set_option("display.max_columns", 30)
    print("\n=== ETH IS-only primary-signal edge structure (14d horizon) ===")
    print(out.to_string(index=False))
    print("\nKEY: prefer a primary with HIGHER hit_rate + LOWER top1/top2 share + MANY winners.")


if __name__ == "__main__":
    main()
