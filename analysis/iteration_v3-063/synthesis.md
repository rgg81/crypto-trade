# iter-v3/063 EDA Synthesis

## Catalog summary

- Total proposed features: 71
- Already in parquet (zero compute cost): 49 (69%)
- NEW (need implementation): 22 (31%)

## Category distribution

category
technical         8
regime            7
tail_risk         7
volume_micro      7
microstructure    7
cross_asset       7
engineered        6
momentum          5
vol_estimator     4
returns           4
calendar          4
fracdiff          3
funding           2

## ADF stationarity

- Features stationary in ≥2 of 3 symbols at p<0.05: 70/71
- Non-stationary features (regime-indicator exceptions need justification): 1

## Pairwise IC (BCH IS data)

- High-IC pairs (|IC|>0.70): 119
- With Category-2 carve-out applicable: 39
- Pairs needing resolution (no carve-out): 80

## Path recommendation

**Path B — Moderate ~50 features** is the PRIMARY recommendation.

Rationale:
1. **Avoids wall-clock blowup**: /060/061 ran at 0.69h. Path A (100 features) at single-seed
   n_trials=35 would expand Optuna search space materially; wall-clock projection 1.5-2h
   (above the 1.5h flag threshold).
2. **Avoids single-seed lottery at 100-feature space**: per
   `feedback_v3_engineered_features_dont_stack.md`, the lesson from iter-v3/026/027 is that
   adding multiple new engineered features at single-seed produces structurally suspicious
   IS/OOS divergence. 100 features at single-seed amplifies this risk.
3. **Already 45 features available in parquet** — adding ~5 NEW high-conviction features to
   reach 50 is the lowest-risk first step.
4. **Preserves Path A optionality at /069 CONFIRMATION**: if /063 Path B is PROMISING, /069
   CONFIRMATION can re-run at ENSEMBLE_SIZE=10 with the same 50-feature set OR expand to
   the full 100 catalog if multi-seed validation supports it.

## Cycle 1 axis-PASS classification probability distribution

Based on prior catalog (iter-v3/015-057) and engineered-features-don't-stack precedent:

- PROMISING-AT-EXPLORATION: 30% (mass expansion is structurally a different axis than
  single-feature SWAP — wider search space could escape cycle-4 saturation)
- INERT-AT-EXPLORATION: 40% (most-likely outcome at single-seed n_trials=35; aggregate
  Sharpe within noise band)
- SUSPICIOUS-OOS-DOMINANT: 15% (specific risk: more features → more lottery in OOS at
  single-seed)
- NEGATIVE-AT-EXPLORATION: 15% (Optuna search budget inadequate at expanded space)

## Pre-registered failure modes

1. **n_trials=35 inadequate for 50-feature space** → INERT or NEGATIVE classification.
   Mitigation: /069 CONFIRMATION retests at n_trials=35 × ENSEMBLE_SIZE=10 = 350 effective
   trials per symbol.

2. **High-IC pairs steal colsample picks** → reduces signal quality. Mitigation: drop
   highest-IC redundant features in Phase 1 EDA selection (this script).

3. **Single-seed lottery at 50-feature space** → SUSPICIOUS-OOS-DOMINANT. Mitigation:
   pre-registered SUSPICIOUS-OOS-DOMINANT classification + defer to /069 CONFIRMATION.

4. **Feature regen wall-clock** → If parquet regen takes >10min, total wall-clock could
   exceed 1.5h. Mitigation: most features (45 of 50) are already in parquet; new feature
   regen estimated at 3-5min.
