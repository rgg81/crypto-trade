"""Dual-trend weekly fast breakout for Team 02."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    interval_hours: int = 8
    channel_days: int = 20
    confirmation_days: int = 7
    trend_days: int = 63
    persistence_bars: int = 3
    rebalance_weekdays: tuple[int, ...] = (0,)
    rebalance_hour_utc: int = 0
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    unconfirmed_scale: float = 0.2
    total_gross: float = 0.36
    maximum_symbol_weight: float = 0.04


_REFERENCE = StrategyParameters()


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        decision_time.weekday() in parameters.rebalance_weekdays
        and decision_time.hour == parameters.rebalance_hour_utc
        and decision_time.minute == 0
        and decision_time.second == 0
        and decision_time.microsecond == 0
    )


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    required_bars: int,
    interval: pd.Timedelta,
) -> pd.DataFrame:
    columns = ["open_time", "high", "low", "close"]
    if not set(columns).issubset(frame.columns):
        return pd.DataFrame(columns=columns)
    bounded = frame.tail(required_bars + 3)
    times = pd.to_datetime(bounded["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    history = bounded.loc[complete, columns].copy()
    history["open_time"] = times.loc[complete]
    for column in ("high", "low", "close"):
        history[column] = pd.to_numeric(history[column], errors="coerce")
    values = history[["high", "low", "close"]].to_numpy(dtype=float)
    finite = np.isfinite(values).all(axis=1) & (values > 0.0).all(axis=1)
    history = (
        history.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .tail(required_bars)
        .reset_index(drop=True)
    )
    if len(history) != required_bars:
        return pd.DataFrame(columns=columns)
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_bars,
        freq=interval,
    )
    if not pd.DatetimeIndex(history["open_time"]).equals(expected):
        return pd.DataFrame(columns=columns)
    return history


def _scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    bars_per_day = 24 // parameters.interval_hours
    channel_bars = parameters.channel_days * bars_per_day
    confirmation_bars = parameters.confirmation_days * bars_per_day
    trend_bars = parameters.trend_days * bars_per_day
    required_bars = max(channel_bars, confirmation_bars, trend_bars) + 1
    interval = pd.Timedelta(hours=parameters.interval_hours)
    scores: dict[str, float] = {}

    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _complete_history(
            frame,
            decision_time=decision_time,
            required_bars=required_bars,
            interval=interval,
        )
        if history.empty:
            continue
        prior = history.iloc[-channel_bars - 1 : -1]
        upper = float(prior["high"].max())
        lower = float(prior["low"].min())
        half_width = 0.5 * (upper - lower)
        midpoint = 0.5 * (upper + lower)
        close = float(history.iloc[-1]["close"])
        if not math.isfinite(half_width) or half_width <= 1e-12:
            continue

        channel_position = float(np.clip((close - midpoint) / half_width, -2.0, 2.0))
        closes = history["close"].to_numpy(dtype=float)
        trend_return = float(np.log(closes[-1] / closes[-trend_bars - 1]))
        recent_returns = np.diff(np.log(closes[-confirmation_bars - 1 :]))
        realized = float(np.std(recent_returns, ddof=1))
        if not math.isfinite(realized) or realized <= 1e-8:
            continue
        confirmation_return = float(np.sum(recent_returns))
        momentum = confirmation_return / (realized * math.sqrt(confirmation_bars))
        momentum = float(np.clip(momentum, -2.0, 2.0))
        raw_score = 0.65 * channel_position + 0.35 * momentum
        if abs(raw_score) <= 1e-12 or raw_score * trend_return <= 0.0:
            continue
        direction = 1.0 if raw_score > 0.0 else -1.0
        persistent_closes = closes[-parameters.persistence_bars :]
        persistent = bool(
            np.all(persistent_closes > midpoint)
            if direction > 0.0
            else np.all(persistent_closes < midpoint)
        )
        confirmed = persistent and confirmation_return * direction > 0.0
        score = raw_score if confirmed else raw_score * parameters.unconfirmed_scale
        if math.isfinite(score):
            scores[symbol] = float(score)
    return scores


def _portfolio(
    scores: dict[str, float],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if len(scores) < parameters.minimum_valid_symbols:
        return {}
    values = tuple(scores.values())
    if max(values) - min(values) <= 1e-12:
        return {}
    desired = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(scores))),
    )
    longs = sorted(
        (symbol for symbol, score in scores.items() if score > 0.0),
        key=lambda symbol: (-scores[symbol], symbol),
    )[:desired]
    shorts = sorted(
        (symbol for symbol, score in scores.items() if score < 0.0),
        key=lambda symbol: (scores[symbol], symbol),
    )[:desired]
    if len(longs) < parameters.minimum_positions_per_side:
        longs = []
    if len(shorts) < parameters.minimum_positions_per_side:
        shorts = []
    if not longs and not shorts:
        return {}
    side_gross = parameters.total_gross / 2.0
    long_weight = min(
        parameters.maximum_symbol_weight,
        side_gross / len(longs) if longs else 0.0,
    )
    short_weight = min(
        parameters.maximum_symbol_weight,
        side_gross / len(shorts) if shorts else 0.0,
    )
    targets = {symbol: -short_weight for symbol in shorts}
    targets.update({symbol: long_weight for symbol in longs})
    return {symbol: targets[symbol] for symbol in sorted(targets)}


class BufferedFastBreakout:
    def __init__(self, parameters: StrategyParameters = _REFERENCE):
        self.parameters = parameters

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> dict[str, float] | None:
        del seed
        decision_time = _utc(context.decision_time)
        if not _scheduled(decision_time, self.parameters):
            return None
        scores = _scores(context, parameters=self.parameters)
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return BufferedFastBreakout()
