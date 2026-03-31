# Iteration 098 Diary — 2026-03-31

## Merge Decision: NO-MERGE (EARLY STOP)

**Trigger**: Year 2022 PnL=-109.6%, WR=31.0%. IS Sharpe -1.44.

**OOS cutoff**: 2025-03-24

## Hypothesis

Time decay weighting (half-life=12mo) preserves |PnL| signal while adding recency bias.

## What Failed

Time decay catastrophically failed because it **undermines the 24-month training window design**. The window intentionally spans bull + bear cycles. By down-weighting old samples (0.25×), time decay effectively reduces the high-weight window to ~12 months — losing regime diversity.

First prediction year 2022 was a bear market. The model, heavily weighted toward late-2021 bull patterns, got destroyed.

## Key Insight: The Training Window IS the Recency Mechanism

The 24-month rolling window already handles recency: old data naturally drops out as the window slides. Adding time decay within the window creates a double penalty on old data that destroys the balance between bull/bear regimes.

## Exploration/Exploitation Tracker

Last 10 (iters 089-098): [E, E, E, X, E, X, E, X, E, **E**]
Exploration rate: 7/10 = 70%
Type: **EXPLORATION** (time decay weighting)

## Lessons Learned

1. **Don't add time decay within a rolling window.** The window itself is the recency mechanism.
2. **Weight modifications are extremely dangerous.** Both uniqueness (iter 097) and time decay (iter 098) destroyed OOS. The baseline's simple |PnL| weighting works — don't touch it.
3. **Regime balance matters more than recency.** The model needs both bull and bear examples at equal weight to generalize.

## Next Iteration Ideas

After 6 consecutive NO-MERGE (093-098 excluding 093 MERGE), must propose structural changes only.

1. **EXPLORATION: Per-symbol models with honest CV.** The one structural change that hasn't been tried with the iter 093 baseline config. BTC 33.3% WR vs ETH 50.0% OOS — fundamentally different dynamics.

2. **EXPLORATION: Wider confidence threshold range.** Current Optuna range [0.50, 0.85]. The model might benefit from narrower — [0.60, 0.80] — or the threshold mechanism itself could be changed.

3. **EXPLORATION: Regime-conditional prediction.** Don't trade in low-ADX environments. Add a hard filter: if BTC ADX_14 < 15, don't predict. This removes choppy-market trades that the model consistently loses.
