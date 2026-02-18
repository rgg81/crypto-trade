import csv
import io
import zipfile

import httpx

from crypto_trade.bulk import (
    MonthlyArchive,
    bulk_fetch_symbol,
    compute_missing_months,
    download_and_extract,
    list_monthly_archives,
)
from crypto_trade.models import Kline
from crypto_trade.storage import csv_path, write_klines

S3_LISTING_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>false</IsTruncated>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip</Key>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-02.zip</Key>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-03.zip</Key>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip.CHECKSUM</Key>
  </Contents>
</ListBucketResult>
"""


def _make_kline(open_time: int) -> Kline:
    return Kline(
        open_time=open_time,
        open="42000.00",
        high="42500.50",
        low="41800.00",
        close="42300.25",
        volume="1234.567",
        close_time=open_time + 59999,
        quote_volume="52345678.90",
        trades=5000,
        taker_buy_volume="600.123",
        taker_buy_quote_volume="25345678.45",
    )


def _make_csv_row(open_time: int) -> list[str]:
    return [
        str(open_time),
        "42000.00",
        "42500.50",
        "41800.00",
        "42300.25",
        "1234.567",
        str(open_time + 59999),
        "52345678.90",
        "5000",
        "600.123",
        "25345678.45",
        "0",
    ]


def _make_zip(rows: list[list[str]], filename: str = "data.csv") -> bytes:
    """Create an in-memory ZIP file containing a CSV with the given rows."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        csv_buf = io.StringIO()
        writer = csv.writer(csv_buf)
        for row in rows:
            writer.writerow(row)
        zf.writestr(filename, csv_buf.getvalue())
    return buf.getvalue()


def test_list_monthly_archives():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=S3_LISTING_XML)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        archives = list_monthly_archives(http, "https://data.binance.vision", "BTCUSDT", "1m")

    # Should only pick .zip files, not .CHECKSUM
    assert len(archives) == 3
    assert archives[0].year == 2024
    assert archives[0].month == 1
    assert archives[0].symbol == "BTCUSDT"
    assert archives[0].interval == "1m"
    assert "BTCUSDT-1m-2024-01.zip" in archives[0].url
    assert archives[2].month == 3


def test_download_and_extract():
    rows = [_make_csv_row(1000), _make_csv_row(2000), _make_csv_row(3000)]
    zip_data = _make_zip(rows, "BTCUSDT-1m-2024-01.csv")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=zip_data)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        klines = download_and_extract(http, "https://example.com/test.zip")

    assert len(klines) == 3
    assert klines[0].open_time == 1000
    assert klines[2].open_time == 3000


def test_download_and_extract_empty_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("readme.txt", "no csv here")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=buf.getvalue())

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        klines = download_and_extract(http, "https://example.com/test.zip")

    assert klines == []


def test_compute_missing_months_no_existing_data(tmp_path):
    archives = [
        MonthlyArchive("BTCUSDT", "1m", 2024, 1, "url1"),
        MonthlyArchive("BTCUSDT", "1m", 2024, 2, "url2"),
    ]
    missing = compute_missing_months(tmp_path, "BTCUSDT", "1m", archives)
    assert len(missing) == 2


def test_compute_missing_months_with_existing_data(tmp_path):
    # Write klines up to end of January 2024
    # Feb 1 00:00 UTC 2024 = 1706745600000, so last kline at that boundary
    path = csv_path(tmp_path, "BTCUSDT", "1m")
    klines = [_make_kline(1706745600000)]
    write_klines(path, klines)

    archives = [
        MonthlyArchive("BTCUSDT", "1m", 2024, 1, "url1"),
        MonthlyArchive("BTCUSDT", "1m", 2024, 2, "url2"),
        MonthlyArchive("BTCUSDT", "1m", 2024, 3, "url3"),
    ]
    missing = compute_missing_months(tmp_path, "BTCUSDT", "1m", archives)
    # Jan should be skipped (its end < last_time), Feb and Mar should be missing
    assert len(missing) == 2
    assert missing[0].month == 2
    assert missing[1].month == 3


def test_bulk_fetch_symbol(tmp_path, monkeypatch):
    monkeypatch.setattr("crypto_trade.bulk.time.sleep", lambda _: None)

    rows_jan = [_make_csv_row(1000), _make_csv_row(2000)]
    rows_feb = [_make_csv_row(3000), _make_csv_row(4000)]
    zip_jan = _make_zip(rows_jan, "BTCUSDT-1m-2024-01.csv")
    zip_feb = _make_zip(rows_feb, "BTCUSDT-1m-2024-02.csv")

    listing_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>false</IsTruncated>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip</Key>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-02.zip</Key>
  </Contents>
</ListBucketResult>
"""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "BTCUSDT-1m-2024-01.zip" in url:
            return httpx.Response(200, content=zip_jan)
        elif "BTCUSDT-1m-2024-02.zip" in url:
            return httpx.Response(200, content=zip_feb)
        else:
            return httpx.Response(200, text=listing_xml)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        count = bulk_fetch_symbol(http, "https://data.binance.vision", tmp_path, "BTCUSDT", "1m")

    assert count == 4
    path = csv_path(tmp_path, "BTCUSDT", "1m")
    assert path.exists()


def test_bulk_fetch_symbol_skips_404(tmp_path, monkeypatch):
    monkeypatch.setattr("crypto_trade.bulk.time.sleep", lambda _: None)
    monkeypatch.setattr("crypto_trade.bulk.MAX_RETRIES", 1)

    listing_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>false</IsTruncated>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip</Key>
  </Contents>
</ListBucketResult>
"""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if ".zip" in url:
            return httpx.Response(404)
        return httpx.Response(200, text=listing_xml)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        count = bulk_fetch_symbol(http, "https://data.binance.vision", tmp_path, "BTCUSDT", "1m")

    assert count == 0


def test_download_and_extract_with_header():
    """CSVs with a header row (post-2021) should skip the header and parse data rows."""
    header = [
        "open_time", "open", "high", "low", "close", "volume",
        "close_time", "quote_volume", "trades",
        "taker_buy_volume", "taker_buy_quote_volume", "ignore",
    ]
    rows = [header, _make_csv_row(1000), _make_csv_row(2000)]
    zip_data = _make_zip(rows, "BTCUSDT-1m-2022-01.csv")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=zip_data)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        klines = download_and_extract(http, "https://example.com/test.zip")

    assert len(klines) == 2
    assert klines[0].open_time == 1000
    assert klines[1].open_time == 2000


def test_bulk_fetch_symbol_handles_bad_csv(tmp_path, monkeypatch):
    """A corrupt CSV in one archive should be counted as an error, not abort the symbol."""
    monkeypatch.setattr("crypto_trade.bulk.time.sleep", lambda _: None)

    # First archive has a corrupt row that will raise ValueError
    bad_rows = [["not_a_number", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x", "x"]]
    zip_bad = _make_zip(bad_rows, "BTCUSDT-1m-2024-01.csv")

    rows_feb = [_make_csv_row(3000), _make_csv_row(4000)]
    zip_feb = _make_zip(rows_feb, "BTCUSDT-1m-2024-02.csv")

    listing_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>false</IsTruncated>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-01.zip</Key>
  </Contents>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-02.zip</Key>
  </Contents>
</ListBucketResult>
"""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if "BTCUSDT-1m-2024-01.zip" in url:
            return httpx.Response(200, content=zip_bad)
        elif "BTCUSDT-1m-2024-02.zip" in url:
            return httpx.Response(200, content=zip_feb)
        else:
            return httpx.Response(200, text=listing_xml)

    transport = httpx.MockTransport(handler)
    progress = None
    with httpx.Client(transport=transport) as http:
        from crypto_trade.bulk import BulkProgress

        progress = BulkProgress()
        count = bulk_fetch_symbol(
            http, "https://data.binance.vision", tmp_path, "BTCUSDT", "1m",
            progress=progress,
        )

    # Bad archive counted as error, good archive still processed
    assert progress.errors == 1
    assert count == 2


def test_bulk_fetch_symbol_deduplicates(tmp_path, monkeypatch):
    """Doesn't write klines that already exist in the CSV."""
    monkeypatch.setattr("crypto_trade.bulk.time.sleep", lambda _: None)

    # Pre-populate with kline at time 2000
    path = csv_path(tmp_path, "BTCUSDT", "1m")
    existing = [_make_kline(1000), _make_kline(2000)]
    write_klines(path, existing)

    # Archive contains overlapping data (1000, 2000) plus new (3000)
    rows = [_make_csv_row(1000), _make_csv_row(2000), _make_csv_row(3000)]
    zip_data = _make_zip(rows, "BTCUSDT-1m-2024-03.csv")

    listing_xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <IsTruncated>false</IsTruncated>
  <Contents>
    <Key>data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2024-03.zip</Key>
  </Contents>
</ListBucketResult>
"""

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if ".zip" in url:
            return httpx.Response(200, content=zip_data)
        return httpx.Response(200, text=listing_xml)

    transport = httpx.MockTransport(handler)
    with httpx.Client(transport=transport) as http:
        count = bulk_fetch_symbol(http, "https://data.binance.vision", tmp_path, "BTCUSDT", "1m")

    # Only kline at 3000 should be written (1000, 2000 already exist)
    assert count == 1
