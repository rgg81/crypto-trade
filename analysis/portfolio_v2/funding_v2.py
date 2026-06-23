"""funding_v2 — cross-sectional FUNDING-rank (carry) signal for rank 21-40.

User insight: the rank-21-40 mid-caps carry richer/more-crowded funding than the top-20. Carry =
fade the crowded: SHORT the highest-funding names (crowded longs paying to hold), LONG the
lowest/most-negative-funding names (crowded shorts paying you). Dollar-neutral within the band.

Orthogonal to the XS-mom price-rank (different input panel = funding, not price), so it can compose
with the XS-mom baseline as a second uncorrelated dollar-neutral sleeve (the classic momentum+carry
Sharpe-lifter). NOTE (RESEARCH_notes #2): crypto carry is REGIME-FADED (Sharpe 6.45 full-sample but
negative in 2025 broadly) — so judge this on the RECENT (LATE/OOS) regime, not the full sample.

Signal (ALL past-only): trailing-mean funding -> within-band centered rank -> NEGATED (fade):
  tfund[c,t] = fund.rolling(M).mean()                 (funding is per-8h-candle; past-only)
  rk         = tfund.where(elig).rank(axis=1)          # high funding = high rank
  sig        = -(rk - (n+1)/2)/n , .where(elig)        # SHORT high-funding / LONG low, Σ≈0
The whole signal is lagged once more by the engine's w=.shift(1).
"""

from __future__ import annotations

import pandas as pd

from . import engine_v2 as e2
from . import universe_v2 as uv


def funding_signal(
    coins: dict,
    *,
    rank_lo: float = 20,
    rank_hi: float = 40,
    season: int | None = 168,
    lookback: int = 21,
    liq_win: int = uv.LIQ_WIN,
) -> pd.DataFrame:
    """Centered within-band rank of trailing funding, NEGATED (fade crowded) -> dollar-neutral."""
    panel = e2.build_panel(coins, liq_win=liq_win)
    fund = panel["fund"]
    elig = (
        uv.eligibility(coins, rank_lo, rank_hi, season, liq_win=liq_win)
        .reindex(index=fund.index, columns=fund.columns)
        .fillna(False)
    )
    tfund = fund.rolling(lookback).mean()
    rk = tfund.where(elig).rank(axis=1)
    n = elig.sum(axis=1)
    centered = rk.sub(n.add(1) / 2.0, axis=0).div(n, axis=0).where(elig).fillna(0.0)
    return -centered  # fade: short high-funding, long low/negative-funding
