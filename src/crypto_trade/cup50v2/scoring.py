"""Frozen CUP-50 v2 holdout-only scoring and total ordering."""

from __future__ import annotations

import dataclasses
import decimal
import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2.config import FOLDS, OOS_END, OOS_START
from crypto_trade.cup50v2.replay import EvaluationResultV2

_SIX_PLACES = decimal.Decimal("0.000001")
_COST_WEIGHTS = {1: 0.20, 2: 0.30, 3: 0.50}
_WEAKEST_FOLD_WEIGHTS = (0.40, 0.25, 0.20, 0.10, 0.05)


def round_half_even(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("score fields must be finite before rounding")
    return float(
        decimal.Decimal(str(value)).quantize(_SIX_PLACES, rounding=decimal.ROUND_HALF_EVEN)
    )


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
) -> CellScore:
    """Score one coherent candidate/window/cost cell exactly once."""
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
    activity = float((daily["gross_exposure"] >= 0.05).mean())
    utilization = min(1.0, volatility / 0.10, activity / 0.50)
    absolute = gross.abs()
    total_absolute = float(absolute.sum())
    concentration = (
        float(absolute.nlargest(5).sum() / total_absolute) if total_absolute > 0 else 1.0
    )
    x = (
        growth
        - 0.50 * drawdown
        - 0.10 * (1.0 - utilization)
        - 0.05 * max(0.0, (concentration - 0.25) / 0.75)
    )
    if not all(
        math.isfinite(value)
        for value in (growth, drawdown, volatility, activity, utilization, concentration, x)
    ):
        return CellScore(0.0, -1_000_000_000.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1_000_000_000.0, True)
    q = 50.0 * (1.0 + math.tanh(x / 0.10))
    q = min(100.0, max(0.0, q))
    return CellScore(q, growth, drawdown, volatility, activity, utilization, concentration, x)


def combine_costs(cells: Mapping[int, CellScore]) -> float:
    if set(cells) != set(_COST_WEIGHTS):
        raise ValueError("a CUP-50 v2 cost aggregate requires exactly 1x, 2x, and 3x cells")
    return sum(_COST_WEIGHTS[cost] * cells[cost].q for cost in (1, 2, 3))


def score_point(
    results: Mapping[int, EvaluationResultV2 | pd.DataFrame | None],
    *,
    failed_cells: Sequence[tuple[str, int]] = (),
) -> PointScore:
    """Five chronological folds, weakest-first aggregation, then the full 30-month path."""
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
            )
        fold_cells[name] = cells
        fold_scores[name] = combine_costs(cells)
    weakest = sorted(fold_scores.values())
    generalization = sum(
        weight * value for weight, value in zip(_WEAKEST_FOLD_WEIGHTS, weakest, strict=True)
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
        )
    all_window = combine_costs(all_cells)
    point = 0.85 * generalization + 0.15 * all_window
    return PointScore(point, generalization, all_window, fold_scores, fold_cells, all_cells)


def score_neighbourhood(
    points: Sequence[PointScore | float], *, centre_index: int = 0
) -> NeighbourhoodScore:
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
    lower_position = math.ceil(len(values) / 4) - 1
    lower = ordered[lower_position]
    median = float(np.median(values))
    centre = values[centre_index]
    official = 0.50 * median + 0.25 * lower + 0.25 * centre
    return NeighbourhoodScore(official, centre, median, lower, min(values), values)


def rounded_neighbourhood(score: NeighbourhoodScore) -> NeighbourhoodScore:
    return NeighbourhoodScore(
        official_score=round_half_even(score.official_score),
        centre_score=round_half_even(score.centre_score),
        median_score=round_half_even(score.median_score),
        lower_quartile_score=round_half_even(score.lower_quartile_score),
        minimum_score=round_half_even(score.minimum_score),
        point_scores=tuple(round_half_even(value) for value in score.point_scores),
    )


def rank_entries(entries: Sequence[RankedEntry]) -> tuple[RankedEntry, ...]:
    """Deterministic total order with every valid submission ahead of every DNF."""
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
                -round_half_even(entry.official_score),
                -round_half_even(entry.lower_quartile_score),
                -round_half_even(entry.minimum_point_score),
                -round_half_even(entry.centre_score),
                -round_half_even(entry.centre_worst_fold_3x_score),
                round_half_even(entry.centre_3x_drawdown),
                round_half_even(entry.centre_turnover),
                entry.bundle_sha256,
                entry.team_id,
            ),
        )
    )
