from __future__ import annotations

import json
from pathlib import Path

from crypto_trade.tournament.risk_policy import boundary_risk_decision, load_risk_policy

TEAM_DIR = Path(__file__).resolve().parent
NO_CONTROL_TEMPLATE = TEAM_DIR / "risk_policies" / "no-control.json"
COMBINED_TEMPLATE = TEAM_DIR / "risk_policies" / "combined.json"


def test_risk_plan_starts_with_root_no_control_and_defers_combined() -> None:
    plan = json.loads((TEAM_DIR / "risk_ablations.json").read_text(encoding="utf-8"))
    assert plan["policies"][0] == "risk_policy.json"
    assert plan["policies"][-1] == "risk_policies/combined.json"
    assert plan["core_alpha_activation_gate"] == {
        "applies_to": (
            "team07-shock-diffusion-center-v1 with root risk_policy.json "
            "in its no-control state"
        ),
        "base_cost_net_return_strictly_positive": True,
        "base_cost_net_sharpe_strictly_positive": True,
        "both_sleeves_meet_activity_floors": True,
        "combined_chop_attribution_strictly_positive": True,
        "doubled_cost_net_return_strictly_positive": True,
        "doubled_cost_net_sharpe_strictly_positive": True,
        "long_bull_attribution_strictly_positive": True,
        "minimum_positive_folds": 4,
        "required_positive_return_regimes": ["bull", "bear", "chop"],
        "short_bear_attribution_strictly_positive": True,
    }


def test_every_declared_risk_policy_parses_and_disables_same_boundary_reentry() -> None:
    paths = [
        TEAM_DIR / "risk_policy.json",
        TEAM_DIR / "risk_policies" / "volatility-only.json",
        TEAM_DIR / "risk_policies" / "drawdown-only.json",
        TEAM_DIR / "risk_policies" / "position-stop-only.json",
        TEAM_DIR / "risk_policies" / "turnover-only.json",
        COMBINED_TEMPLATE,
    ]
    assert len(paths) == 6
    for path in paths:
        policy = load_risk_policy(path)
        assert policy.schema_version == 1
        assert policy.same_boundary_reentry is False


def test_root_policy_is_byte_exact_no_control() -> None:
    assert (TEAM_DIR / "risk_policy.json").read_bytes() == NO_CONTROL_TEMPLATE.read_bytes()
    assert not load_risk_policy(TEAM_DIR / "risk_policy.json").enabled


def test_combined_template_has_only_the_declared_controls() -> None:
    policy = load_risk_policy(COMBINED_TEMPLATE)
    assert policy.volatility_target.enabled
    assert policy.drawdown_brakes
    assert policy.position_stop.enabled
    assert not policy.time_stop.enabled
    assert policy.turnover_limit.enabled
    assert policy.side_scaling.long_scale == 1.0
    assert policy.side_scaling.short_scale == 1.0


def test_boundary_decision_stops_blocks_scales_and_limits_turnover() -> None:
    policy = load_risk_policy(COMBINED_TEMPLATE)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.20,
        annualized_volatility=0.70,
        position_returns={"COINUSDT": -0.13},
        holding_bars={"COINUSDT": 5},
        cooldown_bars_remaining={},
    )
    assert decision.gross_scale == 0.5
    assert decision.stopped_symbols == ("COINUSDT",)
    assert decision.timed_out_symbols == ()
    assert decision.blocked_symbols == ("COINUSDT",)
    assert decision.maximum_one_way_turnover == 0.35
    assert "drawdown_brake" in decision.reasons
    assert "volatility_target" in decision.reasons
    assert "position_stop" in decision.reasons
    assert "cooldown_or_reentry_block" in decision.reasons


def test_no_control_policy_is_inert() -> None:
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.30,
        annualized_volatility=1.5,
        position_returns={"COINUSDT": -0.50},
        holding_bars={"COINUSDT": 100},
        cooldown_bars_remaining={},
    )
    assert decision.gross_scale == 1.0
    assert decision.stopped_symbols == ()
    assert decision.timed_out_symbols == ()
    assert decision.blocked_symbols == ()
    assert decision.maximum_one_way_turnover is None
