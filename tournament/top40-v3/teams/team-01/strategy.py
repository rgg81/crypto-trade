"""Team 01: causal weekday-residual seasonality with append-only caches."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    interval_hours: int = 8
    decision_hour_utc: int = 0
    same_weekday_occurrences: int = 13
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    total_gross: float = 0.48
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05


_REFERENCE = StrategyParameters()


@dataclasses.dataclass
class _SymbolCache:
    """Causal derived history for one append-only worker bar stream."""

    cursor: int = 0
    partial_days: dict[pd.Timestamp, dict[int, float]] = dataclasses.field(
        default_factory=dict
    )
    daily_closes: dict[pd.Timestamp, float] = dataclasses.field(default_factory=dict)
    daily_returns: dict[pd.Timestamp, float] = dataclasses.field(default_factory=dict)


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        decision_time.hour == parameters.decision_hour_utc
        and decision_time.minute == 0
        and decision_time.second == 0
        and decision_time.microsecond == 0
    )


def _update_symbol_cache(
    frame: pd.DataFrame,
    *,
    cache: _SymbolCache,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> None:
    """Consume each completed canonical bar at most once."""

    if not {"open_time", "close"}.issubset(frame.columns):
        return
    if len(frame) < cache.cursor:
        # Fail safely if an unexpected worker reset replaces an append-only history.
        cache.cursor = 0
        cache.partial_days.clear()
        cache.daily_closes.clear()
        cache.daily_returns.clear()
    if len(frame) == cache.cursor:
        return

    delta = frame.iloc[cache.cursor:]
    times = pd.to_datetime(delta["open_time"], utc=True, errors="coerce")
    interval = pd.Timedelta(hours=parameters.interval_hours)
    complete = times.notna() & ((times + interval) <= decision_time)
    complete_positions = np.flatnonzero(complete.to_numpy(dtype=bool))
    if not len(complete_positions):
        return
    consumed = int(complete_positions[-1]) + 1
    chunk = delta.iloc[:consumed]
    chunk_times = times.iloc[:consumed]
    cache.cursor += consumed

    closes = pd.to_numeric(chunk["close"], errors="coerce").to_numpy(dtype=float)
    touched_days: set[pd.Timestamp] = set()
    seen_times: set[pd.Timestamp] = set()
    for timestamp, close in zip(chunk_times, closes, strict=True):
        if pd.isna(timestamp) or not math.isfinite(close) or close <= 0.0:
            continue
        timestamp = _utc(timestamp)
        if (
            timestamp in seen_times
            or timestamp.minute != 0
            or timestamp.second != 0
            or timestamp.microsecond != 0
            or timestamp.hour % parameters.interval_hours != 0
        ):
            continue
        seen_times.add(timestamp)
        day = timestamp.floor("D")
        cache.partial_days.setdefault(day, {})[timestamp.hour] = float(close)
        touched_days.add(day)

    new_close_days: list[pd.Timestamp] = []
    expected_hours = {0, 8, 16}
    for day in sorted(touched_days):
        slots = cache.partial_days.get(day, {})
        if set(slots) != expected_hours:
            continue
        cache.daily_closes[day] = slots[16]
        cache.partial_days.pop(day, None)
        new_close_days.append(day)

    for day in new_close_days:
        previous_day = day - pd.Timedelta(days=1)
        previous_close = cache.daily_closes.get(previous_day)
        close = cache.daily_closes[day]
        if previous_close is None:
            continue
        value = math.log(close / previous_close)
        if math.isfinite(value):
            # The day-16:00 close completes the return from day 00:00 through day 24:00.
            cache.daily_returns[day] = value


def _weekday_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
    caches: dict[str, _SymbolCache],
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    eligible = tuple(sorted({str(symbol) for symbol in context.eligible_symbols}))
    for symbol in eligible:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        cache = caches.setdefault(symbol, _SymbolCache())
        _update_symbol_cache(
            frame,
            cache=cache,
            decision_time=decision_time,
            parameters=parameters,
        )

    histories: dict[str, Mapping[pd.Timestamp, float]] = {
        symbol: caches[symbol].daily_returns
        for symbol in eligible
        if symbol in caches and caches[symbol].daily_returns
    }
    if len(histories) < parameters.minimum_valid_symbols:
        return {}

    target_weekday = decision_time.weekday()
    selected_dates: dict[str, tuple[pd.Timestamp, ...]] = {}
    candidate_dates: set[pd.Timestamp] = set()
    for symbol, history in histories.items():
        dates = tuple(sorted(day for day in history if day.weekday() == target_weekday))
        if len(dates) < parameters.same_weekday_occurrences:
            continue
        chosen = dates[-parameters.same_weekday_occurrences :]
        selected_dates[symbol] = chosen
        candidate_dates.update(chosen)
    if len(selected_dates) < parameters.minimum_valid_symbols:
        return {}

    ordered_dates = tuple(sorted(candidate_dates))
    returns = pd.DataFrame(
        {
            symbol: pd.Series(
                {day: history[day] for day in ordered_dates if day in history},
                dtype=float,
            )
            for symbol, history in histories.items()
        },
        index=ordered_dates,
        dtype=float,
    )
    residuals = returns.sub(returns.median(axis=1, skipna=True), axis=0)
    scores: dict[str, float] = {}
    for symbol in sorted(selected_dates):
        value = float(residuals.loc[list(selected_dates[symbol]), symbol].mean())
        if math.isfinite(value):
            scores[symbol] = value
    return scores


def _portfolio(
    scores: dict[str, float],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if len(scores) < parameters.minimum_valid_symbols:
        return {}
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    side_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(ordered))),
    )
    side_count = min(side_count, len(ordered) // 2)
    if side_count < parameters.minimum_positions_per_side:
        return {}

    shorts = ordered[:side_count]
    longs = ordered[-side_count:]
    side_gross = parameters.total_gross / 2.0
    weight = side_gross / side_count
    if weight > parameters.maximum_symbol_weight + 1e-12:
        return {}

    result = {symbol: -weight for symbol in shorts}
    result.update({symbol: weight for symbol in longs})
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > parameters.total_gross + 1e-12:
        return {}
    if abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class WeekdayResidualSeasonality:
    def __init__(self, parameters: StrategyParameters = _REFERENCE):
        self.parameters = parameters
        self._caches: dict[str, _SymbolCache] = {}

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> dict[str, float] | None:
        del seed
        decision_time = _utc(context.decision_time)
        if not _is_scheduled(decision_time, self.parameters):
            return None
        scores = _weekday_scores(
            context,
            parameters=self.parameters,
            caches=self._caches,
        )
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return WeekdayResidualSeasonality()
