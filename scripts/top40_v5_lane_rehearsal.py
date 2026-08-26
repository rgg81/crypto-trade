"""Drive one real lane through the real broker with a real agent, end to end.

The definitive readiness proof, and the last thing that runs before a green light. Everything below
it is unit-tested; this is the only check that exercises the *composition* -- materialise, assert
exclusions, probe the boundary live, journal, launch a real agent, harvest, audit, journal again --
against the actual filesystem, the actual runtime and the actual lane material.

It rehearses on a **copy** of the lane and a throwaway journal, so nothing it does can touch the
tournament's own state. A rehearsal that wrote into the real journal would itself be a contamination
of the record it exists to protect.

What it proves, and what it does not. It proves a lane can start: the sandbox holds, the agent
produces the declared artifacts, the harvest collects them and the audit is clean. It does not
prove the strategy is any good, and it deliberately does not run a scored trial -- the first charged
trial is the organizer seed, and spending one here would consume a lane's budget on a rehearsal.

Usage::

    uv run python scripts/top40_v5_lane_rehearsal.py --team team-08
"""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from crypto_trade.tournament.v5 import broker, isolation, journal, lanes, runtime
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

REPO = Path(__file__).resolve().parents[1]

REHEARSAL_PROMPT = """You are a quantitative researcher on an isolated tournament lane.

Read lane/TEAM-BRIEF.md and team-kit/RULES.md. Then write two files:

1. `lane/outbox/candidate.py` — a Python module defining `build_strategy()` that returns an object
   with a `target_weights(context, *, seed)` method returning a mapping of symbol to signed weight.
   Implement the simplest possible expression of your assigned mandate. Keep it under 60 lines.
2. `lane/outbox/RATIONALE.md` — three short paragraphs: the economic mechanism you are trading, who
   is on the other side, and the falsifier you would accept.

Work only inside your lane. Do not attempt to read anything outside it."""


def _candidate_trades(source: str, staging: Path) -> bool:
    """Execute the agent's candidate against a real DecisionContext and see if it opens a book.

    The check that matters most, and one a rehearsal without it would miss entirely. A candidate
    that misreads the context shape raises nothing -- it returns no weights and holds a flat book
    all window, which reads as a strategy with no edge rather than one that never ran.
    That is precisely how two organizer seeds scored exactly zero across 808 days before a run
    against real data exposed them.
    """

    snapshot = REPO / "data" / "top40" / "snapshot-v3"
    if not (snapshot / "bars.parquet").is_file():
        print("\ncandidate exec: SKIPPED (no snapshot in this checkout)")
        return True

    import importlib.util

    import pandas as pd

    from crypto_trade.tournament.v5.engine import generate_targets

    module_path = staging / "candidate_under_test.py"
    module_path.write_text(source, encoding="utf-8")
    spec = importlib.util.spec_from_file_location("candidate_under_test", module_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
        strategy = module.build_strategy()
    except Exception as error:  # noqa: BLE001 - the report is the point
        print(f"\ncandidate exec: FAILED to load — {type(error).__name__}: {error}")
        return False

    frames = {
        name: pd.read_parquet(snapshot / f"{name}.parquet")
        for name in ("bars", "funding", "membership")
    }
    decisions = list(pd.date_range("2022-03-01", "2022-03-06", freq="8h", tz="UTC"))
    try:
        targets = generate_targets(
            strategy, frames["bars"], frames["funding"], frames["membership"], decisions, seed=42
        )
    except Exception as error:  # noqa: BLE001
        print(f"\ncandidate exec: RAISED — {type(error).__name__}: {error}")
        return False

    tradable = targets.drop(
        columns=[c for c in targets.columns if c.startswith("__")], errors="ignore"
    )
    numeric = tradable.select_dtypes("number")
    positions = int((numeric.abs() > 1e-9).to_numpy().sum()) if not numeric.empty else 0
    print(f"\ncandidate exec: {positions} non-zero targets across {len(decisions)} decisions")
    if positions == 0:
        print("  the candidate ran but never opened a position — it would score a flat book")
    return positions > 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", default="team-08")
    parser.add_argument("--timeout", type=int, default=900)
    arguments = parser.parse_args()

    lane = lanes.lane(arguments.team)
    tournament_root = REPO / TOP40_V5_LAYOUT.tournament_root
    lane_source = tournament_root / "teams" / lane.team_id
    if not (lane_source / "TEAM-BRIEF.md").is_file():
        print(f"{lane.team_id} is not scaffolded; run top40_v5_scaffold_lanes.py first")
        return 1

    staging = Path(tempfile.mkdtemp(prefix=f"v5-rehearsal-{lane.team_id}-", dir=Path.home()))
    try:
        # A throwaway journal: a rehearsal must not write into the record it exists to protect.
        journal_path = staging / "rehearsal-journal.jsonl"
        journal.initialize(journal_path)

        peers = [
            str(tournament_root / "teams" / other.team_id)
            for other in lanes.LANES
            if other.team_id != lane.team_id
        ]
        forbidden_roots = [*peers, str(REPO / "src"), str(REPO / "reports-top40-v5")]

        profile = isolation.offline_profile(
            str(tournament_root),
            f"teams/{lane.team_id}",
            "team-kit",
            toolchain_root=str(REPO / ".venv"),
        )

        print(f"lane      {lane.team_id} — {lane.title}")
        print(f"family    {lane.family}")
        print(f"forbidden {len(forbidden_roots)} roots ({len(peers)} peer lanes)")

        outcome = broker.run_phase(
            runtime.ClaudeCodeRuntime(),
            profile,
            team_id=lane.team_id,
            phase="discovery",
            prompt=REHEARSAL_PROMPT,
            workspace_root=staging / "workspace",
            kit_source=tournament_root / "team-kit",
            lane_files={"TEAM-BRIEF.md": lane_source / "TEAM-BRIEF.md"},
            forbidden_roots=forbidden_roots,
            forbidden_filenames=[f"{other.team_id}.py" for other in lanes.LANES],
            journal_path=journal_path,
            tournament_root=str(tournament_root),
            probe_inside="lane/TEAM-BRIEF.md",
            probe_outside=Path(peers[0]) / "TEAM-BRIEF.md",
            timeout_seconds=arguments.timeout,
        )

        print(f"\nexit      {outcome.receipt.exit_code}  ({outcome.receipt.duration_seconds:.0f}s)")
        print(f"artifacts {sorted(outcome.produced)}")
        print(f"audit     {outcome.audit_findings or 'clean'}")
        print(f"denials   {outcome.receipt.denials or 'none'}")

        try:
            broker.assert_required_artifacts(outcome)
            complete = True
        except broker.BrokerError as error:
            complete = False
            print(f"INCOMPLETE: {error}")

        candidate = outcome.produced.get("candidate.py", b"").decode("utf-8", "replace")
        if candidate:
            head = "\n".join(f"    {line}" for line in candidate.splitlines()[:12])
            print(f"\ncandidate.py (first lines):\n{head}")

        statuses = [
            record.payload.get("status")
            for record in journal.iter_events(journal_path, "phase_launched")
        ]
        print(f"\njournal   {statuses}")

        traded = _candidate_trades(candidate, staging) if candidate else False

        ok = outcome.usable and complete and not outcome.audit_findings and traded
        print(f"\nRESULT: {'READY' if ok else 'NOT READY'}")
        return 0 if ok else 1
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
