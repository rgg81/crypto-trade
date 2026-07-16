"""Team 07 causal market-state and relative-opportunity ensemble pivot.

The organizer supplies point-in-time pure-crypto membership and completed 8-hour bars.  The
strategy first estimates a robust common crypto trend from the cross-sectional median return.
It then blends medium/slow residual momentum with short residual reversal; the blend moves toward
momentum only when the fast and slow common trends agree.  Past funding is a small cross-sectional
carry input.  No position, fill, PnL, evaluator state, external file, or network input is used.

Every scheduled construction sends one finite built-in score dictionary through the organizer's
public A5 boundary.  A common score offset encodes the directional forecast and the centered score
dispersion encodes relative opportunity.  The returned dictionary is therefore the only signal
object used for both side sizing and cross-sectional selection.
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
HISTORY_RETURN_BARS = 189
SHORT_REVERSAL_BARS = 3
MEDIUM_TREND_BARS = 21
SLOW_TREND_BARS = 63
MARKET_FAST_BARS = 21
MARKET_SLOW_BARS = 126
VOLATILITY_BARS = 63
FUNDING_LOOKBACK_EVENTS = 21
MINIMUM_VALID_SYMBOLS = 24
MINIMUM_POSITIONS_PER_SIDE = 8
SELECTION_NUMERATOR = 1
SELECTION_DENOMINATOR = 4
GROSS_TARGET = 0.48
MAXIMUM_DIRECTIONAL_NET = 0.20
MAXIMUM_SYMBOL_EXPOSURE = 0.04
MINIMUM_RETURN_VOLATILITY = 0.002
MARKET_TREND_Z_SCALE = 2.0
MARKET_FAST_WEIGHT = 0.45
MARKET_SLOW_WEIGHT = 0.45
MARKET_BREADTH_WEIGHT = 0.10
RELATIVE_TREND_BASE_WEIGHT = 0.35
RELATIVE_TREND_STATE_WEIGHT = 0.45
MEDIUM_RELATIVE_TREND_WEIGHT = 0.60
SLOW_RELATIVE_TREND_WEIGHT = 0.40
FUNDING_CARRY_WEIGHT = 0.15
MARKET_SCORE_OFFSET = 1.25
TOLERANCE = 1e-10

ACTIVE_FAMILY_ID = "t07-market-state-relative-ensemble-v1"
ACTIVE_CANDIDATE_ID = "t07-market-state-relative-ensemble-v1-base"
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
class _RelativeFeature:
    short_reversal: float
    medium_trend: float
    slow_trend: float


@dataclasses.dataclass(frozen=True)
class PreconstructionSnapshot:
    """Immutable final forecasts before selection, sizing, caps, or organizer risk."""

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
    values: dict[pd.Timestamp, list[float]] = {timestamp: [] for timestamp in expected}
    for raw_open, raw_close in frame.loc[:, ["open_time", "close"]].itertuples(
        index=False, name=None
    ):
        open_time = _utc_timestamp(raw_open)
        if open_time is None or open_time not in values:
            continue
        close = _finite_number(raw_close)
        if open_time + _BAR_INTERVAL > decision_time or close is None or close <= 0.0:
            continue
        values[open_time].append(close)
    if any(len(values[timestamp]) != 1 for timestamp in expected):
        return None
    return tuple(values[timestamp][0] for timestamp in expected)


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


def _sample_volatility(values: Sequence[float]) -> float | None:
    if len(values) < 2:
        return None
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
    if not math.isfinite(variance) or variance < 0.0:
        return None
    result = math.sqrt(variance)
    return result if math.isfinite(result) else None


def _bounded_trend(path: Sequence[float], bars: int, volatility: float) -> float:
    denominator = max(MINIMUM_RETURN_VOLATILITY, volatility) * math.sqrt(bars)
    raw = math.fsum(path[-bars:]) / denominator
    return float(max(-6.0, min(6.0, raw)))


def _market_path(return_paths: Mapping[str, Sequence[float]]) -> tuple[float, ...] | None:
    if len(return_paths) < MINIMUM_VALID_SYMBOLS:
        return None
    result: list[float] = []
    for index in range(HISTORY_RETURN_BARS):
        value = _median([path[index] for path in return_paths.values()])
        if value is None:
            return None
        result.append(value)
    return tuple(result)


def _market_state(
    return_paths: Mapping[str, Sequence[float]], market_path: Sequence[float]
) -> tuple[float, float] | None:
    volatility = _sample_volatility(market_path[-MARKET_SLOW_BARS:])
    if volatility is None:
        return None
    fast_z = _bounded_trend(market_path, MARKET_FAST_BARS, volatility)
    slow_z = _bounded_trend(market_path, MARKET_SLOW_BARS, volatility)
    fast_state = math.tanh(fast_z / MARKET_TREND_Z_SCALE)
    slow_state = math.tanh(slow_z / MARKET_TREND_Z_SCALE)
    positive = sum(math.fsum(path[-MARKET_FAST_BARS:]) > 0.0 for path in return_paths.values())
    negative = sum(math.fsum(path[-MARKET_FAST_BARS:]) < 0.0 for path in return_paths.values())
    breadth = (positive - negative) / len(return_paths)
    state = (
        MARKET_FAST_WEIGHT * fast_state
        + MARKET_SLOW_WEIGHT * slow_state
        + MARKET_BREADTH_WEIGHT * breadth
    )
    state = float(max(-1.0, min(1.0, state)))
    agreement = abs(0.5 * (fast_state + slow_state))
    confidence = float(max(0.0, min(1.0, agreement)))
    return state, confidence


def _relative_feature(
    asset_path: Sequence[float], market_path: Sequence[float]
) -> _RelativeFeature | None:
    if len(asset_path) != HISTORY_RETURN_BARS or len(market_path) != HISTORY_RETURN_BARS:
        return None
    residual = tuple(asset - market for asset, market in zip(asset_path, market_path, strict=True))
    volatility = _sample_volatility(residual[-VOLATILITY_BARS:])
    if volatility is None:
        return None
    short_reversal = -_bounded_trend(residual, SHORT_REVERSAL_BARS, volatility)
    medium_trend = _bounded_trend(residual, MEDIUM_TREND_BARS, volatility)
    slow_trend = _bounded_trend(residual, SLOW_TREND_BARS, volatility)
    values = (short_reversal, medium_trend, slow_trend)
    if any(not math.isfinite(value) for value in values):
        return None
    return _RelativeFeature(
        short_reversal=float(short_reversal),
        medium_trend=float(medium_trend),
        slow_trend=float(slow_trend),
    )


def _past_funding_carry(
    raw_funding: Any,
    *,
    decision_time: pd.Timestamp,
    eligible: set[str],
) -> dict[str, float] | None:
    """Return negative trailing funding means using only strictly past events."""

    if not isinstance(raw_funding, pd.DataFrame):
        return None
    if raw_funding.empty:
        return {symbol: 0.0 for symbol in eligible}
    required = {"funding_time", "symbol", "funding_rate"}
    if not required.issubset(raw_funding.columns):
        return None
    observations: dict[str, list[tuple[pd.Timestamp, float]]] = {symbol: [] for symbol in eligible}
    seen: set[tuple[str, pd.Timestamp]] = set()
    for raw_time, raw_symbol, raw_rate in raw_funding.loc[
        :, ["funding_time", "symbol", "funding_rate"]
    ].itertuples(index=False, name=None):
        timestamp = _utc_timestamp(raw_time)
        rate = _finite_number(raw_rate)
        if timestamp is None or timestamp >= decision_time or rate is None:
            return None
        if not isinstance(raw_symbol, str) or raw_symbol not in eligible:
            return None
        key = (raw_symbol, timestamp)
        if key in seen:
            return None
        seen.add(key)
        observations[raw_symbol].append((timestamp, rate))
    carry: dict[str, float] = {}
    for symbol in sorted(eligible):
        recent = sorted(observations[symbol], key=lambda item: item[0])[-FUNDING_LOOKBACK_EVENTS:]
        carry[symbol] = (
            0.0 if not recent else -float(math.fsum(rate for _, rate in recent) / len(recent))
        )
    return carry


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


class MarketStateRelativeEnsembleStrategy:
    """Blend causal common trend, residual trend/reversal, and past funding carry."""

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
        """Build final common-plus-relative scores from exact completed histories."""

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

        market_path = _market_path(return_paths)
        if market_path is None:
            return None
        state_result = _market_state(return_paths, market_path)
        if state_result is None:
            return None
        market_state, state_confidence = state_result

        features: dict[str, _RelativeFeature] = {}
        for symbol in sorted(return_paths):
            feature = _relative_feature(return_paths[symbol], market_path)
            if feature is not None:
                features[symbol] = feature
        if len(features) < MINIMUM_VALID_SYMBOLS:
            return None

        carry = _past_funding_carry(
            context.funding,
            decision_time=decision_time,
            eligible=set(eligible),
        )
        if carry is None:
            return None
        short_ranks = _centered_ranks(
            {symbol: features[symbol].short_reversal for symbol in sorted(features)}
        )
        medium_ranks = _centered_ranks(
            {symbol: features[symbol].medium_trend for symbol in sorted(features)}
        )
        slow_ranks = _centered_ranks(
            {symbol: features[symbol].slow_trend for symbol in sorted(features)}
        )
        carry_ranks = _centered_ranks(
            {symbol: carry.get(symbol, 0.0) for symbol in sorted(features)}
        )
        if short_ranks is None or medium_ranks is None or slow_ranks is None or carry_ranks is None:
            return None

        trend_weight = RELATIVE_TREND_BASE_WEIGHT + (RELATIVE_TREND_STATE_WEIGHT * state_confidence)
        reversal_weight = 1.0 - trend_weight
        raw_relative: dict[str, float] = {}
        for symbol in sorted(features):
            trend = (
                MEDIUM_RELATIVE_TREND_WEIGHT * medium_ranks[symbol]
                + SLOW_RELATIVE_TREND_WEIGHT * slow_ranks[symbol]
            )
            value = (
                trend_weight * trend
                + reversal_weight * short_ranks[symbol]
                + FUNDING_CARRY_WEIGHT * carry_ranks[symbol]
            )
            if not math.isfinite(value):
                return None
            raw_relative[symbol] = float(value)
        relative_ranks = _centered_ranks(raw_relative)
        if relative_ranks is None:
            return None

        common_offset = MARKET_SCORE_OFFSET * market_state
        scores = {
            symbol: float(relative_ranks[symbol] + common_offset)
            for symbol in sorted(relative_ranks)
        }
        if any(not math.isfinite(value) for value in scores.values()):
            return None
        return PreconstructionSnapshot(
            decision_time=decision_time,
            scores=tuple((symbol, scores[symbol]) for symbol in sorted(scores)),
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

        captured_mean = math.fsum(scores.values()) / len(scores)
        captured_market_state = max(-1.0, min(1.0, captured_mean / MARKET_SCORE_OFFSET))
        directional_net = MAXIMUM_DIRECTIONAL_NET * captured_market_state
        long_budget = 0.5 * (GROSS_TARGET + directional_net)
        short_budget = 0.5 * (GROSS_TARGET - directional_net)
        cap_count = int(
            math.ceil((max(long_budget, short_budget) - TOLERANCE) / MAXIMUM_SYMBOL_EXPOSURE)
        )
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
        long_weight = long_budget / count
        short_weight = short_budget / count
        if (
            not math.isfinite(long_weight)
            or not math.isfinite(short_weight)
            or long_weight <= 0.0
            or short_weight <= 0.0
            or max(long_weight, short_weight) > MAXIMUM_SYMBOL_EXPOSURE + TOLERANCE
        ):
            return {}

        targets = {symbol: -float(short_weight) for symbol in short_symbols}
        targets.update({symbol: float(long_weight) for symbol in long_symbols})
        targets = {symbol: targets[symbol] for symbol in sorted(targets)}
        gross = math.fsum(abs(value) for value in targets.values())
        net = math.fsum(targets.values())
        if abs(gross - GROSS_TARGET) > TOLERANCE:
            return {}
        if abs(net) > MAXIMUM_DIRECTIONAL_NET + TOLERANCE:
            return {}
        if not any(value > 0.0 for value in targets.values()):
            return {}
        if not any(value < 0.0 for value in targets.values()):
            return {}
        return targets


def build_strategy() -> MarketStateRelativeEnsembleStrategy:
    """Canonical zero-argument factory for the exact promoted pivot candidate."""

    candidate_id = candidate_variant.ACTIVE_CANDIDATE_ID
    overrides = candidate_variant.ACTIVE_OVERRIDES
    expected = MATERIALIZED_CANDIDATE_OVERRIDES.get(candidate_id)
    if expected is None:
        raise ValueError(f"unknown materialized candidate identifier: {candidate_id}")
    if type(overrides) is not dict or overrides != expected:
        raise ValueError(f"active overrides do not match the declaration for {candidate_id}")
    return MarketStateRelativeEnsembleStrategy()
