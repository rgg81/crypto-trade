# Iteration 159 Research Brief

**Type**: EXPLOITATION (analytical overfitting audit, no new config)
**Model Track**: v0.152 baseline DSR audit
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 158 produced a marginal improvement (+0.023 OOS Sharpe) that strictly
beat baseline but was called NO-MERGE because the improvement was within
multiple-testing noise. The diary recommended implementing the Deflated
Sharpe Ratio (DSR) to establish a **principled magnitude floor** for
future iteration MERGE criteria.

This iteration computes DSR retroactively for v0.152 accounting for the
accumulated iteration count, and derives the minimum Sharpe improvement
required for future MERGE candidates to be statistically distinguishable
from multiple-testing noise.

## Method

Per AFML Ch. 14 (Bailey & López de Prado):

```
E[max(SR_0)] ≈ √(2 ln N) × (1 − γ/(2 ln N)) + γ/√(2 ln N)
DSR = (SR_observed − E[max(SR_0)]) / SE(SR)
SE(SR) ≈ √((1 − γ_3·SR + (γ_4-1)/4·SR²) / (T-1))
```

where γ = 0.5772 (Euler-Mascheroni), γ_3 = skewness, γ_4 = kurtosis,
T = obs count.

DSR > 0 means observed Sharpe beats the expected max under random null.
DSR > 1 means ~84% confidence the result isn't multiple-testing noise.

## Scenarios

N (trial count) is the key question:

1. **N=21**: single iteration (iter 158's grid). Strict per-iteration DSR.
2. **N=71**: cumulative configs tested in iters 152-158 (9+5+14+14+8+21).
3. **N=159**: full iteration history count (generous upper bound).

## Checklist Categories

- **H (Overfitting Audit)**: MANDATORY per skill's "Multiple testing" rule.
- **F (Statistical Rigor)**: DSR is a formal statistical test for Sharpe
  significance under multiple testing.

## Hypothesis

At N=21 (isolated iteration), v0.152's OOS Sharpe +2.83 should beat
E[max(SR_0)] ≈ 2.47, giving positive DSR. At N=71+, the accumulated
iteration count may place the baseline within the noise range.

## Output

This iteration produces a **recommended magnitude floor for future MERGE
criteria** derived from the DSR framework. No config change is proposed;
no MERGE/NO-MERGE on a trading strategy.
