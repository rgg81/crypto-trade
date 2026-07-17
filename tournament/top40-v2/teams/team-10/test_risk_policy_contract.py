from __future__ import annotations

import hashlib
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


def _sha256(relative_path: str) -> str:
    return hashlib.sha256((TEAM_DIR / relative_path).read_bytes()).hexdigest()


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


def test_final_risk_plan_has_exactly_one_no_control_policy() -> None:
    plan = _load("risk_ablations.json")
    assert plan["status"] == "final_pivot_controls_forbidden"
    assert plan["cost_accounting"] == {
        "additional_policy_configurations_after_core": 0,
        "center_no_control_included": True,
        "cost_multipliers_per_policy": [1.0, 2.0],
        "material_configuration_count": 1,
        "paired_outputs_in_one_organizer_evaluation": True,
        "prohibited_interpretation": (
            "Do not count base and doubled costs as two policy configurations."
        ),
    }
    assert plan["policies"] == [{"path": "risk_policy.json", "policy_id": "team-10-no-control"}]
    assert set(plan["forbidden_policy_paths_retained_as_historical_files_only"]) == {
        "risk_policies/volatility-only.json",
        "risk_policies/drawdown-only.json",
        "risk_policies/position-stop-only.json",
        "risk_policies/turnover-only.json",
        "risk_policies/combined.json",
    }
    gate = plan["core_alpha_gate"]
    assert gate["applies_to"] == (
        "t10-fpu-core-v1 final pivot-02 with root risk_policy.json in its no-control state"
    )
    assert gate["failure_action"] == "dnf"
    assert gate["base_cost_net_return"] == {"operator": ">", "threshold": 0.0}
    assert gate["base_cost_net_sharpe"] == {"operator": ">=", "threshold": 0.75}
    assert gate["doubled_cost_net_return"] == {"operator": ">", "threshold": 0.0}
    assert gate["doubled_cost_net_sharpe"] == {"operator": ">=", "threshold": 0.35}


def test_root_policy_is_byte_exact_and_contains_no_active_control() -> None:
    assert (TEAM_DIR / "risk_policy.json").read_bytes() == (
        TEAM_DIR / "risk_policies/no-control.json"
    ).read_bytes()
    policy = _load("risk_policy.json")
    assert set(policy) == POLICY_KEYS
    assert policy["policy_id"] == "team-10-no-control"
    assert policy["same_boundary_reentry"] is False
    assert policy["side_scaling"] == {"long_scale": 1.0, "short_scale": 1.0}
    assert _active_controls(policy) == set()


def test_historical_ledgers_and_both_terminal_results_are_preserved() -> None:
    families = [
        json.loads(line)
        for line in (TEAM_DIR / "families.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    experiments = [
        json.loads(line)
        for line in (TEAM_DIR / "experiments.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert [family["family_id"] for family in families[:2]] == [
        "t10-residual-trend-reversion-ensemble-v1",
        "t10-defensive-anchor-convergence-v1",
    ]
    assert [event["event_type"] for event in experiments[:4]] == [
        "trial_registration",
        "trial_result",
        "trial_registration",
        "trial_result",
    ]
    assert [event["candidate_id"] for event in experiments[:4]] == [
        "t10-rtre-core-v1",
        "t10-rtre-core-v1",
        "t10-dac-core-v1",
        "t10-dac-core-v1",
    ]

    initial = experiments[1]
    assert initial["status"] == "failed"
    assert initial["failure_reason"] == (
        "ValueError: portfolio insolvent at 2022-05-13 00:00:00+00:00"
    )
    assert initial["metrics_summary"] == {}
    assert initial["registration_sha256"] == (
        "2f6625ee5b4ca7e641b9e9b1a6f8ec7068bcc6bc6e9a75a8cc910c2fd8345fa2"
    )

    pivot = experiments[3]
    assert pivot["status"] == "completed"
    assert pivot["failure_reason"] is None
    assert pivot["registration_sha256"] == (
        "1261660821ba905a2c52d4fc6086bba3918a18480966973f0fb85c5b5b554ea6"
    )
    metrics = pivot["metrics_summary"]
    assert metrics["source_bundle_sha256"] == (
        "ee3cac3c14ea028b11198cc1532b7fc50bfb98fcdc924882e9bc1d3e62888183"
    )
    assert metrics["strategy_sha256"] == (
        "d5e09cdb795955bcac87f03b8333092a2d7ba481642d9038c09ff0271b70bf7a"
    )
    assert metrics["trade_count"] == 9581
    assert metrics["double_cost_sharpe"] == -2.436836526128816
    assert metrics["regime_sharpe"] == {
        "bear": -2.200607191286561,
        "bull": -1.5124282333375314,
        "chop": -3.0617769845946468,
        "stress": -1.5413188398402713,
    }
    assert metrics["scored_window"]["metrics"] == {
        "annualized_return": -0.09328445205038527,
        "calmar": -0.30631265956122306,
        "max_drawdown": 0.3045399827222629,
        "net_sharpe": -1.86846407399797,
        "net_sortino": -2.396098794518946,
        "positive_quarter_fraction": 0.14285714285714285,
    }


def test_completed_score_artifacts_remain_separate_from_new_templates() -> None:
    expected_hashes = {
        "score-adapters/t10-rtre-core-v1.json": (
            "0089f98191fd8764a86d99418d33382def19808fa2433832394f437aa606ff97"
        ),
        "score-adapters/t10-rtre-core-v1.executable-source-manifest.json": (
            "6d4d9d0a6f62baac0a078ecc732bc03966c07f4df19cea9e5aecc6ecc67eec24"
        ),
        "score-adapters/t10-rtre-core-v1.semantic-coupling-review.json": (
            "6a283dc87da516aa520309ba0f5672d3309906596abc20367de33e6812d5f617"
        ),
        "score-adapters/t10-dac-core-v1.json": (
            "700e9885c4195e3fd19dcb398dd9e8bae50bb3692f27f9cbe4b86d28fca7f30f"
        ),
        "score-adapters/t10-dac-core-v1.executable-source-manifest.json": (
            "362836527c5f4e59c17bbd2e26cf44cbbc438ca764172d9084d547a8c7636f64"
        ),
        "score-adapters/t10-dac-core-v1.semantic-coupling-review.json": (
            "59b0c7030e0dc0614aa3a84f302fa732cd48101cfd2674f651e509e58bc2e4cf"
        ),
    }
    assert {path: _sha256(path) for path in expected_hashes} == expected_hashes
    assert (
        TEAM_DIR / "score-adapters/t10-fpu-core-v1.score-adapter-manifest.template.json"
    ).is_file()
    assert (
        TEAM_DIR / "score-adapters/t10-fpu-core-v1.executable-source-manifest.template.json"
    ).is_file()
    assert (TEAM_DIR / "score-adapters/t10-fpu-core-v1.semantic-review.template.json").is_file()


def test_complete_numeric_threshold_binding_and_final_disposition() -> None:
    thresholds = _load("qualification_thresholds.json")
    assert thresholds["a5_score_diagnostic"] == {
        "complete_manifest_scheduled_score_coverage_required": True,
        "executable_price_column": "open",
        "holding_horizon_hours": 168,
        "independent_semantic_coupling_approval_required": True,
        "minimum_pairs": 240,
        "minimum_positive_fold_pearson_count": 4,
        "pooled_development_pearson": {"operator": ">", "threshold": 0.0},
        "purge_cross_fold_endpoints": True,
        "required_fold_count": 6,
        "return_definition": "simple-executable-open-to-open",
        "schedule_anchor_timestamp_utc": "1970-01-01T00:00:00Z",
        "schedule_interval_hours": 168,
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
    assert thresholds["final_pivot_disposition"] == {
        "all_gates_noncompensatory": True,
        "controls_permitted": False,
        "core_failure_action": "dnf",
        "neighbor_runs_permitted": False,
        "qualification_claim_without_official_stability_evidence": False,
        "stability_thresholds_waived": False,
    }


def test_final_pivot_has_no_ablation_or_neighbor_escape_path() -> None:
    ablations = _load("ablations.json")
    neighborhood = _load("parameter_neighborhood.json")
    manifest = _load("parameter_neighborhood_manifest.template.json")
    staging = _load("neighbor_staging_plan.json")
    assert ablations["ablations"] == []
    assert ablations["status"] == "final_pivot_ablations_forbidden"
    assert neighborhood["neighbors"] == []
    assert neighborhood["status"] == "final_pivot_neighbors_forbidden"
    assert neighborhood["rules"] == {
        "center_failure_action": "dnf",
        "neighbor_definition_permitted": False,
        "neighbor_registration_permitted": False,
        "neighbor_result_permitted": False,
        "official_stability_thresholds_waived": False,
        "qualification_without_official_stability_evidence": False,
    }
    assert manifest["neighbors"] == []
    assert manifest["evidence_status"] == "not-authorized"
    assert staging["stages"] == []
    assert staging["noncircular_rules"]["neighbor_runs_authorized"] is False
    assert staging["noncircular_rules"]["center_failure_action"] == "dnf"


def test_pure_crypto_authority_is_explicit_and_has_no_local_classifier() -> None:
    frozen = _load("frozen_config.json")
    authority = _load("a7_execution_authority.json")
    amendment = frozen["amendment_0006"]
    assert amendment["violations"] == 0
    assert "native crypto" in amendment["asset_scope"]
    assert "Stablecoin bases" in amendment["asset_scope"]
    assert "tokenized or synthetic TradFi" in amendment["asset_scope"]
    assert "commodities" in amendment["asset_scope"]
    assert "metals" in amendment["asset_scope"]
    assert "indexes" in amendment["asset_scope"]
    assert "ticker" in amendment["classifier_rule"]
    pure_crypto = authority["pure_crypto_report"]
    assert pure_crypto["violations"] == 0
    assert "tokenized or synthetic TradFi" in pure_crypto["classification_scope"]
    assert "commodities" in pure_crypto["classification_scope"]
    assert pure_crypto["ticker_heuristics_permitted"] is False


def test_a7_execution_authority_and_a5_identity_are_frozen() -> None:
    authority = _load("a7_execution_authority.json")
    assert authority["candidate_id"] == "t10-fpu-core-v1"
    assert authority["family_id"] == "t10-funding-pressure-unwind-v1"
    assert authority["active_entrypoint"] == {
        "path": "scripts/top40_v2_tournament_runtime_preload_v7.py",
        "sha256": "8a4ada10176d2606df3f358fc188e21b45153ad9a7270f36908736f03322a3a9",
    }
    assert authority["integration_freeze"]["sha256"] == (
        "6f77a146e7b414eabd20c5cc9321a95493bb98116dde07ef79d9eb009b6a6f51"
    )
    score = authority["operative_a5_score_contract"]
    assert score["hook"] == "strategy.score_boundary"
    assert score["schedule_interval_hours"] == 168
    assert score["holding_horizon_hours"] == 168
    assert score["minimum_pairs"] == 240
