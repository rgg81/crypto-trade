"""Multi-horizon time-series trend with a bounded common-factor share.

Perpetual funding and cross-margin make a crypto move self-financing on the way up and
self-liquidating on the way down, and there is no closing auction to reset positioning overnight,
so a direction persists over weeks rather than reverting within a day. This book reads that
persistence across a dense geometric ladder of formation horizons -- five rungs spanning a band
whose geometric centre and width are the only two numbers that describe the book's speed -- and
normalises every rung by the volatility of its own holding period, so what sizes a name is
agreement between horizons rather than whichever name moved hardest.

One thing here is not in the naive form of the lane, and it is the whole of the research result.
A Binance top-50 cross-section is close to a one-factor market. Decompose the trend score into the
inverse-volatility-weighted cross-sectional mean -- the component that survives as net exposure
once weights are taken proportional to score/sigma -- plus the deviation from it, and the two legs
have almost opposite regime profiles: measured in sample, the common leg is strongly positive in
trending months and roughly -1.7 Sharpe in choppy ones, while the relative leg is mildly positive
in exactly those choppy months. Essentially all of a naive trend book's chop loss is the market
bet, not name selection.

So the common leg is passed through a saturating response before the book is built. Below the
saturation scale nothing happens and the book is the ordinary time-series trend book; above it the
market bet stops growing while the relative leg keeps its full size. That bounds the share of book
risk sitting in the single market factor without ever removing the factor, and -- the reason it is
built this way rather than as a smaller book -- it changes the *shape* of the book rather than its
size, so the organizer's ex-ante risk unit, which divides any uniform rescale straight back out,
cannot undo it.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit


class MultiHorizonTrend:
    """A dense ladder of trailing-return horizons, with the common component saturated."""

    # The mechanism is a function of closes alone. Declaring it keeps the funding frame out of
    # every decision context; a variant that starts reading funding must flip this back to True.
    uses_funding = False

    # --- formation band ---------------------------------------------------------------
    # Five rungs spaced geometrically between h_centre/sqrt(spread) and h_centre*sqrt(spread).
    # Parameterising the band by centre and width rather than by a list of horizons keeps
    # "how fast is this book" and "how many speeds does it average" on separate axes, and makes
    # the blend an average over a band instead of over three arbitrary points.
    h_centre_days = 21.0
    h_spread = 3.0
    n_rungs = 5

    # Per-rung clip on the holding-period t-statistic. A trailing return many sigma-root-h large
    # is usually one event rather than a trend, and it should not be allowed to size the book.
    clip_limit = 2.0

    # --- normalisation ----------------------------------------------------------------
    # Deliberately shorter than the slowest rung: the denominator should describe the risk the
    # book is about to carry, not the average risk over the whole formation window.
    sigma_bars = 90

    # --- shape ------------------------------------------------------------------------
    # Saturation scale of the risk-weighted common component, in units of the clipped
    # t-statistic. Small values bound the market-factor share of risk hard; large values
    # reproduce the naive time-series book exactly.
    net_scale = 0.18

    # Largest share of the pre-scalar book any one name may carry. Measured in sample this
    # almost never binds -- the book is diffuse over roughly forty names -- so it is insurance
    # against a degenerate cross-section, and it is deliberately not a declared dimension.
    symbol_cap = 0.15

    # --- turnover ---------------------------------------------------------------------
    smooth_decay = 0.25
    smooth_band = 0.05

    def __init__(self) -> None:
        # Held across decisions on purpose: a no-trade band can only suppress a small move if it
        # remembers what was last emitted. Both dictionaries are built from the streamed sequence
        # of decisions and from nothing else, so corrupting the future cannot reach back and
        # change an earlier decision.
        self._current: dict[str, float] = {}
        self._emitted: dict[str, float] = {}

    # -- signal ------------------------------------------------------------------------

    def _ladder(self) -> list[int]:
        """Bar counts for the rungs, de-duplicated so two that round together are counted once."""
        rungs = max(1, int(self.n_rungs))
        spread = max(1.0, float(self.h_spread))
        shortest = float(self.h_centre_days) / math.sqrt(spread)
        step = spread ** (1.0 / (rungs - 1)) if rungs > 1 else 1.0
        bars: list[int] = []
        for rung in range(rungs):
            count = toolkit.bars_for_days(shortest * (step**rung))
            if count >= 1 and count not in bars:
                bars.append(count)
        return bars

    def _scores(self, panel: pd.DataFrame, sigma_daily: pd.Series) -> pd.Series:
        """Mean clipped, holding-period-normalised trailing return, per symbol."""
        columns: dict[int, pd.Series] = {}
        for bars in self._ladder():
            returns = toolkit.trailing_return(panel, bars)
            if returns.empty:
                continue
            # Dividing by sigma*sqrt(h) asks the only question worth asking of a trailing return:
            # is it larger than what this symbol's own volatility could have produced by accident
            # over the same span? Without it the slowest rung and the wildest name dominate.
            span = sigma_daily * math.sqrt(bars / toolkit.BARS_PER_DAY)
            scaled = returns.div(span).replace([np.inf, -np.inf], np.nan)
            columns[bars] = scaled.clip(-float(self.clip_limit), float(self.clip_limit))
        if not columns:
            return pd.Series(dtype=float)
        # skipna is the "enough history for" rule: a young symbol contributes the rungs it can
        # actually measure and is not punished for missing the slow ones.
        return pd.DataFrame(columns).mean(axis=1, skipna=True).dropna()

    def _bound_common(self, scores: pd.Series, sigma: pd.Series) -> pd.Series:
        """Saturate the risk-weighted common component of the cross-section.

        The weights this book sends are proportional to score/sigma, so the part that survives as
        net exposure is the inverse-sigma weighted mean of the score, not the plain mean.
        Removing that mean leaves a leg with exactly zero net weight; adding back a saturated
        version of it puts the market bet in with a ceiling on it.
        """
        inverse = (1.0 / sigma.reindex(scores.index)).replace([np.inf, -np.inf], np.nan)
        total = float(inverse.sum(skipna=True))
        if not math.isfinite(total) or total <= 0.0:
            return scores
        common = float((scores * inverse).sum(skipna=True) / total)
        if not math.isfinite(common):
            return scores
        scale = float(self.net_scale)
        if not math.isfinite(scale) or scale <= 0.0:
            return scores - common
        return scores - common + scale * math.tanh(common / scale)

    # -- book --------------------------------------------------------------------------

    def _blend_and_emit(
        self, raw: Mapping[str, float], eligible: Sequence[str]
    ) -> dict[str, float] | None:
        """Exponential blend, prune, then either emit the new book or hold the old one.

        Two costs are being managed: rebalancing all the way to a fresh signal every day pays the
        full spread on noise, and a book whose weights jitter around a stable view pays repeatedly
        for nothing. The blend damps the first, the band suppresses the second.

        Every iteration order here is explicit. A set's iteration order depends on the
        interpreter's hash seed and a float sum taken in two different orders is not
        bit-identical; two independent clean runs of this candidate have to agree exactly, so
        nothing in this method is allowed to iterate an unordered container.
        """
        allowed = set(map(str, eligible))
        decay = float(self.smooth_decay)
        blended: dict[str, float] = {}
        for symbol in sorted(set(self._current) | set(raw)):
            if symbol not in allowed:
                continue
            previous = float(self._current.get(symbol, 0.0))
            target = float(raw.get(symbol, 0.0))
            value = (1.0 - decay) * previous + decay * target
            if abs(value) >= 5e-4:
                blended[symbol] = value
        total = sum(abs(value) for value in blended.values())
        if total > 1.0:
            blended = {symbol: value / total for symbol, value in blended.items()}
        self._current = blended
        move = 0.0
        for symbol in sorted(set(blended) | set(self._emitted)):
            move += abs(blended.get(symbol, 0.0) - self._emitted.get(symbol, 0.0))
        if self._emitted and move < float(self.smooth_band):
            # Too small a move to be worth its own spread: hold what is already on.
            return None
        self._emitted = dict(blended)
        return dict(blended)

    def target_weights(self, context, *, seed: int):
        # Once a day. Three decisions a day would pay the spread three times over for a signal
        # whose shortest rung is nearly two weeks long.
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        if panel.empty:
            return {}
        sigma = toolkit.realised_sigma(panel, bars=int(self.sigma_bars))
        if sigma.empty:
            return {}
        scores = self._scores(panel, sigma / math.sqrt(365.0))
        if scores.empty:
            return {}
        scores = self._bound_common(scores, sigma)
        scores = scores.replace([np.inf, -np.inf], np.nan).dropna()
        if scores.empty:
            return {}

        # Sorted, so every dictionary downstream is insertion-ordered by symbol and every float
        # sum is accumulated in the same order on every run.
        signals = {
            str(symbol): float(scores[symbol])
            for symbol in sorted(map(str, scores.index))
            if float(scores[symbol]) != 0.0
        }
        if not signals:
            return {}
        # neutral is off because the lane is time-series, not cross-sectional: when the horizons
        # agree the net tilt IS the signal. It is bounded above, not balanced away.
        raw = toolkit.vol_parity(
            signals, sigma, gross=1.0, symbol_cap=float(self.symbol_cap), neutral=False
        )
        return self._blend_and_emit(raw, context.eligible_symbols)


def build_strategy() -> MultiHorizonTrend:
    return MultiHorizonTrend()
