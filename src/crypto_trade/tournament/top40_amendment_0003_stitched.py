"""Prospective stitched public assessment for Top40 V3 Amendment 0003.

Amendment 0002 deliberately stopped after the simultaneous release of fixed validation
packets.  This layer binds that release, verifies the organizer-owned artifacts without
disclosing their rows, deterministically concatenates train and validation, and applies the
already-frozen V3 public qualification factory.
"""

from __future__ import annotations

import base64
import csv
import dataclasses
import hashlib
import io
import json
import math
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament import (
    coaching_v3,
    metrics_v3,
    orchestrator_v3,
    runner_v3,
)
from crypto_trade.tournament import (
    top40_amendment_0002_durability as durability,
)
from crypto_trade.tournament import (
    top40_amendment_0002_validation as validation,
)
from crypto_trade.tournament.qualification_v3 import (
    PublicAssessment,
    assess_public,
    rank_public_assessments,
)

SCHEMA_VERSION = 1
AMENDMENT_ID = "top40-v3-amendment-0003-stitched-public-assessment"
AMENDMENT_ROOT = "tournament/top40-v3/amendments/0003"
AMENDMENT_POLICY_PATH = f"{AMENDMENT_ROOT}/AMENDMENT.md"
INTEGRATION_FREEZE_PATH = f"{AMENDMENT_ROOT}/integration-freeze.json"
PUBLIC_REPORT_PATH = "tournament/top40-v3/public-development-assessment.json"
MODULE_PATH = "src/crypto_trade/tournament/top40_amendment_0003_stitched.py"
SCRIPT_PATH = "scripts/top40_v3_amendment_0003.py"
TEST_PATH = "tests/tournament/test_top40_amendment_0003_stitched.py"
IMPLEMENTATION_PATHS = (MODULE_PATH, SCRIPT_PATH, TEST_PATH, AMENDMENT_POLICY_PATH)
AMENDMENT_TEST_COMMAND = (
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

TRAIN_START = pd.Timestamp("2020-02-03T00:00:00Z")
VALIDATION_START = pd.Timestamp("2022-07-01T00:00:00Z")
VALIDATION_END_EXCLUSIVE = pd.Timestamp("2023-07-01T00:00:00Z")
PUBLIC_END = VALIDATION_END_EXCLUSIVE - pd.Timedelta(days=1)
REGIMES = ("bull", "bear", "chop", "stress")

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_FREEZE_KEYS = frozenset(
    {
        "schema_version",
        "amendment_id",
        "parent_validation",
        "parent_durability",
        "validation_release",
        "implementation",
        "amendment_tests",
        "record_sha256",
    }
)


class Amendment0003StitchedError(orchestrator_v3.OrchestratorError):
    """The stitched assessment authority or evidence is absent, changed, or invalid."""


@dataclasses.dataclass(frozen=True, slots=True)
class ActivationAuthority:
    freeze_file_sha256: str
    freeze_commit: str
    record_sha256: str
    implementation_commit: str
    validation_journal_head_sha256: str
    validation_release_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class ProvisionalActivationFreeze:
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
        raise Amendment0003StitchedError("payload is not finite canonical JSON") from exc


def _pretty(payload: object) -> bytes:
    try:
        return (
            json.dumps(payload, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True)
            .encode("ascii")
            + b"\n"
        )
    except (TypeError, ValueError) as exc:
        raise Amendment0003StitchedError("payload is not finite pretty JSON") from exc


def _strict_json(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise Amendment0003StitchedError(f"{label} contains a duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(payload.decode("ascii"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Amendment0003StitchedError(f"{label} is not valid ASCII JSON") from exc
    if not isinstance(value, Mapping):
        raise Amendment0003StitchedError(f"{label} must be an object")
    return value


def _safe_relative(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise Amendment0003StitchedError(f"{label} must be a POSIX relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise Amendment0003StitchedError(f"{label} is unsafe")
    return value


def _digest(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise Amendment0003StitchedError(f"{label} must be a lowercase SHA-256")
    return value


def _git(root: Path, arguments: Sequence[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )


def _verified_commit(root: Path, value: object, label: str) -> str:
    if not isinstance(value, str) or _COMMIT.fullmatch(value) is None:
        raise Amendment0003StitchedError(f"{label} is not a full Git commit")
    result = _git(root, ["cat-file", "-e", f"{value}^{{commit}}"])
    if result.returncode != 0:
        raise Amendment0003StitchedError(f"{label} does not exist")
    return value


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
    commit = _verified_commit(root, implementation_commit, "implementation commit")
    for entry in entries:
        relative = str(entry["path"])
        result = _git(root, ["show", f"{commit}:{relative}"])
        if result.returncode != 0 or _sha256(result.stdout) != entry["sha256"]:
            raise Amendment0003StitchedError(
                f"implementation commit does not bind {relative}"
            )


def _run_tests(root: Path) -> bytes:
    completed = subprocess.run(
        list(AMENDMENT_TEST_COMMAND),
        cwd=root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    output = completed.stdout
    if completed.returncode != 0:
        raise Amendment0003StitchedError(
            f"Amendment 0003 tests failed with exit code {completed.returncode}"
        )
    if not output or len(output) > MAX_TEST_OUTPUT_BYTES:
        raise Amendment0003StitchedError("Amendment 0003 test output is missing or too large")
    orchestrator_v3._parse_passed_count(output)
    return output


def _test_evidence(output: bytes) -> dict[str, object]:
    count = orchestrator_v3._parse_passed_count(output)
    return {
        "command": list(AMENDMENT_TEST_COMMAND),
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
        raise Amendment0003StitchedError("test evidence is malformed")
    try:
        output = base64.b64decode(str(value["output_base64"]).encode("ascii"), validate=True)
    except Exception as exc:
        raise Amendment0003StitchedError("test evidence encoding is invalid") from exc
    count = orchestrator_v3._parse_passed_count(output)
    if (
        value["command"] != list(AMENDMENT_TEST_COMMAND)
        or value["collected"] != count
        or value["passed"] != count
        or value["output_size"] != len(output)
        or value["output_sha256"] != _sha256(output)
    ):
        raise Amendment0003StitchedError("test evidence binding changed")


def _released_authority(root: Path) -> tuple[dict[str, object], validation.ValidationJournalState]:
    parent = validation.verify_activation(root)
    durable = durability.verify_durability(root)
    cohort = validation.load_cohort(root)
    journal_bytes = orchestrator_v3._read_regular_bytes(root, validation.VALIDATION_JOURNAL_PATH)
    state = validation.replay_validation_journal_bytes(journal_bytes)
    validation._verify_journal_cohort(state, cohort)
    if (
        state.release_record is None
        or state.pending_request_sha256s
        or len(state.accepted_records) != 4
        or len(state.terminal_records) != 4
        or any(record["event_type"] != "succeeded" for record in state.terminal_records)
    ):
        raise Amendment0003StitchedError("stitched activation requires a complete released cohort")
    release = state.release_record
    return (
        {
            "journal_path": validation.VALIDATION_JOURNAL_PATH,
            "journal_file_sha256": _sha256(journal_bytes),
            "journal_head_sha256": state.head_sha256,
            "release_record_sha256": release["record_sha256"],
            "packet_sha256_by_team": dict(release["packet_sha256_by_team"]),
            "cohort_freeze_sha256": cohort.file_sha256,
            "parent_activation_freeze_sha256": parent.freeze_file_sha256,
            "parent_durability_freeze_sha256": durable.freeze_file_sha256,
        },
        state,
    )


def freeze_activation(
    root: str | Path, *, implementation_commit: str
) -> ProvisionalActivationFreeze:
    """Freeze code and the already-released validation boundary before reading private rows."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        freeze_path = root_path / INTEGRATION_FREEZE_PATH
        report_path = root_path / PUBLIC_REPORT_PATH
        if freeze_path.exists() or freeze_path.is_symlink():
            raise Amendment0003StitchedError("Amendment 0003 integration freeze already exists")
        if report_path.exists() or report_path.is_symlink():
            raise Amendment0003StitchedError("public assessment must be absent before activation")
        parent = validation.verify_activation(root_path)
        durable = durability.verify_durability(root_path)
        release_before, _ = _released_authority(root_path)
        entries_before = _implementation_entries(root_path)
        _verify_implementation_commit(root_path, implementation_commit, entries_before)
        output = _run_tests(root_path)
        release_after, _ = _released_authority(root_path)
        if (
            release_after != release_before
            or validation.verify_activation(root_path) != parent
            or durability.verify_durability(root_path) != durable
            or _implementation_entries(root_path) != entries_before
            or report_path.exists()
            or report_path.is_symlink()
        ):
            raise Amendment0003StitchedError("activation inputs changed during serial evidence")
        body = {
            "schema_version": SCHEMA_VERSION,
            "amendment_id": AMENDMENT_ID,
            "parent_validation": dataclasses.asdict(parent),
            "parent_durability": dataclasses.asdict(durable),
            "validation_release": release_before,
            "implementation": {
                "commit": implementation_commit,
                "files": [dict(entry) for entry in entries_before],
                "manifest_sha256": _manifest_sha256(entries_before),
            },
            "amendment_tests": _test_evidence(output),
        }
        record = {**body, "record_sha256": _sha256(_canonical(body))}
        orchestrator_v3._write_new_file(
            root_path, INTEGRATION_FREEZE_PATH, _pretty(record), mode=0o444
        )
        freeze_bytes = orchestrator_v3._read_regular_bytes(root_path, INTEGRATION_FREEZE_PATH)
        return ProvisionalActivationFreeze(
            freeze_file_sha256=_sha256(freeze_bytes),
            record_sha256=str(record["record_sha256"]),
            implementation_commit=implementation_commit,
        )


def _verify_freeze_commit(root: Path, implementation_commit: str, freeze_bytes: bytes) -> str:
    additions = _git(root, ["log", "--diff-filter=A", "--format=%H", "--", INTEGRATION_FREEZE_PATH])
    commits = [line for line in additions.stdout.decode("ascii", "replace").splitlines() if line]
    if additions.returncode != 0 or len(commits) != 1:
        raise Amendment0003StitchedError("activation requires one unique freeze commit")
    freeze_commit = _verified_commit(root, commits[0], "freeze commit")
    parent = _git(root, ["rev-parse", f"{freeze_commit}^"])
    if parent.returncode != 0 or parent.stdout.decode("ascii").strip() != implementation_commit:
        raise Amendment0003StitchedError("freeze commit must directly follow implementation commit")
    delta = _git(root, ["diff-tree", "--no-commit-id", "--name-status", "-r", freeze_commit])
    if delta.returncode != 0 or delta.stdout.decode("utf-8").splitlines() != [
        f"A\t{INTEGRATION_FREEZE_PATH}"
    ]:
        raise Amendment0003StitchedError("freeze commit has an unexpected repository delta")
    committed = _git(root, ["show", f"{freeze_commit}:{INTEGRATION_FREEZE_PATH}"])
    if committed.returncode != 0 or committed.stdout != freeze_bytes:
        raise Amendment0003StitchedError("live activation freeze differs from its commit")
    return freeze_commit


def verify_activation(root: str | Path = ".") -> ActivationAuthority:
    root_path = orchestrator_v3._trusted_root(root)
    freeze_bytes = orchestrator_v3._read_regular_bytes(root_path, INTEGRATION_FREEZE_PATH)
    record = _strict_json(freeze_bytes, "Amendment 0003 integration freeze")
    if _pretty(record) != freeze_bytes or set(record) != set(_FREEZE_KEYS):
        raise Amendment0003StitchedError("activation freeze is not canonical or has invalid keys")
    body = {key: record[key] for key in _FREEZE_KEYS - {"record_sha256"}}
    if (
        record["schema_version"] != SCHEMA_VERSION
        or record["amendment_id"] != AMENDMENT_ID
        or record["record_sha256"] != _sha256(_canonical(body))
    ):
        raise Amendment0003StitchedError("activation freeze identity or hash is invalid")
    parent = validation.verify_activation(root_path)
    durable = durability.verify_durability(root_path)
    release, _ = _released_authority(root_path)
    if record["parent_validation"] != dataclasses.asdict(parent):
        raise Amendment0003StitchedError("parent validation authority changed")
    if record["parent_durability"] != dataclasses.asdict(durable):
        raise Amendment0003StitchedError("parent durability authority changed")
    if record["validation_release"] != release:
        raise Amendment0003StitchedError("released validation boundary changed")
    implementation = record["implementation"]
    if not isinstance(implementation, Mapping):
        raise Amendment0003StitchedError("implementation authority is malformed")
    entries = _implementation_entries(root_path)
    if (
        implementation.get("files") != list(entries)
        or implementation.get("manifest_sha256") != _manifest_sha256(entries)
    ):
        raise Amendment0003StitchedError("implementation bytes changed")
    implementation_commit = str(implementation.get("commit"))
    _verify_implementation_commit(root_path, implementation_commit, entries)
    _verify_test_evidence(record["amendment_tests"])
    freeze_commit = _verify_freeze_commit(root_path, implementation_commit, freeze_bytes)
    return ActivationAuthority(
        freeze_file_sha256=_sha256(freeze_bytes),
        freeze_commit=freeze_commit,
        record_sha256=str(record["record_sha256"]),
        implementation_commit=implementation_commit,
        validation_journal_head_sha256=str(release["journal_head_sha256"]),
        validation_release_sha256=str(release["release_record_sha256"]),
    )


def _read_hashed(root: Path, relative: str, expected: object, label: str) -> bytes:
    safe = _safe_relative(relative, label)
    payload = orchestrator_v3._read_regular_bytes(root, safe)
    if _sha256(payload) != _digest(expected, f"{label} sha256"):
        raise Amendment0003StitchedError(f"{label} hash changed")
    return payload


def _daily_series(payload: bytes, label: str) -> pd.Series:
    try:
        frame = pd.read_csv(io.BytesIO(payload))
    except Exception as exc:
        raise Amendment0003StitchedError(f"cannot parse {label}") from exc
    if list(frame.columns) != ["date", "net_return"] or frame.empty:
        raise Amendment0003StitchedError(f"{label} has an invalid schema")
    try:
        index = pd.DatetimeIndex(pd.to_datetime(frame["date"], utc=True, errors="raise"))
        values = pd.to_numeric(frame["net_return"], errors="raise").to_numpy(dtype=float)
    except Exception as exc:
        raise Amendment0003StitchedError(f"{label} contains invalid values") from exc
    if (
        index.has_duplicates
        or not index.is_monotonic_increasing
        or not np.isfinite(values).all()
        or (values <= -1.0).any()
    ):
        raise Amendment0003StitchedError(f"{label} is not a valid ordered return series")
    return pd.Series(values, index=index, name="net_return")


def _trade_counts(payload: bytes) -> tuple[int, int, int]:
    try:
        rows = list(csv.DictReader(io.StringIO(payload.decode("utf-8"))))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise Amendment0003StitchedError("cannot parse public trade evidence") from exc
    if rows and "timestamp" not in rows[0]:
        raise Amendment0003StitchedError("trade evidence lacks timestamp")
    timestamps = pd.DatetimeIndex(
        pd.to_datetime([row["timestamp"] for row in rows], utc=True, errors="raise")
    )
    train = int((timestamps < VALIDATION_START).sum())
    validation_count = int(
        ((timestamps >= VALIDATION_START) & (timestamps < VALIDATION_END_EXCLUSIVE)).sum()
    )
    if train + validation_count != len(rows):
        raise Amendment0003StitchedError("trade evidence escaped the public window")
    return train, validation_count, len(rows)


def _close(observed: object, expected: object, label: str) -> None:
    try:
        left = float(observed)
        right = float(expected)
    except (TypeError, ValueError, OverflowError) as exc:
        raise Amendment0003StitchedError(f"{label} is not numeric") from exc
    if not math.isfinite(left) or not math.isfinite(right) or not math.isclose(
        left, right, rel_tol=1e-10, abs_tol=1e-12
    ):
        raise Amendment0003StitchedError(f"{label} does not reproduce its released value")


def _metrics_mapping(
    returns: pd.Series,
    double_cost_returns: pd.Series,
    labels: pd.Series,
    trade_count: int,
) -> dict[str, object]:
    metrics = metrics_v3.compute_window_metrics(returns)
    double_cost = metrics_v3.compute_window_metrics(double_cost_returns)
    regimes = metrics_v3.compute_regime_sharpes(returns, labels)
    return {
        "net_sharpe": float(metrics.net_sharpe),
        "net_sortino": float(metrics.net_sortino),
        "calmar": float(metrics.calmar),
        "annualized_return": float(metrics.annualized_return),
        "max_drawdown": float(metrics.max_drawdown),
        "positive_quarter_fraction": float(metrics.positive_quarter_fraction),
        "double_cost_sharpe": float(double_cost.net_sharpe),
        "regime_sharpe": {name: float(regimes[name]) for name in REGIMES},
        "trade_count": int(trade_count),
        "cumulative_net_return": float((1.0 + returns).prod() - 1.0),
        "cumulative_double_cost_return": float((1.0 + double_cost_returns).prod() - 1.0),
    }


def _verify_stage_metrics(
    observed: Mapping[str, object],
    packet_metrics: Mapping[str, object],
    packet_double_cost: object,
    packet_regimes: Mapping[str, object],
    label: str,
) -> None:
    for name in (
        "net_sharpe",
        "net_sortino",
        "calmar",
        "annualized_return",
        "max_drawdown",
        "positive_quarter_fraction",
    ):
        _close(observed[name], packet_metrics[name], f"{label}.{name}")
    _close(observed["double_cost_sharpe"], packet_double_cost, f"{label}.double_cost_sharpe")
    for regime in REGIMES:
        _close(
            observed["regime_sharpe"][regime],
            packet_regimes[regime],
            f"{label}.regime_sharpe.{regime}",
        )


def _assessment_mapping(assessment: PublicAssessment) -> dict[str, object]:
    return {
        "eligible": assessment.eligible,
        "robustness_score": assessment.robustness_score,
        "positive_regime_count": assessment.positive_regime_count,
        "worst_regime_sharpe": assessment.worst_regime_sharpe,
        "failed_core_floor_names": list(assessment.failed_core_floor_names),
        "core_checks": [dataclasses.asdict(check) for check in assessment.core_checks],
    }


def _candidate_result(
    root: Path,
    candidate: validation.CohortCandidate,
    accepted: Mapping[str, Any],
    terminal: Mapping[str, Any],
    validation_packet: Mapping[str, Any],
    labels: pd.Series,
) -> tuple[dict[str, object], PublicAssessment]:
    team_id = candidate.identity.team_id
    if terminal["event_type"] != "succeeded":
        raise Amendment0003StitchedError("stitched assessment requires successful validation")
    artifact_hashes = terminal["artifact_hashes"]
    if not isinstance(artifact_hashes, Mapping):
        raise Amendment0003StitchedError("validation artifact manifest is malformed")
    for relative, digest in artifact_hashes.items():
        _read_hashed(root, str(relative), digest, f"{team_id} validation artifact")
    output = _safe_relative(accepted["output_path"], "validation output")
    base_relative = f"{output}/daily_returns.csv"
    double_relative = f"{output}/double_cost_daily_returns.csv"
    trades_relative = f"{output}/trades.csv"
    base = _daily_series(
        _read_hashed(root, base_relative, artifact_hashes[base_relative], "public returns"),
        f"{team_id} public returns",
    )
    double_cost = _daily_series(
        _read_hashed(
            root,
            double_relative,
            artifact_hashes[double_relative],
            "public double-cost returns",
        ),
        f"{team_id} public double-cost returns",
    )
    expected_index = pd.date_range(TRAIN_START, PUBLIC_END, freq="1D")
    if not base.index.equals(expected_index) or not double_cost.index.equals(expected_index):
        raise Amendment0003StitchedError("public returns do not cover the exact stitched grid")

    train_packet_bytes = _read_hashed(
        root,
        candidate.train_metric_packet_path,
        candidate.train_metric_packet_sha256,
        "train metric packet",
    )
    train_packet = _strict_json(train_packet_bytes, "train metric packet")
    if coaching_v3.canonical_packet_bytes(train_packet) != train_packet_bytes:
        raise Amendment0003StitchedError("train metric packet is not canonical")
    artifact_block = train_packet.get("artifacts")
    if not isinstance(artifact_block, Mapping):
        raise Amendment0003StitchedError("train artifact block is malformed")
    paths = artifact_block.get("paths")
    hashes = artifact_block.get("sha256")
    if not isinstance(paths, Mapping) or not isinstance(hashes, Mapping):
        raise Amendment0003StitchedError("train artifact authority is malformed")
    train_base = _daily_series(
        _read_hashed(root, str(paths["daily_returns"]), hashes["daily_returns"], "train returns"),
        f"{team_id} train returns",
    )
    train_double = _daily_series(
        _read_hashed(
            root,
            str(paths["double_cost_daily_returns"]),
            hashes["double_cost_daily_returns"],
            "train double-cost returns",
        ),
        f"{team_id} train double-cost returns",
    )
    train_slice = base.loc[TRAIN_START : VALIDATION_START - pd.Timedelta(days=1)]
    train_double_slice = double_cost.loc[TRAIN_START : VALIDATION_START - pd.Timedelta(days=1)]
    if not train_base.equals(train_slice) or not train_double.equals(train_double_slice):
        raise Amendment0003StitchedError(
            "validation replay does not reproduce immutable IS returns"
        )

    trades_payload = _read_hashed(
        root, trades_relative, artifact_hashes[trades_relative], "public trades"
    )
    train_trades, validation_trades, total_trades = _trade_counts(trades_payload)
    expected_train_trades = int(train_packet["counts"]["trade_count"])
    expected_validation_trades = int(validation_packet["validation_aggregates"]["trade_count"])
    if train_trades != expected_train_trades or validation_trades != expected_validation_trades:
        raise Amendment0003StitchedError("public trade counts do not reproduce IS/OOS packets")

    train_labels = labels.loc[train_slice.index]
    validation_slice = base.loc[VALIDATION_START:PUBLIC_END]
    validation_double_slice = double_cost.loc[VALIDATION_START:PUBLIC_END]
    validation_labels = labels.loc[validation_slice.index]
    train_metrics = _metrics_mapping(
        train_slice, train_double_slice, train_labels, train_trades
    )
    validation_metrics = _metrics_mapping(
        validation_slice,
        validation_double_slice,
        validation_labels,
        validation_trades,
    )
    _verify_stage_metrics(
        train_metrics,
        train_packet["scored_window"]["metrics"],
        train_packet["double_cost_sharpe"],
        train_packet["regime_sharpe"],
        f"{team_id}.train",
    )
    _verify_stage_metrics(
        validation_metrics,
        validation_packet["scored_window"]["metrics"],
        validation_packet["double_cost_sharpe"],
        validation_packet["regime_sharpe"],
        f"{team_id}.validation",
    )
    _close(
        validation_metrics["cumulative_net_return"],
        validation_packet["validation_aggregates"]["cumulative_net_return"],
        f"{team_id}.validation.cumulative_net_return",
    )
    _close(
        validation_metrics["cumulative_double_cost_return"],
        validation_packet["validation_aggregates"]["cumulative_double_cost_return"],
        f"{team_id}.validation.cumulative_double_cost_return",
    )

    stitched = _metrics_mapping(base, double_cost, labels, total_trades)
    qualification_metrics = {
        key: stitched[key]
        for key in (
            "net_sharpe",
            "annualized_return",
            "max_drawdown",
            "double_cost_sharpe",
            "positive_quarter_fraction",
            "trade_count",
            "regime_sharpe",
        )
    }
    hard_gates = validation_packet["structural_hard_gates"]
    assessment = assess_public(
        candidate.identity,
        qualification_metrics,
        reproducible=True,
        data_authority=bool(hard_gates["data_authority"]),
        universe_compliant=bool(hard_gates["universe_compliant"]),
        causal=bool(hard_gates["causal"]),
        execution_compliant=bool(hard_gates["execution_compliant"]),
        solvent=bool(hard_gates["solvent"]),
        window_complete=bool(hard_gates["window_complete"]),
    )
    train_ready = all(
        float(value) > 0.0
        for value in (
            train_metrics["net_sharpe"],
            train_metrics["annualized_return"],
            train_metrics["double_cost_sharpe"],
        )
    )
    validation_ready = bool(validation_packet["readiness"]["validation_positive"])
    readiness_eligible = train_ready and validation_ready and assessment.structural_checks.passed
    nomination_ready = readiness_eligible and assessment.eligible
    result = {
        "rank": candidate.rank,
        "team_id": team_id,
        "candidate_id": candidate.identity.candidate_id,
        "candidate_identity_sha256": candidate.identity.sha256,
        "train": train_metrics,
        "validation": validation_metrics,
        "stitched_public": stitched,
        "public_assessment": _assessment_mapping(assessment),
        "readiness_eligible": readiness_eligible,
        "nomination_ready": nomination_ready,
    }
    return result, assessment


def _build_public_report(root: Path, activation: ActivationAuthority) -> dict[str, object]:
    cohort = validation.load_cohort(root)
    _, state = _released_authority(root)
    accepted_by_team = {str(item["team_id"]): item for item in state.accepted_records}
    terminal_by_team = {str(item["team_id"]): item for item in state.terminal_records}

    config = runner_v3._load_config(root / orchestrator_v3.CONFIG_PATH, "team-01")
    authorized = runner_v3._authorized_window(config, "public")
    snapshot = runner_v3._load_verified_snapshot(
        root, root / orchestrator_v3.DATA_MANIFEST_PATH
    )
    decision_times = runner_v3._decision_grid(authorized)
    runner_v3._validate_snapshot_bounds(snapshot, config, decision_times)
    btc_daily = runner_v3._btc_daily_returns(snapshot.bars, config, authorized)
    labels = metrics_v3.classify_btc_regimes(btc_daily).loc[TRAIN_START:PUBLIC_END]
    expected_index = pd.date_range(TRAIN_START, PUBLIC_END, freq="1D")
    if not labels.index.equals(expected_index) or labels.notna().sum() == 0:
        raise Amendment0003StitchedError("BTC regime labels do not cover the public grid")

    results: list[dict[str, object]] = []
    assessments: dict[str, PublicAssessment] = {}
    nomination_ready: dict[str, bool] = {}
    for candidate in cohort.candidates:
        team_id = candidate.identity.team_id
        packet = validation._read_released_packet(root, terminal_by_team[team_id])
        if not isinstance(packet, Mapping):
            raise Amendment0003StitchedError("released validation packet is missing")
        item, assessment = _candidate_result(
            root,
            candidate,
            accepted_by_team[team_id],
            terminal_by_team[team_id],
            packet,
            labels,
        )
        results.append(item)
        assessments[team_id] = assessment
        nomination_ready[team_id] = bool(item["nomination_ready"])
    runner_v3._verify_snapshot_files_unchanged(snapshot)

    ready_assessments = {
        team_id: assessment
        for team_id, assessment in assessments.items()
        if nomination_ready[team_id]
    }
    ranking = list(rank_public_assessments(ready_assessments))
    return {
        "schema_version": "top40-v3-public-development-assessment-v1",
        "amendment_id": AMENDMENT_ID,
        "activation_freeze_sha256": activation.freeze_file_sha256,
        "cohort_freeze_sha256": cohort.file_sha256,
        "validation_journal_head_sha256": activation.validation_journal_head_sha256,
        "validation_release_sha256": activation.validation_release_sha256,
        "public_window": {
            "start_utc": TRAIN_START.isoformat().replace("+00:00", "Z"),
            "end_exclusive_utc": VALIDATION_END_EXCLUSIVE.isoformat().replace("+00:00", "Z"),
        },
        "results": results,
        "nomination_ready_ranking": ranking,
        "nomination_ready_count": len(ranking),
        "comeback_triggered": len(ranking) < 3,
        "comeback_reason": "fewer-than-three-nomination-ready-teams" if len(ranking) < 3 else None,
    }


def assess(root: str | Path = ".") -> dict[str, object]:
    """Create or verify the immutable aggregate stitched public assessment."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        activation = verify_activation(root_path)
        body = _build_public_report(root_path, activation)
        record = {**body, "record_sha256": _sha256(_canonical(body))}
        payload = _pretty(record)
        path = root_path / PUBLIC_REPORT_PATH
        if path.exists() or path.is_symlink():
            existing = orchestrator_v3._read_regular_bytes(root_path, PUBLIC_REPORT_PATH)
            if existing != payload:
                raise Amendment0003StitchedError("existing public assessment differs")
        else:
            orchestrator_v3._write_new_file(root_path, PUBLIC_REPORT_PATH, payload, mode=0o444)
        return {"command": "assess", "report_path": PUBLIC_REPORT_PATH, **record, "ok": True}


def report(root: str | Path = ".") -> dict[str, object]:
    root_path = orchestrator_v3._trusted_root(root)
    activation = verify_activation(root_path)
    payload = orchestrator_v3._read_regular_bytes(root_path, PUBLIC_REPORT_PATH)
    record = _strict_json(payload, "public development assessment")
    if (
        _pretty(record) != payload
        or record.get("activation_freeze_sha256") != activation.freeze_file_sha256
    ):
        raise Amendment0003StitchedError("public development assessment authority changed")
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    if record.get("record_sha256") != _sha256(_canonical(body)):
        raise Amendment0003StitchedError("public development assessment hash is invalid")
    return {"command": "report", **record, "ok": True}


def validate(root: str | Path = ".") -> dict[str, object]:
    activation = verify_activation(root)
    return {
        "amendment_id": AMENDMENT_ID,
        "command": "validate",
        "activation": dataclasses.asdict(activation),
        "ok": True,
    }


__all__ = [
    "AMENDMENT_ID",
    "AMENDMENT_TEST_COMMAND",
    "ActivationAuthority",
    "Amendment0003StitchedError",
    "ProvisionalActivationFreeze",
    "assess",
    "freeze_activation",
    "report",
    "validate",
    "verify_activation",
]
