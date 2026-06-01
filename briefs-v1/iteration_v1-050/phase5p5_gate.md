# Phase 5.5 Gate — iter-v1/050 (retry)

OVERALL: BLOCK

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION

## Axis Family + Rotation Status
FAMILY: feature-family + risk-primitive (compound; single DOT-specialist mechanism)
ROTATION_STATUS: VALID — last 5 families (from catalog): /046 methodology, /047 feature-family,
/048 feature-family, /049 feature-family, /050 feature-family+risk-primitive. Not all 5 same
family (methodology at /046 breaks monoculture). Rotation discipline honored.

## HIGH-RISK Declaration
HIGH-RISK: NO — additive feature NORMAL-RISK (45→46 cols; no Optuna-objective-domain change) +
post-prediction stateless regime gate NORMAL-RISK (operates after Optuna training).
No multi-seed mitigation required at EXPLORATION budget; Rec 3 pre-registers multi-seed
validation at /051 or /054 conditional on PROMISING verdict.

## LM Master Response Verification
- briefs-v1/iteration_v1-050/lgbm_advisor.md exists: PASS — file present at commit 8054700
  (authored 2026-06-01; Phase 4.5 section present with 3 numbered recommendations).
- Brief Section 3.5 addresses each LM Master recommendation: PASS
  - Rec 1 (regime gate is load-bearing; attribution analysis required): ADOPTED — dispatch
    runner logs regime_gate_fire_rate_is + regime_gate_fire_rate_oos per-regime in
    comparison.csv; post-mortem disambiguation protocol specified.
  - Rec 2 (trade-rate floor risk at ≥30% fire rate): ADOPTED — F-AXIS #4 pre-registered
    IS ≥ 50 / OOS ≥ 10 floor; downgrade clause bound in Section 8.2.
  - Rec 3 (single-seed lottery risk; multi-seed pre-registration): ADOPTED CONDITIONAL —
    PROMISING verdict triggers /051 or /054 multi-seed re-validation at seeds [123, 456,
    789]; binding pre-registration in Section 3.5 and confirmed in Section 8.

## Cadence Check
- Wall-clock budget declared: ≤ 2h for EXPLORATION: PASS
- EXPLORATION 5/10 of cycle-6: PASS (cadence within 10-iter cycle)
- CONFIRMATION checks: N/A (TYPE=EXPLORATION)

## Per-Section Status
- Section 0 (Data Split): PASS — OOS_CUTOFF_MS=1742774400000 (2025-03-24 UTC), training_months=24
  both IMMUTABLE; IS window (data start → 2025-03-24) and OOS window (2025-03-24 → data end)
  named; DOTUSDT-only traded cohort + BTC klines for feature computation declared.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, cycle-6 slot 5/10 with prior 4 slots
  enumerated (/046-/049).
- Section 0.6 (Architecture-Family Justification): PASS — table of last 5 EXPLORATION families
  present; axis family declared as feature-family+risk-primitive (compound DOT-specialist);
  ROTATION_STATUS=VALID with explicit reasoning.
- Section 1 (Hypothesis): PASS — specific ONE-sentence hypothesis: "Adding
  dot_vs_btc_ret_ratio_30 + vol-spike regime gate will flip DOT IS Sharpe from −1.23 to ≥ 0."
  Mechanism described (idiosyncratic alpha periods vs BTC-contagion vol-spike periods). Specific
  enough: names the feature, names the gate, names the expected direction and magnitude.
- Section 2 (IS-Only Numerical Evidence): **BLOCK** — EDA artifact missing.
  The v1 skill (quant-iteration-v1.md §"EDA Discipline (revised 2026-06-01)") states explicitly:
  "EDA scripts and outputs are still REQUIRED for Phase 5.5 PASS. Phase 5.5 BLOCKS on: (a) EDA
  script does not exist on disk, (b) eda.csv is missing." The directory
  `analysis/iteration_v1-050/` was created but is EMPTY — no `eda.py` (or equivalent), no
  `eda.csv`. Note: the brief's Section 2 content (DOT baseline stats from BASELINE_V1.md,
  feature design rationale, predicted IC) is informational and passes the VALUES test. The
  artifact existence requirement is separate and categorical. Previous gate (commit 65f75b1)
  erred by granting PASS on Section 2 without checking for the artifact — that error is corrected
  here. Committed script path required: `analysis/iteration_v1-050/eda.py` (or named
  equivalently) + `analysis/iteration_v1-050/eda.csv`.
- Section 2.5 (HIGH-RISK Axis Declaration): PASS — NORMAL-RISK declared; explicit reasoning for
  both mechanisms (additive feature + post-prediction stateless gate); DOT-only cohort precedent
  at /029 cited.
- Section 3 (Proposed Changes): PASS — enumerated: (3.1) feature add dot_vs_btc_ret_ratio_30
  with module spec; (3.2) vol-spike regime gate implementation; (3.4) feature column count
  update 45→46 with assert. LM Master responses addressed in Section 3.5. All changes are
  enumerated.
- Section 4 (Expected OOS Impact): PASS — F-AXIS #1–#5 table with PROMISING/PARTIAL/NEG-CLEAN
  numerical thresholds; F-AXIS #5 (IC) explicitly marked informational only (never blocking,
  per EDA Discipline revision). Explicit falsifiers present.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 stack confirmed active for DOT; new regime gate
  (R-GATE /050) described as post-prediction stateless gate with IS-calibrated q75 threshold.
- Section 6 (Risk Management Design): PASS — 8-primitive table present; gate fire-rate
  prediction in [8%, 20%] IS; vol-spike gate classified under BTC-contagion primitive.
- Section 7 (Failure-Mode Prediction): PASS — 2-paragraph section present. Most plausible OOS
  failure identified (feature INERT-OOS-overfit; DOT/BTC ratio distribution shift between IS
  2021-2024 and OOS Q1 2025+ macro context). Modal failure scenario explicitly described
  (PROMISING-PARTIAL with gate fire rate mismatch IS→OOS). Load-bearing mechanism identified
  (regime gate vs feature). Forward-falsifier structure intact for Phase 8 diary verification.
- Section 8 (Pre-Registered MERGE/NO-MERGE Criteria): PASS — Sections 8.1–8.6 present.
  Primary numerical criterion: DOT IS Sharpe Δ thresholds with 4 verdict bands
  (PROMISING-SPECIALIST ≥+1.23, PROMISING-PARTIAL +0.50–+1.23, NEG-INERT −0.05–+0.50,
  NEG-CLEAN ≤−0.05). Trade-rate floor gating (8.2), gate fire-rate reporting (8.3), IS MaxDD
  regression check (8.4), OOS forensic-only declaration (8.5), per-regime Pareto secondary (8.6).
  All thresholds declared BEFORE backtest runs — pre-registration intact.
- Section 9 (Library Stack Declaration): PASS — Table present; all components are existing
  pins (lightgbm, scipy, pandas, numpy, stdlib); no new deps; no mlfinlab/mlfinpy/pypbo/fracdiff
  in scope; explicitly stated: "No NEW pip / uv adds."

## Reasons (BLOCK)
1. **Section 2 — EDA artifact MISSING**: `analysis/iteration_v1-050/` directory exists but
   is empty. Per quant-iteration-v1.md §"EDA Discipline (revised 2026-06-01)", Phase 5.5 BLOCKS
   when the EDA script does not exist on disk AND when `eda.csv` is missing. Both are absent.
   The VALUES in brief Section 2 are informational and acceptable; the ARTIFACT existence is a
   separate hard requirement. Required artifacts before re-submission:
   - `analysis/iteration_v1-050/eda.py` (or equivalent name) — committed, IS-data-only,
     grep-clean for OOS-side patterns.
   - `analysis/iteration_v1-050/eda.csv` — produced by the script, at minimum containing
     per-feature ADF p-values + pairwise IC + distribution stats for `dot_vs_btc_ret_ratio_30`
     vs V1_FEATURE_COLUMNS_PRUNED (IS window only).

## Path Forward for QR
1. Create `analysis/iteration_v1-050/eda.py`: load IS parquets for DOTUSDT
   (open_time < OOS_CUTOFF_MS), compute dot_vs_btc_ret_ratio_30 for IS window, compute
   pairwise IC vs top-10 V1_FEATURE_COLUMNS_PRUNED features, compute ADF p-value, compute
   distribution stats. Grep-clean: no `oos`, no `out_of_sample`, no date filter
   ≥ OOS_CUTOFF_DATE.
2. Produce and commit `analysis/iteration_v1-050/eda.csv`.
3. Optionally update brief Section 2 to reference actual computed values (IC, ADF p-value,
   distribution stats) instead of "predicted ~0.25–0.30" estimates — not required for gate
   PASS but improves Phase 8 diary traceability.
4. Re-submit; QE re-runs Phase 5.5 gate.

## Note on Previous Gate Error
The first gate attempt (commit 65f75b1) granted Section 2 a PASS with the comment "No
committed analysis script required under EDA-informational mandate." That was incorrect: the
EDA Discipline revision decouples VALUES (informational, no longer blocking on IC/ADF
magnitudes) from ARTIFACT EXISTENCE (still required, Phase 5.5 hard block). This retry
corrects that error. All other section verdicts from the previous gate are unchanged or
upgraded (lgbm_advisor.md + Sections 7/8/9 now all PASS).
