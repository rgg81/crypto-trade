"""Data pipeline for live trading: kline fetch → feature generation → master DF.

Keeps kline CSVs and feature Parquet files current so LightGbmStrategy
can read up-to-date features via its standard Parquet-based lookup.
"""

from __future__ import annotations

import logging
from pathlib import Path

from crypto_trade.backtest import build_master as build_master  # noqa: F401 (re-export)
from crypto_trade.client import BinanceClient
from crypto_trade.fetcher import fetch_symbol_interval
from crypto_trade.models import Kline

log = logging.getLogger(__name__)


def refresh_klines(
    client: BinanceClient,
    symbols: list[str],
    interval: str,
    data_dir: Path,
) -> dict[str, int]:
    """Incrementally fetch latest klines for each symbol, appending to CSV.

    Returns {symbol: n_new_klines}.
    """
    result: dict[str, int] = {}
    for symbol in symbols:
        n = fetch_symbol_interval(client, data_dir, symbol, interval)
        result[symbol] = n
    return result


def refresh_features(
    symbols: list[str],
    interval: str,
    data_dir: str,
    features_dir: str,
    groups: list[str],
    output_format: str = "parquet",
) -> None:
    """Regenerate feature files for the given symbols."""
    from crypto_trade.features import list_groups, run_features

    # Expand "all" to actual group names (same as CLI does)
    if groups == ["all"]:
        groups = list_groups()

    run_features(
        symbols=symbols,
        interval=interval,
        data_dir=data_dir,
        groups=groups,
        start_ms=None,
        end_ms=None,
        output_dir=features_dir,
        workers=1,
        output_format=output_format,
    )


def detect_new_candle(
    client: BinanceClient,
    symbol: str,
    interval: str,
    last_processed_open_time: int | None,
) -> Kline | None:
    """Poll Binance for the latest closed candle.

    Returns the last closed candle if its open_time differs from
    last_processed_open_time, else None.
    """
    klines = client.fetch_klines(symbol, interval, start_time=None, end_time=None)
    if len(klines) < 2:
        return None

    closed = klines[-2]
    if last_processed_open_time is not None and closed.open_time == last_processed_open_time:
        return None
    return closed
