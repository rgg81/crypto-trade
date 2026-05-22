# Phase 7.5 Critic Review — iter-v3/120

OVERALL: CONFIRMATION-NO-MERGE — pre-committed F3 (sister-redistribution / catalyst-without-contribution) FIRES + F4 (IS regime-cost floor +0.79) FAILS; BOTH-must-improve breaks on IS leg (+0.7293 < /059 +1.0894); all-time v3 OOS record (+1.6946) noted but not merged.

## Iteration Type (from Brief Section 0.5)
TYPE: CYCLE 6 CONFIRMATION mandatory; first multi-mechanism bundle in v3 history; 10/10 EXPLORATIONs /110–/119 completed; bundles 2 mechanical primitives (Component A: no_confirm exit overlay at trigger_atr=0.50, k_candles=4 from /116; Component B: ret5d_signed_tbi engineered feature at index-14 from /119); 10-seed unified ensemble, n_trials=35.

## QR Response Considered (Round 2)

1. **Q1 Attribution gap → (b) Authorize iter-v3/121-METHODOLOGY**: QR concurs with Critic preliminary one-line recommendation. Three artifact-grounded reasons: (i) Component A is mechanically firing in the bundle (8 no_confirm exits / 96 OOS trades per `reports-v3/iteration_v3-120/out_of_sample/trades.csv`); (ii) /116-only-at-10-seed is the ONLY missing data point in the cycle-6 multi-seed evaluation grid; (iii) brief Section 8.4 branch 3 explicitly pre-committed "/116-only re-evaluation" as a binding outcome path. **Critic VERDICT: CONCUR.** Closing without that branch leaves a pre-committed outcome path unevaluated.

2. **Q2 F4 knife-edge → GENUINE binding-fail**: QR affirms +0.79 floor is contract; renegotiation would violate `feedback_no_cheating.md`; the IS-leg miss is mechanism-confirmed (BCH IS net_pnl_pct collapsed 69.31 pct, trade count +6 — the no_confirm channel cut BCH trades that would have recovered, exactly the regime-cost mechanism F4 was designed to gate on). **Critic VERDICT: CONCUR.** Pre-commitment is binding contract.

3. **Q3 F3 mechanism scope → (a) Interaction effect REAL**: QR provides Jaccard set-comparison on committed trade rosters: /120 vs /116-alone Jaccard = 0.48 (66/96 shared, 30 trades unique to bundle); /120 vs /119-alone Jaccard = 0.55. Bundle is NOT a near-duplicate of /116-alone — Component B reshaped the loss surface; Component A's exit overlay operated on a different entry distribution. **Critic VERDICT: CONCUR on mechanism diagnosis (genuine interaction, not cannibal-only), DECLINE on bundle-retention implication.** F3 is an allocation-accounting gate (split-budget catalyst-without-contribution by importance-share thresholds), NOT an OOS-performance gate. Both legs hold cleanly at multi-seed (regime_momentum_signed_5d 171.9 vs anchor 506.67 = −66.1%, below 253.34 threshold; C6 portfolio share 2.72% < 5%). F3 fires REGARDLESS of whether the OOS lift is interaction-driven or cannibal-only; the mechanism diagnosis matters for cycle-7 axis selection, not for /120 verdict. The interaction-effect finding is important context for the /121-METHODOLOGY design (it is the disciplined isolation that resolves whether the 30 unique bundle trades are interaction effect or multi-seed superset artifact).

4. **Q4 BASELINE_V3.md → UNCHANGED at /059**: QR confirms no exception for all-time OOS record. Three binding rules: BOTH-must-improve gate (Δ IS −0.3601 from /059 +1.0894); brief Section 8.3 pre-registered no-exception clause; F4 independent IS-leg breach. /039 precedent (OOS +1.47 / IS −0.08 vs baseline +0.51/+0.51 → NO MERGE) is structurally identical to /120 (large OOS gain, IS regression). **Critic VERDICT: CONCUR.** Doubly-binding; no precedent of OOS-only exception in v3 history.

5. **Q5 Cycle-7 framing → (b) /121-METHODOLOGY first, then /122 cycle-7 EXPLORATION axis-1**: QR commits to (i) /121-METHODOLOGY (Component A 10-seed isolation, NOT counted toward cycle-7 cadence — analogous to /018 BOOTSTRAP precedent); (ii) /122 = cycle-7 EXPLORATION axis-1 from /119 diary §8.2 candidate menu, QR-selected per `feedback_v3_axis_selection_quant_discipline.md`; (iii) standard 10/10 + 1 CONFIRMATION cadence resumes from /122. **Critic VERDICT: CONCUR.** Premature axis selection without isolating Component A risks running cycle-7 on a baseline that is wrong by a Component-A-shaped term.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

No /120-specific feature/backtest code introduced. Bundle is the union of components individually audited PASS at /116 (Component A `no_confirm_arm_time = open_time + k_candles * interval_ms` and `no_confirm_threshold_price = entry_price * (1.0 ± trigger_atr * sl_pct)` both knowable strictly at trade entry) and /119 (Component B `ret_5d = log_close - log_close.shift(15)` and `taker_buy_imbalance_20.shift(1).rolling(20).mean()` both past-only by construction). The /120 setup commit added ZERO feature/backtest code (only runner-state flag flips + assertions). PASS.

### Check 2 — Embargo Width: PASS

REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3. CPCV embargo=27 ≈ 1% of 2742-candle IS window. CPCV n_paths=45 unchanged from /059. Walk-forward POST-FIX at `e149e9d` carry-forward. PASS.

### Check 3 — Multiple-Testing Correction: SPLIT VERDICT (PBO/PSR/frac_positive_paths PASS; DSR informational FAIL)

- DSR = 0.0 — raw threshold FAIL, but structural artifact inherited from /059 per `feedback_v3_dsr_mode_artifact.md`.
- PBO = 0.0957 < 0.40: PASS.
- PSR = 1.0 > 0.95: PASS.
- frac_positive_paths = 0.6444 ≥ 0.55: PASS (29 of 45 CPCV paths positive).
- n_trials = 1050 (35 × 3 × 10) matches /059. n_eff = 19.

Mechanically PASS on PBO + PSR + frac_positive_paths. DSR informational only.

### Check 4 — IC Correlation Between Feature Families: PASS

15×15 IC matrix; high pairwise ICs pre-registered under Category-2 algebraic-sister carve-out: regime_momentum_signed_5d × vwap_dev_20 = +0.7642; ret5d_signed_tbi × regime_momentum_signed_5d = −0.7229 (algebraic sister via shared ret_5d); ret5d_signed_tbi × vwap_dev_20 = −0.5668. Max non-carve-out pair: regime_momentum_signed_5d × sym_vs_btc_ret_7d = +0.6189 (< 0.70). Carve-out replacement gate (importance ≥ 30): C6 per-symbol importance BCH 36.4, LDO 34.7, TRX 57.5 — all ≥ 30. PASS.

### Check 5 — ADF Stationarity: PASS

C6 stationary at IS-end month across all 3 symbols (BCH ADF=−7.753, LDO=−8.128, TRX=−10.295; all p=0.0). /059 14-feature stack carries forward unchanged. PASS.

### Check 6 — Pareto Dominance: PASS (via frac_positive_paths gate)

Per `feedback_v3_unified_10seed_baseline.md`, Gate 10 per-seed Pareto replaced at /059+ by `cpcv_frac_positive_paths_gate_pass`. Observed 0.6444 PASS. CPCV path Sharpe distribution: min=−1.318, Q25=−0.243, Q50=+0.335, Q75=+0.838, max=+1.880. PASS.

### Check 7 — Reproducibility: PASS

Setup SHA `294ac0e` stamped. Engineering report SHA `55f2246`. Brief SHA `26d99f2`. Gate SHA `1145c30`. ENSEMBLE_SEEDS pinned. `feature_columns=_feature_columns` explicit. Pre-flight bundle-state assertions fire 4 distinct guards. Wall-clock 3.14h within 6h cap. PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Bundle state implemented per Brief Section 1; pre-flight assertions verify joint state. No scope creep. 7-gate RiskV2 stack + training_months=24 + OOS_CUTOFF_DATE=2025-03-24 + ENSEMBLE_SIZE=10 + n_trials=35 all unchanged from /059. PASS.

## Falsifier Status Summary (binding, pre-committed at brief Section 4)

| F# | Status | Observed | Threshold |
|---|---|---|---|
| F1 stacking-linearity | PASS | OOS +1.6946 | ≥ +1.0089 |
| F2 TRX-concentration | PASS | TRX 18.79% of positive total | ≤ 65% (50% flag) |
| F3 sister-redistribution | **FIRES** | regime_momentum 171.9 < 253.34 AND C6 share 2.72% < 5% (BOTH legs hold) | NOT BOTH |
| F4 IS regime-cost floor | **FAILS** | IS +0.7293 < +0.79 | ≥ +0.79 |
| F5 per-symbol cascade | PASS | 3/3 symbols positive Δ vs /059 | ≥ 2/3 |

**BOTH-must-improve gate**: IS +0.7293 < /059 IS +1.0894 (Δ −0.3601) → BASELINE_V3.md does NOT update. Doubly-binding alongside F4.

## Substantive Classification — CONFIRMATION-NO-MERGE

Per brief Section 8.4 first-match-wins decision tree:

1. **F3 FIRES → DROP Component B** per pre-committed branch 3. The Q3 interaction-effect finding (Jaccard 0.48 with /116-alone; 30 trades unique) refines mechanism diagnosis but does NOT cure F3 (allocation-accounting gate). Both legs hold cleanly at multi-seed with remarkable numerical stability vs /119 single-seed (regime_mom −66.1% vs −65.3%; C6 share 2.72% vs 2.6%).

2. **F4 FAILS → NO-MERGE on IS leg.** IS +0.7293 < +0.79 floor by 0.0607. Pre-commitment is contract. Mechanism-confirmed (BCH IS net_pnl_pct collapsed 69.31 pct with trade count +6 — no_confirm cutting BCH trades that would have recovered). Not statistical noise.

3. **BOTH-must-improve INDEPENDENTLY confirms NO baseline update.** IS Δ −0.3601 robust to any F4-band renegotiation. No pre-registered exception exists for OOS records in v3 history.

4. **All-time v3 OOS record (+1.6946 vs prior /059 +0.5791; Δ +1.12) is a notable structural finding**, not a merge trigger. Q3 elevates this to substantively interesting — but binding F3 fires regardless.

## Recommendations for Cycle-6 Closeout + Cycle-7 Setup

1. **iter-v3/120 CONFIRMATION-NO-MERGE final.** Component B (C6) DROPPED per F3 pre-commitment, regardless of /121-METHODOLOGY outcome. Component A's standalone 10-seed value remains unevaluated; the load-bearing unknown for cycle-6 final closure.

2. **iter-v3/121-METHODOLOGY AUTHORIZED as cycle-7 BOOTSTRAP** (analogous to iter-v3/018 BOOTSTRAP precedent; NOT counted toward cycle-7 10/10 EXPLORATION cadence). Spec: identical /059 baseline runner with single change `enable_no_confirm_exit=True` (trigger_atr=0.50, k_candles=4); V3_FEATURE_COLUMNS_TOP_N reverts to /059's 14-feature set (C6 removed); --n-trials 35, no --exploration, 10-seed unified ensemble; 6h CONFIRMATION cap (estimated 3-4h). If /121 PASSES all gates including BOTH-must-improve on /059 → BASELINE_V3.md updates with Component A only (PARTIAL-MERGE RULE-layer baseline). If /121 FAILS → cycle-6 closes with 0 ingredients merged; cycle-7 axis selection proceeds from /059 unchanged.

3. **iter-v3/122 = cycle-7 EXPLORATION axis-1** from /119 diary §8.2 candidate menu (cross-asset/external feeds, longer-cadence labels, NEW model architecture, NEW symbol universe). QR-selected per `feedback_v3_axis_selection_quant_discipline.md`. Cycle-7 standard 10/10 + 1 CONFIRMATION cadence resumes from /122 anchored against whichever baseline /121-METHODOLOGY yields.

## Memory updates needed (orchestrator's responsibility)

- Add note to PROMISING-FEATURE-MECHANICAL memory file: validated at /120 multi-seed; F3 ("allocation cannibal without contribution") is the BINDING gate that catches it cleanly even when the bundle achieves all-time OOS record and the interaction effect is genuine (Jaccard 0.48 NOT near-duplicate); pre-committed F3 is the right test for future PROMISING-FEATURE-MECHANICAL candidates.
- Update `project_v3_cycle6_axis_menu.md` to note cycle 6 closed CONFIRMATION-NO-MERGE; cycle-7 starts with /121-METHODOLOGY bootstrap.

## Catalog entry

iter-v3/120 CONFIRMATION-NO-MERGE — F3 FIRES (sister-redistribution / catalyst-without-contribution: regime_momentum_signed_5d 171.9 vs threshold 253.34 AND C6 portfolio share 2.72% vs 5% threshold — BOTH legs of conjunctive gate hold cleanly at multi-seed) + F4 FAILS (IS regime-cost floor: +0.7293 < +0.79; BCH IS net_pnl_pct −69.31 pct mechanism-confirmed). BOTH-must-improve breaks on IS leg (Δ −0.3601 vs /059). All-time v3 OOS record +1.6946 recorded but not merged (no pre-registered exception). Genuine interaction effect confirmed by trade-roster Jaccard 0.48 vs /116-alone (30 trades unique to bundle) but does NOT cure F3 allocation-accounting gate. Component B DROPPED per F3 pre-commitment. Component A unevaluated standalone at 10-seed → iter-v3/121-METHODOLOGY AUTHORIZED as cycle-7 BOOTSTRAP (NOT counted toward cycle-7 cadence) to settle attribution before /122 cycle-7 EXPLORATION axis-1 selection.

## Clarifications Requested from QR — NONE
