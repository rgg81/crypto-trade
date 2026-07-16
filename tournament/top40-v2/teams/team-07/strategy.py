"""Team 07 causal two-tape relative-rank durability pivot.

The organizer supplies point-in-time pure-crypto membership and completed 8-hour bars.  On every
scheduled construction, the strategy ranks each coin's return against the other eligible coins at
each of 126 completed bars.  A coin earns a durable relative-strength score only to the extent that
its ranks agree across common-market up and down bars and across three non-overlapping time blocks.
This is a cross-sectional persistence mechanism: it has no common directional forecast, residual
trend/reversal blend, funding input, position state, PnL state, external file, or network input.

One finite built-in score dictionary crosses the organizer's public A5 boundary after the complete
durability transform and before selection, sizing, caps, or organizer risk.  The exact returned
dictionary is the sole signal object used to build a weekly, broad, dollar-neutral portfolio.
"""

from __future__ import annotations

import dataclasses
import math
import numbers
from collections.abc import Mapping, Sequence
from typing import Any, Literal, Protocol

import candidate_variant
import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

FROZEN_SEED = 20260801
BAR_INTERVAL_HOURS = 8
REBALANCE_INTERVAL_BARS = 21
HISTORY_RETURN_BARS = 126
TIME_BLOCK_COUNT = 3
TIME_BLOCK_BARS = 42
MINIMUM_TAPE_BARS = 18
MINIMUM_VALID_SYMBOLS = 24
MINIMUM_POSITIONS_PER_SIDE = 8
SELECTION_NUMERATOR = 1
SELECTION_DENOMINATOR = 5
GROSS_TARGET = 0.36
MAXIMUM_SYMBOL_EXPOSURE = 0.025
TAPE_CORE_WEIGHT = 0.70
BLOCK_CORE_WEIGHT = 0.30
CROSS_TAPE_DISAGREEMENT_SHRINK = 0.15
TOLERANCE = 1e-10

ACTIVE_FAMILY_ID = "t07-two-tape-rank-durability-v1"
ACTIVE_CANDIDATE_ID = "t07-two-tape-rank-durability-v1-base"
MATERIALIZED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    ACTIVE_CANDIDATE_ID: {},
}

_BAR_INTERVAL = pd.Timedelta(hours=BAR_INTERVAL_HOURS)


class ContextLike(Protocol):
    """Runtime subset of the neutral decision context consumed by Team 07."""

    decision_time: pd.Timestamp
    bars: Mapping[str, pd.DataFrame]
    funding: pd.DataFrame
    auxiliary: Mapping[str, pd.DataFrame]
    eligible_symbols: Sequence[str]


@dataclasses.dataclass(frozen=True)
class _DurabilityFeature:
    up_tape_mean: float
    down_tape_mean: float
    block_means: tuple[float, float, float]
    raw_score: float


@dataclasses.dataclass(frozen=True)
class PreconstructionSnapshot:
    """Immutable final scores before selection, sizing, caps, or organizer risk."""

    decision_time: pd.Timestamp
    scores: tuple[tuple[str, float], ...]

    def score_map(self) -> dict[str, float]:
        return {symbol: float(value) for symbol, value in self.scores}


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return result if math.isfinite(result) else None


def _utc_timestamp(value: Any) -> pd.Timestamp | None:
    """Parse an aware timestamp, including common integer epoch encodings."""

    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, numbers.Real):
            magnitude = abs(float(value))
            if magnitude >= 1.0e17:
                unit = "ns"
            elif magnitude >= 1.0e14:
                unit = "us"
            elif magnitude >= 1.0e11:
                unit = "ms"
            else:
                unit = "s"
            timestamp = pd.Timestamp(value, unit=unit, tz="UTC")
        else:
            timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if pd.isna(timestamp) or timestamp.tzinfo is None:
        return None
    try:
        return timestamp.tz_convert("UTC")
    except (TypeError, ValueError, OverflowError):
        return None


_DecisionState = Literal["flat", "hold", "scheduled"]


def _decision_state(value: Any) -> tuple[_DecisionState, pd.Timestamp | None]:
    timestamp = _utc_timestamp(value)
    if timestamp is None:
        return "flat", None
    interval_ns = int(_BAR_INTERVAL.value)
    timestamp_ns = int(timestamp.value)
    if timestamp_ns < 0 or timestamp_ns % interval_ns:
        return "flat", timestamp
    if (timestamp_ns // interval_ns) % REBALANCE_INTERVAL_BARS:
        return "hold", timestamp
    return "scheduled", timestamp


def _expected_open_times(decision_time: pd.Timestamp) -> tuple[pd.Timestamp, ...]:
    """Exact opens for the closes needed to form the frozen return history."""

    return tuple(
        decision_time - offset * _BAR_INTERVAL for offset in range(HISTORY_RETURN_BARS + 1, 0, -1)
    )


def _closed_history(frame: Any, *, decision_time: pd.Timestamp) -> tuple[float, ...] | None:
    """Extract one finite positive close at every exact completed-bar open."""

    if not isinstance(frame, pd.DataFrame) or not {"open_time", "close"}.issubset(frame.columns):
        return None
    expected = _expected_open_times(decision_time)
    values: dict[pd.Timestamp, list[Any]] = {timestamp: [] for timestamp in expected}
    for raw_open, raw_close in frame.loc[:, ["open_time", "close"]].itertuples(
        index=False, name=None
    ):
        open_time = _utc_timestamp(raw_open)
        if open_time is None or open_time not in values:
            continue
        values[open_time].append(raw_close)
    closes: list[float] = []
    for timestamp in expected:
        if len(values[timestamp]) != 1:
            return None
        close = _finite_number(values[timestamp][0])
        if timestamp + _BAR_INTERVAL > decision_time or close is None or close <= 0.0:
            return None
        closes.append(close)
    return tuple(closes)


def _log_returns(closes: Sequence[float]) -> tuple[float, ...] | None:
    if len(closes) != HISTORY_RETURN_BARS + 1:
        return None
    result: list[float] = []
    for previous, current in zip(closes[:-1], closes[1:], strict=True):
        ratio = current / previous
        if not math.isfinite(ratio) or ratio <= 0.0:
            return None
        value = math.log(ratio)
        if not math.isfinite(value):
            return None
        result.append(value)
    return tuple(result)


def _median(values: Sequence[float]) -> float | None:
    ordered = sorted(values)
    if not ordered or any(not math.isfinite(value) for value in ordered):
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return float(ordered[middle])
    return float(0.5 * (ordered[middle - 1] + ordered[middle]))


def _centered_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    """Deterministic average-tie ranks mapped to [-1, 1]."""

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
        average_index = (start + stop - 1) / 2.0
        rank = 2.0 * average_index / denominator - 1.0
        for index in range(start, stop):
            result[ordered[index][0]] = float(rank)
        start = stop
    return result


def _eligible_symbols(context: ContextLike) -> tuple[str, ...] | None:
    raw = context.eligible_symbols
    if isinstance(raw, (str, bytes)):
        return None
    try:
        supplied = tuple(raw)
    except TypeError:
        return None
    if any(not isinstance(symbol, str) or not symbol for symbol in supplied):
        return None
    if len(supplied) != len(set(supplied)):
        return None
    eligible = tuple(sorted(supplied))
    return eligible if len(eligible) >= MINIMUM_VALID_SYMBOLS else None


def _rank_histories(
    return_paths: Mapping[str, Sequence[float]],
) -> tuple[dict[str, tuple[float, ...]], tuple[float, ...]] | None:
    """Build causal same-bar return ranks and the median common tape."""

    if len(return_paths) < MINIMUM_VALID_SYMBOLS:
        return None
    if any(len(path) != HISTORY_RETURN_BARS for path in return_paths.values()):
        return None
    rank_paths: dict[str, list[float]] = {symbol: [] for symbol in sorted(return_paths)}
    market_path: list[float] = []
    for index in range(HISTORY_RETURN_BARS):
        cross_section = {
            symbol: float(return_paths[symbol][index]) for symbol in sorted(return_paths)
        }
        market_return = _median(list(cross_section.values()))
        ranks = _centered_ranks(cross_section)
        if market_return is None or ranks is None:
            return None
        market_path.append(market_return)
        for symbol in sorted(rank_paths):
            rank_paths[symbol].append(ranks[symbol])
    return (
        {symbol: tuple(rank_paths[symbol]) for symbol in sorted(rank_paths)},
        tuple(market_path),
    )


def _mean(values: Sequence[float]) -> float | None:
    if not values or any(not math.isfinite(value) for value in values):
        return None
    result = math.fsum(values) / len(values)
    return float(result) if math.isfinite(result) else None


def _durability_feature(
    rank_path: Sequence[float], market_path: Sequence[float]
) -> _DurabilityFeature | None:
    """Shrink relative strength that does not survive both market tapes and time blocks."""

    if len(rank_path) != HISTORY_RETURN_BARS or len(market_path) != HISTORY_RETURN_BARS:
        return None
    up_values = [rank for rank, market in zip(rank_path, market_path, strict=True) if market > 0.0]
    down_values = [
        rank for rank, market in zip(rank_path, market_path, strict=True) if market < 0.0
    ]
    if len(up_values) < MINIMUM_TAPE_BARS or len(down_values) < MINIMUM_TAPE_BARS:
        return None
    up_mean = _mean(up_values)
    down_mean = _mean(down_values)
    block_means = tuple(
        _mean(rank_path[index * TIME_BLOCK_BARS : (index + 1) * TIME_BLOCK_BARS])
        for index in range(TIME_BLOCK_COUNT)
    )
    if up_mean is None or down_mean is None or any(value is None for value in block_means):
        return None
    finite_blocks = tuple(float(value) for value in block_means if value is not None)
    if len(finite_blocks) != TIME_BLOCK_COUNT:
        return None

    if up_mean * down_mean > 0.0:
        tape_core = math.copysign(min(abs(up_mean), abs(down_mean)), up_mean)
    else:
        tape_core = CROSS_TAPE_DISAGREEMENT_SHRINK * 0.5 * (up_mean + down_mean)
    block_core = _median(finite_blocks)
    if block_core is None:
        return None
    combined = TAPE_CORE_WEIGHT * tape_core + BLOCK_CORE_WEIGHT * block_core
    components = (up_mean, down_mean, *finite_blocks)
    if combined == 0.0:
        agreement = 0.0
    else:
        agreement = sum(component * combined > 0.0 for component in components) / len(components)
    dispersion = abs(up_mean - down_mean) + max(finite_blocks) - min(finite_blocks)
    raw_score = combined * agreement**2 / (1.0 + dispersion)
    if not math.isfinite(raw_score):
        return None
    return _DurabilityFeature(
        up_tape_mean=float(up_mean),
        down_tape_mean=float(down_mean),
        block_means=(finite_blocks[0], finite_blocks[1], finite_blocks[2]),
        raw_score=float(raw_score),
    )


class TwoTapeRankDurabilityStrategy:
    """Trade persistent cross-sectional leaders and laggards across both market tapes."""

    @staticmethod
    def _validate_seed(seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed != FROZEN_SEED:
            raise ValueError(f"Team 07 requires frozen seed {FROZEN_SEED}")

    def preconstruction_snapshot(
        self,
        context: ContextLike,
        *,
        seed: int,
        decision_time: pd.Timestamp | None = None,
    ) -> PreconstructionSnapshot | None:
        """Build final durability ranks from exact completed histories."""

        self._validate_seed(seed)
        if decision_time is None:
            state, parsed = _decision_state(context.decision_time)
            if state != "scheduled" or parsed is None:
                return None
            decision_time = parsed

        eligible = _eligible_symbols(context)
        if eligible is None or not isinstance(context.bars, Mapping):
            return None

        return_paths: dict[str, tuple[float, ...]] = {}
        for symbol in eligible:
            history = _closed_history(context.bars.get(symbol), decision_time=decision_time)
            if history is None:
                continue
            returns = _log_returns(history)
            if returns is not None:
                return_paths[symbol] = returns
        ranked = _rank_histories(return_paths)
        if ranked is None:
            return None
        rank_paths, market_path = ranked

        raw_scores: dict[str, float] = {}
        for symbol in sorted(rank_paths):
            feature = _durability_feature(rank_paths[symbol], market_path)
            if feature is None:
                return None
            raw_scores[symbol] = feature.raw_score
        final_scores = _centered_ranks(raw_scores)
        if final_scores is None:
            return None
        return PreconstructionSnapshot(
            decision_time=decision_time,
            scores=tuple((symbol, float(final_scores[symbol])) for symbol in sorted(final_scores)),
        )

    @staticmethod
    def _apply_public_score_boundary(scores: dict[str, float]) -> dict[str, float]:
        if type(scores) is not dict or any(
            type(symbol) is not str or type(value) is not float or not math.isfinite(value)
            for symbol, value in scores.items()
        ):
            raise ValueError("score boundary input must be a finite built-in dict[str, float]")
        input_scores = scores
        expected_symbols = set(scores)
        scores = score_boundary(scores)
        if scores is not input_scores:
            raise ValueError("score_boundary must return its exact input dictionary")
        if (
            type(scores) is not dict
            or set(scores) != expected_symbols
            or any(
                type(symbol) is not str or type(value) is not float or not math.isfinite(value)
                for symbol, value in scores.items()
            )
        ):
            raise ValueError("score_boundary returned invalid scores")
        return scores

    def preconstruction_scores(self, context: ContextLike, *, seed: int) -> Mapping[str, float]:
        """Return one captured scheduled score dictionary for organizer diagnostics."""

        self._validate_seed(seed)
        state, decision_time = _decision_state(context.decision_time)
        if state != "scheduled" or decision_time is None:
            return {}
        snapshot = self.preconstruction_snapshot(
            context,
            seed=seed,
            decision_time=decision_time,
        )
        return self._apply_public_score_boundary({} if snapshot is None else snapshot.score_map())

    def target_weights(self, context: ContextLike, *, seed: int) -> Mapping[str, float] | None:
        self._validate_seed(seed)
        state, decision_time = _decision_state(context.decision_time)
        if state == "hold":
            return None
        if state == "flat" or decision_time is None:
            return {}

        snapshot = self.preconstruction_snapshot(
            context,
            seed=seed,
            decision_time=decision_time,
        )
        scores = self._apply_public_score_boundary({} if snapshot is None else snapshot.score_map())
        if len(scores) < MINIMUM_VALID_SYMBOLS:
            return {}

        side_budget = 0.5 * GROSS_TARGET
        cap_count = int(math.ceil((side_budget - TOLERANCE) / MAXIMUM_SYMBOL_EXPOSURE))
        count = max(
            MINIMUM_POSITIONS_PER_SIDE,
            (SELECTION_NUMERATOR * len(scores)) // SELECTION_DENOMINATOR,
            cap_count,
        )
        if count <= 0 or 2 * count > len(scores):
            return {}

        ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
        short_symbols = tuple(ordered[:count])
        long_symbols = tuple(ordered[-count:])
        side_weight = side_budget / count
        if (
            not math.isfinite(side_weight)
            or side_weight <= 0.0
            or side_weight > MAXIMUM_SYMBOL_EXPOSURE + TOLERANCE
        ):
            return {}

        targets = {symbol: -float(side_weight) for symbol in short_symbols}
        targets.update({symbol: float(side_weight) for symbol in long_symbols})
        targets = {symbol: targets[symbol] for symbol in sorted(targets)}
        gross = math.fsum(abs(value) for value in targets.values())
        net = math.fsum(targets.values())
        if abs(gross - GROSS_TARGET) > TOLERANCE or abs(net) > TOLERANCE:
            return {}
        if not any(value > 0.0 for value in targets.values()):
            return {}
        if not any(value < 0.0 for value in targets.values()):
            return {}
        return targets


def build_strategy() -> TwoTapeRankDurabilityStrategy:
    """Canonical zero-argument factory for the exact promoted pivot candidate."""

    candidate_id = candidate_variant.ACTIVE_CANDIDATE_ID
    overrides = candidate_variant.ACTIVE_OVERRIDES
    expected = MATERIALIZED_CANDIDATE_OVERRIDES.get(candidate_id)
    if expected is None:
        raise ValueError(f"unknown materialized candidate identifier: {candidate_id}")
    if type(overrides) is not dict or overrides != expected:
        raise ValueError(f"active overrides do not match the declaration for {candidate_id}")
    return TwoTapeRankDurabilityStrategy()
