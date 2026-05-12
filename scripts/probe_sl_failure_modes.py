"""Reproduce the actual STOP_MARKET / TAKE_PROFIT_MARKET failure modes on testnet.

Walks through the same code path as OrderManager.open_trade on a single small
position, capturing every Binance error response so we can see exactly which
codes the engine has been silently swallowing.

Cleans up afterwards: cancels any orders left open, market-closes any position
this script opened.

Run via:
  source ~/.binance_testnet_env
  BINANCE_BASE_URL=https://testnet.binancefuture.com \
    uv run python scripts/probe_sl_failure_modes.py
"""

from __future__ import annotations

import json
import os
import sys

import httpx

from crypto_trade.live.auth_client import AuthenticatedBinanceClient

API_KEY = os.environ["BINANCE_API_KEY"]
API_SECRET = os.environ["BINANCE_API_SECRET"]
BASE = os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com")

SYMBOL = "BTCUSDT"
NOTIONAL_USD = 200.0  # tiny — small enough to abandon if cleanup fails


def err_body(exc: httpx.HTTPStatusError) -> str:
    """Pull Binance's response body out of the exception — what the engine swallows."""
    try:
        return json.dumps(exc.response.json())
    except Exception:
        return exc.response.text


def fetch_mark_price(c: AuthenticatedBinanceClient, symbol: str) -> float:
    r = httpx._client.Client(base_url=BASE).get(f"/fapi/v1/premiumIndex?symbol={symbol}")
    r.raise_for_status()
    return float(r.json()["markPrice"])


def main() -> int:
    c = AuthenticatedBinanceClient(API_KEY, API_SECRET, base_url=BASE)

    info = c.get_exchange_info()
    sinfo = next(s for s in info["symbols"] if s["symbol"] == SYMBOL)
    filt = {f["filterType"]: f for f in sinfo["filters"]}
    tick = float(filt["PRICE_FILTER"]["tickSize"])
    step = float(filt["LOT_SIZE"]["stepSize"])
    qty_prec = int(sinfo["quantityPrecision"])
    pct_up = float(filt["PERCENT_PRICE"]["multiplierUp"])
    pct_dn = float(filt["PERCENT_PRICE"]["multiplierDown"])

    mark = fetch_mark_price(c, SYMBOL)
    print(f"=== {SYMBOL} ===")
    print(f"  mark={mark}  tick={tick}  step={step}  qtyPrec={qty_prec}")
    print(f"  PERCENT_PRICE: dn={pct_dn} up={pct_up}")
    print(f"  Allowed price range: [{mark * pct_dn:.2f}, {mark * pct_up:.2f}]")
    print()

    qty = round(NOTIONAL_USD / mark, qty_prec)
    print(f"=== Entry: MARKET BUY {qty} {SYMBOL} (~${qty * mark:.2f}) ===")
    try:
        entry = c.place_market_order(SYMBOL, "BUY", qty)
        print(f"  OK: orderId={entry.get('orderId')}")
    except httpx.HTTPStatusError as exc:
        print(f"  FAIL: HTTP {exc.response.status_code} body={err_body(exc)}")
        return 1

    # Tests below — record every outcome so we can summarize at the end.
    results: list[tuple[str, str, str]] = []  # (label, status, detail)

    def try_sl(label: str, stop_price: float, **kwargs) -> str | None:
        # Round to tick — same algorithm as OrderManager._round_price.
        rounded = round(round(stop_price / tick) * tick, 8)
        sp_str = f"{rounded}"
        params = {
            "symbol": SYMBOL,
            "side": "SELL",
            "type": "STOP_MARKET",
            "stopPrice": sp_str,
        }
        params.update(kwargs)
        if "closePosition" not in params:
            params["quantity"] = f"{qty}"
            params["reduceOnly"] = "true"
        print(f"  -> {label}: stopPrice={sp_str} extra={kwargs}")
        try:
            resp = c._signed_post("/fapi/v1/order", params)
            print(f"     OK: orderId={resp.get('orderId')}")
            results.append((label, "OK", str(resp.get("orderId"))))
            return str(resp.get("orderId"))
        except httpx.HTTPStatusError as exc:
            body = err_body(exc)
            print(f"     FAIL: HTTP {exc.response.status_code} body={body}")
            results.append((label, "FAIL", body))
            return None

    placed_ids: list[str] = []

    print()
    print("=== SL failure-mode probes ===")
    placed_ids += filter(None, [try_sl(
        "A. baseline 4% below mark, reduceOnly+qty",
        mark * 0.96,
    )])
    placed_ids += filter(None, [try_sl(
        "B. 6% below mark — should hit PERCENT_PRICE",
        mark * 0.94,
    )])
    placed_ids += filter(None, [try_sl(
        "C. 4% below mark with closePosition=true (no qty/reduceOnly)",
        mark * 0.96,
        closePosition="true",
    )])
    placed_ids += filter(None, [try_sl(
        "D. 4% below mark with workingType=MARK_PRICE",
        mark * 0.96,
        workingType="MARK_PRICE",
    )])
    placed_ids += filter(None, [try_sl(
        "E. 1% above mark — would-immediately-trigger SELL",
        mark * 1.01,
    )])
    # F: invalid format (sci-notation) using deliberately small stop
    print(f"  -> F. literal sci-notation stopPrice='1e-05'")
    try:
        resp = c._signed_post(
            "/fapi/v1/order",
            {
                "symbol": SYMBOL,
                "side": "SELL",
                "type": "STOP_MARKET",
                "stopPrice": "1e-05",
                "quantity": f"{qty}",
                "reduceOnly": "true",
            },
        )
        print(f"     OK?? orderId={resp.get('orderId')}")
        results.append(("F", "OK", str(resp.get("orderId"))))
        placed_ids.append(str(resp.get("orderId")))
    except httpx.HTTPStatusError as exc:
        body = err_body(exc)
        print(f"     FAIL: HTTP {exc.response.status_code} body={body}")
        results.append(("F. sci-notation '1e-05'", "FAIL", body))

    # Cleanup
    print()
    print("=== Cleanup ===")
    for oid in placed_ids:
        try:
            c.cancel_order(SYMBOL, oid)
            print(f"  cancelled {oid}")
        except Exception as exc:
            print(f"  cancel {oid} failed: {exc}")
    try:
        c.cancel_all_orders(SYMBOL)
        print(f"  cancel_all OK")
    except Exception as exc:
        print(f"  cancel_all failed: {exc}")
    try:
        close = c.place_market_order(SYMBOL, "SELL", qty)
        print(f"  market-close OK: orderId={close.get('orderId')}")
    except Exception as exc:
        print(f"  market-close failed: {exc}")

    print()
    print("=== SUMMARY ===")
    for label, status, detail in results:
        print(f"  [{status}] {label}: {detail}")

    c.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
