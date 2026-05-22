# Phase 7.5 Critic Review — iter-v3/127

OVERALL: EXPLORATION-NEGATIVE — NEGATIVE-catastrophic on F1 (IS Δ −0.5242 vs /121 PUBLIC, IS=+0.7866 < +0.91 threshold); PROMISING-MECHANICAL override REJECTED on three independent diagnostics vs /116 precedent (IS Jaccard 0.43 ≠ /116's ~0.90 bit-identity; OOS lift is concentration-flip not broad-based; behavioral-effect predictor missed by 9×). The drawdown-brake axis class CLOSES at /127 — empirical Optuna-trajectory-shift dominance over the ORACLE-estimated +0.0348 IS lift.

## Iteration Type
TYPE: EXPLORATION (cycle-7 slot #6 of 10; RISK-PRIMITIVE axis class; closed-loop simulator + deadlock-impossibility proof methodology)

## QR Response Considered (Round 2 only)
Single-round emit. Zero clarifications — artifacts adjudicate unambiguously.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
/127 adds zero new features. RiskV2Wrapper drawdown brake state machine reads only past closed trades + past timestamps. Time-override check uses past brake_on_close_time. /058 walk-forward fix preserved.

### Check 2 — Embargo Width: PASS
REQUIRED_GAP=66 unchanged.

### Check 3 — Multiple-Testing Correction: PASS (informational for EXPLORATION)
PBO=0.1278 PASS (only EXPLORATION-mode hard gate). PSR=1.0 PASS. DSR=0.0 informational.

### Check 4 — IC Correlation: PASS (carry-forward)
14-feature stack /121-bit-identical.

### Check 5 — ADF Stationarity: PASS (carry-forward)

### Check 6 — Pareto Dominance: N/A (single-seed EXPLORATION)

### Check 7 — Reproducibility: PASS (with infrastructure note)
Setup verified. **Note**: run.log missing from `reports-v3/iteration_v3-127/`. Brake fire counters not directly observable; Engineer inferred behavior from trade-roster Jaccard. Not classification-compromising but QE should ensure run.log captured for /128+.

### Check 8 — Hypothesis-Implementation Alignment: PASS
All 5 brief Section 3 changes verified at source. No scope creep.

## Verdict Mechanism

**Mechanical first-match-wins**: NEGATIVE-catastrophic (Criterion 1 fires; IS Δ −0.5242 is 1.31× the −0.40 threshold magnitude).

**/116 PROMISING-MECHANICAL override REJECTED** on three independent diagnostics:

1. **Bit-identity FAIL**: /116 had BCH 95% / LDO 85% / TRX 88% open-time match (drag-removal). /127 has IS Jaccard 0.43, OOS Jaccard 0.56 (Optuna re-convergence under brake-constrained objective).

2. **Broad-based OOS lift FAIL**: /116 all 3 symbols positive vs /060. /127 concentration FLIP:
   - BCH OOS wpnl Δ **−24.57**
   - LDO OOS wpnl Δ **−9.46**
   - TRX OOS wpnl Δ **+27.29**
   - Net OOS wpnl Δ **−6.74** (LOWER than /121)
   
   The +0.025 OOS Sharpe Δ is single-symbol-carrier accident driven by TRX's OOS WR jumping 41.2% → 54.4% — and EDA T4 shows TRX had **0 brake activations OOS**. Brake mechanism cannot mechanistically explain the TRX surge; the surge is Optuna trajectory drift on the brake-unaffected symbol (frozen-baseline pattern per `feedback_v3_single_seed_frozen_baseline.md`).

3. **Behavioral-effect predictor MISS (9×)**: Brief Section 4.4 pre-registered IS trade-roster change band [−5%, +5%] with falsifier. EDA ORACLE predicted 3 IS trades skipped (−1.73%). Production observed **−15.0%** IS trade-count change. This is 9× the predicted magnitude. **The /054 → /127 progression demonstrates TWICE that ORACLE-on-frozen-roster ≠ production-with-Optuna-re-convergence.** Carver canonical brake calibrated on a trade roster does not transfer through Optuna training. Deadlock failure mode AVERTED by time-override; Optuna-trajectory-shift failure mode NOT averted, and is the dominant production effect.

## Methodological Finding (cross-iteration)

The /054 + /127 progression demonstrates that the closed-loop simulator + ORACLE-estimate-on-frozen-trade-roster methodology does NOT predict production behavior when Optuna re-trains under the brake constraint. The brake mechanism's effect on a frozen /121 trade roster (EDA T6 +0.0348 ORACLE IS Δ) is NOT what happens when Optuna retrains: production IS Δ −0.524 (15× magnitude with opposite sign).

**Until /128+ briefs explicitly model the Optuna-trajectory-shift channel** (e.g., closed-loop simulator that RE-RUNS Optuna under the constrained training objective across N=10+ training-window-starts), RISK-PRIMITIVE axes will continue the /054 + /127 base rate.

## Recommendations to QR for /128 Axis Selection

Cycle-7 status: 6/10 NEGATIVE-class. Axis exhaustion: NEW feature axes (EDA methodology FALSIFIED at 3-occurrence /122/123/126), universe substitution (CLOSED at /125 + 9-attempt cumulative streak), labeling DURATION (CLOSED bilaterally /068+/124), cross-asset OHLCV (CLOSED), non-LightGBM model (LOCKED OUT), drawdown brake binary kill (CLOSED at /127).

Critic-recommended priority order for /128:

1. **PRIMARY: Symmetric per-symbol POSITION-SIZE SCALING at drawdown** (orchestrator option a), NOT binary brake. The /127 finding is that binary kill switches at the Optuna training-objective boundary cause re-convergence to suboptimal regions. Continuous size-scaling (weight 1.0 → 0.5 → 0.0 as dd_45d traverses [T_R, T, T_max]) preserves the Optuna gradient: trades aren't deleted from training; their contribution is dampened. /127 closed-loop simulator infrastructure ports directly — only the kill-vs-scale logic in `RiskV2Wrapper.get_signal` changes. Pre-register falsifier: if behavioral-effect predictor misses by > 3×, the size-scaling axis is closed as a methodology defect (the same gate /127 brief Section 4.4 should have enforced).

2. **SECONDARY: Cycle-7 close-early with /128 = CONFIRMATION re-validating /121** (orchestrator option d). Per `feedback_v3_strict_10_to_1_cadence.md`, 10:1 is canonical — but this is the 6/10-NEGATIVE pattern and the /127 finding is methodologically more general than just the brake axis. Multi-seed CONFIRMATION at /128 spec confirms /121 as stable canonical and frees QR cycle-7 budget for methodology-overhaul retrospective. Requires user override of cadence rule.

3. **TERTIARY (REJECT) — Out-of-box creative** (option c): cycle-7 dispatch space dominated by axes whose EDA→production translation has been falsified 6 ways. A novel creative axis without solving EDA-methodology gap is statistically indistinguishable from the prior NEGATIVE 6/10 base rate.

4. **TERTIARY (REJECT) — RiskV2 untested gate combinations** (option b): RiskV2 knob space functionally exhausted; further single-gate axes are knob-tuning per `feedback_v3_structural_over_knob_exploration.md`.

**Process-level recommendation for /128 brief** (if PRIMARY accepted): the brief's pre-flight EDA MUST include a closed-loop Optuna-trajectory-shift sensitivity test. The /127 closed-loop simulator tested only the brake state machine on a FROZEN /121 trade roster; it did not simulate Optuna re-training under the constrained objective. The /054 → /127 progression has demonstrated TWICE that the methodology gap is precisely this: ORACLE-on-frozen-roster does not predict production-with-Optuna-re-convergence. Until /128+ briefs explicitly model the Optuna-trajectory-shift channel, RISK-PRIMITIVE axes will continue the /054 + /127 base rate.

## Clarifications Requested from QR — NONE
