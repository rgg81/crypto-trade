"""The journal is evidence, not a log.

Every material event is recorded before the thing it authorises happens, and the chain makes an
edit, a reorder or a removal detectable. Prior editions relied on exactly that to prove a restart
inherited no evidence from the run it replaced.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from crypto_trade.tournament.v5 import journal


@pytest.fixture(name="path")
def _path(tmp_path: Path) -> Path:
    return journal.initialize(tmp_path / "research-journal.jsonl")


def test_a_fresh_journal_is_empty_and_starts_from_genesis(path: Path) -> None:
    assert journal.read(path) == []
    assert journal.head(path) == journal.GENESIS


def test_initialize_refuses_to_overwrite(path: Path) -> None:
    """Silently truncating a journal would destroy the only record of what happened."""

    with pytest.raises(journal.JournalError, match="already exists"):
        journal.initialize(path)


def test_records_chain_to_their_predecessor(path: Path) -> None:
    first = journal.append(path, "trial_accepted", {"team_id": "team-01", "trial": 1})
    second = journal.append(path, "trial_succeeded", {"team_id": "team-01", "trial": 1})
    assert first.previous_sha256 == journal.GENESIS
    assert second.previous_sha256 == first.record_sha256
    assert journal.head(path) == second.record_sha256


def test_an_edited_record_breaks_the_chain(path: Path) -> None:
    journal.append(path, "trial_accepted", {"team_id": "team-01"})
    journal.append(path, "trial_succeeded", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    tampered = json.loads(lines[0])
    tampered["payload"]["team_id"] = "team-02"
    lines[0] = json.dumps(tampered, sort_keys=True, separators=(",", ":"))
    path.write_text("\n".join(lines) + "\n")
    with pytest.raises(journal.JournalError, match="tampered digest"):
        journal.read(path)


def test_a_removed_record_breaks_the_chain(path: Path) -> None:
    journal.append(path, "trial_accepted", {"team_id": "team-01"})
    journal.append(path, "trial_succeeded", {"team_id": "team-01"})
    journal.append(path, "nominated", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    path.write_text("\n".join([lines[0], lines[2]]) + "\n")
    with pytest.raises(journal.JournalError, match="out of order"):
        journal.read(path)


def test_a_reordered_journal_is_rejected(path: Path) -> None:
    journal.append(path, "trial_accepted", {"team_id": "team-01"})
    journal.append(path, "trial_succeeded", {"team_id": "team-01"})
    lines = path.read_text().splitlines()
    path.write_text("\n".join(reversed(lines)) + "\n")
    with pytest.raises(journal.JournalError):
        journal.read(path)


def test_appending_verifies_the_chain_first(path: Path) -> None:
    """Appending onto a broken chain would bury the evidence of whatever broke it."""

    journal.append(path, "trial_accepted", {"team_id": "team-01"})
    path.write_text(path.read_text().replace('"team-01"', '"team-09"'))
    with pytest.raises(journal.JournalError):
        journal.append(path, "trial_succeeded", {"team_id": "team-01"})


def test_an_unknown_event_type_is_refused(path: Path) -> None:
    with pytest.raises(journal.JournalError, match="unknown event type"):
        journal.append(path, "quietly_promoted_a_finalist", {})


def test_a_missing_journal_is_an_error_rather_than_an_empty_history() -> None:
    """'No events' and 'no journal' are different claims."""

    with pytest.raises(journal.JournalError, match="missing"):
        journal.read(Path("/nonexistent/research-journal.jsonl"))


# -- trial accounting ------------------------------------------------------------------------


def test_a_rejected_candidate_consumes_its_slot(path: Path) -> None:
    journal.append(path, "trial_accepted", {"team_id": "team-01"})
    journal.append(path, "trial_rejected", {"team_id": "team-01"})
    assert journal.charged_trials(path) == {"team-01": 1}


def test_an_evaluator_fault_does_not_consume_a_slot(path: Path) -> None:
    """V4-R9 charged teams for the organizer's defect: 86 of 180 trials died on one bar and
    eleven of fifteen teams lost budget to it unevenly, which corrupted selection."""

    journal.append(path, "trial_accepted", {"team_id": "team-01"})
    journal.append(path, "trial_evaluator_fault", {"team_id": "team-01", "fault": "ruin"})
    assert journal.charged_trials(path) == {}
    assert journal.refunded_trials(path) == {"team-01": 1}


def test_trial_accounting_separates_teams(path: Path) -> None:
    for team in ("team-01", "team-01", "team-02"):
        journal.append(path, "trial_succeeded", {"team_id": team})
    journal.append(path, "trial_evaluator_fault", {"team_id": "team-02"})
    assert journal.charged_trials(path) == {"team-01": 2, "team-02": 1}
    assert journal.refunded_trials(path) == {"team-02": 1}


def test_consuming_and_refunding_events_are_disjoint() -> None:
    """An event that both charged and refunded would make the budget unauditable."""

    assert not (journal.TRIAL_CONSUMING & journal.TRIAL_REFUNDING)
    assert (journal.TRIAL_CONSUMING | journal.TRIAL_REFUNDING) <= journal.EVENT_TYPES


def test_events_can_be_filtered_by_type(path: Path) -> None:
    journal.append(path, "trial_accepted", {"team_id": "team-01"})
    journal.append(path, "nominated", {"team_id": "team-01", "candidate_id": "a"})
    journal.append(path, "nominated", {"team_id": "team-02", "candidate_id": "b"})
    nominations = list(journal.iter_events(path, "nominated"))
    assert [record.payload["team_id"] for record in nominations] == ["team-01", "team-02"]
