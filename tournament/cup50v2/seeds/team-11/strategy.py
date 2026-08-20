"""Lane seed: a ridge model that learns its cross-sectional combination inside the replay.

Every other lane fixes the rule that turns features into a book before the replay starts. This one
fixes only the feature list and the regulariser, and learns the combination from rows the streamed
context has already delivered: each decision stores a rank-transformed feature row, each row is
labelled ``horizon_days`` later by the cross-sectional rank of its realised risk-adjusted return,
and on the first decision of each calendar month the accumulated pairs are refit by ridge. There is
no pre-fitted artifact, so the lane is honestly flat over the opening stretch of a replay -- the
label horizon has to elapse, the row floor has to fill, and a month has to turn before any weight
exists -- and the score's activity term prices that silence rather than rewarding it.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# Fixed order, because the fitted coefficient vector is positional: a column reshuffle between the
# fit and the prediction would silently read the model wrong rather than fail.
FEATURES = (
    "mom21",
    "mom63",
    "rev5",
    "sigma30",
    "channel84",
    "flow10",
    "funding21",
    "attention",
    "drawdown",
    "beta",
)
MINIMUM_SECTION = 4


class WalkForwardRidge:
    """Ridge on cross-sectionally ranked features, refit monthly on accumulated observations."""

    ridge_lambda = 10.0
    horizon_days = 7
    top_k = 10

    # Not tunable: a floor below which a fit is noise, and a cap so a long replay cannot grow the
    # training set without bound.
    minimum_rows = 500
    memory_rows = 200_000

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(decay=0.20, band=0.05)
        self._pending: dict[pd.Timestamp, tuple[pd.DataFrame, pd.Series, pd.Series]] = {}
        self._rows: list[np.ndarray] = []
        self._labels: list[float] = []
        self._coefficients: np.ndarray | None = None
        self._fitted_month: tuple[int, int] | None = None

    def target_weights(
        self, context: DecisionContextV2, *, seed: int
    ) -> Mapping[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        if panel.empty:
            return None
        now = pd.Timestamp(context.decision_time)
        ranked, sigma = self._observe(context, panel)
        if ranked is not None:
            self._pending[now] = (ranked, panel.iloc[-1].reindex(ranked.index), sigma)
        self._realise(now, panel.iloc[-1])
        month = (now.year, now.month)
        if month != self._fitted_month:
            self._refit(month)
        if self._coefficients is None:
            # Honest silence: no artifact was carried in, so there is nothing to trade on yet.
            return {}
        if ranked is None:
            return None
        prediction = pd.Series(
            ranked.to_numpy(dtype=float) @ self._coefficients, index=ranked.index
        )
        signals = toolkit.long_short_extremes(prediction, int(self.top_k))
        raw = toolkit.vol_parity(signals, sigma, neutral=True, symbol_cap=0.15)
        return self._smoother.update(raw, context.eligible_symbols)

    def _observe(
        self, context: DecisionContextV2, panel: pd.DataFrame
    ) -> tuple[pd.DataFrame | None, pd.Series]:
        """The current rank-transformed feature row, or ``None`` when the section is unusable."""
        empty = pd.Series(dtype=float)
        # The longest feature that hard-fails on a short panel is mom63 (63 days plus a 3-day
        # skip); the rest degrade to whatever history exists. Waiting for the full 180-day
        # drawdown window instead would cost months of accumulation the lane cannot spare.
        if len(panel) < toolkit.bars_for_days(67):
            return None, empty
        highs = toolkit.column_panel(context, "high")
        lows = toolkit.column_panel(context, "low")
        quote = toolkit.column_panel(context, "quote_volume")
        taker = toolkit.column_panel(context, "taker_buy_quote_volume")
        last = panel.iloc[-1]

        channel_bars = toolkit.bars_for_days(84)
        span = highs.tail(channel_bars).max() - lows.tail(channel_bars).min()
        flow_bars = toolkit.bars_for_days(10)
        turnover = quote.tail(flow_bars).sum()
        share = quote.div(quote.sum(axis=1), axis=0)
        attention = (
            share.tail(toolkit.bars_for_days(14)).mean()
            / share.tail(toolkit.bars_for_days(90)).mean()
        ).replace([np.inf, -np.inf], np.nan)
        funding = toolkit.funding_by_symbol(context)
        sigma = toolkit.realised_sigma(panel, toolkit.bars_for_days(30))

        raw = pd.DataFrame(
            {
                "mom21": toolkit.trailing_return(panel, toolkit.bars_for_days(21)),
                "mom63": toolkit.trailing_return(
                    panel, toolkit.bars_for_days(63), skip=toolkit.bars_for_days(3)
                ),
                "rev5": toolkit.trailing_return(panel, toolkit.bars_for_days(5)),
                "sigma30": sigma,
                "channel84": (last - lows.tail(channel_bars).min()).div(span.where(span > 0.0)),
                "flow10": (2.0 * taker.tail(flow_bars).sum() - turnover).div(
                    turnover.where(turnover > 0.0)
                ),
                "funding21": pd.Series(
                    {
                        symbol: float(series.tail(21).mean())
                        for symbol, series in funding.items()
                        if len(series)
                    },
                    dtype=float,
                ),
                "attention": np.log(attention.where(attention > 0.0)),
                "drawdown": toolkit.drawdown_from_high(panel, toolkit.bars_for_days(180)),
                "beta": toolkit.beta_to(
                    panel, toolkit.equal_weight_index(panel), toolkit.bars_for_days(90)
                ),
            }
        )
        raw = raw.replace([np.inf, -np.inf], np.nan).dropna()
        raw = raw[raw["sigma30"] > 0.0]
        if len(raw) < MINIMUM_SECTION:
            return None, empty
        # Ranking column by column is the point of the lane: the model then fits the cross-section
        # rather than the market's volatility level, which is what inverts through a regime shift.
        ranked = pd.DataFrame(
            {name: toolkit.cross_sectional_rank(raw[name]) for name in FEATURES}, columns=FEATURES
        )
        return ranked, raw["sigma30"]

    def _realise(self, now: pd.Timestamp, last: pd.Series) -> None:
        """Move any stored row that has reached its horizon into the training set."""
        horizon = pd.Timedelta(days=max(1, int(self.horizon_days)))
        for stamp in sorted(self._pending):
            if now - stamp < horizon:
                continue
            ranked, entry, sigma = self._pending.pop(stamp)
            realised = ((last.reindex(ranked.index) / entry - 1.0) / sigma).replace(
                [np.inf, -np.inf], np.nan
            )
            # Ranking the label too keeps the target on the same bounded scale in every regime, so
            # a violent month cannot dominate the fit purely by having larger numbers in it.
            label = toolkit.cross_sectional_rank(realised.dropna())
            if len(label) < MINIMUM_SECTION:
                continue
            self._rows.extend(ranked.reindex(label.index).to_numpy(dtype=float))
            self._labels.extend(float(value) for value in label.to_numpy(dtype=float))
        excess = len(self._rows) - int(self.memory_rows)
        if excess > 0:
            del self._rows[:excess]
            del self._labels[:excess]

    def _refit(self, month: tuple[int, int]) -> None:
        """Closed-form ridge on everything accumulated so far; a pure function of the rows."""
        self._fitted_month = month
        if len(self._rows) < int(self.minimum_rows):
            return
        design = np.asarray(self._rows, dtype=float)
        labels = np.asarray(self._labels, dtype=float)
        gram = design.T @ design + float(self.ridge_lambda) * np.eye(design.shape[1])
        moment = design.T @ labels
        try:
            fitted = np.linalg.solve(gram, moment)
        except np.linalg.LinAlgError:
            fitted = np.linalg.lstsq(gram, moment, rcond=None)[0]
        if np.all(np.isfinite(fitted)):
            self._coefficients = fitted


def build_strategy() -> WalkForwardRidge:
    return WalkForwardRidge()
