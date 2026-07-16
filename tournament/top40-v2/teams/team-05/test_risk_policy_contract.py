"""Synthetic declarative-risk tests; the organizer evaluator still owns action execution."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import candidate_variant

from crypto_trade.tournament.risk_policy import boundary_risk_decision, load_risk_policy

POLICY_PATH = Path(__file__).with_name("risk_policy.json")
ABLATION_ROOT = Path(__file__).with_name("risk_ablations")
COMBINED_PATH = ABLATION_ROOT / "combined.json"


POLICY_CASES = (
    (ABLATION_ROOT / "none.json", "team-05-crtr-none-v1", frozenset()),
    (
        ABLATION_ROOT / "volatility_only.json",
        "team-05-crtr-volatility-only-v1",
        frozenset({"volatility_target"}),
    ),
    (
        ABLATION_ROOT / "drawdown_only.json",
        "team-05-crtr-drawdown-only-v1",
        frozenset({"drawdown_brakes"}),
    ),
    (
        ABLATION_ROOT / "position_stop_only.json",
        "team-05-crtr-position-stop-only-v1",
        frozenset({"position_stop"}),
    ),
    (
        ABLATION_ROOT / "turnover_only.json",
        "team-05-crtr-turnover-only-v1",
        frozenset({"turnover_limit"}),
    ),
    (
        COMBINED_PATH,
        "team-05-crtr-conservative-v1",
        frozenset(
            {
                "volatility_target",
                "drawdown_brakes",
                "position_stop",
                "turnover_limit",
            }
        ),
    ),
)


def test_root_policy_is_the_exact_active_candidate_template() -> None:
    template_path = POLICY_PATH.parent / candidate_variant.ACTIVE_RISK_POLICY_TEMPLATE
    assert POLICY_PATH.read_bytes() == template_path.read_bytes()


def _exact_expected_policy(
    policy_id: str,
    enabled_controls: frozenset[str],
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "policy_id": policy_id,
        "same_boundary_reentry": False,
        "volatility_target": {
            "enabled": "volatility_target" in enabled_controls,
            "lookback_days": 30,
            "annualized_target": 0.18,
            "minimum_scale": 0.35,
            "maximum_scale": 1.0,
        },
        "drawdown_brakes": (
            (
                {"drawdown": 0.10, "gross_scale": 0.75},
                {"drawdown": 0.16, "gross_scale": 0.50},
                {"drawdown": 0.22, "gross_scale": 0.25},
                {"drawdown": 0.28, "gross_scale": 0.0},
            )
            if "drawdown_brakes" in enabled_controls
            else ()
        ),
        "position_stop": {
            "enabled": "position_stop" in enabled_controls,
            "loss_fraction": 0.12,
            "cooldown_bars": 6,
        },
        "time_stop": {
            "enabled": False,
            "maximum_holding_bars": 90,
            "cooldown_bars": 3,
        },
        "turnover_limit": {
            "enabled": "turnover_limit" in enabled_controls,
            "maximum_one_way_turnover": 0.18,
        },
        "side_scaling": {
            "long_scale": 1.0,
            "short_scale": 1.0,
        },
    }


def test_every_policy_has_exhaustive_exact_control_and_setting_declaration() -> None:
    for path, policy_id, enabled_controls in POLICY_CASES:
        policy = load_risk_policy(path)
        assert dataclasses.asdict(policy) == _exact_expected_policy(
            policy_id,
            enabled_controls,
        )
        assert policy.enabled is bool(enabled_controls)


def test_drawdown_and_volatility_take_the_more_conservative_scale() -> None:
    policy = load_risk_policy(COMBINED_PATH)
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
    policy = load_risk_policy(COMBINED_PATH)
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
    policy = load_risk_policy(COMBINED_PATH)
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
    policy = load_risk_policy(COMBINED_PATH)
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
