"""Evaluate nominated candidates on the sealed blocks. Organizer only.

The confirmation stage. Everything it writes goes to the private sealed root, never to the visible
reports root, and nothing it computes is returned to a lane -- which is why it is a separate script
rather than a flag on the evaluator: the two use different functions, write to different roots, and
neither is handed the other's index.

What this stage can and cannot conclude, stated because it constrains how the result may be read:

It is a **screen**, not a certification. At 360 sealed days the standard error of an annualised
Sharpe is about 1.0, and no threshold does better. The measured operating characteristic of this
bar is a 0.283 null pass rate against 0.662 power at a true Sharpe of 1.0 -- so roughly a third of
worthless books survive it and roughly a third of good ones do not. Its job is to stop the 2.5-year
historical window being spent on books that are degenerate, cost-annihilated or negative. Ranking
happens later, on the historical window; capital is decided only on the forward record.

The trial count here is **one**. A team selected its nominee from a search over *visible* data that
the sealed blocks never saw, so holding them out is already the correction and the sealed estimate
is unbiased. Deflating again by the team's trial count charges the same search twice, and measurably
costs more than half the power at a true Sharpe of 1.0.

Usage::

    uv run python scripts/top40_v5_sealed.py --team team-14
    uv run python scripts/top40_v5_sealed.py
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.v5 import journal, lanes, runner
from crypto_trade.tournament.v5.engine import EvaluatorConfig, generate_targets
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

sys.path.insert(0, str(Path(__file__).resolve().parent))
from top40_v5_evaluate import (  # noqa: E402
    INTERVAL_HOURS,
    REPO,
    SCORED_END,
    SCORED_START,
    SNAPSHOT,
    TOURNAMENT,
    _partition,
    _thresholds,
)


def _nominations() -> dict[str, str]:
    """The candidate each lane nominated, from the journal rather than from the filesystem."""

    nominated = {}
    for record in journal.iter_events(TOURNAMENT / "research-journal.jsonl", "nominated"):
        nominated[record.payload["team_id"]] = record.payload["candidate_id"]
    return nominated


def confirm(team_id: str, candidate_id: str, data, part, thresholds, decisions) -> dict:
    started = time.monotonic()
    path = TOURNAMENT / "teams" / team_id / "outbox" / "candidate.py"
    spec = importlib.util.spec_from_file_location(f"sealed_{team_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    targets = generate_targets(
        module.build_strategy(),
        data["bars"],
        data["funding"],
        data["membership"],
        decisions,
        seed=42,
        interval_hours=INTERVAL_HOURS,
    )
    ladder = runner.evaluate_cost_ladder(
        data["bars"],
        data["funding"],
        data["membership"],
        targets,
        mark_prices=data["mark_prices"],
        config=EvaluatorConfig(),
    )
    confirmation = runner.run_sealed_confirmation(
        ladder,
        part.sealed,
        thresholds,
        team_id=team_id,
        candidate_id=candidate_id,
        private_root=REPO / TOP40_V5_LAYOUT.sealed_private_root,
        accepted_trials=8,
        source_review_passed=True,
        invariance_suite_passed=True,
    )
    journal.append(
        TOURNAMENT / "research-journal.jsonl",
        "sealed_evaluated",
        {
            "team_id": team_id,
            "candidate_id": candidate_id,
            "cleared": confirmation.cleared,
            "failures": list(confirmation.assessment.failures()),
            "packet": confirmation.packet.as_dict(),
        },
    )
    p = confirmation.packet
    print(
        f"  {team_id:10s} {'CLEAR' if confirmation.cleared else 'no':>5}  "
        f"sh={p.net_sharpe:+.3f} 2x={p.double_cost_sharpe:+.3f} "
        f"robust={p.deletion_profile_p05_sharpe:+.3f} dsr={p.deflated_sharpe_probability:.3f} "
        f"turn={p.annualised_turnover:6.1f} dd={p.max_drawdown:.2f} "
        f"[{(time.monotonic() - started) / 60:.1f}m] "
        f"{','.join(confirmation.assessment.failures())}"[:190],
        flush=True,
    )
    return {"team_id": team_id, "cleared": confirmation.cleared}


def main() -> int:
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", default=None)
    arguments = parser.parse_args()

    nominated = _nominations()
    if not nominated:
        print("no nominations recorded; run the decision phase and nominate first")
        return 1
    roster = (
        [lanes.lane(arguments.team)]
        if arguments.team
        else [lane for lane in lanes.LANES if lane.team_id in nominated]
    )

    thresholds = _thresholds()
    part = _partition()
    runner.assert_windows_are_disjoint(part.visible, part.sealed)
    print(f"sealed={len(part.sealed)}d across {len(part.blocks)} blocks", flush=True)
    print(f"{len(roster)} nomination(s); trial count 1, uncorrected\n", flush=True)

    data = {
        name: pd.read_parquet(SNAPSHOT / f"{name}.parquet")
        for name in ("bars", "funding", "membership", "mark_prices")
    }
    decisions = list(
        pd.date_range(
            SCORED_START, SCORED_END, freq=f"{INTERVAL_HOURS}h", tz="UTC", inclusive="left"
        )
    )

    results = []
    for lane in roster:
        try:
            results.append(
                confirm(lane.team_id, nominated[lane.team_id], data, part, thresholds, decisions)
            )
        except Exception as error:  # noqa: BLE001
            print(f"  {lane.team_id:10s} FAULT {type(error).__name__}: {error}"[:150], flush=True)

    cleared = sum(1 for r in results if r["cleared"])
    print(f"\n{cleared}/{len(results)} cleared the sealed bar")
    # The visible root must never acquire a sealed artifact, and this is checked by looking.
    runner.assert_no_sealed_artifact_is_visible(REPO / TOP40_V5_LAYOUT.is_reports_root)
    print("visible reports root contains no sealed artifact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
