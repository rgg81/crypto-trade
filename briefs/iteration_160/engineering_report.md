# Iteration 160 Engineering Report

## Implementation

Added three functions to `src/crypto_trade/backtest_report.py`:

### `expected_max_sharpe(n_trials: int) -> float`

Closed-form approximation of E[max(SR_0)] under the null hypothesis of
`n_trials` independent random Sharpe estimates (mean 0, unit variance):

```
E[max(SR_0)] ≈ √(2·ln·N) · (1 − γ/(2·ln·N)) + γ/√(2·ln·N)
```

Returns 0.0 for N ≤ 1 (no multiple-testing adjustment).

### `sharpe_standard_error(sharpe: float, returns: list[float]) -> float`

Standard error of an annualized Sharpe ratio, adjusted for skew (γ_3)
and kurtosis (γ_4) of the return distribution:

```
SE(SR)² ≈ (1 − γ_3·SR + (γ_4 − 1)/4·SR²) / (T − 1)
```

Returns 0.0 for T < 3 or degenerate variance.

### `compute_deflated_sharpe_ratio(sharpe, n_trials, returns) -> float`

```
DSR = (SR_observed − E[max(SR_0)]) / SE(SR)
```

Interpretation:
- DSR > 0: observed Sharpe exceeds expected random maximum
- DSR > 1: ~84% confidence the result isn't multiple-testing noise
- DSR < 0: observed Sharpe is within random-chance range
- Returns 0.0 if SE can't be computed

## Tests (13 new, all pass)

**`TestExpectedMaxSharpe`** (4 tests):
- `test_n_one_returns_zero`: N=1 → 0.0
- `test_n_zero_returns_zero`: N=0 → 0.0
- `test_monotonically_increasing`: E[max] strictly rises with N
- `test_known_values`: matches iter 159 reference at N=21/100/200

**`TestSharpeStandardError`** (4 tests):
- `test_too_few_observations`: T<3 → 0.0
- `test_zero_variance`: constant returns → 0.0
- `test_positive_for_normal_returns`: SE > 0 for non-degenerate input
- `test_scales_with_sqrt_t`: more observations shrink SE

**`TestComputeDeflatedSharpeRatio`** (5 tests):
- `test_dsr_exceeds_zero_when_sharpe_above_emax`: high SR + small N
- `test_dsr_below_zero_when_sharpe_below_emax`: low SR + large N
- `test_zero_se_returns_zero`: degenerate input → 0.0
- `test_matches_iter159_baseline_reference`: analytical match (DSR≈+1.38)
- `test_n_one_reduces_to_raw_sharpe_over_se`: formula identity at N=1

## Test Run

```
13 passed in 0.57s
```

No existing tests regressed. 5 pre-existing failures (test_features,
test_lgbm, test_adaptive_range_spike_filter) are unrelated to this
change — verified identical count pre/post via `git stash`.

## Lint

```
ruff check src/crypto_trade/backtest_report.py tests/test_backtest_report.py
All checks passed!
```

## Code Quality

- All new functions have type hints.
- Docstrings explain formula derivation with AFML Ch. 14 reference.
- Pure functions (no I/O, no globals beyond `_EULER_MASCHERONI` constant).
- Edge cases handled: N≤1, T<3, zero variance, negative SE².

## No Strategy Impact

- `BacktestSummary` unchanged (backward-compat preserved).
- `summarize()` unchanged.
- Report generation unchanged (DSR is opt-in, called explicitly).
- BASELINE.md unchanged.

## Usage Example

```python
from crypto_trade.backtest_report import compute_deflated_sharpe_ratio

dsr = compute_deflated_sharpe_ratio(
    sharpe=2.83,           # observed OOS Sharpe
    n_trials=71,           # cumulative configs tested
    returns=oos_daily_returns,
)
if dsr > 1:
    print("Result is statistically significant")
elif dsr > 0:
    print("Result beats random, but not decisively")
else:
    print("Within multiple-testing noise range")
```

## Merge Decision

**MERGE** (infrastructure addition). Baseline v0.152 unchanged. DSR is
now available for future iterations to call.
