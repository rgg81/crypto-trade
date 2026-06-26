"""Metals paper-engine DIGEST — the periodic BOOK + STATS report (NOT an alert source).

READ-ONLY. Reports the held BOOK (per-metal weight + $ exposure, long/short), gross/net exposure,
regime (breadth), equity, and PnL (since-launch + 24h) for the deployed metals champion at its live
leverage. Per the HANDS-OFF mandate these are TEST RESULTS — report them, never act on them.

`REPORT_DUE: yes` fires when a NEW REBALANCE has occurred since the last report (the book changed —
every ~8h) OR it's the first report of a new UTC day, so the monitor loop pushes the book "from time
to time" (≈ on each rebalance + at least daily). `--mark-pushed` records that it fired.

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

import live_weights as lw  # noqa: E402  — for the deployed leverage
import universe_metals as um  # noqa: E402

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
    last_candle = st.get_state("metals_last_candle")

    eq_df = pd.read_csv(EQ) if EQ.exists() else pd.DataFrame()
    ret_since = d24 = float("nan")
    breadth = float("nan")
    if len(eq_df):
        e0 = float(eq_df["equity_usd"].iloc[0])
        ret_since = (equity / e0 - 1) * 100 if e0 else 0.0
        cutoff = (pd.Timestamp.now("UTC") - pd.Timedelta(hours=24)).isoformat()
        prev = eq_df[eq_df["ts_utc"] < cutoff]
        if len(prev):
            d24 = (equity / float(prev["equity_usd"].iloc[-1]) - 1) * 100
        if "breadth" in eq_df:
            breadth = float(eq_df["breadth"].iloc[-1])
    regime = "BEAR" if breadth >= 0.6 else ("transitional" if breadth >= 0.3 else "calm")
    asof = pd.Timestamp(int(last_candle), unit="ms") if last_candle else "n/a"

    gross = sum(abs(w) for w in held.values())
    net = sum(held.values())
    print(
        f"METALS BOOK + STATS  (as_of {asof}, {lw.LEVERAGE:.0f}x leverage)\n"
        f"  equity ${equity:,.0f}   since-launch {ret_since:+.1f}%   24h {d24:+.1f}%   "
        f"regime {regime} (breadth {breadth:.2f})\n"
        f"  gross {gross:.2f}x (${gross * equity:,.0f})   net {net:+.2f}x (${net * equity:,.0f})"
    )
    if held:
        print("  book:")
        for s, w in sorted(held.items(), key=lambda kv: -abs(kv[1])):
            name = um.NAMES.get(s, s)
            side = "LONG " if w > 0 else "SHORT"
            print(f"    {side} {name:10} {s:8} {w:+.4f}   ${w * equity:>+9,.0f}")

    # push trigger: a new rebalance (book changed) OR a new UTC day since the last report
    today = dt.datetime.now(dt.UTC).date().isoformat()
    last_rep_candle = st.get_state("metals_report_candle")
    last_rep_day = st.get_state("metals_report_day")
    due = (last_candle is not None and last_candle != last_rep_candle) or (last_rep_day != today)
    if mark:
        st.set_state("metals_report_candle", str(last_candle))
        st.set_state("metals_report_day", today)
        print(f"  (reported: candle {asof}, day {today})")
    else:
        print(f"REPORT_DUE: {'yes' if due else 'no'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
