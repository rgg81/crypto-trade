"""Run one frozen candidate through the organiser's own pipeline, and coach on the result.

This is the only scorer. The alternative -- twelve teams each building a private one -- is not a
hypothetical: a private scorer will disagree about which cost level each floor reads, about where
the fold boundaries fall, about whether the risk unit runs before or after the caps, and about all
three in different directions. Every number a team acts on therefore comes out of the same
``run_candidate -> assemble_scored_metrics -> adjudicate_candidate`` path the organiser scores
nominations with, over the same full in-sample window, under the same frozen ``[execution]`` and
``[risk_unit]`` tables.

**The window is never shortened, and there is no flag to shorten it.** Section 7.1 makes the window
part of the material tuple, so a short-window run is a *different material trial*: it would cost
the same one-twelfth of the budget and produce a number comparable to nothing -- not to the team's
other runs, not to the floors, not to another team. Offering it would create a second, cheaper
currency of evidence, and the cheaper currency is the one that ends up driving decisions. What that
costs is real and is paid deliberately: an evaluation is about seven minutes, and there is no quick
look. What it does *not* cost is a trial spent on a typo, because :func:`check_candidate` exists --
it loads the entrypoint, builds the strategy, parses the risk policy and runs the blindness scan
without opening a single row of market data, so it produces no metric, is not an evaluation, and
consumes nothing.

**What a team is shown about its own failure: everything measured.** Every floor and every
threshold is already public in charter section 7.3 and in the playbook, and a team holds its own
returns, so reporting the observed value against the floor discloses nothing it could not compute
-- it only removes the incentive to compute it differently. The gradient worry is real and is
answered by the mechanism the charter already carries for it: the budget is twelve, and
``confidence = 1 - T(1 - B)`` makes every additional look strictly more expensive to survive.
Hiding numbers would not add discipline; it would add a second scorer.

**The falsification battery is run here, not by the team.** An exact sign inversion is mechanically
defined and its verdict is *disqualifying*, so it cannot be a self-report: a team implementing its
own inversion can get it wrong in ways nobody can audit, and can skip it entirely by accident.
:func:`run_falsification_battery` negates the emitted weights and nothing else, and scores the
result through the identical pipeline.
"""

from __future__ import annotations

import dataclasses
import importlib.util
import math
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.cup20.adjudication import CandidateAdjudication, adjudicate_candidate
from crypto_trade.cup20.archive import (
    WorkspaceScan,
    scan_workspace_for_blindness_violations,
    verify_neighbourhood_coordinates,
)
from crypto_trade.cup20.bootstrap import (
    circular_block_bootstrap_positive_fraction,
    trial_adjusted_confidence,
)
from crypto_trade.cup20.config import IS_END
from crypto_trade.cup20.metrics import Fold, daily_returns, fold_sharpes, is_folds, window_metrics
from crypto_trade.cup20.neighbourhood import load_declaration

# Private on purpose, and imported rather than reimplemented: the 1e-6 materiality threshold that
# decides which sides a book "actually traded" is a hard-floor input, and a second copy of it here
# could disagree with the copy the floors use -- which would show a team one set of observed roles
# while gating it on another.
from crypto_trade.cup20.qualification import _material_sides, evaluate_floors
from crypto_trade.cup20.runner import (
    CandidateRun,
    decision_grid,
    evaluator_config,
    run_candidate,
)
from crypto_trade.cup20.scored_metrics import (
    BASE_COST,
    DOUBLE_COST,
    STAGE_IN_SAMPLE,
    ScoredVector,
    assemble_scored_metrics,
)
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.cup20.trials import ENTRYPOINT, RISK_POLICY_FILENAME
from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy
from crypto_trade.tournament.risk_policy import RiskPolicy, load_risk_policy

CORE_FLOOR_CHECKS: tuple[str, ...] = (
    "net_sharpe",
    "double_cost_sharpe",
    "triple_cost_sharpe",
    "annualized_return",
    "double_cost_annualized_return",
    "max_drawdown",
    "annualized_volatility",
    "trade_count",
)
"""The **core performance floors** of section 7.3's falsification row.

The charter says an exact sign inversion that "clears the core floors" disqualifies the candidate,
without previously saying which floors are core. These are: the eight floors that are properties of
a single run's own return stream, and therefore mean the same thing for an inverted book as for the
book it inverts. Excluded, and why:

* ``neighbourhood_positive_fraction``, ``trial_adjusted_confidence`` -- properties of the team's
  research process, not of the run. An inversion does not have its own trial count.
* ``sign_inversion_not_profitable`` -- self-referential; it is the verdict being computed.
* ``declared_roles_match_traded_sides``, ``role_long_gross_pnl``, ``role_short_gross_pnl`` -- an
  inversion swaps the sides by construction, so a long-only candidate's inversion is short-only and
  the role gates would fail for a reason that says nothing about whether the edge is an artifact.
* the shape floors (turnover, gross edge per turnover, cost share, top-5-day share, fold PnL
  concentration, fold and quarter positivity) -- these are nearly sign-symmetric, so including them
  would let a candidate pass the falsifier because its *inversion* had the same turnover, which is
  not evidence of anything.

The set is not sensitive in practice, and that is the point: an exactly inverted book has the
negative of the original's gross return, so ``annualized_return > 0`` alone fails almost every
inversion. A candidate whose inversion clears these eight is one whose apparent edge comes from
cost, funding or cap asymmetry rather than from direction.
"""

UNMEASURED_AT_A_SINGLE_POINT: tuple[str, ...] = (
    "neighbourhood_positive_fraction",
    "sign_inversion_not_profitable",
)
"""Gates a single-point evaluation cannot decide, and therefore never reports as passed.

They are supplied to ``evaluate_floors`` at values that pass -- otherwise every packet would carry
two failures that mean nothing -- and then subtracted again in :attr:`CoachingPacket.verdict`,
which is why this command can print ``FAILS`` but never prints ``QUALIFIED``.
"""

# gate name -> (scored metric key, comparison, [floors] key or None for a bare > 0 floor)
_FLOOR_DETAIL: dict[str, tuple[str, str, str | None]] = {
    "net_sharpe": ("net_sharpe", ">=", "net_sharpe"),
    "double_cost_sharpe": ("double_cost_sharpe", ">=", "double_cost_sharpe"),
    "triple_cost_sharpe": ("triple_cost_sharpe", ">", None),
    "annualized_return": ("annualized_return", ">", None),
    "double_cost_annualized_return": ("double_cost_annualized_return", ">", None),
    "max_drawdown": ("max_drawdown", "<=", "max_drawdown"),
    "annualized_volatility": ("annualized_volatility", ">=", "minimum_realized_volatility"),
    "positive_quarter_fraction": (
        "positive_quarter_fraction",
        ">=",
        "positive_quarter_fraction",
    ),
    "positive_fold_count": ("positive_fold_count", ">=", "minimum_positive_folds"),
    "worst_fold_sharpe": ("worst_fold_sharpe", ">=", "worst_fold_sharpe"),
    "annualized_turnover": ("annualized_turnover", "<=", "max_annualized_turnover"),
    "gross_edge_bps_per_turnover": (
        "gross_edge_bps_per_turnover",
        ">=",
        "min_gross_edge_bps_per_turnover",
    ),
    "cost_share_of_positive_gross": (
        "cost_share_of_positive_gross",
        "<=",
        "max_cost_share_of_positive_gross",
    ),
    "top5_day_share": ("top5_day_share", "<=", "max_top5_day_share"),
    "max_fold_positive_pnl_share": (
        "max_fold_positive_pnl_share",
        "<=",
        "max_fold_share_of_positive_pnl",
    ),
    "trade_count": ("trade_count", ">=", "minimum_trades"),
    "role_long_gross_pnl": ("long_gross_pnl", ">", None),
    "role_short_gross_pnl": ("short_gross_pnl", ">", None),
}

# Gates whose observed value is not a member of the scored vector.
_SCALAR_GATES: tuple[str, ...] = (
    "neighbourhood_positive_fraction",
    "trial_adjusted_confidence",
    "sign_inversion_not_profitable",
    "declared_roles_match_traded_sides",
)


class CandidateLoadError(RuntimeError):
    """The team's entrypoint could not be turned into a usable strategy."""


def load_team_strategy(candidate_root: str | Path) -> TargetStrategy:
    """Import ``strategy.py`` and call its ``build_strategy()``.

    Team code IS executed here, unavoidably -- it is the thing being evaluated. What that requires
    of the caller is that the blindness scan has already run (see :func:`evaluate_point`, which
    orders them), because a scan that ran after an import would be reporting on a tree the imported
    code had already had a chance to change.

    The module is registered under a name derived from its own path so that two candidates in one
    process cannot share module state, and it is popped from ``sys.modules`` first so a second
    evaluation in the same process re-executes the file rather than reusing a stale import.

    The entrypoint's **current bytes** are compiled directly rather than going through
    ``SourceFileLoader.exec_module``, which consults ``__pycache__``. Bytecode invalidation is
    keyed on (mtime to the second, source size), and an edit that changes neither -- ``VALUE = 1``
    to ``VALUE = 2`` inside the same second is the whole of it -- silently re-runs the PREVIOUS
    code. That is not theoretical: it is what this loader did before, and it is the one failure
    that cannot be detected downstream, because the source digest would correctly report the new
    bytes while the evaluator ran the old ones.
    """
    root = Path(candidate_root)
    entry = root / ENTRYPOINT
    if not entry.is_file():
        raise CandidateLoadError(f"{entry} does not exist")
    module_name = f"_cup20_candidate_{abs(hash(str(entry.resolve()))):x}"
    sys.modules.pop(module_name, None)
    spec = importlib.util.spec_from_file_location(module_name, entry)
    if spec is None:
        raise CandidateLoadError(f"cannot import {entry}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        code = compile(entry.read_text(), str(entry), "exec")
        exec(code, module.__dict__)
    except BaseException as error:
        sys.modules.pop(module_name, None)
        raise CandidateLoadError(f"{entry} raised on import: {error!r}") from error
    factory = getattr(module, "build_strategy", None)
    if not callable(factory):
        raise CandidateLoadError(f"{entry} defines no callable build_strategy()")
    strategy = factory()
    if not callable(getattr(strategy, "target_weights", None)):
        raise CandidateLoadError(
            f"{entry}: build_strategy() returned {strategy!r}, which has no target_weights()"
        )
    return strategy


def load_candidate_risk_policy(candidate_root: str | Path) -> RiskPolicy:
    """Parse the declared risk policy. Required; see ``trials.risk_policy_digest``."""
    path = Path(candidate_root) / RISK_POLICY_FILENAME
    if not path.is_file():
        raise CandidateLoadError(
            f"{path} does not exist; every candidate declares a risk policy (charter section 11)"
        )
    return load_risk_policy(path)


def run_full_window(
    strategy: TargetStrategy,
    snapshot: Snapshot,
    raw: Mapping[str, Any],
    *,
    is_start: pd.Timestamp,
    seed: int,
    risk_policy: RiskPolicy | None,
    cost_multipliers: Sequence[int] | None = None,
) -> CandidateRun:
    """One two-pass evaluation over the whole in-sample window, at the frozen config.

    ``cost_multipliers`` defaults to the frozen ``[execution]`` list and is overridden only by the
    placebo, which is scored on gross edge and therefore needs exactly one cost level -- gross PnL
    per unit turnover does not read the cost multiplier at all, so running three would be three
    times the wall clock for one number.
    """
    config = evaluator_config(raw["execution"])
    grid = decision_grid(is_start, IS_END, interval_hours=config.interval_hours)
    levels = (
        tuple(int(value) for value in raw["execution"]["cost_multipliers"])
        if cost_multipliers is None
        else tuple(int(value) for value in cost_multipliers)
    )
    return run_candidate(
        strategy,
        snapshot,
        decision_times=grid,
        seed=seed,
        config=config,
        risk_unit=raw["risk_unit"],
        cost_multipliers=levels,
        risk_policy=risk_policy,
    )


def _json_safe(value: Any) -> Any:
    """Replace every non-finite float with ``None``, recursively.

    ``json.dumps(..., allow_nan=False)`` is the right setting for an artifact anyone else reads:
    ``NaN`` and ``Infinity`` are not JSON and a strict parser rejects them. But a coaching packet
    legitimately CARRIES non-finite values -- a book that barely traded has a NaN Sharpe, and a
    failed bootstrap has a NaN positive fraction -- and refusing to write the file would take the
    diagnosis away from exactly the team that needs it. ``null`` is JSON's way of saying "there is
    no number here", which is what a non-finite metric means. The rendered text still shows ``nan``,
    so nothing is hidden from a human reader either.
    """
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Mapping):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


@dataclasses.dataclass(frozen=True, slots=True)
class GateDetail:
    """One floor, what it required, and what this candidate actually did."""

    name: str
    passed: bool
    observed: float | None
    comparison: str
    floor: float | None
    measured: bool
    note: str = ""

    def render(self) -> str:
        mark = "PASS" if self.passed else "FAIL"
        if not self.measured:
            mark = "----"
        if self.observed is None:
            body = self.note or "boolean gate"
        else:
            floor = "0" if self.floor is None else f"{self.floor:g}"
            body = f"{self.observed:>14.6f}  required {self.comparison} {floor}"
            if self.note:
                body = f"{body}  ({self.note})"
        return f"  {mark}  {self.name:<38} {body}"


def gate_details(
    gates: Mapping[str, bool],
    scored: Mapping[str, float],
    *,
    floors: Mapping[str, Any],
    statistics_config: Mapping[str, Any],
    research_config: Mapping[str, Any],
    declared_roles: Sequence[str],
    observed_roles: Sequence[str],
    neighbourhood_positive_fraction: float,
    confidence: float,
    unmeasured: Sequence[str],
) -> tuple[GateDetail, ...]:
    """Attach the required value and the achieved value to every gate the floors returned.

    Every gate name in ``gates`` must be covered, and an unknown one raises rather than being
    silently rendered as a bare boolean: this table necessarily restates section 7.3's thresholds,
    and the way that restatement goes wrong is by falling behind a new floor rather than by
    contradicting an existing one. A test asserts this module covers exactly the gate set
    ``evaluate_floors`` produces, so the drift is caught at the moment the floor is added.
    """
    unmeasured_names = set(unmeasured)
    details: list[GateDetail] = []
    for name, passed in gates.items():
        measured = name not in unmeasured_names
        if name in _FLOOR_DETAIL:
            key, comparison, floor_key = _FLOOR_DETAIL[name]
            details.append(
                GateDetail(
                    name=name,
                    passed=bool(passed),
                    observed=float(scored[key]),
                    comparison=comparison,
                    floor=None if floor_key is None else float(floors[floor_key]),
                    measured=measured,
                )
            )
            continue
        if name == "neighbourhood_positive_fraction":
            details.append(
                GateDetail(
                    name=name,
                    passed=bool(passed),
                    observed=float(neighbourhood_positive_fraction),
                    comparison=">=",
                    floor=float(research_config["neighbourhood_positive_fraction"]),
                    measured=measured,
                    note="assumed; a single point cannot measure a neighbourhood",
                )
            )
            continue
        if name == "trial_adjusted_confidence":
            details.append(
                GateDetail(
                    name=name,
                    passed=bool(passed),
                    observed=float(confidence),
                    comparison=">=",
                    floor=float(statistics_config["minimum_trial_adjusted_confidence"]),
                    measured=measured,
                )
            )
            continue
        if name == "sign_inversion_not_profitable":
            # When this gate is unmeasured the note must say so rather than reporting the value it
            # was ASSUMED at. "the inversion did not clear the core floors" is the assumption, and
            # printing it as a finding is exactly the fail-open the unmeasured marking exists to
            # prevent -- a team would read it as evidence its falsifier had already been satisfied.
            if not measured:
                note = "not measured here; run --falsification, which is its own material trial"
            elif passed:
                note = "the exact sign inversion did NOT clear the core floors"
            else:
                note = "the exact sign inversion CLEARED the core floors -- disqualifying"
            details.append(
                GateDetail(
                    name=name,
                    passed=bool(passed),
                    observed=None,
                    comparison="",
                    floor=None,
                    measured=measured,
                    note=note,
                )
            )
            continue
        if name == "declared_roles_match_traded_sides":
            details.append(
                GateDetail(
                    name=name,
                    passed=bool(passed),
                    observed=None,
                    comparison="",
                    floor=None,
                    measured=measured,
                    note=(
                        f"declared {sorted(set(declared_roles))}, "
                        f"traded {sorted(set(observed_roles))}"
                    ),
                )
            )
            continue
        raise ValueError(
            f"gate {name!r} has no detail entry in crypto_trade.cup20.harness; a floor was added "
            "to qualification.evaluate_floors without teaching the coaching packet what it means"
        )
    return tuple(details)


def _observed_sides(scored: Mapping[str, float]) -> tuple[str, ...]:
    """Which sides the book materially traded, by the same rule the floors use.

    Reported so ``declared_roles_match_traded_sides`` can say what it disagreed with rather than
    only that it disagreed.
    """
    return _material_sides({"long": scored["long_gross_pnl"], "short": scored["short_gross_pnl"]})


def _confidence(run: CandidateRun, raw: Mapping[str, Any], trial_count: int) -> tuple[float, float]:
    """The bootstrap positive fraction ``B`` and the trial-adjusted confidence, or a failing pair.

    Fails CLOSED. The bootstrap raises on a series that is too short or carries a non-finite
    observation, and both are real outcomes for a book that barely traded. Turning that into
    ``B = NaN`` and ``confidence = 0.0`` makes the floor fail -- which is the direction a hard floor
    must fail in -- instead of either crashing the packet or, far worse, letting ``NaN`` reach
    ``min(1.0, nan)``, which CPython evaluates to ``1.0``: the most favourable possible confidence
    out of the one term whose job is to penalise.
    """
    statistics_config = raw["statistics"]
    daily = daily_returns(run.results[BASE_COST])
    try:
        positive_fraction = circular_block_bootstrap_positive_fraction(
            daily,
            samples=int(statistics_config["bootstrap_samples"]),
            block_days=int(statistics_config["bootstrap_block_days"]),
            seed=int(statistics_config["bootstrap_seed"]),
        )
    except ValueError:
        return math.nan, 0.0
    return positive_fraction, trial_adjusted_confidence(positive_fraction, trial_count)


@dataclasses.dataclass(frozen=True, slots=True)
class CoachingPacket:
    """Everything a team is shown about one evaluation of one candidate."""

    team_id: str
    candidate_id: str
    trial_sequence: int
    accepted_trials: int
    trial_budget: int
    source_sha256: str
    snapshot_sha256: str
    window: tuple[pd.Timestamp, pd.Timestamp]
    folds: tuple[Fold, ...]
    seed: int
    declared_roles: tuple[str, ...]
    observed_roles: tuple[str, ...]
    cost_levels: dict[str, dict[str, float]]
    fold_sharpes: dict[str, float]
    scored: Mapping[str, float]
    gate_details: tuple[GateDetail, ...]
    unmeasured_gates: tuple[str, ...]
    exposure_caps: dict[str, dict[str, Any]]
    risk_scalars: dict[str, float]
    bootstrap_positive_fraction: float
    trial_adjusted_confidence: float
    ranking_score: float | None
    workspace: WorkspaceScan

    @property
    def measured_failures(self) -> tuple[str, ...]:
        return tuple(
            detail.name for detail in self.gate_details if detail.measured and not detail.passed
        )

    @property
    def verdict(self) -> str:
        """Never ``QUALIFIED``. A single point cannot decide the neighbourhood or the falsifier."""
        if self.measured_failures:
            return f"FAILS {len(self.measured_failures)} measured floor(s)"
        if self.unmeasured_gates:
            return (
                f"NO MEASURED FAILURE -- {len(self.unmeasured_gates)} gate(s) cannot be decided "
                "at a single point"
            )
        return "NO MEASURED FAILURE"

    def as_dict(self) -> dict[str, Any]:
        return _json_safe(
            {
                "team_id": self.team_id,
                "candidate_id": self.candidate_id,
                "trial_sequence": self.trial_sequence,
                "accepted_trials": self.accepted_trials,
                "trial_budget": self.trial_budget,
                "source_sha256": self.source_sha256,
                "snapshot_sha256": self.snapshot_sha256,
                "window": {"start": str(self.window[0]), "end": str(self.window[1])},
                "folds": [
                    {"name": name, "start": str(start), "end": str(end)}
                    for name, start, end in self.folds
                ],
                "seed": self.seed,
                "declared_roles": list(self.declared_roles),
                "observed_roles": list(self.observed_roles),
                "cost_levels": self.cost_levels,
                "fold_sharpes": self.fold_sharpes,
                "scored": {key: float(self.scored[key]) for key in sorted(self.scored)},
                "gates": {
                    detail.name: {
                        "passed": detail.passed,
                        "measured": detail.measured,
                        "observed": detail.observed,
                        "comparison": detail.comparison,
                        "floor": detail.floor,
                        "note": detail.note,
                    }
                    for detail in self.gate_details
                },
                "unmeasured_gates": list(self.unmeasured_gates),
                "exposure_caps": self.exposure_caps,
                "risk_scalars": self.risk_scalars,
                "bootstrap_positive_fraction": self.bootstrap_positive_fraction,
                "trial_adjusted_confidence": self.trial_adjusted_confidence,
                "ranking_score": self.ranking_score,
                "verdict": self.verdict,
                "measured_failures": list(self.measured_failures),
                "workspace": {
                    "root": self.workspace.root,
                    "files_scanned": self.workspace.files_scanned,
                    "violations": list(self.workspace.violations),
                    "unscanned": list(self.workspace.unscanned),
                },
            }
        )

    def render(self) -> str:
        rule = "-" * 78
        score = "n/a" if self.ranking_score is None else f"{self.ranking_score:.3f}"
        folds = [f"{name} [{start.date()}, {end.date()})" for name, start, end in self.folds]
        lines = [
            rule,
            f"CUP-20 coaching packet -- {self.team_id} / {self.candidate_id}",
            rule,
            f"  trial            #{self.trial_sequence}  "
            f"({self.accepted_trials} of {self.trial_budget} accepted trials spent)",
            f"  source           {self.source_sha256}",
            f"  snapshot         {self.snapshot_sha256}",
            f"  window           [{self.window[0]}, {self.window[1]})   seed {self.seed}",
            "  folds            " + ", ".join(folds),
            "",
            "metric vector, at every cost level",
            rule,
        ]
        keys = sorted({key for level in self.cost_levels.values() for key in level})
        header = "".join(f"{level:>16}" for level in sorted(self.cost_levels))
        lines.append(f"  {'metric':<36}{header}")
        for key in keys:
            row = "".join(
                f"{self.cost_levels[level][key]:>16.6f}" for level in sorted(self.cost_levels)
            )
            lines.append(f"  {key:<36}{row}")
        lines += [
            "",
            "fold Sharpes (2x cost, the level section 7.3 floors them at)",
            rule,
        ]
        for name, value in self.fold_sharpes.items():
            lines.append(f"  {name:<38}{value:>14.6f}")
        lines += [
            "",
            f"trial-adjusted confidence: B={self.bootstrap_positive_fraction:.4f}, "
            f"T={self.accepted_trials}, confidence={self.trial_adjusted_confidence:.4f}",
            "",
            "hard floors (charter 7.3). '----' is a gate a single point cannot decide.",
            rule,
        ]
        lines += [detail.render() for detail in self.gate_details]
        lines += [
            "",
            "exposure caps -- how far your book was reduced (charter 4)",
            rule,
        ]
        for stage in sorted(self.exposure_caps):
            summary = self.exposure_caps[stage]
            lines.append(
                f"  {stage:<12} {summary['trimmed_boundaries']}/{summary['boundaries']} boundaries "
                f"reduced, minimum scale {summary['minimum_scale']:.4f}, median "
                f"{summary['median_scale']:.4f}, binding {summary['binding_cap_counts']}"
            )
        lines += [
            "",
            f"  risk-unit scalar   median {self.risk_scalars['median']:.4f}  "
            f"min {self.risk_scalars['minimum']:.4f}  max {self.risk_scalars['maximum']:.4f}",
            "",
            rule,
            f"  verdict: {self.verdict}",
            f"  indicative ranking score G: {score}",
            "",
            "  This is your NOMINATED POINT's own vector. It is not your score. Section 7.2",
            "  scores the per-metric MEDIAN across your declared neighbourhood, which is always",
            "  below the maximum of a noisy surface and is what the organiser will rank you on.",
            rule,
        ]
        if self.workspace.unscanned:
            lines += [
                "",
                f"  WARNING: {len(self.workspace.unscanned)} workspace file(s) were too large to "
                "read and were NOT scanned for blindness violations:",
                *(f"    {entry}" for entry in self.workspace.unscanned),
            ]
        return "\n".join(lines)


def build_coaching_packet(
    run: CandidateRun,
    scored: ScoredVector,
    adjudication: CandidateAdjudication,
    *,
    team_id: str,
    candidate_id: str,
    trial_sequence: int,
    accepted_trials: int,
    raw: Mapping[str, Any],
    source_sha256: str,
    snapshot_sha256: str,
    is_start: pd.Timestamp,
    folds: Sequence[Fold],
    seed: int,
    declared_roles: Sequence[str],
    neighbourhood_positive_fraction: float,
    bootstrap_positive_fraction: float,
    confidence: float,
    unmeasured: Sequence[str],
    workspace: WorkspaceScan,
) -> CoachingPacket:
    """Assemble everything a team is shown, from artifacts the pipeline already produced."""
    observed = _observed_sides(scored)
    details = gate_details(
        adjudication.gates.checks,
        scored,
        floors=raw["floors"],
        statistics_config=raw["statistics"],
        research_config=raw["research"],
        declared_roles=declared_roles,
        observed_roles=observed,
        neighbourhood_positive_fraction=neighbourhood_positive_fraction,
        confidence=confidence,
        unmeasured=unmeasured,
    )
    scalars = run.risk_scalars
    return CoachingPacket(
        team_id=team_id,
        candidate_id=candidate_id,
        trial_sequence=trial_sequence,
        accepted_trials=accepted_trials,
        trial_budget=int(raw["research"]["trial_budget"]),
        source_sha256=source_sha256,
        snapshot_sha256=snapshot_sha256,
        window=(is_start, IS_END),
        folds=tuple(folds),
        seed=seed,
        declared_roles=tuple(declared_roles),
        observed_roles=tuple(observed),
        cost_levels={
            f"{multiplier}x": window_metrics(result).as_dict()
            for multiplier, result in sorted(run.results.items())
        },
        fold_sharpes=dict(fold_sharpes(run.results[DOUBLE_COST], folds)),
        scored=scored,
        gate_details=details,
        unmeasured_gates=tuple(unmeasured),
        exposure_caps={
            "requested": run.requested_trim.summary(),
            "executed": run.executed_trim.summary(),
        },
        risk_scalars={
            "count": float(scalars.size),
            "median": float(scalars.median()) if scalars.size else 0.0,
            "minimum": float(scalars.min()) if scalars.size else 0.0,
            "maximum": float(scalars.max()) if scalars.size else 0.0,
        },
        bootstrap_positive_fraction=bootstrap_positive_fraction,
        trial_adjusted_confidence=confidence,
        ranking_score=adjudication.score,
        workspace=workspace,
    )


class BlindnessViolationError(RuntimeError):
    """The team's workspace refers to something it is not allowed to refer to."""


def scan_workspace_or_refuse(workspace_root: str | Path, *, team_id: str) -> WorkspaceScan:
    """Run the blindness scan and refuse to go further on a violation.

    Run BEFORE the candidate is imported and before a single row is read. Catching a prohibited
    reference now costs a team an edit; catching it at nomination costs it the tournament, and
    catching it after the holdout costs everyone the result.

    Only ``violations`` refuse. ``unscanned`` -- a file too large to read -- is surfaced in the
    packet as a warning instead, because an unreadable file is an organiser decision at nomination
    and not something this tool should silently grant or silently deny.
    """
    scan = scan_workspace_for_blindness_violations(workspace_root, team_id=team_id)
    if scan.violations:
        listed = "\n".join(f"    {violation}" for violation in scan.violations[:40])
        more = (
            f"\n    ... and {len(scan.violations) - 40} more" if len(scan.violations) > 40 else ""
        )
        raise BlindnessViolationError(
            f"the blindness scan found {len(scan.violations)} violation(s) under "
            f"{scan.root}:\n{listed}{more}\n"
            "Nothing was evaluated. Each entry is file:line:pattern -- a prohibited path, a "
            "post-cutoff date literal, another team's directory, or a symlink."
        )
    return scan


def evaluate_point(
    *,
    snapshot: Snapshot,
    raw: Mapping[str, Any],
    candidate_root: str | Path,
    workspace_root: str | Path,
    team_id: str,
    candidate_id: str,
    seed: int,
    declared_roles: Sequence[str],
    trial_sequence: int,
    accepted_trials: int,
    source_sha256: str,
    is_start: pd.Timestamp,
) -> CoachingPacket:
    """Scan, load, run the full window, score, adjudicate, and coach. In that order.

    ``sign_inversion_passes_core`` is fixed at ``False`` here and the gate is reported as
    unmeasured, rather than being a parameter a caller could set. The inversion is a whole second
    evaluation with its own accepted trial (:func:`run_falsification_battery`), so there is no
    state in which this function legitimately knows the answer -- and a parameter that could only
    ever be passed a guess is a way for a guess to reach a disqualifying gate.
    """
    workspace = scan_workspace_or_refuse(workspace_root, team_id=team_id)
    strategy = load_team_strategy(candidate_root)
    policy = load_candidate_risk_policy(candidate_root)
    run = run_full_window(strategy, snapshot, raw, is_start=is_start, seed=seed, risk_policy=policy)
    scored = assemble_scored_metrics(run, stage=STAGE_IN_SAMPLE, is_start=is_start, is_end=IS_END)
    bootstrap_fraction, confidence = _confidence(run, raw, accepted_trials)
    # Assumed at a value that passes, then subtracted again by ``unmeasured``. A single point has
    # no neighbourhood, and reporting a manufactured failure here would bury the real ones.
    assumed_neighbourhood_fraction = 1.0
    adjudication = adjudicate_candidate(
        scored,
        team_id=team_id,
        candidate_id=candidate_id,
        floors=raw["floors"],
        statistics_config=raw["statistics"],
        research_config=raw["research"],
        declared_roles=tuple(declared_roles),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=assumed_neighbourhood_fraction,
        trial_adjusted_confidence=confidence,
        drawdown_floor=float(raw["floors"]["max_drawdown"]),
    )
    return build_coaching_packet(
        run,
        scored,
        adjudication,
        team_id=team_id,
        candidate_id=candidate_id,
        trial_sequence=trial_sequence,
        accepted_trials=accepted_trials,
        raw=raw,
        source_sha256=source_sha256,
        snapshot_sha256=snapshot.manifest_sha256,
        is_start=is_start,
        folds=is_folds(is_start, IS_END),
        seed=seed,
        declared_roles=declared_roles,
        neighbourhood_positive_fraction=assumed_neighbourhood_fraction,
        bootstrap_positive_fraction=bootstrap_fraction,
        confidence=confidence,
        unmeasured=UNMEASURED_AT_A_SINGLE_POINT,
        workspace=workspace,
    )


# --- the falsification battery -------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class SignInverted:
    """The exact sign inversion: every emitted weight negated, and nothing else touched.

    ``None`` (hold) and ``{}`` (go flat) are instructions about *whether* to trade, not about
    direction, so they pass through unchanged -- inverting them would change the book's trading
    schedule and the result would no longer be an exact inversion of anything.

    Negation commutes with ``normalise_unit_gross``: that function divides by the row's absolute
    sum, which negation leaves unchanged, so inverting before normalisation and inverting after are
    the same book. The inversion is therefore exact rather than merely close.
    """

    inner: TargetStrategy

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        weights = self.inner.target_weights(context, seed=seed)
        if weights is None:
            return None
        return {symbol: -float(weight) for symbol, weight in weights.items()}


@dataclasses.dataclass(frozen=True, slots=True)
class PermutedAttribution:
    """The gross-edge placebo: the same weights, attached to randomly chosen eligible symbols.

    What it nulls is *selection*, which is the only thing a weights-only protocol can express an
    opinion about. The weight multiset is preserved exactly, so gross exposure, the sizing
    distribution and the rebalance schedule are all untouched; only which symbol receives which
    weight is randomised, over the eligible set at that boundary rather than over the names the
    candidate happened to pick -- otherwise the placebo would still be trading the candidate's
    selection, just shuffled within it.

    Scored on **gross** edge, never on net, exactly as charter section 7.3 requires: a costed
    random book centres at minus its cost rather than at zero, so a net-of-cost placebo null is
    structurally broken and would flatter every candidate.
    """

    inner: TargetStrategy
    permutation_seed: int

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        weights = self.inner.target_weights(context, seed=seed)
        if weights is None or not weights:
            return weights
        eligible = sorted(context.eligible_symbols)
        values = [float(weights[symbol]) for symbol in sorted(weights)]
        if len(values) > len(eligible):
            # The candidate targeted a symbol outside the eligible set; the evaluator will reject
            # that on its own terms. Passing the book through unchanged keeps the placebo from
            # masking it as a placebo artifact.
            return weights
        generator = np.random.default_rng([self.permutation_seed, int(context.decision_time.value)])
        chosen = generator.choice(len(eligible), size=len(values), replace=False)
        return {eligible[int(index)]: value for index, value in zip(chosen, values, strict=True)}


@dataclasses.dataclass(frozen=True, slots=True)
class FalsificationReport:
    """The battery's two verdicts, and the numbers behind them."""

    team_id: str
    candidate_id: str
    trial_sequence: int
    inverted_core_gates: Mapping[str, bool]
    inverted_metrics: Mapping[str, float]
    sign_inversion_passes_core: bool
    candidate_gross_edge_bps: float
    placebo_gross_edge_bps: tuple[float, ...]
    placebo_seeds: tuple[int, ...]

    @property
    def placebo_exceedance(self) -> float:
        """Fraction of placebo books whose gross edge reached the candidate's."""
        if not self.placebo_gross_edge_bps:
            return math.nan
        reached = sum(
            1 for value in self.placebo_gross_edge_bps if value >= self.candidate_gross_edge_bps
        )
        return reached / len(self.placebo_gross_edge_bps)

    def as_dict(self) -> dict[str, Any]:
        return _json_safe(
            {
                "team_id": self.team_id,
                "candidate_id": self.candidate_id,
                "trial_sequence": self.trial_sequence,
                "inverted_core_gates": dict(self.inverted_core_gates),
                "inverted_metrics": dict(self.inverted_metrics),
                "sign_inversion_passes_core": self.sign_inversion_passes_core,
                "candidate_gross_edge_bps_per_turnover": self.candidate_gross_edge_bps,
                "placebo_gross_edge_bps_per_turnover": list(self.placebo_gross_edge_bps),
                "placebo_seeds": list(self.placebo_seeds),
                "placebo_exceedance": self.placebo_exceedance,
            }
        )

    def render(self) -> str:
        rule = "-" * 78
        lines = [
            rule,
            f"CUP-20 falsification battery -- {self.team_id} / {self.candidate_id}"
            f"  (trial #{self.trial_sequence})",
            rule,
            "exact sign inversion, scored on the core floors (charter 7.3)",
            rule,
        ]
        for name in CORE_FLOOR_CHECKS:
            passed = self.inverted_core_gates[name]
            observed = self.inverted_metrics.get(name)
            shown = "" if observed is None else f"{observed:>14.6f}"
            lines.append(f"  {'CLEARS' if passed else 'fails ':<7} {name:<38}{shown}")
        lines += [
            "",
            (
                "  DISQUALIFYING: the exact inversion clears every core floor, so the apparent "
                "edge is a construction artifact rather than a mechanism."
                if self.sign_inversion_passes_core
                else "  The inversion does not clear the core floors. The falsifier is satisfied."
            ),
            "",
            "gross-edge placebo -- same weights, randomly attributed across eligible symbols",
            rule,
            f"  candidate gross edge      {self.candidate_gross_edge_bps:>14.4f} bps per unit "
            "one-way turnover",
        ]
        if self.placebo_gross_edge_bps:
            ordered = sorted(self.placebo_gross_edge_bps)
            lines += [
                f"  placebo books ({len(ordered)})          "
                f"min {ordered[0]:.4f}  median {float(np.median(ordered)):.4f}  "
                f"max {ordered[-1]:.4f}",
                f"  placebo exceedance        {self.placebo_exceedance:.4f}  "
                "(fraction of placebos reaching the candidate)",
            ]
        lines.append(rule)
        return "\n".join(lines)


def run_falsification_battery(
    *,
    snapshot: Snapshot,
    raw: Mapping[str, Any],
    candidate_root: str | Path,
    workspace_root: str | Path,
    team_id: str,
    candidate_id: str,
    seed: int,
    trial_sequence: int,
    is_start: pd.Timestamp,
    placebo_permutations: int = 8,
) -> FalsificationReport:
    """Both halves of section 7.1's battery, in one trial, run by the organiser's code.

    The inversion is scored at every frozen cost level, because the core floors it is checked
    against name 1x, 2x and 3x. Each placebo is scored at 1x only: gross edge per unit turnover
    reads no cost multiplier at all, so the other two levels would be wall clock spent on nothing.
    """
    if placebo_permutations < 0:
        raise ValueError(f"placebo_permutations must not be negative, got {placebo_permutations}")
    scan_workspace_or_refuse(workspace_root, team_id=team_id)
    policy = load_candidate_risk_policy(candidate_root)

    inverted_run = run_full_window(
        SignInverted(load_team_strategy(candidate_root)),
        snapshot,
        raw,
        is_start=is_start,
        seed=seed,
        risk_policy=policy,
    )
    inverted_scored = assemble_scored_metrics(
        inverted_run, stage=STAGE_IN_SAMPLE, is_start=is_start, is_end=IS_END
    )
    # Routed through the frozen ``evaluate_floors`` rather than recomparing the eight values here:
    # the comparison semantics (non-finite fails, ">= floor" not "> floor") are policy, and a second
    # implementation of them is a second place for them to drift. The three research inputs are
    # supplied at passing values and are not read back -- only CORE_FLOOR_CHECKS is.
    inverted_gates = evaluate_floors(
        inverted_scored,
        floors=raw["floors"],
        statistics_config=raw["statistics"],
        research_config=raw["research"],
        declared_roles=_observed_sides(inverted_scored),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=1.0,
        trial_adjusted_confidence=1.0,
    )
    core = {name: bool(inverted_gates.checks[name]) for name in CORE_FLOOR_CHECKS}

    candidate_run = run_full_window(
        load_team_strategy(candidate_root),
        snapshot,
        raw,
        is_start=is_start,
        seed=seed,
        risk_policy=policy,
        cost_multipliers=(BASE_COST,),
    )
    candidate_edge = float(
        window_metrics(candidate_run.results[BASE_COST]).gross_edge_bps_per_turnover
    )

    placebo_seeds = tuple(seed + 1 + index for index in range(placebo_permutations))
    placebo_edges: list[float] = []
    for permutation_seed in placebo_seeds:
        placebo_run = run_full_window(
            PermutedAttribution(load_team_strategy(candidate_root), permutation_seed),
            snapshot,
            raw,
            is_start=is_start,
            seed=seed,
            risk_policy=policy,
            cost_multipliers=(BASE_COST,),
        )
        placebo_edges.append(
            float(window_metrics(placebo_run.results[BASE_COST]).gross_edge_bps_per_turnover)
        )

    return FalsificationReport(
        team_id=team_id,
        candidate_id=candidate_id,
        trial_sequence=trial_sequence,
        inverted_core_gates=core,
        inverted_metrics={
            name: float(inverted_scored[_FLOOR_DETAIL[name][0]]) for name in CORE_FLOOR_CHECKS
        },
        sign_inversion_passes_core=all(core.values()),
        candidate_gross_edge_bps=candidate_edge,
        placebo_gross_edge_bps=tuple(placebo_edges),
        placebo_seeds=placebo_seeds,
    )


# --- the no-cost plumbing check ---------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateCheck:
    """What :func:`check_candidate` could establish without opening any market data."""

    team_id: str
    candidate_id: str
    source_sha256: str
    strategy_built: bool
    risk_policy_id: str
    neighbourhood_points: int | None
    coordinate_violations: tuple[str, ...]
    workspace: WorkspaceScan

    @property
    def ok(self) -> bool:
        return self.strategy_built and not self.coordinate_violations

    def render(self) -> str:
        rule = "-" * 78
        lines = [
            rule,
            f"CUP-20 candidate check -- {self.team_id} / {self.candidate_id}",
            rule,
            f"  source                 {self.source_sha256}",
            f"  workspace scan         {self.workspace.files_scanned} files, 0 violations",
            f"  build_strategy()       {'ok' if self.strategy_built else 'FAILED'}",
            f"  risk policy            {self.risk_policy_id}",
            "  neighbourhood          "
            + (
                "not declared yet"
                if self.neighbourhood_points is None
                else f"{self.neighbourhood_points} points including the nominee"
            ),
        ]
        if self.coordinate_violations:
            lines.append("  coordinate rule        VIOLATIONS:")
            lines += [f"    {entry}" for entry in self.coordinate_violations]
        elif self.neighbourhood_points is not None:
            lines.append("  coordinate rule        ok")
        lines += [
            "",
            "  No market data was opened and no metric was produced, so this consumed no trial.",
            rule,
        ]
        if self.workspace.unscanned:
            lines += [
                f"  WARNING: {len(self.workspace.unscanned)} file(s) too large to scan:",
                *(f"    {entry}" for entry in self.workspace.unscanned),
            ]
        return "\n".join(lines)


def check_candidate(
    *,
    candidate_root: str | Path,
    workspace_root: str | Path,
    team_id: str,
    candidate_id: str,
    source_sha256: str,
) -> CandidateCheck:
    """Everything that can be verified about a candidate without evaluating it.

    Exists so the twelve-trial budget is never spent on a typo. It reads the workspace, imports the
    entrypoint, builds the strategy, parses the risk policy and -- if a neighbourhood has been
    declared -- checks the coordinate rule against the frozen source. It opens no bars, no funding
    and no marks, produces no metric and journals nothing, so it is not an evaluation under section
    7.1 and costs no trial.
    """
    workspace = scan_workspace_or_refuse(workspace_root, team_id=team_id)
    load_team_strategy(candidate_root)
    policy = load_candidate_risk_policy(candidate_root)
    declaration_path = Path(candidate_root) / "neighbourhood.json"
    points: int | None = None
    violations: tuple[str, ...] = ()
    if declaration_path.is_file():
        declaration = load_declaration(declaration_path)
        points = len(declaration.all_points())
        violations = verify_neighbourhood_coordinates(candidate_root, declaration)
    return CandidateCheck(
        team_id=team_id,
        candidate_id=candidate_id,
        source_sha256=source_sha256,
        strategy_built=True,
        risk_policy_id=policy.policy_id,
        neighbourhood_points=points,
        coordinate_violations=violations,
        workspace=workspace,
    )
