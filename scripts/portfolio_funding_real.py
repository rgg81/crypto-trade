"""Re-price the portfolio's funding using PRODUCTION funding rates, not testnet.

Testnet funding is unrepresentative: the testnet matching engine has thin/synthetic
order books, so its funding rates are distorted (e.g. ESPORTSUSDT pinned at the
-3.75%/8h cap on testnet vs ~+0.05% on production — wrong magnitude AND sign, and
testnet even settles it every 4h vs production's 8h). Testnet-charged funding is
therefore NOT what this book would pay live.

This re-prices each historical funding settlement at the real production rate. Since
funding = -notional * rate and the position is identical, for each testnet funding
record:

    funding_real = funding_testnet * (rate_prod / rate_testnet)

exactly (the notional cancels). Where production has NO settlement at that timestamp
(testnet's extra 4h intervals), production would charge nothing -> funding_real = 0.

It also prints a forward run-rate: current live positions * current production rate.

  uv run python scripts/portfolio_funding_real.py
  uv run python scripts/portfolio_funding_real.py --since 2026-06-21

Reads the cost ledger (data/portfolio_cost_ledger.csv) for FUNDING_FEE records, so
run scripts/portfolio_cost_tracker.py first. Production rates come from
https://fapi.binance.com (public, separate host from the testnet trading IP).
"""

from __future__ import annotations

import bisect
import calendar
import csv
import sys
import time
import warnings
from collections import defaultdict

import httpx

warnings.filterwarnings("ignore")

LEDGER_CSV = "data/portfolio_cost_ledger.csv"
PROD_BASE = "https://fapi.binance.com"
TEST_BASE = "https://testnet.binancefuture.com"
MATCH_TOL_MS = 4 * 60 * 1000  # match a funding record to a rate within +/-4 min


def _funding_history(base: str, symbol: str, start_ms: int) -> dict[int, float]:
    """{fundingTime_ms: rate} for a symbol, paginated forward from start_ms."""
    out: dict[int, float] = {}
    cursor = start_ms
    now = int(time.time() * 1000)
    for _ in range(20):
        try:
            r = httpx.get(
                f"{base}/fapi/v1/fundingRate",
                params={"symbol": symbol, "startTime": cursor, "limit": 1000},
                timeout=20,
            ).json()
        except Exception:  # noqa: BLE001
            break
        if not isinstance(r, list) or not r:
            break
        for x in r:
            out[int(x["fundingTime"])] = float(x["fundingRate"])
        last = max(int(x["fundingTime"]) for x in r)
        if len(r) < 1000 or last >= now:
            break
        cursor = last + 1
    return out


def _match(sorted_times: list[int], rates: dict[int, float], t: int):
    """Nearest funding rate to time t within tolerance, else None."""
    if not sorted_times:
        return None
    i = bisect.bisect_left(sorted_times, t)
    best = None
    for j in (i - 1, i):
        if 0 <= j < len(sorted_times):
            dt = abs(sorted_times[j] - t)
            if dt <= MATCH_TOL_MS and (best is None or dt < best[0]):
                best = (dt, sorted_times[j])
    return rates[best[1]] if best else None


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient

    argv = sys.argv[1:]
    since = None
    if "--since" in argv:
        since = calendar.timegm(time.strptime(argv[argv.index("--since") + 1], "%Y-%m-%d")) * 1000

    # load testnet FUNDING_FEE records from the ledger
    try:
        rows = list(csv.DictReader(open(LEDGER_CSV)))
    except OSError:
        print("FUNDING_REAL: no ledger — run portfolio_cost_tracker.py first")
        return
    fund = defaultdict(list)  # symbol -> [(time_ms, income_testnet)]
    for r in rows:
        if r.get("incomeType") != "FUNDING_FEE":
            continue
        t = int(r["time"])
        if since and t < since:
            continue
        fund[r.get("symbol") or "(none)"].append((t, float(r.get("income", 0) or 0)))
    if not fund:
        print("FUNDING_REAL: no FUNDING_FEE records in ledger")
        return

    test_total = sum(v for recs in fund.values() for _, v in recs)
    real_by_coin = {}
    test_by_coin = {}
    unmatched = 0
    for sym, recs in fund.items():
        start = min(t for t, _ in recs) - 2 * 86400_000
        prod = _funding_history(PROD_BASE, sym, start)
        test = _funding_history(TEST_BASE, sym, start)
        pt = sorted(prod)
        tt = sorted(test)
        real_sum = 0.0
        for t, inc in recs:
            rp = _match(pt, prod, t)
            rt = _match(tt, test, t)
            if rt is None or rt == 0:
                unmatched += 1
                continue  # can't rescale without the testnet rate that produced it
            if rp is None:
                continue  # production has no settlement here -> 0
            real_sum += inc * (rp / rt)
        real_by_coin[sym] = real_sum
        test_by_coin[sym] = sum(v for _, v in recs)

    real_total = sum(real_by_coin.values())
    span_recs = [t for recs in fund.values() for t, _ in recs]
    span_d = max((max(span_recs) - min(span_recs)) / 86400000, 1e-9)

    print(f"FUNDING RE-PRICED at PRODUCTION rates  ({len(span_recs)} settlements, {span_d:.1f}d)")
    print(
        f"  testnet-charged funding: ${test_total:+,.2f} ({test_total / span_d:+.2f}/d) [artifact]"
    )
    print(
        f"  production-real funding: ${real_total:+,.2f} ({real_total / span_d:+.2f}/d) [realistic]"
    )
    print(f"  testnet overstates cost by ${test_total - real_total:+,.2f}")
    if unmatched:
        print(f"  ({unmatched} settlements had no testnet rate to rescale — treated as 0)")
    print("  per-coin (testnet -> production):")
    for sym in sorted(test_by_coin, key=lambda k: test_by_coin[k])[:10]:
        print(
            f"    {sym.replace('USDT', ''):<10} testnet {test_by_coin[sym]:+8.2f}  ->  "
            f"production {real_by_coin.get(sym, 0.0):+8.2f}"
        )

    # forward run-rate: current live positions * current production funding rate
    s = load_settings()
    if not s.binance_api_key:
        return
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=s.auth_base_url
    )
    try:
        pos = [p for p in a.get_positions() if float(p.get("positionAmt", 0) or 0) != 0]
        prem = httpx.get(f"{PROD_BASE}/fapi/v1/premiumIndex", timeout=20).json()
        fr = {x["symbol"]: float(x["lastFundingRate"]) for x in prem}
        # funding paid per settlement = -signed_notional * rate; summed over the book
        per_settle = 0.0
        for p in pos:
            amt = float(p["positionAmt"])
            mk = float(p.get("markPrice", 0) or 0)
            rate = fr.get(p["symbol"])
            if rate is None:
                continue
            per_settle += -(amt * mk) * rate
        print(
            f"  FORWARD run-rate (current book x current prod rate): "
            f"${per_settle:+.3f}/settlement  (~${per_settle * 3:+.2f}/day at 8h cadence)"
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  (forward run-rate skipped: {repr(exc)[:50]})")


if __name__ == "__main__":
    main()
