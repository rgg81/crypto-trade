# Iteration 145 Diary

**Date**: 2026-04-05
**Type**: EXPLORATION (vol-targeted position sizing)
**Model Track**: A+C+D with dynamic position sizing
**Decision**: **MERGE** — OOS Sharpe +2.33 beats baseline +2.32, OOS MaxDD drops 39% (62.8% → 38.1%)

## Results vs Baseline

| Metric | Iter 138 (baseline) | Iter 145 (vol-targeted) | Change |
|--------|---------------------|--------------------------|--------|
| OOS Sharpe | +2.32 | **+2.33** | **+0.4%** |
| OOS Sortino | +3.41 | +3.01 | -12% |
| OOS WR | 50.6% | 50.6% | same |
| OOS PF | 1.49 | **1.53** | +3% |
| **OOS MaxDD** | **62.8%** | **38.1%** | **-39%** |
| **OOS Calmar** | **2.74** | **3.40** | **+24%** |
| OOS Net PnL | +172.4% | +129.5% | -25% |
| IS Sharpe | +1.15 | **+1.36** | +18% |

## Analysis

### Vol targeting preserves Sharpe while crushing MaxDD

Applying inverse-volatility position sizing (scale = 1.5 / realized_14d_vol, clipped
to [0.5, 2.0]) to the iter 138 portfolio produced:
- **Sharpe**: marginal improvement (+0.01)
- **MaxDD**: 39% reduction (62.8% → 38.1%)
- **Calmar**: 24% improvement
- **PnL**: 25% lower (smaller average position)

The strategy trades the same signals at varying sizes. During high-vol periods
(e.g., July 2025 crash), position sizes drop to ~0.5x. During calm periods, sizes
can reach 2.0x.

### Walk-forward validation

Parameters were tuned on **IS data only** (24 configs tested). The IS-best config
(target=1.5, lookback=14) was then applied to OOS trades without further tuning.
This is honest walk-forward: no OOS information leaked into parameter selection.

### IS Sharpe also improved

IS Sharpe: +1.15 → +1.36 (+18%). The vol-targeting rule helps on both IS and OOS,
confirming it's not OOS-specific. It generalizes.

### Concentration shift (BNB → top position)

Portfolio concentration shifted from LINK (34.4% baseline) to BNB (36.6% iter 145).
Why: BNB's trades happened during lower-vol periods on average, keeping their scales
higher. LINK's trades were more often scaled down.

This still passes the ≤50% concentration constraint but worsens marginally vs iter 138.

### The avg scale is 0.65

Portfolio trades at 65% of nominal size on average during OOS. This is a significant
deleveraging — the system recognizes elevated vol regimes through OOS and scales back.

### Why this works

The trade signals from LightGBM are unchanged. The win rate is unchanged (50.6%).
What changes: when the market is volatile (high realized vol), scale down to avoid
amplifying losses. When the market is calm, scale normally.

**Classical risk management, applied as post-processing**: no re-training, no new
features, no new models.

## Gap Quantification

- OOS WR 50.6% (unchanged), break-even 33.3%, gap +17.3pp — unchanged
- TP/SL rates unchanged (same trades, scaled sizes)
- **The gain isn't from better signal — it's from better sizing**

## Hard Constraints

| Constraint | Threshold | Iter 145 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.32 | +2.33 | **PASS** |
| OOS MaxDD ≤ 75.4% | ≤ 75.4% | 38.09% | **PASS** |
| OOS Trades ≥ 50 | ≥ 50 | 164 | **PASS** |
| OOS PF > 1.0 | > 1.0 | 1.53 | **PASS** |
| Symbol concentration ≤ 50% | ≤ 50% | 36.6% | **PASS** |
| IS/OOS Sharpe ratio > 0.5 | > 0.5 | 0.58 | **PASS** |

**All 6 constraints pass**.

## Research Checklist

- **E (Trade Pattern)**: Examined trade-level volatility exposure. Vol-targeting
  scales down during high-vol periods where all models lose together (July 2025).
- **F (Statistical Rigor)**: Walk-forward parameter tuning (IS only, applied to OOS).
  IS improvement (+18%) and OOS improvement (+0.4%) both positive — no regime overfit.

## Implementation Status

**POST-PROCESSING RULE, not yet in backtest engine.** To fully deploy:
1. Add vol-targeting to `src/crypto_trade/backtest.py` (compute weight_factor at
   trade open time from trailing portfolio vol)
2. Verify weight_factor flows through to execution (already does)
3. Re-run full backtests to validate integrated result

For this iteration, the improvement was demonstrated via post-processing of iter 138
trades. The LightGBM models and backtest engine are unchanged.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, X, E, X, X, E, X, X, **E**] (iters 136-145)
Exploration rate: 4/10 = 40% ✓

## Next Iteration Ideas

1. **Implement vol-targeting in backtest.py** (EXPLOITATION, code change) — Move
   the post-processing rule into the backtest engine. Re-run full A+C+D pipeline
   to validate integrated Sharpe +2.33 / MaxDD 38.1% result.

2. **Different vol-targeting configs** (EXPLOITATION) — Test target_vol ∈ [1.0, 3.0]
   and lookback ∈ [7, 21] with multi-seed sensitivity. See if OOS improvement is
   config-robust.

3. **Per-symbol vol targeting** (EXPLORATION) — Each model's trades scaled by its
   own per-symbol vol, not portfolio-wide. Would preserve concentration better.

4. **Combine with Kelly sizing** (EXPLORATION) — Scale by BOTH inverse vol AND
   model probability (half-Kelly). Pairs risk management with edge weighting.

5. **Apply vol targeting to A+C+D+DOGE** (EXPLORATION) — iter 143 failed due to
   DOGE's MaxDD explosion. With vol targeting, the portfolio effect might differ.
   Could unlock DOGE addition at acceptable risk.

## lgbm.py Code Review

No changes to lgbm.py this iteration. The strategy logic is unchanged; only
position sizing was modified at the portfolio level.

## Caveat

The OOS Sharpe improvement is marginal (+0.01). The real win is risk reduction
(MaxDD -39%, Calmar +24%). If the user prioritizes pure Sharpe, this is nearly
a wash. If risk-adjusted returns matter, this is a clear improvement.
