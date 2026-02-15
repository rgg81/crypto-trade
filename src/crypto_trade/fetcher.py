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
    incrementally. Returns the number of new klines written.
    """
    path = csv_path(data_dir, symbol, interval)
    last_time = read_last_open_time(path)

    effective_start = start_time
    append = False
    if last_time is not None:
        # Resume from after the last known kline
        effective_start = last_time + 1
        append = True

    klines = client.fetch_klines(symbol, interval, start_time=effective_start)
    if not klines:
        return 0

    return write_klines(path, klines, append=append)


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
