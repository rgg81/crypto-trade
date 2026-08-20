"""Strict append-only lifecycle journal for the Top-40 V4 tournament."""

from __future__ import annotations

import contextlib
import dataclasses
import datetime as dt
import fcntl
import hashlib
import json
import os
import re
import stat
from collections.abc import Mapping
from pathlib import Path
from types import MappingProxyType
from typing import Any

from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

_SCHEMA_PREFIX = (
    TOP40_V4_LAYOUT.name if TOP40_V4_LAYOUT.name.endswith("-r2") else "top40-v4-r1"
)
SCHEMA_VERSION = f"{_SCHEMA_PREFIX}-lifecycle-journal-v1"
GENESIS_SHA256 = "0" * 64
MAX_RECORD_BYTES = 1_048_576

_SHA256 = re.compile(r"[0-9a-f]{64}")
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
_TOP_KEYS = frozenset(
    {
        "schema_version",
        "sequence",
        "previous_sha256",
        "record_sha256",
        "event_type",
        "recorded_at_utc",
        "payload",
    }
)
_EVENT_KEYS = {
    "is_accepted": frozenset(
        {
            "team_id",
            "run_id",
            "trial_number",
            "candidate_id",
            "purpose",
            "metadata",
            "authority",
            "output_path",
        }
    ),
    "is_succeeded": frozenset(
        {
            "team_id",
            "run_id",
            "candidate_id",
            "request_sha256",
            "summary_path",
            "summary_sha256",
        }
    ),
    "is_failed": frozenset(
        {
            "team_id",
            "run_id",
            "candidate_id",
            "request_sha256",
            "failure",
        }
    ),
    "nominated": frozenset(
        {
            "team_id",
            "candidate_id",
            "success_record_sha256",
            "certificate_path",
            "certificate_sha256",
            "nomination_path",
            "nomination_sha256",
        }
    ),
    "retired": frozenset({"team_id", "reason"}),
    "selection_frozen": frozenset(
        {
            "input_head_sha256",
            "advancing",
            "selection_freeze_path",
            "selection_freeze_sha256",
        }
    ),
    "historical_accepted": frozenset(
        {
            "team_id",
            "candidate_id",
            "run_id",
            "selection_record_sha256",
            "output_path",
        }
    ),
    "historical_started": frozenset(
        {
            "team_id",
            "candidate_id",
            "run_id",
            "request_sha256",
        }
    ),
    "historical_succeeded": frozenset(
        {
            "team_id",
            "candidate_id",
            "run_id",
            "request_sha256",
            "summary_path",
            "summary_sha256",
        }
    ),
    "historical_failed": frozenset(
        {
            "team_id",
            "candidate_id",
            "run_id",
            "request_sha256",
            "failure_code",
        }
    ),
    "release_authorized": frozenset(
        {
            "selection_record_sha256",
            "terminal_record_sha256s",
            "staging_path",
            "release_path",
            "manifest_sha256",
            "bundle_sha256",
        }
    ),
}
if TOP40_V4_LAYOUT.name.endswith("-r2"):
    _EVENT_KEYS["is_accepted"] = frozenset(
        {*_EVENT_KEYS["is_accepted"], "research_session"}
    )


class JournalError(ValueError):
    """The V4 lifecycle journal or a proposed transition is invalid."""


@dataclasses.dataclass(frozen=True, slots=True)
class JournalState:
    records: tuple[Mapping[str, Any], ...]
    head_sha256: str
    trials_by_team: Mapping[str, int]
    is_requests: Mapping[str, Mapping[str, Any]]
    is_terminals: Mapping[str, Mapping[str, Any]]
    is_successes: Mapping[str, Mapping[str, Any]]
    nominations: Mapping[str, Mapping[str, Any]]
    retired: Mapping[str, Mapping[str, Any]]
    selection: Mapping[str, Any] | None
    selection_record_sha256: str | None
    historical_requests: Mapping[str, Mapping[str, Any]]
    historical_starts: Mapping[str, Mapping[str, Any]]
    historical_terminals: Mapping[str, Mapping[str, Any]]
    release: Mapping[str, Any] | None

    @property
    def record_count(self) -> int:
        return len(self.records)


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise JournalError("journal value is not canonical finite ASCII JSON") from exc


def _record_sha256(record: Mapping[str, Any]) -> str:
    unsigned = dict(record)
    unsigned.pop("record_sha256", None)
    return hashlib.sha256(canonical_json_bytes(unsigned)).hexdigest()


def _hash(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise JournalError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or _IDENTIFIER.fullmatch(value) is None:
        raise JournalError(f"{label} is not a safe identifier")
    return value


def _team(value: object) -> str:
    if not isinstance(value, str) or value not in TOP40_V4_LAYOUT.team_ids:
        raise JournalError(
            f"team_id must be {TOP40_V4_LAYOUT.team_ids[0]} through "
            f"{TOP40_V4_LAYOUT.team_ids[-1]}"
        )
    return value


def _text(value: object, label: str, maximum: int = 2048) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > maximum
        or value != value.strip()
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise JournalError(f"{label} must be nonempty bounded single-line text")
    return value


def _validate_payload(event_type: str, payload: object) -> Mapping[str, Any]:
    if event_type not in _EVENT_KEYS:
        raise JournalError(f"unknown V4 journal event type: {event_type}")
    if not isinstance(payload, Mapping) or set(payload) != _EVENT_KEYS[event_type]:
        raise JournalError(f"{event_type} payload has missing or unexpected fields")
    canonical_json_bytes(payload)
    if "team_id" in payload:
        _team(payload["team_id"])
    for key in ("run_id", "candidate_id"):
        if key in payload:
            _identifier(payload[key], key)
    for key in (
        "request_sha256",
        "summary_sha256",
        "success_record_sha256",
        "certificate_sha256",
        "nomination_sha256",
        "input_head_sha256",
        "selection_freeze_sha256",
        "selection_record_sha256",
        "manifest_sha256",
        "bundle_sha256",
    ):
        if key in payload:
            _hash(payload[key], key)
    if event_type == "is_accepted":
        trial = payload["trial_number"]
        if type(trial) is not int or not 1 <= trial <= TOP40_V4_LAYOUT.maximum_trials:
            raise JournalError(
                f"trial_number must be in 1..{TOP40_V4_LAYOUT.maximum_trials}"
            )
        _text(payload["purpose"], "purpose")
        if not isinstance(payload["metadata"], Mapping) or not isinstance(
            payload["authority"], Mapping
        ):
            raise JournalError("accepted trial metadata and authority must be objects")
        if TOP40_V4_LAYOUT.name.endswith("-r2"):
            authority = payload["authority"]
            session = payload["research_session"]
            if not isinstance(session, Mapping) or set(session) != {
                "path",
                "sha256",
                "source_bundle_sha256",
            }:
                raise JournalError("accepted trial research session is malformed")
            _hash(session["sha256"], "research_session.sha256")
            _hash(
                session["source_bundle_sha256"],
                "research_session.source_bundle_sha256",
            )
            if session["source_bundle_sha256"] != authority.get("source_bundle_sha256"):
                raise JournalError("research session differs from accepted source authority")
            expected_path = (
                f"tournament/top40-v4-r2/research-sessions/{payload['team_id']}/"
                f"{session['source_bundle_sha256']}.json"
            )
            if session["path"] != expected_path:
                raise JournalError("research session path differs from accepted identity")
    if event_type.endswith("failed"):
        key = "failure" if event_type == "is_failed" else "failure_code"
        _text(payload[key], key)
    if event_type == "retired":
        _text(payload["reason"], "reason")
    for key in (
        "output_path",
        "summary_path",
        "certificate_path",
        "nomination_path",
        "selection_freeze_path",
        "staging_path",
        "release_path",
    ):
        if key in payload:
            _text(payload[key], key, maximum=4096)
    if event_type == "selection_frozen":
        advancing = payload["advancing"]
        if (
            not isinstance(advancing, list)
            or len(advancing) > TOP40_V4_LAYOUT.advance_count
            or any(not isinstance(team_id, str) for team_id in advancing)
            or len(set(advancing)) != len(advancing)
        ):
            raise JournalError(
                "advancing must be a unique list of at most "
                f"{TOP40_V4_LAYOUT.advance_count} teams"
            )
        for team_id in advancing:
            _team(team_id)
    if event_type == "release_authorized":
        terminal = payload["terminal_record_sha256s"]
        if (
            not isinstance(terminal, list)
            or any(not isinstance(digest, str) for digest in terminal)
            or len(set(terminal)) != len(terminal)
        ):
            raise JournalError("terminal_record_sha256s must be a unique list")
        for digest in terminal:
            _hash(digest, "terminal_record_sha256")
    return payload


def _decode_lines(payload: bytes) -> list[dict[str, Any]]:
    if not payload:
        return []
    lines = payload.splitlines(keepends=True)
    records: list[dict[str, Any]] = []
    for number, line in enumerate(lines, start=1):
        if not line.endswith(b"\n") or line == b"\n" or len(line) > MAX_RECORD_BYTES:
            raise JournalError(f"journal line {number} is blank, truncated, or too large")
        raw = line[:-1]

        def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            value: dict[str, Any] = {}
            for key, item in pairs:
                if key in value:
                    raise JournalError(f"journal line {number} contains duplicate key {key}")
                value[key] = item
            return value

        def reject(value: str) -> None:
            raise JournalError(f"journal line {number} contains nonfinite value {value}")

        try:
            record = json.loads(
                raw.decode("ascii"),
                object_pairs_hook=unique,
                parse_constant=reject,
            )
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise JournalError(f"journal line {number} is invalid JSON") from exc
        if not isinstance(record, dict) or set(record) != _TOP_KEYS:
            raise JournalError(f"journal line {number} has an invalid schema")
        if canonical_json_bytes(record) != raw:
            raise JournalError(f"journal line {number} is not canonical JSON")
        records.append(record)
    return records


def replay_bytes(payload: bytes) -> JournalState:
    records = _decode_lines(payload)
    head = GENESIS_SHA256
    trials = {team_id: 0 for team_id in TOP40_V4_LAYOUT.team_ids}
    is_requests: dict[str, Mapping[str, Any]] = {}
    is_terminals: dict[str, Mapping[str, Any]] = {}
    is_successes: dict[str, Mapping[str, Any]] = {}
    nominations: dict[str, Mapping[str, Any]] = {}
    retired: dict[str, Mapping[str, Any]] = {}
    selection: Mapping[str, Any] | None = None
    selection_record_sha256: str | None = None
    historical_requests: dict[str, Mapping[str, Any]] = {}
    historical_starts: dict[str, Mapping[str, Any]] = {}
    historical_terminals: dict[str, Mapping[str, Any]] = {}
    release: Mapping[str, Any] | None = None
    seen_candidates: set[tuple[str, str]] = set()
    seen_run_ids: set[str] = set()
    previous_time: dt.datetime | None = None

    for expected_sequence, record in enumerate(records, start=1):
        if record["schema_version"] != SCHEMA_VERSION:
            raise JournalError("journal schema_version changed")
        if record["sequence"] != expected_sequence or record["previous_sha256"] != head:
            raise JournalError("journal sequence or hash chain is broken")
        if (
            not isinstance(record["recorded_at_utc"], str)
            or _UTC.fullmatch(record["recorded_at_utc"]) is None
        ):
            raise JournalError("recorded_at_utc is not canonical UTC")
        recorded_time = dt.datetime.strptime(
            record["recorded_at_utc"], "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=dt.UTC)
        if previous_time is not None and recorded_time < previous_time:
            raise JournalError("journal timestamps move backwards")
        event_type = record["event_type"]
        if not isinstance(event_type, str):
            raise JournalError("event_type must be a string")
        event = _validate_payload(event_type, record["payload"])
        digest = _record_sha256(record)
        if record["record_sha256"] != digest:
            raise JournalError("journal record hash is invalid")

        if event_type == "is_accepted":
            if selection is not None:
                raise JournalError("IS trial accepted after selection freeze")
            team_id = str(event["team_id"])
            candidate_key = (team_id, str(event["candidate_id"]))
            if candidate_key in seen_candidates:
                raise JournalError("candidate consumed more than one IS observation")
            if event["trial_number"] != trials[team_id] + 1:
                raise JournalError("team trial numbering is not contiguous")
            run_id = str(event["run_id"])
            if run_id in seen_run_ids:
                raise JournalError("duplicate tournament run_id")
            trials[team_id] += 1
            seen_candidates.add(candidate_key)
            seen_run_ids.add(run_id)
            is_requests[digest] = record
        elif event_type in {"is_succeeded", "is_failed"}:
            request_hash = str(event["request_sha256"])
            request = is_requests.get(request_hash)
            if request is None or request_hash in is_terminals:
                raise JournalError("IS terminal does not reference one pending request")
            accepted = request["payload"]
            for key in ("team_id", "run_id", "candidate_id"):
                if event[key] != accepted[key]:
                    raise JournalError("IS terminal identity differs from its request")
            is_terminals[request_hash] = record
            if event_type == "is_succeeded":
                is_successes[digest] = record
        elif event_type in {"nominated", "retired"}:
            if selection is not None:
                raise JournalError("team disposition changed after selection freeze")
            team_id = str(event["team_id"])
            if team_id in nominations or team_id in retired:
                raise JournalError("team has more than one terminal IS disposition")
            if event_type == "retired":
                if trials[team_id] < 8:
                    raise JournalError("team retired before eight accepted trials")
                retired[team_id] = record
            else:
                if trials[team_id] < 8:
                    raise JournalError("team nominated before eight accepted trials")
                success = is_successes.get(str(event["success_record_sha256"]))
                if success is None or success["payload"]["team_id"] != team_id:
                    raise JournalError("nomination does not reference a team success")
                if success["payload"]["candidate_id"] != event["candidate_id"]:
                    raise JournalError("nomination candidate differs from its success")
                nominations[team_id] = record
        elif event_type == "selection_frozen":
            if selection is not None or release is not None:
                raise JournalError("selection was frozen more than once")
            if set(nominations) | set(retired) != set(TOP40_V4_LAYOUT.team_ids):
                raise JournalError("selection frozen before all teams were resolved")
            if event["input_head_sha256"] != head:
                raise JournalError("selection does not bind its exact input journal head")
            if any(team_id not in nominations for team_id in event["advancing"]):
                raise JournalError("selection advances a non-nominated team")
            selection = event
            selection_record_sha256 = digest
        elif event_type == "historical_accepted":
            if selection is None or selection_record_sha256 is None or release is not None:
                raise JournalError("historical observation is outside the frozen final phase")
            team_id = str(event["team_id"])
            if team_id not in selection["advancing"]:
                raise JournalError("historical observation is for a non-finalist")
            if event["selection_record_sha256"] != selection_record_sha256:
                raise JournalError("historical observation binds the wrong selection")
            if team_id in historical_requests:
                raise JournalError("finalist received more than one historical observation")
            run_id = str(event["run_id"])
            if run_id in seen_run_ids:
                raise JournalError("duplicate tournament run_id")
            nomination = nominations[team_id]["payload"]
            if event["candidate_id"] != nomination["candidate_id"]:
                raise JournalError("historical candidate differs from frozen nomination")
            seen_run_ids.add(run_id)
            historical_requests[team_id] = record
        elif event_type == "historical_started":
            team_id = str(event["team_id"])
            request = historical_requests.get(team_id)
            if (
                selection is None
                or set(historical_requests) != set(selection["advancing"])
                or request is None
                or team_id in historical_starts
                or team_id in historical_terminals
                or event["request_sha256"] != request["record_sha256"]
            ):
                raise JournalError("historical start does not reference one accepted finalist")
            accepted = request["payload"]
            for key in ("team_id", "run_id", "candidate_id"):
                if event[key] != accepted[key]:
                    raise JournalError("historical start identity differs from its request")
            historical_starts[team_id] = record
        elif event_type in {"historical_succeeded", "historical_failed"}:
            team_id = str(event["team_id"])
            request = historical_requests.get(team_id)
            if (
                request is None
                or team_id not in historical_starts
                or team_id in historical_terminals
            ):
                raise JournalError("historical terminal does not reference one pending finalist")
            accepted = request["payload"]
            if event["request_sha256"] != request["record_sha256"]:
                raise JournalError("historical terminal binds the wrong request")
            for key in ("team_id", "run_id", "candidate_id"):
                if event[key] != accepted[key]:
                    raise JournalError("historical terminal identity differs from its request")
            historical_terminals[team_id] = record
        elif event_type == "release_authorized":
            if selection is None or selection_record_sha256 is None or release is not None:
                raise JournalError("historical release has no unique frozen selection")
            finalists = tuple(selection["advancing"])
            if set(historical_terminals) != set(finalists):
                raise JournalError("historical release preceded all terminal observations")
            if event["selection_record_sha256"] != selection_record_sha256:
                raise JournalError("release binds the wrong selection")
            expected_terminals = [
                historical_terminals[team_id]["record_sha256"] for team_id in finalists
            ]
            if event["terminal_record_sha256s"] != expected_terminals:
                raise JournalError("release terminal list is incomplete or out of order")
            release = event
        head = digest
        previous_time = recorded_time

    return JournalState(
        records=tuple(MappingProxyType(dict(record)) for record in records),
        head_sha256=head,
        trials_by_team=MappingProxyType(trials),
        is_requests=MappingProxyType(is_requests),
        is_terminals=MappingProxyType(is_terminals),
        is_successes=MappingProxyType(is_successes),
        nominations=MappingProxyType(nominations),
        retired=MappingProxyType(retired),
        selection=selection,
        selection_record_sha256=selection_record_sha256,
        historical_requests=MappingProxyType(historical_requests),
        historical_starts=MappingProxyType(historical_starts),
        historical_terminals=MappingProxyType(historical_terminals),
        release=release,
    )


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def initialize(path: str | Path) -> JournalState:
    """Create or verify an exact empty journal without invoking crash-tail recovery.

    Activation calls this before the frozen seed surface is admitted.  An existing journal is
    therefore authority, not recoverable runtime state: reading it through :func:`read` could
    truncate an unterminated suffix before activation has rejected the pathname or link topology.
    Runtime recovery remains confined to ``read`` and ``append`` after activation.
    """

    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    parent_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_DIRECTORY", 0)
    )
    file_flags = (
        os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        parent_descriptor = os.open(journal.parent, parent_flags)
    except OSError as exc:
        raise JournalError("cannot pin the journal parent during initialization") from exc
    created = False
    try:
        parent_before = os.fstat(parent_descriptor)
        if (
            not stat.S_ISDIR(parent_before.st_mode)
            or parent_before.st_uid != os.geteuid()
            or stat.S_IMODE(parent_before.st_mode) & 0o022
        ):
            raise JournalError("journal parent is not owner-controlled")
        try:
            descriptor = os.open(journal.name, file_flags, dir_fd=parent_descriptor)
        except FileNotFoundError:
            try:
                descriptor = os.open(
                    journal.name,
                    file_flags | os.O_CREAT | os.O_EXCL,
                    0o600,
                    dir_fd=parent_descriptor,
                )
            except OSError as exc:
                raise JournalError("cannot exclusively create the lifecycle journal") from exc
            created = True
        except OSError as exc:
            raise JournalError("cannot safely open the lifecycle journal") from exc
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            before = os.fstat(descriptor)
            if created:
                os.fchmod(descriptor, 0o600)
                before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != os.geteuid()
                or before.st_nlink != 1
                or stat.S_IMODE(before.st_mode) != 0o600
                or before.st_size != 0
            ):
                raise JournalError("activation requires one private byte-empty journal")
            os.lseek(descriptor, 0, os.SEEK_SET)
            payload = os.read(descriptor, 1)
            after = os.fstat(descriptor)
            lexical = os.stat(
                journal.name,
                dir_fd=parent_descriptor,
                follow_symlinks=False,
            )

            def identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
                return (
                    value.st_dev,
                    value.st_ino,
                    value.st_size,
                    value.st_mtime_ns,
                    value.st_nlink,
                )

            if (
                payload != b""
                or identity(before) != identity(after)
                or identity(after) != identity(lexical)
                or not stat.S_ISREG(lexical.st_mode)
                or lexical.st_uid != os.geteuid()
                or stat.S_IMODE(lexical.st_mode) != 0o600
            ):
                raise JournalError("lifecycle journal changed during initialization")
            parent_after = os.fstat(parent_descriptor)
            parent_lexical = journal.parent.lstat()
            if (
                (parent_before.st_dev, parent_before.st_ino)
                != (parent_after.st_dev, parent_after.st_ino)
                or (parent_after.st_dev, parent_after.st_ino)
                != (parent_lexical.st_dev, parent_lexical.st_ino)
                or not stat.S_ISDIR(parent_lexical.st_mode)
            ):
                raise JournalError("journal parent changed during initialization")
            if created:
                os.fsync(descriptor)
                os.fsync(parent_descriptor)
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
    finally:
        os.close(parent_descriptor)
    return replay_bytes(b"")


def _open_journal(path: Path) -> int:
    flags = os.O_RDWR | os.O_CREAT
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    metadata = os.fstat(descriptor)
    if not stat.S_ISREG(metadata.st_mode):
        os.close(descriptor)
        raise JournalError("journal must be a regular file")
    return descriptor


def _read_descriptor(descriptor: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    while True:
        chunk = os.read(descriptor, 1024 * 1024)
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)


def _recover_unterminated_tail(descriptor: int, payload: bytes) -> bytes:
    """Discard only bytes after the last committed newline under an exclusive lock.

    A newline is the commit marker for one journal record. A newline-terminated malformed record
    is never repaired: replay remains fail-closed. Only a fragment left by an interrupted append
    can be truncated, and the complete prefix must verify before any mutation occurs.
    """

    if not payload or payload.endswith(b"\n"):
        return payload
    boundary = payload.rfind(b"\n") + 1
    committed = payload[:boundary]
    replay_bytes(committed)
    os.ftruncate(descriptor, boundary)
    os.fsync(descriptor)
    return committed


def read(path: str | Path) -> JournalState:
    journal = Path(path)
    if not journal.exists():
        raise JournalError("V4 lifecycle journal is missing")
    descriptor = _open_journal(journal)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        payload = _recover_unterminated_tail(descriptor, _read_descriptor(descriptor))
        return replay_bytes(payload)
    finally:
        os.close(descriptor)


def append(
    path: str | Path,
    event_type: str,
    payload: Mapping[str, Any],
    *,
    recorded_at_utc: str | None = None,
) -> Mapping[str, Any]:
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    descriptor = _open_journal(journal)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        existing = _recover_unterminated_tail(descriptor, _read_descriptor(descriptor))
        state = replay_bytes(existing)
        timestamp = recorded_at_utc or dt.datetime.now(dt.UTC).replace(microsecond=0).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        if recorded_at_utc is None and state.records:
            previous_timestamp = str(state.records[-1]["recorded_at_utc"])
            if timestamp < previous_timestamp:
                timestamp = previous_timestamp
        record: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "sequence": state.record_count + 1,
            "previous_sha256": state.head_sha256,
            "event_type": event_type,
            "recorded_at_utc": timestamp,
            "payload": dict(payload),
        }
        record["record_sha256"] = _record_sha256(record)
        proposed = existing + canonical_json_bytes(record) + b"\n"
        replay_bytes(proposed)
        os.lseek(descriptor, 0, os.SEEK_END)
        encoded = canonical_json_bytes(record) + b"\n"
        written = 0
        while written < len(encoded):
            count = os.write(descriptor, encoded[written:])
            if count <= 0:
                raise JournalError("short journal append")
            written += count
        os.fsync(descriptor)
        return MappingProxyType(record)
    finally:
        os.close(descriptor)


__all__ = [
    "GENESIS_SHA256",
    "JournalError",
    "JournalState",
    "SCHEMA_VERSION",
    "append",
    "canonical_json_bytes",
    "initialize",
    "read",
    "replay_bytes",
]
