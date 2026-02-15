import httpx
import pytest

from crypto_trade.client import BinanceClient


def _make_raw_kline(open_time: int) -> list:
    return [
        open_time,
        "42000.00",
        "42500.50",
        "41800.00",
        "42300.25",
        "1234.567",
        open_time + 3599999,
        "52345678.90",
        5000,
        "600.123",
        "25345678.45",
        "0",
    ]


def _mock_transport(responses: list[list[list]]) -> httpx.MockTransport:
    """Create a MockTransport that returns successive responses."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        if call_count < len(responses):
            data = responses[call_count]
            call_count += 1
        else:
            data = []
        return httpx.Response(200, json=data)

    return httpx.MockTransport(handler)


def test_single_page():
    """Fetches a single page when batch < limit."""
    raw = [_make_raw_kline(1000), _make_raw_kline(2000)]
    transport = _mock_transport([raw])
    client = BinanceClient(limit=1500, transport=transport)
    klines = client.fetch_klines("BTCUSDT", "1h")
    assert len(klines) == 2
    assert klines[0].open_time == 1000
    assert klines[1].open_time == 2000


def test_multi_page(monkeypatch):
    """Paginates when batch == limit."""
    monkeypatch.setattr("crypto_trade.client.time.sleep", lambda _: None)
    page1 = [_make_raw_kline(1000), _make_raw_kline(2000)]
    page2 = [_make_raw_kline(3000)]  # less than limit -> stop
    transport = _mock_transport([page1, page2])
    client = BinanceClient(limit=2, transport=transport)
    klines = client.fetch_klines("BTCUSDT", "1h", start_time=1000)
    assert len(klines) == 3
    assert klines[-1].open_time == 3000


def test_empty_response():
    """Returns empty list when API returns no data."""
    transport = _mock_transport([[]])
    client = BinanceClient(transport=transport)
    klines = client.fetch_klines("BTCUSDT", "1h")
    assert klines == []


def test_http_error():
    """Raises on HTTP error status."""

    def error_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"msg": "rate limited"})

    transport = httpx.MockTransport(error_handler)
    client = BinanceClient(transport=transport)
    with pytest.raises(httpx.HTTPStatusError):
        client.fetch_klines("BTCUSDT", "1h")


def test_params_include_start_and_end():
    """Verifies startTime and endTime are passed as query params."""
    captured_params: list[dict] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured_params.append(dict(request.url.params))
        return httpx.Response(200, json=[])

    transport = httpx.MockTransport(handler)
    client = BinanceClient(limit=1500, transport=transport)
    client.fetch_klines("BTCUSDT", "1h", start_time=5000, end_time=9000)
    assert captured_params[0]["startTime"] == "5000"
    assert captured_params[0]["endTime"] == "9000"
    assert captured_params[0]["limit"] == "1500"
