"""Append-only, hash-chained research journal for Top-40 V5.

Every material event is recorded before the thing it authorises happens: a trial is accepted before
market data are opened, a nomination is journalled before selection reads it, a phase launch is
recorded before the process starts. That ordering is what makes the record evidence rather than a
log -- a log written afterwards can only describe what someone believed happened.

Two properties earn their complexity.

**The chain.** Each record carries the digest of its predecessor, so a record cannot be edited,
reordered or removed without invalidating everything after it. Prior editions relied on this to
prove that a restart inherited no evidence from the run it replaced.

**Evaluator faults do not consume a trial.** V4-R9 recorded 86 of 180 trials as failures because
the evaluator raised on one bar, and eleven of fifteen teams lost research budget to it unevenly.
A candidate that is genuinely rejected consumes its slot; an organizer-side fault is recorded and
refunded, because charging a team for the organizer's defect corrupts selection.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from collections.abc import Iterator, Mapping
from pathlib import Path

SCHEMA_VERSION = "top40-v5-journal-v1"
GENESIS = "0" * 64

# Events that consume one of a team's charged trials.
TRIAL_CONSUMING = frozenset({"trial_succeeded", "trial_rejected"})
# Recorded, refunded, and never counted against a team.
TRIAL_REFUNDING = frozenset({"trial_evaluator_fault"})

EVENT_TYPES = frozenset(
    {
        "tournament_activated",
        "phase_launched",
        "scouting_frozen",
        "trial_accepted",
        "trial_succeeded",
        "trial_rejected",
        "trial_evaluator_fault",
        "nominated",
        "retired",
        "sealed_evaluated",
        "selection_frozen",
        "historical_accepted",
        "historical_released",
    }
)


class JournalError(RuntimeError):
    """The journal is missing, malformed, or its chain does not verify."""


def _canonical(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


@dataclasses.dataclass(frozen=True, slots=True)
class Record:
    sequence: int
    event_type: str
    payload: Mapping[str, object]
    previous_sha256: str
    record_sha256: str

    def as_dict(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "sequence": self.sequence,
            "event_type": self.event_type,
            "payload": dict(self.payload),
            "previous_sha256": self.previous_sha256,
            "record_sha256": self.record_sha256,
        }


def _digest(sequence: int, event_type: str, payload: Mapping[str, object], previous: str) -> str:
    body = {
        "schema_version": SCHEMA_VERSION,
        "sequence": sequence,
        "event_type": event_type,
        "payload": dict(payload),
        "previous_sha256": previous,
    }
    return hashlib.sha256(_canonical(body)).hexdigest()


def initialize(path: str | Path) -> Path:
    """Create an empty journal. Refuses to overwrite an existing one."""

    resolved = Path(path)
    if resolved.exists():
        raise JournalError(f"journal already exists: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.touch()
    return resolved


def read(path: str | Path) -> list[Record]:
    """Read and verify the whole chain."""

    resolved = Path(path)
    if not resolved.is_file():
        raise JournalError(f"journal is missing: {resolved}")
    records: list[Record] = []
    previous = GENESIS
    for number, line in enumerate(resolved.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as error:
            raise JournalError(f"journal line {number} is not valid JSON") from error
        if raw.get("schema_version") != SCHEMA_VERSION:
            raise JournalError(f"journal line {number} has an unknown schema version")
        record = Record(
            sequence=int(raw["sequence"]),
            event_type=str(raw["event_type"]),
            payload=raw["payload"],
            previous_sha256=str(raw["previous_sha256"]),
            record_sha256=str(raw["record_sha256"]),
        )
        if record.sequence != len(records):
            raise JournalError(
                f"journal line {number} is out of order: expected sequence {len(records)}"
            )
        if record.previous_sha256 != previous:
            raise JournalError(
                f"journal line {number} does not chain to its predecessor; "
                "a record has been edited, reordered or removed"
            )
        expected = _digest(
            record.sequence, record.event_type, record.payload, record.previous_sha256
        )
        if record.record_sha256 != expected:
            raise JournalError(f"journal line {number} has a tampered digest")
        records.append(record)
        previous = record.record_sha256
    return records


def head(path: str | Path) -> str:
    records = read(path)
    return records[-1].record_sha256 if records else GENESIS


def append(path: str | Path, event_type: str, payload: Mapping[str, object]) -> Record:
    """Append one record, verifying the existing chain first.

    Verifying before writing costs a full read and is worth it: appending onto a chain that no
    longer verifies would bury the evidence of whatever broke it.
    """

    if event_type not in EVENT_TYPES:
        raise JournalError(f"unknown event type: {event_type}")
    resolved = Path(path)
    records = read(resolved)
    sequence = len(records)
    previous = records[-1].record_sha256 if records else GENESIS
    digest = _digest(sequence, event_type, payload, previous)
    record = Record(
        sequence=sequence,
        event_type=event_type,
        payload=dict(payload),
        previous_sha256=previous,
        record_sha256=digest,
    )
    line = json.dumps(record.as_dict(), sort_keys=True, separators=(",", ":")) + "\n"
    # Append and flush to disk before returning: a caller that has been told the trial is accepted
    # must not be able to open market data on the strength of a record still sitting in a buffer.
    with resolved.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    return record


def iter_events(path: str | Path, event_type: str) -> Iterator[Record]:
    for record in read(path):
        if record.event_type == event_type:
            yield record


def charged_trials(path: str | Path) -> dict[str, int]:
    """Trials each team has actually spent.

    A rejected candidate consumes its slot; an evaluator fault does not. Charging a team for the
    organizer's defect is how V4-R9 lost 86 of 180 trials and did so unevenly across the field.
    """

    counts: dict[str, int] = {}
    for record in read(path):
        if record.event_type in TRIAL_CONSUMING:
            team = str(record.payload.get("team_id", ""))
            counts[team] = counts.get(team, 0) + 1
    return dict(sorted(counts.items()))


def refunded_trials(path: str | Path) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in read(path):
        if record.event_type in TRIAL_REFUNDING:
            team = str(record.payload.get("team_id", ""))
            counts[team] = counts.get(team, 0) + 1
    return dict(sorted(counts.items()))


def _assert_disjoint() -> None:
    overlap = TRIAL_CONSUMING & TRIAL_REFUNDING
    if overlap:
        raise JournalError(f"event types both consume and refund a trial: {sorted(overlap)}")
    unknown = (TRIAL_CONSUMING | TRIAL_REFUNDING) - EVENT_TYPES
    if unknown:
        raise JournalError(f"trial accounting refers to unknown event types: {sorted(unknown)}")


_assert_disjoint()


__all__ = [
    "EVENT_TYPES",
    "GENESIS",
    "SCHEMA_VERSION",
    "TRIAL_CONSUMING",
    "TRIAL_REFUNDING",
    "JournalError",
    "Record",
    "append",
    "charged_trials",
    "head",
    "initialize",
    "iter_events",
    "read",
    "refunded_trials",
]
