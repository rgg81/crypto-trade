"""Team 08 causal volatility-scaled rank-persistence pivot.

The organizer supplies point-in-time pure-crypto membership and completed 8-hour bars.  At each
weekly construction this strategy removes the same-bar cross-sectional median return and measures
coin-specific continuation over distinct 21-, 63-, and 126-bar horizons.  Every horizon is scaled
by a past residual-volatility baseline.  At least two horizons must agree, disagreement is shrunk,
and excessive recent volatility can reduce but never increase the score.  This is an explicit
multi-horizon persistence model, not a sign flip or parameter variant of the terminal recoil model.

One finite built-in score dictionary crosses the public A5 boundary after every signal transform
and before selection, sizing, caps, or organizer risk.  The exact returned object alone builds a
weekly broad, equal-dollar, exactly neutral no-control portfolio.
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
SHORT_HORIZON_BARS = 21
MEDIUM_HORIZON_BARS = 63
SLOW_HORIZON_BARS = 126
RECENT_VOLATILITY_BARS = 21
BASELINE_VOLATILITY_BARS = 105
SHORT_HORIZON_WEIGHT = 0.50
MEDIUM_HORIZON_WEIGHT = 0.30
SLOW_HORIZON_WEIGHT = 0.20
HORIZON_SATURATION_Z = 3.0
MINIMUM_AGREEING_HORIZONS = 2
DISAGREEMENT_POWER = 2.0
MINIMUM_VALID_SYMBOLS = 24
MINIMUM_POSITIONS_PER_SIDE = 8
SELECTION_NUMERATOR = 1
SELECTION_DENOMINATOR = 5
GROSS_TARGET = 0.36
MAXIMUM_SYMBOL_EXPOSURE = 0.025
TOLERANCE = 1e-10

ACTIVE_FAMILY_ID = "t08-volatility-scaled-rank-persistence-v1"
ACTIVE_CANDIDATE_ID = "t08-volatility-scaled-rank-persistence-v1-base"
MATERIALIZED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    ACTIVE_CANDIDATE_ID: {},
}

_BAR_INTERVAL = pd.Timedelta(hours=BAR_INTERVAL_HOURS)
_HORIZONS = (SHORT_HORIZON_BARS, MEDIUM_HORIZON_BARS, SLOW_HORIZON_BARS)
_HORIZON_WEIGHTS = (
    SHORT_HORIZON_WEIGHT,
    MEDIUM_HORIZON_WEIGHT,
    SLOW_HORIZON_WEIGHT,
)


class ContextLike(Protocol):
    """Runtime subset of the neutral decision context consumed by Team 08."""

    decision_time: pd.Timestamp
    bars: Mapping[str, pd.DataFrame]
    funding: pd.DataFrame
    auxiliary: Mapping[str, pd.DataFrame]
    eligible_symbols: Sequence[str]


@dataclasses.dataclass(frozen=True)
class _PersistenceFeature:
    horizon_z_scores: tuple[float, float, float]
    horizon_components: tuple[float, float, float]
    recent_to_baseline_volatility: float
    horizon_agreement: float
    volatility_shrink: float
    raw_persistence_score: float


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
    return tuple(
        decision_time - offset * _BAR_INTERVAL
        for offset in range(HISTORY_RETURN_BARS + 1, 0, -1)
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


def _sample_standard_deviation(values: Sequence[float]) -> float | None:
    if len(values) < 2 or any(not math.isfinite(value) for value in values):
        return None
    mean = math.fsum(values) / len(values)
    variance = math.fsum((value - mean) ** 2 for value in values) / (len(values) - 1)
    if not math.isfinite(variance) or variance < 0.0:
        return None
    result = math.sqrt(variance)
    return float(result) if math.isfinite(result) else None


def _signed_magnitude_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    """Rank persistence magnitude within sign while preserving inactive zero scores."""

    if len(values) < MINIMUM_VALID_SYMBOLS or any(
        not math.isfinite(value) for value in values.values()
    ):
        return None
    positive = sorted(
        ((symbol, value) for symbol, value in values.items() if value > 0.0),
        key=lambda item: (item[1], item[0]),
    )
    negative = sorted(
        ((symbol, value) for symbol, value in values.items() if value < 0.0),
        key=lambda item: (-item[1], item[0]),
    )
    result = {symbol: 0.0 for symbol in sorted(values)}
    for rank, (symbol, _) in enumerate(positive, start=1):
        result[symbol] = float(rank / len(positive))
    for rank, (symbol, _) in enumerate(negative, start=1):
        result[symbol] = -float(rank / len(negative))
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


def _residual_paths(
    return_paths: Mapping[str, Sequence[float]],
) -> dict[str, tuple[float, ...]] | None:
    """Subtract the contemporaneous pure-crypto median at every completed bar."""

    if len(return_paths) < MINIMUM_VALID_SYMBOLS:
        return None
    if any(len(path) != HISTORY_RETURN_BARS for path in return_paths.values()):
        return None
    result: dict[str, list[float]] = {symbol: [] for symbol in sorted(return_paths)}
    for index in range(HISTORY_RETURN_BARS):
        cross_section = [float(return_paths[symbol][index]) for symbol in sorted(return_paths)]
        market_return = _median(cross_section)
        if market_return is None:
            return None
        for symbol in sorted(result):
            residual = float(return_paths[symbol][index]) - market_return
            if not math.isfinite(residual):
                return None
            result[symbol].append(residual)
    return {symbol: tuple(result[symbol]) for symbol in sorted(result)}


def _persistence_feature(residual_path: Sequence[float]) -> _PersistenceFeature | None:
    """Build a volatility-scaled continuation score with explicit horizon agreement."""

    if (
        len(residual_path) != HISTORY_RETURN_BARS
        or BASELINE_VOLATILITY_BARS + RECENT_VOLATILITY_BARS != HISTORY_RETURN_BARS
        or SLOW_HORIZON_BARS != HISTORY_RETURN_BARS
    ):
        return None
    baseline = residual_path[:BASELINE_VOLATILITY_BARS]
    recent = residual_path[-RECENT_VOLATILITY_BARS:]
    baseline_scale = _sample_standard_deviation(baseline)
    recent_scale = _sample_standard_deviation(recent)
    if baseline_scale is None or recent_scale is None or baseline_scale <= 1e-12:
        return None

    horizon_z_scores: list[float] = []
    horizon_components: list[float] = []
    for horizon in _HORIZONS:
        horizon_sum = math.fsum(residual_path[-horizon:])
        z_score = horizon_sum / (baseline_scale * math.sqrt(horizon))
        component = math.tanh(z_score / HORIZON_SATURATION_Z)
        if not math.isfinite(z_score) or not math.isfinite(component):
            return None
        horizon_z_scores.append(float(z_score))
        horizon_components.append(float(component))

    consensus = _median(horizon_components)
    if consensus is None:
        return None
    recent_ratio = recent_scale / baseline_scale
    volatility_shrink = min(1.0, 1.0 / max(recent_ratio, 1e-12))
    if abs(consensus) <= 1e-15:
        agreement = 0.0
        raw_score = 0.0
    else:
        direction = math.copysign(1.0, consensus)
        agreeing = tuple(component * direction > 0.0 for component in horizon_components)
        agreement_count = sum(agreeing)
        agreement = agreement_count / len(_HORIZONS)
        weighted_core = math.fsum(
            weight * component
            for weight, component in zip(_HORIZON_WEIGHTS, horizon_components, strict=True)
        )
        agreeing_weight = math.fsum(
            weight
            for weight, is_agreeing in zip(_HORIZON_WEIGHTS, agreeing, strict=True)
            if is_agreeing
        )
        if agreement_count < MINIMUM_AGREEING_HORIZONS or weighted_core * direction <= 0.0:
            raw_score = 0.0
        else:
            raw_score = (
                weighted_core
                * agreeing_weight**DISAGREEMENT_POWER
                * volatility_shrink
            )
    values = (
        *horizon_z_scores,
        *horizon_components,
        recent_ratio,
        agreement,
        volatility_shrink,
        raw_score,
    )
    if any(not math.isfinite(value) for value in values):
        return None
    return _PersistenceFeature(
        horizon_z_scores=(horizon_z_scores[0], horizon_z_scores[1], horizon_z_scores[2]),
        horizon_components=(
            horizon_components[0],
            horizon_components[1],
            horizon_components[2],
        ),
        recent_to_baseline_volatility=float(recent_ratio),
        horizon_agreement=float(agreement),
        volatility_shrink=float(volatility_shrink),
        raw_persistence_score=float(raw_score),
    )


class VolatilityScaledRankPersistenceStrategy:
    """Trade persistent residual leaders and laggards across three horizons."""

    @staticmethod
    def _validate_seed(seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed != FROZEN_SEED:
            raise ValueError(f"Team 08 requires frozen seed {FROZEN_SEED}")

    def preconstruction_snapshot(
        self,
        context: ContextLike,
        *,
        seed: int,
        decision_time: pd.Timestamp | None = None,
    ) -> PreconstructionSnapshot | None:
        """Build final persistence ranks from exact completed pure-crypto histories."""

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
        residuals = _residual_paths(return_paths)
        if residuals is None:
            return None

        raw_scores: dict[str, float] = {}
        for symbol in sorted(residuals):
            feature = _persistence_feature(residuals[symbol])
            if feature is None:
                return None
            raw_scores[symbol] = feature.raw_persistence_score
        final_scores = _signed_magnitude_ranks(raw_scores)
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
            raise ValueError("score_boundary returned invalid or mutated scores")
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
        positive = sorted(
            (symbol for symbol, value in scores.items() if value > 0.0),
            key=lambda symbol: (scores[symbol], symbol),
        )
        negative = sorted(
            (symbol for symbol, value in scores.items() if value < 0.0),
            key=lambda symbol: (scores[symbol], symbol),
        )
        if count <= 0 or len(positive) < count or len(negative) < count:
            return {}
        short_symbols = tuple(negative[:count])
        long_symbols = tuple(positive[-count:])
        if set(short_symbols) & set(long_symbols):
            return {}
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
        return targets


def build_strategy() -> VolatilityScaledRankPersistenceStrategy:
    """Canonical zero-argument factory for the exact second-pivot candidate."""

    candidate_id = candidate_variant.ACTIVE_CANDIDATE_ID
    overrides = candidate_variant.ACTIVE_OVERRIDES
    expected = MATERIALIZED_CANDIDATE_OVERRIDES.get(candidate_id)
    if expected is None:
        raise ValueError(f"unknown materialized candidate identifier: {candidate_id}")
    if type(overrides) is not dict or overrides != expected:
        raise ValueError(f"active overrides do not match the declaration for {candidate_id}")
    return VolatilityScaledRankPersistenceStrategy()
