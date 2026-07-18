"""Scored-stage concatenation addendum for Top40 V3 Amendment 0003.

The frozen parent correctly failed closed when it treated the validation replay's unscored
training prefix as if it were the immutable scored training stage.  A standalone train run has a
boundary settlement while a validation replay continues through that date, so those prefixes are
not required to be equal.  The charter's public record concatenates the two authoritative scored
stages: the immutable train artifact and the released validation slice.
"""

from __future__ import annotations

import base64
import dataclasses
import hashlib
import json
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.tournament import coaching_v3, metrics_v3, orchestrator_v3, runner_v3
from crypto_trade.tournament import top40_amendment_0002_validation as validation
from crypto_trade.tournament import top40_amendment_0003_stitched as parent
from crypto_trade.tournament.qualification_v3 import (
    PublicAssessment,
    assess_public,
    rank_public_assessments,
)

SCHEMA_VERSION = 1
ADDENDUM_ID = "top40-v3-amendment-0003-scored-stage-concatenation"
PARENT_FREEZE_SHA256 = "bbeb52060628a09505af374c4fc68d1d604c68d46e0e1f268e183642d89ded2c"
PARENT_FREEZE_COMMIT = "81356743ee0c814e677356b1a67616bd89f7bee1"
POLICY_PATH = "tournament/top40-v3/amendments/0003/STAGE-STITCH-ADDENDUM.md"
FREEZE_PATH = "tournament/top40-v3/amendments/0003/stage-stitch-freeze.json"
MODULE_PATH = "src/crypto_trade/tournament/top40_amendment_0003_stage_stitch.py"
SCRIPT_PATH = "scripts/top40_v3_amendment_0003_stage_stitch.py"
TEST_PATH = "tests/tournament/test_top40_amendment_0003_stage_stitch.py"
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


class StageStitchAddendumError(orchestrator_v3.OrchestratorError):
    """The scored-stage concatenation authority is absent, changed, or invalid."""


@dataclasses.dataclass(frozen=True, slots=True)
class StageStitchAuthority:
    freeze_file_sha256: str
    freeze_commit: str
    record_sha256: str
    implementation_commit: str
    parent_freeze_sha256: str
    validation_journal_head_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class ProvisionalStageStitchFreeze:
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
        raise StageStitchAddendumError("payload is not finite canonical JSON") from exc


def _pretty(payload: object) -> bytes:
    try:
        return (
            json.dumps(payload, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True)
            .encode("ascii")
            + b"\n"
        )
    except (TypeError, ValueError) as exc:
        raise StageStitchAddendumError("payload is not finite pretty JSON") from exc


def _strict_json(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise StageStitchAddendumError(f"{label} contains a duplicate key")
            result[key] = value
        return result

    try:
        value = json.loads(payload.decode("ascii"), object_pairs_hook=unique)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise StageStitchAddendumError(f"{label} is not valid ASCII JSON") from exc
    if not isinstance(value, Mapping):
        raise StageStitchAddendumError(f"{label} must be an object")
    return value


def _parent_authority(root: Path) -> parent.ActivationAuthority:
    authority = parent.verify_activation(root)
    if (
        authority.freeze_file_sha256 != PARENT_FREEZE_SHA256
        or authority.freeze_commit != PARENT_FREEZE_COMMIT
    ):
        raise StageStitchAddendumError("frozen Amendment 0003 parent authority changed")
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
    commit = parent._verified_commit(root, implementation_commit, "implementation commit")
    for entry in entries:
        result = parent._git(root, ["show", f"{commit}:{entry['path']}"])
        if result.returncode != 0 or _sha256(result.stdout) != entry["sha256"]:
            raise StageStitchAddendumError(
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
        raise StageStitchAddendumError(
            f"stage-stitch tests failed with exit code {completed.returncode}"
        )
    if not output or len(output) > MAX_TEST_OUTPUT_BYTES:
        raise StageStitchAddendumError("stage-stitch test output is missing or too large")
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
        raise StageStitchAddendumError("stage-stitch test evidence is malformed")
    try:
        output = base64.b64decode(str(value["output_base64"]).encode("ascii"), validate=True)
    except Exception as exc:
        raise StageStitchAddendumError("stage-stitch test encoding is invalid") from exc
    count = orchestrator_v3._parse_passed_count(output)
    if (
        value["command"] != list(TEST_COMMAND)
        or value["collected"] != count
        or value["passed"] != count
        or value["output_size"] != len(output)
        or value["output_sha256"] != _sha256(output)
    ):
        raise StageStitchAddendumError("stage-stitch test evidence changed")


def freeze_activation(
    root: str | Path, *, implementation_commit: str
) -> ProvisionalStageStitchFreeze:
    """Freeze the corrected scored-stage rule before computing any stitched metric."""

    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        freeze_path = root_path / FREEZE_PATH
        report_path = root_path / parent.PUBLIC_REPORT_PATH
        if freeze_path.exists() or freeze_path.is_symlink():
            raise StageStitchAddendumError("stage-stitch freeze already exists")
        if report_path.exists() or report_path.is_symlink():
            raise StageStitchAddendumError("public assessment must be absent before addendum")
        parent_before = _parent_authority(root_path)
        release_before, _ = parent._released_authority(root_path)
        entries_before = _implementation_entries(root_path)
        _verify_implementation_commit(root_path, implementation_commit, entries_before)
        output = _run_tests(root_path)
        release_after, _ = parent._released_authority(root_path)
        if (
            _parent_authority(root_path) != parent_before
            or release_after != release_before
            or _implementation_entries(root_path) != entries_before
            or report_path.exists()
            or report_path.is_symlink()
        ):
            raise StageStitchAddendumError("addendum activation inputs changed")
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
        return ProvisionalStageStitchFreeze(
            freeze_file_sha256=_sha256(payload),
            record_sha256=str(record["record_sha256"]),
            implementation_commit=implementation_commit,
        )


def _verify_freeze_commit(root: Path, implementation_commit: str, freeze_bytes: bytes) -> str:
    additions = parent._git(root, ["log", "--diff-filter=A", "--format=%H", "--", FREEZE_PATH])
    commits = [line for line in additions.stdout.decode("ascii", "replace").splitlines() if line]
    if additions.returncode != 0 or len(commits) != 1:
        raise StageStitchAddendumError("addendum requires one unique freeze commit")
    freeze_commit = parent._verified_commit(root, commits[0], "addendum freeze commit")
    direct_parent = parent._git(root, ["rev-parse", f"{freeze_commit}^"])
    if (
        direct_parent.returncode != 0
        or direct_parent.stdout.decode("ascii").strip() != implementation_commit
    ):
        raise StageStitchAddendumError("addendum freeze must follow implementation directly")
    delta = parent._git(
        root, ["diff-tree", "--no-commit-id", "--name-status", "-r", freeze_commit]
    )
    if delta.returncode != 0 or delta.stdout.decode("utf-8").splitlines() != [f"A\t{FREEZE_PATH}"]:
        raise StageStitchAddendumError("addendum freeze commit has an unexpected delta")
    committed = parent._git(root, ["show", f"{freeze_commit}:{FREEZE_PATH}"])
    if committed.returncode != 0 or committed.stdout != freeze_bytes:
        raise StageStitchAddendumError("live addendum freeze differs from its commit")
    return freeze_commit


def verify_activation(root: str | Path = ".") -> StageStitchAuthority:
    root_path = orchestrator_v3._trusted_root(root)
    freeze_bytes = orchestrator_v3._read_regular_bytes(root_path, FREEZE_PATH)
    record = _strict_json(freeze_bytes, "stage-stitch freeze")
    if _pretty(record) != freeze_bytes or set(record) != set(_FREEZE_KEYS):
        raise StageStitchAddendumError("stage-stitch freeze is not canonical")
    body = {key: record[key] for key in _FREEZE_KEYS - {"record_sha256"}}
    if (
        record["schema_version"] != SCHEMA_VERSION
        or record["addendum_id"] != ADDENDUM_ID
        or record["record_sha256"] != _sha256(_canonical(body))
    ):
        raise StageStitchAddendumError("stage-stitch freeze identity or hash is invalid")
    parent_authority = _parent_authority(root_path)
    release, _ = parent._released_authority(root_path)
    if record["parent_activation"] != dataclasses.asdict(parent_authority):
        raise StageStitchAddendumError("parent activation changed")
    if record["released_validation"] != release:
        raise StageStitchAddendumError("released validation boundary changed")
    implementation = record["implementation"]
    if not isinstance(implementation, Mapping):
        raise StageStitchAddendumError("addendum implementation is malformed")
    entries = _implementation_entries(root_path)
    if (
        implementation.get("files") != list(entries)
        or implementation.get("manifest_sha256") != _manifest_sha256(entries)
    ):
        raise StageStitchAddendumError("addendum implementation bytes changed")
    implementation_commit = str(implementation.get("commit"))
    _verify_implementation_commit(root_path, implementation_commit, entries)
    _verify_test_evidence(record["addendum_tests"])
    freeze_commit = _verify_freeze_commit(
        root_path, implementation_commit, freeze_bytes
    )
    return StageStitchAuthority(
        freeze_file_sha256=_sha256(freeze_bytes),
        freeze_commit=freeze_commit,
        record_sha256=str(record["record_sha256"]),
        implementation_commit=implementation_commit,
        parent_freeze_sha256=parent_authority.freeze_file_sha256,
        validation_journal_head_sha256=str(release["journal_head_sha256"]),
    )


def _stage_concat(train: pd.Series, validation_full: pd.Series) -> pd.Series:
    train_expected = pd.date_range(
        parent.TRAIN_START,
        parent.VALIDATION_START - pd.Timedelta(days=1),
        freq="1D",
    )
    public_expected = pd.date_range(parent.TRAIN_START, parent.PUBLIC_END, freq="1D")
    if not train.index.equals(train_expected) or not validation_full.index.equals(public_expected):
        raise StageStitchAddendumError("stage returns do not cover their exact authorized grids")
    validation_scored = validation_full.loc[parent.VALIDATION_START : parent.PUBLIC_END]
    stitched = pd.concat([train, validation_scored]).rename("net_return")
    if not stitched.index.equals(public_expected) or stitched.index.has_duplicates:
        raise StageStitchAddendumError("scored-stage concatenation is not the exact public grid")
    return stitched


def _candidate_result(
    root: Path,
    candidate: validation.CohortCandidate,
    accepted: Mapping[str, Any],
    terminal: Mapping[str, Any],
    validation_packet: Mapping[str, Any],
    labels: pd.Series,
) -> tuple[dict[str, object], PublicAssessment]:
    team_id = candidate.identity.team_id
    artifact_hashes = terminal["artifact_hashes"]
    if terminal["event_type"] != "succeeded" or not isinstance(artifact_hashes, Mapping):
        raise StageStitchAddendumError("candidate lacks successful validation evidence")
    for relative, digest in artifact_hashes.items():
        parent._read_hashed(root, str(relative), digest, f"{team_id} validation artifact")

    output = parent._safe_relative(accepted["output_path"], "validation output")
    base_relative = f"{output}/daily_returns.csv"
    double_relative = f"{output}/double_cost_daily_returns.csv"
    trades_relative = f"{output}/trades.csv"
    validation_full = parent._daily_series(
        parent._read_hashed(
            root, base_relative, artifact_hashes[base_relative], "validation public returns"
        ),
        f"{team_id} validation public returns",
    )
    validation_double_full = parent._daily_series(
        parent._read_hashed(
            root,
            double_relative,
            artifact_hashes[double_relative],
            "validation double-cost returns",
        ),
        f"{team_id} validation double-cost returns",
    )

    train_packet_bytes = parent._read_hashed(
        root,
        candidate.train_metric_packet_path,
        candidate.train_metric_packet_sha256,
        "train metric packet",
    )
    train_packet = parent._strict_json(train_packet_bytes, "train metric packet")
    if coaching_v3.canonical_packet_bytes(train_packet) != train_packet_bytes:
        raise StageStitchAddendumError("train metric packet is not canonical")
    artifact_block = train_packet["artifacts"]
    paths = artifact_block["paths"]
    hashes = artifact_block["sha256"]
    train = parent._daily_series(
        parent._read_hashed(
            root, str(paths["daily_returns"]), hashes["daily_returns"], "train returns"
        ),
        f"{team_id} train returns",
    )
    train_double = parent._daily_series(
        parent._read_hashed(
            root,
            str(paths["double_cost_daily_returns"]),
            hashes["double_cost_daily_returns"],
            "train double-cost returns",
        ),
        f"{team_id} train double-cost returns",
    )

    stitched_returns = _stage_concat(train, validation_full)
    stitched_double = _stage_concat(train_double, validation_double_full)
    validation_slice = validation_full.loc[parent.VALIDATION_START : parent.PUBLIC_END]
    validation_double_slice = validation_double_full.loc[
        parent.VALIDATION_START : parent.PUBLIC_END
    ]
    train_trades = int(train_packet["counts"]["trade_count"])
    trades_payload = parent._read_hashed(
        root, trades_relative, artifact_hashes[trades_relative], "validation public trades"
    )
    _, validation_trades, _ = parent._trade_counts(trades_payload)
    expected_validation_trades = int(validation_packet["validation_aggregates"]["trade_count"])
    if validation_trades != expected_validation_trades:
        raise StageStitchAddendumError("validation trade count does not reproduce its packet")

    train_metrics = parent._metrics_mapping(
        train, train_double, labels.loc[train.index], train_trades
    )
    validation_metrics = parent._metrics_mapping(
        validation_slice,
        validation_double_slice,
        labels.loc[validation_slice.index],
        validation_trades,
    )
    parent._verify_stage_metrics(
        train_metrics,
        train_packet["scored_window"]["metrics"],
        train_packet["double_cost_sharpe"],
        train_packet["regime_sharpe"],
        f"{team_id}.train",
    )
    parent._verify_stage_metrics(
        validation_metrics,
        validation_packet["scored_window"]["metrics"],
        validation_packet["double_cost_sharpe"],
        validation_packet["regime_sharpe"],
        f"{team_id}.validation",
    )
    parent._close(
        validation_metrics["cumulative_net_return"],
        validation_packet["validation_aggregates"]["cumulative_net_return"],
        f"{team_id}.validation.cumulative_net_return",
    )
    parent._close(
        validation_metrics["cumulative_double_cost_return"],
        validation_packet["validation_aggregates"]["cumulative_double_cost_return"],
        f"{team_id}.validation.cumulative_double_cost_return",
    )

    stitched = parent._metrics_mapping(
        stitched_returns,
        stitched_double,
        labels,
        train_trades + validation_trades,
    )
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
    gates = validation_packet["structural_hard_gates"]
    assessment = assess_public(
        candidate.identity,
        qualification_metrics,
        reproducible=True,
        data_authority=bool(gates["data_authority"]),
        universe_compliant=bool(gates["universe_compliant"]),
        causal=bool(gates["causal"]),
        execution_compliant=bool(gates["execution_compliant"]),
        solvent=bool(gates["solvent"]),
        window_complete=bool(gates["window_complete"]),
    )
    train_ready = all(
        float(train_metrics[name]) > 0.0
        for name in ("net_sharpe", "annualized_return", "double_cost_sharpe")
    )
    readiness = (
        train_ready
        and bool(validation_packet["readiness"]["validation_positive"])
        and assessment.structural_checks.passed
    )
    nomination_ready = readiness and assessment.eligible
    return (
        {
            "rank": candidate.rank,
            "team_id": team_id,
            "candidate_id": candidate.identity.candidate_id,
            "candidate_identity_sha256": candidate.identity.sha256,
            "train": train_metrics,
            "validation": validation_metrics,
            "stitched_public": stitched,
            "public_assessment": parent._assessment_mapping(assessment),
            "readiness_eligible": readiness,
            "nomination_ready": nomination_ready,
        },
        assessment,
    )


def _build_report(root: Path, authority: StageStitchAuthority) -> dict[str, object]:
    cohort = validation.load_cohort(root)
    _, state = parent._released_authority(root)
    accepted = {str(item["team_id"]): item for item in state.accepted_records}
    terminals = {str(item["team_id"]): item for item in state.terminal_records}

    config = runner_v3._load_config(root / orchestrator_v3.CONFIG_PATH, "team-01")
    authorized = runner_v3._authorized_window(config, "public")
    snapshot = runner_v3._load_verified_snapshot(root, root / orchestrator_v3.DATA_MANIFEST_PATH)
    runner_v3._validate_snapshot_bounds(
        snapshot, config, runner_v3._decision_grid(authorized)
    )
    btc_daily = runner_v3._btc_daily_returns(snapshot.bars, config, authorized)
    labels = metrics_v3.classify_btc_regimes(btc_daily).loc[
        parent.TRAIN_START : parent.PUBLIC_END
    ]
    expected_index = pd.date_range(parent.TRAIN_START, parent.PUBLIC_END, freq="1D")
    if not labels.index.equals(expected_index) or labels.notna().sum() == 0:
        raise StageStitchAddendumError("BTC labels do not cover the exact public grid")

    results: list[dict[str, object]] = []
    assessments: dict[str, PublicAssessment] = {}
    ready: dict[str, bool] = {}
    for candidate in cohort.candidates:
        team_id = candidate.identity.team_id
        packet = validation._read_released_packet(root, terminals[team_id])
        item, assessment = _candidate_result(
            root,
            candidate,
            accepted[team_id],
            terminals[team_id],
            packet,
            labels,
        )
        results.append(item)
        assessments[team_id] = assessment
        ready[team_id] = bool(item["nomination_ready"])
    runner_v3._verify_snapshot_files_unchanged(snapshot)

    ranking = list(
        rank_public_assessments(
            {team_id: assessment for team_id, assessment in assessments.items() if ready[team_id]}
        )
    )
    return {
        "schema_version": "top40-v3-public-development-assessment-v1",
        "amendment_id": ADDENDUM_ID,
        "activation_freeze_sha256": authority.freeze_file_sha256,
        "parent_activation_freeze_sha256": authority.parent_freeze_sha256,
        "cohort_freeze_sha256": cohort.file_sha256,
        "validation_journal_head_sha256": authority.validation_journal_head_sha256,
        "public_window": {
            "start_utc": parent.TRAIN_START.isoformat().replace("+00:00", "Z"),
            "end_exclusive_utc": parent.VALIDATION_END_EXCLUSIVE.isoformat().replace(
                "+00:00", "Z"
            ),
            "construction": "immutable-scored-train-plus-released-scored-validation",
        },
        "results": results,
        "nomination_ready_ranking": ranking,
        "nomination_ready_count": len(ranking),
        "comeback_triggered": len(ranking) < 3,
        "comeback_reason": "fewer-than-three-nomination-ready-teams" if len(ranking) < 3 else None,
    }


def assess(root: str | Path = ".") -> dict[str, object]:
    root_path = orchestrator_v3._trusted_root(root)
    with orchestrator_v3._result_command_lock(root_path):
        authority = verify_activation(root_path)
        body = _build_report(root_path, authority)
        record = {**body, "record_sha256": _sha256(_canonical(body))}
        payload = _pretty(record)
        path = root_path / parent.PUBLIC_REPORT_PATH
        if path.exists() or path.is_symlink():
            if orchestrator_v3._read_regular_bytes(root_path, parent.PUBLIC_REPORT_PATH) != payload:
                raise StageStitchAddendumError("existing public assessment differs")
        else:
            orchestrator_v3._write_new_file(
                root_path, parent.PUBLIC_REPORT_PATH, payload, mode=0o444
            )
        return {"command": "assess", "report_path": parent.PUBLIC_REPORT_PATH, **record, "ok": True}


def report(root: str | Path = ".") -> dict[str, object]:
    root_path = orchestrator_v3._trusted_root(root)
    authority = verify_activation(root_path)
    payload = orchestrator_v3._read_regular_bytes(root_path, parent.PUBLIC_REPORT_PATH)
    record = _strict_json(payload, "public development assessment")
    if (
        _pretty(record) != payload
        or record.get("activation_freeze_sha256") != authority.freeze_file_sha256
    ):
        raise StageStitchAddendumError("public assessment authority changed")
    body = {key: value for key, value in record.items() if key != "record_sha256"}
    if record.get("record_sha256") != _sha256(_canonical(body)):
        raise StageStitchAddendumError("public assessment hash is invalid")
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
    "ProvisionalStageStitchFreeze",
    "StageStitchAddendumError",
    "StageStitchAuthority",
    "assess",
    "freeze_activation",
    "report",
    "validate",
    "verify_activation",
]
