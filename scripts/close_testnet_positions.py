"""Close all positions + algo orders on Binance Futures testnet.

Workflow:
  1. Snapshot current positions + algo orders
  2. Cancel every open algo order (so SL/TP can't fire during close)
  3. Market-close every non-zero position (capture fill price)
  4. Verify clean state
  5. Update data/testnet.db open trades to status=closed,
     exit_reason='manual_close', exit_price=market_close fill,
     exit_time=now — so the DB matches the exchange and the live
     trade history is preserved for the comparison against the
     fresh backtests.

Run via:
  source ~/.binance_testnet_env
  BINANCE_BASE_URL=https://testnet.binancefuture.com \
    uv run python scripts/close_testnet_positions.py
"""

from __future__ import annotations

import json
import os
import sqlite3
import time

from crypto_trade.live.auth_client import AuthenticatedBinanceClient


def main() -> int:
    api_key = os.environ["BINANCE_API_KEY"]
    api_secret = os.environ["BINANCE_API_SECRET"]
    base = os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com")
    c = AuthenticatedBinanceClient(api_key, api_secret, base_url=base)

    # --- 1. Snapshot ---
    print("=" * 70)
    print("STEP 1 — SNAPSHOT")
    print("=" * 70)
    positions = [p for p in c.get_positions() if float(p.get("positionAmt", 0)) != 0]
    algos = c.get_open_algo_orders()
    print(f"Open positions: {len(positions)}")
    for p in positions:
        print(
            f"  {p['symbol']:9} amt={p['positionAmt']:>10} entry={p['entryPrice']:>12} "
            f"mark={p.get('markPrice', '?'):>12} uPnL={p.get('unRealizedProfit', '?')}"
        )
    print(f"Open algo orders: {len(algos)}")
    for a in algos:
        print(
            f"  algoId={a['algoId']} {a['orderType']:<22} {a['symbol']:9} "
            f"side={a['side']} trigger={a['triggerPrice']}"
        )
    if not positions and not algos:
        print("\nNothing to close. Exiting.")
        c.close()
        return 0

    # --- 2. Cancel algos ---
    print()
    print("=" * 70)
    print("STEP 2 — CANCEL ALGO ORDERS")
    print("=" * 70)
    for a in algos:
        try:
            c.cancel_algo_order(a["symbol"], str(a["algoId"]))
            print(f"  cancelled algoId={a['algoId']} on {a['symbol']}")
        except Exception as exc:
            print(f"  cancel algoId={a['algoId']} failed: {exc}")
    # Verify
    remaining_algos = c.get_open_algo_orders()
    print(f"  → remaining algo orders: {len(remaining_algos)}")

    # --- 3. Market-close positions ---
    print()
    print("=" * 70)
    print("STEP 3 — MARKET-CLOSE POSITIONS")
    print("=" * 70)
    close_results: dict[str, dict] = {}
    for p in positions:
        sym = p["symbol"]
        amt = float(p["positionAmt"])
        close_side = "SELL" if amt > 0 else "BUY"
        qty = abs(amt)
        try:
            resp = c.place_market_order(sym, close_side, qty)
            orderId = resp.get("orderId")
            print(f"  {sym:9} {close_side} {qty} → orderId={orderId}")
            close_results[sym] = {"orderId": orderId, "side": close_side, "qty": qty}
        except Exception as exc:
            print(f"  {sym} FAILED: {exc}")

    # Give Binance a moment to settle, then read back fill prices.
    time.sleep(2)
    print()
    print("  Fill prices:")
    for sym, info in close_results.items():
        try:
            order = c._signed_get("/fapi/v1/order", {"symbol": sym, "orderId": info["orderId"]})
            fill = float(order.get("avgPrice", 0))
            status = order.get("status")
            info["fill_price"] = fill
            info["update_time"] = int(order.get("updateTime", time.time() * 1000))
            print(f"  {sym:9} avgPrice={fill}  status={status}")
        except Exception as exc:
            print(f"  {sym} order lookup failed: {exc}")

    # --- 4. Verify clean exchange state ---
    print()
    print("=" * 70)
    print("STEP 4 — VERIFY CLEAN STATE")
    print("=" * 70)
    positions2 = [p for p in c.get_positions() if float(p.get("positionAmt", 0)) != 0]
    algos2 = c.get_open_algo_orders()
    print(f"Open positions: {len(positions2)}")
    print(f"Open algo orders: {len(algos2)}")
    acct = c.get_account()
    print(
        f"Wallet: {acct.get('totalWalletBalance')} total, "
        f"{acct.get('availableBalance')} available, "
        f"uPnL={acct.get('totalUnrealizedProfit')}"
    )

    # --- 5. Update DB ---
    print()
    print("=" * 70)
    print("STEP 5 — UPDATE LOCAL testnet.db (mark open trades closed)")
    print("=" * 70)
    con = sqlite3.connect("data/testnet.db")
    cur = con.cursor()
    cur.execute(
        """SELECT id, model_name, symbol, direction, entry_price, entry_order_id
           FROM trades WHERE status = 'open'"""
    )
    open_rows = cur.fetchall()
    print(f"DB has {len(open_rows)} open trades:")
    for r in open_rows:
        print(f"  {r}")

    updated = 0
    for tid, model, sym, direction, entry_price, eid in open_rows:
        info = close_results.get(sym)
        if info is None:
            print(f"  SKIP {sym} (no close result)")
            continue
        fill = info.get("fill_price")
        update_time = info.get("update_time", int(time.time() * 1000))
        if not fill:
            print(f"  SKIP {sym} (no fill price)")
            continue
        cur.execute(
            """UPDATE trades
               SET status = 'closed', exit_price = ?, exit_time = ?,
                   exit_reason = 'manual_close'
               WHERE id = ? AND status = 'open'""",
            (fill, update_time, tid),
        )
        if cur.rowcount > 0:
            updated += 1
            print(f"  closed {model:8} {sym:9} dir={direction:+d} fill={fill}")
    con.commit()
    print(f"  → {updated} rows updated")

    # Final state
    print()
    print("=== FINAL DB STATE ===")
    cur.execute("SELECT status, COUNT(*) FROM trades GROUP BY status")
    for r in cur.fetchall():
        print(f"  {r}")
    con.close()
    c.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
