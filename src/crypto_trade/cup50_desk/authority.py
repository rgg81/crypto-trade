"""Fail-closed deployment authority for the CUP-50 Team-02 paper lineage."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.cup50.config import load_config
from crypto_trade.cup50.paper import verify_desk_authority

WINNER_TEAM_ID = "team-02"
WINNER_CANDIDATE_ID = "centre-v1"
SCHEMA_VERSION = 1


class DeploymentChangedError(RuntimeError):
    """A byte used by the frozen desk differs from its deployment manifest."""


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_sha256(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode()
    ).hexdigest()


def paper_root(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "paper-cup50" / WINNER_TEAM_ID


def winner_bundle(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "tournament" / "cup50" / "teams" / WINNER_TEAM_ID


def corrected_release(root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "reports-cup50" / "corrected-leaderboard.json"


def verify_lineage(root: str | Path | None = None) -> Mapping[str, object]:
    base = Path(root).resolve() if root is not None else repository_root()
    release_path = corrected_release(base)
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if release.get("winner_team_id") != WINNER_TEAM_ID:
        raise DeploymentChangedError(
            f"corrected release no longer names {WINNER_TEAM_ID} as winner"
        )
    config = load_config(base / "tournament" / "cup50" / "config.toml")
    authority = verify_desk_authority(
        paper_root(base) / "authority.json",
        release_path=release_path,
        winner_bundle=winner_bundle(base),
    )
    if authority.get("public_data_only") is not True:
        raise DeploymentChangedError("paper authority is not public-data-only")
    nomination = json.loads(
        (base / "tournament" / "cup50" / "nominations" / "team-02.json").read_text()
    )
    if authority.get("nomination_sha256") != nomination.get("freeze_sha256"):
        raise DeploymentChangedError("paper authority nomination binding drifted")
    if nomination.get("centre") != {"lookback_bars": 189.0}:
        raise DeploymentChangedError("Team-02 centre parameters drifted")
    reconstruction = json.loads((paper_root(base) / "reconstruction.json").read_text())
    if (
        reconstruction.get("parity") is not True
        or reconstruction.get("winner_team_id") != WINNER_TEAM_ID
        or reconstruction.get("lineage_sha256") != authority.get("lineage_sha256")
    ):
        raise DeploymentChangedError("historical reconstruction is not the frozen winner")
    return {
        "authority": authority,
        "config_sha256": config.sha256,
        "nomination": nomination,
        "reconstruction": reconstruction,
    }


def _safe_bound_path(base: Path, relative: object) -> Path:
    if not isinstance(relative, str):
        raise DeploymentChangedError("deployment artifact path is not a string")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise DeploymentChangedError(f"unsafe deployment artifact path: {relative!r}")
    resolved = (base / path).resolve()
    if not resolved.is_relative_to(base):
        raise DeploymentChangedError(f"deployment artifact escapes repository: {relative!r}")
    return resolved


def verify_deployment(root: str | Path | None = None) -> Mapping[str, Any]:
    """Verify lineage plus every engine/data byte bound at activation."""
    base = Path(root).resolve() if root is not None else repository_root()
    verify_lineage(base)
    path = paper_root(base) / "deployment-manifest.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != SCHEMA_VERSION:
        raise DeploymentChangedError("unknown CUP-50 desk deployment schema")
    recorded = payload.get("manifest_sha256")
    body = {key: value for key, value in payload.items() if key != "manifest_sha256"}
    if recorded != canonical_sha256(body):
        raise DeploymentChangedError("deployment manifest digest mismatch")
    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise DeploymentChangedError("deployment manifest has no artifacts")
    for relative, expected in artifacts.items():
        artifact = _safe_bound_path(base, relative)
        if not artifact.is_file():
            raise DeploymentChangedError(f"bound deployment artifact is missing: {relative}")
        observed = sha256_file(artifact)
        if observed != expected:
            raise DeploymentChangedError(
                f"bound deployment artifact drifted: {relative}: {observed} != {expected}"
            )
    if payload.get("lineage_sha256") != verify_lineage(base)["authority"]["lineage_sha256"]:
        raise DeploymentChangedError("deployment manifest binds another paper lineage")
    return payload


def build_deployment_manifest(
    artifact_paths: Sequence[str | Path],
    *,
    root: str | Path | None = None,
    git_commit: str,
) -> Mapping[str, Any]:
    """Create the immutable activation record once, after all verification has passed."""
    base = Path(root).resolve() if root is not None else repository_root()
    destination = paper_root(base) / "deployment-manifest.json"
    if destination.exists():
        raise FileExistsError(destination)
    lineage = verify_lineage(base)
    artifacts: dict[str, str] = {}
    for raw in artifact_paths:
        path = Path(raw)
        path = path.resolve() if path.is_absolute() else (base / path).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError(f"deployment artifact is outside repository or missing: {raw}")
        artifacts[path.relative_to(base).as_posix()] = sha256_file(path)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "namespace": "cup50-team02-paper-deployment",
        "team_id": WINNER_TEAM_ID,
        "candidate_id": WINNER_CANDIDATE_ID,
        "lineage_sha256": lineage["authority"]["lineage_sha256"],
        "git_commit": git_commit,
        "public_data_only": True,
        "exact_replay": True,
        "artifacts": dict(sorted(artifacts.items())),
    }
    record = {**body, "manifest_sha256": canonical_sha256(body)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record
