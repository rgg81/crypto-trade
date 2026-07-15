"""Causal Crowding-Conditioned Residual Persistence (C3RP) baseline.

The strategy consumes only the past-only ``DecisionContext`` supplied by the V2 worker.  It
returns target weights; execution, costs, funding cashflows, positions, and risk state remain
central-engine responsibilities.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

_EIGHT_HOURS = pd.Timedelta(hours=8)
_DAY = pd.Timedelta(days=1)
_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


@dataclasses.dataclass(frozen=True)
class _Config:
    canonical_seed: int = 20260801
    beta_days: int = 20
    slow_days: int = 20
    fast_days: int = 10
    reversal_days: int = 2
    volatility_days: int = 20
    funding_days: int = 7
    slow_weight: float = 0.65
    fast_weight: float = 0.35
    funding_weight: float = 0.20
    theta_efficiency: float = 0.30
    theta_breadth: float = 0.30
    transition_width: float = 0.15
    selection_numerator: int = 1
    selection_denominator: int = 4
    gross: float = 0.90
    maximum_side_tilt: float = 0.0
    direction_scale: float = 1.5
    rebalance_bars: int = 3
    valid_history_numerator: int = 4
    valid_history_denominator: int = 5
    minimum_cross_section: int = 12
    minimum_sleeve_names: int = 4
    minimum_funding_events: int = 2
    minimum_funding_symbols: int = 4
    beta_minimum: float = -1.0
    beta_maximum: float = 3.0
    volatility_quantile_low: float = 0.10
    volatility_quantile_high: float = 0.90
    symbol_cap: float = 0.095
    epsilon: float = 1e-12
    weight_tolerance: float = 1e-12

    @property
    def beta_bars(self) -> int:
        return 3 * self.beta_days

    @property
    def slow_bars(self) -> int:
        return 3 * self.slow_days

    @property
    def fast_bars(self) -> int:
        return 3 * self.fast_days

    @property
    def reversal_bars(self) -> int:
        return 3 * self.reversal_days

    @property
    def volatility_bars(self) -> int:
        return 3 * self.volatility_days

    @property
    def maximum_return_bars(self) -> int:
        return max(
            self.beta_bars,
            self.slow_bars,
            self.fast_bars,
            self.reversal_bars,
            self.volatility_bars,
        )


_BASELINE = _Config()


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


def _decision_index(decision_time: Any) -> int | None:
    timestamp = _utc_timestamp(decision_time)
    if timestamp is None:
        return None
    delta = timestamp.value - _EPOCH.value
    interval = _EIGHT_HOURS.value
    if delta % interval:
        return None
    return delta // interval


def _population_mean(values: Sequence[float]) -> float:
    return math.fsum(values) / len(values)


def _population_variance(values: Sequence[float]) -> float:
    mean = _population_mean(values)
    return math.fsum((value - mean) * (value - mean) for value in values) / len(values)


def _population_covariance(left: Sequence[float], right: Sequence[float]) -> float:
    left_mean = _population_mean(left)
    right_mean = _population_mean(right)
    return math.fsum(
        (left_value - left_mean) * (right_value - right_mean)
        for left_value, right_value in zip(left, right, strict=True)
    ) / len(left)


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return math.fsum((ordered[middle - 1], ordered[middle])) / 2.0


def _average_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    """Exact-equality average ranks mapped to [-1, 1]."""
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
        average_one_based_rank = ((start + 1) + stop) / 2.0
        mapped = 2.0 * (average_one_based_rank - 1.0) / denominator - 1.0
        for index in range(start, stop):
            result[ordered[index][0]] = mapped
        start = stop
    return result


def _type7_quantile(values: Sequence[float], probability: float) -> float:
    ordered = sorted(values)
    location = (len(ordered) - 1) * probability
    lower = math.floor(location)
    fraction = location - lower
    upper = min(lower + 1, len(ordered) - 1)
    return (1.0 - fraction) * ordered[lower] + fraction * ordered[upper]


def _state_probability(
    efficiency_ratio: float, breadth: float, config: _Config = _BASELINE
) -> float:
    state_input = (efficiency_ratio - config.theta_efficiency) / config.transition_width + (
        breadth - config.theta_breadth
    ) / config.transition_width
    clipped = min(40.0, max(-40.0, state_input))
    return 1.0 / (1.0 + math.exp(-clipped))


def _state_blend(
    trend_rank: float,
    reversal_rank: float,
    funding_rank: float,
    persistence_probability: float,
    config: _Config = _BASELINE,
) -> float:
    return (1.0 - config.funding_weight) * (
        persistence_probability * trend_rank + (1.0 - persistence_probability) * reversal_rank
    ) + config.funding_weight * funding_rank


def _expected_return_times(cutoff: pd.Timestamp, count: int) -> tuple[pd.Timestamp, ...]:
    return tuple(cutoff - multiple * _EIGHT_HOURS for multiple in range(count, 0, -1))


def _symbol_returns(
    frame: Any,
    *,
    cutoff: pd.Timestamp,
    expected_times: Sequence[pd.Timestamp],
) -> dict[pd.Timestamp, float | None]:
    """Build exact-grid close-to-close returns without shortening a missing slot."""
    result = {timestamp: None for timestamp in expected_times}
    if not isinstance(frame, pd.DataFrame):
        return result
    required = {"open_time", "close_time", "close"}
    if not required.issubset(frame.columns):
        return result

    expected_prices = {timestamp - _EIGHT_HOURS for timestamp in expected_times}
    expected_prices.update(expected_times)
    rows_by_open: dict[pd.Timestamp, list[float | None]] = {
        timestamp: [] for timestamp in expected_prices
    }
    for raw_open, raw_close_time, raw_close in frame.loc[
        :, ["open_time", "close_time", "close"]
    ].itertuples(index=False, name=None):
        open_time = _utc_timestamp(raw_open)
        close_time = _utc_timestamp(raw_close_time)
        if open_time is None or close_time is None or close_time > cutoff:
            continue
        if open_time not in rows_by_open:
            continue
        close = _finite_number(raw_close)
        if close is None or close <= 0.0:
            rows_by_open[open_time].append(None)
        else:
            rows_by_open[open_time].append(close)

    prices: dict[pd.Timestamp, float | None] = {}
    for timestamp in expected_prices:
        candidates = rows_by_open[timestamp]
        prices[timestamp] = candidates[0] if len(candidates) == 1 else None

    for timestamp in expected_times:
        later = prices[timestamp]
        prior = prices[timestamp - _EIGHT_HOURS]
        if later is None or prior is None:
            continue
        ratio = later / prior
        if not math.isfinite(ratio) or ratio <= 0.0:
            continue
        value = math.log(ratio)
        if math.isfinite(value):
            result[timestamp] = value
    return result


def _minimum_valid_count(window: int, config: _Config) -> int:
    numerator = config.valid_history_numerator * window
    denominator = config.valid_history_denominator
    return max(2, (numerator + denominator - 1) // denominator)


def _complete_window(
    series: Mapping[pd.Timestamp, float | None], times: Sequence[pd.Timestamp]
) -> list[float] | None:
    values = [series.get(timestamp) for timestamp in times]
    if any(value is None for value in values):
        return None
    return [float(value) for value in values if value is not None]


def _estimate_beta(
    symbol_returns: Mapping[pd.Timestamp, float | None],
    common_returns: Mapping[pd.Timestamp, float | None],
    times: Sequence[pd.Timestamp],
    config: _Config,
) -> float | None:
    paired = [(symbol_returns.get(timestamp), common_returns.get(timestamp)) for timestamp in times]
    valid = [
        (float(symbol), float(common))
        for symbol, common in paired
        if symbol is not None and common is not None
    ]
    if len(valid) < _minimum_valid_count(len(times), config):
        return None
    symbol_values = [item[0] for item in valid]
    common_values = [item[1] for item in valid]
    variance = _population_variance(common_values)
    if not math.isfinite(variance) or variance <= config.epsilon:
        return None
    beta = _population_covariance(symbol_values, common_values) / variance
    if not math.isfinite(beta):
        return None
    return min(config.beta_maximum, max(config.beta_minimum, beta))


def _estimate_symbol_volatility(
    symbol_returns: Mapping[pd.Timestamp, float | None],
    times: Sequence[pd.Timestamp],
    config: _Config,
) -> float | None:
    values = [symbol_returns.get(timestamp) for timestamp in times]
    valid = [float(value) for value in values if value is not None]
    if len(valid) < _minimum_valid_count(len(times), config):
        return None
    variance = _population_variance(valid)
    if not math.isfinite(variance) or variance < 0.0:
        return None
    volatility = math.sqrt(variance)
    if not math.isfinite(volatility) or volatility <= config.epsilon:
        return None
    return volatility


def _residual_displacement(
    symbol_returns: Mapping[pd.Timestamp, float | None],
    common_returns: Mapping[pd.Timestamp, float | None],
    times: Sequence[pd.Timestamp],
    *,
    beta: float,
    volatility: float,
    epsilon: float,
) -> float | None:
    symbol_window = _complete_window(symbol_returns, times)
    common_window = _complete_window(common_returns, times)
    if symbol_window is None or common_window is None:
        return None
    numerator = math.fsum(symbol_window) - beta * math.fsum(common_window)
    denominator = volatility * math.sqrt(len(times)) + epsilon
    result = numerator / denominator
    return result if math.isfinite(result) else None


def _funding_ranks(
    funding: Any,
    eligible_symbols: Sequence[str],
    cutoff: pd.Timestamp,
    config: _Config = _BASELINE,
) -> dict[str, float]:
    neutral = {symbol: 0.0 for symbol in eligible_symbols}
    if not isinstance(funding, pd.DataFrame):
        return neutral
    required = {"symbol", "funding_time", "funding_rate"}
    if not required.issubset(funding.columns):
        return neutral
    eligible = set(eligible_symbols)
    left_boundary = cutoff - config.funding_days * _DAY
    valid_rows: dict[str, list[tuple[pd.Timestamp, float]]] = {
        symbol: [] for symbol in eligible_symbols
    }
    seen_events: dict[str, set[pd.Timestamp]] = {symbol: set() for symbol in eligible_symbols}
    invalid_symbols: set[str] = set()
    for raw_symbol, raw_time, raw_rate in funding.loc[
        :, ["symbol", "funding_time", "funding_rate"]
    ].itertuples(index=False, name=None):
        if not isinstance(raw_symbol, str) or raw_symbol not in eligible:
            continue
        funding_time = _utc_timestamp(raw_time)
        if funding_time is None or not left_boundary < funding_time <= cutoff:
            continue
        if funding_time in seen_events[raw_symbol]:
            invalid_symbols.add(raw_symbol)
            continue
        seen_events[raw_symbol].add(funding_time)
        rate = _finite_number(raw_rate)
        if rate is None:
            invalid_symbols.add(raw_symbol)
            continue
        valid_rows[raw_symbol].append((funding_time, rate))

    cumulative_funding: dict[str, float] = {}
    for symbol in eligible_symbols:
        if symbol in invalid_symbols:
            continue
        rows = sorted(valid_rows[symbol], key=lambda item: item[0])
        if len(rows) < config.minimum_funding_events:
            continue
        value = math.fsum(row[1] for row in rows)
        if math.isfinite(value):
            cumulative_funding[symbol] = value
    if len(cumulative_funding) < config.minimum_funding_symbols:
        return neutral
    ranked = _average_ranks({symbol: -value for symbol, value in cumulative_funding.items()})
    if ranked is None:
        return neutral
    neutral.update(ranked)
    return neutral


def _select_sleeves(
    alpha_ranks: Mapping[str, float], config: _Config = _BASELINE
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    count = len(alpha_ranks)
    if count < config.minimum_cross_section:
        return None
    selected_count = max(
        config.minimum_sleeve_names,
        (config.selection_numerator * count) // config.selection_denominator,
    )
    if 2 * selected_count > count:
        return None
    ordered = sorted(alpha_ranks, key=lambda symbol: (alpha_ranks[symbol], symbol))
    shorts = tuple(ordered[:selected_count])
    longs = tuple(ordered[-selected_count:])
    return longs, shorts


def _capped_inverse_volatility_weights(
    symbols: Sequence[str],
    clipped_volatility: Mapping[str, float],
    requested_budget: float,
    config: _Config = _BASELINE,
) -> dict[str, float] | None:
    ordered_symbols = tuple(sorted(symbols))
    if not ordered_symbols or not math.isfinite(requested_budget) or requested_budget < 0.0:
        return None
    scores: dict[str, float] = {}
    for symbol in ordered_symbols:
        volatility = clipped_volatility.get(symbol)
        if volatility is None or not math.isfinite(volatility) or volatility <= 0.0:
            return None
        score = 1.0 / volatility
        if not math.isfinite(score) or score <= 0.0:
            return None
        scores[symbol] = score

    effective_budget = min(requested_budget, len(ordered_symbols) * config.symbol_cap)
    weights = {symbol: 0.0 for symbol in ordered_symbols}
    active = list(ordered_symbols)
    remaining = effective_budget
    while active:
        denominator = math.fsum(scores[symbol] for symbol in active)
        if remaining > config.weight_tolerance and (
            not math.isfinite(denominator) or denominator <= 0.0
        ):
            return None
        if denominator <= 0.0:
            break
        proposals = {symbol: remaining * scores[symbol] / denominator for symbol in active}
        capped = [
            symbol
            for symbol in active
            if proposals[symbol] >= config.symbol_cap - config.weight_tolerance
        ]
        if not capped:
            for symbol in active:
                weights[symbol] = proposals[symbol]
            remaining = 0.0
            break
        for symbol in capped:
            weights[symbol] = config.symbol_cap
        remaining -= len(capped) * config.symbol_cap
        capped_set = set(capped)
        active = [symbol for symbol in active if symbol not in capped_set]
        if remaining <= config.weight_tolerance or not active:
            break

    for value in weights.values():
        if value < -config.weight_tolerance or value > config.symbol_cap + config.weight_tolerance:
            return None
    for symbol in ordered_symbols:
        weights[symbol] = min(config.symbol_cap, max(0.0, weights[symbol]))

    delta = effective_budget - math.fsum(weights[symbol] for symbol in ordered_symbols)
    if delta > config.weight_tolerance:
        for symbol in sorted(
            ordered_symbols,
            key=lambda item: (-(config.symbol_cap - weights[item]), item),
        ):
            addition = min(delta, config.symbol_cap - weights[symbol])
            weights[symbol] += addition
            delta -= addition
            if abs(delta) <= config.weight_tolerance:
                break
    elif delta < -config.weight_tolerance:
        for symbol in sorted(ordered_symbols, key=lambda item: (-weights[item], item)):
            subtraction = min(-delta, weights[symbol])
            weights[symbol] -= subtraction
            delta += subtraction
            if abs(delta) <= config.weight_tolerance:
                break

    if abs(delta) > config.weight_tolerance:
        return None
    if any(
        not math.isfinite(value) or value < 0.0 or value > config.symbol_cap
        for value in weights.values()
    ):
        return None
    if (
        abs(math.fsum(weights[symbol] for symbol in ordered_symbols) - effective_budget)
        > config.weight_tolerance
    ):
        return None
    return weights


def _target_for_scheduled_decision(
    context: Any, decision_time: pd.Timestamp, config: _Config
) -> dict[str, float]:
    raw_eligible = getattr(context, "eligible_symbols", ())
    if isinstance(raw_eligible, (str, bytes)):
        return {}
    try:
        eligible_input = tuple(raw_eligible)
    except TypeError:
        return {}
    if any(not isinstance(symbol, str) or not symbol for symbol in eligible_input) or len(
        eligible_input
    ) != len(set(eligible_input)):
        return {}
    eligible_symbols = tuple(sorted(eligible_input))
    if len(eligible_symbols) < config.minimum_cross_section:
        return {}
    bars = getattr(context, "bars", None)
    if not isinstance(bars, Mapping):
        return {}

    cutoff = decision_time - _EIGHT_HOURS
    expected_times = _expected_return_times(cutoff, config.maximum_return_bars)
    returns_by_symbol = {
        symbol: _symbol_returns(bars.get(symbol), cutoff=cutoff, expected_times=expected_times)
        for symbol in eligible_symbols
    }

    common_returns: dict[pd.Timestamp, float | None] = {}
    for timestamp in expected_times:
        values = [
            returns_by_symbol[symbol][timestamp]
            for symbol in eligible_symbols
            if returns_by_symbol[symbol][timestamp] is not None
        ]
        common_returns[timestamp] = (
            _median([float(value) for value in values if value is not None])
            if len(values) >= config.minimum_cross_section
            else None
        )

    beta_times = expected_times[-config.beta_bars :]
    volatility_times = expected_times[-config.volatility_bars :]
    slow_times = expected_times[-config.slow_bars :]
    fast_times = expected_times[-config.fast_bars :]
    reversal_times = expected_times[-config.reversal_bars :]
    common_slow = _complete_window(common_returns, slow_times)
    if common_slow is None:
        return {}

    breadth_sums = [
        math.fsum(values)
        for symbol in eligible_symbols
        if (values := _complete_window(returns_by_symbol[symbol], slow_times)) is not None
    ]
    if len(breadth_sums) < config.minimum_cross_section:
        return {}
    positive_fraction = sum(value > 0.0 for value in breadth_sums) / len(breadth_sums)
    breadth = abs(2.0 * positive_fraction - 1.0)
    common_sum = math.fsum(common_slow)
    efficiency_ratio = abs(common_sum) / (
        math.fsum(abs(value) for value in common_slow) + config.epsilon
    )
    persistence_probability = _state_probability(efficiency_ratio, breadth, config)
    common_variance = _population_variance(common_slow)
    if not math.isfinite(common_variance) or common_variance < 0.0:
        return {}
    common_volatility = math.sqrt(common_variance)
    direction_z = common_sum / (common_volatility * math.sqrt(config.slow_bars) + config.epsilon)
    direction = math.tanh(min(20.0, max(-20.0, direction_z / config.direction_scale)))

    trend_raw: dict[str, float] = {}
    reversal_raw: dict[str, float] = {}
    volatilities: dict[str, float] = {}
    for symbol in eligible_symbols:
        symbol_returns = returns_by_symbol[symbol]
        beta = _estimate_beta(symbol_returns, common_returns, beta_times, config)
        volatility = _estimate_symbol_volatility(symbol_returns, volatility_times, config)
        if beta is None or volatility is None:
            continue
        slow = _residual_displacement(
            symbol_returns,
            common_returns,
            slow_times,
            beta=beta,
            volatility=volatility,
            epsilon=config.epsilon,
        )
        fast = _residual_displacement(
            symbol_returns,
            common_returns,
            fast_times,
            beta=beta,
            volatility=volatility,
            epsilon=config.epsilon,
        )
        reversal = _residual_displacement(
            symbol_returns,
            common_returns,
            reversal_times,
            beta=beta,
            volatility=volatility,
            epsilon=config.epsilon,
        )
        if slow is None or fast is None or reversal is None:
            continue
        trend_value = config.slow_weight * slow + config.fast_weight * fast
        reversal_value = -reversal
        if not math.isfinite(trend_value) or not math.isfinite(reversal_value):
            continue
        trend_raw[symbol] = trend_value
        reversal_raw[symbol] = reversal_value
        volatilities[symbol] = volatility

    if len(trend_raw) < config.minimum_cross_section:
        return {}
    trend_ranks = _average_ranks(trend_raw)
    reversal_ranks = _average_ranks(reversal_raw)
    if trend_ranks is None or reversal_ranks is None:
        return {}
    funding_ranks = _funding_ranks(
        getattr(context, "funding", None), eligible_symbols, cutoff, config
    )
    alpha_raw = {
        symbol: _state_blend(
            trend_ranks[symbol],
            reversal_ranks[symbol],
            funding_ranks[symbol],
            persistence_probability,
            config,
        )
        for symbol in trend_ranks
    }
    alpha_ranks = _average_ranks(alpha_raw)
    if alpha_ranks is None:
        return {}
    sleeves = _select_sleeves(alpha_ranks, config)
    if sleeves is None:
        return {}
    long_symbols, short_symbols = sleeves

    all_volatilities = [volatilities[symbol] for symbol in alpha_ranks]
    low = _type7_quantile(all_volatilities, config.volatility_quantile_low)
    high = _type7_quantile(all_volatilities, config.volatility_quantile_high)
    if not math.isfinite(low) or not math.isfinite(high) or low <= 0.0 or high < low:
        return {}
    clipped = {symbol: min(high, max(low, volatilities[symbol])) for symbol in alpha_ranks}
    long_budget = config.gross / 2.0 + config.maximum_side_tilt * direction
    short_budget = config.gross / 2.0 - config.maximum_side_tilt * direction
    long_weights = _capped_inverse_volatility_weights(long_symbols, clipped, long_budget, config)
    short_weights = _capped_inverse_volatility_weights(short_symbols, clipped, short_budget, config)
    if long_weights is None or short_weights is None:
        return {}

    targets: dict[str, float] = {}
    for symbol in sorted(long_weights):
        targets[symbol] = long_weights[symbol]
    for symbol in sorted(short_weights):
        targets[symbol] = -short_weights[symbol] if short_weights[symbol] else 0.0
    if any(
        symbol not in eligible_symbols
        or not math.isfinite(weight)
        or abs(weight) > config.symbol_cap
        for symbol, weight in targets.items()
    ):
        return {}
    return targets


class CausalCrowdingResidualPersistence:
    """Fresh, deterministic C3RP baseline instance."""

    def __init__(self, config: _Config = _BASELINE) -> None:
        self._config = config

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or seed != self._config.canonical_seed
        ):
            raise ValueError("team-02 requires canonical runtime seed 20260801")
        decision_time = _utc_timestamp(getattr(context, "decision_time", None))
        decision_index = _decision_index(getattr(context, "decision_time", None))
        if decision_time is None or decision_index is None:
            return {}
        if decision_index % self._config.rebalance_bars:
            return None
        try:
            return _target_for_scheduled_decision(context, decision_time, self._config)
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError):
            return {}


def build_strategy() -> CausalCrowdingResidualPersistence:
    """Return a fresh baseline strategy object for the official worker."""
    return CausalCrowdingResidualPersistence()
