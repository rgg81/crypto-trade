---
name: top40v5-monitor
description: Monitor the four Top-40 V5 forward paper desks (ranks 1-3 plus the equal-weight ensemble), report every desk's performance and backtest parity on every tick, diagnose integrity failures, and observe without intervening. Use when asked to check the Top-40 V5 desks, top40v5 paper PnL, ensemble-eq3, the capital rule's standing, live/backtest parity, deployment or lineage drift, stale snapshot data, append-invariance aborts, engine lock contention, or safe engine recovery.
---

# Top-40 V5 Monitor

Monitors the forward stage in
`/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v4-r1-v3`.

Four desks under `paper-top40v5/`: `desk-1-team-14`, `desk-2-team-08`, `desk-3-team-09` and
`ensemble-eq3`. Each replays one frozen lane bundle through the tournament's own evaluator. The
ensemble is not a special case — it is one more frozen bundle that happens to name the other three
and combine their target weights at one third each.

## Why there are four

The edition's own evidence says a single-winner deployment is a bet on a ranking that does not hold.
**team-15 led the sealed stage decisively** — block-deletion robustness 1.614 against 0.969 for the
next book, sealed Sharpe +2.113 — **and finished fourth on the historical window at +0.269, inside
its own null band.** Spearman between sealed robustness and historical Sharpe was +0.543: real, and
nowhere near enough to stake one desk on.

So the final stage runs four desks and the capital decision reads the **forward record**, never the
leaderboard.

This means: **a desk losing to another desk is the experiment working, not a problem.** Do not
recommend moving capital toward whichever desk is ahead this month. That is the ranking error the
four-desk design exists to avoid, arriving by a different route.

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
Do not delete a ledger row, hand-edit an `attempt.json` or a `boundary.json`, or re-bind a hash in
`deployment-manifest.json` to whatever is on disk.

The forward year produces exactly one thing — an unedited record. **A red check with intact evidence
is worth incomparably more than a green one without.**

The one thing that is not an edit: withdrawing rows that were computed on **wrong inputs**, before
the official record opens. That is not making a check pass, it is refusing to publish a number the
desk never earned — and it is only legitimate with the whole apparatus attached. Record it in
`paper-top40v5/corrections.jsonl` (hash-chained, append-only, separate from the tournament's
research journal because that journal's event vocabulary was frozen at activation and is release
evidence), state exactly what was wrong and how it was verified fixed, back up the pre-correction
artifacts, and confirm no `official` row is touched. Once the official record has opened, a wrong
input is a finding to report, not rows to withdraw.

## The desks are paper-only, by construction

`top40v5_paper_engine.py` has no signed client and no order path anywhere in its import graph. There
is nothing to disable and no key in use. A proposal to add an order path is a different system and a
different conversation.

## One snapshot, four desks

The engine builds **one** market generation per boundary and replays all four desks against those
exact bytes, hashed into `paper-top40v5/boundary.json`. Two consequences:

- A data failure hits all four desks at once. Four desks reporting the same failure at the same
  boundary is **one** fault, not four — diagnose the generation, not the desks.
- A difference between two desks is a difference between two strategies, never between two fetches.
  If two desks disagree about a price, that is a real integrity failure.

The engine lock is held once at `paper-top40v5/engine.lock` for the whole field.

## Every check reports every desk's performance AND its backtest parity, together

**Report a performance line and a parity line for all four desks on every tick, without being
asked.** Not only on a status change, not only when something is wrong.

```
uv run python scripts/top40v5_paper_healthcheck.py
uv run python scripts/top40v5_paper_digest.py
```

**Both scripts import `crypto_trade.tournament.v5.desk.parity.desk_parity()` — the same function,
not two independently-derived opinions.** That is what "the stats and the parity must raise the same
signal" means at the code level: the integrity report and the performance report read one fact, so
they cannot disagree about whether a desk still matches its backtest. If you add a third place that
reports desk state, import `desk_parity()` rather than re-deriving parity from `attempt.json` — a
second implementation of "what counts as a parity break" is exactly how the guarantee stops holding.

### Parity states

- `OK` — the last tick passed, or failed for a reason that is not a parity break (a fetch timeout,
  an unclosed bar). Parity holds through `verified_through`, the last published boundary.
- `BROKEN` — the last tick's replay genuinely disagreed with the frozen record
  (`AppendInvarianceError` or `DeskParityError`). **The single worst state a desk can report.** The
  live desk and the backtest evaluator it is supposed to BE have diverged. Escalate above an
  ordinary LATE or FAIL; do not let it read as routine.
- `UNVERIFIED` — no reconstruction and no tick yet. Pre-launch only.

An operational failure is never parity-broken. Conflating a transient fetch error with a genuine
divergence would make the strongest signal in the system noisy, and a noisy alarm is the one that
gets ignored on the day it matters.

### Two distinctions in the ledger, both load-bearing

- **Bars are not days.** One row per 8h decision, three per day. The digest compounds to UTC days
  before computing anything, so its numbers mean what the tournament's cells mean.
- **Bridge is not official.** The ledger begins where the historical window ended (2024-02-01), not
  where the desks launched, so its early rows are real out-of-sample data that existed before any
  desk went live. Only the `official` phase — from **2026-09-01** — is the forward record. Report
  them apart, always. Adding them would credit a desk with performance it never traded, and the
  bridge is over 900 days of it sitting right there in a column that is easy to ignore.

A useful sanity check: the bridge Sharpes should reproduce the historical release exactly —
team-14 +1.357, team-08 +0.901, team-09 +0.809. If they drift, that is a finding, not a rounding.

**This is reporting, not ranking, and the distinction is load-bearing.** Print the numbers for all
four every time and let them be compared by the person reading. Do not sort the desks by
performance, do not name a leader, do not describe one desk as ahead of another, and do not compute
a provisional capital winner. Losses are reported the same way as gains: as data, in the same
format, with no commentary about what should be done.

## The named failure classes

Alert on these and nothing else:

1. **PARITY-BROKEN** — `desk_parity()` reports `BROKEN`. Listed first because it outranks everything
   below it, and the healthcheck's `STATUS` line escalates to `PARITY-BROKEN` ahead of ordinary
   `ATTENTION`. So should you.
2. **DATA-STALE** — the snapshot's last bar is more than 8h behind the boundary. Reported once for
   the field, not per desk. The engine clamps to the last available bar and publishes nothing past
   it rather than raising, so a stale desk is *waiting*, not broken. The watchdog appends from live
   REST before every tick (`top40v5_live_append.py`: klines from the local proxy, funding and
   exchangeInfo direct from Binance, marks derived from the funding response), so persistent
   staleness means that append is failing — read `logs/v5_live_append.log` rather than the desks.

   A clamped tick is retried, not abandoned. Each desk's `boundary.json` records both the nominal
   `boundary` and the `replayed_through` it actually reached, and the early-exit guard compares the
   latter — so when the bar lands, the retry cron entry re-ticks and fills the row.

13. **UNIVERSE-DIVERGENCE** — the desks trading a universe that is not the one they were selected
    on. It has no automatic check and it does not announce itself: nothing raises, the membership
    frame simply contains different symbols and every downstream number is quietly built on them.

    It has happened twice, both times in `top40v5_live_append.py`, both times because an
    incremental path applied a *laxer* rule than the canonical builder:

    - **Persistence not armed.** `seasoned_membership()` applies persistence only once a week has
      ten prior reconstitutions *inside the grid it is handed*, and exempts the first ten. Passing
      only the new weeks means none of them ever has ten priors, so the rule silently does not
      apply. The four weeks from 2026-08-03 came out with three to five wrong symbols each —
      admitting newly liquid ALLOUSDT and ESPORTSUSDT while dropping 1000SHIBUSDT and XMRUSDT,
      which is the RIVER failure the seasoned rule exists to prevent. Fixed by arming the grid
      backwards and discarding the extension; the 320 affected bridge rows were withdrawn and
      republished (`paper-top40v5/corrections.jsonl`).
    - **Eligibility not applied.** Binance reports `underlyingType == "COIN"` for USDCUSDT,
      USTCUSDT, PAXGUSDT and XAUTUSDT alike, so a filter built from exchangeInfo's own fields
      admits stablecoin pegs and gold-backed tokens. Of nine listings absent from the snapshot,
      `is_eligible_usdt_perpetual()` rejects seven. Caught before it shipped.

    The lesson generalizes past these two: **when a rule is applied incrementally, check it against
    a from-scratch rebuild rather than against the previous incremental output.** That comparison
    is what found the first one, and it is cheap — `seasoned_membership` over the whole grid takes
    seconds.
3. **NO-TICK** — launched but never published a boundary.
4. **LATE** — more than 8h45m past the boundary it owes.
5. **FAIL** — last attempt recorded an exception that is not a parity break. Read `attempt.json`.
6. **DEPLOYMENT-DRIFT** — a frozen bundle's sha256 no longer matches `deployment-manifest.json`. The
   desk is no longer replaying what was frozen.
7. **Lineage drift** — the historical release no longer ranks a desk's lane in the top three, or a
   desk's frozen bundle differs from the nomination's. `top40v5_paper_deploy.py --check` re-verifies
   this against `reports-top40-v5/historical/release.json`.
8. **Append-invariance abort** — a row already on disk came back different. Nothing was written. The
   exception names the key, the column and both values. **This is evidence; preserve it.**
9. **Ensemble member drift** — `ensemble-eq3` is defined over exactly the three ranked finalists at
   their frozen bytes. Anything else is a new lineage.
10. **Engine lock contention** — two engines. This happened once during build: the second truncated
    the shared log while the first still held it open at its old offset, so the log showed one run's
    desks and the other run's summary and read as a failure that had not occurred. The lock now
    makes it impossible; if it happens anyway, find the second process before restarting anything.
11. **BOUNDARY-SKEW** — a published boundary off the 8h grid, or ahead of now.
12. **Runaway CPU** — the engine at 100% of a core for long stretches. A tick replays 2.5 years
    across four desks and legitimately costs ~25 minutes, so one busy tick is normal; *continuous*
    busy is not. It happened once: the watchdog was scheduled every 20 minutes against a 25-minute
    tick, so a finished replay was immediately followed by another, roughly seventy a day to
    publish three rows. The engine lock stopped them corrupting each other and did nothing about
    the waste, because a lock is the wrong tool for it.

    Two things hold it fixed. The cron cadence is boundary-aligned — `13 2,3,10,11,18,19` local,
    shortly after each 8h boundary plus one retry — and the engine exits in about a second when
    every desk has already replayed as far as the data reaches. If you see sustained full CPU,
    check the cadence first (`crontab -l | grep top40v5`) and then that the early-exit guard still
    fires: running the engine by hand should print "already replayed through …".

    The guard reads one column of one parquet before deciding, and keys on `replayed_through`
    rather than on the nominal boundary. That is deliberate: keying on the boundary would mark a
    clamped tick finished at the first attempt and make the retry entry — which exists for exactly
    the too-early case — exit without looking, stranding a row for a full 8h. Skipping owed work is
    the worse failure of the two, so it carries more tests than the waste does
    (`tests/tournament/test_v5_paper_engine_guard.py`, both directions mutation-checked).

## Diagnose in order

1. `scripts/top40v5_paper_healthcheck.py` — which desks, which class.
2. If all four failed at the same boundary → the shared generation. Read `paper-top40v5/boundary.json`.
3. `paper-top40v5/<desk>/attempt.json` — the traceback for a single-desk failure.
4. `logs/v5_paper_tick.log` — what the engine did.
5. Only then consider recovery.

## Recovery

Every tick is idempotent per boundary: a desk that already published reports no new rows and is
skipped, and the append-invariant ledger refuses a rewrite rather than accepting one. Restart with:

```
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v4-r1-v3
uv run python scripts/top40v5_paper_engine.py --once
```

It declines to start when another engine holds `paper-top40v5/engine.lock`, and does nothing at all
before `launch.json`.

**A killed tick is safe.** Nothing is published until the tick completes; a partial tick leaves an
`attempt.json` in `RUNNING` and no boundary record, and the next run redoes that boundary. There is
no half-published state to repair.

## The capital rule is pre-registered — read it, do not re-derive it

After **≥ 365 official days**, the capital decision reads the forward record. Before that the rule is
not readable and the healthcheck says `ACCRUING`. Do not compute a provisional winner, do not rank
the desks in a report, and do not let a strong early desk become the assumed answer.

**The historical window authorizes nothing.** It ranked the desks and staffed them; it is
byte-identical to a prior edition's published window and was known to the organizer while this
edition was designed. Capital gates solely on the forward record.

If no desk qualifies, no capital is deployed and the edition closes without deployment — a legal,
pre-registered outcome and not a failure to be worked around.

## Reporting: in-session when there is a session, pushed when there is not

If a user is actively asking for status, answer in the session — a push on top of a visible answer
is redundant noise.

But this desk is meant to report **every tick, unprompted**, and most ticks happen with no session
open. For those the only way a report reaches the user is `PushNotification`; an in-session answer to
nobody is a log entry, not a report. `scripts/top40v5_run_monitor_skill.sh` exists for this: it runs
this skill headlessly and pushes the four-desk healthcheck + performance + parity report every time,
whether or not anything is wrong.

## Report concisely

Every tick: the integrity line and the performance line for **all four desks**, plus the capital
standing. That is the whole report when nothing is wrong — brief, complete, and the same shape every
time so a change is visible at a glance. When something is wrong, add the class, the desk, the
boundary, and what you did or did not do.

## Provenance

The tournament's record lives in `tournament/top40-v5/`: `research-journal.jsonl` (hash-chained,
247 records at release — every trial, nomination, retirement, amendment and the one refunded
evaluator fault), `activation-freeze.json`, `selection-freeze.json`, `calibration-report.json`,
`adversarial-review.json`, `mutation-ledger.json` and the charter at
`TOURNAMENT-CHARTER-TOP40-V5.md`.

Read the amendments in the journal before concluding that something here is surprising. Several
surprising things are already written down, including the cap-raise defect that destroyed the
eventual top desk's first evaluation over a 7.6e-5 rounding artifact, and the under-documented
decision-context interface that cost two lanes a discovery phase.
