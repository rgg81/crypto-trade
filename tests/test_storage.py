from crypto_trade.models import Kline
from crypto_trade.storage import csv_path, read_klines, read_last_open_time, write_klines


def _make_kline(open_time: int = 1704067200000) -> Kline:
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


def test_csv_path(tmp_path):
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    assert path == tmp_path / "BTCUSDT" / "1h.csv"


def test_read_last_open_time_no_file(tmp_path):
    path = tmp_path / "nonexistent.csv"
    assert read_last_open_time(path) is None


def test_write_and_read_klines(tmp_path):
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    klines = [_make_kline(1000), _make_kline(2000)]
    count = write_klines(path, klines)
    assert count == 2
    result = read_klines(path)
    assert len(result) == 2
    assert result[0] == klines[0]
    assert result[1] == klines[1]


def test_write_empty_list(tmp_path):
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    count = write_klines(path, [])
    assert count == 0
    assert not path.exists()


def test_read_last_open_time(tmp_path):
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    klines = [_make_kline(1000), _make_kline(2000), _make_kline(3000)]
    write_klines(path, klines)
    assert read_last_open_time(path) == 3000


def test_append_mode(tmp_path):
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    batch1 = [_make_kline(1000), _make_kline(2000)]
    write_klines(path, batch1)
    batch2 = [_make_kline(3000), _make_kline(4000)]
    write_klines(path, batch2, append=True)
    result = read_klines(path)
    assert len(result) == 4
    assert result[0].open_time == 1000
    assert result[3].open_time == 4000


def test_read_klines_no_file(tmp_path):
    path = tmp_path / "missing.csv"
    assert read_klines(path) == []


def test_read_last_open_time_header_only(tmp_path):
    """Header-only CSV returns None."""
    path = csv_path(tmp_path, "BTCUSDT", "1h")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(",".join(Kline.CSV_HEADER) + "\n")
    assert read_last_open_time(path) is None
