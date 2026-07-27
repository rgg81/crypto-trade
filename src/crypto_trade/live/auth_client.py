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


_TIME_OFFSET_TTL_S = 300  # how long a cached serverTime offset stays valid


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
        self._time_offset_ms = 0.0  # serverTime - localTime; see _refresh_time_offset
        self._time_offset_at = 0.0

        client_kwargs: dict = {
            "base_url": base_url,
            "headers": {"X-MBX-APIKEY": api_key},
        }
        if transport is not None:
            client_kwargs["transport"] = transport
        self._client = httpx.Client(**client_kwargs)

    def _refresh_time_offset(self, force: bool = False) -> None:
        """Cache (serverTime - localTime) so signed requests survive host clock drift.

        Binance rejects any signed request whose timestamp is >1000ms AHEAD of server time
        (-1021); recvWindow only widens the BEHIND tolerance, so it cannot help. A host clock
        running fast therefore blocks every signed call — order placement included — while
        unsigned endpoints keep working, which makes it look like a network problem rather than
        a clock one. Observed on this deployment 2026-07-27: WSL sat +1.34s ahead because the
        Windows Time service was never synced, and re-syncing inside WSL was undone within ~40s.

        Offset is measured mid-flight (local clock sampled either side of the request) so network
        latency isn't baked in as skew. Called on demand from _signed() when Binance rejects a
        timestamp, and at most once per _TIME_OFFSET_TTL_S otherwise. When the host clock is
        correct this never runs and signing behaviour is unchanged.
        """
        now = time.time()
        if not force and self._time_offset_at and now - self._time_offset_at < _TIME_OFFSET_TTL_S:
            return
        try:
            t0 = time.time() * 1000
            resp = self._client.get("/fapi/v1/time", timeout=10)
            resp.raise_for_status()
            t1 = time.time() * 1000
            server = float(resp.json()["serverTime"])
            self._time_offset_ms = server - (t0 + t1) / 2
            self._time_offset_at = now
        except Exception:
            # Keep the previous offset (0.0 if never established) — a failed probe must never
            # break signing; the request will simply use the uncorrected clock as before.
            self._time_offset_at = now

    def _sign(self, params: dict) -> dict:
        """Append timestamp, recvWindow, and HMAC-SHA256 signature."""
        params["timestamp"] = int(time.time() * 1000 + self._time_offset_ms)
        params["recvWindow"] = self._recv_window
        query = urlencode(params)
        signature = hmac.new(self._api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = signature
        return params

    def _signed(self, method: str, path: str, params: dict | None = None) -> dict | list:
        """Issue a signed request, re-syncing the clock offset once on -1021.

        Reactive rather than proactive: the happy path costs no extra round-trip, and the
        offset probe only runs when Binance has actually rejected our timestamp. Retrying is
        safe for orders too — -1021 is rejected at the gateway before matching, so nothing was
        placed. Only ONE retry, so a persistently-wrong clock surfaces as an error rather than
        looping.
        """
        base = dict(params or {})
        for attempt in (0, 1):
            resp = self._client.request(method, path, params=self._sign(dict(base)))
            if attempt == 0 and resp.status_code >= 400 and self._is_timestamp_error(resp):
                self._refresh_time_offset(force=True)
                continue
            _raise_with_body(resp)
            return resp.json()
        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def _is_timestamp_error(resp: httpx.Response) -> bool:
        try:
            return int(resp.json().get("code", 0)) == -1021
        except Exception:
            return False

    def _signed_get(self, path: str, params: dict | None = None) -> dict | list:
        return self._signed("GET", path, params)

    def _signed_post(self, path: str, params: dict | None = None) -> dict:
        return self._signed("POST", path, params)  # type: ignore[return-value]

    def _signed_delete(self, path: str, params: dict | None = None) -> dict:
        return self._signed("DELETE", path, params)  # type: ignore[return-value]

    def place_market_order(
        self, symbol: str, side: str, quantity: float, reduce_only: bool = False
    ) -> dict:
        params = {
            "symbol": symbol,
            "side": side,
            "type": "MARKET",
            "quantity": f"{quantity}",
        }
        if reduce_only:
            params["reduceOnly"] = "true"  # only reduces an existing position
        return self._signed_post("/fapi/v1/order", params)

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

    def get_income(
        self, income_type: str | None = None, start_time: int | None = None, limit: int = 1000
    ) -> list:
        """Account income history (/fapi/v1/income) — REALIZED_PNL, FUNDING_FEE, COMMISSION, etc.

        Read-only. Used by the PnL-attribution digest. Empty income_type returns all types.
        """
        params: dict = {"limit": limit}
        if income_type:
            params["incomeType"] = income_type
        if start_time is not None:
            params["startTime"] = start_time
        return self._signed_get("/fapi/v1/income", params)

    def get_user_trades(self, symbol: str, start_time: int | None = None, limit: int = 500) -> list:
        """Account trade fills for a symbol (/fapi/v1/userTrades) — executed price + commission.

        Read-only. Used by the fill-quality / slippage check. Futures requires a per-symbol query.
        """
        params: dict = {"symbol": symbol, "limit": limit}
        if start_time is not None:
            params["startTime"] = start_time
        return self._signed_get("/fapi/v1/userTrades", params)

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
