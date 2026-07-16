"""Focused tests for the schema-v3 score-diagnostic compatibility boundary."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

import pytest

from crypto_trade.tournament import runner_v2
from crypto_trade.tournament import score_diagnostic_compat_v2 as compatibility
from crypto_trade.tournament.amendment_integrity_v2 import pretty_json_bytes
from crypto_trade.tournament.top40_v2 import LoadedV2Config


def _state() -> dict[str, Any]:
    return {
        "schema_version": 3,
        "state_schema": "top40-v2-amendment-aware-state-v1",
    }


def _completed_result() -> dict[str, object]:
    return {
        "status": "completed",
        "failure_reason": None,
        "organizer_cpu_hours": 0.25,
        "organizer_wall_clock_hours": 0.5,
    }


def _install_validated_state(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    snapshots: list[compatibility._StateSnapshot] | None = None,
) -> tuple[LoadedV2Config, dict[str, Any], list[tuple[dict[str, Any], LoadedV2Config]]]:
    config = LoadedV2Config(tmp_path / "tournament/top40-v2/config.toml", "a" * 64, {})
    state = _state()
    payload = pretty_json_bytes(state)
    default = compatibility._StateSnapshot(payload, compatibility.sha256_bytes(payload))
    pending = iter(snapshots if snapshots is not None else [default, default])
    validations: list[tuple[dict[str, Any], LoadedV2Config]] = []

    monkeypatch.setattr(compatibility, "_load_canonical_config", lambda _root: config)
    monkeypatch.setattr(
        compatibility,
        "_read_exact_schema3_state",
        lambda _root, _config, *, amended_validator: next(pending),
    )

    def amended_validator(raw: dict[str, Any], loaded: LoadedV2Config) -> None:
        validations.append((raw, loaded))

    monkeypatch.setattr(
        compatibility.amendment_v2,
        "validate_amended_run_state",
        amended_validator,
    )
    return config, state, validations


def test_facade_is_allowlisted_immutable_and_restored(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config, state, validations = _install_validated_state(monkeypatch, tmp_path)
    original = runner_v2.tournament_contract
    observed: list[object] = []

    def runner_call() -> object:
        facade = runner_v2.tournament_contract
        observed.append(facade)
        assert facade is not original
        with pytest.raises(AttributeError):
            getattr(facade, "TEAM_IDS")
        with pytest.raises(dataclasses.FrozenInstanceError):
            facade.PHASE0_FROZEN_FILES = ()
        facade.validate_run_state(state, config)
        return _completed_result()

    result = compatibility.run_score_diagnostic_with_schema3_compatibility(
        root=tmp_path,
        runner_call=runner_call,
    )

    assert result == _completed_result()
    assert runner_v2.tournament_contract is original
    assert len(observed) == 1
    assert validations == [(state, config)]


def test_runner_exception_still_restores_and_performs_postcheck(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config, state, _validations = _install_validated_state(monkeypatch, tmp_path)
    original = runner_v2.tournament_contract

    class ExpectedFailureError(RuntimeError):
        pass

    def runner_call() -> object:
        runner_v2.tournament_contract.validate_run_state(state, config)
        raise ExpectedFailureError("runner failed")

    with pytest.raises(ExpectedFailureError, match="runner failed"):
        compatibility.run_score_diagnostic_with_schema3_compatibility(
            root=tmp_path,
            runner_call=runner_call,
        )
    assert runner_v2.tournament_contract is original


def test_state_change_fails_closed_after_contract_restoration(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    first_payload = pretty_json_bytes(_state())
    changed_payload = pretty_json_bytes({**_state(), "changed": True})
    snapshots = [
        compatibility._StateSnapshot(
            first_payload, compatibility.sha256_bytes(first_payload)
        ),
        compatibility._StateSnapshot(
            changed_payload, compatibility.sha256_bytes(changed_payload)
        ),
    ]
    config, state, _validations = _install_validated_state(
        monkeypatch,
        tmp_path,
        snapshots=snapshots,
    )
    original = runner_v2.tournament_contract

    def runner_call() -> object:
        runner_v2.tournament_contract.validate_run_state(state, config)
        return _completed_result()

    with pytest.raises(
        compatibility.ScoreDiagnosticCompatibilityError,
        match="run state changed",
    ):
        compatibility.run_score_diagnostic_with_schema3_compatibility(
            root=tmp_path,
            runner_call=runner_call,
        )
    assert runner_v2.tournament_contract is original


def test_contract_tampering_fails_closed_and_restores(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _config, _state_value, _validations = _install_validated_state(monkeypatch, tmp_path)
    original = runner_v2.tournament_contract

    def runner_call() -> object:
        runner_v2.tournament_contract = object()
        return _completed_result()

    with pytest.raises(
        compatibility.ScoreDiagnosticCompatibilityError,
        match="binding changed",
    ):
        compatibility.run_score_diagnostic_with_schema3_compatibility(
            root=tmp_path,
            runner_call=runner_call,
        )
    assert runner_v2.tournament_contract is original


def test_completed_result_requires_frozen_phase0_validator_path(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _config, _state_value, _validations = _install_validated_state(monkeypatch, tmp_path)
    original = runner_v2.tournament_contract

    with pytest.raises(
        compatibility.ScoreDiagnosticCompatibilityError,
        match="did not traverse",
    ):
        compatibility.run_score_diagnostic_with_schema3_compatibility(
            root=tmp_path,
            runner_call=_completed_result,
        )
    assert runner_v2.tournament_contract is original


@pytest.mark.parametrize(
    "raw",
    [
        {**_completed_result(), "private_ic": 0.1},
        {**_completed_result(), "status": "unknown"},
        {**_completed_result(), "failure_reason": "failure"},
        {
            **_completed_result(),
            "status": "failed",
            "failure_reason": None,
        },
        {**_completed_result(), "organizer_cpu_hours": -0.1},
        {**_completed_result(), "organizer_wall_clock_hours": True},
    ],
)
def test_runner_result_contract_fails_closed(raw: object) -> None:
    with pytest.raises(compatibility.ScoreDiagnosticCompatibilityError):
        compatibility._validate_runner_result(raw)


def test_exact_state_reader_requires_canonical_schema3_and_full_validation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config = LoadedV2Config(tmp_path / "config.toml", "b" * 64, {})
    state = _state()
    payload = pretty_json_bytes(state)
    calls: list[tuple[dict[str, Any], LoadedV2Config]] = []

    monkeypatch.setattr(
        compatibility,
        "read_repo_file",
        lambda *_args, **_kwargs: (
            "tournament/top40-v2/run_state.json",
            tmp_path / "run_state.json",
            payload,
            object(),
        ),
    )

    def validate(raw: dict[str, Any], loaded: LoadedV2Config) -> None:
        calls.append((raw, loaded))

    snapshot = compatibility._read_exact_schema3_state(
        tmp_path,
        config,
        amended_validator=validate,
    )
    assert snapshot.payload == payload
    assert snapshot.sha256 == compatibility.sha256_bytes(payload)
    assert calls == [(state, config)]

    noncanonical = json.dumps(state, separators=(",", ":")).encode("utf-8")
    monkeypatch.setattr(
        compatibility,
        "read_repo_file",
        lambda *_args, **_kwargs: (
            "tournament/top40-v2/run_state.json",
            tmp_path / "run_state.json",
            noncanonical,
            object(),
        ),
    )
    with pytest.raises(
        compatibility.ScoreDiagnosticCompatibilityError,
        match="not canonical pretty JSON",
    ):
        compatibility._read_exact_schema3_state(
            tmp_path,
            config,
            amended_validator=validate,
        )
