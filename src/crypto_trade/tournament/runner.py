"""Canonical, strategy-neutral runner for one isolated Top-40 tournament team."""

from __future__ import annotations

import dataclasses
import hashlib
import importlib
import inspect
import json
import os
import re
import select
import shutil
import signal
import subprocess
import sys
import sysconfig
import tempfile
import time
import tomllib
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, TextIO

import numpy as np
import pandas as pd

import crypto_trade.tournament.top40 as tournament_contract
from crypto_trade.tournament.data import sha256_manifest
from crypto_trade.tournament.engine import (
    EvaluationResult,
    EvaluatorConfig,
    _normalise_bars,
    _normalise_funding,
    evaluate_base_and_double_cost,
    generate_targets,
)
from crypto_trade.tournament.metrics import (
    aggregate_daily_returns,
    classify_btc_regimes,
    compute_regime_sharpes,
    compute_window_metrics,
    sharpe_confidence_interval,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, DecisionContext
from crypto_trade.tournament.top40 import (
    IS_END,
    IS_START,
    OOS_END,
    OOS_START,
    EvaluationWindow,
)

_TEAM_ID = re.compile(r"team-(?:0[1-9]|10)")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_INTERVAL = pd.Timedelta(hours=8)
_END_EXCLUSIVE = pd.Timestamp("2026-07-01", tz="UTC")
_REQUIRED_DATASETS = (
    "bars",
    "funding",
    "mark_prices",
    "membership",
    "contract_metadata",
)
_CANONICAL_SNAPSHOT_NAMES = frozenset(
    {
        "archive_provenance",
        "bars",
        "btc_daily_returns",
        "btc_regimes",
        "contract_metadata",
        "coverage",
        "exchange_info",
        "funding",
        "mark_prices",
        "mark_rest_provenance",
        "membership",
        "rest_provenance",
    }
)
_SNAPSHOT_BUILDER_PATH = "src/crypto_trade/tournament/snapshot.py"
_DATASET_BASENAMES = {name: f"{name}.parquet" for name in _REQUIRED_DATASETS}
_EVENT_COLUMNS = (
    "timestamp",
    "symbol",
    "event_type",
    "phase",
    "quantity",
    "price",
    "notional",
    "funding_rate",
    "cashflow",
    "fee",
    "slippage",
)
_TRADE_EVENT_TYPES = frozenset({"trade", "risk_reduction", "forced_exit"})
_WORKER_RESPONSE_TIMEOUT_SECONDS = 300.0
_WORKER_TOTAL_TIMEOUT_SECONDS = 900.0
_WORKER_SHUTDOWN_TIMEOUT_SECONDS = 5.0
_MAX_WORKER_RESPONSE_BYTES = 1_048_576
_TEAM_TREE_MAX_FILE_BYTES = 2 * 1024 * 1024
_TEAM_TREE_MAX_TOTAL_BYTES = 10 * 1024 * 1024
_STAGED_CONFIG_MAX_BYTES = 64 * 1024
_MUTABLE_TEAM_OUTPUTS = frozenset({"artifact_manifest.json", "submission.json"})
_TEAM_TEXT_SUFFIXES = frozenset(
    {".py", ".md", ".json", ".jsonl", ".toml", ".lock", ".txt", ".yaml", ".yml"}
)
_STAGED_CONFIG_NAMES = frozenset(
    {
        "frozen_config.json",
        "strategy_config.json",
        "strategy_config.toml",
        "strategy_config.yaml",
        "strategy_config.yml",
    }
)
_LITERAL_DATE_TARGET = re.compile(
    r"(?is)(?:20\d{2}-\d{2}-\d{2}.{0,200}(?:target|weight|position|signal)|"
    r"(?:target|weight|position|signal).{0,200}20\d{2}-\d{2}-\d{2})"
)
_SINGLE_THREAD_ENVIRONMENT_VARIABLES = (
    "BLIS_NUM_THREADS",
    "GOTO_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
    "OMP_NUM_THREADS",
    "OMP_THREAD_LIMIT",
    "OPENBLAS_NUM_THREADS",
    "TBB_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
)


class NetworkAccessError(RuntimeError):
    """Raised when team code attempts network access during a canonical run."""


class StrategySandboxError(RuntimeError):
    """Raised when the isolated strategy worker cannot start or violates its sandbox."""


class StrategyExecutionError(RuntimeError):
    """Raised when team strategy construction or target generation fails in the worker."""


class _OrganizerRunAuthorization:
    """Private identity capability for trusted organizer evaluation calls."""


_ORGANIZER_RUN_AUTHORIZATION = _OrganizerRunAuthorization()


@dataclasses.dataclass(frozen=True)
class TeamRunResult:
    """Canonical outputs and scalar fields needed to populate a submission."""

    team_id: str
    entrypoint: str
    seed: int
    data_manifest_sha256: str
    config_sha256: str
    strategy_sha256: str
    source_bundle_sha256: str
    output_dir: str
    artifacts: Mapping[str, str]
    in_sample: EvaluationWindow
    public_oos: EvaluationWindow
    double_cost_oos_sharpe: float
    regime_sharpe: Mapping[str, float]
    confidence_intervals: Mapping[str, tuple[float, float]]
    decision_count: int
    event_count: int
    trade_count: int

    def submission_fields(self) -> dict[str, Any]:
        """Return the result subset that maps directly onto ``submission.json``."""
        return {
            "team_id": self.team_id,
            "entrypoint": self.entrypoint,
            "seeds": [self.seed],
            "data_manifest_sha256": self.data_manifest_sha256,
            "config_sha256": self.config_sha256,
            "strategy_sha256": self.strategy_sha256,
            "in_sample": dataclasses.asdict(self.in_sample),
            "public_oos": dataclasses.asdict(self.public_oos),
            "double_cost_oos_sharpe": self.double_cost_oos_sharpe,
            "regime_sharpe": dict(self.regime_sharpe),
            "confidence_intervals": {
                name: list(bounds) for name, bounds in self.confidence_intervals.items()
            },
            "artifacts": dict(self.artifacts),
        }


@dataclasses.dataclass(frozen=True)
class _SnapshotData:
    manifest_sha256: str
    paths: Mapping[str, Path]
    file_hashes: Mapping[Path, str]
    bars: pd.DataFrame
    funding: pd.DataFrame
    mark_prices: pd.DataFrame
    membership: pd.DataFrame
    contract_metadata: pd.DataFrame


def run_team(
    root: str | Path,
    team_id: str,
    entrypoint: str | Path,
    config_path: str | Path,
    manifest_path: str | Path,
    *,
    _authorization: object | None = None,
) -> TeamRunResult:
    """Run one team against a verified frozen snapshot and publish canonical artifacts.

    Team code executes only in a namespaced worker and receives past-truncated contexts through
    ``generate_targets``.  The verified snapshot and canonical evaluator remain in the trusted
    parent.  Nothing is promoted to the final report directory until target generation, both
    evaluator passes, metrics, and all artifact writes have succeeded.
    """
    if _authorization is not _ORGANIZER_RUN_AUTHORIZATION:
        raise PermissionError(
            "full-window tournament evaluation is a trusted organizer operation; "
            "use scripts/top40_tournament.py"
        )
    root_path = Path(root).resolve()
    if not root_path.is_dir():
        raise ValueError(f"tournament root is not a directory: {root_path}")
    if not _TEAM_ID.fullmatch(team_id):
        raise ValueError("team_id must be team-01 through team-10")

    entrypoint_path, entrypoint_relative = _resolve_team_entrypoint(root_path, team_id, entrypoint)
    canonical_config_path = _resolve_root_file(root_path, config_path, "config")
    canonical_manifest_path = _resolve_root_file(root_path, manifest_path, "manifest")
    expected_manifest_path = (root_path / "tournament/top40/data_manifest.json").resolve()
    if canonical_manifest_path != expected_manifest_path:
        raise ValueError("manifest_path must be tournament/top40/data_manifest.json")
    initial_config_sha256 = _sha256_file(canonical_config_path)
    initial_strategy_sha256 = _sha256_file(entrypoint_path)
    initial_source_bundle_sha256 = source_bundle_fingerprint(
        root_path, team_id, entrypoint_relative
    )[0]
    initial_manifest_sha256 = _sha256_file(canonical_manifest_path)
    config = _load_config(canonical_config_path, team_id)
    evaluator_config = _evaluator_config(config)
    decision_times = _decision_grid(config)
    seed = int(config["research_budget"]["strategy_seed"])

    snapshot = _load_verified_snapshot(root_path, canonical_manifest_path)
    _validate_snapshot_bounds(snapshot, config, decision_times)
    raw_targets = _generate_targets_in_worker(
        root_path,
        team_id,
        entrypoint_path,
        snapshot.bars,
        snapshot.funding,
        snapshot.membership,
        decision_times,
        seed=seed,
        interval_hours=8,
        expected_source_bundle_sha256=initial_source_bundle_sha256,
    )
    targets = _canonical_targets(raw_targets, snapshot.bars, decision_times)
    base, stressed = evaluate_base_and_double_cost(
        snapshot.bars,
        snapshot.funding,
        snapshot.membership,
        targets,
        mark_prices=snapshot.mark_prices,
        config=evaluator_config,
    )

    _validate_evaluation_grids(base, stressed, decision_times)
    base_daily = _canonical_daily_returns(base.returns, "base")
    stressed_daily = _canonical_daily_returns(stressed.returns, "double-cost")
    btc_daily = _btc_daily_returns(snapshot.bars, config)
    metrics = _compute_metrics(base_daily, stressed_daily, btc_daily, config)
    _verify_snapshot_files_unchanged(snapshot)
    final_hashes = {
        "config": _sha256_file(canonical_config_path),
        "strategy": _sha256_file(entrypoint_path),
        "source_bundle": source_bundle_fingerprint(root_path, team_id, entrypoint_relative)[0],
        "manifest": _sha256_file(canonical_manifest_path),
    }
    initial_hashes = {
        "config": initial_config_sha256,
        "strategy": initial_strategy_sha256,
        "source_bundle": initial_source_bundle_sha256,
        "manifest": initial_manifest_sha256,
    }
    changed = [name for name in initial_hashes if final_hashes[name] != initial_hashes[name]]
    if changed:
        raise ValueError(f"canonical inputs changed during team run: {changed}")
    if snapshot.manifest_sha256 != initial_manifest_sha256:
        raise ValueError("verified snapshot manifest hash differs from the runner input hash")

    artifact_paths = _publish_artifacts(
        root_path,
        team_id,
        targets=targets,
        base=base,
        stressed=stressed,
        base_daily=base_daily,
        stressed_daily=stressed_daily,
    )
    trades = _trade_events(base.events)
    return TeamRunResult(
        team_id=team_id,
        entrypoint=entrypoint_relative,
        seed=seed,
        data_manifest_sha256=snapshot.manifest_sha256,
        config_sha256=initial_config_sha256,
        strategy_sha256=initial_strategy_sha256,
        source_bundle_sha256=initial_source_bundle_sha256,
        output_dir=f"reports-top40/{team_id}",
        artifacts=artifact_paths,
        in_sample=metrics["in_sample"],
        public_oos=metrics["public_oos"],
        double_cost_oos_sharpe=metrics["double_cost_oos_sharpe"],
        regime_sharpe=metrics["regime_sharpe"],
        confidence_intervals=metrics["confidence_intervals"],
        decision_count=len(decision_times),
        event_count=len(base.events),
        trade_count=len(trades),
    )


def _resolve_team_entrypoint(root: Path, team_id: str, entrypoint: str | Path) -> tuple[Path, str]:
    raw = Path(entrypoint)
    if raw.is_absolute() or ".." in PurePosixPath(raw.as_posix()).parts:
        raise ValueError("entrypoint must be a safe path relative to the tournament root")
    relative = PurePosixPath(raw.as_posix()).as_posix()
    required_prefix = f"tournament/top40/teams/{team_id}/"
    if not relative.startswith(required_prefix) or not relative.endswith(".py"):
        raise ValueError(f"entrypoint must be a Python file under {required_prefix}")
    team_root = (root / required_prefix).resolve()
    if not team_root.is_relative_to(root):
        raise ValueError("team namespace escapes the tournament root")
    path = (root / raw).resolve()
    if not path.is_relative_to(team_root) or not path.is_file():
        raise ValueError(f"entrypoint does not exist inside {team_id} namespace: {relative}")
    return path, relative


def _resolve_root_file(root: Path, value: str | Path, label: str) -> Path:
    raw = Path(value)
    path = raw.resolve() if raw.is_absolute() else (root / raw).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f"{label} path escapes tournament root")
    if not path.is_file():
        raise ValueError(f"{label} file does not exist: {path}")
    return path


@dataclasses.dataclass(frozen=True)
class _TeamTreeFile:
    relative: str
    path: Path
    size: int
    sha256: str
    staged: bool


def _stable_file_bytes(path: Path) -> bytes:
    """Read a bounded regular file and reject replacement or mutation during the read."""
    before = path.stat()
    with path.open("rb") as handle:
        content = handle.read(_TEAM_TREE_MAX_FILE_BYTES + 1)
    after = path.stat()
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity:
        raise StrategySandboxError(f"team source file changed while reading: {path.name}")
    if len(content) > _TEAM_TREE_MAX_FILE_BYTES:
        raise StrategySandboxError(f"team source text file exceeds 2 MiB: {path.name}")
    return content


def _timestamp_target_structure(value: object) -> bool:
    if isinstance(value, dict):
        lowered = {str(key).lower() for key in value}
        has_time = any(key in lowered for key in {"timestamp", "timestamp_utc", "date", "time"})
        has_target = any(
            any(token in key for token in ("target", "weight", "position", "signal"))
            for key in lowered
        )
        if has_time and has_target:
            return True
        for key, nested in value.items():
            if re.fullmatch(r"20\d{2}-\d{2}-\d{2}(?:[T ].*)?", str(key)) and isinstance(
                nested, (dict, list, int, float)
            ):
                return True
            if _timestamp_target_structure(nested):
                return True
    elif isinstance(value, list):
        return any(_timestamp_target_structure(item) for item in value)
    return False


def _validate_team_text(relative: str, suffix: str, content: bytes) -> None:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StrategySandboxError(f"team file is not UTF-8 text: {relative}") from exc
    if suffix in {".py", ".toml", ".yaml", ".yml"} and _LITERAL_DATE_TARGET.search(text):
        raise StrategySandboxError(
            f"literal timestamp-to-target/weight logic is forbidden: {relative}"
        )
    if suffix == ".json":
        try:
            parsed: object = json.loads(text)
        except json.JSONDecodeError as exc:
            raise StrategySandboxError(f"invalid JSON team file: {relative}") from exc
        if _timestamp_target_structure(parsed):
            raise StrategySandboxError(
                f"timestamp-keyed target/weight table is forbidden: {relative}"
            )
    elif suffix == ".jsonl":
        try:
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
        except json.JSONDecodeError as exc:
            raise StrategySandboxError(f"invalid JSONL team file: {relative}") from exc
        if any(_timestamp_target_structure(row) for row in rows):
            raise StrategySandboxError(
                f"timestamp-keyed target/weight table is forbidden: {relative}"
            )


def _team_tree_files(source: Path) -> list[_TeamTreeFile]:
    """Validate and fingerprint every non-self regular file in a team namespace."""
    files: list[_TeamTreeFile] = []
    total_size = 0
    for path in sorted(source.rglob("*"), key=lambda candidate: candidate.as_posix()):
        relative = path.relative_to(source)
        relative_text = relative.as_posix()
        if relative_text in _MUTABLE_TEAM_OUTPUTS:
            continue
        if "__pycache__" in relative.parts or path.suffix.lower() == ".pyc":
            raise StrategySandboxError(f"generated Python cache is forbidden: {relative}")
        if path.is_symlink():
            raise StrategySandboxError(f"team tree cannot contain symlinks: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise StrategySandboxError(f"team tree contains a non-regular file: {relative}")
        suffix = path.suffix.lower()
        if suffix not in _TEAM_TEXT_SUFFIXES:
            raise StrategySandboxError(
                f"opaque/prefit file type is forbidden in canonical team tree: {relative}"
            )
        content = _stable_file_bytes(path)
        total_size += len(content)
        if total_size > _TEAM_TREE_MAX_TOTAL_BYTES:
            raise StrategySandboxError("canonical team source tree exceeds 10 MiB")
        _validate_team_text(relative_text, suffix, content)
        staged = suffix == ".py" or path.name in _STAGED_CONFIG_NAMES
        if path.name in _STAGED_CONFIG_NAMES and len(content) > _STAGED_CONFIG_MAX_BYTES:
            raise StrategySandboxError(f"staged strategy config exceeds 64 KiB: {relative}")
        files.append(
            _TeamTreeFile(
                relative=relative_text,
                path=path,
                size=len(content),
                sha256=hashlib.sha256(content).hexdigest(),
                staged=staged,
            )
        )
    return files


def _team_tree_fingerprint(files: Sequence[_TeamTreeFile]) -> str:
    entries = [{"path": item.relative, "size": item.size, "sha256": item.sha256} for item in files]
    encoded = json.dumps(entries, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def source_bundle_fingerprint(
    root: str | Path,
    team_id: str,
    entrypoint: str | Path,
) -> tuple[str, tuple[dict[str, object], ...]]:
    """Hash the complete validated team tree, not only the executable worker subset."""
    root_path = Path(root).resolve()
    entrypoint_path, _relative = _resolve_team_entrypoint(root_path, team_id, entrypoint)
    files = _team_tree_files(entrypoint_path.parent)
    entries = tuple(
        {"path": item.relative, "size": item.size, "sha256": item.sha256} for item in files
    )
    return _team_tree_fingerprint(files), entries


class _StrategyWorkerClient:
    def __init__(self, process: subprocess.Popen[str], diagnostics: BinaryIO | None = None) -> None:
        if process.stdin is None or process.stdout is None:
            raise StrategySandboxError("strategy worker pipes were not created")
        self.process = process
        self.stdin: TextIO = process.stdin
        self.stdout: TextIO = process.stdout
        self.diagnostics = diagnostics
        self.ready = False
        self._response_buffer = b""
        self._closed = False
        self._process_group_reaped = False
        self._whole_run_deadline = time.monotonic() + _WORKER_TOTAL_TIMEOUT_SECONDS

    def _diagnostic_text(self) -> str:
        if self.diagnostics is None:
            return ""
        try:
            self.diagnostics.flush()
            self.diagnostics.seek(0)
            return self.diagnostics.read().decode("utf-8", errors="replace").strip()
        except OSError:
            return ""

    def request(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        if self._closed:
            raise StrategySandboxError("strategy worker client is closed")
        try:
            encoded = json.dumps(payload, allow_nan=False, separators=(",", ":"))
            self.stdin.write(encoded + "\n")
            self.stdin.flush()
        except (BrokenPipeError, OSError, ValueError) as exc:
            self.process.poll()
            detail = self._diagnostic_text()
            suffix = f": {detail}" if detail else ""
            raise StrategySandboxError(f"strategy worker communication failed{suffix}") from exc
        response_deadline = time.monotonic() + _WORKER_RESPONSE_TIMEOUT_SECONDS
        deadline = min(response_deadline, self._whole_run_deadline)
        while b"\n" not in self._response_buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                self._kill_process_group()
                detail = self._diagnostic_text()
                suffix = f": {detail}" if detail else ""
                if deadline == self._whole_run_deadline:
                    raise StrategySandboxError(
                        "strategy worker exceeded the whole-run wall deadline of "
                        f"{_WORKER_TOTAL_TIMEOUT_SECONDS:g}s{suffix}"
                    )
                raise StrategySandboxError(
                    "strategy worker response timed out after "
                    f"{_WORKER_RESPONSE_TIMEOUT_SECONDS:g}s{suffix}"
                )
            readable, _, _ = select.select([self.stdout.fileno()], [], [], remaining)
            if not readable:
                continue
            try:
                chunk = os.read(self.stdout.fileno(), 65_536)
            except OSError as exc:
                raise StrategySandboxError("cannot read strategy worker response") from exc
            if not chunk:
                break
            if len(self._response_buffer) + len(chunk) > _MAX_WORKER_RESPONSE_BYTES:
                self._kill_process_group()
                raise StrategySandboxError(
                    "strategy worker response exceeded the maximum size of "
                    f"{_MAX_WORKER_RESPONSE_BYTES} bytes"
                )
            self._response_buffer += chunk
        if b"\n" in self._response_buffer:
            raw_line, self._response_buffer = self._response_buffer.split(b"\n", 1)
            try:
                line = raw_line.decode("utf-8", errors="strict")
            except UnicodeDecodeError as exc:
                raise StrategySandboxError(
                    "strategy worker returned non-UTF-8 protocol data"
                ) from exc
        else:
            line = ""
        if not line:
            returncode = self.process.poll()
            if returncode is None:
                self._kill_process_group()
                returncode = self.process.returncode
            detail = self._diagnostic_text()
            suffix = f": {detail}" if detail else ""
            raise StrategySandboxError(
                f"strategy worker exited without a response (status {returncode}){suffix}"
            )
        try:
            response = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StrategySandboxError("strategy worker returned malformed protocol JSON") from exc
        if not isinstance(response, dict):
            raise StrategySandboxError("strategy worker response must be a JSON object")
        if response.get("type") == "error":
            error_type = str(response.get("error_type", "StrategyExecutionError"))
            message = str(response.get("message", "strategy worker failed"))
            if error_type == "StrategySandboxViolationError":
                if "network access" in message:
                    raise NetworkAccessError(message)
                raise StrategySandboxError(message)
            if error_type == "StrategySandboxError":
                raise StrategySandboxError(message)
            raise StrategyExecutionError(f"{error_type}: {message}")
        return response

    def initialise(self, payload: Mapping[str, Any]) -> None:
        response = self.request(payload)
        if response.get("type") != "ready":
            raise StrategySandboxError("strategy worker did not acknowledge initialization")
        self.ready = True

    def _kill_process_group(self) -> None:
        if self._process_group_reaped:
            return
        # The namespace leader may already have exited while one of its descendants remains.
        # Always target the dedicated session/process group created at launch.
        try:
            os.killpg(self.process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        try:
            self.process.wait(timeout=_WORKER_SHUTDOWN_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=_WORKER_SHUTDOWN_TIMEOUT_SECONDS)
        self._process_group_reaped = True

    def _close_handles(self) -> None:
        if self._closed:
            return
        self._closed = True
        for stream in (self.stdin, self.stdout, self.diagnostics):
            if stream is None:
                continue
            try:
                stream.close()
            except OSError:
                pass

    def abort(self) -> None:
        if self._closed:
            return
        self._kill_process_group()
        self._close_handles()

    def finish(self) -> None:
        if self._closed:
            raise StrategySandboxError("strategy worker was already closed")
        returncode = self.process.poll()
        if returncode is not None:
            detail = self._diagnostic_text()
            suffix = f": {detail}" if detail else ""
            self.abort()
            raise StrategySandboxError(
                f"strategy worker exited before clean shutdown (status {returncode}){suffix}"
            )
        try:
            response = self.request({"type": "shutdown"})
            if response.get("type") != "bye":
                raise StrategySandboxError("strategy worker did not acknowledge shutdown")
            remaining = self._whole_run_deadline - time.monotonic()
            if remaining <= 0:
                raise StrategySandboxError("strategy worker exceeded its whole-run wall deadline")
            returncode = self.process.wait(timeout=min(_WORKER_SHUTDOWN_TIMEOUT_SECONDS, remaining))
            if returncode != 0:
                detail = self._diagnostic_text()
                suffix = f": {detail}" if detail else ""
                raise StrategySandboxError(
                    f"strategy worker exited uncleanly (status {returncode}){suffix}"
                )
            self._process_group_reaped = True
        except BaseException:
            self.abort()
            raise
        self._close_handles()


def _strategy_worker_command(
    root: Path,
    repository_parent: Path,
    bundle: Path,
    site_packages: Path,
    runtime_site_packages: Path,
    entrypoint: str,
    empty_dir: Path,
    empty_file: Path,
) -> list[str]:
    if not sys.platform.startswith("linux"):
        raise StrategySandboxError("canonical strategy workers require Linux namespaces")
    unshare = shutil.which("unshare")
    if unshare is None:
        raise StrategySandboxError("unshare is unavailable; refusing an unsandboxed team run")
    return [
        unshare,
        "--user",
        "--map-root-user",
        "--mount",
        "--net",
        "--pid",
        "--fork",
        "--kill-child=KILL",
        "--mount-proc",
        sys.executable,
        "-u",
        "-m",
        "crypto_trade.tournament._strategy_worker",
        "--root",
        str(root),
        "--repository-parent",
        str(repository_parent),
        "--bundle",
        str(bundle),
        "--site-packages",
        str(site_packages),
        "--runtime-site-packages",
        str(runtime_site_packages),
        "--entrypoint",
        entrypoint,
        "--empty-dir",
        str(empty_dir),
        "--empty-file",
        str(empty_file),
    ]


def _copy_team_source_bundle(
    source: Path,
    destination: Path,
    *,
    expected_fingerprint: str | None = None,
) -> str:
    before = _team_tree_files(source)
    fingerprint = _team_tree_fingerprint(before)
    if expected_fingerprint is not None and fingerprint != expected_fingerprint:
        raise StrategySandboxError("team tree differs from the pre-run fingerprint")
    destination.mkdir(parents=True, exist_ok=False)
    for item in before:
        if not item.staged:
            continue
        target = destination / item.relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(item.path, target)
        staged_content = _stable_file_bytes(target)
        if (
            len(staged_content) != item.size
            or hashlib.sha256(staged_content).hexdigest() != item.sha256
        ):
            raise StrategySandboxError(
                f"staged team source differs from fingerprint: {item.relative}"
            )
    after = _team_tree_files(source)
    if _team_tree_fingerprint(after) != fingerprint:
        raise StrategySandboxError("team tree changed while staging the worker bundle")
    return fingerprint


def _runner_repository_parent() -> Path:
    """Return the common Git repository whose worktrees must be hidden from team code."""
    checkout_root = Path(__file__).resolve().parents[3]
    git_marker = checkout_root / ".git"
    if git_marker.is_dir():
        common_git_dir = git_marker.resolve()
    elif git_marker.is_file():
        try:
            marker = git_marker.read_text(encoding="utf-8").strip()
        except OSError as exc:
            raise StrategySandboxError(f"cannot read runner Git metadata: {exc}") from exc
        prefix = "gitdir: "
        if not marker.startswith(prefix):
            raise StrategySandboxError("runner .git file does not declare a gitdir")
        raw_git_dir = Path(marker.removeprefix(prefix))
        git_dir = (
            raw_git_dir.resolve()
            if raw_git_dir.is_absolute()
            else (checkout_root / raw_git_dir).resolve()
        )
        common_dir_file = git_dir / "commondir"
        try:
            raw_common_dir = Path(common_dir_file.read_text(encoding="utf-8").strip())
        except OSError as exc:
            raise StrategySandboxError(f"cannot read runner common Git metadata: {exc}") from exc
        common_git_dir = (
            raw_common_dir.resolve()
            if raw_common_dir.is_absolute()
            else (git_dir / raw_common_dir).resolve()
        )
    else:
        raise StrategySandboxError("cannot locate the runner Git repository")
    repository_parent = common_git_dir.parent.resolve()
    if (
        common_git_dir.name != ".git"
        or not repository_parent.is_dir()
        or not checkout_root.is_relative_to(repository_parent)
    ):
        raise StrategySandboxError("runner common Git repository is not safely nested")
    return repository_parent


def _current_venv_site_packages(repository_parent: Path) -> Path:
    """Locate the active venv runtime that must survive masking the repository."""
    purelib = Path(sysconfig.get_path("purelib")).resolve()
    platlib = Path(sysconfig.get_path("platlib")).resolve()
    prefix = Path(sys.prefix).resolve()
    if purelib != platlib:
        raise StrategySandboxError("worker requires one shared purelib/platlib directory")
    if (
        not purelib.is_dir()
        or not purelib.is_relative_to(prefix)
        or not purelib.is_relative_to(repository_parent)
    ):
        raise StrategySandboxError(
            "active worker site-packages must be inside the masked repository venv"
        )
    return purelib


def _strategy_worker_environment(seed: int) -> dict[str, str]:
    if not 0 <= seed <= 2**32 - 1:
        raise StrategySandboxError("strategy seed is outside PYTHONHASHSEED's integer range")
    # Do not inherit credentials, proxy settings, cloud configuration, or loader controls from
    # the organizer. Every variable visible to team code is constructed explicitly here.
    environment = {
        "CUDA_VISIBLE_DEVICES": "",
        "HOME": "/nonexistent",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/sbin:/usr/bin:/sbin:/bin",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": str(seed),
        "PYTHONNOUSERSITE": "1",
        "PYTHONUNBUFFERED": "1",
        "TZ": "UTC",
        "XDG_CACHE_HOME": "/nonexistent",
        "XDG_CONFIG_HOME": "/nonexistent",
    }
    for name in _SINGLE_THREAD_ENVIRONMENT_VARIABLES:
        environment[name] = "1"
    return environment


def _launch_strategy_worker(
    root: Path,
    entrypoint: Path,
    team_id: str,
    seed: int,
    expected_source_bundle_sha256: str | None,
) -> tuple[_StrategyWorkerClient, tempfile.TemporaryDirectory[str]]:
    repository_parent = _runner_repository_parent()
    site_packages = _current_venv_site_packages(repository_parent)
    sandbox = tempfile.TemporaryDirectory(prefix=f"top40-{team_id}-")
    sandbox_root = Path(sandbox.name)
    bundle = sandbox_root / "bundle"
    runtime_site_packages = sandbox_root / "runtime-site-packages"
    empty_dir = sandbox_root / "empty-dir"
    empty_file = sandbox_root / "empty-file"
    runtime_site_packages.mkdir()
    empty_dir.mkdir()
    empty_file.touch()
    source = entrypoint.parent
    try:
        _copy_team_source_bundle(
            source,
            bundle,
            expected_fingerprint=expected_source_bundle_sha256,
        )
        copied_entrypoint = entrypoint.relative_to(source).as_posix()
        command = _strategy_worker_command(
            root,
            repository_parent,
            bundle,
            site_packages,
            runtime_site_packages,
            copied_entrypoint,
            empty_dir,
            empty_file,
        )
        environment = _strategy_worker_environment(seed)
        try:
            process = subprocess.Popen(
                command,
                cwd=sandbox_root,
                env=environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                close_fds=True,
                start_new_session=True,
            )
        except OSError as exc:
            raise StrategySandboxError(f"cannot launch strategy namespace: {exc}") from exc
        return _StrategyWorkerClient(process), sandbox
    except BaseException:
        sandbox.cleanup()
        raise


def _json_scalar(value: Any) -> Any:
    if value is None or value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, pd.Timestamp):
        timestamp = value
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        return timestamp.isoformat()
    if isinstance(value, float):
        return value if np.isfinite(value) else None
    if isinstance(value, (str, int, bool)):
        return value
    try:
        if bool(pd.isna(value)):
            return None
    except (TypeError, ValueError):
        pass
    raise TypeError(f"unsupported strategy-context scalar type: {type(value).__name__}")


def _datetime_columns(frame: pd.DataFrame) -> list[str]:
    return [
        str(column)
        for column in frame.columns
        if isinstance(frame[column].dtype, pd.DatetimeTZDtype)
        or pd.api.types.is_datetime64_dtype(frame[column].dtype)
    ]


def _encoded_rows(frame: pd.DataFrame, columns: Sequence[str]) -> list[list[Any]]:
    return [
        [_json_scalar(value) for value in row]
        for row in frame.loc[:, list(columns)].itertuples(index=False, name=None)
    ]


def _validated_worker_weights(
    response: Mapping[str, Any], eligible: Sequence[str]
) -> dict[str, float] | None:
    if response.get("type") != "weights" or "weights" not in response:
        raise StrategySandboxError("strategy worker returned an invalid weight response")
    raw_weights = response["weights"]
    if raw_weights is None:
        return None
    if not isinstance(raw_weights, dict):
        raise StrategySandboxError("strategy worker returned an invalid weight response")
    eligible_set = set(eligible)
    weights: dict[str, float] = {}
    for symbol, raw_weight in raw_weights.items():
        if not isinstance(symbol, str) or symbol not in eligible_set:
            raise StrategySandboxError("strategy worker returned an ineligible target symbol")
        if isinstance(raw_weight, bool):
            raise StrategySandboxError("strategy worker returned a Boolean target weight")
        try:
            weight = float(raw_weight)
        except (TypeError, ValueError) as exc:
            raise StrategySandboxError("strategy worker returned a non-numeric weight") from exc
        if not np.isfinite(weight):
            raise StrategySandboxError("strategy worker returned a non-finite weight")
        weights[symbol] = weight
    return weights


class _WorkerStrategyProxy:
    """Delta-encode authoritative ``generate_targets`` contexts for one worker."""

    def __init__(
        self,
        worker: _StrategyWorkerClient,
        *,
        seed: int,
        interval_hours: int,
        bar_schema: pd.DataFrame,
        funding_schema: pd.DataFrame,
        bar_history: pd.DataFrame | None = None,
        funding_history: pd.DataFrame | None = None,
    ):
        self.worker = worker
        self.seed = seed
        self.bar_columns = tuple(str(column) for column in bar_schema.columns)
        self.funding_columns = tuple(str(column) for column in funding_schema.columns)
        self.interval = pd.Timedelta(hours=interval_hours)
        self.bar_cursors: dict[str, int] = {}
        self.funding_cursors: dict[str, int] = {}
        self.previous_decision: pd.Timestamp | None = None
        if (bar_history is None) != (funding_history is None):
            raise ValueError("canonical bar and funding histories must be supplied together")
        self.bar_history = self._group_history(bar_history, self.bar_columns, "bar")
        self.funding_history = self._group_history(funding_history, self.funding_columns, "funding")
        self.bar_times = self._history_times(self.bar_history, "open_time")
        self.funding_times = self._history_times(self.funding_history, "funding_time")
        worker.initialise(
            {
                "type": "init",
                "seed": seed,
                "interval_hours": interval_hours,
                "bar_columns": list(self.bar_columns),
                "bar_dtypes": [str(dtype) for dtype in bar_schema.dtypes],
                "bar_datetime_columns": _datetime_columns(bar_schema),
                "funding_columns": list(self.funding_columns),
                "funding_dtypes": [str(dtype) for dtype in funding_schema.dtypes],
                "funding_datetime_columns": _datetime_columns(funding_schema),
            }
        )

    @staticmethod
    def _group_history(
        history: pd.DataFrame | None,
        columns: tuple[str, ...],
        label: str,
    ) -> dict[str, pd.DataFrame] | None:
        if history is None:
            return None
        if tuple(str(column) for column in history.columns) != columns:
            raise StrategySandboxError(f"canonical {label} history schema differs")
        if "symbol" not in history.columns:
            raise StrategySandboxError(f"canonical {label} history has no symbol column")
        return {
            str(symbol): frame.reset_index(drop=True).copy(deep=True)
            for symbol, frame in history.groupby("symbol", observed=True, sort=False)
        }

    @staticmethod
    def _history_times(
        histories: dict[str, pd.DataFrame] | None, column: str
    ) -> dict[str, pd.DatetimeIndex] | None:
        if histories is None:
            return None
        result: dict[str, pd.DatetimeIndex] = {}
        for symbol, frame in histories.items():
            values = pd.DatetimeIndex(pd.to_datetime(frame[column], utc=True))
            if not values.is_monotonic_increasing:
                raise StrategySandboxError(f"canonical {column} history is not sorted")
            result[symbol] = values
        return result

    @staticmethod
    def _history_end(
        values: pd.DatetimeIndex,
        cutoff: pd.Timestamp,
        *,
        side: str,
    ) -> int:
        return int(values.searchsorted(cutoff, side=side))

    @staticmethod
    def _validate_context_boundary(
        context_frame: pd.DataFrame,
        canonical_frame: pd.DataFrame,
        length: int,
        *,
        symbol: str,
        label: str,
    ) -> None:
        if tuple(str(column) for column in context_frame.columns) != tuple(
            str(column) for column in canonical_frame.columns
        ):
            raise StrategySandboxError(f"authoritative {label} schema changed for {symbol}")
        if len(context_frame) != length:
            raise StrategySandboxError(f"authoritative {label} history length differs for {symbol}")
        if not length:
            return
        # Worker deltas come from the private canonical snapshot copy below, never from this
        # repeatedly materialized context. Boundary checks still fail closed on truncation,
        # reorder, or replacement at either edge without hashing the full prefix every decision.
        for offset in (0, length - 1):
            left = context_frame.iloc[offset]
            right = canonical_frame.iloc[offset]
            if not left.equals(right):
                raise StrategySandboxError(
                    f"authoritative {label} history boundary changed for {symbol}"
                )

    @staticmethod
    def _tail(
        frame: pd.DataFrame,
        *,
        symbol: str,
        cursor: int,
        columns: tuple[str, ...],
        label: str,
    ) -> list[list[Any]]:
        if tuple(str(column) for column in frame.columns) != columns:
            raise StrategySandboxError(f"authoritative {label} schema changed for {symbol}")
        if len(frame) < cursor:
            raise StrategySandboxError(f"authoritative {label} history shrank for {symbol}")
        return _encoded_rows(frame.iloc[cursor:], columns)

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        if seed != self.seed:
            raise StrategySandboxError("trusted target generator changed the strategy seed")
        if context.auxiliary:
            raise StrategySandboxError("worker protocol does not accept auxiliary datasets")
        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")
        if self.previous_decision is not None and decision_time <= self.previous_decision:
            raise StrategySandboxError("trusted target generator emitted unordered decisions")
        eligible = tuple(str(symbol) for symbol in context.eligible_symbols)
        if len(eligible) != len(set(eligible)):
            raise StrategySandboxError("trusted target generator emitted duplicate symbols")
        eligible_set = set(eligible)
        context_bar_symbols = {str(symbol) for symbol in context.bars}
        if context_bar_symbols != eligible_set:
            raise StrategySandboxError(
                "trusted bar context must contain exactly the eligible symbols"
            )
        bar_updates: dict[str, list[list[Any]]] = {}
        funding_updates: dict[str, list[list[Any]]] = {}
        if self.bar_history is not None:
            assert self.bar_times is not None
            assert self.funding_history is not None
            assert self.funding_times is not None
            closed_cutoff = decision_time - self.interval
            for symbol in eligible:
                history = self.bar_history.get(symbol)
                times = self.bar_times.get(symbol)
                if history is None or times is None:
                    raise StrategySandboxError(
                        f"eligible symbol has no canonical bar history: {symbol}"
                    )
                stop = self._history_end(times, closed_cutoff, side="right")
                self._validate_context_boundary(
                    context.bars[symbol], history, stop, symbol=symbol, label="bar"
                )
                cursor = self.bar_cursors.get(symbol, 0)
                if stop < cursor:
                    raise StrategySandboxError(f"canonical bar history shrank for {symbol}")
                update = _encoded_rows(history.iloc[cursor:stop], self.bar_columns)
                if update:
                    bar_updates[symbol] = update
                self.bar_cursors[symbol] = stop

            if tuple(str(column) for column in context.funding.columns) != self.funding_columns:
                raise StrategySandboxError("authoritative funding schema changed")
            expected_funding_rows = 0
            for symbol in eligible:
                history = self.funding_history.get(symbol)
                times = self.funding_times.get(symbol)
                if history is None or times is None:
                    continue
                stop = self._history_end(times, decision_time, side="left")
                expected_funding_rows += stop
                cursor = self.funding_cursors.get(symbol, 0)
                if stop < cursor:
                    raise StrategySandboxError(f"canonical funding history shrank for {symbol}")
                update = _encoded_rows(history.iloc[cursor:stop], self.funding_columns)
                if update:
                    funding_updates[symbol] = update
                self.funding_cursors[symbol] = stop
            if len(context.funding) != expected_funding_rows:
                raise StrategySandboxError("authoritative funding history length differs")
        else:
            for raw_symbol, frame in context.bars.items():
                symbol = str(raw_symbol)
                cursor = self.bar_cursors.get(symbol, 0)
                update = self._tail(
                    frame,
                    symbol=symbol,
                    cursor=cursor,
                    columns=self.bar_columns,
                    label="bar",
                )
                if update:
                    bar_updates[symbol] = update
                self.bar_cursors[symbol] = len(frame)
            if not context.funding.empty:
                for raw_symbol, frame in context.funding.groupby(
                    "symbol", observed=True, sort=False
                ):
                    symbol = str(raw_symbol)
                    if symbol not in eligible_set:
                        raise StrategySandboxError(
                            "trusted funding context includes an ineligible symbol"
                        )
                    cursor = self.funding_cursors.get(symbol, 0)
                    update = self._tail(
                        frame,
                        symbol=symbol,
                        cursor=cursor,
                        columns=self.funding_columns,
                        label="funding",
                    )
                    if update:
                        funding_updates[symbol] = update
                    self.funding_cursors[symbol] = len(frame)
        response = self.worker.request(
            {
                "type": "decision",
                "decision_time": decision_time.isoformat(),
                "eligible_symbols": list(eligible),
                "bars": bar_updates,
                "funding": funding_updates,
            }
        )
        self.previous_decision = decision_time
        return _validated_worker_weights(response, eligible)


def _generate_targets_in_worker(
    root: Path,
    team_id: str,
    entrypoint: Path,
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    decision_times: Sequence[pd.Timestamp],
    *,
    seed: int,
    interval_hours: int,
    expected_source_bundle_sha256: str | None = None,
) -> pd.DataFrame:
    worker, sandbox = _launch_strategy_worker(
        root,
        entrypoint,
        team_id,
        seed,
        expected_source_bundle_sha256,
    )
    try:
        canonical_bars = _normalise_bars(bars)
        canonical_funding = _normalise_funding(funding)
        bar_schema = canonical_bars.iloc[0:0]
        funding_schema = canonical_funding.iloc[0:0]
        proxy = _WorkerStrategyProxy(
            worker,
            seed=seed,
            interval_hours=interval_hours,
            bar_schema=bar_schema,
            funding_schema=funding_schema,
            bar_history=canonical_bars,
            funding_history=canonical_funding,
        )
        targets = generate_targets(
            proxy,
            bars,
            funding,
            membership,
            decision_times,
            seed=seed,
            interval_hours=interval_hours,
        )
    except BaseException:
        worker.abort()
        raise
    else:
        worker.finish()
        return targets
    finally:
        sandbox.cleanup()


def _load_config(path: Path, team_id: str) -> dict[str, Any]:
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    teams = config.get("teams")
    if not isinstance(teams, list) or team_id not in teams:
        raise ValueError(f"{team_id} is not registered in the tournament config")
    try:
        execution = config["execution"]
        statistics = config["statistics"]
        regimes = config["regimes"]
        research = config["research_budget"]
        data = config["data"]
        splits = config["splits"]
    except KeyError as exc:
        raise ValueError(f"config missing section: {exc.args[0]}") from exc
    if data.get("transaction_interval") != "8h" or execution.get("base_interval") != "8h":
        raise ValueError("canonical runner requires an 8h transaction interval")
    if float(execution.get("double_cost_multiplier", 0.0)) != 2.0:
        raise ValueError("double_cost_multiplier must be exactly 2.0")
    fixed_splits = {
        "in_sample_start": IS_START,
        "in_sample_end_inclusive": IS_END,
        "public_oos_start": OOS_START,
        "public_oos_end_inclusive": OOS_END,
    }
    for name, expected in fixed_splits.items():
        if splits.get(name) != expected:
            raise ValueError(f"config {name} must be {expected}")
    if data.get("hard_end_exclusive") != "2026-07-01":
        raise ValueError("hard_end_exclusive must be 2026-07-01")
    expected_regimes = {
        "stress_trailing_days": 30,
        "stress_annualized_btc_vol": 0.80,
        "direction_trailing_days": 60,
        "bull_btc_return": 0.10,
        "bear_btc_return": -0.10,
        "lag_days": 1,
    }
    if any(regimes.get(name) != value for name, value in expected_regimes.items()):
        raise ValueError("config regime parameters differ from the canonical metric implementation")
    if int(execution.get("annualization_days", 0)) != 365:
        raise ValueError("annualization_days must be 365")
    if int(statistics.get("bootstrap_samples", 0)) < 100:
        raise ValueError("bootstrap_samples must be at least 100")
    if int(statistics.get("bootstrap_block_days", 0)) < 1:
        raise ValueError("bootstrap_block_days must be positive")
    try:
        strategy_seed = int(research["strategy_seed"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("research_budget.strategy_seed must be an integer") from exc
    if not 0 <= strategy_seed <= 2**32 - 1:
        raise ValueError("research_budget.strategy_seed must fit PYTHONHASHSEED's integer range")
    return config


def _evaluator_config(config: Mapping[str, Any]) -> EvaluatorConfig:
    execution = config["execution"]
    return EvaluatorConfig(
        interval_hours=8,
        initial_equity=float(execution["initial_equity_usdt"]),
        taker_fee_bps_per_side=float(execution["taker_fee_bps_per_side"]),
        slippage_bps_per_side=float(execution["slippage_bps_per_side"]),
        max_gross_exposure=float(execution["max_gross_exposure"]),
        max_abs_net_exposure=float(execution["max_abs_net_exposure"]),
        max_symbol_exposure=float(execution["max_symbol_exposure"]),
        max_bar_participation=float(execution["max_bar_participation"]),
    )


def _decision_grid(config: Mapping[str, Any]) -> pd.DatetimeIndex:
    start = pd.Timestamp(config["splits"]["in_sample_start"], tz="UTC")
    end = pd.Timestamp(config["data"]["hard_end_exclusive"], tz="UTC")
    return pd.date_range(start, end, freq=_INTERVAL, inclusive="left")


def _load_verified_snapshot(root: Path, manifest_path: Path) -> _SnapshotData:
    try:
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(manifest_text)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read snapshot manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("snapshot manifest root must be an object")
    raw_entries = manifest.get("files", manifest.get("entries"))
    if not isinstance(raw_entries, list):
        raise ValueError("snapshot manifest must contain a files or entries list")

    entries: list[tuple[Mapping[str, Any], Path]] = []
    seen_paths: set[Path] = set()
    for index, raw_entry in enumerate(raw_entries):
        if not isinstance(raw_entry, dict):
            raise ValueError(f"snapshot manifest entry {index} must be an object")
        path_value = raw_entry.get("path")
        size = raw_entry.get("size")
        sha256 = raw_entry.get("sha256")
        if not isinstance(path_value, str) or not path_value:
            raise ValueError(f"snapshot manifest entry {index} has no path")
        pure_path = PurePosixPath(path_value)
        if pure_path.is_absolute() or ".." in pure_path.parts or "." in pure_path.parts:
            raise ValueError(f"unsafe snapshot path: {path_value}")
        path = (root / Path(*pure_path.parts)).resolve()
        if not path.is_relative_to(root):
            raise ValueError(f"snapshot path escapes tournament root: {path_value}")
        if path in seen_paths:
            raise ValueError(f"duplicate snapshot manifest path: {path_value}")
        seen_paths.add(path)
        if not path.is_file():
            raise ValueError(f"snapshot file does not exist: {path_value}")
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError(f"snapshot entry has invalid size: {path_value}")
        if path.stat().st_size != size:
            raise ValueError(f"snapshot size mismatch: {path_value}")
        if not isinstance(sha256, str) or not _SHA256.fullmatch(sha256):
            raise ValueError(f"snapshot entry has invalid sha256: {path_value}")
        actual_sha256 = _sha256_file(path)
        if actual_sha256 != sha256:
            raise ValueError(
                f"snapshot sha256 mismatch for {path_value}: {actual_sha256} != {sha256}"
            )
        entries.append((raw_entry, path))

    if not _phase0_allows_fast_snapshot_verification(root, manifest_path, manifest, manifest_text):
        _invoke_snapshot_verifier(root, manifest_path)
    paths = {name: _resolve_dataset_entry(name, entries) for name in _REQUIRED_DATASETS}
    if len(set(paths.values())) != len(paths):
        raise ValueError("required logical datasets must resolve to distinct files")
    frames = {name: pd.read_parquet(path) for name, path in paths.items()}
    return _SnapshotData(
        manifest_sha256=_sha256_file(manifest_path),
        paths=paths,
        file_hashes={path: str(entry["sha256"]) for entry, path in entries},
        bars=frames["bars"],
        funding=frames["funding"],
        mark_prices=frames["mark_prices"],
        membership=frames["membership"],
        contract_metadata=frames["contract_metadata"],
    )


def _phase0_allows_fast_snapshot_verification(
    root: Path,
    manifest_path: Path,
    manifest: Mapping[str, Any],
    manifest_text: str,
) -> bool:
    """Prove that Phase 0 already performed the expensive source-provenance audit.

    Absence of a Phase-0 record preserves the standalone/full-verifier behavior.  Once a
    Phase-0 record exists, however, an invalid or stale binding is an integrity fault rather than
    permission to silently evaluate against a different snapshot.  The fast path therefore
    fails closed on any malformed, dirty, rewritten, or mismatched Phase-0 record.

    This deliberately does *not* reparse raw Binance archives.  It binds the canonical manifest,
    builder, evaluator, config, dependency lock, methodology, and organizer bytes to the common
    commit whose exact child uniquely first-added ``phase0_freeze.json``.  The caller has already
    hashed every manifest-listed canonical file and will hash every one again after team code.
    """
    freeze_path = root / tournament_contract.PHASE0_FREEZE_PATH
    if not freeze_path.exists() and not freeze_path.is_symlink():
        return False

    issues: list[tournament_contract.ValidationIssue] = []
    if not freeze_path.is_file() or freeze_path.is_symlink():
        issues.append(
            tournament_contract.ValidationIssue(
                "phase0_freeze", "phase0_freeze.json is missing or unsafe"
            )
        )
    state_path = root / tournament_contract.RUN_STATE_PATH
    if not state_path.is_file() or state_path.is_symlink():
        issues.append(
            tournament_contract.ValidationIssue("run_state", "run_state.json is missing or unsafe")
        )

    freeze = tournament_contract._read_json_object(  # noqa: SLF001
        freeze_path, "phase0_freeze", issues
    )
    state = tournament_contract._read_json_object(  # noqa: SLF001
        state_path, "run_state", issues
    )
    if freeze is None or state is None:
        _raise_phase0_fast_path_issues(issues)
    assert freeze is not None and state is not None

    issues.extend(tournament_contract._validate_run_state_phase(state))  # noqa: SLF001
    if freeze.get("schema_version") != 1:
        issues.append(
            tournament_contract.ValidationIssue(
                "phase0_freeze.schema_version", "Phase-0 schema_version must be 1"
            )
        )
    if freeze.get("branch") != tournament_contract.TOURNAMENT_BRANCH:
        issues.append(
            tournament_contract.ValidationIssue(
                "phase0_freeze.branch",
                f"Phase-0 branch must be {tournament_contract.TOURNAMENT_BRANCH}",
            )
        )
    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if branch.returncode != 0 or branch.stdout.strip() != tournament_contract.TOURNAMENT_BRANCH:
        issues.append(
            tournament_contract.ValidationIssue(
                "branch",
                f"current branch must be {tournament_contract.TOURNAMENT_BRANCH}",
            )
        )

    _validate_fast_snapshot_manifest_schema(manifest, manifest_text, issues)
    canonical_manifest = (root / tournament_contract.CANONICAL_MANIFEST_PATH).resolve()
    if manifest_path.resolve() != canonical_manifest:
        issues.append(
            tournament_contract.ValidationIssue(
                "data_manifest", "fast verification requires the canonical manifest path"
            )
        )

    common_commit = freeze.get("common_freeze_commit")
    if not isinstance(common_commit, str) or not re.fullmatch(r"[0-9a-f]{40,64}", common_commit):
        issues.append(
            tournament_contract.ValidationIssue(
                "common_freeze_commit", "Phase-0 common freeze commit is invalid"
            )
        )
        common_commit = None

    sources = manifest.get("sources")
    builder_path = root / _SNAPSHOT_BUILDER_PATH
    if not isinstance(sources, Mapping):
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.sources", "snapshot manifest requires sources"
            )
        )
    elif sources.get("builder_path") != _SNAPSHOT_BUILDER_PATH:
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_builder_sha256",
                f"snapshot builder path must be {_SNAPSHOT_BUILDER_PATH}",
            )
        )

    common_paths = (
        tournament_contract.CANONICAL_MANIFEST_PATH,
        tournament_contract.CANONICAL_CONFIG_PATH,
        tournament_contract.PHASE0_POLICY_PATH,
        tournament_contract.ROOT_DEPENDENCY_LOCK_PATH,
        tournament_contract.ORCHESTRATOR_SCRIPT_PATH,
        _SNAPSHOT_BUILDER_PATH,
        *tournament_contract.EVALUATOR_SOURCE_PATHS,
        *tournament_contract.METHODOLOGY_PATHS,
    )
    unsafe_common = [
        relative
        for relative in common_paths
        if not (root / relative).is_file() or (root / relative).is_symlink()
    ]
    for relative in unsafe_common:
        issues.append(
            tournament_contract.ValidationIssue(
                "common_freeze_commit", f"frozen common file is missing/unsafe: {relative}"
            )
        )

    current_hashes: dict[str, str] = {}
    if not unsafe_common:
        current_hashes = {
            "data_manifest_sha256": _sha256_file(canonical_manifest),
            "config_sha256": _sha256_file(root / tournament_contract.CANONICAL_CONFIG_PATH),
            "phase0_policy_sha256": _sha256_file(root / tournament_contract.PHASE0_POLICY_PATH),
            "root_dependency_lock_sha256": _sha256_file(
                root / tournament_contract.ROOT_DEPENDENCY_LOCK_PATH
            ),
            "orchestrator_sha256": _sha256_file(
                root / tournament_contract.ORCHESTRATOR_SCRIPT_PATH
            ),
            "snapshot_builder_sha256": _sha256_file(builder_path),
            "evaluator_sha256": sha256_manifest(
                [root / relative for relative in tournament_contract.EVALUATOR_SOURCE_PATHS],
                root=root,
            )[0],
            "methodology_sha256": sha256_manifest(
                [root / relative for relative in tournament_contract.METHODOLOGY_PATHS],
                root=root,
            )[0],
        }
        file_entries = {
            entry.get("name"): entry
            for entry in manifest.get("files", [])
            if isinstance(entry, Mapping)
        }
        for logical_name, field in (
            ("btc_daily_returns", "btc_daily_returns_sha256"),
            ("btc_regimes", "btc_regimes_sha256"),
        ):
            entry = file_entries.get(logical_name)
            if isinstance(entry, Mapping) and isinstance(entry.get("sha256"), str):
                current_hashes[field] = str(entry["sha256"])

    for field, current_hash in current_hashes.items():
        if freeze.get(field) != current_hash:
            issues.append(
                tournament_contract.ValidationIssue(
                    field, f"current {field} differs from phase0_freeze.json"
                )
            )
    if isinstance(sources, Mapping):
        builder_sha256 = sources.get("builder_sha256")
        if builder_sha256 != current_hashes.get("snapshot_builder_sha256"):
            issues.append(
                tournament_contract.ValidationIssue(
                    "snapshot_builder_sha256",
                    "manifest builder hash differs from the current frozen builder",
                )
            )

    for field in (
        "common_freeze_commit",
        "data_manifest_sha256",
        "evaluator_sha256",
        "methodology_sha256",
        "config_sha256",
        "orchestrator_sha256",
    ):
        if state.get(field) != freeze.get(field):
            issues.append(
                tournament_contract.ValidationIssue(
                    f"run_state.{field}",
                    f"run_state {field} differs from phase0_freeze.json",
                )
            )

    if common_commit is not None:
        issues.extend(
            tournament_contract._verify_git_frozen_files(  # noqa: SLF001
                root,
                common_commit,
                common_paths,
                issue_code="common_freeze_commit",
            )
        )
        record_commit = tournament_contract._phase0_record_commit(  # noqa: SLF001
            root, common_commit, issues
        )
        if record_commit is not None:
            ancestor = subprocess.run(
                ["git", "merge-base", "--is-ancestor", record_commit, "HEAD"],
                cwd=root,
                check=False,
                capture_output=True,
            )
            if ancestor.returncode != 0:
                issues.append(
                    tournament_contract.ValidationIssue(
                        "phase0_record_commit",
                        "Phase-0 record commit must remain an ancestor of HEAD",
                    )
                )

    _raise_phase0_fast_path_issues(issues)
    return True


def _validate_fast_snapshot_manifest_schema(
    manifest: Mapping[str, Any],
    manifest_text: str,
    issues: list[tournament_contract.ValidationIssue],
) -> None:
    """Validate the canonical-file schema without touching raw-source provenance."""
    if manifest_text != json.dumps(manifest, indent=2, sort_keys=True) + "\n":
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest", "snapshot manifest is not in canonical JSON form"
            )
        )
    if manifest.get("schema_version") != 1:
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.schema_version", "snapshot schema_version must be 1"
            )
        )
    if (
        not isinstance(manifest.get("parser_version"), str)
        or not str(manifest.get("parser_version")).strip()
    ):
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.parser_version", "snapshot parser_version is required"
            )
        )
    limitations = manifest.get("limitations")
    if (
        not isinstance(limitations, list)
        or not limitations
        or not all(isinstance(item, str) and item.strip() for item in limitations)
    ):
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.limitations", "snapshot limitations must be non-empty text"
            )
        )
    window = manifest.get("window")
    if not isinstance(window, Mapping) or set(window) != {
        "warmup_start",
        "evaluation_start",
        "hard_end_exclusive",
    }:
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.window", "snapshot window schema is invalid"
            )
        )
    elif not all(isinstance(value, str) and value for value in window.values()):
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.window", "snapshot window values must be timestamps"
            )
        )

    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.files", "snapshot manifest requires canonical files"
            )
        )
        return
    names: list[str] = []
    paths: list[str] = []
    for index, entry in enumerate(files):
        if not isinstance(entry, Mapping) or set(entry) != {
            "name",
            "path",
            "rows",
            "sha256",
            "size",
        }:
            issues.append(
                tournament_contract.ValidationIssue(
                    f"snapshot_manifest.files.{index}",
                    "canonical file entry schema is invalid",
                )
            )
            continue
        name = entry.get("name")
        path = entry.get("path")
        rows = entry.get("rows")
        if not isinstance(name, str) or not name:
            issues.append(
                tournament_contract.ValidationIssue(
                    f"snapshot_manifest.files.{index}.name", "logical name is invalid"
                )
            )
        else:
            names.append(name)
        if not isinstance(path, str) or not path:
            issues.append(
                tournament_contract.ValidationIssue(
                    f"snapshot_manifest.files.{index}.path", "canonical path is invalid"
                )
            )
        else:
            paths.append(path)
        if isinstance(rows, bool) or not isinstance(rows, int) or rows < 0:
            issues.append(
                tournament_contract.ValidationIssue(
                    f"snapshot_manifest.files.{index}.rows", "row count is invalid"
                )
            )
    if frozenset(names) != _CANONICAL_SNAPSHOT_NAMES or len(names) != len(set(names)):
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.files", "canonical logical names are incomplete or duplicated"
            )
        )
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        issues.append(
            tournament_contract.ValidationIssue(
                "snapshot_manifest.files", "canonical paths must be unique and sorted"
            )
        )


def _raise_phase0_fast_path_issues(
    issues: Sequence[tournament_contract.ValidationIssue],
) -> None:
    if not issues:
        return
    details = "; ".join(f"{issue.code}: {issue.message}" for issue in issues[:8])
    if len(issues) > 8:
        details += f"; plus {len(issues) - 8} more issue(s)"
    raise ValueError(f"invalid Phase-0 snapshot binding: {details}")


def _verify_snapshot_files_unchanged(snapshot: _SnapshotData) -> None:
    """Rehash every manifest-listed file after team code and before publication."""
    for path, expected_sha256 in sorted(
        snapshot.file_hashes.items(), key=lambda item: item[0].as_posix()
    ):
        if not path.is_file():
            raise ValueError(f"snapshot file disappeared during team run: {path}")
        actual_sha256 = _sha256_file(path)
        if actual_sha256 != expected_sha256:
            raise ValueError(f"snapshot file changed during team run: {path}")


def _invoke_snapshot_verifier(root: Path, manifest_path: Path) -> None:
    """Call the Phase-0 verifier when its module is installed, without fixing its signature."""
    module_name = "crypto_trade.tournament.snapshot"
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return
        raise
    verifier = getattr(module, "verify_snapshot_manifest", None)
    if verifier is None:
        return
    if not callable(verifier):
        raise TypeError("snapshot.verify_snapshot_manifest is not callable")
    signature = inspect.signature(verifier)
    candidates = (
        ((), {"root": root, "manifest_path": manifest_path}),
        ((manifest_path,), {"root": root}),
        ((root, manifest_path), {}),
        ((manifest_path,), {}),
    )
    for args, kwargs in candidates:
        try:
            signature.bind(*args, **kwargs)
        except TypeError:
            continue
        result = verifier(*args, **kwargs)
        if result is False:
            raise ValueError("snapshot verifier rejected the manifest")
        if isinstance(result, Mapping) and result.get("valid") is False:
            raise ValueError("snapshot verifier rejected the manifest")
        if hasattr(result, "valid") and getattr(result, "valid") is False:
            raise ValueError("snapshot verifier rejected the manifest")
        return
    raise TypeError("unsupported verify_snapshot_manifest signature")


def _resolve_dataset_entry(
    logical_name: str, entries: list[tuple[Mapping[str, Any], Path]]
) -> Path:
    explicit: list[Path] = []
    for entry, path in entries:
        values = (entry.get("dataset"), entry.get("name"))
        if any(_normalise_dataset_name(value) == logical_name for value in values):
            explicit.append(path)
    if len(explicit) > 1:
        raise ValueError(f"ambiguous explicit snapshot dataset: {logical_name}")
    if explicit:
        selected = explicit[0]
    else:
        basename = _DATASET_BASENAMES[logical_name]
        matches = [path for _, path in entries if path.name == basename]
        if len(matches) != 1:
            qualifier = "missing" if not matches else "ambiguous"
            raise ValueError(f"{qualifier} snapshot dataset: {logical_name}")
        selected = matches[0]
    if selected.suffix.lower() != ".parquet":
        raise ValueError(f"snapshot dataset {logical_name} must be Parquet")
    return selected


def _normalise_dataset_name(value: Any) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    name = PurePosixPath(value).name.lower()
    if name.endswith(".parquet"):
        name = name[: -len(".parquet")]
    return name.replace("-", "_")


def _validate_snapshot_bounds(
    snapshot: _SnapshotData,
    config: Mapping[str, Any],
    decision_times: pd.DatetimeIndex,
) -> None:
    bars = snapshot.bars
    funding = snapshot.funding
    mark_prices = snapshot.mark_prices
    membership = snapshot.membership
    required_bars = {"open_time", "symbol", "open", "close", "quote_volume"}
    required_funding = {"funding_time", "symbol", "funding_rate", "mark_price"}
    required_mark_prices = {"mark_time", "symbol", "mark_price"}
    required_membership = {
        "reconstitution_time",
        "symbol",
        "liquidity_rank",
        "trailing_quote_volume",
    }
    for name, frame, required in (
        ("bars", bars, required_bars),
        ("funding", funding, required_funding),
        ("mark_prices", mark_prices, required_mark_prices),
        ("membership", membership, required_membership),
    ):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"snapshot {name} missing columns: {sorted(missing)}")
    if snapshot.contract_metadata.empty:
        raise ValueError("snapshot contract_metadata cannot be empty")

    bar_times = pd.to_datetime(bars["open_time"], utc=True, errors="raise")
    funding_times = pd.to_datetime(funding["funding_time"], utc=True, errors="raise")
    mark_times = pd.to_datetime(mark_prices["mark_time"], utc=True, errors="raise")
    membership_times = pd.to_datetime(membership["reconstitution_time"], utc=True, errors="raise")
    if (bar_times >= _END_EXCLUSIVE).any():
        raise ValueError("snapshot bars cross the hard end-exclusive boundary")
    if (funding_times >= _END_EXCLUSIVE).any():
        raise ValueError("snapshot funding crosses the hard end-exclusive boundary")
    if (mark_times >= _END_EXCLUSIVE).any():
        raise ValueError("snapshot mark prices cross the hard end-exclusive boundary")
    if (membership_times >= _END_EXCLUSIVE).any():
        raise ValueError("snapshot membership crosses the hard end-exclusive boundary")
    if mark_prices.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("snapshot mark prices contain duplicate boundaries")
    aligned_marks = (
        (mark_times.dt.minute == 0)
        & (mark_times.dt.second == 0)
        & (mark_times.dt.microsecond == 0)
        & (mark_times.dt.hour % 8 == 0)
    )
    if not aligned_marks.all():
        raise ValueError("snapshot mark prices must be exact 8h UTC boundaries")
    numeric_marks = pd.to_numeric(mark_prices["mark_price"], errors="raise")
    if not np.isfinite(numeric_marks.to_numpy()).all() or (numeric_marks <= 0.0).any():
        raise ValueError("snapshot mark prices must be finite and positive")
    available_bar_times = pd.DatetimeIndex(bar_times.unique()).sort_values()
    missing_decisions = decision_times.difference(available_bar_times)
    if len(missing_decisions):
        raise ValueError(
            f"snapshot has {len(missing_decisions)} decision timestamps without any bar open"
        )

    warmup_start = pd.Timestamp(config["data"]["warmup_start"], tz="UTC")
    expected_btc_times = pd.date_range(
        warmup_start, _END_EXCLUSIVE, freq=_INTERVAL, inclusive="left"
    )
    btc_times = pd.DatetimeIndex(
        bar_times.loc[bars["symbol"].astype(str).eq("BTCUSDT")]
    ).sort_values()
    if btc_times.duplicated().any() or not btc_times.equals(expected_btc_times):
        raise ValueError("BTCUSDT must have one complete 8h bar grid from warmup through cutoff")


def _canonical_targets(
    raw: pd.DataFrame, bars: pd.DataFrame, decision_times: pd.DatetimeIndex
) -> pd.DataFrame:
    if not isinstance(raw, pd.DataFrame):
        raise TypeError("generate_targets must return a DataFrame")
    targets = raw.copy()
    targets.index = pd.to_datetime(targets.index, utc=True)
    if targets.index.duplicated().any() or not targets.index.equals(decision_times):
        raise ValueError("strategy targets must contain exactly the canonical 8h decision grid")
    if targets.columns.duplicated().any():
        raise ValueError("strategy targets contain duplicate symbols")
    bar_symbols = set(bars["symbol"].astype(str))
    if REBALANCE_INSTRUCTION_COLUMN in bar_symbols:
        raise ValueError("bars contain the reserved rebalance instruction symbol")
    targets.columns = [str(name) for name in targets.columns]
    if targets.columns.duplicated().any():
        raise ValueError("strategy targets contain duplicate symbols after normalization")
    if REBALANCE_INSTRUCTION_COLUMN in targets:
        instructions = targets.pop(REBALANCE_INSTRUCTION_COLUMN)
        if instructions.isna().any() or not pd.api.types.is_bool_dtype(instructions.dtype):
            raise ValueError("strategy rebalance instructions must be Boolean")
        instructions = instructions.astype(bool)
    else:
        # Compatibility for direct/focused generators; canonical artifacts always gain the flag.
        instructions = pd.Series(True, index=targets.index, dtype=bool)
    columns = sorted(bar_symbols | {str(name) for name in targets.columns})
    targets = targets.reindex(columns=columns, fill_value=0.0)
    targets = targets.apply(pd.to_numeric, errors="raise").astype(float)
    if not np.isfinite(targets.to_numpy()).all():
        raise ValueError("strategy targets contain NaN or infinite values")
    targets.insert(0, REBALANCE_INSTRUCTION_COLUMN, instructions.to_numpy(dtype=bool))
    targets.index.name = "timestamp"
    return targets


def _validate_evaluation_grids(
    base: EvaluationResult,
    stressed: EvaluationResult,
    decision_times: pd.DatetimeIndex,
) -> None:
    for label, result in (("base", base), ("double-cost", stressed)):
        if not isinstance(result, EvaluationResult):
            raise TypeError(f"{label} evaluator did not return EvaluationResult")
        for artifact_name, frame in (
            ("returns", result.returns),
            ("positions", result.positions),
        ):
            index = pd.DatetimeIndex(pd.to_datetime(frame.index, utc=True))
            if index.duplicated().any() or not index.equals(decision_times):
                raise ValueError(
                    f"{label} {artifact_name} must contain exactly the canonical 8h grid"
                )


def _canonical_daily_returns(returns: pd.DataFrame, label: str) -> pd.Series:
    if "net_return" not in returns:
        raise ValueError(f"{label} evaluator returns are missing net_return")
    daily = aggregate_daily_returns(returns["net_return"])
    expected = pd.date_range(IS_START, OOS_END, freq="1D", tz="UTC")
    if not daily.index.equals(expected):
        raise ValueError(f"{label} daily returns do not cover the canonical daily grid")
    return daily


def _btc_daily_returns(bars: pd.DataFrame, config: Mapping[str, Any]) -> pd.Series:
    btc = bars.loc[bars["symbol"].astype(str).eq("BTCUSDT"), ["open_time", "close"]].copy()
    btc["open_time"] = pd.to_datetime(btc["open_time"], utc=True)
    btc["close"] = pd.to_numeric(btc["close"], errors="raise")
    btc = btc.sort_values("open_time").set_index("open_time")
    daily_close = btc["close"].resample("1D").last()
    if daily_close.isna().any() or (daily_close <= 0.0).any():
        raise ValueError("BTCUSDT daily closes are incomplete or invalid")
    returns = daily_close.pct_change(fill_method=None).dropna().rename("btc_return")
    expected = pd.date_range(IS_START, OOS_END, freq="1D", tz="UTC")
    scored = returns.reindex(expected)
    if scored.isna().any():
        raise ValueError("BTCUSDT daily returns do not cover the scored period")
    warmup_start = pd.Timestamp(config["data"]["warmup_start"], tz="UTC")
    oos_end = pd.Timestamp(OOS_END, tz="UTC")
    return returns.loc[warmup_start:oos_end]


def _compute_metrics(
    base_daily: pd.Series,
    stressed_daily: pd.Series,
    btc_daily: pd.Series,
    config: Mapping[str, Any],
) -> dict[str, Any]:
    is_returns = base_daily.loc[IS_START:IS_END]
    oos_returns = base_daily.loc[OOS_START:OOS_END]
    stressed_oos = stressed_daily.loc[OOS_START:OOS_END]
    labels = classify_btc_regimes(btc_daily).loc[OOS_START:OOS_END]
    if labels.isna().any() or not labels.index.equals(oos_returns.index):
        raise ValueError("BTC regime labels do not cover the exact public-OOS grid")
    statistics = config["statistics"]
    interval_kwargs = {
        "samples": int(statistics["bootstrap_samples"]),
        "block_days": int(statistics["bootstrap_block_days"]),
        "seed": int(statistics["bootstrap_seed"]),
    }
    return {
        "in_sample": EvaluationWindow(IS_START, IS_END, compute_window_metrics(is_returns)),
        "public_oos": EvaluationWindow(OOS_START, OOS_END, compute_window_metrics(oos_returns)),
        "double_cost_oos_sharpe": compute_window_metrics(stressed_oos).net_sharpe,
        "regime_sharpe": dict(compute_regime_sharpes(oos_returns, labels)),
        "confidence_intervals": {
            "is_net_sharpe_95": sharpe_confidence_interval(is_returns, **interval_kwargs),
            "public_oos_net_sharpe_95": sharpe_confidence_interval(oos_returns, **interval_kwargs),
            "double_cost_oos_net_sharpe_95": sharpe_confidence_interval(
                stressed_oos, **interval_kwargs
            ),
        },
    }


def _publish_artifacts(
    root: Path,
    team_id: str,
    *,
    targets: pd.DataFrame,
    base: EvaluationResult,
    stressed: EvaluationResult,
    base_daily: pd.Series,
    stressed_daily: pd.Series,
) -> dict[str, str]:
    report_parent = (root / "reports-top40").resolve()
    if not report_parent.is_relative_to(root):
        raise ValueError("report directory escapes tournament root")
    report_parent.mkdir(parents=True, exist_ok=True)
    output_dir = report_parent / team_id
    if output_dir.is_symlink():
        raise ValueError("team report directory cannot be a symlink")
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("team report path must be a directory")
    staging = Path(tempfile.mkdtemp(prefix=f".{team_id}-", dir=report_parent))
    files = {
        "targets": "targets.parquet",
        "events": "events.parquet",
        "positions": "positions.parquet",
        "evaluator_returns": "bar_returns.csv",
        "double_cost_evaluator_returns": "double_cost_bar_returns.csv",
        "daily_returns": "daily_returns.csv",
        "double_cost_daily_returns": "double_cost_daily_returns.csv",
        "trades": "trades.csv",
    }
    try:
        _write_parquet(_indexed_frame(targets, "timestamp"), staging / files["targets"])
        events = _canonical_events(base.events)
        _write_parquet(events, staging / files["events"])
        _write_parquet(_indexed_frame(base.positions, "timestamp"), staging / files["positions"])
        _write_csv(
            _indexed_frame(base.returns, "timestamp"),
            staging / files["evaluator_returns"],
        )
        _write_csv(
            _indexed_frame(stressed.returns, "timestamp"),
            staging / files["double_cost_evaluator_returns"],
        )
        _write_csv(
            pd.DataFrame({"date": base_daily.index, "net_return": base_daily.to_numpy()}),
            staging / files["daily_returns"],
        )
        _write_csv(
            pd.DataFrame({"date": stressed_daily.index, "net_return": stressed_daily.to_numpy()}),
            staging / files["double_cost_daily_returns"],
        )
        _write_csv(_trade_events(events), staging / files["trades"])
        _promote_report_directory(staging, output_dir)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return {name: f"reports-top40/{team_id}/{filename}" for name, filename in files.items()}


def _indexed_frame(frame: pd.DataFrame, index_name: str) -> pd.DataFrame:
    result = frame.copy()
    result.index = pd.to_datetime(result.index, utc=True)
    result = result.sort_index()
    result.index.name = index_name
    return result.reset_index()


def _canonical_events(events: pd.DataFrame) -> pd.DataFrame:
    frame = events.copy()
    for column in _EVENT_COLUMNS:
        if column not in frame:
            dtype = "datetime64[ns, UTC]" if column == "timestamp" else object
            frame[column] = pd.Series(dtype=dtype)
    frame = frame.loc[:, _EVENT_COLUMNS]
    if not frame.empty:
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
        frame = frame.sort_values(
            ["timestamp", "symbol", "event_type", "phase"], kind="mergesort"
        ).reset_index(drop=True)
    return frame


def _trade_events(events: pd.DataFrame) -> pd.DataFrame:
    frame = _canonical_events(events)
    return frame.loc[frame["event_type"].isin(_TRADE_EVENT_TYPES)].reset_index(drop=True)


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    frame.to_parquet(path, engine="pyarrow", compression="zstd", index=False)


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    output = frame.copy()
    for column in output.columns:
        if isinstance(output[column].dtype, pd.DatetimeTZDtype) or pd.api.types.is_datetime64_dtype(
            output[column].dtype
        ):
            timestamps = pd.to_datetime(output[column], utc=True)
            if column == "date":
                output[column] = timestamps.dt.strftime("%Y-%m-%d")
            else:
                output[column] = timestamps.dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    output.to_csv(path, index=False, lineterminator="\n", float_format="%.17g")


def _promote_report_directory(staging: Path, output_dir: Path) -> None:
    if not output_dir.exists():
        os.replace(staging, output_dir)
        return
    backup = output_dir.parent / f".{output_dir.name}-backup"
    if backup.exists():
        raise FileExistsError(f"stale report backup exists: {backup}")
    os.replace(output_dir, backup)
    try:
        os.replace(staging, output_dir)
    except BaseException:
        os.replace(backup, output_dir)
        raise
    shutil.rmtree(backup)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
