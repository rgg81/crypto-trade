"""Market-residual cross-sectional momentum with hysteresis and a crash guard.

Almost all of an alt's variance is market beta, so raw cross-sectional momentum is mostly a
leveraged bet on the index that works right up until the index turns.  This lane ranks names on
what is left once the beta-implied move is removed -- the part of the formation return that could
plausibly be about the name rather than about the market.  Membership is sticky: entering needs a
top-``top_k`` rank while leaving needs to fall out of a wider hold band, which cuts turnover
without changing the view.  After a deep index drawdown that has already begun to rebound the
short side is halved, because that rebound is where an unguarded residual book takes its worst
single loss.
"""

from __future__ import annotations

import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2, TargetStrategyV2

# The crash guard is a hazard control, not a view, so its trigger is fixed rather than tunable:
# a month-deep index drawdown that has turned up over the last ten days.
CRASH_WINDOW_DAYS = 30
REBOUND_WINDOW_DAYS = 10
CRASH_DRAWDOWN = -0.20
REBOUND_RETURN = 0.05
SHORT_HAIRCUT = 0.5


class ResidualCrossSectionalMomentum:
    """Long the strongest beta-adjusted formation returns, short the weakest."""

    form_days = 90
    skip_days = 3
    top_k = 10
    hold_k = 15

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(decay=0.25, band=0.05)
        self._longs: set[str] = set()
        self._shorts: set[str] = set()

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        form = toolkit.bars_for_days(self.form_days)
        skip = toolkit.bars_for_days(self.skip_days)
        panel = toolkit.close_panel(context)
        if panel.empty or panel.shape[1] < 4 or len(panel) <= form + skip:
            return self._stand_down(context)

        # The market factor is the eligible panel's own equal-weight book: no single name is
        # guaranteed to be a member, so the cross-section has to supply its own benchmark.
        benchmark = toolkit.equal_weight_index(panel)
        if benchmark.empty:
            return self._stand_down(context)
        # Compounding the benchmark on the panel's bar grid makes the market's own formation
        # return measured over exactly the window the symbols are measured over.
        level = (1.0 + benchmark.reindex(panel.index).fillna(0.0)).cumprod()
        market = toolkit.trailing_return(pd.DataFrame({"market": level}), form, skip=skip)
        beta = toolkit.beta_to(panel, benchmark, form)
        formation = toolkit.trailing_return(panel, form, skip=skip)
        if market.empty or beta.empty or formation.empty:
            return self._stand_down(context)

        residual = (formation - beta.reindex(formation.index) * float(market.iloc[0])).dropna()
        signals = self._membership(toolkit.cross_sectional_z(residual))
        if not signals:
            return self._stand_down(context)

        weights = toolkit.vol_parity(
            signals, toolkit.realised_sigma(panel), symbol_cap=0.15, neutral=True
        )
        if self._crash_risk(level):
            # Applied after sizing: halving the signal instead would be undone by the
            # side-by-side normalisation, which is exactly the de-risking we want to survive.
            weights = {
                symbol: value * SHORT_HAIRCUT if value < 0.0 else value
                for symbol, value in weights.items()
            }
        return self._smoother.update(weights, context.eligible_symbols)

    def _membership(self, signal: pd.Series) -> dict[str, float]:
        """Rank the cross-section and update the sticky long/short book."""
        ranked = [
            str(symbol)
            for symbol in sorted(signal.index, key=lambda name: (-float(signal[name]), str(name)))
        ]
        if len(ranked) < 4:
            self._longs.clear()
            self._shorts.clear()
            return {}
        entry = max(1, min(int(self.top_k), len(ranked) // 2))
        # The hold band is derived at call time so it stays wider than the entry rank even when the
        # neighbourhood perturbs top_k upward, and never so wide that the two bands overlap -- an
        # overlap would let one name be held long and short at once.
        hold = max(entry, min(max(int(self.hold_k), entry + 5), len(ranked) // 2))

        self._longs = set(ranked[:entry]) | (self._longs & set(ranked[:hold]))
        self._shorts = set(ranked[-entry:]) | (self._shorts & set(ranked[-hold:]))
        signals = {symbol: 1.0 for symbol in sorted(self._longs)}
        signals.update({symbol: -1.0 for symbol in sorted(self._shorts)})
        return signals

    def _crash_risk(self, level: pd.Series) -> bool:
        """True when the index is deep in a drawdown that has started to reverse.

        Every bar in ``level`` closed before the decision, so the trigger is causal.  This is the
        momentum crash: the beaten-down names rebound hardest, and the short side pays for it.
        """
        deep = toolkit.bars_for_days(CRASH_WINDOW_DAYS)
        bounce = toolkit.bars_for_days(REBOUND_WINDOW_DAYS)
        if len(level) <= deep:
            return False
        drawdown = float(level.iloc[-1] / level.iloc[-1 - deep] - 1.0)
        rebound = float(level.iloc[-1] / level.iloc[-1 - bounce] - 1.0)
        return drawdown <= CRASH_DRAWDOWN and rebound >= REBOUND_RETURN

    def _stand_down(self, context: DecisionContextV2) -> dict[str, float] | None:
        """No usable view: decay the book toward flat instead of holding a stale one."""
        self._longs.clear()
        self._shorts.clear()
        return self._smoother.update({}, context.eligible_symbols)


def build_strategy() -> TargetStrategyV2:
    return ResidualCrossSectionalMomentum()
