"""Durable hash-chained lifecycle journal."""

from __future__ import annotations

import contextlib
import fcntl
import hashlib
import json
import os
from collections.abc import Iterator, Mapping
from pathlib import Path

GENESIS = "0" * 64


def _canonical(payload: object) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


@contextlib.contextmanager
def journal_lock(path: str | Path) -> Iterator[None]:
    lock_path = Path(f"{path}.lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def read_records(path: str | Path) -> tuple[Mapping[str, object], ...]:
    source = Path(path)
    if not source.exists():
        return ()
    records: list[Mapping[str, object]] = []
    for number, line in enumerate(source.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            raise ValueError(f"invalid CUP-50 v2 journal line {number}") from error
        records.append(record)
    verify_chain(records)
    return tuple(records)


def verify_chain(records: tuple[Mapping[str, object], ...] | list[Mapping[str, object]]) -> None:
    previous = GENESIS
    for sequence, raw in enumerate(records, start=1):
        record = dict(raw)
        digest = record.pop("record_sha256", None)
        if record.get("sequence") != sequence or record.get("previous_sha256") != previous:
            raise ValueError(f"broken CUP-50 v2 journal chain at sequence {sequence}")
        expected = hashlib.sha256(_canonical(record)).hexdigest()
        if digest != expected:
            raise ValueError(f"CUP-50 v2 journal digest mismatch at sequence {sequence}")
        previous = str(digest)


def append_record(
    path: str | Path, event: str, payload: Mapping[str, object]
) -> Mapping[str, object]:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with journal_lock(destination):
        records = read_records(destination)
        previous = str(records[-1]["record_sha256"]) if records else GENESIS
        body: dict[str, object] = {
            "sequence": len(records) + 1,
            "previous_sha256": previous,
            "event": event,
            "payload": dict(payload),
        }
        record = {**body, "record_sha256": hashlib.sha256(_canonical(body)).hexdigest()}
        with destination.open("ab") as handle:
            handle.write(_canonical(record) + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
    return record
