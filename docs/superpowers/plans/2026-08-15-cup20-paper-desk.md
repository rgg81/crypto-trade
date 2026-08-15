# CUP-20 Winner Paper Desk — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to
> implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run CUP-20's winner — team-02 `channel-position-ls` — as a hash-bound, append-invariant
paper desk for six months of forward observation, with a healthcheck, a digest and a monitor skill.

**"Winner" means the HOLDOUT winner, and the distinction matters when reading the artifacts.**
team-02 ranked **3rd in-sample** (G 70.58), behind team-09 (91.25) and team-12 (84.27). It won on
the sealed window: holdout G 65.979 against 54.54 and 0.00, all six section 8 conditions passing,
while the in-sample leader lost money out of sample. `selection-freeze.json` is ordered by
IN-SAMPLE rank, so team-02 appears third in it; `holdout-observations.json` carries the result.
Never describe team-02 as the in-sample leader, and never rank finalists off the selection freeze.

**Architecture:** A new package `crypto_trade.cup20_desk` that *consumes* the frozen tournament
stack without touching it. Forward market data is fetched from Binance public endpoints into a
rolling snapshot with the same schema as `data/cup20/is`; the point-in-time universe is
reconstituted weekly by the tournament's own `build_membership`; each 8h boundary is evaluated
through the tournament's own evaluator. Nothing about the strategy or the scoring is reimplemented.

**Tech Stack:** Python 3.13, uv, pandas, httpx, pyarrow. Reference implementation to mirror:
`/home/roberto/crypto-trade/.worktrees/quant-portfolio-blind-top40-v4-r1` (`run_team09_paper.py`,
`src/crypto_trade/team09/`, `scripts/team09_paper_*`), which is a working desk of this exact shape.

## Global Constraints

- **`src/crypto_trade/cup20/` is HASH-BOUND by `tournament/cup20/activation-freeze.json`
  (`implementation_root`). Do not add, edit or delete a single byte under it.** The desk lives in
  `src/crypto_trade/cup20_desk/`. Any task that needs behaviour from the tournament stack imports
  it; it never modifies it. After every task, `verify_activation` must still pass.
- **The desk is paper-only.** No signed Binance client, no order path, no API key use. Public
  market endpoints only. A code path that could place an order is a defect.
- **Append-invariance is a hard abort, not a warning.** If a source row that was already recorded
  comes back with different values, stop and preserve both. Never overwrite.
- **The frozen strategy is `tournament/cup20/teams/team-02/candidates/channel-position-ls/`** and
  its bytes must match `source_sha256` in `tournament/cup20/selection-freeze.json`
  (use `crypto_trade.cup20.trials.candidate_source_digest` — the bundle digest, NOT a hash of
  `strategy.py` alone; mixing those two definitions already produced one false tampering alarm).
- **Windows.** Sealed holdout ended `2026-08-01T00:00:00Z`. Bars from then until the first official
  boundary are an **UNSCORED BRIDGE** and must be labelled as such in every artifact. Official
  forward observation begins at the first Monday `00:00 UTC` strictly after the desk's first
  successful tick, and runs six months.
- **Decision grid is 8h (00:00/08:00/16:00 UTC).** The strategy rebalances weekly and returns
  `None` (hold) at every other boundary. Do not special-case Mondays anywhere.
- Ruff, line-length 100. `uv run pytest` green before each commit.

---

### Task 1: Package skeleton and deployment authority

**Files:**
- Create: `src/crypto_trade/cup20_desk/__init__.py`
- Create: `src/crypto_trade/cup20_desk/authority.py`
- Test: `tests/cup20_desk/test_authority.py`

**Interfaces:**
- Produces: `DeskAuthority` (frozen dataclass) with fields `strategy_sha256`, `risk_policy_sha256`,
  `neighbourhood_sha256`, `config_sha256`, `selection_freeze_sha256`, `evaluator_sha256`;
  `verify_desk_authority(...) -> DeskAuthority` which recomputes and raises on any mismatch;
  `DeploymentChangedError`.

Mirror `team09/authority.py`. `evaluator_sha256` is the bundle digest of
`src/crypto_trade/cup20` — the desk must refuse to run if the tournament evaluator it is replaying
through has changed since the winner was scored.

- [ ] **Step 1: failing test** — authority verifies against the real repo, and each of the six
      digests independently detects a mutation (parametrize over the six).
- [ ] **Step 2: run it, confirm failure**
- [ ] **Step 3: implement**
- [ ] **Step 4: tests pass; `verify_activation` still passes**
- [ ] **Step 5: commit**

---

### Task 2: Forward market data, append-invariant

**Files:**
- Create: `src/crypto_trade/cup20_desk/live_data.py`
- Test: `tests/cup20_desk/test_live_data.py`

**Interfaces:**
- Consumes: nothing from task 1.
- Produces: `fetch_forward(symbols, start, end) -> dict[str, DataFrame]` returning frames in the
  **exact schema of `data/cup20/is`** (bars, funding, mark_prices, contract_metadata);
  `append_frame(path, frame) -> AppendResult` which appends only genuinely new rows and raises
  `AppendInvarianceError` naming the key and column if an existing row's values changed;
  `cache_manifest(root) -> dict` and `verify_cache_manifest(root)`.

Read `data/cup20/is/*.parquet` first and match dtypes and column order exactly — a schema drift
here silently produces a snapshot the tournament loader accepts and the evaluator mis-reads.
Binance public endpoints only (klines, fundingRate, premiumIndex). Rate-limit politely.

- [ ] **Step 1: failing tests** — schema matches the sealed snapshot column-for-column; a changed
      value on an existing key raises `AppendInvarianceError`; a genuinely new row appends; the
      manifest detects a mutated file.
- [ ] **Step 2: run, confirm failure**
- [ ] **Step 3: implement**
- [ ] **Step 4: tests pass**
- [ ] **Step 5: commit**

---

### Task 2a (prerequisite for Task 3): delisting is a transition, not a revision

**Decided, after Task 2 raised it.** `contract_metadata` keyed on `(symbol,)` under strict
append-invariance aborts when a symbol is delisted mid-window, because its provenance flips
`current_exchangeInfo` -> `archive_inference`. Over six months on a twenty-name crypto universe
this WILL fire, and a desk that halts on a routine delisting is not operational.

The rule is wrong, not the event. Append-invariance exists to catch a **revised fact** — a bar whose
OHLCV changed underneath us. A contract ceasing to exist is not a revision of an old fact; it is a
new fact about a later time, and the tournament's own execution contract already treats delisting as
normal ("force exit at the last executable open, no survivorship rescue").

`append_frame` must therefore permit a **declared one-way transition** on `contract_metadata`:
`current_exchangeInfo` -> `archive_inference`, and a live contract becoming delisted. Any other
change to an existing metadata row — a changed tick size, a changed quote asset, a delisted contract
returning to live — remains a hard abort. The permitted transitions are a frozen allowlist in the
module, not a general "metadata may change" escape hatch.

- [ ] **Step 1: failing test** — a delisting appends/transitions cleanly; a tick-size change on an
      existing row still aborts; a delisted->live reversal aborts.
- [ ] **Step 2: run, confirm failure**
- [ ] **Step 3: implement**
- [ ] **Step 4: tests pass; mutation-prove the allowlist is not a blanket bypass**
- [ ] **Step 5: commit**

---

### Task 3: Rolling universe and snapshot assembly

**Files:**
- Create: `src/crypto_trade/cup20_desk/snapshot_forward.py`
- Test: `tests/cup20_desk/test_snapshot_forward.py`

**Interfaces:**
- Consumes: `live_data.append_frame`.
- Produces: `extend_membership(sealed_membership, bars, through) -> DataFrame` which continues the
  weekly reconstitution **carrying the sealed window's final incumbency forward**, so hysteresis
  (enter ≤20, exit >25) is continuous across the seam rather than restarting;
  `build_forward_snapshot(root, through) -> Snapshot`.

Reuse `crypto_trade.cup20.universe.build_membership` and `unmarkable_member_boundaries`. Do not
reimplement the ranking, the median-volume statistic, or the mark-coverage rule.

- [ ] **Step 1: failing tests** — membership continues without a discontinuity at the seam; an
      incumbent at rank 23 across the seam is retained, not dropped; a symbol lacking mark coverage
      over its membership period is refused.
- [ ] **Step 2: run, confirm failure**
- [ ] **Step 3: implement**
- [ ] **Step 4: tests pass**
- [ ] **Step 5: commit**

---

### Operational facts established by Tasks 2a/3 — Tasks 4-6 depend on these

1. **The cache must hold the WIDE cross-section, not just members.** The trailing-180-day median
   volume ranking needs every eligible symbol, not the twenty currently in. The desk must fetch the
   full cross-section back at least 180 days before its first forward boundary or that boundary
   cannot be scored at all. `data/cup20/acquisition` (670 symbols) is the shape; the split
   member-only snapshots cannot reproduce a reconstitution and never could.
2. **The desk must fetch its own `contract_metadata`.** The split snapshots scope metadata to the
   62 symbols visible in-sample, and **four of today's twenty members are absent from both**:
   `ENAUSDT`, `HYPEUSDT`, `RIVERUSDT`, `TAOUSDT`. The universe has already turned over since the
   tournament window; treating the sealed metadata as sufficient would fail on day one.
3. **The sealed mark panel is NOT narrowed to membership periods** — 77 symbols carry marks against
   41 that were ever members. The earlier plan text asserting otherwise was wrong. **Superseded by
   Task 4, see fact 5: the narrowing keeps everything from a symbol's first admission ONWARD.**
4. **Warm-up bars below `IS_START` are retained.** Truncating them silently shortens every
   formation window. The decision grid still begins at `IS_START`.

---

### Operational facts established by Task 4 — Tasks 5-6 depend on these

5. **The mark panel may only be narrowed at the FRONT.** Task 3's rule — the membership period plus
   its exit boundary — is what the position record shows *after* execution, and it is wrong: a
   departing member's mandatory exit is filled against `max_bar_participation` = 0.001 of a bar's
   volume, so a large position in a thin name is still on the book several boundaries later, at
   instants inside nobody's membership period. The first real full-window replay raised `missing
   current mark for held symbols: ['TRBUSDT']` out of the evaluator; `1000BONKUSDT`, `PNUTUSDT` and
   a five-day `FTMUSDT`/`SOLUSDT`/`XRPUSDT` unwind in Feb 2022 do the same. `narrow_mark_panel` now
   keeps every mark at or after a symbol's first admission and nothing before it, which is the only
   statically safe rule. Verified: the narrowed panel reproduces the un-narrowed one's evaluation
   bit for bit over the whole six-year window.
6. **The record is `desk/ledger/{forward_returns,paper_fills}.parquet`; the CSVs are renderings.**
   The ledgers are appended through `live_data.append_frame` under a caller-declared `FrameSchema`
   (which `frame_schema` now accepts, so there is exactly one implementation of "has a recorded row
   changed"), and the CSVs are rewritten from the ledgers on every tick. **The healthcheck must
   bind both**, and must treat a CSV that disagrees with its ledger as drift.
7. **`desk/snapshot/` is a work product, not an artifact.** It is reassembled on every tick and
   legitimately grows with the window; only the ledgers, the CSVs, `boundaries/`,
   `latest-boundary.json` and `integrity.json` are the record. Boundary records are named
   `boundaries/YYYYMMDDTHHMMSSZ.json`.
8. **`integrity.json` pins `official_start`, `seam` and `is_start`,** and `run_tick` reads them back
   rather than recomputing. A tick that would use a different `seam` or `is_start` raises
   `DeskPinDriftError` before writing an artifact. The runner must not pass window overrides.
9. **One tick costs ~410 s** against the real 6525-boundary window (assembly is 1.3 s of it), so a
   25-minute publication lag and an 8-hourly grid leave ample headroom, but two ticks must never
   overlap — the `fcntl` engine lock in Task 5 is load-bearing.

---

### Task 4: Exact-replay tick (PARITY BY CONSTRUCTION)

**The design decision that makes parity provable rather than tested.** The desk does NOT
reimplement execution. At each boundary it rebuilds the snapshot through that boundary and re-runs
the tournament's own `run_candidate` over the WHOLE window from `IS_START` to now, then reads the
forward tail off the result. Fills at next-bar-open, the 5 bps taker fee, the 2.5 bps slippage per
side, native per-event funding, the common risk unit and both cap applications are therefore not
"matched" to the backtest -- they ARE the backtest, executing the same lines of the same module.

There is no code path in the desk that computes a fill, a fee or a slippage figure. If one appears,
it is a defect: it means execution has been duplicated and the two copies can now disagree.

Cost: one full-window evaluation per tick, measured at roughly 8 minutes against 8-hourly
boundaries. That is the price of exact replay and it is worth paying.

Determinism check, run every tick: the replay must reproduce the previous tick's forward rows
bit-identically. A change in an already-recorded forward row means the input data was revised
underneath the desk, which is an append-invariance abort, not a rounding difference.

### Task 4 (original framing): The paper tick

**Files:**
- Create: `src/crypto_trade/cup20_desk/tick.py`
- Test: `tests/cup20_desk/test_tick.py`

**Interfaces:**
- Consumes: tasks 1–3.
- Produces: `run_tick(boundary, *, desk_root, authority) -> TickResult` and
  `persist_tick(result, desk_root)`.

At a boundary: verify authority, assemble the snapshot through that boundary, build the decision
context, call the frozen strategy, and evaluate through the tournament's own execution contract
(next-bar-open fills, 5bps fee + 2.5bps slippage, native funding, the common risk unit). Persist
`paper_fills.csv`, `current_positions.csv`, `forward_returns.csv`, `boundaries/`,
`latest-boundary.json` and `integrity.json`. Every row carries `phase` ∈ {`bridge`, `official`}.

- [ ] **Step 1: failing tests** — a bridge boundary is labelled `bridge`; the first Monday after the
      first tick starts `official`; a non-rebalance boundary produces zero fills but still marks to
      market; an authority mismatch aborts before any artifact is written.
- [ ] **Step 2: run, confirm failure**
- [ ] **Step 3: implement**
- [ ] **Step 4: tests pass**
- [ ] **Step 5: commit**

---

### Task 5: Runner, healthcheck, digest, watchdog

**Files:**
- Create: `run_cup20_paper.py`
- Create: `scripts/cup20_paper_healthcheck.py`
- Create: `scripts/cup20_paper_digest.py`
- Create: `scripts/cup20_paper_watchdog.sh`
- Test: `tests/cup20_desk/test_healthcheck.py`

Mirror the team09 equivalents. Runner: `fcntl` engine lock so two processes cannot tick at once,
a 25-minute publication lag before treating a boundary as final, structured logging to
`logs/cup20_paper.log`, and a clean `--once` mode for cron. Healthcheck: bind every artifact and
cache file by path, size, row count and SHA-256, and print `STATUS OK` or a named failure class.
Digest: observational only — forward PnL, Sharpe, drawdown, turnover, exposure, on the
**official** phase only, labelled `INSUFFICIENT` before 90 official bars.

- [ ] **Step 1: failing test** — healthcheck detects a mutated artifact and a stale boundary
- [ ] **Step 2: run, confirm failure**
- [ ] **Step 3: implement**
- [ ] **Step 4: tests pass; run the runner once against real data and read the output**
- [ ] **Step 5: commit**

---

### Task 6: The monitor skill

**Files:**
- Create: `.claude/skills/cup20-monitor/SKILL.md`

Model on `.claude/skills/team09-monitor/SKILL.md` in this worktree. It must state: preserve the
experiment (observe, never intervene); PnL and drawdown are **results, not alerts**; alert only on
integrity failures (engine down, stale boundary, authority drift, append-invariance abort, cache
drift, missing marks, non-pure-crypto membership, traceback); never edit desk artifacts to make a
check pass; the desk is paper-only. Include the standard check commands, the diagnosis order, and
the recovery procedure. Per the user's standing preference, **all alerts are written in-session —
no push notifications.**

- [ ] **Step 1: write the skill**
- [ ] **Step 2: invoke it once and confirm the commands run**
- [ ] **Step 3: commit**
