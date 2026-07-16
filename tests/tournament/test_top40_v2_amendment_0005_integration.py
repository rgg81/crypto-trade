"""Focused tests for the prospective Amendment 0005 active integration."""

from __future__ import annotations

import contextlib
import json
from pathlib import Path

import pytest

from crypto_trade.tournament import amendment_0005_integration_v2 as integration
from crypto_trade.tournament import amendment_0005_v2 as amendment
from crypto_trade.tournament.amendment_integrity_v2 import sha256_bytes


def _bypass_active_guard(
    _root: Path, *, _authorization: object
) -> contextlib.AbstractContextManager[None]:
    assert _authorization is amendment._ACTIVE_INTEGRATION_AUTHORIZATION
    return contextlib.nullcontext()


def test_superset_delegates_every_non_a5_argv_unchanged(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed: list[tuple[list[str], Path]] = []
    argv = ["research-status", "team-07"]
    monkeypatch.setattr(integration, "_A5_ACTIVE_GUARD", _bypass_active_guard)
    monkeypatch.setattr(
        integration,
        "_A6_RUN",
        lambda values, *, root: observed.append((values, root)) or 9,
    )

    assert integration.run(argv, root=tmp_path) == 9
    assert observed == [(argv, tmp_path.resolve())]


def test_superset_dispatches_status_without_mutation_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    expected = {"status": "active", "execution_enabled": True}
    monkeypatch.setattr(integration, "_A5_ACTIVE_GUARD", _bypass_active_guard)
    monkeypatch.setattr(integration, "_A5_STATUS", lambda root: expected)
    monkeypatch.setattr(
        integration,
        "_A6_RUN",
        lambda *_args, **_kwargs: pytest.fail("A5 status reached Amendment 0006"),
    )

    assert integration.run([integration.STATUS_COMMAND], root=tmp_path) == 0
    assert json.loads(capsys.readouterr().out) == expected


@pytest.mark.parametrize(
    ("command", "attribute"),
    (
        (integration.RESERVE_COMMAND, "_A5_RESERVE"),
        (integration.RUN_COMMAND, "_A5_RUN"),
    ),
)
def test_superset_passes_private_identity_to_result_bearing_calls(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    attribute: str,
) -> None:
    observed: list[tuple[Path, str, str, object]] = []

    def call(
        root: Path,
        team_id: str,
        candidate_id: str,
        *,
        _authorization: object,
    ) -> dict[str, object]:
        observed.append((root, team_id, candidate_id, _authorization))
        return {"status": "ok"}

    monkeypatch.setattr(integration, "_A5_ACTIVE_GUARD", _bypass_active_guard)
    monkeypatch.setattr(integration, attribute, call)
    assert integration.run([command, "team-07", "candidate-07"], root=tmp_path) == 0
    assert observed == [
        (
            tmp_path.resolve(),
            "team-07",
            "candidate-07",
            amendment._ACTIVE_INTEGRATION_AUTHORIZATION,
        )
    ]
    assert json.loads(capsys.readouterr().out) == {"status": "ok"}


def test_public_mutations_fail_before_loading_config_without_private_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(
        amendment,
        "load_config",
        lambda *_args: pytest.fail("unauthorized mutation loaded tournament config"),
    )
    for call in (
        amendment.reserve_development_score_diagnostic,
        amendment.run_development_score_diagnostic,
    ):
        with pytest.raises(PermissionError, match="active-entrypoint"):
            call(tmp_path, "team-07", "candidate-07")


def test_loaded_superset_dispatch_identity_is_exact() -> None:
    root = Path(__file__).resolve().parents[2]
    amendment._verify_loaded_integration_dispatch(root)


def test_freeze_without_integration_reports_pending_and_disabled(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    freeze_path = tmp_path / amendment.FREEZE_PATH
    freeze_path.parent.mkdir(parents=True)
    freeze_path.write_bytes(b"present")
    freeze_bytes = b"reviewed amendment freeze"
    monkeypatch.setattr(
        amendment,
        "_pure_crypto_audit_guard",
        lambda _root: contextlib.nullcontext(),
    )
    monkeypatch.setattr(amendment, "_load_draft", lambda _root: ({}, b"draft"))
    monkeypatch.setattr(
        amendment,
        "_load_freeze",
        lambda _root: ({}, freeze_bytes, "a" * 40),
    )

    status = amendment.amendment_status(tmp_path)
    assert status["status"] == "frozen-pending-integration"
    assert status["execution_enabled"] is False
    assert status["freeze_sha256"] == sha256_bytes(freeze_bytes)
    assert "activation_journal" not in status


def test_integration_freeze_is_the_only_prospective_boundary() -> None:
    integration_freeze = {
        "activation_journal": {
            "path": "tournament/top40-v2/organizer_research_journal.jsonl",
            "record_count": 31,
            "head_sha256": "b" * 64,
        }
    }
    assert amendment._integration_activation_boundary(integration_freeze) == (31, "b" * 64)
    assert amendment._is_post_journal_prefix(30, 31) is False
    assert amendment._is_post_journal_prefix(31, 31) is True


def test_integration_authority_requires_exact_strict_commit_chain(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    observed: list[tuple[str, str, str]] = []
    monkeypatch.setattr(
        amendment,
        "_require_strict_ancestor",
        lambda _root, ancestor, descendant, label: observed.append((ancestor, descendant, label)),
    )
    commits = ("1" * 40, "2" * 40, "3" * 40, "4" * 40)
    amendment._require_integration_ancestry(tmp_path, *commits)
    assert observed == [
        (commits[0], commits[1], "A5 freeze/integration draft"),
        (commits[1], commits[2], "integration draft/review"),
        (commits[2], commits[3], "integration review/integration freeze"),
    ]


def test_authority_json_is_not_prematurely_part_of_implementation() -> None:
    assert amendment.INTEGRATION_DRAFT_PATH not in amendment.IMPLEMENTATION_FILE_PATHS
    assert amendment.INTEGRATION_REVIEW_PATH not in amendment.IMPLEMENTATION_FILE_PATHS
    assert amendment.INTEGRATION_FREEZE_PATH not in amendment.IMPLEMENTATION_FILE_PATHS
    assert amendment.ACTIVE_INTEGRATION_ENTRYPOINT_PATH in amendment.IMPLEMENTATION_FILE_PATHS
    assert amendment.ACTIVE_INTEGRATION_MODULE_PATH in amendment.IMPLEMENTATION_FILE_PATHS
