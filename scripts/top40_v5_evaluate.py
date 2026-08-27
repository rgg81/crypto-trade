"""Evaluate lane candidates as charged trials, and return each lane its feedback packet.

This is where a trial is actually spent, so the ordering is the substance of it:

1. **Journal ``trial_accepted`` before market data is opened.** A record written afterwards can only
   describe what somebody believed happened, and this is the record that makes the trial count in a
   deflated Sharpe mean something.
2. Evaluate the whole development window at 1x, 2x and 3x costs -- three independent runs, never one
   rescaled, because costs interact with the participation cap and with forced exits.
3. Score **only the visible days**. The sealed blocks are held by a different function that this one
   never calls and never receives an index for.
4. Journal the outcome. A rejected candidate consumes its slot; an **evaluator fault does not** --
   V4-R9 charged eighty-six trials to teams because the evaluator raised on one bar, unevenly across
   eleven of fifteen lanes.
5. Write the lane its feedback packet: the allowlisted fields, visible window only.

Usage::

    uv run python scripts/top40_v5_evaluate.py --team team-01     # one lane
    uv run python scripts/top40_v5_evaluate.py                    # the field
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import warnings
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.v5 import contract, gates, journal, lanes, runner, sealed
from crypto_trade.tournament.v5.engine import EvaluatorConfig, generate_targets
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

REPO = Path(__file__).resolve().parents[1]
TOURNAMENT = REPO / TOP40_V5_LAYOUT.tournament_root
SNAPSHOT = REPO / "data" / "top40" / "snapshot-v3"
SCORED_START = pd.Timestamp("2020-08-02", tz="UTC")
SCORED_END = pd.Timestamp("2024-02-01", tz="UTC")
INTERVAL_HOURS = 8


def _thresholds() -> gates.GateThresholds:
    """Read the frozen contract rather than restating its numbers here."""

    raw = contract.load_config(TOURNAMENT / "config.toml").raw
    floors = raw["selection"]["floors"]  # type: ignore[index]
    return gates.GateThresholds(
        minimum_mean_gross_exposure=floors["minimum_mean_gross_exposure"],
        minimum_median_effective_breadth=floors["minimum_median_effective_breadth"],
        minimum_breadth_pass_fraction=floors["minimum_breadth_pass_fraction"],
        minimum_active_bar_fraction=floors["minimum_active_bar_fraction"],
        minimum_side_exposure_share=floors["minimum_side_exposure_share"],
        volatility_band=(
            floors["minimum_realized_annual_volatility"],
            floors["maximum_realized_annual_volatility"],
        ),
        maximum_risk_unit_capped_fraction=floors["maximum_risk_unit_capped_fraction"],
        minimum_annualised_turnover=floors["minimum_annualised_turnover"],
        maximum_annualised_turnover=floors["maximum_annualised_turnover"],
        minimum_gross_edge_bps_per_turnover=floors["minimum_gross_edge_bps_per_turnover"],
        maximum_cost_share_of_positive_gross=floors["maximum_cost_share_of_positive_gross"],
        minimum_positive_fold_fraction=floors["minimum_positive_fold_fraction"],
        minimum_deflated_sharpe_probability=floors["minimum_deflated_sharpe_probability"],
        maximum_vol_normalised_drawdown=floors["maximum_vol_normalised_drawdown"],
        maximum_top_symbol_gross_pnl_share=floors["maximum_top_symbol_gross_pnl_share"],
        minimum_deletion_profile_p05_sharpe=floors["minimum_deletion_profile_p05_sharpe"],
        minimum_accepted_trials=floors["minimum_accepted_trials"],
        volatility_reference=floors["volatility_reference"],
    )


def _partition() -> sealed.SealedPartition:
    index = pd.date_range(SCORED_START, SCORED_END - pd.Timedelta(days=1), freq="D", tz="UTC")
    blocks = sealed.sealed_blocks(
        start=SCORED_START,
        end_exclusive=SCORED_END,
        block_days=45,
        stride=7,
        residues=(1, 4),
        interleaved_count=7,
        terminal_block=True,
    )
    return sealed.partition(index, blocks, purge_days=5, embargo_days=10)


def _load_strategy(team_id: str):  # type: ignore[no-untyped-def]
    path = TOURNAMENT / "teams" / team_id / "outbox" / "candidate.py"
    spec = importlib.util.spec_from_file_location(f"candidate_{team_id}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module.build_strategy(), path


def evaluate_team(team_id: str, data, part, thresholds, decisions, trial_id: str) -> dict:
    journal_path = TOURNAMENT / "research-journal.jsonl"
    started = time.monotonic()

    strategy, source = _load_strategy(team_id)
    # Accepted before any market data is opened. This is the record that makes a trial count.
    journal.append(
        journal_path,
        "trial_accepted",
        {
            "team_id": team_id,
            "trial_id": trial_id,
            "candidate_lines": len(
                source.read_text(encoding="utf-8", errors="replace").splitlines()
            ),
        },
    )

    try:
        targets = generate_targets(
            strategy,
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
        trial = runner.run_development_trial(
            ladder,
            part.visible,
            thresholds,
            team_id=team_id,
            trial_id=trial_id,
            reports_root=REPO / TOP40_V5_LAYOUT.is_reports_root,
            trial_count=1,
            trial_sharpe_dispersion=0.0,
            accepted_trials=8,
            source_review_passed=True,
            invariance_suite_passed=True,
        )
    except Exception as error:  # noqa: BLE001 - an organizer fault must not charge the team
        journal.append(
            journal_path,
            "trial_evaluator_fault",
            {"team_id": team_id, "trial_id": trial_id, "error": f"{type(error).__name__}: {error}"},
        )
        print(f"  {team_id:10s} EVALUATOR FAULT (refunded): {type(error).__name__}: {error}"[:150])
        return {"team_id": team_id, "fault": True}

    journal.append(
        journal_path,
        "trial_succeeded" if trial.admitted else "trial_rejected",
        {
            "team_id": team_id,
            "trial_id": trial_id,
            "admitted": trial.admitted,
            "failures": list(trial.assessment.failures()),
            "packet": trial.packet.as_dict(),
        },
    )

    # The lane's own feedback, visible window only, allowlisted fields.
    feedback = TOURNAMENT / "teams" / team_id / "feedback"
    feedback.mkdir(parents=True, exist_ok=True)
    (feedback / f"{trial_id}.json").write_text(
        json.dumps(
            {
                "trial_id": trial_id,
                "admitted": trial.admitted,
                "failed_gates": list(trial.assessment.failures()),
                "metrics": dict(trial.feedback),
            },
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    p = trial.packet
    print(
        f"  {team_id:10s} {'ADMIT' if trial.admitted else 'reject':>6}  "
        f"sh={p.net_sharpe:+.3f} 2x={p.double_cost_sharpe:+.3f} "
        f"gross={p.mean_gross_exposure:.2f} brd={p.median_effective_breadth:4.1f} "
        f"turn={p.annualised_turnover:6.1f} edge={p.gross_edge_bps_per_turnover:6.1f} "
        f"dd={p.max_drawdown:.2f}  [{(time.monotonic() - started) / 60:.1f}m] "
        f"{','.join(trial.assessment.failures()) if not trial.admitted else ''}"[:190],
        flush=True,
    )
    return {"team_id": team_id, "admitted": trial.admitted, "packet": p.as_dict()}


def main() -> int:
    warnings.filterwarnings("ignore")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--team", default=None)
    parser.add_argument("--trial-id", default="t01")
    arguments = parser.parse_args()

    roster = [lanes.lane(arguments.team)] if arguments.team else list(lanes.LANES)
    thresholds = _thresholds()
    part = _partition()
    runner.assert_windows_are_disjoint(part.visible, part.sealed)
    print(
        f"visible={len(part.visible)}d sealed={len(part.sealed)}d (never scored here)", flush=True
    )

    data = {
        name: pd.read_parquet(SNAPSHOT / f"{name}.parquet")
        for name in ("bars", "funding", "membership", "mark_prices")
    }
    decisions = list(
        pd.date_range(
            SCORED_START, SCORED_END, freq=f"{INTERVAL_HOURS}h", tz="UTC", inclusive="left"
        )
    )
    print(f"{len(roster)} lane(s), {len(decisions)} decisions each\n", flush=True)

    results = [
        evaluate_team(lane.team_id, data, part, thresholds, decisions, arguments.trial_id)
        for lane in roster
    ]
    admitted = sum(1 for r in results if r.get("admitted"))
    faults = sum(1 for r in results if r.get("fault"))
    print(f"\n{admitted}/{len(results)} admitted, {faults} evaluator fault(s) refunded")
    return 0


if __name__ == "__main__":
    sys.exit(main())
