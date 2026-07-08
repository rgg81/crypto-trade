# TradFi Monitor — live watch on the tradfi PAPER desk

## Operating principle (read first)
**This skill is the canonical home for ALL monitoring + assistant intelligence on the TRADFI paper
desk.** Every improvement — a new health signal, a smarter check, an auto-recovery playbook — lands
HERE (this file + helper scripts `scripts/tradfi_status.py` / `scripts/tradfi_digest.py`), gets
committed, and is logged in the Changelog. Keep helper logic in the committed scripts (testable, see
`tests/test_tradfi_monitor.py`); keep this file the index + playbook. This is the sibling of
`metals-monitor` (the metals paper desk) — same HANDS-OFF philosophy, adapted for the tradfi desk's
DAILY cadence, dual P&L, and funding carry.

## What's being watched
The **tradfi paper-trading desk** (`run_tradfi_paper.py`): the confirmed **iter-016 BEAR-GATED
TSMOM** book on **68 Binance single-stock TradFi perps** (the 69-name `SECTOR_MAP` universe **minus
PAYP**), **DAILY US-trading-day rebalance**, **PAPER mode only** — no exchange, no real orders. Two
P&L tracks are booked each settled bar:

- **PARITY** — the Yahoo total-return backtest net compounded since launch (the book of record; all
  names; the anchor the desk is validated on). Signals are parity-by-construction with the backtest
  (same `champ.deployed_weights` on the same Yahoo TR history — recompute-from-full-history, no
  stored position state to drift).
- **LIVE** — the SAME deployed weights scored on Binance perp returns MINUS funding MINUS turnover,
  coverage-aware (a name with no perp bar / no funding that day contributes 0). `basis_gap =
  equity_live − equity_parity`.

State: `data/tradfi_paper.db` (SQLite `StateStore`), equity curve `data/tradfi_equity.csv`, log
`logs/tradfi_paper.log`. Signal data: `data/<SYM>/1d.csv` (Yahoo TR). Perp marks:
`data_live_tradfi/<PERP>/1d.csv`. Funding: `data/funding_rates/<PERP>.csv`.

## Strategy facts (for context — do NOT re-derive)
- iter-016 = one change vs iter-015: gate the directional TSMOM sleeve to 0 in the EW-252d
  bear-state (`lam_eff = 0.25·(1−g)`, `g = 1{EW-universe trailing-252d return < 0}`), ZERO new
  params. IS net Sharpe **+0.73**, **13/16 positive years**, sector/dollar-near-neutral with a small
  bear-gated net-long β-tilt.
- **Book-level perp+funding tracking** (Phase-2b reconcile): the LIVE perp book tracks the Yahoo-TR
  underlying at **≈ −85 bps** with a **tracking error ≈ 5.8%** at 100% perp coverage.
- **Funding is a CARRY, not a dividend bridge**: net long-premium drag **≈ −0.7%/yr** at book level
  (per-leg funding P&L = `−w·f`; Binance `f>0` ⇒ longs pay). It is a modeled cost of the perp book,
  not a corporate-action reconciliation.
- **Funding AUDIT (verified 2026-07-08; the digest now shows the split each report):**
  1. **Source = PRODUCTION public fapi** — `data/funding_rates/<PERP>.csv` via
     `crypto_trade.portfolio.funding.refresh_funding` @ `https://fapi.binance.com/fapi/v1/fundingRate`.
     NEVER testnet (no testnet ref anywhere in the funding path). Same helper the engine reuses.
  2. **Direction = `−w·f`, correct** — `f>0` ⇒ long pays / short earns; `f<0` ⇒ long earns / short
     pays (Binance convention). Verified in code (`reconcile_basis_tradfi` lines 11/127/192/238, and
     `live_tradfi._live_returns` reuses `rc.daily_funding`) and by per-leg example.
  3. **NOT net-zero, and that's EXPECTED** — measured gross **long-leg ≈ −1.5%/yr** (pay) vs
     **short-leg ≈ +0.8%/yr** (earn) ⇒ **NET ≈ −0.76%/yr**. Two real reasons it doesn't cancel: the
     book is **net-long ~10–13%** (bear-gated TSMOM tilt, not perfectly dollar-neutral), and the perps'
     retail-long-premium funding is **asymmetric** (longs pay more than shorts earn). A small negative
     NET is correct, **not a bug**. This carry is **NOT in the backtest** (Yahoo TR) — the LIVE track
     models it. **Re-check** the gross-long/short/NET split (in the digest, or
     `reconcile_basis_tradfi.funding_drag`) after any big regime/net-long-tilt shift; a NET that swings
     large-positive or large-negative (beyond ±~2%/yr) would be worth investigating.
- **PAYP is EXCLUDED** (`LIVE_EXCLUDED = {PAYPUSDT}`) — a broken PayPal perp (perp ~$14 vs PayPal
  ~$43, corr 0.19: a perp-venue decoupling / ticker mismap). Dropped from the LIVE book and **NOT
  re-normalized** (every other name keeps its exact backtest weight; the tiny gross drift is the
  documented cost). **The monitor applies the SAME exclusion** or it would false-DRIFT on PAYP.

## HANDS-OFF MANDATE — never interfere with the strategy
We are TESTING the strategy. It runs UNTOUCHED through wins AND losses.
- **NEVER** alter positions in response to performance. There is no kill-switch to invoke (paper).
- **Drawdown / PnL / basis / funding / regime / turnover are TEST RESULTS, not alerts** — they are
  printed (the FUNDING/BASIS line in status; the full digest) so the operator SEES them, but they are
  never acted on.
- The ONLY alerts are **TEST-INTEGRITY** failures — the test isn't running, or the paper book
  stopped tracking the backtest: **engine DOWN**, **Traceback**, **MISSED rebalance**,
  **PARITY=DRIFT**, **CANDLE=BAD** (look-ahead). Relaunching a crashed engine is PRO-test (it
  recomputes the target + resumes from `tradfi_last_candle` — self-tracking) — allowed, not
  interference.

## How to run a check (per tick)
```
cd /home/roberto/crypto-trade/.worktrees/portfolio-tradfi \
  && export PATH="$HOME/.local/bin:$PATH" \
  && uv run python scripts/tradfi_status.py | grep -vE "findfont|Arial" \
  && uv run python scripts/tradfi_digest.py | grep -vE "findfont|Arial"
```
Both are READ-ONLY (read the DB / equity CSV / log + recompute the strategy target). `tradfi_digest.py
--mark-pushed` writes ONE bookkeeping key (`tradfi_digest_last_pushed`) — the only permitted write;
it never touches the trade/rebalance path. Filter matplotlib noise with `| grep -vE "findfont|Arial"`.
- `tradfi_status.py` → `STATUS: OK|ALERT` (engine alive + no traceback + not-behind) + `parity=OK|
  DRIFT` (held book vs recomputed iter-016 target ex-PAYP, at the bar the book was built for) +
  `candle=OK|BAD` (no look-ahead) + a FUNDING/BASIS observational line. **The only alert source.**
  Exit 1 if any alert.
- `tradfi_digest.py` → both equity tracks (since-launch + since-last-rebalance), basis_gap (bps),
  funding carry + the **gross long-leg/short-leg/NET funding split** (direction + source audit),
  bear-gate regime, held book (per-name weight + $ exposure, long/short, top legs).
  `REPORT_DUE: yes` on a new rebalance OR the first report of a new UTC day. **Observational.**

## ALERT conditions (investigate → fix if safe → notify)
- **engine DOWN** — `run_tradfi_paper.py` not running → relaunch (below) + notify.
- **TRACEBACK** in the log → read the tail, diagnose.
- **MISSED rebalance** — a NEW SETTLED Yahoo daily bar exists on disk (date < today UTC) but
  `tradfi_last_candle` hasn't advanced to it. The rule is **on-disk-data-freshness** (reuses the
  engine's own `_latest_settled_ms()` / `_today_ms()`), so it fires only when a genuinely new settled
  trading-day bar has landed unprocessed — the data refresh is stuck or a traceback killed the tick.
- **PARITY=DRIFT** — the held paper book diverges from the recomputed iter-016 target (ex-PAYP). In
  PAPER the fill is exact, so steady-state parity ≈ 0; a DRIFT means the engine persisted the wrong
  book or the champion code/data changed under it. The core correctness alarm.
- **CANDLE=BAD** — `tradfi_last_candle >= today UTC`, i.e. a forming/unsettled daily bar leaked into
  the book (look-ahead). The engine truncates to `date < today`; a BAD here means that guard failed.

## BENIGN — do NOT alert
- **Weekend / US-holiday with no new Yahoo bar is NORMAL.** The perp trades 24/7 but the SIGNAL only
  updates on settled US trading days, so `settled == last_candle` and MISSED correctly stays quiet.
  There is nothing to rebalance until the next US session settles.
- `engine DOWN` immediately after an intentional stop (you stopped it) — only alert on unexpected
  death.
- `data stale` FLAG on a weekday (freshest settled bar > 5d old) — INFORMATIONAL, not an alert; it is
  benign over long holiday weekends and only worth a look if it persists into an active trading week.
- Any equity / basis_gap / funding move, a bull↔bear regime flip, `n_positions` drift as names
  onboard (ragged perp coverage 34→100%) — all TEST RESULTS.

## Response protocol each tick
1. Run both checks.
2. **STATUS=OK** → stay quiet (no ping), reschedule ~3600s out via ScheduleWakeup (pass this monitor
   prompt verbatim so it repeats).
3. **STATUS=ALERT** → read `tail -40 logs/tradfi_paper.log`, diagnose, fix if safe + within these
   patterns (a relaunch is safe + self-tracking), then **PushNotification** the user with what
   happened + what you did. Reschedule.
4. **DIGEST_DUE: yes** → PushNotification the digest block, then `tradfi_digest.py --mark-pushed`.
5. Don't spam: one ping per *state*, not per tick.

## Engine-down recovery (relaunch — safe + self-tracking)
```
cd /home/roberto/crypto-trade/.worktrees/portfolio-tradfi
export PATH="$HOME/.local/bin:$PATH"
PYTHONUNBUFFERED=1 uv run python run_tradfi_paper.py > logs/tradfi_paper.log 2>&1 &
```
On restart the engine recomputes the iter-016 target from full Yahoo history and resumes from the
persisted `tradfi_last_candle` — a relaunch re-tracks the backtest, **no seeding needed**. Ctrl-C is
safe; the DB persists.

> **Flat-start caveat.** For a genuine go-forward start (equity tracks begin flat at the current
> settled bar), delete `data/tradfi_paper.db* data/tradfi_equity.csv` BEFORE the first launch — the
> Phase-2c smoke may have left a **back-dated** `tradfi_launch_candle` row (e.g. launch 2026-06-01),
> which makes since-launch % span a synthetic history rather than the true deploy moment. A relaunch
> that intends to CONTINUE the existing paper track must NOT delete these.

## Self-paced loop
Self-pacing, not a cron. Each tick, after handling the checks, call **ScheduleWakeup** with
`delaySeconds` ~3600 (DAILY rebalances are the events; ~1-hour checks catch a new settled US bar +
liveness) and `prompt` = this monitor instruction verbatim. To STOP, the user says so — then omit
ScheduleWakeup. Keep ~3600s unless asked for tighter/looser.

## Deeper on-demand reconciliation (beyond the per-tick check)
```
uv run python analysis/portfolio/tradfi/reconcile_tradfi.py        # weights bit-exact (recompute==book)
uv run python analysis/portfolio/tradfi/reconcile_basis_tradfi.py  # perp/funding basis (−85 bps book-level)
```
`reconcile_tradfi.py` proves the live recompute reproduces the backtest deployed book bit-for-bit
(parity by construction). `reconcile_basis_tradfi.py` measures the perp-vs-(underlying+funding) basis
+ tracking error — run before trusting a long paper track or before any move toward real capital.

## Key files & facts
- Checks: `scripts/tradfi_status.py` (alerts), `scripts/tradfi_digest.py` (report). Tests:
  `tests/test_tradfi_monitor.py`.
- Runner: `run_tradfi_paper.py` (equity $100k, db `data/tradfi_paper.db`, equity
  `data/tradfi_equity.csv`, log `logs/tradfi_paper.log`).
- Engine: `analysis/portfolio/tradfi/live_tradfi.py` (`TradfiPaperEngine` / `TradfiPaperConfig`,
  `LIVE_EXCLUDED = {PAYPUSDT}`). Parity bridge:
  `analysis/portfolio/tradfi/live_weights_tradfi.py::deployed_target_weights`.
- Champion: iter-016 (`analysis/portfolio/tradfi/iter_016_bear_gated_tsmom.py`). Baseline doc
  `BASELINE_TRADFI.md`.
- State keys: `tradfi_held_w` (JSON {sym: w}), `tradfi_last_candle` (ms settled-bar open_time),
  `tradfi_launch_candle`, `tradfi_equity_parity`, `tradfi_equity_live`, `tradfi_funding_cum`, plus
  the monitor's own `tradfi_digest_last_pushed`.
- **Signal = Yahoo TR** (`data/<SYM>/1d.csv`); **fills = Binance perps** (`data_live_tradfi/`); the
  perp-vs-underlying basis + funding is the LIVE track's modeled drag (already in the dual P&L).
- Going to **real money** (far off): add a Binance TradFi-perp execution path + a forward bear +
  tighten the watch cadence first. Paper is the current scope.

## Changelog
- **2026-07-01 v0** — initial skill: `tradfi_status.py` (STATUS/PARITY/CANDLE test-integrity alerts +
  observational FUNDING/BASIS line) + `tradfi_digest.py` (dual-P&L / basis / funding-carry / bear-gate
  regime / held book, observational, once-a-day or per-rebalance push). HANDS-OFF mandate, on-disk
  MISSED-rebalance rule (weekend-benign, reuses the engine's settled-bar helpers), PAYP exclusion in
  the parity recompute, engine-down relaunch + flat-start caveat, self-paced ScheduleWakeup loop.
  Watches the iter-016 bear-gated TSMOM tradfi paper desk (68 perps ex-PAYP, DAILY, PAPER).
- **2026-07-07 — refresh-deadlock fix** (`9403db90`): the engine gated its data refresh on the on-disk
  bar the refresh advances → a long-running engine went deaf to new bars (only advanced on restart).
  Decoupled: `_maybe_refresh` (30-min cadence + startup force-refresh) then `_new_candle_due` gates
  only the rebalance. Validated in production (07-06→07-07 auto-advanced). Regression test
  `tests/test_tradfi_refresh_gate.py`. If the engine is up but stuck ≥1h past a settled bar, this is
  the class of bug to suspect — check `tail logs/tradfi_paper.log` for a stale refresh.
- **2026-07-08 — funding audit + digest split**: audited the LIVE-only funding (not in the backtest).
  Source = production public fapi (never testnet); direction `−w·f` verified (f>0 ⇒ long pays/short
  earns); NET drag ≈ −0.76%/yr (net-long tilt + asymmetric retail-long-premium funding — expected, not
  a bug, does not net to zero). `tradfi_digest.py` now prints the gross long-leg/short-leg/NET split
  each report (best-effort `_funding_split` → `reconcile_basis_tradfi.funding_drag`). See Strategy
  facts → Funding AUDIT.
