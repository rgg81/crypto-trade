"""Health check for the LIVE v2 testnet portfolio engine (rank-21-40 XS-mom ensemble).

One-shot; prints STATUS: OK|ALERT + positions/balance + FLAG: lines. Mirrors the v1
portfolio_healthcheck but for the ISOLATED v2 deploy (separate runner / log / DB / account).

Per the monitor HANDS-OFF mandate: alerts are TEST-INTEGRITY only (engine down, traceback, REAL
order errors, missed rebalance). Testnet-artifact order errors (-1121 invalid-symbol, -4131
PERCENT_PRICE, -4411 TradFi-agreement, -4141 symbol-closed/not-on-testnet + its -1111 precision
cascade) are INFO, not alerts — testnet liquidity/listing quirks that vanish on production.
DD/PnL/tilt are observational (not acted on).

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
# -4141 "Symbol is closed" = a prod-listed name absent from testnet (e.g. TLM: TRADING on prod,
# NOT LISTED on testnet) — same family as -1121 invalid-symbol / -4140. Trades fine on production.
TESTNET_ERR = {"-1121", "-4131", "-4411", "-4061", "-4046", "-4140", "-4141"}
# Binance hard-rejects a timestamp >1000ms AHEAD of server time (-1021). The client compensates
# (see the skew block in main), so this is reported as INFO well below the 1000ms cliff.
CLOCK_SKEW_WARN_MS = 300


def _proc_alive() -> bool:
    out = subprocess.run(["ps", "-eo", "cmd"], capture_output=True, text=True).stdout
    return PROC in out


def _clock_skew_ms(base: str) -> float | None:
    """Local clock offset vs Binance server time, in ms (positive = local AHEAD).

    Binance REJECTS any signed request whose timestamp is >1000ms AHEAD of server time
    (error -1021), and `recvWindow` does NOT relax that side — it only widens the
    behind-tolerance. So a host clock running fast is a HARD trading blocker: every signed
    call (get_positions, place_order, set_leverage) fails and the engine places NO orders,
    while public kline fetches keep working and the log looks healthy. WSL hosts drift
    ahead across a reboot/suspend when NTP is inactive, which is exactly how this bites.
    Measured mid-flight (local clock sampled either side of the request) so network latency
    doesn't masquerade as skew.
    """
    import json
    import time as _t
    import urllib.request

    try:
        t0 = _t.time() * 1000
        with urllib.request.urlopen(f"{base}/fapi/v1/time", timeout=10) as r:
            server = float(json.load(r)["serverTime"])
        t1 = _t.time() * 1000
        return (t0 + t1) / 2 - server
    except Exception:
        return None


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
    # transient -4131 (thin-book PERCENT_PRICE) retries — INFO, not an error: v20 retries a liquid
    # symbol instead of permanently papering it, and only papers after N consecutive strikes.
    retries = re.findall(r"errors=\d+ retrying=(\d+)", txt)
    if retries and int(retries[-1]) > 0:
        info.append(
            f"transient -4131 retries x{retries[-1]} (INFO: thin-book PERCENT_PRICE; retried, "
            f"papers only after consecutive strikes — liquid names retry+fill)"
        )
    # classify the order-error lines of the LAST rebalance block
    if res:
        last_errs = int(res[-1][2])
        if last_errs:
            # the failure lines after the last 'rebalance plan'
            tail = txt[txt.rfind("rebalance plan") :]
            # Group failure codes by SYMBOL, not by raw "code" occurrence: one failing leg can
            # emit TWO codes (e.g. set_leverage -4141 THEN order -1111 for the same symbol), so
            # counting occurrences double-flags a single benign leg. Classify per symbol.
            sym_codes: dict[str, set[str]] = {}
            fail_pat = (
                r"(?:order \w+ (\w+) x[\d.]+ failed|set_leverage (\w+) failed)"
                r'[^\n]*?"code":(-?\d+)'
            )
            for m in re.finditer(fail_pat, tail):
                sym_codes.setdefault(m.group(1) or m.group(2), set()).add(m.group(3))
            # A symbol whose codes are ALL testnet artifacts is INFO. -1111 "precision" is a
            # CASCADE (INFO) when the same symbol also threw a listing artifact: a prod-listed
            # symbol absent from testnet (e.g. TLM) gets default precision -> -1111. -4164
            # "notional < min" is a benign DUST-boundary leg (< $5), held at current — self-corrects
            # next rebalance; the v22 min-notional buffer skips these before send.
            listing = {"-4141", "-1121", "-4140"}  # symbol closed / invalid / not tradeable
            dust_errs = 0
            for cset in sym_codes.values():
                has_listing = bool(cset & listing)
                benign = all(
                    c in TESTNET_ERR or c == "-4164" or (c == "-1111" and has_listing) for c in cset
                )
                if benign and "-4164" in cset:
                    dust_errs += 1
                elif benign:
                    testnet_errs += 1
                else:
                    real_errs += 1
            # HTTP 5xx / gateway failures (e.g. 502 Bad Gateway) are testnet INFRA
            # transients — the exchange's edge returned an HTML error page with NO JSON
            # "code", so they slip past the per-symbol classifier above. Count the engine's own
            # per-order failure lines (one per failed POST) so errors>0 is never silent.
            gateway_errs = len(re.findall(r"order .* failed: 5\d\d", tail))
            if testnet_errs:
                info.append(
                    f"testnet-artifact order errors x{testnet_errs} "
                    f"(INFO: symbol closed/invalid on testnet incl -4141/-1121, +cascade -1111)"
                )
            if dust_errs:
                info.append(
                    f"min-notional dust legs x{dust_errs} (INFO: -4164 <$5 notional; held at "
                    f"current, self-corrects next rebalance; v22 buffer skips these pre-send)"
                )
            if gateway_errs:
                info.append(
                    f"testnet gateway 5xx order errors x{gateway_errs} "
                    f"(INFO: transient infra; off-target legs self-heal at next rebalance)"
                )
            # never swallow errors silently: surface any last_errs not classified above
            unclassified = last_errs - testnet_errs - dust_errs - real_errs - gateway_errs
            if unclassified > 0:
                info.append(f"unclassified order errors x{unclassified} (review log)")
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

    # Clock skew vs the exchange. Since 4874fba2 AuthenticatedBinanceClient re-syncs its own
    # offset from /fapi/v1/time on a -1021 and retries, so skew no longer blocks trading — it is
    # HOST HYGIENE, reported as INFO. (Proven live 2026-07-27: 17 orders placed, errors=0, with
    # the host still +1.32s off.) It stays worth surfacing because the compensation is a fallback,
    # not a licence to let the host drift, and because v1 has its own un-patched src/ copy.
    auth_base = os.environ.get("BINANCE_AUTH_BASE_URL", "https://testnet.binancefuture.com")
    skew = _clock_skew_ms(auth_base)
    if skew is not None and abs(skew) > CLOCK_SKEW_WARN_MS:
        info.append(
            f"host clock {skew:+.0f}ms vs exchange (engine self-corrects via /fapi/v1/time on "
            f"-1021; host fix needs an ELEVATED Windows prompt: "
            f"sc config w32time start= auto; net start w32time; w32tm /resync /force)"
        )

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
        # surface the Binance error code — a bare exception name hides WHY (e.g. -1021 clock
        # skew vs -2015 bad key vs -1003 rate limit), which cost real diagnosis time on 2026-07-27
        detail = ""
        resp = getattr(e, "response", None)
        if resp is not None:
            try:
                body = resp.json()
                detail = f" [{body.get('code')}: {body.get('msg')}]"
            except Exception:
                detail = f" [HTTP {resp.status_code}]"
        info.append(f"account query failed: {type(e).__name__}{detail}")

    status = "ALERT" if flags else "OK"
    proc_s = "up" if alive else "DOWN"
    print(f"STATUS: {status}  MODE=TESTNET-v2  proc={proc_s}  last_rebal={last_rebal}")
    print(f"  {pos_line}")
    for f in flags:
        print(f"  ALERT: {f}")
    for i in info:
        print(f"  INFO:  {i}")


if __name__ == "__main__":
    main()
