"""An independent, contamination-free threshold proposal, in the same clean room the teams get.

I am the contaminated party. I have seen this window's results in six prior editions, including the
full published leaderboard of the edition whose sealed window is byte-identical to this one's
historical window. Every threshold I place is a number chosen by someone who knows how the story
ends, and no amount of care on my part changes that.

So a second proposal is produced by an agent that does not know. It is given the charter, the
development-only measurements and the measured seed field -- and **nothing else**: no repository, no
prior edition, no leaderboard, no result from any window. Deliberately it is *not* given my proposed
values, because a reviewer shown the answer reviews the answer rather than the question.

The comparison rule is preregistered here, before either proposal is read, so it cannot be chosen
afterwards to make the two agree:

* Within :data:`TOLERANCE` relative difference -- **agreed**. Activate the value.
* Outside it -- **disagreed**. The contamination-free proposal wins, because the only thing that
  distinguishes the two is that one of them was made by someone who has seen the outcome.
* Both proposals are recorded either way. A disagreement that resolved my way by accident should
  still be visible to a later reader.

This does not make the edition uncontaminated. It prices the contamination, which is the honest
option rather than the reassuring one.

Usage::

    uv run python scripts/top40_v5_adversarial_review.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

from crypto_trade.tournament.v5 import runtime, workspace

REPO = Path(__file__).resolve().parents[1]
CHARTER = REPO / "TOURNAMENT-CHARTER-TOP40-V5.md"
MEASUREMENTS = REPO / "tournament" / "top40-v5" / "measurements.json"
DISTRIBUTION = REPO / "reports-top40-v5" / "is" / "seed-distribution.json"
CALIBRATION = REPO / "tournament" / "top40-v5" / "calibration-report.json"

# Preregistered, before either proposal is read.
TOLERANCE = 0.25

REVIEW_TASK = """You are an independent reviewer setting qualification thresholds for a blind
quantitative trading tournament. You have no stake in any outcome and have seen no results from any
prior edition.

Read `lane/CHARTER.md` (the rules and what each stage may conclude), `lane/measurements.json`
(properties of the development window, measured on development data only) and
`lane/seed-distribution.json` (fifteen naive baseline strategies scored on the visible development
window — the only measured field that exists).

Propose a value for each threshold listed below. For each one, state in a sentence what evidence in
the two artifacts justifies it. Where the seed field is the relevant evidence, prefer placing a
threshold in an observed gap in that distribution rather than at a round number, so the value is
reproducible from the data rather than chosen.

Write your proposal to `lane/outbox/proposal.json` as a flat JSON object mapping each key below to
an object `{"value": <number>, "because": "<one sentence>"}`. Write nothing else to that file.

State every value in the units given below. Where a formula is shown, that is exactly what the
gate computes, so propose a number on that scale and no other.

Keys:
  selection.floors.minimum_mean_gross_exposure
  selection.floors.minimum_median_effective_breadth
  selection.floors.minimum_breadth_pass_fraction
  selection.floors.minimum_active_bar_fraction
  selection.floors.minimum_side_exposure_share
  selection.floors.minimum_realized_annual_volatility   [a fraction, e.g. 0.06 for 6% a year]
  selection.floors.maximum_realized_annual_volatility   [a fraction]
  selection.floors.maximum_risk_unit_capped_fraction
  selection.floors.minimum_annualised_turnover
  selection.floors.maximum_annualised_turnover
      [turnover per year, one-way executed notional over equity]
  selection.floors.minimum_gross_edge_bps_per_turnover
      [basis points of gross P&L per unit of turnover, where turnover is executed notional over
       equity and is ONE-WAY, so one unit pays one side of costs]
  selection.floors.minimum_positive_fold_fraction
  selection.floors.minimum_deflated_sharpe_probability
  selection.floors.maximum_vol_normalised_drawdown
      [computed as: max_drawdown * (0.10 / realized_annual_volatility) — a fraction, so a book
       drawing down 30% at exactly 10% realized volatility scores 0.30, NOT 3.0]
  selection.floors.maximum_top_symbol_gross_pnl_share
  sealed.purge_days
  sealed.embargo_days
  statistics.bootstrap_samples
  statistics.deletion_block_days

Two cautions the charter explains and you should weigh. A bar that no plausible strategy clears is
as broken as one a null strategy walks through — a prior edition's floor set admitted zero of
ninety-four measured trials. And the fifteen seeds are naive baselines, not good strategies: a
threshold that merely excludes all of them has excluded the baseline, not the failures."""


def _relative_difference(mine: float, theirs: float) -> float:
    scale = max(abs(mine), abs(theirs), 1e-9)
    return abs(mine - theirs) / scale


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="tournament/top40-v5/adversarial-review.json")
    parser.add_argument("--timeout", type=int, default=1800)
    arguments = parser.parse_args()

    for required in (CHARTER, MEASUREMENTS, DISTRIBUTION, CALIBRATION):
        if not required.is_file():
            print(f"missing {required}")
            return 1

    mine = json.loads(CALIBRATION.read_text(encoding="utf-8"))["resolved_values"]

    staging = Path(tempfile.mkdtemp(prefix="v5-adversarial-", dir=Path.home()))
    try:
        kit = staging / "kit"
        kit.mkdir()
        (kit / "NOTES.md").write_text(
            "You have only the three files in your lane. There is no repository here.\n",
            encoding="utf-8",
        )
        space = workspace.materialise(
            staging / "workspace",
            phase="adversarial-review",
            kit_source=kit,
            lane_files={
                "CHARTER.md": CHARTER,
                "measurements.json": MEASUREMENTS,
                "seed-distribution.json": DISTRIBUTION,
            },
            writable=workspace.LANE_WRITABLE,
            network=False,
        )
        # The reviewer must not see my values; that is the whole point of a second proposal.
        workspace.assert_workspace_excludes(space, ["calibration-report.json", "config.toml"])

        forbidden = [
            str(REPO / "src"),
            str(REPO / "tournament"),
            str(REPO / "reports-top40-v5"),
            str(REPO / "scripts"),
        ]
        for sibling in sorted(REPO.parent.glob("*")):
            if sibling != REPO and sibling.is_dir():
                forbidden.append(str(sibling))

        agent = runtime.ClaudeCodeRuntime()
        observed = runtime.boundary_probe(
            agent,
            space,
            lane="adversarial-review",
            inside=Path("lane/CHARTER.md"),
            outside=REPO / "tournament" / "top40-v5" / "config.toml",
            forbidden_roots=forbidden,
        )
        runtime.assert_boundary_probe_passed(observed)
        print(f"boundary probe: {observed}")

        receipt = agent.launch(
            runtime.PhaseRequest(
                lane="adversarial-review",
                phase="review",
                prompt=REVIEW_TASK,
                workspace=space,
                forbidden_roots=tuple(forbidden),
                allowed_tools=runtime.RESEARCH_TOOLS,
                timeout_seconds=arguments.timeout,
            )
        )
        print(f"review: exit={receipt.exit_code} ({receipt.duration_seconds:.0f}s)")

        produced = workspace.harvest(space, "outbox")
        if "proposal.json" not in produced:
            print(f"no proposal produced (got {sorted(produced)})")
            return 1
        theirs = json.loads(produced["proposal.json"].decode("utf-8"))

        rows = []
        disagreements = 0
        print(f"\n{'key':56s} {'mine':>10} {'theirs':>10}  verdict")
        for key in sorted(theirs):
            if key not in mine:
                continue
            proposed = float(theirs[key]["value"])
            held = float(mine[key])
            difference = _relative_difference(held, proposed)
            agreed = difference <= TOLERANCE
            if not agreed:
                disagreements += 1
            verdict = "agreed" if agreed else "DISAGREED -> reviewer's value wins"
            rows.append(
                {
                    "key": key,
                    "organizer": held,
                    "reviewer": proposed,
                    "relative_difference": round(difference, 4),
                    "agreed": agreed,
                    "activated": held if agreed else proposed,
                    "reviewer_reasoning": theirs[key].get("because", ""),
                }
            )
            print(f"{key:56s} {held:>10.4g} {proposed:>10.4g}  {verdict}")

        payload = {
            "schema_version": "top40-v5-adversarial-review-v1",
            "tolerance": TOLERANCE,
            "rule": (
                "within tolerance the organizer value activates; outside it the "
                "contamination-free reviewer value activates"
            ),
            "compared": len(rows),
            "disagreements": disagreements,
            "rows": rows,
        }
        destination = Path(arguments.out)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

        print(f"\n{len(rows) - disagreements}/{len(rows)} agreed within {TOLERANCE:.0%}")
        print(f"wrote {destination}")
        return 0
    finally:
        shutil.rmtree(staging, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
