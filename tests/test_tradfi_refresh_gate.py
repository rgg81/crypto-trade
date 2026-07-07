"""Regression test for the TradFi paper engine's NEW-CANDLE-GATE deadlock
(analysis/portfolio/tradfi/live_tradfi.py).

THE BUG (confirmed live — 1d14h frozen desk):
  The OLD poll loop was ``while True: if self._new_candle_due(): self.run_once()``. ``run_once`` is
  the ONLY caller of ``refresh_data`` (the on-disk pull). But ``_new_candle_due`` reads each
  universe CSV's LAST on-disk bar, and the on-disk data only advances via ``refresh_data``. So once
  the engine processed the latest on-disk bar (``_latest_settled_ms() == tradfi_last_candle``), the
  gate returned False FOREVER → ``refresh_data`` never ran → the next settled bar that appears on
  yfinance later was never pulled → the desk never rebalanced again (only on a fresh start).

THE FIX (this test guards it):
  ``run()`` refreshes on a TIME cadence via ``_maybe_refresh`` (INDEPENDENT of the gate) and only
  THEN gates the REBALANCE on the now-fresh on-disk data. ``_tick`` is the extracted per-poll step.

Pure-unit: tiny synthetic universe CSVs in a tmp data dir + a tmp DB; ``refresh_data`` is STUBBED to
append the new settled bar (mimicking yfinance getting a new day) — NO network. ``run_once`` is
stubbed to a FAITHFUL mini-rebalance that advances ``tradfi_last_candle`` to whatever settled bar is
on disk (exactly what the real ``run_once`` persists), so the state advance is genuinely DRIVEN by
the refresh having happened.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

_TF = Path(__file__).resolve().parents[1] / "analysis" / "portfolio" / "tradfi"
_SRC = Path(__file__).resolve().parents[1] / "src"
for _p in (str(_TF), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import live_tradfi as lt  # noqa: E402
import universe_tradfi as ut  # noqa: E402

DAY_MS = 86_400_000
# _latest_settled_ms iterates SECTOR_MAP and reads <data_dir>/<KEY>/1d.csv — use 3 real keys.
_KEYS = list(ut.SECTOR_MAP)[:3]


# ------------------------------------------------------------------ synthetic-data helpers -------
def _write_universe_csv(data_dir: Path, sym: str, open_times: list[int]) -> None:
    d = data_dir / sym
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "1d.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["open_time", "open", "high", "low", "close", "volume"])
        for ot in open_times:
            w.writerow([ot, 100.0, 100.0, 100.0, 100.0, 0.0])


def _append_universe_bar(data_dir: Path, sym: str, open_time: int) -> None:
    with open(data_dir / sym / "1d.csv", "a", newline="") as f:
        csv.writer(f).writerow([open_time, 100.0, 100.0, 100.0, 100.0, 0.0])


def _caught_up_engine(tmp_path: Path) -> tuple[lt.TradfiPaperEngine, int, int, dict]:
    """Build an engine CAUGHT UP at settled bar N: universe CSVs' last bar = N, DB
    ``tradfi_last_candle`` = N (so ``_new_candle_due()`` is initially False — the deadlock
    precondition). Returns ``(engine, bar_n, bar_np1, calls)``.

    Both bar_n and bar_np1 are strictly < today UTC (both SETTLED), with bar_np1 > bar_n — the new
    day that yfinance will publish. ``refresh_data`` is stubbed to append bar_np1 to the on-disk
    universe CSVs (mimics a new settled yfinance bar); ``run_once`` is stubbed to a faithful
    mini-rebalance (advance ``tradfi_last_candle`` to the newest on-disk settled bar).
    """
    cfg = lt.TradfiPaperConfig(
        db_path=str(tmp_path / "paper.db"),
        live_data_dir=str(tmp_path / "live"),
        funding_dir=str(tmp_path / "fund"),
        data_dir=str(tmp_path / "data"),
        equity_csv=str(tmp_path / "eq.csv"),
    )
    eng = lt.TradfiPaperEngine(cfg)
    data_dir = Path(cfg.data_dir)

    today_ms = eng._today_ms()
    bar_n = today_ms - 3 * DAY_MS  # settled (date < today)
    bar_np1 = today_ms - 1 * DAY_MS  # a NEWER settled bar (date < today), > bar_n

    for sym in _KEYS:
        _write_universe_csv(data_dir, sym, [bar_n - DAY_MS, bar_n])  # last on-disk bar = N
    eng.store.set_state("tradfi_last_candle", str(bar_n))  # engine has already processed N

    calls: dict = {"refresh": 0, "run_once": 0, "run_once_refresh": None}

    def _fake_refresh() -> None:
        # Mimic yfinance getting the next settled bar: append N+1 to every on-disk universe CSV.
        calls["refresh"] += 1
        for sym in _KEYS:
            _append_universe_bar(data_dir, sym, bar_np1)

    def _fake_run_once(*, refresh: bool = True) -> dict | None:
        # Faithful mini-rebalance: advance tradfi_last_candle to the newest SETTLED on-disk bar,
        # exactly as the real run_once persists (set_state("tradfi_last_candle", as_of_ms)). The
        # advance is DRIVEN by the refresh — if the refresh never ran, _latest_settled_ms stays N.
        calls["run_once"] += 1
        calls["run_once_refresh"] = refresh
        settled = eng._latest_settled_ms()
        if settled is None:
            return None
        eng.store.set_state("tradfi_last_candle", str(settled))
        return {"as_of_ms": settled}

    eng.refresh_data = _fake_refresh  # type: ignore[method-assign]
    eng.run_once = _fake_run_once  # type: ignore[method-assign]
    return eng, bar_n, bar_np1, calls


# ------------------------------------------------------------------ 1. the FIX ------------------
def test_tick_refreshes_then_rebalances_new_bar(tmp_path):
    """After the fix: one poll tick refreshes on the cadence (stamp is None → force), pulling the
    new settled bar N+1, THEN the gate flips True and the engine rebalances — advancing
    ``tradfi_last_candle`` to N+1. This is the exact scenario that deadlocked live.

    FAILS on the OLD gated code (``_tick`` does not exist → AttributeError; and even a gate-first
    ``_tick`` would leave ``tradfi_last_candle`` stuck at N — see the companion deadlock test).
    """
    eng, bar_n, bar_np1, calls = _caught_up_engine(tmp_path)

    # Precondition — the engine is caught up at N, so the OLD gate is False (would never refresh).
    assert eng._new_candle_due() is False
    assert eng._latest_settled_ms() == bar_n

    result = eng._tick()  # ← the refactored refresh-then-gate poll step

    # (1) it refreshed the on-disk data INDEPENDENTLY of the gate ...
    assert calls["refresh"] == 1
    # (2) ... which advanced the on-disk universe to N+1, so the gate flipped True ...
    assert eng._latest_settled_ms() == bar_np1
    # (3) ... and it rebalanced: run_once dispatched with refresh=False (no double pull) ...
    assert calls["run_once"] == 1
    assert calls["run_once_refresh"] is False
    # (4) ... advancing the processed-bar state from N to N+1. THE DEADLOCK IS BROKEN.
    assert result is not None
    assert int(eng.store.get_state("tradfi_last_candle")) == bar_np1


# ------------------------------------------------------------------ 2. root-cause doc -----------
def test_old_gate_before_refresh_would_deadlock(tmp_path):
    """Documents the ROOT CAUSE (invariant on old + new code): the OLD ordering — gate FIRST,
    refresh ONLY inside the gated ``run_once`` — deadlocks a caught-up desk. The gate reads the last
    on-disk bar and the on-disk bar only advances via a refresh that the gate itself blocks, the
    refresh never fires and the state is stuck at N forever."""
    eng, bar_n, bar_np1, calls = _caught_up_engine(tmp_path)

    # Replicate the OLD loop body EXACTLY: ``if self._new_candle_due(): self.run_once()``.
    if eng._new_candle_due():
        eng.run_once()

    # Gate was False → run_once (the only refresher) never ran → nothing advanced. DEADLOCK.
    assert calls["refresh"] == 0
    assert calls["run_once"] == 0
    assert eng._latest_settled_ms() == bar_n
    assert int(eng.store.get_state("tradfi_last_candle")) == bar_n


# ------------------------------------------------------------------ 3. cadence gating -----------
def test_refresh_is_time_cadenced_not_every_poll(tmp_path):
    """The refresh must NOT run on every 60s poll (that would hammer the 69-name yfinance pull). The
    startup tick refreshes (stamp None → force); an immediate second poll tick must NOT refresh
    again (cadence not elapsed), but a tick after the interval has elapsed must."""
    eng, bar_n, bar_np1, calls = _caught_up_engine(tmp_path)

    eng._tick()  # startup tick — refreshes (stamp was None)
    assert calls["refresh"] == 1

    eng._tick()  # immediate next poll — cadence not elapsed → NO refresh
    assert calls["refresh"] == 1

    # Simulate the cadence window elapsing, then a tick DOES refresh again.
    eng._last_refresh_monotonic -= eng.cfg.refresh_interval_seconds + 1
    eng._tick()
    assert calls["refresh"] == 2


# ------------------------------------------------------------------ 4. today's bar unsettled ----
def test_unsettled_today_bar_is_not_due(tmp_path):
    """Settled-bar semantics are unchanged: ``_latest_settled_ms`` is a TAIL read
    (``read_last_open_time``) that drops the tail bar when its UTC date == today. So appending
    today's (unsettled) bar must NOT make ``_new_candle_due()`` fire — the gate only rebalances on a
    genuinely settled new day."""
    eng, bar_n, bar_np1, calls = _caught_up_engine(tmp_path)
    today_ms = eng._today_ms()
    for sym in _KEYS:
        _append_universe_bar(Path(eng.cfg.data_dir), sym, today_ms)  # tail bar = today (unsettled)
    # Tail is today → dropped by the ``ot < today_ms`` guard → no settled bar visible at the tail.
    assert eng._latest_settled_ms() is None
    # ... so the gate does NOT fire on today's unsettled bar (settled-bar discipline intact).
    assert eng._new_candle_due() is False
