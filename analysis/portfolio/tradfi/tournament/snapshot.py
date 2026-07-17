"""Frozen IS snapshot — build, SHA-256 manifest, tamper verification.

``build_is_snapshot`` copies each name's daily CSV keeping ONLY rows with
``open_time <= IS_END_MS`` (2024-06-30). The manifest records a SHA-256 per file; every
team-facing load re-hashes all files first (``verify_manifest``), so no holdout byte can
reach a team without tripping either the hash check or the loader's boundary check.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

_HERE = Path(__file__).resolve().parent
if str(_HERE.parent) not in sys.path:
    sys.path.insert(0, str(_HERE.parent))

from tournament import constants as tc  # noqa: E402
from universe_tradfi import SECTOR_MAP  # noqa: E402


class SnapshotTamperedError(RuntimeError):
    """Snapshot bytes do not match the frozen manifest."""


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _files_digest(files: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()


def build_is_snapshot(
    src_data_dir: Path,
    dest: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    symbols: list[str] | None = None,
    *,
    source_commit: str = "",
) -> dict:
    """Build the frozen IS snapshot from a full data dir; returns the written manifest.

    Names whose source CSV is missing or has ZERO rows inside the IS window (post-IS IPOs)
    are skipped with a note — the tournament universe is exactly the manifest's tradable set.
    """
    src = Path(src_data_dir)
    if symbols is None:
        symbols = sorted(SECTOR_MAP) + [tc.VIX_SYM]
    if dest.exists():
        shutil.rmtree(dest)
    files: dict[str, str] = {}
    for sym in symbols:
        p = src / sym / "1d.csv"
        if not p.exists():
            print(f"  ! {sym}: missing {p} — skipped (not in tournament universe)")
            continue
        df = pd.read_csv(p)
        df = df[df["open_time"] <= tc.IS_END_MS]
        if df.empty:
            print(f"  ! {sym}: no bars inside IS window — skipped (post-IS listing)")
            continue
        out = dest / sym / "1d.csv"
        out.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False, float_format="%.17g")  # full float64 precision
        files[f"{sym}/1d.csv"] = sha256_file(out)
    manifest = {
        "schema": 1,
        "name": "tradfi-cup-01",
        "is_end_ms": tc.IS_END_MS,
        "is_end": str(tc.TRN_IS_END.date()),
        "built_at_utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "source_commit": source_commit,
        "n_files": len(files),
        "files": files,
        "files_sha256": _files_digest(files),
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def read_manifest(manifest_path: Path = tc.MANIFEST_PATH) -> dict:
    return json.loads(Path(manifest_path).read_text())


def verify_manifest(dest: Path = tc.SNAPSHOT_DIR, manifest_path: Path = tc.MANIFEST_PATH) -> dict:
    """Re-hash every snapshot file against the manifest; any mismatch, missing file, extra
    file, or edited file-list digest raises ``SnapshotTamperedError``. Returns the manifest."""
    manifest = read_manifest(manifest_path)
    files: dict[str, str] = manifest["files"]
    if _files_digest(files) != manifest["files_sha256"]:
        raise SnapshotTamperedError("manifest file-list digest mismatch (manifest edited)")
    on_disk = {str(p.relative_to(dest)) for p in Path(dest).rglob("*") if p.is_file()}
    listed = set(files)
    if on_disk - listed:
        raise SnapshotTamperedError(f"extra files in snapshot: {sorted(on_disk - listed)[:5]}")
    if listed - on_disk:
        raise SnapshotTamperedError(f"missing snapshot files: {sorted(listed - on_disk)[:5]}")
    for rel, want in files.items():
        got = sha256_file(dest / rel)
        if got != want:
            raise SnapshotTamperedError(f"{rel}: sha256 mismatch (got {got[:12]}…)")
    return manifest
