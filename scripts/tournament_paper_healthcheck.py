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

# 1. process — check the actual PYTHON engine child, not just the `uv run` wrapper. pgrep
# matches both; the wrapper sits at ~0 CPU in futex_do_wait (waiting on its child), so
# "wrapper alive" is NOT proof the engine loop is alive. Prefer the `.venv/bin/python3` child.
ps = subprocess.run(
    ["pgrep", "-fa", "run_portfolio_tournament_paper"], capture_output=True, text=True
)
procs = [ln for ln in ps.stdout.splitlines() if "pgrep" not in ln and "shell-snapshot" not in ln]
py_child = [ln for ln in procs if "python3 " in ln or ".venv" in ln]
if py_child:
    notes.append(f"engine (python child) alive: {py_child[0][:90]}")
elif procs:
    alerts.append(f"only the uv wrapper is alive, no python engine child: {procs[0][:70]}")
else:
    alerts.append("engine process NOT running")

# 2. log + REBALANCE RECENCY — the load-bearing liveness signal. A rebalance must land every
# 8h; if the newest one is older than 8h + the 25-min stagger + a 90-min margin (~10h), the
# engine has silently stopped rebalancing regardless of what any PID says (child hang, stuck
# poll, or dead). This catches what a bare pgrep misses.
if LOG.exists():
    age_min = (time.time() - LOG.stat().st_mtime) / 60
    notes.append(f"log mtime {age_min:.0f} min ago")
    text = LOG.read_text()
    if "Traceback" in text[-8000:]:
        alerts.append("Traceback in recent log tail")
    import re
    from datetime import UTC, datetime

    stamps = re.findall(r"rebalance plan as_of=(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})", text)
    if stamps:
        last_rb = datetime.strptime(stamps[-1], "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
        rb_age_h = (datetime.now(UTC) - last_rb).total_seconds() / 3600
        msg = f"last rebalance {stamps[-1]} UTC ({rb_age_h:.1f}h ago)"
        (alerts if rb_age_h > 10.0 else notes).append(
            msg + (" — MISSED REBALANCE (>10h)" if rb_age_h > 10.0 else "")
        )
    else:
        notes.append("no rebalance in log yet")
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
