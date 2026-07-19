"""One-time hash freeze for the Top-40 V4 tournament infrastructure."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from crypto_trade.tournament import pure_crypto_universe_v6, top40_v4
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

SCHEMA_VERSION = "top40-v4-r1-activation-freeze-v1"
TEST_OUTPUT_PATH = "tournament/top40-v4-r1/activation-tests.out"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_GIT_OBJECT_ID = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})")

FROZEN_SCOPE = (
    ".python-version",
    "TOURNAMENT-CHARTER-TOP40-V4-R1.md",
    "pyproject.toml",
    "scripts/top40_v4_tournament.py",
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
    "tests/tournament/test_top40_v4.py",
    "tests/tournament/test_v4_team_bundles.py",
    "tournament/top40/data_manifest.json",
    "tournament/top40-v4-r1/README.md",
    "tournament/top40-v4-r1/ROBUSTNESS-POLICY.md",
    "tournament/top40-v4-r1/TEAM-MANDATES.md",
    "tournament/top40-v4-r1/TEAM-PLAYBOOK.md",
    "tournament/top40-v4-r1/config.toml",
    "uv.lock",
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
    report = pure_crypto_universe_v6.audit_report_bytes(root)
    digest = _sha256(report)
    expected = str(config["universe"]["a6_authority"]["audit_report_sha256"])
    if digest != expected:
        raise ActivationError("pure-crypto audit report differs from the frozen config")
    parsed = json.loads(report)
    if parsed.get("status") != "passed" or parsed.get("violations") != []:
        raise ActivationError("pure-crypto audit did not pass with zero violations")
    return digest


def activate(root: str | Path) -> Mapping[str, Any]:
    root_path = Path(root).resolve()
    freeze_path = root_path / TOP40_V4_LAYOUT.activation_freeze_path
    if freeze_path.exists():
        raise ActivationError("V4 activation is one-time and already exists")
    implementation_commit = _implementation_commit(root_path)
    loaded = top40_v4.load_config(root=root_path)
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
    if set(record) != expected_keys:
        raise ActivationError("V4 activation freeze schema changed")
    unsigned = dict(record)
    claimed = unsigned.pop("record_sha256")
    if not isinstance(claimed, str) or _SHA256.fullmatch(claimed) is None:
        raise ActivationError("V4 activation record hash is invalid")
    if _sha256(_canonical(unsigned)) != claimed:
        raise ActivationError("V4 activation record was modified")
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
    "validate",
]
