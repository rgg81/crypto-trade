"""Team 05 pivot-01: up/down capture convexity (UDCC).

UDCC estimates how each organizer-authorized native-crypto contract participated in positive
and negative moves of the contemporaneous common crypto tape during the preceding 84 days.  A
contract with high upside capture and low downside capture receives a high long-desirability
score; the opposite asymmetry receives a low score.  The statistic uses no funding, volume,
future direction forecast, lagged cross-sectional rank, or cumulative return signal.

Universe classification is organizer-owned.  Amendment 0006 supplies point-in-time membership
containing native crypto assets only and excludes stablecoin bases plus tokenized or synthetic
TradFi securities, commodities, metals, and indexes.  This module never guesses asset class from
ticker text.
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
    """Complete fixed material configuration for the UDCC pivot core."""

    algorithm_id: str = "team05-udcc-v1"
    rebalance_anchor_utc: str = "1970-01-01T00:00:00Z"
    bar_interval_hours: int = 8
    decision_interval_hours: int = 168
    price_count: int = 253
    maximum_latest_staleness_hours: int = 12
    minimum_symbols: int = 12
    minimum_up_observations: int = 63
    minimum_down_observations: int = 63
    minimum_beta_denominator: float = 1e-8
    maximum_abs_beta: float = 5.0
    minimum_score_span: float = 0.50
    selection_fraction: float = 0.20
    minimum_side_symbols: int = 5
    maximum_side_symbols: int = 8
    minimum_up_capture_separation: float = 0.10
    minimum_down_capture_separation: float = 0.10
    target_gross: float = 0.48
    maximum_symbol_weight: float = 0.05
    maximum_abs_net: float = 1e-12

    def __post_init__(self) -> None:
        if self.algorithm_id != "team05-udcc-v1":
            raise ValueError("unexpected algorithm_id")
        integer_fields = (
            self.bar_interval_hours,
            self.decision_interval_hours,
            self.price_count,
            self.maximum_latest_staleness_hours,
            self.minimum_symbols,
            self.minimum_up_observations,
            self.minimum_down_observations,
            self.minimum_side_symbols,
            self.maximum_side_symbols,
        )
        if any(type(value) is not int or value <= 0 for value in integer_fields):
            raise ValueError("integer configuration fields must be positive")
        if self.decision_interval_hours % self.bar_interval_hours:
            raise ValueError("decision interval must be a multiple of the bar interval")
        if self.price_count != 253:
            raise ValueError("UDCC requires exactly 253 prices")
        return_count = self.price_count - 1
        if self.minimum_up_observations + self.minimum_down_observations > return_count:
            raise ValueError("conditional observation floors exceed the return sample")
        if self.minimum_symbols < 2 * self.minimum_side_symbols:
            raise ValueError("minimum universe cannot support disjoint sleeves")
        if self.maximum_side_symbols < self.minimum_side_symbols:
            raise ValueError("maximum sleeve size cannot be below the minimum")
        if not 0.0 < self.selection_fraction <= 0.5:
            raise ValueError("selection fraction must be inside (0, 0.5]")
        finite_positive = (
            self.minimum_beta_denominator,
            self.maximum_abs_beta,
            self.minimum_score_span,
            self.minimum_up_capture_separation,
            self.minimum_down_capture_separation,
            self.target_gross,
            self.maximum_symbol_weight,
            self.maximum_abs_net,
        )
        if any(not math.isfinite(value) or value <= 0.0 for value in finite_positive):
            raise ValueError("continuous configuration fields must be positive and finite")
        if self.target_gross > 1.0 or self.maximum_symbol_weight > 0.10:
            raise ValueError("gross exposure or symbol cap exceeds the frozen range")
        maximum_requested_weight = self.target_gross / (2 * self.minimum_side_symbols)
        if maximum_requested_weight > self.maximum_symbol_weight:
            raise ValueError("minimum sleeve size cannot implement the target gross")


BASE_PARAMETERS = StrategyParameters()

PREREGISTERED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    "team05-udcc-pivot01-core-v1": {},
}

PREREGISTERED_RISK_POLICY_TEMPLATES: dict[str, str] = {
    "team05-udcc-pivot01-core-v1": "risk_policies/no-control.json",
}


@dataclasses.dataclass(frozen=True)
class PreconstructionScore:
    """Auditable conditional-capture record produced before portfolio construction."""

    symbol: str
    score: float
    beta_up: float
    beta_down: float


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


def _closed_price_suffix(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series | None:
    """Return one exact contiguous 253-price suffix using only past-closed bars."""
    if (
        not isinstance(frame, pd.DataFrame)
        or not isinstance(frame.index, pd.RangeIndex)
        or not {"open_time", "close"}.issubset(frame.columns)
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

    closed_values = frame.loc[closed_mask, "close"].tolist()
    if any(isinstance(value, (bool, np.bool_)) for value in closed_values):
        return None
    try:
        prices = np.asarray([float(value) for value in closed_values], dtype=float)
    except (TypeError, ValueError, OverflowError):
        return None
    if not np.isfinite(prices).all() or bool((prices <= 0.0).any()):
        return None

    admitted_times = close_times[closed_mask]
    if admitted_times.duplicated().any():
        return None
    history = pd.Series(prices, index=admitted_times, dtype="float64").sort_index(kind="mergesort")
    latest_close = history.index[-1]
    latest_gap = decision_time - latest_close
    if latest_gap < pd.Timedelta(0) or latest_gap > pd.Timedelta(
        hours=parameters.maximum_latest_staleness_hours
    ):
        return None
    expected = pd.date_range(
        end=latest_close,
        periods=parameters.price_count,
        freq=interval,
    )
    suffix = history.reindex(expected)
    if suffix.isna().any():
        return None
    return suffix


def _modal_grid_histories(
    context: DecisionContext,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> dict[str, pd.Series]:
    eligible_raw = tuple(context.eligible_symbols)
    if any(type(symbol) is not str or not symbol for symbol in eligible_raw):
        return {}
    if len(eligible_raw) != len(set(eligible_raw)):
        return {}
    eligible = sorted(symbol for symbol in eligible_raw if symbol != _RESERVED_SYMBOL)

    histories: dict[str, pd.Series] = {}
    groups: dict[tuple[int, ...], list[str]] = {}
    for symbol in eligible:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _closed_price_suffix(
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

    # Prefer the grid shared by the most eligible symbols, then the most recent grid.  The final
    # signature tie-break makes the choice independent of mapping or eligible-symbol order.
    selected_signature = min(
        groups,
        key=lambda signature: (-len(groups[signature]), -signature[-1], signature),
    )
    selected_symbols = sorted(groups[selected_signature])
    if len(selected_symbols) < parameters.minimum_symbols:
        return {}
    return {symbol: histories[symbol] for symbol in selected_symbols}


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
    """Estimate conditional common-tape captures and return the complete final score map."""
    decision_time = _as_utc(context.decision_time)
    histories = _modal_grid_histories(
        context,
        decision_time=decision_time,
        parameters=parameters,
    )
    if len(histories) < parameters.minimum_symbols:
        return {}

    symbols = sorted(histories)
    log_prices = np.vstack([np.log(histories[symbol].to_numpy(dtype=float)) for symbol in symbols])
    returns = np.diff(log_prices, axis=1)
    if returns.shape != (len(symbols), parameters.price_count - 1):
        return {}
    if not np.isfinite(returns).all():
        return {}
    common_returns = np.median(returns, axis=0)
    up_mask = common_returns > 0.0
    down_mask = common_returns < 0.0
    if int(up_mask.sum()) < parameters.minimum_up_observations:
        return {}
    if int(down_mask.sum()) < parameters.minimum_down_observations:
        return {}

    up_denominator = float(np.dot(common_returns[up_mask], common_returns[up_mask]))
    down_denominator = float(np.dot(common_returns[down_mask], common_returns[down_mask]))
    if (
        not math.isfinite(up_denominator)
        or not math.isfinite(down_denominator)
        or up_denominator <= parameters.minimum_beta_denominator
        or down_denominator <= parameters.minimum_beta_denominator
    ):
        return {}

    beta_up: dict[str, float] = {}
    beta_down: dict[str, float] = {}
    for row_index, symbol in enumerate(symbols):
        symbol_returns = returns[row_index]
        up_value = float(np.dot(common_returns[up_mask], symbol_returns[up_mask])) / up_denominator
        down_value = (
            float(np.dot(common_returns[down_mask], symbol_returns[down_mask])) / down_denominator
        )
        if (
            not math.isfinite(up_value)
            or not math.isfinite(down_value)
            or abs(up_value) > parameters.maximum_abs_beta
            or abs(down_value) > parameters.maximum_abs_beta
        ):
            continue
        beta_up[symbol] = up_value
        beta_down[symbol] = down_value
    if len(beta_up) < parameters.minimum_symbols:
        return {}

    up_ranks = _centered_fractional_ranks(beta_up)
    down_ranks = _centered_fractional_ranks(beta_down)
    result: dict[str, PreconstructionScore] = {}
    for symbol in sorted(beta_up):
        score = 0.50 * (up_ranks[symbol] - down_ranks[symbol])
        if not math.isfinite(score) or not -1.0 <= score <= 1.0:
            return {}
        result[symbol] = PreconstructionScore(
            symbol=symbol,
            score=float(score),
            beta_up=float(beta_up[symbol]),
            beta_down=float(beta_down[symbol]),
        )
    return result


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
        values = (row.score, row.beta_up, row.beta_down)
        if any(type(value) is not float or not math.isfinite(value) for value in values):
            return {}
        if not -1.0 <= row.score <= 1.0:
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

    up_separation = statistics.median(scores[symbol].beta_up for symbol in long_symbols) - (
        statistics.median(scores[symbol].beta_up for symbol in short_symbols)
    )
    down_separation = statistics.median(scores[symbol].beta_down for symbol in short_symbols) - (
        statistics.median(scores[symbol].beta_down for symbol in long_symbols)
    )
    if (
        up_separation < parameters.minimum_up_capture_separation
        or down_separation < parameters.minimum_down_capture_separation
    ):
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
class UpDownCaptureConvexityStrategy(TargetStrategy):
    """Stateless weekly UDCC selector."""

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
) -> UpDownCaptureConvexityStrategy:
    """Construct the exact preregistered candidate without hidden state."""
    updates = dict(overrides or {})
    allowed = {field.name for field in dataclasses.fields(StrategyParameters)}
    unknown = sorted(set(updates) - allowed)
    if unknown:
        raise ValueError(f"unknown strategy parameters: {unknown}")
    return UpDownCaptureConvexityStrategy(
        parameters=dataclasses.replace(BASE_PARAMETERS, **updates)
    )


def build_strategy() -> TargetStrategy:
    """Canonical evaluator entrypoint for the explicitly materialized UDCC candidate."""
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
