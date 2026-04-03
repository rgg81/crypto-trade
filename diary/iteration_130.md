# Iteration 130 Diary

**Date**: 2026-04-03
**Type**: EXPLORATION (Model D screening: ADA standalone)
**Model Track**: ADA standalone (iter 126 config template)
**Decision**: **NO-MERGE** — IS Sharpe -0.73, ADA fails Model D screening.

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | **-0.73** | +0.31 |
| WR | 36.0% | 48.9% |
| PF | 0.79 | 1.10 |
| MaxDD | 166.8% | 41.3% |
| Trades | 186 | 47 |
| Net PnL | **-149.1%** | +15.3% |

## Analysis

### ADA has no signal with this config

IS Sharpe -0.73 and IS Net PnL -149% over 3 years of in-sample trading is catastrophic. The model consistently loses money on ADA throughout the IS period. The marginally positive OOS (+15.3% from 47 trades) is statistical noise — with only 47 trades and negative IS, there's no reason to believe the OOS result is real.

### Why ADA fails where LINK succeeds

LINK (iter 126) showed IS Sharpe +0.45 and OOS +1.20. ADA shows IS -0.73. The difference is likely:
1. **ADA's price dynamics are too smooth.** ADA has lower volatility and fewer sharp moves compared to LINK. The ATR-based barriers may be too tight for ADA's price structure.
2. **ADA may have different feature requirements.** The 185 auto-discovered features work for BTC/ETH and LINK but may not capture ADA-specific patterns.
3. **ADA's market microstructure** is different — it's driven more by Cardano-specific catalysts (hard forks, staking events) that aren't captured by technical features.

### Model D screening scorecard

| Gate | Threshold | ADA | Pass? |
|------|-----------|-----|-------|
| IS Sharpe > 0 | > 0 | -0.73 | **FAIL** |
| OOS Sharpe > 0 | > 0 | +0.31 | PASS (noise) |
| OOS WR > 33% | > 33% | 48.9% | PASS |
| OOS Trades ≥ 20 | ≥ 20 | 47 | PASS |

ADA fails the first and most important gate. No further analysis needed.

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, E, E, E, X, X, X, X, **E**] (iters 121-130)
Exploration rate: 5/10 = 50%

## Next Iteration Ideas

1. **Model D: XRP standalone** (EXPLORATION, single-model) — XRP has fundamentally different price drivers (payment rails, regulatory catalysts, Ripple partnerships). Data since Jan 2020. Use iter 126 config template. XRP's regulatory-driven volatility may produce different signal patterns.

2. **Model D: DOT standalone** (EXPLORATION, single-model) — DOT (Polkadot) is an interoperability-focused L1 with different market dynamics. Data since Aug 2020.

3. **Model D: BNB standalone** (EXPLORATION, single-model) — BNB is exchange-native with unique dynamics (burn mechanism, Binance ecosystem). Data since Feb 2020. Less correlated with general alt market.

4. **Model D: SOL with adjusted barriers** (EXPLORATION, single-model) — SOL failed in iter 123-124 but with different configs. Re-try with iter 126 template (ATR 3.5x/1.75x, 185 auto-discovery). SOL has higher vol than ADA — may respond better to ATR barriers.
