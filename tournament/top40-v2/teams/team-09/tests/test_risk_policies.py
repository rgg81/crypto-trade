from __future__ import annotations

import json
from pathlib import Path

from crypto_trade.tournament.risk_policy import risk_policy_from_dict

TEAM_DIR = Path(__file__).resolve().parents[1]


def _load(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_all_six_policies_pass_the_authoritative_parser() -> None:
    paths = sorted((TEAM_DIR / "risk_policies").glob("*.json"))
    assert len(paths) == 6
    policies = [risk_policy_from_dict(_load(path)) for path in paths]
    assert len({policy.policy_id for policy in policies}) == 6
    assert all(not policy.same_boundary_reentry for policy in policies)


def test_each_single_control_and_combined_policy_are_exact() -> None:
    policies = {
        risk_policy_from_dict(_load(path)).policy_id: risk_policy_from_dict(_load(path))
        for path in sorted((TEAM_DIR / "risk_policies").glob("*.json"))
    }
    assert not policies["team09-risk-none"].enabled
    assert policies["team09-risk-vol"].volatility_target.enabled
    assert policies["team09-risk-drawdown"].drawdown_brakes
    assert policies["team09-risk-stop"].position_stop.enabled
    assert policies["team09-risk-turnover"].turnover_limit.enabled
    combined = policies["team09-risk-combined"]
    assert combined.volatility_target.enabled
    assert combined.drawdown_brakes
    assert combined.position_stop.enabled
    assert combined.turnover_limit.enabled
    assert not combined.time_stop.enabled
    assert combined.side_scaling.long_scale == combined.side_scaling.short_scale == 1.0


def test_canonical_root_policy_is_byte_exact_no_control() -> None:
    assert (TEAM_DIR / "risk_policy.json").read_bytes() == (
        TEAM_DIR / "risk_policies/00-none.json"
    ).read_bytes()


def test_risk_plan_counts_cost_panels_as_paired_outputs() -> None:
    plan = _load(TEAM_DIR / "risk_ablations.json")
    assert plan["policy_count"] == 6
    assert len(plan["policies"]) == 6
    assert plan["threshold_contract_path"] == (
        "qualification_thresholds.json#/core_alpha_activation"
    )
    assert plan["pivot_threshold_contract_path"] == (
        "qualification_thresholds.json#/pivot_02_mechanism_gate"
    )
    assert plan["material_policy_accounting"] == {
        "additional_policy_configurations_after_core": 5,
        "center_no_control_included": True,
        "total_policy_states": 6,
    }
    assert plan["cost_output_contract"] == {
        "base_cost_multiplier": 1.0,
        "double_cost_multiplier": 2.0,
        "material_count_rule": (
            "Each policy is one material configuration whose organizer run emits base and "
            "doubled-cost outputs together. The two cost panels are not separately selected "
            "and do not count as two policy trials."
        ),
        "required_for_every_policy": True,
    }
    assert [item["path"] for item in plan["policies"]] == [
        "risk_policy.json",
        "risk_policies/01-volatility-target.json",
        "risk_policies/02-drawdown-brakes.json",
        "risk_policies/03-position-stop.json",
        "risk_policies/04-turnover-limit.json",
        "risk_policies/05-combined.json",
    ]
    assert plan["core_alpha_activation_gate"] == {
        "applies_to": "team09-drp-pivot02-v1 with root risk_policy.json in its no-control state",
        "base_cost_net_return_strictly_positive": True,
        "base_cost_net_sharpe_strictly_positive": True,
        "both_sleeves_meet_activity_floors": True,
        "combined_chop_attribution_strictly_positive": True,
        "completed_without_insolvency": True,
        "doubled_cost_net_return_strictly_positive": True,
        "doubled_cost_net_sharpe_strictly_positive": True,
        "long_bull_attribution_strictly_positive": True,
        "minimum_positive_folds": 4,
        "required_positive_return_regimes": ["bull", "bear", "chop"],
        "short_bear_attribution_strictly_positive": True,
    }
