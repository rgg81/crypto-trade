"""Frozen CUP-50 v2 holdout-only scoring and total ordering."""

from __future__ import annotations

import dataclasses
import decimal
import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2.config import FOLDS, OOS_END, OOS_START, ScoringPolicy, active_policy
from crypto_trade.cup50v2.replay import EvaluationResultV2


def _scoring(policy: ScoringPolicy | None) -> ScoringPolicy:
    return policy if policy is not None else active_policy().scoring


def round_half_even(value: float, *, policy: ScoringPolicy | None = None) -> float:
    if not math.isfinite(value):
        raise ValueError("score fields must be finite before rounding")
    quantum = decimal.Decimal(1).scaleb(-_scoring(policy).rounding_places)
    return float(decimal.Decimal(str(value)).quantize(quantum, rounding=decimal.ROUND_HALF_EVEN))


@dataclasses.dataclass(frozen=True, slots=True)
class CellScore:
    q: float
    growth: float
    drawdown: float
    volatility: float
    activity: float
    utilization: float
    concentration: float
    x: float
    failed: bool = False


@dataclasses.dataclass(frozen=True, slots=True)
class PointScore:
    score: float
    generalization: float
    all_window: float
    fold_scores: Mapping[str, float]
    fold_cost_cells: Mapping[str, Mapping[int, CellScore]]
    all_cost_cells: Mapping[int, CellScore]


@dataclasses.dataclass(frozen=True, slots=True)
class NeighbourhoodScore:
    official_score: float
    centre_score: float
    median_score: float
    lower_quartile_score: float
    minimum_score: float
    point_scores: tuple[float, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class RankedEntry:
    team_id: str
    candidate_id: str
    valid: bool
    official_score: float
    lower_quartile_score: float
    minimum_point_score: float
    centre_score: float
    centre_worst_fold_3x_score: float
    centre_3x_drawdown: float
    centre_turnover: float
    bundle_sha256: str
    dnf_reason: str = ""


def _daily_frame(returns: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    required = {"net_return", "gross_return", "gross_exposure"}
    missing = required - set(returns)
    if missing:
        raise ValueError(f"scoring returns missing columns: {sorted(missing)}")
    first, stop = pd.Timestamp(start).tz_convert("UTC"), pd.Timestamp(end).tz_convert("UTC")
    selected = returns.loc[(returns.index >= first) & (returns.index < stop), list(required)].copy()
    index = pd.DatetimeIndex(selected.index).tz_convert("UTC")
    selected.index = index
    for column in required:
        values = selected[column].to_numpy(dtype=float)
        if not np.isfinite(values).all():
            raise ValueError(f"non-finite {column} in score window")
    selected["day"] = index.normalize()
    groups = selected.groupby("day", sort=True)
    daily = pd.DataFrame(
        {
            "net_return": groups["net_return"].apply(lambda values: float(np.prod(1 + values) - 1)),
            "gross_return": groups["gross_return"].apply(
                lambda values: float(np.prod(1 + values) - 1)
            ),
            "gross_exposure": groups["gross_exposure"].mean(),
        }
    )
    calendar = pd.date_range(
        first.normalize(), stop.normalize(), freq="D", inclusive="left", tz="UTC"
    )
    return daily.reindex(calendar, fill_value=0.0)


def _max_drawdown(returns: pd.Series) -> float:
    values = returns.to_numpy(dtype=float)
    if not len(values):
        return 0.0
    if np.any(values <= -1.0):
        return 1.0
    equity = np.concatenate(([1.0], np.cumprod(1.0 + values)))
    peaks = np.maximum.accumulate(equity)
    return float(np.max(1.0 - equity / peaks))


def score_cell(
    returns: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    failed: bool = False,
    policy: ScoringPolicy | None = None,
) -> CellScore:
    """Score one coherent candidate/window/cost cell exactly once."""
    rules = _scoring(policy)
    if failed:
        return CellScore(0.0, -1_000_000_000.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1_000_000_000.0, True)
    daily = _daily_frame(returns, start, end)
    n = len(daily)
    if n == 0:
        return CellScore(0.0, -1_000_000_000.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1_000_000_000.0, True)
    net = daily["net_return"].astype(float)
    gross = daily["gross_return"].astype(float)
    if (net <= -1.0).any():
        return CellScore(0.0, -1_000_000_000.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1_000_000_000.0, True)
    growth = 365.0 / n * float(np.log1p(net).sum())
    drawdown = _max_drawdown(net)
    volatility = (
        float(np.std(gross.to_numpy(dtype=float), ddof=1)) * math.sqrt(365.0) if n > 1 else 0.0
    )
    activity = float((daily["gross_exposure"] >= rules.activity_exposure_floor).mean())
    utilization = min(
        1.0,
        volatility / rules.volatility_reference,
        activity / rules.activity_reference,
    )
    absolute = gross.abs()
    total_absolute = float(absolute.sum())
    concentration = (
        float(absolute.nlargest(rules.concentration_top_days).sum() / total_absolute)
        if total_absolute > 0
        else 1.0
    )
    headroom = 1.0 - rules.concentration_threshold
    x = (
        growth
        - rules.drawdown_penalty * drawdown
        - rules.underdeployment_penalty * (1.0 - utilization)
        - rules.concentration_penalty
        * max(0.0, (concentration - rules.concentration_threshold) / headroom)
    )
    if not all(
        math.isfinite(value)
        for value in (growth, drawdown, volatility, activity, utilization, concentration, x)
    ):
        return CellScore(0.0, -1_000_000_000.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1_000_000_000.0, True)
    q = 50.0 * (1.0 + math.tanh(x / rules.squash_scale))
    q = min(100.0, max(0.0, q))
    return CellScore(q, growth, drawdown, volatility, activity, utilization, concentration, x)


def combine_costs(cells: Mapping[int, CellScore], *, policy: ScoringPolicy | None = None) -> float:
    weights = _scoring(policy).cost_weights
    if set(cells) != set(weights):
        raise ValueError("a CUP-50 v2 cost aggregate requires exactly 1x, 2x, and 3x cells")
    return sum(weights[cost] * cells[cost].q for cost in sorted(weights))


def score_point(
    results: Mapping[int, EvaluationResultV2 | pd.DataFrame | None],
    *,
    failed_cells: Sequence[tuple[str, int]] = (),
    policy: ScoringPolicy | None = None,
) -> PointScore:
    """Five chronological folds, weakest-first aggregation, then the full 30-month path."""
    rules = _scoring(policy)
    if set(results) != {1, 2, 3}:
        raise ValueError("point scoring requires independent 1x, 2x, and 3x results")
    failure_set = set(failed_cells)
    fold_scores: dict[str, float] = {}
    fold_cells: dict[str, dict[int, CellScore]] = {}
    for name, start, end in FOLDS:
        cells: dict[int, CellScore] = {}
        for cost in (1, 2, 3):
            value = results[cost]
            frame = value.returns if isinstance(value, EvaluationResultV2) else value
            is_failed = value is None or (name, cost) in failure_set
            cells[cost] = score_cell(
                pd.DataFrame() if frame is None else frame,
                start,
                end,
                failed=is_failed,
                policy=rules,
            )
        fold_cells[name] = cells
        fold_scores[name] = combine_costs(cells, policy=rules)
    weakest = sorted(fold_scores.values())
    generalization = sum(
        weight * value for weight, value in zip(rules.fold_weights, weakest, strict=True)
    )

    all_cells: dict[int, CellScore] = {}
    for cost in (1, 2, 3):
        value = results[cost]
        frame = value.returns if isinstance(value, EvaluationResultV2) else value
        all_cells[cost] = score_cell(
            pd.DataFrame() if frame is None else frame,
            OOS_START,
            OOS_END,
            failed=value is None or ("ALL", cost) in failure_set,
            policy=rules,
        )
    all_window = combine_costs(all_cells, policy=rules)
    point = rules.generalization_weight * generalization + rules.all_window_weight * all_window
    return PointScore(point, generalization, all_window, fold_scores, fold_cells, all_cells)


def score_neighbourhood(
    points: Sequence[PointScore | float],
    *,
    centre_index: int = 0,
    policy: ScoringPolicy | None = None,
) -> NeighbourhoodScore:
    rules = _scoring(policy)
    if not points:
        raise ValueError("neighbourhood has no observed points")
    if not 0 <= centre_index < len(points):
        raise ValueError("centre_index is outside the neighbourhood")
    values = tuple(
        float(point.score if isinstance(point, PointScore) else point) for point in points
    )
    if not all(math.isfinite(value) and 0.0 <= value <= 100.0 for value in values):
        raise ValueError("neighbourhood scores must be finite and within [0, 100]")
    ordered = sorted(values)
    lower_position = math.ceil(len(values) / rules.lower_quartile_fraction) - 1
    lower = ordered[lower_position]
    median = float(np.median(values))
    centre = values[centre_index]
    median_weight, lower_weight, centre_weight = rules.neighbourhood_weights
    official = median_weight * median + lower_weight * lower + centre_weight * centre
    return NeighbourhoodScore(official, centre, median, lower, min(values), values)


def rounded_neighbourhood(
    score: NeighbourhoodScore, *, policy: ScoringPolicy | None = None
) -> NeighbourhoodScore:
    rules = _scoring(policy)
    return NeighbourhoodScore(
        official_score=round_half_even(score.official_score, policy=rules),
        centre_score=round_half_even(score.centre_score, policy=rules),
        median_score=round_half_even(score.median_score, policy=rules),
        lower_quartile_score=round_half_even(score.lower_quartile_score, policy=rules),
        minimum_score=round_half_even(score.minimum_score, policy=rules),
        point_scores=tuple(round_half_even(value, policy=rules) for value in score.point_scores),
    )


def rank_entries(
    entries: Sequence[RankedEntry], *, policy: ScoringPolicy | None = None
) -> tuple[RankedEntry, ...]:
    """Deterministic total order with every valid submission ahead of every DNF."""
    rules = _scoring(policy)
    for entry in entries:
        fields = (
            entry.official_score,
            entry.lower_quartile_score,
            entry.minimum_point_score,
            entry.centre_score,
            entry.centre_worst_fold_3x_score,
            entry.centre_3x_drawdown,
            entry.centre_turnover,
        )
        if not all(math.isfinite(value) for value in fields):
            raise ValueError(f"ranking fields are non-finite for {entry.team_id}")
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                not entry.valid,
                -round_half_even(entry.official_score, policy=rules),
                -round_half_even(entry.lower_quartile_score, policy=rules),
                -round_half_even(entry.minimum_point_score, policy=rules),
                -round_half_even(entry.centre_score, policy=rules),
                -round_half_even(entry.centre_worst_fold_3x_score, policy=rules),
                round_half_even(entry.centre_3x_drawdown, policy=rules),
                round_half_even(entry.centre_turnover, policy=rules),
                entry.bundle_sha256,
                entry.team_id,
            ),
        )
    )
