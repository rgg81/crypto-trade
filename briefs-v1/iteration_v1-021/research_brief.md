# iter-v1/021 — Research Brief (Phases 2-5)

**Branch**: `iteration-v1/021` from `iteration-v1/020` HEAD `cd75939` (tag `v0.v1-020`).

**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`). Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E).

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic + Engineer + QR.

**Iteration type**: EXPLORATION (cycle-3 #6 of 10) — METHODOLOGY PIVOT subtype (diagnostic; no edge-finding backtest in the traditional sense; src/ changes produce two diagnostic artifacts that gate /022 axis routing).

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-3 cadence position

- Cycle-3 EXPLORATION #6 of 10 (CONFIRMATION earliest at /027; CONDITIONAL /022 if H1 confirmed).
- Prior cycle-3 EXPLORATIONs: /016 (sample-weighting NEGATIVE-catastrophic), /017 (universe NEGATIVE-anti-direction-INERT), /018 (per-cohort-specialization-LINK PROMISING-INERT favorable), /019 (per-cohort-specialization-ETH PROMISING), /020 (per-cohort-specialization-BTC NEGATIVE-Catastrophic).
- Cycle-3 ledger thus far: 2 PROMISING (LINK + ETH+gate) / 3 NEGATIVE (sample-weighting + universe + BTC-only) / 0 merges.
- After /021: 6 of 10 EXPLORATIONs done; 4 more before /027 CONFIRMATION (OR /022 = /027 if H1 confirmed).

### 0.2 Methodology pivot — convergent recommendation from THREE roles

User strategic input + /020 closeout converged three independent roles on a methodology pivot for /021:

1. **/020 Critic Phase 7.5 Path Forward** preference #1: "Methodology pivot to `_write_feature_importance` + training-time pool-anchor diagnostic — family: methodology-pivot [Critic preference #1]. Add `feature_importance.csv` output (closing /019 §6 outstanding gap) AND per-(symbol, month) Optuna best-trial parameter delta between BTC-in-pool (Model A) and BTC-only (Model H) at SAME seed=42."

2. **/020 LM Master Phase 7.4 §5 hybrid Option C + B**: "Option C — methodology fix first (`_write_feature_importance` + training-time pool-anchor diagnostic). After Option C lands, decision between Option A (LTC-only specialization fallback per Phase 4.5 §6) or Option B (/027 CONFIRMATION moved up) depends on the training-time pool-anchor evidence."

3. **/019 LM Master Phase 7.4 §6 outstanding gap**: "ADD `_write_feature_importance` for v1 runner BEFORE /021. Without it, LM Master cannot triage features per-cohort, and per-cohort specialization decisions are made without feature-level evidence." This was carry-forward from /019 closeout but NOT addressed in /020 (which was a single-cohort isolation test, not a methodology iteration).

The convergent recommendation: /021 = methodology-only iteration that adds both (a) `_write_feature_importance` hook to v1 runner AND (b) training-time pool-anchor diagnostic that captures Optuna best-trial parameters per (model, symbol, train_month). Produces diagnostic artifacts that gate the /022 axis routing.

### 0.3 Why a diagnostic — three reasons

1. **/020 produced a NEGATIVE Catastrophic outcome** that REFUTED the EDA's H_POOL_ANCHOR-monthly-aggregate inference. The structural lesson (LESSON #1 in /020 diary): monthly aggregate Pearson(BTC, ETH) ρ ≈ 0 is a methodological **false-negative** for training-time pool dependence. The correct diagnostic substrate is training-time (Optuna best-trial parameter delta between pool and cohort-only at SAME seed), NOT monthly aggregate Pearson.

2. **The remaining cohorts (LTC, DOT) are next in queue** at /022-/026. Spending one EXPLORATION on each before /027 = 5 × 30 min wall-clock + uncertain outcomes. If /021 diagnostic confirms LM Master §3 mechanism, **we can predict LTC and DOT outcomes OFFLINE** and route /022-/026 accordingly. Conservative estimate: 1-3 EXPLORATIONs saved.

3. **`_write_feature_importance` is missing from v1 runner** (/019 §6 outstanding gap, /020 Critic Rec #3 carry-forward). Without it, future per-cohort decisions are made without feature-level evidence. The v1 runner currently relies on tree.dump_model() inspection or post-hoc parquet aggregation — neither produces the canonical `feature_importance.csv` artifact that v3 has at `_write_feature_importance` (runner line 3937 in v3).

### 0.4 EDA-driven hypothesis sharpening (THREE-COHORT principle established)

From `analysis/iteration_v1-021/three_cohort_outcome_table.csv`:

| Cohort | Iteration | Isolation mode | Knob added | Prior class | IS net_pnl_pct | OOS net_pnl_pct |
|---|---|---|---|---|---|---|
| BTC | baseline (in pool, Model A) | pool | none | ASYMMETRIC_ROTATION | **−37.28%** | **+33.17%** |
| LINK | baseline (in pool, Model C) | pool | none | POSITIVE_EVERYWHERE | +72.06% | +34.23% |
| ETH | baseline (in pool, Model A) | pool | none | NEGATIVE_EVERYWHERE | −13.70% | +2.75% |
| **LINK** | /018 | **single_cohort** | **none** | POSITIVE_EVERYWHERE | +52.58% | **+53.80% (PRESERVED)** |
| **ETH** | /019 | **single_cohort** | **BTC_trend_gate** | NEGATIVE_EVERYWHERE | −3.18% | **+32.65% (DISSOLVED)** |
| **BTC** | /020 | **single_cohort** | **none** | ASYMMETRIC_ROTATION | −23.25% | **+0.99% (LOST)** |

**Three-cohort principle**: per-cohort isolation succeeds when EITHER:
- (a) the cohort has an independent positive prior at pool level (LINK: 9/9 OOS positive even with pool-distortion) — **LINK case**, OR
- (b) an orthogonal mechanism is added on top of isolation (ETH: BTC-trend gate dissolved the negative drag at OOS) — **ETH+gate case**.

The BTC case fails BOTH conditions: BTC has an asymmetric-rotation prior (not positive-everywhere; not negative-everywhere either), and no knob was added. The OOS positive contribution at baseline was **pool-conferred** at training time, and isolation alone dissolved it.

**The question for LTC and DOT**: which prior class do they map to? If LTC/DOT have pool-conferred OOS positives (like BTC's case), single-cohort isolation will lose them. If LTC/DOT have intrinsic prior load (like LINK's case), isolation will preserve them.

The training-time pool-anchor diagnostic at /021 produces the evidence to answer this OFFLINE before spending /022-/026 wall-clock.

### 0.5 Cadence ledger summary

Cycle-3 #6 of 10. After /021: 6 of 10 done. 4 more EXPLORATIONs (/022-/025) before /027 CONFIRMATION — OR /022 = /027 CONFIRMATION moved up if H1 confirmed.

### 0.6 Axis Rotation Discipline + Family Declaration (v1 mandatory)

- **This iter's axis family**: `methodology-pivot` (NEW 12th family at v1 catalog level — FIRST usage; convergent recommendation per Section 0.2).
- **Prior 5 EXPLORATION families** (verified against `briefs-v1/exploration_catalog.md`):
  - /016: `sample-weighting`
  - /017: `universe`
  - /018: `per-cohort-specialization-LINK`
  - /019: `per-cohort-specialization-ETH`
  - /020: `per-cohort-specialization-BTC`
- **Rotation status**: **VALID** — `methodology-pivot` is in NONE of the prior 5 families. The methodology-pivot family was last touched at /008 (n_eff PCA per-cell median PROMISING-METHODOLOGY non-compoundable) and indirectly via /012/013 methodology-substrate-test cells; neither in the immediate prior 5. /001 was `methodology` (methodology-layer wiring); also outside the rolling 5-window.
- **One-sentence rationale**: Prior 5 families include 3 per-cohort-specialization-{LINK,ETH,BTC} EXPLORATIONs that have effectively saturated the pure-isolation axis (2/3 PROMISING with mechanism + 1/3 NEGATIVE-Catastrophic pure isolation); the methodology-pivot diagnostic produces the substrate to either RESUME per-cohort EXPLORATION (LTC, DOT) with informed routing OR ESCAPE to /027 CONFIRMATION-moved-up — both routes are downstream of the diagnostic outcome.

**NEW family declaration check (Critic Phase 7.5 Check 14 PASS requires Critic + LM Master + QR convergence on orthogonality)**: `methodology-pivot` is orthogonal to the prior 5 families because (a) NO knob axis variation — no labeling, no feature-set, no universe, no risk-primitive, no sample-weighting change; (b) it is INSTRUMENTATION — adds two diagnostic outputs (feature_importance.csv + training_time_pool_anchor.csv) without altering Optuna's training-objective domain on the BASELINE config; (c) it is non-edge-finding — the verdict is DIAGNOSTIC-{CONFIRMED, MIXED, REFUTED} based on the H1/H2 falsifier signatures, NOT IS/OOS Sharpe Δ. Justified per /020 closeout Path Forward (3-role convergence).

### 0.7 LM Master Phase 4.5 coordination slot

LM Master Phase 4.5 fires AFTER this brief. Section 3.4 below RESERVES a placeholder for LM Master responses; integration is a Phase 5.5 BLOCK condition if LM Master fires after brief but brief doesn't echo each recommendation.

QR pre-EDA prior: this is a diagnostic, so traditional verdict-class priors (PROMISING / INERT / NEGATIVE) don't apply directly. Instead the brief Section 5 uses H1/H2 verdict-class priors (DIAGNOSTIC-{CONFIRMED, MIXED, REFUTED}) derived from `analysis/iteration_v1-021/h1_verdict_class_priors.csv`:
- DIAGNOSTIC-CONFIRMED 55% / DIAGNOSTIC-MIXED 30% / DIAGNOSTIC-REFUTED 15%

LM Master Phase 4.5 will weigh in on whether the predicted prior is well-calibrated against LM Master Phase 7.4 §3 mechanism analysis from /020 (which is the basis for these priors).

---

## Section 1 — Hypothesis

This iteration tests TWO hypotheses simultaneously via methodology instrumentation. Neither is a directional edge claim; both are mechanism-level claims about the LightGBM training dynamics in pooled vs cohort-isolated configurations.

### H1 — Primary: training-time pool-anchor mechanism

**Claim**: LM Master Phase 7.4 §3 mechanism analysis (from /020 closeout) is correct — BTC's OOS positive rotation under the baseline Model A is **POOL-CONFERRED at training time** via at least one of three channels:

- **C1 — Shared feature normalization at Optuna training time**: rolling 50-bar features compute per-symbol but Optuna trial selection on COMBINED IS labels picks splits favoring features whose value distribution is regular across all 5 cohorts. BTC-alone trains on BTC's narrower NATR distribution and Optuna lands in a different basin.
- **C2 — Label-timing co-location**: training months containing BTC labels also contain ETH/LINK/LTC/DOT labels; Optuna's IS loss surface is integrated over all of them. Best-trial selection optimizes for JOINT loss; BTC-conditional optimum within that joint solution differs from BTC-alone optimum.
- **C3 — abs_pnl sample weighting integration**: BTC's large-magnitude trades are downweighted RELATIVE to LINK/LTC vol-amplified trades in the pool; BTC-only retraining REMOVES this implicit downweighting.

**Falsification logic for H1**: see Section 4 for the formal per-channel falsifier table. Summary thresholds:
- Per-parameter Optuna best-trial Δ across (sym, month) cells, comparing BTC-in-pool (Model A, dispatched on the BTC slice of pool training) vs BTC-only (Model H, single-cohort).
- DIAGNOSTIC-CONFIRMED: ≥50% of (sym, month) cells show |Δ| > threshold on ≥4 of 10 hyperparameters AND ≥1 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted.
- DIAGNOSTIC-MIXED: 20-50% of cells OR shift confined to 1-2 param families.
- DIAGNOSTIC-REFUTED: <20% of cells OR the shifts are direction-random.

### H2 — Secondary: feature dominance signature divergence

**Claim**: per-cohort feature importance differs systematically between (a) pool-trained Model A and (b) single-cohort Models C (LINK), G (ETH), H (BTC). If signatures differ, the cohort-isolation successes at /018 LINK and /019 ETH were NOT due to "same features used differently" but instead to "DIFFERENT features dominating per cohort" — supporting per-cohort specialization architecture as a fundamentally different model from the pooled one.

**Falsification logic for H2**: Spearman rank correlation between feature-importance rankings of pool (BTC slice) vs single-cohort.
- DIAGNOSTIC-CONFIRMED-H2: ≥3 features in top-10 importance differ between Model A pool (BTC slice) and Models C/G/H single-cohort; Spearman ρ < 0.5.
- DIAGNOSTIC-MIXED-H2: 1-2 features in top-10 differ; or 0.5 ≤ Spearman ρ ≤ 0.8.
- DIAGNOSTIC-REFUTED-H2: Spearman ρ > 0.8 across model variants — same features used in similar order.

### Joint verdict structure (Section 8 verdict matrix)

H1 outcome × H2 outcome × QR posterior interpretation determines the /022 routing. See Section 11.7 (verdict-conditional /022 staging).

### Critical interpretation notes

- **This iteration produces NO new trade-level backtest results in the directional-Sharpe-improvement sense.** It produces DIAGNOSTIC ARTIFACTS at the training-time and importance-distribution level.
- **Verdict cells are DIAGNOSTIC-CONFIRMED/MIXED/REFUTED, NOT PROMISING/INERT/NEGATIVE.** The Critic Phase 7.5 verdict set is unchanged (EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / BLOCK-PENDING-FIX / BLOCK-FINAL — CONFIRMATION-MERGE is not available at /021 since this is EXPLORATION). The mapping is: DIAGNOSTIC-CONFIRMED → EXPLORATION-PROMISING-METHODOLOGY (sister to /008/001); DIAGNOSTIC-MIXED → EXPLORATION-PROMISING-METHODOLOGY (partial signal); DIAGNOSTIC-REFUTED → EXPLORATION-NEGATIVE (LM Master §3 mechanism wrong; per-cohort axis viable for LTC/DOT under intrinsic-only mechanism).
- **/021 does NOT update BASELINE_V1.md regardless of outcome.** Methodology-pivot diagnostics are PROMISING-METHODOLOGY non-compoundable per `feedback_v1_methodology_probe_discipline.md` — they inform downstream iterations but are not bundled as edge ingredients.

---

## Section 2 — IS-Only Evidence (EDA results)

EDA scripts under `analysis/iteration_v1-021/`. Outputs committed at `f6a7632`.

### 2.1 Three-cohort outcome table (script 01, `three_cohort_outcome_table.csv`)

See Section 0.4. Establishes the per-cohort isolation principle:

| Cohort | Iteration | Knob | Prior class | OOS net_pnl outcome | Mechanism |
|---|---|---|---|---|---|
| LINK | /018 | none | POSITIVE_EVERYWHERE | +53.80% (PRESERVED from +34.23%) | Intrinsic positive prior survives isolation |
| ETH | /019 | BTC_trend_gate | NEGATIVE_EVERYWHERE | +32.65% (DISSOLVED from +2.75%) | Orthogonal mechanism (gate) lifted negative drag |
| BTC | /020 | none | ASYMMETRIC_ROTATION | +0.99% (LOST from +33.17%) | Neither intrinsic nor gate; pool-conferred edge dissolved |

**Codified principle**: cohort isolation success requires (a) intrinsic positive prior at pool level OR (b) orthogonal mechanism on top of isolation. Cohorts without either lose pool-conferred edge under pure isolation. /021 diagnostic establishes whether LTC and DOT fall in the (a)/(b) success branch or the BTC-case dissolution branch.

### 2.2 OOF trajectory proxy: pool vs BTC-only (script 02, `oof_per_month_summary_stats.csv` + `oof_per_month_best_trial_proxy.csv`)

Reads /001 pool trial-OOF parquet (Model A) and /020 BTC-only trial-OOF parquet (Model H). For BTC slice of each, computes per-(train_month) best-trial OOF mean (proxy for best-trial Sharpe surface; SAME seed=42).

| Source | n_months | Mean best OOF return | Median best OOF return | Std | Min | Max | n_pos | n_neg |
|---|---|---|---|---|---|---|---|---|
| pool baseline (Model A, BTC slice) | 52 | +0.190505 | (see CSV) | (see CSV) | (see CSV) | (see CSV) | (see CSV) | (see CSV) |
| BTC-only /020 (Model H) | 53 | +0.166864 | (see CSV) | (see CSV) | (see CSV) | (see CSV) | (see CSV) | (see CSV) |

**Cross-source correlation across 52 train_months**: Pearson = **+0.5893**, Spearman = **+0.2621**.

**Interpretation**: Pearson 0.59 (moderately positive) is driven by both signs being aligned in many months — pool and BTC-only both produce positive best-trial means on similar months. But Spearman 0.26 is **weak rank-correlation** — the order of "best" months differs materially between pool and BTC-only. This proxy evidence supports H1: pool and BTC-only land on materially different Optuna basins per-month, even at the proxy granularity (mean across folds, no Optuna params). The params-level diagnostic at Phase 6 will produce the direct measurement.

**Caveats**:
- /001 pool was 35 trials; /020 BTC-only was 18 trials. trial_id semantics differ between sources (TPE adapts to loss surface).
- Best-trial mean OOF return is NOT the same as Sharpe — it omits the fold-level variability.
- The proxy is sufficient to **motivate** the Phase 6 diagnostic; it is NOT sufficient to confirm H1 directly.

### 2.3 Channel-by-channel falsifier predictions (script 03, `h1_h2_pre_registration_predictions.csv`)

10-row table of LightGBM hyperparameters × expected direction × magnitude × channel × falsifier threshold. Summary by channel:

- **Channel C1 (feature normalization)**: primary impact on num_leaves, max_depth (capacity to capture cross-symbol structure), colsample_bytree (feature selection). Expected |Δ| 10-25%.
- **Channel C2 (label-timing co-location)**: primary impact on n_estimators, learning_rate, min_child_samples, reg_alpha, reg_lambda. Expected |Δ| 15-50%.
- **Channel C3 (abs_pnl weighting)**: primary impact on confidence_threshold (label-distribution dependent) + min_child_samples. Expected |Δ| 20-50%.

**Expected aggregate (H1 prior)**: across 10 hyperparams × 113-130 IS labels × 24-53 train months, the predicted % of (sym, month) cells with |Δ|>threshold on ≥4 of 10 params is **55%** (DIAGNOSTIC-CONFIRMED prior).

### 2.4 H1 verdict-class priors (script 03, `h1_verdict_class_priors.csv`)

| Verdict | Definition | Prior % | /022 routing |
|---|---|---|---|
| DIAGNOSTIC-CONFIRMED | ≥50% of (sym, month) cells show |Δ|>threshold on ≥4 of 10 params AND ≥1 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted | **55%** | /027 CONFIRMATION moved up with 2-specialist (LINK + ETH+gate) + BTC IN POOL bundle |
| DIAGNOSTIC-MIXED | 20-50% of (sym, month) cells OR shift confined to 1-2 param families | **30%** | Selective cohort coverage; bundle ETH+gate +/- LINK only; LTC/DOT TBD per partial signature |
| DIAGNOSTIC-REFUTED | <20% of cells OR direction-random | **15%** | LTC-only specialization (LM Master Phase 4.5 §6 fallback); per-cohort axis viable for remaining cohorts under intrinsic-only mechanism |

### 2.5 H2 verdict-class priors (script 03, `h2_verdict_class_priors.csv`)

| Verdict | Definition | Prior % |
|---|---|---|
| DIAGNOSTIC-CONFIRMED-H2 | ≥3 features in top-10 importance differ between Model A pool (BTC slice) and Models C/G/H single-cohort; Spearman ρ < 0.5 | **70%** |
| DIAGNOSTIC-MIXED-H2 | 1-2 features in top-10 differ; or 0.5 ≤ Spearman ρ ≤ 0.8 | **20%** |
| DIAGNOSTIC-REFUTED-H2 | Spearman ρ > 0.8 across model variants — same features used in similar order | **10%** |

H2 priors are higher confidence (CONFIRMED at 70% vs H1 55%) because the EDA proxy at script 02 (Spearman 0.26 OOF correlation across months) is consistent with significantly divergent feature-usage patterns — though it's a proxy not a direct measurement.

### 2.6 Why this evidence base is IS-only

- Script 01 reads `per_symbol.csv` and `comparison.csv` from /018, /019, /020 reports. /018 and /019 were authorized to see OOS at Phase 7; /020 saw OOS at Phase 7. The QR's USE of these CSVs is post-the-fact analysis, NOT IS-only contamination — these CSVs are already part of the iteration record.
- Script 02 reads trial-OOF parquets that contain only IN-SAMPLE training-window Optuna OOF returns. The OOS data is never accessed.
- Script 03 produces predictions; it does not access any backtest data.

The brief Section 2 evidence base is honestly IS-only.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

- **Declaration**: NORMAL-RISK
- **Reason**: This is a methodology-only diagnostic. The src/ changes are PURELY ADDITIVE:
  1. Add a `params_persist_path` parquet buffer to `optimize_and_train` (mirroring the existing `oof_persist_path` pattern at `optimization.py:415-483`) that captures Optuna `study.best_params` per `(model_role, symbol, train_month, seed)` row. This buffer is OPT-IN (set only when the runner passes a non-None path); the BASELINE config does not set it.
  2. Add a `_write_feature_importance` function to `run_baseline_v1.py` (port from `run_baseline_v3.py:2730-2818`) that captures per-model per-symbol importance from `_models[].feature_importances_` after the last walk-forward month's training. Emits `in_sample/feature_importance_<SYMBOL>.csv` and `in_sample/feature_importance_portfolio.csv`. Again purely additive — does not change predictions.
  3. Add `analysis/iteration_v1-021/04_optuna_param_delta.py` (NEW script) that, after the diagnostic backtest runs, reads the params parquet and computes per-(sym, month) delta tables for the H1 falsifier. **NOT a src/ change** — analysis script only.
  4. Add `analysis/iteration_v1-021/05_feature_importance_signature_extraction.py` (NEW script) that reads the feature_importance CSVs and computes per-cohort Spearman rank correlations for the H2 falsifier.

  NONE of these change:
  - Optuna's search space or objective (no bounds_profile change; no n_trials change)
  - The feature column set (V1_FEATURE_COLUMNS_PRUNED unchanged)
  - The labeling method (`atr_tp=2.9, atr_sl=1.45, apply_r1=False` for Model H matches /020; baseline config unchanged for Model A)
  - The trade roster (params persistence is INSTRUMENTATION; feature importance is REPORT EMISSION ONLY; both are no-ops on trade decisions)

- **Multi-seed validation**: not applicable (this is a diagnostic; the verdict is binary CONFIRMED/MIXED/REFUTED, not Sharpe-magnitude).

The HIGH-RISK gate is NOT triggered. Phase 5.5 verifies via the src/ diff (no Optuna objective/bounds/feature/label/universe/risk-primitive change).

---

## Section 3 — Proposed Changes (src/)

### 3.1 Add `params_persist_path` buffer to `optimize_and_train`

**LM Master Phase 4.5 §6 mandate (ADOPTED)**: this §3.1 implementation IS the substrate of the entire /021 diagnostic. If `params_persist_path` has partial-coverage bug (only 6 of 10 hyperparams written), the H1 falsifier becomes partially blind and verdict is forced to DIAGNOSTIC-MIXED regardless of underlying truth. Phase 5.5 BLOCK gate INCLUDES static code-review: every key in `study.best_params` for v1_pruned bounds_profile is written, NO `.get(default)` silent drops. Critic Phase 6.0 must verify on QE's src/ diff. The two QR-proposed methodology alternatives at Section 3.4 (n_trials=3 re-run + log-grep fallback) are REJECTED per LM Master §2; only the params buffer at the canonical /020 budget (n_trials=18, seed=42) is admissible — ~25 min wall-clock side-by-side BASELINE-config + Model H run with the new buffer.

**Location**: `src/crypto_trade/strategies/ml/optimization.py`, function `optimize_and_train` (lines 356-499).

**Specification**:
- New optional parameter `params_persist_path: Path | None = None` (alongside the existing `oof_persist_path` at line 371).
- After `study.optimize` completes (line 438), if `params_persist_path is not None`, append a single row to the parquet at that path with:
  - `model_role` (str — caller-provided via study.user_attr or a new function parameter)
  - `symbol` (str — caller-provided)
  - `train_month` (str)
  - `seed` (int)
  - For each of the 10 Optuna best_params keys: `confidence_threshold`, `training_days`, `n_estimators`, `max_depth`, `num_leaves`, `learning_rate`, `subsample`, `colsample_bytree`, `min_child_samples`, `reg_alpha`, `reg_lambda` (use `.get(...)` with safe fallback for fast_mode and v1_pruned_axis016 profiles)
  - Atomic write via the same `tempfile.mkstemp` + `os.replace` pattern as `oof_persist_path` (lines 449-483).

- Caller responsibility: pass `params_persist_path` from `lgbm.py::_train_for_month` via a new field `_params_persist_path` (mirrors `_oof_persist_path`). The runner sets the path; the strategy threads it.

### 3.2 Add `_write_feature_importance` function to `run_baseline_v1.py`

**Location**: `run_baseline_v1.py`, NEW function.

**Specification**: port from `run_baseline_v3.py:2730-2818`. Differences:
- Use `V1_FEATURE_COLUMNS_PRUNED` as the fallback feature list (not V3_FEATURE_COLUMNS).
- Emit to `report_dir / "in_sample" / "feature_importance_<SYMBOL>.csv"` per model.
- Emit `report_dir / "in_sample" / "feature_importance_portfolio.csv"` (sum across models).
- **Feature importance method LOCKED to `importance_type='gain'`** (mean gain, cumulative loss-reduction per feature). Per LM Master Phase 4.5 §4 (ADOPTED): matches v3 `run_baseline_v3.py:2730-2818` convention; Spearman rank well-defined; H2 falsifier comparisons interpretable. Alternatives REJECTED: raw split count `(a)` is noisy (captures "feature used in ≥1 split" frequency, not predictive power); permutation importance `(c)` is most trustworthy but costs ~5-10× wall-clock and is deferred.
- For the baseline pool config: emit ONLY the Model A pool feature importance (which is the BTC+ETH combined slot in baseline).
- For the diagnostic /021 run: emit feature_importance for Model A pool config AND Model H BTC-only config (the diagnostic runs BOTH side-by-side at the same seed=42 + same n_trials=18 used at /020).
- v1 reuses v3's last-month-only convention per Critic Clar 3 (iter-v3/017) — feature_importance reflects the LAST walk-forward month's trained models, NOT a per-month aggregate. Per-month feature importance would require a separate buffer in `_train_for_month` and is OUT OF SCOPE for /021 (LM Master Phase 7.4 §6 outstanding gap addresses the last-month-snapshot first; per-month aggregation is a future iteration).

### 3.3 Add `analysis/iteration_v1-021/04_optuna_param_delta.py`

**Location**: `analysis/iteration_v1-021/04_optuna_param_delta.py`.

**Specification**: reads `reports-v1/iteration_v1-021/optuna_best_params.parquet` (the buffer flushed by §3.1). Joins on `(symbol, train_month, seed)`. For each (sym, month, seed) cell where both Model A pool and Model H BTC-only have a row, computes per-parameter delta:
- For continuous parameters (learning_rate, subsample, colsample_bytree, reg_alpha, reg_lambda, confidence_threshold): `delta = (btc_only - pool) / max(|pool|, |btc_only|)` (symmetric pct delta).
- For integer parameters (n_estimators, max_depth, num_leaves, min_child_samples, training_days): `delta = (btc_only - pool) / max(|pool|, |btc_only|)`.
- For log-scale parameters (reg_alpha, reg_lambda): additionally compute `log_delta = log10(btc_only / pool)`.

Emits:
- `analysis/iteration_v1-021/optuna_param_delta_per_cell.csv` — one row per (sym, month) cell, columns are the 10 deltas.
- `analysis/iteration_v1-021/optuna_param_delta_summary.csv` — per-parameter aggregate (mean Δ, std Δ, %|Δ|>threshold, n_cells_breached).
- `analysis/iteration_v1-021/h1_verdict.csv` — single-row verdict (DIAGNOSTIC-CONFIRMED/MIXED/REFUTED based on Section 4 falsifier thresholds).

### 3.4 LM Master Phase 4.5 responses

LM Master Phase 4.5 emitted at `briefs-v1/iteration_v1-021/lgbm_advisor.md` (101 lines) AFTER this brief's initial draft. The seven LM Master recommendations are addressed below with QR's explicit response per `feedback_v3_brief_parameter_provenance.md`. All seven items ADOPTED; downstream sections (3.1 introduction, 3.2 importance method lock, 4.4 methodology gates, 5 priors, 11.6 bundle table, 11.7 routing matrix, 10 closeout protocol) amended in place.

- **LM Master Rec #1**: Recalibrated H1 verdict-class priors **CONFIRMED 45% / MIXED 40% / REFUTED 15%** (vs QR's 55/30/15) — Spearman 0.26 dominates over Pearson 0.59 (the latter inflated by shared positive sign in 90%+ months); mean-OOF-return is a noisy upper-bound proxy for direct parameter delta; n_trials disparity (35 pool vs 18 BTC-only) confounds best-trial parameters at warm-up vs saturated TPE.
  QR response: **ADOPTED**.
  Justification: LM Master's three-point argument is methodologically tighter than QR's (which leaned on Pearson 0.59); the MIXED-tail underweight at QR's 30% is the directly addressable gap; Section 5 priors updated.

- **LM Master Rec #2**: REJECT both QR-proposed Section 3.4 methodology alternatives. (a) n_trials=3 re-run is BELOW TPE warmup (first 5-10 trials = pure random search), yielding a NULL diagnostic dressed in compute; (b) log-grep is structurally incomplete (6/10 hyperparams never printed: subsample, colsample_bytree, min_child_samples, reg_alpha, reg_lambda) AND /020 has no run.log file at all. MANDATE: §3.1 implementation IS the diagnostic; ~25 min side-by-side BASELINE-config + Model H at n_trials=18 seed=42 with the new buffer.
  QR response: **ADOPTED**.
  Justification: Both QR alternatives have fatal defects (random-search NULL + 60% parameter-blind); only the §3.1 path produces 10/10 hyperparams per cell at the canonical /020 budget; Section 3.1 introduction now ANCHORS the §3.1 method as the substrate and explicitly rejects both alternatives.

- **LM Master Rec #3**: F-AXIS-MECHANISM #1 THREE-LAYER TEST replaces the brief's single-layer ≥96-row gate. **Layer A**: ≥**168 rows** total in `optuna_best_params.parquet` (the brief's "≥96" miscounted; pool runs 5 symbols × 24 months × 1 seed = 120 rows + 48 rows for BTC's two model_roles = ≥168). BLOCK-PENDING-FIX on row count < 168. **Layer B**: BASELINE-config trade roster bit-identical to `v0.v1-baseline-corrected` at comparison.csv level (BLOCK-FINAL on fail; adding `params_persist_path` MUST be a true no-op). **Layer C**: ALL 10 hyperparameter columns non-null per (sym, month, seed) cell — no silent `.get(default)` drops on v1_pruned profile; if only 6/10 sampled (the v1_pruned_axis016 incident from /016), verdict is forced to DIAGNOSTIC-MIXED-or-worse.
  QR response: **ADOPTED**.
  Justification: Brief Section 4.4 row-count was wrong (forgot pool runs 5 symbols); the three-layer structure correctly separates row-count (A), determinism (B), and per-row visibility (C) — all three are independent failure modes; Section 4.4 amended.

- **LM Master Rec #4**: Feature importance method = mean gain (b), matching v3 `run_baseline_v3.py:2730-2818`. Reject (a) raw split count (noisy frequency proxy) and (c) permutation importance (5-10× wall-clock, defer).
  QR response: **ADOPTED**.
  Justification: Mean gain is the v3 convention and gives interpretable Spearman rank for H2; Section 3.2 now LOCKS `importance_type='gain'` as the only admissible setting.

- **LM Master Rec #5**: /022 conditional staging — **HIGH-CONFIDENCE H1 CONFIRMED gate ≥6/10 params shifted on ≥50% of (sym, month) cells AND ≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted** → accelerated /022 = /027. **Borderline (4-5/10)** → /022 = LTC-only specialization. **H1 MIXED / REFUTED** → /022 = LTC-only specialization (cadence preserved).
  QR response: **ADOPTED**.
  Justification: The brief's previous /022 routing in Section 11.7 used ≥4/10 + ≥1 key-param as the H1 CONFIRMED bar — which is the H1 verdict threshold itself, NOT a separate /022-acceleration gate. LM Master's distinction is correct: cadence violation (skipping /023-/026) requires HIGHER confidence than H1 CONFIRMED-floor; ≥6/10 + ≥2 key-params is the right /022-acceleration threshold; Section 11.7 amended.

- **LM Master Rec #6**: Most important single-sentence directional call — §3.1 implementation IS the substrate.
  QR response: **ADOPTED**.
  Justification: Section 3.1 introduction now opens with the LM Master §6 framing as the anchor sentence; downstream gates derive from §3.1 substrate correctness.

- **LM Master Rec #7**: /027 bundle architecture = **Option β (FULL POOL preserved + specialists as alpha-enhancement)** with signal-level merge logic + pre-committed weight rule. REJECT Option α (reduced pool from 5→3 syms shifts BTC's basin via H1-in-reverse, which would CONTAMINATE the diagnostic's basis assumption). Multi-seed bundle Δ target: +1.10 to +1.30; must clear Sharpe 1.0 floor merge gate.
  QR response: **ADOPTED**.
  Justification: Option α had not been explicitly entertained by QR; LM Master's H1-in-reverse contamination argument is decisive — reducing pool size 5→3 IS itself a pool-anchor mechanism intervention that would invalidate the bundle's basis vs. the BASELINE_V1.md anchor (+0.6637 OOS Sharpe @ 5-sym pool); only Option β (FULL POOL preserved + portfolio-level additive specialists) preserves the basis; Section 11.6 bundle table amended.

- **LM Master Closing — Critic Phase 7.5 priority items (5)**: Layer A buffer flush completeness (≥168 rows) / Layer B determinism bit-identical baseline / Layer C 10-param visibility audit / H1 falsifier evaluation against pre-registered thresholds / H2 feature-signature Spearman rank correlation pre-registered band.
  QR response: **ADOPTED**.
  Justification: These five items are the canonical Phase 7.5 review checklist for /021; Section 10.5 amended to enumerate them as the Critic review pass-conditions.

Phase 5.5 gate verifies: (a) all seven recommendations addressed in this Section 3.4, (b) downstream sections amended consistently (Section 3.1 intro + Section 3.2 importance method lock + Section 4.4 three-layer test + Section 5 priors + Section 11.6 bundle table + Section 11.7 routing matrix + Section 10.5 Critic priority items).

### 3.5 NEW script: `analysis/iteration_v1-021/05_feature_importance_signature_extraction.py`

**Location**: `analysis/iteration_v1-021/05_feature_importance_signature_extraction.py`.

**Specification**: reads `reports-v1/iteration_v1-021/in_sample/feature_importance_*.csv` for both BASELINE (Model A pool) and /021 diagnostic (Model H BTC-only + Models C LINK / G ETH single-cohort, if those reports exist from /018/019 in-tree).

For each model variant, computes:
- Top-10 feature ranking.
- Spearman rank correlation with the pool baseline ranking.
- Set difference: which features appear in the top-10 of one but not the other.

Emits:
- `analysis/iteration_v1-021/feature_importance_signature_table.csv` — per (model_variant, feature) rank.
- `analysis/iteration_v1-021/feature_importance_cross_correlation.csv` — pairwise Spearman ρ.
- `analysis/iteration_v1-021/h2_verdict.csv` — single-row verdict (DIAGNOSTIC-CONFIRMED-H2 / MIXED / REFUTED based on Section 4 falsifier thresholds).

### 3.6 NO changes to:

- `V1_FEATURE_COLUMNS_PRUNED` (40 cols; unchanged)
- `V1_BASELINE_UNIVERSE` (5 syms; unchanged for Model A pool; Model H uses `(BTCUSDT,)` as in /020)
- Risk gates (R1, R2, R3) — unchanged from baseline
- Optuna bounds_profile, n_trials, ensemble_seeds (baseline config; n_trials=18 for diagnostic /021 run matches /020)
- Labeling parameters (atr_tp, atr_sl, label_timeout_minutes) — unchanged
- `OOS_CUTOFF_DATE = 2025-03-24` (IMMUTABLE)
- `training_months = 24` (IMMUTABLE)

---

## Section 4 — Falsifiers

### 4.1 H1 falsifier — Optuna best-trial parameter delta

| Parameter | Expected Δ direction | Threshold | Channel |
|---|---|---|---|
| confidence_threshold | lower | |Δ| > 15% | C2+C3 |
| n_estimators | lower | |Δ| > 25% | C2 |
| max_depth | lower or flat | |Δ| > 20% | C1+C2 |
| num_leaves | lower | |Δ| > 25% | C1 |
| learning_rate | higher | |Δ| > 20% | C2 |
| subsample | indeterminate | |Δ| > 15% | C1 |
| colsample_bytree | higher | |Δ| > 15% | C1 |
| min_child_samples | lower | |Δ| > 25% | C2+C3 |
| reg_alpha | indeterminate | |log10(Δ)| > 0.5 | C2 |
| reg_lambda | indeterminate | |log10(Δ)| > 0.5 | C2 |

**H1 verdict cells**:
- **DIAGNOSTIC-CONFIRMED**: ≥50% of (sym, month) cells show |Δ| > threshold on ≥4 of 10 parameters AND ≥1 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted. /022 routes to /027 CONFIRMATION moved up with 2-specialist (LINK + ETH+gate) + BTC IN POOL bundle.
- **DIAGNOSTIC-MIXED**: 20-50% of (sym, month) cells OR shift confined to 1-2 param families. /022 routes to selective cohort coverage; bundle ETH+gate +/- LINK only; LTC/DOT depend on partial signature.
- **DIAGNOSTIC-REFUTED**: <20% of cells OR direction-random. /022 routes to LTC-only specialization (LM Master Phase 4.5 §6 fallback); per-cohort axis viable for remaining cohorts under intrinsic-only mechanism (no pool-conferred channel).

### 4.2 H2 falsifier — Feature importance signature divergence

| Verdict | Spearman ρ (pool vs cohort) | Top-10 disagreement count |
|---|---|---|
| DIAGNOSTIC-CONFIRMED-H2 | ρ < 0.5 | ≥3 features differ |
| DIAGNOSTIC-MIXED-H2 | 0.5 ≤ ρ ≤ 0.8 | 1-2 features differ |
| DIAGNOSTIC-REFUTED-H2 | ρ > 0.8 | 0 features differ |

### 4.3 Joint H1+H2 verdict matrix (gates /022 routing)

| H1 verdict | H2 verdict | Joint posterior | /022 routing |
|---|---|---|---|
| CONFIRMED | CONFIRMED | Strong pool-conferred edge + per-cohort feature specialization | **/027 CONFIRMATION moved up: 2-specialist (LINK+ETH+gate) + BTC IN POOL** |
| CONFIRMED | MIXED | Strong pool-conferred edge; partial feature specialization | **/027 CONFIRMATION moved up: 2-specialist bundle; LTC/DOT enter via pool** |
| CONFIRMED | REFUTED | Pool-conferred edge despite same features — basin-level interaction effect | **/027 CONFIRMATION moved up with caution: structural feature interaction worth re-examining at multi-seed** |
| MIXED | CONFIRMED | Partial pool-anchor; clear feature specialization | **/022 = selective cohort EXPLORATION; LTC or DOT (NOT both) per H2 cohort-specific signature** |
| MIXED | MIXED | Both signals partial | **/022 = LTC-only specialization (Phase 4.5 §6 fallback); DOT deferred** |
| MIXED | REFUTED | Partial pool-anchor; same features | **/022 = LTC-only specialization with orthogonal mechanism (e.g., BTC-trend gate adapted)** |
| REFUTED | CONFIRMED | No pool-anchor but feature specialization differs — interesting; H2-alone routing | **/022 = LTC-only specialization; H1-mechanism analysis revised in /021 diary** |
| REFUTED | MIXED | Weak both signals | **/022 = LTC-only specialization (fallback)** |
| REFUTED | REFUTED | Both null — LM Master §3 mechanism wrong; pool-independence is true | **/022 = LTC-only specialization with confidence (LM Master §6 fallback path)** |

The /022 routing branches under the H1×H2 verdict are pre-registered here to prevent post-hoc rationalization.

### 4.4 F-AXIS-MECHANISM #1 — THREE-LAYER TEST (LM Master Phase 4.5 §3, ADOPTED)

The single-layer ≥96-row gate from the brief's initial draft was REPLACED at LM Master Phase 4.5 §3 with a three-layer test that separates row-count, determinism, and per-row visibility. The original ≥96-row count miscounted (forgot pool runs 5 symbols × 24 months × 1 seed = 120 rows + 48 rows for BTC's two model_roles).

| Layer | Gate | PASS criterion | Verdict on fail |
|---|---|---|---|
| **A** | Buffer flush completeness — row count | `reports-v1/iteration_v1-021/optuna_best_params.parquet` exists with **≥168 rows total** (pool runs 5 symbols × 24 months × 1 seed = 120 rows + BTC × 2 model_roles × 24 months × 1 seed = 48 rows; Σ ≥168). | **BLOCK-PENDING-FIX** |
| **B** | Determinism re-test — bit-identical baseline | BASELINE-config /021 run (Model A pool only, `params_persist_path=None` OR with buffer enabled but BASELINE config) produces `comparison.csv` IS/OOS Sharpe bit-identical to `v0.v1-baseline-corrected` headline (+0.2829 IS / +0.6637 OOS); zero divergences. Adding `params_persist_path` MUST be a true no-op on Optuna's training-objective domain. | **BLOCK-FINAL** |
| **C** | Parameter visibility audit — 10-column non-null | For each (sym, month, seed) cell in the params parquet, verify **ALL 10 hyperparameter columns are non-null** (confidence_threshold, training_days, n_estimators, max_depth, num_leaves, learning_rate, subsample, colsample_bytree, min_child_samples, reg_alpha, reg_lambda). v1_pruned profile MUST not have any silent `.get(default)` drops — if only 6/10 sampled (the v1_pruned_axis016 incident from /016 recurrence pattern), H1 falsifier is partially blind and verdict is FORCED to DIAGNOSTIC-MIXED-or-worse regardless of underlying truth. | **BLOCK-PENDING-FIX** + downgrade H1 verdict |
| ancillary | `feature_importance_<SYM>.csv` emitted | `reports-v1/iteration_v1-021/in_sample/feature_importance_BTCUSDT.csv` AND `in_sample/feature_importance_ETHUSDT.csv` (for pool Model A) AND `in_sample/feature_importance_portfolio.csv` exist with `importance_type='gain'`. | BLOCK-PENDING-FIX |
| ancillary | Wall-clock ≤ 30 min target / 60 min HARD CAP for diagnostic-only run | Stopwatch from QE engineering_report.md. | Informational |

**Critic Phase 7.5 verdict structure**:
- Layer A fail → BLOCK-PENDING-FIX (the missing rows are evidence of incorrect callsite threading; QE re-runs after fix).
- Layer B fail → BLOCK-FINAL (the src/ changes were not actually no-ops; revert per Section 12 roll-back protocol).
- Layer C fail → BLOCK-PENDING-FIX + the H1 verdict CANNOT BE BETTER THAN DIAGNOSTIC-MIXED (since 4 of 10 parameters were silently dropped to `.get(default)` and the falsifier is partially blind).
- All three layers PASS → proceed to H1/H2 falsifier evaluation per Section 4.1 + 4.2 + 4.3 joint matrix.

---

## Section 5 — Predicted verdict-class priors

**H1 priors** — RECALIBRATED per LM Master Phase 4.5 §1 (ADOPTED). Original QR draft (55/30/15) was based on Pearson 0.59 + 3-channel mechanism plausibility; LM Master's three-point recalibration argues Spearman 0.26 (the rank-correlation, not Pearson) is the substrate signal AND mean-OOF-return is a noisy upper-bound on direct parameter delta AND n_trials disparity (35 pool vs 18 BTC-only) confounds best-trial parameters. The MIXED tail at QR's 30% was the underweighted region — partial channel signal across 1-2 of {C1, C2, C3} is the modal interior outcome.

- DIAGNOSTIC-CONFIRMED **45%** (was 55%; LM Master §1)
- DIAGNOSTIC-MIXED **40%** (was 30%; LM Master §1 — modal-tail upweighted)
- DIAGNOSTIC-REFUTED **15%** (unchanged)

**H2 priors** (from `analysis/iteration_v1-021/h2_verdict_class_priors.csv`) — unchanged:
- DIAGNOSTIC-CONFIRMED-H2 **70%**
- DIAGNOSTIC-MIXED-H2 **20%**
- DIAGNOSTIC-REFUTED-H2 **10%**

**Joint H1×H2 modal prior** (recalibrated): DIAGNOSTIC-CONFIRMED + DIAGNOSTIC-CONFIRMED-H2 = **0.45 × 0.70 = 31.5%** (modal). DIAGNOSTIC-MIXED + DIAGNOSTIC-CONFIRMED-H2 = **0.40 × 0.70 = 28%** (close second; together ~60% of joint mass anchors on H2-CONFIRMED-with-H1-mixed-or-confirmed). Joint REFUTED+REFUTED = 1.5%.

**Critic Phase 7.5 verdict mapping (H1-anchored)**:
- DIAGNOSTIC-CONFIRMED → EXPLORATION-PROMISING-METHODOLOGY (modal)
- DIAGNOSTIC-MIXED → EXPLORATION-PROMISING-METHODOLOGY (partial)
- DIAGNOSTIC-REFUTED → EXPLORATION-NEGATIVE (LM Master §3 mechanism wrong)

**Bayesian priors update plan (Section 4.3 joint matrix)**:
- If H1 posterior at Phase 7.5 lands on CONFIRMED with HIGH-CONFIDENCE per LM Master Rec #5 (≥6/10 params + ≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted on ≥50% cells), /022 = /027 CONFIRMATION moved up.
- If H1 posterior lands on CONFIRMED-borderline (4-5/10 params) OR on MIXED OR on REFUTED, /022 = LTC-only specialization (cadence preserved). The HIGH-CONFIDENCE gate (LM Master Rec #5) is the only valid /022-acceleration trigger.

---

## Section 6 — Failure modes

### 6.1 Diagnostic noise — single-seed param shifts may be lottery

At single-seed=42, Optuna TPE adapts to the loss surface deterministically. But the loss surface itself has finite labels (BTC-only ~113-130 IS labels). Per-month best-trial parameters at small n_trials=18 may bounce around within a wide basin region without reflecting underlying mechanism. **Mitigation**: aggregate across 24 train months in IS — gives 24 deltas per parameter. If 4+ of 10 parameters show |Δ|>threshold on ≥12/24 months (50% cell breach), the H1 signal is robust to single-month noise.

### 6.2 Feature importance noise — n=24 months too few for signal

Feature importance for a single LightGBM model snapshot is the gain-aggregated split count across that model's trees. With n_estimators ~ 200-500 and ~40 features, the per-feature importance is averaged over hundreds of splits — high resolution. But comparing two models trained on disjoint sets (pool vs BTC-only), the importance ranking may differ purely due to label-distribution shift, not "fundamentally different features". **Mitigation**: H2 uses Spearman rank correlation NOT raw importance ratio. Spearman captures the ORDER stability; if the top-5 features are the same in both rankings (even at different absolute values), H2 reports REFUTED-H2.

### 6.3 Methodology probe wall-clock overrun

/021 estimated ≤30 min for diagnostic-only run. If implementation takes longer (e.g., the params_persist_path I/O is slower than expected due to atomic-write contention), wall-clock could go to 60-90 min. **Mitigation**: brief Section 10 specifies HARD CAP of 60 min for the methodology probe; QE kills if exceeded.

### 6.4 LM Master Phase 4.5 directional track 0/3 at /020

LM Master Phase 4.5 directional track is 0/3 on /020 (INERT-modal, Jaccard prediction, BTC-only diversification role all REFUTED). The /021 brief priors at Section 5 (DIAGNOSTIC-CONFIRMED 55%) lean heavily on LM Master §3 mechanism analysis from /020 Phase 7.4. **Mitigation**: at Phase 4.5, LM Master is asked to (a) re-test the mechanism claim at training-time granularity, (b) update priors if any of the three channels (C1, C2, C3) should be re-weighted, (c) provide alternative-branch pre-registration for what happens if all three channels are LOW-impact.

### 6.5 Determinism risk — params_persist_path side-channel

The `oof_persist_path` parquet write is the source of `feedback_deterministic_trade_match.md` discipline (atomic write via tempfile + os.replace). Adding `params_persist_path` parallel to it must preserve the same atomic-write pattern. **Mitigation**: code review at Phase 5.5 verifies the params buffer write follows the same `tempfile.mkstemp + os.replace` pattern. Determinism re-test: run BASELINE config /021 (params write OFF — `params_persist_path=None`) and verify trade roster bit-identical to BASELINE_V1.md. Phase 6 explicit step.

### 6.6 Engineering report MISSING at Phase 7.5 dispatch (3rd cycle-3 incident risk)

/019 and /020 both had engineering_report.md missing at Phase 7.5 dispatch (Critic Rec #1 cycle-3 incidents 1 and 2). If /021 also misses, the contract was 3 strikes incidence pattern. **Mitigation**: brief Section 10.4 explicitly re-enforces the Phase 6 contract — engineering_report.md MUST be in the same commit as comparison.csv (NOT QR scope per /020 closeout; this is QE/orchestrator responsibility). The brief carries the contract forward but doesn't fix it at QR level.

---

## Section 7 — Pre-registered failure-mode predictions

If the diagnostic produces the following observations, the following interpretations apply (pre-registered):

| Observation | Interpretation |
|---|---|
| H1 CONFIRMED + n_estimators consistently shifts DOWN BTC-only vs pool | Channel C2 (label co-location) is the load-bearing mechanism; LTC/DOT under-pool training will follow same pattern |
| H1 CONFIRMED + confidence_threshold consistently shifts DOWN | Channel C3 (abs_pnl weighting) is the load-bearing mechanism; LTC large-mag trades downweighted by BTC/ETH/LINK in pool |
| H1 CONFIRMED + num_leaves consistently shifts DOWN | Channel C1 (feature normalization) is load-bearing; cohort-specific feature distributions trigger different leaf-split patterns |
| H1 MIXED + only 1-2 params shifted | Single-channel dominance; LM Master §3's 3-channel framing is partially wrong; ONE channel does the work; LTC/DOT routing depends on which channel |
| H1 REFUTED + all parameters within noise band | Pool-independence claim at training-time granularity TRUE; LM Master §3 mechanism analysis REFUTED; per-cohort EXPLORATIONs can proceed with intrinsic-only mechanism |
| H1 REFUTED + 8/10 parameters shift but at noise-level magnitude (3-10%) | Real but tiny mechanism; pool-conferred edge magnitude is < the 0.86σ shift /020 produced — implies /020's catastrophic outcome was OTHER mechanism (multi-seed lottery, basin choice at single-seed) |
| H2 CONFIRMED + Spearman ρ < 0.3 across all model variants | Per-cohort feature specialization is fundamental; cohort-isolation architecture is structurally distinct from pool, NOT a small parameter variation |
| H2 CONFIRMED + same top-3 features (RSI, returns, atr) but ordering differs | Feature specialization is in RANKING not in INCLUSION; CIM (Cluster-Informativeness Matrix) or similar may be needed for stacking |
| H2 REFUTED + Spearman ρ > 0.9 across all variants | Per-cohort architecture uses same features in same order; the /018 + /019 successes were purely KNOB-level (Optuna param differences) not feature-level; /021 H1 outcome alone gates /022 routing |

These pre-registrations prevent post-hoc rationalization in Phase 8 diary.

---

## Section 8 — MERGE/NO-MERGE

**This iteration does NOT update BASELINE_V1.md.** Methodology-pivot diagnostics are PROMISING-METHODOLOGY non-compoundable per `feedback_v1_methodology_probe_discipline.md`.

The /021 verdict GATES /022 axis routing (per Section 4.3 joint matrix), it does NOT update BASELINE_V1.md.

Trade-roster determinism gate (Section 4.4) is the ONLY merge-style criterion: the BASELINE-config half of /021 (Model A pool only, no diagnostic) must produce trade roster bit-identical to `v0.v1-baseline-corrected`. If this gate fails, the src/ changes accidentally broke the baseline and must be reverted — Critic verdict BLOCK-FINAL.

`feature_importance` and `params_persist_path` instrumentation lands on the iteration branch but is NOT cherry-picked to trunk unless /022+ promotes them (PROMISING-METHODOLOGY merge requires user authorization). The /021 closeout will record whether the methodology probes should land on trunk for future iterations.

**Verdict outcomes**:
- DIAGNOSTIC-CONFIRMED → EXPLORATION-PROMISING-METHODOLOGY. Inform /022 routing. Methodology instrumentation lands on trunk if user authorizes.
- DIAGNOSTIC-MIXED → EXPLORATION-PROMISING-METHODOLOGY (partial). Inform /022 routing with partial signature. Methodology stays on iteration branch.
- DIAGNOSTIC-REFUTED → EXPLORATION-NEGATIVE. LM Master §3 mechanism wrong. /022 routes to LTC-only specialization fallback. Methodology stays on iteration branch.

---

## Section 9 — Library stack

No new library additions. All dependencies already present:
- `lightgbm` (existing)
- `optuna` (existing) — `study.best_params` accessor used by `optimize_and_train`
- `pandas` (existing) — parquet read/write for params persistence
- `scipy.stats.spearmanr` (via scipy 1.13+, existing) — H2 Spearman rank correlation

---

## Section 10 — Run protocol

### 10.1 Total wall-clock estimate: ≤30 min

| Step | Estimate |
|---|---|
| QE implements §3.1 (params buffer) + §3.2 (`_write_feature_importance`) | 15-25 min (small additive changes; pattern-matches existing `oof_persist_path` and v3 reference) |
| QE runs determinism check (BASELINE config only) | already covered by /021 backtest; no extra time |
| QE runs diagnostic backtest (Model A pool + Model H BTC-only, side-by-side, single seed=42, n_trials=18) | ~25 min for both models (matches /020 BTC-only wall-clock of ~25 min; pool side is similar) |
| QE writes engineering_report.md | 5 min |
| **Total** | **≤60 min HARD CAP** (target ≤30 min for the backtest portion alone) |

### 10.2 Pass conditions for Phase 5.5 Gate

- All 11 mandatory brief sections present, including Section 0.6 + Section 2.5.
- Section 3.4 placeholder for LM Master Phase 4.5 responses present.
- Section 4.4 methodology gates pre-registered.
- Axis Rotation Discipline (Section 0.6) justified — `methodology-pivot` is in NONE of the prior 5 EXPLORATION families.
- HIGH-RISK declaration (Section 2.5) = NORMAL-RISK (justified by src/ changes being purely additive).

### 10.3 Pass conditions for Phase 6.0 Critic pre-flight

- Brief look-ahead audit (no OOS contamination in EDA scripts).
- Anti-pattern static scan on QE's src/ diff: verify (a) no Optuna objective/bounds change, (b) no feature column set change, (c) no labeling change, (d) no universe change, (e) walk_forward.py:113 invariant.
- Falsifier presence: Section 4 H1/H2 matrices present and unambiguous.

### 10.4 Phase 6 contract — engineering_report.md timing (3rd cycle-3 incident risk mitigation)

**Per /020 LESSON #4 + Critic Rec #1 cycle-3 carry-forward** — engineering_report.md MUST be in the same commit as comparison.csv (NOT QR scope; this is QE/orchestrator responsibility). The brief carries the contract forward but does not fix it at QR level. If Phase 7.5 fires without engineering_report.md emitted, this is the 3RD CYCLE-3 INCIDENT and the orchestrator's "permanent fix" from /017 6th-strike protocol failed THREE times → permanent escalation required.

The diagnostic backtest is short (≤30 min) so the orchestrator dispatch flow is: Phase 6 launches → backtest completes → QE writes engineering_report.md IN THE SAME COMMIT as comparison.csv → Critic Phase 7.5 dispatches.

### 10.5 Pass conditions for Phase 7.5 Critic review — LM Master Closing 5 priority items (ADOPTED)

LM Master Phase 4.5 Closing enumerated the Critic Phase 7.5 priority items as the canonical review checklist for /021. QR ADOPTED per Section 3.4 Closing-response.

1. **Layer A** buffer flush completeness audit (≥168 rows in `optuna_best_params.parquet`) — per Section 4.4 Layer A.
2. **Layer B** determinism bit-identical baseline audit (BASELINE-config trade roster = `v0.v1-baseline-corrected` headline) — per Section 4.4 Layer B.
3. **Layer C** 10-parameter visibility audit (all 10 hyperparam columns non-null per (sym, month, seed) cell; no `.get(default)` silent drops on v1_pruned profile) — per Section 4.4 Layer C.
4. **H1 falsifier evaluation** against pre-registered Section 4.1 thresholds AND against the /022-ACCELERATION HIGH-CONFIDENCE gate in Section 11.7 (≥6/10 params + ≥2 of 4 key-params shifted on ≥50% cells).
5. **H2 feature-signature Spearman rank correlation** evaluation against pre-registered Section 4.2 band (ρ<0.5 → CONFIRMED, 0.5≤ρ≤0.8 → MIXED, ρ>0.8 → REFUTED).

Joint H1×H2 verdict cell determined per Section 4.3 matrix. /022 routing recommendation per Section 11.7 HIGH-CONFIDENCE stratification written into Phase 7.5 review.

---

## Section 11 — Bundle composition + /027 roadmap (forward-looking)

### 11.6 /027 bundle architecture — Option β FULL POOL + alpha-enhancement specialists (LM Master Phase 4.5 §7, ADOPTED)

LM Master Phase 4.5 §7 recommended **Option β** (FULL POOL preserved + specialists as alpha-enhancement) and REJECTED **Option α** (reduced pool 5→3 syms shifts BTC's basin via H1-in-reverse, contaminating the diagnostic's basis assumption). QR ADOPTED Option β per Section 3.4 Rec #7 — the H1-in-reverse contamination argument is decisive: reducing pool size IS itself a pool-anchor mechanism intervention that would invalidate the bundle's basis vs. the BASELINE_V1.md anchor (+0.6637 OOS Sharpe @ 5-sym pool).

**Architecture invariants**:
- **Model A pool UNCHANGED at 5 symbols** (BTC, ETH, LINK, LTC, DOT) — preserves baseline determinism and the BASELINE_V1.md anchor.
- Specialists are **PORTFOLIO-LEVEL ADDITIVE** (allocate fresh capital on top of pool signal; NOT a swap-out of pool slots).
- **Signal-level merge logic** with pre-committed weight rule: specialist gets a fixed % of pool's per-symbol allocation when in directional agreement; 0% when in disagreement. The exact weight % is locked at /027 brief writeup (~30% draft per LM Master §7) and CANNOT be tuned at multi-seed run-time.

**Bundle composition table**:

| Component | Provenance | Bundle role | Single-seed Δ | Multi-seed target Δ |
|---|---|---|---|---|
| Model A pool (5 syms, unchanged) | `BASELINE_V1.md` (+0.2829 IS / +0.6637 OOS) | Pool baseline (basis) | 0 | 0 |
| LINK-only specialist (Model C) | /018 PROMISING-INERT-favorable | Alpha-enhancement on LINK | +0.16 | **+0.80** |
| ETH-only + BTC-trend gate specialist (Model G) | /019 PROMISING | Alpha-enhancement on ETH | +0.65 | **+0.50** |
| BTC | via Model A pool (NO specialist) | Pool-routed; /020 NEGATIVE Catastrophic — EXCLUDED from specialist bundle | — | — |
| LTC, DOT | via Model A pool (NO specialists pending /021 H1 outcome) | If /021 H1 CONFIRMED → also pool-routed (LM Master §3 mechanism implies BTC-pattern); if /021 H1 MIXED/REFUTED → individual specialists may be queued per Section 11.7 routing | — | — |

**Bundle Δ target at /027 multi-seed**: nominal Σ = +0.6637 baseline + LINK +0.80 + ETH +0.50 = +1.96 if independent. Realistic with correlation drag: **+1.10 to +1.30**. Multi-seed regression MUST demonstrate ≥+1.0 OOS Sharpe to clear the Sharpe 1.0 floor merge gate (`feedback_sharpe_floor.md`).

**Why Option α is REJECTED**: dropping LINK + ETH from the pool to make a "3-sym pool with 2 specialists" structure would change the pool from 5 syms to 3 syms — itself a pool-anchor mechanism intervention. If H1 is even partially CONFIRMED, shifting the pool composition shifts BTC's basin in the OPPOSITE direction (away from the BASELINE_V1.md anchor). The /027 bundle would no longer be measurable against a stable baseline. Option β preserves the basis and lets specialists add ADDITIVE alpha at portfolio level without contaminating the pool's training-time mechanism.

### 11.7 /022+ conditional roadmap per /021 H1 outcome — HIGH-CONFIDENCE THRESHOLD (LM Master Phase 4.5 §5, ADOPTED)

LM Master Phase 4.5 §5 ADOPTED — separates H1-CONFIRMED-floor (Section 4.1 threshold ≥4/10 + ≥1 key-param) from /022-ACCELERATION-floor (Section 11.7 threshold ≥6/10 + ≥2 key-params). The brief's previous Section 11.7 conflated the two and treated H1-CONFIRMED-floor as the /022-acceleration trigger; LM Master correctly argued the cadence violation (skipping /023-/026) requires HIGHER confidence than H1-CONFIRMED-floor alone, because the alternative is PREDICTABLE-NEGATIVE under H1 across LTC + DOT (replicating BTC pattern).

**H1 verdict-class definitions (recalled from Section 4.1)**:
- DIAGNOSTIC-CONFIRMED: ≥50% (sym, month) cells show |Δ|>threshold on **≥4 of 10 params** AND **≥1 of {confidence_threshold, n_estimators, num_leaves, min_child_samples}** shifted.
- DIAGNOSTIC-MIXED: 20-50% cells OR shift confined to 1-2 param families.
- DIAGNOSTIC-REFUTED: <20% cells OR direction-random.

**/022-ACCELERATION HIGH-CONFIDENCE gate (LM Master Rec #5)**:
- **HIGH-CONFIDENCE H1 CONFIRMED**: ≥50% (sym, month) cells show |Δ|>threshold on **≥6 of 10 params** AND **≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples}** shifted.
- **BORDERLINE H1 CONFIRMED**: ≥50% cells on 4-5 of 10 params (i.e., H1 CONFIRMED-floor met but ≥6/10 + ≥2 key-params NOT met).

**Routing table (formal pre-registration; LM Master §5 stratification)**:

| /021 H1 verdict + confidence | /021 H2 verdict | /022 (next iter) | /023-/026 plan | /027 CONFIRMATION timing |
|---|---|---|---|---|
| HIGH-CONFIDENCE CONFIRMED (≥6/10 + ≥2 key-params) | CONFIRMED | **/022 = /027 CONFIRMATION moved up** | Skip /023-/026 in cycle-3 | /022 = /027 |
| HIGH-CONFIDENCE CONFIRMED (≥6/10 + ≥2 key-params) | MIXED | **/022 = /027 CONFIRMATION moved up** | Skip /023-/026 in cycle-3 | /022 = /027 |
| HIGH-CONFIDENCE CONFIRMED (≥6/10 + ≥2 key-params) | REFUTED | **/022 = /027 CONFIRMATION moved up (with caution)** | Skip /023-/026 in cycle-3 | /022 = /027 |
| BORDERLINE CONFIRMED (4-5/10) | CONFIRMED | /022 = LTC-only specialization | DOT-only at /023 OR mechanism-augmented LTC | /027 at end |
| BORDERLINE CONFIRMED (4-5/10) | MIXED | /022 = LTC-only specialization | DOT deferred to cycle-4 | /027 at end |
| BORDERLINE CONFIRMED (4-5/10) | REFUTED | /022 = LTC-only + orthogonal mechanism | /023 = DOT-only similar | /027 at end |
| MIXED | CONFIRMED | /022 = LTC-only specialization | DOT-only at /023 OR mechanism-augmented LTC | /027 at end |
| MIXED | MIXED | /022 = LTC-only specialization | DOT deferred to cycle-4 | /027 at end |
| MIXED | REFUTED | /022 = LTC-only + orthogonal mechanism | /023 = DOT-only similar | /027 at end |
| REFUTED | CONFIRMED | /022 = LTC-only specialization | DOT-only at /023 | /027 at end |
| REFUTED | MIXED | /022 = LTC-only specialization | DOT deferred to cycle-4 | /027 at end |
| REFUTED | REFUTED | /022 = LTC-only specialization | DOT-only at /023 | /027 at end |

**Justification for the HIGH-CONFIDENCE threshold**: the 4-EXPLORATION savings (/023-/026 ~ 2-3 hours wall-clock) is justified ONLY when the alternative is PREDICTABLE-NEGATIVE with high posterior confidence. At H1-CONFIRMED-floor (4 of 10), 6 of 10 hyperparams could still be in low-impact channels — LTC/DOT may have a different mechanism load. At HIGH-CONFIDENCE (≥6/10 + ≥2 key-params), the 3-channel framework (C1+C2+C3) has substantial evidence across all key load-bearing parameters, and the LTC/DOT outcomes are mechanically predictable. At BORDERLINE, cadence is safer than the credibility cost of /027 revealing nothing.

### 11.8 Anchor proxy formalization for /027 (Critic Phase 7.5 Rec #2 from /020 closeout)

Per /020 closeout LESSON #5: /027 CONFIRMATION brief pre-computes BTC-in-pool annualized-daily-Sharpe directly (single deterministic number, no proxy). This is forward-looking; /021 brief Section 11.7 routing table assumes the anchor proxy will be formalized BEFORE /027 brief writeup.

If /021 routes to /022 = /027 CONFIRMATION moved up, the QR's /022 brief Section 4 anchor frames MUST include the formalized BTC-in-pool annualized-daily-Sharpe — pre-computed as part of /021's diagnostic outputs (since /021 also re-runs the BASELINE Model A pool config and produces the annualized daily Sharpe in comparison.csv).

---

## Section 12 — Roll-back protocol

If src/ changes (§3.1 + §3.2) break BASELINE config determinism:
1. Revert `optimization.py` changes (drop `params_persist_path` parameter and the params buffer write block).
2. Revert `lgbm.py` changes (drop `_params_persist_path` field).
3. Revert `run_baseline_v1.py` changes (drop `_write_feature_importance` function call).
4. Re-run BASELINE config (Model A pool only, params_persist_path=None equivalent of the unmodified code) and verify trade roster bit-identical to v0.v1-baseline-corrected.
5. Critic Phase 7.5 verdict: BLOCK-FINAL (this would be a process-integrity violation).

If only the `feature_importance.csv` emission fails but determinism holds:
1. Phase 7.5 verdict: BLOCK-PENDING-FIX.
2. QR addresses the defect (with QE if it's a code fix) and re-runs Phase 6.
3. After re-evaluation, verdict can only be PASS or BLOCK-FINAL.

If only the `params_persist_path` emission fails but determinism holds AND `feature_importance.csv` emitted:
1. H1 cannot be evaluated; H2 alone can be evaluated.
2. Phase 7.5 verdict depends on H2 outcome: CONFIRMED-H2 → EXPLORATION-PROMISING-METHODOLOGY (partial); MIXED/REFUTED-H2 → EXPLORATION-NEGATIVE.
3. Recommendation: re-attempt H1 in /022 as a follow-on methodology iteration.

---

## Section 13 — Self-check template

Before declaring brief complete, QR confirms:

- [ ] Section 0.6 (Axis Rotation Discipline) declared and justified — `methodology-pivot` NOT in prior 5 families.
- [ ] Section 2.5 (HIGH-RISK declaration) declared and justified — NORMAL-RISK with src/ additive justification.
- [ ] Section 3.4 (LM Master Phase 4.5 responses) placeholder reserved.
- [ ] Section 4.4 (methodology gates) thresholds pre-registered.
- [ ] Section 4 falsifier matrices (H1, H2, joint) unambiguous.
- [ ] Section 5 verdict-class priors numerically specified.
- [ ] Section 6 failure modes addressed (5 modes).
- [ ] Section 7 pre-registered failure-mode predictions (9 rows).
- [ ] Section 8 MERGE/NO-MERGE — /021 does NOT update BASELINE_V1.md regardless of verdict.
- [ ] Section 10.4 engineering_report.md timing contract re-enforced.
- [ ] Section 11.7 /022+ conditional roadmap pre-registered (9-cell verdict matrix).
- [ ] All EDA evidence in Section 2 cites a committed `analysis/iteration_v1-021/*.py` script + CSV output.
- [ ] No OOS leak in EDA scripts (verified at Phase 6.0 pre-flight).
- [ ] Wall-clock estimate ≤ 60 min HARD CAP (target ≤ 30 min).

---

## EDA → backtest contract summary

The brief produces TWO commits to branch `iteration-v1/021`:

1. **`feat(iter-v1/021): EDA — diagnostic methodology design`** (HEAD `f6a7632`)
   - 3 EDA scripts + 6 CSV outputs in `analysis/iteration_v1-021/`.

2. **`docs(iter-v1/021): QR Phases 1-5 + methodology-pivot brief`** (THIS COMMIT, TBD)
   - `briefs-v1/iteration_v1-021/research_brief.md` (this file)

Phase 4.5 LM Master dispatch FOLLOWS the brief; Section 3.4 reserves the integration slot. Phase 5.5 gate verifies all 11 sections + LM Master integration. Phase 6.0 Critic pre-flight verifies the src/ diff. Phase 6 QE implements §3.1 + §3.2 and runs the diagnostic backtest. Phase 7.4 LM Master post-mortem reads the diagnostic outputs. Phase 7.5 Critic review evaluates H1/H2 verdicts per Section 4.3 matrix.

Phase 8 QR diary records the /022 routing per Section 11.7.
