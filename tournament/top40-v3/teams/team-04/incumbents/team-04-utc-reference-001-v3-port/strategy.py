"""Uncrowded Trend Carry (UTC) exact no-control reference candidate."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

_INTERVAL = pd.Timedelta(hours=8)
_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


@dataclasses.dataclass(frozen=True)
class _Config:
    candidate_id: str = "team-04-utc-reference-001"
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
    epsilon: float = 1e-12
    tolerance: float = 1e-12

    @property
    def history_return_bars(self) -> int:
        return max(
            3 * (self.slow_trend_days + self.slow_skip_days),
            3 * (self.fast_trend_days + self.fast_skip_days),
            3 * self.volatility_lookback_days,
        )


_REFERENCE = _Config()


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
    config: _Config = _REFERENCE,
) -> _PriceFeature | None:
    if not isinstance(frame, pd.DataFrame):
        return None
    required = ("open_time", "close_time", "close")
    if not set(required).issubset(frame.columns):
        return None
    expected = _expected_open_times(cutoff, config.history_return_bars)
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
    if len(returns) != config.history_return_bars:
        return None
    slow = _window_sum(
        returns,
        days=config.slow_trend_days,
        skip_days=config.slow_skip_days,
    )
    fast = _window_sum(
        returns,
        days=config.fast_trend_days,
        skip_days=config.fast_skip_days,
    )
    volatility_returns = returns[-3 * config.volatility_lookback_days :]
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
    config: _Config = _REFERENCE,
) -> dict[str, float]:
    if not isinstance(frame, pd.DataFrame):
        return {}
    required = ("funding_time", "symbol", "funding_rate")
    if not set(required).issubset(frame.columns):
        return {}
    eligible = frozenset(eligible_symbols)
    start = decision_time - pd.Timedelta(days=config.funding_lookback_days)
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
        if rate is None or abs(rate) > config.maximum_absolute_funding_rate:
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
            len(events) < config.minimum_funding_events
            or len(timestamps) != len(set(timestamps))
            or decision_time - events[-1][0]
            > pd.Timedelta(hours=config.maximum_funding_staleness_hours)
        ):
            continue
        value = math.fsum(rate for _timestamp, rate in events) / config.funding_lookback_days
        if math.isfinite(value):
            result[symbol] = value
    return result


def _retain_low_volatility(
    features: Mapping[str, _Feature], config: _Config = _REFERENCE
) -> tuple[str, ...] | None:
    if len(features) < config.minimum_prefilter_cross_section:
        return None
    keep = (config.volatility_keep_numerator * len(features)) // (
        config.volatility_keep_denominator
    )
    if keep < config.minimum_cross_section:
        return None
    ordered = sorted(
        features,
        key=lambda symbol: (features[symbol].volatility, symbol),
    )
    return tuple(ordered[:keep])


def _select_sleeves(
    scores: Mapping[str, float], config: _Config = _REFERENCE
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    if len(scores) < config.minimum_cross_section:
        return None
    count = max(
        config.minimum_sleeve_names,
        (config.selection_numerator * len(scores)) // config.selection_denominator,
    )
    if 2 * count > len(scores):
        return None
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    return tuple(ordered[-count:]), tuple(ordered[:count])


def _equal_allocation(
    symbols: Sequence[str], config: _Config = _REFERENCE
) -> dict[str, float] | None:
    ordered = tuple(sorted(symbols))
    if not ordered:
        return None
    effective = min(config.side_budget, len(ordered) * config.symbol_cap)
    initial = effective / len(ordered)
    if not math.isfinite(initial) or initial < 0.0 or initial > config.symbol_cap:
        return None
    weights = {symbol: initial for symbol in ordered}
    residual = effective - math.fsum(weights.values())
    if residual > 0.0:
        for symbol in ordered:
            addition = min(residual, config.symbol_cap - weights[symbol])
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
    if abs(residual) > config.tolerance:
        return None
    if any(
        not math.isfinite(value) or value < 0.0 or value > config.symbol_cap
        for value in weights.values()
    ):
        return None
    if abs(math.fsum(weights.values()) - effective) > config.tolerance:
        return None
    return weights


def _scheduled_targets(
    context: Any, decision_time: pd.Timestamp, config: _Config
) -> dict[str, float]:
    raw_eligible = getattr(context, "eligible_symbols", ())
    if isinstance(raw_eligible, (str, bytes)):
        return {}
    try:
        eligible_input = tuple(raw_eligible)
    except TypeError:
        return {}
    if any(not isinstance(symbol, str) or not symbol for symbol in eligible_input):
        return {}
    if len(eligible_input) != len(set(eligible_input)):
        return {}
    eligible = tuple(sorted(eligible_input))
    if len(eligible) < config.minimum_prefilter_cross_section:
        return {}
    bars = getattr(context, "bars", None)
    if not isinstance(bars, Mapping):
        return {}
    funding = _funding_per_day(
        getattr(context, "funding", None),
        eligible_symbols=eligible,
        decision_time=decision_time,
        config=config,
    )
    cutoff = decision_time - _INTERVAL
    features: dict[str, _Feature] = {}
    for symbol in eligible:
        price = _price_feature(bars.get(symbol), cutoff=cutoff, config=config)
        funding_value = funding.get(symbol)
        if price is None or funding_value is None:
            continue
        features[symbol] = _Feature(
            slow_trend=price.slow_trend,
            fast_trend=price.fast_trend,
            funding_per_day=funding_value,
            volatility=price.volatility,
        )
    retained = _retain_low_volatility(features, config)
    if retained is None:
        return {}
    slow_ranks = _average_ranks({symbol: features[symbol].slow_trend for symbol in retained})
    fast_ranks = _average_ranks({symbol: features[symbol].fast_trend for symbol in retained})
    funding_ranks = _average_ranks(
        {symbol: features[symbol].funding_per_day for symbol in retained}
    )
    if slow_ranks is None or fast_ranks is None or funding_ranks is None:
        return {}
    scores = {
        symbol: config.slow_weight * slow_ranks[symbol]
        + config.fast_weight * fast_ranks[symbol]
        - config.funding_weight * funding_ranks[symbol]
        for symbol in retained
    }
    sleeves = _select_sleeves(scores, config)
    if sleeves is None:
        return {}
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
        mean_long_slow - mean_short_slow <= config.epsilon
        or mean_short_funding - mean_long_funding <= config.epsilon
    ):
        return {}
    long_weights = _equal_allocation(long_symbols, config)
    short_weights = _equal_allocation(short_symbols, config)
    if long_weights is None or short_weights is None:
        return {}
    targets = {
        **{symbol: long_weights[symbol] for symbol in sorted(long_weights)},
        **{symbol: -short_weights[symbol] for symbol in sorted(short_weights)},
    }
    gross = math.fsum(abs(weight) for weight in targets.values())
    net = math.fsum(targets.values())
    if (
        gross > config.gross_target + config.tolerance
        or abs(net) > config.tolerance
        or any(
            symbol not in eligible or not math.isfinite(weight) or abs(weight) > config.symbol_cap
            for symbol, weight in targets.items()
        )
    ):
        return {}
    return targets


class UncrowdedTrendCarry:
    """Fresh deterministic instance of the exact UTC reference."""

    def __init__(self, config: _Config = _REFERENCE) -> None:
        self._config = config

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or seed != self._config.canonical_seed
        ):
            raise ValueError("team-04 UTC requires canonical runtime seed 20260718")
        decision_time = _utc_timestamp(getattr(context, "decision_time", None))
        decision_index = _decision_index(getattr(context, "decision_time", None))
        if decision_time is None or decision_index is None:
            return {}
        if decision_index % self._config.rebalance_bars:
            return None
        try:
            return _scheduled_targets(context, decision_time, self._config)
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError):
            return {}


def build_strategy() -> UncrowdedTrendCarry:
    """Return a fresh UTC reference strategy for the official worker."""

    return UncrowdedTrendCarry()
