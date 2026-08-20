"""Adopt an earlier edition's acquisition, by proving it byte for byte.

The charter permits exactly one kind of reuse: checksum-verified raw Binance archive bytes. A price
history is not a result -- it carries no candidate, parameter, ranking or conclusion -- and
re-downloading five million mark rows to obtain identical bytes would risk the acquisition defects
that cost a prior edition two invalidated fields, in exchange for nothing.

What makes this admissible is that it is *verified* rather than trusted: every file is re-hashed
against the source manifest before it is copied, the copy is re-hashed after, and the receipt
records both, so the adoption can be audited later without the source being present.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from pathlib import Path

REUSE_NAMESPACE = "cup50v2-acquisition-reuse"
CHUNK = 1 << 20


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(CHUNK):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical(payload: object) -> bytes:
    return (json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)).encode()


def reuse_acquisition(
    source: str | Path, destination: str | Path, *, receipt: str | Path
) -> Mapping[str, object]:
    """Verify every file against the source manifest, copy, and re-verify the copy."""
    origin = Path(source).resolve()
    target = Path(destination)
    if target.exists() and any(target.iterdir()):
        raise FileExistsError("acquisition destination must be new and empty")
    manifest_path = origin / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    entries = manifest.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("source acquisition manifest lists no files")

    verified: list[dict[str, object]] = []
    for entry in entries:
        name = str(entry["path"])
        source_file = origin / name
        if not source_file.is_file() or source_file.is_symlink():
            raise ValueError(f"source acquisition is missing {name}")
        observed = _sha256(source_file)
        if observed != str(entry["sha256"]):
            raise ValueError(f"source acquisition file does not match its manifest: {name}")
        verified.append({"path": name, "sha256": observed, "size": source_file.stat().st_size})

    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=target.parent))
    try:
        for entry in verified:
            name = str(entry["path"])
            copied = staging / name
            copied.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(origin / name, copied)
            if _sha256(copied) != entry["sha256"]:
                raise ValueError(f"copied acquisition file does not match its source: {name}")
        shutil.copyfile(manifest_path, staging / "manifest.json")
        staging.chmod(0o755)
        os.replace(staging, target)
    finally:
        if staging.exists():
            shutil.rmtree(staging)

    body = {
        "schema_version": 1,
        "namespace": REUSE_NAMESPACE,
        "source_root": str(origin),
        "source_manifest_sha256": hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
        "source_namespace": manifest.get("namespace"),
        "destination_root": str(Path(destination)),
        "files": sorted(verified, key=lambda item: str(item["path"])),
        "basis": (
            "Raw Binance archive bytes only. No candidate source, parameter, ranking, result or "
            "conclusion from the source edition is adopted, and none is present in these files."
        ),
    }
    record = {**body, "receipt_sha256": hashlib.sha256(_canonical(body)).hexdigest()}
    receipt_path = Path(receipt)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    return record


def verify_reuse_receipt(receipt: str | Path, root: str | Path) -> Mapping[str, object]:
    """Re-inventory the adopted acquisition against its receipt."""
    record = json.loads(Path(receipt).read_text())
    stored = record.pop("receipt_sha256", None)
    if stored != hashlib.sha256(_canonical(record)).hexdigest():
        raise ValueError("acquisition reuse receipt digest mismatch")
    base = Path(root)
    for entry in record["files"]:
        path = base / str(entry["path"])
        if not path.is_file() or _sha256(path) != entry["sha256"]:
            raise ValueError(f"adopted acquisition drifted: {entry['path']}")
    return {**record, "receipt_sha256": stored}
