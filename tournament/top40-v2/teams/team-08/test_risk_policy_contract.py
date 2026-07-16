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


def test_combined_policy_parses_and_enables_declared_controls() -> None:
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
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
    combined = json.loads((TEAM_DIR / "risk_policy.json").read_text(encoding="utf-8"))
    assert document["policies"][-1]["policy"] == combined


def test_material_configuration_accounting_counts_combined_policy_once() -> None:
    risk = json.loads((TEAM_DIR / "risk_ablations.json").read_text(encoding="utf-8"))
    neighborhood = json.loads(
        (TEAM_DIR / "parameter_neighborhood.json").read_text(encoding="utf-8")
    )
    mechanism = json.loads((TEAM_DIR / "ablations.json").read_text(encoding="utf-8"))
    accounting = risk["material_configuration_accounting"]
    assert len(risk["policies"]) == accounting["matrix_policy_count"] == 7
    assert accounting["additional_policy_configurations"] == 6
    center_policy_id = "team-08-vdr-combined"
    assert sum(item["policy"]["policy_id"] == center_policy_id for item in risk["policies"]) == 1
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
    assert expected == accounting["total_initial_family_configurations"] == 21


@pytest.mark.parametrize(
    ("drawdown", "expected"),
    [(0.0, 1.0), (0.099, 1.0), (0.1, 0.75), (0.18, 0.45), (0.26, 0.0)],
)
def test_drawdown_brakes_are_graduated(drawdown: float, expected: float) -> None:
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
    assert drawdown_gross_scale(policy, drawdown) == expected


def test_volatility_target_never_leverages_and_fails_conservatively_without_history() -> None:
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
    assert volatility_gross_scale(policy, None) == 0.25
    assert volatility_gross_scale(policy, 0.20) == 1.0
    assert volatility_gross_scale(policy, 0.70) == pytest.approx(0.5)
    assert volatility_gross_scale(policy, 2.0) == 0.25


def test_stops_timeouts_cooldowns_and_same_boundary_reentry_are_deterministic() -> None:
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
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
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
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
