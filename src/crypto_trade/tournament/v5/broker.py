"""Running one phase for one lane: materialise, probe, launch, harvest, audit, journal.

This is the only place the pieces meet, and the ordering is the substance of it. Each step is a
precondition for the next, and every one of them exists because skipping it has cost a prior edition
something concrete:

1. **Materialise** a workspace holding only the bytes this lane may see. Deny-by-absence.
2. **Assert the exclusions** by looking at what was actually copied, rather than trusting the plan.
3. **Probe the boundary live**, both directions, and refuse to launch if either half fails. A
   malformed deny rule denies nothing and says nothing, so a configuration that merely looks right
   is not evidence.
4. **Journal the launch before it happens.** A record written afterwards can only describe what
   somebody believed happened.
5. **Launch**, with a timeout.
6. **Harvest** only the declared outbox surface.
7. **Audit** the harvested bytes for references that would only make sense if something outside had
   been read -- detection, not prevention, and labelled as such.
8. **Journal the outcome**, charging a trial only where a team is genuinely responsible.

Two properties are worth stating separately because they are easy to lose in a refactor.

**A lease, held one lane at a time.** Phases are not run concurrently across lanes. The evaluation
pool parallelises the *evaluator*, which is pure compute over a frozen snapshot; the agent phases
stay serial, because two lanes writing through the same organizer process is how a peer artifact
ends up somewhere it was never meant to be.

**Restart is idempotent.** A completed phase is not re-run on restart -- it is recognised from the
journal and skipped. V4 accumulated nine restarts, and the recurring damage was not the crash but
the re-execution: work redone, trials recharged, and evidence appended twice.
"""

from __future__ import annotations

import dataclasses
import hashlib
from collections.abc import Mapping, Sequence
from pathlib import Path

from crypto_trade.tournament.v5 import journal, runtime, workspace
from crypto_trade.tournament.v5.isolation import (
    RESEARCH_PHASES,
    SCOUTING_PHASE,
    PermissionProfile,
    allowed_tools,
    assert_profile_invariants,
)

# Artifacts a phase must produce for its output to count as a submission at all.
REQUIRED_ARTIFACTS: Mapping[str, tuple[str, ...]] = {
    SCOUTING_PHASE: ("THESIS.md",),
    "discovery": ("candidate.py", "RATIONALE.md"),
    "refinement": ("candidate.py", "RATIONALE.md"),
    "decision": ("candidate.py", "RATIONALE.md"),
}


class BrokerError(RuntimeError):
    """A phase could not be run, or ran into a state the edition does not permit."""


@dataclasses.dataclass(frozen=True, slots=True)
class PhaseOutcome:
    """The complete record of one phase. Journalled, and the only thing callers read."""

    team_id: str
    phase: str
    receipt: runtime.PhaseReceipt
    produced: Mapping[str, bytes]
    audit_findings: tuple[str, ...]
    skipped: bool = False

    @property
    def usable(self) -> bool:
        """Whether this phase produced something the tournament can act on.

        An audit finding does not silently discard the work -- it is surfaced for organizer review,
        because a mechanical string match is evidence of a possible read, not proof of one, and
        throwing away a lane's trial on that basis would be its own kind of error.
        """

        return self.receipt.succeeded and bool(self.produced)

    def as_dict(self) -> dict[str, object]:
        return {
            "team_id": self.team_id,
            "phase": self.phase,
            "skipped": self.skipped,
            "usable": self.usable,
            "receipt": self.receipt.as_dict(),
            "artifacts": sorted(self.produced),
            "audit_findings": list(self.audit_findings),
        }


def _digest_tree(root: Path) -> str:
    """One digest over a directory's relative paths and contents."""

    if not root.is_dir():
        return ""
    body = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_file():
            body.update(path.relative_to(root).as_posix().encode("utf-8"))
            body.update(hashlib.sha256(path.read_bytes()).digest())
    return body.hexdigest()


def phase_fingerprint(team_id: str, phase: str, prompt: str, kit_digest: str = "") -> str:
    """Identifies a phase attempt for restart purposes.

    The prompt is part of it deliberately: a changed mandate is a different phase, and silently
    inheriting the previous one's completion would let an edition claim work it never did under the
    instructions it actually issued.

    So is the **kit**, for exactly the same reason and learned the harder way. The kit is as much
    part of a lane's instructions as its prompt -- when a documentation defect in it cost two lanes
    a discovery phase, correcting the kit left the fingerprint unchanged, so the restart logic would
    have skipped both lanes as already complete and served the broken result as final.
    """

    payload = f"{team_id}\x00{phase}\x00{prompt}\x00{kit_digest}".encode()
    return hashlib.sha256(payload).hexdigest()


def already_completed(journal_path: str | Path, fingerprint: str) -> bool:
    """Whether this exact phase has already run to completion."""

    return any(
        record.payload.get("fingerprint") == fingerprint
        and record.payload.get("status") == "completed"
        for record in journal.iter_events(journal_path, "phase_launched")
    )


def run_phase(
    agent_runtime: runtime.AgentRuntime,
    profile: PermissionProfile,
    *,
    team_id: str,
    phase: str,
    prompt: str,
    workspace_root: str | Path,
    kit_source: str | Path,
    lane_files: Mapping[str, str | Path],
    forbidden_roots: Sequence[str],
    forbidden_filenames: Sequence[str],
    journal_path: str | Path,
    tournament_root: str | Path,
    probe_inside: str,
    probe_outside: str | Path,
    timeout_seconds: int = runtime.DEFAULT_TIMEOUT_SECONDS,
) -> PhaseOutcome:
    """Run one phase for one lane, or recognise that it has already run.

    Every argument that names a surface is passed explicitly rather than derived here. Deriving
    would make this function the single place that decides what a lane can see, and that decision
    belongs to the isolation policy, which is separately tested.
    """

    if phase != SCOUTING_PHASE and phase not in RESEARCH_PHASES:
        raise BrokerError(f"unknown phase: {phase}")
    assert_profile_invariants(
        profile,
        root=tournament_root,
        team_root=f"teams/{team_id}",
        forbidden_roots=forbidden_roots,
    )

    kit_digest = _digest_tree(Path(kit_source))
    fingerprint = phase_fingerprint(team_id, phase, prompt, kit_digest)
    if already_completed(journal_path, fingerprint):
        return PhaseOutcome(
            team_id=team_id,
            phase=phase,
            receipt=runtime.PhaseReceipt(
                lane=team_id,
                phase=phase,
                runtime=getattr(agent_runtime, "name", "unknown"),
                exit_code=0,
                duration_seconds=0.0,
                timed_out=False,
                produced={},
                denials=(),
                transcript_sha256="",
            ),
            produced={},
            audit_findings=(),
            skipped=True,
        )

    writable = workspace.SCOUTING_WRITABLE if phase == SCOUTING_PHASE else workspace.LANE_WRITABLE
    space = workspace.materialise(
        workspace_root,
        phase=phase,
        kit_source=kit_source,
        lane_files=lane_files,
        writable=writable,
        network=profile.network_enabled,
    )
    workspace.assert_workspace_excludes(space, forbidden_filenames)

    observed = runtime.boundary_probe(
        agent_runtime,
        space,
        lane=team_id,
        inside=Path(probe_inside),
        outside=Path(probe_outside),
        forbidden_roots=forbidden_roots,
    )
    runtime.assert_boundary_probe_passed(observed)

    # Journalled before the process starts, so a crash mid-phase leaves evidence that it began.
    journal.append(
        journal_path,
        "phase_launched",
        {
            "team_id": team_id,
            "phase": phase,
            "fingerprint": fingerprint,
            "status": "started",
            "profile_sha256": profile.sha256(),
            "workspace": space.as_dict(),
        },
    )

    surface = "scouting" if phase == SCOUTING_PHASE else "outbox"
    receipt = agent_runtime.launch(
        runtime.PhaseRequest(
            lane=team_id,
            phase=phase,
            prompt=prompt,
            workspace=space,
            forbidden_roots=tuple(forbidden_roots),
            allowed_tools=allowed_tools(profile),
            output_surface=surface,
            timeout_seconds=timeout_seconds,
        )
    )

    try:
        produced = workspace.harvest(space, surface)
    except workspace.WorkspaceError:
        produced = {}

    findings = tuple(workspace.audit_workspace(space, produced, forbidden_roots=forbidden_roots))
    outcome = PhaseOutcome(
        team_id=team_id,
        phase=phase,
        receipt=receipt,
        produced=produced,
        audit_findings=findings,
    )

    journal.append(
        journal_path,
        "phase_launched",
        {
            "team_id": team_id,
            "phase": phase,
            "fingerprint": fingerprint,
            "status": "completed" if outcome.usable else "failed",
            "outcome": outcome.as_dict(),
        },
    )
    return outcome


def assert_required_artifacts(outcome: PhaseOutcome) -> None:
    """A phase that did not produce its declared artifacts did not complete."""

    required = REQUIRED_ARTIFACTS.get(outcome.phase, ())
    missing = [name for name in required if name not in outcome.produced]
    if missing:
        raise BrokerError(
            f"{outcome.team_id} {outcome.phase} did not produce required artifacts: {missing}"
        )


class LaneLease:
    """One lane at a time.

    The agent phases stay serial while the evaluator parallelises, because the evaluator is pure
    compute over a frozen snapshot and the agent phases write through a shared organizer process.
    Two lanes doing that concurrently is how a peer artifact reaches a lane that should never have
    seen it.
    """

    def __init__(self) -> None:
        self._holder: str | None = None

    @property
    def holder(self) -> str | None:
        return self._holder

    def acquire(self, team_id: str) -> None:
        if self._holder is not None and self._holder != team_id:
            raise BrokerError(
                f"{self._holder} already holds the lane lease; {team_id} must wait. "
                "Agent phases are deliberately serial across lanes."
            )
        self._holder = team_id

    def release(self, team_id: str) -> None:
        if self._holder != team_id:
            raise BrokerError(f"{team_id} does not hold the lane lease ({self._holder} does)")
        self._holder = None

    def __enter__(self) -> LaneLease:
        return self

    def __exit__(self, *exception: object) -> None:
        self._holder = None


__all__ = [
    "REQUIRED_ARTIFACTS",
    "BrokerError",
    "LaneLease",
    "PhaseOutcome",
    "already_completed",
    "assert_required_artifacts",
    "phase_fingerprint",
    "run_phase",
]
