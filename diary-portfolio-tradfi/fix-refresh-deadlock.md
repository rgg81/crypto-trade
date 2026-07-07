# Fix — TradFi paper engine new-candle-gate DEADLOCK

**Date:** 2026-07-07 · **Scope:** `analysis/portfolio/tradfi/live_tradfi.py` refresh scheduling only.
**Verdict:** real deadlock, confirmed live (1d14h frozen desk) — FIXED + regression-guarded.

## The bug (confirmed live)
The poll loop was `while True: if self._new_candle_due(): self.run_once()`. `run_once` is the ONLY
caller of `refresh_data()` (the heavy 69-name Yahoo + perp + funding pull). But the gate
`_new_candle_due()` → `_latest_settled_ms()` reads each universe CSV's LAST on-disk bar via
`read_last_open_time`, and the on-disk data only advances **inside** `refresh_data()`.

So the refresh was gated behind the very quantity it was responsible for advancing. Once the engine
processed the latest on-disk bar (`_latest_settled_ms() == tradfi_last_candle`), the gate returned
`False` **forever** → `refresh_data()` never ran → the next settled yfinance bar was never pulled →
the desk never rebalanced again. It only advanced on a fresh start (which force-refreshed via the
first-run seed path). Observed: engine idle 1d14h, on-disk stuck at 07-02 while yfinance already had
the settled 07-06 bar; log silent (start banner only) the whole time; no `[rebal]` line.

## The fix — decouple the data refresh from the rebalance gate
Refresh on a **time cadence**, independent of `_new_candle_due()`; then gate only the **rebalance**
on the now-fresh on-disk data.

- **New config field** `TradfiPaperConfig.refresh_interval_seconds: int = 1800` (30 min). NOT every
  60s poll — `refresh_data()` is a heavy full pull and a per-tick pull would hammer/rate-limit
  yfinance. 30 min catches the ~00:00-UTC daily settlement fast enough for a daily-rebalance desk.
- **`_maybe_refresh(force=False) -> bool`**: refreshes iff `force`, or never-refreshed, or
  `monotonic_now - last_refresh >= refresh_interval_seconds`. Uses `time.monotonic()` (immune to
  wall-clock jumps / NTP steps), NOT wall-clock. Wraps `refresh_data()` in try/except so a transient
  source hiccup never kills the loop; the monotonic stamp advances regardless, so a persistently
  failing source is not re-hit every 60s. Returns whether it refreshed this call.
- **`_tick(force_refresh=False) -> dict | None`** (extracted per-poll step, unit-testable):
  `refreshed = _maybe_refresh(force=force_refresh)`; then `if _new_candle_due(): run_once(refresh=not
  refreshed)`. When this tick already refreshed → `run_once(refresh=False)` (no double pull);
  otherwise `run_once` keeps its default `refresh=True` so nothing else that relies on that default
  breaks.
- **`run()`** now: calls `_tick(force_refresh=True)` ONCE at startup (before the first gate check) so
  a RESUMED engine caught up at bar N immediately pulls N+1 and rebalances — this also fixes the
  resume-deadlock case — then loops `_tick()` on the 60s poll with the 30-min cadenced refresh.
  KeyboardInterrupt / tick-error handling preserved.

Settled-bar semantics UNCHANGED: `_latest_settled_ms` still tail-reads on-disk and drops a tail bar
whose UTC date == today (`ot < today_ms`). No trading-calendar/holiday logic added — yfinance only
returns real trading-day bars, so refresh + read-what's-there is automatically calendar-correct (the
July-4th week correctly had no 07-03/04/05 bars). Splice loader wiring, exec-model
(quantization/funding), parity vs live, and `tradfi_held_w` continuity are all untouched — this is
purely a refresh-scheduling fix.

## Regression test — `tests/test_tradfi_refresh_gate.py` (NEW, 4 tests)
Pure-unit, tmp data dir + tmp DB, NO network (`refresh_data` stubbed). Engine caught up at bar N
(universe CSVs' last bar = N; DB `tradfi_last_candle = N` ⇒ `_new_candle_due()` initially False).
Stubbed `refresh_data` appends N+1 to the on-disk CSVs (mimics a new settled yfinance bar); stubbed
`run_once` is a faithful mini-rebalance that advances `tradfi_last_candle` to the newest settled
on-disk bar (exactly what the real `run_once` persists), so the advance is genuinely DRIVEN by the
refresh having happened.

- `test_tick_refreshes_then_rebalances_new_bar` (primary): one `_tick()` → refresh ran, on-disk
  advanced to N+1, gate flipped True, `run_once` dispatched with `refresh=False`, and
  `tradfi_last_candle` advanced N → N+1. Key assertion:
  `int(eng.store.get_state("tradfi_last_candle")) == bar_np1`.
- `test_old_gate_before_refresh_would_deadlock`: replicates the OLD `if _new_candle_due():
  run_once()` body — gate False → refresh never fires → state stuck at N. Documents the root cause.
- `test_refresh_is_time_cadenced_not_every_poll`: startup tick refreshes; immediate 2nd poll does
  NOT (cadence not elapsed); a tick after the interval elapses DOES. Guards against per-poll hammer.
- `test_unsettled_today_bar_is_not_due`: appending today's (unsettled) tail bar leaves
  `_latest_settled_ms() is None` and `_new_candle_due() is False` — settled-bar discipline intact.

**Before/after proof:** ran the primary scenario against the ORIGINAL file (git HEAD, extracted via
`git show`) driving the OLD loop body — the FIX assertion `tradfi_last_candle == N+1` FAILS
(`_tick` absent; state stuck at N=1783123200000, N+1=1783296000000, refresh calls=0). After the fix,
the 4 new tests + the 4 existing `test_tradfi_paper_engine.py` tests all pass (8 passed). Ruff clean
on both touched files.
