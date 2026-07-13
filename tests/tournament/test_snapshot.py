from __future__ import annotations

import csv
import hashlib
import io
import json
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

import httpx
import pandas as pd
import pytest

from crypto_trade.tournament import snapshot


def _zip_csv(header: list[str], rows: list[list[object]], filename: str) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        text = io.StringIO()
        writer = csv.writer(text, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)
        archive.writestr(filename, text.getvalue())
    return buffer.getvalue()


def _kline_rows(start: str, end: str, *, interval_hours: int, base: float) -> list[list[object]]:
    rows: list[list[object]] = []
    last_open = pd.Timestamp(end) - pd.Timedelta(hours=interval_hours)
    for index, timestamp in enumerate(
        pd.date_range(start, last_open, freq=f"{interval_hours}h", tz="UTC")
    ):
        open_time = int(timestamp.timestamp() * 1000)
        close = base + index / 100.0
        rows.append(
            [
                open_time,
                close,
                close + 1.0,
                close - 1.0,
                close + 0.5,
                100.0,
                open_time + interval_hours * 60 * 60 * 1000 - 1,
                1_000_000.0 if base >= 100 else 500_000.0,
                100,
                50.0,
                500_000.0,
                0,
            ]
        )
    return rows


def _listing(*, keys: list[str] = (), prefixes: list[str] = ()) -> bytes:
    contents = "".join(f"<Contents><Key>{key}</Key></Contents>" for key in keys)
    common = "".join(
        f"<CommonPrefixes><Prefix>{prefix}</Prefix></CommonPrefixes>" for prefix in prefixes
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
        f"<IsTruncated>false</IsTruncated>{contents}{common}</ListBucketResult>"
    ).encode()


class _OfficialArchiveFixture:
    def __init__(self) -> None:
        self.keys_by_prefix: dict[str, list[str]] = defaultdict(list)
        self.payloads: dict[str, bytes] = {}
        self.requests: Counter[str] = Counter()
        self.rest_events: dict[str, list[dict[str, object]]] = defaultdict(list)
        self.mark_rest_rows: dict[str, list[list[object]]] = defaultdict(list)
        self.symbols = ("AAAUSDT", "BTCUSDT")
        self.exchange_info = {
            "serverTime": 1_768_435_200_000,
            "timezone": "UTC",
            "symbols": [
                {
                    "symbol": symbol,
                    "contractType": "PERPETUAL",
                    "status": "TRADING",
                    "quoteAsset": "USDT",
                    "marginAsset": "USDT",
                    "underlyingType": "COIN",
                    "onboardDate": 1_570_000_000_000,
                    "deliveryDate": 4_102_444_800_000,
                }
                for symbol in self.symbols
            ]
            + [
                {
                    "symbol": "XAUUSDT",
                    "contractType": "TRADIFI_PERPETUAL",
                    "quoteAsset": "USDT",
                    "marginAsset": "USDT",
                    "underlyingType": "COMMODITY",
                    "onboardDate": 1_570_000_000_000,
                    "deliveryDate": 4_102_444_800_000,
                }
            ],
        }
        self._populate()

    def _add(self, prefix: str, key: str, content: bytes) -> None:
        checksum = hashlib.sha256(content).hexdigest()
        self.keys_by_prefix[prefix].extend([key, key + ".CHECKSUM"])
        self.payloads[key] = content
        self.payloads[key + ".CHECKSUM"] = f"{checksum}  {Path(key).name}\n".encode()

    def _populate(self) -> None:
        kline_header = [
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
        months = (
            ("2019-11", "2019-12-01"),
            ("2019-12", "2020-01-01"),
            ("2020-01", "2020-02-01"),
        )
        for symbol in self.symbols:
            for month_index, (year_month, month_end) in enumerate(months):
                transaction_prefix = f"data/futures/um/monthly/klines/{symbol}/8h/"
                transaction_key = f"{transaction_prefix}{symbol}-8h-{year_month}.zip"
                transaction_rows = _kline_rows(
                    f"{year_month}-01",
                    month_end,
                    interval_hours=8,
                    base=100.0 if symbol == "BTCUSDT" else 50.0,
                )
                self._add(
                    transaction_prefix,
                    transaction_key,
                    _zip_csv(kline_header, transaction_rows, f"{symbol}-8h-{year_month}.csv"),
                )

                funding_prefix = f"data/futures/um/monthly/fundingRate/{symbol}/"
                funding_key = f"{funding_prefix}{symbol}-fundingRate-{year_month}.zip"
                funding_time = int(
                    (
                        pd.Timestamp(f"{year_month}-01", tz="UTC") + pd.Timedelta(milliseconds=5)
                    ).timestamp()
                    * 1000
                )
                self._add(
                    funding_prefix,
                    funding_key,
                    _zip_csv(
                        ["calc_time", "funding_interval_hours", "last_funding_rate"],
                        [[funding_time, 8, 0.0001 + month_index / 100_000]],
                        f"{symbol}-fundingRate-{year_month}.csv",
                    ),
                )

                mark_prefix = f"data/futures/um/monthly/markPriceKlines/{symbol}/1h/"
                mark_key = f"{mark_prefix}{symbol}-1h-{year_month}.zip"
                mark_rows = _kline_rows(
                    f"{year_month}-01",
                    month_end,
                    interval_hours=1,
                    base=100.0 if symbol == "BTCUSDT" else 50.0,
                )
                self._add(
                    mark_prefix,
                    mark_key,
                    _zip_csv(kline_header, mark_rows, f"{symbol}-1h-{year_month}.csv"),
                )

    def remove_funding_archive(self, symbol: str, year_month: str) -> None:
        prefix = f"data/futures/um/monthly/fundingRate/{symbol}/"
        key = f"{prefix}{symbol}-fundingRate-{year_month}.zip"
        self.keys_by_prefix[prefix].remove(key)
        self.keys_by_prefix[prefix].remove(key + ".CHECKSUM")
        self.payloads.pop(key)
        self.payloads.pop(key + ".CHECKSUM")

    def remove_mark_archive_hour(self, symbol: str, mark_time: pd.Timestamp) -> None:
        timestamp = pd.Timestamp(mark_time)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        year_month = timestamp.strftime("%Y-%m")
        prefix = f"data/futures/um/monthly/markPriceKlines/{symbol}/1h/"
        key = f"{prefix}{symbol}-1h-{year_month}.zip"
        with zipfile.ZipFile(io.BytesIO(self.payloads[key])) as archive:
            names = archive.namelist()
            assert len(names) == 1
            filename = names[0]
            rows = list(csv.reader(io.StringIO(archive.read(filename).decode())))
        target_ms = int(timestamp.timestamp() * 1000)
        filtered = [rows[0], *(row for row in rows[1:] if int(row[0]) != target_ms)]
        assert len(filtered) == len(rows) - 1
        content = _zip_csv(filtered[0], filtered[1:], filename)
        checksum = hashlib.sha256(content).hexdigest()
        self.payloads[key] = content
        self.payloads[key + ".CHECKSUM"] = f"{checksum}  {Path(key).name}\n".encode()

    def add_daily_mark_archive(
        self,
        symbol: str,
        day: pd.Timestamp,
        *,
        base: float,
    ) -> str:
        timestamp = pd.Timestamp(day)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("UTC")
        else:
            timestamp = timestamp.tz_convert("UTC")
        timestamp = timestamp.floor("D")
        date = timestamp.strftime("%Y-%m-%d")
        prefix = f"data/futures/um/daily/markPriceKlines/{symbol}/1h/"
        key = f"{prefix}{symbol}-1h-{date}.zip"
        content = _zip_csv(
            [
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
            ],
            _kline_rows(
                timestamp.isoformat(),
                (timestamp + pd.Timedelta(days=1)).isoformat(),
                interval_hours=1,
                base=base,
            ),
            f"{symbol}-1h-{date}.csv",
        )
        self._add(prefix, key, content)
        return key

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.requests[str(request.url)] += 1
        if request.url.host == "fapi.binance.com":
            if request.url.path == "/fapi/v1/exchangeInfo":
                return httpx.Response(200, json=self.exchange_info)
            if request.url.path == "/fapi/v1/fundingRate":
                symbol = request.url.params["symbol"]
                start = int(request.url.params["startTime"])
                end = int(request.url.params["endTime"])
                limit = int(request.url.params["limit"])
                rows = [
                    row
                    for row in self.rest_events[symbol]
                    if start <= int(row["fundingTime"]) <= end
                ]
                return httpx.Response(200, json=rows[:limit])
            if request.url.path == "/fapi/v1/markPriceKlines":
                symbol = request.url.params["symbol"]
                start = int(request.url.params["startTime"])
                end = int(request.url.params["endTime"])
                limit = int(request.url.params["limit"])
                rows = [row for row in self.mark_rest_rows[symbol] if start <= int(row[0]) <= end]
                return httpx.Response(200, json=rows[:limit])
            return httpx.Response(404)
        if request.url.host == "s3-ap-northeast-1.amazonaws.com":
            prefix = request.url.params.get("prefix", "")
            delimiter = request.url.params.get("delimiter")
            if prefix == "data/futures/um/monthly/klines/" and delimiter == "/":
                prefixes = [f"{prefix}{symbol}/" for symbol in (*self.symbols, "XAUUSDT")]
                return httpx.Response(200, content=_listing(prefixes=prefixes))
            return httpx.Response(200, content=_listing(keys=self.keys_by_prefix.get(prefix, [])))
        if request.url.host == "data.binance.vision":
            key = request.url.path.lstrip("/")
            if key in self.payloads:
                return httpx.Response(200, content=self.payloads[key])
        return httpx.Response(404)


def _write_config(root: Path) -> Path:
    path = root / "tournament/top40/config.toml"
    path.parent.mkdir(parents=True)
    path.write_text(
        """
schema_version = 1

[data]
source = "binance-public-usdm"
archive_base_url = "https://data.binance.vision"
archive_s3_url = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
exchange_info_url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
funding_rate_url = "https://fapi.binance.com/fapi/v1/fundingRate"
mark_price_klines_url = "https://fapi.binance.com/fapi/v1/markPriceKlines"
warmup_start = "2019-11-01"
hard_end_exclusive = "2020-02-01"
transaction_interval = "8h"
mark_price_interval = "1h"
checksum_policy = "require-binance-sha256-sidecar"
parser_version = "test-snapshot-v1"

[splits]
in_sample_start = "2020-01-01"

[universe]
size = 2
trailing_days = 30
minimum_history_days = 30
""".lstrip(),
        encoding="utf-8",
    )
    return path


def _pin_test_builder(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = root / "src/crypto_trade/tournament/snapshot.py"
    path.parent.mkdir(parents=True)
    path.write_text("# pinned mocked snapshot builder\n", encoding="utf-8")
    monkeypatch.setattr(snapshot, "__file__", str(path))


def test_build_snapshot_is_resumable_and_publishes_verified_canonical_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _OfficialArchiveFixture()
    transport = httpx.MockTransport(fixture.handler)
    monkeypatch.setattr(snapshot, "_make_http_client", lambda: httpx.Client(transport=transport))
    root = tmp_path
    _pin_test_builder(root, monkeypatch)
    config_path = _write_config(root)
    output_dir = root / "data/top40/snapshot-v1"
    manifest_path = root / "tournament/top40/data_manifest.json"
    common_dir = root / "reports-top40/common"

    manifest = snapshot.build_snapshot(
        config_path, output_dir, manifest_path, common_dir, resume=True
    )

    assert snapshot.verify_snapshot_manifest(manifest_path) == manifest
    assert manifest["sources"]["rest_request_count"] == 0
    assert manifest["sources"]["mark_rest_request_count"] == 0
    assert (output_dir / "rest_provenance.jsonl").read_text() == ""
    assert (output_dir / "mark_rest_provenance.jsonl").read_text() == ""
    assert {entry["name"] for entry in manifest["files"]} == {
        "archive_provenance",
        "bars",
        "btc_daily_returns",
        "btc_regimes",
        "contract_metadata",
        "coverage",
        "exchange_info",
        "funding",
        "mark_prices",
        "membership",
        "mark_rest_provenance",
        "rest_provenance",
    }
    bars = pd.read_parquet(output_dir / "bars.parquet")
    assert bars["open_time"].min() == pd.Timestamp("2019-11-01", tz="UTC")
    assert bars["open_time"].max() < pd.Timestamp("2020-02-01", tz="UTC")
    membership = pd.read_parquet(output_dir / "membership.parquet")
    assert membership["reconstitution_time"].min() == pd.Timestamp("2019-12-30", tz="UTC")
    funding = pd.read_parquet(output_dir / "funding.parquet")
    jitter = funding["funding_time"] - funding["settlement_time"]
    assert (jitter == pd.Timedelta(milliseconds=5)).all()
    assert (funding["mark_time"] == funding["settlement_time"]).all()
    assert (funding["mark_time"] <= funding["funding_time"]).all()
    mark_prices = pd.read_parquet(output_dir / "mark_prices.parquet")
    assert set(mark_prices) == {"mark_time", "symbol", "mark_price"}
    assert (mark_prices["mark_time"].dt.hour % 8 == 0).all()
    first_admission = membership.groupby("symbol", observed=True)["reconstitution_time"].min()
    expected_mark_rows = sum(
        int(((bars["symbol"] == symbol) & (bars["open_time"] >= admitted_at)).sum())
        for symbol, admitted_at in first_admission.items()
    )
    assert len(mark_prices) == expected_mark_rows
    metadata = pd.read_parquet(output_dir / "contract_metadata.parquet")
    assert set(metadata["symbol"]) == {"AAAUSDT", "BTCUSDT"}

    btc = pd.read_csv(common_dir / "btc_daily_returns.csv")
    regimes = pd.read_csv(common_dir / "btc_regimes.csv")
    expected = pd.date_range("2020-01-01", "2020-01-31", freq="D", tz="UTC")
    assert list(pd.to_datetime(btc["date"], utc=True)) == list(expected)
    assert list(pd.to_datetime(regimes["date"], utc=True)) == list(expected)
    assert regimes["regime"].notna().all()

    downloads_before = sum(count for url, count in fixture.requests.items() if url.endswith(".zip"))
    archive_requests_before = sum(
        count for url, count in fixture.requests.items() if "data.binance.vision/data/" in url
    )
    snapshot.build_snapshot(config_path, output_dir, manifest_path, common_dir, resume=True)
    downloads_after = sum(count for url, count in fixture.requests.items() if url.endswith(".zip"))
    assert downloads_after == downloads_before
    archive_requests_after = sum(
        count for url, count in fixture.requests.items() if "data.binance.vision/data/" in url
    )
    assert archive_requests_after == archive_requests_before


def test_exact_required_mark_gap_uses_rest_and_binds_archive_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _OfficialArchiveFixture()
    mark_time = pd.Timestamp("2020-01-01T00:00:00Z")
    mark_time_ms = int(mark_time.timestamp() * 1000)
    fixture.remove_mark_archive_hour("AAAUSDT", mark_time)
    fixture.mark_rest_rows["AAAUSDT"] = [
        [
            mark_time_ms,
            "123.45",
            "124.00",
            "123.00",
            "123.75",
            "0",
            mark_time_ms + 3_600_000 - 1,
            "0",
            0,
            "0",
            "0",
            "0",
        ]
    ]
    monkeypatch.setattr(
        snapshot,
        "_make_http_client",
        lambda: httpx.Client(transport=httpx.MockTransport(fixture.handler)),
    )
    _pin_test_builder(tmp_path, monkeypatch)
    config_path = _write_config(tmp_path)
    output_dir = tmp_path / "data/top40/snapshot-v1"
    manifest_path = tmp_path / "tournament/top40/data_manifest.json"
    common_dir = tmp_path / "reports-top40/common"

    manifest = snapshot.build_snapshot(
        config_path, output_dir, manifest_path, common_dir, resume=True
    )

    lines = (output_dir / "mark_rest_provenance.jsonl").read_text().splitlines()
    assert len(lines) == manifest["sources"]["mark_rest_request_count"] == 1
    provenance = json.loads(lines[0])
    assert provenance["endpoint"] == ("https://fapi.binance.com/fapi/v1/markPriceKlines")
    assert provenance["params"] == {
        "symbol": "AAAUSDT",
        "interval": "1h",
        "startTime": str(mark_time_ms),
        "endTime": str(mark_time_ms),
        "limit": "1",
    }
    assert provenance["required_for"] == ["funding_floor", "risk_boundary"]
    assert (
        provenance["archive_sha256"]
        == hashlib.sha256(
            fixture.payloads[
                "data/futures/um/monthly/markPriceKlines/AAAUSDT/1h/AAAUSDT-1h-2020-01.zip"
            ]
        ).hexdigest()
    )
    raw_path = tmp_path / provenance["raw_path"]
    assert raw_path.read_bytes() == snapshot._canonical_rest_response(
        fixture.mark_rest_rows["AAAUSDT"]
    )
    assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == provenance["sha256"]
    assert snapshot.verify_snapshot_manifest(manifest_path) == manifest

    funding = pd.read_parquet(output_dir / "funding.parquet")
    funding_row = funding[funding["symbol"].eq("AAAUSDT") & funding["mark_time"].eq(mark_time)]
    assert funding_row["mark_price"].tolist() == [123.45]
    marks = pd.read_parquet(output_dir / "mark_prices.parquet")
    boundary_row = marks[marks["symbol"].eq("AAAUSDT") & marks["mark_time"].eq(mark_time)]
    assert boundary_row["mark_price"].tolist() == [123.45]

    requests_before = sum(
        count for url, count in fixture.requests.items() if "/fapi/v1/markPriceKlines?" in url
    )
    snapshot.build_snapshot(config_path, output_dir, manifest_path, common_dir, resume=True)
    requests_after = sum(
        count for url, count in fixture.requests.items() if "/fapi/v1/markPriceKlines?" in url
    )
    assert requests_after == requests_before + 1

    raw_path.write_bytes(raw_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="raw mark REST response missing/size mismatch"):
        snapshot.verify_snapshot_manifest(manifest_path)


def test_daily_mark_archive_precedes_rest_and_verifier_reparses_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _OfficialArchiveFixture()
    mark_time = pd.Timestamp("2020-01-01T00:00:00Z")
    mark_time_ms = int(mark_time.timestamp() * 1000)
    fixture.remove_mark_archive_hour("AAAUSDT", mark_time)
    daily_key = fixture.add_daily_mark_archive("AAAUSDT", mark_time, base=222.0)
    fixture.mark_rest_rows["AAAUSDT"] = [
        [
            mark_time_ms,
            "999.0",
            "1000.0",
            "998.0",
            "999.5",
            "0",
            mark_time_ms + 3_600_000 - 1,
            "0",
            0,
            "0",
            "0",
            "0",
        ]
    ]
    monkeypatch.setattr(
        snapshot,
        "_make_http_client",
        lambda: httpx.Client(transport=httpx.MockTransport(fixture.handler)),
    )
    _pin_test_builder(tmp_path, monkeypatch)
    config_path = _write_config(tmp_path)
    output_dir = tmp_path / "data/top40/snapshot-v1"
    manifest_path = tmp_path / "tournament/top40/data_manifest.json"

    manifest = snapshot.build_snapshot(
        config_path,
        output_dir,
        manifest_path,
        tmp_path / "reports-top40/common",
        resume=True,
    )

    assert manifest["sources"]["mark_rest_request_count"] == 0
    assert not any("/fapi/v1/markPriceKlines?" in url for url in fixture.requests)
    archive_rows = [
        json.loads(line)
        for line in (output_dir / "archive_provenance.jsonl").read_text().splitlines()
    ]
    daily_rows = [row for row in archive_rows if row["dataset"] == "mark_price_1h_daily"]
    assert len(daily_rows) == 1
    assert daily_rows[0]["date"] == "2020-01-01"
    assert daily_rows[0]["url"] == f"https://data.binance.vision/{daily_key}"
    marks = pd.read_parquet(output_dir / "mark_prices.parquet")
    assert marks.loc[
        marks["symbol"].eq("AAAUSDT") & marks["mark_time"].eq(mark_time),
        "mark_price",
    ].tolist() == [222.0]
    assert snapshot.verify_snapshot_manifest(manifest_path) == manifest

    raw_daily = tmp_path / daily_rows[0]["raw_path"]
    raw_daily.write_bytes(raw_daily.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="raw archive missing/size mismatch"):
        snapshot.verify_snapshot_manifest(manifest_path)


def test_daily_mark_archive_checksum_mismatch_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _OfficialArchiveFixture()
    mark_time = pd.Timestamp("2020-01-01T00:00:00Z")
    fixture.remove_mark_archive_hour("AAAUSDT", mark_time)
    daily_key = fixture.add_daily_mark_archive("AAAUSDT", mark_time, base=222.0)
    fixture.payloads[daily_key + ".CHECKSUM"] = f"{'0' * 64}  {Path(daily_key).name}\n".encode()
    monkeypatch.setattr(
        snapshot,
        "_make_http_client",
        lambda: httpx.Client(transport=httpx.MockTransport(fixture.handler)),
    )
    _pin_test_builder(tmp_path, monkeypatch)

    with pytest.raises(ValueError, match="Binance SHA-256 mismatch"):
        snapshot.build_snapshot(
            _write_config(tmp_path),
            tmp_path / "data/top40/snapshot-v1",
            tmp_path / "tournament/top40/data_manifest.json",
            tmp_path / "reports-top40/common",
            resume=True,
        )


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "exactly one response row"),
        (
            [
                [
                    1_577_840_400_000,
                    "100",
                    "101",
                    "99",
                    "100",
                    "0",
                    1_577_843_999_999,
                    "0",
                    0,
                    "0",
                    "0",
                    "0",
                ]
            ],
            "foreign requested time",
        ),
        (
            [
                [
                    1_577_836_800_000,
                    "100",
                    "101",
                    "99",
                    "100",
                    "0",
                    1_577_840_400_000,
                    "0",
                    0,
                    "0",
                    "0",
                    "0",
                ]
            ],
            "exact one-hour kline",
        ),
    ],
)
def test_mark_rest_rejects_missing_foreign_and_malformed_rows(
    payload: list[list[object]], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        snapshot._validate_mark_rest_payload(
            payload,
            requested_time_ms=1_577_836_800_000,
            limit=1,
        )


def test_mark_rest_acquisition_rejects_out_of_window_request(tmp_path: Path) -> None:
    with httpx.Client(transport=httpx.MockTransport(lambda _: httpx.Response(500))) as client:
        with pytest.raises(ValueError, match="outside the snapshot window"):
            snapshot._acquire_mark_rest_time(
                client,
                endpoint="https://fapi.binance.com/fapi/v1/markPriceKlines",
                symbol="AAAUSDT",
                mark_time=pd.Timestamp("2020-02-01", tz="UTC"),
                required_for=("risk_boundary",),
                archive_source={
                    "dataset": "mark_price_1h",
                    "symbol": "AAAUSDT",
                    "year_month": "2020-02",
                    "raw_path": "raw.zip",
                    "sha256": "0" * 64,
                },
                raw_dir=tmp_path / "raw",
                root=tmp_path,
                warmup_start=pd.Timestamp("2019-11-01", tz="UTC"),
                hard_end=pd.Timestamp("2020-02-01", tz="UTC"),
            )


def test_required_archive_gap_uses_rest_and_manifest_rehashes_every_response(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _OfficialArchiveFixture()
    fixture.remove_funding_archive("AAAUSDT", "2020-01")
    base = pd.Timestamp("2020-01-01T00:00:00.005Z")
    fixture.rest_events["AAAUSDT"] = [
        {
            "symbol": "AAAUSDT",
            "fundingTime": int(timestamp.timestamp() * 1000),
            "fundingRate": str(rate),
            "markPrice": "999999.0",
        }
        for timestamp, rate in (
            (base, 0.0002),
            (base + pd.Timedelta(hours=4), 0.0003),
            (base + pd.Timedelta(hours=12), 0.0004),
        )
    ]
    monkeypatch.setattr(
        snapshot,
        "_make_http_client",
        lambda: httpx.Client(transport=httpx.MockTransport(fixture.handler)),
    )
    _pin_test_builder(tmp_path, monkeypatch)
    config_path = _write_config(tmp_path)
    output_dir = tmp_path / "data/top40/snapshot-v1"
    manifest_path = tmp_path / "tournament/top40/data_manifest.json"
    stale_path = output_dir / "raw/funding_rate_rest/AAAUSDT/2020-01/page-0001.json"
    stale_path.parent.mkdir(parents=True)
    stale_path.write_bytes(b"interrupted-cache-must-not-be-trusted")

    manifest = snapshot.build_snapshot(
        config_path,
        output_dir,
        manifest_path,
        tmp_path / "reports-top40/common",
        resume=True,
    )

    rest_lines = (output_dir / "rest_provenance.jsonl").read_text().splitlines()
    assert len(rest_lines) == manifest["sources"]["rest_request_count"] == 1
    provenance = json.loads(rest_lines[0])
    assert provenance["endpoint"] == "https://fapi.binance.com/fapi/v1/fundingRate"
    assert provenance["params"]["symbol"] == "AAAUSDT"
    assert provenance["response_rows"] == 3
    assert stale_path.read_bytes() == snapshot._canonical_rest_response(
        fixture.rest_events["AAAUSDT"]
    )
    assert hashlib.sha256(stale_path.read_bytes()).hexdigest() == provenance["sha256"]
    assert any("no upstream SHA-256 sidecar" in item for item in manifest["limitations"])

    funding = pd.read_parquet(output_dir / "funding.parquet")
    rest_funding = funding[
        funding["symbol"].eq("AAAUSDT")
        & funding["funding_time"].ge(pd.Timestamp("2020-01-01", tz="UTC"))
        & funding["funding_time"].lt(pd.Timestamp("2020-02-01", tz="UTC"))
    ].sort_values("funding_time")
    assert rest_funding["funding_interval_hours"].iloc[-2:].tolist() == [4.0, 8.0]
    assert 999999.0 not in rest_funding["mark_price"].tolist()

    requests_before = sum(
        count for url, count in fixture.requests.items() if "/fapi/v1/fundingRate?" in url
    )
    snapshot.build_snapshot(
        config_path,
        output_dir,
        manifest_path,
        tmp_path / "reports-top40/common",
        resume=True,
    )
    requests_after = sum(
        count for url, count in fixture.requests.items() if "/fapi/v1/fundingRate?" in url
    )
    assert requests_after == requests_before + 1

    stale_path.write_bytes(stale_path.read_bytes() + b"tampered")
    with pytest.raises(ValueError, match="raw REST response missing/size mismatch"):
        snapshot.verify_snapshot_manifest(manifest_path)


def test_funding_rest_gap_paginates_deterministically_and_always_refetches(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(snapshot, "_FUNDING_REST_LIMIT", 2)
    base = pd.Timestamp("2020-01-01T00:00:00Z")
    payload = [
        {
            "symbol": "AAAUSDT",
            "fundingTime": int((base + pd.Timedelta(hours=hours)).timestamp() * 1000),
            "fundingRate": f"0.000{index}",
        }
        for index, hours in enumerate((0, 4, 12, 20), start=1)
    ]
    requested_params: list[dict[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        params = dict(request.url.params.multi_items())
        requested_params.append(params)
        start = int(params["startTime"])
        end = int(params["endTime"])
        rows = [row for row in payload if start <= int(row["fundingTime"]) <= end]
        return httpx.Response(200, json=rows[: int(params["limit"])])

    raw_dir = tmp_path / "raw"
    stale = raw_dir / "funding_rate_rest/AAAUSDT/2020-01/page-0001.json"
    stale.parent.mkdir(parents=True)
    stale.write_bytes(b"stale")
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        frame, provenance = snapshot._acquire_funding_rest_month(
            client,
            endpoint="https://fapi.binance.com/fapi/v1/fundingRate",
            symbol="AAAUSDT",
            year=2020,
            month=1,
            raw_dir=raw_dir,
            root=tmp_path,
            warmup_start=pd.Timestamp("2019-11-01", tz="UTC"),
            hard_end=pd.Timestamp("2020-02-01", tz="UTC"),
        )
        snapshot._acquire_funding_rest_month(
            client,
            endpoint="https://fapi.binance.com/fapi/v1/fundingRate",
            symbol="AAAUSDT",
            year=2020,
            month=1,
            raw_dir=raw_dir,
            root=tmp_path,
            warmup_start=pd.Timestamp("2019-11-01", tz="UTC"),
            hard_end=pd.Timestamp("2020-02-01", tz="UTC"),
        )

    assert len(frame) == 4
    assert frame["funding_interval_hours"].isna().all()
    assert [row["response_rows"] for row in provenance] == [2, 2, 0]
    assert [row["page"] for row in provenance] == [1, 2, 3]
    first_run = requested_params[:3]
    assert requested_params[3:] == first_run
    assert int(first_run[1]["startTime"]) == payload[1]["fundingTime"] + 1
    assert int(first_run[2]["startTime"]) == payload[3]["fundingTime"] + 1
    assert len({params["endTime"] for params in first_run}) == 1
    assert stale.read_bytes() == snapshot._canonical_rest_response(payload[:2])
    for row in provenance:
        raw_path = tmp_path / row["raw_path"]
        assert hashlib.sha256(raw_path.read_bytes()).hexdigest() == row["sha256"]
        assert pd.Timestamp(row["retrieved_at"]).tzinfo is not None


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ([], "missing funding REST event coverage"),
        (
            [
                {
                    "symbol": "AAAUSDT",
                    "fundingTime": int(pd.Timestamp("2020-02-01", tz="UTC").timestamp() * 1000),
                    "fundingRate": "0.0001",
                }
            ],
            "outside requested window",
        ),
        (
            [
                {
                    "symbol": "AAAUSDT",
                    "fundingTime": int(pd.Timestamp("2020-01-01", tz="UTC").timestamp() * 1000),
                    "fundingRate": "0.0001",
                },
                {
                    "symbol": "AAAUSDT",
                    "fundingTime": int(pd.Timestamp("2020-01-01", tz="UTC").timestamp() * 1000),
                    "fundingRate": "0.0002",
                },
            ],
            "strictly increasing",
        ),
    ],
)
def test_funding_rest_gap_rejects_missing_out_of_window_and_duplicate_rows(
    tmp_path: Path,
    payload: list[dict[str, object]],
    message: str,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match=message):
            snapshot._acquire_funding_rest_month(
                client,
                endpoint="https://fapi.binance.com/fapi/v1/fundingRate",
                symbol="AAAUSDT",
                year=2020,
                month=1,
                raw_dir=tmp_path / "raw",
                root=tmp_path,
                warmup_start=pd.Timestamp("2019-11-01", tz="UTC"),
                hard_end=pd.Timestamp("2020-02-01", tz="UTC"),
            )


def test_missing_funding_intervals_use_adjacent_events_and_reject_duplicates() -> None:
    funding = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(
                [
                    "2020-01-01T00:00:00Z",
                    "2020-01-01T04:00:00Z",
                    "2020-01-01T12:00:00Z",
                ]
            ),
            "symbol": "AAAUSDT",
            "funding_rate": [0.0001, 0.0002, 0.0003],
            "funding_interval_hours": [float("nan"), float("nan"), float("nan")],
        }
    )

    result = snapshot._derive_missing_funding_intervals(funding, symbol="AAAUSDT")

    assert result["funding_interval_hours"].tolist() == [4.0, 4.0, 8.0]
    with pytest.raises(ValueError, match="duplicate funding event"):
        snapshot._derive_missing_funding_intervals(
            pd.concat([funding, funding.iloc[[1]]], ignore_index=True),
            symbol="AAAUSDT",
        )


def test_verify_manifest_rehashes_retained_raw_archives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _OfficialArchiveFixture()
    monkeypatch.setattr(
        snapshot,
        "_make_http_client",
        lambda: httpx.Client(transport=httpx.MockTransport(fixture.handler)),
    )
    _pin_test_builder(tmp_path, monkeypatch)
    config_path = _write_config(tmp_path)
    output_dir = tmp_path / "data/top40/snapshot-v1"
    manifest_path = tmp_path / "tournament/top40/data_manifest.json"
    snapshot.build_snapshot(
        config_path,
        output_dir,
        manifest_path,
        tmp_path / "reports-top40/common",
    )
    first = json.loads((output_dir / "archive_provenance.jsonl").read_text().splitlines()[0])
    raw_path = tmp_path / first["raw_path"]
    raw_path.write_bytes(raw_path.read_bytes() + b"tampered")
    message = "raw archive missing/size mismatch|raw archive hash mismatch"
    with pytest.raises(ValueError, match=message):
        snapshot.verify_snapshot_manifest(manifest_path)


def test_checksum_mismatch_never_publishes_archive(tmp_path: Path) -> None:
    archive = snapshot._Archive(
        dataset="transaction_8h",
        symbol="BTCUSDT",
        year=2020,
        month=1,
        key="data/futures/um/monthly/klines/BTCUSDT/8h/BTCUSDT-8h-2020-01.zip",
        url="https://data.binance.vision/bad.zip",
        checksum_url="https://data.binance.vision/bad.zip.CHECKSUM",
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url).endswith(".CHECKSUM"):
            return httpx.Response(200, text=f"{'0' * 64}  {archive.filename}\n")
        return httpx.Response(200, content=b"not-the-declared-bytes")

    raw_dir = tmp_path / "raw"
    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ValueError, match="SHA-256 mismatch"):
            snapshot._acquire_archive(client, archive, raw_dir=raw_dir, root=tmp_path, resume=True)
    assert not (raw_dir / archive.dataset / archive.symbol / archive.filename).exists()


def test_funding_mark_join_requires_exact_floor_hour_and_subsecond_jitter() -> None:
    funding_time = pd.Timestamp("2020-01-01T00:00:00.005Z")
    funding = pd.DataFrame(
        {
            "funding_time": [funding_time],
            "symbol": ["BTCUSDT"],
            "funding_rate": [0.0001],
            "funding_interval_hours": [8],
        }
    )
    marks = pd.DataFrame(
        {
            "mark_time": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T01:00:00Z"]),
            "symbol": ["BTCUSDT", "BTCUSDT"],
            "mark_price": [100.0, 999.0],
        }
    )
    result = snapshot._attach_mark_prices(funding, marks)
    assert result.loc[0, "mark_price"] == 100.0
    assert result.loc[0, "settlement_time"] == pd.Timestamp("2020-01-01", tz="UTC")

    funding.loc[0, "funding_time"] = pd.Timestamp("2020-01-01T00:00:01Z")
    with pytest.raises(ValueError, match="sub-second hour boundaries"):
        snapshot._attach_mark_prices(funding, marks)


def test_boundary_mark_panel_requires_exact_mark_for_every_executable_member_bar() -> None:
    bars = pd.DataFrame(
        {
            "open_time": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T08:00:00Z"]),
            "symbol": ["AAAUSDT", "AAAUSDT"],
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": pd.to_datetime(["2019-12-30T00:00:00Z"]),
            "symbol": ["AAAUSDT"],
        }
    )
    marks = pd.DataFrame(
        {
            "mark_time": pd.to_datetime(["2020-01-01T00:00:00Z", "2020-01-01T08:00:00Z"]),
            "symbol": ["AAAUSDT", "AAAUSDT"],
            "mark_price": [200.0, 201.0],
        }
    )

    panel = snapshot._boundary_mark_prices(bars, marks, membership)
    assert panel["mark_price"].tolist() == [200.0, 201.0]
    with pytest.raises(ValueError, match="missing exact 8h boundary mark"):
        snapshot._boundary_mark_prices(bars, marks.iloc[:1], membership)


def test_pre_admission_bar_needs_no_risk_mark_and_remains_non_executable() -> None:
    bars = pd.DataFrame(
        {
            "open_time": pd.to_datetime(["2020-01-01T08:00:00Z", "2020-01-06T00:00:00Z"]),
            "symbol": ["AAAUSDT", "AAAUSDT"],
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": pd.to_datetime(["2020-01-06T00:00:00Z"]),
            "symbol": ["AAAUSDT"],
        }
    )
    marks = pd.DataFrame(
        {
            "mark_time": pd.to_datetime(["2020-01-06T00:00:00Z"]),
            "symbol": ["AAAUSDT"],
            "mark_price": [201.0],
        }
    )
    funding = pd.DataFrame(
        {
            "funding_time": pd.to_datetime([], utc=True),
            "symbol": pd.Series(dtype=str),
        }
    )

    reasons = snapshot._required_mark_reasons(
        bars,
        funding,
        membership,
        symbol="AAAUSDT",
    )
    assert reasons == {
        pd.Timestamp("2020-01-06T00:00:00Z"): ("risk_boundary",),
    }
    panel = snapshot._boundary_mark_prices(bars, marks, membership)
    assert panel[["mark_time", "symbol", "mark_price"]].to_dict(orient="records") == [
        {
            "mark_time": pd.Timestamp("2020-01-06T00:00:00Z"),
            "symbol": "AAAUSDT",
            "mark_price": 201.0,
        }
    ]


def test_funding_intervals_are_derived_before_pre_admission_events_are_filtered() -> None:
    raw = pd.DataFrame(
        {
            "funding_time": pd.to_datetime(["2020-01-05T16:00:00Z", "2020-01-06T00:00:00Z"]),
            "symbol": ["AAAUSDT", "AAAUSDT"],
            "funding_rate": [0.0001, 0.0002],
            "funding_interval_hours": [float("nan"), float("nan")],
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": pd.to_datetime(["2020-01-06T00:00:00Z"]),
            "symbol": ["AAAUSDT"],
        }
    )

    derived = snapshot._derive_missing_funding_intervals(raw, symbol="AAAUSDT")
    scoped = snapshot._funding_since_first_admission(
        derived,
        membership,
        symbol="AAAUSDT",
    )

    assert scoped["funding_time"].tolist() == [pd.Timestamp("2020-01-06T00:00:00Z")]
    assert scoped["funding_interval_hours"].tolist() == [8.0]


def test_manifest_verifier_rejects_canonical_pre_admission_funding(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture = _OfficialArchiveFixture()
    monkeypatch.setattr(
        snapshot,
        "_make_http_client",
        lambda: httpx.Client(transport=httpx.MockTransport(fixture.handler)),
    )
    _pin_test_builder(tmp_path, monkeypatch)
    config_path = _write_config(tmp_path)
    output_dir = tmp_path / "data/top40/snapshot-v1"
    manifest_path = tmp_path / "tournament/top40/data_manifest.json"
    snapshot.build_snapshot(
        config_path,
        output_dir,
        manifest_path,
        tmp_path / "reports-top40/common",
        resume=True,
    )
    funding_path = output_dir / "funding.parquet"
    funding = pd.read_parquet(funding_path)
    injected = funding.iloc[[0]].copy()
    injected["funding_time"] = pd.Timestamp("2019-11-01T00:00:00.005Z")
    injected["settlement_time"] = pd.Timestamp("2019-11-01T00:00:00Z")
    injected["mark_time"] = pd.Timestamp("2019-11-01T00:00:00Z")
    pd.concat([injected, funding], ignore_index=True).to_parquet(
        funding_path, index=False, compression="zstd"
    )
    manifest = json.loads(manifest_path.read_text())
    entry = next(item for item in manifest["files"] if item["name"] == "funding")
    entry["rows"] += 1
    entry["size"] = funding_path.stat().st_size
    entry["sha256"] = hashlib.sha256(funding_path.read_bytes()).hexdigest()
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    with pytest.raises(ValueError, match="pre-admission event"):
        snapshot.verify_snapshot_manifest(manifest_path)


def test_active_contract_requires_final_month_archive() -> None:
    archive = snapshot._Archive(
        dataset="transaction_8h",
        symbol="BTCUSDT",
        year=2020,
        month=1,
        key="key",
        url="https://data.binance.vision/key",
        checksum_url="https://data.binance.vision/key.CHECKSUM",
    )
    info = {"deliveryDate": 4_102_444_800_000}
    with pytest.raises(ValueError, match="lacks hard-end archive"):
        snapshot._require_active_hard_end_coverage(
            [archive], info, hard_end=pd.Timestamp("2020-03-01", tz="UTC")
        )


def test_funding_months_are_required_only_for_executable_weekly_membership() -> None:
    bars = pd.DataFrame(
        {
            "open_time": pd.to_datetime(
                [
                    "2020-01-06T00:00:00Z",
                    "2020-01-13T00:00:00Z",
                    "2020-03-02T00:00:00Z",
                ]
            ),
            "symbol": ["AAAUSDT", "AAAUSDT", "AAAUSDT"],
        }
    )
    membership = pd.DataFrame(
        {
            "reconstitution_time": pd.to_datetime(["2020-01-06T00:00:00Z", "2020-03-02T00:00:00Z"]),
            "symbol": ["AAAUSDT", "AAAUSDT"],
        }
    )

    result = snapshot._member_bar_months(
        bars,
        membership,
        symbol="AAAUSDT",
        evaluation_start=pd.Timestamp("2020-01-10", tz="UTC"),
    )

    assert result == {(2020, 3)}


def test_archive_only_composite_contracts_are_not_crypto_candidates() -> None:
    discovered = (
        "BTCUSDT",
        "DOTECOUSDT",
        "FOOTBALLUSDT",
        "DEFIUSDT",
    )

    result = snapshot._candidate_symbols(
        discovered,
        current={},
        hard_end=pd.Timestamp("2026-07-01", tz="UTC"),
    )

    assert result == ("BTCUSDT",)


def test_monthly_archive_bootstrap_first_supports_thirty_day_universe_on_february_3() -> None:
    times = pd.date_range("2020-01-01", "2020-02-10", freq="8h", inclusive="left", tz="UTC")
    bars = pd.DataFrame(
        {
            "open_time": times,
            "symbol": "BTCUSDT",
            "quote_volume": 1_000_000.0,
        }
    )
    metadata = pd.DataFrame(
        {
            "symbol": ["BTCUSDT"],
            "contract_type": ["PERPETUAL"],
            "quote_asset": ["USDT"],
            "margin_asset": ["USDT"],
            "is_crypto": [True],
            "onboard_date": pd.to_datetime(["2020-01-01T00:00:00Z"]),
            "delivery_date": [pd.NaT],
        }
    )
    universe = {"size": 40, "trailing_days": 30, "minimum_history_days": 30}

    with pytest.raises(ValueError, match="empty point-in-time universe"):
        snapshot._build_membership(
            bars,
            metadata,
            evaluation_start=pd.Timestamp("2020-01-27", tz="UTC"),
            hard_end=pd.Timestamp("2020-02-10", tz="UTC"),
            universe_config=universe,
        )

    membership = snapshot._build_membership(
        bars,
        metadata,
        evaluation_start=pd.Timestamp("2020-02-03", tz="UTC"),
        hard_end=pd.Timestamp("2020-02-10", tz="UTC"),
        universe_config=universe,
    )
    assert membership["reconstitution_time"].min() == pd.Timestamp("2020-02-03", tz="UTC")
