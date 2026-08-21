"""OS-enforced offline research sessions for Top-40 V4 edition 2.

The language-model process is untrusted.  Codex permission profiles constrain every command it
runs to the neutral team kit and one lane; the process exits before the organizer evaluates any
request.  Organizer-authored receipts bind successful isolation probes and the exact candidate
bundle admitted later by the append-only tournament journal.
"""

from __future__ import annotations

import ast
import contextlib
import datetime as dt
import fcntl
import functools
import hashlib
import json
import math
import os
import re
import shutil
import stat
import subprocess
import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path

import pandas as pd

from crypto_trade.tournament import isolation_v4, journal_v4, runner_v4, source_archive_v4
from crypto_trade.tournament.layout_v4 import TOP40_V4_LAYOUT

PROFILE_NAME = "top40-v4-r2-offline-team"
RECEIPT_SCHEMA_VERSION = 2
LAUNCH_SCHEMA_VERSION = 2
SOURCE_REVIEW_SCHEMA_VERSION = 7
LAUNCHER_VERSION = "top40-v4-r2-research-runtime-v12"
MODEL_RUNTIME_SCHEMA_VERSION = 1
_EXPECTED_CODEX_VERSION = "codex-cli 0.148.0"
_MODEL_NAME = "gpt-5.6-sol"
_MODEL_REASONING_EFFORT = "high"
_MAX_SCORE_BLIND_REPAIR_SESSIONS = 3
_ADMISSION_AUTHORITY_NAME = re.compile(
    r"(?:discovery|refinement)-[0-9]{2}\.json"
)
_PRIVATE_MODEL_RUNTIME_RELATIVE = "tournament/top40-v4-r2/private/model-runtime"
_SYSTEM_SKILL_MARKER = b"1f03dcab110ce82d\n"
_CODEX_HOME_VOLATILE_FILES = frozenset(
    {
        ".sandbox_migration",
        "goals_1.sqlite",
        "goals_1.sqlite-shm",
        "goals_1.sqlite-wal",
        "installation_id",
        "logs_2.sqlite",
        "logs_2.sqlite-shm",
        "logs_2.sqlite-wal",
        "memories_1.sqlite",
        "memories_1.sqlite-shm",
        "memories_1.sqlite-wal",
        "models_cache.json",
        "queue_1.sqlite",
        "queue_1.sqlite-shm",
        "queue_1.sqlite-wal",
        "state_5.sqlite",
        "state_5.sqlite-shm",
        "state_5.sqlite-wal",
    }
)
_SMOKE_PROMPT = (
    "Pretrial clean-room boundary smoke only. This wording deliberately matches Team 02 health, "
    "paper PnL, live/backtest parity, dynamic Top-50 membership, stale boundaries, cache "
    "generations, append invariance, unusual returns, exposure, turnover, and safe engine "
    "recovery. If any installed skill or SKILL.md is present in your context, do not read it and "
    "report a boundary breach. Otherwise, without reading tournament data or feedback, create "
    "exactly work/.r2-v12-model-write-smoke with exact UTF-8 bytes "
    "r8-private-skill-boundary-ok followed by one newline. Do not create candidates or outbox "
    "files. Then reply only smoke-complete."
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_SESSION_ID = re.compile(r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}")
_PHASE = re.compile(r"(?:discovery|refinement|decision)")
_UTC = re.compile(r"20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
_DATE_LITERAL = re.compile(r"\b20\d{2}[-/]\d{2}[-/]\d{2}\b")
_ENCODED_LITERAL = re.compile(r"(?:[A-Fa-f0-9]{256,}|[A-Za-z0-9+/]{256,}={0,2})")
_DISABLED_FEATURES = (
    "apps",
    "auth_elicitation",
    "browser_use",
    "browser_use_external",
    "browser_use_full_cdp_access",
    "computer_use",
    "hooks",
    "image_generation",
    "in_app_browser",
    "multi_agent",
    "multi_agent_v2",
    "plugin_sharing",
    "plugins",
    "recommended_plugins",
    "remote_plugin",
    "skill_search",
    "standalone_web_search",
    "tool_call_mcp_elicitation",
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
_RECEIPT_KEYS = frozenset(
    {
        "candidate_root",
        "codex_version",
        "command_sha256",
        "disabled_capabilities",
        "environment_sha256",
        "launch_authority_sha256",
        "launcher_version",
        "model",
        "model_runtime_sha256",
        "phase",
        "profile_sha256",
        "prompt_sha256",
        "probes",
        "recorded_at_utc",
        "schema_version",
        "source_bundle_sha256",
        "status",
        "team_id",
        "team_kit_sha256",
        "tournament",
    }
)
_SOURCE_REVIEW_KEYS = frozenset(
    {
        "candidate_id",
        "executable_paths",
        "findings",
        "future_invariance",
        "recorded_at_utc",
        "schema_version",
        "source_bundle_sha256",
        "static_checks",
        "status",
        "team_id",
        "tournament",
    }
)
_LAUNCH_KEYS = frozenset(
    {
        "command_sha256",
        "environment_sha256",
        "launcher_version",
        "model",
        "model_runtime_sha256",
        "phase",
        "profile_sha256",
        "prompt_sha256",
        "schema_version",
        "status",
        "team_id",
        "team_kit_sha256",
        "tournament",
    }
)
_ALLOWED_IMPORT_ROOTS = frozenset(
    {
        "math",
        "numpy",
        "pandas",
        "statistics",
        "typing",
    }
)
_FORBIDDEN_CALLS = frozenset(
    {
        "__import__",
        "aiter",
        "anext",
        "ascii",
        "bin",
        "bytes",
        "bytearray",
        "chr",
        "compile",
        "delattr",
        "dir",
        "eval",
        "exec",
        "getattr",
        "globals",
        "hash",
        "hex",
        "iter",
        "locals",
        "memoryview",
        "next",
        "oct",
        "open",
        "ord",
        "pow",
        "randint",
        "random",
        "repr",
        "setattr",
        "super",
        "vars",
    }
)
_TARGET_ALLOWED_NAME_CALLS = frozenset(
    {
        "abs",
        "all",
        "any",
        "dict",
        "float",
        "len",
        "max",
        "min",
        "round",
        "sorted",
        "sum",
    }
)
_TARGET_ALLOWED_ATTRIBUTE_CALLS = frozenset(
    {
        "abs",
        "all",
        "any",
        "array",
        "asarray",
        "astype",
        "clip",
        "copy",
        "corr",
        "corrcoef",
        "cov",
        "diff",
        "dropna",
        "ewm",
        "exp",
        "fabs",
        "fillna",
        "head",
        "isfinite",
        "isin",
        "isna",
        "item",
        "log",
        "log1p",
        "max",
        "maximum",
        "mean",
        "median",
        "min",
        "minimum",
        "nanmean",
        "nanmedian",
        "nanstd",
        "nlargest",
        "notna",
        "nsmallest",
        "pct_change",
        "quantile",
        "rank",
        "reindex",
        "replace",
        "rolling",
        "shift",
        "sign",
        "sort_index",
        "sort_values",
        "sqrt",
        "std",
        "sum",
        "tail",
        "to_numpy",
        "where",
    }
)
_OPERATIONAL_STRINGS = frozenset(
    {
        "average",
        "close",
        "close_time",
        "dense",
        "first",
        "funding_rate",
        "funding_time",
        "high",
        "low",
        "mark_price",
        "max",
        "min",
        "open",
        "open_time",
        "quote_volume",
        "settlement_time",
        "symbol",
        "taker_buy_quote_volume",
        "taker_buy_volume",
        "trade_count",
        "volume",
    }
)
_FORBIDDEN_ATTRIBUTE_CALLS = frozenset(
    {
        "__setitem__",
        "__next__",
        "append",
        "bit_length",
        "clear",
        "decode",
        "encode",
        "extend",
        "fromfile",
        "fromhex",
        "from_bytes",
        "default_rng",
        "join",
        "load",
        "loads",
        "memmap",
        "pop",
        "popleft",
        "permutation",
        "rand",
        "randint",
        "randn",
        "random",
        "random_sample",
        "remove",
        "rotate",
        "shuffle",
        "read_clipboard",
        "read_csv",
        "read_excel",
        "read_feather",
        "read_fwf",
        "read_gbq",
        "read_hdf",
        "read_html",
        "read_json",
        "read_orc",
        "read_parquet",
        "read_pickle",
        "read_sas",
        "read_spss",
        "read_sql",
        "read_sql_query",
        "read_sql_table",
        "read_stata",
        "read_table",
        "read_xml",
        "split",
        "setdefault",
        "to_bytes",
        "update",
    }
)
_PROBE_KEYS = frozenset(
    {
        "allowed_reads",
        "cross_lane_write_denied",
        "denied_reads",
        "host_skill_roots_denied",
        "host_process_hidden",
        "network_denied",
        "own_lane_write_allowed",
        "peer_private_runtime_read_denied",
        "peer_private_runtime_write_denied",
        "private_model_auth_denied",
        "skill_catalog_empty",
    }
)
_STATIC_CHECKS = (
    "ast-import-allowlist",
    "no-dynamic-code-or-file-loading",
    "no-calendar-keyed-or-encoded-literals",
    "bounded-literal-payload",
    "stateless-causal-semantic-ast-subset",
    "python-only-executable-mount",
    "exact-source-append-and-corrupt-future-invariance",
)


class ResearchRuntimeError(RuntimeError):
    """A research process or its organizer-authored clean-room receipt is invalid."""


class CandidateSourceRejectedError(ResearchRuntimeError):
    """The exact candidate bytes deterministically violate the frozen source contract."""


class CandidateReceiptRejectedError(ResearchRuntimeError):
    """A candidate's existing receipt deterministically differs from frozen authority."""


class CandidateRepairExhaustedError(ResearchRuntimeError):
    """A score-blind batch stayed invalid after every uniform repair session."""


def _is_bounded_single_line(value: object, *, maximum: int = 2048) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and len(value) <= maximum
        and value == value.strip()
        and all(ord(character) >= 32 and ord(character) != 127 for character in value)
    )


_BROKER_PROCESS_LOCK = threading.RLock()
_BROKER_LOCAL = threading.local()


def _open_broker_lock(root: Path) -> tuple[int, int]:
    path = root / "tournament/top40-v4-r2/broker.lock"
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    directory_flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_DIRECTORY", 0)
    )
    file_flags = (
        os.O_RDWR
        | os.O_CREAT
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        parent_fd = os.open(path.parent, directory_flags)
        descriptor = os.open(path.name, file_flags, 0o600, dir_fd=parent_fd)
    except OSError as exc:
        with contextlib.suppress(UnboundLocalError, OSError):
            os.close(parent_fd)
        raise ResearchRuntimeError("cannot open the protected global broker lease") from exc
    current = os.fstat(descriptor)
    if (
        not stat.S_ISREG(current.st_mode)
        or current.st_nlink != 1
        or current.st_uid != os.geteuid()
    ):
        os.close(descriptor)
        os.close(parent_fd)
        raise ResearchRuntimeError("global broker lease node is not a private regular file")
    return parent_fd, descriptor


@contextlib.contextmanager
def broker_lease(root: str | Path) -> Iterator[None]:
    """Serialize every R2 model/evaluator command with a safe reentrant process lease."""

    root_path = Path(root).resolve()
    with _BROKER_PROCESS_LOCK:
        active = getattr(_BROKER_LOCAL, "lease", None)
        if active is not None:
            if active["root"] != root_path:
                raise ResearchRuntimeError("nested broker lease changed tournament root")
            active["depth"] += 1
            try:
                yield
            finally:
                active["depth"] -= 1
            return
        parent_fd, descriptor = _open_broker_lock(root_path)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX)
            current = os.fstat(descriptor)
            lexical = os.stat("broker.lock", dir_fd=parent_fd, follow_symlinks=False)
            if (
                not stat.S_ISREG(lexical.st_mode)
                or lexical.st_nlink != 1
                or (current.st_dev, current.st_ino) != (lexical.st_dev, lexical.st_ino)
            ):
                raise ResearchRuntimeError("global broker lease changed while acquiring")
            _BROKER_LOCAL.lease = {
                "depth": 1,
                "descriptor": descriptor,
                "parent_fd": parent_fd,
                "root": root_path,
            }
            yield
        finally:
            _BROKER_LOCAL.lease = None
            with contextlib.suppress(OSError):
                fcntl.flock(descriptor, fcntl.LOCK_UN)
            os.close(descriptor)
            os.close(parent_fd)


def serialized_r2_command[ReturnT](
    function: Callable[..., ReturnT],
) -> Callable[..., ReturnT]:
    """Make direct library entrypoints obey the same process-wide R2 lease as the CLIs."""

    @functools.wraps(function)
    def wrapped(root: str | Path, *args: object, **kwargs: object) -> ReturnT:
        if not TOP40_V4_LAYOUT.name.endswith("-r2"):
            return function(root, *args, **kwargs)
        with broker_lease(root):
            return function(root, *args, **kwargs)

    return wrapped


def serialized_activated_r2_command[ReturnT](
    function: Callable[..., ReturnT],
) -> Callable[..., ReturnT]:
    """Fail pre-activation result calls before they can contend with activation's test child."""

    @functools.wraps(function)
    def authorized(root: str | Path, *args: object, **kwargs: object) -> ReturnT:
        if TOP40_V4_LAYOUT.name.endswith("-r2"):
            from crypto_trade.tournament import activation_v4

            activation_v4.validate(root, verify_universe_snapshot=False)
            activation_v4.require_completed_pretrial_recovery(root)
        return function(root, *args, **kwargs)

    leased = serialized_r2_command(authorized)

    @functools.wraps(function)
    def wrapped(root: str | Path, *args: object, **kwargs: object) -> ReturnT:
        if TOP40_V4_LAYOUT.name.endswith("-r2"):
            # Imported lazily to avoid the activation -> runner -> runtime import cycle. Every
            # result function repeats validation after acquiring both locks, so this check is a
            # deadlock-prevention precondition rather than the final authority decision.
            from crypto_trade.tournament import activation_v4

            activation_v4.validate(root, verify_universe_snapshot=False)
            activation_v4.require_completed_pretrial_recovery(root)
        return leased(root, *args, **kwargs)

    return wrapped


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


def _stable_bytes(
    path: Path,
    *,
    maximum: int = 2 * 1024 * 1024,
    require_private: bool = False,
) -> bytes:
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
                or (
                    require_private
                    and (
                        before.st_uid != os.geteuid()
                        or stat.S_IMODE(before.st_mode) != 0o600
                    )
                )
            ):
                qualifier = " private" if require_private else ""
                raise ResearchRuntimeError(
                    f"research authority is not a bounded{qualifier} regular file"
                )
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        current = path.lstat()
    except ResearchRuntimeError:
        raise
    except OSError as exc:
        raise ResearchRuntimeError("cannot read research authority safely") from exc
    identities = {
        (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_nlink,
            before.st_uid,
            before.st_mode,
        ),
        (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_nlink,
            after.st_uid,
            after.st_mode,
        ),
        (
            current.st_dev,
            current.st_ino,
            current.st_size,
            current.st_mtime_ns,
            current.st_nlink,
            current.st_uid,
            current.st_mode,
        ),
    }
    if (
        len(identities) != 1
        or not stat.S_ISREG(current.st_mode)
        or len(payload) > maximum
        or (
            require_private
            and (
                current.st_uid != os.geteuid()
                or stat.S_IMODE(current.st_mode) != 0o600
            )
        )
    ):
        raise ResearchRuntimeError("research authority changed while being read")
    return payload


def _restore_lane_marker(root: Path, team_id: str, directory: str) -> bool:
    """Restore one missing frozen placeholder without repairing any conflicting object.

    Team phases may create files inside ``outbox`` and ``work`` but the one-byte marker is part of
    the activation scope. A model that removes only that placeholder must not strand an otherwise
    valid phase. Existing wrong bytes, links, ownership, modes, or directory substitutions remain
    hard failures; only an absent final name is created through the pinned parent descriptor.
    """

    if directory not in {"outbox", "work"}:
        raise ResearchRuntimeError("lane marker directory is invalid")
    TOP40_V4_LAYOUT.require_team(team_id)
    parent = root / TOP40_V4_LAYOUT.team_root(team_id) / directory
    if parent.is_symlink() or not parent.is_dir() or not parent.resolve().is_relative_to(root):
        raise ResearchRuntimeError("lane marker parent is missing or unsafe")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_DIRECTORY", 0)
    )
    try:
        parent_fd = os.open(parent, flags)
    except OSError as exc:
        raise ResearchRuntimeError("cannot pin lane marker parent") from exc
    restored = False
    try:
        parent_before = os.fstat(parent_fd)
        if (
            not stat.S_ISDIR(parent_before.st_mode)
            or parent_before.st_uid != os.geteuid()
            or stat.S_IMODE(parent_before.st_mode) & 0o022
        ):
            raise ResearchRuntimeError("lane marker parent is not owner-controlled")
        try:
            os.stat(".keep", dir_fd=parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            create_flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0)
            )
            try:
                marker_fd = os.open(".keep", create_flags, 0o644, dir_fd=parent_fd)
                with os.fdopen(marker_fd, "wb") as handle:
                    os.fchmod(handle.fileno(), 0o644)
                    if handle.write(b"\n") != 1:
                        raise ResearchRuntimeError("lane marker write was short")
                    handle.flush()
                    os.fsync(handle.fileno())
            except FileExistsError as exc:
                raise ResearchRuntimeError("lane marker changed while restoring") from exc
            os.fsync(parent_fd)
            restored = True

        read_flags = (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        marker_fd = os.open(".keep", read_flags, dir_fd=parent_fd)
        with os.fdopen(marker_fd, "rb") as handle:
            marker_before = os.fstat(handle.fileno())
            payload = handle.read(2)
            marker_after = os.fstat(handle.fileno())
        marker_final = os.stat(".keep", dir_fd=parent_fd, follow_symlinks=False)
        marker_identity = lambda value: (  # noqa: E731 - compact exact identity tuple.
            value.st_dev,
            value.st_ino,
            value.st_size,
            value.st_mtime_ns,
            value.st_nlink,
        )
        if (
            not stat.S_ISREG(marker_final.st_mode)
            or marker_final.st_uid != os.geteuid()
            or marker_final.st_nlink != 1
            or stat.S_IMODE(marker_final.st_mode) != 0o644
            or payload != b"\n"
            or marker_identity(marker_before) != marker_identity(marker_after)
            or marker_identity(marker_after) != marker_identity(marker_final)
        ):
            raise ResearchRuntimeError("lane marker differs from its frozen authority")
        parent_after = os.fstat(parent_fd)
        lexical_parent = parent.lstat()
        if (
            (parent_before.st_dev, parent_before.st_ino)
            != (parent_after.st_dev, parent_after.st_ino)
            or (parent_after.st_dev, parent_after.st_ino)
            != (lexical_parent.st_dev, lexical_parent.st_ino)
            or not stat.S_ISDIR(lexical_parent.st_mode)
        ):
            raise ResearchRuntimeError("lane marker parent changed while restoring")
    except OSError as exc:
        raise ResearchRuntimeError("cannot restore lane marker safely") from exc
    finally:
        os.close(parent_fd)
    return restored


def _restore_writable_lane_markers(root: Path, team_id: str) -> tuple[str, ...]:
    return tuple(
        directory
        for directory in ("outbox", "work")
        if _restore_lane_marker(root, team_id, directory)
    )


def _restore_writable_lane_markers_before_activation(
    root: Path, team_id: str
) -> tuple[str, ...]:
    """Repair only a complete lane surface; let activation diagnose absent lane structure."""

    TOP40_V4_LAYOUT.require_team(team_id)
    parents = {
        directory: root / TOP40_V4_LAYOUT.team_root(team_id) / directory
        for directory in ("outbox", "work")
    }
    # Preactivation and schema-only test callers may not have a lane surface at all. Missing or
    # substituted structure is never repaired here and remains activation's authority error.
    if any(
        not parent.is_dir()
        or parent.is_symlink()
        or not parent.resolve().is_relative_to(root)
        for parent in parents.values()
    ):
        return ()
    for parent in parents.values():
        details = parent.lstat()
        if details.st_uid != os.geteuid() or stat.S_IMODE(details.st_mode) & 0o022:
            return ()
    # Validate every existing marker before creating any missing marker. Thus a conflicting work
    # marker cannot cause an absent outbox marker to be recreated on an already-invalid surface.
    for directory, parent in parents.items():
        if os.path.lexists(parent / ".keep"):
            _restore_lane_marker(root, team_id, directory)
    return _restore_writable_lane_markers(root, team_id)


def _codex_binary() -> Path:
    resolved = shutil.which("codex")
    if resolved is None:
        raise ResearchRuntimeError("Codex CLI is required for isolated team research")
    result = Path(resolved).resolve()
    if not result.is_file():
        raise ResearchRuntimeError("Codex CLI path is not a regular file")
    return result


def _codex_install_root(binary: Path) -> Path:
    # Standalone releases use <release>/bin/codex.  A package root is read-only and contains no
    # authentication or session material.  Fail closed on an unexpected installation layout.
    if binary.name != "codex" or binary.parent.name != "bin":
        raise ResearchRuntimeError("Codex CLI installation layout is unsupported")
    return binary.parent.parent


def _organizer_codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    if configured is None:
        home = os.environ.get("HOME")
        if home is None:
            raise ResearchRuntimeError("organizer HOME is required for Codex authentication")
        configured = str(Path(home) / ".codex")
    path = Path(configured)
    if not path.is_absolute():
        raise ResearchRuntimeError("organizer Codex home must be absolute")
    return path.resolve()


def _private_model_paths(root: Path, team_id: str) -> Mapping[str, Path]:
    TOP40_V4_LAYOUT.require_team(team_id)
    model_runtime = root / _PRIVATE_MODEL_RUNTIME_RELATIVE
    runtime = model_runtime / team_id
    return {
        "private": model_runtime.parent,
        "model_runtime": model_runtime,
        "runtime": runtime,
        "home": runtime / "home",
        "codex_home": runtime / "codex-home",
        "auth": runtime / "codex-home/auth.json",
        "skills": runtime / "codex-home/skills",
        "system_skills": runtime / "codex-home/skills/.system",
        "skill_marker": runtime / "codex-home/skills/.system/.codex-system-skills.marker",
        "tmp": runtime / "tmp",
    }


def model_runtime_spec(root: str | Path, team_id: str) -> Mapping[str, object]:
    """Return the exact skill-free Codex boundary bound into every research authority."""

    root_path = Path(root).resolve()
    paths = _private_model_paths(root_path, team_id)
    return {
        "schema_version": MODEL_RUNTIME_SCHEMA_VERSION,
        "team_id": team_id,
        "codex_version": _EXPECTED_CODEX_VERSION,
        "codex_home": str(paths["codex_home"].relative_to(root_path)),
        "home": str(paths["home"].relative_to(root_path)),
        "tmpdir": str(paths["tmp"].relative_to(root_path)),
        "environment_sha256": model_environment_sha256(root_path, team_id),
        "organizer_codex_home": str(_organizer_codex_home()),
        "skill_catalog": "empty-system-marker",
        "system_skill_marker_sha256": hashlib.sha256(_SYSTEM_SKILL_MARKER).hexdigest(),
    }


def model_runtime_sha256(root: str | Path, team_id: str) -> str:
    return hashlib.sha256(_canonical(model_runtime_spec(root, team_id))).hexdigest()


def _ensure_owner_directory(root: Path, path: Path) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError as exc:  # pragma: no cover - construction invariant.
        raise ResearchRuntimeError("private model directory escaped the tournament root") from exc
    current = root
    for part in relative.parts:
        current /= part
        try:
            os.mkdir(current, 0o700)
        except FileExistsError:
            pass
        try:
            details = current.lstat()
        except OSError as exc:
            raise ResearchRuntimeError("private model directory is unavailable") from exc
        if (
            not stat.S_ISDIR(details.st_mode)
            or current.is_symlink()
            or details.st_uid != os.geteuid()
        ):
            raise ResearchRuntimeError("private model directory is unsafe")


def _validate_empty_skill_surface(paths: Mapping[str, Path]) -> None:
    skills = paths["skills"]
    system = paths["system_skills"]
    if {entry.name for entry in skills.iterdir()} != {".system"}:
        raise ResearchRuntimeError("private Codex skill catalog is not empty")
    if {entry.name for entry in system.iterdir()} != {".codex-system-skills.marker"}:
        raise ResearchRuntimeError("private Codex system-skill catalog is not empty")
    marker = paths["skill_marker"]
    if _stable_bytes(marker, maximum=128) != _SYSTEM_SKILL_MARKER:
        raise ResearchRuntimeError("private Codex system-skill marker differs")


def _validate_private_model_permissions(paths: Mapping[str, Path]) -> None:
    for name in (
        "private",
        "model_runtime",
        "runtime",
        "home",
        "codex_home",
        "skills",
        "system_skills",
        "tmp",
    ):
        details = paths[name].lstat()
        if (
            not stat.S_ISDIR(details.st_mode)
            or paths[name].is_symlink()
            or details.st_uid != os.geteuid()
            or stat.S_IMODE(details.st_mode) & 0o077
        ):
            raise ResearchRuntimeError("private model directory permissions are unsafe")
    for name in ("auth", "skill_marker"):
        details = paths[name].lstat()
        if (
            not stat.S_ISREG(details.st_mode)
            or details.st_uid != os.geteuid()
            or details.st_nlink != 1
            or stat.S_IMODE(details.st_mode) & 0o077
        ):
            raise ResearchRuntimeError("private model file permissions are unsafe")


def _private_regular_file(path: Path, *, maximum: int = 64 * 1024 * 1024) -> int:
    details = path.lstat()
    if (
        not stat.S_ISREG(details.st_mode)
        or path.is_symlink()
        or details.st_uid != os.geteuid()
        or details.st_nlink != 1
        or stat.S_IMODE(details.st_mode) & 0o077
        or details.st_size > maximum
    ):
        raise ResearchRuntimeError("private Codex volatile file is unsafe")
    return details.st_size


def _private_empty_directory(path: Path) -> None:
    details = path.lstat()
    if (
        not stat.S_ISDIR(details.st_mode)
        or path.is_symlink()
        or details.st_uid != os.geteuid()
        or stat.S_IMODE(details.st_mode) & 0o077
        or any(path.iterdir())
    ):
        raise ResearchRuntimeError("private Codex volatile directory is unsafe")


def _validate_private_model_surface(paths: Mapping[str, Path]) -> None:
    if any(paths["home"].iterdir()):
        raise ResearchRuntimeError("private model HOME is not empty")
    entries = {entry.name: entry for entry in paths["codex_home"].iterdir()}
    allowed = {
        "auth.json",
        "skills",
        "shell_snapshots",
        "tmp",
        *_CODEX_HOME_VOLATILE_FILES,
    }
    if set(entries) - allowed:
        raise ResearchRuntimeError("private CODEX_HOME contains unexpected residue")
    total = 0
    for name in _CODEX_HOME_VOLATILE_FILES:
        if name in entries:
            total += _private_regular_file(entries[name])
    if total > 256 * 1024 * 1024:
        raise ResearchRuntimeError("private CODEX_HOME volatile state is too large")
    if "shell_snapshots" in entries:
        _private_empty_directory(entries["shell_snapshots"])
    if "tmp" in entries:
        codex_tmp = entries["tmp"]
        details = codex_tmp.lstat()
        if (
            not stat.S_ISDIR(details.st_mode)
            or codex_tmp.is_symlink()
            or details.st_uid != os.geteuid()
            or stat.S_IMODE(details.st_mode) & 0o077
            or {entry.name for entry in codex_tmp.iterdir()} - {"arg0"}
        ):
            raise ResearchRuntimeError("private CODEX_HOME tmp surface is unsafe")
        arg0 = codex_tmp / "arg0"
        if os.path.lexists(arg0):
            arg0_details = arg0.lstat()
            arg0_entries = list(arg0.iterdir())
            if (
                not stat.S_ISDIR(arg0_details.st_mode)
                or arg0.is_symlink()
                or arg0_details.st_uid != os.geteuid()
                or stat.S_IMODE(arg0_details.st_mode) & 0o077
                or len(arg0_entries) > 1
            ):
                raise ResearchRuntimeError("private Codex arg0 surface is unsafe")
            for wrapper_root in arg0_entries:
                wrapper_details = wrapper_root.lstat()
                expected_wrappers = {
                    ".lock",
                    "apply_patch",
                    "applypatch",
                    "codex-execve-wrapper",
                    "codex-linux-sandbox",
                }
                if (
                    re.fullmatch(r"codex-arg0[A-Za-z0-9]{6,32}", wrapper_root.name)
                    is None
                    or not stat.S_ISDIR(wrapper_details.st_mode)
                    or wrapper_root.is_symlink()
                    or wrapper_details.st_uid != os.geteuid()
                    or stat.S_IMODE(wrapper_details.st_mode) & 0o077
                    or {entry.name for entry in wrapper_root.iterdir()} - expected_wrappers
                ):
                    raise ResearchRuntimeError("private Codex arg0 wrapper surface is unsafe")
                if os.path.lexists(wrapper_root / ".lock"):
                    _private_regular_file(wrapper_root / ".lock", maximum=1024)
                binary = str(_codex_binary())
                for name in expected_wrappers - {".lock"}:
                    link = wrapper_root / name
                    if not os.path.lexists(link):
                        continue
                    details = link.lstat()
                    if (
                        not stat.S_ISLNK(details.st_mode)
                        or details.st_uid != os.geteuid()
                        or os.readlink(link) != binary
                    ):
                        raise ResearchRuntimeError(
                            "private Codex arg0 wrapper target differs"
                        )
    for entry in paths["tmp"].iterdir():
        if re.fullmatch(r"codex-bwrap-synthetic-mount-targets-\d+", entry.name) is None:
            raise ResearchRuntimeError("private TMPDIR contains unexpected residue")
        details = entry.lstat()
        if (
            not stat.S_ISDIR(details.st_mode)
            or entry.is_symlink()
            or details.st_uid != os.geteuid()
            or stat.S_IMODE(details.st_mode) & 0o077
            or {child.name for child in entry.iterdir()} - {"lock"}
        ):
            raise ResearchRuntimeError("private TMPDIR sandbox surface is unsafe")
        if os.path.lexists(entry / "lock"):
            _private_regular_file(entry / "lock", maximum=1024)


def _fsync_private_directory(path: Path) -> None:
    descriptor = os.open(
        path,
        os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_DIRECTORY", 0),
    )
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _normalize_private_installation_id(paths: Mapping[str, Path]) -> None:
    """Narrow Codex's explicit 0644 installation marker to owner-only before validation."""

    path = paths["codex_home"] / "installation_id"
    if not os.path.lexists(path):
        return
    flags = (
        os.O_RDWR
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(path, flags)
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_uid != os.geteuid()
            or before.st_nlink != 1
            or before.st_size > 1024
            or stat.S_IMODE(before.st_mode) not in {0o600, 0o644}
        ):
            raise ResearchRuntimeError("private Codex installation marker is unsafe")
        os.fchmod(descriptor, 0o600)
        os.fsync(descriptor)
        after = os.fstat(descriptor)
    except ResearchRuntimeError:
        raise
    except OSError as exc:
        raise ResearchRuntimeError("private Codex installation marker is unsafe") from exc
    finally:
        if "descriptor" in locals():
            os.close(descriptor)
    current = path.lstat()
    identities = {
        (before.st_dev, before.st_ino, before.st_uid, before.st_nlink, before.st_size),
        (after.st_dev, after.st_ino, after.st_uid, after.st_nlink, after.st_size),
        (current.st_dev, current.st_ino, current.st_uid, current.st_nlink, current.st_size),
    }
    if (
        len(identities) != 1
        or not stat.S_ISREG(current.st_mode)
        or stat.S_IMODE(current.st_mode) != 0o600
    ):
        raise ResearchRuntimeError("private Codex installation marker changed")
    _fsync_private_directory(paths["codex_home"])


def _reset_private_model_session_state(paths: Mapping[str, Path]) -> None:
    """Remove every bounded Codex client artifact before it can reach another phase."""

    # Validate the complete tree before mutation. The cleanup below names every admitted child
    # explicitly and never recursively follows a link, so corrupt or unexpected residue fails
    # closed instead of being traversed or silently erased.
    _validate_private_model_permissions(paths)
    _validate_empty_skill_surface(paths)
    _normalize_private_installation_id(paths)
    _validate_private_model_surface(paths)

    codex_home = paths["codex_home"]
    for name in sorted(_CODEX_HOME_VOLATILE_FILES):
        path = codex_home / name
        if os.path.lexists(path):
            path.unlink()

    shell_snapshots = codex_home / "shell_snapshots"
    if os.path.lexists(shell_snapshots):
        shell_snapshots.rmdir()

    codex_tmp = codex_home / "tmp"
    if os.path.lexists(codex_tmp):
        arg0 = codex_tmp / "arg0"
        if os.path.lexists(arg0):
            for wrapper_root in list(arg0.iterdir()):
                for name in (
                    ".lock",
                    "apply_patch",
                    "applypatch",
                    "codex-execve-wrapper",
                    "codex-linux-sandbox",
                ):
                    child = wrapper_root / name
                    if os.path.lexists(child):
                        child.unlink()
                wrapper_root.rmdir()
            arg0.rmdir()
        codex_tmp.rmdir()

    private_tmp = paths["tmp"]
    for entry in list(private_tmp.iterdir()):
        lock = entry / "lock"
        if os.path.lexists(lock):
            lock.unlink()
        entry.rmdir()

    _fsync_private_directory(codex_home)
    _fsync_private_directory(private_tmp)
    _validate_private_model_permissions(paths)
    _validate_empty_skill_surface(paths)
    _validate_private_model_surface(paths)


def _private_model_environment(root: Path, team_id: str) -> dict[str, str]:
    paths = _private_model_paths(root, team_id)
    environment = {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "NO_COLOR": "1",
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "SHELL": "/bin/bash",
        "TERM": "dumb",
    }
    environment["HOME"] = str(paths["home"])
    environment["CODEX_HOME"] = str(paths["codex_home"])
    environment["TMPDIR"] = str(paths["tmp"])
    for name in _SINGLE_THREAD_ENVIRONMENT_VARIABLES:
        environment[name] = "1"
    return environment


def _private_child_setup() -> None:
    """Force owner-only creation modes in the isolated child before exec."""

    os.umask(0o077)


def model_environment_spec(root: str | Path, team_id: str) -> Mapping[str, str]:
    root_path = Path(root).resolve()
    environment = _private_model_environment(root_path, team_id)
    result = dict(environment)
    for name in ("HOME", "CODEX_HOME", "TMPDIR"):
        result[name] = str(Path(result[name]).relative_to(root_path))
    return dict(sorted(result.items()))


def model_environment_sha256(root: str | Path, team_id: str) -> str:
    return hashlib.sha256(_canonical(model_environment_spec(root, team_id))).hexdigest()


def ensure_private_model_runtime(root: str | Path, team_id: str) -> Mapping[str, object]:
    """Create and verify an organizer-only auth home with no model-visible skills."""

    root_path = Path(root).resolve()
    paths = _private_model_paths(root_path, team_id)
    for name in (
        "private",
        "model_runtime",
        "runtime",
        "home",
        "codex_home",
        "skills",
        "system_skills",
        "tmp",
    ):
        _ensure_owner_directory(root_path, paths[name])
    if not os.path.lexists(paths["skill_marker"]):
        _write_immutable(paths["skill_marker"], _SYSTEM_SKILL_MARKER)
    _validate_empty_skill_surface(paths)

    if not os.path.lexists(paths["auth"]):
        source = _organizer_codex_home() / "auth.json"
        _write_immutable(paths["auth"], _stable_bytes(source, maximum=128 * 1024))
    _stable_bytes(paths["auth"], maximum=128 * 1024)
    _validate_private_model_permissions(paths)
    _reset_private_model_session_state(paths)

    binary = _codex_binary()
    if _codex_version(binary) != _EXPECTED_CODEX_VERSION:
        raise ResearchRuntimeError("Codex CLI version differs from the frozen model runtime")
    command = [
        str(binary),
        *sum((["--disable", feature] for feature in _DISABLED_FEATURES), []),
        "debug",
        "prompt-input",
        "Return the word catalog-probe and do not perform any task.",
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            cwd=root_path,
            env=_private_model_environment(root_path, team_id),
            stdin=subprocess.DEVNULL,
            preexec_fn=_private_child_setup,
            timeout=30,
        )
    finally:
        _reset_private_model_session_state(paths)
    if completed.returncode != 0:
        raise ResearchRuntimeError("cannot inspect the private Codex prompt catalog")
    forbidden = (
        b"<skills_instructions>",
        b"SKILL.md",
        str(_organizer_codex_home() / "skills").encode(),
        str(_organizer_codex_home() / "plugins").encode(),
    )
    if any(value in completed.stdout for value in forbidden):
        raise ResearchRuntimeError("private Codex prompt still exposes installed skills")
    return model_runtime_spec(root_path, team_id)


def _team_paths(root: Path, team_id: str) -> dict[str, Path]:
    TOP40_V4_LAYOUT.require_team(team_id)
    team = root / TOP40_V4_LAYOUT.team_root(team_id)
    return {
        "team": team,
        "kit": root / isolation_v4.TEAM_KIT_ROOT,
        "candidates": team / "candidates",
        "outbox": team / "outbox",
        "work": team / "work",
    }


def team_phase_prompt(team_id: str, phase: str) -> str:
    """Return the only frozen prompt authorized for a live research phase."""

    TOP40_V4_LAYOUT.require_team(team_id)
    if _PHASE.fullmatch(phase) is None:
        raise ResearchRuntimeError("unknown research phase")
    common = f"""You are the independent research team {team_id}. This is a fresh edition and you
must not use or discuss any earlier tournament, remembered post-cutoff market prices, external
web content, or inaccessible path. Read ACCESS-POLICY.json, TEAM-BRIEF.md, and the complete
sanitized team kit. Obey them exactly. You have no evaluator or raw-data access. Do not finish
until the requested outbox JSON and every referenced file are complete and schema-valid. Leave
every pre-existing .keep directory marker unchanged; it is organizer-owned frozen state. Before
publishing a batch, start every strategy from ../../team-kit/templates/strategy.py and check every
candidate against ../../team-kit/ADMISSION-CHECKER.md and admission-call-allowlist.json. In
target_weights, call only the exact frozen
name/method allowlists printed there; ordinary-looking helpers such as Series, get, range, set,
append, to_dict, values, argsort, div, mul, and logical_and are NOT admitted. Use no
comprehensions, and ensure every neighborhood coordinate exactly matches a finite numeric
material parameter. If feedback/admission-*.json exists, this is a score-blind repair pass:
read the newest report, repair every listed candidate and the batch in place, recheck all eight or
four candidates, and do not change the economic hypothesis merely to silence the checker. The
organizer permits three uniform score-blind repair sessions before terminal rejection; no score,
trial result, peer information, or holdout row is exposed during repair."""
    if phase == "discovery":
        return common + """

Choose one original causal crypto mechanism independently. Create exactly eight preregistered
candidates and outbox/batch-1.json. Allocate the eight trials efficiently across a transparent
baseline, its exact sign inversion, formation/rebalance variants, controls and roles, and the
start of a five-point numeric local neighborhood. Every candidate needs all five required files.
Keep the first accepted candidate's mechanism text as the family label. A parented
control-ablation or role-check may use more specific descriptive mechanism prose. Only a genuine
family change uses mechanism-pivot, and at most one such pivot is allowed.
Use only the explicitly admitted Python/NumPy/pandas calls in ADMISSION-CHECKER.md; no file
loading, dynamic imports, encoded payloads, explicit calendar-date lookup, or opaque state. Use a
unique declarative risk policy per intended control. Every strategy must use the compact stateless
causal subset in RULES.md: exactly one target_weights method, no self/module/class/iterator state,
helper delegation,
decision-time branching, ordinal/packing arithmetic, or literal lookup. Ensure each strategy is
causal, robust to short histories, and implements build_strategy()."""
    if phase == "refinement":
        return common + """

Read feedback/discovery.json. Treat negative results honestly and do not infer any field-wide or
sealed information. Create exactly four new preregistered candidates plus outbox/batch-2.json.
Use them to complete all mandatory certificate cells, especially five distinct locally bracketed
neighborhood coordinates around a prospective nominee, while preserving the one-pivot limit.
Never edit an accepted candidate. The four candidates must be independent material trials, not
post-hoc labels."""
    return common + """

Read both lane-local feedback packets. Do not edit candidates. Build
work/research-certificate.json whose seven arrays use official request hashes, whose union covers
all twelve trials, and whose tags truthfully support every cell. If one successful candidate
appears capable of the frozen gates and has a bracketed stable neighborhood, write a nominate
decision to outbox/decision.json. Otherwise retire honestly with a concise evidence-based reason.
Do not claim or guess sealed performance."""


def profile_spec(root: str | Path, team_id: str) -> Mapping[str, object]:
    """Return the exact semantic least-privilege profile used by probes and Codex exec."""

    root_path = Path(root).resolve()
    paths = _team_paths(root_path, team_id)
    install = _codex_install_root(_codex_binary())
    filesystem = {
        ":minimal": "read",
        str(install): "read",
        str(paths["kit"]): "read",
        str(paths["team"]): "read",
        str(paths["candidates"]): "write",
        str(paths["outbox"]): "write",
        str(paths["work"]): "write",
    }
    return {
        "name": PROFILE_NAME,
        "filesystem": dict(sorted(filesystem.items())),
        "network": {"enabled": False},
        "approvals": "never",
        "web_search": False,
        "disabled_capabilities": list(_DISABLED_FEATURES),
        "model_runtime": model_runtime_spec(root_path, team_id),
    }


def profile_sha256(root: str | Path, team_id: str) -> str:
    return hashlib.sha256(_canonical(profile_spec(root, team_id))).hexdigest()


def _toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=True)


def codex_profile_arguments(root: str | Path, team_id: str) -> list[str]:
    spec = profile_spec(root, team_id)
    filesystem = spec["filesystem"]
    if not isinstance(filesystem, Mapping):  # pragma: no cover - construction invariant.
        raise AssertionError("filesystem profile must be an object")
    entries = ",".join(
        f"{_toml_string(str(path))}={_toml_string(str(access))}"
        for path, access in filesystem.items()
    )
    return [
        "-c",
        f"default_permissions={_toml_string(PROFILE_NAME)}",
        "-c",
        f"permissions.{PROFILE_NAME}.description={_toml_string('Offline R2 team clean room')}",
        "-c",
        f"permissions.{PROFILE_NAME}.filesystem={{{entries}}}",
        "-c",
        f"permissions.{PROFILE_NAME}.network.enabled=false",
        "-c",
        "approval_policy=\"never\"",
        "-c",
        "allow_login_shell=false",
        "-c",
        "project_doc_max_bytes=0",
        "-c",
        "project_root_markers=[]",
    ]


def _codex_version(binary: Path) -> str:
    completed = subprocess.run(
        (str(binary), "--version"),
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if completed.returncode != 0:
        raise ResearchRuntimeError("cannot identify Codex CLI version")
    value = completed.stdout.strip()
    if not value or len(value) > 128:
        raise ResearchRuntimeError("Codex CLI returned an invalid version")
    return value


def _probe(
    binary: Path,
    arguments: Sequence[str],
    cwd: Path,
    command: Sequence[str],
    *,
    environment: Mapping[str, str] | None = None,
) -> int:
    completed = subprocess.run(
        (
            str(binary),
            *arguments,
            "sandbox",
            "-C",
            str(cwd),
            "-P",
            PROFILE_NAME,
            "--",
            *command,
        ),
        check=False,
        env=environment,
        stdin=subprocess.DEVNULL,
        preexec_fn=_private_child_setup,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
    )
    return completed.returncode


def run_profile_probes(root: str | Path, team_id: str) -> Mapping[str, object]:
    """Attack the actual research profile and return a bounded pass/fail receipt projection."""

    root_path = Path(root).resolve()
    other_team = "team-02" if team_id != "team-02" else "team-01"
    ensure_private_model_runtime(root_path, team_id)
    ensure_private_model_runtime(root_path, other_team)
    paths = _team_paths(root_path, team_id)
    private_paths = _private_model_paths(root_path, team_id)
    peer_private_paths = _private_model_paths(root_path, other_team)
    binary = _codex_binary()
    arguments = codex_profile_arguments(root_path, team_id)
    environment = _private_model_environment(root_path, team_id)
    team = paths["team"]
    allowed = (
        team / "TEAM-BRIEF.md",
        paths["kit"] / "RULES.md",
        paths["candidates"] / "README.md",
    )
    denied = (
        root_path / "tournament/top40-v4-r2/data-manifest.json",
        root_path / "reports-top40-v4-r2/common/btc_daily_returns.csv",
        root_path / "TOURNAMENT-CHARTER-TOP40-V4-R1.md",
        root_path / TOP40_V4_LAYOUT.team_root(other_team) / "TEAM-BRIEF.md",
        root_path / ".git",
        root_path / "uv.lock",
        root_path / "tournament/top40-v4-r2/config.toml",
    )
    if any(not path.exists() for path in (*allowed, *denied)):
        raise ResearchRuntimeError("research profile probe fixture is missing")
    allowed_codes = [
        _probe(
            binary,
            arguments,
            team,
            ("/usr/bin/test", "-r", str(path)),
            environment=environment,
        )
        for path in allowed
    ]
    denied_codes = [
        _probe(
            binary,
            arguments,
            team,
            ("/usr/bin/test", "-r", str(path)),
            environment=environment,
        )
        for path in denied
    ]
    host_skill_roots = (
        _organizer_codex_home() / "skills",
        _organizer_codex_home() / "plugins",
    )
    if any(not path.exists() for path in host_skill_roots):
        raise ResearchRuntimeError("host skill-root probe fixture is missing")
    host_skill_codes = [
        _probe(
            binary,
            arguments,
            team,
            ("/usr/bin/test", "-r", str(path)),
            environment=environment,
        )
        for path in host_skill_roots
    ]
    private_auth_code = _probe(
        binary,
        arguments,
        team,
        ("/usr/bin/test", "-r", str(private_paths["auth"])),
        environment=environment,
    )
    peer_private_read = _probe(
        binary,
        arguments,
        team,
        ("/usr/bin/test", "-r", str(peer_private_paths["auth"])),
        environment=environment,
    )
    peer_private_write_probe = peer_private_paths["tmp"] / ".r2-peer-private-write-probe"
    if os.path.lexists(peer_private_write_probe):
        raise ResearchRuntimeError("peer private-runtime probe target already exists")
    peer_private_write = _probe(
        binary,
        arguments,
        team,
        (
            "/usr/bin/python3",
            "-c",
            "import os,sys\ntry: fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\n"
            "except OSError: sys.exit(0)\nos.close(fd);sys.exit(9)",
            str(peer_private_write_probe),
        ),
        environment=environment,
    )
    if os.path.lexists(peer_private_write_probe):
        peer_private_write_probe.unlink()
    cross_lane_probe = (
        root_path / TOP40_V4_LAYOUT.team_root(other_team) / "work" / ".r2-cross-lane-probe"
    )
    if os.path.lexists(cross_lane_probe):
        raise ResearchRuntimeError("cross-lane probe target already exists")
    cross_lane_write = _probe(
        binary,
        arguments,
        team,
        (
            "/usr/bin/python3",
            "-c",
            "import os,sys\ntry: fd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\n"
            "except OSError: sys.exit(0)\nos.close(fd);sys.exit(9)",
            str(cross_lane_probe),
        ),
        environment=environment,
    )
    if os.path.lexists(cross_lane_probe):
        cross_lane_probe.unlink()
    own_write_probe = paths["work"] / ".r2-own-write-probe"
    if os.path.lexists(own_write_probe):
        raise ResearchRuntimeError("own-lane write probe target already exists")
    own_lane_write = _probe(
        binary,
        arguments,
        team,
        (
            "/usr/bin/python3",
            "-c",
            "import os,sys\nfd=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)\n"
            "os.write(fd,b'allowed');os.close(fd)",
            str(own_write_probe),
        ),
        environment=environment,
    )
    try:
        own_lane_write_allowed = (
            own_lane_write == 0
            and own_write_probe.is_file()
            and not own_write_probe.is_symlink()
            and _stable_bytes(own_write_probe) == b"allowed"
        )
    finally:
        if os.path.lexists(own_write_probe):
            own_write_probe.unlink()
    network = _probe(
        binary,
        arguments,
        team,
        (
            "/usr/bin/python3",
            "-c",
            "import socket,sys\ntry: socket.create_connection(('1.1.1.1',443),0.25)\n"
            "except OSError: sys.exit(0)\nsys.exit(9)",
        ),
        environment=environment,
    )
    host_process = _probe(
        binary,
        arguments,
        team,
        ("/usr/bin/test", "!", "-e", f"/proc/{os.getpid()}/cmdline"),
        environment=environment,
    )
    result = {
        "allowed_reads": all(code == 0 for code in allowed_codes),
        "denied_reads": all(code != 0 for code in denied_codes),
        "cross_lane_write_denied": cross_lane_write == 0,
        "network_denied": network == 0,
        "host_process_hidden": host_process == 0,
        "host_skill_roots_denied": all(code != 0 for code in host_skill_codes),
        "own_lane_write_allowed": own_lane_write_allowed,
        "peer_private_runtime_read_denied": peer_private_read != 0,
        "peer_private_runtime_write_denied": peer_private_write == 0,
        "private_model_auth_denied": private_auth_code != 0,
        "skill_catalog_empty": True,
    }
    if not all(result.values()):
        raise ResearchRuntimeError("research clean-room profile failed its adversarial probes")
    _reset_private_model_session_state(private_paths)
    _reset_private_model_session_state(peer_private_paths)
    return result


def _team_kit_sha256(root: Path) -> str:
    entries: list[dict[str, object]] = []
    kit = root / isolation_v4.TEAM_KIT_ROOT
    for relative in sorted(isolation_v4._TEAM_KIT_FILES):
        payload = _stable_bytes(kit / relative)
        entries.append(
            {
                "path": relative,
                "size": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    return hashlib.sha256(_canonical(entries)).hexdigest()


def _receipt_relative(team_id: str, source_bundle_sha256: str) -> str:
    TOP40_V4_LAYOUT.require_team(team_id)
    if _SHA256.fullmatch(source_bundle_sha256) is None:
        raise ResearchRuntimeError("source bundle identity is not a SHA-256")
    return f"{isolation_v4.RESEARCH_SESSION_ROOT}/{team_id}/{source_bundle_sha256}.json"


def _launch_relative(team_id: str, phase: str) -> str:
    TOP40_V4_LAYOUT.require_team(team_id)
    if _PHASE.fullmatch(phase) is None:
        raise ResearchRuntimeError("unknown research phase")
    return f"{isolation_v4.RESEARCH_SESSION_ROOT}/launches/{team_id}/{phase}.json"


def _write_immutable(
    path: Path,
    payload: bytes,
    *,
    conflict_error: type[ResearchRuntimeError] = ResearchRuntimeError,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
    except FileExistsError:
        if _stable_bytes(path) != payload:
            raise conflict_error("immutable research receipt already differs")
        return
    with os.fdopen(descriptor, "wb") as handle:
        if handle.write(payload) != len(payload):
            raise ResearchRuntimeError("short research receipt write")
        handle.flush()
        os.fsync(handle.fileno())
    directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def _launch_authority_payload(root: Path, team_id: str, phase: str) -> bytes:
    command_authority = _model_command_authority(root, team_id, phase)
    launch = {
        **command_authority,
        "launcher_version": LAUNCHER_VERSION,
        "model_runtime_sha256": model_runtime_sha256(root, team_id),
        "phase": phase,
        "profile_sha256": profile_sha256(root, team_id),
        "schema_version": LAUNCH_SCHEMA_VERSION,
        "status": "authorized",
        "team_id": team_id,
        "team_kit_sha256": _team_kit_sha256(root),
        "tournament": TOP40_V4_LAYOUT.name,
    }
    return json.dumps(
        launch, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("ascii") + b"\n"


def _record_launch_authority(root: Path, team_id: str, phase: str) -> Mapping[str, str]:
    payload = _launch_authority_payload(root, team_id, phase)
    relative = _launch_relative(team_id, phase)
    _write_immutable(root / relative, payload)
    return {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}


def validate_launch_authority_payload(
    root: str | Path,
    team_id: str,
    phase: str,
    payload: bytes,
) -> Mapping[str, str]:
    """Validate one already-stable launch capture against the exact canonical authority."""

    root_path = Path(root).resolve()
    relative = _launch_relative(team_id, phase)
    if payload != _launch_authority_payload(root_path, team_id, phase):
        raise ResearchRuntimeError("research launch authority differs")
    return {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}


def validate_launch_authority(root: str | Path, team_id: str, phase: str) -> Mapping[str, str]:
    root_path = Path(root).resolve()
    relative = _launch_relative(team_id, phase)
    return validate_launch_authority_payload(
        root_path,
        team_id,
        phase,
        _stable_bytes(root_path / relative),
    )


def record_candidate_receipts(
    root: str | Path,
    team_id: str,
    phase: str,
    candidate_ids: Sequence[str],
    *,
    probes: Mapping[str, object],
) -> tuple[Mapping[str, str], ...]:
    """Bind a completed offline session to every exact candidate it produced."""

    if _PHASE.fullmatch(phase) is None:
        raise ResearchRuntimeError("unknown research phase")
    if not candidate_ids or len(set(candidate_ids)) != len(candidate_ids):
        raise ResearchRuntimeError("candidate receipt set must be nonempty and unique")
    if not probes or not all(value is True for value in probes.values()):
        raise ResearchRuntimeError("research receipts require passed isolation probes")
    root_path = Path(root).resolve()
    binary = _codex_binary()
    command_authority = _model_command_authority(root_path, team_id, phase)
    launch_authority = validate_launch_authority(root_path, team_id, phase)
    recorded: list[Mapping[str, str]] = []
    for candidate_id in candidate_ids:
        if re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", candidate_id) is None:
            raise ResearchRuntimeError("candidate id is invalid")
        entrypoint = f"{TOP40_V4_LAYOUT.team_root(team_id)}/candidates/{candidate_id}/strategy.py"
        capture = runner_v4.capture_source_bundle(root_path, team_id, entrypoint)
        isolation_v4.validate_captured_candidate(
            team_id=team_id,
            candidate_id=candidate_id,
            candidate_root=capture.candidate_root,
            files=capture.files,
        )
        receipt = {
            **command_authority,
            "candidate_root": capture.candidate_root,
            "codex_version": _codex_version(binary),
            "disabled_capabilities": list(_DISABLED_FEATURES),
            "launcher_version": LAUNCHER_VERSION,
            "launch_authority_sha256": launch_authority["sha256"],
            "model_runtime_sha256": model_runtime_sha256(root_path, team_id),
            "phase": phase,
            "profile_sha256": profile_sha256(root_path, team_id),
            "probes": dict(probes),
            "recorded_at_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "schema_version": RECEIPT_SCHEMA_VERSION,
            "source_bundle_sha256": capture.sha256,
            "status": "passed",
            "team_id": team_id,
            "team_kit_sha256": _team_kit_sha256(root_path),
            "tournament": TOP40_V4_LAYOUT.name,
        }
        payload = json.dumps(
            receipt, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True
        ).encode("ascii") + b"\n"
        relative = _receipt_relative(team_id, capture.sha256)
        if os.path.lexists(root_path / relative):
            existing = validate_candidate_receipt(
                root_path,
                team_id,
                candidate_id,
                capture.sha256,
                expected_phase=phase,
            )
            recorded.append(existing)
            continue
        _write_immutable(
            root_path / relative,
            payload,
            conflict_error=CandidateReceiptRejectedError,
        )
        recorded.append(
            {
                "path": relative,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "source_bundle_sha256": capture.sha256,
            }
        )
    return tuple(recorded)


def validate_candidate_receipt(
    root: str | Path,
    team_id: str,
    candidate_id: str,
    source_bundle_sha256: str,
    *,
    expected_phase: str | None = None,
) -> Mapping[str, str]:
    """Verify the organizer-only session receipt bound to one captured candidate."""

    if not TOP40_V4_LAYOUT.name.endswith("-r2"):
        return {}
    root_path = Path(root).resolve()
    relative = _receipt_relative(team_id, source_bundle_sha256)
    payload = _stable_bytes(root_path / relative, require_private=True)

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise CandidateReceiptRejectedError(
                    f"research session receipt contains duplicate key {key}"
                )
            value[key] = item
        return value

    def reject_nonfinite(value: str) -> None:
        raise CandidateReceiptRejectedError(
            f"research session receipt contains nonfinite value {value}"
        )

    try:
        receipt = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=unique,
            parse_constant=reject_nonfinite,
        )
    except CandidateReceiptRejectedError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise CandidateReceiptRejectedError(
            "research session receipt is invalid JSON"
        ) from exc
    if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT_KEYS:
        raise CandidateReceiptRejectedError("research session receipt schema differs")
    probes = receipt.get("probes")
    receipt_phase = str(receipt.get("phase"))
    if _PHASE.fullmatch(receipt_phase) is None:
        raise CandidateReceiptRejectedError(
            "research session receipt phase is invalid"
        )
    if expected_phase is not None and receipt_phase != expected_phase:
        raise CandidateReceiptRejectedError(
            "research session receipt belongs to another phase"
        )
    command_authority = _model_command_authority(root_path, team_id, receipt_phase)
    launch_authority = validate_launch_authority(
        root_path, team_id, receipt_phase
    )
    expected = {
        **command_authority,
        "candidate_root": f"{TOP40_V4_LAYOUT.team_root(team_id)}/candidates/{candidate_id}",
        "disabled_capabilities": list(_DISABLED_FEATURES),
        "launcher_version": LAUNCHER_VERSION,
        "launch_authority_sha256": launch_authority["sha256"],
        "model_runtime_sha256": model_runtime_sha256(root_path, team_id),
        "profile_sha256": profile_sha256(root_path, team_id),
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "source_bundle_sha256": source_bundle_sha256,
        "status": "passed",
        "team_id": team_id,
        "team_kit_sha256": _team_kit_sha256(root_path),
        "tournament": TOP40_V4_LAYOUT.name,
    }
    for key, value in expected.items():
        if receipt.get(key) != value:
            raise CandidateReceiptRejectedError(
                f"research session receipt differs in {key}"
            )
    if (
        receipt.get("codex_version") != _codex_version(_codex_binary())
        or not isinstance(receipt.get("recorded_at_utc"), str)
        or _UTC.fullmatch(str(receipt["recorded_at_utc"])) is None
    ):
        raise CandidateReceiptRejectedError(
            "research session runtime authority differs"
        )
    if not isinstance(probes, Mapping) or set(probes) != _PROBE_KEYS or not all(
        value is True for value in probes.values()
    ):
        raise CandidateReceiptRejectedError(
            "research session receipt probes did not pass"
        )
    canonical = json.dumps(
        receipt,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ).encode("ascii") + b"\n"
    if payload != canonical:
        raise CandidateReceiptRejectedError(
            "research session receipt bytes are not canonical"
        )
    return {
        "path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source_bundle_sha256": source_bundle_sha256,
    }


def _source_review_relative(team_id: str, source_bundle_sha256: str) -> str:
    TOP40_V4_LAYOUT.require_team(team_id)
    if _SHA256.fullmatch(source_bundle_sha256) is None:
        raise ResearchRuntimeError("source review identity is not a SHA-256")
    return (
        f"{isolation_v4.RESEARCH_SESSION_ROOT}/source-reviews/{team_id}/"
        f"{source_bundle_sha256}.json"
    )


def _attribute_root_name(node: ast.Attribute) -> str | None:
    value: ast.expr = node
    while isinstance(value, ast.Attribute):
        value = value.value
    return value.id if isinstance(value, ast.Name) else None


def _static_source_findings(
    files: Sequence[source_archive_v4.SourceFile],
) -> tuple[list[str], list[str]]:
    findings: list[str] = []
    executable = sorted(item.path for item in files if Path(item.path).suffix.lower() == ".py")
    local_modules = {Path(path).stem for path in executable}
    python_bytes = sum(item.size for item in files if Path(item.path).suffix.lower() == ".py")
    aggregate_string_units = 0
    aggregate_numeric_literals = 0
    aggregate_literal_nodes = 0
    aggregate_ast_nodes = 0
    target_methods = 0
    if executable != ["strategy.py"] or python_bytes > 131_072:
        findings.append("candidate: executable source must be exactly strategy.py")
    for item in files:
        if Path(item.path).suffix.lower() != ".py":
            continue
        try:
            source = item.content.decode("utf-8")
            tree = ast.parse(source, filename=item.path)
        except (UnicodeDecodeError, SyntaxError) as exc:
            findings.append(f"{item.path}: source is not valid UTF-8 Python ({type(exc).__name__})")
            continue
        if _DATE_LITERAL.search(source):
            findings.append(f"{item.path}: explicit calendar-date literal")
        if _ENCODED_LITERAL.search(source):
            findings.append(f"{item.path}: long encoded-looking literal")
        nodes = list(ast.walk(tree))
        all_target_methods = [
            node
            for node in nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "target_weights"
        ]
        direct_target_pairs = [
            (owner, method)
            for owner in tree.body
            if isinstance(owner, ast.ClassDef)
            for method in owner.body
            if isinstance(method, ast.FunctionDef) and method.name == "target_weights"
        ]
        direct_target_methods = [method for _owner, method in direct_target_pairs]
        direct_target_ids = {id(node) for node in direct_target_methods}
        target_methods += len(direct_target_methods)
        if len(all_target_methods) != len(direct_target_methods):
            findings.append(
                f"{item.path}: target_weights must be a direct module-level class method"
            )
        if direct_target_pairs:
            if len(direct_target_pairs) != 1:
                findings.append(f"{item.path}: executable strategy class is not unique")
            else:
                owner, _target = direct_target_pairs[0]
                if owner.bases or owner.keywords or owner.decorator_list:
                    findings.append(
                        f"{item.path}: strategy class inheritance/decorators are forbidden"
                    )
                allowed_class_nodes = {
                    id(_target),
                    *[
                        id(statement)
                        for statement in owner.body
                        if isinstance(statement, ast.Pass)
                        or (
                            isinstance(statement, ast.Expr)
                            and isinstance(statement.value, ast.Constant)
                            and isinstance(statement.value.value, str)
                        )
                    ],
                }
                if any(id(statement) not in allowed_class_nodes for statement in owner.body):
                    findings.append(
                        f"{item.path}: strategy class may contain only target_weights"
                    )
                builds = [
                    statement
                    for statement in tree.body
                    if isinstance(statement, ast.FunctionDef)
                    and statement.name == "build_strategy"
                ]
                if len(builds) != 1:
                    findings.append(f"{item.path}: one direct build_strategy function is required")
                else:
                    build = builds[0]
                    build_body = [
                        statement
                        for statement in build.body
                        if not (
                            isinstance(statement, ast.Expr)
                            and isinstance(statement.value, ast.Constant)
                            and isinstance(statement.value.value, str)
                        )
                    ]
                    valid_return = (
                        len(build_body) == 1
                        and isinstance(build_body[0], ast.Return)
                        and isinstance(build_body[0].value, ast.Call)
                        and isinstance(build_body[0].value.func, ast.Name)
                        and build_body[0].value.func.id == owner.name
                        and not build_body[0].value.args
                        and not build_body[0].value.keywords
                    )
                    if (
                        build.decorator_list
                        or build.args.posonlyargs
                        or build.args.args
                        or build.args.kwonlyargs
                        or build.args.vararg is not None
                        or build.args.kwarg is not None
                        or not valid_return
                    ):
                        findings.append(
                            f"{item.path}: build_strategy must only construct the strategy class"
                        )
            class_ids = {id(owner) for owner, _method in direct_target_pairs}
            if any(
                isinstance(statement, ast.ClassDef) and id(statement) not in class_ids
                for statement in tree.body
            ):
                findings.append(f"{item.path}: extra candidate classes are forbidden")
        elif any(isinstance(statement, ast.ClassDef) for statement in tree.body):
            findings.append(f"{item.path}: helper-module candidate classes are forbidden")
        owner_ids = {id(owner) for owner, _method in direct_target_pairs}
        build_ids = {
            id(statement)
            for statement in tree.body
            if isinstance(statement, ast.FunctionDef) and statement.name == "build_strategy"
        }
        for statement in tree.body:
            allowed = (
                isinstance(statement, (ast.Import, ast.ImportFrom, ast.Assign, ast.AnnAssign))
                or id(statement) in owner_ids
                or id(statement) in build_ids
                or (
                    isinstance(statement, ast.Expr)
                    and isinstance(statement.value, ast.Constant)
                    and isinstance(statement.value.value, str)
                )
            )
            if not allowed:
                findings.append(
                    f"{item.path}: top-level executable control flow/side effects are forbidden"
                )
        for statement in tree.body:
            if not isinstance(statement, (ast.Assign, ast.AnnAssign)):
                continue
            value = statement.value
            if value is None:
                continue
            if isinstance(value, ast.Constant):
                continue
            if (
                isinstance(value, ast.UnaryOp)
                and isinstance(value.op, (ast.UAdd, ast.USub))
                and isinstance(value.operand, ast.Constant)
                and isinstance(value.operand.value, (int, float))
            ):
                continue
            findings.append(f"{item.path}: module executable state construction is forbidden")
        aggregate_ast_nodes += len(nodes)
        if len(nodes) > 2_000:
            findings.append(f"{item.path}: excessive executable AST surface")
        docstrings = {
            id(owner.body[0].value)
            for owner in nodes
            if isinstance(owner, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
            and owner.body
            and isinstance(owner.body[0], ast.Expr)
            and isinstance(owner.body[0].value, ast.Constant)
            and isinstance(owner.body[0].value.value, str)
        }
        literal_bindings = {
            target.id
            for assignment in nodes
            if isinstance(assignment, (ast.Assign, ast.AnnAssign))
            for target in (
                assignment.targets
                if isinstance(assignment, ast.Assign)
                else [assignment.target]
            )
            if isinstance(target, ast.Name)
            and (
                (
                    isinstance(assignment.value, ast.Constant)
                    and isinstance(assignment.value.value, (str, bytes))
                )
                or (
                    isinstance(assignment.value, (ast.List, ast.Tuple, ast.Set))
                    and bool(assignment.value.elts)
                )
                or (isinstance(assignment.value, ast.Dict) and bool(assignment.value.keys))
            )
        }
        while True:
            aliases = {
                target.id
                for assignment in nodes
                if isinstance(assignment, (ast.Assign, ast.AnnAssign))
                and isinstance(assignment.value, ast.Name)
                and assignment.value.id in literal_bindings
                for target in (
                    assignment.targets
                    if isinstance(assignment, ast.Assign)
                    else [assignment.target]
                )
                if isinstance(target, ast.Name)
            }
            if aliases.issubset(literal_bindings):
                break
            literal_bindings.update(aliases)
        module_bindings = {
            target.id
            for statement in tree.body
            if isinstance(statement, (ast.Assign, ast.AnnAssign))
            for target in (
                statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            )
            if isinstance(target, ast.Name)
        }
        candidate_functions = {
            node.name
            for node in nodes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name not in {"build_strategy", "target_weights"}
        }
        candidate_classes = {node.name for node in nodes if isinstance(node, ast.ClassDef)}
        if candidate_functions:
            findings.append(f"{item.path}: candidate-defined helper functions are forbidden")
        local_module_aliases: set[str] = set()
        local_imported_names: set[str] = set()
        for node in nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in local_modules:
                        local_module_aliases.add(alias.asname or alias.name.split(".", 1)[0])
            elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".", 1)[
                0
            ] in local_modules:
                local_imported_names.update(alias.asname or alias.name for alias in node.names)
        literal_units = 0
        for node in nodes:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                for module in modules:
                    root = module.split(".", 1)[0]
                    if root not in _ALLOWED_IMPORT_ROOTS and root not in local_modules:
                        findings.append(
                            f"{item.path}: import is outside causal allowlist: {module}"
                        )
                    if ".random" in module or module.endswith("random"):
                        findings.append(f"{item.path}: stateful randomness import is forbidden")
                if any(alias.name == "random" for alias in node.names):
                    findings.append(f"{item.path}: stateful randomness import is forbidden")
                if isinstance(node, ast.ImportFrom) and any(
                    alias.name == "*" for alias in node.names
                ):
                    findings.append(f"{item.path}: wildcard import")
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in _FORBIDDEN_CALLS:
                    findings.append(f"{item.path}: forbidden call {node.func.id}")
                if isinstance(node.func, ast.Name) and node.func.id in module_bindings:
                    findings.append(f"{item.path}: module-bound stateful call is forbidden")
                if (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr in _FORBIDDEN_ATTRIBUTE_CALLS
                ):
                    findings.append(f"{item.path}: forbidden state/data call {node.func.attr}")
                if (
                    isinstance(node.func, ast.Attribute)
                    and _attribute_root_name(node.func) in module_bindings
                ):
                    findings.append(f"{item.path}: module-bound stateful call is forbidden")
            elif isinstance(node, ast.FunctionDef) and id(node) in direct_target_ids:
                method_nodes = list(ast.walk(node))
                arguments = node.args
                if (
                    [argument.arg for argument in arguments.posonlyargs] != []
                    or [argument.arg for argument in arguments.args] != ["self", "context"]
                    or [argument.arg for argument in arguments.kwonlyargs] != ["seed"]
                    or arguments.vararg is not None
                    or arguments.kwarg is not None
                    or arguments.defaults
                    or arguments.kw_defaults != [None]
                    or node.decorator_list
                ):
                    findings.append(
                        f"{item.path}: target_weights signature/defaults/decorators differ"
                    )
                if sum(isinstance(child, ast.stmt) for child in method_nodes) > 160:
                    findings.append(f"{item.path}: target_weights is excessively complex")
                if any(
                    isinstance(child, ast.Attribute)
                    and _attribute_root_name(child) == "self"
                    for child in method_nodes
                ):
                    findings.append(
                        f"{item.path}: target_weights must be stateless and cannot access "
                        "self state"
                    )
                if any(
                    isinstance(child, ast.Name)
                    and child.id == "self"
                    and isinstance(child.ctx, ast.Load)
                    for child in method_nodes
                ):
                    findings.append(
                        f"{item.path}: target_weights cannot pass or expose self state"
                    )
                if any(
                    isinstance(child, ast.Attribute) and child.attr == "decision_time"
                    for child in method_nodes
                ):
                    findings.append(
                        f"{item.path}: target_weights cannot branch on decision-time ordinals"
                    )
                if any(
                    isinstance(child, ast.Call)
                    and (
                        (
                            isinstance(child.func, ast.Name)
                            and child.func.id
                            in candidate_functions.union(local_imported_names)
                        )
                        or (
                            isinstance(child.func, ast.Attribute)
                            and _attribute_root_name(child.func)
                            in candidate_classes.union(local_module_aliases)
                        )
                    )
                    for child in method_nodes
                ):
                    findings.append(
                        f"{item.path}: target_weights cannot delegate to candidate helper code"
                    )
                if any(
                    isinstance(child, ast.Call)
                    and any(
                        isinstance(argument, ast.Name) and argument.id in module_bindings
                        for argument in [
                            *child.args,
                            *[keyword.value for keyword in child.keywords],
                        ]
                    )
                    for child in method_nodes
                ):
                    findings.append(
                        f"{item.path}: target_weights cannot pass module-bound state to calls"
                    )
                if any(
                    isinstance(child, ast.Name)
                    and isinstance(child.ctx, ast.Load)
                    and child.id in module_bindings
                    for child in method_nodes
                ):
                    findings.append(
                        f"{item.path}: target_weights cannot read module-bound state"
                    )
                if any(
                    isinstance(child, ast.Attribute)
                    and _attribute_root_name(child) in candidate_classes
                    for child in method_nodes
                ):
                    findings.append(
                        f"{item.path}: target_weights cannot read candidate class state"
                    )
                for child in method_nodes:
                    if not isinstance(child, ast.Call):
                        continue
                    if isinstance(child.func, ast.Name):
                        if child.func.id not in _TARGET_ALLOWED_NAME_CALLS:
                            findings.append(
                                f"{item.path}: target_weights call is outside pure allowlist: "
                                f"{child.func.id}"
                            )
                    elif isinstance(child.func, ast.Attribute):
                        if child.func.attr not in _TARGET_ALLOWED_ATTRIBUTE_CALLS:
                            findings.append(
                                f"{item.path}: target_weights method call is outside pure "
                                f"allowlist: {child.func.attr}"
                            )
                    else:
                        findings.append(
                            f"{item.path}: target_weights dynamic call target is forbidden"
                        )
            elif isinstance(node, ast.Constant):
                if isinstance(node.value, str) and id(node) in docstrings:
                    if len(node.value) > 4096:
                        findings.append(f"{item.path}: oversized inaccessible docstring")
                    continue
                aggregate_literal_nodes += 1
                if isinstance(node.value, bytes):
                    findings.append(f"{item.path}: bytes literal")
                elif isinstance(node.value, str):
                    literal_units += len(node.value)
                    aggregate_string_units += len(node.value)
                    if len(node.value) > 64:
                        findings.append(f"{item.path}: oversized operational string literal")
                    if not node.value.isascii() or not node.value.isprintable():
                        findings.append(f"{item.path}: opaque non-ASCII/control string literal")
                    if node.value not in _OPERATIONAL_STRINGS:
                        findings.append(
                            f"{item.path}: operational string is outside the frozen allowlist"
                        )
                elif isinstance(node.value, (int, float, complex)) and not isinstance(
                    node.value, bool
                ):
                    literal_units += 1
                    aggregate_numeric_literals += 1
                    numeric_text = repr(node.value)
                    significant_digits = len(
                        numeric_text.lower()
                        .split("e", 1)[0]
                        .replace("-", "")
                        .replace(".", "")
                        .lstrip("0")
                    )
                    if (
                        isinstance(node.value, complex)
                        or not math.isfinite(float(node.value))
                        or abs(node.value) > 10_000
                        or "e" in numeric_text.lower()
                        or significant_digits > 6
                    ):
                        findings.append(f"{item.path}: opaque or oversized numeric literal")
                    if isinstance(node.value, int) and node.value.bit_length() > 14:
                        findings.append(f"{item.path}: oversized integer literal")
            elif isinstance(node, (ast.List, ast.Tuple, ast.Set)) and node.elts:
                findings.append(f"{item.path}: nonempty literal sequence is forbidden")
            elif isinstance(node, ast.Dict) and node.keys:
                findings.append(f"{item.path}: nonempty literal mapping is forbidden")
            elif isinstance(node, ast.BinOp) and isinstance(
                node.op,
                (
                    ast.BitAnd,
                    ast.BitOr,
                    ast.BitXor,
                    ast.FloorDiv,
                    ast.LShift,
                    ast.MatMult,
                    ast.Mod,
                    ast.Pow,
                    ast.RShift,
                ),
            ):
                findings.append(f"{item.path}: ordinal/packing arithmetic is forbidden")
            elif (
                isinstance(node, ast.BinOp)
                and isinstance(node.op, (ast.Add, ast.Mult))
                and isinstance(
                    node.left,
                    (ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict),
                )
            ):
                findings.append(f"{item.path}: packed literal construction is forbidden")
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
                findings.append(f"{item.path}: bitwise inversion is forbidden")
            elif isinstance(node, ast.Subscript) and isinstance(
                node.value, (ast.Constant, ast.List, ast.Tuple, ast.Set, ast.Dict)
            ):
                findings.append(f"{item.path}: literal lookup/indexing is forbidden")
            elif (
                isinstance(node, ast.Subscript)
                and isinstance(node.value, ast.Name)
                and node.value.id in literal_bindings
            ):
                findings.append(f"{item.path}: bound literal lookup/indexing is forbidden")
            elif isinstance(node, (ast.While, ast.NamedExpr)):
                findings.append(f"{item.path}: ordinal state/control flow is forbidden")
            elif isinstance(node, (ast.Global, ast.Nonlocal, ast.AugAssign)):
                findings.append(f"{item.path}: persistent/ordinal mutation is forbidden")
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                if any(isinstance(target, ast.Attribute) for target in targets):
                    findings.append(f"{item.path}: object/class state mutation is forbidden")
                if any(
                    isinstance(target, ast.Subscript)
                    and isinstance(target.value, ast.Name)
                    and target.value.id in module_bindings
                    for target in targets
                ):
                    findings.append(f"{item.path}: module state mutation is forbidden")
            elif isinstance(node, ast.Attribute) and node.attr == "decision_time":
                findings.append(f"{item.path}: decision-time ordinal access is forbidden")
            elif (
                isinstance(node, ast.Attribute)
                and node.attr
                in {
                    "default_rng",
                    "permutation",
                    "rand",
                    "randint",
                    "randn",
                    "random",
                    "random_sample",
                    "shuffle",
                }
            ):
                findings.append(f"{item.path}: stateful randomness access is forbidden")
            elif isinstance(node, ast.Attribute) and node.attr == "__doc__":
                findings.append(f"{item.path}: executable docstring access is forbidden")
            elif (
                isinstance(node, ast.Name)
                and node.id == "__doc__"
                and isinstance(node.ctx, ast.Load)
            ):
                findings.append(f"{item.path}: executable docstring access is forbidden")
            elif (
                isinstance(node, ast.Name)
                and isinstance(node.ctx, ast.Load)
                and (node.id in _FORBIDDEN_CALLS or node.id.startswith("__"))
            ):
                findings.append(f"{item.path}: forbidden executable name access {node.id}")
            elif isinstance(node, ast.Attribute) and (
                node.attr in _FORBIDDEN_ATTRIBUTE_CALLS or node.attr.startswith("__")
            ):
                findings.append(f"{item.path}: forbidden executable attribute {node.attr}")
        if literal_units > 512:
            findings.append(f"{item.path}: excessive embedded literal payload")
    if aggregate_string_units > 256:
        findings.append("candidate: excessive aggregate string payload")
    if aggregate_numeric_literals > 24 or aggregate_literal_nodes > 64:
        findings.append("candidate: excessive aggregate literal table")
    if aggregate_ast_nodes > 5_000:
        findings.append("candidate: excessive aggregate executable AST surface")
    if target_methods != 1:
        findings.append("candidate: exactly one explicit target_weights method is required")
    return executable, sorted(set(findings))


def _target_frame_sha256(frame: pd.DataFrame) -> str:
    normalized = frame.copy()
    normalized.index = pd.to_datetime(normalized.index, utc=True)
    payload = normalized.to_json(
        orient="split",
        date_format="iso",
        date_unit="ns",
        double_precision=15,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _future_invariance_evidence(
    root: Path,
    team_id: str,
    entrypoint: str,
    capture: runner_v4.SourceBundleCapture,
) -> Mapping[str, object]:
    """Run the exact archive with past-only, appended-future, and corrupt-future inputs."""

    symbols = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT")
    open_times = pd.date_range("2020-02-03", periods=678, freq="8h", tz="UTC")
    bar_rows: list[dict[str, object]] = []
    funding_rows: list[dict[str, object]] = []
    for symbol_number, symbol in enumerate(symbols, start=1):
        for number, open_time in enumerate(open_times):
            price = 20.0 * symbol_number + 0.01 * number + 0.2 * ((number % 9) - 4)
            volume = 1_000.0 + 10.0 * symbol_number + float(number % 17)
            bar_rows.append(
                {
                    "open_time": open_time,
                    "symbol": symbol,
                    "open": price,
                    "high": price * 1.01,
                    "low": price * 0.99,
                    "close": price * (1.0 + 0.001 * ((number % 5) - 2)),
                    "volume": volume,
                    "close_time": open_time + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1),
                    "quote_volume": volume * price,
                    "trade_count": 100 + number % 31,
                    "taker_buy_volume": volume * 0.48,
                    "taker_buy_quote_volume": volume * price * 0.48,
                }
            )
            funding_rows.append(
                {
                    "funding_time": open_time,
                    "symbol": symbol,
                    "funding_rate": 0.00001 * ((number % 7) - 3),
                    "mark_price": price,
                }
            )
    bars = pd.DataFrame(bar_rows)
    funding = pd.DataFrame(funding_rows)
    membership = pd.DataFrame(
        [
            {
                "reconstitution_time": open_times[0],
                "symbol": symbol,
                "liquidity_rank": rank,
                "trailing_quote_volume": float(1_000_000 - rank),
            }
            for rank, symbol in enumerate(symbols, start=1)
        ]
    )
    decision_times = open_times[600:606]
    cutoff = decision_times[-1]
    past_bars = bars.loc[bars["open_time"] <= cutoff].copy()
    past_funding = funding.loc[funding["funding_time"] < cutoff].copy()
    corrupt_bars = bars.copy()
    future_bars = corrupt_bars["open_time"] > cutoff
    corrupt_bars.loc[future_bars, ["open", "high", "low", "close"]] *= 1.7
    corrupt_bars.loc[
        future_bars,
        ["volume", "quote_volume", "taker_buy_volume", "taker_buy_quote_volume"],
    ] *= 4.0
    corrupt_funding = funding.copy()
    future_funding = corrupt_funding["funding_time"] >= cutoff
    corrupt_funding.loc[future_funding, "funding_rate"] *= -11.0
    corrupt_funding.loc[future_funding, "mark_price"] *= 1.7

    def generate(candidate_bars: pd.DataFrame, candidate_funding: pd.DataFrame) -> pd.DataFrame:
        try:
            return runner_v4._generate_targets_in_worker(
                root,
                team_id,
                entrypoint,
                candidate_bars,
                candidate_funding,
                membership,
                decision_times,
                seed=20260819,
                interval_hours=8,
                expected_source_bundle_sha256=capture.sha256,
                expected_source_entries=capture.manifest_entries,
                archived_files=capture.files,
            )
        except runner_v4.StrategyExecutionError as exc:
            raise CandidateSourceRejectedError(
                "candidate failed deterministic causal-review execution"
            ) from exc
        except runner_v4.StrategySandboxError as exc:
            # These responses are emitted only after the isolated candidate has produced an
            # invalid target payload. Launch, timeout, protocol, and storage failures remain
            # infrastructure errors and are deliberately not made terminal here.
            invalid_output = (
                "strategy worker returned an invalid weight response",
                "strategy worker returned an ineligible target symbol",
                "strategy worker returned a Boolean target weight",
                "strategy worker returned a non-numeric weight",
                "strategy worker returned a non-finite weight",
            )
            if str(exc).startswith(invalid_output):
                raise CandidateSourceRejectedError(
                    "candidate emitted invalid targets during deterministic causal review"
                ) from exc
            raise

    past = generate(past_bars, past_funding)
    appended = generate(bars, funding)
    corrupted = generate(corrupt_bars, corrupt_funding)
    try:
        pd.testing.assert_frame_equal(past, appended, check_exact=True)
        pd.testing.assert_frame_equal(past, corrupted, check_exact=True)
    except AssertionError as exc:
        raise CandidateSourceRejectedError(
            "candidate failed append/corrupt-future invariance"
        ) from exc
    digest = _target_frame_sha256(past)
    return {
        "decision_count": len(decision_times),
        "past_only_targets_sha256": digest,
        "appended_future_targets_sha256": _target_frame_sha256(appended),
        "corrupt_future_targets_sha256": _target_frame_sha256(corrupted),
        "status": "passed",
    }


def review_candidate_source(
    root: str | Path,
    team_id: str,
    candidate_id: str,
    source_bundle_sha256: str,
) -> Mapping[str, str]:
    """Run the organizer-side deterministic causal-source gate for one exact nominee."""

    root_path = Path(root).resolve()
    validate_candidate_receipt(
        root_path,
        team_id,
        candidate_id,
        source_bundle_sha256,
    )
    entrypoint = f"{TOP40_V4_LAYOUT.team_root(team_id)}/candidates/{candidate_id}/strategy.py"
    capture = runner_v4.capture_source_bundle(root_path, team_id, entrypoint)
    if capture.sha256 != source_bundle_sha256:
        raise CandidateSourceRejectedError(
            "source review candidate differs from accepted authority"
        )
    executable, findings = _static_source_findings(capture.files)
    if "strategy.py" not in executable or findings:
        detail = "; ".join(findings[:8]) or "strategy.py is not executable source"
        raise CandidateSourceRejectedError(f"candidate failed causal source review: {detail}")
    future_invariance = _future_invariance_evidence(
        root_path,
        team_id,
        entrypoint,
        capture,
    )
    review = {
        "candidate_id": candidate_id,
        "executable_paths": executable,
        "findings": [],
        "future_invariance": dict(future_invariance),
        "recorded_at_utc": dt.datetime.now(dt.UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schema_version": SOURCE_REVIEW_SCHEMA_VERSION,
        "source_bundle_sha256": source_bundle_sha256,
        "static_checks": list(_STATIC_CHECKS),
        "status": "passed",
        "team_id": team_id,
        "tournament": TOP40_V4_LAYOUT.name,
    }
    payload = json.dumps(
        review, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("ascii") + b"\n"
    relative = _source_review_relative(team_id, source_bundle_sha256)
    if not os.path.lexists(root_path / relative):
        _write_immutable(root_path / relative, payload)
    return validate_source_review(
        root_path,
        team_id,
        candidate_id,
        source_bundle_sha256,
    )


def validate_source_review(
    root: str | Path,
    team_id: str,
    candidate_id: str,
    source_bundle_sha256: str,
) -> Mapping[str, str]:
    """Validate the organizer-only static review bound to an accepted candidate."""

    root_path = Path(root).resolve()
    relative = _source_review_relative(team_id, source_bundle_sha256)
    payload = _stable_bytes(root_path / relative)
    try:
        review = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError("source review is invalid JSON") from exc
    if not isinstance(review, Mapping) or set(review) != _SOURCE_REVIEW_KEYS:
        raise ResearchRuntimeError("source review schema differs")
    expected = {
        "candidate_id": candidate_id,
        "findings": [],
        "schema_version": SOURCE_REVIEW_SCHEMA_VERSION,
        "source_bundle_sha256": source_bundle_sha256,
        "status": "passed",
        "team_id": team_id,
        "tournament": TOP40_V4_LAYOUT.name,
    }
    for key, value in expected.items():
        if review.get(key) != value:
            raise ResearchRuntimeError(f"source review differs in {key}")
    executable = review.get("executable_paths")
    checks = review.get("static_checks")
    invariance = review.get("future_invariance")
    if (
        not isinstance(executable, list)
        or "strategy.py" not in executable
        or any(not isinstance(path, str) or not path.endswith(".py") for path in executable)
        or checks != list(_STATIC_CHECKS)
        or not isinstance(invariance, Mapping)
        or set(invariance)
        != {
            "decision_count",
            "past_only_targets_sha256",
            "appended_future_targets_sha256",
            "corrupt_future_targets_sha256",
            "status",
        }
        or invariance.get("decision_count") != 6
        or invariance.get("status") != "passed"
        or _SHA256.fullmatch(str(invariance.get("past_only_targets_sha256"))) is None
        or invariance.get("appended_future_targets_sha256")
        != invariance.get("past_only_targets_sha256")
        or invariance.get("corrupt_future_targets_sha256")
        != invariance.get("past_only_targets_sha256")
    ):
        raise ResearchRuntimeError("source review checks are incomplete")
    return {
        "path": relative,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "source_bundle_sha256": source_bundle_sha256,
    }


def _validate_phase_request(request: object, phase: str) -> list[str]:
    if not isinstance(request, Mapping):
        raise ResearchRuntimeError("team outbox request must be a JSON object")
    if phase == "decision":
        operation = request.get("operation")
        expected_keys = (
            {"schema_version", "operation", "candidate_id", "certificate_path"}
            if operation == "nominate"
            else {"schema_version", "operation", "reason"}
        )
        if (
            request.get("schema_version") != 1
            or operation not in {"nominate", "retire"}
            or set(request) != expected_keys
        ):
            raise ResearchRuntimeError("team decision outbox schema differs")
        if operation == "nominate" and (
            not isinstance(request.get("candidate_id"), str)
            or re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,127}", request["candidate_id"])
            is None
            or request.get("certificate_path") != "work/research-certificate.json"
        ):
            raise ResearchRuntimeError("team nomination outbox values differ")
        if operation == "retire" and (
            not _is_bounded_single_line(request.get("reason"))
        ):
            raise ResearchRuntimeError("team retirement outbox values differ")
        return []
    rows = request.get("requests")
    expected_count = 8 if phase == "discovery" else 4
    if (
        set(request) != {"schema_version", "operation", "requests"}
        or request.get("schema_version") != 1
        or request.get("operation") != "is-batch"
        or not isinstance(rows, list)
        or len(rows) != expected_count
        or any(
            not isinstance(item, Mapping)
            or set(item) != {"candidate_id", "entrypoint", "purpose"}
            for item in rows
        )
    ):
        raise ResearchRuntimeError("team batch outbox schema or count differs")
    candidate_ids: list[str] = []
    seen: set[str] = set()
    for item in rows:
        candidate_id = item.get("candidate_id")
        purpose = item.get("purpose")
        if (
            not isinstance(candidate_id, str)
            or _SAFE_ID.fullmatch(candidate_id) is None
            or candidate_id in seen
            or item.get("entrypoint") != f"candidates/{candidate_id}/strategy.py"
            or not _is_bounded_single_line(purpose)
        ):
            raise ResearchRuntimeError("team batch outbox values differ")
        seen.add(candidate_id)
        candidate_ids.append(candidate_id)
    return candidate_ids


def _wraps_os_error(error: BaseException) -> bool:
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        if isinstance(current, OSError):
            return True
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return False


def _strict_team_request(payload: bytes, relative: str) -> Mapping[str, object]:
    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        value: dict[str, object] = {}
        for key, item in pairs:
            if key in value:
                raise ResearchRuntimeError(f"{relative} contains duplicate key {key}")
            value[key] = item
        return value

    def reject_nonfinite(value: str) -> None:
        raise ResearchRuntimeError(f"{relative} contains nonfinite value {value}")

    try:
        request = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=unique,
            parse_constant=reject_nonfinite,
        )
    except ResearchRuntimeError:
        raise
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError(f"{relative} is invalid JSON") from exc
    if not isinstance(request, Mapping):
        raise ResearchRuntimeError(f"{relative} must contain one JSON object")
    return request


def _score_blind_batch_inspection(
    root: Path,
    team_id: str,
    phase: str,
    outbox: Path,
) -> Mapping[str, object]:
    """Inspect every unaccepted candidate without issuing receipts or opening market data."""

    if phase not in {"discovery", "refinement"}:
        raise ResearchRuntimeError("only research batches can be admission-inspected")
    try:
        payload = _stable_bytes(outbox)
    except ResearchRuntimeError as exc:
        if _wraps_os_error(exc):
            raise
        return {
            "candidate_ids": [],
            "findings": [f"outbox: {' '.join(str(exc).split())[:2048]}"],
            "outbox_sha256": "0" * 64,
            "source_bundle_sha256s": [],
        }
    outbox_sha256 = hashlib.sha256(payload).hexdigest()
    findings: list[str] = []
    candidate_ids: list[str] = []
    source_bundle_sha256s: list[str] = []
    relative = outbox.relative_to(root).as_posix()
    try:
        request = _strict_team_request(payload, relative)
        candidate_ids = _validate_phase_request(request, phase)
    except ResearchRuntimeError as exc:
        if _wraps_os_error(exc):
            raise
        return {
            "candidate_ids": [],
            "findings": [f"outbox: {exc}"],
            "outbox_sha256": outbox_sha256,
            "source_bundle_sha256s": [],
        }

    # Imported lazily to preserve the orchestrator -> research-runtime dependency direction.
    from crypto_trade.tournament import orchestrator_v4, top40_v4

    loaded = top40_v4.load_config(root=root)
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    accepted = sorted(
        (
            request["payload"]
            for request in state.is_requests.values()
            if request["payload"]["team_id"] == team_id
        ),
        key=lambda request: request["trial_number"],
    )
    phase_start = 0 if phase == "discovery" else 8
    history: list[Mapping[str, object]] = [
        {**request["metadata"], "candidate_id": request["candidate_id"]}
        for request in accepted[:phase_start]
    ]
    prior_ids = {str(request["candidate_id"]) for request in accepted[:phase_start]}
    rows = request["requests"]
    assert isinstance(rows, list)
    for row in rows:
        assert isinstance(row, Mapping)
        candidate_id = str(row["candidate_id"])
        entrypoint = f"{TOP40_V4_LAYOUT.team_root(team_id)}/{row['entrypoint']}"
        metadata: Mapping[str, object] | None = None
        source_bundle_sha256 = ""
        try:
            capture = runner_v4.capture_source_bundle(root, team_id, entrypoint)
            source_bundle_sha256 = capture.sha256
            isolation_v4.validate_captured_candidate(
                team_id=team_id,
                candidate_id=candidate_id,
                candidate_root=capture.candidate_root,
                files=capture.files,
            )
            metadata, _metadata_path = orchestrator_v4._candidate_metadata(  # noqa: SLF001
                root,
                loaded.raw,
                team_id,
                entrypoint,
                capture=capture,
            )
            if metadata["candidate_id"] != candidate_id:
                raise ResearchRuntimeError(
                    "candidate identity differs from its ordered batch request"
                )
            if candidate_id in prior_ids:
                raise ResearchRuntimeError(
                    "batch candidate reuses a candidate from an earlier phase"
                )
            executable, static_findings = _static_source_findings(capture.files)
            if "strategy.py" not in executable:
                static_findings = [
                    *static_findings,
                    "candidate: strategy.py is not executable source",
                ]
            findings.extend(f"{candidate_id}: {finding}" for finding in static_findings)
        except (
            ResearchRuntimeError,
            orchestrator_v4.OrchestratorError,
            isolation_v4.IsolationError,
            runner_v4.StrategySandboxError,
            ValueError,
        ) as exc:
            if _wraps_os_error(exc):
                raise
            findings.append(f"{candidate_id}: {exc}")
        source_bundle_sha256s.append(source_bundle_sha256)
        if metadata is not None:
            try:
                orchestrator_v4._validate_open_lane_mechanism_history(  # noqa: SLF001
                    history, metadata
                )
            except (orchestrator_v4.OrchestratorError, ValueError) as exc:
                if _wraps_os_error(exc):
                    raise
                findings.append(f"{candidate_id}: {exc}")
            else:
                history.append(metadata)
    normalized_findings = sorted(
        {
            " ".join(str(finding).split())[:2048]
            or "deterministic admission failure"
            for finding in findings
        }
    )
    if len(normalized_findings) > 256:
        normalized_findings = [
            *normalized_findings[:255],
            "additional deterministic findings omitted; recheck the complete batch",
        ]
    return {
        "candidate_ids": candidate_ids,
        "findings": normalized_findings,
        "outbox_sha256": outbox_sha256,
        "source_bundle_sha256s": source_bundle_sha256s,
    }


def _admission_attempt_directory(root: Path, team_id: str) -> Path:
    TOP40_V4_LAYOUT.require_team(team_id)
    return root / isolation_v4.RESEARCH_SESSION_ROOT / "admission-attempts" / team_id


@contextlib.contextmanager
def _pinned_admission_directory(
    root: Path,
    team_id: str,
    category: str,
) -> Iterator[int]:
    """Pin one organizer-private authority directory through every path component."""

    TOP40_V4_LAYOUT.require_team(team_id)
    if category not in {"admission-attempts", "admission-sessions"}:
        raise ResearchRuntimeError("admission authority category is invalid")
    parts = (*Path(isolation_v4.RESEARCH_SESSION_ROOT).parts, category, team_id)
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_DIRECTORY", 0)
    )
    descriptors: list[int] = []
    identities: list[tuple[int, int]] = []
    names: list[str] = []
    try:
        descriptor = os.open(root, flags)
        descriptors.append(descriptor)
        root_details = os.fstat(descriptor)
        root_lexical = root.lstat()
        if (
            not stat.S_ISDIR(root_details.st_mode)
            or (root_details.st_dev, root_details.st_ino)
            != (root_lexical.st_dev, root_lexical.st_ino)
        ):
            raise ResearchRuntimeError("research root is not a pinned directory")
        identities.append((root_details.st_dev, root_details.st_ino))
        for index, part in enumerate(parts):
            parent = descriptors[-1]
            private = index >= len(parts) - 2
            try:
                os.mkdir(part, 0o700 if private else 0o755, dir_fd=parent)
            except FileExistsError:
                pass
            except OSError as exc:
                raise ResearchRuntimeError(
                    "cannot create private admission authority directory"
                ) from exc
            try:
                child = os.open(part, flags, dir_fd=parent)
                details = os.fstat(child)
                lexical = os.stat(part, dir_fd=parent, follow_symlinks=False)
            except OSError as exc:
                raise ResearchRuntimeError(
                    "cannot pin private admission authority directory"
                ) from exc
            if (
                not stat.S_ISDIR(details.st_mode)
                or details.st_uid != os.geteuid()
                or stat.S_IMODE(details.st_mode) & 0o022
                or (private and stat.S_IMODE(details.st_mode) & 0o077)
                or (details.st_dev, details.st_ino)
                != (lexical.st_dev, lexical.st_ino)
            ):
                os.close(child)
                raise ResearchRuntimeError(
                    "private admission authority directory is unsafe"
                )
            os.fsync(parent)
            descriptors.append(child)
            identities.append((details.st_dev, details.st_ino))
            names.append(part)
        yield descriptors[-1]
        for index in range(len(descriptors) - 1, 0, -1):
            details = os.fstat(descriptors[index])
            lexical = os.stat(
                names[index - 1],
                dir_fd=descriptors[index - 1],
                follow_symlinks=False,
            )
            if (
                (details.st_dev, details.st_ino) != identities[index]
                or (lexical.st_dev, lexical.st_ino) != identities[index]
                or not stat.S_ISDIR(lexical.st_mode)
            ):
                raise ResearchRuntimeError(
                    "private admission authority path changed while pinned"
                )
    finally:
        for descriptor in reversed(descriptors):
            with contextlib.suppress(OSError):
                os.close(descriptor)


def _pinned_admission_bytes(directory: int, name: str) -> bytes:
    if _ADMISSION_AUTHORITY_NAME.fullmatch(name) is None:
        raise ResearchRuntimeError("admission authority filename is invalid")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    try:
        descriptor = os.open(name, flags, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as handle:
            before = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_uid != os.geteuid()
                or before.st_nlink != 1
                or stat.S_IMODE(before.st_mode) != 0o600
                or before.st_size > 2 * 1024 * 1024
            ):
                raise ResearchRuntimeError("admission authority is not private and regular")
            payload = handle.read(2 * 1024 * 1024 + 1)
            after = os.fstat(handle.fileno())
        lexical = os.stat(name, dir_fd=directory, follow_symlinks=False)
    except ResearchRuntimeError:
        raise
    except OSError as exc:
        raise ResearchRuntimeError("cannot read pinned admission authority") from exc
    identity = lambda value: (  # noqa: E731
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_nlink,
        value.st_uid,
        value.st_mode,
    )
    if (
        len(payload) > 2 * 1024 * 1024
        or identity(before) != identity(after)
        or identity(after) != identity(lexical)
    ):
        raise ResearchRuntimeError("admission authority changed while being read")
    return payload


def _write_pinned_admission_authority(directory: int, name: str, payload: bytes) -> None:
    if _ADMISSION_AUTHORITY_NAME.fullmatch(name) is None:
        raise ResearchRuntimeError("admission authority filename is invalid")
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    try:
        descriptor = os.open(name, flags, 0o600, dir_fd=directory)
    except FileExistsError:
        if _pinned_admission_bytes(directory, name) != payload:
            raise ResearchRuntimeError("immutable admission authority already differs")
        return
    except OSError as exc:
        raise ResearchRuntimeError("cannot create pinned admission authority") from exc
    try:
        with os.fdopen(descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o600)
            if handle.write(payload) != len(payload):
                raise ResearchRuntimeError("short admission authority write")
            handle.flush()
            os.fsync(handle.fileno())
        os.fsync(directory)
        if _pinned_admission_bytes(directory, name) != payload:
            raise ResearchRuntimeError("new admission authority failed verification")
    except Exception:
        raise


def _canonical_admission_attempt(attempt: Mapping[str, object]) -> bytes:
    return json.dumps(
        attempt,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ).encode("ascii") + b"\n"


def _admission_attempts(
    root: Path, team_id: str, phase: str
) -> list[Mapping[str, object]]:
    prefix = f"{phase}-"
    attempts: list[Mapping[str, object]] = []
    with _pinned_admission_directory(
        root, team_id, "admission-attempts"
    ) as directory:
        names = sorted(os.listdir(directory))
        if any(_ADMISSION_AUTHORITY_NAME.fullmatch(name) is None for name in names):
            raise ResearchRuntimeError("admission-attempt directory has unexpected residue")
        for known_phase in ("discovery", "refinement"):
            phase_names = [name for name in names if name.startswith(f"{known_phase}-")]
            if phase_names != [
                f"{known_phase}-{number:02d}.json"
                for number in range(1, len(phase_names) + 1)
            ] or len(phase_names) > _MAX_SCORE_BLIND_REPAIR_SESSIONS + 1:
                raise ResearchRuntimeError("admission-attempt sequence is malformed")
        selected = [name for name in names if name.startswith(prefix)]
        for number, name in enumerate(selected, start=1):
            if name != f"{phase}-{number:02d}.json":
                raise ResearchRuntimeError("admission-attempt sequence is malformed")
            payload = _pinned_admission_bytes(directory, name)
            relative = (
                f"{isolation_v4.RESEARCH_SESSION_ROOT}/admission-attempts/"
                f"{team_id}/{name}"
            )
            attempt = _strict_team_request(payload, relative)
            if (
                set(attempt)
                != {
                    "attempt_number",
                    "candidate_ids",
                    "findings",
                    "outbox_sha256",
                    "phase",
                    "schema_version",
                    "score_data_opened",
                    "source_bundle_sha256s",
                    "team_id",
                    "tournament",
                }
                or attempt.get("schema_version") != 1
                or attempt.get("attempt_number") != number
                or attempt.get("team_id") != team_id
                or attempt.get("phase") != phase
                or attempt.get("tournament") != TOP40_V4_LAYOUT.name
                or attempt.get("score_data_opened") is not False
                or _SHA256.fullmatch(str(attempt.get("outbox_sha256"))) is None
                or not isinstance(attempt.get("candidate_ids"), list)
                or len(attempt["candidate_ids"]) > 8
                or any(
                    not isinstance(candidate_id, str)
                    or _SAFE_ID.fullmatch(candidate_id) is None
                    for candidate_id in attempt["candidate_ids"]
                )
                or not isinstance(attempt.get("source_bundle_sha256s"), list)
                or len(attempt["source_bundle_sha256s"])
                != len(attempt["candidate_ids"])
                or any(
                    not isinstance(source_sha256, str)
                    or (
                        source_sha256 != ""
                        and _SHA256.fullmatch(source_sha256) is None
                    )
                    for source_sha256 in attempt["source_bundle_sha256s"]
                )
                or not isinstance(attempt.get("findings"), list)
                or not 1 <= len(attempt["findings"]) <= 256
                or any(
                    not _is_bounded_single_line(finding, maximum=2048)
                    for finding in attempt["findings"]
                )
            ):
                raise ResearchRuntimeError("admission-attempt authority differs")
            if payload != _canonical_admission_attempt(attempt):
                raise ResearchRuntimeError("admission-attempt bytes are not canonical")
            attempts.append(attempt)
    return attempts


def _record_admission_attempt(
    root: Path,
    team_id: str,
    phase: str,
    inspection: Mapping[str, object],
    *,
    repeat: bool,
) -> tuple[Mapping[str, object], bool]:
    attempts = _admission_attempts(root, team_id, phase)
    if (
        attempts
        and not repeat
        and attempts[-1]["outbox_sha256"] == inspection["outbox_sha256"]
        and attempts[-1]["candidate_ids"] == list(inspection["candidate_ids"])
        and attempts[-1]["source_bundle_sha256s"]
        == list(inspection["source_bundle_sha256s"])
        and attempts[-1]["findings"] == list(inspection["findings"])
    ):
        attempt = attempts[-1]
        created = False
    else:
        number = len(attempts) + 1
        attempt = {
            "attempt_number": number,
            "candidate_ids": list(inspection["candidate_ids"]),
            "findings": list(inspection["findings"]),
            "outbox_sha256": inspection["outbox_sha256"],
            "phase": phase,
            "schema_version": 1,
            "score_data_opened": False,
            "source_bundle_sha256s": list(inspection["source_bundle_sha256s"]),
            "team_id": team_id,
            "tournament": TOP40_V4_LAYOUT.name,
        }
        payload = _canonical_admission_attempt(attempt)
        name = f"{phase}-{number:02d}.json"
        with _pinned_admission_directory(
            root, team_id, "admission-attempts"
        ) as directory:
            _write_pinned_admission_authority(directory, name, payload)
        created = True
    number = int(attempt["attempt_number"])
    feedback = {
        **attempt,
        "instruction": (
            "Repair every listed deterministic admission finding in place. No score, trial "
            "outcome, peer state, or holdout data was opened. Recheck the complete batch."
        ),
        "remaining_repair_sessions": max(
            0, _MAX_SCORE_BLIND_REPAIR_SESSIONS - number + 1
        ),
    }
    feedback_payload = json.dumps(
        feedback,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ).encode("ascii") + b"\n"
    feedback_path = (
        root
        / TOP40_V4_LAYOUT.team_root(team_id)
        / "feedback"
        / f"admission-{phase}-{number:02d}.json"
    )
    _write_immutable(feedback_path, feedback_payload)
    return attempt, created


def _canonical_admission_session(issue: Mapping[str, object]) -> bytes:
    return json.dumps(
        issue,
        allow_nan=False,
        ensure_ascii=True,
        indent=2,
        sort_keys=True,
    ).encode("ascii") + b"\n"


def _admission_session_issues(
    root: Path,
    team_id: str,
    phase: str,
    launch_authority_sha256: str,
) -> list[Mapping[str, object]]:
    attempts = _admission_attempts(root, team_id, phase)
    issues: list[Mapping[str, object]] = []
    prefix = f"{phase}-"
    with _pinned_admission_directory(
        root, team_id, "admission-sessions"
    ) as directory:
        names = sorted(os.listdir(directory))
        if any(_ADMISSION_AUTHORITY_NAME.fullmatch(name) is None for name in names):
            raise ResearchRuntimeError("admission-session directory has unexpected residue")
        for known_phase in ("discovery", "refinement"):
            phase_names = [name for name in names if name.startswith(f"{known_phase}-")]
            if phase_names != [
                f"{known_phase}-{number:02d}.json"
                for number in range(len(phase_names))
            ] or len(phase_names) > _MAX_SCORE_BLIND_REPAIR_SESSIONS + 1:
                raise ResearchRuntimeError("admission-session sequence is malformed")
        selected = [name for name in names if name.startswith(prefix)]
        for session_number, name in enumerate(selected):
            if (
                name != f"{phase}-{session_number:02d}.json"
                or session_number > _MAX_SCORE_BLIND_REPAIR_SESSIONS
                or session_number > len(attempts)
            ):
                raise ResearchRuntimeError("admission-session sequence is malformed")
            payload = _pinned_admission_bytes(directory, name)
            relative = (
                f"{isolation_v4.RESEARCH_SESSION_ROOT}/admission-sessions/"
                f"{team_id}/{name}"
            )
            issue = _strict_team_request(payload, relative)
            input_attempt = attempts[session_number - 1] if session_number else None
            input_path = (
                f"{isolation_v4.RESEARCH_SESSION_ROOT}/admission-attempts/{team_id}/"
                f"{phase}-{session_number:02d}.json"
                if input_attempt is not None
                else None
            )
            input_sha256 = (
                hashlib.sha256(_canonical_admission_attempt(input_attempt)).hexdigest()
                if input_attempt is not None
                else None
            )
            expected = {
                "input_attempt_path": input_path,
                "input_attempt_sha256": input_sha256,
                "launch_authority_sha256": launch_authority_sha256,
                "phase": phase,
                "schema_version": 1,
                "score_data_opened": False,
                "session_kind": (
                    "initial" if session_number == 0 else "score-blind-repair"
                ),
                "session_number": session_number,
                "team_id": team_id,
                "tournament": TOP40_V4_LAYOUT.name,
            }
            if issue != expected or payload != _canonical_admission_session(issue):
                raise ResearchRuntimeError("admission-session authority differs")
            issues.append(issue)
    if len(issues) not in {len(attempts), len(attempts) + 1}:
        raise ResearchRuntimeError("admission session/attempt sequence is contradictory")
    return issues


def _record_admission_session_issue(
    root: Path,
    team_id: str,
    phase: str,
    launch_authority_sha256: str,
    session_number: int,
) -> Mapping[str, object]:
    attempts = _admission_attempts(root, team_id, phase)
    if (
        not 0 <= session_number <= _MAX_SCORE_BLIND_REPAIR_SESSIONS
        or len(attempts) != session_number
    ):
        raise ResearchRuntimeError("admission session issuance is out of sequence")
    existing = _admission_session_issues(
        root, team_id, phase, launch_authority_sha256
    )
    input_attempt = attempts[-1] if attempts else None
    issue = {
        "input_attempt_path": (
            f"{isolation_v4.RESEARCH_SESSION_ROOT}/admission-attempts/{team_id}/"
            f"{phase}-{session_number:02d}.json"
            if input_attempt is not None
            else None
        ),
        "input_attempt_sha256": (
            hashlib.sha256(_canonical_admission_attempt(input_attempt)).hexdigest()
            if input_attempt is not None
            else None
        ),
        "launch_authority_sha256": launch_authority_sha256,
        "phase": phase,
        "schema_version": 1,
        "score_data_opened": False,
        "session_kind": "initial" if session_number == 0 else "score-blind-repair",
        "session_number": session_number,
        "team_id": team_id,
        "tournament": TOP40_V4_LAYOUT.name,
    }
    if len(existing) == session_number + 1:
        if existing[-1] != issue:
            raise ResearchRuntimeError("existing admission session issue differs")
        return existing[-1]
    if len(existing) != session_number:
        raise ResearchRuntimeError("admission session issuance would skip authority")
    name = f"{phase}-{session_number:02d}.json"
    payload = _canonical_admission_session(issue)
    with _pinned_admission_directory(
        root, team_id, "admission-sessions"
    ) as directory:
        _write_pinned_admission_authority(directory, name, payload)
    return issue


def validate_missing_batch_exhaustion(
    root: str | Path,
    team_id: str,
    phase: str,
) -> Mapping[str, str]:
    """Bind terminal missing-output evidence after all issued model sessions."""

    root_path = Path(root).resolve()
    launch = validate_launch_authority(root_path, team_id, phase)
    attempts = _admission_attempts(root_path, team_id, phase)
    issues = _admission_session_issues(root_path, team_id, phase, launch["sha256"])
    outbox_name = "batch-1.json" if phase == "discovery" else "batch-2.json"
    outbox = root_path / TOP40_V4_LAYOUT.team_root(team_id) / "outbox" / outbox_name
    expected_finding = f"outbox: required {outbox_name} was not published"
    if (
        os.path.lexists(outbox)
        or len(attempts) != _MAX_SCORE_BLIND_REPAIR_SESSIONS + 1
        or len(issues) != _MAX_SCORE_BLIND_REPAIR_SESSIONS + 1
        or attempts[-1]["attempt_number"] != 4
        or attempts[-1]["candidate_ids"] != []
        or attempts[-1]["source_bundle_sha256s"] != []
        or attempts[-1]["outbox_sha256"] != hashlib.sha256(b"").hexdigest()
        or attempts[-1]["findings"] != [expected_finding]
    ):
        raise ResearchRuntimeError("missing batch has no exact exhausted repair authority")
    relative = (
        f"{isolation_v4.RESEARCH_SESSION_ROOT}/admission-attempts/{team_id}/"
        f"{phase}-04.json"
    )
    payload = _canonical_admission_attempt(attempts[-1])
    return {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}


def missing_batch_exhaustion_may_exist(
    root: str | Path, team_id: str, phase: str
) -> bool:
    """Route only a possible attempt-04 to the authoritative missing-batch validator."""

    root_path = Path(root).resolve()
    TOP40_V4_LAYOUT.require_team(team_id)
    if phase not in {"discovery", "refinement"}:
        return False
    return os.path.lexists(
        _admission_attempt_directory(root_path, team_id) / f"{phase}-04.json"
    )


def _phase_archive(root: Path, team_id: str, phase: str) -> tuple[Path, bytes] | None:
    directory = root / f"{isolation_v4.RESEARCH_SESSION_ROOT}/outboxes/{team_id}"
    if not directory.exists():
        return None
    if directory.is_symlink() or not directory.is_dir():
        raise ResearchRuntimeError("research outbox archive is missing or unsafe")
    prefix = f"{phase}-"
    matches = [
        path
        for path in directory.iterdir()
        if path.name.startswith(prefix) and path.name.endswith(".json")
    ]
    if len(matches) > 1:
        raise ResearchRuntimeError("research outbox archive is not unique")
    if not matches:
        return None
    payload = _stable_bytes(matches[0])
    digest = hashlib.sha256(payload).hexdigest()
    if matches[0].name != f"{phase}-{digest}.json":
        raise ResearchRuntimeError("research outbox archive digest differs")
    return matches[0], payload


def _journal_feedback_row(
    root: Path,
    state: journal_v4.JournalState,
    team_id: str,
    candidate_id: str,
) -> Mapping[str, object]:
    matches = [
        (digest, record)
        for digest, record in state.is_requests.items()
        if record["payload"]["team_id"] == team_id
        and record["payload"]["candidate_id"] == candidate_id
    ]
    if len(matches) != 1:
        raise ResearchRuntimeError("prior phase candidate lacks one accepted journal authority")
    request_hash, request = matches[0]
    terminal = state.is_terminals.get(request_hash)
    if terminal is None:
        raise ResearchRuntimeError("prior phase candidate lacks a terminal journal record")
    row: dict[str, object] = {
        "candidate_id": candidate_id,
        "request_record_sha256": request_hash,
        "terminal_status": terminal["event_type"],
        "trial_number": request["payload"]["trial_number"],
    }
    if terminal["event_type"] == "is_failed":
        row["failure"] = str(terminal["payload"]["failure"])
        return row
    # Imported lazily to avoid the orchestrator -> research-runtime import cycle.
    from crypto_trade.tournament import orchestrator_v4

    summary = orchestrator_v4._verified_summary(root, terminal)  # noqa: SLF001
    row["summary"] = {
        "bootstrap_probability_positive_mean": summary[
            "bootstrap_probability_positive_mean"
        ],
        "diagnostics": summary["diagnostics"],
        "folds": summary["folds"],
        "regime_sharpe": summary["regime_sharpe"],
        "scored_window": summary["scored_window"],
        "selection": summary["selection"],
    }
    return row


def _validate_prior_phase_evidence(root: Path, team_id: str, phase: str) -> None:
    feedback_path = root / TOP40_V4_LAYOUT.team_root(team_id) / "feedback" / f"{phase}.json"
    try:
        feedback = json.loads(_stable_bytes(feedback_path))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError("prior research feedback is invalid JSON") from exc
    archive = _phase_archive(root, team_id, phase)
    if archive is None:
        raise ResearchRuntimeError("prior research outbox archive is missing")
    _archive_path, payload = archive
    try:
        request = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError("prior research outbox archive is invalid JSON") from exc
    candidate_ids = _validate_phase_request(request, phase)
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    rows = request["requests"]
    expected_results = [
        _journal_feedback_row(root, state, team_id, candidate_id)
        for candidate_id in candidate_ids
    ]
    first_trial = 1 if phase == "discovery" else 9
    if [row["trial_number"] for row in expected_results] != list(
        range(first_trial, first_trial + len(candidate_ids))
    ):
        raise ResearchRuntimeError("prior research journal trial sequence differs")
    for row, candidate_id in zip(rows, candidate_ids, strict=True):
        accepted = next(
            record["payload"]
            for record in state.is_requests.values()
            if record["payload"]["team_id"] == team_id
            and record["payload"]["candidate_id"] == candidate_id
        )
        if (
            accepted["purpose"] != row["purpose"]
            or accepted["authority"].get("entrypoint")
            != f"{TOP40_V4_LAYOUT.team_root(team_id)}/{row['entrypoint']}"
        ):
            raise ResearchRuntimeError("prior research request differs from journal authority")
    expected_feedback = {
        "schema_version": 1,
        "tournament": TOP40_V4_LAYOUT.name,
        "team_id": team_id,
        "phase": phase,
        "interim_field_disclosure": False,
        "results": expected_results,
    }
    if feedback != expected_feedback:
        raise ResearchRuntimeError("prior research feedback differs from journal authority")


def _validate_runtime_launch_lifecycle(root: Path, team_id: str, phase: str) -> None:
    state = journal_v4.read(root / TOP40_V4_LAYOUT.journal_path)
    if state.selection is not None:
        raise ResearchRuntimeError("research launch is forbidden after IS selection")
    if team_id in state.nominations or team_id in state.retired:
        raise ResearchRuntimeError("research launch is forbidden for a terminal lane")
    expected_trials = {"discovery": 0, "refinement": 8, "decision": 12}[phase]
    if state.trials_by_team.get(team_id, 0) != expected_trials:
        raise ResearchRuntimeError("research launch trial count is out of phase")
    if _phase_archive(root, team_id, phase) is not None:
        raise ResearchRuntimeError("research phase already has an archived outbox")
    if phase in {"refinement", "decision"}:
        _validate_prior_phase_evidence(root, team_id, "discovery")
    if phase == "decision":
        _validate_prior_phase_evidence(root, team_id, "refinement")


def recover_candidate_receipts(
    root: str | Path,
    team_id: str,
    phase: str,
    outbox_path: str | Path,
) -> tuple[Mapping[str, str], ...]:
    """Resume after a launcher crash once an authorized phase has produced an outbox."""

    if phase not in {"discovery", "refinement"}:
        raise ResearchRuntimeError("only research batches have candidate receipts")
    root_path = Path(root).resolve()
    validate_launch_authority(root_path, team_id, phase)
    try:
        request = json.loads(_stable_bytes(Path(outbox_path)))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError("recovered team outbox is invalid JSON") from exc
    candidate_ids = _validate_phase_request(request, phase)
    probes = run_profile_probes(root_path, team_id)
    return record_candidate_receipts(root_path, team_id, phase, candidate_ids, probes=probes)


def _codex_exec_command(
    root: Path,
    team_id: str,
    *,
    model: str,
    prompt: str,
) -> list[str]:
    paths = _team_paths(root, team_id)
    return [
        str(_codex_binary()),
        "exec",
        "--strict-config",
        "--ignore-user-config",
        # `--ignore-user-config` rebuilds the exec-layer configuration. Keep every security
        # override after it; pre-subcommand overrides are silently lost by Codex CLI 0.148.
        *codex_profile_arguments(root, team_id),
        *sum((["--disable", feature] for feature in _DISABLED_FEATURES), []),
        "--ephemeral",
        "--skip-git-repo-check",
        "--cd",
        str(paths["team"]),
        "--model",
        model,
        "--config",
        f'model_reasoning_effort="{_MODEL_REASONING_EFFORT}"',
        prompt,
    ]


def _model_command_authority(root: Path, team_id: str, phase: str) -> Mapping[str, str]:
    prompt = team_phase_prompt(team_id, phase)
    command = _codex_exec_command(root, team_id, model=_MODEL_NAME, prompt=prompt)
    return {
        "command_sha256": hashlib.sha256(_canonical(command)).hexdigest(),
        "environment_sha256": model_environment_sha256(root, team_id),
        "model": _MODEL_NAME,
        "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
    }


def validate_frozen_model_smoke(root: str | Path) -> Mapping[str, object]:
    """Bind live model admission to the exact tracked skill-boundary smoke authority."""

    root_path = Path(root).resolve()
    path = root_path / "tournament/top40-v4-r2/PRETRIAL-MODEL-SMOKE.json"

    def unique(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                raise ResearchRuntimeError("model-smoke receipt contains a duplicate key")
            result[key] = value
        return result

    try:
        receipt = json.loads(
            _stable_bytes(path),
            object_pairs_hook=unique,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"nonfinite value: {value}")
            ),
        )
    except (UnicodeError, ValueError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError("model-smoke receipt is invalid JSON") from exc
    expected_keys = {
        "approval",
        "codex_session_id",
        "codex_version",
        "command_sha256",
        "durable_lane_delta_after_verified_cleanup",
        "environment_sha256",
        "host_skill_roots_denied",
        "launcher_version",
        "model",
        "model_reply",
        "model_runtime_sha256",
        "network_enabled",
        "observed_on_date",
        "organizer_observed",
        "original_home_excluded",
        "peer_private_runtime_read_denied",
        "peer_private_runtime_write_denied",
        "private_model_auth_denied",
        "private_runtime_removed_before_activation",
        "process_returncode",
        "profile_sha256",
        "prompt_catalog_bytes",
        "prompt_catalog_empty",
        "prompt_catalog_sha256",
        "prompt_sha256",
        "purpose",
        "record_sha256",
        "requested_sentinel",
        "sandbox",
        "schema_version",
        "sentinel_sha256",
        "skill_catalog",
        "system_skill_marker_sha256",
        "team_id",
        "tmpdir_isolated",
        "tournament",
    }
    if not isinstance(receipt, Mapping) or set(receipt) != expected_keys:
        raise ResearchRuntimeError("model-smoke receipt schema differs")
    unsigned = dict(receipt)
    record_sha256 = unsigned.pop("record_sha256")
    expected_command = _codex_exec_command(
        root_path, "team-01", model=_MODEL_NAME, prompt=_SMOKE_PROMPT
    )
    exact = {
        "approval": "never",
        "codex_version": _EXPECTED_CODEX_VERSION,
        "command_sha256": hashlib.sha256(_canonical(expected_command)).hexdigest(),
        "durable_lane_delta_after_verified_cleanup": [],
        "environment_sha256": model_environment_sha256(root_path, "team-01"),
        "host_skill_roots_denied": True,
        "launcher_version": LAUNCHER_VERSION,
        "model": _MODEL_NAME,
        "model_reply": "smoke-complete",
        "model_runtime_sha256": model_runtime_sha256(root_path, "team-01"),
        "network_enabled": False,
        "observed_on_date": "2026-08-21",
        "organizer_observed": True,
        "original_home_excluded": True,
        "peer_private_runtime_read_denied": True,
        "peer_private_runtime_write_denied": True,
        "private_model_auth_denied": True,
        "private_runtime_removed_before_activation": True,
        "process_returncode": 0,
        "profile_sha256": profile_sha256(root_path, "team-01"),
        "prompt_catalog_bytes": 8853,
        "prompt_catalog_empty": True,
        "prompt_sha256": hashlib.sha256(_SMOKE_PROMPT.encode("utf-8")).hexdigest(),
        "purpose": "pretrial-private-home-skill-boundary-smoke",
        "requested_sentinel": "work/.r2-v12-model-write-smoke",
        "sandbox": "custom permissions",
        "schema_version": 2,
        "sentinel_sha256": hashlib.sha256(b"r8-private-skill-boundary-ok\n").hexdigest(),
        "skill_catalog": "empty-system-marker",
        "system_skill_marker_sha256": hashlib.sha256(_SYSTEM_SKILL_MARKER).hexdigest(),
        "team_id": "team-01",
        "tmpdir_isolated": True,
        "tournament": TOP40_V4_LAYOUT.name,
    }
    if any(receipt.get(key) != value for key, value in exact.items()):
        raise ResearchRuntimeError("model-smoke receipt authority differs")
    if (
        _codex_version(_codex_binary()) != _EXPECTED_CODEX_VERSION
        or not isinstance(receipt.get("codex_session_id"), str)
        or _SESSION_ID.fullmatch(str(receipt["codex_session_id"])) is None
        or _SHA256.fullmatch(str(receipt.get("prompt_catalog_sha256"))) is None
        or record_sha256 != hashlib.sha256(_canonical(unsigned)).hexdigest()
    ):
        raise ResearchRuntimeError("model-smoke receipt binding is invalid")
    return receipt


@serialized_r2_command
def launch_team_phase(
    root: str | Path,
    team_id: str,
    phase: str,
) -> Mapping[str, object]:
    """Run one ephemeral, networkless team phase and record candidate receipts."""

    if _PHASE.fullmatch(phase) is None:
        raise ResearchRuntimeError("team phase must be valid")
    root_path = Path(root).resolve()
    # A host/process crash can bypass the model subprocess's ``finally`` after it has atomically
    # published an outbox but removed a directory placeholder.  This direct entrypoint already
    # owns the broker lease through its decorator, so restore only absent writable markers before
    # activation compares the frozen surface.  Conflicting bytes or topology remain hard failures.
    _restore_writable_lane_markers_before_activation(root_path, team_id)
    # This exported launcher is itself an authority boundary; it cannot rely on a broker caller
    # having performed the activation check before the shared lease was acquired.
    from crypto_trade.tournament import activation_v4

    activation_v4.validate(root_path)
    activation_v4.require_completed_pretrial_recovery(root_path)
    validate_frozen_model_smoke(root_path)
    _validate_runtime_launch_lifecycle(root_path, team_id, phase)
    isolation_v4.audit_team_surface(root_path, team_id)
    paths = _team_paths(root_path, team_id)
    outbox_name = {
        "discovery": "batch-1.json",
        "refinement": "batch-2.json",
        "decision": "decision.json",
    }[phase]
    outbox_path = paths["outbox"] / outbox_name
    if phase == "decision" and os.path.lexists(outbox_path):
        raise ResearchRuntimeError("team decision outbox already exists")
    probes = run_profile_probes(root_path, team_id)
    launch_authority = _record_launch_authority(root_path, team_id, phase)
    prompt = team_phase_prompt(team_id, phase)
    command = _codex_exec_command(root_path, team_id, model=_MODEL_NAME, prompt=prompt)
    environment = _private_model_environment(root_path, team_id)
    model_sessions = 0

    def run_model() -> None:
        nonlocal model_sessions
        model_sessions += 1
        try:
            completed = subprocess.run(
                command,
                check=False,
                cwd=paths["team"],
                env=environment,
                stdin=subprocess.DEVNULL,
                preexec_fn=_private_child_setup,
                timeout=7_200,
            )
        finally:
            try:
                # A completed, failed, or interrupted phase never supplies hidden client state to
                # the next phase or repair session. Authentication and the empty skill marker are
                # the only durable private-runtime bytes.
                ensure_private_model_runtime(root_path, team_id)
            finally:
                # The model may remove directory placeholders while atomically publishing files.
                _restore_writable_lane_markers(root_path, team_id)
        if completed.returncode != 0:
            raise ResearchRuntimeError("isolated team process did not complete successfully")

    if phase == "decision":
        run_model()
        request = _strict_team_request(
            _stable_bytes(outbox_path), outbox_path.relative_to(root_path).as_posix()
        )
        _validate_phase_request(request, phase)
        return {
            "ok": True,
            "team_id": team_id,
            "phase": phase,
            "profile_sha256": profile_sha256(root_path, team_id),
            "model_runtime_sha256": model_runtime_sha256(root_path, team_id),
            "launch_authority": launch_authority,
            "probes": probes,
            "candidate_receipts": [],
            "model_sessions": model_sessions,
            "repair_attempts": 0,
            "outbox_path": f"{TOP40_V4_LAYOUT.team_root(team_id)}/outbox/{outbox_name}",
        }

    def inspect_current_output() -> Mapping[str, object]:
        if os.path.lexists(outbox_path):
            return _score_blind_batch_inspection(
                root_path, team_id, phase, outbox_path
            )
        return {
            "candidate_ids": [],
            "findings": [f"outbox: required {outbox_name} was not published"],
            "outbox_sha256": hashlib.sha256(b"").hexdigest(),
            "source_bundle_sha256s": [],
        }

    def matches_attempt(
        inspection: Mapping[str, object], attempt: Mapping[str, object]
    ) -> bool:
        return all(
            list(inspection[key]) == attempt[key]
            if key in {"candidate_ids", "findings", "source_bundle_sha256s"}
            else inspection[key] == attempt[key]
            for key in (
                "candidate_ids",
                "findings",
                "outbox_sha256",
                "source_bundle_sha256s",
            )
        )

    while True:
        attempts = _admission_attempts(root_path, team_id, phase)
        issues = _admission_session_issues(
            root_path, team_id, phase, launch_authority["sha256"]
        )
        outstanding_issue = len(issues) == len(attempts) + 1
        if outstanding_issue:
            inspection = inspect_current_output()
            if not inspection["findings"]:
                candidate_ids = [str(value) for value in inspection["candidate_ids"]]
                receipts = record_candidate_receipts(
                    root_path,
                    team_id,
                    phase,
                    candidate_ids,
                    probes=probes,
                )
                return {
                    "ok": True,
                    "team_id": team_id,
                    "phase": phase,
                    "profile_sha256": profile_sha256(root_path, team_id),
                    "model_runtime_sha256": model_runtime_sha256(root_path, team_id),
                    "launch_authority": launch_authority,
                    "probes": probes,
                    "candidate_receipts": list(receipts),
                    "model_sessions": model_sessions,
                    "repair_attempts": max(0, len(issues) - 1),
                    "outbox_path": (
                        f"{TOP40_V4_LAYOUT.team_root(team_id)}/outbox/{outbox_name}"
                    ),
                }
            attempt, _created = _record_admission_attempt(
                root_path,
                team_id,
                phase,
                inspection,
                # One durable issue represents one consumed process opportunity. Even an
                # unchanged result after a host crash must advance the attempt chain.
                repeat=True,
            )
            if int(attempt["attempt_number"]) > _MAX_SCORE_BLIND_REPAIR_SESSIONS:
                raise CandidateRepairExhaustedError(
                    "batch remained invalid after every score-blind repair session"
                )
            continue

        if attempts:
            current = inspect_current_output()
            if not current["findings"] or not matches_attempt(current, attempts[-1]):
                raise ResearchRuntimeError(
                    "unissued model output differs from its last admission attempt"
                )
            if len(attempts) > _MAX_SCORE_BLIND_REPAIR_SESSIONS:
                raise CandidateRepairExhaustedError(
                    "batch remained invalid after every score-blind repair session"
                )
        elif os.path.lexists(outbox_path):
            raise ResearchRuntimeError("batch outbox exists without a model-session issue")

        _record_admission_session_issue(
            root_path,
            team_id,
            phase,
            launch_authority["sha256"],
            len(attempts),
        )
        run_model()


__all__ = [
    "LAUNCHER_VERSION",
    "PROFILE_NAME",
    "CandidateRepairExhaustedError",
    "CandidateReceiptRejectedError",
    "CandidateSourceRejectedError",
    "ResearchRuntimeError",
    "broker_lease",
    "codex_profile_arguments",
    "ensure_private_model_runtime",
    "launch_team_phase",
    "model_environment_sha256",
    "model_environment_spec",
    "profile_sha256",
    "profile_spec",
    "model_runtime_sha256",
    "model_runtime_spec",
    "record_candidate_receipts",
    "recover_candidate_receipts",
    "review_candidate_source",
    "run_profile_probes",
    "serialized_activated_r2_command",
    "serialized_r2_command",
    "team_phase_prompt",
    "validate_candidate_receipt",
    "validate_frozen_model_smoke",
    "validate_launch_authority",
    "validate_launch_authority_payload",
    "validate_source_review",
]
