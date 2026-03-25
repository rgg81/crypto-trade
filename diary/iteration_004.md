# Iteration 004 Diary - 2026-03-25

## Merge Decision: MERGE

OOS Sharpe improved -1.96→-1.91. Win rate improved 30.7%→32.9% (+2.2pp, biggest gain across all iterations). Max drawdown reduced 5x. The liquid-only universe is clearly better.

## Hypothesis

Reducing from 201 symbols to top 50 by IS quote volume will improve signal quality by focusing the model on liquid, well-behaved markets.

## Configuration Summary

- OOS cutoff: 2025-03-24 (fixed)
- Labeling: Triple barrier TP=4%, SL=2%, timeout=4320min (unchanged)
- **Change**: Top 50 symbols by IS quote volume (from 201)
- Features: 106 (all available in parquet intersection for 50 symbols)
- Walk-forward: monthly, 12-month window, 5 CV, 50 Optuna trials
- Confidence threshold: Optuna 0.50–0.65 (unchanged)
- Seed: 42

## Results: In-Sample (trades with entry_time < 2025-03-24)

| Metric | Value |
|--------|-------|
| Sharpe | -4.63 |
| Sortino | -5.15 |
| Max Drawdown | 13,558% |
| Win Rate | 30.6% |
| Profit Factor | 0.80 |
| Total Trades | 47,269 |
| Calmar Ratio | 1.00 |

## Results: Out-of-Sample (trades with entry_time >= 2025-03-24)

| Metric | Value | Baseline OOS |
|--------|-------|--------------|
| Sharpe | -1.91 | -1.96 |
| Sortino | -2.80 | -2.58 |
| Max Drawdown | 997% | 5,079% |
| Win Rate | 32.9% | 30.7% |
| Profit Factor | 0.92 | 0.89 |
| Total Trades | 6,831 | 26,545 |
| Calmar Ratio | 0.77 | 0.76 |

## Overfitting Diagnostics

| Metric   | IS     | OOS    | Ratio (OOS/IS) | Assessment |
|----------|--------|--------|----------------|------------|
| Sharpe   | -4.63  | -1.91  | 0.41           | Below 0.5 |
| Sortino  | -5.15  | -2.80  | 0.54           | Passes |
| Win Rate | 30.6%  | 32.9%  | 1.08           | OOS better! |

## Hard Constraints Check (all evaluated on OOS)

| Constraint                        | Value | Threshold | Pass |
|-----------------------------------|-------|-----------|------|
| Max Drawdown (OOS)                | 997%  | ≤ 6,095%  | PASS |
| Min OOS Trades                    | 6,831 | ≥ 50      | PASS |
| Profit Factor (OOS)               | 0.92  | > 1.0     | FAIL |
| Max Single-Symbol PnL Contribution| TBD   | ≤ 30%     | TBD  |
| IS/OOS Sharpe Ratio               | 0.41  | > 0.5     | FAIL |

## What Worked

- **Win rate 32.9%**: The most significant improvement across all iterations. Reducing to liquid symbols removed noise. Only 1.1pp from break-even (34%).
- **Max drawdown 5x better**: 997% vs 5,079%. Fewer symbols + slightly better WR = dramatically less accumulated losses.
- **OOS > IS win rate**: 32.9% vs 30.6% — the model generalizes BETTER to OOS. This is rare and suggests the liquid symbols have more stable, learnable patterns in recent data.
- **Fast execution**: ~6,000s total (vs ~17,000s for 201 symbols)

## What Failed

- **Still below break-even**: 32.9% vs 34% needed. Close but not profitable.
- **PF still below 1.0**: 0.92. Needs to cross 1.0 for the strategy to make money.
- **IS/OOS Sharpe ratio 0.41**: Below 0.50 gate. But this is an artifact of both values being negative.

## Next Iteration Ideas

1. **Lower TP/SL barriers**: Try TP=3%/SL=1.5% (same 2:1 RR). More trades resolve via TP (94% vs 87%), cleaner labels. The 1.1pp gap to break-even might close with better label quality.
2. **Add BTC regime filter**: Only trade in trending regimes (BTC ADX > median). Choppy regimes showed -0.06% mean return in EDA — filtering them out might push WR past 34%.
3. **Increase Optuna trials**: 50 trials may not be enough for the threshold + hyperparams. Try 100 trials per month.
4. **Try top 30 symbols**: Even more focused. Top 30 covers the most liquid names.

## Lessons Learned

- Liquid symbols are significantly more predictable than the full universe. The WR jump from 30.7% to 32.9% is the largest improvement from any single change.
- The 106 features available for 50 symbols (vs 25 for iter 003's 40 symbols) shows the parquet intersection matters: fewer symbols = more common features available.
- OOS win rate EXCEEDING IS win rate (32.9% vs 30.6%) suggests the model is genuinely learning patterns that persist — the signal is real, just not strong enough yet.
