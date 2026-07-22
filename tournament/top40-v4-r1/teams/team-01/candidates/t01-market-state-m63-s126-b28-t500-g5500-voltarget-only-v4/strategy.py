"""Volatility-only fast-market-state slow per-coin momentum for Team 01."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    interval_hours: int = 8
    medium_days: int = 63
    slow_days: int = 126
    volatility_days: int = 63
    rebalance_weekday: int = 0
    rebalance_hour_utc: int = 0
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    disagreement_scale: float = 0.25
    market_days: int = 28
    market_threshold: float = 0.05
    dominant_side_fraction: float = 0.72
    total_gross: float = 0.55
    maximum_symbol_weight: float = 0.05
    maximum_abs_net: float = 0.242


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
) -> pd.DataFrame:
    required_columns = {"open_time", "close"}
    if not required_columns.issubset(frame.columns):
        return pd.DataFrame(columns=["open_time", "close"])

    bounded = frame.tail(required_bars + 3)
    times = pd.to_datetime(bounded["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    history = bounded.loc[complete, ["open_time", "close"]].copy()
    history["open_time"] = times.loc[complete]
    history["close"] = pd.to_numeric(history["close"], errors="coerce")
    finite = np.isfinite(history["close"].to_numpy(dtype=float)) & history["close"].gt(0.0)
    history = (
        history.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .tail(required_bars)
        .reset_index(drop=True)
    )
    if len(history) != required_bars:
        return pd.DataFrame(columns=["open_time", "close"])
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_bars,
        freq=interval,
    )
    if not pd.DatetimeIndex(history["open_time"]).equals(expected):
        return pd.DataFrame(columns=["open_time", "close"])
    return history


def _scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    bars_per_day = 24 // parameters.interval_hours
    medium_bars = parameters.medium_days * bars_per_day
    slow_bars = parameters.slow_days * bars_per_day
    volatility_bars = parameters.volatility_days * bars_per_day
    required_bars = slow_bars + 1
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
        closes = history["close"].to_numpy(dtype=float)
        returns = np.diff(np.log(closes))
        realized = float(np.std(returns[-volatility_bars:], ddof=1))
        if not math.isfinite(realized) or realized <= 1e-8:
            continue

        medium_return = float(np.sum(returns[-medium_bars:]))
        slow_return = float(np.sum(returns[-slow_bars:]))
        medium_signal = medium_return / (realized * math.sqrt(medium_bars))
        slow_signal = slow_return / (realized * math.sqrt(slow_bars))
        agreement = medium_signal * slow_signal >= 0.0
        score = 0.35 * medium_signal + 0.65 * slow_signal
        if not agreement:
            score *= parameters.disagreement_scale
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
        long_fraction = parameters.dominant_side_fraction
    elif market_return is not None and market_return < -parameters.market_threshold:
        long_fraction = 1.0 - parameters.dominant_side_fraction
    else:
        long_fraction = 0.5
    long_gross = parameters.total_gross * long_fraction
    short_gross = parameters.total_gross - long_gross
    if not longs:
        long_gross = 0.0
        short_gross = min(short_gross, parameters.maximum_abs_net)
    if not shorts:
        short_gross = 0.0
        long_gross = min(long_gross, parameters.maximum_abs_net)
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


class SlowPerCoinMomentum:
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
        return _portfolio(scores, market_return=market_return, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return SlowPerCoinMomentum()
