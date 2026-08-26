"""Driving a candidate through evaluation and publishing to two disjoint artifact roots.

The sealed design rests on a property that is easy to state and easy to lose: **nothing a team sees
may be a function of a sealed day.** The evaluator has to run the whole development window
continuously -- carried positions, funding accrual and forced exits are path-dependent and cannot be
skipped -- so the split is an operation on the scoring index, applied after the fact, in code that a
later refactor could quietly widen.

This module makes that structural rather than careful. There are two entry points:

* :func:`run_development_trial` is handed the **visible** index and writes to the visible reports
  root. It never receives the sealed index, so it cannot compute a sealed statistic to leak.
* :func:`run_sealed_confirmation` is handed the **sealed** index and writes to the organizer's
  private root. It returns nothing a team-facing caller would have a use for.

Neither function takes both windows. A filter can be forgotten; a parameter that was never passed
cannot be consulted. :func:`assert_windows_are_disjoint` closes the remaining gap by refusing a pair
of indexes that overlap at all, so a mis-derived schedule fails here rather than silently scoring
the same day twice.

The cost ladder is evaluated once and shared by both. Three independent evaluator runs at 1x, 2x and
3x costs, never an analytic rescale of one: costs interact with the participation cap and with
forced exits, so a book that survives arithmetically can still die when the costs are really charged
-- which is the whole point of asking.
"""

from __future__ import annotations

import dataclasses
import json
from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.v5 import metrics
from crypto_trade.tournament.v5.engine import EvaluationResult, EvaluatorConfig, evaluate_targets
from crypto_trade.tournament.v5.gates import (
    DEVELOPMENT_STAGE,
    SEALED_STAGE,
    Assessment,
    GateThresholds,
    assess,
)

# What a team is entitled to see about its own trial. An allowlist: a field added to the packet
# later is withheld until someone decides it should not be. Forgetting to allow something costs a
# team information; forgetting to deny something costs the edition its blindness.
TEAM_VISIBLE_FIELDS = (
    "days",
    "annualised_return",
    "annualised_volatility",
    "net_sharpe",
    "double_cost_sharpe",
    "triple_cost_annualised_return",
    "max_drawdown",
    "positive_fold_fraction",
    "mean_gross_exposure",
    "median_effective_breadth",
    "breadth_pass_fraction",
    "active_bar_fraction",
    "long_exposure_share",
    "short_exposure_share",
    "risk_unit_capped_fraction",
    "annualised_turnover",
    "gross_edge_bps_per_turnover",
    "cost_share_of_positive_gross",
    "ruined",
)


class RunnerError(RuntimeError):
    """A trial could not be run, or was asked to score a window it must not see."""


def assert_windows_are_disjoint(visible: pd.DatetimeIndex, sealed: pd.DatetimeIndex) -> None:
    """Refuse a schedule whose two halves overlap.

    Cheap, and it fails at the one moment the overlap is still theoretical. An earlier version of
    the metric layer silently scored 705 days out of a 400-day window because a resample spanned the
    gaps a sealed carve leaves behind; the arithmetic is what exposed it, so the arithmetic is
    checked here every time.
    """

    overlap = visible.intersection(sealed)
    if len(overlap) > 0:
        raise RunnerError(
            f"visible and sealed windows overlap on {len(overlap)} day(s), "
            f"first {overlap[0].date()}: the sealed blocks would not be held out"
        )


@dataclasses.dataclass(frozen=True, slots=True)
class CostLadder:
    """One candidate, evaluated independently at each cost multiple."""

    base: EvaluationResult
    double: EvaluationResult
    triple: EvaluationResult

    def daily(self, which: str) -> pd.Series:
        result = {"base": self.base, "double": self.double, "triple": self.triple}[which]
        return metrics.daily_returns(result.returns)


def evaluate_cost_ladder(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    targets: pd.DataFrame,
    *,
    mark_prices: pd.DataFrame,
    config: EvaluatorConfig | None = None,
    risk_policy=None,  # type: ignore[no-untyped-def]
) -> CostLadder:
    """Three independent runs. Never one run rescaled.

    CUP-50 v2 is the reason the 3x rung carries weight in this edition rather than sitting in a
    footnote: it weighted its cost cells 0.20/0.30/0.50 instead of front-loading the cheap one, and
    was the first edition whose in-sample rank predicted out-of-sample rank -- "so a lane that would
    die of costs died where its team could see it."
    """

    runs = {
        multiple: evaluate_targets(
            bars,
            funding,
            membership,
            targets,
            mark_prices=mark_prices,
            config=config,
            cost_multiplier=multiple,
            risk_policy=risk_policy,
        )
        for multiple in (1.0, 2.0, 3.0)
    }
    return CostLadder(base=runs[1.0], double=runs[2.0], triple=runs[3.0])


def _summarise(
    ladder: CostLadder,
    index: pd.DatetimeIndex,
    *,
    trial_count: int,
    trial_sharpe_dispersion: float,
    breadth_floor: float,
) -> metrics.MetricPacket:
    return metrics.summarize(
        ladder.base,
        index,
        double_cost_returns=ladder.daily("double"),
        triple_cost_returns=ladder.daily("triple"),
        trial_count=trial_count,
        trial_sharpe_dispersion=trial_sharpe_dispersion,
        breadth_floor=breadth_floor,
    )


def _publish(root: str | Path, name: str, payload: Mapping[str, object]) -> Path:
    destination = Path(root)
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


@dataclasses.dataclass(frozen=True, slots=True)
class DevelopmentTrial:
    """What a development trial produced. Contains no sealed-window quantity, by construction."""

    team_id: str
    trial_id: str
    packet: metrics.MetricPacket
    assessment: Assessment
    feedback: Mapping[str, object]
    artifact_path: Path

    @property
    def admitted(self) -> bool:
        """Whether the book is a valid entry at all.

        Structure and cost only. A development Sharpe is a statement about a search rather than an
        edge -- every floor set in the repository admitted zero of V4-R9's ninety-four measured
        trials -- so performance is reported here and enforced only on the sealed blocks.
        """

        return self.assessment.eligible


def run_development_trial(
    ladder: CostLadder,
    visible_index: pd.DatetimeIndex,
    thresholds: GateThresholds,
    *,
    team_id: str,
    trial_id: str,
    reports_root: str | Path,
    trial_count: int,
    trial_sharpe_dispersion: float,
    accepted_trials: int,
    source_review_passed: bool,
    invariance_suite_passed: bool,
) -> DevelopmentTrial:
    """Score the visible window and publish where the team can read it.

    Note what this signature does not accept: the sealed index. That is the point -- the function
    that builds a team's feedback has no access to the days the confirmation stage will use, so no
    amount of later editing inside it can leak one.
    """

    packet = _summarise(
        ladder,
        visible_index,
        trial_count=trial_count,
        trial_sharpe_dispersion=trial_sharpe_dispersion,
        breadth_floor=thresholds.minimum_median_effective_breadth,
    )
    evidence = metrics.evidence_from_packet(
        packet,
        accepted_trials=accepted_trials,
        source_review_passed=source_review_passed,
        invariance_suite_passed=invariance_suite_passed,
    )
    assessment = assess(evidence, thresholds, stage=DEVELOPMENT_STAGE)
    feedback = metrics.team_feedback(packet, TEAM_VISIBLE_FIELDS)

    artifact = _publish(
        reports_root,
        f"{team_id}.{trial_id}.json",
        {
            "team_id": team_id,
            "trial_id": trial_id,
            "stage": DEVELOPMENT_STAGE,
            "packet": packet.as_dict(),
            "gates": dict(assessment.gates),
            "enforced": list(assessment.enforced),
            "reported": list(assessment.reported),
            "admitted": assessment.eligible,
        },
    )
    return DevelopmentTrial(
        team_id=team_id,
        trial_id=trial_id,
        packet=packet,
        assessment=assessment,
        feedback=feedback,
        artifact_path=artifact,
    )


@dataclasses.dataclass(frozen=True, slots=True)
class SealedConfirmation:
    """Organizer-only. Nothing here is ever handed to a lane."""

    team_id: str
    candidate_id: str
    packet: metrics.MetricPacket
    assessment: Assessment
    artifact_path: Path

    @property
    def cleared(self) -> bool:
        return self.assessment.eligible


def run_sealed_confirmation(
    ladder: CostLadder,
    sealed_index: pd.DatetimeIndex,
    thresholds: GateThresholds,
    *,
    team_id: str,
    candidate_id: str,
    private_root: str | Path,
    accepted_trials: int,
    source_review_passed: bool,
    invariance_suite_passed: bool,
) -> SealedConfirmation:
    """Score the sealed blocks. Publishes only into the organizer's private root.

    The trial count is **one**, and that is not an oversight. A team selected its nominee from a
    search over *visible* data; the sealed blocks never saw that search, so holding them out is
    already the correction and the sealed estimate is unbiased. Deflating it again by the team's
    trial count charges the same search twice -- measured, it costs more than half the power at a
    true Sharpe of 1.0 while barely moving the false-positive rate.
    """

    packet = _summarise(
        ladder,
        sealed_index,
        trial_count=metrics.SEALED_TRIALS,
        trial_sharpe_dispersion=0.0,
        breadth_floor=thresholds.minimum_median_effective_breadth,
    )
    evidence = metrics.evidence_from_packet(
        packet,
        accepted_trials=accepted_trials,
        source_review_passed=source_review_passed,
        invariance_suite_passed=invariance_suite_passed,
    )
    assessment = assess(evidence, thresholds, stage=SEALED_STAGE)

    artifact = _publish(
        private_root,
        f"{team_id}.{candidate_id}.sealed.json",
        {
            "team_id": team_id,
            "candidate_id": candidate_id,
            "stage": SEALED_STAGE,
            "packet": packet.as_dict(),
            "gates": dict(assessment.gates),
            "enforced": list(assessment.enforced),
            "cleared": assessment.eligible,
        },
    )
    return SealedConfirmation(
        team_id=team_id,
        candidate_id=candidate_id,
        packet=packet,
        assessment=assessment,
        artifact_path=artifact,
    )


def assert_no_sealed_artifact_is_visible(
    reports_root: str | Path, sealed_markers: Sequence[str] = ("sealed",)
) -> None:
    """The visible root must not contain a sealed artifact, under any name.

    Checked by looking rather than assumed from the call sites. The two roots are only disjoint for
    as long as nobody writes to the wrong one, and this is what notices when somebody does.
    """

    root = Path(reports_root)
    if not root.is_dir():
        return
    offending = [
        path.name
        for path in root.rglob("*")
        if path.is_file() and any(marker in path.name.lower() for marker in sealed_markers)
    ]
    if offending:
        raise RunnerError(
            f"sealed artifacts found in the visible reports root: {sorted(offending)}"
        )


__all__ = [
    "TEAM_VISIBLE_FIELDS",
    "CostLadder",
    "DevelopmentTrial",
    "RunnerError",
    "SealedConfirmation",
    "assert_no_sealed_artifact_is_visible",
    "assert_windows_are_disjoint",
    "evaluate_cost_ladder",
    "run_development_trial",
    "run_sealed_confirmation",
]
