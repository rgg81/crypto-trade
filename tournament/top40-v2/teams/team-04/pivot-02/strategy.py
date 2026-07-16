"""Path-Adaptive Relative Dynamics (PARD) no-control pivot reference."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any, Literal

import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

_INTERVAL = pd.Timedelta(hours=8)
_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


@dataclasses.dataclass(frozen=True)
class _Config:
    candidate_id: str = "team-04-pard-reference-001"
    family_id: str = "team-04-path-adaptive-relative-dynamics-v1"
    canonical_seed: int = 20260801
    established_bars: int = 63
    medium_bars: int = 21
    displacement_bars: int = 6
    coherence_block_bars: int = 9
    minimum_volatility: float = 1e-6
    maximum_staleness_bars: int = 2
    minimum_cross_section: int = 20
    minimum_sleeve_names: int = 6
    selection_numerator: int = 1
    selection_denominator: int = 4
    long_trend_weight: float = 0.60
    medium_trend_weight: float = 0.40
    minimum_trend_blend: float = 0.35
    side_budget: float = 0.25
    symbol_cap: float = 0.03
    gross_target: float = 0.50
    rebalance_bars: int = 6
    epsilon: float = 1e-12
    tolerance: float = 1e-12

    @property
    def history_return_bars(self) -> int:
        return self.established_bars + self.displacement_bars


_REFERENCE = _Config()


@dataclasses.dataclass(frozen=True)
class _PathFeature:
    established_z: float
    medium_z: float
    displacement_z: float
    coherence: float


@dataclasses.dataclass(frozen=True)
class _ScoreSnapshot:
    decision_time: pd.Timestamp
    scores: dict[str, float]


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _utc_timestamp(value: Any) -> pd.Timestamp | None:
    """Normalize organizer UTC timestamps, including naive and epoch encodings."""

    if isinstance(value, bool):
        return None
    try:
        if isinstance(value, Real):
            numeric = float(value)
            if not math.isfinite(numeric):
                return None
            magnitude = abs(numeric)
            if magnitude >= 1e17:
                unit = "ns"
            elif magnitude >= 1e14:
                unit = "us"
            elif magnitude >= 1e11:
                unit = "ms"
            else:
                unit = "s"
            timestamp = pd.Timestamp(pd.to_datetime(value, unit=unit, utc=True))
        else:
            timestamp = pd.Timestamp(value)
            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize("UTC")
            else:
                timestamp = timestamp.tz_convert("UTC")
    except (TypeError, ValueError, OverflowError):
        return None
    return None if pd.isna(timestamp) else timestamp


def _decision_index(value: Any) -> int | None:
    timestamp = _utc_timestamp(value)
    if timestamp is None:
        return None
    delta = timestamp.value - _EPOCH.value
    if delta < 0 or delta % _INTERVAL.value:
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


def _completed_closes(
    frame: Any,
    *,
    cutoff: pd.Timestamp,
    config: _Config = _REFERENCE,
) -> tuple[float, ...] | None:
    """Extract the latest causal contiguous closes without assuming a storage timezone."""

    if not isinstance(frame, pd.DataFrame):
        return None
    required = ("close_time", "close")
    if not set(required).issubset(frame.columns):
        return None
    rows: dict[pd.Timestamp, list[float]] = {}
    for raw_close_time, raw_close in frame.loc[:, list(required)].itertuples(
        index=False, name=None
    ):
        close_time = _utc_timestamp(raw_close_time)
        close = _finite_number(raw_close)
        if close_time is None or close_time > cutoff or close is None or close <= 0.0:
            continue
        rows.setdefault(close_time, []).append(close)
    required_closes = config.history_return_bars + 1
    ordered_times = sorted(rows)
    if len(ordered_times) < required_closes:
        return None
    times = ordered_times[-required_closes:]
    if any(len(rows[timestamp]) != 1 for timestamp in times):
        return None
    if any(current - previous != _INTERVAL for previous, current in zip(times, times[1:])):
        return None
    age = cutoff - times[-1]
    if age < pd.Timedelta(0) or age > config.maximum_staleness_bars * _INTERVAL:
        return None
    return tuple(rows[timestamp][0] for timestamp in times)


def _path_feature(
    frame: Any,
    *,
    cutoff: pd.Timestamp,
    config: _Config = _REFERENCE,
) -> _PathFeature | None:
    closes = _completed_closes(frame, cutoff=cutoff, config=config)
    if closes is None:
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
    established = returns[: config.established_bars]
    displacement = returns[config.established_bars :]
    medium = established[-config.medium_bars :]
    if (
        len(established) != config.established_bars
        or len(medium) != config.medium_bars
        or len(displacement) != config.displacement_bars
        or config.established_bars % config.coherence_block_bars
    ):
        return None
    mean = math.fsum(established) / len(established)
    variance = math.fsum((value - mean) ** 2 for value in established) / len(established)
    if not math.isfinite(variance) or variance < 0.0:
        return None
    volatility = math.sqrt(variance)
    if not math.isfinite(volatility) or volatility < config.minimum_volatility:
        return None
    established_sum = math.fsum(established)
    established_z = established_sum / (volatility * math.sqrt(len(established)))
    medium_z = math.fsum(medium) / (volatility * math.sqrt(len(medium)))
    displacement_z = math.fsum(displacement) / (volatility * math.sqrt(len(displacement)))
    if abs(established_sum) <= config.epsilon:
        coherence = 0.0
    else:
        direction = 1.0 if established_sum > 0.0 else -1.0
        block_sums = [
            math.fsum(established[start : start + config.coherence_block_bars])
            for start in range(0, len(established), config.coherence_block_bars)
        ]
        agreeing = sum(1 for value in block_sums if direction * value > 0.0)
        agreement_fraction = agreeing / len(block_sums)
        coherence = min(1.0, max(0.0, 2.0 * agreement_fraction - 1.0))
    values = (established_z, medium_z, displacement_z, coherence)
    if any(not math.isfinite(value) for value in values):
        return None
    return _PathFeature(
        established_z=established_z,
        medium_z=medium_z,
        displacement_z=displacement_z,
        coherence=coherence,
    )


def _eligible_symbols(context: Any, config: _Config = _REFERENCE) -> tuple[str, ...] | None:
    raw_eligible = getattr(context, "eligible_symbols", ())
    if isinstance(raw_eligible, (str, bytes)):
        return None
    try:
        eligible_input = tuple(raw_eligible)
    except TypeError:
        return None
    if any(not isinstance(symbol, str) or not symbol for symbol in eligible_input):
        return None
    if len(eligible_input) != len(set(eligible_input)):
        return None
    eligible = tuple(sorted(eligible_input))
    return eligible if len(eligible) >= config.minimum_cross_section else None


def _ranked_path_scores(
    features: Mapping[str, _PathFeature], config: _Config = _REFERENCE
) -> dict[str, float] | None:
    if len(features) < config.minimum_cross_section:
        return None
    long_ranks = _average_ranks(
        {symbol: feature.established_z for symbol, feature in features.items()}
    )
    medium_ranks = _average_ranks(
        {symbol: feature.medium_z for symbol, feature in features.items()}
    )
    displacement_ranks = _average_ranks(
        {symbol: feature.displacement_z for symbol, feature in features.items()}
    )
    if long_ranks is None or medium_ranks is None or displacement_ranks is None:
        return None
    raw: dict[str, float] = {}
    for symbol in sorted(features):
        feature = features[symbol]
        trend = (
            config.long_trend_weight * long_ranks[symbol]
            + config.medium_trend_weight * medium_ranks[symbol]
        )
        trend_blend = (
            config.minimum_trend_blend + (1.0 - config.minimum_trend_blend) * feature.coherence
        )
        raw[symbol] = trend_blend * trend - (1.0 - trend_blend) * displacement_ranks[symbol]
    return _average_ranks(raw)


def _scheduled_score_snapshot(
    context: Any,
    decision_time: pd.Timestamp,
    config: _Config = _REFERENCE,
) -> _ScoreSnapshot | None:
    eligible = _eligible_symbols(context, config)
    if eligible is None:
        return None
    bars = getattr(context, "bars", None)
    if not isinstance(bars, Mapping):
        return None
    cutoff = decision_time - _INTERVAL
    features: dict[str, _PathFeature] = {}
    for symbol in eligible:
        feature = _path_feature(bars.get(symbol), cutoff=cutoff, config=config)
        if feature is not None:
            features[symbol] = feature
    scores = _ranked_path_scores(features, config)
    if scores is None:
        return None
    return _ScoreSnapshot(decision_time=decision_time, scores=scores)


def _capture_scheduled_scores(scores: dict[str, float]) -> dict[str, float]:
    """Call the A5 identity hook once for one manifest-scheduled decision."""

    input_scores = scores
    scores = score_boundary(scores)
    if scores is not input_scores:
        raise RuntimeError("A5 score_boundary must return its input dictionary by identity")
    return scores


def _select_sleeves(
    scores: Mapping[str, float], config: _Config = _REFERENCE
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    if len(scores) < config.minimum_cross_section or any(
        not math.isfinite(score) for score in scores.values()
    ):
        return None
    count = max(
        config.minimum_sleeve_names,
        (config.selection_numerator * len(scores)) // config.selection_denominator,
    )
    if 2 * count > len(scores):
        return None
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    long_symbols = tuple(ordered[-count:])
    short_symbols = tuple(ordered[:count])
    if (
        min(scores[symbol] for symbol in long_symbols) <= 0.0
        or max(scores[symbol] for symbol in short_symbols) >= 0.0
    ):
        return None
    return long_symbols, short_symbols


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
    return weights


def _targets_from_snapshot(
    snapshot: _ScoreSnapshot, config: _Config = _REFERENCE
) -> dict[str, float]:
    sleeves = _select_sleeves(snapshot.scores, config)
    if sleeves is None:
        return {}
    long_symbols, short_symbols = sleeves
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
            not math.isfinite(weight) or abs(weight) > config.symbol_cap
            for weight in targets.values()
        )
    ):
        return {}
    return targets


_DecisionState = Literal["flat", "hold", "scheduled"]


def _evaluate_score_state(
    context: Any, config: _Config = _REFERENCE
) -> tuple[_DecisionState, _ScoreSnapshot | None]:
    raw_decision_time = getattr(context, "decision_time", None)
    decision_time = _utc_timestamp(raw_decision_time)
    decision_index = _decision_index(raw_decision_time)
    if decision_time is None or decision_index is None:
        return "flat", None
    if decision_index % config.rebalance_bars:
        return "hold", None
    try:
        snapshot = _scheduled_score_snapshot(context, decision_time, config)
    except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError):
        snapshot = None
    if snapshot is None:
        _capture_scheduled_scores({})
        return "flat", None
    captured_scores = _capture_scheduled_scores(snapshot.scores)
    return "scheduled", dataclasses.replace(snapshot, scores=captured_scores)


def _validate_seed(seed: Any, config: _Config = _REFERENCE) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed != config.canonical_seed:
        raise ValueError("team-04 PARD requires canonical runtime seed 20260801")


class PathAdaptiveRelativeDynamics:
    """Deterministic market-neutral path-state blend with no risk controls."""

    def __init__(self, config: _Config = _REFERENCE) -> None:
        self._config = config

    def preconstruction_scores(self, context: Any, *, seed: int) -> dict[str, float] | None:
        _validate_seed(seed, self._config)
        state, snapshot = _evaluate_score_state(context, self._config)
        if state == "hold":
            return None
        if state == "flat" or snapshot is None:
            return {}
        return dict(snapshot.scores)

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        _validate_seed(seed, self._config)
        state, snapshot = _evaluate_score_state(context, self._config)
        if state == "hold":
            return None
        if state == "flat" or snapshot is None:
            return {}
        try:
            return _targets_from_snapshot(snapshot, self._config)
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError):
            return {}


def build_strategy() -> PathAdaptiveRelativeDynamics:
    """Return a fresh PARD reference for the official worker."""

    return PathAdaptiveRelativeDynamics()
