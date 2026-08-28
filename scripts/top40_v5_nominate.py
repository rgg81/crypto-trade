"""Nominate, or retire. One lane, one decision, no third option.

A lane whose final candidate clears the development gates is nominated; one whose candidate does not
is **retired**, plainly and in the journal. Retirement is a normal outcome here rather than a
problem to be worked around at selection time -- which is exactly what V4-R9 did, patching in a
fallback that promoted a book running 3.7% mean gross exposure and failing thirteen of twenty-two
gates to first place.

:func:`orchestrator.nominate` raises unconditionally on an ineligible candidate and takes no
parameter that could suppress it. This script cannot override that, and does not try; a lane that
fails is retired.

Nomination reads whichever trial is the lane's best **admitted** result, not necessarily its last.
team-09's discovery book was admitted and its refined book was not, so "last" would have discarded
the only qualifying evidence it has.

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
        admitted = [t for t in trials if t["admitted"]]
        if admitted:
            # Best admitted by 2x-cost Sharpe: a book that survives costs is the one worth carrying,
            # and the sealed stage will judge robustness rather than this number.
            best = max(admitted, key=lambda t: t["packet"]["double_cost_sharpe"])
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
            worst = trials[-1]["failures"] if trials else ["no trial completed"]
            label = f"retire ({','.join(worst[:3])})"
            if not arguments.dry_run:
                orchestrator.retire(
                    str(JOURNAL),
                    lane.team_id,
                    reason=f"no admitted candidate across {len(trials)} trial(s)",
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
