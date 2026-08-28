"""Rank the cleared candidates and form the four forward desks.

Ranking is by **robustness on sealed data** -- the contiguous block-deletion fifth percentile --
never by a Sharpe and never by worst-fold. Worst-fold rewards inactivity: in V4-R9 it put a book
running 3.7% mean gross exposure and 1.39x annual turnover in first place, scoring exactly 0.000. A
near-flat book cannot win a deletion profile, because deleting any month of a book that barely
trades leaves a Sharpe near zero rather than a high one.

Qualification was a bar, not a rank cut, so every candidate that cleared the sealed blocks is ranked
here and every one of them is observed on the historical window. The desks are the top three plus an
equal-weight ensemble of those three -- equal weights because there are three constituents and
nothing to tune, and because a weighting scheme fitted now would be fitted by someone who has seen
this window's results in six prior editions.

Selection takes no minimum count, no fallback and no floor. An empty field would produce
``advancing=()`` and no desks, which is a supported terminal state rather than an error.

Usage::

    uv run python scripts/top40_v5_select.py
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

from crypto_trade.tournament.v5 import journal, metrics, orchestrator
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

REPO = Path(__file__).resolve().parents[1]
TOURNAMENT = REPO / TOP40_V5_LAYOUT.tournament_root
JOURNAL = TOURNAMENT / "research-journal.jsonl"

# Measured before any of this ran, and published beside the leaderboard so a reader can price the
# field's multiplicity. Never used as a gate: across fifteen nominees a false-discovery correction
# selects roughly half a team, which is V4-R2's unpassable bar in a new costume.
FIELD_DISPERSION = 0.768


@dataclasses.dataclass(frozen=True)
class _Confirmation:
    team_id: str
    candidate_id: str
    packet: metrics.MetricPacket
    cleared: bool

    @property
    def assessment(self):  # pragma: no cover - selection reads only `cleared`
        raise NotImplementedError


def _cleared() -> list[_Confirmation]:
    out = []
    for record in journal.iter_events(JOURNAL, "sealed_evaluated"):
        payload = record.payload
        out.append(
            _Confirmation(
                team_id=payload["team_id"],
                candidate_id=payload["candidate_id"],
                packet=metrics.MetricPacket(**payload["packet"]),
                cleared=bool(payload["cleared"]),
            )
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    arguments = parser.parse_args()

    confirmations = _cleared()
    if not confirmations:
        print("no sealed evaluations recorded")
        return 1

    selection = orchestrator.select(confirmations)
    orchestrator.assert_selection_is_honest(selection, confirmations)

    print(f"{len(confirmations)} nomination(s) evaluated on the sealed blocks\n")
    print(f"{'rank':>4} {'candidate':18s} {'robustness':>10} {'sealed sh':>9} {'2x':>7} {'dsr':>6}")
    by_name = {f"{c.team_id}:{c.candidate_id}": c for c in confirmations}
    for position, (name, robustness) in enumerate(selection.ranked, start=1):
        p = by_name[name].packet
        print(
            f"{position:>4} {name:18s} {robustness:>10.3f} {p.net_sharpe:>+9.3f} "
            f"{p.double_cost_sharpe:>+7.3f} {p.deflated_sharpe_probability:>6.3f}"
        )

    hurdle = orchestrator.expected_field_maximum(len(confirmations), FIELD_DISPERSION)
    print(f"\nexpected field maximum under the null: {hurdle:+.3f} annualised Sharpe")
    print("reported beside the leaderboard, never used as a gate")

    print(f"\n{len(selection.desks)} forward desk(s):")
    for desk in selection.desks:
        share = ", ".join(f"{n} {w:.3f}" for n, w in sorted(desk.weights.items()))
        print(f"  {desk.name:22s} {share}")

    if selection.ties:
        print("\ntied on the paired daily difference (not ranked against each other):")
        for left, right in selection.ties:
            print(f"  {left} ~ {right}")

    if not arguments.dry_run:
        orchestrator.freeze_selection(str(JOURNAL), selection)
        out = TOURNAMENT / "selection-freeze.json"
        payload = selection.as_dict()
        payload["expected_field_maximum_under_null"] = hurdle
        payload["field_dispersion"] = FIELD_DISPERSION
        out.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
        print(f"\nwrote {out.relative_to(REPO)} and froze the selection in the journal")

    print(
        "\nThe historical window ranks and staffs the desks. It authorizes nothing: "
        "capital gates on the forward record from 2026-09-01."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
