# Phase 5.5 Gate — iter-v1/010

OVERALL: PASS

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION
Mode: single-seed (seed=42), ENSEMBLE_SIZE=3, n_trials=35, ≤2h cap

## Axis Family + Rotation Status (Section 0.6)
FAMILY: risk-primitive
Prior 5 families: hyperparameter-region (005), universe (006), feature-family (007), methodology (008), feature-family (009)
ROTATION_STATUS: VALID — risk-primitive is UNUSED across all prior v1 EXPLORATIONs (first appearance of this family in v1 catalog); none of the prior 5 match risk-primitive.

## HIGH-RISK Declaration (Section 2.5)
HIGH-RISK: YES
Reason: R5 multiplies into weight_factor which scales weighted_pnl which enters Optuna's mean_oos_sharpe CV objective; changes the training-objective domain.
Mitigation: opt-in pre-commit to /011 multi-seed CONFIRMATION if /010 verdict = PROMISING (lighter footing than v3 mandatory).

## LM Master Response Verification
- briefs-v1/iteration_v1-010/lgbm_advisor.md exists: PASS
  Committed at SHA e03c138 (docs(iter-v1/010): LM Master Phase 4.5 pre-design advisory)
- Brief Section 3 addresses each LM Master recommendation: PASS
  - LM §1 (mechanism — basin-shift unlikely at single-seed n_trials=35): addressed in brief §3.2
    ("mechanism acknowledged; ADOPTED verbatim") and Section 5.3 counter-evidence #2
  - LM §2 (per-symbol heterogeneity — no per-symbol calibration at /010): addressed in brief §3.2
    ("No Phase 4.5 LM Master dispatch for /010"; QR pre-authored defer-to-/011) and §10.5
  - LM §3 (/011 staging — vol_target ∈ {3.5, 4.0, 4.25} 3-point grid if PROMISING):
    addressed in brief Section 11 (Alternate Designs table lists exactly 3.5/4.0/4.25)

## Cadence Check
- Wall-clock budget declared: ≤2h EXPLORATION cap: PASS
- Not a CONFIRMATION; 10-EXPLORATION prerequisite does not apply.
- Cycle-2 position: /010 = EXPLORATION #5 of 10 (cycle-2 catalog: /006/007/008/009 = 4 prior; /010 = 5th). On-track.

## Per-Section Status

- Section 0 (Data Split): PASS
  §0.1 anchors v0.v1-baseline-corrected with OOS_CUTOFF_DATE 2025-03-24 + training_months=24 (baseline config). IS/OOS windows named in §0.1 (anchor: IS=621 trades, OOS=189 trades matching 24-month IS + OOS window post-cutoff).

- Section 0.5 (Iteration Type): PASS
  Declares EXPLORATION mode with canonical knobs (--seeds 1, --n-trials 35, ENSEMBLE_SIZE=3, ≤2h cap).

- Section 0.6 (Architecture-Family Justification): PASS
  Declares risk-primitive, lists prior 5 families, rotation VALID. One-sentence rationale present (3-way convergence: LM Master /009 Phase 7.4 PRIMARY + Critic /009 Path Forward #1 + QR selection).

- Section 1 (Hypothesis): PASS
  Specific single-axis hypothesis with 3-part mechanism (vol-ceiling reducing position size at high-NATR entries), predicted effect (variance reduction, modest mean-cap), and expected outcome class (PROMISING-INERT to marginal-NEGATIVE). Explicit falsifier statement present. Oracle prediction quantified (-0.020 OOS Δ at vol_target=4.0%).

- Section 2 (IS-Only Evidence): PASS — committed script: analysis/iteration_v1-010/r5_vol_target_calibration.py (SHA 5506507)
  Four evidence tables from committed CSVs:
    §2.1 per-symbol IS NATR_14 distributions (5 symbols × 8 percentiles; IS-only filter stated)
    §2.2 trade-level fire rate simulation at 7 vol_target values (oracle on IS+OOS splits)
    §2.3 oracle Sharpe-delta simulation (7 vol_target values; F1/F3 pass/fail)
    §2.4 per-symbol PnL impact at vol_target=4.0% (6 symbols × IS+OOS oracle)
  Oracle methodology declared STATELESS-gate-valid per /054 precedent.

- Section 2.5 (HIGH-RISK Axis Declaration): PASS
  HIGH-RISK declared with explicit mechanism (Optuna objective domain changed via weight_factor). Multi-seed opt-in mitigation pre-committed. 6th-consecutive HIGH-RISK context addressed (prior axis family differs from /010 family = single-axis HIGH-RISK justified).

- Section 3 (Proposed Changes): PASS
  §3.1 = 3-file src/ diff with line-level implementation skeleton (backtest_models.py fields, backtest.py NATR lookup + R5 block, run_baseline_v1.py enable args).
  §3.2 = LM Master /009 Phase 7.4 PRIMARY recommendation: ADOPTED (R5 vol-target ceiling; vol_target_pct revised 2.5%→4.0% per EDA calibration; revision is sharpening of LM Master's intent, not rejection).
  §3.3 = Critic /009 Path Forward: PRIMARY (R5) ADOPTED; SECONDARY (methodology debt) REJECTED with reason (N_eff PCA refactor CLOSED at /008, no outstanding debt).
  §3.4 = hyperparameter/search-space unchanged.

- Section 4 (Expected OOS Impact / Falsifiers): PASS
  F1 (OOS Sharpe Δ): explicit numerical condition (< -0.05 = NEGATIVE; < -0.20 = catastrophic).
  F2 (behavioral fire-rate band): [10%, 60%] OOS, with oracle prediction 15.3%.
  F3 (IS Sharpe Δ): < -0.10 = NEGATIVE-catastrophic.
  F4 (DEGENERATE_PREDICTOR): 0 fires expected with explicit oracle justification.
  F5 (DSR computability): n_eff_per_cell_median ≥ 4 check.
  All falsifiers have pre-registered oracle predictions and verdict labels.

- Section 5 (Risk Mitigation): PASS
  §5 = P10/P25/P50/P75/P90 OOS Δ band with confidence labels.
  §6 = R1/R2/R3 interaction analysis (§6.1-§6.6), IS-calibrated threshold (vol_target=4.0% from Phase 1 EDA), kill-switch criteria (§6.6), simulated historical effect (§6.5).

- Section 6 (Risk Management Design): PASS
  All active risk layers (R1, R2, R3, R5) addressed with interaction analysis. R5 is the new primitive; §6.1 covers R2×R5 double-attenuation (worst-case ~10% position), §6.2 covers R1×R5 orthogonality, §6.3 covers R3×R5 orthogonality. IS-calibrated threshold present. Kill-switch criteria present (§6.6).

- Section 7 (Failure-Mode Prediction): PASS
  5 failure modes with detection conditions and verdict classifications:
    FM1 = R5 too tight (>80% fire rate)
    FM2 = R5 too loose (<5% fire rate)
    FM3 = R5×R2 double-attenuation on Model E
    FM4 = Optuna re-optimization into new IS-overfit basin
    FM5 = LINK edge-source erosion (LINK has highest NATR; cut disproportionately)

- Section 8 (MERGE/NO-MERGE Criteria): PASS
  Pre-registered verdict gates with explicit numerical thresholds:
    PROMISING: OOS Δ ≥ +0.05, IS Δ ≥ -0.05, fire rate ∈ [10%,60%], 0 F4 fires, F5 computable, ≥10/month OOS trades
    PROMISING-INERT: OOS Δ ∈ [-0.05, +0.05], IS Δ ∈ [-0.10, +0.05]
    NEGATIVE: any single failure below PROMISING-INERT band
    NEGATIVE-NEGATIVE: both F1 < -0.05 AND F3 < -0.10
    NEGATIVE-mis-calibrated: F2 OOS fire rate < 5% OR > 80%
  PROMISING tripwire commitment to /011 multi-seed CONFIRMATION pre-committed.

- Section 9 (Library Stack): PASS
  All relevant libraries listed (lightgbm, optuna, pandas, pyarrow, numpy, scikit-learn, statsmodels, scipy, pandas-ta). No new dependencies introduced. NATR_14 loaded from existing feature parquets.

## Reasons (if BLOCK)
N/A — OVERALL is PASS.

## Gate Summary
All 13 mandatory sections PASS. LM Master advisory exists and all 3 LM recommendations addressed in brief. Axis Rotation VALID (risk-primitive first usage in v1 catalog). Cadence: EXPLORATION #5 of 10 in cycle-2. HIGH-RISK declared with appropriate single-seed mitigation. Analysis script committed at SHA 5506507 with 4 evidence CSVs. Implementation spec is unambiguous (3-file diff with line-level skeletons).

Phase 6 setup may proceed.
