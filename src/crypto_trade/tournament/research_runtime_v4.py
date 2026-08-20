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
RECEIPT_SCHEMA_VERSION = 1
SOURCE_REVIEW_SCHEMA_VERSION = 7
LAUNCHER_VERSION = "top40-v4-r2-research-runtime-v8"
_SHA256 = re.compile(r"[0-9a-f]{64}")
_SAFE_ID = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
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
        "disabled_capabilities",
        "launcher_version",
        "phase",
        "profile_sha256",
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
        "launcher_version",
        "phase",
        "profile_sha256",
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
        "host_process_hidden",
        "network_denied",
        "own_lane_write_allowed",
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


def _stable_bytes(path: Path, *, maximum: int = 2 * 1024 * 1024) -> bytes:
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
                raise ResearchRuntimeError("research authority is not a bounded regular file")
            payload = handle.read(maximum + 1)
            after = os.fstat(handle.fileno())
        current = path.lstat()
    except ResearchRuntimeError:
        raise
    except OSError as exc:
        raise ResearchRuntimeError("cannot read research authority safely") from exc
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
    if len(identities) != 1 or not stat.S_ISREG(current.st_mode) or len(payload) > maximum:
        raise ResearchRuntimeError("research authority changed while being read")
    return payload


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
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=30,
    )
    return completed.returncode


def run_profile_probes(root: str | Path, team_id: str) -> Mapping[str, object]:
    """Attack the actual research profile and return a bounded pass/fail receipt projection."""

    root_path = Path(root).resolve()
    paths = _team_paths(root_path, team_id)
    binary = _codex_binary()
    arguments = codex_profile_arguments(root_path, team_id)
    team = paths["team"]
    other_team = "team-02" if team_id != "team-02" else "team-01"
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
        _probe(binary, arguments, team, ("/usr/bin/test", "-r", str(path)))
        for path in allowed
    ]
    denied_codes = [
        _probe(binary, arguments, team, ("/usr/bin/test", "-r", str(path)))
        for path in denied
    ]
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
    )
    host_process = _probe(
        binary,
        arguments,
        team,
        ("/usr/bin/test", "!", "-e", f"/proc/{os.getpid()}/cmdline"),
    )
    result = {
        "allowed_reads": all(code == 0 for code in allowed_codes),
        "denied_reads": all(code != 0 for code in denied_codes),
        "cross_lane_write_denied": cross_lane_write == 0,
        "network_denied": network == 0,
        "host_process_hidden": host_process == 0,
        "own_lane_write_allowed": own_lane_write_allowed,
    }
    if not all(result.values()):
        raise ResearchRuntimeError("research clean-room profile failed its adversarial probes")
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


def _write_immutable(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
    except FileExistsError:
        if _stable_bytes(path) != payload:
            raise ResearchRuntimeError("immutable research receipt already differs")
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


def _record_launch_authority(root: Path, team_id: str, phase: str) -> Mapping[str, str]:
    launch = {
        "launcher_version": LAUNCHER_VERSION,
        "phase": phase,
        "profile_sha256": profile_sha256(root, team_id),
        "schema_version": 1,
        "status": "authorized",
        "team_id": team_id,
        "team_kit_sha256": _team_kit_sha256(root),
        "tournament": TOP40_V4_LAYOUT.name,
    }
    payload = json.dumps(
        launch, allow_nan=False, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("ascii") + b"\n"
    relative = _launch_relative(team_id, phase)
    _write_immutable(root / relative, payload)
    return {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}


def validate_launch_authority(root: str | Path, team_id: str, phase: str) -> Mapping[str, str]:
    root_path = Path(root).resolve()
    relative = _launch_relative(team_id, phase)
    payload = _stable_bytes(root_path / relative)
    try:
        launch = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError("research launch authority is invalid JSON") from exc
    expected = {
        "launcher_version": LAUNCHER_VERSION,
        "phase": phase,
        "profile_sha256": profile_sha256(root_path, team_id),
        "schema_version": 1,
        "status": "authorized",
        "team_id": team_id,
        "team_kit_sha256": _team_kit_sha256(root_path),
        "tournament": TOP40_V4_LAYOUT.name,
    }
    if not isinstance(launch, Mapping) or set(launch) != _LAUNCH_KEYS or dict(launch) != expected:
        raise ResearchRuntimeError("research launch authority differs")
    return {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}


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
            "candidate_root": capture.candidate_root,
            "codex_version": _codex_version(binary),
            "disabled_capabilities": list(_DISABLED_FEATURES),
            "launcher_version": LAUNCHER_VERSION,
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
            )
            recorded.append(existing)
            continue
        _write_immutable(root_path / relative, payload)
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
) -> Mapping[str, str]:
    """Verify the organizer-only session receipt bound to one captured candidate."""

    if not TOP40_V4_LAYOUT.name.endswith("-r2"):
        return {}
    root_path = Path(root).resolve()
    relative = _receipt_relative(team_id, source_bundle_sha256)
    payload = _stable_bytes(root_path / relative)
    try:
        receipt = json.loads(payload)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ResearchRuntimeError("research session receipt is invalid JSON") from exc
    if not isinstance(receipt, Mapping) or set(receipt) != _RECEIPT_KEYS:
        raise ResearchRuntimeError("research session receipt schema differs")
    probes = receipt.get("probes")
    expected = {
        "candidate_root": f"{TOP40_V4_LAYOUT.team_root(team_id)}/candidates/{candidate_id}",
        "disabled_capabilities": list(_DISABLED_FEATURES),
        "launcher_version": LAUNCHER_VERSION,
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
            raise ResearchRuntimeError(f"research session receipt differs in {key}")
    if _PHASE.fullmatch(str(receipt.get("phase"))) is None:
        raise ResearchRuntimeError("research session receipt phase is invalid")
    if (
        receipt.get("codex_version") != _codex_version(_codex_binary())
        or not isinstance(receipt.get("recorded_at_utc"), str)
        or _UTC.fullmatch(str(receipt["recorded_at_utc"])) is None
    ):
        raise ResearchRuntimeError("research session runtime authority differs")
    if not isinstance(probes, Mapping) or set(probes) != _PROBE_KEYS or not all(
        value is True for value in probes.values()
    ):
        raise ResearchRuntimeError("research session receipt probes did not pass")
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
        'model_reasoning_effort="high"',
        prompt,
    ]


@serialized_r2_command
def launch_team_phase(
    root: str | Path,
    team_id: str,
    phase: str,
    prompt: str,
    *,
    model: str = "gpt-5.6-sol",
) -> Mapping[str, object]:
    """Run one ephemeral, networkless team phase and record candidate receipts."""

    if _PHASE.fullmatch(phase) is None or not prompt.strip():
        raise ResearchRuntimeError("team phase and prompt must be valid")
    root_path = Path(root).resolve()
    # This exported launcher is itself an authority boundary; it cannot rely on a broker caller
    # having performed the activation check before the shared lease was acquired.
    from crypto_trade.tournament import activation_v4

    activation_v4.validate(root_path)
    activation_v4.require_completed_pretrial_recovery(root_path)
    _validate_runtime_launch_lifecycle(root_path, team_id, phase)
    isolation_v4.audit_team_surface(root_path, team_id)
    paths = _team_paths(root_path, team_id)
    outbox_name = {
        "discovery": "batch-1.json",
        "refinement": "batch-2.json",
        "decision": "decision.json",
    }[phase]
    if os.path.lexists(paths["outbox"] / outbox_name):
        raise ResearchRuntimeError("team phase outbox already exists")
    probes = run_profile_probes(root_path, team_id)
    launch_authority = _record_launch_authority(root_path, team_id, phase)
    command = _codex_exec_command(root_path, team_id, model=model, prompt=prompt)
    environment = {
        name: os.environ[name]
        for name in ("HOME", "LANG", "LC_ALL", "LC_CTYPE", "NO_COLOR", "PATH", "SHELL", "TERM")
        if name in os.environ
    }
    environment["TMPDIR"] = str(paths["work"])
    for name in _SINGLE_THREAD_ENVIRONMENT_VARIABLES:
        environment[name] = "1"
    completed = subprocess.run(
        command,
        check=False,
        cwd=paths["team"],
        env=environment,
        stdin=subprocess.DEVNULL,
        timeout=7_200,
    )
    if completed.returncode != 0:
        raise ResearchRuntimeError("isolated team process did not complete successfully")
    request = json.loads(_stable_bytes(paths["outbox"] / outbox_name))
    candidate_ids = _validate_phase_request(request, phase)
    receipts = (
        record_candidate_receipts(
            root_path,
            team_id,
            phase,
            candidate_ids,
            probes=probes,
        )
        if candidate_ids
        else ()
    )
    return {
        "ok": True,
        "team_id": team_id,
        "phase": phase,
        "profile_sha256": profile_sha256(root_path, team_id),
        "launch_authority": launch_authority,
        "probes": probes,
        "candidate_receipts": list(receipts),
        "outbox_path": f"{TOP40_V4_LAYOUT.team_root(team_id)}/outbox/{outbox_name}",
    }


__all__ = [
    "LAUNCHER_VERSION",
    "PROFILE_NAME",
    "CandidateSourceRejectedError",
    "ResearchRuntimeError",
    "broker_lease",
    "codex_profile_arguments",
    "launch_team_phase",
    "profile_sha256",
    "profile_spec",
    "record_candidate_receipts",
    "recover_candidate_receipts",
    "review_candidate_source",
    "run_profile_probes",
    "serialized_activated_r2_command",
    "serialized_r2_command",
    "validate_candidate_receipt",
    "validate_launch_authority",
    "validate_source_review",
]
