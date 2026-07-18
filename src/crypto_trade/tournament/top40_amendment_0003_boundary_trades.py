"""End-boundary trade-count adapter for the Amendment 0003 stage stitch.

Canonical evaluator artifacts may contain forced-settlement trade rows exactly at a stage's
end-exclusive timestamp.  Amendment 0002 correctly excluded those rows from the validation trade
count.  This prospective adapter applies that same frozen interval rule to public trade-count
reconciliation while rejecting rows before the public start or after the exact terminal boundary.
"""

from __future__ import annotations

import base64
import csv
import dataclasses
import hashlib
import io
import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.tournament import orchestrator_v3
from crypto_trade.tournament import top40_amendment_0003_stage_stitch as stage_stitch
from crypto_trade.tournament import top40_amendment_0003_stitched as base

SCHEMA_VERSION = 1
ADDENDUM_ID = "top40-v3-amendment-0003-end-boundary-trade-count"
PARENT_FREEZE_SHA256 = "f280f57f25ddb9528447b72543db0f0b4358de8f8ae3750aadc23c361aa8cf88"
PARENT_FREEZE_COMMIT = "4d63d3fce4d217fd3f908773afc51863750d47a7"
POLICY_PATH = "tournament/top40-v3/amendments/0003/BOUNDARY-TRADE-ADDENDUM.md"
FREEZE_PATH = "tournament/top40-v3/amendments/0003/boundary-trade-freeze.json"
MODULE_PATH = "src/crypto_trade/tournament/top40_amendment_0003_boundary_trades.py"
SCRIPT_PATH = "scripts/top40_v3_amendment_0003_boundary_trades.py"
TEST_PATH = "tests/tournament/test_top40_amendment_0003_boundary_trades.py"
IMPLEMENTATION_PATHS = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, POLICY_PATH)
TEST_COMMAND = (
    "env",
    "PYTHONPATH=src",
    "PYTHONDONTWRITEBYTECODE=1",
    "uv",
    "run",
    "--frozen",
    "pytest",
    "-q",
    TEST_PATH,
)
MAX_TEST_OUTPUT_BYTES = 4 * 1024 * 1024
_FREEZE_KEYS = frozenset(
    {
        "schema_version",
        "addendum_id",
        "parent_activation",
        "released_validation",
        "implementation",
        "addendum_tests",
        "record_sha256",
    }
)


class BoundaryTradeAddendumError(orchestrator_v3.OrchestratorError):
    """The boundary-trade authority or interval evidence is invalid."""


@dataclasses.dataclass(frozen=True, slots=True)
class BoundaryTradeAuthority:
    freeze_file_sha256: str
    freeze_commit: str
    record_sha256: str
    implementation_commit: str
    parent_freeze_sha256: str
    validation_journal_head_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class ProvisionalBoundaryTradeFreeze:
    freeze_file_sha256: str
    record_sha256: str
    implementation_commit: str
    activation: str = "pending-unique-freeze-commit"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError) as exc:
        raise BoundaryTradeAddendumError("payload is not finite canonical JSON") from exc


def _pretty(payload: object) -> bytes:
    try:
        return (
            json.dumps(payload, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True)
            .encode("ascii")
            + b"\n"
        )
    except (TypeError, ValueError) as exc:
        raise BoundaryTradeAddendumError("payload is not finite pretty JSON") from exc


def _strict_json(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise BoundaryTradeAddendumError(f"{label} contains a duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(payload.decode("ascii"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise BoundaryTradeAddendumError(f"{label} is not valid ASCII JSON") from exc
    if not isinstance(value, Mapping):
        raise BoundaryTradeAddendumError(f"{label} must be an object")
    return value


def _parent_authority(root: Path) -> stage_stitch.StageStitchAuthority:
    authority = stage_stitch.verify_activation(root)
    if (
        authority.freeze_file_sha256 != PARENT_FREEZE_SHA256
        or authority.freeze_commit != PARENT_FREEZE_COMMIT
    ):
        raise BoundaryTradeAddendumError("scored-stage parent authority changed")
    return authority


def _implementation_entries(root: Path) -> tuple[dict[str, object], ...]:
    entries: list[dict[str, object]] = []
    for relative in IMPLEMENTATION_PATHS:
        payload = orchestrator_v3._read_regular_bytes(root, relative)
        entries.append({"path": relative, "size": len(payload), "sha256": _sha256(payload)})
    return tuple(entries)


def _manifest_sha256(entries: Sequence[Mapping[str, object]]) -> str:
    return _sha256(_canonical(list(entries)))


def _verify_implementation_commit(
    root: Path, implementation_commit: str, entries: Sequence[Mapping[str, object]]
) -> None:
    commit = base._verified_commit(root, implementation_commit, "implementation commit")
    for entry in entries:
        result = base._git(root, ["show", f"{commit}:{entry['path']}"])
        if result.returncode != 0 or _sha256(result.stdout) != entry["sha256"]:
            raise BoundaryTradeAddendumError(
                f"implementation commit does not bind {entry['path']}"
            )


def _run_tests(root: Path) -> bytes:
    completed = subprocess.run(
        list(TEST_COMMAND),
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout
    if completed.returncode != 0:
        raise BoundaryTradeAddendumError(
            f"boundary-trade tests failed with exit code {completed.returncode}"
        )
    if not output or len(output) > MAX_TEST_OUTPUT_BYTES:
        raise BoundaryTradeAddendumError("boundary-trade test output is missing or too large")
    orchestrator_v3._parse_passed_count(output)
    return output


def _test_evidence(output: bytes) -> dict[str, object]:
    count = orchestrator_v3._parse_passed_count(output)
    return {
        "command": list(TEST_COMMAND),
        "collected": count,
        "passed": count,
        "output_size": len(output),
        "output_sha256": _sha256(output),
        "output_base64": base64.b64encode(output).decode("ascii"),
    }


def _verify_test_evidence(value: object) -> None:
    if not isinstance(value, Mapping) or set(value) != {
        "command",
        "collected",
        "passed",
        "output_size",
        "output_sha256",
        "output_base64",
    }:
        raise BoundaryTradeAddendumError("boundary-trade test evidence is malformed")
    try:
        output = base64.b64decode(str(value["output_base64"]).encode("ascii"), validate=True)
    except Exception as exc:
        raise BoundaryTradeAddendumError("boundary-trade test encoding is invalid") from exc
    count = orchestrator_v3._parse_passed_count(output)
    if (
        value["command"] != list(TEST_COMMAND)
        or value["collected"] != count
        or value["passed"] != count
        or value["output_size"] != len(output)
        or value["output_sha256"] != _sha256(output)
    ):
        raise BoundaryTradeAddendumError("boundary-trade test evidence changed")


def freeze_activation(
    root: str | Path, *, implementation_commit: str
) -> ProvisionalBoundaryTradeFreeze:
    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        freeze_path = root_path / FREEZE_PATH
        report_path = root_path / base.PUBLIC_REPORT_PATH
        if freeze_path.exists() or freeze_path.is_symlink():
            raise BoundaryTradeAddendumError("boundary-trade freeze already exists")
        if report_path.exists() or report_path.is_symlink():
            raise BoundaryTradeAddendumError("public assessment must be absent before addendum")
        parent_before = _parent_authority(root_path)
        release_before, _ = base._released_authority(root_path)
        entries_before = _implementation_entries(root_path)
        _verify_implementation_commit(root_path, implementation_commit, entries_before)
        output = _run_tests(root_path)
        release_after, _ = base._released_authority(root_path)
        if (
            _parent_authority(root_path) != parent_before
            or release_after != release_before
            or _implementation_entries(root_path) != entries_before
            or report_path.exists()
            or report_path.is_symlink()
        ):
            raise BoundaryTradeAddendumError("boundary-trade activation inputs changed")
        body = {
            "schema_version": SCHEMA_VERSION,
            "addendum_id": ADDENDUM_ID,
            "parent_activation": dataclasses.asdict(parent_before),
            "released_validation": release_before,
            "implementation": {
                "commit": implementation_commit,
                "files": [dict(entry) for entry in entries_before],
                "manifest_sha256": _manifest_sha256(entries_before),
            },
            "addendum_tests": _test_evidence(output),
        }
        record = {**body, "record_sha256": _sha256(_canonical(body))}
        orchestrator_v3._write_new_file(root_path, FREEZE_PATH, _pretty(record), mode=0o444)
        payload = orchestrator_v3._read_regular_bytes(root_path, FREEZE_PATH)
        return ProvisionalBoundaryTradeFreeze(
            freeze_file_sha256=_sha256(payload),
            record_sha256=str(record["record_sha256"]),
            implementation_commit=implementation_commit,
        )


def _verify_freeze_commit(root: Path, implementation_commit: str, freeze_bytes: bytes) -> str:
    additions = base._git(root, ["log", "--diff-filter=A", "--format=%H", "--", FREEZE_PATH])
    commits = [line for line in additions.stdout.decode("ascii", "replace").splitlines() if line]
    if additions.returncode != 0 or len(commits) != 1:
        raise BoundaryTradeAddendumError("boundary-trade addendum requires one freeze commit")
    freeze_commit = base._verified_commit(root, commits[0], "boundary-trade freeze commit")
    direct_parent = base._git(root, ["rev-parse", f"{freeze_commit}^"])
    if (
        direct_parent.returncode != 0
        or direct_parent.stdout.decode("ascii").strip() != implementation_commit
    ):
        raise BoundaryTradeAddendumError("boundary-trade freeze must follow implementation")
    delta = base._git(
        root, ["diff-tree", "--no-commit-id", "--name-status", "-r", freeze_commit]
    )
    if delta.returncode != 0 or delta.stdout.decode("utf-8").splitlines() != [f"A\t{FREEZE_PATH}"]:
        raise BoundaryTradeAddendumError("boundary-trade freeze commit has an unexpected delta")
    committed = base._git(root, ["show", f"{freeze_commit}:{FREEZE_PATH}"])
    if committed.returncode != 0 or committed.stdout != freeze_bytes:
        raise BoundaryTradeAddendumError("live boundary-trade freeze differs from its commit")
    return freeze_commit


def verify_activation(root: str | Path = ".") -> BoundaryTradeAuthority:
    root_path = orchestrator_v3._trusted_root(root)
    freeze_bytes = orchestrator_v3._read_regular_bytes(root_path, FREEZE_PATH)
    record = _strict_json(freeze_bytes, "boundary-trade freeze")
    if _pretty(record) != freeze_bytes or set(record) != set(_FREEZE_KEYS):
        raise BoundaryTradeAddendumError("boundary-trade freeze is not canonical")
    body = {key: record[key] for key in _FREEZE_KEYS - {"record_sha256"}}
    if (
        record["schema_version"] != SCHEMA_VERSION
        or record["addendum_id"] != ADDENDUM_ID
        or record["record_sha256"] != _sha256(_canonical(body))
    ):
        raise BoundaryTradeAddendumError("boundary-trade freeze identity is invalid")
    parent_authority = _parent_authority(root_path)
    release, _ = base._released_authority(root_path)
    if record["parent_activation"] != dataclasses.asdict(parent_authority):
        raise BoundaryTradeAddendumError("scored-stage parent activation changed")
    if record["released_validation"] != release:
        raise BoundaryTradeAddendumError("released validation boundary changed")
    implementation = record["implementation"]
    if not isinstance(implementation, Mapping):
        raise BoundaryTradeAddendumError("boundary-trade implementation is malformed")
    entries = _implementation_entries(root_path)
    if (
        implementation.get("files") != list(entries)
        or implementation.get("manifest_sha256") != _manifest_sha256(entries)
    ):
        raise BoundaryTradeAddendumError("boundary-trade implementation bytes changed")
    implementation_commit = str(implementation.get("commit"))
    _verify_implementation_commit(root_path, implementation_commit, entries)
    _verify_test_evidence(record["addendum_tests"])
    freeze_commit = _verify_freeze_commit(root_path, implementation_commit, freeze_bytes)
    return BoundaryTradeAuthority(
        freeze_file_sha256=_sha256(freeze_bytes),
        freeze_commit=freeze_commit,
        record_sha256=str(record["record_sha256"]),
        implementation_commit=implementation_commit,
        parent_freeze_sha256=parent_authority.freeze_file_sha256,
        validation_journal_head_sha256=str(release["journal_head_sha256"]),
    )


def _scored_trade_counts(payload: bytes) -> tuple[int, int, int]:
    """Count [start, split) and [split, end), excluding rows exactly at end."""

    try:
        rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise BoundaryTradeAddendumError("cannot parse public trade evidence") from exc
    if rows and "timestamp" not in rows[0]:
        raise BoundaryTradeAddendumError("trade evidence lacks timestamp")
    timestamps = pd.DatetimeIndex(
        pd.to_datetime([row["timestamp"] for row in rows], utc=True, errors="raise")
    )
    before = timestamps < base.TRAIN_START
    after = timestamps > base.VALIDATION_END_EXCLUSIVE
    if before.any() or after.any():
        raise BoundaryTradeAddendumError("trade evidence escaped the authorized public boundary")
    train = int(
        ((timestamps >= base.TRAIN_START) & (timestamps < base.VALIDATION_START)).sum()
    )
    validation_count = int(
        (
            (timestamps >= base.VALIDATION_START)
            & (timestamps < base.VALIDATION_END_EXCLUSIVE)
        ).sum()
    )
    boundary_count = int((timestamps == base.VALIDATION_END_EXCLUSIVE).sum())
    if train + validation_count + boundary_count != len(rows):
        raise BoundaryTradeAddendumError("trade interval partition is incomplete")
    return train, validation_count, train + validation_count


def assess(root: str | Path = ".") -> dict[str, object]:
    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        authority = verify_activation(root_path)
        parent_authority = stage_stitch.verify_activation(root_path)
        original = base._trade_counts
        base._trade_counts = _scored_trade_counts
        try:
            body = stage_stitch._build_report(root_path, parent_authority)
        finally:
            base._trade_counts = original
        body["amendment_id"] = ADDENDUM_ID
        body["activation_freeze_sha256"] = authority.freeze_file_sha256
        body["parent_activation_freeze_sha256"] = authority.parent_freeze_sha256
        body["trade_boundary_policy"] = {
            "scored_interval": "[2020-02-03T00:00:00Z,2023-07-01T00:00:00Z)",
            "terminal_rows_at_end_exclusive_excluded": True,
            "rows_after_end_exclusive_rejected": True,
        }
        record = {**body, "record_sha256": _sha256(_canonical(body))}
        payload = _pretty(record)
        path = root_path / base.PUBLIC_REPORT_PATH
        if path.exists() or path.is_symlink():
            if orchestrator_v3._read_regular_bytes(root_path, base.PUBLIC_REPORT_PATH) != payload:
                raise BoundaryTradeAddendumError("existing public assessment differs")
        else:
            orchestrator_v3._write_new_file(
                root_path, base.PUBLIC_REPORT_PATH, payload, mode=0o444
            )
        return {"command": "assess", "report_path": base.PUBLIC_REPORT_PATH, **record, "ok": True}


def report(root: str | Path = ".") -> dict[str, object]:
    root_path = orchestrator_v3._trusted_root(root)
    authority = verify_activation(root_path)
    payload = orchestrator_v3._read_regular_bytes(root_path, base.PUBLIC_REPORT_PATH)
    record = _strict_json(payload, "public development assessment")
    if (
        _pretty(record) != payload
        or record.get("activation_freeze_sha256") != authority.freeze_file_sha256
    ):
        raise BoundaryTradeAddendumError("public assessment authority changed")
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    if record.get("record_sha256") != _sha256(_canonical(body)):
        raise BoundaryTradeAddendumError("public assessment hash is invalid")
    return {"command": "report", **record, "ok": True}


def validate(root: str | Path = ".") -> dict[str, object]:
    authority = verify_activation(root)
    return {
        "addendum_id": ADDENDUM_ID,
        "command": "validate",
        "activation": dataclasses.asdict(authority),
        "ok": True,
    }


__all__ = [
    "ADDENDUM_ID",
    "BoundaryTradeAddendumError",
    "BoundaryTradeAuthority",
    "ProvisionalBoundaryTradeFreeze",
    "assess",
    "freeze_activation",
    "report",
    "validate",
    "verify_activation",
]
