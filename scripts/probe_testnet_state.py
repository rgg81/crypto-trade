"""Probe testnet account state — position mode, balance, open positions/orders.

Run via:
  source ~/.binance_testnet_env
  BINANCE_BASE_URL=https://testnet.binancefuture.com uv run python scripts/probe_testnet_state.py
"""

import hashlib
import hmac
import os
import time
from urllib.parse import urlencode

import httpx

from crypto_trade.live.auth_client import AuthenticatedBinanceClient

api_key = os.environ["BINANCE_API_KEY"]
api_secret = os.environ["BINANCE_API_SECRET"]
base = os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com")

c = AuthenticatedBinanceClient(api_key, api_secret, base_url=base)

print(f"=== Endpoint: {base} ===")
print()
print("=== Account ===")
acct = c.get_account()
keys = ["totalWalletBalance", "availableBalance", "feeTier", "totalUnrealizedProfit"]
for k in keys:
    print(f"  {k}: {acct.get(k)}")

print()
print("=== Position mode (dual-side / hedge) ===")
ts = int(time.time() * 1000)
params = {"timestamp": ts, "recvWindow": 5000}
q = urlencode(params)
sig = hmac.new(api_secret.encode(), q.encode(), hashlib.sha256).hexdigest()
params["signature"] = sig
r = httpx.get(
    f"{base}/fapi/v1/positionSide/dual",
    params=params,
    headers={"X-MBX-APIKEY": api_key},
)
print(f"  HTTP {r.status_code}: {r.text}")

print()
print("=== Open positions (non-zero) ===")
positions = c.get_positions()
nonzero = [p for p in positions if float(p.get("positionAmt", 0)) != 0]
if not nonzero:
    print("  (none)")
else:
    for p in nonzero:
        print(
            f"  {p.get('symbol')} amt={p.get('positionAmt')} "
            f"entry={p.get('entryPrice')} side={p.get('positionSide')}"
        )

print()
print("=== Open orders ===")
oo = c.get_open_orders()
if not oo:
    print("  (none)")
else:
    for o in oo[:20]:
        print(
            f"  {o.get('symbol')} id={o.get('orderId')} type={o.get('type')} "
            f"side={o.get('side')} stopPrice={o.get('stopPrice')} "
            f"qty={o.get('origQty')} reduceOnly={o.get('reduceOnly')} "
            f"closePosition={o.get('closePosition')} workingType={o.get('workingType')}"
        )

print()
print("=== Symbols of interest — exchangeInfo filters ===")
info = c.get_exchange_info()
of_interest = {"BTCUSDT", "ETHUSDT", "LTCUSDT", "DOTUSDT", "NEARUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT"}
for s in info.get("symbols", []):
    if s.get("symbol") in of_interest:
        filt = {f["filterType"]: f for f in s.get("filters", [])}
        pf = filt.get("PRICE_FILTER", {})
        ls = filt.get("LOT_SIZE", {})
        pp = filt.get("PERCENT_PRICE", {})
        print(
            f"  {s['symbol']}: tickSize={pf.get('tickSize')} stepSize={ls.get('stepSize')} "
            f"minQty={ls.get('minQty')} qtyPrec={s.get('quantityPrecision')} "
            f"pricePrec={s.get('pricePrecision')} "
            f"PercentPrice up={pp.get('multiplierUp')} dn={pp.get('multiplierDown')}"
        )

c.close()
