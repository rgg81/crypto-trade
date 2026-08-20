"""Multi-horizon time-series trend.

Perpetual funding and cross-margin make a crypto move self-financing on the way up and
self-liquidating on the way down, and there is no closing auction to reset positioning overnight,
so a direction tends to persist for weeks rather than revert within a day. This seed reads that
persistence at three formation horizons at once and normalises each by the volatility of its own
holding period, so the book expresses agreement between horizons rather than whichever name moved
hardest. When no horizon agrees anywhere the book is deployed smaller instead of louder.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit


class MultiHorizonTrend:
    """Blend three trailing-return horizons into one signed trend score per symbol."""

    # The mechanism is a function of closes alone. Declaring it keeps the funding frame out of
    # every decision context; a variant that starts reading funding must flip this back to True.
    uses_funding = False

    h_fast_days = 21
    h_mid_days = 63
    h_slow_days = 126
    clip_limit = 2.0

    # Deliberately much shorter than the slowest horizon: the denominator should describe the risk
    # the book is about to carry, not the average risk over the whole formation window.
    sigma_bars = 90

    def __init__(self) -> None:
        # Held across decisions on purpose -- the no-trade band can only suppress a small move if
        # it remembers what was last emitted.
        self.smoother = toolkit.TargetSmoother(decay=0.25, band=0.05)

    def _horizon_scores(self, panel: pd.DataFrame, sigma_daily: pd.Series) -> pd.Series:
        """Mean of the clipped, horizon-normalised trailing returns, per symbol."""
        columns: dict[int, pd.Series] = {}
        # Keyed by bar count, so two horizon settings that round to the same window count once
        # rather than quietly double-weighting themselves.
        for days in (self.h_fast_days, self.h_mid_days, self.h_slow_days):
            bars = toolkit.bars_for_days(days)
            if bars < 1:
                continue
            returns = toolkit.trailing_return(panel, bars)
            if returns.empty:
                continue
            # Dividing by sigma * sqrt(h) asks the only question worth asking of a trailing return:
            # is it larger than what this symbol's own volatility could have produced by accident
            # over the same span? Without it the slow horizon and the wildest name both dominate.
            span = sigma_daily * math.sqrt(bars / toolkit.BARS_PER_DAY)
            scaled = returns.div(span).replace([np.inf, -np.inf], np.nan)
            columns[bars] = scaled.clip(-self.clip_limit, self.clip_limit)
        if not columns:
            return pd.Series(dtype=float)
        # skipna is the "enough history for" rule: a young symbol contributes the horizons it can
        # actually measure and is not punished for missing the slow one.
        return pd.DataFrame(columns).mean(axis=1, skipna=True).dropna()

    def target_weights(self, context, *, seed: int):
        # Once a day. Three decisions a day would pay the spread three times for a signal whose
        # shortest horizon is three weeks long.
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        if panel.empty:
            return {}
        sigma = toolkit.realised_sigma(panel, bars=self.sigma_bars)
        if sigma.empty:
            return {}
        scores = self._horizon_scores(panel, sigma / math.sqrt(365.0))
        if scores.empty:
            return {}

        # Conviction gate. The clipped score is roughly a t-statistic, so a cross-section with no
        # trend in it produces small |scores| everywhere; scaling the budget by their average keeps
        # a quiet tape from being renormalised back up into a full-size book of noise. It saturates
        # at 1.0 as soon as the average name carries half a sigma of trend.
        signals = {str(symbol): float(value) for symbol, value in scores.items()}
        strength = sum(abs(value) for value in signals.values())
        gross = min(1.0, strength / (0.5 * len(signals)))

        # neutral is off because the lane is time-series, not cross-sectional: when every horizon
        # points the same way the net tilt IS the signal, and balancing the sides would spend half
        # the book arguing with it.
        raw = toolkit.vol_parity(signals, sigma, gross=gross, symbol_cap=0.15, neutral=False)
        return self.smoother.update(raw, context.eligible_symbols)


def build_strategy() -> MultiHorizonTrend:
    return MultiHorizonTrend()
