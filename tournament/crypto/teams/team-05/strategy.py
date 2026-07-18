"""team-05 — cross-sectional taker-flow imbalance continuation (t05-taker-flow-imbalance-v2).

Mechanism: ``taker_buy_quote_volume / quote_volume`` is the dollar-weighted aggressive-buyer
share of each 8h candle. Crypto perp flow is retail-dominated and herding-prone, so sustained
one-sided aggressive buying arrives in multi-day waves and is absorbed by market makers with a
lag; a name whose smoothed aggressive-buy share is high has demand pressure not yet fully
priced, and continues. sign = +1 (continuation): long the high aggressive-buy-share names,
short the low ones.

Signal (frozen QE SPEC §9, implement exactly; no hidden choices):
  W = 21 trailing candles, MIN_PERIODS = 16 (= ceil(0.75 * 21)).
  sig = rolling-sum(taker_buy_quote_volume) / rolling-sum(quote_volume) - 0.5,
        NaN where the denominator sum is <= 0 or fewer than 16 non-NaN candles exist.
  Gate on same-bar eligibility (widening-safe reindex; unknown/synthetic columns -> False),
  cross-sectional percentile-rank the eligible non-NaN names, row-demean to a sum-zero
  long/short book, and fill NaN/ineligible with 0.0 (flat). sign is +1: no negation.

Pure, deterministic, past-only, column-set agnostic (symbols derived from the panel columns at
runtime). ``aux["seed"]`` is intentionally unused (no randomness). The evaluator owns the
eligibility re-masking, gross normalisation, per-name / net caps, the decision lag, taker +
slippage costs, funding P&L, and portfolio vol-targeting — none of that is applied here.
"""

from __future__ import annotations

import pandas as pd

W = 21
MIN_PERIODS = 16  # ceil(0.75 * 21)


def build_raw_weights(pn: dict[str, pd.DataFrame], aux: dict) -> pd.DataFrame:
    """Raw signed weight panel (candle-index x symbol-columns; NaN filled to 0.0 = flat)."""
    tb = pn["taker_buy_quote_volume"]  # candle x symbol, float
    qv = pn["quote_volume"]

    num = tb.rolling(window=W, min_periods=MIN_PERIODS).sum()  # trailing sums, past-only,
    den = qv.rolling(window=W, min_periods=MIN_PERIODS).sum()  # NaNs skipped by rolling.sum
    sig = num / den.where(den > 0) - 0.5  # NaN if den<=0 or <16 non-NaN candles

    elig = (
        aux["eligibility"]
        .reindex(index=sig.index, columns=sig.columns)  # widening-safe alignment
        .fillna(False)
        .astype(bool)  # unknown/synthetic cols -> False
    )
    masked = sig.where(elig)  # ineligible or NaN -> NaN

    r = masked.rank(axis=1, pct=True)  # ascending, average ties, NaN excluded from the rank
    w = r.sub(r.mean(axis=1), axis=0)  # row-demeaned -> sum-zero long/short book
    return w.fillna(0.0)  # NaN = flat (sign is +1: NO negation anywhere)
