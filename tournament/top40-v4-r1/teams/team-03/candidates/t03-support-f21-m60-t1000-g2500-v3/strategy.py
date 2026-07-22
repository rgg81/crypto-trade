"""Short-horizon volume-confirmed momentum with strict causal state gating."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    interval_hours: int = 8
    formation_days: int = 21
    confirmation_days: int = 14
    rebalance_weekday: int = 0
    rebalance_hour_utc: int = 0
    minimum_positive_volume_fraction: float = 0.9
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    weak_confirmation_scale: float = 0.35
    market_days: int = 60
    market_threshold: float = 0.10
    total_gross: float = 0.25
    maximum_symbol_weight: float = 0.04
    maximum_abs_net: float = 0.25


_REFERENCE = StrategyParameters()


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        decision_time.weekday() == parameters.rebalance_weekday
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
    minimum_positive_volume_fraction: float,
) -> pd.DataFrame:
    columns = ["open_time", "close", "quote_volume"]
    if not set(columns).issubset(frame.columns):
        return pd.DataFrame(columns=columns)
    bounded = frame.tail(required_bars + 3)
    times = pd.to_datetime(bounded["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    history = bounded.loc[complete, columns].copy()
    history["open_time"] = times.loc[complete]
    history["close"] = pd.to_numeric(history["close"], errors="coerce")
    history["quote_volume"] = pd.to_numeric(history["quote_volume"], errors="coerce")
    values = history[["close", "quote_volume"]].to_numpy(dtype=float)
    finite = (
        np.isfinite(values).all(axis=1)
        & history["close"].gt(0.0).to_numpy(dtype=bool)
        & history["quote_volume"].ge(0.0).to_numpy(dtype=bool)
    )
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
    if float(history["quote_volume"].gt(0.0).mean()) < minimum_positive_volume_fraction:
        return pd.DataFrame(columns=columns)
    return history


def _scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    bars_per_day = 24 // parameters.interval_hours
    formation_bars = parameters.formation_days * bars_per_day
    confirmation_bars = parameters.confirmation_days * bars_per_day
    required_bars = max(formation_bars + 1, confirmation_bars + 1)
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
            minimum_positive_volume_fraction=parameters.minimum_positive_volume_fraction,
        )
        if history.empty:
            continue
        closes = history["close"].to_numpy(dtype=float)
        volumes = history["quote_volume"].to_numpy(dtype=float)[1:]
        returns = np.diff(np.log(closes))
        trend_returns = returns[-formation_bars:]
        realized = float(np.std(trend_returns, ddof=1))
        trend_return = float(np.sum(trend_returns))
        if not math.isfinite(realized) or realized <= 1e-8 or trend_return == 0.0:
            continue
        direction = 1.0 if trend_return > 0.0 else -1.0
        trend_score = trend_return / (realized * math.sqrt(formation_bars))

        recent_returns = returns[-confirmation_bars:]
        recent_volumes = volumes[-confirmation_bars:]
        positive_recent = recent_volumes[recent_volumes > 0.0]
        volume_sum = float(np.sum(recent_volumes))
        if positive_recent.size == 0 or volume_sum <= 0.0:
            continue
        support = float(np.sum(recent_volumes[recent_returns * direction > 0.0]) / volume_sum)
        confirmation_scale = 0.5 + support
        if support < 0.5:
            confirmation_scale *= parameters.weak_confirmation_scale
        score = trend_score * confirmation_scale
        if math.isfinite(score):
            scores[symbol] = float(score)
    return scores


def _market_return(
    context: DecisionContext,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> float | None:
    frame = context.bars.get("BTCUSDT")
    if frame is None:
        return None
    bars_per_day = 24 // parameters.interval_hours
    required_bars = parameters.market_days * bars_per_day + 1
    interval = pd.Timedelta(hours=parameters.interval_hours)
    history = _complete_history(
        frame,
        decision_time=decision_time,
        required_bars=required_bars,
        interval=interval,
        minimum_positive_volume_fraction=parameters.minimum_positive_volume_fraction,
    )
    if history.empty:
        return None
    closes = history["close"].to_numpy(dtype=float)
    value = float(math.log(closes[-1] / closes[0]))
    return value if math.isfinite(value) else None


def _portfolio(
    scores: dict[str, float],
    *,
    market_return: float | None,
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
    if market_return is not None and market_return > parameters.market_threshold:
        long_gross = parameters.total_gross
        short_gross = 0.0
    elif market_return is not None and market_return < -parameters.market_threshold:
        long_gross = 0.0
        short_gross = parameters.total_gross
    else:
        long_gross = parameters.total_gross / 2.0
        short_gross = parameters.total_gross / 2.0
    if not longs:
        long_gross = 0.0
    if not shorts:
        short_gross = 0.0
    long_weight = min(
        parameters.maximum_symbol_weight,
        long_gross / len(longs) if longs else 0.0,
    )
    short_weight = min(
        parameters.maximum_symbol_weight,
        short_gross / len(shorts) if shorts else 0.0,
    )
    targets = {symbol: -short_weight for symbol in shorts}
    targets.update({symbol: long_weight for symbol in longs})
    gross = math.fsum(abs(value) for value in targets.values())
    net = math.fsum(targets.values())
    if gross > parameters.total_gross + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: targets[symbol] for symbol in sorted(targets)}


class VolumeConfirmedMomentum:
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
        market_return = _market_return(
            context,
            decision_time=decision_time,
            parameters=self.parameters,
        )
        return _portfolio(
            scores,
            market_return=market_return,
            parameters=self.parameters,
        )


def build_strategy() -> TargetStrategy:
    return VolumeConfirmedMomentum()
