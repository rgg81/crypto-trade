"""Calendar-month performance stats for the LIVE v2 testnet portfolio.

Complements `portfolio_v2_pnl.py` (which reports the run-to-date bottom line) by slicing the
SAME Binance income ledger into a single month and deriving a daily P/L series from it, plus
the execution record parsed from the engine log.

Same accounting basis as portfolio_v2_pnl.py, and for the same reason: the HEADLINE is on a
PRODUCTION-funding basis, because testnet funding slams the +-3.75%/8h cap and is a pure
artifact (SIREN alone settled ~-$218 of fake cost). Raw testnet funding is shown alongside so
the distortion stays visible.

IMPORTANT — what the daily series can and cannot say:
  * Realized P/L, funding and commission are CASH-DATED by the exchange, so their daily
    attribution is exact.
  * Unrealized (open-position mark) is NOT in the ledger, so the daily series is a REALIZED-basis
    curve. The month's total therefore differs from the equity delta by the change in open
    unrealized over the month. Both are printed so the gap is explicit rather than hidden.
  * Risk stats (Sharpe, drawdown) are computed on that realized-basis daily series. On a book
    that rebalances every 8h and carries positions across days, a realized-basis curve is
    lumpier than true mark-to-market equity, so treat Sharpe here as indicative, NOT as the
    strategy's Sharpe. Flagged in the output rather than left for the reader to infer.

Read-only. Run:
  cd .worktrees/quant-portfolio && export PATH="$HOME/.local/bin:$PATH" \
    && set -a; source ~/.binance_testnet_v2_env; set +a \
    && export BINANCE_AUTH_BASE_URL=https://testnet.binancefuture.com \
    && uv run python scripts/portfolio_v2_stats.py --month 2026-07
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import os
import re
import statistics
import sys

sys.path.insert(0, "src")

LOG = "logs/portfolio_v2_testnet.log"
SEED = 5_000.0


def _load_pnl_module():
    """Reuse portfolio_v2_pnl's ledger fetch + production-funding repricing (not a package)."""
    here = os.path.dirname(os.path.abspath(__file__))
    spec = importlib.util.spec_from_file_location("pnl", os.path.join(here, "portfolio_v2_pnl.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _month_bounds(month: str) -> tuple[int, int, str]:
    y, mo = (int(x) for x in month.split("-"))
    start = dt.datetime(y, mo, 1, tzinfo=dt.UTC)
    end = dt.datetime(y + (mo == 12), (mo % 12) + 1, 1, tzinfo=dt.UTC)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000), start.strftime("%B %Y")


def _scan_log(lo_ms: int, hi_ms: int):
    """Rebalances/orders/errors for the month, from the engine log.

    The log has no per-line timestamps, so rebalances are dated by their `as_of` candle and the
    following `orders placed=` line is attributed to it. Anything before the first in-month
    rebalance is ignored.
    """
    out = {
        "rebals": 0,
        "orders": 0,
        "skipped": 0,
        "errors": 0,
        "papered": 0,
        "turnover": 0.0,
        "legs": [],
        "tick_errors": 0,
    }
    if not os.path.exists(LOG):
        return out
    in_month = False
    for line in open(LOG, errors="replace"):
        m = re.search(r"rebalance plan as_of=([\d\- :]+) .*legs=(\d+) rebal=\$?([\d.]+)", line)
        if m:
            try:
                ts = dt.datetime.strptime(m.group(1).strip(), "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=dt.UTC
                )
            except ValueError:
                in_month = False
                continue
            in_month = lo_ms <= int(ts.timestamp() * 1000) < hi_ms
            if in_month:
                out["rebals"] += 1
                out["legs"].append(int(m.group(2)))
                out["turnover"] += float(m.group(3))
            continue
        o = re.search(
            r"orders placed=(\d+) skipped=(\d+) errors=(\d+)(?: retrying=(\d+))? papered=(\d+)",
            line,
        )
        if o and in_month:
            out["orders"] += int(o.group(1))
            out["skipped"] += int(o.group(2))
            out["errors"] += int(o.group(3))
            out["papered"] += int(o.group(5))
            in_month = False
        if in_month and "tick error" in line:
            out["tick_errors"] += 1
    return out


def _max_drawdown(cum: list[float]) -> float:
    peak = dd = 0.0
    for v in cum:
        peak = max(peak, v)
        dd = min(dd, v - peak)
    return dd


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", default=dt.datetime.now(dt.UTC).strftime("%Y-%m"))
    args = ap.parse_args()
    lo, hi, label = _month_bounds(args.month)

    pnl = _load_pnl_module()
    from crypto_trade.config import load_settings
    from crypto_trade.live.auth_client import AuthenticatedBinanceClient

    s = load_settings()
    a = AuthenticatedBinanceClient(
        api_key=s.binance_api_key,
        api_secret=s.binance_api_secret,
        base_url=os.environ.get("BINANCE_AUTH_BASE_URL", pnl.TEST_BASE),
    )

    income = pnl._fetch_all_income(a)
    month_rows = [r for r in income if lo <= int(r.get("time", 0)) < hi]
    if not month_rows:
        print(f"[v2 stats — {label}] no ledger rows in month")
        return

    # --- production-funding repricing, month-scoped ------------------------------------
    fund_evs = [
        (r["symbol"], int(r["time"]), float(r["income"]))
        for r in month_rows
        if r.get("incomeType") == "FUNDING_FEE" and r.get("symbol")
    ]
    rp = pnl._prod_repriced_funding(fund_evs)
    funding_tn = sum(i for _, _, i in fund_evs)
    # unmatched testnet events keep their (artifact) value out of the prod figure entirely
    funding_prod = rp["prod_total"]

    realized = sum(float(r["income"]) for r in month_rows if r.get("incomeType") == "REALIZED_PNL")
    commission = sum(float(r["income"]) for r in month_rows if r.get("incomeType") == "COMMISSION")
    deposits = sum(
        float(r["income"]) for r in month_rows if r.get("incomeType") in pnl.DEPOSIT_TYPES
    )

    # --- daily realized-basis series (prod funding substituted per-day, pro-rata) -------
    # Per-day prod funding is scaled by the month's prod/testnet ratio on MATCHED events only;
    # attributing each event individually would need its own rate lookup, and the ratio is the
    # same quantity the headline uses.
    ratio = (rp["prod_total"] / rp["testnet_matched"]) if rp["testnet_matched"] else 0.0
    daily: dict[str, float] = {}
    for r in month_rows:
        t = r.get("incomeType")
        if t in pnl.DEPOSIT_TYPES:
            continue
        day = dt.datetime.fromtimestamp(int(r["time"]) / 1000, dt.UTC).strftime("%Y-%m-%d")
        v = float(r["income"])
        if t == "FUNDING_FEE":
            v *= ratio  # testnet -> production basis
        daily[day] = daily.get(day, 0.0) + v

    days = sorted(daily)
    vals = [daily[d] for d in days]
    cum, run = [], 0.0
    for v in vals:
        run += v
        cum.append(run)
    total = run
    wins = [v for v in vals if v > 0]
    losses = [v for v in vals if v < 0]
    sd = statistics.pstdev(vals) if len(vals) > 1 else 0.0
    sharpe = (statistics.fmean(vals) / sd * (365**0.5)) if sd else 0.0

    # --- current equity, for the mark-to-market reconciliation -------------------------
    acct = a.get_account()
    equity = float(acct.get("totalMarginBalance", 0) or 0)
    unreal = float(acct.get("totalUnrealizedProfit", 0) or 0)

    lg = _scan_log(lo, hi)

    print(f"[v2 portfolio — {label}]  (PRODUCTION-funding basis; testnet funding is an artifact)")
    print(
        f"  REALIZED-BASIS P/L: {total:+.2f}  ({total / SEED * 100:+.2f}% of ${SEED:,.0f} seed)"
        f"  over {len(days)} active days"
    )
    print(
        f"    realized {realized:+.2f} | funding(PROD) {funding_prod:+.2f} "
        f"| commission {commission:+.2f}" + (f" | deposits {deposits:+.2f}" if deposits else "")
    )
    print(
        f"    funding artifact removed: testnet {funding_tn:+.2f} -> prod {funding_prod:+.2f} "
        f"(swing {funding_prod - funding_tn:+.2f}; {rp['n_matched']} matched"
        + (f", {rp['n_unmatched']} unmatched" if rp["n_unmatched"] else "")
        + ")"
    )
    print("  DAILY (realized-basis):")
    print(
        f"    mean {statistics.fmean(vals):+.2f}/d | sd {sd:.2f} | "
        f"best {max(vals):+.2f} ({days[vals.index(max(vals))]}) | "
        f"worst {min(vals):+.2f} ({days[vals.index(min(vals))]})"
    )
    print(
        f"    up {len(wins)}d / down {len(losses)}d ({len(wins) / len(vals) * 100:.0f}% up) | "
        f"maxDD {_max_drawdown(cum):+.2f} | Sharpe~{sharpe:.2f} (indicative only, see below)"
    )
    if lg["rebals"]:
        avg_legs = statistics.fmean(lg["legs"])
        print("  EXECUTION:")
        print(
            f"    {lg['rebals']} rebalances | {lg['orders']} orders placed | "
            f"{lg['errors']} errors | {lg['skipped']} dust-skipped | {lg['papered']} papered"
        )
        print(
            f"    turnover ${lg['turnover']:,.0f} | avg {avg_legs:.1f} legs/rebal "
            f"(min {min(lg['legs'])}, max {max(lg['legs'])})"
        )
    print(
        f"  EQUITY NOW: ${equity:,.2f} (unrealized {unreal:+.2f} not in the daily series above — "
        f"that is why realized-basis != equity delta)"
    )
    print(
        "  CAVEAT: daily series is REALIZED-basis (the ledger has no mark-to-market), so Sharpe "
        "and maxDD are lumpier than true equity and are indicative, not the strategy's Sharpe."
    )


if __name__ == "__main__":
    main()
