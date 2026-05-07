# Engineering Report — iter-v3/018

## Headers

- Iteration: iter-v3/018
- Type: CONFIRMATION (first true v3 CONFIRMATION ever)
- Branch: iteration-v3/018
- Setup commit SHA: a595f46 (ITERATION_LABEL=v3-018, the only code change)
- Phase 5.5 gate SHA: 98769ce (PASS)
- Brief SHA: 5c1b303
- Hardware: WSL2 / Linux 6.6.87.2 x86_64
- Wall-clock time: 4.54h (4h 32min — 32min over 4h cadence cap)
- Runner invocation: `uv run python run_baseline_v3.py --seeds 2 --n-trials 50`
- No `--exploration` flag (CONFIRMATION mode confirmed)

## Library Stack (Reproducibility Stamp)

| Package | Version |
|---|---|
| lightgbm | 4.6.0 |
| numpy | 2.2.6 |
| optuna | 4.8.0 |
| pandas | 3.0.0 |
| pyarrow | 23.0.1 |
| pytest | 9.0.2 |
| scikit-learn | 1.8.0 |
| scipy | 1.17.0 |
| statsmodels | 0.14.6 |

## Configuration Diff vs Baseline (iter-v3/013 single-seed EXPLORATION baseline)

| Parameter | iter-v3/013 baseline | iter-v3/018 CONFIRMATION |
|---|---|---|
| Outer seeds | 1 (default, --seeds 1) | **2** (--seeds 2) |
| ENSEMBLE_SIZE (inner) | 1 (--exploration forces 1) | **5** (non-exploration mode) |
| Models per cell | 1 × 1 = 1 | **2 × 5 = 10** |
| n_trials (Optuna) | 10 (--exploration forces 10) | **50** (--n-trials 50 default) |
| colsample_bytree | hardcoded 1.0 (fast_mode=True) | **Optuna-tuned** (fast_mode=False) |
| --exploration flag | YES | **NO** |
| ITERATION_LABEL | "v3-017" (prior baseline) | **"v3-018"** |
| Symbols | BCH, LDO, TRX | UNCHANGED |
| V3_FEATURE_COLUMNS | 13 columns | UNCHANGED |
| ATR labeling (2.0/1.0) | atr_tp=2.0, atr_sl=1.0 | UNCHANGED |
| zscore_threshold | 2.0 | UNCHANGED |
| BTC trend threshold_pct | 15.0 | UNCHANGED |
| REQUIRED_GAP | 66 | UNCHANGED |
| OOS_CUTOFF_DATE | 2025-03-24 | UNCHANGED (sacred) |
| training_months | 24 | UNCHANGED (sacred) |

One-axis-only discipline: the SOLE change is the multi-seed configuration (--seeds 2, ENSEMBLE_SIZE=5, n_trials=50, colsample Optuna-tuned). All strategy parameters byte-identical to iter-v3/013.

## Key Metrics Block

### Headline (comparison.csv — primary seed 42 IS + both seeds OOS aggregated into primary seed)

NOTE: comparison.csv reports primary seed (seed=42) metrics. Multi-seed mean computed from seed_summary.json is shown separately below.

| Metric | IS (seed 42) | OOS (seed 42) | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.4563 | +0.2343 | 0.5134 |
| daily_sharpe | +1.1668 | +0.4643 | 0.3979 |
| max_drawdown (%) | 36.7045 | 29.1986 | 0.7955 |
| profit_factor | 1.1861 | 1.0584 | 0.8923 |
| win_rate (%) | 30.8140 | 41.1765 | 1.3363 |
| n_trades | 172 | 102 | 0.5930 |
| total_pnl | 35.7119 | 7.8711 | 0.2204 |
| monthly_calmar | 0.9730 | 0.2696 | 0.2771 |
| weighted_pnl_total | 35.7119 | 7.8711 | 0.2204 |
| dsr | 0.0 | — | — |
| pbo | 0.0892 | — | — |
| psr | 0.9936 | — | — |
| n_trials | 1500 | — | — |
| n_effective_trials | 25 | — | — |

### Per-seed IS/OOS summary (seed_summary.json)

| Seed | IS monthly Sharpe | OOS monthly Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Max OOS Conc | BTC killed |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.4563 | +0.2343 | 29.20% | 0.2696 | 102 | 66.08% | 28 |
| 123 | +0.3013 | +0.5394 | 27.74% | 0.6562 | 79 | 55.83% | 29 |
| **Mean** | **+0.3788** | **+0.3869** | 28.47% | 0.4629 | 90.5 | 60.96% | 28.5 |

### Comparison vs iter-v3/013 single-seed baseline

| Metric | iter-v3/013 (single-seed) | iter-v3/018 mean (2-seed) | Delta |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | +0.3788 | **-0.630** |
| OOS monthly Sharpe | +2.6970 | +0.3869 | **-2.310** |
| IS n_trades | 209 | ~160 (seed-42: 172) | -49 |
| OOS n_trades | 85 | 90.5 (mean) | +5.5 |

**Sharpe compression magnitude: IS delta -0.63, OOS delta -2.31 (85.6% OOS reduction).**

## Hypothesis-Implementation Alignment

Brief spec fully implemented:
- `--seeds 2`: CONFIRMED from run.log line 6 "Seeds: 2 Optuna trials/model: 50"
- `--n-trials 50`: CONFIRMED from run.log "Optuna trials/model: 50"
- ENSEMBLE_SIZE=5: CONFIRMED from pre-flight verifier (assertion passes)
- NO `--exploration` flag: CONFIRMED — fast_mode_for_run=False, ensemble_size_for_run=5
- `colsample_bytree` Optuna-tuned: CONFIRMED — full search space (not hardcoded 1.0)

Wall-clock: 4.54h vs 4h HARD CAP — exceeded by 32 minutes. The brief's Calibration A (linear 50x from 6-min baseline = ~5h) was closer to reality than Calibration B (calibrated from iter-v3/008 abort ~1.3h). Root cause: Calibration B under-estimated because iter-v3/008 was aborted at 4h 15min with 5 outer seeds × 4 symbols; the per-cell Optuna computation at n_trials=50 dominates, and the brief's 30% scaling factor was optimistic. Empirical cap for future CONFIRMATIONs should be updated to 5h or n_trials reduced to 30 for next CONFIRMATION.

## Multi-Seed Sharpe Compression Analysis

**Observed**: IS +1.0088 → +0.3788 (mean), OOS +2.6970 → +0.3869 (mean). The hypothesis did NOT hold.

**Mechanism analysis (ranked by probability)**:

1. **Single-seed lottery — dominant (P=75%)**: iter-v3/013's seed=42 was favorable across all 3 symbols. OOS Sharpe +2.70 on 85 trades with LDO 80% WR on 10 trades (single-seed) is consistent with an underlying distribution that produces much lower Sharpe in expectation. The 2-seed mean (+0.39 OOS) better reflects the true expected performance. Seed 123 OOS=+0.54 is also weak, confirming the single-seed result was not reproducible.

2. **Optuna n_trials=50 found more conservative hyperparams (P=20%)**: With 10x more Optuna trials than the EXPLORATION baseline (10 trials), the search space was explored more broadly. This can lower IS Sharpe when the additional trials find that aggressive hyperparams (found quickly at n=10) are over-fit. The IS trade count dropped from 209 to ~160-172, consistent with higher confidence_threshold hyperparams being selected under more thorough search.

3. **ENSEMBLE_SIZE=5 inner averaging (P=5%)**: 5-seed inner ensemble should reduce variance without compressing Sharpe in expectation. Not a primary contributor.

**Key structural finding**: `comparison.csv` IS Sharpe = 0.4563 is seed 42's IS value, NOT a multi-seed mean. The runner pools seed 42's trade list (primary seed) for all metrics in `comparison.csv`. The multi-seed mean IS Sharpe is 0.3788 (from `seed_summary.json`). This is documented transparently; the Phase 7 QR evaluating gates should use seed_summary.json for the multi-seed mean and pareto_front.csv for the 2-seed Pareto check.

## Per-Symbol Multi-Seed Analysis

### BCH (BCHUSDT)

- IS (seed 42): 87 trades, 41.4% WR, +31.52% PnL — strong IS contributor
- OOS (seed 42): 38 trades, 42.1% WR, weighted_pnl=+6.14, concentration=33.9% (positive-denominator)
- Per-symbol brief §4: BCH is the STABLE contributor. OOS performance is positive and more diluted than LDO single-seed. TRUE positive.

### TRX (TRXUSDT)

- IS (seed 42): 75 trades, 33.3% WR, -1.07% PnL — IS NEGATIVE
- OOS (seed 42): 48 trades, 43.8% WR, weighted_pnl=+11.97, concentration=66.1%
- Divergent IS-negative / OOS-positive pattern: TRX appears to trade against IS trend but aligns OOS. This is suspicious and consistent with the LdP purge gap operating correctly (IS data is harder after proper purge). TRX at 66.1% OOS concentration (primary seed) fails gate 7 by 36pp.

### LDO (LDOUSDT)

- IS (seed 42): 10 trades, 30.0% WR, +5.63% PnL — marginal
- OOS (seed 42): 16 trades, 31.2% WR, weighted_pnl=-10.24 — NEGATIVE
- LDO single-seed lottery CONFIRMED: iter-v3/013 showed 80% WR on 10 OOS trades at seed=42. Under multi-seed (n_trials=50 Optuna), LDO OOS flips to -10.24 weighted_pnl and -13.34% raw PnL on 16 trades. The 80% WR was a favorable Optuna path at n_trials=10 that the fuller search space did not replicate.

## Seed Concentration Audit

| Seed | OOS Sharpe | OOS trades | Max OOS conc | IS Sharpe |
|---|---:|---:|---:|---:|
| 42 | +0.2343 | 102 | 66.08% (TRX) | +0.4563 |
| 123 | +0.5394 | 79 | 55.83% (TRX) | +0.3013 |
| Mean | +0.3869 | 90.5 | 60.96% (TRX) | +0.3788 |

Per-symbol concentration did NOT compress under multi-seed: TRX dominates OOS in both seeds (66% and 56%). The LDO single-seed lottery resolved to NEGATIVE, and BCH remains a secondary contributor. Concentration failure is now TRX-driven, not LDO-driven.

## Label Leakage Audit

From run.log pre-flight:
```
Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66  [matches REQUIRED_GAP=66]  PASS
```
REQUIRED_GAP=66 was UNCHANGED from iter-v3/013. The gap satisfies the López de Prado purge requirement: `(21+1) * 3 = 66` candles gap between training and validation windows. No label leakage detected.

## Gate Efficacy Table (7-primitive risk stack)

All gates are identical to iter-v3/013 — thresholds unchanged. Multi-seed fire rates observed from run.log:

| Primitive | Threshold | IS fire rate | OOS fire rate | Notes |
|---|---|---|---|---|
| BTC trend kill | ±15%/14d band | seed 42: 10.2% killed (28/274) | — | seed 123: 12.5% killed (29/232) |
| Vol scaling | clip(atr_pct_rank_200, 0.3, 1.0) | always active | — | mean scale ~0.6 expected |
| ADX gate | ADX > 20 | ~60% pass (inherited) | — | unchanged from iter-v3/013 |
| Hurst regime | 0.05–0.95 | ~90% pass (inherited) | — | unchanged |
| Feature z-score OOD | |z| > 2.0 | ~25–35% killed (inherited) | — | unchanged |
| Low-vol filter | atr_pct_rank_200 ≥ 0.33 | ~67% pass (inherited) | — | unchanged |
| Hit-rate feedback | DISABLED | 0% | — | unchanged |

BTC trend fire rate slightly higher at seed 123 (12.5% vs 10.2%), consistent with different trade timing under different Optuna hyperparams.

## MERGE Gates Evaluation (Section 8 — Locked Pre-Backtest)

| Gate | Threshold | Observed | PASS/FAIL |
|---|---|---|---|
| 1. IS monthly Sharpe ≥ +1.0 | ≥ +1.0 | +0.3788 (mean) | **FAIL** by 0.621 |
| 2. OOS monthly Sharpe ≥ +1.0 | ≥ +1.0 | +0.3869 (mean) | **FAIL** by 0.613 |
| 3. OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | 0.5134 (seed 42) / 1.791 (seed 123) / mean ~1.02 | **PASS** (both seeds individually exceed 0.5) |
| 4. DSR > 0.95 | > 0.95 | 0.0 | **FAIL** — see DSR root cause below |
| 5. PBO < 0.4 (mean AND max) | < 0.4 (mean); max noted | mean=0.0892 PASS; max=1.0 (TRX/2022-10, TRX/2023-01) FAIL on max-aggregator | **PASS (mean) / FAIL (max-aggregator)** — 13 cells ≥ 0.4, 2 cells = 1.0 |
| 6. PSR > 0.95 | > 0.95 | 0.9936 | **PASS** |
| 7. Top-symbol concentration ≤ 30% | ≤ 30% | 66.08% TRX OOS (seed 42), 55.83% TRX (seed 123) | **FAIL** by 36pp (seed 42) / 26pp (seed 123) |
| 8. Bundle OOS trade count ≥ 130 | ≥ 130 | 102 (seed 42) / 79 (seed 123); pooled = 181 (sum, not deduped) | **FAIL** — per-seed both below 130; "bundle" interpretation is ambiguous — see note |
| 9. 10-seed pre-MERGE validation | mean Sharpe > 0, ≥7/10 profitable | NOT RUN — pending gate 1+2 failure | **NOT TRIGGERED** (gates 1+2 fail first) |
| 10. Pareto non-domination — both seeds Sharpe > 0 | both > 0 | seed 42: +0.2343, seed 123: +0.5394 | **PASS** — both positive |

**Failed gates (locked pre-backtest): 1, 2, 4, 7.** Gate 5 PASS on mean-aggregator but FAIL on max-aggregator. Gate 8 depends on "bundle" interpretation (per-seed both fail the 130 floor; sum of unique trades across seeds = 181 which would pass — but the brief specifies per-bundle, not per-seed-sum). Conservatively: FAIL on per-seed. Gates 3, 6, 10 PASS.

**Confirmed FAIL count: 5** (gates 1, 2, 4, 7, and gate 5 max-aggregator). Gate 8 status: FAIL under strict per-seed reading.

### DSR=0 Root Cause Investigation

DSR=0 is **NOT a computation bug**. It is the mathematically correct result of the DSR formula under the iter-v3/018 configuration:

- `n_trials_total = 50 × 5 × 3 × 2 = 1500`
- Expected max Sharpe for n=1500 trials: `E[max_SR] = 3.369` (computed from López de Prado formula)
- Trade-level raw IS Sharpe (mean/std × sqrt(172)): estimated ~1.7 from monthly Sharpe=0.4563
- `dsr_z = (1.7 - 3.369) / sr_std` is strongly negative → `p_value = norm.cdf(very_negative) ≈ 0.0`

The DSR correctly reports that 1500 Optuna trials on 172 IS trades makes it essentially certain the observed IS Sharpe was discovered through search-space overfit. This is not a code defect — the `deflated_sharpe_ratio_v3` function (validation_v3.py:397) does not clamp and returns the correct mathematical value.

**Structural implication**: DSR > 0.95 requires `observed_sr > E[max_SR] = 3.369`. Achieving this requires either (a) far more IS trades (hundreds of OOS-quality trades), (b) far fewer Optuna trials (defeat the point of multi-seed validation), or (c) a fundamentally stronger underlying signal. The DSR gate at 0.95 is a legitimate structural constraint: the current 13-feature stack on 172 IS trades with 1500 Optuna trials does NOT clear it.

**Noted discrepancy**: iter-v3/013 single-seed also showed DSR=0.0 with n_trials=30 and E[max_SR]=2.073. The brief (Section 4.2) predicted DSR in [0.85, 0.99] for multi-seed "because n_eff > 10". This prediction was incorrect — n_eff does not enter the DSR formula directly; what matters is `observed_sr vs E[max_SR]`. The prediction was overconfident.

### PBO Max-Aggregator Analysis

- Mean aggregator: 0.0892 — PASS (< 0.4)
- **13 cells with PBO ≥ 0.4**: BCHUSDT/2023-04 (0.804), BCHUSDT/2024-05 (0.9998), LDOUSDT/2024-10 (0.438), LDOUSDT/2025-01 (0.543), LDOUSDT/2025-08 (0.544), LDOUSDT/2025-11 (0.518), LDOUSDT/2026-05 (0.573), TRXUSDT/2022-10 (1.0), TRXUSDT/2022-11 (0.784), TRXUSDT/2022-12 (0.926), TRXUSDT/2023-01 (1.0), TRXUSDT/2024-12 (0.593), TRXUSDT/2025-09 (0.958)
- **Max per-cell PBO = 1.0** (TRX/2022-10 and TRX/2023-01)

The TRX/2022 Q4 high-PBO cluster (pre-committed in iter-v3/013 catalog) persists unchanged. These cells correspond to the FTX/LUNA crash regime where TRX price was highly correlated with BTC; the Optuna search found no consistent out-of-sample edge and the best IS config was overfitted rank-1. The mean aggregator (0.0892) is still well below 0.4, so the cross-cell average is healthy. Per the brief Section 5.2 pre-commit, Critic flags max-aggregator as INFORMATIONAL — the binding gate uses the mean aggregator per `BASELINE_V3.md`. However, per the brief Section 8 gate 5 wording "cross-cell mean AND max-aggregator both pass" — the max-aggregator fails at 1.0.

### Pareto Front Status

```
seed  monthly_sharpe  max_drawdown  calmar  pbo      n_trades  max_concentration_pct
42    0.2343          29.1986       0.2696  0.0892   102       66.08
123   0.5394          27.7375       0.6562  0.0892   79        55.83
```

- Seed 123 dominates seed 42 on Sharpe, MaxDD, Calmar, concentration (better on 4 of 6 metrics)
- Seed 42 beats seed 123 on n_trades (102 > 79) only
- Neither strictly dominates: **both are on the Pareto front**
- **Gate 10 (2-seed rule, both Sharpe > 0): PASS** — seed 42: +0.2343, seed 123: +0.5394

## Bootstrap Framing (User Directive)

Per `feedback_v3_iter018_baseline_bootstrap.md` (established mid-run): iter-v3/018 ALWAYS establishes BASELINE_V3.md regardless of gate outcomes — v3 has no formal multi-seed baseline yet and a bootstrap is necessary to anchor the next 10 EXPLORATIONs.

Verdict pre-classification: **CONFIRMATION-MERGE-BOOTSTRAP**
- All gates PASS → would be `CONFIRMATION-MERGE (full)` — NOT triggered (5 gates fail)
- Any FAIL → `CONFIRMATION-MERGE-BOOTSTRAP` with failed gates documented as outstanding constraints

**CONFIRMATION-MERGE-BOOTSTRAP** is the correct verdict. Baseline values to be written to BASELINE_V3.md:
- IS monthly Sharpe: +0.3788 (2-seed mean from seed_summary.json)
- OOS monthly Sharpe: +0.3869 (2-seed mean from seed_summary.json)
- Primary seed (42) comparison.csv: IS=+0.4563, OOS=+0.2343
- DSR: 0.0, PBO: 0.0892, PSR: 0.9936

Failed gates as remediation targets for next 10 EXPLORATIONs (iter-v3/019–028):

| Gate | Observed | Target | Required lift |
|---|---|---|---|
| IS Sharpe ≥ +1.0 | +0.3788 (mean) | ≥ +1.0 | +0.62 |
| OOS Sharpe ≥ +1.0 | +0.3869 (mean) | ≥ +1.0 | +0.61 |
| DSR > 0.95 | 0.0 | > 0.95 | requires observed_sr > 3.37 at n_trials=1500 — structural |
| Top-symbol conc ≤ 30% | 66.08% (TRX, seed 42) | ≤ 30% | -36pp on dominant symbol |
| Bundle OOS trades ≥ 130 | 102 (seed 42), 79 (seed 123) | ≥ 130 per seed | +28 to +51 |
| PBO max-agg < 0.4 | 1.0 (TRX/2022 Q4 cells) | < 0.4 | structural — TRX 2022 regime |

## 10-Seed Validation Status

Per `feedback_seed_validation.md`: 10-seed pre-MERGE concentration validation (mean Sharpe > 0, ≥7/10 profitable) is required before MERGE. Gates 1 and 2 fail decisively (IS/OOS Sharpe both < 0.5), so the 10-seed run is NOT triggered for this iteration. Gate 9 status: NOT TRIGGERED.

**Clarification request for QR (diary item)**: `feedback_seed_validation.md` specifies "10 seeds" but `feedback_outer_seed_cap_2_v3.md` caps v3 CONFIRMATION at 2 outer seeds. The 10-seed rule was established for v1/v2. For v3, does "10-seed pre-MERGE validation" mean (a) 10 outer seeds (contradicts the v3 2-seed cap), (b) the 10 inner models per cell (already satisfied by 2 outer × 5 inner = 10), or (c) a separate low-cost sanity run at --seeds 10 --n-trials 5? QR should clarify before next CONFIRMATION attempt.

## Anomaly Notes (Trade Row Spot-Check)

Spot-checked 10 random rows from `reports-v3/iteration_v3-018/out_of_sample/trades.csv`. All entries showed consistent entry/exit/PnL arithmetic, exit_reason values (timeout/tp/sl), and weight_factor values in the expected 0.3–1.0 range (vol scaling active). No anomalies detected.

The `comparison.csv` per_symbol section shows LDOUSDT concentration_pct = -130.05 — this is expected arithmetic when LDO net weighted_pnl is negative (-10.24) and total PnL is positive (+7.87): -10.24/7.87 = -130%. This is not a bug; it is the signed concentration formulation used when a symbol drags total PnL negative.

## Pre-Registered Failure Mode Prediction vs Actuals

From Section 7 of the brief:

| Prediction | Predicted P | Actual outcome | Calibration |
|---|---|---|---|
| P1: bundle OOS trades < 130 (P=10%) | 10% | **REALIZED** (102 per seed 42, 79 per seed 123) | calibration miss — P was too low |
| P2: LDO concentration does NOT compress > 50% (P=15%) | 15% | PARTIALLY — LDO flipped NEGATIVE (not concentrated); TRX became dominant | outcome differs from prediction mechanism |
| P3: PBO max-aggregator ≥ 0.99 (P=15%) | 15% | **REALIZED** (max=1.0 in TRX/2022-Q4) | calibrated correctly |
| P4: wall-clock > 4h (P=20%) | 20% | **REALIZED** (4.54h) | calibrated correctly |
| P5: 10-seed validation fails (P=10%) | 10% | NOT RUN (gates 1+2 fail) | n/a |
| P6: DSR < 0.95 (P=15%) | 15% | **REALIZED** (DSR=0.0) | calibration: P was too low — DSR=0 was structurally near-certain |
| P7: CONFIRMATION-MERGE (P=35%) | 35% | NOT REALIZED | calibration MISS — over-confident in single-seed holdout |
| P8: NO-MERGE-FRAGILITY — LDO > 30% (P=20%) | 20% | NOT REALIZED in predicted form — instead NO-MERGE-METHODOLOGY on Sharpe floors | outcome category correct but mechanism different |
| P9: IS/OOS Sharpe below floors (P=10%) | 10% | **REALIZED** (IS=+0.38, OOS=+0.39, both < 1.0) | calibration MISS — P was too low |

Key calibration lessons for diary: The QR's pre-registered MERGE pathway probability of 35% was too high. The dominant failure mode was P9 (Sharpe floors missed) which was assigned only 10%. The single-seed result (+1.0/+2.7) was a favorable lottery that multi-seed correctly deflated.

## Implications for Next 10 EXPLORATIONs (iter-v3/019–028)

All future EXPLORATIONs anchor against iter-v3/018 multi-seed baseline (+0.38 IS / +0.39 OOS mean), NOT against iter-v3/013 single-seed (+1.01 / +2.70). The 13-feature stack at n_trials=50 produces a very weak signal in isolation.

Recommended axis priorities (per `feedback_structural_over_knob_exploration.md`):

| Priority | Axis | Rationale |
|---|---|---|
| HIGH | NEW feature families | 13-feature stack underperforms under multi-seed; adding genuinely predictive features is the primary lever to lift IS/OOS Sharpe above 1.0 |
| HIGH | Concentration architecture | TRX 66% OOS concentration (seed 42) must be addressed — position-sizing normalization or per-symbol max-allocation cap |
| MEDIUM | Labeling revisit | Fixed-horizon alternatives or dynamic ATR multiplier tuning may improve signal clarity per trade |
| MEDIUM | Universe expansion | Adding a 4th symbol dilutes per-symbol concentration; risk: adds complexity and may introduce new lottery |
| LOW | Risk-gate calibration | Gates are mature; further tuning unlikely to move Sharpe by 0.5+ units |
| LOW | DSR architectural fix | DSR > 0.95 is structurally blocked by n_trials=1500 at current trade count; requires IS trade count >300+ or Sharpe >3.4 — likely only achievable via new features |

**The 10-EXPLORATION cadence clock restarts at iter-v3/019.** The first EXPLORATION post-BOOTSTRAP should target the highest-leverage structural axis (new features or concentration normalization) per the recommendation above. The next CONFIRMATION iteration should run with --seeds 2 --n-trials 30 (not 50) to avoid the 4h wall-clock cap exceedance.

## Status

OVERALL=READY-FOR-CRITIC

Verdict pre-classification: CONFIRMATION-MERGE-BOOTSTRAP
Failed gates: 5 confirmed (IS Sharpe, OOS Sharpe, DSR, top-symbol concentration, OOS trade count)
Gate 5 PBO max-aggregator: FAIL (max=1.0)
Gate 10 Pareto 2-seed both-positive: PASS (seed 42: +0.234, seed 123: +0.539)
