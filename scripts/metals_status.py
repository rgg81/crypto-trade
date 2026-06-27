"""Metals paper-engine STATUS — the per-tick alert check (health + parity + candle integrity).

READ-ONLY. Three test-integrity checks for the metals paper desk (iter-010 breadth-accel champion):
  STATUS  : engine alive (ps), no Traceback, last rebalance not overdue (a new 8h candle is due but
            unprocessed). ALERT on engine down / traceback / missed rebalance.
  PARITY  : recompute the champion target from data_live_metals and compare per-metal to the held
            book in the DB. DRIFT = the paper book no longer matches what the strategy says to hold.
  CANDLE  : no forming (incomplete) candle leaked into the signal data; data not stale (>9h).

Per the HANDS-OFF mandate these are the ONLY alert sources (test-integrity). PnL / drawdown / regime
are observational — see metals_digest.py. Exit 0 = all OK; exit 1 = an alert fired.

Run:  uv run python scripts/metals_status.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
for p in (str(_ROOT / "src"), str(_ROOT / "analysis" / "portfolio" / "metals")):
    if p not in sys.path:
        sys.path.insert(0, p)

import live_weights as lw  # noqa: E402
import universe_metals as um  # noqa: E402
from live_metals import MetalsPaperEngine  # noqa: E402

from crypto_trade.live.state_store import StateStore  # noqa: E402

DB = _ROOT / "data" / "metals_paper.db"
LOG = _ROOT / "logs" / "metals_paper.log"
DATA = _ROOT / "data_live_metals"
STEP_MS = 8 * 60 * 60 * 1000
PARITY_TOL = 1e-4  # held vs recomputed target (paper = exact fill, so this should be ~0)


def _engine_up() -> bool:
    """True iff the engine PROCESS is running — match the actual `python … run_metals_paper.py`,
    not a shell/grep/monitor command that merely MENTIONS the string (which naive substring matching
    false-positives on; e.g. a `bash -c '… grep run_metals_paper.py …'` wrapper)."""
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    bad = ("grep", "pgrep", "bash -c", "/bin/sh", "metals_status", "metals_digest")
    return any(
        "run_metals_paper.py" in ln and "python" in ln and not any(b in ln for b in bad)
        for ln in out.splitlines()
    )


def _log_scan() -> tuple[bool, str]:
    if not LOG.exists():
        return False, "no log"
    tail = LOG.read_text(errors="ignore").splitlines()[-400:]
    tb = any("Traceback" in line for line in tail)
    rebal = next((line for line in reversed(tail) if "[rebal]" in line), "")
    return tb, rebal.strip()


def main() -> int:
    alerts: list[str] = []
    flags: list[str] = []

    up = _engine_up()
    if not up:
        alerts.append("engine DOWN (run_metals_paper.py not running)")
    tb, last_rebal = _log_scan()
    if tb:
        alerts.append("TRACEBACK in logs/metals_paper.log")

    held, last_candle, equity, launch = {}, None, None, None
    if DB.exists():
        st = StateStore(DB)
        raw = st.get_state("metals_held_w")
        held = json.loads(raw) if raw else {}
        last_candle = st.get_state("metals_last_candle")
        equity = st.get_state("metals_equity")
        launch = st.get_state("metals_launch_candle")
    else:
        flags.append("no DB yet (engine not seeded)")

    # MISSED rebalance: a new COMPLETE 8h candle is clock-due but last_candle hasn't advanced.
    if last_candle is not None:
        now_ms = int(time.time() * 1000)
        latest_complete = (now_ms // STEP_MS) * STEP_MS - STEP_MS
        behind_h = (latest_complete - int(last_candle)) / 3_600_000
        if behind_h >= 8:  # a full candle overdue (weekend gaps are < 8h of trading candles)
            alerts.append(
                f"MISSED rebalance: last_candle {pd.Timestamp(int(last_candle), unit='ms')} is "
                f"{behind_h:.0f}h behind the clock-due candle"
            )

    # CANDLE integrity + PARITY (only when data present)
    candle = "n/a"
    parity = "n/a"
    if DATA.exists() and any(DATA.iterdir()):
        coins = um.load_metals(DATA)
        now_ms = int(time.time() * 1000)
        leaks = [s for s, d in coins.items() if len(d) and int(d.index[-1]) + STEP_MS > now_ms]
        freshest = max((int(d.index[-1]) for d in coins.values() if len(d)), default=0)
        stale_h = (now_ms - (freshest + STEP_MS)) / 3_600_000
        if leaks:
            alerts.append(f"CANDLE=BAD forming-candle leak in {leaks}")
            candle = "BAD"
        elif stale_h > 9:
            flags.append(f"data stale: freshest complete candle {stale_h:.0f}h old (>9h)")
            candle = f"STALE {stale_h:.0f}h"
        else:
            candle = "OK"

        if held:  # parity: recompute the champion target (SAME forming proxy the engine uses)
            tgt = lw.next_target_weights_metals(MetalsPaperEngine._append_forming(coins))
            tgt.pop("_meta", None)
            drift = [
                f"{s}: held {held.get(s, 0.0):+.4f} vs target {tgt.get(s, 0.0):+.4f}"
                for s in set(held) | set(tgt)
                if abs(float(held.get(s, 0.0)) - float(tgt.get(s, 0.0))) > PARITY_TOL
            ]
            parity = "OK" if not drift else "DRIFT"
            if drift:
                alerts.append("PARITY=DRIFT: " + "; ".join(drift[:6]))

    status = "ALERT" if alerts else "OK"
    eq = f"${float(equity):,.0f}" if equity else "n/a"
    print(
        f"STATUS: {status}  (engine={'up' if up else 'DOWN'}, equity={eq}, "
        f"held={len(held)} names, parity={parity}, candle={candle})"
    )
    if last_rebal:
        print(f"  last rebal: {last_rebal}")
    if launch and last_candle:
        print(
            f"  candles: launch {pd.Timestamp(int(launch), unit='ms')} → "
            f"last {pd.Timestamp(int(last_candle), unit='ms')}"
        )
    for a in alerts:
        print(f"  ALERT: {a}")
    for f in flags:
        print(f"  flag: {f}")
    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
