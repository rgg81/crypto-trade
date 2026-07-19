"""Post-tournament Team 04 UTC family with cadence and rank-persistence controls."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

_INTERVAL = pd.Timedelta(hours=8)
_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    canonical_seed: int = 20260718
    slow_trend_days: int = 42
    slow_skip_days: int = 2
    fast_trend_days: int = 14
    fast_skip_days: int = 1
    funding_lookback_days: int = 7
    minimum_funding_events: int = 7
    maximum_funding_staleness_hours: int = 16
    maximum_absolute_funding_rate: float = 0.05
    volatility_lookback_days: int = 30
    volatility_keep_numerator: int = 4
    volatility_keep_denominator: int = 5
    slow_weight: float = 0.50
    fast_weight: float = 0.30
    funding_weight: float = 0.20
    minimum_prefilter_cross_section: int = 30
    minimum_cross_section: int = 24
    selection_numerator: int = 1
    selection_denominator: int = 4
    minimum_sleeve_names: int = 6
    gross_target: float = 0.60
    side_budget: float = 0.30
    symbol_cap: float = 0.04
    rebalance_bars: int = 9
    rank_buffer_fraction: float = 0.25
    epsilon: float = 1e-12
    tolerance: float = 1e-12

    def __post_init__(self) -> None:
        if self.rebalance_bars not in {9, 21, 42}:
            raise ValueError("rebalance_bars is outside the preregistered matrix")
        if self.rank_buffer_fraction not in {0.25, 0.4}:
            raise ValueError("rank_buffer_fraction is outside the preregistered matrix")
        if not math.isclose(
            self.slow_weight + self.fast_weight + self.funding_weight,
            1.0,
            abs_tol=1e-12,
        ):
            raise ValueError("UTC score weights must sum to one")

    @property
    def history_return_bars(self) -> int:
        return max(
            3 * (self.slow_trend_days + self.slow_skip_days),
            3 * (self.fast_trend_days + self.fast_skip_days),
            3 * self.volatility_lookback_days,
        )


@dataclasses.dataclass(frozen=True)
class _PriceFeature:
    slow_trend: float
    fast_trend: float
    volatility: float


@dataclasses.dataclass(frozen=True)
class _Feature:
    slow_trend: float
    fast_trend: float
    funding_per_day: float
    volatility: float


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _utc_timestamp(value: Any) -> pd.Timestamp | None:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        return None
    try:
        return timestamp.tz_convert("UTC")
    except (TypeError, ValueError, OverflowError):
        return None


def _decision_index(value: Any) -> int | None:
    timestamp = _utc_timestamp(value)
    if timestamp is None:
        return None
    delta = timestamp.value - _EPOCH.value
    if delta % _INTERVAL.value:
        return None
    return delta // _INTERVAL.value


def _average_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    if len(values) < 2 or any(not math.isfinite(value) for value in values.values()):
        return None
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    denominator = len(ordered) - 1
    result: dict[str, float] = {}
    start = 0
    while start < len(ordered):
        stop = start + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[start][1]:
            stop += 1
        average_rank = ((start + 1) + stop) / 2.0
        mapped = 2.0 * (average_rank - 1.0) / denominator - 1.0
        for index in range(start, stop):
            result[ordered[index][0]] = mapped
        start = stop
    return result


def _expected_open_times(cutoff: pd.Timestamp, return_bars: int) -> tuple[pd.Timestamp, ...]:
    return tuple(cutoff - multiple * _INTERVAL for multiple in range(return_bars + 1, 0, -1))


def _window_sum(returns: Sequence[float], *, days: int, skip_days: int) -> float | None:
    width = 3 * days
    stop = len(returns) - 3 * skip_days
    start = stop - width
    if start < 0 or stop <= start:
        return None
    result = math.fsum(returns[start:stop])
    return result if math.isfinite(result) else None


def _price_feature(
    frame: Any,
    *,
    cutoff: pd.Timestamp,
    parameters: StrategyParameters,
) -> _PriceFeature | None:
    if not isinstance(frame, pd.DataFrame):
        return None
    required = ("open_time", "close_time", "close")
    if not set(required).issubset(frame.columns):
        return None
    expected = _expected_open_times(cutoff, parameters.history_return_bars)
    rows: dict[pd.Timestamp, list[float]] = {timestamp: [] for timestamp in expected}
    for raw_open, raw_close_time, raw_close in frame.loc[:, list(required)].itertuples(
        index=False, name=None
    ):
        open_time = _utc_timestamp(raw_open)
        if open_time is None or open_time not in rows:
            continue
        close_time = _utc_timestamp(raw_close_time)
        close = _finite_number(raw_close)
        if close_time is None or close_time > cutoff or close is None or close <= 0.0:
            continue
        rows[open_time].append(close)
    if any(len(rows[timestamp]) != 1 for timestamp in expected):
        return None
    closes = [rows[timestamp][0] for timestamp in expected]
    returns: list[float] = []
    for previous, current in zip(closes[:-1], closes[1:], strict=True):
        ratio = current / previous
        if not math.isfinite(ratio) or ratio <= 0.0:
            return None
        value = math.log(ratio)
        if not math.isfinite(value):
            return None
        returns.append(value)
    if len(returns) != parameters.history_return_bars:
        return None
    slow = _window_sum(
        returns, days=parameters.slow_trend_days, skip_days=parameters.slow_skip_days
    )
    fast = _window_sum(
        returns, days=parameters.fast_trend_days, skip_days=parameters.fast_skip_days
    )
    volatility_returns = returns[-3 * parameters.volatility_lookback_days :]
    mean = math.fsum(volatility_returns) / len(volatility_returns)
    variance = math.fsum((value - mean) ** 2 for value in volatility_returns) / len(
        volatility_returns
    )
    if slow is None or fast is None or not math.isfinite(variance) or variance < 0.0:
        return None
    volatility = math.sqrt(variance)
    if not math.isfinite(volatility):
        return None
    return _PriceFeature(slow_trend=slow, fast_trend=fast, volatility=volatility)


def _funding_per_day(
    frame: Any,
    *,
    eligible_symbols: Sequence[str],
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if not isinstance(frame, pd.DataFrame):
        return {}
    required = ("funding_time", "symbol", "funding_rate")
    if not set(required).issubset(frame.columns):
        return {}
    eligible = frozenset(eligible_symbols)
    start = decision_time - pd.Timedelta(days=parameters.funding_lookback_days)
    observed: dict[str, list[tuple[pd.Timestamp, float]]] = {symbol: [] for symbol in eligible}
    invalid: set[str] = set()
    for raw_time, raw_symbol, raw_rate in frame.loc[:, list(required)].itertuples(
        index=False, name=None
    ):
        if not isinstance(raw_symbol, str) or raw_symbol not in eligible:
            continue
        timestamp = _utc_timestamp(raw_time)
        if timestamp is None:
            invalid.add(raw_symbol)
            continue
        if timestamp < start or timestamp >= decision_time:
            continue
        rate = _finite_number(raw_rate)
        if rate is None or abs(rate) > parameters.maximum_absolute_funding_rate:
            invalid.add(raw_symbol)
            continue
        observed[raw_symbol].append((timestamp, rate))
    result: dict[str, float] = {}
    for symbol in sorted(eligible):
        if symbol in invalid:
            continue
        events = sorted(observed[symbol], key=lambda item: item[0])
        timestamps = [timestamp for timestamp, _rate in events]
        if (
            len(events) < parameters.minimum_funding_events
            or len(timestamps) != len(set(timestamps))
            or decision_time - events[-1][0]
            > pd.Timedelta(hours=parameters.maximum_funding_staleness_hours)
        ):
            continue
        value = math.fsum(rate for _timestamp, rate in events) / parameters.funding_lookback_days
        if math.isfinite(value):
            result[symbol] = value
    return result


def _retain_low_volatility(
    features: Mapping[str, _Feature], parameters: StrategyParameters
) -> tuple[str, ...] | None:
    if len(features) < parameters.minimum_prefilter_cross_section:
        return None
    keep = (parameters.volatility_keep_numerator * len(features)) // (
        parameters.volatility_keep_denominator
    )
    if keep < parameters.minimum_cross_section:
        return None
    ordered = sorted(features, key=lambda symbol: (features[symbol].volatility, symbol))
    return tuple(ordered[:keep])


def _sleeve_count(scores: Mapping[str, float], parameters: StrategyParameters) -> int | None:
    if len(scores) < parameters.minimum_cross_section:
        return None
    count = max(
        parameters.minimum_sleeve_names,
        (parameters.selection_numerator * len(scores)) // parameters.selection_denominator,
    )
    return count if 2 * count <= len(scores) else None


def _select_sleeves(
    scores: Mapping[str, float],
    *,
    previous_long: frozenset[str],
    previous_short: frozenset[str],
    parameters: StrategyParameters,
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    count = _sleeve_count(scores, parameters)
    if count is None:
        return None
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    if parameters.rank_buffer_fraction <= (
        parameters.selection_numerator / parameters.selection_denominator
    ):
        return tuple(ordered[-count:]), tuple(ordered[:count])

    buffer_count = max(count, math.ceil(parameters.rank_buffer_fraction * len(ordered)))
    long_buffer = frozenset(ordered[-buffer_count:])
    short_buffer = frozenset(ordered[:buffer_count])
    retained_long = sorted(
        previous_long & long_buffer,
        key=lambda symbol: (scores[symbol], symbol),
        reverse=True,
    )[:count]
    retained_short = sorted(
        previous_short & short_buffer,
        key=lambda symbol: (scores[symbol], symbol),
    )[:count]
    long_symbols = list(retained_long)
    short_symbols = list(retained_short)
    occupied = set(long_symbols) | set(short_symbols)
    for symbol in reversed(ordered):
        if len(long_symbols) >= count:
            break
        if symbol not in occupied:
            long_symbols.append(symbol)
            occupied.add(symbol)
    for symbol in ordered:
        if len(short_symbols) >= count:
            break
        if symbol not in occupied:
            short_symbols.append(symbol)
            occupied.add(symbol)
    if len(long_symbols) != count or len(short_symbols) != count:
        return None
    return tuple(sorted(long_symbols)), tuple(sorted(short_symbols))


def _equal_allocation(
    symbols: Sequence[str], parameters: StrategyParameters
) -> dict[str, float] | None:
    ordered = tuple(sorted(symbols))
    if not ordered:
        return None
    effective = min(parameters.side_budget, len(ordered) * parameters.symbol_cap)
    initial = effective / len(ordered)
    if not math.isfinite(initial) or initial < 0.0 or initial > parameters.symbol_cap:
        return None
    weights = {symbol: initial for symbol in ordered}
    residual = effective - math.fsum(weights.values())
    if residual > 0.0:
        for symbol in ordered:
            addition = min(residual, parameters.symbol_cap - weights[symbol])
            weights[symbol] += addition
            residual -= addition
            if residual == 0.0:
                break
    elif residual < 0.0:
        for symbol in ordered:
            subtraction = min(-residual, weights[symbol])
            weights[symbol] -= subtraction
            residual += subtraction
            if residual == 0.0:
                break
    if abs(residual) > parameters.tolerance:
        return None
    return weights


def _scheduled_targets(
    context: Any,
    decision_time: pd.Timestamp,
    *,
    previous_long: frozenset[str],
    previous_short: frozenset[str],
    parameters: StrategyParameters,
) -> tuple[dict[str, float], frozenset[str], frozenset[str]]:
    raw_eligible = getattr(context, "eligible_symbols", ())
    if isinstance(raw_eligible, (str, bytes)):
        return {}, frozenset(), frozenset()
    try:
        eligible_input = tuple(raw_eligible)
    except TypeError:
        return {}, frozenset(), frozenset()
    if any(not isinstance(symbol, str) or not symbol for symbol in eligible_input):
        return {}, frozenset(), frozenset()
    if len(eligible_input) != len(set(eligible_input)):
        return {}, frozenset(), frozenset()
    eligible = tuple(sorted(eligible_input))
    if len(eligible) < parameters.minimum_prefilter_cross_section:
        return {}, frozenset(), frozenset()
    bars = getattr(context, "bars", None)
    if not isinstance(bars, Mapping):
        return {}, frozenset(), frozenset()
    funding = _funding_per_day(
        getattr(context, "funding", None),
        eligible_symbols=eligible,
        decision_time=decision_time,
        parameters=parameters,
    )
    cutoff = decision_time - _INTERVAL
    features: dict[str, _Feature] = {}
    for symbol in eligible:
        price = _price_feature(bars.get(symbol), cutoff=cutoff, parameters=parameters)
        funding_value = funding.get(symbol)
        if price is None or funding_value is None:
            continue
        features[symbol] = _Feature(
            slow_trend=price.slow_trend,
            fast_trend=price.fast_trend,
            funding_per_day=funding_value,
            volatility=price.volatility,
        )
    retained = _retain_low_volatility(features, parameters)
    if retained is None:
        return {}, frozenset(), frozenset()
    slow_ranks = _average_ranks({symbol: features[symbol].slow_trend for symbol in retained})
    fast_ranks = _average_ranks({symbol: features[symbol].fast_trend for symbol in retained})
    funding_ranks = _average_ranks(
        {symbol: features[symbol].funding_per_day for symbol in retained}
    )
    if slow_ranks is None or fast_ranks is None or funding_ranks is None:
        return {}, frozenset(), frozenset()
    scores = {
        symbol: parameters.slow_weight * slow_ranks[symbol]
        + parameters.fast_weight * fast_ranks[symbol]
        - parameters.funding_weight * funding_ranks[symbol]
        for symbol in retained
    }
    sleeves = _select_sleeves(
        scores,
        previous_long=previous_long,
        previous_short=previous_short,
        parameters=parameters,
    )
    if sleeves is None:
        return {}, frozenset(), frozenset()
    long_symbols, short_symbols = sleeves
    mean_long_slow = math.fsum(features[symbol].slow_trend for symbol in long_symbols) / len(
        long_symbols
    )
    mean_short_slow = math.fsum(features[symbol].slow_trend for symbol in short_symbols) / len(
        short_symbols
    )
    mean_long_funding = math.fsum(
        features[symbol].funding_per_day for symbol in long_symbols
    ) / len(long_symbols)
    mean_short_funding = math.fsum(
        features[symbol].funding_per_day for symbol in short_symbols
    ) / len(short_symbols)
    if (
        mean_long_slow - mean_short_slow <= parameters.epsilon
        or mean_short_funding - mean_long_funding <= parameters.epsilon
    ):
        return {}, frozenset(), frozenset()
    long_weights = _equal_allocation(long_symbols, parameters)
    short_weights = _equal_allocation(short_symbols, parameters)
    if long_weights is None or short_weights is None:
        return {}, frozenset(), frozenset()
    targets = {
        **{symbol: long_weights[symbol] for symbol in sorted(long_weights)},
        **{symbol: -short_weights[symbol] for symbol in sorted(short_weights)},
    }
    gross = math.fsum(abs(weight) for weight in targets.values())
    net = math.fsum(targets.values())
    if (
        gross > parameters.gross_target + parameters.tolerance
        or abs(net) > parameters.tolerance
        or any(
            symbol not in eligible
            or not math.isfinite(weight)
            or abs(weight) > parameters.symbol_cap
            for symbol, weight in targets.items()
        )
    ):
        return {}, frozenset(), frozenset()
    return targets, frozenset(long_symbols), frozenset(short_symbols)


class UncrowdedTrendCarryResearch:
    def __init__(self, parameters: StrategyParameters) -> None:
        self._parameters = parameters
        self._previous_long: frozenset[str] = frozenset()
        self._previous_short: frozenset[str] = frozenset()

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or seed != self._parameters.canonical_seed
        ):
            raise ValueError("Team 04 UTC research requires canonical seed 20260718")
        decision_time = _utc_timestamp(getattr(context, "decision_time", None))
        decision_index = _decision_index(getattr(context, "decision_time", None))
        if decision_time is None or decision_index is None:
            return {}
        if decision_index % self._parameters.rebalance_bars:
            return None
        try:
            targets, long_symbols, short_symbols = _scheduled_targets(
                context,
                decision_time,
                previous_long=self._previous_long,
                previous_short=self._previous_short,
                parameters=self._parameters,
            )
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError):
            targets, long_symbols, short_symbols = {}, frozenset(), frozenset()
        self._previous_long = long_symbols
        self._previous_short = short_symbols
        return targets


def strategy(parameters: StrategyParameters) -> UncrowdedTrendCarryResearch:
    return UncrowdedTrendCarryResearch(parameters)
