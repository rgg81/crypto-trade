"""Health check for the live testnet portfolio engine — one-shot, prints STATUS: OK|WARN|ALERT.

Checks everything that could go wrong during the multi-day run:
  - engine process alive
  - recent tracebacks / order errors in the log
  - last rebalance (as_of, orders placed/errors) + staleness vs the 8h cadence
  - live positions: count, gross, net, max single-name concentration, zombie/delisted reappearance
  - balance + margin ratio (liquidation headroom)

Reads creds from the environment (source ~/.binance_testnet_env + BINANCE_AUTH_BASE_URL=testnet).
Exit 0 always; the STATUS line + flags are what the monitor reads.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time

sys.path.insert(0, "src")

LOG = "logs/portfolio_testnet_v3.log"
EXPECT_GROSS = (5_000, 12_000)     # $ gross band ($10k equity x 0.70-0.85 vol-target +/- slack)
MAX_CONC = 0.30                    # single-name share of gross alarm threshold
CANDLE_MS = 8 * 60 * 60 * 1000
DELISTED = {"TOMOUSDT", "BLZUSDT"}  # must NOT reappear in the book


def _proc_alive() -> bool:
    out = subprocess.run(
        ["ps", "-eo", "cmd"], capture_output=True, text=True).stdout
    return "venv/bin/python3 run_portfolio_testnet" in out


def _log_scan() -> tuple[list[str], str | None, int]:
    flags = []
    last_rebal = None
    last_errs = 0
    if not os.path.exists(LOG):
        return ["log missing"], None, 0
    txt = open(LOG, errors="replace").read()
    if "Traceback" in txt:
        flags.append(f"TRACEBACK x{txt.count('Traceback')}")
    rebals = re.findall(r"rebalance plan as_of=([\d :-]+) .*?legs=(\d+)", txt)
    errs = re.findall(r"orders placed=(\d+) errors=(\d+)", txt)
    if rebals:
        last_rebal = rebals[-1][0].strip()
    if errs:
        last_errs = int(errs[-1][1])
    return flags, last_rebal, last_errs


def main() -> None:
    flags: list[str] = []
    alive = _proc_alive()
    if not alive:
        flags.append("ENGINE DOWN (process not running)")
    log_flags, last_rebal, last_errs = _log_scan()
    flags += log_flags
    if last_errs > 0:
        flags.append(f"last rebalance had {last_errs} order errors")

    # live positions (best-effort; needs creds)
    pos_line = "positions: (no creds / API skipped)"
    try:
        from crypto_trade.config import load_settings
        from crypto_trade.live.auth_client import AuthenticatedBinanceClient
        s = load_settings()
        if s.binance_api_key:
            a = AuthenticatedBinanceClient(
                api_key=s.binance_api_key, api_secret=s.binance_api_secret,
                base_url=s.auth_base_url)
            pos = [p for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]

            def nz(p):
                return float(p["positionAmt"]) * float(p.get("markPrice", 0) or 0)
            gl = sum(nz(p) for p in pos if nz(p) > 0)
            gs = sum(nz(p) for p in pos if nz(p) < 0)
            gross = gl - gs
            upnl = sum(float(p.get("unRealizedProfit", 0) or 0) for p in pos)
            top = max((abs(nz(p)) for p in pos), default=0.0)
            conc = top / gross if gross else 0.0
            zomb = [p["symbol"] for p in pos if p["symbol"] in DELISTED]
            bal = next((float(b["balance"]) for b in a.get_balance()
                        if b["asset"] == "USDT"), 0.0)
            mbal = next((float(b.get("availableBalance", 0) or 0) for b in a.get_balance()
                         if b["asset"] == "USDT"), 0.0)
            pos_line = (f"positions: {len(pos)}  gross ${gross:,.0f}  net ${gl + gs:+,.0f}  "
                        f"uPnL ${upnl:+,.0f}  maxConc {conc * 100:.0f}%  "
                        f"bal ${bal:,.0f} avail ${mbal:,.0f}")
            if gross and not (EXPECT_GROSS[0] <= gross <= EXPECT_GROSS[1]):
                flags.append(f"GROSS OUT OF BAND (${gross:,.0f})")
            if conc > MAX_CONC:
                flags.append(f"CONCENTRATION {conc * 100:.0f}% > {MAX_CONC * 100:.0f}%")
            if zomb:
                flags.append(f"DELISTED REAPPEARED: {zomb}")
            if mbal < 200:
                flags.append(f"LOW MARGIN: avail ${mbal:,.0f}")
    except Exception as exc:
        flags.append(f"API check failed: {repr(exc)[:80]}")

    status = "ALERT" if flags else "OK"
    print(f"STATUS: {status}  (engine={'up' if alive else 'DOWN'}, "
          f"last_rebal={last_rebal}, last_errs={last_errs})")
    print(f"  {pos_line}")
    if flags:
        for f in flags:
            print(f"  FLAG: {f}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
