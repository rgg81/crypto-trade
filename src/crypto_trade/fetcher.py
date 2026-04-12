import time
from pathlib import Path

from crypto_trade.client import BinanceClient
from crypto_trade.storage import csv_path, read_last_open_time, write_klines


def fetch_symbol_interval(
    client: BinanceClient,
    data_dir: Path,
    symbol: str,
    interval: str,
    start_time: int | None = None,
) -> int:
    """Fetch klines for one symbol/interval pair and append to CSV.

    Reads the last open_time from the existing CSV to resume
    incrementally. Only CLOSED klines are written — the currently
    forming candle (close_time > now) is dropped so it never
    contaminates the CSV with stale mid-candle values.

    Returns the number of new klines written.
    """
    path = csv_path(data_dir, symbol, interval)
    last_time = read_last_open_time(path)

    effective_start = start_time
    append = False
    if last_time is not None:
        effective_start = last_time + 1
        append = True

    klines = client.fetch_klines(symbol, interval, start_time=effective_start)
    if not klines:
        return 0

    now_ms = int(time.time() * 1000)
    closed = [k for k in klines if k.close_time < now_ms]
    if not closed:
        return 0

    return write_klines(path, closed, append=append)


def fetch_all(
    client: BinanceClient,
    data_dir: Path,
    symbols: tuple[str, ...],
    intervals: tuple[str, ...],
    start_time: int | None = None,
) -> dict[str, int]:
    """Fetch klines for all symbol/interval combinations.

    Returns a dict mapping "SYMBOL/interval" to the count of new klines.
    """
    results: dict[str, int] = {}
    for symbol in symbols:
        for interval in intervals:
            key = f"{symbol}/{interval}"
            count = fetch_symbol_interval(client, data_dir, symbol, interval, start_time)
            results[key] = count
    return results
