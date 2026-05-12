"""Find which endpoint+payload Binance Futures testnet now accepts for STOP_MARKET / TAKE_PROFIT_MARKET.

Tries several known/likely endpoints and parameter combinations against a tiny
real position, captures every error body.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import httpx

API_KEY = os.environ["BINANCE_API_KEY"]
API_SECRET = os.environ["BINANCE_API_SECRET"]
BASE = os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
SYMBOL = "BTCUSDT"


def sign(params: dict) -> dict:
    params["timestamp"] = int(time.time() * 1000)
    params["recvWindow"] = 5000
    q = urlencode(params)
    sig = hmac.new(API_SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()
    params["signature"] = sig
    return params


def post(path: str, params: dict) -> tuple[int, str]:
    """Return (status_code, body_text) — never raises."""
    p = sign(dict(params))
    r = httpx.post(
        f"{BASE}{path}",
        params=p,
        headers={"X-MBX-APIKEY": API_KEY},
        timeout=10.0,
    )
    return r.status_code, r.text


def get(path: str, params: dict | None = None) -> tuple[int, str]:
    p = sign(dict(params or {}))
    r = httpx.get(
        f"{BASE}{path}",
        params=p,
        headers={"X-MBX-APIKEY": API_KEY},
        timeout=10.0,
    )
    return r.status_code, r.text


def public_get(path: str, params: dict | None = None) -> tuple[int, str]:
    r = httpx.get(f"{BASE}{path}", params=params, timeout=10.0)
    return r.status_code, r.text


def main() -> int:
    # Mark price for sizing
    sc, body = public_get("/fapi/v1/premiumIndex", {"symbol": SYMBOL})
    mark = float(json.loads(body)["markPrice"])
    print(f"=== {SYMBOL} mark={mark} ===")

    # Open a tiny long position so reduceOnly orders make sense
    qty = round(200.0 / mark, 4)
    sc, body = post("/fapi/v1/order", {
        "symbol": SYMBOL, "side": "BUY", "type": "MARKET", "quantity": f"{qty}",
    })
    if sc != 200:
        print(f"Entry failed: {sc} {body}")
        return 1
    entry_id = json.loads(body)["orderId"]
    print(f"Entry OK: orderId={entry_id} qty={qty}")
    print()

    sl_price = round(round(mark * 0.97 / 0.1) * 0.1, 8)
    sl_str = f"{sl_price}"

    placed_ids: list[str] = []
    results: list[tuple[str, int, str]] = []

    def try_call(label: str, path: str, params: dict) -> None:
        print(f"-> {label}")
        print(f"   path={path}  params={params}")
        sc, body = post(path, params)
        print(f"   HTTP {sc}: {body}")
        results.append((label, sc, body))
        if sc == 200:
            try:
                oid = json.loads(body).get("orderId") or json.loads(body).get("algoId")
                if oid:
                    placed_ids.append((path, str(oid)))
            except Exception:
                pass

    # 1. Standard endpoint with full params (current code path)
    try_call("1. /fapi/v1/order STOP_MARKET reduceOnly+qty", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP_MARKET",
        "stopPrice": sl_str, "quantity": f"{qty}", "reduceOnly": "true",
    })

    # 2. Add timeInForce
    try_call("2. /fapi/v1/order STOP_MARKET +timeInForce=GTC", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP_MARKET",
        "stopPrice": sl_str, "quantity": f"{qty}", "reduceOnly": "true",
        "timeInForce": "GTC",
    })

    # 3. closePosition only (no qty/reduceOnly)
    try_call("3. /fapi/v1/order STOP_MARKET closePosition", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP_MARKET",
        "stopPrice": sl_str, "closePosition": "true",
    })

    # 4. workingType=MARK_PRICE + closePosition
    try_call("4. /fapi/v1/order STOP_MARKET closePosition+MARK_PRICE", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP_MARKET",
        "stopPrice": sl_str, "closePosition": "true", "workingType": "MARK_PRICE",
    })

    # 5. STOP (limit-trigger) instead of STOP_MARKET
    sl_limit = round(round((mark * 0.97 - 0.5) / 0.1) * 0.1, 8)
    try_call("5. /fapi/v1/order STOP (LIMIT)", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP",
        "stopPrice": sl_str, "price": f"{sl_limit}", "quantity": f"{qty}",
        "reduceOnly": "true", "timeInForce": "GTC",
    })

    # 6. /fapi/v2/order ? (probably 404/405 but worth trying)
    try_call("6. /fapi/v2/order STOP_MARKET", "/fapi/v2/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP_MARKET",
        "stopPrice": sl_str, "quantity": f"{qty}", "reduceOnly": "true",
    })

    # 7. /fapi/v1/algo/futures/newOrder ? (algo order endpoint guess)
    try_call("7. /fapi/v1/algo/futures/newOrder STOP_MARKET", "/fapi/v1/algo/futures/newOrder", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP_MARKET",
        "stopPrice": sl_str, "quantity": f"{qty}", "reduceOnly": "true",
    })

    # 8. /papi/v1/algo/futures/newOrder ? (portfolio margin algo endpoint)
    try_call("8. /papi/v1/algo/futures/newOrder", "/papi/v1/algo/futures/newOrder", {
        "symbol": SYMBOL, "side": "SELL", "type": "STOP_MARKET",
        "stopPrice": sl_str, "quantity": f"{qty}", "reduceOnly": "true",
    })

    # 9. TRAILING_STOP_MARKET (different conditional type)
    try_call("9. /fapi/v1/order TRAILING_STOP_MARKET", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "TRAILING_STOP_MARKET",
        "callbackRate": "1.0", "quantity": f"{qty}", "reduceOnly": "true",
    })

    # 10. TAKE_PROFIT_MARKET (parallel test for TP)
    tp_price = round(round(mark * 1.03 / 0.1) * 0.1, 8)
    try_call("10. /fapi/v1/order TAKE_PROFIT_MARKET reduceOnly+qty", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "TAKE_PROFIT_MARKET",
        "stopPrice": f"{tp_price}", "quantity": f"{qty}", "reduceOnly": "true",
    })

    # 11. LIMIT order (not conditional) — sanity that auth+endpoint work fine
    far_price = round(round(mark * 0.50 / 0.1) * 0.1, 8)
    try_call("11. SANITY /fapi/v1/order LIMIT BUY far below", "/fapi/v1/order", {
        "symbol": SYMBOL, "side": "BUY", "type": "LIMIT",
        "price": f"{far_price}", "quantity": f"{qty}", "timeInForce": "GTC",
    })

    # Cleanup
    print()
    print("=== Cleanup ===")
    for path, oid in placed_ids:
        # Try cancel on whichever endpoint accepted it
        cancel_path = "/fapi/v1/order" if "fapi" in path else path.replace("newOrder", "cancelOrder")
        sc, body = post(cancel_path, {"symbol": SYMBOL, "orderId": oid})
        print(f"  cancel via {cancel_path} {oid}: {sc} {body[:100]}")
    sc, body = post("/fapi/v1/allOpenOrders", {"symbol": SYMBOL})
    print(f"  cancel_all: {sc} {body[:100]}")
    # Manually craft DELETE for cancel_all (allOpenOrders is DELETE)
    p = sign({"symbol": SYMBOL})
    r = httpx.delete(
        f"{BASE}/fapi/v1/allOpenOrders",
        params=p,
        headers={"X-MBX-APIKEY": API_KEY},
        timeout=10.0,
    )
    print(f"  DELETE allOpenOrders: {r.status_code} {r.text[:100]}")

    sc, body = post("/fapi/v1/order", {
        "symbol": SYMBOL, "side": "SELL", "type": "MARKET", "quantity": f"{qty}",
    })
    print(f"  market-close: {sc} {body[:120]}")

    print()
    print("=== SUMMARY ===")
    for label, sc, body in results:
        ok = "OK  " if sc == 200 else "FAIL"
        print(f"  [{ok} {sc}] {label}")
        if sc != 200:
            print(f"        body: {body[:160]}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
