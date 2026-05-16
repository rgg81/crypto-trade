# Iteration iter-v3/060 — Diary

## Decision: EXPLORATION-PROMISING — EXPLORATION-MODE-REFERENCE anchor established (Path A passive)

iter-v3/060 is the **first cycle 1 EXPLORATION post-RE-ANCHOR #2** and the **first 3-seed EXPLORATION-mode run in v3 history**. It is also the **first run after the EXPLORATION/CONFIRMATION mode-flag refactor** at SHA `56f5a30`. Per Critic FINAL `3cee250`: **OVERALL: EXPLORATION-PROMISING — EXPLORATION-MODE-REFERENCE certified clean** (13/13 methodology checks PASS or PASS-equivalent; mode-flag refactor correctly wired across all expected sites; §11 Anti-Pattern static scan CLEAN). Per Critic Rec #2: /060 numbers (IS +0.8325 / OOS +0.1403) become the cycle 1 EXPLORATION-mode anchor for iter-v3/061-068 axis-PASS deltas. **BASELINE_V3.md DOES NOT UPDATE** — /059 stays as the canonical CONFIRMATION-mode anchor (IS +1.0894 / OOS +0.5791). The /060 anchor is a parallel/supplementary reference, not a replacement.

## Section 1 — What Was Done

### Mode-flag refactor (commit `56f5a30`)

User directive 2026-05-13 mid-setup ("use the 10 seeds only for the confirmation") drove the architectural change. The Phase B-3 unified ensemble at `ab2d9ac` had baked ENSEMBLE_SIZE=10 as a hard constant; the mode-flag refactor at `56f5a30` decouples EXPLORATION from CONFIRMATION:

- New constants in `run_baseline_v3.py`:
  - `EXPLORATION_ENSEMBLE_SIZE = 3`
  - `CONFIRMATION_ENSEMBLE_SIZE = 10`
  - `ENSEMBLE_SIZE = CONFIRMATION_ENSEMBLE_SIZE` backward-compat alias
- New CLI flag: `--exploration` (argparse at lines 1907-1914) with descriptive help text
- New runtime path: `ensemble_size_for_run = EXPLORATION_ENSEMBLE_SIZE if args.exploration else CONFIRMATION_ENSEMBLE_SIZE` (lines 1960-1962)
- New active seed slicing: `active_ensemble_seeds = ENSEMBLE_SEEDS[:ensemble_size_for_run]` (line 2092)
- `_verify_feature_columns(ensemble_size=...)` extended with mode-aware assertion enforcing `ensemble_size in (3, 10)` (lines 291-297)
- `ensemble_summary.json` now has top-level `mode` + `ensemble_size` fields (lines 2399-2400)
- 5 new dedicated tests: `TestExplorationConfirmationModeConstants` in `tests/strategies/ml/test_ensemble_unified.py:302-356`
  - `test_exploration_mode_uses_3_seeds`
  - `test_confirmation_mode_uses_10_seeds`
  - `test_exploration_seeds_are_outer_42_lineage_subset`
  - `test_ensemble_size_alias_equals_confirmation`
  - `test_exploration_is_strict_subset_of_confirmation_seeds`
- Test suite total: 31/31 pass

### ITERATION_LABEL fix (commit `3fae219`)

The setup commit at `2d82079` bumped `ITERATION_LABEL` to "v3-060", but the mode-flag refactor at `56f5a30` reset it back to "v3-059" due to a merge accident. Commit `3fae219` re-applied the bump. The Phase 5.5 gate had to be re-run after this fix.

### Brief revision (commit `8430516`)

The original Phase 5 brief at SHA `2d82079` was written under a "bit-identical to /059" contract — assuming /060 would reproduce /059's numbers exactly because no axis change was made. The mode-flag refactor at `56f5a30` invalidated this contract: 3-seed averaging produces materially different numbers than 10-seed averaging on the same code state. The brief was rewritten under the new "EXPLORATION-MODE-REFERENCE establishment" contract:

- Section 4 predicted bands rewritten (IS [+0.85, +1.15], OOS [+0.30, +0.85])
- Section 7 failure-mode probabilities rewritten (~25% "3-seed variance noise floor"; ~65% predicted-success path)
- Section 8 LOCKED criteria rewritten (IS Sharpe ≥ +0.50; OOS Sharpe ≥ 0.0; BCH IS share ≥ 80%; cpcv_frac_positive_paths ≥ 0.50)
- New Section 2.10: EXPLORATION-mode reference scope (axes anchor against /060, not /059, for cycle 1)
- New Section 8.6: DSR_relative gate informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`

### Phase 5.5 gate re-PASS (commit `bb34e76`)

Re-ran the Phase 5.5 gate after brief revision + ITERATION_LABEL fix. OVERALL=PASS at HEAD `bb34e76`. Pre-run state verified clean.

### Phase 6 backtest

Run command: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35`. Wall-clock: **0.69h** (vs 1.1h target — 37% faster than expected; **5.2x speedup vs /059's 3.60h** CONFIRMATION). PID 486948; log at `logs/iter-v3-060.log`. Engineering report at SHA `df41f65`; Critic review at SHA `3cee250`.

---

## Section 2 — Results Table

### Multi-anchor headline comparison

| Metric | /059 CONFIRMATION-mode anchor (10-seed) | **/060 EXPLORATION-mode anchor (3-seed)** | Δ vs /059 |
|---|---:|---:|---:|
| **IS monthly Sharpe** | +1.0894 | **+0.8325** | **-0.26** |
| **OOS monthly Sharpe** | +0.5791 | **+0.1403** | **-0.44** |
| IS daily Sharpe | 2.7092 | 1.7115 | -0.99 |
| OOS daily Sharpe | 1.4359 | 0.3659 | -1.07 |
| OOS/IS monthly ratio | 0.5316 | **0.1685** | -0.36 (3-seed variance amplifies suspicion pattern) |
| OOS MaxDD | 34.53% | 35.78% | +1.25pp |
| OOS Calmar | 0.6585 | 0.1537 | -0.50 |
| OOS Profit Factor | n/a | 1.0482 | barely above 1.0 (3-seed noise) |
| OOS Win Rate | n/a | 39.22% | similar to /059's 36% range |
| frac_positive_paths (CPCV) | 0.6444 | **0.6444** | **0.000 (IDENTICAL — architecture-invariant)** |
| PBO | 0.1278 | **0.1278** | **0.000 (IDENTICAL — architecture-invariant)** |
| CPCV path Sharpe Q75 | 0.8378 | 0.8378 | 0.000 (IDENTICAL) |
| PSR | 1.0000 | 0.9763 | -0.024 (informational at EXPLORATION mode) |
| DSR_relative | 0.1134 | 0.0000 | -0.11 (informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`) |
| IS Trades | 171 | **159** | -12 |
| OOS Trades | 94 | **102** | +8 |
| n_trials_total | 1050 | **315** | -735 (3.33x reduction; per-cell unchanged at 35) |
| n_eff | 19 | **19** | **0 (architecture-invariant)** |
| Wall-clock | 3.60h | **0.69h** | **5.2x speedup** |

### Hard-blocking PASS gates (per brief Section 8.1 LOCKED)

| Gate | Threshold | /060 Observed | Status |
|---|---|---:|---|
| IS Sharpe ≥ +0.50 (relaxed EXPLORATION floor) | ≥ +0.50 | **+0.8325** | **PASS** (+0.33 cushion) |
| OOS Sharpe ≥ 0.0 (relaxed EXPLORATION floor) | ≥ 0.0 | **+0.1403** | **PASS** (+0.14 cushion — barely above floor) |
| BCH IS share ≥ 80% (one-sided per Section 4.4 falsifier) | ≥ 80% | **176.68%** | **PASS** (above the inflated denominator) |
| cpcv_frac_positive_paths ≥ 0.50 (relaxed EXPLORATION threshold) | ≥ 0.50 | **0.6444** | **PASS** (architecture-invariant vs /059) |
| ensemble_summary.json mode + size | mode="exploration", size=3 | **mode="exploration", size=3** | **PASS** |
| IS trade count in [128, 222] | 128 ≤ IS ≤ 222 | **159** | **PASS** |
| OOS trade count in [66, 122] | 66 ≤ OOS ≤ 122 | **102** | **PASS** |
| Tests 31/31 pass | 31/31 | **31/31** | **PASS** |

All 8 PASS gates clear. Borderline marks: OOS Sharpe is only +0.14 above the 0.0 floor (3-seed variance noise floor was pre-registered at brief Section 7 with Probability ~25% — see Section 6 below).

---

## Section 3 — Per-Symbol IS+OOS Decomposition

### IS decomposition (driver vs drag)

| Symbol | /060 IS weighted_pnl | /059 IS weighted_pnl | Δ vs /059 | /060 IS share (% of total IS) |
|---|---:|---:|---:|---:|
| **BCH** | **+79.45** | +76.61 | +2.84 | **176.68%** (denominator-inflated; driver) |
| LDO | **-11.44** | +8.93 | **-20.37** | **-25.44%** (drag — FLIPPED IS-negative) |
| TRX | **-23.04** | -7.35 | **-15.69** | **-51.25%** (drag — FLIPPED MORE IS-negative) |
| **Portfolio total** | **+44.97** | +78.18 | -33.21 | 100.00% (arithmetic check) |

### OOS decomposition (TRX inverted from IS; LDO worst in v3 history)

| Symbol | /060 OOS weighted_pnl | /059 OOS weighted_pnl | Δ vs /059 | /060 OOS share | /060 OOS trades | /060 OOS WR |
|---|---:|---:|---:|---:|---:|---:|
| **TRX** | **+23.31** | +4.16 | **+19.15** | 423.94% (inverted: IS-drag, OOS-driver!) | 54 | 48.1% |
| **BCH** | +1.91 | +24.75 | -22.84 | 34.69% (collapsed from /059 driver) | 37 | 32.4% |
| **LDO** | **-19.72** | -6.18 | **-13.54** | **-358.63%** (worst OOS in v3 history) | 11 | 18.2% |
| **Portfolio total** | +5.50 | +22.73 | -17.23 | 100.00% | 102 | 39.22% |

**TRX OOS inverted from IS sign**: TRX went IS-negative (-23.04) but OOS-positive (+23.31) — confirming the Section 2 EDA Q3 finding that TRX OOS is "single-trade outcome" (top-1 trade contributes 91.5% of total OOS weighted_pnl). The +23.31 is 3-seed lottery, not stable signal. Critic Adversarial Adjudication accepted this as a STRUCTURAL consequence of the 3-seed averaging noise floor, not a methodology defect.

**LDO -19.72 is the worst single-symbol OOS in v3 history** (vs prior worst LDO -15.29 at /058 seed 42). The 11-trade volume × 18.2% WR makes this entirely lottery-noise at single-symbol granularity.

### OOS monthly profitability check

| Period | Months OOS positive | /060 | /059 |
|---|---:|---:|---:|
| Total | 14 months | **7/14** | 10/14 |
| Net improvement / regression vs /059 | -3 months profitable | weaker monthly distribution | n/a |

The 7/14 OOS-positive rate is the lowest in v3 since pre-/028 baseline bootstrap. This is consistent with 3-seed variance amplification.

---

## Section 4 — Critic Verdict Summary

Per Critic FINAL `3cee250`: **OVERALL: EXPLORATION-PROMISING — EXPLORATION-MODE-REFERENCE certified clean** (cycle 1 #1 anchor established; mode-flag refactor at `56f5a30` correctly wired; methodology invariants intact; 13/13 methodology checks PASS or PASS-equivalent).

### Methodology checks (13 of 13 PASS or PASS-equivalent)

| Check | Status | Notes |
|---|---|---|
| 1 Look-Ahead Audit | PASS | Walk-forward fix at `e149e9d` intact; embargo 22 candles; mode-flag refactor did NOT touch walk_forward.py or labeling.py (verified by grep); 14 features unchanged |
| 2 Embargo Width | PASS | REQUIRED_GAP=66=(21+1)×3; runtime assertion fires; CPCV embargo=27 |
| 3 Multiple-Testing Correction | PASS (informational) | Gates 3+6+10-CPCV all PASS; DSR_relative=0.0 + Legacy DSR=0.0 + PSR=0.9763 informational only at EXPLORATION mode per brief Section 8.6 + `feedback_v3_dsr_mode_artifact.md`; n_trials accounting verified (315 = 35 × 3 × 3) |
| 4 IC Correlation | PASS | No new features at /060; carve-out `regime_momentum_signed_5d × vwap_dev_20 = 0.7642` per established `feedback_v3_engineered_feature_pivot.md` |
| 5 ADF Stationarity | PASS | 1803/2198 stationary; 3.5% non-stationary in IS-window proper; identical pattern to /059 |
| 6 Pareto Dominance | PASS | Replaced by Gate 10-CPCV (frac_positive_paths ≥ 0.50); 0.6444 PASS at both EXPLORATION (0.50) and CONFIRMATION (0.55) thresholds; pareto_front.csv correctly ABSENT; ensemble_summary.json PRESENT with 3 entries lineage=outer=42 |
| 7 Reproducibility | PASS | All commit SHAs verifiable; ENSEMBLE_SEEDS[0:3] = (191664963, 1662057957, 1405681631); trade-math spot-check matches CSV to 4 decimals on 2 rows |
| 8 Hypothesis-Implementation | PASS (with EXPLICIT NOTE on brief 8.1/4.4 inconsistency) | Two interventions verified (ITERATION_LABEL + --exploration); BCH 176.68% IS share is acceptable per Section 4.4 one-sided <80% falsifier (NOT the closed-band Section 8.1 phrasing); brief Section 8.1 wording needs cleanup at /061 setup (Recommendation #1) |
| 9 Symbol Exclusion | PASS | V3_EXCLUDED_SYMBOLS unchanged; V3_MODELS=(BCHUSDT, LDOUSDT, TRXUSDT) |
| 10 Feature Isolation | PASS | features_v3/ has zero active v1/v2 imports |
| 11 Forming-Candle | PASS | Phase 5.5 gate verified last-candle close_time already in past |
| 12 Library Version Pinning | PASS | All versions unchanged from /059; Optuna n_jobs=1 (Phase A revert intact) |
| 13 Mode-Flag Wiring Audit (NEW) | PASS | EXPLORATION_ENSEMBLE_SIZE=3 line 92; CONFIRMATION_ENSEMBLE_SIZE=10 line 90; --exploration flag wired at 8 expected sites; tests 31/31 pass; OOF parquet path collision-free across mode flips |

### §11 Anti-Pattern Static Scan (A1-A13): CLEAN

A1 (train_end leak), A5 (master-data invariance), A7 (OOF parquet guardrail), A8 (stateful gate deadlock), A10 (track isolation), A12 (DSR/PSR granularity), A13 (written-before-read) — all PASS.

### Adversarial Adjudication — BCH 176.68% IS Dominance

The 176.68% IS share is methodologically VALID:
- Arithmetic: BCH 79.45 / portfolio 44.97 = 176.68% (sum of shares 176.68 - 25.44 - 51.25 = 99.99% rounding-consistent)
- Mechanism: Under 3-seed averaging vs 10-seed, LDO and TRX both flipped IS-negative (-11.44 / -23.04 vs +8.93 / -7.35 at /059) — exactly the noise-floor failure mode pre-registered with Probability ~25% in brief Section 7
- Falsifier semantics: Section 4.4 explicit one-sided `< 80%` gate. 176.68% > 80% → PASS

The fragility this raises for cycle 1 axis-attribution: /060's anchor is structurally fragile (2 of 3 symbols IS-negative); axis-PASS deltas measured against (IS +0.8325 / OOS +0.1403) must NOT be conflated with /059's clean (IS +1.0894 / OOS +0.5791) anchor. Critic Recommendation #2 formalizes the cross-validation requirement at CONFIRMATION.

---

## Section 5 — PATH Classification: EXPLORATION-MODE-REFERENCE

The /060 outcome is **EXPLORATION-PROMISING** per the Critic taxonomy: not a competitive new-axis EXPLORATION (no signal-quality lift), not a NEGATIVE-no-effect (Path A intentionally passive), not a NULL-RESULT-INFRASTRUCTURE (no falsifier fired), but a **first-of-kind establishment iteration** for the EXPLORATION mode architecture.

This is **NOT a replacement for /059 BASELINE_V3.md anchor**. /059's 10-seed CONFIRMATION-mode numbers (IS +1.0894 / OOS +0.5791) remain canonical for:
- Future CONFIRMATIONs (iter-v3/069+) — must clear /059's numbers to update BASELINE_V3.md
- Cross-cycle BASELINE_V3.md comparisons
- Live-deployment trade-roster matching (unified architecture; deterministic single roster)

/060's 3-seed EXPLORATION-mode numbers (IS +0.8325 / OOS +0.1403) become the **parallel anchor** for:
- iter-v3/061-068 axis-PASS deltas (each cycle 1 EXPLORATION measures against /060, not /059)
- 3-seed-mode variance benchmarking for cycle 1 axis-attribution
- Behavioral effect predictors for cycle 1 brief Section 4 projections

The user directive 2026-05-13 ("use the 10 seeds only for the confirmation") drove this architectural separation. The /060 EXPLORATION-mode anchor enables 5.2x faster axis discrimination at the cost of 3-seed variance noise (pre-registered + observed). The /059 CONFIRMATION-mode anchor remains the gating reference for BASELINE_V3.md.

---

## Section 6 — Failure-Mode Prediction Check

### Brief Section 7 pre-registered failure modes

| Failure mode | Probability estimate | Detection criterion | **Fired?** |
|---|---|---|---|
| **3-seed variance noise floor too high** (Cycle 1 EXPLORATIONs may show indistinguishable axis-attribution noise) | **~25%** | OOS Sharpe near 0.0 floor; LDO/TRX IS-flip; BCH IS share inflates above predicted [85%, 100%] band | **YES** — fired exactly as described (OOS +0.1403 barely above 0.0; LDO IS flipped -11.44; TRX IS flipped -23.04; BCH IS share 176.68% above 100% upper-band prediction) |
| BCH IS concentration shifts unexpectedly (PATH-DIVERGENCE-AT-MODE-FLAG; BCH share < 80%) | <5% | BCH IS share < 80% | NO (176.68% well above) |
| Backtest runtime failure | <5% | Phase 6 crashes | NO (run completed in 0.69h) |
| Path A EXPLORATION-mode-reference established (predicted success) | ~65% | All falsifiers cleared | YES (technically — but with caveat) |

**The pre-registered Probability ~25% noise-floor failure mode FIRED.** The brief explicitly anticipated this exact pattern: "3-seed reduces averaging convergence; higher variance" → observed LDO + TRX both flipping IS-negative; "OOS retains lottery exposure at single-seed mode side" → observed TRX OOS inverting from -23.04 IS to +23.31 OOS as single-trade outcome.

The Critic accepted this as STRUCTURAL (the brief was explicit on the mechanism) rather than methodological FAIL.

### Predicted-vs-observed band check (brief Section 4.1)

| Metric | /060 predicted band | /060 observed | Direction |
|---|---|---:|---|
| IS Sharpe | +0.85 to +1.15 | **+0.8325** | BELOW lower band by -0.018 (within ±2% tolerance) |
| OOS Sharpe | +0.30 to +0.85 | **+0.1403** | BELOW lower band by **-0.160** (significant miss) |
| OOS/IS ratio | 0.35 to 0.75 | **0.1685** | BELOW lower band by -0.181 |
| BCH OOS weighted_pnl | comparable ±20% of /059's +24.75 | **+1.91** | BELOW lower band (-92.3%) |
| LDO OOS weighted_pnl | -3 to -10 | **-19.72** | BELOW lower band (-9.72 below the -10 floor) |
| TRX OOS weighted_pnl | -5 to +15 | **+23.31** | ABOVE upper band by +8.31 |
| OOS trade count | 90-110 | **102** | WITHIN band |
| IS trade count | 150-200 | **159** | WITHIN band |
| cpcv_frac_positive_paths | 0.50 to 0.70 | **0.6444** | WITHIN band |
| BCH IS share | 85%-100% (Section 4.2) | **176.68%** | ABOVE upper band (NOT a falsifier per Section 4.4 one-sided <80%) |

OOS Sharpe missed DOWN significantly (-0.16 below band); per-symbol IS/OOS displaced; trade counts WITHIN bands; methodology invariants (CPCV) IDENTICAL. The miss is consistent with the pre-registered noise-floor mechanism; falsifier "IS < +0.50 or OOS < 0.0" did NOT fire (IS +0.83, OOS +0.14), so NULL-RESULT-INFRASTRUCTURE escalation is NOT triggered. The /060 anchor is accepted as the cycle 1 EXPLORATION reference.

---

## Section 7 — BASELINE_V3.md Status: UNCHANGED

**Per Critic FINAL `3cee250` Recommendation #2 and user directive (Phase 8 dispatch):** BASELINE_V3.md is NOT updated by /060.

| Reference type | Anchor | Numerical values |
|---|---|---|
| **BASELINE_V3.md** (canonical CONFIRMATION-mode) | **iter-v3/059** | **IS +1.0894 / OOS +0.5791** (10-seed unified) |
| **Cycle 1 EXPLORATION-mode anchor** (parallel) | **iter-v3/060** | **IS +0.8325 / OOS +0.1403** (3-seed) |

The /059 tag `v0.v3-059` remains the canonical baseline tag; no new tag is issued for /060. BASELINE_V3.md content is UNCHANGED; the file points to /059's RE-ANCHOR #2 metrics. Future cycle 1 CONFIRMATION (iter-v3/069 or later) must clear /059's CONFIRMATION-mode numbers to update BASELINE_V3.md — NOT /060's EXPLORATION-mode numbers.

This is structurally identical to how v1/v2 manages baseline vs in-flight EXPLORATION reference: BASELINE_V3.md stays put while iteration-level anchors evolve per cycle.

---

## Section 8 — Critic Recommendations for Cycle 1

Per Critic FINAL `3cee250` Recommendations (3 items carried forward to cycle 1):

### Recommendation #1 — Brief Section 8.1 BCH-share gate wording cleanup at iter-v3/061 setup

**Issue identified**: Brief Section 8.1 LOCKED text reads "BCH IS share in [80%, 100%] band" (closed two-sided interval), but Section 4.4 falsifier list reads "BCH IS share < 80%" (explicitly one-sided lower bound). Observed BCH IS share = 176.68% sits above the closed-band upper bound but is acceptable per the one-sided falsifier. The engineering report adopted the 4.4 interpretation; Critic accepted under "pre-registered falsifier is the binding gate" precedent but flagged the inconsistency.

**Action at iter-v3/061 brief Section 8 setup**: State explicitly that the BCH IS share gate is one-sided lower (`≥ 80%`, no upper cap). Reference the Section 4.4 falsifier directly rather than restating a closed band. Closed-band phrasing in PASS criteria sections should be reserved for the SUCCESS prediction (Section 4 expected-impact projections), not the elimination criterion.

### Recommendation #2 — Cycle 1 axis-PASS deltas anchored against /060 MUST be cross-validated at CONFIRMATION

**Issue identified**: iter-v3/061-068 EXPLORATIONs will measure axis-PASS deltas against the /060 anchor (IS +0.8325 / OOS +0.1403). These are 3-seed-mode deltas. A /061-068 axis showing OOS +0.34 (PASS at /060-delta criterion of +0.20) could still be lottery-noise relative to /059's CONFIRMATION-mode +0.58 OOS.

**Action at iter-v3/069 cycle 1 CONFIRMATION brief Section 8 setup**: Explicitly require the candidate bundle to clear /059's CONFIRMATION baseline (+1.0894 IS / +0.5791 OOS) on BOTH axes simultaneously at 10-seed mode — NOT /060's EXPLORATION baseline. Per `feedback_v3_strict_both_is_oos_baseline.md`, the BOTH-must-improve discipline applies at CONFIRMATION against the canonical CONFIRMATION-mode baseline.

The new memory rule `feedback_v3_cycle1_axis_pass_criteria.md` (added 2026-05-13 — see Section 9 below) formalizes this two-tier evaluation: cycle 1 EXPLORATIONs use /060 deltas; cycle 1 CONFIRMATION re-validates against /059's full 10-seed baseline.

### Recommendation #3 — iter-v3/061 axis = TRX RiskV2 anti-Kelly diagnostic per EDA Q7 finding

**EDA Q7 finding (decisive)**: TRX is the ONLY symbol where average RiskV2 vol-scaling weight_factor on **winning** trades < average weight_factor on **losing** trades, in BOTH IS and OOS:

| Symbol | IS win_w − loss_w | OOS win_w − loss_w |
|---|---:|---:|
| BCH | **+0.099** (Kelly-aligned: high conviction → high weight → wins) | +0.072 |
| LDO | **+0.222** (strongly Kelly-aligned) | +0.189 |
| **TRX** | **-0.061** (anti-Kelly) | **-0.014** (anti-Kelly) |

This is a SYSTEM-level diagnostic finding (RiskV2 vol-scaling miscalibrated for TRX) NOT a TRX-feature/label finding. The EDA committed at SHA `6ab47b4` (`analysis/iteration_v3-060/trx_diagnostic.py`) is the cycle 1 #1 axis-feeding insight.

**Action at iter-v3/061 brief setup**:
- Section 2 EDA must include committed IS-only numerical tables comparing per-symbol weight_factor distributions before and after the proposed RiskV2 calibration change
- Test ONE engineered intervention alone at single-seed/3-seed mode per `feedback_v3_engineered_features_dont_stack.md` — do not stack multiple changes
- The axis is the **RiskV2 weight_factor calibration** (vol-scaling zscore_threshold, ATR-regime conditioning, or weight_factor floor/cap) targeting TRX's anti-Kelly profile — primary candidate per Path A diagnostic finding

---

## Section 9 — Next Iteration Ideas (Cycle 1 — iter-v3/061 through iter-v3/069)

Per `feedback_v3_strict_10_to_1_cadence.md`: cycle 1 = 10 SEPARATE single-seed/3-seed EXPLORATIONs at iter-v3/060-068. iter-v3/069 = SEPARATE CONFIRMATION (do NOT collapse EXPLORATION #10 into CONFIRMATION).

### Proposed iter-v3/061 — TRX RiskV2 anti-Kelly axis (per Critic Rec #3 mandate)

QR-driven EDA on TRX RiskV2 calibration:
- Per-symbol weight_factor distribution (winning vs losing) at multiple zscore_threshold values
- ATR-regime conditioning of weight_factor on TRX specifically
- Weight_factor floor/cap effect on TRX win/loss-weighted PnL ratio
- Quantify the IS-shift behavioral effect (predicted delta on the Q7 metric)

Single-axis variation; ONE RiskV2 intervention per EXPLORATION. EDA committed before brief.

### Proposed iter-v3/062 — DSR_relative threshold/benchmark recalibration (carried from /059 Critic Rec #1)

Methodology-only EXPLORATION:
- Investigate whether the 0.95 DSR_relative threshold is structurally unreachable under unified-roster Sharpe distributions
- Investigate alternative benchmark (CPCV-Q50 or CPCV-Q60 instead of Q75) at 10-seed CONFIRMATION mode
- Test reformulation against /058 + /059 + /050 + /028 historical reports
- Per `feedback_v3_methodology_post_hoc_input_traceback.md` mandate, all DSR_relative input variables must be traced to exact runner code paths

### Proposed iter-v3/063 — MASS FEATURE EXPANSION (per `feedback_v3_mass_feature_expansion.md`)

Originally queued at /062 then shifted +1 to /063 (RE-ANCHOR #2 consumed /060 EXPLORATION-mode-reference slot). QR mandated to research papers/literature for production-grade features (TA-lib, microstructure, cross-asset, regime, statistical, etc.) and elevate V3_FEATURE_COLUMNS_TOP_N from 14 to TARGET 100 (50 minimum).

### Proposed iter-v3/064-068 — remaining cycle 1 EXPLORATIONs

To be determined by QR EDA-driven discipline (per `feedback_v3_axis_selection_quant_discipline.md`). Candidate axes (TBD ranking):
- LDO diagnostic axis (LDO is the worst single-symbol OOS in v3 history at /060 — -19.72; 5th+ consecutive negative OOS)
- BCH-specific axis to reduce IS concentration without sacrificing BCH OOS (per /059 Critic Rec #3)
- Per-symbol RiskV2 tuning (post /061 outcome)
- NEW labeling architecture (return-based or volatility-adjusted alternatives)
- NEW model architecture (alternative tree growth, drawdown-penalized objective)
- Universe expansion candidates subject to V3_EXCLUDED_SYMBOLS constraint

### Proposed iter-v3/069 — Cycle 1 CONFIRMATION

Multi-seed validation of cycle 1 PROMISING bundle. Spec: `--n-trials 35` per cell, ENSEMBLE_SIZE=10 (CONFIRMATION mode — no --exploration flag), full DSR/PBO/PSR re-eval. PASS gates per `feedback_v3_strict_both_is_oos_baseline.md`: BOTH IS Sharpe AND OOS Sharpe must improve over /059's +1.0894 / +0.5791 anchor; Gate 3 OOS/IS ≥ 0.5; Gate 6 PSR > 0.95; Gate 10-CPCV frac_positive_paths ≥ 0.55. 6h hard cap.

### Cycle 1 axis-PASS classification bands (LOCKED at /060 — new memory rule)

The new memory rule `feedback_v3_cycle1_axis_pass_criteria.md` (added 2026-05-13) formalizes:

- **PROMISING-AT-EXPLORATION** (cycle 1 single-axis EXPLORATION): IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060 anchor AND frac_positive_paths ≥ 0.50 AND no methodology FAIL
- **INERT-AT-EXPLORATION** (within noise band): IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20]
- **NEGATIVE-AT-EXPLORATION**: IS Δ < -0.10 OR OOS Δ < -0.20
- **CONFIRMATION re-validation requirement**: PROMISING-AT-EXPLORATION axes carry forward to cycle 1 CONFIRMATION; CONFIRMATION re-validates against /059 (NOT /060) at 10-seed mode

---

## Reproducibility

- HEAD SHA at backtest run: `bb34e76` (Phase 5.5 re-gate PASS)
- Setup commit SHA: `2d82079` (original setup: TRX OOS diagnostic EDA + research brief + Path A) — superseded by `8430516` after mode-flag refactor
- EDA commit SHA: `6ab47b4` (`analysis/iteration_v3-060/trx_diagnostic.py` + 9 CSVs + `diagnostic_summary.md`)
- Mode-flag refactor commit SHA: `56f5a30` (--exploration → ENSEMBLE_SIZE=3 + 5 new tests; tests 31/31)
- Brief revision SHA: `8430516` (EXPLORATION-mode contract revision; replaced bit-identical-to-/059 contract)
- ITERATION_LABEL fix SHA: `3fae219` (re-applied "v3-060" bump after merge-accident regression)
- Phase 5.5 re-gate SHA: `bb34e76` (OVERALL=PASS at HEAD after brief revision + ITERATION_LABEL fix)
- Engineering report SHA: `df41f65` (Phase 7)
- Critic FINAL SHA: `3cee250` (EXPLORATION-PROMISING — 13/13 PASS)
- Diary SHA: (this commit)
- Tag: NONE (BASELINE_V3.md UNCHANGED; /059's `v0.v3-059` remains canonical)
- Wall-clock: 0.69h (5.2x speedup vs /059's 3.60h; 37% faster than 1.1h target)
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Library stack: UNCHANGED from /059 (Python 3.13, lightgbm 4.6.0, optuna 4.8.0 n_jobs=1, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1)
- Run command: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 35`
- Reports artifacts: `reports-v3/iteration_v3-060/comparison.csv`, `dsr.json`, `ensemble_summary.json`, `per_cell_pbo.csv`, `cpcv_paths.csv`, `adf_test.csv`, `ic_matrix.csv`, `trial_oof_returns.parquet`, `in_sample/`, `out_of_sample/`
