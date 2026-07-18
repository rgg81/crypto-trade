"""Team 05: deterministic causal residual-trend/reversal targets.

The central evaluator owns orders, fills, costs, funding, risk state, and positions.  This module
only converts past-closed bars and point-in-time eligibility into signed target weights.
"""

from __future__ import annotations

import dataclasses
import json
import math
import statistics
from collections.abc import Mapping

import candidate_variant
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy
from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

CANONICAL_SEED = 20260801
BAR_DURATION = pd.Timedelta(hours=8)


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    algorithm_id: str = "team05-crtr-v1"
    rebalance_anchor_utc: str = "2020-01-01T00:00:00Z"
    rebalance_every_days: int = 3
    short_horizon_days: int = 3
    medium_horizon_days: int = 20
    slow_horizon_days: int = 60
    bars_per_day: int = 3
    minimum_coverage_fraction: float = 0.85
    maximum_latest_staleness_hours: int = 12
    maximum_anchor_gap_hours: int = 16
    minimum_symbols: int = 12
    selection_fraction: float = 0.25
    minimum_side_symbols: int = 4
    target_gross: float = 0.60
    maximum_abs_net_tilt: float = 0.08
    maximum_symbol_weight: float = 0.04
    market_tilt_scale: float = 0.12
    directional_full_scale: float = 0.10
    medium_score_weight: float = 0.35
    chop_reversal_weight: float = 0.20
    directional_reversal_weight: float = 0.05
    alignment_discount: float = 0.65
    volatility_reliability_penalty: float = 0.15
    trend_gate_log_return: float = 0.02
    equal_weight_fraction: float = 0.70
    minimum_score_span: float = 0.10

    def __post_init__(self) -> None:
        if self.algorithm_id != "team05-crtr-v1":
            raise ValueError("unexpected algorithm_id")
        if self.rebalance_every_days < 1 or self.bars_per_day < 1:
            raise ValueError("rebalance cadence and bars_per_day must be positive")
        if not 0 < self.short_horizon_days < self.medium_horizon_days < self.slow_horizon_days:
            raise ValueError("feature horizons must increase strictly")
        if not 0 < self.minimum_coverage_fraction <= 1:
            raise ValueError("minimum_coverage_fraction must be in (0,1]")
        if self.maximum_latest_staleness_hours < 0 or self.maximum_anchor_gap_hours < 0:
            raise ValueError("time tolerances cannot be negative")
        if self.minimum_symbols < 2 or self.minimum_side_symbols < 1:
            raise ValueError("minimum universe and sleeve sizes must be positive")
        if not 0 < self.selection_fraction <= 0.5:
            raise ValueError("selection_fraction must be in (0,0.5]")
        if not 0 < self.target_gross <= 1:
            raise ValueError("target_gross must be in (0,1]")
        if not 0 <= self.maximum_abs_net_tilt <= 0.25:
            raise ValueError("maximum_abs_net_tilt must be in [0,0.25]")
        if self.maximum_abs_net_tilt > self.target_gross:
            raise ValueError("net tilt cannot exceed target gross")
        if not 0 < self.maximum_symbol_weight <= 0.10:
            raise ValueError("maximum_symbol_weight must be in (0,0.10]")
        if self.market_tilt_scale <= 0 or self.directional_full_scale <= 0:
            raise ValueError("market scaling constants must be positive")
        if not 0 <= self.medium_score_weight < 1:
            raise ValueError("medium_score_weight must be in [0,1)")
        if not 0 <= self.directional_reversal_weight <= self.chop_reversal_weight:
            raise ValueError("reversal weight must not rise with directionality")
        if self.medium_score_weight + self.chop_reversal_weight >= 1:
            raise ValueError("chop weights leave no slow-trend component")
        if not 0 < self.alignment_discount <= 1:
            raise ValueError("alignment_discount must be in (0,1]")
        if not 0 <= self.volatility_reliability_penalty < 1:
            raise ValueError("volatility_reliability_penalty must be in [0,1)")
        if self.trend_gate_log_return < 0:
            raise ValueError("trend_gate_log_return cannot be negative")
        if not 0 <= self.equal_weight_fraction <= 1:
            raise ValueError("equal_weight_fraction must be in [0,1]")
        if not 0 <= self.minimum_score_span <= 2:
            raise ValueError("minimum_score_span must be in [0,2]")


BASE_PARAMETERS = StrategyParameters()

PREREGISTERED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    "team05-crtr-core-v2": {},
    "team05-crtr-core-v2-infra-r1": {},
    "team05-crtr-ab-vol": {},
    "team05-crtr-ab-dd": {},
    "team05-crtr-ab-stop": {},
    "team05-crtr-ab-turnover": {},
    "team05-crtr-base-v1": {},
    "team05-crtr-n01-slow-50d": {"slow_horizon_days": 50},
    "team05-crtr-n02-slow-70d": {"slow_horizon_days": 70},
    "team05-crtr-n03-selection-020": {"selection_fraction": 0.20},
    "team05-crtr-n04-selection-030": {"selection_fraction": 0.30},
    "team05-crtr-n05-gross-050": {"target_gross": 0.50},
    "team05-crtr-n06-gross-070": {"target_gross": 0.70},
    "team05-crtr-n07-chop-reversal-015": {"chop_reversal_weight": 0.15},
    "team05-crtr-n08-chop-reversal-025": {"chop_reversal_weight": 0.25},
}

PREREGISTERED_RISK_POLICY_TEMPLATES: dict[str, str] = {
    "team05-crtr-core-v2": "risk_ablations/none.json",
    "team05-crtr-core-v2-infra-r1": "risk_ablations/none.json",
    "team05-crtr-ab-vol": "risk_ablations/volatility_only.json",
    "team05-crtr-ab-dd": "risk_ablations/drawdown_only.json",
    "team05-crtr-ab-stop": "risk_ablations/position_stop_only.json",
    "team05-crtr-ab-turnover": "risk_ablations/turnover_only.json",
    "team05-crtr-base-v1": "risk_ablations/combined.json",
    "team05-crtr-n01-slow-50d": "risk_ablations/combined.json",
    "team05-crtr-n02-slow-70d": "risk_ablations/combined.json",
    "team05-crtr-n03-selection-020": "risk_ablations/combined.json",
    "team05-crtr-n04-selection-030": "risk_ablations/combined.json",
    "team05-crtr-n05-gross-050": "risk_ablations/combined.json",
    "team05-crtr-n06-gross-070": "risk_ablations/combined.json",
    "team05-crtr-n07-chop-reversal-015": "risk_ablations/combined.json",
    "team05-crtr-n08-chop-reversal-025": "risk_ablations/combined.json",
}


@dataclasses.dataclass(frozen=True)
class PreconstructionScore:
    """Auditable score record produced before portfolio construction.

    Values are based only on closed prices at or before the decision boundary.  The adapter may
    use only fields in this record plus the frozen parameters; it receives no portfolio state.
    """

    symbol: str
    score: float
    short_log_return: float
    medium_log_return: float
    slow_log_return: float
    realized_bar_volatility: float
    market_direction_log_return: float


@dataclasses.dataclass(frozen=True)
class _RawFeatures:
    symbol: str
    short_log_return: float
    medium_log_return: float
    slow_log_return: float
    short_normalized_return: float
    medium_normalized_return: float
    slow_normalized_return: float
    realized_bar_volatility: float


def _as_utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _closed_price_series(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series | None:
    if (
        not isinstance(frame, pd.DataFrame)
        or not isinstance(frame.index, pd.RangeIndex)
        or not {"open_time", "close"}.issubset(frame.columns)
    ):
        return None
    try:
        raw_open_times = frame["open_time"]
        if pd.api.types.is_bool_dtype(raw_open_times.dtype):
            return None
        if pd.api.types.is_numeric_dtype(raw_open_times.dtype):
            open_times = pd.to_datetime(
                raw_open_times,
                unit="ms",
                utc=True,
                errors="coerce",
            )
        else:
            open_times = pd.to_datetime(raw_open_times, utc=True, errors="coerce")
    except (TypeError, ValueError, OverflowError):
        return None
    close_times = open_times + BAR_DURATION
    numeric_values: list[float] = []
    admitted_close_times: list[pd.Timestamp] = []
    for close_time, value in zip(close_times.tolist(), frame["close"].tolist(), strict=True):
        if pd.isna(close_time) or close_time > decision_time:
            continue
        admitted_close_times.append(_as_utc(close_time))
        if isinstance(value, bool):
            numeric_values.append(math.nan)
            continue
        try:
            numeric_values.append(float(value))
        except (TypeError, ValueError, OverflowError):
            numeric_values.append(math.nan)
    series = pd.Series(
        numeric_values,
        index=pd.DatetimeIndex(admitted_close_times),
        dtype="float64",
    )
    series = series[~series.index.duplicated(keep="last")].sort_index(kind="mergesort")
    finite_positive = series.map(lambda value: math.isfinite(float(value)) and float(value) > 0)
    series = series.loc[finite_positive]
    if series.empty:
        return None
    latest_gap = decision_time - series.index[-1]
    if latest_gap < pd.Timedelta(0):
        return None
    if latest_gap > pd.Timedelta(hours=parameters.maximum_latest_staleness_hours):
        return None
    return series


def _price_at_or_before(
    prices: pd.Series,
    cutoff: pd.Timestamp,
    *,
    maximum_gap_hours: int,
) -> float | None:
    location = int(prices.index.searchsorted(cutoff, side="right")) - 1
    if location < 0:
        return None
    observed_time = prices.index[location]
    if cutoff - observed_time > pd.Timedelta(hours=maximum_gap_hours):
        return None
    value = float(prices.iloc[location])
    return value if math.isfinite(value) and value > 0 else None


def _raw_features(
    symbol: str,
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> _RawFeatures | None:
    prices = _closed_price_series(
        frame,
        decision_time=decision_time,
        parameters=parameters,
    )
    if prices is None:
        return None
    expected_slow_bars = parameters.slow_horizon_days * parameters.bars_per_day
    slow_window_prices = prices.loc[
        prices.index >= decision_time - pd.Timedelta(days=parameters.slow_horizon_days)
    ]
    if len(slow_window_prices) < math.ceil(
        expected_slow_bars * parameters.minimum_coverage_fraction
    ):
        return None

    latest = float(prices.iloc[-1])
    anchors: dict[str, float] = {}
    for label, days in (
        ("short", parameters.short_horizon_days),
        ("medium", parameters.medium_horizon_days),
        ("slow", parameters.slow_horizon_days),
    ):
        anchor = _price_at_or_before(
            prices,
            decision_time - pd.Timedelta(days=days),
            maximum_gap_hours=parameters.maximum_anchor_gap_hours,
        )
        if anchor is None:
            return None
        anchors[label] = anchor

    volatility_start = decision_time - pd.Timedelta(days=parameters.medium_horizon_days)
    volatility_prices = prices.loc[prices.index >= volatility_start]
    minimum_volatility_observations = math.ceil(
        parameters.medium_horizon_days
        * parameters.bars_per_day
        * parameters.minimum_coverage_fraction
    )
    if len(volatility_prices) < minimum_volatility_observations:
        return None
    log_prices = volatility_prices.map(math.log)
    log_changes = log_prices.diff().dropna()
    if len(log_changes) < 2:
        return None
    realized_bar_volatility = float(log_changes.std(ddof=0))
    if not math.isfinite(realized_bar_volatility) or realized_bar_volatility <= 1e-8:
        return None

    latest_log = math.log(latest)
    short_return = latest_log - math.log(anchors["short"])
    medium_return = latest_log - math.log(anchors["medium"])
    slow_return = latest_log - math.log(anchors["slow"])
    short_scale = realized_bar_volatility * math.sqrt(
        parameters.short_horizon_days * parameters.bars_per_day
    )
    medium_scale = realized_bar_volatility * math.sqrt(
        parameters.medium_horizon_days * parameters.bars_per_day
    )
    slow_scale = realized_bar_volatility * math.sqrt(
        parameters.slow_horizon_days * parameters.bars_per_day
    )
    return _RawFeatures(
        symbol=symbol,
        short_log_return=short_return,
        medium_log_return=medium_return,
        slow_log_return=slow_return,
        short_normalized_return=short_return / short_scale,
        medium_normalized_return=medium_return / medium_scale,
        slow_normalized_return=slow_return / slow_scale,
        realized_bar_volatility=realized_bar_volatility,
    )


def _centered_fractional_ranks(values: Mapping[str, float]) -> dict[str, float]:
    """Average-rank ties exactly and map ranks deterministically to [-1, 1]."""
    ordered = sorted(values.items(), key=lambda item: (item[1], item[0]))
    count = len(ordered)
    if count == 0:
        return {}
    if count == 1:
        return {ordered[0][0]: 0.0}
    result: dict[str, float] = {}
    start = 0
    while start < count:
        end = start + 1
        while end < count and ordered[end][1] == ordered[start][1]:
            end += 1
        average_zero_based_rank = (start + end - 1) / 2.0
        centered_rank = 2.0 * average_zero_based_rank / (count - 1) - 1.0
        for index in range(start, end):
            result[ordered[index][0]] = centered_rank
        start = end
    return result


def preconstruction_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = BASE_PARAMETERS,
) -> dict[str, PreconstructionScore]:
    """Return the complete deterministic score map before any asset selection.

    The result is independent of mapping insertion order and ``seed``.  Invalid, stale, or
    insufficient histories are omitted rather than imputed.  A universe with fewer than the
    frozen minimum number of valid members returns an empty map.
    """
    decision_time = _as_utc(context.decision_time)
    eligible = sorted(
        {
            str(symbol)
            for symbol in context.eligible_symbols
            if str(symbol) != "__crypto_trade_rebalance__"
        }
    )
    raw: dict[str, _RawFeatures] = {}
    for symbol in eligible:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        features = _raw_features(
            symbol,
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if features is not None:
            raw[symbol] = features
    if len(raw) < parameters.minimum_symbols:
        return {}

    slow_ranks = _centered_fractional_ranks(
        {symbol: row.slow_normalized_return for symbol, row in raw.items()}
    )
    medium_ranks = _centered_fractional_ranks(
        {symbol: row.medium_normalized_return for symbol, row in raw.items()}
    )
    short_ranks = _centered_fractional_ranks(
        {symbol: row.short_normalized_return for symbol, row in raw.items()}
    )
    volatility_ranks = _centered_fractional_ranks(
        {symbol: row.realized_bar_volatility for symbol, row in raw.items()}
    )

    market_direction = 0.40 * statistics.median(
        row.medium_log_return for row in raw.values()
    ) + 0.60 * statistics.median(row.slow_log_return for row in raw.values())
    directionality = min(1.0, abs(market_direction) / parameters.directional_full_scale)
    reversal_weight = parameters.chop_reversal_weight + directionality * (
        parameters.directional_reversal_weight - parameters.chop_reversal_weight
    )
    slow_weight = 1.0 - parameters.medium_score_weight - reversal_weight

    scores: dict[str, PreconstructionScore] = {}
    for symbol in sorted(raw):
        row = raw[symbol]
        composite = (
            slow_weight * slow_ranks[symbol]
            + parameters.medium_score_weight * medium_ranks[symbol]
            - reversal_weight * short_ranks[symbol]
        )
        aligned = (
            row.medium_log_return == 0
            or row.slow_log_return == 0
            or math.copysign(1.0, row.medium_log_return) == math.copysign(1.0, row.slow_log_return)
        )
        alignment_scale = 1.0 if aligned else parameters.alignment_discount
        unit_volatility_rank = (volatility_ranks[symbol] + 1.0) / 2.0
        reliability_scale = 1.0 - (parameters.volatility_reliability_penalty * unit_volatility_rank)
        score = max(-1.0, min(1.0, composite * alignment_scale * reliability_scale))
        scores[symbol] = PreconstructionScore(
            symbol=symbol,
            score=score,
            short_log_return=row.short_log_return,
            medium_log_return=row.medium_log_return,
            slow_log_return=row.slow_log_return,
            realized_bar_volatility=row.realized_bar_volatility,
            market_direction_log_return=market_direction,
        )
    return scores


def candidate_score_values(
    scores: Mapping[str, PreconstructionScore],
) -> dict[str, float]:
    """Expose the exact A5 identity boundary and return its construction inputs.

    The hook receives only a built-in ``dict[str, float]`` after all score transforms and before
    score-span checks, sleeve selection, or weighting.  The returned values are validated and are
    the values used by portfolio construction.  Amendment 0005 and
    ``score_adapter_protocol_v5`` are active; Team05's use remains prospective until the core
    manifest, semantic review, and registration are organizer-bound.
    """
    if any(type(symbol) is not str or not symbol for symbol in scores):
        return {}
    ordered_symbols = sorted(scores)
    for symbol in ordered_symbols:
        row = scores[symbol]
        if not isinstance(row, PreconstructionScore):
            return {}
        if type(row.symbol) is not str or row.symbol != symbol:
            return {}
        values = (
            row.score,
            row.short_log_return,
            row.medium_log_return,
            row.slow_log_return,
            row.realized_bar_volatility,
            row.market_direction_log_return,
        )
        # The dataclass annotations are not runtime validators.  Reject malformed typed fields
        # before comparisons or ``math.isfinite`` so hostile strings, booleans, ``None``, and
        # other non-floats can never escape the fail-closed boundary as a TypeError.
        if any(type(value) is not float for value in values):
            return {}
        if not all(math.isfinite(value) for value in values):
            return {}
        if not -1.0 <= row.score <= 1.0 or row.realized_bar_volatility <= 0:
            return {}

    boundary_input = {symbol: float(scores[symbol].score) for symbol in ordered_symbols}
    boundary_output = score_boundary(boundary_input)
    if not isinstance(boundary_output, Mapping) or set(boundary_output) != set(boundary_input):
        return {}

    result: dict[str, float] = {}
    for symbol in ordered_symbols:
        value = boundary_output[symbol]
        if isinstance(value, bool):
            return {}
        try:
            built_in_value = float(value)
        except (TypeError, ValueError, OverflowError):
            return {}
        if not math.isfinite(built_in_value) or not -1.0 <= built_in_value <= 1.0:
            return {}
        result[symbol] = built_in_value
    return result


def candidate_score_payload_bytes(
    scores: Mapping[str, PreconstructionScore],
) -> bytes:
    """Canonical Team05 A5 audit bytes, or empty bytes for a malformed nonempty map."""
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


def _bounded_side_weights(
    symbols: list[str],
    scores: Mapping[str, PreconstructionScore],
    *,
    budget: float,
    maximum_symbol_weight: float,
    equal_weight_fraction: float,
) -> dict[str, float]:
    if not symbols or budget <= 0:
        return {}
    magnitudes = {symbol: abs(scores[symbol].score) for symbol in symbols}
    magnitude_sum = sum(magnitudes.values())
    if magnitude_sum <= 0:
        magnitude_share = {symbol: 1.0 / len(symbols) for symbol in symbols}
    else:
        magnitude_share = {symbol: magnitudes[symbol] / magnitude_sum for symbol in symbols}
    preference = {
        symbol: equal_weight_fraction / len(symbols)
        + (1.0 - equal_weight_fraction) * magnitude_share[symbol]
        for symbol in symbols
    }

    result = {symbol: 0.0 for symbol in symbols}
    active = list(symbols)
    remaining = budget
    while active and remaining > 1e-15:
        preference_sum = sum(preference[symbol] for symbol in active)
        if preference_sum <= 0:
            shares = {symbol: remaining / len(active) for symbol in active}
        else:
            shares = {symbol: remaining * preference[symbol] / preference_sum for symbol in active}
        capped = [
            symbol for symbol in active if result[symbol] + shares[symbol] > maximum_symbol_weight
        ]
        if not capped:
            for symbol in active:
                result[symbol] += shares[symbol]
            remaining = 0.0
            break
        for symbol in capped:
            addition = maximum_symbol_weight - result[symbol]
            remaining -= max(0.0, addition)
            result[symbol] = maximum_symbol_weight
        active = [symbol for symbol in active if symbol not in set(capped)]
    return {symbol: weight for symbol, weight in result.items() if weight > 0}


def scores_to_target_weights(
    scores: Mapping[str, PreconstructionScore],
    *,
    parameters: StrategyParameters = BASE_PARAMETERS,
) -> dict[str, float]:
    """Pure, deterministic adapter from preconstruction scores to signed targets."""
    # A5 observes every scheduled decision, including explicit flat decisions.  The hook must
    # therefore receive the exact empty/sparse score dictionary before the breadth gate returns.
    adapted_score_values = candidate_score_values(scores)
    if len(scores) < parameters.minimum_symbols:
        return {}
    if len(adapted_score_values) != len(scores):
        return {}
    construction_scores = {
        symbol: dataclasses.replace(scores[symbol], score=adapted_score_values[symbol])
        for symbol in sorted(scores)
    }
    ordered_symbols = sorted(construction_scores)
    market_values = [
        construction_scores[symbol].market_direction_log_return for symbol in ordered_symbols
    ]
    if max(market_values) - min(market_values) > 1e-15:
        return {}
    score_span = max(construction_scores[symbol].score for symbol in ordered_symbols) - min(
        construction_scores[symbol].score for symbol in ordered_symbols
    )
    if score_span < parameters.minimum_score_span:
        return {}

    count = len(ordered_symbols)
    side_count = max(
        parameters.minimum_side_symbols,
        math.ceil(count * parameters.selection_fraction),
    )
    side_count = min(side_count, count // 2)
    if side_count < 1:
        return {}

    long_order = sorted(
        ordered_symbols,
        key=lambda symbol: (-construction_scores[symbol].score, symbol),
    )
    long_preferred = [
        symbol
        for symbol in long_order
        if construction_scores[symbol].medium_log_return >= -parameters.trend_gate_log_return
    ]
    long_symbols = (
        long_preferred + [symbol for symbol in long_order if symbol not in set(long_preferred)]
    )[:side_count]

    long_set = set(long_symbols)
    short_order = sorted(
        (symbol for symbol in ordered_symbols if symbol not in long_set),
        key=lambda symbol: (construction_scores[symbol].score, symbol),
    )
    short_preferred = [
        symbol
        for symbol in short_order
        if construction_scores[symbol].medium_log_return <= parameters.trend_gate_log_return
    ]
    short_symbols = (
        short_preferred + [symbol for symbol in short_order if symbol not in set(short_preferred)]
    )[:side_count]
    if not long_symbols or not short_symbols:
        return {}

    market_direction = market_values[0]
    net_tilt = parameters.maximum_abs_net_tilt * math.tanh(
        market_direction / parameters.market_tilt_scale
    )
    long_budget = (parameters.target_gross + net_tilt) / 2.0
    short_budget = (parameters.target_gross - net_tilt) / 2.0
    long_weights = _bounded_side_weights(
        long_symbols,
        construction_scores,
        budget=long_budget,
        maximum_symbol_weight=parameters.maximum_symbol_weight,
        equal_weight_fraction=parameters.equal_weight_fraction,
    )
    short_weights = _bounded_side_weights(
        short_symbols,
        construction_scores,
        budget=short_budget,
        maximum_symbol_weight=parameters.maximum_symbol_weight,
        equal_weight_fraction=parameters.equal_weight_fraction,
    )
    targets = {symbol: weight for symbol, weight in long_weights.items()}
    targets.update({symbol: -weight for symbol, weight in short_weights.items()})
    if any(not math.isfinite(weight) for weight in targets.values()):
        return {}
    return dict(sorted(targets.items()))


@dataclasses.dataclass
class CausalResidualTrendReversalStrategy(TargetStrategy):
    parameters: StrategyParameters = BASE_PARAMETERS

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed != CANONICAL_SEED:
            raise ValueError(f"seed must equal canonical seed {CANONICAL_SEED}")
        decision_time = _as_utc(context.decision_time)
        if (
            decision_time.hour != 0
            or decision_time.minute != 0
            or decision_time.second != 0
            or decision_time.microsecond != 0
        ):
            return None
        anchor = _as_utc(self.parameters.rebalance_anchor_utc).normalize()
        elapsed_days = (decision_time.normalize() - anchor).days
        if elapsed_days < 0 or elapsed_days % self.parameters.rebalance_every_days != 0:
            return None
        scores = preconstruction_scores(
            context,
            parameters=self.parameters,
        )
        return scores_to_target_weights(scores, parameters=self.parameters)


def build_strategy_from_parameters(
    overrides: Mapping[str, object] | None = None,
) -> CausalResidualTrendReversalStrategy:
    """Construct an explicit preregistered variant without filesystem or hidden state."""
    updates = dict(overrides or {})
    allowed = {field.name for field in dataclasses.fields(StrategyParameters)}
    unknown = sorted(set(updates) - allowed)
    if unknown:
        raise ValueError(f"unknown strategy parameters: {unknown}")
    return CausalResidualTrendReversalStrategy(
        parameters=dataclasses.replace(BASE_PARAMETERS, **updates)
    )


def build_strategy() -> TargetStrategy:
    """Canonical evaluator entrypoint for the explicitly materialized candidate variant."""
    if (
        type(candidate_variant.ACTIVE_CANDIDATE_ID) is not str
        or not candidate_variant.ACTIVE_CANDIDATE_ID
    ):
        raise ValueError("active candidate identifier must be nonempty text")
    expected_overrides = PREREGISTERED_CANDIDATE_OVERRIDES.get(
        candidate_variant.ACTIVE_CANDIDATE_ID
    )
    if expected_overrides is None:
        raise ValueError("active candidate is not preregistered")
    if (
        not isinstance(candidate_variant.ACTIVE_OVERRIDES, Mapping)
        or dict(candidate_variant.ACTIVE_OVERRIDES) != expected_overrides
    ):
        raise ValueError("active overrides do not match the preregistered candidate")
    expected_risk_template = PREREGISTERED_RISK_POLICY_TEMPLATES[
        candidate_variant.ACTIVE_CANDIDATE_ID
    ]
    if candidate_variant.ACTIVE_RISK_POLICY_TEMPLATE != expected_risk_template:
        raise ValueError("active risk template does not match the preregistered candidate")
    return build_strategy_from_parameters(candidate_variant.ACTIVE_OVERRIDES)
