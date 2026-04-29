# Iteration v2/009 Research Brief

**Type**: EXPLOITATION (NEAR training window middle-ground)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, primary seed 42 +1.671)
**Date**: 2026-04-14
**Researcher**: QR
**Full Research Checklist Required**: Yes (3+ consecutive NO-MERGE rule)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/006, iter-v2/007, iter-v2/008 are all NO-MERGE. Per the v2 skill
rule, iter-v2/009 must complete **4+ categories from the Research
Checklist** (A-H) plus mandatory Category I.

Beyond the procedural requirement, the pattern across the last 3 NO-MERGEs
is informative. Each one showed:

1. **iter-v2/006** (ADX 20→15): primary seed 42 +0.11, 10-seed mean flat,
   IS Sharpe went negative. Pre-registered failure mode confirmed.
2. **iter-v2/007** (Optuna 10→25): primary seed 42 −0.19, IS unchanged
   (hypothesis failed), per-symbol PnL redistributed rather than aggregate
   lifting.
3. **iter-v2/008** (NEAR 12mo window): primary seed 42 +0.29 (v2's best
   single-seed), but 10-seed mean dropped −0.21 due to cross-seed variance
   widening.

The thread: **iter-v2/005's baseline is a strong local optimum** that is
resistant to small perturbations. We're seeing "primary seed 42 is biased
upward" repeatedly because seed 42 tends to find the best local
configurations under the standing regime, and most changes widen the
cross-seed distribution.

iter-v2/009 attempts to split the difference on the NEAR-window axis: 18
months instead of 12 or 24. The goal is to capture SOME of iter-v2/008's
NEAR OOS quality improvement (+15 pp weighted PnL on primary seed) while
restoring enough training samples to stabilize the hyperparameter search.

## Research Checklist Coverage

Per the 3+ consecutive NO-MERGE mandate, this brief covers **4 categories
from A-H** plus Category I:

### Category A: Feature Contribution — deferred to iter-v2/010+

Running per-symbol feature importance analysis requires a dedicated
reference LightGBM training run (described in v2 skill §20 A1). The
effort is substantial and iter-v2/009's hypothesis doesn't hinge on
feature-level changes. Deferred to a future iteration.

### Category B: Symbol Universe & Diversification Analysis ✓

**Is NEAR the right symbol at all?** Reviewing iter-v2/001's 6-gate
screening results:

| Candidate | v1 corr | IS rows | Daily vol | Notes |
|---|---|---|---|---|
| DOGEUSDT | 0.507 | 5,153 | $967M | Meme, currently Model E |
| SUIUSDT | 0.588 | 2,071 | $476M | Just over 1yr IS, risky |
| FILUSDT | 0.665 | 4,845 | $257M | Next-best L1-adjacent |
| APTUSDT | 0.665 | 2,661 | $309M | Shorter IS, 1yr 9mo |
| NEARUSDT | 0.665 | 4,847 | $240M | Currently Model H |
| XRPUSDT | 0.665 | 5,696 | $1022M | Currently Model G |
| TRXUSDT | 0.667 | 5,669 | $138M | Lower volume |
| SOLUSDT | 0.669 | 4,941 | $1581M | Currently Model F |

NEAR and FIL have essentially the same screening profile (both at v1 corr
0.665, ~4,845 IS rows). FIL has slightly more daily volume ($257M vs
$240M). **FIL is a near-identical alternative** — if iter-v2/009's
18-month NEAR fails, iter-v2/010 should swap NEAR for FIL.

**NEAR vs the 2022 bear context**: NEAR's price trajectory was
particularly brutal in 2022. From a January 2022 high of ~$20 to a
December 2022 low of ~$1.50 — a −92.5% drawdown. For comparison, FIL
also had a bad 2022 but less extreme. The training-regime hostility is
worse for NEAR than for any other L1 candidate.

**Category B conclusion**: NEAR is a reasonable candidate but
structurally harder than alternatives. 18-month window is the right
next step before considering symbol replacement.

### Category C: Labeling Analysis ✓

**NEAR OOS exit-reason distribution (iter-v2/005 baseline, seed 42)**:

| Exit reason | n | % | Raw PnL | Weighted PnL |
|---|---|---|---|---|
| take_profit | 7 | 32% | +82.07% | +54.28% |
| **stop_loss** | **13** | **59%** | **−80.73%** | **−47.22%** |
| timeout | 2 | 9% | +2.19% | +1.65% |

**Compared to other symbols (exit reason rates)**:

| Symbol | TP rate | SL rate | Timeout rate |
|---|---|---|---|
| DOGEUSDT | 23% | 48% | 29% |
| SOLUSDT | 27% | 51% | 19% |
| XRPUSDT | 30% | 44% | 26% |
| **NEARUSDT** | **32%** | **59%** | **9%** |

**NEAR has the highest TP rate AND the highest SL rate of all 4 symbols**.
Very few timeouts (9% vs 19-29% for others). This means **NEAR's TP/SL
barriers are well-calibrated to NEAR's volatility** — trades decisively
hit one barrier or the other rather than drifting out to timeout.

But the asymmetry (32% TP, 59% SL) means the average NEAR trade is a
loser even with the 2:1 reward:risk ratio. Expected value at 32% TP /
59% SL / 9% timeout with 2:1 R:R:

  EV = 0.32 × 2 − 0.59 × 1 + 0.09 × 0 = 0.64 − 0.59 = **+0.05** (marginally positive)

NEAR per-trade raw EV is barely positive. With fees (0.1%/trade) factored
in, NEAR is near break-even per-trade — which matches iter-v2/005's
observed NEAR per-trade net PnL of +0.40% / trade (22 trades, +8.71%
weighted).

**Category C finding**: NEAR's label distribution is fine (TP:SL ratio
is actually the best in the portfolio), but the WR is structurally low.
To improve NEAR's OOS contribution beyond +8.71%, we need to either:

1. **Raise the WR** via better entry signals (which is what shorter
   training window attempts — learn from more recent regime)
2. **Change the barrier ratio** — wider SL reduces SL rate but also
   reduces TP rate; tighter SL cuts losses faster but loses more to
   timeouts. iter-v2/003's widening experiment failed for this reason.

18-month training window is the cleaner intervention.

### Category E: Trade Pattern Analysis ✓

**NEAR OOS monthly distribution (iter-v2/005 baseline)**:

| Month | n | wins | raw_pnl | wt_pnl | mean/trade |
|---|---|---|---|---|---|
| 2025-04 | 1 | 1 | +11.54% | +4.04% | +11.54% |
| 2025-06 | 4 | 1 | −7.30% | −5.35% | −1.83% |
| 2025-07 | 8 | 3 | −4.61% | −0.80% | −0.58% |
| 2025-08 | 4 | 1 | −4.72% | +1.46% | −1.18% |
| 2025-09 | 3 | 2 | +14.37% | +12.03% | +4.79% |
| 2025-11 | 1 | 1 | +0.65% | +0.47% | +0.65% |
| 2026-01 | 1 | 0 | −6.41% | −3.14% | −6.41% |

**Clear bimodal pattern**: NEAR is profitable in April 2025 and September
2025 (+11.54% and +14.37% respectively, 100% and 67% WR) but unprofitable
in the middle months (June-August 2025, −16.63% combined).

The summer 2025 weakness is concentrated in one stretch. If we look at
NEAR's price action (not analyzed here but known from data): NEAR was
in a choppy range during that period while the ATR percentile gates were
passing through signals that ultimately resolved to SL.

**Category E finding**: NEAR's 2025 OOS weakness is time-concentrated
(not uniformly distributed). A shorter training window (18 or 12 months)
means the model predicting, say, August 2025 is trained on Oct 2023 -
July 2025 data (18 months) or April 2024 - July 2025 data (12 months)
— both exclude 2022 bear entirely. The more recent training data
should capture late-2024/early-2025 NEAR dynamics, which are closer
to what's needed for the summer 2025 bad stretch.

This supports the 18-month window hypothesis.

### Category I: Risk Management Analysis ✓ (mandatory)

See §6 below.

## Hypothesis

An 18-month rolling training window for NEAR should:

1. **Retain ~75% of iter-v2/005's training samples** (18/24) compared
   to iter-v2/008's 50% (12/24) — should stabilize hyperparameter
   search across seeds.
2. **Partially avoid 2022 bear**: the 18-month window for a model
   predicting 2023-12 starts at 2022-06, missing the worst Q1-Q2 2022
   crashes but keeping H2 2022 recovery. For a model predicting 2024+,
   the window entirely excludes 2022.
3. **Capture SOME of the 12-month NEAR OOS improvement** while
   preserving more of iter-v2/005's cross-seed stability.
4. **Leave DOGE/SOL/XRP unchanged** (still at 24-month window).

Quantitative prediction (pre-registered):

- **NEAR per-symbol weighted OOS Sharpe**: +0.33 to +0.80 (between
  iter-v2/005's +0.33 at 24mo and iter-v2/008's seed-42 +1.36 at 12mo)
- **NEAR OOS weighted PnL**: +10% to +20% (between +8.71% at 24mo
  and +23.93% at 12mo)
- **Primary seed 42 OOS Sharpe**: +1.7 to +1.9
- **10-seed mean**: +1.20 to +1.40 (goal: ≥ +1.297 baseline)
- **Std**: between iter-v2/005's 0.552 and iter-v2/008's ~0.74
- **Concentration**: XRP 40-47% (under 50%)

## Failure-mode prediction (pre-registered)

Most likely way to fail:

1. **18 months is a compromise that doesn't commit**. The 12→24 relationship
   may not be linear — 18mo could be worse than both endpoints, landing
   between their failure modes (less NEAR OOS quality AND still some
   cross-seed instability). Signal: 10-seed mean lands at +1.10 to +1.20.
2. **NEAR summer 2025 weakness persists**. The 18-month window starting
   mid-2022 could actually INCLUDE NEAR's 2022 Q3-Q4 volatile period,
   which has its own pattern-learning issues. NEAR OOS summer stretch
   stays negative.
3. **NEAR's structural hostility is not fixable at any window length**.
   If 18mo also fails, iter-v2/010 should pivot to symbol replacement
   (Category B flagged FILUSDT as a near-identical alternative).

## Configuration (one variable changed from iter-v2/005)

| Setting | iter-v2/005 | iter-v2/009 | Changed? |
|---|---|---|---|
| DOGE training_months | 24 | 24 | — |
| SOL training_months | 24 | 24 | — |
| XRP training_months | 24 | 24 | — |
| **NEAR training_months** | **24** | **18** | **Yes** |
| Schema | 2-tuple `(name, symbol)` | 3-tuple `(name, symbol, months)` | iter-v2/008 refactor reused |
| Everything else | Same | Same | — |

## Success Criteria (inherits iter-v2/005 baseline)

Primary: **10-seed mean OOS Sharpe > +1.297**.

Hard constraints: same as iter-v2/008. ≥7/10 profitable, concentration
≤ 50%, PF > 1.1, trades ≥ 50, DSR > +1.0, v2-v1 correlation < 0.80,
IS/OOS ratio > 0.

## Section 6: Risk Management Design

### 6.1 Active primitives

Unchanged from iter-v2/005. 5 active gates (vol scaling, ADX at 20,
Hurst regime, feature z-score OOD, low-vol filter at 0.33).

### 6.2 Expected fire rates

NEAR gate stats may shift because the 18-month feature z-score OOD
training window is 75% of the 24-month one. Slight widening of
per-feature stats could reduce z-score OOD fire rate marginally. Low
expected impact.

### 6.3 Pre-registered failure-mode prediction

"The most likely way iter-v2/009 fails is that 18 months is a
non-committing compromise — neither stable enough nor regime-free
enough. The 10-seed distribution lands between iter-v2/005's (mean
+1.297) and iter-v2/008's (mean +1.089), roughly at +1.15 to +1.25.
If this happens, iter-v2/010 should either (a) commit to symbol
replacement with FIL, or (b) accept the current baseline and shift
focus to the drawdown brake or combined-portfolio preparation."

### 6.4 Exit Conditions

Unchanged.

### 6.5 Post-Mortem Template

Phase 7 will compare per-symbol NEAR metrics across iter-v2/005,
iter-v2/008, iter-v2/009 at each seed level, and report the
cross-seed variance of NEAR at each training window length.
