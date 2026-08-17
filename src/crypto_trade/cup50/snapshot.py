"""Physically separate CUP-50 research and sealed snapshots."""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path

import pandas as pd

from crypto_trade.cup50.config import IS_START, OOS_END, OOS_START

DATASETS = ("bars", "funding", "mark_prices", "membership", "contract_metadata")
TIME_COLUMNS = {
    "bars": "open_time",
    "funding": "settlement_time",
    "mark_prices": "mark_time",
    "membership": "reconstitution_time",
}
KEYS = {
    "bars": ("open_time", "symbol"),
    "funding": ("funding_time", "symbol"),
    "mark_prices": ("mark_time", "symbol"),
    "membership": ("reconstitution_time", "symbol"),
    "contract_metadata": ("symbol",),
}


@dataclasses.dataclass(frozen=True, slots=True)
class Snapshot:
    bars: pd.DataFrame
    funding: pd.DataFrame
    mark_prices: pd.DataFrame
    membership: pd.DataFrame
    contract_metadata: pd.DataFrame
    manifest_sha256: str
    window_start: pd.Timestamp
    window_end: pd.Timestamp
    sealed: bool


@dataclasses.dataclass(frozen=True, slots=True)
class SnapshotPaths:
    root: Path
    manifest: Path
    files: Mapping[str, Path]


@dataclasses.dataclass(frozen=True, slots=True)
class TeamSnapshotPaths:
    root: Path
    manifest: Path
    files: Mapping[str, Path]


def _utc(value: object, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware UTC")
    return timestamp.tz_convert("UTC")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical_json(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _validate_unique(name: str, frame: pd.DataFrame) -> None:
    key = list(KEYS[name])
    missing = set(key) - set(frame)
    if missing:
        raise ValueError(f"{name} missing key columns: {sorted(missing)}")
    if frame.duplicated(key).any():
        raise ValueError(f"{name} contains duplicate {key} keys")


def _slice_time(
    name: str,
    frame: pd.DataFrame,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    sealed: bool,
) -> pd.DataFrame:
    column = TIME_COLUMNS.get(name)
    if column is None:
        result = frame.copy()
    else:
        times = pd.to_datetime(frame[column], utc=True)
        # Bars and membership are left-boundary facts and remain half-open.  Funding and marks at
        # an endpoint settle/mark the interval that just ended and therefore belong to the earlier
        # partition.  At OOS_START that means the boundary settlement is in IS, not the first OOS
        # interval.  The sealed split consequently opens those datasets strictly after start.
        if name in {"bars", "membership"}:
            mask = (times >= start) & (times < end)
        elif sealed:
            mask = (times > start) & (times <= end)
        else:
            mask = (times >= start) & (times <= end)
        result = frame.loc[mask].copy()
        result[column] = times.loc[mask]
    _validate_unique(name, result)
    return result.sort_values(list(KEYS[name]), ignore_index=True)


def censor_metadata_for_research(metadata: pd.DataFrame, cutoff: pd.Timestamp) -> pd.DataFrame:
    """Remove every contract fact not knowable strictly before the research cutoff."""
    edge = _utc(cutoff, "cutoff")
    _validate_unique("contract_metadata", metadata)
    result = metadata.copy()
    if "onboard_date" in result:
        onboard = pd.to_datetime(result["onboard_date"], utc=True, errors="coerce")
        result = result.loc[onboard.notna() & onboard.lt(edge)].copy()
        result["onboard_date"] = onboard.loc[result.index]
    if "delivery_date" in result:
        delivery = pd.to_datetime(result["delivery_date"], utc=True, errors="coerce")
        # Unknown and future delivery dates are indistinguishable to a research participant.
        visible = delivery.where(delivery.lt(edge), pd.NaT)
        result["delivery_date"] = visible
    for column in (
        "metadata_source",
        "archive_last_seen",
        "current_status",
        "future_status",
        "listing_episode_end",
    ):
        if column in result:
            result = result.drop(columns=column)
    return result.sort_values("symbol", ignore_index=True)


def _write_snapshot(
    frames: Mapping[str, pd.DataFrame],
    root: Path,
    *,
    start: pd.Timestamp,
    end: pd.Timestamp,
    sealed: bool,
) -> SnapshotPaths:
    root.mkdir(parents=True, exist_ok=True)
    files: dict[str, Path] = {}
    entries: dict[str, dict[str, object]] = {}
    for name in DATASETS:
        path = root / f"{name}.parquet"
        frames[name].to_parquet(path, index=False)
        files[name] = path
        entries[name] = {
            "path": path.name,
            "sha256": _sha256(path),
            "rows": len(frames[name]),
        }
    body = {
        "schema_version": 2,
        "namespace": "cup50",
        "sealed": sealed,
        "window": {
            "start": start.isoformat().replace("+00:00", "Z"),
            "end": end.isoformat().replace("+00:00", "Z"),
            "bars": "start-inclusive/end-exclusive by open_time",
            "terminal_marks_and_funding": "end-inclusive",
        },
        "files": entries,
    }
    body_bytes = _canonical_json(body)
    manifest = {**body, "manifest_sha256": hashlib.sha256(body_bytes).hexdigest()}
    manifest_path = root / "manifest.json"
    _atomic_write(manifest_path, _canonical_json(manifest))
    return SnapshotPaths(root=root, manifest=manifest_path, files=files)


def write_split_snapshots(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    mark_prices: pd.DataFrame,
    membership: pd.DataFrame,
    contract_metadata: pd.DataFrame,
    *,
    is_root: str | Path,
    sealed_root: str | Path,
    is_start: pd.Timestamp = IS_START,
    oos_start: pd.Timestamp = OOS_START,
    oos_end: pd.Timestamp = OOS_END,
) -> tuple[SnapshotPaths, SnapshotPaths]:
    """Write research and sealed bytes with no sealed-only roster or metadata facts in IS."""
    first = _utc(is_start, "is_start")
    split = _utc(oos_start, "oos_start")
    end = _utc(oos_end, "oos_end")
    if not first < split < end:
        raise ValueError("snapshot bounds must satisfy is_start < oos_start < oos_end")
    normalized_funding = funding.copy()
    normalized_funding["funding_time"] = pd.to_datetime(
        normalized_funding["funding_time"], utc=True
    )
    if "settlement_time" not in normalized_funding:
        normalized_funding["settlement_time"] = normalized_funding["funding_time"].dt.floor("h")
    else:
        normalized_funding["settlement_time"] = pd.to_datetime(
            normalized_funding["settlement_time"], utc=True
        )
    source = {
        "bars": bars,
        "funding": normalized_funding,
        "mark_prices": mark_prices,
        "membership": membership,
        "contract_metadata": contract_metadata,
    }
    research = {
        name: _slice_time(name, frame, start=first, end=split, sealed=False)
        for name, frame in source.items()
    }
    research["contract_metadata"] = censor_metadata_for_research(contract_metadata, split)

    is_symbols = set(research["membership"]["symbol"].astype(str))
    for name in ("bars", "funding", "mark_prices"):
        research[name] = (
            research[name]
            .loc[research[name]["symbol"].astype(str).isin(is_symbols)]
            .reset_index(drop=True)
        )
    research["contract_metadata"] = (
        research["contract_metadata"]
        .loc[research["contract_metadata"]["symbol"].astype(str).isin(is_symbols)]
        .reset_index(drop=True)
    )
    sealed_frames = {
        name: _slice_time(name, frame, start=split, end=end, sealed=True)
        for name, frame in source.items()
    }
    return (
        _write_snapshot(research, Path(is_root), start=first, end=split, sealed=False),
        _write_snapshot(sealed_frames, Path(sealed_root), start=split, end=end, sealed=True),
    )


def write_team_visible_snapshot(research: Snapshot, *, root: str | Path) -> TeamSnapshotPaths:
    """Export the IS facts a team may inspect, excluding execution opens and marks."""
    if research.sealed:
        raise ValueError("a sealed snapshot can never be exported to a team")
    destination = Path(root)
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("team-visible snapshot destination must be new and empty")
    destination.mkdir(parents=True, exist_ok=True)
    bars = research.bars.drop(columns=["open"], errors="ignore")
    funding = research.funding.drop(
        columns=["mark_price", "mark_time", "settlement_time"], errors="ignore"
    )
    frames = {
        "bars": bars,
        "funding": funding,
        "membership": research.membership,
        "contract_metadata": research.contract_metadata,
    }
    files: dict[str, Path] = {}
    entries: dict[str, dict[str, object]] = {}
    for name, frame in frames.items():
        path = destination / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        files[name] = path
        entries[name] = {"path": path.name, "sha256": _sha256(path), "rows": len(frame)}
    body = {
        "schema_version": 2,
        "namespace": "cup50-team-visible-is",
        "source_is_manifest_sha256": research.manifest_sha256,
        "window": {
            "start": research.window_start.isoformat().replace("+00:00", "Z"),
            "end": research.window_end.isoformat().replace("+00:00", "Z"),
        },
        "files": entries,
    }
    manifest = {**body, "manifest_sha256": hashlib.sha256(_canonical_json(body)).hexdigest()}
    manifest_path = destination / "manifest.json"
    _atomic_write(manifest_path, _canonical_json(manifest))
    return TeamSnapshotPaths(destination, manifest_path, files)


def verify_team_visible_snapshot(root: str | Path) -> Mapping[str, object]:
    base = Path(root)
    manifest = json.loads((base / "manifest.json").read_text())
    if manifest.get("namespace") != "cup50-team-visible-is":
        raise ValueError("not a CUP-50 team-visible IS snapshot")
    digest = manifest.pop("manifest_sha256", None)
    if digest != hashlib.sha256(_canonical_json(manifest)).hexdigest():
        raise ValueError("team-visible snapshot manifest digest mismatch")
    if set(manifest["files"]) != {"bars", "funding", "membership", "contract_metadata"}:
        raise ValueError("team-visible snapshot exposes unexpected datasets")
    for name, entry in manifest["files"].items():
        path = base / entry["path"]
        if _sha256(path) != entry["sha256"]:
            raise ValueError(f"team-visible snapshot drifted: {name}")
    bars = pd.read_parquet(base / manifest["files"]["bars"]["path"])
    funding = pd.read_parquet(base / manifest["files"]["funding"]["path"])
    if "open" in bars or "mark_price" in funding or (base / "mark_prices.parquet").exists():
        raise ValueError("team-visible snapshot contains organizer execution data")
    return {**manifest, "manifest_sha256": digest}


def load_snapshot(root: str | Path) -> Snapshot:
    root_path = Path(root)
    manifest_path = root_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if manifest.get("namespace") != "cup50" or manifest.get("schema_version") != 2:
        raise ValueError("not a CUP-50 snapshot manifest")
    stored_digest = manifest.pop("manifest_sha256", None)
    if stored_digest != hashlib.sha256(_canonical_json(manifest)).hexdigest():
        raise ValueError("snapshot manifest body digest mismatch")
    loaded: dict[str, pd.DataFrame] = {}
    for name in DATASETS:
        entry = manifest["files"][name]
        path = root_path / entry["path"]
        if _sha256(path) != entry["sha256"]:
            raise ValueError(f"snapshot dataset checksum mismatch: {name}")
        loaded[name] = pd.read_parquet(path)
        if len(loaded[name]) != int(entry["rows"]):
            raise ValueError(f"snapshot dataset row-count mismatch: {name}")
    return Snapshot(
        **loaded,
        manifest_sha256=str(stored_digest),
        window_start=pd.Timestamp(manifest["window"]["start"]),
        window_end=pd.Timestamp(manifest["window"]["end"]),
        sealed=bool(manifest["sealed"]),
    )


def stitch_snapshots(research: Snapshot, sealed: Snapshot) -> Snapshot:
    """Organizer-only continuous replay view; never exported to a team root."""
    if research.sealed or not sealed.sealed:
        raise ValueError("stitch_snapshots expects (research, sealed)")
    if research.window_end != sealed.window_start:
        raise ValueError("snapshot partitions are not adjacent")
    frames: dict[str, pd.DataFrame] = {}
    for name in DATASETS:
        combined = pd.concat([getattr(research, name), getattr(sealed, name)], ignore_index=True)
        # Metadata legitimately repeats across physical snapshots.  Time-series endpoint semantics
        # are disjoint by construction and duplicates there are corruption.
        if name == "contract_metadata":
            combined = combined.drop_duplicates("symbol", keep="last")
        _validate_unique(name, combined)
        frames[name] = combined.sort_values(list(KEYS[name]), ignore_index=True)
    digest = hashlib.sha256(
        f"{research.manifest_sha256}:{sealed.manifest_sha256}".encode()
    ).hexdigest()
    return Snapshot(
        **frames,
        manifest_sha256=digest,
        window_start=research.window_start,
        window_end=sealed.window_end,
        sealed=True,
    )


def verify_semantic_coverage(snapshot: Snapshot) -> None:
    """Check the bounds the evaluator means, not merely parquet filename partitions."""
    bars = pd.to_datetime(snapshot.bars["open_time"], utc=True)
    if (bars < snapshot.window_start).any() or (bars >= snapshot.window_end).any():
        raise ValueError("bar open_time lies outside the half-open snapshot window")
    for name, column in (("funding", "settlement_time"), ("mark_prices", "mark_time")):
        frame = getattr(snapshot, name)
        times = pd.to_datetime(frame[column], utc=True)
        lower = times > snapshot.window_start if snapshot.sealed else times >= snapshot.window_start
        if (~lower).any() or (times > snapshot.window_end).any():
            raise ValueError(f"{name} lies outside its semantic endpoint bounds")
    if snapshot.window_end == OOS_END:
        for name, column in (("funding", "settlement_time"), ("mark_prices", "mark_time")):
            times = pd.to_datetime(getattr(snapshot, name)[column], utc=True)
            if OOS_END not in set(times):
                raise ValueError(f"{name} lacks the required terminal {OOS_END} boundary")
