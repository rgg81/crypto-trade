"""Broad Exhaustion Reversal (BER) exact no-control pivot reference."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

_INTERVAL = pd.Timedelta(hours=8)
_EPOCH = pd.Timestamp("1970-01-01T00:00:00Z")


@dataclasses.dataclass(frozen=True)
class _Config:
    candidate_id: str = "team-04-ber-reference-001"
    family_id: str = "team-04-broad-exhaustion-reversal-v1"
    canonical_seed: int = 20260801
    baseline_volatility_days: int = 21
    shock_days: int = 3
    minimum_baseline_volatility: float = 1e-6
    coherence_base_weight: float = 0.50
    minimum_cross_section: int = 24
    selection_numerator: int = 3
    selection_denominator: int = 10
    minimum_sleeve_names: int = 8
    side_budget: float = 0.24
    symbol_cap: float = 0.03
    gross_target: float = 0.48
    rebalance_bars: int = 6
    epsilon: float = 1e-12
    tolerance: float = 1e-12

    @property
    def baseline_bars(self) -> int:
        return 3 * self.baseline_volatility_days

    @property
    def shock_bars(self) -> int:
        return 3 * self.shock_days

    @property
    def history_return_bars(self) -> int:
        return self.baseline_bars + self.shock_bars


_REFERENCE = _Config()


@dataclasses.dataclass(frozen=True)
class _ShockFeature:
    shock_log_return: float
    baseline_volatility: float
    path_efficiency: float
    raw_reversal_score: float


@dataclasses.dataclass(frozen=True)
class _ScoreSnapshot:
    decision_time: pd.Timestamp
    raw_scores: Mapping[str, float]
    scores: Mapping[str, float]


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


def _shock_feature(
    frame: Any,
    *,
    cutoff: pd.Timestamp,
    config: _Config = _REFERENCE,
) -> _ShockFeature | None:
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
        if (
            close_time is None
            or close_time != open_time + _INTERVAL
            or close_time > cutoff
            or close is None
            or close <= 0.0
        ):
            # Malformed extras never become observations.  Conversely, every row
            # satisfying this exact predicate is retained, so two valid rows for
            # one expected open fail the len==1 check below.
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
    baseline = returns[: config.baseline_bars]
    shock_path = returns[config.baseline_bars :]
    if len(baseline) != config.baseline_bars or len(shock_path) != config.shock_bars:
        return None
    baseline_mean = math.fsum(baseline) / len(baseline)
    variance = math.fsum((value - baseline_mean) ** 2 for value in baseline) / len(baseline)
    if not math.isfinite(variance) or variance < 0.0:
        return None
    baseline_volatility = math.sqrt(variance)
    if (
        not math.isfinite(baseline_volatility)
        or baseline_volatility < config.minimum_baseline_volatility
    ):
        return None
    shock_log_return = math.fsum(shock_path)
    absolute_path = math.fsum(abs(value) for value in shock_path)
    if absolute_path <= config.epsilon:
        path_efficiency = 0.0
    else:
        # The mathematical ratio is at most one.  Clamp only a possible binary64
        # upward-rounding overshoot; this convention is part of the frozen spec.
        path_efficiency = min(1.0, abs(shock_log_return) / absolute_path)
    standardized_shock = shock_log_return / (
        baseline_volatility * math.sqrt(config.shock_bars)
    )
    coherence_multiplier = config.coherence_base_weight + (
        1.0 - config.coherence_base_weight
    ) * path_efficiency
    raw_reversal_score = -standardized_shock * coherence_multiplier
    values = (
        shock_log_return,
        baseline_volatility,
        path_efficiency,
        raw_reversal_score,
    )
    if any(not math.isfinite(value) for value in values):
        return None
    return _ShockFeature(
        shock_log_return=shock_log_return,
        baseline_volatility=baseline_volatility,
        path_efficiency=path_efficiency,
        raw_reversal_score=raw_reversal_score,
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
    features: dict[str, _ShockFeature] = {}
    for symbol in eligible:
        feature = _shock_feature(bars.get(symbol), cutoff=cutoff, config=config)
        if feature is not None:
            features[symbol] = feature
    if len(features) < config.minimum_cross_section:
        return None
    raw_scores = {
        symbol: features[symbol].raw_reversal_score for symbol in sorted(features)
    }
    ranked = _average_ranks(raw_scores)
    if ranked is None:
        return None
    scores = {symbol: ranked[symbol] for symbol in sorted(ranked)}
    boundary_scores = score_boundary(scores)
    if boundary_scores is not scores:
        raise RuntimeError("A5 score_boundary must return its input dictionary by identity")
    return _ScoreSnapshot(
        decision_time=decision_time,
        raw_scores=raw_scores,
        scores=boundary_scores,
    )


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
    decision_time = _utc_timestamp(getattr(context, "decision_time", None))
    decision_index = _decision_index(getattr(context, "decision_time", None))
    if decision_time is None or decision_index is None:
        return "flat", None
    if decision_index % config.rebalance_bars:
        return "hold", None
    snapshot = _scheduled_score_snapshot(context, decision_time, config)
    if snapshot is None:
        return "flat", None
    return "scheduled", snapshot


def _validate_seed(seed: Any, config: _Config = _REFERENCE) -> None:
    if isinstance(seed, bool) or not isinstance(seed, int) or seed != config.canonical_seed:
        raise ValueError("team-04 BER requires canonical runtime seed 20260801")


class BroadExhaustionReversal:
    """Fresh deterministic instance of the exact BER pivot reference."""

    def __init__(self, config: _Config = _REFERENCE) -> None:
        self._config = config

    def preconstruction_scores(
        self, context: Any, *, seed: int
    ) -> dict[str, float] | None:
        """Return exact ranked scores before sleeve construction; never consumes labels."""

        _validate_seed(seed, self._config)
        try:
            state, snapshot = _evaluate_score_state(context, self._config)
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError):
            return {}
        if state == "hold":
            return None
        if state == "flat" or snapshot is None:
            return {}
        return dict(snapshot.scores)

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        _validate_seed(seed, self._config)
        try:
            state, snapshot = _evaluate_score_state(context, self._config)
            if state == "hold":
                return None
            if state == "flat" or snapshot is None:
                return {}
            return _targets_from_snapshot(snapshot, self._config)
        except (ArithmeticError, KeyError, TypeError, ValueError, OverflowError):
            return {}


def build_strategy() -> BroadExhaustionReversal:
    """Return a fresh BER pivot strategy for the official worker."""

    return BroadExhaustionReversal()
