"""Incremental, persistent cost tracker for the v3 testnet portfolio.

Wired into the monitor so EVERY tick keeps a running ledger of ALL trade costs —
REALIZED_PNL, FUNDING_FEE, COMMISSION, TRANSFER — pulled from the Binance income
endpoint (ground truth). Unlike the daily digest (which anchors to the last
relaunch) this accumulates across the whole test and never loses history.

Cheap by design: it stores every income row in data/portfolio_cost_ledger.csv and
each run fetches ONLY rows newer than the last stored one (usually a single page),
dedups by (tranId, type, time, income, symbol), appends, then prints cumulative
totals + per-coin funding + a one-line COSTS: summary the monitor greps, and
reconciles the ledger sum against the live wallet balance.

  uv run python scripts/portfolio_cost_tracker.py            # incremental update + report
  uv run python scripts/portfolio_cost_tracker.py --bootstrap 2026-06-21   # seed from a date

First run with an empty ledger bootstraps from --bootstrap (default: equity-curve
start, matching the digest). Env: testnet creds + BINANCE_AUTH_BASE_URL.
"""

from __future__ import annotations

import calendar
import csv
import os
import sys
import time
import warnings
from collections import defaultdict

warnings.filterwarnings("ignore")

LEDGER_CSV = "data/portfolio_cost_ledger.csv"
BASELINE_TXT = "data/portfolio_cost_baseline.txt"  # wallet balance just before ledger start
EQUITY_CSV = "data/portfolio_equity.csv"
FIELDS = ["tranId", "time", "incomeType", "asset", "income", "symbol", "tradeId"]
SEVEN_D = 7 * 24 * 3600 * 1000
OVERLAP_MS = 5 * 60 * 1000  # refetch a small tail to catch same-boundary races


def _row_key(r: dict) -> tuple:
    return (
        str(r.get("tranId", "")),
        r.get("incomeType", ""),
        str(r.get("time", "")),
        str(r.get("income", "")),
        r.get("symbol", "") or "",
    )


def _load_ledger() -> list[dict]:
    if not os.path.exists(LEDGER_CSV):
        return []
    with open(LEDGER_CSV, newline="") as f:
        return list(csv.DictReader(f))


def _append_ledger(new_rows: list[dict]) -> None:
    exists = os.path.exists(LEDGER_CSV)
    os.makedirs(os.path.dirname(LEDGER_CSV), exist_ok=True)
    with open(LEDGER_CSV, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            w.writeheader()
        for r in new_rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def _curve_start_ms() -> int | None:
    try:
        rows = list(csv.DictReader(open(EQUITY_CSV)))
        return int(rows[0]["ts_ms"]) if rows else None
    except (OSError, KeyError, ValueError, IndexError):
        return None


def _bootstrap_start(argv: list[str]) -> int:
    if "--bootstrap" in argv:
        d = argv[argv.index("--bootstrap") + 1]
        return calendar.timegm(time.strptime(d, "%Y-%m-%d")) * 1000
    cs = _curve_start_ms()
    return cs if cs is not None else int(time.time() * 1000) - 14 * 86400_000


def main() -> None:
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient

    s = load_settings()
    if not s.binance_api_key:
        print("COSTS: SKIP (no creds)")
        return
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key, api_secret=s.binance_api_secret, base_url=s.auth_base_url
    )

    ledger = _load_ledger()
    seen = {_row_key(r) for r in ledger}
    now_ms = int(time.time() * 1000)
    if ledger:
        last_t = max(int(r["time"]) for r in ledger)
        cursor = last_t - OVERLAP_MS  # small overlap; dedup handles it
    else:
        cursor = _bootstrap_start(sys.argv[1:])

    # paginate forward from cursor to now: full page -> advance to last+1; short -> +7d
    fresh, guard = [], 0
    while cursor < now_ms and guard < 500:
        guard += 1
        try:
            batch = a.get_income(start_time=cursor, limit=1000)
        except Exception as exc:  # noqa: BLE001
            print(f"COSTS: fetch error ({repr(exc)[:50]}) — using stored ledger")
            break
        if not batch:
            cursor += SEVEN_D
            continue
        page_last = cursor
        for inc in batch:
            page_last = max(page_last, int(inc.get("time", cursor)))
            k = _row_key(inc)
            if k in seen:
                continue
            seen.add(k)
            fresh.append(inc)
        cursor = (page_last + 1) if len(batch) >= 1000 else (cursor + SEVEN_D)
        time.sleep(0.2)  # gentle; engine shares this IP

    if fresh:
        _append_ledger(fresh)
    ledger = ledger + fresh

    if not ledger:
        print("COSTS: no income rows yet")
        return

    by_type, by_type_n = defaultdict(float), defaultdict(int)
    funding_by_coin = defaultdict(float)
    t_min = min(int(r["time"]) for r in ledger)
    t_max = max(int(r["time"]) for r in ledger)
    for r in ledger:
        typ = r.get("incomeType", "?")
        amt = float(r.get("income", 0) or 0)
        by_type[typ] += amt
        by_type_n[typ] += 1
        if typ == "FUNDING_FEE":
            funding_by_coin[r.get("symbol", "") or "(none)"] += amt

    realized = by_type.get("REALIZED_PNL", 0.0)
    funding = by_type.get("FUNDING_FEE", 0.0)
    commission = by_type.get("COMMISSION", 0.0)
    transfer = by_type.get("TRANSFER", 0.0)
    strat_net = realized + funding + commission
    span_d = max((t_max - t_min) / 86400000, 1e-9)

    def utc(ms):
        return time.strftime("%Y-%m-%d %H:%M", time.gmtime(ms / 1000))

    # one-line summary (monitor greps "COSTS:")
    print(
        f"COSTS: funding ${funding:+,.2f} | commission ${commission:+,.2f} | "
        f"realized ${realized:+,.2f} | strat_net ${strat_net:+,.2f} | "
        f"funding_rate ${funding / span_d:+.2f}/day  (+{len(fresh)} new rows, {span_d:.1f}d ledger)"
    )
    # detail block
    top_f = sorted(funding_by_coin, key=lambda k: -abs(funding_by_coin[k]))[:5]
    worst = min(funding_by_coin.values()) if funding_by_coin else 0.0
    print(
        "  funding by coin: "
        + ", ".join(f"{k.replace('USDT', '')}={funding_by_coin[k]:+.1f}" for k in top_f)
        + f"   (ex-worst: {funding - worst:+.2f})"
    )
    if transfer:
        print(f"  (excl TRANSFER ${transfer:+,.2f} faucet)  ledger {utc(t_min)}->{utc(t_max)} UTC")

    # reconcile against live wallet. invariant: wallet(now) = baseline + sum(income since start),
    # where baseline = wallet balance just before the ledger's first row. Captured once so drift
    # is meaningful no matter where we bootstrapped from.
    try:
        acct = a.get_account()
        wallet = float(acct.get("totalWalletBalance", 0) or 0)
        upnl = float(acct.get("totalUnrealizedProfit", 0) or 0)
        led_total = realized + funding + commission + transfer
        if os.path.exists(BASELINE_TXT):
            baseline = float(open(BASELINE_TXT).read().strip() or 0)
        else:
            baseline = wallet - led_total  # first run: infer pre-ledger wallet
            with open(BASELINE_TXT, "w") as f:
                f.write(f"{baseline:.8f}")
        drift = wallet - (baseline + led_total)
        flag = "" if abs(drift) < 5.0 else "  ⚠ ledger-vs-wallet DRIFT (income gap?)"
        print(
            f"  RECONCILE: baseline ${baseline:,.2f} + ledger ${led_total:+,.2f} "
            f"= ${baseline + led_total:,.2f} vs wallet ${wallet:,.2f} | "
            f"drift ${drift:+,.2f}{flag} | uPnL ${upnl:+,.2f}"
        )
    except Exception as exc:  # noqa: BLE001
        print(f"  (reconcile skipped: {repr(exc)[:50]})")


if __name__ == "__main__":
    main()
