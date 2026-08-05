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
    """Write the IS snapshot (strictly before ``is_end``) and the sealed snapshot.

    ``contract_metadata`` is timeless (see ``_TIME_COLUMN``) and ``_slice`` ships it whole into
    every split -- correct for the sealed side (organiser-only, needs the truth), wrong for the IS
    side: ``onboard_date`` and ``delivery_date`` are themselves future universe composition, the
    same leak class as ``membership.reconstitution_time``, just carried by a different dataset.
    ``_censor_contract_metadata_for_is`` scrubs both before the IS write; the sealed side is left
    untouched.
    """
    frames = {
        "bars": bars,
        "funding": funding,
        "mark_prices": mark_prices,
        "membership": membership,
        "contract_metadata": contract_metadata,
    }
    is_frames = {name: _slice(name, frame, None, is_end) for name, frame in frames.items()}
    is_frames["contract_metadata"] = _censor_contract_metadata_for_is(
        is_frames["contract_metadata"], is_end
    )
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
        _require_unique_key(name, frame, ["symbol"])
        return frame.sort_values("symbol").reset_index(drop=True)
    times = pd.to_datetime(frame[column], utc=True)
    mask = times < end
    if start is not None:
        mask &= times >= start
    result = frame.loc[mask].copy()
    result[column] = times.loc[mask]
    _require_unique_key(name, result, [column, "symbol"])
    return result.sort_values([column, "symbol"]).reset_index(drop=True)


def _require_unique_key(name: str, frame: pd.DataFrame, key_columns: list[str]) -> None:
    """Fail loudly rather than silently reorder: the sort key must be a total order.

    A duplicate key means the byte order of the written parquet -- and therefore the manifest
    digest -- would depend on the caller's incoming row order, which breaks determinism. A
    duplicate row here means the upstream acquisition is wrong; picking a tiebreaker would hide
    that instead of surfacing it.
    """
    duplicated = frame.duplicated(subset=key_columns, keep=False)
    if duplicated.any():
        example = tuple(frame.loc[duplicated, key_columns].iloc[0])
        raise ValueError(
            f"{name} has duplicate rows for key {key_columns} (e.g. {example}); "
            "sort order would not be deterministic"
        )


def _perpetual_delivery_sentinel(contract_metadata: pd.DataFrame) -> pd.Timestamp:
    """The ``delivery_date`` value meaning "no scheduled delivery is known" -- derived from the
    data itself as its single most common value, not hardcoded: the overwhelming majority of any
    real contract universe is perpetual and shares one placeholder date (Binance's own convention
    is ``2100-12-25T08:00:00Z`` / epoch ms ``4133404800000``). Deriving it here means this keeps
    working unmodified if the exchange's own placeholder ever changes, rather than silently
    drifting out of sync with a hardcoded literal.

    Fails loudly rather than guessing: this value stands in for every post-cutoff
    ``delivery_date`` in the IS snapshot, so an absent, null, or ambiguous derivation must raise --
    never fail open into skipping censorship or picking an arbitrary candidate.
    """
    if "delivery_date" not in contract_metadata.columns or contract_metadata.empty:
        raise ValueError(
            "cannot derive a perpetual delivery sentinel: contract_metadata is empty or has no "
            "delivery_date column"
        )
    values = pd.to_datetime(contract_metadata["delivery_date"], utc=True)
    if values.isna().any():
        raise ValueError("contract_metadata delivery_date contains null values")
    mode = values.mode()
    if len(mode) != 1:
        raise ValueError(
            "contract_metadata delivery_date has no single unambiguous mode across "
            f"{len(contract_metadata)} rows -- cannot derive a perpetual sentinel"
        )
    return pd.Timestamp(mode.iloc[0])


def _censor_contract_metadata_for_is(
    contract_metadata: pd.DataFrame, is_end: pd.Timestamp
) -> pd.DataFrame:
    """Scrub future universe composition out of ``contract_metadata`` before it enters the IS
    snapshot.

    Two independent leaks, both future universe composition -- the same class this module's own
    docstring calls out for the time-keyed datasets, just carried by columns rather than rows:

      - A row whose ``onboard_date`` is at or after ``is_end`` was not listed yet as of the IS
        cutoff. Its very presence -- let alone its ``onboard_date`` -- tells a team a symbol
        exists before it does. Dropped entirely.
      - A row whose ``delivery_date`` is at or after ``is_end`` carries a future delisting date no
        IS-era observer could know. Replaced with the perpetual sentinel (see
        ``_perpetual_delivery_sentinel``) -- the value the data itself already uses for
        genuinely-perpetual contracts, so a censored row is indistinguishable from one that was
        never going to delist at all.

    A no-op when ``onboard_date`` / ``delivery_date`` are absent (older or synthetic fixtures
    without them): nothing to censor.
    """
    frame = contract_metadata
    if "onboard_date" in frame.columns:
        onboard = pd.to_datetime(frame["onboard_date"], utc=True)
        frame = frame.loc[onboard < is_end].reset_index(drop=True)
    if frame.empty or "delivery_date" not in frame.columns:
        return frame
    sentinel = _perpetual_delivery_sentinel(frame)
    delivery = pd.to_datetime(frame["delivery_date"], utc=True)
    frame = frame.copy()
    frame.loc[delivery >= is_end, "delivery_date"] = sentinel
    return frame


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
