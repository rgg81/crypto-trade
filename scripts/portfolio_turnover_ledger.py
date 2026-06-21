"""Turnover / cost ledger — confirm the low-turnover win holds live, and catch turnover spikes.

Parses the engine log for each 8h rebalance (legs / notional / placed / skipped / errors),
per-rebalance ledger to data/portfolio_turnover.csv (dedup by as_of), and reports live tickets per
rebalance. Live steady-state turnover should be LOW (the hysteresis band + eligibility-exit + the $5
min-notional skip suppress tiny trades) — typically a few legs/rebalance, under the backtest's
~18 ticket/candle figure (the backtest counts sub-$5 scale-drift adjustments the live engine skips).

Alerts on a turnover SPIKE: a steady-state rebalance with an unusually high leg count (band not
suppressing churn / a regime shift) — distinct from the one-off cold-start full-entry rebalances.
Log-only -> never competes with the trade loop. Prints `TURNOVER: OK | SPIKE`.
"""

from __future__ import annotations

import csv
import os
import re
import time

LOG = "logs/portfolio_testnet_v3.log"
LEDGER = "data/portfolio_turnover.csv"
COLDSTART_LEGS = 15       # >= this on the FIRST rebalance(s) = cold-start full entry (expected)
SPIKE_LEGS = 15           # a non-cold-start rebalance with this many legs = turnover spike

PLAN_RE = re.compile(r"rebalance plan as_of=([\d-]+ [\d:]+).*?legs=(\d+) rebal=\$([\d.]+)")
ORD_RE = re.compile(r"orders placed=(\d+)(?: skipped=(\d+))? errors=(\d+)")


def _parse() -> list[dict]:
    if not os.path.exists(LOG):
        return []
    recs, pending = [], None
    for line in open(LOG, errors="replace"):
        m = PLAN_RE.search(line)
        if m:
            pending = {"as_of": m.group(1), "legs": int(m.group(2)), "rebal": float(m.group(3))}
            continue
        o = ORD_RE.search(line)
        if o and pending:
            pending["placed"] = int(o.group(1))
            pending["skipped"] = int(o.group(2) or 0)
            pending["errors"] = int(o.group(3))
            recs.append(pending)
            pending = None
    return recs


def _persist(recs: list[dict]) -> None:
    if not recs:
        return
    os.makedirs("data", exist_ok=True)
    cols = ["as_of", "legs", "rebal", "placed", "skipped", "errors"]
    seen = {}
    for r in recs:
        seen[r["as_of"]] = r                       # dedup by as_of, keep latest
    with open(LEDGER, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in sorted(seen.values(), key=lambda x: x["as_of"]):
            w.writerow({k: r.get(k, "") for k in cols})


def main() -> None:
    recs = _parse()
    if not recs:
        print("TURNOVER: OK (no rebalances logged yet)")
        return
    _persist(recs)

    # tag cold-starts: leading rebalances with >=COLDSTART_LEGS legs (full entry on (re)launch)
    flags = []
    for i, r in enumerate(recs):
        cold = r["legs"] >= COLDSTART_LEGS and i <= 2
        if not cold and r["legs"] >= SPIKE_LEGS:
            flags.append(f"turnover SPIKE at {r['as_of']}: {r['legs']} legs (band off?)")
    steady = [r for i, r in enumerate(recs) if not (r["legs"] >= COLDSTART_LEGS and i <= 2)]
    avg_legs = sum(r["legs"] for r in steady) / len(steady) if steady else 0.0
    last = recs[-1]
    tot_err = sum(r["errors"] for r in recs)

    status = "SPIKE" if flags else "OK"
    print(f"TURNOVER: {status}  ({len(recs)} rebalances, steady avg {avg_legs:.1f} legs/rebal "
          f"[backtest ~18 incl sub-$5; live skips those], last {last['as_of']} "
          f"legs={last['legs']} rebal=${last['rebal']:,.0f} err={last['errors']}, "
          f"tot_err={tot_err})")
    for f in flags:
        print(f"  SPIKE: {f}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
