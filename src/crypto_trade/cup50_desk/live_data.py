"""Public-only, append-invariant cache generations for the CUP-50 paper desk.

Wire parsing and snapshot schemas are deliberately reused from the already verified CUP-20 desk;
both tournaments consume the same Binance USD-M 8-hour bars, hourly marks and native funding
events. CUP-50 adds immutable generations and resolves its own dynamic Top-50 membership before
fetching the narrower execution panel.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.cup20_desk.live_data import (
    BARS,
    CONTRACT_METADATA,
    FUNDING,
    KLINE_LIMIT,
    MARK_PRICES,
    PublicMarketDataClient,
    _fetch_bars,
    _fetch_contract_metadata,
    _fetch_funding,
    _fetch_hourly_marks,
    _publish_boundary_marks,
    append_frame,
    cache_manifest,
    empty_frame,
    verify_cache_manifest,
)
from crypto_trade.cup50.config import OOS_END
from crypto_trade.cup50.paper import cache_generation

INTERVAL = pd.Timedelta(hours=8)
FUNDING_EDGE = pd.Timedelta(seconds=1)
MARK_EDGE = pd.Timedelta(hours=1)
CURRENT_FILENAME = "CURRENT"
GENERATIONS_DIRNAME = "generations"
DIAGNOSTICS_FILENAME = "diagnostics.json"
MANIFEST_FILENAME = "cache-manifest.json"
PERPETUAL_DELIVERY_SENTINEL = pd.Timestamp(4_133_404_800_000, unit="ms", tz="UTC")

MembershipResolver = Callable[
    [Path, pd.Timestamp], tuple[pd.DataFrame, tuple[str, ...], tuple[str, ...]]
]


class CacheGenerationError(RuntimeError):
    """The current cache pointer or generation chain is invalid."""


def _utc(value: object) -> pd.Timestamp:
    stamp = pd.Timestamp(value)
    if stamp.tzinfo is None:
        raise ValueError("paper cache timestamps must be timezone-aware UTC")
    return stamp.tz_convert("UTC")


def _canonical(payload: object) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode()


def _read_manifest(generation: Path) -> Mapping[str, Any]:
    manifest = json.loads((generation / MANIFEST_FILENAME).read_text(encoding="utf-8"))
    return verify_cache_manifest(generation, manifest)


def _generation_file_bindings(generation: Path) -> list[dict[str, object]]:
    bindings: list[dict[str, object]] = []
    for path in sorted(generation.glob("*.parquet")):
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        bindings.append(
            {"path": path.name, "size": path.stat().st_size, "sha256": digest.hexdigest()}
        )
    return bindings


def _verify_generation_name(generation: Path, diagnostics: Mapping[str, Any]) -> None:
    bindings = _generation_file_bindings(generation)
    if diagnostics.get("data_files_sha256") != hashlib.sha256(_canonical(bindings)).hexdigest():
        raise CacheGenerationError("cache generation data-file binding drifted")
    body = {
        key: value
        for key, value in diagnostics.items()
        if key not in {"data_files_sha256", "generation_sha256"}
    }
    observed = hashlib.sha256(_canonical({**body, "files": bindings})).hexdigest()
    if diagnostics.get("generation_sha256") != observed or generation.name != observed:
        raise CacheGenerationError("cache generation digest/name mismatch")


def current_generation(cache_root: str | Path) -> Path | None:
    root = Path(cache_root).resolve()
    pointer = root / CURRENT_FILENAME
    if not pointer.is_file():
        return None
    relative = pointer.read_text(encoding="utf-8").strip()
    expected_prefix = f"{GENERATIONS_DIRNAME}/"
    if not relative.startswith(expected_prefix) or ".." in Path(relative).parts:
        raise CacheGenerationError(f"unsafe cache generation pointer: {relative!r}")
    generation = (root / relative).resolve()
    if not generation.is_relative_to(root) or not generation.is_dir():
        raise CacheGenerationError(f"current cache generation is missing: {relative}")
    _read_manifest(generation)
    diagnostics = json.loads((generation / DIAGNOSTICS_FILENAME).read_text())
    _verify_generation_name(generation, diagnostics)
    return generation


def load_cached_frame(generation: Path | None, name: str) -> pd.DataFrame:
    if generation is None:
        return empty_frame(name)
    path = generation / f"{name}.parquet"
    return pd.read_parquet(path) if path.is_file() else empty_frame(name)


def _candidate_symbols(payload: Mapping[str, Any]) -> tuple[str, ...]:
    symbols = payload.get("symbols")
    if not isinstance(symbols, list):
        raise ValueError("exchangeInfo has no symbols array")
    names = {
        str(item["symbol"])
        for item in symbols
        if isinstance(item, Mapping)
        and item.get("symbol")
        and item.get("contractType") == "PERPETUAL"
        and item.get("quoteAsset") == "USDT"
        and item.get("marginAsset") == "USDT"
        and item.get("underlyingType") == "COIN"
        # PENDING_TRADING contracts are not executable and Binance rejects their kline endpoint
        # with -1122. They also cannot possess the required 180 complete prior days.
        and item.get("status") == "TRADING"
    }
    if not names:
        raise ValueError("exchangeInfo exposes no eligible USD-M candidates")
    return tuple(sorted(names))


def _copy_previous(previous: Path | None, staging: Path) -> None:
    if previous is None:
        return
    for name in (BARS, FUNDING, MARK_PRICES, CONTRACT_METADATA):
        source = previous / f"{name}.parquet"
        if source.is_file():
            shutil.copy2(source, staging / source.name)


def _append(staging: Path, name: str, frame: pd.DataFrame) -> None:
    append_frame(staging / f"{name}.parquet", frame, name=name)


def _defer_announced_delivery_dates(
    staging: Path, incoming: pd.DataFrame, *, observed_at: object
) -> tuple[pd.DataFrame, tuple[dict[str, str], ...]]:
    """Keep a live perpetual's recorded sentinel while auditing a scheduled delivery.

    Binance can announce a future delivery while a USD-M perpetual is still ``TRADING`` and
    remains in ``exchangeInfo``.  That changes ``deliveryDate`` from Binance's perpetual sentinel
    to the announced timestamp without firing the existing ``current_exchangeInfo`` ->
    ``archive_inference`` delisting transition.  Rewriting the symbol-keyed metadata row would
    retroactively inject the announcement into every earlier replay.

    Defer only the exact causal case: both observations are still current-exchange records, the
    recorded value is Binance's exact perpetual sentinel, and the newly observed delivery is
    strictly after this generation's public-data cutoff but before the sentinel.  The recorded row
    remains byte-stable; the new observation is hash-bound in generation diagnostics.  Once the
    contract actually leaves exchangeInfo, CUP-20's existing delisting transition adopts the real
    delivery date.  Every other metadata difference still reaches ``append_frame`` and aborts.
    """
    path = staging / f"{CONTRACT_METADATA}.parquet"
    if not path.is_file() or incoming.empty:
        return incoming, ()
    cutoff = _utc(observed_at)
    recorded = pd.read_parquet(path)
    overlap = recorded.merge(
        incoming,
        on="symbol",
        how="inner",
        suffixes=("__recorded", "__fetched"),
        validate="one_to_one",
    )
    normalized = incoming.copy()
    observations: list[dict[str, str]] = []
    for row in overlap.itertuples(index=False):
        recorded_source = str(getattr(row, "metadata_source__recorded"))
        fetched_source = str(getattr(row, "metadata_source__fetched"))
        recorded_delivery = pd.Timestamp(getattr(row, "delivery_date__recorded"))
        fetched_delivery = pd.Timestamp(getattr(row, "delivery_date__fetched"))
        if (
            recorded_source != "current_exchangeInfo"
            or fetched_source != "current_exchangeInfo"
            or pd.isna(recorded_delivery)
            or pd.isna(fetched_delivery)
            or recorded_delivery != PERPETUAL_DELIVERY_SENTINEL
            or not cutoff < fetched_delivery < recorded_delivery
        ):
            continue
        symbol = str(row.symbol)
        normalized.loc[normalized["symbol"].astype(str).eq(symbol), "delivery_date"] = (
            recorded_delivery
        )
        observations.append(
            {
                "symbol": symbol,
                "field": "delivery_date",
                "recorded_value": recorded_delivery.isoformat(),
                "observed_value": fetched_delivery.isoformat(),
                "observed_at": cutoff.isoformat(),
                "disposition": "deferred_until_delisting_transition",
            }
        )
    return normalized, tuple(sorted(observations, key=lambda item: item["symbol"]))


def refresh_generation(
    cache_root: str | Path,
    *,
    boundary: object,
    resolve_membership: MembershipResolver,
    client: PublicMarketDataClient | None = None,
) -> tuple[Path, pd.DataFrame]:
    """Acquire one completed decision interval and publish one cumulative generation.

    Bars are fetched only through ``boundary + 8h`` (the just-completed transaction interval).
    Funding is fetched through that right endpoint inclusively, which preserves CUP-50's
    ``(t,t+8h]`` attribution. The next, still-forming transaction bar is never cached.
    """
    decision = _utc(boundary)
    if decision != decision.floor("8h") or decision < OOS_END:
        raise ValueError(f"invalid CUP-50 forward boundary: {decision}")
    right = decision + INTERVAL
    root = Path(cache_root).resolve()
    generations = root / GENERATIONS_DIRNAME
    generations.mkdir(parents=True, exist_ok=True)
    previous = current_generation(root)
    previous_diagnostics: Mapping[str, Any] = {}
    if previous is not None:
        previous_diagnostics = json.loads((previous / DIAGNOSTICS_FILENAME).read_text())
        previous_boundary = _utc(previous_diagnostics["boundary"])
        if decision < previous_boundary:
            raise CacheGenerationError("cache generations cannot move backwards")
        if decision == previous_boundary:
            return previous, pd.read_parquet(previous / "membership.parquet")

    staging = generations / f".staging-{uuid.uuid4().hex}"
    staging.mkdir()
    _copy_previous(previous, staging)
    owned = client is None
    reader = client or PublicMarketDataClient()
    try:
        exchange = reader.exchange_info()
        candidates = _candidate_symbols(exchange)
        old_bars = load_cached_frame(previous, BARS)
        old_names = set(old_bars["symbol"].astype(str)) if not old_bars.empty else set()
        known = tuple(name for name in candidates if name in old_names)
        new = tuple(name for name in candidates if name not in old_names)
        fetched_bars: list[pd.DataFrame] = []
        if known:
            overlap = max(OOS_END, decision - 2 * INTERVAL)
            fetched_bars.append(_fetch_bars(reader, known, overlap, right, KLINE_LIMIT))
        if new:
            fetched_bars.append(_fetch_bars(reader, new, OOS_END, right, KLINE_LIMIT))
        bars = (
            pd.concat([frame for frame in fetched_bars if not frame.empty], ignore_index=True)
            if any(not frame.empty for frame in fetched_bars)
            else empty_frame(BARS)
        )
        _append(staging, BARS, bars)
        metadata, deferred_metadata = _defer_announced_delivery_dates(
            staging,
            _fetch_contract_metadata(reader, bars, right),
            observed_at=right,
        )
        _append(staging, CONTRACT_METADATA, metadata)

        membership, current_members, execution_symbols = resolve_membership(staging, decision)
        if len(current_members) != 50:
            raise ValueError(
                f"dynamic CUP-50 membership at {decision} has {len(current_members)} names"
            )
        if not execution_symbols:
            raise ValueError("paper cache has no execution symbols")
        execution = tuple(sorted(set(execution_symbols)))
        # A departed/delisted former member remains in the accounting set, but Binance correctly
        # rejects REST requests for a symbol no longer in exchangeInfo. Its last cached bar is what
        # the evaluator uses for causal settlement; only current contracts are fetched anew.
        fetchable_execution = tuple(name for name in execution if name in set(candidates))
        if not fetchable_execution:
            raise ValueError("none of the accounting symbols is currently fetchable")
        execution_start = OOS_END
        if previous is not None:
            execution_start = max(OOS_END, decision - pd.Timedelta(days=3))
        hourly = _fetch_hourly_marks(
            reader, fetchable_execution, execution_start, right + MARK_EDGE, KLINE_LIMIT
        )
        cached_bars = pd.read_parquet(staging / f"{BARS}.parquet")
        published_marks = _publish_boundary_marks(hourly, cached_bars)
        funding = _fetch_funding(
            reader,
            fetchable_execution,
            execution_start,
            right + FUNDING_EDGE,
            pd.Timedelta(days=3),
            hourly,
        )
        _append(staging, MARK_PRICES, published_marks)
        _append(staging, FUNDING, funding)
        membership.to_parquet(staging / "membership.parquet", index=False)

        parent = previous.name if previous is not None else None
        generation_number = int(previous_diagnostics.get("generation", 0)) + 1
        row_key = pd.DataFrame(
            {
                "dataset": [BARS, FUNDING, MARK_PRICES, CONTRACT_METADATA, "membership"],
                "rows": [
                    len(pd.read_parquet(staging / f"{name}.parquet"))
                    for name in (BARS, FUNDING, MARK_PRICES, CONTRACT_METADATA, "membership")
                ],
            }
        )
        cache_generation(
            generation=generation_number,
            parent_sha256=parent,
            cutoff=right,
            rows=row_key,
        )
        diagnostics: dict[str, Any] = {
            "schema_version": 1,
            "namespace": "cup50-team02-cache-generation",
            "generation": generation_number,
            "parent_sha256": parent,
            "boundary": decision.isoformat(),
            "right_boundary": right.isoformat(),
            "candidate_symbol_count": len(candidates),
            "current_members": list(current_members),
            "execution_symbols": list(execution),
            "public_endpoints_only": True,
            "funding_right_boundary_inclusive": True,
            "transaction_bars_end_exclusive": True,
            "deferred_contract_metadata_observation_count": len(deferred_metadata),
            "deferred_contract_metadata_observations": list(deferred_metadata),
        }
        # The generation name binds the cumulative parquet bytes. The final cache manifest then
        # binds this diagnostics record too, avoiding an impossible self-hash cycle.
        file_bindings = _generation_file_bindings(staging)
        material = {**diagnostics, "files": file_bindings}
        digest = hashlib.sha256(_canonical(material)).hexdigest()
        diagnostics = {
            **diagnostics,
            "data_files_sha256": hashlib.sha256(_canonical(file_bindings)).hexdigest(),
            "generation_sha256": digest,
        }
        (staging / DIAGNOSTICS_FILENAME).write_text(
            json.dumps(diagnostics, indent=2, sort_keys=True) + "\n"
        )
        manifest = cache_manifest(staging)
        (staging / MANIFEST_FILENAME).write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n"
        )
        verify_cache_manifest(staging, manifest)
        destination = generations / digest
        if destination.exists():
            raise FileExistsError(destination)
        os.replace(staging, destination)
        temporary = root / f".{CURRENT_FILENAME}.{os.getpid()}"
        temporary.write_text(f"{GENERATIONS_DIRNAME}/{digest}\n")
        os.replace(temporary, root / CURRENT_FILENAME)
        return destination, membership
    finally:
        if owned:
            reader.close()
        if staging.exists():
            shutil.rmtree(staging)


def verify_generation_chain(cache_root: str | Path) -> tuple[Path, ...]:
    """Verify every immutable generation and its single-parent lineage."""
    root = Path(cache_root).resolve()
    current = current_generation(root)
    if current is None:
        return ()
    chain: list[Path] = []
    seen: set[str] = set()
    cursor: Path | None = current
    while cursor is not None:
        if cursor.name in seen:
            raise CacheGenerationError("cache generation chain contains a cycle")
        seen.add(cursor.name)
        _read_manifest(cursor)
        diagnostics = json.loads((cursor / DIAGNOSTICS_FILENAME).read_text())
        _verify_generation_name(cursor, diagnostics)
        chain.append(cursor)
        parent = diagnostics.get("parent_sha256")
        cursor = (root / GENERATIONS_DIRNAME / str(parent)) if parent else None
        if cursor is not None and not cursor.is_dir():
            raise CacheGenerationError(f"missing parent cache generation: {parent}")
    expected = list(range(1, len(chain) + 1))
    observed = sorted(
        int(json.loads((path / DIAGNOSTICS_FILENAME).read_text())["generation"])
        for path in chain
    )
    if observed != expected:
        raise CacheGenerationError(f"non-contiguous cache generations: {observed}")
    return tuple(reversed(chain))


def execution_symbols_from_membership(
    membership: pd.DataFrame, *, carried: Sequence[str] = ()
) -> tuple[str, ...]:
    return tuple(sorted(set(membership["symbol"].astype(str)) | set(carried)))
