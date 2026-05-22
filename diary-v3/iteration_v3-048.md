# Iteration iter-v3/048 — Diary

## Decision: EXPLORATION-NEGATIVE — clean PATH C (NEW universal engineered feature axis CLOSED for cycle 3)

iter-v3/048 = NINTH iteration of cycle 3 (cycle 3 #9 of 10; iter-v3/049 remains before iter-v3/050 SECOND v3 CONFIRMATION). Single new EXPLORATION axis on top of the iter-v3/045 PROMISING bundle + iter-v3/047 primitive 10 carry-forward state: ADD `vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + 1e-6)` as 15th column in V3_FEATURE_COLUMNS_TOP_N. Composed Category 2 feature (canonical Sharpe-like risk-normalized momentum; built on rank-1 TRX importance feature `range_realized_vol_50`). Per QR EDA `analysis/iteration_v3-048/synthesis.md` + `candidate_axes_ranking.md` (SHA `a230cd1`), all direction-asymmetric and regime-conditional axes were EDA-falsified BEFORE backtest (TRX SHORT regime gate fails at all 5 thresholds; ALGO LONG/LDO SHORT face iter-v3/039 OOS-divergence pattern); cycle 3 plan Axis 1 (NEW universal engineered feature) was the QR-recommended residual.

Result: **IS Sharpe +0.3118 / OOS Sharpe +0.3746** (single-seed=42, ENSEMBLE_SIZE=5, n_trials=35, EXPLORATION-spec, `--clean-oof` guardrail active). Pre-registered PATH C-clean fires unambiguously on BOTH locked thresholds (Section 8): IS Sharpe Δ -0.43 < -0.10 AND OOS Sharpe Δ -3.15 < -0.30 vs iter-v3/045 single-seed anchor (+0.7459 / +3.5259). Per QR locked Section 8 thresholds (non-renegotiable per cycle 3 discipline) the verdict path resolved as **PATH C-clean — NEGATIVE-clean**.

`vol_normalized_ret_5d` ranks **13-15/15 across all 4 symbols** (BCH 14/15, LDO 14/15, TRX 15/15, ALGO 13/15) with importance 53/56/82/97 — the model did not learn the new feature beyond bottom-tier utilization. Cycle 3 NEW universal engineered feature axis is **CLOSED** per pre-registered saturation rule (5 attempts: iter-v3/035 fracdiff_d05_close, iter-v3/041 universal pruning, iter-v3/043 efficiency_ratio_50, iter-v3/044 reverted regime_momentum_signed_3d, and now iter-v3/048).

**Material side-finding**: iter-v3/048's `--clean-oof` single-process run produced n_trials=700 / 110MB OOF parquet IDENTICAL to iter-v3/047 — directly FALSIFYING the iter-v3/047 "5-process multi-run-stochasticity contamination" attribution. The 5x OOF parquet duplication is **structural** (per-ensemble-seed namespace collision in shared parquet at `optimization.py:425-430` — no `seed` column in OOF schema), not multi-process pollution. The new catalog NEGATIVE subtype `NEGATIVE-multi-run-stochasticity-contaminated` introduced at iter-v3/047 closeout has zero supporting cases and is **RETIRED from taxonomy**. The orchestrator-level memory rule `feedback_v3_single_seed_frozen_baseline.md` was REVISED 2026-05-09 per Critic recommendation to remove the cross-process-OpenMP qualifier and replace with the corrected feature-change-breaks-frozen-baseline attribution.

Per QR + Critic + Engineering recommendations: NO re-run (peeking-at-OOS violation per `feedback_no_cheating.md`); accept-NEGATIVE; iter-v3/049 = NEW EXPLORATION axis (cycle 3 #10 of 10), QR-EDA-driven, **MUST be a different axis category** per saturation rule; iter-v3/050 SECOND v3 CONFIRMATION carries primitive 10 + iter-v3/045 ATR config UNCHANGED forward as the EXPLORATION-PROMISING bundle. The CONFIRMATION QR brief MUST still note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 multi-seed run is the first OOS test of primitive 10 in clean conditions" (the iter-v3/047 misdiagnosis correction does NOT change this — primitive 10 IS-only validation basis remains the original premise).

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Adding `vol_normalized_ret_5d = ret_5d / (range_realized_vol_50 + 1e-6)` as a 15th feature in V3_FEATURE_COLUMNS_TOP_N (Category 2 composed feature; ON TOP of regime_momentum_signed_5d) gives the LightGBM models a risk-normalized momentum signal they cannot represent at depth-3-5 splits. The composed feature uses range_realized_vol_50 (rank-1 importance for TRX, the IS-axis-bottleneck symbol with flat importance distribution; rank-3 BCH, rank-4 ALGO). Expected effect: bundle IS Sharpe lift +0.05 to +0.15 (single-seed n_trials=35) via better split-quality on the toxic-direction trades that the model currently can't separate from healthy ones; bundle OOS Sharpe regression within [-0.10, +0.30] band (uncertain — the cycle 3 base rate for NEW engineered features is poor [iter-v3/043, /044, /035 all NEGATIVE], but `vol_normalized_ret_5d` has stronger primitive-importance support than those candidates)."

**Predicted bands (locked in brief Section 4):**
- IS Sharpe: [+0.85, +1.15] median +0.92 (vs iter-v3/045 anchor +0.7459)
- OOS Sharpe: [+3.30, +3.85] (regression up to -0.30 OR lift up to +0.30) (vs iter-v3/045 anchor +3.5259)
- vol_normalized_ret_5d importance rank @ TRX: 5-8 (TRX uses range_realized_vol_50 at rank 1)
- vol_normalized_ret_5d importance rank @ BCH+ALGO+LDO: 8-12
- Bundle IS trade count: 250 → 240-260 (±4%)
- IS-OOS daily Sharpe ratio: ∈ [0.5, 2.0] (band falsifier per `feedback_v3_engineered_features_dont_stack.md`)

**Spec (locked in brief Section 0.5):**
- ADD `compute_vol_normalized_ret_5d` to `engineered_v3.py` (parallel to existing `compute_regime_momentum_signed_5d`)
- ADD to V3_FEATURE_COLUMNS_TOP_N (14 → 15)
- 5 adversarial tests in `tests/features_v3/test_vol_normalized_ret_5d.py` PASS at setup commit `c69fdaa`
- Re-generate v3 features for all 4 symbols (BCH, LDO, TRX, ALGO)
- Carry-forward state from iter-v3/047 UNCHANGED:
  - V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)}
  - block_long_for = ("BCHUSDT",) — primitive 10 ON
  - block_short_for = ()
  - V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols
  - V3_FEATURES_PER_SYMBOL = {} (empty)
  - REQUIRED_GAP = 88 = (21+1)*4
- ITERATION_LABEL = "v3-048"
- Runner: `uv run python run_baseline_v3.py --seeds 1 --clean-oof`

## Headline Numbers

### Bundle metrics (single-seed, ENSEMBLE_SIZE=5)

| Metric | iter-v3/045 anchor | iter-v3/047 prior | **iter-v3/048** | Δ vs iter-v3/045 | Verdict |
|---|---:|---:|---:|---:|---|
| **IS monthly Sharpe** | +0.7459 | +0.4872 | **+0.3118** | **-0.43** | FAR BELOW band [+0.85, +1.15]; PATH C IS regression fires |
| **OOS monthly Sharpe** | +3.5259 | +1.1675 | **+0.3746** | **-3.15** | FAR BELOW band [+3.30, +3.85]; PATH C OOS regression fires |
| Daily Sharpe IS | +1.3115 | — | +0.6269 | -0.68 | regression |
| Daily Sharpe OOS | +4.2020 | — | +0.5996 | -3.60 | regression |
| OOS/IS monthly ratio | 4.73 | 2.40 | 1.20 | -3.53 | within positive range; not suspicious |
| **IS-OOS daily Sharpe ratio** | 3.20 | — | **0.96** | — | **within band [0.5, 2.0] — clean regression NOT NEGATIVE-SUSPICIOUS** |
| IS Trades | 250 | 201 | 204 | -46 | -18.4% (vs 045 incl. primitive 10 effect; +1.5% vs 047 carry-forward) |
| OOS Trades | 119 | 92 | 95 | -24 | -20% (vs 045); +3.3% vs 047 |
| IS MaxDD | 66.06% | 60.97% | 38.04% | -28.02pp better | improvement (mechanical from fewer trades) |
| OOS MaxDD | 13.26% | 20.21% | 19.62% | +6.36pp worse | regression |
| OOS Calmar | 7.31 | 2.30 | 0.55 | -6.76 | regression |
| IS Profit factor | 1.21 | 1.20 | 1.10 | -0.11 | regression |
| OOS Profit factor | 1.68 | 1.40 | 1.08 | -0.60 | regression |
| OOS Top-symbol concentration | 54.77% (ALGO) | 64.43% (TRX) | 44.88% (max) | — | improvement (mechanical from LDO collapse) |
| DSR | 0.0 | 0.0 (n_trials=700) | 0.0 (n_trials=700 STRUCTURAL) | structural | INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md` |
| PBO | 0.0782 | 0.0939 | 0.1339 | +0.056 | acceptable (gate 0.4) |
| PSR | 1.0 | 1.0 | 0.9971 | -0.003 | acceptable |
| n_trials reported | 140 | 700 | 700 | +560 | STRUCTURAL: 4 syms × 5 ensemble × 35 trials/seed; CORRECT for ENSEMBLE_SIZE=5 |
| n_effective_trials | 19 | 18 | 18 | -1 | acceptable |

### Per-symbol IS decomposition

| Symbol | iter-v3/045 trades | iter-v3/047 trades | **iter-v3/048 trades** | WR 045 | **WR 048** | net_pnl_pct 045 | **net_pnl_pct 048** | Δ pnl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALGO | 53 | 51 | 51 | 39.6% | 41.2% | -34.05% | -37.36% | **-3.31pp** |
| BCH | 94 | 50 | 57 | 38.3% | 42.1% | +23.62% | +45.72% | **+22.10pp** |
| LDO | 18 | 15 | 16 | 55.6% | 43.8% | +54.55% | +16.94% | **-37.61pp** |
| TRX | 85 | 85 | 80 | 34.1% | 31.2% | -7.28% | -24.26% | **-16.98pp** |

BCH IS lifted modestly (+22.10pp vs 045; primitive 10 carry-forward continues to suppress LONGs and Optuna picked 7 more BCH SHORTs than iter-v3/047). TRX IS collapsed (-16.98pp) — ironically the symbol the new feature was designed to address (range_realized_vol_50 rank-1 utilization). LDO IS collapsed (-37.61pp) — small-sample symbol where adding the 15th feature confused Optuna's hyperparameter search. ALGO IS slightly worse (-3.31pp).

### Per-symbol OOS decomposition

| Symbol | iter-v3/045 trades | iter-v3/047 trades | **iter-v3/048 trades** | WR 045 | **WR 048** | weighted_pnl 045 | **weighted_pnl 048** | Δ pnl |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ALGO | 22 | 13 | 16 | 63.6% | 43.8% | +53.12 | +16.30 | **-36.82** |
| BCH | 38 | 21 | 22 | 39.5% | 45.5% | +11.31 | +7.88 | **-3.43** |
| LDO | 13 | 12 | 11 | 53.8% | 27.3% | +9.34 | -25.51 | **-34.85** |
| TRX | 46 | 46 | 46 | 52.2% | 43.5% | +23.23 | +12.14 | **-11.09** |

**ALL 4 SYMBOLS REGRESSED OOS.** Combined OOS swing -86.19 weighted_pnl. The new feature harmed every OOS symbol contribution; LDO collapsed most severely (-34.85, 27.3% WR is one of the worst LDO OOS profiles in the v3 catalog). No symbol improved OOS.

### Pre-registered Falsifier Audit (brief Section 4 + Section 8 — locked thresholds)

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe band | [+0.85, +1.15] | +0.3118 | **FAR BELOW band — FIRES** |
| IS Sharpe Δ vs 045 | ≥ +0.10 | -0.43 | **FALSIFIED** |
| OOS Sharpe band | [+3.30, +3.85] | +0.3746 | **FAR BELOW band — FIRES** |
| OOS Sharpe Δ vs 045 | ≥ -0.10 | -3.15 | **FALSIFIED** |
| IS-OOS daily Sharpe ratio | [0.5, 2.0] | 0.956 | **PASS (within band — clean regression NOT NEGATIVE-SUSPICIOUS)** |
| vol_normalized_ret_5d rank | ≤ 10 in ≥2 symbols | 13-15 ALL syms | **FAILS (all bottom-2)** |
| vol_normalized_ret_5d importance | ≥ 30 in ≥2 symbols | 53/56/82/97 | PASS (relaxed Falsifier per IC carve-out for Category 2 composed features) |
| IS trade count delta vs 045 | ≤ 15% | -18.4% | OUTSIDE BAND (incl. primitive 10 carry-forward effect) |
| IS trade count delta vs 047 | ≤ 15% (carry-forward base) | +1.5% | **PASS (within band — feature pipeline intact)** |
| Bundle IS Sharpe Δ | ≥ +0.10 | -0.43 | **FALSIFIED — PATH C fires** |
| Bundle OOS Sharpe Δ | ≥ -0.10 | -3.15 | **FALSIFIED — PATH C fires** |

### Pre-registered Path Verdict (brief Section 8 — non-renegotiable)

| Path | Threshold | Observed | Trigger |
|---|---|---|---|
| PATH A (PROMISING-clean) | IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ -0.10 AND vol_normalized_ret_5d rank ≤ 10 in ≥2 syms AND IS-OOS daily ratio ∈ [0.5, 2.0] | IS Δ -0.43 < +0.10; OOS Δ -3.15 < -0.10; rank 13-15 ALL syms; daily ratio 0.96 within band | NO |
| PATH B (PROMISING-INERT) | rank ≥ 11 in ALL 4 syms AND IS Δ ∈ [-0.10, +0.10] AND OOS Δ ∈ [-0.20, +0.20] | rank ≥ 11 in ALL 4 syms PASS; IS Δ -0.43 outside [-0.10, +0.10]; OOS Δ -3.15 outside [-0.20, +0.20] | NO |
| **PATH C-clean (NEGATIVE-clean)** | IS Sharpe Δ < -0.10 OR OOS Sharpe Δ < -0.30 | **IS Δ -0.43 < -0.10 AND OOS Δ -3.15 < -0.30** | **YES — both criteria fire** |
| PATH C-suspicious (NEGATIVE-SUSPICIOUS-OOS) | IS-OOS daily Sharpe ratio outside [0.5, 2.0] | 0.956 within band | NO |

**Brief verdict: PATH C-clean — EXPLORATION-NEGATIVE clean.** This is a genuine IS+OOS regression, NOT the iter-v3/026/027 anti-pattern (the IS-OOS daily Sharpe ratio is 0.96, well within the [0.5, 2.0] band).

## What Worked

- **EDA-driven axis selection paid off methodologically** even with NEGATIVE outcome. The QR EDA at `analysis/iteration_v3-048/multi_axis_diagnosis.py` + `regime_gate_validation.py` + `regime_threshold_sweep.py` (SHA `a230cd1`) correctly FALSIFIED the regime-conditional TRX SHORT axis BEFORE backtest (saving an EXPLORATION slot per cycle 3 cadence discipline). All 5 thresholds tested (T1 narrow → T5 vol_z-only) cost OOS edge. The 5-axis ranking (TRX SHORT, ALGO LONG, LDO direction, BCH SHORT residual, NEW engineered feature) correctly identified that direction-asymmetric and per-symbol axes are exhausted in cycle 3.

- **Implementation hygiene clean.** All 12 standard methodology checks PASS or N/A per Critic FINAL `55fbadb`:
  - Check 1 (Look-ahead) PASS — past-only construction verified by adversarial test
  - Check 2 (Embargo width) PASS — REQUIRED_GAP=88 unchanged
  - Check 4 (IC) PASS engineered-feature carve-out — |IC|=0.892 with regime_momentum_signed_5d acknowledged as construction artifact; importance ≥30 binding gate satisfied (53/56/82/97 ≥ 30)
  - Check 5 (ADF stationarity) PASS — all 4 symbols stationary by IS-window start
  - Check 6 (Pareto) N/A single-seed
  - Check 7 (Reproducibility) PASS — setup `c69fdaa`, brief backfill `4c7ff26`, 5 adversarial tests pass, spot-check OOS row 2 PnL math reconciles to CSV
  - Check 8 (Hypothesis-Implementation alignment) PASS — zero scope creep, single-axis discipline preserved
  - Checks 9-12 PASS or N/A
  - 5 adversarial tests in `tests/features_v3/test_vol_normalized_ret_5d.py` PASS at setup commit
  - Pre-commit SHAs: EDA `a230cd1`, brief `81af783`, setup `c69fdaa`, Phase 5.5 gate `34c97c5`, brief backfill `4c7ff26`, engineering report `a068edd`, Critic FINAL `55fbadb` — full audit chain present

- **`--clean-oof` guardrail (SHA `6a216b5`) functioned as designed.** Single-process invocation produced n_trials=700 / 110MB OOF parquet — NOT a contamination artifact. The guardrail correctly prevents a true multi-run scenario (engineer re-runs same iteration accidentally), even though the original motivation (5-process pollution explaining iter-v3/047 drift) has now been falsified.

- **Predicted behavioral effect partially matched observation.** Brief Section 2.11 predicted bundle IS trade count 250 → 240-260 (±4%); observed 204 (-18.4% vs 045). The discrepancy is attributable to primitive 10 carry-forward (which iter-v3/045 anchor did NOT have); compared to iter-v3/047 carry-forward base (201), iter-v3/048 trade count is +1.5% — well within the ±15% Sub-fix 4 cascade-effect falsifier band. Feature pipeline intact, no cascade effect from the new feature.

- **QR EDA discipline maintained per `feedback_v3_axis_selection_quant_discipline.md`.** Brief Section 2 contains 11 sub-sections, 6 numerical tables, falsifiers with explicit thresholds, behavioral-effect predictor, regime-conditional axis falsification at all 5 thresholds. Brief Section 10 (QR Audit Trail) cites EDA SHA `a230cd1` explicitly. Pre-registered classification (PATH A/B/C-clean/C-suspicious) covered the observed outcome unambiguously.

## What Failed

- **Pre-registered PATH C-clean fires unambiguously on BOTH locked thresholds.** Bundle IS Sharpe Δ -0.43 < -0.10 AND OOS Sharpe Δ -3.15 < -0.30. Per QR locked Section 8 thresholds (non-renegotiable), verdict path resolved as PATH C-clean — NEGATIVE-clean.

- **vol_normalized_ret_5d ranks 13-15/15 across ALL 4 symbols** (BCH 14/15 / 53.0; LDO 14/15 / 56.2; TRX 15/15 / 82.4; ALGO 13/15 / 96.8). Predicted importance rank @ TRX: 5-8 (FALSIFIED — observed 15/15, dead last). Predicted importance rank @ BCH+ALGO+LDO: 8-12 (FALSIFIED — observed 13-14). The model did not learn the new feature beyond bottom-tier utilization.

- **High pairwise IC with existing features confirms near-collinear redundancy.** Per `ic_matrix.csv` row 16 (vol_normalized_ret_5d):
  - `regime_momentum_signed_5d`: **|IC|=0.892** (BREACH of strict gate 0.7; carve-out applied per Category 2 composed feature)
  - `vwap_dev_20`: **|IC|=0.888** (BREACH)
  - `ema_spread_atr_20`: 0.670 (within gate, marginal)
  
  Both vol_normalized_ret_5d and regime_momentum_signed_5d share the `ret_5d` numerator by construction; LightGBM's depth-3-5 trees see them as redundant → both rank at the bottom together (regime_momentum_signed_5d itself ranks 14-15/15 in every symbol, equal to or below vol_normalized_ret_5d). The carve-out gate (importance ≥30) PASSES technically but the high-IC redundancy prevents the new feature from contributing differential signal.

- **ALL 4 OOS symbol contributions regressed.** ALGO -36.82, LDO -34.85, TRX -11.09, BCH -3.43 weighted_pnl. Combined OOS swing -86.19. LDO OOS WR collapsed to 27.3% (one of the worst LDO OOS profiles in v3 catalog).

- **TRX (the IS-axis bottleneck symbol the new feature was designed to address) WORSENED IS** -16.98pp (-7.28% → -24.26%). vol_normalized_ret_5d ranked dead last (15/15) for TRX. The composed feature did NOT break TRX's flat importance distribution — it joined the flat tail (top:bottom ratio 045: 2.5×, 048: 3.2× — barely changed). The hypothesis that "a NEW composed feature exposing risk-normalized momentum could give Optuna better split-quality on TRX" is FALSIFIED.

- **Cycle 3 NEW universal engineered feature axis CLOSED per pre-registered saturation rule.** 5 attempts: iter-v3/035 fracdiff_d05_close, iter-v3/041 universal pruning, iter-v3/043 efficiency_ratio_50, iter-v3/044 reverted regime_momentum_signed_3d, and iter-v3/048. The base rate is 0/5 successes. The only PROVEN engineered feature edge in v3 history remains regime_momentum_signed_5d (iter-v3/025 → iter-v3/028 CONFIRMATION-MERGE).

- **Cycle 3 engineered feature attempts at higher Optuna budget (n_trials=35) actively HARM OOS** per `feedback_v3_inert_features_at_higher_budget.md`. INERT features at rank 13-15/15 enlarge the Optuna search space without adding signal, causing convergence to lower-quality regions. Per Engineering report Anomaly Notes #1 and #2, LDO and TRX both saw IS regression directly attributable to confused Optuna search; ALGO and BCH less affected because they retained higher-quality search regions.

## iter-v3/047 Misdiagnosis Section (FORENSIC FINDING)

**The iter-v3/047 root-cause attribution is FALSIFIED by iter-v3/048 evidence.**

iter-v3/047 Critic FINAL `785500f` + diary documented a NEW NEGATIVE catalog subtype: `NEGATIVE-multi-run-stochasticity-contaminated`. The claimed mechanism was:
- "5 process invocations of iter-v3/047 single-seed config accumulated in `trial_oof_returns.parquet` (55.78M rows = 5.00× expected ~11M; 44.6M duplicate rows confirmed)"
- "LightGBM C++ OpenMP thread scheduling is NOT seeded by `random_state=seed` — each fresh process produces modestly different ALGO/LDO/TRX model weights"
- "The trades.csv reflects only the LAST of the 5 runs"

**iter-v3/048 evidence directly falsifies this:**

iter-v3/048 ran in single PID 38365 with `--clean-oof` (parquet truncated at start; verified no prior file). The same single PID grew the parquet monotonically 25MB → 49MB → 73MB → 89MB → 110MB during the in-process loop. Final parquet: 110MB / 55.78M rows / 5x duplicate-by-(trial_id,symbol,train_month,fold_idx,candle_open_time_ms) — **IDENTICAL** to iter-v3/047's parquet shape.

**True root cause of the 5x row duplication (STRUCTURAL, not contamination):**

The OOF parquet schema has no seed column: `(trial_id, symbol, train_month, fold_idx, candle_open_time_ms, oof_return)`. The optimization loop in `lgbm.py:456-481` iterates over `self.ensemble_seeds` (5 seeds for ENSEMBLE_SIZE=5). Each ensemble seed calls `optimize_and_train()` with its own Optuna study and writes trial_id 0-34 to the shared parquet via `optimization.py:425-430` (append-if-exists semantics). Since all 5 ensemble seeds use the same local trial_id counter (0-34), the 5 seeds produce 5 identical (trial_id, ...) key namespaces and 5x raw rows when concatenated.

Verification:
- Total rows: 55,779,535
- Duplicate rows (by 5-col key): 44,618,560
- Unique rows: 11,160,975
- Duplication factor: exactly 5.00x
- Unique rows match iter-v3/045 (ENSEMBLE_SIZE=1, no duplication): 11,155,545

n_trials=700 = 4 symbols × 5 ensemble seeds × 35 trials per seed is the **CORRECT structural count for ENSEMBLE_SIZE=5**, not a contamination artifact.

**True root cause of the iter-v3/047 OOS regression:**

Single-seed Optuna lottery variance on per-symbol independent searches. ALGO and LDO landed on hyperparameter configurations that produced lower OOS performance — exactly the same mechanism as ordinary single-seed EXPLORATION variance (and exactly the mechanism iter-v3/048 itself exhibits, just in a single-process clean run). This is NOT primitive 10 cross-symbol contagion; the trades.csv is the result of one process, not the LAST of 5.

**Implications (recorded as material corrections to the historical record):**

1. **iter-v3/047 catalog row label retroactively re-classified** from `NEGATIVE-multi-run-stochasticity-contaminated` to **`NEGATIVE-clean (single-seed Optuna lottery on non-target symbols; primitive 10 IS-validated)`**. The PATH C verdict stands (OOS Δ -2.36 fires the bundle-regression threshold); only the SUBCATEGORY label needs correction.

2. **`NEGATIVE-multi-run-stochasticity-contaminated` subtype RETIRED from taxonomy.** Zero supporting cases after iter-v3/048's forensic correction. Catalog taxonomy reverts to: `NEGATIVE-no-effect`, `NEGATIVE-redistribution`, `NEGATIVE-architecture-bug`, `NEGATIVE-clean` (the standard subtype the iter-v3/047 case actually fit).

3. **`feedback_v3_single_seed_frozen_baseline.md` REVISED 2026-05-09** at iter-v3/048 Critic FINAL `55fbadb`. The "CRITICAL QUALIFIER" paragraph (added at iter-v3/047 closeout citing the falsified cross-process-OpenMP attribution) was removed and replaced with the corrected attribution: "the frozen-baseline pattern dissolves whenever feature_columns OR data input OR Optuna search-space schema CHANGES. Same-feature-same-data invocations of seed=42 ARE bit-reproducible whether run in 1 process or 5 sequential processes." The iter-v3/047 case (added new RiskV2Config fields `block_long_for`/`block_short_for`) and iter-v3/048 case (added vol_normalized_ret_5d to V3_FEATURE_COLUMNS_TOP_N) BOTH break the frozen-baseline assumption from iter-v3/020/021/022 (which were TRX-only changes inside an unchanged feature stack).

4. **Primitive 10 carry-forward to iter-v3/050 CONFIRMATION decision UNCHANGED.** The IS-only validation basis remains the original premise (BCH IS net_pnl +42pp lift; 0 LONG leakage at iter-v3/047). The corrected attribution simply removes a spurious confound from the historical record — it does NOT weaken or strengthen primitive 10's bundle-ingredient candidacy. The CONFIRMATION QR brief at iter-v3/050 must still note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 is the first multi-seed OOS test."

5. **`--clean-oof` guardrail (SHA `6a216b5`) is correctly placed but the original motivation was wrong.** The guardrail prevents a true multi-run contamination scenario (engineer re-runs the backtest multiple times intentionally or accidentally and the second run appends to the first run's OOF). The structural 5x duplication from ENSEMBLE_SIZE=5 is by design and is benign (deduplicated for any per-row analysis). No change needed to the guardrail; the behavior is correct.

## Lessons

1. **The frozen-baseline pattern dissolves whenever Optuna search-space schema changes.** ANY change to V3_FEATURE_COLUMNS_TOP_N, V3_ATR_MULTIPLIERS_PER_SYMBOL, RiskV2Config schema, or any input that perturbs Optuna's per-symbol search trajectory produces non-bit-identical non-target rosters at single-seed. iter-v3/047 (added RiskV2Config fields) and iter-v3/048 (added 15th feature) both demonstrate this. The original iter-v3/020/021/022 bit-identity pattern held only because those iterations were TRX-only changes inside an unchanged feature stack. Memory rule `feedback_v3_single_seed_frozen_baseline.md` updated.

2. **n_trials reported by `dsr.json` for ENSEMBLE_SIZE=5 is correctly 700 = 4 syms × 5 ensemble × 35 trials/seed.** This is NOT a contamination signal. The 5x OOF parquet row duplication is structural per-ensemble-seed namespace collision in `optimization.py:425-430` (no `seed` column in OOF schema). Future DSR forensics MUST distinguish structural ensemble multiplicity from genuine multi-run contamination — the former is deterministic and benign; the latter requires the `--clean-oof` guardrail.

3. **Composed Category 2 engineered features that share a primitive (e.g., ret_5d numerator) with an existing PROVEN feature (regime_momentum_signed_5d) are at risk of high-IC redundancy.** vol_normalized_ret_5d shares ret_5d with regime_momentum_signed_5d (|IC|=0.892); both rank 13-15/15 in every symbol. LightGBM's depth-3-5 trees see them as redundant — the new feature steals importance slots without contributing differential signal. Future engineered features should be tested for collinearity with EXISTING engineered features BEFORE addition (the IC carve-out gate should explicitly check pairwise |IC| with the bundle's existing engineered features, not just primitives).

4. **Cycle 3 NEW universal engineered feature axis is SATURATED.** 5 attempts (iter-v3/035, /041, /042, /043, /044+/048), 0 successes. The pre-registered saturation rule (Section 8) fires CLEANLY: NEW universal engineered feature axis CLOSED for cycle 3. iter-v3/049 MUST use a different axis category per `feedback_axis_saturation_predictor.md` discipline. Cannot be retroactively renegotiated.

5. **`feedback_v3_inert_features_at_higher_budget.md` predictions held.** Adding an INERT feature (rank 13-15/15) at n_trials=35 actively HARMED OOS via Optuna search-space confusion (LDO collapsed -34.85 OOS, TRX -11.09, ALGO -36.82). The lesson from iter-v3/023 (-1.85 OOS Sharpe at n_trials=35 vs +0.78 at n_trials=10 with INERT feature) generalizes to iter-v3/048. Drop INERT features after 1 EXPLORATION verdict; do not retest at higher budget.

6. **Cycle 3 base rate for direction-asymmetric and per-symbol axes confirmed exhausted by EDA.** Per iter-v3/048 EDA synthesis: every symbol has a "toxic IS / healthy OOS" direction; universal direction blocks would cost OOS edge for 3 of 4 symbols (BCH LONG is the exception, already addressed by primitive 10). Regime-conditional analogues fail at all 5 thresholds tested. Per-symbol customizations break IS aggregate per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`. iter-v3/049 axis MUST avoid these closed categories per Critic recommendation #2.

## Architectural Decisions

- **iter-v3/045 PROMISING bundle PRESERVED** as best EXPLORATION-PROMISING in cycle 3 to date. State: V3_ATR_MULTIPLIERS_PER_SYMBOL = {ALGOUSDT: (2.0, 1.5), LDOUSDT: (2.0, 1.5)} (2 entries; iter-v3/044 ALGO + iter-v3/045 LDO). vol_normalized_ret_5d MUST be DROPPED at iter-v3/049 setup (revert V3_FEATURE_COLUMNS_TOP_N from 15 → 14).
- **Primitive 10 (direction-asymmetric kill switch) carry-forward UNCHANGED.** Still IS-validated mechanism, OOS-untested cleanly. Carries forward to iter-v3/049 + iter-v3/050 CONFIRMATION as CANDIDATE bundle ingredient on IS-only evidence basis. CONFIRMATION QR brief MUST explicitly note "primitive 10 has no clean OOS evidence from EXPLORATION; iter-v3/050 multi-seed run is the first OOS test of primitive 10 in clean conditions."
- **`block_long_for=("BCHUSDT",)` and `block_short_for=()` REMAIN in `run_baseline_v3.py:_build_v3_model`** for iter-v3/049 (carried forward as architectural state). Primitive 10 mechanism + 7 adversarial tests + GateStats counter REMAIN in `RiskV2Config` + `RiskV3Wrapper` + tests directory.
- **vol_normalized_ret_5d implementation infrastructure REMAINS** in `engineered_v3.py` and `tests/features_v3/test_vol_normalized_ret_5d.py` for future reuse, but the feature is REMOVED from V3_FEATURE_COLUMNS_TOP_N at iter-v3/049 setup. (No need to delete the function — it's gracefully ignored when not in feature list.)
- **BASELINE_V3.md UNCHANGED at iter-v3/028** (+0.5101 IS / +0.5053 OOS). Per the strict BOTH-IS-AND-OOS-must-improve policy. iter-v3/045 single-seed PROMISING-anchor is NOT a CONFIRMATION baseline.
- **NO TAG ISSUED.** Per project convention, only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags. iter-v3/048 = EXPLORATION-NEGATIVE → no tag.
- **`--clean-oof` guardrail (SHA `6a216b5`) RETAINED.** The guardrail's behavior is correct even though the original motivation (5-process pollution) was based on a falsified diagnosis. It defends against true multi-run contamination scenarios (engineer accidentally re-runs same iteration).

## Cycle 3 Cadence

- **Cycle 3 progress: #9 of 10 EXPLORATION complete.**
- **iter-v3/049 = #10 of 10 (LAST EXPLORATION before SECOND v3 CONFIRMATION).** NEW EXPLORATION axis, QR-EDA-driven per `feedback_v3_axis_selection_quant_discipline.md`. Brief Section 2 must contain QR-EDA-driven numerical evidence; analysis script committed before brief write. **MUST be a different axis category from NEW universal engineered feature** per pre-registered saturation rule. Cannot be a re-run of iter-v3/048 (peeking-at-OOS violation per `feedback_no_cheating.md`). Per `feedback_v3_strict_10_to_1_cadence.md`, iter-v3/049 must be a SEPARATE single-seed EXPLORATION (NOT CONFIRMATION-spec); do NOT collapse iter-v3/049 into the CONFIRMATION at iter-v3/050.
- **iter-v3/050 = SECOND v3 CONFIRMATION** on the best validated bundle. Multi-seed (`--seeds 2`); ENSEMBLE_SIZE=5; n_trials=35; full DSR/PBO/PSR re-eval; multi-seed Pareto. Carries primitive 10 forward as CANDIDATE bundle ingredient on IS-only evidence basis (CONFIRMATION QR brief MUST explicitly note this lacks clean OOS EXPLORATION evidence).
- **EXPLORATION wall-clock cap: 2h.** iter-v3/048 actual: 1.95h (within cap, despite the 5-process re-run inflation false-claim from iter-v3/047 era — this run was single-process).
- **CONFIRMATION wall-clock cap: 6h** (empirically updated 2026-05-07 from 4h after iter-v3/018 ran 4.54h).

## Memory Rule Updates

- **`feedback_v3_single_seed_frozen_baseline.md` REVISED** by orchestrator 2026-05-09 per Critic FINAL `55fbadb` recommendation. The cross-process-OpenMP qualifier (added at iter-v3/047 closeout citing the now-falsified 5-process attribution) was REMOVED and replaced with the corrected attribution: "the frozen-baseline pattern dissolves whenever `feature_columns` OR data input OR Optuna search-space schema CHANGES. Same-feature-same-data invocations of seed=42 ARE bit-reproducible whether run in 1 process or 5 sequential processes." Plus: "Catalog taxonomy correction: the `NEGATIVE-multi-run-stochasticity-contaminated` subtype (introduced at iter-v3/047 closeout) has zero supporting cases after iter-v3/048's forensic correction. RETIRED from taxonomy. iter-v3/047's catalog row label should be re-classified as `NEGATIVE-clean (single-seed Optuna lottery on non-target symbols; primitive 10 IS-validated)`." Verified at `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` line 19+.
- **NEGATIVE catalog subtype `NEGATIVE-multi-run-stochasticity-contaminated` RETIRED from taxonomy.** Zero supporting cases. iter-v3/047 catalog row label retroactively re-classified to `NEGATIVE-clean (single-seed Optuna lottery on non-target symbols; primitive 10 IS-validated)`. Updated at `briefs-v3/exploration_catalog.md` (or pending update at next catalog refresh).
- **NEW lesson recorded** (this diary §Lessons #3): composed Category 2 engineered features should be tested for pairwise |IC| with EXISTING engineered features in the bundle (not just primitives) BEFORE addition. vol_normalized_ret_5d's |IC|=0.892 with regime_momentum_signed_5d (shared ret_5d numerator) was the structural mechanism behind the bottom-2 importance ranking. Future engineered feature briefs Section 2 should add a table of pairwise |IC| with EXISTING engineered features in V3_FEATURE_COLUMNS_TOP_N.
- **NO new memory rule introduced** for the n_trials=700 finding because it is a one-time forensic correction documented in this diary's "iter-v3/047 Misdiagnosis Section". The structural mechanism (per-ensemble-seed namespace collision in shared OOF parquet) is now documented in `briefs-v3/iteration_v3-048/engineering_report.md` Section "n_trials=700 Investigation" for future reference.

## Pre-iter-v3/049 Actions

**Required pre-iter-v3/049 setup commit (single non-axis change before EDA + brief):**
- DROP `vol_normalized_ret_5d` from V3_FEATURE_COLUMNS_TOP_N in `src/crypto_trade/features_v3/__init__.py` (revert 15 → 14 features).
- UPDATE `_verify_feature_columns` assertion in `run_baseline_v3.py` to assert `vol_normalized_ret_5d NOT IN V3_FEATURE_COLUMNS_TOP_N` AND `len(V3_FEATURE_COLUMNS_TOP_N) == 14` (mirror of iter-v3/043 efficiency_ratio_50 + iter-v3/044 regime_momentum_signed_3d drop pattern).
- LEAVE `compute_vol_normalized_ret_5d` function in `engineered_v3.py` and 5 tests in `tests/features_v3/test_vol_normalized_ret_5d.py` IN PLACE (gracefully ignored when not in feature list; no need to delete; available for future re-evaluation if needed).
- Cycle 3 saturation rule fires: setup commit message MUST cite "vol_normalized_ret_5d DROPPED per iter-v3/048 PATH C-clean verdict; NEW universal engineered feature axis CLOSED for cycle 3 per saturation rule (5 attempts: iter-v3/035, /041, /042, /043, /044+/048)".

After the drop commit lands, iter-v3/049 setup proceeds normally: QR EDA at `analysis/iteration_v3-049/*.py` BEFORE brief write → brief at `briefs-v3/iteration_v3-049/research_brief.md` with Section 10 (QR Audit Trail) citing EDA SHA → Phase 5.5 gate → setup commit → backtest → engineering report → Critic FINAL → diary.

**iter-v3/049 axis MUST be a different category** from NEW universal engineered feature per saturation rule. See "Next Iteration Ideas" below for 5 categorically-distinct candidate axes (per Critic FINAL `55fbadb` recommendation #2).

## Next Iteration Ideas (Seed Candidates for iter-v3/049 EDA)

Per `feedback_v3_axis_selection_quant_discipline.md`, the orchestrator must dispatch QR to do EDA before iter-v3/049 brief write. The candidates below are SEED IDEAS for QR exploration, not commitments. All 5 are categorically distinct from the closed NEW universal engineered feature axis. The orchestrator may suggest these but cannot commit setup without QR backing via committed EDA script.

1. **NEW labeling architecture variant (Critic FINAL `55fbadb` recommendation #2 candidate (a)).** Universal triple-barrier with adaptive horizon by per-symbol vol regime: instead of fixed `timeout_candles=21` for all symbols, set per-symbol horizon = base_timeout × (1 / vol_regime_score) where vol_regime_score is a percentile rank of recent realized vol vs symbol's historical distribution. High-vol regimes get shorter horizon (faster barrier hits); low-vol regimes get longer (allow more time for slow trends). Different from iter-v3/017 meta-labeling architecture (which already failed). EDA candidates: per-symbol vol-regime distributions; trade-rate sensitivity to horizon scaling; backtest horizon-vs-PnL sensitivity per symbol. Compatible with primitive 10 carry-forward.

2. **NEW model architecture (CatBoost head-to-head with LightGBM at 14-feature stack) (Critic FINAL `55fbadb` recommendation #2 candidate (b)).** iter-v3/016 closed XGBoost specifically (n_trials=10, cross-entropy, depth-wise defaults), but NOT closed for all configs and NOT for CatBoost. CatBoost is categorically different (ordered boosting, monotone-constraint capability, native categorical handling — though all v3 features are numeric). Same 14-feature stack + carry-forward iter-v3/045 ATR + primitive 10. EDA candidates: paired-bootstrap CV on per-symbol gradient-booster choice; CatBoost's monotone constraints applied to vol-regime features (range_realized_vol_50 monotone increasing → trade size decreasing). Single-axis variation: model = LGBM vs CatBoost.

3. **Per-symbol features that pass IS-axis pre-validation (Critic FINAL `55fbadb` recommendation #2 candidate (c)).** Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`, per-symbol customizations can lift OOS Sharpe but break IS aggregate. The mitigation: validate that per-symbol additions PRESERVE OR LIFT IS Sharpe BEFORE adding to bundle. Specific candidate: TRX-specific `ret_kurt_50_signed_momentum = ret_5d × sign(ret_kurt_50 - 3.0)` (analogous to regime_momentum_signed_5d but using kurtosis regime instead of Hurst). TRX has flat importance distribution and the IS-axis bottleneck — a TRX-specific feature could give Optuna better split-quality without contaminating ALGO/LDO/BCH models. EDA candidates: per-symbol Spearman correlation of ret_kurt_50_signed_momentum vs forward returns; per-symbol importance prediction; multi-axis fairness check (does adding TRX-specific feature regress non-TRX models?).

4. **Drawdown-brake risk primitive (orthogonal-to-existing per `feedback_v3_concentration_is_signal.md`) (Critic FINAL `55fbadb` recommendation #2 candidate (d)).** iter-v3/020 PATH C confirmed per-symbol PnL share caps CLOSED at catalog level (concentration is signal not risk). The orthogonal alternative: per-symbol drawdown brake with loss-stop semantics — when a symbol's per-model cumulative weighted_pnl crosses a 7% drawdown threshold, halve trade size for the next 27 candles. Mirror of v1's R2 mechanism but applied per-symbol within v3. EDA candidates: per-symbol historical drawdown distributions; sensitivity of OOS PnL to drawdown thresholds; whether the brake compounds with primitive 10 BCH LONG block. Compatible with primitive 10 carry-forward; orthogonal mechanism (loss-stop, not proportional scaling).

5. **ADX-conditional regime gate variant (regime gate axis is OPEN; iter-v3/048 EDA falsified TRX SHORT regime gate but did NOT test ADX-conditional) (Critic FINAL `55fbadb` recommendation #2 candidate (e)).** Primitive 9 (regime gate) is currently DISABLED (`enable_regime_gate=False`). The iter-v3/048 EDA falsified TRX SHORT block at all 5 BTC drawdown / vol z-score thresholds. ADX-conditional regime gate is a DIFFERENT regime mechanism: when symbol's own ADX < 20 (low-trend regime), block all signals for that symbol regardless of model confidence. EDA candidates: per-symbol ADX distributions; per-symbol IS/OOS PnL stratified by ADX bins; whether low-ADX trades have negative-EV across all 4 symbols (OR specifically for the IS-axis bottleneck symbols TRX+ALGO). Compatible with primitive 10 (different mechanism layer); regime gate axis OPEN for the same logic family but different conditioning variable.

The QR is expected to score these (or alternate candidates) by EDA-driven quantitative basis, with brief Section 2 numerical tables produced by a committed `analysis/iteration_v3-049/*.py` script BEFORE brief write. Brief Section 10 (QR Audit Trail) documents which candidate was selected and why. The selected axis MUST be categorically distinct from the closed NEW universal engineered feature axis.

## See Also

- `briefs-v3/iteration_v3-048/research_brief.md` — Phase 5 brief (SHA `81af783`, backfilled at SHA `4c7ff26`)
- `briefs-v3/iteration_v3-048/phase5p5_gate.md` — Phase 5.5 gate PASS (SHA `34c97c5`)
- `briefs-v3/iteration_v3-048/engineering_report.md` — Phase 6/7 engineering report (SHA `a068edd`)
- `briefs-v3/iteration_v3-048/review.md` — Phase 7.5 Critic FINAL (SHA `55fbadb`)
- `analysis/iteration_v3-048/multi_axis_diagnosis.py` — 5-axis QR EDA script (SHA `a230cd1`)
- `analysis/iteration_v3-048/regime_gate_validation.py` — primitive 9 stratification (SHA `a230cd1`)
- `analysis/iteration_v3-048/regime_threshold_sweep.py` — 5 thresholds tested (all fail OOS) (SHA `a230cd1`)
- `analysis/iteration_v3-048/multi_axis_diagnosis.csv` — 14 sub-tables incl. per-symbol direction asymmetry
- `analysis/iteration_v3-048/regime_validation.csv` — regime fire rates, direction × regime PnL
- `analysis/iteration_v3-048/regime_threshold_sweep.csv` — TRX SHORT regime gate falsification data
- `analysis/iteration_v3-048/synthesis.md` — EDA synthesis with headline finding
- `analysis/iteration_v3-048/candidate_axes_ranking.md` — 5-axis ranking with Candidate 1 (vol_normalized_ret_5d) selected
- `reports-v3/iteration_v3-048/comparison.csv` — full numerical results
- `reports-v3/iteration_v3-048/dsr.json` — DSR/PBO/PSR (n_trials=700 STRUCTURAL not contamination; PBO + PSR valid; DSR INFORMATIONAL ONLY at EXPLORATION)
- `reports-v3/iteration_v3-048/seed_summary.json` — single-seed=42 Pareto data
- `reports-v3/iteration_v3-048/in_sample/per_symbol.csv` — per-symbol IS PnL attribution
- `reports-v3/iteration_v3-048/out_of_sample/per_symbol.csv` — per-symbol OOS PnL attribution
- `reports-v3/iteration_v3-048/ic_matrix.csv` — pairwise IC including |IC|=0.892 with regime_momentum_signed_5d
- `reports-v3/iteration_v3-048/adf_test.csv` — ADF stationarity verification
- `reports-v3/iteration_v3-048/in_sample/model_importance_last_month_*.csv` — feature importance ranks (vol_normalized_ret_5d 13-15/15)
- Setup commit SHA `c69fdaa` (vol_normalized_ret_5d wiring + V3_FEATURE_COLUMNS_TOP_N expansion 14→15)
- Pre-OOF-guardrail commit SHA `6a216b5` (--clean-oof flag + fail-loud check; correctly placed even though original motivation was based on falsified diagnosis)
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
- `/home/roberto/.claude/projects/-home-roberto-crypto-trade/memory/feedback_v3_single_seed_frozen_baseline.md` — REVISED 2026-05-09 per Critic FINAL `55fbadb` (cross-process-OpenMP qualifier removed; replaced with feature-change-breaks-frozen-baseline corrected attribution; NEGATIVE-multi-run-stochasticity-contaminated subtype RETIRED)
- `briefs-v3/iteration_v3-047/review.md` (SHA `785500f`) — n_trials=700 attribution falsified by iter-v3/048 forensic
- `briefs-v3/iteration_v3-047/engineering_report.md` (SHA `af168c4`) — 5-process attribution falsified
- `diary-v3/iteration_v3-047.md` — catalog subtype attribution corrected at this diary's "iter-v3/047 Misdiagnosis Section"
- `briefs-v3/cycle3_plan.md` — cycle 3 strategy (iter-v3/040-050)
- `briefs-v3/exploration_catalog.md` — iter-v3/048 catalog row appended at diary closure (PATH C-clean verdict + iter-v3/047 retroactive re-classification note)
