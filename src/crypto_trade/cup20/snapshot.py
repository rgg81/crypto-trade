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
    side: ``onboard_date``, ``delivery_date``, and (once a ``delivery_date`` is censored)
    ``metadata_source`` / ``underlying_type`` are themselves future universe composition, the same
    leak class as ``membership.reconstitution_time``, just carried by a different dataset.
    ``_censor_contract_metadata_for_is`` scrubs all of it before the IS write; the sealed side is
    left untouched.
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


def _dominant_value(values: pd.Series, *, label: str) -> object:
    """The single most common value in ``values`` -- derived from the data, never hardcoded, so
    normalising a censored row keeps working unmodified if the acquisition pipeline's own
    conventions ever change.

    Used to normalise a censored row's non-date columns to whatever an ORDINARY, still-listed
    contract shows, so a censored row carries no residual, reconstructible trace of its true
    future status in any column -- not just ``delivery_date``. Fails loudly rather than guessing
    on an empty series, a null value, or a tie for the mode: a wrong or arbitrary guess here would
    ship a value that itself might distinguish a censored row from an ordinary one, which is
    exactly the failure this function exists to prevent.
    """
    if values.empty:
        raise ValueError(f"cannot derive a dominant {label} value: no rows to derive it from")
    if values.isna().any():
        raise ValueError(f"contract_metadata {label} contains null values")
    mode = values.mode()
    if len(mode) != 1:
        raise ValueError(
            f"contract_metadata {label} has no single unambiguous mode across {len(values)} rows "
            "-- cannot derive a dominant value"
        )
    return mode.iloc[0]


def _perpetual_delivery_sentinel(delivery_date: pd.Series) -> pd.Timestamp:
    """The ``delivery_date`` value meaning "no scheduled delivery is known" -- derived from the
    data itself (Binance's own real convention is ``2100-12-25T08:00:00Z`` / epoch ms
    ``4133404800000``, but this never hardcodes it; see ``_dominant_value``).
    """
    return pd.Timestamp(
        _dominant_value(pd.to_datetime(delivery_date, utc=True), label="delivery_date")
    )


# The two contract_metadata columns known to be stamped with an acquisition-pipeline-specific
# sentinel for exactly the symbols absent from live exchangeInfo at data-build time -- which is to
# say, for symbols that have already delisted -- verified directly against
# crypto_trade/tournament/snapshot.py's `_contract_metadata` (the acquisition function that
# actually sets every field in this schema): archive-inferred rows get
# underlying_type="ARCHIVE_INFERRED_COIN" and metadata_source="archive_inference", where a
# genuinely still-listed contract shows the exchange's own `underlyingType` (validated elsewhere
# to always be "COIN" for this pure-crypto universe -- see
# crypto_trade/tournament/pure_crypto_universe_v6.py's `current_contract_violations`) and
# metadata_source="current_exchangeInfo". Combined with a delivery_date censored to the perpetual
# sentinel, either field alone is an exact, unambiguous reconstruction of "this contract delists
# after the IS cutoff" -- found the hard way, as a real false-assurance defect, during fix-round 3.
#
# contract_type, quote_asset, margin_asset, and is_crypto are NOT in this list: all four are
# hardcoded to the identical literal ("PERPETUAL" / "USDT" / "USDT" / True) on the archive-inferred
# branch of `_contract_metadata`, and separately validated by `current_contract_violations` /
# `_contract_metadata` itself to be forced to those same values on the current-exchangeInfo branch
# too (a row violating either is rejected before it ever reaches this universe) -- so none of the
# four can carry this correlation. Checked directly against both functions' source, not assumed.
_ARCHIVE_STATUS_COLUMNS = ("metadata_source", "underlying_type")


def _censor_contract_metadata_for_is(
    contract_metadata: pd.DataFrame, is_end: pd.Timestamp
) -> pd.DataFrame:
    """Scrub future universe composition out of ``contract_metadata`` before it enters the IS
    snapshot.

    Three independent leaks, all future universe composition -- the same class this module's own
    docstring calls out for the time-keyed datasets, just carried by columns rather than rows:

      - A row whose ``onboard_date`` is at or after ``is_end`` was not listed yet as of the IS
        cutoff. Its very presence -- let alone its ``onboard_date`` -- tells a team a symbol
        exists before it does. Dropped entirely.
      - A row whose ``delivery_date`` is at or after ``is_end`` carries a future delisting date no
        IS-era observer could know. Replaced with the perpetual sentinel (see
        ``_perpetual_delivery_sentinel``) -- the value the data itself already uses for
        genuinely-perpetual contracts.
      - The same row's ``metadata_source`` / ``underlying_type`` (see ``_ARCHIVE_STATUS_COLUMNS``)
        are normalised to whatever an ordinary, still-listed contract shows (``_dominant_value``,
        derived from every OTHER row -- never from the row being censored itself). A censored
        ``delivery_date`` alone is not enough: these two columns independently reveal that a
        symbol has already delisted by acquisition build time, regardless of when, which is
        exactly as severe a leak as the date itself once combined with the sentinel.

    A no-op when ``onboard_date`` / ``delivery_date`` are absent (older or synthetic fixtures
    without them): nothing to censor. ``metadata_source`` / ``underlying_type`` are normalised only
    if present.
    """
    frame = contract_metadata
    if "onboard_date" in frame.columns:
        onboard = pd.to_datetime(frame["onboard_date"], utc=True)
        frame = frame.loc[onboard < is_end].reset_index(drop=True)
    if frame.empty or "delivery_date" not in frame.columns:
        return frame
    delivery = pd.to_datetime(frame["delivery_date"], utc=True)
    sentinel = _perpetual_delivery_sentinel(frame["delivery_date"])
    # A row needs censoring only if its delivery_date is a GENUINE post-cutoff date, not the
    # sentinel itself: the sentinel already sits at or after is_end for any is_end this tournament
    # will ever use (it means "no delivery date known", conventionally far in the future), so a
    # naive `delivery >= is_end` mask would also flag every already-safe, genuinely-perpetual row
    # -- shrinking the "ordinary" reference population derived below, in the worst case to empty
    # (found the hard way, as a real crash, while verifying this fix).
    censor_mask = (delivery >= is_end) & (delivery != sentinel)
    if not censor_mask.any():
        return frame
    ordinary = frame.loc[~censor_mask]
    frame = frame.copy()
    frame.loc[censor_mask, "delivery_date"] = sentinel
    for column in _ARCHIVE_STATUS_COLUMNS:
        if column not in frame.columns:
            continue
        dominant = _dominant_value(ordinary[column], label=column)
        frame.loc[censor_mask, column] = dominant
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
