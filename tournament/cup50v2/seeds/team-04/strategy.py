"""Regime-allocated ensemble: four plain sleeves, one causal allocation.

No single mechanism is all-weather. Trend earns while a move persists and bleeds in chop, carry
earns while positioning is calm and hands it back in the cascade, and a defensive book lags the
euphoria it insures against. Each sleeve here is kept deliberately plain so its behaviour stays
attributable, and the work goes into the allocation across them: a two-axis read of the equal-weight
member index -- which way it has been going, and whether it is wilder than its own normal -- selects
one row of a fixed allocation matrix. The matrix is a stated prior rather than a fit, and every
input to the state read closed strictly before the decision.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# Rows are (trend, xsmom, carry, defensive) and are read positionally against the sleeve tuple
# built in target_weights, so an allocation stays legible as one line per state.
#
# A stated prior about which mechanism survives which state, not a fit to a sample. Trend always
# carries weight because it is the effect with the longest record. The residual sleeve is switched
# off in falling markets, where cross-sectional dispersion turns into correlated liquidation and
# the "own strength" it ranks on stops being idiosyncratic. Carry is switched off in the wild half
# of a falling market -- that is exactly where the payer crowd unwinds and the carry collected for
# months is returned in days. The defensive sleeve is only paid for when volatility is above the
# index's own normal, because in the calm it is a drag with no crash to earn against.
_ALLOCATIONS = {
    ("up", "low"): (0.40, 0.40, 0.20, 0.00),
    ("up", "high"): (0.30, 0.30, 0.20, 0.20),
    ("down", "low"): (0.40, 0.00, 0.30, 0.30),
    ("down", "high"): (0.50, 0.00, 0.00, 0.50),
}
# Stated, not implicit: when the index is too young to read, the ensemble runs its calm-uptrend row.
_DEFAULT_STATE = ("up", "low")

_SLEEVE_BREADTH = 10
_SIGMA_DAYS = 30
_STATE_TREND_DAYS = 60
_STATE_MIN_DAYS = 90
_SYMBOL_CAP = 0.15


class RegimeAllocatedEnsemble:
    """Blend four sleeve signals with weights chosen by the market state, then size once."""

    trend_days = 63
    xs_days = 90
    carry_settlements = 21
    vol_median_days = 365

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(decay=0.20, band=0.05)

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        # A single name has no cross-section to z-score; unwind through the smoother rather than
        # snapping the book flat on a transient roster.
        if panel.empty or panel.shape[1] < 2:
            return self._smoother.update({}, context.eligible_symbols)
        sigma = toolkit.realised_sigma(panel, toolkit.bars_for_days(_SIGMA_DAYS))
        index_returns = toolkit.equal_weight_index(panel)
        allocation = _ALLOCATIONS[self._market_state(index_returns)]
        sleeves = (
            self._trend_sleeve(panel),
            self._xsmom_sleeve(panel, index_returns),
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

    def _trend_sleeve(self, panel: pd.DataFrame) -> pd.Series:
        """Cross-sectional strength over the medium horizon: the plainest form of the effect."""
        return toolkit.cross_sectional_z(
            toolkit.trailing_return(panel, toolkit.bars_for_days(self.trend_days))
        )

    def _xsmom_sleeve(self, panel: pd.DataFrame, index_returns: pd.Series) -> pd.Series:
        """Cross-sectional strength over a longer horizon than the trend sleeve.

        An earlier draft subtracted the equal-weight index return before the z-score. That is a
        constant common to every name, so it does not survive the cross-sectional standardisation:
        the line read as a residual and computed nothing. What genuinely separates this sleeve from
        the trend sleeve is its horizon, so that is all it claims. Making it a true residual would
        need a beta, and this lane spends its degrees of freedom on the allocation, not on a better
        momentum signal.
        """
        bars = toolkit.bars_for_days(self.xs_days)
        own = toolkit.trailing_return(panel, bars)
        if own.empty or len(index_returns) < bars:
            return pd.Series(dtype=float)
        return toolkit.cross_sectional_z(own)

    def _carry_sleeve(self, context: DecisionContextV2) -> pd.Series:
        """Short the payers of high funding, long the receivers.

        Funding is the only number in the interface that prices positioning directly, and the side
        paying it is the crowded one. A mean over several settlements rather than the last print,
        because a single settlement is as much a basis accident as a positioning signal.
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

    @staticmethod
    def _trim(signal: pd.Series) -> pd.Series:
        """Keep only the strongest names on each side of a sleeve.

        A raw z-score sleeve holds the entire cross-section, so even a sleeve with a small
        allocation touches every name and the book pays turnover for opinions it barely holds.
        Trimming each side separately rather than by magnitude alone keeps a sleeve two-sided when
        the cross-section is lopsided.
        """
        clean = signal.replace([np.inf, -np.inf], np.nan).dropna()
        if clean.empty:
            return clean
        longs = toolkit.top_by_absolute(clean[clean > 0.0], _SLEEVE_BREADTH)
        shorts = toolkit.top_by_absolute(clean[clean < 0.0], _SLEEVE_BREADTH)
        return clean.loc[list(longs.index) + list(shorts.index)]

    def _market_state(self, index_returns: pd.Series) -> tuple[str, str]:
        """Read direction and volatility state from closed bars of the equal-weight index.

        The volatility leg compares the index's recent realised dispersion with the median of that
        same rolling estimate, so the annualisation factor would cancel and is left out. The
        interface hands a strategy a bounded trailing window, so at the declared centre the median
        is taken over every rolling estimate available; declaring a shorter horizon is what makes
        the reference more reactive. Sufficiency is guarded at the shortest history that supports
        both legs -- guarding at the full median horizon would fire on every single decision and
        freeze the state read at its default, which is a regime map that never reads anything.
        """
        if len(index_returns) < toolkit.bars_for_days(_STATE_MIN_DAYS):
            return _DEFAULT_STATE
        recent = index_returns.tail(toolkit.bars_for_days(_STATE_TREND_DAYS))
        direction = "up" if float((1.0 + recent).prod()) >= 1.0 else "down"
        rolling = index_returns.rolling(toolkit.bars_for_days(_SIGMA_DAYS)).std(ddof=1).dropna()
        history = rolling.tail(toolkit.bars_for_days(self.vol_median_days))
        if history.empty:
            return direction, _DEFAULT_STATE[1]
        volatility = "high" if float(history.iloc[-1]) > float(history.median()) else "low"
        return direction, volatility


def build_strategy() -> RegimeAllocatedEnsemble:
    return RegimeAllocatedEnsemble()
