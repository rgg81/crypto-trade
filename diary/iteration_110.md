# Iteration 110 Diary

**Date**: 2026-04-01
**Type**: EXPLORATION
**Merge Decision**: NO-MERGE (EARLY STOP — Year 2023: PnL=-64.9%, WR=34.5%, 55 trades)

**OOS cutoff**: 2025-03-24

## Results

| Metric | Iter 110 (NATR filter) | Iter 108 (no filter) |
|--------|----------------------|---------------------|
| IS Sharpe | +0.064 | +0.10 |
| IS WR | 40.5% | 38.6% |
| IS PF | 1.02 | 1.03 |
| IS MaxDD | 91.6% | 108.6% |
| IS Trades | 84 | 114 |
| Early Stop | 2023: -64.9% | 2023: -69.7% |

The NATR filter reduced trades by 26% (114→84) and slightly improved 2023 PnL (-64.9% vs -69.7%), but the improvement was marginal (~5pp). Still early-stopped.

## Critical Finding: NATR Filter Is Redundant

0 signals were NATR-filtered across the entire backtest. The confidence threshold (0.65-0.85) already filters low-vol candles — high-confidence predictions naturally occur during high-vol periods. The NATR gate adds nothing.

The 30-trade reduction (114→84) came from different Optuna optimization paths (same training data, different random seeds → slightly different models → fewer total signals). NOT from the NATR filter itself.

## 2023 Problem: Not a Regime Problem, But a Prediction Quality Problem

The deep analysis revealed:
- **Feb 2023**: 11/13 SL at NATR=3.63% (not low-vol) → model was simply WRONG
- **Dec 2023**: 8/12 SL at NATR=3.79% (not low-vol) → same issue
- The losing months aren't characterized by low NATR. They're characterized by the model making bad predictions in moderately-volatile, choppy, range-bound markets.
- A regime filter can't fix bad predictions. The model needs to learn "when I'm uncertain, don't trade" — which is what the confidence threshold already does.

## Conclusion: Meme Coin Model Cannot Profitably Navigate 2023

After 3 iterations (108, 109, 110) on meme coins:
1. The only IS profit comes from crash shorting (Nov 2022 FTX)
2. 2023 is structurally unprofitable for this approach
3. Neither per-symbol, nor regime filtering, nor feature curation can fix 2023
4. The model generates IS Sharpe ~0.1 but with catastrophic MaxDD (90-109%)

## Exploration/Exploitation Tracker

Last 10 (iters 101-110): [X, E, E, E, E, E, E, E, X, **E**]
Exploration rate: 8/10 = 80%. Type: EXPLORATION (regime filter).

## Next Iteration Ideas

The meme coin track has reached a dead end with this LightGBM approach. Three options:

1. **ACCEPT the meme model as crash-only and deploy it with position limits.** The model profits during crashes. Run it live but with 10% of capital — it's a "tail hedge" strategy, not a core strategy.

2. **EXPLORATION: Totally different approach for meme coins.** Instead of LightGBM on 8h candles, try:
   - Shorter timeframe (1h or 15m) for meme coins
   - Volume spike event-driven trading (only trade on 3x volume events)
   - Simple rule-based strategy (no ML) — e.g., "short when RSI > 80 and NATR > 6%"

3. **Return to BTC+ETH baseline.** The meme coin exploration provided diversification insights but the IS Sharpe is marginal. Apply the dynamic ATR labeling and feature pruning (42 features) to the BTC+ETH baseline instead.
