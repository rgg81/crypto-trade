# Iteration 133 Diary

**Date**: 2026-04-03
**Type**: EXPLORATION (Model D/E screening: DOT standalone)
**Model Track**: DOT standalone (iter 126 config template)
**Decision**: **NO-MERGE** — IS Sharpe -0.02 (flat). DOT fails Model D screening.

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | **-0.02** | +1.10 |
| WR | 42.5% | 44.7% |
| PF | 0.99 | 1.41 |
| MaxDD | 148.2% | 42.0% |
| Trades | 113 | 47 |
| Net PnL | -2.5% | +59.0% |

## Analysis

### DOT has no IS signal — same pattern as XRP

IS Sharpe -0.02 and IS PF 0.99 over 113 trades is essentially break-even. The OOS +1.10 with 47 trades is statistically unreliable given zero IS profitability. This is the same pattern as XRP (iter 131, IS -0.03) — the model cannot learn predictive patterns for these symbols.

### Screening campaign complete — final scorecard

| Symbol | IS Sharpe | OOS Sharpe | IS Trades | OOS Trades | Verdict |
|--------|-----------|------------|-----------|------------|---------|
| **LINK** (iter 126) | **+0.45** | **+1.20** | 224 | 42 | **PASS** |
| **BNB** (iter 132) | **+0.51** | **+1.04** | 143 | 50 | **PASS** |
| ADA (iter 130) | -0.73 | +0.31 | 186 | 47 | FAIL |
| XRP (iter 131) | -0.03 | +2.03 | 169 | 22 | FAIL |
| DOT (iter 133) | -0.02 | +1.10 | 113 | 47 | FAIL |

**2 out of 5 candidates pass**: LINK and BNB. The iter 126 config template (ATR 3.5x/1.75x, 185 auto-discovery) works for exchange-native (BNB) and oracle/DeFi infrastructure (LINK) symbols, but fails for general-purpose L1 alts (ADA, DOT) and payment tokens (XRP).

### Pattern: IS-flat symbols share OOS noise

ADA, XRP, and DOT all show negative or flat IS with positive OOS. This is the hallmark of models that learn nothing — the OOS results are random walks that happened to trend up during the 11-month OOS period. Only LINK and BNB show positive IS AND OOS, indicating real signal.

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, X, X, X, X, E, E, E, **E**] (iters 124-133)
Exploration rate: 6/10 = 60%

## Next Iteration Ideas

1. **A+C+D portfolio: BTC/ETH + LINK + BNB** (EXPLOITATION, combined run) — Combine the 3 qualified models: Model A (BTC/ETH), Model C (LINK), Model D (BNB). Expected ~199 OOS trades (107 A + 42 C + 50 D). Target: beat baseline OOS Sharpe +1.68. This is the milestone portfolio test with 5 symbols.

2. **Model E: SOL with iter 126 template** (EXPLORATION, single-model) — SOL is the highest-volume alt not tested with this config. Previous attempts (iter 123-124) used different configs.

3. **Model E: ATOM standalone** (EXPLORATION, single-model) — Cosmos/IBC ecosystem. Data since Feb 2020. Different from all tested symbols.
