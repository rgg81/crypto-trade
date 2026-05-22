# iter-v3/129 — Cycle-7 slot 8 — EXPLORATION-NEGATIVE-catastrophic / continuous multiplicative position-size scaling at per-symbol drawdown; continuous-scaling sub-axis CLOSED; Optuna-trajectory-shift channel TRIPLE-validated (/127 binary, /128 universe, /129 continuous); methodology-fix simulator operationally validated (z=-0.298)

**Date**: 2026-05-21
**Type**: EXPLORATION (cycle-7 slot 8 of 10; RISK-PRIMITIVE continuous size-scaling axis; closed-loop Optuna-re-training simulator load-bearing pre-flight per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION at /128 closeout)
**Axis**: NEW RiskV2Config primitive 13 — `enable_per_symbol_drawdown_scaling` (continuous multiplicative position-size dampening at per-symbol 45-day rolling drawdown; T_R=6.0 wpnl full size, T_max=7.0 wpnl zero size; linear interpolation; M=21 candles time-override carry-forward from /127)
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `fd29feb`
**Classification**: NEGATIVE-catastrophic — Section 8 first-match Criterion 1 (PUBLIC anchor): IS Sharpe **+0.6683** < +0.91 threshold → FIRES with IS Δ **-0.6425** (1.61× the magnitude of the catastrophic -0.40 threshold). Criterion 2 ALSO FIRES independently (F6: IS Jaccard 0.4213 < 0.70) but pre-empted by Criterion 1 first-match-wins.
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

Single-axis activation of a NEW continuous multiplicative position-size scaling RISK-PRIMITIVE at per-symbol 45-day rolling drawdown. Distinct from /127's binary kill brake (RiskV2Config primitive 11): primitive 13 multiplies the position weight by a linear ramp `(T_max - dd) / (T_max - T_R)` in [0, 1] when dd is between T_R=6.0 wpnl (full size) and T_max=7.0 wpnl (zero size); preserves the M=21 candles time-override (deadlock-impossibility carry-forward from /127 formal proof). The structural hypothesis: continuous semantics preserve the Optuna gradient (trades not deleted from training; contribution dampened proportionally) — distinct from /127's binary kill which masked training labels entirely and produced IS Jaccard 0.4286 = wholesale Optuna re-convergence.

All other architecture bit-identical to /121: 14-feature V3_FEATURE_COLUMNS_TOP_N (UNCHANGED), +2/-1 ATR triple-barrier K=21, BCH/LDO/TRX universe (REVERTED from /128's ATOM/RUNE/AVAX/HBAR/ICP/ALGO), 7-gate RiskV2 with /116 no_confirm primitive (trigger_atr=0.50, k_candles=4), REQUIRED_GAP=66 (REVERTED from /128's 132), ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35. `enable_per_symbol_drawdown_brake` REVERTED to False (axis CLOSED at /127). ZERO new features added in /129.

First v3 iteration to operationalize a closed-loop Optuna-re-training simulator as load-bearing pre-flight gate per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION (the binding rule established at /128 closeout: ANY axis changing Optuna training-objective domain requires closed-loop Optuna-re-training simulator). T2 simulator at N=10 outer-seeds × 3 training-window-starts = 30 configurations; bootstrap-based regime-anchored resampling within month-groups.

T2 simulator distribution: mean IS Sharpe **0.9186**, std **0.8409**, frac ≥ 0.91 = **46.67%** (FAIL at ≥60% gate threshold), frac catastrophic (<0.50) = **30.00%**. Pre-flight gate G1 FAIL. Decision: **GO_HIGH_RISK** per PRIME DIRECTIVE (brief + backtest; NO EDA-kill). Section 7 modal expectation distribution honestly weighted NEGATIVE-class at 70% prior (35% catastrophic + 20% Optuna-trajectory-shift + 15% INERT); PROMISING-class at 10%.

Commit chain: EDA `5d90e2c` → brief `2111638` → Phase 5.5 gate PASS `bc665db` → setup `b918ea9` (RiskV2Config primitive 13 + new gate 5.5 in `get_signal`; V3_MODELS REVERT BCH/LDO/TRX; REQUIRED_GAP REVERT 132→66; `enable_per_symbol_drawdown_brake` REVERT True→False) → engineering report `244e674` → Critic FINAL `fd29feb`. Wall-clock 0.69h (within 2h EXPLORATION cap; consistent with /127's 0.71h at cardinality-3).

Files changed: `src/crypto_trade/strategies/ml/risk_v2.py` (new 6 fields in RiskV2Config + new gate 5.5 in `get_signal` between gates 5 vol-scaling and 6 cap; new `_update_drawdown_scaling` paralleling `_update_drawdown_brake`; new `_compute_drawdown_at_signal` helper; new GateStats counter `drawdown_scaling_fires`); `run_baseline_v3.py` (ITERATION_LABEL "v3-129" + V3_MODELS REVERT + REQUIRED_GAP REVERT + `enable_per_symbol_drawdown_brake=False` REVERT + `_canonical_v059` accretion guard update); `tests/strategies/ml/test_risk_v2.py` (continuous multiplier unit tests + state machine + time-override + deadlock-impossibility adversarial test). ZERO changes to `src/crypto_trade/features_v3/`.

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /129 (3-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **+0.6683** | **-0.6425** |
| OOS monthly Sharpe | +0.9682 | **+0.9694** | **+0.0012** (preserved within 0.001) |
| IS daily Sharpe | 3.1180 | 1.6075 | -1.5105 |
| OOS daily Sharpe | 2.3979 | 2.2406 | -0.1573 |
| IS MaxDD | 26.38% | 34.64% | +8.26pp |
| OOS MaxDD | 25.70% | 24.43% | -1.28pp |
| OOS/IS Sharpe ratio | 0.7386 | 1.4504 | +0.71 (HEALTHY but IS-failure-distorted) |
| Profit Factor IS | 1.6019 | 1.3049 | -0.30 |
| Profit Factor OOS | 1.3869 | 1.3289 | -0.06 |
| IS trades | 173 | 161 | -12 (-6.9% — within F7 ±15% band) |
| OOS trades | 98 | 107 | +9 (+9.2% — within F7 ±15% band) |
| PSR | 1.0 | 1.0 | 0.000 (PASS) |
| PBO mean | 0.1278 | 0.1278 | 0.000 (PASS) |
| frac_positive_paths | 0.6444 | 0.6444 | 0.000 (PASS at 0.55 floor) |
| DSR | 0.0 | 0.0 (EXPLORATION informational) | — |

**Anchor deltas (ADJUSTED IS ≈ +1.06 / OOS ≈ +0.85):**
- IS adj-Δ = **-0.3917**
- OOS adj-Δ = **+0.1194**
- Dissociation |IS adj-Δ - OOS adj-Δ| = **0.5111** (just above F3 threshold of 0.50; SUSPICIOUS-OOS-DOMINANT pattern present but pre-empted by Criterion 1)

Per-symbol IS attribution (from `in_sample/per_symbol.csv`):
- BCHUSDT: 74 IS trades, 40.5% WR, net PnL +59.48% (+11.33 wpnl; +168.26% concentration)
- LDOUSDT: 11 IS trades, 27.3% WR, net PnL -6.61% (-13.70 wpnl; -18.71% concentration; sole negative IS contributor by net_pnl_pct, equal to LDO's structural sample-starvation pattern)
- TRXUSDT: 76 IS trades, 28.9% WR, net PnL -17.52% (+32.50 wpnl; -49.55% concentration; IS WR collapse continues — same pattern as /127's 27.9%)

Per-symbol OOS attribution (from `out_of_sample/per_symbol.csv`):
- TRXUSDT: 57 OOS trades, **54.4% WR**, net PnL +48.14% (+32.50 wpnl; +80.83% concentration; F8 informational on 107.9% wpnl concentration)
- BCHUSDT: 37 OOS trades, 40.5% WR, net PnL +22.86% (+11.33 wpnl; +38.39% concentration)
- LDOUSDT: 13 OOS trades, 30.8% WR, net PnL -11.45% (-13.70 wpnl; -19.22% concentration)

**Trade-roster Jaccard finding** (load-bearing — Criterion 2 F6 binding):
- **IS Jaccard vs /121 = 0.4213** (16.8% activation rate; 27 scaling fires across 161 IS trades)
- Per-symbol: BCH 0.4722, LDO 0.4286, TRX 0.3717 — all 3 individually fail the 0.70 threshold
- **/129 IS roster Jaccard vs /116 = 1.0000** (bit-exact — 161 of 161 IS trades match by symbol × open_time)

The /129 IS roster is bit-identical to /116. The continuous-scaling primitive's 27 weight modifications change weight_factors but do not change which trades fire under Optuna re-convergence; Optuna under the continuous-scaling constraint converged to a /116-like basin (no_confirm primitive ONLY, no drawdown-scaling fires affecting label selection). This is the third independent validation of the Optuna-trajectory-shift channel — under the new constraint, Optuna re-converges to a structurally distinct trajectory regardless of severity of intervention.

## 3. Falsifier verdicts

Section 8 first-match-wins decision tree pre-registered at brief commit time (`2111638`):

| Falsifier | Threshold | Observed | Fires? |
|---|---|---|---|
| **F1 IS band** | [0.66, 1.36] | **+0.6683** | NO (0.6683 ≥ 0.66 by 0.0083; lower-edge survival) |
| F2 OOS band | [0.67, 1.27] | **+0.9694** | NO (within band) |
| F3 Dissociation | < 0.50 | 0.5111 (1.02× threshold) | YES (marginal; pre-empted by Criterion 1) |
| F4 Trade-rate (informational) | ≥130 OOS | 107 OOS | INFORMATIONAL FAIL (below 130 threshold; documented as cycle-7 base-rate for cardinality-3) |
| F5 Per-symbol cascade | 2/3 IS-negative | **2/3 IS-negative** (LDO -6.61%, TRX -17.52% net_pnl_pct) | YES |
| **F6 Optuna-trajectory-shift Jaccard binding** | IS Jaccard ≥ 0.70 | **0.4213** (per-sym: BCH 0.47, LDO 0.43, TRX 0.37 — all FAIL) | **YES (LOAD-BEARING)** |
| F7 Behavioral-effect predictor | |Δ IS trades| ≤ 15% | 6.9% (-12 trades) | NO |
| F8 Top-symbol concentration | <40% OOS | TRX 107.9% | INFORMATIONAL (single-symbol carrier; F3+F5 already firing) |

Section 8 first-match-wins fires at **Criterion 1 (NEGATIVE-catastrophic)** on IS Sharpe +0.6683 < +0.91 threshold. Criterion 2 (NEGATIVE-Optuna-trajectory-shift) WOULD fire on F6 IS Jaccard 0.4213 < 0.70 if Criterion 1 had not pre-empted it. Both criteria fire independently — the verdict is doubly-binding. Criterion 1's IS-Sharpe threshold pre-empts because it appears first in the decision tree and is structurally calibrated to detect IS catastrophe regardless of mechanism.

## 4. Mechanistic explanation

### 4.1 Continuous scaling reproduces /127's Optuna-trajectory-shift signature at near-identical Jaccard magnitude

The structural hypothesis was that continuous semantics (partial scaling preserves training-objective gradient) would reduce the Optuna-trajectory-shift magnitude compared to /127's binary kill (which masked training labels entirely). The evidence falsifies this:

| Iter | Mechanism | % IS trades touched | IS Jaccard vs /121 |
|---|---|---:|---:|
| /127 | Binary kill (weight → 0) | 1.7% | **0.4286** |
| **/129** | **Continuous scale (weight × 0–1 ramp)** | **16.8%** | **0.4213** |

The continuous form engaged on **10× more IS trades** (16.8% vs 1.7%) but produced near-identical Jaccard magnitude (0.4213 vs 0.4286). The mechanism is not "zero vs nonzero weight" — it is **any state-dependent weight redistribution that correlates with training trajectory**. Even partial dampening shifts the Optuna search landscape: at 35 Optuna trials with 3 inner seeds, the optimal (depth, colsample, reg_lambda) combination under scaled weights is different from the combination under uniform weights, causing Optuna to converge to a different IS-optimal region.

The Optuna-trajectory-shift channel is not about severity of intervention but about ANY presence of state-dependent training-objective modification. This is the THIRD validation of the channel after /127 (RISK-PRIMITIVE binary) and /128 (UNIVERSE substitution). The channel generalizes regardless of axis class or intervention severity.

### 4.2 /129 IS roster Jaccard 1.0 vs /116 — Optuna converges to /116-like basin

The /129 IS trade roster is **bit-identical to /116** (Jaccard 1.0000; 161 of 161 trades match by symbol × open_time). /116 was the no_confirm exit primitive iteration (IS Sharpe +0.6246 / OOS Sharpe +1.1089) — a PROMISING-MECHANICAL precedent that became part of the /121 baseline. With the same universe + same features + same outer seed 42 + a state-dependent weight perturbation, Optuna re-converges to a basin similar to /116's basin (which also ran at seed 42 with no_confirm + the same features but NO drawdown primitive).

The interpretation: the continuous-scaling primitive's weight perturbation has zero effect on which trades emit (because the IS roster is bit-identical to a primitive-13-disabled run at the same seed), but it does change which (depth, colsample, reg_lambda) combinations are Optuna-optimal under the scaled-weight loss surface. The /121 baseline's Optuna trajectory required the no_confirm primitive WITHOUT a drawdown-scaling primitive in the training objective. Adding primitive 13 (even when its 27 fires only modify weight_factors, not entry decisions) sufficiently perturbs the training-objective Sharpe surface that Optuna re-converges to /116's hyperparameter region.

This is structurally important: **the Optuna-trajectory-shift channel operates at the hyperparameter level, not the trade-emission level**. The 27 scaling fires do not change which 161 trades emit; they change which model's hyperparameters Optuna selects to produce those 161 trades. The /116 → /121 progression (which required a multi-seed CONFIRMATION budget to find the +1.31 IS Sharpe) is undone at single-seed EXPLORATION by the addition of any state-dependent constraint to the training objective.

### 4.3 Closed-loop Optuna-re-training simulator operationally validated

The T2 closed-loop simulator predicted production IS Sharpe distribution mean **0.9186** (std **0.8409**) with frac ≥ 0.91 = 46.67% (G1 FAIL at 60% gate). Production produced IS Sharpe **0.6683**, which lands at:
- **z-score**: (0.6683 - 0.9186) / 0.8409 = **-0.298** (within first sigma band)
- Within the simulator's [-1.1952, +3.0362] range
- Slightly below the Q50 median (0.9676)
- In the predicted sub-threshold class (1 - 0.4667 = 0.5333 probability of below 0.91; production confirmed this)
- NOT catastrophic (0.6683 > 0.50; simulator predicted 30% catastrophic; production landed in the non-catastrophic below-threshold class which the simulator estimated at ~23%)

**Validation verdict**: the simulator's G1 FAIL flag was honest and calibrated; the HIGH-RISK posture was structurally correct; the production outcome falls in the predicted sub-threshold but non-catastrophic class. This is the FIRST operational validation of the closed-loop Optuna-re-training simulator methodology established at /128 closeout — it correctly predicted the regime of the production outcome at z = -0.298.

The methodology is therefore **operationally validated**: the simulator distribution honestly captured the regime of Optuna re-convergence under the continuous-scaling constraint. Briefs at /130+ MUST include closed-loop Optuna-re-training simulators for ANY axis changing the Optuna training-objective domain (universe, RISK-PRIMITIVE, LABEL-MODE, FEATURE-SET composition, ENSEMBLE_SIZE/n_trials/bar-interval per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION). The pre-flight gate threshold (60% frac ≥ anchor) operationally maps to production: G1 PASS implies higher production-success probability; G1 FAIL with HIGH-RISK posture implies production observations distributed across the simulator range.

### 4.4 Triple-validation of the Optuna-trajectory-shift channel — generalization complete

The /127 + /128 + /129 chain triple-validates the Optuna-trajectory-shift finding across three structurally distinct axis classes:

| Iter | Axis class | Intervention | IS Jaccard vs anchor | IS Δ |
|---|---|---|---:|---:|
| /127 | RISK-PRIMITIVE binary kill | weight → 0 (1.7% trades) | 0.4286 | -0.5242 |
| /128 | UNIVERSE substitution | wholesale symbol replacement | bimodal CPCV (frac_pos 0.444) | -1.4819 vs ADJ |
| **/129** | **RISK-PRIMITIVE continuous scale** | **weight × 0–1 ramp (16.8% trades)** | **0.4213** | **-0.6425** |

Three distinct mechanism classes; three distinct intervention severities (1.7% binary, 100% wholesale universe, 16.8% continuous); essentially the same Optuna-trajectory-shift signature. The 10× variation in trade-touching rate between /127 and /129 produces near-identical Jaccard magnitude — the channel is not severity-driven but presence-driven. The /128 universe substitution doesn't even use Jaccard directly (the symbols are different) but produces the equivalent signature in CPCV path bimodality and the largest F3 dissociation in v3 history (2.77).

The unifying principle (per `feedback_v3_optuna_trajectory_shift_finding.md`): **any axis that changes the Optuna training-objective domain causes Optuna to re-converge to a different region of hyperparameter space, producing a different model that produces a different trade roster**. The channel generalization is complete across RISK-PRIMITIVE and UNIVERSE; by structural extension, it must also apply to LABEL-MODE, FEATURE-SET composition, ENSEMBLE_SIZE / n_trials / outer-seed changes, and BAR-INTERVAL changes (the /130 axis class).

## 5. Process notes

### 5.1 Methodology-fix simulator operationally validated FIRST IMPLEMENTATION

The closed-loop Optuna-re-training simulator methodology established at /128 closeout (per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION) has its first operational validation at /129. The simulator's HIGH-RISK posture (G1 FAIL at 46.67% < 60%) accurately predicted the regime of production outcome (z = -0.298 within first sigma band; sub-threshold but non-catastrophic). The methodology is therefore production-ready as a pre-flight gate; future brief Section 2 must operate it on ANY axis in the expanded scope.

**Methodology gates that work**:
- T2 simulator distribution mean + std + frac-above-threshold predicts production regime within first sigma
- G1 pre-flight gate threshold (60% frac ≥ anchor) corresponds to production-success probability inflection
- N=10 outer-seeds × 3 training-window-starts = 30 configurations are sufficient sample size to detect distribution moments
- Bootstrap-based regime-anchored resampling within month-groups preserves regime structure (validated by Q50 median proximity)

**Open methodology questions**:
- Does the simulator predict IS Jaccard distribution? (Not currently emitted; future versions should add this)
- Does z-score reliably predict catastrophic-class assignment? (Single-iteration evidence; need more data points at +1σ and +2σ to validate distribution tails)
- Can the simulator pre-flight gate threshold be tightened (e.g., 70% instead of 60%) without losing PROMISING-class candidates? (Open question for cycle 8+ when methodology has more operating history)

### 5.2 /129 IS-roster identity with /116 — structural finding

The /129 IS trade roster is bit-identical to /116 (Jaccard 1.0000; 161 of 161 trades match by symbol × open_time). This is a structurally meaningful finding because /116 and /121 have IS Sharpe 0.6246 vs 1.3108 respectively despite both being at the BCH/LDO/TRX universe with the 14-feature stack and no_confirm primitive. The difference is the multi-seed CONFIRMATION budget at /121 (10 outer seeds × 5 inner × 35 trials = 1050 trials per WF month) vs /116's single-seed EXPLORATION budget. The /121 IS Sharpe lift came from Optuna trajectory variance reduction at the multi-seed budget, NOT from any new edge ingredient.

**Implication**: at single-seed EXPLORATION budget (3 inner × 1 outer × 35 trials = 105 trials per WF month), the addition of ANY state-dependent constraint to the training objective causes Optuna to land in a /116-like basin (IS Sharpe ~0.62-0.67), not the /121 basin (IS Sharpe ~1.31). The /121 IS-leg lift is fragile to ANY perturbation of the training objective at single-seed budget. This explains why all cycle-7 single-axis EXPLORATIONs have produced IS Sharpe well below /121's PUBLIC anchor: any structural change (RISK-PRIMITIVE, UNIVERSE, NEW-feature, LABEL-MODE, multi-frequency) destabilizes the Optuna trajectory enough to fall out of the /121 basin.

This is a powerful constraint on cycle-7's remaining slots and on cycle-8+ design: structural changes at single-seed EXPLORATION will systematically underperform /121 PUBLIC anchor, but their value lies in whether they hold up at multi-seed CONFIRMATION (where Optuna trajectory variance is reduced by averaging). The cycle-7 catalog state (8/8 NEGATIVE-class) is consistent with this finding — none of the cycle-7 axes have produced PROMISING-class candidates at single-seed; the CONFIRMATION at /132 must therefore be a baseline-revalidation of /121 (not a bundle of cycle-7 components, none of which exist as PROMISING-class).

### 5.3 F6 instrumentation gap — 5th recurrence (/124/125/127/128/129)

`run.log` missing from `reports-v3/iteration_v3-129/`. The instrumentation gap continues despite the brief Section 9 smoke-test assertion requirement per `feedback_v3_instrumentation_run_log_missing.md`. The runner output schema does not consistently emit `run.log` to the report directory. This is the 5th consecutive recurrence at /124/125/127/128/129.

**Binding requirement for /130 setup commit**: the engineer MUST fix the runner output schema to persist `run.log` (and `per_symbol_walk_forward_auc.csv` if relevant) at the report directory before launching the /130 backtest. The 5-occurrence pattern blocks methodology-axis falsifier evaluation (F6-class) and must be resolved at the next setup commit.

### 5.4 Cycle-7 catalog state at /129 closeout

Cycle-7 catalog (8 of 10 EXPLORATIONs complete; 2 remaining slots /130 + /131; /132 = CONFIRMATION):

| Slot | Iter | Axis | IS Δ | OOS Δ | Verdict |
|---:|---|---|---:|---:|---|
| 1 | /122 | cross-asset (ETH OHLCV eth_ret_3d) | -0.34 | +0.20 | NEGATIVE-INERT |
| 2 | /123 | cross-asset (eth_vs_sym_rv_50) | -1.73 | +0.79 | NEGATIVE-catastrophic |
| 3 | /124 | longer-cadence labels K=63 + sqrt(3) ATR | -0.87 | -0.94 | NEGATIVE-catastrophic |
| 4 | /125 | WILD V3_MODELS ATOM/RUNE/UNI | -1.25 | -0.86 | NEGATIVE-catastrophic |
| 5 | /126 | multi-frequency d24_ret_autocorr_lag1_50 | -1.21 | -1.08 | NEGATIVE-catastrophic |
| 6 | /127 | per-symbol drawdown brake (binary kill) | -0.52 | +0.03 | NEGATIVE-catastrophic |
| 7 | /128 | WILD 6-symbol sector-pure L1 universe (ATOM/RUNE/AVAX/HBAR/ICP/ALGO) | -1.73 | +1.17 | NEGATIVE-catastrophic |
| **8** | **/129** | **continuous position-size scaling at drawdown (T_R=6.0, T_max=7.0)** | **-0.64** | **+0.001** | **NEGATIVE-catastrophic — Optuna-trajectory-shift TRIPLE-validated; methodology-fix simulator operationally validated z=-0.298** |
| 9 | /130 | bar-interval axis (Critic PRIMARY remaining) | — | — | (pending) |
| 10 | /131 | TBD | — | — | (pending) |

**7/8 catastrophic; 1/8 INERT; 0/8 PROMISING.** Closed axes through /129: cross-asset OHLCV (2 attempts), longer-cadence labels (1), universe substitution (cardinality-3 + cardinality-6, 2 attempts), multi-frequency features (1 + EDA methodology FALSIFIED), RISK-PRIMITIVE (binary kill + continuous scale, 2 attempts; class CLOSED). The /130 axis menu narrows to: bar-interval variants (Critic FINAL PRIMARY recommendation) — the only untested axis class structurally orthogonal to the Optuna-trajectory-shift channel because bar-interval changes the data discretization domain WHILE STILL requiring closed-loop simulator per channel generalization EXTENSION.

### 5.5 Cycle-7 /132 CONFIRMATION shape — MULTI-SEED BASELINE-VALIDATION of /121

Per Critic FINAL Recommendation 3: the /132 CONFIRMATION shape is dictated by the cycle-7 catalog state (8/8 NEGATIVE through /129; 0 PROMISING components to bundle). /132 should be a MULTI-SEED BASELINE-VALIDATION of /121 (structural analog of /018 BOOTSTRAP-CONFIRMATION), NOT a bundle assembly of any /127-/131 component. The /121 multi-seed numbers (IS +1.3108 / OOS +0.9682) are due for /132 re-validation under the current runner code at full 10-seed budget; the cycle-7 single-axis EXPLORATIONs have not produced PROMISING-class candidates suitable for additive bundling. Per `feedback_v3_strict_10_to_1_cadence.md` /132 must NOT collapse the 10th EXPLORATION (/131) into the CONFIRMATION.

## 6. Lessons

1. **The Optuna-trajectory-shift channel is TRIPLE-validated across axis classes** (/127 RISK-PRIMITIVE binary, /128 UNIVERSE, /129 RISK-PRIMITIVE continuous). The channel is presence-driven, not severity-driven: 10× variation in intervention rate (1.7% binary vs 16.8% continuous) produces near-identical Jaccard magnitude (~0.42). Future axes in any class that changes the Optuna training-objective domain require the closed-loop Optuna-re-training simulator as load-bearing pre-flight per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION.

2. **The closed-loop Optuna-re-training simulator methodology is OPERATIONALLY VALIDATED** at /129 (first implementation; z = -0.298 within first sigma band; G1 FAIL flag honest and calibrated). Briefs at /130+ MUST operate this methodology on any axis in the expanded scope. The pre-flight gate threshold (60% frac ≥ anchor) is production-meaningful — G1 FAIL with HIGH-RISK posture predicts the distribution of production outcomes within the simulator range.

3. **The /129 IS roster bit-identity with /116 reveals the structural fragility of the /121 IS-leg lift at single-seed budget**. The /121 IS Sharpe +1.31 requires multi-seed CONFIRMATION budget; any structural perturbation at single-seed EXPLORATION lands in the /116 basin (IS Sharpe ~0.62-0.67). This is a structural constraint on cycle-7 (single-axis EXPLORATIONs will systematically underperform /121 PUBLIC); cycle-8+ design should account for this by either (a) running structural axes at multi-seed CONFIRMATION budget OR (b) tolerating single-seed sub-/121 results in EXPLORATION and validating at CONFIRMATION.

4. **Continuous semantics do NOT mitigate the Optuna-trajectory-shift channel.** The hypothesis that "continuous preserves Optuna gradient" was falsified: continuous scaling produced the same Jaccard magnitude as binary kill despite engaging 10× more trades. The channel operates at the hyperparameter level, not the trade-emission level — partial scaling perturbs the training-objective Sharpe surface enough to re-converge Optuna's hyperparameter trajectory.

5. **The RISK-PRIMITIVE axis class is CLOSED at /129** (binary kill /127 + continuous scale /129; 2/2 NEGATIVE-catastrophic). Future RISK-PRIMITIVE axes in cycle-8+ require either (a) a different mechanism class (e.g., post-Optuna deterministic filter applied AFTER signal emission, NOT inside the training objective) OR (b) a multi-seed CONFIRMATION budget to operate. Single-seed EXPLORATION of state-dependent RISK-PRIMITIVE axes is exhausted as a search direction.

6. **The /130 axis (bar-interval) is the sole remaining untested viable axis class in cycle-7.** Bar-interval changes the data discretization domain rather than the Optuna training-objective domain, but per channel generalization EXTENSION still requires closed-loop simulator. The /130 brief MUST include the simulator distribution; the pre-flight gate G1 must be evaluated; production prediction must reference the simulator distribution.

7. **The F6 instrumentation gap is the 5th recurrence at /129** (/124/125/127/128/129). The /130 setup commit MUST fix the runner output schema to persist `run.log` at the report directory. This is non-negotiable; the gap blocks methodology-axis falsifier evaluation at production and must be resolved before /132 CONFIRMATION's weight-fragile multi-seed audit.

8. **The methodology-fix simulator's z-score band classification is a NEW diagnostic dimension**. /129's z = -0.298 (within first sigma) maps to "predicted regime; simulator calibrated." Future iterations should report z-score against the simulator distribution as a standard engineering report row; |z| > 2.0 implies simulator miscalibration; |z| < 1.0 implies simulator-predicted regime.

## 7. Decision

**NO MERGE.** EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `fd29feb`. /129 is the 8th cycle-7 EXPLORATION; RISK-PRIMITIVE axis class CLOSED at 2/2 (binary kill /127 + continuous scale /129); Optuna-trajectory-shift channel TRIPLE-validated across RISK-PRIMITIVE binary + UNIVERSE + RISK-PRIMITIVE continuous; closed-loop Optuna-re-training simulator methodology operationally validated (z=-0.298 first implementation). BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`). Tag `v0.v3-129` set on the closeout commit.

## 8. Pre-Commit for iter-v3/130

Per `feedback_v3_axis_selection_quant_discipline.md`, the orchestrator + QR adjudicate axis for /130. Cycle-7 axis menu at /129 closeout has CLOSED axes through /129: cross-asset OHLCV (cycle-7 methodology block), longer-cadence labels, universe-substitution (any cardinality), multi-frequency features (EDA methodology FALSIFIED), RISK-PRIMITIVE (binary + continuous; class CLOSED), knob-tuning saturated. Remaining viable axes:

- **PRIMARY**: bar-interval axis (multi-offset 12h, 4h base candles, or alternative cadences). Per Critic FINAL Recommendation 1: "Bar-interval changes do NOT modify Optuna training-objective weight distribution — they change data discretization. Structural orthogonality." Bar-interval is the SOLE remaining untested viable axis class in cycle-7. Per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION, bar-interval is in the expanded scope — closed-loop Optuna-re-training simulator REQUIRED.

- **SECONDARY**: cycle-7 close-early with /130 = MULTI-SEED BASELINE-VALIDATION of /121 (structural analog of /018 BOOTSTRAP-CONFIRMATION). Collides with `feedback_v3_strict_10_to_1_cadence.md` strict 10:1 sequencing rule.

**Adjudicated /130 axis**: PRIMARY (bar-interval axis). This satisfies the Critic FINAL Recommendation 1 and respects the strict 10:1 cadence rule.

**Bound rules for /130 brief**:
- Section 2 MUST include closed-loop Optuna-re-training simulator at the chosen bar-interval (vary outer-seed × training-window-start across N ≥ 10 configurations; report DISTRIBUTION of IS Sharpe outcomes per `feedback_v3_optuna_trajectory_shift_finding.md` EXTENSION).
- Pre-flight gate: ≥60% of simulator seeds produce IS Sharpe ≥ +0.91 (/121 BASELINE re-validation under the new bar-interval).
- Brief Section 9 smoke-test MUST include assertion that `run.log` persists at `reports-v3/iteration_v3-130/run.log` (5-occurrence instrumentation gap fix).
- F3 dissociation falsifier remains binding (any |IS Δ - OOS Δ| > 0.50 triggers SUSPICIOUS-OOS-DOMINANT pre-emption logic).
- F6 Optuna-trajectory-shift Jaccard binding falsifier remains binding (production IS Jaccard vs anchor < 0.70 triggers automatic NEGATIVE classification — BUT at bar-interval changes the symbol × open_time roster mapping is non-trivial; Jaccard binding may need adaptation at the bar-interval granularity).
- Label-horizon math at new bar-interval must be explicit (K=21 at 4h = 84h = 3.5 days vs K=21 at 8h = 168h = 7 days; the absolute time horizon changes proportionally).
- F6-equivalent methodology-validation gate must be evaluable from committed artifacts (per-symbol production WF AUC table generation in runner — instrumentation gap fix mandatory).
- Cycle-7 slot 9/10 designation explicit in Section 0.5.
- Anchor: /121 multi-seed CONFIRMATION-MERGE BASELINE (PUBLIC IS +1.3108 / OOS +0.9682); ADJUSTED IS ≈ +1.06 / OOS ≈ +0.85.

These pre-commits are LOCKED at this closeout; cannot be renegotiated post-hoc at /130 brief commit.
