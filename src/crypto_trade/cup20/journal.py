"""Append-only, hash-chained research journal.

A trial is consumed when it is accepted, before market data are opened, even if the run later
crashes or is abandoned. Records are never deleted, renumbered, replaced or squashed.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "cup20-research-journal-v1"


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _record_digest(record: Mapping[str, Any]) -> str:
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def read_records(path: str | Path) -> tuple[dict[str, Any], ...]:
    """Every record in file order.

    Raises ValueError naming the record's position if a line is not valid JSON. Each line is
    parsed independently, so json.JSONDecodeError's own line/column numbers are relative to
    that single line's content and would otherwise always misreport "line 1" regardless of
    which record in the file actually broke.
    """
    journal = Path(path)
    if not journal.exists():
        return ()
    records: list[dict[str, Any]] = []
    for line in journal.read_text().splitlines():
        if not line.strip():
            continue
        position = len(records) + 1
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"journal record at position {position} is not valid JSON: {exc}"
            ) from exc
    return tuple(records)


def append_record(path: str | Path, event_type: str, payload: Mapping[str, Any]) -> str:
    """Append one chained record and return its digest."""
    journal = Path(path)
    journal.parent.mkdir(parents=True, exist_ok=True)
    existing = read_records(journal)
    record = {
        "schema_version": SCHEMA_VERSION,
        "sequence": len(existing) + 1,
        "event_type": event_type,
        "payload": dict(payload),
        "previous_sha256": existing[-1]["record_sha256"] if existing else None,
    }
    record["record_sha256"] = _record_digest(record)
    with journal.open("a", encoding="utf-8") as handle:
        handle.write(_canonical(record) + "\n")
    return str(record["record_sha256"])


def verify_chain(path: str | Path) -> int:
    """Verify record structure, sequence numbers, parent links and digests. Return the record
    count.

    Fails closed on three structural shapes, alongside the original three chain-integrity
    checks: a record that is not itself a mapping (e.g. a bare `42` -- valid JSON, but not an
    object, so read_records' JSON-syntax-only guard lets it through), a record whose
    `event_type` is not a string, and a record whose `payload` is not a mapping.
    accepted_trial_count deliberately fails OPEN on the same conditions (skips the record, so
    one bad entry cannot take every team's count down) -- this function is the other half of
    that design: the counter stays available, the validator refuses to bless the journal that
    made the skip necessary in the first place.
    """
    records = read_records(path)
    previous: str | None = None
    for index, record in enumerate(records, start=1):
        if not isinstance(record, Mapping):
            raise ValueError(f"journal record at position {index} is not a mapping")
        if record.get("sequence") != index:
            raise ValueError(f"journal sequence break at position {index}")
        if record.get("previous_sha256") != previous:
            raise ValueError(f"journal parent link break at sequence {index}")
        if _record_digest(record) != record.get("record_sha256"):
            raise ValueError(f"journal record digest mismatch at sequence {index}")
        if not isinstance(record.get("event_type"), str):
            raise ValueError(f"journal record event_type is not a string at sequence {index}")
        if not isinstance(record.get("payload"), Mapping):
            raise ValueError(f"journal record payload is not a mapping at sequence {index}")
        previous = str(record["record_sha256"])
    return len(records)


def accepted_trial_count(path: str | Path, team_id: str) -> int:
    """Count accepted material trials for one team.

    A payload that is not itself a mapping (for example a hand-edited or corrupted
    `payload: null`) cannot name any team, so the record is skipped for every team's count --
    the same graceful non-match already given to a mapping that is simply missing the
    `team_id` key -- rather than raising and denying every other team's count over one
    malformed record elsewhere in the shared journal.
    """
    return sum(
        1
        for record in read_records(path)
        if record.get("event_type") == "trial_accepted"
        and isinstance(record.get("payload"), Mapping)
        and record.get("payload", {}).get("team_id") == team_id
    )
