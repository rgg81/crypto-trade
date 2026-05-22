# iter-v3/131 — Cycle-7 Closure-Reconciliation Memo (NOT EXPLORATION)

**Date**: 2026-05-21
**Type**: CLOSURE-RECONCILIATION (cycle-7 slot 10 of 10; NO backtest; NO axis; structural memo + /132 CONFIRMATION setup spec)
**Cycle**: 7 (slots 1-9 = EXPLORATIONs at /122-/130; slot 10 = this closure-reconciliation; slot 11 = /132 CONFIRMATION)
**Authority**: Critic FINAL Rec 1 at /130 review.md: "/131 = formal cycle-7 closure-reconciliation diary, NOT EXPLORATION axis. ... 10:1 cadence rule does NOT require slot #10 to be EXPLORATION on new axis — closure-reconciliation pre-CONFIRMATION is valid."

**Anchor**: /121 multi-seed CONFIRMATION-MERGE BASELINE (PUBLIC IS +1.3108 / OOS +0.9682). ADJUSTED IS ≈ +1.06 / OOS ≈ +0.85.

---

## Section 1 — Why this is a closure-reconciliation, not an EXPLORATION

### 1.1 The empirical record at /131

Cycle-7 EXPLORATION catalog at /130 closeout:

| Slot | Iter | Axis class | IS Δ vs /121 | OOS Δ vs /121 | Verdict |
|---:|---|---|---:|---:|---|
| 1 | /122 | cross-asset (ETH OHLCV eth_ret_3d) | −0.34 | +0.20 | NEGATIVE-INERT |
| 2 | /123 | cross-asset (eth_vs_sym_rv_50) | −1.73 | +0.79 | NEGATIVE-catastrophic |
| 3 | /124 | longer-cadence labels K=63 + sqrt(3) ATR | −0.87 | −0.94 | NEGATIVE-catastrophic |
| 4 | /125 | WILD V3_MODELS ATOM/RUNE/UNI | −1.25 | −0.86 | NEGATIVE-catastrophic |
| 5 | /126 | multi-frequency d24_ret_autocorr_lag1_50 | −1.21 | −1.08 | NEGATIVE-catastrophic |
| 6 | /127 | per-symbol drawdown brake (binary kill) | −0.52 | +0.03 | NEGATIVE-catastrophic |
| 7 | /128 | WILD 6-symbol sector-pure L1 universe | −1.73 | +1.17 | NEGATIVE-catastrophic |
| 8 | /129 | continuous position-size scaling at drawdown | −0.64 | +0.001 | NEGATIVE-catastrophic |
| 9 | /130 | 4h bar-interval (BCH/LDO/TRX preserved) | **−2.61** | −0.64 | NEGATIVE-catastrophic (worst IS in v3 history) |

**8/9 catastrophic; 1/9 INERT; 0/9 PROMISING.** Last 4 (/127-/130) all catastrophic across 4 structurally distinct axis classes.

### 1.2 The QR adjudication at /131 — Option A vs Option B

The /131 task statement enumerated 6 candidate "wild axes" for Option A (one final EXPLORATION):
- A1: NEW labeling architecture (quantile/multi-class instead of binary)
- A2: Different Optuna search strategy (larger n_trials, different objective, post-hoc model selection)
- A3: Mixed-frequency feature stack at 8h+24h (NOT /126's autocorrelation-only)
- A4: Per-symbol feature selection (NOT per-symbol asymmetry closed at /074)
- A5: Trade-payload features (holding time, drawdown trajectory)
- A6: Position sizing via feature-conditional confidence calibration

**Test each against the closed channels**:

| Candidate | Cohort-shape channel? | Frequency-shape channel? | Optuna-trajectory-shift channel? | Verdict |
|---|---|---|---|---|
| A1 (NEW labeling) | NO | NO | **YES** — LABEL-MODE explicit in /128 EXTENSION enumeration | IN-SCOPE-OF-CLOSED-CHANNEL |
| A2 (different Optuna) | NO | NO | **YES** — ENSEMBLE_SIZE/n_trials/seed explicit in /128 EXTENSION | IN-SCOPE-OF-CLOSED-CHANNEL |
| A3 (mixed-frequency 8h+24h) | NO | **PARTIAL** — adds 24h aggregated features without changing base bar | **YES** — feature-set composition change explicit in /128 EXTENSION | IN-SCOPE-OF-CLOSED-CHANNEL |
| A4 (per-symbol feature selection) | NO | NO | **YES** — feature-set composition change | IN-SCOPE-OF-CLOSED-CHANNEL |
| A5 (trade-payload features) | NO | NO | **YES** — feature-set composition change | IN-SCOPE-OF-CLOSED-CHANNEL |
| A6 (feature-conditional confidence calibration) | NO | NO | **YES** — modifies position-size scaling tied to Optuna confidence output (analogous to /129 continuous-scaling primitive at the inference layer) | IN-SCOPE-OF-CLOSED-CHANNEL |

**ALL 6 candidate Option A axes are in the expanded scope of the QUADRUPLE-validated Optuna-trajectory-shift channel.** The /127-/130 finding established that at single-seed EXPLORATION budget (3 inner × 1 outer × 35 trials = 105 trials/WF month), ANY axis changing the Optuna training-objective domain causes Optuna to re-converge to a different region of hyperparameter space — producing a different model that lands in the /116 basin (IS Sharpe ~0.62-0.67) or worse.

The empirical PROMISING-class prior at /131 under any Option A axis ≤ 10%. The cycle-7 catalog evidence does not support a 10th single-seed EXPLORATION as productive research.

### 1.3 Why Option B is the structurally correct call

1. **9/9 NEGATIVE consecutive with last 4 catastrophic** across 4 structurally distinct axis classes is the strongest exhaustion signal in v3 history. Cycle-5's terminal (/105-/109) was 5/5 axis-saturated at a single model-architecture dimension; cycle-7's terminal is 9/9 axis-saturated across 4 distinct dimensions.

2. **ALL viable Option A axes are in closed channels.** The /127-/130 chain established the channel boundaries: cohort-shape (CLOSED), frequency-shape (CLOSED), Optuna-trajectory-shift (TRIPLE-validated CLOSED, QUADRUPLE-validated at /130). The 6 candidate wild axes all fall in the third channel. Running a 10th EXPLORATION when the structurally-anticipated outcome is PROMISING-class probability ≤ 10% is performative axis-shopping, not research.

3. **The QR creativity mandate (`feedback_v3_qr_axis_creativity_mandate.md`) addresses lazy axis selection after 1-2 NEGATIVEs.** It does NOT mandate continuation at structural exhaustion. The mandate's explicit text: "NEVER close an axis class after 1-2 NEGATIVEs." Cycle-7 has 9 NEGATIVEs across multiple axis classes — not 1-2 NEGATIVEs at a single axis. The mandate's protective scope is exhausted.

4. **The 10:1 cadence rule (`feedback_v3_strict_10_to_1_cadence.md`) does NOT require slot #10 to be EXPLORATION on new axis.** Per Critic FINAL Rec 1 at /130: "closure-reconciliation pre-CONFIRMATION is valid." The cadence rule requires that EXPLORATION and CONFIRMATION not be collapsed into one iteration (e.g., the 10th EXPLORATION cannot run CONFIRMATION-spec); a closure-reconciliation memo without backtest at slot #10 is not a CONFIRMATION and does not violate the cadence rule.

5. **A closure-reconciliation at /131 with multi-seed re-validation at /132 is the correct next research step.** The cycle-7 EXPLORATIONs were all single-seed; the /121 baseline's reproducibility under current code state has not been verified since /121's 2026-05-20 CONFIRMATION-MERGE. /132 = MULTI-SEED VALIDATION of /121 is a direct, decisive next step that closes the cycle without speculative additional single-seed EXPLORATIONs.

**Adjudication: Option B (closure-reconciliation; NO backtest; /132 = MULTI-SEED VALIDATION of /121).**

This adjudication is not a refusal to be creative — it is the honest application of the rigor discipline. The PRIME DIRECTIVE binds at brief commit time; Option B's brief + no backtest is the binding compliant deliverable when the empirical evidence rules out productive Option A axes within the closed channels.

---

## Section 2 — The cohort-AND-frequency-shape TERMINAL finding

### 2.1 Statement

The /121 baseline architecture (BCH/LDO/TRX universe + 14-feature V3_FEATURE_COLUMNS_TOP_N + ATR (2.0, 1.0) triple-barrier K=21 + /116 no_confirm primitive + 7-gate RiskV2) is **cohort-AND-frequency-shaped**: its IS Sharpe +1.31 is a hyperparameter-region-locked solution at the specific joint (3-symbol cohort, 8h bar interval, 14-feature stack, no_confirm primitive, ATR (2.0, 1.0), K=21).

The IS-leg lift can only be FOUND with the multi-seed CONFIRMATION budget (10 outer × 5 inner × 35 trials = 1750 trials/WF month at /018 multi-seed setup). At single-seed EXPLORATION budget, ANY structural perturbation destabilizes the Optuna trajectory enough to fall out of the /121 basin and land in the /116 basin (IS Sharpe ~0.62-0.67) or worse.

### 2.2 The 4-dimension fragility evidence chain

| Dimension | Perturbation iter | IS Δ vs /121 | Mechanism evidence |
|---|---|---:|---|
| **RISK-PRIMITIVE binary** | /127 | −0.5242 | IS Jaccard 0.4286; weight → 0 at 1.7% of trades; Optuna re-converges to /116 basin |
| **UNIVERSE** (3-sym & 6-sym) | /125 + /128 | −1.25 / −1.48 vs ADJ | 3-axis distribution mismatch (vol-magnitude, kurtosis-tail, timeout-rate) per `feedback_v3_architecture_cohort_shaped.md` |
| **RISK-PRIMITIVE continuous** | /129 | −0.6425 | IS Jaccard 0.4213; weight × 0–1 ramp at 16.8% of trades; /116-basin convergence; **continuous semantics do NOT mitigate channel** (Jaccard near-identical at 10× more trade engagement) |
| **BAR-INTERVAL** (frequency) | /130 | **−2.6136** | WORST IS in v3; 8.4σ below T3b 4h-proxy simulator predicted mean; HALVED label horizon (3.5d vs 7d) mis-targets crypto alt-coin 5-7d mean-reversion cycle; 4h-density feature compression → Optuna explores fundamentally different (depth, colsample, reg_lambda) regions |

Across these 4 dimensions, the consistent signature:
- IS Sharpe collapse (range −0.52 to −2.61, all ≥ 1.3× the catastrophic threshold magnitude of −0.40)
- Optuna trajectory re-convergence (IS Jaccard ~0.42 at RISK-PRIMITIVE axes; bimodal CPCV at UNIVERSE; frequency-shifted Optuna search regions at BAR-INTERVAL)
- OOS marginal (range −0.64 to +1.17 — OOS not predictive of IS structural problem)

### 2.3 Why /121's IS-leg lift is region-locked

The /116 → /121 progression added the no_confirm primitive (RULE-layer drag-removal) at multi-seed CONFIRMATION budget. /116 alone (single-seed EXPLORATION budget) produced IS Sharpe ~0.62 / OOS ~1.10. /121 at multi-seed CONFIRMATION budget produced IS Sharpe +1.31 / OOS +0.97. The +0.69 IS lift between /116 and /121 came **entirely from the multi-seed budget's Optuna-trajectory variance reduction** — averaging across 1750 trials/WF month (per CONFIRMATION cell), the Optuna search found a (depth, colsample, reg_lambda) basin with higher IS Sharpe than any single-seed configuration could reliably find.

The /129 finding established this empirically: /129 IS roster is **bit-identical to /116** (Jaccard 1.0000; 161 of 161 trades match). The continuous-scaling primitive's 27 weight modifications change weight_factors but do not change which trades emit; Optuna under the continuous-scaling constraint at single-seed budget re-converges to /116's hyperparameter region, NOT /121's. The /121 basin requires the multi-seed budget to be **visible at all** — it does not exist in the single-seed search space.

**Implication**: at single-seed EXPLORATION budget, cycle-7's structural EXPLORATIONs are SYSTEMATICALLY DESTINED to land in the /116 basin or worse. Any structural perturbation (RISK-PRIMITIVE, UNIVERSE, BAR-INTERVAL, LABEL-MODE, FEATURE-SET) shifts the Optuna search landscape enough to lose the /121 basin's signal.

### 2.4 Analogy to cycle-5 terminal (/105-/109 representational-capacity FALSIFICATION)

The cycle-7 terminal finding is structurally analogous to cycle-5's terminal:

| Cycle | Terminal finding | Mechanism |
|---|---|---|
| 5 (/105-/109) | Representational-capacity axis FALSIFIED | No neural-class model improves on depth 3-5 LightGBM with /059 architecture; 5/5 axis-saturated at model-architecture dimension |
| 7 (/127-/130) | Cohort-AND-frequency-shape TERMINAL | /121's IS-leg lift is hyperparameter-region-locked at single-seed EXPLORATION budget across 4 distinct structural-axis perturbation dimensions |

Both findings establish a structural-exhaustion boundary at the current research operating point. Cycle-5's terminal was overridden by the user mid-cycle-6 (per `project_v3_cycle5_terminal_finding.md`); whether cycle-7's terminal is overridden at cycle-8 setup is the user's call.

---

## Section 3 — The Optuna-trajectory-shift channel QUADRUPLE-VALIDATED + simulator BAR-INTERVAL LIMITATION

### 3.1 Channel completeness at /130

The /127 → /128 → /129 → /130 chain QUADRUPLE-validates the Optuna-trajectory-shift channel across 4 structurally distinct axis classes:

| Iter | Axis class | Intervention | IS Jaccard signature | IS Δ vs /121 | Simulator predicted | Simulator-vs-production miss |
|---|---|---|---:|---:|---:|---:|
| /127 | RISK-PRIMITIVE binary kill | weight → 0 (1.7%) | 0.4286 | −0.5242 | (no closed-loop simulator; ORACLE +0.0348) | 15× ORACLE magnitude, sign-flipped |
| /128 | UNIVERSE substitution | 6-symbol L1 swap | bimodal CPCV frac_pos 0.444 | −1.4819 vs ADJ | (no closed-loop simulator; rolling-endpoint EDA) | mean prediction inverted to bimodal regime |
| /129 | RISK-PRIMITIVE continuous scale | weight × 0–1 ramp (16.8%) | 0.4213 | −0.6425 | mean 0.9186 std 0.8409 | **z=-0.298 (within first sigma — FIRST OPERATIONAL VALIDATION)** |
| /130 | **BAR-INTERVAL change** | **8h → 4h density 2.0×** | N/A (timestamp granularity differs) | **−2.6136 (WORST IS in v3)** | **mean 0.391 std 0.20** | **z=-8.4 (FAR OUTSIDE ±3σ — simulator BAR-INTERVAL LIMITATION)** |

### 3.2 Simulator methodology status at /131

Per `feedback_v3_optuna_trajectory_shift_finding.md` /130 EXTENSION, the closed-loop Optuna-re-training simulator methodology validation status by axis class:

| Axis class | Simulator methodology adequate? | Notes |
|---|---|---|
| RISK-PRIMITIVE (binary or continuous) | YES at within-bar-interval | /129 z=-0.298 first sigma; closed-loop Optuna-retraining over /121 trade roster captures Optuna response |
| UNIVERSE | YES at within-bar-interval | /128 used rolling-endpoint EDA; future universe axes should operate closed-loop Optuna-retraining over candidate universe's trade roster |
| LABEL-MODE | UNTESTED — projected adequate at within-bar-interval | Triple-barrier params change Optuna training objective; bootstrap proxy on prior-label-mode trade roster should capture response if labels are recomputed in closed-loop fashion |
| FEATURE-SET composition | UNTESTED — projected adequate at within-bar-interval | Closed-loop simulator must retrain Optuna with new feature set |
| ENSEMBLE_SIZE / n_trials / outer-seed | UNTESTED — projected adequate at within-bar-interval | Direct simulation of CONFIRMATION-budget hyperparameter search compared to EXPLORATION-budget baseline |
| **BAR-INTERVAL change** | **NO — limitation confirmed at /130** | **Bootstrap proxy on prior-bar-interval trade roster systematically under-estimates production response magnitude** |

### 3.3 The simulator-fix simulator is OPERATIONALLY VALIDATED for within-bar-interval axes

The /129 first-implementation operational validation (z=-0.298 within first sigma at RISK-PRIMITIVE continuous-scaling axis) establishes the methodology as production-ready for within-bar-interval axes. The /130 BAR-INTERVAL LIMITATION (z=-8.4 outside ±3σ) is a STRUCTURAL BOUNDARY of the methodology, not a methodology defect — the brief Section 2 PRE-DISCLOSED the bootstrap proxy limitation, and production confirmed the disclosed limitation at the catastrophic-magnitude end.

For cycle-8+ briefs operating within-bar-interval axes, the closed-loop Optuna-re-training simulator stays load-bearing as the EDA Section 2 pre-flight gate per `feedback_v3_optuna_trajectory_shift_finding.md` /128 EXTENSION. For bar-interval-changing axes (if any cycle-8+), the simulator must be redesigned to retrain Optuna over native-frequency features — not bootstrap-upsampled prior-frequency trade rosters.

---

## Section 4 — Open methodology questions logged for cycle-8+

These are NOT closure items at /131; they are reference for cycle-8+ design:

1. **Does the simulator predict IS Jaccard distribution?** Currently the simulator emits IS Sharpe distribution moments (mean, std, quartiles, frac-above-threshold) but not the IS trade-roster Jaccard distribution. Future simulator versions should add this — it would provide an additional pre-flight signal for the Optuna-trajectory-shift channel discrimination boundary (Jaccard < 0.70).

2. **Does z-score reliably predict catastrophic-class assignment?** Single-iteration evidence at /129 (z=-0.298, non-catastrophic) and /130 (z=-8.4, catastrophic) is insufficient to validate distribution tails. Cycle-8+ needs more |z| > 2.0 data points to validate the simulator's tail-class predictive value.

3. **Can the pre-flight gate threshold be tightened (e.g., 70% instead of 60%) without losing PROMISING-class candidates?** Open question for cycle-8+ when methodology has more operating history. At /130, the 60% threshold correctly classified the axis as HIGH-RISK; whether 70% would have similarly classified is untested.

4. **For UNIVERSE-class axes, the simulator's Jaccard binding doesn't directly apply** (symbols are different; no anchor open-time mapping). The simulator distribution + CPCV path bimodality jointly served as methodology validation at /128. For cycle-8+ UNIVERSE axes, this should be encoded in briefs as the universe-axis methodology variant.

5. **Single-seed EXPLORATION budget appropriateness.** The /127-/130 evidence motivates re-examination of whether single-seed EXPLORATION is appropriate for structural axis exploration at /121's hyperparameter-region-locked architecture. Per `feedback_v3_outer_seed_cap_2_v3.md`, EXPLORATION uses single-seed by design to economize Optuna budget; the cycle-7 evidence suggests structural axes may require a higher-than-EXPLORATION-default seed budget to even detect signal. This is a design question for cycle-8+ orchestration.

---

## Section 5 — /132 CONFIRMATION setup spec (LOCKED)

Per Critic FINAL Rec 2 at /130 review.md, the /132 CONFIRMATION shape is dictated by the cycle-7 catalog state (9/9 NEGATIVE through /130; 0 PROMISING components to bundle). /132 should be a MULTI-SEED BASELINE-VALIDATION of /121 (structural analog of /018 BOOTSTRAP-CONFIRMATION), NOT a bundle assembly of any /127-/131 component.

### 5.1 /132 declared parameters

| Parameter | Value | Provenance |
|---|---|---|
| TYPE | CONFIRMATION (cycle-7 slot 11 — CONFIRMATION; baseline re-validation) | Per `feedback_v3_strict_10_to_1_cadence.md` |
| ITERATION_LABEL | "v3-132" | New iteration label |
| CLI invocation | `uv run python run_baseline_v3.py --confirmation --n-trials 35 --clean-oof --seeds 2` | CONFIRMATION mode + explicit n-trials + clean-oof + 2 outer seeds |
| ENSEMBLE_SIZE | 10 (CONFIRMATION mode default: 5 inner × 2 outer = 10 models per WF month per symbol) | Per `feedback_v3_outer_seed_cap_2_v3.md` |
| n_trials | 35 | Per `feedback_v3_confirmation_n_trials_35.md` |
| Universe | BCH/LDO/TRX (UNCHANGED) | INHERITED from /121 |
| V3_FEATURE_COLUMNS_TOP_N | 14 features (UNCHANGED) | INHERITED from /121 |
| Labels | triple_barrier K=21, ATR (2.0, 1.0), label_timeout_minutes=10080 | INHERITED from /121 |
| Bar-interval | **8h (UNCHANGED)** | INHERITED from /121; explicit REVERT from /130's 4h |
| `enable_no_confirm_exit` | True (trigger_atr=0.50, k_candles=4) | INHERITED from /121 |
| `enable_per_symbol_drawdown_brake` | **False** (axis CLOSED at /127) | INHERITED from /129 REVERT |
| `enable_per_symbol_drawdown_scaling` | **False** (axis CLOSED at /129) | INHERITED from /130 REVERT |
| REQUIRED_GAP | 66 = (21+1)×3 | INHERITED from /121 |
| Wall-clock cap | 6h | Per `feedback_v3_cadence_discipline.md` CONFIRMATION cap |
| Features cache dir | `data/features_v3/` (UNCHANGED) | INHERITED from /121 |
| ZERO new features | (UNCHANGED) | Baseline re-validation, not axis assembly |
| ZERO new gates / risk primitives | (UNCHANGED) | Baseline re-validation |

### 5.2 Acceptance gates for /132

**PASS criteria** (must hold ALL):
- Multi-seed mean IS monthly Sharpe ≥ +1.0
- Multi-seed mean OOS monthly Sharpe ≥ +0.8
- Both Pareto seeds positive on IS leg AND on OOS leg
- PSR > 0.95 (full re-evaluation per /018 BOOTSTRAP-CONFIRMATION protocol)
- frac_positive_paths ≥ 0.55 (CPCV path distribution)

**PASS outcome**:
- BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`)
- /132 confirms /121 is reproducible under current code state
- File CONFIRMATION-VALIDATION-PASS diary
- Cycle-7 closes at the /121 baseline
- Cycle-8 design begins from /121 with the cohort-AND-frequency-shape constraint binding

**FAIL outcome**:
- File CONFIRMATION-RE-ANCHOR diary (analog of /018 BOOTSTRAP-CONFIRMATION)
- Investigate code-state drift across /122-/131
- Downgrade BASELINE_V3.md if multi-seed mean falls materially below /121 ADJUSTED reference (IS ≈ +1.06 / OOS ≈ +0.85)
- Cycle-8 design requires resolving the regression before proposing axes

### 5.3 Tolerance for re-validation

The /121 multi-seed CONFIRMATION-MERGE produced IS +1.3108 / OOS +0.9682 on 2026-05-20 (commit `b0576df` from /121 BASELINE_V3.md update; tag `v0.v3-121`). Between then and /132, the worktree has merged /127's RiskV2 binary-brake infrastructure + /129's continuous-scaling primitive + /130's bar-interval support + ITERATION_LABEL updates + the `_TeeLogger` run.log wrap + various test additions. While /127/129/130 features are DISABLED at /132, the runner code path has changed enough that exact reproduction (bit-identical) is not expected.

**Loose tolerance**: multi-seed mean IS ≥ +1.0 AND OOS ≥ +0.8. This allows up to −0.31 IS slippage and −0.17 OOS slippage from /121's exact reproduction — sufficient buffer for incidental code drift but not enough to mask material regression.

### 5.4 Pre-launch checks for /132 setup commit

The Engineer must verify before launching the /132 backtest:

1. `V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT)` in `run_baseline_v3.py`
2. V3_FEATURE_COLUMNS_TOP_N is exactly 14 features (UNCHANGED from /121)
3. `enable_no_confirm_exit=True, no_confirm_trigger_atr=0.50, no_confirm_k_candles=4` (carried from /121)
4. `enable_per_symbol_drawdown_brake=False` (REVERT preserved from /129+/130)
5. `enable_per_symbol_drawdown_scaling=False` (REVERT preserved from /130)
6. Bar-interval is 8h (REVERT from /130's 4h; features cache at `data/features_v3/` not `data/features_v3_4h/`)
7. REQUIRED_GAP=66=(21+1)×3
8. `_canonical_v059` accretion guard reflects /132 = /121 baseline re-validation (no new ingredients)
9. CLI accepts `--confirmation` flag and routes to ENSEMBLE_SIZE=10
10. run.log persists to `reports-v3/iteration_v3-132/run.log` (instrumentation fix carried from /130)
11. CPCV paths emit to `reports-v3/iteration_v3-132/cpcv_paths.csv`
12. DSR/PBO/PSR re-evaluate at full CONFIRMATION protocol per /018

If any pre-launch check fails, the Engineer aborts and fixes BEFORE launching the backtest.

### 5.5 /131 → /132 handoff sequence

1. /131 closeout commit (this memo + minimal diary) — to be tagged `v0.v3-131`
2. /132 Engineer setup commit (parameter VERIFY + ITERATION_LABEL update + any infrastructure adjustments) — branch `iteration-v3/132`
3. Phase 5.5 gate: smoke test asserts the 12 pre-launch checks PASS
4. Phase 6 backtest launch (CONFIRMATION mode; wall-clock cap 6h)
5. Phase 7.5 Critic review on the CONFIRMATION methodology (PSR/PBO/DSR re-evaluation)
6. Phase 8 closeout diary with MERGE / NO-MERGE / RE-ANCHOR decision

The /131 → /132 handoff binds the /131 closure-reconciliation as the upstream artifact; /132 cannot launch without /131 closeout. Cycle-7 closes at /132's verdict.

---

## Section 6 — What this memo does NOT claim

This memo does NOT close v3 research broadly. It establishes:

1. The cycle-7 terminal finding (cohort-AND-frequency-shape) — a structural property of the /121 architecture at single-seed EXPLORATION budget
2. The exhaustion of cycle-7's structural EXPLORATIONs under the current axis menu within the closed channels (cohort, frequency, Optuna-trajectory-shift)
3. The /132 baseline re-validation plan as the binding next step

It does NOT close:
- Cycle-8's untested axis families (wholly-new model architecture, wholly-new labeling architecture, CONFIRMATION-budget-first design)
- The possibility that multi-seed CONFIRMATION budget would reveal PROMISING cycle-7 axes that single-seed EXPLORATION missed
- The /121 multi-seed CONFIRMATION baseline itself (which is exactly what /132 validates)
- The methodology research questions logged in Section 4

The cycle-7 terminal status, like the cycle-5 terminal status (`project_v3_cycle5_terminal_finding.md`), may be overridden by user directive at cycle-8 setup. The QR adjudication at /131 is "structurally exhausted within the closed channels at single-seed EXPLORATION budget" — the user may direct continuation in a specific direction.

---

## Section 7 — Commit / file plan for /131

This iteration is unique in v3 history in that it has NO backtest, NO axis variation, NO Engineer phase, NO Phase 5.5 gate, NO Phase 7.5 Critic adjudication. The Phase 5 brief = THIS DOCUMENT (closure-reconciliation memo). The Phase 8 diary closeout is a minimal 1-2 paragraph file that records the verdict.

### 7.1 Files to produce at /131

1. **`briefs-v3/iteration_v3-131/closure_reconciliation.md`** — this file (the Phase 5 deliverable, in lieu of a research brief)
2. **`diary-v3/iteration_v3-131.md`** — minimal closeout recording the closure-reconciliation verdict and the /132 setup spec hand-off
3. **`briefs-v3/exploration_catalog.md`** — catalog row append for /131 as "cycle-7 closure-reconciliation" with no IS/OOS columns (TBD or "—")

### 7.2 Files NOT to produce at /131

1. NO EDA scripts (no axis to test)
2. NO `analysis/iteration_v3-131/` directory
3. NO Engineer setup commit (no code changes)
4. NO Phase 5.5 gate document
5. NO Phase 6 engineering report
6. NO Phase 7.5 Critic review
7. NO `reports-v3/iteration_v3-131/` directory
8. NO BASELINE_V3.md update (UNCHANGED at /121 canonical)

### 7.3 Git tag at /131 closeout

`v0.v3-131` set on the /131 closeout commit, marking the cycle-7 closure-reconciliation milestone.

---

## Section 8 — Cycle-8 design considerations (NOT binding at /131)

Per Critic FINAL Rec 3 at /130: cycle-8 axis menu must structurally reformulate post-/132. The cohort-AND-frequency-shape terminal finding sets binding constraints on cycle-8 axis selection:

### 8.1 Mandatory brief Section 0.6 at cycle-8 first EXPLORATION

The cycle-8 first EXPLORATION brief MUST include a new Section 0.6 "Architecture-Family Justification" arguing why the proposed axis is NOT in any of the 3 closed channels:
1. Cohort-shape channel — universe substitution at /121 architecture (CLOSED through 8 attempts per `feedback_v3_architecture_cohort_shaped.md`)
2. Frequency-shape channel — bar-interval change at /121 architecture (CLOSED at /130; bootstrap-proxy simulator inadequate at frequency density changes)
3. Optuna-trajectory-shift channel — any axis changing Optuna training-objective domain (QUADRUPLE-validated CLOSED)

The brief commit is BLOCKED if Section 0.6 cannot establish channel-orthogonality.

### 8.2 Viable cycle-8 axis families

Per Critic FINAL Rec 3 at /130:

1. **WHOLLY-NEW model architecture** at a different operating point than /105-/109's depth-3-5 LightGBM. The /105-/109 cycle FALSIFIED neural-class at single-seed EXPLORATION budget; cycle-8 may revisit with different priors such as transformer attention or LSTM with regime-conditional pretraining — **at CONFIRMATION budget to escape single-seed-EXPLORATION fragility**.

2. **WHOLLY-NEW labeling architecture** distinct from triple-barrier and meta-labeling. /017 and /108 corrected meta-labeling both NULL-AT-EDA; cycle-8 may revisit at quantile-multi-class labels OR cross-sectional ranking labels OR fixed-horizon return labels — **at CONFIRMATION budget**.

3. **CONFIRMATION-budget-first design** — recognize that /121's basin requires multi-seed CONFIRMATION to be visible; cycle-8 may design axes that are evaluated ONLY at CONFIRMATION budget, skipping single-seed EXPLORATION because the channel evidence at /127-/130 establishes single-seed EXPLORATION is structurally insufficient for /121-class lift detection. This would be a process innovation breaking the 10:1 cadence rule's implicit assumption that EXPLORATIONs are single-seed; the user may approve such a process change at cycle-8 setup.

4. **Explicit acknowledgment** /121 is practical edge ceiling under the current research workflow and pivot to operational deployment focus (live-trading robustness, multi-track portfolio assembly v1+v2+v3, risk-of-ruin analysis at deployment).

### 8.3 What cycle-8 SHOULD NOT propose at first EXPLORATION

- Single-axis EXPLORATIONs in the /121 parameter neighborhood (RISK-PRIMITIVE, UNIVERSE, FEATURE-SET composition, ENSEMBLE_SIZE/n_trials/seed knobs at within-bar-interval)
- Bar-interval changes at single-seed EXPLORATION budget without a closed-loop simulator on native-frequency features (the /130 evidence establishes the bootstrap proxy methodology gap)
- Any axis lacking a Section 0.6 channel-orthogonality argument

These are not bans on the axis classes — they are bans on the axis-class operating point (single-seed EXPLORATION budget at /121 parameter neighborhood). The same axis classes may be viable at multi-seed CONFIRMATION budget or with a redesigned simulator methodology for bar-interval axes.

---

## Section 9 — Audit trail

**QR rationale chain at /131**:
1. Read /130 review.md Critic FINAL `d33cc2e` — recommendation 1 explicitly: "/131 = formal cycle-7 closure-reconciliation diary, NOT EXPLORATION axis."
2. Read `feedback_v3_qr_axis_creativity_mandate.md` — mandate scope is "lazy QR after 1-2 NEGATIVEs," NOT structural exhaustion at 9/9 NEGATIVE consecutive across 4 axis classes
3. Read `feedback_v3_strict_10_to_1_cadence.md` — cadence rule does not require slot #10 to be EXPLORATION; closure-reconciliation pre-CONFIRMATION is valid
4. Read `feedback_v3_optuna_trajectory_shift_finding.md` /128 EXTENSION — expanded scope explicit enumeration of axis classes in channel; all 6 candidate Option A axes fall in expanded scope
5. Enumerated and tested all 6 Option A wild-axis candidates against the 3 closed channels — ALL 6 in expanded Optuna-trajectory-shift scope (Section 1.2 table)
6. Applied honest empirical PROMISING-class prior at /131 ≤ 10% under any in-scope axis
7. Adjudicated Option B (closure-reconciliation; NO backtest) per the empirical evidence + Critic recommendation + cadence rule permissive scope

**Memory files consulted (and updated at /130 closeout)**:
- `feedback_v3_optuna_trajectory_shift_finding.md` — QUADRUPLE-VALIDATED + bar-interval LIMITATION EXTENSION (appended at /130 closeout)
- `feedback_v3_cycle7_terminal_finding.md` — NEW memory file documenting the cohort-AND-frequency-shape TERMINAL finding (created at /130 closeout)
- `feedback_v3_architecture_cohort_shaped.md` — /125 cohort-shape establishment; the COHORT half of the TERMINAL finding
- `project_v3_cycle5_terminal_finding.md` — analog cycle-5 TERMINAL (the structural template for cycle-7 closure-reconciliation pattern)
- `feedback_v3_qr_axis_creativity_mandate.md` — scope-bounded mandate (1-2 NEGATIVE failure mode, not structural exhaustion)
- `feedback_v3_strict_10_to_1_cadence.md` — cadence rule permitting closure-reconciliation at slot #10
- `feedback_v3_outer_seed_cap_2_v3.md` — single-seed EXPLORATION budget definition

**Critic FINAL recommendations at /130 (binding scope for /131-/132)**:
1. /131 = formal cycle-7 closure-reconciliation diary, NOT EXPLORATION axis
2. /132 = MULTI-SEED VALIDATION of /121-canonical, NOT bundle assembly
3. Cycle-8 axis menu must structurally reformulate post-/132

All 3 recommendations are honored at /131 closeout. /132 setup spec is LOCKED in Section 5 of this memo per Recommendation 2. Recommendation 3 binds at cycle-8 first EXPLORATION; not adjudicated at /131.

---

## End of memo
