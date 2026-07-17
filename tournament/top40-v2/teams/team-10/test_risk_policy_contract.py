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
        "additional_policy_configurations_after_core": 5,
        "center_no_control_included": True,
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
    assert [entry["path"] for entry in policies] == [
        "risk_policy.json",
        "risk_policies/volatility-only.json",
        "risk_policies/drawdown-only.json",
        "risk_policies/position-stop-only.json",
        "risk_policies/turnover-only.json",
        "risk_policies/combined.json",
    ]
    assert plan["core_alpha_activation_gate"] == {
        "applies_to": "t10-dac-core-v1 pivot-01 with root risk_policy.json in its no-control state",
        "all_team_a5_score_gates_must_pass": True,
        "base_cost_net_return": {"operator": ">", "threshold": 0.0},
        "base_cost_net_sharpe": {"operator": ">=", "threshold": 0.75},
        "combined_chop_attribution": {"operator": ">", "threshold": 0.0},
        "doubled_cost_net_return": {"operator": ">", "threshold": 0.0},
        "doubled_cost_net_sharpe": {"operator": ">=", "threshold": 0.35},
        "long_bull_attribution": {"operator": ">", "threshold": 0.0},
        "minimum_positive_folds": {"operator": ">=", "threshold": 4, "total_folds": 6},
        "official_non_neighbor_gates_must_pass": True,
        "required_positive_return_regimes": {
            "operator": ">",
            "regimes": ["bull", "bear", "chop"],
            "threshold": 0.0,
        },
        "short_bear_attribution": {"operator": ">", "threshold": 0.0},
        "sleeve_activity_thresholds_path": "qualification_thresholds.json#/sleeves",
        "thresholds_path": "qualification_thresholds.json",
    }


def test_root_policy_is_byte_exact_no_control() -> None:
    assert (TEAM_DIR / "risk_policy.json").read_bytes() == (
        TEAM_DIR / "risk_policies/no-control.json"
    ).read_bytes()


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


def test_initial_terminal_ledger_history_is_preserved() -> None:
    families = [
        json.loads(line)
        for line in (TEAM_DIR / "families.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    experiments = [
        json.loads(line)
        for line in (TEAM_DIR / "experiments.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert families[0]["family_id"] == "t10-residual-trend-reversion-ensemble-v1"
    assert [event["event_type"] for event in experiments[:2]] == [
        "trial_registration",
        "trial_result",
    ]
    assert experiments[1]["status"] == "failed"
    assert experiments[1]["failure_reason"] == (
        "ValueError: portfolio insolvent at 2022-05-13 00:00:00+00:00"
    )
    assert experiments[1]["metrics_summary"] == {}
    assert experiments[1]["registration_sha256"] == (
        "2f6625ee5b4ca7e641b9e9b1a6f8ec7068bcc6bc6e9a75a8cc910c2fd8345fa2"
    )
    assert all(event["candidate_id"] == "t10-rtre-core-v1" for event in experiments[:2])


def test_complete_numeric_threshold_binding() -> None:
    thresholds = _load("qualification_thresholds.json")
    assert thresholds["a5_score_diagnostic"] == {
        "complete_manifest_scheduled_score_coverage_required": True,
        "executable_price_column": "open",
        "holding_horizon_hours": 24,
        "independent_semantic_coupling_approval_required": True,
        "minimum_pairs": 240,
        "minimum_positive_fold_pearson_count": 4,
        "pooled_development_pearson": {"operator": ">", "threshold": 0.0},
        "purge_cross_fold_endpoints": True,
        "required_fold_count": 6,
        "return_definition": "simple-executable-open-to-open",
        "schedule_anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "schedule_interval_hours": 24,
        "score_direction": "higher-score-higher-return",
        "statistic_id": "globally-pooled-pearson-v1",
    }
    assert thresholds["development"] == {
        "maximum_drawdown": {"operator": "<=", "threshold": 0.3},
        "minimum_annualized_return": {"operator": ">=", "threshold": 0.0},
        "minimum_calmar": {"operator": ">=", "threshold": 0.4},
        "minimum_double_cost_sharpe": {"operator": ">=", "threshold": 0.35},
        "minimum_net_sharpe": {"operator": ">=", "threshold": 0.75},
        "minimum_positive_folds": {"operator": ">=", "threshold": 4, "total_folds": 6},
        "minimum_positive_quarter_fraction": {"operator": ">=", "threshold": 0.55},
        "minimum_trial_adjusted_probability_positive": {
            "operator": ">=",
            "threshold": 0.9,
        },
    }
    assert thresholds["stability"] == {
        "maximum_positive_pnl_concentration": {"operator": "<=", "threshold": 0.4},
        "minimum_neighbor_median_sharpe": {"operator": ">=", "threshold": 0.5},
        "minimum_profitable_neighbor_fraction": {"operator": ">=", "threshold": 0.7},
    }


def test_neighbor_staging_is_complete_and_noncircular() -> None:
    declaration = _load("parameter_neighborhood.json")
    staging = _load("neighbor_staging_plan.json")
    declared_ids = [neighbor["neighbor_id"] for neighbor in declaration["neighbors"]]
    manifest_ids = [
        neighbor["neighbor_id"]
        for neighbor in _load("parameter_neighborhood_manifest.template.json")["neighbors"]
    ]
    assert len(declared_ids) == 12
    assert len(set(declared_ids)) == 12
    assert manifest_ids == declared_ids
    assert staging["declaration"]["declared_neighbor_count"] == 12
    assert (
        staging["declaration"]["all_neighbor_ids_and_one_axis_values_fixed_before_center_result"]
        is True
    )
    rules = staging["noncircular_rules"]
    assert rules["all_twelve_neighbors_registered_before_first_neighbor_result"] is True
    assert rules["center_cannot_qualify_until_complete_neighbor_aggregation_passes"] is True
    assert rules["neighbor_definition_changes_after_center_result"] is False
    assert rules["neighbor_subset_selection_after_any_neighbor_result"] is False
