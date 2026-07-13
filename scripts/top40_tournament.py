"""Build, run, validate, and score the Binance Top-40 tournament."""

from __future__ import annotations

import argparse
import base64
import csv
import dataclasses
import fcntl
import hashlib
import json
import math
import os
import re
import resource
import subprocess
import tempfile
import time
import tomllib
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path

from crypto_trade.tournament.top40 import (
    CANONICAL_CONFIG_PATH,
    CANONICAL_MANIFEST_PATH,
    CRITIC_ADJUDICATIONS_PATH,
    CRITIC_CONFIRMATION_LOCK_PATH,
    CRITIC_CONFIRMATIONS_PATH,
    CRITIC_INTEGRITY_DQ_CODES,
    CRITIC_LOCK_PATH,
    CRITIC_SCORES_PATH,
    EVALUATOR_SOURCE_PATHS,
    FINAL_SCORE_PATH,
    IS_START,
    METHODOLOGY_PATHS,
    OBJECTIVE_LOCK_PATH,
    ORCHESTRATOR_SCRIPT_PATH,
    PHASE0_FREEZE_PATH,
    ROOT_DEPENDENCY_LOCK_PATH,
    RUN_STATE_PATH,
    TEAM_SOURCE_POLICY,
    TOURNAMENT_BRANCH,
    USER_BALLOT_LOCK_PATH,
    USER_SCORES_PATH,
    WINNER_FREEZE_PATH,
    EvaluationWindow,
    Submission,
    ValidationIssue,
    WindowMetrics,
    canonical_artifact_paths,
    load_submission,
    score_as_dict,
    score_tournament,
    validate_submission,
    verify_canonical_artifacts,
    verify_phase0_freeze,
    verify_team_freeze,
)

TEAM_IDS = tuple(f"team-{number:02d}" for number in range(1, 11))
QR_EVIDENCE = (
    "research_brief",
    "provenance",
    "feature_lineage",
    "ablations",
    "trial_ledger",
)
QE_EVIDENCE = (
    "strategy_source",
    "team_source_manifest",
    "dependency_lock",
    "frozen_config",
    "audit_report",
    "compliance_evidence",
)
ORGANIZER_RESEARCH_JOURNAL_PATH = "tournament/top40/organizer_research_journal.jsonl"
_JOURNAL_ZERO_HASH = "0" * 64
_JOURNAL_RECORD_KEYS = {
    "schema_version",
    "sequence",
    "event_type",
    "timestamp_utc",
    "previous_record_sha256",
    "payload",
    "record_sha256",
}
_JOURNAL_RESULT_PAYLOAD_KEYS = {
    "run_id",
    "team_id",
    "candidate_id",
    "status",
    "failure_type",
    "cpu_hours",
    "wall_clock_hours",
    "source_bundle_sha256",
    "canonical_metrics",
    "artifact_hashes",
    "artifact_sizes",
    "decision_count",
    "event_count",
    "trade_count",
    "team_result_bytes_base64",
    "team_result_sha256",
}
_TEAM_RESULT_EVENT_KEYS = {
    "event_id",
    "candidate_id",
    "event_type",
    "timestamp_utc",
    "cpu_hours",
    "wall_clock_hours",
    "is_metrics",
    "public_oos_accessed",
    "public_oos_metrics",
    "disposition",
    "artifact_hashes",
}


def _atomic_write_json(path: Path, payload: object) -> None:
    """Replace an organizer-owned JSON file atomically on its existing filesystem."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    """Atomically replace one organizer-owned byte stream and fsync its contents."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _journal_record(
    sequence: int,
    event_type: str,
    timestamp_utc: str,
    previous_record_sha256: str,
    payload: Mapping[str, object],
) -> tuple[dict[str, object], bytes]:
    core: dict[str, object] = {
        "schema_version": 1,
        "sequence": sequence,
        "event_type": event_type,
        "timestamp_utc": timestamp_utc,
        "previous_record_sha256": previous_record_sha256,
        "payload": dict(payload),
    }
    record_sha256 = hashlib.sha256(_canonical_json_bytes(core)).hexdigest()
    record = {**core, "record_sha256": record_sha256}
    return record, _canonical_json_bytes(record) + b"\n"


def _new_research_journal() -> tuple[dict[str, object], bytes, dict[str, object]]:
    timestamp = datetime.now(UTC).isoformat()
    record, raw_line = _journal_record(
        0,
        "genesis",
        timestamp,
        _JOURNAL_ZERO_HASH,
        {"branch": TOURNAMENT_BRANCH, "team_ids": list(TEAM_IDS)},
    )
    digest = str(record["record_sha256"])
    state = {
        "schema_version": 1,
        "path": ORGANIZER_RESEARCH_JOURNAL_PATH,
        "record_count": 1,
        "genesis_sha256": digest,
        "head_sha256": digest,
    }
    return record, raw_line, state


def _validate_research_journal_chain(root: Path) -> list[dict]:
    """Verify the independent, normalized organizer write-ahead journal."""
    path = root / ORGANIZER_RESEARCH_JOURNAL_PATH
    if not path.is_file() or path.is_symlink():
        raise ValueError("organizer research journal is missing or unsafe")
    raw_lines = path.read_bytes().splitlines(keepends=True)
    if not raw_lines or any(not line.endswith(b"\n") for line in raw_lines):
        raise ValueError("organizer research journal must use newline-terminated records")

    records: list[dict] = []
    previous_hash = _JOURNAL_ZERO_HASH
    previous_timestamp: datetime | None = None
    reservations: dict[str, dict] = {}
    results: set[str] = set()
    for sequence, raw_line in enumerate(raw_lines):
        try:
            record = json.loads(raw_line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"organizer journal record {sequence} is invalid JSON") from exc
        if not isinstance(record, dict) or set(record) != _JOURNAL_RECORD_KEYS:
            raise ValueError(f"organizer journal record {sequence} has an invalid schema")
        if raw_line != _canonical_json_bytes(record) + b"\n":
            raise ValueError(f"organizer journal record {sequence} is not canonically encoded")
        core = {name: value for name, value in record.items() if name != "record_sha256"}
        digest = hashlib.sha256(_canonical_json_bytes(core)).hexdigest()
        if (
            record["schema_version"] != 1
            or record["sequence"] != sequence
            or record["previous_record_sha256"] != previous_hash
            or record["record_sha256"] != digest
        ):
            raise ValueError(f"organizer journal hash chain breaks at record {sequence}")
        timestamp = _utc_timestamp(
            record["timestamp_utc"], f"organizer journal record {sequence}.timestamp_utc"
        )
        if previous_timestamp is not None and timestamp < previous_timestamp:
            raise ValueError("organizer research journal timestamps are not monotonic")
        previous_timestamp = timestamp
        event_type = record["event_type"]
        payload = record["payload"]
        if not isinstance(payload, dict):
            raise ValueError(f"organizer journal record {sequence} payload must be an object")
        if sequence == 0:
            if event_type != "genesis" or payload != {
                "branch": TOURNAMENT_BRANCH,
                "team_ids": list(TEAM_IDS),
            }:
                raise ValueError("organizer research journal has an invalid genesis record")
        elif event_type == "reservation":
            run_id = payload.get("run_id")
            team_id = payload.get("team_id")
            candidate_id = payload.get("candidate_id")
            if (
                not isinstance(run_id, str)
                or not re.fullmatch(r"[0-9a-f]{64}", run_id)
                or run_id in reservations
                or team_id not in TEAM_IDS
                or not isinstance(candidate_id, str)
                or not candidate_id
                or any(
                    prior.get("team_id") == team_id and prior.get("candidate_id") == candidate_id
                    for prior in reservations.values()
                )
            ):
                raise ValueError("organizer journal has a malformed/duplicate reservation")
            registration_b64 = payload.get("registration_bytes_base64")
            registration_sha = payload.get("registration_sha256")
            try:
                registration_bytes = base64.b64decode(registration_b64, validate=True)
            except (TypeError, ValueError) as exc:
                raise ValueError("organizer reservation registration bytes are invalid") from exc
            if (
                len(registration_bytes.splitlines(keepends=True)) != 1
                or not registration_bytes.endswith(b"\n")
                or hashlib.sha256(registration_bytes).hexdigest() != registration_sha
            ):
                raise ValueError("organizer reservation registration hash differs from its bytes")
            ledger_size = payload.get("team_ledger_size")
            ledger_sha256 = payload.get("team_ledger_sha256")
            if (
                isinstance(ledger_size, bool)
                or not isinstance(ledger_size, int)
                or ledger_size < len(registration_bytes)
                or not isinstance(ledger_sha256, str)
                or re.fullmatch(r"[0-9a-f]{64}", ledger_sha256) is None
            ):
                raise ValueError("organizer reservation ledger prefix binding is invalid")
            reservations[run_id] = payload
        elif event_type == "result":
            run_id = payload.get("run_id")
            if run_id not in reservations or run_id in results:
                raise ValueError("organizer journal result has no unique prior reservation")
            reservation = reservations[run_id]
            if any(
                payload.get(name) != reservation.get(name) for name in ("team_id", "candidate_id")
            ):
                raise ValueError("organizer journal result differs from its reservation identity")
            if set(payload) != _JOURNAL_RESULT_PAYLOAD_KEYS or payload.get("status") not in {
                "completed",
                "failed",
            }:
                raise ValueError("organizer journal result status is invalid")
            team_result_b64 = payload.get("team_result_bytes_base64")
            team_result_sha256 = payload.get("team_result_sha256")
            try:
                team_result_bytes = base64.b64decode(team_result_b64, validate=True)
            except (TypeError, ValueError) as exc:
                raise ValueError("organizer result team bytes are invalid") from exc
            if (
                len(team_result_bytes.splitlines(keepends=True)) != 1
                or not team_result_bytes.endswith(b"\n")
                or hashlib.sha256(team_result_bytes).hexdigest() != team_result_sha256
            ):
                raise ValueError("organizer result team bytes differ from their hash")
            try:
                team_result = json.loads(team_result_bytes)
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("organizer result team bytes are invalid JSON") from exc
            if (
                not isinstance(team_result, dict)
                or set(team_result) != _TEAM_RESULT_EVENT_KEYS
                or team_result_bytes != _canonical_json_bytes(team_result) + b"\n"
                or team_result.get("event_id") != f"organizer-{run_id}-result"
                or team_result.get("candidate_id") != reservation.get("candidate_id")
                or team_result.get("event_type") != "result"
                or team_result.get("timestamp_utc") != record["timestamp_utc"]
                or team_result.get("public_oos_accessed") is not True
            ):
                raise ValueError("organizer result team event is not canonical or identity-bound")
            status = payload["status"]
            failure_type = payload.get("failure_type")
            if (status == "failed") != (
                isinstance(failure_type, str) and bool(failure_type)
            ) or payload.get("source_bundle_sha256") != reservation.get("source_bundle_sha256"):
                raise ValueError("organizer result status/source binding is invalid")
            for resource_name in ("cpu_hours", "wall_clock_hours"):
                value = payload.get(resource_name)
                if (
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(float(value))
                    or float(value) < 0.0
                ):
                    raise ValueError("organizer result resource accounting is invalid")
            metrics = payload.get("canonical_metrics")
            if metrics is None:
                expected_is = None
                expected_oos = None
            else:
                try:
                    expected_is = metrics["in_sample"]["metrics"]
                    expected_oos = metrics["public_oos"]["metrics"]
                except (KeyError, TypeError) as exc:
                    raise ValueError("organizer result canonical metrics are malformed") from exc
            expected_disposition = (
                "organizer_completed"
                if status == "completed"
                else f"organizer_failed:{failure_type}"
            )
            if any(
                team_result.get(name) != value
                for name, value in {
                    "cpu_hours": payload["cpu_hours"],
                    "wall_clock_hours": payload["wall_clock_hours"],
                    "is_metrics": expected_is,
                    "public_oos_metrics": expected_oos,
                    "disposition": expected_disposition,
                    "artifact_hashes": payload["artifact_hashes"],
                }.items()
            ):
                raise ValueError("organizer result team event differs from journal accounting")
            results.add(run_id)
        else:
            raise ValueError(f"organizer journal event type is invalid at record {sequence}")
        previous_hash = digest
        records.append(record)

    return records


def _research_journal_anchor(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    if not records:
        raise ValueError("organizer research journal cannot be empty")
    return {
        "schema_version": 1,
        "path": ORGANIZER_RESEARCH_JOURNAL_PATH,
        "record_count": len(records),
        "genesis_sha256": records[0]["record_sha256"],
        "head_sha256": records[-1]["record_sha256"],
    }


def _validate_research_journal_prefix(
    records: Sequence[Mapping[str, object]], state: Mapping[str, object]
) -> int:
    """Require the mutable anchor to identify one exact prefix of the journal."""
    journal_state = state.get("research_journal")
    expected_state_keys = {
        "schema_version",
        "path",
        "record_count",
        "genesis_sha256",
        "head_sha256",
    }
    if not isinstance(journal_state, Mapping) or set(journal_state) != expected_state_keys:
        raise ValueError("run_state research_journal anchor is missing or malformed")
    count = journal_state.get("record_count")
    if (
        journal_state.get("schema_version") != 1
        or journal_state.get("path") != ORGANIZER_RESEARCH_JOURNAL_PATH
        or isinstance(count, bool)
        or not isinstance(count, int)
        or count < 1
        or count > len(records)
    ):
        raise ValueError("run_state research_journal anchor is not a valid journal prefix")
    if records[0]["record_sha256"] != journal_state.get("genesis_sha256"):
        raise ValueError("organizer journal genesis differs from run_state")
    if records[count - 1]["record_sha256"] != journal_state.get("head_sha256"):
        raise ValueError("organizer journal prefix head differs from run_state")
    return count


def _validate_research_journal(root: Path, state: Mapping[str, object]) -> list[dict]:
    """Verify the journal and require run state to anchor its current head exactly."""
    records = _validate_research_journal_chain(root)
    count = _validate_research_journal_prefix(records, state)
    if count != len(records):
        raise ValueError("organizer journal record count differs from run_state")
    return records


def _append_research_journal_locked(
    root: Path,
    state: dict,
    event_type: str,
    payload: Mapping[str, object],
    *,
    timestamp: datetime,
) -> dict:
    records = _validate_research_journal(root, state)
    journal_state = state["research_journal"]
    record, raw_line = _journal_record(
        len(records),
        event_type,
        timestamp.astimezone(UTC).isoformat(),
        str(journal_state["head_sha256"]),
        payload,
    )
    path = root / ORGANIZER_RESEARCH_JOURNAL_PATH
    with path.open("ab", buffering=0) as handle:
        handle.write(raw_line)
        os.fsync(handle.fileno())
    journal_state["record_count"] = len(records) + 1
    journal_state["head_sha256"] = record["record_sha256"]
    return record


def _organizer_runs(records: Sequence[Mapping[str, object]]) -> dict[str, dict[str, dict]]:
    """Index complete organizer reservation/result pairs by team and candidate."""
    by_run: dict[str, dict[str, dict]] = {}
    for record in records[1:]:
        payload = record["payload"]
        assert isinstance(payload, dict)
        run_id = payload["run_id"]
        item = by_run.setdefault(run_id, {})
        item[str(record["event_type"])] = {
            "record_sha256": record["record_sha256"],
            "timestamp_utc": record["timestamp_utc"],
            "payload": payload,
        }
    output: dict[str, dict[str, dict]] = {team_id: {} for team_id in TEAM_IDS}
    for item in by_run.values():
        reservation = item.get("reservation")
        if reservation is None:
            continue
        payload = reservation["payload"]
        output[payload["team_id"]][payload["candidate_id"]] = item
    return output


def _verify_git_append_only_path(
    root: Path,
    relative: str,
    *,
    initial_commit: str | None = None,
    initial_bytes: bytes | None = None,
) -> None:
    """Require every reachable version of one file to be a complete strict byte append."""
    head = _head_commit(root)
    current = (root / relative).read_bytes()
    if initial_commit is None:
        revision = head
        previous: bytes | None = None
    else:
        revision = f"{initial_commit}..{head}"
        previous = initial_bytes
        if previous is None:
            raise ValueError("append-only history requires initial bytes with an initial commit")
    history = subprocess.run(
        [
            "git",
            "log",
            "--format=%H",
            "--reverse",
            "--topo-order",
            revision,
            "--",
            relative,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    for commit in history:
        committed = _git_file_bytes(root, commit, relative)
        if committed and not committed.endswith(b"\n"):
            raise ValueError(f"append-only Git history has a partial line: {relative}")
        if previous is not None and (
            len(committed) <= len(previous) or not committed.startswith(previous)
        ):
            raise ValueError(f"append-only Git history rewrites or truncates {relative}")
        if not current.startswith(committed):
            raise ValueError(f"append-only Git history rewrites or truncates {relative}")
        previous = committed
    if previous is None or previous != current:
        raise ValueError(f"current append-only bytes are not committed at HEAD: {relative}")


def _verify_research_journal_git_history(
    root: Path,
    state: Mapping[str, object],
    *,
    affected_team_ids: Sequence[str],
) -> None:
    """Anchor accounting to Git and reject every committed rewrite or truncation."""
    records = _validate_research_journal(root, state)
    try:
        phase0 = json.loads((root / PHASE0_FREEZE_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot verify research journal Git history: {exc}") from exc
    if not isinstance(phase0, dict) or not isinstance(phase0.get("common_freeze_commit"), str):
        raise ValueError("Phase-0 freeze has no common commit for journal history")
    common = subprocess.run(
        ["git", "rev-parse", f"{phase0['common_freeze_commit']}^{{commit}}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    head = _head_commit(root)
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", common, head],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise ValueError("Phase-0 common commit is not an ancestor of the accounting commit")

    genesis_bytes = _canonical_json_bytes(records[0]) + b"\n"
    common_journal = _git_file_bytes(root, common, ORGANIZER_RESEARCH_JOURNAL_PATH)
    if common_journal != genesis_bytes:
        raise ValueError("organizer journal genesis is not exact at the Phase-0 common commit")
    try:
        common_state = json.loads(_git_file_bytes(root, common, RUN_STATE_PATH))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("Phase-0 common run_state cannot anchor journal genesis") from exc
    common_anchor = common_state.get("research_journal") if isinstance(common_state, dict) else None
    current_anchor = state.get("research_journal")
    if (
        not isinstance(common_anchor, dict)
        or not isinstance(current_anchor, Mapping)
        or common_anchor.get("record_count") != 1
        or common_anchor.get("head_sha256") != records[0]["record_sha256"]
        or common_anchor.get("genesis_sha256") != records[0]["record_sha256"]
        or common_anchor.get("path") != ORGANIZER_RESEARCH_JOURNAL_PATH
        or common_anchor.get("genesis_sha256") != current_anchor.get("genesis_sha256")
    ):
        raise ValueError("Phase-0 common run_state does not anchor the journal genesis")

    affected = tuple(dict.fromkeys(affected_team_ids))
    if any(team_id not in TEAM_IDS for team_id in affected):
        raise ValueError("affected journal team ID is invalid")
    required_paths = [
        ORGANIZER_RESEARCH_JOURNAL_PATH,
        RUN_STATE_PATH,
        *(canonical_artifact_paths(team_id)["trial_ledger"] for team_id in affected),
    ]
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", *required_paths],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    if status.strip():
        raise ValueError(
            "commit the organizer journal, run_state, and affected experiments.jsonl "
            "before freeze-team"
        )
    for relative in required_paths:
        path = root / relative
        if (
            not path.is_file()
            or path.is_symlink()
            or _git_file_bytes(root, head, relative) != path.read_bytes()
        ):
            raise ValueError(f"accounting input is not clean and committed at HEAD: {relative}")
    _verify_git_append_only_path(
        root,
        ORGANIZER_RESEARCH_JOURNAL_PATH,
        initial_commit=common,
        initial_bytes=common_journal,
    )
    for team_id in affected:
        relative = canonical_artifact_paths(team_id)["trial_ledger"]
        _verify_git_append_only_path(root, relative)
        team = state.get("teams", {}).get(team_id)
        champion = team.get("champion") if isinstance(team, Mapping) else None
        freeze_commit = champion.get("freeze_commit") if isinstance(champion, Mapping) else None
        if (
            isinstance(freeze_commit, str)
            and _git_file_bytes(root, freeze_commit, relative) != (root / relative).read_bytes()
        ):
            raise ValueError(f"frozen team experiment ledger changed after freeze: {team_id}")


def _state_lock_path(root: Path) -> Path:
    result = subprocess.run(
        ["git", "rev-parse", "--git-path", "top40-run-state.lock"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    path = Path(result.stdout.strip())
    return path if path.is_absolute() else root / path


@contextmanager
def _edit_run_state(root: Path) -> Iterator[dict]:
    """Serialize and atomically commit one run-state mutation."""
    lock_path = _state_lock_path(root)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        state_path = root / RUN_STATE_PATH
        state = json.loads(state_path.read_text(encoding="utf-8"))
        if not isinstance(state, dict):
            raise ValueError("run_state.json must be a JSON object")
        yield state
        _atomic_write_json(state_path, state)


def _read_state(root: Path) -> dict:
    state = json.loads((root / RUN_STATE_PATH).read_text(encoding="utf-8"))
    if not isinstance(state, dict):
        raise ValueError("run_state.json must be a JSON object")
    return state


def _score_map(path: str | None) -> dict[str, float]:
    if path is None:
        return {}
    with Path(path).open(encoding="utf-8") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"{path} must contain a JSON object mapping team_id to score")
    return {str(team): float(score) for team, score in raw.items()}


def _load_config(path: str | Path) -> dict:
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)


def _require_phase0(root: Path) -> None:
    issues = verify_phase0_freeze(root=root)
    if issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
        raise ValueError(f"Phase-0 freeze verification failed: {detail}")
    state = _read_state(root)
    try:
        records = _validate_research_journal(root, state)
        freeze = json.loads((root / PHASE0_FREEZE_PATH).read_text(encoding="utf-8"))
        journal_state = state["research_journal"]
        if (
            not isinstance(freeze, dict)
            or freeze.get("research_journal_path") != ORGANIZER_RESEARCH_JOURNAL_PATH
            or freeze.get("research_journal_genesis_sha256") != journal_state["genesis_sha256"]
            or records[0]["record_sha256"] != journal_state["genesis_sha256"]
        ):
            raise ValueError("Phase-0 journal genesis/path binding differs")
    except (KeyError, OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"Phase-0 research journal verification failed: {exc}") from exc


def _init_teams(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.top40 import HARD_COMPLIANCE_CHECKS

    root = Path.cwd()
    config = _load_config(args.config)
    template_path = root / "tournament/top40/templates/submission.json"
    with template_path.open(encoding="utf-8") as handle:
        template = json.load(handle)
    team_states: dict[str, dict[str, object]] = {}
    for team_id in config["teams"]:
        team_dir = root / "tournament/top40/teams" / team_id
        report_dir = root / "reports-top40" / team_id
        team_dir.mkdir(parents=True, exist_ok=True)
        report_dir.mkdir(parents=True, exist_ok=True)
        submission_path = team_dir / "submission.json"
        if args.force or not submission_path.exists():
            raw = json.loads(json.dumps(template).replace("team-01", team_id))
            raw["team_id"] = team_id
            raw["seeds"] = [int(config["research_budget"]["strategy_seed"])]
            submission_path.write_text(
                json.dumps(raw, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        bootstrap_path = team_dir / "BOOTSTRAP.md"
        if args.force or not bootstrap_path.exists():
            bootstrap_path.write_text(
                "# "
                + team_id
                + " bootstrap\n\n"
                + "Status: `QR_PENDING`\n\n"
                + "Read only the common charter, config, Phase-0 policy, frozen data manifest, "
                + "strategy-neutral tournament modules, and this team namespace. Do not inspect "
                + "historical portfolio artifacts or another team.\n",
                encoding="utf-8",
            )
        compliance_path = team_dir / "compliance.json"
        if args.force or not compliance_path.exists():
            compliance_path.write_text(
                json.dumps(
                    {name: False for name in HARD_COMPLIANCE_CHECKS},
                    indent=2,
                    sort_keys=True,
                )
                + "\n",
                encoding="utf-8",
            )
        team_states[team_id] = {
            "qr": "pending",
            "qe": "pending",
            "canonical_run": "pending",
            "freeze_commit": None,
            "champion": None,
            "oos_accesses": [],
            "reviews": {},
        }
    state_path = root / "tournament/top40/run_state.json"
    if args.force or not state_path.exists():
        _genesis, journal_bytes, journal_state = _new_research_journal()
        state = {
            "schema_version": 1,
            "phase": "phase0",
            "common_freeze_commit": None,
            "data_manifest_sha256": None,
            "evaluator_sha256": None,
            "methodology_sha256": None,
            "config_sha256": None,
            "orchestrator_sha256": None,
            "research_journal": journal_state,
            "teams": team_states,
        }
        _atomic_write_bytes(root / ORGANIZER_RESEARCH_JOURNAL_PATH, journal_bytes)
        _atomic_write_json(state_path, state)
    print(f"initialized {len(team_states)} isolated team namespaces")
    return 0


def _snapshot_locations(args: argparse.Namespace) -> tuple[Path, Path, Path, Path]:
    root = Path.cwd().resolve()
    config_path = (root / args.config).resolve()
    config = _load_config(config_path)

    def location(override: str | None, key: str) -> Path:
        value = override if override is not None else str(config["data"][key])
        path = Path(value)
        return path.resolve() if path.is_absolute() else (root / path).resolve()

    return (
        config_path,
        location(args.output_dir, "snapshot_dir"),
        location(args.manifest, "manifest_path"),
        location(args.common_reports, "common_report_dir"),
    )


def _build_snapshot(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.snapshot import build_snapshot

    config_path, output_dir, manifest_path, common_reports = _snapshot_locations(args)
    manifest = build_snapshot(
        config_path,
        output_dir,
        manifest_path,
        common_reports,
        resume=not args.no_resume,
    )
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    print(
        f"snapshot verified: files={len(manifest['files'])} "
        f"archives={manifest['sources']['archive_count']} manifest_sha256={digest}"
    )
    return 0


def _verify_snapshot(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.snapshot import verify_snapshot_manifest

    _, _, manifest_path, _ = _snapshot_locations(args)
    manifest = verify_snapshot_manifest(manifest_path)
    digest = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    print(
        f"snapshot valid: files={len(manifest['files'])} "
        f"archives={manifest['sources']['archive_count']} manifest_sha256={digest}"
    )
    return 0


def _registration_digest(raw_line: bytes) -> str:
    return hashlib.sha256(raw_line).hexdigest()


def _pending_public_oos_registration(path: Path, candidate_id: str) -> tuple[dict, str, bytes]:
    """Return one exact pending OOS registration and its append-only line hash."""
    if not candidate_id:
        raise ValueError("candidate_id must be non-empty")
    try:
        raw_lines = path.read_bytes().splitlines(keepends=True)
    except OSError as exc:
        raise ValueError(f"cannot read experiment ledger: {exc}") from exc
    if not raw_lines or any(not line.endswith(b"\n") for line in raw_lines):
        raise ValueError("experiments.jsonl must use one newline-terminated JSON event per line")

    registrations: dict[str, tuple[dict, str, bytes]] = {}
    results: set[str] = set()
    event_ids: set[str] = set()
    registered_keys = {
        "event_id",
        "candidate_id",
        "event_type",
        "timestamp_utc",
        "parent_candidate_id",
        "delta",
        "seed",
        "parameters",
        "public_oos_requested",
    }
    for number, raw_line in enumerate(raw_lines, start=1):
        try:
            row = json.loads(raw_line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"experiments.jsonl line {number} is invalid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"experiments.jsonl line {number} must be an object")
        event_id = row.get("event_id")
        row_candidate = row.get("candidate_id")
        if not isinstance(event_id, str) or not event_id or event_id in event_ids:
            raise ValueError("experiment event IDs must be unique non-empty strings")
        if not isinstance(row_candidate, str) or not row_candidate:
            raise ValueError("experiment candidate IDs must be non-empty strings")
        event_ids.add(event_id)
        if row.get("event_type") == "registered":
            if set(row) != registered_keys or row_candidate in registrations:
                raise ValueError("experiment registration has invalid fields or is duplicated")
            registrations[row_candidate] = (row, _registration_digest(raw_line), raw_line)
        elif row.get("event_type") == "result":
            if row_candidate not in registrations or row_candidate in results:
                raise ValueError("experiment result must follow one unique registration")
            results.add(row_candidate)
        else:
            raise ValueError("experiment event_type must be registered or result")

    registration = registrations.get(candidate_id)
    if registration is None:
        raise ValueError(f"candidate {candidate_id} has no prior registration")
    row, digest, raw_line = registration
    if candidate_id in results:
        raise ValueError(f"candidate {candidate_id} already has a result; replay is forbidden")
    if row.get("public_oos_requested") is not True:
        raise ValueError(f"candidate {candidate_id} did not request public-OOS access")
    return row, digest, raw_line


_OOS_ACCESS_KEYS = {
    "run_id",
    "candidate_id",
    "registration_sha256",
    "team_ledger_sha256",
    "source_bundle_sha256",
    "reservation_record_sha256",
    "result_record_sha256",
    "reserved_at_utc",
    "status",
    "finished_at_utc",
    "failure_type",
}


def _projected_oos_access(candidate_id: str, item: Mapping[str, object]) -> dict[str, object]:
    reservation = item.get("reservation")
    if not isinstance(reservation, Mapping):
        raise ValueError("organizer journal run is missing its reservation")
    reservation_payload = reservation.get("payload")
    if not isinstance(reservation_payload, Mapping):
        raise ValueError("organizer journal reservation payload is malformed")
    result = item.get("result")
    result_payload = result.get("payload") if isinstance(result, Mapping) else None
    return {
        "run_id": reservation_payload.get("run_id"),
        "candidate_id": candidate_id,
        "registration_sha256": reservation_payload.get("registration_sha256"),
        "team_ledger_sha256": reservation_payload.get("team_ledger_sha256"),
        "source_bundle_sha256": reservation_payload.get("source_bundle_sha256"),
        "reservation_record_sha256": reservation.get("record_sha256"),
        "result_record_sha256": (
            result.get("record_sha256") if isinstance(result, Mapping) else None
        ),
        "reserved_at_utc": reservation.get("timestamp_utc"),
        "status": (
            result_payload.get("status") if isinstance(result_payload, Mapping) else "reserved"
        ),
        "finished_at_utc": (result.get("timestamp_utc") if isinstance(result, Mapping) else None),
        "failure_type": (
            result_payload.get("failure_type") if isinstance(result_payload, Mapping) else None
        ),
    }


def _validate_oos_state_against_journal(
    team_id: str,
    accesses: object,
    journal_runs: Mapping[str, Mapping[str, object]],
) -> None:
    """Require mutable run state to be a complete projection of the hash-chain journal."""
    if not isinstance(accesses, list):
        raise ValueError("team oos_accesses must be a JSON array")
    by_candidate: dict[str, dict] = {}
    for access in accesses:
        if (
            not isinstance(access, dict)
            or set(access) != _OOS_ACCESS_KEYS
            or not isinstance(access.get("candidate_id"), str)
            or access["candidate_id"] in by_candidate
        ):
            raise ValueError(f"{team_id} public-OOS run-state projection is malformed")
        by_candidate[access["candidate_id"]] = access
    if set(by_candidate) != set(journal_runs):
        raise ValueError(f"{team_id} public-OOS run state omits or invents organizer runs")
    for candidate_id, item in journal_runs.items():
        expected = _projected_oos_access(candidate_id, item)
        if by_candidate[candidate_id] != expected:
            raise ValueError(f"{team_id}/{candidate_id} run state differs from organizer journal")


def _validate_state_oos_projection(
    state: Mapping[str, object], records: Sequence[Mapping[str, object]]
) -> None:
    """Validate every mutable team projection against one journal prefix."""
    teams = state.get("teams")
    if not isinstance(teams, Mapping):
        raise ValueError("run_state teams projection is missing or malformed")
    journal_runs = _organizer_runs(records)
    for team_id in TEAM_IDS:
        team = teams.get(team_id)
        runs = journal_runs[team_id]
        if not isinstance(team, Mapping):
            if runs:
                raise ValueError(f"run_state is missing journaled team {team_id}")
            continue
        _validate_oos_state_against_journal(team_id, team.get("oos_accesses"), runs)


def _result_team_bytes(result_record: Mapping[str, object]) -> bytes:
    payload = result_record.get("payload")
    if not isinstance(payload, Mapping):
        raise ValueError("organizer result payload is malformed")
    try:
        raw = base64.b64decode(payload["team_result_bytes_base64"], validate=True)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("organizer result team bytes are malformed") from exc
    if hashlib.sha256(raw).hexdigest() != payload.get("team_result_sha256"):
        raise ValueError("organizer result team bytes differ from their hash")
    return raw


def _reconcile_research_ledger_tail(
    root: Path,
    records: Sequence[Mapping[str, object]],
    anchored_count: int,
) -> int:
    """Materialize only result bytes authorized by the valid journal tail."""
    tail = records[anchored_count:]
    if not tail:
        return 0
    all_runs_by_id: dict[str, dict[str, Mapping[str, object]]] = {}
    for record in records[1:]:
        payload = record["payload"]
        assert isinstance(payload, Mapping)
        all_runs_by_id.setdefault(str(payload["run_id"]), {})[str(record["event_type"])] = record

    ledger_bytes: dict[str, bytes] = {}
    affected_run_ids = {str(record["payload"]["run_id"]) for record in tail}
    for run_id in sorted(affected_run_ids):
        item = all_runs_by_id[run_id]
        reservation = item.get("reservation")
        if not isinstance(reservation, Mapping):
            raise ValueError("journal recovery found a result without its reservation")
        payload = reservation.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("journal recovery found a malformed reservation")
        team_id = str(payload["team_id"])
        ledger = root / canonical_artifact_paths(team_id)["trial_ledger"]
        if not ledger.is_file() or ledger.is_symlink():
            raise ValueError(f"journal recovery found an unsafe team ledger: {team_id}")
        current = ledger_bytes.setdefault(team_id, ledger.read_bytes())
        size = int(payload["team_ledger_size"])
        if (
            len(current) < size
            or hashlib.sha256(current[:size]).hexdigest() != payload["team_ledger_sha256"]
        ):
            raise ValueError(
                "journal recovery rejected divergent reservation prefix: "
                f"{team_id}/{payload['candidate_id']}"
            )
        if "result" not in item and len(current) != size:
            raise ValueError(
                "journal recovery rejected divergent orphan-reservation tail: "
                f"{team_id}/{payload['candidate_id']}"
            )

    appended = 0
    for record in tail:
        if record["event_type"] != "result":
            continue
        payload = record["payload"]
        assert isinstance(payload, Mapping)
        item = all_runs_by_id[str(payload["run_id"])]
        reservation = item["reservation"]
        reservation_payload = reservation["payload"]
        assert isinstance(reservation_payload, Mapping)
        team_id = str(reservation_payload["team_id"])
        ledger = root / canonical_artifact_paths(team_id)["trial_ledger"]
        current = ledger_bytes[team_id]
        size = int(reservation_payload["team_ledger_size"])
        team_line = _result_team_bytes(record)
        if len(current) == size:
            with ledger.open("ab", buffering=0) as handle:
                handle.write(team_line)
                os.fsync(handle.fileno())
            current += team_line
            ledger_bytes[team_id] = current
            appended += 1
        elif current != current[:size] + team_line:
            raise ValueError(
                "journal recovery rejected divergent result bytes: "
                f"{team_id}/{payload['candidate_id']}"
            )
    return appended


def _recover_research_accounting_locked(root: Path, state: dict) -> tuple[int, int]:
    """Replay a journal-only crash tail into ledgers, state projections, and anchor."""
    records = _validate_research_journal_chain(root)
    anchored_count = _validate_research_journal_prefix(records, state)
    _validate_state_oos_projection(state, records[:anchored_count])
    appended = _reconcile_research_ledger_tail(root, records, anchored_count)
    tail = records[anchored_count:]
    if tail:
        teams = state["teams"]
        journal_runs = _organizer_runs(records)
        affected = {
            str(record["payload"]["team_id"])
            for record in tail
            if isinstance(record.get("payload"), Mapping)
        }
        for team_id in sorted(affected):
            team = teams.get(team_id)
            if not isinstance(team, dict):
                raise ValueError(f"run_state is missing journaled team {team_id}")
            team["oos_accesses"] = [
                _projected_oos_access(candidate_id, item)
                for candidate_id, item in journal_runs[team_id].items()
            ]
        state["research_journal"] = _research_journal_anchor(records)
        _validate_state_oos_projection(state, records)
    return len(tail), appended


def _recover_research_accounting(_args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    with _edit_run_state(root) as state:
        if state.get("phase") != "research":
            raise ValueError("research accounting recovery is allowed only in research phase")
        replayed, appended = _recover_research_accounting_locked(root, state)
    print(
        f"research accounting recovered: journal_records={replayed} "
        f"team_results_appended={appended}"
    )
    return 0


def _require_public_oos_capacity(
    team_id: str,
    journal_runs: Mapping[str, object],
    maximum: int,
) -> None:
    if len(journal_runs) >= maximum:
        raise ValueError(f"{team_id} already consumed its {maximum} public-OOS attempts")


def _process_cpu_seconds() -> float:
    own = resource.getrusage(resource.RUSAGE_SELF)
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return float(own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime)


def _git_head_and_team_tree(root: Path, team_id: str) -> tuple[str, str | None]:
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tree = subprocess.run(
        ["git", "rev-parse", f"HEAD:tournament/top40/teams/{team_id}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    tree_id = tree.stdout.strip() if tree.returncode == 0 else None
    return head, tree_id


def _run_artifact_hashes(
    root: Path, artifacts: Mapping[str, str]
) -> tuple[dict[str, str], dict[str, int]]:
    hashes: dict[str, str] = {}
    sizes: dict[str, int] = {}
    for name, relative in sorted(artifacts.items()):
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file() or path.is_symlink():
            raise ValueError(f"runner artifact is missing or unsafe: {name}/{relative}")
        before = path.stat()
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        after = path.stat()
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        ) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns):
            raise ValueError(f"runner artifact changed while hashing: {name}/{relative}")
        hashes[relative] = digest.hexdigest()
        sizes[relative] = after.st_size
    return hashes, sizes


def _canonical_research_metrics(result: object | None) -> dict[str, object] | None:
    if result is None:
        return None
    return {
        "in_sample": dataclasses.asdict(result.in_sample),
        "public_oos": dataclasses.asdict(result.public_oos),
        "double_cost_oos_sharpe": result.double_cost_oos_sharpe,
        "regime_sharpe": dict(result.regime_sharpe),
        "confidence_intervals": {
            name: list(bounds) for name, bounds in result.confidence_intervals.items()
        },
    }


def _team_result_event(
    *,
    run_id: str,
    candidate_id: str,
    finished_at: datetime,
    status: str,
    failure_type: str | None,
    cpu_hours: float,
    wall_clock_hours: float,
    metrics: Mapping[str, object] | None,
    artifact_hashes: Mapping[str, str],
) -> dict[str, object]:
    return {
        "event_id": f"organizer-{run_id}-result",
        "candidate_id": candidate_id,
        "event_type": "result",
        "timestamp_utc": finished_at.astimezone(UTC).isoformat(),
        "cpu_hours": cpu_hours,
        "wall_clock_hours": wall_clock_hours,
        "is_metrics": metrics["in_sample"]["metrics"] if metrics is not None else None,
        "public_oos_accessed": True,
        "public_oos_metrics": metrics["public_oos"]["metrics"] if metrics is not None else None,
        "disposition": (
            "organizer_completed"
            if status == "completed"
            else f"organizer_failed:{failure_type or 'UnknownFailure'}"
        ),
        "artifact_hashes": dict(artifact_hashes),
    }


def _record_oos_result_locked(
    root: Path,
    state: dict,
    team_id: str,
    candidate_id: str,
    run_id: str,
    *,
    status: str,
    failure_type: str | None,
    source_bundle_sha256: str | None,
    metrics: Mapping[str, object] | None,
    artifact_hashes: Mapping[str, str],
    artifact_sizes: Mapping[str, int],
    decision_count: int | None,
    event_count: int | None,
    trade_count: int | None,
    cpu_hours: float,
    wall_clock_hours: float,
    finished_at: datetime,
) -> str | None:
    """Write ahead to the journal, then append the ledger, then project state."""
    records = _validate_research_journal(root, state)
    runs = _organizer_runs(records)[team_id]
    team = state.get("teams", {}).get(team_id)
    if not isinstance(team, dict):
        raise ValueError(f"run_state is missing OOS reservations for {team_id}")
    accesses = team.get("oos_accesses")
    _validate_oos_state_against_journal(team_id, accesses, runs)
    item = runs.get(candidate_id)
    if not isinstance(item, dict) or "result" in item:
        raise ValueError("public-OOS reservation changed during execution")
    reservation = item["reservation"]
    reservation_payload = reservation["payload"]
    if reservation_payload.get("run_id") != run_id:
        raise ValueError("public-OOS run capability differs from its reservation")
    ledger = root / canonical_artifact_paths(team_id)["trial_ledger"]
    current_ledger = ledger.read_bytes()
    integrity_error: str | None = None
    if (
        len(current_ledger) != reservation_payload["team_ledger_size"]
        or hashlib.sha256(current_ledger).hexdigest() != reservation_payload["team_ledger_sha256"]
    ):
        integrity_error = "ExperimentLedgerChanged"
    if (
        source_bundle_sha256 is not None
        and source_bundle_sha256 != reservation_payload["source_bundle_sha256"]
    ):
        integrity_error = integrity_error or "SourceBundleChanged"
    effective_status = "failed" if integrity_error is not None else status
    effective_failure = integrity_error or failure_type
    if effective_status == "failed" and not effective_failure:
        effective_failure = "UnknownFailure"
    if effective_status == "completed" and effective_failure is not None:
        raise ValueError("completed public-OOS results cannot have a failure type")
    team_event = _team_result_event(
        run_id=run_id,
        candidate_id=candidate_id,
        finished_at=finished_at,
        status=effective_status,
        failure_type=effective_failure,
        cpu_hours=cpu_hours,
        wall_clock_hours=wall_clock_hours,
        metrics=metrics,
        artifact_hashes=artifact_hashes,
    )
    team_line = _canonical_json_bytes(team_event) + b"\n"
    team_result_sha256 = hashlib.sha256(team_line).hexdigest()
    result_payload = {
        "run_id": run_id,
        "team_id": team_id,
        "candidate_id": candidate_id,
        "status": effective_status,
        "failure_type": effective_failure,
        "cpu_hours": cpu_hours,
        "wall_clock_hours": wall_clock_hours,
        "source_bundle_sha256": reservation_payload["source_bundle_sha256"],
        "canonical_metrics": metrics,
        "artifact_hashes": dict(artifact_hashes),
        "artifact_sizes": dict(artifact_sizes),
        "decision_count": decision_count,
        "event_count": event_count,
        "trade_count": trade_count,
        "team_result_bytes_base64": base64.b64encode(team_line).decode("ascii"),
        "team_result_sha256": team_result_sha256,
    }
    result_record = _append_research_journal_locked(
        root,
        state,
        "result",
        result_payload,
        timestamp=finished_at,
    )
    if integrity_error == "ExperimentLedgerChanged":
        raise ValueError("public-OOS accounting failed closed: ExperimentLedgerChanged")
    with ledger.open("ab", buffering=0) as handle:
        handle.write(team_line)
        os.fsync(handle.fileno())
    access = next(item for item in accesses if item.get("candidate_id") == candidate_id)
    access.update(
        {
            "result_record_sha256": result_record["record_sha256"],
            "status": effective_status,
            "finished_at_utc": result_record["timestamp_utc"],
            "failure_type": effective_failure,
        }
    )
    return integrity_error


def _finish_oos_reservation(
    root: Path,
    team_id: str,
    candidate_id: str,
    run_id: str,
    *,
    status: str,
    failure_type: str | None,
    result: object | None,
    cpu_hours: float,
    wall_clock_hours: float,
) -> None:
    """Persist an organizer-measured result through the write-ahead protocol."""
    if status not in {"completed", "failed"}:
        raise ValueError("public-OOS result status is invalid")
    metrics = _canonical_research_metrics(result)
    artifact_hashes: dict[str, str] = {}
    artifact_sizes: dict[str, int] = {}
    if result is not None:
        artifact_hashes, artifact_sizes = _run_artifact_hashes(root, result.artifacts)
    finished_at = datetime.now(UTC)
    with _edit_run_state(root) as state:
        integrity_error = _record_oos_result_locked(
            root,
            state,
            team_id,
            candidate_id,
            run_id,
            status=status,
            failure_type=failure_type,
            source_bundle_sha256=(result.source_bundle_sha256 if result is not None else None),
            metrics=metrics,
            artifact_hashes=artifact_hashes,
            artifact_sizes=artifact_sizes,
            decision_count=result.decision_count if result is not None else None,
            event_count=result.event_count if result is not None else None,
            trade_count=result.trade_count if result is not None else None,
            cpu_hours=cpu_hours,
            wall_clock_hours=wall_clock_hours,
            finished_at=finished_at,
        )
    if integrity_error is not None:
        raise ValueError(f"public-OOS accounting failed closed: {integrity_error}")


def _close_interrupted_run(args: argparse.Namespace) -> int:
    """Explicitly close one recovered orphan reservation as a counted failure."""
    root = Path.cwd().resolve()
    _require_phase0(root)
    if args.team_id not in TEAM_IDS:
        raise ValueError("team_id must be team-01 through team-10")
    with _edit_run_state(root) as state:
        if state.get("phase") != "research":
            raise ValueError("interrupted runs may be closed only in research phase")
        records = _validate_research_journal(root, state)
        _validate_state_oos_projection(state, records)
        item = _organizer_runs(records)[args.team_id].get(args.candidate_id)
        if not isinstance(item, Mapping) or "result" in item:
            raise ValueError("candidate is not a recovered orphan reservation")
        reservation = item.get("reservation")
        if not isinstance(reservation, Mapping):
            raise ValueError("candidate reservation is malformed")
        payload = reservation.get("payload")
        if not isinstance(payload, Mapping):
            raise ValueError("candidate reservation payload is malformed")
        finished_at = datetime.now(UTC)
        reserved_at = _utc_timestamp(reservation.get("timestamp_utc"), "reservation timestamp_utc")
        wall_clock_hours = max(0.0, (finished_at - reserved_at).total_seconds() / 3600.0)
        integrity_error = _record_oos_result_locked(
            root,
            state,
            args.team_id,
            args.candidate_id,
            str(payload["run_id"]),
            status="failed",
            failure_type="OrganizerInterruptedRun",
            source_bundle_sha256=None,
            metrics=None,
            artifact_hashes={},
            artifact_sizes={},
            decision_count=None,
            event_count=None,
            trade_count=None,
            cpu_hours=0.0,
            wall_clock_hours=wall_clock_hours,
            finished_at=finished_at,
        )
    if integrity_error is not None:
        raise ValueError(f"public-OOS accounting failed closed: {integrity_error}")
    print(
        f"closed interrupted run: {args.team_id}/{args.candidate_id} "
        f"wall_clock_hours={wall_clock_hours:.9f}"
    )
    return 0


def _run_team(args: argparse.Namespace) -> int:
    """Consume one organizer-reserved public-OOS view for a registered candidate."""
    from crypto_trade.tournament.data import sha256_manifest
    from crypto_trade.tournament.runner import (
        _ORGANIZER_RUN_AUTHORIZATION,
        run_team,
        source_bundle_fingerprint,
    )

    root = Path.cwd().resolve()
    _require_phase0(root)
    if args.team_id not in TEAM_IDS:
        raise ValueError("team_id must be team-01 through team-10")
    config = _load_config(root / CANONICAL_CONFIG_PATH)
    budget = config["research_budget"]
    if datetime.now(UTC) > _utc_timestamp(budget["deadline_utc"], "research_budget.deadline_utc"):
        raise ValueError("the research deadline has passed")
    ledger = root / canonical_artifact_paths(args.team_id)["trial_ledger"]

    entrypoint = canonical_artifact_paths(args.team_id)["strategy_source"]
    with _edit_run_state(root) as state:
        if state.get("phase") != "research":
            raise ValueError("public-OOS research runs are allowed only in research phase")
        team = state.get("teams", {}).get(args.team_id)
        if not isinstance(team, dict):
            raise ValueError(f"run_state is missing {args.team_id}")
        if team.get("champion") is not None:
            raise ValueError("a frozen champion cannot consume another public-OOS view")
        records = _validate_research_journal(root, state)
        journal_runs = _organizer_runs(records)[args.team_id]
        accesses = team.setdefault("oos_accesses", [])
        _validate_oos_state_against_journal(args.team_id, accesses, journal_runs)
        registration, registration_sha, registration_bytes = _pending_public_oos_registration(
            ledger, args.candidate_id
        )
        if args.candidate_id in journal_runs:
            raise ValueError(f"candidate {args.candidate_id} has already consumed an attempt")
        if any("result" not in item for item in journal_runs.values()):
            raise ValueError(
                f"{args.team_id} has an interrupted reservation; recover and close it first"
            )
        maximum = int(budget["maximum_public_oos_views_per_team"])
        _require_public_oos_capacity(args.team_id, journal_runs, maximum)
        reserved_at = datetime.now(UTC)
        registered_at = _utc_timestamp(
            registration["timestamp_utc"], "experiment registration timestamp_utc"
        )
        phase0 = json.loads((root / PHASE0_FREEZE_PATH).read_text(encoding="utf-8"))
        if registered_at < _utc_timestamp(phase0["frozen_at_utc"], "phase0 frozen_at_utc"):
            raise ValueError("public-OOS registration predates Phase-0")
        if registered_at > reserved_at:
            raise ValueError("public-OOS registration timestamp cannot be in the future")
        seed = int(budget["strategy_seed"])
        if registration["seed"] != seed:
            raise ValueError("public-OOS registration seed differs from the frozen strategy seed")
        source_bundle_sha, source_bundle_files = source_bundle_fingerprint(
            root, args.team_id, entrypoint
        )
        config_sha = hashlib.sha256((root / CANONICAL_CONFIG_PATH).read_bytes()).hexdigest()
        manifest_sha = hashlib.sha256((root / CANONICAL_MANIFEST_PATH).read_bytes()).hexdigest()
        evaluator_sha = sha256_manifest(
            [root / path for path in EVALUATOR_SOURCE_PATHS], root=root
        )[0]
        git_head, git_team_tree = _git_head_and_team_tree(root, args.team_id)
        ledger_bytes = ledger.read_bytes()
        run_id = hashlib.sha256(
            _canonical_json_bytes(
                {
                    "candidate_id": args.candidate_id,
                    "registration_sha256": registration_sha,
                    "reserved_at_utc": reserved_at.isoformat(),
                    "team_id": args.team_id,
                    "prior_journal_head": state["research_journal"]["head_sha256"],
                }
            )
            + os.urandom(32)
        ).hexdigest()
        reservation_payload = {
            "run_id": run_id,
            "team_id": args.team_id,
            "candidate_id": args.candidate_id,
            "registration_bytes_base64": base64.b64encode(registration_bytes).decode("ascii"),
            "registration_sha256": registration_sha,
            "team_ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
            "team_ledger_size": len(ledger_bytes),
            "source_bundle_sha256": source_bundle_sha,
            "source_bundle_files": list(source_bundle_files),
            "entrypoint": entrypoint,
            "config_sha256": config_sha,
            "manifest_sha256": manifest_sha,
            "evaluator_sha256": evaluator_sha,
            "seed": seed,
            "git_head_commit": git_head,
            "git_team_tree_id": git_team_tree,
        }
        reservation_record = _append_research_journal_locked(
            root,
            state,
            "reservation",
            reservation_payload,
            timestamp=reserved_at,
        )
        accesses.append(
            {
                "run_id": run_id,
                "candidate_id": args.candidate_id,
                "registration_sha256": registration_sha,
                "team_ledger_sha256": reservation_payload["team_ledger_sha256"],
                "source_bundle_sha256": source_bundle_sha,
                "reservation_record_sha256": reservation_record["record_sha256"],
                "result_record_sha256": None,
                "reserved_at_utc": reservation_record["timestamp_utc"],
                "status": "reserved",
                "finished_at_utc": None,
                "failure_type": None,
            }
        )

    started_wall = time.perf_counter()
    started_cpu = _process_cpu_seconds()
    result = None
    failure: BaseException | None = None
    try:
        result = run_team(
            root,
            args.team_id,
            entrypoint,
            CANONICAL_CONFIG_PATH,
            CANONICAL_MANIFEST_PATH,
            _authorization=_ORGANIZER_RUN_AUTHORIZATION,
        )
    except BaseException as exc:
        failure = exc
    cpu_hours = max(0.0, _process_cpu_seconds() - started_cpu) / 3600.0
    wall_clock_hours = max(0.0, time.perf_counter() - started_wall) / 3600.0
    _finish_oos_reservation(
        root,
        args.team_id,
        args.candidate_id,
        run_id,
        status="failed" if failure is not None else "completed",
        failure_type=type(failure).__name__ if failure is not None else None,
        result=result,
        cpu_hours=cpu_hours,
        wall_clock_hours=wall_clock_hours,
    )
    if failure is not None:
        raise failure.with_traceback(failure.__traceback__)
    assert result is not None
    text = json.dumps(result.submission_fields(), indent=2, sort_keys=True) + "\n"
    if args.json_out:
        Path(args.json_out).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def _freeze_phase0(args: argparse.Namespace) -> int:
    from crypto_trade.tournament.data import sha256_manifest
    from crypto_trade.tournament.snapshot import verify_snapshot_manifest

    root = Path.cwd().resolve()
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if branch != TOURNAMENT_BRANCH:
        raise ValueError(f"Phase-0 may freeze only on branch {TOURNAMENT_BRANCH}")
    freeze_path = root / PHASE0_FREEZE_PATH
    if freeze_path.exists() or freeze_path.is_symlink():
        raise ValueError("Phase-0 freeze is single-shot; phase0_freeze.json already exists")
    state_path = root / RUN_STATE_PATH
    state = _read_state(root)
    if state.get("phase") != "phase0" or set(state.get("teams", {})) != set(TEAM_IDS):
        raise ValueError("Phase-0 freeze requires the initialized phase0 state for all ten teams")
    for team_id in TEAM_IDS:
        team = state["teams"][team_id]
        if not isinstance(team, dict) or any(
            (
                team.get("qr") != "pending",
                team.get("qe") != "pending",
                team.get("canonical_run") != "pending",
                team.get("freeze_commit") is not None,
                team.get("champion") is not None,
                team.get("oos_accesses") != [],
                team.get("reviews") != {},
            )
        ):
            raise ValueError(f"{team_id} is not in its pristine Phase-0 state")
    journal_records = _validate_research_journal(root, state)
    if len(journal_records) != 1 or journal_records[0]["event_type"] != "genesis":
        raise ValueError("Phase-0 freeze requires a pristine organizer research journal")
    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if dirty:
        raise ValueError(
            "commit the common infrastructure and snapshot manifest before Phase-0 freeze"
        )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    manifest_path = (root / CANONICAL_MANIFEST_PATH).resolve()
    manifest = verify_snapshot_manifest(manifest_path)
    evaluator_paths = [root / path for path in EVALUATOR_SOURCE_PATHS]
    evaluator_sha = sha256_manifest(evaluator_paths, root=root)[0]
    methodology_sha = sha256_manifest([root / path for path in METHODOLOGY_PATHS], root=root)[0]
    config_path = (root / CANONICAL_CONFIG_PATH).resolve()

    logical_files = {entry["name"]: entry for entry in manifest["files"]}
    payload = {
        "schema_version": 1,
        "frozen_at_utc": datetime.now(UTC).isoformat(),
        "branch": TOURNAMENT_BRANCH,
        "common_freeze_commit": commit,
        "data_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "evaluator_sha256": evaluator_sha,
        "methodology_sha256": methodology_sha,
        "config_sha256": hashlib.sha256(config_path.read_bytes()).hexdigest(),
        "btc_daily_returns_sha256": logical_files["btc_daily_returns"]["sha256"],
        "btc_regimes_sha256": logical_files["btc_regimes"]["sha256"],
        "phase0_policy_sha256": hashlib.sha256(
            (root / "tournament/top40/PHASE0-POLICY.md").read_bytes()
        ).hexdigest(),
        "snapshot_builder_sha256": manifest["sources"]["builder_sha256"],
        "root_dependency_lock_sha256": hashlib.sha256(
            (root / ROOT_DEPENDENCY_LOCK_PATH).read_bytes()
        ).hexdigest(),
        "orchestrator_sha256": hashlib.sha256(
            (root / ORCHESTRATOR_SCRIPT_PATH).read_bytes()
        ).hexdigest(),
        "research_journal_path": ORGANIZER_RESEARCH_JOURNAL_PATH,
        "research_journal_genesis_sha256": journal_records[0]["record_sha256"],
    }
    _atomic_write_json(freeze_path, payload)
    state.update(
        {
            "phase": "research",
            "common_freeze_commit": commit,
            "data_manifest_sha256": payload["data_manifest_sha256"],
            "evaluator_sha256": evaluator_sha,
            "methodology_sha256": methodology_sha,
            "config_sha256": payload["config_sha256"],
            "orchestrator_sha256": payload["orchestrator_sha256"],
        }
    )
    _atomic_write_json(state_path, state)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _head_commit(root: Path) -> str:
    return subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def _git_file_bytes(root: Path, commit: str, relative: str) -> bytes:
    result = subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode != 0:
        raise ValueError(f"{relative} is not committed at {commit}")
    return result.stdout


def _unique_first_add_commit(
    root: Path,
    relative: str,
    *,
    expected_parent: str,
    label: str,
) -> str:
    """Verify an immutable lock was first-added once with the exact expected sole parent."""
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} is missing or unsafe: {relative}")
    status = subprocess.run(
        ["git", "status", "--porcelain=v1", "--", relative],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if status.returncode != 0 or status.stdout.strip():
        raise ValueError(f"{label} must be tracked, committed, and clean")
    history = subprocess.run(
        ["git", "log", "--format=%H", "--", relative],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    commits = [line for line in history.stdout.splitlines() if line]
    if history.returncode != 0 or len(commits) != 1:
        raise ValueError(f"{label} must have exactly one first-add Git commit and no modifications")
    record_commit = commits[0]
    expected = subprocess.run(
        ["git", "rev-parse", f"{expected_parent}^{{commit}}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    ).stdout.strip()
    parents = subprocess.run(
        ["git", "rev-list", "--parents", "-n", "1", record_commit],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if parents.returncode != 0 or parents.stdout.strip().split() != [record_commit, expected]:
        raise ValueError(f"{label} record commit does not have the exact expected sole parent")
    added = subprocess.run(
        [
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-status",
            "-r",
            record_commit,
            "--",
            relative,
        ],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if added.returncode != 0 or added.stdout.strip() != f"A\t{relative}":
        raise ValueError(f"{label} path was not first-added in its record commit")
    if _git_file_bytes(root, record_commit, relative) != path.read_bytes():
        raise ValueError(f"{label} bytes changed after its first-add record commit")
    return record_commit


def _require_untracked_new_path(root: Path, relative: str, label: str) -> None:
    path = root / relative
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} is missing or unsafe: {relative}")
    history = subprocess.run(
        ["git", "log", "--format=%H", "--", relative],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", relative],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if history.returncode != 0 or history.stdout.strip() or tracked.returncode == 0:
        raise ValueError(f"{label} must be a new untracked file at its lock stage")


def _evidence_hashes(root: Path, team_id: str, names: Sequence[str], commit: str) -> dict[str, str]:
    artifacts = canonical_artifact_paths(team_id)
    hashes: dict[str, str] = {}
    for name in names:
        relative = artifacts[name]
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"review evidence is missing/unsafe: {relative}")
        committed = _git_file_bytes(root, commit, relative)
        current = path.read_bytes()
        if committed != current:
            raise ValueError(f"review evidence is not clean at {commit}: {relative}")
        hashes[relative] = hashlib.sha256(current).hexdigest()
    return hashes


def _verify_review_evidence(
    root: Path,
    team_id: str,
    team_state: Mapping[str, object],
    freeze_commit: str,
    roles: Sequence[str] = ("qr", "qe"),
) -> None:
    reviews = team_state.get("reviews")
    if not isinstance(reviews, dict):
        raise ValueError("team review records are missing")
    evidence_by_role = {"qr": QR_EVIDENCE, "qe": QE_EVIDENCE}
    for role in roles:
        names = evidence_by_role[role]
        record = reviews.get(role)
        if not isinstance(record, dict):
            raise ValueError(f"{team_id} has no hash-bound {role.upper()} review")
        review_commit = record.get("commit")
        hashes = record.get("evidence_sha256")
        if not isinstance(review_commit, str) or not isinstance(hashes, dict):
            raise ValueError(f"{team_id} {role.upper()} review record is malformed")
        ancestry = subprocess.run(
            ["git", "merge-base", "--is-ancestor", review_commit, freeze_commit],
            cwd=root,
            check=False,
            capture_output=True,
        )
        if ancestry.returncode != 0:
            raise ValueError(
                f"{team_id} freeze commit does not descend from its {role.upper()} review"
            )
        expected_paths = {canonical_artifact_paths(team_id)[name] for name in names}
        if set(hashes) != expected_paths:
            raise ValueError(f"{team_id} {role.upper()} evidence set is incomplete")
        for relative, digest in hashes.items():
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ValueError(f"{team_id} {role.upper()} evidence hash is malformed")
            path = root / relative
            if (
                not path.is_file()
                or path.is_symlink()
                or hashlib.sha256(path.read_bytes()).hexdigest() != digest
                or hashlib.sha256(_git_file_bytes(root, freeze_commit, relative)).hexdigest()
                != digest
            ):
                raise ValueError(f"{team_id} {role.upper()} reviewed evidence changed: {relative}")


def _mark_review(args: argparse.Namespace) -> int:
    """Record a Git- and evidence-bound organizer-observed QR or QE handoff."""
    root = Path.cwd().resolve()
    _require_phase0(root)
    if args.team_id not in TEAM_IDS:
        raise ValueError("team_id must be team-01 through team-10")
    preflight = _read_state(root).get("teams", {}).get(args.team_id)
    if args.role == "qe" and (not isinstance(preflight, dict) or preflight.get("qr") != "complete"):
        raise ValueError("QE review cannot complete before the QR handoff is recorded")
    head = _head_commit(root)
    names = QR_EVIDENCE if args.role == "qr" else QE_EVIDENCE
    hashes = _evidence_hashes(root, args.team_id, names, head)
    timestamp = datetime.now(UTC).isoformat()
    with _edit_run_state(root) as state:
        if state.get("phase") != "research":
            raise ValueError("reviews may be recorded only during research")
        team_state = state.get("teams", {}).get(args.team_id)
        if not isinstance(team_state, dict):
            raise ValueError(f"run_state is missing {args.team_id}")
        if team_state.get("canonical_run") != "pending" or team_state.get("champion") is not None:
            raise ValueError("cannot mark a review after champion freeze")
        if args.role == "qr":
            if team_state.get("qr") != "pending":
                raise ValueError(f"{args.team_id} QR review is not pending")
        else:
            if team_state.get("qr") != "complete":
                raise ValueError("QE review cannot complete before the QR handoff is recorded")
            if team_state.get("qe") != "pending":
                raise ValueError(f"{args.team_id} QE review is not pending")
            _verify_review_evidence(root, args.team_id, team_state, head, roles=("qr",))
        team_state[args.role] = "complete"
        team_state[f"{args.role}_completed_at_utc"] = timestamp
        reviews = team_state.setdefault("reviews", {})
        if not isinstance(reviews, dict):
            raise ValueError("team reviews must be a JSON object")
        reviews[args.role] = {
            "commit": head,
            "completed_at_utc": timestamp,
            "evidence_sha256": hashes,
        }
    print(f"{args.team_id}: {args.role.upper()} handoff recorded at {head}")
    return 0


def _utc_timestamp(value: object, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 UTC string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 UTC string") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != datetime.min.replace(tzinfo=UTC).utcoffset():
        raise ValueError(f"{field} must be timezone-aware UTC")
    return parsed.astimezone(UTC)


def _validate_experiment_ledger(
    path: Path,
    budget: dict,
    *,
    phase0_started_at: datetime,
    oos_accesses: Sequence[Mapping[str, object]] | None = None,
    organizer_runs: Mapping[str, Mapping[str, object]] | None = None,
) -> tuple[list[dict], int]:
    """Validate the frozen append-only registration/result event ledger."""
    raw_lines = path.read_bytes().splitlines(keepends=True)
    if not raw_lines or any(not line.strip() or not line.endswith(b"\n") for line in raw_lines):
        raise ValueError(
            "experiments.jsonl must contain only non-empty newline-terminated JSON event lines"
        )
    rows: list[dict] = []
    event_ids: set[str] = set()
    registrations: dict[str, tuple[dict, datetime]] = {}
    registration_hashes: dict[str, str] = {}
    registration_lines: dict[str, bytes] = {}
    results: dict[str, tuple[dict, datetime]] = {}
    result_hashes: dict[str, str] = {}
    previous_timestamp: datetime | None = None
    cpu_hours = 0.0
    wall_clock_hours = 0.0
    public_accesses = 0
    deadline = _utc_timestamp(budget["deadline_utc"], "research_budget.deadline_utc")
    validated_at = datetime.now(UTC)
    registered_keys = {
        "event_id",
        "candidate_id",
        "event_type",
        "timestamp_utc",
        "parent_candidate_id",
        "delta",
        "seed",
        "parameters",
        "public_oos_requested",
    }
    result_keys = {
        "event_id",
        "candidate_id",
        "event_type",
        "timestamp_utc",
        "cpu_hours",
        "wall_clock_hours",
        "is_metrics",
        "public_oos_accessed",
        "public_oos_metrics",
        "disposition",
        "artifact_hashes",
    }
    for line_number, raw_line in enumerate(raw_lines, start=1):
        try:
            row = json.loads(raw_line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"experiments.jsonl line {line_number} is invalid JSON") from exc
        if not isinstance(row, dict):
            raise ValueError(f"experiments.jsonl line {line_number} must be a JSON object")
        event_type = row.get("event_type")
        expected_keys = registered_keys if event_type == "registered" else result_keys
        if event_type not in {"registered", "result"} or set(row) != expected_keys:
            raise ValueError(f"experiments.jsonl line {line_number} has invalid event_type/fields")
        event_id = row["event_id"]
        candidate_id = row["candidate_id"]
        if not isinstance(event_id, str) or not event_id or event_id in event_ids:
            raise ValueError("every ledger event_id must be a non-empty unique string")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("every ledger candidate_id must be a non-empty string")
        event_ids.add(event_id)
        timestamp = _utc_timestamp(
            row["timestamp_utc"], f"experiments.jsonl line {line_number}.timestamp_utc"
        )
        if previous_timestamp is not None and timestamp < previous_timestamp:
            raise ValueError("experiment ledger timestamps must be append-order monotonic")
        if timestamp < phase0_started_at:
            raise ValueError("experiment event timestamp predates the Phase-0 freeze")
        if timestamp > validated_at:
            raise ValueError("experiment event timestamp cannot be in the future")
        previous_timestamp = timestamp

        if event_type == "registered":
            if candidate_id in registrations:
                raise ValueError(f"candidate {candidate_id} has multiple registrations")
            parent = row["parent_candidate_id"]
            if parent is not None and (
                not isinstance(parent, str)
                or not parent
                or parent == candidate_id
                or parent not in registrations
            ):
                raise ValueError("parent_candidate_id must name an earlier registered candidate")
            if not isinstance(row["delta"], str) or not row["delta"]:
                raise ValueError("registration delta must be a non-empty string")
            if isinstance(row["seed"], bool) or not isinstance(row["seed"], int):
                raise ValueError("registration seed must be an integer")
            if not isinstance(row["parameters"], dict):
                raise ValueError("registration parameters must be a JSON object")
            if not isinstance(row["public_oos_requested"], bool):
                raise ValueError("public_oos_requested must be a JSON boolean")
            registrations[candidate_id] = (row, timestamp)
            registration_hashes[candidate_id] = _registration_digest(raw_line)
            registration_lines[candidate_id] = raw_line
        else:
            if candidate_id not in registrations or candidate_id in results:
                raise ValueError(
                    f"candidate {candidate_id} result must follow exactly one registration"
                )
            if timestamp <= registrations[candidate_id][1]:
                raise ValueError("candidate result timestamp must be after registration")
            if timestamp > deadline:
                raise ValueError("candidate result timestamp exceeds the research deadline")
            numeric: dict[str, float] = {}
            for field in ("cpu_hours", "wall_clock_hours"):
                value = row[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)):
                    raise ValueError(f"result {field} must be numeric")
                numeric[field] = float(value)
                if not math.isfinite(numeric[field]) or numeric[field] < 0.0:
                    raise ValueError(f"result {field} must be finite and non-negative")
            for field in ("is_metrics", "public_oos_metrics"):
                if row[field] is not None and not isinstance(row[field], dict):
                    raise ValueError(f"result {field} must be an object or null")
            accessed = row["public_oos_accessed"]
            if not isinstance(accessed, bool):
                raise ValueError("public_oos_accessed must be a JSON boolean")
            requested = registrations[candidate_id][0]["public_oos_requested"]
            if accessed and not requested:
                raise ValueError("public OOS access requires prior registration request")
            if not accessed and row["public_oos_metrics"] is not None:
                raise ValueError("public_oos_metrics requires a declared OOS access")
            if accessed and row["public_oos_metrics"] is None and oos_accesses is None:
                raise ValueError("public_oos_metrics must be present when OOS was accessed")
            if not isinstance(row["disposition"], str) or not row["disposition"]:
                raise ValueError("result disposition must be a non-empty string")
            artifact_hashes = row["artifact_hashes"]
            if not isinstance(artifact_hashes, dict) or any(
                not isinstance(name, str)
                or not name
                or not isinstance(digest, str)
                or not re.fullmatch(r"[0-9a-f]{64}", digest)
                for name, digest in artifact_hashes.items()
            ):
                raise ValueError("artifact_hashes must map names to lowercase SHA-256 strings")
            cpu_hours += numeric["cpu_hours"]
            wall_clock_hours += numeric["wall_clock_hours"]
            public_accesses += int(accessed)
            results[candidate_id] = (row, timestamp)
            result_hashes[candidate_id] = _registration_digest(raw_line)
        rows.append(row)

    if set(registrations) != set(results):
        raise ValueError("every registered candidate must have exactly one result event")
    candidate_count = len(registrations)
    if candidate_count < 1:
        raise ValueError("experiments.jsonl must register at least one candidate")
    if candidate_count > int(budget["maximum_material_configurations_per_team"]):
        raise ValueError("team exceeded its material-configuration budget")
    if public_accesses > int(budget["maximum_public_oos_views_per_team"]):
        raise ValueError("team exceeded its public-OOS view budget")
    if oos_accesses is not None:
        if organizer_runs is None:
            raise ValueError("organizer journal runs are required for public-OOS reconciliation")
        _validate_oos_state_against_journal("frozen team", oos_accesses, organizer_runs)
        reserved_candidates = set(organizer_runs)
        for candidate_id, item in organizer_runs.items():
            if candidate_id not in registrations or candidate_id not in results:
                raise ValueError("organizer public-OOS run is missing from the team ledger")
            registration, registered_at = registrations[candidate_id]
            result, result_at = results[candidate_id]
            reservation_record = item.get("reservation")
            result_record = item.get("result")
            if not isinstance(reservation_record, Mapping) or not isinstance(
                result_record, Mapping
            ):
                raise ValueError("every organizer public-OOS reservation must have a result")
            reservation_payload = reservation_record.get("payload")
            result_payload = result_record.get("payload")
            if not isinstance(reservation_payload, Mapping) or not isinstance(
                result_payload, Mapping
            ):
                raise ValueError("organizer public-OOS journal payload is malformed")
            try:
                registered_bytes = base64.b64decode(
                    reservation_payload["registration_bytes_base64"], validate=True
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError("organizer registration bytes are malformed") from exc
            if (
                registration["public_oos_requested"] is not True
                or reservation_payload.get("registration_sha256")
                != registration_hashes[candidate_id]
                or registered_bytes != registration_lines[candidate_id]
            ):
                raise ValueError("public-OOS registration changed after organizer reservation")
            reserved_at = _utc_timestamp(
                reservation_record.get("timestamp_utc"),
                f"organizer reservation {candidate_id}.timestamp_utc",
            )
            finished_at = _utc_timestamp(
                result_record.get("timestamp_utc"),
                f"organizer result {candidate_id}.timestamp_utc",
            )
            if (
                reserved_at > validated_at
                or finished_at > validated_at
                or reserved_at < registered_at
                or finished_at < reserved_at
                or result_at != finished_at
            ):
                raise ValueError("public-OOS organizer timestamps do not bracket the team events")
            if result_payload.get("team_result_sha256") != result_hashes[candidate_id]:
                raise ValueError("team public-OOS result bytes differ from organizer result")
            metrics = result_payload.get("canonical_metrics")
            expected_is = metrics["in_sample"]["metrics"] if metrics is not None else None
            expected_oos = metrics["public_oos"]["metrics"] if metrics is not None else None
            expected_result_fields = {
                "cpu_hours": result_payload.get("cpu_hours"),
                "wall_clock_hours": result_payload.get("wall_clock_hours"),
                "is_metrics": expected_is,
                "public_oos_accessed": True,
                "public_oos_metrics": expected_oos,
                "artifact_hashes": result_payload.get("artifact_hashes"),
            }
            if any(result.get(name) != value for name, value in expected_result_fields.items()):
                raise ValueError("team public-OOS metrics/resources differ from organizer result")
            status = result_payload.get("status")
            failure = result_payload.get("failure_type")
            if (status == "failed") != (isinstance(failure, str) and bool(failure)):
                raise ValueError("failed organizer public-OOS attempts require a failure type only")
            if status == "completed" and expected_oos is None:
                raise ValueError("completed organizer public-OOS attempts require metrics")
        accessed_candidates = {
            candidate_id
            for candidate_id, (result, _timestamp) in results.items()
            if result["public_oos_accessed"] is True
        }
        if reserved_candidates != accessed_candidates:
            raise ValueError("ledger public-OOS accesses must exactly match organizer reservations")
        if len(organizer_runs) > int(budget["maximum_public_oos_views_per_team"]):
            raise ValueError("team exceeded its organizer-reserved public-OOS attempt budget")
    if cpu_hours > float(budget["maximum_cpu_hours_per_team"]):
        raise ValueError("team exceeded its CPU-hour budget")
    if wall_clock_hours > float(budget["maximum_wall_clock_hours_per_team"]):
        raise ValueError("team exceeded its wall-clock-hour budget")
    return rows, candidate_count


def _validate_team_freeze_inputs(
    root: Path,
    team_id: str,
    freeze_commit: str,
    team_state: Mapping[str, object],
) -> tuple[dict[str, str], dict[str, bool], int]:
    from crypto_trade.tournament.top40 import HARD_COMPLIANCE_CHECKS

    artifacts = canonical_artifact_paths(team_id)
    if team_state.get("qr") != "complete" or team_state.get("qe") != "complete":
        raise ValueError(f"{team_id} requires completed QR and QE reviews")
    _verify_review_evidence(root, team_id, team_state, freeze_commit)
    required_names = (*QR_EVIDENCE, *QE_EVIDENCE)
    missing = [
        artifacts[name]
        for name in required_names
        if not (root / artifacts[name]).is_file() or (root / artifacts[name]).is_symlink()
    ]
    if missing:
        raise ValueError(f"team freeze inputs are missing/unsafe: {missing}")
    if (root / artifacts["dependency_lock"]).read_bytes() != (
        root / ROOT_DEPENDENCY_LOCK_PATH
    ).read_bytes():
        raise ValueError("team uv.lock must be byte-identical to root uv.lock")
    freeze_issues = verify_team_freeze(
        team_id,
        freeze_commit,
        artifacts["strategy_source"],
        artifacts,
        root=root,
    )
    if freeze_issues:
        details = "; ".join(f"{issue.code}: {issue.message}" for issue in freeze_issues)
        raise ValueError(f"team freeze verification failed: {details}")
    try:
        compliance = json.loads(
            (root / artifacts["compliance_evidence"]).read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"compliance.json is invalid: {exc}") from exc
    if (
        not isinstance(compliance, dict)
        or set(compliance) != set(HARD_COMPLIANCE_CHECKS)
        or any(value is not True for value in compliance.values())
    ):
        raise ValueError("compliance.json must contain every hard check as JSON true")
    config = _load_config(root / CANONICAL_CONFIG_PATH)
    phase0 = json.loads((root / PHASE0_FREEZE_PATH).read_text(encoding="utf-8"))
    accesses = team_state.get("oos_accesses")
    if not isinstance(accesses, list):
        raise ValueError("team public-OOS reservations are missing")
    state = _read_state(root)
    journal_runs = _organizer_runs(_validate_research_journal(root, state))[team_id]
    _rows, trial_count = _validate_experiment_ledger(
        root / artifacts["trial_ledger"],
        config["research_budget"],
        phase0_started_at=_utc_timestamp(
            phase0.get("frozen_at_utc"), "phase0_freeze.frozen_at_utc"
        ),
        oos_accesses=accesses,
        organizer_runs=journal_runs,
    )
    return artifacts, compliance, trial_count


def _freeze_team(args: argparse.Namespace) -> int:
    """Record one reviewed champion without exposing any canonical cohort result."""
    root = Path.cwd().resolve()
    _require_phase0(root)
    if args.team_id not in TEAM_IDS:
        raise ValueError("team_id must be team-01 through team-10")
    if not isinstance(args.strategy_name, str) or not args.strategy_name.strip():
        raise ValueError("strategy_name must be non-empty")
    freeze_commit = subprocess.run(
        ["git", "rev-parse", "--verify", f"{args.freeze_commit}^{{commit}}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    state = _read_state(root)
    if state.get("phase") != "research":
        raise ValueError("champions may be frozen only during research")
    team_state = state.get("teams", {}).get(args.team_id)
    if not isinstance(team_state, dict) or team_state.get("champion") is not None:
        raise ValueError(f"{args.team_id} already has a frozen champion")
    artifacts, _compliance, trial_count = _validate_team_freeze_inputs(
        root, args.team_id, freeze_commit, team_state
    )
    champion_count = sum(
        isinstance(team.get("champion"), dict)
        for team in state["teams"].values()
        if isinstance(team, dict)
    )
    affected_team_ids = TEAM_IDS if champion_count == len(TEAM_IDS) - 1 else (args.team_id,)
    _verify_research_journal_git_history(
        root,
        state,
        affected_team_ids=affected_team_ids,
    )
    strategy_sha = hashlib.sha256((root / artifacts["strategy_source"]).read_bytes()).hexdigest()
    frozen_at = datetime.now(UTC).isoformat()
    with _edit_run_state(root) as locked:
        if locked.get("phase") != "research":
            raise ValueError("tournament phase changed during champion validation")
        current = locked.get("teams", {}).get(args.team_id)
        if (
            not isinstance(current, dict)
            or current.get("champion") is not None
            or current != team_state
        ):
            raise ValueError(f"{args.team_id} champion state changed during validation")
        _verify_review_evidence(root, args.team_id, current, freeze_commit)
        current["freeze_commit"] = freeze_commit
        current["champion"] = {
            "strategy_name": args.strategy_name.strip(),
            "freeze_commit": freeze_commit,
            "strategy_sha256": strategy_sha,
            "trial_count": trial_count,
            "frozen_at_utc": frozen_at,
        }
        if all(isinstance(locked["teams"][team_id].get("champion"), dict) for team_id in TEAM_IDS):
            locked["phase"] = "cohort_frozen"
    print(f"{args.team_id}: champion frozen at {freeze_commit}")
    return 0


def _build_team_source_manifest(args: argparse.Namespace) -> int:
    """Inventory every non-self team source/evidence file before its final Git commit."""
    root = Path.cwd().resolve()
    _require_phase0(root)
    if args.team_id not in TEAM_IDS:
        raise ValueError("team_id must be team-01 through team-10")
    state = _read_state(root)
    team_state = state.get("teams", {}).get(args.team_id)
    if (
        state.get("phase") != "research"
        or not isinstance(team_state, dict)
        or team_state.get("champion") is not None
    ):
        raise ValueError("team source manifests may be built only before champion freeze")
    team_root = root / f"tournament/top40/teams/{args.team_id}"
    if not team_root.is_dir() or team_root.is_symlink():
        raise ValueError("team namespace is missing or unsafe")
    manifest_path = team_root / "team_source_manifest.json"
    excluded = {manifest_path, team_root / "submission.json", team_root / "artifact_manifest.json"}
    entries: list[dict[str, object]] = []
    for path in sorted(team_root.rglob("*"), key=lambda item: item.as_posix()):
        if path in excluded or path.is_dir():
            continue
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"team source path is not a regular file: {path.relative_to(root)}")
        oid = subprocess.run(
            ["git", "hash-object", str(path)],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        relative = path.relative_to(root).as_posix()
        content = path.read_bytes()
        entries.append(
            {
                "path": relative,
                "git_mode": "100644",
                "git_blob_oid": oid,
                "size": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    payload = {
        "schema_version": 1,
        "team_id": args.team_id,
        "prefit_state_policy": TEAM_SOURCE_POLICY,
        "entries": entries,
    }
    _atomic_write_json(manifest_path, payload)
    print(f"{args.team_id}: source manifest contains {len(entries)} frozen files")
    return 0


def _set_canonical_failure(root: Path, team_id: str, failure_type: str) -> None:
    with _edit_run_state(root) as state:
        team = state.get("teams", {}).get(team_id)
        if isinstance(team, dict) and team.get("canonical_run") == "running":
            team["canonical_run"] = "failed"
            team["canonical_failure_type"] = failure_type
            team["canonical_finished_at_utc"] = datetime.now(UTC).isoformat()


def _objective_lock_payload(
    root: Path,
    state: Mapping[str, object],
    finishing_team_id: str,
    finishing_output_sha256: str,
) -> tuple[dict[str, object], list[Submission]]:
    """Build the exact ten-team objective record before the final state mutation."""
    phase0_path = root / PHASE0_FREEZE_PATH
    phase0 = json.loads(phase0_path.read_text(encoding="utf-8"))
    if not isinstance(phase0, dict) or not isinstance(phase0.get("common_freeze_commit"), str):
        raise ValueError("Phase-0 freeze is malformed during objective locking")
    phase0_record_commit = _unique_first_add_commit(
        root,
        PHASE0_FREEZE_PATH,
        expected_parent=phase0["common_freeze_commit"],
        label="Phase-0 freeze",
    )
    teams_state = state.get("teams")
    if not isinstance(teams_state, dict):
        raise ValueError("run_state teams are malformed during objective locking")
    submissions: list[Submission] = []
    for team_id in TEAM_IDS:
        team = teams_state.get(team_id)
        expected_status = "running" if team_id == finishing_team_id else "complete"
        if not isinstance(team, dict) or team.get("canonical_run") != expected_status:
            raise ValueError(
                f"objective lock requires {team_id} canonical status {expected_status}"
            )
        submission_path = root / f"tournament/top40/teams/{team_id}/submission.json"
        submission = load_submission(submission_path)
        champion = team.get("champion")
        if (
            submission.team_id != team_id
            or not isinstance(champion, dict)
            or champion.get("freeze_commit") != submission.freeze_commit
            or champion.get("strategy_name") != submission.strategy_name
        ):
            raise ValueError(f"objective lock identity binding failed for {team_id}")
        issues = validate_submission(submission) + verify_canonical_artifacts(submission, root=root)
        if issues:
            detail = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
            raise ValueError(f"objective lock validation failed for {team_id}: {detail}")
        submissions.append(submission)
    scores = score_tournament(submissions)
    if any(not score.valid or score.automatic_score is None for score in scores):
        raise ValueError("objective lock requires ten mechanically valid canonical submissions")
    by_team = {score.team_id: score for score in scores}
    team_bindings: list[dict[str, object]] = []
    for submission in sorted(submissions, key=lambda item: item.team_id):
        team = teams_state[submission.team_id]
        assert isinstance(team, dict)
        artifact_path = root / submission.artifacts["artifact_manifest"]
        submission_path = root / f"tournament/top40/teams/{submission.team_id}/submission.json"
        output_sha = (
            finishing_output_sha256
            if submission.team_id == finishing_team_id
            else team.get("canonical_output_sha256")
        )
        if not isinstance(output_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", output_sha):
            raise ValueError(f"canonical reproducibility hash is missing for {submission.team_id}")
        current_output_sha = _canonical_output_sha256(root, submission)
        if current_output_sha != output_sha:
            raise ValueError(
                f"canonical outputs changed after reproducibility check for {submission.team_id}"
            )
        score = by_team[submission.team_id]
        team_bindings.append(
            {
                "team_id": submission.team_id,
                "freeze_commit": submission.freeze_commit,
                "submission_path": submission_path.relative_to(root).as_posix(),
                "submission_sha256": hashlib.sha256(submission_path.read_bytes()).hexdigest(),
                "artifact_manifest_path": submission.artifacts["artifact_manifest"],
                "artifact_manifest_file_sha256": hashlib.sha256(
                    artifact_path.read_bytes()
                ).hexdigest(),
                "artifact_manifest_sha256": submission.artifact_manifest_sha256,
                "canonical_output_sha256": output_sha,
                "automatic_score": score.automatic_score,
                "objective_rank": score.objective_rank,
            }
        )
    locked_at = datetime.now(UTC).isoformat()
    payload: dict[str, object] = {
        "schema_version": 1,
        "locked_at_utc": locked_at,
        "prelock_head_commit": _head_commit(root),
        "phase0_record_commit": phase0_record_commit,
        "phase0_freeze_sha256": hashlib.sha256(phase0_path.read_bytes()).hexdigest(),
        "common_freeze_commit": phase0["common_freeze_commit"],
        "data_manifest_sha256": phase0["data_manifest_sha256"],
        "evaluator_sha256": phase0["evaluator_sha256"],
        "config_sha256": phase0["config_sha256"],
        "cohort_sha256": _cohort_sha256(submissions),
        "teams": team_bindings,
    }
    return payload, submissions


def _canonical_output_sha256(root: Path, submission: Submission) -> str:
    from crypto_trade.tournament.data import sha256_manifest

    names = (
        "daily_returns",
        "double_cost_daily_returns",
        "double_cost_evaluator_returns",
        "events",
        "evaluator_returns",
        "positions",
        "targets",
        "trades",
    )
    paths = [root / submission.artifacts[name] for name in names]
    return sha256_manifest(paths, root=root)[0]


def _verify_independent_canonical_runs(
    first_result: object,
    second_result: object,
    first_output_sha256: str,
    second_output_sha256: str,
    first_output_entries: Sequence[Mapping[str, object]],
    second_output_entries: Sequence[Mapping[str, object]],
) -> None:
    first_fields = getattr(first_result, "submission_fields")()
    second_fields = getattr(second_result, "submission_fields")()
    if (
        second_fields != first_fields
        or second_output_sha256 != first_output_sha256
        or list(second_output_entries) != list(first_output_entries)
    ):
        raise ValueError("independent canonical runs were not byte-for-byte deterministic")


def _finalize_team(args: argparse.Namespace) -> int:
    """Canonical-run one recorded champion only after the ten-team freeze barrier."""
    from crypto_trade.tournament.data import sha256_manifest
    from crypto_trade.tournament.runner import _ORGANIZER_RUN_AUTHORIZATION, run_team

    root = Path.cwd().resolve()
    _require_phase0(root)
    team_id = args.team_id
    if team_id not in TEAM_IDS:
        raise ValueError("team_id must be team-01 through team-10")
    state = _read_state(root)
    if state.get("phase") != "cohort_frozen":
        raise ValueError("canonical reruns require all ten champion SHAs and cohort_frozen phase")
    if not all(isinstance(state["teams"][other].get("champion"), dict) for other in TEAM_IDS):
        raise ValueError("canonical reruns cannot start before all ten champions are frozen")
    team_state = state["teams"][team_id]
    if team_state.get("canonical_run") not in {"pending", "failed"}:
        raise ValueError(f"{team_id} canonical run is not available")
    champion = team_state.get("champion")
    if not isinstance(champion, dict):
        raise ValueError(f"{team_id} champion record is missing")
    freeze_commit = champion.get("freeze_commit")
    strategy_name = champion.get("strategy_name")
    if not isinstance(freeze_commit, str) or not isinstance(strategy_name, str):
        raise ValueError(f"{team_id} champion record is malformed")
    artifacts, compliance, trial_count = _validate_team_freeze_inputs(
        root, team_id, freeze_commit, team_state
    )
    strategy_sha = hashlib.sha256((root / artifacts["strategy_source"]).read_bytes()).hexdigest()
    if strategy_sha != champion.get("strategy_sha256") or trial_count != champion.get(
        "trial_count"
    ):
        raise ValueError("recorded champion hashes/counts changed before canonical rerun")
    with _edit_run_state(root) as locked:
        current = locked["teams"][team_id]
        if locked.get("phase") != "cohort_frozen" or current.get("canonical_run") not in {
            "pending",
            "failed",
        }:
            raise ValueError("canonical state changed during preflight")
        current["canonical_run"] = "running"
        current["canonical_started_at_utc"] = datetime.now(UTC).isoformat()
        current.pop("canonical_failure_type", None)

    team_root = root / "tournament/top40/teams" / team_id
    try:
        first_result = run_team(
            root,
            team_id,
            artifacts["strategy_source"],
            CANONICAL_CONFIG_PATH,
            CANONICAL_MANIFEST_PATH,
            _authorization=_ORGANIZER_RUN_AUTHORIZATION,
        )
        expected_outputs = {
            name: artifacts[name]
            for name in (
                "targets",
                "events",
                "positions",
                "evaluator_returns",
                "double_cost_evaluator_returns",
                "daily_returns",
                "double_cost_daily_returns",
                "trades",
            )
        }
        if dict(first_result.artifacts) != expected_outputs:
            raise ValueError("canonical runner returned non-canonical artifact paths")
        output_paths = [root / expected_outputs[name] for name in sorted(expected_outputs)]
        first_output_sha, first_output_entries = sha256_manifest(output_paths, root=root)
        result = run_team(
            root,
            team_id,
            artifacts["strategy_source"],
            CANONICAL_CONFIG_PATH,
            CANONICAL_MANIFEST_PATH,
            _authorization=_ORGANIZER_RUN_AUTHORIZATION,
        )
        if dict(result.artifacts) != expected_outputs:
            raise ValueError("second canonical runner returned non-canonical artifact paths")
        second_output_sha, second_output_entries = sha256_manifest(output_paths, root=root)
        _verify_independent_canonical_runs(
            first_result,
            result,
            first_output_sha,
            second_output_sha,
            first_output_entries,
            second_output_entries,
        )
        artifact_files = [
            root / value
            for name, value in artifacts.items()
            if name not in {"artifact_manifest", "reproduce_command"}
        ]
        artifact_sha, artifact_entries = sha256_manifest(artifact_files, root=root)
        _atomic_write_json(root / artifacts["artifact_manifest"], artifact_entries)
        evaluator_sha = sha256_manifest(
            [root / path for path in EVALUATOR_SOURCE_PATHS], root=root
        )[0]
        submission = {
            **result.submission_fields(),
            "strategy_name": strategy_name,
            "freeze_commit": freeze_commit,
            "evaluator_sha256": evaluator_sha,
            "dependency_lock_sha256": hashlib.sha256(
                (root / artifacts["dependency_lock"]).read_bytes()
            ).hexdigest(),
            "artifact_manifest_sha256": artifact_sha,
            "trial_count": trial_count,
            "compliance": compliance,
            "artifacts": artifacts,
        }
        submission_path = team_root / "submission.json"
        _atomic_write_json(submission_path, submission)
        parsed = load_submission(submission_path)
        issues = validate_submission(parsed) + verify_canonical_artifacts(parsed, root=root)
        if issues:
            details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
            raise ValueError(f"canonical team finalization failed: {details}")
    except BaseException as exc:
        _set_canonical_failure(root, team_id, type(exc).__name__)
        raise

    objective_payload: dict[str, object] | None = None
    latest_state = _read_state(root)
    if all(
        latest_state["teams"][other].get("canonical_run") == "complete"
        for other in TEAM_IDS
        if other != team_id
    ):
        if (root / OBJECTIVE_LOCK_PATH).exists() or (root / OBJECTIVE_LOCK_PATH).is_symlink():
            _set_canonical_failure(root, team_id, "PreexistingObjectiveLock")
            raise ValueError("objective lock is single-shot and already exists")
        try:
            objective_payload, _objective_submissions = _objective_lock_payload(
                root,
                latest_state,
                team_id,
                second_output_sha,
            )
        except BaseException as exc:
            _set_canonical_failure(root, team_id, type(exc).__name__)
            raise

    with _edit_run_state(root) as locked:
        current = locked["teams"][team_id]
        if current.get("canonical_run") != "running":
            raise ValueError(f"{team_id} canonical state changed during finalization")
        current["canonical_run"] = "complete"
        current["canonical_output_sha256"] = second_output_sha
        current["canonical_finished_at_utc"] = datetime.now(UTC).isoformat()
        if all(locked["teams"][other].get("canonical_run") == "complete" for other in TEAM_IDS):
            if objective_payload is None:
                raise ValueError("tenth completion lacks a validated objective-lock payload")
            if objective_payload["prelock_head_commit"] != _head_commit(root):
                raise ValueError("Git HEAD changed before objective lock could be recorded")
            objective_path = root / OBJECTIVE_LOCK_PATH
            if objective_path.exists() or objective_path.is_symlink():
                raise ValueError("objective lock was created concurrently")
            _atomic_write_json(objective_path, objective_payload)
            objective_sha = hashlib.sha256(objective_path.read_bytes()).hexdigest()
            locked["phase"] = "objective_locked"
            locked["objective_lock"] = {
                "path": OBJECTIVE_LOCK_PATH,
                "sha256": objective_sha,
                "cohort_sha256": objective_payload["cohort_sha256"],
                "locked_at_utc": objective_payload["locked_at_utc"],
            }
    print(f"{team_id}: VALID canonical submission at {submission_path.relative_to(root)}")
    return 0


def _submission_preflight_issues(submission, root: Path) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    try:
        freeze = json.loads((root / PHASE0_FREEZE_PATH).read_text(encoding="utf-8"))
        state = json.loads((root / RUN_STATE_PATH).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return (ValidationIssue("phase0_freeze", str(exc)),)
    if not isinstance(freeze, dict) or not isinstance(state, dict):
        return (ValidationIssue("phase0_freeze", "freeze/state root must be a JSON object"),)
    for field in ("data_manifest_sha256", "evaluator_sha256", "config_sha256"):
        if getattr(submission, field) != freeze.get(field):
            issues.append(
                ValidationIssue(
                    field,
                    f"submission {field} differs from the common Phase-0 freeze",
                )
            )
    team_state = state.get("teams", {}).get(submission.team_id, {})
    champion = team_state.get("champion") if isinstance(team_state, dict) else None
    if (
        not isinstance(team_state, dict)
        or team_state.get("canonical_run") != "complete"
        or team_state.get("qr") != "complete"
        or team_state.get("qe") != "complete"
        or team_state.get("freeze_commit") != submission.freeze_commit
        or not isinstance(champion, dict)
        or champion.get("freeze_commit") != submission.freeze_commit
        or champion.get("strategy_name") != submission.strategy_name
        or champion.get("strategy_sha256") != submission.strategy_sha256
    ):
        issues.append(
            ValidationIssue(
                "run_state",
                "team is not recorded as complete at its submitted freeze commit",
            )
        )
    if isinstance(team_state, dict):
        try:
            _verify_review_evidence(root, submission.team_id, team_state, submission.freeze_commit)
        except ValueError as exc:
            issues.append(ValidationIssue("review_evidence", str(exc)))
    issues.extend(
        verify_team_freeze(
            submission.team_id,
            submission.freeze_commit,
            submission.entrypoint,
            submission.artifacts,
            root=root,
        )
    )
    return tuple(issues)


def _canonical_rerun_issues(submission, root: Path) -> tuple[ValidationIssue, ...]:
    """Rerun the frozen factory and compare its bytes with the submitted artifact manifest."""
    from crypto_trade.tournament.runner import _ORGANIZER_RUN_AUTHORIZATION, run_team

    if validate_submission(submission):
        return ()
    preflight = _submission_preflight_issues(submission, root)
    if preflight:
        return preflight
    try:
        run_team(
            root,
            submission.team_id,
            canonical_artifact_paths(submission.team_id)["strategy_source"],
            CANONICAL_CONFIG_PATH,
            CANONICAL_MANIFEST_PATH,
            _authorization=_ORGANIZER_RUN_AUTHORIZATION,
        )
    except Exception as exc:
        return (ValidationIssue("canonical_rerun", f"canonical rerun failed: {exc}"),)
    return verify_canonical_artifacts(submission, root=root)


def _validate(paths: list[str]) -> int:
    root = Path.cwd().resolve()
    _require_phase0(root)
    failed = False
    for path in paths:
        try:
            submission = load_submission(path)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            failed = True
            print(f"{path}: DISQUALIFIED")
            print(f"  - submission: {exc}")
            continue
        issues = validate_submission(submission) + _canonical_rerun_issues(submission, root)
        if issues:
            failed = True
            print(f"{submission.team_id}: DISQUALIFIED")
            for issue in issues:
                print(f"  - {issue.code}: {issue.message}")
        else:
            print(f"{submission.team_id}: VALID")
    return int(failed)


def _malformed_submission(team_id: str) -> Submission:
    metrics = WindowMetrics(
        net_sharpe=0.0,
        net_sortino=0.0,
        calmar=0.0,
        annualized_return=0.0,
        max_drawdown=0.0,
        positive_quarter_fraction=0.0,
    )
    return Submission(
        team_id=team_id,
        strategy_name="MALFORMED_SUBMISSION",
        freeze_commit="0000000",
        data_manifest_sha256="0" * 64,
        evaluator_sha256="0" * 64,
        config_sha256="0" * 64,
        strategy_sha256="0" * 64,
        dependency_lock_sha256="0" * 64,
        artifact_manifest_sha256="0" * 64,
        entrypoint=f"tournament/top40/teams/{team_id}/strategy.py",
        seeds=(0,),
        trial_count=0,
        in_sample=EvaluationWindow(IS_START, "2024-06-30", metrics),
        public_oos=EvaluationWindow("2024-07-01", "2026-06-30", metrics),
        double_cost_oos_sharpe=0.0,
        regime_sharpe={},
        confidence_intervals={},
        compliance={},
        artifacts={},
    )


def _canonical_team_for_submission_path(path: str, root: Path) -> str | None:
    raw = Path(path)
    resolved = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    for number in range(1, 11):
        team_id = f"team-{number:02d}"
        expected = root / f"tournament/top40/teams/{team_id}/submission.json"
        if resolved == expected:
            return team_id
    return None


def _load_scoring_submissions(
    paths: list[str], root: Path
) -> tuple[list[Submission], dict[str, tuple[ValidationIssue, ...]]]:
    submissions: list[Submission] = []
    issues: dict[str, tuple[ValidationIssue, ...]] = {}
    for index, path in enumerate(paths, start=1):
        path_team = _canonical_team_for_submission_path(path, root)
        raw_path = Path(path)
        load_path = raw_path if raw_path.is_absolute() else root / raw_path
        try:
            submission = load_submission(load_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            team_id = path_team or f"invalid-input-{index:02d}"
            submission = _malformed_submission(team_id)
            issues[team_id] = (
                ValidationIssue("submission", f"malformed submission {path}: {exc}"),
            )
        else:
            if path_team is not None and submission.team_id != path_team:
                submission = _malformed_submission(path_team)
                issues[path_team] = (
                    ValidationIssue(
                        "submission_path",
                        f"{path} does not report its canonical team_id {path_team}",
                    ),
                )
        submissions.append(submission)
    return submissions, issues


def _cohort_sha256(submissions: Sequence[Submission]) -> str:
    bindings = [
        {
            "team_id": submission.team_id,
            "freeze_commit": submission.freeze_commit,
            "artifact_manifest_sha256": submission.artifact_manifest_sha256,
        }
        for submission in sorted(submissions, key=lambda item: item.team_id)
    ]
    encoded = json.dumps(bindings, separators=(",", ":"), sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _critic_adjudication_issues(
    path: str,
    submissions: Sequence[Submission],
    root: Path,
) -> dict[str, tuple[ValidationIssue, ...]]:
    """Parse strict, cohort-bound, artifact-evidenced Critic DQ findings."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Critic adjudications: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {"schema_version", "cohort_sha256", "teams"}:
        raise ValueError(
            "Critic adjudications must have exactly schema_version/cohort_sha256/teams"
        )
    if raw["schema_version"] != 1 or raw["cohort_sha256"] != _cohort_sha256(submissions):
        raise ValueError("Critic adjudications are not bound to this exact frozen cohort")
    teams = raw["teams"]
    by_team = {submission.team_id: submission for submission in submissions}
    if not isinstance(teams, dict) or set(teams) != set(by_team):
        raise ValueError("Critic adjudications must include every submitted team exactly once")

    output: dict[str, tuple[ValidationIssue, ...]] = {}
    for team_id, submission in by_team.items():
        record = teams[team_id]
        if not isinstance(record, dict) or set(record) != {
            "freeze_commit",
            "artifact_manifest_sha256",
            "findings",
        }:
            raise ValueError(f"Critic adjudication record is malformed for {team_id}")
        if (
            record["freeze_commit"] != submission.freeze_commit
            or record["artifact_manifest_sha256"] != submission.artifact_manifest_sha256
        ):
            raise ValueError(f"Critic adjudication binding differs for {team_id}")
        findings = record["findings"]
        if not isinstance(findings, list):
            raise ValueError(f"Critic findings must be an array for {team_id}")
        seen_codes: set[str] = set()
        issues: list[ValidationIssue] = []
        for finding in findings:
            if not isinstance(finding, dict) or set(finding) != {
                "code",
                "evidence_artifact",
                "evidence_sha256",
                "detail",
            }:
                raise ValueError(f"Critic finding is malformed for {team_id}")
            code = finding["code"]
            artifact_name = finding["evidence_artifact"]
            detail = finding["detail"]
            if code not in CRITIC_INTEGRITY_DQ_CODES or code in seen_codes:
                raise ValueError(f"Critic DQ code is forbidden or duplicated for {team_id}: {code}")
            if (
                not isinstance(artifact_name, str)
                or artifact_name == "reproduce_command"
                or artifact_name not in submission.artifacts
            ):
                raise ValueError(f"Critic evidence artifact is invalid for {team_id}")
            relative = submission.artifacts[artifact_name]
            evidence_path = (root / relative).resolve()
            if (
                not evidence_path.is_relative_to(root)
                or not evidence_path.is_file()
                or evidence_path.is_symlink()
                or finding["evidence_sha256"]
                != hashlib.sha256(evidence_path.read_bytes()).hexdigest()
            ):
                raise ValueError(f"Critic evidence hash does not match for {team_id}/{code}")
            if not isinstance(detail, str) or not detail.strip():
                raise ValueError(f"Critic finding requires specific evidence detail for {team_id}")
            seen_codes.add(code)
            issues.append(ValidationIssue(code, detail.strip()))
        output[team_id] = tuple(issues)
    return output


def _canonical_ballot_path(root: Path, value: str, expected: str, label: str) -> Path:
    """Resolve one organizer ballot, requiring its canonical in-repository location."""
    raw = Path(value)
    path = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    expected_path = (root / expected).resolve()
    if path != expected_path:
        raise ValueError(f"{label} must be stored at {expected}")
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"{label} is missing or unsafe: {expected}")
    return path


def _complete_score_map(path: Path, label: str) -> dict[str, float]:
    scores = _score_map(str(path))
    expected = set(TEAM_IDS)
    if set(scores) != expected:
        raise ValueError(f"{label} must score all ten teams exactly once")
    for team_id, score in scores.items():
        if not math.isfinite(score) or not 0.0 <= score <= 15.0:
            raise ValueError(f"{label}.{team_id} must be finite and in [0, 15]")
    return scores


def _locked_cohort(root: Path) -> list[Submission]:
    """Load and reverify the exact ten canonical submissions used for the Critic lock."""
    submissions: list[Submission] = []
    for team_id in TEAM_IDS:
        path = root / canonical_artifact_paths(team_id)["artifact_manifest"]
        submission_path = path.with_name("submission.json")
        try:
            submission = load_submission(submission_path)
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
            raise ValueError(f"cannot lock Critic ballot with malformed {team_id}: {exc}") from exc
        if submission.team_id != team_id:
            raise ValueError(f"canonical submission path is impersonated for {team_id}")
        issues = (
            validate_submission(submission)
            + _submission_preflight_issues(submission, root)
            + verify_canonical_artifacts(submission, root=root)
        )
        if issues:
            detail = "; ".join(f"{issue.code}: {issue.message}" for issue in issues)
            raise ValueError(f"cannot lock Critic ballot before {team_id} revalidates: {detail}")
        submissions.append(submission)
    return submissions


def _verify_objective_lock(
    root: Path, state: Mapping[str, object]
) -> tuple[list[Submission], dict[str, object], str]:
    """Verify the first-add objective record and its exact live cohort bindings."""
    allowed_phases = {
        "objective_locked",
        "critic_locked",
        "dq_confirmed",
        "user_locked",
        "paper_frozen",
    }
    if state.get("phase") not in allowed_phases:
        raise ValueError("objective-lock verification requires an objective-or-later phase")
    path = root / OBJECTIVE_LOCK_PATH
    if not path.is_file() or path.is_symlink():
        raise ValueError("objective lock is missing or unsafe")
    try:
        lock = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid objective lock: {exc}") from exc
    expected_keys = {
        "schema_version",
        "locked_at_utc",
        "prelock_head_commit",
        "phase0_record_commit",
        "phase0_freeze_sha256",
        "common_freeze_commit",
        "data_manifest_sha256",
        "evaluator_sha256",
        "config_sha256",
        "cohort_sha256",
        "teams",
    }
    if not isinstance(lock, dict) or set(lock) != expected_keys or lock["schema_version"] != 1:
        raise ValueError("objective lock has an invalid schema")
    _utc_timestamp(lock["locked_at_utc"], "objective_lock.locked_at_utc")
    record = state.get("objective_lock")
    lock_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    if not isinstance(record, dict) or (
        record.get("path") != OBJECTIVE_LOCK_PATH
        or record.get("sha256") != lock_sha
        or record.get("cohort_sha256") != lock["cohort_sha256"]
        or record.get("locked_at_utc") != lock["locked_at_utc"]
    ):
        raise ValueError("run_state differs from the immutable objective lock")
    if not isinstance(lock["prelock_head_commit"], str):
        raise ValueError("objective lock prelock commit is invalid")
    record_commit = _unique_first_add_commit(
        root,
        OBJECTIVE_LOCK_PATH,
        expected_parent=lock["prelock_head_commit"],
        label="objective lock",
    )
    phase0_path = root / PHASE0_FREEZE_PATH
    phase0 = json.loads(phase0_path.read_text(encoding="utf-8"))
    if not isinstance(phase0, dict) or not isinstance(phase0.get("common_freeze_commit"), str):
        raise ValueError("Phase-0 freeze is malformed during objective verification")
    phase0_record = _unique_first_add_commit(
        root,
        PHASE0_FREEZE_PATH,
        expected_parent=phase0["common_freeze_commit"],
        label="Phase-0 freeze",
    )
    phase0_bindings = {
        "phase0_record_commit": phase0_record,
        "phase0_freeze_sha256": hashlib.sha256(phase0_path.read_bytes()).hexdigest(),
        "common_freeze_commit": phase0["common_freeze_commit"],
        "data_manifest_sha256": phase0["data_manifest_sha256"],
        "evaluator_sha256": phase0["evaluator_sha256"],
        "config_sha256": phase0["config_sha256"],
    }
    if any(lock[field] != value for field, value in phase0_bindings.items()):
        raise ValueError("objective lock Phase-0/evaluator/config/data binding changed")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", phase0_record, lock["prelock_head_commit"]],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise ValueError("objective prelock commit does not descend from the Phase-0 record")

    submissions = _locked_cohort(root)
    scores = score_tournament(submissions)
    by_team = {score.team_id: score for score in scores}
    expected_teams: list[dict[str, object]] = []
    teams_state = state.get("teams")
    if not isinstance(teams_state, dict):
        raise ValueError("run_state teams are malformed during objective verification")
    for submission in sorted(submissions, key=lambda item: item.team_id):
        team = teams_state.get(submission.team_id)
        score = by_team[submission.team_id]
        if (
            not isinstance(team, dict)
            or not isinstance(team.get("canonical_output_sha256"), str)
            or not score.valid
            or score.automatic_score is None
        ):
            raise ValueError(f"objective state/score binding failed for {submission.team_id}")
        if _canonical_output_sha256(root, submission) != team["canonical_output_sha256"]:
            raise ValueError(f"canonical outputs changed after locking for {submission.team_id}")
        submission_path = root / f"tournament/top40/teams/{submission.team_id}/submission.json"
        artifact_path = root / submission.artifacts["artifact_manifest"]
        expected_teams.append(
            {
                "team_id": submission.team_id,
                "freeze_commit": submission.freeze_commit,
                "submission_path": submission_path.relative_to(root).as_posix(),
                "submission_sha256": hashlib.sha256(submission_path.read_bytes()).hexdigest(),
                "artifact_manifest_path": submission.artifacts["artifact_manifest"],
                "artifact_manifest_file_sha256": hashlib.sha256(
                    artifact_path.read_bytes()
                ).hexdigest(),
                "artifact_manifest_sha256": submission.artifact_manifest_sha256,
                "canonical_output_sha256": team["canonical_output_sha256"],
                "automatic_score": score.automatic_score,
                "objective_rank": score.objective_rank,
            }
        )
    if lock["cohort_sha256"] != _cohort_sha256(submissions) or lock["teams"] != expected_teams:
        raise ValueError("objective lock differs from current submissions/artifacts/scores")
    return submissions, lock, record_commit


def _critic_eliminates_every_mechanical_team(
    mechanically_valid: set[str],
    critic_issues: Mapping[str, Sequence[ValidationIssue]],
) -> bool:
    return bool(mechanically_valid) and all(
        critic_issues.get(team_id) for team_id in mechanically_valid
    )


def _lock_critic(args: argparse.Namespace) -> int:
    """Single-shot lock of the complete Critic ballot before a user ballot may exist."""
    root = Path.cwd().resolve()
    _require_phase0(root)
    state = _read_state(root)
    if state.get("phase") != "objective_locked":
        raise ValueError("Critic locking requires the objective_locked phase")
    user_path = root / USER_SCORES_PATH
    if user_path.exists() or user_path.is_symlink():
        raise ValueError(
            f"the user ballot must not exist before Critic lock; remove {USER_SCORES_PATH} "
            "and request it only after locking"
        )
    submissions, _objective_lock, objective_record_commit = _verify_objective_lock(root, state)
    if _head_commit(root) != objective_record_commit:
        raise ValueError(
            "Critic lock must be created directly on the committed objective-lock record"
        )
    lock_path = root / CRITIC_LOCK_PATH
    if lock_path.exists() or lock_path.is_symlink():
        raise ValueError("Critic ballot is already locked")
    for forbidden in (CRITIC_CONFIRMATIONS_PATH, CRITIC_CONFIRMATION_LOCK_PATH):
        if (root / forbidden).exists() or (root / forbidden).is_symlink():
            raise ValueError("Critic confirmations must not exist before the Critic lock")

    scores_path = _canonical_ballot_path(
        root, args.critic_scores, CRITIC_SCORES_PATH, "Critic scores"
    )
    adjudications_path = _canonical_ballot_path(
        root,
        args.critic_adjudications,
        CRITIC_ADJUDICATIONS_PATH,
        "Critic adjudications",
    )
    _require_untracked_new_path(root, CRITIC_SCORES_PATH, "Critic scores")
    _require_untracked_new_path(root, CRITIC_ADJUDICATIONS_PATH, "Critic adjudications")
    _complete_score_map(scores_path, "Critic scores")
    _critic_adjudication_issues(str(adjudications_path), submissions, root)
    cohort_sha = _cohort_sha256(submissions)
    payload = {
        "schema_version": 1,
        "locked_at_utc": datetime.now(UTC).isoformat(),
        "parent_objective_lock_commit": objective_record_commit,
        "objective_lock_sha256": hashlib.sha256(
            (root / OBJECTIVE_LOCK_PATH).read_bytes()
        ).hexdigest(),
        "cohort_sha256": cohort_sha,
        "critic_scores_path": CRITIC_SCORES_PATH,
        "critic_scores_sha256": hashlib.sha256(scores_path.read_bytes()).hexdigest(),
        "critic_adjudications_path": CRITIC_ADJUDICATIONS_PATH,
        "critic_adjudications_sha256": hashlib.sha256(adjudications_path.read_bytes()).hexdigest(),
        "team_ids": list(TEAM_IDS),
    }
    with _edit_run_state(root) as locked:
        if locked.get("phase") != "objective_locked" or locked.get("critic_lock") is not None:
            raise ValueError("tournament state changed before the Critic lock was recorded")
        if lock_path.exists() or lock_path.is_symlink():
            raise ValueError("Critic ballot was locked concurrently")
        _atomic_write_json(lock_path, payload)
        lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
        locked["phase"] = "critic_locked"
        locked["critic_lock"] = {
            "path": CRITIC_LOCK_PATH,
            "sha256": lock_sha,
            "cohort_sha256": cohort_sha,
            "locked_at_utc": payload["locked_at_utc"],
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _verify_critic_lock(
    root: Path,
    state: Mapping[str, object],
    submissions: Sequence[Submission],
    critic_scores_path: str | None,
    critic_adjudications_path: str | None,
    *,
    required_phase: str = "critic_locked",
) -> str:
    """Bind final scoring to the single-shot Critic files and frozen objective cohort."""
    if state.get("phase") != required_phase:
        raise ValueError(f"Critic verification requires the {required_phase} phase")
    if critic_scores_path is None or critic_adjudications_path is None:
        raise ValueError("final scoring requires the locked Critic scores and adjudications")
    lock_path = root / CRITIC_LOCK_PATH
    if not lock_path.is_file() or lock_path.is_symlink():
        raise ValueError("Critic lock file is missing or unsafe")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Critic lock: {exc}") from exc
    expected_keys = {
        "schema_version",
        "locked_at_utc",
        "parent_objective_lock_commit",
        "objective_lock_sha256",
        "cohort_sha256",
        "critic_scores_path",
        "critic_scores_sha256",
        "critic_adjudications_path",
        "critic_adjudications_sha256",
        "team_ids",
    }
    if not isinstance(lock, dict) or set(lock) != expected_keys or lock["schema_version"] != 1:
        raise ValueError("Critic lock has an invalid schema")
    _utc_timestamp(lock["locked_at_utc"], "critic_lock.locked_at_utc")
    record = state.get("critic_lock")
    if not isinstance(record, dict) or set(record) != {
        "path",
        "sha256",
        "cohort_sha256",
        "locked_at_utc",
    }:
        raise ValueError("run_state Critic lock record is missing or malformed")
    lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    if (
        record["path"] != CRITIC_LOCK_PATH
        or record["sha256"] != lock_sha
        or record["cohort_sha256"] != lock["cohort_sha256"]
        or record["locked_at_utc"] != lock["locked_at_utc"]
    ):
        raise ValueError("run_state differs from the immutable Critic lock")
    if lock["team_ids"] != list(TEAM_IDS) or lock["cohort_sha256"] != _cohort_sha256(submissions):
        raise ValueError("Critic lock is not bound to this exact objective cohort")
    objective_submissions, _objective, objective_record_commit = _verify_objective_lock(root, state)
    if [item.team_id for item in objective_submissions] != [item.team_id for item in submissions]:
        raise ValueError("Critic lock cohort differs from the objective-lock cohort")
    if (
        lock["parent_objective_lock_commit"] != objective_record_commit
        or lock["objective_lock_sha256"]
        != hashlib.sha256((root / OBJECTIVE_LOCK_PATH).read_bytes()).hexdigest()
    ):
        raise ValueError("Critic lock is not bound to the immutable objective lock")
    scores_path = _canonical_ballot_path(
        root, critic_scores_path, CRITIC_SCORES_PATH, "Critic scores"
    )
    adjudications_path = _canonical_ballot_path(
        root,
        critic_adjudications_path,
        CRITIC_ADJUDICATIONS_PATH,
        "Critic adjudications",
    )
    if (
        lock["critic_scores_path"] != CRITIC_SCORES_PATH
        or lock["critic_scores_sha256"] != hashlib.sha256(scores_path.read_bytes()).hexdigest()
        or lock["critic_adjudications_path"] != CRITIC_ADJUDICATIONS_PATH
        or lock["critic_adjudications_sha256"]
        != hashlib.sha256(adjudications_path.read_bytes()).hexdigest()
    ):
        raise ValueError("Critic ballot bytes changed after the immutable lock")
    critic_record_commit = _unique_first_add_commit(
        root,
        CRITIC_LOCK_PATH,
        expected_parent=objective_record_commit,
        label="Critic lock",
    )
    scores_record_commit = _unique_first_add_commit(
        root,
        CRITIC_SCORES_PATH,
        expected_parent=objective_record_commit,
        label="Critic scores",
    )
    adjudications_record_commit = _unique_first_add_commit(
        root,
        CRITIC_ADJUDICATIONS_PATH,
        expected_parent=objective_record_commit,
        label="Critic adjudications",
    )
    if {scores_record_commit, adjudications_record_commit} != {critic_record_commit}:
        raise ValueError("Critic files were not first-added with their immutable lock")
    _complete_score_map(scores_path, "Critic scores")
    return critic_record_commit


def _confirmed_critic_issues(
    path: Path,
    submissions: Sequence[Submission],
    critic_issues: Mapping[str, Sequence[ValidationIssue]],
    critic_lock_sha256: str,
) -> dict[str, tuple[ValidationIssue, ...]]:
    """Apply only independently confirmed codes from the already-frozen Critic findings."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Critic confirmations: {exc}") from exc
    if not isinstance(raw, dict) or set(raw) != {
        "schema_version",
        "confirmed_by",
        "critic_lock_sha256",
        "cohort_sha256",
        "teams",
    }:
        raise ValueError("Critic confirmations have an invalid schema")
    if (
        raw["schema_version"] != 1
        or raw["confirmed_by"] != "organizer-user"
        or raw["critic_lock_sha256"] != critic_lock_sha256
        or raw["cohort_sha256"] != _cohort_sha256(submissions)
    ):
        raise ValueError("Critic confirmations are not independently bound to this lock/cohort")
    teams = raw["teams"]
    by_team = {submission.team_id: submission for submission in submissions}
    if not isinstance(teams, dict) or set(teams) != set(by_team):
        raise ValueError("Critic confirmations must include all ten teams exactly once")
    confirmed: dict[str, tuple[ValidationIssue, ...]] = {}
    for team_id, submission in by_team.items():
        team = teams[team_id]
        if not isinstance(team, dict) or set(team) != {
            "freeze_commit",
            "artifact_manifest_sha256",
            "confirmed_codes",
        }:
            raise ValueError(f"Critic confirmation record is malformed for {team_id}")
        codes = team["confirmed_codes"]
        if (
            team["freeze_commit"] != submission.freeze_commit
            or team["artifact_manifest_sha256"] != submission.artifact_manifest_sha256
            or not isinstance(codes, list)
            or any(not isinstance(code, str) for code in codes)
            or len(codes) != len(set(codes))
        ):
            raise ValueError(f"Critic confirmation binding is invalid for {team_id}")
        findings = {issue.code: issue for issue in critic_issues.get(team_id, ())}
        unknown = set(codes) - set(findings)
        if unknown:
            raise ValueError(
                f"Critic confirmations name absent findings for {team_id}: {sorted(unknown)}"
            )
        confirmed[team_id] = tuple(findings[code] for code in codes)
    return confirmed


def _lock_critic_confirmations(args: argparse.Namespace) -> int:
    """Freeze independent integrity confirmations before the later user score ballot."""
    root = Path.cwd().resolve()
    _require_phase0(root)
    state = _read_state(root)
    if state.get("phase") != "critic_locked":
        raise ValueError("Critic confirmations require the critic_locked phase")
    submissions = _locked_cohort(root)
    critic_record_commit = _verify_critic_lock(
        root,
        state,
        submissions,
        CRITIC_SCORES_PATH,
        CRITIC_ADJUDICATIONS_PATH,
    )
    if _head_commit(root) != critic_record_commit:
        raise ValueError("Critic confirmations must directly follow the Critic-lock commit")
    if (root / USER_SCORES_PATH).exists() or (root / USER_SCORES_PATH).is_symlink():
        raise ValueError("the user score ballot must not exist before DQ confirmations lock")
    lock_path = root / CRITIC_CONFIRMATION_LOCK_PATH
    if lock_path.exists() or lock_path.is_symlink():
        raise ValueError("Critic confirmation lock is single-shot")
    confirmations_path = _canonical_ballot_path(
        root,
        args.confirmations,
        CRITIC_CONFIRMATIONS_PATH,
        "Critic confirmations",
    )
    _require_untracked_new_path(root, CRITIC_CONFIRMATIONS_PATH, "Critic confirmations")
    critic_issues = _critic_adjudication_issues(
        str(root / CRITIC_ADJUDICATIONS_PATH), submissions, root
    )
    critic_lock_sha = hashlib.sha256((root / CRITIC_LOCK_PATH).read_bytes()).hexdigest()
    confirmed = _confirmed_critic_issues(
        confirmations_path, submissions, critic_issues, critic_lock_sha
    )
    if _critic_eliminates_every_mechanical_team(set(TEAM_IDS), confirmed):
        raise ValueError(
            "independent confirmations would eliminate every team; manual adjudication required"
        )
    locked_at = datetime.now(UTC).isoformat()
    payload = {
        "schema_version": 1,
        "locked_at_utc": locked_at,
        "parent_critic_lock_commit": critic_record_commit,
        "critic_lock_sha256": critic_lock_sha,
        "cohort_sha256": _cohort_sha256(submissions),
        "confirmations_path": CRITIC_CONFIRMATIONS_PATH,
        "confirmations_sha256": hashlib.sha256(confirmations_path.read_bytes()).hexdigest(),
    }
    with _edit_run_state(root) as locked:
        if locked.get("phase") != "critic_locked":
            raise ValueError("tournament state changed before DQ confirmations were locked")
        if lock_path.exists() or lock_path.is_symlink():
            raise ValueError("Critic confirmation lock was created concurrently")
        _atomic_write_json(lock_path, payload)
        locked["phase"] = "dq_confirmed"
        locked["critic_confirmation_lock"] = {
            "path": CRITIC_CONFIRMATION_LOCK_PATH,
            "sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
            "cohort_sha256": payload["cohort_sha256"],
            "locked_at_utc": locked_at,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _verify_critic_confirmations(
    root: Path,
    state: Mapping[str, object],
    submissions: Sequence[Submission],
    *,
    required_phase: str,
) -> tuple[dict[str, tuple[ValidationIssue, ...]], str]:
    if state.get("phase") != required_phase:
        raise ValueError(f"DQ-confirmation verification requires the {required_phase} phase")
    critic_record_commit = _verify_critic_lock(
        root,
        state,
        submissions,
        CRITIC_SCORES_PATH,
        CRITIC_ADJUDICATIONS_PATH,
        required_phase=required_phase,
    )
    lock_path = root / CRITIC_CONFIRMATION_LOCK_PATH
    if not lock_path.is_file() or lock_path.is_symlink():
        raise ValueError("Critic confirmation lock is missing or unsafe")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Critic confirmation lock: {exc}") from exc
    expected = {
        "schema_version",
        "locked_at_utc",
        "parent_critic_lock_commit",
        "critic_lock_sha256",
        "cohort_sha256",
        "confirmations_path",
        "confirmations_sha256",
    }
    if not isinstance(lock, dict) or set(lock) != expected or lock["schema_version"] != 1:
        raise ValueError("Critic confirmation lock has an invalid schema")
    _utc_timestamp(lock["locked_at_utc"], "critic_confirmation_lock.locked_at_utc")
    record = state.get("critic_confirmation_lock")
    lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    if not isinstance(record, dict) or (
        record.get("path") != CRITIC_CONFIRMATION_LOCK_PATH
        or record.get("sha256") != lock_sha
        or record.get("cohort_sha256") != lock["cohort_sha256"]
        or record.get("locked_at_utc") != lock["locked_at_utc"]
    ):
        raise ValueError("run_state differs from the Critic confirmation lock")
    if (
        lock["parent_critic_lock_commit"] != critic_record_commit
        or lock["critic_lock_sha256"]
        != hashlib.sha256((root / CRITIC_LOCK_PATH).read_bytes()).hexdigest()
        or lock["cohort_sha256"] != _cohort_sha256(submissions)
        or lock["confirmations_path"] != CRITIC_CONFIRMATIONS_PATH
    ):
        raise ValueError("Critic confirmation lock binding is inconsistent")
    confirmation_record_commit = _unique_first_add_commit(
        root,
        CRITIC_CONFIRMATION_LOCK_PATH,
        expected_parent=critic_record_commit,
        label="Critic confirmation lock",
    )
    confirmations_path = root / CRITIC_CONFIRMATIONS_PATH
    confirmations_commit = _unique_first_add_commit(
        root,
        CRITIC_CONFIRMATIONS_PATH,
        expected_parent=critic_record_commit,
        label="Critic confirmations",
    )
    if (
        confirmations_commit != confirmation_record_commit
        or lock["confirmations_sha256"]
        != hashlib.sha256(confirmations_path.read_bytes()).hexdigest()
    ):
        raise ValueError("Critic confirmations were not frozen with their lock")
    critic_issues = _critic_adjudication_issues(
        str(root / CRITIC_ADJUDICATIONS_PATH), submissions, root
    )
    confirmed = _confirmed_critic_issues(
        confirmations_path,
        submissions,
        critic_issues,
        str(lock["critic_lock_sha256"]),
    )
    return confirmed, confirmation_record_commit


def _lock_user_ballot(args: argparse.Namespace) -> int:
    """Freeze the later user score ballot in its own first-add commit stage."""
    root = Path.cwd().resolve()
    _require_phase0(root)
    state = _read_state(root)
    if state.get("phase") != "dq_confirmed":
        raise ValueError("user ballot locking requires the dq_confirmed phase")
    submissions = _locked_cohort(root)
    _confirmed, confirmation_record_commit = _verify_critic_confirmations(
        root, state, submissions, required_phase="dq_confirmed"
    )
    if _head_commit(root) != confirmation_record_commit:
        raise ValueError("user ballot must directly follow the confirmation-lock commit")
    lock_path = root / USER_BALLOT_LOCK_PATH
    if lock_path.exists() or lock_path.is_symlink():
        raise ValueError("user ballot lock is single-shot")
    scores_path = _canonical_ballot_path(root, args.user_scores, USER_SCORES_PATH, "user scores")
    _require_untracked_new_path(root, USER_SCORES_PATH, "user score ballot")
    _complete_score_map(scores_path, "user scores")
    locked_at = datetime.now(UTC).isoformat()
    payload = {
        "schema_version": 1,
        "locked_at_utc": locked_at,
        "parent_confirmation_lock_commit": confirmation_record_commit,
        "confirmation_lock_sha256": hashlib.sha256(
            (root / CRITIC_CONFIRMATION_LOCK_PATH).read_bytes()
        ).hexdigest(),
        "user_scores_path": USER_SCORES_PATH,
        "user_scores_sha256": hashlib.sha256(scores_path.read_bytes()).hexdigest(),
    }
    with _edit_run_state(root) as locked:
        if locked.get("phase") != "dq_confirmed":
            raise ValueError("tournament state changed before the user ballot was locked")
        if lock_path.exists() or lock_path.is_symlink():
            raise ValueError("user ballot lock was created concurrently")
        _atomic_write_json(lock_path, payload)
        locked["phase"] = "user_locked"
        locked["user_ballot_lock"] = {
            "path": USER_BALLOT_LOCK_PATH,
            "sha256": hashlib.sha256(lock_path.read_bytes()).hexdigest(),
            "locked_at_utc": locked_at,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _verify_user_ballot_lock(
    root: Path,
    state: Mapping[str, object],
    submissions: Sequence[Submission],
    *,
    required_phase: str,
) -> tuple[dict[str, tuple[ValidationIssue, ...]], str]:
    if state.get("phase") != required_phase:
        raise ValueError(f"user-ballot verification requires the {required_phase} phase")
    confirmed, confirmation_record_commit = _verify_critic_confirmations(
        root, state, submissions, required_phase=required_phase
    )
    lock_path = root / USER_BALLOT_LOCK_PATH
    if not lock_path.is_file() or lock_path.is_symlink():
        raise ValueError("user ballot lock is missing or unsafe")
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid user ballot lock: {exc}") from exc
    expected = {
        "schema_version",
        "locked_at_utc",
        "parent_confirmation_lock_commit",
        "confirmation_lock_sha256",
        "user_scores_path",
        "user_scores_sha256",
    }
    if not isinstance(lock, dict) or set(lock) != expected or lock["schema_version"] != 1:
        raise ValueError("user ballot lock has an invalid schema")
    _utc_timestamp(lock["locked_at_utc"], "user_ballot_lock.locked_at_utc")
    record = state.get("user_ballot_lock")
    lock_sha = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    if not isinstance(record, dict) or (
        record.get("path") != USER_BALLOT_LOCK_PATH
        or record.get("sha256") != lock_sha
        or record.get("locked_at_utc") != lock["locked_at_utc"]
    ):
        raise ValueError("run_state differs from the immutable user ballot lock")
    if (
        lock["parent_confirmation_lock_commit"] != confirmation_record_commit
        or lock["confirmation_lock_sha256"]
        != hashlib.sha256((root / CRITIC_CONFIRMATION_LOCK_PATH).read_bytes()).hexdigest()
        or lock["user_scores_path"] != USER_SCORES_PATH
    ):
        raise ValueError("user ballot lock binding is inconsistent")
    user_record_commit = _unique_first_add_commit(
        root,
        USER_BALLOT_LOCK_PATH,
        expected_parent=confirmation_record_commit,
        label="user ballot lock",
    )
    scores_path = root / USER_SCORES_PATH
    scores_record_commit = _unique_first_add_commit(
        root,
        USER_SCORES_PATH,
        expected_parent=confirmation_record_commit,
        label="user score ballot",
    )
    if (
        scores_record_commit != user_record_commit
        or lock["user_scores_sha256"] != hashlib.sha256(scores_path.read_bytes()).hexdigest()
    ):
        raise ValueError("user score ballot was not frozen with its first-add lock")
    _complete_score_map(scores_path, "user scores")
    return confirmed, user_record_commit


def _raw_metric_payload(submissions: Sequence[Submission]) -> dict[str, dict[str, object]]:
    return {
        submission.team_id: {
            "trial_count": submission.trial_count,
            "in_sample": dataclasses.asdict(submission.in_sample.metrics),
            "public_oos": dataclasses.asdict(submission.public_oos.metrics),
            "double_cost_oos_sharpe": submission.double_cost_oos_sharpe,
            "regime_sharpe": dict(submission.regime_sharpe),
            "confidence_intervals": dict(submission.confidence_intervals),
        }
        for submission in submissions
    }


def _final_ballot_hashes(root: Path) -> dict[str, str]:
    return {
        "objective_lock_sha256": hashlib.sha256(
            (root / OBJECTIVE_LOCK_PATH).read_bytes()
        ).hexdigest(),
        "critic_lock_sha256": hashlib.sha256((root / CRITIC_LOCK_PATH).read_bytes()).hexdigest(),
        "critic_scores_sha256": hashlib.sha256(
            (root / CRITIC_SCORES_PATH).read_bytes()
        ).hexdigest(),
        "critic_adjudications_sha256": hashlib.sha256(
            (root / CRITIC_ADJUDICATIONS_PATH).read_bytes()
        ).hexdigest(),
        "critic_confirmations_sha256": hashlib.sha256(
            (root / CRITIC_CONFIRMATIONS_PATH).read_bytes()
        ).hexdigest(),
        "critic_confirmation_lock_sha256": hashlib.sha256(
            (root / CRITIC_CONFIRMATION_LOCK_PATH).read_bytes()
        ).hexdigest(),
        "user_scores_sha256": hashlib.sha256((root / USER_SCORES_PATH).read_bytes()).hexdigest(),
        "user_ballot_lock_sha256": hashlib.sha256(
            (root / USER_BALLOT_LOCK_PATH).read_bytes()
        ).hexdigest(),
    }


def _recompute_final_score(
    root: Path, state: Mapping[str, object], *, required_phase: str
) -> tuple[dict[str, object], list[Submission]]:
    """Recompute the immutable final selection from canonical cohort and ballot bytes."""
    submissions = _locked_cohort(root)
    critic_issues, _user_record_commit = _verify_user_ballot_lock(
        root, state, submissions, required_phase=required_phase
    )
    mechanically_valid = {submission.team_id for submission in submissions}
    if _critic_eliminates_every_mechanical_team(mechanically_valid, critic_issues):
        raise ValueError(
            "Critic findings would eliminate every mechanically valid team; winner freeze "
            "is suspended for manual integrity adjudication"
        )
    critic_scores = _complete_score_map(root / CRITIC_SCORES_PATH, "Critic scores")
    user_scores = _complete_score_map(root / USER_SCORES_PATH, "user scores")
    scores = score_tournament(
        submissions,
        critic_scores=critic_scores,
        user_scores=user_scores,
        critic_issues=critic_issues,
    )
    payload: dict[str, object] = {
        "status": "FINAL",
        "cohort_sha256": _cohort_sha256(submissions),
        "leaderboard": [score_as_dict(score) for score in scores],
        "raw_metrics": _raw_metric_payload(submissions),
        "ballot_hashes": _final_ballot_hashes(root),
    }
    return payload, submissions


def _verified_final_score(
    root: Path, state: Mapping[str, object], *, required_phase: str = "user_locked"
) -> tuple[dict[str, object], list[Submission], Submission]:
    """Require the canonical final leaderboard to equal a fresh trusted recomputation."""
    final_path = root / FINAL_SCORE_PATH
    if not final_path.is_file() or final_path.is_symlink():
        raise ValueError(f"final leaderboard is missing or unsafe: {FINAL_SCORE_PATH}")
    expected, submissions = _recompute_final_score(root, state, required_phase=required_phase)
    try:
        observed = json.loads(final_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid final leaderboard: {exc}") from exc
    if observed != expected:
        raise ValueError("canonical final leaderboard differs from trusted recomputation")
    canonical_bytes = (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode()
    if final_path.read_bytes() != canonical_bytes:
        raise ValueError("canonical final leaderboard bytes are not normalized")
    winners = [
        row
        for row in expected["leaderboard"]
        if isinstance(row, dict) and row.get("valid") is True and row.get("rank") == 1
    ]
    if len(winners) != 1:
        raise ValueError("final leaderboard must identify exactly one valid rank-1 winner")
    winner_id = winners[0].get("team_id")
    matches = [submission for submission in submissions if submission.team_id == winner_id]
    if len(matches) != 1:
        raise ValueError("rank-1 winner is absent from the exact frozen cohort")
    return expected, submissions, matches[0]


def _next_utc_8h_boundary(value: datetime) -> datetime:
    """Return the first canonical 00:00/08:00/16:00 UTC boundary strictly after value."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("winner freeze timestamp must be timezone-aware")
    utc = value.astimezone(UTC)
    floor = utc.replace(hour=(utc.hour // 8) * 8, minute=0, second=0, microsecond=0)
    return floor + timedelta(hours=8)


def _git_object_id(root: Path, revision: str, relative: str, expected_type: str) -> str:
    result = subprocess.run(
        ["git", "rev-parse", f"{revision}:{relative}"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    object_id = result.stdout.strip()
    if result.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40,64}", object_id):
        raise ValueError(f"cannot bind {relative} at Git revision {revision}")
    kind = subprocess.run(
        ["git", "cat-file", "-t", object_id],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if kind.returncode != 0 or kind.stdout.strip() != expected_type:
        raise ValueError(f"Git object for {relative} is not a {expected_type}")
    return object_id


def _selection_record_commit(root: Path, winner: Submission) -> tuple[str, str]:
    """Bind organizer selection files and mutable canonical manifests to the current commit."""
    commit = _head_commit(root)
    required = (
        RUN_STATE_PATH,
        FINAL_SCORE_PATH,
        OBJECTIVE_LOCK_PATH,
        CRITIC_LOCK_PATH,
        CRITIC_SCORES_PATH,
        CRITIC_ADJUDICATIONS_PATH,
        CRITIC_CONFIRMATIONS_PATH,
        CRITIC_CONFIRMATION_LOCK_PATH,
        USER_SCORES_PATH,
        USER_BALLOT_LOCK_PATH,
        f"tournament/top40/teams/{winner.team_id}/submission.json",
        winner.artifacts["artifact_manifest"],
    )
    for relative in required:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"selection input is missing or unsafe: {relative}")
        if _git_file_bytes(root, commit, relative) != path.read_bytes():
            raise ValueError(
                f"selection input must be committed and clean before winner freeze: {relative}"
            )
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", winner.freeze_commit, commit],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise ValueError("selection record commit does not descend from the winner freeze commit")
    team_tree = _git_object_id(
        root,
        winner.freeze_commit,
        f"tournament/top40/teams/{winner.team_id}",
        "tree",
    )
    return commit, team_tree


def _artifact_hash_records(root: Path, winner: Submission) -> list[dict[str, object]]:
    path = root / winner.artifacts["artifact_manifest"]
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid winning artifact manifest: {exc}") from exc
    if not isinstance(raw, list) or any(
        not isinstance(entry, dict)
        or set(entry) != {"path", "size", "sha256"}
        or not isinstance(entry["path"], str)
        or not isinstance(entry["size"], int)
        or entry["size"] < 0
        or not isinstance(entry["sha256"], str)
        or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
        for entry in raw
    ):
        raise ValueError("winning artifact manifest has an invalid schema")
    return raw


def _ledger_genesis_sha256(
    final_score_sha256: str,
    winner_freeze_commit: str,
    team_tree_oid: str,
    start_utc: str,
) -> str:
    encoded = "\0".join(
        (
            "top40-forward-paper-v1",
            final_score_sha256,
            winner_freeze_commit,
            team_tree_oid,
            start_utc,
        )
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _winner_freeze_payload(
    root: Path,
    state: Mapping[str, object],
    frozen_at: datetime,
) -> dict[str, object]:
    final_score, _submissions, winner = _verified_final_score(root, state)
    freeze_issues = verify_team_freeze(
        winner.team_id,
        winner.freeze_commit,
        winner.entrypoint,
        winner.artifacts,
        root=root,
    )
    if freeze_issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in freeze_issues)
        raise ValueError(f"winning team freeze no longer verifies: {detail}")
    canonical_issues = verify_canonical_artifacts(winner, root=root)
    if canonical_issues:
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in canonical_issues)
        raise ValueError(f"winning artifacts no longer verify: {detail}")

    if frozen_at.tzinfo is None or frozen_at.utcoffset() is None:
        raise ValueError("winner freeze timestamp must be timezone-aware")
    frozen_at = frozen_at.astimezone(UTC)
    quarantine_start = datetime(2026, 7, 1, tzinfo=UTC)
    if frozen_at < quarantine_start:
        raise ValueError("winner cannot freeze before the public-OOS period has ended")
    paper_start = _next_utc_8h_boundary(frozen_at)
    frozen_at_text = frozen_at.isoformat()
    paper_start_text = paper_start.isoformat()

    selection_commit, team_tree_oid = _selection_record_commit(root, winner)
    phase0_path = root / PHASE0_FREEZE_PATH
    try:
        phase0 = json.loads(phase0_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid Phase-0 freeze during winner binding: {exc}") from exc
    phase0_fields = (
        "common_freeze_commit",
        "data_manifest_sha256",
        "evaluator_sha256",
        "methodology_sha256",
        "config_sha256",
        "snapshot_builder_sha256",
        "root_dependency_lock_sha256",
        "orchestrator_sha256",
    )
    if not isinstance(phase0, dict) or any(
        not isinstance(phase0.get(field), str) for field in phase0_fields
    ):
        raise ValueError("Phase-0 freeze lacks required winner-binding hashes")
    config = _load_config(root / CANONICAL_CONFIG_PATH)
    final_score_sha = hashlib.sha256((root / FINAL_SCORE_PATH).read_bytes()).hexdigest()
    artifact_manifest_path = root / winner.artifacts["artifact_manifest"]
    artifact_records = _artifact_hash_records(root, winner)
    genesis = _ledger_genesis_sha256(
        final_score_sha,
        winner.freeze_commit,
        team_tree_oid,
        paper_start_text,
    )
    return {
        "schema_version": 1,
        "record_type": "top40-forward-paper-freeze",
        "frozen_at_utc": frozen_at_text,
        "selection_record_commit": selection_commit,
        "public_oos_end_inclusive": "2026-06-30",
        "quarantine": {
            "start_utc": quarantine_start.isoformat(),
            "through_winner_freeze_utc": frozen_at_text,
            "end_exclusive_utc": paper_start_text,
            "backfill_as_prospective_evidence_allowed": False,
        },
        "winner": {
            "team_id": winner.team_id,
            "strategy_name": winner.strategy_name,
            "freeze_commit": winner.freeze_commit,
            "entrypoint": winner.entrypoint,
            "team_namespace": f"tournament/top40/teams/{winner.team_id}",
            "team_tree_oid": team_tree_oid,
            "submission_sha256": hashlib.sha256(
                (root / f"tournament/top40/teams/{winner.team_id}/submission.json").read_bytes()
            ).hexdigest(),
            "artifact_manifest_path": winner.artifacts["artifact_manifest"],
            "artifact_manifest_file_sha256": hashlib.sha256(
                artifact_manifest_path.read_bytes()
            ).hexdigest(),
            "artifact_manifest_sha256": winner.artifact_manifest_sha256,
            "artifact_files": artifact_records,
        },
        "selection": {
            "leaderboard_path": FINAL_SCORE_PATH,
            "leaderboard_sha256": final_score_sha,
            "cohort_sha256": final_score["cohort_sha256"],
            "ballot_hashes": final_score["ballot_hashes"],
        },
        "phase0": {
            "freeze_path": PHASE0_FREEZE_PATH,
            "freeze_sha256": hashlib.sha256(phase0_path.read_bytes()).hexdigest(),
            **{field: phase0[field] for field in phase0_fields},
        },
        "forward_paper": {
            "start_utc": paper_start_text,
            "decision_interval": str(config["execution"]["base_interval"]),
            "venue": str(config["universe"]["venue"]),
            "data_source": str(config["data"]["source"]),
            "archive_base_url": str(config["data"]["archive_base_url"]),
            "exchange_info_url": str(config["data"]["exchange_info_url"]),
            "funding_rate_url": str(config["data"]["funding_rate_url"]),
            "execution_mode": "paper-only",
            "live_orders_allowed": False,
            "observation_ledger_path": "reports-top40/forward-paper/observations.jsonl",
            "observation_hash_chain_genesis_sha256": genesis,
        },
    }


def _freeze_winner(args: argparse.Namespace) -> int:
    """Single-shot handoff from the immutable final selection to prospective paper evaluation."""
    del args
    root = Path.cwd().resolve()
    _require_phase0(root)
    state = _read_state(root)
    if state.get("phase") != "user_locked":
        raise ValueError("winner freeze requires final scoring in the user_locked phase")
    freeze_path = root / WINNER_FREEZE_PATH
    if freeze_path.exists() or freeze_path.is_symlink() or state.get("winner_freeze") is not None:
        raise ValueError("winner freeze is single-shot and has already been created")
    payload = _winner_freeze_payload(root, state, datetime.now(UTC))
    winner = payload["winner"]
    paper = payload["forward_paper"]
    assert isinstance(winner, dict) and isinstance(paper, dict)
    with _edit_run_state(root) as locked:
        if locked.get("phase") != "user_locked" or locked.get("winner_freeze") is not None:
            raise ValueError("tournament state changed before winner freeze was recorded")
        if freeze_path.exists() or freeze_path.is_symlink():
            raise ValueError("winner freeze was created concurrently")
        _atomic_write_json(freeze_path, payload)
        freeze_sha = hashlib.sha256(freeze_path.read_bytes()).hexdigest()
        locked["phase"] = "paper_frozen"
        locked["winner_freeze"] = {
            "path": WINNER_FREEZE_PATH,
            "sha256": freeze_sha,
            "winner_team_id": winner["team_id"],
            "winner_freeze_commit": winner["freeze_commit"],
            "selection_record_commit": payload["selection_record_commit"],
            "frozen_at_utc": payload["frozen_at_utc"],
            "forward_paper_start_utc": paper["start_utc"],
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _exact_keys(value: object, expected: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError(f"{label} has an invalid schema")
    return value


def _verify_winner_freeze(args: argparse.Namespace) -> int:
    """Fail closed unless the committed prospective paper handoff is internally consistent."""
    del args
    root = Path.cwd().resolve()
    _require_phase0(root)
    state = _read_state(root)
    if state.get("phase") != "paper_frozen":
        raise ValueError("winner-freeze verification requires the paper_frozen phase")
    path = root / WINNER_FREEZE_PATH
    if not path.is_file() or path.is_symlink():
        raise ValueError("winner-freeze record is missing or unsafe")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid winner-freeze record: {exc}") from exc
    payload = _exact_keys(
        payload,
        {
            "schema_version",
            "record_type",
            "frozen_at_utc",
            "selection_record_commit",
            "public_oos_end_inclusive",
            "quarantine",
            "winner",
            "selection",
            "phase0",
            "forward_paper",
        },
        "winner-freeze record",
    )
    if payload["schema_version"] != 1 or payload["record_type"] != "top40-forward-paper-freeze":
        raise ValueError("winner-freeze record version/type is invalid")
    selection_record_commit = payload["selection_record_commit"]
    if not isinstance(selection_record_commit, str):
        raise ValueError("winner-freeze selection commit is invalid")
    winner_record_commit = _unique_first_add_commit(
        root,
        WINNER_FREEZE_PATH,
        expected_parent=selection_record_commit,
        label="winner freeze",
    )
    if (
        _git_file_bytes(root, winner_record_commit, RUN_STATE_PATH)
        != (root / RUN_STATE_PATH).read_bytes()
    ):
        raise ValueError("winner freeze and paper-frozen run state must share one record commit")
    quarantine = _exact_keys(
        payload["quarantine"],
        {
            "start_utc",
            "through_winner_freeze_utc",
            "end_exclusive_utc",
            "backfill_as_prospective_evidence_allowed",
        },
        "winner-freeze quarantine",
    )
    winner_record = _exact_keys(
        payload["winner"],
        {
            "team_id",
            "strategy_name",
            "freeze_commit",
            "entrypoint",
            "team_namespace",
            "team_tree_oid",
            "submission_sha256",
            "artifact_manifest_path",
            "artifact_manifest_file_sha256",
            "artifact_manifest_sha256",
            "artifact_files",
        },
        "winner-freeze winner",
    )
    selection = _exact_keys(
        payload["selection"],
        {"leaderboard_path", "leaderboard_sha256", "cohort_sha256", "ballot_hashes"},
        "winner-freeze selection",
    )
    phase0_record = _exact_keys(
        payload["phase0"],
        {
            "freeze_path",
            "freeze_sha256",
            "common_freeze_commit",
            "data_manifest_sha256",
            "evaluator_sha256",
            "methodology_sha256",
            "config_sha256",
            "snapshot_builder_sha256",
            "root_dependency_lock_sha256",
            "orchestrator_sha256",
        },
        "winner-freeze Phase-0 binding",
    )
    paper = _exact_keys(
        payload["forward_paper"],
        {
            "start_utc",
            "decision_interval",
            "venue",
            "data_source",
            "archive_base_url",
            "exchange_info_url",
            "funding_rate_url",
            "execution_mode",
            "live_orders_allowed",
            "observation_ledger_path",
            "observation_hash_chain_genesis_sha256",
        },
        "winner-freeze forward-paper binding",
    )

    freeze_sha = hashlib.sha256(path.read_bytes()).hexdigest()
    state_record = state.get("winner_freeze")
    if not isinstance(state_record, dict) or (
        state_record.get("path") != WINNER_FREEZE_PATH
        or state_record.get("sha256") != freeze_sha
        or state_record.get("winner_team_id") != winner_record["team_id"]
        or state_record.get("winner_freeze_commit") != winner_record["freeze_commit"]
        or state_record.get("selection_record_commit") != payload["selection_record_commit"]
        or state_record.get("frozen_at_utc") != payload["frozen_at_utc"]
        or state_record.get("forward_paper_start_utc") != paper["start_utc"]
    ):
        raise ValueError("run_state differs from the immutable winner-freeze record")

    frozen_at = _utc_timestamp(payload["frozen_at_utc"], "winner_freeze.frozen_at_utc")
    paper_start = _utc_timestamp(paper["start_utc"], "winner_freeze.forward_paper.start_utc")
    if (
        payload["public_oos_end_inclusive"] != "2026-06-30"
        or quarantine["start_utc"] != datetime(2026, 7, 1, tzinfo=UTC).isoformat()
        or quarantine["through_winner_freeze_utc"] != payload["frozen_at_utc"]
        or quarantine["end_exclusive_utc"] != paper["start_utc"]
        or quarantine["backfill_as_prospective_evidence_allowed"] is not False
        or paper_start != _next_utc_8h_boundary(frozen_at)
    ):
        raise ValueError("winner-freeze quarantine/start-boundary policy is inconsistent")

    final_score, _submissions, winner = _verified_final_score(
        root, state, required_phase="paper_frozen"
    )
    if (
        selection["leaderboard_path"] != FINAL_SCORE_PATH
        or selection["leaderboard_sha256"]
        != hashlib.sha256((root / FINAL_SCORE_PATH).read_bytes()).hexdigest()
        or selection["cohort_sha256"] != final_score["cohort_sha256"]
        or selection["ballot_hashes"] != final_score["ballot_hashes"]
    ):
        raise ValueError("winner-freeze final selection binding is inconsistent")
    if (
        winner_record["team_id"] != winner.team_id
        or winner_record["strategy_name"] != winner.strategy_name
        or winner_record["freeze_commit"] != winner.freeze_commit
        or winner_record["entrypoint"] != winner.entrypoint
        or winner_record["team_namespace"] != f"tournament/top40/teams/{winner.team_id}"
        or winner_record["artifact_manifest_path"] != winner.artifacts["artifact_manifest"]
        or winner_record["artifact_manifest_sha256"] != winner.artifact_manifest_sha256
    ):
        raise ValueError("winner-freeze rank-1 identity binding is inconsistent")
    freeze_issues = verify_team_freeze(
        winner.team_id,
        winner.freeze_commit,
        winner.entrypoint,
        winner.artifacts,
        root=root,
    )
    canonical_issues = verify_canonical_artifacts(winner, root=root)
    if freeze_issues or canonical_issues:
        combined = freeze_issues + canonical_issues
        detail = "; ".join(f"{issue.code}: {issue.message}" for issue in combined)
        raise ValueError(f"frozen winning bundle no longer verifies: {detail}")

    submission_path = root / f"tournament/top40/teams/{winner.team_id}/submission.json"
    artifact_manifest_path = root / winner.artifacts["artifact_manifest"]
    if (
        winner_record["submission_sha256"]
        != hashlib.sha256(submission_path.read_bytes()).hexdigest()
        or winner_record["artifact_manifest_file_sha256"]
        != hashlib.sha256(artifact_manifest_path.read_bytes()).hexdigest()
        or winner_record["artifact_files"] != _artifact_hash_records(root, winner)
    ):
        raise ValueError("winner-freeze artifact hashes changed after handoff")

    selection_commit = selection_record_commit
    if not isinstance(selection_commit, str) or not re.fullmatch(
        r"[0-9a-f]{40,64}", selection_commit
    ):
        raise ValueError("winner-freeze selection commit is invalid")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", selection_commit, "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise ValueError("winner-freeze selection commit is not an ancestor of HEAD")
    for relative in (
        FINAL_SCORE_PATH,
        OBJECTIVE_LOCK_PATH,
        CRITIC_LOCK_PATH,
        CRITIC_SCORES_PATH,
        CRITIC_ADJUDICATIONS_PATH,
        CRITIC_CONFIRMATIONS_PATH,
        CRITIC_CONFIRMATION_LOCK_PATH,
        USER_SCORES_PATH,
        USER_BALLOT_LOCK_PATH,
        f"tournament/top40/teams/{winner.team_id}/submission.json",
        winner.artifacts["artifact_manifest"],
    ):
        if _git_file_bytes(root, selection_commit, relative) != (root / relative).read_bytes():
            raise ValueError(f"selection-commit binding changed for {relative}")
    try:
        selection_state = json.loads(
            _git_file_bytes(root, selection_commit, RUN_STATE_PATH).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("selection commit contains invalid run_state JSON") from exc
    if (
        not isinstance(selection_state, dict)
        or selection_state.get("phase") != "user_locked"
        or selection_state.get("winner_freeze") is not None
        or any(
            selection_state.get(key) != state.get(key)
            for key in (
                "objective_lock",
                "critic_lock",
                "critic_confirmation_lock",
                "user_ballot_lock",
            )
        )
    ):
        raise ValueError("selection commit is not the pre-handoff user_locked state")
    expected_tree = _git_object_id(
        root,
        winner.freeze_commit,
        f"tournament/top40/teams/{winner.team_id}",
        "tree",
    )
    if winner_record["team_tree_oid"] != expected_tree:
        raise ValueError("winner helper/model Git tree differs from the winner freeze")

    phase0_path = root / PHASE0_FREEZE_PATH
    phase0 = json.loads(phase0_path.read_text(encoding="utf-8"))
    expected_phase0 = {
        "freeze_path": PHASE0_FREEZE_PATH,
        "freeze_sha256": hashlib.sha256(phase0_path.read_bytes()).hexdigest(),
        **{
            field: phase0[field]
            for field in (
                "common_freeze_commit",
                "data_manifest_sha256",
                "evaluator_sha256",
                "methodology_sha256",
                "config_sha256",
                "snapshot_builder_sha256",
                "root_dependency_lock_sha256",
                "orchestrator_sha256",
            )
        },
    }
    if phase0_record != expected_phase0:
        raise ValueError("winner-freeze Phase-0/snapshot/evaluator hashes changed")
    config = _load_config(root / CANONICAL_CONFIG_PATH)
    if (
        paper["decision_interval"] != str(config["execution"]["base_interval"])
        or paper["venue"] != str(config["universe"]["venue"])
        or paper["data_source"] != str(config["data"]["source"])
        or paper["archive_base_url"] != str(config["data"]["archive_base_url"])
        or paper["exchange_info_url"] != str(config["data"]["exchange_info_url"])
        or paper["funding_rate_url"] != str(config["data"]["funding_rate_url"])
        or paper["execution_mode"] != "paper-only"
        or paper["live_orders_allowed"] is not False
        or paper["observation_ledger_path"] != "reports-top40/forward-paper/observations.jsonl"
        or paper["observation_hash_chain_genesis_sha256"]
        != _ledger_genesis_sha256(
            str(selection["leaderboard_sha256"]),
            winner.freeze_commit,
            expected_tree,
            str(paper["start_utc"]),
        )
    ):
        raise ValueError("winner-freeze paper-only data/ledger binding is inconsistent")

    head = _head_commit(root)
    for relative in (WINNER_FREEZE_PATH, RUN_STATE_PATH):
        if _git_file_bytes(root, head, relative) != (root / relative).read_bytes():
            raise ValueError(
                f"commit the immutable paper handoff before live observation: {relative}"
            )
    print(
        f"winner freeze valid: team={winner.team_id} start={paper['start_utc']} "
        f"record_commit={head}"
    )
    return 0


def _score(args: argparse.Namespace) -> int:
    root = Path.cwd().resolve()
    _require_phase0(root)
    state = _read_state(root)
    if args.provisional:
        submissions, load_issues = _load_scoring_submissions(args.submissions, root)
    else:
        expected_paths = {
            (root / f"tournament/top40/teams/{team_id}/submission.json").resolve()
            for team_id in TEAM_IDS
        }
        supplied_paths = [
            (Path(value).resolve() if Path(value).is_absolute() else (root / value).resolve())
            for value in args.submissions
        ]
        if len(supplied_paths) != len(expected_paths) or set(supplied_paths) != expected_paths:
            raise ValueError("final scoring accepts only the ten canonical locked submission paths")
        submissions = _locked_cohort(root)
        load_issues = {}
    expected_teams = set(TEAM_IDS)
    submitted_teams = {submission.team_id for submission in submissions}
    if not args.provisional and submitted_teams != expected_teams:
        raise ValueError(
            "final scoring requires exactly team-01 through team-10; "
            f"missing={sorted(expected_teams - submitted_teams)}, "
            f"extra={sorted(submitted_teams - expected_teams)}"
        )
    if not args.provisional:
        critic_issues, _user_record_commit = _verify_user_ballot_lock(
            root, state, submissions, required_phase="user_locked"
        )
        mechanical_issues = {submission.team_id: () for submission in submissions}
    else:
        critic_issues = {}
        mechanical_issues = {
            submission.team_id: load_issues.get(submission.team_id, ())
            + (
                ()
                if load_issues.get(submission.team_id)
                else _canonical_rerun_issues(submission, root)
            )
            for submission in submissions
        }
    if not args.provisional:
        if args.critic_scores is None or args.critic_adjudications is None:
            raise ValueError("final scoring requires the locked canonical Critic ballot")
        _canonical_ballot_path(root, args.critic_scores, CRITIC_SCORES_PATH, "Critic scores")
        _canonical_ballot_path(
            root,
            args.critic_adjudications,
            CRITIC_ADJUDICATIONS_PATH,
            "Critic adjudications",
        )
    critic_scores = _score_map(args.critic_scores)
    if not args.provisional:
        if args.user_scores is None:
            raise ValueError("final scoring requires the post-lock user ballot")
        user_path = _canonical_ballot_path(
            root,
            args.user_scores,
            USER_SCORES_PATH,
            "user scores",
        )
        user_scores = _complete_score_map(user_path, "user scores")
    else:
        user_scores = _score_map(args.user_scores)
    if not args.provisional:
        if set(critic_scores) != expected_teams:
            raise ValueError("final Critic ballot must score all ten teams")
        mechanically_valid = {
            submission.team_id
            for submission in submissions
            if not validate_submission(submission) and not mechanical_issues[submission.team_id]
        }
        if _critic_eliminates_every_mechanical_team(mechanically_valid, critic_issues):
            raise ValueError(
                "Critic findings would eliminate every mechanically valid team; final scoring "
                "is suspended for manual integrity adjudication"
            )
    scores = score_tournament(
        submissions,
        critic_scores=critic_scores,
        user_scores=user_scores,
        extra_issues=mechanical_issues,
        critic_issues=critic_issues,
    )
    rows = [score_as_dict(score) for score in scores]
    raw_metrics = _raw_metric_payload(submissions)
    payload = {
        "status": "PROVISIONAL" if args.provisional else "FINAL",
        "cohort_sha256": _cohort_sha256(submissions),
        "leaderboard": rows,
        "raw_metrics": raw_metrics,
    }
    if not args.provisional:
        payload["ballot_hashes"] = _final_ballot_hashes(root)
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.json_out:
        Path(args.json_out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    if args.csv_out:
        with Path(args.csv_out).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=(
                    "rank",
                    "objective_rank",
                    "team_id",
                    "valid",
                    "automatic_score",
                    "critic_score",
                    "user_score",
                    "total_score",
                    "paper_eligible",
                    "disqualification_reasons",
                ),
            )
            writer.writeheader()
            for row in rows:
                row["disqualification_reasons"] = " | ".join(row["disqualification_reasons"])
                writer.writerow(row)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    init = subparsers.add_parser(
        "init-teams", help="create the ten isolated team namespaces and resumable run state"
    )
    init.add_argument("--config", default="tournament/top40/config.toml")
    init.add_argument("--force", action="store_true", help="replace existing placeholder files")

    snapshot = subparsers.add_parser(
        "build-snapshot", help="download, checksum, normalize, and freeze Binance public data"
    )
    snapshot.add_argument("--config", default="tournament/top40/config.toml")
    snapshot.add_argument("--output-dir")
    snapshot.add_argument("--manifest")
    snapshot.add_argument("--common-reports")
    snapshot.add_argument(
        "--no-resume", action="store_true", help="redownload archives instead of using cache"
    )

    verify_snapshot = subparsers.add_parser(
        "verify-snapshot", help="offline-verify the frozen snapshot and source provenance"
    )
    verify_snapshot.add_argument("--config", default="tournament/top40/config.toml")
    verify_snapshot.add_argument("--output-dir")
    verify_snapshot.add_argument("--manifest")
    verify_snapshot.add_argument("--common-reports")

    run_team = subparsers.add_parser(
        "run-team", help="consume one registered public-OOS research attempt"
    )
    run_team.add_argument("team_id")
    run_team.add_argument("--candidate-id", required=True)
    run_team.add_argument("--json-out")

    subparsers.add_parser(
        "recover-research-accounting",
        help="replay a valid journal write-ahead tail into team ledgers and run state",
    )

    close_run = subparsers.add_parser(
        "close-interrupted-run",
        help="close one recovered orphan reservation as a failed counted attempt",
    )
    close_run.add_argument("team_id")
    close_run.add_argument("candidate_id")

    subparsers.add_parser(
        "freeze-phase0", help="record common commit and immutable config/evaluator/data hashes"
    )

    review = subparsers.add_parser(
        "mark-review", help="record an explicit organizer-observed QR or QE handoff"
    )
    review.add_argument("team_id")
    review.add_argument("role", choices=("qr", "qe"))

    source_manifest = subparsers.add_parser(
        "build-team-source-manifest",
        help="inventory all auditable source/text/config files before team freeze",
    )
    source_manifest.add_argument("team_id")

    freeze_team = subparsers.add_parser(
        "freeze-team",
        help=("freeze one champion after committing the journal, run_state, and experiment ledger"),
    )
    freeze_team.add_argument("team_id")
    freeze_team.add_argument("--strategy-name", required=True)
    freeze_team.add_argument("--freeze-commit", required=True)

    finalize = subparsers.add_parser(
        "finalize-team", help="canonical-rerun one recorded champion after cohort freeze"
    )
    finalize.add_argument("team_id")

    validate = subparsers.add_parser("validate", help="validate frozen submission manifests")
    validate.add_argument("submissions", nargs="+")

    critic_lock = subparsers.add_parser(
        "lock-critic",
        help="immutably bind the complete Critic ballot before requesting the user ballot",
    )
    critic_lock.add_argument("--critic-scores", default=CRITIC_SCORES_PATH)
    critic_lock.add_argument(
        "--critic-adjudications",
        default=CRITIC_ADJUDICATIONS_PATH,
    )

    confirmation_lock = subparsers.add_parser(
        "lock-critic-confirmations",
        help="lock independent integrity confirmations before requesting user scores",
    )
    confirmation_lock.add_argument("--confirmations", default=CRITIC_CONFIRMATIONS_PATH)

    user_lock = subparsers.add_parser(
        "lock-user-ballot",
        help="first-add lock the later user score ballot before final scoring",
    )
    user_lock.add_argument("--user-scores", default=USER_SCORES_PATH)

    score = subparsers.add_parser("score", help="produce the final tournament leaderboard")
    score.add_argument("submissions", nargs="+")
    score.add_argument("--critic-scores", help="JSON mapping team_id to a score in [0, 15]")
    score.add_argument(
        "--critic-adjudications",
        help="strict cohort/hash-bound Critic integrity findings JSON",
    )
    score.add_argument("--user-scores", help="JSON mapping team_id to a score in [0, 15]")
    score.add_argument("--json-out")
    score.add_argument("--csv-out")
    score.add_argument(
        "--provisional",
        action="store_true",
        help="allow an incomplete roster/ballots and label the output PROVISIONAL",
    )

    subparsers.add_parser(
        "freeze-winner",
        help="single-shot freeze of the rank-1 artifact for next-boundary paper evaluation",
    )
    subparsers.add_parser(
        "verify-winner-freeze",
        help="verify the committed winner handoff before any prospective observation",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "init-teams":
        return _init_teams(args)
    if args.command == "build-snapshot":
        return _build_snapshot(args)
    if args.command == "verify-snapshot":
        return _verify_snapshot(args)
    if args.command == "run-team":
        return _run_team(args)
    if args.command == "recover-research-accounting":
        return _recover_research_accounting(args)
    if args.command == "close-interrupted-run":
        return _close_interrupted_run(args)
    if args.command == "freeze-phase0":
        return _freeze_phase0(args)
    if args.command == "mark-review":
        return _mark_review(args)
    if args.command == "build-team-source-manifest":
        return _build_team_source_manifest(args)
    if args.command == "freeze-team":
        return _freeze_team(args)
    if args.command == "finalize-team":
        return _finalize_team(args)
    if args.command == "validate":
        return _validate(args.submissions)
    if args.command == "lock-critic":
        return _lock_critic(args)
    if args.command == "lock-critic-confirmations":
        return _lock_critic_confirmations(args)
    if args.command == "lock-user-ballot":
        return _lock_user_ballot(args)
    if args.command == "freeze-winner":
        return _freeze_winner(args)
    if args.command == "verify-winner-freeze":
        return _verify_winner_freeze(args)
    return _score(args)


if __name__ == "__main__":
    raise SystemExit(main())
