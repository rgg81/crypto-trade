# Iteration 157 Diary

**Date**: 2026-04-08
**Type**: EXPLORATION (rule-based meta-filter, no ML)
**Decision**: **NO-MERGE** — IS-best rule (G) fails OOS Sharpe

## Key Findings

### IS Bucket Analysis

Clear patterns in iter 138's IS trades (652 total):

1. **Direction bias**: LONG WR 48.3%, SHORT WR 40.2% (8pp gap).
2. **Symbol × Direction**: BTC/BNB/LINK SHORTs all WR < 41% with negative
   mean PnL. Only ETH SHORT is break-even.
3. **ADX Q3 zone** (19.6 < ADX ≤ 34.6): WR 39.9%, mean -0.44%. The
   "mid-trend" false-signal zone.
4. **Hour-of-day**: hour=23 UTC is worst (WR 43.1%, mean -0.13%).

### Rule Grid Results

| Rule | IS Sharpe | OOS Sharpe | ΔOOS vs baseline |
|------|-----------|-----------|------------------|
| baseline | +1.33 | +2.83 | — |
| D_adx_q3 | +1.70 | **+2.95** | **+4.2%** |
| F_weak_bucket | +1.77 | **+2.92** | **+3.3%** |
| G_hour23_adx_q3 [IS-best] | +1.83 | +2.60 | -8.1% |

Every rule improves OOS MaxDD (from 21.81% baseline down to 10-20%).

### The IS-Best Pathology

The IS-best rule (G, drops 84% of trades) has the highest IS Sharpe but
FAILS OOS. Less aggressive rules (D, F) beat baseline OOS but weren't
IS-best.

**Reason**: Aggressive filtering inflates IS Sharpe by dropping trade
count — fewer trades → higher variance per kept trade → apparently higher
Sharpe. But this IS-Sharpe inflation doesn't translate to OOS.

**t-stat-adjusted** (Sharpe × sqrt(n)) would pick F:
- F: 1.77 × sqrt(505) = **39.8** ⭐
- baseline: 1.33 × sqrt(652) = 33.9
- D: 1.70 × sqrt(326) = 30.7
- G: 1.83 × sqrt(211) = 26.6

## Hard Constraints (IS-best G)

| Check | Threshold | Actual | Pass |
|-------|-----------|--------|------|
| OOS Sharpe > baseline | > +2.83 | +2.60 | **FAIL** |
| OOS trades ≥ 50 | ≥ 50 | 59 | ✓ |
| OOS MaxDD ≤ 38.7% | ≤ 38.7% | 13.31% | ✓ |
| OOS PF > 1.0 | > 1.0 | 2.72 | ✓ |
| Concentration ≤ 50% | ≤ 50% | ETH 33% | ✓ |
| IS/OOS ratio > 0.5 | > 0.5 | 0.71 | ✓ |

## Research Checklist

- **E (Trade Pattern)**: Deep IS bucket analysis (direction, symbol ×
  direction, hour, ADX, NATR, BTC NATR). Identified LONG bias and SHORT
  weakness per symbol.
- **F (Statistical Rigor)**: WR per bucket with n per group. BTC/BNB/LINK
  SHORTs each below break-even with n=69-77 — statistically meaningful
  patterns.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, X, X, X, X, X, E, E, **E**] (iters 148-157)
Exploration rate: 4/10 = 40% ✓

## Next Iteration Ideas

### 1. Iteration 158: IS-selection with t-stat adjustment (EXPLOITATION)

The IS-best selection rule is the problem, not rule-based filtering.
Retest iter 157 rules with **Sharpe × sqrt(n)** as selection metric. If
F wins and OOS Sharpe > baseline, that's a legitimate MERGE candidate.

**Rule**: IS-select by argmax(IS_Sharpe × sqrt(IS_trade_count)). This is a
standard t-stat analog — penalizes aggressive filters that inflate Sharpe
via variance reduction.

### 2. Drop NO rule, keep ONLY symbol × direction asymmetry

A simpler, more principled variant: **short-sell only ETH, long all 4
symbols**. Matches the IS finding that ETH-SHORT is the only viable short.
Keeps 560 IS trades (drops 92 BTC+BNB+LINK SHORTs).

### 3. Apply rules to primary model output, not post-hoc

Instead of filtering iter 138's trades, REFIT the primary LightGBM with
`{symbol} × (direction == -1)` as a hard constraint feature. Not
post-processing — changes the model's learned distribution. Needs
retraining.

### 4. Paper trading with v0.152

After 5 unsuccessful exploration iterations (152 exhausted parameters;
153, 155 parameter space confirmed; 156 ML meta-label failed; 157 rule
meta-label IS-best fails), the production-ready path is v0.152
deployment. Further research should be CONCURRENT with paper trading,
not blocking it.

## Notes

- NO-MERGE is correct under the stated IS-best rule.
- D_adx_q3 and F_weak_bucket are genuine candidates under a t-stat-adjusted
  selection rule — this is what iter 158 should formalize.
- The core insight is real: **mid-range ADX and late-UTC hours are
  genuinely weak** — this pattern holds IS and OOS. A more principled
  selection metric may unlock the signal.
