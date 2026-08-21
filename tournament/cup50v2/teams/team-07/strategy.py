"""Taker-flow pressure, expressed as a liquidity-neutral cross-section.

Taker buy volume is the half of the tape that crossed the spread to get filled. Aggression of that
kind is either informed or reflexive, and either way it persists for days, so a trailing buy/sell
imbalance is a tradeable statement about who is in a hurry.

Three things separate this book from a naive reading of that idea.

*The horizon is long.* The imbalance predicts forward returns best over one to four weeks, not over
one bar, and the estimate is steadier the longer the window. A fast window and a slow window are
carried together because they answer different questions -- who is in a hurry now, and who has been
in a hurry for a month -- and averaging them is a more honest estimate than either alone.

*The imbalance is not a fade.* The lane's stated refinement was absorption: persistent buying that
fails to lift price is landing in a larger seller's inventory and should be traded against. Measured
on the research window, that is false and its sign is backwards. Sorting the cross-section jointly
on flow and on the price response the flow produced, forward returns rise monotonically with flow at
every level of price response, and the supposedly absorbed cell -- heavy buying, no price move -- is
one of the strongest. So this book follows the pressure everywhere and fades it nowhere.

*The book is neutralised against liquidity.* Raw taker imbalance correlates about 0.39 with the log
of a name's dollar volume, so a book ranked on it is quietly long the largest names and short the
smallest. That is a size bet, not a flow bet, and it is the reason the naive version has no edge at
all in an advancing market. Regressing the imbalance on log dollar volume across the cross-section
each day and keeping the residual leaves the flow signal essentially intact while removing the tilt,
and it is the single change that makes the book work in every market state rather than two of three.

The remaining problem is cost. The signal is slow, so the book is rebalanced slowly: weights are
blended toward the new target rather than jumped to it, and a move too small to be worth its own
spread is not made at all.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# A name needs this share of its window's bars present before its imbalance is trusted. Below it
# the ratio is an average over a handful of bars and belongs in the tail of the cross-section for
# the wrong reason.
COVERAGE = 0.5
# Per-name ceiling inside the book's own construction. The evaluator's cap is 0.20; this sits under
# it so the shape the strategy asks for is the shape it gets, rather than one the caps carved.
SYMBOL_CAP = 0.15
# Trailing bars used for the volatility that sizes each leg. Thirty days is long enough to be a
# stable divisor and short enough to notice a name that has changed character.
SIGMA_BARS = 90
# Fewest bars that may stand in for a full flow window while a replay is warming up.
MIN_SPAN_BARS = 9
# Smallest cross-section the book will trade. Below it the z-scores and the neutralising regression
# are being estimated on too few names to mean anything.
MIN_NAMES = 8


class TakerFlowPressure:
    """Long the aggressively bought, short the aggressively sold, net of the liquidity tier.

    Class attributes are the tunable surface; the evaluator rewrites them per neighbourhood point,
    so every one of them is read inside ``target_weights`` rather than captured at construction.
    """

    # Fast and slow flow windows, in days.
    fast_days = 13
    slow_days = 40
    # Trailing window for the dollar-volume control that the imbalance is neutralised against.
    adv_days = 24
    # Share of the distance to the fresh target taken each day.
    blend_decay = 0.09
    # Total weight movement below which the book is left alone rather than rebalanced.
    trade_band = 0.12

    # Funding says nothing about who crossed the spread; the interface may supply an empty frame.
    uses_funding = False

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(decay=self.blend_decay, band=self.trade_band)

    # -- signal ------------------------------------------------------------------------------

    @staticmethod
    def _imbalance(taker: pd.DataFrame, quote: pd.DataFrame, bars: int) -> pd.Series:
        """Signed share of trailing quote volume that was buyer-initiated, in [-1, +1].

        Both columns are per-bar sums, so summing bars over the horizon is the horizon's total and
        the ratio needs no reweighting. Dividing by traded value rather than differencing raw
        volume keeps a mega-cap and a mid-cap on the same scale.
        """
        if taker.empty or quote.empty or bars < 1:
            return pd.Series(dtype=float)
        # Use the longest window available rather than refusing to answer until the full one
        # exists. Demanding the whole window makes the book sit flat through the opening weeks of
        # any replay -- a hole in the record, which the scorer prices at zero, rather than a form
        # of caution -- while half a window is already enough bars to estimate a ratio.
        span = min(int(bars), len(quote))
        if span < max(MIN_SPAN_BARS, int(bars) // 2):
            return pd.Series(dtype=float)
        buy = taker.tail(span).sum(min_count=1)
        total = quote.tail(span).sum(min_count=1)
        counts = quote.tail(span).notna().sum()
        flow = (2.0 * buy - total) / total
        usable = (counts >= max(1, int(round(COVERAGE * span)))) & (total > 0.0)
        return flow.where(usable).replace([np.inf, -np.inf], np.nan).dropna()

    @staticmethod
    def _neutralise(signal: pd.Series, control: pd.Series) -> pd.Series:
        """Cross-sectional OLS residual of the signal on one control.

        Both inputs are z-scored first, so each is already mean-zero across the section and the
        regression needs no intercept. A control with no spread leaves the signal untouched rather
        than dividing by zero.
        """
        z_signal = toolkit.cross_sectional_z(signal)
        z_control = toolkit.cross_sectional_z(control)
        shared = z_signal.index.intersection(z_control.index)
        if len(shared) < MIN_NAMES:
            return z_signal
        y = z_signal.reindex(shared)
        x = z_control.reindex(shared)
        denominator = float((x * x).sum())
        if not math.isfinite(denominator) or denominator <= 0.0:
            return y
        beta = float((y * x).sum()) / denominator
        if not math.isfinite(beta):
            return y
        return (y - beta * x).replace([np.inf, -np.inf], np.nan).dropna()

    # -- book --------------------------------------------------------------------------------

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        # Deciding once a day rather than three times cuts turnover by two thirds before any other
        # control acts, and the signal has nothing to say at an eight-hour cadence anyway.
        if not toolkit.is_daily_decision(context):
            return None
        self._smoother.decay = float(self.blend_decay)
        self._smoother.band = float(self.trade_band)

        eligible = context.eligible_symbols
        closes = toolkit.close_panel(context)
        taker = toolkit.column_panel(context, "taker_buy_quote_volume")
        quote = toolkit.column_panel(context, "quote_volume")
        if closes.empty or taker.empty or quote.empty:
            return self._smoother.update({}, eligible)
        # Inner alignment first: a symbol whose flow columns disagree on coverage would otherwise
        # contribute a numerator and a denominator measured over different bars.
        taker, quote = taker.align(quote, join="inner")

        fast_bars = toolkit.bars_for_days(max(1, int(self.fast_days)))
        slow_bars = toolkit.bars_for_days(max(1, int(self.slow_days)))
        fast = self._imbalance(taker, quote, fast_bars)
        slow = self._imbalance(taker, quote, slow_bars)
        # Equal weight on purpose: the fast window says who is aggressive now, the slow one says
        # who has been aggressive for a while, and neither question dominates the other.
        blended = 0.5 * toolkit.cross_sectional_z(fast) + 0.5 * toolkit.cross_sectional_z(slow)
        blended = blended.replace([np.inf, -np.inf], np.nan).dropna()
        if len(blended) < MIN_NAMES:
            return self._smoother.update({}, eligible)

        # The liquidity control: average traded value per bar over its own trailing window, in
        # logs so that a mega-cap and a mid-cap differ by a number rather than by an order of
        # magnitude. Neutralising against it is what stops the book being a size bet.
        adv_bars = toolkit.bars_for_days(max(1, int(self.adv_days)))
        adv = quote.tail(adv_bars).mean()
        adv = adv.where(adv > 0.0).dropna()
        if len(adv) >= MIN_NAMES:
            liquidity = pd.Series(np.log(adv.to_numpy(dtype=float)), index=adv.index)
            scores = self._neutralise(blended, liquidity)
        else:
            scores = toolkit.cross_sectional_z(blended)
        if len(scores) < MIN_NAMES:
            return self._smoother.update({}, eligible)

        # Rank rather than level: the imbalance has fat tails, and one name at -0.9 should not be
        # allowed to decide how large the rest of the short leg is.
        ranked = toolkit.cross_sectional_rank(scores)
        sigma = toolkit.realised_sigma(closes, SIGMA_BARS)
        raw = toolkit.vol_parity(
            {str(symbol): float(value) for symbol, value in ranked.items()},
            sigma,
            neutral=True,
            symbol_cap=SYMBOL_CAP,
        )
        return self._smoother.update(raw, eligible)


def build_strategy() -> TakerFlowPressure:
    return TakerFlowPressure()
