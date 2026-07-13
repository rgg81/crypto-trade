"""Fail-closed builder for the canonical Binance USD-M Top-40 snapshot.

The builder deliberately owns acquisition and normalisation only.  It downloads official
``data.binance.vision`` monthly archives, verifies every Binance SHA-256 sidecar before parsing,
and publishes canonical files only after the complete build succeeds.  When, and only when, a
required executable-member funding month is absent from the archive catalog, the builder refetches
the official USD-M funding-rate REST history and freezes each canonical response separately.  It
resolves required hourly marks through a strict source priority: checksummed monthly
``markPriceKlines``, checksummed daily ``markPriceKlines``, then the exact official USD-M REST
hour. Raw verified archives and canonical REST responses are kept below ``output_dir/raw``.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import time
import tomllib
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any
from xml.etree import ElementTree

import httpx
import numpy as np
import pandas as pd

from crypto_trade.tournament.data import is_eligible_usdt_perpetual, point_in_time_top40
from crypto_trade.tournament.metrics import classify_btc_regimes

_SCHEMA_VERSION = 1
_HTTP_RETRIES = 3
_DOWNLOAD_WORKERS = 48
_FUNDING_REST_LIMIT = 1000
_OFFICIAL_FUNDING_RATE_URL = "https://fapi.binance.com/fapi/v1/fundingRate"
_OFFICIAL_MARK_PRICE_KLINES_URL = "https://fapi.binance.com/fapi/v1/markPriceKlines"
_OFFICIAL_ARCHIVE_BASE_URL = "https://data.binance.vision"
_KNOWN_ARCHIVE_ONLY_INDEXES = frozenset(
    {"BLUEBIRDUSDT", "BTCDOMUSDT", "DEFIUSDT", "DOTECOUSDT", "FOOTBALLUSDT"}
)
_KLINE_COLUMNS = (
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
)
_FUNDING_COLUMNS = ("calc_time", "funding_interval_hours", "last_funding_rate")
_LIMITATIONS = (
    "Binance does not publish complete point-in-time exchangeInfo/filter history.",
    "Archive-only plain USDT symbols are inferred to be crypto perpetuals; known historical "
    "composite/index symbols BLUEBIRDUSDT, BTCDOMUSDT, DEFIUSDT, DOTECOUSDT, and "
    "FOOTBALLUSDT are explicitly excluded.",
    "Archive-only onboard/delivery bounds are inferred from first/last executable 8h bars.",
    "Funding mark price is the exact floor-hour 1h mark open (a boundary-open proxy); actual "
    "funding timestamps are preserved and must have less than one second of boundary jitter.",
    "Risk exposure uses exact 8h boundary opens from Binance 1h mark-price archives; transaction "
    "klines remain the execution and participation source.",
    "Exact required marks absent from a checksummed monthly markPriceKlines archive use the "
    "checksummed Binance daily markPriceKlines archive first, then exact-hour REST only when the "
    "daily object is absent or lacks that hour; no mark is interpolated.",
    "Monthly archive gaps are treated as non-executable intervals, not silently interpolated; "
    "funding coverage is required for every month in which a weekly member has executable bars.",
    "Official fundingRate REST responses used only for required archive gaps have no upstream "
    "SHA-256 sidecar and Binance may revise that API history; exact parameters, retrieval time, "
    "canonical response bytes, and a local SHA-256 are frozen for every request.",
    "Official markPriceKlines REST responses used only for exact required hourly marks absent "
    "from checksummed monthly and daily archives have no upstream SHA-256 sidecar and Binance "
    "may revise that API history; exact parameters, retrieval time, canonical response bytes, "
    "fallback reason, archive SHA-256, and a local response SHA-256 are frozen for every request.",
    "Transaction bars before a symbol's first Top-40 admission remain available as research "
    "history but are non-executable; no risk mark is required or synthesized for those bars.",
)


@dataclass(frozen=True, order=True)
class _Archive:
    dataset: str
    symbol: str
    year: int
    month: int
    key: str
    url: str
    checksum_url: str
    day: int | None = None

    @property
    def filename(self) -> str:
        return PurePosixPath(self.key).name


def build_snapshot(
    config_path: str | Path,
    output_dir: str | Path,
    manifest_path: str | Path,
    reports_common_dir: str | Path,
    resume: bool = True,
) -> dict[str, Any]:
    """Acquire, verify, build, and atomically publish the canonical snapshot.

    The function raises on any missing checksum, checksum mismatch, malformed archive, missing
    funding mark, incomplete reconstitution, or publication-verification error.  Verified raw ZIPs
    remain cached after failure; canonical files and the manifest are not published until all
    inputs have passed validation.
    """

    config_path = Path(config_path).resolve()
    output_dir = Path(output_dir).resolve()
    manifest_path = Path(manifest_path).resolve()
    reports_common_dir = Path(reports_common_dir).resolve()
    root = _project_root(config_path)
    for path in (output_dir, manifest_path, reports_common_dir):
        if not path.is_relative_to(root):
            raise ValueError(f"snapshot path must remain below project root {root}: {path}")

    config = _load_config(config_path)
    data_config = config["data"]
    warmup_start = _utc(data_config["warmup_start"])
    hard_end = _utc(data_config["hard_end_exclusive"])
    evaluation_start = _utc(config["splits"]["in_sample_start"])
    if warmup_start >= evaluation_start or evaluation_start >= hard_end:
        raise ValueError("expected warmup_start < in_sample_start < hard_end_exclusive")
    if data_config["transaction_interval"] != "8h":
        raise ValueError("canonical transaction_interval must be 8h")
    if data_config["mark_price_interval"] != "1h":
        raise ValueError("canonical mark_price_interval must be 1h")
    if data_config["checksum_policy"] != "require-binance-sha256-sidecar":
        raise ValueError("canonical snapshot requires Binance SHA-256 sidecars")
    if data_config["funding_rate_url"] != _OFFICIAL_FUNDING_RATE_URL:
        raise ValueError("canonical funding REST fallback requires official Binance USD-M")
    if data_config["mark_price_klines_url"] != _OFFICIAL_MARK_PRICE_KLINES_URL:
        raise ValueError("canonical mark-price REST fallback requires official Binance USD-M")

    raw_dir = output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    reports_common_dir.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    provenance: list[dict[str, Any]] = []
    rest_provenance: list[dict[str, Any]] = []
    mark_rest_provenance: list[dict[str, Any]] = []
    with _make_http_client() as client:
        exchange_info = _fetch_exchange_info(client, data_config["exchange_info_url"])
        exchange_info_retrieved_at = pd.Timestamp.now(tz="UTC").isoformat()
        current_symbols = {
            str(item.get("symbol")): item
            for item in exchange_info.get("symbols", [])
            if isinstance(item, dict) and item.get("symbol")
        }
        _progress("fetching exchangeInfo and discovering archived USD-M symbols")
        discovered = _discover_symbols(
            client,
            data_config["archive_s3_url"],
            "data/futures/um/monthly/klines/",
        )
        candidates = _candidate_symbols(discovered, current_symbols, hard_end)
        if "BTCUSDT" not in candidates:
            raise ValueError("BTCUSDT is absent from the eligible archive catalog")

        transaction_frames: list[pd.DataFrame] = []
        _progress(f"building transaction-bar panel for {len(candidates)} candidate symbols")
        for symbol_index, symbol in enumerate(candidates, start=1):
            archives = _list_monthly_archives(
                client,
                s3_url=data_config["archive_s3_url"],
                base_url=data_config["archive_base_url"],
                dataset="transaction_8h",
                symbol=symbol,
                interval="8h",
                warmup_start=warmup_start,
                hard_end=hard_end,
            )
            if not archives:
                raise ValueError(f"no 8h transaction archives for candidate {symbol}")
            _require_active_hard_end_coverage(
                archives, current_symbols.get(symbol), hard_end=hard_end
            )
            acquired = _acquire_archives(
                client, archives, raw_dir=raw_dir, root=root, resume=resume
            )
            for archive, (path, source) in zip(archives, acquired, strict=True):
                provenance.append(source)
                frame = _parse_kline_archive(
                    path,
                    symbol=symbol,
                    warmup_start=warmup_start,
                    hard_end=hard_end,
                    expected_hours=8,
                )
                if frame.empty:
                    raise ValueError(f"empty in-window transaction archive: {archive.url}")
                transaction_frames.append(frame)
            if symbol_index % 25 == 0 or symbol_index == len(candidates):
                _progress(f"transaction bars: {symbol_index}/{len(candidates)} symbols")

        bars = _canonical_bars(transaction_frames, warmup_start, hard_end)
        metadata = _contract_metadata(bars, current_symbols, hard_end)
        membership = _build_membership(
            bars,
            metadata,
            evaluation_start=evaluation_start,
            hard_end=hard_end,
            universe_config=config["universe"],
        )
        membership_symbols = tuple(sorted(membership["symbol"].unique()))
        if not membership_symbols:
            raise ValueError("point-in-time membership is empty")

        _progress(
            f"membership built; acquiring funding and marks for {len(membership_symbols)} symbols"
        )
        funding_frames: list[pd.DataFrame] = []
        mark_frames: list[pd.DataFrame] = []
        required_funding_by_symbol: dict[str, set[tuple[int, int]]] = {}
        for symbol_index, symbol in enumerate(membership_symbols, start=1):
            funding_archives = _list_monthly_archives(
                client,
                s3_url=data_config["archive_s3_url"],
                base_url=data_config["archive_base_url"],
                dataset="funding_rate",
                symbol=symbol,
                interval=None,
                warmup_start=warmup_start,
                hard_end=hard_end,
            )
            required_funding_months = _member_bar_months(
                bars,
                membership,
                symbol=symbol,
                evaluation_start=evaluation_start,
            )
            required_funding_by_symbol[symbol] = required_funding_months
            available_funding_months = {
                (archive.year, archive.month) for archive in funding_archives
            }
            missing_funding_months = sorted(required_funding_months - available_funding_months)
            symbol_funding: list[pd.DataFrame] = []
            acquired_funding = _acquire_archives(
                client, funding_archives, raw_dir=raw_dir, root=root, resume=resume
            )
            for archive, (path, source) in zip(funding_archives, acquired_funding, strict=True):
                provenance.append(source)
                frame = _parse_funding_archive(
                    path, symbol=symbol, warmup_start=warmup_start, hard_end=hard_end
                )
                if frame.empty:
                    raise ValueError(f"empty in-window funding archive: {archive.url}")
                symbol_funding.append(frame)
            for year, month in missing_funding_months:
                frame, requests = _acquire_funding_rest_month(
                    client,
                    endpoint=data_config["funding_rate_url"],
                    symbol=symbol,
                    year=year,
                    month=month,
                    raw_dir=raw_dir,
                    root=root,
                    warmup_start=warmup_start,
                    hard_end=hard_end,
                )
                symbol_funding.append(frame)
                rest_provenance.extend(requests)
            if not symbol_funding:
                raise ValueError(f"no funding history for executable member {symbol}")
            funding_frame = _derive_missing_funding_intervals(
                pd.concat(symbol_funding, ignore_index=True), symbol=symbol
            )
            # Keep the predecessor event available while deriving a variable funding interval,
            # then remove cashflows that could not have affected a tournament position.
            funding_frame = _funding_since_first_admission(
                funding_frame,
                membership,
                symbol=symbol,
            )
            actual_funding_months = {
                (timestamp.year, timestamp.month) for timestamp in funding_frame["funding_time"]
            }
            if not required_funding_months.issubset(actual_funding_months):
                missing = sorted(required_funding_months - actual_funding_months)
                raise ValueError(
                    f"missing fundingRate event coverage while {symbol} is an executable "
                    f"weekly member: {missing}"
                )
            funding_frames.append(funding_frame)

            mark_archives = _list_monthly_archives(
                client,
                s3_url=data_config["archive_s3_url"],
                base_url=data_config["archive_base_url"],
                dataset="mark_price_1h",
                symbol=symbol,
                interval="1h",
                warmup_start=warmup_start,
                hard_end=hard_end,
            )
            if not mark_archives:
                raise ValueError(f"no monthly 1h markPriceKlines archives for member {symbol}")
            _require_active_hard_end_coverage(
                mark_archives, current_symbols.get(symbol), hard_end=hard_end
            )
            funding_months = {
                (timestamp.year, timestamp.month) for timestamp in funding_frame["funding_time"]
            }
            mark_months = {(archive.year, archive.month) for archive in mark_archives}
            if not funding_months.issubset(mark_months):
                missing = sorted(funding_months - mark_months)
                raise ValueError(f"missing mark-price archive months for {symbol}: {missing}")
            acquired_marks = _acquire_archives(
                client, mark_archives, raw_dir=raw_dir, root=root, resume=resume
            )
            symbol_mark_frames: list[pd.DataFrame] = []
            symbol_mark_sources: dict[tuple[int, int], dict[str, Any]] = {}
            for archive, (path, source) in zip(mark_archives, acquired_marks, strict=True):
                provenance.append(source)
                month_key = (archive.year, archive.month)
                if month_key in symbol_mark_sources:
                    raise ValueError(
                        f"duplicate mark-price archive month for {symbol}: {month_key}"
                    )
                symbol_mark_sources[month_key] = source
                frame = _parse_kline_archive(
                    path,
                    symbol=symbol,
                    warmup_start=warmup_start - pd.Timedelta(hours=1),
                    hard_end=hard_end,
                    expected_hours=1,
                )
                if frame.empty:
                    raise ValueError(f"empty in-window mark-price archive: {archive.url}")
                symbol_mark_frames.append(
                    frame.loc[:, ["open_time", "symbol", "open"]].rename(
                        columns={"open_time": "mark_time", "open": "mark_price"}
                    )
                )
            archive_marks = pd.concat(symbol_mark_frames, ignore_index=True)
            archive_marks = archive_marks.sort_values("mark_time").reset_index(drop=True)
            if archive_marks.duplicated(["mark_time", "symbol"]).any():
                raise ValueError(f"duplicate archived mark-price rows for {symbol}")
            required_reasons = _required_mark_reasons(
                bars,
                funding_frame,
                membership,
                symbol=symbol,
            )
            archived_times = set(pd.to_datetime(archive_marks["mark_time"], utc=True))
            fallback_frames: list[pd.DataFrame] = []
            missing_reasons = {
                mark_time: reasons
                for mark_time, reasons in required_reasons.items()
                if mark_time not in archived_times
            }
            daily_dates = tuple(sorted({mark_time.floor("D") for mark_time in missing_reasons}))
            acquired_daily = _acquire_daily_mark_archives(
                client,
                base_url=data_config["archive_base_url"],
                symbol=symbol,
                dates=daily_dates,
                raw_dir=raw_dir,
                root=root,
                resume=resume,
            )
            daily_times: set[pd.Timestamp] = set()
            for day, acquired in zip(daily_dates, acquired_daily, strict=True):
                if acquired is None:
                    continue
                path, source = acquired
                daily_frame = (
                    _parse_kline_archive(
                        path,
                        symbol=symbol,
                        warmup_start=warmup_start - pd.Timedelta(hours=1),
                        hard_end=hard_end,
                        expected_hours=1,
                    )
                    .loc[:, ["open_time", "symbol", "open"]]
                    .rename(columns={"open_time": "mark_time", "open": "mark_price"})
                )
                if daily_frame.duplicated(["mark_time", "symbol"]).any():
                    raise ValueError(
                        f"duplicate daily mark-price rows for {symbol} on {day.date()}"
                    )
                required_on_day = {
                    mark_time for mark_time in missing_reasons if mark_time.floor("D") == day
                }
                selected = daily_frame.loc[daily_frame["mark_time"].isin(required_on_day)].copy()
                if selected.empty:
                    # A valid daily object may itself contain a historical publication gap. It
                    # remains only an unreferenced cache object and the exact REST hour is next.
                    continue
                selected_times = set(pd.to_datetime(selected["mark_time"], utc=True))
                if daily_times.intersection(selected_times):
                    raise ValueError(f"daily mark-price fallbacks overlap for {symbol}")
                daily_times.update(selected_times)
                fallback_frames.append(selected)
                provenance.append(source)

            for mark_time, reasons in missing_reasons.items():
                if mark_time in daily_times:
                    continue
                month_key = (mark_time.year, mark_time.month)
                archive_source = symbol_mark_sources.get(month_key)
                if archive_source is None:
                    raise ValueError(
                        f"required mark-price fallback has no checksummed archive month for "
                        f"{symbol} at {mark_time}"
                    )
                frame, request = _acquire_mark_rest_time(
                    client,
                    endpoint=data_config["mark_price_klines_url"],
                    symbol=symbol,
                    mark_time=mark_time,
                    required_for=reasons,
                    archive_source=archive_source,
                    raw_dir=raw_dir,
                    root=root,
                    warmup_start=warmup_start,
                    hard_end=hard_end,
                )
                fallback_frames.append(frame)
                mark_rest_provenance.append(request)
            combined_marks = pd.concat([archive_marks, *fallback_frames], ignore_index=True)
            if combined_marks.duplicated(["mark_time", "symbol"]).any():
                raise ValueError(
                    f"duplicate mark-price rows across archive/REST inputs for {symbol}"
                )
            mark_frames.append(combined_marks.sort_values("mark_time").reset_index(drop=True))
            if symbol_index % 25 == 0 or symbol_index == len(membership_symbols):
                _progress(f"funding/marks: {symbol_index}/{len(membership_symbols)} symbols")

    funding_raw = pd.concat(funding_frames, ignore_index=True)
    marks = pd.concat(mark_frames, ignore_index=True)
    funding = _attach_mark_prices(funding_raw, marks)
    boundary_marks = _boundary_mark_prices(bars, marks, membership)
    coverage = _coverage_report(
        bars,
        funding_raw,
        marks,
        membership,
        current_symbols=current_symbols,
        hard_end=hard_end,
        required_funding_by_symbol=required_funding_by_symbol,
    )
    btc_daily_full = _btc_daily_returns(bars, warmup_start, hard_end)
    btc_regimes_full = (
        classify_btc_regimes(
            pd.Series(
                btc_daily_full["btc_return"].to_numpy(),
                index=pd.to_datetime(btc_daily_full["date"], utc=True),
                name="btc_return",
            )
        )
        .rename_axis("date")
        .reset_index(name="regime")
    )
    btc_daily = btc_daily_full[
        (btc_daily_full["date"] >= evaluation_start) & (btc_daily_full["date"] < hard_end)
    ].reset_index(drop=True)
    btc_regimes = btc_regimes_full[
        (btc_regimes_full["date"] >= evaluation_start) & (btc_regimes_full["date"] < hard_end)
    ].reset_index(drop=True)
    expected_report_dates = pd.date_range(
        evaluation_start.floor("D"), hard_end - pd.Timedelta(days=1), freq="D"
    )
    if list(btc_daily["date"]) != list(expected_report_dates) or list(btc_regimes["date"]) != list(
        expected_report_dates
    ):
        raise ValueError("common BTC report dates do not exactly cover the evaluation window")

    provenance.sort(
        key=lambda row: (
            row["dataset"],
            row["symbol"],
            row["year_month"],
            row.get("date", ""),
        )
    )
    if len({row["url"] for row in provenance}) != len(provenance):
        raise ValueError("duplicate archive provenance rows")
    rest_provenance.sort(key=lambda row: (row["symbol"], row["year_month"], row["page"]))
    if len({row["raw_path"] for row in rest_provenance}) != len(rest_provenance):
        raise ValueError("duplicate REST provenance rows")
    mark_rest_provenance.sort(key=lambda row: (row["symbol"], row["mark_time"]))
    if len({row["raw_path"] for row in mark_rest_provenance}) != len(mark_rest_provenance):
        raise ValueError("duplicate mark-price REST provenance rows")
    canonical_exchange_info = _canonical_exchange_info(exchange_info)

    targets: list[tuple[Path, str, Any]] = [
        (output_dir / "bars.parquet", "parquet", bars),
        (output_dir / "funding.parquet", "parquet", funding),
        (output_dir / "mark_prices.parquet", "parquet", boundary_marks),
        (output_dir / "contract_metadata.parquet", "parquet", metadata),
        (output_dir / "membership.parquet", "parquet", membership),
        (
            output_dir / "archive_provenance.jsonl",
            "text",
            "".join(_json_line(row) for row in provenance),
        ),
        (
            output_dir / "rest_provenance.jsonl",
            "text",
            "".join(_json_line(row) for row in rest_provenance),
        ),
        (
            output_dir / "mark_rest_provenance.jsonl",
            "text",
            "".join(_json_line(row) for row in mark_rest_provenance),
        ),
        (
            output_dir / "exchange_info.json",
            "text",
            json.dumps(canonical_exchange_info, indent=2, sort_keys=True) + "\n",
        ),
        (
            output_dir / "coverage.json",
            "text",
            json.dumps(coverage, indent=2, sort_keys=True) + "\n",
        ),
        (reports_common_dir / "btc_daily_returns.csv", "csv", btc_daily),
        (reports_common_dir / "btc_regimes.csv", "csv", btc_regimes),
    ]
    staged: list[tuple[Path, Path]] = []
    try:
        for path, kind, value in targets:
            temp = path.with_name(f".{path.name}.snapshot-tmp")
            if kind == "parquet":
                value.to_parquet(temp, index=False, compression="zstd")
            elif kind == "csv":
                value.to_csv(temp, index=False, lineterminator="\n")
            else:
                temp.write_text(value, encoding="utf-8")
            staged.append((temp, path))
        for temp, path in staged:
            os.replace(temp, path)
    finally:
        for temp, _ in staged:
            temp.unlink(missing_ok=True)

    row_counts = {
        "bars.parquet": len(bars),
        "funding.parquet": len(funding),
        "mark_prices.parquet": len(boundary_marks),
        "contract_metadata.parquet": len(metadata),
        "membership.parquet": len(membership),
        "btc_daily_returns.csv": len(btc_daily),
        "btc_regimes.csv": len(btc_regimes),
        "archive_provenance.jsonl": len(provenance),
        "rest_provenance.jsonl": len(rest_provenance),
        "mark_rest_provenance.jsonl": len(mark_rest_provenance),
        "exchange_info.json": len(canonical_exchange_info.get("symbols", [])),
        "coverage.json": len(coverage["symbols"]),
    }
    logical_names = {
        "bars.parquet": "bars",
        "funding.parquet": "funding",
        "mark_prices.parquet": "mark_prices",
        "contract_metadata.parquet": "contract_metadata",
        "membership.parquet": "membership",
        "archive_provenance.jsonl": "archive_provenance",
        "rest_provenance.jsonl": "rest_provenance",
        "mark_rest_provenance.jsonl": "mark_rest_provenance",
        "exchange_info.json": "exchange_info",
        "coverage.json": "coverage",
        "btc_daily_returns.csv": "btc_daily_returns",
        "btc_regimes.csv": "btc_regimes",
    }
    files = []
    for path, _, _ in targets:
        files.append(
            {
                "name": logical_names[path.name],
                "path": _relative(path, root),
                "size": path.stat().st_size,
                "sha256": _sha256_file(path),
                "rows": row_counts[path.name],
            }
        )
    files.sort(key=lambda entry: entry["path"])
    provenance_path = output_dir / "archive_provenance.jsonl"
    rest_provenance_path = output_dir / "rest_provenance.jsonl"
    mark_rest_provenance_path = output_dir / "mark_rest_provenance.jsonl"
    manifest: dict[str, Any] = {
        "schema_version": _SCHEMA_VERSION,
        "parser_version": str(data_config["parser_version"]),
        "window": {
            "warmup_start": warmup_start.isoformat(),
            "evaluation_start": evaluation_start.isoformat(),
            "hard_end_exclusive": hard_end.isoformat(),
        },
        "sources": {
            "source": str(data_config["source"]),
            "archive_base_url": str(data_config["archive_base_url"]),
            "archive_s3_url": str(data_config["archive_s3_url"]),
            "exchange_info_url": str(data_config["exchange_info_url"]),
            "funding_rate_url": str(data_config["funding_rate_url"]),
            "mark_price_klines_url": str(data_config["mark_price_klines_url"]),
            "checksum_policy": str(data_config["checksum_policy"]),
            "archive_count": len(provenance),
            "archive_provenance_path": _relative(provenance_path, root),
            "archive_provenance_sha256": _sha256_file(provenance_path),
            "rest_request_count": len(rest_provenance),
            "rest_provenance_path": _relative(rest_provenance_path, root),
            "rest_provenance_sha256": _sha256_file(rest_provenance_path),
            "mark_rest_request_count": len(mark_rest_provenance),
            "mark_rest_provenance_path": _relative(mark_rest_provenance_path, root),
            "mark_rest_provenance_sha256": _sha256_file(mark_rest_provenance_path),
            "config_path": _relative(config_path, root),
            "config_sha256": _sha256_file(config_path),
            "builder_path": _relative(Path(__file__).resolve(), root),
            "builder_sha256": _sha256_file(Path(__file__).resolve()),
            "exchange_info_retrieved_at_utc": exchange_info_retrieved_at,
            "exchange_info_server_time": exchange_info.get("serverTime"),
        },
        "limitations": list(_LIMITATIONS),
        "files": files,
    }
    manifest_text = json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    manifest_temp = manifest_path.with_name(f".{manifest_path.name}.snapshot-tmp")
    manifest_temp.write_text(manifest_text, encoding="utf-8")
    os.replace(manifest_temp, manifest_path)
    _progress(f"published and verifying {manifest_path}")
    return verify_snapshot_manifest(manifest_path)


def verify_snapshot_manifest(manifest_path: str | Path) -> dict[str, Any]:
    """Verify canonical JSON form and every generated file referenced by a manifest.

    Returns the parsed manifest on success and raises ``ValueError`` on the first integrity issue.
    """

    manifest_path = Path(manifest_path).resolve()
    root = _manifest_root(manifest_path)
    try:
        raw_text = manifest_path.read_text(encoding="utf-8")
        manifest = json.loads(raw_text)
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid snapshot manifest: {exc}") from exc
    if not isinstance(manifest, dict):
        raise ValueError("snapshot manifest must be a JSON object")
    if raw_text != json.dumps(manifest, indent=2, sort_keys=True) + "\n":
        raise ValueError("snapshot manifest is not in canonical JSON form")
    if manifest.get("schema_version") != _SCHEMA_VERSION:
        raise ValueError("unsupported snapshot manifest schema_version")
    if not str(manifest.get("parser_version", "")).strip():
        raise ValueError("snapshot manifest requires parser_version")
    if not isinstance(manifest.get("limitations"), list) or not manifest["limitations"]:
        raise ValueError("snapshot manifest requires disclosed limitations")
    if not any(
        "fundingRate REST" in str(item)
        and "no upstream SHA-256 sidecar" in str(item)
        and "may revise" in str(item)
        for item in manifest["limitations"]
    ):
        raise ValueError("snapshot manifest omits the REST revision/checksum limitation")
    if not any(
        "markPriceKlines REST" in str(item)
        and "no upstream SHA-256 sidecar" in str(item)
        and "may revise" in str(item)
        for item in manifest["limitations"]
    ):
        raise ValueError("snapshot manifest omits the mark REST revision/checksum limitation")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise ValueError("snapshot manifest requires canonical files")
    paths = [entry.get("path") for entry in files if isinstance(entry, dict)]
    if len(paths) != len(files) or paths != sorted(paths) or len(paths) != len(set(paths)):
        raise ValueError("snapshot manifest file paths must be unique and sorted")
    names = [entry.get("name") for entry in files]
    invalid_names = any(not isinstance(name, str) or not name for name in names)
    if invalid_names or len(names) != len(set(names)):
        raise ValueError("snapshot manifest logical names must be non-empty and unique")
    required_names = {
        "archive_provenance",
        "bars",
        "btc_daily_returns",
        "btc_regimes",
        "contract_metadata",
        "coverage",
        "exchange_info",
        "funding",
        "mark_prices",
        "mark_rest_provenance",
        "membership",
        "rest_provenance",
    }
    if set(names) != required_names:
        raise ValueError(f"snapshot manifest logical names differ: {sorted(set(names))}")
    file_entries = {entry["name"]: entry for entry in files}
    for entry in files:
        path = _resolve_manifest_path(root, entry["path"])
        if not path.is_file():
            raise ValueError(f"snapshot file is missing: {entry['path']}")
        if path.stat().st_size != entry.get("size"):
            raise ValueError(f"snapshot file size mismatch: {entry['path']}")
        if _sha256_file(path) != entry.get("sha256"):
            raise ValueError(f"snapshot file hash mismatch: {entry['path']}")
        if not isinstance(entry.get("rows"), int) or entry["rows"] < 0:
            raise ValueError(f"snapshot file row count is invalid: {entry['path']}")
        if _actual_manifest_rows(path, entry["name"]) != entry["rows"]:
            raise ValueError(f"snapshot file row count mismatch: {entry['path']}")
    sources = manifest.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("snapshot manifest requires sources")
    if sources.get("archive_base_url") != "https://data.binance.vision":
        raise ValueError("snapshot archive source is not official data.binance.vision")
    if sources.get("archive_s3_url") != (
        "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
    ):
        raise ValueError("snapshot archive catalog is not official data.binance.vision")
    if sources.get("checksum_policy") != "require-binance-sha256-sidecar":
        raise ValueError("snapshot archive checksum policy is not fail-closed")
    if sources.get("exchange_info_url") != "https://fapi.binance.com/fapi/v1/exchangeInfo":
        raise ValueError("snapshot exchangeInfo source is not official Binance USD-M")
    if sources.get("funding_rate_url") != _OFFICIAL_FUNDING_RATE_URL:
        raise ValueError("snapshot funding-rate REST source is not official Binance USD-M")
    if sources.get("mark_price_klines_url") != _OFFICIAL_MARK_PRICE_KLINES_URL:
        raise ValueError("snapshot mark-price REST source is not official Binance USD-M")
    try:
        retrieved_at = pd.Timestamp(sources["exchange_info_retrieved_at_utc"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("snapshot exchangeInfo retrieval time is invalid") from exc
    if retrieved_at.tzinfo is None:
        raise ValueError("snapshot exchangeInfo retrieval time must be timezone-aware")
    if not isinstance(sources.get("exchange_info_server_time"), int):
        raise ValueError("snapshot exchangeInfo serverTime is invalid")
    provenance_path = _resolve_manifest_path(root, sources.get("archive_provenance_path", ""))
    if provenance_path != _resolve_manifest_path(root, file_entries["archive_provenance"]["path"]):
        raise ValueError("archive provenance source/file paths disagree")
    if _sha256_file(provenance_path) != sources.get("archive_provenance_sha256"):
        raise ValueError("archive provenance hash mismatch")
    rest_provenance_path = _resolve_manifest_path(root, sources.get("rest_provenance_path", ""))
    if rest_provenance_path != _resolve_manifest_path(
        root, file_entries["rest_provenance"]["path"]
    ):
        raise ValueError("REST provenance source/file paths disagree")
    if _sha256_file(rest_provenance_path) != sources.get("rest_provenance_sha256"):
        raise ValueError("REST provenance hash mismatch")
    mark_rest_provenance_path = _resolve_manifest_path(
        root, sources.get("mark_rest_provenance_path", "")
    )
    if mark_rest_provenance_path != _resolve_manifest_path(
        root, file_entries["mark_rest_provenance"]["path"]
    ):
        raise ValueError("mark REST provenance source/file paths disagree")
    if _sha256_file(mark_rest_provenance_path) != sources.get("mark_rest_provenance_sha256"):
        raise ValueError("mark REST provenance hash mismatch")
    config_path = _resolve_manifest_path(root, sources.get("config_path", ""))
    if _sha256_file(config_path) != sources.get("config_sha256"):
        raise ValueError("snapshot config hash mismatch")
    builder_path = _resolve_manifest_path(root, sources.get("builder_path", ""))
    if _sha256_file(builder_path) != sources.get("builder_sha256"):
        raise ValueError("snapshot builder hash mismatch")
    provenance_lines = [line for line in provenance_path.read_text(encoding="utf-8").splitlines()]
    if len(provenance_lines) != sources.get("archive_count"):
        raise ValueError("archive provenance count mismatch")
    archive_rows: list[dict[str, Any]] = []
    for line in provenance_lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("archive provenance contains invalid JSON") from exc
        if line + "\n" != _json_line(row):
            raise ValueError("archive provenance is not canonical JSONL")
        required = {
            "dataset",
            "symbol",
            "year_month",
            "url",
            "checksum_url",
            "sha256",
            "size",
            "raw_path",
            "checksum_sha256",
            "raw_checksum_path",
        }
        if not isinstance(row, dict) or required - set(row):
            raise ValueError("archive provenance row is incomplete")
        supported_datasets = {
            "transaction_8h",
            "funding_rate",
            "mark_price_1h",
            "mark_price_1h_daily",
        }
        if row["dataset"] not in supported_datasets:
            raise ValueError("archive provenance dataset is invalid")
        expected_keys = required | ({"date"} if row["dataset"] == "mark_price_1h_daily" else set())
        if set(row) != expected_keys:
            raise ValueError("archive provenance row has unexpected fields")
        if not isinstance(row["symbol"], str) or re.fullmatch(r"[A-Z0-9]+", row["symbol"]) is None:
            raise ValueError("archive provenance symbol is invalid")
        if re.fullmatch(r"\d{4}-\d{2}", str(row["year_month"])) is None:
            raise ValueError("archive provenance year_month is invalid")
        if not str(row["url"]).startswith("https://data.binance.vision/"):
            raise ValueError("archive provenance URL is not official data.binance.vision")
        if row["checksum_url"] != row["url"] + ".CHECKSUM":
            raise ValueError("archive provenance checksum URL is invalid")
        raw_path = _resolve_manifest_path(root, row["raw_path"])
        if not raw_path.is_file() or raw_path.stat().st_size != row["size"]:
            raise ValueError(f"raw archive missing/size mismatch: {row['raw_path']}")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row["sha256"])):
            raise ValueError("archive provenance SHA-256 is invalid")
        if _sha256_file(raw_path) != row["sha256"]:
            raise ValueError(f"raw archive hash mismatch: {row['raw_path']}")
        raw_checksum_path = _resolve_manifest_path(root, row["raw_checksum_path"])
        if not raw_checksum_path.is_file():
            raise ValueError(f"raw checksum sidecar is missing: {row['raw_checksum_path']}")
        if _sha256_file(raw_checksum_path) != row["checksum_sha256"]:
            raise ValueError(f"raw checksum sidecar hash mismatch: {row['raw_checksum_path']}")
        sidecar_hash = _parse_checksum(
            raw_checksum_path.read_text(encoding="utf-8"), PurePosixPath(row["url"]).name
        )
        if sidecar_hash != row["sha256"]:
            raise ValueError(f"raw checksum sidecar disagrees with archive: {row['raw_path']}")
        if row["dataset"] == "mark_price_1h_daily":
            try:
                day = pd.Timestamp(row["date"], tz="UTC")
            except (TypeError, ValueError) as exc:
                raise ValueError("daily mark archive provenance date is invalid") from exc
            if row["date"] != day.strftime("%Y-%m-%d") or day != day.floor("D"):
                raise ValueError("daily mark archive provenance date is not canonical")
            if row["year_month"] != day.strftime("%Y-%m"):
                raise ValueError("daily mark archive month disagrees with date")
            filename = f"{row['symbol']}-1h-{row['date']}.zip"
            expected_url = (
                f"{_OFFICIAL_ARCHIVE_BASE_URL}/data/futures/um/daily/markPriceKlines/"
                f"{row['symbol']}/1h/{filename}"
            )
            if row["url"] != expected_url:
                raise ValueError("daily mark archive provenance URL is not canonical")
            expected_raw = (
                provenance_path.parent / "raw" / "mark_price_1h_daily" / row["symbol"] / filename
            ).resolve()
            expected_checksum = expected_raw.with_name(f"{filename}.CHECKSUM")
            if raw_path != expected_raw or raw_checksum_path != expected_checksum:
                raise ValueError("daily mark archive raw paths are not canonical")
        archive_rows.append(row)

    if archive_rows != sorted(
        archive_rows,
        key=lambda row: (
            row["dataset"],
            row["symbol"],
            row["year_month"],
            row.get("date", ""),
        ),
    ):
        raise ValueError("archive provenance rows are not canonically sorted")

    try:
        warmup_start = _utc(manifest["window"]["warmup_start"])
        evaluation_start = _utc(manifest["window"]["evaluation_start"])
        hard_end = _utc(manifest["window"]["hard_end_exclusive"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("snapshot manifest window is invalid") from exc
    rest_rows, rest_events = _verify_rest_provenance(
        rest_provenance_path,
        root=root,
        expected_count=sources.get("rest_request_count"),
        warmup_start=warmup_start,
        hard_end=hard_end,
    )
    archive_funding_months = {
        (str(row["symbol"]), str(row["year_month"]))
        for row in archive_rows
        if row["dataset"] == "funding_rate"
    }
    rest_months = {(str(row["symbol"]), str(row["year_month"])) for row in rest_rows}
    overlap = archive_funding_months & rest_months
    if overlap:
        raise ValueError(f"REST fallback overlaps checksummed funding archives: {sorted(overlap)}")

    bars_path = _resolve_manifest_path(root, file_entries["bars"]["path"])
    membership_path = _resolve_manifest_path(root, file_entries["membership"]["path"])
    bars = pd.read_parquet(bars_path)
    membership = pd.read_parquet(membership_path)
    expected_rest_months: set[tuple[str, str]] = set()
    for symbol in sorted(set(membership["symbol"].astype(str))):
        required_months = _member_bar_months(
            bars,
            membership,
            symbol=symbol,
            evaluation_start=evaluation_start,
        )
        for year, month in required_months:
            key = (symbol, f"{year:04d}-{month:02d}")
            if key not in archive_funding_months:
                expected_rest_months.add(key)
    if rest_months != expected_rest_months:
        raise ValueError(
            "REST funding fallback months differ from required archive gaps: "
            f"expected {sorted(expected_rest_months)}, got {sorted(rest_months)}"
        )

    funding_path = _resolve_manifest_path(root, file_entries["funding"]["path"])
    funding = pd.read_parquet(funding_path)
    if funding.duplicated(["funding_time", "symbol"]).any():
        raise ValueError("canonical funding contains duplicate events")
    funding["funding_time"] = pd.to_datetime(funding["funding_time"], utc=True, errors="raise")
    first_admissions = {
        symbol: _first_admission(membership, symbol=symbol)
        for symbol in sorted(set(membership["symbol"].astype(str)))
    }
    for row in funding.itertuples(index=False):
        first_admission = first_admissions.get(str(row.symbol))
        if first_admission is None or pd.Timestamp(row.funding_time) < first_admission:
            raise ValueError("canonical funding contains a pre-admission event")
    intervals = pd.to_numeric(funding["funding_interval_hours"], errors="coerce")
    if (
        intervals.isna().any()
        or not np.isfinite(intervals.to_numpy(dtype=float)).all()
        or (intervals <= 0).any()
    ):
        raise ValueError("canonical funding contains invalid derived intervals")
    canonical_events = {
        (str(row.symbol), int(pd.Timestamp(row.funding_time).value // 1_000_000)): float(
            row.funding_rate
        )
        for row in funding.itertuples(index=False)
    }
    for event in rest_events:
        key = (event["symbol"], event["funding_time"])
        first_admission = first_admissions.get(event["symbol"])
        if first_admission is None:
            raise ValueError("retained REST funding has a non-member symbol")
        event_time = pd.Timestamp(event["funding_time"], unit="ms", tz="UTC")
        if event_time < first_admission:
            continue
        if key not in canonical_events or canonical_events[key] != event["funding_rate"]:
            raise ValueError("canonical funding disagrees with retained REST response")
    retained_rest_keys = {
        (event["symbol"], event["funding_time"])
        for event in rest_events
        if pd.Timestamp(event["funding_time"], unit="ms", tz="UTC")
        >= first_admissions[event["symbol"]]
    }
    canonical_rest_keys = {
        (str(row.symbol), int(pd.Timestamp(row.funding_time).value // 1_000_000))
        for row in funding.itertuples(index=False)
        if (
            str(row.symbol),
            pd.Timestamp(row.funding_time).strftime("%Y-%m"),
        )
        in rest_months
    }
    if canonical_rest_keys != retained_rest_keys:
        raise ValueError("canonical funding does not exactly reproduce REST gap events")
    source_funding_times: dict[str, list[pd.Timestamp]] = {
        symbol: [] for symbol in first_admissions
    }
    for archive_row in archive_rows:
        if archive_row["dataset"] != "funding_rate":
            continue
        symbol = str(archive_row["symbol"])
        frame = _parse_funding_archive(
            _resolve_manifest_path(root, archive_row["raw_path"]),
            symbol=symbol,
            warmup_start=warmup_start,
            hard_end=hard_end,
        )
        source_funding_times.setdefault(symbol, []).extend(frame["funding_time"].tolist())
    for event in rest_events:
        source_funding_times.setdefault(event["symbol"], []).append(
            pd.Timestamp(event["funding_time"], unit="ms", tz="UTC")
        )
    expected_rest_intervals: dict[tuple[str, int], float] = {}
    for symbol, times in source_funding_times.items():
        ordered_times = sorted(times)
        if len(ordered_times) != len(set(ordered_times)):
            raise ValueError(f"duplicate funding event across retained sources for {symbol}")
        for index, timestamp in enumerate(ordered_times):
            key = (symbol, int(timestamp.value // 1_000_000))
            if key not in retained_rest_keys:
                continue
            if index > 0:
                delta = timestamp - ordered_times[index - 1]
            elif len(ordered_times) > 1:
                delta = ordered_times[1] - timestamp
            else:
                raise ValueError(f"retained REST funding event is isolated for {symbol}")
            expected_rest_intervals[key] = float(delta / pd.Timedelta(hours=1))
    for symbol, symbol_funding in funding.groupby("symbol", observed=True, sort=True):
        ordered = symbol_funding.sort_values("funding_time").reset_index(drop=True)
        for _, row in ordered.iterrows():
            key = (str(symbol), int(pd.Timestamp(row["funding_time"]).value // 1_000_000))
            if key not in retained_rest_keys:
                continue
            expected_hours = expected_rest_intervals.get(key)
            if expected_hours is None:
                raise ValueError("canonical REST funding lacks a retained source interval")
            if not np.isclose(
                float(row["funding_interval_hours"]),
                expected_hours,
                rtol=0.0,
                atol=1e-12,
            ):
                raise ValueError("canonical REST funding interval is not adjacent-event derived")

    required_mark_reasons: dict[tuple[str, int], tuple[str, ...]] = {}
    for symbol in sorted(set(membership["symbol"].astype(str))):
        symbol_reasons = _required_mark_reasons(
            bars,
            funding,
            membership,
            symbol=symbol,
        )
        for timestamp, reasons in symbol_reasons.items():
            key = (symbol, int(timestamp.value // 1_000_000))
            if key in required_mark_reasons:
                raise ValueError("required mark-price scope contains duplicate timestamps")
            required_mark_reasons[key] = reasons
    _, retained_mark_sources = _verify_mark_rest_provenance(
        mark_rest_provenance_path,
        root=root,
        expected_count=sources.get("mark_rest_request_count"),
        warmup_start=warmup_start,
        hard_end=hard_end,
        archive_rows=archive_rows,
        required_reasons=required_mark_reasons,
    )

    mark_prices_path = _resolve_manifest_path(root, file_entries["mark_prices"]["path"])
    mark_prices = pd.read_parquet(mark_prices_path)
    required_mark_columns = {"mark_time", "symbol", "mark_price"}
    if required_mark_columns - set(mark_prices):
        raise ValueError("canonical mark-price panel is incomplete")
    if mark_prices.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("canonical mark-price panel contains duplicate observations")
    mark_prices["mark_time"] = pd.to_datetime(mark_prices["mark_time"], utc=True, errors="raise")
    mark_prices["mark_price"] = pd.to_numeric(mark_prices["mark_price"], errors="raise")
    if (
        not np.isfinite(mark_prices["mark_price"].to_numpy(dtype=float)).all()
        or (mark_prices["mark_price"] <= 0).any()
    ):
        raise ValueError("canonical mark-price panel contains invalid prices")
    risk_keys = {
        key for key, reasons in required_mark_reasons.items() if "risk_boundary" in reasons
    }
    canonical_risk_keys = {
        (str(row.symbol), int(pd.Timestamp(row.mark_time).value // 1_000_000))
        for row in mark_prices.itertuples(index=False)
    }
    if canonical_risk_keys != risk_keys:
        raise ValueError("canonical mark-price panel differs from exact executable boundaries")

    required_funding_mark_columns = {"mark_time", "mark_price"}
    if required_funding_mark_columns - set(funding):
        raise ValueError("canonical funding is missing attached mark prices")
    funding_mark_times = pd.to_datetime(funding["mark_time"], utc=True, errors="raise")
    if not funding_mark_times.equals(
        pd.to_datetime(funding["funding_time"], utc=True, errors="raise").dt.floor("h")
    ):
        raise ValueError("canonical funding marks are not exact funding floor-hours")
    funding_mark_prices = pd.to_numeric(funding["mark_price"], errors="raise")
    if (
        not np.isfinite(funding_mark_prices.to_numpy(dtype=float)).all()
        or (funding_mark_prices <= 0).any()
    ):
        raise ValueError("canonical funding contains invalid mark prices")

    canonical_marks: dict[tuple[str, int], float] = {}
    for row in mark_prices.itertuples(index=False):
        key = (str(row.symbol), int(pd.Timestamp(row.mark_time).value // 1_000_000))
        canonical_marks[key] = float(row.mark_price)
    for row in funding.itertuples(index=False):
        key = (str(row.symbol), int(pd.Timestamp(row.mark_time).value // 1_000_000))
        value = float(row.mark_price)
        previous = canonical_marks.setdefault(key, value)
        if previous != value:
            raise ValueError("canonical risk/funding mark prices disagree")
    if set(canonical_marks) != set(required_mark_reasons):
        raise ValueError("canonical mark prices differ from exact required mark scope")
    if canonical_marks != retained_mark_sources:
        raise ValueError("canonical mark prices disagree with retained archive/REST sources")
    return manifest


def _verify_mark_rest_provenance(
    provenance_path: Path,
    *,
    root: Path,
    expected_count: Any,
    warmup_start: pd.Timestamp,
    hard_end: pd.Timestamp,
    archive_rows: list[dict[str, Any]],
    required_reasons: dict[tuple[str, int], tuple[str, ...]],
) -> tuple[list[dict[str, Any]], dict[tuple[str, int], float]]:
    """Verify exact missing-hour mark REST requests and their archive bindings."""

    if (
        isinstance(expected_count, bool)
        or not isinstance(expected_count, int)
        or expected_count < 0
    ):
        raise ValueError("mark REST provenance count is invalid")
    lines = provenance_path.read_text(encoding="utf-8").splitlines()
    if len(lines) != expected_count:
        raise ValueError("mark REST provenance count mismatch")

    archive_index: dict[tuple[str, str], dict[str, Any]] = {}
    daily_index: dict[tuple[str, str], dict[str, Any]] = {}
    for archive_row in archive_rows:
        if archive_row.get("dataset") == "mark_price_1h":
            key = (str(archive_row.get("symbol")), str(archive_row.get("year_month")))
            if key in archive_index:
                raise ValueError(f"duplicate mark-price archive provenance month: {key}")
            archive_index[key] = archive_row
        elif archive_row.get("dataset") == "mark_price_1h_daily":
            key = (str(archive_row.get("symbol")), str(archive_row.get("date")))
            if key in daily_index:
                raise ValueError(f"duplicate daily mark-price archive provenance date: {key}")
            daily_index[key] = archive_row

    required_keys = {
        "dataset",
        "symbol",
        "year_month",
        "mark_time",
        "page",
        "endpoint",
        "params",
        "required_for",
        "archive_raw_path",
        "archive_sha256",
        "retrieved_at",
        "response_rows",
        "sha256",
        "size",
        "raw_path",
    }
    rows: list[dict[str, Any]] = []
    rest_values: dict[tuple[str, int], float] = {}
    raw_paths: set[str] = set()
    request_keys: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
    event_keys: set[tuple[str, int]] = set()
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("mark REST provenance contains invalid JSON") from exc
        if not isinstance(row, dict) or set(row) != required_keys or line + "\n" != _json_line(row):
            raise ValueError("mark REST provenance is incomplete or non-canonical JSONL")
        if row["dataset"] != "mark_price_rest":
            raise ValueError("mark REST provenance dataset is invalid")
        if row["endpoint"] != _OFFICIAL_MARK_PRICE_KLINES_URL:
            raise ValueError("mark REST provenance endpoint is not official Binance USD-M")

        symbol = row["symbol"]
        if not isinstance(symbol, str) or re.fullmatch(r"[A-Z0-9]+", symbol) is None:
            raise ValueError("mark REST provenance symbol is invalid")
        try:
            mark_time = pd.Timestamp(row["mark_time"])
        except (TypeError, ValueError) as exc:
            raise ValueError("mark REST provenance mark_time is invalid") from exc
        if mark_time.tzinfo is None or mark_time.utcoffset() != pd.Timedelta(0):
            raise ValueError("mark REST provenance mark_time must be UTC")
        mark_time = mark_time.tz_convert("UTC")
        if row["mark_time"] != mark_time.isoformat() or mark_time != mark_time.floor("h"):
            raise ValueError("mark REST provenance mark_time is not a canonical exact hour")
        if mark_time < warmup_start or mark_time >= hard_end:
            raise ValueError("mark REST provenance mark_time is outside the snapshot window")
        year_month = mark_time.strftime("%Y-%m")
        if row["year_month"] != year_month:
            raise ValueError("mark REST provenance month disagrees with mark_time")
        if row["page"] != 1 or isinstance(row["page"], bool):
            raise ValueError("mark REST provenance page must be exactly one")

        params = row["params"]
        expected_params = {
            "symbol": symbol,
            "interval": "1h",
            "startTime": str(int(mark_time.value // 1_000_000)),
            "endTime": str(int(mark_time.value // 1_000_000)),
            "limit": "1",
        }
        if params != expected_params:
            raise ValueError("mark REST provenance params are not the exact requested hour")
        request_key = (row["endpoint"], tuple(sorted(params.items())))
        if request_key in request_keys:
            raise ValueError("mark REST provenance repeats request params")
        request_keys.add(request_key)

        event_key = (symbol, int(mark_time.value // 1_000_000))
        expected_reasons = required_reasons.get(event_key)
        required_for = row["required_for"]
        if (
            expected_reasons is None
            or not isinstance(required_for, list)
            or required_for != list(expected_reasons)
        ):
            raise ValueError("mark REST fallback reasons differ from required scope")
        if event_key in event_keys:
            raise ValueError("mark REST provenance repeats a requested event")
        event_keys.add(event_key)

        archive_key = (symbol, year_month)
        archive_source = archive_index.get(archive_key)
        if archive_source is None:
            raise ValueError("mark REST fallback lacks a checksummed archive month")
        if (
            row["archive_raw_path"] != archive_source["raw_path"]
            or row["archive_sha256"] != archive_source["sha256"]
        ):
            raise ValueError("mark REST fallback archive binding is invalid")
        try:
            retrieved_at = pd.Timestamp(row["retrieved_at"])
        except (TypeError, ValueError) as exc:
            raise ValueError("mark REST provenance retrieval time is invalid") from exc
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() != pd.Timedelta(0):
            raise ValueError("mark REST provenance retrieval time must be UTC")
        if row["response_rows"] != 1 or isinstance(row["response_rows"], bool):
            raise ValueError("mark REST provenance must retain exactly one response row")
        if isinstance(row["size"], bool) or not isinstance(row["size"], int) or row["size"] < 0:
            raise ValueError("mark REST provenance size is invalid")
        if re.fullmatch(r"[0-9a-f]{64}", str(row["sha256"])) is None:
            raise ValueError("mark REST provenance SHA-256 is invalid")

        raw_path_value = row["raw_path"]
        if not isinstance(raw_path_value, str) or raw_path_value in raw_paths:
            raise ValueError("mark REST provenance repeats or has invalid raw response path")
        raw_paths.add(raw_path_value)
        raw_path = _resolve_manifest_path(root, raw_path_value)
        expected_raw_path = (
            provenance_path.parent
            / "raw"
            / "mark_price_rest"
            / symbol
            / year_month
            / f"{mark_time.strftime('%Y%m%dT%H%M%SZ')}.json"
        ).resolve()
        if raw_path != expected_raw_path:
            raise ValueError("mark REST provenance raw response path is not canonical")
        if not raw_path.is_file() or raw_path.stat().st_size != row["size"]:
            raise ValueError(f"raw mark REST response missing/size mismatch: {raw_path_value}")
        if _sha256_file(raw_path) != row["sha256"]:
            raise ValueError(f"raw mark REST response hash mismatch: {raw_path_value}")
        raw_bytes = raw_path.read_bytes()
        payload = _decode_mark_rest_response(raw_bytes)
        if raw_bytes != _canonical_rest_response(payload):
            raise ValueError("raw mark REST response is not canonical JSON")
        if len(payload) != row["response_rows"]:
            raise ValueError("mark REST provenance response row count mismatch")
        observations = _validate_mark_rest_payload(
            payload,
            requested_time_ms=event_key[1],
            limit=1,
        )
        rest_values[event_key] = observations[0][1]
        rows.append(row)

    if rows != sorted(rows, key=lambda row: (row["symbol"], row["mark_time"])):
        raise ValueError("mark REST provenance rows are not canonically sorted")

    required_months: set[tuple[str, str]] = set()
    for symbol, timestamp_ms in required_reasons:
        timestamp = pd.Timestamp(timestamp_ms, unit="ms", tz="UTC")
        if timestamp < warmup_start or timestamp >= hard_end or timestamp != timestamp.floor("h"):
            raise ValueError("required mark-price scope contains an invalid timestamp")
        required_months.add((symbol, timestamp.strftime("%Y-%m")))

    archive_values: dict[tuple[str, int], float] = {}
    for archive_key in sorted(required_months):
        if archive_key not in archive_index:
            raise ValueError("required mark-price scope lacks a checksummed archive month")
        archive_source = archive_index[archive_key]
        archive_path = _resolve_manifest_path(root, archive_source["raw_path"])
        frame = _parse_kline_archive(
            archive_path,
            symbol=archive_key[0],
            warmup_start=warmup_start - pd.Timedelta(hours=1),
            hard_end=hard_end,
            expected_hours=1,
        )
        if frame.duplicated(["open_time", "symbol"]).any():
            raise ValueError("checksummed mark-price archive contains duplicate hours")
        month_values = {
            int(pd.Timestamp(row.open_time).value // 1_000_000): float(row.open)
            for row in frame.itertuples(index=False)
        }
        for key in required_reasons:
            if key[0] != archive_key[0]:
                continue
            if pd.Timestamp(key[1], unit="ms", tz="UTC").strftime("%Y-%m") != archive_key[1]:
                continue
            if key[1] in month_values:
                archive_values[key] = month_values[key[1]]

    missing_after_monthly = set(required_reasons) - set(archive_values)
    daily_values: dict[tuple[str, int], float] = {}
    for daily_key, daily_source in sorted(daily_index.items()):
        day = pd.Timestamp(daily_key[1], tz="UTC")
        if day < warmup_start.floor("D") or day >= hard_end:
            raise ValueError("daily mark-price archive is outside the snapshot window")
        daily_path = _resolve_manifest_path(root, daily_source["raw_path"])
        frame = _parse_kline_archive(
            daily_path,
            symbol=daily_key[0],
            warmup_start=warmup_start - pd.Timedelta(hours=1),
            hard_end=hard_end,
            expected_hours=1,
        )
        if frame.empty or frame.duplicated(["open_time", "symbol"]).any():
            raise ValueError("checksummed daily mark-price archive is empty or duplicated")
        if not pd.to_datetime(frame["open_time"], utc=True).dt.floor("D").eq(day).all():
            raise ValueError("daily mark-price archive contains a foreign UTC date")
        values = {
            int(pd.Timestamp(row.open_time).value // 1_000_000): float(row.open)
            for row in frame.itertuples(index=False)
        }
        contributions = {
            key: values[key[1]]
            for key in missing_after_monthly
            if key[0] == daily_key[0]
            and pd.Timestamp(key[1], unit="ms", tz="UTC").strftime("%Y-%m-%d") == daily_key[1]
            and key[1] in values
        }
        if not contributions:
            raise ValueError(
                "retained daily mark-price archive contributes no monthly-gap required hour"
            )
        if set(daily_values).intersection(contributions):
            raise ValueError("daily mark-price archives overlap required observations")
        daily_values.update(contributions)

    expected_rest_keys = missing_after_monthly - set(daily_values)
    if event_keys != expected_rest_keys:
        raise ValueError("mark REST fallback scope differs from required monthly/daily gaps")
    if (
        set(archive_values) & set(daily_values)
        or set(archive_values) & set(rest_values)
        or set(daily_values) & set(rest_values)
    ):
        raise ValueError("mark-price fallback sources violate source priority")
    retained_sources = archive_values | daily_values | rest_values
    if set(retained_sources) != set(required_reasons):
        raise ValueError("retained mark sources do not exactly cover required mark scope")
    return rows, retained_sources


def _verify_rest_provenance(
    provenance_path: Path,
    *,
    root: Path,
    expected_count: Any,
    warmup_start: pd.Timestamp,
    hard_end: pd.Timestamp,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Verify canonical REST provenance, retained pages, and deterministic pagination."""

    if (
        isinstance(expected_count, bool)
        or not isinstance(expected_count, int)
        or expected_count < 0
    ):
        raise ValueError("REST provenance count is invalid")
    lines = provenance_path.read_text(encoding="utf-8").splitlines()
    if len(lines) != expected_count:
        raise ValueError("REST provenance count mismatch")
    rows: list[dict[str, Any]] = []
    events: list[dict[str, Any]] = []
    page_details: dict[tuple[str, str], list[dict[str, Any]]] = {}
    raw_paths: set[str] = set()
    request_keys: set[tuple[str, tuple[tuple[str, str], ...]]] = set()
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError("REST provenance contains invalid JSON") from exc
        if not isinstance(row, dict) or line + "\n" != _json_line(row):
            raise ValueError("REST provenance is not canonical JSONL")
        required = {
            "dataset",
            "symbol",
            "year_month",
            "page",
            "endpoint",
            "params",
            "retrieved_at",
            "response_rows",
            "sha256",
            "size",
            "raw_path",
        }
        if required - set(row):
            raise ValueError("REST provenance row is incomplete")
        if row["dataset"] != "funding_rate_rest":
            raise ValueError("REST provenance dataset is invalid")
        if row["endpoint"] != _OFFICIAL_FUNDING_RATE_URL:
            raise ValueError("REST provenance endpoint is not official Binance USD-M")
        symbol = row["symbol"]
        year_month = row["year_month"]
        if not isinstance(symbol, str) or re.fullmatch(r"[A-Z0-9]+", symbol) is None:
            raise ValueError("REST provenance symbol is invalid")
        match = re.fullmatch(r"(\d{4})-(\d{2})", str(year_month))
        if match is None:
            raise ValueError("REST provenance year_month is invalid")
        year, month = int(match.group(1)), int(match.group(2))
        try:
            month_start = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
        except ValueError as exc:
            raise ValueError("REST provenance year_month is invalid") from exc
        month_end = month_start + pd.offsets.MonthBegin(1)
        expected_start = max(month_start, warmup_start)
        expected_end = min(month_end, hard_end)
        if expected_start >= expected_end:
            raise ValueError("REST provenance month is outside the snapshot window")

        page = row["page"]
        if isinstance(page, bool) or not isinstance(page, int) or page < 1:
            raise ValueError("REST provenance page is invalid")
        params = row["params"]
        required_params = {"symbol", "startTime", "endTime", "limit"}
        if (
            not isinstance(params, dict)
            or set(params) != required_params
            or not all(isinstance(value, str) for value in params.values())
        ):
            raise ValueError("REST provenance params are invalid")
        if params["symbol"] != symbol:
            raise ValueError("REST provenance symbol disagrees with request params")
        try:
            start_ms = int(params["startTime"])
            end_ms = int(params["endTime"])
            limit = int(params["limit"])
        except ValueError as exc:
            raise ValueError("REST provenance numeric params are invalid") from exc
        if str(start_ms) != params["startTime"] or str(end_ms) != params["endTime"]:
            raise ValueError("REST provenance time params are not canonical integers")
        if str(limit) != params["limit"] or limit <= 0 or limit > 1000:
            raise ValueError("REST provenance limit is invalid")
        expected_end_ms = int(expected_end.value // 1_000_000) - 1
        if end_ms != expected_end_ms or start_ms > end_ms:
            raise ValueError("REST provenance request window is invalid")
        try:
            retrieved_at = pd.Timestamp(row["retrieved_at"])
        except (TypeError, ValueError) as exc:
            raise ValueError("REST provenance retrieval time is invalid") from exc
        if retrieved_at.tzinfo is None or retrieved_at.utcoffset() != pd.Timedelta(0):
            raise ValueError("REST provenance retrieval time must be UTC")
        if (
            isinstance(row["response_rows"], bool)
            or not isinstance(row["response_rows"], int)
            or row["response_rows"] < 0
        ):
            raise ValueError("REST provenance response row count is invalid")
        if isinstance(row["size"], bool) or not isinstance(row["size"], int) or row["size"] < 0:
            raise ValueError("REST provenance size is invalid")
        if not re.fullmatch(r"[0-9a-f]{64}", str(row["sha256"])):
            raise ValueError("REST provenance SHA-256 is invalid")
        raw_path_value = row["raw_path"]
        if raw_path_value in raw_paths:
            raise ValueError("REST provenance repeats a raw response path")
        raw_paths.add(raw_path_value)
        request_key = (row["endpoint"], tuple(sorted(params.items())))
        if request_key in request_keys:
            raise ValueError("REST provenance repeats request params")
        request_keys.add(request_key)
        raw_path = _resolve_manifest_path(root, raw_path_value)
        expected_raw_path = (
            provenance_path.parent
            / "raw"
            / "funding_rate_rest"
            / symbol
            / str(year_month)
            / f"page-{page:04d}.json"
        ).resolve()
        if raw_path != expected_raw_path:
            raise ValueError("REST provenance raw response path is not canonical")
        if not raw_path.is_file() or raw_path.stat().st_size != row["size"]:
            raise ValueError(f"raw REST response missing/size mismatch: {raw_path_value}")
        if _sha256_file(raw_path) != row["sha256"]:
            raise ValueError(f"raw REST response hash mismatch: {raw_path_value}")
        raw_bytes = raw_path.read_bytes()
        payload = _decode_funding_rest_response(raw_bytes)
        if raw_bytes != _canonical_rest_response(payload):
            raise ValueError("raw REST response is not canonical JSON")
        if len(payload) != row["response_rows"]:
            raise ValueError("REST provenance response row count mismatch")
        funding_times = _validate_funding_rest_payload(
            payload,
            symbol=symbol,
            start_ms=start_ms,
            end_ms=end_ms,
            limit=limit,
        )
        detail = {
            "row": row,
            "start_ms": start_ms,
            "end_ms": end_ms,
            "limit": limit,
            "funding_times": funding_times,
            "payload": payload,
            "expected_start_ms": int(expected_start.value // 1_000_000),
        }
        page_details.setdefault((symbol, str(year_month)), []).append(detail)
        rows.append(row)

    sorted_rows = sorted(rows, key=lambda row: (row["symbol"], row["year_month"], row["page"]))
    if rows != sorted_rows:
        raise ValueError("REST provenance rows are not canonically sorted")
    for (symbol, year_month), details in sorted(page_details.items()):
        details.sort(key=lambda detail: detail["row"]["page"])
        pages = [detail["row"]["page"] for detail in details]
        if pages != list(range(1, len(details) + 1)):
            raise ValueError(f"REST pagination pages are not contiguous for {symbol} {year_month}")
        if details[0]["start_ms"] != details[0]["expected_start_ms"]:
            raise ValueError(f"REST pagination does not start at month boundary for {symbol}")
        seen_times: set[int] = set()
        for index, detail in enumerate(details):
            funding_times = detail["funding_times"]
            duplicates = seen_times.intersection(funding_times)
            if duplicates:
                raise ValueError(f"duplicate REST events across pages for {symbol}")
            seen_times.update(funding_times)
            for item, funding_time in zip(detail["payload"], funding_times, strict=True):
                events.append(
                    {
                        "symbol": symbol,
                        "funding_time": funding_time,
                        "funding_rate": float(item["fundingRate"]),
                    }
                )
            if index == 0:
                continue
            previous = details[index - 1]
            if len(previous["payload"]) != previous["limit"]:
                raise ValueError(f"REST pagination continued after a short page for {symbol}")
            if not previous["funding_times"]:
                raise ValueError(f"REST pagination continued after an empty page for {symbol}")
            expected_cursor = previous["funding_times"][-1] + 1
            if detail["start_ms"] != expected_cursor:
                raise ValueError(f"REST pagination cursor is non-deterministic for {symbol}")
            if detail["end_ms"] != previous["end_ms"] or detail["limit"] != previous["limit"]:
                raise ValueError(f"REST pagination params changed within month for {symbol}")
        final = details[-1]
        if len(final["payload"]) == final["limit"] and final["funding_times"][-1] < final["end_ms"]:
            raise ValueError(f"REST pagination lacks terminal response for {symbol}")
        if not seen_times:
            raise ValueError(f"missing REST month coverage for {symbol} {year_month}")
    return rows, events


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        config = tomllib.load(handle)
    required_sections = {"data", "splits", "universe"}
    missing = required_sections - set(config)
    if missing:
        raise ValueError(f"snapshot config missing sections: {sorted(missing)}")
    required_data = {
        "source",
        "archive_base_url",
        "archive_s3_url",
        "exchange_info_url",
        "funding_rate_url",
        "mark_price_klines_url",
        "warmup_start",
        "hard_end_exclusive",
        "transaction_interval",
        "mark_price_interval",
        "checksum_policy",
        "parser_version",
    }
    missing_data = required_data - set(config["data"])
    if missing_data:
        raise ValueError(f"snapshot config missing data keys: {sorted(missing_data)}")
    return config


def _make_http_client() -> httpx.Client:
    return httpx.Client(timeout=60.0, follow_redirects=True)


def _request(client: httpx.Client, url: str, *, params: dict[str, str] | None = None) -> bytes:
    last_error: Exception | None = None
    for attempt in range(_HTTP_RETRIES):
        try:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.content
        except (httpx.HTTPError, OSError) as exc:
            last_error = exc
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            if status is not None and status < 500 and status != 429:
                break
            if attempt + 1 < _HTTP_RETRIES:
                time.sleep(0.05 * (2**attempt))
    raise ValueError(f"failed official Binance request {url}: {last_error}") from last_error


def _request_optional_not_found(client: httpx.Client, url: str) -> bytes | None:
    """Return ``None`` only for an authoritative 404; fail closed for every other error."""

    last_error: Exception | None = None
    for attempt in range(_HTTP_RETRIES):
        try:
            response = client.get(url)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.content
        except (httpx.HTTPError, OSError) as exc:
            last_error = exc
            status = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            if status is not None and status < 500 and status != 429:
                break
            if attempt + 1 < _HTTP_RETRIES:
                time.sleep(0.05 * (2**attempt))
    raise ValueError(f"failed official Binance request {url}: {last_error}") from last_error


def _fetch_exchange_info(client: httpx.Client, url: str) -> dict[str, Any]:
    try:
        payload = json.loads(_request(client, url))
    except json.JSONDecodeError as exc:
        raise ValueError("exchangeInfo is not valid JSON") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("symbols"), list):
        raise ValueError("exchangeInfo requires a symbols array")
    return payload


def _canonical_exchange_info(payload: dict[str, Any]) -> dict[str, Any]:
    result = {key: value for key, value in payload.items() if key != "serverTime"}
    result["symbols"] = sorted(payload["symbols"], key=lambda item: str(item.get("symbol", "")))
    return result


def _list_s3(
    client: httpx.Client, s3_url: str, prefix: str, *, delimiter: str | None
) -> tuple[list[str], list[str]]:
    keys: list[str] = []
    prefixes: list[str] = []
    marker = ""
    while True:
        params = {"prefix": prefix}
        if delimiter is not None:
            params["delimiter"] = delimiter
        if marker:
            params["marker"] = marker
        try:
            root = ElementTree.fromstring(_request(client, s3_url, params=params))
        except ElementTree.ParseError as exc:
            raise ValueError(f"invalid Binance archive listing for {prefix}") from exc
        page_keys = [(node.findtext("{*}Key") or "") for node in root.findall(".//{*}Contents")]
        page_prefixes = [
            (node.findtext("{*}Prefix") or "") for node in root.findall(".//{*}CommonPrefixes")
        ]
        keys.extend(value for value in page_keys if value)
        prefixes.extend(value for value in page_prefixes if value)
        truncated = (root.findtext("{*}IsTruncated") or "false").lower() == "true"
        if not truncated:
            break
        next_marker = root.findtext("{*}NextMarker")
        candidates = page_keys + page_prefixes
        marker = next_marker or (candidates[-1] if candidates else "")
        if not marker:
            raise ValueError(f"truncated Binance listing lacks continuation marker: {prefix}")
    return sorted(set(keys)), sorted(set(prefixes))


def _discover_symbols(client: httpx.Client, s3_url: str, prefix: str) -> tuple[str, ...]:
    keys, prefixes = _list_s3(client, s3_url, prefix, delimiter="/")
    symbols = {
        value[len(prefix) :].split("/", 1)[0]
        for value in prefixes + keys
        if value.startswith(prefix) and value[len(prefix) :]
    }
    if not symbols:
        raise ValueError("Binance archive symbol discovery returned no symbols")
    return tuple(sorted(symbols))


def _candidate_symbols(
    discovered: tuple[str, ...], current: dict[str, dict[str, Any]], hard_end: pd.Timestamp
) -> tuple[str, ...]:
    result: list[str] = []
    for symbol in discovered:
        if (
            symbol in _KNOWN_ARCHIVE_ONLY_INDEXES
            or "_" in symbol
            or not is_eligible_usdt_perpetual(symbol)
        ):
            continue
        info = current.get(symbol)
        if info is not None:
            onboard = _timestamp_from_scalar(info.get("onboardDate"))
            if pd.notna(onboard) and onboard >= hard_end:
                continue
            if info.get("contractType") != "PERPETUAL" or info.get("underlyingType") != "COIN":
                continue
        result.append(symbol)
    return tuple(sorted(result))


def _archive_prefix(dataset: str, symbol: str, interval: str | None) -> str:
    if dataset == "transaction_8h":
        return f"data/futures/um/monthly/klines/{symbol}/{interval}/"
    if dataset == "mark_price_1h":
        return f"data/futures/um/monthly/markPriceKlines/{symbol}/{interval}/"
    if dataset == "funding_rate":
        return f"data/futures/um/monthly/fundingRate/{symbol}/"
    raise ValueError(f"unsupported snapshot dataset: {dataset}")


def _list_monthly_archives(
    client: httpx.Client,
    *,
    s3_url: str,
    base_url: str,
    dataset: str,
    symbol: str,
    interval: str | None,
    warmup_start: pd.Timestamp,
    hard_end: pd.Timestamp,
) -> list[_Archive]:
    prefix = _archive_prefix(dataset, symbol, interval)
    keys, _ = _list_s3(client, s3_url, prefix, delimiter=None)
    key_set = set(keys)
    archives: list[_Archive] = []
    for key in keys:
        if not key.endswith(".zip"):
            continue
        match = re.search(r"-(\d{4})-(\d{2})\.zip$", key)
        if match is None:
            raise ValueError(f"unrecognised Binance monthly archive name: {key}")
        year, month = int(match.group(1)), int(match.group(2))
        month_start = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
        month_end = month_start + pd.offsets.MonthBegin(1)
        if month_end <= warmup_start or month_start >= hard_end:
            continue
        checksum_key = key + ".CHECKSUM"
        if checksum_key not in key_set:
            raise ValueError(f"Binance checksum sidecar is missing from catalog: {checksum_key}")
        archives.append(
            _Archive(
                dataset=dataset,
                symbol=symbol,
                year=year,
                month=month,
                key=key,
                url=f"{base_url.rstrip('/')}/{key}",
                checksum_url=f"{base_url.rstrip('/')}/{checksum_key}",
            )
        )
    return sorted(archives)


def _member_bar_months(
    bars: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    symbol: str,
    evaluation_start: pd.Timestamp,
) -> set[tuple[int, int]]:
    """Return months where ``symbol`` is both a weekly member and executable.

    Binance archive catalogs legitimately contain gaps around suspensions and relistings.  A gap
    in transaction bars therefore means that the contract is not executable, while a funding
    archive gap during an executable membership interval is a fatal accounting omission.
    """

    member_rows = membership.loc[membership["symbol"].eq(symbol), "reconstitution_time"]
    member_weeks = set(pd.to_datetime(member_rows, utc=True))
    first_admission = _first_admission(membership, symbol=symbol)
    symbol_times = pd.to_datetime(
        bars.loc[
            bars["symbol"].eq(symbol)
            & pd.to_datetime(bars["open_time"], utc=True).ge(
                max(first_admission, _utc(evaluation_start))
            ),
            "open_time",
        ],
        utc=True,
    )
    if symbol_times.empty or not member_weeks:
        return set()
    week_starts = symbol_times.dt.floor("D") - pd.to_timedelta(symbol_times.dt.weekday, unit="D")
    executable_member_times = symbol_times[week_starts.isin(member_weeks)]
    return {(timestamp.year, timestamp.month) for timestamp in executable_member_times}


def _first_admission(membership: pd.DataFrame, *, symbol: str) -> pd.Timestamp:
    required = {"reconstitution_time", "symbol"}
    if required - set(membership):
        raise ValueError("membership is missing columns needed for first admission")
    rows = membership.loc[membership["symbol"].astype(str).eq(symbol), "reconstitution_time"]
    if rows.empty:
        raise ValueError(f"first admission requested for non-member symbol {symbol}")
    return pd.to_datetime(rows, utc=True, errors="raise").min()


def _funding_since_first_admission(
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    symbol: str,
) -> pd.DataFrame:
    """Filter already-derived funding events to the first possible holding time."""

    required = {"funding_time", "symbol", "funding_rate", "funding_interval_hours"}
    if required - set(funding):
        raise ValueError("funding is missing columns needed for admission scope")
    if not funding["symbol"].astype(str).eq(symbol).all():
        raise ValueError(f"funding admission scope contains a foreign symbol for {symbol}")
    first_admission = _first_admission(membership, symbol=symbol)
    times = pd.to_datetime(funding["funding_time"], utc=True, errors="raise")
    result = funding.loc[times >= first_admission].copy()
    result["funding_time"] = times.loc[result.index]
    return result.sort_values("funding_time").reset_index(drop=True)


def _require_active_hard_end_coverage(
    archives: list[_Archive], current_info: dict[str, Any] | None, *, hard_end: pd.Timestamp
) -> None:
    """Reject a missing final archive for a contract known active through the cutoff."""

    if current_info is None:
        return
    delivery = _timestamp_from_scalar(current_info.get("deliveryDate"))
    if pd.notna(delivery) and delivery < hard_end:
        return
    final_month = hard_end - pd.Timedelta(nanoseconds=1)
    latest = archives[-1]
    if (latest.year, latest.month) != (final_month.year, final_month.month):
        raise ValueError(
            f"active {latest.dataset} contract {latest.symbol} lacks hard-end archive "
            f"{final_month.year:04d}-{final_month.month:02d}"
        )


def _acquire_archive(
    client: httpx.Client,
    archive: _Archive,
    *,
    raw_dir: Path,
    root: Path,
    resume: bool,
) -> tuple[Path, dict[str, Any]]:
    directory = raw_dir / archive.dataset / archive.symbol
    directory.mkdir(parents=True, exist_ok=True)
    zip_path = directory / archive.filename
    checksum_path = directory / f"{archive.filename}.CHECKSUM"
    checksum_bytes: bytes | None = None
    expected: str | None = None
    cached_is_valid = False
    if resume and zip_path.is_file() and checksum_path.is_file():
        try:
            checksum_bytes = checksum_path.read_bytes()
            expected = _parse_checksum(checksum_bytes.decode("utf-8"), archive.filename)
            cached_is_valid = _sha256_file(zip_path) == expected
        except (OSError, UnicodeDecodeError, ValueError):
            # Recover from an incomplete/corrupt cache by reacquiring both official objects.
            checksum_bytes = None
            expected = None
    if not cached_is_valid:
        checksum_bytes = _request(client, archive.checksum_url)
        expected = _parse_checksum(checksum_bytes.decode("utf-8"), archive.filename)
    if not cached_is_valid:
        zip_bytes = _request(client, archive.url)
        actual = hashlib.sha256(zip_bytes).hexdigest()
        if actual != expected:
            raise ValueError(
                f"Binance SHA-256 mismatch for {archive.url}: expected {expected}, got {actual}"
            )
        _atomic_bytes(zip_path, zip_bytes)
    assert checksum_bytes is not None and expected is not None
    _atomic_bytes(checksum_path, checksum_bytes)
    actual = _sha256_file(zip_path)
    if actual != expected:
        raise ValueError(f"cached archive failed Binance checksum: {zip_path}")
    source = {
        "dataset": archive.dataset,
        "symbol": archive.symbol,
        "year_month": f"{archive.year:04d}-{archive.month:02d}",
        "url": archive.url,
        "checksum_url": archive.checksum_url,
        "sha256": expected,
        "size": zip_path.stat().st_size,
        "raw_path": _relative(zip_path, root),
        "checksum_sha256": hashlib.sha256(checksum_bytes).hexdigest(),
        "raw_checksum_path": _relative(checksum_path, root),
    }
    return zip_path, source


def _acquire_archives(
    client: httpx.Client,
    archives: list[_Archive],
    *,
    raw_dir: Path,
    root: Path,
    resume: bool,
) -> list[tuple[Path, dict[str, Any]]]:
    """Acquire independent monthly files concurrently while preserving catalog order."""

    if len(archives) <= 1:
        return [
            _acquire_archive(client, archive, raw_dir=raw_dir, root=root, resume=resume)
            for archive in archives
        ]

    def acquire(archive: _Archive) -> tuple[Path, dict[str, Any]]:
        return _acquire_archive(client, archive, raw_dir=raw_dir, root=root, resume=resume)

    workers = min(_DOWNLOAD_WORKERS, len(archives))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="top40-snapshot") as pool:
        return list(pool.map(acquire, archives))


def _daily_mark_archive(
    *,
    base_url: str,
    symbol: str,
    day: pd.Timestamp,
) -> _Archive:
    """Construct the one official deterministic daily markPriceKlines object."""

    if base_url.rstrip("/") != _OFFICIAL_ARCHIVE_BASE_URL:
        raise ValueError("daily mark-price fallback requires official data.binance.vision")
    if re.fullmatch(r"[A-Z0-9]+", symbol) is None:
        raise ValueError("daily mark-price fallback symbol is invalid")
    timestamp = _utc(day)
    if timestamp != timestamp.floor("D"):
        raise ValueError("daily mark-price fallback date is not a UTC day boundary")
    date = timestamp.strftime("%Y-%m-%d")
    key = f"data/futures/um/daily/markPriceKlines/{symbol}/1h/{symbol}-1h-{date}.zip"
    return _Archive(
        dataset="mark_price_1h_daily",
        symbol=symbol,
        year=timestamp.year,
        month=timestamp.month,
        day=timestamp.day,
        key=key,
        url=f"{_OFFICIAL_ARCHIVE_BASE_URL}/{key}",
        checksum_url=f"{_OFFICIAL_ARCHIVE_BASE_URL}/{key}.CHECKSUM",
    )


def _acquire_daily_mark_archive(
    client: httpx.Client,
    archive: _Archive,
    *,
    raw_dir: Path,
    root: Path,
    resume: bool,
) -> tuple[Path, dict[str, Any]] | None:
    """Acquire a daily archive, treating only a missing checksum object as unavailable."""

    if archive.dataset != "mark_price_1h_daily" or archive.day is None:
        raise ValueError("daily mark-price acquisition requires an exact archive date")
    directory = raw_dir / archive.dataset / archive.symbol
    directory.mkdir(parents=True, exist_ok=True)
    zip_path = directory / archive.filename
    checksum_path = directory / f"{archive.filename}.CHECKSUM"
    checksum_bytes: bytes | None = None
    expected: str | None = None
    cached_is_valid = False
    if resume and zip_path.is_file() and checksum_path.is_file():
        try:
            checksum_bytes = checksum_path.read_bytes()
            expected = _parse_checksum(checksum_bytes.decode("utf-8"), archive.filename)
            cached_is_valid = _sha256_file(zip_path) == expected
        except (OSError, UnicodeDecodeError, ValueError):
            checksum_bytes = None
            expected = None
    if not cached_is_valid:
        checksum_bytes = _request_optional_not_found(client, archive.checksum_url)
        if checksum_bytes is None:
            return None
        try:
            expected = _parse_checksum(checksum_bytes.decode("utf-8"), archive.filename)
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"invalid Binance checksum sidecar encoding for {archive.filename}"
            ) from exc
        zip_bytes = _request(client, archive.url)
        actual = hashlib.sha256(zip_bytes).hexdigest()
        if actual != expected:
            raise ValueError(
                f"Binance SHA-256 mismatch for {archive.url}: expected {expected}, got {actual}"
            )
        _atomic_bytes(zip_path, zip_bytes)
    assert checksum_bytes is not None and expected is not None
    _atomic_bytes(checksum_path, checksum_bytes)
    if _sha256_file(zip_path) != expected:
        raise ValueError(f"cached daily archive failed Binance checksum: {zip_path}")
    date = f"{archive.year:04d}-{archive.month:02d}-{archive.day:02d}"
    source = {
        "dataset": archive.dataset,
        "symbol": archive.symbol,
        "year_month": f"{archive.year:04d}-{archive.month:02d}",
        "date": date,
        "url": archive.url,
        "checksum_url": archive.checksum_url,
        "sha256": expected,
        "size": zip_path.stat().st_size,
        "raw_path": _relative(zip_path, root),
        "checksum_sha256": hashlib.sha256(checksum_bytes).hexdigest(),
        "raw_checksum_path": _relative(checksum_path, root),
    }
    return zip_path, source


def _acquire_daily_mark_archives(
    client: httpx.Client,
    *,
    base_url: str,
    symbol: str,
    dates: tuple[pd.Timestamp, ...],
    raw_dir: Path,
    root: Path,
    resume: bool,
) -> list[tuple[Path, dict[str, Any]] | None]:
    """Probe independent exact daily objects concurrently, preserving requested date order."""

    archives = [_daily_mark_archive(base_url=base_url, symbol=symbol, day=day) for day in dates]

    def acquire(archive: _Archive) -> tuple[Path, dict[str, Any]] | None:
        return _acquire_daily_mark_archive(
            client,
            archive,
            raw_dir=raw_dir,
            root=root,
            resume=resume,
        )

    if len(archives) <= 1:
        return [acquire(archive) for archive in archives]
    workers = min(_DOWNLOAD_WORKERS, len(archives))
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="top40-daily-marks") as pool:
        return list(pool.map(acquire, archives))


def _acquire_funding_rest_month(
    client: httpx.Client,
    *,
    endpoint: str,
    symbol: str,
    year: int,
    month: int,
    raw_dir: Path,
    root: Path,
    warmup_start: pd.Timestamp,
    hard_end: pd.Timestamp,
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Refetch one archive-gap month from official REST and freeze every response page."""

    if endpoint != _OFFICIAL_FUNDING_RATE_URL:
        raise ValueError("funding REST gap endpoint is not official Binance USD-M")
    try:
        month_start = pd.Timestamp(year=year, month=month, day=1, tz="UTC")
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid funding REST gap month: {year}-{month}") from exc
    month_end = month_start + pd.offsets.MonthBegin(1)
    window_start = max(month_start, warmup_start)
    window_end = min(month_end, hard_end)
    if window_start >= window_end:
        raise ValueError(f"funding REST gap month is outside snapshot window: {year}-{month:02d}")
    start_ms = int(window_start.value // 1_000_000)
    end_ms = int(window_end.value // 1_000_000) - 1
    if start_ms > end_ms:
        raise ValueError(f"empty funding REST gap window: {year}-{month:02d}")

    directory = raw_dir / "funding_rate_rest" / symbol / f"{year:04d}-{month:02d}"
    directory.mkdir(parents=True, exist_ok=True)
    cursor = start_ms
    page = 1
    event_rows: list[dict[str, Any]] = []
    seen_times: set[int] = set()
    provenance: list[dict[str, Any]] = []
    while True:
        params = {
            "symbol": symbol,
            "startTime": str(cursor),
            "endTime": str(end_ms),
            "limit": str(_FUNDING_REST_LIMIT),
        }
        response_bytes = _request(client, endpoint, params=params)
        retrieved_at = pd.Timestamp.now(tz="UTC").isoformat()
        payload = _decode_funding_rest_response(response_bytes)
        canonical_bytes = _canonical_rest_response(payload)
        raw_path = directory / f"page-{page:04d}.json"
        # REST gap pages are deliberately never resumed: every build reaches the network first,
        # then atomically replaces any interrupted or stale response at this path.
        _atomic_bytes(raw_path, canonical_bytes)
        page_times = _validate_funding_rest_payload(
            payload,
            symbol=symbol,
            start_ms=cursor,
            end_ms=end_ms,
            limit=_FUNDING_REST_LIMIT,
        )
        provenance.append(
            {
                "dataset": "funding_rate_rest",
                "symbol": symbol,
                "year_month": f"{year:04d}-{month:02d}",
                "page": page,
                "endpoint": endpoint,
                "params": params,
                "retrieved_at": retrieved_at,
                "response_rows": len(payload),
                "sha256": hashlib.sha256(canonical_bytes).hexdigest(),
                "size": len(canonical_bytes),
                "raw_path": _relative(raw_path, root),
            }
        )
        for item, funding_time in zip(payload, page_times, strict=True):
            if funding_time in seen_times:
                raise ValueError(f"duplicate funding REST event for {symbol} at {funding_time}")
            seen_times.add(funding_time)
            event_rows.append(item)
        if len(payload) < _FUNDING_REST_LIMIT:
            break
        last_time = page_times[-1]
        if last_time >= end_ms:
            break
        next_cursor = last_time + 1
        if next_cursor <= cursor:
            raise ValueError(f"funding REST pagination made no progress for {symbol}")
        cursor = next_cursor
        page += 1

    if not event_rows:
        raise ValueError(
            f"missing funding REST event coverage for {symbol} in {year:04d}-{month:02d}"
        )
    result = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(
                [item["fundingTime"] for item in event_rows], unit="ms", utc=True
            ),
            "symbol": symbol,
            "funding_rate": pd.to_numeric(
                [item["fundingRate"] for item in event_rows], errors="raise"
            ),
            "funding_interval_hours": np.nan,
        }
    )
    actual_months = {(timestamp.year, timestamp.month) for timestamp in result["funding_time"]}
    if actual_months != {(year, month)}:
        raise ValueError(
            f"funding REST response does not exactly cover requested month for {symbol}: "
            f"{sorted(actual_months)}"
        )
    return result, provenance


def _decode_funding_rest_response(content: bytes) -> list[dict[str, Any]]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("funding REST response is not valid JSON") from exc
    if not isinstance(payload, list):
        raise ValueError("funding REST response must be a JSON array")
    if not all(isinstance(item, dict) for item in payload):
        raise ValueError("funding REST response rows must be JSON objects")
    return payload


def _canonical_rest_response(payload: Any) -> bytes:
    try:
        text = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("REST response is not canonicalisable JSON") from exc
    return (text + "\n").encode("utf-8")


def _validate_funding_rest_payload(
    payload: list[dict[str, Any]],
    *,
    symbol: str,
    start_ms: int,
    end_ms: int,
    limit: int,
) -> list[int]:
    if limit <= 0 or limit > 1000:
        raise ValueError("funding REST limit is outside Binance bounds")
    if len(payload) > limit:
        raise ValueError("funding REST response exceeds requested limit")
    times: list[int] = []
    for item in payload:
        if item.get("symbol") != symbol:
            raise ValueError(f"funding REST response contains foreign symbol for {symbol}")
        funding_time = item.get("fundingTime")
        if isinstance(funding_time, bool) or not isinstance(funding_time, int):
            raise ValueError("funding REST response has invalid fundingTime")
        if funding_time < start_ms or funding_time > end_ms:
            raise ValueError(
                f"funding REST response event is outside requested window for {symbol}"
            )
        funding_rate = item.get("fundingRate")
        if isinstance(funding_rate, bool):
            raise ValueError("funding REST response has invalid fundingRate")
        try:
            numeric_rate = float(funding_rate)
        except (TypeError, ValueError) as exc:
            raise ValueError("funding REST response has invalid fundingRate") from exc
        if not np.isfinite(numeric_rate):
            raise ValueError("funding REST response has non-finite fundingRate")
        times.append(funding_time)
    if any(current <= previous for previous, current in zip(times, times[1:])):
        raise ValueError("funding REST response times must be strictly increasing")
    return times


def _required_mark_reasons(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    symbol: str,
) -> dict[pd.Timestamp, tuple[str, ...]]:
    """Return exact hourly marks required for funding cashflows and evaluator risk."""

    required_bar_columns = {"open_time", "symbol"}
    required_funding_columns = {"funding_time", "symbol"}
    required_membership_columns = {"reconstitution_time", "symbol"}
    if required_bar_columns - set(bars):
        raise ValueError("bars are missing columns needed for required mark times")
    if required_funding_columns - set(funding):
        raise ValueError("funding is missing columns needed for required mark times")
    if required_membership_columns - set(membership):
        raise ValueError("membership is missing columns needed for required mark times")
    first_member_time = _first_admission(membership, symbol=symbol)
    reasons: dict[pd.Timestamp, set[str]] = {}
    risk_times = pd.to_datetime(
        bars.loc[bars["symbol"].astype(str).eq(symbol), "open_time"],
        utc=True,
        errors="raise",
    )
    # A symbol cannot be held before its first admission. Preserve earlier transaction bars as
    # feature warm-up, but do not invent mark prices merely to make those bars executable. Once
    # admitted, require every later transaction boundary so a participation-limited universe exit
    # can continue to liquidate safely after the symbol drops from a subsequent weekly cohort.
    risk_times = risk_times[risk_times >= first_member_time]
    funding_times = pd.to_datetime(
        funding.loc[funding["symbol"].astype(str).eq(symbol), "funding_time"],
        utc=True,
        errors="raise",
    ).dt.floor("h")
    funding_times = funding_times[funding_times >= first_member_time]
    for timestamp in risk_times:
        reasons.setdefault(pd.Timestamp(timestamp), set()).add("risk_boundary")
    for timestamp in funding_times:
        reasons.setdefault(pd.Timestamp(timestamp), set()).add("funding_floor")
    result: dict[pd.Timestamp, tuple[str, ...]] = {}
    for timestamp in sorted(reasons):
        if (
            timestamp.minute != 0
            or timestamp.second != 0
            or timestamp.microsecond != 0
            or timestamp.nanosecond != 0
        ):
            raise ValueError(f"required mark time is not an exact hour: {timestamp}")
        result[timestamp] = tuple(sorted(reasons[timestamp]))
    return result


def _acquire_mark_rest_time(
    client: httpx.Client,
    *,
    endpoint: str,
    symbol: str,
    mark_time: pd.Timestamp,
    required_for: tuple[str, ...],
    archive_source: dict[str, Any],
    raw_dir: Path,
    root: Path,
    warmup_start: pd.Timestamp,
    hard_end: pd.Timestamp,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Always refetch one exact required mark absent from a checksummed archive."""

    if endpoint != _OFFICIAL_MARK_PRICE_KLINES_URL:
        raise ValueError("mark-price REST gap endpoint is not official Binance USD-M")
    timestamp = _utc(mark_time)
    if timestamp < warmup_start or timestamp >= hard_end:
        raise ValueError(f"mark-price REST request is outside the snapshot window: {timestamp}")
    if timestamp != timestamp.floor("h"):
        raise ValueError(f"mark-price REST request must be an exact hour: {timestamp}")
    allowed_reasons = {"funding_floor", "risk_boundary"}
    if (
        not required_for
        or tuple(sorted(set(required_for))) != required_for
        or not set(required_for).issubset(allowed_reasons)
    ):
        raise ValueError("mark-price REST fallback reasons are invalid")
    year_month = timestamp.strftime("%Y-%m")
    if (
        archive_source.get("dataset") != "mark_price_1h"
        or archive_source.get("symbol") != symbol
        or archive_source.get("year_month") != year_month
        or re.fullmatch(r"[0-9a-f]{64}", str(archive_source.get("sha256", ""))) is None
        or not isinstance(archive_source.get("raw_path"), str)
    ):
        raise ValueError("mark-price REST fallback lacks its checksummed archive binding")
    timestamp_ms = int(timestamp.value // 1_000_000)
    params = {
        "symbol": symbol,
        "interval": "1h",
        "startTime": str(timestamp_ms),
        "endTime": str(timestamp_ms),
        "limit": "1",
    }
    response_bytes = _request(client, endpoint, params=params)
    retrieved_at = pd.Timestamp.now(tz="UTC").isoformat()
    payload = _decode_mark_rest_response(response_bytes)
    canonical_bytes = _canonical_rest_response(payload)
    try:
        mark_price = _validate_mark_rest_payload(
            payload,
            requested_time_ms=timestamp_ms,
            limit=1,
        )[0][1]
    except ValueError as exc:
        raise ValueError(
            f"invalid mark-price REST fallback for {symbol} at {timestamp.isoformat()}: {exc}"
        ) from exc
    directory = raw_dir / "mark_price_rest" / symbol / year_month
    directory.mkdir(parents=True, exist_ok=True)
    raw_path = directory / f"{timestamp.strftime('%Y%m%dT%H%M%SZ')}.json"
    # Deliberately ignore any cached response: REST history has no upstream checksum and may change.
    _atomic_bytes(raw_path, canonical_bytes)
    provenance = {
        "dataset": "mark_price_rest",
        "symbol": symbol,
        "year_month": year_month,
        "mark_time": timestamp.isoformat(),
        "page": 1,
        "endpoint": endpoint,
        "params": params,
        "required_for": list(required_for),
        "archive_raw_path": archive_source["raw_path"],
        "archive_sha256": archive_source["sha256"],
        "retrieved_at": retrieved_at,
        "response_rows": len(payload),
        "sha256": hashlib.sha256(canonical_bytes).hexdigest(),
        "size": len(canonical_bytes),
        "raw_path": _relative(raw_path, root),
    }
    frame = pd.DataFrame(
        {
            "mark_time": pd.DatetimeIndex([timestamp]),
            "symbol": [symbol],
            "mark_price": [mark_price],
        }
    )
    return frame, provenance


def _decode_mark_rest_response(content: bytes) -> list[list[Any]]:
    try:
        payload = json.loads(content)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("mark-price REST response is not valid JSON") from exc
    if not isinstance(payload, list):
        raise ValueError("mark-price REST response must be a JSON array")
    if not all(isinstance(item, list) for item in payload):
        raise ValueError("mark-price REST response rows must be arrays")
    return payload


def _validate_mark_rest_payload(
    payload: list[list[Any]],
    *,
    requested_time_ms: int,
    limit: int,
) -> list[tuple[int, float]]:
    """Validate the exact Binance markPriceKlines array response for one request."""

    if limit != 1:
        raise ValueError("mark-price REST fallback limit must be exactly one")
    if len(payload) != 1:
        raise ValueError("mark-price REST fallback requires exactly one response row")
    observations: list[tuple[int, float]] = []
    for row in payload:
        if len(row) != len(_KLINE_COLUMNS):
            raise ValueError("mark-price REST response row must contain exactly 12 fields")
        open_time = row[0]
        close_time = row[6]
        if isinstance(open_time, bool) or not isinstance(open_time, int):
            raise ValueError("mark-price REST response has invalid open time")
        if isinstance(close_time, bool) or not isinstance(close_time, int):
            raise ValueError("mark-price REST response has invalid close time")
        if open_time != requested_time_ms:
            raise ValueError("mark-price REST response contains a foreign requested time")
        if close_time != open_time + 3_600_000 - 1:
            raise ValueError("mark-price REST response is not an exact one-hour kline")
        timestamp = pd.Timestamp(open_time, unit="ms", tz="UTC")
        if timestamp != timestamp.floor("h"):
            raise ValueError("mark-price REST response time is not hour-aligned")
        prices: list[float] = []
        for value in row[1:5]:
            if isinstance(value, bool):
                raise ValueError("mark-price REST response has an invalid price")
            try:
                price = float(value)
            except (TypeError, ValueError) as exc:
                raise ValueError("mark-price REST response has an invalid price") from exc
            if not np.isfinite(price) or price <= 0.0:
                raise ValueError("mark-price REST response has a non-positive/non-finite price")
            prices.append(price)
        observations.append((open_time, prices[0]))
    times = [item[0] for item in observations]
    if len(times) != len(set(times)):
        raise ValueError("mark-price REST response contains duplicate times")
    if any(current - previous != 3_600_000 for previous, current in zip(times, times[1:])):
        raise ValueError("mark-price REST response times are not a strict hourly sequence")
    return observations


def _derive_missing_funding_intervals(funding: pd.DataFrame, *, symbol: str) -> pd.DataFrame:
    """Derive absent REST intervals from adjacent actual events without a schedule assumption."""

    required = {
        "funding_time",
        "symbol",
        "funding_rate",
        "funding_interval_hours",
    }
    missing = required - set(funding.columns)
    if missing:
        raise ValueError(f"funding history missing columns for {symbol}: {sorted(missing)}")
    result = funding.loc[:, sorted(required)].copy()
    result["funding_time"] = pd.to_datetime(result["funding_time"], utc=True, errors="coerce")
    if result["funding_time"].isna().any():
        raise ValueError(f"funding history has invalid timestamps for {symbol}")
    if not result["symbol"].eq(symbol).all():
        raise ValueError(f"funding history contains foreign symbol for {symbol}")
    result = result.sort_values("funding_time").reset_index(drop=True)
    if result.duplicated(["funding_time", "symbol"]).any():
        raise ValueError(f"duplicate funding event across archive/REST inputs for {symbol}")
    result["funding_rate"] = pd.to_numeric(result["funding_rate"], errors="raise")
    if not np.isfinite(result["funding_rate"].to_numpy(dtype=float)).all():
        raise ValueError(f"non-finite funding rate for {symbol}")

    original_intervals = result["funding_interval_hours"]
    intervals = pd.to_numeric(original_intervals, errors="coerce")
    if ((original_intervals.notna()) & intervals.isna()).any():
        raise ValueError(f"invalid funding interval for {symbol}")
    present = intervals.notna()
    if present.any() and (
        not np.isfinite(intervals.loc[present].to_numpy(dtype=float)).all()
        or (intervals.loc[present] <= 0).any()
    ):
        raise ValueError(f"non-positive/non-finite funding interval for {symbol}")
    for index in intervals.index[~present]:
        if index > 0:
            delta = result.loc[index, "funding_time"] - result.loc[index - 1, "funding_time"]
        elif len(result) > 1:
            delta = result.loc[1, "funding_time"] - result.loc[0, "funding_time"]
        else:
            raise ValueError(f"cannot derive isolated funding interval for {symbol}")
        hours = float(delta / pd.Timedelta(hours=1))
        if not np.isfinite(hours) or hours <= 0:
            raise ValueError(f"invalid adjacent funding interval for {symbol}")
        intervals.loc[index] = hours
    result["funding_interval_hours"] = intervals.astype(float)
    return result.loc[:, ["funding_time", "symbol", "funding_rate", "funding_interval_hours"]]


def _parse_checksum(text: str, filename: str) -> str:
    matches: list[str] = []
    for line in text.splitlines():
        match = re.fullmatch(r"\s*([0-9a-fA-F]{64})\s+\*?(.+?)\s*", line)
        if match and PurePosixPath(match.group(2)).name == filename:
            matches.append(match.group(1).lower())
    if len(set(matches)) != 1:
        raise ValueError(f"invalid Binance checksum sidecar for {filename}")
    return matches[0]


def _zip_csv(path: Path) -> pd.DataFrame:
    try:
        with zipfile.ZipFile(path) as archive:
            names = sorted(name for name in archive.namelist() if name.lower().endswith(".csv"))
            if not names:
                raise ValueError(f"archive contains no CSV: {path}")
            frames = []
            for name in names:
                raw = archive.read(name)
                first = next(csv.reader(io.StringIO(raw.decode("utf-8-sig"))), [])
                header = bool(first) and not _looks_numeric(first[0])
                frames.append(
                    pd.read_csv(
                        io.BytesIO(raw),
                        header=0 if header else None,
                        dtype=str,
                        keep_default_na=False,
                    )
                )
    except (zipfile.BadZipFile, UnicodeDecodeError, csv.Error) as exc:
        raise ValueError(f"malformed Binance archive {path}: {exc}") from exc
    return pd.concat(frames, ignore_index=True)


def _parse_kline_archive(
    path: Path,
    *,
    symbol: str,
    warmup_start: pd.Timestamp,
    hard_end: pd.Timestamp,
    expected_hours: int,
) -> pd.DataFrame:
    frame = _zip_csv(path)
    if all(isinstance(column, int) for column in frame.columns):
        if len(frame.columns) < 11:
            raise ValueError(f"kline archive has too few columns: {path}")
        frame.columns = list(_KLINE_COLUMNS[: len(frame.columns)])
    else:
        frame.columns = [_canonical_column(column) for column in frame.columns]
        frame = frame.rename(columns={"count": "trade_count", "trades": "trade_count"})
    required = set(_KLINE_COLUMNS[:11])
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"kline archive missing columns {sorted(missing)}: {path}")
    result = frame.loc[:, list(_KLINE_COLUMNS[:11])].copy()
    result["open_time"] = _epoch_to_utc(result["open_time"], "open_time")
    result["close_time"] = _epoch_to_utc(result["close_time"], "close_time")
    numeric = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "trade_count",
        "taker_buy_volume",
        "taker_buy_quote_volume",
    ]
    for column in numeric:
        result[column] = pd.to_numeric(result[column], errors="raise")
        if not np.isfinite(result[column].to_numpy(dtype=float)).all():
            raise ValueError(f"non-finite {column} in {path}")
    if (result[["open", "high", "low", "close"]] <= 0).any().any():
        raise ValueError(f"non-positive kline price in {path}")
    if (result[["volume", "quote_volume", "trade_count"]] < 0).any().any():
        raise ValueError(f"negative kline volume/count in {path}")
    result = result[(result["open_time"] >= warmup_start) & (result["open_time"] < hard_end)]
    if not result.empty:
        aligned = (
            (result["open_time"].dt.minute == 0)
            & (result["open_time"].dt.second == 0)
            & (result["open_time"].dt.microsecond == 0)
            & (result["open_time"].dt.hour % expected_hours == 0)
        )
        if not aligned.all():
            raise ValueError(f"misaligned {expected_hours}h kline timestamp in {path}")
    result.insert(1, "symbol", symbol)
    return result.sort_values("open_time").reset_index(drop=True)


def _parse_funding_archive(
    path: Path,
    *,
    symbol: str,
    warmup_start: pd.Timestamp,
    hard_end: pd.Timestamp,
) -> pd.DataFrame:
    frame = _zip_csv(path)
    if all(isinstance(column, int) for column in frame.columns):
        if len(frame.columns) < 3:
            raise ValueError(f"funding archive has too few columns: {path}")
        extras = [f"extra_{i}" for i in range(len(frame.columns) - 3)]
        frame.columns = list(_FUNDING_COLUMNS) + extras
    else:
        frame.columns = [_canonical_column(column) for column in frame.columns]
    aliases = {
        "funding_time": "calc_time",
        "funding_rate": "last_funding_rate",
        "funding_interval": "funding_interval_hours",
    }
    frame = frame.rename(columns=aliases)
    missing = set(_FUNDING_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"funding archive missing columns {sorted(missing)}: {path}")
    result = pd.DataFrame(
        {
            "funding_time": _epoch_to_utc(frame["calc_time"], "calc_time"),
            "symbol": symbol,
            "funding_rate": pd.to_numeric(frame["last_funding_rate"], errors="raise"),
            "funding_interval_hours": pd.to_numeric(
                frame["funding_interval_hours"], errors="raise"
            ),
        }
    )
    if not np.isfinite(
        result[["funding_rate", "funding_interval_hours"]].to_numpy(dtype=float)
    ).all():
        raise ValueError(f"non-finite funding value in {path}")
    if (result["funding_interval_hours"] <= 0).any():
        raise ValueError(f"non-positive funding interval in {path}")
    result = result[(result["funding_time"] >= warmup_start) & (result["funding_time"] < hard_end)]
    return result.sort_values("funding_time").reset_index(drop=True)


def _canonical_bars(
    frames: list[pd.DataFrame], warmup_start: pd.Timestamp, hard_end: pd.Timestamp
) -> pd.DataFrame:
    if not frames:
        raise ValueError("no transaction rows were parsed")
    bars = pd.concat(frames, ignore_index=True)
    bars = bars[(bars["open_time"] >= warmup_start) & (bars["open_time"] < hard_end)]
    if bars.duplicated(["open_time", "symbol"]).any():
        raise ValueError("duplicate canonical transaction (open_time, symbol) rows")
    return bars.sort_values(["open_time", "symbol"]).reset_index(drop=True)


def _contract_metadata(
    bars: pd.DataFrame, current: dict[str, dict[str, Any]], hard_end: pd.Timestamp
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for symbol, symbol_bars in bars.groupby("symbol", observed=True, sort=True):
        first_bar = symbol_bars["open_time"].min()
        last_bar = symbol_bars["open_time"].max()
        info = current.get(symbol)
        if info is None:
            rows.append(
                {
                    "symbol": symbol,
                    "contract_type": "PERPETUAL",
                    "quote_asset": "USDT",
                    "margin_asset": "USDT",
                    "is_crypto": symbol not in _KNOWN_ARCHIVE_ONLY_INDEXES,
                    "onboard_date": first_bar,
                    "delivery_date": min(last_bar + pd.Timedelta(hours=8), hard_end),
                    "underlying_type": "ARCHIVE_INFERRED_COIN",
                    "metadata_source": "archive_inference",
                }
            )
            continue
        onboard = _timestamp_from_scalar(info.get("onboardDate"))
        delivery = _timestamp_from_scalar(info.get("deliveryDate"))
        rows.append(
            {
                "symbol": symbol,
                "contract_type": str(info.get("contractType", "")),
                "quote_asset": str(info.get("quoteAsset", "")),
                "margin_asset": str(info.get("marginAsset", "")),
                "is_crypto": info.get("underlyingType") == "COIN",
                "onboard_date": first_bar if pd.isna(onboard) else onboard,
                "delivery_date": pd.NaT if pd.isna(delivery) else delivery,
                "underlying_type": str(info.get("underlyingType", "")),
                "metadata_source": "current_exchangeInfo",
            }
        )
    metadata = pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)
    if metadata["symbol"].duplicated().any() or not metadata["is_crypto"].all():
        raise ValueError("canonical contract metadata contains duplicate/non-crypto symbols")
    return metadata


def _build_membership(
    bars: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    evaluation_start: pd.Timestamp,
    hard_end: pd.Timestamp,
    universe_config: dict[str, Any],
) -> pd.DataFrame:
    first = evaluation_start.floor("D") - pd.Timedelta(days=evaluation_start.weekday())
    last_day = (hard_end - pd.Timedelta(nanoseconds=1)).floor("D")
    last = last_day - pd.Timedelta(days=last_day.weekday())
    reconstitutions = pd.date_range(first, last, freq="7D", tz="UTC")
    membership = point_in_time_top40(
        bars,
        metadata,
        reconstitutions,
        top_n=int(universe_config["size"]),
        trailing_days=int(universe_config["trailing_days"]),
        min_history_days=int(universe_config["minimum_history_days"]),
        bars_per_day=3,
    )
    present = set(pd.to_datetime(membership["reconstitution_time"], utc=True))
    missing = [timestamp for timestamp in reconstitutions if timestamp not in present]
    if missing:
        raise ValueError(f"empty point-in-time universe at reconstitutions: {missing[:3]}")
    return membership.sort_values(["reconstitution_time", "liquidity_rank"]).reset_index(drop=True)


def _attach_mark_prices(funding: pd.DataFrame, marks: pd.DataFrame) -> pd.DataFrame:
    if funding.duplicated(["funding_time", "symbol"]).any():
        raise ValueError("duplicate canonical funding (funding_time, symbol) rows")
    if marks.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("duplicate canonical mark (mark_time, symbol) rows")
    joined: list[pd.DataFrame] = []
    for symbol, events in funding.groupby("symbol", observed=True, sort=True):
        symbol_marks = marks[marks["symbol"] == symbol]
        if symbol_marks.empty:
            raise ValueError(f"no mark prices for funding symbol {symbol}")
        events = events.sort_values("funding_time").copy()
        events["settlement_time"] = events["funding_time"].dt.floor("h")
        jitter = events["funding_time"] - events["settlement_time"]
        if (jitter < pd.Timedelta(0)).any() or (jitter >= pd.Timedelta(seconds=1)).any():
            bad = events.loc[jitter >= pd.Timedelta(seconds=1), "funding_time"].tolist()
            raise ValueError(f"funding timestamps are not sub-second hour boundaries: {bad[:3]}")
        merged = events.merge(
            symbol_marks.loc[:, ["mark_time", "mark_price"]].sort_values("mark_time"),
            left_on="settlement_time",
            right_on="mark_time",
            how="left",
            validate="many_to_one",
        )
        if merged[["mark_time", "mark_price"]].isna().any().any():
            missing = merged.loc[merged["mark_price"].isna(), "funding_time"].tolist()
            raise ValueError(f"no exact floor-hour mark for {symbol} funding events: {missing[:3]}")
        if (merged["mark_time"] > merged["funding_time"]).any():
            raise ValueError("future mark price joined to funding event")
        joined.append(merged)
    result = pd.concat(joined, ignore_index=True)
    columns = [
        "funding_time",
        "symbol",
        "funding_rate",
        "mark_price",
        "mark_time",
        "settlement_time",
        "funding_interval_hours",
    ]
    return result.loc[:, columns].sort_values(["funding_time", "symbol"]).reset_index(drop=True)


def _boundary_mark_prices(
    bars: pd.DataFrame, marks: pd.DataFrame, membership: pd.DataFrame
) -> pd.DataFrame:
    """Publish exact 8h marks from each symbol's first admission onward."""

    required_marks = {"mark_time", "symbol", "mark_price"}
    missing = required_marks - set(marks.columns)
    if missing:
        raise ValueError(f"mark-price panel missing columns: {sorted(missing)}")
    if marks.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("duplicate canonical mark (mark_time, symbol) rows")
    required_membership = {"reconstitution_time", "symbol"}
    if required_membership - set(membership):
        raise ValueError("membership is missing columns needed for boundary marks")
    first_admission = (
        membership.loc[:, ["reconstitution_time", "symbol"]]
        .assign(
            reconstitution_time=lambda frame: pd.to_datetime(
                frame["reconstitution_time"], utc=True, errors="raise"
            ),
            symbol=lambda frame: frame["symbol"].astype(str),
        )
        .groupby("symbol", as_index=False, observed=True)["reconstitution_time"]
        .min()
        .rename(columns={"reconstitution_time": "first_admission"})
    )
    executable = bars.loc[:, ["open_time", "symbol"]].copy()
    executable["open_time"] = pd.to_datetime(executable["open_time"], utc=True, errors="raise")
    executable["symbol"] = executable["symbol"].astype(str)
    executable = executable.merge(
        first_admission,
        on="symbol",
        how="inner",
        validate="many_to_one",
    )
    executable = (
        executable.loc[
            executable["open_time"] >= executable["first_admission"],
            ["open_time", "symbol"],
        ]
        .rename(columns={"open_time": "mark_time"})
        .sort_values(["mark_time", "symbol"])
        .reset_index(drop=True)
    )
    if executable.empty:
        raise ValueError("no executable transaction boundaries for membership symbols")
    if executable.duplicated(["mark_time", "symbol"]).any():
        raise ValueError("duplicate executable member transaction boundaries")
    boundary = marks.loc[
        (marks["mark_time"].dt.minute == 0)
        & (marks["mark_time"].dt.second == 0)
        & (marks["mark_time"].dt.microsecond == 0)
        & (marks["mark_time"].dt.hour % 8 == 0),
        ["mark_time", "symbol", "mark_price"],
    ]
    merged = executable.merge(
        boundary,
        on=["mark_time", "symbol"],
        how="left",
        validate="one_to_one",
    )
    if merged["mark_price"].isna().any():
        missing_rows = merged.loc[merged["mark_price"].isna(), ["mark_time", "symbol"]].head(3)
        raise ValueError(
            "missing exact 8h boundary mark for executable member bars: "
            f"{missing_rows.to_dict(orient='records')}"
        )
    if (
        not np.isfinite(merged["mark_price"].to_numpy(dtype=float)).all()
        or (merged["mark_price"] <= 0).any()
    ):
        raise ValueError("invalid 8h boundary mark price")
    return merged.sort_values(["mark_time", "symbol"]).reset_index(drop=True)


def _coverage_report(
    bars: pd.DataFrame,
    funding: pd.DataFrame,
    marks: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    current_symbols: dict[str, dict[str, Any]],
    hard_end: pd.Timestamp,
    required_funding_by_symbol: dict[str, set[tuple[int, int]]],
) -> dict[str, Any]:
    final_timestamp = hard_end - pd.Timedelta(nanoseconds=1)
    final_month = final_timestamp.strftime("%Y-%m")
    symbols: dict[str, dict[str, Any]] = {}
    membership_ever = set(membership["symbol"])
    all_symbols = sorted(set(bars["symbol"]) | set(funding["symbol"]) | set(marks["symbol"]))
    for symbol in all_symbols:
        symbol_bars = bars[bars["symbol"] == symbol].sort_values("open_time")
        symbol_funding = funding[funding["symbol"] == symbol].sort_values("funding_time")
        symbol_marks = marks[marks["symbol"] == symbol].sort_values("mark_time")
        info = current_symbols.get(symbol)
        delivery = _timestamp_from_scalar(info.get("deliveryDate")) if info else pd.NaT
        active_through_end = bool(info is not None and (pd.isna(delivery) or delivery >= hard_end))
        funding_mark_required = symbol in membership_ever
        final_month_required = (
            final_timestamp.year,
            final_timestamp.month,
        ) in required_funding_by_symbol.get(symbol, set())
        symbols[symbol] = {
            "transaction": _series_coverage(
                symbol_bars, "open_time", expected_interval=pd.Timedelta(hours=8)
            ),
            "funding": _series_coverage(symbol_funding, "funding_time"),
            "mark_price": _series_coverage(
                symbol_marks, "mark_time", expected_interval=pd.Timedelta(hours=1)
            ),
            "funding_interval_hours": sorted(
                float(value) for value in symbol_funding["funding_interval_hours"].unique()
            ),
            "active_through_hard_end": active_through_end,
            "funding_mark_required": funding_mark_required,
            "hard_end_funding_required": final_month_required,
            "hard_end_final_month": final_month,
            "hard_end_transaction_covered": bool(
                not active_through_end
                or (
                    not symbol_bars.empty
                    and symbol_bars["open_time"].max().strftime("%Y-%m") == final_month
                )
            ),
            "hard_end_funding_covered": bool(
                not active_through_end
                or not final_month_required
                or (
                    not symbol_funding.empty
                    and symbol_funding["funding_time"].max().strftime("%Y-%m") == final_month
                )
            ),
            "hard_end_mark_covered": bool(
                not active_through_end
                or not funding_mark_required
                or (
                    not symbol_marks.empty
                    and symbol_marks["mark_time"].max().strftime("%Y-%m") == final_month
                )
            ),
        }
        required_keys = ["hard_end_transaction_covered"]
        if final_month_required:
            required_keys.extend(["hard_end_funding_covered", "hard_end_mark_covered"])
        if active_through_end and not all(symbols[symbol][key] for key in required_keys):
            raise ValueError(f"active symbol lacks hard-end row coverage: {symbol}")
    membership_sizes = [
        {
            "reconstitution_time": pd.Timestamp(timestamp).isoformat(),
            "size": int(len(group)),
        }
        for timestamp, group in membership.groupby("reconstitution_time", sort=True)
    ]
    return {
        "schema_version": 1,
        "hard_end_exclusive": hard_end.isoformat(),
        "hard_end_final_month": final_month,
        "symbols": symbols,
        "weekly_membership_sizes": membership_sizes,
        "gap_policy": (
            "BTC 8h daily grid and active-through-cutoff final-month coverage fail closed; "
            "other exchange/archive grid gaps are disclosed per symbol."
        ),
    }


def _series_coverage(
    frame: pd.DataFrame, timestamp_column: str, *, expected_interval: pd.Timedelta | None = None
) -> dict[str, Any]:
    if frame.empty:
        return {"first": None, "last": None, "rows": 0, "duplicates": 0, "grid_gaps": None}
    timestamps = pd.to_datetime(frame[timestamp_column], utc=True).sort_values()
    duplicates = int(timestamps.duplicated().sum())
    gaps: int | None = None
    if expected_interval is not None:
        ratios = timestamps.drop_duplicates().diff().dropna() / expected_interval
        gaps = int(sum(max(int(round(float(ratio))) - 1, 0) for ratio in ratios))
    return {
        "first": timestamps.iloc[0].isoformat(),
        "last": timestamps.iloc[-1].isoformat(),
        "rows": int(len(timestamps)),
        "duplicates": duplicates,
        "grid_gaps": gaps,
    }


def _btc_daily_returns(
    bars: pd.DataFrame, warmup_start: pd.Timestamp, hard_end: pd.Timestamp
) -> pd.DataFrame:
    btc = bars[bars["symbol"] == "BTCUSDT"].sort_values("open_time")
    if btc.empty:
        raise ValueError("canonical bars contain no BTCUSDT")
    dates = btc["open_time"].dt.floor("D")
    counts = btc.groupby(dates, observed=True)["open_time"].nunique()
    expected_days = pd.date_range(
        warmup_start.floor("D"), hard_end - pd.Timedelta(days=1), freq="D"
    )
    bad = counts.reindex(expected_days)
    if bad.isna().any() or (bad != 3).any():
        raise ValueError("BTCUSDT does not have exactly three canonical 8h bars per UTC day")
    daily_close = btc.groupby(dates, observed=True)["close"].last().sort_index()
    returns = daily_close.pct_change(fill_method=None).dropna()
    if not np.isfinite(returns.to_numpy(dtype=float)).all() or (returns <= -1.0).any():
        raise ValueError("invalid canonical BTC daily returns")
    return pd.DataFrame({"date": returns.index, "btc_return": returns.to_numpy(dtype=float)})


def _epoch_to_utc(values: pd.Series, field: str) -> pd.Series:
    numeric = pd.to_numeric(values, errors="raise")
    if not np.isfinite(numeric.to_numpy(dtype=float)).all():
        raise ValueError(f"non-finite epoch timestamp: {field}")
    result = pd.Series(pd.NaT, index=values.index, dtype="datetime64[ns, UTC]")
    microseconds = numeric.abs() >= 100_000_000_000_000
    if microseconds.any():
        result.loc[microseconds] = pd.to_datetime(numeric.loc[microseconds], unit="us", utc=True)
    if (~microseconds).any():
        result.loc[~microseconds] = pd.to_datetime(numeric.loc[~microseconds], unit="ms", utc=True)
    if result.isna().any():
        raise ValueError(f"invalid epoch timestamp: {field}")
    return result


def _timestamp_from_scalar(value: Any) -> pd.Timestamp | pd.NaT:
    if value in (None, "", 0, "0"):
        return pd.NaT
    try:
        numeric = int(value)
        unit = "us" if abs(numeric) >= 100_000_000_000_000 else "ms"
        return pd.Timestamp(numeric, unit=unit, tz="UTC")
    except (TypeError, ValueError, OverflowError):
        return pd.NaT


def _canonical_column(value: Any) -> str:
    text = str(value).strip().lower().replace(" ", "_")
    return re.sub(r"[^a-z0-9_]+", "", text)


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
        return True
    except ValueError:
        return False


def _utc(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


def _project_root(config_path: Path) -> Path:
    for parent in (config_path.parent, *config_path.parents):
        if (parent / "pyproject.toml").is_file():
            return parent.resolve()
    if config_path.parent.name == "top40" and config_path.parent.parent.name == "tournament":
        return config_path.parent.parent.parent.resolve()
    raise ValueError("cannot determine project root from config_path")


def _manifest_root(manifest_path: Path) -> Path:
    if manifest_path.parent.name == "top40" and manifest_path.parent.parent.name == "tournament":
        return manifest_path.parent.parent.parent.resolve()
    for parent in (manifest_path.parent, *manifest_path.parents):
        if (parent / "pyproject.toml").is_file():
            return parent.resolve()
    raise ValueError("cannot determine project root from manifest_path")


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f"snapshot file escapes project root: {path}") from exc


def _resolve_manifest_path(root: Path, value: str) -> Path:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts or "." in path.parts:
        raise ValueError(f"unsafe snapshot manifest path: {value}")
    resolved = (root / Path(*path.parts)).resolve()
    if not resolved.is_relative_to(root):
        raise ValueError(f"snapshot manifest path escapes project root: {value}")
    return resolved


def _actual_manifest_rows(path: Path, logical_name: str) -> int:
    if logical_name in {
        "bars",
        "funding",
        "mark_prices",
        "contract_metadata",
        "membership",
    }:
        return len(pd.read_parquet(path))
    if logical_name in {"btc_daily_returns", "btc_regimes"}:
        return len(pd.read_csv(path))
    if logical_name in {
        "archive_provenance",
        "rest_provenance",
        "mark_rest_provenance",
    }:
        return len(path.read_text(encoding="utf-8").splitlines())
    payload = json.loads(path.read_text(encoding="utf-8"))
    if logical_name == "exchange_info":
        return len(payload.get("symbols", []))
    if logical_name == "coverage":
        return len(payload.get("symbols", {}))
    raise ValueError(f"unsupported snapshot logical name: {logical_name}")


def _atomic_bytes(path: Path, content: bytes) -> None:
    temp = path.with_name(f".{path.name}.download-tmp")
    try:
        temp.write_bytes(content)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_line(value: dict[str, Any]) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"


def _progress(message: str) -> None:
    print(f"[top40-snapshot] {message}", flush=True)
