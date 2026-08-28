"""Nominate, or retire. One lane, one decision, no third option.

A lane whose final candidate clears the development gates is nominated; one whose candidate does not
is **retired**, plainly and in the journal. Retirement is a normal outcome here rather than a
problem to be worked around at selection time -- which is exactly what V4-R9 did, patching in a
fallback that promoted a book running 3.7% mean gross exposure and failing thirteen of twenty-two
gates to first place.

:func:`orchestrator.nominate` raises unconditionally on an ineligible candidate and takes no
parameter that could suppress it. This script cannot override that, and does not try; a lane that
fails is retired.

The nominee is the lane's **decision-phase candidate**, and nothing else. That phase exists so the
team chooses, and its guidance says in as many words that a nomination need not be the highest-Sharpe
book -- so picking a lane best-scoring trial on its behalf would be the organizer choosing and
calling it the team's decision. A lane whose decision candidate does not clear the bar is retired;
promoting an earlier trial instead would be a fallback, which this edition does not have.

The candidate archive is what makes that fair rather than harsh: every lane could read all of its
earlier books and their scores before deciding, so carrying a weaker final candidate is a choice
rather than an accident.

Usage::

    uv run python scripts/top40_v5_nominate.py --dry-run
    uv run python scripts/top40_v5_nominate.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from crypto_trade.tournament.v5 import journal, lanes, orchestrator
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

REPO = Path(__file__).resolve().parents[1]
TOURNAMENT = REPO / TOP40_V5_LAYOUT.tournament_root
JOURNAL = TOURNAMENT / "research-journal.jsonl"
# The trial that scored each lane's decision-phase candidate, which is its nomination.
DECISION_TRIAL = "t03"


class _Trial:
    """The minimum orchestrator.nominate reads, rebuilt from the journalled record."""

    def __init__(self, team_id: str, trial_id: str, admitted: bool, failures: list[str]):
        self.team_id = team_id
        self.trial_id = trial_id
        self.admitted = admitted
        self.assessment = _Assessment(failures)


class _Assessment:
    def __init__(self, failures: list[str]):
        self._failures = tuple(failures)
        self.gates: dict[str, bool] = {}

    def failures(self) -> tuple[str, ...]:
        return self._failures


def _trials() -> dict[str, list[dict]]:
    by_team: dict[str, list[dict]] = {}
    for record in journal.read(JOURNAL):
        if record.event_type in ("trial_succeeded", "trial_rejected"):
            by_team.setdefault(record.payload["team_id"], []).append(record.payload)
    return by_team


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    by_team = _trials()
    already = {r.payload["team_id"] for r in journal.iter_events(JOURNAL, "nominated")}
    already |= {r.payload["team_id"] for r in journal.iter_events(JOURNAL, "retired")}

    nominated = retired = 0
    for lane in lanes.LANES:
        if lane.team_id in already:
            print(f"  {lane.team_id:10s} already decided")
            continue
        trials = by_team.get(lane.team_id, [])
        final = next((t for t in trials if t["trial_id"] == DECISION_TRIAL), None)
        if final is not None and final["admitted"]:
            best = final
            label = (
                f"NOMINATE {best['trial_id']} "
                f"(2x sharpe {best['packet']['double_cost_sharpe']:+.3f})"
            )
            if not arguments.dry_run:
                orchestrator.nominate(
                    str(JOURNAL),
                    _Trial(lane.team_id, best["trial_id"], True, []),
                    candidate_id=best["trial_id"],
                )
            nominated += 1
        else:
            worst = (final or (trials[-1] if trials else {})).get(
                "failures", ["no decision-phase trial completed"]
            )
            label = f"retire ({','.join(worst[:3])})"
            if not arguments.dry_run:
                orchestrator.retire(
                    str(JOURNAL),
                    lane.team_id,
                    reason=(
                        f"decision-phase candidate did not clear the bar "
                        f"({len(trials)} trial(s) run)"
                    ),
                )
            retired += 1
        print(f"  {lane.team_id:10s} {label}")

    verb = "would be" if arguments.dry_run else "were"
    print(f"\n{nominated} {verb} nominated, {retired} retired")
    if nominated == 0:
        print("an empty field is a supported terminal state; there is no fallback promotion")
    return 0


if __name__ == "__main__":
    sys.exit(main())
