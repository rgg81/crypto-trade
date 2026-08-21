"""Fail-closed research clean-room checks for Top-40 V4 edition 2."""

from __future__ import annotations

import json
import os
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path

from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

ACCESS_SCHEMA_VERSION = 2
ATTESTATION_FILENAME = "cleanroom-attestation.json"

TEAM_KIT_ROOT = "tournament/top40-v4-r2/team-kit"
RESEARCH_SESSION_ROOT = "tournament/top40-v4-r2/research-sessions"
_TEAM_KIT_FILES = (
    "ADMISSION-CHECKER.md",
    "RULES.md",
    "STRATEGY-API.md",
    "admission-call-allowlist.json",
    "templates/candidate.json",
    "templates/cleanroom-attestation.json",
    "templates/research-certificate.json",
    "templates/risk-policy.json",
    "templates/strategy.py",
)
_DENY_CATEGORIES = (
    "other-team-workspaces",
    "prior-tournament-artifacts",
    "sealed-organizer-data",
    "repository-history",
    "legacy-research-and-reports",
)
_PROHIBITED_CANDIDATE_MARKERS = (
    b"TOURNAMENT-CHARTER-TOP40-V4-R1",
    b"tournament/top40-v4-r1",
    b"reports-top40-v4-r1",
    b"tournament/top40-v3",
    b"reports-top40-v3",
    b"tournament/top40-v2",
    b"reports-top40-v2",
    b"tournament/top40/teams",
    b"reports-top40/team-",
    b"briefs-portfolio-",
    b"diary-portfolio-",
    b"analysis/portfolio/iter_",
    b"ORCHESTRATOR_BRIEF",
)
_TEXT_SUFFIXES = frozenset(
    {".json", ".jsonl", ".lock", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
)


class IsolationError(ValueError):
    """A team-facing surface or candidate violated the clean-room contract."""


def access_policy(team_id: str) -> dict[str, object]:
    TOP40_V4_LAYOUT.require_team(team_id)
    team_root = TOP40_V4_LAYOUT.team_root(team_id)
    return {
        "schema_version": ACCESS_SCHEMA_VERSION,
        "tournament": TOP40_V4_LAYOUT.name,
        "team_id": team_id,
        "default_access": "deny",
        "read_allowlist": [
            f"{TEAM_KIT_ROOT}/",
            f"{team_root}/ACCESS-POLICY.json",
            f"{team_root}/TEAM-BRIEF.md",
            f"{team_root}/candidates/",
            f"{team_root}/feedback/",
            f"{team_root}/work/",
            f"{team_root}/outbox/",
        ],
        "write_allowlist": [
            f"{team_root}/candidates/",
            f"{team_root}/work/",
            f"{team_root}/outbox/",
        ],
        "deny_categories": list(_DENY_CATEGORIES),
        "network_during_research": False,
        "network_during_official_runs": False,
        "research_process": "ephemeral-os-enforced-permission-profile",
        "organizer_broker": "offline-asynchronous-lane-local-results",
        "sealed_stage_feedback": "atomic-cohort-release-only",
        "candidate_cleanroom_attestation_required": True,
    }


def team_brief(team_id: str) -> str:
    TOP40_V4_LAYOUT.require_team(team_id)
    return f"""# Independent research lane {team_id}

You own one strategy-neutral lane. Choose your own causal economic mechanism; no alpha family is
assigned and no result is implied. Work only from the organizer-supplied team kit and causal
market reasoning already available to you before this session.

The OS-enforced permission profile makes `ACCESS-POLICY.json` the complete readable and writable
surface. Every unlisted path and all command networking are unavailable. Do not request access to
another lane, repository history, legacy research, organizer-private state, sealed rows, or the
public internet. No host, system, user, plugin, or external skill is available to this session.
Do not use remembered post-cutoff prices, results, or precomputed strategies.

Before any official run, create a new candidate directory under `candidates/` containing
`candidate.json`, `strategy.py`, `risk_policy.json`, `README.md`, and
`cleanroom-attestation.json`. Put broker requests only in `outbox/`. The attestation is an
integrity statement, not a substitute for organizer-side causal review. Every accepted material
trial consumes one slot, including runtime failures.

Start from the supplied accepted strategy template and follow `ADMISSION-CHECKER.md` literally.
If the organizer places an `admission-*.json` report in `feedback/`, it contains only score-blind
deterministic findings; repair the complete unaccepted batch in place before finishing again.

The team process exits before the organizer evaluates a batch. A later clean-room session receives
only this lane's normalized feedback. Never infer sealed performance from timing, errors,
progress, or another lane. A negative result is valid evidence. There is no requirement to
nominate and no guaranteed winner.
"""


def _regular_bytes(path: Path, label: str, maximum: int = 2 * 1024 * 1024) -> bytes:
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_size > maximum
            ):
                raise IsolationError(f"{label} is not a bounded regular file")
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        current = path.lstat()
    except OSError as exc:
        raise IsolationError(f"cannot read {label}") from exc
    identities = (
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink),
        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink),
        (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns, current.st_nlink),
    )
    if (
        len(set(identities)) != 1
        or not stat.S_ISREG(current.st_mode)
        or current.st_nlink != 1
        or len(payload) > maximum
    ):
        raise IsolationError(f"{label} changed while being read")
    return payload


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ).encode("ascii") + b"\n"


def _audit_team_surface(root_path: Path, team_id: str) -> None:
    TOP40_V4_LAYOUT.require_team(team_id)
    team_root = root_path / TOP40_V4_LAYOUT.team_root(team_id)
    if team_root.is_symlink() or not team_root.is_dir():
        raise IsolationError(f"team clean-room root is missing or unsafe: {team_id}")
    policy_path = team_root / "ACCESS-POLICY.json"
    brief_path = team_root / "TEAM-BRIEF.md"
    if _regular_bytes(policy_path, f"{team_id} access policy") != _canonical_json(
        access_policy(team_id)
    ):
        raise IsolationError(f"{team_id} access policy differs from the frozen surface")
    if _regular_bytes(brief_path, f"{team_id} brief") != team_brief(team_id).encode("utf-8"):
        raise IsolationError(f"{team_id} brief differs from the frozen surface")
    for directory_name in ("candidates", "feedback", "outbox", "work"):
        directory = team_root / directory_name
        if directory.is_symlink() or not directory.is_dir():
            raise IsolationError(f"{team_id} {directory_name} root is missing or unsafe")
    candidates = team_root / "candidates"
    for candidate_path in candidates.rglob("*"):
        metadata = candidate_path.lstat()
        if stat.S_ISLNK(metadata.st_mode):
            raise IsolationError(f"{team_id} candidate tree contains a symlink")
        if candidate_path.is_dir():
            continue
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise IsolationError(f"{team_id} candidate tree contains an unsafe file")
        if candidate_path.suffix.lower() not in _TEXT_SUFFIXES:
            raise IsolationError(f"{team_id} candidate tree contains an opaque file")
        payload = _regular_bytes(candidate_path, f"{team_id} candidate file")
        if any(marker in payload for marker in _PROHIBITED_CANDIDATE_MARKERS):
            raise IsolationError(f"{team_id} candidate cites a prohibited artifact")


def audit_team_surface(root: str | Path, team_id: str) -> dict[str, object]:
    """Verify one identity-bound lane without touching any peer lane."""

    if not TOP40_V4_LAYOUT.name.endswith("-r2"):
        return {"ok": True, "applicable": False, "tournament": TOP40_V4_LAYOUT.name}
    _audit_team_surface(Path(root).resolve(), team_id)
    return {"ok": True, "applicable": True, "tournament": TOP40_V4_LAYOUT.name}


def audit_surface(root: str | Path) -> dict[str, object]:
    """Organizer-only verification of all 15 physical clean-room roots."""

    if not TOP40_V4_LAYOUT.name.endswith("-r2"):
        return {"ok": True, "applicable": False, "tournament": TOP40_V4_LAYOUT.name}
    root_path = Path(root).resolve()
    kit_root = root_path / TEAM_KIT_ROOT
    if kit_root.is_symlink() or not kit_root.is_dir():
        raise IsolationError("team kit root is missing or unsafe")
    for relative in _TEAM_KIT_FILES:
        _regular_bytes(kit_root / relative, f"team kit {relative}")
    for team_id in TOP40_V4_LAYOUT.team_ids:
        _audit_team_surface(root_path, team_id)
    return {
        "ok": True,
        "applicable": True,
        "tournament": TOP40_V4_LAYOUT.name,
        "team_count": len(TOP40_V4_LAYOUT.team_ids),
    }


def validate_captured_candidate(
    *,
    team_id: str,
    candidate_id: str,
    candidate_root: str,
    files: Sequence[object],
) -> Mapping[str, object]:
    """Validate policy and attestation against the exact immutable captured bytes."""

    if not TOP40_V4_LAYOUT.name.endswith("-r2"):
        return {}
    TOP40_V4_LAYOUT.require_team(team_id)
    expected_root = f"{TOP40_V4_LAYOUT.team_root(team_id)}/candidates/{candidate_id}"
    if candidate_root != expected_root:
        raise IsolationError("captured candidate root differs from its team identity")
    by_path: dict[str, bytes] = {}
    for item in files:
        relative = getattr(item, "path", None)
        payload = getattr(item, "content", None)
        if not isinstance(relative, str) or not isinstance(payload, bytes) or relative in by_path:
            raise IsolationError("captured candidate file set is invalid")
        by_path[relative] = payload
        if any(marker in payload for marker in _PROHIBITED_CANDIDATE_MARKERS):
            raise IsolationError("captured candidate cites a prohibited artifact")
    payload = by_path.get(ATTESTATION_FILENAME)
    if payload is None:
        raise IsolationError("captured candidate clean-room attestation is missing")
    try:
        value = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IsolationError("captured candidate clean-room attestation is invalid JSON") from exc
    expected = {
        "schema_version": 1,
        "tournament": TOP40_V4_LAYOUT.name,
        "team_id": team_id,
        "candidate_id": candidate_id,
        "access_policy_followed": True,
        "other_team_artifacts_accessed": False,
        "legacy_tournament_artifacts_accessed": False,
        "sealed_data_accessed": False,
        "timestamp_target_table_embedded": False,
    }
    if not isinstance(value, Mapping) or dict(value) != expected:
        raise IsolationError("captured candidate clean-room attestation is missing or false")
    return value


def validate_candidate_attestation(
    root: str | Path,
    *,
    team_id: str,
    candidate_id: str,
    candidate_root: str | Path,
) -> Mapping[str, object]:
    """Require one exact, candidate-local clean-room attestation before source capture."""

    if not TOP40_V4_LAYOUT.name.endswith("-r2"):
        return {}
    TOP40_V4_LAYOUT.require_team(team_id)
    expected = {
        "schema_version": 1,
        "tournament": TOP40_V4_LAYOUT.name,
        "team_id": team_id,
        "candidate_id": candidate_id,
        "access_policy_followed": True,
        "other_team_artifacts_accessed": False,
        "legacy_tournament_artifacts_accessed": False,
        "sealed_data_accessed": False,
        "timestamp_target_table_embedded": False,
    }
    root_path = Path(root).resolve()
    candidate_path = Path(candidate_root).resolve()
    expected_parent = (root_path / TOP40_V4_LAYOUT.team_root(team_id) / "candidates").resolve()
    if candidate_path.parent != expected_parent or candidate_path.name != candidate_id:
        raise IsolationError("candidate attestation root differs from its team identity")
    attestation_path = candidate_path / ATTESTATION_FILENAME
    payload = _regular_bytes(attestation_path, "candidate clean-room attestation")
    try:
        value = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IsolationError("candidate clean-room attestation is invalid JSON") from exc
    if not isinstance(value, Mapping) or dict(value) != expected:
        raise IsolationError("candidate clean-room attestation is missing or false")
    return value


__all__ = [
    "ACCESS_SCHEMA_VERSION",
    "ATTESTATION_FILENAME",
    "IsolationError",
    "RESEARCH_SESSION_ROOT",
    "TEAM_KIT_ROOT",
    "access_policy",
    "audit_surface",
    "audit_team_surface",
    "team_brief",
    "validate_captured_candidate",
    "validate_candidate_attestation",
]
