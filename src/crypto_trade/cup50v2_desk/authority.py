"""Fail-closed deployment authority for a CUP-50 v2 paper desk.

CUP-50's desk hard-coded its winner in module constants -- team id, candidate id, centre
parameters, and the paths built from them. That is correct for one desk and impossible for four.
CUP-50 v2 runs the winner, two runners-up and an equal-risk ensemble in parallel precisely because
IS-to-OOS-to-forward rank instability is the documented failure mode, so the desk identity has to
be data, not code. A :class:`Desk` is read from ``paper-cup50v2/<desk_id>/desk.json`` and threaded
through every function that used to reach for a constant.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from crypto_trade.cup50v2.config import load_config
from crypto_trade.cup50v2.paper import verify_desk_authority

SCHEMA_VERSION = 1
DESK_SCHEMA_VERSION = 1


@dataclasses.dataclass(frozen=True)
class Desk:
    """Which lane a desk replays, and the exact centre it replays it at."""

    desk_id: str
    team_id: str
    candidate_id: str
    centre: Mapping[str, float]
    nomination_sha256: str

    def __post_init__(self) -> None:
        if not self.desk_id or "/" in self.desk_id or ".." in self.desk_id:
            raise ValueError(f"unsafe desk id: {self.desk_id!r}")
        if len(self.nomination_sha256) != 64:
            raise ValueError("desk nomination_sha256 must be a SHA-256")
        if not self.centre:
            raise ValueError("a desk must name the centre it replays")


def load_desk(desk_id: str, root: str | Path | None = None) -> Desk:
    """Read a desk's identity from its own directory, never from a module constant."""
    base = Path(root).resolve() if root is not None else repository_root()
    if not desk_id or "/" in desk_id or ".." in desk_id:
        raise ValueError(f"unsafe desk id: {desk_id!r}")
    payload = json.loads((base / "paper-cup50v2" / desk_id / "desk.json").read_text())
    if payload.get("schema_version") != DESK_SCHEMA_VERSION:
        raise DeploymentChangedError("unknown CUP-50 v2 desk schema")
    return Desk(
        desk_id=str(payload["desk_id"]),
        team_id=str(payload["team_id"]),
        candidate_id=str(payload["candidate_id"]),
        centre={str(k): float(v) for k, v in dict(payload["centre"]).items()},
        nomination_sha256=str(payload["nomination_sha256"]),
    )


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


def paper_root(desk: Desk, root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "paper-cup50v2" / desk.desk_id


def desk_bundle(desk: Desk, root: str | Path | None = None) -> Path:
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "tournament" / "cup50v2" / "teams" / desk.team_id


def release_path(root: str | Path | None = None) -> Path:
    """The released leaderboard. CUP-50 needed a *corrected* one; this edition must not.

    The correction existed because CUP-50 changed its winner after the sealed read. CUP-50 v2
    pre-registers the qualification bar and the winner rule and freezes both before observation,
    so there is one release and no corrected successor. A desk that ever needs one is a desk whose
    edition broke its own amendment rule.
    """
    base = Path(root).resolve() if root is not None else repository_root()
    return base / "reports-cup50v2" / "leaderboard.json"


def verify_lineage(desk: Desk, root: str | Path | None = None) -> Mapping[str, object]:
    base = Path(root).resolve() if root is not None else repository_root()
    released = release_path(base)
    release = json.loads(released.read_text(encoding="utf-8"))
    if desk.team_id not in {str(entry.get("team_id")) for entry in release.get("entries", [])}:
        raise DeploymentChangedError(f"release does not rank {desk.team_id}")
    config = load_config(base / "tournament" / "cup50v2" / "config.toml")
    authority = verify_desk_authority(
        paper_root(desk, base) / "authority.json",
        release_path=released,
        winner_bundle=desk_bundle(desk, base),
    )
    if authority.get("public_data_only") is not True:
        raise DeploymentChangedError("paper authority is not public-data-only")
    nomination = json.loads(
        (base / "tournament" / "cup50v2" / "nominations" / f"{desk.team_id}.json").read_text()
    )
    if authority.get("nomination_sha256") != nomination.get("freeze_sha256"):
        raise DeploymentChangedError("paper authority nomination binding drifted")
    if nomination.get("freeze_sha256") != desk.nomination_sha256:
        raise DeploymentChangedError(f"{desk.desk_id} binds a nomination the lane did not freeze")
    # The centre is the desk's own, compared against the frozen neighbourhood rather than a
    # literal: a hard-coded centre is what made CUP-50's desk single-tenant in the first place.
    if {str(k): float(v) for k, v in nomination.get("centre", {}).items()} != dict(desk.centre):
        raise DeploymentChangedError(f"{desk.desk_id} centre parameters drifted")
    reconstruction = json.loads((paper_root(desk, base) / "reconstruction.json").read_text())
    if (
        reconstruction.get("parity") is not True
        or reconstruction.get("team_id") != desk.team_id
        or reconstruction.get("lineage_sha256") != authority.get("lineage_sha256")
    ):
        raise DeploymentChangedError("historical reconstruction is not this desk's frozen lane")
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


def verify_deployment(desk: Desk, root: str | Path | None = None) -> Mapping[str, Any]:
    """Verify lineage plus every engine/data byte bound at activation."""
    base = Path(root).resolve() if root is not None else repository_root()
    verify_lineage(desk, base)
    path = paper_root(desk, base) / "deployment-manifest.json"
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
    if payload.get("lineage_sha256") != verify_lineage(desk, base)["authority"]["lineage_sha256"]:
        raise DeploymentChangedError("deployment manifest binds another paper lineage")
    return payload


def build_deployment_manifest(
    desk: Desk,
    artifact_paths: Sequence[str | Path],
    *,
    root: str | Path | None = None,
    git_commit: str,
) -> Mapping[str, Any]:
    """Create the immutable activation record once, after all verification has passed."""
    base = Path(root).resolve() if root is not None else repository_root()
    destination = paper_root(desk, base) / "deployment-manifest.json"
    if destination.exists():
        raise FileExistsError(destination)
    lineage = verify_lineage(desk, base)
    artifacts: dict[str, str] = {}
    for raw in artifact_paths:
        path = Path(raw)
        path = path.resolve() if path.is_absolute() else (base / path).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError(f"deployment artifact is outside repository or missing: {raw}")
        artifacts[path.relative_to(base).as_posix()] = sha256_file(path)
    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "namespace": f"cup50v2-{desk.desk_id}-paper-deployment",
        "desk_id": desk.desk_id,
        "team_id": desk.team_id,
        "candidate_id": desk.candidate_id,
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
