"""Clean-room validation and network-disabled Docker command construction."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path

from crypto_trade.cup50.snapshot import (
    load_snapshot,
    verify_semantic_coverage,
    verify_team_visible_snapshot,
)

FORBIDDEN_PARTS = frozenset(
    {
        ".git",
        "private",
        "sealed",
        "reports-cup20",
        "reports-top40",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
    }
)
FORBIDDEN_NAMES = frozenset({"activation-freeze.json", "selection-freeze.json"})
FORBIDDEN_CACHE_SUFFIXES = frozenset(
    {".arrow", ".csv", ".feather", ".joblib", ".parquet", ".pickle", ".pkl"}
)
FORBIDDEN_IMPORT_ROOTS = frozenset(
    {
        "builtins",
        "ctypes",
        "httpx",
        "importlib",
        "multiprocessing",
        "os",
        "pathlib",
        "requests",
        "shutil",
        "socket",
        "subprocess",
        "sys",
        "urllib",
    }
)
FORBIDDEN_CALLS = frozenset(
    {
        "__import__",
        "compile",
        "eval",
        "exec",
        "open",
        "read_csv",
        "read_feather",
        "read_json",
        "read_parquet",
        "read_pickle",
        "read_table",
        "to_csv",
        "to_feather",
        "to_json",
        "to_parquet",
        "to_pickle",
    }
)


def _source_violations(path: Path, relative: Path) -> list[str]:
    if path.suffix != ".py":
        return []
    try:
        tree = ast.parse(path.read_text(), filename=str(path))
    except (OSError, SyntaxError, UnicodeError):
        return [f"invalid-python:{relative.as_posix()}"]
    violations: list[str] = []
    for node in ast.walk(tree):
        imports: list[str] = []
        if isinstance(node, ast.Import):
            imports = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports = [node.module]
        for name in imports:
            if name.split(".", 1)[0] in FORBIDDEN_IMPORT_ROOTS:
                violations.append(f"forbidden-import:{relative.as_posix()}:{name}")
        if isinstance(node, ast.Call):
            called: str | None = None
            if isinstance(node.func, ast.Name):
                called = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called = node.func.attr
            if called in FORBIDDEN_CALLS:
                violations.append(f"forbidden-call:{relative.as_posix()}:{called}")
    return violations


def export_protocol_bundle(source: str | Path, destination: str | Path) -> dict[str, object]:
    """Create a minimal, immutable strategy-interface mount without organizer code."""
    protocol = Path(source).resolve()
    target = Path(destination).resolve()
    if not protocol.is_file() or protocol.is_symlink() or protocol.name != "protocol.py":
        raise ValueError("protocol export source must be the real CUP-50 protocol.py")
    if target.exists():
        raise FileExistsError("protocol export destination already exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        package = temporary / "crypto_trade" / "cup50"
        package.mkdir(parents=True)
        (temporary / "crypto_trade" / "__init__.py").write_text("")
        (package / "__init__.py").write_text("")
        exported = package / "protocol.py"
        shutil.copyfile(protocol, exported)
        digest = hashlib.sha256(exported.read_bytes()).hexdigest()
        body: dict[str, object] = {
            "schema_version": 1,
            "namespace": "cup50-protocol-export",
            "files": {"crypto_trade/cup50/protocol.py": digest},
        }
        body_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        manifest = {**body, "manifest_sha256": hashlib.sha256(body_bytes).hexdigest()}
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
        )
        temporary.chmod(0o755)
        os.replace(temporary, target)
        return manifest
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def export_evaluator_bundle(source: str | Path, destination: str | Path) -> dict[str, object]:
    """Export only CUP-50 Python modules for the isolated organizer evaluator."""
    source_root = Path(source).resolve()
    target = Path(destination).resolve()
    if not source_root.is_dir() or source_root.name != "cup50":
        raise ValueError("evaluator export source must be the CUP-50 package directory")
    if target.exists():
        raise FileExistsError("evaluator export destination already exists")
    modules = sorted(source_root.glob("*.py"))
    if not modules or any(path.is_symlink() for path in modules):
        raise ValueError("CUP-50 evaluator source is missing or linked")
    for path in modules:
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            imported: list[str] = []
            if isinstance(node, ast.Import):
                imported = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported = [node.module]
            outside = [
                name
                for name in imported
                if name.startswith("crypto_trade.")
                and not name.startswith("crypto_trade.cup50")
            ]
            if outside:
                raise ValueError(f"evaluator imports outside CUP-50: {path.name}: {outside}")

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        package = temporary / "crypto_trade" / "cup50"
        package.mkdir(parents=True)
        (temporary / "crypto_trade" / "__init__.py").write_text("")
        entries: dict[str, str] = {}
        for source_path in modules:
            exported = package / source_path.name
            shutil.copyfile(source_path, exported)
            relative = exported.relative_to(temporary).as_posix()
            entries[relative] = hashlib.sha256(exported.read_bytes()).hexdigest()
        body: dict[str, object] = {
            "schema_version": 1,
            "namespace": "cup50-evaluator-export",
            "files": dict(sorted(entries.items())),
        }
        body_bytes = json.dumps(body, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        manifest = {**body, "manifest_sha256": hashlib.sha256(body_bytes).hexdigest()}
        (temporary / "manifest.json").write_text(
            json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n"
        )
        temporary.chmod(0o755)
        os.replace(temporary, target)
        return manifest
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def scan_research_root(root: str | Path) -> tuple[str, ...]:
    base = Path(root).resolve()
    violations: list[str] = []
    for path in base.rglob("*"):
        relative = path.relative_to(base)
        lowered = {part.lower() for part in relative.parts}
        if lowered & FORBIDDEN_PARTS or path.name in FORBIDDEN_NAMES:
            violations.append(relative.as_posix())
        if any(part.lower().startswith(("cup20", "top40")) for part in relative.parts):
            violations.append(relative.as_posix())
        if path.is_file() and (
            path.suffix.lower() in FORBIDDEN_CACHE_SUFFIXES or path.stat().st_size > 2_000_000
        ):
            violations.append(relative.as_posix())
        if path.is_file():
            violations.extend(_source_violations(path, relative))
        if path.is_symlink():
            resolved = path.resolve()
            if not resolved.is_relative_to(base):
                violations.append(f"external-symlink:{relative.as_posix()}")
    return tuple(sorted(set(violations)))


def require_isolation_available(*, docker_binary: str = "docker") -> str:
    executable = shutil.which(docker_binary)
    if executable is None:
        raise RuntimeError("CUP-50 activation requires Docker isolation")
    result = subprocess.run(
        [executable, "info", "--format", "{{.ServerVersion}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    if result.returncode != 0 or not result.stdout.strip():
        raise RuntimeError("CUP-50 activation requires a functioning Docker daemon")
    return result.stdout.strip()


def require_image_digest(
    image: str, expected_sha256: str, *, docker_binary: str = "docker"
) -> str:
    """Resolve a local image tag and require the activation-supplied content ID."""
    expected = expected_sha256.removeprefix("sha256:")
    if len(expected) != 64 or any(character not in "0123456789abcdef" for character in expected):
        raise ValueError("expected sandbox image digest is not a SHA-256")
    result = subprocess.run(
        [docker_binary, "image", "inspect", image, "--format", "{{.Id}}"],
        check=False,
        capture_output=True,
        text=True,
        timeout=20,
    )
    observed = result.stdout.strip().removeprefix("sha256:")
    if result.returncode != 0 or observed != expected:
        raise RuntimeError("sandbox image tag does not resolve to the activation digest")
    return f"sha256:{observed}"


def evaluator_container_command(
    *,
    image: str,
    research_root: str | Path,
    protocol_root: str | Path,
    is_snapshot: str | Path,
    output_root: str | Path,
    command: list[str],
    execution_snapshot: str | Path | None = None,
    read_only_files: Mapping[str | Path, str] | None = None,
) -> list[str]:
    roots = [Path(value).resolve() for value in (research_root, protocol_root, is_snapshot)]
    output = Path(output_root).resolve()
    if scan_research_root(roots[0]):
        raise ValueError("research root contains forbidden prior/private artifacts")
    verify_team_visible_snapshot(roots[2])
    execution_mount: list[str] = []
    if execution_snapshot is not None:
        execution = Path(execution_snapshot).resolve()
        verify_semantic_coverage(load_snapshot(execution))
        execution_mount = [
            f"--mount=type=bind,src={execution},dst=/workspace/execution,readonly"
        ]
    file_mounts: list[str] = []
    for source, destination in (read_only_files or {}).items():
        path = Path(source).resolve()
        target = Path(destination)
        if not path.is_file() or path.is_symlink():
            raise ValueError(f"read-only sandbox artifact is missing or linked: {source}")
        if (
            not target.is_absolute()
            or target.parent != Path("/workspace")
            or target.name in {"team", "protocol", "is", "execution", "output"}
        ):
            raise ValueError(f"invalid read-only sandbox destination: {destination}")
        file_mounts.append(
            f"--mount=type=bind,src={path},dst={target.as_posix()},readonly"
        )
    output.mkdir(parents=True, exist_ok=True)
    return [
        "docker",
        "run",
        "--rm",
        f"--user={os.getuid()}:{os.getgid()}",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--env=CUP50_SANDBOX=network-none-read-only",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=256m",
        f"--mount=type=bind,src={roots[0]},dst=/workspace/team,readonly",
        f"--mount=type=bind,src={roots[1]},dst=/workspace/protocol,readonly",
        f"--mount=type=bind,src={roots[2]},dst=/workspace/is,readonly",
        *execution_mount,
        *file_mounts,
        f"--mount=type=bind,src={output},dst=/workspace/output",
        "--workdir=/workspace/team",
        image,
        *command,
    ]


def observer_container_command(
    *,
    image: str,
    source_bundle: str | Path,
    protocol_root: str | Path,
    is_snapshot: str | Path,
    sealed_snapshot: str | Path,
    lifecycle_root: str | Path,
    command: list[str],
) -> list[str]:
    """Container contract for private observation; only lifecycle staging is writable."""
    source, protocol, research, sealed, lifecycle = (
        Path(value).resolve()
        for value in (
            source_bundle,
            protocol_root,
            is_snapshot,
            sealed_snapshot,
            lifecycle_root,
        )
    )
    lifecycle.mkdir(parents=True, exist_ok=True)
    return [
        "docker",
        "run",
        "--rm",
        f"--user={os.getuid()}:{os.getgid()}",
        "--network=none",
        "--read-only",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--env=CUP50_SANDBOX=network-none-read-only",
        "--tmpfs=/tmp:rw,noexec,nosuid,size=256m",
        f"--mount=type=bind,src={source},dst=/workspace/team,readonly",
        f"--mount=type=bind,src={protocol},dst=/workspace/protocol,readonly",
        f"--mount=type=bind,src={research},dst=/workspace/is,readonly",
        f"--mount=type=bind,src={sealed},dst=/workspace/sealed,readonly",
        f"--mount=type=bind,src={lifecycle},dst=/workspace/lifecycle",
        "--workdir=/workspace/team",
        image,
        *command,
    ]


def require_read_only(path: str | Path) -> None:
    mode = os.stat(path).st_mode
    if mode & 0o222:
        raise ValueError(f"path is not read-only: {path}")
