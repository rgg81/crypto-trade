"""One-time hash freeze for the Top-40 V4 tournament infrastructure."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import stat
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from crypto_trade.tournament import (
    journal_v4,
    pure_crypto_universe_v4_r2,
    pure_crypto_universe_v6,
    snapshot,
    top40_v4,
)
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

_IS_R2 = TOP40_V4_LAYOUT.name.endswith("-r2")
_SCHEMA_PREFIX = TOP40_V4_LAYOUT.name if _IS_R2 else "top40-v4-r1"
SCHEMA_VERSION = f"{_SCHEMA_PREFIX}-activation-freeze-v1"
TEST_OUTPUT_PATH = f"{TOP40_V4_LAYOUT.tournament_root}/activation-tests.out"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")
_REVIEW_RECORD_PATH = "tournament/top40-v4-r2/adversarial-review.json"
_REVIEW_REPORT_PATHS = (
    "tournament/top40-v4-r2/reviews/leakage-cleanroom.md",
    "tournament/top40-v4-r2/reviews/lifecycle-holdout.md",
    "tournament/top40-v4-r2/reviews/evaluator-compatibility.md",
)
_PRETRIAL_INCIDENT_ID = "team-01-discovery-permission-profile-v7"
_PRETRIAL_INCIDENT_ROOT = "tournament/top40-v4-r2/private/pretrial-incidents"
_PRETRIAL_INCIDENT_STAGE = f"{_PRETRIAL_INCIDENT_ROOT}/.{_PRETRIAL_INCIDENT_ID}.staging"
_PRETRIAL_INCIDENT_FINAL = f"{_PRETRIAL_INCIDENT_ROOT}/{_PRETRIAL_INCIDENT_ID}"
_PRETRIAL_SMOKE_RECEIPT_PATH = "tournament/top40-v4-r2/PRETRIAL-MODEL-SMOKE.json"
_PRETRIAL_SMOKE_RECEIPT_SHA256 = (
    "3d6d524c9420ff2019a2176f74845d3fd13852700d18214bc3d02b15ee863136"
)
_PRETRIAL_OLD_ACTIVATION_FILE_SHA256 = (
    "d1b4aa7242b2085e9455ac7628672e7f6bc9826e3e4559f87f8d88a87db53aef"
)
_PRETRIAL_OLD_ACTIVATION_RECORD_SHA256 = (
    "c2777fbe3aa1ea80e86e35f346e771bccf0dfdb892c2c2bb8b3d0aaf3355d654"
)
_PRETRIAL_OLD_TEST_OUTPUT_SHA256 = (
    "66d244083e4c8b9ddf35c9c3c583ad96c58f37bd5073d60b3fed9596dc4843bb"
)
_PRETRIAL_OLD_LAUNCH_SHA256 = (
    "726ed7f538e4c49c5c98a3a35a80f7948631cf47091c99b791202d72dcdf2bc5"
)
_PRETRIAL_OLD_LAUNCH_PATH = (
    "tournament/top40-v4-r2/research-sessions/launches/team-01/discovery.json"
)

_COMMON_FROZEN_SCOPE = (
    ".python-version",
    "pyproject.toml",
    "src/crypto_trade/tournament/_strategy_worker_v4.py",
    "src/crypto_trade/tournament/activation_v4.py",
    "src/crypto_trade/tournament/amendment_integrity_v2.py",
    "src/crypto_trade/tournament/data.py",
    "src/crypto_trade/tournament/engine_v2.py",
    "src/crypto_trade/tournament/journal_v4.py",
    "src/crypto_trade/tournament/layout_v4.py",
    "src/crypto_trade/tournament/metrics_v3.py",
    "src/crypto_trade/tournament/orchestrator_v4.py",
    "src/crypto_trade/tournament/protocol.py",
    "src/crypto_trade/tournament/pure_crypto_universe_v6.py",
    "src/crypto_trade/tournament/risk_policy.py",
    "src/crypto_trade/tournament/runner_v4.py",
    "src/crypto_trade/tournament/scoring_v4.py",
    "src/crypto_trade/tournament/source_archive_v4.py",
    "src/crypto_trade/tournament/top40_v4.py",
    "uv.lock",
)

if _IS_R2:
    FROZEN_SCOPE = (
        *_COMMON_FROZEN_SCOPE,
        "TOURNAMENT-CHARTER-TOP40-V4-R2.md",
        "scripts/top40_v4_r2_team_broker.py",
        "scripts/top40_v4_r2_tournament.py",
        "reports-top40-v4-r2/common/btc_daily_returns.csv",
        "reports-top40-v4-r2/common/btc_regimes.csv",
        "src/crypto_trade/tournament/isolation_v4.py",
        "src/crypto_trade/tournament/pure_crypto_universe_v4_r2.py",
        "src/crypto_trade/tournament/research_runtime_v4.py",
        "src/crypto_trade/tournament/snapshot.py",
        "tests/tournament/test_top40_v4_r2.py",
        "tournament/top40-v4-r2/CLEANROOM-POLICY.md",
        "tournament/top40-v4-r2/PRETRIAL-INCIDENT.md",
        _PRETRIAL_SMOKE_RECEIPT_PATH,
        "tournament/top40-v4-r2/README.md",
        "tournament/top40-v4-r2/ROBUSTNESS-POLICY.md",
        "tournament/top40-v4-r2/SNAPSHOT-BUILD.toml",
        "tournament/top40-v4-r2/STRATEGY-API.md",
        "tournament/top40-v4-r2/TEAM-PLAYBOOK.md",
        "tournament/top40-v4-r2/config.toml",
        "tournament/top40-v4-r2/data-manifest.json",
        "tournament/top40-v4-r2/team-kit/RULES.md",
        "tournament/top40-v4-r2/team-kit/STRATEGY-API.md",
        "tournament/top40-v4-r2/team-kit/templates/candidate.json",
        "tournament/top40-v4-r2/team-kit/templates/cleanroom-attestation.json",
        "tournament/top40-v4-r2/team-kit/templates/research-certificate.json",
        "tournament/top40-v4-r2/team-kit/templates/risk-policy.json",
        _REVIEW_RECORD_PATH,
        *_REVIEW_REPORT_PATHS,
        "tournament/top40-v4-r2/templates/candidate.json",
        "tournament/top40-v4-r2/templates/cleanroom-attestation.json",
        "tournament/top40-v4-r2/templates/research-certificate.json",
        "tournament/top40-v4-r2/templates/risk-policy.json",
        *tuple(
            f"tournament/top40-v4-r2/teams/{team_id}/{filename}"
            for team_id in TOP40_V4_LAYOUT.team_ids
            for filename in ("ACCESS-POLICY.json", "TEAM-BRIEF.md")
        ),
        *tuple(
            f"tournament/top40-v4-r2/teams/{team_id}/candidates/README.md"
            for team_id in TOP40_V4_LAYOUT.team_ids
        ),
    )
    TARGETED_TESTS = ("tests/tournament/test_top40_v4_r2.py",)
else:
    FROZEN_SCOPE = (
        *_COMMON_FROZEN_SCOPE,
        "TOURNAMENT-CHARTER-TOP40-V4-R1.md",
        "scripts/top40_v4_tournament.py",
        "tests/tournament/test_top40_v4.py",
        "tests/tournament/test_v4_team_bundles.py",
        "tournament/top40-v4-r1/README.md",
        "tournament/top40-v4-r1/ROBUSTNESS-POLICY.md",
        "tournament/top40-v4-r1/TEAM-MANDATES.md",
        "tournament/top40-v4-r1/TEAM-PLAYBOOK.md",
        "tournament/top40-v4-r1/config.toml",
        "tournament/top40/data_manifest.json",
    )
    TARGETED_TESTS = (
        "tests/tournament/test_top40_v4.py",
        "tests/tournament/test_v4_team_bundles.py",
    )


class ActivationError(ValueError):
    """The V4 activation evidence is missing, unsafe, or no longer valid."""


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ActivationError("activation evidence is not canonical finite JSON") from exc


def _pretty(value: object) -> bytes:
    try:
        return json.dumps(value, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    except (TypeError, ValueError) as exc:
        raise ActivationError("activation evidence is not finite JSON") from exc


def _file(root: Path, relative: str) -> Path:
    lexical = root
    for part in Path(relative).parts:
        lexical = lexical / part
        if os.path.lexists(lexical) and lexical.is_symlink():
            raise ActivationError(f"activation scope contains a symlink: {relative}")
    path = lexical.resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise ActivationError(f"activation scope file is missing or unsafe: {relative}")
    return path


def _committed_blob(root: Path, commit: str, relative: str) -> bytes:
    completed = subprocess.run(
        ("git", "show", f"{commit}:{relative}"),
        cwd=root,
        check=False,
        capture_output=True,
    )
    if completed.returncode:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ActivationError(f"cannot read committed activation scope {relative}: {detail}")
    return completed.stdout


def _scope(
    root: Path, *, implementation_commit: str | None = None
) -> tuple[list[dict[str, Any]], str]:
    entries: list[dict[str, Any]] = []
    previous = "0" * 64
    for sequence, relative in enumerate(FROZEN_SCOPE, start=1):
        payload = _file(root, relative).read_bytes()
        if implementation_commit is not None and payload != _committed_blob(
            root, implementation_commit, relative
        ):
            raise ActivationError(
                f"activation scope differs from implementation commit: {relative}"
            )
        row: dict[str, Any] = {
            "sequence": sequence,
            "path": relative,
            "size": len(payload),
            "sha256": _sha256(payload),
            "previous_sha256": previous,
        }
        row["entry_sha256"] = _sha256(_canonical(row))
        previous = row["entry_sha256"]
        entries.append(row)
    return entries, previous


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_CLOEXEC", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _durable_directory(path: Path, *, stop: Path) -> None:
    missing: list[Path] = []
    current = path
    while not os.path.lexists(current):
        if current == stop or not current.is_relative_to(stop):
            raise ActivationError("durable directory escaped the tournament root")
        missing.append(current)
        current = current.parent
    if not current.is_dir() or current.is_symlink():
        raise ActivationError("durable directory ancestor is unsafe")
    for directory in reversed(missing):
        os.mkdir(directory, mode=0o700)
        _fsync_directory(directory)
        _fsync_directory(directory.parent)
    if not path.is_dir() or path.is_symlink():
        raise ActivationError("durable directory is unsafe")


def _fsync_regular_file(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        details = os.fstat(descriptor)
        if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
            raise ActivationError("durable incident evidence is not a single regular file")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_atomic(path: Path, payload: bytes, *, exclusive: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            if handle.write(payload) != len(payload):
                raise OSError("short activation evidence write")
            handle.flush()
            os.fsync(handle.fileno())
        if exclusive:
            try:
                os.link(temporary, path, follow_symlinks=False)
            except FileExistsError as exc:
                raise ActivationError("V4 activation freeze already exists") from exc
        else:
            os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if os.path.lexists(temporary):
            temporary.unlink()
            _fsync_directory(path.parent)


def _pretrial_runtime_path(root: Path, relative: str) -> Path:
    path = root
    for part in Path(relative).parts:
        path = path / part
        if os.path.lexists(path) and path.is_symlink():
            raise ActivationError(f"pretrial recovery path is a symlink: {relative}")
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise ActivationError(f"pretrial recovery path escapes the root: {relative}")
    return path


def _pretrial_stable_evidence(
    path: Path,
    *,
    allowed_links: frozenset[int] = frozenset({1}),
    maximum: int = 2 * 1024 * 1024,
) -> tuple[bytes, os.stat_result]:
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
                or before.st_nlink not in allowed_links
                or before.st_size > maximum
            ):
                raise ActivationError("pretrial evidence is not a bounded regular file")
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        current = path.lstat()
    except ActivationError:
        raise
    except OSError as exc:
        raise ActivationError("cannot read pretrial evidence safely") from exc
    identities = {
        (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink),
        (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink),
        (
            current.st_dev,
            current.st_ino,
            current.st_size,
            current.st_mtime_ns,
            current.st_nlink,
        ),
    }
    if (
        len(identities) != 1
        or not stat.S_ISREG(current.st_mode)
        or len(payload) > maximum
    ):
        raise ActivationError("pretrial evidence changed while being read")
    return payload, current


def _pretrial_stable_bytes(
    path: Path,
    *,
    allowed_links: frozenset[int] = frozenset({1}),
    maximum: int = 2 * 1024 * 1024,
) -> bytes:
    return _pretrial_stable_evidence(
        path, allowed_links=allowed_links, maximum=maximum
    )[0]


def _pretrial_file_bytes(root: Path, relative: str) -> bytes:
    path = _pretrial_runtime_path(root, relative)
    try:
        return _pretrial_stable_bytes(path)
    except ActivationError as exc:
        raise ActivationError(
            f"pretrial recovery file is missing or unsafe: {relative}"
        ) from exc


def _pretrial_object_bytes(payload: bytes, label: str) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ActivationError(f"duplicate JSON key in {label}")
            result[key] = item
        return result

    def reject(value: str) -> None:
        raise ActivationError(f"nonfinite JSON value in {label}: {value}")

    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=unique,
            parse_constant=reject,
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError(f"{label} is invalid JSON") from exc
    if not isinstance(value, Mapping):
        raise ActivationError(f"{label} must be a JSON object")
    return value


def _pretrial_object(
    path: Path,
    label: str,
    *,
    allowed_links: frozenset[int] = frozenset({1}),
) -> Mapping[str, Any]:
    return _pretrial_object_bytes(
        _pretrial_stable_bytes(path, allowed_links=allowed_links), label
    )


def _pretrial_exact_directory(root: Path, relative: str, expected: set[str]) -> None:
    path = _pretrial_runtime_path(root, relative)
    if not path.is_dir() or path.is_symlink():
        raise ActivationError(f"pretrial recovery directory is missing or unsafe: {relative}")
    entries = list(path.iterdir())
    if {entry.name for entry in entries} != expected or any(
        not stat.S_ISREG(entry.lstat().st_mode) or entry.lstat().st_nlink != 1
        for entry in entries
    ):
        raise ActivationError(f"pretrial recovery directory is not seed-only: {relative}")


def _validate_pretrial_empty_state(root: Path) -> None:
    journal = _pretrial_file_bytes(root, TOP40_V4_LAYOUT.journal_path)
    if journal != b"" or journal_v4.replay_bytes(journal).record_count != 0:
        raise ActivationError("pretrial recovery requires an exactly empty research journal")
    for team_id in TOP40_V4_LAYOUT.team_ids:
        team = TOP40_V4_LAYOUT.team_root(team_id)
        _pretrial_exact_directory(root, f"{team}/candidates", {"README.md"})
        for directory in ("feedback", "outbox", "work"):
            _pretrial_exact_directory(root, f"{team}/{directory}", {".keep"})
    forbidden = (
        TOP40_V4_LAYOUT.nomination_registry_path,
        TOP40_V4_LAYOUT.selection_freeze_path,
        f"{TOP40_V4_LAYOUT.tournament_root}/nominations",
        f"{TOP40_V4_LAYOUT.tournament_root}/certificates",
        f"{TOP40_V4_LAYOUT.tournament_root}/lifecycle.jsonl",
        f"{TOP40_V4_LAYOUT.tournament_root}/private/historical-oos",
        f"{TOP40_V4_LAYOUT.reports_root}/is",
        f"{TOP40_V4_LAYOUT.reports_root}/source-archives",
        f"{TOP40_V4_LAYOUT.reports_root}/historical-oos",
    )
    if any(os.path.lexists(_pretrial_runtime_path(root, relative)) for relative in forbidden):
        raise ActivationError("pretrial recovery found result, selection, or release artifacts")
    sessions_relative = f"{TOP40_V4_LAYOUT.tournament_root}/research-sessions"
    sessions = _pretrial_runtime_path(root, sessions_relative)
    if os.path.lexists(sessions):
        if not sessions.is_dir() or sessions.is_symlink():
            raise ActivationError("pretrial research-session root is unsafe")
        allowed_files = {"launches/team-01/discovery.json"}
        allowed_directories = {"launches", "launches/team-01"}
        files: set[str] = set()
        directories: set[str] = set()
        for entry in sessions.rglob("*"):
            if entry.is_symlink():
                raise ActivationError("pretrial research-session tree contains a symlink")
            relative = entry.relative_to(sessions).as_posix()
            if entry.is_dir():
                directories.add(relative)
            elif entry.is_file():
                files.add(relative)
            else:
                raise ActivationError("pretrial research-session tree is not regular")
        if not files.issubset(allowed_files) or not directories.issubset(allowed_directories):
            raise ActivationError("pretrial research-session tree contains result evidence")
        launch = sessions / "launches/team-01/discovery.json"
        if os.path.lexists(launch):
            launch_payload, launch_details = _pretrial_stable_evidence(
                launch, allowed_links=frozenset({1, 2})
            )
            if _sha256(launch_payload) != _PRETRIAL_OLD_LAUNCH_SHA256:
                raise ActivationError("pretrial launch authority hash differs")
            if launch_details.st_nlink == 2:
                staged_launch = (
                    _pretrial_runtime_path(root, _PRETRIAL_INCIDENT_STAGE)
                    / "superseded-team-01-discovery-v7.json"
                )
                if not os.path.lexists(staged_launch):
                    raise ActivationError("pretrial launch hardlink has no staged counterpart")
                staged_payload, staged_details = _pretrial_stable_evidence(
                    staged_launch, allowed_links=frozenset({2})
                )
                if (
                    _sha256(staged_payload) != _PRETRIAL_OLD_LAUNCH_SHA256
                    or (launch_details.st_dev, launch_details.st_ino)
                    != (staged_details.st_dev, staged_details.st_ino)
                ):
                    raise ActivationError("pretrial launch hardlink topology is unsafe")


def _pretrial_incident_manifest(root: Path, path: Path) -> Mapping[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise ActivationError("pretrial incident manifest is missing or unsafe")
    manifest = _pretrial_object(path, "pretrial incident manifest")
    expected = {
        "schema_version",
        "tournament",
        "incident_id",
        "status",
        "reason",
        "verified_empty_journal_sha256",
        "old_activation",
        "old_test_output",
        "old_launch_authority",
        "new_activation",
        "model_smoke_receipt",
        "record_sha256",
    }
    if set(manifest) != expected:
        raise ActivationError("pretrial incident manifest schema changed")
    unsigned = dict(manifest)
    claimed = unsigned.pop("record_sha256")
    if not isinstance(claimed, str) or claimed != _sha256(_canonical(unsigned)):
        raise ActivationError("pretrial incident manifest hash is invalid")
    if (
        manifest["schema_version"] != 1
        or manifest["tournament"] != TOP40_V4_LAYOUT.name
        or manifest["incident_id"] != _PRETRIAL_INCIDENT_ID
        or manifest["status"] != "completed-before-first-trial"
        or manifest["reason"]
        != "codex-0.148-exec-security-overrides-preceded-ignore-user-config"
        or manifest["verified_empty_journal_sha256"] != _sha256(b"")
    ):
        raise ActivationError("pretrial incident manifest identity changed")
    old_activation = manifest["old_activation"]
    old_tests = manifest["old_test_output"]
    old_launch = manifest["old_launch_authority"]
    new_activation = manifest["new_activation"]
    smoke = manifest["model_smoke_receipt"]
    if (
        not isinstance(old_activation, Mapping)
        or dict(old_activation)
        != {
            "file_sha256": _PRETRIAL_OLD_ACTIVATION_FILE_SHA256,
            "record_sha256": _PRETRIAL_OLD_ACTIVATION_RECORD_SHA256,
        }
        or not isinstance(old_tests, Mapping)
        or dict(old_tests) != {"sha256": _PRETRIAL_OLD_TEST_OUTPUT_SHA256}
        or not isinstance(old_launch, Mapping)
        or dict(old_launch)
        != {
            "launcher_version": "top40-v4-r2-research-runtime-v7",
            "sha256": _PRETRIAL_OLD_LAUNCH_SHA256,
            "team_id": "team-01",
            "phase": "discovery",
        }
        or not isinstance(new_activation, Mapping)
        or set(new_activation)
        != {"file_sha256", "record_sha256", "implementation_commit", "launcher_version"}
        or new_activation.get("launcher_version") != "top40-v4-r2-research-runtime-v8"
        or not isinstance(new_activation.get("file_sha256"), str)
        or _SHA256.fullmatch(str(new_activation.get("file_sha256"))) is None
        or not isinstance(new_activation.get("record_sha256"), str)
        or _SHA256.fullmatch(str(new_activation.get("record_sha256"))) is None
        or not isinstance(new_activation.get("implementation_commit"), str)
        or _GIT_OBJECT_ID.fullmatch(str(new_activation.get("implementation_commit"))) is None
        or not isinstance(smoke, Mapping)
        or dict(smoke)
        != {
            "path": _PRETRIAL_SMOKE_RECEIPT_PATH,
            "sha256": _PRETRIAL_SMOKE_RECEIPT_SHA256,
            "record_sha256": "ebbd03151348350767feac7acb9eebb0e57f15659353ea43cc51738292e87565",
        }
    ):
        raise ActivationError("pretrial incident authority binding changed")
    archived = {
        "superseded-activation-freeze.json": _PRETRIAL_OLD_ACTIVATION_FILE_SHA256,
        "superseded-activation-tests.out": _PRETRIAL_OLD_TEST_OUTPUT_SHA256,
        "superseded-team-01-discovery-v7.json": _PRETRIAL_OLD_LAUNCH_SHA256,
    }
    if any(
        not (candidate := path.parent / name).is_file()
        or candidate.is_symlink()
        or _sha256(_pretrial_stable_bytes(candidate)) != digest
        for name, digest in archived.items()
    ):
        raise ActivationError("pretrial incident archived evidence changed")
    prepared_path = path.parent / "prepared.json"
    if not prepared_path.is_file() or prepared_path.is_symlink():
        raise ActivationError("pretrial incident prepared receipt is missing or unsafe")
    prepared = _pretrial_object(prepared_path, "pretrial prepared receipt")
    if set(prepared) != {
        "schema_version",
        "tournament",
        "incident_id",
        "status",
        "old_activation_file_sha256",
        "old_activation_record_sha256",
        "old_test_output_sha256",
        "old_launch_authority_sha256",
        "verified_empty_journal_sha256",
        "record_sha256",
    }:
        raise ActivationError("pretrial incident prepared receipt schema changed")
    prepared_unsigned = dict(prepared)
    prepared_claimed = prepared_unsigned.pop("record_sha256")
    if (
        prepared_claimed != _sha256(_canonical(prepared_unsigned))
        or prepared_unsigned
        != {
            "schema_version": 1,
            "tournament": TOP40_V4_LAYOUT.name,
            "incident_id": _PRETRIAL_INCIDENT_ID,
            "status": "prepared-awaiting-v8-activation",
            "old_activation_file_sha256": _PRETRIAL_OLD_ACTIVATION_FILE_SHA256,
            "old_activation_record_sha256": _PRETRIAL_OLD_ACTIVATION_RECORD_SHA256,
            "old_test_output_sha256": _PRETRIAL_OLD_TEST_OUTPUT_SHA256,
            "old_launch_authority_sha256": _PRETRIAL_OLD_LAUNCH_SHA256,
            "verified_empty_journal_sha256": _sha256(b""),
        }
    ):
        raise ActivationError("pretrial incident prepared receipt binding changed")
    current_activation = _pretrial_file_bytes(root, TOP40_V4_LAYOUT.activation_freeze_path)
    if _sha256(current_activation) != new_activation["file_sha256"]:
        raise ActivationError("pretrial incident new activation binding changed")
    current_activation_object = _pretrial_object_bytes(
        current_activation, "current activation"
    )
    if (
        current_activation_object.get("record_sha256") != new_activation["record_sha256"]
        or current_activation_object.get("implementation_commit")
        != new_activation["implementation_commit"]
    ):
        raise ActivationError("pretrial incident stable activation identity changed")
    validated_activation = validate(root, verify_universe_snapshot=False)
    if (
        validated_activation.get("record_sha256") != new_activation["record_sha256"]
        or validated_activation.get("implementation_commit")
        != new_activation["implementation_commit"]
    ):
        raise ActivationError("pretrial incident current activation identity changed")
    smoke_receipt = _pretrial_file_bytes(root, _PRETRIAL_SMOKE_RECEIPT_PATH)
    if _sha256(smoke_receipt) != _PRETRIAL_SMOKE_RECEIPT_SHA256:
        raise ActivationError("pretrial model-smoke receipt changed")
    final_entries = {entry.name for entry in path.parent.iterdir()}
    if final_entries != {
        "incident.json",
        "prepared.json",
        "superseded-activation-freeze.json",
        "superseded-activation-tests.out",
        "superseded-team-01-discovery-v7.json",
    }:
        raise ActivationError("pretrial incident archive surface changed")
    return manifest


def pretrial_recovery_pending(root: str | Path) -> bool:
    root_path = Path(root).resolve()
    stage = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_STAGE)
    final = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_FINAL)
    return os.path.lexists(stage) or not os.path.lexists(final)


def require_completed_pretrial_recovery(root: str | Path) -> Mapping[str, Any]:
    """Fail closed until the known incident archive and its new activation binding are valid."""

    root_path = Path(root).resolve()
    stage = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_STAGE)
    if os.path.lexists(stage):
        raise ActivationError("pretrial activation recovery is not complete")
    final = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_FINAL)
    if not final.is_dir() or final.is_symlink():
        raise ActivationError("completed pretrial incident authority is missing or unsafe")
    return _pretrial_incident_manifest(root_path, final / "incident.json")


def _move_pretrial_file(
    root: Path,
    source_relative: str,
    destination: Path,
    expected_sha256: str,
) -> None:
    source = _pretrial_runtime_path(root, source_relative)
    source_exists = os.path.lexists(source)
    destination_exists = os.path.lexists(destination)
    if source_exists and destination_exists:
        source_payload, source_details = _pretrial_stable_evidence(
            source, allowed_links=frozenset({1, 2})
        )
        destination_payload, destination_details = _pretrial_stable_evidence(
            destination, allowed_links=frozenset({1, 2})
        )
        same_inode = (source_details.st_dev, source_details.st_ino) == (
            destination_details.st_dev,
            destination_details.st_ino,
        )
        valid_topology = (
            source_details.st_nlink == destination_details.st_nlink == 1
        ) or (
            source_details.st_nlink == destination_details.st_nlink == 2 and same_inode
        )
        if (
            not valid_topology
            or _sha256(source_payload) != expected_sha256
            or _sha256(destination_payload) != expected_sha256
        ):
            raise ActivationError("pretrial recovery found unsafe duplicate authority")
        # Destination-first fsync can recover with both names after a crash. Preserve the verified
        # archive, release only the redundant source name, then persist that cleanup.
        source.unlink()
        _fsync_directory(source.parent)
        source_exists = False
    if source_exists:
        payload = _pretrial_file_bytes(root, source_relative)
        if _sha256(payload) != expected_sha256:
            raise ActivationError("pretrial recovery old authority hash differs")
        _durable_directory(destination.parent, stop=root)
        os.replace(source, destination)
        _fsync_regular_file(destination)
        # Persist the new name before persisting removal of the only old name. A crash may leave
        # both names durable, but must never durably lose the archived authority from both sides.
        _fsync_directory(destination.parent)
        _fsync_directory(source.parent)
    elif not destination_exists:
        raise ActivationError("pretrial recovery old authority is missing")
    if (
        not destination.is_file()
        or destination.is_symlink()
        or _sha256(_pretrial_stable_bytes(destination)) != expected_sha256
    ):
        raise ActivationError("archived pretrial authority differs from its expected hash")
    _fsync_regular_file(destination)


def _preflight_pretrial_file(
    root: Path,
    source_relative: str,
    staged: Path,
    expected_sha256: str,
) -> Path:
    source = _pretrial_runtime_path(root, source_relative)
    candidates = [path for path in (source, staged) if os.path.lexists(path)]
    if not candidates:
        raise ActivationError("pretrial recovery old authority is missing")
    evidence = [
        (
            candidate,
            *_pretrial_stable_evidence(
                candidate, allowed_links=frozenset({1, 2})
            ),
        )
        for candidate in candidates
    ]
    for _candidate, payload, _details in evidence:
        if _sha256(payload) != expected_sha256:
            raise ActivationError("pretrial recovery old authority hash differs")
    if len(evidence) == 1 and evidence[0][2].st_nlink != 1:
        raise ActivationError("pretrial recovery found unsafe duplicate authority")
    if len(evidence) == 2:
        source_details = evidence[0][2]
        staged_details = evidence[1][2]
        same_inode = (source_details.st_dev, source_details.st_ino) == (
            staged_details.st_dev,
            staged_details.st_ino,
        )
        valid_topology = (
            source_details.st_nlink == staged_details.st_nlink == 1
        ) or (
            source_details.st_nlink == staged_details.st_nlink == 2 and same_inode
        )
        if not valid_topology:
            raise ActivationError("pretrial recovery found unsafe duplicate authority")
    return staged if os.path.lexists(staged) else source


def _expected_pretrial_prepared() -> dict[str, Any]:
    prepared: dict[str, Any] = {
        "schema_version": 1,
        "tournament": TOP40_V4_LAYOUT.name,
        "incident_id": _PRETRIAL_INCIDENT_ID,
        "status": "prepared-awaiting-v8-activation",
        "old_activation_file_sha256": _PRETRIAL_OLD_ACTIVATION_FILE_SHA256,
        "old_activation_record_sha256": _PRETRIAL_OLD_ACTIVATION_RECORD_SHA256,
        "old_test_output_sha256": _PRETRIAL_OLD_TEST_OUTPUT_SHA256,
        "old_launch_authority_sha256": _PRETRIAL_OLD_LAUNCH_SHA256,
        "verified_empty_journal_sha256": _sha256(b""),
    }
    prepared["record_sha256"] = _sha256(_canonical(prepared))
    return prepared


def _validate_pretrial_prepared(root: Path, stage: Path) -> Mapping[str, Any]:
    """Validate a durable prepared stage without treating a new freeze as old authority."""

    prepared_path = stage / "prepared.json"
    prepared = _pretrial_object(prepared_path, "pretrial prepared receipt")
    if dict(prepared) != _expected_pretrial_prepared():
        raise ActivationError("pretrial incident prepared receipt binding changed")
    expected_entries = {
        "prepared.json",
        "superseded-activation-freeze.json",
        "superseded-activation-tests.out",
    }
    optional_entries = {
        "incident.json",
        "superseded-team-01-discovery-v7.json",
    }
    entries = {entry.name for entry in stage.iterdir()}
    if not expected_entries.issubset(entries) or not entries.issubset(
        expected_entries | optional_entries
    ):
        raise ActivationError("pretrial incident staging surface changed")
    for name, digest in (
        ("superseded-activation-freeze.json", _PRETRIAL_OLD_ACTIVATION_FILE_SHA256),
        ("superseded-activation-tests.out", _PRETRIAL_OLD_TEST_OUTPUT_SHA256),
    ):
        if _sha256(_pretrial_stable_bytes(stage / name)) != digest:
            raise ActivationError("pretrial incident prepared authority changed")
    active_tests = _pretrial_runtime_path(root, TEST_OUTPUT_PATH)
    active_activation = _pretrial_runtime_path(
        root, TOP40_V4_LAYOUT.activation_freeze_path
    )
    if os.path.lexists(active_activation):
        active_payload = _pretrial_stable_bytes(active_activation)
        if _sha256(active_payload) == _PRETRIAL_OLD_ACTIVATION_FILE_SHA256:
            raise ActivationError("superseded activation reappeared after preparation")
        validated = validate(root, verify_universe_snapshot=False)
        tests = validated.get("tests")
        test_payload = _pretrial_stable_bytes(active_tests)
        if (
            not isinstance(tests, Mapping)
            or tests.get("output_path") != TEST_OUTPUT_PATH
            or tests.get("exit_code") != 0
            or tests.get("output_size") != len(test_payload)
            or tests.get("output_sha256") != _sha256(test_payload)
        ):
            raise ActivationError("prepared successor activation tests are not bound")
    elif os.path.lexists(active_tests):
        # Activation publishes its bounded test output before the exclusive freeze. A crash in
        # that window leaves disposable successor scratch evidence, which the next activation
        # rerun atomically replaces. It is not authority until a freeze binds its exact bytes.
        scratch = _pretrial_stable_bytes(active_tests)
        if _sha256(scratch) == _PRETRIAL_OLD_TEST_OUTPUT_SHA256:
            raise ActivationError("superseded activation tests reappeared after preparation")
    _preflight_pretrial_file(
        root,
        _PRETRIAL_OLD_LAUNCH_PATH,
        stage / "superseded-team-01-discovery-v7.json",
        _PRETRIAL_OLD_LAUNCH_SHA256,
    )
    if "incident.json" in entries:
        _pretrial_incident_manifest(root, stage / "incident.json")
    return prepared


def prepare_pretrial_recovery(root: str | Path) -> Mapping[str, Any]:
    """Archive the exact old activation while leaving the stale launch fail-closed."""

    if not _IS_R2:
        raise ActivationError("pretrial recovery exists only for Top-40 V4 R2")
    root_path = Path(root).resolve()
    _validate_pretrial_empty_state(root_path)
    final = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_FINAL)
    if os.path.lexists(final):
        return _pretrial_incident_manifest(root_path, final / "incident.json")
    stage = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_STAGE)
    if os.path.lexists(stage) and (not stage.is_dir() or stage.is_symlink()):
        raise ActivationError("pretrial incident staging path is unsafe")
    if os.path.lexists(stage / "prepared.json"):
        return _validate_pretrial_prepared(root_path, stage)
    old_activation_path = _preflight_pretrial_file(
        root_path,
        TOP40_V4_LAYOUT.activation_freeze_path,
        stage / "superseded-activation-freeze.json",
        _PRETRIAL_OLD_ACTIVATION_FILE_SHA256,
    )
    _preflight_pretrial_file(
        root_path,
        TEST_OUTPUT_PATH,
        stage / "superseded-activation-tests.out",
        _PRETRIAL_OLD_TEST_OUTPUT_SHA256,
    )
    _preflight_pretrial_file(
        root_path,
        _PRETRIAL_OLD_LAUNCH_PATH,
        stage / "superseded-team-01-discovery-v7.json",
        _PRETRIAL_OLD_LAUNCH_SHA256,
    )
    old_activation = _pretrial_object(
        old_activation_path,
        "superseded activation",
        allowed_links=frozenset({1, 2}),
    )
    if old_activation.get("record_sha256") != _PRETRIAL_OLD_ACTIVATION_RECORD_SHA256:
        raise ActivationError("superseded activation record identity differs")
    _durable_directory(stage, stop=root_path)
    _move_pretrial_file(
        root_path,
        TOP40_V4_LAYOUT.activation_freeze_path,
        stage / "superseded-activation-freeze.json",
        _PRETRIAL_OLD_ACTIVATION_FILE_SHA256,
    )
    _move_pretrial_file(
        root_path,
        TEST_OUTPUT_PATH,
        stage / "superseded-activation-tests.out",
        _PRETRIAL_OLD_TEST_OUTPUT_SHA256,
    )
    prepared = _expected_pretrial_prepared()
    _write_atomic(stage / "prepared.json", _pretty(prepared), exclusive=False)
    return prepared


def complete_pretrial_recovery(root: str | Path) -> Mapping[str, Any]:
    """Bind the valid new activation, then archive the stale v7 launch authority."""

    if not _IS_R2:
        raise ActivationError("pretrial recovery exists only for Top-40 V4 R2")
    root_path = Path(root).resolve()
    _validate_pretrial_empty_state(root_path)
    final = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_FINAL)
    if os.path.lexists(final):
        return _pretrial_incident_manifest(root_path, final / "incident.json")
    stage = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_STAGE)
    if not stage.is_dir() or stage.is_symlink():
        raise ActivationError("pretrial recovery was not prepared")
    new_activation = validate(root_path)
    new_activation_payload = _pretrial_file_bytes(
        root_path, TOP40_V4_LAYOUT.activation_freeze_path
    )
    if new_activation.get("record_sha256") == _PRETRIAL_OLD_ACTIVATION_RECORD_SHA256:
        raise ActivationError("pretrial recovery requires a distinct new activation")
    _move_pretrial_file(
        root_path,
        _PRETRIAL_OLD_LAUNCH_PATH,
        stage / "superseded-team-01-discovery-v7.json",
        _PRETRIAL_OLD_LAUNCH_SHA256,
    )
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "tournament": TOP40_V4_LAYOUT.name,
        "incident_id": _PRETRIAL_INCIDENT_ID,
        "status": "completed-before-first-trial",
        "reason": "codex-0.148-exec-security-overrides-preceded-ignore-user-config",
        "verified_empty_journal_sha256": _sha256(b""),
        "old_activation": {
            "file_sha256": _PRETRIAL_OLD_ACTIVATION_FILE_SHA256,
            "record_sha256": _PRETRIAL_OLD_ACTIVATION_RECORD_SHA256,
        },
        "old_test_output": {"sha256": _PRETRIAL_OLD_TEST_OUTPUT_SHA256},
        "old_launch_authority": {
            "launcher_version": "top40-v4-r2-research-runtime-v7",
            "sha256": _PRETRIAL_OLD_LAUNCH_SHA256,
            "team_id": "team-01",
            "phase": "discovery",
        },
        "new_activation": {
            "file_sha256": _sha256(new_activation_payload),
            "record_sha256": new_activation["record_sha256"],
            "implementation_commit": new_activation["implementation_commit"],
            "launcher_version": "top40-v4-r2-research-runtime-v8",
        },
        "model_smoke_receipt": {
            "path": _PRETRIAL_SMOKE_RECEIPT_PATH,
            "sha256": _PRETRIAL_SMOKE_RECEIPT_SHA256,
            "record_sha256": "ebbd03151348350767feac7acb9eebb0e57f15659353ea43cc51738292e87565",
        },
    }
    manifest["record_sha256"] = _sha256(_canonical(manifest))
    _write_atomic(stage / "incident.json", _pretty(manifest), exclusive=False)
    destination = _pretrial_runtime_path(root_path, _PRETRIAL_INCIDENT_FINAL)
    _durable_directory(destination.parent, stop=root_path)
    os.replace(stage, destination)
    _fsync_directory(destination.parent)
    return _pretrial_incident_manifest(root_path, destination / "incident.json")


def _test_command() -> tuple[str, ...]:
    return (
        "uv",
        "run",
        "--frozen",
        "pytest",
        "-q",
        *TARGETED_TESTS,
    )


def _run_tests(root: Path) -> tuple[bytes, int]:
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "src",
            "OMP_NUM_THREADS": "1",
            "OPENBLAS_NUM_THREADS": "1",
            "MKL_NUM_THREADS": "1",
        }
    )
    if _IS_R2:
        environment["CRYPTO_TRADE_TOP40_V4_EDITION"] = "r2"
    with tempfile.TemporaryDirectory(prefix="top40-v4-uv-cache-") as uv_cache:
        environment["UV_CACHE_DIR"] = uv_cache
        completed = subprocess.run(
            _test_command(),
            cwd=root,
            env=environment,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    return completed.stdout, int(completed.returncode)


def _git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ("git", *arguments),
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode:
        detail = completed.stderr.strip() or completed.stdout.strip()
        raise ActivationError(f"git {' '.join(arguments)} failed: {detail}")
    return completed.stdout.strip()


def _implementation_commit(root: Path) -> str:
    branch = _git(root, "branch", "--show-current")
    if branch != TOP40_V4_LAYOUT.branch:
        raise ActivationError(f"current branch must be {TOP40_V4_LAYOUT.branch}")
    for relative in FROZEN_SCOPE:
        _git(root, "ls-files", "--error-unmatch", "--", relative)
    completed = subprocess.run(
        ("git", "diff", "--quiet", "HEAD", "--", *FROZEN_SCOPE),
        cwd=root,
        check=False,
    )
    if completed.returncode != 0:
        raise ActivationError("every activation-scope file must be committed and clean")
    commit = _git(root, "rev-parse", "HEAD")
    if _GIT_OBJECT_ID.fullmatch(commit) is None:
        raise ActivationError("implementation commit is not a full Git object id")
    return commit


def _audit_sha256(root: Path, config: Mapping[str, Any]) -> str:
    report = (
        pure_crypto_universe_v4_r2.audit_report_bytes(root, config)
        if _IS_R2
        else pure_crypto_universe_v6.audit_report_bytes(root)
    )
    digest = _sha256(report)
    expected = str(config["universe"]["a6_authority"]["audit_report_sha256"])
    if digest != expected:
        raise ActivationError("pure-crypto audit report differs from the frozen config")
    parsed = json.loads(report)
    if parsed.get("status") != "passed" or parsed.get("violations") != []:
        raise ActivationError("pure-crypto audit did not pass with zero violations")
    return digest


def _validate_snapshot_window(root: Path, config: Mapping[str, Any]) -> None:
    """Refuse activation when the bound snapshot omits any configured holdout month."""

    manifest_relative = str(config["data"]["manifest_path"])
    manifest_path = _file(root, manifest_relative)
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_end = str(manifest["window"]["hard_end_exclusive"]).replace("+00:00", "Z")
    except (KeyError, TypeError, UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError("snapshot manifest has no canonical hard-end authority") from exc
    configured_end = str(config["data"]["hard_end_exclusive"])
    holdout_end = str(config["splits"]["historical_oos"]["end_exclusive"])
    if manifest_end != configured_end or configured_end != holdout_end:
        raise ActivationError(
            "snapshot does not cover the complete configured historical holdout; "
            f"manifest={manifest_end}, configured={configured_end}, holdout={holdout_end}"
        )


def _verify_full_snapshot_once(root: Path, config: Mapping[str, Any]) -> str | None:
    """Perform the expensive raw-source replay once at activation, never per team trial."""

    if not _IS_R2:
        return None
    manifest_path = _file(root, str(config["data"]["manifest_path"]))
    try:
        snapshot.verify_snapshot_manifest(manifest_path)
    except (OSError, TypeError, ValueError) as exc:
        raise ActivationError("full July-inclusive snapshot verification failed") from exc
    digest = _sha256(manifest_path.read_bytes())
    if digest != config["data"]["manifest_sha256"]:
        raise ActivationError("verified snapshot manifest differs from the config")
    return digest


def _review_scope_head(root: Path) -> str:
    excluded = {_REVIEW_RECORD_PATH, *_REVIEW_REPORT_PATHS}
    previous = "0" * 64
    for sequence, relative in enumerate(
        (path for path in FROZEN_SCOPE if path not in excluded), start=1
    ):
        payload = _file(root, relative).read_bytes()
        previous = _sha256(
            _canonical(
                {
                    "sequence": sequence,
                    "path": relative,
                    "size": len(payload),
                    "sha256": _sha256(payload),
                    "previous_sha256": previous,
                }
            )
        )
    return previous


def _validate_adversarial_review(root: Path) -> Mapping[str, Any] | None:
    if not _IS_R2:
        return None
    record = _read_object(_file(root, _REVIEW_RECORD_PATH))
    if set(record) != {
        "schema_version",
        "tournament",
        "status",
        "reviewed_scope_head_sha256",
        "reports",
    }:
        raise ActivationError("adversarial review record schema changed")
    if (
        record["schema_version"] != 1
        or record["tournament"] != TOP40_V4_LAYOUT.name
        or record["status"] != "passed-after-remediation"
        or record["reviewed_scope_head_sha256"] != _review_scope_head(root)
    ):
        raise ActivationError("adversarial review does not bind the activation implementation")
    reports = record["reports"]
    expected_reports = {
        "leakage-cleanroom": "tournament/top40-v4-r2/reviews/leakage-cleanroom.md",
        "lifecycle-holdout": "tournament/top40-v4-r2/reviews/lifecycle-holdout.md",
        "evaluator-compatibility": (
            "tournament/top40-v4-r2/reviews/evaluator-compatibility.md"
        ),
    }
    if not isinstance(reports, list) or len(reports) != 3:
        raise ActivationError("adversarial review must contain exactly three reports")
    seen: set[str] = set()
    for report in reports:
        if not isinstance(report, Mapping) or set(report) != {
            "scope",
            "path",
            "sha256",
            "status",
            "unresolved_findings",
        }:
            raise ActivationError("adversarial review report binding is malformed")
        scope = report["scope"]
        path = report["path"]
        if (
            scope not in expected_reports
            or scope in seen
            or path != expected_reports[scope]
            or report["status"] != "passed"
            or type(report["unresolved_findings"]) is not int
            or report["unresolved_findings"] != 0
            or _sha256(_file(root, str(path)).read_bytes()) != report["sha256"]
        ):
            raise ActivationError("adversarial review report did not pass or changed")
        seen.add(str(scope))
    if seen != set(expected_reports):
        raise ActivationError("adversarial review scopes are incomplete")
    return record


def activate(root: str | Path) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    freeze_path = root_path / TOP40_V4_LAYOUT.activation_freeze_path
    if freeze_path.exists():
        raise ActivationError("V4 activation is one-time and already exists")
    implementation_commit = _implementation_commit(root_path)
    loaded = top40_v4.load_config(root=root_path)
    _validate_snapshot_window(root_path, loaded.raw)
    full_snapshot_sha256 = _verify_full_snapshot_once(root_path, loaded.raw)
    review = _validate_adversarial_review(root_path)
    entries, head = _scope(root_path, implementation_commit=implementation_commit)
    audit_sha256 = _audit_sha256(root_path, loaded.raw)
    output, exit_code = _run_tests(root_path)
    _write_atomic(root_path / TEST_OUTPUT_PATH, output, exclusive=False)
    if exit_code != 0:
        raise ActivationError(f"V4 focused activation tests failed; inspect {TEST_OUTPUT_PATH}")
    if _implementation_commit(root_path) != implementation_commit:
        raise ActivationError("implementation commit changed during activation")
    verified_entries, verified_head = _scope(root_path, implementation_commit=implementation_commit)
    if verified_entries != entries or verified_head != head:
        raise ActivationError("activation scope changed while tests were running")
    unsigned: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "tournament_id": TOP40_V4_LAYOUT.name,
        "branch": TOP40_V4_LAYOUT.branch,
        "implementation_commit": implementation_commit,
        "activated_at_utc": dt.datetime.now(dt.UTC)
        .replace(microsecond=0)
        .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "config_sha256": loaded.sha256,
        "pure_crypto_report_sha256": audit_sha256,
        "scope_entries": entries,
        "scope_head_sha256": head,
        "tests": {
            "command": list(_test_command()),
            "exit_code": exit_code,
            "output_path": TEST_OUTPUT_PATH,
            "output_size": len(output),
            "output_sha256": _sha256(output),
        },
    }
    if review is not None:
        unsigned["adversarial_review_sha256"] = _sha256(
            _file(root_path, _REVIEW_RECORD_PATH).read_bytes()
        )
    if full_snapshot_sha256 is not None:
        unsigned["full_snapshot_manifest_sha256"] = full_snapshot_sha256
    unsigned["record_sha256"] = _sha256(_canonical(unsigned))
    _write_atomic(freeze_path, _pretty(unsigned), exclusive=True)
    return unsigned


def _read_object(path: Path) -> Mapping[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in pairs:
            if key in result:
                raise ActivationError(f"duplicate JSON key in activation freeze: {key}")
            result[key] = item
        return result

    def reject(value: str) -> None:
        raise ActivationError(f"nonfinite JSON value in activation freeze: {value}")

    try:
        value = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=unique,
            parse_constant=reject,
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ActivationError("V4 activation freeze is unreadable") from exc
    if not isinstance(value, Mapping):
        raise ActivationError("V4 activation freeze must be a JSON object")
    return value


def validate(root: str | Path, *, verify_universe_snapshot: bool = True) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    loaded = top40_v4.load_config(root=root_path)
    _validate_snapshot_window(root_path, loaded.raw)
    review = _validate_adversarial_review(root_path)
    freeze_path = root_path / TOP40_V4_LAYOUT.activation_freeze_path
    if not freeze_path.is_file() or freeze_path.is_symlink():
        raise ActivationError("V4 is not activated")
    record = _read_object(freeze_path)
    expected_keys = {
        "schema_version",
        "tournament_id",
        "branch",
        "implementation_commit",
        "activated_at_utc",
        "config_sha256",
        "pure_crypto_report_sha256",
        "scope_entries",
        "scope_head_sha256",
        "tests",
        "record_sha256",
    }
    if review is not None:
        expected_keys.add("adversarial_review_sha256")
    if _IS_R2:
        expected_keys.add("full_snapshot_manifest_sha256")
    if set(record) != expected_keys:
        raise ActivationError("V4 activation freeze schema changed")
    unsigned = dict(record)
    claimed = unsigned.pop("record_sha256")
    if not isinstance(claimed, str) or _SHA256.fullmatch(claimed) is None:
        raise ActivationError("V4 activation record hash is invalid")
    if _sha256(_canonical(unsigned)) != claimed:
        raise ActivationError("V4 activation record was modified")
    if review is not None and record["adversarial_review_sha256"] != _sha256(
        _file(root_path, _REVIEW_RECORD_PATH).read_bytes()
    ):
        raise ActivationError("V4 adversarial review binding changed")
    if _IS_R2 and record["full_snapshot_manifest_sha256"] != loaded.raw["data"][
        "manifest_sha256"
    ]:
        raise ActivationError("V4 full-snapshot activation binding changed")
    if (
        record["schema_version"] != SCHEMA_VERSION
        or record["tournament_id"] != TOP40_V4_LAYOUT.name
        or record["branch"] != TOP40_V4_LAYOUT.branch
        or record["config_sha256"] != loaded.sha256
    ):
        raise ActivationError("V4 activation identity differs from the current contract")
    if _git(root_path, "branch", "--show-current") != TOP40_V4_LAYOUT.branch:
        raise ActivationError(f"current branch must be {TOP40_V4_LAYOUT.branch}")
    commit = record["implementation_commit"]
    if not isinstance(commit, str) or _GIT_OBJECT_ID.fullmatch(commit) is None:
        raise ActivationError("V4 activation implementation commit is invalid")
    ancestor = subprocess.run(
        ("git", "merge-base", "--is-ancestor", commit, "HEAD"),
        cwd=root_path,
        check=False,
    )
    if ancestor.returncode != 0:
        raise ActivationError("V4 implementation commit is not an ancestor of HEAD")
    entries, head = _scope(root_path)
    if record["scope_entries"] != entries or record["scope_head_sha256"] != head:
        raise ActivationError("V4 frozen infrastructure changed after activation")
    tests = record["tests"]
    if not isinstance(tests, Mapping) or tests.get("command") != list(_test_command()):
        raise ActivationError("V4 activation test authority changed")
    output = _file(root_path, TEST_OUTPUT_PATH).read_bytes()
    if (
        tests.get("exit_code") != 0
        or tests.get("output_size") != len(output)
        or tests.get("output_sha256") != _sha256(output)
    ):
        raise ActivationError("V4 activation test evidence changed")
    if verify_universe_snapshot and record["pure_crypto_report_sha256"] != _audit_sha256(
        root_path, loaded.raw
    ):
        raise ActivationError("V4 pure-crypto authority changed")
    return record


__all__ = [
    "ActivationError",
    "FROZEN_SCOPE",
    "SCHEMA_VERSION",
    "TARGETED_TESTS",
    "TEST_OUTPUT_PATH",
    "activate",
    "complete_pretrial_recovery",
    "prepare_pretrial_recovery",
    "pretrial_recovery_pending",
    "require_completed_pretrial_recovery",
    "validate",
]
