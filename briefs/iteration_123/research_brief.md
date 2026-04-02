# Iteration 123 — Research Brief

**Type**: EXPLORATION (new Model C: SOL standalone screening)
**Date**: 2026-04-02
**OOS cutoff**: 2025-03-24 (fixed, never changes)

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24
```

## Objective

Screen SOLUSDT as a standalone model (Model C candidate). Run the 5-gate qualification protocol. If SOL passes Gate 3 (standalone IS profitability), it becomes a candidate for portfolio addition.

**Per user feedback**: Single-model only. No combined portfolio run. Find new profitable models first.

## Gate Results (Pre-Backtest)

| Gate | Criterion | Result | Status |
|------|-----------|--------|--------|
| 1 — Data quality | ≥1095 IS candles, no gaps >3d | 4941 candles, max gap 3.3d | **PASS** (borderline gap) |
| 2 — Liquidity | Daily volume >$10M | $23.4M | **PASS** |
| 3 — Stand-alone IS profitability | IS Sharpe >0, WR >33.3%, ≥100 trades | **PENDING** | Backtest needed |
| 4 — Pooled compatibility | N/A until Gate 3 passes | — | — |
| 5 — Diversification value | N/A until Gate 3 passes | — | — |

## Architecture

- **Single model**: SOLUSDT only (1 symbol)
- **Config**: Same as BTC/ETH baseline — 24-month training, 5 CV folds, 50 Optuna trials
- **Labeling**: Static TP=8%/SL=4%, 7-day timeout (same as BTC/ETH)
- **Features**: Auto-discovery from SOL parquet (~185 features)
- **Ensemble**: 5 seeds [42, 123, 456, 789, 1001]
- **Signal cooldown**: 2 candles
- **No ATR labeling** (static barriers, like BTC/ETH — SOL NATR ~5-8% is higher than BTC but TP=8% is still reachable)

## Why SOL?

- Highest volume L1 alt after BTC/ETH
- Sufficient IS data (4941 candles, from Sep 2020)
- Different market dynamics: higher volatility (NATR ~5-8% vs BTC ~3%), more retail-driven, ecosystem-specific catalysts
- Past failures (iter 071) were due to naive pooling with BTC+ETH, NOT standalone testing

## Risk

- SOL NATR ~5-8% is 2x BTC. Fixed TP=8%/SL=4% may be too tight — timeout rate could be high
- With 1 symbol, training samples are ~2,200/year. With 185 features, ratio is ~12 (very low). colsample_bytree will handle implicit pruning
- If IS Sharpe ≤ 0: STOP, do not proceed to Gate 4. Try next candidate (AVAX, LINK, etc.)

## Research Checklist

- **B** (symbols): Gate 1-3 screening for SOL
- **A** (features): Auto-discovery on SOL-only parquet
