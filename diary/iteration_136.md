# Iteration 136 Diary

**Date**: 2026-04-04
**Type**: EXPLOITATION (BTC standalone screening with ATR labeling)
**Model Track**: BTC standalone — testing LINK/BNB template on BTC
**Decision**: **NO-MERGE** (screening fail) — BTC fails Gate 3, IS Sharpe -0.90. ATR 3.5x/1.75x too wide for BTC.

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | -0.90 | -1.41 |
| WR | 40.6% | 32.0% |
| PF | 0.75 | 0.65 |
| MaxDD | 140.5% | 46.7% |
| Trades | 170 | 50 |
| Net PnL | -109.3% | -36.4% |

## Analysis

### BTC standalone fails with LINK/BNB ATR template

The 3.5×NATR/1.75×NATR barrier multipliers that work for LINK (IS +0.45) and BNB (IS +0.51) produce deeply negative results for BTC (IS -0.90). This is a clear signal that BTC's dynamics are fundamentally different from the alts.

**SL rate is catastrophic**: 52.9% IS, 64.0% OOS. More than half of all trades are stopped out. The model generates signals but can't protect them — the ATR-scaled stop-losses are too tight relative to BTC's intra-day noise, or the directional calls are simply wrong.

### OOS direction disaster

The model went 64% short during the OOS period (Mar 2025 - present), precisely when BTC rallied from ~$80K to ~$120K. This isn't just weak signal — it's actively wrong on BTC's trend.

Compare with BTC inside Model A: pooled with ETH, Model A's BTC also has a moderate OOS WR (38.5%), but it manages +16.8% net PnL because the trade selection is better (fewer bad short calls).

### Why BTC standalone doesn't work

1. **Insufficient standalone signal**: BTC is the most efficient crypto market. Its price moves are harder to predict than alts. LINK/BNB have more exploitable patterns (wider spreads, less institutional coverage, more retail-driven).

2. **ATR barriers interact badly with BTC**: BTC's NATR has been declining (4-5% in 2022, 2-2.5% in 2025). ATR×3.5 gives ~8.75% TP in 2025 — similar to static 8%. But ATR×1.75 gives ~4.375% SL — also similar to static 4%. So ATR labeling isn't the differentiator; the standalone model itself lacks signal.

3. **BTC benefits from pooling with ETH**: Model A's BTC gets ETH's training data too, increasing the sample count from ~2,200 to ~4,400. The extra data helps regularization and the pooled model learns shared crypto patterns that don't exist in BTC alone.

### Screening scorecard updated

| Symbol | IS Sharpe | OOS Sharpe | OOS Trades | Config | Verdict |
|--------|-----------|------------|------------|--------|---------|
| **LINK** | **+0.45** | **+1.20** | 42 | ATR 3.5x/1.75x | **STRONG PASS** |
| **BNB** | **+0.51** | **+1.04** | 50 | ATR 3.5x/1.75x | **STRONG PASS** |
| SOL | +0.16 | +0.47 | 32 | ATR 3.5x/1.75x | MARGINAL |
| ADA | -0.73 | +0.31 | 47 | ATR 3.5x/1.75x | FAIL |
| XRP | -0.03 | +2.03 | 22 | ATR 3.5x/1.75x | FAIL |
| DOT | -0.02 | +1.10 | 47 | ATR 3.5x/1.75x | FAIL |
| **BTC** | **-0.90** | **-1.41** | **50** | ATR 3.5x/1.75x | **FAIL** |

BTC is the worst standalone performer of all 7 screened symbols. This definitively answers the question: BTC cannot be profitably modeled standalone with the current pipeline.

### Gap quantification

BTC standalone: WR 40.6% IS, break-even 33.3% (2:1 TP/SL), gap +7.3pp above break-even. But PF=0.75 means the average loss exceeds the average win by enough to be net negative despite WR > break-even. The problem is asymmetric returns: avg SL loss -4.67% is much larger than avg TP gain +7.66% would suggest, because the 2:1 nominal ratio only holds for clean TP/SL exits — timeouts and partial exits dilute the effective RR.

## Label Leakage Audit

- CV gap = 22 (22 × 1 symbol). Verified correct.
- Walk-forward boundaries verified.

## Research Checklist

- **B (Symbol/Architecture)**: Tested BTC standalone. Result: BTC cannot be modeled standalone. Must stay pooled with ETH in Model A.
- **E (Trade Pattern)**: SL rate 53-64% is the primary failure mode. Direction calls wrong in OOS (64% short during bull market).

## Exploration/Exploitation Tracker

Last 10 iterations: [X, X, X, E, E, E, E, X, E, **X**] (iters 127-136)
Exploration rate: 5/10 = 50%

## Next Iteration Ideas

1. **Model A with ATR labeling (pooled BTC+ETH)** (EXPLOITATION) — Don't separate BTC. Instead, enable ATR labeling on the existing pooled Model A with 2.9x/1.45x multipliers (matching current execution barriers). This preserves the pooled training data advantage while testing whether ATR labeling improves Model A's overall signal.

2. **Remove BTC from portfolio entirely** (EXPLORATION) — Radical idea: ETH+LINK+BNB portfolio WITHOUT BTC. BTC contributes only 10.3% of OOS PnL and drags down portfolio WR. Test whether removing it improves Sharpe despite losing trade count.

3. **Cross-asset features for Model A** (EXPLORATION) — Add LINK and BNB return/volatility as features for Model A. Now that we have confirmed alt model performance, their signals could inform BTC+ETH predictions. `xlink_return_1`, `xbnb_natr_14` as new features.

4. **Feature pruning for Model A** (EXPLOITATION) — Model A has 196 features. The alt models also have ~185-196 features but only ~2,200 training samples per symbol, giving low samples/feature ratio. Run A1 feature pruning to reduce to 80-100 features.
