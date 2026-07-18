"""Exact no-control risk-policy contract for Team05 UDCC pivot-01."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import candidate_variant

from crypto_trade.tournament.risk_policy import boundary_risk_decision, load_risk_policy

TEAM_ROOT = Path(__file__).resolve().parent
POLICY_PATH = TEAM_ROOT / "risk_policy.json"


def test_root_policy_is_byte_identical_to_active_pivot_template() -> None:
    template = TEAM_ROOT / candidate_variant.ACTIVE_RISK_POLICY_TEMPLATE
    assert POLICY_PATH.read_bytes() == template.read_bytes()


def test_udcc_policy_has_no_enabled_control() -> None:
    policy = load_risk_policy(POLICY_PATH)
    assert dataclasses.asdict(policy) == {
        "schema_version": 1,
        "policy_id": "team-05-udcc-none-v1",
        "same_boundary_reentry": False,
        "volatility_target": {
            "enabled": False,
            "lookback_days": 30,
            "annualized_target": 0.18,
            "minimum_scale": 0.35,
            "maximum_scale": 1.0,
        },
        "drawdown_brakes": (),
        "position_stop": {
            "enabled": False,
            "loss_fraction": 0.12,
            "cooldown_bars": 6,
        },
        "time_stop": {
            "enabled": False,
            "maximum_holding_bars": 90,
            "cooldown_bars": 3,
        },
        "turnover_limit": {
            "enabled": False,
            "maximum_one_way_turnover": 0.18,
        },
        "side_scaling": {"long_scale": 1.0, "short_scale": 1.0},
    }
    assert policy.enabled is False


def test_no_control_changes_a_boundary_decision() -> None:
    policy = load_risk_policy(POLICY_PATH)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.80,
        annualized_volatility=5.0,
        position_returns={"LOSERUSDT": -0.90},
        holding_bars={"LOSERUSDT": 10_000},
        cooldown_bars_remaining={},
    )
    assert decision.gross_scale == 1.0
    assert decision.maximum_one_way_turnover is None
    assert decision.stopped_symbols == ()
    assert decision.blocked_symbols == ()
    assert decision.reasons == ()
