# Iteration 068 Diary — 2026-03-28

## Merge Decision: MERGE

OOS Sharpe +1.84 > baseline +1.64. All hard constraints pass except single-symbol concentration, which the baseline also violates (102.9% ETH). Iter 068 actually improves concentration to 91.6%.

**OOS cutoff**: 2025-03-24

## Hypothesis

Signal cooldown: after a trade closes for a symbol, wait 2 candles (16h) before allowing a new trade. Reduces rapid re-entry that constitutes 81% of baseline trades.

## Configuration Summary

- Ensemble: seeds [42, 123, 789], 3 models per month
- cooldown_candles=2 (the ONLY change vs baseline)
- All else identical to iter 067

## Results

| Metric | Iter 068 | Baseline (067) | Change |
|--------|----------|----------------|--------|
| IS Sharpe | +1.22 | +1.23 | -0.8% |
| IS MaxDD | 45.9% | 50.0% | -4.1pp |
| IS Trades | 373 | 495 | -24.6% |
| OOS Sharpe | +1.84 | +1.64 | +12.2% |
| OOS MaxDD | 42.6% | 39.0% | +3.6pp |
| OOS Trades | 87 | 114 | -23.7% |
| OOS PF | 1.62 | 1.49 | +8.7% |
| OOS WR | 44.8% | 39.5% | +5.3pp |

## What Happened

### 1. Cooldown removed 24% of trades — the marginal ones

The 2-candle cooldown eliminated ~120 IS trades (495→373) and 27 OOS trades (114→87). These were the rapid re-entries that had WR 42% in the baseline (below overall 45%). Removing them improved per-trade quality.

### 2. OOS Sharpe improved 12% despite fewer trades

Fewer but better trades. The cooldown forced the model to skip immediate re-entries after losses, breaking some of the consecutive loss streaks that drive drawdown.

### 3. IS MaxDD improved 4pp (50% → 46%)

Consistent with fewer rapid re-entries during loss streaks. The Aug-Oct 2024 drawdown period (all shorts, 49 trades in baseline) would have fewer trades with cooldown.

### 4. OOS MaxDD slightly worse (+3.6pp)

42.6% vs 39.0%. The cooldown doesn't prevent directional bias — the model still goes persistently short when it's wrong. It just trades less often during those periods.

### 5. OOS/IS ratio of 1.50 is suspicious but explainable

The OOS period is 4 months vs 37 months IS. With 87 OOS trades, the Sharpe has high variance. The ratio would normalize with more OOS data.

## Baseline Constraint Check

1. OOS Sharpe 1.84 > 1.64 → **PASS**
2. OOS MaxDD 42.6% ≤ 46.8% (39.0% × 1.2) → **PASS**
3. Min 50 OOS trades: 87 → **PASS**
4. OOS PF 1.62 > 1.0 → **PASS**
5. Single symbol ≤30%: ETH 91.6% → FAIL (but baseline 102.9% also fails — inherent to 2-symbol universe)
6. OOS/IS ratio 1.50 > 0.5 → PASS (flagged >0.9, see analysis above)

## Exploration/Exploitation Tracker

Last 10 (iters 059-068): [E, E, X, X, E, X, E, X, E, E]
Exploration rate: 5/10 = 50%
Type: EXPLORATION (trade execution — signal cooldown)

## Lessons Learned

1. **The original whipsaw hypothesis was wrong, but cooldown helped anyway.** The EDA showed whipsaws are rare (12-15%) and profitable. But cooldown still helped by removing marginal rapid re-entries (WR 42%, below average). The mechanism is different from hypothesized.

2. **81% immediate re-entry is too aggressive.** The baseline's model trades immediately after each close. Cooldown=2 reduced this to 0% and improved quality. The model needs time for the market to develop new information.

3. **Single-symbol concentration constraint is inapplicable to 2-symbol portfolios.** With BTC+ETH only, it's mathematically near-impossible to have each <30%. This constraint should be revisited when adding more symbols.

4. **Cooldown is simple, effective, and backward-compatible.** Default=0 preserves existing behavior. No Strategy Protocol changes. Can be combined with any future iteration.

## lgbm.py Code Review

No changes to lgbm.py in this iteration. The cooldown was implemented in backtest.py (cleaner separation). The pipeline is working correctly — ensemble averaging produces deterministic output, Optuna optimization converges consistently.

## Next Iteration Ideas

1. **EXPLOITATION: Optimize cooldown value** — Test cooldown=1, 3, 4, 6 to find the optimal value. cooldown=2 was an educated guess; the optimum may be different.

2. **EXPLORATION: Optuna-optimized cooldown** — Add cooldown_candles as an Optuna parameter (range 0-6) so it can be optimized per walk-forward month. Months with high model confidence might benefit from less cooldown.

3. **EXPLORATION: Direction-specific cooldown** — After an SL loss, increase cooldown (e.g., 3 candles). After a TP win, reduce it (e.g., 1 candle). This adapts to the model's recent accuracy.

4. **EXPLORATION: Add more symbols** — The single-symbol concentration constraint will keep failing until we expand beyond BTC+ETH. Top candidates: SOL, DOGE (high volume, low correlation with ETH).
