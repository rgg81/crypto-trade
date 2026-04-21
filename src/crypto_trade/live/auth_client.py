"""Authenticated Binance Futures USD-M client.

Extends the existing httpx pattern from client.py with HMAC-SHA256 signing
for private endpoints (orders, positions, account). Injectable transport
for test mocking.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from urllib.parse import urlencode

import httpx


class AuthenticatedBinanceClient:
    """HTTP client for authenticated Binance Futures endpoints."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        base_url: str = "https://fapi.binance.com",
        rate_limit_pause: float = 0.25,
        recv_window: int = 5000,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._api_secret = api_secret
        self._base_url = base_url
        self._rate_limit_pause = rate_limit_pause
        self._recv_window = recv_window
        self._transport = transport

        client_kwargs: dict = {
            "base_url": base_url,
            "headers": {"X-MBX-APIKEY": api_key},
        }
        if transport is not None:
            client_kwargs["transport"] = transport
        self._client = httpx.Client(**client_kwargs)

    def _sign(self, params: dict) -> dict:
        """Append timestamp, recvWindow, and HMAC-SHA256 signature."""
        params["timestamp"] = int(time.time() * 1000)
        params["recvWindow"] = self._recv_window
        query = urlencode(params)
        signature = hmac.new(self._api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return params

    def _signed_get(self, path: str, params: dict | None = None) -> dict | list:
        params = self._sign(params or {})
        resp = self._client.get(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def _signed_post(self, path: str, params: dict | None = None) -> dict:
        params = self._sign(params or {})
        resp = self._client.post(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def _signed_delete(self, path: str, params: dict | None = None) -> dict:
        params = self._sign(params or {})
        resp = self._client.delete(path, params=params)
        resp.raise_for_status()
        return resp.json()

    def place_market_order(self, symbol: str, side: str, quantity: float) -> dict:
        return self._signed_post(
            "/fapi/v1/order",
            {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": f"{quantity}",
            },
        )

    def _place_conditional_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        stop_price: float,
        quantity: float,
        reduce_only: bool = True,
    ) -> dict:
        """Place STOP_MARKET or TAKE_PROFIT_MARKET order."""
        params: dict = {
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "stopPrice": f"{stop_price}",
            "quantity": f"{quantity}",
        }
        if reduce_only:
            params["reduceOnly"] = "true"
        return self._signed_post("/fapi/v1/order", params)

    def place_stop_market_order(
        self,
        symbol: str,
        side: str,
        stop_price: float,
        quantity: float,
        reduce_only: bool = True,
    ) -> dict:
        return self._place_conditional_order(
            symbol, side, "STOP_MARKET", stop_price, quantity, reduce_only
        )

    def place_take_profit_market_order(
        self,
        symbol: str,
        side: str,
        stop_price: float,
        quantity: float,
        reduce_only: bool = True,
    ) -> dict:
        return self._place_conditional_order(
            symbol, side, "TAKE_PROFIT_MARKET", stop_price, quantity, reduce_only
        )

    def cancel_order(self, symbol: str, order_id: str) -> dict:
        return self._signed_delete(
            "/fapi/v1/order",
            {"symbol": symbol, "orderId": order_id},
        )

    def cancel_all_orders(self, symbol: str) -> dict:
        return self._signed_delete(
            "/fapi/v1/allOpenOrders",
            {"symbol": symbol},
        )

    def get_order(self, symbol: str, order_id: str) -> dict:
        return self._signed_get(
            "/fapi/v1/order",
            {"symbol": symbol, "orderId": order_id},
        )

    def get_open_orders(self, symbol: str | None = None) -> list:
        params: dict = {}
        if symbol:
            params["symbol"] = symbol
        return self._signed_get("/fapi/v1/openOrders", params)

    def get_positions(self, symbol: str | None = None) -> list:
        params: dict = {}
        if symbol:
            params["symbol"] = symbol
        return self._signed_get("/fapi/v3/positionRisk", params)

    def get_balance(self) -> list:
        return self._signed_get("/fapi/v3/balance")

    def get_account(self) -> dict:
        return self._signed_get("/fapi/v3/account")

    def set_leverage(self, symbol: str, leverage: int) -> dict:
        return self._signed_post(
            "/fapi/v1/leverage",
            {"symbol": symbol, "leverage": leverage},
        )

    def get_exchange_info(self) -> dict:
        resp = self._client.get("/fapi/v1/exchangeInfo")
        resp.raise_for_status()
        return resp.json()

    def close(self) -> None:
        self._client.close()
