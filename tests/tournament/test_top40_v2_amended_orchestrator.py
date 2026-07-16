from __future__ import annotations

import contextlib
import copy
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import crypto_trade.tournament.amended_orchestrator_v2 as amended
from crypto_trade.tournament.amendment_v2 import LEGACY_STATE_KEYS
from crypto_trade.tournament.top40_v2 import LoadedV2Config


def _state(*, hold_active: bool) -> dict[str, Any]:
    state = {key: None for key in LEGACY_STATE_KEYS}
    state.update(
        {
            "schema_version": 3,
            "state_schema": "top40-v2-amendment-aware-state-v1",
            "administrative_hold": {
                "active": hold_active,
                "effective_research_deadline_utc": "2026-08-03T18:00:00Z",
            },
        }
    )
    return state


def _config(tmp_path: Path) -> LoadedV2Config:
    return LoadedV2Config(
        path=tmp_path / "config.toml",
        sha256="a" * 64,
        raw={"research_budget": {"deadline_utc": "2026-08-01T18:00:00Z"}},
    )


def _legacy() -> SimpleNamespace:
    def disk_write(path: Path, payload: bytes) -> None:
        path.write_bytes(payload)

    def disk_read(path: Path, _label: str) -> bytes:
        return path.read_bytes()

    def read_json(path: str | Path, _label: str) -> tuple[dict[str, Any], bytes]:
        payload = Path(path).read_bytes()
        return {}, payload

    @contextlib.contextmanager
    def edit_state(_root: Path, _config: LoadedV2Config):
        yield {}

    return SimpleNamespace(
        _atomic_write_bytes=disk_write,
        _config=lambda _root, _value: None,
        _edit_state=edit_state,
        _read_json=read_json,
        _safe_regular_bytes=disk_read,
        read_run_state=lambda _root, _config: {},
    )


def test_staged_writes_coalesce_and_overlay(tmp_path: Path) -> None:
    target = tmp_path / "ledger.jsonl"
    target.write_bytes(b"before\n")
    staged = amended._StagedWrites(tmp_path)

    staged.write(target, b"middle\n")
    staged.write(target, b"after\n")

    assert target.read_bytes() == b"before\n"
    assert staged.read(target, "ledger") == b"after\n"
    assert len(staged.changes) == 1
    assert staged.changes[0].expected == b"before\n"
    assert staged.changes[0].replacement == b"after\n"


def test_staged_writes_reject_symlink_target(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.write_bytes(b"value")
    link = tmp_path / "link"
    link.symlink_to(actual)

    with pytest.raises(ValueError, match="unsafe"):
        amended._StagedWrites(tmp_path).write(link, b"replacement")


def test_effective_config_changes_only_adapter_copy_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _config(tmp_path)
    state = _state(hold_active=False)
    monkeypatch.setattr(
        amended,
        "effective_research_deadline",
        lambda _state: datetime(2026, 8, 3, 18, tzinfo=UTC),
    )

    adapted = amended._effective_config(config, state)

    assert adapted.sha256 == config.sha256
    assert adapted.raw["research_budget"]["deadline_utc"] == "2026-08-03T18:00:00Z"
    assert config.raw["research_budget"]["deadline_utc"] == "2026-08-01T18:00:00Z"


def test_patch_stages_legacy_write_with_schema2_projection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state(hold_active=False)
    state["phase"] = "research"
    config = _config(tmp_path)
    legacy = _legacy()
    target = tmp_path / "journal.jsonl"
    target.write_bytes(b"before\n")
    observed: list[Any] = []

    monkeypatch.setattr(amended, "read_amended_state", lambda *_args, **_kwargs: state)
    monkeypatch.setattr(amended, "assert_operation_permitted", lambda *_args: None)

    @contextlib.contextmanager
    def edit(
        _root: Path,
        _config: LoadedV2Config,
        *,
        operation: str,
        staged_changes: list[Any],
    ):
        projection = amended._legacy_projection(state)
        yield projection
        observed.append((operation, copy.deepcopy(projection), list(staged_changes)))

    monkeypatch.setattr(amended, "amendment_aware_legacy_state_edit", edit)
    with amended._patch_legacy_module(
        legacy,
        root=tmp_path,
        config=config,
        effective_config=config,
        operation="register-trial",
    ):
        with legacy._edit_state(tmp_path, config) as projection:
            assert projection["schema_version"] == 2
            assert projection["phase"] == "research"
            projection["phase"] = "qualification_closed"
            legacy._atomic_write_bytes(target, b"after\n")
            assert legacy._safe_regular_bytes(target, "journal") == b"after\n"

    assert target.read_bytes() == b"before\n"
    assert observed[0][0] == "register-trial"
    assert observed[0][1]["phase"] == "qualification_closed"
    assert observed[0][2][0].expected == b"before\n"
    assert observed[0][2][0].replacement == b"after\n"


def test_patch_rejects_held_read_only_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = _state(hold_active=True)
    config = _config(tmp_path)
    legacy = _legacy()
    target = tmp_path / "journal.jsonl"
    target.write_bytes(b"before\n")
    monkeypatch.setattr(amended, "read_amended_state", lambda *_args, **_kwargs: state)
    monkeypatch.setattr(amended, "assert_operation_permitted", lambda *_args: None)
    monkeypatch.setattr(amended, "validate_run_state", lambda *_args: None)

    with amended._patch_legacy_module(
        legacy,
        root=tmp_path,
        config=config,
        effective_config=config,
        operation="research-status",
    ), pytest.raises(ValueError, match="read-only"):
        with legacy._edit_state(tmp_path, config):
            legacy._atomic_write_bytes(target, b"after\n")

    assert target.read_bytes() == b"before\n"
