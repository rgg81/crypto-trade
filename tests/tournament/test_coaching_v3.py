from __future__ import annotations

import copy
import hashlib
import json

import pytest

from crypto_trade.tournament.coaching_v3 import (
    build_training_metric_packet,
    canonical_packet_bytes,
    packet_sha256,
)
from crypto_trade.tournament.qualification_v3 import CandidateIdentity
from crypto_trade.tournament.runner_v3 import (
    EvaluationWindow,
    TeamWindowRunResult,
    WindowMetrics,
)


ARTIFACT_NAMES = (
    "targets",
    "events",
    "positions",
    "evaluator_returns",
    "double_cost_evaluator_returns",
    "daily_returns",
    "double_cost_daily_returns",
    "trades",
)


def _identity(**changes: str) -> CandidateIdentity:
    fields = {
        "team_id": "team-01",
        "candidate_id": "team-01-candidate-001",
        "source_bundle_sha256": "a" * 64,
        "strategy_sha256": "b" * 64,
        "dependency_lock_sha256": "c" * 64,
        "config_sha256": "d" * 64,
        "risk_policy_sha256": "e" * 64,
        "data_authority_sha256": "f" * 64,
        "evaluator_sha256": "1" * 64,
    }
    fields.update(changes)
    return CandidateIdentity(**fields)


def _organizer_mapping(**changes: object) -> dict[str, object]:
    output_dir = "reports-top40-v3/labs/team-01/run-0001"
    artifacts = {
        name: f"{output_dir}/{name}.artifact" for name in ARTIFACT_NAMES
    }
    values: dict[str, object] = {
        "stage": "train",
        "team_id": "team-01",
        "entrypoint": "tournament/top40-v3/teams/team-01/strategy.py",
        "seeds": [20260718],
        "data_manifest_sha256": "f" * 64,
        "config_sha256": "d" * 64,
        "strategy_sha256": "b" * 64,
        "risk_policy_sha256": "e" * 64,
        "source_bundle_sha256": "a" * 64,
        "dependency_lock_sha256": "c" * 64,
        "evaluator_sha256": "1" * 64,
        "pure_crypto_policy_sha256": "2" * 64,
        "pure_crypto_report_sha256": "3" * 64,
        "output_dir": output_dir,
        "scored_window": {
            "start": "2020-02-03",
            "end": "2022-06-30",
            "metrics": {
                "net_sharpe": 1.10,
                "net_sortino": 1.40,
                "calmar": 1.20,
                "annualized_return": 0.18,
                "max_drawdown": 0.18,
                "positive_quarter_fraction": 0.75,
            },
        },
        "double_cost_sharpe": 0.65,
        "regime_sharpe": {
            "bull": 0.80,
            "bear": 0.20,
            "chop": 0.35,
            "stress": -0.10,
        },
        "confidence_intervals": {
            "net_sharpe_95": [0.70, 1.40],
            "double_cost_sharpe_95": [0.30, 0.90],
        },
        "artifacts": artifacts,
        "artifact_sha256": {
            name: format(index + 4, "x")[-1] * 64
            for index, name in enumerate(ARTIFACT_NAMES)
        },
        "artifact_sizes": {
            name: 1_000 + index for index, name in enumerate(ARTIFACT_NAMES)
        },
        "decision_count": 2_600,
        "event_count": 4_000,
        "trade_count": 1_500,
    }
    values.update(changes)
    return values


def _typed_result(raw: dict[str, object]) -> TeamWindowRunResult:
    scored = raw["scored_window"]
    confidence = raw["confidence_intervals"]
    return TeamWindowRunResult(
        stage=raw["stage"],
        team_id=raw["team_id"],
        entrypoint=raw["entrypoint"],
        seed=raw["seeds"][0],
        data_manifest_sha256=raw["data_manifest_sha256"],
        config_sha256=raw["config_sha256"],
        strategy_sha256=raw["strategy_sha256"],
        risk_policy_sha256=raw["risk_policy_sha256"],
        source_bundle_sha256=raw["source_bundle_sha256"],
        dependency_lock_sha256=raw["dependency_lock_sha256"],
        evaluator_sha256=raw["evaluator_sha256"],
        pure_crypto_policy_sha256=raw["pure_crypto_policy_sha256"],
        pure_crypto_report_sha256=raw["pure_crypto_report_sha256"],
        output_dir=raw["output_dir"],
        artifacts=raw["artifacts"],
        artifact_sha256=raw["artifact_sha256"],
        artifact_sizes=raw["artifact_sizes"],
        scored_window=EvaluationWindow(
            start=scored["start"],
            end=scored["end"],
            metrics=WindowMetrics(**scored["metrics"]),
        ),
        double_cost_sharpe=raw["double_cost_sharpe"],
        regime_sharpe=raw["regime_sharpe"],
        net_sharpe_confidence_interval=tuple(confidence["net_sharpe_95"]),
        double_cost_sharpe_confidence_interval=tuple(
            confidence["double_cost_sharpe_95"]
        ),
        decision_count=raw["decision_count"],
        event_count=raw["event_count"],
        trade_count=raw["trade_count"],
    )


def _set_window_metrics(raw: dict[str, object], **changes: float) -> None:
    raw["scored_window"]["metrics"].update(changes)


def test_v2_calibrated_train_result_is_green_but_never_a_nomination() -> None:
    identity = _identity()
    raw = _organizer_mapping()
    from_mapping = build_training_metric_packet(raw, identity)
    from_runner_type = build_training_metric_packet(_typed_result(raw), identity)

    assert from_mapping == from_runner_type
    assessment = from_mapping["training_assessment"]
    assert assessment["status"] == "GREEN"
    assert assessment["public_core_is_train_target_only"] is True
    assert assessment["public_core_train_target_passed"] is True
    assert assessment["largest_open_gaps"] == []
    assert assessment["mandatory_action_codes"] == []
    assert len(assessment["core_floor_checks"]) == 8
    assert all(
        check["normalized_shortfall"] == 0.0
        for check in assessment["core_floor_checks"]
    )
    assert from_mapping["train_only_lifecycle"] == {
        "validation_status": "unknown",
        "readiness": False,
        "nomination": False,
    }


@pytest.mark.parametrize(
    "sign_field",
    ["net_sharpe", "annualized_return", "double_cost_sharpe"],
)
def test_red_sign_override_cannot_become_green_from_other_metrics_or_score(
    sign_field: str,
) -> None:
    raw = _organizer_mapping()
    if sign_field == "double_cost_sharpe":
        raw[sign_field] = 0.0
    else:
        _set_window_metrics(raw, **{sign_field: 0.0})
    packet = build_training_metric_packet(raw, _identity())
    assessment = packet["training_assessment"]

    assert assessment["status"] == "RED"
    assert assessment["public_core_train_target_passed"] is False
    assert assessment["mandatory_action_codes"] == ["sign_inversion_cost_audit"]
    assert assessment["robustness_score_changes_status"] is False
    assert assessment["robustness_score"] > 0.0


def test_amber_reports_only_two_largest_gaps_with_frozen_tie_order() -> None:
    raw = _organizer_mapping(double_cost_sharpe=0.175, trade_count=500)
    _set_window_metrics(raw, net_sharpe=0.375, positive_quarter_fraction=0.25)
    packet = build_training_metric_packet(raw, _identity())
    assessment = packet["training_assessment"]

    assert assessment["status"] == "AMBER"
    assert assessment["public_core_train_target_passed"] is False
    assert assessment["largest_open_gaps"] == [
        {
            "name": "net_sharpe",
            "normalized_shortfall": 0.5,
            "next_action_code": "alpha_sign_or_horizon",
        },
        {
            "name": "double_cost_sharpe",
            "normalized_shortfall": 0.5,
            "next_action_code": "turnover_cost_control",
        },
    ]
    passed = [
        check
        for check in assessment["core_floor_checks"]
        if check["passed"]
    ]
    assert all(check["normalized_shortfall"] == 0.0 for check in passed)
    assert all(check["next_action_code"] is None for check in passed)


def test_nan_unknown_key_and_identity_hash_mismatch_fail_closed() -> None:
    nan_result = _organizer_mapping()
    _set_window_metrics(nan_result, net_sharpe=float("nan"))
    with pytest.raises(ValueError, match="finite"):
        build_training_metric_packet(nan_result, _identity())

    extra_key = _organizer_mapping()
    extra_key["unexpected"] = True
    with pytest.raises(ValueError, match="exactly"):
        build_training_metric_packet(extra_key, _identity())

    with pytest.raises(ValueError, match="strategy_sha256"):
        build_training_metric_packet(
            _organizer_mapping(),
            _identity(strategy_sha256="9" * 64),
        )

    bad_artifact_hash = _organizer_mapping()
    bad_artifact_hash["artifact_sha256"]["trades"] = "not-a-hash"
    with pytest.raises(ValueError, match="artifact_sha256.trades"):
        build_training_metric_packet(bad_artifact_hash, _identity())


def test_trade_and_regime_floor_boundaries_are_exact() -> None:
    boundary = _organizer_mapping(
        trade_count=1_000,
        regime_sharpe={
            "bull": 0.10,
            "bear": 0.0,
            "chop": 0.20,
            "stress": -0.75,
        },
    )
    packet = build_training_metric_packet(boundary, _identity())
    assert packet["training_assessment"]["status"] == "GREEN"
    checks = {
        check["name"]: check
        for check in packet["training_assessment"]["core_floor_checks"]
    }
    assert checks["trade_count"]["passed"] is True
    assert checks["positive_regime_count"]["observed"] == 2
    assert checks["positive_regime_count"]["passed"] is True
    assert checks["worst_regime_sharpe"]["observed"] == -0.75
    assert checks["worst_regime_sharpe"]["passed"] is True

    below_trade = copy.deepcopy(boundary)
    below_trade["trade_count"] = 999
    assert (
        build_training_metric_packet(below_trade, _identity())["training_assessment"][
            "status"
        ]
        == "AMBER"
    )

    wrong_regimes = copy.deepcopy(boundary)
    wrong_regimes["regime_sharpe"]["sideways"] = 0.1
    with pytest.raises(ValueError, match="regime_sharpe"):
        build_training_metric_packet(wrong_regimes, _identity())
    negative_trades = copy.deepcopy(boundary)
    negative_trades["trade_count"] = -1
    with pytest.raises(ValueError, match="trade_count"):
        build_training_metric_packet(negative_trades, _identity())


def test_packet_and_hash_are_deterministic_canonical_json() -> None:
    identity = _identity()
    raw = _organizer_mapping()
    first = build_training_metric_packet(raw, identity)

    reordered = dict(reversed(list(raw.items())))
    reordered["regime_sharpe"] = dict(
        reversed(list(raw["regime_sharpe"].items()))
    )
    reordered["artifacts"] = dict(reversed(list(raw["artifacts"].items())))
    reordered["artifact_sha256"] = dict(
        reversed(list(raw["artifact_sha256"].items()))
    )
    reordered["artifact_sizes"] = dict(
        reversed(list(raw["artifact_sizes"].items()))
    )
    second = build_training_metric_packet(reordered, identity)

    first_bytes = canonical_packet_bytes(first)
    assert first == second
    assert first_bytes == canonical_packet_bytes(second)
    assert json.loads(first_bytes) == first
    assert packet_sha256(first) == hashlib.sha256(first_bytes).hexdigest()
    assert packet_sha256(first) == packet_sha256(second)
    with pytest.raises(ValueError, match="finite JSON-safe"):
        canonical_packet_bytes({"bad": float("nan")})
