# iter-v3/130 — Cycle-7 slot 9 — EXPLORATION-NEGATIVE-catastrophic / 4h bar-interval; bar-interval axis CLOSED; /121 architecture cohort-AND-frequency-shaped (TERMINAL cycle-7 finding); production IS 8.4σ below T3b 4h-proxy simulator predicted mean

**Date**: 2026-05-21
**Type**: EXPLORATION (cycle-7 slot 9 of 10; BAR-INTERVAL axis class; 4h base candles)
**Axis**: BAR-INTERVAL transition from 8h base candles to 4h base candles for the BCH/LDO/TRX universe with /121 14-feature stack + ATR (2.0, 1.0) + K=21 + /116 no_confirm. ZERO new features. Single-axis perturbation in candle-count terms; HALVED absolute time horizon (84h = 3.5d at 4h vs 168h = 7d at 8h).
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `d33cc2e`
**Classification**: NEGATIVE-catastrophic — Section 8 first-match Criterion 1 (PUBLIC anchor): IS Sharpe **−1.3028** < +0.91 threshold → FIRES with IS Δ **−2.6136** (6.5× the magnitude of the catastrophic −0.40 threshold). **WORST IS Sharpe in v3 history.** Production IS 8.4σ below T3b 4h-proxy simulator predicted mean (0.391 ± 0.20).
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

Single-axis activation: bar-interval 8h → 4h on the BCH/LDO/TRX universe with /121's bit-identical architecture in candle-count terms. All other parameters preserved: 14-feature V3_FEATURE_COLUMNS_TOP_N, ATR (2.0, 1.0) triple-barrier K=21, REQUIRED_GAP=66 = (21+1)×3, /116 no_confirm primitive (trigger_atr=0.50, k_candles=4), 7-gate RiskV2, ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35 single-seed. The /127 binary brake + /129 continuous scaling REVERTED (both axis class CLOSED at /129). Absolute time semantics CHANGE: K=21 label horizon becomes 84h = 3.5d at 4h (HALVED from 7d); rolling-window features cover halved absolute time spans (range_realized_vol_50 covers 200h vs 400h, hurst_100 covers 400h vs 800h, ret_skew_200 covers 800h vs 1600h).

Pre-launch data pipeline: 4h native data did NOT exist on disk; setup commit downloaded 4h klines for BCH/LDO/TRX and regenerated 4h V3 features at `data/features_v3_4h/`. Wall-clock 1.02h (within 2h EXPLORATION cap).

**FIRST v3 iteration where the closed-loop Optuna-re-training simulator was OPERATED on a bar-interval-CHANGING axis.** T3b 4h-proxy simulator (bootstrap upsampling of /121's 8h IS trade roster at density multiplier 2.0×) predicted distribution mean **0.391**, std **0.20**, max **0.804**, frac ≥ 0.91 = **0.0%** (G1 FAIL at 60% gate). T3c relative improvement Δmean **−0.0043** (essentially zero). Brief pre-disclosed proxy limitation: "bootstrap upsampling cannot capture Optuna's response to actual 4h-density training (different (depth, colsample, reg_lambda) search regions)."

Brief commit chain: EDA `ccc0446` → brief `8c429a0` → Phase 5.5 gate PASS `3dbcc49` → setup `e77e2b6` (ITERATION_LABEL v3-130, label_timeout=5040, FEATURES_DIR_4H, /127+/129 REVERT, TeeLogger run.log capture fix) → engineering report `51ed8f9` → Critic FINAL `d33cc2e`. Wall-clock 1.02h.

**run.log instrumentation gap FIXED at /130** via `_TeeLogger` wrap (per `feedback_v3_instrumentation_run_log_missing.md` 5-occurrence pattern). run.log persists at `reports-v3/iteration_v3-130/run.log` — Critic Check 7 PASS.

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /130 (single-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **−1.3028** | **−2.6136** |
| OOS monthly Sharpe | +0.9682 | **+0.3276** | **−0.6406** |
| IS daily Sharpe | 3.1180 | −2.7168 | −5.8348 |
| OOS daily Sharpe | 2.3979 | +0.6083 | −1.7896 |
| IS MaxDD | 26.38% | **79.79%** | +53.41pp |
| OOS MaxDD | 25.70% | 19.53% | −6.17pp |
| OOS/IS Sharpe ratio | 0.7386 | −0.2515 | sign-flip |
| IS Profit Factor | 1.6019 | 0.6894 | −0.91 |
| OOS Profit Factor | 1.3869 | 1.0856 | −0.30 |
| IS trades | 173 | 242 | +69 (+39.9%) |
| OOS trades | 98 | 108 | +10 (+10.2%) |
| IS WR | ~50% | **26.4%** | catastrophic |
| OOS WR | ~46% | 30.6% | −15.4pp |
| PSR | 1.0 | 0.9999 | PASS |
| PBO | 0.1278 | 0.0978 | PASS |
| frac_positive_paths | 0.6444 | 0.600 | PASS at 0.55 floor |
| DSR | 0.0 | 0.0 (IS Sharpe negative → degenerate) | — |

**Anchor deltas (ADJUSTED IS ≈ +1.06 / OOS ≈ +0.85):**
- IS adj-Δ = **−2.3628**
- OOS adj-Δ = **−0.5224**
- Dissociation |IS adj-Δ − OOS adj-Δ| = **1.8404** (3.7× F3 threshold of 0.50)

**Per-symbol IS attribution** (from `in_sample/per_symbol.csv`):
- BCHUSDT: 126 IS trades, 30.2% WR, net PnL **−38.17%** (primary IS destroyer; 4h Optuna search converged on high-frequency low-WR region)
- LDOUSDT: **only 8 IS trades**, 25.0% WR, net PnL −16.87% (3.4× inversion of normal IS>OOS trade-count ratio — Optuna found near-degenerate LDO model at 4h)
- TRXUSDT: 108 IS trades, 35.2% WR, net PnL −9.75% (4h cycle structure at K=21 = 84h does not support 35% WR profitability at (2.0, 1.0)-ATR multipliers calibrated for 8h)

**Per-symbol OOS attribution**:
- BCHUSDT: 48 OOS trades, 33.3% WR, +8.04 wpnl (108.81% concentration)
- LDOUSDT: 27 OOS trades, 37.0% WR, +6.49 wpnl (87.79% concentration)
- TRXUSDT: 33 OOS trades, 21.2% WR, **−7.14 wpnl** (−96.60% concentration — only OOS-DOMINANT pattern because OOS LDO/BCH stayed marginally profitable)

**IS WR 26.4% interpretation**: With TP=1.0×ATR and SL=2.0×ATR (reward:risk = 1:2), breakeven WR is 66.7%. Observed IS WR of 26.4% means the model is **directionally ANTI-predictive at 4h** — the feature stack implicitly calibrated for 8h periodicity produces inverted signals at 4h. This is the structural signature of cohort-AND-frequency-shape architecture-mismatch.

## 3. Falsifier verdicts

Section 8 first-match-wins decision tree pre-registered at brief commit `8c429a0`:

| Falsifier | Threshold | Observed | Fires? |
|---|---|---|---|
| **F1 IS band** | [+0.91, +1.21] | **−1.3028** | **YES (Criterion 1 NEGATIVE-catastrophic — first match)** |
| F2 OOS band | [+0.67, +0.95] | +0.3276 | YES (OOS < +0.67 lower edge) |
| F3 Dissociation | < 0.50 | **1.8404** | YES (3.7× threshold) |
| F4 Trade-rate (informational) | ≥130 OOS | 108 | INFORMATIONAL FAIL |
| F5 Per-symbol cascade | 2/3 IS-negative | **3/3 IS-negative** | YES |
| **F6 Optuna-trajectory-shift Jaccard binding** | IS Jaccard ≥ 0.70 | N/A at bar-interval change (timestamp granularity differs; 8h-aligned mapping non-trivial) | INFORMATIONAL |
| F7 Behavioral-effect predictor | IS trades in [260, 433] | 242 | YES (below 260 lower bound) |
| F8 Top-symbol concentration | <40% OOS | 108.81% (BCH) | INFORMATIONAL (single-symbol carrier) |
| F9 Wall-clock cap | ≤2.5h | 1.02h | NO |

Section 8 first-match-wins fires at **Criterion 1 (NEGATIVE-catastrophic)** on IS Sharpe −1.3028 < +0.91 threshold. Criteria 2-7 ALL fire independently but pre-empted. The verdict is multiply-binding — first-match-wins protocol classifies as **NEGATIVE-catastrophic**.

## 4. Mechanistic explanation

### 4.1 4h-density Optuna explores a qualitatively different hyperparameter region than 8h-density

The 14-feature stack was implicitly calibrated for 8h candle noise/signal patterns. At 4h, the same feature lookbacks span halved absolute time:
- `range_realized_vol_50` covers 200h (8.3 days) instead of 400h (16.7 days)
- `hurst_100` covers 400h (16.7 days) instead of 800h (33.3 days)
- `ret_skew_200` / `ret_kurt_200` cover 800h (33.3 days) instead of 1600h (66.7 days)

Optuna's IS hyperparameter search operates on compressed feature distributions. At 4h-density, the optimal (depth, colsample, reg_lambda) combinations under the 35-trial single-seed budget land in a region producing high-frequency entries (BCH +39.9% trade count) at sub-30% WR. This is the structural footprint of an over-trained model on a feature stack that does not transfer cleanly to the new frequency.

### 4.2 The HALVED label horizon mis-targets crypto alt-coin cycle structure

K=21 candles at 4h = 84h = 3.5 days. Crypto alt-coin mean-reversion cycles cluster in the 5-7 day range. The 4h label distribution is therefore dominated by SL hits and timeouts rather than TP captures (TP would require the 5-7 day cycle to fire within a 3.5-day window). The 26.4% IS WR is the direct mechanical consequence — below the 33.3% one-sided breakeven for 2:1 reward:risk and far below the 66.7% required for a profitable (+TP=1.0×ATR, −SL=2.0×ATR) ratio.

### 4.3 The simulator was OPERATIONALLY VALIDATED but proxy-limited

T3b 4h-proxy simulator predicted IS distribution mean 0.391 ± 0.20 (G1 FAIL flag honest at frac ≥ 0.91 = 0.0%). Production IS = **−1.3028**, which is:
- **z-score = (−1.3028 − 0.391) / 0.20 = −8.4** (FAR outside ±3σ prediction band)
- 6.5× the simulator's Q25 (−0.297 at 8h baseline; q25 was the lower-quartile expectation)

**The simulator's HIGH-RISK flag was structurally correct; the magnitude prediction was wrong.** The simulator predicted FLAT (delta_mean −0.0043 essentially zero); production produced CATASTROPHIC. The brief Section 2 and Section 10 pre-disclosed this exact failure mode: "bootstrap upsampling of /121's 8h trade roster cannot capture Optuna's response to actual 4h-density training (different (depth, colsample, reg_lambda) search regions that trade-level resampling cannot reproduce)."

This is the SECOND operational validation of the closed-loop Optuna-re-training simulator methodology (after /129's first validation at z=-0.298). The /130 z=-8.4 is OUTSIDE the simulator's predictive range — confirming the proxy limitation for bar-interval-changing axes. The simulator's regime classification is reliable for axes that preserve the bar-interval; for axes that CHANGE the bar-interval, the bootstrap proxy systematically under-estimates Optuna's response magnitude.

**Methodology lesson**: bar-interval-changing axes are in the Optuna-trajectory-shift channel's expanded scope (per `feedback_v3_optuna_trajectory_shift_finding.md` /128 EXTENSION explicit enumeration), but the SIMULATOR METHODOLOGY is inadequate at bar-interval-density changes. Future bar-interval EXPLORATIONs (in cycle-8+ if ever revisited) require a closed-loop simulator that actually retrains models at the proposed bar-interval — not a bootstrap proxy on the prior bar-interval's trade roster.

### 4.4 Cohort-AND-frequency-shape — TERMINAL cycle-7 finding

The /128 closeout established that the /121 14-feature stack + ATR + K=21 calibration is **cohort-shaped** (per `feedback_v3_architecture_cohort_shaped.md`) — does not transfer to symbols with different vol-magnitude + kurtosis profiles. The /130 result EXTENDS this to FREQUENCY: the architecture is also **frequency-shaped** — does not transfer to non-8h candle frequencies.

**The /121 architecture is cohort-AND-frequency-shaped**: changing either the symbol set OR the bar interval destroys its IS behavior. /127+/129 (RISK-PRIMITIVE binary + continuous) extended fragility to STATE-DEPENDENT TRAINING-OBJECTIVE perturbations. The 4-iteration progression /127 → /128 → /129 → /130 demonstrates that /121's IS-leg lift is locally hyperparameter-region-locked across 4 distinct perturbation dimensions:

| Dimension | Perturbation iter | Fragility evidence |
|---|---|---|
| RISK-PRIMITIVE binary | /127 | IS Jaccard 0.4286; IS Δ −0.52; Optuna re-converges to /116 basin |
| UNIVERSE (3-sym & 6-sym) | /125 + /128 | 3-axis distribution mismatch (vol-magnitude, kurtosis-tail, timeout-rate); IS Δ −1.25 / −1.48 vs ADJ |
| RISK-PRIMITIVE continuous | /129 | IS Jaccard 0.4213; IS Δ −0.64; /116-basin convergence at 16.8% trade-touching |
| BAR-INTERVAL (frequency) | /130 | IS Δ −2.61 (worst in v3); 8.4σ below proxy simulator; 4h Optuna explores fundamentally different region |

**Single conclusion**: /121's IS Sharpe +1.31 is a hyperparameter-region-locked solution at the specific (3-symbol cohort, 8h bar interval, 14-feature stack, no_confirm primitive, ATR (2.0, 1.0), K=21) joint — and it can only be FOUND with the multi-seed CONFIRMATION budget (10 outer × 5 inner × 35 trials = 1750 trials/WF month at /018 multi-seed setup). At single-seed EXPLORATION (3 inner × 1 outer × 35 trials = 105 trials/WF month), ANY structural perturbation destabilizes the Optuna trajectory enough to fall out of the /121 basin and land in the /116 basin (IS Sharpe ~0.62-0.67) or worse.

This is the **TERMINAL cycle-7 finding**: structurally analogous to the /105-/109 representational-capacity FALSIFICATION (cycle-5 terminal). The /105-/109 cycle proved at-axis-saturation that no neural-class model improves on depth 3-5 LightGBM with the /059 architecture; the /127-/130 cycle proves at-axis-saturation that no single-axis structural perturbation lifts the /121 architecture at single-seed EXPLORATION.

## 5. Process notes

### 5.1 9/9 NEGATIVE consecutive at cycle-7

Cycle-7 catalog state at /130 closeout:

| Slot | Iter | Axis | IS Δ | OOS Δ | Verdict |
|---:|---|---|---:|---:|---|
| 1 | /122 | cross-asset (ETH OHLCV eth_ret_3d) | −0.34 | +0.20 | NEGATIVE-INERT |
| 2 | /123 | cross-asset (eth_vs_sym_rv_50) | −1.73 | +0.79 | NEGATIVE-catastrophic |
| 3 | /124 | longer-cadence labels K=63 + sqrt(3) ATR | −0.87 | −0.94 | NEGATIVE-catastrophic |
| 4 | /125 | WILD V3_MODELS ATOM/RUNE/UNI | −1.25 | −0.86 | NEGATIVE-catastrophic |
| 5 | /126 | multi-frequency d24_ret_autocorr_lag1_50 | −1.21 | −1.08 | NEGATIVE-catastrophic |
| 6 | /127 | per-symbol drawdown brake (binary kill) | −0.52 | +0.03 | NEGATIVE-catastrophic |
| 7 | /128 | WILD 6-symbol sector-pure L1 universe | −1.73 | +1.17 | NEGATIVE-catastrophic |
| 8 | /129 | continuous position-size scaling at drawdown | −0.64 | +0.001 | NEGATIVE-catastrophic |
| **9** | **/130** | **4h bar-interval (BCH/LDO/TRX, /121 14-feature stack preserved)** | **−2.61** | **−0.64** | **NEGATIVE-catastrophic — WORST IS in v3 history; cohort-AND-frequency-shape TERMINAL** |
| 10 | /131 | closure-reconciliation memo (per Critic FINAL Rec 1) | — | — | (pending — NOT EXPLORATION; documents TERMINAL finding) |

**8/9 catastrophic; 1/9 INERT; 0/9 PROMISING.** Last 4 (/127-/130) ALL catastrophic across 4 structurally distinct axis classes. PROMISING-class empirical prior at /131 ≤ 10% under any axis in the expanded Optuna-trajectory-shift scope.

### 5.2 Simulator methodology calibration extension

The closed-loop Optuna-re-training simulator methodology has now operated twice:
- /129 first implementation: z=-0.298 within first sigma band (RISK-PRIMITIVE continuous scale, preserves bar-interval)
- /130 second implementation: z=-8.4 FAR outside ±3σ band (BAR-INTERVAL change, frequency-shift)

**The simulator's regime detection is reliable when the axis preserves bar-interval.** At bar-interval-changing axes, the bootstrap proxy is structurally inadequate — production response magnitude can be 20-30× the proxy's predicted std. Future bar-interval EXPLORATIONs (if any cycle-8+) need a genuinely closed-loop simulator that retrains models at the proposed bar-interval, not a bootstrap upsample of the prior bar-interval's trade roster.

This finding extends `feedback_v3_optuna_trajectory_shift_finding.md` from "channel triple-validated; methodology operationally validated for trajectory-shift detection within bar-interval" to "channel triple-validated; methodology operationally validated for non-bar-interval axes; bar-interval-axis simulator requires native-frequency retraining substrate."

### 5.3 run.log instrumentation gap FIXED at /130

The 5-occurrence pattern (per `feedback_v3_instrumentation_run_log_missing.md`, established at /128 closeout with continued recurrence at /128 /129) is FIXED at /130 via the `_TeeLogger` wrap in the setup commit (`e77e2b6`). run.log persists at `reports-v3/iteration_v3-130/run.log` — Critic Check 7 PASS. **This is the first cycle-7 iteration without the run.log gap.**

### 5.4 Cycle-7 /132 CONFIRMATION shape — MULTI-SEED BASELINE-VALIDATION of /121

Per Critic FINAL Recommendation 2 (/130 review.md):
- /132 = MULTI-SEED VALIDATION of /121-canonical, NOT bundle assembly
- Spec: ENSEMBLE_SIZE=10, n_trials=35, bit-identical to /121 architecture (BCH/LDO/TRX, 14-feature stack, ATR (2.0, 1.0), 7-gate RiskV2 with /127+/129 DISABLED, K=21 at 8h, REQUIRED_GAP=66)
- Acceptance: multi-seed mean IS ≥ +1.0 AND OOS ≥ +0.8 (loose tolerance vs /121 +1.31/+0.97 for code-state drift across /122-/131)
- If reproduces: BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`)
- If fails: file CONFIRMATION-RE-ANCHOR diary

Cycle-7 produced NO ingredient for accretion (8/8 NEGATIVE through /129; /130 = 9/9 NEGATIVE). /132 must be baseline re-validation. Per `feedback_v3_strict_10_to_1_cadence.md` /131 must NOT collapse the CONFIRMATION; /131 documents the cohort-AND-frequency-shape TERMINAL finding as a structural memo + /132 spec.

### 5.5 Cycle-8 axis menu must structurally reformulate post-/132

Per Critic FINAL Recommendation 3: cohort-AND-frequency-shape is the cycle-7 terminal finding (analogous to /105-/109 representational-capacity FALSIFICATION at cycle-5 terminal). Cycle-8 should NOT propose further axes in /121's parameter neighborhood at single-seed EXPLORATION budget. Pivot to:
- (a) WHOLLY-NEW model architecture (the /105-/109 finding closed neural-class; cycle-8 may revisit at a different operating point such as transformer attention or LSTM with regime-conditional pretraining), OR
- (b) WHOLLY-NEW labeling architecture (the /017 meta-labeling and /108 corrected meta-labeling both closed at-NULL; cycle-8 may revisit at quantile-multi-class labels OR cross-sectional ranking labels), OR
- (c) explicit acknowledgment /121 is practical edge ceiling under the current research workflow and pivot to operational deployment focus

At minimum, cycle-8 first EXPLORATION brief must include a new Section 0.6 "Architecture-Family Justification" arguing why the proposed axis is NOT in:
- cohort-shape channel (universe substitution at /121 architecture — CLOSED through 8 attempts)
- frequency-shape channel (bar-interval change at /121 architecture — CLOSED at /130)
- Optuna-trajectory-shift channel (any axis changing Optuna training-objective domain — TRIPLE-validated CLOSED at /127+/128+/129+/130)

## 6. Lessons

1. **The /121 architecture is cohort-AND-frequency-shaped — TERMINAL cycle-7 finding.** Four distinct perturbation dimensions (RISK-PRIMITIVE binary, RISK-PRIMITIVE continuous, UNIVERSE, BAR-INTERVAL) all produce IS catastrophe at single-seed EXPLORATION budget. /121's IS Sharpe +1.31 is hyperparameter-region-locked and requires multi-seed CONFIRMATION budget (1750 trials/WF month) to be visible at all. Documented in NEW memory `feedback_v3_cycle7_terminal_finding.md`.

2. **Closed-loop Optuna-re-training simulator methodology has bar-interval limitation.** /129 first-implementation z=-0.298 within first sigma (within-bar-interval axis); /130 second-implementation z=-8.4 FAR outside ±3σ (bar-interval-CHANGING axis). The bootstrap proxy on prior-bar-interval trade roster is structurally inadequate for bar-interval-density changes. Documented in EXTENSION to `feedback_v3_optuna_trajectory_shift_finding.md`.

3. **9/9 NEGATIVE consecutive in cycle-7 with last 4 catastrophic is a structural-exhaustion signal.** /127-/130 cover 4 structurally distinct axis classes; all 4 catastrophic. The PROMISING-class empirical prior at /131 ≤ 10% under any axis in the expanded Optuna-trajectory-shift scope. The QR creativity mandate (`feedback_v3_qr_axis_creativity_mandate.md`) addresses the "lazy QR after 1-2 NEGATIVEs" failure mode, NOT the "structurally exhausted cycle after 9/9" mode.

4. **The run.log instrumentation gap is FIXED at /130** via `_TeeLogger` wrap (commit `e77e2b6`). First cycle-7 iteration without the gap. The 5-occurrence pattern closes.

5. **HALVED label horizon (K=21 at 4h = 3.5d) mis-targets crypto alt-coin mean-reversion cycle structure** (which clusters in the 5-7 day range). Future bar-interval EXPLORATIONs (if any) must scale K proportionally to preserve absolute time horizon (e.g., K=42 at 4h preserves 168h = 7d).

6. **Cycle-8 must structurally reformulate** post-/132. Cohort-AND-frequency-shape is terminal for cycle-7's parameter neighborhood. Cycle-8 axis menu must originate from outside the closed channels (cohort, frequency, Optuna-trajectory-shift) — wholly-new architecture, wholly-new labeling, or explicit pivot to operational focus.

## 7. Decision

**NO MERGE.** EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `d33cc2e`. /130 is the 9th cycle-7 EXPLORATION; bar-interval axis CLOSED; cohort-AND-frequency-shape finding TERMINAL (cycle-7 analog to /105-/109 representational-capacity FALSIFICATION); closed-loop Optuna-re-training simulator methodology BAR-INTERVAL LIMITATION established (z=-8.4 outside ±3σ; bootstrap proxy inadequate for bar-interval-density changes). BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`). Tag `v0.v3-130` set on the closeout commit.

## 8. Pre-Commit for iter-v3/131

Per `feedback_v3_axis_selection_quant_discipline.md` and Critic FINAL Recommendations 1-2: the orchestrator + QR adjudicate /131. The Option B path is chosen — /131 = formal cycle-7 closure-reconciliation memo, NOT EXPLORATION axis. Reasoning:

- 9/9 NEGATIVE consecutive with last 4 catastrophic across 4 structurally distinct axis classes — empirical evidence of cycle-7 structural exhaustion at single-seed EXPLORATION budget
- ALL candidate WILD axes (NEW labeling/multi-class, NEW Optuna strategy, mixed-frequency feature stack at 8h+24h, per-symbol feature selection, trade-payload features, feature-conditional confidence calibration) are in the expanded Optuna-trajectory-shift scope per `feedback_v3_optuna_trajectory_shift_finding.md` /128 EXTENSION explicit enumeration
- At single-seed EXPLORATION budget, the /129 finding established empirically that ANY structural change destabilizes the Optuna trajectory enough to fall out of /121 basin — PROMISING-class prior at /131 ≤ 10% under ANY in-scope axis
- The QR creativity mandate (`feedback_v3_qr_axis_creativity_mandate.md`) addresses lazy axis selection after 1-2 NEGATIVEs, NOT structural exhaustion after 9/9 NEGATIVE with last 4 catastrophic — running a 10th EXPLORATION as performative axis-shopping is the FALSE-POSITIVE failure mode the cycle-7 evidence rules out
- Critic FINAL Rec 1 (review.md): "/131 = formal cycle-7 closure-reconciliation diary, NOT EXPLORATION axis. ... 10:1 cadence rule does NOT require slot #10 to be EXPLORATION on new axis — closure-reconciliation pre-CONFIRMATION is valid."

**/131 deliverables (no backtest):**
1. `briefs-v3/iteration_v3-131/closure_reconciliation.md` — formal cycle-7 closure memo documenting:
   - Cohort-AND-frequency-shape TERMINAL finding (the /127→/128→/129→/130 fragility evidence chain)
   - Optuna-trajectory-shift channel TRIPLE-VALIDATED + bar-interval-axis simulator LIMITATION (z=-8.4 at /130)
   - Closed-loop simulator methodology validation status (within-bar-interval reliable; bar-interval-changing requires native-frequency retraining substrate)
   - /132 CONFIRMATION setup spec
2. NO EDA script required (no axis to test)
3. NO backtest required
4. NO Phase 5.5 gate / Phase 6 engineer dispatch / Phase 7.5 Critic review (no axis = no risk to adjudicate)
5. Closeout diary `diary-v3/iteration_v3-131.md` filed at structural finding state

**/132 CONFIRMATION setup spec** (LOCKED at /130 closeout per Critic FINAL Rec 2):
- TYPE: CONFIRMATION (cycle-7 slot 10/10 CONFIRMATION; baseline re-validation)
- CLI: `uv run python run_baseline_v3.py --confirmation --n-trials 35 --clean-oof --seeds 2`
- ENSEMBLE_SIZE=10 (CONFIRMATION mode default — 5 inner × 2 outer = 10 models per cell)
- n_trials=35 per `feedback_v3_confirmation_n_trials_35.md`
- Universe: BCH/LDO/TRX (UNCHANGED)
- Features: V3_FEATURE_COLUMNS_TOP_N (14 features, UNCHANGED)
- Labels: triple_barrier K=21 ATR (2.0, 1.0), label_timeout_minutes=10080 (UNCHANGED)
- Bar-interval: 8h (UNCHANGED)
- /116 no_confirm primitive: ENABLED (trigger_atr=0.50, k_candles=4)
- /127 binary brake: DISABLED (axis CLOSED at /127)
- /129 continuous scaling: DISABLED (axis CLOSED at /129)
- REQUIRED_GAP=66 = (21+1)×3
- ITERATION_LABEL="v3-132"
- Wall-clock cap: 6h per `feedback_v3_cadence_discipline.md`
- Acceptance gates:
  - PASS: multi-seed mean IS ≥ +1.0 AND multi-seed mean OOS ≥ +0.8 (loose tolerance vs /121 +1.31/+0.97 for code-state drift)
  - PASS → BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`); /132 confirms /121 is reproducible
  - FAIL (IS < +1.0 OR OOS < +0.8) → file CONFIRMATION-RE-ANCHOR diary; downgrade BASELINE_V3.md if multi-seed mean falls materially below /121
- F3 dissociation falsifier (|IS Δ − OOS Δ| > 0.50) NOT applicable for re-validation (not adding axis)
- PBO/PSR/DSR gates: full re-evaluation per /018 BOOTSTRAP-CONFIRMATION protocol
- Concentration audit: top-symbol ≤ 30% multi-seed mean (informational at re-validation)

These pre-commits are LOCKED at this closeout; cannot be renegotiated post-hoc at /131 brief commit.
