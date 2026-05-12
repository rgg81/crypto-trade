"""End-to-end test of OrderManager.open_trade against Binance Futures testnet.

Exercises the patched code path: places a real entry + SL + TP triple via the
new algo endpoint, verifies the algo orders show up in /fapi/v1/openAlgoOrders,
then cleans up (cancels SL/TP, market-closes the entry).

Pass criterion: OrderManager.open_trade returns successfully and the SL/TP
algoIds are present in the open-algo-orders list.

Run via:
  source ~/.binance_testnet_env
  BINANCE_BASE_URL=https://testnet.binancefuture.com \
    uv run python scripts/probe_open_trade_e2e.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

from crypto_trade.backtest_models import Signal
from crypto_trade.live.auth_client import AuthenticatedBinanceClient
from crypto_trade.live.models import LiveConfig
from crypto_trade.live.order_manager import OrderManager
from crypto_trade.live.state_store import StateStore

API_KEY = os.environ["BINANCE_API_KEY"]
API_SECRET = os.environ["BINANCE_API_SECRET"]
BASE = os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com")

SYMBOL = "BTCUSDT"


def main() -> int:
    auth = AuthenticatedBinanceClient(API_KEY, API_SECRET, base_url=BASE)

    # Pull the same exchange-info data the engine loads at startup.
    info = auth.get_exchange_info()
    sinfo = next(s for s in info["symbols"] if s["symbol"] == SYMBOL)
    qty_prec = int(sinfo["quantityPrecision"])
    tick = next(
        float(f["tickSize"]) for f in sinfo["filters"] if f["filterType"] == "PRICE_FILTER"
    )

    # Mark price for sizing + barriers.
    import json
    import httpx
    r = httpx.get(f"{BASE}/fapi/v1/premiumIndex", params={"symbol": SYMBOL}, timeout=10.0)
    mark = float(json.loads(r.text)["markPrice"])
    print(f"=== {SYMBOL} mark={mark} tick={tick} qtyPrec={qty_prec} ===\n")

    cfg = LiveConfig(
        models=(),  # not needed for OrderManager
        dry_run=False,
        max_amount_usd=200.0,
        stop_loss_pct=4.0,
        take_profit_pct=8.0,
        timeout_minutes=10080,
        cooldown_candles=2,
        fee_pct=0.04,
    )

    with tempfile.TemporaryDirectory() as tmpd:
        state = StateStore(Path(tmpd) / "e2e.db")
        mgr = OrderManager(
            cfg, state, auth,
            quantity_precision={SYMBOL: qty_prec},
            tick_size={SYMBOL: tick},
        )

        # Long signal, fixed barriers (4% SL, 8% TP relative to entry).
        signal = Signal(direction=1, weight=100)
        # close_time before now + something ahead; not strictly used by the API call.
        import time as _time
        now_ms = int(_time.time() * 1000)
        candle_close_time = now_ms - 60_000
        candle_open_time = candle_close_time - 60_000

        print("--- open_trade ---")
        try:
            trade = mgr.open_trade(
                model_name="E2E", symbol=SYMBOL, signal=signal,
                entry_price=mark, candle_close_time=candle_close_time,
                candle_open_time=candle_open_time, weight_factor=1.0,
            )
        except Exception as exc:
            print(f"  FAIL: open_trade raised: {exc}")
            return 1

        print(f"  entry_order_id={trade.entry_order_id}")
        print(f"  sl_order_id   ={trade.sl_order_id}  trigger={trade.stop_loss_price}")
        print(f"  tp_order_id   ={trade.tp_order_id}  trigger={trade.take_profit_price}")

        # Verify algos are open on the exchange.
        open_algos = auth.get_open_algo_orders(SYMBOL)
        algo_ids = {str(a["algoId"]) for a in open_algos}
        print(f"\n  open algo orders on exchange ({len(open_algos)}): {algo_ids}")
        sl_ok = trade.sl_order_id in algo_ids
        tp_ok = trade.tp_order_id in algo_ids
        print(f"  SL present: {sl_ok}    TP present: {tp_ok}")

        success = sl_ok and tp_ok

        # Inspect filter populations on each open algo.
        for a in open_algos:
            print(
                f"    algoId={a['algoId']} type={a['orderType']} side={a['side']} "
                f"trigger={a['triggerPrice']} status={a['algoStatus']} "
                f"reduceOnly={a['reduceOnly']} workingType={a['workingType']}"
            )

        # Cleanup
        print("\n--- cleanup ---")
        for aid in (trade.sl_order_id, trade.tp_order_id):
            if aid:
                try:
                    auth.cancel_algo_order(SYMBOL, aid)
                    print(f"  cancelled algoId={aid}")
                except Exception as exc:
                    print(f"  cancel algoId={aid} failed: {exc}")
        try:
            quantity = round(cfg.max_amount_usd / mark, qty_prec)
            close_resp = auth.place_market_order(SYMBOL, "SELL", quantity)
            print(f"  market-close OK: orderId={close_resp.get('orderId')}")
        except Exception as exc:
            print(f"  market-close failed: {exc}")

        # Verify no leftover algos.
        leftover = auth.get_open_algo_orders(SYMBOL)
        print(f"  leftover algos after cleanup: {len(leftover)}")

        state.close()

    print()
    print("=== RESULT ===  " + ("PASS" if success else "FAIL"))
    return 0 if success else 2


if __name__ == "__main__":
    sys.exit(main())
