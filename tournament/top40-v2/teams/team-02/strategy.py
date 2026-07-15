"""Directional Auction Absorption (DAA) exact no-control reference candidate."""

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
    candidate_id: str = "team-02-daa-reference-001"
    canonical_seed: int = 20260801
    trend_efficiency_days: int = 12
    absorption_window_bars: int = 3
    absorption_half_life_bars: float = 2.0
    trend_weight: float = 0.60
    absorption_weight: float = 0.40
    minimum_cross_section: int = 24
    selection_numerator: int = 1
    selection_denominator: int = 4
    minimum_sleeve_names: int = 6
    gross_target: float = 0.80
    side_budget: float = 0.40
    symbol_cap: float = 0.06
    rebalance_bars: int = 3
    epsilon: float = 1e-12
    tolerance: float = 1e-12

    @property
    def trend_return_bars(self) -> int:
        return 3 * self.trend_efficiency_days


_REFERENCE = _Config()


@dataclasses.dataclass(frozen=True)
class _Features:
    path_efficiency: float
    absorption: float


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
    interval = _EIGHT_HOURS.value
    if delta % interval:
        return None
    return delta // interval


def _average_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    """Return exact-equality average ranks mapped to [-1, 1]."""
    if len(values) < 2 or any(not math.isfinite(value) for value in values.values()):
        return None
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    denominator = len(ordered) - 1
    ranked: dict[str, float] = {}
    start = 0
    while start < len(ordered):
        stop = start + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[start][1]:
            stop += 1
        average_one_based_rank = ((start + 1) + stop) / 2.0
        mapped = 2.0 * (average_one_based_rank - 1.0) / denominator - 1.0
        for index in range(start, stop):
            ranked[ordered[index][0]] = mapped
        start = stop
    return ranked


def _path_efficiency(closes: Sequence[float], epsilon: float = _REFERENCE.epsilon) -> float | None:
    if len(closes) < 2 or any(not math.isfinite(value) or value <= 0.0 for value in closes):
        return None
    returns: list[float] = []
    for previous, current in zip(closes[:-1], closes[1:], strict=True):
        ratio = current / previous
        if not math.isfinite(ratio) or ratio <= 0.0:
            return None
        value = math.log(ratio)
        if not math.isfinite(value):
            return None
        returns.append(value)
    denominator = math.fsum(abs(value) for value in returns) + epsilon
    result = math.fsum(returns) / denominator
    return result if math.isfinite(result) else None


def _absorption_gap(
    *,
    open_price: Any,
    high: Any,
    low: Any,
    close: Any,
    quote_volume: Any,
    taker_buy_quote_volume: Any,
    epsilon: float = _REFERENCE.epsilon,
) -> float | None:
    open_value = _finite_number(open_price)
    high_value = _finite_number(high)
    low_value = _finite_number(low)
    close_value = _finite_number(close)
    quote_value = _finite_number(quote_volume)
    taker_value = _finite_number(taker_buy_quote_volume)
    if any(
        value is None or value <= 0.0 for value in (open_value, high_value, low_value, close_value)
    ):
        return None
    assert open_value is not None
    assert high_value is not None
    assert low_value is not None
    assert close_value is not None
    if not low_value <= open_value <= high_value or not low_value <= close_value <= high_value:
        return None
    price_range = high_value - low_value
    minimum_range = epsilon * max(1.0, abs(high_value), abs(low_value))
    if not math.isfinite(price_range) or price_range <= minimum_range:
        return None
    if (
        quote_value is None
        or taker_value is None
        or quote_value <= epsilon
        or taker_value < 0.0
        or taker_value > quote_value
    ):
        return None
    flow = 2.0 * taker_value / quote_value - 1.0
    closing_location = (2.0 * close_value - high_value - low_value) / price_range
    if not math.isfinite(flow) or not math.isfinite(closing_location):
        return None
    closing_location = min(1.0, max(-1.0, closing_location))
    gap = (closing_location - flow) / 2.0
    return gap if math.isfinite(gap) else None


def _smooth_absorption(
    gaps_oldest_to_newest: Sequence[float],
    half_life_bars: float = _REFERENCE.absorption_half_life_bars,
) -> float | None:
    if (
        not gaps_oldest_to_newest
        or not math.isfinite(half_life_bars)
        or half_life_bars <= 0.0
        or any(not math.isfinite(value) for value in gaps_oldest_to_newest)
    ):
        return None
    count = len(gaps_oldest_to_newest)
    raw_weights = [math.pow(2.0, -(count - 1 - index) / half_life_bars) for index in range(count)]
    weight_sum = math.fsum(raw_weights)
    if not math.isfinite(weight_sum) or weight_sum <= 0.0:
        return None
    result = math.fsum(
        (raw_weight / weight_sum) * gap
        for raw_weight, gap in zip(raw_weights, gaps_oldest_to_newest, strict=True)
    )
    return result if math.isfinite(result) else None


def _expected_price_times(cutoff: pd.Timestamp, return_bars: int) -> tuple[pd.Timestamp, ...]:
    return tuple(cutoff - multiple * _EIGHT_HOURS for multiple in range(return_bars + 1, 0, -1))


def _available_rows(
    frame: Any,
    *,
    cutoff: pd.Timestamp,
    expected_times: Sequence[pd.Timestamp],
) -> dict[pd.Timestamp, list[tuple[Any, ...]]]:
    rows = {timestamp: [] for timestamp in expected_times}
    if not isinstance(frame, pd.DataFrame):
        return rows
    columns = (
        "open_time",
        "close_time",
        "open",
        "high",
        "low",
        "close",
        "quote_volume",
        "taker_buy_quote_volume",
    )
    if not set(columns).issubset(frame.columns):
        return rows
    for raw_row in frame.loc[:, list(columns)].itertuples(index=False, name=None):
        open_time = _utc_timestamp(raw_row[0])
        if open_time is None or open_time not in rows:
            continue
        close_time = _utc_timestamp(raw_row[1])
        if close_time is not None and close_time > cutoff:
            continue
        rows[open_time].append(raw_row)
    return rows


def _symbol_features(
    frame: Any, cutoff: pd.Timestamp, config: _Config = _REFERENCE
) -> _Features | None:
    price_times = _expected_price_times(cutoff, config.trend_return_bars)
    rows = _available_rows(frame, cutoff=cutoff, expected_times=price_times)
    if any(len(rows[timestamp]) != 1 for timestamp in price_times):
        return None

    closes: list[float] = []
    for timestamp in price_times:
        row = rows[timestamp][0]
        close_time = _utc_timestamp(row[1])
        close = _finite_number(row[5])
        if close_time is None or close_time > cutoff or close is None or close <= 0.0:
            return None
        closes.append(close)
    efficiency = _path_efficiency(closes, config.epsilon)
    if efficiency is None:
        return None

    absorption_times = price_times[-config.absorption_window_bars :]
    gaps: list[float] = []
    for timestamp in absorption_times:
        row = rows[timestamp][0]
        gap = _absorption_gap(
            open_price=row[2],
            high=row[3],
            low=row[4],
            close=row[5],
            quote_volume=row[6],
            taker_buy_quote_volume=row[7],
            epsilon=config.epsilon,
        )
        if gap is None:
            return None
        gaps.append(gap)
    absorption = _smooth_absorption(gaps, config.absorption_half_life_bars)
    if absorption is None:
        return None
    return _Features(path_efficiency=efficiency, absorption=absorption)


def _select_sleeves(
    scores: Mapping[str, float], config: _Config = _REFERENCE
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    count = len(scores)
    if count < config.minimum_cross_section:
        return None
    sleeve_count = max(
        config.minimum_sleeve_names,
        (config.selection_numerator * count) // config.selection_denominator,
    )
    if 2 * sleeve_count > count:
        return None
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    shorts = tuple(ordered[:sleeve_count])
    longs = tuple(ordered[-sleeve_count:])
    return longs, shorts


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
    delta = effective_budget - math.fsum(weights[symbol] for symbol in ordered)
    if delta > 0.0:
        for symbol in ordered:
            addition = min(delta, config.symbol_cap - weights[symbol])
            weights[symbol] += addition
            delta -= addition
            if delta == 0.0:
                break
    elif delta < 0.0:
        for symbol in ordered:
            subtraction = min(-delta, weights[symbol])
            weights[symbol] -= subtraction
            delta += subtraction
            if delta == 0.0:
                break
    if abs(delta) > config.tolerance:
        return None
    if any(
        not math.isfinite(value) or value < 0.0 or value > config.symbol_cap
        for value in weights.values()
    ):
        return None
    if abs(math.fsum(weights[symbol] for symbol in ordered) - effective_budget) > config.tolerance:
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
    if any(not isinstance(symbol, str) or not symbol for symbol in eligible_input) or len(
        eligible_input
    ) != len(set(eligible_input)):
        return {}
    eligible = tuple(sorted(eligible_input))
    if len(eligible) < config.minimum_cross_section:
        return {}
    bars = getattr(context, "bars", None)
    if not isinstance(bars, Mapping):
        return {}

    cutoff = decision_time - _EIGHT_HOURS
    features: dict[str, _Features] = {}
    for symbol in eligible:
        feature = _symbol_features(bars.get(symbol), cutoff, config)
        if feature is not None:
            features[symbol] = feature
    if len(features) < config.minimum_cross_section:
        return {}

    trend_ranks = _average_ranks(
        {symbol: feature.path_efficiency for symbol, feature in features.items()}
    )
    absorption_ranks = _average_ranks(
        {symbol: feature.absorption for symbol, feature in features.items()}
    )
    if trend_ranks is None or absorption_ranks is None:
        return {}
    scores = {
        symbol: config.trend_weight * trend_ranks[symbol]
        + config.absorption_weight * absorption_ranks[symbol]
        for symbol in features
    }
    if any(not math.isfinite(value) for value in scores.values()):
        return {}
    sleeves = _select_sleeves(scores, config)
    if sleeves is None:
        return {}
    long_symbols, short_symbols = sleeves
    long_weights = _equal_side_allocation(long_symbols, config)
    short_weights = _equal_side_allocation(short_symbols, config)
    if long_weights is None or short_weights is None:
        return {}

    targets: dict[str, float] = {}
    for symbol in sorted(long_weights):
        targets[symbol] = long_weights[symbol]
    for symbol in sorted(short_weights):
        targets[symbol] = -short_weights[symbol] if short_weights[symbol] else 0.0
    if any(
        symbol not in eligible or not math.isfinite(weight) or abs(weight) > config.symbol_cap
        for symbol, weight in targets.items()
    ):
        return {}
    return targets


class DirectionalAuctionAbsorption:
    """Fresh deterministic instance of the exact DAA reference."""

    def __init__(self, config: _Config = _REFERENCE) -> None:
        self._config = config

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or seed != self._config.canonical_seed
        ):
            raise ValueError("team-02 DAA requires canonical runtime seed 20260801")
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


def build_strategy() -> DirectionalAuctionAbsorption:
    """Return a fresh DAA reference strategy for the official worker."""
    return DirectionalAuctionAbsorption()
