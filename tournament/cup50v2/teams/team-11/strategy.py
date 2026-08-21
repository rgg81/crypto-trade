"""State-matched walk-forward ridge for the CUP-50 v2 learned-model lane.

The lane asks whether a model refit inside the replay adapts across regimes better than a fixed
rule. The seed answers no, and says why: a fit on an expanding window of realised cross-sections is
estimated on the state the market was in and deployed into the state it moved to, so it is
permanently one regime behind. Fitting *faster* turns that lag into a whipsaw.

This candidate changes what "refit" means. Two things are learned from the streamed past and
nothing else is:

1. **Which of its own past resembles today.** Every stored observation carries the market state that
   was observable when it was made -- trailing index return, index volatility, cross-sectional
   dispersion. At each refit the rows are weighted by a Gaussian kernel in that state space centred
   on *today's* state, so the coefficients are estimated from the parts of the record that look like
   now rather than from the parts that happened most recently. The state is observable at decision
   time; the regime label is not, and is never used.

2. **The combination itself**, by ridge, with a shrinkage that is a fraction of the accumulated row
   count rather than an absolute constant. The seed's ``ridge_lambda`` of 10 against roughly 10^5
   rows is numerically zero, so its declared regularisation axis could not move anything; here the
   same name means what it says, and at the declared centre the fit sits close to the diagonal
   solution that collinear ranked features can actually support.

What the book is *not* allowed to learn is a view on the market's direction. The combined prediction
is residualised cross-sectionally against the beta, index-correlation and volatility ranks before a
single weight is formed. In this field the direction exposure is the whole inversion: the features
that pay in a rising market are close to the negatives of the ones that pay in a falling market, and
a cross-sectional book that carries a net beta is a market call wearing a factor's clothes.

Nothing is fitted outside the replay: there is no artifact, no cache and no training set. The book
is honestly flat over the opening stretch while the label horizon elapses and the row floor fills.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2 import toolkit
from crypto_trade.cup50v2.protocol import DecisionContextV2

# Fixed order: the fitted coefficient vector is positional, so a column reshuffle between the fit
# and the prediction would read the model wrong rather than fail.
FEATURES = (
    "mom63",
    "mom126",
    "mom252",
    "rev5",
    "rev10",
    "sigma90",
    "volratio",
    "channel84",
    "flow10",
    "funding21",
    "attention",
    "attention7",
    "drawdown",
    "beta",
    "size",
    "vol_trend",
    "skew60",
    "amihud",
    "corr",
    "trade_size",
)
NEUTRALISE_ON = ("beta", "corr", "sigma30")
MINIMUM_SECTION = 8
STATE_DIMENSIONS = 3


class StateMatchedRidge:
    """Ridge on ranked features, refit on the parts of the past that resemble the present."""

    # --- declared dimensions -------------------------------------------------------------
    ridge_lambda = 3.0        # shrinkage per accumulated row; scale-free, so it means something
    horizon_days = 7          # base label horizon; the ensemble also fits 2x and 4x this
    breadth = 8               # names per side
    state_bandwidth = 0.64    # kernel width in standardised state units
    refit_days = 14           # days between refits

    # --- fixed by design, not tunable ---------------------------------------------------
    minimum_rows = 250        # below this a fit is noise
    memory_rows = 250_000     # a long replay cannot grow the training set without bound
    symbol_cap = 0.15         # tighter than the organizer's 0.20
    blend_decay = 0.20        # exponential blending toward the fresh target
    trade_band = 0.05         # hold rather than pay for a move smaller than this
    warmup_days = 25.0        # panel length before any feature row exists
    minimum_coverage = 0.5    # fraction of features a name must have to stay in the section

    def __init__(self) -> None:
        self._smoother = toolkit.TargetSmoother(decay=self.blend_decay, band=self.trade_band)
        self._observations: dict[pd.Timestamp, tuple] = {}
        self._rows: dict[int, list[np.ndarray]] = {}
        self._labels: dict[int, list[float]] = {}
        self._states: dict[int, list[np.ndarray]] = {}
        self._coefficients: dict[int, np.ndarray] = {}
        self._last_fit: pd.Timestamp | None = None

    # ------------------------------------------------------------------ helpers
    def _horizons(self) -> tuple[int, ...]:
        base = max(1, int(self.horizon_days))
        return (base, 2 * base, 4 * base)

    def _section(self, context, panel):
        """Ranked feature matrix, sigma, the neutralisation controls and today's state."""
        empty = pd.Series(dtype=float)
        d = toolkit.bars_for_days
        if len(panel) < d(float(self.warmup_days)):
            return None, empty, None, None
        highs = toolkit.column_panel(context, "high")
        lows = toolkit.column_panel(context, "low")
        quote = toolkit.column_panel(context, "quote_volume")
        taker = toolkit.column_panel(context, "taker_buy_quote_volume")
        trades = toolkit.column_panel(context, "trade_count")
        last = panel.iloc[-1]
        length = len(panel)

        channel = min(d(84), length)
        span = highs.tail(channel).max() - lows.tail(channel).min()
        flow = d(10)
        turnover = quote.tail(flow).sum()
        share = quote.div(quote.sum(axis=1), axis=0)
        attention = (share.tail(d(14)).mean() / share.tail(min(d(90), length)).mean()).replace(
            [np.inf, -np.inf], np.nan
        )
        attention7 = (share.tail(d(7)).mean() / share.tail(min(d(60), length)).mean()).replace(
            [np.inf, -np.inf], np.nan
        )
        funding = toolkit.funding_by_symbol(context)
        sigma = toolkit.realised_sigma(panel, min(d(30), length))
        sigma90 = toolkit.realised_sigma(panel, min(d(90), length))
        sigma10 = toolkit.realised_sigma(panel, min(d(10), length))
        returns = toolkit.bar_returns(panel)
        index = returns.mean(axis=1, skipna=True)
        beta, correlation = _beta_and_correlation(returns, index, min(d(90), length))
        logs = np.log(panel).diff()
        size = np.log(turnover.where(turnover > 0.0))
        volume_trend = np.log(
            (quote.tail(d(10)).mean() / quote.tail(min(d(60), length)).mean()).replace(
                [np.inf, -np.inf], np.nan
            )
        )
        amihud = (
            returns.tail(min(d(30), length)).abs() / quote.tail(min(d(30), length)).replace(0.0, np.nan)
        ).mean()
        if len(trades):
            average_trade = (
                quote.tail(flow).sum() / trades.tail(flow).sum().replace(0.0, np.nan)
            )
        else:
            average_trade = pd.Series(dtype=float)

        raw = pd.DataFrame(
            {
                "mom63": toolkit.trailing_return(panel, d(63), skip=d(3)),
                "mom126": toolkit.trailing_return(panel, d(126), skip=d(3)),
                "mom252": toolkit.trailing_return(panel, d(252), skip=d(3)),
                "rev5": toolkit.trailing_return(panel, d(5)),
                "rev10": toolkit.trailing_return(panel, d(10)),
                "sigma90": sigma90,
                "volratio": (sigma10 / sigma90).replace([np.inf, -np.inf], np.nan),
                "channel84": (last - lows.tail(channel).min()).div(span.where(span > 0.0)),
                "flow10": (2.0 * taker.tail(flow).sum() - turnover).div(
                    turnover.where(turnover > 0.0)
                ),
                "funding21": pd.Series(
                    {
                        symbol: float(series.tail(63).mean())
                        for symbol, series in funding.items()
                        if len(series)
                    },
                    dtype=float,
                ),
                "attention": np.log(attention.where(attention > 0.0)),
                "attention7": np.log(attention7.where(attention7 > 0.0)),
                "drawdown": toolkit.drawdown_from_high(panel, min(d(180), length)),
                "beta": beta,
                "size": size,
                "vol_trend": volume_trend,
                "skew60": logs.tail(min(d(60), length)).skew(),
                "amihud": np.log(amihud.where(amihud > 0.0)),
                "corr": correlation,
                "trade_size": (
                    np.log(average_trade.where(average_trade > 0.0))
                    if len(average_trade)
                    else pd.Series(dtype=float)
                ),
                "sigma30": sigma,
            }
        ).replace([np.inf, -np.inf], np.nan)

        raw = raw[raw["sigma30"].notna() & (raw["sigma30"] > 0.0)]
        if raw.empty:
            return None, empty, None, None
        # A name keeps its place when most of its features exist. Dropping the whole cross-section
        # because one long-lookback column is not ready yet costs months of a replay: the seed's
        # 252-day column would silence the book until the fourth quarter of the first year.
        coverage = raw[list(FEATURES)].notna().sum(axis=1)
        needed = max(1, int(round(float(self.minimum_coverage) * len(FEATURES))))
        raw = raw[coverage >= needed]
        if len(raw) < MINIMUM_SECTION:
            return None, empty, None, None
        # Ranking column by column is the point of the lane: the model then fits the cross-section
        # rather than the market's volatility level. A name missing a column takes the neutral rank
        # rather than a guess.
        ranked = pd.DataFrame(
            {
                name: toolkit.cross_sectional_rank(raw[name].dropna())
                .reindex(raw.index)
                .fillna(0.0)
                for name in FEATURES
            },
            columns=list(FEATURES),
            index=raw.index,
        )
        controls = pd.DataFrame(
            {
                name: toolkit.cross_sectional_rank(raw[name].dropna())
                .reindex(raw.index)
                .fillna(0.0)
                for name in NEUTRALISE_ON
            },
            columns=list(NEUTRALISE_ON),
            index=raw.index,
        )
        state = _state_vector(index, panel)
        return ranked, raw["sigma30"], controls, state

    # ------------------------------------------------------------------ labels
    def _realise(self, now: pd.Timestamp, last: pd.Series) -> None:
        """Move stored rows that have reached each horizon into that horizon's training set."""
        for horizon in self._horizons():
            stamp = now - pd.Timedelta(days=horizon)
            stored = self._observations.get(stamp)
            if stored is None:
                continue
            ranked, entry, sigma, state = stored
            realised = ((last.reindex(ranked.index) / entry - 1.0) / sigma).replace(
                [np.inf, -np.inf], np.nan
            )
            # Ranking the label keeps the target on the same bounded scale in every regime, so a
            # violent month cannot dominate the fit purely by having larger numbers in it.
            label = toolkit.cross_sectional_rank(realised.dropna())
            if len(label) < MINIMUM_SECTION:
                continue
            block = ranked.reindex(label.index).to_numpy(dtype=float)
            rows = self._rows.setdefault(horizon, [])
            labels = self._labels.setdefault(horizon, [])
            states = self._states.setdefault(horizon, [])
            rows.extend(block)
            labels.extend(float(value) for value in label.to_numpy(dtype=float))
            states.extend([state] * len(block))
            excess = len(rows) - int(self.memory_rows)
            if excess > 0:
                del rows[:excess]
                del labels[:excess]
                del states[:excess]
        horizon_limit = pd.Timedelta(days=4 * max(1, int(self.horizon_days)) + 2)
        stale = [stamp for stamp in self._observations if now - stamp > horizon_limit]
        for stamp in stale:
            del self._observations[stamp]

    # ------------------------------------------------------------------ fitting
    def _fit(self, design, labels, weights):
        total = float(weights.sum())
        if not math.isfinite(total) or total <= 0.0:
            return None
        gram = design.T @ (design * weights[:, None])
        moment = design.T @ (labels * weights)
        ridge = max(1e-9, float(self.ridge_lambda)) * total * np.eye(design.shape[1])
        try:
            fitted = np.linalg.solve(gram + ridge, moment)
        except np.linalg.LinAlgError:
            fitted = np.linalg.lstsq(gram + ridge, moment, rcond=None)[0]
        return fitted if np.all(np.isfinite(fitted)) else None

    def _refit(self, state_now) -> None:
        for horizon in self._horizons():
            rows = self._rows.get(horizon, [])
            if len(rows) < int(self.minimum_rows):
                continue
            design = np.asarray(rows, dtype=float)
            labels = np.asarray(self._labels[horizon], dtype=float)
            pooled = self._fit(design, labels, np.ones(len(design), dtype=float))
            if pooled is None:
                continue
            fitted = pooled
            if state_now is not None:
                states = np.asarray(self._states[horizon], dtype=float)
                usable = np.all(np.isfinite(states), axis=1)
                if usable.sum() >= int(self.minimum_rows):
                    scale = np.std(states[usable], axis=0)
                    scale = np.where(scale > 0.0, scale, 1.0)
                    distance = np.sum(((states - state_now) / scale) ** 2, axis=1)
                    width = max(1e-6, float(self.state_bandwidth)) ** 2
                    kernel = np.where(usable, np.exp(-0.5 * distance / width), 0.0)
                    # An effective sample size, not a raw one: a kernel that has collapsed onto a
                    # handful of rows is a fit on a handful of rows however many rows it touched.
                    total = float(kernel.sum())
                    effective = (total * total / float((kernel * kernel).sum())) if total > 0 else 0.0
                    if effective >= float(self.minimum_rows):
                        matched = self._fit(design, labels, kernel)
                        if matched is not None:
                            fitted = matched
            self._coefficients[horizon] = fitted

    # ------------------------------------------------------------------ book
    def _book(self, prediction, sigma, controls, eligible):
        design = np.column_stack(
            [np.ones(len(prediction)), controls.reindex(prediction.index).to_numpy(dtype=float)]
        )
        target = prediction.to_numpy(dtype=float)
        coefficients, *_ = np.linalg.lstsq(design, target, rcond=None)
        residual = pd.Series(target - design @ coefficients, index=prediction.index)
        ranks = toolkit.cross_sectional_rank(residual)
        if ranks.empty:
            return None
        count = len(ranks)
        side = max(1, min(int(self.breadth), (count - 1) // 2))
        cut = 0.5 - (side + 0.5) / count
        magnitude = (ranks.abs() - cut).clip(lower=0.0) / max(1e-9, 0.5 - cut)
        signals = {
            str(symbol): float(np.sign(ranks[symbol]) * magnitude[symbol])
            for symbol in ranks.index
            if magnitude[symbol] > 0.0
        }
        raw = toolkit.vol_parity(
            signals, sigma, neutral=True, symbol_cap=float(self.symbol_cap)
        )
        return self._smoother.update(raw, eligible)

    # ------------------------------------------------------------------ entrypoint
    def target_weights(
        self, context: DecisionContextV2, *, seed: int
    ) -> Mapping[str, float] | None:
        if not toolkit.is_daily_decision(context):
            return None
        panel = toolkit.close_panel(context)
        if panel.empty:
            return None
        now = pd.Timestamp(context.decision_time)
        ranked, sigma, controls, state = self._section(context, panel)
        if ranked is not None:
            self._observations[now] = (
                ranked,
                panel.iloc[-1].reindex(ranked.index),
                sigma,
                state if state is not None else np.full(STATE_DIMENSIONS, np.nan),
            )
        self._realise(now, panel.iloc[-1])
        cadence = pd.Timedelta(days=max(1, int(self.refit_days)))
        if self._last_fit is None or now - self._last_fit >= cadence:
            self._last_fit = now
            self._refit(state)
        if not self._coefficients:
            # Honest silence: no artifact was carried in, so there is nothing to trade on yet.
            return {}
        if ranked is None:
            return None
        matrix = ranked.to_numpy(dtype=float)
        predictions = [
            toolkit.cross_sectional_rank(pd.Series(matrix @ vector, index=ranked.index))
            for vector in (
                self._coefficients[horizon]
                for horizon in self._horizons()
                if horizon in self._coefficients
            )
        ]
        if not predictions:
            return {}
        combined = sum(predictions) / float(len(predictions))
        return self._book(combined, sigma, controls, context.eligible_symbols)


def _beta_and_correlation(returns: pd.DataFrame, index: pd.Series, bars: int):
    """Vectorised beta and correlation against the equal-weight cross-section."""
    window = returns.tail(bars)
    reference = index.reindex(window.index)
    values = window.to_numpy(dtype=float)
    mask = np.isfinite(values)
    market = reference.to_numpy(dtype=float)
    market = np.where(np.isfinite(market), market, np.nan)
    valid = mask & np.isfinite(market)[:, None]
    counts = valid.sum(axis=0)
    filled = np.where(valid, values, 0.0)
    reference_filled = np.where(np.isfinite(market), market, 0.0)[:, None]
    reference_masked = np.where(valid, reference_filled, 0.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        n = np.where(counts > 2, counts, np.nan)
        mean_x = filled.sum(axis=0) / n
        mean_m = reference_masked.sum(axis=0) / n
        centred_x = np.where(valid, filled - mean_x, 0.0)
        centred_m = np.where(valid, reference_masked - mean_m, 0.0)
        covariance = (centred_x * centred_m).sum(axis=0) / (n - 1.0)
        variance_m = (centred_m * centred_m).sum(axis=0) / (n - 1.0)
        variance_x = (centred_x * centred_x).sum(axis=0) / (n - 1.0)
        beta = covariance / np.where(variance_m > 0.0, variance_m, np.nan)
        denominator = np.sqrt(variance_x * variance_m)
        correlation = covariance / np.where(denominator > 0.0, denominator, np.nan)
    columns = list(returns.columns)
    return (
        pd.Series(beta, index=columns).replace([np.inf, -np.inf], np.nan).dropna(),
        pd.Series(correlation, index=columns).replace([np.inf, -np.inf], np.nan).dropna(),
    )


def _state_vector(index: pd.Series, panel: pd.DataFrame):
    """The market state that was observable when an observation was made.

    Trailing index return, trailing index volatility and cross-sectional dispersion. Every element
    is a past-only statistic: the regime a month turns out to be is never an input, because at the
    moment of the decision nobody has it.
    """
    bars = toolkit.bars_for_days(21)
    trailing = index.tail(bars)
    if len(trailing) < 3:
        return None
    dispersion = toolkit.trailing_return(panel, min(bars, max(3, len(panel) - 1)))
    values = np.array(
        [
            float(trailing.sum()),
            float(trailing.std(ddof=1)),
            float(dispersion.std(ddof=1)) if len(dispersion) > 2 else np.nan,
        ],
        dtype=float,
    )
    return values if np.all(np.isfinite(values)) else None


def build_strategy() -> StateMatchedRidge:
    return StateMatchedRidge()
