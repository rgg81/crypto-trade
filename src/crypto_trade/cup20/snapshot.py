"""Physically separated IS and sealed snapshots.

Blindness is enforced by absence: the IS snapshot on disk contains no row at or after the IS
cutoff, so no team code path can read a sealed row even if it tries.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.data import sha256_manifest

# Canonical snapshot schemas, matching the acquisition pipeline:
#   bars              open_time, symbol, open, high, low, close, volume, close_time,
#                     quote_volume, trade_count, taker_buy_volume, taker_buy_quote_volume
#   funding           funding_time, symbol, funding_rate, mark_price, mark_time,
#                     settlement_time, funding_interval_hours
#   mark_prices       mark_time, symbol, mark_price
#   membership        reconstitution_time, symbol, liquidity_rank, trailing_quote_volume
#   contract_metadata symbol, contract_type, quote_asset, margin_asset, is_crypto,
#                     onboard_date, delivery_date, underlying_type, metadata_source
_TIME_COLUMN = {
    "bars": "open_time",
    "funding": "funding_time",
    "mark_prices": "mark_time",
    "membership": "reconstitution_time",
}
_DATASETS = ("bars", "funding", "mark_prices", "membership", "contract_metadata")


@dataclasses.dataclass(frozen=True, slots=True)
class SnapshotPaths:
    root: Path
    bars: Path
    funding: Path
    mark_prices: Path
    membership: Path
    contract_metadata: Path
    manifest: Path


@dataclasses.dataclass(frozen=True, slots=True)
class Snapshot:
    bars: pd.DataFrame
    funding: pd.DataFrame
    mark_prices: pd.DataFrame
    membership: pd.DataFrame
    contract_metadata: pd.DataFrame
    manifest_sha256: str


def resolve_is_start(membership: pd.DataFrame, *, target_size: int = 20) -> pd.Timestamp:
    """First reconstitution boundary whose membership reaches ``target_size``."""
    counts = membership.groupby("reconstitution_time").size().sort_index()
    reached = counts[counts >= target_size]
    if reached.empty:
        raise ValueError(f"membership never reaches {target_size} constituents")
    return pd.Timestamp(reached.index[0]).tz_convert("UTC")


def write_split_snapshots(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    mark_prices: pd.DataFrame,
    membership: pd.DataFrame,
    contract_metadata: pd.DataFrame,
    *,
    is_root: str | Path,
    sealed_root: str | Path,
    is_end: pd.Timestamp,
    sealed_end: pd.Timestamp,
) -> tuple[SnapshotPaths, SnapshotPaths]:
    """Write the IS snapshot (strictly before ``is_end``) and the sealed snapshot."""
    frames = {
        "bars": bars,
        "funding": funding,
        "mark_prices": mark_prices,
        "membership": membership,
        "contract_metadata": contract_metadata,
    }
    is_frames = {name: _slice(name, frame, None, is_end) for name, frame in frames.items()}
    sealed_frames = {
        name: _slice(name, frame, is_end, sealed_end) for name, frame in frames.items()
    }
    return (
        _write(is_frames, Path(is_root), window=("", is_end)),
        _write(sealed_frames, Path(sealed_root), window=(is_end, sealed_end)),
    )


def load_snapshot(root: str | Path) -> Snapshot:
    """Load a snapshot and verify its manifest digest."""
    root_path = Path(root)
    manifest = json.loads((root_path / "manifest.json").read_text())
    files = [root_path / f"{name}.parquet" for name in _DATASETS]
    digest, _ = sha256_manifest(files, root=root_path)
    if digest != manifest["manifest_sha256"]:
        raise ValueError(f"snapshot at {root_path} does not match its manifest digest")
    loaded = {name: pd.read_parquet(root_path / f"{name}.parquet") for name in _DATASETS}
    return Snapshot(manifest_sha256=digest, **loaded)


def _slice(
    name: str, frame: pd.DataFrame, start: pd.Timestamp | None, end: pd.Timestamp
) -> pd.DataFrame:
    column = _TIME_COLUMN.get(name)
    if column is None:
        # Timeless datasets (contract metadata) are sorted for byte-stable manifests.
        return frame.sort_values("symbol").reset_index(drop=True)
    times = pd.to_datetime(frame[column], utc=True)
    mask = times < end
    if start is not None:
        mask &= times >= start
    result = frame.loc[mask].copy()
    result[column] = times.loc[mask]
    return result.sort_values([column, "symbol"]).reset_index(drop=True)


def _write(
    frames: dict[str, pd.DataFrame], root: Path, *, window: tuple[object, pd.Timestamp]
) -> SnapshotPaths:
    root.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_parquet(root / f"{name}.parquet", index=False)
    files = [root / f"{name}.parquet" for name in _DATASETS]
    digest, entries = sha256_manifest(files, root=root)
    manifest = {
        "schema_version": 1,
        "manifest_sha256": digest,
        "window_start": str(window[0]),
        "window_end": str(window[1]),
        "files": entries,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return SnapshotPaths(
        root=root,
        bars=root / "bars.parquet",
        funding=root / "funding.parquet",
        mark_prices=root / "mark_prices.parquet",
        membership=root / "membership.parquet",
        contract_metadata=root / "contract_metadata.parquet",
        manifest=root / "manifest.json",
    )
