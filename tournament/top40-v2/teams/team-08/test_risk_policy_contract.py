from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_trade.tournament.risk_policy import (
    boundary_risk_decision,
    drawdown_gross_scale,
    load_risk_policy,
    risk_policy_from_dict,
    volatility_gross_scale,
)

TEAM_DIR = Path(__file__).resolve().parent
ROOT_POLICY = TEAM_DIR / "risk_policy.json"
NO_CONTROL_TEMPLATE = TEAM_DIR / "risk_policies" / "no-control.json"
COMBINED_TEMPLATE = TEAM_DIR / "risk_policies" / "combined.json"


def test_root_policy_is_byte_exact_no_control() -> None:
    assert ROOT_POLICY.read_bytes() == NO_CONTROL_TEMPLATE.read_bytes()
    policy = load_risk_policy(ROOT_POLICY)
    assert not policy.enabled
    assert policy.policy_id == "team-08-risk-none"


def test_risk_plan_requires_complete_no_control_gate_before_controls() -> None:
    plan = json.loads((TEAM_DIR / "risk_ablations.json").read_text(encoding="utf-8"))
    assert plan["policies"][0]["template_path"] == "risk_policies/no-control.json"
    assert plan["policies"][-1]["template_path"] == "risk_policies/combined.json"
    assert plan["core_alpha_activation_gate"] == {
        "annualized_return_strictly_positive": True,
        "applies_to": (
            "t08-volatility-scaled-rank-persistence-v1-base with root risk_policy.json "
            "in its exact no-control state"
        ),
        "complete_a5_score_coverage": True,
        "combined_chop_attribution_strictly_positive": True,
        "doubled_cost_net_return_strictly_positive": True,
        "long_bull_attribution_strictly_positive": True,
        "maximum_drawdown": 0.3,
        "maximum_positive_pnl_concentration": 0.4,
        "minimum_calmar": 0.4,
        "minimum_double_cost_net_sharpe": 0.35,
        "minimum_fold_score_ic_positive": 4,
        "minimum_neighbor_median_sharpe": 0.5,
        "minimum_net_sharpe": 0.75,
        "minimum_positive_folds": 4,
        "minimum_positive_quarter_fraction": 0.55,
        "minimum_positive_regime_sharpes": 3,
        "minimum_profitable_neighbor_fraction": 0.7,
        "minimum_trial_adjusted_probability_positive": 0.9,
        "minimum_worst_regime_sharpe": -0.25,
        "pooled_score_ic_strictly_positive": True,
        "required_positive_sharpe_regimes": ["bull", "bear", "chop"],
        "required_positive_return_regimes": ["bull", "bear", "chop"],
        "short_bear_attribution_strictly_positive": True,
        "sleeve_minima": {
            "minimum_mean_side_exposure": 0.01,
            "minimum_side_active_bar_fraction": 0.1,
            "minimum_side_executed_notional_usdt": 1000.0,
            "minimum_side_exposure": 0.01,
        },
    }


def test_combined_template_parses_and_enables_declared_controls() -> None:
    policy = load_risk_policy(COMBINED_TEMPLATE)
    assert policy.enabled
    assert policy.policy_id == "team-08-vdr-combined"
    assert policy.volatility_target.enabled
    assert policy.position_stop.enabled
    assert policy.time_stop.enabled
    assert policy.turnover_limit.enabled
    assert policy.same_boundary_reentry is False


def test_every_risk_ablation_is_a_complete_strict_policy() -> None:
    document = json.loads((TEAM_DIR / "risk_ablations.json").read_text(encoding="utf-8"))
    parsed = [risk_policy_from_dict(item["policy"]) for item in document["policies"]]
    assert len(parsed) == 7
    assert len({policy.policy_id for policy in parsed}) == len(parsed)
    assert document["cost_multipliers_for_every_policy"] == [1.0, 2.0]
    assert not parsed[0].enabled
    assert parsed[-1].policy_id == "team-08-vdr-combined"
    for item in document["policies"]:
        template = json.loads((TEAM_DIR / item["template_path"]).read_text(encoding="utf-8"))
        assert item["policy"] == template
    assert document["policies"][0]["policy"] == json.loads(
        ROOT_POLICY.read_text(encoding="utf-8")
    )


def test_material_configuration_accounting_counts_no_control_core_once() -> None:
    risk = json.loads((TEAM_DIR / "risk_ablations.json").read_text(encoding="utf-8"))
    neighborhood = json.loads(
        (TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    mechanism = json.loads((TEAM_DIR / "ablations.json").read_text(encoding="utf-8"))
    accounting = risk["material_configuration_accounting"]
    assert len(risk["policies"]) == accounting["matrix_policy_count"] == 7
    assert accounting["additional_policy_configurations"] == 6
    assert accounting["center_candidate_uses_no_control_policy"] is True
    center_policy_id = "team-08-risk-none"
    assert (
        sum(item["policy"]["policy_id"] == center_policy_id for item in risk["policies"])
        == 1
    )
    assert (
        sum(item["policy"]["policy_id"] != center_policy_id for item in risk["policies"])
        == accounting["additional_policy_configurations"]
    )
    expected = (
        1
        + len(neighborhood["neighbors"])
        + len(mechanism["mechanism_ablations"])
        + accounting["additional_policy_configurations"]
        + 1
    )
    assert expected == accounting["total_initial_family_configurations"] == 22


@pytest.mark.parametrize(
    ("drawdown", "expected"),
    [(0.0, 1.0), (0.099, 1.0), (0.1, 0.75), (0.18, 0.45), (0.26, 0.0)],
)
def test_drawdown_brakes_are_graduated(drawdown: float, expected: float) -> None:
    policy = load_risk_policy(COMBINED_TEMPLATE)
    assert drawdown_gross_scale(policy, drawdown) == expected


def test_volatility_target_never_leverages_and_fails_conservatively_without_history() -> None:
    policy = load_risk_policy(COMBINED_TEMPLATE)
    assert volatility_gross_scale(policy, None) == 0.25
    assert volatility_gross_scale(policy, 0.20) == 1.0
    assert volatility_gross_scale(policy, 0.70) == pytest.approx(0.5)
    assert volatility_gross_scale(policy, 2.0) == 0.25


def test_stops_timeouts_cooldowns_and_same_boundary_reentry_are_deterministic() -> None:
    policy = load_risk_policy(COMBINED_TEMPLATE)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.19,
        annualized_volatility=0.70,
        position_returns={"BTCUSDT": -0.08, "ETHUSDT": 0.01},
        holding_bars={"BTCUSDT": 2, "ETHUSDT": 18},
        cooldown_bars_remaining={"SOLUSDT": 2},
    )
    assert decision.gross_scale == 0.45
    assert decision.stopped_symbols == ("BTCUSDT",)
    assert decision.timed_out_symbols == ("ETHUSDT",)
    assert decision.blocked_symbols == ("BTCUSDT", "ETHUSDT", "SOLUSDT")
    assert decision.maximum_one_way_turnover == 0.45
    assert decision.reasons == (
        "drawdown_brake",
        "volatility_target",
        "position_stop",
        "time_stop",
        "cooldown_or_reentry_block",
    )


def test_boundary_decision_is_instruction_only_and_contains_no_fill_price() -> None:
    policy = load_risk_policy(COMBINED_TEMPLATE)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.0,
        annualized_volatility=0.20,
        position_returns={},
        holding_bars={},
        cooldown_bars_remaining={},
    )
    assert not hasattr(decision, "fill_price")
    assert not hasattr(decision, "pnl")
    assert decision.gross_scale == 1.0
