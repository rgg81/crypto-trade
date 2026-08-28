"""Run the tournament: every lane, every phase, one at a time, restartable.

The entry point for the actual run. It holds the lane lease, walks the fifteen lanes through each
phase in turn, and writes every artifact back into the lane it came from.

Four properties are structural rather than conventional, and each exists because a prior edition
lost something to its absence.

**Nothing runs before activation.** The first thing this does is load the activation freeze and
refuse without one. A lane that started before the config was frozen would be researching against
thresholds that could still move.

**One lane at a time.** The lease is held for the whole of a lane's phase. The evaluator
parallelises later -- it is pure compute over a frozen snapshot -- but the agent phases stay serial,
because two lanes writing through one organizer process is how a peer artifact reaches a lane that
should never have seen it.

**Restart is free.** Every phase is fingerprinted over (team, phase, prompt) and a completed one is
recognised from the journal and skipped. V4 accumulated nine restarts and the recurring damage was
the re-execution, not the crash.

**A lane that fails does not stop the field.** Its failure is journalled and the run continues. One
lane's broken phase is not a reason to deny the other fourteen their research.

Usage::

    uv run python scripts/top40_v5_tournament.py --phase scouting --dry-run
    uv run python scripts/top40_v5_tournament.py --phase scouting
    uv run python scripts/top40_v5_tournament.py --phase discovery --team team-03
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
import time
from pathlib import Path

from crypto_trade.tournament.v5 import (
    activation,
    broker,
    isolation,
    journal,
    lanes,
    runtime,
)
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

REPO = Path(__file__).resolve().parents[1]
PHASES = (isolation.SCOUTING_PHASE, *isolation.RESEARCH_PHASES)

SCOUTING_TASK = """You are a quantitative researcher beginning work on an isolated tournament lane.

Read `lane/TEAM-BRIEF.md` for your assigned mandate and `lane/SCOUTING-BRIEF.md` for what this phase
requires. You have the public internet and no market data.

Research the professional literature on your assigned economic family — how crypto hedge funds and
systematic managers actually trade it, what the premium is compensation for, and what is known about
where it fails. Then write `lane/scouting/THESIS.md` exactly as SCOUTING-BRIEF.md specifies.

This thesis is sealed before any market data is mounted. You cannot revise it after seeing a result,
so state the falsifier you are genuinely willing to be held to."""

RESEARCH_TASK = """You are a quantitative researcher on an isolated tournament lane.

Read `lane/TEAM-BRIEF.md` (your mandate), `team-kit/RULES.md` (the contract), and
`team-kit/protocol.py` (the authoritative interface). If `lane/scouting/THESIS.md` is present it is
your own preregistered thesis — work from it. If `lane/feedback/` holds packets from earlier trials,
read them: they are your only evidence, and they cover the visible development window only.

Write `lane/outbox/candidate.py` defining `build_strategy()`, and `lane/outbox/RATIONALE.md`
explaining the mechanism, who is on the other side, and what would falsify it.

Phase guidance — {phase}:
{guidance}

Read `protocol.py` rather than assuming the shape of `context`. A strategy that misreads it raises
nothing, opens no position, and scores as a book with no edge rather than one that never ran.

Work only inside your lane."""

GUIDANCE = {
    "discovery": (
        "Express your mandate in its most direct form. Prefer the honest simple version over a "
        "clever one — you have later phases to elaborate, and a baseline you understand is worth "
        "more than a complex book you cannot diagnose."
    ),
    "refinement": (
        "You have feedback on the visible window. Diagnose rather than tune: if the book failed a "
        "structural gate, that is a design problem, not a parameter problem. Costs are charged at "
        "1x, 2x and 3x — a book that only survives at 1x is not a book."
    ),
    "decision": (
        "Choose what you will nominate. It does not have to be your highest Sharpe: qualification "
        "is a bar on structure and cost, and ranking happens later on evidence you have never "
        "seen. A robust book you can explain beats a fragile one you cannot."
    ),
}


def _lane_files(lane_root: Path, phase: str) -> dict[str, Path]:
    """Exactly what this phase may read from the lane. An allowlist, named file by file."""

    files = {"TEAM-BRIEF.md": lane_root / "TEAM-BRIEF.md"}
    if phase == isolation.SCOUTING_PHASE:
        files["SCOUTING-BRIEF.md"] = lane_root / "SCOUTING-BRIEF.md"
        return files

    files["RESEARCH-BRIEF.md"] = lane_root / "RESEARCH-BRIEF.md"
    thesis = lane_root / "scouting" / "THESIS.md"
    if thesis.is_file():
        files["scouting/THESIS.md"] = thesis
    feedback = lane_root / "feedback"
    if feedback.is_dir():
        for packet in sorted(feedback.glob("*.json")):
            files[f"feedback/{packet.name}"] = packet
    # The decision phase may re-nominate an earlier book, so it needs the sources as well as the
    # scores. Earlier phases do not get the archive -- discovery has nothing to look back on, and
    # handing refinement its own previous attempt invites tuning where the guidance asks for
    # diagnosis.
    if phase == "decision":
        archive = lane_root / "candidates"
        if archive.is_dir():
            for prior in sorted(archive.iterdir()):
                if prior.is_file() and not prior.name.startswith("."):
                    files[f"candidates/{prior.name}"] = prior
    return files


def _prompt(lane: lanes.Lane, phase: str) -> str:
    if phase == isolation.SCOUTING_PHASE:
        return SCOUTING_TASK
    return RESEARCH_TASK.format(phase=phase, guidance=GUIDANCE[phase])


def run_lane(
    lane: lanes.Lane,
    phase: str,
    *,
    tournament_root: Path,
    journal_path: Path,
    agent_runtime: runtime.AgentRuntime,
    timeout_seconds: int,
) -> broker.PhaseOutcome:
    lane_root = tournament_root / "teams" / lane.team_id
    peers = [
        str(tournament_root / "teams" / other.team_id)
        for other in lanes.LANES
        if other.team_id != lane.team_id
    ]
    forbidden_roots = [
        *peers,
        str(REPO / "src"),
        str(REPO / "reports-top40-v5"),
        str(tournament_root / "private"),
    ]
    profile = (
        isolation.scouting_profile
        if phase == isolation.SCOUTING_PHASE
        else isolation.offline_profile
    )(
        str(tournament_root),
        f"teams/{lane.team_id}",
        "team-kit",
        toolchain_root=str(REPO / ".venv"),
    )

    staging = Path(tempfile.mkdtemp(prefix=f"v5-{lane.team_id}-{phase}-", dir=Path.home()))
    try:
        outcome = broker.run_phase(
            agent_runtime,
            profile,
            team_id=lane.team_id,
            phase=phase,
            prompt=_prompt(lane, phase),
            workspace_root=staging / "workspace",
            kit_source=tournament_root / "team-kit",
            lane_files=_lane_files(lane_root, phase),
            forbidden_roots=forbidden_roots,
            forbidden_filenames=[f"{other.team_id}.py" for other in lanes.LANES],
            journal_path=journal_path,
            tournament_root=str(tournament_root),
            probe_inside="lane/TEAM-BRIEF.md",
            probe_outside=Path(peers[0]) / "TEAM-BRIEF.md",
            timeout_seconds=timeout_seconds,
        )
        # Artifacts go back into the lane they came from, never into a shared directory.
        #
        # Guarded, because a phase can time out having written only part of a file. The harvest
        # collects whatever is on disk regardless of how the phase ended, so a truncated candidate
        # would silently replace a working one and the lane would discover it at evaluation. Seen
        # live: team-07 timed out in refinement, and only luck decided that it had already finished
        # writing. Parsing is cheap, decisive against truncation, and does not execute the file.
        if outcome.produced and not outcome.skipped:
            broken = []
            for name, body in outcome.produced.items():
                if not name.endswith(".py"):
                    continue
                try:
                    compile(body.decode("utf-8", "replace"), name, "exec")
                except SyntaxError as error:
                    broken.append(f"{name}: {error}")
            if broken:
                print(f"  {lane.team_id}: DISCARDED, artifact does not parse: {broken}", flush=True)
                journal.append(
                    journal_path,
                    "trial_evaluator_fault",
                    {
                        "team_id": lane.team_id,
                        "phase": phase,
                        "error": f"harvested artifact does not parse; lane keeps its previous "
                        f"candidate: {broken}",
                    },
                )
                return outcome
        if outcome.produced and not outcome.skipped:
            surface = "scouting" if phase == isolation.SCOUTING_PHASE else "outbox"
            destination = lane_root / surface
            destination.mkdir(parents=True, exist_ok=True)
            for name, body in outcome.produced.items():
                (destination / name).write_bytes(body)
            # Archive under the phase that produced it, so a later phase can still nominate an
            # earlier book. Without this each phase overwrote the last and refinement became a
            # ratchet that could only lose: team-09's discovery candidate was admitted and its
            # refined one was not, and it had no way to go back to the source that worked.
            if phase != isolation.SCOUTING_PHASE:
                archive = lane_root / "candidates"
                archive.mkdir(parents=True, exist_ok=True)
                for name, body in outcome.produced.items():
                    (archive / f"{phase}-{name}").write_bytes(body)
        return outcome
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", required=True, choices=PHASES)
    parser.add_argument("--team", default=None, help="run one lane instead of the field")
    parser.add_argument("--timeout", type=int, default=1200)
    parser.add_argument("--dry-run", action="store_true", help="show what would run")
    arguments = parser.parse_args()

    tournament_root = REPO / TOP40_V5_LAYOUT.tournament_root
    journal_path = tournament_root / "research-journal.jsonl"
    freeze_path = tournament_root / "activation-freeze.json"

    roster = [lanes.lane(arguments.team)] if arguments.team else list(lanes.LANES)

    if arguments.dry_run:
        print(f"phase {arguments.phase}: would run {len(roster)} lane(s)")
        for lane in roster:
            files = sorted(_lane_files(tournament_root / "teams" / lane.team_id, arguments.phase))
            print(f"  {lane.team_id}  reads {files}")
        print(f"\nactivation freeze: {'present' if freeze_path.is_file() else 'ABSENT'}")
        return 0

    # Nothing runs before activation: a lane that started before the config was frozen would be
    # researching against thresholds that could still move.
    activation.assert_activated(freeze_path)
    if not journal_path.is_file():
        journal.initialize(journal_path)

    agent_runtime = runtime.ClaudeCodeRuntime()
    lease = broker.LaneLease()
    started = time.monotonic()
    results: dict[str, str] = {}

    print(f"phase {arguments.phase}: {len(roster)} lane(s), one at a time\n", flush=True)
    for index, lane in enumerate(roster, start=1):
        lease.acquire(lane.team_id)
        try:
            outcome = run_lane(
                lane,
                arguments.phase,
                tournament_root=tournament_root,
                journal_path=journal_path,
                agent_runtime=agent_runtime,
                timeout_seconds=arguments.timeout,
            )
            if outcome.skipped:
                status = "skipped (already complete)"
            elif outcome.usable:
                status = f"ok — {sorted(outcome.produced)}"
                if outcome.audit_findings:
                    status += f"  AUDIT: {outcome.audit_findings}"
            else:
                status = f"failed (exit {outcome.receipt.exit_code})"
        except Exception as error:  # noqa: BLE001 - one lane must not stop the field
            status = f"ERROR {type(error).__name__}: {error}"
            journal.append(
                journal_path,
                "trial_evaluator_fault",
                {"team_id": lane.team_id, "phase": arguments.phase, "error": str(error)},
            )
        finally:
            lease.release(lane.team_id)
        results[lane.team_id] = status
        print(f"[{index}/{len(roster)}] {lane.team_id}  {status}", flush=True)

    elapsed = (time.monotonic() - started) / 60.0
    ok = sum(1 for status in results.values() if status.startswith(("ok", "skipped")))
    print(f"\n{ok}/{len(roster)} lanes completed phase {arguments.phase} in {elapsed:.0f}m")
    return 0 if ok == len(roster) else 1


if __name__ == "__main__":
    sys.exit(main())
