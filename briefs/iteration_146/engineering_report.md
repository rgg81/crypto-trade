# Iteration 146 Engineering Report

## Results

| Metric | Baseline (iter 145) | Iter 146 (A+C+D+DOGE+VT) | Change |
|--------|---------------------|---------------------------|--------|
| OOS Sharpe | +2.33 | **+2.10** | **-10%** |
| OOS Sortino | +3.01 | +2.65 | -12% |
| OOS WR | 50.6% | 50.9% | +0.3pp |
| OOS PF | 1.53 | 1.45 | -5% |
| OOS MaxDD | 38.09% | 48.49% | +27% |
| OOS Calmar | 3.40 | 2.83 | -17% |
| OOS Trades | 164 | 214 | +50 (DOGE) |
| OOS Net PnL | +129.5% | +137.2% | +6% |

**Avg scale**: 0.59 (more aggressive deleveraging than iter 145's 0.65 due to higher 4-model vol).

## Per-Symbol OOS

| Symbol | Trades | WR | Net PnL | % Total |
|--------|--------|-----|---------|---------|
| ETHUSDT | 34 | 55.9% | +40.1% | 29.2% |
| DOGEUSDT | 50 | 52.0% | +33.2% | 24.2% |
| LINKUSDT | 42 | 52.4% | +28.4% | 20.7% |
| BNBUSDT | 50 | 52.0% | +24.4% | 17.8% |
| BTCUSDT | 38 | 42.1% | +11.1% | 8.1% |

**Best concentration ever**: ETH 29.2%, under the strict 30% threshold for the first time.

## Comparison: DOGE impact with and without vol targeting

| | iter 138 (A+C+D) | iter 145 (A+C+D+VT) | iter 143 (A+C+D+DOGE) | iter 146 (A+C+D+DOGE+VT) |
|-|------------------|---------------------|------------------------|---------------------------|
| Sharpe | +2.32 | +2.33 | +2.30 | +2.10 |
| MaxDD | 62.8% | 38.1% | 92.5% | 48.5% |

Vol targeting reduces DOGE-portfolio's MaxDD from 92.5% → 48.5% (-48%), but Sharpe
degrades from +2.33 → +2.10 (-10%). DOGE's correlated drawdowns remain problematic
even under vol targeting.

## Hard Constraints

| Constraint | Threshold | Iter 146 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.33 | +2.10 | **FAIL** |
| OOS MaxDD ≤ 45.7% | ≤ 45.7% | 48.49% | **FAIL** |
| OOS Trades ≥ 50 | ≥ 50 | 214 | PASS |
| OOS PF > 1.0 | > 1.0 | 1.45 | PASS |
| Concentration ≤ 50% | ≤ 50% | 29.2% | **PASS** (best ever) |

Primary (Sharpe) AND MaxDD constraints both fail.

## Label Leakage Audit

Reused deterministic trade outputs; no new training runs. All prior audits valid.
