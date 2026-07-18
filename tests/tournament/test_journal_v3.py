from __future__ import annotations

import copy
import json
import threading
from pathlib import Path

import pytest

from crypto_trade.tournament import journal_v3 as journal


def _request_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "team_id": "team-01",
        "run_sequence": 1,
        "run_id": "run-0001",
        "candidate_id": "candidate-0001",
        "parent_candidate_id": "baseline-0000",
        "purpose": "baseline calibration",
        "accepted_at_utc": "2026-07-18T12:00:00Z",
        "source_bundle_sha256": "1" * 64,
        "source_archive_path": (
            "reports-top40-v3/source-archives/sha256/" + "0" * 64 + ".json"
        ),
        "source_archive_sha256": "0" * 64,
        "strategy_sha256": "2" * 64,
        "dependency_lock_sha256": "3" * 64,
        "config_sha256": "4" * 64,
        "risk_policy_sha256": "5" * 64,
        "data_authority_sha256": "6" * 64,
        "evaluator_sha256": "7" * 64,
        "seed": 20260718,
        "material_parameters": {
            "lookback_days": 90,
            "feature_family": "residual_momentum",
            "break_enabled": True,
        },
        "train_window": dict(journal.FROZEN_TRAIN_WINDOW),
        "cost_model": dict(journal.FROZEN_COST_MODEL),
        "output_path": "reports-top40-v3/labs/team-01/run-0001",
        "cumulative_material_trial_count": 1,
    }
    values.update(overrides)
    return values


def _terminal_kwargs(request: dict[str, object], **overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "event_type": "succeeded",
        "team_id": request["team_id"],
        "run_sequence": request["run_sequence"],
        "run_id": request["run_id"],
        "candidate_id": request["candidate_id"],
        "request_sha256": request["record_sha256"],
        "completed_at_utc": "2026-07-18T12:05:00Z",
        "cpu_seconds": 1.25,
        "wall_seconds": 2.5,
        "gate_vector": {"is_positive": True, "risk_ok": True},
        "metric_packet_sha256": "8" * 64,
        "artifact_hashes": {
            "metrics.json": "9" * 64,
            "targets.parquet": "a" * 64,
        },
        "cumulative_material_trial_count": request[
            "cumulative_material_trial_count"
        ],
        "failure_reason": None,
    }
    values.update(overrides)
    return values


def _append_request(path: Path, **overrides: object) -> dict[str, object]:
    state = journal.append_request_accepted(path, **_request_kwargs(**overrides))
    return dict(state.records[-1])


def _append_success(path: Path, request: dict[str, object]) -> dict[str, object]:
    state = journal.append_terminal_event(path, **_terminal_kwargs(request))
    return dict(state.records[-1])


def _records(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _seal(records: list[dict[str, object]]) -> bytes:
    """Rebuild a valid chain so semantic-corruption tests reach replay rules."""

    sealed: list[dict[str, object]] = []
    previous = journal.GENESIS_SHA256
    for sequence, source in enumerate(copy.deepcopy(records), start=1):
        source["event_sequence"] = sequence
        source["previous_sha256"] = previous
        source.pop("record_sha256", None)
        source["record_sha256"] = journal._record_sha256(source)
        previous = str(source["record_sha256"])
        sealed.append(source)
    return b"".join(journal.canonical_json_bytes(record) + b"\n" for record in sealed)


def test_identical_events_produce_identical_deterministic_journals(tmp_path: Path) -> None:
    first = tmp_path / "first.jsonl"
    second = tmp_path / "second.jsonl"
    for path in (first, second):
        request = _append_request(path)
        _append_success(path, request)

    assert first.read_bytes() == second.read_bytes()
    state = journal.replay_journal(first)
    assert state.record_count == 2
    assert state.head_sha256 == state.records[-1]["record_sha256"]
    assert state.pending_request_sha256s == ()
    assert state.material_trial_counts == {"team-01": 1}


def test_replay_rejects_tampering_and_truncation(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    request = _append_request(path)
    _append_success(path, request)
    original = path.read_bytes()

    tampered = original.replace(
        b'"purpose":"baseline calibration"',
        b'"purpose":"xaseline calibration"',
        1,
    )
    assert tampered != original
    with pytest.raises(journal.JournalValidationError, match="hash"):
        journal.replay_journal_bytes(tampered)
    with pytest.raises(journal.JournalValidationError, match="truncated"):
        journal.replay_journal_bytes(original[:-1])


def test_request_is_fsynced_before_terminal_and_each_append_is_one_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "journal.jsonl"
    durable_snapshots: list[bytes] = []

    def observe_fsync(_descriptor: int) -> None:
        durable_snapshots.append(path.read_bytes())

    monkeypatch.setattr(journal.os, "fsync", observe_fsync)
    request = _append_request(path)
    assert len(durable_snapshots) == 1
    first = journal.replay_journal_bytes(durable_snapshots[0])
    assert first.record_count == 1
    assert first.records[0]["event_type"] == "request_accepted"
    assert first.pending_request_sha256s == (request["record_sha256"],)

    _append_success(path, request)
    assert len(durable_snapshots) == 2
    completed = journal.replay_journal_bytes(durable_snapshots[1])
    assert completed.record_count == 2
    assert completed.records[1]["event_type"] == "succeeded"


def test_append_never_replaces_or_overwrites_existing_prefix(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    request = _append_request(path)
    prefix = path.read_bytes()
    inode = path.stat().st_ino

    _append_success(path, request)
    result = path.read_bytes()
    assert result.startswith(prefix)
    assert len(result) > len(prefix)
    assert path.stat().st_ino == inode


def test_exclusive_lock_blocks_a_concurrent_writer(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    attempted = threading.Event()
    acquired = threading.Event()
    failures: list[BaseException] = []

    def contender() -> None:
        attempted.set()
        try:
            with journal.exclusive_journal_lock(path):
                acquired.set()
        except BaseException as exc:  # pragma: no cover - assertion reports it
            failures.append(exc)
            acquired.set()

    with journal.exclusive_journal_lock(path):
        thread = threading.Thread(target=contender, daemon=True)
        thread.start()
        assert attempted.wait(timeout=1.0)
        assert not acquired.wait(timeout=0.05)

    assert acquired.wait(timeout=1.0)
    thread.join(timeout=1.0)
    assert not thread.is_alive()
    assert failures == []


def test_symlink_and_nonregular_journals_are_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.jsonl"
    target.write_bytes(b"")
    symlink = tmp_path / "link.jsonl"
    symlink.symlink_to(target)
    directory = tmp_path / "directory.jsonl"
    directory.mkdir()

    for unsafe in (symlink, directory):
        with pytest.raises(journal.JournalValidationError):
            journal.replay_journal(unsafe)
        with pytest.raises(journal.JournalValidationError):
            journal.append_request_accepted(unsafe, **_request_kwargs())


def test_replay_rejects_unknown_missing_and_malformed_request_fields(
    tmp_path: Path,
) -> None:
    path = tmp_path / "journal.jsonl"
    _append_request(path)
    [valid] = _records(path)

    unknown = copy.deepcopy(valid)
    unknown["surprise"] = True
    missing = copy.deepcopy(valid)
    missing.pop("purpose")
    malformed_hash = copy.deepcopy(valid)
    malformed_hash["data_authority_sha256"] = "X" * 64
    malformed_time = copy.deepcopy(valid)
    malformed_time["accepted_at_utc"] = "2026-07-18T12:00:00+00:00"

    for record in (unknown, missing, malformed_hash, malformed_time):
        with pytest.raises(journal.JournalValidationError):
            journal.replay_journal_bytes(_seal([record]))


def test_request_freezes_team_window_cost_output_and_global_serialization(
    tmp_path: Path,
) -> None:
    invalid_cases = (
        {
            "team_id": "team-99",
            "output_path": "reports-top40-v3/labs/team-99/run-0001",
        },
        {
            "train_window": {
                "start_utc": "2020-02-03T00:00:00Z",
                "end_exclusive_utc": "2022-07-02T00:00:00Z",
            }
        },
        {"cost_model": {**dict(journal.FROZEN_COST_MODEL), "taker_fee_bps_per_side": 4.0}},
        {"output_path": "reports-top40-v3/labs/team-02/run-0001"},
        {
            "source_archive_path": (
                "reports-top40-v3/source-archives/sha256/" + "f" * 64 + ".json"
            )
        },
        {"candidate_id": "Candidate-0001"},
        {"run_id": "Run-0001"},
    )
    for number, overrides in enumerate(invalid_cases):
        path = tmp_path / f"invalid-{number}.jsonl"
        with pytest.raises(journal.JournalValidationError):
            journal.append_request_accepted(path, **_request_kwargs(**overrides))
        assert path.read_bytes() == b""

    path = tmp_path / "serialized.jsonl"
    _append_request(path)
    prefix = path.read_bytes()
    with pytest.raises(journal.JournalValidationError, match="pending globally"):
        journal.append_request_accepted(
            path,
            **_request_kwargs(
                team_id="team-02",
                run_sequence=1,
                run_id="team02-run-0001",
                candidate_id="team02-candidate-0001",
                accepted_at_utc="2026-07-18T12:01:00Z",
                output_path="reports-top40-v3/labs/team-02/run-0001",
                cumulative_material_trial_count=1,
            ),
        )
    assert path.read_bytes() == prefix


def test_replay_rejects_sequence_gaps_and_nonfinite_resources(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    request = _append_request(path)
    _append_success(path, request)
    records = _records(path)

    gap = copy.deepcopy(records)
    gap[1]["event_sequence"] = 3
    gap[1].pop("record_sha256")
    gap[1]["record_sha256"] = journal._record_sha256(gap[1])
    gap_bytes = b"".join(
        journal.canonical_json_bytes(record) + b"\n" for record in gap
    )
    with pytest.raises(journal.JournalValidationError, match="gap"):
        journal.replay_journal_bytes(gap_bytes)

    finite_bytes = path.read_bytes()
    nonfinite_bytes = finite_bytes.replace(
        b'"cpu_seconds":1.25', b'"cpu_seconds":1e309', 1
    )
    assert nonfinite_bytes != finite_bytes
    with pytest.raises(journal.JournalValidationError):
        journal.replay_journal_bytes(nonfinite_bytes)


def test_terminal_requires_request_and_rejects_duplicate_or_identity_mismatch(
    tmp_path: Path,
) -> None:
    orphan = tmp_path / "orphan.jsonl"
    fake_request = {
        **_request_kwargs(),
        "record_sha256": "b" * 64,
    }
    with pytest.raises(journal.JournalValidationError, match="no accepted request"):
        journal.append_terminal_event(orphan, **_terminal_kwargs(fake_request))
    assert orphan.read_bytes() == b""

    path = tmp_path / "journal.jsonl"
    request = _append_request(path)
    _append_success(path, request)
    completed_bytes = path.read_bytes()
    with pytest.raises(journal.JournalValidationError, match="duplicate terminal"):
        journal.append_terminal_event(path, **_terminal_kwargs(request))
    assert path.read_bytes() == completed_bytes

    mismatch_path = tmp_path / "mismatch.jsonl"
    mismatch_request = _append_request(mismatch_path)
    with pytest.raises(journal.JournalValidationError, match="candidate_id"):
        journal.append_terminal_event(
            mismatch_path,
            **_terminal_kwargs(mismatch_request, candidate_id="candidate-wrong"),
        )


def test_per_team_sequence_and_trial_counter_cannot_gap_or_reset(tmp_path: Path) -> None:
    path = tmp_path / "journal.jsonl"
    first_request = _append_request(path)
    _append_success(path, first_request)
    prefix = path.read_bytes()

    common = {
        "run_id": "run-0002",
        "candidate_id": "candidate-0002",
        "parent_candidate_id": "candidate-0001",
        "accepted_at_utc": "2026-07-18T12:06:00Z",
        "output_path": "reports-top40-v3/labs/team-01/run-0002",
    }
    with pytest.raises(journal.JournalValidationError, match="run_sequence"):
        journal.append_request_accepted(
            path,
            **_request_kwargs(
                **common,
                run_sequence=3,
                cumulative_material_trial_count=2,
            ),
        )
    with pytest.raises(journal.JournalValidationError, match="trial count"):
        journal.append_request_accepted(
            path,
            **_request_kwargs(
                **common,
                run_sequence=2,
                cumulative_material_trial_count=1,
            ),
        )
    assert path.read_bytes() == prefix


def test_success_requires_metrics_and_artifacts_and_failure_requires_reason(
    tmp_path: Path,
) -> None:
    success_path = tmp_path / "success.jsonl"
    success_request = _append_request(success_path)
    for missing in (
        {"metric_packet_sha256": None},
        {"artifact_hashes": {}},
        {"gate_vector": {}},
    ):
        with pytest.raises(journal.JournalValidationError):
            journal.append_terminal_event(
                success_path, **_terminal_kwargs(success_request, **missing)
            )

    failure_path = tmp_path / "failure.jsonl"
    failure_request = _append_request(failure_path)
    with pytest.raises(journal.JournalValidationError, match="failure_reason"):
        journal.append_terminal_event(
            failure_path,
            **_terminal_kwargs(
                failure_request,
                event_type="failed",
                gate_vector={},
                metric_packet_sha256=None,
                artifact_hashes={},
                failure_reason=None,
            ),
        )

    failed = journal.append_terminal_event(
        failure_path,
        **_terminal_kwargs(
            failure_request,
            event_type="failed",
            gate_vector={"data_ok": False},
            metric_packet_sha256=None,
            artifact_hashes={},
            failure_reason="worker exited before evaluation",
        ),
    )
    assert failed.records[-1]["event_type"] == "failed"
