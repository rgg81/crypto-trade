"""One-time CUP-50 activation binding."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import tempfile
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path


def _canonical(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def artifact_manifest(paths: Iterable[str | Path], *, root: str | Path) -> Mapping[str, str]:
    base = Path(root).resolve()
    result: dict[str, str] = {}
    for raw in paths:
        candidate = Path(raw)
        path = (candidate if candidate.is_absolute() else base / candidate).resolve()
        if not path.is_file() or path.is_symlink() or not path.is_relative_to(base):
            raise ValueError(f"activation artifact is missing, linked, or outside root: {raw}")
        result[path.relative_to(base).as_posix()] = sha256_file(path)
    return dict(sorted(result.items()))


def transitive_evaluator_paths(
    entries: Sequence[str | Path], *, repository_root: str | Path
) -> tuple[Path, ...]:
    """Resolve local ``crypto_trade`` imports so activation binds the complete code path."""
    root = Path(repository_root).resolve()
    source_root = root / "src"
    queue = [
        (Path(entry) if Path(entry).is_absolute() else root / Path(entry)).resolve()
        for entry in entries
    ]
    visited: set[Path] = set()
    while queue:
        path = queue.pop()
        if path in visited:
            continue
        if not path.is_file() or not path.is_relative_to(root):
            raise ValueError(f"evaluator path is missing or outside repository: {path}")
        visited.add(path)
        if path.suffix != ".py":
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules.add(node.module)
                modules.update(
                    f"{node.module}.{alias.name}" for alias in node.names if alias.name != "*"
                )
        for module in modules:
            if not module.startswith("crypto_trade"):
                continue
            relative = Path(*module.split("."))
            candidates = (source_root / f"{relative}.py", source_root / relative / "__init__.py")
            local = next((candidate for candidate in candidates if candidate.is_file()), None)
            if local is not None and local not in visited:
                queue.append(local)
    return tuple(sorted(visited))


def build_activation_record(
    destination: str | Path,
    *,
    repository_root: str | Path,
    artifacts: Sequence[str | Path],
    evaluator_entries: Sequence[str | Path],
    git_commit: str,
    git_clean: bool,
    sandbox_image: str,
    sandbox_image_digest: str,
    focused_test_transcript: str | Path,
    isolation_verified: bool,
) -> Mapping[str, object]:
    """Create the activation freeze once; all material policy/data/code facts are bound."""
    target = Path(destination)
    if target.exists():
        raise FileExistsError(f"CUP-50 is already activated: {target}")
    if not git_clean or len(git_commit) < 7:
        raise ValueError("activation requires a named clean Git commit")
    if not isolation_verified:
        raise ValueError("activation requires verified network-disabled container isolation")
    digest_value = sandbox_image_digest.rsplit("@sha256:", maxsplit=1)[-1]
    if len(digest_value) != 64 or any(
        character not in "0123456789abcdef" for character in digest_value
    ):
        raise ValueError("sandbox image must be content-addressed")
    root = Path(repository_root).resolve()
    transitive = transitive_evaluator_paths(evaluator_entries, repository_root=root)
    all_paths = [*map(Path, artifacts), *transitive, Path(focused_test_transcript)]
    manifest = artifact_manifest(all_paths, root=root)
    body: dict[str, object] = {
        "schema_version": 1,
        "namespace": "cup50",
        "git_commit": git_commit,
        "git_clean": True,
        "sandbox_image": sandbox_image,
        "sandbox_image_digest": sandbox_image_digest,
        "isolation_verified": True,
        "artifacts": manifest,
        "transitive_evaluator_paths": [path.relative_to(root).as_posix() for path in transitive],
    }
    record = {**body, "activation_sha256": hashlib.sha256(_canonical(body)).hexdigest()}
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(record))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return record


def verify_activation(path: str | Path, *, repository_root: str | Path) -> Mapping[str, object]:
    record = json.loads(Path(path).read_text())
    digest = record.pop("activation_sha256", None)
    if digest != hashlib.sha256(_canonical(record)).hexdigest():
        raise ValueError("activation record digest mismatch")
    root = Path(repository_root).resolve()
    for relative, expected in record["artifacts"].items():
        if sha256_file(root / relative) != expected:
            raise ValueError(f"activated artifact drifted: {relative}")
    return {**record, "activation_sha256": digest}
