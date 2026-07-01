"""Unit tests for the tradfi paper-desk monitor pure logic (READ-ONLY, no network, no DB).

Covers the three load-bearing decision helpers in ``scripts/tradfi_status.py``:
  1. ``_engine_up_from_ps`` — string-matching a real ``python … run_tradfi_paper.py`` while
     rejecting grep / self-monitor / ``bash -c`` wrapper lines that merely MENTION the runner.
  2. ``_missed_rebalance`` — on-disk-data-freshness rule: a settled bar strictly ahead of the last
     processed one FIRES; a weekend (no new settled bar) does NOT; first run (last=None) does NOT.
  3. ``_parity_drift`` — the PAYP exclusion: a held book without PAYP does NOT drift against a raw
     target that still carries PAYP (exclusion applied) but DOES if PAYP is not excluded.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
for _p in (str(_ROOT / "src"), str(_ROOT / "analysis" / "portfolio" / "tradfi")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Load scripts/tradfi_status.py by path (scripts/ is not an importable package).
_spec = importlib.util.spec_from_file_location(
    "tradfi_status", str(_ROOT / "scripts" / "tradfi_status.py")
)
tradfi_status = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tradfi_status)


# ── 1. engine-liveness string matching ──────────────────────────────────────────────────────────
def test_engine_up_matches_real_runner():
    ps = (
        "PID TTY  CMD\n"
        "/usr/bin/python /home/x/.worktrees/portfolio-tradfi/run_tradfi_paper.py\n"
        "-bash\n"
    )
    assert tradfi_status._engine_up_from_ps(ps) is True


def test_engine_up_matches_uv_run_python():
    ps = "python run_tradfi_paper.py\n"
    assert tradfi_status._engine_up_from_ps(ps) is True


def test_engine_up_rejects_grep_line():
    ps = "grep run_tradfi_paper.py\ngrep --color=auto run_tradfi_paper.py\n"
    assert tradfi_status._engine_up_from_ps(ps) is False


def test_engine_up_rejects_bash_c_and_self_monitor():
    ps = (
        "bash -c 'python scripts/tradfi_status.py; ps -eo args | grep run_tradfi_paper.py'\n"
        "python scripts/tradfi_status.py\n"
        "python scripts/tradfi_digest.py --mark-pushed\n"
    )
    assert tradfi_status._engine_up_from_ps(ps) is False


def test_engine_up_false_when_absent():
    assert tradfi_status._engine_up_from_ps("-bash\nsshd: roberto\n") is False


# ── 2. MISSED-rebalance on-disk-data-freshness rule ─────────────────────────────────────────────
_WED = 1782777600000  # 2026-06-30 (a settled trading-day bar, ms open_time)
_THU = _WED + 86_400_000  # next trading day's settled bar


def test_missed_fires_when_settled_bar_ahead_on_trading_day():
    # A new settled bar landed on disk but last_candle is stuck one trading day behind → MISSED.
    assert tradfi_status._missed_rebalance(_WED, _THU) is True


def test_missed_does_not_fire_on_weekend_no_new_bar():
    # Weekend / holiday: no new settled Yahoo bar appears, so settled == last → NOT missed.
    assert tradfi_status._missed_rebalance(_WED, _WED) is False


def test_missed_does_not_fire_on_first_run_or_missing_data():
    assert tradfi_status._missed_rebalance(None, _THU) is False  # engine never ran
    assert tradfi_status._missed_rebalance(_WED, None) is False  # no settled data on disk


# ── 3. PARITY recompute applies the PAYP exclusion ──────────────────────────────────────────────
def test_parity_no_drift_when_payp_excluded():
    held = {"AAPLUSDT": 0.02, "MSFTUSDT": -0.01}  # LIVE book never carries PAYP
    target = {"AAPLUSDT": 0.02, "MSFTUSDT": -0.01, "PAYPUSDT": 0.03, "_meta": {"gross": 1.0}}
    # Default excluded = LIVE_EXCLUDED ({PAYPUSDT}) → PAYP dropped from target → no drift.
    assert tradfi_status._parity_drift(held, target) == []


def test_parity_drift_when_payp_not_excluded():
    held = {"AAPLUSDT": 0.02, "MSFTUSDT": -0.01}
    target = {"AAPLUSDT": 0.02, "MSFTUSDT": -0.01, "PAYPUSDT": 0.03, "_meta": {"gross": 1.0}}
    # Without the exclusion, PAYP (held 0 vs target +0.03) shows as drift → proves exclusion works.
    drift = tradfi_status._parity_drift(held, target, excluded=frozenset())
    assert len(drift) == 1 and "PAYPUSDT" in drift[0]


def test_parity_drift_detects_a_real_weight_mismatch():
    held = {"AAPLUSDT": 0.02, "MSFTUSDT": -0.01}
    target = {"AAPLUSDT": 0.05, "MSFTUSDT": -0.01, "_meta": {}}  # AAPL diverged
    drift = tradfi_status._parity_drift(held, target)
    assert len(drift) == 1 and "AAPLUSDT" in drift[0]
