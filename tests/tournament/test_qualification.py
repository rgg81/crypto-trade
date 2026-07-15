from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from crypto_trade.tournament.qualification import assess_development, assess_private
from crypto_trade.tournament.top40_v2 import load_config


def _config():
    root = Path(__file__).parents[2]
    return load_config(root / "tournament/top40-v2/config.toml")


def _identity(stage: str) -> dict:
    return {
        "schema_version": 1,
        "stage": stage,
        "team_id": "team-01",
        "candidate_id": "candidate-1",
        "strategy_sha256": "1" * 64,
        "risk_policy_sha256": "2" * 64,
        "config_sha256": "3" * 64,
        "trial_count": 20,
    }


def _passing_development() -> dict:
    return {
        **_identity("development"),
        "aggregate": {
            "net_sharpe": 0.80,
            "annualized_return": 0.10,
            "calmar": 0.50,
            "max_drawdown": 0.20,
            "double_cost_sharpe": 0.40,
            "positive_quarter_fraction": 0.60,
            "trial_adjusted_probability_positive": 0.95,
        },
        "folds": [
            {"fold_id": f"fold-{index}", "net_return": 0.01 if index != 6 else -0.01}
            for index in range(1, 7)
        ],
        "regimes": {
            "bull": {"net_return": 0.10, "net_sharpe": 0.8},
            "bear": {"net_return": 0.05, "net_sharpe": 0.4},
            "chop": {"net_return": 0.03, "net_sharpe": 0.3},
            "stress": {"net_return": -0.01, "net_sharpe": -0.1},
        },
        "roles": {
            "long_bull_net_return": 0.06,
            "short_bear_net_return": 0.04,
            "combined_chop_net_return": 0.03,
        },
        "sleeves": {
            "long": {
                "active_bar_fraction": 0.20,
                "mean_gross_exposure": 0.05,
                "executed_notional_usdt": 50_000,
            },
            "short": {
                "active_bar_fraction": 0.20,
                "mean_gross_exposure": 0.05,
                "executed_notional_usdt": 50_000,
            },
        },
        "stability": {
            "profitable_neighbor_fraction": 0.80,
            "neighbor_median_sharpe": 0.60,
            "maximum_positive_pnl_concentration": 0.30,
        },
    }


def test_complete_development_evidence_passes_every_gate():
    config = _config()
    assessment = assess_development(
        _passing_development(), config.qualification_thresholds, evidence_sha256="a" * 64
    )

    assert assessment.passed
    assert assessment.failed_gate_names == ()
    assert len(assessment.gates) == 25


def test_one_bad_metric_cannot_be_compensated_by_other_results():
    config = _config()
    evidence = deepcopy(_passing_development())
    evidence["aggregate"]["net_sharpe"] = 0.74
    evidence["aggregate"]["calmar"] = 100.0

    assessment = assess_development(
        evidence, config.qualification_thresholds, evidence_sha256="a" * 64
    )

    assert not assessment.passed
    assert assessment.failed_gate_names == ("development.net_sharpe",)


def test_private_feedback_can_hide_every_numeric_observation():
    config = _config()
    evidence = {
        **_identity("private"),
        "aggregate": {
            "net_sharpe": 0.60,
            "annualized_return": 0.05,
            "max_drawdown": 0.20,
            "double_cost_sharpe": 0.10,
            "positive_quarter_fraction": 0.75,
        },
    }
    assessment = assess_private(
        evidence, config.qualification_thresholds, evidence_sha256="b" * 64
    )

    public = assessment.to_dict(include_observations=False)
    assert assessment.passed
    assert all(set(gate) == {"name", "passed"} for gate in public["gates"])
    assert "observed" not in str(public)
