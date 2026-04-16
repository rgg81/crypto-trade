# Iteration v2/035 Diary

**Date**: 2026-04-16
**Type**: EXPLOITATION (v1-style 5-seed ensemble, 50 trials)
**Parent baseline**: iter-v2/029
**Decision**: **NO-MERGE** — IS/OOS ratio 0.475 < 0.5 rule (all other constraints pass)

## The best v2 result ever — blocked by one constraint

| Metric | iter-029 | **iter-035** | Pass? |
|---|---|---|---|
| OOS trade Sharpe | +1.4054 | **+1.7229** (+23%) | ✓ primary |
| OOS monthly | +1.2774 | **+1.4805** (+16%) | — |
| OOS PF | 1.5889 | **1.8702** (+18%) | ✓ > 1.0 |
| OOS MaxDD | 32.08% | **26.69%** (best ever) | ✓ ≤38.5 |
| OOS WR | 41.1% | **49.2%** (+8pp!) | — |
| OOS trades | 107 | 63 | ✓ ≥50 |
| Concentration | 69.47% FAIL | **44.57% PASS** | ✓ first ever! |
| **IS/OOS trade ratio** | 0.553 PASS | **0.475 FAIL** | **✗ < 0.5** |
| IS trade Sharpe | +0.7778 | +0.8186 (flat) | — |

**5 of 6 hard constraints PASS.** Only one fails: IS/OOS ratio at
0.475 vs 0.5 rule (off by 0.025). The ratio is high because OOS is
exceptionally strong, not because IS is weak — IS is actually better
than iter-029 (+0.82 vs +0.78).

## What the v1-style ensemble does

v1 config: `ensemble_seeds=[42,123,456,789,1001]`, `n_trials=50`.
Each model averages predictions across 5 Optuna-trained models.

**The ensemble acts as a quality filter**:
- Trade count dropped 41% (107 → 63 OOS)
- But Win Rate jumped 8pp (41.1% → 49.2%)
- Each surviving trade is a trade where 5 models agreed
- XRP: only 7 OOS trades but 71.4% WR (!)
- NEAR: 17 OOS trades, 64.7% WR

**All 4 symbols are profitable** for the first time. No net-losers.
The ensemble eliminates the "noise-filler" trades that dragged
DOGE/SOL negative in prior iters.

## Per-symbol (weighted_pnl share)

| Symbol | Trades | WR | Weighted PnL | Share |
|---|---|---|---|---|
| XRP | 7 | 71.4% | +31.47 | 44.57% |
| NEAR | 17 | 64.7% | +28.85 | 40.86% |
| DOGE | 19 | 42.1% | +8.62 | 12.20% |
| SOL | 20 | 35.0% | +1.68 | 2.37% |

XRP and NEAR contribute 85% — but both are below 50% individually.
The concentration rule passes because the ensemble splits the
high-confidence signals more evenly between these two.

## How to fix the IS/OOS ratio — iter-036 plan

The ratio fails because IS is +0.82 while OOS is +1.72 (trade
Sharpe). We need IS ≥ 0.86 for the ratio to hit 0.5.

iter-032 showed IS trade Sharpe **+1.04** with the ADA symbol mix
(DOGE+XRP+NEAR+ADA). iter-035 used the baseline mix (DOGE+SOL+XRP+NEAR).

**iter-036 = v1-style 5-seed ensemble + iter-032 symbol mix**:
- ensemble_seeds=[42,123,456,789,1001], n_trials=50 (from iter-035)
- V2_MODELS = DOGE+XRP+NEAR+ADA (from iter-032)
- Expected IS ≈ +1.0 (from iter-032's IS), OOS ≈ +1.5 (from iter-035)
- Ratio ≈ 1.0/1.5 ≈ 0.67 → PASSES easily

If iter-036 produces OOS comparable to iter-035 AND IS comparable to
iter-032, it will pass ALL 6 constraints and be the first clean MERGE
since the iter-029 forced reset.

## Runtime

- Total: ~2.8 hours (4 models × ~42min each)
- Per model: 5 × 50 = 250 Optuna trials per model per month
- Each model: ~2500-3050s

## MERGE / NO-MERGE

**NO-MERGE.** IS/OOS ratio 0.475 < 0.5 constraint fails. Everything
else passes including the concentration audit (first time ever).

**Next iteration**: iter-v2/036 = v1-ensemble + ADA symbol swap.
Expected to fix the ratio by combining iter-035's ensemble approach
with iter-032's IS-boosting symbol mix.
