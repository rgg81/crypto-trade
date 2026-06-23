"""resmom_v2 — residual (BTC-beta-neutralized) cross-sectional momentum signal for rank 21–40.

Literature-backed (diary-portfolio-v2/RESEARCH_notes.md #1/#3): raw cross-sectional momentum is weak
on crypto, but RESIDUAL momentum — momentum of the return left AFTER removing market (BTC) beta —
survives out-of-sample with higher Sharpe and fewer crashes. This directly targets the iter-v2-001
anchor's failure: mid-cap directional trend died because it is BTC-beta-coupled and that beta went
dead in 2024–26. Residualizing strips the dead cohort-beta and isolates idiosyncratic strength.

Produces a per-(coin,candle) `signal_panel` (centered within-band rank, dollar-neutral) to feed
`engine_v2.run_book_from_signal(...)`. ALL past-only:
  beta[c,t]  = rolling Cov(r_c, r_btc) / Var(r_btc) over BETA_WIN, .shift(1)           (past-only)
  resid[c,t] = r_c[t] - beta[c,t] * r_btc[t]            (idiosyncratic 8h return)
  resmom     = sum of resid over the trailing L candles (cumulative residual momentum), .shift not
               needed here — the engine lags the whole signal via w=.shift(1)
  signal     = centered within-band rank of resmom (winners>0 / losers<0, Σ≈0)
"""

from __future__ import annotations

import pandas as pd

from . import engine_v2 as e2
from . import universe_v2 as uv

BETA_WIN = 90  # rolling window (candles) for the BTC beta estimate (~30d)
BTC = "BTCUSDT"


def residual_returns(close: pd.DataFrame, beta_win: int = BETA_WIN) -> pd.DataFrame:
    """Per-coin idiosyncratic 8h return = r_c - beta_c*r_btc, beta past-only (rolling, shifted)."""
    r = close.pct_change()
    if BTC not in r.columns:
        raise ValueError("BTCUSDT not in pool — residual momentum needs the market proxy")
    rb = r[BTC]
    var_b = rb.rolling(beta_win).var().shift(1)
    # cov(r_c, r_btc) per coin, rolling, past-only
    cov = (
        r.mul(rb, axis=0)
        .rolling(beta_win)
        .mean()
        .shift(1)
        .sub(r.rolling(beta_win).mean().shift(1).mul(rb.rolling(beta_win).mean().shift(1), axis=0))
    )
    beta = cov.div(var_b, axis=0)
    return r.sub(beta.mul(rb, axis=0))


def resmom_signal(
    coins: dict,
    *,
    rank_lo: float = 20,
    rank_hi: float = 40,
    season: int | None = 168,
    lookback: int = 84,
    beta_win: int = BETA_WIN,
    liq_win: int = uv.LIQ_WIN,
) -> pd.DataFrame:
    """Centered within-band rank of cumulative residual momentum → dollar-neutral signal panel."""
    panel = e2.build_panel(coins, liq_win=liq_win)
    close = panel["close"]
    elig = (
        uv.eligibility(coins, rank_lo, rank_hi, season, liq_win=liq_win)
        .reindex(index=close.index, columns=close.columns)
        .fillna(False)
    )
    resid = residual_returns(close, beta_win)
    resmom = resid.rolling(lookback).sum()  # cumulative idiosyncratic momentum over L
    rk = resmom.where(elig).rank(axis=1)
    n = elig.sum(axis=1)
    sig = rk.sub(n.add(1) / 2.0, axis=0).div(n, axis=0).where(elig).fillna(0.0)
    return sig
