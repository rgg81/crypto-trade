"""Defensive quality from the two-sidedness of taker flow, neutral to liquidity and to the market.

The lane's question is what "quality" means for a perpetual future, and how to own it without owning
the market. The seed answered with volatility: long the calm names, short the wild ones, then
subtract a beta overlay. Two things went wrong. Volatility *is* the market factor in crypto --
realised sigma and downside sigma each correlate about 0.7 with beta across this cross-section --
so the spread was a short-beta bet wearing a factor name. And the correction that removed the beta
put it back as dollars: forcing net beta to zero on a long-low-beta book adds roughly a third of
gross in net long market exposure, which is why the seed scored 74 in bull and 1.6 in bear when its
own thesis said the opposite.

This book measures quality where the market factor is not. For each name it takes the share of a
day's quote volume that crossed the spread on the buy side, and asks how far that share sits from
one half -- both in the typical day, and cumulatively across the window. A venue where both sides
trade patiently prints a share near 0.5 day after day. A venue where one side is systematically
paying up -- impatient, herding, retail-fragmented flow into somebody else's inventory -- prints a
lopsided share, and prints it in the same direction for weeks. The first is resilience, the second
is fragility, and the distance between them is nearly orthogonal to the market: the cross-sectional
correlation of this trait with beta is about 0.09, against 0.73 for realised volatility.

Raw, the trait is still contaminated. Deep names have two-sided flow *because* they are deep, so the
unadjusted spread is a long-majors / short-alts book, and it inverts whenever the majors are what is
being liquidated. So the liquidity factor is projected out: the requested weights are made
orthogonal to the cross-sectional rank of traded depth and to the constant in one least-squares
step, which makes the book simultaneously dollar-neutral and depth-neutral. What survives is flow
quality *within* a liquidity stratum, and that is what this lane is actually about. Measured over
the research window the residual book carries a realised market beta of about -0.02, so the market
factor is removed by the shape of the signal rather than by an overlay that has to be paid for.

Nothing here targets volatility. The book is emitted at gross 1.0 and the organizer's common risk
unit decides its size.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# A name needs this many days on which it actually traded before it is ranked at all.
MINIMUM_DAYS = 5
# Excess rise over the crash window that bars a *short*. Wider than the fall threshold on purpose:
# a squeeze is the mirror risk of a collapse, but it is slower and rarer, and a tight ceiling here
# would keep ejecting exactly the fragile names the book exists to be short of.
CRASH_POP = 0.50
# Per-name ceiling inside the book's own gross budget. The organizer caps a symbol at 0.20 of the
# executed book; this is tighter, and it binds on the residual before the risk unit rescales.
SYMBOL_CAP = 0.15
_DUST = 1e-6
_PRUNE = 5e-4


class DefensiveFlowQuality:
    """Long two-sided flow, short one-sided flow, orthogonal to depth and to the market."""

    # Trait window, in days. Long enough that a fortnight of noise cannot re-rank a venue, short
    # enough that one whose flow has genuinely turned one-sided is re-ranked within a quarter. The
    # measured plateau runs from about a month to about eleven weeks, and this sits in it so that
    # the whole two-step probe envelope stays inside the plateau rather than half outside it.
    window_days = 48
    # Weight on the *persistence* estimator relative to the *magnitude* estimator of one-sidedness.
    # Both measure the same thing and neither is obviously right: one asks how lopsided a typical
    # day is, the other whether the lopsidedness kept pointing the same way. Averaging their ranks
    # is an estimator-risk decision, not a fit.
    persistence_weight = 0.5
    # Lookback of the crash guard, in days.
    crash_days = 20
    # Excess log fall over that window which bars a name from the long leg outright. A defensive
    # book that keeps buying a name on its way to zero is not defensive: a constant-weight target in
    # a collapsing name is a martingale, and exactly one such name cost the unguarded version eight
    # points of equity inside a single month.
    crash_drop = 0.35
    # Blend of the exponential smoother, per decision.
    decay = 0.12
    # No-trade band: the gross distance the requested book must move before it is worth its spread.
    band = 0.08
    # Funding is a cashflow the organizer settles; nothing in this mechanism reads it, and saying
    # so is more honest than accepting an input the book never looks at.
    uses_funding = False

    def __init__(self) -> None:
        self._current: dict[str, float] = {}
        self._emitted: dict[str, float] = {}

    # -- interface -----------------------------------------------------------------------------

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        eligible = [str(symbol) for symbol in context.eligible_symbols]
        closes = toolkit.close_panel(context)
        if closes.empty or closes.shape[1] < 6:
            return self._smooth({}, eligible)
        volume = toolkit.column_panel(context, "quote_volume").reindex(columns=closes.columns)
        buys = toolkit.column_panel(context, "taker_buy_quote_volume").reindex(
            columns=closes.columns
        )
        if volume.empty or buys.empty:
            return self._smooth({}, eligible)

        bars = max(9, toolkit.bars_for_days(max(1.0, float(self.window_days))))
        typical, persistent, depth = self._flow_traits(volume, buys, bars)
        sigma = toolkit.realised_sigma(closes, bars)
        usable = typical.index.intersection(persistent.index).intersection(depth.index)
        usable = usable.intersection(sigma.index)
        usable = usable[sigma.reindex(usable).to_numpy(dtype=float) > 0.0]
        if len(usable) < 6:
            return self._smooth({}, eligible)

        share = min(1.0, max(0.0, float(self.persistence_weight)))
        fragility = (1.0 - share) * _rank(typical.reindex(usable)) + share * _rank(
            persistent.reindex(usable)
        )
        # Fragility is the high end of the rank, so the sign of the signal is negative by
        # construction: the book is long resilience and short fragility, never the other way.
        signal = -_rank(fragility)
        signal, barred = self._crash_guard(signal, closes)
        weights = signal / sigma.reindex(usable)
        weights = weights[weights.abs() > 0.0]
        if len(weights) < 4:
            return self._smooth({}, eligible, barred=barred)
        weights = _orthogonalise(weights, _rank(depth.reindex(usable)))
        return self._smooth(_budget(weights), eligible, barred=barred)

    # -- mechanism -----------------------------------------------------------------------------

    def _flow_traits(
        self, volume: pd.DataFrame, buys: pd.DataFrame, bars: int
    ) -> tuple[pd.Series, pd.Series, pd.Series]:
        """Two estimators of taker-flow one-sidedness, plus traded depth, per symbol.

        Everything is aggregated to calendar days first. An 8h bar's flow is dominated by which
        session it covers, and that intraday shape would otherwise read as a property of the venue.
        The typical-day estimator is a median rather than a mean, so one liquidation print cannot
        define a name's character; the persistence estimator deliberately is not, because a venue
        that is bought every day for two months is exactly what it is supposed to catch.
        """
        window_volume = volume.tail(bars)
        window_buys = buys.tail(bars)
        days = pd.DatetimeIndex(window_volume.index).floor("1D")
        daily_volume = window_volume.groupby(days).sum(min_count=1)
        daily_buys = window_buys.groupby(days).sum(min_count=1)
        traded = daily_volume.where(daily_volume > 0.0)
        enough = traded.notna().sum() >= MINIMUM_DAYS

        share = daily_buys.where(traded.notna()) / traded
        typical = (share - 0.5).abs().median().where(enough)
        total_volume = daily_volume.sum()
        aggregate = daily_buys.sum().where(total_volume > 0.0) / total_volume.where(
            total_volume > 0.0
        )
        persistent = (aggregate - 0.5).abs().where(enough)
        depth = np.log(traded).median().where(enough)
        return (_finite(typical), _finite(persistent), _finite(depth))

    def _crash_guard(
        self, signal: pd.Series, closes: pd.DataFrame
    ) -> tuple[pd.Series, frozenset[str]]:
        """Drop a name from the leg that a violent idiosyncratic move has made indefensible.

        The move is measured against the cross-sectional median of the same window, so a market-wide
        selloff does not empty the book; only a name coming apart on its own is ejected. The set of
        ejected names is returned as well as applied, because the smoother has to treat them
        differently: a stop that is subject to a no-trade band is not a stop.
        """
        window = max(3, toolkit.bars_for_days(max(1.0, float(self.crash_days))))
        recent = closes.tail(window + 1)
        if len(recent) < 2:
            return signal, frozenset()
        move = np.log(recent.iloc[-1] / recent.iloc[0]).replace([np.inf, -np.inf], np.nan)
        move = move.reindex(signal.index).dropna()
        if len(move) < 6:
            return signal, frozenset()
        excess = move - float(move.median())
        aligned = signal.reindex(excess.index)
        long_hits = excess.index[(excess < -float(self.crash_drop)) & (aligned > 0.0)]
        short_hits = excess.index[(excess > CRASH_POP) & (aligned < 0.0)]
        guarded = signal.copy()
        guarded.loc[long_hits] = 0.0
        guarded.loc[short_hits] = 0.0
        return guarded, frozenset(str(name) for name in long_hits.union(short_hits))

    # -- book keeping --------------------------------------------------------------------------

    def _smooth(
        self, raw: dict[str, float], eligible: list[str], *, barred: frozenset[str] = frozenset()
    ) -> dict[str, float] | None:
        """Blend toward the requested book, and hold when the move is not worth its own cost.

        A name the crash guard has ejected is the one exception: it leaves the book at once rather
        than decaying out of it, and its departure overrides the no-trade band. Without that, the
        stop is throttled by the very control that exists to stop the book paying for noise, and the
        result is a book whose worst fold depends on which day it happened to rebalance -- measured,
        that path dependence was worth up to sixty points of a fold score.
        """
        allowed = set(eligible)
        decay = min(1.0, max(0.0, float(self.decay)))
        override = False
        blended: dict[str, float] = {}
        # Sorted, not set order: Python randomises string hashing per process, and an unordered
        # accumulation makes the gross total differ in its last bit between runs. The charter
        # requires two clean runs to agree exactly, so the order is pinned here.
        for symbol in sorted(set(self._current) | set(raw)):
            if symbol not in allowed:
                continue
            previous = float(self._current.get(symbol, 0.0))
            if symbol in barred:
                if abs(previous) >= _PRUNE:
                    override = True
                continue
            value = (1.0 - decay) * previous + decay * float(raw.get(symbol, 0.0))
            if abs(value) >= _PRUNE:
                blended[symbol] = value
        total = sum(abs(value) for value in blended.values())
        if total > 1.0:
            blended = {symbol: value / total for symbol, value in blended.items()}
        self._current = blended
        move = sum(
            abs(blended.get(symbol, 0.0) - self._emitted.get(symbol, 0.0))
            for symbol in sorted(set(blended) | set(self._emitted))
        )
        if self._emitted and move < float(self.band) and not override:
            return None
        self._emitted = dict(blended)
        return dict(blended)


def _finite(values: pd.Series) -> pd.Series:
    return values.replace([np.inf, -np.inf], np.nan).dropna()


def _rank(values: pd.Series) -> pd.Series:
    """Cross-sectional rank on [-0.5, 0.5]: scale-free, and no single outlier owns the book."""
    clean = values.replace([np.inf, -np.inf], np.nan).dropna()
    if clean.empty:
        return pd.Series(dtype=float)
    if len(clean) == 1:
        return pd.Series(0.0, index=clean.index)
    return clean.rank(method="average").sub(0.5).div(len(clean)).sub(0.5)


def _orthogonalise(weights: pd.Series, factor: pd.Series) -> pd.Series:
    """Project the constant and one cross-sectional factor out of the requested weights.

    Removing the constant is dollar neutrality; removing the factor is liquidity neutrality. Doing
    both in one least-squares step is what turns the residual into a spread *within* a depth
    stratum rather than a bet on depth wearing a flow name.
    """
    aligned = factor.reindex(weights.index)
    usable = weights.index[aligned.notna()]
    if len(usable) < 4:
        return weights - float(weights.mean())
    design = np.column_stack(
        [np.ones(len(usable)), aligned.reindex(usable).to_numpy(dtype=float)]
    )
    response = weights.reindex(usable).to_numpy(dtype=float)
    coefficients, *_ = np.linalg.lstsq(design, response, rcond=None)
    residual = pd.Series(0.0, index=weights.index)
    residual.loc[usable] = response - design @ coefficients
    return residual


def _budget(weights: pd.Series, *, gross: float = 1.0) -> dict[str, float]:
    """Normalise to the gross budget and hold every name under its ceiling."""
    values = weights.replace([np.inf, -np.inf], np.nan).fillna(0.0)
    total = float(values.abs().sum())
    if not math.isfinite(total) or total <= 0.0:
        return {}
    values = values / total * gross
    if float(values.abs().max()) > SYMBOL_CAP:
        values = values.clip(-SYMBOL_CAP, SYMBOL_CAP)
        total = float(values.abs().sum())
        if total > gross:
            values = values / total * gross
    return {
        str(symbol): float(value)
        for symbol, value in values.items()
        if math.isfinite(value) and abs(value) > _DUST
    }


def build_strategy() -> DefensiveFlowQuality:
    return DefensiveFlowQuality()
