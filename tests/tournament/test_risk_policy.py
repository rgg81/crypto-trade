from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_trade.tournament.risk_policy import (
    boundary_risk_decision,
    drawdown_gross_scale,
    risk_policy_from_dict,
    volatility_gross_scale,
)


def _policy() -> dict:
    path = Path(__file__).parents[2] / "tournament/top40-v2/templates/risk-policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_default_policy_is_valid_and_disabled():
    policy = risk_policy_from_dict(_policy())

    assert policy.policy_id == "replace-me"
    assert not policy.enabled
    assert drawdown_gross_scale(policy, 0.75) == 1.0
    assert volatility_gross_scale(policy, 2.0) == 1.0


def test_boundary_policy_combines_brakes_stops_timeouts_and_cooldowns():
    raw = _policy()
    raw["policy_id"] = "defensive-overlay"
    raw["volatility_target"] = {
        "enabled": True,
        "lookback_days": 30,
        "annualized_target": 0.4,
        "minimum_scale": 0.2,
        "maximum_scale": 1.0,
    }
    raw["drawdown_brakes"] = [
        {"drawdown": 0.10, "gross_scale": 0.6},
        {"drawdown": 0.20, "gross_scale": 0.25},
    ]
    raw["position_stop"]["enabled"] = True
    raw["time_stop"]["enabled"] = True
    raw["time_stop"]["maximum_holding_bars"] = 5
    raw["turnover_limit"]["enabled"] = True
    raw["turnover_limit"]["maximum_one_way_turnover"] = 0.4
    policy = risk_policy_from_dict(raw)

    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.22,
        annualized_volatility=0.8,
        position_returns={"A": -0.11, "B": 0.02, "C": 0.01},
        holding_bars={"A": 2, "B": 5, "C": 1},
        cooldown_bars_remaining={"C": 1},
    )

    assert decision.gross_scale == 0.25
    assert decision.stopped_symbols == ("A",)
    assert decision.timed_out_symbols == ("B",)
    assert decision.blocked_symbols == ("A", "B", "C")
    assert decision.maximum_one_way_turnover == 0.4
    assert set(decision.reasons) == {
        "drawdown_brake",
        "volatility_target",
        "position_stop",
        "time_stop",
        "cooldown_or_reentry_block",
    }


def test_risk_policy_rejects_weakening_or_ambiguous_parameters():
    raw = _policy()
    raw["drawdown_brakes"] = [
        {"drawdown": 0.20, "gross_scale": 0.25},
        {"drawdown": 0.10, "gross_scale": 0.50},
    ]
    with pytest.raises(ValueError, match="increase in threshold"):
        risk_policy_from_dict(raw)

    raw = _policy()
    raw["volatility_target"]["maximum_scale"] = 1.1
    with pytest.raises(ValueError, match="scales"):
        risk_policy_from_dict(raw)

    raw = _policy()
    raw["unexpected"] = True
    with pytest.raises(ValueError, match="invalid keys"):
        risk_policy_from_dict(raw)
