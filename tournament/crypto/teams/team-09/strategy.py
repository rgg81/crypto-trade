"""team-09 strategy — trade-size composition cross-section (research_brief.md Section 9).

Mechanism: the kline ``trades`` field makes the marginal participant observable. Average
trade size (dollars per print = quote_volume / trades) separates a retail swarm (trade count
explodes while average trade size SHRINKS) from large-trade flow (average trade size RISES).
We LONG names whose average trade size is rising (accumulation / large-trade flow) and SHORT
names whose average trade size is shrinking (retail swarm — marginally overpriced).

Signal, per name i, candle t (same-bar info is legal at t's close):
  - recent-window (W) ratio-of-sums average trade size vs an overlap-free baseline-window (B)
    average trade size, shifted W so the windows never overlap;
  - composition score comp = log(recent_ats / baseline_ats): positive = rising, negative =
    shrinking; scale-free across names and time;
  - mask to eligible names BEFORE ranking, then a per-candle cross-sectional centered rank;
  - rows with fewer than MIN_NAMES valid eligible names -> flat (thin-universe guard).

Pure, deterministic, past-only. Uses only pn['quote_volume'], pn['trades'] and
aux['eligibility'] — no price, no OI, no funding, no positioning ratios, no randomness
(aux['seed'] unused). Column-set agnostic (every op is panel-wide) and NaN-tolerant by
construction (young / dead names and thin rows become NaN = flat). The engine owns the
eligibility mask, gross normalisation, per-name / net caps, the decision lag, taker +
slippage costs, funding P&L, and vol-targeting — this returns RAW signed weights only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Section-9 constants (frozen). W = recent composition window (2 weeks of 8h candles);
# B = baseline window; MPW / MPB = min_periods = ceil(0.8 * window); MIN_NAMES = row validity.
W = 42
B = 90
MPW = 34  # ceil(0.8 * 42)
MPB = 72  # ceil(0.8 * 90)
MIN_NAMES = 10


def build_raw_weights(pn: dict, aux: dict) -> pd.DataFrame:
    qv = pn["quote_volume"]
    tr = pn["trades"]
    elig = aux["eligibility"]

    # 1-2: ratio-of-sums average trade size — recent (W) and overlap-free baseline (B, shifted W).
    qs_W = qv.rolling(W, min_periods=MPW).sum()
    ts_W = tr.rolling(W, min_periods=MPW).sum()
    qs_B = qv.rolling(B, min_periods=MPB).sum()
    ts_B = tr.rolling(B, min_periods=MPB).sum()

    # 3: composition score — positive = rising avg trade size, negative = retail swarm.
    comp = np.log((qs_W / ts_W) / (qs_B / ts_B).shift(W))

    # 4: mask BEFORE ranking — ranks are computed among eligible names only (order-affecting;
    # do not move this step).
    comp = comp.replace([np.inf, -np.inf], np.nan).where(elig)

    # 5-6: per-candle cross-sectional centered rank (pandas defaults: ascending, average ties,
    # NaNs excluded).
    r = comp.rank(axis=1)
    sig = r.sub(r.mean(axis=1), axis=0).div(r.count(axis=1).clip(lower=1), axis=0)

    # 7: rows with fewer than MIN_NAMES valid eligible names -> entire row flat.
    n_valid = comp.notna().sum(axis=1)
    sig = sig.where(n_valid >= MIN_NAMES)

    # 8: raw signed weights (LONG high comp = rising avg trade size, SHORT low comp = retail
    # swarm; NaN = flat). No h-smoothing step (h=1 => identity). Engine owns everything else.
    return sig
