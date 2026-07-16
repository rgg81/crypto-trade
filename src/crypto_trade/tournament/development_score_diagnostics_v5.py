"""Prospective development-only declared-score diagnostics for draft Amendment 0005.

The engine reconstructs the exact preregistration tree, runs two clean sandbox replays, requires
bit-exact replay scores and targets, and requires both target replays to equal the archived
completed development targets. It never selects a private or final window. Runtime proves only
the exact captured bytes, schedule, replay, and target equivalence. It does not prove that the
captured values are the operative model-ranking signal or semantically pre-construction; that
claim requires a separately hash-bound static source review. The resulting Pearson statistic is
candidate-declared, nonautomatic public development evidence.
"""

from __future__ import annotations

import contextlib
import dataclasses
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
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Any, BinaryIO

import numpy as np
import pandas as pd

from crypto_trade.tournament import runner_v2
from crypto_trade.tournament import score_diagnostics_v2 as frozen_science
from crypto_trade.tournament.amendment_integrity_v2 import (
    atomic_write_bytes,
    fsync_directory,
    git_bytes,
    read_repo_file,
    safe_relative,
    sha256_bytes,
    strict_json_object,
    unique_first_add_commit,
)
from crypto_trade.tournament.engine_v2 import (
    _normalise_bars,
    _normalise_funding,
    generate_targets,
)
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.research_v2 import build_trial_registration
from crypto_trade.tournament.score_adapter_protocol_v5 import (
    ADAPTER_ID,
    CAPTURE_BOUNDARY,
    HOOK_QUALNAME,
)
from crypto_trade.tournament.top40_v2 import LoadedV2Config
from crypto_trade.tournament.top40_v2 import load_config as load_v2_config

DIAGNOSTIC_KIND = "top40-v2-development-declared-score-diagnostic-v1"
LABEL_ID = "manifest-horizon-simple-executable-open-to-open-return-v1"
STATISTIC_ID = "globally-pooled-pearson-v1"
STAGE = "development"

FOLDS = (
    ("F1", "2020-02-03T00:00:00Z", "2020-09-01T00:00:00Z"),
    ("F2", "2020-09-01T00:00:00Z", "2021-04-01T00:00:00Z"),
    ("F3", "2021-04-01T00:00:00Z", "2021-11-01T00:00:00Z"),
    ("F4", "2021-11-01T00:00:00Z", "2022-06-01T00:00:00Z"),
    ("F5", "2022-06-01T00:00:00Z", "2023-01-01T00:00:00Z"),
    ("F6", "2023-01-01T00:00:00Z", "2023-07-01T00:00:00Z"),
)

REQUIRED_ARTIFACT_NAMES = tuple(
    sorted(
        {
            "diagnostic-summary.json",
            "labeled-score-panel.parquet",
            "replay-1-scores.parquet",
            "replay-1-targets.parquet",
            "replay-2-scores.parquet",
            "replay-2-targets.parquet",
        }
    )
)

_A1_MATERIALIZE_TREE = frozen_science._materialize_team_tree
_A1_TARGET_FROM_BYTES = frozen_science._target_frame_from_bytes
_A1_TARGETS_EXACT = frozen_science._targets_exact
_A1_SCORES_EXACT = frozen_science._scores_exact
_A1_TARGET_DIGEST = frozen_science._target_digest
_A1_SCORE_DIGEST = frozen_science._score_digest
_A1_SNAPSHOT_HASHES = frozen_science._snapshot_hashes
_A1_PARQUET_BYTES = frozen_science._parquet_bytes
_A1_INDEXED_TARGETS = frozen_science._indexed_targets

_MAX_ARTIFACT_BYTES = 128 * 1024 * 1024
_IDENTIFIER = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_ELIGIBLE_TEAMS = {f"team-{number:02d}" for number in range(4, 11)}


def frozen_science_helper_bindings() -> Mapping[str, object]:
    """Return every Amendment 0001 helper captured by this draft module."""

    return {
        "_materialize_team_tree": _A1_MATERIALIZE_TREE,
        "_target_frame_from_bytes": _A1_TARGET_FROM_BYTES,
        "_targets_exact": _A1_TARGETS_EXACT,
        "_scores_exact": _A1_SCORES_EXACT,
        "_target_digest": _A1_TARGET_DIGEST,
        "_score_digest": _A1_SCORE_DIGEST,
        "_snapshot_hashes": _A1_SNAPSHOT_HASHES,
        "_parquet_bytes": _A1_PARQUET_BYTES,
        "_indexed_targets": _A1_INDEXED_TARGETS,
    }


def verify_frozen_science_helper_identities() -> None:
    for name, captured in frozen_science_helper_bindings().items():
        if getattr(frozen_science, name, None) is not captured:
            raise ValueError(f"Amendment 0001 helper identity changed: {name}")


@dataclasses.dataclass(frozen=True, slots=True)
class ScoreAdapterManifest:
    team_id: str
    family_id: str
    candidate_id: str
    anchor_timestamp_utc: str
    interval_hours: int
    holding_horizon_hours: int
    minimum_pairs: int
    score_description: str
    semantic_coupling_review_sha256: str

    @property
    def worker_schedule(self) -> Mapping[str, object]:
        return {
            "anchor_timestamp_utc": self.anchor_timestamp_utc,
            "interval_hours": self.interval_hours,
        }

    def scheduled(self, timestamp: pd.Timestamp) -> bool:
        value = (
            timestamp.tz_localize("UTC")
            if timestamp.tzinfo is None
            else timestamp.tz_convert("UTC")
        )
        anchor = pd.Timestamp(self.anchor_timestamp_utc)
        delta = value - anchor
        return (
            delta >= pd.Timedelta(0)
            and delta.value % pd.Timedelta(hours=self.interval_hours).value == 0
        )


@dataclasses.dataclass(frozen=True, slots=True)
class DevelopmentScoreDiagnosticRequest:
    diagnostic_id: str
    team_id: str
    family_id: str
    candidate_id: str
    registration_input_path: str
    registration_sha256: str
    registration_commit: str
    strategy_sha256: str
    risk_policy_sha256: str
    source_bundle_sha256: str
    candidate_seed: int
    config_sha256: str
    score_manifest_path: str
    score_manifest_sha256: str
    score_manifest_commit: str
    semantic_coupling_review_path: str
    semantic_coupling_review_sha256: str
    semantic_coupling_review_commit: str
    snapshot_manifest_path: str
    snapshot_manifest_sha256: str
    development_target_path: str
    development_target_sha256: str
    runner_record_path: str
    runner_record_sha256: str
    reservation_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class HistoricalSourceBinding:
    registration_commit: str
    score_manifest_commit: str
    source_tree_manifest_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class _MaterializedSource:
    binding: HistoricalSourceBinding
    team_root: Path
    entrypoint: Path
    registration: Mapping[str, Any]
    manifest: ScoreAdapterManifest


@dataclasses.dataclass(frozen=True, slots=True)
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


def _exact_regular_bytes(path: Path, *, maximum_bytes: int, label: str) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_size > maximum_bytes
        ):
            raise ValueError(f"{label} is not a bounded single-link regular file")
        chunks: list[bytes] = []
        remaining = before.st_size
        while remaining:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                raise ValueError(f"{label} truncated while read")
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        if os.read(descriptor, 1) or (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_nlink,
        ) != (before.st_dev, before.st_ino, before.st_size, 1):
            raise ValueError(f"{label} grew or changed while read")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def parse_score_adapter_manifest(
    payload: bytes,
    *,
    expected_team_id: str | None = None,
    expected_family_id: str | None = None,
    expected_candidate_id: str | None = None,
) -> ScoreAdapterManifest:
    raw = strict_json_object(payload, "score-adapter manifest")
    if _pretty_json_bytes(raw) != payload:
        raise ValueError("score-adapter manifest must be canonical pretty JSON")
    if set(raw) != {
        "schema_version",
        "adapter_id",
        "team_id",
        "family_id",
        "candidate_id",
        "stage",
        "hook",
        "capture_boundary",
        "schedule_utc",
        "label",
        "score_description",
        "semantic_coupling_review_sha256",
    }:
        raise ValueError("score-adapter manifest has invalid keys")
    if (
        raw["schema_version"] != 1
        or raw["adapter_id"] != ADAPTER_ID
        or raw["stage"] != STAGE
        or raw["hook"] != HOOK_QUALNAME
        or raw["capture_boundary"] != CAPTURE_BOUNDARY
    ):
        raise ValueError("score-adapter manifest identity or boundary is invalid")
    for field, expected in (
        ("team_id", expected_team_id),
        ("family_id", expected_family_id),
        ("candidate_id", expected_candidate_id),
    ):
        value = raw[field]
        if (
            type(value) is not str
            or _IDENTIFIER.fullmatch(value) is None
            or (field == "team_id" and value not in _ELIGIBLE_TEAMS)
            or (expected is not None and value != expected)
        ):
            raise ValueError(f"score-adapter manifest {field} is invalid")
    schedule = raw["schedule_utc"]
    if not isinstance(schedule, Mapping) or set(schedule) != {
        "anchor_timestamp_utc",
        "interval_hours",
    }:
        raise ValueError("score-adapter manifest schedule is invalid")
    anchor = schedule["anchor_timestamp_utc"]
    if type(anchor) is not str or not anchor.endswith("Z"):
        raise ValueError("score schedule anchor must be canonical UTC text")
    try:
        anchor_value = pd.Timestamp(anchor)
    except (TypeError, ValueError) as exc:
        raise ValueError("score schedule anchor is invalid") from exc
    if anchor_value.tzinfo is None or anchor_value.nanosecond:
        raise ValueError("score schedule anchor must be timezone-aware and whole-second")
    interval = schedule["interval_hours"]
    if type(interval) is not int or not 8 <= interval <= 168 or interval % 8:
        raise ValueError("score schedule interval must be 8..168 and divisible by eight")
    label = raw["label"]
    if not isinstance(label, Mapping) or set(label) != {
        "label_id",
        "holding_horizon_hours",
        "return_definition",
        "executable_price_column",
        "score_direction",
        "statistic_id",
        "purge_cross_fold_endpoints",
        "minimum_pairs",
    }:
        raise ValueError("score-adapter manifest label is invalid")
    if (
        label["label_id"] != LABEL_ID
        or label["return_definition"] != "simple-executable-open-to-open"
        or label["executable_price_column"] != "open"
        or label["score_direction"] != "higher-score-higher-return"
        or label["statistic_id"] != STATISTIC_ID
        or label["purge_cross_fold_endpoints"] is not True
    ):
        raise ValueError("score-adapter label contract cannot be changed")
    horizon = label["holding_horizon_hours"]
    if type(horizon) is not int or not 8 <= horizon <= 168 or horizon % 8:
        raise ValueError("holding horizon must be 8..168 and divisible by eight")
    minimum_pairs = label["minimum_pairs"]
    if type(minimum_pairs) is not int or not 2 <= minimum_pairs <= 1_000_000:
        raise ValueError("minimum_pairs must be an integer from 2 through 1000000")
    description = raw["score_description"]
    if (
        type(description) is not str
        or not description.strip()
        or description != description.strip()
        or len(description) > 4000
    ):
        raise ValueError("score_description must be bounded trimmed text")
    semantic_review_sha = raw["semantic_coupling_review_sha256"]
    if (
        type(semantic_review_sha) is not str
        or len(semantic_review_sha) != 64
        or any(character not in "0123456789abcdef" for character in semantic_review_sha)
    ):
        raise ValueError("semantic_coupling_review_sha256 must be lowercase SHA-256")
    return ScoreAdapterManifest(
        team_id=str(raw["team_id"]),
        family_id=str(raw["family_id"]),
        candidate_id=str(raw["candidate_id"]),
        anchor_timestamp_utc=str(anchor),
        interval_hours=int(interval),
        holding_horizon_hours=int(horizon),
        minimum_pairs=int(minimum_pairs),
        score_description=str(description),
        semantic_coupling_review_sha256=semantic_review_sha,
    )


def parse_semantic_coupling_review(
    payload: bytes,
    *,
    expected_team_id: str,
    expected_family_id: str,
    expected_candidate_id: str,
    expected_strategy_sha256: str,
) -> Mapping[str, Any]:
    """Validate the preregistered human/static-review attestation.

    This validates immutable review bytes and fixed attestations; it intentionally does not turn
    those attestations into a runtime proof of score semantics.
    """

    raw = strict_json_object(payload, "semantic-coupling static review")
    if _pretty_json_bytes(raw) != payload or set(raw) != {
        "schema_version",
        "review_kind",
        "team_id",
        "family_id",
        "candidate_id",
        "strategy_sha256",
        "hook",
        "declared_capture_boundary",
        "decision",
        "reviewer_id",
        "reviewed_at_utc",
        "findings",
        "runtime_proof_limit",
    }:
        raise ValueError("semantic-coupling static review has invalid keys or encoding")
    expected_findings = {
        "direct_hook_call_found": True,
        "score_object_is_declared_model_ranking_signal": True,
        "hook_after_declared_score_transform": True,
        "hook_before_selection_weight_caps_and_risk": True,
        "no_decoy_or_transient_score_path_found": True,
    }
    if (
        raw["schema_version"] != 1
        or raw["review_kind"] != "top40-v2-score-semantic-coupling-static-review-v1"
        or raw["team_id"] != expected_team_id
        or raw["family_id"] != expected_family_id
        or raw["candidate_id"] != expected_candidate_id
        or raw["strategy_sha256"] != expected_strategy_sha256
        or raw["hook"] != HOOK_QUALNAME
        or raw["declared_capture_boundary"] != CAPTURE_BOUNDARY
        or raw["decision"] != "approve"
        or raw["findings"] != expected_findings
        or raw["runtime_proof_limit"] != "static-review-attestation-not-runtime-semantic-proof"
        or type(raw["reviewer_id"]) is not str
        or not raw["reviewer_id"].strip()
        or raw["reviewer_id"] != raw["reviewer_id"].strip()
        or type(raw["reviewed_at_utc"]) is not str
        or not raw["reviewed_at_utc"].endswith("Z")
    ):
        raise ValueError("semantic-coupling static review binding is invalid")
    return raw


def _request_paths(request: DevelopmentScoreDiagnosticRequest) -> None:
    TOP40_V2_LAYOUT.require_team(request.team_id)
    expected_registration = (
        f"{TOP40_V2_LAYOUT.report_root(request.team_id)}/registration-inputs/"
        f"{request.candidate_id}.json"
    )
    expected_manifest = (
        f"{TOP40_V2_LAYOUT.team_root(request.team_id)}/score-adapters/{request.candidate_id}.json"
    )
    expected_semantic_review = (
        f"{TOP40_V2_LAYOUT.team_root(request.team_id)}/score-adapters/"
        f"{request.candidate_id}.semantic-coupling-review.json"
    )
    expected_target = (
        f"{TOP40_V2_LAYOUT.report_root(request.team_id)}/development-runs/"
        f"{request.candidate_id}/targets.parquet"
    )
    expected_runner = (
        f"{TOP40_V2_LAYOUT.report_root(request.team_id)}/qualification-attempts/"
        f"{request.candidate_id}.runner-record.json"
    )
    if (
        request.registration_input_path != expected_registration
        or request.score_manifest_path != expected_manifest
        or request.semantic_coupling_review_path != expected_semantic_review
        or request.development_target_path != expected_target
        or request.runner_record_path != expected_runner
    ):
        raise ValueError("development score diagnostic contains a noncanonical path")
    if request.snapshot_manifest_path != safe_relative(
        request.snapshot_manifest_path, "snapshot manifest path"
    ):
        raise ValueError("snapshot manifest path is noncanonical")


@contextlib.contextmanager
def materialized_historical_source(
    root: str | Path,
    config: LoadedV2Config,
    request: DevelopmentScoreDiagnosticRequest,
) -> Iterator[_MaterializedSource]:
    root_path = Path(root).resolve()
    _request_paths(request)
    if config.sha256 != request.config_sha256:
        raise ValueError("diagnostic request differs from the frozen config")
    _relative, _path, registration_bytes, _stat = read_repo_file(
        root_path,
        request.registration_input_path,
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
        raise ValueError("historical registration differs from its journal SHA-256")
    registration = json.loads(registration_line)
    expected = {
        "team_id": request.team_id,
        "family_id": request.family_id,
        "candidate_id": request.candidate_id,
        "strategy_sha256": request.strategy_sha256,
        "risk_config_sha256": request.risk_policy_sha256,
        "source_bundle_sha256": request.source_bundle_sha256,
        "config_sha256": request.config_sha256,
        "seed": request.candidate_seed,
    }
    if any(registration.get(field) != value for field, value in expected.items()):
        raise ValueError("historical registration differs from diagnostic authority")
    registration_commit = unique_first_add_commit(
        root_path, request.registration_input_path, registration_bytes
    )
    if registration_commit != request.registration_commit:
        raise ValueError("registration first-add commit differs from reservation")

    _manifest_relative, _manifest_path, manifest_bytes, _manifest_stat = read_repo_file(
        root_path,
        request.score_manifest_path,
        "score-adapter manifest",
        maximum_bytes=1024 * 1024,
        require_single_link=True,
    )
    if sha256_bytes(manifest_bytes) != request.score_manifest_sha256:
        raise ValueError("score-adapter manifest differs from reservation")
    manifest_commit = unique_first_add_commit(
        root_path, request.score_manifest_path, manifest_bytes
    )
    if manifest_commit != request.score_manifest_commit:
        raise ValueError("manifest first-add commit differs from reservation")
    if (
        git_bytes(
            root_path,
            "show",
            f"{registration_commit}:{request.score_manifest_path}",
            label="score manifest at registration",
        )
        != manifest_bytes
    ):
        raise ValueError("registration tree does not contain the exact score manifest")
    manifest = parse_score_adapter_manifest(
        manifest_bytes,
        expected_team_id=request.team_id,
        expected_family_id=request.family_id,
        expected_candidate_id=request.candidate_id,
    )
    _review_relative, _review_path, review_bytes, _review_stat = read_repo_file(
        root_path,
        request.semantic_coupling_review_path,
        "semantic-coupling static review",
        maximum_bytes=1024 * 1024,
        require_single_link=True,
    )
    if sha256_bytes(review_bytes) != request.semantic_coupling_review_sha256:
        raise ValueError("semantic-coupling static review differs from reservation")
    if manifest.semantic_coupling_review_sha256 != request.semantic_coupling_review_sha256:
        raise ValueError("manifest does not bind the reserved semantic review")
    review_commit = unique_first_add_commit(
        root_path, request.semantic_coupling_review_path, review_bytes
    )
    if review_commit != request.semantic_coupling_review_commit:
        raise ValueError("semantic review first-add commit differs from reservation")
    if (
        git_bytes(
            root_path,
            "show",
            f"{registration_commit}:{request.semantic_coupling_review_path}",
            label="semantic review at registration",
        )
        != review_bytes
    ):
        raise ValueError("registration tree lacks the exact semantic review")
    parse_semantic_coupling_review(
        review_bytes,
        expected_team_id=request.team_id,
        expected_family_id=request.family_id,
        expected_candidate_id=request.candidate_id,
        expected_strategy_sha256=request.strategy_sha256,
    )

    with tempfile.TemporaryDirectory(
        prefix=f"top40-v2-development-score-source-{request.team_id}-"
    ) as raw:
        temporary = Path(raw)
        team_root = temporary / "team"
        _A1_MATERIALIZE_TREE(root_path, registration_commit, request.team_id, team_root)
        entrypoint = team_root / "strategy.py"
        risk_path = team_root / "risk_policy.json"
        historical_manifest = team_root / "score-adapters" / f"{request.candidate_id}.json"
        historical_review = (
            team_root / "score-adapters" / f"{request.candidate_id}.semantic-coupling-review.json"
        )
        if any(
            path.is_symlink() or not path.is_file()
            for path in (entrypoint, risk_path, historical_manifest, historical_review)
        ):
            raise ValueError("historical source tree lacks required regular files")
        if (
            historical_manifest.read_bytes() != manifest_bytes
            or historical_review.read_bytes() != review_bytes
        ):
            raise ValueError("historical source tree contains different diagnostic bindings")
        files = runner_v2._team_tree_files(team_root)
        entries = [
            {"path": item.relative, "sha256": item.sha256, "size": item.size} for item in files
        ]
        if (
            sha256_bytes(runner_v2._stable_file_bytes(entrypoint)) != request.strategy_sha256
            or sha256_bytes(runner_v2._stable_file_bytes(risk_path)) != request.risk_policy_sha256
            or runner_v2._team_tree_fingerprint(files) != request.source_bundle_sha256
        ):
            raise ValueError("registration commit does not reconstruct registered source hashes")
        yield _MaterializedSource(
            HistoricalSourceBinding(
                registration_commit=registration_commit,
                score_manifest_commit=manifest_commit,
                source_tree_manifest_sha256=sha256_bytes(_canonical_json_bytes(entries)),
            ),
            team_root,
            entrypoint,
            registration,
            manifest,
        )


class _CapturingClient:
    def __init__(self, client: Any, *, manifest: ScoreAdapterManifest) -> None:
        self._client = client
        self._manifest = manifest
        self.captured: dict[pd.Timestamp, Mapping[str, float] | None] = {}

    def initialise(self, payload: Mapping[str, Any]) -> None:
        request = dict(payload)
        request["score_adapter_id"] = ADAPTER_ID
        request["score_schedule_utc"] = dict(self._manifest.worker_schedule)
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
        if not isinstance(eligible, list) or any(type(item) is not str for item in eligible):
            raise runner_v2.StrategySandboxError("score worker received invalid eligibility")
        raw_scores = response.get("scores")
        scheduled = self._manifest.scheduled(timestamp)
        if scheduled != (raw_scores is not None):
            raise runner_v2.StrategySandboxError("score capture differs from manifest schedule")
        if raw_scores is None:
            scores = None
        else:
            if not isinstance(raw_scores, Mapping):
                raise runner_v2.StrategySandboxError("score worker returned invalid scores")
            scores: dict[str, float] = {}
            for symbol, raw_score in raw_scores.items():
                if type(symbol) is not str or symbol not in eligible or isinstance(raw_score, bool):
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
        "crypto_trade.tournament._score_worker_v5",
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
) -> tuple[_CapturingClient, tempfile.TemporaryDirectory[str]]:
    repository_parent = runner_v2._runner_repository_parent()
    site_packages = runner_v2._current_venv_site_packages(repository_parent)
    sandbox = tempfile.TemporaryDirectory(prefix="top40-v2-development-score-worker-")
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
            expected_fingerprint=source.registration["source_bundle_sha256"],
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
        return _CapturingClient(client, manifest=source.manifest), sandbox
    except BaseException:
        if diagnostics is not None:
            diagnostics.close()
        sandbox.cleanup()
        raise


def _score_frame(
    captured: Mapping[pd.Timestamp, Mapping[str, float] | None],
    decision_times: pd.DatetimeIndex,
    manifest: ScoreAdapterManifest,
) -> pd.DataFrame:
    if set(captured) != set(decision_times):
        raise ValueError("score worker did not return every canonical decision")
    rows: list[dict[str, object]] = []
    scheduled_count = 0
    for timestamp in decision_times:
        value = pd.Timestamp(timestamp)
        scores = captured[value]
        if manifest.scheduled(value):
            scheduled_count += 1
            if scores is None:
                raise ValueError("scheduled decision lacks score-boundary capture")
            for symbol in sorted(scores):
                rows.append({"decision_time": value, "symbol": symbol, "score": scores[symbol]})
        elif scores is not None:
            raise ValueError("unscheduled decision contains score-boundary capture")
    if scheduled_count == 0:
        raise ValueError("manifest schedule selects no development decisions")
    frame = pd.DataFrame(rows, columns=("decision_time", "symbol", "score"))
    if frame.empty:
        raise ValueError("score replay produced no declared-score captures")
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
) -> _Replay:
    client, sandbox = _launch_score_worker(root, source, seed=seed)
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
        scores = _score_frame(client.captured, decision_times, source.manifest)
    except BaseException:
        client.abort()
        raise
    else:
        client.finish()
        return _Replay(targets=targets, scores=scores)
    finally:
        sandbox.cleanup()


def _fold(timestamp: pd.Timestamp) -> tuple[str, pd.Timestamp, pd.Timestamp] | None:
    value = (
        timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")
    )
    for fold_id, raw_start, raw_end in FOLDS:
        start = pd.Timestamp(raw_start)
        end = pd.Timestamp(raw_end)
        if start <= value < end:
            return fold_id, start, end
    return None


def _pearson(frame: pd.DataFrame, minimum_pairs: int) -> float | None:
    if len(frame) < minimum_pairs:
        return None
    scores = frame["score"].to_numpy(dtype=np.float64, copy=True)
    outcomes = frame["forward_return"].to_numpy(dtype=np.float64, copy=True)
    if not np.isfinite(scores).all() or not np.isfinite(outcomes).all():
        raise ValueError("Pearson inputs must be finite")
    score_centered = scores - scores.mean(dtype=np.float64)
    outcome_centered = outcomes - outcomes.mean(dtype=np.float64)
    denominator = math.sqrt(
        float(np.dot(score_centered, score_centered))
        * float(np.dot(outcome_centered, outcome_centered))
    )
    if not math.isfinite(denominator) or denominator <= 0.0:
        return None
    result = float(np.dot(score_centered, outcome_centered) / denominator)
    if not math.isfinite(result):
        return None
    return max(-1.0, min(1.0, result))


def label_score_panel(
    scores: pd.DataFrame,
    bars: pd.DataFrame,
    manifest: ScoreAdapterManifest,
) -> tuple[pd.DataFrame, Mapping[str, Any]]:
    if not {"decision_time", "symbol", "score"}.issubset(scores):
        raise ValueError("score panel lacks required columns")
    if not {"open_time", "symbol", "open"}.issubset(bars):
        raise ValueError("bar panel lacks executable opens")
    score_frame = scores.loc[:, ["decision_time", "symbol", "score"]].copy()
    score_frame["decision_time"] = pd.to_datetime(score_frame["decision_time"], utc=True)
    if score_frame.duplicated(["decision_time", "symbol"]).any():
        raise ValueError("score panel contains duplicate decision-symbol rows")
    if any(not manifest.scheduled(pd.Timestamp(value)) for value in score_frame["decision_time"]):
        raise ValueError("score panel contains a decision outside the manifest schedule")
    bar_frame = bars.loc[:, ["open_time", "symbol", "open"]].copy()
    bar_frame["open_time"] = pd.to_datetime(bar_frame["open_time"], utc=True)
    if bar_frame.duplicated(["open_time", "symbol"]).any():
        raise ValueError("bar panel contains duplicate executable opens")
    bar_frame["open"] = pd.to_numeric(bar_frame["open"], errors="coerce").astype(float)
    opens = bar_frame.set_index(["open_time", "symbol"])["open"]
    horizon = pd.Timedelta(hours=manifest.holding_horizon_hours)

    rows: list[dict[str, object]] = []
    purged_decisions = 0
    unavailable_labels = 0
    for decision_time, cross_section in score_frame.groupby(
        "decision_time", observed=True, sort=True
    ):
        timestamp = pd.Timestamp(decision_time)
        fold = _fold(timestamp)
        if fold is None:
            raise ValueError("score decision lies outside the six development folds")
        fold_id, _start, fold_end = fold
        label_end = timestamp + horizon
        if label_end >= fold_end:
            purged_decisions += 1
            continue
        for item in cross_section.sort_values("symbol").itertuples(index=False):
            start_open = opens.get((timestamp, str(item.symbol)), np.nan)
            end_open = opens.get((label_end, str(item.symbol)), np.nan)
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
        raise ValueError("no declared-score label pairs remain after fold purging")
    panel = panel.sort_values(["decision_time", "symbol"]).reset_index(drop=True)
    fold_values: dict[str, float | None] = {}
    fold_counts: dict[str, int] = {}
    for fold_id, _start, _end in FOLDS:
        subset = panel.loc[panel["fold_id"].eq(fold_id)]
        fold_counts[fold_id] = int(len(subset))
        fold_values[fold_id] = _pearson(subset, manifest.minimum_pairs)
    statistics = {
        "label_id": LABEL_ID,
        "statistic_id": STATISTIC_ID,
        "holding_horizon_hours": manifest.holding_horizon_hours,
        "minimum_pairs": manifest.minimum_pairs,
        "development_pair_count": int(len(panel)),
        "development_pearson": _pearson(panel, manifest.minimum_pairs),
        "fold_pair_counts": fold_counts,
        "fold_pearson": fold_values,
        "purged_fold_boundary_decision_count": purged_decisions,
        "unavailable_symbol_label_count": unavailable_labels,
        "qualification_gate": False,
    }
    return panel, statistics


def _verify_runner_record(
    root: Path,
    request: DevelopmentScoreDiagnosticRequest,
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
        "stage": STAGE,
        "team_id": request.team_id,
        "strategy_sha256": registration["strategy_sha256"],
        "risk_policy_sha256": registration["risk_config_sha256"],
        "source_bundle_sha256": registration["source_bundle_sha256"],
        "config_sha256": request.config_sha256,
        "data_manifest_sha256": request.snapshot_manifest_sha256,
    }
    if any(record.get(field) != value for field, value in expected.items()):
        raise ValueError("completed runner record differs from development authority")
    if record.get("seeds") != [request.candidate_seed]:
        raise ValueError("completed runner seed differs from preregistration")
    artifacts = record.get("artifact_sha256")
    if (
        not isinstance(artifacts, Mapping)
        or artifacts.get("targets") != request.development_target_sha256
    ):
        raise ValueError("completed runner record does not bind development targets")


def _evidence_relative(request: DevelopmentScoreDiagnosticRequest) -> str:
    return (
        f"{TOP40_V2_LAYOUT.report_root(request.team_id)}/"
        f"development-score-diagnostics/{request.candidate_id}"
    )


def _safe_directory_chain(root: Path, directory: Path) -> None:
    relative = directory.relative_to(root)
    safe_relative(relative.as_posix(), "declared-score staging parent")
    root_info = os.lstat(root)
    if (
        not stat.S_ISDIR(root_info.st_mode)
        or stat.S_ISLNK(root_info.st_mode)
        or root_info.st_uid != os.geteuid()
    ):
        raise ValueError("declared-score worktree root is unsafe")
    current = root
    for part in relative.parts:
        current /= part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            os.mkdir(current, 0o755)
            fsync_directory(current.parent)
            info = os.lstat(current)
        if not os.path.isdir(current) or os.path.islink(current) or info.st_uid != os.geteuid():
            raise ValueError("declared-score staging ancestor is unsafe")


def stage_diagnostic_artifacts(
    root: Path,
    request: DevelopmentScoreDiagnosticRequest,
    artifacts: Mapping[str, bytes],
) -> Mapping[str, str]:
    """Stage an exact artifact set behind an unguessable internally generated capability."""

    if artifacts and set(artifacts) != set(REQUIRED_ARTIFACT_NAMES):
        raise ValueError("development declared-score artifact set is incomplete")
    if any(len(payload) > _MAX_ARTIFACT_BYTES for payload in artifacts.values()):
        raise ValueError("development declared-score artifact exceeds size ceiling")
    parent = root / Path(_evidence_relative(request)).parent
    _safe_directory_chain(root, parent)
    token = os.urandom(32).hex()
    stage = parent / f".{request.candidate_id}.{token}.staged"
    os.mkdir(stage, 0o700)
    try:
        for name, payload in artifacts.items():
            atomic_write_bytes(stage / name, payload, mode=0o600)
        fsync_directory(stage)
    except BaseException:
        shutil.rmtree(stage)
        raise
    return {
        "capability": token,
        "staging_path": stage.relative_to(root).as_posix(),
    }


def validate_staged_artifacts(
    root: Path,
    request: DevelopmentScoreDiagnosticRequest,
    capability: Mapping[str, str],
    *,
    completed: bool,
) -> tuple[Path, Mapping[str, str]]:
    if set(capability) != {"capability", "staging_path"}:
        raise ValueError("declared-score staging capability has invalid keys")
    token = capability["capability"]
    if (
        type(token) is not str
        or len(token) != 64
        or any(character not in "0123456789abcdef" for character in token)
    ):
        raise ValueError("declared-score staging capability is invalid")
    expected = (
        Path(_evidence_relative(request)).parent / f".{request.candidate_id}.{token}.staged"
    ).as_posix()
    if capability["staging_path"] != expected:
        raise ValueError("declared-score staging path is not internally derived")
    stage = root / expected
    _safe_directory_chain(root, stage.parent)
    info = os.lstat(stage)
    if (
        not os.path.isdir(stage)
        or os.path.islink(stage)
        or info.st_uid != os.geteuid()
        or info.st_mode & 0o077
    ):
        raise ValueError("declared-score staging directory is unsafe")
    expected_names = set(REQUIRED_ARTIFACT_NAMES) if completed else set()
    if {entry.name for entry in os.scandir(stage)} != expected_names:
        raise ValueError("declared-score staged artifact set differs")
    hashes: dict[str, str] = {}
    for name in sorted(expected_names):
        path = stage / name
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        try:
            before = os.fstat(descriptor)
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size > _MAX_ARTIFACT_BYTES
            ):
                raise ValueError("declared-score staged artifact is unsafe")
            payload = b""
            while len(payload) < before.st_size:
                chunk = os.read(descriptor, min(1024 * 1024, before.st_size - len(payload)))
                if not chunk:
                    raise ValueError("declared-score staged artifact truncated while read")
                payload += chunk
            if os.read(descriptor, 1) or os.fstat(descriptor).st_size != before.st_size:
                raise ValueError("declared-score staged artifact grew while read")
        finally:
            os.close(descriptor)
        hashes[f"{_evidence_relative(request)}/{name}"] = sha256_bytes(payload)
    return stage, hashes


def run_development_score_diagnostic(
    root: str | Path,
    config: LoadedV2Config,
    request: DevelopmentScoreDiagnosticRequest,
) -> Mapping[str, bytes]:
    root_path = Path(root).resolve()
    verify_frozen_science_helper_identities()
    _request_paths(request)
    if config.sha256 != request.config_sha256:
        raise ValueError("diagnostic request config binding differs")
    if request.snapshot_manifest_path != str(config.raw["paths"]["shared_snapshot_manifest"]):
        raise ValueError("diagnostic may use only the shared development snapshot")
    manifest_relative = safe_relative(request.snapshot_manifest_path, "snapshot manifest")
    _manifest_relative, manifest_path, manifest_bytes, _manifest_stat = read_repo_file(
        root_path,
        manifest_relative,
        "development snapshot manifest",
        maximum_bytes=32 * 1024 * 1024,
        require_single_link=True,
    )
    if (
        _exact_regular_bytes(
            manifest_path,
            maximum_bytes=32 * 1024 * 1024,
            label="development snapshot manifest",
        )
        != manifest_bytes
    ):
        raise ValueError("development snapshot manifest changed during initial read")
    if sha256_bytes(manifest_bytes) != request.snapshot_manifest_sha256:
        raise ValueError("development snapshot manifest hash differs")
    _target_relative, _target_path, target_bytes, _target_stat = read_repo_file(
        root_path,
        request.development_target_path,
        "completed development targets",
        maximum_bytes=16 * 1024 * 1024,
        require_single_link=True,
    )
    if sha256_bytes(target_bytes) != request.development_target_sha256:
        raise ValueError("completed development target hash differs")

    with materialized_historical_source(root_path, config, request) as historical:
        _verify_runner_record(root_path, request, historical.registration)
        snapshot = runner_v2._load_verified_snapshot(root_path, manifest_path)
        authorized = runner_v2._authorized_window(config.raw, STAGE)
        if authorized.stage != STAGE:
            raise ValueError("diagnostic selected a non-development window")
        decision_times = runner_v2._decision_grid(authorized)
        expected_anchor = pd.Timestamp(decision_times[0])
        if pd.Timestamp(historical.manifest.anchor_timestamp_utc) != expected_anchor:
            raise ValueError("score schedule anchor must equal the first development decision")
        runner_v2._validate_snapshot_bounds(snapshot, config.raw, decision_times)
        end = pd.Timestamp(authorized.end_exclusive, tz="UTC")
        bars = snapshot.bars.loc[pd.to_datetime(snapshot.bars["open_time"], utc=True) < end].copy()
        funding = snapshot.funding.loc[
            pd.to_datetime(snapshot.funding["funding_time"], utc=True) < end
        ].copy()
        membership = snapshot.membership.loc[
            pd.to_datetime(snapshot.membership["reconstitution_time"], utc=True) < end
        ].copy()
        before_hashes = _A1_SNAPSHOT_HASHES(snapshot, root_path)
        canonical_targets = _A1_TARGET_FROM_BYTES(target_bytes, bars, decision_times)
        seed = int(historical.registration["seed"])
        first = _run_replay(
            root_path,
            historical,
            bars=bars,
            funding=funding,
            membership=membership,
            decision_times=decision_times,
            seed=seed,
        )
        second = _run_replay(
            root_path,
            historical,
            bars=bars,
            funding=funding,
            membership=membership,
            decision_times=decision_times,
            seed=seed,
        )
        replay_targets_exact = _A1_TARGETS_EXACT(first.targets, second.targets)
        replay_scores_exact = _A1_SCORES_EXACT(first.scores, second.scores)
        canonical_first_exact = _A1_TARGETS_EXACT(first.targets, canonical_targets)
        canonical_second_exact = _A1_TARGETS_EXACT(second.targets, canonical_targets)
        if not (
            replay_targets_exact
            and replay_scores_exact
            and canonical_first_exact
            and canonical_second_exact
        ):
            raise ValueError("score or target replay differs from immutable development evidence")
        panel, statistics = label_score_panel(first.scores, bars, historical.manifest)
        after_hashes = _A1_SNAPSHOT_HASHES(snapshot, root_path)
        if after_hashes != before_hashes:
            raise ValueError("development snapshot changed during diagnostics")
        _after_relative, _after_path, after_manifest_bytes, _after_stat = read_repo_file(
            root_path,
            manifest_relative,
            "development snapshot manifest after replay",
            maximum_bytes=32 * 1024 * 1024,
            require_single_link=True,
        )
        if after_manifest_bytes != manifest_bytes:
            raise ValueError("development snapshot manifest changed during diagnostics")
        if (
            _exact_regular_bytes(
                manifest_path,
                maximum_bytes=32 * 1024 * 1024,
                label="development snapshot manifest after replay",
            )
            != manifest_bytes
        ):
            raise ValueError("development snapshot manifest grew during diagnostics")
        verify_frozen_science_helper_identities()
        summary = {
            "schema_version": 1,
            "diagnostic_kind": DIAGNOSTIC_KIND,
            "stage": STAGE,
            "team_id": request.team_id,
            "family_id": request.family_id,
            "candidate_id": request.candidate_id,
            "diagnostic_id": request.diagnostic_id,
            "reservation_sha256": request.reservation_sha256,
            "score_manifest_sha256": request.score_manifest_sha256,
            "score_manifest_commit": request.score_manifest_commit,
            "semantic_coupling_review_sha256": request.semantic_coupling_review_sha256,
            "semantic_coupling_review_commit": request.semantic_coupling_review_commit,
            "registration_sha256": request.registration_sha256,
            "registration_commit": historical.binding.registration_commit,
            "source_tree_manifest_sha256": historical.binding.source_tree_manifest_sha256,
            "replay": {
                "targets_identical": replay_targets_exact,
                "scores_identical": replay_scores_exact,
                "canonical_targets_replay_1_exact": canonical_first_exact,
                "canonical_targets_replay_2_exact": canonical_second_exact,
                "target_digest": _A1_TARGET_DIGEST(first.targets),
                "score_digest": _A1_SCORE_DIGEST(first.scores),
            },
            "statistics": statistics,
            "declared_score_diagnostic_only": True,
            "runtime_semantic_coupling_proved": False,
            "semantic_coupling_evidence_kind": "hash-bound-static-source-review",
            "automatic_qualification_gate": False,
        }
        artifacts = {
            "diagnostic-summary.json": _pretty_json_bytes(summary),
            "labeled-score-panel.parquet": _A1_PARQUET_BYTES(panel),
            "replay-1-scores.parquet": _A1_PARQUET_BYTES(first.scores),
            "replay-1-targets.parquet": _A1_PARQUET_BYTES(_A1_INDEXED_TARGETS(first.targets)),
            "replay-2-scores.parquet": _A1_PARQUET_BYTES(second.scores),
            "replay-2-targets.parquet": _A1_PARQUET_BYTES(_A1_INDEXED_TARGETS(second.targets)),
        }
        return artifacts


def _resource_snapshot() -> tuple[float, float]:
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    return time.process_time() + children.ru_utime + children.ru_stime, time.monotonic()


def _resource_delta(before: tuple[float, float]) -> tuple[float, float]:
    children = resource.getrusage(resource.RUSAGE_CHILDREN)
    cpu = time.process_time() + children.ru_utime + children.ru_stime
    return max(0.0, (cpu - before[0]) / 3600.0), max(0.0, (time.monotonic() - before[1]) / 3600.0)


def run_reserved_development_score_diagnostic(
    *,
    root: Path,
    request: DevelopmentScoreDiagnosticRequest,
) -> Mapping[str, Any]:
    """A2-compatible boundary with no caller-selected stage, data, or output path."""

    usage = _resource_snapshot()
    root_path = Path(root).resolve()
    artifacts: Mapping[str, bytes] = {}
    try:
        config = load_v2_config(root_path / TOP40_V2_LAYOUT.config_path)
        artifacts = run_development_score_diagnostic(
            root_path,
            config,
            request,
        )
    except BaseException as exc:
        cpu_hours, wall_hours = _resource_delta(usage)
        outcome: dict[str, Any] = {
            "status": "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed",
            "failure_reason": f"{type(exc).__name__}: {exc}"[:8000],
            "organizer_cpu_hours": cpu_hours,
            "organizer_wall_clock_hours": wall_hours,
        }
    else:
        cpu_hours, wall_hours = _resource_delta(usage)
        outcome = {
            "status": "completed",
            "failure_reason": None,
            "organizer_cpu_hours": cpu_hours,
            "organizer_wall_clock_hours": wall_hours,
        }
    capability = stage_diagnostic_artifacts(root_path, request, artifacts)
    return {**outcome, "staged_artifacts": capability}
