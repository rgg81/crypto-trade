"""Checksum-bound reuse and exact terminal-gap acquisition for CUP-50."""

from __future__ import annotations

import concurrent.futures
import csv
import datetime as dt
import hashlib
import json
import shutil
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.cup50.availability import UnavailabilityWindow, unavailable_symbols
from crypto_trade.cup50.config import OOS_END
from crypto_trade.cup50.replay import _normalise_funding, decision_grid
from crypto_trade.cup50.snapshot import load_snapshot, stitch_snapshots
from crypto_trade.cup50.universe import members_at

FUNDING_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
MARK_URL = "https://fapi.binance.com/fapi/v1/markPriceKlines"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _canonical(payload: object) -> bytes:
    return (
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _fetch(endpoint: str, params: Mapping[str, object]) -> tuple[object, bytes]:
    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    request = urllib.request.Request(url, headers={"User-Agent": "cup50-acquisition-v1"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                raw = response.read()
            break
        except urllib.error.HTTPError:
            raise
        except (TimeoutError, urllib.error.URLError):
            if attempt == 4:
                raise
            time.sleep(0.5 * (2**attempt))
    else:  # pragma: no cover - the final attempt either returns or raises
        raise AssertionError("unreachable REST retry state")
    payload = json.loads(raw)
    return payload, _canonical(payload)


def _parse_mark(payload: object, *, symbol: str, terminal_ms: int) -> dict[str, object]:
    if not isinstance(payload, list) or len(payload) != 1 or not isinstance(payload[0], list):
        raise ValueError(f"terminal mark response is not one kline: {symbol}")
    row = payload[0]
    if len(row) != 12 or row[0] != terminal_ms or row[6] != terminal_ms + 3_600_000 - 1:
        raise ValueError(f"terminal mark response has wrong bounds: {symbol}")
    price = float(row[1])
    if not np.isfinite(price) or price <= 0:
        raise ValueError(f"terminal mark response has invalid open: {symbol}")
    return {
        "mark_time": pd.Timestamp(terminal_ms, unit="ms", tz="UTC"),
        "symbol": symbol,
        "mark_price": price,
    }


def _parse_funding(
    payload: object,
    *,
    symbol: str,
    lower_ms: int,
    upper_ms: int,
    mark_prices: Mapping[tuple[pd.Timestamp, str], float] | None = None,
) -> list[dict[str, object]]:
    if not isinstance(payload, list):
        raise ValueError(f"terminal funding response is not a list: {symbol}")
    rows: list[dict[str, object]] = []
    previous = -1
    for item in payload:
        if not isinstance(item, dict) or item.get("symbol") != symbol:
            raise ValueError(f"terminal funding response has a foreign row: {symbol}")
        timestamp = item.get("fundingTime")
        if not isinstance(timestamp, int) or not lower_ms <= timestamp <= upper_ms:
            raise ValueError(f"terminal funding response has an invalid time: {symbol}")
        if timestamp <= previous:
            raise ValueError(f"terminal funding response is not strictly ordered: {symbol}")
        previous = timestamp
        actual = pd.Timestamp(timestamp, unit="ms", tz="UTC")
        settlement = actual.floor("h")
        rate = float(item["fundingRate"])
        try:
            mark = float(item["markPrice"])
        except (TypeError, ValueError):
            mark = float((mark_prices or {}).get((settlement, symbol), np.nan))
        if not np.isfinite(rate) or not np.isfinite(mark) or mark <= 0:
            raise ValueError(f"terminal funding response has invalid values: {symbol}")
        jitter = actual - settlement
        if jitter < pd.Timedelta(0) or jitter >= pd.Timedelta(seconds=1):
            raise ValueError(f"terminal funding jitter exceeds one second: {symbol}")
        rows.append(
            {
                "funding_time": actual,
                "symbol": symbol,
                "funding_rate": rate,
                "mark_price": mark,
                "mark_time": settlement,
                "settlement_time": settlement,
                "funding_interval_hours": np.nan,
            }
        )
    return rows


def _request_symbol(symbol: str, terminal: pd.Timestamp) -> dict[str, object]:
    terminal_ms = int(terminal.value // 1_000_000)
    lower_ms = int((terminal - pd.Timedelta(hours=8)).value // 1_000_000)
    upper_ms = terminal_ms + 999
    mark_params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": terminal_ms,
        "endTime": terminal_ms + 3_600_000 - 1,
        "limit": 1,
    }
    funding_params = {
        "symbol": symbol,
        "startTime": lower_ms,
        "endTime": upper_ms,
        "limit": 100,
    }
    mark_payload, mark_raw = _fetch(MARK_URL, mark_params)
    funding_payload, funding_raw = _fetch(FUNDING_URL, funding_params)
    return {
        "symbol": symbol,
        "mark": _parse_mark(mark_payload, symbol=symbol, terminal_ms=terminal_ms),
        "funding": _parse_funding(
            funding_payload,
            symbol=symbol,
            lower_ms=lower_ms,
            upper_ms=upper_ms,
        ),
        "raw": {"mark": mark_raw, "funding": funding_raw},
        "params": {"mark": mark_params, "funding": funding_params},
    }


def _verified_sources(
    source: Path, manifest: Mapping[str, Any]
) -> tuple[dict[str, Path], dict[str, Mapping[str, Any]]]:
    entries = {
        str(entry.get("name")): entry
        for entry in manifest.get("files", [])
        if isinstance(entry, dict)
    }
    required = {"bars", "funding", "mark_prices", "contract_metadata"}
    if required - set(entries):
        raise ValueError("source manifest lacks a required reusable cache")
    paths: dict[str, Path] = {}
    for name, entry in entries.items():
        path = source / Path(str(entry["path"])).name
        if not path.is_file():
            continue
        if _sha256(path) != entry.get("sha256"):
            raise ValueError(f"reusable acquisition cache failed checksum: {name}")
        paths[name] = path
    if required - set(paths):
        raise ValueError("verified source acquisition files are incomplete")
    return paths, entries


def acquire_terminal_gaps(
    *,
    source_root: str | Path,
    source_manifest: str | Path,
    membership_path: str | Path,
    destination: str | Path,
    terminal: pd.Timestamp = OOS_END,
    workers: int = 8,
) -> Mapping[str, object]:
    """Reuse verified caches, then fetch only the exact active terminal gaps."""
    source, manifest_path, output = (
        Path(source_root),
        Path(source_manifest),
        Path(destination),
    )
    if output.exists():
        raise FileExistsError("CUP-50 acquisition destination must be new")
    if workers < 1 or workers > 16:
        raise ValueError("acquisition workers must be in 1..16")
    terminal = pd.Timestamp(terminal)
    if terminal.tzinfo is None:
        raise ValueError("terminal acquisition bound must be UTC-aware")
    terminal = terminal.tz_convert("UTC")
    manifest = json.loads(manifest_path.read_text())
    verified, entries = _verified_sources(source, manifest)
    membership = pd.read_parquet(membership_path)
    active = tuple(sorted(members_at(membership, terminal - pd.Timedelta(nanoseconds=1))))
    if len(active) != 50:
        raise ValueError(f"terminal CUP-50 membership has {len(active)} names")

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda symbol: _request_symbol(symbol, terminal), active))
    results.sort(key=lambda item: str(item["symbol"]))

    output.mkdir(parents=True)
    for name, path in sorted(verified.items()):
        shutil.copy2(path, output / path.name)
    shutil.copy2(manifest_path, output / "reused-source-manifest.json")

    raw_root = output / "raw" / "terminal-gap-rest"
    retrieved = dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")
    provenance: list[dict[str, object]] = []
    mark_rows, funding_rows = [], []
    for result in results:
        symbol = str(result["symbol"])
        mark_rows.append(result["mark"])
        funding_rows.extend(result["funding"])
        for kind, endpoint in (("mark", MARK_URL), ("funding", FUNDING_URL)):
            path = raw_root / kind / f"{symbol}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            raw = result["raw"][kind]
            path.write_bytes(raw)
            provenance.append(
                {
                    "endpoint": endpoint,
                    "kind": kind,
                    "params": result["params"][kind],
                    "raw_path": path.relative_to(output).as_posix(),
                    "retrieved_at": retrieved,
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "size": len(raw),
                    "symbol": symbol,
                }
            )

    funding = pd.read_parquet(output / "funding.parquet")
    additions = pd.DataFrame(funding_rows, columns=funding.columns)
    funding = pd.concat([funding, additions], ignore_index=True)
    funding = funding.drop_duplicates(["funding_time", "symbol"], keep="first")
    funding = funding.sort_values(["funding_time", "symbol"], ignore_index=True)
    settlement = pd.to_datetime(funding["settlement_time"], utc=True)
    prior = settlement.groupby(funding["symbol"].astype(str)).diff().dt.total_seconds().div(3600)
    funding.loc[funding["funding_interval_hours"].isna(), "funding_interval_hours"] = prior
    funding.to_parquet(output / "funding.parquet", index=False)

    marks = pd.read_parquet(output / "mark_prices.parquet")
    marks = pd.concat([marks, pd.DataFrame(mark_rows, columns=marks.columns)], ignore_index=True)
    marks = marks.drop_duplicates(["mark_time", "symbol"], keep="first")
    marks = marks.sort_values(["mark_time", "symbol"], ignore_index=True)
    marks.to_parquet(output / "mark_prices.parquet", index=False)

    provenance_path = output / "terminal-gap-provenance.jsonl"
    provenance_path.write_bytes(b"".join(_canonical(row) for row in provenance))
    file_entries = []
    logical_by_filename = {
        Path(str(entry["path"])).name: name for name, entry in entries.items()
    }
    for path in sorted(output.iterdir()):
        if not path.is_file() or path.name in {"manifest.json"}:
            continue
        name = logical_by_filename.get(path.name, path.stem)
        rows = None
        if path.suffix == ".parquet":
            rows = len(pd.read_parquet(path))
        elif path.suffix == ".jsonl":
            rows = len(path.read_text().splitlines())
        file_entries.append(
            {
                "name": name,
                "path": path.name,
                "rows": rows,
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
        )
    body = {
        "schema_version": 1,
        "namespace": "cup50-acquisition",
        "files": file_entries,
        "source_manifest_sha256": _sha256(manifest_path),
        "terminal_bound_inclusive": terminal.isoformat().replace("+00:00", "Z"),
        "terminal_member_count": len(active),
        "terminal_members": list(active),
    }
    manifest_output = output / "manifest.json"
    manifest_output.write_bytes(_canonical(body))
    return {
        "status": "acquired",
        "manifest": str(manifest_output),
        "manifest_sha256": _sha256(manifest_output),
        "terminal_members": len(active),
        "requests": len(provenance),
    }


def _execution_gaps(
    *,
    bars: pd.DataFrame,
    marks: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    start: pd.Timestamp,
    terminal: pd.Timestamp,
    unavailability: Sequence[UnavailabilityWindow] = (),
) -> tuple[
    list[tuple[pd.Timestamp, str]],
    list[tuple[pd.Timestamp, str]],
    list[tuple[pd.Timestamp, str]],
]:
    decisions = decision_grid(start, terminal)
    bar_keys = set(
        zip(pd.to_datetime(bars["open_time"], utc=True), bars["symbol"].astype(str), strict=True)
    )
    mark_keys = set(
        zip(pd.to_datetime(marks["mark_time"], utc=True), marks["symbol"].astype(str), strict=True)
    )
    normalized_funding = _normalise_funding(funding)
    interval_left = (
        normalized_funding["settlement_time"].dt.ceil("8h") - pd.Timedelta(hours=8)
    )
    funded = {
        pd.Timestamp(time): frozenset(normalized_funding.loc[index, "symbol"].astype(str))
        for time, index in normalized_funding.groupby(interval_left, sort=False).groups.items()
    }
    missing_marks: list[tuple[pd.Timestamp, str]] = []
    missing_funding: list[tuple[pd.Timestamp, str]] = []
    missing_bars: list[tuple[pd.Timestamp, str]] = []
    for decision in decisions:
        active = set(members_at(membership, decision))
        executable = active - set(unavailable_symbols(unavailability, decision))
        missing_bars.extend(
            (decision, symbol)
            for symbol in sorted(executable)
            if (decision, symbol) not in bar_keys
        )
        missing_marks.extend(
            (decision, symbol)
            for symbol in sorted(executable)
            if (decision, symbol) not in mark_keys
        )
        unavailable_next = set(
            unavailable_symbols(unavailability, decision + pd.Timedelta(hours=8))
        )
        missing_funding.extend(
            (decision, symbol)
            for symbol in sorted(
                executable - unavailable_next - set(funded.get(decision, ()))
            )
        )
    terminal_members = set(members_at(membership, terminal - pd.Timedelta(nanoseconds=1)))
    terminal_members -= set(unavailable_symbols(unavailability, terminal))
    missing_marks.extend(
        (terminal, symbol)
        for symbol in sorted(terminal_members)
        if (terminal, symbol) not in mark_keys
    )
    # Archived funding rates do not embed the settlement mark. Bind the canonical mark at the
    # right boundary even when the symbol exits the weekly roster at that same boundary.
    missing_marks.extend(
        (decision + pd.Timedelta(hours=8), symbol)
        for decision, symbol in missing_funding
        if (decision + pd.Timedelta(hours=8), symbol) not in mark_keys
    )
    return (
        sorted(set(missing_bars)),
        sorted(set(missing_marks)),
        sorted(set(missing_funding)),
    )


def _download_verified_archive(url: str) -> tuple[bytes, bytes, str]:
    def download(resource: str) -> bytes:
        for attempt in range(5):
            try:
                with urllib.request.urlopen(resource, timeout=30) as response:  # noqa: S310
                    return response.read()
            except urllib.error.HTTPError:
                raise
            except (TimeoutError, urllib.error.URLError):
                if attempt == 4:
                    raise
                time.sleep(0.5 * (2**attempt))
        raise AssertionError("unreachable archive retry state")

    archive = download(url)
    checksum = download(f"{url}.CHECKSUM")
    expected = checksum.decode().strip().split()[0].lower()
    observed = hashlib.sha256(archive).hexdigest()
    if expected != observed:
        raise ValueError(f"Binance archive checksum mismatch: {url}")
    return archive, checksum, observed


def _mark_archive_rows(
    archive: bytes,
    *,
    symbol: str,
    required: set[pd.Timestamp],
) -> list[dict[str, object]]:
    import io

    rows: list[dict[str, object]] = []
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = bundle.namelist()
        if len(names) != 1:
            raise ValueError(f"mark archive has an unexpected member count: {symbol}")
        text = io.TextIOWrapper(bundle.open(names[0]), encoding="utf-8")
        for row in csv.reader(text):
            try:
                raw_time = int(row[0])
                price = float(row[1])
            except (IndexError, TypeError, ValueError):
                continue
            unit = "us" if raw_time >= 100_000_000_000_000 else "ms"
            timestamp = pd.Timestamp(raw_time, unit=unit, tz="UTC")
            if timestamp in required:
                if not np.isfinite(price) or price <= 0:
                    raise ValueError(f"mark archive contains an invalid open: {symbol}")
                rows.append({"mark_time": timestamp, "symbol": symbol, "mark_price": price})
    return rows


def _transaction_archive_rows(
    archive: bytes,
    *,
    symbol: str,
    required: set[pd.Timestamp],
) -> tuple[list[dict[str, object]], list[pd.Timestamp]]:
    import io

    hourly: dict[pd.Timestamp, list[str]] = {}
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = bundle.namelist()
        if len(names) != 1:
            raise ValueError(f"transaction archive has an unexpected member count: {symbol}")
        text = io.TextIOWrapper(bundle.open(names[0]), encoding="utf-8")
        for row in csv.reader(text):
            try:
                raw_time = int(row[0])
            except (IndexError, TypeError, ValueError):
                continue
            unit = "us" if raw_time >= 100_000_000_000_000 else "ms"
            hourly[pd.Timestamp(raw_time, unit=unit, tz="UTC")] = row
    result: list[dict[str, object]] = []
    missing: list[pd.Timestamp] = []
    for decision in sorted(required):
        times = pd.date_range(decision, periods=8, freq="1h")
        if any(time not in hourly for time in times):
            missing.append(decision)
            continue
        rows = [hourly[time] for time in times]
        close_raw = int(rows[-1][6])
        close_unit = "us" if close_raw >= 100_000_000_000_000 else "ms"
        close_time = pd.Timestamp(close_raw, unit=close_unit, tz="UTC")
        expected_close = decision + pd.Timedelta(hours=8) - pd.Timedelta(milliseconds=1)
        if close_time != expected_close:
            raise ValueError(f"restored transaction bar has a noncanonical close: {symbol}")
        result.append(
            {
                "open_time": decision,
                "symbol": symbol,
                "open": float(rows[0][1]),
                "high": max(float(row[2]) for row in rows),
                "low": min(float(row[3]) for row in rows),
                "close": float(rows[-1][4]),
                "volume": sum(float(row[5]) for row in rows),
                "close_time": close_time,
                "quote_volume": sum(float(row[7]) for row in rows),
                "trade_count": sum(int(row[8]) for row in rows),
                "taker_buy_volume": sum(float(row[9]) for row in rows),
                "taker_buy_quote_volume": sum(float(row[10]) for row in rows),
            }
        )
    return result, missing


def _funding_archive_rows(
    archive: bytes,
    *,
    symbol: str,
    required: set[pd.Timestamp],
    mark_prices: Mapping[tuple[pd.Timestamp, str], float],
) -> tuple[list[dict[str, object]], set[pd.Timestamp]]:
    """Recover funding rates and join their checksum-bound canonical execution marks."""
    import io

    rows: list[dict[str, object]] = []
    covered: set[pd.Timestamp] = set()
    previous: pd.Timestamp | None = None
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        names = bundle.namelist()
        if len(names) != 1:
            raise ValueError(f"funding archive has an unexpected member count: {symbol}")
        text = io.TextIOWrapper(bundle.open(names[0]), encoding="utf-8")
        for row in csv.reader(text):
            try:
                raw_time = int(row[0])
                interval = float(row[1])
                rate = float(row[2])
            except (IndexError, TypeError, ValueError):
                continue
            unit = "us" if raw_time >= 100_000_000_000_000 else "ms"
            actual = pd.Timestamp(raw_time, unit=unit, tz="UTC")
            if previous is not None and actual <= previous:
                raise ValueError(f"funding archive is not strictly ordered: {symbol}")
            previous = actual
            settlement = actual.floor("h")
            if actual - settlement >= pd.Timedelta(seconds=1):
                raise ValueError(f"funding archive jitter exceeds one second: {symbol}")
            interval_left = settlement.ceil("8h") - pd.Timedelta(hours=8)
            if interval_left not in required:
                continue
            mark = float(mark_prices.get((settlement, symbol), np.nan))
            if (
                not np.isfinite(rate)
                or not np.isfinite(interval)
                or interval <= 0
                or not np.isfinite(mark)
                or mark <= 0
            ):
                raise ValueError(
                    f"funding archive contains invalid values: {symbol} at {actual} "
                    f"(interval={interval}, rate={rate}, mark={mark})"
                )
            if interval_left in covered:
                raise ValueError(f"funding archive duplicates an interval: {symbol}")
            covered.add(interval_left)
            rows.append(
                {
                    "funding_time": actual,
                    "symbol": symbol,
                    "funding_rate": rate,
                    "mark_price": mark,
                    "mark_time": settlement,
                    "settlement_time": settlement,
                    "funding_interval_hours": interval,
                }
            )
    return rows, covered


def acquire_execution_gaps(
    *,
    source_root: str | Path,
    source_manifest: str | Path,
    is_root: str | Path,
    sealed_root: str | Path,
    destination: str | Path,
    unavailability: Sequence[UnavailabilityWindow] = (),
    workers: int = 8,
) -> Mapping[str, object]:
    """Fill exact-union mark/funding gaps without changing weekly membership."""
    source, manifest_path, output = Path(source_root), Path(source_manifest), Path(destination)
    if output.exists():
        raise FileExistsError("CUP-50 coverage acquisition destination must be new")
    if workers < 1 or workers > 16:
        raise ValueError("acquisition workers must be in 1..16")
    manifest = json.loads(manifest_path.read_text())
    verified, entries = _verified_sources(source, manifest)
    snapshot = stitch_snapshots(load_snapshot(is_root), load_snapshot(sealed_root))
    bars = pd.read_parquet(verified["bars"])
    marks = pd.read_parquet(verified["mark_prices"])
    funding = pd.read_parquet(verified["funding"])
    bar_gaps, mark_gaps, funding_gaps = _execution_gaps(
        bars=bars,
        marks=marks,
        funding=funding,
        membership=snapshot.membership,
        start=snapshot.window_start,
        terminal=snapshot.window_end,
        unavailability=unavailability,
    )

    required_by_archive: dict[tuple[str, str], set[pd.Timestamp]] = {}
    for timestamp, symbol in mark_gaps:
        required_by_archive.setdefault((symbol, timestamp.strftime("%Y-%m")), set()).add(timestamp)
    required_transaction_archives: dict[tuple[str, str], set[pd.Timestamp]] = {}
    for timestamp, symbol in bar_gaps:
        key = (symbol, timestamp.strftime("%Y-%m"))
        required_transaction_archives.setdefault(key, set()).add(timestamp)

    def download_mark(item: tuple[tuple[str, str], set[pd.Timestamp]]) -> dict[str, object]:
        (symbol, year_month), required = item
        filename = f"{symbol}-1h-{year_month}.zip"
        url = (
            "https://data.binance.vision/data/futures/um/monthly/markPriceKlines/"
            f"{symbol}/1h/{filename}"
        )
        try:
            archive, checksum, digest = _download_verified_archive(url)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            return {
                "archive": None,
                "checksum": None,
                "digest": None,
                "filename": filename,
                "rows": [],
                "missing": sorted(required),
                "symbol": symbol,
                "url": url,
                "year_month": year_month,
            }
        rows = _mark_archive_rows(archive, symbol=symbol, required=required)
        found = {pd.Timestamp(row["mark_time"]) for row in rows}
        return {
            "archive": archive,
            "checksum": checksum,
            "digest": digest,
            "filename": filename,
            "rows": rows,
            "missing": sorted(required - found),
            "symbol": symbol,
            "url": url,
            "year_month": year_month,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        mark_results = list(pool.map(download_mark, sorted(required_by_archive.items())))
    mark_results.sort(key=lambda item: (str(item["symbol"]), str(item["year_month"])))

    daily_required: dict[tuple[str, str], set[pd.Timestamp]] = {}
    for result in mark_results:
        for timestamp in result["missing"]:
            time = pd.Timestamp(timestamp)
            key = (str(result["symbol"]), time.strftime("%Y-%m-%d"))
            daily_required.setdefault(key, set()).add(time)

    def download_mark_daily(
        item: tuple[tuple[str, str], set[pd.Timestamp]],
    ) -> dict[str, object]:
        (symbol, date), required = item
        filename = f"{symbol}-1h-{date}.zip"
        url = (
            "https://data.binance.vision/data/futures/um/daily/markPriceKlines/"
            f"{symbol}/1h/{filename}"
        )
        try:
            archive, checksum, digest = _download_verified_archive(url)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            return {
                "archive": None,
                "checksum": None,
                "digest": None,
                "filename": filename,
                "missing": sorted(required),
                "rows": [],
                "symbol": symbol,
                "url": url,
                "date": date,
            }
        rows = _mark_archive_rows(archive, symbol=symbol, required=required)
        found = {pd.Timestamp(row["mark_time"]) for row in rows}
        return {
            "archive": archive,
            "checksum": checksum,
            "digest": digest,
            "filename": filename,
            "missing": sorted(required - found),
            "rows": rows,
            "symbol": symbol,
            "url": url,
            "date": date,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        daily_mark_results = list(pool.map(download_mark_daily, sorted(daily_required.items())))
    daily_mark_results.sort(key=lambda item: (str(item["symbol"]), str(item["date"])))
    mark_rest_required = [
        (str(result["symbol"]), pd.Timestamp(timestamp))
        for result in daily_mark_results
        for timestamp in result["missing"]
    ]

    def request_mark_gap(item: tuple[str, pd.Timestamp]) -> dict[str, object]:
        symbol, timestamp = item
        requested_ms = int(timestamp.value // 1_000_000)
        params = {
            "symbol": symbol,
            "interval": "1h",
            "startTime": requested_ms,
            "endTime": requested_ms + 3_600_000 - 1,
            "limit": 1,
        }
        payload, raw = _fetch(MARK_URL, params)
        return {
            "symbol": symbol,
            "timestamp": timestamp,
            "params": params,
            "raw": raw,
            "row": _parse_mark(payload, symbol=symbol, terminal_ms=requested_ms),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        mark_rest_results = list(pool.map(request_mark_gap, sorted(mark_rest_required)))

    def download_transaction(
        item: tuple[tuple[str, str], set[pd.Timestamp]],
    ) -> dict[str, object]:
        (symbol, year_month), required = item
        filename = f"{symbol}-1h-{year_month}.zip"
        url = (
            "https://data.binance.vision/data/futures/um/monthly/klines/"
            f"{symbol}/1h/{filename}"
        )
        try:
            archive, checksum, digest = _download_verified_archive(url)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            return {
                "archive": None,
                "checksum": None,
                "digest": None,
                "filename": filename,
                "rows": [],
                "missing": sorted(required),
                "symbol": symbol,
                "url": url,
                "year_month": year_month,
            }
        rows, missing = _transaction_archive_rows(
            archive, symbol=symbol, required=required
        )
        return {
            "archive": archive,
            "checksum": checksum,
            "digest": digest,
            "filename": filename,
            "rows": rows,
            "missing": missing,
            "symbol": symbol,
            "url": url,
            "year_month": year_month,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        transaction_results = list(
            pool.map(download_transaction, sorted(required_transaction_archives.items()))
        )
    transaction_results.sort(
        key=lambda item: (str(item["symbol"]), str(item["year_month"]))
    )
    daily_transaction_required: dict[tuple[str, str], set[pd.Timestamp]] = {}
    for result in transaction_results:
        for timestamp in result["missing"]:
            time = pd.Timestamp(timestamp)
            key = (str(result["symbol"]), time.strftime("%Y-%m-%d"))
            daily_transaction_required.setdefault(key, set()).add(time)

    def download_transaction_daily(
        item: tuple[tuple[str, str], set[pd.Timestamp]],
    ) -> dict[str, object]:
        (symbol, date), required = item
        filename = f"{symbol}-1h-{date}.zip"
        url = (
            "https://data.binance.vision/data/futures/um/daily/klines/"
            f"{symbol}/1h/{filename}"
        )
        archive, checksum, digest = _download_verified_archive(url)
        rows, missing = _transaction_archive_rows(
            archive, symbol=symbol, required=required
        )
        if missing:
            raise ValueError(
                f"verified daily transaction archive cannot restore {symbol}: {missing}"
            )
        return {
            "archive": archive,
            "checksum": checksum,
            "digest": digest,
            "filename": filename,
            "rows": rows,
            "symbol": symbol,
            "url": url,
            "date": date,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        daily_transaction_results = list(
            pool.map(
                download_transaction_daily,
                sorted(daily_transaction_required.items()),
            )
        )
    daily_transaction_results.sort(
        key=lambda item: (str(item["symbol"]), str(item["date"]))
    )

    acquired_mark_rows = [
        row
        for result in [*mark_results, *daily_mark_results]
        for row in result["rows"]
    ]
    acquired_mark_rows.extend(result["row"] for result in mark_rest_results)
    complete_marks = pd.concat(
        [marks, pd.DataFrame(acquired_mark_rows, columns=marks.columns)], ignore_index=True
    ).drop_duplicates(["mark_time", "symbol"], keep="first")
    mark_lookup = {
        (pd.Timestamp(row.mark_time), str(row.symbol)): float(row.mark_price)
        for row in complete_marks.itertuples(index=False)
    }

    funding_by_symbol: dict[str, list[pd.Timestamp]] = {}
    for decision, symbol in funding_gaps:
        funding_by_symbol.setdefault(symbol, []).append(decision)

    funding_archive_required: dict[tuple[str, str], set[pd.Timestamp]] = {}
    for symbol, decisions in funding_by_symbol.items():
        for decision in decisions:
            settlement = decision + pd.Timedelta(hours=8)
            funding_archive_required.setdefault(
                (symbol, settlement.strftime("%Y-%m")), set()
            ).add(decision)

    def download_funding_archive(
        item: tuple[tuple[str, str], set[pd.Timestamp]],
    ) -> dict[str, object]:
        (symbol, year_month), required = item
        filename = f"{symbol}-fundingRate-{year_month}.zip"
        url = (
            "https://data.binance.vision/data/futures/um/monthly/fundingRate/"
            f"{symbol}/{filename}"
        )
        try:
            archive, checksum, digest = _download_verified_archive(url)
        except urllib.error.HTTPError as error:
            if error.code != 404:
                raise
            return {
                "archive": None,
                "checksum": None,
                "digest": None,
                "filename": filename,
                "rows": [],
                "covered": set(),
                "symbol": symbol,
                "url": url,
                "year_month": year_month,
            }
        rows, covered = _funding_archive_rows(
            archive,
            symbol=symbol,
            required=required,
            mark_prices=mark_lookup,
        )
        return {
            "archive": archive,
            "checksum": checksum,
            "digest": digest,
            "filename": filename,
            "rows": rows,
            "covered": covered,
            "symbol": symbol,
            "url": url,
            "year_month": year_month,
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        funding_archive_results = list(
            pool.map(download_funding_archive, sorted(funding_archive_required.items()))
        )
    funding_archive_results.sort(
        key=lambda item: (str(item["symbol"]), str(item["year_month"]))
    )
    archive_covered = {
        (str(result["symbol"]), decision)
        for result in funding_archive_results
        for decision in result["covered"]
    }

    funding_rest_results: list[dict[str, object]] = []
    for symbol, all_decisions in sorted(funding_by_symbol.items()):
        decisions = [
            decision
            for decision in all_decisions
            if (symbol, decision) not in archive_covered
        ]
        if not decisions:
            continue
        lower = min(decisions)
        upper = max(decisions) + pd.Timedelta(hours=8)
        lower_ms = int((lower + pd.Timedelta(milliseconds=1)).value // 1_000_000)
        upper_ms = int(upper.value // 1_000_000) + 999
        params = {"symbol": symbol, "startTime": lower_ms, "endTime": upper_ms, "limit": 1000}
        payload, raw = _fetch(FUNDING_URL, params)
        rows = _parse_funding(
            payload,
            symbol=symbol,
            lower_ms=lower_ms,
            upper_ms=upper_ms,
            mark_prices=mark_lookup,
        )
        covered = {
            pd.Timestamp(row["settlement_time"]).ceil("8h") - pd.Timedelta(hours=8)
            for row in rows
        }
        required = set(decisions)
        if not required <= covered:
            raise ValueError(f"funding REST gap remains for {symbol}: {sorted(required - covered)}")
        funding_rest_results.append(
            {"symbol": symbol, "params": params, "raw": raw, "rows": rows}
        )

    output.mkdir(parents=True)
    for _, path in sorted(verified.items()):
        shutil.copy2(path, output / path.name)
    if (source / "raw").is_dir():
        shutil.copytree(source / "raw", output / "raw")
    shutil.copy2(manifest_path, output / "reused-source-manifest.json")
    provenance: list[dict[str, object]] = []
    new_bars: list[dict[str, object]] = []
    for result in transaction_results:
        if result["archive"] is None:
            continue
        raw_dir = (
            output / "raw" / "coverage-archives" / "transaction_1h" / str(result["symbol"])
        )
        raw_dir.mkdir(parents=True, exist_ok=True)
        archive_path = raw_dir / str(result["filename"])
        archive_path.write_bytes(result["archive"])
        (raw_dir / f"{result['filename']}.CHECKSUM").write_bytes(result["checksum"])
        new_bars.extend(result["rows"])
        provenance.append(
            {
                "dataset": "transaction_1h_recovery",
                "raw_path": archive_path.relative_to(output).as_posix(),
                "sha256": result["digest"],
                "size": archive_path.stat().st_size,
                "symbol": result["symbol"],
                "url": result["url"],
                "year_month": result["year_month"],
            }
        )
    for result in daily_transaction_results:
        raw_dir = (
            output
            / "raw"
            / "coverage-archives"
            / "transaction_1h_daily"
            / str(result["symbol"])
        )
        raw_dir.mkdir(parents=True, exist_ok=True)
        archive_path = raw_dir / str(result["filename"])
        archive_path.write_bytes(result["archive"])
        (raw_dir / f"{result['filename']}.CHECKSUM").write_bytes(result["checksum"])
        new_bars.extend(result["rows"])
        provenance.append(
            {
                "dataset": "transaction_1h_daily_recovery",
                "raw_path": archive_path.relative_to(output).as_posix(),
                "sha256": result["digest"],
                "size": archive_path.stat().st_size,
                "symbol": result["symbol"],
                "url": result["url"],
                "date": result["date"],
            }
        )
    new_marks: list[dict[str, object]] = []
    for result in mark_results:
        if result["archive"] is None:
            continue
        raw_dir = output / "raw" / "coverage-archives" / "mark" / str(result["symbol"])
        raw_dir.mkdir(parents=True, exist_ok=True)
        archive_path = raw_dir / str(result["filename"])
        archive_path.write_bytes(result["archive"])
        checksum_path = raw_dir / f"{result['filename']}.CHECKSUM"
        checksum_path.write_bytes(result["checksum"])
        new_marks.extend(result["rows"])
        provenance.append(
            {
                "dataset": "mark_price_1h",
                "raw_path": archive_path.relative_to(output).as_posix(),
                "sha256": result["digest"],
                "size": archive_path.stat().st_size,
                "symbol": result["symbol"],
                "url": result["url"],
                "year_month": result["year_month"],
            }
        )
    for result in daily_mark_results:
        if result["archive"] is None:
            continue
        raw_dir = (
            output / "raw" / "coverage-archives" / "mark-daily" / str(result["symbol"])
        )
        raw_dir.mkdir(parents=True, exist_ok=True)
        archive_path = raw_dir / str(result["filename"])
        archive_path.write_bytes(result["archive"])
        (raw_dir / f"{result['filename']}.CHECKSUM").write_bytes(result["checksum"])
        new_marks.extend(result["rows"])
        provenance.append(
            {
                "dataset": "mark_price_1h_daily",
                "raw_path": archive_path.relative_to(output).as_posix(),
                "sha256": result["digest"],
                "size": archive_path.stat().st_size,
                "symbol": result["symbol"],
                "url": result["url"],
                "date": result["date"],
            }
        )
    retrieved = dt.datetime.now(dt.UTC).isoformat().replace("+00:00", "Z")
    for result in mark_rest_results:
        timestamp = pd.Timestamp(result["timestamp"])
        raw_path = (
            output
            / "raw"
            / "coverage-rest"
            / "mark"
            / str(result["symbol"])
            / f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
        )
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(result["raw"])
        new_marks.append(result["row"])
        provenance.append(
            {
                "dataset": "mark_price_rest",
                "endpoint": MARK_URL,
                "params": result["params"],
                "raw_path": raw_path.relative_to(output).as_posix(),
                "retrieved_at": retrieved,
                "sha256": _sha256(raw_path),
                "size": raw_path.stat().st_size,
                "symbol": result["symbol"],
            }
        )
    new_funding: list[dict[str, object]] = []
    for result in funding_archive_results:
        if result["archive"] is None:
            continue
        raw_dir = (
            output / "raw" / "coverage-archives" / "funding" / str(result["symbol"])
        )
        raw_dir.mkdir(parents=True, exist_ok=True)
        archive_path = raw_dir / str(result["filename"])
        archive_path.write_bytes(result["archive"])
        (raw_dir / f"{result['filename']}.CHECKSUM").write_bytes(result["checksum"])
        new_funding.extend(result["rows"])
        provenance.append(
            {
                "dataset": "funding_rate_monthly",
                "raw_path": archive_path.relative_to(output).as_posix(),
                "sha256": result["digest"],
                "size": archive_path.stat().st_size,
                "symbol": result["symbol"],
                "url": result["url"],
                "year_month": result["year_month"],
                "mark_source": "canonical checksum-bound mark-price open",
            }
        )
    for result in funding_rest_results:
        raw_path = output / "raw" / "coverage-rest" / "funding" / f"{result['symbol']}.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_bytes(result["raw"])
        new_funding.extend(result["rows"])
        provenance.append(
            {
                "dataset": "funding_rate_rest",
                "endpoint": FUNDING_URL,
                "params": result["params"],
                "raw_path": raw_path.relative_to(output).as_posix(),
                "retrieved_at": retrieved,
                "sha256": _sha256(raw_path),
                "size": raw_path.stat().st_size,
                "symbol": result["symbol"],
            }
        )

    bars = pd.concat([bars, pd.DataFrame(new_bars, columns=bars.columns)], ignore_index=True)
    bars = bars.drop_duplicates(["open_time", "symbol"], keep="first")
    bars.sort_values(["open_time", "symbol"], inplace=True, ignore_index=True)
    bars.to_parquet(output / "bars.parquet", index=False)
    marks = pd.concat([marks, pd.DataFrame(new_marks, columns=marks.columns)], ignore_index=True)
    marks = marks.drop_duplicates(["mark_time", "symbol"], keep="first")
    marks.sort_values(["mark_time", "symbol"], inplace=True, ignore_index=True)
    marks.to_parquet(output / "mark_prices.parquet", index=False)
    additions = pd.DataFrame(new_funding, columns=funding.columns)
    funding = pd.concat([funding, additions], ignore_index=True)
    funding = funding.drop_duplicates(["funding_time", "symbol"], keep="first")
    funding.sort_values(["funding_time", "symbol"], inplace=True, ignore_index=True)
    settlements = pd.to_datetime(funding["settlement_time"], utc=True)
    prior = settlements.groupby(funding["symbol"].astype(str)).diff().dt.total_seconds().div(3600)
    funding.loc[funding["funding_interval_hours"].isna(), "funding_interval_hours"] = prior
    funding.to_parquet(output / "funding.parquet", index=False)
    provenance_path = output / "coverage-gap-provenance.jsonl"
    provenance_path.write_bytes(b"".join(_canonical(row) for row in provenance))

    logical_by_filename = {
        Path(str(entry["path"])).name: name for name, entry in entries.items()
    }
    file_entries = []
    for path in sorted(output.iterdir()):
        if not path.is_file() or path.name == "manifest.json":
            continue
        rows = None
        if path.suffix == ".parquet":
            rows = len(pd.read_parquet(path))
        elif path.suffix == ".jsonl":
            rows = len(path.read_text().splitlines())
        file_entries.append(
            {
                "name": logical_by_filename.get(path.name, path.stem),
                "path": path.name,
                "rows": rows,
                "sha256": _sha256(path),
                "size": path.stat().st_size,
            }
        )
    body = {
        "schema_version": 2,
        "namespace": "cup50-acquisition",
        "files": file_entries,
        "source_manifest_sha256": _sha256(manifest_path),
        "bar_gap_count": len(bar_gaps),
        "mark_gap_count": len(mark_gaps),
        "funding_gap_count": len(funding_gaps),
        "coverage_archive_count": sum(
            result["archive"] is not None for result in mark_results
        ),
        "coverage_daily_archive_count": sum(
            result["archive"] is not None for result in daily_mark_results
        ),
        "transaction_recovery_archive_count": sum(
            result["archive"] is not None for result in transaction_results
        ),
        "transaction_daily_recovery_archive_count": len(daily_transaction_results),
        "funding_archive_count": sum(
            result["archive"] is not None for result in funding_archive_results
        ),
        "coverage_rest_request_count": len(funding_rest_results),
        "mark_rest_fallback_count": len(mark_rest_results),
    }
    manifest_output = output / "manifest.json"
    manifest_output.write_bytes(_canonical(body))
    return {
        "status": "coverage-acquired",
        "manifest": str(manifest_output),
        "manifest_sha256": _sha256(manifest_output),
        "bars_filled": len(bar_gaps),
        "marks_filled": len(mark_gaps),
        "funding_intervals_filled": len(funding_gaps),
        "archive_requests": (
            len(mark_results)
            + sum(result["archive"] is not None for result in transaction_results)
            + len(daily_transaction_results)
            + sum(result["archive"] is not None for result in daily_mark_results)
            + sum(result["archive"] is not None for result in funding_archive_results)
        )
        * 2,
        "rest_requests": len(funding_rest_results) + len(mark_rest_results),
    }
