# Iteration v2/009 Engineering Report

**Type**: EXPLOITATION (NEAR 18-month training window)
**Role**: QE
**Date**: 2026-04-14
**Branch**: `iteration-v2/009` on `quant-research`
**Parent baseline**: iter-v2/005 (10-seed mean +1.297)
**Decision**: **NO-MERGE** — 10-seed mean +1.250 fails primary by 0.047
(within noise but strictly fails), primary seed 42 concentration fails
at 54%, NEAR primary seed 42 went negative.

## Run Summary

| Item | Value |
|---|---|
| Models | 4 (E=DOGE, F=SOL, G=XRP, H=NEAR) |
| NEAR training_months | **18** (vs 24 baseline, 12 in iter-v2/008) |
| Seeds | 10 |
| Optuna trials | 10 |
| Wall-clock | ~50 min |

## Primary seed 42 — comparison vs baseline

| Metric | iter-v2/005 | iter-v2/009 | Δ |
|---|---|---|---|
| OOS Sharpe | +1.671 | +1.431 | **−0.240** |
| OOS PF | 1.457 | 1.371 | −0.09 |
| OOS MaxDD | 59.88% | 63.74% | +3.86 pp |
| OOS WR | 45.3% | 43.8% | −1.5 pp |
| **IS Sharpe** | **+0.116** | **+0.416** | **+0.300** |
| IS PF | 1.029 | 1.101 | +0.072 |
| **IS MaxDD** | 111.55% | 92.07% | **−19.48 pp** |
| IS WR | 40.1% | 40.6% | +0.5 pp |
| IS/OOS Sharpe ratio | +0.069 | **+0.290** | +0.22 |

**The IS improvement is real**: IS Sharpe jumped from +0.12 to +0.42 —
the first material IS recovery in 4 iterations. IS MaxDD dropped by
nearly 20 pp. IS/OOS ratio is now +0.29 (much closer to the > 0.5
target).

**But the OOS regressed**: primary seed 42 OOS Sharpe dropped 0.24,
and the per-symbol breakdown reveals why.

## Per-symbol OOS (primary seed 42)

| Symbol | iter-v2/005 | iter-v2/009 | Δ |
|---|---|---|---|
| DOGEUSDT | 31 trades, +11.52% (12.3%) | **identical** | — |
| SOLUSDT | 37, +28.89% (30.7%) | **identical** | — |
| XRPUSDT | 27, +44.89% (47.8%) | **identical** | — |
| **NEARUSDT** | **22, +8.71% (9.3%)** | **26, −2.11% (−2.5%)** | **−10.82 pp** |

**DOGE/SOL/XRP metrics are byte-for-byte identical** — perfect
one-variable isolation. Only NEAR changed.

**NEAR primary seed 42 went negative** at 18 months (−2.11% weighted,
−0.07 Sharpe) despite being +8.71% at 24 months and +23.93% at 12 months.
The 18-month window is WORSE than both endpoints on seed 42 specifically.

**Interpretation**: the NEAR hyperparameter landscape is non-monotonic
in training window length. Seed 42's Optuna search at 18 months
happened to land in a bad local optimum — one that neither of the
other two windows produced. This is a local-optimum trap, not a
systematic degradation.

## Concentration (primary seed 42)

| Share of signed OOS weighted PnL | iter-v2/005 | iter-v2/009 |
|---|---|---|
| DOGEUSDT | 12.3% | 13.8% |
| SOLUSDT | 30.7% | 34.7% |
| XRPUSDT | **47.8%** | **54.0%** |
| NEARUSDT | 9.3% | **−2.5%** |
| Concentration rule (≤ 50%) | PASS | **FAIL** |

**XRP concentration is back to 54%** because NEAR went negative,
shrinking the positive-share denominator. This is a second strict
failure on primary seed 42. (Absolute-share concentration is 51.4%
— also above 50% but marginally.)

## 10-seed summary

| Seed | iter-v2/005 | iter-v2/009 | Δ |
|---|---|---|---|
| 42 | +1.671 | +1.431 | −0.240 |
| 123 | +1.287 | +1.398 | +0.111 |
| 456 | +1.560 | **+1.948** | **+0.388** |
| 789 | +0.565 | +0.912 | +0.347 |
| 1001 | +1.644 | **+2.232** | **+0.588** |
| 1234 | +1.485 | +1.581 | +0.096 |
| 2345 | +0.685 | **+0.130** | **−0.555** |
| 3456 | +0.319 | +0.320 | +0.001 |
| 4567 | +1.130 | +1.218 | +0.088 |
| 5678 | +1.172 | +1.335 | +0.163 |

| Statistic | iter-v2/005 | iter-v2/009 | Δ |
|---|---|---|---|
| Mean OOS Sharpe | +1.297 | +1.250 | **−0.047** |
| Std | ~0.552 | 0.621 | +0.069 |
| Min | +0.319 | +0.130 | −0.189 |
| Max | +1.866 | **+2.232** | +0.366 |
| Profitable | 10/10 | 10/10 | — |

**7 of 10 seeds IMPROVED**. Only 3 regressed (42, 2345, and a tiny
change on 3456). The mean nonetheless landed slightly below baseline
because seeds 42 and 2345 dropped more than the others improved.

**Primary 10-seed mean fails by 0.047** — within the standard error
of the mean (~0.20) but strictly below baseline. Under the strict
rule (primary > baseline), NO-MERGE.

## Hard-constraint check

| Constraint | Target | Actual | Pass? |
|---|---|---|---|
| **Primary: 10-seed mean > +1.297** | +1.297 | **+1.250** | **FAIL** (−0.047) |
| ≥ 7/10 seeds profitable | 7/10 | 10/10 | PASS |
| OOS trades ≥ 50 | 50 | 121 | PASS |
| OOS PF > 1.1 | 1.1 | 1.371 | PASS |
| OOS MaxDD ≤ 64.1% | 64.1% | 63.74% | PASS (marginally) |
| **Concentration ≤ 50% (primary seed)** | **50%** | **54.0%** | **FAIL** |
| DSR > +1.0 | 1.0 | +13.67 | PASS |
| IS/OOS ratio > 0 | 0 | +0.29 | PASS (strongly, first v2 iter with healthy ratio) |
| v2-v1 correlation < 0.80 | 0.80 | not recomputed | likely PASS |

**Two strict failures**: primary metric and concentration. The IS
improvement is valuable but not enough to override the strict rules.

## Pre-registered failure mode — 100% confirmed

Brief §6.3 said: "The most likely way iter-v2/009 fails is that 18
months is a non-committing compromise — neither stable enough nor
regime-free enough. The 10-seed distribution lands between
iter-v2/005's (mean +1.297) and iter-v2/008's (mean +1.089), roughly
at +1.15 to +1.25."

**Confirmed exactly**: 10-seed mean landed at **+1.250** — inside the
predicted +1.15 to +1.25 band, closer to the upper end. The brief
correctly anticipated the compromise-window failure mode.

## Category C insight validated: NEAR's 59% SL rate

iter-v2/005 per-symbol analysis showed NEAR has the highest SL rate
(59%) and highest TP rate (32%) of all 4 symbols — a **decisive** but
**adverse** exit distribution. The 18-month window didn't change this
structure materially for NEAR; the per-trade expectancy on NEAR stays
marginally positive (~+0.05 raw) regardless of window length.

**This is a SYMBOL quality issue, not a training window issue.** The
window shift just moves which hyperparameter local optimum gets found
— the underlying NEAR signal quality is bounded by NEAR's price
action. A different symbol (FIL, APT) might not have this bound.

## Pattern across iter-v2/005-009 — NEAR tuning is exhausted

| Iteration | NEAR change | NEAR primary OOS | 10-seed mean | Decision |
|---|---|---|---|---|
| 005 | Baseline (24mo) | +8.71% wt | **+1.297** | MERGE |
| 006 | ADX 20→15 | +8.71% wt (unchanged) | +1.294 | NO-MERGE |
| 007 | Optuna 10→25 | +3.53% wt | not run | NO-MERGE |
| 008 | NEAR 12mo | **+23.93% wt** | +1.089 | NO-MERGE |
| 009 | NEAR 18mo | −2.11% wt | +1.250 | NO-MERGE |

**iter-v2/008 has the best NEAR primary seed** (+23.93% weighted at
12mo, seed 42) but the worst 10-seed mean (wide variance).
**iter-v2/009 has the most volatile NEAR primary seed** (−2.11%)
despite having the best IS recovery. NEAR tuning is an over-optimized
parameter space — further NEAR-specific changes are unlikely to
break through iter-v2/005's +1.297 baseline.

**The right next step is NOT more NEAR tuning**. iter-v2/010 should
try **replacing NEAR with FIL** — a clean symbol swap that tests
whether the 4th-symbol slot can find a less-fragile contributor.

## Label Leakage Audit

No leakage. `training_months` parameter is supported in `LightGbmStrategy`
and flows correctly through the walk-forward generator.

## Conclusion

iter-v2/009 validated two findings:

1. **NEAR's IS weakness is fixable via shorter training window** — IS
   Sharpe jumped from +0.12 to +0.42. This is a genuine improvement.
2. **But the OOS primary metric doesn't move** — 10-seed mean lands at
   +1.250 (within noise but strictly below +1.297 baseline). The
   NEAR hyperparameter landscape is non-monotonic in window length,
   so different seeds find different local optima — the 10-seed mean
   is the average across them and doesn't systematically improve.

**The 4th-symbol slot should be re-evaluated**. NEAR's structural
signal quality appears to be bounded by its price action (59% SL rate,
decisive but adverse exit distribution). A different symbol might
yield a better 4th contributor.

**Decision**: NO-MERGE. Cherry-pick docs. Next iteration: FIL
replacement (iter-v2/010).

**Lessons for iter-v2/010+**:

1. **Stop tuning NEAR**. iter-v2/007-009 all tried NEAR-specific
   interventions. None moved the 10-seed mean above baseline.
   The ceiling is real.
2. **Symbol replacement is the remaining NEAR lever**. FIL has the
   same v1 correlation, similar IS length, different historical
   trajectory. Clean 1-variable swap.
3. **IS Sharpe CAN be improved** (iter-v2/009 proved it) but the
   mechanism (shorter training window) trades off against OOS
   stability. Per-symbol tuning is the right surface but NEAR is the
   wrong symbol for it.
4. **The 10-seed std floor is ~0.55**. Any change that moves the mean
   by less than ~0.1 is in the noise floor. This gives a practical
   threshold for iter-v2/010's hypothesis strength test.
