from __future__ import annotations

import argparse
import base64
import dataclasses
import hashlib
import importlib.util
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_trade.tournament.top40 import submission_from_dict


def _load_cli_module():
    path = Path(__file__).parents[2] / "scripts" / "top40_tournament.py"
    spec = importlib.util.spec_from_file_location("top40_tournament_cli_for_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _budget() -> dict:
    return {
        "maximum_material_configurations_per_team": 120,
        "maximum_public_oos_views_per_team": 3,
        "maximum_cpu_hours_per_team": 12.0,
        "maximum_wall_clock_hours_per_team": 18.0,
        "deadline_utc": "2026-07-16T18:00:00Z",
    }


def _events(*, requested: bool = False, accessed: bool = False) -> list[dict]:
    return [
        {
            "event_id": "event-1-register",
            "candidate_id": "candidate-1",
            "event_type": "registered",
            "timestamp_utc": "2026-07-13T01:00:00Z",
            "parent_candidate_id": None,
            "delta": "initial hypothesis",
            "seed": 2026071301,
            "parameters": {"lookback": 30},
            "public_oos_requested": requested,
        },
        {
            "event_id": "event-1-result",
            "candidate_id": "candidate-1",
            "event_type": "result",
            "timestamp_utc": "2026-07-13T02:00:00Z",
            "cpu_hours": 1.0,
            "wall_clock_hours": 1.5,
            "is_metrics": {"net_sharpe": 0.5},
            "public_oos_accessed": accessed,
            "public_oos_metrics": {"net_sharpe": 0.4} if accessed else None,
            "disposition": "keep",
            "artifact_hashes": {"report": "a" * 64},
        },
    ]


def _write_events(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )


def _organizer_accounting(cli, ledger: Path, *, status: str = "failed"):
    lines = ledger.read_bytes().splitlines(keepends=True)
    registration_sha = hashlib.sha256(lines[0]).hexdigest()
    result_sha = hashlib.sha256(lines[1]).hexdigest()
    failure = "RuntimeError" if status == "failed" else None
    reservation_payload = {
        "run_id": "1" * 64,
        "team_id": "team-01",
        "candidate_id": "candidate-1",
        "registration_bytes_base64": base64.b64encode(lines[0]).decode("ascii"),
        "registration_sha256": registration_sha,
        "team_ledger_sha256": "2" * 64,
        "source_bundle_sha256": "3" * 64,
    }
    result_row = json.loads(lines[1])
    canonical_metrics = None
    if result_row["is_metrics"] is not None:
        canonical_metrics = {
            "in_sample": {"metrics": result_row["is_metrics"]},
            "public_oos": {"metrics": result_row["public_oos_metrics"]},
        }
    result_payload = {
        "run_id": "1" * 64,
        "team_id": "team-01",
        "candidate_id": "candidate-1",
        "status": status,
        "failure_type": failure,
        "cpu_hours": result_row["cpu_hours"],
        "wall_clock_hours": result_row["wall_clock_hours"],
        "canonical_metrics": canonical_metrics,
        "artifact_hashes": result_row["artifact_hashes"],
        "team_result_sha256": result_sha,
    }
    runs = {
        "candidate-1": {
            "reservation": {
                "record_sha256": "4" * 64,
                "timestamp_utc": "2026-07-13T01:30:00Z",
                "payload": reservation_payload,
            },
            "result": {
                "record_sha256": "5" * 64,
                "timestamp_utc": result_row["timestamp_utc"],
                "payload": result_payload,
            },
        }
    }
    accesses = [
        {
            "run_id": "1" * 64,
            "candidate_id": "candidate-1",
            "registration_sha256": registration_sha,
            "team_ledger_sha256": "2" * 64,
            "source_bundle_sha256": "3" * 64,
            "reservation_record_sha256": "4" * 64,
            "result_record_sha256": "5" * 64,
            "reserved_at_utc": "2026-07-13T01:30:00Z",
            "status": status,
            "finished_at_utc": result_row["timestamp_utc"],
            "failure_type": failure,
        }
    ]
    return accesses, runs


def _git_init(path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Top40 Test"], cwd=path, check=True)


def _git_commit(path: Path, message: str) -> str:
    subprocess.run(["git", "add", "."], cwd=path, check=True)
    subprocess.run(["git", "commit", "-qm", message], cwd=path, check=True)
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_journal_fixture(cli, root: Path):
    _git_init(root)
    _genesis, genesis_bytes, journal_state = cli._new_research_journal()
    journal = root / cli.ORGANIZER_RESEARCH_JOURNAL_PATH
    journal.parent.mkdir(parents=True)
    journal.write_bytes(genesis_bytes)
    ledger = root / cli.canonical_artifact_paths("team-01")["trial_ledger"]
    ledger.parent.mkdir(parents=True, exist_ok=True)
    _write_events(ledger, _events(requested=True)[:1])
    state = {"research_journal": dict(journal_state), "teams": {}}
    state_path = root / cli.RUN_STATE_PATH
    state_path.write_text(json.dumps(state) + "\n", encoding="utf-8")
    common = _git_commit(root, "common Phase-0 inputs")
    phase0 = root / cli.PHASE0_FREEZE_PATH
    phase0.write_text(json.dumps({"common_freeze_commit": common}) + "\n", encoding="utf-8")
    _git_commit(root, "Phase-0 record")
    return state, ledger, genesis_bytes, dict(journal_state)


def _append_git_journal_reservation(cli, root: Path, state: dict, *, run_digit: str) -> None:
    ledger = root / cli.canonical_artifact_paths("team-01")["trial_ledger"]
    ledger_bytes = ledger.read_bytes()
    registration = ledger_bytes.splitlines(keepends=True)[0]
    cli._append_research_journal_locked(
        root,
        state,
        "reservation",
        {
            "run_id": run_digit * 64,
            "team_id": "team-01",
            "candidate_id": f"candidate-{run_digit}",
            "registration_bytes_base64": base64.b64encode(registration).decode("ascii"),
            "registration_sha256": hashlib.sha256(registration).hexdigest(),
            "team_ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "team_ledger_size": len(ledger_bytes),
        },
        timestamp=datetime.now(UTC),
    )
    (root / cli.RUN_STATE_PATH).write_text(json.dumps(state) + "\n", encoding="utf-8")


def _valid_submissions(count: int = 10):
    template_path = Path(__file__).parents[2] / "tournament/top40/templates/submission.json"
    template = template_path.read_text(encoding="utf-8")
    submissions = []
    for number in range(1, count + 1):
        team_id = f"team-{number:02d}"
        raw = json.loads(template.replace("team-01", team_id))
        raw["team_id"] = team_id
        raw["strategy_name"] = f"strategy-{team_id}"
        raw["freeze_commit"] = f"{number:x}" * 40
        raw["compliance"] = {name: True for name in raw["compliance"]}
        submissions.append(submission_from_dict(raw))
    return submissions


def test_append_only_ledger_counts_candidates_and_enforces_access_and_budgets(tmp_path):
    cli = _load_cli_module()
    ledger = tmp_path / "experiments.jsonl"
    rows = _events(requested=True, accessed=True)
    _write_events(ledger, rows)
    parsed, trial_count = cli._validate_experiment_ledger(
        ledger,
        _budget(),
        phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
    )
    assert parsed == rows
    assert trial_count == 1

    rows = _events(requested=False, accessed=True)
    _write_events(ledger, rows)
    with pytest.raises(ValueError, match="requires prior registration"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
        )

    rows = _events()
    rows[1]["cpu_hours"] = 12.1
    _write_events(ledger, rows)
    with pytest.raises(ValueError, match="CPU-hour budget"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
        )


def test_ledger_rejects_backdated_or_unpaired_events(tmp_path):
    cli = _load_cli_module()
    ledger = tmp_path / "experiments.jsonl"
    rows = _events()
    rows[0]["timestamp_utc"] = "2026-07-12T23:59:59Z"
    _write_events(ledger, rows)
    with pytest.raises(ValueError, match="predates the Phase-0 freeze"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
        )

    _write_events(ledger, _events()[:1])
    with pytest.raises(ValueError, match="exactly one result"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
        )


def test_public_oos_reservations_bind_registration_and_count_failed_attempts(tmp_path):
    cli = _load_cli_module()
    ledger = tmp_path / "experiments.jsonl"
    rows = _events(requested=True, accessed=True)
    rows[1]["public_oos_metrics"] = None
    rows[1]["is_metrics"] = None
    rows[1]["artifact_hashes"] = {}
    _write_events(ledger, rows)
    reservations, organizer_runs = _organizer_accounting(cli, ledger)
    _parsed, trial_count = cli._validate_experiment_ledger(
        ledger,
        _budget(),
        phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
        oos_accesses=reservations,
        organizer_runs=organizer_runs,
    )
    assert trial_count == 1

    unfinished = [
        dict(
            reservations[0],
            status="reserved",
            result_record_sha256=None,
            finished_at_utc=None,
            failure_type=None,
        )
    ]
    with pytest.raises(ValueError, match="differs from organizer journal"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
            oos_accesses=unfinished,
            organizer_runs=organizer_runs,
        )

    rows[1]["timestamp_utc"] = "2026-07-13T01:40:00Z"
    _write_events(ledger, rows)
    with pytest.raises(ValueError, match="bytes differ|timestamps"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
            oos_accesses=reservations,
            organizer_runs=organizer_runs,
        )
    rows[1]["timestamp_utc"] = "2026-07-13T02:00:00Z"

    rows[0]["delta"] = "rewritten after reservation"
    _write_events(ledger, rows)
    with pytest.raises(ValueError, match="changed after organizer reservation"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
            oos_accesses=reservations,
            organizer_runs=organizer_runs,
        )


def test_ledger_rejects_event_timestamps_in_the_future(tmp_path):
    cli = _load_cli_module()
    ledger = tmp_path / "experiments.jsonl"
    rows = _events()
    rows[1]["timestamp_utc"] = "2026-07-14T00:00:00Z"
    _write_events(ledger, rows)
    with pytest.raises(ValueError, match="cannot be in the future"):
        cli._validate_experiment_ledger(
            ledger,
            _budget(),
            phase0_started_at=datetime(2026, 7, 13, tzinfo=UTC),
        )


def test_public_oos_gate_requires_one_pending_request_and_rejects_replay(tmp_path):
    cli = _load_cli_module()
    ledger = tmp_path / "experiments.jsonl"
    pending = _events(requested=True, accessed=True)[:1]
    _write_events(ledger, pending)
    row, digest, raw_line = cli._pending_public_oos_registration(ledger, "candidate-1")
    assert row["public_oos_requested"] is True
    assert digest == hashlib.sha256(ledger.read_bytes()).hexdigest()
    assert raw_line == ledger.read_bytes()

    _write_events(ledger, _events(requested=True, accessed=True))
    with pytest.raises(ValueError, match="replay is forbidden"):
        cli._pending_public_oos_registration(ledger, "candidate-1")


def test_organizer_journal_is_canonical_hash_chained_and_state_anchored(tmp_path):
    cli = _load_cli_module()
    _record, raw_line, journal_state = cli._new_research_journal()
    path = tmp_path / cli.ORGANIZER_RESEARCH_JOURNAL_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes(raw_line)
    state = {"research_journal": journal_state}

    records = cli._validate_research_journal(tmp_path, state)
    assert [record["event_type"] for record in records] == ["genesis"]

    tampered = json.loads(raw_line)
    tampered["payload"]["branch"] = "rewritten"
    path.write_bytes(cli._canonical_json_bytes(tampered) + b"\n")
    with pytest.raises(ValueError, match="hash chain|genesis"):
        cli._validate_research_journal(tmp_path, state)


def test_git_history_accepts_only_committed_strict_journal_and_ledger_appends(tmp_path):
    cli = _load_cli_module()
    state, _ledger, _genesis_bytes, _genesis_state = _git_journal_fixture(cli, tmp_path)
    _append_git_journal_reservation(cli, tmp_path, state, run_digit="7")
    _git_commit(tmp_path, "organizer reservation")

    cli._verify_research_journal_git_history(
        tmp_path,
        json.loads((tmp_path / cli.RUN_STATE_PATH).read_text(encoding="utf-8")),
        affected_team_ids=("team-01",),
    )


@pytest.mark.parametrize("mutation", ["rewrite", "truncate"])
def test_git_history_rejects_committed_organizer_journal_rewrite_or_truncation(
    tmp_path: Path, mutation: str
):
    cli = _load_cli_module()
    state, _ledger, genesis_bytes, genesis_state = _git_journal_fixture(cli, tmp_path)
    _append_git_journal_reservation(cli, tmp_path, state, run_digit="7")
    _git_commit(tmp_path, "first organizer reservation")

    journal = tmp_path / cli.ORGANIZER_RESEARCH_JOURNAL_PATH
    state["research_journal"] = dict(genesis_state)
    journal.write_bytes(genesis_bytes)
    if mutation == "rewrite":
        _append_git_journal_reservation(cli, tmp_path, state, run_digit="8")
    else:
        (tmp_path / cli.RUN_STATE_PATH).write_text(json.dumps(state) + "\n", encoding="utf-8")
    _git_commit(tmp_path, f"forbidden journal {mutation}")

    with pytest.raises(ValueError, match="rewrites|truncat|preserve Git history"):
        cli._verify_research_journal_git_history(
            tmp_path,
            json.loads((tmp_path / cli.RUN_STATE_PATH).read_text(encoding="utf-8")),
            affected_team_ids=("team-01",),
        )


def test_git_history_rejects_committed_team_ledger_rewrite(tmp_path):
    cli = _load_cli_module()
    state, ledger, _genesis_bytes, _genesis_state = _git_journal_fixture(cli, tmp_path)
    rewritten = _events(requested=True)[:1]
    rewritten[0]["delta"] = "rewritten committed hypothesis"
    _write_events(ledger, rewritten)
    _git_commit(tmp_path, "forbidden team ledger rewrite")

    with pytest.raises(ValueError, match="rewrites or truncates"):
        cli._verify_research_journal_git_history(
            tmp_path,
            state,
            affected_team_ids=("team-01",),
        )


def test_git_history_rejects_uncommitted_accounting_inputs(tmp_path):
    cli = _load_cli_module()
    state, ledger, _genesis_bytes, _genesis_state = _git_journal_fixture(cli, tmp_path)
    with ledger.open("ab") as handle:
        handle.write(b"uncommitted\n")

    with pytest.raises(ValueError, match="commit the organizer journal"):
        cli._verify_research_journal_git_history(
            tmp_path,
            state,
            affected_team_ids=("team-01",),
        )


def test_fourth_public_oos_view_is_rejected_from_authoritative_journal_count():
    cli = _load_cli_module()
    prior_runs = {f"candidate-{index}": {} for index in range(1, 4)}
    with pytest.raises(ValueError, match="already consumed its 3"):
        cli._require_public_oos_capacity("team-01", prior_runs, 3)


def test_run_state_cannot_delete_a_failed_organizer_attempt():
    cli = _load_cli_module()
    runs = {
        "failed-candidate": {
            "reservation": {
                "record_sha256": "a" * 64,
                "timestamp_utc": "2026-07-13T01:00:00Z",
                "payload": {
                    "run_id": "b" * 64,
                    "candidate_id": "failed-candidate",
                    "registration_sha256": "c" * 64,
                    "team_ledger_sha256": "d" * 64,
                    "source_bundle_sha256": "e" * 64,
                },
            },
            "result": {
                "record_sha256": "f" * 64,
                "timestamp_utc": "2026-07-13T02:00:00Z",
                "payload": {"status": "failed", "failure_type": "RuntimeError"},
            },
        }
    }
    with pytest.raises(ValueError, match="omits or invents organizer runs"):
        cli._validate_oos_state_against_journal("team-01", [], runs)


def test_organizer_automatically_appends_measured_public_oos_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    team_id = "team-01"
    ledger = tmp_path / cli.canonical_artifact_paths(team_id)["trial_ledger"]
    ledger.parent.mkdir(parents=True)
    _write_events(ledger, _events(requested=True, accessed=True)[:1])
    registration_line = ledger.read_bytes()
    _genesis, journal_bytes, journal_state = cli._new_research_journal()
    journal_path = tmp_path / cli.ORGANIZER_RESEARCH_JOURNAL_PATH
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_bytes(journal_bytes)
    state = {
        "phase": "research",
        "research_journal": journal_state,
        "teams": {team_id: {"oos_accesses": []}},
    }
    run_id = "7" * 64
    reserved_at = datetime.now(UTC)
    reservation_payload = {
        "run_id": run_id,
        "team_id": team_id,
        "candidate_id": "candidate-1",
        "registration_bytes_base64": base64.b64encode(registration_line).decode("ascii"),
        "registration_sha256": hashlib.sha256(registration_line).hexdigest(),
        "team_ledger_sha256": hashlib.sha256(registration_line).hexdigest(),
        "team_ledger_size": len(registration_line),
        "source_bundle_sha256": "8" * 64,
    }
    reservation = cli._append_research_journal_locked(
        tmp_path,
        state,
        "reservation",
        reservation_payload,
        timestamp=reserved_at,
    )
    state["teams"][team_id]["oos_accesses"].append(
        {
            "run_id": run_id,
            "candidate_id": "candidate-1",
            "registration_sha256": reservation_payload["registration_sha256"],
            "team_ledger_sha256": reservation_payload["team_ledger_sha256"],
            "source_bundle_sha256": reservation_payload["source_bundle_sha256"],
            "reservation_record_sha256": reservation["record_sha256"],
            "result_record_sha256": None,
            "reserved_at_utc": reservation["timestamp_utc"],
            "status": "reserved",
            "finished_at_utc": None,
            "failure_type": None,
        }
    )
    state_path = tmp_path / cli.RUN_STATE_PATH
    state_path.write_text(json.dumps(state), encoding="utf-8")
    artifact = tmp_path / "reports-top40/team-01/targets.parquet"
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"canonical targets")
    metrics = cli.WindowMetrics(0.5, 0.6, 0.4, 0.2, -0.1, 0.75)
    result = SimpleNamespace(
        in_sample=cli.EvaluationWindow("2020-02-03", "2024-06-30", metrics),
        public_oos=cli.EvaluationWindow("2024-07-01", "2026-06-30", metrics),
        double_cost_oos_sharpe=0.3,
        regime_sharpe={"bull": 0.4},
        confidence_intervals={"public_oos_net_sharpe_95": (0.1, 0.9)},
        artifacts={"targets": "reports-top40/team-01/targets.parquet"},
        source_bundle_sha256="8" * 64,
        decision_count=10,
        event_count=4,
        trade_count=2,
    )
    monkeypatch.chdir(tmp_path)

    cli._finish_oos_reservation(
        tmp_path,
        team_id,
        "candidate-1",
        run_id,
        status="completed",
        failure_type=None,
        result=result,
        cpu_hours=0.25,
        wall_clock_hours=0.5,
    )

    rows = [json.loads(line) for line in ledger.read_bytes().splitlines()]
    assert len(rows) == 2
    assert rows[1]["cpu_hours"] == 0.25
    assert rows[1]["public_oos_metrics"]["net_sharpe"] == 0.5
    final_state = json.loads(state_path.read_text(encoding="utf-8"))
    assert final_state["teams"][team_id]["oos_accesses"][0]["status"] == "completed"
    journal = cli._validate_research_journal(tmp_path, final_state)
    assert [record["event_type"] for record in journal] == [
        "genesis",
        "reservation",
        "result",
    ]
    payload = journal[-1]["payload"]
    team_line = base64.b64decode(payload["team_result_bytes_base64"], validate=True)
    assert hashlib.sha256(team_line).hexdigest() == payload["team_result_sha256"]
    assert ledger.read_bytes().endswith(team_line)


def _research_crash_fixture(cli, root: Path):
    team_id = "team-01"
    ledger = root / cli.canonical_artifact_paths(team_id)["trial_ledger"]
    ledger.parent.mkdir(parents=True)
    _write_events(ledger, _events(requested=True)[:1])
    registration_line = ledger.read_bytes()
    _genesis, journal_bytes, journal_state = cli._new_research_journal()
    journal_path = root / cli.ORGANIZER_RESEARCH_JOURNAL_PATH
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_bytes(journal_bytes)
    state = {
        "phase": "research",
        "research_journal": journal_state,
        "teams": {team_id: {"oos_accesses": []}},
    }
    state_before_reservation = json.loads(json.dumps(state))
    run_id = "9" * 64
    reservation_payload = {
        "run_id": run_id,
        "team_id": team_id,
        "candidate_id": "candidate-1",
        "registration_bytes_base64": base64.b64encode(registration_line).decode("ascii"),
        "registration_sha256": hashlib.sha256(registration_line).hexdigest(),
        "team_ledger_sha256": hashlib.sha256(registration_line).hexdigest(),
        "team_ledger_size": len(registration_line),
        "source_bundle_sha256": "8" * 64,
    }
    reservation = cli._append_research_journal_locked(
        root,
        state,
        "reservation",
        reservation_payload,
        timestamp=datetime.now(UTC),
    )
    return (
        state_before_reservation,
        state,
        ledger,
        reservation,
        reservation_payload,
    )


def _append_result_write_ahead(cli, root: Path, reserved_state: dict, reservation: dict):
    payload = reservation["payload"]
    finished_at = datetime.now(UTC)
    team_event = cli._team_result_event(
        run_id=payload["run_id"],
        candidate_id=payload["candidate_id"],
        finished_at=finished_at,
        status="failed",
        failure_type="RuntimeError",
        cpu_hours=0.25,
        wall_clock_hours=0.5,
        metrics=None,
        artifact_hashes={},
    )
    team_line = cli._canonical_json_bytes(team_event) + b"\n"
    result_payload = {
        "run_id": payload["run_id"],
        "team_id": payload["team_id"],
        "candidate_id": payload["candidate_id"],
        "status": "failed",
        "failure_type": "RuntimeError",
        "cpu_hours": 0.25,
        "wall_clock_hours": 0.5,
        "source_bundle_sha256": payload["source_bundle_sha256"],
        "canonical_metrics": None,
        "artifact_hashes": {},
        "artifact_sizes": {},
        "decision_count": None,
        "event_count": None,
        "trade_count": None,
        "team_result_bytes_base64": base64.b64encode(team_line).decode("ascii"),
        "team_result_sha256": hashlib.sha256(team_line).hexdigest(),
    }
    record = cli._append_research_journal_locked(
        root,
        reserved_state,
        "result",
        result_payload,
        timestamp=finished_at,
    )
    return record, team_line


def test_recovery_replays_journal_only_reservation_into_state(tmp_path):
    cli = _load_cli_module()
    stale, _advanced, ledger, reservation, _payload = _research_crash_fixture(cli, tmp_path)

    replayed, appended = cli._recover_research_accounting_locked(tmp_path, stale)

    assert (replayed, appended) == (1, 0)
    access = stale["teams"]["team-01"]["oos_accesses"][0]
    assert access["reservation_record_sha256"] == reservation["record_sha256"]
    assert access["status"] == "reserved"
    assert len(ledger.read_bytes().splitlines()) == 1
    cli._validate_research_journal(tmp_path, stale)


@pytest.mark.parametrize("ledger_already_appended", [False, True])
def test_recovery_repairs_result_crash_before_state_without_duplicate(
    tmp_path: Path, ledger_already_appended: bool
):
    cli = _load_cli_module()
    stale, _advanced, ledger, reservation, _payload = _research_crash_fixture(cli, tmp_path)
    cli._recover_research_accounting_locked(tmp_path, stale)
    reserved_state = json.loads(json.dumps(stale))
    wal_state = json.loads(json.dumps(stale))
    result_record, team_line = _append_result_write_ahead(cli, tmp_path, wal_state, reservation)
    if ledger_already_appended:
        with ledger.open("ab") as handle:
            handle.write(team_line)

    replayed, appended = cli._recover_research_accounting_locked(tmp_path, reserved_state)

    assert replayed == 1
    assert appended == int(not ledger_already_appended)
    assert ledger.read_bytes().count(team_line) == 1
    access = reserved_state["teams"]["team-01"]["oos_accesses"][0]
    assert access["result_record_sha256"] == result_record["record_sha256"]
    assert access["status"] == "failed"
    cli._validate_research_journal(tmp_path, reserved_state)


def test_recovery_rejects_divergent_ledger_or_nonprefix_state(tmp_path):
    cli = _load_cli_module()
    stale, _advanced, ledger, reservation, _payload = _research_crash_fixture(cli, tmp_path)
    cli._recover_research_accounting_locked(tmp_path, stale)
    reserved_state = json.loads(json.dumps(stale))
    wal_state = json.loads(json.dumps(stale))
    _record, team_line = _append_result_write_ahead(cli, tmp_path, wal_state, reservation)
    with ledger.open("ab") as handle:
        handle.write(b'{"divergent":true}\n')

    with pytest.raises(ValueError, match="divergent result bytes"):
        cli._recover_research_accounting_locked(tmp_path, reserved_state)
    assert reserved_state["research_journal"]["record_count"] == 2

    prefix_size = reservation["payload"]["team_ledger_size"]
    registration = ledger.read_bytes()[:prefix_size]
    ledger.write_bytes(registration + team_line + b'{"unexpected_tail":true}\n')
    with pytest.raises(ValueError, match="divergent result bytes"):
        cli._recover_research_accounting_locked(tmp_path, reserved_state)

    bad_anchor = json.loads(json.dumps(reserved_state))
    bad_anchor["research_journal"]["head_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="prefix head"):
        cli._recover_research_accounting_locked(tmp_path, bad_anchor)


def test_close_interrupted_run_is_failed_counted_and_uses_elapsed_wall_time(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    _git_init(tmp_path)
    stale, _advanced, ledger, _reservation, _payload = _research_crash_fixture(cli, tmp_path)
    cli._recover_research_accounting_locked(tmp_path, stale)
    (tmp_path / cli.RUN_STATE_PATH).write_text(json.dumps(stale) + "\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)

    cli._close_interrupted_run(argparse.Namespace(team_id="team-01", candidate_id="candidate-1"))

    final_state = json.loads((tmp_path / cli.RUN_STATE_PATH).read_text(encoding="utf-8"))
    records = cli._validate_research_journal(tmp_path, final_state)
    result = records[-1]["payload"]
    assert result["status"] == "failed"
    assert result["failure_type"] == "OrganizerInterruptedRun"
    assert result["wall_clock_hours"] >= 0.0
    assert len(ledger.read_bytes().splitlines()) == 2
    assert final_state["teams"]["team-01"]["oos_accesses"][0]["status"] == "failed"


def test_malformed_canonical_submission_becomes_a_team_disqualification(tmp_path):
    cli = _load_cli_module()
    path = tmp_path / "tournament/top40/teams/team-03/submission.json"
    path.parent.mkdir(parents=True)
    path.write_text("{not JSON", encoding="utf-8")
    submissions, issues = cli._load_scoring_submissions([str(path.relative_to(tmp_path))], tmp_path)
    assert [submission.team_id for submission in submissions] == ["team-03"]
    assert issues["team-03"][0].code == "submission"


def test_submission_cannot_impersonate_another_team_and_abort_scoring(tmp_path):
    cli = _load_cli_module()
    template_path = Path(__file__).parents[2] / "tournament/top40/templates/submission.json"
    payload = json.loads(template_path.read_text(encoding="utf-8"))
    payload["team_id"] = "team-02"
    path = tmp_path / "tournament/top40/teams/team-03/submission.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload), encoding="utf-8")

    submissions, issues = cli._load_scoring_submissions([str(path.relative_to(tmp_path))], tmp_path)

    assert [submission.team_id for submission in submissions] == ["team-03"]
    assert issues["team-03"][0].code == "submission_path"


def test_critic_adjudications_are_cohort_bound_evidenced_and_allowlisted(tmp_path):
    cli = _load_cli_module()
    template_path = Path(__file__).parents[2] / "tournament/top40/templates/submission.json"
    raw = json.loads(template_path.read_text(encoding="utf-8"))
    raw["freeze_commit"] = "a" * 40
    raw["artifact_manifest_sha256"] = "b" * 64
    evidence = tmp_path / raw["artifacts"]["research_brief"]
    evidence.parent.mkdir(parents=True)
    evidence.write_text("demonstrated future timestamp\n", encoding="utf-8")
    submission = submission_from_dict(raw)
    payload = {
        "schema_version": 1,
        "cohort_sha256": cli._cohort_sha256([submission]),
        "teams": {
            "team-01": {
                "freeze_commit": submission.freeze_commit,
                "artifact_manifest_sha256": submission.artifact_manifest_sha256,
                "findings": [
                    {
                        "code": "critic_future_data",
                        "evidence_artifact": "research_brief",
                        "evidence_sha256": hashlib.sha256(evidence.read_bytes()).hexdigest(),
                        "detail": "Feature timestamp is later than its decision timestamp.",
                    }
                ],
            }
        },
    }
    path = tmp_path / "critic.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    issues = cli._critic_adjudication_issues(str(path), [submission], tmp_path)
    assert issues["team-01"][0].code == "critic_future_data"

    payload["teams"]["team-01"]["findings"][0]["code"] = "critic_low_sharpe"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="forbidden"):
        cli._critic_adjudication_issues(str(path), [submission], tmp_path)


def test_mark_review_requires_explicit_ordered_handoffs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Top40 Test"], cwd=tmp_path, check=True)
    state_path = tmp_path / "tournament/top40/run_state.json"
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps(
            {
                "phase": "research",
                "teams": {
                    "team-01": {
                        "qr": "pending",
                        "qe": "pending",
                        "canonical_run": "pending",
                        "champion": None,
                        "reviews": {},
                        "oos_accesses": [],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    artifacts = cli.canonical_artifact_paths("team-01")
    for name in cli.QR_EVIDENCE:
        path = tmp_path / artifacts[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"QR {name}\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "QR evidence"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)
    with pytest.raises(ValueError, match="before the QR handoff"):
        cli._mark_review(argparse.Namespace(team_id="team-01", role="qe"))
    assert cli._mark_review(argparse.Namespace(team_id="team-01", role="qr")) == 0
    subprocess.run(["git", "add", str(state_path)], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "QR review"], cwd=tmp_path, check=True)
    for name in cli.QE_EVIDENCE:
        path = tmp_path / artifacts[name]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"QE {name}\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "QE evidence"], cwd=tmp_path, check=True)
    assert cli._mark_review(argparse.Namespace(team_id="team-01", role="qe")) == 0
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["teams"]["team-01"]["qr"] == "complete"
    assert state["teams"]["team-01"]["qe"] == "complete"
    qr_hashes = state["teams"]["team-01"]["reviews"]["qr"]["evidence_sha256"]
    assert (
        qr_hashes[artifacts["research_brief"]]
        == hashlib.sha256((tmp_path / artifacts["research_brief"]).read_bytes()).hexdigest()
    )


def test_freeze_team_enforces_ten_champion_barrier(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Top40 Test"], cwd=tmp_path, check=True)
    teams = {}
    for team_id in cli.TEAM_IDS:
        strategy = tmp_path / cli.canonical_artifact_paths(team_id)["strategy_source"]
        strategy.parent.mkdir(parents=True, exist_ok=True)
        strategy.write_text(f"# {team_id}\n", encoding="utf-8")
        teams[team_id] = {
            "qr": "complete",
            "qe": "complete",
            "canonical_run": "pending",
            "freeze_commit": None,
            "champion": None,
            "reviews": {},
            "oos_accesses": [],
        }
    state_path = tmp_path / "tournament/top40/run_state.json"
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({"phase": "research", "teams": teams}), encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "team inputs"], cwd=tmp_path, check=True)
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)
    monkeypatch.setattr(cli, "_verify_review_evidence", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cli, "_verify_research_journal_git_history", lambda *_args, **_kwargs: None)

    def validated(root, team_id, _commit, _state):
        return cli.canonical_artifact_paths(team_id), {}, 1

    monkeypatch.setattr(cli, "_validate_team_freeze_inputs", validated)
    for team_id in cli.TEAM_IDS[:-1]:
        cli._freeze_team(
            argparse.Namespace(
                team_id=team_id,
                strategy_name=f"strategy-{team_id}",
                freeze_commit=commit,
            )
        )
    assert json.loads(state_path.read_text(encoding="utf-8"))["phase"] == "research"
    with pytest.raises(ValueError, match="all ten champion SHAs"):
        cli._finalize_team(argparse.Namespace(team_id="team-01"))

    cli._freeze_team(
        argparse.Namespace(
            team_id="team-10", strategy_name="strategy-team-10", freeze_commit=commit
        )
    )
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase"] == "cohort_frozen"
    assert all(isinstance(team["champion"], dict) for team in state["teams"].values())


def test_phase0_freeze_is_branch_bound_and_single_shot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Top40 Test"], cwd=tmp_path, check=True)
    marker = tmp_path / "marker"
    marker.write_text("initial\n", encoding="utf-8")
    subprocess.run(["git", "add", "marker"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=tmp_path, check=True)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="only on branch"):
        cli._freeze_phase0(argparse.Namespace())

    subprocess.run(["git", "checkout", "-qb", cli.TOURNAMENT_BRANCH], cwd=tmp_path, check=True)
    freeze = tmp_path / cli.PHASE0_FREEZE_PATH
    freeze.parent.mkdir(parents=True)
    freeze.write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="single-shot"):
        cli._freeze_phase0(argparse.Namespace())


def test_common_phase0_fault_aborts_validation_and_scoring(monkeypatch, tmp_path):
    cli = _load_cli_module()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        cli,
        "verify_phase0_freeze",
        lambda **_kwargs: (cli.ValidationIssue("orchestrator_sha256", "mutated CLI"),),
    )
    with pytest.raises(ValueError, match="Phase-0 freeze verification failed"):
        cli._validate(["missing.json"])
    with pytest.raises(ValueError, match="Phase-0 freeze verification failed"):
        cli._score(
            argparse.Namespace(
                submissions=[],
                provisional=True,
                critic_adjudications=None,
                critic_scores=None,
                user_scores=None,
                json_out=None,
                csv_out=None,
            )
        )


def test_critic_lock_is_single_shot_hash_bound_and_precedes_user_ballot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Top40 Test"], cwd=tmp_path, check=True)
    state_path = tmp_path / cli.RUN_STATE_PATH
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps({"phase": "objective_locked", "critic_lock": None}),
        encoding="utf-8",
    )
    objective_path = tmp_path / cli.OBJECTIVE_LOCK_PATH
    objective_path.write_text("{}\n", encoding="utf-8")
    subprocess.run(
        ["git", "add", cli.RUN_STATE_PATH, cli.OBJECTIVE_LOCK_PATH],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "commit", "-qm", "objective lock"], cwd=tmp_path, check=True)
    objective_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    scores_path = tmp_path / cli.CRITIC_SCORES_PATH
    scores_path.write_text(
        json.dumps({team_id: 7.5 for team_id in cli.TEAM_IDS}),
        encoding="utf-8",
    )
    adjudications_path = tmp_path / cli.CRITIC_ADJUDICATIONS_PATH
    adjudications_path.write_text("{}\n", encoding="utf-8")
    submissions = _valid_submissions()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)
    monkeypatch.setattr(cli, "_locked_cohort", lambda _root: submissions)
    monkeypatch.setattr(
        cli,
        "_verify_objective_lock",
        lambda _root, _state: (submissions, {}, objective_commit),
    )
    monkeypatch.setattr(
        cli,
        "_critic_adjudication_issues",
        lambda _path, _submissions, _root: {team_id: () for team_id in cli.TEAM_IDS},
    )
    args = argparse.Namespace(
        critic_scores=cli.CRITIC_SCORES_PATH,
        critic_adjudications=cli.CRITIC_ADJUDICATIONS_PATH,
    )

    assert cli._lock_critic(args) == 0
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["phase"] == "critic_locked"
    lock_path = tmp_path / cli.CRITIC_LOCK_PATH
    assert state["critic_lock"]["sha256"] == hashlib.sha256(lock_path.read_bytes()).hexdigest()
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "critic lock"], cwd=tmp_path, check=True)
    cli._verify_critic_lock(
        tmp_path,
        state,
        submissions,
        cli.CRITIC_SCORES_PATH,
        cli.CRITIC_ADJUDICATIONS_PATH,
    )

    scores_path.write_text(
        json.dumps({team_id: 8.0 for team_id in cli.TEAM_IDS}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="bytes changed"):
        cli._verify_critic_lock(
            tmp_path,
            state,
            submissions,
            cli.CRITIC_SCORES_PATH,
            cli.CRITIC_ADJUDICATIONS_PATH,
        )


def test_critic_lock_refuses_a_preexisting_user_ballot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    state_path = tmp_path / cli.RUN_STATE_PATH
    state_path.parent.mkdir(parents=True)
    state_path.write_text(json.dumps({"phase": "objective_locked"}), encoding="utf-8")
    user_path = tmp_path / cli.USER_SCORES_PATH
    user_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)

    with pytest.raises(ValueError, match="must not exist before Critic lock"):
        cli._lock_critic(
            argparse.Namespace(
                critic_scores=cli.CRITIC_SCORES_PATH,
                critic_adjudications=cli.CRITIC_ADJUDICATIONS_PATH,
            )
        )


def test_final_scoring_stops_if_critic_would_eliminate_every_mechanical_team(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    submissions = _valid_submissions()
    scores_path = tmp_path / cli.CRITIC_SCORES_PATH
    scores_path.parent.mkdir(parents=True)
    scores_path.write_text(
        json.dumps({team_id: 5.0 for team_id in cli.TEAM_IDS}),
        encoding="utf-8",
    )
    (tmp_path / cli.CRITIC_ADJUDICATIONS_PATH).write_text("{}\n", encoding="utf-8")
    user_path = tmp_path / cli.USER_SCORES_PATH
    user_path.write_text(
        json.dumps({team_id: 5.0 for team_id in cli.TEAM_IDS}),
        encoding="utf-8",
    )
    finding = cli.ValidationIssue("critic_future_data", "manual review required")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)
    monkeypatch.setattr(cli, "_read_state", lambda _root: {"phase": "user_locked"})
    monkeypatch.setattr(cli, "_locked_cohort", lambda _root: submissions)
    monkeypatch.setattr(
        cli,
        "_verify_user_ballot_lock",
        lambda *_args, **_kwargs: (
            {team_id: (finding,) for team_id in cli.TEAM_IDS},
            "a" * 40,
        ),
    )

    with pytest.raises(ValueError, match="suspended for manual integrity adjudication"):
        cli._score(
            argparse.Namespace(
                submissions=[
                    f"tournament/top40/teams/{team_id}/submission.json" for team_id in cli.TEAM_IDS
                ],
                provisional=False,
                critic_adjudications=cli.CRITIC_ADJUDICATIONS_PATH,
                critic_scores=cli.CRITIC_SCORES_PATH,
                user_scores=cli.USER_SCORES_PATH,
                json_out=None,
                csv_out=None,
            )
        )


def test_first_add_lock_rejects_any_later_committed_modification(tmp_path: Path):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Top40 Test"], cwd=tmp_path, check=True)
    marker = tmp_path / "marker"
    marker.write_text("base\n", encoding="utf-8")
    subprocess.run(["git", "add", "marker"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    parent = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    lock = tmp_path / "lock.json"
    lock.write_text('{"version": 1}\n', encoding="utf-8")
    subprocess.run(["git", "add", "lock.json"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "first add lock"], cwd=tmp_path, check=True)
    assert (
        cli._unique_first_add_commit(
            tmp_path,
            "lock.json",
            expected_parent=parent,
            label="test lock",
        )
        == subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    lock.write_text('{"version": 2}\n', encoding="utf-8")
    subprocess.run(["git", "add", "lock.json"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "forbidden lock rewrite"], cwd=tmp_path, check=True)
    with pytest.raises(ValueError, match="exactly one first-add"):
        cli._unique_first_add_commit(
            tmp_path,
            "lock.json",
            expected_parent=parent,
            label="test lock",
        )


def test_independent_canonical_runs_require_equal_fields_and_file_hashes():
    cli = _load_cli_module()

    class Result:
        def __init__(self, value: int):
            self.value = value

        def submission_fields(self):
            return {"value": self.value}

    entries = [{"path": "report.csv", "size": 10, "sha256": "a" * 64}]
    cli._verify_independent_canonical_runs(
        Result(1), Result(1), "b" * 64, "b" * 64, entries, entries
    )
    with pytest.raises(ValueError, match="byte-for-byte deterministic"):
        cli._verify_independent_canonical_runs(
            Result(1), Result(2), "b" * 64, "b" * 64, entries, entries
        )
    with pytest.raises(ValueError, match="byte-for-byte deterministic"):
        cli._verify_independent_canonical_runs(
            Result(1), Result(1), "b" * 64, "c" * 64, entries, entries
        )


def test_unconfirmed_critic_finding_cannot_disqualify(tmp_path: Path):
    cli = _load_cli_module()
    submission = _valid_submissions(1)[0]
    finding = cli.ValidationIssue("critic_future_data", "alleged future leak")
    lock_sha = "a" * 64
    path = tmp_path / "confirmations.json"
    payload = {
        "schema_version": 1,
        "confirmed_by": "organizer-user",
        "critic_lock_sha256": lock_sha,
        "cohort_sha256": cli._cohort_sha256([submission]),
        "teams": {
            submission.team_id: {
                "freeze_commit": submission.freeze_commit,
                "artifact_manifest_sha256": submission.artifact_manifest_sha256,
                "confirmed_codes": [],
            }
        },
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    issues = cli._confirmed_critic_issues(
        path,
        [submission],
        {submission.team_id: (finding,)},
        lock_sha,
    )
    assert issues[submission.team_id] == ()
    payload["teams"][submission.team_id]["confirmed_codes"] = ["critic_future_data"]
    path.write_text(json.dumps(payload), encoding="utf-8")
    issues = cli._confirmed_critic_issues(
        path,
        [submission],
        {submission.team_id: (finding,)},
        lock_sha,
    )
    assert issues[submission.team_id] == (finding,)


def test_next_utc_8h_boundary_is_strict_even_on_an_exact_boundary():
    cli = _load_cli_module()
    exact = datetime(2026, 7, 13, 16, tzinfo=UTC)
    assert cli._next_utc_8h_boundary(exact) == datetime(2026, 7, 14, tzinfo=UTC)
    assert cli._next_utc_8h_boundary(
        datetime(2026, 7, 13, 7, 59, 59, 999999, tzinfo=UTC)
    ) == datetime(2026, 7, 13, 8, tzinfo=UTC)
    with pytest.raises(ValueError, match="timezone-aware"):
        cli._next_utc_8h_boundary(datetime(2026, 7, 13, 12))


def test_winner_freeze_is_single_shot_commit_bound_and_paper_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "Top40 Test"], cwd=tmp_path, check=True)
    team_id = "team-01"
    team_dir = tmp_path / f"tournament/top40/teams/{team_id}"
    team_dir.mkdir(parents=True)
    (team_dir / "strategy.py").write_text("# immutable helper tree\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "winner logic freeze"], cwd=tmp_path, check=True)
    winner_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    winner = dataclasses.replace(_valid_submissions(1)[0], freeze_commit=winner_commit)
    state_path = tmp_path / cli.RUN_STATE_PATH
    critic_lock = {
        "path": cli.CRITIC_LOCK_PATH,
        "sha256": "1" * 64,
        "cohort_sha256": "2" * 64,
        "locked_at_utc": "2026-07-13T12:00:00+00:00",
    }
    state_path.write_text(
        json.dumps({"phase": "user_locked", "critic_lock": critic_lock}), encoding="utf-8"
    )
    artifact_manifest = tmp_path / winner.artifacts["artifact_manifest"]
    artifact_manifest.write_text(
        json.dumps([{"path": "reports-top40/team-01/returns.csv", "size": 7, "sha256": "a" * 64}])
        + "\n",
        encoding="utf-8",
    )
    submission_path = team_dir / "submission.json"
    submission_path.write_text('{"bound": true}\n', encoding="utf-8")
    phase0 = {
        "common_freeze_commit": winner_commit,
        "data_manifest_sha256": "a" * 64,
        "evaluator_sha256": "b" * 64,
        "methodology_sha256": "c" * 64,
        "config_sha256": "d" * 64,
        "snapshot_builder_sha256": "e" * 64,
        "root_dependency_lock_sha256": "f" * 64,
        "orchestrator_sha256": "0" * 64,
    }
    (tmp_path / cli.PHASE0_FREEZE_PATH).write_text(json.dumps(phase0) + "\n", encoding="utf-8")
    source_config = Path(__file__).parents[2] / "tournament/top40/config.toml"
    (tmp_path / cli.CANONICAL_CONFIG_PATH).write_text(
        source_config.read_text(encoding="utf-8"), encoding="utf-8"
    )
    final_payload = {
        "status": "FINAL",
        "cohort_sha256": "3" * 64,
        "leaderboard": [{"team_id": team_id, "valid": True, "rank": 1}],
        "raw_metrics": {},
        "ballot_hashes": {
            "critic_lock_sha256": "4" * 64,
            "critic_scores_sha256": "5" * 64,
            "critic_adjudications_sha256": "6" * 64,
            "user_scores_sha256": "7" * 64,
        },
    }
    (tmp_path / cli.FINAL_SCORE_PATH).write_text(
        json.dumps(final_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    for relative in (
        cli.OBJECTIVE_LOCK_PATH,
        cli.CRITIC_LOCK_PATH,
        cli.CRITIC_SCORES_PATH,
        cli.CRITIC_ADJUDICATIONS_PATH,
        cli.CRITIC_CONFIRMATIONS_PATH,
        cli.CRITIC_CONFIRMATION_LOCK_PATH,
        cli.USER_SCORES_PATH,
        cli.USER_BALLOT_LOCK_PATH,
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "committed final selection"], cwd=tmp_path, check=True)
    selection_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)
    monkeypatch.setattr(
        cli,
        "_verified_final_score",
        lambda _root, _state, **_kwargs: (final_payload, [winner], winner),
    )
    monkeypatch.setattr(cli, "verify_team_freeze", lambda *_args, **_kwargs: ())
    monkeypatch.setattr(cli, "verify_canonical_artifacts", lambda *_args, **_kwargs: ())

    assert cli._freeze_winner(argparse.Namespace()) == 0
    state = json.loads(state_path.read_text(encoding="utf-8"))
    record_path = tmp_path / cli.WINNER_FREEZE_PATH
    record = json.loads(record_path.read_text(encoding="utf-8"))
    assert state["phase"] == "paper_frozen"
    assert state["winner_freeze"]["sha256"] == hashlib.sha256(record_path.read_bytes()).hexdigest()
    assert record["selection_record_commit"] == selection_commit
    assert record["winner"]["freeze_commit"] == winner_commit
    assert record["forward_paper"]["execution_mode"] == "paper-only"
    assert record["forward_paper"]["live_orders_allowed"] is False
    frozen = datetime.fromisoformat(record["frozen_at_utc"])
    start = datetime.fromisoformat(record["forward_paper"]["start_utc"])
    assert start == cli._next_utc_8h_boundary(frozen)
    assert record["quarantine"]["end_exclusive_utc"] == record["forward_paper"]["start_utc"]
    with pytest.raises(ValueError, match="single-shot|user_locked"):
        cli._freeze_winner(argparse.Namespace())

    subprocess.run(
        ["git", "add", cli.RUN_STATE_PATH, cli.WINNER_FREEZE_PATH],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(["git", "commit", "-qm", "seal forward paper handoff"], cwd=tmp_path, check=True)
    assert cli._verify_winner_freeze(argparse.Namespace()) == 0

    record["forward_paper"]["start_utc"] = "2026-07-14T09:00:00+00:00"
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="tracked, committed, and clean|run_state differs"):
        cli._verify_winner_freeze(argparse.Namespace())


def test_final_scoring_rejects_noncanonical_submission_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    cli = _load_cli_module()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(cli, "_require_phase0", lambda _root: None)
    monkeypatch.setattr(cli, "_read_state", lambda _root: {"phase": "user_locked"})
    alternate = tmp_path / "alternate.json"
    alternate.write_text("{}\n", encoding="utf-8")

    with pytest.raises(ValueError, match="ten canonical locked submission paths"):
        cli._score(
            argparse.Namespace(
                submissions=[str(alternate)] * 10,
                provisional=False,
                critic_adjudications=cli.CRITIC_ADJUDICATIONS_PATH,
                critic_scores=cli.CRITIC_SCORES_PATH,
                user_scores=cli.USER_SCORES_PATH,
                json_out=None,
                csv_out=None,
            )
        )
