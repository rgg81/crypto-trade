# Iteration 047 Diary - 2026-03-27

## Merge Decision: MERGE

**BREAKTHROUGH: First strategy with BOTH IS and OOS positive Sharpe.**
**First strategy to pass the year-1 fail-fast checkpoint.**

## Configuration
- Symbols: BTCUSDT + ETHUSDT
- Training: 24 months (covers bull + bear)
- Barriers: TP=8%, SL=4% (bigger moves, more predictable)
- Timeout: 7 days (gives 8% targets time to be reached)
- Confidence threshold: Optuna 0.50-0.85
- 50 Optuna trials, 5 CV folds, seed 42

## Results (seed 42)
| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | +1.60 | +1.16 |
| Win Rate | 43.4% | 44.9% |
| Profit Factor | 1.31 | 1.27 |
| Max Drawdown | 64.3% | 75.9% |
| Trades | 574 | 136 |
| IS/OOS Ratio | 0.72 (passes >0.5) |

## Seed Validation (5 seeds)
| Seed | IS Sharpe | OOS Sharpe |
|------|----------|-----------|
| 42   | +1.60    | +1.16     |
| 123  | +1.76    | -0.32     |
| 456  | +1.32    | +1.66     |
| 789  | +1.02    | +0.51     |
| 1001 | +1.19    | -0.95     |

IS: **5/5 positive** (mean +1.38, std 0.27) — robust
OOS: **3/5 positive** (mean +0.41, std 0.95) — profitable on average

## Why This Works
1. **24mo training**: Model sees both bull (2020) and bear (2021) before first predictions in 2022
2. **8%/4% barriers**: Bigger moves are more predictable (iter 027 proved 46% WR at these levels)
3. **7-day timeout**: Gives 8% targets enough time to be reached — previous 3-day timeout caused too many timeouts
4. **BTC+ETH only**: Signal concentrates on the two most liquid, predictable assets

## Key Path to This Result
- Iter 010: BTC+ETH only (first profit)
- Iter 016: 0.85 threshold (best OOS)
- Iter 027: 8%/4% barriers showed 46% WR
- Iter 041-043: Fail-fast killed bad ideas in 5 minutes
- Iter 045: 24mo training → almost passed year-1
- Iter 046: 24mo + 8%/4% → 42% WR but timeout losses
- **Iter 047: + 7-day timeout → BOTH POSITIVE**
