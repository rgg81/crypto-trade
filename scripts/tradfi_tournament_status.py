"""tradfi-cup-01 WINNER paper-desk STATUS — per-tick alert check + compact digest line.

READ-ONLY. Mirrors scripts/tradfi_status.py for the tournament desk (team-10 per-name 12m
sign trend on the 65-name tournament universe, DAILY rebalance, dual PARITY/LIVE paper P&L):

  STATUS  : (a) engine alive (`ps` has a real `python … run_tradfi_tournament_paper.py`),
            (b) no Traceback in the last ~400 log lines,
            (c) MISSED rebalance — a NEW settled bar exists but `tradfi_last_candle` lags it.
  BUNDLE  : frozen team-10 sources re-hash against submission.json (post-freeze mutation of
            the deployed strategy is an alert, not a curiosity).
  PARITY  : recompute the team-10 target book at `tradfi_last_candle` through the SAME code
            path the engine uses (frozen-IS-canon spliced panel -> frozen build_raw_weights
            -> organizer caps), drop LIVE_EXCLUDED, compare per-name to the held book.
  CANDLE  : `tradfi_last_candle` strictly < today UTC (no forming-bar look-ahead).
  OBS     : equity parity/live, basis gap, cum funding, held gross/net — observational only.

Exit 0 = all OK; exit 1 = an alert fired.   Run: uv run python scripts/tradfi_tournament_status.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT / "src"), str(_ROOT / "analysis" / "portfolio" / "tradfi")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from live_tradfi import LIVE_EXCLUDED  # noqa: E402
from tournament import constants as tc  # noqa: E402
from tournament import protocol as tp  # noqa: E402
from tournament.paper import settled_scaled_book  # noqa: E402 — SAME code path as the desk

from crypto_trade.live.state_store import StateStore  # noqa: E402

DB = _ROOT / "data" / "tradfi_tournament_paper.db"
LOG = _ROOT / "logs" / "tradfi_tournament_paper.log"
RUNNER = "run_tradfi_tournament_paper.py"
TEAM = "team-10"
PARITY_TOL = 1e-6
_BAD = ("grep", "pgrep", "bash -c", "/bin/sh", "tradfi_status", "tradfi_tournament_status")


def _alive() -> bool:
    out = subprocess.run(["ps", "-eo", "args"], capture_output=True, text=True).stdout
    return any(
        RUNNER in ln and "python" in ln and not any(b in ln for b in _BAD)
        for ln in out.splitlines()
    )


def _traceback_in_log() -> bool:
    if not LOG.exists():
        return False
    return any("Traceback" in ln for ln in LOG.read_text(errors="ignore").splitlines()[-400:])


def _today_ms() -> int:
    return int(pd.Timestamp.now("UTC").normalize().value // 1_000_000)


def main() -> int:
    alerts: list[str] = []
    flags: list[str] = []

    if not _alive():
        alerts.append(f"engine DOWN ({RUNNER} not running)")
    if _traceback_in_log():
        alerts.append(f"TRACEBACK in {LOG.relative_to(_ROOT)}")
    try:
        tp.check_submission_shas(tc.team_dir(TEAM))
    except Exception as e:  # noqa: BLE001
        alerts.append(f"BUNDLE mutated: {e}")

    if not DB.exists():
        flags.append("no DB yet (engine never launched)")
        _emit(alerts, flags, None)
        return 1 if alerts else 0

    st = StateStore(DB)
    last = st.get_state("tradfi_last_candle")
    eq_p = st.get_state("tradfi_equity_parity")
    eq_l = st.get_state("tradfi_equity_live")
    fund = st.get_state("tradfi_funding_cum")
    held = json.loads(st.get_state("tradfi_held_w") or "{}")

    obs = None
    if last is not None:
        last_ms = int(last)
        today = _today_ms()
        if last_ms >= today:
            alerts.append("CANDLE look-ahead: last_candle >= today UTC")

        # settled panel + VOL-SCALED target recompute — the desk's own code path, shared
        _net, w = settled_scaled_book(tc.team_dir(TEAM), today_ms=today)
        if w is None:
            flags.append("no settled data on recompute")
            _emit(alerts, flags, None)
            return 1 if alerts else 0

        settled_ms = int(w.index[-1].value // 1_000_000)
        if settled_ms > last_ms:
            behind = (settled_ms - last_ms) // 86_400_000
            alerts.append(f"MISSED rebalance: settled bar {behind}d ahead of last_candle")

        ts_last = pd.Timestamp(last_ms, unit="ms")
        if ts_last in w.index:
            target = {
                k: float(v)
                for k, v in w.loc[ts_last].items()
                if k not in LIVE_EXCLUDED and abs(v) > 0
            }
            names = set(target) | set(held)
            drift = max((abs(target.get(n, 0.0) - held.get(n, 0.0)) for n in names), default=0.0)
            if drift > PARITY_TOL:
                alerts.append(f"PARITY drift: max|held-target| = {drift:.2e}")
        else:
            flags.append("last_candle not on recomputed grid (catch-up in progress?)")

        gross = sum(abs(v) for v in held.values())
        net = sum(held.values())
        basis_bps = (
            (float(eq_l) - float(eq_p)) / float(eq_p) * 1e4 if eq_p and float(eq_p) else 0.0
        )
        obs = (
            f"as_of={ts_last.date()}  eq_parity=${float(eq_p or 0):,.0f}  "
            f"eq_live=${float(eq_l or 0):,.0f}  basis={basis_bps:+.0f}bps  "
            f"cum_fund=${float(fund or 0):,.2f}  held: n={len(held)} gross={gross:.3f} "
            f"net={net:+.3f}"
        )
    else:
        flags.append("no rebalance yet (tradfi_last_candle unset)")

    _emit(alerts, flags, obs)
    return 1 if alerts else 0


def _emit(alerts: list[str], flags: list[str], obs: str | None) -> None:
    verdict = "ALERT" if alerts else "OK"
    print(f"[tournament-desk] STATUS {verdict}")
    for a in alerts:
        print(f"  ALERT: {a}")
    for f in flags:
        print(f"  flag : {f}")
    if obs:
        print(f"  obs  : {obs}")


if __name__ == "__main__":
    raise SystemExit(main())
