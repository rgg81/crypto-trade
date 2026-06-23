"""Health check for the LIVE v2 testnet portfolio engine (rank-21-40 XS-mom ensemble).

One-shot; prints STATUS: OK|ALERT + positions/balance + FLAG: lines. Mirrors the v1
portfolio_healthcheck but for the ISOLATED v2 deploy (separate runner / log / DB / account).

Per the monitor HANDS-OFF mandate: alerts are TEST-INTEGRITY only (engine down, traceback, REAL order
errors, missed rebalance). Testnet-artifact order errors (-1121 invalid-symbol, -4131 PERCENT_PRICE,
-4411 TradFi-agreement) are INFO, not alerts — they're testnet liquidity/listing quirks that vanish on
production. DD/PnL/tilt are observational (not acted on).

Run:  cd .worktrees/quant-portfolio && export PATH="$HOME/.local/bin:$PATH" \
      && set -a; source ~/.binance_testnet_v2_env; set +a \
      && export BINANCE_AUTH_BASE_URL=https://testnet.binancefuture.com \
      && uv run python scripts/portfolio_v2_healthcheck.py
"""

from __future__ import annotations

import os
import re
import subprocess
import sys

sys.path.insert(0, "src")

LOG = "logs/portfolio_v2_testnet.log"
PROC = "run_portfolio_v2_testnet"
EXPECT_GROSS = (700, 3_500)  # $ gross band ($4k equity x vol-target ~0.3-0.6 after the de-lever)
MAX_CONC = 0.40  # single-name share of gross (mid-caps run a touch more concentrated than top-20)
CANDLE_MS = 8 * 60 * 60 * 1000
# testnet-only execution quirks (INFO, never a strategy alert):
TESTNET_ERR = {"-1121", "-4131", "-4411", "-4061", "-4046", "-4140"}


def _proc_alive() -> bool:
    out = subprocess.run(["ps", "-eo", "cmd"], capture_output=True, text=True).stdout
    return PROC in out


def _log_scan():
    flags, info, last_rebal, real_errs, testnet_errs = [], [], None, 0, 0
    if not os.path.exists(LOG):
        return ["log missing"], [], None, 0, 0
    txt = open(LOG, errors="replace").read()
    if "Traceback" in txt:
        flags.append(f"TRACEBACK x{txt.count('Traceback')}")
    rebals = re.findall(r"rebalance plan as_of=([\d :-]+) ", txt)
    last_rebal = rebals[-1].strip() if rebals else None
    res = re.findall(r"orders placed=(\d+) skipped=(\d+) errors=(\d+)", txt)
    # classify the order-error lines of the LAST rebalance block
    if res:
        last_errs = int(res[-1][2])
        if last_errs:
            # the failure lines after the last 'rebalance plan'
            tail = txt[txt.rfind("rebalance plan") :]
            codes = re.findall(r'"code":(-?\d+)', tail)
            for c in codes:
                if c in TESTNET_ERR:
                    testnet_errs += 1
                else:
                    real_errs += 1
            if testnet_errs:
                info.append(
                    f"testnet-artifact order errors x{testnet_errs} (INFO: -1121/-4131/-4411)"
                )
            if real_errs:
                flags.append(f"REAL order errors x{real_errs}")
    return flags, info, last_rebal, real_errs, testnet_errs


def main() -> None:
    import time

    flags: list[str] = []
    info: list[str] = []
    alive = _proc_alive()
    if not alive:
        flags.append("ENGINE DOWN")
    lf, li, last_rebal, real_errs, testnet_errs = _log_scan()
    flags += lf
    info += li

    # staleness: how far past the last 8h boundary is last_rebal?
    now = time.time()
    boundary = (int(now) // (8 * 3600)) * (8 * 3600)
    if last_rebal:
        try:
            import datetime as dt

            lr = dt.datetime.strptime(last_rebal, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.UTC)
            # alert only if we're >25min past a boundary and last_rebal hasn't reached it
            if now - boundary > 1500 and lr.timestamp() < boundary:
                flags.append(f"MISSED rebalance (last={last_rebal}, boundary passed)")
        except Exception:
            pass

    # live account (v2 creds from env)
    pos_line = "positions: n/a (no creds / API error)"
    try:
        from crypto_trade.config import load_settings
        from crypto_trade.live.auth_client import AuthenticatedBinanceClient

        s = load_settings()
        if s.binance_api_key:
            a = AuthenticatedBinanceClient(
                api_key=s.binance_api_key,
                api_secret=s.binance_api_secret,
                base_url=os.environ.get(
                    "BINANCE_AUTH_BASE_URL", "https://testnet.binancefuture.com"
                ),
            )
            pos = [p for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]
            gross = sum(
                abs(float(p["positionAmt"]) * float(p.get("markPrice", 0) or 0)) for p in pos
            )
            net = sum(float(p["positionAmt"]) * float(p.get("markPrice", 0) or 0) for p in pos)
            upnl = sum(float(p.get("unRealizedProfit", 0) or 0) for p in pos)
            conc = (
                max(
                    (abs(float(p["positionAmt"]) * float(p.get("markPrice", 0) or 0)) for p in pos),
                    default=0,
                )
                / gross
                if gross
                else 0
            )
            bal = [b for b in a.get_balance() if b.get("asset") == "USDT"]
            avail = float(bal[0].get("availableBalance", 0)) if bal else 0
            pos_line = (
                f"positions={len(pos)} gross=${gross:.0f} net=${net:+.0f} uPnL=${upnl:+.1f} "
                f"maxConc={conc:.0%} avail=${avail:.0f}"
            )
            if not (EXPECT_GROSS[0] <= gross <= EXPECT_GROSS[1]) and gross > 0:
                info.append(f"gross ${gross:.0f} outside {EXPECT_GROSS} (info)")
            if conc > MAX_CONC:
                info.append(f"concentration {conc:.0%} > {MAX_CONC:.0%} (info)")
    except Exception as e:
        info.append(f"account query failed: {type(e).__name__}")

    status = "ALERT" if flags else "OK"
    print(
        f"STATUS: {status}  MODE=TESTNET-v2  proc={'up' if alive else 'DOWN'}  last_rebal={last_rebal}"
    )
    print(f"  {pos_line}")
    for f in flags:
        print(f"  ALERT: {f}")
    for i in info:
        print(f"  INFO:  {i}")


if __name__ == "__main__":
    main()
