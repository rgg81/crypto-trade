"""Team 06 relative-rank acceleration reversal pivot.

The strategy uses only organizer-certified, point-in-time pure-crypto membership and completed
8-hour closes.  At each scheduled decision it converts every cross section of close-to-close
returns to centered ranks.  This removes the common crypto direction without estimating a market
portfolio.  It then reverses abrupt changes in each coin's relative rank, rather than fighting a
persistent trend level or taking a directional market tilt.

Every finite final score crosses the organizer-owned prospective score boundary exactly once on
each scheduled construction, before sleeve selection, sizing, caps, or risk.  The returned score
dictionary is the sole input to portfolio construction.
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
REBALANCE_INTERVAL_BARS = 6
BASELINE_RANK_BARS = 63
PRIOR_RANK_BARS = 6
RECENT_RANK_BARS = 6
HISTORY_RETURN_BARS = BASELINE_RANK_BARS + PRIOR_RANK_BARS + RECENT_RANK_BARS
MINIMUM_VALID_SYMBOLS = 24
MINIMUM_POSITIONS_PER_SIDE = 8
SELECTION_NUMERATOR = 1
SELECTION_DENOMINATOR = 4
SIDE_BUDGET = 0.24
MAXIMUM_SYMBOL_EXPOSURE = 0.03
MINIMUM_RANK_VOLATILITY = 0.15
COHERENCE_BASE_WEIGHT = 0.50
EPSILON = 1e-12
TOLERANCE = 1e-12

ACTIVE_FAMILY_ID = "t06-relative-rank-acceleration-v1"
ACTIVE_CANDIDATE_ID = "t06-relative-rank-acceleration-v1-base"
MATERIALIZED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    ACTIVE_CANDIDATE_ID: {},
}

_BAR_INTERVAL = pd.Timedelta(hours=BAR_INTERVAL_HOURS)


class ContextLike(Protocol):
    """Runtime subset of the neutral decision context used by this strategy."""

    decision_time: pd.Timestamp
    bars: Mapping[str, pd.DataFrame]
    funding: pd.DataFrame
    auxiliary: Mapping[str, pd.DataFrame]
    eligible_symbols: Sequence[str]


@dataclasses.dataclass(frozen=True)
class _RelativeFeature:
    prior_mean_rank: float
    recent_mean_rank: float
    baseline_rank_volatility: float
    acceleration: float
    coherence: float
    raw_reversal_score: float


@dataclasses.dataclass(frozen=True)
class PreconstructionSnapshot:
    """Immutable all-candidate scores before selection, sizing, caps, or risk."""

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
    """Parse timezone-aware timestamps and common integer epoch encodings."""

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
    """Exact opens for the closes that form ``HISTORY_RETURN_BARS`` returns."""

    return tuple(
        decision_time - offset * _BAR_INTERVAL for offset in range(HISTORY_RETURN_BARS + 1, 0, -1)
    )


def _closed_history(
    frame: Any,
    *,
    decision_time: pd.Timestamp,
) -> tuple[float, ...] | None:
    """Extract one finite positive close at every exact required past open."""

    if (
        not isinstance(frame, pd.DataFrame)
        or not isinstance(frame.index, pd.RangeIndex)
        or "open_time" not in frame.columns
        or "close" not in frame.columns
    ):
        return None

    expected = _expected_open_times(decision_time)
    rows: dict[pd.Timestamp, list[Any]] = {timestamp: [] for timestamp in expected}
    for raw_open, raw_close in frame.loc[:, ["open_time", "close"]].itertuples(
        index=False, name=None
    ):
        open_time = _utc_timestamp(raw_open)
        if open_time is None or open_time not in rows:
            continue
        rows[open_time].append(raw_close)

    values: list[float] = []
    for timestamp in expected:
        if len(rows[timestamp]) != 1:
            return None
        close = _finite_number(rows[timestamp][0])
        if timestamp + _BAR_INTERVAL > decision_time or close is None or close <= 0.0:
            return None
        values.append(close)
    return tuple(values)


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


def _centered_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    """Deterministic average-tie ranks mapped to ``[-1, 1]``."""

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


def _sample_volatility(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
    if not math.isfinite(variance) or variance < 0.0:
        return None
    result = math.sqrt(variance)
    return result if math.isfinite(result) else None


def _relative_feature(rank_path: Sequence[float]) -> _RelativeFeature | None:
    if len(rank_path) != HISTORY_RETURN_BARS:
        return None
    baseline_stop = BASELINE_RANK_BARS
    prior_stop = baseline_stop + PRIOR_RANK_BARS
    baseline = rank_path[:baseline_stop]
    prior = rank_path[baseline_stop:prior_stop]
    recent = rank_path[prior_stop:]
    if len(prior) != PRIOR_RANK_BARS or len(recent) != RECENT_RANK_BARS:
        return None

    baseline_volatility = _sample_volatility(baseline)
    if baseline_volatility is None:
        return None
    prior_mean = math.fsum(prior) / len(prior)
    recent_mean = math.fsum(recent) / len(recent)
    acceleration = recent_mean - prior_mean
    deviations = tuple(value - prior_mean for value in recent)
    absolute_path = math.fsum(abs(value) for value in deviations)
    coherence = (
        0.0 if absolute_path <= EPSILON else min(1.0, abs(math.fsum(deviations)) / absolute_path)
    )
    standardized = acceleration / max(MINIMUM_RANK_VOLATILITY, baseline_volatility)
    raw_score = -standardized * (COHERENCE_BASE_WEIGHT + (1.0 - COHERENCE_BASE_WEIGHT) * coherence)
    values = (
        prior_mean,
        recent_mean,
        baseline_volatility,
        acceleration,
        coherence,
        raw_score,
    )
    if any(not math.isfinite(value) for value in values):
        return None
    return _RelativeFeature(
        prior_mean_rank=float(prior_mean),
        recent_mean_rank=float(recent_mean),
        baseline_rank_volatility=float(baseline_volatility),
        acceleration=float(acceleration),
        coherence=float(coherence),
        raw_reversal_score=float(raw_score),
    )


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


class RelativeRankAccelerationStrategy:
    """Cross-sectional reversal of common-factor-free relative-rank acceleration."""

    @staticmethod
    def _validate_seed(seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed != FROZEN_SEED:
            raise ValueError(f"Team 06 requires frozen seed {FROZEN_SEED}")

    def preconstruction_snapshot(
        self,
        context: ContextLike,
        *,
        seed: int,
        decision_time: pd.Timestamp | None = None,
    ) -> PreconstructionSnapshot | None:
        """Build final ranked scores from exact completed histories."""

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
        if len(return_paths) < MINIMUM_VALID_SYMBOLS:
            return None

        rank_paths: dict[str, list[float]] = {symbol: [] for symbol in sorted(return_paths)}
        for index in range(HISTORY_RETURN_BARS):
            cross_section = {symbol: return_paths[symbol][index] for symbol in sorted(return_paths)}
            ranks = _centered_ranks(cross_section)
            if ranks is None:
                return None
            for symbol in rank_paths:
                rank_paths[symbol].append(ranks[symbol])

        features: dict[str, _RelativeFeature] = {}
        for symbol in sorted(rank_paths):
            feature = _relative_feature(rank_paths[symbol])
            if feature is not None:
                features[symbol] = feature
        if len(features) < MINIMUM_VALID_SYMBOLS:
            return None

        ranked_scores = _centered_ranks(
            {symbol: features[symbol].raw_reversal_score for symbol in sorted(features)}
        )
        if ranked_scores is None:
            return None
        return PreconstructionSnapshot(
            decision_time=decision_time,
            scores=tuple(
                (symbol, float(ranked_scores[symbol])) for symbol in sorted(ranked_scores)
            ),
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
        """Return scheduled captured scores; nonscheduled calls are empty and uncaptured."""

        self._validate_seed(seed)
        state, decision_time = _decision_state(context.decision_time)
        if state != "scheduled" or decision_time is None:
            return {}
        snapshot = self.preconstruction_snapshot(
            context,
            seed=seed,
            decision_time=decision_time,
        )
        scores = {} if snapshot is None else snapshot.score_map()
        return self._apply_public_score_boundary(scores)

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

        count = max(
            MINIMUM_POSITIONS_PER_SIDE,
            (SELECTION_NUMERATOR * len(scores)) // SELECTION_DENOMINATOR,
        )
        if 2 * count > len(scores):
            return {}
        ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
        short_symbols = tuple(ordered[:count])
        long_symbols = tuple(ordered[-count:])
        effective_side_budget = min(SIDE_BUDGET, count * MAXIMUM_SYMBOL_EXPOSURE)
        weight = effective_side_budget / count
        if not math.isfinite(weight) or weight <= 0.0 or weight > MAXIMUM_SYMBOL_EXPOSURE:
            return {}

        targets = {symbol: -float(weight) for symbol in short_symbols}
        targets.update({symbol: float(weight) for symbol in long_symbols})
        gross = math.fsum(abs(value) for value in targets.values())
        net = math.fsum(targets.values())
        if gross > 2.0 * SIDE_BUDGET + TOLERANCE or abs(net) > TOLERANCE:
            return {}
        return {symbol: targets[symbol] for symbol in sorted(targets)}


def build_strategy() -> RelativeRankAccelerationStrategy:
    """Canonical zero-argument factory for the exact promoted pivot candidate."""

    candidate_id = candidate_variant.ACTIVE_CANDIDATE_ID
    overrides = candidate_variant.ACTIVE_OVERRIDES
    expected = MATERIALIZED_CANDIDATE_OVERRIDES.get(candidate_id)
    if expected is None:
        raise ValueError(f"unknown materialized candidate identifier: {candidate_id}")
    if type(overrides) is not dict or overrides != expected:
        raise ValueError(f"active overrides do not match the declaration for {candidate_id}")
    return RelativeRankAccelerationStrategy()
