# Engineering Report: Iteration 055

## Configuration

- **Change**: Balanced class weights (`_balance_weights()` from iter 048)
- **Symbols**: BTCUSDT, ETHUSDT
- **Training**: 24 months, 5 CV folds, 50 Optuna trials
- **Barriers**: TP=8%, SL=4%, timeout=7 days (10080 min)
- **Confidence threshold**: Optuna 0.50–0.85
- **Seeds**: 42, 123, 456, 789, 1001
- **Code change**: Added `_balance_weights(y, w)` in optimization.py — scales sample weights so sum(w[class_0]) ≈ sum(w[class_1]) in both CV folds and final retrain

## Seed Validation Results

| Seed | IS Sharpe | OOS Sharpe | OOS WR | OOS PF | OOS MaxDD | OOS Trades | OOS PnL |
|------|-----------|------------|--------|--------|-----------|------------|---------|
| 42   | +1.86     | +0.10      | 40.0%  | 1.02   | 77.9%     | 170        | +6.8%   |
| 123  | +1.65     | -1.94      | 32.3%  | 0.73   | 128.4%    | 130        | -89.1%  |
| 456  | +1.19     | +0.77      | 40.7%  | 1.15   | 74.5%     | 150        | +50.3%  |
| 789  | +1.09     | +0.53      | 41.7%  | 1.12   | 51.0%     | 115        | +30.4%  |
| 1001 | +1.32     | -0.56      | 36.8%  | 0.91   | 79.5%     | 133        | -28.1%  |

**IS**: 5/5 positive (mean +1.42, std 0.29)
**OOS**: 3/5 positive (mean -0.22, std 0.97)

**FAIL**: Mean OOS Sharpe -0.22 ≤ 0. Only 3/5 profitable (need ≥ 4).

## Comparison with Baseline 047 Seed Validation

| Seed | Baseline OOS | Balanced Weights OOS | Delta |
|------|-------------|---------------------|-------|
| 42   | +1.16       | +0.10               | -1.06 |
| 123  | -0.32       | -1.94               | -1.62 |
| 456  | +1.66       | +0.77               | -0.89 |
| 789  | +0.51       | +0.53               | +0.02 |
| 1001 | -0.95       | -0.56               | +0.39 |

| Metric | Baseline | Balanced |
|--------|----------|----------|
| Mean OOS Sharpe | +0.41 | -0.22 |
| OOS Std | 0.95 | 0.97 |
| OOS Profitable | 3/5 | 3/5 |
| Mean IS Sharpe | +1.38 | +1.42 |

Balanced weights WORSEN OOS performance (mean dropped from +0.41 to -0.22) while slightly improving IS (mean +1.38 → +1.42). Classic overfitting signature.

## Per-Symbol OOS Breakdown

| Seed | BTC Trades | BTC WR | BTC PnL | ETH Trades | ETH WR | ETH PnL |
|------|-----------|--------|---------|-----------|--------|---------|
| 42   | 59        | 47.5%  | +15.1%  | 111       | 36.0%  | -8.2%   |
| 123  | 48        | 33.3%  | -53.9%  | 82        | 31.7%  | -35.2%  |
| 456  | 57        | 45.6%  | +6.0%   | 93        | 37.6%  | +44.3%  |
| 789  | 35        | 37.1%  | -21.9%  | 80        | 43.8%  | +52.3%  |
| 1001 | 41        | 43.9%  | -0.6%   | 92        | 33.7%  | -27.4%  |

No consistent pattern — dominance swings between BTC and ETH across seeds. In 3/5 seeds, one symbol is significantly negative.

## Critical Finding: Iter 050 Discrepancy

Seed 42 in iter 055 produces OOS Sharpe +0.10. Iter 050 (same supposed approach) reported OOS +1.66.

Investigation: `git diff main..iteration/050 -- src/` shows **NO code changes**. The iteration/050 branch is identical to main. This means iter 050 did NOT actually use balanced class weights — it was a re-run of the baseline configuration. The OOS +1.66 was simply the baseline with a lucky Optuna run, not a result of balanced weights.

The iteration/048 branch DOES have the `_balance_weights` code. Iter 050's diary claiming "retry of iter 048 approach" was incorrect — the code was never applied.

## Trade Execution Verification (10 sample trades)

Verified from seed 42 OOS trades.csv:
- Entry prices match signal candle close prices
- SL = entry ± 4% correctly computed
- TP = entry ± 8% correctly computed
- Timeout = open_time + 10080 min correctly
- PnL calculations correct: SL trades = -4.1% (net of fee), TP = +7.9% (net of fee)
- No anomalies found

## Early Stops

Seeds 42 and 1001 hit early stop (year 2025 PnL negative). Seeds 123, 456, 789 ran to completion.
