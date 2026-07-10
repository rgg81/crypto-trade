# PROTOCOL-L1-FORWARD — Pre-registered forward-validation contract for the frozen L1 (C1+C2)

> **RETIRED 2026-07-10, PRE-T0 — SUPERSEDED by PROTOCOL-ENSEMBLE-L1-FORWARD.md (v2).**
> Zero forward candles ever accrued under this contract (verified in
> REVIEW-PROTOCOL-V2-preflight.md); no in-flight test was abandoned. The user accepted the
> PHASE7-007 §5(c) recommendation to switch the single forward book to ENSEMBLE-L1.
> This document is preserved as the historical v1 contract; nothing below is active.

**Status: FROZEN 2026-07-10, before the first forward candle.** **Pre-T0 amendment (same day,
REVIEW-006 ADDENDUM 2):** rebal-phase anchor re-pinned Mon@00h → **Wed@00h** (the a-priori frozen
construction), new **T0 = 2026-07-15**, revised expectation band **+0.55–0.80**, new **M-phase** gate +
21-phase log — a pre-registration correction, NOT a clock reset (no forward candle observed). This is
the pre-registered forward contract for the EXPLORATION-006 primary candidate **L1 = C1 + C2**
(PHASE7-006 SUCCESS-WITH-CAVEATS).
Paper trading only — **no real orders**. The construction is FROZEN: no threshold changes, C2 stays
exactly as-is (**no post-hoc Q scan**, per REVIEW-006 caveat 5). Any construction/parameter change
resets the clock to a new T0 and a new protocol version (§5).

**Quarantines.** IS artifacts only for design; **`CONFIRMATION-005.md` not read**; the burned OOS
window **2025-03-24 → 2026-07-08 stays quarantined as EVALUATION data** and contributes **no** forward
metric (indicator-history exception in §2). This is a forward test of ONE frozen candidate; **n_eff = 1
forward** (§6).

---

## §1 — Architecture (orchestrator-fixed): recompute, not a live path

Each weekly run **rebuilds the full panel (2020-01-01 → now)** and re-runs the **UNCHANGED**
`blind_engine.run_backtest` with the frozen L1 parameters:

- `lowvol_signal(window=12)`, `pit_topn_universe(top_n=20, lookback=30)`,
  `CostModel(taker_fee_bps=5.0, slippage_bps=2.5, funding_enable=True)`, funding ON, `gross=1.0`,
  `rebal=21`, `weighting="midvol_short"`, `long_frac=0.5`, `short_frac=0.25`;
- **C1** = `short_scalar_series` from the committed `mania_gate` with the **0.5 floor**
  (`short_scalar_series[t] = 0.5 if gate[t] else 1.0`);
- **C2** = `short_exclude` from trailing-21c return `> +0.30`, `short_exclude_mode="shrink"`.
- **C3, C4, C5 are OUT** (correctly dropped by the frozen §5.2 tree).

Only the **post-T0 slice** is the forward evaluation; everything before T0 is context/warmup. The
engine's proven **append-invariance** (leak positive-controls; PHASE7-006 §1) guarantees past decisions
never change as candles append. **Every run ASSERTS bit-identity** of all pre-existing (< current-run)
decisions against the prior run's `decisions.csv` — this both proves no forward leak and **catches
upstream data revisions** (a revised historical kline would flip a past decision and trip the assert).

## §2 — Decision timestamps (orchestrator-fixed) — REBAL-PHASE RE-PIN (pre-T0 correction)

**Pre-T0 correction (REVIEW-006 ADDENDUM 2, ruling 2; NOT a clock reset — no forward candle has been
observed).** The weekly `rebal=21` construction has 21 possible 8h phase offsets. All /005 and /006
evidence was generated at the phase inherited from the panel's **2020-01-01 (Wednesday) start** — the
a-priori frozen-candidate phase, never chosen, never scanned. The forward anchor is therefore pinned to
**Wed@00h UTC** (matching the frozen construction), **superseding the earlier Mon@00h operational pin**
(which the IS sweep showed to be the single worst of 21 phases, near-guaranteed FF-1 breach).

- 8h grid (candles open 00/08/16 UTC). **Weekly rebal anchor (Wed@00h):** decision at the **close of the
  candle ENDING Wednesday 00:00 UTC**; fill at the **open of the Wednesday 00:00→08:00 UTC candle** —
  identical to the engine's `signal[k-1] → open[k]` convention; the QE pins the rebal phase so
  `k % 21 == 0` lands on that candle.
- **T0 = 2026-07-15 00:00 UTC** (Wednesday; first forward decision). The **evaluation window starts at
  the first forward fill** (open of the 2026-07-15 00:00→08:00 UTC candle).
- **INDICATOR-HISTORY EXCEPTION (explicit):** the z365 / universe-lookback / vol warmup necessarily
  consumes pre-T0 history, **including the burned OOS window (2025-03-24 → 2026-07-08)**. That history
  is permitted as **INPUT only**. **No pre-T0 candle contributes to any forward evaluation metric** —
  every gate in §4 is computed strictly on fills at candles with open_time ≥ T0.

### §2.1 — Phase disclosure (FROZEN, mandatory — REVIEW-006 ADDENDUM 2)

The forward test is anchored on ONE phase; full transparency about that choice, from the committed
IS-only 21-phase sweep (`paper-l1/phase_sweep_is.csv`, `blind_phase_sweep_006.py` — selection-free,
IS-clean, fully disclosed):

1. **What is validated:** the test validates **Wed@00h = the frozen-candidate phase** (the a-priori
   panel-start phase, fixed by the 2020-01-01 Wednesday start — NOT selected from the sweep).
2. **Full sweep disclosed:** at the frozen Wed@00h phase, L1 Sharpe ranks **8/21** with the **SMALLEST
   overlay delta of all 21 phases (+0.250)** — the frozen /006 evidence UNDERSTATES the C1+C2 benefit.
   Phase-agnostic L1 mean **+0.947** (min +0.085, **21/21 phases positive**); V0's /005 headline +0.913
   ranks **3/21** of its own phase distribution (V0 phase mean only +0.334, min −0.795).
3. **Favorable LEVEL draw:** Wed@00h is a favorable LEVEL draw for L1 (+1.164 > phase mean +0.947). The
   **forward LEVEL expectation is anchored on the phase-agnostic distribution (≈ +0.55–0.80, §6), NOT on
   +1.164.**
4. **maxDD is phase-fragile:** L1 maxDD at the frozen phase is −28.6% but the **phase mean is −37.3%**
   and **7/21 phases breach the −35% floor** (worst −70.4%). So the passing G-dd-floor reading was a
   favorable draw; **FF-1 is calibrated to a phase-lucky IS maxDD and carries elevated phase-driven
   breach risk** (accepted, not accommodated — §6).
5. **Phase-selection BAN:** **Wed@08h (the sweep max, L1 +1.589) is explicitly FORBIDDEN.** No phase may
   EVER be adopted from the sweep or from the forward phase logs — doing so would convert the disclosed
   robustness analysis into a best-of-21 search and void the n_eff accounting. The all-21 equal-weight
   ensemble is a genuinely more robust *new* construction (a future design iteration), not this test.

## §3 — Costs / funding / state (orchestrator-fixed)

- Costs identical to the backtest: taker 5 bps + slippage 2.5 bps on one-way turnover at fills
  (recorded kline **open = fill price**, exactly as the backtest); **funding** = `blind_funding`
  bucket-sum on held weights; equity compounds multiplicatively; fixed-share drift between rebals.
- **State/logs:** `paper-l1/` at worktree root — `equity.csv` (per-candle), `decisions.csv` (per-rebal:
  target weights, turnover, costs, C1 gate state, C2 exclusions **with names**), `gates.csv` (rolling
  gate readouts), `runs.log`; **append-only, committed weekly** (docs-style commits → git history =
  tamper-evident audit trail).
- **Integrity:** SHA256 of `blind_engine.py` / `blind_risk_calib_006.py` / `blind_mania_rule.py` / the
  runner are **pinned in this doc at T0** (§7); every run re-hashes and **alerts on drift**.
- **Cadence:** weekly, **Wednesday ~00:10 UTC** (aligned to the Wed@00h rebal anchor re-pin, §2), after a
  data refresh (fetch 8h klines for all perp symbols
  + funding into the worktree data path). **Staleness/completeness guard:** retry up to 3× over 6h,
  then proceed on available data with a **DEGRADED** flag logged (engine force-exits invalid prices,
  same as the backtest).

---

## §4 — Pre-registered gates + horizon (QR design)

### 4.0 Statistical-power framing (why the Sharpe gate is deliberately weak)

Forward horizon = **12 months ≈ 1092 8h candles ≈ 52 weekly rebals**. For an annualized Sharpe estimated
from `T_years` of data, the iid asymptotic standard error (Lo 2002) is
**SE(SR̂) ≈ √(1/T_years)** — essentially independent of the true Sharpe at 8h sampling (the
`½·SR_period²` correction is ~3e-4 and negligible). So:

| horizon | T_years | SE(SR̂) |
|---|---|---|
| 6 months | 0.50 | ≈ **1.41** |
| 12 months | 1.00 | ≈ **1.00** |
| 18 months (extension) | 1.50 | ≈ **0.82** |

**A 12-month Sharpe gate has SE ≈ 1.0 — it is LOW-POWER, and crypto fat tails / autocorrelation only
widen the true SE (so treat 1.0 as an optimistic lower bound).** The design consequence is explicit:
the **Sharpe gate is a modest, deflated bar**; the **risk-containment gates (fail-fast) and the
mechanism gates carry the decision weight** because they test decisive single numbers and
conditional/directional edge-mechanism evidence rather than a noisy aggregate.

The **revised** deflated forward Sharpe expectation band (§6, re-anchored off the phase-agnostic mean
+0.947 per REVIEW-006 ADDENDUM 2) is **≈ +0.55–0.80** (superseding the pre-phase-sweep +0.75–0.95). The
SUCCESS Sharpe bar is **RE-AFFIRMED at +0.50** (see §4.3 for the decision): it now sits just below the
re-anchored band floor (+0.55 − 0.05), i.e. a Sharpe SUCCESS requires the realized forward Sharpe to
essentially reach the honest expectation floor — a deliberately non-trivial but still low-power
(SE≈1.0) screen. It was **not** lowered toward the band interior, because the LEVEL axis became MORE
fragile (phase/maxDD), so the design leans further on the strengthened mechanism/design axis (M-C1 /
M-C2 / M-phase) and keeps a meaningful Sharpe SUCCESS, while the PARTIAL band (−0.25…+0.50) + the one
extension absorb the phase-unlucky-but-positive near-misses.

### 4.1 Gate table (FROZEN)

Sign convention: maxDD and returns negative; "breach" = worse than the floor. All forward metrics on
fills at candles with open_time ≥ T0.

| Gate | Type | Metric | Threshold | Evaluated | Power |
|---|---|---|---|---|---|
| **FF-1 maxDD** | HARD fail-fast | forward equity peak-to-trough DD since T0 | **< −35% → FAIL** (NOT widened for phase fragility) | every run | HIGH (acute-crash stop; /005's OOS failure mode was −73%, so −35% stops well short). **At any breach, log the concurrent 21-phase overlay delta for attribution** (breach + positive overlay = base phase-tail fragility, mechanism intact; breach + negative overlay = mechanism failure) — **either way FF-1 FAILS.** |
| **FF-2 worst-month** | HARD fail-fast | any completed forward calendar-month return | **< −15% → FAIL** | every run (on month close) | HIGH (anchors G-worst-month; L1 IS worst was −12.72%) |
| **FF-3 slow-bleed** | HARD fail-fast | trailing-26wk ann. Sharpe **AND** trailing-26wk cum. return | **Sharpe < −1.0 AND return < −15% → FAIL** | every run, once ≥26 fwd weeks | MED (catches a low-vol persistent bleed that FF-1 maxDD misses) |
| **CP6 fail-early** | fail-early only | cumulative forward Sharpe since T0 | **< −1.0 → FAIL-EARLY** (+ re-affirm FF-1/2/3) | 6-mo checkpoint (T0+26wk) | LOW (one-sided; only a clear half-year bleed) — **no SUCCESS/PARTIAL at 6mo** |
| **P-Sharpe** | PRIMARY (tiered) | cumulative forward Sharpe since T0 | **≥ +0.50 → SUCCESS-tier · −0.25…+0.50 → PARTIAL · < −0.25 → FAIL** | 12-mo (T0+52wk) | LOW (SE≈1.0) — deflated by design |
| **P-turnover** | HARD sanity | forward annualized one-way turnover | **≤ 100x** (else FAIL) | 12-mo | structural (L1 IS = 50.1x; >100x = universe/data breakdown) |
| **P-risk-held** | HARD (SUCCESS precondition) | FF-1/FF-2/FF-3 never breached in-window | must hold for SUCCESS | 12-mo | HIGH |
| **M-C1** | mechanism (conditional) | short-leg P&L in C1-fired weeks vs unflagged weeks | fired-week (un-scaled) short leg **more negative** than unflagged → C1 fired on real squeezes → PASS; opposite → CONTRADICTION | 12-mo if ≥4 fired weeks, else **N/A** | HIGH (conditional) |
| **M-C2** | mechanism (conditional) | aggregate counterfactual short P&L of C2-excluded names over their exclusion windows | excluded names were **bad shorts** (counterfactual short P&L < 0) → PASS; > 0 → CONTRADICTION. **Broken out mania-month vs non-mania-month** (caveat-5 non-2024-11 stress) | 12-mo if ≥1 exclusion, else **N/A** | HIGH (conditional; the fragile control) |
| **M-crash** | mechanism (conditional) | forward crash-bucket (frozen rule `btc_ret<−15% OR btc_dd_end(540)>25%`) mean + leg P&L | short leg still the crash friend (short_px > 0) AND bucket mean > 0 → PASS | 12-mo if ≥2 fwd crash months, else **N/A** | MED (low-N, directional) |
| **M-mania** | mechanism (conditional) | forward mania-bucket (frozen `blind_mania_rule` ≥40% coverage) mean + leg P&L | short-leg squeeze fix holds (short_px less negative than an un-controlled short) → PASS | 12-mo if ≥2 fwd mania months, else **N/A** | MED (low-N, directional) |
| **M-phase** | mechanism (conditional, one-sided) | forward overlay delta (L1−V0) across the 21 rebal phases over the full forward window | **overlay delta < 0 at ≥ 11 of 21 phases → CONTRADICTION** (contributes to FAIL exactly as the other M-gate contradictions). **Positive overlay grants NOTHING** — SUCCESS still requires the Wed@00h gates | 12-mo, if ≥ 26 forward weeks, else **N/A** | HIGH (aggregates across phases; selects nothing; tests the strengthened 21/21 overlay claim forward) |

### 4.1a — Weekly INFORMATIONAL 21-phase forward log

The runner computes **all 21 phase books each run** (the same frozen L1 construction at each of the 21
8h phase offsets) and logs, in `gates.csv`: forward Sharpe **mean / min / max across the 21 phases**,
and the **per-phase overlay delta (L1 − V0)**. This log is **INFORMATIONAL** — the binding gates in §4.1
evaluate ONLY the **Wed@00h** book. **No mid-window action derives from the phase log except the
pre-registered M-phase mechanism gate (§4.1) and the FF-1 breach-attribution logging.** The
phase-selection ban (§2.1 point 5) applies absolutely: no phase may be adopted from this log.

### 4.2 Verdict integration at the 12-month PRIMARY

- **FAIL** if ANY of: a fail-fast gate (FF-1/2/3) breached at any point in-window; **or** P-Sharpe < −0.25;
  **or** P-turnover > 100x; **or** any EVALUABLE mechanism gate returns a **CONTRADICTION** — C1 fired but
  worsened outcomes (M-C1) / C2's excluded names were on-net GOOD shorts (M-C2) / **the overlay delta is
  negative at ≥11 of 21 phases (M-phase)** — the edge mechanism is falsified forward, which overrides a
  merely-noisy positive Sharpe.
- **SUCCESS** if ALL of: P-Sharpe ≥ +0.50 **AND** P-risk-held (no fail-fast breach) **AND**
  P-turnover ≤ 100x **AND** every evaluable mechanism gate is PASS-or-N/A (no contradiction).
- **PARTIAL** otherwise (e.g. −0.25 ≤ P-Sharpe < +0.50 with risk contained and no mechanism
  contradiction; or P-Sharpe ≥ +0.50 but a mechanism gate is a borderline CONCERN not a contradiction)
  → **one 6-month extension** (§4.4).

The mechanism gates are load-bearing precisely because the Sharpe is low-power: a mechanism
CONTRADICTION can FAIL even a positive-Sharpe run (the "edge" was luck), and mechanism PASSes are what
let a modest positive Sharpe qualify as SUCCESS.

### 4.3 Error rates for the SUCCESS Sharpe bar (+0.50) at 12 months (honest, quoted)

Normal approx, SE ≈ 1.0 at 12mo (both hypotheses; SR-dependence negligible):

- **P(false PASS | true SR = 0) = P(SR̂ ≥ +0.50) ≈ 31%.** This is the Sharpe-gate ALONE. The SUCCESS
  verdict additionally requires P-risk-held **and** no mechanism contradiction, which drives the **joint**
  false-positive far below 31% (a true-zero book must also survive a year without a −35% DD or a −15%
  month AND have C1/C2 mechanisms non-contradicted — jointly unlikely by luck).
- **P(miss | true SR = 0.85) = P(SR̂ < +0.50) ≈ 36%** — but only **≈14%** of that is an outright FAIL
  (P(SR̂ < −0.25 | 0.85) ≈ 14%); the remaining **≈22%** routes to **PARTIAL → the one extension**, which
  re-tests with more power.

These rates are deliberately poor — that is the honest statistical reality of a one-year Sharpe — and
are the entire reason the risk and mechanism gates carry the weight. **The +0.50 bar is not a
significance test; it is a deflated screen.**

**Tier re-affirmation vs the REVISED band (+0.55–0.80) — FINAL, this is the last moment the tiers can
move.** I **RE-AFFIRM +0.50 SUCCESS / −0.25 FAIL, unchanged.** Power against the revised band (SE≈1.0):
P(miss) for a true book at the band floor +0.55 ≈ **48%** (half of floor-level books land in PARTIAL →
extension), at the band mid +0.675 ≈ **43%**, at the band top +0.80 ≈ **38%**; the outright-hard-FAIL
portion runs 15–21% across the band. **Decision rationale:** the +0.50 SUCCESS bar now sits just below
the re-anchored floor (+0.55), keeping a Sharpe SUCCESS meaningful; I deliberately did NOT lower it to
+0.30 (a quarter-SE below the new floor) because the LEVEL axis became MORE fragile (phase/maxDD), so
SUCCESS should not get cheaper on the noisy Sharpe axis — the confidence shifts to the strengthened
mechanism/design gates (M-C1/M-C2/M-phase), and the PARTIAL band + one extension recover the
phase-unlucky-but-positive middle. The **−0.25 FAIL floor is band-independent** ("a clearly-negative
forward year") and stays put.

### 4.4 Extension rule (pre-registered, once)

**PARTIAL at 12 months → exactly ONE 6-month extension** (to T0 + 78 weeks). At the 18-month terminus,
re-evaluate the SAME gate structure over the **full 18-month forward window** (SE ≈ 0.82):

- **SUCCESS** if P-Sharpe(18mo) ≥ +0.50 AND P-risk-held AND P-turnover ≤ 100x AND no mechanism
  contradiction. **FAIL** otherwise. **No second extension.**
- Error rates at 18mo for the +0.50 bar: **P(false PASS | SR=0) ≈ 27%**, **P(miss | SR=0.85) ≈ 33%**.
  The extension buys only modest power (1.5yr is still low-power); its purpose is to resolve a genuinely
  ambiguous 12-month outcome, not to manufacture significance.

### 4.5 Horizon dates (FROZEN)

| milestone | offset from T0 | date (UTC, **Wednesday**) | forward candles |
|---|---|---|---|
| **T0** (first forward decision/fill) | 0 | **2026-07-15 00:00** | 0 |
| 6-month checkpoint (fail-early only) | +26 weeks | **2027-01-13 00:00** | ≈ 546 |
| **12-month PRIMARY evaluation** | +52 weeks | **2027-07-14 00:00** | ≈ 1092 |
| 18-month extension terminus (if PARTIAL) | +78 weeks | **2028-01-12 00:00** | ≈ 1638 |

---

## §5 — Frozen interpretation map

| 12-mo (or 18-mo) verdict | action |
|---|---|
| **SUCCESS** | Candidate for **small-size REAL deployment consideration** — a NEW decision made WITH the user, **not automatic**. The forward result is entered as evidence; sizing/deployment is a separate approval. |
| **PARTIAL** (12-mo only) | **One 6-month extension**, once, as pre-registered in §4.4. A PARTIAL at the 18-month terminus is a FAIL (no second extension). |
| **FAIL** | **Track concludes. L1 is archived. NO rescue tuning** — no Q scan, no threshold nudge, no control swap. A failed forward test is a result, not a starting point. |

**Clock-reset rule.** ANY change to the construction or any C1/C2/base parameter during the window
**resets the clock to a new T0 and a new protocol version** (PROTOCOL-L1-FORWARD-v2). The whole point
of a pre-registered forward test is that the thing being tested does not move.

**No mid-window peeking-based action** other than the pre-registered fail-fast gates (FF-1/2/3) and the
6-month fail-early checkpoint. The weekly logs are an audit trail, not a decision surface; there is no
"it looks weak, let me adjust" move — the only permitted early actions are the frozen fail-fast stops.

---

## §6 — Multiple-testing note

This is **ONE pre-registered forward test of ONE frozen candidate → n_eff = 1 forward.** The Sharpe bar
is deflated to +0.50 (just below the revised +0.55–0.80 expectation band) **precisely because the IS-side
cumulative selection surface already inflated the IS Sharpe** — the forward test must not re-spend that
budget.

**Ledger update (REVIEW-006 ADDENDUM 2).** The 21-phase sweep added **zero best-of-k inflation** (nothing
was selected — the Wed@00h phase is the a-priori frozen construction, and the sweep-max Wed@08h is
banned) but **+1 researcher-DOF** for the phase choice itself → **cumulative IS-side n_eff ≈ 16–22**
(was 15–21). The material move is a **LEVEL RE-ANCHOR, not a fresh haircut:** the expectation base drops
from the frozen-phase +1.164 to the **phase-agnostic mean +0.947**, and after the standard deflation the
**honest forward Sharpe band is revised to ≈ +0.55–0.80** (superseding +0.75–0.95).

**Forward maxDD honest expectation: −35% … −50% is within the phase-neutral distribution even if the
mechanism holds** (phase-agnostic maxDD mean −37.3%, 7/21 phases breach −35%, worst −70.4%). An FF-1
breach is therefore a **live, phase-driven risk that is ACCEPTED, not accommodated** — FF-1 stays at
−35% (a −35% drawdown is undeployable regardless of cause), and a breach FAILS the test even if the
overlay (mechanism) is intact; the overlay is logged at breach only for attribution (§4.1).

Therefore:
- **No sibling forward variants may be launched.** Running C1-only, C1+C2+C3, a different Q, **or any
  other rebal phase** in parallel would recreate the selection problem forward (best-of-k on the forward
  window) and void the n_eff = 1 property. The forward test validates **exactly L1 at Wed@00h as frozen**
  — it does not get to re-pick among C1/C2/C3/C4, thresholds, or phases. (The 21-phase log is
  informational + the M-phase gate only; §4.1a / §2.1 point 5.)
- The forward Sharpe, if SUCCESS, is **not** re-deflated (n_eff = 1 forward), but it is read against the
  revised ≈ **+0.55–0.80** band, and a SUCCESS is evidence for a deployment *decision*, not proof of a
  specific live Sharpe.

---

## §7 — Integrity pins (populated by the QE at T0, before the first forward run)

At T0 the QE pins, in this section, the SHA256 of: `analysis/portfolio/blind_engine.py`,
`analysis/portfolio/blind_risk_calib_006.py`, `analysis/portfolio/blind_mania_rule.py`, and the forward
runner. Every subsequent weekly run re-hashes and alerts on any drift (a hash change ⇒ the construction
moved ⇒ clock-reset per §5). The append-invariance assert (§1) covers the data side.

```
blind_engine.py         SHA256: <pinned at T0>
blind_risk_calib_006.py SHA256: <pinned at T0>
blind_mania_rule.py     SHA256: <pinned at T0>
forward runner          SHA256: <pinned at T0>
T0 panel extent         : <max grid_ms at T0 build>
```

---

**FROZEN 2026-07-10.** Gates, thresholds, horizon dates, the interpretation map, and the extension rule
are locked before the first forward candle. No OOS was read; the burned window is INPUT-history only; no
backtest was run to author this contract. Any deviation is a new protocol version with a new T0.

---

## §7 ACTIVATION RECORD (2026-07-10)

**Scheduler:** systemd user timer `blind-paper-l1.timer` (`~/.config/systemd/user/`), enabled +
started, `OnCalendar=Wed *-*-* 00:10:00 UTC`, **Persistent=true** (a run missed while the host is
down fires on next boot — harmless: the runner recomputes decisions from recorded klines, so a
late run reconstructs the Wednesday decision exactly). `loginctl` linger enabled for the user.
Verified: next fire Wed 2026-07-15 00:10 UTC = the first forward decision day.

**Job:** `/bin/bash paper-l1/run_weekly.sh` → cd worktree, `PYTHONUNBUFFERED=1 uv run python
analysis/portfolio/blind_paper_l1.py`, output appended to `paper-l1/cron_runs.log`; on runner
exit 0 with log changes, commits `paper-l1/` to `quant-portfolio-blind` via a temporary git
index (tolerates the worktree's pre-existing unmerged path). Runner failure (e.g.
append-invariance ABORT) ⇒ NO commit + FAILED line in cron_runs.log.

**End-to-end proof run (2026-07-10 04:23–04:34 UTC, via the exact scheduled path):** parity
PASS (V0 +0.9134 / L1 +1.1638 direct), append-invariance OK, 0 forward rows (pre-T0, correct),
burned window sealed, auto-commit fired. Known issues found and fixed before T0: the `fetch
--all` kline refresh returned HTTP 400 (diagnosed + fixed, see cron_runs.log for the re-proof)
and the staleness guard counted permanently-dead feeds (LUNAUSDT) in "top-40" — guard re-scoped
to feeds alive in the panel's recent rows so DEGRADED can clear.

**Paper only.** The runner contains no exchange-order code; nothing in this protocol places real
orders. Monitoring cadence: weekly commit diffs on `paper-l1/` are the audit trail; gate
evaluation per §4/§5 only.
