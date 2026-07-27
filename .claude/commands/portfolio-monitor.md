# Portfolio Monitor — live watch on the deployed L/S portfolio bot

## Operating principle (read first)
**This skill is the canonical home for ALL monitoring + assistant intelligence on the trade bot.**
Every improvement we make — a new health signal, a smarter alert, a reconciliation check, a report,
an auto-recovery playbook — lands HERE (in this file + its helper scripts under `scripts/`), gets
committed, and is logged in the Changelog below. Intelligence compounds in one place instead of
scattering across sessions. When the user asks to "improve the monitoring/assistant," extend this
skill. Keep helper logic in committed scripts (testable, reusable) and keep this file the index +
playbook over them. The roadmap below is the living backlog; promote items into the workflow as we
build them and tick them off in the Changelog.

## HANDS-OFF MANDATE — NEVER interfere with the strategy (user directive 2026-06-22)
We are TESTING the strategy. It must run UNTOUCHED through wins AND losses. The monitor OBSERVES and
INFORMS; it NEVER intervenes in the trading.
- **NEVER** flatten, reduce, hedge, or otherwise alter positions in response to performance.
- **NEVER** run or recommend the kill-switch because of drawdown / a losing streak / an offside tilt.
  Overriding the strategy on a loss corrupts the test (the −23% drawdown budget exists to sit through
  exactly these). The kill-switch stays a MANUAL, user-only tool — the monitor never invokes or
  suggests it for performance reasons.
- **DRAWDOWN / PnL / tilt / turnover are TEST RESULTS, not alerts.** Report them in the daily digest
  and on request; do NOT treat them as something to act on. (A genuine DD=BREACH at the catastrophic
  20%-account band is still surfaced as INFORMATION, not a call to intervene.)
- The ONLY things that warrant an alert are TEST-INTEGRITY failures — the test isn't running correctly
  or the strategy isn't faithfully following the backtest: engine DOWN, traceback, order ERRORS,
  PARITY=DRIFT, CANDLE=BAD, a MISSED rebalance. Relaunching a crashed engine is PRO-test (it resumes
  the run and reconciles to the strategy's own target), so it's allowed — it is not interference.

## Run modes — PAPER vs TEST BINANCE vs LIVE (keep these distinct)
The bot can run in three modes; metrics mean different things in each, and the monitor must label
which one it's watching. NEVER conflate them.
- **PAPER (dry-run)** — no exchange. Fills are SIMULATED at the engine's reference price (close-proxy),
  so PnL is idealized and slippage is zero by construction. Good for decision-parity, not for cost.
- **TEST BINANCE (testnet, current deploy)** — REAL orders on Binance's testnet matching engine with
  FAKE money. Decisions, positions, balance, funding, rebalances are real-shaped — but testnet
  LIQUIDITY is thin/artificial, so FILL PRICES and SLIPPAGE are NOT representative of production.
  The effective fee rate IS real. This is a full smoke test of the integration, not a cost study.
- **LIVE** — real money + real liquidity. The only mode where slippage / fill-quality is the true
  number to trust. Tighten thresholds + run the pre-flight before this.
The monitor scripts auto-detect mode (creds + auth_base_url) and label output (e.g. `MODE=TESTNET`).
Treat testnet fill/slippage as INFO, never as an alert; on LIVE they become real alert sources.

## Mission
Keep a continuous, self-paced watch on the **live portfolio trading engine** (currently the
baseline-v3 long/short top-20 book on Binance **testnet**) and alert the user on **any unexpected
situation or error**. The bot rebalances every 8h; this skill verifies — from the **real Binance
API** — that it stays healthy between rebalances and that each rebalance fires cleanly.

Source of truth: **the live signed Binance API**, queried fresh every tick — never local cache.
Positions, unrealized PnL, balance, margin, liquidation come from `/fapi/v3/positionRisk`,
`/balance`, `/account`. Only "engine alive" (a `ps` check) and "last rebalance / errors" (parsed
from the engine log) are local — and correctly so, since they describe the *bot*, not the money.

## How to run a check
Each tick runs BOTH the fast health check and the deeper parity/drift check:
```
cd /home/roberto/crypto-trade/.worktrees/quant-research \
  && export PATH="$HOME/.local/bin:$PATH" \
  && set -a; source ~/.binance_testnet_env; set +a \
  && export BINANCE_AUTH_BASE_URL="https://testnet.binancefuture.com" \
  && uv run python scripts/portfolio_healthcheck.py \
  && uv run python scripts/portfolio_candle_check.py \
  && uv run python scripts/portfolio_parity_check.py \
  && uv run python scripts/portfolio_digest.py \
  && uv run python scripts/portfolio_drawdown_check.py \
  && uv run python scripts/portfolio_fill_quality.py \
  && uv run python scripts/portfolio_trend_alerts.py \
  && uv run python scripts/portfolio_turnover_ledger.py
```
All checks are READ-ONLY and DON'T COMPETE with the trade loop: they read CSVs / the log / the
testnet-signed endpoints, while the engine's heavy 8h refresh hits PRODUCTION klines+funding (a
different host/rate-limit pool), and nothing here touches the engine's SQLite DB. Avoid running the
heavy parity check in the ~5min right at an 8h boundary (engine mid-refresh) — the 45min cadence
naturally does.
- `portfolio_healthcheck.py` → `STATUS: OK|ALERT` + positions summary + `FLAG:` lines (fast, API-only).
- `portfolio_candle_check.py` → `CANDLE: OK|BAD` (fast, CSV-only). BAD = a forming (incomplete) candle
  leaked into the signal data, or the data is stale (missed refresh). Guards the "close must be a
  COMPLETE candle, never the forming one" invariant.
- `portfolio_parity_check.py` → `PARITY: OK|DRIFT` (loads the universe + recomputes the strategy
  target; ~20s). DRIFT = the live book no longer matches what the strategy says it should hold.
- `portfolio_digest.py` → appends an equity snapshot to `data/portfolio_equity.csv` (the equity
  curve) and prints a 24h PnL digest (realized / funding / commission / unrealized, per-name) +
  `DIGEST_DUE: yes|no`. Not an alert source — it's the periodic report (see Daily digest below).
  RUN IT BEFORE the drawdown check so the latest equity snapshot is logged first.
- `portfolio_drawdown_check.py` → `DD: OK|BREACH` from the equity curve. Reports ACCOUNT DD (vs peak,
  liquidation-relevant) AND STRATEGY-EQUIV DD (cumPnL/notional, comparable to the backtest −23%).
  BREACH = account DD >20% or strat-equiv DD worse than backtest×1.5.
- `portfolio_fill_quality.py` → `FILLQUAL: OK|INFO|n/a` + `MODE=PAPER|TESTNET|LIVE`. Effective fee
  rate (real in every mode; ~5bps expected) + adverse slippage vs the close-proxy reference. On
  TESTNET slippage is flagged NON-REPRESENTATIVE (INFO, never an alert); on PAPER it's n/a (simulated
  fills); on LIVE large adverse slippage or a fee-rate far above ~5bps IS an alert.
- `portfolio_trend_alerts.py` → `TREND: OK|WATCH` from the equity curve — slow bleeds the per-tick
  thresholds miss (equity down >5%/2h, margin down >30%/2h) + "what changed since last tick". CSV-only.
- `portfolio_turnover_ledger.py` → `TURNOVER: OK|SPIKE`. Parses the log into a per-rebalance ledger
  (`data/portfolio_turnover.csv`); confirms low live turnover (~1-4 legs/rebal steady-state, under the
  backtest's ~18 since live skips sub-$5 dust); SPIKE = a non-cold-start rebalance with many legs.
Filter stderr noise with `| grep -vE "UserWarning|warn"`. Per the HANDS-OFF mandate, the ALERT set is
TEST-INTEGRITY only: `STATUS=ALERT` (engine down / traceback / order ERRORS / missed rebalance / zombie
reappear), `CANDLE=BAD`, `PARITY=DRIFT` (not near-boundary-transient). These mean the test isn't running
right or the strategy isn't tracking the backtest → investigate/fix (fixes that resume the run, never
position changes) + PushNotification. `DD=BREACH`, `TURNOVER=SPIKE`, `TREND=WATCH`, `FILLQUAL` are
OBSERVATIONAL test-results — report in the digest / on request, do NOT act on them and do NOT push a
"consider flattening" alert. (Concentration/gross/margin: surface only as info; never act.)

## Emergency & cutover tools (on-demand, NOT per-tick)
- **Pre-flight** (`scripts/portfolio_preflight.py`) → `PREFLIGHT: GO|NO-GO`. Run before the live-money
  cutover: checks creds/mode, balance ≥ 1.5× est. margin, baseline-v3 tag, fresh data, sane ~top-20
  target. Read-only.
- **Kill-switch** (`scripts/portfolio_killswitch.py`) → emergency halt. DRY-RUN by default; `--confirm`
  STOPS the engine FIRST then flattens every position (reduceOnly). **USER-ONLY.** Per the HANDS-OFF
  mandate the monitor NEVER runs it and NEVER recommends it for performance/drawdown — the strategy is
  being tested and must run untouched. It exists solely for the user to invoke manually if they choose,
  or for a genuine operational emergency the user directs.

## Daily digest (PnL attribution)
`portfolio_digest.py` runs every tick to log the equity snapshot (cheap). When its output shows
`DIGEST_DUE: yes` (first tick of a new UTC day), **PushNotification the digest block** to the user
(equity + 24h Δ, realized/funding/commission/net, top winners/losers), then run
`uv run python scripts/portfolio_digest.py --mark-pushed` so it only fires once per day. On
`DIGEST_DUE: no`, do nothing with it (the snapshot was already logged). The equity CSV builds the
curve; after 24h of snapshots the "24h Δ" populates. NOTE early realized/commission numbers are
inflated by deploy/debug churn (flatten + re-enter); steady-state commission is near-zero (the band +
eligibility-exit keep turnover low).

## What the health check verifies (`scripts/portfolio_healthcheck.py`)
- **engine alive** — the `run_portfolio_testnet.py` process is running (`ps`).
- **log scan** — any `Traceback`; the last rebalance `as_of` + `orders placed/errors`.
- **positions (LIVE API)** — count, gross $, net $, max single-name concentration, and whether any
  delisted/zombie name (TOMO/BLZ) reappeared.
- **balance/margin (LIVE API)** — wallet balance + available margin (liquidation headroom).
- **unrealized PnL (LIVE API)** — Binance's own `unRealizedProfit`, summed (matches account total).

## ALERT conditions (investigate → fix if safe → PushNotification the user)
- **engine DOWN** (process not running) — relaunch (see below) and notify.
- **Traceback** in the log.
- **NEW order errors** — `last_errs > 0` on the most recent rebalance (find the failing leg in the
  log; the usual causes are already fixed — stepSize floor (-4023) and post-floor min-notional
  (-4164) — so a new error means a genuinely new condition).
- **Concentration > 30%** of gross in one name.
- **Gross outside $5–12k** (the $10k-equity × ~0.70–0.85 vol-target band).
- **TOMO/BLZ (delisted) reappear** in the book — the eligibility-exit should keep them out.
- **Margin avail < $200** — liquidation risk.
- **MISSED rebalance** — UTC time is well past an 8h boundary (00/08/16 UTC) but `last_rebal`
  hasn't advanced to it. Check the log tail for a stuck refresh / traceback.
- **PARITY=DRIFT** — the live book diverges from the strategy target: a `MISSING` name (failed
  entry), `EXTRA` (failed close), `WRONGSIDE`, or `MISSIZED` leg. The real correctness alarm —
  means the bot is NOT holding what v3 says. (If the line says "NEAR 8h boundary, likely transient,"
  the engine is mid-rebalance — re-check next tick before alerting.)
- **CANDLE=BAD** — `FORMING-CANDLE LEAK` (an incomplete candle is in the signal data — a look-ahead
  bug; the fetcher should have dropped it) or `STALE data` (freshest complete candle >9h old → the
  engine missed a refresh). Either breaks backtest parity at the data layer — investigate the
  fetcher / refresh immediately.

## BENIGN — do NOT alert
- `skipped > 0` dust legs (sub-$5 after stepSize floor — correctly skipped).
- Mild net-short (or net-long) tilt — the trend+carry signal isn't dollar-neutral by construction.
- Small uPnL swings (a few $ to low tens on an ~$8k book = normal mark-price noise).
- `last_rebal` not yet advanced when the next 8h boundary hasn't passed **in UTC** (the schedule
  display is local TZ, often +2h; the health check `checked` line is UTC — trust the UTC one).
- The frozen TNSR ~$0.16 dust position (too small to close under the $5 min; harmless).

## Response protocol each tick
1. Run the check.
2. **STATUS=OK** and `last_rebal` consistent with UTC → stay quiet (no ping), reschedule the next
   tick ~2700s out via ScheduleWakeup (pass the monitor prompt verbatim so it repeats).
3. **STATUS=ALERT** → read the log tail (`tail -30 logs/portfolio_testnet_v3.log`), diagnose, fix if
   it's safe and within established patterns, then **PushNotification** the user with what happened +
   what you did. Reschedule.
4. Don't spam: one ping per *state*, not per tick. If an alert persists across ticks and you've
   already notified + can't safely auto-fix, wait for the user.

## Engine-down recovery (relaunch)
```
cd /home/roberto/crypto-trade/.worktrees/quant-research
export PATH="$HOME/.local/bin:$PATH"; set -a; source ~/.binance_testnet_env; set +a
export BINANCE_AUTH_BASE_URL="https://testnet.binancefuture.com"
rm -f data/portfolio_testnet.db    # fresh DB -> re-reconciles vs ACTUAL exchange positions on start
PYTHONUNBUFFERED=1 uv run python run_portfolio_testnet.py > logs/portfolio_testnet_v3.log 2>&1 &
```
On restart the engine reads the **actual** book from the exchange (`get_positions`), recomputes the
v3 target, and trades only the diff — so a relaunch is safe and self-reconciling. First refresh
takes ~5–7 min (540-coin klines+funding) before the first rebalance line appears.

## Self-paced loop (how to keep watching)
This is a self-pacing monitor, not a cron. On each tick, after handling the check, call
**ScheduleWakeup** with `delaySeconds` ~2700 (the 8h rebalances are the key events; ~45-min checks
catch them and liveness in between) and `prompt` = the same monitor instruction verbatim so the
next firing repeats it. To **stop**, the user says so — then omit the ScheduleWakeup and mark
task #189 done. Keep the cadence at 2700s unless the user asks for tighter/looser watch.

### Session-cron alternative (CronCreate) — how the v2-track loop is currently driven (2026-07-18)
Instead of ScheduleWakeup, the loop can be driven by a **CronCreate session cron** when the user asks
for a fixed wall-clock cadence ("every 2 hours"). The **v2-track monitor currently runs this way**:
a recurring cron fires **every 2h at :13 local** (off the :00 mark so the fleet doesn't hammer the API
in lockstep) whose `prompt` is the full v2-only tick instruction (healthcheck + pnl + log scan, HANDS-OFF
interpretation — the verbatim block quoted in the v2 section below). Gotchas, all load-bearing:
- **The cron IS the cadence — the fired prompt must NOT also call ScheduleWakeup** (that spawns a
  competing loop). The v2 prompt says so explicitly.
- **Session-only + in-memory.** A CronCreate job lives only in the current Claude session; it does NOT
  survive a session resume/reset, and it auto-expires after ~7 days. **If `CronList` shows "No scheduled
  jobs", the loop has stopped — recreate it.** (Happened 2026-07-18: the cron silently dropped on a
  session reset while the engine kept trading fine; the ticks had been cron-driven, so the loop just
  ended. Recreated as a fresh job.) Re-run `CronList` whenever the user asks "is the monitor still
  looping / looping here?".
- **Recreate recipe:** `CronCreate` with `cron: "13 */2 * * *"`, `recurring: true`, `prompt` = the
  verbatim v2-only tick instruction. Stop early with `CronDelete <id>`.
- **Worktree/session separation still applies** ([[project_monitor_session_separation]]): launch the v2
  cron from the quant-portfolio worktree session so it watches the v2 book and never cross-fires with
  the v1/metals crons. Keep it v2-ONLY (do not run the v1/quant-research checks from it).

## Key files & facts
- Health check: `scripts/portfolio_healthcheck.py`
- Engine runner: `run_portfolio_testnet.py` (equity $10k, leverage 3x, db `data/portfolio_testnet.db`)
- Log: `logs/portfolio_testnet_v3.log` · Creds: `~/.binance_testnet_env` (testnet keys only)
- Data path = **production** klines/funding (`fapi.binance.com`); **orders/positions = testnet**
  (`testnet.binancefuture.com`). Real market data, fake-money execution.
- Strategy = baseline-v3 (trend+carry walk-forward-λ + hysteresis δ=0.010 + eligibility-exit K=2),
  tag `portfolio-baseline-v3`. Parity is bit-exact vs the backtest (reconcile_live + parity test).
- Going to **real money**: swap `--testnet`/keys for production, seed `data/live.db`; same recipe.
  Tighten the watch cadence and re-confirm the ALERT thresholds before that step.

## v2 PARALLEL TRACK — rank-21–40 dollar-neutral XS-mom (added 2026-06-23)
A SECOND book runs ALONGSIDE v1, fully isolated, on a SEPARATE testnet account. Monitor BOTH.
- **Worktree:** `/home/roberto/crypto-trade/.worktrees/quant-portfolio` · **Runner:**
  `run_portfolio_v2_testnet.py` (equity $4k, lev 1x, `--live-testnet` to trade) ·
  **Log:** `logs/portfolio_v2_testnet.log` · **DB:** `data/portfolio_v2_testnet.db` ·
  **Creds:** `~/.binance_testnet_v2_env` (DIFFERENT account, $5k faucet) · **proc:** `run_portfolio_v2_testnet`.
- **Strategy** = BASELINE_PORTFOLIO_V2 (crypto-only rank-21–40 XS-mom 5-way ensemble {42,63,84,126,168} +
  risk layer TARGET_VOL=0.006/MAX_LEV=2.0). Dollar-neutral-ISH (small inverse-vol net tilt is expected,
  certified). Gross ≈ 0.3–0.6×equity (lower than v1 — the de-lever). Backtest OOS +1.16 (2× taker +0.90).
- **v2 health check:** `scripts/portfolio_v2_healthcheck.py` (v2 paths/creds/account; STATUS OK|ALERT).
  Run it with `source ~/.binance_testnet_v2_env` (NOT v1's). The full v2 parity/candle/digest suite is
  a roadmap item — for now the healthcheck + a manual log scan cover the TEST-INTEGRITY essentials.
  NOTE its one-line `uPnL` is MARK-ONLY (open-position mark-to-market); it does NOT include funding/fees.
- **v2 all-in cost accounting (REALISTIC bottom line):** `scripts/portfolio_v2_pnl.py` (v17). Since these
  are REAL exchange trades, it reconciles to Binance's own ledger: `seed + realized + funding + commission
  == wallet balance` (ties to the cent → nothing missing by construction), `+ unrealized == margin balance
  (true equity)`, `− seed == ALL-IN P/L`. **HEADLINE P/L is stated on a PRODUCTION-funding basis** (user
  directive — testnet funding is a garbage artifact): every real funding settlement is repriced to what it
  WOULD have cost at production rates via `prod_income = testnet_income × (prod_rate / testnet_rate)` per
  (symbol, funding_time) — funding is linear in the rate and the notional is identical, so notional cancels;
  prod_rate/testnet_rate come from the public historical `fapi/v1/fundingRate` endpoints (prod =
  fapi.binance.com, testnet host). So `funding(PROD)` replaces the testnet funding in `all-in P/L`, and the
  raw testnet funding is used ONLY for the reconcile-to-wallet integrity check (the wallet physically holds
  testnet funding). Testnet slams the ±3.75%/8h cap flat (SIREN settled −3.75% every 8h ≈ −$113 total; real
  prod rate is +0.0001–0.0003 → repriced to ~+$1.6 since we're SHORT and a positive rate PAYS the short).
  Net effect: the ~−$109 testnet funding drag is a pure artifact; on prod funding is ~neutral, so the true
  strategy P/L is ~+3.5% not the ~+1.3% the raw testnet ledger shows. Reports equity(prod-adj), all-in P/L,
  the breakdown (realized / funding(PROD) / commission / unrealized / dust), the testnet→prod funding
  repricing detail + top artifact swings, a forward run-rate on the current book, and a reconcile line whose
  `opening` residual must stay small+stable (a GROWING gap = a cost bucket we're not capturing → investigate).
  Run each tick alongside the healthcheck. Slippage is already baked into realized/unrealized (it lands in
  the fill price); `portfolio_fill_quality.py` isolates it explicitly.
- **v2 PAPER-FALLBACK (testnet-only, hard-gated):** `paper_untradeable=True` in the v2 runner →
  symbols testnet can't fill are tracked as PAPER (not dropped), so the strategy holds its full intended
  book. Two failure classes (v20): PERMANENT codes (`-1121/-4140/-4411/-4061/-4046` at the ORDER step,
  `-4141/-1121/-4140` at SET_LEVERAGE per v19 — prod-listed names absent from testnet like TLM, caught
  before the order so no `-1111` cascade) paper on the FIRST failure; TRANSIENT `-4131` PERCENT_PRICE
  (thin-book) is RETRIED and papers only after 3 consecutive strikes (a liquid name like LINK retries +
  fills instead of freezing). A `_reconcile_paper_vs_positions()` startup step un-sticks any papered
  symbol that holds a live position (they're tradeable). The papered symbol's log shows
  `PAPER-FALLBACK <sym>` + `orders ... errors=0 papered=N`, and `engine_state["portfolio_paper"]` holds
  the papered symbols+weights. So on v2, **`errors=0` is the healthy steady state** (was the testnet-
  artifact errors). A REAL order error (any code NOT in the testnet set) IS still an alert. The
  fallback is `_paper_enabled() = paper_untradeable AND testnet AND not dry_run` → IMPOSSIBLE on
  production (real money); turn the flag OFF for the production cutover (there a MISSING leg = real alert).
- **Universe hygiene (load-bearing, real-money-critical):** v2 trades ONLY Binance `underlyingType==COIN`
  perps. Tokenized stocks (INTC/CRCL/NVDA/…), commodities (XAU/XAG), index baskets (BTCDOM/DEFI), and
  pre-market tokens are EXCLUDED via `universe_v2.NON_COIN_PERPS`. Before the production cutover, REGENERATE
  that set from production exchangeInfo (testnet ≠ production listings). If a stock-perp ever appears in the
  v2 book → ALERT (universe filter stale). See `diary-portfolio-v2/LIVE_DEPLOY.md`.
- **Relaunch v2** (same self-reconcile pattern as v1) — for a CRASH-RESUME or HUNG restart, **KEEP the DB**
  (preserves paper state + held + `last_candle` → resumes mid-cycle, no spurious rebalance) and **append**
  (`>>`) to the log so the incident history survives. Only `rm data/portfolio_v2_testnet.db` + truncate
  (`>`) for a deliberate CLEAN RESET (e.g. universe change). Recipe:
  `set -a; source ~/.binance_testnet_v2_env; set +a`, `export BINANCE_AUTH_BASE_URL=https://testnet.binancefuture.com`,
  `PYTHONUNBUFFERED=1 nohup uv run python run_portfolio_v2_testnet.py --live-testnet >> logs/portfolio_v2_testnet.log 2>&1 &`.
  ⚠️ **Killing the old proc:** NEVER `pkill -f run_portfolio_v2` / `pgrep -f run_portfolio_v2` — the pattern
  self-matches your own shell command (a false "STILL ALIVE"). Kill by **process-group**: `ps -eo pid,pgid,cmd`
  to get the pgid of the `uv run` leader, then `kill -TERM -- -<pgid>` (TERMs the `uv` wrapper AND its python
  child together), escalate to `-KILL` if it survives ~4s. Verify dead with `ps -eo cmd | grep run_portfolio_v2`
  (NOT pgrep). NEVER touch the v1 quant-research worktree/proc.
- **STAGGER THE RELAUNCH after a host reboot/resume — do NOT launch into the other engine's cold refresh
  (2026-07-26).** A WSL reboot kills BOTH engines, so recovery tends to restart them near-simultaneously —
  and two concurrent cold 540-symbol production-kline refreshes off the SAME IP are exactly what trips the
  `418` ban (root cause of the v11/v12/v16/v24 incidents; the `rebalance_lag_seconds` stagger only covers
  steady-state 8h boundaries, NOT restart time). Before relaunching v2, check whether v1 is mid-cold-start
  (`tail` its log for `loaded NNN TRADING symbols` with no `klines refreshed` yet). If it is, WAIT — then
  gate the launch on a clean IP: poll ~3 different symbols' klines every ~45s until you get **3/3 HTTP 200
  in one round** (a single 200 is not enough — a recovering IP FLAPS: expect runs like `418 418 418` /
  `200 418 200` before it settles). Launch in that window. Payoff is large and measured: this recovery got
  a clean **538/542-ok refresh on the FIRST successful tick**, versus the un-staggered restart the night
  before which ground through `125 → 305 → 538` across 4 failed ticks and ~6 min of 418 storm. There is
  almost always slack to spend on this — the book sits safely flat-held between 8h boundaries and the
  engine catch-up rebalances to the CURRENT target regardless of how many boundaries were missed.
- **CLOCK SKEW after a reboot/resume — a SILENT hard trading blocker (2026-07-27).** Binance rejects any
  signed request whose timestamp is **>1000ms AHEAD** of server time (`-1021`), and `recvWindow` does NOT
  relax that side (it only widens the behind-tolerance). WSL drifts ahead across a reboot/suspend when
  `timedatectl` shows `NTP service: inactive`. The failure is nasty because it is **invisible in the log**:
  public kline fetches are unsigned and keep succeeding, so refreshes look fine, while EVERY signed call
  (`get_positions`, `set_leverage`, `place_order`) fails — the engine computes a correct plan and places
  NOTHING. Skew near the 1s cliff is INTERMITTENT (some calls squeak through), so "the API worked once"
  proves nothing. `portfolio_v2_healthcheck.py` now measures it directly and ALERTs above 700ms.
  **FIX (no password needed — this is the important part):** the host has a NOPASSWD sudoers entry for
  ntpdate, so a monitor session can fix this itself in seconds:
  `sudo -n /usr/sbin/ntpdate pool.ntp.org` — verify with a skew re-probe (`/fapi/v1/time` vs local, sampled
  either side of the request so latency isn't misread as skew). Do NOT conclude "needs the user" on a
  password prompt: run `sudo -n -l` FIRST to list NOPASSWD rights (currently `service cron start|stop`,
  `/usr/sbin/hwclock`, `/usr/sbin/ntpdate pool.ntp.org`). `sudo systemctl restart systemd-timesyncd` and
  `timedatectl set-ntp true` both DO require a password, and `hwclock` fails under WSL ("Cannot access the
  Hardware Clock") — ntpdate is the one that works. Fixing the clock needs NO engine restart: each request
  is signed with a fresh timestamp, so trading resumes on the next tick by itself. Landing slightly BEHIND
  (negative skew, e.g. −50ms) is the safe side. Host-wide, so it fixes v1 too.
  ⚠️ **BUT ntpdate does NOT HOLD on this host — measured, don't re-litigate (2026-07-27).** After a step to
  −48ms the clock returns to +1.34s within ~40s and plateaus there (`t+0s −48ms, t+20s +867ms, t+40s
  +1440ms, t+60..180s ≈ +1338ms`). WSL re-syncs the guest clock from the WINDOWS host, and the Windows
  clock is the one that's wrong: `w32tm /query /status` showed `Leap Indicator: 3(not synchronized)`,
  `Source: Local CMOS Clock`, `Last Successful Sync Time: unspecified`, with `w32time` at
  `START_TYPE: 3 DEMAND_START` (so it never starts at boot). The peer (`time.windows.com,0x9`) IS
  configured but wouldn't poll for ~9h. `w32tm /resync` and `sc start w32time` are BOTH refused from WSL
  (`Access is denied`) — they need an ELEVATED Windows prompt:
  `sc config w32time start= auto; net start w32time; w32tm /resync /force`.
  **So a periodic ntpdate is NOT a viable stopgap** (drift returns faster than any sane cron), and
  **`AuthenticatedBinanceClient` now self-corrects** (commit `4874fba2`) — it re-syncs its own offset from
  `/fapi/v1/time` on a `-1021` and retries once, so host drift no longer blocks trading at all. Treat the
  Windows fix as hygiene, not as the thing standing between the book and a rebalance.
  📌 **Verifying a clock claim:** a ~1.3s error is INVISIBLE on any clock display — the taskbar will look
  perfectly correct. Never accept "the clock is fine" (from a human OR from one good reading) without a
  programmatic probe against `/fapi/v1/time`, AND a re-probe past 60s, since the host re-sync interval is
  what silently undoes an in-WSL fix. The decisive test is a real signed call: `-1021` or not.
- **HUNG engine (proc up, but frozen) — a distinct failure mode from a crash (2026-07-05).** A crash removes
  the proc (`STATUS: ENGINE DOWN`); a HANG leaves `proc=up` but the poll loop stops advancing. The tell: the
  engine was in an **actively-logging** state (a `tick error #N … retrying in 60s` storm writes a line every
  60s) and then the **log mtime freezes** mid-storm. A healthy engine BETWEEN 8h boundaries is also log-silent
  (no-op ticks don't log), so log-silence alone is NOT a hang — silence is only suspicious while the engine
  should be logging (mid-storm, or mid-refresh). The current healthcheck won't flag a between-boundary hang
  until it's `>25min` past the next boundary (`MISSED rebalance`); to catch it sooner, when the log has been
  frozen through what should be active logging, (1) confirm the IP is NOT the cause with a direct
  `curl -s -o /dev/null -w '%{http_code}' 'https://fapi.binance.com/fapi/v1/klines?symbol=BTCUSDT&interval=8h&limit=2'`
  — a `200` means the IP is clear and the freeze is a genuine process hang — then (2) PGID-kill + relaunch
  (KEEP the DB). A restart of a stuck engine is PRO-test recovery (it reconciles to its own target), not
  interference.
  **CRITICAL false-hang caveat (learned 2026-07-25, nearly mis-fired a relaunch):** `log frozen + IP 200`
  is NOT sufficient to call a hang. A **full 540-symbol refresh in progress freezes the log for MINUTES**
  legitimately (it logs nothing until the refresh completes), and a *throttled* refresh grinding through
  partial-418s can freeze it ~8–10 min. Before concluding hung + killing, grep the last few
  `klines refreshed: N ok` lines: **if N is CLIMBING across attempts (e.g. 125 → 305 → 538) the engine is
  actively RECOVERING, not hung — do NOT kill** (killing interrupts recovery + triggers a fresh cold
  refresh into the ban). Only conclude a genuine hang if the log is frozen AND the refresh ok-count is
  NOT progressing across a real ≥5-min window AND IP=200. When in doubt, watch the log mtime for ~3 min:
  a healthy-but-slow engine's mtime advances (even if minutes apart); a truly hung one never moves.
  Backlog: add a lightweight engine heartbeat / poll-tick timestamp so a hang is detectable without the
  log-activity heuristic (would have removed all ambiguity here).
- The HANDS-OFF mandate applies to v2 identically: observe + inform, never intervene on performance.
- **Network resilience (2026-06-23):** the engine poll loop (`engine.py:run()`) now wraps each tick in
  try/except → a transient `ConnectError`/network/API failure logs a ONE-LINER `tick error #N (...);
  retrying` and the loop CONTINUES (no crash). So a genuine `Traceback` in the v2 log now means a REAL
  bug (still an ALERT); recurring `tick error` one-liners = a network/outage condition (watch, but the
  engine self-heals when connectivity returns). `last_candle` only advances after a SUCCESSFUL tick, so
  no rebalance is lost to a blip. **For a CRASH-RESUME relaunch, KEEP the DB** (preserves the paper
  state + held + `last_candle` → resumes mid-cycle, no spurious rebalance); only `rm` the DB for a
  deliberate clean reset (e.g. universe change). The crash on 2026-06-23 (2× `ConnectError [Errno 104]
  Connection reset by peer` during a kline fetch) is what this hardening prevents from recurring.

## Intelligence roadmap (the living backlog — build these into the skill over time)
Prioritized; each becomes a committed helper script + a section here when built.
1. **Parity / drift check (HIGH).** ✅ DONE 2026-06-21 — `scripts/portfolio_parity_check.py`.
1b. **Candle-integrity check (HIGH).** ✅ DONE 2026-06-21 — `scripts/portfolio_candle_check.py`
   (signal close must be a COMPLETE candle, never the forming one; + staleness).
2. **PnL attribution + daily digest (HIGH).** ✅ DONE 2026-06-21 — `scripts/portfolio_digest.py`
   (realized/funding/commission/unrealized, per-name, equity snapshots, once-a-day digest).
3. **Drawdown / equity-curve tracking.** ✅ DONE 2026-06-21 — `scripts/portfolio_drawdown_check.py`
   (account DD + strategy-equiv DD vs backtest −23%; BREACH alert).
4. **Fill-quality / slippage tracking.** ✅ DONE 2026-06-21 — `scripts/portfolio_fill_quality.py`
   (MODE-AWARE: paper=n/a, testnet=INFO non-representative, live=real; fee rate + adverse slippage).
5. **Trend-aware alerts.** ✅ DONE 2026-06-21 — `scripts/portfolio_trend_alerts.py`.
6. **Turnover / cost ledger.** ✅ DONE 2026-06-21 — `scripts/portfolio_turnover_ledger.py`.
7. **Live-money pre-flight + kill-switch.** ✅ DONE 2026-06-21 — `scripts/portfolio_preflight.py`
   + `scripts/portfolio_killswitch.py` (stop-engine-first, reduceOnly flatten, --confirm).
ROADMAP #1–#7 COMPLETE. Future ideas: per-name funding-carry attribution, regime/vol dashboard,
auto-recovery escalation ladder, a live-vs-backtest tracking-error report.

## Changelog (tick off as we build)
- **2026-07-27 v27** — CLOCK DRIFT MADE HARMLESS IN CODE (`4874fba2`), after the host-side fix proved
  unreachable. Continues the v26 incident. The Windows fix could NOT be landed: `w32time` was stopped,
  `DEMAND_START`, never synced (`Source: Local CMOS Clock`), and every corrective command (`sc start`,
  `w32tm /resync`) is refused from WSL with `Access is denied`; three attempts from the Windows side did
  not change a single field. Measurement also killed the ntpdate stopgap: after stepping to −48ms the
  clock returns to +1.34s **within ~40 seconds** and plateaus (WSL re-syncs from the bad Windows clock),
  so no cron cadence can cover a rebalance. FIX: `AuthenticatedBinanceClient` now self-corrects — signs
  with a cached offset (0 until proven otherwise) and, on a `-1021`, re-syncs from `/fapi/v1/time` and
  retries ONCE. Chose REACTIVE over the usual proactive SDK sync deliberately: no extra round-trip on the
  happy path, and it doesn't perturb the 14 existing auth tests that index `captured[0]` (a proactive
  probe broke 8 of them — the failure that redirected the design). Retry is safe for orders because
  `-1021` is rejected at the gateway before matching; capped at one retry so a persistently-bad clock
  errors rather than loops. VERIFIED against the live API with the host still +1.32s off: first call
  re-syncs to −1364ms, then 8/8 signed calls succeed; previously 0/1. Added
  `tests/test_auth_client_time_offset.py` (6 tests — first coverage of the signing path): incident-exact
  skew, no-extra-request when healthy, offset reuse, single-placement on order retry, bounded retry,
  probe-failure not masking the original error. Full live+portfolio+auth scope 273 passed / 0 failed
  (4 pre-existing collection errors in v1-iteration test files are unrelated — verified by stashing).
  Engine restarted to load it (PGID-kill, DB KEPT, log appended). **Two process lessons.** (1) The
  self-match trap is WIDER than documented: `ps -eo cmd | grep run_portfolio_v2` also false-positives when
  YOUR OWN shell command contains the pattern — it reported "STILL ALIVE" against my own bash process.
  Verify by PID (`kill -0 <pid>`) or match the venv python (`/venv\/bin\/python3 run_portfolio_v2/`),
  never a bare cmd-grep. (2) A user (or a single green reading) asserting "the clock is fixed" is not
  evidence — 1.3s is invisible on a display, and one signed call succeeded by luck mid-incident while the
  skew was unchanged. Always probe programmatically, re-probe past 60s, and treat a real signed call as
  the arbiter. NOTE this fixes the v2 worktree's `src/` only; v1 (quant-research) has its own copy and is
  still exposed — port `4874fba2` before v1 real money.
- **2026-07-27 v26** — CLOCK-SKEW blocker found, fixed, and made self-detecting (+ a process lesson about
  giving up too early on sudo). INCIDENT: host rebooted ~07:14 UTC; both engines were relaunched
  concurrently ~07:18/07:41 (un-staggered — the v25 hazard, nobody was watching), a ~3h DNS outage
  (`Temporary failure in name resolution`, 366 ticks) then delayed them into cold-refreshing together →
  418 ban. That much was self-healing. The REAL blocker was hiding underneath: the host clock had drifted
  **+1.36s AHEAD**, so every SIGNED call returned `-1021` while unsigned kline fetches kept working — the
  log looked like an ordinary 418 recovery, and the engine would have computed a correct plan at 16:15 and
  placed NOTHING. The healthcheck's only clue was `account query failed: HTTPStatusError`, which cost real
  diagnosis time (hand-signing probe requests to see the code). THREE fixes: (1) `_clock_skew_ms()` in
  `portfolio_v2_healthcheck.py` — measured mid-flight so latency isn't misread as skew, ALERT >700ms (below
  the 1000ms cliff, while calls still intermittently succeed), INFO >300ms; (2) account-query failures now
  print the Binance code+msg, so `-1021` (clock) is distinguishable at a glance from `-2015` (bad key) /
  `-1003` (rate limit); (3) the skew playbook bullet above. **PROCESS LESSON (the one that cost the most):**
  I checked `sudo -n true`, saw a password was required, and told the user it was theirs to fix — but
  `sudo -n -l` reveals a **NOPASSWD entry for `/usr/sbin/ntpdate pool.ntp.org`**, which fixed it instantly
  (`step time server … offset -1.385914 sec`; skew +1364ms → −50ms; signed calls restored, book readable
  again at 32 pos / uPnL +$44.8). ALWAYS run `sudo -n -l` to enumerate NOPASSWD rights before declaring a
  privileged action blocked. Note `systemctl restart systemd-timesyncd` and `timedatectl set-ntp true` DO
  need a password and `hwclock` doesn't work under WSL — ntpdate is the one that works. No engine restart
  was needed (fresh timestamp per request). All-in P/L (prod-funding basis) +$118.91 / +2.38% vs seed.
  Backlog: have the auth client cache a `/fapi/v1/time` offset (what most Binance SDKs do) so clock drift
  becomes impossible rather than merely visible — untouched here since it's the live order path.
- **2026-07-26 v25** — STAGGERED-RELAUNCH recovery (the standing "stagger cold-start refreshes" backlog
  item, finally exercised as an operational procedure). INCIDENT: WSL host **rebooted** ~12:10 UTC
  (`uptime` = `up 7 min`), killing BOTH engines; v2's log ended cleanly on the 2026-07-25 16:00 rebalance
  with `errors=0` and no traceback → host kill, not a crash (v23 signature). v2 missed the 00:00 + 08:00
  Jul 26 boundaries; the book sat untouched on the venue (32 pos, gross $1508, uPnL +$42.9, avail $3299 —
  no liquidation risk). KEY DIFFERENCE FROM PRIOR RECOVERIES: v1 had already been relaunched ~12:15 and was
  mid-cold-start, so I did **not** immediately relaunch v2 — launching into a concurrent 540-symbol refresh
  is the documented cause of the 418 storm. Confirmed the hazard was real: v1's cold refresh tripped a 418
  and parked it in a 900s backoff, and a probe showed the IP **flapping** (`200`, then `418 418`) rather
  than hard-banned. Polled 3 symbols every 45s until one round came back **3/3 200** (12:38:25Z, after ~9
  min and 13 rounds of flapping), launched v2 in that window KEEPING the DB + APPENDING the log. Result:
  **538/542-ok refresh on the FIRST tick**, one-shot rebalance to the CURRENT `as_of=2026-07-26 08:00`
  target (correctly did NOT replay the missed 00:00 cycle), `orders placed=9 skipped=1 errors=0 retrying=0
  papered=1`, STATUS→OK. Compare the un-staggered restart the previous night: `125 → 305 → 538` across 4
  failed ticks. LESSONS added to the Relaunch-v2 bullet: (a) after a host reboot, CHECK the other engine's
  state before relaunching and wait out its cold refresh; (b) gate the launch on **3/3 clean 200s in one
  round**, since a single 200 is meaningless on a flapping IP; (c) there is nearly always slack to spend —
  the catch-up rebalances to the current target no matter how many boundaries were missed. ALSO: `CronList`
  returned "No scheduled jobs" (the session cron dies with the host, per v23) → recreated as `13 */2 * * *`.
  Reconcile dust drifted +$0.29 over ~18d (−$2.93 → −$3.22), well inside the $5 tolerance and NOT growing
  materially — benign testnet wallet drift exactly as diagnosed in v21. All-in P/L (prod-funding basis)
  **+$113.54 / +2.27%** vs the $5,000 seed. Still-open backlog: an engine heartbeat, and a shared/staggered
  cold-start kline cache so this stays a procedure rather than a manual wait.
- **2026-07-25 v24** — FALSE-HANG CAVEAT (a slow refresh ≠ a hang). INCIDENT: WSL host was **suspended
  ~35h** (machine asleep; `uptime` showed NO reboot + proc etime continuous — a suspend freezes the
  process, so it logged nothing and missed 4 boundaries). On resume the cold 540-symbol refresh tripped a
  **418 IP ban**; the `min_refresh_fraction=0.80` guard correctly REFUSED to rebalance on the partial
  panels (125/542, then 305/542) — book never traded on ragged data. The log then went quiet ~9 min and,
  with `IP=200`, I nearly called it a HANG and PGID-killed it — but a re-check showed the refresh ok-count
  was **CLIMBING (125 → 305 → 538)**, i.e. the engine was inside a slow/throttled full refresh, actively
  RECOVERING, not hung. Held off; it completed the 538-ok refresh, rebalanced to the **current** 16:00 Jul
  25 target (one shot, NOT replaying the 4 slept-through cycles), `errors=0`, STATUS→OK. LESSON added to the
  HUNG-engine bullet: `log-frozen + IP-200` is NOT sufficient to call a hang — a full refresh freezes the
  log for MINUTES legitimately; **grep the last few `klines refreshed: N ok` lines and if N is climbing, the
  engine is recovering — do NOT kill** (a kill interrupts recovery + fires a fresh cold refresh into the
  ban). Only conclude hung if the ok-count is NOT progressing across a real ≥5-min window. Reinforces the
  suspend/resume + cold-refresh-418 failure mode (2nd occurrence) → backlog: stagger engines' cold-start
  refreshes / shared kline cache / post-resume backoff, and an engine heartbeat to kill the ambiguity.
- **2026-07-18 v23** — V2-TRACK MONITOR now driven by a **CronCreate session cron** + WSL-reboot recovery
  documented (user directive: "this must be tracked by the skill"). Two additions. (1) **Session-cron
  loop** (see "Session-cron alternative" under Self-paced loop): the v2 monitor runs every 2h at :13
  local via a recurring CronCreate job whose payload is the verbatim v2-only tick prompt; the cron is the
  cadence (no ScheduleWakeup). It's session-only/in-memory → does NOT survive a session reset and
  auto-expires ~7 days, so `CronList` returning "No scheduled jobs" means the loop stopped → recreate
  with `cron:"13 */2 * * *"`. This is exactly what happened 2026-07-18 (cron silently dropped on a session
  reset; engine kept trading; recreated). (2) **WSL-reboot recovery (2026-07-13, v2)** — the healthcheck
  correctly flagged `STATUS: ALERT proc=DOWN` after the **WSL host rebooted ~19:53 UTC** (`uptime` showed
  `up 3:04`; both v1+v2 engines gone; v2 log ended cleanly on the 16:00 rebalance with NO traceback → host
  kill, not a crash). Recovery per the v16 playbook: verified IP clear (`curl … klines → HTTP 200`), then
  relaunched v2 **KEEPING the DB** + **appending** the log (`[relaunch] … WSL host reboot …`). Came back
  `STATUS: OK`; the v20 startup reconcile un-stuck SIRENUSDT (frozen paper since Jul 10) back to strategy-
  managed; the next 00:00 rebalance fired clean (`540 klines ok`, errors=0) → recovery confirmed. Lessons
  reinforced: (a) a **host reboot kills BOTH engines** — after any WSL restart, check v1 AND v2 (v1 lives
  in the quant-research worktree/session, out of the v2 cron's mandate — flag it to the user, don't touch
  it); (b) `proc=DOWN` + a clean final log line = host kill (relaunch, KEEP DB, append log), distinct from
  a crash (traceback) or a hang (proc=up, log frozen mid-storm); (c) relaunching a reboot-killed engine is
  PRO-test recovery, not interference.
- **2026-07-09 v22** — MIN-NOTIONAL BUFFER + -4164 classified benign. The 00:00 Jul 9 rebalance sent a
  SELL SKYAIUSDT leg sized $5.31 at the close-proxy price (just above Binance's $5 MIN_NOTIONAL floor);
  by the staggered execution (~00:15) SKYAI's price had drifted down and Binance re-evaluated the notional
  BELOW $5 → rejected `-4164`. The healthcheck flagged it `REAL order errors x1` (false alarm — it's a
  benign ~$5 dust leg; impact: SKYAI position off ~$5 on a $1491 book, self-corrects next rebalance). Fixes:
  (1) ENGINE (`engine.py`) — new `PortfolioConfig.min_notional_buffer=1.20`; the post-floor guard now skips
  legs sized below `MIN_NOTIONAL × buffer` ($6 for a $5 floor), so a normal ~15-min price move can't push a
  just-above-floor leg below it at execution. Live-execution-only — does NOT touch target-weight parity
  (skipped dust legs are held at current, bounded by one filter-notional off target, self-correct next
  rebalance, per the guard docstring). (2) MONITOR — `-4164` now classifies as `min-notional dust legs`
  INFO (not REAL); it's a benign <$5 dust boundary that applies on production too, not a strategy break.
  Added `test_min_notional_buffer_skips_boundary_dust_leg`; full portfolio+live scope 258 passed / 0 failed.
- **2026-07-08 v21** — RECONCILE DUST STEP diagnosed BENIGN (no code change). At the 08:00 Jul 8 rebalance
  the `portfolio_v2_pnl.py` opening dust stepped from the long-stable +$1.11 to −$2.93 and HELD there (not
  income-ledger lag — it didn't settle back in ~50min). Full diagnostic: (1) dedup is CLEAN — raw vs
  composite-key-deduped income are bit-identical (0 rows dropped), so NOT the tranId/tradeId collision I
  suspected; (2) NO unrecorded income type (only TRANSFER/REALIZED_PNL/FUNDING_FEE/COMMISSION); (3) account
  fields SELF-CONSISTENT to 8 decimals (`totalMarginBalance == wallet + totalUnrealizedProfit` exactly).
  CONCLUSION: the residual = `wallet − Σ(income rows)` = −$2.93; on PRODUCTION `wallet == Σ(income)` is a
  hard invariant, but TESTNET's matching engine drifts its wallet bookkeeping ~$1-4 from the income ledger.
  **The headline all-in P/L is UNAFFECTED** — it's anchored to `equity(totalMarginBalance) − seed`, not the
  income sum. The −$2.93 is within the $5 reconcile tolerance (verdict stays OK). ONLY act if the residual
  EXCEEDS $5 (real GAP) — then re-run this diagnostic: a genuine missing-cost bug shows as a dropped income
  row (dedup) OR a new incomeType OR account-field inconsistency; if all three are clean it's testnet drift.
  Do NOT tighten the $5 tolerance (it's sized to absorb this testnet noise). Won't occur on real money.
- **2026-07-06 v20** — PAPER-FALLBACK OVER-ACCUMULATION FIXED — transient errors no longer permanently
  freeze liquid symbols (`src/crypto_trade/portfolio/engine.py`), on user directive after a `book?`
  query surfaced it. FINDING: the paper set only ever GREW and papered on the FIRST failure of ANY
  code — so LINK/HEI (liquid, tradeable) hit a one-off `-4131 PERCENT_PRICE` (a *transient* thin-testnet-
  book rejection) and got frozen as paper FOREVER, while their real positions sat on the venue diverging
  from the strategy (LINK: real LONG +$64 vs paper SHORT −0.020 — opposite sign; SIREN's frozen short is
  what bled the −$114 funding artifact). Fix: (1) split codes — only `-4131` is now TRANSIENT (strike-
  based: retried, papered only after `PAPER_STRIKE_N=3` consecutive fails); all others keep paper-on-
  first-failure. (2) `retrying` counter added to `execute()` + the `orders …` log line (a transient retry
  is INFO, not an error). (3) startup `_reconcile_paper_vs_positions()` — a symbol must never be BOTH
  papered AND holding a real position; if it is (LINK/HEI/SIREN/PUMP) it's un-stuck so the next rebalance
  manages the real position toward target again (TLM/EVAA, no real position, stay papered). Strike state
  is in-memory (resets on restart — acceptable). Added 5 tests (transient-retry, paper-after-N, reset-on-
  fill, reconcile-unstick, reconcile-noop); full portfolio+live scope 257 passed / 0 failed; ruff clean.
  Healthcheck v20: surfaces `retrying=` as INFO. On real money none of this triggers (prod symbols trade).
- **2026-07-06 v19** — ENGINE paper-fallback now covers the set_leverage step (`src/crypto_trade/
  portfolio/engine.py`) — the v18 "deferred" gap, done after the user pushed "why not restart?". Root
  cause on inspection: `-4141` surfaces from `set_leverage`, which `_ensure_leverage` CATCHES AND
  SWALLOWS, so the order was still attempted and failed with a `-1111` precision cascade — meaning
  adding `-4141` to `_TESTNET_UNTRADEABLE` alone did NOTHING (my first assumption was wrong; verified by
  reading the code). Fix: `_ensure_leverage` now returns `bool` — `False` when set_leverage returns a
  code in the new `_LEVERAGE_UNTRADEABLE={-4141,-1121,-4140}` subset (deliberately EXCLUDES the benign
  `-4046/-4061` "leverage already set" quirks, which must fall through to the order). `execute()` papers
  it on testnet / skips it as an error leg on production (papering a REAL position would fabricate P&L —
  production behavior unchanged: an untradeable symbol is still a missing leg, which is correct). Added
  `tests/test_portfolio_engine_execute.py` (3 tests: testnet-paper, production-skip, benign-quirk-still-
  places) — the FIRST coverage of the live-engine execute() path. Full suite 252 passed / 0 failed; my
  edits lint-clean. Restarted the engine (v16 playbook: PGID-kill, KEEP DB, append log) to put it live;
  TLM will PAPER (not error) at the next rebalance that targets it. NOTE restart risk was low (v1
  steady-state, IP clear, single refresh proven fine at 16:00+00:00); a restart alone would NOT have
  fixed it — the code change is what matters, and it only takes effect at the next rebalance anyway.
- **2026-07-06 v18** — `-4141 "Symbol is closed"` classified as testnet artifact + per-symbol error
  grouping (`scripts/portfolio_v2_healthcheck.py`). The 00:00 Jul 6 rebalance targeted a BUY TLMUSDT leg;
  testnet has **NO TLM listing** (prod: status=TRADING qtyPrec=0 stepSize=1; testnet: NOT LISTED), so
  `set_leverage` returned `-4141 "Symbol is closed"` and the order returned `-1111 "Precision over maximum"`
  (the engine loads precision from testnet, which lacks TLM → default precision → non-integer qty). The
  healthcheck counted BOTH codes as REAL (neither was in TESTNET_ERR) → false `STATUS: ALERT REAL order
  errors x2`. Fix: (a) added `-4141` to TESTNET_ERR (same family as -1121/-4140 — a prod-listed name absent
  from testnet, trades fine on production); (b) rewrote the classifier to group codes PER SYMBOL (one failing
  leg emits 2 codes; occurrence-counting double-flagged it) and treat `-1111` as a benign CASCADE when the
  same symbol also threw a listing artifact. Verified: STATUS flips ALERT→OK, TLM → INFO x1. **KNOWN
  testnet-fidelity gap (NOT a production bug):** the engine's paper-fallback trigger set (`-1121/-4131/
  -4140/-4411`) does NOT include `-4141`, so a prod-listed/testnet-unlisted symbol hard-errors + leaves a
  MISSING leg (TLM ~$93, benign) instead of being papered. On real money TLM (and any halted name) is
  handled correctly — the symbol simply can't be traded, a missing leg is unavoidable, and papering a REAL
  position would be wrong. OPTIONAL testnet-only improvement: add `-4141` to the engine paper-fallback set so
  the smoke-test book holds the intended weight as paper (keeps parity clean). Deferred — needs a restart and
  only affects testnet fidelity, not production. See universe-hygiene bullet.
- **2026-07-05 v17** — FUNDING NOW REPRICED TO PRODUCTION RATES (`scripts/portfolio_v2_pnl.py`), on user
  directive: "do not account the funding from testnet, it must be the funding from prod binance." The v15
  report summed the raw testnet FUNDING_FEE (−$108.82, dominated by SIREN's −$113 cap-slam) into the
  headline all-in P/L and only showed prod as a forward run-rate footnote — so the P/L read +1.34% when the
  real number is +3.56%. Now every real funding settlement is repriced per (symbol, funding_time) via
  `prod_income = testnet_income × (prod_rate / testnet_rate)` (notional cancels; rates from the public
  historical `fapi/v1/fundingRate` on both hosts). `funding(PROD)` (+$0.73 over 12d, ~neutral) replaces
  testnet funding in the headline; raw testnet funding is retained ONLY for the reconcile-to-wallet check.
  Verified: all-in flips +1.34% → +3.56%, SIREN testnet −112.83 → prod +1.64, reconcile still ties to the
  cent ($1.11 dust). 887/925 settlements repriced (38 unmatched = testnet fundingRate gaps, assumed 0 prod
  → immaterial at tiny prod rates). This is the number that carries to real money.
- **2026-07-05 v16** — HUNG-ENGINE failure mode + PGID-kill recovery documented (v2 section). After a WSL
  reboot, a ~3h DNS outage spanned the 08:00 boundary and an IP-level 418 storm followed on relaunch (v1+v2
  both cold-started 540-symbol production refreshes → shared IP → 418). The v2 engine then HUNG: `proc=up`
  but the log froze at 11:24 UTC mid-418-storm (2.5h). Diagnosed as a genuine process hang (direct curl to
  the engine's exact klines URL returned 200 → IP clear), killed the hung proc by PROCESS-GROUP
  (`kill -TERM -- -<pgid>`; `pgrep -f`/`pkill -f` self-match the shell — a false "STILL ALIVE"), relaunched
  KEEPING the DB (append log). Came back clean: 0 errors since restart, 21 positions intact, reconciles to
  the cent. Documented: (a) hung ≠ crashed (proc stays up), (b) log-silence is only suspicious while the
  engine SHOULD be logging, (c) the crash-resume relaunch must KEEP the DB + append the log (the old recipe
  wrongly said `rm` DB + truncate). Backlog: engine heartbeat to detect a hang without the log heuristic;
  stagger v1+v2 COLD-START refreshes (the stagger only covers steady-state 8h rebalances, not restart-time).
- **2026-07-01 v15** — ALL-IN COST ACCOUNTING (`scripts/portfolio_v2_pnl.py`), on user request to make PnL
  "as realistic as possible / consider all costs." The healthcheck `uPnL` was MARK-ONLY (open-position
  mark-to-market) — it omitted funding, commission, and realized. New report reconciles to Binance's OWN
  ledger: `seed + realized + funding + commission == wallet balance` (ties to the cent → by construction
  every cost is captured), `+ unrealized == margin balance = true equity`, `− seed == ALL-IN P/L`. Prints
  equity, all-in P/L vs seed, trading-attributable breakdown, per-symbol funding, and a reconcile verdict.
  Findings on the live v2 account: all-in P/L ~+$16 (+0.32% vs $5k seed); the headline mark uPnL (+$64) is
  ~2/3 offset by funding (−$76.94, almost ALL from the SIREN short) — funding is the dominant cost. Gotchas
  fixed while building: (a) a fill emits REALIZED_PNL + COMMISSION under the SAME `tranId`, so income
  de-dupe MUST key on incomeType+symbol+time (tranId alone dropped realized rows → false −$35 gap); (b) the
  reconcile residual is a fixed ~$1.11 pre-existing OPENING balance (income ledger sums to $4950.98 vs
  wallet $4952.09) — labeled "opening dust", only warns if it GROWS (= a missing bucket). TESTNET funding
  rates flagged NON-representative. Now run each tick beside the healthcheck. v1 has no equivalent yet —
  port for the real-money cutover (where funding/fees are the true costs).
  **PRODUCTION FUNDING OVERLAY** (added same day, user request "use the REAL binance funding endpoint not
  testnet"): the report also queries PRODUCTION `fapi.binance.com/premiumIndex` (public, no auth — same
  host the engine uses for klines) for the CURRENT book and prints the real-rate funding run-rate. Finding:
  testnet funding is a pure artifact — SIREN settles at the testnet cap −3.75%/8h (cost −$78.94, 25/25
  intervals PAID as a short) whereas its REAL rate is +0.0190%/8h (opposite sign; our short would EARN a
  cent/day). Across the whole ~dollar-neutral book, REAL funding runs ~−$0.08/day (~−$29/yr, negligible)
  vs testnet's ~−$9.4/day. So the strategy's true edge (~+$92 ex-funding price/execution) is masked on
  testnet by artificial funding; on production funding is near-neutral. Sign convention verified against
  live data (short + negative rate = we pay; long + positive rate = we pay).
- **2026-06-30 v14** — MONITORING BLIND-SPOT FIX (first non-zero `errors=` of the v2 run): the 00:00
  UTC Jun 30 rebalance logged `orders placed=6 errors=2` — both were **502 Bad Gateway** HTML responses
  from the testnet edge on the `SELL INJUSDT` + `SELL XPLUSDT` POSTs (transient infra, `Powered by
  tengine`, NO JSON `"code"`). The engine handled it correctly: logged the 2 failures, placed the other
  6, papered 2, advanced `last_rebal`, no traceback; the 2 off-target legs (a sub-$50 INJ flip + a $5 XPL
  trim) self-heal at the next rebalance (engine trades to target off ACTUAL exchange positions each
  cycle). NOT a strategy/code fault, NOT an alert. BUT `portfolio_v2_healthcheck.py` only classified JSON
  `"code":` rejections, so a 502 (no code) made `errors=2` pass as **silent STATUS=OK** — a real gap.
  FIX: `_log_scan` now counts engine `order ... failed: 5\d\d` lines as `gateway_errs` → surfaced as an
  INFO line (`testnet gateway 5xx order errors xN … self-heal at next rebalance`), AND any `last_errs`
  not matched by code/gateway is surfaced as `unclassified order errors xN (review log)` so errors>0 is
  NEVER swallowed. STATUS stays OK for transient 5xx (correct — observational), still ALERTs on real
  `"code"` rejections. Verified against the live log (shows the x2 INFO). Note for v1 cutover: the v1
  `portfolio_healthcheck.py` likely has the same blind spot — port this when porting the guards/stagger.
- **2026-06-24 v13** — ROOT-CAUSE FIX (the standing v11/v12 follow-up): the 418 contention happened
  because all the engines hammer production klines at the SAME 8h boundary. `PortfolioConfig.rebalance_lag_seconds`
  (v2 runner = **900 / 15 min**) staggers v2's rebalance 15 min PAST the candle close — non-blocking
  (the run loop keeps polling; `last_candle` only advances after the rebalance fires; `due = candle
  open_time + interval + lag`). Parity-safe: still the just-closed candle's signal, same target, just
  executed later. So **v2 now rebalances at ~HH:15, not HH:00** (00:15 / 08:15 / 16:15) — clear of the
  v1/paper engines' boundary refresh, so the 418 contention stops at the source. The guards (v11/v12)
  remain the safety net if it ever recurs. Log shows `staggering rebalance ~Nmin` when a candle closes.
  REMAINING follow-up: port the guards + resilience + this stagger to the v1 engine before v1 real money.
- **2026-06-24 v12** — INCIDENT (recurrence) + STRONGER FIX: the 08:00 UTC rebalance degenerated AGAIN
  (net −$1,612) and the v11 guard did NOT fire (`collapse-aborts: 0`). The 418 contention recurred at
  the boundary (`klines refreshed: 171 ok` vs 540), but the v11 `min_active_universe=100` guard was the
  WRONG metric — the active count stayed > 100 while the *seasoned-eligible* rank set collapsed (the
  partial fetch leaves GAPS in trailing candles → coins lose per-bar seasoning → the rank-21-40 denom
  shrinks → a few oversized non-neutral names). ROOT: `refresh_data` catches a 418 fetch failure as
  `skipped += 1` "delisted", so a 418-storm silently truncates the panel. STRONGER FIX:
  `PortfolioConfig.min_refresh_fraction` (v2 runner sets **0.80**) — `run_once` now records the refresh
  ok-count and RAISES if `ok/total < 0.80` (caught by the poll loop → retries next tick when contention
  clears). This catches the partial refresh DIRECTLY (171/542 ≈ 31% → abort), the root signal the
  active-count guard couldn't see. Reconciled the book the same way (clear last_candle → relaunch →
  `540 ok` → 20 names, net +$232/+15%). The v11 `min_active_universe` guard is kept as a backstop.
  Open follow-up still stands: stagger the engines' kline refreshes / share a cache so the 418
  contention stops happening at the boundary.
- **2026-06-24 v11** — INCIDENT + FIX: the 00:00 UTC rebalance traded a DEGENERATE book (gross $1.6k→
  $2.9k, net +$240→**−$1,495**, 4 oversized shorts at w −0.13/−0.15). Root cause: a Binance **`418`
  rate-limit ban** (concurrent engines all refreshing klines at the 8h boundary) hit the refresh
  MID-FETCH — only 236/540 coins updated; the missing ones were silently logged as "skipped
  (delisted)". `forming_from_close` then saw a collapsed active universe → the rank-21-40 book
  degenerated. Diagnosis: data freshness showed most coins stuck 1-2 candles stale + `538 skipped`;
  a fresh recompute gave the proper 20-name dollar-neutral book (net −0.004). FIX (2 parts):
  (1) **GUARD** `PortfolioConfig.min_active_universe=100` — `compute_plan` raises if the active
  universe collapses below the floor (caught by the poll loop → retries on complete data, never trades
  a ragged panel). (2) **RECONCILE** — stopped v2, cleared the `portfolio_last_candle_BTCUSDT`
  engine_state key to force ONE corrective rebalance, relaunched on the guarded code; the refresh came
  back `540 ok` and the book reconciled to 20 names / net +$180 (+11%), errors=0. Procedure to force a
  corrective rebalance: stop engine → `sqlite3 …delete from engine_state where key='portfolio_last_candle_BTCUSDT'`
  (KEEP the rest of the DB) → relaunch. **FOLLOW-UPS:** the 418 is from kline-refresh CONTENTION across
  concurrent engines — consider staggering refreshes / a shared kline cache. The v1 engine
  (quant-research) has the ORIGINAL engine.py — it lacks BOTH this guard AND the v10 network-resilience
  fix; port them before v1 real-money.
- **2026-06-23 v10** — INCIDENT + FIX: the v2 engine CRASHED on 2× `httpx.ConnectError [Errno 104]
  Connection reset by peer` during a candle-check kline fetch — the `run()` poll loop had no exception
  handling, so a transient network blip propagated out and killed the process (book left unmanaged).
  Fix: wrapped each tick in try/except (`engine.py:run()`) → log a one-liner `tick error #N` + retry
  next poll, never crash. Relaunched on the hardened code KEEPING the DB (paper state + held + last
  candle preserved → resumed mid-cycle, no spurious rebalance). Book intact (20 positions), STATUS OK.
  Benefits v1 + v2 (shared engine). See the v2-section "Network resilience" note.
- **2026-06-23 v9** — v2 PARALLEL TRACK added (rank-21–40 XS-mom on a separate testnet account) +
  PAPER-FALLBACK (testnet-untradeable symbols tracked as paper) + universe hygiene (NON_COIN_PERPS).
- **2026-06-22 v8** — HANDS-OFF mandate (user: "never interfere, we need to test this"). The
  monitor now OBSERVES + INFORMS only; never flattens/recommends the kill-switch on drawdown.
  Alert set narrowed to TEST-INTEGRITY (engine/parity/candle/errors); DD/PnL/tilt/turnover are
  observational test-results (digest only). Kill-switch is user-only. Drawdown is expected.
- **2026-06-22 v7** — calibration fix: turnover SPIKE threshold 15 -> 30 + cold-start = first row
  only. The 15 threshold false-fired on normal ~16-18-leg active rebalances (backtest averages
  ~18 tickets/candle; live steady-state confirmed ~18). No real issue — a monitor false positive
  caught + fixed live. Turnover parity is GOOD (live ~18 ≈ backtest ~18).
- **2026-06-21 v0** — initial skill: live-API health check (`scripts/portfolio_healthcheck.py`),
  STATUS OK|ALERT, threshold alerts, benign list, engine-down relaunch, self-paced ScheduleWakeup
  loop. Deployed against baseline-v3 on testnet ($10k/3x). Task #189.
- **2026-06-21 v1** — roadmap #1: **parity/drift check** (`scripts/portfolio_parity_check.py`).
  Recomputes the v3 strategy target (same code + close-proxy forming) and compares per-name to the
  LIVE book; flags MISSING / EXTRA / WRONGSIDE / MISSIZED, tolerates price-drift + dust, notes 8h
  boundary transients. Monitor now runs health + parity each tick; either ALERT or DRIFT pings.
- **2026-06-21 v6** — roadmap #5 **trend-aware alerts** (`portfolio_trend_alerts.py`), #6 **turnover
  ledger** (`portfolio_turnover_ledger.py`), #7 **pre-flight + kill-switch** (`portfolio_preflight.py`
  + `portfolio_killswitch.py`, stop-engine-first reduceOnly flatten). User constraint baked in: all
  checks read-only + non-competing with the trade loop (CSV/log/testnet-signed; engine uses production
  klines pool + its own DB). Monitor now runs 8 checks/tick; preflight+killswitch are on-demand.
  ROADMAP #1–#7 COMPLETE.
- **2026-06-21 v5** — roadmap #4: **fill-quality / slippage** (`scripts/portfolio_fill_quality.py`
  + read-only `auth_client.get_user_trades`), MODE-AWARE per the user's paper-vs-testnet-vs-live
  distinction. Reports effective fee rate (real everywhere, ~5bps expected) + adverse slippage vs the
  close-proxy reference; testnet slippage flagged NON-REPRESENTATIVE (INFO, not an alert); paper=n/a;
  live=real alert source. Verified live: MODE=TESTNET, fee 3.9bps (vs 5bps assumed), slippage +28.5bps
  correctly flagged testnet-noise. Added the "Run modes" section. Monitor now runs 6 checks/tick.
- **2026-06-21 v4** — roadmap #3: **drawdown / equity-curve tracking**
  (`scripts/portfolio_drawdown_check.py`). Reads the logged equity curve; reports account DD (vs peak)
  + strategy-equiv DD (cumPnL/notional, comparable to backtest −23%); BREACH alert on account DD >20%
  or strat-equiv worse than backtest×1.5. Monitor now runs 5 checks/tick. Account DD is
  leverage-amplified vs the backtest DD (testnet account < $10k notional) — both reported.
- **2026-06-21 v3** — roadmap #2: **PnL attribution + daily digest** (`scripts/portfolio_digest.py`
  + read-only `auth_client.get_income`). Logs an equity snapshot each tick to
  `data/portfolio_equity.csv`; reports 24h realized/funding/commission/unrealized PnL attributed
  per-name from `/fapi/v1/income`; pushes a digest once per UTC day (DIGEST_DUE flag + --mark-pushed).
- **2026-06-21 v2** — roadmap #1b: **candle-integrity check** (`scripts/portfolio_candle_check.py`),
  per the user: the signal close must always be a COMPLETE candle, never the forming one. Verifies no
  forming candle leaked into any coin CSV (close_time > now) + data isn't stale (missed refresh).
  Confirmed clean live (667 coins, 0 leaks). Monitor now runs health + candle + parity each tick.
  GUIDING MANDATE (user): make the bot run as close as possible to the backtest, solve any unexpected
  issue, be the user's eyes when away — contribute proactively, every improvement lands in this skill.
