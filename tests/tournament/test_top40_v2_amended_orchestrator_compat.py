from __future__ import annotations

import contextlib
from pathlib import Path
from typing import Any

import pytest

import crypto_trade.tournament.amended_orchestrator_compat_v3 as compat
from crypto_trade.tournament.top40_v2 import LoadedV2Config


def _config(tmp_path: Path) -> LoadedV2Config:
    return LoadedV2Config(
        path=tmp_path / "config.toml",
        sha256="a" * 64,
        raw={"research_budget": {"deadline_utc": "2026-08-01T18:00:00Z"}},
    )


def _projection() -> dict[str, Any]:
    return {"schema_version": 2, "phase": "research"}


def test_read_only_command_receives_unchanged_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    projection = _projection()
    monkeypatch.setattr(
        compat,
        "read_amendment_aware_legacy_state",
        lambda *_args, **_kwargs: projection.copy(),
    )
    monkeypatch.setattr(compat, "validate_run_state", lambda *_args: None)

    with compat._compatible_legacy_state_edit(
        tmp_path,
        _config(tmp_path),
        operation="research-status",
        staged_changes=[],
    ) as observed:
        assert observed == projection


def test_read_only_command_cannot_mutate_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        compat,
        "read_amendment_aware_legacy_state",
        lambda *_args, **_kwargs: _projection(),
    )
    monkeypatch.setattr(compat, "validate_run_state", lambda *_args: None)

    with pytest.raises(ValueError, match="state mutation"):
        with compat._compatible_legacy_state_edit(
            tmp_path,
            _config(tmp_path),
            operation="research-status",
            staged_changes=[],
        ) as observed:
            observed["phase"] = "qualification_closed"


def test_read_only_command_cannot_stage_file_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    changes: list[Any] = []
    monkeypatch.setattr(
        compat,
        "read_amendment_aware_legacy_state",
        lambda *_args, **_kwargs: _projection(),
    )
    monkeypatch.setattr(compat, "validate_run_state", lambda *_args: None)

    with pytest.raises(ValueError, match="staged file mutation"):
        with compat._compatible_legacy_state_edit(
            tmp_path,
            _config(tmp_path),
            operation="research-status",
            staged_changes=changes,
        ):
            changes.append(object())


def test_result_bearing_command_delegates_to_frozen_transaction(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    observed: list[str] = []

    @contextlib.contextmanager
    def frozen_edit(*_args: Any, operation: str, **_kwargs: Any):
        observed.append(operation)
        yield _projection()

    monkeypatch.setattr(compat, "_FROZEN_EDIT", frozen_edit)
    with compat._compatible_legacy_state_edit(
        tmp_path,
        _config(tmp_path),
        operation="register-trial",
        staged_changes=[],
    ):
        pass

    assert observed == ["register-trial"]


def test_run_installs_and_restores_exact_frozen_binding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = compat.frozen_adapter.amendment_aware_legacy_state_edit

    def frozen_run(_argv: Any, *, root: Any) -> int:
        assert (
            compat.frozen_adapter.amendment_aware_legacy_state_edit
            is compat._compatible_legacy_state_edit
        )
        return 7

    monkeypatch.setattr(compat, "_FROZEN_RUN", frozen_run)
    assert compat.run(["research-status"], root=None) == 7
    assert compat.frozen_adapter.amendment_aware_legacy_state_edit is original


def test_run_restores_binding_when_frozen_adapter_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = compat.frozen_adapter.amendment_aware_legacy_state_edit

    def frozen_run(_argv: Any, *, root: Any) -> int:
        raise ValueError("boom")

    monkeypatch.setattr(compat, "_FROZEN_RUN", frozen_run)
    with pytest.raises(ValueError, match="boom"):
        compat.run(["research-status"], root=None)
    assert compat.frozen_adapter.amendment_aware_legacy_state_edit is original
