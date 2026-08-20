"""Frozen CUP-50 v2 holdout-only scoring and total ordering."""

from __future__ import annotations

import dataclasses
import decimal
import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.cup50v2.config import (
    FOLDS,
    IS_FOLDS,
    IS_START,
    OOS_END,
    OOS_START,
    ScoringPolicy,
    active_policy,
)
from crypto_trade.cup50v2.regimes import REGIMES, RegimePolicy
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
    regime: float
    all_window: float
    fold_scores: Mapping[str, float]
    fold_cost_cells: Mapping[str, Mapping[int, CellScore]]
    regime_scores: Mapping[str, float]
    regime_cost_cells: Mapping[str, Mapping[int, CellScore]]
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
    # Cleared the pre-registered in-sample bar. Ineligible lanes are still observed and published
    # in full; they simply cannot win.
    eligible: bool = False
    eligibility_reason: str = ""


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


_FAILED_CELL = CellScore(0.0, -1_000_000_000.0, 1.0, 0.0, 0.0, 0.0, 1.0, -1_000_000_000.0, True)


def score_daily(daily: pd.DataFrame, *, policy: ScoringPolicy | None = None) -> CellScore:
    """Score a set of scored days, which need not be contiguous.

    Folds hand this a calendar slice; regimes hand it every day carrying one label. Growth,
    activity, volatility and concentration are day-set statistics either way, and the drawdown is
    the loss the book would have taken had those days run back to back.
    """
    rules = _scoring(policy)
    n = len(daily)
    if n == 0:
        return _FAILED_CELL
    net = daily["net_return"].astype(float)
    gross = daily["gross_return"].astype(float)
    if (net <= -1.0).any():
        return _FAILED_CELL
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
        return _FAILED_CELL
    if activity < rules.minimum_activity:
        # A book that never deploys is not a low-risk book, it is an absent one. CUP-50 paid it
        # more than it paid genuine trading that lost money, and two lanes collected.
        return CellScore(0.0, growth, drawdown, volatility, activity, utilization, concentration, x)
    q = 50.0 * (1.0 + math.tanh(x / rules.squash_scale))
    q = min(100.0, max(0.0, q))
    return CellScore(q, growth, drawdown, volatility, activity, utilization, concentration, x)


def score_cell(
    returns: pd.DataFrame,
    start: pd.Timestamp,
    end: pd.Timestamp,
    *,
    failed: bool = False,
    policy: ScoringPolicy | None = None,
) -> CellScore:
    """Score one coherent candidate/window/cost cell exactly once."""
    if failed:
        return _FAILED_CELL
    return score_daily(_daily_frame(returns, start, end), policy=policy)


def combine_costs(cells: Mapping[int, CellScore], *, policy: ScoringPolicy | None = None) -> float:
    weights = _scoring(policy).cost_weights
    if set(cells) != set(weights):
        raise ValueError("a CUP-50 v2 cost aggregate requires exactly 1x, 2x, and 3x cells")
    return sum(weights[cost] * cells[cost].q for cost in sorted(weights))


def _regime_days(daily: pd.DataFrame, labels: Mapping[str, str], regime: str) -> pd.DataFrame:
    months = pd.DatetimeIndex(daily.index).strftime("%Y-%m")
    selector = np.array([labels.get(month) == regime for month in months], dtype=bool)
    return daily.loc[selector]


def score_window(
    results: Mapping[int, EvaluationResultV2 | pd.DataFrame | None],
    *,
    window: tuple[pd.Timestamp, pd.Timestamp],
    folds: Sequence[tuple[str, pd.Timestamp, pd.Timestamp]],
    fold_weights: Sequence[float],
    regime_labels: Mapping[str, str],
    failed_cells: Sequence[tuple[str, int]] = (),
    policy: ScoringPolicy | None = None,
    regime_policy: RegimePolicy | None = None,
) -> PointScore:
    """Score one point over one window: weakest-fold, weakest-regime, and the whole path.

    Folds ask whether a book survived each stretch of calendar time. Regimes ask whether it
    survived each kind of market, which is the question the tournament is actually for, and which a
    half-year fold cannot answer because every one of them mixes regimes.
    """
    rules = _scoring(policy)
    regime_rules = regime_policy if regime_policy is not None else active_policy().regimes
    costs = tuple(sorted(rules.cost_weights))
    if set(results) != set(costs):
        raise ValueError("point scoring requires independent 1x, 2x, and 3x results")
    failure_set = set(failed_cells)
    start, end = window

    def frame_for(cost: int) -> pd.DataFrame | None:
        value = results[cost]
        return value.returns if isinstance(value, EvaluationResultV2) else value

    fold_scores: dict[str, float] = {}
    fold_cells: dict[str, dict[int, CellScore]] = {}
    for name, fold_start, fold_end in folds:
        cells: dict[int, CellScore] = {}
        for cost in costs:
            frame = frame_for(cost)
            cells[cost] = score_cell(
                pd.DataFrame() if frame is None else frame,
                fold_start,
                fold_end,
                failed=results[cost] is None or (name, cost) in failure_set,
                policy=rules,
            )
        fold_cells[name] = cells
        fold_scores[name] = combine_costs(cells, policy=rules)
    weakest = sorted(fold_scores.values())
    generalization = sum(
        weight * value for weight, value in zip(fold_weights, weakest, strict=True)
    )

    regime_scores: dict[str, float] = {}
    regime_cells: dict[str, dict[int, CellScore]] = {}
    for regime in REGIMES:
        cells = {}
        represented = True
        for cost in costs:
            frame = frame_for(cost)
            if frame is None or (regime, cost) in failure_set:
                cells[cost] = _FAILED_CELL
                continue
            days = _regime_days(_daily_frame(frame, start, end), regime_labels, regime)
            if len(days) < regime_rules.minimum_days:
                represented = False
                break
            cells[cost] = score_daily(days, policy=rules)
        if not represented:
            # Too little of this regime in the window to say anything; dropping it beats scoring a
            # fortnight as if it were a market state.
            continue
        regime_cells[regime] = cells
        regime_scores[regime] = combine_costs(cells, policy=rules)
    if regime_scores:
        ordered = sorted(regime_scores.values())
        weights = regime_rules.weights[: len(ordered)]
        total = sum(weights)
        regime = sum(weight * value for weight, value in zip(weights, ordered, strict=True)) / total
    else:
        regime = 0.0

    all_cells: dict[int, CellScore] = {}
    for cost in costs:
        frame = frame_for(cost)
        all_cells[cost] = score_cell(
            pd.DataFrame() if frame is None else frame,
            start,
            end,
            failed=results[cost] is None or ("ALL", cost) in failure_set,
            policy=rules,
        )
    all_window = combine_costs(all_cells, policy=rules)
    point = (
        rules.generalization_weight * generalization
        + rules.regime_weight * regime
        + rules.all_window_weight * all_window
    )
    return PointScore(
        point,
        generalization,
        regime,
        all_window,
        fold_scores,
        fold_cells,
        regime_scores,
        regime_cells,
        all_cells,
    )


def score_point(
    results: Mapping[int, EvaluationResultV2 | pd.DataFrame | None],
    *,
    regime_labels: Mapping[str, str],
    failed_cells: Sequence[tuple[str, int]] = (),
    policy: ScoringPolicy | None = None,
    regime_policy: RegimePolicy | None = None,
) -> PointScore:
    """Score a point on the sealed window: the result the leaderboard reports."""
    rules = _scoring(policy)
    return score_window(
        results,
        window=(OOS_START, OOS_END),
        folds=FOLDS,
        fold_weights=rules.fold_weights,
        regime_labels=regime_labels,
        failed_cells=failed_cells,
        policy=rules,
        regime_policy=regime_policy,
    )


def score_in_sample_point(
    results: Mapping[int, EvaluationResultV2 | pd.DataFrame | None],
    *,
    regime_labels: Mapping[str, str],
    failed_cells: Sequence[tuple[str, int]] = (),
    policy: ScoringPolicy | None = None,
    regime_policy: RegimePolicy | None = None,
) -> PointScore:
    """Score a point on the research window, in the units the qualification bar is stated in."""
    rules = _scoring(policy)
    return score_window(
        results,
        window=(IS_START, OOS_START),
        folds=IS_FOLDS,
        fold_weights=rules.is_fold_weights,
        regime_labels=regime_labels,
        failed_cells=failed_cells,
        policy=rules,
        regime_policy=regime_policy,
    )


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
    """Deterministic total order: eligible, then observed-ineligible, then DNF."""
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
                not entry.eligible,
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
