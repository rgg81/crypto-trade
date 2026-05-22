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


def _raise_with_body(resp: httpx.Response) -> None:
    """Raise like ``raise_for_status`` but include Binance's response body in the message.

    Binance returns ``{"code": -XXXX, "msg": "..."}`` on 4xx; the default
    ``HTTPStatusError`` strips that, which makes order rejections undebuggable.
    """
    if resp.is_success:
        return
    body = resp.text
    raise httpx.HTTPStatusError(
        f"{resp.status_code} {resp.reason_phrase} for {resp.request.method} "
        f"{resp.request.url.path}: {body}",
        request=resp.request,
        response=resp,
    )


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
        _raise_with_body(resp)
        return resp.json()

    def _signed_post(self, path: str, params: dict | None = None) -> dict:
        params = self._sign(params or {})
        resp = self._client.post(path, params=params)
        _raise_with_body(resp)
        return resp.json()

    def _signed_delete(self, path: str, params: dict | None = None) -> dict:
        params = self._sign(params or {})
        resp = self._client.delete(path, params=params)
        _raise_with_body(resp)
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

    # --- Algo (conditional) orders -----------------------------------------
    # As of 2025-12-09 Binance USDⓈ-M Futures conditional order types
    # (STOP_MARKET, TAKE_PROFIT_MARKET, STOP, TAKE_PROFIT, TRAILING_STOP_MARKET)
    # are placed/cancelled/queried on a separate Algo Service. Sending them
    # to /fapi/v1/order returns code -4120.
    #
    # Endpoints:
    #   POST   /fapi/v1/algoOrder          — place
    #   DELETE /fapi/v1/algoOrder          — cancel
    #   GET    /fapi/v1/algoOrder          — query single
    #   GET    /fapi/v1/openAlgoOrders     — list active
    #
    # The trigger price field is `triggerPrice`, not `stopPrice`. Status
    # field is `algoStatus` (NEW / TRIGGERED / FINISHED / CANCELED / EXPIRED);
    # the resulting market-order ID lands in `actualOrderId` and the fill
    # price in `actualPrice` once `algoStatus ∈ {TRIGGERED, FINISHED}`.

    def _place_algo_conditional(
        self,
        symbol: str,
        side: str,
        order_type: str,
        trigger_price: float,
        quantity: float,
        reduce_only: bool,
    ) -> dict:
        params: dict = {
            "algoType": "CONDITIONAL",
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "triggerPrice": f"{trigger_price}",
            "quantity": f"{quantity}",
        }
        if reduce_only:
            params["reduceOnly"] = "true"
        return self._signed_post("/fapi/v1/algoOrder", params)

    def place_algo_stop_market_order(
        self,
        symbol: str,
        side: str,
        trigger_price: float,
        quantity: float,
        reduce_only: bool = True,
    ) -> dict:
        return self._place_algo_conditional(
            symbol, side, "STOP_MARKET", trigger_price, quantity, reduce_only
        )

    def place_algo_take_profit_market_order(
        self,
        symbol: str,
        side: str,
        trigger_price: float,
        quantity: float,
        reduce_only: bool = True,
    ) -> dict:
        return self._place_algo_conditional(
            symbol, side, "TAKE_PROFIT_MARKET", trigger_price, quantity, reduce_only
        )

    def cancel_algo_order(self, symbol: str, algo_id: str) -> dict:
        return self._signed_delete(
            "/fapi/v1/algoOrder",
            {"symbol": symbol, "algoId": algo_id},
        )

    def get_algo_order(self, symbol: str, algo_id: str) -> dict:
        return self._signed_get(
            "/fapi/v1/algoOrder",
            {"symbol": symbol, "algoId": algo_id},
        )

    def get_open_algo_orders(self, symbol: str | None = None) -> list:
        params: dict = {}
        if symbol:
            params["symbol"] = symbol
        return self._signed_get("/fapi/v1/openAlgoOrders", params)

    # --- Regular (non-conditional) orders ---------------------------------

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
