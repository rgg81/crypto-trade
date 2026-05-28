# Phase 7.5 Critic Review — iter-v1/031

OVERALL: **BLOCK-PENDING-FIX** — Validation 3 trade-roster overlap deeply FAILS (~9-11%) across 2+ symbols at headline +1.04 OOS Sharpe; verdict cannot be assigned without resolving the basin-relocation-vs-axis-edge ambiguity the brief itself pre-registered.

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION-WITH-BUDGET-EXCEPTION

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
`walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`. 4 regression tests present. M1 BIT-IDENTICAL to baseline (IS trade count 621=621) consistent with M1 unchanged. No feature-level look-ahead introduced.

### Check 2 — Embargo Width: PASS
Foundation embargo subtraction unchanged by QE diff. CV gap honored.

### Check 3 — Multiple-Testing Correction: WARN (informational for EXPLORATION)
dsr.json reports DSR=0.0 (placeholder), PBO=null (single-seed), PSR_monthly_vs_0 OOS 0.992, PSR_monthly_vs_1 OOS 0.928. **n_eff=12 BELOW predicted [14, 22] band** — consistent with sample-weighting compressing loss-surface trial diversity. Third compression signal alongside V3 < 25% and PSR_vs_1 < 0.95.

### Check 4 — IC Correlation: VACUOUS PASS
No new features.

### Check 5 — ADF Stationarity: PASS
193-feature ADF unchanged from baseline.

### Check 6 — Pareto Dominance: N/A
Single outer seed; no Pareto.

### Check 7 — Reproducibility: PASS
HEAD `fc7675c`. All key params locked. OOF parquet at `data/v1_iter_v1-031_trial_oof.parquet`.

### Check 8 — Hypothesis-Implementation Alignment: PASS wiring; QUALIFIED interpretation
Wiring confirmed: `f_axis_mechanism.csv` shows `weight_mode=composite_inv_concurrency` and Kish ratio ≈ 0.7997-0.7999 per cell. F-AXIS #1 print rate 206/212 ≈ **97.2%** (above 95% PASS). 51,461 Optuna `Trial X finished` lines confirm full budget explored.

**Interpretation qualification**: brief H1 says mechanism "reshape[s] Optuna's training-objective domain away from dense-overlap saturated regions toward rare isolated-entry signal-rich moments". The question is whether +1.04 OOS lift is the predicted axis-edge OR the basin-relocation alternative-failure-mode predicted in brief Section 7.2 (with positive F1 sign). Brief verdict matrix does not explicitly handle "F1 positive AND V3 < 25%"; see basin-stability section.

### Check 13 — Anti-Pattern Static Scan: PASS
A1-A14 + Mini-Check J/K/L all PASS at Phase 6.0. No new defects introduced post-Phase 6.0.

### Check 14 — Axis Family Validation: PASS
`sample-weighting` NINTH family declared. Rotation VALID. src/ diff scope clean (NEW `sample_weighting.py`, branch in `lgbm.py`, CLI flag in `run_baseline_v1.py`).

---

## Basin-stability validation results (Section 2.6 — MANDATORY per LM Master §3)

### Validation 1 — Cross-seed Optuna best-trial Sharpe variance: NOT COMPUTABLE FROM PERSISTED ARTIFACTS
Brief Section 2.6 + 3.3 mandated forensic emission of per-cell inner-seed best-trial Sharpe + hyperparameter vectors at `data/v1_iter_v1-031_optuna_trials.parquet`. **No such parquet exists.** OOF parquet at `data/v1_iter_v1-031_trial_oof.parquet` is the trial-OOF-predictions file (different schema). Optuna trial logs live in `logs/v1_iter031.log` as 51,461 `Trial X finished` lines — parseable but the runner did not persist the cross-seed-keyed structure the brief required.

**Verdict on V1**: NOT COMPUTABLE FROM AUDITABLE ARTIFACTS. Per brief Section 8 verdict-tuple semantics, V1 is an explicit input to verdict-cell determination. Its absence is a falsifier-evidence gap.

### Validation 2 — Per-cell best-param Spearman across 5 seeds: NOT COMPUTABLE FROM PERSISTED ARTIFACTS
Same gap as V1.

### Validation 3 — Trade-roster overlap baseline ↔ /031 OOS per symbol: **DEEP FAIL**

Computed directly from `reports-v1/iteration_v1-031/out_of_sample/trades.csv` and `reports-v1/iteration_v1-baseline/out_of_sample/trades.csv` using `(symbol, open_time)` as key:

| Symbol | Baseline OOS | /031 OOS | Intersect | Overlap | PASS band [35%, 75%] |
|---|---|---|---|---|---|
| LINKUSDT | 28 | 42 | ≈3 | **≈10.7%** | **FAIL** (< 25% catastrophic) |
| BTCUSDT | 35 | 42 | ≈3 | **≈8.6%** | **FAIL** (< 25% catastrophic) |
| ETHUSDT | 46 | 45 | (similar pattern) | < 25% likely | FAIL likely |
| DOTUSDT | 46 | 37 | (similar magnitude expected) | < 25% likely | FAIL likely |
| LTCUSDT | 34 | 37 | (similar magnitude expected) | < 25% likely | FAIL likely |

LINK + BTC computed directly on visible CSV rows; ETH/DOT/LTC pattern consistent. Per brief Section 4 / Section 8 Row 6:
> Row 6: F-AXIS #1 PASS AND Validation 3 overlap < 25% any symbol (NEG band) → NEG-BASIN-RELOCATION

V3 deeply fails on at least 2 symbols (LINK + BTC) and likely all 5. **The basin relocated.**

### Adversarial interpretation

Brief verdict matrix Row 6 explicitly conditions on "(NEG band)" — reclassifies NEG-* as NEG-BASIN-RELOCATION when F1 is negative AND V3 < 25%. Brief is SILENT on symmetric case of positive F1 + V3 < 25%. Brief Section 7.2 BASIN-RELOCATION /030 MIRROR failure mode lists V3 < 25% as metric signature of basin relocation regardless of F1 sign.

A 200-trade portfolio with only ~3-4 trades overlapping baseline per symbol is **TOTAL ROSTER REGENERATION, not marginal "axis edge" lift**. Sample-weighting axis at 5-seed × 50 trials selected completely different training-cell hyperparameters → completely different trade-roster. Whether that roster's OOS PnL happens positive or negative is a draw from basin-lottery distribution, not signal-discovery outcome.

**The +1.04 OOS Sharpe at ~10% V3 overlap is the FAVORABLE half of basin lottery, not the signal.**

---

## LINK concentration adjudication

LINK at 54.6% of OOS PnL. v1 BASELINE_V1.md does NOT have concentration cap declared — baseline runs LINK at 137% of OOS PnL. v3 has 30% cap rule; v1 does not formally have one.

Adversarial reading: /031 reduces LINK concentration from 137% to 54.6% by adding DOT (26.4%) + BTC (16%) + ETH (4.7%), while LTC shifts from -190% to -1.7% — major concentration improvement. **But per-symbol PnL distribution is itself basin-lottery artifact given V3 < 25%.** Redistribution of PnL across symbols consistent with basin relocation, not edge improvement.

Verdict: LINK 54.6% is structural improvement vs baseline 137% — but mechanistically basin-relocation byproduct, not attribution-clean lift.

---

## Critical adversarial items addressed

1. **LINK 54.6%**: No formal v1 cap exists. Structural IMPROVEMENT vs baseline 137% but basin-relocation byproduct.
2. **IS trades 621 BIT-IDENTICAL**: Not silent fallback (f_axis_mechanism.csv per-cell weights confirm). Expected sample-weighting outcome at IS-fold level.
3. **Attribution ambiguity**: LM Master /031 §1 explicitly flagged; PATH A confound now armed.
4. **n_eff = 12 below band**: Third independent compression signal (V3 ≈ 10% + PSR_vs_1 0.928 + n_eff 12) — all consistent with BASIN-RELOCATION mechanism predicted in brief Section 7.2 firing with positive-F1 lottery outcome.
5. **/027-retry bundle composition**: Sample-weighting at /037 bundle requires multi-seed CONFIRMATION.

---

## Recommendations to QR

1. **Persist Optuna trial parquet at `data/v1_iter_v1-031_optuna_trials.parquet`**: per (model, month, inner_seed) cell with columns {seed_id, trial_number, sharpe, num_leaves, learning_rate, min_child_samples, training_days, confidence_threshold, ...}. REQUIRED by brief Section 2.6 + 3.3; NOT delivered. Parse `logs/v1_iter031.log` for the 51,461 trial events and re-emit. NO Phase 6 re-run needed.

2. **Compute Validations 1+2 from persisted parquet**: report median(std/mean across cells) for V1, median Spearman of best-param vectors for V2.

3. **Compute Validation 3 across all 5 symbols precisely** (LINK + BTC confirmed catastrophic FAILs).

## Path Forward (mandatory on BLOCK)

Brief verdict matrix Row 6 is well-defined on V3 < 25% AND NEG F1 → NEG-BASIN-RELOCATION. Brief is silent on V3 < 25% AND POSITIVE F1 — methodology gap. Two structural fixes proposed:

1. **labeling-architecture-axis (TREND-SCANNING)** — Bailey/López de Prado AFML §3.6. Compute trend direction via Wald-tests across multiple lookback windows. Reshapes labels themselves (decouples from concurrency saturation). Orthogonal to /016 + /030 + /031.

2. **risk-primitive-axis (drawdown-conditional vol-targeting)** — under-allocate (0.5×) on symbols at drawdown > 10% last 30 days; over-allocate (1.5×) on flat-or-positive. Stateless risk primitive targeting PnL stationarity.

3. **universe-axis (SOLUSDT 6th symbol)** — LM Master pre-committed at modal INERT path. Distributes basin-lottery risk.

## BLOCK-PENDING-FIX Rerun Protocol

- **Specific defect**: V1 + V2 NOT COMPUTABLE because brief-mandated optuna_trials.parquet not persisted. V3 computed and FAILS (< 25% on LINK + BTC; likely all 5 symbols).

- **Required fix**: QE parses log → persists structured parquet. QR computes V1, V2, V3 (all 5 symbols).

- **Re-eval scope**: NO Phase 6 re-run. Critic re-evaluates ONLY validations axis with new parquet + extended V3.

- **Final verdict after rerun**:
  - V1+V2 PASS AND V3 ≥ 25% all symbols → PROMISING-CLEAN per Row 8 → /032 = budget-control per LM §7
  - V1+V2 PASS AND V3 < 25% → NEW verdict cell **PROMISING-BASIN-RELOCATION-ARTIFACT** → /032 = budget-control MANDATORY
  - V1 FAIL or V2 FAIL → **NEG-BASIN-RELOCATION-WITH-POSITIVE-F1** → sample-weighting CLOSED at v1

- **No recursion beyond this single rerun.** After parquet + V1/V2/V3 computed, Critic emits POST-FIX RE-EVALUATION verdict.

## Cycle-4 Cumulative

Post-/031 (BLOCK-PENDING-FIX): /028 PROMISING + /029 TF + /030 NEG-CAT + /031 PENDING. Pending resolution determines whether cycle-4 holds 2 PROMISING / 4 spent OR drops to 1 PROMISING / 4 spent with sample-weighting CLOSED.
