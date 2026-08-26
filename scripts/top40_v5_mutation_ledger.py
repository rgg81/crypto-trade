"""Break every gate, confirm it flips, and record the result as a durable artifact.

The countermeasure to this repository's dominant defect class: a gate that reads a field nothing
sets, compares against a threshold nothing reaches, or is simply never evaluated -- and therefore
passes everything while looking like a control. It has cost real runs. V4-R1's
``neighborhood_stability`` read false on all three advancing finalists and changed nothing;
CUP-50 v2 shipped ten separate instances of it; V4-R2 validated a config key promising floors would
not be lowered while the code had been patched to lower them.

The test is mechanical and unforgiving: for each declared gate, construct evidence that passes
everything, break **only** the field that gate reads, and require that **exactly that gate** flips.
Two failure modes are caught rather than one. A gate that does not flip is not reading its field. A
gate whose break also flips others is not isolating what it claims to measure, and a field failing
two gates would be charged twice for one defect.

The ledger this writes is bound into the activation freeze, so a later reader can see which controls
were demonstrated to work rather than taking the gate list on trust.

Usage::

    uv run python scripts/top40_v5_mutation_ledger.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from crypto_trade.tournament.v5 import gates

THRESHOLDS = gates.GateThresholds(
    minimum_mean_gross_exposure=0.30,
    minimum_median_effective_breadth=6.0,
    minimum_breadth_pass_fraction=0.80,
    minimum_active_bar_fraction=0.80,
    minimum_side_exposure_share=0.20,
    volatility_band=(0.06, 0.15),
    maximum_risk_unit_capped_fraction=0.50,
    minimum_annualised_turnover=4.0,
    maximum_annualised_turnover=90.0,
    minimum_gross_edge_bps_per_turnover=20.0,
    maximum_cost_share_of_positive_gross=0.50,
    minimum_positive_fold_fraction=0.60,
    minimum_deflated_sharpe_probability=0.60,
    maximum_vol_normalised_drawdown=0.25,
    maximum_top_symbol_gross_pnl_share=0.40,
    minimum_deletion_profile_p05_sharpe=0.0,
    minimum_accepted_trials=8,
)

PASSING = gates.SelectionEvidence(
    mean_gross_exposure=0.55,
    median_effective_breadth=11.0,
    breadth_pass_fraction=0.95,
    active_bar_fraction=0.96,
    long_exposure_share=0.50,
    short_exposure_share=0.50,
    realized_annual_volatility=0.11,
    risk_unit_capped_fraction=0.10,
    ruined=False,
    annualised_turnover=22.0,
    gross_edge_bps_per_turnover=45.0,
    cost_share_of_positive_gross=0.30,
    triple_cost_annualised_return=0.04,
    net_sharpe=1.20,
    double_cost_sharpe=0.90,
    max_drawdown=0.14,
    positive_fold_fraction=0.80,
    deflated_sharpe_probability=0.82,
    top_symbol_gross_pnl_share=0.19,
    deletion_profile_p05_sharpe=0.55,
    accepted_trials=12,
    source_review_passed=True,
    invariance_suite_passed=True,
)

# One break per gate, touching only the field that gate reads.
BREAKS: dict[str, dict[str, object]] = {
    "not_ruined": {"ruined": True},
    "mean_gross_exposure": {"mean_gross_exposure": 0.05},
    "effective_breadth": {"median_effective_breadth": 1.2},
    "breadth_persistence": {"breadth_pass_fraction": 0.20},
    "participation": {"active_bar_fraction": 0.10},
    "both_sides_used": {"long_exposure_share": 0.97, "short_exposure_share": 0.03},
    "risk_unit_attained": {"realized_annual_volatility": 0.40},
    "risk_unit_not_permanently_capped": {"risk_unit_capped_fraction": 0.95},
    "turnover_floor": {"annualised_turnover": 0.5},
    "turnover_ceiling": {"annualised_turnover": 500.0},
    "gross_edge_density": {"gross_edge_bps_per_turnover": 1.0},
    "cost_share": {"cost_share_of_positive_gross": 0.95},
    "survives_triple_cost": {"triple_cost_annualised_return": -0.30},
    "source_review": {"source_review_passed": False},
    "causal_invariance": {"invariance_suite_passed": False},
    "research_budget": {"accepted_trials": 1},
    "fold_breadth": {"positive_fold_fraction": 0.20},
    "deflated_sharpe": {"deflated_sharpe_probability": 0.01},
    "vol_normalised_drawdown": {"max_drawdown": 0.90},
    "symbol_concentration": {"top_symbol_gross_pnl_share": 0.95},
    "deletion_robustness": {"deletion_profile_p05_sharpe": -1.5},
}


def _with(**overrides: object) -> gates.SelectionEvidence:
    import dataclasses

    return dataclasses.replace(PASSING, **overrides)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="tournament/top40-v5/mutation-ledger.json")
    arguments = parser.parse_args()

    declared = set(gates.ALL_GATES)
    missing = sorted(declared - set(BREAKS))
    orphaned = sorted(set(BREAKS) - declared)
    if missing or orphaned:
        print(f"break coverage is wrong: missing={missing} orphaned={orphaned}")
        return 1

    baseline = gates.assess(PASSING, THRESHOLDS, stage=gates.SEALED_STAGE)
    if not baseline.eligible:
        print(f"the passing fixture does not pass: {baseline.failures()}")
        return 1

    entries = []
    problems = 0
    for name in sorted(declared):
        assessment = gates.assess(_with(**BREAKS[name]), THRESHOLDS, stage=gates.SEALED_STAGE)
        flipped = sorted(gate for gate, ok in assessment.gates.items() if not ok)
        reads_field = assessment.gates[name] is False
        isolated = flipped == [name]
        if not reads_field:
            verdict = "DOES NOT GATE — the field it reads does not change its outcome"
            problems += 1
        elif not isolated:
            verdict = f"NOT ISOLATED — also flipped {[g for g in flipped if g != name]}"
            problems += 1
        else:
            verdict = "ok"
        entries.append(
            {
                "gate": name,
                "category": (
                    "degeneracy"
                    if name in gates.DEGENERACY_GATES
                    else "cost"
                    if name in gates.COST_GATES
                    else "performance"
                ),
                "broken_field": sorted(BREAKS[name]),
                "flipped": flipped,
                "reads_its_field": reads_field,
                "isolated": isolated,
                "verdict": verdict,
            }
        )
        marker = " " if verdict == "ok" else "!"
        print(f"{marker} {name:36s} {verdict}")

    payload = {
        "schema_version": "top40-v5-mutation-ledger-v1",
        "gate_count": len(entries),
        "problems": problems,
        "entries": entries,
    }
    destination = Path(arguments.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\n{len(entries) - problems}/{len(entries)} gates demonstrated to gate")
    print(f"wrote {destination}")
    return 0 if problems == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
