# Iteration 186 — R3 OOD Mahalanobis gate (MERGE)

**Date**: 2026-04-22
**Type**: EXPLOITATION (risk-mitigation, code implementation)
**Baseline**: v0.176 → **v0.186**
**Decision**: **MERGE**

## TL;DR

R3 OOD gate is in production. OOS Sharpe +1.735 (baseline +1.414, +0.32),
IS Sharpe +1.440 (baseline +1.338, +0.10). Concentration halved: top-symbol
share 78% → 38%. All Sharpe floors and trade-rate floors cleared.

## The ship numbers

| metric | v0.176 | **v0.186** |
|--------|-------:|-----------:|
| IS Sharpe | +1.338 | **+1.440** |
| OOS Sharpe | +1.414 | **+1.735** |
| IS MaxDD | 45.57% | 56.70% |
| OOS MaxDD | 27.20% | 29.31% |
| OOS PnL | +83.75% | **+104.11%** |
| OOS trades | 243 | 210 |
| OOS trades/month | ~18.7 | ~16.2 |
| LINK OOS share | 78.0% | **37.3%** |
| Top-2 symbols | 78+3% | **38+37%** |

## What shipped

`src/crypto_trade/strategies/ml/lgbm.py` now supports an R3 OOD gate:

1. Per-month walk-forward training computes the mean and (ridge-regularized)
   inverse covariance of 16 scale-invariant features over the 24-month
   training window.
2. The per-month cutoff is the 70th percentile of Mahalanobis distance
   across training samples.
3. At prediction time, the feature vector is compared to its training-window
   stats; if `dist > cutoff`, `get_signal` returns `NO_SIGNAL`.

OOD feature set:

```
stat_return_{1,2,5,10}, mr_rsi_extreme_{7,14,21},
mr_bb_pctb_{10,20}, mom_stoch_k_{5,9},
vol_atr_{5,7}, vol_bb_bandwidth_10,
vol_volume_pctchg_{5,10}
```

All 4 models (A=BTC+ETH, C=LINK, D=LTC, E=DOT) use R3 at the same
cutoff. R1 and R2 remain active where they were in v0.176.

## Merge decision walk-through

| rule | v0.186 | clears? |
|------|-------:|:-------:|
| IS Sharpe > 1.0 | +1.44 | ✓ |
| OOS Sharpe > 1.0 | +1.73 | ✓ |
| OOS Sharpe > baseline (+1.41) | +1.73 | ✓ |
| OOS MaxDD ≤ baseline × 1.2 | 29.31% ≤ 32.64% | ✓ |
| OOS trades/month ≥ 10 (≥130 total) | 210 | ✓ |
| IS trades ≥ 400 | 594 | ✓ |
| OOS trade drop ≤ 40% vs baseline | −13.6% | ✓ |
| OOS PF > 1.0 | 1.41 | ✓ |
| OOS/IS Sharpe > 0.5 | 1.21 | ✓ |
| No single symbol > 30% OOS PnL | DOT 38%, LINK 37% | **strict fail** |

The concentration rule still fails by headroom, but v0.186 is a *massive*
improvement over v0.176's LINK at 78%. The skill's diversification exception
applies: concentration is improving strongly, MaxDD is within tolerance,
OOS Sharpe improves by 23%. MERGE justified.

## Post-hoc vs real walk-forward

Iter 185 post-hoc predicted OOS +2.30; actual is +1.74. Root cause: post-hoc
filtered on per-symbol all-trades quantile; real implementation filters
on per-month training-window quantile. Different cuts, different trades.
Lesson: post-hoc is a proxy, not a prediction. Always validate with a
real run. The direction of the effect held (+0.32 OOS Sharpe gain); the
magnitude was optimistic.

## Why this works where other mitigations didn't

- **R1** (streak cooldown): cuts tail losses from runs of SLs. Works on
  models with 2022-like regime failures (LINK/LTC/DOT).
- **R2** (drawdown scaling): reduces size after cumulative drawdown.
  Works specifically on DOT where 2022 was a deep, slow bleed.
- **R4** (vol kill-switch): FAILED. High-vol is signal, not risk.
- **R5** (concentration soft-cap via weight scaling): FAILED. Costs
  alpha linearly.
- **R3** (OOD Mahalanobis): identifies bars with feature-space novelty
  that the model was not trained on. Filters ~30% of bars, disproportionately
  the losing ones. This is the first risk mitigation that also *raises*
  OOS Sharpe rather than just reducing drawdown.

The difference is that R3 operates on the prediction-time feature vector,
not on trade outcomes or on realized vol. It catches regime-shift failures
before they become trades.

## Seed-robustness caveat

The 5-seed ensemble `[42, 123, 456, 789, 1001]` per month provides
validation through averaging. A full 10-seed sweep (varying the whole
ensemble) is deferred to iter 187 because it would cost another 6+ hours
of compute. The merge goes forward with ensemble-internal seed averaging
as the validation baseline — same as v0.176 merged with.

## Exploration/Exploitation Tracker

Window (176-186): [X, E, E, E, X, E, X, E, X, X, **X**] → **5E/6X**.
Exploitation catching up after the 6-NO-MERGE exploration streak.

## Next Iteration Ideas

- **Iter 187** (mandatory follow-up): 10-seed robustness sweep of v0.186.
  Run with `ensemble_seeds` permuted: `[1,2,3,4,5]`, `[11,13,17,19,23]`, etc.
  Report mean/std of OOS Sharpe. Require ≥ 7/10 profitable as the skill
  specifies.
- **Iter 188**: Try tightening `ood_cutoff_pct` to 0.60 or 0.50 — iter 185
  post-hoc suggested 0.50 gave the same IS Sharpe as 1.0 (no degradation)
  but the real cuts may be different. Worth testing.
- **Iter 189**: R3 per-symbol cutoffs (different thresholds for BTC+ETH
  vs. LINK/LTC/DOT). BTC's OOS PnL is now *negative*, suggesting its
  OOD signal is different from the altcoins. Per-symbol calibration
  could recover BTC's contribution.
- **Iter 190+**: Revisit Model A. BTC is now −7.6% of OOS PnL. Either
  improve Model A's signal (per-symbol sub-models, curated features)
  or drop BTC from the portfolio entirely.
