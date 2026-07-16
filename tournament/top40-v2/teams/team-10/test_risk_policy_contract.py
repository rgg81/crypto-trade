from __future__ import annotations

import json
from pathlib import Path

TEAM_DIR = Path(__file__).resolve().parent
POLICY_KEYS = {
    "drawdown_brakes",
    "policy_id",
    "position_stop",
    "same_boundary_reentry",
    "schema_version",
    "side_scaling",
    "time_stop",
    "turnover_limit",
    "volatility_target",
}


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((TEAM_DIR / relative_path).read_text(encoding="utf-8"))


def _active_controls(policy: dict[str, object]) -> set[str]:
    active = set()
    if policy["drawdown_brakes"]:
        active.add("drawdown")
    for field in ("position_stop", "time_stop", "turnover_limit", "volatility_target"):
        control = policy[field]
        assert isinstance(control, dict)
        if control["enabled"]:
            active.add(field)
    return active


def test_risk_plan_counts_paired_costs_as_six_material_policies() -> None:
    plan = _load("risk_ablations.json")
    accounting = plan["cost_accounting"]
    assert accounting == {
        "cost_multipliers_per_policy": [1.0, 2.0],
        "material_configuration_count": 6,
        "paired_outputs_in_one_organizer_evaluation": True,
        "prohibited_interpretation": (
            "Do not count base and doubled costs as two policy configurations."
        ),
    }
    policies = plan["policies"]
    assert isinstance(policies, list) and len(policies) == 6
    assert len({entry["policy_id"] for entry in policies}) == 6


def test_each_policy_is_declarative_bounded_and_disables_same_boundary_reentry() -> None:
    plan = _load("risk_ablations.json")
    for entry in plan["policies"]:
        policy = _load(entry["path"])
        assert set(policy) == POLICY_KEYS
        assert policy["schema_version"] == 1
        assert policy["policy_id"] == entry["policy_id"]
        assert policy["same_boundary_reentry"] is False
        assert policy["side_scaling"] == {"long_scale": 1.0, "short_scale": 1.0}
        volatility = policy["volatility_target"]
        assert 0.0 <= volatility["minimum_scale"] <= volatility["maximum_scale"] <= 1.0
        assert volatility["lookback_days"] >= 2
        assert 0.0 < volatility["annualized_target"]
        turnover = policy["turnover_limit"]
        assert 0.0 < turnover["maximum_one_way_turnover"] <= 2.0
        position_stop = policy["position_stop"]
        assert 0.0 < position_stop["loss_fraction"] < 1.0
        assert position_stop["cooldown_bars"] >= 0
        assert all(
            0.0 < brake["drawdown"] < 1.0 and 0.0 <= brake["gross_scale"] <= 1.0
            for brake in policy["drawdown_brakes"]
        )


def test_individual_and_combined_control_matrix_is_exact() -> None:
    plan = _load("risk_ablations.json")
    active = {
        entry["policy_id"]: _active_controls(_load(entry["path"])) for entry in plan["policies"]
    }
    assert active == {
        "team-10-combined": {
            "drawdown",
            "position_stop",
            "turnover_limit",
            "volatility_target",
        },
        "team-10-drawdown-only": {"drawdown"},
        "team-10-no-control": set(),
        "team-10-position-stop-only": {"position_stop"},
        "team-10-turnover-only": {"turnover_limit"},
        "team-10-volatility-only": {"volatility_target"},
    }


def test_execution_contract_is_next_open_and_organizer_owned() -> None:
    contract = _load("risk_ablations.json")["execution_contract"]
    assert contract == {
        "intrabar_fills": False,
        "ordinary_costs": True,
        "same_boundary_reentry": False,
        "shared_participation_capacity": True,
        "stop_confirmation": "closed boundary mark",
        "stop_execution": "next executable open",
    }


def test_organizer_ledgers_remain_empty() -> None:
    assert (TEAM_DIR / "families.jsonl").read_bytes() == b""
    assert (TEAM_DIR / "experiments.jsonl").read_bytes() == b""
