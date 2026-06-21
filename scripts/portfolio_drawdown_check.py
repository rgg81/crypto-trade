"""Drawdown / equity-curve tracking — live DD vs the backtest's -23%, from the logged equity curve.

Reads the equity snapshots `portfolio_digest.py` logs to data/portfolio_equity.csv and computes the
live drawdown. Reports TWO numbers because the testnet account is smaller than the strategy notional
base, so account DD is leverage-amplified vs the strategy DD:

  - ACCOUNT DD  = equity vs its running peak (the real liquidation-relevant number).
  - STRATEGY-EQUIV DD = cumulative-PnL-as-fraction-of-NOTIONAL vs its peak — directly comparable to
    the baseline-v3 backtest maxDD of -23%.

Alerts on a BREACH: account DD beyond ALERT_ACCOUNT_DD, OR strategy-equiv DD worse than the backtest
-23% by a margin (live worse than ever backtested -> investigate). Prints `DD: OK | BREACH`.
The curve starts when digest logging began, so it tracks forward strategy performance — not the
earlier deploy/debug churn. Short window early on => mostly informational until days accumulate.
"""

from __future__ import annotations

import csv
import os
import time

EQUITY_CSV = "data/portfolio_equity.csv"
NOTIONAL = 10_000.0            # strategy notional base (matches run_portfolio_testnet.py)
BACKTEST_MAXDD = 0.23         # baseline-v3 backtest maxDD (reference)
ALERT_ACCOUNT_DD = 0.20      # account DD from peak that warrants an alert
ALERT_STRAT_MARGIN = 1.5     # strat-equiv DD worse than backtest x this => alert


def main() -> None:
    if not os.path.exists(EQUITY_CSV):
        print("DD: OK (no equity curve yet)")
        return
    rows = list(csv.DictReader(open(EQUITY_CSV)))
    if len(rows) < 2:
        print(f"DD: OK (need >=2 snapshots, have {len(rows)})")
        return

    eq = [float(r["equity"]) for r in rows]
    t0, t1 = int(rows[0]["ts_ms"]), int(rows[-1]["ts_ms"])
    hours = (t1 - t0) / 3_600_000

    # account DD: equity vs its running peak
    peak = eq[0]
    acct_maxdd = 0.0
    for e in eq:
        peak = max(peak, e)
        acct_maxdd = max(acct_maxdd, (peak - e) / peak)
    acct_now_dd = (max(eq) - eq[-1]) / max(eq) if max(eq) > 0 else 0.0

    # strategy-equiv DD: drawdown of cumulative PnL as a fraction of NOTIONAL (vs backtest -23%)
    base = eq[0]
    cum = [e - base for e in eq]
    cpeak = cum[0]
    strat_maxdd = 0.0
    for c in cum:
        cpeak = max(cpeak, c)
        strat_maxdd = max(strat_maxdd, (cpeak - c) / NOTIONAL)
    cum_pnl = cum[-1]

    flags = []
    if acct_maxdd > ALERT_ACCOUNT_DD:
        flags.append(f"ACCOUNT DD {acct_maxdd * 100:.1f}% > {ALERT_ACCOUNT_DD * 100:.0f}%")
    if strat_maxdd > BACKTEST_MAXDD * ALERT_STRAT_MARGIN:
        flags.append(f"STRAT-EQUIV DD {strat_maxdd * 100:.1f}% >> backtest "
                     f"{BACKTEST_MAXDD * 100:.0f}%")

    status = "BREACH" if flags else "OK"
    print(f"DD: {status}  (account maxDD {acct_maxdd * 100:.1f}% / now {acct_now_dd * 100:.1f}%; "
          f"strat-equiv maxDD {strat_maxdd * 100:.1f}% vs backtest -{BACKTEST_MAXDD * 100:.0f}%; "
          f"cumPnL ${cum_pnl:+,.2f}; {len(eq)} snaps over {hours:.1f}h)")
    for f in flags:
        print(f"  BREACH: {f}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
