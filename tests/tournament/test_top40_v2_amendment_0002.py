"""Focused tests for Top-40 V2 Amendment 0002 authority and execution."""

from __future__ import annotations

import copy
from contextlib import nullcontext
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_trade.tournament import amendment_0002_v2 as correction
from crypto_trade.tournament import score_diagnostics_v2
from crypto_trade.tournament.amendment_integrity_v2 import pretty_json_bytes, sha256_bytes
from crypto_trade.tournament.top40_v2 import LoadedV2Config


def _original_reservation() -> dict[str, object]:
    return {
        "record_sha256": correction.CORE_RESERVATION_SHA256,
        "payload": {
            "diagnostic_id": correction.CORE_DIAGNOSTIC_ID,
            "diagnostic_kind": "organizer-private-score-diagnostics-backfill-v1",
            "team_id": "team-01",
            "candidate_id": "rdf-core-h21-k3-g10",
            "candidate_registration_sha256": "1" * 64,
            "strategy_sha256": "2" * 64,
            "source_bundle_sha256": "3" * 64,
            "risk_policy_sha256": "4" * 64,
            "config_sha256": "5" * 64,
            "candidate_seed": 20260801,
            "runner_seed": 20260801,
            "snapshot_manifest_path": "snapshot.json",
            "snapshot_manifest_sha256": "6" * 64,
            "development_target_path": "targets.parquet",
            "development_target_sha256": "7" * 64,
            "runner_record_path": "runner.json",
            "runner_record_sha256": "8" * 64,
            "amendment_freeze_sha256": "9" * 64,
            "reservation_key_sha256": "a" * 64,
            "non_material": True,
            "charges_team_trial_budget": False,
        },
    }


def _failure_result() -> dict[str, object]:
    return {
        "record_sha256": correction.CORE_FAILURE_RESULT_SHA256,
        "timestamp_utc": "2026-07-16T02:52:56.233226Z",
        "payload": {
            "diagnostic_id": correction.CORE_DIAGNOSTIC_ID,
            "reservation_sha256": correction.CORE_RESERVATION_SHA256,
            "status": "failed",
            "failure_reason": correction.CORE_FAILURE_REASON,
            "artifact_hashes": {},
            "diagnostic_outcomes": None,
            "non_material": True,
            "team_material_trial_delta": 0,
            "team_cpu_hours_delta": 0.0,
            "team_wall_clock_hours_delta": 0.0,
        },
    }


def _freeze() -> dict[str, object]:
    return {
        "frozen_at_utc": "2026-07-16T03:00:00Z",
        "retry_reservation": correction._retry_reservation(_original_reservation()),
    }


def test_retry_reservation_changes_only_administrative_identity() -> None:
    original = _original_reservation()
    retry = correction._retry_reservation(original)
    assert retry["diagnostic_id"] == correction.CORE_RETRY_DIAGNOSTIC_ID
    assert retry["corrects_reservation_sha256"] == correction.CORE_RESERVATION_SHA256
    assert retry["corrects_failure_result_sha256"] == correction.CORE_FAILURE_RESULT_SHA256
    core = {key: value for key, value in retry.items() if key != "record_sha256"}
    assert retry["record_sha256"] == sha256_bytes(
        correction.amendment_v2._canonical_json_bytes(core)
    )

    payload = retry["payload"]
    assert isinstance(payload, dict)
    expected = copy.deepcopy(original["payload"])
    assert isinstance(expected, dict)
    expected.pop("reservation_key_sha256")
    expected.update(
        {
            "diagnostic_id": correction.CORE_RETRY_DIAGNOSTIC_ID,
            "correction_amendment_id": correction.AMENDMENT_ID,
            "corrects_reservation_sha256": correction.CORE_RESERVATION_SHA256,
            "corrects_failure_result_sha256": correction.CORE_FAILURE_RESULT_SHA256,
        }
    )
    assert payload == expected


def test_core_failure_must_be_exact_pre_replay_nonmaterial_failure() -> None:
    audit = SimpleNamespace(
        reservations={correction.CORE_DIAGNOSTIC_ID: _original_reservation()},
        results={correction.CORE_DIAGNOSTIC_ID: _failure_result()},
    )
    reservation, result = correction._validate_core_failure(audit)
    assert reservation["record_sha256"] == correction.CORE_RESERVATION_SHA256
    assert result["record_sha256"] == correction.CORE_FAILURE_RESULT_SHA256

    changed = _failure_result()
    assert isinstance(changed["payload"], dict)
    changed["payload"]["artifact_hashes"] = {"leak": "f" * 64}
    audit.results[correction.CORE_DIAGNOSTIC_ID] = changed
    with pytest.raises(ValueError, match="exact pre-replay"):
        correction._validate_core_failure(audit)


def test_completed_retry_result_requires_exact_public_boundary() -> None:
    freeze = _freeze()
    freeze_bytes = pretty_json_bytes(freeze)
    retry = freeze["retry_reservation"]
    assert isinstance(retry, dict)
    result = {
        "schema_version": 1,
        "amendment_id": correction.AMENDMENT_ID,
        "diagnostic_id": correction.CORE_RETRY_DIAGNOSTIC_ID,
        "status": "completed",
        "failure_reason": None,
        "recorded_at_utc": "2026-07-16T03:01:00Z",
        "retry_reservation_sha256": retry["record_sha256"],
        "amendment_0002_freeze_sha256": sha256_bytes(freeze_bytes),
        "corrects_failure_result_sha256": correction.CORE_FAILURE_RESULT_SHA256,
        "artifact_hashes": {
            name: "b" * 64 for name in correction.amendment_v2.REQUIRED_PRIVATE_ARTIFACT_NAMES
        },
        "diagnostic_outcomes": {
            name: True for name in correction.amendment_v2.DIAGNOSTIC_OUTCOME_FIELDS
        },
        "organizer_cpu_hours": 0.25,
        "organizer_wall_clock_hours": 0.5,
        "non_material": True,
        "team_material_trial_delta": 0,
        "team_cpu_hours_delta": 0.0,
        "team_wall_clock_hours_delta": 0.0,
    }
    assert correction._validate_result(result, freeze, freeze_bytes) == result
    result["diagnostic_outcomes"] = {"pooled_score_ic_positive": True}
    with pytest.raises(ValueError, match="evidence is invalid"):
        correction._validate_result(result, freeze, freeze_bytes)
    result["diagnostic_outcomes"] = {
        name: True for name in correction.amendment_v2.DIAGNOSTIC_OUTCOME_FIELDS
    }
    result["team_cpu_hours_delta"] = False
    with pytest.raises(ValueError, match="must be numeric zero"):
        correction._validate_result(result, freeze, freeze_bytes)


def test_reference_uses_facade_once_and_restores_runner(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = LoadedV2Config(tmp_path / "config.toml", "c" * 64, {})
    monkeypatch.setattr(
        correction,
        "_load_committed_successful_retry",
        lambda *_args, **_kwargs: ({}, {}),
    )
    monkeypatch.setattr(correction, "_require_active_hold", lambda *_args, **_kwargs: None)
    original = score_diagnostics_v2.run_reserved_score_diagnostic
    facade_calls: list[Path] = []

    def facade(*, root: Path, runner_call: object) -> dict[str, object]:
        facade_calls.append(Path(root))
        assert callable(runner_call)
        return runner_call()

    monkeypatch.setattr(correction, "run_score_diagnostic_with_schema3_compatibility", facade)

    def lifecycle(root: Path, _config: LoadedV2Config, **kwargs: object) -> dict[str, object]:
        assert kwargs["diagnostic_id"] == correction.REFERENCE_DIAGNOSTIC_ID
        return score_diagnostics_v2.run_reserved_score_diagnostic(
            root=root,
            reservation={},
            private_output_dir=tmp_path,
        )

    monkeypatch.setattr(correction.amendment_v2, "run_diagnostic_backfill", lifecycle)
    monkeypatch.setattr(
        score_diagnostics_v2,
        "run_reserved_score_diagnostic",
        lambda **_kwargs: {
            "status": "completed",
            "failure_reason": None,
            "organizer_cpu_hours": 0.0,
            "organizer_wall_clock_hours": 0.0,
        },
    )
    pinned = score_diagnostics_v2.run_reserved_score_diagnostic
    monkeypatch.setattr(correction, "_CANONICAL_RESERVED_RUNNER", pinned)
    event = correction.run_reference_diagnostic(tmp_path, config)
    assert event["status"] == "completed"
    assert facade_calls == [tmp_path.resolve()]
    assert score_diagnostics_v2.run_reserved_score_diagnostic is pinned
    assert pinned is not original


def test_freeze_publishes_exact_reviewed_manifest_and_record(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = LoadedV2Config(tmp_path / "config.toml", "d" * 64, {})
    review = {"reviewed_at_utc": "2026-07-16T03:00:00Z"}
    review_bytes = pretty_json_bytes(review)
    retry = correction._retry_reservation(_original_reservation())
    manifest = {
        "implementation_commit": "1" * 40,
        "implementation_files": {path: "2" * 64 for path in correction.IMPLEMENTATION_FILE_PATHS},
        "amendment_0001_freeze_sha256": "3" * 64,
        "amendment_0001_integration_sha256": "4" * 64,
        "core_failure_timestamp_utc": "2026-07-16T02:52:56.233226Z",
        "retry_reservation": retry,
    }
    captured: list[correction.TransactionChange] = []
    monkeypatch.setattr(correction, "_require_active_hold", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        correction.amendment_v2,
        "_state_lock",
        lambda _root: nullcontext(),
    )
    monkeypatch.setattr(correction, "_require_active_state_locked", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        correction,
        "_load_review",
        lambda *_args, **_kwargs: (
            review,
            review_bytes,
            "5" * 40,
            manifest,
            "6" * 64,
        ),
    )
    monkeypatch.setattr(correction, "require_no_git_history", lambda *_args: None)
    monkeypatch.setattr(
        correction,
        "publish_transaction",
        lambda _root, changes: captured.extend(changes),
    )
    def clock() -> datetime:
        return datetime(2026, 7, 16, 3, 1, tzinfo=UTC)

    freeze = correction.freeze_correction(tmp_path, config, clock=clock)
    assert freeze["retry_reservation"] == retry
    assert freeze["integration_manifest_sha256"] == "6" * 64
    assert freeze["review_sha256"] == sha256_bytes(review_bytes)
    assert [change.path for change in captured] == [
        tmp_path / correction.INTEGRATION_PATH,
        tmp_path / correction.FREEZE_PATH,
    ]
    assert captured[0].replacement == pretty_json_bytes(manifest)
    assert captured[1].replacement == pretty_json_bytes(freeze)


def test_cli_parser_exposes_only_reviewed_operations() -> None:
    import scripts.top40_v2_amendment_0002 as cli

    parser = cli.build_parser()
    assert parser.parse_args(["review-material"]).command == "review-material"
    assert parser.parse_args(["freeze-correction"]).command == "freeze-correction"
    assert parser.parse_args(["run-core-retry"]).command == "run-core-retry"
    assert parser.parse_args(["run-reference"]).command == "run-reference"
    assert parser.parse_args(["status"]).command == "status"
