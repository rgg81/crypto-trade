from __future__ import annotations

import os
from pathlib import Path

import pytest

from crypto_trade.tournament import orchestrator_v3
from crypto_trade.tournament import top40_amendment_0002_durability as durability
from crypto_trade.tournament import top40_amendment_0002_validation as validation

ROOT = Path(__file__).parents[2]


def _authority() -> durability.DurabilityAuthority:
    return durability.DurabilityAuthority(
        freeze_file_sha256="a" * 64,
        freeze_commit="b" * 40,
        record_sha256="c" * 64,
        implementation_commit="d" * 40,
        parent_activation_freeze_sha256="e" * 64,
    )


def test_initialize_creates_empty_mode_0600_journal_and_fsyncs_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tournament = tmp_path / "tournament/top40-v3"
    tournament.mkdir(parents=True)
    monkeypatch.setattr(durability, "_VERIFY_DURABILITY", lambda _root: _authority())
    observed_fsync: list[Path] = []
    original_fsync = orchestrator_v3._fsync_directory

    def record_fsync(path: Path) -> None:
        observed_fsync.append(path)
        original_fsync(path)

    monkeypatch.setattr(orchestrator_v3, "_fsync_directory", record_fsync)

    result = durability.initialize_journal(tmp_path)
    journal = tmp_path / validation.VALIDATION_JOURNAL_PATH

    assert result["journal_created"] is True
    assert journal.read_bytes() == b""
    assert os.stat(journal).st_mode & 0o777 == 0o600
    assert journal.parent in observed_fsync
    assert validation.replay_validation_journal_bytes(journal.read_bytes()).records == ()


def test_initialize_is_idempotent_only_while_journal_is_empty(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / "tournament/top40-v3").mkdir(parents=True)
    monkeypatch.setattr(durability, "_VERIFY_DURABILITY", lambda _root: _authority())
    first = durability.initialize_journal(tmp_path)
    second = durability.initialize_journal(tmp_path)

    assert first["journal_created"] is True
    assert second["journal_created"] is False

    journal = tmp_path / validation.VALIDATION_JOURNAL_PATH
    journal.write_bytes(b"not-canonical\n")
    with pytest.raises(durability.DurabilityAddendumError, match="already nonempty"):
        durability.initialize_journal(tmp_path)


def test_initialize_refuses_an_open_private_validation_namespace(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / validation.PRIVATE_VALIDATION_ROOT).mkdir(parents=True)
    monkeypatch.setattr(durability, "_VERIFY_DURABILITY", lambda _root: _authority())

    with pytest.raises(durability.DurabilityAddendumError, match="private validation output"):
        durability.initialize_journal(tmp_path)

    assert not (tmp_path / validation.VALIDATION_JOURNAL_PATH).exists()


def test_addendum_is_exactly_parented_to_frozen_amendment_0002() -> None:
    parent = validation.verify_activation(ROOT)

    assert parent.freeze_commit == durability.IMPLEMENTATION_PARENT_COMMIT
    assert durability.PARENT_TEST_COMMAND == validation.AMENDMENT_TEST_COMMAND


def test_addendum_cli_has_no_probe_or_data_stage_command() -> None:
    script = (ROOT / durability.SCRIPT_PATH).read_text()

    assert 'add_parser("freeze"' in script
    assert 'add_parser("validate"' in script
    assert '"initialize-journal"' in script
    assert 'add_parser("probe"' not in script
    assert 'add_parser("private"' not in script
    assert 'add_parser("final"' not in script
