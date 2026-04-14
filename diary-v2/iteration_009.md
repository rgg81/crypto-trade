# Iteration v2/009 Diary

**Date**: 2026-04-14
**Type**: EXPLOITATION (NEAR 18-month training window, full checklist)
**Track**: v2 — diversification arm
**Branch**: `iteration-v2/009` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Decision**: **NO-MERGE** — 4th consecutive NO-MERGE. Primary 10-seed
mean +1.250 (−0.047 from baseline), primary seed 42 concentration
strict-fails at 54%, NEAR seed 42 went negative at the 18mo window.
IS recovery is real but OOS primary metric doesn't move.

## Results — 10-seed distribution

| Statistic | iter-v2/005 baseline | iter-v2/009 | Δ |
|---|---|---|---|
| **Mean OOS Sharpe** | **+1.297** | **+1.250** | **−0.047** |
| Std | 0.552 | 0.621 | +0.07 |
| Min | +0.319 | +0.130 | −0.189 |
| Max | +1.866 | **+2.232** | +0.366 |
| Profitable | 10/10 | 10/10 | — |

**Distribution widened slightly** (std +0.07), max rose (+0.37), min
dropped (−0.19). 7 seeds improved, 3 regressed. The mean lands **0.047
below baseline**, inside the standard error (~0.20) but strictly
below.

## Primary seed 42 breakdown

| Metric | iter-v2/005 | iter-v2/009 | Δ |
|---|---|---|---|
| OOS Sharpe | +1.671 | +1.431 | −0.24 |
| OOS PF | 1.457 | 1.371 | −0.09 |
| OOS MaxDD | 59.88% | 63.74% | +3.86 pp |
| OOS WR | 45.3% | 43.8% | −1.5 pp |
| **IS Sharpe** | **+0.116** | **+0.416** | **+0.30** |
| IS PF | 1.029 | 1.101 | +0.072 |
| **IS MaxDD** | 111.55% | **92.07%** | **−19.48 pp** |
| IS/OOS Sharpe ratio | +0.069 | **+0.290** | +0.22 |

**IS RECOVERED materially**: IS Sharpe jumped from +0.12 to **+0.42**
— the first material IS improvement in 4 iterations. IS MaxDD fell
from 111% to 92%. IS/OOS ratio is now +0.29 (healthy direction).

**But OOS regressed on primary seed**: OOS Sharpe dropped by 0.24.
This is seed 42's specific misfortune at 18 months — the NEAR
hyperparameter search found a worse local optimum than either 12 or
24 months produced.

## Per-symbol OOS (primary seed) — NEAR went NEGATIVE

| Symbol | iter-v2/005 (24mo) | iter-v2/008 (12mo) | iter-v2/009 (18mo) |
|---|---|---|---|
| DOGE | +11.52% wt (31 trades, 48.4% WR) | identical | identical |
| SOL | +28.89% wt (37 trades, 37.8%) | identical | identical |
| XRP | +44.89% wt (27 trades, 55.6%) | identical | identical |
| **NEAR** | **+8.71% wt, 22, 40.9%** | **+23.93% wt, 22, 50.0%** | **−2.11% wt, 26, 34.6%** |

**DOGE/SOL/XRP are byte-for-byte identical** across all three
iterations — confirms the one-variable NEAR isolation holds.

**NEAR varies dramatically by window length**:
- 24mo: +8.71% weighted (modest positive)
- 12mo: +23.93% weighted (BEST — iter-v2/008)
- **18mo: −2.11% weighted (WORST — iter-v2/009)**

**18mo is not "between" 12mo and 24mo**. It's outside both. NEAR's
hyperparameter landscape is non-monotonic in training window length
— specific seeds find local optima at specific window lengths, and
seed 42 at 18mo found a bad one.

## Concentration — primary seed 42 strict fail

| Share of signed OOS weighted PnL | iter-v2/005 | iter-v2/009 |
|---|---|---|
| DOGEUSDT | 12.3% | 13.8% |
| SOLUSDT | 30.7% | 34.7% |
| XRPUSDT | **47.8%** | **54.0%** |
| NEARUSDT | 9.3% | **−2.5%** |
| **Rule (≤ 50%)** | PASS | **FAIL** |

XRP signed-share rises to 54% because NEAR went negative, shrinking
the positive-contributor denominator. Absolute-share concentration
is 51.4% — also over 50%.

**Second strict failure** on primary seed 42.

## Pre-registered failure mode — 100% confirmed

Brief §6.3 predicted: "18 months is a non-committing compromise. The
10-seed distribution lands between iter-v2/005 (+1.297) and
iter-v2/008 (+1.089), roughly at +1.15 to +1.25."

**Actual: +1.250**. Inside the predicted band, at the upper end. The
brief correctly anticipated the compromise-window failure.

## Cross-iteration NEAR-tuning summary

| Iter | NEAR change | NEAR primary OOS | 10-seed mean | Primary decision factor |
|---|---|---|---|---|
| 005 | 24mo (baseline) | +8.71% wt | **+1.297** | BASELINE |
| 006 | ADX 20→15 | unchanged | +1.294 (flat) | IS catastrophe |
| 007 | Optuna 10→25 | +3.53% wt | — | Hypothesis failed flat |
| 008 | NEAR 12mo | **+23.93% wt** | +1.089 | Cross-seed variance widened |
| 009 | NEAR 18mo | −2.11% wt | +1.250 | Primary still below baseline |

**Pattern**: 4 consecutive iterations targeting various levers (ADX,
Optuna, NEAR window at 12mo, NEAR window at 18mo). All four
NO-MERGE. iter-v2/005's **+1.297 mean is a genuine local optimum**
that these interventions haven't been able to improve.

## Hard constraints

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| **Primary: 10-seed mean > +1.297** | +1.297 | **+1.250** | **FAIL** (−0.047) |
| ≥ 7/10 seeds profitable | 7/10 | 10/10 | PASS |
| OOS trades ≥ 50 | 50 | 121 | PASS |
| OOS PF > 1.1 | 1.1 | 1.371 | PASS |
| OOS MaxDD ≤ 64.1% | 64.1% | 63.74% | PASS (marginally) |
| **Concentration ≤ 50% (primary)** | **50%** | **54.0%** | **FAIL** |
| DSR > +1.0 | 1.0 | +13.67 | PASS |
| IS/OOS ratio > 0 | 0 | **+0.29** | PASS (best v2) |

**Two strict failures**: primary metric and concentration. No
override applies (no new symbols).

## Exploration/Exploitation Tracker

- iter-v2/001-009: 3 EXPLORATION (001, 005, 008), 6 EXPLOITATION
- Rolling rate: 3/9 = **33%**, above 30% minimum

**Consecutive NO-MERGE count: 4** (006, 007, 008, 009). The mandatory
Research Checklist was completed for this iteration (Categories B, C,
E, I).

## Lessons Learned

1. **NEAR tuning is exhausted**. Four iterations tried NEAR-specific
   interventions (ADX for all, Optuna depth, 12mo window, 18mo window).
   None lifted the 10-seed mean above iter-v2/005's +1.297. The
   NEAR hyperparameter landscape is non-monotonic and NEAR's price
   action structurally limits its contribution.

2. **IS Sharpe CAN be moved** — iter-v2/009 proved it (+0.30 IS
   improvement). But the mechanism (shorter NEAR window) is tied to
   a seed-variance trade-off that neutralizes on the 10-seed mean.
   IS improvement without OOS improvement isn't enough to MERGE.

3. **The 10-seed std floor is ~0.55**. Changes that shift the mean by
   less than ~0.10 Sharpe are inside the noise floor of the
   measurement. iter-v2/009's −0.047 delta is well inside that — a
   meaningful change by this metric requires a shift of at least
   0.15-0.20.

4. **Pre-registered failure modes work (again)**. Brief §6.3
   predicted +1.15 to +1.25 mean; actual was +1.250. The brief was
   a useful falsifier because I couldn't post-hoc reinterpret the
   outcome.

5. **NEAR's structural ceiling is visible now**. Its 59% SL rate and
   32% TP rate produce a per-trade EV of ~+0.05, regardless of
   hyperparameter search or training window. This is a symbol
   quality issue, not a training quality issue. Replacing NEAR with
   a symbol that doesn't have this structural SL ratio is the
   remaining lever.

6. **The strongest argument AGAINST more NEAR tuning is the 10-seed
   consistency**: no NEAR change has moved the 10-seed mean by more
   than ±0.21, and most changes land within ±0.05. Given the ~0.20
   standard error of the mean, these are noise-level differences.
   The signal is: NEAR as currently used is stuck.

## lgbm.py Code Review

No changes needed. Per-symbol `training_months` flows correctly
through the walk-forward generator. No bugs.

One observation: with very short training windows (12mo), the
walk-forward generator produces more monthly splits because the
window warmup period is shorter. This causes NEAR to have more trade
opportunities in early IS months (2021) than with 24mo. Not a bug,
but worth documenting: shorter training windows don't just change
the training data — they change the SET of months that get models
at all.

## Next Iteration Ideas

### Priority 1 (iter-v2/010, EXPLORATION): Replace NEAR with FIL

iter-v2/001's screening ranked FILUSDT second among L1-adjacent alts
after NEAR (both at v1 correlation 0.665). FIL has:
- 4,845 IS candles (NEAR: 4,847 — essentially identical)
- $257M daily volume (NEAR: $240M — slightly higher)
- Filecoin's price trajectory: had a 2022 bear but less extreme than
  NEAR's −92% crash (FIL dropped roughly −87% from peak vs NEAR's −92%)
- Different underlying use case (decentralized storage vs L1 blockchain)

**Pre-registered hypothesis**: FIL as Model H (replacing NEAR) gives
a different 4th contributor with potentially better per-trade EV
than NEAR's 32% TP / 59% SL. Even if FIL's aggregate PnL matches
NEAR's, the reduced seed variance should lift the 10-seed mean above
iter-v2/005's +1.297.

**Pre-registered failure mode**: FIL has the same NEAR-like problems
(hostile 2022 training data, structural SL disadvantage). 10-seed
mean lands at +1.20-1.30 (similar to NEAR-based iterations). If
confirmed, iter-v2/011 should pivot to EITHER:
- Accept baseline, shift to drawdown brake or combined portfolio prep
- Try a completely different 4th symbol (SOL variant, payment/non-L1
  category entirely)

EXPLORATION category (symbol universe change), restores exploration
rate to 4/10 = 40%.

### Priority 2 (iter-v2/011): Accept iter-v2/005, shift focus

If FIL also fails to beat iter-v2/005, the v2 track has clearly
found a strong local optimum. Three productive directions:

a. **Enable drawdown brake** — deferred from iter-v2/001. Adds
   capital-preservation during slow monotone bleeds that no current
   gate catches. EXPLOITATION, but adds a genuinely new mechanism.

b. **Combined portfolio preparation** — start `run_portfolio_combined.py`
   on the `main` branch (outside v2 iteration scope). The v2
   baseline is robust enough to start testing its combination with
   v1.

c. **Paper-trade v2 baseline** — deploy iter-v2/005's 4-symbol
   portfolio on a paper trading account for ground-truth validation.

## MERGE / NO-MERGE

**NO-MERGE**. Cherry-pick research brief + engineering report + this
diary to `quant-research`. Branch stays as record.

iter-v2/005 remains the v2 baseline:
- 10-seed mean: +1.297
- Primary seed 42: +1.671
- Profitable: 10/10
- Concentration: 47.8%
- v2-v1 correlation: −0.046

**4th consecutive NO-MERGE** (006, 007, 008, 009). iter-v2/010 is on
a pivot:
- Last NEAR intervention (FIL replacement) or
- Shift away from 4th-symbol tuning entirely toward deferred
  primitives and combined portfolio work
