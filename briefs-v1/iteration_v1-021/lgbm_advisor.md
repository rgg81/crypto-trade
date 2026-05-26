# LightGBM Master Advisor — iter-v1/021 — Phase 4.5 (Pre-Design)

## Context Read

- **Track**: v1. Branch `iteration-v1/021`. HEAD `0a2343b`. Cycle-3 EXPLORATION #6 of 10 — methodology-pivot subtype (the iteration I myself recommended at /020 Phase 7.4 §5 hybrid Option C+B).
- **Track record entering /021**: 0/3 directional calls at /020, 1/1 methodology call (n_eff=9), 1/1 pre-registered alternative-branch utility. Phase 4.5 directional reasoning at /020 collapsed because monthly aggregate ρ ≈ -0.022 was treated as evidence of training-time pool independence — wrong inference. The /021 diagnostic IS the audit of that mistake.
- **Anchor EDA**: `analysis/iteration_v1-021/oof_per_month_summary_stats.csv` confirms Pearson **0.5893** / Spearman **0.2621** across 52 train-months between pool baseline (Model A, BTC slice) and BTC-only /020 (Model H). Directionally aligned, structurally different rankings.
- **Critical infrastructure finding**: NO existing parquet captures Optuna `study.best_params`. The `oof_persist_path` mechanism (`optimization.py:475-483`) flushes per-trial OOF returns but NOT the `study.best_params` dict. Baseline `run.log` has 1025 `Best params:` print lines but only 4 of 10 hyperparams (n_estimators, max_depth, learning_rate, num_leaves) are emitted. /020 has NO run.log file at all.

## 1. QR's 55/30/15 H1 priors — REJECT, recalibrate to 45/40/15

**Pearson 0.59 is moderately positive but NOT strong evidence for H1 CONFIRMED at 55%.** Three reasons:

1. **Spearman 0.26 dominates the inference**, not Pearson. The QR Section 2.2 text correctly notes Spearman 0.26 is "weak rank-correlation — the order of 'best' months differs materially". This is the substrate-level signal: month-by-month, the basins ARE different. Pearson 0.59 inflates because BOTH series are sign-positive in 90%+ of months (pool 48/52 = 92%; BTC-only 45/53 = 85%) — Pearson is pulled up by shared positive sign, not by per-month parameter alignment.

2. **The proxy is mean-OOF-return, not Optuna parameter delta directly**. Mean OOF return at best-trial can converge between pool and BTC-only via DIFFERENT parameter combinations (multiple basins yielding similar Sharpe). H1 specifically claims **parameter-space divergence**; the OOF proxy is at-best a noisy upper bound on H1's strength.

3. **n_trials disparity (35 pool vs 18 BTC-only)** confounds: pool's TPE saturated; BTC-only's TPE was warming up. Best-trial parameters at 18 trials are HIGHER-VARIANCE than at 35 — guarantees larger nominal parameter-Δ even if the underlying basin is the same.

**Recalibrated**: DIAGNOSTIC-CONFIRMED **45%** / MIXED **40%** / REFUTED **15%**. The MIXED tail is the underweighted prior — partial channel signal across 1-2 of {C1, C2, C3} is the modal interior outcome.

## 2. Methodology question — REJECT BOTH QR-proposed alternatives

### Why "re-run n_trials=3 for ALL months" is wrong
n_trials=3 is BELOW TPE warmup — first 5-10 trials are pure random search. At n_trials=3, "best_params" is essentially the maximum of 3 IID random draws from the search-space prior. The H1 falsifier requires basin-converged params — n_trials=3 is a NULL diagnostic dressed in compute.

### Why "extract from existing /020+baseline runs via run.log grep" is also wrong
(a) `/020` has NO run.log. (b) Print line emits only 6/10 hyperparams (subsample, colsample_bytree, min_child_samples, reg_alpha, reg_lambda NEVER printed). (c) Parsing is fragile.

### CORRECT APPROACH (mandate)

**Implement `params_persist_path` as the QR brief §3.1 already specifies, AND re-run /020 BASELINE-config + Model H side-by-side at `n_trials=18 seed=42` (canonical /020 budget) WITH the new buffer.** This costs ~25 min wall-clock. Produces 10/10 params per cell, structured by `(model_role, symbol, train_month, seed)`. CONFIRM with QR before Phase 5 brief finalization that §3.1 is THE method, not a tiny-budget alternative.

## 3. F-AXIS-MECHANISM #1 for diagnostic — THREE-LAYER TEST

**Layer A — Buffer flush completeness**: `optuna_best_params.parquet` exists with ≥ (24 train_months × 2 model_roles × 1 seed) = 48 rows for BTC PLUS rows for all 5 pool symbols (BTC, ETH, LINK, LTC, DOT) on Model A pool = 24 × 5 = 120 rows. **TOTAL ≥ 168 rows** (brief's "≥ 96 rows" miscounts; forgot pool runs 5 symbols). BLOCK-PENDING-FIX if row count < 168.

**Layer B — Determinism re-test**: BASELINE-config /021 trade roster bit-identical to `v0.v1-baseline-corrected` portfolio Sharpe headline (+0.2829 IS / +0.6637 OOS) at COMPARISON.CSV level. Adding `params_persist_path` MUST be a true no-op on Optuna's training-objective domain. BLOCK-FINAL if this fails.

**Layer C — Parameter visibility audit**: for each (sym, month, seed) cell, verify ALL 10 hyperparameter columns are non-null. v1_pruned profile MUST not have any silent `.get(default)` drops — if only 6 of 10 are sampled (the v1_pruned_axis016 incident from /016), H1 falsifier is partially blind and verdict is forced to DIAGNOSTIC-MIXED-or-worse.

## 4. Feature importance method — RECOMMEND mean gain (b)

- **(a) Raw split count**: noisy; captures "feature used in ≥1 split" frequency not predictive power.
- **(b) Mean gain** (`importance_type='gain'`): cumulative loss-reduction per feature. **This is what v3 uses at `run_baseline_v3.py:2730-2818`.** Spearman rank well-defined; H2 falsifier comparisons interpretable. **RECOMMEND.**
- **(c) Permutation importance**: most trustworthy but ~5-10× wall-clock. Defer.

`_write_feature_importance` uses `importance_type='gain'`. Per-month aggregation deferred to future iteration (LM Master Phase 7.4 §6 outstanding gap II).

## 5. /022 conditional staging — accelerated /027 vs cadence-preserved LTC-only

**Recommendation: CONDITIONAL — modal LTC-only; accelerate /027 ONLY at HIGH-CONFIDENCE H1 CONFIRMED.**

- **If H1 CONFIRMED with ≥6 of 10 params shifted on ≥50% of (sym, month) cells AND ≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted** → accelerated /022=/027. Cadence violation justified because /023-/026 single-cohort EXPLORATIONs are PREDICTABLY NEGATIVE under H1 (replicate BTC pattern).
- **If borderline (4-5 of 10 params shifted)** → /022 = LTC-only specialization, then re-evaluate /023 after observing LTC.
- **If H1 MIXED OR REFUTED** → /022 = LTC-only specialization (preserves cadence; per-cohort axis revives).

The 4-EXPLORATION savings (~2-3 hours wall-clock) is justified at HIGH-CONFIDENCE because the alternative is PREDICTABLE-NEGATIVE. At BORDERLINE, cadence is safer than the credibility cost of /027 revealing nothing.

## 6. Most important point — single-sentence directional call

**The diagnostic is methodology-defensible IF (a) `params_persist_path` flushes ALL 10 hyperparams at ≥168 rows via the brief §3.1 method (NOT QR-proposed n_trials=3 re-run NOR run.log grep), (b) BASELINE-config trade-roster determinism holds bit-identical, and (c) feature_importance uses `importance_type='gain'`; /027 CONFIRMATION moves to /022 ONLY if H1 CONFIRMED with mean |Δ|>0.30 on ≥6 of 10 params across ≥50% of (sym, month) cells AND ≥2 of {confidence_threshold, n_estimators, num_leaves, min_child_samples} shifted — otherwise /022 = LTC-only specialization preserving cadence.**

## 7. /027 BUNDLE COMPOSITION — RECOMMEND Option β

### Option α — TWO-SPECIALIST + REDUCED POOL (rejected)
Drop LINK + ETH from pool; 3-sym pool may shift BTC's basin (H1 in reverse).

### Option β — TWO-SPECIALIST + FULL POOL preserved (recommended)
- LINK-only specialist (Model C): +0.80 anchor — alpha-enhancement layer on top of pool
- ETH-only + gate specialist (Model G): +0.50 anchor — alpha-enhancement layer
- Model A pool **UNCHANGED at 5 symbols** — preserves baseline determinism
- Specialists are PORTFOLIO-LEVEL ADDITIVE (allocate fresh capital on top of pool signal)
- Signal-level merge logic with pre-committed weight rule (e.g., specialist gets 30% of pool's per-symbol allocation when in agreement; 0% when in disagreement)

| Component | Provenance | Bundle role | Single-seed Δ | Multi-seed target Δ |
|---|---|---|---|---|
| Model A pool (5 sym, unchanged) | BASELINE_V1.md | Pool baseline | 0 | 0 |
| LINK-only specialist (Model C) | /018 PROMISING | Alpha-enhancement | +0.16 | +0.80 |
| ETH-only + BTC-trend gate (Model G) | /019 PROMISING | Alpha-enhancement | +0.65 | +0.50 |
| **BTC** | via Model A pool | NO specialist | — | — |
| **LTC, DOT** | via Model A pool | NO specialists (H1 implies BTC-pattern) | — | — |

Bundle Δ target at /027 multi-seed: +0.6637 baseline + LINK +0.80 + ETH +0.50 = nominal +1.96 if independent. Realistic with correlation drag: **+1.10 to +1.30**. Multi-seed regression must demonstrate ≥+1.0 OOS Sharpe to clear the Sharpe 1.0 floor merge gate.

## Closing Notes

**HIGH-MEDIUM confidence in three calls** (calibrated against /020's 0/3 directional record):

1. **H1 prior CONFIRMED 45% (not QR's 55%)** — Spearman 0.26 + n_trials confound + proxy-vs-direct-parameter gap argue for MIXED tail being underweighted.
2. **Methodology: brief §3.1 implementation IS the diagnostic; reject QR alternatives (tiny-budget + log-grep)** — both have fatal defects.
3. **/022 routing: LTC-only modal unless H1 CONFIRMED with HIGH confidence** — cadence violation only at clearly CONFIRMED.

**Single most important point for QR**: the brief §3.1 implementation is the substrate of the entire diagnostic. If `params_persist_path` has partial-coverage bug (only 6 of 10 params written), the H1 falsifier becomes partially blind and verdict is forced to DIAGNOSTIC-MIXED regardless of underlying truth. Phase 5.5 BLOCK gate must include static code-review: every key in `study.best_params` for v1_pruned bounds_profile is written, NO `.get(default)` silent drops. Critic Phase 6.0 must verify on QE's src/ diff.

**Critic Phase 7.5 priority items**:
1. Layer A buffer flush completeness (≥168 rows)
2. Layer B determinism bit-identical baseline
3. Layer C 10-param visibility audit
4. H1 falsifier evaluation against pre-registered thresholds
5. H2 feature-signature Spearman rank correlation pre-registered band
