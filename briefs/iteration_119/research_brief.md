# Iteration 119 — Research Brief

**Type**: EXPLOITATION (portfolio combination, no model changes)
**Date**: 2026-04-02
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

IS data: before 2025-03-24. OOS data: >= 2025-03-24. The QR designed using IS data only.

## Objective

Combine the BTC/ETH baseline model (iter 093, OOS Sharpe +1.01) with the improved meme model (iter 118, OOS Sharpe +0.73) into a unified portfolio. Test whether the combined portfolio beats the baseline OOS Sharpe of +1.01.

## Rationale

Iter 115 attempted this with the iter 114 meme model (OOS Sharpe +0.29) and failed: combined OOS Sharpe +0.83, MaxDD 61.8% (exceeded 55.9% constraint). Since then:
- Iter 117: Feature pruning 67→45, meme OOS Sharpe +0.29 → +0.66
- Iter 118: Wider ATR barriers 3.5x/1.75x, meme OOS Sharpe +0.66 → +0.73

The meme model's OOS Sharpe has improved 2.5x since iter 115's failed attempt (+0.29 → +0.73). With higher meme Sharpe, the dilution effect should be smaller.

**Key math**: If BTC/ETH contributes Sharpe +1.01 on 107 trades and DOGE/SHIB contributes +0.73 on 81 trades, and trade PnL correlation between the two models is low (~0.1-0.3), the combined portfolio Sharpe should be between +0.85 and +1.05 depending on correlation structure.

## Architecture

Two independent LightGBM models running in parallel (same as iter 115):
- **Model A (BTC+ETH)**: Iter 093 baseline config — 185 features, auto-discovery, TP=8%/SL=4%, ATR execution 2.9x/1.45x, 24-month window, 5-seed ensemble
- **Model B (DOGE+SHIB)**: Iter 118 meme config — 45 pruned features, ATR labeling 3.5x/1.75x, 24-month window, 5-seed ensemble

Each model trades independently with $1000 per trade. Trades are concatenated and sorted by close_time for combined reporting.

## Single Variable Changed

| Parameter | Iter 118 | Iter 119 |
|-----------|----------|----------|
| Model scope | Meme only (DOGE+SHIB) | **Combined portfolio (BTC+ETH + DOGE+SHIB)** |

No model parameters changed. This is purely a portfolio combination test.

## Research Checklist

Categories completed:
- **E** (trade patterns): Analyzing combined trade patterns, cross-model correlation, concentration
- **B** (symbols): Portfolio-level diversification assessment
