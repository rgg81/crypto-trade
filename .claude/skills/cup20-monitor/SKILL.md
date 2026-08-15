---
name: cup20-monitor
description: Monitor the CUP-20 holdout winner's frozen exact-replay paper desk, diagnose integrity failures, and report forward observation without intervening in the strategy. Use when asked to check the CUP-20 desk, cup20 paper PnL, team-02 channel-position-ls forward performance, live/backtest parity, deployment-authority or pin drift, stale boundaries, append-invariance aborts, cache or artifact drift, or safe engine recovery.
---

# CUP-20 Monitor

Monitor the six-month forward paper desk in
`/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top20-low-dd`.

The desk is `paper-cup20/`. It runs **team-02 `channel-position-ls`**, CUP-20's holdout winner,
through the tournament's own frozen evaluator. Treat the frozen strategy, the frozen risk policy
and the tournament evaluator as one indivisible model. The desk exists to find out how that model
behaves on data nobody has seen. Nothing else.

## Preserve the experiment

- Observe and report. Never flatten, hedge, resize, re-weight, or edit a signal because of
  performance. There is no intervention that improves this test; every one of them ends it.
- **PnL, drawdown, Sharpe, turnover and exposure are test results, not operational alerts.** A
  losing month is data. A drawdown is data. Neither is a reason to touch anything, and neither is
  ever reported as a problem.
- Alert only on **test-integrity** failures — the named classes below. The question a healthcheck
  answers is "can the record still be trusted", never "is the book doing well".
- Never recommend a strategy intervention on the basis of losses. If asked to, say why not.

## Never edit desk artifacts to make a check pass

`paper-cup20/ledger/forward_returns.parquet` and `paper-cup20/ledger/paper_fills.parquet` are the
record: append-invariant evidence, written once per row and never revised. The three CSVs
(`forward_returns.csv`, `paper_fills.csv`, `current_positions.csv`) are **renderings** re-written
from the ledgers on every tick, and the healthcheck re-renders them and compares byte for byte.

So: do not delete a ledger row, do not rewrite a CSV, do not hand-edit `integrity.json` or a
`boundaries/*.json` record, and do not re-bind a hash to whatever is currently on disk. Six months
of running produces exactly one thing — an unedited record — and making a check pass by editing
the evidence destroys it. A red check with intact evidence is worth incomparably more than a green
one without.

`paper-cup20/desk/snapshot/` is the exception in the other direction: it is a work product,
reassembled every tick, deliberately unbound and not evidence.

## The desk is paper-only, by construction

`run_cup20_paper.py` has no signed Binance client and no order path. The only network client in its
import graph is `PublicMarketDataClient`, which refuses any endpoint outside four public
market-data paths, and `tests/cup20_desk/test_healthcheck.py::test_the_runner_cannot_sign_or_place_an_order`
asserts that by inspection. There is nothing to disable and no key in use.

If anyone proposes adding an order path, a signed client, or "just a small live allocation": that
is a different system and a different conversation. Do not add it here, and do not treat it as a
change to this desk.

## Parity, stated precisely

The desk does not reimplement execution. At each boundary it rebuilds the snapshot and re-runs the
tournament's own `run_candidate` over the whole window, then reads the forward tail off the result.
Next-bar-open fills, the **5 bps taker fee**, the **2.5 bps slippage per side**, native per-event
funding, the common risk unit and both cap applications are therefore not *matched to* the
backtest — they **are** the backtest, executing the same lines of the same module. There is no code
path in the desk that computes a fill, a fee or a slippage figure; if one appears, it is a defect.

**And yet the desk's numbers are not expected to equal the holdout result.** The replay runs from
`IS_START` (2020-08-17, resolved by the tournament's own `resolve_is_start` and pinned in
`integrity.json`), while the holdout observation ran only over the sealed window
`SEALED_START` 2024-08-01 → `SEALED_END` 2026-08-01. Different window, different starting book,
different path. Anyone who lines up the desk's forward Sharpe against holdout G 65.979 and reads a
discrepancy as a parity failure is making a mistake — say so plainly. What parity guarantees is
that the *execution* is the tournament's, not that the *window* is.

Two further things worth stating whenever the winner comes up:

- **"Winner" means the holdout winner.** team-02 ranked **3rd in sample** (G 70.58) behind team-09
  (91.25) and team-12 (84.27); it won on the sealed window (holdout G 65.979, rank 1) while the
  in-sample leader lost money out of sample. `selection-freeze.json` is ordered by IN-SAMPLE rank,
  so team-02 appears third in it; `holdout-observations.json` carries the result. Never describe
  team-02 as the in-sample leader and never rank finalists off the selection freeze.
- The publication lag is deliberate. A boundary is ready only once its own 8h bar has closed and
  then stood unrevised for 25 minutes, so the desk publishes roughly 8h25m after the instant a
  decision is stamped with. That is not lateness; a forming bar's volume and close would make the
  recorded fills change underneath the record.

## Phases

Every persisted row carries `phase`:

- **`bridge`** — unscored continuity, from the seam `2026-08-01T00:00:00Z` until official
  observation opens. These rows exist so the book is already formed when observation starts. They
  are excluded from every digest statistic and reported only as a count.
- **`official`** — the scored six-month forward window. It opens at the first Monday `00:00` UTC
  **strictly after the desk's first successful tick**, and that instant is pinned once in
  `integrity.json` and read back forever after.

The digest reports the **official phase only** and labels the whole result `INSUFFICIENT` below
**90 official 8h bars** (30 days). Below that line, do not infer success or failure — and when
reporting, say what it is insufficient *for*: 90 bars is roughly where a Sharpe estimate stops
being dominated by its own standard error, so a shorter window supports no inference about forward
Sharpe, drawdown or turnover. Print the numbers; they are there to be watched, not read as a
result.

## Run the standard check

Serially, in this order:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top20-low-dd
uv run python scripts/cup20_paper_healthcheck.py
uv run python scripts/cup20_paper_digest.py
```

The healthcheck prints `STATUS OK` or `STATUS ALERT` followed by one line per finding, each opening
with a named failure class, and exits non-zero on any alert. It binds every published artifact and
every cache file by path, size, row count and SHA-256 against the tick's own `integrity.json`,
re-renders the CSVs from the ledgers, re-verifies the six deployment-authority digests, checks the
three pins from three independent directions, and checks liveness through the engine's `flock`.
It is read-only and never writes to the desk.

Useful flags (both verified):

- `scripts/cup20_paper_healthcheck.py --skip-process` — artifact-only validation, for when the
  engine is intentionally not running.
- `scripts/cup20_paper_healthcheck.py --now <UTC instant>` — evaluate freshness against a stated
  instant instead of now.
- `--desk-dir <path>` on both scripts — defaults to `paper-cup20/`.

Report the digest as observational information only. It states no verdict, applies no threshold and
compares nothing to a floor.

### Before the desk has ever ticked

This is the expected pre-launch state and it is not a fault:

```
STATUS ALERT - CUP-20 winner exact-replay paper desk (.../paper-cup20)
  ALERT: ENGINE DOWN: .../paper-cup20/engine.lock is missing; no engine has ever held this desk
  ALERT: ARTIFACTS MISSING: .../paper-cup20/integrity.json does not exist; the desk has never ticked
```

and the digest renders `INSUFFICIENT` with `0 official 8h bars`. Report it as "not launched", not
as an integrity failure.

**Do not start the desk on your own initiative — not even `--once`.** The first successful tick
permanently pins `official_start`, `seam` and `is_start`, and choosing the moment the scored six
months begin is the user's call. Launch only when the user asks for it.

## The named failure classes

The healthcheck emits exactly these. **Stop and report** means: change nothing, restart nothing,
regenerate nothing, and hand the user the specific mismatch.

| Class | What it means | What to do |
|---|---|---|
| `ENGINE DOWN` | `engine.lock` is missing, or exists and nobody holds the `flock`. The kernel drops the lock when the holder dies, so an unheld lock file means the engine is gone. | **Recover**, if authority/pins/ledgers are otherwise clean and the user has asked for recovery or an active mandate authorises it. |
| `ENGINE IDENTITY BAD` | The lock IS held, but by a process that is not `run_cup20_paper.py` in this worktree. | **Stop and report.** Never kill an unidentified process. Report pid, cwd and cmdline; a second desk or a foreign holder is the user's decision. |
| `AUTHORITY DRIFT` | One of the six pinned digests (`strategy`, `risk_policy`, `neighbourhood`, `config`, `selection_freeze`, `evaluator`) differs from what the desk published. The scored model changed on disk. | **Stop and report.** Do not restart — a desk running a changed model produces a record that is not comparable to the holdout result. Name which field moved and both values. |
| `PIN DRIFT` | `official_start`, `seam` or `is_start` no longer agrees with `integrity.json`, a `boundaries/*.json` record, or the phase labels on the forward ledger. | **Stop and report.** The pins decide which rows exist and what phase they carry. A moved pin retroactively relabels published rows. |
| `APPEND-INVARIANCE ABORT` | A row already recorded came back with different values — the market data was revised underneath the desk — or a ledger is missing, holds duplicate keys, is out of order, or disagrees with the row counts in `integrity.json`. | **Stop and report.** Preserve both the recorded value and the refetched one; the exception names key, column and both values. **Never "fix" this by deleting rows.** |
| `CACHE DRIFT` | A market-cache file is not the one the last successful tick's manifest bound, and the cache did not merely grow ahead of it. Shrinkage is called out explicitly. | **Stop and report.** Keep the last sealed state and name the affected file. A cache legitimately *ahead* of the binding while a tick is in flight is reported as a note, not an alert. |
| `STALE BOUNDARY` | The newest published boundary is older than one that has been ready for longer than the 75-minute grace on top of the publication lag. | **Diagnose first.** With clean authority/pins/ledgers this usually accompanies `ENGINE DOWN` and recovery is the answer. With a failing or hung tick, fix the cause, not the symptom. |
| `LEDGER/CSV MISMATCH` | A published CSV is not a faithful rendering of its ledger, or `current_positions.csv` disagrees with `latest-boundary.json`. The ledger is the record and the CSV disagrees with it. | **Stop and report.** Do not regenerate the CSV to make it agree — that erases the evidence of how they diverged. |
| `ARTIFACT DRIFT` | A bound non-ledger artifact changed size, row count or SHA-256; the bound artifact set is wrong; or `integrity.json` no longer says `status: PASS` / `paper_only: true`. | **Stop and report.** Name the file and the mismatch. |
| `ARTIFACTS MISSING` | A bound artifact is gone, or `integrity.json` does not exist. | Before the first tick this is the **pre-launch state** — report "not launched". After the desk has published, it is **stop and report**. |
| `LATEST TICK FAILED` | `attempt.json` records `status: FAIL`. The boundary and error are in the alert; the full traceback is in `attempt.json` and the log. | **Diagnose from the log.** Recovery is appropriate only for a transient cause (a public endpoint refusing, a network blip). Never bypass a fail-closed check to advance the desk. |
| `TICK HUNG` | An attempt has been `RUNNING` for more than 90 minutes. One tick is a full-window replay measured at ~410 s plus a wide cross-section fetch, so this is well past normal. | **Diagnose.** Check the log's mtime for real progress before concluding anything. Killing a hung tick is safe (see recovery) but is a user decision unless a mandate covers it. |
| `HEALTHCHECK ERROR` | A check itself raised. The remaining checks still ran. | **Report it as a finding**, not as a clean bill of health. A healthcheck that cannot answer a question has not answered it. |

## Diagnose in order

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top20-low-dd
tail -60 logs/cup20_paper.log
cat paper-cup20/attempt.json
cat paper-cup20/integrity.json
ls -t paper-cup20/boundaries | head -5
cat paper-cup20/latest-boundary.json
tail -20 logs/cup20_paper_watchdog.log
```

Then, when authority is implicated:

```bash
uv run python -c "
from crypto_trade.cup20_desk.authority import current_desk_authority
import json; print(json.dumps(current_desk_authority().to_dict(), indent=1, sort_keys=True))"
```

and compare field by field against the same keys inside `paper-cup20/integrity.json`.

The tournament stack under `src/crypto_trade/cup20/` is hash-bound. Confirm it is intact — this must
pass, and never edit a byte under that tree to make anything else pass:

```bash
uv run python -c "
from crypto_trade.cup20.activation import verify_activation
verify_activation('tournament/cup20/activation-freeze.json'); print('activation freeze OK')"
```

Order of suspicion, because the answers are nested: **authority → pins → ledgers → renderings →
cache → freshness → liveness.** A drifted deployment explains everything downstream of it, so
resolve it first and do not chase a stale boundary that is really an authority problem.

## Recovery

Recovery is legitimate for `ENGINE DOWN`, and for a stale boundary or failed tick whose cause is
transient, **when authority, pins and ledgers are clean**. It is never the answer to authority
drift, pin drift, an append-invariance abort or a ledger/CSV mismatch.

Restart only when the user asks for recovery or an active monitoring mandate authorises it, and
confirm no other desk process is running first with `pgrep -af "[r]un_cup20_paper\.py"` — the
bracket keeps the pattern from matching the shell line that carries it, which a plain
`pgrep -af run_cup20_paper.py` does, reporting a desk that is not there. Prefer the
watchdog, which holds its own lock, checks the engine lock, and starts nothing if an engine is
alive:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top20-low-dd
bash scripts/cup20_paper_watchdog.sh
tail -20 logs/cup20_paper_watchdog.log
```

Direct launch, equivalent to what the watchdog runs:

```bash
cd /home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top20-low-dd
mkdir -p logs
PYTHONUNBUFFERED=1 nohup uv run python run_cup20_paper.py \
  >> logs/cup20_paper.log 2>&1 &
```

Single-boundary and offline diagnostic modes (all flags verified): `--once` runs one boundary and
exits; `--boundary <exact 8h UTC instant>` replays a specific one; `--no-refresh` replays from the
recorded cache without touching the network. `--once` and `--boundary` still pin the windows on a
desk that has never ticked, so they are not safe as a casual probe.

### Why a killed tick is safe

Every ledger and JSON write goes to a temporary file and lands with `os.replace`, so a killed
process leaves either the complete old file or the complete new one, never a torn one. And every
tick re-presents the *whole* seam-to-boundary tail, not just the newest rows: the identical rows
append as no-ops, the CSVs are re-rendered from the ledgers, and `integrity.json` is re-bound. A
tick killed halfway therefore self-heals on the next successful one, including the case where the
forward ledger advanced and the fills ledger did not. **Killing a tick is safe; deleting a row is
not.**

An append-invariance abort must never be resolved by deleting the offending rows, truncating a
ledger, or moving a ledger aside and letting the desk rebuild. That is the one failure the entire
desk exists to make loud, and the recorded value is the finding. Preserve it, report it, and let
the user adjudicate.

A running engine that detects the deployment changing underneath it exits by design rather than
keep publishing; the watchdog then restarts it onto one internally consistent release. If that
happens, expect an authority discussion, not just a restart.

## Alerts are written in-session

Standing user preference: **report everything in the session. No push notifications**, no
`notify-send`, no mail, no webhook, no external alerting of any kind. If an integrity failure is
urgent, say so loudly in the reply.

## Report concisely

Lead with one verdict:

- `OK` — boundary current, authority/pins/ledgers/renderings/cache all verified.
- `INSUFFICIENT` — integrity passes but fewer than 90 official forward bars exist.
- `NOT LAUNCHED` — the desk has never ticked (pre-launch `ENGINE DOWN` + `ARTIFACTS MISSING`).
- `INTEGRITY ALERT` — name the exact failure class and the affected file, symbol or boundary.

Then, briefly: latest published boundary and its phase; official bar and day counts; bridge bar
count; cumulative return, daily-annualized Sharpe and max drawdown **when they are meaningful**;
turnover and mean gross/net exposure; recorded fees and slippage as the evaluator wrote them; and
any integrity action taken. Mark every performance figure as observation. Below 90 official bars,
carry the `INSUFFICIENT` label into the summary rather than dropping it because the numbers look
fine.
