from __future__ import annotations

from pathlib import Path

from crypto_trade.tournament.risk_policy import boundary_risk_decision, load_risk_policy

TEAM_DIR = Path(__file__).resolve().parent


def test_every_declared_risk_policy_parses_and_disables_same_boundary_reentry() -> None:
    paths = [TEAM_DIR / "risk_policy.json", *sorted((TEAM_DIR / "risk_policies").glob("*.json"))]
    assert len(paths) == 6
    for path in paths:
        policy = load_risk_policy(path)
        assert policy.schema_version == 1
        assert policy.same_boundary_reentry is False


def test_combined_policy_has_only_the_declared_controls() -> None:
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
    assert policy.volatility_target.enabled
    assert policy.drawdown_brakes
    assert policy.position_stop.enabled
    assert not policy.time_stop.enabled
    assert policy.turnover_limit.enabled
    assert policy.side_scaling.long_scale == 1.0
    assert policy.side_scaling.short_scale == 1.0


def test_boundary_decision_stops_blocks_scales_and_limits_turnover() -> None:
    policy = load_risk_policy(TEAM_DIR / "risk_policy.json")
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
    policy = load_risk_policy(TEAM_DIR / "risk_policies" / "no-control.json")
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
