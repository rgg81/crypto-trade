"""Integrity custody for acquisition, sealed, private, cache, and report roots."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path

# Roots the organizer is meant to write into while the tournament runs, and whose invariant is
# therefore append-only rather than frozen. "private" collects transcript audits, adjudications,
# falsifier evidence, dispositions and -- during observation -- one evidence file per point.
# Freezing it made a receipt that must fail as soon as the process it protects actually runs, which
# is worse than useless: it trains the operator to expect the failure and wave it through. What
# genuinely must never happen there is an existing record changing or disappearing, and that is
# what is checked instead.
APPEND_ONLY_ROOTS = frozenset({"private", "reports"})


def _canonical(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _inventory(root: Path) -> list[dict[str, object]]:
    if not root.exists() or root.is_symlink():
        raise ValueError(f"quarantine root is missing or linked: {root}")
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"quarantine refuses symbolic links: {path}")
        if not path.is_file():
            continue
        stat = path.stat()
        entries.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size": stat.st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return entries


def create_receipt(
    destination: str | Path,
    *,
    roots: Mapping[str, str | Path],
    research_roots: Sequence[str | Path] = (),
) -> Mapping[str, object]:
    """Hash every quarantined byte and prove none sits below a team-visible root."""
    path = Path(destination)
    if path.exists():
        raise FileExistsError("quarantine receipt already exists")
    required = {"acquisition", "sealed", "private", "caches", "reports"}
    if set(roots) != required:
        raise ValueError(f"quarantine must cover exactly {sorted(required)}")
    visible = [Path(value).resolve() for value in research_roots]
    inventories: dict[str, object] = {}
    resolved_roots: dict[str, str] = {}
    for name, raw in roots.items():
        root = Path(raw).resolve()
        if any(root.is_relative_to(team) or team.is_relative_to(root) for team in visible):
            raise ValueError(f"quarantine root overlaps a research root: {name}")
        resolved_roots[name] = str(root)
        inventories[name] = _inventory(root)
    body = {
        "schema_version": 1,
        "namespace": "cup50v2",
        "roots": resolved_roots,
        "inventories": inventories,
    }
    receipt = {**body, "receipt_sha256": hashlib.sha256(_canonical(body)).hexdigest()}
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical(receipt))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return receipt


def verify_receipt(path: str | Path) -> Mapping[str, object]:
    receipt = json.loads(Path(path).read_text())
    digest = receipt.pop("receipt_sha256", None)
    if digest != hashlib.sha256(_canonical(receipt)).hexdigest():
        raise ValueError("quarantine receipt digest mismatch")
    for name, raw in receipt["roots"].items():
        current = _inventory(Path(raw))
        recorded = receipt["inventories"][name]
        if name not in APPEND_ONLY_ROOTS:
            if current != recorded:
                raise ValueError(f"quarantined root drifted: {name}")
            continue
        now = {entry["path"]: entry["sha256"] for entry in current}
        was = {entry["path"]: entry["sha256"] for entry in recorded}
        removed = sorted(set(was) - set(now))
        if removed:
            raise ValueError(f"append-only root lost records: {name}: {removed[:5]}")
        changed = sorted(path for path in was if path in now and was[path] != now[path])
        if changed:
            raise ValueError(f"append-only root rewrote records: {name}: {changed[:5]}")
    return {**receipt, "receipt_sha256": digest}
