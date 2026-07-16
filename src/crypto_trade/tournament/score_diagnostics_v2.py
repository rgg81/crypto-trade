"""Organizer-private score diagnostics for Top-40 V2 amendment 0001.

This module does not alter tournament targets, returns, qualification, or team research budgets.
It reconstructs the exact source tree present at preregistration, runs two clean sandboxed target
replays, proves exact equality with the completed candidate's target artifact, calculates the
frozen cross-sectional score diagnostic, and publishes numeric evidence only below an owner-only
Git administrative path.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import io
import json
import math
import os
import re
import resource
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO

import numpy as np
import pandas as pd

from crypto_trade.tournament import runner_v2
from crypto_trade.tournament.amendment_integrity_v2 import (
    MAX_PRIVATE_ARTIFACT_BYTES,
    MAX_PRIVATE_RESULT_BYTES,
    PRIVATE_ARTIFACT_GIT_PATH,
    atomic_write_bytes,
    ensure_owner_directory,
    fsync_directory,
    git_path,
    read_repo_file,
    safe_relative,
    sha256_bytes,
    strict_json_object,
    unique_first_add_commit,
    validate_private_artifacts,
)
from crypto_trade.tournament.engine_v2 import (
    _normalise_bars,
    _normalise_funding,
    generate_targets,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN
from crypto_trade.tournament.research_v2 import build_trial_registration
from crypto_trade.tournament.score_adapters.team01_rdf_v1 import ADAPTER_ID, FAMILY_ID
from crypto_trade.tournament.top40_v2 import LoadedV2Config
from crypto_trade.tournament.top40_v2 import load_config as load_v2_config

DIAGNOSTIC_SPEC_ID = "top40-v2-organizer-private-score-diagnostic-v1"
LABEL_ID = "next-daily-executable-open-to-open-simple-return-v1"
IC_ID = "mean-daily-cross-sectional-spearman-average-ties-v1"

FOLDS = (
    ("F1", "2020-02-03T00:00:00Z", "2020-09-01T00:00:00Z"),
    ("F2", "2020-09-01T00:00:00Z", "2021-04-01T00:00:00Z"),
    ("F3", "2021-04-01T00:00:00Z", "2021-11-01T00:00:00Z"),
    ("F4", "2021-11-01T00:00:00Z", "2022-06-01T00:00:00Z"),
    ("F5", "2022-06-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    ("F6", "2023-01-01T00:00:00Z", "2023-07-01T00:00:00Z"),
)

REQUIRED_PRIVATE_ARTIFACT_NAMES = tuple(
    sorted(
        (
            "diagnostic-summary.json",
            "labeled-score-panel.parquet",
            "replay-1-scores.parquet",
            "replay-1-targets.parquet",
            "replay-2-scores.parquet",
            "replay-2-targets.parquet",
        )
    )
)

_SHA256 = re.compile(r"[0-9a-f]{64}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_INTERVAL = pd.Timedelta(hours=8)
_LABEL_HORIZON = pd.Timedelta(hours=24)


@dataclasses.dataclass(frozen=True)
class ScoreDiagnosticRequest:
    """All public/hash-only authority supplied by the amendment reservation."""

    diagnostic_id: str
    team_id: str
    family_id: str
    candidate_id: str
    registration_sha256: str
    strategy_sha256: str
    risk_policy_sha256: str
    source_bundle_sha256: str
    candidate_seed: int
    config_sha256: str
    snapshot_manifest_path: str
    snapshot_manifest_sha256: str
    development_target_path: str
    development_target_sha256: str
    runner_record_path: str
    runner_record_sha256: str
    score_adapter_id: str = ADAPTER_ID


@dataclasses.dataclass(frozen=True)
class HistoricalSourceBinding:
    registration_input_path: str
    registration_commit: str
    strategy_sha256: str
    risk_policy_sha256: str
    source_bundle_sha256: str
    source_tree_manifest_sha256: str


@dataclasses.dataclass(frozen=True)
class ScoreDiagnosticOutcome:
    """Internal publication result; the lifecycle API does not disclose it."""

    diagnostic_id: str
    team_id: str
    candidate_id: str
    artifact_hashes: Mapping[str, str]
    historical_source_commit: str


@dataclasses.dataclass(frozen=True)
class _MaterializedSource:
    binding: HistoricalSourceBinding
    team_root: Path
    entrypoint: Path
    registration: Mapping[str, Any]


@dataclasses.dataclass(frozen=True)
class _Replay:
    targets: pd.DataFrame
    scores: pd.DataFrame


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _pretty_json_bytes(value: object) -> bytes:
    return json.dumps(value, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _require_sha(value: object, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase SHA-256")
    return value


def _request_paths(request: ScoreDiagnosticRequest) -> tuple[str, str, str]:
    if _SAFE_ID.fullmatch(request.diagnostic_id) is None:
        raise ValueError("diagnostic_id is unsafe")
    TOP40_V2_LAYOUT.require_team(request.team_id)
    if _SAFE_ID.fullmatch(request.candidate_id) is None:
        raise ValueError("candidate_id is unsafe")
    if request.team_id != "team-01" or request.family_id != FAMILY_ID:
        raise ValueError("amendment 0001 score adapter supports only Team01 RDF")
    if request.score_adapter_id != ADAPTER_ID:
        raise ValueError("diagnostic request names an unreviewed score adapter")
    for value, label in (
        (request.registration_sha256, "registration_sha256"),
        (request.strategy_sha256, "strategy_sha256"),
        (request.risk_policy_sha256, "risk_policy_sha256"),
        (request.source_bundle_sha256, "source_bundle_sha256"),
        (request.config_sha256, "config_sha256"),
        (request.snapshot_manifest_sha256, "snapshot_manifest_sha256"),
        (request.development_target_sha256, "development_target_sha256"),
        (request.runner_record_sha256, "runner_record_sha256"),
    ):
        _require_sha(value, label)
    if isinstance(request.candidate_seed, bool) or not isinstance(request.candidate_seed, int):
        raise ValueError("candidate_seed must be an integer")
    if not 0 <= request.candidate_seed <= 2**32 - 1:
        raise ValueError("candidate_seed is outside the canonical worker seed range")
    registration_path = (
        f"{TOP40_V2_LAYOUT.report_root(request.team_id)}/registration-inputs/"
        f"{request.candidate_id}.json"
    )
    target_path = (
        f"{TOP40_V2_LAYOUT.report_root(request.team_id)}/development-runs/"
        f"{request.candidate_id}/targets.parquet"
    )
    runner_path = (
        f"{TOP40_V2_LAYOUT.report_root(request.team_id)}/qualification-attempts/"
        f"{request.candidate_id}.runner-record.json"
    )
    if request.development_target_path != target_path:
        raise ValueError("diagnostic target path is not the completed candidate archive")
    if request.runner_record_path != runner_path:
        raise ValueError("diagnostic runner-record path is noncanonical")
    safe_relative(request.snapshot_manifest_path, "snapshot manifest path")
    return registration_path, target_path, runner_path


def _git(root: Path, *arguments: str, label: str) -> bytes:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if result.returncode:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"{label} failed: {detail or 'unknown Git error'}")
    return result.stdout


def _materialize_team_tree(root: Path, commit: str, team_id: str, destination: Path) -> None:
    if _COMMIT.fullmatch(commit) is None:
        raise ValueError("historical source commit is invalid")
    prefix = TOP40_V2_LAYOUT.team_root(team_id)
    raw = _git(
        root,
        "ls-tree",
        "-r",
        "-z",
        "--full-tree",
        commit,
        "--",
        prefix,
        label="historical team tree listing",
    )
    records = [item for item in raw.split(b"\0") if item]
    if not records:
        raise ValueError("registration commit contains no historical team tree")
    observed: set[str] = set()
    destination.mkdir(mode=0o700, parents=True, exist_ok=False)
    for record in records:
        try:
            header, raw_path = record.split(b"\t", 1)
            mode, object_type, object_id = header.decode("ascii").split()
            path_text = raw_path.decode("utf-8", errors="strict")
        except (UnicodeError, ValueError) as exc:
            raise ValueError("historical team tree contains a malformed entry") from exc
        expected_prefix = prefix + "/"
        if object_type != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("historical team tree contains a non-regular Git entry")
        if not path_text.startswith(expected_prefix):
            raise ValueError("historical team tree entry escapes its namespace")
        relative = PurePosixPath(path_text.removeprefix(expected_prefix))
        if (
            relative.is_absolute()
            or any(part in {"", ".", ".."} for part in relative.parts)
            or relative.as_posix() in observed
        ):
            raise ValueError("historical team tree contains an unsafe or duplicate path")
        observed.add(relative.as_posix())
        payload = _git(root, "cat-file", "blob", object_id, label="historical source blob")
        target = destination.joinpath(*relative.parts)
        target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        descriptor = os.open(
            target,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
        try:
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                view = view[written:]
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


@contextlib.contextmanager
def materialized_historical_source(
    root: str | Path,
    config: LoadedV2Config,
    request: ScoreDiagnosticRequest,
) -> Iterator[_MaterializedSource]:
    """Reconstruct and verify the exact team tree present at preregistration."""

    root_path = Path(root).resolve()
    registration_path, _target_path, _runner_path = _request_paths(request)
    if config.sha256 != request.config_sha256:
        raise ValueError("diagnostic request differs from the frozen config")
    _relative, _path, registration_bytes, _stat = read_repo_file(
        root_path,
        registration_path,
        "historical registration input",
        maximum_bytes=1024 * 1024,
        require_single_link=True,
    )
    registration_raw = strict_json_object(registration_bytes, "historical registration input")
    try:
        registration_line = build_trial_registration(**dict(registration_raw))
    except TypeError as exc:
        raise ValueError("historical registration input has unexpected fields") from exc
    if sha256_bytes(registration_line) != request.registration_sha256:
        raise ValueError("historical registration input differs from its journal SHA-256")
    registration = json.loads(registration_line)
    expected_identity = {
        "team_id": request.team_id,
        "family_id": request.family_id,
        "candidate_id": request.candidate_id,
        "config_sha256": request.config_sha256,
    }
    if any(registration[field] != value for field, value in expected_identity.items()):
        raise ValueError("historical registration identity differs from the reservation")
    expected_registration_bindings = {
        "strategy_sha256": request.strategy_sha256,
        "risk_config_sha256": request.risk_policy_sha256,
        "source_bundle_sha256": request.source_bundle_sha256,
        "seed": request.candidate_seed,
    }
    if any(
        registration[field] != value
        for field, value in expected_registration_bindings.items()
    ):
        raise ValueError("historical registration hashes or seed differ from the reservation")
    registration_commit = unique_first_add_commit(
        root_path,
        registration_path,
        registration_bytes,
    )

    with tempfile.TemporaryDirectory(prefix=f"top40-v2-score-source-{request.team_id}-") as raw:
        temporary = Path(raw)
        team_root = temporary / "team"
        _materialize_team_tree(root_path, registration_commit, request.team_id, team_root)
        entrypoint = team_root / "strategy.py"
        risk_path = team_root / "risk_policy.json"
        if not entrypoint.is_file() or entrypoint.is_symlink():
            raise ValueError("historical source tree lacks a safe strategy.py")
        if not risk_path.is_file() or risk_path.is_symlink():
            raise ValueError("historical source tree lacks a safe risk_policy.json")
        files = runner_v2._team_tree_files(team_root)
        source_bundle = runner_v2._team_tree_fingerprint(files)
        entries = [
            {"path": item.relative, "sha256": item.sha256, "size": item.size}
            for item in files
        ]
        strategy_sha = sha256_bytes(runner_v2._stable_file_bytes(entrypoint))
        risk_sha = sha256_bytes(runner_v2._stable_file_bytes(risk_path))
        if (
            strategy_sha != registration["strategy_sha256"]
            or risk_sha != registration["risk_config_sha256"]
            or source_bundle != registration["source_bundle_sha256"]
        ):
            raise ValueError("registration commit does not reconstruct the registered source")
        binding = HistoricalSourceBinding(
            registration_input_path=registration_path,
            registration_commit=registration_commit,
            strategy_sha256=strategy_sha,
            risk_policy_sha256=risk_sha,
            source_bundle_sha256=source_bundle,
            source_tree_manifest_sha256=sha256_bytes(_canonical_json_bytes(entries)),
        )
        yield _MaterializedSource(binding, team_root, entrypoint, registration)


class _CapturingClient:
    """Translate the score-worker extension back into the frozen target proxy protocol."""

    def __init__(self, client: Any, *, adapter_id: str) -> None:
        self._client = client
        self._adapter_id = adapter_id
        self.captured: dict[pd.Timestamp, Mapping[str, float] | None] = {}

    def initialise(self, payload: Mapping[str, Any]) -> None:
        request = dict(payload)
        request["score_adapter_id"] = self._adapter_id
        self._client.initialise(request)

    def request(self, payload: Mapping[str, Any]) -> Mapping[str, Any]:
        response = self._client.request(payload)
        if payload.get("type") != "decision":
            return response
        if response.get("type") != "score_result" or "weights" not in response:
            raise runner_v2.StrategySandboxError("score worker returned an invalid response")
        timestamp = pd.Timestamp(payload["decision_time"])
        timestamp = (
            timestamp.tz_localize("UTC")
            if timestamp.tzinfo is None
            else timestamp.tz_convert("UTC")
        )
        if timestamp in self.captured:
            raise runner_v2.StrategySandboxError("score worker replayed a decision")
        eligible = payload.get("eligible_symbols")
        if not isinstance(eligible, list) or any(not isinstance(item, str) for item in eligible):
            raise runner_v2.StrategySandboxError("score worker received invalid eligibility")
        raw_scores = response.get("scores")
        if raw_scores is None:
            scores = None
        else:
            if not isinstance(raw_scores, Mapping) or not raw_scores:
                raise runner_v2.StrategySandboxError("score worker returned invalid scores")
            scores = {}
            for symbol, raw_score in raw_scores.items():
                if (
                    not isinstance(symbol, str)
                    or symbol not in eligible
                    or symbol == "BTCUSDT"
                    or isinstance(raw_score, bool)
                ):
                    raise runner_v2.StrategySandboxError("score worker returned an invalid symbol")
                try:
                    score = float(raw_score)
                except (TypeError, ValueError) as exc:
                    raise runner_v2.StrategySandboxError(
                        "score worker returned a nonnumeric score"
                    ) from exc
                if not math.isfinite(score):
                    raise runner_v2.StrategySandboxError("score worker returned a nonfinite score")
                scores[symbol] = score
            if timestamp.hour != 0 or timestamp.minute or timestamp.second:
                raise runner_v2.StrategySandboxError(
                    "Team01 score worker emitted scores outside 00:00 UTC"
                )
        self.captured[timestamp] = scores
        return {"type": "weights", "weights": response["weights"]}

    def finish(self) -> None:
        self._client.finish()

    def abort(self) -> None:
        self._client.abort()


def _score_worker_command(
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
        raise runner_v2.StrategySandboxError("score diagnostics require Linux namespaces")
    unshare = shutil.which("unshare")
    if unshare is None:
        raise runner_v2.StrategySandboxError("unshare is unavailable")
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
        "crypto_trade.tournament._score_worker_v2",
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


def _launch_score_worker(
    root: Path,
    source: _MaterializedSource,
    *,
    seed: int,
    adapter_id: str,
) -> tuple[_CapturingClient, tempfile.TemporaryDirectory[str]]:
    repository_parent = runner_v2._runner_repository_parent()
    site_packages = runner_v2._current_venv_site_packages(repository_parent)
    sandbox = tempfile.TemporaryDirectory(prefix="top40-v2-score-worker-")
    sandbox_root = Path(sandbox.name)
    bundle = sandbox_root / "bundle"
    runtime = sandbox_root / "runtime-site-packages"
    empty_dir = sandbox_root / "empty-dir"
    empty_file = sandbox_root / "empty-file"
    diagnostics: BinaryIO | None = None
    runtime.mkdir()
    empty_dir.mkdir()
    empty_file.touch()
    try:
        runner_v2._copy_team_source_bundle(
            source.team_root,
            bundle,
            expected_fingerprint=source.binding.source_bundle_sha256,
        )
        command = _score_worker_command(
            root,
            repository_parent,
            bundle,
            site_packages,
            runtime,
            source.entrypoint.relative_to(source.team_root).as_posix(),
            empty_dir,
            empty_file,
        )
        diagnostics = tempfile.TemporaryFile(mode="w+b")
        process = subprocess.Popen(
            command,
            cwd=sandbox_root,
            env=runner_v2._strategy_worker_environment(seed),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=diagnostics,
            text=True,
            bufsize=1,
            close_fds=True,
            start_new_session=True,
        )
        client = runner_v2._StrategyWorkerClient(process, diagnostics)
        diagnostics = None
        return _CapturingClient(client, adapter_id=adapter_id), sandbox
    except BaseException:
        if diagnostics is not None:
            diagnostics.close()
        sandbox.cleanup()
        raise


def _score_frame(
    captured: Mapping[pd.Timestamp, Mapping[str, float] | None],
    decision_times: pd.DatetimeIndex,
) -> pd.DataFrame:
    if set(captured) != set(decision_times):
        raise ValueError("score worker did not return every canonical decision")
    rows: list[dict[str, object]] = []
    for timestamp in decision_times:
        scores = captured[pd.Timestamp(timestamp)]
        if scores is None:
            continue
        for symbol in sorted(scores):
            rows.append(
                {"decision_time": timestamp, "symbol": symbol, "score": scores[symbol]}
            )
    frame = pd.DataFrame(rows, columns=("decision_time", "symbol", "score"))
    if frame.empty:
        raise ValueError("score replay produced no pre-construction scores")
    frame["decision_time"] = pd.to_datetime(frame["decision_time"], utc=True)
    frame["symbol"] = frame["symbol"].astype(str)
    frame["score"] = pd.to_numeric(frame["score"], errors="raise").astype(float)
    if frame.duplicated(["decision_time", "symbol"]).any():
        raise ValueError("score replay contains duplicate decision-symbol rows")
    return frame.sort_values(["decision_time", "symbol"]).reset_index(drop=True)


def _run_replay(
    root: Path,
    source: _MaterializedSource,
    *,
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    decision_times: pd.DatetimeIndex,
    seed: int,
    adapter_id: str,
) -> _Replay:
    client, sandbox = _launch_score_worker(root, source, seed=seed, adapter_id=adapter_id)
    try:
        canonical_bars = _normalise_bars(bars)
        canonical_funding = _normalise_funding(funding)
        proxy = runner_v2._WorkerStrategyProxy(
            client,
            seed=seed,
            interval_hours=8,
            bar_schema=canonical_bars.iloc[0:0],
            funding_schema=canonical_funding.iloc[0:0],
            bar_history=canonical_bars,
            funding_history=canonical_funding,
        )
        raw_targets = generate_targets(
            proxy,
            bars,
            funding,
            membership,
            decision_times,
            seed=seed,
            interval_hours=8,
        )
        targets = runner_v2._canonical_targets(raw_targets, bars, decision_times)
        scores = _score_frame(client.captured, decision_times)
    except BaseException:
        client.abort()
        raise
    else:
        client.finish()
        return _Replay(targets=targets, scores=scores)
    finally:
        sandbox.cleanup()


def _target_frame_from_bytes(
    payload: bytes,
    bars: pd.DataFrame,
    decision_times: pd.DatetimeIndex,
) -> pd.DataFrame:
    try:
        frame = pd.read_parquet(io.BytesIO(payload))
    except Exception as exc:
        raise ValueError("canonical development target artifact is invalid Parquet") from exc
    if "timestamp" not in frame:
        raise ValueError("canonical development target artifact lacks timestamp")
    frame = frame.set_index("timestamp")
    return runner_v2._canonical_targets(frame, bars, decision_times)


def _targets_exact(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    if not left.index.equals(right.index) or list(left.columns) != list(right.columns):
        return False
    if not np.array_equal(
        left[REBALANCE_INSTRUCTION_COLUMN].to_numpy(dtype=bool),
        right[REBALANCE_INSTRUCTION_COLUMN].to_numpy(dtype=bool),
    ):
        return False
    columns = [name for name in left.columns if name != REBALANCE_INSTRUCTION_COLUMN]
    left_values = left.loc[:, columns].to_numpy(dtype="<f8", copy=True).view("<u8")
    right_values = right.loc[:, columns].to_numpy(dtype="<f8", copy=True).view("<u8")
    return bool(np.array_equal(left_values, right_values))


def _scores_exact(left: pd.DataFrame, right: pd.DataFrame) -> bool:
    if list(left.columns) != list(right.columns) or len(left) != len(right):
        return False
    if not pd.DatetimeIndex(left["decision_time"]).equals(
        pd.DatetimeIndex(right["decision_time"])
    ):
        return False
    if not np.array_equal(left["symbol"].to_numpy(), right["symbol"].to_numpy()):
        return False
    left_values = left["score"].to_numpy(dtype="<f8", copy=True).view("<u8")
    right_values = right["score"].to_numpy(dtype="<f8", copy=True).view("<u8")
    return bool(np.array_equal(left_values, right_values))


def _target_digest(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    digest.update(_canonical_json_bytes(list(frame.columns)))
    digest.update(pd.DatetimeIndex(frame.index).asi8.astype("<i8", copy=False).tobytes())
    digest.update(frame[REBALANCE_INSTRUCTION_COLUMN].to_numpy(dtype=np.uint8).tobytes())
    columns = [name for name in frame.columns if name != REBALANCE_INSTRUCTION_COLUMN]
    digest.update(frame.loc[:, columns].to_numpy(dtype="<f8", copy=True).tobytes())
    return digest.hexdigest()


def _score_digest(frame: pd.DataFrame) -> str:
    digest = hashlib.sha256()
    for row in frame.itertuples(index=False):
        digest.update(np.asarray([pd.Timestamp(row.decision_time).value], dtype="<i8").tobytes())
        encoded = str(row.symbol).encode("utf-8")
        digest.update(len(encoded).to_bytes(4, "big"))
        digest.update(encoded)
        digest.update(np.asarray([float(row.score)], dtype="<f8").tobytes())
    return digest.hexdigest()


def _average_ranks(values: Sequence[float]) -> np.ndarray:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or not len(array) or not np.isfinite(array).all():
        raise ValueError("rank input must be a finite nonempty vector")
    order = sorted(range(len(array)), key=lambda index: (array[index], index))
    ranks = np.empty(len(array), dtype=float)
    start = 0
    while start < len(order):
        stop = start + 1
        while stop < len(order) and array[order[stop]] == array[order[start]]:
            stop += 1
        average = ((start + 1) + stop) / 2.0
        for position in order[start:stop]:
            ranks[position] = average
        start = stop
    return ranks


def _spearman(values: Sequence[float], outcomes: Sequence[float]) -> float | None:
    left = np.asarray(values, dtype=float)
    right = np.asarray(outcomes, dtype=float)
    if (
        left.ndim != 1
        or right.ndim != 1
        or left.shape != right.shape
        or len(left) < 2
        or not np.isfinite(left).all()
        or not np.isfinite(right).all()
    ):
        return None
    left_rank = _average_ranks(left)
    right_rank = _average_ranks(right)
    left_centered = left_rank - math.fsum(left_rank) / len(left_rank)
    right_centered = right_rank - math.fsum(right_rank) / len(right_rank)
    denominator = math.sqrt(
        math.fsum(left_centered * left_centered)
        * math.fsum(right_centered * right_centered)
    )
    if not math.isfinite(denominator) or denominator <= 0.0:
        return None
    result = math.fsum(left_centered * right_centered) / denominator
    return float(result) if math.isfinite(result) else None


def _fold_for(timestamp: pd.Timestamp) -> tuple[str, pd.Timestamp, pd.Timestamp] | None:
    value = pd.Timestamp(timestamp)
    value = value.tz_localize("UTC") if value.tzinfo is None else value.tz_convert("UTC")
    for fold_id, raw_start, raw_end in FOLDS:
        start = pd.Timestamp(raw_start)
        end = pd.Timestamp(raw_end)
        if start <= value < end:
            return fold_id, start, end
    return None


def _label_score_panel(
    scores: pd.DataFrame,
    bars: pd.DataFrame,
) -> tuple[pd.DataFrame, Mapping[str, Any]]:
    required_scores = {"decision_time", "symbol", "score"}
    required_bars = {"open_time", "symbol", "open"}
    if not required_scores.issubset(scores) or not required_bars.issubset(bars):
        raise ValueError("score or bar panel lacks required columns")
    score_frame = scores.loc[:, ["decision_time", "symbol", "score"]].copy()
    score_frame["decision_time"] = pd.to_datetime(score_frame["decision_time"], utc=True)
    if score_frame.duplicated(["decision_time", "symbol"]).any():
        raise ValueError("score panel contains duplicate decision-symbol rows")
    if any(timestamp.hour != 0 for timestamp in score_frame["decision_time"]):
        raise ValueError("score panel contains a non-00:00 decision")
    bar_frame = bars.loc[:, ["open_time", "symbol", "open"]].copy()
    bar_frame["open_time"] = pd.to_datetime(bar_frame["open_time"], utc=True)
    if bar_frame.duplicated(["open_time", "symbol"]).any():
        raise ValueError("bar panel contains duplicate executable opens")
    bar_frame["open"] = pd.to_numeric(bar_frame["open"], errors="coerce").astype(float)
    opens = bar_frame.set_index(["open_time", "symbol"])["open"]

    rows: list[dict[str, object]] = []
    purged_decisions = 0
    unavailable_labels = 0
    for decision_time, cross_section in score_frame.groupby(
        "decision_time", observed=True, sort=True
    ):
        timestamp = pd.Timestamp(decision_time)
        fold = _fold_for(timestamp)
        if fold is None:
            raise ValueError("score decision lies outside the frozen six folds")
        fold_id, _fold_start, fold_end = fold
        label_end = timestamp + _LABEL_HORIZON
        if label_end >= fold_end:
            purged_decisions += 1
            continue
        for item in cross_section.sort_values("symbol").itertuples(index=False):
            key_start = (timestamp, str(item.symbol))
            key_end = (label_end, str(item.symbol))
            start_open = opens.get(key_start, np.nan)
            end_open = opens.get(key_end, np.nan)
            if (
                not math.isfinite(float(start_open))
                or not math.isfinite(float(end_open))
                or float(start_open) <= 0.0
                or float(end_open) <= 0.0
            ):
                unavailable_labels += 1
                continue
            rows.append(
                {
                    "decision_time": timestamp,
                    "label_end_time": label_end,
                    "fold_id": fold_id,
                    "symbol": str(item.symbol),
                    "score": float(item.score),
                    "forward_return": float(end_open) / float(start_open) - 1.0,
                }
            )
    panel = pd.DataFrame(
        rows,
        columns=(
            "decision_time",
            "label_end_time",
            "fold_id",
            "symbol",
            "score",
            "forward_return",
        ),
    )
    if panel.empty:
        raise ValueError("no causal score-label pairs remain after fold-boundary purging")
    panel = panel.sort_values(["decision_time", "symbol"]).reset_index(drop=True)

    daily_rows: list[dict[str, object]] = []
    undefined_daily = 0
    for timestamp, cross_section in panel.groupby("decision_time", observed=True, sort=True):
        value = _spearman(cross_section["score"], cross_section["forward_return"])
        if value is None:
            undefined_daily += 1
            continue
        daily_rows.append(
            {
                "decision_time": pd.Timestamp(timestamp),
                "fold_id": str(cross_section["fold_id"].iloc[0]),
                "pair_count": len(cross_section),
                "spearman_ic": value,
            }
        )
    daily = pd.DataFrame(
        daily_rows,
        columns=("decision_time", "fold_id", "pair_count", "spearman_ic"),
    )
    if daily.empty:
        pooled: float | None = None
    else:
        pooled = float(math.fsum(daily["spearman_ic"]) / len(daily))
    fold_values: dict[str, float | None] = {}
    fold_daily_counts: dict[str, int] = {}
    for fold_id, _start, _end in FOLDS:
        values = daily.loc[daily["fold_id"].eq(fold_id), "spearman_ic"]
        fold_daily_counts[fold_id] = int(len(values))
        fold_values[fold_id] = (
            None if values.empty else float(math.fsum(values) / len(values))
        )
    positive_fold_count = sum(
        value is not None and value > 0.0 for value in fold_values.values()
    )
    statistics = {
        "label_id": LABEL_ID,
        "ic_id": IC_ID,
        "pooled_next_day_score_ic": pooled,
        "fold_score_ic": fold_values,
        "fold_daily_ic_counts": fold_daily_counts,
        "positive_fold_count": positive_fold_count,
        "valid_daily_ic_count": len(daily),
        "undefined_daily_ic_count": undefined_daily,
        "labeled_pair_count": len(panel),
        "purged_fold_boundary_decision_count": purged_decisions,
        "unavailable_symbol_label_count": unavailable_labels,
    }
    return panel, statistics


def _snapshot_hashes(snapshot: Any, root: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for path, expected in sorted(snapshot.file_hashes.items(), key=lambda item: item[0].as_posix()):
        relative = path.resolve().relative_to(root).as_posix()
        actual = runner_v2._sha256_file(path)
        if actual != expected:
            raise ValueError("snapshot changed during score diagnostics")
        result[relative] = actual
    return result


def _parquet_bytes(frame: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    frame.to_parquet(buffer, index=False)
    return buffer.getvalue()


def _indexed_targets(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    result.index = pd.to_datetime(result.index, utc=True)
    result.index.name = "timestamp"
    return result.reset_index()


def _publish_private_artifacts(
    root: Path,
    request: ScoreDiagnosticRequest,
    artifacts: Mapping[str, bytes],
    private_output_dir: Path,
) -> dict[str, str]:
    if set(artifacts) != set(REQUIRED_PRIVATE_ARTIFACT_NAMES):
        raise ValueError("score diagnostic private artifact set is incomplete")
    if any(len(artifacts[name]) > MAX_PRIVATE_ARTIFACT_BYTES for name in artifacts):
        raise ValueError("score diagnostic private artifact exceeds its size ceiling")
    if sum(len(artifacts[name]) for name in artifacts) > MAX_PRIVATE_RESULT_BYTES:
        raise ValueError("score diagnostic private result exceeds its size ceiling")
    hashes = {name: sha256_bytes(artifacts[name]) for name in REQUIRED_PRIVATE_ARTIFACT_NAMES}
    base = git_path(root, PRIVATE_ARTIFACT_GIT_PATH)
    ensure_owner_directory(base.parent)
    ensure_owner_directory(base)
    team_root = base / request.team_id
    ensure_owner_directory(team_root)
    final = team_root / request.diagnostic_id
    supplied = Path(private_output_dir).absolute()
    if supplied != final.absolute():
        raise ValueError("private_output_dir is not the reserved Git-administrative path")
    if final.is_symlink():
        raise ValueError("private_output_dir cannot be a symlink")
    if final.exists():
        info = os.lstat(final)
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.geteuid() or (
            stat.S_IMODE(info.st_mode) != 0o700
        ):
            raise ValueError("private_output_dir must be an owner-only directory")
        if any(final.iterdir()):
            # A hard interruption can occur after the complete directory rename but before the
            # lifecycle records its hashes. Accept only the exact bytes regenerated by the two
            # deterministic replays; arbitrary or partial pre-existing evidence stays closed.
            validate_private_artifacts(
                root,
                request.team_id,
                request.diagnostic_id,
                hashes,
                REQUIRED_PRIVATE_ARTIFACT_NAMES,
            )
            return hashes

    temporary = Path(
        tempfile.mkdtemp(prefix=f".{request.diagnostic_id}.publishing-", dir=team_root)
    )
    os.chmod(temporary, 0o700)
    published = False
    try:
        for name in REQUIRED_PRIVATE_ARTIFACT_NAMES:
            path = temporary / name
            atomic_write_bytes(path, artifacts[name], mode=0o600)
        fsync_directory(temporary)
        if final.exists():
            # The lifecycle may pre-create a canonical empty placeholder. Removing it lets the
            # complete six-file set become visible through one atomic directory rename.
            os.rmdir(final)
            fsync_directory(team_root)
        os.rename(temporary, final)
        published = True
        fsync_directory(team_root)
    finally:
        if not published and temporary.exists():
            for path in temporary.iterdir():
                path.unlink(missing_ok=True)
            os.rmdir(temporary)
            fsync_directory(team_root)
    validate_private_artifacts(
        root,
        request.team_id,
        request.diagnostic_id,
        hashes,
        REQUIRED_PRIVATE_ARTIFACT_NAMES,
    )
    return hashes


def trusted_boolean_verdict(summary_bytes: bytes) -> Mapping[str, bool]:
    """Derive the only public disclosure from a private numeric summary."""

    summary = strict_json_object(summary_bytes, "private score diagnostic summary")
    if _pretty_json_bytes(summary) != summary_bytes:
        raise ValueError("private score diagnostic summary is not canonical JSON")
    if set(summary) != {
        "schema_version",
        "diagnostic_id",
        "reservation_sha256",
        "status",
        "replay",
        "score_ic",
    }:
        raise ValueError("private score diagnostic summary has unexpected fields")
    if (
        summary.get("schema_version") != 1
        or summary.get("status") != "completed"
        or not isinstance(summary.get("diagnostic_id"), str)
        or _SAFE_ID.fullmatch(str(summary.get("diagnostic_id"))) is None
    ):
        raise ValueError("private score diagnostic summary identity is invalid")
    _require_sha(summary.get("reservation_sha256"), "summary reservation_sha256")
    replay = summary.get("replay")
    statistics = summary.get("score_ic")
    if not isinstance(replay, Mapping) or set(replay) != {
        "replay_targets_identical",
        "replay_scores_identical",
        "canonical_targets_replay_1_exact",
        "canonical_targets_replay_2_exact",
    }:
        raise ValueError("private replay evidence is incomplete")
    if any(type(value) is not bool for value in replay.values()):
        raise ValueError("private replay evidence must contain booleans")
    if not isinstance(statistics, Mapping) or set(statistics) != {
        "pooled_ic",
        "fold_ics",
        "daily_ic_count",
        "fold_daily_ic_counts",
    }:
        raise ValueError("private score IC evidence is incomplete")
    pooled = statistics.get("pooled_ic")
    fold_values = statistics.get("fold_ics")
    if pooled is not None and (
        isinstance(pooled, bool)
        or not isinstance(pooled, (int, float))
        or not math.isfinite(pooled)
        or abs(float(pooled)) > 1.0 + 1.0e-12
    ):
        raise ValueError("private pooled IC is invalid")
    if not isinstance(fold_values, list) or len(fold_values) != len(FOLDS):
        raise ValueError("private fold IC list differs from the frozen folds")
    daily_count = statistics.get("daily_ic_count")
    fold_daily_counts = statistics.get("fold_daily_ic_counts")
    if isinstance(daily_count, bool) or not isinstance(daily_count, int) or daily_count < 0:
        raise ValueError("private daily IC count is invalid")
    if not isinstance(fold_daily_counts, list) or len(fold_daily_counts) != len(FOLDS):
        raise ValueError("private fold daily IC counts differ from the frozen folds")
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in fold_daily_counts
    ):
        raise ValueError("private fold daily IC count is invalid")
    if sum(fold_daily_counts) != daily_count:
        raise ValueError("private daily and fold IC counts are inconsistent")
    normalized_folds: list[float | None] = []
    for raw, count in zip(fold_values, fold_daily_counts, strict=True):
        if raw is None:
            normalized_folds.append(None)
        elif (
            isinstance(raw, bool)
            or not isinstance(raw, (int, float))
            or not math.isfinite(raw)
            or abs(float(raw)) > 1.0 + 1.0e-12
        ):
            raise ValueError("private fold IC is invalid")
        else:
            normalized_folds.append(float(raw))
        if (count == 0) != (raw is None):
            raise ValueError("private fold IC availability differs from its daily count")
    if (daily_count == 0) != (pooled is None):
        raise ValueError("private pooled IC availability differs from its daily count")
    positive_count = sum(value is not None and value > 0.0 for value in normalized_folds)
    deterministic = (
        replay["replay_targets_identical"] and replay["replay_scores_identical"]
    )
    target_exact = (
        replay["canonical_targets_replay_1_exact"]
        and replay["canonical_targets_replay_2_exact"]
    )
    pooled_positive = pooled is not None and float(pooled) > 0.0
    four_positive = positive_count >= 4
    return {
        "canonical_targets_exact": target_exact,
        "deterministic_replays_passed": deterministic,
        "four_of_six_fold_ics_positive": four_positive,
        "pooled_ic_positive": pooled_positive,
        "score_ic_gate_passed": (
            deterministic and target_exact and pooled_positive and four_positive
        ),
    }


def _verify_runner_record(
    root: Path,
    request: ScoreDiagnosticRequest,
    registration: Mapping[str, Any],
) -> None:
    _relative, _path, payload, _stat = read_repo_file(
        root,
        request.runner_record_path,
        "completed development runner record",
        maximum_bytes=4 * 1024 * 1024,
        require_single_link=True,
    )
    if sha256_bytes(payload) != request.runner_record_sha256:
        raise ValueError("completed development runner record hash differs")
    record = strict_json_object(payload, "completed development runner record")
    expected = {
        "stage": "development",
        "team_id": request.team_id,
        "strategy_sha256": registration["strategy_sha256"],
        "risk_policy_sha256": registration["risk_config_sha256"],
        "source_bundle_sha256": registration["source_bundle_sha256"],
        "config_sha256": request.config_sha256,
        "data_manifest_sha256": request.snapshot_manifest_sha256,
    }
    if any(record.get(field) != value for field, value in expected.items()):
        raise ValueError("completed runner record differs from diagnostic authority")
    if record.get("seeds") != [request.candidate_seed]:
        raise ValueError("completed runner record seed differs from diagnostic authority")
    artifacts = record.get("artifact_sha256")
    if not isinstance(artifacts, Mapping) or artifacts.get("targets") != (
        request.development_target_sha256
    ):
        raise ValueError("completed runner record does not bind the target artifact")


def run_score_diagnostic(
    root: str | Path,
    config: LoadedV2Config,
    request: ScoreDiagnosticRequest,
    *,
    reservation_sha256: str,
    private_output_dir: Path,
) -> ScoreDiagnosticOutcome:
    """Execute the reviewed diagnostic twice and publish private evidence atomically."""

    root_path = Path(root).resolve()
    _require_sha(reservation_sha256, "reservation_sha256")
    _registration_path, target_relative, _runner_relative = _request_paths(request)
    if config.sha256 != request.config_sha256:
        raise ValueError("diagnostic request config binding differs")
    expected_manifest = str(config.raw["paths"]["shared_snapshot_manifest"])
    if request.snapshot_manifest_path != expected_manifest:
        raise ValueError("score diagnostic snapshot path differs from the frozen config")
    manifest_relative = safe_relative(request.snapshot_manifest_path, "snapshot manifest")
    _manifest_relative, manifest_path, manifest_bytes, _manifest_stat = read_repo_file(
        root_path,
        manifest_relative,
        "score diagnostic snapshot manifest",
        maximum_bytes=32 * 1024 * 1024,
        require_single_link=True,
    )
    if sha256_bytes(manifest_bytes) != request.snapshot_manifest_sha256:
        raise ValueError("score diagnostic snapshot manifest hash differs")
    _target_relative, _target_path, target_bytes, _target_stat = read_repo_file(
        root_path,
        target_relative,
        "completed development targets",
        maximum_bytes=16 * 1024 * 1024,
        require_single_link=True,
    )
    if sha256_bytes(target_bytes) != request.development_target_sha256:
        raise ValueError("completed development target hash differs")

    with materialized_historical_source(root_path, config, request) as historical:
        _verify_runner_record(root_path, request, historical.registration)
        snapshot = runner_v2._load_verified_snapshot(root_path, manifest_path)
        authorized = runner_v2._authorized_window(config.raw, "development")
        decision_times = runner_v2._decision_grid(authorized)
        runner_v2._validate_snapshot_bounds(snapshot, config.raw, decision_times)
        end = pd.Timestamp(authorized.end_exclusive, tz="UTC")
        bars = snapshot.bars.loc[
            pd.to_datetime(snapshot.bars["open_time"], utc=True) < end
        ].copy()
        funding = snapshot.funding.loc[
            pd.to_datetime(snapshot.funding["funding_time"], utc=True) < end
        ].copy()
        membership = snapshot.membership.loc[
            pd.to_datetime(snapshot.membership["reconstitution_time"], utc=True) < end
        ].copy()
        before_hashes = _snapshot_hashes(snapshot, root_path)
        canonical_targets = _target_frame_from_bytes(target_bytes, bars, decision_times)
        seed = int(historical.registration["seed"])

        first = _run_replay(
            root_path,
            historical,
            bars=bars,
            funding=funding,
            membership=membership,
            decision_times=decision_times,
            seed=seed,
            adapter_id=request.score_adapter_id,
        )
        second = _run_replay(
            root_path,
            historical,
            bars=bars,
            funding=funding,
            membership=membership,
            decision_times=decision_times,
            seed=seed,
            adapter_id=request.score_adapter_id,
        )
        replay_targets_identical = _targets_exact(first.targets, second.targets)
        canonical_first_exact = _targets_exact(first.targets, canonical_targets)
        canonical_second_exact = _targets_exact(second.targets, canonical_targets)
        targets_match = (
            replay_targets_identical and canonical_first_exact and canonical_second_exact
        )
        scores_match = _scores_exact(first.scores, second.scores)
        if not targets_match:
            raise ValueError("score diagnostic targets differ from canonical completed targets")
        if not scores_match:
            raise ValueError("score diagnostic score replays are nondeterministic")
        labeled_panel, statistics = _label_score_panel(first.scores, bars)
        runner_v2._verify_snapshot_files_unchanged(snapshot)
        after_hashes = _snapshot_hashes(snapshot, root_path)
        if before_hashes != after_hashes:
            raise ValueError("snapshot hashes changed during score diagnostics")
        _post_relative, _post_path, post_manifest_bytes, _post_stat = read_repo_file(
            root_path,
            manifest_relative,
            "score diagnostic snapshot manifest after replays",
            maximum_bytes=32 * 1024 * 1024,
            require_single_link=True,
        )
        if (
            post_manifest_bytes != manifest_bytes
            or sha256_bytes(post_manifest_bytes) != request.snapshot_manifest_sha256
        ):
            raise ValueError("snapshot manifest changed during score diagnostics")

        summary = {
            "schema_version": 1,
            "diagnostic_id": request.diagnostic_id,
            "reservation_sha256": reservation_sha256,
            "status": "completed",
            "replay": {
                "replay_targets_identical": replay_targets_identical,
                "replay_scores_identical": scores_match,
                "canonical_targets_replay_1_exact": canonical_first_exact,
                "canonical_targets_replay_2_exact": canonical_second_exact,
            },
            "score_ic": {
                "pooled_ic": statistics["pooled_next_day_score_ic"],
                "fold_ics": [
                    statistics["fold_score_ic"][fold_id]
                    for fold_id, _start, _end in FOLDS
                ],
                "daily_ic_count": statistics["valid_daily_ic_count"],
                "fold_daily_ic_counts": [
                    statistics["fold_daily_ic_counts"][fold_id]
                    for fold_id, _start, _end in FOLDS
                ],
            },
        }
        summary_bytes = _pretty_json_bytes(summary)
        trusted_boolean_verdict(summary_bytes)
        artifacts = {
            "diagnostic-summary.json": summary_bytes,
            "labeled-score-panel.parquet": _parquet_bytes(labeled_panel),
            "replay-1-scores.parquet": _parquet_bytes(first.scores),
            "replay-1-targets.parquet": _parquet_bytes(_indexed_targets(first.targets)),
            "replay-2-scores.parquet": _parquet_bytes(second.scores),
            "replay-2-targets.parquet": _parquet_bytes(_indexed_targets(second.targets)),
        }
        artifact_hashes = _publish_private_artifacts(
            root_path,
            request,
            artifacts,
            private_output_dir,
        )
        return ScoreDiagnosticOutcome(
            diagnostic_id=request.diagnostic_id,
            team_id=request.team_id,
            candidate_id=request.candidate_id,
            artifact_hashes=artifact_hashes,
            historical_source_commit=historical.binding.registration_commit,
        )


def _resource_snapshot() -> tuple[float, float]:
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime, time.monotonic()


def _resource_delta(before: tuple[float, float]) -> tuple[float, float]:
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = time.process_time() + children.ru_utime + children.ru_stime
    return (
        max(0.0, (cpu - before[0]) / 3600.0),
        max(0.0, (time.monotonic() - before[1]) / 3600.0),
    )


def _reservation_body(
    reservation: Mapping[str, Any],
) -> tuple[Mapping[str, Any], str]:
    raw_payload = reservation.get("payload")
    if isinstance(raw_payload, Mapping):
        body = raw_payload
        reservation_sha = reservation.get("record_sha256")
    else:
        body = reservation
        reservation_sha = reservation.get("reservation_sha256")
    _require_sha(reservation_sha, "reservation record SHA-256")
    required = {
        "diagnostic_id",
        "team_id",
        "candidate_id",
        "candidate_registration_sha256",
        "strategy_sha256",
        "source_bundle_sha256",
        "risk_policy_sha256",
        "config_sha256",
        "candidate_seed",
        "runner_seed",
        "snapshot_manifest_path",
        "snapshot_manifest_sha256",
        "development_target_path",
        "development_target_sha256",
        "runner_record_path",
        "runner_record_sha256",
    }
    missing = sorted(required - set(body))
    if missing:
        raise ValueError(f"diagnostic reservation lacks required bindings: {missing}")
    if body.get("diagnostic_kind") not in {
        None,
        "organizer-private-score-diagnostics-backfill-v1",
    }:
        raise ValueError("diagnostic reservation has the wrong diagnostic kind")
    if body.get("non_material", True) is not True or body.get(
        "charges_team_trial_budget", False
    ) is not False:
        raise ValueError("score diagnostic reservation is not non-material")
    if body["candidate_seed"] != body["runner_seed"]:
        raise ValueError("candidate and canonical runner seeds differ")
    return body, str(reservation_sha)


def run_reserved_score_diagnostic(
    *,
    root: Path,
    reservation: Mapping[str, Any],
    private_output_dir: Path,
) -> Mapping[str, Any]:
    """Lifecycle boundary returning resource accounting and no score information.

    All numeric IC evidence remains in the six owner-only files.  On failure this function
    returns a terminal status and bounded reason; it never converts a diagnostic failure into a
    material team trial or performance result.
    """

    usage = _resource_snapshot()
    try:
        root_path = Path(root).resolve()
        body, reservation_sha = _reservation_body(reservation)
        config = load_v2_config(root_path / TOP40_V2_LAYOUT.config_path)
        request = ScoreDiagnosticRequest(
            diagnostic_id=str(body["diagnostic_id"]),
            team_id=str(body["team_id"]),
            family_id=FAMILY_ID,
            candidate_id=str(body["candidate_id"]),
            registration_sha256=str(body["candidate_registration_sha256"]),
            strategy_sha256=str(body["strategy_sha256"]),
            risk_policy_sha256=str(body["risk_policy_sha256"]),
            source_bundle_sha256=str(body["source_bundle_sha256"]),
            candidate_seed=body["candidate_seed"],
            config_sha256=str(body["config_sha256"]),
            snapshot_manifest_path=str(body["snapshot_manifest_path"]),
            snapshot_manifest_sha256=str(body["snapshot_manifest_sha256"]),
            development_target_path=str(body["development_target_path"]),
            development_target_sha256=str(body["development_target_sha256"]),
            runner_record_path=str(body["runner_record_path"]),
            runner_record_sha256=str(body["runner_record_sha256"]),
        )
        run_score_diagnostic(
            root_path,
            config,
            request,
            reservation_sha256=reservation_sha,
            private_output_dir=Path(private_output_dir),
        )
    except BaseException as exc:
        cpu_hours, wall_hours = _resource_delta(usage)
        return {
            "status": "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
            "failure_reason": f"{type(exc).__name__}: {exc}"[:8000],
            "organizer_cpu_hours": cpu_hours,
            "organizer_wall_clock_hours": wall_hours,
        }
    cpu_hours, wall_hours = _resource_delta(usage)
    return {
        "status": "completed",
        "failure_reason": None,
        "organizer_cpu_hours": cpu_hours,
        "organizer_wall_clock_hours": wall_hours,
    }
