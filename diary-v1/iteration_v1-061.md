# iter-v1/061 — EXPLORATION-NEGATIVE-DEEPER-ARCHITECTURE-OR-DATA-ISSUE — BTC-only zero-randomness diagnostic (cycle-7 EXP-4/N)

**Tag**: `v0.v1-061`
**Date**: 2026-06-02
**Iteration type**: EXPLORATION-METHODOLOGY (zero-randomness diagnostic; pipeline reproducibility test; methodology family)
**Cycle slot**: cycle-7 EXP **4/N**
**Verdict**: **NEGATIVE-DEEPER-ARCHITECTURE-OR-DATA-ISSUE** (PROCEDURAL-PASS / SUBSTANTIVE-NEGATIVE per Critic Phase 7.5)
**Decision**: NO baseline change. V1_FEATURE_COLUMNS_PRUNED UNCHANGED at 48 cols. BTC-only single-symbol single-deterministic-fit architecture flagged for cycle-7 closure (pivot to structural per LM Master §5 + Critic §"Recommendations").
**Status**: NO-MERGE (EXPLORATION; methodology); BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`)

**Banner**: Fourth cycle-7 EXPLORATION under reformed multi-seed-from-start budget — but this iteration deliberately exits the multi-seed frame to test the PROCEDURAL property "is the pipeline bit-exact reproducible at central-tendency HPs with ALL randomness sources eliminated?". **F1 PRIMARY VERDICT GATE — PASS** (Run-1 ≡ Run-2 IS Sharpe = −0.8260 to all decimal places; bit-exact `diff -r` on `in_sample/trades.csv`; basin_diagnostics v1.cross_seed_sharpe_std = 0.0). **F2 IS Sharpe vs LM Master prediction +0.08 — MISS** (observed −0.826 outside both 60% band [−0.10, +0.20] and implied 90% band [−0.20, +0.30]; |Δ| = 0.91 = ~4.6σ from LM's modal prediction). Per the pre-registered basin-lottery diagnostic map (Section 4 F-AXIS #2 / brief §4): IS << −0.10 AND reproducible → DEEPER-ARCHITECTURE-OR-DATA-ISSUE. **The HIDDEN-RANDOMNESS-BUG, SAMPLE-SIZE-NOISE-FLOOR, and OPTUNA-LOTTERY-SOURCE branches are ruled out**: HIDDEN-RANDOMNESS-BUG by bit-identity; SAMPLE-SIZE-NOISE-FLOOR by magnitude (−0.83 is too extreme for the implied basin); OPTUNA-LOTTERY-SOURCE by direction (wrong sign — the central-tendency recipe lands in the unfavorable tail, NOT a favorable basin). The BTC-only-specialist edge, if any, is below the single-seed detection floor at 24-month-rolling × 48-feature × LightGBM defaults.

---

## 1. Decision: NEGATIVE-DEEPER-ARCHITECTURE-OR-DATA-ISSUE; NO BASELINE CHANGE

| Section 8 / Section 4 F-AXIS verdict gate | Threshold | Observed | Verdict |
|---|---|---:|---|
| F1 — Bit-exact reproducibility (Run-1 vs Run-2 IS Sharpe identical to ≥8 dp) | identical | **−0.8260 ≡ −0.8260** | **PASS** (primary gate) |
| F2 — IS Sharpe in LM Master 60% band [−0.10, +0.20] | in-band | **−0.8260** | **OUT OF BAND** (|Δ| = 0.91) |
| F2 — IS Sharpe in LM Master 90% band [−0.20, +0.30] | in-band | **−0.8260** | **OUT OF BAND** (|Δ| = 0.83) |
| F3 — Diagnostic falsified (IS trades = 0 OR non-reproducible) | not falsified | 224 IS trades / reproducible | **PASS** (diagnostic ran cleanly) |

Per the pre-registered basin-lottery diagnostic map (brief Section 4 F-AXIS #2 outcome table):
- F1 PASS rules out HIDDEN-RANDOMNESS-BUG. Pipeline is provably deterministic at the LM Master Phase 4.5 central-tendency HP recipe.
- F2 below band by 0.91 Sharpe rules in **DEEPER-ARCHITECTURE-OR-DATA-ISSUE**: the central-tendency HP recipe lands in the unfavorable tail of the basin distribution.

**MERGE criteria N/A** — methodology diagnostic iterations never directly update BASELINE_V1. The diagnostic outcome IS the deliverable.

---

## 2. Observed Results

### 2.1 Headline (single-seed=42, n_trials=1, all randomness eliminated)

| Metric | IS | OOS | Ratio (OOS/IS) |
|---|---:|---:|---:|
| Sharpe (annualized, monthly) | **−0.8260** | **−0.0689** | 0.0834 |
| Sortino | −0.7797 | −0.0982 | 0.1260 |
| Max DD | 55.35% | 8.73% | — |
| Win rate | 36.2% | 39.0% | — |
| Profit factor | 0.7774 | 0.9811 | — |
| Total trades | **224** | **82** | 0.3661 |
| Calmar | 0.7914 | 0.1035 | — |
| DSR (single-trial) | −10.1026 | −1.3387 | informational only |
| PSR vs 0 (monthly) | 0.0380 | 0.4683 | informational only |
| Total net PnL | −43.80 | −0.90 | — |

(Per `reports-v1/iteration_v1-061/comparison.csv`.)

### 2.2 Bit-Exact Reproducibility — F1 PRIMARY VERDICT GATE PASS

- Run-1 (commit `71adabf`): IS Sharpe **−0.8260**, 224 IS trades, 82 OOS trades.
- Run-2 (commit `7a13331`): IS Sharpe **−0.8260** (identical to all decimal places), trades.csv `diff -r` zero divergence.
- basin_diagnostics v1.cross_seed_sharpe_std = **0.0** (PASS; threshold ≤ 0.3).

Implication: at the LM Master Phase 4.5 central-tendency HP recipe (n_estimators=300, max_depth=4, num_leaves=31, learning_rate=0.05, min_child_samples=50, subsample=1.0, colsample_bytree=1.0, bagging_freq=0, deterministic=True, num_threads=1, is_unbalance=False, force_col_wise=True), the v1 pipeline is **provably deterministic**. No hidden randomness source contaminates the diagnostic. The pipeline's reproducibility property is now empirically established and can be relied on by future iterations.

### 2.3 LM Master Phase 4.5 Prediction Calibration Distance

| Quantity | LM Master prediction | Observed | |Δ| | Verdict |
|---|---:|---:|---:|---|
| IS Sharpe | +0.08 (mode); 60% band [−0.10, +0.20] | **−0.826** | **0.91** | **OUT OF BAND** |
| OOS Sharpe | −0.70 (mode); 60% band [−1.20, −0.20] | **−0.069** | **0.63** | OUT OF BAND (other direction) |

Both predictions miss the observed values by ~0.6–0.9 Sharpe units. The LM Master Phase 7.4 post-mortem candidly accounts for these misses; calibration distance noted for future Phase 4.5 priors on BTC-only-specialist single-deterministic-fit predictions specifically.

### 2.4 Catalog-Context Comparison (BTC-only-specialist single-cohort reads)

| Iter | Config | IS Sharpe | Notes |
|---|---|---:|---|
| /054 (cycle-6) | single-seed=42, n_trials=18, full Optuna | **+0.2614** | favorable basin draw (top of catalog) |
| /053 (cycle-6) | 3-seed mean, n_trials=18 | −0.0400 | spread 0.31 |
| /058 (cycle-7) | 3-seed mean, n_trials=18 | −0.2803 | spread 0.90 (catalog record before /061) |
| /059 (cycle-7) | Pool single-seed, n_trials=18 | −0.1600 | pool architecture, informational |
| **/061 (THIS)** | **single-seed=42, n_trials=1, zero-randomness** | **−0.8260** | **central-tendency HP recipe; below all prior catalog reads** |

**Catalog spread for BTC-only specialist single-cohort reads now revised: [−0.83, +0.26] = spread 1.09** (previously 0.90 at /058). /061 establishes a new floor and confirms the basin distribution is centered well below 0. The /054 +0.26 was a +1.2σ favorable draw from a Sharpe-mean ≈ −0.3 distribution (or worse — /061 suggests the underlying mean may be closer to −0.5 if /061's deterministic recipe is centrally representative; the LM Master honestly notes this is one observation thin and recommends a 10-seed MC sweep at /054 HPs as the confirming experiment).

### 2.5 Feature Provenance Forensic — RESOLVED

The LM Master Phase 4.5 advisory referenced "BTC-only 48-col stack (basis_zscore_30 added)" — this was **an LM Master Phase 4.5 misstatement**, NOT a runner misconfiguration. Confirmation:

- `feature_importance_Model_A_BTC_specialist_061.csv` lists exactly 48 features; `basis_zscore_30` is NOT among them.
- `V1_FEATURE_COLUMNS_PRUNED` (`src/crypto_trade/features_v1/__init__.py`) is 48 cols; `basis_zscore_30` is in `V1_RETIRED_FEATURES` (DROPPED at iter-v1/040 for 3-consecutive INERT; replaced by `regime_momentum_signed_5d`).
- The /061 brief explicitly states (§3.3 + §3.4): "Features: V1_FEATURE_COLUMNS_PRUNED (48 cols; UNCHANGED — no feature add/drop)". The runner dispatch (`run_baseline_v1.py:6681`) asserts `len(active_feature_columns) == 48`.
- The git commit `1be3bd1` referenced in the Critic's Check 4 is from **iter-v1/034** (per `run_baseline_v1.py:4448`'s comment block), where `basis_zscore_30` WAS the banner feature; it was DROPPED at /040.

**Resolution**: /061 trained on the correct 48-col V1_FEATURE_COLUMNS_PRUNED stack as designed; the absence of `basis_zscore_30` is CORRECT (the feature was retired at /040). No reclassification to NEGATIVE-DIAGNOSTIC-MISCONFIGURATION is warranted. The verdict stands at **NEGATIVE-DEEPER-ARCHITECTURE-OR-DATA-ISSUE**.

The Critic's forensic flag in Check 4 and the LM Master's Phase 4.5/7.4 reference to `basis_zscore_30` reflect a shared misreading of which iteration owned which feature; both the brief and the runner were internally correct.

### 2.6 OOS Behavior — Informational Only

Per `feedback_v3_dsr_mode_artifact.md` analog applied to methodology iterations: single-seed=1 + n_trials=1 OOS Sharpe is informational. /061 OOS −0.069 (essentially flat near zero) over 82 OOS trades. This is BTC-only-specialist's typical OOS regression signature compressed near zero by the unfavorable IS-fit (the model under-fits IS sufficiently that OOS variance is also compressed). Not a verdict driver.

### 2.7 Trade-Rate Floor Observation (Informational)

- IS: 224 trades / 24 months = **9.33 trades/month** (below 10/month floor)
- OOS: 82 trades / ~14 months = **5.86 trades/month** (below 10/month floor AND below 130 total)

For MERGE candidates this would BLOCK. For an EXPLORATION methodology diagnostic this is informational — the experiment is not proposing a baseline update. Flag for cycle-7 axis selection: BTC-only single-symbol architecture is structurally too thin on trade count to support a multi-symbol-portfolio replacement (Critic Check 7 confirms).

### 2.8 Per-Regime Tooling — STILL Not Wired

`in_sample/per_regime.csv` contains exactly ONE row: `regime=unknown, 224 trades, sharpe=-0.1165`. Cumulative debt /049-/061 (13 iterations) — regime tagger remains non-functional. Critic Check 6 flagged BORDERLINE. Plug in cycle-7's next iteration brief Section 6, OR codify as a methodology iteration explicitly to wire up the regime classifier (axis family: `methodology`).

---

## 3. What Worked

1. **F1 reproducibility property ESTABLISHED.** The pipeline is bit-exact deterministic at the LM Master Phase 4.5 central-tendency HP recipe with all 10 randomness sources eliminated (n_trials=1, seeds=1, subsample=1.0, colsample=1.0, bagging_freq=0, deterministic=True, num_threads=1, is_unbalance=False, force_col_wise=True, R3 OOD off). This is a foundational property that future v1 iterations can rely on — any future variance across runs at these HPs is attributable to genuine non-deterministic changes, not hidden randomness.
2. **HARDCODED HP injection via `study.enqueue_trial()` monkey-patch WORKS.** The monkey-patch mechanism in `run_iteration_061.py` correctly forces a single Optuna trial to use the hardcoded HP dict; no fallback to TPE-sampled HPs. The pattern is now validated and can be reused for future diagnostic iterations that need to fix HPs deterministically.
3. **Basin-lottery diagnostic map FIRED CORRECTLY.** The pre-registered Section 4 F-AXIS #2 outcome table cleanly maps (IS = −0.826, reproducible) → DEEPER-ARCHITECTURE-OR-DATA-ISSUE. The map is well-designed; the outcome is interpretable; the action implied is concrete (Critic + LM Master both recommend pivoting to structural).
4. **Three competing diagnostic branches RULED OUT decisively.** HIDDEN-RANDOMNESS-BUG (by bit-identity); SAMPLE-SIZE-NOISE-FLOOR (by magnitude — −0.83 is 8× the band edge of −0.10); OPTUNA-LOTTERY-SOURCE (by direction — wrong sign relative to +0.08 modal prediction). The remaining branch is unambiguous.
5. **LM Master Phase 4.5 → Phase 7.4 → Critic Phase 7.5 three-way alignment.** All three roles agree on the diagnosis (DEEPER-ARCHITECTURE-OR-DATA-ISSUE) and on the action (pivot to structural per `feedback_v3_structural_over_knob_exploration.md`). The Critic softens slightly (recommends 10-seed MC sweep at /054 HPs FIRST before declaring the architecture closed); both versions of the recommendation lead to the same cycle-7 axis pivot.
6. **R3 OOD disabled cleanly.** The runner correctly constructed `LightGbmStrategy` directly with `ood_enabled=False` (bypassing `run_model()`'s default `ood_enabled=True`); no covariance-inversion non-determinism in the diagnostic. Verifies that R3 disable path is reachable from the dispatch level for future diagnostic iterations.

## 4. What Failed

1. **F2 IS Sharpe prediction MISS by 0.91 Sharpe units.** The LM Master Phase 4.5 modal prediction +0.08 is off by ~4.6σ relative to the observed −0.826. The central-tendency HP recipe (n_estimators=300, depth=4, leaves=31, lr=0.05, min_child=50, reg_alpha=0.1, reg_lambda=0.1) lands in the unfavorable tail of the basin distribution — the opposite of /054's favorable +0.26 single-seed=42 draw at full Optuna search. This is not a methodology failure (the diagnostic ran correctly); it is a finding about the BTC-only-specialist basin distribution: the central-tendency HP recipe is not centrally representative of the basin.
2. **BTC-only-specialist single-deterministic-fit architecture is below detection floor.** With single-seed=42 + n_trials=1 + all randomness off, the model has no Optuna basin-hopping to find the favorable region of the loss surface. The result is a deterministic IS fit to one of the basin's unfavorable trajectories. Without basin-hopping, the BTC-only-specialist signal — if any — is below the detection floor at 24-month-rolling × 48-feature × LightGBM defaults.
3. **Catalog spread for BTC-only specialist single-cohort reads expanded to 1.09.** Prior record was /058's 0.90; /061 establishes a new floor at −0.83. The basin distribution for BTC-only-specialist is wide and centered well below 0; favorable draws at /054 (+0.26) were ~+1.2σ tail events.
4. **Trade-rate floor not met (informational).** 9.33 IS trades/month + 5.86 OOS trades/month + 82 OOS total trades all below the 10/month AND 130-total floors. Structural too-thin observation: BTC-only single-symbol architecture cannot support a multi-symbol-portfolio replacement at this trade rate. Confirmed by Critic Check 7.
5. **No new EXPLORATION signal for cycle-7's cadence ledger.** /061 contributes to cycle-7's cadence count (4/10) but produces no new feature/architecture/labeling signal that compounds toward a CONFIRMATION-PORTFOLIO bundle. The diagnostic value is foundational (reproducibility established + BTC-only-specialist architecture flagged for closure) but does not add to roster.

## 5. Lessons

1. **The pipeline is provably deterministic at the LM Master Phase 4.5 HP recipe.** Future v1 iterations can rely on bit-exact reproducibility when running with `n_trials=1, seeds=1, subsample=1.0, colsample_bytree=1.0, bagging_freq=0, deterministic=True, num_threads=1, is_unbalance=False, force_col_wise=True, R3 OOD off`. Any future variance across runs at these HPs is attributable to genuine non-deterministic changes (data, code, dependencies), not hidden randomness.
2. **Central-tendency HP recipes are NOT centrally representative of the BTC-only-specialist basin distribution.** /061 demonstrates that "median/modal HP values from /054's trial range" lands in the unfavorable tail of the basin. This is a more general lesson: when the loss surface is multi-modal and Optuna's TPE finds favorable basins by hopping, the median of /054's HP range may not correspond to a favorable basin at all. **Codify into future Phase 4.5 LM Master advisories: when recommending central-tendency HPs, do NOT predict the IS Sharpe will land in the favorable basin's range — predict it will land in the basin distribution's mode, which may be very different from the favorable-draw mean.**
3. **BTC-only-specialist single-deterministic-fit at 48 features × 24 months is below detection floor.** Without Optuna basin-hopping, the BTC-only-specialist edge cannot be detected at single-seed=42. This is structural evidence that the BTC-only-specialist architecture's edge — if any — depends on lottery-favorable basin draws, NOT on a robust signal that any reasonable HP draw would surface. **Action: BTC-only-specialist as an axis for feature-engineering EXPLORATION is closed at v1 cycle-7. The architecture remains a valid component-decision input (where favorable-basin lottery draws can be averaged out at multi-seed ensemble at CONFIRMATION budget) but NOT a productive single-EXPLORATION axis at any HP recipe.**
4. **The catalog's full basin distribution should be measured before declaring the architecture closed.** The Critic's recommendation (10-seed Monte Carlo at /054's exact HPs) is the cleanest follow-up — it directly estimates the basin's percentiles and confirms whether /054 was a favorable tail OR representative. Wall-clock ~30 min at single-cell config. **This is recorded as a cycle-7 next-axis CANDIDATE per Section 6.**
5. **F1 reproducibility property + F2 prediction-miss does NOT impair the LM Master.** The Phase 4.5 → 7.4 calibration loop is working as designed: LM Master honestly accounts for prediction misses; QR + Critic + LM Master converge on diagnosis; the agent is improving its priors through this loop. No corrective action on the LM Master role; calibration-discount factor for BTC-only-specialist single-deterministic-fit predictions noted.
6. **LM Master Phase 4.5 misstatement about `basis_zscore_30` did NOT contaminate the diagnostic.** The misstatement ("48-col stack basis_zscore_30 added") was inherited by the Critic's Check 4 as a forensic flag. Resolution: the brief, runner, and feature stack all correctly used V1_FEATURE_COLUMNS_PRUNED (48 cols; basis_zscore_30 retired at /040). **Lesson: LM Master Phase 4.5 advisory text should be cross-checked against the brief's Section 3 "Proposed Changes" by the QR at Phase 5 drafting. The Critic should cross-check LM advisory claims against the importance CSV at Phase 7.5. Both should escalate to the QR if they conflict.**

## 6. Path Forward (recommended /062 axis)

Recommended /062 priorities, ordered by EV (per Critic + LM Master + brief Section 6 alignment):

### Option A (CRITIC-PREFERRED) — 10-seed Monte Carlo at /054 HPs (resolve basin question definitively)

Before closing the BTC-only-specialist architecture, run a 10-seed MC sweep at /054's exact HPs (Trial-15 best): n_est=190, depth=4, leaves=41, lr=0.019, subsample=0.985, colsample=0.888, min_child=96, reg_alpha=1.13, reg_lambda=0.07, confidence_threshold=0.55, training_days=260. Same monkey-patch mechanism as /061, but enqueue 10 different seeds (42, 123, 456, 789, 1001, 2002, 3003, 4004, 5005, 6006). Wall-clock ~30 min at single-cell config. Output: per-seed IS Sharpe distribution + percentile bounds. Decision criterion: if 5th-percentile IS Sharpe ≤ 0, the BTC-only-specialist architecture is decisively closed; if 5th-percentile > 0, the architecture has a measurable robust edge and warrants further investment.

Axis family: `methodology-substrate-test` (basin distribution probe at IDENTICAL substrate).

### Option B (LM-PREFERRED) — Structural pivot per `feedback_v3_structural_over_knob_exploration.md`

Skip the basin-measurement experiment; treat /061 as sufficient evidence that BTC-only-specialist single-EXPLORATION axis is closed. Pivot directly to:
1. **NEW feature family on ETH cohort** — ETH /055 was the only cohort with positive multi-seed Δ at /056 CONFIRMATION (+0.20). Test a NEW feature family that is orthogonal to cross-asset return-ratio, OI primitive, and funding rate (all 3 are exhausted at ETH). Candidates: ETH microstructure z-score (taker-buy-ratio z30 or vol-weighted realized vol z30); ETH Hurst regime (100-bar); ETH vol-of-vol z30.
2. **Pooled architecture with regime-conditional weighting** — Pool BTC+ETH+DOT+LTC+LINK as in baseline Model A, but condition the final position weight on an IS-regime classifier (Hurst high-vol regime gets lower weight). Tests whether the pooled architecture's OOS +0.66 is durable under explicit regime conditioning. Axis family: `risk-primitive`.

Axis family: `feature-family` OR `risk-primitive`.

### Option C — Wire up the regime tagger (methodology debt repayment)

Cumulative debt /049-/061 = 13 iterations with non-functional `per_regime.csv`. Codify a methodology iteration to: (a) audit which regime classifier is supposed to be invoked from `run_baseline_v1.py`, (b) wire it up, (c) regenerate per_regime.csv for /061 + /060 + /059 + /058 + /057 retroactively to validate the wiring, (d) commit the diagnostic. Wall-clock < 1h. Future EXPLORATION briefs can then cite per-regime stratified Sharpe.

Axis family: `methodology` (debt repayment; no model change).

### Reject

- **Re-running BTC-only-specialist with DIFFERENT hardcoded HPs.** /061 establishes that the central-tendency recipe lands in the basin's unfavorable tail; testing other hardcoded HP recipes is the "knob-tuning trap" warned against in `feedback_v3_structural_over_knob_exploration.md`. **Use Option A (10-seed MC at /054 HPs) instead if basin measurement is needed.**
- **Adding new features to V1_FEATURE_COLUMNS_PRUNED at BTC-only cohort without addressing the architecture-level basin distribution.** Single-EXPLORATION lottery at BTC-only single-seed=42 is now empirically exhausted as a search modality (/050, /051, /052, /053, /054, /058, /061 all at this cohort; basin spread 1.09; central-tendency recipe in unfavorable tail).
- **Running another methodology iteration that does not address either (a) basin measurement OR (b) regime tagger debt OR (c) a substantive architectural pivot.** Methodology family has now consumed /060 (Pool+Route disambiguation) + /061 (zero-randomness) — both ruled out branches of the basin-lottery diagnostic map. The next iteration should produce a substantive signal contribution OR repay methodology debt.

---

## 7. Cycle-7 Status

| Iter | Type | Axis family | Multi-seed mean IS Δ | Verdict | Baseline update? |
|---|---|---|---:|---|---|
| /057 | EXPLORATION-MULTI-SEED | feature-family (cross-asset ratio, LTC cohort) | +0.1082 | MULTI-SEED-WEAK-BASIN-LOTTERY | NO |
| /058 | EXPLORATION-MULTI-SEED | feature-family (OI short-window, BTC cohort) | +0.5697 | MULTI-SEED-SPECIALIST-BASIN-LOTTERY | NO |
| /059 | EXPLORATION | model-architecture (Pool+Route validation) | informational | NEGATIVE-INFORMATIONAL | NO |
| /060 | EXPLORATION | methodology (multi-seed Pool+Route disambiguation) | informational | NEGATIVE-INFORMATIONAL | NO |
| /061 | EXPLORATION-METHODOLOGY | methodology (zero-randomness diagnostic) | N/A (single-seed=1) | **NEGATIVE-DEEPER-ARCHITECTURE-OR-DATA-ISSUE** | NO |

Cycle-7 cadence: **5/10 EXPLORATIONs complete** (counting /057, /058, /059, /060, /061 — all post-cycle-6-CONFIRMATION-BLOCK). Cycle-7 produces 0 PROMISING / 0 SPECIALIST-CONFIRMED rows; 2 BASIN-LOTTERY at feature-family axis + 2 NEGATIVE-INFORMATIONAL at architecture/methodology axes + 1 NEGATIVE-DEEPER-ARCHITECTURE at methodology zero-randomness axis. The cycle is honestly characterizing the v1 substrate's structural limits at single-seed-or-3-seed EXPLORATION budget. Next CONFIRMATION-PORTFOLIO window opens at /067 if 5 more EXPLORATIONs accumulate.

**Axis-family rotation status** (last 5 EXPLORATIONs /057-/061):
- /057: feature-family
- /058: feature-family
- /059: model-architecture
- /060: methodology
- /061: methodology

Last 5 families: {feature-family×2, model-architecture×1, methodology×2}. NOT a 5-of-5 monoculture. /062 axis is UNCONSTRAINED by rotation discipline — QR can select feature-family, model-arch, labeling, universe, risk-primitive, OR methodology. Per Critic + LM Master Path Forward, the priority order is: methodology-substrate-test (Option A 10-seed MC) > feature-family (Option B ETH NEW family) > risk-primitive (Option B regime-conditional weighting) > methodology (Option C regime tagger debt).

Per-symbol regime-specialist mandate (per `feedback_v1_cycle6_per_symbol_regime_specialist_mandate.md`) continues into cycle-7 with the multi-seed-from-start reform.

---

## 8. Critic Verdict (Phase 7.5, summary)

**Verdict**: EXPLORATION — PROCEDURAL-PASS / SUBSTANTIVE-NEGATIVE / NO-MERGE (verdict-neutral; no BLOCK).

Key findings (compressed from `briefs-v1/iteration_v1-061/review.md`):
- **Procedural PASS**: bit-identical Run-1 ≡ Run-2 IS Sharpe −0.8260 confirmed by `diff -r` on trades.csv; pipeline is provably deterministic at the LM Master Phase 4.5 central-tendency HP recipe.
- **Substantive NEGATIVE**: IS Sharpe −0.826 outside both 60% band [−0.10, +0.20] and 90% band [−0.20, +0.30] of LM Master prediction; |Δ| = 0.91 = ~4.6σ; cleanly fires DEEPER-ARCHITECTURE-OR-DATA-ISSUE per the user's pre-registered basin-lottery diagnostic map.
- **Pre-registration compliance PASS** (procedural sub-hypothesis HIT; substantive sub-hypothesis MISS — both pre-registered; honest negative).
- **DSR/PSR informational only** at single-trial budget (n_eff=1; per `feedback_v3_dsr_mode_artifact.md`).
- **`basis_zscore_30` forensic flag — RESOLVED at QR closeout** (Section 2.5 above): LM Master Phase 4.5 misstatement, NOT runner misconfiguration. The brief, runner, and 48-col V1_FEATURE_COLUMNS_PRUNED are internally consistent and correct. `basis_zscore_30` was retired at /040.
- **Per-regime tooling debt** flagged (Critic Check 6 BORDERLINE) — cumulative /049-/061; recorded in Section 6 Option C.
- **Trade-rate floor below 10/month** in both IS + OOS — informational for EXPLORATION; structural too-thin for BTC-only single-symbol cohort as a portfolio replacement.
- **Adversarial-stress 8+1 test**: PASS; the iteration's results are interpretable under the adversarial frame; no hidden defect that would change the diagnosis.

Critic's recommendation (softened from LM Master's structural-closure call): run 10-seed Monte Carlo at /054's exact HPs (cycle-7 Option A above) before declaring the BTC-only-specialist architecture closed. Wall-clock cheap (~30 min); resolves the "favorable tail vs representative" question definitively. If MC 5th-percentile ≤ 0, the axis closes; otherwise it warrants further investment.

QR adopts the Critic's softer recommendation as Section 6 Option A (first-tier candidate). LM Master's harder structural-closure call is preserved as Section 6 Option B (second-tier; viable if QR prefers to skip basin measurement and pivot directly).

---

## 9. Path Forward (from Critic, verbatim per v1 Discipline §4)

From `briefs-v1/iteration_v1-061/review.md` §"Recommendations for Next Iteration":

1. **RESOLVE THE FEATURE-PROVENANCE FORENSIC.** Before any next axis runs, the QR should commit a 1-paragraph note in the iteration diary documenting whether `basis_zscore_30` was in /061's training set. — **RESOLVED at this closeout Section 2.5: NO, basis_zscore_30 was correctly absent; retired at /040; LM Master Phase 4.5 misstatement; brief + runner + feature stack internally consistent.** No reclassification needed.

2. **CONSIDER LM MASTER §3 (10-seed MC at /054 HPs)** as the cleanest follow-up before architectural closure. Wall-clock ~30 min at single-cell config; resolves the "is /054 a favorable tail or representative" question definitively. — **Adopted as Section 6 Option A (first-tier candidate for /062).**

3. **DROP `dot_vs_btc_ret_ratio_30` AND `eth_vs_btc_ret_ratio_30`** in any next BTC-only-cohort stack (both have 0.0 importance; pure dead weight). — **Adopted; flagged for next BTC-only-cohort iteration as a precondition. NOT a /062 axis on its own (too small a change), but baked into any /062 iteration that touches the BTC-only cohort.**

4. **PIVOT AWAY FROM BTC-ONLY-SPECIALIST KNOB-TUNING** if the LM Master §3 MC reveals 5th-percentile IS Sharpe ≤ 0 at the favorable HPs. The structural alternatives (pooled architecture, multi-symbol cohort, new feature family) are all higher-EV per `feedback_v3_structural_over_knob_exploration.md`. — **Adopted as Section 6 Option B (second-tier; activates conditional on Option A's 5th-percentile result).**

---

**End of diary.**
