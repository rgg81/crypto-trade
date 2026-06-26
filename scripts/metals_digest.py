"""Metals paper-engine DIGEST — the periodic observational report (NOT an alert source).

READ-ONLY. Reports the paper equity curve + PnL + the current regime (breadth) + held positions for
the iter-010 metals champion. Per the HANDS-OFF mandate these are TEST RESULTS, not alerts — report
them, never act on them. Prints `DIGEST_DUE: yes` on the first run of a new UTC day (so the monitor
loop pushes one digest/day); `--mark-pushed` records that it fired.

Run:  uv run python scripts/metals_digest.py [--mark-pushed]
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
for p in (str(_ROOT / "src"), str(_ROOT / "analysis" / "portfolio" / "metals")):
    if p not in sys.path:
        sys.path.insert(0, p)

from crypto_trade.live.state_store import StateStore  # noqa: E402

DB = _ROOT / "data" / "metals_paper.db"
EQ = _ROOT / "data" / "metals_equity.csv"


def main() -> int:
    mark = "--mark-pushed" in sys.argv
    if not DB.exists():
        print("DIGEST: n/a (no DB yet)")
        return 0
    st = StateStore(DB)
    held = json.loads(st.get_state("metals_held_w") or "{}")
    equity = float(st.get_state("metals_equity") or 0.0)

    eq_df = pd.read_csv(EQ) if EQ.exists() else pd.DataFrame()
    line = f"DIGEST  equity=${equity:,.0f}"
    if len(eq_df) >= 2:
        e0 = float(eq_df["equity_usd"].iloc[0])
        prev = eq_df[eq_df["ts_utc"] < (pd.Timestamp.utcnow() - pd.Timedelta(hours=24)).isoformat()]
        ret_since = (equity / e0 - 1) * 100 if e0 else 0.0
        d24 = (equity / float(prev["equity_usd"].iloc[-1]) - 1) * 100 if len(prev) else float("nan")
        breadth = float(eq_df["breadth"].iloc[-1]) if "breadth" in eq_df else float("nan")
        regime = "BEAR" if breadth >= 0.6 else ("transitional" if breadth >= 0.3 else "calm")
        line += (
            f"  since-launch {ret_since:+.1f}%  24h {d24:+.1f}%  "
            f"breadth={breadth:.2f} ({regime})  snapshots={len(eq_df)}"
        )
    print(line)
    if held:
        print("  positions: " + ", ".join(f"{s} {w:+.4f}" for s, w in sorted(held.items())))

    # once-a-day push flag
    today = dt.datetime.now(dt.UTC).date().isoformat()
    last = st.get_state("metals_digest_pushed_day")
    due = last != today
    if mark:
        st.set_state("metals_digest_pushed_day", today)
        print("  (marked pushed for", today, ")")
    else:
        print(f"DIGEST_DUE: {'yes' if due else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
