"""Pure hybrid finalist scoring for the Top-40 V2 tournament.

The objective score is locked before jury input or later integrity adjudication:

* 50 fixed-band absolute points;
* 20 tie-aware cohort-relative points;
* 15 bounded Critic points; and
* 15 bounded user points.

Only locked finalists belong in this module. A DNF has no final-OOS performance record and is never
manufactured as a zero-score submission. An empty finalist iterable therefore returns the explicit
``no-qualified-model`` outcome required by the V2 charter.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Iterable, Mapping, Sequence
from typing import Literal

REQUIRED_REGIMES = ("bear", "bull", "chop", "stress")

# Each tuple is (component name, maximum points). Keeping these as ordered immutable tuples makes
# the published formula and component serialization deterministic.
ABSOLUTE_COMPONENT_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("final_oos_sharpe", 15.0),
    ("final_oos_drawdown", 10.0),
    ("double_cost_oos_sharpe", 8.0),
    ("final_oos_annualized_return", 5.0),
    ("final_oos_positive_quarters", 3.0),
    ("regime_robustness", 4.0),
    ("generalization_role_stability", 5.0),
)

RELATIVE_COMPONENT_WEIGHTS: tuple[tuple[str, float], ...] = (
    ("final_oos_sharpe", 7.0),
    ("final_oos_drawdown", 4.0),
    ("double_cost_oos_sharpe", 3.0),
    ("final_oos_annualized_return", 2.0),
    ("worst_regime_sharpe", 2.0),
    ("generalization_role_stability", 2.0),
)

if not math.isclose(sum(weight for _, weight in ABSOLUTE_COMPONENT_WEIGHTS), 50.0):
    raise AssertionError("V2 absolute component weights must total 50")
if not math.isclose(sum(weight for _, weight in RELATIVE_COMPONENT_WEIGHTS), 20.0):
    raise AssertionError("V2 relative component weights must total 20")


def _finite(value: object, label: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be numeric")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _fraction(value: object, label: str) -> float:
    result = _finite(value, label)
    if not 0.0 <= result <= 1.0:
        raise ValueError(f"{label} must be in [0, 1]")
    return result


@dataclasses.dataclass(frozen=True)
class WindowPerformance:
    """Canonical metrics for one development, private, or final-OOS window."""

    net_sharpe: float
    annualized_return: float
    calmar: float
    max_drawdown: float
    positive_quarter_fraction: float

    def __post_init__(self) -> None:
        for field in ("net_sharpe", "annualized_return", "calmar"):
            object.__setattr__(self, field, _finite(getattr(self, field), field))
        drawdown = _fraction(self.max_drawdown, "max_drawdown")
        object.__setattr__(self, "max_drawdown", drawdown)
        quarters = _fraction(
            self.positive_quarter_fraction, "positive_quarter_fraction"
        )
        object.__setattr__(self, "positive_quarter_fraction", quarters)


@dataclasses.dataclass(frozen=True)
class RoleStabilityObservations:
    """Centrally measured sleeve-role and development-stability observations."""

    bull_long_attribution: float
    bear_short_attribution: float
    chop_combined_return: float
    parameter_stability: float
    positive_fold_fraction: float

    def __post_init__(self) -> None:
        for field in (
            "bull_long_attribution",
            "bear_short_attribution",
            "chop_combined_return",
        ):
            object.__setattr__(self, field, _finite(getattr(self, field), field))
        object.__setattr__(
            self,
            "parameter_stability",
            _fraction(self.parameter_stability, "parameter_stability"),
        )
        object.__setattr__(
            self,
            "positive_fold_fraction",
            _fraction(self.positive_fold_fraction, "positive_fold_fraction"),
        )

    @property
    def positive_role_fraction(self) -> float:
        observations = (
            self.bull_long_attribution,
            self.bear_short_attribution,
            self.chop_combined_return,
        )
        return sum(value > 0.0 for value in observations) / len(observations)


@dataclasses.dataclass(frozen=True)
class FinalistPerformance:
    """Immutable, complete performance input for one locked V2 finalist."""

    team_id: str
    development: WindowPerformance
    private: WindowPerformance
    final_oos: WindowPerformance
    double_cost_oos_sharpe: float
    regime_sharpes: tuple[tuple[str, float], ...]
    role_stability: RoleStabilityObservations

    def __post_init__(self) -> None:
        if (
            not isinstance(self.team_id, str)
            or not self.team_id
            or self.team_id.strip() != self.team_id
        ):
            raise ValueError("team_id must be a nonempty trimmed string")
        for field in ("development", "private", "final_oos"):
            if not isinstance(getattr(self, field), WindowPerformance):
                raise ValueError(f"{field} must be WindowPerformance")
        if not isinstance(self.role_stability, RoleStabilityObservations):
            raise ValueError("role_stability must be RoleStabilityObservations")
        object.__setattr__(
            self,
            "double_cost_oos_sharpe",
            _finite(self.double_cost_oos_sharpe, "double_cost_oos_sharpe"),
        )
        try:
            raw_regimes = tuple(self.regime_sharpes)
        except TypeError as exc:
            raise ValueError("regime_sharpes must contain (name, sharpe) pairs") from exc
        regimes: list[tuple[str, float]] = []
        for item in raw_regimes:
            if not isinstance(item, Sequence) or isinstance(item, (str, bytes)) or len(item) != 2:
                raise ValueError("regime_sharpes must contain (name, sharpe) pairs")
            name, value = item
            if not isinstance(name, str):
                raise ValueError("regime names must be strings")
            regimes.append((name, _finite(value, f"regime_sharpes.{name}")))
        names = [name for name, _ in regimes]
        if len(names) != len(set(names)):
            raise ValueError("regime_sharpes contains duplicate regimes")
        if set(names) != set(REQUIRED_REGIMES):
            raise ValueError(f"regime_sharpes must contain exactly {list(REQUIRED_REGIMES)}")
        object.__setattr__(self, "regime_sharpes", tuple(sorted(regimes)))

    def regime_sharpe(self, name: str) -> float:
        return dict(self.regime_sharpes)[name]


@dataclasses.dataclass(frozen=True)
class FinalistScore:
    team_id: str
    rank: int | None
    objective_rank: int
    absolute_score: float
    relative_score: float
    automatic_score: float
    critic_score: float
    user_score: float
    total_score: float | None
    absolute_components: tuple[tuple[str, float], ...]
    relative_components: tuple[tuple[str, float], ...]
    integrity_disqualified: bool = False
    disqualification_reasons: tuple[str, ...] = ()


ScoreStatus = Literal["scored", "no-qualified-model"]


@dataclasses.dataclass(frozen=True)
class TournamentScoreResult:
    status: ScoreStatus
    winner_team_id: str | None
    scores: tuple[FinalistScore, ...]


def _higher_band(value: float, zero_at: float, full_at: float) -> float:
    if full_at <= zero_at:
        raise ValueError("higher-is-better band requires full_at > zero_at")
    return min(1.0, max(0.0, (value - zero_at) / (full_at - zero_at)))


def _lower_band(value: float, full_at: float, zero_at: float) -> float:
    if zero_at <= full_at:
        raise ValueError("lower-is-better band requires zero_at > full_at")
    return min(1.0, max(0.0, (zero_at - value) / (zero_at - full_at)))


def _regime_values(performance: FinalistPerformance) -> tuple[float, ...]:
    return tuple(value for _, value in performance.regime_sharpes)


def _stability_composite(performance: FinalistPerformance) -> float:
    cross_window_floor = min(
        performance.development.net_sharpe,
        performance.private.net_sharpe,
        performance.final_oos.net_sharpe,
    )
    return (
        _higher_band(cross_window_floor, 0.0, 0.75)
        + performance.role_stability.parameter_stability
        + performance.role_stability.positive_fold_fraction
        + performance.role_stability.positive_role_fraction
    ) / 4.0


def _absolute_components(performance: FinalistPerformance) -> tuple[tuple[str, float], ...]:
    regimes = _regime_values(performance)
    worst_regime = min(regimes)
    positive_regime_fraction = sum(value > 0.0 for value in regimes) / len(regimes)
    stability = performance.role_stability
    cross_window_floor = min(
        performance.development.net_sharpe,
        performance.private.net_sharpe,
        performance.final_oos.net_sharpe,
    )

    # Config-frozen anchors are used verbatim for the three primary components. The remaining
    # bands are explicit V2 formula constants and should be promoted into config before Phase 0.
    components = (
        (
            "final_oos_sharpe",
            15.0 * _higher_band(performance.final_oos.net_sharpe, 0.0, 1.5),
        ),
        (
            "final_oos_drawdown",
            10.0 * _lower_band(performance.final_oos.max_drawdown, 0.15, 0.40),
        ),
        (
            "double_cost_oos_sharpe",
            8.0 * _higher_band(performance.double_cost_oos_sharpe, 0.0, 0.75),
        ),
        (
            "final_oos_annualized_return",
            5.0 * _higher_band(performance.final_oos.annualized_return, 0.0, 0.30),
        ),
        (
            "final_oos_positive_quarters",
            3.0
            * _higher_band(performance.final_oos.positive_quarter_fraction, 0.50, 0.75),
        ),
        (
            "regime_robustness",
            2.5 * _higher_band(worst_regime, -0.25, 0.75)
            + 1.5 * positive_regime_fraction,
        ),
        (
            "generalization_role_stability",
            2.0 * _higher_band(cross_window_floor, 0.0, 0.75)
            + stability.parameter_stability
            + stability.positive_fold_fraction
            + stability.positive_role_fraction,
        ),
    )
    return tuple((name, round(points, 6)) for name, points in components)


def _relative_values(performance: FinalistPerformance) -> dict[str, float]:
    return {
        "final_oos_sharpe": performance.final_oos.net_sharpe,
        "final_oos_drawdown": performance.final_oos.max_drawdown,
        "double_cost_oos_sharpe": performance.double_cost_oos_sharpe,
        "final_oos_annualized_return": performance.final_oos.annualized_return,
        "worst_regime_sharpe": min(_regime_values(performance)),
        "generalization_role_stability": _stability_composite(performance),
    }


def _average_percentiles(
    values: Mapping[str, float], *, higher_is_better: bool
) -> dict[str, float]:
    """Return [0,1] average-rank percentiles; a one-team cohort receives neutral 0.5."""

    if not values:
        return {}
    ordered = sorted(
        values.items(),
        key=lambda item: (item[1], item[0]) if higher_is_better else (-item[1], item[0]),
    )
    if len(ordered) == 1:
        return {ordered[0][0]: 0.5}
    percentiles: dict[str, float] = {}
    index = 0
    while index < len(ordered):
        stop = index + 1
        while stop < len(ordered) and ordered[stop][1] == ordered[index][1]:
            stop += 1
        average_position = (index + stop - 1) / 2.0
        percentile = average_position / (len(ordered) - 1)
        for tied_index in range(index, stop):
            percentiles[ordered[tied_index][0]] = percentile
        index = stop
    return percentiles


def _jury_score(value: object, label: str) -> float:
    score = _finite(value, label)
    if not 0.0 <= score <= 15.0:
        raise ValueError(f"{label} must be in [0, 15]")
    return score


def _validate_score_keys(
    values: Mapping[str, object], team_ids: set[str], label: str
) -> None:
    unknown = set(values) - team_ids
    if unknown:
        raise ValueError(f"{label} names unknown finalists: {sorted(unknown)}")


def score_finalists(
    finalists: Iterable[FinalistPerformance],
    *,
    critic_scores: Mapping[str, float] | None = None,
    user_scores: Mapping[str, float] | None = None,
    integrity_disqualifications: Mapping[str, Sequence[str]] | None = None,
) -> TournamentScoreResult:
    """Score a variable locked finalist cohort and optionally apply later integrity DQs."""

    finalist_list = list(finalists)
    if any(not isinstance(finalist, FinalistPerformance) for finalist in finalist_list):
        raise ValueError("finalists must contain only FinalistPerformance records")
    team_ids = [finalist.team_id for finalist in finalist_list]
    if len(team_ids) != len(set(team_ids)):
        raise ValueError("duplicate team_id in finalist cohort")
    team_id_set = set(team_ids)
    critic = critic_scores or {}
    user = user_scores or {}
    disqualifications = integrity_disqualifications or {}
    _validate_score_keys(critic, team_id_set, "critic_scores")
    _validate_score_keys(user, team_id_set, "user_scores")
    _validate_score_keys(disqualifications, team_id_set, "integrity_disqualifications")

    if not finalist_list:
        return TournamentScoreResult(
            status="no-qualified-model", winner_team_id=None, scores=()
        )

    absolute_by_team = {
        finalist.team_id: _absolute_components(finalist) for finalist in finalist_list
    }
    raw_relative = {
        finalist.team_id: _relative_values(finalist) for finalist in finalist_list
    }
    relative_percentiles: dict[str, dict[str, float]] = {}
    for component, _ in RELATIVE_COMPONENT_WEIGHTS:
        relative_percentiles[component] = _average_percentiles(
            {
                team_id: values[component]
                for team_id, values in raw_relative.items()
            },
            higher_is_better=component != "final_oos_drawdown",
        )

    relative_by_team: dict[str, tuple[tuple[str, float], ...]] = {}
    automatic_by_team: dict[str, float] = {}
    for finalist in finalist_list:
        team_id = finalist.team_id
        relative_components = tuple(
            (
                component,
                round(weight * relative_percentiles[component][team_id], 6),
            )
            for component, weight in RELATIVE_COMPONENT_WEIGHTS
        )
        relative_by_team[team_id] = relative_components
        absolute_score = sum(points for _, points in absolute_by_team[team_id])
        relative_score = sum(points for _, points in relative_components)
        automatic_by_team[team_id] = round(absolute_score + relative_score, 6)

    objective_order = sorted(team_ids, key=lambda team_id: (-automatic_by_team[team_id], team_id))
    objective_ranks = {
        team_id: rank for rank, team_id in enumerate(objective_order, start=1)
    }

    unranked: list[FinalistScore] = []
    for finalist in finalist_list:
        team_id = finalist.team_id
        critic_score = _jury_score(critic.get(team_id, 0.0), f"critic_scores.{team_id}")
        user_score = _jury_score(user.get(team_id, 0.0), f"user_scores.{team_id}")
        absolute_score = round(sum(points for _, points in absolute_by_team[team_id]), 6)
        relative_score = round(sum(points for _, points in relative_by_team[team_id]), 6)
        automatic_score = automatic_by_team[team_id]
        unranked.append(
            FinalistScore(
                team_id=team_id,
                rank=None,
                objective_rank=objective_ranks[team_id],
                absolute_score=absolute_score,
                relative_score=relative_score,
                automatic_score=automatic_score,
                critic_score=critic_score,
                user_score=user_score,
                total_score=round(automatic_score + critic_score + user_score, 6),
                absolute_components=absolute_by_team[team_id],
                relative_components=relative_by_team[team_id],
            )
        )

    ordered = sorted(
        unranked,
        key=lambda score: (-float(score.total_score), score.team_id),
    )
    locked = TournamentScoreResult(
        status="scored",
        winner_team_id=ordered[0].team_id,
        scores=tuple(
            dataclasses.replace(score, rank=rank)
            for rank, score in enumerate(ordered, start=1)
        ),
    )
    if disqualifications:
        return apply_integrity_disqualifications(locked, disqualifications)
    return locked


def apply_integrity_disqualifications(
    locked: TournamentScoreResult,
    disqualifications: Mapping[str, Sequence[str]],
) -> TournamentScoreResult:
    """Apply later integrity DQs without recomputing locked objective scores or ranks."""

    team_ids = {score.team_id for score in locked.scores}
    _validate_score_keys(disqualifications, team_ids, "integrity_disqualifications")
    if locked.status == "no-qualified-model":
        return locked

    updated: list[FinalistScore] = []
    for score in locked.scores:
        new_reasons = disqualifications.get(score.team_id, ())
        if isinstance(new_reasons, (str, bytes)):
            raise ValueError(
                "integrity disqualification reasons must be a sequence of nonempty strings"
            )
        reasons = list(score.disqualification_reasons)
        for reason in new_reasons:
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("integrity disqualification reasons must be nonempty strings")
            if reason not in reasons:
                reasons.append(reason)
        if reasons:
            updated.append(
                dataclasses.replace(
                    score,
                    rank=None,
                    total_score=None,
                    integrity_disqualified=True,
                    disqualification_reasons=tuple(reasons),
                )
            )
        else:
            updated.append(score)

    valid = sorted(
        (score for score in updated if not score.integrity_disqualified),
        key=lambda score: (-float(score.total_score), score.team_id),
    )
    ranked_valid = [
        dataclasses.replace(score, rank=rank)
        for rank, score in enumerate(valid, start=1)
    ]
    disqualified = sorted(
        (score for score in updated if score.integrity_disqualified),
        key=lambda score: (score.objective_rank, score.team_id),
    )
    return TournamentScoreResult(
        status="scored",
        winner_team_id=ranked_valid[0].team_id if ranked_valid else None,
        scores=tuple((*ranked_valid, *disqualified)),
    )
