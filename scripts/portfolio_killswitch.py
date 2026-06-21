"""KILL-SWITCH — emergency halt: STOP the engine, then FLATTEN every position. Manual, --confirm.

Order matters and is the point of "don't compete with the trade loop": STOP the engine FIRST so it
can't re-enter, THEN flatten. Flattening uses reduceOnly market orders (bypasses the $5 min, so it
clears dust too). Idempotent: re-running after a partial flatten finishes the job.

  portfolio_killswitch.py            # DRY: show what it WOULD do (no orders, no kill)
  portfolio_killswitch.py --confirm  # actually stop the engine + flatten

Requires creds in the env (source ~/.binance_testnet_env + BINANCE_AUTH_BASE_URL). Targets whatever
account those creds point at — testnet flattens testnet, live flattens live. Use with care.
"""

from __future__ import annotations

import subprocess
import sys
import time

sys.path.insert(0, "src")

ENGINE_PATTERN = "run_portfolio_testnet"      # the engine process to stop first


def _stop_engine(confirm: bool) -> int:
    n = int(subprocess.run(
        ["bash", "-c", f"ps -eo cmd | grep '{ENGINE_PATTERN}' | grep -v grep | wc -l"],
        capture_output=True, text=True).stdout.strip() or "0")
    if confirm and n:
        subprocess.run(["pkill", "-9", "-f", ENGINE_PATTERN], capture_output=True)
        time.sleep(2)
    return n


def main() -> None:
    confirm = "--confirm" in sys.argv
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient
    s = load_settings()
    if not s.binance_api_key:
        print("KILLSWITCH: SKIP (no creds)")
        return
    mode = "TESTNET" if "testnet" in (s.auth_base_url or "").lower() else "LIVE"
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=s.auth_base_url)

    print(f"KILLSWITCH ({'EXECUTE' if confirm else 'DRY-RUN'}, MODE={mode})")

    # 1) STOP the engine FIRST (so it cannot re-enter after we flatten)
    running = _stop_engine(confirm)
    print(f"  engine: {running} process(es) " + ("STOPPED" if confirm and running
                                                  else "found" if running else "not running"))

    # 2) FLATTEN every open position (reduceOnly market orders)
    prec = {si["symbol"]: int(si["quantityPrecision"])
            for si in a.get_exchange_info()["symbols"]}
    pos = [p for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]
    print(f"  positions to flatten: {len(pos)}")
    closed = errors = 0
    for p in pos:
        sym = p["symbol"]
        amt = float(p["positionAmt"])
        side = "SELL" if amt > 0 else "BUY"
        qty = round(abs(amt), prec.get(sym, 3))
        notl = abs(amt) * float(p.get("markPrice", 0) or 0)
        if not confirm:
            print(f"    WOULD {side} {sym} x{qty}  (${notl:,.2f})")
            continue
        try:
            a.place_market_order(sym, side, qty, reduce_only=True)
            closed += 1
        except Exception as exc:
            errors += 1
            print(f"    close {sym} FAILED: {repr(exc)[:80]}")

    if confirm:
        time.sleep(1)
        rem = [p for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]
        print(f"  flattened {closed} closed, {errors} errors; remaining open: {len(rem)}")
        if rem:
            print("    (re-run --confirm to finish any remainder)")
    else:
        print("  DRY-RUN — pass --confirm to actually stop the engine + flatten")


if __name__ == "__main__":
    main()
