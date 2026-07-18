"""team-06 strategy - t06-ls-ratio-contrarian-v1.

Fade per-coin extremes in the global long/short ACCOUNT ratio (retail crowd). Pure,
deterministic, past-only. The strategy emits RAW signed weights only; the engine owns the
eligibility mask, gross normalisation, per-name / net caps, the decision lag, taker +
slippage costs, funding P&L, and portfolio vol-targeting.

Frozen pipeline (research_brief.md QE SPEC 10.2 - the pandas calls are load-bearing and are
replicated verbatim; every parameter is fixed, no alternatives):

  x  = log of the ls_accounts ratio panel (non-positive -> NaN)
  mu = per-coin trailing rolling mean (W=90, min_periods=45), current bar included
  sd = per-coin trailing rolling std  (W=90, min_periods=45); std==0 -> NaN
  z  = ((x - mu) / sd) clipped to +/-3
  s  = -z  (fade the crowd), EMA-smoothed (span=3), re-masked to the raw-signal NaN pattern
  w  = centered cross-sectional rank of s over eligible AND non-NaN names, in [-0.5, +0.5]

Uses ONLY aux["ls_accounts"] and aux["eligibility"]; klines (pn) are untouched. No
randomness (aux["seed"] unused). rolling / ewm(adjust=True) are strictly trailing and rank
is per-row, so every row is computable from data at or before that row (past-only).
"""

from __future__ import annotations

import numpy as np

PANEL = "ls_accounts"
W = 90
MIN_PERIODS = 45
CLIP = 3.0
EMA_SPAN = 3


def build_raw_weights(pn, aux):
    R = aux[PANEL]  # 8h sums of 5-min ratio snapshots; NaN/zero-corrupted pre-2023
    E = aux["eligibility"]  # bool panel, same grid (organizer, past-only)
    x = np.log(R.where(R > 0.0))  # zeros/negatives -> NaN (e01: 2022 zero plague)
    mu = x.rolling(W, min_periods=MIN_PERIODS).mean()  # current bar INCLUDED (same-bar)
    sd = x.rolling(W, min_periods=MIN_PERIODS).std()
    z = ((x - mu) / sd.where(sd > 0.0)).clip(-CLIP, CLIP)
    s = -z  # FADE the per-coin positioning extreme
    s = s.ewm(span=EMA_SPAN, min_periods=1).mean().where(s.notna())
    #   ^ pandas defaults: adjust=True, ignore_na=False; the trailing .where(s.notna())
    #     re-masks bars whose raw signal is NaN (EMA must not invent values there)
    avail = s.where(E)  # rank only eligible AND non-NaN names
    r = avail.rank(axis=1)  # pandas defaults: ascending, ties -> average
    n = avail.notna().sum(axis=1)
    w = r.sub((n + 1) / 2.0, axis=0).div(n.where(n > 1), axis=0)  # centered rank in [-0.5, 0.5]
    return w
