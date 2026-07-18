"""team-03 — BTC-beta-residual cross-sectional momentum (family t03-btc-residual-momentum-v1).

Raw signed weight builder for crypto-cup-01. This is a faithful, literal implementation of the
QE SPEC (research_brief.md §10). It is a PURE, DETERMINISTIC, PAST-ONLY function of its inputs:
no file I/O, no network, no subprocess, no wall clock, no randomness (aux['seed'] is NOT used —
the strategy is deterministic by construction). Only numpy/pandas are imported.

Mechanism (see research_brief.md §1): rank the weekly top-40 on trailing momentum of the
BTC-beta *residual* return e_i = r_i - beta_i * m (m = equal-weighted eligible-mean market
factor), long persistent residual winners / short persistent residual losers via a centered
cross-sectional percentile rank, EMA-smoothed for turnover. Residualizing strips the common
market factor so the book is near-market-neutral and survives common crashes structurally.

The engine (portfolio_tournament) owns everything after this function: the eligibility zeroing,
gross normalisation, the 0.10/0.25 caps, the .shift(1) decision lag, taker+slippage costs,
funding P&L, and the portfolio vol-target. This function must NEVER pre-apply any of those.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Fixed parameters (FINAL per QE SPEC §10 — no free parameters remain).
W_BETA = 270            # rolling-beta window (candles)
MP_BETA = 135           # rolling-beta min_periods = W_BETA // 2
L = 63                  # formation window (candles)
MP_L = 51               # formation min_periods = ceil(0.8 * L)
G = 3                   # skip-gap (candles) — shift the score BEFORE cross-sectional masking
K_EMA = 3               # turnover-smoothing EMA span
BETA_CLIP_LO = 0.0      # beta clip lower (guards thin-history blowups); fixed, not tuned
BETA_CLIP_HI = 3.0      # beta clip upper
MIN_FACTOR_NAMES = 5    # minimum eligible+valid names to define the market factor at t


def build_raw_weights(pn, aux):
    """Return raw signed weights (candle-index x symbol-columns); NaN/flat -> 0.

    Order of operations is normative (QE SPEC §10). Symbol set is derived from the panel
    columns at runtime — never hard-coded. Eligibility is reindexed to the panel's index AND
    columns with fill_value False, so any widened/synthetic column is permanently ineligible
    (score NaN -> weight 0), and the function never crashes on unknown columns.
    """
    close = pn["close"]                                   # DatetimeIndex x symbols
    elig = (
        aux["eligibility"]
        .reindex(index=close.index, columns=close.columns)
        .fillna(False)
        .astype(bool)
    )                                                     # widening-safe: unknown cols -> False

    r = np.log(close.where(close > 0)).diff()             # log returns; NaN-tolerant
    valid = r.notna() & elig
    m = r.where(valid).mean(axis=1)                       # EW eligible-mean market factor
    m = m.where(valid.sum(axis=1) >= MIN_FACTOR_NAMES)    # need >= MIN_FACTOR_NAMES names

    cov = r.rolling(W_BETA, min_periods=MP_BETA).cov(m)   # column-wise rolling cov vs m
    var = m.rolling(W_BETA, min_periods=MP_BETA).var()
    beta = cov.div(var, axis=0).clip(BETA_CLIP_LO, BETA_CLIP_HI)

    e = r.sub(beta.mul(m, axis=0))                        # residual; NaN if any input NaN
    s = e.rolling(L, min_periods=MP_L).mean() / e.rolling(L, min_periods=MP_L).std()
    s = s.replace([np.inf, -np.inf], np.nan)              # guard sd==0 degenerate rows
    s = s.shift(G)                                        # skip-gap G (shift BEFORE masking)
    s = s.where(elig)                                     # rank only the CURRENT top-40

    rk = s.rank(axis=1, pct=True)                         # method='average', na_option='keep'
    w = rk.sub(rk.mean(axis=1), axis=0)                   # centered rank => exact zero-sum
    w = w.fillna(0.0)                                     # NaN = flat
    w = w.ewm(span=K_EMA, adjust=True).mean()             # turnover smoothing K_EMA
    return w                                              # raw signed weights; engine owns rest
