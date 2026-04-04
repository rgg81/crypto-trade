# Iteration 137 Research Brief

**Type**: EXPLOITATION (Model A with ATR labeling)
**Model Track**: Model A (BTC+ETH pooled) — enable ATR labeling
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    (FIXED. NEVER CHANGES.)
```

## Motivation

Model A (BTC+ETH pooled) uses **static labeling** (TP=8%, SL=4%) while Models C (LINK) and D (BNB) use **ATR labeling** (3.5×NATR/1.75×NATR). The alt models have significantly better performance:

| Model | Labeling | OOS WR | OOS PnL |
|-------|----------|--------|---------|
| A (BTC) | Static 8%/4% | 38.5% | +16.8% |
| A (ETH) | Static 8%/4% | 45.5% | +52.1% |
| C (LINK) | ATR 3.5x/1.75x | 52.4% | +56.0% |
| D (BNB) | ATR 3.5x/1.75x | 52.0% | +37.7% |

**Hypothesis**: ATR labeling adapts barriers to each symbol's current volatility regime. During low-vol periods, static 8% TP may be unreachable for BTC; during high-vol periods, static 4% SL may be too tight for ETH. ATR labeling would dynamically adjust both, improving label quality and model signal.

**Iter 136 lesson**: BTC standalone with ATR 3.5x/1.75x fails (IS -0.90). But this was because BTC lacks standalone signal, NOT because ATR labeling is wrong. The pooled BTC+ETH model has proven IS signal (IS WR 42.5% in baseline). The question is whether ATR labeling improves that pooled signal.

**Multiplier choice**: Model A already uses ATR execution barriers at 2.9x/1.45x. Aligning labeling with execution (2.9x/1.45x) ensures the model trains on labels that match how trades are actually executed. This is the same principle that makes LINK/BNB work (labeling = execution = 3.5x/1.75x).

## Research Checklist Categories

### C. Labeling Analysis

Comparing static vs ATR labeling for pooled BTC+ETH:
- **Static (current)**: TP=8%, SL=4% for all candles regardless of volatility
  - BTC NATR ~2.5%: effective RR = 3.2x NATR / 1.6x NATR
  - ETH NATR ~3.5%: effective RR = 2.3x NATR / 1.1x NATR
  - Problem: ETH's SL is very tight (1.1× NATR) — easily hit by noise
- **ATR 2.9x/1.45x (proposed)**: TP = 2.9×NATR, SL = 1.45×NATR
  - BTC: TP ≈ 7.25%, SL ≈ 3.625% (slightly tighter than static)
  - ETH: TP ≈ 10.15%, SL ≈ 5.075% (wider than static — less noise)
  - Benefit: ETH gets wider barriers matching its higher volatility

### E. Trade Pattern Analysis

From iter 134 portfolio, Model A's exit breakdown:
- BTC OOS: 38.5% WR, 10.3% PnL contribution
- ETH OOS: 45.5% WR, 32.0% PnL contribution
- ETH is clearly the stronger component — ATR labeling should help ETH more by widening its effective barriers

## Configuration

| Parameter | Baseline (iter 134 Model A) | Iter 137 |
|-----------|----------------------------|----------|
| Symbols | BTCUSDT + ETHUSDT | Same |
| Labeling | Static TP=8%, SL=4% | **ATR: TP=2.9×NATR, SL=1.45×NATR** |
| Execution | ATR: TP=2.9×NATR, SL=1.45×NATR | Same |
| use_atr_labeling | False | **True** |
| Training months | 24 | Same |
| Timeout | 7 days | Same |
| Features | Auto-discovery | Same |
| Ensemble | 5 seeds | Same |
| CV | 5 folds, 50 Optuna trials | Same |
| CV gap | 44 (22 × 2 symbols) | Same |
| Cooldown | 2 | Same |

**Single variable changed**: `use_atr_labeling` False → True (with existing 2.9x/1.45x multipliers).

## Success Criteria

This is a Model A improvement test. Success = Model A metrics improve. If Model A improves, we run the full A+C+D portfolio as a follow-up to check baseline beat.

| Metric | Current Model A | Target |
|--------|----------------|--------|
| IS PnL | +32.5% (BTC+ETH) | > +32.5% |
| OOS WR | 41.1% (combined) | > 41.1% |
| OOS PnL | +68.9% (BTC+ETH) | > +68.9% |
