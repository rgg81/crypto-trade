"""Run the declared neighbourhood, and produce the number that is actually the team's score.

Section 7.2: **every scored metric is the per-metric median across the neighbourhood's runs.** A
nominated point is the maximum of a noisy surface and is upward-biased by construction; a median
over a plateau declared before evaluation is not. Until this module existed the tournament had no
way to compute that median, so the one number a team is ranked on was the one number nothing could
produce -- and a team that evaluated its seven points as seven ordinary candidates would have spent
seven of its twelve trials to arrive at it, which puts nomination (eight accepted trials, plus the
falsification battery, plus the research matrix section 7 requires) out of reach. Section 7.1
prices the sweep as **one trial however many points it contains**; this is the runner that makes
that price real.

**How a point is made, and why it is sound.** See :mod:`crypto_trade.cup20.variants`. The rejected
alternative -- import the module, then assign its constants -- is unsound for any strategy that
reads a constant at import time, which is most of them. Textual substitution of the module-level
literals produces a real file whose bytes are provably the nominee's outside the declared
coordinates.

**Why a subprocess per point.** Each point is evaluated in its own freshly spawned interpreter
(``max_tasks_per_child=1``), never in the parent and never in a reused worker. Three reasons, and
the first is the one that decides it:

* **Team code runs here, and process state is not scoped to a module.** A candidate that seeds
  ``random``, caches on another package's module global, sets an environment variable, changes a
  pandas option or installs a warnings filter would leave that behind for the next point evaluated
  in the same interpreter. The points would then not be independent evaluations, and -- worse --
  the nominee's own vector inside the sweep would stop being comparable with the same candidate's
  vector out of ``scripts/cup20_evaluate.py``, which is the one cross-check that proves the sweep
  runs the organiser's pipeline.
* **A point that dies takes only its own worker down.** A segfault or an ``os._exit`` in one point
  is reported as that point failing, rather than losing a whole trial's work.
* **It permits parallelism without weakening anything.** Points share no state by construction, so
  running several at once cannot change any of them. A test asserts the sweep's metric vectors are
  identical at two workers and at three, because "faster" is only worth having if it is the same
  answer. Measured on the real snapshot: 1222.8 s for seven points at four workers against 489.7 s
  for one point alone -- 2.8x, not 4x, because the work is memory-bandwidth bound as well as
  CPU-bound.

Nothing else is shared between points, deliberately: each worker loads the snapshot itself and
re-reads the frozen config, so no object crosses a point boundary. Snapshot load is 0.4 s against
an evaluation of roughly eight minutes, which is not a saving worth buying an argument with.
"""

from __future__ import annotations

import concurrent.futures
import dataclasses
import hashlib
import json
import math
import multiprocessing
import os
import statistics
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.cup20.adjudication import adjudicate_candidate
from crypto_trade.cup20.archive import WorkspaceScan
from crypto_trade.cup20.bootstrap import trial_adjusted_confidence
from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.harness import (
    GateDetail,
    _json_safe,
    _observed_sides,
    bootstrap_positive_fraction,
    gate_details,
    load_candidate_risk_policy,
    load_team_module,
    run_full_window,
    scan_workspace_or_refuse,
    strategy_from_module,
)
from crypto_trade.cup20.metrics import Fold, fold_sharpes, is_folds, window_metrics
from crypto_trade.cup20.neighbourhood import (
    NeighbourhoodDeclaration,
    load_declaration,
    positive_point_fraction,
)
from crypto_trade.cup20.scored_metrics import (
    DOUBLE_COST,
    STAGE_IN_SAMPLE,
    ScoredVector,
    assemble_scored_metrics,
    neighbourhood_median,
)
from crypto_trade.cup20.snapshot import load_snapshot
from crypto_trade.cup20.trials import ENTRYPOINT
from crypto_trade.cup20.variants import (
    MaterialisedPoint,
    VariantIntegrityError,
    materialise_point,
    point_label,
    verify_declaration_or_refuse,
)

NEIGHBOURHOOD_FILENAME = "neighbourhood.json"

UNMEASURED_BY_A_SWEEP: tuple[str, ...] = ("sign_inversion_not_profitable",)
"""The one gate a neighbourhood sweep still cannot decide.

``neighbourhood_positive_fraction`` -- unmeasurable at a single point, and reported as ``----`` by
``scripts/cup20_evaluate.py`` -- IS measured here; measuring it is half the reason the sweep
exists. The sign inversion is a separate evaluation with its own accepted trial
(``--falsification``), so this command has no honest way to know it and does not guess: it is
supplied at a value that passes and then subtracted again from the verdict, which is why a sweep
can print ``FAILS`` and still never print ``QUALIFIED``.
"""

_COORDINATE_TOLERANCE = 1e-9
"""Relative tolerance when checking an imported module bound the substituted value.

The declared value round-trips through JSON as a float and the module binds whatever the literal
parsed to, so an exact ``==`` would reject ``0.1`` for being ``0.1``. Matches the tolerance
``verify_neighbourhood_coordinates`` compares the nominee against the frozen source with, so the
static check and the runtime check cannot disagree about what "equal" means.
"""


class SweepError(RuntimeError):
    """The sweep cannot run, or one of its points did not complete."""


@dataclasses.dataclass(frozen=True, slots=True)
class PointJob:
    """Everything one worker needs, as plain values that survive a trip to a fresh process."""

    label: str
    is_nominee: bool
    coordinates: dict[str, float]
    root: str
    entrypoint_sha256: str
    snapshot_root: str
    config_path: str
    seed: int
    is_start: str


@dataclasses.dataclass(frozen=True, slots=True)
class PointOutcome:
    """One evaluated neighbourhood point."""

    label: str
    is_nominee: bool
    coordinates: dict[str, float]
    entrypoint_sha256: str
    bound_constants: dict[str, float]
    scored: ScoredVector
    bootstrap_positive_fraction: float
    cost_levels: dict[str, dict[str, float]]
    fold_sharpes: dict[str, float]
    exposure_caps: dict[str, dict[str, Any]]
    risk_scalars: dict[str, float]
    observed_roles: tuple[str, ...]
    seconds: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "is_nominee": self.is_nominee,
            "coordinates": dict(sorted(self.coordinates.items())),
            "entrypoint_sha256": self.entrypoint_sha256,
            "bound_constants": dict(sorted(self.bound_constants.items())),
            "scored": {key: float(self.scored[key]) for key in sorted(self.scored)},
            "bootstrap_positive_fraction": self.bootstrap_positive_fraction,
            "cost_levels": self.cost_levels,
            "fold_sharpes": self.fold_sharpes,
            "exposure_caps": self.exposure_caps,
            "risk_scalars": self.risk_scalars,
            "observed_roles": list(self.observed_roles),
            "seconds": self.seconds,
        }


def _bound_coordinate_values(module: object, coordinates: Mapping[str, float]) -> dict[str, float]:
    """Read the coordinates back out of the IMPORTED module, and refuse if they are not the point's.

    This is the check that a sweep which silently ran the same point seven times cannot survive,
    and it is the only one that can be made: everything else in this pipeline reads files, and a
    file that says ``FORMATION_BARS = 24`` proves nothing about what the interpreter bound if the
    wrong file was imported, a stale ``__pycache__`` was executed, the copy did not land, or the
    module rebound the name during import.

    A coordinate that is not bound at all after import is refused rather than skipped. The
    coordinate rule permits a module-level ``if``, so a name assigned only in a branch that did not
    run is reachable -- but such a name is not a parameter the frozen code is governed by, and
    treating it as one would let a team declare a plateau across a constant nothing reads.
    """
    bound: dict[str, float] = {}
    for name, expected in coordinates.items():
        if not hasattr(module, name):
            raise SweepError(
                f"{name} is not bound after importing {ENTRYPOINT}. A neighbourhood coordinate "
                "must be a module-level constant the frozen code actually binds (playbook 6.1)."
            )
        value = getattr(module, name)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise SweepError(f"{name} imported as {value!r}, which is not a number")
        if not math.isclose(
            float(value), float(expected), rel_tol=_COORDINATE_TOLERANCE, abs_tol=1e-12
        ):
            raise SweepError(
                f"the materialised point declares {name}={float(expected)!r} but the imported "
                f"module bound {name}={float(value)!r}. The point that ran is not the point that "
                "was declared, so nothing it produced is evidence about anything."
            )
        bound[name] = float(value)
    return bound


def evaluate_materialised_point(job: PointJob) -> PointOutcome:
    """Evaluate one materialised point, in its own interpreter, through the organiser's pipeline.

    Identical to what ``scripts/cup20_evaluate.py`` does to a single candidate -- the same
    ``run_full_window`` over the full in-sample window at the frozen ``[execution]`` and
    ``[risk_unit]`` tables, the same ``assemble_scored_metrics(stage="in_sample")`` -- with two
    checks in front of it that only a variant needs:

    1. the file on disk still hashes to what the parent materialised, so the worker is provably
       running the bytes the parent proved were the nominee's-plus-coordinates;
    2. the imported module bound this point's coordinate values (:func:`_bound_coordinate_values`).
    """
    root = Path(job.root)
    entry = root / ENTRYPOINT
    digest = hashlib.sha256(entry.read_bytes()).hexdigest()
    if digest != job.entrypoint_sha256:
        raise SweepError(
            f"{job.label}: {entry} hashes to {digest}, not the {job.entrypoint_sha256} the sweep "
            "materialised; the file changed between materialisation and execution"
        )

    started = time.monotonic()
    raw = load_config(job.config_path).raw
    snapshot = load_snapshot(job.snapshot_root)
    is_start = pd.Timestamp(job.is_start)

    module = load_team_module(root)
    bound = _bound_coordinate_values(module, job.coordinates)
    strategy = strategy_from_module(module, entry=entry)
    policy = load_candidate_risk_policy(root)

    run = run_full_window(
        strategy, snapshot, raw, is_start=is_start, seed=job.seed, risk_policy=policy
    )
    scored = assemble_scored_metrics(run, stage=STAGE_IN_SAMPLE, is_start=is_start, is_end=IS_END)
    scalars = run.risk_scalars
    return PointOutcome(
        label=job.label,
        is_nominee=job.is_nominee,
        coordinates=dict(job.coordinates),
        entrypoint_sha256=job.entrypoint_sha256,
        bound_constants=bound,
        scored=scored,
        bootstrap_positive_fraction=bootstrap_positive_fraction(run, raw),
        cost_levels={
            f"{multiplier}x": window_metrics(result).as_dict()
            for multiplier, result in sorted(run.results.items())
        },
        fold_sharpes=dict(fold_sharpes(run.results[DOUBLE_COST], is_folds(is_start, IS_END))),
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
        observed_roles=_observed_sides(scored),
        seconds=time.monotonic() - started,
    )


def median_bootstrap_fraction(outcomes: Sequence[PointOutcome]) -> float:
    """``B`` for the neighbourhood: the per-point median, ``NaN`` if any point had none.

    Section 7.2 makes every scored metric the per-metric median across the neighbourhood's runs,
    and ``B`` is a property of a run's own return stream exactly like the metrics beside it, so it
    takes the same median. The fail-closed rule is
    :func:`~crypto_trade.cup20.scored_metrics.neighbourhood_median`'s, for its reason:
    ``statistics.median`` sorts, ``NaN`` has no ordering, so one unusable point can land anywhere in
    the sorted run and hand back a finite, plausible median with a non-number behind it.
    """
    if not outcomes:
        raise ValueError("median_bootstrap_fraction requires at least one point")
    values = [float(outcome.bootstrap_positive_fraction) for outcome in outcomes]
    if not all(math.isfinite(value) for value in values):
        return math.nan
    return float(statistics.median(values))


@dataclasses.dataclass(frozen=True, slots=True)
class NeighbourhoodPacket:
    """The team's actual score, the diagnostics beside it, and what it still may not be."""

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
    workers: int
    declared_roles: tuple[str, ...]
    coordinates: tuple[str, ...]
    outcomes: tuple[PointOutcome, ...]
    median: Mapping[str, float]
    positive_point_fraction: float
    positive_point_fraction_floor: float
    bootstrap_positive_fraction: float
    trial_adjusted_confidence: float
    gate_details: tuple[GateDetail, ...]
    unmeasured_gates: tuple[str, ...]
    ranking_score: float | None
    elapsed_seconds: float
    workspace: WorkspaceScan

    @property
    def nominee(self) -> PointOutcome:
        return self.outcomes[0]

    @property
    def measured_failures(self) -> tuple[str, ...]:
        return tuple(
            detail.name for detail in self.gate_details if detail.measured and not detail.passed
        )

    @property
    def verdict(self) -> str:
        """Never ``QUALIFIED``: the sign-inversion falsifier is a separate trial."""
        if self.measured_failures:
            return f"FAILS {len(self.measured_failures)} measured floor(s)"
        return (
            f"NO MEASURED FAILURE -- {len(self.unmeasured_gates)} gate(s) cannot be decided by a "
            "neighbourhood sweep"
        )

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
                "workers": self.workers,
                "declared_roles": list(self.declared_roles),
                "coordinates": list(self.coordinates),
                "points": [outcome.as_dict() for outcome in self.outcomes],
                "score_is_the_neighbourhood_median": True,
                "median": {key: float(self.median[key]) for key in sorted(self.median)},
                "nominee_diagnostic_only": {
                    key: float(self.nominee.scored[key]) for key in sorted(self.nominee.scored)
                },
                "positive_point_fraction": self.positive_point_fraction,
                "positive_point_fraction_floor": self.positive_point_fraction_floor,
                "bootstrap_positive_fraction": self.bootstrap_positive_fraction,
                "trial_adjusted_confidence": self.trial_adjusted_confidence,
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
                "ranking_score": self.ranking_score,
                "verdict": self.verdict,
                "measured_failures": list(self.measured_failures),
                "elapsed_seconds": self.elapsed_seconds,
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
            f"CUP-20 neighbourhood sweep -- {self.team_id} / {self.candidate_id}",
            rule,
            f"  trial            #{self.trial_sequence}  "
            f"({self.accepted_trials} of {self.trial_budget} accepted trials spent)",
            f"  source           {self.source_sha256}",
            f"  snapshot         {self.snapshot_sha256}",
            f"  window           [{self.window[0]}, {self.window[1]})   seed {self.seed}",
            "  folds            " + ", ".join(folds),
            f"  coordinates      {', '.join(self.coordinates)}",
            f"  points           {len(self.outcomes)} including the nominee, "
            f"{self.workers} worker(s), {self.elapsed_seconds:.1f}s wall clock",
            "",
            "the points, each a separately materialised and separately executed file",
            rule,
            f"  {'point':<34}{'net_sharpe':>12}{'2x_sharpe':>12}{'ann_return':>12}"
            f"{'max_dd':>10}{'trades':>9}",
        ]
        for outcome in self.outcomes:
            scored = outcome.scored
            lines.append(
                f"  {outcome.label:<34}{scored['net_sharpe']:>12.4f}"
                f"{scored['double_cost_sharpe']:>12.4f}{scored['annualized_return']:>12.4f}"
                f"{scored['max_drawdown']:>10.4f}{scored['trade_count']:>9.0f}"
            )
        for outcome in self.outcomes:
            lines.append(f"    {outcome.label}  ->  strategy.py {outcome.entrypoint_sha256}")
        lines += [
            "",
            "YOUR SCORE -- the per-metric MEDIAN across the declared neighbourhood (section 7.2)",
            rule,
        ]
        for key in sorted(self.median):
            lines.append(f"  {key:<40}{self.median[key]:>16.6f}")
        lines += [
            "",
            f"  positive_point_fraction   {self.positive_point_fraction:.4f}  required >= "
            f"{self.positive_point_fraction_floor:g}  "
            f"({round(self.positive_point_fraction * len(self.outcomes))} of "
            f"{len(self.outcomes)} points have positive 1x return AND positive 2x Sharpe)",
            f"  trial-adjusted confidence B={self.bootstrap_positive_fraction:.4f} (median across "
            f"points), T={self.accepted_trials}, confidence="
            f"{self.trial_adjusted_confidence:.4f}",
            "",
            "hard floors (charter 7.3), on the MEDIAN. '----' is a gate a sweep cannot decide.",
            rule,
        ]
        lines += [detail.render() for detail in self.gate_details]
        lines += [
            "",
            rule,
            f"  verdict: {self.verdict}",
            f"  indicative ranking score G: {score}",
            rule,
            "",
            "DIAGNOSTIC ONLY -- your NOMINATED POINT's own vector. This is NOT your score.",
            rule,
        ]
        for key in sorted(self.nominee.scored):
            median = float(self.median[key])
            own = float(self.nominee.scored[key])
            lines.append(f"  {key:<40}{own:>16.6f}   (median {median:>14.6f})")
        lines += [
            "",
            "  Section 7.2 scores the median, not this. Where the two disagree, the median is the",
            "  number you are ranked on -- a nominated point is the max of a noisy surface.",
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


def load_neighbourhood(candidate_root: str | Path) -> NeighbourhoodDeclaration:
    """Read and fully validate the declared neighbourhood, or refuse.

    ``load_declaration`` runs ``validate()``: point count against ``max(7, 2k+1)``, distinctness on
    the full coordinate vector including against the nominee, material variation above and below
    every coordinate, and finite values. :func:`verify_declaration_or_refuse` adds the half that
    needs the frozen source.
    """
    path = Path(candidate_root) / NEIGHBOURHOOD_FILENAME
    if not path.is_file():
        raise VariantIntegrityError(
            f"{path} does not exist; a neighbourhood sweep needs a declared neighbourhood "
            "(playbook section 6)"
        )
    try:
        declaration = load_declaration(path)
    # Re-raised as this module's own type rather than letting ValueError/KeyError travel: the
    # callers must be able to refuse a team's malformed declaration WITHOUT catching bare
    # ValueError, which would also swallow an organiser-side fault from deep inside the scoring
    # stack and report it to a team as if the team had done something wrong.
    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as failure:
        raise VariantIntegrityError(f"{path} is not a usable declaration: {failure}") from failure
    verify_declaration_or_refuse(candidate_root, declaration)
    return declaration


def materialise_neighbourhood(
    candidate_root: str | Path,
    sweep_root: str | Path,
    declaration: NeighbourhoodDeclaration,
) -> tuple[MaterialisedPoint, ...]:
    """Write every declared point, nominee first, as its own complete candidate directory."""
    root = Path(sweep_root)
    points: list[MaterialisedPoint] = []
    for index, point in enumerate(declaration.all_points()):
        is_nominee = index == 0
        points.append(
            materialise_point(
                candidate_root,
                root / f"point-{index:02d}",
                declaration=declaration,
                point=point,
                is_nominee=is_nominee,
                label=point_label(index, point, is_nominee=is_nominee),
            )
        )
    return tuple(points)


def _run_jobs(jobs: Sequence[PointJob], *, workers: int) -> list[PointOutcome]:
    """Evaluate every job, each in a freshly spawned interpreter, and return them in job order.

    ``max_tasks_per_child=1`` is what makes "freshly spawned" true of every point rather than only
    of every worker slot: without it a pool of three workers evaluating seven points would run two
    or three points inside one interpreter, and the second point would inherit whatever the first
    left in the process.
    """
    if workers < 1:
        raise ValueError(f"workers must be at least 1, got {workers}")
    # A pool even at ``workers=1``, never a plain loop in this process. Running the serial path
    # in-process would be a SECOND execution model with weaker isolation than the parallel one, so
    # ``--workers 1`` would be a quietly different scorer from the default -- the exact two-currency
    # failure the single-scorer rule exists to prevent. The cost of being consistent is one
    # interpreter spawn per point, against an eight-minute evaluation.
    context = multiprocessing.get_context("spawn")
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers, mp_context=context, max_tasks_per_child=1
    ) as pool:
        futures = [pool.submit(evaluate_materialised_point, job) for job in jobs]
        outcomes: list[PointOutcome] = []
        for job, future in zip(jobs, futures, strict=True):
            try:
                outcomes.append(future.result())
            except Exception as failure:
                raise SweepError(f"{job.label} did not complete: {failure}") from failure
        return outcomes


def default_workers(point_count: int) -> int:
    """A modest default: never more than four, never more than there are points.

    Four rather than "every core" on purpose. Phase 1 runs twelve teams against one machine, and a
    sweep that helped itself to every core would make eleven other teams' runs slower while its own
    points queued anyway. A team with the machine to itself can raise it; the answer does not
    change either way.
    """
    return max(1, min(4, point_count, os.cpu_count() or 1))


def run_neighbourhood_sweep(
    *,
    raw: Mapping[str, Any],
    config_path: str | Path,
    snapshot_root: str | Path,
    snapshot_sha256: str,
    candidate_root: str | Path,
    workspace_root: str | Path,
    sweep_root: str | Path,
    team_id: str,
    candidate_id: str,
    seed: int,
    declared_roles: Sequence[str],
    trial_sequence: int,
    accepted_trials: int,
    source_sha256: str,
    is_start: pd.Timestamp,
    workers: int | None = None,
) -> NeighbourhoodPacket:
    """Validate, materialise, run every point, and take the per-metric median. In that order.

    The order is the substance. Validation happens before a single point is materialised and before
    a single row is read, so a neighbourhood that cannot be scored costs nothing but the time to
    say so -- and ``scripts/cup20_trial.py`` refuses to journal a ``--kind neighbourhood`` trial
    against a declaration that fails these same checks, so it costs no trial either.
    """
    started = time.monotonic()
    workspace = scan_workspace_or_refuse(workspace_root, team_id=team_id)
    declaration = load_neighbourhood(candidate_root)
    materialised = materialise_neighbourhood(candidate_root, sweep_root, declaration)
    resolved_workers = default_workers(len(materialised)) if workers is None else int(workers)

    jobs = [
        PointJob(
            label=point.label,
            is_nominee=point.is_nominee,
            coordinates=dict(point.coordinates),
            root=str(point.root),
            entrypoint_sha256=point.entrypoint_sha256,
            snapshot_root=str(snapshot_root),
            config_path=str(config_path),
            seed=int(seed),
            is_start=str(is_start),
        )
        for point in materialised
    ]
    outcomes = tuple(_run_jobs(jobs, workers=resolved_workers))

    per_point = [outcome.scored for outcome in outcomes]
    median = neighbourhood_median(per_point)
    fraction = positive_point_fraction(per_point)
    bootstrap = median_bootstrap_fraction(outcomes)
    confidence = (
        0.0
        if not math.isfinite(bootstrap)
        else trial_adjusted_confidence(bootstrap, accepted_trials)
    )
    adjudication = adjudicate_candidate(
        median,
        team_id=team_id,
        candidate_id=candidate_id,
        floors=raw["floors"],
        statistics_config=raw["statistics"],
        research_config=raw["research"],
        declared_roles=tuple(declared_roles),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=fraction,
        trial_adjusted_confidence=confidence,
        drawdown_floor=float(raw["floors"]["max_drawdown"]),
    )
    details = gate_details(
        adjudication.gates.checks,
        median,
        floors=raw["floors"],
        statistics_config=raw["statistics"],
        research_config=raw["research"],
        declared_roles=declared_roles,
        observed_roles=_observed_sides(median),
        neighbourhood_positive_fraction=fraction,
        confidence=confidence,
        unmeasured=UNMEASURED_BY_A_SWEEP,
    )
    return NeighbourhoodPacket(
        team_id=team_id,
        candidate_id=candidate_id,
        trial_sequence=trial_sequence,
        accepted_trials=accepted_trials,
        trial_budget=int(raw["research"]["trial_budget"]),
        source_sha256=source_sha256,
        snapshot_sha256=snapshot_sha256,
        window=(is_start, IS_END),
        folds=tuple(is_folds(is_start, IS_END)),
        seed=int(seed),
        workers=resolved_workers,
        declared_roles=tuple(declared_roles),
        coordinates=tuple(declaration.coordinates),
        outcomes=outcomes,
        median=median,
        positive_point_fraction=fraction,
        positive_point_fraction_floor=float(raw["research"]["neighbourhood_positive_fraction"]),
        bootstrap_positive_fraction=bootstrap,
        trial_adjusted_confidence=confidence,
        gate_details=details,
        unmeasured_gates=UNMEASURED_BY_A_SWEEP,
        ranking_score=adjudication.score,
        elapsed_seconds=time.monotonic() - started,
        workspace=workspace,
    )
