"""Synthetic declarative-risk tests; the organizer evaluator still owns action execution."""

from __future__ import annotations

from pathlib import Path

from crypto_trade.tournament.risk_policy import boundary_risk_decision, load_risk_policy


POLICY_PATH = Path(__file__).with_name("risk_policy.json")
ABLATION_ROOT = Path(__file__).with_name("risk_ablations")


def test_frozen_policy_parses_and_is_enabled() -> None:
    policy = load_risk_policy(POLICY_PATH)
    assert policy.policy_id == "team-05-crtr-conservative-v1"
    assert policy.enabled
    assert not policy.same_boundary_reentry


def test_every_exact_ablation_policy_parses_with_only_declared_controls() -> None:
    none = load_risk_policy(ABLATION_ROOT / "none.json")
    volatility = load_risk_policy(ABLATION_ROOT / "volatility_only.json")
    drawdown = load_risk_policy(ABLATION_ROOT / "drawdown_only.json")
    position = load_risk_policy(ABLATION_ROOT / "position_stop_only.json")
    turnover = load_risk_policy(ABLATION_ROOT / "turnover_only.json")

    assert not none.enabled
    assert volatility.volatility_target.enabled and not volatility.drawdown_brakes
    assert drawdown.drawdown_brakes and not drawdown.volatility_target.enabled
    assert position.position_stop.enabled and not position.turnover_limit.enabled
    assert turnover.turnover_limit.enabled and not turnover.position_stop.enabled


def test_drawdown_and_volatility_take_the_more_conservative_scale() -> None:
    policy = load_risk_policy(POLICY_PATH)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.17,
        annualized_volatility=0.30,
        position_returns={},
        holding_bars={},
        cooldown_bars_remaining={},
    )
    assert decision.gross_scale == 0.50
    assert "drawdown_brake" in decision.reasons
    assert "volatility_target" in decision.reasons
    assert decision.maximum_one_way_turnover == 0.18


def test_close_confirmed_stop_blocks_same_boundary_reentry() -> None:
    policy = load_risk_policy(POLICY_PATH)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.0,
        annualized_volatility=0.10,
        position_returns={"LOSERUSDT": -0.12, "OKUSDT": -0.119},
        holding_bars={"LOSERUSDT": 20, "OKUSDT": 20},
        cooldown_bars_remaining={},
    )
    assert decision.stopped_symbols == ("LOSERUSDT",)
    assert "LOSERUSDT" in decision.blocked_symbols
    assert "OKUSDT" not in decision.blocked_symbols
    assert "position_stop" in decision.reasons
    assert "cooldown_or_reentry_block" in decision.reasons


def test_existing_cooldown_is_deterministically_sorted_and_blocked() -> None:
    policy = load_risk_policy(POLICY_PATH)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.0,
        annualized_volatility=0.10,
        position_returns={},
        holding_bars={},
        cooldown_bars_remaining={"ZUSDT": 1, "AUSDT": 2, "FREEUSDT": 0},
    )
    assert decision.blocked_symbols == ("AUSDT", "ZUSDT")


def test_full_drawdown_brake_requests_zero_gross_without_manufacturing_fill() -> None:
    policy = load_risk_policy(POLICY_PATH)
    decision = boundary_risk_decision(
        policy,
        current_drawdown=0.28,
        annualized_volatility=0.10,
        position_returns={},
        holding_bars={},
        cooldown_bars_remaining={},
    )
    assert decision.gross_scale == 0.0
    assert not hasattr(decision, "fill_price")
