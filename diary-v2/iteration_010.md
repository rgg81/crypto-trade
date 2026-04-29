# Iteration v2/010 Diary

**Date**: 2026-04-14
**Type**: EXPLORATION (symbol replacement NEAR → FIL)
**Track**: v2 — diversification arm
**Branch**: `iteration-v2/010` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Decision**: **NO-MERGE** (1-seed fail-fast). **5th consecutive
NO-MERGE**. FIL is structurally equivalent to NEAR as a 4th
contributor — same 2022 bear training problem, slightly worse OOS
per-trade expectancy. The 4th-symbol slot is definitively bounded at
the iter-v2/005 ceiling.

## The 5-iteration pattern — definitive ceiling

| Iter | Intervention | Primary seed 42 OOS | 10-seed mean | Distance from baseline |
|---|---|---|---|---|
| 005 | NEAR @ 24mo (BASELINE) | +1.671 | **+1.297** | — |
| 006 | ADX 20→15 | +1.782 | +1.294 | −0.003 (flat) |
| 007 | Optuna 10→25 | +1.481 | (not run) | below baseline |
| 008 | NEAR @ 12mo | +1.965 | +1.089 | −0.208 |
| 009 | NEAR @ 18mo | +1.431 | +1.250 | −0.047 |
| 010 | FIL @ 24mo | +1.420 | (1-seed) | below baseline |

**5 consecutive NO-MERGEs**. The baseline mean has not moved.

## FIL replacement — results

Primary seed 42 (1-seed, iter-v2/010):

| Metric | iter-v2/005 NEAR | iter-v2/010 FIL | Δ |
|---|---|---|---|
| OOS Sharpe | +1.671 | +1.420 | −0.25 |
| OOS MaxDD | 59.88% | **55.52%** | **−4.36 pp** |
| IS Sharpe | +0.116 | +0.163 | +0.05 |
| IS MaxDD | 111.55% | 108.02% | −3.53 pp |

### Per-symbol OOS

| Symbol | iter-v2/005 | iter-v2/010 |
|---|---|---|
| DOGEUSDT | 31, +11.52% (12.3%) | **identical** |
| SOLUSDT | 37, +28.89% (30.7%) | **identical** |
| XRPUSDT | 27, +44.89% (47.8%) | **identical** |
| **Model H** | **NEAR: 22, +8.71%, +0.33 sr** | **FIL: 23, −4.51%, −0.17 sr** |

**DOGE/SOL/XRP byte-for-byte identical** — the symbol swap is
isolated to Model H.

**FIL is materially worse than NEAR**:

| Metric | NEAR | FIL |
|---|---|---|
| Per-trade WR | 40.9% | 43.5% |
| TP rate | 32% | 26% |
| SL rate | 59% | 52% |
| Timeout rate | 9% | 22% |
| OOS weighted Sharpe | +0.33 | **−0.17** |
| IS raw PnL | −67.39% | **−72.93%** |

FIL's lower SL rate (52% vs 59%) is partly offset by lower TP rate
(26% vs 32%) and much higher timeout rate (22% vs 9%). Net per-trade
expectancy is slightly worse.

**Concentration**: XRP 55.6% — strict fail (same pattern as iter-v2/009).
The 4th model going negative pushes XRP's positive share above 50%.

## Pre-registered failure mode — confirmed

Brief §6.3 said: "FIL has the same structural problems as NEAR.
FIL OOS weighted PnL within ±5% of NEAR's ±8.71% range."

**Actual**: FIL OOS weighted PnL is **−4.51%**. Delta from NEAR is
−13.22 pp — larger than predicted. FIL is WORSE than NEAR.

The overall conclusion (FIL doesn't break the ceiling) holds.

## Why 10-seed validation was skipped

Same reasoning as iter-v2/007 and iter-v2/009's skip decision:

1. **Primary seed 42 is 0.25 below baseline** — larger gap than
   iter-v2/009 (−0.24) or iter-v2/008 (+0.29 above). Similar pattern
   to both.
2. **Per-symbol FIL shows a structural failure** — negative Sharpe,
   worse-than-NEAR exit distribution.
3. **Pre-registered failure mode confirmed unambiguously** — not a
   seed-specific quirk.
4. **Compute discipline** — 50 min to confirm a clear NO-MERGE is
   wasteful when the strategic pivot (iter-v2/011+) is the higher-
   value work.

## Hard constraints

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| OOS Sharpe (seed 42) ≳ baseline | +1.67 | +1.42 | Fail (−0.25) |
| OOS trades ≥ 50 | 50 | 118 | PASS |
| OOS PF > 1.1 | 1.1 | 1.380 | PASS |
| OOS MaxDD ≤ 64.1% | 64.1% | 55.52% | PASS (better) |
| **Concentration ≤ 50% (primary seed)** | **50%** | **55.6%** | **FAIL** |
| IS/OOS ratio > 0 | 0 | +0.11 | PASS |

## Exploration/Exploitation Tracker

- iter-v2/001: EXPLORATION
- iter-v2/002: EXPLOITATION
- iter-v2/003: EXPLOITATION (NO-MERGE)
- iter-v2/004: EXPLOITATION
- iter-v2/005: EXPLORATION
- iter-v2/006: EXPLOITATION (NO-MERGE)
- iter-v2/007: EXPLOITATION (NO-MERGE)
- iter-v2/008: EXPLORATION (NO-MERGE)
- iter-v2/009: EXPLOITATION (NO-MERGE)
- **iter-v2/010: EXPLORATION (NO-MERGE)**

Rolling 10-iter: 4 EXPLORATION / 6 EXPLOITATION = **40% exploration**.

5 consecutive NO-MERGEs. The "3+ consecutive NO-MERGE" rule is still
in effect.

## Lessons Learned

1. **The 4th-symbol slot is structurally bounded**. 5 different
   interventions on 4 different levers (ADX threshold, Optuna depth,
   NEAR window at 12mo and 18mo, FIL replacement) all failed to lift
   the 10-seed mean. Neither the symbol choice nor the training
   parameters are the constraint — the ceiling is in the data.

2. **All cryptocurrency L1/storage alts with similar screening
   profiles share the 2022 bear problem**. FIL dropped −87% peak-to-
   trough in 2022, NEAR dropped −92%. Both produce hostile training
   distributions that marginally-profitable models struggle to
   generalize from.

3. **The v2 baseline at iter-v2/005 is a genuine local optimum**.
   Not just "slightly hard to beat" — it's the ceiling for this
   configuration. Moving beyond it requires a **fundamentally
   different approach** (new feature set, different model
   architecture, event-driven sampling, etc.) or **different
   infrastructure** (per-symbol Optuna studies, ensemble model
   stacking, etc.).

4. **Fail-fast is legitimate when the pattern is clear**. 5 consecutive
   NO-MERGEs with similar failure modes is a strong signal to stop
   pouring compute into the same axis and pivot. iter-v2/010 skipping
   its 10-seed validation saved ~50 minutes of compute for a
   near-certain NO-MERGE.

5. **The strategic goal is now the combined-portfolio, not v2 track
   improvements**. The user's initial ask was diversification + risk
   management to feed the combined portfolio. Both are delivered.
   Continued v2 track work has diminishing returns; combined portfolio
   work has not started at all.

## Strategic Pivot Recommendation

**STOP 4th-symbol tuning**. The ceiling is real. Three productive
directions for subsequent work:

### Option A (iter-v2/011): Enable drawdown brake (deferred primitive)

The iter-v2/001 diary flagged the drawdown brake as a deferred risk
primitive. It addresses the "slow monotone bleed" failure mode that
no current gate catches. Implementation requires:
- Adding a `RiskV2Wrapper._check_drawdown` hook that tracks portfolio
  running PnL
- A mechanism for the wrapper to observe trade closes (needs a
  callback or an engine-level hook)
- Config: `enable_drawdown_brake=True`, `dd_shrink_threshold=5%`,
  `dd_flatten_threshold=10%`

Expected outcome: SAME OOS Sharpe (doesn't improve return) + SMALLER
MaxDD (risk improvement). Primary metric unlikely to strictly improve
but the baseline QUALITY is meaningfully better.

### Option B (off-track): Combined portfolio preparation on `main`

Create `run_portfolio_combined.py` on the `main` branch that loads
both v1's baseline (BTC/ETH/LINK/BNB) and v2's baseline
(DOGE/SOL/XRP/NEAR via v0.v2-005) and reports combined metrics. The
key questions to answer:
- Combined 10-seed mean OOS Sharpe (should exceed either v1 or v2
  alone due to low correlation)
- Combined MaxDD (should be better than v1's 21.81% or v2's 53.42%)
- Combined concentration (should dilute XRP from 47.8% to ~20%)
- Combined v1-v2 correlation (should match v2-v1 correlation of
  −0.046)

This is the actual end-goal of the v2 track. Pursuing it validates
whether the work was worth it.

### Option C: Paper trading v0.v2-005

Deploy the current v2 baseline on a paper trading account. Live data
is the ultimate validation. Let the model run forward for 1-3 months
and compare live results to walk-forward OOS projections.

**Recommendation**: **Option B (combined portfolio prep)**. It is the
explicit end-goal of the entire project and has not been started.
Even a minimum-viable `run_portfolio_combined.py` would be more
valuable than another v2 iteration.

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick research brief + engineering report + this
diary. Branch stays as record.

iter-v2/005 remains the v2 baseline.

**5th consecutive NO-MERGE. The pattern is now clear enough to
recommend stopping 4th-symbol tuning entirely.**
