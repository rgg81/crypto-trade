---
name: cup50v2-monitor
description: Monitor the four CUP-50 v2 forward paper desks (winner, both runners-up, equal-risk ensemble), report every desk's performance on every tick, diagnose integrity failures, and observe without intervening. Use when asked to check the CUP-50 v2 desks, cup50v2 paper PnL, ensemble-eq3, the capital rule's standing, live/backtest parity, deployment-authority or pin drift, stale boundaries, append-invariance aborts, shared market-cache drift, or safe engine recovery.
---

# CUP-50 v2 Monitor

Monitors the six-month forward stage in
`/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top50-v2`.

Four desks under `paper-cup50v2/`: `winner`, `runner-up-1`, `runner-up-2`, and `ensemble-eq3`.
Each replays one frozen lane through the tournament's own evaluator. The ensemble is not a special
case — it is one more frozen source bundle that happens to instantiate the other three.

## Why there are four

Across six editions the one durable finding is that in-sample rank carries almost no information
about out-of-sample rank at the top, and CUP-20 measured a forward rank correlation of **−1**
against its own leaderboard. Deploying the single winner is a bet on a ranking the evidence says is
noise. So the final stage runs four desks and the capital decision reads the **forward record**,
never the leaderboard.

This means: **a desk losing to another desk is the experiment working, not a problem.** Do not
recommend switching capital toward whichever desk is ahead this month. That is the ranking error
the four-desk design exists to avoid, arriving by a different route.

## Preserve the experiment

- Observe and report. Never flatten, hedge, resize, re-weight, or edit a signal because of
  performance. Every intervention ends the test it was meant to protect.
- **PnL, drawdown, Sharpe, turnover and exposure are test results, not operational alerts.** A
  losing month is data. A drawdown is data.
- Alert only on **test-integrity** failures — the named classes below. The question is always "can
  the record still be trusted", never "is the book doing well".
- Never recommend a strategy intervention on the basis of losses. If asked to, say why not.

## Never edit desk artifacts to make a check pass

The ledgers under each desk are the record: append-invariant, written once per row, never revised.
Do not delete a ledger row, rewrite a rendering, hand-edit an `integrity.json` or a `boundaries/*`
record, or re-bind a hash to whatever is on disk.

Six months produces exactly one thing — an unedited record. **A red check with intact evidence is
worth incomparably more than a green one without.**

## The desks are paper-only, by construction

`run_cup50v2_paper.py` has no signed client and no order path. The only network client in its
import graph is `PublicMarketDataClient`. There is nothing to disable and no key in use. A proposal
to add an order path is a different system and a different conversation.

## One cache, four desks

The engine builds **one** market-cache generation per boundary and replays all four desks against
those exact bytes. Two consequences:

- A cache or fetch failure hits all four desks at once. Four desks reporting the same failure at
  the same boundary is **one** fault, not four — diagnose the generation, not the desks.
- A difference between two desks is a difference between two strategies, never between two fetches.
  If two desks disagree about a price, that is a real integrity failure, not a data race.

The engine lock is held once at `paper-cup50v2/engine.lock` for the whole field.

## Every check reports every desk's performance

**Report a performance line for all four desks on every tick, without being asked.** Not only on a
status change, not only when something is wrong, and not only in the 24-hour digest.

```
uv run python scripts/cup50v2_paper_healthcheck.py
uv run python scripts/cup50v2_paper_digest.py
```

The digest reads `ledger/forward_returns.parquet`. Two distinctions in it are load-bearing, and
both were wrong in the first version of the script:

- **Bars are not days.** One row per 8h decision, three per day. The digest compounds to UTC days
  before computing anything, so its numbers mean what the tournament's cells mean.
- **Bridge is not official.** The ledger begins when the *sealed window* ends, not when the desk
  launched, so its early rows are real out-of-sample data that existed before the desk went live.
  Only the `official` phase is the forward record and only official days count toward the capital
  rule. Report them apart, always. Adding them would credit a desk with performance it never
  traded — and the bridge is 22 days of it, sitting right there, labelled in a column that is easy
  to ignore.

The digest also never reads `historical_daily_returns.parquet`, which sits beside it and holds the
pre-launch replay used for the tearsheets.

A tick report is two blocks: the integrity line per desk (from the healthcheck), then the
performance line per desk (from the digest) — days, total return, annualised growth, volatility,
max drawdown. Four desks, four lines. If a desk has no forward returns yet, say so for that desk
rather than omitting it; a missing row reads as a desk that is fine.

**This is reporting, not ranking, and the distinction is load-bearing.** Print the numbers for all
four every time and let them be compared by the person reading. Do not sort the desks by
performance, do not name a leader, do not describe one desk as ahead of another, and do not compute
a provisional capital winner. The capital rule is read **once**, after 183 official days, and the
four-desk design exists precisely because in-sample rank did not predict forward rank. Turning a
weekly report into a weekly verdict is that same error arriving by a different route.

Losses are reported the same way as gains: as data, in the same format, with no commentary about
what should be done. There is nothing to do about a losing month.

## Run the standard check

```
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top50-v2
uv run python scripts/cup50v2_paper_healthcheck.py
```

`STATUS OK` means every desk published its boundary and none is late. `STATUS ATTENTION` names the
desk and the class. Add `--json` for a machine-readable form.

### Before launch

`PENDING` with `capital NOT-LAUNCHED` is correct and not an alert — no `launch.json` exists yet.
After launch the same empty desk reports `NO-TICK` and `ATTENTION`. If you ever see `PENDING`
alongside a launched capital line, the healthcheck is lying and that is itself the finding.

## The named failure classes

Alert on these and nothing else:

1. **NO-TICK** — launched but never published a boundary.
2. **LATE** — more than 8h45m past the boundary it owes.
3. **FAIL** — last attempt recorded an exception. Read `attempt.json` for the traceback.
4. **Deployment drift** — a byte bound in `deployment-manifest.json` no longer matches. This is
   `DeploymentChangedError` and it means the desk is no longer replaying what was frozen.
5. **Lineage drift** — the release no longer ranks the desk's lane, or the desk's centre differs
   from the nomination's frozen centre.
6. **Append-invariance abort** — a row already on disk came back different. Nothing was written.
   The exception names the key, the column and both values. **This is evidence; preserve it.**
7. **Ensemble member drift** — a finalist's frozen bundle or `finalists.json` changed. The ensemble
   is defined over exactly three finalists at their frozen centres; anything else is a new lineage.
8. **Cache generation failure** — the shared generation could not be built. Expect all four desks
   to fail together; treat as one fault.
9. **Engine lock contention** — two engines. The watchdog should make this impossible; if it
   happens, find the second process before restarting anything.
10. **Clock or boundary skew** — a published boundary that is not on an 8h grid, or ahead of now.

## Diagnose in order

1. `scripts/cup50v2_paper_healthcheck.py` — which desks, which class.
2. If all four failed at the same boundary → the shared generation. Read `paper-cup50v2/boundary.json`.
3. `paper-cup50v2/<desk>/attempt.json` — the traceback for a single-desk failure.
4. `logs/cup50v2_paper.log` and `logs/cup50v2_watchdog.log` — what the engine and watchdog did.
5. Only then consider recovery.

## Recovery

The engine is safe to restart: every tick is idempotent per boundary, a desk that already published
its boundary reports `ALREADY` and is skipped, and the append-invariant ledgers refuse a rewrite
rather than accepting one. Restart with the watchdog, never by hand:

```
bash scripts/cup50v2_paper_watchdog.sh
```

It does nothing when an engine already holds the lock, and nothing at all before `launch.json`.

**A killed tick is safe.** Nothing is published until the tick completes; a partial tick leaves an
`attempt.json` in `RUNNING` and no boundary record, and the next run redoes that boundary from the
shared cache. There is no half-published state to repair.

## The capital rule is pre-registered — read it, do not re-derive it

After **≥ 183 official days**, the capital candidate is the desk with the highest official-phase
**1× cell score q**, among desks with official **maxDD ≤ 20%** and **q ≥ 50**. Ties break by lower
maxDD. If no desk qualifies, **no capital is deployed and the edition closes without deployment** —
that is a legal, pre-registered outcome and not a failure to be worked around.

Before 183 days the rule is not readable and the healthcheck says `ACCRUING`. Do not compute a
provisional winner, do not rank the desks in a report, and do not let a strong early desk become
the assumed answer. The whole design rests on the decision being made once, on a full record.

## Alerts are written in-session

Report in the session. Do not send push notifications and do not open external channels.

## Report concisely

Every tick: the integrity line and the performance line for **all four desks**, plus the capital
standing. That is the whole report when nothing is wrong — brief, complete, and the same shape
every time so a change is visible at a glance.

When something is wrong, add the class, the desk, the boundary, and what you did or did not do.

## Provenance

The tournament's own record lives in `tournament/cup50v2/`: `amendments/` (A1–A13, including the
defects found during the edition and how they were ruled), `findings/` (F1–F2, disclosed lane
findings), `activation-freeze.json`, and the charter. Read them before concluding that something
about this desk is surprising — several surprising things are already written down there,
including the one evaluator file that drifted during the sealed observation (A13).
