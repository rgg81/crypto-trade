# Phase 7.5 Critic Review — iter-v3/038

OVERALL: **EXPLORATION-NEGATIVE** — ALGO fracdiff confirms fracdiff is BCH-specific (-8.24 ALGO swing).

## Cycle 10/10 Summary

3 PROMISING / 7 NEGATIVE in post-iter-v3/028 cycle. Best result iter-v3/035 (BCH-only fracdiff + LDO ATR + ALGO universe + regime_momentum + 4-sym).

## iter-v3/039 CONFIRMATION Spec (LOCKED)

- 4 symbols: BCH+LDO+TRX+ALGO
- 14 features universal incl regime_momentum_signed_5d
- BCH-only +fracdiff_d05_close (15 features for BCH; 14 for others)
- LDO ATR (1.5, 0.75); others default (2.0, 1.0)
- --seeds 2 --n-trials 35, ENSEMBLE_SIZE=5
- 6h wall-clock cap

## Multi-Seed Forecast

iter-v3/035 single-seed +2.85 OOS. Compression precedents:
- iter-v3/013 single-seed +2.70 → +0.39 multi-seed (86% reduction; falsified)
- iter-v3/025 single-seed +1.22 → +0.51 multi-seed (58% reduction)

iter-v3/035 forecast at 50-60% compression: +1.14 to +1.43 OOS. Likely clears +1.0 floor.

User directive 2026-05-08: STRICTLY-BETTER-than-prior-baseline triggers BASELINE_V3.md update. iter-v3/028 baseline = +0.51 IS / +0.51 OOS. iter-v3/039 must clear +0.51 IS / +0.51 OOS at multi-seed to update baseline.

## Catalog Row

`| iter-v3/038 | 2026-05-08 | ALGO-only fracdiff (test specificity) | -0.26 (vs iter-v3/035 -0.10) | +2.4444 (Δ -0.41; ALGO -8.24 swing) | EXPLORATION-NEGATIVE | NO — fracdiff CONFIRMED BCH-specific; cycle 10/10 complete; iter-v3/039 = CONFIRMATION on iter-v3/035 bundle |`
