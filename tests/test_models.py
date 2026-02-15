import pytest

from crypto_trade.models import Kline

RAW_API_RESPONSE = [
    1704067200000,  # open_time
    "42000.00",  # open
    "42500.50",  # high
    "41800.00",  # low
    "42300.25",  # close
    "1234.567",  # volume
    1704070799999,  # close_time
    "52345678.90",  # quote_volume
    5000,  # trades
    "600.123",  # taker_buy_volume
    "25345678.45",  # taker_buy_quote_volume
    "0",  # unused "ignore" field
]


def test_from_api_parses_correctly():
    kline = Kline.from_api(RAW_API_RESPONSE)
    assert kline.open_time == 1704067200000
    assert kline.open == "42000.00"
    assert kline.high == "42500.50"
    assert kline.low == "41800.00"
    assert kline.close == "42300.25"
    assert kline.volume == "1234.567"
    assert kline.close_time == 1704070799999
    assert kline.quote_volume == "52345678.90"
    assert kline.trades == 5000
    assert kline.taker_buy_volume == "600.123"
    assert kline.taker_buy_quote_volume == "25345678.45"


def test_to_row_returns_string_list():
    kline = Kline.from_api(RAW_API_RESPONSE)
    row = kline.to_row()
    assert len(row) == 11
    assert all(isinstance(v, str) for v in row)
    assert row[0] == "1704067200000"
    assert row[8] == "5000"


def test_round_trip():
    """from_api -> to_row -> from_api produces the same kline."""
    original = Kline.from_api(RAW_API_RESPONSE)
    row = original.to_row()
    # Simulate reading back: row is list[str], same positional order
    restored = Kline(
        open_time=int(row[0]),
        open=row[1],
        high=row[2],
        low=row[3],
        close=row[4],
        volume=row[5],
        close_time=int(row[6]),
        quote_volume=row[7],
        trades=int(row[8]),
        taker_buy_volume=row[9],
        taker_buy_quote_volume=row[10],
    )
    assert restored == original


def test_immutability():
    kline = Kline.from_api(RAW_API_RESPONSE)
    with pytest.raises(AttributeError):
        kline.open = "99999.00"


def test_csv_header_matches_field_count():
    kline = Kline.from_api(RAW_API_RESPONSE)
    assert len(Kline.CSV_HEADER) == len(kline.to_row())


RAW_CSV_ROW = [
    "1704067200000",
    "42000.00",
    "42500.50",
    "41800.00",
    "42300.25",
    "1234.567",
    "1704070799999",
    "52345678.90",
    "5000",
    "600.123",
    "25345678.45",
    "0",  # unused ignore field (12th column)
]


def test_from_csv_row_parses_correctly():
    kline = Kline.from_csv_row(RAW_CSV_ROW)
    assert kline.open_time == 1704067200000
    assert kline.open == "42000.00"
    assert kline.high == "42500.50"
    assert kline.low == "41800.00"
    assert kline.close == "42300.25"
    assert kline.volume == "1234.567"
    assert kline.close_time == 1704070799999
    assert kline.quote_volume == "52345678.90"
    assert kline.trades == 5000
    assert kline.taker_buy_volume == "600.123"
    assert kline.taker_buy_quote_volume == "25345678.45"


def test_from_csv_row_matches_from_api():
    """from_csv_row and from_api produce identical Kline for equivalent data."""
    from_api = Kline.from_api(RAW_API_RESPONSE)
    from_csv = Kline.from_csv_row(RAW_CSV_ROW)
    assert from_api == from_csv


def test_from_csv_row_round_trip():
    """from_csv_row -> to_row -> from_csv_row produces the same kline."""
    original = Kline.from_csv_row(RAW_CSV_ROW)
    row = original.to_row()
    restored = Kline.from_csv_row(row)
    assert restored == original
