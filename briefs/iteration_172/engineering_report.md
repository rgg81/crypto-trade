# Iteration 172 Engineering Report

**Role**: QE
**Config**: DOT standalone full IS+OOS, baseline 193 features, ATR 3.5/1.75, no year-1 fail-fast
**Status**: COMPLETED
**Elapsed**: 79 min (4,759 s)

## Headline metrics (DOT standalone)

| Metric       | IS                | OOS               | IS/OOS ratio |
|--------------|-------------------|-------------------|--------------|
| Sharpe       | **−0.07**         | **+0.65**         | −8.84        |
| WR           | 41.5%             | 45.6%             | 1.10         |
| Profit Factor| 0.97              | 1.25              | 1.28         |
| MaxDD        | 71.55%            | 20.63%            | 0.29         |
| Trades       | 118               | 57                | 0.48         |
| Net PnL      | **−5.96%**        | **+19.40%**       | −3.26        |

Key observation: iter-168's year-1 fail-fast was catching a single adverse year (2022), not a systemic failure. DOT is break-even in IS overall and clearly positive in OOS. The previous "reject" verdicts on DOT at iters 168 / 171 were based on incomplete information.

## R1 Risk Mitigation Analysis (from skill's new section)

### R1 bucket analysis on DOT IS (`analysis/iteration_172/dot_r1_bucket_is.csv`)

| Preceding SL streak | Trades | WR      | Mean PnL |
|---------------------|-------:|--------:|---------:|
| 0                   | 53     | 45.3%   | −0.55%   |
| 1                   | 29     | 44.8%   | +1.44%   |
| **2**               | **13** | **23.1%** | **−2.31%** |
| **3**               | **9**  | **22.2%** | **−2.56%** |
| ≥ 4                 | 14     | 50.0%   | −0.19%   |

The 2-3 streak buckets are the clear "knife-catching" zone — WR collapses to ~23% (half the break-even rate for 8%/4% effective) at those streak lengths.

### R1 simulation sweep (`analysis/iteration_172/r1_sweep.py`)

Applied to full IS+OOS DOT trade stream:

| Config                       | IS Sharpe | IS MaxDD | OOS Sharpe | OOS MaxDD | OOS PnL   |
|------------------------------|----------:|---------:|-----------:|----------:|----------:|
| Baseline (no R1)             | −0.21     | 71.55%   | +1.70      | 20.63%    | +19.40%   |
| K=3 C=18 (skill default)     | +0.26     | 59.73%   | +1.80      | 15.89%    | +19.20%   |
| K=3 C=27 (9 days)            | **+1.04** | **49.18%** | +1.48    | 19.65%    | +15.44%   |

K=3 C=27 lifts DOT IS Sharpe past the 1.0 floor while retaining OOS profitability.

### LTC R1 bucket analysis (cross-check)

LTC is the baseline's strongest standalone symbol. Does R1 help or hurt LTC?

| Streak | Trades | WR     | Sum PnL |
|--------|-------:|-------:|--------:|
| 0      | 105    | 41.0%  | −19.86  |
| 1      | 53     | 50.9%  | +93.80  |
| 2      | 22     | 50.0%  | +28.58  |
| **3**  | **9**  | **33.3%** | **−19.45** |
| ≥ 4    | 9      | 55.6%  | +25.85  |

LTC has a similar streak=3 WR collapse (33%). Applying R1 K=3 C=18 to LTC is defensible (evidence-based).

## Pooled portfolio metrics (A+C+LTC+DOT + R1 variants)

From `analysis/iteration_172/r1_sweep.py`:

| Config                             | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS PnL | LINK% | merge status |
|------------------------------------|----------:|-----------:|----------:|--------:|------:|:-----|
| Baseline v0.165 (A+C+LTC)          | +1.08     | +1.27      | **30.56%**| +73.64% | 77.5% | current baseline |
| +DOT (no R1)                       | +0.91     | +1.34      | 37.82%    | +93.04% | 61.3% | ✗ floor + MaxDD fail |
| +DOT R1 K=2 C=18                   | +1.04     | +1.31      | 35.22%    | +89.12% | 64.0% | ✗ concentration |
| +DOT+LTC R1 K=3 C=18               | +1.02     | +1.30      | **33.09%**| +89.35% | 63.8% | ✗ concentration |
| +DOT R1 K=3 C=27                   | +1.09     | +1.29      | 36.84%    | +89.08% | 64.0% | ✗ concentration |

All variants pass the 1.0 Sharpe floors and OOS-vs-baseline. None passes the "single symbol ≤ 30% OOS PnL" concentration hard constraint (best is 61.3%). Diversification exception requires MaxDD to *improve* by >10%; adding DOT regresses MaxDD by 2-7pp, so the exception does not apply.

## Merge decision under strict rules: NO-MERGE

| Check | Threshold | Best R1 config | Pass? |
|-------|-----------|----------------|:-----:|
| IS Sharpe floor | > 1.0 | +1.02 | ✓ |
| OOS Sharpe floor | > 1.0 | +1.30 | ✓ |
| OOS Sharpe > baseline | > +1.27 | +1.30 | ✓ |
| OOS MaxDD ≤ 36.67% | ≤ 36.67% | 33.09% | ✓ |
| Min 50 OOS trades | ≥ 50 | 253 | ✓ |
| OOS PF > 1.0 | > 1.0 | 1.28 | ✓ |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 1.27 | ✓ |
| **Single symbol ≤ 30% OOS PnL** | ≤ 30% | **63.8%** | ✗ |

And diversification exception fails on MaxDD improvement requirement.

## Feature Reproducibility Check

All runs passed `feature_columns=list(BASELINE_FEATURE_COLUMNS)` — 193 explicit columns. Confirmed by `[lgbm] 193 feature columns, 51 walk-forward splits` in logs.

## Label Leakage Audit

CV gap `22` rows per fold. Unchanged.

## Deliverables for next iteration

All analysis CSVs saved in `analysis/iteration_172/` (gitignored):
- `dot_monthly_pnl.csv`
- `btc_monthly_regime.csv`
- `dot_vs_btc_regime_joined.csv`
- `filter_candidate_evaluation.csv`
- `dot_r1_bucket_is.csv`
- `dot_r1_simulation_summary.csv`

The R1 framework (code in `analysis/iteration_172/risk_mitigation_r1.py`) is proven as a post-hoc simulator. For this to become a merge-worthy mechanism, it needs to be implemented in the backtest engine itself (`BacktestConfig.risk_consecutive_sl_*` params per the skill). That is iter 173's task.
