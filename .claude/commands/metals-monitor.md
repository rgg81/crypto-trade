# Metals Monitor — live watch on the metals PAPER desk

## Operating principle (read first)
**This skill is the canonical home for ALL monitoring + assistant intelligence on the METALS paper
desk.** Every improvement — a new health signal, a smarter check, an auto-recovery playbook — lands
HERE (this file + helper scripts under `scripts/metals_*.py`), gets committed, and is logged in the
Changelog. Keep helper logic in committed scripts (testable); keep this file the index + playbook.
This is the sibling of `portfolio-monitor` (the crypto L/S bot) — same philosophy, different desk.

## What's being watched
The **metals paper-trading desk** (`run_metals_paper.py`): the iter-010 champion (breadth-acceleration
dispersion gate + position-level honest net) on the 4 Binance metal perps (gold/silver/platinum/
palladium), 8h candles. **PAPER mode only** — no exchange, no real money. Signals come from
**Dukascopy** data (the backtest's source, for EXACT signal parity); fills are simulated at the candle
open. The book rebalances every 8h. State: `data/metals_paper.db` (SQLite), equity curve
`data/metals_equity.csv`, log `logs/metals_paper.log`, data `data_live_metals/`.

Strategy facts (for context — do NOT re-derive): leak-free, position-level honest BEAR +0.36 / IS
+0.16 / BULL +1.60 (all-3-positive). The earlier iter-008 "+0.75 bear" was look-ahead-inflated and is
**WITHDRAWN** (see `BASELINE_METALS.md`) — do not cite it. The whole point of this paper run is to
WATCH the honest book run live and confirm it tracks the backtest.

## HANDS-OFF MANDATE — never interfere with the strategy
We are TESTING the strategy. It runs UNTOUCHED through wins AND losses.
- **NEVER** alter positions in response to performance. There is no kill-switch to invoke (paper).
- **Drawdown / PnL / regime / turnover are TEST RESULTS, not alerts** — report them in the digest, do
  NOT act on them.
- The ONLY alerts are **TEST-INTEGRITY** failures — the test isn't running, or the paper book stopped
  tracking the backtest: engine DOWN, Traceback, MISSED rebalance, **PARITY=DRIFT**, **CANDLE=BAD**.
  Relaunching a crashed engine is PRO-test (it resumes + re-tracks the target) — allowed, not interference.

## How to run a check (per tick)
```
cd /home/roberto/crypto-trade/.worktrees/portfolio-metals \
  && export PATH="$HOME/.local/bin:$PATH" \
  && uv run python scripts/metals_status.py \
  && uv run python scripts/metals_digest.py
```
Both are READ-ONLY (read the DB / CSV / log / Dukascopy CSVs + recompute the strategy target). They
don't touch the engine's SQLite write path meaningfully (read-only opens). Filter matplotlib noise
with `| grep -vE "findfont|Arial"`.
- `metals_status.py` → `STATUS: OK|ALERT` (engine alive + no traceback + not-overdue) + `PARITY: OK|
  DRIFT` (held book vs recomputed iter-010 target, same forming-proxy) + `CANDLE: OK|BAD` (no forming
  leak / not stale >9h). **The only alert source.** Exit 1 if any alert.
- `metals_digest.py` → equity + since-launch% + 24h% + breadth/regime + held positions. `DIGEST_DUE:
  yes` on the first run of a new UTC day → push it, then run with `--mark-pushed`. **Observational.**

## ALERT conditions (investigate → fix if safe → notify)
- **engine DOWN** — `run_metals_paper.py` not running → relaunch (below) + notify.
- **TRACEBACK** in the log → read the tail, diagnose.
- **MISSED rebalance** — a complete 8h candle (00/08/16 UTC) is clock-due but `metals_last_candle`
  hasn't advanced ≥8h → the Dukascopy refresh is stuck (npx slow/hung) or a traceback; check the log.
- **PARITY=DRIFT** — the held paper book diverges from the recomputed iter-010 target. In PAPER the
  fill is exact, so steady-state parity is ~0; a DRIFT means the engine persisted the wrong book or
  the champion code/data changed under it. The real correctness alarm.
- **CANDLE=BAD** — a forming (incomplete) candle leaked into `data_live_metals` (look-ahead) — the
  ingest should drop it; investigate `live_metals._refresh_one`.

## BENIGN — do NOT alert
- `engine DOWN` immediately after an intentional stop (you stopped it) — only alert on unexpected death.
- `data stale` flag during a weekend (metals trade ~24/5; Dukascopy has no Sat/Sun candles) — the
  staleness flag is informational; only a >9h gap on a TRADING day + a missed clock-due candle is real.
- Small equity moves / breadth changes / a flip between bull and bear regime — TEST RESULTS.
- `n_positions` changing (the dispersion sleeve scales continuously with breadth) — expected.

## Response protocol each tick
1. Run both checks.
2. **STATUS=OK** → stay quiet (no ping), reschedule ~2700s out via ScheduleWakeup (pass this monitor
   prompt verbatim so it repeats).
3. **STATUS=ALERT** → read `tail -40 logs/metals_paper.log`, diagnose, fix if safe + within these
   patterns (a relaunch is safe + self-tracking), then **PushNotification** the user with what happened
   + what you did. Reschedule.
4. **DIGEST_DUE: yes** → PushNotification the digest block, then `metals_digest.py --mark-pushed`.
5. Don't spam: one ping per *state*, not per tick.

## Engine-down recovery (relaunch — safe + self-tracking)
```
cd /home/roberto/crypto-trade/.worktrees/portfolio-metals
export PATH="$HOME/.local/bin:$PATH"
PYTHONUNBUFFERED=1 uv run python run_metals_paper.py > logs/metals_paper.log 2>&1 &
```
On restart the engine recomputes the iter-010 target from full Dukascopy history and resumes from the
persisted `metals_last_candle` — a relaunch re-tracks the backtest, no seeding needed. The FIRST launch
seeds the deep Dukascopy history (gold/silver 2005+) into `data_live_metals/` — that initial pull takes
a few minutes (every later tick is an incremental append). Ctrl-C is safe; the DB persists.

## Self-paced loop
Self-pacing, not a cron. Each tick, after handling the checks, call **ScheduleWakeup** with
`delaySeconds` ~2700 (8h rebalances are the events; ~45-min checks catch them + liveness) and `prompt`
= this monitor instruction verbatim. To STOP, the user says so — then omit ScheduleWakeup. Keep 2700s
unless asked for tighter/looser.

## Verify parity on demand (deeper than the per-tick check)
```
uv run python analysis/portfolio/metals/reconcile_metals.py --n 200 --data data_live_metals
```
Replays history: bit-exact recompute==book (0.0) + the live forming-proxy gap (~1e-3). PARITY: OK means
the live engine reproduces the backtest bit-for-bit. Run before trusting a long paper track.

## Key files & facts
- Checks: `scripts/metals_status.py` (alerts), `scripts/metals_digest.py` (report).
- Runner: `run_metals_paper.py` (equity $10k, db `data/metals_paper.db`, log `logs/metals_paper.log`).
- Champion: iter-010 (`analysis/portfolio/metals/iter_010_breadth_accel.py`), deployed via
  `live_weights.py`. Baseline doc `diary-portfolio-metals/BASELINE_METALS.md`.
- Data path = Dukascopy (`data_live_metals/`), for EXACT signal parity with the backtest. The Binance
  metals-perp basis is a FUTURE pre-capital reconcile item (real execution would be on Binance perps).
- Going to **real money** (far off): add a Binance metals-perp execution path + a Dukascopy-vs-Binance
  basis reconcile + a forward bear; tighten the watch cadence first. Paper is the current scope.

## Changelog
- **2026-07-04 v4** — WEEKEND MISSED false-positive fix. `metals_status.py`'s overdue check used a
  naive `(now // 8h) * 8h - 8h` clock grid (comment wrongly assumed "weekend gaps are < 8h") so it
  fired `STATUS: ALERT MISSED rebalance` on EVERY Sat/Sun tick (the Fri-16:00 → Sun-16:00 gap is 48h
  with no trading candles). New pure helper `universe_metals.expected_trading_candle(now_ms)` walks
  back over non-trading weekend slots (Sat 00/08/16 + Sun 00/08) to the most recent CLOSED
  market-open candle; the MISSED check compares last_candle to that. Weekend stays OK; a genuine
  trading-day miss (incl. a Monday-reopen miss parked at Fri-16:00 → 48h behind) still fires. 3 new
  tests in `test_metals_data_sourcing.py` (10 total pass). Caught live on Sat 2026-07-04 08:54 UTC.
- **2026-07-03 v3** — DATA SOURCING: Binance live (24/5) + Dukascopy one-time backfill (user: "stop
  relying on Dukascopy live"). Recurring Dukascopy live fetch-failures (twice in ~8h + an uneven-
  recovery incident that briefly corrupted the book) → swapped `live_metals._refresh_one` to
  `fetcher.fetch_symbol_interval` (Binance incremental, reliable). Per metal: Dukascopy[deep..
  perp_launch) + Binance[perp_launch..now], built once by `build_merged_data.py` into data/ +
  data_live_metals/. Binance is 24/7 but the strategy is 24/5 → `um.metals_market_open` filters to
  Mon-Fri + Sun-16:00. Also added: MIN-ALIGNMENT guard (`live_metals` run_once uses min-of-coins
  latest — never rebalance on partially-refreshed data; commit 04552538); hardened `_engine_up`;
  "exactly-ONE-engine" check (kill extras by PID, NEVER `pkill -f run_metals_paper.py` — self-matches
  the monitor shell). Parity bit-exact on the merged store; 36 metals tests pass. Weekend gap still
  applies (24/5): Fri-16:00 candle → Sun-16:00 reopen; STALE/MISSED benign Sat/Sun.
- **2026-07-01 v2** — REALISTIC FUNDING (user: "account those trades realistically"). Paper equity now
  = price leg + FUNDING leg from REAL Binance metal-perp 4h `fundingRate` (`metals_funding.py`;
  refreshed at each rebalance in `live_metals`; shown as `[fund $X]` in the digest, `metals_funding_pnl`
  in the DB). Funding is post-decision on the deployed book → held book bit-identical, parity preserved
  (19-test suite green). Causal (complete-candle gate; no look-ahead — quant-critic PASS). Live funding
  leg ≈ +$13 (net-short book earns). Push block's REALIZED line carries the funding automatically.
- **2026-06-30 v1** — realized/unrealized/total PnL + per-metal MTM in the digest; `_engine_up` hardened
  (positional match, not naive `ps` substring — a computer restart had it false-report engine=up); push
  gated on genuine book change (`legs>0`), not day-flips; deployment leverage 3× (`live_weights.LEVERAGE`).
- **2026-06-26 v0** — initial skill: `metals_status.py` (STATUS/PARITY/CANDLE, the test-integrity alert
  set) + `metals_digest.py` (equity/regime/positions, observational, once-a-day push). HANDS-OFF
  mandate, engine-down relaunch, self-paced ScheduleWakeup loop. Watches the iter-010 metals paper desk.
  Parity check applies the same forming-proxy the engine uses (avoids a one-candle false DRIFT).
