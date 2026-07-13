"""Persistent strategy worker executed inside the runner's Linux namespaces.

The worker never receives the canonical snapshot.  The trusted parent streams each closed bar and
past funding row at most once, together with the current eligible-symbol set.  Standard output is
reserved for the JSON-lines control protocol; team output is redirected to standard error.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import dataclasses
import errno
import importlib
import importlib.util
import json
import math
import os
import resource
import subprocess
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, TextIO

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

_PROCESS_AUDIT_EVENTS = frozenset(
    {
        "os.exec",
        "os.fork",
        "os.forkpty",
        "os.posix_spawn",
        "os.spawn",
        "os.system",
        "pty.spawn",
        "subprocess.Popen",
    }
)
_PR_CAPBSET_DROP = 24
_PR_SET_NO_NEW_PRIVS = 38
_PR_SET_SECCOMP = 22
_SECCOMP_MODE_FILTER = 2
_LINUX_CAPABILITY_VERSION_3 = 0x20080522
_LANDLOCK_CREATE_RULESET_VERSION = 1
_LANDLOCK_RULE_PATH_BENEATH = 1
_LANDLOCK_MINIMUM_ABI = 6
_LANDLOCK_SYSCALL_CREATE_RULESET = 444
_LANDLOCK_SYSCALL_ADD_RULE = 445
_LANDLOCK_SYSCALL_RESTRICT_SELF = 446
_LANDLOCK_ACCESS_FS_EXECUTE = 1 << 0
_LANDLOCK_ACCESS_FS_WRITE_FILE = 1 << 1
_LANDLOCK_ACCESS_FS_READ_FILE = 1 << 2
_LANDLOCK_ACCESS_FS_READ_DIR = 1 << 3
_LANDLOCK_ACCESS_FS_REMOVE_DIR = 1 << 4
_LANDLOCK_ACCESS_FS_REMOVE_FILE = 1 << 5
_LANDLOCK_ACCESS_FS_MAKE_CHAR = 1 << 6
_LANDLOCK_ACCESS_FS_MAKE_DIR = 1 << 7
_LANDLOCK_ACCESS_FS_MAKE_REG = 1 << 8
_LANDLOCK_ACCESS_FS_MAKE_SOCK = 1 << 9
_LANDLOCK_ACCESS_FS_MAKE_FIFO = 1 << 10
_LANDLOCK_ACCESS_FS_MAKE_BLOCK = 1 << 11
_LANDLOCK_ACCESS_FS_MAKE_SYM = 1 << 12
_LANDLOCK_ACCESS_FS_REFER = 1 << 13
_LANDLOCK_ACCESS_FS_TRUNCATE = 1 << 14
_LANDLOCK_ACCESS_FS_IOCTL_DEV = 1 << 15
_LANDLOCK_ACCESS_NET_BIND_TCP = 1 << 0
_LANDLOCK_ACCESS_NET_CONNECT_TCP = 1 << 1
_LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET = 1 << 0
_LANDLOCK_SCOPE_SIGNAL = 1 << 1
_LANDLOCK_FS_ALL = (1 << 16) - 1
_AUDIT_ARCH_X86_64 = 0xC000003E
_X32_SYSCALL_BIT = 0x40000000
_BPF_LD_W_ABS = 0x20
_BPF_JMP_JEQ_K = 0x15
_BPF_JMP_JGE_K = 0x35
_BPF_RET_K = 0x06
_SECCOMP_RET_KILL_PROCESS = 0x80000000
_SECCOMP_RET_ERRNO = 0x00050000
_SECCOMP_RET_ALLOW = 0x7FFF0000
_DENIED_SYSCALLS_X86_64 = (
    41,  # socket
    42,  # connect
    43,  # accept
    44,  # sendto
    49,  # bind
    50,  # listen
    53,  # socketpair
    56,  # clone
    57,  # fork
    58,  # vfork
    59,  # execve
    101,  # ptrace
    155,  # pivot_root
    161,  # chroot
    165,  # mount
    166,  # umount2
    167,  # swapon
    168,  # swapoff
    169,  # reboot
    172,  # iopl
    173,  # ioperm
    175,  # init_module
    176,  # delete_module
    179,  # quotactl
    246,  # kexec_load
    248,  # add_key
    249,  # request_key
    250,  # keyctl
    272,  # unshare
    288,  # accept4
    298,  # perf_event_open
    300,  # fanotify_init
    303,  # name_to_handle_at
    304,  # open_by_handle_at
    308,  # setns
    310,  # process_vm_readv
    311,  # process_vm_writev
    313,  # finit_module
    320,  # kexec_file_load
    321,  # bpf
    322,  # execveat
    323,  # userfaultfd
    425,  # io_uring_setup
    426,  # io_uring_enter
    427,  # io_uring_register
    435,  # clone3
    438,  # pidfd_getfd
)
_WORKER_RESOURCE_LIMITS = (
    (resource.RLIMIT_AS, 4 * 1024**3, "address space"),
    (resource.RLIMIT_CORE, 0, "core dump"),
    (resource.RLIMIT_CPU, 900, "CPU time"),
    (resource.RLIMIT_FSIZE, 1024 * 1024, "file size"),
    (resource.RLIMIT_NOFILE, 128, "open files"),
    (resource.RLIMIT_NPROC, 32, "processes/threads"),
)
_LATCHED_SANDBOX_VIOLATION: str | None = None


class StrategySandboxViolationError(RuntimeError):
    """Raised when strategy code attempts an operation forbidden by the worker sandbox."""


def _latch_sandbox_violation(message: str) -> None:
    global _LATCHED_SANDBOX_VIOLATION
    if _LATCHED_SANDBOX_VIOLATION is None:
        _LATCHED_SANDBOX_VIOLATION = message


def _raise_latched_sandbox_violation() -> None:
    if _LATCHED_SANDBOX_VIOLATION is not None:
        raise StrategySandboxViolationError(_LATCHED_SANDBOX_VIOLATION)


@dataclasses.dataclass
class _HistoryBuffer:
    """Append-only typed columns with geometric capacity and read-only pandas views."""

    columns: tuple[str, ...]
    dtypes: tuple[str, ...]
    datetime_columns: frozenset[str]
    arrays: dict[str, np.ndarray] = dataclasses.field(default_factory=dict)
    length: int = 0
    capacity: int = 0
    last_time: pd.Timestamp | None = None

    def __post_init__(self) -> None:
        if len(self.columns) != len(self.dtypes):
            raise ValueError("history columns and dtypes differ in length")
        if not self.datetime_columns.issubset(self.columns):
            raise ValueError("history datetime columns are absent from schema")

    def _numpy_dtype(self, column: str, descriptor: str) -> np.dtype[Any]:
        if column in self.datetime_columns:
            dtype = pd.api.types.pandas_dtype(descriptor)
            if not isinstance(dtype, pd.DatetimeTZDtype):
                raise TypeError(f"datetime column {column} requires a timezone dtype")
            return np.dtype(f"datetime64[{dtype.unit}]")
        try:
            dtype = np.dtype(descriptor)
        except TypeError:
            return np.dtype(object)
        if dtype.kind in "biufc":
            return dtype
        return np.dtype(object)

    def _ensure_capacity(self, required: int) -> None:
        if required <= self.capacity:
            return
        capacity = max(16, self.capacity)
        while capacity < required:
            capacity *= 2
        replacement: dict[str, np.ndarray] = {}
        for column, descriptor in zip(self.columns, self.dtypes, strict=True):
            dtype = self._numpy_dtype(column, descriptor)
            values = np.empty(capacity, dtype=dtype)
            if dtype.kind == "O":
                values.fill(None)
            else:
                values.fill(0)
            existing = self.arrays.get(column)
            if existing is not None and self.length:
                values[: self.length] = existing[: self.length]
            replacement[column] = values
        self.arrays = replacement
        self.capacity = capacity

    def append(self, rows: Sequence[Sequence[Any]]) -> None:
        if not rows:
            return
        start = self.length
        stop = start + len(rows)
        self._ensure_capacity(stop)
        for values in self.arrays.values():
            values.flags.writeable = True
        try:
            for row_offset, row in enumerate(rows, start=start):
                if len(row) != len(self.columns):
                    raise ValueError("history row differs from the declared schema")
                for column, descriptor, value in zip(self.columns, self.dtypes, row, strict=True):
                    if column in self.datetime_columns:
                        dtype = pd.api.types.pandas_dtype(descriptor)
                        assert isinstance(dtype, pd.DatetimeTZDtype)
                        timestamp = pd.Timestamp(value)
                        if timestamp.tzinfo is None:
                            timestamp = timestamp.tz_localize("UTC")
                        else:
                            timestamp = timestamp.tz_convert("UTC")
                        value = timestamp.as_unit(dtype.unit).to_datetime64()
                    self.arrays[column][row_offset] = value
            self.length = stop
        finally:
            for values in self.arrays.values():
                values.flags.writeable = False

    @classmethod
    def from_frame(
        cls,
        frame: pd.DataFrame,
        *,
        columns: tuple[str, ...],
        dtypes: tuple[str, ...],
        datetime_columns: frozenset[str],
    ) -> _HistoryBuffer:
        buffer = cls(columns, dtypes, datetime_columns)
        if frame.empty:
            return buffer
        buffer._ensure_capacity(len(frame))
        for values in buffer.arrays.values():
            values.flags.writeable = True
        try:
            for column, descriptor in zip(columns, dtypes, strict=True):
                if column in datetime_columns:
                    dtype = pd.api.types.pandas_dtype(descriptor)
                    assert isinstance(dtype, pd.DatetimeTZDtype)
                    values = pd.to_datetime(frame[column], utc=True).array.as_unit(dtype.unit).asi8
                    buffer.arrays[column][: len(frame)] = values.view(f"datetime64[{dtype.unit}]")
                else:
                    target_dtype = buffer.arrays[column].dtype
                    buffer.arrays[column][: len(frame)] = frame[column].to_numpy(
                        dtype=target_dtype, copy=False
                    )
            buffer.length = len(frame)
        finally:
            for values in buffer.arrays.values():
                values.flags.writeable = False
        return buffer

    def frame(self) -> pd.DataFrame:
        data: dict[str, pd.Series[Any] | pd.api.extensions.ExtensionArray] = {}
        for column, descriptor in zip(self.columns, self.dtypes, strict=True):
            values = self.arrays.get(column)
            if values is None:
                values = np.empty(0, dtype=self._numpy_dtype(column, descriptor))
                values.flags.writeable = False
            else:
                values = values[: self.length]
            if column in self.datetime_columns:
                data[column] = pd.array(values, dtype=descriptor, copy=False)
            else:
                data[column] = pd.Series(values, copy=False)
        return pd.DataFrame(data, columns=self.columns, copy=False)


@dataclasses.dataclass
class _WorkerState:
    strategy: Any
    seed: int
    interval: pd.Timedelta
    bar_columns: tuple[str, ...]
    bar_dtypes: tuple[str, ...]
    bar_datetime_columns: frozenset[str]
    funding_columns: tuple[str, ...]
    funding_dtypes: tuple[str, ...]
    funding_datetime_columns: frozenset[str]
    bars: dict[str, _HistoryBuffer] = dataclasses.field(default_factory=dict)
    funding: dict[str, _HistoryBuffer] = dataclasses.field(default_factory=dict)
    funding_context: _HistoryBuffer | None = None
    funding_eligible: frozenset[str] | None = None
    funding_last_key: tuple[Any, ...] | None = None
    previous_decision: pd.Timestamp | None = None


class _CapabilityHeader(ctypes.Structure):
    _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]


class _CapabilityData(ctypes.Structure):
    _fields_ = [
        ("effective", ctypes.c_uint32),
        ("permitted", ctypes.c_uint32),
        ("inheritable", ctypes.c_uint32),
    ]


class _LandlockRulesetAttr(ctypes.Structure):
    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
        ("scoped", ctypes.c_uint64),
    ]


class _LandlockPathBeneathAttr(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


class _SockFilter(ctypes.Structure):
    _fields_ = [
        ("code", ctypes.c_ushort),
        ("jt", ctypes.c_ubyte),
        ("jf", ctypes.c_ubyte),
        ("k", ctypes.c_uint32),
    ]


class _SockFprog(ctypes.Structure):
    _fields_ = [("length", ctypes.c_ushort), ("filter", ctypes.POINTER(_SockFilter))]


def _run_mount(*arguments: str) -> None:
    command = ["mount", *arguments]
    try:
        result = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError as exc:
        raise RuntimeError(f"cannot execute mount helper: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown mount failure"
        raise RuntimeError(f"{' '.join(command)} failed: {detail}")


def _sensitive_paths(root: Path) -> tuple[Path, ...]:
    fixed = (
        root / ".git",
        root / "data",
        root / "reports-top40",
        root / "tournament/top40/teams",
        root / "src/crypto_trade/portfolio",
        root / "analysis/portfolio",
        root / "TOURNAMENT-CHARTER-MN4.md",
    )
    patterns = (
        "reports-*",
        "briefs-portfolio-*",
        "diary-portfolio-*",
        "ORCHESTRATOR_BRIEF*",
    )
    paths = {path.absolute() for path in fixed}
    for pattern in patterns:
        paths.update(path.absolute() for path in root.glob(pattern))
    return tuple(sorted(paths, key=lambda path: path.as_posix()))


def _bind_read_only(source: Path, target: Path | None = None) -> None:
    destination = target or source
    _run_mount("--bind", str(source), str(destination))
    _run_mount("-o", "remount,bind,ro", str(destination))


def _hide_path(path: Path, *, empty_dir: Path, empty_file: Path) -> bool:
    if not path.exists() and not path.is_symlink():
        return False
    source = empty_dir if path.is_dir() else empty_file
    _run_mount("--bind", str(source), str(path))
    _run_mount("-o", "remount,bind,ro", str(path))
    return True


def _ensure_no_new_privs(libc: ctypes.CDLL | None = None) -> None:
    library = libc or ctypes.CDLL(None, use_errno=True)
    if library.prctl(_PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        error = ctypes.get_errno()
        raise RuntimeError(f"cannot set no_new_privs: {os.strerror(error)}")


def _drop_mount_capabilities() -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    try:
        last_capability = int(Path("/proc/sys/kernel/cap_last_cap").read_text().strip())
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"cannot determine Linux capability range: {exc}") from exc
    for capability in range(last_capability + 1):
        if libc.prctl(_PR_CAPBSET_DROP, capability, 0, 0, 0) != 0:
            error = ctypes.get_errno()
            raise RuntimeError(f"cannot drop capability {capability}: {os.strerror(error)}")
    header = _CapabilityHeader(_LINUX_CAPABILITY_VERSION_3, 0)
    data = (_CapabilityData * 2)()
    capset = getattr(libc, "capset", None)
    if capset is None or capset(ctypes.byref(header), ctypes.byref(data)) != 0:
        error = ctypes.get_errno()
        raise RuntimeError(f"cannot clear worker capabilities: {os.strerror(error)}")
    _ensure_no_new_privs(libc)


def _apply_worker_resource_limits() -> None:
    for resource_id, requested, label in _WORKER_RESOURCE_LIMITS:
        _soft, current_hard = resource.getrlimit(resource_id)
        limit = (
            requested if current_hard == resource.RLIM_INFINITY else min(requested, current_hard)
        )
        try:
            resource.setrlimit(resource_id, (limit, limit))
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"cannot enforce worker {label} resource limit") from exc
        actual = resource.getrlimit(resource_id)
        if actual != (limit, limit):
            raise RuntimeError(f"worker {label} resource limit was not enforced")


def _landlock_abi(libc: ctypes.CDLL) -> int:
    libc.syscall.restype = ctypes.c_long
    result = libc.syscall(
        _LANDLOCK_SYSCALL_CREATE_RULESET,
        ctypes.c_void_p(),
        ctypes.c_size_t(0),
        ctypes.c_uint(_LANDLOCK_CREATE_RULESET_VERSION),
    )
    return int(result)


def _landlock_read_paths(bundle: Path, runtime_site_packages: Path) -> tuple[Path, ...]:
    candidates = [bundle, runtime_site_packages, Path(sys.base_prefix)]
    candidates.extend(Path(value) for value in sys.path if value)
    candidates.extend(
        Path(value)
        for value in (
            "/lib",
            "/lib64",
            "/usr/lib",
            "/usr/lib64",
            "/usr/local/lib",
            "/etc/ld.so.cache",
            "/etc/localtime",
            "/usr/share/zoneinfo/UTC",
            "/dev/null",
            "/dev/random",
            "/dev/urandom",
        )
    )
    allowed: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except (OSError, RuntimeError):
            continue
        if resolved == Path(resolved.anchor):
            raise RuntimeError("refusing a filesystem-root Landlock exception")
        allowed.add(resolved)
    required = {bundle.resolve(), runtime_site_packages.resolve()}
    if not required.issubset(allowed):
        raise RuntimeError("Landlock runtime allowlist is missing a required path")
    return tuple(sorted(allowed, key=lambda path: path.as_posix()))


def _install_landlock(bundle: Path, runtime_site_packages: Path) -> tuple[Path, ...]:
    libc = ctypes.CDLL(None, use_errno=True)
    abi = _landlock_abi(libc)
    if abi < _LANDLOCK_MINIMUM_ABI:
        error = ctypes.get_errno()
        detail = os.strerror(error) if abi < 0 and error else f"ABI {abi}"
        raise RuntimeError(
            f"Landlock ABI {_LANDLOCK_MINIMUM_ABI}+ is required; unavailable ({detail})"
        )
    ruleset_attr = _LandlockRulesetAttr(
        handled_access_fs=_LANDLOCK_FS_ALL,
        handled_access_net=(_LANDLOCK_ACCESS_NET_BIND_TCP | _LANDLOCK_ACCESS_NET_CONNECT_TCP),
        scoped=(_LANDLOCK_SCOPE_ABSTRACT_UNIX_SOCKET | _LANDLOCK_SCOPE_SIGNAL),
    )
    ruleset_fd = int(
        libc.syscall(
            _LANDLOCK_SYSCALL_CREATE_RULESET,
            ctypes.byref(ruleset_attr),
            ctypes.sizeof(ruleset_attr),
            0,
        )
    )
    if ruleset_fd < 0:
        error = ctypes.get_errno()
        raise RuntimeError(f"cannot create Landlock ruleset: {os.strerror(error)}")
    allowed_paths = _landlock_read_paths(bundle, runtime_site_packages)
    try:
        for path in allowed_paths:
            path_fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                access = _LANDLOCK_ACCESS_FS_READ_FILE | _LANDLOCK_ACCESS_FS_EXECUTE
                if path.is_dir():
                    access |= _LANDLOCK_ACCESS_FS_READ_DIR
                if path in {Path("/dev/null"), Path("/dev/random"), Path("/dev/urandom")}:
                    access |= _LANDLOCK_ACCESS_FS_WRITE_FILE
                rule = _LandlockPathBeneathAttr(
                    allowed_access=access,
                    parent_fd=path_fd,
                )
                result = libc.syscall(
                    _LANDLOCK_SYSCALL_ADD_RULE,
                    ruleset_fd,
                    _LANDLOCK_RULE_PATH_BENEATH,
                    ctypes.byref(rule),
                    0,
                )
                if result != 0:
                    error = ctypes.get_errno()
                    raise RuntimeError(f"cannot add Landlock rule for {path}: {os.strerror(error)}")
            finally:
                os.close(path_fd)
        _ensure_no_new_privs(libc)
        if libc.syscall(_LANDLOCK_SYSCALL_RESTRICT_SELF, ruleset_fd, 0) != 0:
            error = ctypes.get_errno()
            raise RuntimeError(f"cannot enforce Landlock ruleset: {os.strerror(error)}")
    finally:
        os.close(ruleset_fd)

    probe = Path("/etc/passwd")
    if probe.exists():
        try:
            descriptor = os.open(probe, os.O_RDONLY | os.O_CLOEXEC)
        except PermissionError:
            pass
        else:
            os.close(descriptor)
            raise RuntimeError("Landlock self-test could still read /etc/passwd")
    return allowed_paths


def _install_seccomp_denylist() -> None:
    if os.uname().machine != "x86_64":
        raise RuntimeError("seccomp syscall policy currently requires x86_64")
    instructions = [
        _SockFilter(_BPF_LD_W_ABS, 0, 0, 4),
        _SockFilter(_BPF_JMP_JEQ_K, 1, 0, _AUDIT_ARCH_X86_64),
        _SockFilter(_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
        _SockFilter(_BPF_LD_W_ABS, 0, 0, 0),
        _SockFilter(_BPF_JMP_JGE_K, 0, 1, _X32_SYSCALL_BIT),
        _SockFilter(_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
    ]
    for syscall_number in _DENIED_SYSCALLS_X86_64:
        instructions.extend(
            (
                _SockFilter(_BPF_JMP_JEQ_K, 0, 1, syscall_number),
                _SockFilter(_BPF_RET_K, 0, 0, _SECCOMP_RET_ERRNO | errno.EPERM),
            )
        )
    instructions.append(_SockFilter(_BPF_RET_K, 0, 0, _SECCOMP_RET_ALLOW))
    filters = (_SockFilter * len(instructions))(*instructions)
    program = _SockFprog(
        length=len(instructions),
        filter=ctypes.cast(filters, ctypes.POINTER(_SockFilter)),
    )
    libc = ctypes.CDLL(None, use_errno=True)
    _ensure_no_new_privs(libc)
    if libc.prctl(_PR_SET_SECCOMP, _SECCOMP_MODE_FILTER, ctypes.byref(program)) != 0:
        error = ctypes.get_errno()
        raise RuntimeError(f"cannot enforce seccomp syscall policy: {os.strerror(error)}")


def _prepare_mount_namespace(
    root: Path,
    repository_parent: Path,
    bundle: Path,
    site_packages: Path,
    runtime_site_packages: Path,
    empty_dir: Path,
    empty_file: Path,
) -> None:
    for name, path, expected in (
        ("repository", root, "directory"),
        ("repository parent", repository_parent, "directory"),
        ("team source bundle", bundle, "directory"),
        ("venv site-packages", site_packages, "directory"),
        ("staged runtime site-packages", runtime_site_packages, "directory"),
        ("empty directory", empty_dir, "directory"),
        ("empty file", empty_file, "file"),
    ):
        valid = path.is_dir() if expected == "directory" else path.is_file()
        if not valid:
            raise RuntimeError(f"sandbox {name} is not a {expected}: {path}")
    if repository_parent == Path(repository_parent.anchor):
        raise RuntimeError("refusing to mask the filesystem root")
    if not site_packages.is_relative_to(repository_parent):
        raise RuntimeError("venv site-packages is outside the repository being masked")
    for name, path in (
        ("team source bundle", bundle),
        ("staged runtime", runtime_site_packages),
        ("empty directory", empty_dir),
        ("empty file", empty_file),
    ):
        if path.is_relative_to(repository_parent):
            raise RuntimeError(f"sandbox {name} would be hidden with the repository")

    _bind_read_only(root)
    _bind_read_only(bundle)
    _bind_read_only(site_packages, runtime_site_packages)
    hidden = [
        path
        for path in _sensitive_paths(root)
        if _hide_path(path, empty_dir=empty_dir, empty_file=empty_file)
    ]
    read_only_flag = getattr(os, "ST_RDONLY", 1)
    if not os.statvfs(root).f_flag & read_only_flag:
        raise RuntimeError("repository bind mount is not read-only")
    if not os.statvfs(bundle).f_flag & read_only_flag:
        raise RuntimeError("team source bundle bind mount is not read-only")
    if not os.statvfs(runtime_site_packages).f_flag & read_only_flag:
        raise RuntimeError("staged venv site-packages bind mount is not read-only")
    for path in hidden:
        if path.is_dir() and any(path.iterdir()):
            raise RuntimeError(f"sensitive directory was not hidden: {path}")
        if path.is_file() and path.stat().st_size:
            raise RuntimeError(f"sensitive file was not hidden: {path}")
    if not _hide_path(repository_parent, empty_dir=empty_dir, empty_file=empty_file):
        raise RuntimeError("repository parent disappeared before it could be masked")
    if any(repository_parent.iterdir()):
        raise RuntimeError("repository parent was not completely hidden")
    if not os.statvfs(repository_parent).f_flag & read_only_flag:
        raise RuntimeError("hidden repository parent is not read-only")
    _drop_mount_capabilities()


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _install_strategy_audit_policy(
    root: Path,
    repository_parent: Path,
    allowed_read_paths: Sequence[Path],
    *,
    repository_masked: bool,
) -> None:
    extra_denied = (repository_parent,) if repository_masked else ()
    denied_roots = tuple(
        path.resolve(strict=False) for path in (*_sensitive_paths(root), *extra_denied)
    )
    allowed_files = frozenset(path for path in allowed_read_paths if path.is_file())
    allowed_directories = tuple(path for path in allowed_read_paths if path.is_dir())

    def allowed_path(path: Path) -> bool:
        return path in allowed_files or any(
            path == directory or _is_relative_to(path, directory)
            for directory in allowed_directories
        )

    def denied_path(value: Any) -> bool:
        if not isinstance(value, (str, bytes, os.PathLike)):
            return False
        try:
            path = Path(os.fsdecode(value)).resolve(strict=False)
        except (OSError, TypeError, ValueError):
            return False
        return any(path == denied or _is_relative_to(path, denied) for denied in denied_roots)

    def prohibited_path(value: Any) -> bool:
        if not isinstance(value, (str, bytes, os.PathLike)):
            return False
        try:
            path = Path(os.fsdecode(value)).resolve(strict=False)
        except (OSError, TypeError, ValueError):
            return True
        return denied_path(path) or not allowed_path(path)

    def write_open(arguments: tuple[Any, ...]) -> bool:
        mode = arguments[1] if len(arguments) > 1 else None
        flags = arguments[2] if len(arguments) > 2 else 0
        if isinstance(mode, str) and any(token in mode for token in "wax+"):
            return True
        write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        return isinstance(flags, int) and bool(flags & write_flags)

    def audit(event: str, arguments: tuple[Any, ...]) -> None:
        if event.startswith("socket."):
            message = "network access is disabled in the strategy worker"
            _latch_sandbox_violation(message)
            raise StrategySandboxViolationError(message)
        if event in _PROCESS_AUDIT_EVENTS:
            message = "subprocess execution is disabled in the strategy worker"
            _latch_sandbox_violation(message)
            raise StrategySandboxViolationError(message)
        if event in {"open", "os.listdir", "os.scandir"} and arguments:
            if prohibited_path(arguments[0]) or (event == "open" and write_open(arguments)):
                message = "filesystem access is outside the strategy runtime allowlist"
                _latch_sandbox_violation(message)
                raise StrategySandboxViolationError(message)

    sys.addaudithook(audit)


def _remap_site_path(value: Any, source: Path, destination: Path) -> Any:
    if not isinstance(value, str):
        return value
    try:
        relative = Path(value).relative_to(source)
    except ValueError:
        return value
    return str(destination / relative)


def _configure_strategy_runtime(
    bundle: Path,
    source_site_packages: Path,
    runtime_site_packages: Path,
    repository_parent: Path,
    *,
    repository_masked: bool,
) -> None:
    """Detach imports from the soon-hidden checkout while preserving the staged venv."""
    for module in tuple(sys.modules.values()):
        if module is None:
            continue
        for attribute in ("__file__", "__cached__"):
            value = getattr(module, attribute, None)
            remapped = _remap_site_path(value, source_site_packages, runtime_site_packages)
            if remapped != value:
                setattr(module, attribute, remapped)
        package_path = getattr(module, "__path__", None)
        if package_path is not None:
            remapped_path = [
                _remap_site_path(value, source_site_packages, runtime_site_packages)
                for value in package_path
            ]
            if list(package_path) != remapped_path:
                module.__path__ = remapped_path
        spec = getattr(module, "__spec__", None)
        if spec is None:
            continue
        spec.origin = _remap_site_path(
            getattr(spec, "origin", None), source_site_packages, runtime_site_packages
        )
        locations = getattr(spec, "submodule_search_locations", None)
        if locations is not None:
            spec.submodule_search_locations = [
                _remap_site_path(value, source_site_packages, runtime_site_packages)
                for value in locations
            ]
        loader = getattr(spec, "loader", None)
        loader_path = getattr(loader, "path", None)
        remapped_loader_path = _remap_site_path(
            loader_path, source_site_packages, runtime_site_packages
        )
        if loader is not None and remapped_loader_path != loader_path:
            loader.path = remapped_loader_path

    retained: list[str] = []
    for value in sys.path:
        if not value:
            continue
        path = Path(value).resolve(strict=False)
        if (
            path.is_relative_to(repository_parent)
            or path.is_relative_to(bundle.parent)
            or "site-packages" in path.parts
        ):
            continue
        retained.append(str(path))
    sys.path[:] = list(dict.fromkeys([str(bundle), str(runtime_site_packages), *retained]))
    sys.path_importer_cache.clear()
    importlib.invalidate_caches()
    if repository_masked and any(
        Path(value).resolve(strict=False).is_relative_to(repository_parent) for value in sys.path
    ):
        raise RuntimeError("strategy import path still exposes the masked repository")


def _load_strategy(bundle: Path, entrypoint: str) -> Any:
    raw = Path(entrypoint)
    if raw.is_absolute() or ".." in raw.parts:
        raise ValueError("worker entrypoint must be a safe relative path")
    path = (bundle / raw).resolve()
    if not _is_relative_to(path, bundle.resolve()) or not path.is_file():
        raise ValueError("worker entrypoint is absent from the copied source bundle")
    module_name = f"_top40_strategy_{os.getpid()}"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import team entrypoint: {entrypoint}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    sys.path.insert(0, str(bundle))
    try:
        try:
            with contextlib.redirect_stdout(sys.stderr):
                spec.loader.exec_module(module)
                builder = getattr(module, "build_strategy", None)
                if not callable(builder):
                    raise TypeError("team entrypoint must define callable build_strategy()")
                strategy = builder()
            if strategy is None or not callable(getattr(strategy, "target_weights", None)):
                raise TypeError("build_strategy() must return an object with target_weights()")
            return strategy
        finally:
            # Audit-hook exceptions are catchable by Python strategy code.  A denied attempt is
            # nevertheless disqualifying, so re-raise the first violation after loading and
            # validating the returned strategy.
            _raise_latched_sandbox_violation()
    finally:
        try:
            sys.path.remove(str(bundle))
        except ValueError:
            pass


def _string_tuple(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise TypeError(f"{field} must be a JSON string list")
    if len(value) != len(set(value)):
        raise ValueError(f"{field} cannot contain duplicates")
    return tuple(value)


def _initialise(message: Mapping[str, Any], *, bundle: Path, entrypoint: str) -> _WorkerState:
    if message.get("type") != "init":
        raise ValueError("first worker message must be init")
    bar_columns = _string_tuple(message.get("bar_columns"), "bar_columns")
    raw_bar_dtypes = message.get("bar_dtypes")
    if not isinstance(raw_bar_dtypes, list) or any(
        not isinstance(item, str) for item in raw_bar_dtypes
    ):
        raise TypeError("bar_dtypes must be a JSON string list")
    bar_dtypes = tuple(raw_bar_dtypes)
    funding_columns = _string_tuple(message.get("funding_columns"), "funding_columns")
    raw_funding_dtypes = message.get("funding_dtypes")
    if not isinstance(raw_funding_dtypes, list) or any(
        not isinstance(item, str) for item in raw_funding_dtypes
    ):
        raise TypeError("funding_dtypes must be a JSON string list")
    funding_dtypes = tuple(raw_funding_dtypes)
    if len(bar_columns) != len(bar_dtypes) or len(funding_columns) != len(funding_dtypes):
        raise ValueError("worker schema columns and dtypes differ in length")
    bar_datetimes = frozenset(
        _string_tuple(message.get("bar_datetime_columns"), "bar_datetime_columns")
    )
    funding_datetimes = frozenset(
        _string_tuple(message.get("funding_datetime_columns"), "funding_datetime_columns")
    )
    if not bar_datetimes.issubset(bar_columns):
        raise ValueError("bar datetime columns are absent from bar_columns")
    if not funding_datetimes.issubset(funding_columns):
        raise ValueError("funding datetime columns are absent from funding_columns")
    interval_hours = int(message.get("interval_hours"))
    if interval_hours < 1:
        raise ValueError("interval_hours must be positive")
    seed = int(message.get("seed"))
    return _WorkerState(
        strategy=_load_strategy(bundle, entrypoint),
        seed=seed,
        interval=pd.Timedelta(hours=interval_hours),
        bar_columns=bar_columns,
        bar_dtypes=bar_dtypes,
        bar_datetime_columns=bar_datetimes,
        funding_columns=funding_columns,
        funding_dtypes=funding_dtypes,
        funding_datetime_columns=funding_datetimes,
    )


def _decode_row(row: Any, columns: Sequence[str], datetime_columns: frozenset[str]) -> list[Any]:
    if not isinstance(row, list) or len(row) != len(columns):
        raise ValueError("incremental row does not match the declared schema")
    decoded = list(row)
    for index, column in enumerate(columns):
        if column in datetime_columns:
            decoded[index] = pd.Timestamp(decoded[index])
            if decoded[index].tzinfo is None:
                decoded[index] = decoded[index].tz_localize("UTC")
            else:
                decoded[index] = decoded[index].tz_convert("UTC")
    return decoded


def _append_updates(
    destination: dict[str, _HistoryBuffer],
    updates: Any,
    *,
    eligible: frozenset[str],
    columns: tuple[str, ...],
    dtypes: tuple[str, ...],
    datetime_columns: frozenset[str],
    time_column: str,
    decision_time: pd.Timestamp,
    interval: pd.Timedelta | None,
) -> list[list[Any]]:
    if not isinstance(updates, dict):
        raise TypeError("incremental updates must be a JSON object")
    try:
        symbol_index = columns.index("symbol")
        time_index = columns.index(time_column)
    except ValueError as exc:
        raise ValueError("incremental schema requires symbol and event-time columns") from exc
    accepted: list[list[Any]] = []
    for symbol, raw_rows in updates.items():
        if not isinstance(symbol, str) or symbol not in eligible:
            raise ValueError("incremental updates may contain only currently eligible symbols")
        if not isinstance(raw_rows, list):
            raise TypeError("incremental symbol rows must be a JSON list")
        buffer = destination.setdefault(symbol, _HistoryBuffer(columns, dtypes, datetime_columns))
        decoded = [_decode_row(row, columns, datetime_columns) for row in raw_rows]
        previous = buffer.last_time
        for row in decoded:
            if row[symbol_index] != symbol:
                raise ValueError("incremental row symbol differs from its update key")
            timestamp = pd.Timestamp(row[time_index])
            if previous is not None and timestamp <= previous:
                raise ValueError("incremental symbol timestamps must be strictly append-only")
            if interval is None:
                if timestamp >= decision_time:
                    raise ValueError("worker received funding that was not strictly past")
            elif timestamp + interval > decision_time:
                raise ValueError("worker received a bar that was not closed")
            previous = timestamp
        buffer.append(decoded)
        if decoded:
            buffer.last_time = previous
            accepted.extend(decoded)
    return accepted


def _funding_sort_key(row: Sequence[Any], columns: tuple[str, ...]) -> tuple[Any, ...]:
    order = ("settlement_time", "funding_time", "symbol")
    return tuple(row[columns.index(column)] for column in order)


def _rebuild_funding_context(
    state: _WorkerState, eligible_tuple: tuple[str, ...]
) -> _HistoryBuffer:
    frames = [
        state.funding[symbol].frame()
        for symbol in eligible_tuple
        if symbol in state.funding and state.funding[symbol].length
    ]
    if frames:
        frame = (
            pd.concat(frames, ignore_index=True)
            .sort_values(["settlement_time", "funding_time", "symbol"])
            .reset_index(drop=True)
        )
    else:
        frame = _HistoryBuffer(
            state.funding_columns,
            state.funding_dtypes,
            state.funding_datetime_columns,
        ).frame()
    return _HistoryBuffer.from_frame(
        frame,
        columns=state.funding_columns,
        dtypes=state.funding_dtypes,
        datetime_columns=state.funding_datetime_columns,
    )


def _decision(state: _WorkerState, message: Mapping[str, Any]) -> dict[str, float] | None:
    if message.get("type") != "decision":
        raise ValueError("worker expected a decision message")
    decision_time = pd.Timestamp(message.get("decision_time"))
    if decision_time.tzinfo is None:
        decision_time = decision_time.tz_localize("UTC")
    else:
        decision_time = decision_time.tz_convert("UTC")
    if state.previous_decision is not None and decision_time <= state.previous_decision:
        raise ValueError("worker decision times must be strictly increasing")
    eligible_tuple = _string_tuple(message.get("eligible_symbols"), "eligible_symbols")
    eligible = frozenset(eligible_tuple)
    _append_updates(
        state.bars,
        message.get("bars"),
        eligible=eligible,
        columns=state.bar_columns,
        dtypes=state.bar_dtypes,
        datetime_columns=state.bar_datetime_columns,
        time_column="open_time",
        decision_time=decision_time,
        interval=state.interval,
    )
    funding_updates = _append_updates(
        state.funding,
        message.get("funding"),
        eligible=eligible,
        columns=state.funding_columns,
        dtypes=state.funding_dtypes,
        datetime_columns=state.funding_datetime_columns,
        time_column="funding_time",
        decision_time=decision_time,
        interval=None,
    )

    by_symbol: dict[str, pd.DataFrame] = {}
    for symbol in eligible_tuple:
        buffer = state.bars.get(symbol)
        if buffer is None or not buffer.length:
            raise ValueError("eligible symbol has no closed bar history")
        by_symbol[symbol] = buffer.frame()

    past_funding: pd.DataFrame | None = None
    if state.funding_eligible != eligible or state.funding_context is None:
        state.funding_context = _rebuild_funding_context(state, eligible_tuple)
        state.funding_eligible = eligible
        past_funding = state.funding_context.frame()
        if state.funding_context.length:
            state.funding_last_key = tuple(
                past_funding.iloc[-1][column]
                for column in ("settlement_time", "funding_time", "symbol")
            )
        else:
            state.funding_last_key = None
    elif funding_updates:
        funding_updates.sort(key=lambda row: _funding_sort_key(row, state.funding_columns))
        if (
            state.funding_last_key is not None
            and _funding_sort_key(funding_updates[0], state.funding_columns)
            < state.funding_last_key
        ):
            raise ValueError("stable-universe funding updates are not globally append-only")
        state.funding_context.append(funding_updates)
        state.funding_last_key = _funding_sort_key(funding_updates[-1], state.funding_columns)
    if past_funding is None:
        past_funding = state.funding_context.frame()
    context = DecisionContext(
        decision_time=decision_time,
        bars=by_symbol,
        funding=past_funding,
        auxiliary={},
        eligible_symbols=eligible_tuple,
    )
    try:
        with contextlib.redirect_stdout(sys.stderr):
            weights = state.strategy.target_weights(context, seed=state.seed)
        if weights is None:
            result = None
        else:
            if not isinstance(weights, Mapping):
                raise TypeError("target_weights() must return a finite weight mapping or None")
            result = {}
            for symbol, raw_weight in weights.items():
                if not isinstance(symbol, str) or symbol not in eligible:
                    raise ValueError("target_weights() returned a symbol outside the eligible set")
                if isinstance(raw_weight, bool):
                    raise TypeError("target weights must be numeric, not booleans")
                try:
                    weight = float(raw_weight)
                except (TypeError, ValueError) as exc:
                    raise TypeError("target weights must be numeric") from exc
                if not math.isfinite(weight):
                    raise ValueError("target_weights() returned a non-finite weight")
                result[symbol] = weight
    finally:
        # Do not let any team-controlled call, including custom Mapping iteration or numeric
        # conversion, catch a denied audit event and then submit apparently valid weights.
        _raise_latched_sandbox_violation()
    state.previous_decision = decision_time
    return result


def _read_message(stream: TextIO) -> Mapping[str, Any] | None:
    line = stream.readline()
    if not line:
        return None
    value = json.loads(line)
    if not isinstance(value, dict):
        raise TypeError("worker protocol messages must be JSON objects")
    return value


def _send(stream: TextIO, payload: Mapping[str, Any]) -> None:
    stream.write(json.dumps(payload, allow_nan=False, separators=(",", ":")) + "\n")
    stream.flush()


def _serve(protocol_out: TextIO, *, bundle: Path, entrypoint: str) -> int:
    state: _WorkerState | None = None
    while True:
        try:
            message = _read_message(sys.stdin)
            if message is None:
                return 0
            if message.get("type") == "shutdown":
                _send(protocol_out, {"type": "bye"})
                return 0
            if state is None:
                state = _initialise(message, bundle=bundle, entrypoint=entrypoint)
                _send(protocol_out, {"type": "ready"})
                continue
            weights = _decision(state, message)
            _send(protocol_out, {"type": "weights", "weights": weights})
        except BaseException as exc:
            _send(
                protocol_out,
                {
                    "type": "error",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
            )
            return 1


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--root", required=True)
    parser.add_argument("--repository-parent", required=True)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--site-packages", required=True)
    parser.add_argument("--runtime-site-packages", required=True)
    parser.add_argument("--entrypoint", required=True)
    parser.add_argument("--empty-dir", required=True)
    parser.add_argument("--empty-file", required=True)
    parser.add_argument("--test-bypass-namespace", action="store_true", help=argparse.SUPPRESS)
    return parser


def main() -> int:
    args = _parser().parse_args()
    root = Path(args.root).resolve()
    repository_parent = Path(args.repository_parent).resolve()
    bundle = Path(args.bundle).resolve()
    site_packages = Path(args.site_packages).resolve()
    runtime_site_packages = Path(args.runtime_site_packages).resolve()
    empty_dir = Path(args.empty_dir).resolve()
    empty_file = Path(args.empty_file).resolve()

    # Preserve the original stdout pipe exclusively for the protocol.  Team writes to fd 1 are
    # redirected to stderr, so ordinary print/os.write calls cannot corrupt protocol framing.
    protocol_fd = os.dup(sys.stdout.fileno())
    protocol_out = os.fdopen(protocol_fd, "w", buffering=1, encoding="utf-8")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    try:
        if not args.test_bypass_namespace:
            _prepare_mount_namespace(
                root,
                repository_parent,
                bundle,
                site_packages,
                runtime_site_packages,
                empty_dir,
                empty_file,
            )
            strategy_site_packages = runtime_site_packages
        else:
            strategy_site_packages = site_packages
        _configure_strategy_runtime(
            bundle,
            site_packages,
            strategy_site_packages,
            repository_parent,
            repository_masked=not args.test_bypass_namespace,
        )
        os.chdir(bundle)
        _apply_worker_resource_limits()
        allowed_read_paths = _install_landlock(bundle, strategy_site_packages)
        _install_seccomp_denylist()
        _install_strategy_audit_policy(
            root,
            repository_parent,
            allowed_read_paths,
            repository_masked=not args.test_bypass_namespace,
        )
        return _serve(protocol_out, bundle=bundle, entrypoint=args.entrypoint)
    except BaseException as exc:
        _send(
            protocol_out,
            {"type": "error", "error_type": "StrategySandboxError", "message": str(exc)},
        )
        return 1
    finally:
        protocol_out.close()


if __name__ == "__main__":
    raise SystemExit(main())
