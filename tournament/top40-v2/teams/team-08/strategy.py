"""Team 08 causal compressed-shock recoil pivot.

The organizer supplies point-in-time pure-crypto membership and completed 8-hour bars.  At each
weekly construction the strategy subtracts the same-bar cross-sectional median return, measures
whether each coin's idiosyncratic volatility compressed before the latest three-bar shock, and
scores a durable recoil opposite that shock.  Compression, multi-bar direction agreement, the
median aligned shock component, and path roughness all enter before the final deterministic
cross-sectional rank.  This is not the negative of the retired dispersion-release score: it has
new feature lineage, no dispersion-state switch, no continuation sleeve, and no common direction.

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
BASELINE_VOLATILITY_BARS = 84
COMPRESSION_VOLATILITY_BARS = 21
SHOCK_BARS = 3
COMPRESSION_RATIO_FLOOR = 0.45
COMPRESSION_RATIO_CEILING = 1.00
SHOCK_SATURATION_Z = 2.50
MINIMUM_DIRECTION_AGREEMENT_NUMERATOR = 2
MINIMUM_DIRECTION_AGREEMENT_DENOMINATOR = 3
MINIMUM_VALID_SYMBOLS = 24
MINIMUM_POSITIONS_PER_SIDE = 8
SELECTION_NUMERATOR = 1
SELECTION_DENOMINATOR = 5
GROSS_TARGET = 0.36
MAXIMUM_SYMBOL_EXPOSURE = 0.025
TOLERANCE = 1e-10

ACTIVE_FAMILY_ID = "t08-compressed-shock-recoil-v1"
ACTIVE_CANDIDATE_ID = "t08-compressed-shock-recoil-v1-base"
MATERIALIZED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    ACTIVE_CANDIDATE_ID: {},
}

_BAR_INTERVAL = pd.Timedelta(hours=BAR_INTERVAL_HOURS)


class ContextLike(Protocol):
    """Runtime subset of the neutral decision context consumed by Team 08."""

    decision_time: pd.Timestamp
    bars: Mapping[str, pd.DataFrame]
    funding: pd.DataFrame
    auxiliary: Mapping[str, pd.DataFrame]
    eligible_symbols: Sequence[str]


@dataclasses.dataclass(frozen=True)
class _RecoilFeature:
    compression_ratio: float
    signed_shock_z: float
    direction_agreement: float
    durable_shock_z: float
    path_roughness: float
    raw_recoil_score: float


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
    """Subtract the contemporaneous cross-sectional median at every completed bar."""

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


def _recoil_feature(residual_path: Sequence[float]) -> _RecoilFeature | None:
    """Score a durable recent shock for recoil only when it follows lower volatility."""

    required = BASELINE_VOLATILITY_BARS + COMPRESSION_VOLATILITY_BARS + SHOCK_BARS
    if len(residual_path) != HISTORY_RETURN_BARS or required > HISTORY_RETURN_BARS:
        return None
    baseline_stop = len(residual_path) - COMPRESSION_VOLATILITY_BARS - SHOCK_BARS
    baseline_start = baseline_stop - BASELINE_VOLATILITY_BARS
    compression_stop = len(residual_path) - SHOCK_BARS
    baseline = residual_path[baseline_start:baseline_stop]
    compression = residual_path[baseline_stop:compression_stop]
    shock = residual_path[compression_stop:]
    baseline_scale = _sample_standard_deviation(baseline)
    compression_scale = _sample_standard_deviation(compression)
    if (
        baseline_scale is None
        or compression_scale is None
        or baseline_scale <= 1e-12
    ):
        return None

    compression_ratio = compression_scale / baseline_scale
    compression_strength = float(
        max(
            0.0,
            min(
                1.0,
                (COMPRESSION_RATIO_CEILING - compression_ratio)
                / (COMPRESSION_RATIO_CEILING - COMPRESSION_RATIO_FLOOR),
            ),
        )
    )
    shock_sum = math.fsum(shock)
    if not math.isfinite(shock_sum) or abs(shock_sum) <= 1e-15:
        return _RecoilFeature(
            compression_ratio=float(compression_ratio),
            signed_shock_z=0.0,
            direction_agreement=0.0,
            durable_shock_z=0.0,
            path_roughness=1.0,
            raw_recoil_score=0.0,
        )

    direction = math.copysign(1.0, shock_sum)
    aligned = tuple(direction * value / baseline_scale for value in shock)
    agreement_count = sum(value > 0.0 for value in aligned)
    agreement = agreement_count / SHOCK_BARS
    minimum_agreement = (
        MINIMUM_DIRECTION_AGREEMENT_NUMERATOR / MINIMUM_DIRECTION_AGREEMENT_DENOMINATOR
    )
    signed_shock_z = shock_sum / (baseline_scale * math.sqrt(SHOCK_BARS))
    aligned_median = _median(aligned)
    absolute_path = math.fsum(abs(value) for value in shock)
    path_roughness = absolute_path / abs(shock_sum)
    if (
        aligned_median is None
        or aligned_median <= 0.0
        or agreement + TOLERANCE < minimum_agreement
        or not math.isfinite(signed_shock_z)
        or not math.isfinite(path_roughness)
        or path_roughness < 1.0 - TOLERANCE
    ):
        raw_score = 0.0
        durable_shock_z = 0.0
    else:
        durable_shock_z = min(
            abs(signed_shock_z),
            float(aligned_median) * math.sqrt(SHOCK_BARS),
        )
        shock_strength = math.tanh(durable_shock_z / SHOCK_SATURATION_Z)
        raw_score = (
            -direction
            * compression_strength
            * shock_strength
            * agreement**2
            / path_roughness
        )
    if not all(
        math.isfinite(value)
        for value in (
            compression_ratio,
            signed_shock_z,
            agreement,
            durable_shock_z,
            raw_score,
        )
    ):
        return None
    return _RecoilFeature(
        compression_ratio=float(compression_ratio),
        signed_shock_z=float(signed_shock_z),
        direction_agreement=float(agreement),
        durable_shock_z=float(durable_shock_z),
        path_roughness=float(path_roughness),
        raw_recoil_score=float(raw_score),
    )


def _signed_magnitude_ranks(values: Mapping[str, float]) -> dict[str, float] | None:
    """Rank recoil magnitudes within sign while preserving inactive scores at exactly zero."""

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


class CompressedShockRecoilStrategy:
    """Fade durable idiosyncratic shocks that emerge from lower-volatility setups."""

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
        """Build final recoil ranks from exact completed pure-crypto histories."""

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
            feature = _recoil_feature(residuals[symbol])
            if feature is not None:
                raw_scores[symbol] = feature.raw_recoil_score
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
        long_symbols = tuple(positive[-count:])
        short_symbols = tuple(negative[:count])
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


def build_strategy() -> CompressedShockRecoilStrategy:
    """Canonical zero-argument factory for the exact first-pivot candidate."""

    candidate_id = candidate_variant.ACTIVE_CANDIDATE_ID
    overrides = candidate_variant.ACTIVE_OVERRIDES
    expected = MATERIALIZED_CANDIDATE_OVERRIDES.get(candidate_id)
    if expected is None:
        raise ValueError(f"unknown materialized candidate identifier: {candidate_id}")
    if type(overrides) is not dict or overrides != expected:
        raise ValueError(f"active overrides do not match the declaration for {candidate_id}")
    return CompressedShockRecoilStrategy()
