# Iteration 137 Diary

**Date**: 2026-04-04
**Type**: EXPLOITATION (Model A ATR labeling)
**Model Track**: Model A (BTC+ETH pooled) — ATR labeling 2.9×/1.45×
**Decision**: **NO-MERGE** (Model A standalone test; portfolio validation needed)

## Results

| Metric | IS | OOS |
|--------|-----|-----|
| Sharpe | +1.14 | **+1.67** |
| WR | 45.1% | **48.6%** |
| PF | 1.33 | **1.60** |
| MaxDD | 49.2% | **19.8%** |
| Trades | 326 | 72 |
| Net PnL | +213.9% | +78.7% |

## Analysis

### ATR labeling transforms Model A

This is the biggest single-variable improvement in 137 iterations. One change — enabling ATR labeling on Model A — produced:
- IS Sharpe: +1.14 (was ~+0.59 for A in portfolio)
- OOS Sharpe: +1.67 (Model A alone nearly matches the 3-model portfolio!)
- ETH OOS WR: 55.9% (was 45.5% — **+10.4pp**)
- BTC OOS WR: 42.1% (was 38.5% — **+3.6pp**)
- OOS MaxDD: 19.8% (was ~80% at portfolio level)

### ETH was crippled by static labeling

The mechanism is clear. With static 4% SL and ETH NATR ~3.5%, the SL was only 1.14× NATR — essentially one candle of noise could trigger it. ATR labeling gives SL = 1.45×NATR ≈ 5.1% for ETH. The extra breathing room prevents noise-triggered stop-losses, boosting WR from 45.5% to 55.9%.

BTC's improvement is smaller (+3.6pp) because BTC's static barriers were already close to ATR-equivalent (static 8%/4% ≈ 3.2×/1.6× NATR vs ATR 2.9×/1.45×).

### Trade quality over quantity

72 OOS trades (down from 107) but much higher quality. TP rate 33.3% with effective RR 2.07:1. PF 1.60 is the highest we've seen for Model A.

### Gap quantification

Model A OOS: WR 48.6%, break-even 33.3% (2:1 TP/SL), gap **+15.3pp** above break-even. This is massive — the previous gap was ~7.8pp. ATR labeling nearly doubled the edge.

### Why this wasn't tried earlier

Model A has used execution ATR barriers since iter 093. But labeling remained static. The mismatch meant the model trained on labels with fixed 8%/4% barriers but executed with ATR-scaled barriers. Aligning them (same multipliers for both) is the obvious improvement in hindsight. LINK and BNB always had aligned labeling/execution — that's why they performed better.

## Label Leakage Audit

- CV gap = 44 (22 × 2 symbols). Verified.
- Walk-forward boundaries verified.

## Research Checklist

- **C (Labeling)**: ATR labeling vs static — ATR wins decisively for pooled BTC+ETH. ETH was the main beneficiary.
- **E (Trade Pattern)**: Exit reason analysis shows SL rate improved (48.8% IS vs 52.9% baseline IS). TP rate improved too. Effective RR 2.07:1.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, X, E, E, E, E, X, E, X, **X**] (iters 128-137)
Exploration rate: 4/10 = 40%

## Next Iteration Ideas

1. **A(ATR)+C+D portfolio run** (EXPLOITATION, MILESTONE) — Run the full portfolio with the new Model A (ATR labeling) + existing C (LINK) + D (BNB). Expected: OOS Sharpe > +1.94 baseline. This is the natural follow-up — if it beats baseline, MERGE immediately.

2. **Model C (LINK) with 2.9x/1.45x multipliers** (EXPLOITATION) — LINK currently uses 3.5x/1.75x. Would tighter 2.9x/1.45x work better? Or would it hurt? (Low priority — LINK already works well.)

3. **Feature pruning for new Model A** (EXPLOITATION) — New Model A has 196 features. With the improved signal, pruning could further sharpen it. Target 100-120 features.

4. **Cross-asset features** (EXPLORATION) — Add LINK/BNB return signals as features for Model A. Now that all models produce genuine signal, their predictions could be correlated features for each other.
