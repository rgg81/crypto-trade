"""PnL attribution + daily digest — the real money story, from the LIVE Binance API.

Each run: (1) append an equity snapshot to data/portfolio_equity.csv (the equity curve), and
(2) compute a PnL digest over a trailing window from Binance income history — REALIZED_PNL,
FUNDING_FEE, COMMISSION (taker cost) — summed and attributed per coin, plus unrealized PnL now
and equity change vs ~24h ago. Prints a digest block + `DIGEST_DUE: yes|no` (yes once per UTC day).

The monitor runs this each tick (cheap; logs the equity snapshot) and PushNotifications the digest
when DIGEST_DUE=yes, then calls `--mark-pushed`. Usage:
  portfolio_digest.py                 # snapshot + print digest + DIGEST_DUE
  portfolio_digest.py --mark-pushed   # record that today's digest was pushed
"""

from __future__ import annotations

import csv
import os
import sys
import time

sys.path.insert(0, "src")

EQUITY_CSV = "data/portfolio_equity.csv"
PUSH_STATE = "data/portfolio_digest_last_push.txt"
WINDOW_H = 24


def _utc_date() -> str:
    return time.strftime("%Y-%m-%d", time.gmtime())


def _mark_pushed() -> None:
    os.makedirs("data", exist_ok=True)
    with open(PUSH_STATE, "w") as f:
        f.write(_utc_date())
    print(f"digest marked pushed for {_utc_date()}")


def _due() -> bool:
    if not os.path.exists(PUSH_STATE):
        return True
    return open(PUSH_STATE).read().strip() != _utc_date()


def _append_snapshot(row: dict) -> None:
    os.makedirs("data", exist_ok=True)
    new = not os.path.exists(EQUITY_CSV)
    with open(EQUITY_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)


def _equity_24h_ago(now_ms: int) -> float | None:
    if not os.path.exists(EQUITY_CSV):
        return None
    target = now_ms - WINDOW_H * 3600_000
    best = None
    for r in csv.DictReader(open(EQUITY_CSV)):
        if int(r["ts_ms"]) <= target:
            best = float(r["equity"])           # latest snapshot at/just before the 24h mark
    return best


def _curve_start_ms() -> int | None:
    """First equity-snapshot ts — the (re)launch time. Income before this belongs to a prior
    account incarnation (e.g. pre-faucet-reset churn) and must NOT be attributed to this run."""
    if not os.path.exists(EQUITY_CSV):
        return None
    rows = list(csv.DictReader(open(EQUITY_CSV)))
    return int(rows[0]["ts_ms"]) if rows else None


def main() -> None:
    if "--mark-pushed" in sys.argv:
        _mark_pushed()
        return

    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient
    s = load_settings()
    if not s.binance_api_key:
        print("DIGEST: SKIP (no creds)")
        return
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=s.auth_base_url)

    now_ms = int(time.time() * 1000)
    acct = a.get_account()
    wallet = float(acct.get("totalWalletBalance", 0) or 0)
    upnl = float(acct.get("totalUnrealizedProfit", 0) or 0)
    avail = float(acct.get("availableBalance", 0) or 0)
    equity = wallet + upnl
    pos = [p for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]

    def nz(p):
        return float(p["positionAmt"]) * float(p.get("markPrice", 0) or 0)
    gross = sum(abs(nz(p)) for p in pos)
    net = sum(nz(p) for p in pos)
    _append_snapshot({
        "ts_ms": now_ms,
        "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
        "wallet_balance": round(wallet, 4), "unrealized_pnl": round(upnl, 4),
        "equity": round(equity, 4), "gross": round(gross, 2), "net": round(net, 2),
        "n_positions": len(pos), "avail_balance": round(avail, 4),
    })

    # income attribution over the trailing window, but never before this run's (re)launch
    # (the equity-curve start) — so a faucet reset / relaunch doesn't pull a prior account's
    # realized/commission churn into this run's digest.
    start = now_ms - WINDOW_H * 3600_000
    cstart = _curve_start_ms()
    if cstart is not None:
        start = max(start, cstart)
    win_h = (now_ms - start) / 3600_000
    realized = funding = commission = 0.0
    by_coin: dict[str, float] = {}
    try:
        for inc in a.get_income(start_time=start, limit=1000):
            amt = float(inc.get("income", 0) or 0)
            t = inc.get("incomeType")
            sym = inc.get("symbol") or "-"
            if t == "REALIZED_PNL":
                realized += amt
                by_coin[sym] = by_coin.get(sym, 0.0) + amt
            elif t == "FUNDING_FEE":
                funding += amt
                by_coin[sym] = by_coin.get(sym, 0.0) + amt
            elif t == "COMMISSION":
                commission += amt
    except Exception as exc:
        print(f"  (income history unavailable: {repr(exc)[:70]})")

    e0 = _equity_24h_ago(now_ms)
    chg = f"{equity - e0:+.2f}" if e0 is not None else "n/a (need 24h of snapshots)"
    realized_net = realized + funding + commission
    winners = sorted(by_coin.items(), key=lambda kv: -kv[1])[:3]
    losers = sorted(by_coin.items(), key=lambda kv: kv[1])[:3]

    print(f"DIGEST ({win_h:.0f}h since launch, testnet) — "
          f"{time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    print(f"  equity ${equity:,.2f}  (wallet ${wallet:,.2f} + uPnL ${upnl:+,.2f})  24h delta {chg}")
    print(f"  realized PnL ${realized:+,.2f} | funding ${funding:+,.2f} | "
          f"commission ${commission:+,.2f} | net realized ${realized_net:+,.2f}")
    print(f"  positions {len(pos)}  gross ${gross:,.0f}  net ${net:+,.0f}")
    if winners:
        print("  top +: " + ", ".join(f"{k} ${v:+.2f}" for k, v in winners if v > 0))
        print("  top -: " + ", ".join(f"{k} ${v:+.2f}" for k, v in losers if v < 0))
    print(f"DIGEST_DUE: {'yes' if _due() else 'no'}")


if __name__ == "__main__":
    main()
