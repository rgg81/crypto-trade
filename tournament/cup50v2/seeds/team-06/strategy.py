"""Defensive quality, with the market factor removed.

In crypto the low-volatility anomaly runs backwards during euphoria: the most fragile, thinnest,
most retail-fragmented names melt up hardest and then hand it all back. This book scores every
eligible name on four defensive traits -- calm, not crash-prone, deeply traded, steadily traded --
goes long the most resilient and short the most fragile, and then explicitly subtracts the market
factor from the resulting weights. What is left should earn in bear and chop and lose in a melt-up,
which is a regime exposure rather than a defect; without the beta step it would simply be a
short-beta bet wearing a factor name.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# Beta is measured over a longer window than quality: the loading on the market is a slow property
# and a short estimate of it is mostly noise, which would inject turnover through the correction.
BETA_WINDOW_DAYS = 90
# Below this gross-share-weighted beta the cross-section carries no market factor worth removing,
# and the correction that would remove it is a division by almost nothing.
MINIMUM_CARRIER_BETA = 0.05
_DUST = 1e-4


class DefensiveQualityNeutral:
    """Long resilience, short fragility, beta-neutralised."""

    window_days = 60
    top_k = 15

    def __init__(self) -> None:
        # Quality is a slow trait, so the book should be slow too: heavy blending plus a no-trade
        # band stops it paying the spread to re-rank names whose scores barely moved.
        self._smoother = toolkit.TargetSmoother(decay=0.15, band=0.05)

    def target_weights(self, context: DecisionContextV2, *, seed: int) -> dict[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        top_k = max(1, int(self.top_k))
        bars = max(9, toolkit.bars_for_days(max(1.0, float(self.window_days))))
        panel = toolkit.close_panel(context)
        # Both legs must exist or the book is a directional bet, not a quality spread.
        if panel.empty or panel.shape[1] < 2 * top_k:
            return self._smoother.update({}, context.eligible_symbols)
        quality, sigma = self._quality(context, panel, bars)
        signals = toolkit.long_short_extremes(quality, top_k)
        weights = toolkit.vol_parity(signals, sigma, symbol_cap=0.15)
        neutral = self._neutralise(panel, weights)
        return self._smoother.update(neutral, context.eligible_symbols)

    def _quality(
        self, context: DecisionContextV2, panel: pd.DataFrame, bars: int
    ) -> tuple[pd.Series, pd.Series]:
        """Composite defensive score, plus the sigma the sizer needs anyway."""
        sigma = toolkit.realised_sigma(panel, bars)
        downside = toolkit.downside_sigma(panel, bars)
        volume = toolkit.column_panel(context, "quote_volume").tail(bars)
        if sigma.empty or volume.empty:
            return pd.Series(dtype=float), sigma

        # Aggregate turnover to calendar days before taking logs: an 8h bar's volume is dominated
        # by which session it covers, and that intraday shape would otherwise masquerade as
        # instability. Median of the logs is the log of the median -- a level robust to the one
        # listing-day or liquidation-day print that a mean would follow.
        daily = volume.groupby(volume.index.floor("1D")).sum(min_count=1)
        logs = np.log(daily.where(daily > 0.0))
        days = logs.notna().sum()
        depth = logs.median().where(days >= 5).dropna()
        steadiness = logs.std(ddof=1).where(days >= 5).dropna()

        common = sigma.index
        for component in (downside, depth, steadiness):
            common = common.intersection(component.index)
        if len(common) < 2:
            return pd.Series(dtype=float), sigma
        # Every term is z-scored on the same surviving cross-section, so a name missing any one
        # component cannot tilt the mean or spread of the other three.
        quality = (
            -toolkit.cross_sectional_z(sigma.reindex(common))
            - toolkit.cross_sectional_z(downside.reindex(common))
            + toolkit.cross_sectional_z(depth.reindex(common))
            - toolkit.cross_sectional_z(steadiness.reindex(common))
        )
        return quality.replace([np.inf, -np.inf], np.nan).dropna(), sigma

    def _neutralise(self, panel: pd.DataFrame, weights: dict[str, float]) -> dict[str, float]:
        """Subtract a market-proportional adjustment until the book's net beta is about zero."""
        if not weights:
            return {}
        beta = toolkit.beta_to(
            panel, toolkit.equal_weight_index(panel), toolkit.bars_for_days(BETA_WINDOW_DAYS)
        )
        known = {}
        for symbol, weight in weights.items():
            loading = float(beta.get(symbol, float("nan")))
            if math.isfinite(loading):
                known[symbol] = loading
        gross = sum(abs(weights[symbol]) for symbol in known)
        if gross <= 0.0:
            return dict(weights)
        shares = {symbol: abs(weights[symbol]) / gross for symbol in known}
        net_beta = sum(weights[symbol] * known[symbol] for symbol in known)
        # The correction is spread in proportion to |weight|, so removing beta costs each name in
        # proportion to the risk it already carries; this is how much beta that spread removes.
        carrier = sum(shares[symbol] * known[symbol] for symbol in known)
        if not math.isfinite(net_beta) or not math.isfinite(carrier):
            return dict(weights)
        if carrier < MINIMUM_CARRIER_BETA:
            return dict(weights)
        # Solve for the adjustment rather than assuming the book's average beta is exactly 1.0;
        # the sign opposes net_beta by construction, and the clip stops a pathological estimate
        # from turning a spread into a one-sided book.
        adjustment = max(-1.0, min(1.0, net_beta / carrier))
        neutral = dict(weights)
        for symbol, share in shares.items():
            neutral[symbol] = weights[symbol] - adjustment * share
        neutral = {symbol: value for symbol, value in neutral.items() if abs(value) >= _DUST}
        total = sum(abs(value) for value in neutral.values())
        # vol_parity's per-side cap logic cannot be reused once the sides are no longer symmetric;
        # the only budget that still has to hold is the gross one.
        if total > 1.0:
            neutral = {symbol: value / total for symbol, value in neutral.items()}
        return neutral


def build_strategy() -> DefensiveQualityNeutral:
    return DefensiveQualityNeutral()
