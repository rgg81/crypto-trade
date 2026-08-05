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
    """Every record in file order."""
    journal = Path(path)
    if not journal.exists():
        return ()
    return tuple(json.loads(line) for line in journal.read_text().splitlines() if line.strip())


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
    """Verify sequence numbers, parent links and digests. Return the record count."""
    records = read_records(path)
    previous: str | None = None
    for index, record in enumerate(records, start=1):
        if record.get("sequence") != index:
            raise ValueError(f"journal sequence break at position {index}")
        if record.get("previous_sha256") != previous:
            raise ValueError(f"journal parent link break at sequence {index}")
        if _record_digest(record) != record.get("record_sha256"):
            raise ValueError(f"journal record digest mismatch at sequence {index}")
        previous = str(record["record_sha256"])
    return len(records)


def accepted_trial_count(path: str | Path, team_id: str) -> int:
    """Count accepted material trials for one team."""
    return sum(
        1
        for record in read_records(path)
        if record.get("event_type") == "trial_accepted"
        and record.get("payload", {}).get("team_id") == team_id
    )
