"""Team 06 deterministic balanced trend/reversal strategy.

The central evaluator owns membership, fills, costs, funding, positions, risk actions, and PnL.
This module consumes canonical RangeIndex bar frames containing ``open_time`` and ``close`` and
returns signed unlevered targets.  A row is available only after its complete 8-hour interval:
``open_time + 8h <= decision_time``.

Every finite transformed candidate score crosses the public prospective score boundary exactly
once, before selection, weight caps, or risk.  The object returned by that boundary is the score
dictionary used by portfolio construction.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any, Protocol

import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary


FROZEN_SEED = 20260801
BAR_INTERVAL_HOURS = 8
REBALANCE_HOUR_UTC = 0
SLOW_LOOKBACK_BARS = 90
FAST_LOOKBACK_BARS = 21
MOMENTUM_LAG_BARS = 3
REVERSAL_LOOKBACK_BARS = 6
VOLATILITY_LOOKBACK_BARS = 60
ANNUALIZATION_BARS = 3 * 365
VOLATILITY_FLOOR = 0.20
MINIMUM_VALID_SYMBOLS = 12
MINIMUM_POSITIONS_PER_SIDE = 4
SELECTION_FRACTION = 0.25
BASE_GROSS_EXPOSURE = 0.48
MAXIMUM_ABS_NET_EXPOSURE = 0.04
MAXIMUM_SYMBOL_EXPOSURE = 0.07
MAXIMUM_STALENESS_HOURS = 16
SLOW_TREND_WEIGHT = 0.65
FAST_TREND_WEIGHT = 0.35
CHOP_TREND_MIX = 0.35
DIRECTIONAL_TREND_MIX = 0.80
DIRECTION_FULL_SCALE_RETURN = 0.15
VOLATILITY_SCORE_PENALTY = 0.10


class ContextLike(Protocol):
    """Runtime subset of the neutral ``DecisionContext`` used by this strategy."""

    decision_time: pd.Timestamp
    bars: Mapping[str, pd.DataFrame]
    funding: pd.DataFrame
    auxiliary: Mapping[str, pd.DataFrame]
    eligible_symbols: Sequence[str]


@dataclasses.dataclass(frozen=True)
class _RawFeatures:
    slow: float
    fast: float
    reversal: float
    annualized_volatility: float
    unscaled_slow_return: float


@dataclasses.dataclass(frozen=True)
class PreconstructionSnapshot:
    """Immutable all-candidate scores before top/bottom selection and exposure sizing."""

    decision_time: pd.Timestamp
    scores: tuple[tuple[str, float], ...]
    market_slow_return: float

    def score_map(self) -> dict[str, float]:
        return dict(self.scores)


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _datetime_values(values: Any) -> pd.DatetimeIndex:
    """Parse normalized timestamps and common integer epoch encodings deterministically."""

    series = pd.Series(values)
    non_null = series.dropna()
    unit: str | None = None
    if not non_null.empty and pd.api.types.is_numeric_dtype(non_null.dtype):
        magnitude = abs(float(non_null.iloc[0]))
        if magnitude >= 1.0e17:
            unit = "ns"
        elif magnitude >= 1.0e14:
            unit = "us"
        elif magnitude >= 1.0e11:
            unit = "ms"
        else:
            unit = "s"
    return pd.DatetimeIndex(pd.to_datetime(series, utc=True, errors="coerce", unit=unit))


def _closed_close_values(
    frame: pd.DataFrame, decision_time: pd.Timestamp
) -> tuple[list[float], pd.Timestamp] | None:
    """Return canonical closes whose full 8-hour bars have ended by the boundary."""

    if (
        not isinstance(frame, pd.DataFrame)
        or frame.empty
        or not isinstance(frame.index, pd.RangeIndex)
        or "open_time" not in frame.columns
        or "close" not in frame.columns
    ):
        return None

    open_times = _datetime_values(frame["open_time"])
    close_times = open_times + pd.Timedelta(hours=BAR_INTERVAL_HOURS)
    closes = pd.to_numeric(frame["close"], errors="coerce").reset_index(drop=True)
    table = pd.DataFrame(
        {"open_time": open_times, "close_time": close_times, "close": closes}
    )
    table = table.loc[
        table["open_time"].notna()
        & table["close_time"].notna()
        & (table["close_time"] <= decision_time)
    ]
    table = table.sort_values("open_time", kind="mergesort").drop_duplicates(
        "open_time", keep="last"
    )
    if table.empty:
        return None

    last_time = _utc_timestamp(table["close_time"].iloc[-1])
    age_hours = (decision_time - last_time).total_seconds() / 3600.0
    if age_hours < 0.0 or age_hours > MAXIMUM_STALENESS_HOURS:
        return None

    values: list[float] = []
    for raw_value in table["close"]:
        value = float(raw_value)
        if not math.isfinite(value) or value <= 0.0:
            return None
        values.append(value)
    return values, last_time


def _sample_annualized_volatility(values: Sequence[float]) -> float | None:
    required = VOLATILITY_LOOKBACK_BARS + 1
    if len(values) < required:
        return None
    tail = values[-required:]
    log_returns = [math.log(current / previous) for previous, current in zip(tail, tail[1:])]
    if len(log_returns) < 2:
        return None
    mean = sum(log_returns) / len(log_returns)
    variance = sum((value - mean) ** 2 for value in log_returns) / (len(log_returns) - 1)
    annualized = math.sqrt(max(0.0, variance) * ANNUALIZATION_BARS)
    return annualized if math.isfinite(annualized) else None


def _raw_features(
    values: Sequence[float], *, slow_lookback_bars: int
) -> _RawFeatures | None:
    required = slow_lookback_bars + MOMENTUM_LAG_BARS + 1
    if len(values) < required:
        return None
    volatility = _sample_annualized_volatility(values)
    if volatility is None:
        return None

    lagged_end = values[-(MOMENTUM_LAG_BARS + 1)]
    slow_start = values[-(slow_lookback_bars + MOMENTUM_LAG_BARS + 1)]
    fast_start = values[-(FAST_LOOKBACK_BARS + MOMENTUM_LAG_BARS + 1)]
    reversal_start = values[-(REVERSAL_LOOKBACK_BARS + 1)]
    latest = values[-1]
    slow_return = math.log(lagged_end / slow_start)
    fast_return = math.log(lagged_end / fast_start)
    reversal_return = -math.log(latest / reversal_start)
    denominator = max(VOLATILITY_FLOOR, volatility)
    return _RawFeatures(
        slow=slow_return / denominator,
        fast=fast_return / denominator,
        reversal=reversal_return / denominator,
        annualized_volatility=volatility,
        unscaled_slow_return=slow_return,
    )


def _centered_ranks(values: Mapping[str, float]) -> dict[str, float]:
    """Map finite values to deterministic average-tie ranks in [-1, 1]."""

    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    if count == 0:
        return {}
    if count == 1:
        return {ordered[0][0]: 0.0}

    result: dict[str, float] = {}
    cursor = 0
    while cursor < count:
        end = cursor + 1
        while end < count and ordered[end][1] == ordered[cursor][1]:
            end += 1
        average_index = (cursor + end - 1) / 2.0
        centered = 2.0 * average_index / (count - 1) - 1.0
        for position in range(cursor, end):
            result[ordered[position][0]] = centered
        cursor = end
    return result


def _median(values: Sequence[float]) -> float:
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2.0


def _clip(value: float, lower: float, upper: float) -> float:
    return min(upper, max(lower, value))


class BalancedTrendReversalStrategy:
    """Fixed cross-sectional family with a strict preconstruction scoring boundary."""

    def __init__(
        self,
        *,
        slow_lookback_bars: int = SLOW_LOOKBACK_BARS,
        selection_fraction: float = SELECTION_FRACTION,
    ) -> None:
        if (
            isinstance(slow_lookback_bars, bool)
            or not isinstance(slow_lookback_bars, int)
            or slow_lookback_bars <= FAST_LOOKBACK_BARS
        ):
            raise ValueError("slow_lookback_bars must be an integer above fast lookback")
        if isinstance(selection_fraction, bool) or not isinstance(
            selection_fraction, (int, float)
        ):
            raise ValueError("selection_fraction must be numeric")
        if not math.isfinite(selection_fraction) or not 0.0 < selection_fraction < 0.5:
            raise ValueError("selection_fraction must be finite and in (0, 0.5)")
        self._slow_lookback_bars = slow_lookback_bars
        self._selection_fraction = float(selection_fraction)

    @staticmethod
    def _validate_seed(seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed != FROZEN_SEED:
            raise ValueError(f"Team 06 requires frozen seed {FROZEN_SEED}")

    def preconstruction_snapshot(
        self, context: ContextLike, *, seed: int
    ) -> PreconstructionSnapshot:
        """Score every valid point-in-time member before any selection or sizing."""

        self._validate_seed(seed)
        decision_time = _utc_timestamp(context.decision_time)
        features: dict[str, _RawFeatures] = {}
        eligible = sorted(
            {
                symbol
                for symbol in context.eligible_symbols
                if isinstance(symbol, str) and symbol and not symbol.startswith("__")
            }
        )
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            closed = _closed_close_values(frame, decision_time)
            if closed is None:
                continue
            feature = _raw_features(
                closed[0], slow_lookback_bars=self._slow_lookback_bars
            )
            if feature is not None:
                features[symbol] = feature

        if not features:
            return PreconstructionSnapshot(decision_time, (), 0.0)

        slow_rank = _centered_ranks({key: value.slow for key, value in features.items()})
        fast_rank = _centered_ranks({key: value.fast for key, value in features.items()})
        reversal_rank = _centered_ranks(
            {key: value.reversal for key, value in features.items()}
        )
        volatility_rank = _centered_ranks(
            {key: value.annualized_volatility for key, value in features.items()}
        )
        market_slow_return = _median(
            [value.unscaled_slow_return for value in features.values()]
        )
        direction_strength = _clip(
            abs(market_slow_return) / DIRECTION_FULL_SCALE_RETURN, 0.0, 1.0
        )
        trend_mix = CHOP_TREND_MIX + direction_strength * (
            DIRECTIONAL_TREND_MIX - CHOP_TREND_MIX
        )

        scores: list[tuple[str, float]] = []
        for symbol in sorted(features):
            trend = SLOW_TREND_WEIGHT * slow_rank[symbol] + FAST_TREND_WEIGHT * fast_rank[symbol]
            score = (
                trend_mix * trend
                + (1.0 - trend_mix) * reversal_rank[symbol]
                - VOLATILITY_SCORE_PENALTY * volatility_rank[symbol]
            )
            if not math.isfinite(score):
                raise ValueError(f"non-finite preconstruction score for {symbol}")
            scores.append((symbol, float(score)))
        return PreconstructionSnapshot(
            decision_time=decision_time,
            scores=tuple(scores),
            market_slow_return=float(market_slow_return),
        )

    @staticmethod
    def _apply_public_score_boundary(
        snapshot: PreconstructionSnapshot,
    ) -> dict[str, float]:
        """Call the direct public binding once and validate its construction input."""

        scores = {symbol: float(value) for symbol, value in snapshot.scores}
        if type(scores) is not dict or any(
            type(symbol) is not str or type(value) is not float or not math.isfinite(value)
            for symbol, value in scores.items()
        ):
            raise ValueError("score_boundary input must be a finite built-in dict[str, float]")

        bounded_scores = score_boundary(scores)
        if type(bounded_scores) is not dict or set(bounded_scores) != set(scores):
            raise ValueError("score_boundary must return a built-in dict with unchanged keys")
        if any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            for value in bounded_scores.values()
        ):
            raise ValueError("score_boundary returned a non-finite or non-numeric score")
        return bounded_scores

    def preconstruction_scores(
        self, context: ContextLike, *, seed: int
    ) -> Mapping[str, float]:
        """Organizer-facing public boundary; no selection has happened yet."""

        snapshot = self.preconstruction_snapshot(context, seed=seed)
        return self._apply_public_score_boundary(snapshot)

    def target_weights(
        self, context: ContextLike, *, seed: int
    ) -> Mapping[str, float] | None:
        self._validate_seed(seed)
        decision_time = _utc_timestamp(context.decision_time)
        if (
            decision_time.hour != REBALANCE_HOUR_UTC
            or decision_time.minute != 0
            or decision_time.second != 0
        ):
            return None

        snapshot = self.preconstruction_snapshot(context, seed=seed)
        scores = self._apply_public_score_boundary(snapshot)
        if len(scores) < MINIMUM_VALID_SYMBOLS:
            return {}

        count = max(
            MINIMUM_POSITIONS_PER_SIDE,
            int(math.floor(len(scores) * self._selection_fraction)),
        )
        count = min(count, len(scores) // 2)
        if count < MINIMUM_POSITIONS_PER_SIDE:
            return {}

        ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
        short_symbols = ordered[:count]
        long_symbols = ordered[-count:]
        directional_tilt = MAXIMUM_ABS_NET_EXPOSURE * _clip(
            snapshot.market_slow_return / DIRECTION_FULL_SCALE_RETURN, -1.0, 1.0
        )
        long_budget = min(
            (BASE_GROSS_EXPOSURE + directional_tilt) / 2.0,
            count * MAXIMUM_SYMBOL_EXPOSURE,
        )
        short_budget = min(
            (BASE_GROSS_EXPOSURE - directional_tilt) / 2.0,
            count * MAXIMUM_SYMBOL_EXPOSURE,
        )
        long_weight = long_budget / count
        short_weight = short_budget / count

        targets = {symbol: -float(short_weight) for symbol in short_symbols}
        targets.update({symbol: float(long_weight) for symbol in long_symbols})
        return {symbol: targets[symbol] for symbol in sorted(targets)}


def build_strategy() -> BalancedTrendReversalStrategy:
    """Canonical factory; the organizer normally calls it without arguments."""

    return BalancedTrendReversalStrategy()


def build_parameterized_strategy(
    *,
    slow_lookback_bars: int = SLOW_LOOKBACK_BARS,
    selection_fraction: float = SELECTION_FRACTION,
) -> BalancedTrendReversalStrategy:
    """Explicit constructor used only by preregistered byte-distinct neighbor wrappers."""

    return BalancedTrendReversalStrategy(
        slow_lookback_bars=slow_lookback_bars,
        selection_fraction=selection_fraction,
    )
