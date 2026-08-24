"""Append-invariant live-data extension for the frozen Team 09 snapshot."""

from __future__ import annotations

import csv
import dataclasses
import hashlib
import io
import json
import os
import time
import zipfile
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit
from xml.etree import ElementTree

import httpx
import numpy as np
import pandas as pd

from crypto_trade.team09.backtest import (
    HISTORICAL_END_EXCLUSIVE,
    INTERVAL_HOURS,
    Team09MarketData,
    historical_terminal_held_symbols,
)
from crypto_trade.tournament.data import point_in_time_top40
from crypto_trade.tournament.pure_crypto_universe_v6 import (
    POLICY_ID,
    REVIEWED_ARCHIVE_ONLY_CRYPTO,
    current_contract_violations,
    symbol_policy_violations,
)

FAPI_BASE_URL = "https://fapi.binance.com"
ARCHIVE_BASE_URL = "https://data.binance.vision"
ARCHIVE_S3_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
ARCHIVE_DAILY_KLINE_PREFIX = "data/futures/um/daily/klines/"
BRIDGE_START = HISTORICAL_END_EXCLUSIVE
INTERVAL = pd.Timedelta(hours=INTERVAL_HOURS)
CACHE_SCHEMA_VERSION = "team09-live-cache-v2"
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
)
_BAR_VALUE_COLUMNS = _KLINE_COLUMNS[1:]
_MARK_VALUE_COLUMNS = ("mark_price",)
_FUNDING_VALUE_COLUMNS = ("funding_rate", "mark_price")


def _validated_klines_proxy_base_url(value: str) -> str:
    """Return a canonical loopback-only HTTP origin for the klines proxy."""

    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Team 09 klines proxy URL has an invalid port") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "::1"}
        or port is None
        or port < 1
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError(
            "Team 09 klines proxy URL must be a credential-free loopback "
            "HTTP origin with an explicit port"
        )
    host = f"[{parsed.hostname}]" if parsed.hostname == "::1" else parsed.hostname
    return f"http://{host}:{port}"


@dataclasses.dataclass(frozen=True)
class LiveDataDiagnostics:
    boundary: pd.Timestamp
    fetched_at: pd.Timestamp
    pure_crypto_policy_id: str
    current_pure_crypto_symbols: tuple[str, ...]
    known_pure_crypto_symbols: tuple[str, ...]
    archive_catalog_symbol_count: int
    candidate_symbol_count: int
    reviewed_archive_only_symbols: tuple[str, ...]
    unclassified_bridge_symbols: tuple[str, ...]
    excluded_current_contracts: Mapping[str, tuple[str, ...]]
    bridge_membership_symbols: tuple[str, ...]
    accounting_symbols: tuple[str, ...]
    accounting_admission_boundaries: Mapping[str, str]
    current_membership_symbols: tuple[str, ...]
    completed_bridge_bar_rows: int
    bridge_funding_rows: int
    bridge_mark_rows: int
    archive_fallback_file_count: int

    def to_dict(self) -> dict[str, object]:
        result = dataclasses.asdict(self)
        result["boundary"] = self.boundary.isoformat()
        result["fetched_at"] = self.fetched_at.isoformat()
        return result


@dataclasses.dataclass(frozen=True)
class LiveMarketData:
    market_data: Team09MarketData
    diagnostics: LiveDataDiagnostics
    cache_dir: Path


class BinancePublicDataError(RuntimeError):
    """A non-retryable structured error returned by a Binance public endpoint."""

    def __init__(
        self,
        *,
        endpoint: str,
        status_code: int,
        error_code: int | None,
        message: str,
    ) -> None:
        super().__init__(
            f"Binance public-data error {status_code}/{error_code}: "
            f"{endpoint}: {message}"
        )
        self.endpoint = endpoint
        self.status_code = status_code
        self.error_code = error_code


class Team09PublicDataClient:
    """Small serial client for exact public Binance USD-M inputs."""

    def __init__(
        self,
        *,
        base_url: str = FAPI_BASE_URL,
        klines_base_url: str | None = None,
        timeout_seconds: float = 45.0,
        pause_seconds: float = 0.03,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        validated_klines_base_url = (
            _validated_klines_proxy_base_url(klines_base_url)
            if klines_base_url is not None
            else None
        )
        kwargs: dict[str, object] = {
            "base_url": base_url,
            "timeout": timeout_seconds,
            "trust_env": False,
        }
        if transport is not None:
            kwargs["transport"] = transport
        self._http = httpx.Client(**kwargs)
        self._klines_base_url = validated_klines_base_url
        self.pause_seconds = pause_seconds
        self._archive_provenance: dict[str, dict[str, object]] = {}

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Team09PublicDataClient:
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()

    def exchange_info(self) -> Mapping[str, Any]:
        payload = self._get_json("/fapi/v1/exchangeInfo")
        if not isinstance(payload, Mapping) or not isinstance(payload.get("symbols"), list):
            raise ValueError("Binance exchangeInfo payload has an invalid schema")
        return payload

    def archive_symbols(self) -> tuple[str, ...]:
        """Discover every symbol directory in Binance's official daily USD-M catalog."""

        _keys, prefixes = self._list_s3(
            ARCHIVE_S3_URL,
            prefix=ARCHIVE_DAILY_KLINE_PREFIX,
            delimiter="/",
        )
        symbols = {
            value[len(ARCHIVE_DAILY_KLINE_PREFIX) :].split("/", 1)[0]
            for value in prefixes
            if value.startswith(ARCHIVE_DAILY_KLINE_PREFIX)
            and value[len(ARCHIVE_DAILY_KLINE_PREFIX) :]
        }
        if not symbols:
            raise RuntimeError("Binance archive symbol discovery returned no symbols")
        return tuple(sorted(symbols))

    def transaction_bars(
        self,
        symbol: str,
        *,
        start: pd.Timestamp,
        end_inclusive: pd.Timestamp,
    ) -> pd.DataFrame:
        try:
            rows = self._paged_klines(
                "/fapi/v1/klines",
                symbol,
                start=start,
                end_inclusive=end_inclusive,
                limit=99,
            )
        except BinancePublicDataError as exc:
            if exc.error_code not in {-1121, -1122}:
                raise
            rows = self._archived_transaction_rows(
                symbol,
                start=start,
                end_inclusive=end_inclusive,
            )
        return _transaction_bar_frame(symbol, rows)

    def archive_provenance(self) -> tuple[Mapping[str, object], ...]:
        return tuple(
            dict(self._archive_provenance[path])
            for path in sorted(self._archive_provenance)
        )

    def _archived_transaction_rows(
        self,
        symbol: str,
        *,
        start: pd.Timestamp,
        end_inclusive: pd.Timestamp,
    ) -> list[list[object]]:
        """Use checksum-verified official daily archives for REST-invalid symbols."""

        prefix = (
            f"{ARCHIVE_DAILY_KLINE_PREFIX}{symbol}/"
            f"{INTERVAL_HOURS}h/"
        )
        keys, _prefixes = self._list_s3(
            ARCHIVE_S3_URL,
            prefix=prefix,
            delimiter=None,
        )
        start_day = _utc(start).normalize()
        end_day = _utc(end_inclusive).normalize()
        selected: list[str] = []
        filename_prefix = f"{symbol}-{INTERVAL_HOURS}h-"
        for key in keys:
            name = Path(key).name
            if not name.startswith(filename_prefix) or not name.endswith(".zip"):
                continue
            raw_day = name.removeprefix(filename_prefix).removesuffix(".zip")
            try:
                day = pd.Timestamp(raw_day, tz="UTC")
            except ValueError as exc:
                raise RuntimeError(
                    f"malformed Binance daily archive key: {key}"
                ) from exc
            if start_day <= day <= end_day:
                selected.append(key)

        rows: list[list[object]] = []
        for key in sorted(selected):
            archive_url = f"{ARCHIVE_BASE_URL}/{key}"
            checksum_url = f"{archive_url}.CHECKSUM"
            archive_response = self._request(archive_url)
            checksum_response = self._request(checksum_url)
            archive_bytes = archive_response.content
            checksum_bytes = checksum_response.content
            checksum_parts = checksum_bytes.decode("ascii").strip().split()
            if (
                len(checksum_parts) != 2
                or len(checksum_parts[0]) != 64
                or checksum_parts[1] != Path(key).name
            ):
                raise RuntimeError(
                    f"malformed Binance archive checksum payload: {key}"
                )
            expected_sha256 = checksum_parts[0].lower()
            actual_sha256 = hashlib.sha256(archive_bytes).hexdigest()
            if actual_sha256 != expected_sha256:
                raise RuntimeError(
                    f"Binance daily archive checksum mismatch: {key}"
                )
            archive_rows = _read_archive_kline_rows(
                archive_bytes,
                expected_csv_name=Path(key).with_suffix(".csv").name,
            )
            rows.extend(archive_rows)
            record = {
                "archive_path": key,
                "archive_sha256": actual_sha256,
                "archive_size": len(archive_bytes),
                "checksum_path": f"{key}.CHECKSUM",
                "checksum_payload_sha256": hashlib.sha256(
                    checksum_bytes
                ).hexdigest(),
            }
            previous = self._archive_provenance.get(key)
            if previous is not None and previous != record:
                raise RuntimeError(
                    f"APPEND-INVARIANCE ABORT: archive provenance changed for {key}"
                )
            self._archive_provenance[key] = record
        start_ms = _milliseconds(start)
        end_ms = _milliseconds(end_inclusive)
        return [
            row
            for row in rows
            if start_ms <= int(row[0]) <= end_ms
        ]

    def mark_prices(
        self,
        symbol: str,
        *,
        start: pd.Timestamp,
        end_inclusive: pd.Timestamp,
    ) -> pd.DataFrame:
        rows = self._paged_klines(
            "/fapi/v1/markPriceKlines",
            symbol,
            start=start,
            end_inclusive=end_inclusive,
            limit=99,
        )
        parsed: list[dict[str, object]] = []
        for row in rows:
            _validate_kline_row(row, interval_ms=3_600_000)
            parsed.append(
                {
                    "mark_time": pd.Timestamp(int(row[0]), unit="ms", tz="UTC"),
                    "symbol": symbol,
                    "mark_price": _positive_float(row[1], "mark-price open"),
                }
            )
        return pd.DataFrame(parsed, columns=["mark_time", "symbol", "mark_price"])

    def funding(
        self,
        symbol: str,
        *,
        start: pd.Timestamp,
        end_inclusive: pd.Timestamp,
    ) -> pd.DataFrame:
        start_ms = _milliseconds(start)
        end_ms = _milliseconds(end_inclusive)
        current = start_ms
        rows: list[dict[str, object]] = []
        while current <= end_ms:
            payload = self._get_json(
                "/fapi/v1/fundingRate",
                params={
                    "symbol": symbol,
                    "startTime": current,
                    "endTime": end_ms,
                    "limit": 1000,
                },
            )
            if not isinstance(payload, list):
                raise ValueError(f"funding payload for {symbol} is not an array")
            if not payload:
                break
            for item in payload:
                if not isinstance(item, Mapping):
                    raise ValueError(f"funding payload for {symbol} contains a non-object")
                funding_time = int(item["fundingTime"])
                if funding_time < start_ms or funding_time > end_ms:
                    raise ValueError(f"funding payload for {symbol} escaped its request window")
                rows.append(
                    {
                        "funding_time": pd.Timestamp(funding_time, unit="ms", tz="UTC"),
                        "symbol": symbol,
                        "funding_rate": _finite_float(
                            item["fundingRate"], "funding rate"
                        ),
                        "mark_price": _positive_float(
                            item["markPrice"], "funding mark price"
                        ),
                    }
                )
            last = int(payload[-1]["fundingTime"])
            if len(payload) < 1000:
                break
            if last < current:
                raise ValueError(f"funding pagination did not advance for {symbol}")
            current = last + 1
            time.sleep(self.pause_seconds)
        return pd.DataFrame(
            rows,
            columns=["funding_time", "symbol", "funding_rate", "mark_price"],
        )

    def _paged_klines(
        self,
        endpoint: str,
        symbol: str,
        *,
        start: pd.Timestamp,
        end_inclusive: pd.Timestamp,
        limit: int,
    ) -> list[list[object]]:
        start_ms = _milliseconds(start)
        end_ms = _milliseconds(end_inclusive)
        current = start_ms
        rows: list[list[object]] = []
        while current <= end_ms:
            payload = self._get_json(
                endpoint,
                params={
                    "symbol": symbol,
                    "interval": "8h" if endpoint.endswith("/klines") else "1h",
                    "startTime": current,
                    "endTime": end_ms,
                    "limit": limit,
                },
            )
            if not isinstance(payload, list):
                raise ValueError(f"kline payload for {symbol} is not an array")
            if not payload:
                break
            if any(not isinstance(row, list) for row in payload):
                raise ValueError(f"kline payload for {symbol} contains a non-array")
            rows.extend(payload)
            last = int(payload[-1][0])
            if len(payload) < limit:
                break
            if last < current:
                raise ValueError(f"kline pagination did not advance for {symbol}")
            current = last + 1
            time.sleep(self.pause_seconds)
        return rows

    def _get_json(
        self,
        endpoint: str,
        *,
        params: Mapping[str, object] | None = None,
    ) -> object:
        response = self._request(endpoint, params=params)
        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"Binance public-data response is not JSON: {endpoint}"
            ) from exc

    def _list_s3(
        self,
        url: str,
        *,
        prefix: str,
        delimiter: str | None,
    ) -> tuple[list[str], list[str]]:
        keys: list[str] = []
        prefixes: list[str] = []
        marker = ""
        while True:
            params: dict[str, object] = {"prefix": prefix}
            if delimiter is not None:
                params["delimiter"] = delimiter
            if marker:
                params["marker"] = marker
            response = self._request(url, params=params)
            try:
                root = ElementTree.fromstring(response.content)
            except ElementTree.ParseError as exc:
                raise RuntimeError(
                    f"invalid Binance archive listing for {prefix}"
                ) from exc
            page_keys = [
                node.findtext("{*}Key") or ""
                for node in root.findall(".//{*}Contents")
            ]
            page_prefixes = [
                node.findtext("{*}Prefix") or ""
                for node in root.findall(".//{*}CommonPrefixes")
            ]
            keys.extend(value for value in page_keys if value)
            prefixes.extend(value for value in page_prefixes if value)
            truncated = (
                root.findtext("{*}IsTruncated") or "false"
            ).lower() == "true"
            if not truncated:
                break
            next_marker = root.findtext("{*}NextMarker")
            candidates = page_keys + page_prefixes
            marker = next_marker or (candidates[-1] if candidates else "")
            if not marker:
                raise RuntimeError(
                    f"truncated Binance archive listing lacks a marker: {prefix}"
                )
        return sorted(set(keys)), sorted(set(prefixes))

    def _request(
        self,
        endpoint: str,
        *,
        params: Mapping[str, object] | None = None,
    ) -> httpx.Response:
        last_error: Exception | None = None
        target = (
            f"{self._klines_base_url}{endpoint}"
            if endpoint == "/fapi/v1/klines"
            and self._klines_base_url is not None
            else endpoint
        )
        for attempt in range(5):
            try:
                response = self._http.get(target, params=params)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                last_error = exc
                retry_after = exc.response.headers.get("Retry-After")
                if exc.response.status_code not in {418, 429}:
                    try:
                        payload = exc.response.json()
                    except ValueError:
                        payload = {}
                    error_code = (
                        int(payload["code"])
                        if isinstance(payload, Mapping)
                        and isinstance(payload.get("code"), int)
                        else None
                    )
                    message = (
                        str(payload.get("msg"))
                        if isinstance(payload, Mapping)
                        else exc.response.text[:200]
                    )
                    raise BinancePublicDataError(
                        endpoint=endpoint,
                        status_code=exc.response.status_code,
                        error_code=error_code,
                        message=message,
                    ) from exc
                if attempt == 4:
                    break
                delay = _retry_delay(retry_after, attempt)
                time.sleep(delay)
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt < 4:
                    time.sleep(min(2.0**attempt, 15.0))
        raise RuntimeError(
            f"Binance public-data request failed after retries: {endpoint}"
        ) from last_error


def exact_boundary(value: object) -> pd.Timestamp:
    timestamp = _utc(value)
    boundary = timestamp.floor(f"{INTERVAL_HOURS}h")
    if timestamp != boundary:
        raise ValueError("Team 09 live boundary must be an exact 8-hour UTC boundary")
    if boundary < BRIDGE_START:
        raise ValueError(f"Team 09 live boundary cannot precede {BRIDGE_START.isoformat()}")
    return boundary


def current_boundary(now: object | None = None) -> pd.Timestamp:
    timestamp = pd.Timestamp.now(tz="UTC") if now is None else _utc(now)
    return timestamp.floor(f"{INTERVAL_HOURS}h")


def build_live_market_data(
    frozen: Team09MarketData,
    *,
    boundary: object,
    cache_dir: str | Path,
    client: Team09PublicDataClient | None,
    prior_accounting_admissions: Mapping[str, object] | None = None,
    persist_accounting_admissions: bool = False,
) -> LiveMarketData:
    """Extend frozen data through ``boundary`` and add a forming execution row.

    When ``client`` is ``None`` no network requests occur and every cache must
    already reach the requested boundary.
    """

    live_boundary = exact_boundary(boundary)
    cache = Path(cache_dir).resolve()
    cache.mkdir(parents=True, exist_ok=True)
    cache_manifest = verify_live_cache_manifest(
        cache,
        required=client is None,
    )
    cached_diagnostics = (
        _load_json_mapping(cache / "diagnostics.json")
        if (cache / "diagnostics.json").is_file()
        else {}
    )
    if client is not None:
        info = client.exchange_info()
        if not isinstance(info.get("serverTime"), int):
            raise ValueError("Binance exchangeInfo requires an integer serverTime")
        pure_contracts, exclusions = classify_current_contracts(info)
        known_contracts, classification_exclusions = classify_known_contracts(info)
        raw_exchange_symbols = {
            str(item["symbol"])
            for item in info["symbols"]
            if isinstance(item, Mapping) and isinstance(item.get("symbol"), str)
        }
        archive_symbols = client.archive_symbols()
        existing_live_metadata = (
            pd.read_parquet(cache / "contract_metadata.parquet")
            if (cache / "contract_metadata.parquet").is_file()
            else _empty_metadata()
        )
        frozen_delivery = pd.to_datetime(
            frozen.contract_metadata["delivery_date"], utc=True
        )
        bridge_frozen_symbols = set(
            frozen.contract_metadata.loc[
                frozen_delivery > BRIDGE_START, "symbol"
            ].astype(str)
        )
        known_metadata_symbols = (
            set(frozen.contract_metadata["symbol"].astype(str))
            | set(existing_live_metadata["symbol"].astype(str))
        )
        classification_drift = {
            symbol: classification_exclusions[symbol]
            for symbol in sorted(
                known_metadata_symbols & set(classification_exclusions)
            )
        }
        if classification_drift:
            raise RuntimeError(
                "PURE-CRYPTO CLASSIFICATION DRIFT for previously admitted "
                f"contracts: {classification_drift}"
            )
        unknown_archive_symbols = tuple(
            sorted(
                symbol
                for symbol in set(archive_symbols)
                - known_metadata_symbols
                - raw_exchange_symbols
                if not symbol_policy_violations(symbol)
            )
        )
        unclassified_bridge = probe_unclassified_bridge_symbols(
            unknown_archive_symbols,
            boundary=live_boundary,
            client=client,
        )
        unreviewed = tuple(
            symbol
            for symbol in unclassified_bridge
            if symbol not in REVIEWED_ARCHIVE_ONLY_CRYPTO
        )
        if unreviewed:
            raise RuntimeError(
                "UNCLASSIFIED BRIDGE CONTRACTS: exact pure-crypto membership cannot "
                f"be proven for {list(unreviewed)}"
            )
        reviewed_archive_only = tuple(unclassified_bridge)
        candidate_symbols = tuple(
            sorted(
                bridge_frozen_symbols
                | set(existing_live_metadata["symbol"].astype(str))
                | set(known_contracts)
                | set(unclassified_bridge)
            )
        )
        bars, forming = refresh_bar_cache(
            cache / "bars.parquet",
            candidate_symbols,
            required_current_symbols=tuple(
                sorted(
                    symbol
                    for symbol, contract in pure_contracts.items()
                    if pd.Timestamp(
                        int(contract["onboardDate"]), unit="ms", tz="UTC"
                    )
                    <= live_boundary
                    < pd.Timestamp(
                        int(contract["deliveryDate"]), unit="ms", tz="UTC"
                    )
                )
            ),
            boundary=live_boundary,
            client=client,
        )
        lifecycle = resolve_contract_lifecycle(
            candidate_symbols,
            known_contracts,
            bars,
            forming,
            replay_boundary=live_boundary,
            client=client,
        )
        live_metadata = update_live_metadata_cache(
            cache / "contract_metadata.parquet",
            frozen.contract_metadata,
            known_contracts,
            archive_only_symbols=unclassified_bridge,
            bridge_bars=bars,
        )
        _write_immutable_json(
            info,
            cache
            / "exchange-info"
            / (
                f"{live_boundary.strftime('%Y%m%dT%H%M%SZ')}-"
                f"{int(info.get('serverTime', 0))}.json"
            ),
        )
        _write_json_atomic(known_contracts, cache / "classified-contracts.json")
        _write_json_atomic(list(archive_symbols), cache / "archive-symbols.json")
        _write_json_atomic(list(candidate_symbols), cache / "candidate-symbols.json")
        _write_json_atomic(lifecycle, cache / "contract-lifecycle.json")
    else:
        exclusions = _load_json_exclusions(cache / "excluded-contracts.json")
        live_metadata = _read_required_parquet(cache / "contract_metadata.parquet")
        bars = _read_required_parquet(cache / "bars.parquet")
        forming = _read_required_parquet(cache / "forming-bars.parquet")
        known_contracts = _load_contract_mapping(
            cache / "classified-contracts.json"
        )
        pure_contracts = {
            symbol: contract
            for symbol, contract in known_contracts.items()
            if contract.get("status") == "TRADING"
        }
        archive_symbols = tuple(
            str(symbol)
            for symbol in _load_json_list(cache / "archive-symbols.json")
        )
        candidate_symbols = tuple(
            str(symbol)
            for symbol in _load_json_list(cache / "candidate-symbols.json")
        )
        lifecycle = _load_json_mapping(cache / "contract-lifecycle.json")
        unclassified_bridge = ()
        reviewed_archive_only = tuple(
            str(value)
            for value in _load_json_mapping(cache / "diagnostics.json").get(
                "reviewed_archive_only_symbols", ()
            )
        )

    validate_live_cache_domains(
        bars,
        forming,
        live_metadata,
        known_contracts,
        candidate_symbols,
        lifecycle,
    )

    combined_bars = _combine_historical(
        frozen.bars,
        bars,
        time_column="open_time",
        bridge_start=BRIDGE_START,
    )
    combined_metadata = combine_contract_metadata(
        frozen.contract_metadata,
        live_metadata,
    )
    combined_metadata = apply_live_contract_lifecycle(
        combined_metadata,
        lifecycle,
    )
    membership = extend_membership(
        frozen.membership,
        combined_bars,
        combined_metadata,
        boundary=live_boundary,
    )
    membership_times = pd.to_datetime(membership["reconstitution_time"], utc=True)
    anchors = membership_times[membership_times <= BRIDGE_START]
    if anchors.empty:
        raise RuntimeError("Team 09 bridge has no anchor membership")
    bridge_anchor = anchors.max()
    bridge_members = tuple(
        sorted(
            set(
                membership.loc[
                    membership_times >= bridge_anchor,
                    "symbol",
                ].astype(str)
            )
        )
    )
    historical_carried_symbols = historical_terminal_held_symbols()
    prior_admission_symbols = _accounting_admission_symbols(
        cached_diagnostics,
        prior_accounting_admissions,
    )
    accounting_symbols = tuple(
        sorted(
            set(bridge_members)
            | set(historical_carried_symbols)
            | prior_admission_symbols
        )
    )
    accounting_admissions = _resolve_accounting_admissions(
        cached_diagnostics,
        prior=prior_accounting_admissions,
        accounting_symbols=accounting_symbols,
        boundary=live_boundary,
    )
    current_members = _membership_at(membership, live_boundary)

    if client is not None:
        marks = refresh_mark_cache(
            cache / "mark_prices.parquet",
            accounting_symbols,
            boundary=live_boundary,
            client=client,
        )
        funding = refresh_funding_cache(
            cache / "funding.parquet",
            accounting_symbols,
            boundary=live_boundary,
            client=client,
        )
        archive_provenance = _merge_archive_provenance(
            cache / "archive-kline-provenance.json",
            client.archive_provenance(),
        )
        forming = forming[forming["symbol"].isin(set(accounting_symbols))]
        _write_parquet_atomic(forming, cache / "forming-bars.parquet")
        _write_json_atomic(
            {symbol: list(reasons) for symbol, reasons in sorted(exclusions.items())},
            cache / "excluded-contracts.json",
        )
    else:
        marks = _read_required_parquet(cache / "mark_prices.parquet")
        funding = _read_required_parquet(cache / "funding.parquet")
        archive_provenance = _load_archive_provenance(
            cache / "archive-kline-provenance.json"
        )

    validate_live_cache_coverage(
        bars,
        forming,
        funding,
        marks,
        membership,
        required_accounting_symbols=historical_carried_symbols,
        boundary=live_boundary,
    )
    replay_bars = pd.concat([combined_bars, forming], ignore_index=True)
    replay_bars = (
        replay_bars.drop_duplicates(["open_time", "symbol"], keep="last")
        .sort_values(["open_time", "symbol"])
        .reset_index(drop=True)
    )
    causal_funding = _causal_accounting_rows(
        funding,
        time_column="funding_time",
        admissions=accounting_admissions,
    )
    causal_marks = _causal_accounting_rows(
        marks,
        time_column="mark_time",
        admissions=accounting_admissions,
    )
    combined_funding = _combine_historical(
        frozen.funding,
        causal_funding,
        time_column="funding_time",
        bridge_start=BRIDGE_START,
    )
    combined_marks = _combine_historical(
        frozen.mark_prices,
        causal_marks,
        time_column="mark_time",
        bridge_start=BRIDGE_START,
    )
    if client is None:
        diagnostics = _diagnostics_from_mapping(
            _load_json_mapping(cache / "diagnostics.json")
        )
        if diagnostics.boundary != live_boundary:
            raise RuntimeError(
                "cache-only replay boundary differs from the sealed cache manifest"
            )
        if (
            diagnostics.current_membership_symbols != current_members
            or diagnostics.bridge_membership_symbols != bridge_members
            or diagnostics.accounting_symbols != accounting_symbols
        ):
            raise RuntimeError("sealed cache diagnostics disagree with recomputed membership")
        cached_admissions = cached_diagnostics.get(
            "accounting_admission_boundaries"
        )
        if (
            cached_admissions is not None
            and diagnostics.accounting_admission_boundaries
            != accounting_admissions
        ):
            raise RuntimeError(
                "sealed cache diagnostics disagree with accounting admissions"
            )
        diagnostics = dataclasses.replace(
            diagnostics,
            accounting_admission_boundaries=accounting_admissions,
        )
        if persist_accounting_admissions:
            _write_json_atomic(
                diagnostics.to_dict(),
                cache / "diagnostics.json",
            )
            write_live_cache_manifest(cache, boundary=live_boundary)
            cache_manifest = verify_live_cache_manifest(cache)
        if cache_manifest is None:
            raise RuntimeError("cache-only replay has no verified cache manifest")
    else:
        diagnostics = LiveDataDiagnostics(
            boundary=live_boundary,
            fetched_at=pd.Timestamp.now(tz="UTC"),
            pure_crypto_policy_id=POLICY_ID,
            current_pure_crypto_symbols=tuple(sorted(pure_contracts)),
            known_pure_crypto_symbols=tuple(sorted(known_contracts)),
            archive_catalog_symbol_count=len(archive_symbols),
            candidate_symbol_count=len(candidate_symbols),
            reviewed_archive_only_symbols=reviewed_archive_only,
            unclassified_bridge_symbols=(),
            excluded_current_contracts=exclusions,
            bridge_membership_symbols=bridge_members,
            accounting_symbols=accounting_symbols,
            accounting_admission_boundaries=accounting_admissions,
            current_membership_symbols=current_members,
            completed_bridge_bar_rows=int(len(bars)),
            bridge_funding_rows=int(len(funding)),
            bridge_mark_rows=int(len(marks)),
            archive_fallback_file_count=len(archive_provenance),
        )
        _write_json_atomic(diagnostics.to_dict(), cache / "diagnostics.json")
        write_live_cache_manifest(cache, boundary=live_boundary)
    return LiveMarketData(
        market_data=Team09MarketData(
            bars=replay_bars,
            funding=combined_funding,
            membership=membership,
            mark_prices=combined_marks,
            contract_metadata=combined_metadata,
        ),
        diagnostics=diagnostics,
        cache_dir=cache,
    )


def classify_current_contracts(
    exchange_info: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, tuple[str, ...]]]:
    """Apply the frozen native-crypto policy to current exchange contracts."""

    raw_symbols = exchange_info.get("symbols")
    if not isinstance(raw_symbols, list):
        raise ValueError("exchangeInfo.symbols must be an array")
    accepted: dict[str, Mapping[str, Any]] = {}
    exclusions: dict[str, tuple[str, ...]] = {}
    for raw in raw_symbols:
        if not isinstance(raw, Mapping):
            raise ValueError("exchangeInfo contains a non-object contract")
        symbol = raw.get("symbol")
        if not isinstance(symbol, str):
            continue
        reasons = current_contract_violations(raw)
        if raw.get("status") != "TRADING":
            reasons = (*reasons, "status-not-trading")
        reasons = tuple(dict.fromkeys(reasons))
        if reasons:
            exclusions[symbol] = reasons
        else:
            if symbol in accepted:
                raise ValueError(f"duplicate current contract: {symbol}")
            accepted[symbol] = raw
    if not accepted:
        raise ValueError("current exchangeInfo yielded no pure-crypto contracts")
    return accepted, exclusions


def classify_known_contracts(
    exchange_info: Mapping[str, Any],
) -> tuple[dict[str, Mapping[str, Any]], dict[str, tuple[str, ...]]]:
    """Classify all current exchangeInfo rows without introducing status survivorship."""

    raw_symbols = exchange_info.get("symbols")
    if not isinstance(raw_symbols, list):
        raise ValueError("exchangeInfo.symbols must be an array")
    accepted: dict[str, Mapping[str, Any]] = {}
    exclusions: dict[str, tuple[str, ...]] = {}
    for raw in raw_symbols:
        if not isinstance(raw, Mapping):
            raise ValueError("exchangeInfo contains a non-object contract")
        symbol = raw.get("symbol")
        if not isinstance(symbol, str):
            continue
        reasons = current_contract_violations(raw)
        if reasons:
            exclusions[symbol] = reasons
        else:
            if symbol in accepted:
                raise ValueError(f"duplicate current contract: {symbol}")
            accepted[symbol] = raw
    if not accepted:
        raise ValueError("exchangeInfo yielded no classifiable pure-crypto contracts")
    return accepted, exclusions


def update_live_metadata_cache(
    path: Path,
    frozen_metadata: pd.DataFrame,
    contracts: Mapping[str, Mapping[str, Any]],
    *,
    archive_only_symbols: Iterable[str] = (),
    bridge_bars: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Freeze newly admitted pure-crypto metadata; classification is append-only."""

    frozen_symbols = set(frozen_metadata["symbol"].astype(str))
    existing = pd.read_parquet(path) if path.is_file() else _empty_metadata()
    existing_symbols = set(existing["symbol"].astype(str)) if not existing.empty else set()
    current_rows: list[dict[str, object]] = []
    for symbol in sorted(set(contracts) - frozen_symbols - existing_symbols):
        contract = contracts[symbol]
        current_rows.append(
            {
                "symbol": symbol,
                "contract_type": str(contract["contractType"]),
                "quote_asset": str(contract["quoteAsset"]),
                "margin_asset": str(contract["marginAsset"]),
                "is_crypto": True,
                "onboard_date": pd.Timestamp(int(contract["onboardDate"]), unit="ms", tz="UTC"),
                "delivery_date": pd.Timestamp(
                    int(contract["deliveryDate"]), unit="ms", tz="UTC"
                ),
                "underlying_type": str(contract["underlyingType"]),
                "metadata_source": "live_exchangeInfo_frozen_on_admission",
            }
        )
    archive_only = (
        set(str(symbol) for symbol in archive_only_symbols)
        - frozen_symbols
        - existing_symbols
        - set(contracts)
    )
    if archive_only:
        if bridge_bars is None:
            raise ValueError("archive-only metadata requires bridge bars")
        bar_times = pd.to_datetime(bridge_bars["open_time"], utc=True)
        for symbol in sorted(archive_only):
            symbol_times = bar_times.loc[
                bridge_bars["symbol"].astype(str) == symbol
            ]
            if symbol_times.empty:
                raise RuntimeError(
                    f"reviewed archive-only symbol {symbol} has no bridge bars"
                )
            current_rows.append(
                {
                    "symbol": symbol,
                    "contract_type": "PERPETUAL",
                    "quote_asset": "USDT",
                    "margin_asset": "USDT",
                    "is_crypto": True,
                    "onboard_date": symbol_times.min(),
                    "delivery_date": symbol_times.max() + INTERVAL,
                    "underlying_type": "COIN",
                    "metadata_source": "live_archive_only_reviewed_inference",
                }
            )
    additions = pd.DataFrame(current_rows, columns=_empty_metadata().columns)
    result = pd.concat([existing, additions], ignore_index=True)
    if not result.empty:
        result = result.sort_values("symbol").reset_index(drop=True)
        if result["symbol"].duplicated().any():
            raise ValueError("live metadata cache contains duplicate symbols")
        for symbol in sorted(existing_symbols & set(contracts)):
            reasons = current_contract_violations(contracts[symbol], expected_symbol=symbol)
            if reasons:
                raise RuntimeError(
                    f"previously accepted live contract {symbol} changed classification: {reasons}"
                )
    _write_parquet_atomic(result, path)
    return result


def apply_live_contract_lifecycle(
    metadata: pd.DataFrame,
    lifecycle: Mapping[str, Any],
) -> pd.DataFrame:
    """Overlay horizon-independent lifecycle evidence without changing classification."""

    result = metadata.copy()
    for index, row in result.iterrows():
        symbol = str(row["symbol"])
        evidence = lifecycle.get(symbol)
        if evidence is None:
            continue
        if not isinstance(evidence, Mapping):
            raise ValueError(f"lifecycle evidence for {symbol} is malformed")
        if evidence.get("onboard_date") is not None:
            result.at[index, "onboard_date"] = _utc(evidence["onboard_date"])
        result.at[index, "delivery_date"] = _utc(evidence["delivery_date"])
    if set(result["symbol"].astype(str)) != set(metadata["symbol"].astype(str)):
        raise RuntimeError("live lifecycle overlay changed the metadata symbol set")
    missing = set(lifecycle) - set(result["symbol"].astype(str))
    if missing:
        raise RuntimeError(
            f"lifecycle registry symbols are absent from metadata: {sorted(missing)}"
        )
    return result


def resolve_contract_lifecycle(
    candidate_symbols: Iterable[str],
    known_contracts: Mapping[str, Mapping[str, Any]],
    bridge_bars: pd.DataFrame,
    forming_bars: pd.DataFrame,
    *,
    replay_boundary: pd.Timestamp,
    client: Team09PublicDataClient,
) -> dict[str, dict[str, object]]:
    """Resolve delistings through the current horizon, never the replay query horizon."""

    candidates = tuple(sorted(set(str(value) for value in candidate_symbols)))
    horizon = current_boundary()
    if horizon < replay_boundary:
        raise ValueError("lifecycle evidence horizon precedes the replay boundary")
    observed = pd.concat([bridge_bars, forming_bars], ignore_index=True)
    observed_times = pd.to_datetime(observed["open_time"], utc=True)
    absent = tuple(symbol for symbol in candidates if symbol not in known_contracts)
    horizon_times: dict[str, pd.DatetimeIndex] = {}
    if horizon > replay_boundary:
        end = horizon + INTERVAL - pd.Timedelta(milliseconds=1)
        for symbol in absent:
            frame = client.transaction_bars(
                symbol,
                start=BRIDGE_START,
                end_inclusive=end,
            )
            horizon_times[symbol] = pd.DatetimeIndex(
                pd.to_datetime(frame["open_time"], utc=True)
            )
    else:
        for symbol in absent:
            horizon_times[symbol] = pd.DatetimeIndex(
                observed_times.loc[observed["symbol"].astype(str) == symbol]
            )

    result: dict[str, dict[str, object]] = {}
    for symbol in candidates:
        if symbol in known_contracts:
            contract = known_contracts[symbol]
            onboard = pd.Timestamp(int(contract["onboardDate"]), unit="ms", tz="UTC")
            delivery = pd.Timestamp(
                int(contract["deliveryDate"]), unit="ms", tz="UTC"
            )
            source = "exchangeInfo"
        else:
            times = horizon_times[symbol]
            onboard = None
            delivery = BRIDGE_START if not len(times) else times.max() + INTERVAL
            source = "full-current-horizon-bar-lifecycle"
        result[symbol] = {
            "onboard_date": onboard.isoformat() if onboard is not None else None,
            "delivery_date": delivery.isoformat(),
            "evidence_through": horizon.isoformat(),
            "source": source,
        }
    return result


def probe_unclassified_bridge_symbols(
    symbols: Iterable[str],
    *,
    boundary: pd.Timestamp,
    client: Team09PublicDataClient,
) -> tuple[str, ...]:
    """Return archive-only symbols with bridge bars and no exchange classification."""

    present: list[str] = []
    end = boundary + INTERVAL - pd.Timedelta(milliseconds=1)
    for symbol in sorted(set(symbols)):
        frame = client.transaction_bars(
            symbol,
            start=BRIDGE_START,
            end_inclusive=end,
        )
        if not frame.empty:
            present.append(symbol)
    return tuple(present)


def refresh_bar_cache(
    path: Path,
    symbols: Iterable[str],
    *,
    required_current_symbols: Iterable[str],
    boundary: pd.Timestamp,
    client: Team09PublicDataClient,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch serial transaction bars and freeze only completed bridge rows."""

    existing = pd.read_parquet(path) if path.is_file() else _empty_bars()
    last_by_symbol = _latest_by_symbol(existing, "open_time")
    completed_frames: list[pd.DataFrame] = []
    forming_frames: list[pd.DataFrame] = []
    end = boundary + INTERVAL - pd.Timedelta(milliseconds=1)
    required_current = set(str(symbol) for symbol in required_current_symbols)
    for symbol in sorted(set(str(value) for value in symbols)):
        start = _incremental_start(
            last_by_symbol.get(symbol),
            floor=BRIDGE_START,
            overlap=INTERVAL,
        )
        frame = client.transaction_bars(symbol, start=start, end_inclusive=end)
        if frame.empty and symbol in required_current:
            raise RuntimeError(
                f"no bridge transaction bars returned for active contract {symbol}"
            )
        stable = frame.loc[frame["open_time"] < boundary]
        current = frame.loc[frame["open_time"] == boundary]
        if not stable.empty:
            completed_frames.append(stable)
        if not current.empty:
            row = current.iloc[[-1]].copy()
            open_price = row["open"].iloc[0]
            row.loc[:, "high"] = open_price
            row.loc[:, "low"] = open_price
            row.loc[:, "close"] = open_price
            row.loc[:, "volume"] = 0.0
            row.loc[:, "quote_volume"] = 0.0
            row.loc[:, "trade_count"] = 0
            row.loc[:, "taker_buy_volume"] = 0.0
            row.loc[:, "taker_buy_quote_volume"] = 0.0
            forming_frames.append(row)
    fresh = (
        pd.concat(completed_frames, ignore_index=True)
        if completed_frames
        else _empty_bars()
    )
    frozen = _append_invariant_cache(
        path,
        fresh,
        keys=("open_time", "symbol"),
        values=_BAR_VALUE_COLUMNS,
    )
    forming = (
        pd.concat(forming_frames, ignore_index=True)
        if forming_frames
        else _empty_bars()
    )
    missing_current = required_current - set(forming["symbol"].astype(str))
    if missing_current:
        raise RuntimeError(
            "active pure-crypto contracts lack forming transaction opens: "
            f"{sorted(missing_current)}"
        )
    return frozen, forming


def refresh_mark_cache(
    path: Path,
    symbols: Iterable[str],
    *,
    boundary: pd.Timestamp,
    client: Team09PublicDataClient,
) -> pd.DataFrame:
    existing = pd.read_parquet(path) if path.is_file() else _empty_marks()
    last_by_symbol = _latest_by_symbol(existing, "mark_time")
    frames: list[pd.DataFrame] = []
    for symbol in sorted(set(symbols)):
        start = _incremental_start(
            last_by_symbol.get(symbol),
            floor=BRIDGE_START,
            overlap=INTERVAL,
        )
        frame = client.mark_prices(
            symbol,
            start=start,
            end_inclusive=boundary,
        )
        if frame.empty:
            continue
        times = pd.to_datetime(frame["mark_time"], utc=True)
        frames.append(frame.loc[(times.dt.hour % INTERVAL_HOURS) == 0])
    fresh = pd.concat(frames, ignore_index=True) if frames else _empty_marks()
    return _append_invariant_cache(
        path,
        fresh,
        keys=("mark_time", "symbol"),
        values=_MARK_VALUE_COLUMNS,
    )


def refresh_funding_cache(
    path: Path,
    symbols: Iterable[str],
    *,
    boundary: pd.Timestamp,
    client: Team09PublicDataClient,
) -> pd.DataFrame:
    existing = pd.read_parquet(path) if path.is_file() else _empty_funding()
    last_by_symbol = _latest_by_symbol(existing, "funding_time")
    frames: list[pd.DataFrame] = []
    for symbol in sorted(set(symbols)):
        start = _incremental_start(
            last_by_symbol.get(symbol),
            floor=BRIDGE_START,
            overlap=pd.Timedelta(hours=24),
        )
        frame = client.funding(
            symbol,
            start=start,
            end_inclusive=boundary + pd.Timedelta(milliseconds=999),
        )
        if not frame.empty:
            frames.append(frame)
    fresh = pd.concat(frames, ignore_index=True) if frames else _empty_funding()
    return _append_invariant_cache(
        path,
        fresh,
        keys=("funding_time", "symbol"),
        values=_FUNDING_VALUE_COLUMNS,
    )


def combine_contract_metadata(
    frozen: pd.DataFrame,
    live: pd.DataFrame,
) -> pd.DataFrame:
    result = pd.concat([frozen, live], ignore_index=True)
    if result["symbol"].duplicated().any():
        raise ValueError("combined contract metadata contains duplicate symbols")
    return result.sort_values("symbol").reset_index(drop=True)


def extend_membership(
    frozen_membership: pd.DataFrame,
    bars: pd.DataFrame,
    metadata: pd.DataFrame,
    *,
    boundary: pd.Timestamp,
) -> pd.DataFrame:
    first = BRIDGE_START.normalize()
    first += pd.Timedelta(days=(7 - first.weekday()) % 7)
    last = boundary.normalize() - pd.Timedelta(days=boundary.weekday())
    if last < first:
        return frozen_membership.copy()
    reconstitutions = pd.date_range(first, last, freq="7D", tz="UTC")
    live = point_in_time_top40(
        bars,
        metadata,
        reconstitutions,
        top_n=40,
        trailing_days=30,
        min_history_days=30,
        bars_per_day=3,
    )
    expected = set(reconstitutions)
    present = set(pd.to_datetime(live["reconstitution_time"], utc=True))
    if present != expected:
        missing = sorted(expected - present)
        raise RuntimeError(f"empty live Team 09 membership reconstitutions: {missing}")
    for timestamp, group in live.groupby("reconstitution_time", observed=True):
        ranks = sorted(int(value) for value in group["liquidity_rank"])
        if len(group) != 40 or ranks != list(range(1, 41)):
            raise RuntimeError(
                "Team 09 live membership is not an exact Top40 at "
                f"{pd.Timestamp(timestamp).isoformat()}"
            )
    historical = frozen_membership.loc[
        pd.to_datetime(frozen_membership["reconstitution_time"], utc=True) < first
    ]
    result = pd.concat([historical, live], ignore_index=True)
    return result.sort_values(["reconstitution_time", "liquidity_rank"]).reset_index(drop=True)


def validate_live_cache_domains(
    bars: pd.DataFrame,
    forming: pd.DataFrame,
    live_metadata: pd.DataFrame,
    known_contracts: Mapping[str, Mapping[str, Any]],
    candidate_symbols: Iterable[str],
    lifecycle: Mapping[str, Any],
) -> None:
    candidates = set(str(symbol) for symbol in candidate_symbols)
    if not candidates:
        raise RuntimeError("Team 09 live candidate registry is empty")
    observed = (
        set(bars["symbol"].astype(str))
        | set(forming["symbol"].astype(str))
        | set(live_metadata["symbol"].astype(str))
        | set(known_contracts)
    )
    extras = observed - candidates
    if extras:
        raise RuntimeError(
            f"Team 09 live cache contains symbols outside its registry: {sorted(extras)}"
        )
    rejected = {
        symbol: symbol_policy_violations(symbol)
        for symbol in candidates
        if symbol_policy_violations(symbol)
    }
    if rejected:
        raise RuntimeError(
            f"Team 09 candidate registry violates pure-crypto policy: {rejected}"
        )
    if set(lifecycle) != candidates:
        raise RuntimeError(
            "Team 09 lifecycle registry differs from the candidate registry"
        )


def validate_live_cache_coverage(
    bars: pd.DataFrame,
    forming: pd.DataFrame,
    funding: pd.DataFrame,
    marks: pd.DataFrame,
    membership: pd.DataFrame,
    *,
    required_accounting_symbols: Iterable[str],
    boundary: pd.Timestamp,
) -> None:
    current_members = set(_membership_at(membership, boundary))
    required_symbols = current_members | set(
        str(symbol) for symbol in required_accounting_symbols
    )
    forming_symbols = set(
        forming.loc[
            pd.to_datetime(forming["open_time"], utc=True) == boundary, "symbol"
        ].astype(str)
    )
    missing_opens = required_symbols - forming_symbols
    if missing_opens:
        raise RuntimeError(
            "Team 09 current members/carried symbols lack exact transaction "
            f"opens: {sorted(missing_opens)}"
        )
    current_marks = set(
        marks.loc[pd.to_datetime(marks["mark_time"], utc=True) == boundary, "symbol"].astype(str)
    )
    missing_marks = required_symbols - current_marks
    if missing_marks:
        raise RuntimeError(
            "Team 09 current members/carried symbols lack exact boundary "
            f"marks: {sorted(missing_marks)}"
        )
    funding_times = pd.to_datetime(funding["funding_time"], utc=True)
    if (funding_times > boundary + pd.Timedelta(seconds=1)).any():
        raise RuntimeError("Team 09 funding cache contains future settlements")
    latest_complete = boundary - INTERVAL
    bar_times = pd.to_datetime(bars["open_time"], utc=True)
    complete_symbols = set(
        bars.loc[bar_times == latest_complete, "symbol"].astype(str)
    )
    missing_complete = required_symbols - complete_symbols
    if missing_complete:
        raise RuntimeError(
            "Team 09 current members/carried symbols lack the latest completed bar: "
            f"{sorted(missing_complete)}"
        )


def verify_live_cache_manifest(
    cache_dir: str | Path,
    *,
    required: bool = True,
) -> Mapping[str, Any] | None:
    """Verify every load-bearing live-cache file before it is trusted."""

    cache = Path(cache_dir).resolve()
    manifest_path = cache / "cache-manifest.json"
    if not manifest_path.is_file():
        managed = (
            "archive-kline-provenance.json",
            "bars.parquet",
            "forming-bars.parquet",
            "mark_prices.parquet",
            "funding.parquet",
            "contract_metadata.parquet",
            "classified-contracts.json",
            "contract-lifecycle.json",
            "archive-symbols.json",
            "candidate-symbols.json",
            "excluded-contracts.json",
            "diagnostics.json",
        )
        existing = [name for name in managed if (cache / name).exists()]
        if existing:
            raise RuntimeError(
                "UNSEALED LIVE CACHE: cache-manifest.json is missing while "
                f"managed files exist: {existing}"
            )
        if required:
            raise FileNotFoundError(
                f"Team 09 live cache manifest is missing: {manifest_path}"
            )
        return None
    payload = _load_json_mapping(manifest_path)
    if payload.get("schema_version") != CACHE_SCHEMA_VERSION:
        raise RuntimeError("Team 09 live cache manifest schema drift")
    if payload.get("pure_crypto_policy_id") != POLICY_ID:
        raise RuntimeError("Team 09 live cache pure-crypto policy drift")
    entries = payload.get("files")
    if not isinstance(entries, list) or not entries:
        raise ValueError("Team 09 live cache manifest has no file bindings")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, Mapping):
            raise ValueError("Team 09 live cache manifest contains a non-object")
        relative = entry.get("path")
        if (
            not isinstance(relative, str)
            or relative in seen
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise ValueError("Team 09 live cache manifest path is unsafe or duplicated")
        seen.add(relative)
        path = (cache / relative).resolve()
        if not path.is_relative_to(cache) or not path.is_file():
            raise RuntimeError(f"Team 09 live cache file is missing: {relative}")
        if path.stat().st_size != entry.get("size"):
            raise RuntimeError(f"Team 09 live cache size drift: {relative}")
        if _sha256_file(path) != entry.get("sha256"):
            raise RuntimeError(f"Team 09 live cache hash drift: {relative}")
        if _cache_file_rows(path) != entry.get("rows"):
            raise RuntimeError(f"Team 09 live cache row-count drift: {relative}")
    required_paths = {
        "archive-kline-provenance.json",
        "archive-symbols.json",
        "bars.parquet",
        "candidate-symbols.json",
        "classified-contracts.json",
        "contract-lifecycle.json",
        "contract_metadata.parquet",
        "diagnostics.json",
        "excluded-contracts.json",
        "forming-bars.parquet",
        "funding.parquet",
        "mark_prices.parquet",
    }
    boundary_prefix = exact_boundary(payload["boundary"]).strftime(
        "%Y%m%dT%H%M%SZ"
    )
    exchange_paths = {
        relative
        for relative in seen
        if relative.startswith(f"exchange-info/{boundary_prefix}-")
        and relative.endswith(".json")
    }
    if len(exchange_paths) != 1 or seen != required_paths | exchange_paths:
        raise RuntimeError(
            "Team 09 live cache manifest does not bind the exact load-bearing set"
        )
    diagnostics = _load_json_mapping(cache / "diagnostics.json")
    if diagnostics.get("boundary") != payload.get("boundary"):
        raise RuntimeError("Team 09 live cache manifest/diagnostic boundary drift")
    return payload


def write_live_cache_manifest(
    cache_dir: str | Path,
    *,
    boundary: pd.Timestamp,
) -> Path:
    """Seal the exact current cache generation after all coverage checks pass."""

    cache = Path(cache_dir).resolve()
    required_names = (
        "archive-kline-provenance.json",
        "archive-symbols.json",
        "bars.parquet",
        "candidate-symbols.json",
        "classified-contracts.json",
        "contract-lifecycle.json",
        "contract_metadata.parquet",
        "diagnostics.json",
        "excluded-contracts.json",
        "forming-bars.parquet",
        "funding.parquet",
        "mark_prices.parquet",
    )
    paths = [cache / name for name in required_names]
    boundary_prefix = exact_boundary(boundary).strftime("%Y%m%dT%H%M%SZ")
    exchange_snapshots = sorted(
        (cache / "exchange-info").glob(f"{boundary_prefix}-*.json")
    )
    if not exchange_snapshots:
        raise RuntimeError("Team 09 live cache has no exchangeInfo evidence")
    paths.append(exchange_snapshots[-1])
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Team 09 cannot seal incomplete live cache: {missing}")
    entries = []
    for path in sorted(paths):
        entries.append(
            {
                "path": path.relative_to(cache).as_posix(),
                "size": path.stat().st_size,
                "rows": _cache_file_rows(path),
                "sha256": _sha256_file(path),
            }
        )
    payload = {
        "schema_version": CACHE_SCHEMA_VERSION,
        "boundary": exact_boundary(boundary).isoformat(),
        "pure_crypto_policy_id": POLICY_ID,
        "files": entries,
    }
    manifest_path = cache / "cache-manifest.json"
    _write_json_atomic(payload, manifest_path)
    verify_live_cache_manifest(cache)
    return manifest_path


def _append_invariant_cache(
    path: Path,
    fresh: pd.DataFrame,
    *,
    keys: tuple[str, str],
    values: tuple[str, ...],
) -> pd.DataFrame:
    fresh = fresh.copy()
    if fresh.duplicated(list(keys)).any():
        raise ValueError(f"fresh live cache contains duplicate keys: {keys}")
    existing = pd.read_parquet(path) if path.is_file() else fresh.iloc[0:0].copy()
    if not existing.empty:
        overlap = existing.merge(
            fresh,
            on=list(keys),
            how="inner",
            suffixes=("_old", "_new"),
            validate="one_to_one",
        )
        for column in values:
            old = overlap[f"{column}_old"].to_numpy()
            new = overlap[f"{column}_new"].to_numpy()
            if not _exact_array_equal(old, new):
                raise RuntimeError(
                    f"APPEND-INVARIANCE ABORT: {path.name} revised historical {column}"
                )
    additions = fresh.merge(
        existing.loc[:, list(keys)],
        on=list(keys),
        how="left",
        indicator=True,
    )
    additions = additions.loc[additions["_merge"] == "left_only", fresh.columns]
    result = pd.concat([existing, additions], ignore_index=True)
    result = result.sort_values(list(keys)).reset_index(drop=True)
    _write_parquet_atomic(result, path)
    return result


def _combine_historical(
    historical: pd.DataFrame,
    bridge: pd.DataFrame,
    *,
    time_column: str,
    bridge_start: pd.Timestamp,
) -> pd.DataFrame:
    historical_times = pd.to_datetime(historical[time_column], utc=True)
    bridge_times = pd.to_datetime(bridge[time_column], utc=True)
    before = historical.loc[historical_times < bridge_start]
    after = bridge.loc[bridge_times >= bridge_start]
    result = pd.concat([before, after], ignore_index=True)
    keys = [time_column, "symbol"]
    if result.duplicated(keys).any():
        raise ValueError(f"combined Team 09 data contains duplicate keys: {keys}")
    return result.sort_values(keys).reset_index(drop=True)


def _accounting_admission_symbols(
    cached_diagnostics: Mapping[str, Any],
    prior: Mapping[str, object] | None,
) -> set[str]:
    symbols: set[str] = set()
    legacy = cached_diagnostics.get("accounting_symbols", ())
    if not isinstance(legacy, (list, tuple)):
        raise ValueError("cached accounting symbols are malformed")
    for symbol in legacy:
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("cached accounting symbols are malformed")
        symbols.add(symbol)
    for raw in (
        cached_diagnostics.get("accounting_admission_boundaries"),
        prior,
    ):
        if raw is None:
            continue
        if not isinstance(raw, Mapping):
            raise ValueError("accounting admission boundaries must be an object")
        for symbol in raw:
            if not isinstance(symbol, str) or not symbol:
                raise ValueError("accounting admission symbol is malformed")
            symbols.add(symbol)
    return symbols


def _normalise_accounting_admissions(
    raw: Mapping[str, object],
    *,
    boundary: pd.Timestamp,
) -> dict[str, str]:
    result: dict[str, str] = {}
    for symbol, value in raw.items():
        if not isinstance(symbol, str) or not symbol:
            raise ValueError("accounting admission symbol is malformed")
        admission = exact_boundary(value)
        if admission > boundary:
            raise RuntimeError(
                "accounting admission boundary is later than the replay boundary: "
                f"{symbol}={admission.isoformat()}"
            )
        result[symbol] = admission.isoformat()
    return dict(sorted(result.items()))


def _resolve_accounting_admissions(
    cached_diagnostics: Mapping[str, Any],
    *,
    prior: Mapping[str, object] | None,
    accounting_symbols: Iterable[str],
    boundary: pd.Timestamp,
) -> dict[str, str]:
    current = tuple(sorted(set(str(symbol) for symbol in accounting_symbols)))
    cached_raw = cached_diagnostics.get("accounting_admission_boundaries")
    if cached_raw is not None and not isinstance(cached_raw, Mapping):
        raise ValueError("cached accounting admission boundaries are malformed")
    cached = (
        _normalise_accounting_admissions(cached_raw, boundary=boundary)
        if isinstance(cached_raw, Mapping)
        else {}
    )
    if prior is not None:
        if not isinstance(prior, Mapping):
            raise ValueError("prior accounting admission boundaries are malformed")
        resolved = _normalise_accounting_admissions(prior, boundary=boundary)
    elif cached:
        resolved = dict(cached)
    elif cached_diagnostics:
        legacy = cached_diagnostics.get("accounting_symbols")
        if not isinstance(legacy, (list, tuple)):
            raise ValueError("legacy cached accounting symbols are malformed")
        resolved = {
            str(symbol): BRIDGE_START.isoformat()
            for symbol in legacy
        }
    else:
        resolved = {
            symbol: BRIDGE_START.isoformat()
            for symbol in current
        }

    unknown = set(resolved) - set(current)
    if unknown:
        raise RuntimeError(
            "accounting admissions contain symbols outside the replay registry: "
            f"{sorted(unknown)}"
        )
    for symbol in current:
        if symbol not in resolved:
            resolved[symbol] = boundary.isoformat()
    for symbol, cached_boundary in cached.items():
        expected = resolved.get(symbol)
        if expected is not None and cached_boundary != expected:
            raise RuntimeError(
                "APPEND-INVARIANCE ABORT: accounting admission revised for "
                f"{symbol}: {cached_boundary} != {expected}"
            )
    return dict(sorted(resolved.items()))


def _causal_accounting_rows(
    frame: pd.DataFrame,
    *,
    time_column: str,
    admissions: Mapping[str, str],
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    required = {time_column, "symbol"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"accounting frame missing columns: {sorted(missing)}")
    symbols = frame["symbol"].astype(str)
    unknown = set(symbols) - set(admissions)
    if unknown:
        raise RuntimeError(
            "accounting cache contains symbols without admission evidence: "
            f"{sorted(unknown)}"
        )
    times = pd.to_datetime(frame[time_column], utc=True, errors="raise")
    admitted = pd.to_datetime(symbols.map(admissions), utc=True, errors="raise")
    return frame.loc[times >= admitted].copy()


def _membership_at(membership: pd.DataFrame, boundary: pd.Timestamp) -> tuple[str, ...]:
    times = pd.to_datetime(membership["reconstitution_time"], utc=True)
    valid = times[times <= boundary]
    if valid.empty:
        return ()
    latest = valid.max()
    return tuple(
        membership.loc[times == latest]
        .sort_values("liquidity_rank")["symbol"]
        .astype(str)
    )


def _read_archive_kline_rows(
    archive_bytes: bytes,
    *,
    expected_csv_name: str,
) -> list[list[object]]:
    try:
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = [
                info.filename
                for info in archive.infolist()
                if not info.is_dir()
            ]
            if len(names) != 1 or Path(names[0]).name != expected_csv_name:
                raise ValueError(
                    "Binance daily kline archive has an unexpected member set"
                )
            raw_csv = archive.read(names[0])
    except zipfile.BadZipFile as exc:
        raise ValueError("Binance daily kline archive is not a valid ZIP") from exc
    try:
        parsed = list(csv.reader(io.StringIO(raw_csv.decode("utf-8-sig"))))
    except UnicodeDecodeError as exc:
        raise ValueError("Binance daily kline archive is not UTF-8") from exc
    parsed = [row for row in parsed if row]
    expected_header = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "count",
        "taker_buy_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]
    if parsed and parsed[0][0] == "open_time":
        if parsed[0] != expected_header:
            raise ValueError("Binance daily kline archive header drift")
        parsed = parsed[1:]
    result: list[list[object]] = []
    for row in parsed:
        if len(row) != 12:
            raise ValueError("Binance daily kline archive row width drift")
        normalized: list[object] = list(row)
        normalized[0] = _archive_timestamp_milliseconds(row[0])
        normalized[6] = _archive_timestamp_milliseconds(row[6])
        _validate_kline_row(
            normalized,
            interval_ms=INTERVAL_HOURS * 3_600_000,
        )
        result.append(normalized)
    return result


def _archive_timestamp_milliseconds(value: object) -> int:
    timestamp = int(value)
    if timestamp > 10_000_000_000_000:
        timestamp //= 1000
    return timestamp


def _transaction_bar_frame(symbol: str, rows: list[list[object]]) -> pd.DataFrame:
    parsed: list[dict[str, object]] = []
    for row in rows:
        _validate_kline_row(row, interval_ms=INTERVAL_HOURS * 3_600_000)
        parsed.append(
            {
                "open_time": pd.Timestamp(int(row[0]), unit="ms", tz="UTC"),
                "symbol": symbol,
                "open": _positive_float(row[1], "transaction open"),
                "high": _positive_float(row[2], "transaction high"),
                "low": _positive_float(row[3], "transaction low"),
                "close": _positive_float(row[4], "transaction close"),
                "volume": _nonnegative_float(row[5], "transaction volume"),
                "close_time": pd.Timestamp(int(row[6]), unit="ms", tz="UTC"),
                "quote_volume": _nonnegative_float(
                    row[7], "transaction quote volume"
                ),
                "trade_count": int(row[8]),
                "taker_buy_volume": _nonnegative_float(
                    row[9], "transaction taker-buy volume"
                ),
                "taker_buy_quote_volume": _nonnegative_float(
                    row[10], "transaction taker-buy quote volume"
                ),
            }
        )
    return pd.DataFrame(parsed, columns=("symbol", *_KLINE_COLUMNS)).loc[
        :, _empty_bars().columns
    ]


def _validate_kline_row(row: list[object], *, interval_ms: int) -> None:
    if len(row) != 12:
        raise ValueError("Binance kline row must contain exactly 12 fields")
    open_time = int(row[0])
    close_time = int(row[6])
    if close_time != open_time + interval_ms - 1:
        raise ValueError("Binance kline row has the wrong close boundary")


def _empty_bars() -> pd.DataFrame:
    return pd.DataFrame(columns=("open_time", "symbol", *_BAR_VALUE_COLUMNS))


def _empty_marks() -> pd.DataFrame:
    return pd.DataFrame(columns=["mark_time", "symbol", "mark_price"])


def _empty_funding() -> pd.DataFrame:
    return pd.DataFrame(
        columns=["funding_time", "symbol", "funding_rate", "mark_price"]
    )


def _empty_metadata() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "symbol",
            "contract_type",
            "quote_asset",
            "margin_asset",
            "is_crypto",
            "onboard_date",
            "delivery_date",
            "underlying_type",
            "metadata_source",
        ]
    )


def _exact_array_equal(left: np.ndarray, right: np.ndarray) -> bool:
    if left.dtype.kind in "fc" or right.dtype.kind in "fc":
        return bool(np.array_equal(left, right, equal_nan=True))
    return bool(np.array_equal(left, right))


def _read_required_parquet(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(f"Team 09 live cache is missing: {path}")
    return pd.read_parquet(path)


def _latest_by_symbol(frame: pd.DataFrame, time_column: str) -> dict[str, pd.Timestamp]:
    if frame.empty:
        return {}
    times = pd.to_datetime(frame[time_column], utc=True, errors="raise")
    values = pd.DataFrame(
        {"symbol": frame["symbol"].astype(str), "timestamp": times}
    )
    return {
        str(symbol): pd.Timestamp(timestamp)
        for symbol, timestamp in values.groupby(
            "symbol", observed=True
        )["timestamp"].max().items()
    }


def _incremental_start(
    latest: pd.Timestamp | None,
    *,
    floor: pd.Timestamp,
    overlap: pd.Timedelta,
) -> pd.Timestamp:
    return floor if latest is None else max(floor, latest - overlap)


def _write_parquet_atomic(frame: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    frame.to_parquet(
        temporary,
        engine="pyarrow",
        compression="zstd",
        index=False,
    )
    os.replace(temporary, path)


def _write_json_atomic(payload: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def _write_immutable_json(payload: object, path: Path) -> None:
    canonical = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if path.is_file():
        if path.read_text(encoding="utf-8") != canonical:
            raise RuntimeError(
                f"APPEND-INVARIANCE ABORT: immutable {path.name} changed"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(canonical, encoding="utf-8")
    os.replace(temporary, path)


def _archive_provenance_record(value: object) -> dict[str, object]:
    expected_fields = {
        "archive_path",
        "archive_sha256",
        "archive_size",
        "checksum_path",
        "checksum_payload_sha256",
    }
    if not isinstance(value, Mapping) or set(value) != expected_fields:
        raise ValueError("archive kline provenance record has an invalid schema")
    archive_path = value["archive_path"]
    archive_sha256 = value["archive_sha256"]
    archive_size = value["archive_size"]
    checksum_path = value["checksum_path"]
    checksum_payload_sha256 = value["checksum_payload_sha256"]
    if (
        not isinstance(archive_path, str)
        or not archive_path.startswith(ARCHIVE_DAILY_KLINE_PREFIX)
        or not archive_path.endswith(".zip")
        or Path(archive_path).is_absolute()
        or ".." in Path(archive_path).parts
        or checksum_path != f"{archive_path}.CHECKSUM"
        or not isinstance(archive_size, int)
        or isinstance(archive_size, bool)
        or archive_size <= 0
    ):
        raise ValueError("archive kline provenance path/size is invalid")
    for digest in (archive_sha256, checksum_payload_sha256):
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError("archive kline provenance digest is invalid")
    return {
        "archive_path": archive_path,
        "archive_sha256": archive_sha256,
        "archive_size": archive_size,
        "checksum_path": checksum_path,
        "checksum_payload_sha256": checksum_payload_sha256,
    }


def _load_archive_provenance(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise FileNotFoundError(f"Team 09 live cache is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("archive kline provenance must be a JSON array")
    records = [_archive_provenance_record(value) for value in payload]
    keys = [str(record["archive_path"]) for record in records]
    if len(keys) != len(set(keys)) or keys != sorted(keys):
        raise ValueError("archive kline provenance paths are duplicate or unordered")
    return records


def _merge_archive_provenance(
    path: Path,
    fresh: Iterable[Mapping[str, object]],
) -> list[dict[str, object]]:
    existing = _load_archive_provenance(path) if path.is_file() else []
    records = {
        str(record["archive_path"]): record
        for record in existing
    }
    for raw in fresh:
        record = _archive_provenance_record(raw)
        key = str(record["archive_path"])
        previous = records.get(key)
        if previous is not None and previous != record:
            raise RuntimeError(
                f"APPEND-INVARIANCE ABORT: archive provenance revised {key}"
            )
        records[key] = record
    result = [records[key] for key in sorted(records)]
    _write_json_atomic(result, path)
    return result


def _load_json_exclusions(path: Path) -> dict[str, tuple[str, ...]]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("excluded-contract cache must be a JSON object")
    return {
        str(symbol): tuple(str(reason) for reason in reasons)
        for symbol, reasons in payload.items()
    }


def _load_json_mapping(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{path.name} must be a JSON object")
    return payload


def _load_contract_mapping(path: Path) -> dict[str, Mapping[str, Any]]:
    payload = _load_json_mapping(path)
    result: dict[str, Mapping[str, Any]] = {}
    for symbol, contract in payload.items():
        if not isinstance(symbol, str) or not isinstance(contract, Mapping):
            raise ValueError("classified-contract cache is malformed")
        reasons = current_contract_violations(contract, expected_symbol=symbol)
        if reasons:
            raise RuntimeError(
                f"classified-contract cache violates pure-crypto policy: "
                f"{symbol}={reasons}"
            )
        result[symbol] = contract
    return result


def _load_json_list(path: Path) -> list[object]:
    if not path.is_file():
        raise FileNotFoundError(f"Team 09 live cache is missing: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError(f"{path.name} must be a JSON array")
    return payload


def _diagnostics_from_mapping(payload: Mapping[str, Any]) -> LiveDataDiagnostics:
    exclusions = payload.get("excluded_current_contracts")
    if not isinstance(exclusions, Mapping):
        raise ValueError("cached diagnostics exclusions are malformed")
    boundary = exact_boundary(payload["boundary"])
    accounting_symbols = tuple(
        str(value) for value in payload["accounting_symbols"]
    )
    raw_admissions = payload.get("accounting_admission_boundaries")
    if raw_admissions is None:
        accounting_admissions = {
            symbol: BRIDGE_START.isoformat()
            for symbol in accounting_symbols
        }
    elif isinstance(raw_admissions, Mapping):
        accounting_admissions = _normalise_accounting_admissions(
            raw_admissions,
            boundary=boundary,
        )
    else:
        raise ValueError("cached accounting admission boundaries are malformed")
    diagnostics = LiveDataDiagnostics(
        boundary=boundary,
        fetched_at=_utc(payload["fetched_at"]),
        pure_crypto_policy_id=str(payload["pure_crypto_policy_id"]),
        current_pure_crypto_symbols=tuple(
            str(value) for value in payload["current_pure_crypto_symbols"]
        ),
        known_pure_crypto_symbols=tuple(
            str(value) for value in payload["known_pure_crypto_symbols"]
        ),
        archive_catalog_symbol_count=int(payload["archive_catalog_symbol_count"]),
        candidate_symbol_count=int(payload["candidate_symbol_count"]),
        reviewed_archive_only_symbols=tuple(
            str(value) for value in payload["reviewed_archive_only_symbols"]
        ),
        unclassified_bridge_symbols=tuple(
            str(value) for value in payload["unclassified_bridge_symbols"]
        ),
        excluded_current_contracts={
            str(symbol): tuple(str(reason) for reason in reasons)
            for symbol, reasons in exclusions.items()
        },
        bridge_membership_symbols=tuple(
            str(value) for value in payload["bridge_membership_symbols"]
        ),
        accounting_symbols=accounting_symbols,
        accounting_admission_boundaries=accounting_admissions,
        current_membership_symbols=tuple(
            str(value) for value in payload["current_membership_symbols"]
        ),
        completed_bridge_bar_rows=int(payload["completed_bridge_bar_rows"]),
        bridge_funding_rows=int(payload["bridge_funding_rows"]),
        bridge_mark_rows=int(payload["bridge_mark_rows"]),
        archive_fallback_file_count=int(payload["archive_fallback_file_count"]),
    )
    if diagnostics.pure_crypto_policy_id != POLICY_ID:
        raise RuntimeError("cached diagnostics pure-crypto policy drift")
    if diagnostics.unclassified_bridge_symbols:
        raise RuntimeError("cached diagnostics contain unclassified bridge symbols")
    return diagnostics


def _cache_file_rows(path: Path) -> int:
    if path.suffix == ".parquet":
        return len(pd.read_parquet(path))
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, Mapping):
        symbols = payload.get("symbols")
        return len(symbols) if isinstance(symbols, list) else len(payload)
    raise ValueError(f"unsupported cache JSON payload: {path}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _retry_delay(retry_after: str | None, attempt: int) -> float:
    if retry_after is not None:
        try:
            return min(max(float(retry_after), 0.0), 60.0)
        except ValueError:
            pass
    return min(2.0**attempt, 30.0)


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return (
        timestamp.tz_localize("UTC")
        if timestamp.tzinfo is None
        else timestamp.tz_convert("UTC")
    )


def _milliseconds(timestamp: pd.Timestamp) -> int:
    return int(_utc(timestamp).value // 1_000_000)


def _finite_float(value: object, label: str) -> float:
    result = float(value)
    if not np.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _positive_float(value: object, label: str) -> float:
    result = _finite_float(value, label)
    if result <= 0.0:
        raise ValueError(f"{label} must be positive")
    return result


def _nonnegative_float(value: object, label: str) -> float:
    result = _finite_float(value, label)
    if result < 0.0:
        raise ValueError(f"{label} must be nonnegative")
    return result
