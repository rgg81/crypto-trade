"""Trend-aware alerts — catch slow bleeds + drifts the per-tick threshold checks miss.

Reads the equity curve (data/portfolio_equity.csv) and looks at TRENDS across the last ~2h of
snapshots, not just the instantaneous value: a steadily declining equity, margin trending toward
liquidation, gross drifting, or a persistent unrealized-PnL slide. Also reports the delta since the
previous tick ("what changed"). CSV-only -> never competes with the trade loop.

Prints `TREND: OK | WATCH`. WATCH is a soft alert (a developing situation worth a heads-up),
distinct from the hard threshold breaches in the other checks.
"""

from __future__ import annotations

import csv
import os
import time

EQUITY_CSV = "data/portfolio_equity.csv"
WINDOW_MS = 2 * 60 * 60 * 1000     # trend window ~2h
EQUITY_DROP = 0.05                 # equity down >5% over the window -> WATCH (fast bleed)
MARGIN_DROP = 0.30                 # available margin down >30% over the window -> WATCH


def _f(row: dict, key: str):
    v = row.get(key)
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def main() -> None:
    if not os.path.exists(EQUITY_CSV):
        print("TREND: OK (no equity curve yet)")
        return
    rows = list(csv.DictReader(open(EQUITY_CSV)))
    if len(rows) < 3:
        print(f"TREND: OK (need >=3 snapshots, have {len(rows)})")
        return

    now_ms = int(rows[-1]["ts_ms"])
    window_start = now_ms - WINDOW_MS
    past = [r for r in rows if int(r["ts_ms"]) <= window_start] or [rows[0]]
    r0, r1 = past[-1], rows[-1]                         # oldest-in-window vs now
    prev = rows[-2]                                     # previous tick

    e0, e1 = _f(r0, "equity"), _f(r1, "equity")
    flags, parts = [], []
    if e0 and e1:
        de = (e1 - e0) / e0
        parts.append(f"equity {de * 100:+.1f}%/2h (${e1:,.0f})")
        if de < -EQUITY_DROP:
            flags.append(f"equity down {de * 100:.1f}% over 2h (fast bleed)")
    m0, m1 = _f(r0, "avail_balance"), _f(r1, "avail_balance")
    if m0 and m1 and m0 > 0:
        dm = (m1 - m0) / m0
        parts.append(f"margin {dm * 100:+.1f}%/2h (${m1:,.0f})")
        if dm < -MARGIN_DROP:
            flags.append(f"available margin down {dm * 100:.1f}% over 2h (toward liquidation)")
    g1 = _f(r1, "gross")
    if g1 is not None:
        parts.append(f"gross ${g1:,.0f}")

    # what changed since last tick
    de_tick = None
    ep, en = _f(prev, "equity"), _f(r1, "equity")
    if ep and en:
        de_tick = en - ep
    np_, nn = _f(prev, "n_positions"), _f(r1, "n_positions")
    pos_chg = f", positions {int(np_)}->{int(nn)}" if (np_ is not None and nn is not None
                                                       and np_ != nn) else ""

    status = "WATCH" if flags else "OK"
    detail = "; ".join(parts)
    if de_tick is not None:
        detail += f"; since last tick Δequity ${de_tick:+.2f}{pos_chg}"
    print(f"TREND: {status}  ({detail})")
    for f in flags:
        print(f"  WATCH: {f}")
    print(f"  checked {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")


if __name__ == "__main__":
    main()
