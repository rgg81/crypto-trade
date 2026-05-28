# Phase 5.5 Gate — iter-v1/029

OVERALL: BLOCK

## Iteration Type (from Brief header + Section 0.1)
TYPE: EXPLORATION — "Cycle-4 EXPLORATION 2/10" declared in brief header and Section 0.1. No formal `TYPE: EXPLORATION` label in a subsection numbered 0.5 (see per-section status below).

## (v1 only) Axis Family + Rotation Status
FAMILY: per-cohort-specialization-DOT-v2
ROTATION_STATUS: VALID

Verification: catalog rows for last 5 EXPLORATIONs (excluding /026 sanity slot and /027 CONFIRMATION-technical-failure per skill Rule 4):
- /022: per-cohort-specialization-LTC
- /023: feature-family (funding-rate)
- /024: model-arch (regime-conditional)
- /025: feature-family (OI delta)
- /028: per-cohort-specialization-LTC-v2

Three distinct families across 5 slots — NOT 5-of-5 monoculture. Rotation discipline honored. /029 `per-cohort-specialization-DOT-v2` is a NEW family (different cohort + different mechanism class from all prior per-cohort entries). VALID.

Note: /028 is not yet committed to `briefs-v1/exploration_catalog.md` (last catalog entry is /027; /028 row is absent). However, /028 existence is confirmed by commits `5e1a9ec`, `b1b27d7`, `7d06504`, `fef26dc`, `68811f7` and the `briefs-v1/iteration_v1-028/` directory. Catalog gap for /028 is a QR documentation debt item but does not affect the rotation discipline check (families of /022-/025 confirmed from catalog; /028 family `per-cohort-specialization-LTC-v2` confirmed from `briefs-v1/iteration_v1-028/research_brief.md` Section 0.6).

## (v1 only) HIGH-RISK Declaration
HIGH-RISK: NO (NORMAL-RISK)
Declaration at brief Section 2.5: "NORMAL-RISK. Path C (symmetric BTC-trend gate ±8%) is a post-Optuna stateless trade-stream filter applied via `risk_v2.apply_btc_trend_filter`. It does NOT change Optuna's training-objective domain." Rationale adequate.

## (v1 only) LM Master Response Verification
- briefs-v1/iteration_v1-029/lgbm_advisor.md exists: PASS (commit `c4a4d14`)
- Brief Section 3.4 addresses each LM Master recommendation: PASS

LM Master §1-§7 cross-check:
- §1 HYBRID classification: ADOPTED in brief Section 3.4 §1
- §2 Hyperparameter recommendations + §2.5 ESCALATE n_trials/ENSEMBLE_SIZE: ADOPTED (n_trials 18→35, ENSEMBLE_SIZE 3→10); sub-recommendations (num_leaves cap, min_data_in_leaf, learning_rate cap, lambda_l1, bagging_fraction) explicitly DEFERRED with rationale (single-axis isolation). PASS.
- §3 Feature rank predictions: ADOPTED INFORMATIONAL in Section 3.4 §3
- §4 Path C BINDING recommendation: ADOPTED with explicit rejection of Paths A/B/D/E in Section 3.4 §4
- §5 Falsifier pre-registration: ADOPTED VERBATIM in Section 3.4 §5 (all 5 F-AXIS items carried)
- §6 Track-record commentary: ACKNOWLEDGED in Section 3.4 §6
- §7 Routing recommendation for /030: ADOPTED PRE-COMMIT in Section 3.4 §7

All 7 LM Master sections explicitly addressed. PASS.

## Cadence Check (v1)
- Wall-clock budget declared: 35-55 min Optuna + wrap-up total (Section 3.6); INSIDE 2h EXPLORATION cap: PASS
- Cycle-4 EXPLORATION 2/10 declared: PASS
- CONFIRMATION precedent count: N/A (this is EXPLORATION)
- CONFIRMATION imports prior EXPLORATION variations: N/A

## Per-Section Status

- Section 0 (Data Split): PARTIAL-PASS
  Content present but distributed: `OOS_CUTOFF_DATE = 2025-03-24` (Section 7), `training_months = 24` (Section 7), embargo FIX confirmed (Section 3.2 + Section 7). IS window (2023-03-24 − 24 months = 2021-03-24 to 2023-03-24 area) and OOS window absolute dates are NOT explicitly named in the brief. The anchor baseline dates and sacred constants are verifiable from Section 7. Treating as PARTIAL-PASS consistent with prior v1 iteration briefs (/028, /027) which also embedded data-split details in reproducibility sections rather than a standalone Section 0 declaration. This non-blocking inconsistency with the skill template is an improvement item for QR at next brief authoring.

- Section 0.5 (Iteration Type Declaration, v1): PARTIAL-PASS
  Brief header states "Cycle: 4, EXPLORATION 2/10". Section 0.1 states "Cycle-4 EXPLORATION 2 of 10". However, no formal `TYPE: EXPLORATION` subsection labeled "0.5" exists — brief's subsection 0.5 is "LM Master tail re-weighting." Content unambiguously declares EXPLORATION. Treating as PARTIAL-PASS consistent with established v1 brief format (prior v1 briefs also embedded iteration type in headers rather than a named 0.5 subsection). Non-blocking.

- Section 0.6 (Architecture-Family Justification, v1-only): PASS
  Full axis family + prior 5 families table + rotation status VALID + rationale present at Section 0.6 and Section 3.8.

- Section 1 (Hypothesis): PASS
  H1 paragraph in Section 0: "DOT-only single-cohort training... paired with stateless direction-aware BTC-trend regime gate at ±8%... will lift DOT OOS per-trade Sharpe Δ into [+0.05, +0.55]... The mechanism mirrors ETH /019." Specific hypothesis with mechanism and expected metric. PASS.

- Section 2 (IS-Only Evidence): PASS — committed script: `analysis/iteration_v1-029/dot_cohort_classification.py` (commit `0d7a090`)
  Numerical tables from committed CSVs: dot_direction_split.csv (8 rows), dot_btc_trend_bucket.csv (16 cells), dot_monthly_pnl.csv (IS H1/H2 split), dot_exit_reasons.csv. Script committed at `0d7a090`. Note: brief cites commit SHA `bbab148` for these CSVs — this SHA does not exist in the repository (actual commit is `0d7a090`). Minor reference error in the brief; CSVs are confirmed committed and verifiable. Non-blocking.

- Section 2.5 (HIGH-RISK Axis Declaration, v1-only): PASS
  NORMAL-RISK declared with rationale. PASS.

- Section 2.6 (ORACLE EDA trade-attribution requirement): PASS
  Present at brief Section 2.6. Per-direction × per-BTC-trend × IS/OOS 16-cell table cited. PASS (v1-specific section, not in skill template but cross-checked for /029 requirements).

- Section 3 (Proposed Changes + LM Master responses): PASS
  Sections 3.1 (universe/features), 3.2 (labels), 3.3 (mechanism spec), 3.4 (LM Master responses §1-§7 all addressed), 3.5 (configuration), 3.6 (wall-clock), 3.7 (code changes), 3.8 (axis family for Critic Check 14). PASS.

- Section 4 (Expected OOS Impact): PASS
  Section 4 (Verdict Matrix) provides OOS Δ band [+0.05, +0.55] with modal +0.30 and explicit falsifier rows (F-AXIS #3 < 5% caps at INERT-NO-EFFECT; F-AXIS #3 > 35% caps at NEGATIVE; F-AXIS #5 < 2 caps at PROMISING-INERT). Section 8 pre-registers 8-row verdict table. PASS (content serves Section 4 + Section 8 of skill template).

- Section 5 (Risk Mitigation): PASS
  Section 5 covers R1 (ON, IS-calibrated), R2 (OFF, documented), R3 (ON), gate fire-rate monitoring, TP-exit floor monitoring, wall-clock kill-switch. IS-calibrated thresholds present. PASS.

- Section 6 (Risk Management Design): BLOCK
  Brief Section 6 is "Symbol Exclusion" (one line confirming `V1_EXCLUDED_SYMBOLS` unchanged). There is NO risk management design table. The skill requires a structured table of the risk-primitive stack (at minimum: R1 cooldown, R2 drawdown brake, R3 OOD Mahalanobis, BTC-trend gate) with IS fire-rate predictions, OOS fire-rate predictions, and regime coverage narrative. Section 5 contains R1/R2/R3 narrative (risk mitigation) but is not the structured risk management design table. Missing: IS vs OOS fire-rate comparison table, regime coverage per gate, "without gate" vs "with gate" PnL attribution. Prior v1 briefs (/028 Section 6 = Failure Modes) also omit the 8-primitive structured table — however the skill explicitly requires it and this gate must enforce it.

- Section 7 (Pre-Registered Failure-Mode Prediction, v1/v3 mandatory): BLOCK
  Brief Section 7 is "Reproducibility" (seed, ENSEMBLE_SIZE, n_trials, constants). There is NO pre-registered failure-mode prediction section. The skill requires 1-2 paragraphs predicting how this iteration most plausibly fails OOS, what the gates should catch, and what the failure looks like in metrics. This is forward-looking and verified against actual outcomes in Phase 8 diary. The content is completely absent. Note: Section 4 (Verdict Matrix) contains verdict-cap conditions (F-AXIS #3 and #5 capping rules) which cover SOME of this, and Section 3.4 §4 mentions "gate over-kills the H2-recovery edge" as a path risk — but these are mechanism descriptions, not a forward-looking failure mode narrative per the Section 7 requirement.

- Section 8 (Pre-Registered MERGE/NO-MERGE Numerical Criteria, v1/v3 mandatory): PASS
  Section 8 (Verdict Cell Determination Table) provides 8 pre-registered rows with specific F-AXIS conditions and verdict cells. Pre-registered before backtest runs. PASS.

- Section 9 (Library Stack Declaration, v1/v3 mandatory): BLOCK
  Brief Section 9 is "Test Suite Mandate" (regression + new tests). There is NO library stack declaration. The skill requires: which versions of mlfinlab/mlfinpy/pypbo/fracdiff are used; if a library is unavailable and a fallback is used, state which and why. Prior v1 briefs (/028 Section 9, /027 Section 9) contain the library stack. For /029 this section is entirely absent. Required content: mlfinlab==1.4 / mlfinpy fallback status, pypbo (invoked or N/A for EXPLORATION), fracdiff>=0.10 (invoked for ADF on new features, or N/A), statsmodels (adfuller usage).

## Reasons (BLOCK)

- Section 6 (Risk Management Design): MISSING. Brief Section 6 is "Symbol Exclusion" (one line). Required: structured risk-primitive stack table (R1/R2/R3 + BTC-trend gate) with IS fire-rate predictions, OOS fire-rate predictions, regime coverage, and "gate-off vs gate-on" PnL attribution. Section 5's R1/R2/R3 narrative is risk MITIGATION, not risk MANAGEMENT DESIGN per the skill's §3 template (fire-rate table + regime coverage). QR must add a Section 6 block with at minimum: (a) gate stack table listing each primitive, enabled/disabled, IS fire-rate prediction, OOS fire-rate prediction; (b) regime coverage narrative for the BTC-trend gate; (c) attribution estimate ("kills N OOS LONG weak-up-BTC trades at -8.47% = +X% PnL recovery estimate").

- Section 7 (Pre-Registered Failure-Mode Prediction): MISSING. Brief Section 7 is "Reproducibility." Required: 1-2 paragraphs predicting how iter-v1/029 most plausibly fails OOS, what specific metrics indicate failure, which gates would catch it, and what the failure looks like in comparison.csv. This is the forward-looking complement to Section 8's numerical criteria. Example failure modes to address: (1) BTC-trend gate kills the +5.59% OOS SHORT strong-up bucket (positive counter-trend SHORTS that gate eliminates) — net gate effect negative; (2) DOT cohort-isolation basin lottery lands in H1-catastrophic regime with no R2 defense (the R2=OFF exposure); (3) single-seed=42 lottery produces DOT-only retraining in the SHORT-dominant basin (mirrors ETH /019 IS SHORT basin surprise). QR must write this section and commit.

- Section 9 (Library Stack Declaration): MISSING. Brief Section 9 is "Test Suite Mandate." Required: declare mlfinlab/mlfinpy version + fallback status, pypbo invocation status (EXPLORATION = informational/N/A), fracdiff version + usage status (ADF on no new features = N/A), statsmodels version + usage. Prior v1 iterations (/028 Section 9, /027 Section 9) provide this; /029 omits it entirely. QR must add Section 9 Library Stack content.

## Path Forward

OVERALL=BLOCK. Do NOT proceed to Phase 6.0 (Critic pre-flight) or Phase 6 (backtest).

QR must address the 3 BLOCK gaps:
1. Add Section 6 (Risk Management Design): structured gate-stack table with IS/OOS fire-rate predictions, regime coverage, and gate attribution estimate.
2. Add Section 7 (Pre-Registered Failure-Mode Prediction): 1-2 paragraphs naming the 2-3 most plausible OOS failure modes and their metric signatures.
3. Add Section 9 (Library Stack Declaration): mlfinlab/pypbo/fracdiff/statsmodels version declarations with invocation status for this iteration.

After QR addresses all 3 gaps and re-commits the brief, re-submit for Phase 5.5 re-evaluation. The 3 BLOCK items are purely additive (no existing content needs to change; only missing sections need to be added). All other sections PASS.

Non-blocking notes for QR:
- Brief Section 0.3 cites commit SHA `bbab148` for analysis CSVs; actual commit is `0d7a090`. Correct the SHA reference.
- /028 row is absent from `briefs-v1/exploration_catalog.md` — QR documentation debt; not blocking /029 gate but should be addressed at /028 Phase 8 closeout.
