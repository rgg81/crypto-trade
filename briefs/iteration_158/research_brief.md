# Iteration 158 Research Brief

**Type**: EXPLOITATION (ADX threshold grid with principled selection)
**Model Track**: v0.152 baseline + ADX-exclude filter
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 157 found that rule D_adx_q3 (drop trades where 19.6 < sym_ADX ≤ 34.6)
beat baseline OOS Sharpe (+2.95 vs +2.83). But the IS-best selection rule
picked a more aggressive filter (G) that failed OOS. Iter 157's diary
identified t-stat-adjusted IS selection as the proper metric.

**Open question**: Is the ADX-Q3 finding robust across nearby ADX
thresholds, or is it a single lucky boundary?

This iteration grid-searches the ADX exclusion bounds and uses a
**pre-specified t-stat-adjusted IS selection rule** to pick the winner.

## Method

### Grid

Drop trades where `lower < sym_ADX_14 ≤ upper` for:
- lower ∈ {15, 18, 20, 22, 25}
- upper ∈ {30, 33, 36, 40, 45}

25 (lower, upper) pairs. For each, apply iter 152 VT to kept trades.

### Pre-Specified Selection Rule

**t-stat-adjusted IS Sharpe**: `IS_Sharpe × sqrt(IS_trade_count)`.

Justification (pre-OOS):
- Standard AFML Ch. 14 Deflated Sharpe framework: Sharpe variance scales
  with 1/n, so Sharpe × sqrt(n) is proportional to a t-statistic.
- Sample-size-unweighted Sharpe maximization rewards aggressive filtering
  (iter 157 pathology: IS-best G had 211 trades, OOS failed).
- t-stat adjustment penalizes thin-n configurations.

Constraint: **min 200 IS trades retained** (1/3 of baseline 652), stricter
than iter 157's 150 threshold.

### Checklist Categories

- **E (Trade Pattern)**: iter 157 bucket analysis established ADX Q3 as weak.
- **F (Statistical Rigor)**: t-stat-adjusted selection is the formal
  statistical principle.

## Hypothesis

If the ADX-Q3 signal is robust:
1. Multiple nearby (lower, upper) pairs will have positive IS Sharpe impact.
2. The t-stat-best pair will have OOS Sharpe ≥ baseline (+2.83).
3. OOS MaxDD will improve and OOS PF will improve.

If the finding is noise:
1. Only iter 157's exact (19.6, 34.6) boundary works.
2. Small perturbations hurt IS or OOS materially.

## Hard Constraints

- OOS Sharpe > baseline (+2.83) — **primary**
- OOS trades ≥ 50
- OOS MaxDD ≤ 38.7%
- OOS PF > 1.0
- Concentration ≤ 50%

## Notes

No primary model retraining. Post-processing on iter 138 trades. Pure IS
selection; OOS seen only once after t-stat-best is identified.

Random seed: N/A (no stochastic components in rule-based filter).
