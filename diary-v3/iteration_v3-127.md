# iter-v3/127 — Cycle-7 slot 6 — EXPLORATION-NEGATIVE-catastrophic / per-symbol drawdown brake (T=7.0 / T_R=6.0 / N=45 / M=21) creative out-of-box; /116 override REJECTED; Optuna-trajectory-shift methodology finding

**Date**: 2026-05-21
**Type**: EXPLORATION (cycle-7 slot 6 of 10; RISK-PRIMITIVE axis class; closed-loop simulator + deadlock-impossibility proof methodology; creative out-of-box per `feedback_v3_oracle_eda_validity.md` STATEFUL gate companion)
**Axis**: Per-symbol drawdown brake at closed-loop simulator layer with time-based override deadlock-breaker (T=7.0 wpnl / T_R=6.0 wpnl / N=45 day rolling-window peak tracker / M=21 candles time-based brake-OFF)
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `8553a1c`
**Classification**: NEGATIVE-catastrophic — Section 8 first-match Criterion 1 (PUBLIC anchor): IS Sharpe +0.7866 < +0.91 threshold → FIRES with IS Δ −0.5242 (1.31× the magnitude of the catastrophic −0.40 threshold). /116-style PROMISING-MECHANICAL override REJECTED on three independent diagnostics.
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

Single-axis activation of the per-symbol drawdown brake RISK-PRIMITIVE (RiskV2Config primitive 11) with chosen parameters T=7.0 wpnl threshold / T_R=6.0 wpnl recovery / N=45 day rolling-window peak tracker / **M=21 candles time-based override** (mandatory deadlock-breaker preventing /054 BCH+LDO permanent-deadlock recurrence). The brake state machine: when a symbol's trailing 45-day-window weighted_pnl drawdown from rolling-window peak exceeds T=7.0 wpnl, brake-ON (suppress signals for that symbol). Brake-OFF triggers EITHER (a) state-based: dd_45d ≤ T_R=6.0 wpnl, OR (b) time-based: M=21 candles elapsed since brake-ON regardless of dd state.

All other architecture bit-identical to /121: 14-feature V3_FEATURE_COLUMNS_TOP_N (REVERTED from /126's 15 columns — `d24_ret_autocorr_lag1_50` dropped), +2/−1 ATR triple-barrier K=21, BCH/LDO/TRX universe (REVERTED from /125's ATOM/RUNE/UNI), 7-gate RiskV2 with /116 no_confirm primitive (trigger_atr=0.50, k_candles=4), REQUIRED_GAP=66, ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35.

Selection rationale (QR-led EDA at `analysis/iteration_v3-127/`, commit `8b66e12`): T1 parameter search scanned 420 configs jointly optimized on (a) positive ORACLE IS Δ wpnl; (b) ≥ 2 hysteresis cycles for at least 1 symbol; (c) brake activations ≥ 2; (d) M ≤ 63 (deadlock-breaker testable). T=7.0 / T_R=6.0 / N=45 / M=21 produced ORACLE IS Δ +5.41 wpnl (top-tier), TRX 2 IS hysteresis cycles, 4 IS activations + 3 OOS activations. T6 ORACLE Sharpe Δ +0.0348 (small positive lift on frozen /121 trade roster).

Commit chain: EDA `8b66e12` → brief `3c422a2` → Phase 5.5 gate PASS `8f06c3f` → setup `e65073c` (per-symbol drawdown brake + time-override implementation in `RiskV2Wrapper._update_drawdown_brake` and `get_signal`) → preflight fix `c8e7cd7` (feature count 15→14 + d24 ABSENT assertion) → engineering report `3ae8b36` → Critic FINAL `8553a1c`. Wall-clock ≈ 0.71h (within 2h EXPLORATION cap).

Files changed: `src/crypto_trade/strategies/ml/risk_v2.py` (new `enable_per_symbol_drawdown_brake` field + 4 brake parameters + state-machine implementation in `RiskV2Wrapper`); `run_baseline_v3.py` (ITERATION_LABEL "v3-127" + V3_MODELS REVERT to BCH/LDO/TRX + `_verify_feature_columns` 15→14 + d24 ABSENT assertion); `tests/strategies/ml/test_risk_v2.py` (closed-loop simulator unit tests + adversarial deadlock-construction stress test confirming time-override BREAKS /054 permanent-deadlock pattern). ZERO new features added in /127.

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /127 (3-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **+0.7866** | **−0.5242** |
| OOS monthly Sharpe | +0.9682 | **+0.9935** | **+0.0253** |
| IS daily Sharpe | 3.1180 | 1.9565 | −1.16 |
| OOS daily Sharpe | 2.3979 | 2.3453 | −0.05 |
| IS MaxDD | 26.38% | 38.69% | +12.31pp |
| OOS MaxDD | 25.70% | 24.54% | −1.16pp |
| OOS/IS Sharpe ratio | 0.7386 | 1.2630 | +0.524 (HEALTHY; above 0.50 floor) |
| Profit Factor IS | 1.6019 | 1.3551 | −0.25 |
| Profit Factor OOS | 1.3869 | 1.3432 | −0.04 |
| IS trades | 173 | 147 | **−26 (−15.0%)** — OUTSIDE pre-registered [−5%, +5%] band by 9× |
| OOS trades | 98 | 103 | +5 (+5.1%) — at upper boundary |
| PSR | 1.0 | 1.0 | 0.000 (PASS) |
| PBO mean | 0.1278 | 0.1278 | 0.000 (PASS) |
| frac_positive_paths | 0.6444 | 0.6444 | 0.000 (PASS at 0.55 floor) |
| DSR | 0.0 | 0.0 (EXPLORATION informational) | — |

Per-symbol IS attribution (from `in_sample/per_symbol.csv`):
- BCHUSDT: 69 IS trades, 43.5% WR, net PnL +72.37 wpnl (positive; concentration +140.2%)
- LDOUSDT: 10 IS trades, 30.0% WR, net PnL +0.22 wpnl (~flat)
- TRXUSDT: 68 IS trades, **27.9% WR**, net PnL **−20.97** wpnl (drag carrier; concentration −40.6%) — IS WR collapse from /121's 34.2%

Per-symbol OOS attribution (from `out_of_sample/per_symbol.csv`):
- TRXUSDT: 57 OOS trades, **54.4% WR**, net PnL **+48.14** wpnl (carrier; concentration +103.5%) — WR surge from /121's 41.2% (+13.2pp)
- BCHUSDT: 36 OOS trades, 38.9% WR, net PnL +16.19 wpnl (concentration +35.9%) — wpnl collapse from /121's +35.83 (Δ −24.57)
- LDOUSDT: 10 OOS trades, 30.0% WR, net PnL −15.81 wpnl (concentration −39.3%) — wpnl deterioration from /121's −2.89 (Δ −9.46)

**Total OOS wpnl Δ vs /121**: −24.57 (BCH) + −9.46 (LDO) + +27.29 (TRX) = **−6.74 total wpnl** despite the +0.025 Sharpe Δ. The OOS Sharpe Δ is preserved entirely by TRX OOS WR surge (54.4% vs 41.2%), NOT by broad-based lift — a structural concentration FLIP (/121 BCH-dominated 93.92% → /127 TRX-dominated 103.5%).

**Trade-roster Jaccard vs /121** (engineering report cascade test):
- IS Jaccard = 0.4286 (96 shared / 224 union; 77 trades dropped from /121, 51 new trades entered /127)
- OOS Jaccard = 0.5581 (72 shared / 129 union; 26 trades dropped from /121, 31 new trades entered /127)

**The Jaccard 0.43 IS roster is the load-bearing finding**: /116 PROMISING-MECHANICAL precedent had bit-identical trade entry rosters (BCH 95% / LDO 85% / TRX 88% open-time match — drag-removal accounting cleanup). /127's IS Jaccard 0.43 = wholesale Optuna re-convergence under the brake-constrained training objective, NOT drag-removal. Search-space restructuring, not accounting cleanup.

CPCV: 45 paths; path_sharpe_q25 = −0.243, q50 = +0.335, q75 = +0.838; frac_positive_paths 0.6444 PASS at 0.55 gate. Distribution stdev 0.811 (wide; 16 negative paths cluster near −1.3 corresponding to brake firing on profitable BCH positions). PBO 0.1278 PASS. PSR 1.0 PASS. DSR 0.0 informational at EXPLORATION per `feedback_v3_dsr_mode_artifact.md`.

## 3. The /116-style PROMISING-MECHANICAL override — REJECTED on three independent diagnostics

The engineering report flagged a potential /116-style PROMISING-MECHANICAL classification given the +0.025 OOS Sharpe lift (FIRST cycle-7 result where OOS Sharpe meets or exceeds /121's OOS anchor). The Critic adjudicated the override REJECTED on THREE independent diagnostics. This is load-bearing for the catalog classification rationale.

### Diagnostic 1 — Bit-identity FAILS

/116 had BCH 95% / LDO 85% / TRX 88% per-symbol open-time match with the non-no_confirm baseline (drag-removal accounting cleanup — same entries, different exit timing/weighting). /127 has IS Jaccard 0.43 (96/224 shared) and OOS Jaccard 0.56 (72/129 shared). 77 IS trades dropped + 51 IS new trades = fundamentally different model. The brake constrained Optuna's IS training objective; Optuna re-converged to a different hyperparameter region, producing a genuinely different strategy under the brake constraint. This is structural search-space restructuring, NOT route-change.

### Diagnostic 2 — Broad-based OOS lift FAILS

/116 produced broad-based OOS lift: all 3 symbols positive vs /060. /127 produces concentration FLIP not broad-based:
- BCH OOS wpnl Δ **−24.57**
- LDO OOS wpnl Δ **−9.46**
- TRX OOS wpnl Δ **+27.29**
- Net OOS wpnl Δ **−6.74** (LOWER than /121 in absolute wpnl terms)

The +0.025 OOS Sharpe Δ is single-symbol-carrier accident driven by TRX's OOS WR jumping 41.2% → 54.4%. Critically, **EDA T4 closed-loop simulator shows TRX had 0 brake activations OOS**. The brake mechanism cannot mechanistically explain the TRX OOS surge. The surge is Optuna trajectory drift on the brake-unaffected symbol — the frozen-baseline pattern per `feedback_v3_single_seed_frozen_baseline.md` where deterministic per-symbol Optuna trajectories produce IDENTICAL OOS results regardless of axis changes affecting OTHER symbols, EXCEPT here the brake DID change TRX's Optuna trajectory indirectly via the joint training objective.

### Diagnostic 3 — Behavioral-effect predictor MISSED by 9×

Brief Section 4.4 pre-registered the IS trade-roster change band [−5%, +5%] with falsifier. EDA ORACLE simulator predicted exactly 3 IS trades skipped (−1.73% — within band). Production observed **−15.0%** IS trade-count change (−26 net IS trades from 173 → 147). This is **9× the predicted magnitude** and OUTSIDE the band.

The behavioral-effect predictor failed because the ORACLE simulator computed counterfactual on the FROZEN /121 trade roster (apply brake AS FILTER to existing 173 trades, skip 3 brake-fired entries). Production saw the brake CONSTRAINT during Optuna training and converged to a fundamentally different hyperparameter region that inherently generates fewer IS trades — NOT 3 specific skips from the /121 roster. The gap is the Optuna-trajectory-shift channel that the closed-loop simulator does NOT model.

The deadlock failure mode (the /054 risk) was AVERTED by the M=21 time-override (OOS trade count 103 ≫ deadlock floor 60). The Optuna-trajectory-shift failure mode was NOT averted — it dominates the production outcome.

## 4. Methodological finding — ORACLE-on-frozen-roster ≠ production-with-Optuna-re-convergence

The /054 + /127 progression demonstrates TWICE that the closed-loop simulator + ORACLE-estimate-on-frozen-trade-roster methodology does NOT predict production behavior when Optuna re-trains under the constrained training objective.

| Iter | Prediction (closed-loop ORACLE on frozen /N-1 trade roster) | Production observed | Failure mode |
|---|---|---|---|
| /054 | 7 brake fires total; predicted OOS lift +12.51 wpnl | 881 main-run brake fires; OOS trades=0; OOS Sharpe=0 | Deadlock (rolling-window peak tracker entered permanent stuck-state at IS/OOS boundary; brake-ON → no trades → no state update → frozen) |
| **/127** | **3 IS trades skipped (−1.73%); ORACLE Sharpe Δ +0.0348; deadlock impossible via M=21 time-override (formal proof)** | **−26 net IS trades (−15.0%); IS Sharpe Δ −0.524; OOS concentration flip; Net OOS wpnl Δ −6.74** | **Optuna-trajectory-shift (brake constraint visible during Optuna training → re-converges to different hyperparameter region with structurally different trade roster — Jaccard 0.43)** |

**The /127 finding generalizes the /054 finding**: at /054 the methodology gap was diagnosed as STATEFUL-vs-STATELESS gate validity (per `feedback_v3_oracle_eda_validity.md`). The fix was closed-loop simulator + deadlock-impossibility proof. /127 IMPLEMENTED the fix correctly: closed-loop simulator passed (4 IS activations / 3 OOS activations through ≥ 2 hysteresis cycles for TRX); deadlock-impossibility proof passed via M=21 time-override (formal Section 2 argument; adversarial integration test in Section 9 confirmed time-override breaks /054 permanent-deadlock pattern). Production deadlock AVERTED (OOS trades = 103 ≫ 60 floor).

But the methodology STILL failed at production with 15× magnitude on the IS leg with opposite sign. The /054 methodology gap is therefore not just about STATEFUL gate validity in the deadlock sense — it is about the broader fact that **ORACLE-on-frozen-roster cannot capture Optuna's response to the CONSTRAINT being visible during training**. The constraint changes the Optuna gradient (which trades are allowed to contribute to the IS Sharpe objective), and Optuna re-converges to a region of hyperparameter space the ORACLE simulator never saw.

**This is the canonical falsification pattern at meta-level**: ORACLE simulator (frozen-roster predicted +5.41 BCH IS wpnl + small +0.0348 IS Sharpe Δ); production result (IS Sharpe Δ −0.524 with TRX IS PnL −20.97 wpnl drag; opposite direction; 15× ORACLE magnitude). The CLOSED-LOOP simulator added at /054 fixed only the deadlock-class failure mode; the Optuna-trajectory-shift failure mode is structurally undetectable by any frozen-roster counterfactual methodology.

Documented at NEW memory rule `feedback_v3_optuna_trajectory_shift_finding.md` (this iteration's contribution). **Until /128+ briefs explicitly model the Optuna-trajectory-shift channel (e.g., closed-loop simulator that RE-RUNS Optuna under the constrained training objective across N=10+ training-window-starts), RISK-PRIMITIVE axes will continue the /054 + /127 base rate** — both NEGATIVE despite passing all pre-flight gates the methodology defines.

## 5. Critic verdict summary

OVERALL = **EXPLORATION-NEGATIVE-catastrophic**. Single round emit. Zero clarifications (artifacts adjudicate unambiguously). All 8 Critic checks PASS or N/A:

- **Check 1 (look-ahead)**: PASS. Zero new features. RiskV2Wrapper drawdown brake state machine reads only past closed trades + past timestamps. Time-override uses past brake_on_close_time. /058 walk-forward fix preserved.
- **Check 2 (embargo)**: PASS. REQUIRED_GAP=66 unchanged.
- **Check 3 (multiple-testing)**: PASS informational. PBO 0.1278 PASS (only EXPLORATION-mode hard gate). PSR 1.0 PASS. DSR 0.0 informational.
- **Check 4 (IC)**: PASS carry-forward. 14-feature stack /121-bit-identical.
- **Check 5 (ADF)**: PASS carry-forward.
- **Check 6 (Pareto)**: N/A (single-seed-lineage 3-seed EXPLORATION).
- **Check 7 (reproducibility)**: PASS with infrastructure note. Setup verified. **Note**: run.log missing from `reports-v3/iteration_v3-127/` (3rd recurrence after /124 + /125 — engineering anomaly carry-forward; flagged for QE attention at /128+ to ensure run.log written for all EXPLORATIONs). Brake fire counters not directly observable; Engineer inferred behavior from trade-roster Jaccard.
- **Check 8 (alignment)**: PASS. All 5 brief Section 3 changes verified at source. V3_MODELS REVERT (ATOM/RUNE/UNI → BCH/LDO/TRX) is baseline-restore. V3_FEATURE_COLUMNS_TOP_N REVERT (15 → 14) is baseline-restore. No scope creep.

**Critic load-bearing finding** (per review.md): "The /054 + /127 progression demonstrates that the closed-loop simulator + ORACLE-estimate-on-frozen-trade-roster methodology does NOT predict production behavior when Optuna re-trains under the brake constraint. The brake mechanism's effect on a frozen /121 trade roster (EDA T6 +0.0348 ORACLE IS Δ) is NOT what happens when Optuna retrains: production IS Δ −0.524 (15× magnitude with opposite sign)."

## 6. PATH classification

**NEGATIVE-catastrophic** per Section 8 first-match-wins. Criterion 1 (PUBLIC anchor): IS Sharpe < +0.91 OR OOS Sharpe < +0.67. Observed IS = +0.7866 < 0.91 → CRITERION 1 FIRES first. (IS Δ vs PUBLIC = −0.5242; 1.31× the magnitude of the −0.40 catastrophic threshold.)

Section 8 falsifier evaluation (first-match-wins, all thresholds pre-registered in brief):

| Criterion | Threshold | Observed | Fires? |
|---|---|---|---|
| **NEGATIVE-catastrophic** | IS < +0.91 OR OOS < +0.67 (PUBLIC anchor) | **IS = +0.7866 < 0.91** | **YES — FIRST MATCH** |
| NEGATIVE-deadlock-recurrence | fires>30 AND OOS trades<60 | OOS trades=103 | No |
| NEGATIVE-no-effect | IS delta in [−0.05,+0.05] | delta = −0.5242 | No |
| NEGATIVE-INERT | IS in [0.86, 1.11] (ADJUSTED) | IS = 0.7866 | No |
| NEGATIVE-clean | IS adj-delta in [0.05,0.10] | adj-delta = −0.273 | No |
| SUSPICIOUS-OOS-DOMINANT | OOS delta > +0.30 | delta = +0.025 | No |
| PROMISING-strong | IS ≥ 1.16 AND OOS ≥ 1.07 | IS = 0.7866 | No |
| PROMISING-PARTIAL-MECHANICAL | IS in [1.06,1.16] AND OOS in [1.02,1.17] | IS = 0.7866 | No |
| PROMISING-MECHANICAL (/116 override) | bit-identical roster + broad-based OOS lift + behavioral-effect predictor PASS | Jaccard 0.43 FAIL + concentration FLIP FAIL + 9× predictor MISS | OVERRIDE REJECTED |

Pre-registered modal expectation: PROMISING-class (45% prior) vs NEGATIVE-class (45% prior) vs SUSPICIOUS (10%). Observed: NEGATIVE-catastrophic at the IS-leg-catastrophic-only sub-category. The brief placed substantive weight on the closed-loop simulator + deadlock-impossibility proof methodology averting both the deadlock and the IS-drag failure modes. The deadlock was averted; the IS-drag was NOT. The Optuna-trajectory-shift failure mode was not represented in the brief's pre-registered modal expectations.

## 7. Hypothesis check and process notes

### 7.1 Hypothesis falsified

Brief Section 1 hypothesis: "Activating the per-symbol drawdown brake (RiskV2Config primitive 11) with chosen parameters (T=7.0 wpnl, T_R=6.0 wpnl, N=45 days, M=21 candles time-override) on the /121 BCH/LDO/TRX baseline lifts EXPLORATION-mode IS monthly Sharpe by Δ ∈ [−0.10, +0.20] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06) AND OOS monthly Sharpe by Δ ∈ [−0.15, +0.15] vs /121 OOS +0.9682 by skipping catastrophic loss-streak trades on a per-symbol basis while NOT entering permanent deadlock (the /054 failure mode)."

**FALSIFIED on the IS leg with large magnitude.** Observed IS = +0.7866; IS Δ vs PUBLIC = −0.5242 (below the [−0.10, +0.20] band by 0.42 below lower bound). Observed OOS = +0.9935; OOS Δ vs PUBLIC = +0.0253 (within the [−0.15, +0.15] band — the OOS leg matches prediction by accident via TRX concentration flip rather than the predicted "skip catastrophic loss-streak trades" mechanism).

The deadlock-impossibility sub-hypothesis ("structurally DEADLOCK-FREE per Section 2 proof") was CONFIRMED at production (OOS trades = 103 ≫ 60 floor). The dominant failure mode is NOT deadlock; it is Optuna-trajectory-shift under brake-constrained training objective.

### 7.2 Process notes

**Behavioral-effect predictor MISS by 9×** (the load-bearing process finding): brief Section 4.4 pre-registered IS trade-roster change band [−5%, +5%]; observed −15.0% (OUTSIDE band by 9× the upper boundary in opposite direction). The ORACLE simulator predicted 3 specific /121 IS trades skipped. Production saw a net IS reduction of 26 trades because Optuna re-converged to a different hyperparameter region under the brake constraint. The brief Section 4.4 falsifier ("behavioral-effect predictor miss > 3× → axis is closed as methodology defect") FIRES — the size-scaling axis class would be closed by the same gate per Critic recommendation for /128.

**run.log missing (3rd recurrence)**: /127 run.log was not written to `reports-v3/iteration_v3-127/`. Brake fire counters from `GateStats` not directly observable; behavior inferred from trade-roster comparison. /124 + /125 + /127 all missing run.log — recurring engineering anomaly. /126 had run.log; the issue is intermittent. Flagged for QE attention at /128 setup.

**comparison.csv per_symbol aggregation defect carry-forward from /126**: Critic Check 7 at /126 flagged that `comparison.csv` per_symbol numbers don't match granular `out_of_sample/per_symbol.csv`. /127 engineering report cites the same discrepancy: `comparison.csv` IS WR 29.93% / OOS WR 43.69% vs trade-level computation IS 35.37% / OOS 46.60% (matches `per_regime.csv`). The headline metrics (monthly_sharpe, max_drawdown) are intact. Pre-existing runner artifact; not blocking /127 closeout.

**Cycle-7 single-positive-OOS-signal**: /127 is the FIRST cycle-7 result where OOS Sharpe meets or exceeds /121's OOS anchor (+0.9935 vs +0.9682). Prior 5 cycle-7 EXPLORATIONs (/122 + /123 + /124 + /125 + /126) all NEGATIVE on OOS. The +0.025 OOS Δ is real arithmetic but NOT robust signal — it is single-symbol-carrier (TRX 54.4% WR vs 41.2% at /121) within 1-sigma noise for 3-seed EXPLORATION mode. Cannot be cited as edge significance evidence per `feedback_v3_dsr_mode_artifact.md`.

## 8. BASELINE_V3.md status

UNCHANGED — /121 stays canonical at `v0.v3-121` (IS +1.3108 / OOS +0.9682). Per `feedback_v3_strict_both_is_oos_baseline.md`, BASELINE_V3.md updates ONLY when CONFIRMATION beats prior baseline on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean). /127 is EXPLORATION-class (not CONFIRMATION); IS Δ −0.52 fails BOTH-must-improve gate; PROMISING-MECHANICAL override REJECTED on three diagnostics. No baseline update is logically eligible.

## 9. Next-iteration ideas — /128 axis selection state

Per /127 Critic FINAL recommendations and cycle-7 axis exhaustion (6/10 NEGATIVE-class):

**Cycle-7 catalog state at /127 closeout**:

| Axis | State | Closure date | Reason |
|---|---|---|---|
| 1 — Cross-asset OHLCV | CLOSED | /123 closeout | 6 consecutive failures (/082/085/086/119 C6/122/123) |
| 2 — Non-LightGBM model classes | LOCKED OUT (cycle-5) | /109 closeout | Saturated representational-capacity at 8h depth-3-5 |
| 3 — Longer-cadence labels (DURATION) | CLOSED BILATERALLY | /124 closeout | K=42 /068 + K=63 /124 both NEGATIVE-catastrophic |
| 4 — NEW symbol universe variants | CLOSED | /125 closeout | 8 attempts NEGATIVE-or-NEUTRAL (cohort-shaped architecture) |
| 5 — Multi-frequency feature stack | EDA METHODOLOGY FALSIFIED | /126 closeout | 3-occurrence (/122 + /123 + /126); NEW-feature axes FORBIDDEN until methodology replaced |
| **6 — Per-symbol drawdown brake binary kill** | **CLOSED at /127** | **/127 closeout** | **Optuna-trajectory-shift dominates over closed-loop simulator + deadlock-impossibility methodology; ORACLE-on-frozen-roster ≠ production-with-Optuna-re-convergence** |
| 7 — NEW engineered features (strict pairwise-IC gate < 0.40) | OPEN but blocked by axis-5 methodology block | (carry-forward) | Methodology block applies |
| 8 — RiskV2 untested gate threshold combos | OPEN — knob-tuning saturated (Critic Rec REJECTED for /128) | (carry-forward) | Per `feedback_v3_structural_over_knob_exploration.md` |

**Critic-recommended priority order for /128**:

1. **PRIMARY: Symmetric per-symbol POSITION-SIZE SCALING at drawdown** (continuous size-scaling, NOT binary brake). The /127 finding is that binary kill switches at the Optuna training-objective boundary cause re-convergence to suboptimal regions. Continuous size-scaling (weight 1.0 → 0.5 → 0.0 as dd_45d traverses [T_R, T, T_max]) preserves the Optuna gradient: trades aren't deleted from training; their contribution is dampened. The /127 closed-loop simulator infrastructure ports directly — only the kill-vs-scale logic in `RiskV2Wrapper.get_signal` changes. **Pre-register falsifier**: if behavioral-effect predictor misses by > 3×, the size-scaling axis is closed as a methodology defect (the same gate /127 brief Section 4.4 should have enforced as a binding gate rather than informational). **Brief Section 2 EDA MUST include closed-loop Optuna-trajectory-shift sensitivity test**: closed-loop simulator that RE-RUNS Optuna under the constrained training objective across N=10+ training-window-starts. ORACLE-on-frozen-roster predictions cannot be the load-bearing pre-flight gate at /128 per the /054 + /127 finding.

2. **SECONDARY: Cycle-7 close-early with /128 = CONFIRMATION re-validating /121** (requires user override of strict 10:1 cadence rule). The 6/10-NEGATIVE pattern and the /127 finding is methodologically more general than just the brake axis — it generalizes to ALL RISK-PRIMITIVE axes that change the Optuna training objective. Multi-seed CONFIRMATION at /128 spec confirms /121 as stable canonical and frees QR cycle-7 budget for methodology-overhaul retrospective. Analogous to /081 cycle-2 + /092 cycle-3 + /120/121 cycle-6 — multi-seed re-validation with NO new ingredient to bundle.

3. **TERTIARY (REJECT) — Out-of-box creative**: cycle-7 dispatch space dominated by axes whose EDA→production translation has been falsified 6 ways. A novel creative axis without solving the Optuna-trajectory-shift methodology gap is statistically indistinguishable from the prior NEGATIVE 6/10 base rate.

4. **TERTIARY (REJECT) — RiskV2 untested gate combinations**: RiskV2 knob space functionally exhausted; further single-gate axes are knob-tuning per `feedback_v3_structural_over_knob_exploration.md`.

**Cycle-7 cadence**: slot 6/10 EXPLORATION done. 4 EXPLORATIONs remain + /132 CONFIRMATION (per strict 10:1). If /128 + /129 + /130 + /131 also exhaust NEGATIVE under the Optuna-trajectory-shift methodology gap (or if the user accepts the early-close recommendation), /132 CONFIRMATION becomes baseline RE-VALIDATION of /121 with NO new ingredient to bundle.

---

**Catalog entry appended** to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/127 | 2026-05-21 | cycle-7 drawdown brake (T=7.0/T_R=6.0/N=45/M=21) creative out-of-box | -0.5242 | +0.0253 | EXPLORATION-NEGATIVE-catastrophic — /116 override REJECTED (Optuna-trajectory-shift dominates) | NO |
```

**Tag**: `v0.v3-127`. Does NOT supersede `v0.v3-121` as canonical.

**Memory updates**: APPEND cycle-7 slot 6 NEGATIVE-catastrophic outcome + drawdown brake CLOSED + Optuna-trajectory-shift methodology finding to `project_v3_cycle7_setup.md`; NEW feedback file `feedback_v3_optuna_trajectory_shift_finding.md` documenting the /054 + /127 progression that ORACLE-on-frozen-roster ≠ production-with-Optuna-re-convergence and the implication that constraint-based RISK primitives that change the Optuna training objective require closed-loop Optuna-re-training simulators as a load-bearing pre-flight gate, not ORACLE-on-frozen-roster counterfactuals.
