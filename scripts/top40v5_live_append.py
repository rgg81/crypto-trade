"""Extend the forward snapshot to *now* from live REST, so the desks never wait on an archive.

The canonical builder is archive-based and cannot pass the last complete month: Binance publishes a
month's ZIPs only after that month closes. For a paper desk that is a month of blindness, which is
not a trade-off worth taking — so this path fills the tail from REST instead.

Where each field comes from, and why:

``bars``
    8h klines from the **local binance-proxy**. Repeated wide fetches direct to Binance are what
    earned 418 bans on other desks; the proxy is a cache in front of exactly this call.
``funding``
    ``/fapi/v1/fundingRate`` **direct from Binance**. The proxy does not serve it, and the snapshot
    builder refuses a non-official funding host anyway — funding provenance is load-bearing.
``mark_prices``
    Derived from the funding response's ``markPrice``, not fetched. Verified against the frozen
    snapshot first: 673,704 joined rows, **max absolute difference 0.0, 100% exact**. Funding
    settles on the 8h grid, so its mark *is* the boundary mark. This also removes the need for
    ``markPriceKlines``, which the proxy answers 404 on.
``membership``
    Recomputed by calling ``seasoned_membership()`` — the same function the canonical builder uses,
    over the extended history. Not reimplemented: a second implementation of the universe rule is
    how a desk quietly starts trading a different universe from the one it was selected on.

**Provenance is weaker here and the record says so.** Archive rows are checksum-verified against
Binance's published sidecars; these are REST reads with no such proof. Every run writes
``live-append.json`` recording exactly which timestamp range came from REST, so the two are never
silently conflated. The frozen snapshot is never touched.

Usage::

    uv run python scripts/top40v5_live_append.py --check
    uv run python scripts/top40v5_live_append.py
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd

from crypto_trade.tournament.data import is_eligible_usdt_perpetual
from crypto_trade.tournament.v5.universe import seasoned_membership

REPO = Path(__file__).resolve().parents[1]
FROZEN = REPO / "data" / "top40" / "snapshot-v3"
FORWARD = REPO / "data" / "top40" / "forward"
PROXY = "http://127.0.0.1:8000"
BINANCE = "https://fapi.binance.com"
INTERVAL_HOURS = 8
# Symbols that have traded recently are the only ones that can enter the liquid pool; a contract
# with no bars in four months cannot rank in a 90-day trailing median.
RECENT_DAYS = 120
# Must match [universe] persistence_window_weeks in SNAPSHOT-BUILD.toml.
PERSISTENCE_WINDOW_WEEKS = 10

BAR_COLUMNS = [
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
]


# Binance's "this symbol does not exist" code. A contract that delisted during the gap answers
# this for every request, and retrying it three times then aborting the whole run would let one
# dead symbol block the other 644 -- which is exactly what happened on the first attempt, with
# AERGOUSDT. Delisting is ordinary data, not a fault.
INVALID_SYMBOL = -1121


def _get(url: str, *, retries: int = 5) -> list | dict | None:
    """Fetch, retrying transient failures. Returns None for a symbol Binance does not have."""

    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=45) as response:
                return json.loads(response.read())
        except urllib.error.HTTPError as error:
            if error.code == 400:
                try:
                    if json.loads(error.read()).get("code") == INVALID_SYMBOL:
                        return None
                except (json.JSONDecodeError, ValueError):
                    pass
            last = error
            time.sleep(0.6 * (attempt + 1))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last = error
            time.sleep(0.6 * (attempt + 1))
    raise RuntimeError(f"failed after {retries}: {url[:120]}") from last


def _live_contracts() -> dict[str, dict]:
    """Currently-listed USD-M perpetuals, from Binance's own exchangeInfo.

    Without this the tradable universe is a closed set. Every other symbol list in this script is
    derived from the snapshot already on disk, so a contract listed after the snapshot has no bars,
    is therefore never fetched, therefore never accumulates history, and can never qualify -- while
    the seasoned rule the desks were selected on admits new listings as soon as they season.

    The lag hides it. A name listed today needs 90 days of history and persistence over the ten
    prior weeks, so the first divergence lands about five months out -- inside the forward year, and
    silently, because nothing errors: the universe just quietly stops admitting anyone.

    exchangeInfo goes direct to Binance, matching where funding goes and where the snapshot builder
    requires its own metadata to come from. The proxy is a klines cache and is not this.

    ``is_eligible_usdt_perpetual`` carries the charter's fail-closed native-crypto classification
    and is not optional. exchangeInfo's own fields are not sufficient: Binance reports
    ``underlyingType == "COIN"`` for USDCUSDT, USTCUSDT, PAXGUSDT and XAUTUSDT alike, so a filter
    built from them admits stablecoin pegs and gold-backed tokens into a Top-40 book ranked on
    quote volume -- a peg pair carries enormous volume and almost no volatility, which at a common
    ex-ante risk unit sizes into an enormous position. Measured against live exchangeInfo: of the
    nine listings absent from the snapshot, this rule rejects seven, four of them for exactly that
    reason and three for a non-ASCII name.
    """

    payload = _get(f"{BINANCE}/fapi/v1/exchangeInfo")
    if not isinstance(payload, dict):
        raise RuntimeError("exchangeInfo did not return an object")
    contracts: dict[str, dict] = {}
    for info in payload.get("symbols", []):
        symbol = str(info["symbol"])
        if (
            info.get("contractType") == "PERPETUAL"
            and info.get("quoteAsset") == "USDT"
            and info.get("marginAsset") == "USDT"
            and info.get("underlyingType") == "COIN"
            and is_eligible_usdt_perpetual(symbol)
            and "_" not in symbol
        ):
            contracts[symbol] = info
    return contracts


def _metadata_rows(contracts: dict[str, dict], symbols: list[str]) -> pd.DataFrame:
    """Metadata rows for symbols the forward snapshot has never seen.

    Mirrors ``snapshot._contract_metadata``'s ``current_exchangeInfo`` branch. It is not reused
    directly because it raises on any non-crypto symbol, and aborting the whole append because
    Binance listed one index product is the AERGOUSDT failure again: the callers here already
    filtered to COIN-underlying perpetuals, so anything else is simply not ours.
    """

    rows = []
    for symbol in symbols:
        info = contracts[symbol]
        onboard = pd.to_datetime(info.get("onboardDate"), unit="ms", utc=True)
        delivery = pd.to_datetime(info.get("deliveryDate"), unit="ms", utc=True)
        rows.append(
            {
                "symbol": symbol,
                "contract_type": "PERPETUAL",
                "quote_asset": "USDT",
                "margin_asset": "USDT",
                "is_crypto": True,
                "onboard_date": onboard,
                # Store the far-future sentinel exactly as the canonical builder does -- NaT only
                # when Binance omits the field. Collapsing the sentinel to NaT looked tidier and
                # was a divergence: 514 of 671 snapshot rows carry 2100-12-25 and exactly one is
                # NaT, so new listings would have been the only rows shaped differently. It is
                # benign downstream today (data.py treats isna() and > as_of alike) and it is the
                # same shape as both universe defects -- an incremental path quietly applying a
                # different rule from the from-scratch builder.
                "delivery_date": pd.NaT if pd.isna(delivery) else delivery,
                "underlying_type": "COIN",
                "metadata_source": "current_exchangeInfo",
            }
        )
    frame = pd.DataFrame(rows)
    # Force tz-awareness rather than letting pandas infer it from the values.
    #
    # Every perpetual has a sentinel deliveryDate, so delivery_date is all-NaT, and pandas types an
    # all-NaT column as tz-NAIVE datetime64[ns]. _match_dtypes then tries to astype it to the
    # snapshot's tz-aware dtype and pandas refuses naive -> aware outright. That crashed the append
    # on the first run with a new listing and left the desks 40h stale.
    for column in ("onboard_date", "delivery_date"):
        frame[column] = pd.to_datetime(frame[column], utc=True)
    return frame


def _klines(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """8h klines from the proxy, paged. Only closed bars are kept."""

    rows: list[list] = []
    cursor = start_ms
    while cursor < end_ms:
        url = (
            f"{PROXY}/fapi/v1/klines?symbol={symbol}&interval={INTERVAL_HOURS}h"
            f"&startTime={cursor}&endTime={end_ms}&limit=1000"
        )
        page = _get(url)
        if not page:
            break
        rows.extend(page)
        last_open = int(page[-1][0])
        if len(page) < 1000:
            break
        cursor = last_open + INTERVAL_HOURS * 3_600_000
    if not rows:
        return pd.DataFrame(columns=BAR_COLUMNS)
    frame = pd.DataFrame(
        rows,
        columns=[
            "open_time",
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
            "ignore",
        ],
    )
    frame["symbol"] = symbol
    frame["open_time"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
    frame["close_time"] = pd.to_datetime(frame["close_time"], unit="ms", utc=True)
    for column in (
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "taker_buy_volume",
        "taker_buy_quote_volume",
    ):
        frame[column] = frame[column].astype(float)
    frame["trade_count"] = frame["trade_count"].astype("int64")
    return frame[BAR_COLUMNS]


def _funding(symbol: str, start_ms: int, end_ms: int) -> pd.DataFrame:
    """Funding direct from Binance. Its markPrice is the 8h boundary mark."""

    rows: list[dict] = []
    cursor = start_ms
    while cursor < end_ms:
        url = (
            f"{BINANCE}/fapi/v1/fundingRate?symbol={symbol}"
            f"&startTime={cursor}&endTime={end_ms}&limit=1000"
        )
        page = _get(url)
        if not page:
            break
        rows.extend(page)
        if len(page) < 1000:
            break
        cursor = int(page[-1]["fundingTime"]) + 1
    if not rows:
        return pd.DataFrame(
            columns=[
                "funding_time",
                "symbol",
                "funding_rate",
                "mark_price",
                "mark_time",
                "settlement_time",
                "funding_interval_hours",
            ]
        )
    frame = pd.DataFrame(rows)
    frame["funding_time"] = pd.to_datetime(frame["fundingTime"], unit="ms", utc=True)
    # The frozen snapshot floors the mark to the settlement hour; match it exactly so the two
    # halves of the ledger join on the same key.
    frame["mark_time"] = frame["funding_time"].dt.floor("h")
    frame["settlement_time"] = frame["funding_time"]
    frame["symbol"] = frame["symbol"].astype(str)
    frame["funding_rate"] = frame["fundingRate"].astype(float)
    frame["mark_price"] = frame["markPrice"].astype(float)
    frame["funding_interval_hours"] = float(INTERVAL_HOURS)
    return frame[
        [
            "funding_time",
            "symbol",
            "funding_rate",
            "mark_price",
            "mark_time",
            "settlement_time",
            "funding_interval_hours",
        ]
    ]


def _match_dtypes(new: pd.DataFrame, existing: pd.DataFrame) -> pd.DataFrame:
    """Cast appended rows to the existing frame's dtypes, datetime resolution included.

    This is not housekeeping. ``pd.to_datetime(..., unit="ms")`` yields ``datetime64[us]`` while the
    archive-built snapshot is ``datetime64[ns]``, and concatenating upcasts the whole column. Every
    value stays identical -- verified column by column -- but the engine's timestamp lookups and
    joins run against a differently-typed index, and net_return moved by ~10% on rows that had
    already been published. The append-invariant ledger caught it and refused to publish; without
    that guard the desks would have carried a silently different history.
    """

    for column in existing.columns:
        if column in new.columns and new[column].dtype != existing[column].dtype:
            new[column] = new[column].astype(existing[column].dtype)
    return new


def _seed_forward() -> None:
    if (FORWARD / "bars.parquet").is_file():
        return
    FORWARD.mkdir(parents=True, exist_ok=True)
    for name in ("bars", "funding", "mark_prices", "membership", "contract_metadata"):
        source = FROZEN / f"{name}.parquet"
        if source.is_file():
            shutil.copy2(source, FORWARD / f"{name}.parquet")
    print(f"seeded {FORWARD.relative_to(REPO)} from the frozen snapshot")


def extend_membership(
    membership: pd.DataFrame,
    bars: pd.DataFrame,
    metadata: pd.DataFrame,
    last_closed: pd.Timestamp,
) -> pd.DataFrame:
    """Add the reconstitution weeks that the extended bars now support.

    **Persistence has to be armed before the first new week.** ``seasoned_membership`` applies the
    persistence rule only once a week has ``persistence_window_weeks`` of PRIOR reconstitutions
    inside the grid it was handed, and exempts the first ten because no prior history exists to
    judge them against. Hand it only the new weeks and none of them ever has ten priors, so
    persistence silently does not apply and every new week is admitted under a laxer rule than
    every week before it.

    Measured, not theorised: the four weeks from 2026-08-03 came out with three to five wrong
    symbols each -- admitting newly liquid names like ALLOUSDT and ESPORTSUSDT while dropping
    established ones like 1000SHIBUSDT and XMRUSDT. That is the RIVER failure the seasoned rule
    exists to prevent, reintroduced by the shape of the call rather than by the rule.

    So the grid is armed backwards by the persistence window and the extension discarded, which is
    what the canonical builder does. A universe that differs between the two paths is a desk
    trading something it was not selected on.
    """

    first_new = (membership["reconstitution_time"].max() + pd.Timedelta(days=7)).normalize()
    last_day = pd.Timestamp(last_closed).floor("D")
    last_monday = last_day - pd.Timedelta(days=last_day.weekday())
    if first_new > last_monday:
        print("  no new reconstitution week yet")
        return membership

    grid = pd.date_range(first_new, last_monday, freq="7D", tz="UTC")
    armed = pd.date_range(
        first_new - pd.Timedelta(weeks=PERSISTENCE_WINDOW_WEEKS),
        last_monday,
        freq="7D",
        tz="UTC",
    )
    fresh = seasoned_membership(bars, metadata, armed)
    fresh = fresh[fresh["reconstitution_time"].isin(grid)]
    fresh = _match_dtypes(fresh.copy(), membership)
    combined = (
        pd.concat([membership, fresh], ignore_index=True)
        .drop_duplicates(subset=["reconstitution_time", "symbol"], keep="last")
        .sort_values(["reconstitution_time", "liquidity_rank"])
        .reset_index(drop=True)
    )
    print(f"  {len(grid)} new reconstitution(s), {len(fresh)} member rows")
    return combined


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--workers", type=int, default=8)
    arguments = parser.parse_args()

    _seed_forward()
    bars = pd.read_parquet(FORWARD / "bars.parquet")
    metadata = pd.read_parquet(FORWARD / "contract_metadata.parquet")
    last_bar = pd.Timestamp(bars["open_time"].max())
    now = pd.Timestamp.now(tz="UTC")
    last_closed = now.floor(f"{INTERVAL_HOURS}h") - pd.Timedelta(hours=INTERVAL_HOURS)

    print(f"forward snapshot through {last_bar}")
    print(f"last closed boundary     {last_closed}")
    if last_bar >= last_closed:
        # Bars are current, but membership might not be, and the two are separate obligations.
        #
        # The membership recompute lives at the end of the fetch path, so returning here on
        # "nothing to fetch" also skips it -- and once bars are current there is no longer any path
        # that reaches it. Any week that was missed, or that has to be recomputed because the rule
        # was applied wrongly, stays wrong permanently while this prints a reassuring line.
        membership = pd.read_parquet(FORWARD / "membership.parquet")
        extended = extend_membership(membership, bars, metadata, last_closed)
        # Compare contents, not row counts: a recompute that replaced a week with a same-sized but
        # different one is exactly the failure this branch exists to repair, and counting rows
        # would call it a no-op.
        if not extended.equals(membership):
            extended.to_parquet(FORWARD / "membership.parquet")
            print("membership extended; bars were already current")
        else:
            print("already current; nothing to fetch")
        return 0

    start = last_bar + pd.Timedelta(hours=INTERVAL_HOURS)
    span = int((last_closed - start) / pd.Timedelta(hours=INTERVAL_HOURS)) + 1
    print(f"gap {start} -> {last_closed}  ({span} bars)")

    recent = bars[bars["open_time"] >= last_bar - pd.Timedelta(days=RECENT_DAYS)]
    known = set(recent["symbol"].astype(str).unique())
    contracts = _live_contracts()
    listed = set(contracts)
    newly_listed = sorted(listed - set(metadata["symbol"].astype(str)))
    symbols = sorted(known | listed)
    print(
        f"{len(known)} symbols traded in the last {RECENT_DAYS}d, "
        f"{len(listed)} listed on Binance now, {len(symbols)} to fetch"
    )
    if newly_listed:
        print(f"  new listings since the snapshot: {', '.join(newly_listed)}")

    if arguments.check:
        print("check only; nothing fetched")
        return 0

    start_ms, end_ms = int(start.timestamp() * 1000), int((last_closed.timestamp() + 1) * 1000)

    failed: list[str] = []

    def _safe(fetch, symbol):  # type: ignore[no-untyped-def]
        try:
            return fetch(symbol, start_ms, end_ms)
        except RuntimeError:
            failed.append(symbol)
            return None

    print(f"fetching klines from the proxy ({arguments.workers} workers)...", flush=True)
    with ThreadPoolExecutor(max_workers=arguments.workers) as pool:
        kline_frames = list(pool.map(lambda s: _safe(_klines, s), symbols))
    new_bars = pd.concat(
        [f for f in kline_frames if f is not None and not f.empty], ignore_index=True
    )
    print(f"  {len(new_bars):,} new bars across {new_bars['symbol'].nunique()} symbols")

    # Funding goes direct, so fewer workers: this is the one call with no cache in front of it.
    print("fetching funding direct from Binance (4 workers)...", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        funding_frames = list(pool.map(lambda s: _safe(_funding, s), symbols))
    new_funding = pd.concat(
        [f for f in funding_frames if f is not None and not f.empty], ignore_index=True
    )
    print(f"  {len(new_funding):,} new funding rows")

    # A symbol that could not be fetched is reported, never swallowed. If one of them is a current
    # member the run stops: a missing member is a hole in the universe the desks trade, and
    # publishing over it would be the quiet kind of wrong.
    if failed:
        members = pd.read_parquet(FORWARD / "membership.parquet")
        latest_week = members["reconstitution_time"].max()
        current = set(
            members[members["reconstitution_time"] == latest_week]["symbol"].astype(str)
        )
        blocking = sorted(set(failed) & current)
        print(f"  {len(set(failed))} symbol(s) could not be fetched: {sorted(set(failed))[:8]}")
        if blocking:
            print(f"ABORT: {len(blocking)} of them are current members: {blocking}")
            return 1

    new_bars = _match_dtypes(new_bars, bars)
    combined_bars = (
        pd.concat([bars, new_bars], ignore_index=True)
        .drop_duplicates(subset=["open_time", "symbol"], keep="last")
        .sort_values(["open_time", "symbol"])
        .reset_index(drop=True)
    )
    funding = pd.read_parquet(FORWARD / "funding.parquet")
    new_funding = _match_dtypes(new_funding, funding)
    combined_funding = (
        pd.concat([funding, new_funding], ignore_index=True)
        .drop_duplicates(subset=["funding_time", "symbol"], keep="last")
        .sort_values(["funding_time", "symbol"])
        .reset_index(drop=True)
    )
    # Marks are the funding response's own markPrice; verified identical to the frozen snapshot's
    # markPriceKlines-derived column on every one of 673,704 overlapping rows.
    new_marks = new_funding[["mark_time", "symbol", "mark_price"]]
    marks = pd.read_parquet(FORWARD / "mark_prices.parquet")
    new_marks = _match_dtypes(new_marks.copy(), marks)
    combined_marks = (
        pd.concat([marks, new_marks], ignore_index=True)
        .drop_duplicates(subset=["mark_time", "symbol"], keep="last")
        .sort_values(["mark_time", "symbol"])
        .reset_index(drop=True)
    )

    # Metadata has to grow before membership is recomputed: seasoned_membership joins on it, so a
    # symbol with bars but no metadata row is silently unselectable and the new-listing fix above
    # would fetch data nobody can ever trade.
    admitted = [s for s in newly_listed if s in set(combined_bars["symbol"].astype(str))]
    if admitted:
        fresh_metadata = _match_dtypes(_metadata_rows(contracts, admitted), metadata)
        metadata = (
            pd.concat([metadata, fresh_metadata], ignore_index=True)
            .drop_duplicates(subset=["symbol"], keep="first")
            .sort_values("symbol")
            .reset_index(drop=True)
        )
        metadata.to_parquet(FORWARD / "contract_metadata.parquet")
        print(f"  added contract metadata for {len(admitted)} new listing(s)")

    print("recomputing membership over the extended history...", flush=True)
    membership = pd.read_parquet(FORWARD / "membership.parquet")
    combined_membership = extend_membership(membership, combined_bars, metadata, last_closed)

    combined_bars.to_parquet(FORWARD / "bars.parquet")
    combined_funding.to_parquet(FORWARD / "funding.parquet")
    combined_marks.to_parquet(FORWARD / "mark_prices.parquet")
    combined_membership.to_parquet(FORWARD / "membership.parquet")

    provenance_path = FORWARD / "live-append.json"
    provenance = (
        json.loads(provenance_path.read_text(encoding="utf-8"))
        if provenance_path.is_file()
        else {
            "archive_verified_through": str(last_bar if not provenance_path.is_file() else ""),
            "appends": [],
        }
    )
    provenance.setdefault("appends", []).append(
        {
            "at": str(now),
            "range": [str(start), str(last_closed)],
            "bars": int(len(new_bars)),
            "funding": int(len(new_funding)),
            "sources": {
                "bars": f"{PROXY} /fapi/v1/klines",
                "funding": f"{BINANCE} /fapi/v1/fundingRate",
                "mark_prices": "derived from funding markPrice",
            },
            "note": "REST reads; not checksum-verified against Binance archive sidecars",
        }
    )
    provenance_path.write_text(json.dumps(provenance, indent=2, sort_keys=True), encoding="utf-8")

    print(f"\nforward snapshot now through {combined_bars['open_time'].max()}")
    print(f"wrote {provenance_path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
