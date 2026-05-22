# iter-v3/131 — Cycle-7 slot 10 — CLOSURE-RECONCILIATION (NO backtest); /121 architecture cohort-AND-frequency-shaped TERMINAL formalized; /132 = MULTI-SEED VALIDATION of /121 baseline

**Date**: 2026-05-21
**Type**: CLOSURE-RECONCILIATION (cycle-7 slot 10 of 10; NO axis variation; NO backtest; structural memo + /132 CONFIRMATION setup spec)
**Verdict**: CYCLE-7 STRUCTURAL CLOSURE per QR adjudication adopting Critic FINAL Rec 1 at /130 (`d33cc2e`). 9/9 EXPLORATIONs NEGATIVE with last 4 catastrophic across 4 structurally distinct axis classes (RISK-PRIMITIVE binary, UNIVERSE, RISK-PRIMITIVE continuous, BAR-INTERVAL). Cohort-AND-frequency-shape TERMINAL finding formalized; /121 architecture confirmed hyperparameter-region-locked at single-seed EXPLORATION budget.
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

QR adjudication at /131 between Option A (one final wild EXPLORATION under lifted constraints) and Option B (formal cycle-7 closure-reconciliation memo + /132 CONFIRMATION setup spec).

**Decision: Option B.** Reasoning enumerated in `briefs-v3/iteration_v3-131/closure_reconciliation.md` Section 1.2-1.3. All 6 candidate Option A axes (NEW labeling, different Optuna strategy, mixed-frequency 8h+24h, per-symbol feature selection, trade-payload features, feature-conditional confidence calibration) fall in the expanded scope of the QUADRUPLE-validated Optuna-trajectory-shift channel per `feedback_v3_optuna_trajectory_shift_finding.md` /128 EXTENSION explicit enumeration. The cycle-7 empirical evidence (9/9 NEGATIVE; last 4 catastrophic across 4 axis classes) establishes that at single-seed EXPLORATION budget, ANY in-scope axis lands in the /116 basin or worse. Empirical PROMISING-class prior at /131 under any Option A axis ≤ 10%.

The QR creativity mandate (`feedback_v3_qr_axis_creativity_mandate.md`) addresses lazy axis selection after 1-2 NEGATIVEs — its scope does NOT extend to structural exhaustion at 9/9 NEGATIVE consecutive across 4 axis classes. The strict 10:1 cadence rule (`feedback_v3_strict_10_to_1_cadence.md`) does NOT require slot #10 to be EXPLORATION on new axis — closure-reconciliation pre-CONFIRMATION is valid per Critic FINAL Rec 1 explicit text.

Files produced at /131:
- `briefs-v3/iteration_v3-131/closure_reconciliation.md` — formal cycle-7 closure-reconciliation memo (9 sections; documents the cohort-AND-frequency-shape TERMINAL finding + Optuna-trajectory-shift channel QUADRUPLE-VALIDATION + simulator BAR-INTERVAL LIMITATION + /132 CONFIRMATION setup spec)
- `diary-v3/iteration_v3-131.md` — this minimal closeout
- `briefs-v3/exploration_catalog.md` — catalog row append for /131 (closure-reconciliation; no IS/OOS columns)

Files NOT produced (per closure-reconciliation type):
- NO `analysis/iteration_v3-131/` EDA directory
- NO Engineer setup commit (no code changes; ZERO files in `src/`)
- NO Phase 5.5 gate document, Phase 6 engineering report, Phase 7.5 Critic review
- NO `reports-v3/iteration_v3-131/` directory
- NO BASELINE_V3.md update (UNCHANGED at /121 canonical)

## 2. /132 CONFIRMATION setup spec (LOCKED at /131 closeout per Critic FINAL Rec 2)

Per `closure_reconciliation.md` Section 5:

| Parameter | Value |
|---|---|
| TYPE | CONFIRMATION (cycle-7 slot 11; baseline re-validation; structural analog of /018 BOOTSTRAP-CONFIRMATION) |
| ITERATION_LABEL | "v3-132" |
| CLI | `uv run python run_baseline_v3.py --confirmation --n-trials 35 --clean-oof --seeds 2` |
| ENSEMBLE_SIZE | 10 (5 inner × 2 outer per CONFIRMATION default) |
| n_trials | 35 |
| Universe | BCH/LDO/TRX (UNCHANGED) |
| V3_FEATURE_COLUMNS_TOP_N | 14 (UNCHANGED) |
| Labels | triple_barrier K=21 ATR (2.0, 1.0) label_timeout_minutes=10080 |
| Bar-interval | 8h (REVERT from /130's 4h) |
| `enable_no_confirm_exit` | True (trigger_atr=0.50, k_candles=4) |
| `enable_per_symbol_drawdown_brake` | False (axis CLOSED at /127) |
| `enable_per_symbol_drawdown_scaling` | False (axis CLOSED at /129) |
| REQUIRED_GAP | 66 = (21+1)×3 |
| Wall-clock cap | 6h |

**Acceptance gates** (must hold ALL): multi-seed mean IS ≥ +1.0 AND multi-seed mean OOS ≥ +0.8 AND both Pareto seeds positive on IS AND OOS AND PSR > 0.95 AND frac_positive_paths ≥ 0.55.

**PASS outcome**: BASELINE_V3.md UNCHANGED at /121 canonical; /132 confirms /121 reproducibility under current code state; CONFIRMATION-VALIDATION-PASS diary; cycle-7 closes at /121.

**FAIL outcome**: CONFIRMATION-RE-ANCHOR diary (analog of /018 BOOTSTRAP-CONFIRMATION); investigate code-state drift across /122-/131; downgrade BASELINE_V3.md if multi-seed mean falls materially below /121 ADJUSTED reference (IS ≈ +1.06 / OOS ≈ +0.85).

**Pre-launch checks** (12 items in `closure_reconciliation.md` Section 5.4): Engineer must verify before launching the /132 backtest.

## 3. Cohort-AND-frequency-shape TERMINAL finding (formalized)

Cycle-7's structural EXPLORATIONs progressed across 4 distinct axis-class dimensions in /127-/130:

| Dimension | Perturbation iter | IS Δ vs /121 | Mechanism evidence |
|---|---|---:|---|
| RISK-PRIMITIVE binary | /127 | −0.5242 | IS Jaccard 0.4286; weight → 0 at 1.7% of trades; Optuna re-converges to /116 basin |
| UNIVERSE (3-sym & 6-sym) | /125 + /128 | −1.25 / −1.48 vs ADJ | 3-axis distribution mismatch per `feedback_v3_architecture_cohort_shaped.md` |
| RISK-PRIMITIVE continuous | /129 | −0.6425 | IS Jaccard 0.4213; /116-basin convergence; continuous semantics do NOT mitigate channel |
| BAR-INTERVAL (frequency) | /130 | **−2.6136** | WORST IS in v3; 8.4σ below T3b 4h-proxy simulator predicted mean; 4h-density Optuna search regions structurally different |

/121's IS Sharpe +1.31 is a hyperparameter-region-locked solution at the specific joint (3-symbol cohort, 8h bar interval, 14-feature stack, no_confirm primitive, ATR (2.0, 1.0), K=21). The IS-leg lift can only be FOUND with the multi-seed CONFIRMATION budget (1750 trials/WF month). At single-seed EXPLORATION budget (105 trials/WF month), ANY structural perturbation destabilizes the Optuna trajectory enough to fall out of the /121 basin.

The /129 finding established this empirically: /129 IS roster is bit-identical to /116 (Jaccard 1.0000; 161 of 161 trades match). The continuous-scaling primitive's 27 weight modifications change weight_factors but do not change which trades emit; Optuna under the continuous-scaling constraint at single-seed budget re-converges to /116's hyperparameter region, NOT /121's.

This is the cycle-7 TERMINAL finding, structurally analogous to cycle-5's terminal (/105-/109 representational-capacity FALSIFICATION). Documented in NEW memory `feedback_v3_cycle7_terminal_finding.md` (created at /130 closeout) + `feedback_v3_optuna_trajectory_shift_finding.md` /130 EXTENSION (channel QUADRUPLE-VALIDATED + simulator BAR-INTERVAL LIMITATION).

## 4. Optuna-trajectory-shift channel QUADRUPLE-VALIDATED + simulator BAR-INTERVAL LIMITATION

Channel completeness at /130: 4 of 4 cycle-7 structural axis classes confirm the channel signature. Simulator methodology operationally validated for within-bar-interval axes (/129 first implementation z=-0.298 within first sigma); simulator BAR-INTERVAL LIMITATION confirmed at /130 (z=-8.4 FAR outside ±3σ; bootstrap proxy on prior-bar-interval trade roster systematically under-estimates production response magnitude at frequency density changes).

Documented in `feedback_v3_optuna_trajectory_shift_finding.md` /130 EXTENSION (appended at /130 closeout).

## 5. Cycle-8 design considerations (NOT binding at /131)

Per Critic FINAL Rec 3 at /130 + `closure_reconciliation.md` Section 8:

Cycle-8 first EXPLORATION brief MUST include Section 0.6 "Architecture-Family Justification" arguing why the proposed axis is NOT in any of the 3 closed channels (cohort, frequency, Optuna-trajectory-shift).

Viable cycle-8 axis families:
1. WHOLLY-NEW model architecture at CONFIRMATION budget (cycle-5 NEURAL FALSIFICATION at single-seed; cycle-8 may retest with different priors at higher budget)
2. WHOLLY-NEW labeling architecture at CONFIRMATION budget (quantile-multi-class, cross-sectional ranking, fixed-horizon return at CONFIRMATION budget)
3. CONFIRMATION-budget-first design (process innovation: design axes evaluated ONLY at CONFIRMATION budget, skipping single-seed EXPLORATION; requires user approval at cycle-8 setup since it breaks 10:1 cadence implicit single-seed-EXPLORATION assumption)
4. Explicit acknowledgment /121 is practical edge ceiling and pivot to operational deployment focus

What cycle-8 SHOULD NOT propose at first EXPLORATION: single-axis EXPLORATIONs in /121 parameter neighborhood at single-seed budget; bar-interval changes at single-seed without redesigned simulator on native-frequency features; any axis lacking Section 0.6 channel-orthogonality argument.

## 6. Lessons

1. **Cycle-7 TERMINAL formalized**: /121 architecture cohort-AND-frequency-shaped; hyperparameter-region-locked at single-seed EXPLORATION budget across 4 axis-class perturbation dimensions. Memory file `feedback_v3_cycle7_terminal_finding.md` documents the architecture-fragility constraint.

2. **Closure-reconciliation pre-CONFIRMATION is a valid slot-10 type** per Critic FINAL Rec 1 + cadence rule permissive scope. The 10:1 cadence rule does NOT prohibit non-EXPLORATION slot-10 types; the rule prohibits collapsing EXPLORATION and CONFIRMATION into one iteration. /131's closure-reconciliation memo + /132's separate CONFIRMATION honors the rule.

3. **QR adjudication discipline**: Option A vs Option B was decided on empirical evidence (9/9 NEGATIVE consecutive, channel scope enumeration, PROMISING-class prior ≤ 10%), NOT on "the user mandated wildness" feeling. The QR creativity mandate's scope is bounded (1-2 NEGATIVE laziness mode); the structural exhaustion mode requires a different process answer.

4. **/132 CONFIRMATION setup spec is LOCKED at /131 closeout**, not at /132 brief commit. The setup spec is determined by the cycle-7 catalog state (8/8 NEGATIVE through /129 + /130 = 9/9 NEGATIVE; 0 PROMISING components to bundle) — /132 must be baseline re-validation, not bundle assembly. Locking the spec at /131 closes the loop on slot-10 → slot-11 handoff without ambiguity.

## 7. Decision

**CYCLE-7 STRUCTURAL CLOSURE.** Cycle-7 EXPLORATION phase complete (9/9 NEGATIVE consecutive; 0 PROMISING components). /131 = formal closure-reconciliation memo (NO backtest); /132 = MULTI-SEED VALIDATION of /121 baseline (LOCKED setup spec; structural analog of /018 BOOTSTRAP-CONFIRMATION). BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`). Tag `v0.v3-131` set on the /131 closeout commit.

Cycle-7 closes at /132's verdict. If /132 PASS: cycle-7 closes at /121 baseline; cycle-8 design begins with cohort-AND-frequency-shape constraint binding. If /132 FAIL: CONFIRMATION-RE-ANCHOR diary; downgrade BASELINE_V3.md if regression material; cycle-8 design requires resolving the regression first.

## 8. Handoff to /132

The /132 Engineer must:
1. Read `briefs-v3/iteration_v3-131/closure_reconciliation.md` Section 5 (LOCKED setup spec) + Section 5.4 (12 pre-launch checks)
2. Read this diary Section 2 (mirrored setup spec) for cross-verification
3. Apply the 12 pre-launch checks; abort + fix if any fail
4. Launch `uv run python run_baseline_v3.py --confirmation --n-trials 35 --clean-oof --seeds 2` with ITERATION_LABEL="v3-132"
5. Wall-clock cap 6h per `feedback_v3_cadence_discipline.md`

The /131 → /132 handoff sequence is bound; cycle-7 closes at /132's verdict.
