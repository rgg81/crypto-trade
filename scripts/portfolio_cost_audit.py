"""Full cost audit for the v3 testnet portfolio — ground truth from Binance income.

Read-only. Complements the daily digest (which anchors funding/commission to the
LAST relaunch) by reconciling EVERY cost component across the whole test window:

  REALIZED_PNL  — gross price PnL of closed legs
  FUNDING_FEE   — the recurring 8h funding cash-flow on open positions
  COMMISSION    — taker fees on every rebalance leg
  TRANSFER      — faucet top-ups (excluded from strategy PnL)

It paginates the income endpoint (max 1000 rows/call, 7d default window) forward
to the present, aggregates by type and per-coin, expresses funding+commission as a
drag on gross PnL, and reconciles the income sum against the live wallet balance so
you can see nothing is unaccounted for.

  uv run python scripts/portfolio_cost_audit.py            # since equity-curve start
  uv run python scripts/portfolio_cost_audit.py --all      # entire account history
  uv run python scripts/portfolio_cost_audit.py --since 2026-06-21

Env: needs testnet creds + BINANCE_AUTH_BASE_URL, same as the engine.
"""

from __future__ import annotations

import calendar
import csv
import sys
import time
import warnings
from collections import defaultdict

warnings.filterwarnings("ignore")

EQUITY_CSV = "data/portfolio_equity.csv"
SEVEN_D = 7 * 24 * 3600 * 1000


def _curve_start_ms() -> int | None:
    """First equity-snapshot ts — the monitoring/curve start (digest's income anchor)."""
    try:
        rows = list(csv.DictReader(open(EQUITY_CSV)))
        return int(rows[0]["ts_ms"]) if rows else None
    except (OSError, KeyError, ValueError, IndexError):
        return None


def _parse_since(argv: list[str]) -> tuple[int, str]:
    now_ms = int(time.time() * 1000)
    if "--all" in argv:
        return 1_600_000_000_000, "entire account history"
    if "--since" in argv:
        d = argv[argv.index("--since") + 1]
        return calendar.timegm(time.strptime(d, "%Y-%m-%d")) * 1000, f"since {d} UTC"
    cs = _curve_start_ms()
    if cs is not None:
        return cs, "since equity-curve start (matches digest anchor)"
    return now_ms - 14 * 86400_000, "last 14 days (no curve found)"


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient

    s = load_settings()
    if not s.binance_api_key:
        print("COST AUDIT: SKIP (no creds)")
        return
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=s.auth_base_url
    )

    start_ms, label = _parse_since(sys.argv[1:])
    now_ms = int(time.time() * 1000)

    # paginate income forward: full page -> advance to last_time+1; short page -> +7d
    rows, seen, cursor, guard = [], set(), start_ms, 0
    while cursor < now_ms and guard < 500:
        guard += 1
        try:
            batch = a.get_income(start_time=cursor, limit=1000)
        except Exception as exc:  # noqa: BLE001
            print(f"  (income fetch failed: {repr(exc)[:70]})")
            break
        if not batch:
            cursor += SEVEN_D
            continue
        last_t = cursor
        for inc in batch:
            last_t = max(last_t, int(inc.get("time", cursor)))
            key = (
                inc.get("tranId"),
                inc.get("incomeType"),
                inc.get("time"),
                inc.get("asset"),
                inc.get("income"),
                inc.get("symbol"),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(inc)
        cursor = (last_t + 1) if len(batch) >= 1000 else (cursor + SEVEN_D)
        time.sleep(0.2)  # gentle; engine shares this IP

    if not rows:
        print(f"COST AUDIT: no income rows {label}")
        return

    by_type, by_type_n = defaultdict(float), defaultdict(int)
    funding_by_coin, comm_by_coin = defaultdict(float), defaultdict(float)
    t_min = min(int(r["time"]) for r in rows)
    t_max = max(int(r["time"]) for r in rows)
    for r in rows:
        typ, amt = r.get("incomeType", "?"), float(r.get("income", 0) or 0)
        sym = r.get("symbol", "") or "(none)"
        by_type[typ] += amt
        by_type_n[typ] += 1
        if typ == "FUNDING_FEE":
            funding_by_coin[sym] += amt
        elif typ == "COMMISSION":
            comm_by_coin[sym] += amt

    span_d = max((t_max - t_min) / 86400000, 1e-9)
    realized = by_type.get("REALIZED_PNL", 0.0)
    funding = by_type.get("FUNDING_FEE", 0.0)
    commission = by_type.get("COMMISSION", 0.0)
    total = sum(by_type.values())
    costs = funding + commission

    def utc(ms):
        return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ms / 1000))

    print(
        f"COST AUDIT ({label})  {utc(t_min)} -> {utc(t_max)} UTC  ({span_d:.1f}d, {len(rows)} rows)"
    )
    for typ in sorted(by_type, key=lambda k: by_type[k]):
        print(f"  {typ:<14} {by_type[typ]:+11,.2f}  (n={by_type_n[typ]})")
    print(
        f"  strategy net (excl TRANSFER): "
        f"{realized + costs:+,.2f}  = realized {realized:+,.2f} + funding {funding:+,.2f} "
        f"+ commission {commission:+,.2f}"
    )
    print(
        f"  COSTS funding+commission = {costs:+,.2f}  "
        f"(funding {funding / span_d:+.2f}/day, commission {commission / span_d:+.2f}/day)"
    )
    top_f = sorted(funding_by_coin, key=lambda k: -abs(funding_by_coin[k]))[:5]
    print(
        "  funding by coin (top |amt|): "
        + ", ".join(f"{k.replace('USDT', ''):}={funding_by_coin[k]:+.1f}" for k in top_f)
    )
    ex = funding - min((funding_by_coin[k] for k in funding_by_coin), key=lambda v: v)
    print(f"  funding ex-largest-payer: {ex:+.2f}")

    acct = a.get_account()
    wallet = float(acct.get("totalWalletBalance", 0) or 0)
    upnl = float(acct.get("totalUnrealizedProfit", 0) or 0)
    print(
        f"  RECONCILE: income sum {total:+,.2f} | wallet {wallet:,.2f} | "
        f"uPnL {upnl:+,.2f} | equity {wallet + upnl:,.2f}"
    )


if __name__ == "__main__":
    main()
