"""Regime-allocated ensemble: three sleeves with near-orthogonal regime profiles, one causal read.

The lane's claim is that the allocation is the strategy. This candidate keeps that claim and makes
it carry more weight than the seed did, in three places.

*The sleeves are chosen to disagree.* Measured one at a time over the research window, the three
sleeves here have almost disjoint regime profiles: cross-sectional momentum earns in chop and is
close to worthless in both directional states; carry -- shorting the payers of high funding -- is
the only one of the three that earns in a rising market and it is destroyed in a falling one; the
defensive sleeve, long the calm and short the wild, owns falling and sideways markets and is the
single worst book to hold in a rising one. A sleeve set whose members all earn in the same state
would make the allocation decorative, and that is the failure this lane is exposed to.

*Momentum is a state-conditional holding, not a permanent one.* The seed carried two
cross-sectional momentum sleeves that differed only in horizon, switched one of them off in falling
markets on the stated ground that "own strength" stops being idiosyncratic when dispersion turns
into correlated liquidation, and left the other one on at the largest weight in every row. That is
the same argument applied to one sleeve and not to its near-duplicate. This candidate keeps one
momentum sleeve and applies the rule to it: no momentum at all while the index is falling.

*The state read is deliberately sticky.* Its direction leg is the growth of an equal-weight index
of the eligible names over a slow window, and it only changes side when that growth leaves a dead
band around zero; inside the band the previous side is held. A regime map that flips on a
knife-edge is not reading a regime, it is reading noise, and it pays the spread to do it.

Everything the state read consumes closed strictly before the decision. There is no fitted object
and no state that is not a function of the streamed past: the only carried values are the previous
state labels and the previous emitted book, both of which are reconstructed by replaying the
window from its start.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# Rows are (momentum, carry, defensive), read positionally against the sleeve tuple built in
# target_weights. Each row is a stated prior with a reason, and only the proportions matter: the
# blended book is normalised once by the sizer, so a row is a mix, not a level of risk.
#
#   up / low    Momentum leads. The index is rising steadily, dispersion is directional, and the
#               names that have been strong are the ones a calm uptrend keeps rewarding. Carry is
#               held alongside it because funding is a cash flow rather than a directional bet.
#   up / high   Same two sleeves, tilted toward carry. A violent up-leg is exactly where perpetual
#               funding reaches its extremes and where the long crowd is most obviously paying to
#               be there, so carry's expected return is highest precisely when the up-move is
#               wildest. No defensive weight: long-calm/short-wild is short the high-beta names
#               that lead a rising market, and it is the reason the seed's bull score was its
#               worst by a wide margin.
#   down / low  No momentum, for the seed's own reason applied consistently. The book becomes an
#               even split of the two sleeves that do not need the market to rise: carry, while
#               positioning is still orderly, and the defensive sleeve.
#   down / high Positioning is not orderly any more. This is the cascade: the payers of funding
#               are the ones being liquidated, so carry is cut to a third and the defensive sleeve
#               takes the rest. Carry is not cut to zero, because a row that holds one sleeve is a
#               book with no ensemble left in it, and the wild-downtrend row is the one this
#               strategy will be judged on when it is judged at its worst.
_ALLOCATIONS = {
    ("up", "low"): (0.65, 0.35, 0.00),
    ("up", "high"): (0.60, 0.40, 0.00),
    ("down", "low"): (0.00, 0.50, 0.50),
    ("down", "high"): (0.00, 0.33, 0.67),
}
# Stated rather than implicit: before there is enough index history to read a state at all, the
# ensemble runs its calm-uptrend row. It is the row with the least insurance in it, which is the
# honest default for "I do not know yet" only because the alternative -- defaulting to the crisis
# row -- would make a cold start a bet that the window opens in a crash.
_DEFAULT_STATE = ("up", "low")

# The shortest index history that supports both legs of the state read. Guarding at the full
# volatility-reference horizon instead would hold the state at its default on every decision,
# which is a regime map that never reads anything.
_STATE_MIN_DAYS = 90
# Per-name ceiling, applied with redistribution of the freed budget. Deliberately tighter than the
# evaluator's own 0.20 so the binding cap is the strategy's, not the organizer's.
_SYMBOL_CAP = 0.15
# Blending weight and no-trade band on the emitted book. Both are turnover controls and both are
# declared in risk-declaration.json.
_SMOOTHER_DECAY = 0.20
_SMOOTHER_BAND = 0.05


class RegimeAllocatedEnsemble:
    """Blend three sleeve signals with weights chosen by the market state, then size once."""

    # Horizon of the cross-sectional momentum sleeve, in days.
    momentum_days = 90
    # Number of funding settlements averaged by the carry sleeve. A single print is as much a
    # basis accident as a positioning signal; a long mean is a claim about a standing crowd.
    carry_settlements = 42
    # Window of the realised-volatility estimate used for sizing, for the defensive sleeve and for
    # the volatility leg of the state read.
    sigma_days = 30
    # Window of the index growth that sets the direction leg.
    state_trend_days = 60
    # Dead band around zero growth. Inside it the previous direction is held.
    state_band = 0.05
    # Names kept per side per sleeve before blending.
    sleeve_breadth = 10

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(decay=_SMOOTHER_DECAY, band=_SMOOTHER_BAND)
        self._direction = _DEFAULT_STATE[0]
        self._volatility = _DEFAULT_STATE[1]

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        # A single name has no cross-section to score. Unwind through the smoother rather than
        # snapping the book flat on a transient roster.
        if panel.empty or panel.shape[1] < 2:
            return self._smoother.update({}, context.eligible_symbols)
        sigma = toolkit.realised_sigma(panel, toolkit.bars_for_days(self.sigma_days))
        index_returns = toolkit.equal_weight_index(panel)
        allocation = _ALLOCATIONS[self._market_state(index_returns)]
        sleeves = (
            self._momentum_sleeve(panel),
            self._carry_sleeve(context),
            self._defensive_sleeve(sigma),
        )
        combined = pd.Series(0.0, index=panel.columns, dtype=float)
        for weight, sleeve in zip(allocation, sleeves, strict=True):
            if weight <= 0.0 or sleeve.empty:
                continue
            combined = combined.add(
                self._trim(sleeve).reindex(combined.index).fillna(0.0).mul(weight)
            )
        combined = combined[combined.abs() > 0.0]
        # The blended book is sized once. Sizing each sleeve separately and adding the weights
        # would let the noisiest sleeve set the book's risk regardless of its allocation.
        raw = toolkit.vol_parity(combined.to_dict(), sigma, symbol_cap=_SYMBOL_CAP, neutral=True)
        return self._smoother.update(raw, context.eligible_symbols)

    def _momentum_sleeve(self, panel: pd.DataFrame) -> pd.Series:
        """Cross-sectional strength over a quarter: the plainest form of the effect.

        Scored as a z rather than a rank on purpose. The rank version was measured and is worse
        here, and the reason is legible: in a rising market the payoff is concentrated in the few
        names that ran furthest, and a rank throws exactly that information away.
        """
        return toolkit.cross_sectional_z(
            toolkit.trailing_return(panel, toolkit.bars_for_days(self.momentum_days))
        )

    def _carry_sleeve(self, context: DecisionContextV2) -> pd.Series:
        """Short the payers of high funding, long the receivers.

        Funding is the only number in the interface that prices positioning directly, and the side
        paying it is the crowded one.
        """
        count = max(1, int(self.carry_settlements))
        minimum = max(1, count // 2)
        means: dict[str, float] = {}
        for symbol, series in toolkit.funding_by_symbol(context).items():
            window = series.tail(count)
            if len(window) >= minimum:
                means[symbol] = float(window.mean())
        if not means:
            return pd.Series(dtype=float)
        return toolkit.cross_sectional_z(-pd.Series(means))

    def _defensive_sleeve(self, sigma: pd.Series) -> pd.Series:
        """Long the calm, short the wild: the sleeve that is meant to earn while the others hurt."""
        if sigma.empty:
            return pd.Series(dtype=float)
        return -toolkit.cross_sectional_z(sigma)

    def _trim(self, signal: pd.Series) -> pd.Series:
        """Keep only the strongest names on each side of a sleeve.

        A raw z-score sleeve holds the entire cross-section, so even a sleeve with a small
        allocation touches every name and the book pays turnover for opinions it barely holds.
        Trimming each side separately rather than by magnitude alone keeps a sleeve two-sided when
        the cross-section is lopsided.
        """
        clean = signal.replace([np.inf, -np.inf], np.nan).dropna()
        if clean.empty:
            return clean
        count = max(1, int(self.sleeve_breadth))
        longs = toolkit.top_by_absolute(clean[clean > 0.0], count)
        shorts = toolkit.top_by_absolute(clean[clean < 0.0], count)
        return clean.loc[list(longs.index) + list(shorts.index)]

    def _market_state(self, index_returns: pd.Series) -> tuple[str, str]:
        """Read direction and volatility state from closed bars of the equal-weight index.

        The direction leg is hysteretic: it flips only when index growth over the trailing window
        leaves a dead band around zero, and holds the previous side inside it. Without the band the
        seed's read changed side on a sign test at exactly zero, which near a flat market means the
        whole allocation matrix can flip on a rounding error and flip back the next day.

        The volatility leg compares the index's recent realised dispersion with the median of that
        same rolling estimate over the whole trailing window the interface supplies, so the
        annualisation factor would cancel and is left out. Using the whole window rather than a
        declared horizon is deliberate: a shorter reference is more reactive, was measured, and was
        worse, and a longer one is unreachable because the context is bounded at a year.
        """
        if len(index_returns) < toolkit.bars_for_days(_STATE_MIN_DAYS):
            return _DEFAULT_STATE
        recent = index_returns.tail(toolkit.bars_for_days(self.state_trend_days))
        growth = float((1.0 + recent).prod()) - 1.0
        band = abs(float(self.state_band))
        if growth >= band:
            self._direction = "up"
        elif growth <= -band:
            self._direction = "down"
        rolling = index_returns.rolling(toolkit.bars_for_days(self.sigma_days)).std(ddof=1).dropna()
        if not rolling.empty:
            last = float(rolling.iloc[-1])
            reference = float(rolling.median())
            self._volatility = "high" if last > reference else "low"
        return self._direction, self._volatility


def build_strategy() -> RegimeAllocatedEnsemble:
    return RegimeAllocatedEnsemble()
