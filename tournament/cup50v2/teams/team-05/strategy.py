"""Receive the funding paid by the crowded side, and stand aside while the crowd is changing.

Funding is the price leveraged traders pay to hold a perpetual, so the side paying it is the
crowded one.  Four facts about that premium organise this source.

The first is that the premium is a *spread*, not a level.  Receiving it means being short the
names the crowd is paying to be long and long the names the crowd is paying to be short, at the
same time, in the same risk size.  A book that only takes whichever side happens to be extreme is
not collecting a spread; it is taking a direction, and its result is the direction's result.  So
the cross-section is ranked and the book is always two-sided by construction: each side receives
exactly half the risk budget, and the net is zero whatever funding happens to be doing.

The second is that the tail of the funding distribution is a different state from its body.  A
name whose rate has run far out is not a better version of a name whose rate is merely high --
it is the positioning that liquidates.  This source therefore refuses to size by the magnitude of
the rate.  It ranks, which spends the same risk on the tenth-highest rate as on the highest, and
it stands aside entirely from any name whose latest rate is a tail event in its own trailing
history.

The third is the one that decides what happens in a cascade, and it is about the *change* in
funding rather than its level.  Liquidating crowded longs is not this book's problem: that is the
event its short leg is paid for.  The problem is the aftermath.  Once the cascade has run, funding
flips broadly negative, a level-based guard sees a merely-negative rate rather than a tail, and a
carry book rotates long into names that are still being liquidated.  So the stand-aside here is
judged on funding term structure -- how far a name's *current* funding has moved from its own
trailing level -- and it is judged on current state rather than on the averaged carry the position
is built from.  A guard whose reaction time is tied to the averaging window of the signal it is
guarding is, in a week when funding flips sign, looking at a picture that is a fortnight old.

The fourth is that all of the above is computed on the funding leg, and the loss arrives through
the price leg.  Funding says which side of a name pays; it does not say whether the name is in the
middle of being liquidated.  A carry book is long whatever the crowd is paying most to be short,
and the thing the crowd is paying most to be short is sometimes a name on its way to zero.  So the
last stand-aside is a price one, and it is deliberately side-aware rather than symmetric: a name
far below its own recent high may still be shorted, and a name far above its own recent low may
still be held long -- what is refused is only the side that stands in front of the move.  A
symmetric exclusion would throw away the leg the premium is actually earned on.

Turnover is treated as a first-class cost rather than an afterthought.  A funding ranking moves
over weeks, so a book that chases it daily pays the spread three times over to express a view it
already held.  The blend is slow and the no-trade band is wide, and the book is reconstituted only
when the move it wants is worth its own cost.

Funding settles every 4h for some symbols and eras and every 8h for others, so ``settlements``
counts events rather than days: the averaging window is defined in the units the premium actually
accrues in, and a symbol on a faster clock is deliberately averaged over a shorter span of wall
time.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# The own-history tail guard is judged against a symbol's own funding regime, not the
# cross-section's: what counts as an extreme rate for a high-beta alt is unremarkable for BTC, so
# each name is scored against itself.  540 settlements is 180 days on the canonical 8h clock.
GUARD_HISTORY = 540
GUARD_MINIMUM = 60

# Below this many surviving names the cross-section is too thin for a rank to mean anything, and
# a two-sided book cannot be built without one side being a single opinion.  The book decays out
# rather than concentrating.
MINIMUM_BREADTH = 12

# Well inside the organizer's 0.20 per-symbol ceiling.  A rank book over a fifty-name section
# never approaches it; the cap exists so that a thin section cannot quietly become a pair trade.
SYMBOL_CAP = 0.15


class FundingCarryCrowdingGuarded:
    """Rank by carry, stand aside on the movers and on the side the price forbids."""

    settlements = 21
    z_guard = 2.5
    trim = 3
    decay = 0.02
    band = 0.10
    # The guard's two timescales, in settlements, and deliberately NOT tied to ``settlements``.
    # A guard whose reaction time is the averaging window of the signal it guards is looking at a
    # fortnight-old picture in the week that matters.  Three settlements is one day on the
    # canonical 8h clock; twenty-one is a week.
    state_window = 3
    reference_window = 21
    # The price-leg stand-aside, and the one number here that is a judgement rather than a
    # structure.  ``price_drop`` is measured against the name's own extreme over ``price_bars``
    # bars -- ninety eight-hour bars is thirty days -- so it is a freefall measure rather than a
    # cycle-drawdown measure, and it does not empty the book in a slow bear.  It is held fixed
    # and undeclared on purpose: measured in sample, the guard protects the cascade fold at 0.45
    # and at 0.50 and stops protecting it somewhere between 0.50 and 0.55, so a declared axis
    # probed two steps out would be an axis that walks off that edge.  0.45 is the protective
    # side of it, bought at about six points of centre score and six of bull-regime score.
    price_drop = 0.45
    price_bars = 90
    # A spread needs both legs.  Below this many names on a side the surviving book is a handful
    # of opinions rather than a cross-section, and the per-symbol cap would leave it
    # under-deployed anyway; the book decays out instead of holding a direction.
    minimum_side = 4
    # 0 = judge extremity on the current level; 1 = judge it on the change from the trailing
    # level.  Held as a numeric attribute so the choice is measurable rather than asserted.
    term_structure = 1.0

    def __init__(self) -> None:
        # Held as strategy state and rebuilt from the streamed replay like everything else: the
        # smoother starts empty, so the first decision of a run has nothing to hold on to.
        self._smoother = toolkit.TargetSmoother(decay=0.02, band=0.10)

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None

        # Read the tunables at every decision rather than at construction: the evaluator applies
        # declared parameters to the instance after ``build_strategy()`` has returned, and a
        # neighbourhood point that could not reach the smoother would be an inert dimension.
        smoother = self._smoother
        smoother.decay = float(self.decay)
        smoother.band = float(self.band)

        settlements = max(1, int(self.settlements))
        state_window = max(1, int(self.state_window))
        reference_window = max(1, int(self.reference_window))
        trim = max(0, int(self.trim))
        guard = float(self.z_guard)
        term = float(self.term_structure)
        drop = float(self.price_drop)
        price_bars = max(2, int(self.price_bars))
        minimum_side = max(1, int(self.minimum_side))

        history = toolkit.funding_by_symbol(context)
        carry: dict[str, float] = {}
        pressure: dict[str, float] = {}
        for symbol in map(str, context.eligible_symbols):
            series = history.get(symbol)
            if series is None or series.empty:
                continue
            clean = series.replace([np.inf, -np.inf], np.nan).dropna()
            if len(clean) < max(settlements, reference_window, GUARD_MINIMUM):
                continue
            if self._is_crowded(clean, guard):
                continue
            level = float(clean.tail(settlements).mean())
            state = float(clean.tail(state_window).mean())
            reference = float(clean.tail(reference_window).mean())
            if not (math.isfinite(level) and math.isfinite(state) and math.isfinite(reference)):
                continue
            carry[symbol] = level
            # Term structure: where funding is now, relative to where it has been.  The reference
            # is the guard's own trailing window, not the carry window, so how fast the guard
            # reacts does not change when the position signal is re-averaged.  With
            # ``term_structure`` at zero this degenerates to the current level, which is the
            # comparison the choice has to beat.
            pressure[symbol] = state - term * reference

        section = self._stand_aside(
            pd.Series(carry, dtype=float), pd.Series(pressure, dtype=float), trim
        )
        if len(section) < MINIMUM_BREADTH:
            # No opinion is a real state for this lane.  A cross-section too thin or too uniformly
            # guarded to rank should let the book decay out, not force a position into whatever
            # survived the guard.
            return smoother.update({}, context.eligible_symbols)

        # Positive funding means longs pay shorts, so the carry side of a high-funding name is
        # short.  Ranking rather than scaling by the rate is the guard restated as sizing: the
        # highest rate in the section is worth the same risk as the next one, so no amount of
        # funding extremity can buy a position size.
        signals = -toolkit.cross_sectional_rank(section)
        signals = signals[signals != 0.0]
        if signals.empty:
            return smoother.update({}, context.eligible_symbols)

        # Everything above is the funding leg.  The price leg now removes the side that would be
        # standing in front of a move, and only that side.
        panel = toolkit.close_panel(context, symbols=list(map(str, signals.index)))
        signals = self._price_stand_aside(signals, panel, drop, price_bars, minimum_side)
        if signals is None:
            return smoother.update({}, context.eligible_symbols)

        # The signal needs no bars, but the sizing does: equal carry rank on a wild name and a
        # calm one is not equal risk, so names are levelled by their own realised volatility.
        sigma = toolkit.realised_sigma(panel)
        raw = toolkit.vol_parity(signals.to_dict(), sigma, neutral=True, symbol_cap=SYMBOL_CAP)
        return smoother.update(raw, context.eligible_symbols)

    @staticmethod
    def _price_stand_aside(
        signals: pd.Series, panel: pd.DataFrame, drop: float, bars: int, minimum_side: int
    ) -> pd.Series | None:
        """Refuse the long side of a name in freefall and the short side of one squeezing.

        Both distances are measured against the name's own extreme inside the same trailing
        window, so the rule is scale-free and needs no cross-sectional comparison: a name that has
        merely drifted is untouched however loudly the rest of the section is moving.  The two
        thresholds are the same distance in ratio terms rather than the same percentage: a fall of
        ``price_drop`` and the rise that exactly undoes it are one number, so a 45% freefall and an
        82% squeeze are treated as the same dislocation.  Reading them as the same percentage
        makes the short-side rule far stricter than the long-side one, and in a bull market that
        empties one leg of a spread book that has to have two.  Returning ``None`` means the
        surviving book is too one-sided to be a spread, which is a real state and is answered by
        letting the existing book decay rather than by holding a direction.
        """
        if panel.empty:
            return None
        window = panel.tail(bars)
        if len(window) < 2:
            return signals
        high = window.max()
        low = window.min()
        last = window.iloc[-1]
        keep: dict[str, float] = {}
        for symbol, value in signals.items():
            name = str(symbol)
            top, bottom, close = (
                float(high.get(name, float("nan"))),
                float(low.get(name, float("nan"))),
                float(last.get(name, float("nan"))),
            )
            if not (math.isfinite(top) and math.isfinite(bottom) and math.isfinite(close)):
                # A name with no usable recent price is not a name to take a side in.
                continue
            if value > 0.0 and top > 0.0 and close < top * (1.0 - drop):
                continue
            if value < 0.0 and bottom > 0.0 and close * (1.0 - drop) > bottom:
                continue
            keep[name] = float(value)
        survivors = pd.Series(keep, dtype=float)
        longs = int((survivors > 0.0).sum())
        shorts = int((survivors < 0.0).sum())
        if longs < minimum_side or shorts < minimum_side:
            return None
        return survivors

    @staticmethod
    def _stand_aside(carry: pd.Series, pressure: pd.Series, trim: int) -> pd.Series:
        """Drop the ``trim`` names at each end of the *pressure* cross-section.

        This is the crowding guard in its cross-sectional form, and what it ranks on is the point.
        A name whose funding has just run away from its own trailing level is the one about to be
        unwound, whether that run is up or down; a name whose funding is merely high has been
        paying for weeks and is the position this book exists to hold.  Removing on pressure and
        holding on level is therefore not a filter on the signal, it is a different question asked
        of the same cross-section.
        """
        clean = carry.replace([np.inf, -np.inf], np.nan).dropna()
        basis = pressure.reindex(clean.index).replace([np.inf, -np.inf], np.nan).dropna()
        clean = clean.reindex(basis.index)
        if trim <= 0 or len(clean) <= 2 * trim + MINIMUM_BREADTH:
            return clean
        order = sorted(basis.index, key=lambda s: (float(basis[s]), str(s)))
        keep = order[trim : len(order) - trim]
        return clean.loc[keep]

    @staticmethod
    def _is_crowded(rates: pd.Series, guard: float) -> bool:
        """True when the latest rate is a tail event in the symbol's own funding history.

        A degenerate history -- a symbol pinned at a constant rate -- has no distribution to be
        extreme within, so it is treated as ordinary rather than as infinitely crowded.
        """
        window = rates.tail(GUARD_HISTORY)
        spread = float(window.std(ddof=1))
        if not math.isfinite(spread) or spread <= 0.0:
            return False
        z = (float(window.iloc[-1]) - float(window.mean())) / spread
        return math.isfinite(z) and abs(z) >= guard


def build_strategy() -> FundingCarryCrowdingGuarded:
    return FundingCarryCrowdingGuarded()
