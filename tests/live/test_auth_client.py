import hashlib
import hmac as hmac_mod
from urllib.parse import parse_qs, urlencode

import httpx
import pytest

from crypto_trade.live.auth_client import AuthenticatedBinanceClient

API_KEY = "test_api_key_123"
API_SECRET = "test_api_secret_456"


def _capture_transport():
    """Returns (transport, captured_requests) where captured_requests is a list."""
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"orderId": "12345", "status": "NEW"})

    return httpx.MockTransport(handler), captured


def _make_client(transport=None):
    if transport is None:
        transport, _ = _capture_transport()
    return AuthenticatedBinanceClient(
        api_key=API_KEY,
        api_secret=API_SECRET,
        transport=transport,
    )


class TestSigning:
    def test_signature_is_valid_hmac_sha256(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.place_market_order("BTCUSDT", "BUY", 0.001)

        req = captured[0]
        params = dict(parse_qs(str(req.url.params)))
        # parse_qs returns lists; flatten
        flat = {k: v[0] for k, v in params.items()}

        assert "signature" in flat
        assert "timestamp" in flat
        assert "recvWindow" in flat

        # Verify signature: reconstruct query without signature, compute HMAC
        sig = flat.pop("signature")
        query = urlencode(flat)
        expected = hmac_mod.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
        assert sig == expected

    def test_api_key_header(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.get_balance()

        req = captured[0]
        assert req.headers["X-MBX-APIKEY"] == API_KEY


class TestMarketOrder:
    def test_place_market_order_params(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.place_market_order("BTCUSDT", "BUY", 0.001)

        req = captured[0]
        assert req.method == "POST"
        assert "/fapi/v1/order" in str(req.url)
        params = dict(parse_qs(str(req.url.params)))
        assert params["symbol"] == ["BTCUSDT"]
        assert params["side"] == ["BUY"]
        assert params["type"] == ["MARKET"]
        assert params["quantity"] == ["0.001"]


class TestAlgoConditionalOrders:
    """SL/TP are placed via /fapi/v1/algoOrder with algoType=CONDITIONAL.

    The legacy /fapi/v1/order endpoint returns -4120 for STOP_MARKET /
    TAKE_PROFIT_MARKET as of 2025-12-09.
    """

    def test_stop_market_order_via_algo_endpoint(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.place_algo_stop_market_order("BTCUSDT", "SELL", 57600.0, 0.001)

        req = captured[0]
        assert req.method == "POST"
        assert "/fapi/v1/algoOrder" in str(req.url)
        params = dict(parse_qs(str(req.url.params)))
        assert params["algoType"] == ["CONDITIONAL"]
        assert params["type"] == ["STOP_MARKET"]
        assert params["triggerPrice"] == ["57600.0"]
        assert params["quantity"] == ["0.001"]
        assert params["reduceOnly"] == ["true"]

    def test_take_profit_market_order_via_algo_endpoint(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.place_algo_take_profit_market_order("BTCUSDT", "SELL", 64800.0, 0.001)

        req = captured[0]
        assert "/fapi/v1/algoOrder" in str(req.url)
        params = dict(parse_qs(str(req.url.params)))
        assert params["algoType"] == ["CONDITIONAL"]
        assert params["type"] == ["TAKE_PROFIT_MARKET"]
        assert params["triggerPrice"] == ["64800.0"]
        assert params["reduceOnly"] == ["true"]

    def test_cancel_algo_order(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.cancel_algo_order("BTCUSDT", "1000000066764087")

        req = captured[0]
        assert req.method == "DELETE"
        assert "/fapi/v1/algoOrder" in str(req.url)
        params = dict(parse_qs(str(req.url.params)))
        assert params["symbol"] == ["BTCUSDT"]
        assert params["algoId"] == ["1000000066764087"]

    def test_get_algo_order(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.get_algo_order("BTCUSDT", "1000000066764087")

        req = captured[0]
        assert req.method == "GET"
        assert "/fapi/v1/algoOrder" in str(req.url)
        params = dict(parse_qs(str(req.url.params)))
        assert params["algoId"] == ["1000000066764087"]

    def test_get_open_algo_orders(self):
        def handler(request):
            return httpx.Response(200, json=[])

        client = _make_client(httpx.MockTransport(handler))
        result = client.get_open_algo_orders("BTCUSDT")
        assert result == []


class TestQueryEndpoints:
    def test_cancel_order(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.cancel_order("BTCUSDT", "12345")

        req = captured[0]
        assert req.method == "DELETE"
        params = dict(parse_qs(str(req.url.params)))
        assert params["symbol"] == ["BTCUSDT"]
        assert params["orderId"] == ["12345"]

    def test_get_positions(self):
        def handler(request):
            return httpx.Response(200, json=[{"symbol": "BTCUSDT", "positionAmt": "0.001"}])

        transport = httpx.MockTransport(handler)
        client = _make_client(transport)
        positions = client.get_positions("BTCUSDT")
        assert len(positions) == 1
        assert positions[0]["symbol"] == "BTCUSDT"

    def test_set_leverage(self):
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.set_leverage("BTCUSDT", 5)

        req = captured[0]
        assert req.method == "POST"
        params = dict(parse_qs(str(req.url.params)))
        assert params["symbol"] == ["BTCUSDT"]
        assert params["leverage"] == ["5"]

    def test_get_exchange_info_no_auth(self):
        """Exchange info is public — should not have signature."""
        transport, captured = _capture_transport()
        client = _make_client(transport)
        client.get_exchange_info()

        req = captured[0]
        assert req.method == "GET"
        assert "signature" not in str(req.url)


class TestErrorHandling:
    def test_http_error_raised(self):
        def handler(request):
            return httpx.Response(400, json={"code": -1102, "msg": "Bad request"})

        transport = httpx.MockTransport(handler)
        client = _make_client(transport)

        with pytest.raises(httpx.HTTPStatusError):
            client.place_market_order("BTCUSDT", "BUY", 0.001)

    def test_http_error_includes_response_body(self):
        """Exception message must include Binance's response body so order rejections
        (-4120, -2021, -1111, etc.) are diagnosable instead of being silently swallowed."""

        def handler(request):
            return httpx.Response(
                400,
                json={"code": -4120, "msg": "Order type not supported for this endpoint."},
            )

        client = _make_client(httpx.MockTransport(handler))

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            client.place_algo_stop_market_order("BTCUSDT", "SELL", 95.0, 0.001)

        msg = str(exc_info.value)
        assert "-4120" in msg
        assert "Order type not supported" in msg
