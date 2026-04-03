# Iteration 131 Diary

**Date**: 2026-04-03
**Type**: EXPLORATION (Model D screening: XRP standalone)
**Model Track**: XRP standalone (iter 126 config template)
**Decision**: **NO-MERGE** — IS Sharpe -0.03 (flat), only 22 OOS trades. XRP fails Model D screening.

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | **-0.03** | +2.03 |
| WR | 46.7% | 59.1% |
| PF | 0.99 | 2.52 |
| MaxDD | 116.0% | 12.3% |
| Trades | 169 | **22** |
| Net PnL | -4.8% | +69.4% |

## Analysis

### XRP has no IS signal

IS Sharpe -0.03 and IS PF 0.99 over 169 trades means the model is essentially flipping coins on XRP for 3 years. Unlike ADA (iter 130) which actively lost money (IS -149%), XRP breaks even — the model isn't catastrophically wrong, it just has no edge.

### OOS is statistical noise

22 OOS trades with 59.1% WR (13 wins / 22 trades). Binomial test: P(≥13 | n=22, p=0.5) ≈ 0.28. Not statistically significant. The OOS Sharpe +2.03 is meaningless with this sample size.

### Why XRP doesn't work

1. **Too few trades**: 169 IS trades over 3 years = ~4.7/month. The ATR-based barriers (3.5x/1.75x) are very wide for XRP, making the model extremely selective. But selectivity without IS profitability is just noise.
2. **XRP's catalysts are idiosyncratic**: XRP moves on legal rulings, partnership announcements, and regulatory news — events that technical features cannot predict. The 185 auto-discovered features capture price/volume patterns, not legal outcomes.
3. **IS WR 46.7% with ATR barriers**: The break-even WR for 2:1 RR is ~33%, so 46.7% should be profitable. But the dynamic ATR barriers mean actual RR varies — some trades have RR closer to 1:1, dragging PF to 0.99.

### Model D screening scorecard (3 candidates tested)

| Symbol | IS Sharpe | OOS Sharpe | IS Trades | OOS Trades | Verdict |
|--------|-----------|------------|-----------|------------|---------|
| **LINK** (iter 126) | **+0.45** | **+1.20** | 224 | 42 | **PASS** |
| ADA (iter 130) | -0.73 | +0.31 | 186 | 47 | FAIL |
| XRP (iter 131) | -0.03 | +2.03 | 169 | 22 | FAIL |

LINK remains the only alt that passed screening. Two consecutive failures (ADA, XRP) suggest the iter 126 config template doesn't universally work — LINK's success may be specific to LINK's market structure.

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, E, E, E, X, X, X, X, E, **E**] (iters 122-131)
Exploration rate: 6/10 = 60%

## Next Iteration Ideas

1. **Model D: BNB standalone** (EXPLORATION, single-model) — BNB is exchange-native with unique dynamics (burn mechanism, Binance ecosystem fees). Unlike ADA/XRP, BNB has structural demand from exchange usage that could create predictable patterns. Data since Feb 2020.

2. **Model D: DOT standalone** (EXPLORATION, single-model) — DOT (Polkadot) with parachain auction cycles that create predictable demand patterns. Data since Aug 2020.

3. **Model D: SOL with iter 126 template** (EXPLORATION, single-model) — SOL failed in iter 123-124 with different configs. The iter 126 template (ATR 3.5x/1.75x, 185 features) hasn't been tested on SOL yet.

4. **Stop screening, improve existing models** (EXPLOITATION) — After 3 failed screenings (ADA, XRP, and SOL/AVAX from earlier), consider that LINK may be the only viable Model C candidate. Focus on improving Model A (BTC/ETH) or Model C (LINK) performance instead of finding Model D.
