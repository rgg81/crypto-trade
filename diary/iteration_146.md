# Iteration 146 Diary

**Date**: 2026-04-05
**Type**: EXPLORATION (DOGE re-addition + vol targeting)
**Model Track**: A+C+D+DOGE with vol-targeted sizing
**Decision**: **NO-MERGE** — OOS Sharpe +2.10 < baseline +2.33; MaxDD still exceeds 1.2× threshold

## Results

| Metric | Baseline (iter 145) | Iter 146 | Change |
|--------|---------------------|----------|--------|
| OOS Sharpe | +2.33 | +2.10 | -10% |
| OOS MaxDD | 38.1% | 48.5% | +27% |
| OOS PF | 1.53 | 1.45 | -5% |
| OOS Calmar | 3.40 | 2.83 | -17% |
| OOS PnL | +129.5% | +137.2% | +6% |
| OOS Trades | 164 | 214 | +30% |
| Top concentration | 36.6% (BNB) | **29.2%** (ETH) | **best ever** |

## Analysis

### DOGE still doesn't help even with vol targeting

Iter 143 showed DOGE destroys MaxDD (92.5%). Iter 146 shows that vol targeting
dampens DOGE's damage (MaxDD down to 48.5% from 92.5%) but doesn't solve the
underlying issue: **DOGE's drawdowns remain temporally correlated with A/C/D
drawdowns**, just at smaller scale.

The arithmetic:
- With DOGE, the portfolio loses ~50% more total in bad months
- Vol targeting dampens ALL trades (including the good ones from other models)
- Net: Sharpe drops 10% because the added DOGE signal is correlated noise under
  vol targeting

### Best concentration ever achieved

Top concentration 29.2% (ETH) — **first time under the strict 30% threshold**
across all 144 iterations. 5 symbols trading = genuine diversification at PnL level.
But this diversification benefit doesn't translate to higher Sharpe.

### Definitive closure: DOGE is not a viable addition

Tested 3 ways:
1. iter 143: raw portfolio, MaxDD explodes (92.5%)
2. iter 146: vol targeting, Sharpe drops (+2.10)
3. Implicit: standalone DOGE has strong Sharpe (+1.24) but correlated timing

**Conclusion**: DOGE cannot be added to the A+C+D portfolio in any configuration
tested. The correlation structure is the blocker, not individual model quality.

## Gap Quantification

Iter 146: OOS WR 50.9%, break-even 33.3%, gap +17.6pp (similar to baseline).
Sharpe regression (-10%) is from added uncorrelated vol, not WR degradation.

## Hard Constraints

| Constraint | Threshold | Iter 146 | Pass? |
|------------|-----------|----------|-------|
| OOS Sharpe > baseline | > +2.33 | +2.10 | **FAIL** |
| OOS MaxDD ≤ 45.7% | ≤ 45.7% | 48.5% | **FAIL** |

## Research Checklist

- **B (Symbol Universe)**: Confirms iter 144 finding that DOGE's temporal correlation
  blocks portfolio value add, regardless of sizing technique.
- **E (Trade Pattern)**: Vol targeting correctly identifies high-vol periods and
  reduces exposure — but the pattern of losses is distributed broadly across models,
  not concentrated enough for vol targeting to fully offset.

## Exploration/Exploitation Tracker

Last 10 iterations: [X, E, X, E, X, X, E, X, E, **E**] (iters 137-146)
Exploration rate: 5/10 = 50% ✓

## Next Iteration Ideas

1. **Implement vol targeting in backtest.py** (EXPLOITATION, code change) — The
   iter 145 result needs production implementation. Modify `backtest.py` to compute
   weight_factor at trade-open time from trailing portfolio vol.

2. **Per-symbol vol targeting** (EXPLORATION) — Instead of portfolio-wide vol,
   each trade scales by its SYMBOL's vol. BTC trades scale by BTC vol, LINK trades
   by LINK vol. More targeted risk management.

3. **Test different lookback windows** (EXPLOITATION) — iter 145 used 14-day
   lookback. Try 7d, 10d, 21d with multi-seed sensitivity check.

4. **Accept v0.145 as FINAL baseline** — After 146 iterations, the A+C+D+VT
   portfolio at +2.33 OOS Sharpe / 38.1% MaxDD is genuinely strong. Move to
   production deployment.
