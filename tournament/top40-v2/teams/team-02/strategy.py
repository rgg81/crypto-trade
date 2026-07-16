"""Funding Inventory Relaxation (FIR) exact no-control reference candidate."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

_EIGHT_HOURS = pd.Timedelta(hours=8)
_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


@dataclasses.dataclass(frozen=True)
class _Config:
    candidate_id: str = "team-02-fir-reference-001"
    canonical_seed: int = 20260801
    funding_window_days: int = 21
    recent_funding_days: int = 3
    minimum_prior_events: int = 18
    minimum_recent_events: int = 3
    maximum_funding_staleness_hours: int = 16
    maximum_absolute_funding_rate: float = 0.05
    level_weight: float = 0.75
    relaxation_weight: float = 0.25
    volatility_lookback_days: int = 30
    volatility_keep_numerator: int = 4
    volatility_keep_denominator: int = 5
    minimum_prefilter_cross_section: int = 30
    minimum_cross_section: int = 24
    selection_numerator: int = 1
    selection_denominator: int = 4
    minimum_sleeve_names: int = 6
    gross_target: float = 0.40
    side_budget: float = 0.20
    symbol_cap: float = 0.03
    rebalance_bars: int = 9
    epsilon: float = 1e-12
    tolerance: float = 1e-12

    @property
    def volatility_return_bars(self) -> int:
        return 3 * self.volatility_lookback_days

    @property
    def prior_funding_days(self) -> int:
        return self.funding_window_days - self.recent_funding_days


_REFERENCE = _Config()


@dataclasses.dataclass(frozen=True)
class _FundingFeature:
    level_per_day: float
    relaxation_per_day: float


@dataclasses.dataclass(frozen=True)
class _Feature:
    funding_level_per_day: float
    funding_relaxation_per_day: float
    realized_volatility: float


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
    if delta % _EIGHT_HOURS.value:
        return None
    return delta // _EIGHT_HOURS.value


def _average_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    """Return exact-equality average ranks mapped to [-1, 1]."""

    if len(values) < 2 or any(not math.isfinite(value) for value in values.values()):
        return None
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    denominator = len(ordered) - 1
    ranks: dict[str, float] = {}
    start = 0
    while start < len(ordered):
        stop = start + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[start][1]:
            stop += 1
        average_one_based = ((start + 1) + stop) / 2.0
        mapped = 2.0 * (average_one_based - 1.0) / denominator - 1.0
        for index in range(start, stop):
            ranks[ordered[index][0]] = mapped
        start = stop
    return ranks


def _expected_price_times(cutoff: pd.Timestamp, return_bars: int) -> tuple[pd.Timestamp, ...]:
    return tuple(cutoff - multiple * _EIGHT_HOURS for multiple in range(return_bars + 1, 0, -1))


def _realized_volatility(
    frame: Any,
    *,
    cutoff: pd.Timestamp,
    return_bars: int = _REFERENCE.volatility_return_bars,
) -> float | None:
    if not isinstance(frame, pd.DataFrame):
        return None
    required = ("open_time", "close_time", "close")
    if not set(required).issubset(frame.columns):
        return None
    expected = _expected_price_times(cutoff, return_bars)
    rows: dict[pd.Timestamp, list[tuple[Any, Any, Any]]] = {timestamp: [] for timestamp in expected}
    for raw_open, raw_close_time, raw_close in frame.loc[:, list(required)].itertuples(
        index=False, name=None
    ):
        open_time = _utc_timestamp(raw_open)
        if open_time is None or open_time not in rows:
            continue
        close_time = _utc_timestamp(raw_close_time)
        if close_time is None or close_time > cutoff:
            continue
        rows[open_time].append((raw_open, raw_close_time, raw_close))
    if any(len(rows[timestamp]) != 1 for timestamp in expected):
        return None
    closes: list[float] = []
    for timestamp in expected:
        close = _finite_number(rows[timestamp][0][2])
        if close is None or close <= 0.0:
            return None
        closes.append(close)
    returns: list[float] = []
    for previous, current in zip(closes[:-1], closes[1:], strict=True):
        ratio = current / previous
        if not math.isfinite(ratio) or ratio <= 0.0:
            return None
        value = math.log(ratio)
        if not math.isfinite(value):
            return None
        returns.append(value)
    if len(returns) != return_bars:
        return None
    mean = math.fsum(returns) / len(returns)
    variance = math.fsum((value - mean) ** 2 for value in returns) / len(returns)
    if not math.isfinite(variance) or variance < 0.0:
        return None
    result = math.sqrt(variance)
    return result if math.isfinite(result) else None


def _funding_features(
    frame: Any,
    *,
    eligible_symbols: Sequence[str],
    decision_time: pd.Timestamp,
    config: _Config = _REFERENCE,
) -> dict[str, _FundingFeature]:
    if not isinstance(frame, pd.DataFrame):
        return {}
    required = ("funding_time", "symbol", "funding_rate")
    if not set(required).issubset(frame.columns):
        return {}
    eligible = frozenset(eligible_symbols)
    window_start = decision_time - pd.Timedelta(days=config.funding_window_days)
    recent_start = decision_time - pd.Timedelta(days=config.recent_funding_days)
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
        if timestamp < window_start or timestamp >= decision_time:
            continue
        rate = _finite_number(raw_rate)
        if rate is None or abs(rate) > config.maximum_absolute_funding_rate:
            invalid.add(raw_symbol)
            continue
        observed[raw_symbol].append((timestamp, rate))

    result: dict[str, _FundingFeature] = {}
    for symbol in sorted(eligible):
        if symbol in invalid:
            continue
        events = sorted(observed[symbol], key=lambda item: item[0])
        timestamps = [timestamp for timestamp, _rate in events]
        if len(timestamps) != len(set(timestamps)) or not events:
            continue
        prior = [rate for timestamp, rate in events if timestamp < recent_start]
        recent = [rate for timestamp, rate in events if timestamp >= recent_start]
        if (
            len(prior) < config.minimum_prior_events
            or len(recent) < config.minimum_recent_events
            or decision_time - events[-1][0]
            > pd.Timedelta(hours=config.maximum_funding_staleness_hours)
        ):
            continue
        prior_daily = math.fsum(prior) / config.prior_funding_days
        recent_daily = math.fsum(recent) / config.recent_funding_days
        level_daily = math.fsum(rate for _timestamp, rate in events) / config.funding_window_days
        relaxation = recent_daily - prior_daily
        if all(math.isfinite(value) for value in (level_daily, relaxation)):
            result[symbol] = _FundingFeature(level_daily, relaxation)
    return result


def _lowest_volatility_symbols(
    volatility: Mapping[str, float], config: _Config = _REFERENCE
) -> tuple[str, ...] | None:
    if len(volatility) < config.minimum_prefilter_cross_section:
        return None
    if any(not math.isfinite(value) or value < 0.0 for value in volatility.values()):
        return None
    keep = (config.volatility_keep_numerator * len(volatility)) // (
        config.volatility_keep_denominator
    )
    if keep < config.minimum_cross_section:
        return None
    ordered = sorted(volatility, key=lambda symbol: (volatility[symbol], symbol))
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


def _equal_side_allocation(
    symbols: Sequence[str], config: _Config = _REFERENCE
) -> dict[str, float] | None:
    ordered = tuple(sorted(symbols))
    if not ordered:
        return None
    effective_budget = min(config.side_budget, len(ordered) * config.symbol_cap)
    initial = effective_budget / len(ordered)
    if not math.isfinite(initial) or initial < 0.0 or initial > config.symbol_cap:
        return None
    weights = {symbol: initial for symbol in ordered}
    residual = effective_budget - math.fsum(weights.values())
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
    if abs(math.fsum(weights.values()) - effective_budget) > config.tolerance:
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
    funding = _funding_features(
        getattr(context, "funding", None),
        eligible_symbols=eligible,
        decision_time=decision_time,
        config=config,
    )
    cutoff = decision_time - _EIGHT_HOURS
    features: dict[str, _Feature] = {}
    for symbol in eligible:
        funding_feature = funding.get(symbol)
        if funding_feature is None:
            continue
        volatility = _realized_volatility(
            bars.get(symbol),
            cutoff=cutoff,
            return_bars=config.volatility_return_bars,
        )
        if volatility is None:
            continue
        features[symbol] = _Feature(
            funding_level_per_day=funding_feature.level_per_day,
            funding_relaxation_per_day=funding_feature.relaxation_per_day,
            realized_volatility=volatility,
        )
    retained = _lowest_volatility_symbols(
        {symbol: feature.realized_volatility for symbol, feature in features.items()},
        config,
    )
    if retained is None:
        return {}
    level_ranks = _average_ranks(
        {symbol: features[symbol].funding_level_per_day for symbol in retained}
    )
    relaxation_ranks = _average_ranks(
        {symbol: features[symbol].funding_relaxation_per_day for symbol in retained}
    )
    if level_ranks is None or relaxation_ranks is None:
        return {}
    scores = {
        symbol: -config.level_weight * level_ranks[symbol]
        + config.relaxation_weight * relaxation_ranks[symbol]
        for symbol in retained
    }
    sleeves = _select_sleeves(scores, config)
    if sleeves is None:
        return {}
    long_symbols, short_symbols = sleeves
    long_level = math.fsum(features[symbol].funding_level_per_day for symbol in long_symbols) / len(
        long_symbols
    )
    short_level = math.fsum(
        features[symbol].funding_level_per_day for symbol in short_symbols
    ) / len(short_symbols)
    if not math.isfinite(long_level) or not math.isfinite(short_level):
        return {}
    if short_level - long_level <= config.epsilon:
        return {}
    long_weights = _equal_side_allocation(long_symbols, config)
    short_weights = _equal_side_allocation(short_symbols, config)
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


class FundingInventoryRelaxation:
    """Fresh deterministic instance of the exact FIR no-control reference."""

    def __init__(self, config: _Config = _REFERENCE) -> None:
        self._config = config

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or seed != self._config.canonical_seed
        ):
            raise ValueError("team-02 FIR requires canonical runtime seed 20260801")
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


def build_strategy() -> FundingInventoryRelaxation:
    """Return a fresh FIR reference strategy for the official worker."""

    return FundingInventoryRelaxation()
