# Iteration 160 Research Brief

**Type**: EXPLOITATION (infrastructure — DSR implementation)
**Model Track**: codebase enhancement, no strategy change
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Iter 159's DSR audit demonstrated that v0.152's OOS Sharpe is within
random-chance range at N≥71 cumulative configurations. The iter 159
diary's Next Ideas #3 directly recommended: "Implement DSR as an official
metric: add `compute_deflated_sharpe()` to `backtest_report.py` as a code
iteration. Future iterations would report DSR alongside raw Sharpe."

This iteration is that code change.

## Scope

**ADD**:
- `compute_deflated_sharpe_ratio(sharpe, n_trials, returns)` function in
  `backtest_report.py` implementing AFML Ch. 14 formula
- `expected_max_sharpe(n_trials)` helper for E[max(SR_0)]
- `sharpe_standard_error(sharpe, returns)` helper using skew/kurtosis
- Tests in `tests/test_backtest_report.py`

**DO NOT CHANGE**:
- `BacktestSummary` dataclass (backward-compat preserved)
- `summarize()` function (DSR is a separate, opt-in computation)
- Iteration report generation (that's a follow-up iter if needed)

## Formula (AFML Ch. 14)

```
E[max(SR_0)] ≈ √(2·ln·N) · (1 − γ/(2·ln·N)) + γ/√(2·ln·N)
SE(SR)² ≈ (1 − γ_3·SR + (γ_4−1)/4·SR²) / (T−1)
DSR = (SR_observed − E[max(SR_0)]) / SE(SR)
```

Where γ = 0.5772 (Euler-Mascheroni), γ_3 = skewness, γ_4 = kurtosis,
T = return observation count.

**Interpretation**:
- DSR > 1: ~84% confidence observed Sharpe isn't multiple-testing noise
- DSR > 0: observed Sharpe exceeds expected random maximum
- DSR < 0: observed Sharpe is within random-chance range

## Tests

Unit tests verify:
1. `expected_max_sharpe(1)` returns 0.0 (no multiple testing).
2. `expected_max_sharpe(N)` is monotonically increasing in N.
3. `sharpe_standard_error()` returns positive value for non-degenerate
   returns.
4. `compute_deflated_sharpe_ratio()` matches iter 159's reference
   calculation (v0.152 baseline, N=21, DSR≈+1.38).

## Checklist Categories

- **H (Overfitting Audit)**: implements the mandatory DSR metric.

## Success Criteria

- All new unit tests pass
- `ruff check` clean on modified files
- Existing tests unaffected (no regressions)

## No Merge Decision Expected

This is a pure infrastructure iteration. The codebase gains DSR; BASELINE
remains v0.152. Merge iff tests pass — no strategy OOS comparison
involved.
