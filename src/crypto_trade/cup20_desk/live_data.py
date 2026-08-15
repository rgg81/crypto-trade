"""Forward market data for the CUP-20 winner's paper desk, in the sealed snapshot's own schema.

The desk gets backtest/live parity by re-running the tournament's own evaluator over a snapshot
that rolls forward. That makes this module the single place where the desk can go wrong quietly:
a frame whose columns are right but whose dtypes are not loads cleanly through
``crypto_trade.tournament.snapshot.load_snapshot`` and then makes the evaluator compute something
subtly different. So nothing here is written from memory of what the schema "should" be.

**How the schema was verified.** Every column name, order and dtype in :data:`SNAPSHOT_SCHEMAS`
was read off the sealed parquet files themselves --
``pd.read_parquet('data/cup20/is/<frame>.parquet').dtypes`` and the corresponding arrow schema via
``pyarrow.parquet.ParquetFile(...).schema_arrow`` -- for both ``data/cup20/is`` and
``data/cup20/sealed``, which agree. ``tests/cup20_desk/test_live_data.py`` re-asserts that equality
on every run, column for column and dtype for dtype, for every frame and both snapshot roots, and
again after a parquet round trip through :func:`append_frame`, so the declaration cannot drift away
from the bytes it describes without a test failing.

That check caught a real trap on the way in. Under pandas 3, ``pd.to_datetime(values, unit='ms',
utc=True)`` yields ``datetime64[ms, UTC]``, not ``[ns, UTC]`` -- a frame built the obvious way
writes ``timestamp[us]`` into parquet where the snapshot holds ``timestamp[ns]``. It reads back
without complaint. :func:`conform_frame` is the single choke point that casts it back, and every
frame this module returns or writes passes through it.

**Reuse over reinvention.** The frames the tournament sealed were produced by
``crypto_trade.tournament.snapshot``; the same functions produce them here, so funding's floor-hour
mark join, its interval derivation and the contract-metadata lifecycle branches are not
"matched" to the acquisition, they ARE the acquisition. Only the wire format differs: the
acquisition parsed checksummed monthly CSV archives, and a forward desk has to read the JSON REST
endpoints, which publish the current month the archives do not carry yet.

**Paper only.** Four public market-data endpoints, declared in :data:`PUBLIC_ENDPOINTS` and
enforced on every request. Nothing here holds a credential, and no order path exists.

**Append invariance is a hard abort.** :func:`append_frame` never overwrites a recorded row. If a
key that was already stored comes back carrying different values, it raises
:class:`AppendInvarianceError` naming the key and the column and writes nothing, leaving both the
stored value and the incoming one available on the exception. Binance revising history underneath a
running desk invalidates the forward record; it is not a rounding difference to absorb.

**Delisting is a transition, not a revision.** ``contract_metadata`` is keyed on ``symbol`` alone,
so a universe member that delists mid-window -- leaving live exchangeInfo and flipping from
``current_exchangeInfo`` to ``archive_inference`` with a real ``delivery_date`` -- would abort a
strictly append-invariant desk. Over six months on a twenty-name crypto universe that WILL happen,
and a desk that halts on a routine delisting is not operational.

The rule was wrong, not the event. Append invariance exists to catch a *revised fact*: a bar whose
OHLCV changed underneath us. A contract ceasing to exist is not a revision of an old fact, it is a
new fact about a later time, and the tournament's own execution contract already treats delisting
as normal -- a member with no executable open is force-exited at its last executable open, with no
survivorship rescue. So :data:`CONTRACT_LIFECYCLE_TRANSITIONS` declares exactly one permitted,
one-way transition on an existing metadata row, and :func:`append_frame` applies it.

It is an allowlist, not an escape hatch, and the difference is enforced three ways. It is scoped to
``contract_metadata``: a changed close on a bar or a changed mark aborts as before. Within that
frame each column is classified explicitly -- the trigger, the columns that follow it, the columns
that may only move one way, and the four that identify the contract and may not move at all -- and
:func:`_require_total_classification` refuses at import time if that classification does not cover
every value column, so a schema that grows a column cannot quietly inherit a bypass. And every
permitted move is directional: ``archive_inference`` never returns to ``current_exchangeInfo``, a
delivery date may only be brought FORWARD from unknown or far-future to a date that has arrived,
and a changed ``quote_asset``, ``margin_asset``, ``contract_type`` or ``is_crypto`` is a different
contract wearing the same ticker and still aborts.

One column is permitted to differ and is deliberately NOT adopted. ``_contract_metadata``'s
archive-inference branch reads ``onboard_date`` off the bars it was handed, and the desk hands it
one fetch window rather than the symbol's whole history, so the incoming onboard date is the desk's
own narrower view of an unchanged fact, not a new one. The recorded value wins, and the incoming
one may only be LATER -- an earlier one would mean the recorded value was wrong, which is a
revision and aborts.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import re
import time
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

import httpx
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from pandas.api.types import pandas_dtype

# The acquisition functions that produced the sealed bytes. Private by name, deliberately imported:
# re-deriving funding's floor-hour mark join, its interval derivation or the contract-metadata
# lifecycle branches would create a second implementation of the schema, and two implementations
# can disagree. These cannot -- they are the originals. `crypto_trade/tournament/` is not
# hash-bound; `crypto_trade/cup20/` is, and nothing here touches it.
from crypto_trade.cup20.universe import MEMBERSHIP_COLUMNS
from crypto_trade.tournament.snapshot import _KLINE_COLUMNS as KLINE_FIELDS
from crypto_trade.tournament.snapshot import _attach_mark_prices as attach_mark_prices
from crypto_trade.tournament.snapshot import _canonical_bars as canonical_bars
from crypto_trade.tournament.snapshot import _contract_metadata as contract_metadata_frame
from crypto_trade.tournament.snapshot import (
    _derive_missing_funding_intervals as derive_funding_intervals,
)
from crypto_trade.tournament.snapshot import _epoch_to_utc as epoch_to_utc
from crypto_trade.tournament.snapshot import _utc as utc

FAPI_BASE_URL = "https://fapi.binance.com"

KLINES_ENDPOINT = "/fapi/v1/klines"
MARK_PRICE_KLINES_ENDPOINT = "/fapi/v1/markPriceKlines"
FUNDING_RATE_ENDPOINT = "/fapi/v1/fundingRate"
EXCHANGE_INFO_ENDPOINT = "/fapi/v1/exchangeInfo"

PUBLIC_ENDPOINTS = frozenset(
    {
        KLINES_ENDPOINT,
        MARK_PRICE_KLINES_ENDPOINT,
        FUNDING_RATE_ENDPOINT,
        EXCHANGE_INFO_ENDPOINT,
    }
)
"""Every endpoint the desk may reach. All four are public market data, and
:meth:`PublicMarketDataClient.get_json` refuses anything absent from this set, so the paper-only
constraint is executable rather than a comment."""

INTERVAL_HOURS = 8
"""The tournament's decision grid. Bars and the published mark panel live on it."""

MARK_INTERVAL = "1h"
BAR_INTERVAL = "8h"

# Binance charges kline weight in bands (1-99 -> 1, 100-499 -> 2, 500-1000 -> 5, >1000 -> 10), so
# 499 rows for two weight units is the cheapest row-per-weight point on the curve, and it keeps
# each response small enough that a retry is cheap.
KLINE_LIMIT = 499
FUNDING_LIMIT = 1000

# Funding intervals are derived from the spacing between adjacent events, exactly as the
# acquisition derived them for REST-sourced months. Derived from the PREVIOUS event, a row's
# interval does not depend on where the fetch window happens to start -- but only if the window
# reaches back far enough to contain that previous event. Hence the context lookback: it is
# fetched, used for the derivation, then discarded. Without it the first row of every fetch would
# fall back to the spacing of the event AFTER it, and a rolling desk would eventually re-derive an
# already-recorded interval differently and abort on its own arithmetic.
FUNDING_CONTEXT = pd.Timedelta(days=3)

MANIFEST_FILENAME = "cache-manifest.json"
CACHE_SCHEMA_VERSION = "cup20-desk-cache-v1"

BARS = "bars"
FUNDING = "funding"
MARK_PRICES = "mark_prices"
CONTRACT_METADATA = "contract_metadata"
MEMBERSHIP = "membership"

SNAPSHOT_FRAMES: tuple[str, ...] = (BARS, FUNDING, MARK_PRICES, CONTRACT_METADATA)
"""The four frames :func:`fetch_forward` acquires from public market data."""

SNAPSHOT_DATASETS: tuple[str, ...] = (*SNAPSHOT_FRAMES, MEMBERSHIP)
"""Every dataset a snapshot directory holds. ``membership`` is DERIVED rather than fetched -- it is
built by ``crypto_trade.cup20_desk.snapshot_forward`` out of the other four -- but it is written
alongside them and read back by the tournament's own loader, so its schema is declared here with
the rest."""

_TIMESTAMP = "datetime64[ns, UTC]"
_MILLISECOND = 1_000_000


class FrameSchemaError(ValueError):
    """A frame is not the snapshot frame it claims to be."""


class AppendInvarianceError(RuntimeError):
    """A row that was already recorded came back with different values.

    Carries the key, the column that differs and both values, so the operator can adjudicate
    without re-fetching. Nothing is written when this is raised.
    """

    def __init__(
        self,
        *,
        name: str,
        path: Path,
        key: Mapping[str, Any],
        column: str,
        existing: Any,
        incoming: Any,
    ) -> None:
        rendered = ", ".join(f"{field}={value}" for field, value in key.items())
        super().__init__(
            f"APPEND-INVARIANCE ABORT: {path} already records {name} row ({rendered}) with "
            f"{column}={existing!r}, but the source now reports {column}={incoming!r}; "
            "both values are preserved and nothing was written"
        )
        self.name = name
        self.path = path
        self.key = dict(key)
        self.column = column
        self.existing = existing
        self.incoming = incoming


class CacheDriftError(RuntimeError):
    """A cache file is not the one the manifest bound."""


class BinancePublicDataError(RuntimeError):
    """A public Binance endpoint refused a request, or kept refusing it."""

    def __init__(self, *, endpoint: str, status_code: int | None, message: str) -> None:
        super().__init__(f"Binance public market data {endpoint} failed ({status_code}): {message}")
        self.endpoint = endpoint
        self.status_code = status_code


@dataclasses.dataclass(frozen=True, slots=True)
class FrameSchema:
    """One snapshot frame's exact shape, plus the key the desk appends on."""

    name: str
    columns: tuple[str, ...]
    dtypes: tuple[str, ...]
    key: tuple[str, ...]
    order: tuple[str, ...]

    @property
    def pandas_dtypes(self) -> tuple[Any, ...]:
        return tuple(pandas_dtype(value) for value in self.dtypes)

    @property
    def values(self) -> tuple[str, ...]:
        """Every non-key column -- the ones append invariance compares."""
        return tuple(column for column in self.columns if column not in self.key)


SNAPSHOT_SCHEMAS: Mapping[str, FrameSchema] = {
    BARS: FrameSchema(
        name=BARS,
        columns=(
            "open_time",
            "symbol",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_volume",
            "trade_count",
            "taker_buy_volume",
            "taker_buy_quote_volume",
        ),
        dtypes=(
            _TIMESTAMP,
            "str",
            "float64",
            "float64",
            "float64",
            "float64",
            "float64",
            _TIMESTAMP,
            "float64",
            "int64",
            "float64",
            "float64",
        ),
        key=("symbol", "open_time"),
        order=("open_time", "symbol"),
    ),
    FUNDING: FrameSchema(
        name=FUNDING,
        columns=(
            "funding_time",
            "symbol",
            "funding_rate",
            "mark_price",
            "mark_time",
            "settlement_time",
            "funding_interval_hours",
        ),
        dtypes=(
            _TIMESTAMP,
            "str",
            "float64",
            "float64",
            _TIMESTAMP,
            _TIMESTAMP,
            "float64",
        ),
        key=("symbol", "funding_time"),
        order=("funding_time", "symbol"),
    ),
    MARK_PRICES: FrameSchema(
        name=MARK_PRICES,
        columns=("mark_time", "symbol", "mark_price"),
        dtypes=(_TIMESTAMP, "str", "float64"),
        key=("symbol", "mark_time"),
        order=("mark_time", "symbol"),
    ),
    CONTRACT_METADATA: FrameSchema(
        name=CONTRACT_METADATA,
        columns=(
            "symbol",
            "contract_type",
            "quote_asset",
            "margin_asset",
            "is_crypto",
            "onboard_date",
            "delivery_date",
            "underlying_type",
            "metadata_source",
        ),
        dtypes=("str", "str", "str", "str", "bool", _TIMESTAMP, _TIMESTAMP, "str", "str"),
        key=("symbol",),
        order=("symbol",),
    ),
    MEMBERSHIP: FrameSchema(
        name=MEMBERSHIP,
        # Column NAMES are imported from the tournament's own universe module rather than repeated
        # here, so a membership frame this package writes cannot drift from the one
        # ``build_membership`` produces. The dtypes are read off the sealed parquet, like the rest.
        columns=MEMBERSHIP_COLUMNS,
        dtypes=(_TIMESTAMP, "str", "int64", "float64"),
        key=("reconstitution_time", "symbol"),
        order=("reconstitution_time", "symbol"),
    ),
}


@dataclasses.dataclass(frozen=True, slots=True)
class AppendResult:
    """What one append actually did.

    ``transitioned`` counts existing rows that changed state through
    :data:`CONTRACT_LIFECYCLE_TRANSITIONS`. It is reported separately from ``appended`` and
    ``unchanged`` precisely because it is the one case in which a recorded row is rewritten: an
    operator reading a tick's result should see a delisting, not have it absorbed into a count.
    """

    path: Path
    name: str
    appended: int
    unchanged: int
    total: int
    transitioned: int = 0


# ------------------------------------------------------------------------------------------------
# schema
# ------------------------------------------------------------------------------------------------


def frame_schema(name: str) -> FrameSchema:
    schema = SNAPSHOT_SCHEMAS.get(name)
    if schema is None:
        raise FrameSchemaError(
            f"{name!r} is not a CUP-20 snapshot frame; expected one of {SNAPSHOT_DATASETS}"
        )
    return schema


def empty_frame(name: str) -> pd.DataFrame:
    """A zero-row frame carrying the snapshot's exact columns and dtypes."""
    schema = frame_schema(name)
    return pd.DataFrame(
        {
            column: pd.Series([], dtype=dtype)
            for column, dtype in zip(schema.columns, schema.pandas_dtypes, strict=True)
        }
    )


def infer_frame_name(frame: pd.DataFrame) -> str:
    """Identify which snapshot frame ``frame`` is trying to be.

    Scored by column overlap rather than requiring an exact match, so a frame that is *nearly* one
    of the schemas is attributed to it and then refused by :func:`conform_frame` with a message
    naming the column it is missing -- which is the diagnostic the caller needs.

    Overlap alone is not enough to separate them: ``mark_prices``' three columns are all present in
    ``funding``, so both score identically on intersection. The symmetric difference breaks that --
    the frame is attributed to the schema it differs from least -- and a genuine tie on both counts
    is unattributable and refused.
    """
    columns = set(frame.columns)
    scored = sorted(
        (
            (-len(columns & set(schema.columns)), len(columns ^ set(schema.columns)), name)
            for name, schema in SNAPSHOT_SCHEMAS.items()
        )
    )
    overlap, distance, name = scored[0]
    if overlap == 0:
        raise FrameSchemaError(f"columns {sorted(columns)} match no CUP-20 snapshot frame")
    if len(scored) > 1 and scored[1][:2] == (overlap, distance):
        raise FrameSchemaError(
            f"columns {sorted(columns)} match {name} and {scored[1][2]} equally well"
        )
    return name


def conform_frame(name: str, frame: pd.DataFrame) -> pd.DataFrame:
    """Return ``frame`` in the snapshot's exact column order and dtypes, or refuse.

    Every frame this module returns or writes passes through here. It is the only defence against
    the drift class that motivates this module: a frame that is right in every visible respect and
    wrong in a dtype.
    """
    schema = frame_schema(name)
    present = set(frame.columns)
    missing = [column for column in schema.columns if column not in present]
    if missing:
        raise FrameSchemaError(f"{name} frame is missing columns {missing}")
    unexpected = sorted(present - set(schema.columns))
    if unexpected:
        raise FrameSchemaError(f"{name} frame carries unexpected columns {unexpected}")
    result = frame.loc[:, list(schema.columns)].copy()
    for column, dtype in zip(schema.columns, schema.pandas_dtypes, strict=True):
        result[column] = _cast(result[column], dtype, name=name, column=column)
    result = result.reset_index(drop=True)
    actual = tuple(str(dtype) for dtype in result.dtypes)
    expected = tuple(str(dtype) for dtype in schema.pandas_dtypes)
    if actual != expected:
        raise FrameSchemaError(f"{name} frame dtypes {actual} do not match the snapshot {expected}")
    return result


def _cast(values: pd.Series, dtype: Any, *, name: str, column: str) -> pd.Series:
    try:
        if isinstance(dtype, pd.DatetimeTZDtype):
            return pd.to_datetime(values, utc=True, errors="raise").astype(dtype)
        return values.astype(dtype)
    except (TypeError, ValueError) as exc:
        raise FrameSchemaError(f"{name}.{column} cannot be read as {dtype}: {exc}") from exc


# ------------------------------------------------------------------------------------------------
# declared lifecycle transitions
# ------------------------------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True, slots=True)
class LifecycleTransition:
    """One declared, one-way change of state an already-recorded row is permitted to make.

    Every value column of the frame falls into exactly one bucket, and
    :func:`_require_total_classification` refuses at import time if one does not:

    ``trigger``
        ``(column, from, to)``. The transition fires only when this column moves exactly this way.
        A row whose trigger has not fired has no permitted changes at all.
    ``followed``
        ``column -> permitted (from, to) pairs``. Columns that change WITH the trigger, to a value
        named in advance. The incoming value is adopted.
    ``advanced``
        Timestamp columns that may only be brought FORWARD: from unknown (``NaT``) or from a
        far-future placeholder to an earlier, real date. A date moving later, or a real date
        becoming unknown, is a revision. The incoming value is adopted.
    ``deferred``
        Timestamp columns the RECORDED value is kept for, because the incoming one is an artifact
        of the desk's narrower observation window rather than a new fact. The incoming value may
        only be later; earlier means the recorded value was wrong, which is a revision.
    ``invariant``
        The columns that identify the contract. Any change is a different contract wearing the same
        ticker, and still aborts.
    """

    name: str
    frame: str
    trigger: tuple[str, str, str]
    followed: Mapping[str, tuple[tuple[str, str], ...]]
    advanced: tuple[str, ...]
    deferred: tuple[str, ...]
    invariant: tuple[str, ...]

    @property
    def trigger_column(self) -> str:
        return self.trigger[0]

    def fired(self, recorded: Any, incoming: Any) -> bool:
        """The transition is happening on this refetch."""
        _, before, after = self.trigger
        return recorded == before and incoming == after

    def settled(self, recorded: Any, incoming: Any) -> bool:
        """The transition already happened, and the source still reports the same state.

        Distinguished from :meth:`fired` because a rolling desk refetches the same window over and
        over. A ``deferred`` column disagrees on EVERY one of those refetches -- the recorded value
        was kept, the source keeps re-deriving its own -- so a transition that tolerated the
        disagreement only while firing would abort on the very next tick. In this state nothing is
        adopted: the ``deferred`` disagreement is tolerated and anything else still aborts.
        """
        _, _, after = self.trigger
        return recorded == after and incoming == after


DELISTING = LifecycleTransition(
    name="delisting",
    frame=CONTRACT_METADATA,
    # The exact literals `crypto_trade.tournament.snapshot._contract_metadata` writes on its two
    # lifecycle branches, read out of that function rather than assumed: a symbol still in live
    # exchangeInfo gets `current_exchangeInfo` / the venue's own `underlyingType`, and one that has
    # left it is archive-inferred.
    trigger=("metadata_source", "current_exchangeInfo", "archive_inference"),
    followed={"underlying_type": (("COIN", "ARCHIVE_INFERRED_COIN"),)},
    advanced=("delivery_date",),
    deferred=("onboard_date",),
    invariant=("contract_type", "quote_asset", "margin_asset", "is_crypto"),
)

CONTRACT_LIFECYCLE_TRANSITIONS: tuple[LifecycleTransition, ...] = (DELISTING,)
"""The complete, frozen allowlist. A change to an existing row that no entry here classifies is an
:class:`AppendInvarianceError`, whatever frame it is in."""


def _require_total_classification(transition: LifecycleTransition) -> LifecycleTransition:
    """Refuse a transition that does not decide every value column of its frame.

    The guarantee this buys is the one the allowlist is for: a column nobody classified would be
    compared by the general path and abort -- fail-closed, so far so good -- but a column added to
    the schema and quietly swept into a permissive bucket would not. Requiring an exact partition
    means the classification has to be revisited by hand whenever the frame changes.
    """
    schema = frame_schema(transition.frame)
    buckets = (
        (transition.trigger_column,),
        tuple(transition.followed),
        transition.advanced,
        transition.deferred,
        transition.invariant,
    )
    classified = [column for bucket in buckets for column in bucket]
    if len(classified) != len(set(classified)):
        raise FrameSchemaError(f"{transition.name} classifies a column twice")
    if set(classified) != set(schema.values):
        difference = sorted(set(classified) ^ set(schema.values))
        raise FrameSchemaError(
            f"{transition.name} does not classify exactly the value columns of {transition.frame}; "
            f"{difference} is classified by one and not the other"
        )
    return transition


for _transition in CONTRACT_LIFECYCLE_TRANSITIONS:
    _require_total_classification(_transition)


# ------------------------------------------------------------------------------------------------
# public market data
# ------------------------------------------------------------------------------------------------


class PublicMarketDataClient:
    """A serial, polite reader of public Binance USD-M market data.

    Serial on purpose: the desk fetches at most a few dozen symbols once every eight hours, so
    there is nothing to gain from concurrency and a burst is the one thing that gets an address
    rate-limited. Request weight is read back off each response and the client pauses when it
    approaches the budget, rather than waiting to be told with a 429.
    """

    def __init__(
        self,
        *,
        base_url: str = FAPI_BASE_URL,
        timeout_seconds: float = 45.0,
        pause_seconds: float = 0.05,
        weight_soft_limit: int = 1_800,
        weight_window_seconds: float = 60.0,
        max_attempts: int = 5,
        transport: httpx.BaseTransport | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        options: dict[str, Any] = {"base_url": base_url, "timeout": timeout_seconds}
        if transport is not None:
            options["transport"] = transport
        self._http = httpx.Client(**options)
        self.pause_seconds = pause_seconds
        self.weight_soft_limit = weight_soft_limit
        self.weight_window_seconds = weight_window_seconds
        self.max_attempts = max_attempts
        self.used_weight = 0
        self._sleep = sleep

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> PublicMarketDataClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def get_json(self, endpoint: str, *, params: Mapping[str, Any] | None = None) -> Any:
        response = self._request(endpoint, params=params)
        try:
            return response.json()
        except ValueError as exc:
            raise BinancePublicDataError(
                endpoint=endpoint, status_code=response.status_code, message="response is not JSON"
            ) from exc

    def exchange_info(self) -> Mapping[str, Any]:
        payload = self.get_json(EXCHANGE_INFO_ENDPOINT)
        if not isinstance(payload, Mapping) or not isinstance(payload.get("symbols"), list):
            raise ValueError("exchangeInfo response has no symbols array")
        return payload

    def klines(
        self, symbol: str, *, start: pd.Timestamp, end_exclusive: pd.Timestamp, limit: int
    ) -> list[list[Any]]:
        return self._paged_klines(
            KLINES_ENDPOINT,
            symbol,
            interval=BAR_INTERVAL,
            start=start,
            end_exclusive=end_exclusive,
            limit=limit,
        )

    def mark_price_klines(
        self, symbol: str, *, start: pd.Timestamp, end_exclusive: pd.Timestamp, limit: int
    ) -> list[list[Any]]:
        return self._paged_klines(
            MARK_PRICE_KLINES_ENDPOINT,
            symbol,
            interval=MARK_INTERVAL,
            start=start,
            end_exclusive=end_exclusive,
            limit=limit,
        )

    def funding_rate(
        self, symbol: str, *, start: pd.Timestamp, end_exclusive: pd.Timestamp
    ) -> list[Mapping[str, Any]]:
        start_ms = _milliseconds(start)
        end_ms = _milliseconds(end_exclusive) - 1
        cursor = start_ms
        events: list[Mapping[str, Any]] = []
        seen: set[int] = set()
        while cursor <= end_ms:
            payload = self.get_json(
                FUNDING_RATE_ENDPOINT,
                params={
                    "symbol": symbol,
                    "startTime": cursor,
                    "endTime": end_ms,
                    "limit": FUNDING_LIMIT,
                },
            )
            if not isinstance(payload, list):
                raise ValueError(f"funding response for {symbol} is not an array")
            if not payload:
                break
            for item in payload:
                if not isinstance(item, Mapping):
                    raise ValueError(f"funding response for {symbol} holds a non-object")
                if str(item.get("symbol")) != symbol:
                    raise ValueError(f"funding response for {symbol} holds a foreign symbol")
                stamp = int(item["fundingTime"])
                if stamp < start_ms or stamp > end_ms:
                    raise ValueError(f"funding response for {symbol} escaped its window")
                if stamp in seen:
                    raise ValueError(f"duplicate funding event for {symbol} at {stamp}")
                seen.add(stamp)
                events.append(item)
            if len(payload) < FUNDING_LIMIT:
                break
            last = int(payload[-1]["fundingTime"])
            if last < cursor:
                raise ValueError(f"funding pagination did not advance for {symbol}")
            cursor = last + 1
        return events

    def _paged_klines(
        self,
        endpoint: str,
        symbol: str,
        *,
        interval: str,
        start: pd.Timestamp,
        end_exclusive: pd.Timestamp,
        limit: int,
    ) -> list[list[Any]]:
        if limit < 1:
            raise ValueError("kline limit must be positive")
        start_ms = _milliseconds(start)
        end_ms = _milliseconds(end_exclusive) - 1
        cursor = start_ms
        rows: list[list[Any]] = []
        seen: set[int] = set()
        while cursor <= end_ms:
            payload = self.get_json(
                endpoint,
                params={
                    "symbol": symbol,
                    "interval": interval,
                    "startTime": cursor,
                    "endTime": end_ms,
                    "limit": limit,
                },
            )
            if not isinstance(payload, list):
                raise ValueError(f"kline response for {symbol} is not an array")
            if not payload:
                break
            for row in payload:
                if not isinstance(row, list) or len(row) < len(KLINE_FIELDS) - 1:
                    raise ValueError(f"kline response for {symbol} holds a malformed row")
                stamp = int(row[0])
                if stamp in seen:
                    raise ValueError(f"duplicate kline for {symbol} at {stamp}")
                seen.add(stamp)
                rows.append(row)
            if len(payload) < limit:
                break
            last = int(payload[-1][0])
            if last < cursor:
                raise ValueError(f"kline pagination did not advance for {symbol}")
            cursor = last + 1
        return rows

    def _request(self, endpoint: str, *, params: Mapping[str, Any] | None = None) -> httpx.Response:
        if endpoint not in PUBLIC_ENDPOINTS:
            raise ValueError(
                f"{endpoint} is not a declared public market-data endpoint; the CUP-20 desk is "
                "paper-only and reads nothing else"
            )
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            if self.pause_seconds and attempt == 0:
                self._sleep(self.pause_seconds)
            try:
                response = self._http.get(endpoint, params=params)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                last_error = exc
                status = exc.response.status_code
                # 418 is Binance's "you ignored a rate limit and this address is now barred", and
                # every further request while it stands EXTENDS it. So it is reported at once,
                # naming the expiry the body carries, and left for the desk's watchdog to wait out.
                # Retrying here would turn a few minutes of downtime into days -- this address was
                # already in that state, from another process, while this module was being written.
                # 429 is the ordinary rate limit and IS retried, honouring Retry-After.
                if status == 418:
                    raise BinancePublicDataError(
                        endpoint=endpoint,
                        status_code=status,
                        message=_barred_message(exc.response.text),
                    ) from exc
                if status != 429 and status < 500:
                    raise BinancePublicDataError(
                        endpoint=endpoint,
                        status_code=status,
                        message=exc.response.text[:200],
                    ) from exc
                if attempt + 1 < self.max_attempts:
                    self._sleep(_retry_delay(exc.response.headers.get("Retry-After"), attempt))
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt + 1 < self.max_attempts:
                    self._sleep(min(2.0**attempt, 30.0))
            else:
                self._observe_weight(response)
                return response
        raise BinancePublicDataError(
            endpoint=endpoint, status_code=None, message=f"exhausted retries: {last_error}"
        )

    def _observe_weight(self, response: httpx.Response) -> None:
        raw = response.headers.get("X-MBX-USED-WEIGHT-1M")
        if raw is None:
            return
        try:
            self.used_weight = int(raw)
        except ValueError:
            return
        if self.used_weight >= self.weight_soft_limit:
            self._sleep(self.weight_window_seconds)


# ------------------------------------------------------------------------------------------------
# forward fetch
# ------------------------------------------------------------------------------------------------


def fetch_forward(
    symbols: Sequence[str],
    start: object,
    end: object,
    *,
    client: PublicMarketDataClient | None = None,
    base_url: str = FAPI_BASE_URL,
    transport: httpx.BaseTransport | None = None,
    sleep: Callable[[float], None] = time.sleep,
    kline_limit: int = KLINE_LIMIT,
    funding_context: pd.Timedelta = FUNDING_CONTEXT,
) -> dict[str, pd.DataFrame]:
    """Fetch ``[start, end)`` for ``symbols`` as the four sealed-snapshot frames.

    ``start`` and ``end`` are exact 8h UTC boundaries: the tournament's decision grid, and the only
    grid the evaluator ever reads a bar or a mark at.

    The returned population is every row the public endpoints publish for the requested symbols in
    the window. It is a superset of the sealed snapshot's, which additionally restricts the mark
    panel to each symbol's membership period -- that restriction needs point-in-time membership and
    therefore belongs to snapshot assembly, not here. The SCHEMA is identical, which is what this
    function is responsible for.
    """
    window_start = _boundary(start)
    window_end = _boundary(end)
    if window_start >= window_end:
        raise ValueError(f"forward window {window_start} .. {window_end} is empty")
    names = tuple(dict.fromkeys(str(symbol) for symbol in symbols))
    if not names:
        raise ValueError("fetch_forward needs at least one symbol")

    owned = client is None
    reader = client or PublicMarketDataClient(base_url=base_url, transport=transport, sleep=sleep)
    try:
        bars = _fetch_bars(reader, names, window_start, window_end, kline_limit)
        hourly = _fetch_hourly_marks(reader, names, window_start, window_end, kline_limit)
        funding = _fetch_funding(reader, names, window_start, window_end, funding_context, hourly)
        metadata = _fetch_contract_metadata(reader, bars, window_end)
    finally:
        if owned:
            reader.close()
    return {
        BARS: bars,
        FUNDING: funding,
        MARK_PRICES: _publish_boundary_marks(hourly, bars),
        CONTRACT_METADATA: metadata,
    }


def _boundary(value: object) -> pd.Timestamp:
    timestamp = utc(value)
    floored = timestamp.floor(f"{INTERVAL_HOURS}h")
    if timestamp != floored:
        raise ValueError(f"{timestamp} is not an exact {INTERVAL_HOURS}h UTC boundary")
    return timestamp


def _fetch_bars(
    client: PublicMarketDataClient,
    symbols: tuple[str, ...],
    start: pd.Timestamp,
    end: pd.Timestamp,
    limit: int,
) -> pd.DataFrame:
    frames = [
        _kline_frame(
            symbol,
            client.klines(symbol, start=start, end_exclusive=end, limit=limit),
            interval_hours=INTERVAL_HOURS,
        )
        for symbol in symbols
    ]
    populated = [frame for frame in frames if not frame.empty]
    if not populated:
        return empty_frame(BARS)
    return conform_frame(BARS, canonical_bars(populated, start, end))


def _kline_frame(symbol: str, rows: list[list[Any]], *, interval_hours: int) -> pd.DataFrame:
    """One symbol's transaction klines, validated exactly as the archive parser validates them."""
    if not rows:
        return empty_frame(BARS)
    fields = list(KLINE_FIELDS[:11])
    raw = pd.DataFrame([row[:11] for row in rows], columns=fields)
    frame = pd.DataFrame(
        {
            "open_time": epoch_to_utc(raw["open_time"], "open_time"),
            "symbol": symbol,
            "close_time": epoch_to_utc(raw["close_time"], "close_time"),
        }
    )
    for column in (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "trade_count",
        "taker_buy_volume",
        "taker_buy_quote_volume",
    ):
        frame[column] = pd.to_numeric(raw[column], errors="raise")
        if not np.isfinite(frame[column].to_numpy(dtype=float)).all():
            raise ValueError(f"non-finite {column} for {symbol}")
    if (frame[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError(f"non-positive kline price for {symbol}")
    if (frame[["volume", "quote_volume", "trade_count"]] < 0).any().any():
        raise ValueError(f"negative kline volume/count for {symbol}")
    _require_alignment(frame["open_time"], interval_hours, f"{symbol} transaction bars")
    return conform_frame(BARS, frame)


def _fetch_hourly_marks(
    client: PublicMarketDataClient,
    symbols: tuple[str, ...],
    start: pd.Timestamp,
    end: pd.Timestamp,
    limit: int,
) -> pd.DataFrame:
    """The full hourly mark panel.

    Hourly rather than 8-hourly because funding needs the mark at the floor hour of each settlement
    and a 4h funding schedule settles at hours the 8h grid never touches. The acquisition did the
    same: it kept a full hourly panel, joined funding against it, and published only the boundary
    subset. Only the boundary subset is published here too.
    """
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        rows = client.mark_price_klines(symbol, start=start, end_exclusive=end, limit=limit)
        if not rows:
            continue
        opens = epoch_to_utc(pd.Series([row[0] for row in rows]), "mark_time")
        prices = pd.to_numeric(pd.Series([row[1] for row in rows]), errors="raise")
        if not np.isfinite(prices.to_numpy(dtype=float)).all() or (prices <= 0).any():
            raise ValueError(f"non-positive/non-finite mark price for {symbol}")
        _require_alignment(opens, 1, f"{symbol} mark prices")
        frames.append(
            conform_frame(
                MARK_PRICES,
                pd.DataFrame({"mark_time": opens, "symbol": symbol, "mark_price": prices}),
            )
        )
    if not frames:
        return empty_frame(MARK_PRICES)
    panel = pd.concat(frames, ignore_index=True)
    if panel.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("duplicate (mark_time, symbol) rows in the forward mark panel")
    return conform_frame(MARK_PRICES, panel.sort_values(["mark_time", "symbol"]))


def _publish_boundary_marks(hourly: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    """Keep the marks an evaluation can actually consult: the ones coincident with a bar open.

    ``evaluate_targets`` looks a mark up at a bar open timestamp and nowhere else, so a mark
    published off that grid is one no evaluation can ever read. Publishing it would inflate apparent
    coverage without adding a single usable row.

    Coincidence with a bar open is the whole rule, and it delivers 8h alignment as a consequence
    rather than as a second filter: ``_kline_frame`` has already refused any bar whose open is not
    on the 8h grid, so an off-grid mark has nothing to join to. A separate alignment predicate here
    would look like a safeguard while being unreachable -- it was written that way first, and a
    mutation that deleted it changed no observable behaviour, which is how it was found.
    """
    if hourly.empty or bars.empty:
        return empty_frame(MARK_PRICES)
    executable = bars.loc[:, ["open_time", "symbol"]].rename(columns={"open_time": "mark_time"})
    merged = hourly.merge(
        executable, on=["mark_time", "symbol"], how="inner", validate="one_to_one"
    )
    return conform_frame(MARK_PRICES, merged.sort_values(["mark_time", "symbol"]))


def _fetch_funding(
    client: PublicMarketDataClient,
    symbols: tuple[str, ...],
    start: pd.Timestamp,
    end: pd.Timestamp,
    context: pd.Timedelta,
    hourly: pd.DataFrame,
) -> pd.DataFrame:
    """Funding events with the interval derived and the floor-hour mark attached.

    The REST payload's own ``markPrice`` field is deliberately not used: the sealed snapshot's
    ``mark_price`` is the open of the 1h mark kline at the settlement's floor hour, joined by
    ``_attach_mark_prices``, and using a second definition of the same column would put two
    different numbers under one name across the seam.
    """
    frames: list[pd.DataFrame] = []
    for symbol in symbols:
        events = client.funding_rate(symbol, start=start - context, end_exclusive=end)
        if not events:
            continue
        frame = pd.DataFrame(
            {
                "funding_time": epoch_to_utc(
                    pd.Series([int(item["fundingTime"]) for item in events]), "funding_time"
                ),
                "symbol": symbol,
                "funding_rate": pd.to_numeric(
                    pd.Series([item["fundingRate"] for item in events]), errors="raise"
                ),
                "funding_interval_hours": np.nan,
            }
        )
        frame = derive_funding_intervals(frame, symbol=symbol)
        in_window = (frame["funding_time"] >= start) & (frame["funding_time"] < end)
        kept = frame.loc[in_window]
        if not kept.empty:
            frames.append(kept)
    if not frames:
        return empty_frame(FUNDING)
    events = pd.concat(frames, ignore_index=True).sort_values(["funding_time", "symbol"])
    return conform_frame(FUNDING, attach_mark_prices(events.reset_index(drop=True), hourly))


def _fetch_contract_metadata(
    client: PublicMarketDataClient, bars: pd.DataFrame, end: pd.Timestamp
) -> pd.DataFrame:
    """Contract metadata through the acquisition's own two lifecycle branches.

    A symbol still in live exchangeInfo gets its exchange record; one that has left it is
    archive-inferred from its own bars, exactly as the sealed metadata was built.
    """
    if bars.empty:
        return empty_frame(CONTRACT_METADATA)
    payload = client.exchange_info()
    current = {
        str(item["symbol"]): item
        for item in payload["symbols"]
        if isinstance(item, Mapping) and item.get("symbol")
    }
    return conform_frame(CONTRACT_METADATA, contract_metadata_frame(bars, current, end))


def _require_alignment(times: pd.Series, interval_hours: int, label: str) -> None:
    if times.empty:
        return
    aligned = (
        (times.dt.minute == 0)
        & (times.dt.second == 0)
        & (times.dt.microsecond == 0)
        & (times.dt.hour % interval_hours == 0)
    )
    if not aligned.all():
        raise ValueError(f"misaligned {interval_hours}h timestamp in {label}")


def _milliseconds(timestamp: pd.Timestamp) -> int:
    return int(utc(timestamp).value // _MILLISECOND)


def _barred_message(body: str) -> str:
    """Render a 418 body with its expiry as a readable UTC timestamp when one is present."""
    match = re.search(r"until\s+(\d{10,})", body)
    if match is None:
        return f"address is barred from public market data: {body[:200]}"
    until = pd.Timestamp(int(match.group(1)), unit="ms", tz="UTC")
    return (
        f"address is barred from public market data until {until.isoformat()}; "
        "further requests extend it, so this is not retried"
    )


def _retry_delay(retry_after: str | None, attempt: int) -> float:
    if retry_after is not None:
        try:
            return min(max(float(retry_after), 0.0), 120.0)
        except ValueError:
            pass
    return min(2.0**attempt, 30.0)


# ------------------------------------------------------------------------------------------------
# append-invariant persistence
# ------------------------------------------------------------------------------------------------


def append_frame(path: str | Path, frame: pd.DataFrame, *, name: str | None = None) -> AppendResult:
    """Append only genuinely new rows, or abort naming the key and column that changed.

    Rows already on disk are compared value for value against the incoming ones under the frame's
    natural key. A difference is :class:`AppendInvarianceError` and nothing is written -- the stored
    file is left exactly as it was, and the exception carries both values.

    The single exception is a lifecycle transition an entry in
    :data:`CONTRACT_LIFECYCLE_TRANSITIONS` classifies in full. Such a row is rewritten in place,
    counted in :attr:`AppendResult.transitioned`, and nothing else about it moves.
    """
    target = Path(path)
    resolved = name or infer_frame_name(frame)
    schema = frame_schema(resolved)
    key = list(schema.key)

    incoming = conform_frame(resolved, frame)
    if incoming.duplicated(key).any():
        example = tuple(incoming.loc[incoming.duplicated(key, keep=False), key].iloc[0])
        raise ValueError(
            f"incoming {resolved} rows carry duplicate {schema.key} keys, e.g. {example}"
        )

    existing = (
        conform_frame(resolved, pd.read_parquet(target))
        if target.is_file()
        else empty_frame(resolved)
    )
    transitions = _resolve_overlap(schema, existing, incoming, target)
    settled = _apply_transitions(schema, existing, transitions)

    additions = incoming.merge(existing.loc[:, key], on=key, how="left", indicator=True)
    additions = additions.loc[additions["_merge"] == "left_only", list(schema.columns)]
    combined = pd.concat([settled, additions], ignore_index=True) if len(additions) else settled
    result = conform_frame(resolved, combined.sort_values(list(schema.order), kind="stable"))
    if not target.is_file() or not result.equals(existing):
        _write_parquet(result, target)
    return AppendResult(
        path=target,
        name=resolved,
        appended=int(len(additions)),
        unchanged=int(len(incoming) - len(additions) - len(transitions)),
        total=int(len(result)),
        transitioned=int(len(transitions)),
    )


def _resolve_overlap(
    schema: FrameSchema, existing: pd.DataFrame, incoming: pd.DataFrame, path: Path
) -> list[tuple[Mapping[str, Any], Mapping[str, Any]]]:
    """Compare every already-recorded row against its refetch.

    Returns ``(key, adopted values)`` for each row that made a declared lifecycle transition, and
    raises :class:`AppendInvarianceError` for every other difference. An unchanged overlap returns
    an empty list, which is the ordinary case on every tick.
    """
    if existing.empty or incoming.empty:
        return []
    key = list(schema.key)
    overlap = existing.merge(
        incoming, on=key, how="inner", suffixes=("__recorded", "__fetched"), validate="one_to_one"
    )
    if overlap.empty:
        return []
    differing = {
        column: ~_element_equal(overlap[f"{column}__recorded"], overlap[f"{column}__fetched"])
        for column in schema.values
    }
    changed = pd.Series(False, index=overlap.index)
    for mask in differing.values():
        changed |= mask
    if not changed.any():
        return []

    transitions: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for position in overlap.index[changed]:
        row = overlap.loc[position]
        columns = [column for column in schema.values if differing[column].loc[position]]
        adopted, offending = _classify_change(schema, row, columns)
        if adopted is None:
            raise AppendInvarianceError(
                name=schema.name,
                path=path,
                key={field: row[field] for field in key},
                column=offending,
                existing=row[f"{offending}__recorded"],
                incoming=row[f"{offending}__fetched"],
            )
        if adopted:
            transitions.append(({field: row[field] for field in key}, adopted))
    return transitions


def _classify_change(
    schema: FrameSchema, row: pd.Series, columns: Sequence[str]
) -> tuple[Mapping[str, Any] | None, str]:
    """Decide whether one row's changes are a declared transition, and which values to adopt.

    Returns ``(None, column)`` naming the column that refused, so the abort message points at the
    fact that actually changed rather than at the transition machinery. An empty adoption mapping
    means the differences are tolerated and nothing needs rewriting -- the already-settled refetch
    of a row that transitioned on an earlier tick.
    """
    for transition in CONTRACT_LIFECYCLE_TRANSITIONS:
        if transition.frame != schema.name:
            continue
        trigger = transition.trigger_column
        before, after = row[f"{trigger}__recorded"], row[f"{trigger}__fetched"]
        fired = transition.fired(before, after)
        if not fired and not transition.settled(before, after):
            continue
        adopted: dict[str, Any] = {trigger: after} if fired else {}
        for column in columns:
            if column == trigger:
                continue
            recorded = row[f"{column}__recorded"]
            fetched = row[f"{column}__fetched"]
            if column in transition.deferred:
                # Permitted to differ, deliberately not adopted -- see the module docstring. The
                # only bucket tolerated once the transition has already settled.
                if pd.isna(recorded) or pd.isna(fetched) or fetched < recorded:
                    return None, column
            elif not fired:
                return None, column
            elif column in transition.followed:
                if (recorded, fetched) not in transition.followed[column]:
                    return None, column
                adopted[column] = fetched
            elif column in transition.advanced:
                if pd.isna(fetched) or not (pd.isna(recorded) or fetched < recorded):
                    return None, column
                adopted[column] = fetched
            else:
                return None, column
        return adopted, trigger
    return None, _offending_column(schema, columns)


def _offending_column(schema: FrameSchema, columns: Sequence[str]) -> str:
    """Which changed column to name when nothing classified the change.

    A trigger column that moved is preferred: when a state machine runs backwards -- an
    ``archive_inference`` row reported live again -- several columns move together, and the one
    worth naming is the state itself rather than whichever happens to sort first.
    """
    triggers = {
        transition.trigger_column
        for transition in CONTRACT_LIFECYCLE_TRANSITIONS
        if transition.frame == schema.name
    }
    return next((column for column in columns if column in triggers), columns[0])


def _apply_transitions(
    schema: FrameSchema,
    existing: pd.DataFrame,
    transitions: Sequence[tuple[Mapping[str, Any], Mapping[str, Any]]],
) -> pd.DataFrame:
    """Rewrite exactly the transitioned rows, leaving every other recorded row untouched."""
    if not transitions:
        return existing
    result = existing.copy()
    for key, adopted in transitions:
        selector = pd.Series(True, index=result.index)
        for field, value in key.items():
            selector &= result[field] == value
        for column, value in adopted.items():
            result.loc[selector, column] = value
    return conform_frame(schema.name, result)


def _element_equal(recorded: pd.Series, fetched: pd.Series) -> pd.Series:
    """Elementwise equality treating two nulls as equal.

    Without the null clause every already-recorded ``NaT`` delivery date would read as a revision
    of itself and abort the desk on its first repeat fetch.
    """
    return (recorded == fetched) | (recorded.isna() & fetched.isna())


def _write_parquet(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    frame.to_parquet(temporary, index=False)
    os.replace(temporary, path)


# ------------------------------------------------------------------------------------------------
# cache manifest
# ------------------------------------------------------------------------------------------------


def cache_manifest(root: str | Path) -> dict[str, Any]:
    """Bind every cache file by path, size, row count and SHA-256.

    The manifest's own stored copy is excluded, so a manifest written INTO the cache it describes
    does not invalidate itself the moment it lands.
    """
    base = Path(root)
    return {
        "schema_version": CACHE_SCHEMA_VERSION,
        "files": [
            {
                "path": relative,
                "size": path.stat().st_size,
                "rows": _file_rows(path),
                "sha256": _file_digest(path),
            }
            for relative, path in sorted(_cache_files(base).items())
        ],
    }


def verify_cache_manifest(root: str | Path, manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    """Refuse unless every bound file is byte-for-byte the one recorded, and no other file exists.

    Checks are ordered size, digest, rows so that a truncated or corrupt file is named by a cheap
    comparison rather than by an exception thrown while trying to parse it.
    """
    base = Path(root)
    if not isinstance(manifest, Mapping):
        raise CacheDriftError("cache manifest must be a mapping")
    if manifest.get("schema_version") != CACHE_SCHEMA_VERSION:
        raise CacheDriftError(
            f"cache manifest schema drift: {manifest.get('schema_version')!r} is not "
            f"{CACHE_SCHEMA_VERSION!r}"
        )
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise CacheDriftError("cache manifest has no file list")

    bound: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise CacheDriftError("cache manifest holds a non-object entry")
        relative = entry.get("path")
        if (
            not isinstance(relative, str)
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise CacheDriftError(f"cache manifest binds an unsafe path: {relative!r}")
        if relative in bound:
            raise CacheDriftError(f"cache manifest binds {relative} twice")
        bound.add(relative)
        path = base / relative
        if not path.is_file():
            raise CacheDriftError(f"cache file is missing: {relative}")
        size = path.stat().st_size
        if size != entry.get("size"):
            raise CacheDriftError(
                f"cache size drift: {relative} is {size} bytes, manifest binds {entry.get('size')}"
            )
        if _file_digest(path) != entry.get("sha256"):
            raise CacheDriftError(f"cache content drift: {relative} does not match its SHA-256")
        rows = _file_rows(path)
        if rows != entry.get("rows"):
            raise CacheDriftError(
                f"cache row-count drift: {relative} holds {rows} rows, manifest binds "
                f"{entry.get('rows')}"
            )
    unbound = sorted(set(_cache_files(base)) - bound)
    if unbound:
        raise CacheDriftError(f"cache holds files the manifest does not bind: {unbound}")
    return manifest


def _cache_files(base: Path) -> dict[str, Path]:
    if not base.is_dir():
        raise CacheDriftError(f"cache root is not a directory: {base}")
    found: dict[str, Path] = {}
    for path in base.rglob("*"):
        if not path.is_file() or path.name.startswith("."):
            continue
        relative = path.relative_to(base).as_posix()
        if relative == MANIFEST_FILENAME:
            continue
        found[relative] = path
    return found


def _file_rows(path: Path) -> int | None:
    """Row count where the format has one; ``None`` where it does not."""
    if path.suffix == ".parquet":
        return int(pq.ParquetFile(path).metadata.num_rows)
    if path.suffix == ".jsonl":
        return sum(1 for line in path.read_text().splitlines() if line.strip())
    if path.suffix == ".json":
        payload = json.loads(path.read_text())
        if isinstance(payload, list | Mapping):
            return len(payload)
        return None
    return None


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()
