"""Team 04 -- market-residual cross-sectional momentum, three-horizon composite score.

Mechanism
---------
Roughly two thirds of an individual top-20 perpetual's 8h return variance is one common factor
(measured on the in-sample rows: median R^2 of 0.68 against the equal-weight cross-section), and
loadings on it are dispersed -- 0.60 for BTC against 1.64 for the most reflexive alt. A
cross-sectional ranking of raw trailing returns is therefore substantially a ranking of beta:
in a formation window where the market rose, the top of the ranking is populated by the names
with the largest loadings rather than the names with the strongest own-move. This strategy
removes an estimated market component first and ranks what is left.

Causality
---------
Everything is computed from rows the organiser hands to this process, and every one of those is
at or before the decision:

* the market factor at past bar s is the equal-weight mean log return, across the symbols that
  are ELIGIBLE AT THE DECISION, of the bar closing at s. Membership at the decision is known at
  the decision; no future reconstitution is consulted, and no symbol enters the factor that the
  organiser did not name as a member at this boundary.
* beta is an ordinary least squares slope with an intercept, fitted on the trailing
  ``BETA_WINDOW`` bars ENDING at the decision. It never sees a row at or after the fill.
* the formation sum ends ``SKIP_BARS`` bars before the decision, so the most recent bar -- the one
  whose close is closest to the unobserved execution open -- does not enter the signal at all.
* the strategy holds no state between calls. Every decision is a pure function of that decision's
  context, which makes the causality claim checkable by inspection rather than by trusting an
  accumulator.

The intercept is deliberately NOT subtracted. The market component is ``beta_i * m_s``; the
intercept is the coin's own drift over the estimation window, which is the very thing a momentum
lane is trying to rank. Subtracting it converts the signal into a short-horizon-versus-long-horizon
contrast, and measured on the in-sample rows it turns the sign of the edge over.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

# --- neighbourhood coordinates: module-level, one plain numeric literal each -------------------
BETA_WINDOW = 270
"""Bars of history the causal market-beta regression is fitted on (270 bars = 90 days)."""

FORMATION_BARS = 63
"""Bars of residual return summed into the cross-sectional score (63 bars = 21 days).

The score is a composite over three formation lengths derived from this one constant --
two thirds of it, it, and twice it -- each z-scored across the cross-section before averaging.
A single formation length is a point estimate of a horizon nobody knows; averaging three makes
the rank vector move more slowly and stops the choice of horizon being a free parameter with a
best value. The derivation is at import, off the constant itself, so the declared neighbourhood
moves all three windows together."""

FORMATION_WINDOWS = (
    max(2, round(FORMATION_BARS * 2 / 3)),
    FORMATION_BARS,
    FORMATION_BARS * 2,
)

SKIP_BARS = 1
"""Most recent bars excluded from the formation sum."""

REBALANCE_BARS = 21
"""Boundaries between strategy rebalances; every other boundary holds quantities."""

REBALANCE_PHASE = 16
"""Offset of the rebalance clock within its cadence."""

SLEEVE_FRACTION = 0.34
"""Fraction of the eligible cross-section taken into the LONG sleeve (thirds, per the charter)."""

SHORT_SLEEVE_FRACTION = 0.20
"""Fraction taken into the SHORT sleeve. Narrower than the long sleeve on purpose: measured on
the in-sample rows, the market's own drift means a diversified short third of a top-20 crypto
universe does not fall in absolute terms, and `short_gross_pnl > 0` is a hard floor. Concentrating
the short sleeve on the deepest residual losers is the only in-lane lever on it."""

MINIMUM_MEMBERS = 9
"""Below this many usable names the cross-section is too thin to rank; the book holds."""


def _closes(context: DecisionContext) -> pd.DataFrame:
    """Wide close-price frame indexed by bar open time, one column per eligible symbol."""
    series = {}
    for symbol in context.eligible_symbols:
        frame = context.bars.get(symbol)
        if frame is None or len(frame) < 2:
            continue
        series[symbol] = pd.Series(
            frame["close"].to_numpy(dtype=float), index=pd.DatetimeIndex(frame["open_time"])
        )
    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).sort_index()


def _score(context: DecisionContext) -> dict[str, float]:
    """Residual momentum per eligible symbol, or an empty mapping if the window is not covered."""
    closes = _closes(context)
    if closes.empty:
        return {}
    need = BETA_WINDOW + SKIP_BARS + 1
    if len(closes) < need:
        return {}
    tail = closes.iloc[-need:]
    values = tail.to_numpy(dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        returns = np.log(values[1:] / values[:-1])
    # A column is usable only if the whole regression window is present; a partially listed
    # symbol has no causal beta and is simply not ranked.
    usable = np.isfinite(returns).all(axis=0)
    if int(usable.sum()) < MINIMUM_MEMBERS:
        return {}
    returns = returns[:, usable]
    symbols = [s for s, keep in zip(tail.columns, usable, strict=True) if keep]

    market = returns.mean(axis=1)
    end = returns.shape[0] - SKIP_BARS
    window_y = returns[:end][-BETA_WINDOW:]
    window_x = market[:end][-BETA_WINDOW:]
    if window_y.shape[0] < BETA_WINDOW:
        return {}
    centred_x = window_x - window_x.mean()
    variance = float((centred_x * centred_x).sum())
    if not math.isfinite(variance) or variance <= 0.0:
        return {}
    beta = (centred_x[:, None] * (window_y - window_y.mean(axis=0))).sum(axis=0) / variance

    total = np.zeros(window_y.shape[1])
    for length in FORMATION_WINDOWS:
        if window_y.shape[0] < length:
            return {}
        residual = window_y[-length:].sum(axis=0) - beta * float(window_x[-length:].sum())
        spread = float(residual.std())
        if not math.isfinite(spread) or spread <= 0.0:
            return {}
        total = total + (residual - float(residual.mean())) / spread
    score = total / len(FORMATION_WINDOWS)
    return {
        symbol: float(value)
        for symbol, value in zip(symbols, score, strict=True)
        if math.isfinite(value)
    }


class MarketResidualThirds:
    """Equal-weight long/short thirds on the causal market-residual momentum score."""

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> Mapping[str, float] | None:
        index = int(
            (context.decision_time - pd.Timestamp("2020-08-17T00:00:00Z"))
            // pd.Timedelta(hours=8)
        )
        if index % REBALANCE_BARS != REBALANCE_PHASE % REBALANCE_BARS:
            return None
        scores = _score(context)
        if len(scores) < MINIMUM_MEMBERS:
            return None
        ordered = sorted(scores.items(), key=lambda item: (item[1], item[0]))
        long_width = max(1, int(round(len(ordered) * SLEEVE_FRACTION)))
        short_width = max(1, int(round(len(ordered) * SHORT_SLEEVE_FRACTION)))
        shorts = ordered[:short_width]
        longs = ordered[-long_width:]
        weights: dict[str, float] = {}
        for symbol, _ in longs:
            weights[symbol] = 0.5 / len(longs)
        for symbol, _ in shorts:
            weights[symbol] = -0.5 / len(shorts)
        return weights


def build_strategy() -> MarketResidualThirds:
    return MarketResidualThirds()
