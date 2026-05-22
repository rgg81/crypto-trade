# iter-v3/128 — Cycle-7 slot 7 — EXPLORATION-NEGATIVE-catastrophic / WILD 6-symbol sector-pure L1 universe (ATOM/RUNE/AVAX/HBAR/ICP/ALGO) at 8h with rolling-endpoint methodology fix; universe-axis CLOSED at 9/9; Optuna-trajectory-shift channel extended to UNIVERSE axis; F6 instrumentation gap 4th recurrence

**Date**: 2026-05-21
**Type**: EXPLORATION (cycle-7 slot 7 of 10; WILD axis class — UNIVERSE substitution + cardinality expansion + sector-pure composition + rolling-endpoint methodology; HIGH-RISK posture pre-declared)
**Axis**: WHOLESALE V3_MODELS replacement BCH/LDO/TRX → ATOM+RUNE+AVAX+HBAR+ICP+ALGO + cardinality-conditional REQUIRED_GAP override (66→132) + /127 drawdown brake REVERT (True→False)
**Verdict**: EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `8d05d4e`
**Classification**: NEGATIVE-catastrophic — Section 8 first-match Criterion 1 (PUBLIC anchor): IS Sharpe **-0.4219** < +0.91 threshold → FIRES with IS Δ **-1.7327** (4.3× the magnitude of the catastrophic −0.40 threshold; the largest IS Δ deterioration in cycle-7). REGIME-MISMATCH reclassification REJECTED on five independent methodological grounds. /116-style PROMISING-MECHANICAL override NOT REACHED (pre-empted by Criterion 1 first-match-wins).
**BASELINE_V3.md**: UNCHANGED (/121 canonical at `v0.v3-121`)

## 1. What was done

WHOLESALE replacement of the V3_MODELS tuple from the /121-canonical (BCHUSDT, LDOUSDT, TRXUSDT) to a 6-symbol sector-pure L1 universe (ATOMUSDT, RUNEUSDT, AVAXUSDT, HBARUSDT, ICPUSDT, ALGOUSDT). Cardinality expansion 3→6 + cardinality-conditional REQUIRED_GAP override (66→132 = (21+1)×6 enforced runner-local at the CV-call site). /127 per-symbol drawdown brake REVERTED to disabled (axis CLOSED at /127 closeout). All other architecture bit-identical to /121: 14-feature V3_FEATURE_COLUMNS_TOP_N, +2/−1 ATR triple-barrier K=21, /116 no_confirm primitive (trigger_atr=0.50, k_candles=4), 7-gate RiskV2 stack, ENSEMBLE_SIZE=3 (EXPLORATION), n_trials=35, single outer seed=42, 8h bar interval.

First cycle-7 EXPLORATION under the **WILD axis creativity HARD MANDATE** per `feedback_v3_qr_axis_creativity_mandate.md` (2026-05-21 user push-back rejecting the cycle-7 "axis exhausted" narrative). The brief combined four structural levers (NEW universe × NEW cardinality × sector-pure L1 composition × rolling-endpoint methodology fix). NEW-feature axes FORBIDDEN at /127+ per `feedback_v3_eda_methodology_falsified.md` — /128 is a UNIVERSE axis (not a NEW-feature axis); ban does NOT apply.

Selection rationale (QR-led EDA at `analysis/iteration_v3-128/`, commit `019fdf2`): T1 universe catalog (all 6 candidates clear 24mo IS extent G1 PASS); T2 intra-universe pairwise return correlation max |corr| = 0.041 (G2 PASS with huge margin); T3 ADF stationarity all 6 PASS (p ≤ 5.6e-22); T4 rolling-endpoint AUC across 3 IS slices (2023-Q1, 2024-Q1, 2025-Q1) — universe-pooled AUC mean = **0.495 (below 0.51 breakeven; G6 INFORMATIONAL FAIL)**; T5 per-symbol AUC stability (all 6 fail G4 < 0.05 — AUC range 0.059 to 0.165); 3/6 symbols fail G5 < 5 top-3 rank shift (ATOM/HBAR/ICP). Decision: **GO under HIGH-RISK posture** per PRIME DIRECTIVE (brief + backtest; NO EDA-kill).

The rolling-endpoint methodology fix is the FIRST iteration to operationalize per `feedback_v3_eda_methodology_falsified.md` mandate point 6 (HIGH-RISK posture pre-declared in Section 6 + Section 7 modal expectation distribution; NEGATIVE-class prior = 60% honest weighting).

Commit chain: EDA `019fdf2` → brief `2bea557` → setup `0469665` (V3_MODELS WHOLESALE replacement + REQUIRED_GAP cardinality-conditional override) → preflight fix `10a689d` (process_symbol_v3 skips multifreq_v3_24h when 24h parquet absent + E501 cleanups) → engineering report `6d8c2ff` → Critic PRELIMINARY `dba7e0b` → QR response `2af30c4` → Critic FINAL `8d05d4e`. Wall-clock 1.70h (within 2h EXPLORATION cap; cardinality 6 added ~1.0h overhead vs cardinality-3 EXPLORATIONs).

Files changed: `run_baseline_v3.py` (V3_MODELS tuple replacement + ITERATION_LABEL "v3-128" + `_canonical_v059` accretion guard update + `_verify_label_leakage_gap` cardinality-conditional override at CV-call site + `_verify_feature_columns` symbol-loop refresh + multifreq_v3_24h skip for absent 24h parquets). ZERO changes to `src/crypto_trade/strategies/ml/risk_v2.py`, ZERO changes to `src/crypto_trade/features_v3/`. ZERO new features added in /128.

## 2. Results

| Metric | /121 BASELINE (multi-seed) | /128 (3-seed EXPLORATION) | Δ vs /121 |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.3108 | **-0.4219** | **-1.7327** |
| OOS monthly Sharpe | +0.9682 | **+2.1354** | **+1.1672** (all-time v3 OOS record) |
| IS daily Sharpe | 3.1180 | -0.7163 | -3.83 |
| OOS daily Sharpe | 2.3979 | +2.2877 | -0.11 |
| IS MaxDD | 26.38% | **154.68%** (wpnl-accounting artifact at 6-symbol simultaneous SL cascade) | +128.3pp |
| OOS MaxDD | 25.70% | 29.14% | +3.44pp |
| OOS/IS Sharpe ratio | 0.7386 | -5.0614 (sign-flipped; meaningless under IS negative) | — |
| Profit Factor IS | 1.6019 | 0.9153 | -0.69 |
| Profit Factor OOS | 1.3869 | 1.3415 | -0.05 |
| IS trades | 173 | 399 | +226 (cardinality scaling) |
| OOS trades | 98 | 163 | +65 (clears 130 floor) |
| PSR | 1.0 | 1.0 | 0.000 (PASS) |
| PBO mean | 0.1278 | 0.0992 | -0.029 (PASS) |
| **frac_positive_paths** | 0.6444 | **0.4444** | **-0.20 (FAIL at 0.55 floor)** — bimodal CPCV distribution (6 paths above +1.7; majority clustered negative) |
| DSR | 0.0 | 0.0 (EXPLORATION informational) | — |

**Anchor deltas (ADJUSTED IS ≈ +1.06 / OOS ≈ +0.85):**
- IS adj-Δ = **−1.4819**
- OOS adj-Δ = **+1.2854**
- Dissociation |IS adj-Δ − OOS adj-Δ| = **2.7673** (5.5× the F3 threshold of 0.50 — **the largest in v3 history**)

Per-symbol IS attribution (from `in_sample/per_symbol.csv`):
- ATOMUSDT: 68 IS trades, 44.1% WR, net PnL **+72.48 wpnl** (sole IS survivor; +56.2% of total)
- AVAXUSDT: 77 IS trades, 33.8% WR, net PnL −11.13 wpnl
- ICPUSDT: 57 IS trades, 36.8% WR, net PnL −2.68 wpnl
- HBARUSDT: 54 IS trades, 31.5% WR, net PnL −39.84 wpnl
- RUNEUSDT: 79 IS trades, 30.4% WR, net PnL −37.34 wpnl
- ALGOUSDT: 64 IS trades, **25.0% WR**, net PnL **−110.52 wpnl** (the primary IS casualty; 85.7% of total drag)

Per-symbol OOS attribution (from `out_of_sample/per_symbol.csv`):
- ICPUSDT: 24 OOS trades, 54.2% WR, net PnL +35.34 wpnl (28.5% of total — top concentration; F7 < 40% PASS)
- AVAXUSDT: 33 OOS trades, 45.5% WR, net PnL +30.75 wpnl
- ATOMUSDT: 28 OOS trades, 39.3% WR, net PnL +19.73 wpnl
- HBARUSDT: 23 OOS trades, 43.5% WR, net PnL +19.11 wpnl
- ALGOUSDT: 27 OOS trades, 37.0% WR, net PnL +15.30 wpnl
- RUNEUSDT: 28 OOS trades, 35.7% WR, net PnL +3.97 wpnl

**OOS lift is genuinely broad-based**: all 6 symbols OOS-positive (6/6 PASS); top OOS concentration ICP 28.5% (below 40% F7 threshold); broad cohort participation rather than single-symbol carrier. F1+F2+F3+F5 all fire; F4+F7 PASS; F6 INDETERMINATE (instrumentation gap).

## 3. Falsifier verdicts

Section 8 first-match-wins decision tree pre-registered at brief commit time (`2bea557`):

| Falsifier | Threshold | Observed | Fires? |
|---|---|---|---|
| **F1 IS band** | [0.66, 1.36] | **−0.4219** | YES (lower-bound; magnitude 4.3× catastrophic threshold) |
| F2 OOS band | [0.47, 1.27] | **+2.1354** | YES (upper-bound; +0.87 above ceiling) |
| **F3 Dissociation** | < 0.50 | **2.7673** (5.5× threshold; **largest in v3 history**) | YES |
| F4 Trade-rate (informational) | ≥130 OOS | 163 OOS | PASS |
| **F5 Per-symbol cascade** | ≥3/6 IS-negative | **5/6 IS-negative** (only ATOM survives) | YES (large margin) |
| F6 EDA-vs-runner methodology validation | ≥3/6 production WF AUC delta >0.05 vs EDA T4 2025-Q1 slice | **INSTRUMENTATION GAP** (run.log missing 4th recurrence; per-symbol AUC NOT persisted in committed artifacts) | INDETERMINATE |
| F7 Top-symbol cap | < 40% OOS | ICPUSDT 28.5% | PASS |

Section 8 first-match-wins fires at **Criterion 1 (NEGATIVE-catastrophic)** on F1 IS-leg failure. Criterion 6 (SUSPICIOUS-OOS-DOMINANT) WOULD fire on dissociation 2.77 >> 0.50 if Criterion 1 had not pre-empted it. The pre-emption is structurally correct: the decision tree was DESIGNED to prevent OOS regime-favorable evidence from overriding IS catastrophe per `feedback_v3_per_symbol_lifts_oos_breaks_is.md` discipline.

## 4. Mechanistic explanation

### 4.1 The IS catastrophe — regime asymmetry + ALGOUSDT systematic LONG-direction failure

The IS losses concentrate in the 2023H2–2025Q1 altcoin bear-chop regime (worst months 2024-04 −71.01, 2024-01 −46.90, 2023-11 −39.79, 2024-11 −32.67, 2023-10 −26.84). Direction analysis in catastrophic months reveals the model going LONG into bear regimes (2024-04, 2024-01) and SHORT into recovery bounces (2023-11, 2024-11). The 24-month rolling IS training window learns from the 2022 altcoin bear (LUNA/FTX produced clean directional signals in the older windows: 2022-05 +4.17, 2022-11 +22.66) but those learnings fail in the 2023H2–2025Q1 chop regime where directional signals decay.

**ALGOUSDT dominates the IS drag**: 28 LONG trades at WR 7.1% (−118.89 cumulative); 36 SHORT trades modestly profitable (+8.37). This is a near-total LONG-signal failure that persists across the full IS window (not regime-localized). The /121 14-feature stack driving ALGO LONG in chop/sideways regimes systematically collects stop-losses. ALGO IS WR 25.0% across the full 64-trade IS extent is the load-bearing falsifier for the "EDA prediction validated at universe level" framing — the rolling-endpoint EDA predicted G5 PASS for ALGO (rank shift = 4) but ALGO was the worst per-symbol IS casualty by an order of magnitude.

**ALGO LONG-direction failure breaks the regime-localized framing**: if IS catastrophe were purely regime-localized, ALGO would show high WR in 2022 and 2024 bull months — it does not. The bear-chop framing fits portfolio monthly distribution but does NOT explain ALGO's full-window LONG-direction failure. This is the structural basis for the Critic's REGIME-MISMATCH rejection (Round 2 adjudication grounds #2).

### 4.2 The OOS record — regime-favorable 2025-2026 altcoin L1 bull

The 2025-2026 OOS window (2025-04 to 2026-05) captures a strong L1 directional regime (altcoin recovery/bull phase post-March 2025). The model generates directionally correct signals in this trending regime: 11-month positive streak (Apr 2025 – Nov 2025; only loss month 2025-11 at −8.93); Jan 2026+ continued positive (high-WR months Sep/Oct/Apr/May 2026 at WR 66.7%–100%). The OOS regime is genuinely favorable for the L1 directional hypothesis. All 6 symbols OOS-positive; top concentration ICP 28.5% well below 40% F7 threshold; this is broad-cohort OOS lift rather than single-symbol carrier.

This is exactly the F3 SUSPICIOUS-OOS-DOMINANT signature pre-empted by Criterion 1 first-match-wins. The OOS record is regime-favorable evidence, NOT generalization evidence — the IS catastrophe demonstrates the strategy is not robust across regimes. The decision-tree DESIGN is methodologically correct: an IS catastrophe with an OOS record cannot be classified PROMISING under v3 methodology.

### 4.3 Why the rolling-endpoint methodology fix's universe-level prediction was directionally validated but per-symbol gates failed

The EDA universe-pooled AUC of 0.495 predicted HIGH-RISK posture (Section 6 brief). Production produced IS monthly Sharpe **−0.4219**, the worst observation in cycle-7. The DIRECTIONAL prediction (HIGH-RISK universe → IS catastrophe risk) was VALIDATED ex-post. However:

- G5 PASS (rank shift = 4 for ALGO) did NOT predict the worst per-symbol IS casualty. The G5 univariate gate's predictive value for per-symbol PnL is **falsified at /128**.
- 3/6 symbols (ATOM/HBAR/ICP) flagged G5 FAIL realized **bimodally**: ATOM diverged HIGH (+72.48 sole survivor), HBAR diverged LOW (−39.84), ICP diverged near-zero (−2.68). The rank-shift instability gate did not cleanly predict the direction of per-symbol attribution.

The methodology-fix's UNIVERSE-LEVEL directional prediction is VALIDATED; the PER-SYMBOL gates (G4, G5) do NOT cleanly map to per-symbol PnL. The methodology fix should be considered **tentatively-validated-at-universe-level only, pending F6 instrumentation in /129+**.

### 4.4 Optuna-trajectory-shift channel extension — UNIVERSE axis is the second occurrence

/127 established the Optuna-trajectory-shift finding for RISK-PRIMITIVE axes (`feedback_v3_optuna_trajectory_shift_finding.md`). /128 extends the finding's scope to UNIVERSE axes. The mechanism is the same channel:

| Channel element | /127 (risk-primitive axis) | /128 (universe axis) |
|---|---|---|
| Pre-Optuna constraint | `enable_per_symbol_drawdown_brake=True` | `V3_MODELS = (ATOM, RUNE, AVAX, HBAR, ICP, ALGO)` |
| Optuna re-training | Each WF month, search space conditioned on brake gating downstream | Each WF month, search space conditioned on 6 new symbols' label/return/feature distributions |
| EDA-on-frozen-substrate prediction | ORACLE +0.0348 IS Δ on /121 roster | Universe-pooled AUC 0.495 → HIGH-RISK posture |
| Production observation | IS Δ −0.5242 (15× ORACLE magnitude, sign-flipped) | IS Δ −1.4819 vs ADJUSTED anchor (catastrophic) |
| Pattern | Frozen-roster ≠ Optuna-retrained-with-constraint | Rolling-endpoint EDA on independent IS slices ≠ Optuna-retrained-with-new-universe |

Both cases share the structural property that **the Optuna objective function is conditional on the architectural change**. The bimodal CPCV path distribution at /128 (frac_pos 0.4444; 6 paths above +1.7; majority clustered negative) is the cross-section evidence of regime-asymmetric Optuna re-convergence. The Optuna search at each WF month finds solutions optimal for that month's training-window data; in chop they are SL-trapped on 5 of 6 symbols, in trend they are directionally aligned. This is the same trajectory-shift dynamic as /127 just sampled at WF-month granularity rather than binary-gate granularity.

**Binding methodology requirement for /129+**: briefs Section 2 MUST include closed-loop Optuna-re-training simulators for ANY axis changing the Optuna training-objective domain (RISK-PRIMITIVE, UNIVERSE, LABEL-MODE, FEATURE-SET COMPOSITION, ENSEMBLE_SIZE / n_trials / bar-interval changes). Frozen-EDA point estimates are insufficient. The simulator must vary Optuna seed + training-window-start across N ≥ 10 configurations to capture the trajectory distribution.

## 5. Process notes

### 5.1 F6 instrumentation gap — 4th recurrence (/124/125/127/128)

`run.log` missing from `reports-v3/iteration_v3-128/`. The methodology-fix PRIMARY validation gate (F6: per-symbol production walk-forward AUC at end-of-IS vs EDA T4 2025-Q1 slice AUC) is unadjudicated because the runner does not persist per-symbol per-WF-month classifier AUC anywhere in committed artifacts. Available proxies (per-symbol IS WR, per-symbol IS net_pnl_pct) are downstream of model output × triple-barrier × gates and cannot reconstruct the AUC ranking.

This is the **4-occurrence pattern** (/124/125/127/128) for run.log missing. Per Critic Recommendation 1 for /129+: persist run.log + per-symbol per-WF-month classifier AUC as required runner outputs. Add per-symbol AUC table generation + run.log persistence to runner's required output schema; add as smoke-test assertion in Section 9 of /129+ briefs. New feedback memory `feedback_v3_instrumentation_run_log_missing.md` filed at this closeout.

### 5.2 REGIME-MISMATCH reclassification REJECTED on five grounds

QR raised "EXPLORATION-REGIME-MISMATCH" as a possible 10th classification. Critic rejected on five independent methodological grounds; QR accepted in Round 2 response. Grounds:

1. Section 8 decision tree LOCKED at brief commit time per `feedback_v3_axis_saturation_predictor.md` + `feedback_v3_lr_pf_methodology.md`. Adding a 10th classification post-hoc IS the post-hoc reclassification anti-pattern.
2. IS catastrophe is NOT cleanly regime-localized (ALGO WR 25.0% across full IS window 2020-2025).
3. "Deferred-merge-pending-IS-update" has no precedent and operationally requires OOS_CUTOFF_DATE to be movable (sacred constant immutable per `feedback_no_cheating.md`).
4. /127 Optuna-trajectory-shift finding GENERALIZES (Clarification 4).
5. OOS record is single-regime-favorable; Section 8 first-match-wins is DESIGNED to pre-empt exactly this pattern at Criterion 1 IS-leg failure.

The OOS record + broad-based + trade-rate-floor-cleared are real positive signals, BUT they are not sufficient on their own to override the IS catastrophe per pre-registered methodology. REGIME-MISMATCH would be post-hoc rule change.

### 5.3 Universe-axis CLOSED at 9/9 NEGATIVE in cycle-7

Cycle-7 universe-substitution attempts: **9/9 NEGATIVE** through /128. Cardinality-expansion sub-axis (sector-pure L1 at cardinality 6) was the structurally-distinct attempt; produced the largest IS catastrophe in cycle-7 (−1.73 IS Δ vs /121). The /125 "cohort-shaped architecture" finding extends to UNIVERSE-axis class as a whole: the /121 14-feature stack is not transferable across universe-substitutions at any cardinality without architecture retuning.

/128 broad-based OOS lift (all 6 symbols positive, ICP 28.5% concentration) is structurally noteworthy — recorded as **"L1 universe is regime-asymmetric: catastrophic in 2023H2–2025Q1 chop, broad-based-positive in 2025Q2–2026Q2 trend"** rather than "universe is dead." Cycle-8+ regime-conditional architecture may revisit. Cycle-7 universe-axis closure verdict stands.

### 5.4 Cycle-7 catalog state at /128 closeout

Cycle-7 catalog (7 of 10 EXPLORATIONs complete; 3 remaining slots):

| Slot | Iter | Axis | IS Δ | OOS Δ | Verdict |
|---:|---|---|---:|---:|---|
| 1 | /122 | cross-asset (ETH OHLCV eth_ret_3d) | -0.34 | +0.20 | NEGATIVE-INERT |
| 2 | /123 | cross-asset (eth_vs_sym_rv_50) | -1.73 | +0.79 | NEGATIVE-catastrophic |
| 3 | /124 | longer-cadence labels K=63 + sqrt(3) ATR | -0.87 | -0.94 | NEGATIVE-catastrophic |
| 4 | /125 | WILD V3_MODELS ATOM/RUNE/UNI | -1.25 | -0.86 | NEGATIVE-catastrophic |
| 5 | /126 | multi-frequency d24_ret_autocorr_lag1_50 | -1.21 | -1.08 | NEGATIVE-catastrophic |
| 6 | /127 | per-symbol drawdown brake (binary kill) | -0.52 | +0.03 | NEGATIVE-catastrophic |
| **7** | **/128** | **WILD 6-symbol sector-pure L1 universe (ATOM/RUNE/AVAX/HBAR/ICP/ALGO)** | **-1.73** | **+1.17** | **NEGATIVE-catastrophic** |
| 8 | /129 | continuous size scaling at drawdown WITH closed-loop Optuna-retraining simulator | — | — | (pending) |
| 9 | /130 | TBD | — | — | (pending) |
| 10 | /131 | TBD | — | — | (pending) |

**6/7 catastrophic; 1/7 INERT; 0/7 PROMISING.** Closed axes through /128: cross-asset OHLCV (2 attempts), longer-cadence labels (1), universe substitution (cardinality-3 + cardinality-6, 2 attempts including /125+/128 here), multi-frequency features (1, plus EDA methodology FALSIFIED at /126), RISK-PRIMITIVE binary kill (1). The /129+ axis menu narrows to: continuous risk-primitive (with closed-loop simulator), multi-offset/cadence variants (12h or 4h base candles), or cycle-7-early-close (would collide with strict 10:1 cadence rule).

### 5.5 Optuna-trajectory-shift channel extension impact on /129 brief

Per Critic Recommendation 2 (FINAL `8d05d4e`): /129 brief Section 2 MUST include closed-loop Optuna-re-training simulator for chosen axis. This binds for /129+ regardless of axis class. The /127 + /128 evidence supports updating `feedback_v3_optuna_trajectory_shift_finding.md` to scope ALL axes that change the Optuna training-objective domain (not just RISK-PRIMITIVE). The /129 axis (continuous position-size scaling at drawdown — re-take of /127 PRIMARY under new methodology) operationalizes this.

## 6. Lessons

1. **The rolling-endpoint EDA methodology fix is partially-validated at the universe level but NOT at the per-symbol level.** Universe-pooled AUC 0.495 directionally predicted HIGH-RISK; production validated. Per-symbol G4 + G5 gates did NOT cleanly map to per-symbol PnL — ALGO G5 PASS was the worst per-symbol IS casualty; G5 FAIL symbols realized bimodally (ATOM HIGH, HBAR LOW, ICP near-zero). Per-symbol gates need refinement before they can carry production prediction weight.

2. **Cardinality-expansion under sector-pure composition does NOT rescue universe-substitution.** /125 same-cardinality (3) + /128 cardinality-6 + sector-pure L1 are TWO distinct sub-axes; both NEGATIVE-catastrophic. The "cohort-shaped architecture" finding from /125 extends to universe-axis-class-general — the /121 14-feature stack is BCH/LDO/TRX-tuned and does not transfer.

3. **F3 dissociation 2.77 (largest in v3 history) is structurally consistent with universe-axis Optuna re-convergence under regime-asymmetric IS/OOS data.** The bimodal CPCV path distribution (frac_pos 0.444; 6 paths above +1.7; majority clustered negative) is the cross-section evidence. The strategy is not generalization-capable across regimes; the OOS record is regime-favorable evidence rather than transferable edge.

4. **The Optuna-trajectory-shift channel generalizes across axis classes** (/127 RISK-PRIMITIVE + /128 UNIVERSE = 2 occurrences). The mechanism: EDA-on-frozen-substrate gives systematically biased predictions for any axis that changes the Optuna training-objective domain. Closed-loop Optuna-re-training simulators required as pre-flight gate for /129+ regardless of axis class.

5. **Instrumentation gap is a CYCLE-7 process risk.** 4-occurrence pattern (/124/125/127/128) for run.log missing. The F6 methodology-fix validation gate cannot be evaluated post-hoc; this blocks PRIMARY methodology iteration. Must fix at /129+ via runner output schema + smoke-test assertion.

6. **Broad-based OOS lift WITHOUT IS support remains pre-empted by Section 8 first-match-wins.** Even though all 6 symbols OOS-positive and top concentration 28.5% (well below 40% F7), the IS catastrophe takes precedence per pre-registered methodology. The pre-emption is structurally correct — `feedback_v3_per_symbol_lifts_oos_breaks_is.md` discipline applies to universe-substitutions just as it applies to per-symbol customizations.

7. **The "L1 universe is regime-asymmetric" observation is cycle-8 axis-selection input, not cycle-7 reopening.** Cataloged as such; preserves possibility that regime-conditional architecture may revisit this universe in a future cycle without contradicting the cycle-7 closure verdict.

## 7. Decision

**NO MERGE.** EXPLORATION-NEGATIVE-catastrophic per Critic FINAL `8d05d4e`. /128 is the 7th cycle-7 EXPLORATION; universe-axis class CLOSED at 9/9 NEGATIVE; Optuna-trajectory-shift channel extended from RISK-PRIMITIVE to UNIVERSE axis class. BASELINE_V3.md UNCHANGED at /121 canonical (`v0.v3-121`). Tag `v0.v3-128` set on the closeout commit.

## 8. Pre-Commit for iter-v3/129

Per `feedback_v3_axis_selection_quant_discipline.md`, the orchestrator + QR adjudicate axis for /129. Cycle-7 axis menu at /128 closeout has CLOSED axes through /128: cross-asset OHLCV (cycle-7 methodology block), longer-cadence labels, universe-substitution (any cardinality), multi-frequency features (EDA methodology FALSIFIED), RISK-PRIMITIVE binary kill, knob-tuning saturated. Remaining viable axes:

- **PRIMARY**: continuous position-size scaling at drawdown WITH closed-loop Optuna-re-training simulator (re-take of /127 PRIMARY under the new methodology binding). This is the QR's recommended /129 axis per the QR response + Critic Recommendation 3 PRIMARY. Continuous version preserves Optuna gradient — trades not deleted from training; their contribution is dampened proportionally to drawdown severity. Brief MUST include closed-loop Optuna-re-training simulator distribution (N ≥ 10 seeds × 3 training-window-starts) per `feedback_v3_optuna_trajectory_shift_finding.md` extended scope. **Pre-flight gate**: Optuna-trajectory distribution must show ≥60% of seeds produce IS Sharpe ≥ +0.91 (the /121 BASELINE re-validation under the new constraint).

- **SECONDARY**: multi-offset 12h or 4h base candles (frequency-axis variants not yet tested; requires closed-loop simulator per Optuna-trajectory-shift extension).

- **TERTIARY**: cycle-7 close-early with /129 = CONFIRMATION re-validating /121. Collides with `feedback_v3_strict_10_to_1_cadence.md` strict 10:1 sequencing rule. Orchestrator must adjudicate whether 9/9 NEGATIVE-universe + closed-axis exhaustion warrants cadence-rule override.

**Adjudicated /129 axis**: PRIMARY (continuous position-size scaling at drawdown with closed-loop Optuna-re-training simulator). This satisfies the Critic FINAL Recommendation 3 PRIMARY and respects the strict 10:1 cadence rule.

**Bound rules for /129 brief**:
- Section 2 MUST include closed-loop Optuna-re-training sensitivity simulator (vary outer-seed × training-window-start across N ≥ 10 configurations; report DISTRIBUTION of IS Sharpe outcomes, not point estimate).
- Pre-flight gate: ≥60% of simulator seeds produce IS Sharpe ≥ +0.91 (/121 re-validation under the new constraint).
- Brief Section 9 smoke-test MUST include assertion that `run.log` persists at `reports-v3/iteration_v3-129/run.log` and per-symbol per-WF-month classifier AUC is persisted in committed artifacts (instrumentation gap fix).
- F3 dissociation falsifier remains binding (any |IS Δ − OOS Δ| > 0.50 triggers SUSPICIOUS-OOS-DOMINANT pre-emption logic).
- Continuous size-multiplier replaces /127's binary kill; M=21 time-override preserved for deadlock-impossibility.
- F6-equivalent methodology-validation gate must be evaluable from committed artifacts (per-symbol production WF AUC table generation in runner).
- Cycle-7 slot 8/10 designation explicit in Section 0.5.
- Anchor: /121 multi-seed CONFIRMATION-MERGE BASELINE (PUBLIC IS +1.3108 / OOS +0.9682); ADJUSTED IS ≈ +1.06 / OOS ≈ +0.85.

These pre-commits are LOCKED at this closeout; cannot be renegotiated post-hoc at /129 brief commit.
