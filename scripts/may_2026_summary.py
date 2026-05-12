"""May 2026 PnL summary — paper + binance, realized + unrealized.

Run via:
  source ~/.binance_testnet_env
  BINANCE_BASE_URL=https://testnet.binancefuture.com \
    uv run python scripts/may_2026_summary.py
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone

from crypto_trade.live.auth_client import AuthenticatedBinanceClient

con = sqlite3.connect("data/testnet.db")
cur = con.cursor()
may_start = int(datetime(2026, 5, 1, tzinfo=timezone.utc).timestamp() * 1000)
may_end = int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp() * 1000)


def trade_type(eid: str | None) -> str:
    if eid is None or eid == "SEEDED":
        return "PAPER"
    if eid.startswith("CATCHUP-") or eid.startswith("DRY-"):
        return "PAPER"
    return "BINANCE"


def latest_close(sym: str) -> float | None:
    try:
        with open(f"data/{sym}/8h.csv") as f:
            return float(f.readlines()[-1].split(",")[4])
    except Exception:
        return None


fee_pct = 0.1

# ---- Realized ----
print("=" * 90)
print("MAY 2026  REALIZED")
print("=" * 90)
cur.execute(
    """SELECT model_name, symbol, direction, entry_price, exit_price, exit_reason,
              weight_factor, amount_usd, entry_order_id, open_time, exit_time
       FROM trades
       WHERE status = 'closed' AND exit_time >= ? AND exit_time < ?
       ORDER BY exit_time""",
    (may_start, may_end),
)
closed = cur.fetchall()

totals = {"PAPER": [0, 0.0], "BINANCE": [0, 0.0]}
header = (
    f"\n{'close (UTC)':17}  {'type':7} {'model':8} {'symbol':9} dir   "
    f"{'entry':>10}  {'exit':>10}  {'net%':>7}  {'wf':>4}  {'weighted':>9}  reason"
)
print(header)
for r in closed:
    model, sym, dirn, entry, ex, reason, wf, amt, eid, ot, ct = r
    pnl_pct = (ex - entry) / entry * 100 * dirn
    net = pnl_pct - fee_pct
    weighted = net * wf
    typ = trade_type(eid)
    totals[typ][0] += 1
    totals[typ][1] += weighted
    iso = datetime.fromtimestamp(ct / 1000, tz=timezone.utc).strftime("%m-%d %H:%M:%S")
    print(
        f"{iso:17}  {typ:7} {model:8} {sym:9} {dirn:+d}    "
        f"{entry:>10.4f}  {ex:>10.4f}  {net:+7.2f}%  {wf:.2f}  {weighted:+9.4f}  {reason}"
    )
print()
print(
    f"  PAPER     realized:  {totals['PAPER'][0]:3} trades  weighted_pnl = "
    f"{totals['PAPER'][1]:+8.4f}"
)
print(
    f"  BINANCE   realized:  {totals['BINANCE'][0]:3} trades  weighted_pnl = "
    f"{totals['BINANCE'][1]:+8.4f}"
)
total_real_n = sum(t[0] for t in totals.values())
total_real_w = sum(t[1] for t in totals.values())
print(
    f"  TOTAL     realized:  {total_real_n:3} trades  weighted_pnl = {total_real_w:+8.4f}"
)

# ---- Unrealized ----
auth = AuthenticatedBinanceClient(
    os.environ["BINANCE_API_KEY"],
    os.environ["BINANCE_API_SECRET"],
    base_url=os.environ.get("BINANCE_BASE_URL", "https://testnet.binancefuture.com"),
)
mark_map: dict[str, float] = {}
for p in auth.get_positions():
    if float(p.get("positionAmt", 0)) != 0:
        mark_map[p["symbol"]] = float(p["markPrice"])

print()
print("=" * 90)
print("MAY 2026  UNREALIZED (open positions)")
print("=" * 90)
cur.execute(
    """SELECT id, model_name, symbol, direction, entry_price, stop_loss_price, take_profit_price,
              amount_usd, weight_factor, entry_order_id, open_time
       FROM trades WHERE status = 'open'"""
)
opens = cur.fetchall()
unr = {"PAPER": [0, 0.0], "BINANCE": [0, 0.0]}
header = (
    f"\n{'type':7} {'model':8} {'symbol':9} dir   {'entry':>10}  {'current':>10}  "
    f"{'unr%':>7}  {'wf':>4}  {'weighted':>9}  source"
)
print(header)
for r in opens:
    tid, model, sym, dirn, entry, sl, tp, amt, wf, eid, ot = r
    typ = trade_type(eid)
    if typ == "BINANCE" and sym in mark_map:
        cur_p = mark_map[sym]
        src = "mark"
    else:
        cur_p = latest_close(sym)
        src = "8h close"
    if cur_p is None:
        continue
    unr_pct = (cur_p - entry) / entry * 100 * dirn
    weighted = unr_pct * wf
    unr[typ][0] += 1
    unr[typ][1] += weighted
    print(
        f"{typ:7} {model:8} {sym:9} {dirn:+d}    {entry:>10.4f}  {cur_p:>10.4f}  "
        f"{unr_pct:+7.2f}%  {wf:.2f}  {weighted:+9.4f}  {src}"
    )
print()
print(
    f"  PAPER    unrealized:  {unr['PAPER'][0]:3} positions  "
    f"weighted_pnl = {unr['PAPER'][1]:+8.4f}"
)
print(
    f"  BINANCE  unrealized:  {unr['BINANCE'][0]:3} positions  "
    f"weighted_pnl = {unr['BINANCE'][1]:+8.4f}"
)

# ---- Grand summary ----
print()
print("=" * 90)
print("MAY 2026  GRAND SUMMARY")
print("=" * 90)
total_unr_n = sum(u[0] for u in unr.values())
total_unr_w = sum(u[1] for u in unr.values())
print(f"  Realized    weighted PnL: {total_real_w:+8.4f}   ({total_real_n} trades)")
print(f"  Unrealized  weighted PnL: {total_unr_w:+8.4f}   ({total_unr_n} positions)")
print(f"  Combined                : {total_real_w + total_unr_w:+8.4f}")
print()
print(
    f"  PAPER     realized + unrealized: {totals['PAPER'][1] + unr['PAPER'][1]:+8.4f}"
)
print(
    f"  BINANCE   realized + unrealized: {totals['BINANCE'][1] + unr['BINANCE'][1]:+8.4f}"
)

acct = auth.get_account()
print()
print("=== Live Binance testnet wallet ===")
print(f"  totalWalletBalance:    {acct.get('totalWalletBalance')}  USDT")
print(f"  availableBalance:      {acct.get('availableBalance')}  USDT")
print(f"  totalUnrealizedProfit: {acct.get('totalUnrealizedProfit')}  USDT")

auth.close()
con.close()
