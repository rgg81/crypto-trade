# Phase 7.5 Critic Review — iter-v1/024 — FINAL (post-BLOCK-PENDING-FIX-rerun)

OVERALL: EXPLORATION-NEGATIVE — pre-registered F3 IS-catastrophic auto-reject fires (IS Sharpe Δ = -0.86 ≤ -0.30); independently, F-AXIS #5 gain-share recurrence FAILS for 2/3 cohorts (Pool A + LINK extreme sub-models lean LESS on funding family than normal counterparts), triggering Row 4 INERT-downgrade.

## Iteration Type
TYPE: EXPLORATION (cycle-3 #9/10), family `model-arch` (NEW 16th)

## Prior Verdict (Round 3 PRELIMINARY)
BLOCK-PENDING-FIX — silent zero-mask fallback masked missing funding column; all 3 extreme sub-models skipped; comparison.csv bit-identical to /023.

## Fix Applied (3b6e2a0 + 67341d7)

- Hard ValueError replaces silent fallback in both filter functions
- NEW `data_filter_columns` parameter in LightGbmStrategy loads listed columns from parquet + left-joins onto kline master slice
- `build_lgbm_strategy` passes `data_filter_columns=[V1_ITER024_Z30_COLUMN]` for all 6 regime sub-model builds
- 5 new tests for hard-raise + new parameter
- /024-A re-run with same config

## Defect Axis: PASS — mechanism ENGAGED

- 7 feature_importance CSVs present (was 4 in pre-fix; bit-identical to /023): A_extreme, A_normal, C_extreme, C_normal, D_extreme, D_normal, E_baseline
- `funding_rate_zscore_30` appears in ALL 7 sub-models' importance rankings
- Engineering report: 318 filter callback invocations, all non-zero
- comparison.csv DIFFERS materially from /023 (IS -0.5761 vs +0.4121; OOS +0.7593 vs +0.4606)

## Re-Evaluation

### Check 1-2 (Look-Ahead + Embargo): PASS
Foundation `walk_forward.py:113` unchanged. `data_filter_callback` applied AFTER walk-forward train-window slice. `funding_rate_zscore_30` pre-shifted at /023 feature-gen time.

### Check 13 (Anti-Pattern): PASS
A1-A13 clean. `data_filter_callback` mechanism past-only by construction.

### Check 14 (Axis Family): PASS
`model-arch` NEW 16th family; rotation VALID.

## Verdict Cell Adjudication

Two pre-registered failure triggers fire INDEPENDENTLY:

### Trigger #1 — Row 7 F3 IS-catastrophic (brief Section 4.1)
- Threshold: F3 IS Sharpe Δ ≤ -0.30 → reject regardless of OOS
- Observed: -0.5761 - 0.2829 = **-0.8590** (≤ -0.30 by -0.559)
- 3rd-largest IS-Δ collapse in v1 cycle-3 history (after /020 -0.86, /022 -1.17)

### Trigger #2 — F-AXIS #5 Gain-Share Recurrence FAIL (brief Section 4.2 LM Master §3 ADOPTED)

| Cohort | EXTREME funding gain share | NORMAL funding gain share | Recurrence (EXT > NORM?) |
|---|---|---|---|
| Pool A (BTC+ETH) | (320.31+190.07)/7083 = **7.21%** | (2608.70+1915.40)/49378 = **9.16%** | **FAIL** |
| Model C (LINK) | (92.43+108.68)/3895 = **5.16%** | (810.00+955.35)/23025 = **7.67%** | **FAIL** |
| Model D (LTC) | (76.13+44.23)/2015 = **5.97%** | (1124.84+722.40)/41108 = **4.49%** | PASS |

**2 of 3 cohorts FAIL** → partition NON-SPECIALIZING. Extends /023 H2 REFUTED + /021 finding: basin effects don't reduce to feature-shift at sub-model level either.

### OOS Δ adjudication
- F1 OOS Δ = +0.7593 - 0.6637 = **+0.0956** ∈ [-0.10, +0.10) INERT band
- 4bp shy of PROMISING threshold +0.10
- Per `feedback_no_cheating.md`: CANNOT be reclassified upward (3bp precedent from /023)
- Independently NEGATIVE/INERT even WITHOUT F3 auto-reject

**Verdict cell**: Section 8 Row 7 (F3 auto-reject) + Row 4 (F-AXIS #5 collision) — EXPLORATION-NEGATIVE clean.

## Structural Finding (load-bearing for /025+)

**The regime-conditional architecture ENGAGED but DID NOT specialize.** Extreme sub-models do NOT lean more on funding family than normal sub-models in 2/3 cohorts. This extends the /021 H2 REFUTED finding (cohort effects are basin-level not feature-level) to the SUB-MODEL level: partition-level effects also don't reduce to feature-shift.

The /023 LEARNED-NEGATIVE pattern (portfolio gain share 5.40% > parity 2.38%) persists at sub-model level — LightGBM treats the partition as noise in 2/3 cohorts. The mechanism the user mandated ("multiple smaller models per regime") cannot be tested at v1 single-seed n_trials=18 ENSEMBLE_SIZE=3 EXPLORATION budget.

## Recommendations to QR

1. **Brief Section 4.2 wording mismatch**: Section 4.2 mandates "7 unique `model_name` values in trades.csv" but trades.csv has no model_name column. Verifiable via 7 feature_importance CSVs instead. Future briefs should reword.

2. **Missing `per_cohort_per_regime_breakdown.csv`**: brief Section 10.4 binds 7-row × 14-col CSV deliverable; file absent. Engineering report `OVERALL=READY-FOR-CRITIC` should be gated on ALL mandatory deliverables present.

3. **F-AXIS #5 gain-share recurrence is empirically validated INERT-detector**: future regime-partition axes should pre-register the same recurrence check as Phase 6.0 pre-flight (computed on synthetic/dry-run data) rather than waiting until Phase 7.5.

## Path Forward (mandatory on NEGATIVE)

Per brief Section 11.7 LM Master §7 ADOPTED staging matrix, verdict EXPLORATION-NEGATIVE clean routes /025 to OI delta family at single-seed.

Three candidates from families NOT in prior 5 EXPLORATIONs (/019/020/021/022 per-cohort + /023 feature-family-funding + /024 model-arch):

1. **Open-interest delta family** — `feature-family` (NEW non-OHLCV per v3 carve-out) — primitive `oi_delta_30 = (open_interest_t − open_interest_t-30) / open_interest_t-30` z-scored on 90-bar window. Same /023 spec (n_trials=18 / ENSEMBLE_SIZE=3 / 5-sym universe). Target rank ≤14/43 on ≥2 cohorts + gain share ≥4.0%. LM Master §7 PRIMARY.

2. **Liquidations-delta family** — `feature-family` (NEW orthogonal non-OHLCV) — rolling 24h-window long-vs-short liquidation imbalance, z-scored on 30-bar window. Substitutable if OI parquet ingestion infeasible.

3. **Tri-partition regime gate at multi-seed CONFIRMATION** — `model-arch` REPEAT — `[|z|<0.5, 0.5≤|z|≤1.5, |z|>1.5]` partitions. DEFERRED to /027+ CONFIRMATION; NOT a /025 option (axis closed per Row 7 + Row 4).

## BLOCK-PENDING-FIX Rerun Protocol — COMPLETED

Single rerun under v1 protocol. Fix applied (3b6e2a0 + 67341d7); /024-A re-run. Current verdict EXPLORATION-NEGATIVE per pre-registered Section 4.1 F3 auto-reject AND Section 4.2 F-AXIS #5 gain-share recurrence FAIL. NO further rerun. Iteration ends NO-MERGE.

/025 proceeds per Path Forward (OI delta family at single-seed).
