"""Frozen IS snapshot — build, SHA-256 manifest, tamper verification (crypto multi-file).

Per union symbol the snapshot holds up to three files, ALL truncated at the single hard
boundary ``ts <= IS_END_MS`` (nothing stamped 2024-07-01 or later ships, period):
    data_is/<SYM>/8h.csv       — all 11 Binance kline columns   (open_time <= IS_END_MS)
    data_is/<SYM>/funding.csv  — funding_time,funding_rate      (funding_time <= IS_END_MS)
    data_is/<SYM>/oi.csv       — 7-column OI/ratio metrics      (open_time <= IS_END_MS)
plus the organizer universe artifacts:
    data_is/_universe/eligibility.csv    — bool candle×symbol weekly top-40 mask (IS rows,
                                           IS-union columns; FULL-POOL derived — see universe.py)
    data_is/_universe/universe_meta.json — pool definition + build provenance

The manifest records a SHA-256 per file; every team-facing load re-hashes all files first
(``verify_manifest``), so no holdout byte can reach a team without tripping either the hash
check or the loader's boundary check.
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

from portfolio_tournament import constants as tc  # noqa: E402
from portfolio_tournament import universe as tu  # noqa: E402


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


def _write_truncated(src_csv: Path, dest_csv: Path, ts_col: str) -> int:
    """Copy a CSV keeping rows with ts_col <= IS_END_MS; returns rows written (0 = skipped)."""
    df = pd.read_csv(src_csv)
    df = df[df[ts_col] <= tc.IS_END_MS]
    df = df.drop_duplicates(subset=ts_col, keep="last").sort_values(ts_col)
    if df.empty:
        return 0
    dest_csv.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(dest_csv, index=False, float_format="%.17g")  # full float64 precision
    return len(df)


def build_is_snapshot(
    src_data_dir: Path,
    dest: Path = tc.SNAPSHOT_DIR,
    manifest_path: Path = tc.MANIFEST_PATH,
    *,
    source_commit: str = "",
) -> dict:
    """Build the frozen IS snapshot from the full data store; returns the written manifest.

    Recomputes the full-pool weekly top-40 mask (universe.build) and ships klines + funding
    + OI for every IS-union symbol, plus the eligibility mask itself. Funding-coverage
    enforcement lives in cli.data_report (run it BEFORE building; build refuses on missing
    funding files unless allow_missing_funding).
    """
    src = Path(src_data_dir)
    summary = tu.build(src, tc.BUILD_DIR)  # refresh _build artifacts (mask, unions, spans)
    union_is = json.loads((tc.BUILD_DIR / "union_is.json").read_text())
    mask = pd.read_csv(tc.BUILD_DIR / "eligibility_full.csv", index_col="open_time")

    if dest.exists():
        shutil.rmtree(dest)
    files: dict[str, str] = {}
    missing_funding: list[str] = []
    for sym in union_is:
        n = _write_truncated(src / sym / "8h.csv", dest / sym / "8h.csv", "open_time")
        if n == 0:
            print(f"  ! {sym}: no kline bars inside IS window — skipped")
            continue
        files[f"{sym}/8h.csv"] = sha256_file(dest / sym / "8h.csv")
        fsrc = src / "funding_rates" / f"{sym}.csv"
        if fsrc.exists():
            if _write_truncated(fsrc, dest / sym / "funding.csv", "funding_time"):
                files[f"{sym}/funding.csv"] = sha256_file(dest / sym / "funding.csv")
            else:
                missing_funding.append(sym)
        else:
            missing_funding.append(sym)
        osrc = src / "open_interest" / sym / "8h.csv"
        if osrc.exists() and _write_truncated(osrc, dest / sym / "oi.csv", "open_time"):
            files[f"{sym}/oi.csv"] = sha256_file(dest / sym / "oi.csv")

    if missing_funding:
        print(f"  ! {len(missing_funding)} symbols lack IS funding: {missing_funding[:10]}…")

    # Eligibility mask: IS rows, IS-union columns, int 0/1 (byte-stable CSV).
    elig = mask.loc[mask.index <= tc.IS_END_MS, [s for s in union_is if f"{s}/8h.csv" in files]]
    udir = dest / "_universe"
    udir.mkdir(parents=True, exist_ok=True)
    elig.to_csv(udir / "eligibility.csv")
    files["_universe/eligibility.csv"] = sha256_file(udir / "eligibility.csv")

    meta = {
        "pool_filter": "USDT-quoted, ascii, ex-STABLE regex, ex-NON_COIN_PERPS",
        "top_n": tc.TOP_N,
        "dvol_win": tc.DVOL_WIN,
        "dvol_min_periods": tc.DVOL_MIN_PERIODS,
        "refresh_weekday": tc.REFRESH_WEEKDAY,
        "full_pool_size": summary["pool"],
        "union_is": summary["union_is"],
        "missing_funding": sorted(missing_funding),
        "grid_step_ms": tc.STEP_MS,
    }
    (udir / "universe_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    files["_universe/universe_meta.json"] = sha256_file(udir / "universe_meta.json")

    manifest = {
        "schema": 1,
        "name": "crypto-cup-01",
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


def manifest_symbols(manifest: dict) -> list[str]:
    """Tradable symbols listed in a manifest (dirs with an 8h.csv, `_universe` excluded)."""
    return sorted(
        {Path(rel).parts[0] for rel in manifest["files"] if rel.endswith("/8h.csv")} - {"_universe"}
    )


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
