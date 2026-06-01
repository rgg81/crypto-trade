# Phase 5.5 Gate — iter-v1/049

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION
CYCLE SLOT: cycle-6 EXPLORATION 4/10
WALL-CLOCK BUDGET: 2h HARD (backtest); 2.5h total

## Axis Family + Rotation Status
FAMILY: feature-family
ROTATION_STATUS: VALID with constraint
ROTATION RATIONALE: Last 5 entries in Section 0.6 table are /043=per-cohort×labeling,
  /045=bundle-substrate, /046=methodology, /047=feature-family, /048=feature-family.
  Only 2 of 5 prior entries are feature-family; rotation is not blocked. Constraint
  registered: if /049 NEG-anything, /050 MUST rotate axis family (three-consecutive
  feature-family NEG saturation rule fires on third NEG).

## HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK)
REASON: feature-ADDITION only (44 → 45 columns); Optuna training objective (Sharpe)
  unchanged; training window (24 months) unchanged; universe (5-cohort) unchanged;
  model architecture (4-model LightGBM ensemble A/C/D/E) unchanged.
MULTI-SEED MITIGATION: not opted in (EXPLORATION default; single-seed=42).

## LM Master Response Verification
- briefs-v1/iteration_v1-049/lgbm_advisor.md exists: PASS
- Brief Section 3 addresses each LM Master recommendation: PASS
  - Rec 1 (frozen Optuna search space + --features-base-hash audit): ADOPTED
  - Rec 1 secondary (NEG-INERT → 1-shot CONFIRMATION retry pre-register): ADOPTED
    with Section 7 + Section 8 disclosure
  - Rec 2 (window=30 hardcoded; forensic 14-bar + 60-bar IC rows): ADOPTED
  - Rec 3 (per-cohort importance prediction pre-registered): ADOPTED with Section 7.4
    + Section 9.2 mandate
  - Risk Flag 1 (HP defensive-widening risk): MITIGATED — Section 3.6 + Critic Check 17
  - Risk Flag 2 (F5' borderline IC single-seed under-reading): DISCLOSED in Section 7.1 + 8.1
  - Risk Flag 3 (v1/034 basis_zscore_30 LEARNED-NEG precedent): CITED in Section 7.1
  - Risk Flag 4 (v3/019 funding_rate_zscore_30 PROMISING-INERT precedent): CITED in Section 7.1
  - Risk Flag 5 (partial-depth S2 honesty mandate): ADOPTED — Section 2.2 + R9 in Section 6
  - Risk Flag 6 (4h→8h aggregation lookahead): MOOT — data is native 8h cadence; no aggregation
  - Risk Flag 7 (S3 backup axis F5' risk): MITIGATED — S1 expected given OI cache start 2020-09
  - Risk Flag 8 (three-consecutive-feature-family-axis risk): REGISTERED in Section 0.6

## Cadence Check
- Wall-clock budget declared: 2h HARD (backtest) / 2.5h total for EXPLORATION: PASS
- CONFIRMATION-specific checks: N/A (TYPE = EXPLORATION)

## Pre-Launch EDA Artifacts Verification
EDA script committed: analysis/iteration_v1-049/eda.py (commit c74867b)
EDA outputs committed: eda.csv (54 rows: 5 ADF + 44 IC_pearson + 5 dist_stats),
  eda_summary.md, feature_columns.json
F4 ADF: 5/5 PASS (all p < 1e-17 — z-score normalization ensures near-perfect stationarity)
F5 IC:  max |IC| = 0.2505 vs cal_hour_norm — IDEAL band (< 0.30 threshold); PASS
  Critical pair funding_rate_zscore_30: |IC| = 0.1955 (below LM Master 0.28 point estimate)
Gate verdict: F4 PASS + F5 PASS (IDEAL). PROMISING-CLEAN-eligible on F1 PASS.

NOTE: Brief Section 9.1 enumerates 8 separately-named artifact files
  (e.g., adf_stationarity_per_symbol.csv, ic_orthogonality_full_44.csv, f4_f5_gate_outcomes.md).
  The committed EDA consolidates all required data into eda.csv + eda_summary.md + feature_columns.json.
  Data content fully covers all 8 brief artifacts; filename consolidation is a minor variance
  that does not affect gate integrity. PASS (substance over filename).

## Per-Section Status

- Section 0 (Data Split): PASS
  OOS_CUTOFF_MS = 1742774400000 (2025-03-24) declared IMMUTABLE; training_months = 24 declared
  IMMUTABLE; IS window named (data start ... 2025-03-24); OOS window named (2025-03-24 ... data end);
  universe BTC/ETH/LINK/LTC/DOT confirmed unchanged.

- Section 0.5 (Iteration Type): PASS
  TYPE: EXPLORATION; cycle slot 4/10; n_trials=18; --seeds 1; ENSEMBLE_SIZE=3; 2h HARD cap declared.

- Section 0.6 (Architecture-Family Justification): PASS
  Axis family: feature-family. Prior 5 listed: per-cohort×labeling, bundle-substrate, methodology,
  feature-family, feature-family. Only 2/5 same family → ROTATION_STATUS: VALID with constraint.
  One-sentence rationale present (non-kline data class escalation from /047/048 ABORT lessons).

- Section 1 (Hypothesis): PASS
  Specific single-sentence: long_short_zscore_30 (named feature, named source primitive, named
  mechanism = positioning-sentiment regime shifts orthogonal to existing 44 features) expected to
  achieve top-15 importance AND IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767. Not vague.

- Section 2 (IS-Only Evidence): PASS — committed script: analysis/iteration_v1-049/eda.py
  IS-window assertion present in script (df["open_time"] < OOS_CUTOFF_MS; assert max < cutoff).
  ADF per-symbol: 5/5 PASS. IC full 44-feature sweep: committed in eda.csv. Distribution stats:
  committed. Feature_columns.json: 45-element list committed. All evidence IS-only.

- Section 2.5 (HIGH-RISK Axis Declaration): PASS
  NORMAL-RISK declared. Explicit reasoning: feature-ADDITION only; Optuna objective unchanged;
  HIGH-RISK criterion (training-objective-domain change) not triggered by column expansion.

- Section 3 (Proposed Changes): PASS
  Enumerated changes: new positioning module (longshort_v1.py per implementation; positioning_v1.py
  per brief spec — naming discrepancy is a Phase 6.0 Critic check item, not a Phase 5.5 blocker);
  V1_FEATURE_COLUMNS_PRUNED 44→45; features/__init__.py registry update; tests/test_iteration_v1_049.py.
  LM Master responses: all 3 Recs + 8 Risk Flags addressed (see LM Master Response Verification above).
  No labeling changes, no universe changes, no risk-gate changes, no model-arch changes documented.

- Section 4 (Expected OOS Impact + Falsifiers): PASS
  F1 dual-gate: top-15 importance AND IS Sharpe Δ ≥ +0.05. F2 band: [-0.05, +0.05] = NEG-INERT;
  ≤ -0.05 = NEG-CLEAN. F3: OOS forensic-only (not a verdict gate). F4: ADF p < 0.05 per symbol.
  F5': max |IC| < 0.30 PASS / [0.30, 0.60) DOCUMENT / ≥ 0.60 ABORT. Explicit falsifiers.
  LM Master conjunction prior 13-17% cited. Verdict routes pre-registered.

- Section 5 (Risk Mitigation): PASS
  R1 (consecutive-SL cool-down K=3 C=27): inherited unchanged.
  R2 (drawdown scaling, Model E only): inherited unchanged.
  R3 (OOD Mahalanobis, 16 features): inherited unchanged; NOT extended to new feature (second axis).
  F4/F5' pre-launch gates (TIGHTENED, third consecutive codification): documented.
  NEG-CLEAN routing (retire + candidate feedback rule): documented.
  Wall-clock kill switch (>2h → abort): documented.
  IS-calibrated thresholds (F1 top-15, F2 +0.05, F5' 0.30/0.60) with simulated effects.

- Section 6 (Risk Management Design): PASS
  9 risk primitives covered: R1 (6.1), R2 (6.1), R3 (6.1), F4-ADF (6.2), F5'-IC (6.2),
  NEG routing (6.3), wall-clock kill switch (6.4), IS-calibrated thresholds (6.5),
  concentration cap (6.6), Critic Check 17 frozen-search-space (6.7), data-source operational
  risk (6.8), partial-depth honesty (6.9). Fire-rate predictions implicit in F-gate bands.
  Regime coverage via Section 10.

- Section 7 (Failure-Mode Prediction): PASS
  1-paragraph plus table priors: NEG-INERT 35-40% (MODAL), with mechanism (funding/OI/cross-BTC
  combinatorially span positioning signal at v1 EXPLORATION budget). Most plausible sub-scenario
  named (rank 17-28 + IS Δ [0.00, +0.04] = passenger usage). Per-cohort importance prediction
  (Section 7.4, LM Rec 3). Forward-looking, pre-registered before backtest.

- Section 8 (MERGE/NO-MERGE Criteria): PASS
  Pre-registered verdict subtypes with locked numerical thresholds:
  PROMISING-CLEAN: F1 PASS (top-15) AND IS Δ ≥ +0.05 AND max |IC| < 0.30.
  NEG-INERT: IS Δ ∈ (-0.05, +0.05) AND rank > 18 AND Δ < +0.03.
  NEG-INERT (partial-pass): IS Δ ∈ (-0.05, +0.05) AND (rank ≤ 18 OR Δ ∈ [+0.03, +0.05]).
  NEG-CLEAN: IS Δ ≤ -0.05.
  NEG-CLEAN-PRE-EDA: max |IC| ≥ 0.60.
  Comparison anchor: BASELINE_V1 ONLY (IS +0.4767, OOS +1.1913). No post-hoc rationalization.

- Section 9 (Library Stack): PASS
  pandas/numpy via pyproject.toml lockfile; statsmodels for ADF; LightGBM version inherited.
  No new dependencies. Test path declared (tests/test_iteration_v1_049.py, 7+ tests).
  8 pre-Phase-6 artifacts enumerated; EDA consolidation covers all required data.

## Minor Variances (Phase 6.0 Critic items — not Phase 5.5 blockers)
1. Module naming: brief Section 3.1 specifies `positioning_v1.py` + `add_positioning_v1_features`;
   implementation (commit 6b46f26) uses `longshort_v1.py` + `add_longshort_v1_features` +
   registry group `longshort_v1`. Functionality equivalent; naming discrepancy should be
   flagged by Phase 6.0 Critic in the pre-flight review (Critic Check 14 axis-family match).
2. EDA artifact filenames: brief lists 8 separately-named files; implementation consolidates
   into eda.csv + eda_summary.md + feature_columns.json. Data substance fully covered.
3. Brief Section 9.1 artifact #1 (long_short_zscore_30_definition.py) and #2
   (long_short_availability_per_symbol.csv) not present as standalone files; their content
   is embedded in eda.py + eda_summary.md. Phase 6.0 Critic may flag if the canonical
   per-symbol availability table is needed as a standalone artifact.

## Reasons (if BLOCK)
N/A — OVERALL: PASS

## Gate Metadata
- Gate author: QE (Phase 5.5)
- Gate date: 2026-06-01
- Branch: iteration-v1/049
- Brief commit: c74867b (latest; includes EDA artifacts)
- Feature module commit: 6b46f26
- lgbm_advisor.md commit: present in briefs-v1/iteration_v1-049/lgbm_advisor.md
- Next step: Phase 6.0 Critic pre-flight dispatch (v1-only mandatory)
