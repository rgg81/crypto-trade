# Iteration 135 Diary

**Date**: 2026-04-04
**Type**: EXPLORATION (Model E screening: SOL standalone)
**Model Track**: SOL standalone (iter 126 config template)
**Decision**: **NO-MERGE** (screening) — SOL marginally passes gates but signal too weak for portfolio. IS +0.16, 32 OOS trades.

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | +0.16 | +0.47 |
| WR | 42.6% | 46.9% |
| PF | 1.05 | 1.19 |
| MaxDD | 124.1% | 31.4% |
| Trades | 141 | 32 |
| Net PnL | +20.1% | +15.1% |

## Analysis

### SOL: marginal signal, not portfolio-ready

SOL technically passes all 5 screening gates but is the weakest candidate to do so. IS Sharpe +0.16 is barely above zero — the model ekes out a tiny profit over 3 years of IS trading. Compare:
- LINK: IS +0.45, OOS +1.20, 42 OOS trades
- BNB: IS +0.51, OOS +1.04, 50 OOS trades
- SOL: IS +0.16, OOS +0.47, 32 OOS trades

SOL's signal is ~3x weaker than LINK/BNB in IS. Adding it to the portfolio would contribute only +15.1% OOS PnL from 32 trades — marginal compared to BNB's +37.7% from 50 trades.

### 32 OOS trades below portfolio minimum

The hard constraint requires ≥50 OOS trades for portfolio merge. SOL's 32 doesn't meet this. While the standalone screening gate (≥20) passes, the portfolio gate would fail.

### Final screening scorecard (6 candidates)

| Symbol | IS Sharpe | OOS Sharpe | OOS Trades | Verdict |
|--------|-----------|------------|------------|---------|
| **LINK** | **+0.45** | **+1.20** | 42 | **STRONG PASS** |
| **BNB** | **+0.51** | **+1.04** | 50 | **STRONG PASS** |
| SOL | +0.16 | +0.47 | 32 | MARGINAL PASS |
| ADA | -0.73 | +0.31 | 47 | FAIL |
| XRP | -0.03 | +2.03 | 22 | FAIL |
| DOT | -0.02 | +1.10 | 47 | FAIL |

LINK and BNB remain the only strong candidates. SOL is a distant third.

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, X, X, E, E, E, E, X, **E**] (iters 126-135)
Exploration rate: 7/10 = 70%

## Next Iteration Ideas

1. **Improve Model A (BTC) IS performance** (EXPLOITATION, single-model) — BTC contributes only 10.3% of OOS PnL with 38.5% WR. Could BTC benefit from ATR labeling like the alts? Test BTC standalone with ATR 3.5x/1.75x config.

2. **Portfolio weighting optimization** (EXPLOITATION, combined run) — Instead of equal weight, use Sharpe-weighted allocation. LINK and BNB have higher standalone Sharpe than BTC — they could get 1.5x weight while BTC gets 0.5x.

3. **Model E: ATOM standalone** (EXPLORATION, single-model) — Cosmos/IBC ecosystem. Different from all tested symbols. Data since Feb 2020.

4. **Feature engineering for alt models** (EXPLORATION, single-model) — Add xbtc_* cross-asset features to LINK or BNB parquets. BTC often leads alts by 1 candle — this could improve alt model IS performance.
