# Iteration v2/007 Research Brief

**Type**: EXPLOITATION (Optuna trial count tuning)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/005 (10-seed mean +1.297, primary seed 42 +1.671)
**Date**: 2026-04-14
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/006 confirmed that gate loosening is at a local optimum: lowering
ADX threshold 20 → 15 did not improve the 10-seed mean and catastrophically
degraded IS. The iter-v2/006 diary identified the main **structural concern**
as IS Sharpe decaying iteration-over-iteration:

- iter-v2/004: IS Sharpe +0.465
- iter-v2/005: +0.116 (NEAR dragged IS)
- iter-v2/006: −0.278 (ADX loosening let net-negative IS trades through)

The diary proposed **Priority 1 = bump Optuna trials from 10 to 25**. The
hypothesis: 10 trials per monthly model is 5× less than v1's 50, so the
per-month LightGBM hyperparameters are under-optimized. With more trials,
Optuna should find hyperparameters that handle NEAR's hostile IS regime
more gracefully — lifting IS Sharpe without hurting OOS.

## Hypothesis

Bumping `n_trials` from 10 to 25 should:

1. **Raise IS Sharpe** from +0.12 toward +0.4-0.7 range (the goal — IS
   recovery is the whole point of this iteration).
2. **Keep OOS Sharpe flat** or lift modestly. The current OOS edge is
   strong; more trials shouldn't destabilize it.
3. **Restore IS/OOS ratio** toward the healthy "> 0.5" region (or at
   least clearly positive).
4. **Compute cost**: 2.5× per seed, ~15 min per seed instead of ~6. A
   10-seed validation becomes ~150 min instead of ~55 min.

Quantitative prediction (pre-registered):

- **IS Sharpe**: +0.4 to +0.7 (recovery from +0.12)
- **OOS Sharpe (primary seed)**: +1.5 to +1.8 (±0.15 of baseline +1.67)
- **10-seed mean**: +1.2 to +1.4 (±0.1 of baseline +1.30)
- **IS/OOS ratio**: > +0.25 (healthy direction)

## Failure-mode prediction (pre-registered)

Most likely way to fail:

1. **IS is structurally stuck** — NEAR's 2022 bear-market training regime
   is so hostile that no amount of hyperparameter search can make it
   profitable. Optuna just finds different ways to lose on it. Signal:
   IS Sharpe stays near +0.12 regardless of n_trials. This would mean
   the IS problem is NOT under-optimization but a DATA/REGIME issue, and
   the correct fix is per-symbol training-window adjustment or symbol
   replacement — not more Optuna.

2. **OOS degrades** — more trials could over-fit the per-month CV folds
   to the training data, making the walk-forward OOS slightly worse.
   Primary seed 42 could drop by 0.1-0.3 Sharpe.

3. **Compute bloat without benefit** — 2.5× compute cost, same or worse
   metrics. Expensive NO-MERGE.

## Configuration (one variable changed from iter-v2/005)

| Setting | iter-v2/005 | iter-v2/007 | Changed? |
|---|---|---|---|
| **`--n-trials`** | **10** | **25** | **Yes** |
| `adx_threshold` | 20 (not 15 from iter-v2/006) | 20 | — (NO-MERGE reverted) |
| Everything else | Same | Same | — |

Note: iter-v2/006's ADX=15 change did not merge. iter-v2/007 is based on
iter-v2/005's configuration (ADX=20).

## Success Criteria

Primary: **10-seed mean OOS Sharpe > +1.297** (iter-v2/005 baseline mean).

Hard constraints:

- ≥ 7/10 seeds profitable
- OOS trades ≥ 50
- OOS PF > 1.1
- OOS MaxDD ≤ 64.1% (1.2 × baseline)
- No single symbol > 50% OOS PnL
- DSR > +1.0
- v2-v1 OOS correlation < 0.80
- **IS/OOS Sharpe ratio** > 0 (relaxed from strict > 0.5 given the
  persistent IS weakness — getting the ratio POSITIVE is the near-term
  target)

## Section 6: Risk Management Design

### 6.1 Active primitives

Unchanged from iter-v2/005. Same 5 gates, same thresholds, same
RiskV2Config defaults (ADX=20).

### 6.2 Expected fire rates

Unchanged from iter-v2/005 (~65-76% combined kill rate per symbol).
The only thing changing is `n_trials` in the training loop; gate
calibration is unaffected.

### 6.3 Pre-registered failure-mode prediction

"The most likely way iter-v2/007 fails is that IS is structurally stuck
due to NEAR's hostile 2022 bear training regime, and more Optuna trials
just find different ways to lose on that data. Signal: IS Sharpe stays
essentially unchanged (±0.05 of +0.12). If that happens, the correct
diagnosis is that IS weakness is a DATA/REGIME issue, not an
optimization-depth issue, and iter-v2/008 should pivot to NEAR-specific
interventions (shorter NEAR training window, or replace NEAR with a
different symbol)."

### 6.4 Exit Conditions

Unchanged.

### 6.5 Post-Mortem Template

Phase 7 will report:
- Per-symbol IS metrics (especially NEAR — did its IS degrade further
  with 25 trials, or stabilize, or improve?)
- Optuna best-trial distribution (did 25 trials find different
  hyperparameters than 10?)
- IS/OOS ratio change
- Compute cost verification
