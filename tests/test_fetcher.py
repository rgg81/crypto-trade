from unittest.mock import MagicMock

from crypto_trade.fetcher import fetch_all, fetch_symbol_interval
from crypto_trade.models import Kline
from crypto_trade.storage import csv_path, write_klines


def _make_kline(open_time: int) -> Kline:
    return Kline(
        open_time=open_time,
        open="42000.00",
        high="42500.50",
        low="41800.00",
        close="42300.25",
        volume="1234.567",
        close_time=open_time + 3599999,
        quote_volume="52345678.90",
        trades=5000,
        taker_buy_volume="600.123",
        taker_buy_quote_volume="25345678.45",
    )


def test_fetch_symbol_interval_fresh(tmp_path):
    """Fetches from start_time when no CSV exists."""
    client = MagicMock()
    client.fetch_klines.return_value = [_make_kline(1000), _make_kline(2000)]

    count = fetch_symbol_interval(client, tmp_path, "BTCUSDT", "1h", start_time=1000)
    assert count == 2
    client.fetch_klines.assert_called_once_with("BTCUSDT", "1h", start_time=1000)

    # Verify file was written
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    assert path.exists()


def test_fetch_symbol_interval_incremental(tmp_path):
    """Resumes from last open_time in existing CSV."""
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    existing = [_make_kline(1000), _make_kline(2000)]
    write_klines(path, existing)

    client = MagicMock()
    client.fetch_klines.return_value = [_make_kline(3000)]

    count = fetch_symbol_interval(client, tmp_path, "BTCUSDT", "1h", start_time=1000)
    assert count == 1
    # Should resume from 2001 (last open_time + 1)
    client.fetch_klines.assert_called_once_with("BTCUSDT", "1h", start_time=2001)


def test_fetch_symbol_interval_no_new_data(tmp_path):
    """Returns 0 when API returns empty."""
    client = MagicMock()
    client.fetch_klines.return_value = []

    count = fetch_symbol_interval(client, tmp_path, "BTCUSDT", "1h")
    assert count == 0


def test_fetch_all(tmp_path):
    """Fetches all symbol/interval combinations."""
    client = MagicMock()
    client.fetch_klines.return_value = [_make_kline(1000)]

    results = fetch_all(
        client,
        tmp_path,
        symbols=("BTCUSDT", "ETHUSDT"),
        intervals=("1h", "15m"),
        start_time=1000,
    )
    assert len(results) == 4
    assert results["BTCUSDT/1h"] == 1
    assert results["ETHUSDT/15m"] == 1
    assert client.fetch_klines.call_count == 4
