"""Team 05 final pivot-02: liquidity-depth migration (LDM).

LDM measures whether a native-crypto contract's unsigned intrabar range is becoming smaller or
larger per unit of contemporaneous cross-sectional quote-volume share.  Falling range-per-share
means market depth is improving and receives a high long-desirability score; rising impact means
depth is deteriorating and receives a low score.

The mechanism uses no price direction, close location, taker-side flow, funding, residual return,
beta, shock, trend, reversal, volatility rank, diffusion, or lead-lag input.  Universe
classification is organizer-owned: Amendment 0006 supplies only point-in-time native-crypto
members and this module never infers asset class from ticker text.
"""

from __future__ import annotations

import dataclasses
import json
import math
import statistics
from collections.abc import Mapping

import candidate_variant
import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy
from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

CANONICAL_SEED = 20260801
_RESERVED_SYMBOL = "__crypto_trade_rebalance__"


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    """Complete fixed material configuration for the final LDM core."""

    algorithm_id: str = "team05-ldm-v1"
    rebalance_anchor_utc: str = "1970-01-01T00:00:00Z"
    bar_interval_hours: int = 8
    decision_interval_hours: int = 168
    history_bars: int = 126
    baseline_bars: int = 105
    recent_bars: int = 21
    maximum_latest_staleness_hours: int = 12
    minimum_symbols: int = 12
    minimum_valid_baseline_bars: int = 95
    minimum_valid_recent_bars: int = 19
    volume_share_floor: float = 1e-5
    maximum_log_range: float = 0.70
    maximum_abs_log_impact_ratio: float = 4.0
    minimum_score_span: float = 0.50
    selection_fraction: float = 0.20
    minimum_side_symbols: int = 5
    maximum_side_symbols: int = 8
    minimum_raw_separation: float = 0.10
    target_gross: float = 0.36
    maximum_symbol_weight: float = 0.04
    maximum_abs_net: float = 1e-12

    def __post_init__(self) -> None:
        if self.algorithm_id != "team05-ldm-v1":
            raise ValueError("unexpected algorithm_id")
        integer_fields = (
            self.bar_interval_hours,
            self.decision_interval_hours,
            self.history_bars,
            self.baseline_bars,
            self.recent_bars,
            self.maximum_latest_staleness_hours,
            self.minimum_symbols,
            self.minimum_valid_baseline_bars,
            self.minimum_valid_recent_bars,
            self.minimum_side_symbols,
            self.maximum_side_symbols,
        )
        if any(type(value) is not int or value <= 0 for value in integer_fields):
            raise ValueError("integer configuration fields must be positive")
        if self.decision_interval_hours % self.bar_interval_hours:
            raise ValueError("decision interval must be a multiple of the bar interval")
        if self.history_bars != self.baseline_bars + self.recent_bars:
            raise ValueError("history must equal the disjoint baseline and recent windows")
        if self.minimum_valid_baseline_bars > self.baseline_bars:
            raise ValueError("baseline validity floor exceeds its window")
        if self.minimum_valid_recent_bars > self.recent_bars:
            raise ValueError("recent validity floor exceeds its window")
        if self.minimum_symbols < 2 * self.minimum_side_symbols:
            raise ValueError("minimum universe cannot support disjoint sleeves")
        if self.maximum_side_symbols < self.minimum_side_symbols:
            raise ValueError("maximum sleeve size cannot be below the minimum")
        if not 0.0 < self.selection_fraction <= 0.5:
            raise ValueError("selection fraction must be inside (0, 0.5]")
        finite_positive = (
            self.volume_share_floor,
            self.maximum_log_range,
            self.maximum_abs_log_impact_ratio,
            self.minimum_score_span,
            self.minimum_raw_separation,
            self.target_gross,
            self.maximum_symbol_weight,
            self.maximum_abs_net,
        )
        if any(not math.isfinite(value) or value <= 0.0 for value in finite_positive):
            raise ValueError("continuous configuration fields must be positive and finite")
        if self.volume_share_floor >= 1.0 / self.minimum_symbols:
            raise ValueError("volume-share floor cannot dominate the minimum cross section")
        if self.target_gross > 1.0 or self.maximum_symbol_weight > 0.10:
            raise ValueError("gross exposure or symbol cap exceeds the frozen range")
        if self.target_gross / (2 * self.minimum_side_symbols) > self.maximum_symbol_weight:
            raise ValueError("minimum sleeve size cannot implement the target gross")


BASE_PARAMETERS = StrategyParameters()

PREREGISTERED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    "team05-ldm-pivot02-core-v1": {},
}

PREREGISTERED_RISK_POLICY_TEMPLATES: dict[str, str] = {
    "team05-ldm-pivot02-core-v1": "risk_policies/no-control.json",
}


@dataclasses.dataclass(frozen=True)
class PreconstructionScore:
    """Auditable depth-migration record produced before portfolio construction."""

    symbol: str
    score: float
    raw_depth_improvement: float
    baseline_impact: float
    recent_impact: float


def _as_utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("decision_time must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _parse_open_times(raw: pd.Series) -> pd.DatetimeIndex | None:
    if pd.api.types.is_bool_dtype(raw.dtype):
        return None
    try:
        if pd.api.types.is_numeric_dtype(raw.dtype):
            parsed = pd.to_datetime(raw, unit="ms", utc=True, errors="coerce")
        else:
            parsed = pd.to_datetime(raw, utc=True, errors="coerce")
    except (TypeError, ValueError, OverflowError):
        return None
    if bool(parsed.isna().any()):
        return None
    return pd.DatetimeIndex(parsed)


def _numeric_or_nan(values: list[object]) -> np.ndarray:
    result: list[float] = []
    for value in values:
        if isinstance(value, (bool, np.bool_)):
            result.append(math.nan)
            continue
        try:
            result.append(float(value))
        except (TypeError, ValueError, OverflowError):
            result.append(math.nan)
    return np.asarray(result, dtype=float)


def _closed_bar_suffix(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame | None:
    """Return an exact contiguous timestamp suffix; invalid values remain unavailable."""
    required = {"open_time", "high", "low", "quote_volume"}
    if (
        not isinstance(frame, pd.DataFrame)
        or not isinstance(frame.index, pd.RangeIndex)
        or not required.issubset(frame.columns)
    ):
        return None
    open_times = _parse_open_times(frame["open_time"])
    if open_times is None:
        return None
    interval = pd.Timedelta(hours=parameters.bar_interval_hours)
    close_times = open_times + interval
    closed_mask = close_times <= decision_time
    if not bool(closed_mask.any()):
        return None
    admitted_times = close_times[closed_mask]
    if admitted_times.duplicated().any():
        return None
    closed = pd.DataFrame(
        {
            "high": _numeric_or_nan(frame.loc[closed_mask, "high"].tolist()),
            "low": _numeric_or_nan(frame.loc[closed_mask, "low"].tolist()),
            "quote_volume": _numeric_or_nan(frame.loc[closed_mask, "quote_volume"].tolist()),
        },
        index=admitted_times,
    ).sort_index(kind="mergesort")
    latest_close = closed.index[-1]
    latest_gap = decision_time - latest_close
    if latest_gap < pd.Timedelta(0) or latest_gap > pd.Timedelta(
        hours=parameters.maximum_latest_staleness_hours
    ):
        return None
    expected = pd.date_range(
        end=latest_close,
        periods=parameters.history_bars,
        freq=interval,
    )
    if not bool(expected.isin(closed.index).all()):
        return None
    suffix = closed.reindex(expected)
    if len(suffix) != parameters.history_bars or suffix.index.has_duplicates:
        return None
    # Invalid field values remain NaN.  Later explicit window counts prevent them from being
    # imputed or turned into artificial liquidity deterioration.
    return suffix


def _modal_grid_histories(
    context: DecisionContext,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> dict[str, pd.DataFrame]:
    eligible_raw = tuple(context.eligible_symbols)
    if any(type(symbol) is not str or not symbol for symbol in eligible_raw):
        return {}
    if len(eligible_raw) != len(set(eligible_raw)):
        return {}
    eligible = sorted(symbol for symbol in eligible_raw if symbol != _RESERVED_SYMBOL)
    histories: dict[str, pd.DataFrame] = {}
    groups: dict[tuple[int, ...], list[str]] = {}
    for symbol in eligible:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _closed_bar_suffix(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if history is None:
            continue
        histories[symbol] = history
        signature = tuple(int(value) for value in history.index.asi8)
        groups.setdefault(signature, []).append(symbol)
    if not groups:
        return {}
    selected_signature = min(
        groups,
        key=lambda signature: (-len(groups[signature]), -signature[-1], signature),
    )
    symbols = sorted(groups[selected_signature])
    if len(symbols) < parameters.minimum_symbols:
        return {}
    return {symbol: histories[symbol] for symbol in symbols}


def _centered_fractional_ranks(values: Mapping[str, float]) -> dict[str, float]:
    """Average-rank exact ties and map ranks deterministically into [-1, 1]."""
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    if count == 0:
        return {}
    if count == 1:
        return {ordered[0][0]: 0.0}
    ranks: dict[str, float] = {}
    start = 0
    while start < count:
        end = start + 1
        while end < count and ordered[end][1] == ordered[start][1]:
            end += 1
        average_zero_based_rank = (start + end - 1) / 2.0
        centered_rank = 2.0 * average_zero_based_rank / (count - 1) - 1.0
        for index in range(start, end):
            ranks[ordered[index][0]] = centered_rank
        start = end
    return ranks


def preconstruction_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = BASE_PARAMETERS,
) -> dict[str, PreconstructionScore]:
    """Estimate recent versus baseline unsigned range-per-volume-share migration."""
    decision_time = _as_utc(context.decision_time)
    histories = _modal_grid_histories(
        context,
        decision_time=decision_time,
        parameters=parameters,
    )
    if len(histories) < parameters.minimum_symbols:
        return {}
    symbols = sorted(histories)
    high = np.vstack([histories[symbol]["high"].to_numpy(dtype=float) for symbol in symbols])
    low = np.vstack([histories[symbol]["low"].to_numpy(dtype=float) for symbol in symbols])
    volume = np.vstack(
        [histories[symbol]["quote_volume"].to_numpy(dtype=float) for symbol in symbols]
    )
    valid = (
        np.isfinite(high)
        & np.isfinite(low)
        & np.isfinite(volume)
        & (high > low)
        & (low > 0.0)
        & (volume > 0.0)
    )
    log_range = np.full(high.shape, np.nan, dtype=float)
    log_range[valid] = np.log(high[valid]) - np.log(low[valid])
    valid &= (
        np.isfinite(log_range) & (log_range > 0.0) & (log_range <= parameters.maximum_log_range)
    )

    impact = np.full(high.shape, np.nan, dtype=float)
    for column in range(parameters.history_bars):
        column_valid = valid[:, column]
        if int(column_valid.sum()) < parameters.minimum_symbols:
            continue
        total_volume = float(volume[column_valid, column].sum())
        if not math.isfinite(total_volume) or total_volume <= 0.0:
            continue
        shares = volume[column_valid, column] / total_volume
        denominators = np.maximum(shares, parameters.volume_share_floor)
        impact[column_valid, column] = log_range[column_valid, column] / denominators

    raw_improvement: dict[str, float] = {}
    baseline_impact: dict[str, float] = {}
    recent_impact: dict[str, float] = {}
    baseline_end = parameters.baseline_bars
    for row_index, symbol in enumerate(symbols):
        baseline = impact[row_index, :baseline_end]
        recent = impact[row_index, baseline_end:]
        finite_baseline = baseline[np.isfinite(baseline) & (baseline > 0.0)]
        finite_recent = recent[np.isfinite(recent) & (recent > 0.0)]
        if len(finite_baseline) < parameters.minimum_valid_baseline_bars:
            continue
        if len(finite_recent) < parameters.minimum_valid_recent_bars:
            continue
        baseline_value = float(np.median(finite_baseline))
        recent_value = float(np.median(finite_recent))
        if (
            not math.isfinite(baseline_value)
            or not math.isfinite(recent_value)
            or baseline_value <= 0.0
            or recent_value <= 0.0
        ):
            continue
        raw_value = math.log(baseline_value / recent_value)
        if not math.isfinite(raw_value) or abs(raw_value) > parameters.maximum_abs_log_impact_ratio:
            continue
        raw_improvement[symbol] = raw_value
        baseline_impact[symbol] = baseline_value
        recent_impact[symbol] = recent_value
    if len(raw_improvement) < parameters.minimum_symbols:
        return {}

    ranks = _centered_fractional_ranks(raw_improvement)
    return {
        symbol: PreconstructionScore(
            symbol=symbol,
            score=float(ranks[symbol]),
            raw_depth_improvement=float(raw_improvement[symbol]),
            baseline_impact=float(baseline_impact[symbol]),
            recent_impact=float(recent_impact[symbol]),
        )
        for symbol in sorted(raw_improvement)
    }


def candidate_score_values(
    scores: Mapping[str, PreconstructionScore],
) -> dict[str, float]:
    """Expose the exact A5 score boundary and return its construction inputs."""
    if any(type(symbol) is not str or not symbol for symbol in scores):
        return {}
    ordered_symbols = sorted(scores)
    for symbol in ordered_symbols:
        row = scores[symbol]
        if not isinstance(row, PreconstructionScore) or row.symbol != symbol:
            return {}
        values = (
            row.score,
            row.raw_depth_improvement,
            row.baseline_impact,
            row.recent_impact,
        )
        if any(type(value) is not float or not math.isfinite(value) for value in values):
            return {}
        if not -1.0 <= row.score <= 1.0:
            return {}
        if row.baseline_impact <= 0.0 or row.recent_impact <= 0.0:
            return {}

    boundary_input = {symbol: float(scores[symbol].score) for symbol in ordered_symbols}
    boundary_output = score_boundary(boundary_input)
    if not isinstance(boundary_output, Mapping) or set(boundary_output) != set(boundary_input):
        return {}
    result: dict[str, float] = {}
    for symbol in ordered_symbols:
        value = boundary_output[symbol]
        if type(value) is not float or not math.isfinite(value) or not -1.0 <= value <= 1.0:
            return {}
        result[symbol] = value
    return result


def candidate_score_payload_bytes(
    scores: Mapping[str, PreconstructionScore],
) -> bytes:
    """Return canonical Team05 A5 audit bytes, or empty bytes for malformed input."""
    values = candidate_score_values(scores)
    if scores and len(values) != len(scores):
        return b""
    payload = {
        "schema_version": 1,
        "scores": [{"score": values[symbol], "symbol": symbol} for symbol in sorted(values)],
    }
    return (
        json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def scores_to_target_weights(
    scores: Mapping[str, PreconstructionScore],
    *,
    parameters: StrategyParameters = BASE_PARAMETERS,
) -> dict[str, float]:
    """Construct an equal-weight, dollar-balanced book from A5-returned scores."""
    adapted_values = candidate_score_values(scores)
    if len(scores) < parameters.minimum_symbols or len(adapted_values) != len(scores):
        return {}
    score_span = max(adapted_values.values()) - min(adapted_values.values())
    if score_span < parameters.minimum_score_span:
        return {}
    count = len(adapted_values)
    side_count = min(
        parameters.maximum_side_symbols,
        max(parameters.minimum_side_symbols, math.ceil(parameters.selection_fraction * count)),
    )
    if 2 * side_count > count:
        return {}
    long_symbols = tuple(
        sorted(adapted_values, key=lambda symbol: (-adapted_values[symbol], symbol))[:side_count]
    )
    short_symbols = tuple(
        sorted(adapted_values, key=lambda symbol: (adapted_values[symbol], symbol))[:side_count]
    )
    if set(long_symbols) & set(short_symbols):
        return {}
    raw_separation = statistics.median(
        scores[symbol].raw_depth_improvement for symbol in long_symbols
    ) - statistics.median(scores[symbol].raw_depth_improvement for symbol in short_symbols)
    if raw_separation < parameters.minimum_raw_separation:
        return {}

    side_budget = parameters.target_gross / 2.0
    symbol_weight = side_budget / side_count
    if symbol_weight > parameters.maximum_symbol_weight:
        return {}
    targets = {symbol: symbol_weight for symbol in long_symbols}
    targets.update({symbol: -symbol_weight for symbol in short_symbols})
    if any(not math.isfinite(weight) for weight in targets.values()):
        return {}
    if sum(abs(weight) for weight in targets.values()) > parameters.target_gross + 1e-12:
        return {}
    if abs(sum(targets.values())) > parameters.maximum_abs_net:
        return {}
    return dict(sorted(targets.items()))


@dataclasses.dataclass
class LiquidityDepthMigrationStrategy(TargetStrategy):
    """Stateless weekly direction-free liquidity migration selector."""

    parameters: StrategyParameters = BASE_PARAMETERS

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        if type(seed) is not int or seed != CANONICAL_SEED:
            raise ValueError(f"seed must equal canonical seed {CANONICAL_SEED}")
        decision_time = _as_utc(context.decision_time)
        anchor = _as_utc(self.parameters.rebalance_anchor_utc)
        elapsed = decision_time - anchor
        interval = pd.Timedelta(hours=self.parameters.decision_interval_hours)
        if elapsed < pd.Timedelta(0) or elapsed % interval != pd.Timedelta(0):
            return None
        scores = preconstruction_scores(context, parameters=self.parameters)
        return scores_to_target_weights(scores, parameters=self.parameters)


def build_strategy_from_parameters(
    overrides: Mapping[str, object] | None = None,
) -> LiquidityDepthMigrationStrategy:
    """Construct the exact preregistered candidate without hidden state."""
    updates = dict(overrides or {})
    allowed = {field.name for field in dataclasses.fields(StrategyParameters)}
    unknown = sorted(set(updates) - allowed)
    if unknown:
        raise ValueError(f"unknown strategy parameters: {unknown}")
    return LiquidityDepthMigrationStrategy(
        parameters=dataclasses.replace(BASE_PARAMETERS, **updates)
    )


def build_strategy() -> TargetStrategy:
    """Canonical evaluator entrypoint for the explicitly materialized LDM candidate."""
    candidate_id = candidate_variant.ACTIVE_CANDIDATE_ID
    expected_overrides = PREREGISTERED_CANDIDATE_OVERRIDES.get(candidate_id)
    if expected_overrides is None:
        raise ValueError("active candidate is not preregistered")
    if (
        not isinstance(candidate_variant.ACTIVE_OVERRIDES, Mapping)
        or dict(candidate_variant.ACTIVE_OVERRIDES) != expected_overrides
    ):
        raise ValueError("active overrides do not match the preregistered candidate")
    expected_template = PREREGISTERED_RISK_POLICY_TEMPLATES[candidate_id]
    if candidate_variant.ACTIVE_RISK_POLICY_TEMPLATE != expected_template:
        raise ValueError("active risk template does not match the preregistered candidate")
    return build_strategy_from_parameters(candidate_variant.ACTIVE_OVERRIDES)
