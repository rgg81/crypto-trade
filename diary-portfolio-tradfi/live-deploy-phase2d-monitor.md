# Live-deploy Phase 2d — the TradFi PAPER-desk READ-ONLY MONITOR

The read-only watch layer for the Phase-2c iter-016 paper desk, mirroring the metals monitor
(`portfolio-metals:scripts/metals_status.py` + `metals_digest.py`) and its HANDS-OFF philosophy,
adapted for the tradfi desk's **DAILY** cadence, **dual P&L**, and **funding carry**.

Files (all NEW):
- `scripts/tradfi_status.py` — the per-tick ALERT check (STATUS / PARITY / CANDLE + a FUNDING/BASIS
  observational line). Exit 1 on any test-integrity alert.
- `scripts/tradfi_digest.py` — the OBSERVATIONAL report (dual-P&L, basis, funding carry, bear-gate
  regime, held book). `REPORT_DUE` gating + `--mark-pushed`.
- `.claude/commands/tradfi-monitor.md` — the skill/playbook (canonical home; helper logic lives in the
  scripts, this file is the index + response protocol).
- `tests/test_tradfi_monitor.py` — 11 pure-logic unit tests.

## Design — test-integrity alerts only (HANDS-OFF)
Per the mandate, drawdown / PnL / basis / funding / regime are **TEST RESULTS**, printed but never
acted on. The ONLY alert sources are: **engine DOWN**, **Traceback**, **MISSED rebalance**,
**PARITY=DRIFT**, **CANDLE=BAD**. `tradfi_status.py` exits 1 iff one fires.

### STATUS
- **engine alive** — `_engine_up_from_ps` (pure, tested) matches a real `python … run_tradfi_paper.py`
  ps line while rejecting `grep` / `pgrep` / `bash -c` / `/bin/sh` / `tradfi_status` / `tradfi_digest`
  lines that merely MENTION the runner (the exact metals `_engine_up` guard, retargeted).
- **traceback** — scans the last ~400 lines of `logs/tradfi_paper.log`; a MISSING log is not a
  traceback (the engine is simply down).
- **MISSED rebalance** — see below.

### MISSED rebalance — ON-DISK-DATA-FRESHNESS, not wall-clock
`_missed_rebalance(last_candle, settled_ms)` fires iff `settled_ms > last_candle`, where `settled_ms`
= the engine's OWN `_latest_settled_ms()` (newest universe `data/<SYM>/1d.csv` open_time with UTC date
< today) and `last_candle` = `tradfi_last_candle`. **The monitor reuses the engine's `_latest_settled_ms()`
/ `_today_ms()` helpers directly** so the two can never disagree on "what is the freshest settled bar"
— a divergent rule would cause false MISSED alerts (the exact trap the task warns about).

**Weekends/holidays are benign by construction**: no new settled Yahoo bar appears, so `settled ==
last_candle` and the rule stays False. It fires ONLY when a genuinely new settled trading-day bar has
landed unprocessed (data refresh stuck / tick traceback). This is on-disk freshness, never a clock
comparison — so it does not false-fire over a Sat/Sun/holiday where the perp trades but no US session
settled. Unit-tested both ways (trading-day advance fires; weekend no-new-bar does not; first
run / no-data returns False).

### PARITY — recompute ex-PAYP at the bar the book was built for
`_parity_drift(held, target, excluded=LIVE_EXCLUDED)` recomputes the iter-016 deployed target via
`live_weights_tradfi.deployed_target_weights(as_of, "data")` at `as_of = tradfi_last_candle` (the bar
the held book was actually computed for — NOT the freshest on-disk bar; in steady state they coincide,
and decoupling them keeps a stale-but-correct book from double-alarming as both MISSED and DRIFT).
It pops `_meta`, **DROPS `LIVE_EXCLUDED` (PAYP)**, and compares per-name at tol `1e-6`. **The PAYP
exclusion is load-bearing**: the LIVE held book never carries PAYP, so a raw target that still
contains PAYP must have it dropped or PAYP false-DRIFTs — unit-tested (excluded → no drift; not
excluded → PAYP shows as the one drift).

### CANDLE — look-ahead guard + staleness flag
- **BAD (alert)** iff `tradfi_last_candle >= today UTC` — a forming/unsettled bar leaked into the book
  (the engine truncates to `date < today`; a BAD means that guard failed).
- **stale (FLAG, not alert)** — freshest settled bar > 5 days old on a weekday. Informational; benign
  over long holiday weekends. Never affects the exit code.

### FUNDING/BASIS — observational line (never an alert)
Prints `eq_parity`, `eq_live`, `basis_gap` (bps of the $100k launch notional, matching the engine's
own `[rebal]` bps base → the −81 bps figure), and `funding_cum`. TEST RESULTS the operator sees at a
glance; the full breakdown is in the digest.

## Digest (observational, DAILY-or-per-rebalance push)
Reports both equity tracks (since-launch % + since-last-rebalance %), `basis_gap` (bps), the funding
carry (cum $, % of notional, a rough annualized note), the **bear-gate regime** `g = 1{EW-universe
trailing-252d return < 0}` (recomputed via the champion's own past-only `iter_006.bear_state`), and
the held book (per-name weight + $ exposure, long/short counts, top-12 legs by |w|, gross Σ|w| / net
Σw). `REPORT_DUE: yes` on a settled-bar advance OR the first report of a new UTC day; `--mark-pushed`
records it via a single `tradfi_digest_last_pushed` state key (`{candle, day}` JSON) — the ONLY write
the monitor performs, mirroring the metals `--mark-pushed` bookkeeping.

## Verify — against the Phase-2c smoke state (back-dated launch 2026-06-01)
`scripts/tradfi_status.py`:
```
STATUS: ALERT  (engine=DOWN, eq_parity=$106,348, eq_live=$105,533, held=68 names, parity=OK, candle=OK)
  last settled bar processed: 2026-06-30   freshest on disk: 2026-06-30
  FUNDING/BASIS: eq_parity=$106,348  eq_live=$105,533  basis_gap=$-815 (-81bps)  funding_cum=$-172.32
  ALERT: engine DOWN (run_tradfi_paper.py not running)
```
Exit 1 (engine DOWN is a legitimate alert — the paper loop isn't running for this build). **PARITY=OK**
(held 68 names == recomputed target ex-PAYP, 0 drift at tol 1e-6), **CANDLE=OK** (last_candle 2026-06-30
< today 2026-07-01, no look-ahead), no MISSED (settled 2026-06-30 == last_candle). FUNDING/BASIS shows
the **−81 bps** basis + **−$172.32** funding carry from the smoke.

`scripts/tradfi_digest.py`:
```
TRADFI BOOK + DUAL P&L  (as_of 2026-06-30, iter-016 bear-gated TSMOM, PAPER)
  PARITY  $106,348   since-launch +6.35%   since-last n/a (1st bar)
  LIVE    $105,533   since-launch +5.53%   since-last n/a (1st bar)   (perp − funding − cost)
  basis_gap $-815 (-81bps)   funding_cum $-172.32 (-0.172% ≈ -2.17%/yr carry)
  regime g=0 (non-bear → TSMOM tilt ON, EW-252d ret +86.2%)
  book: 68 names (ex-PAYP)   32 long / 36 short
  gross Σ|w| 0.690 ($73,428)   net Σw +0.055 ($5,894)
  top legs by |w|:  LONG SNDK +0.0570 … SHORT PLTR -0.0409 … (12 shown)
REPORT_DUE: yes
```
Both equity tracks + basis + funding + bear-gate + the ex-PAYP book render. `--mark-pushed` flips
`REPORT_DUE` to `no` (same candle+day) and writes `tradfi_digest_last_pushed`. (The annualized funding
note is noisy over the ~29-day back-dated smoke window — the book-level steady-state carry is ≈−0.7%/yr;
the note is observational only.)

## Tests
`uv run pytest tests/test_tradfi_monitor.py -q` → **11 passed**. Covers `_engine_up_from_ps`
(real-runner match + grep/self/bash-c rejection), `_missed_rebalance` (trading-day fires, weekend
does not, first-run/no-data does not), `_parity_drift` (PAYP exclusion, real-mismatch detection).
Synthetic inputs only — no network, no DB.

## Constraints honored
- **READ-ONLY** — the scripts read the DB / equity CSV / log + recompute the strategy target; the only
  write is the `tradfi_digest_last_pushed` bookkeeping key (explicitly permitted). No orders (paper).
  The status script opens the engine's StateStore only if `data/tradfi_paper.db` already exists (no DB
  creation).
- **No modification** of `live_tradfi.py`, `live_weights_tradfi.py`, `core_tradfi.py`, `iter_016*.py`,
  or the reconcile modules — new files only.
- The MISSED/settled-bar rule reuses the engine's own helpers (no divergent settled-bar logic).
- The PARITY recompute applies `LIVE_EXCLUDED` (PAYP) exactly as the engine does.
- No `git stash` / `checkout` / `reset`. `git add` only the four new tracked files
  (`scripts/`, `.claude/`, `tests/`, `diary-portfolio-tradfi/`) — nothing under `data/` or
  `data_live_tradfi/`.
- `uv run ruff check scripts/tradfi_status.py scripts/tradfi_digest.py tests/test_tradfi_monitor.py`
  clean; `uv run pytest tests/test_tradfi_monitor.py -q` → 11 passed.

## v0 changelog
Initial monitor skill. `tradfi_status.py` (STATUS/PARITY/CANDLE alerts + FUNDING/BASIS observational),
`tradfi_digest.py` (dual-P&L / basis / funding-carry / bear-gate / held book), the on-disk
weekend-benign MISSED rule reusing the engine's settled-bar helpers, PAYP-exclusion parity recompute,
engine-down relaunch + flat-start caveat, self-paced ~3600s ScheduleWakeup loop. See
`.claude/commands/tradfi-monitor.md`.
