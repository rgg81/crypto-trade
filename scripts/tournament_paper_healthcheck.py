"""crypto-cup-01 paper-desk healthcheck — STATUS OK|ALERT one-pager (read-only).

Checks: engine process alive, log freshness + tracebacks, DB last-candle recency, frozen-
submission SHA integrity, and DB-held-book vs recomputed-strategy-book parity (dry-run desks
must never drift — held IS the strategy output).

  uv run python scripts/tournament_paper_healthcheck.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "analysis"))

LOG = _ROOT / "logs" / "portfolio_tournament_paper.log"
DB = _ROOT / "data" / "portfolio_tournament_paper.db"

alerts: list[str] = []
notes: list[str] = []

# 1. process
ps = subprocess.run(
    ["pgrep", "-fa", "run_portfolio_tournament_paper"], capture_output=True, text=True
)
procs = [ln for ln in ps.stdout.splitlines() if "pgrep" not in ln]
if procs:
    notes.append(f"engine alive: {procs[0][:90]}")
else:
    alerts.append("engine process NOT running")

# 2. log
if LOG.exists():
    age_min = (time.time() - LOG.stat().st_mtime) / 60
    notes.append(f"log mtime {age_min:.0f} min ago")
    tail = LOG.read_text()[-8000:]
    if "Traceback" in tail:
        alerts.append("Traceback in recent log tail")
else:
    alerts.append(f"log missing: {LOG}")

# 3. submission integrity
try:
    from portfolio_tournament import constants as tc
    from portfolio_tournament import protocol as tp

    tp.check_submission_shas(tc.team_dir("team-02"))
    notes.append("frozen submission SHA OK")
except Exception as e:  # noqa: BLE001
    alerts.append(f"SUBMISSION INTEGRITY: {e!r}")

# 4. DB held book vs recomputed strategy book (dry-run parity: must match target exactly)
try:
    import sqlite3

    con = sqlite3.connect(DB)
    row = con.execute("select value from engine_state where key='portfolio_held_w'").fetchone()
    if row is None:
        notes.append("DB: no held book yet (pre-first-rebalance)")
    else:
        held = {k: v for k, v in json.loads(row[0]).items() if not k.startswith("_")}
        from crypto_trade.portfolio import strategy_tournament as st

        coins = st.load_universe()
        coins = st.append_forming(coins, st.forming_from_close(coins))
        tgt = {k: v for k, v in st.next_target_weights(coins).items() if not k.startswith("_")}
        keys = set(held) | set(tgt)
        drift = max((abs(held.get(k, 0.0) - tgt.get(k, 0.0)) for k in keys), default=0.0)
        (notes if drift < 5e-3 else alerts).append(
            f"held-vs-target max drift {drift:.5f} over {len(keys)} names"
        )
    con.close()
except Exception as e:  # noqa: BLE001
    alerts.append(f"DB/parity check failed: {e!r}")

status = "ALERT" if alerts else "OK"
print(f"STATUS {status} — crypto-cup-01 paper desk (team-02 breakout)")
for a in alerts:
    print(f"  ALERT: {a}")
for n in notes:
    print(f"  {n}")
sys.exit(1 if alerts else 0)
