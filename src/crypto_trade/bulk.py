"""Bulk download engine for kline data from data.binance.vision."""

import csv
import io
import time
import zipfile
from collections.abc import Callable
from dataclasses import dataclass
from xml.etree import ElementTree

import httpx

from crypto_trade.models import Kline
from crypto_trade.storage import csv_path, read_last_open_time, write_klines

S3_BUCKET_URL = "https://s3-ap-northeast-1.amazonaws.com/data.binance.vision"
S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

MAX_RETRIES = 3
RETRY_BACKOFF = 2.0


@dataclass(frozen=True)
class MonthlyArchive:
    """Metadata for a monthly kline archive on data.binance.vision."""

    symbol: str
    interval: str
    year: int
    month: int
    url: str


@dataclass
class BulkProgress:
    """Progress state for bulk download."""

    total_symbols: int = 0
    current_symbol_index: int = 0
    current_symbol: str = ""
    current_interval: str = ""
    total_months: int = 0
    current_month: int = 0
    total_klines: int = 0
    errors: int = 0


def list_monthly_archives(
    http: httpx.Client,
    data_vision_base: str,
    symbol: str,
    interval: str,
) -> list[MonthlyArchive]:
    """List available monthly ZIP archives for a symbol/interval from S3."""
    prefix = f"data/futures/um/monthly/klines/{symbol}/{interval}/"
    archives: list[MonthlyArchive] = []
    marker = ""

    while True:
        params: dict[str, str] = {
            "prefix": prefix,
            "delimiter": "/",
        }
        if marker:
            params["marker"] = marker

        resp = _request_with_retry(http, S3_BUCKET_URL, params=params)
        root = ElementTree.fromstring(resp.text)

        for key_elem in root.findall(".//s3:Contents/s3:Key", S3_NS):
            key = key_elem.text or ""
            if key.endswith(".zip"):
                archive = _parse_archive_key(key, symbol, interval, data_vision_base)
                if archive:
                    archives.append(archive)

        is_truncated = root.findtext("s3:IsTruncated", namespaces=S3_NS)
        if is_truncated != "true":
            break

        next_marker = root.findtext("s3:NextMarker", namespaces=S3_NS)
        if next_marker:
            marker = next_marker
        else:
            keys = [e.text or "" for e in root.findall(".//s3:Contents/s3:Key", S3_NS)]
            if keys:
                marker = keys[-1]
            else:
                break

    return sorted(archives, key=lambda a: (a.year, a.month))


def _parse_archive_key(
    key: str, symbol: str, interval: str, data_vision_base: str
) -> MonthlyArchive | None:
    """Parse an S3 key into a MonthlyArchive."""
    # Key: data/futures/um/monthly/klines/BTCUSDT/1m/BTCUSDT-1m-2020-01.zip
    filename = key.rsplit("/", 1)[-1]
    # filename: BTCUSDT-1m-2020-01.zip
    name = filename.removesuffix(".zip")
    parts = name.split("-")
    if len(parts) < 4:
        return None
    try:
        year = int(parts[-2])
        month = int(parts[-1])
    except ValueError:
        return None
    url = f"{data_vision_base}/{key}"
    return MonthlyArchive(symbol=symbol, interval=interval, year=year, month=month, url=url)


def download_and_extract(http: httpx.Client, url: str) -> list[Kline]:
    """Download a ZIP archive and extract klines from the CSV inside."""
    resp = _request_with_retry(http, url)
    buf = io.BytesIO(resp.content)

    with zipfile.ZipFile(buf) as zf:
        csv_names = [n for n in zf.namelist() if n.endswith(".csv")]
        if not csv_names:
            return []

        klines: list[Kline] = []
        for csv_name in csv_names:
            with zf.open(csv_name) as f:
                text = io.TextIOWrapper(f, encoding="utf-8")
                reader = csv.reader(text)
                for row in reader:
                    if len(row) >= 11:
                        klines.append(Kline.from_csv_row(row))

    return klines


def compute_missing_months(
    data_dir, symbol: str, interval: str, archives: list[MonthlyArchive]
) -> list[MonthlyArchive]:
    """Determine which monthly archives still need to be downloaded.

    Compares available archives against the last open_time in the local CSV.
    Archives whose entire month falls before or at the last known kline are skipped.
    """
    path = csv_path(data_dir, symbol, interval)
    last_time = read_last_open_time(path)

    if last_time is None:
        return list(archives)

    missing: list[MonthlyArchive] = []
    for archive in archives:
        # Compute end of this archive's month as a rough timestamp
        if archive.month == 12:
            end_year, end_month = archive.year + 1, 1
        else:
            end_year, end_month = archive.year, archive.month + 1

        import datetime

        month_end = datetime.datetime(end_year, end_month, 1, tzinfo=datetime.UTC)
        month_end_ms = int(month_end.timestamp() * 1000) - 1

        if month_end_ms > last_time:
            missing.append(archive)

    return missing


def bulk_fetch_symbol(
    http: httpx.Client,
    data_vision_base: str,
    data_dir,
    symbol: str,
    interval: str,
    rate_pause: float = 0.1,
    progress_cb: Callable[[BulkProgress], None] | None = None,
    progress: BulkProgress | None = None,
) -> int:
    """Download all available monthly archives for one symbol/interval.

    Returns total kline count written.
    """
    archives = list_monthly_archives(http, data_vision_base, symbol, interval)
    missing = compute_missing_months(data_dir, symbol, interval, archives)

    if progress:
        progress.total_months = len(missing)

    path = csv_path(data_dir, symbol, interval)
    last_time = read_last_open_time(path)
    total_written = 0

    for i, archive in enumerate(missing):
        if progress:
            progress.current_month = i + 1
            if progress_cb:
                progress_cb(progress)

        try:
            klines = download_and_extract(http, archive.url)
        except (httpx.HTTPStatusError, zipfile.BadZipFile) as exc:
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code == 404:
                continue
            if progress:
                progress.errors += 1
            continue

        if not klines:
            continue

        # Deduplicate: filter out klines we already have
        if last_time is not None:
            klines = [k for k in klines if k.open_time > last_time]

        if not klines:
            continue

        # Sort by open_time to ensure correct order
        klines.sort(key=lambda k: k.open_time)

        append = path.exists()
        count = write_klines(path, klines, append=append)
        total_written += count
        last_time = klines[-1].open_time

        if progress:
            progress.total_klines += count

        time.sleep(rate_pause)

    return total_written


def bulk_fetch_all(
    http: httpx.Client,
    data_vision_base: str,
    data_dir,
    symbols: list[str],
    intervals: list[str],
    rate_pause: float = 0.1,
    progress_cb: Callable[[BulkProgress], None] | None = None,
) -> dict[str, int]:
    """Bulk download all symbol/interval combinations.

    Returns a dict mapping "SYMBOL/interval" to kline counts.
    Does not abort on per-symbol failures.
    """
    progress = BulkProgress(total_symbols=len(symbols))
    results: dict[str, int] = {}

    for sym_idx, symbol in enumerate(symbols):
        progress.current_symbol_index = sym_idx + 1
        progress.current_symbol = symbol

        for interval in intervals:
            progress.current_interval = interval
            progress.current_month = 0
            progress.total_months = 0

            key = f"{symbol}/{interval}"
            try:
                count = bulk_fetch_symbol(
                    http,
                    data_vision_base,
                    data_dir,
                    symbol,
                    interval,
                    rate_pause=rate_pause,
                    progress_cb=progress_cb,
                    progress=progress,
                )
                results[key] = count
            except Exception:
                progress.errors += 1
                results[key] = 0

    return results


def _request_with_retry(http: httpx.Client, url: str, params: dict | None = None) -> httpx.Response:
    """Make an HTTP GET request with retry on 429/5xx."""
    for attempt in range(MAX_RETRIES):
        resp = http.get(url, params=params)
        if resp.status_code == 429 or resp.status_code >= 500:
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_BACKOFF * (attempt + 1))
                continue
        resp.raise_for_status()
        return resp
    # Should not reach here, but just in case
    resp.raise_for_status()
    return resp
