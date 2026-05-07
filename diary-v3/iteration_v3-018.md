# Iteration iter-v3/018 — Diary

## Decision: CONFIRMATION-MERGE-BOOTSTRAP

NOT CONFIRMATION-MERGE-FULL. 6 of 10 pre-registered MERGE gates FAILED. Baseline established per `feedback_v3_iter018_baseline_bootstrap.md` one-time directive (v3 had no prior baseline).

## What Was Tested

**Hypothesis (locked in brief Section 1):** "Does iter-v3/013's single-seed IS +1.0088 / OOS +2.6970 monthly Sharpe hold under multi-seed cross-validation, with PBO < 0.4, DSR > 0.95, PSR > 0.95, multi-seed Pareto non-domination, bundle-level OOS trade count ≥ 130?"

**Spec (locked, no axis variation):**
- `--seeds 2 --n-trials 50` (per `feedback_outer_seed_cap_2_v3.md`: 5 inner × 2 outer = 10 models per cell)
- ENSEMBLE_SIZE=5 (live-prediction variance reduction inherited from v1)
- `colsample_bytree` Optuna-tuned (NOT hardcoded 1.0)
- All other strategy parameters byte-identical to iter-v3/013 baseline (13 features, ATR labeling 2.0/1.0, zscore_threshold=2.0, BTC trend ±15%, drop-MKR 3-symbol universe BCH+LDO+TRX, 7-primitive risk gate stack)

This was iter-v3/018, the **first true v3 CONFIRMATION** ever (iter-v3/008 was aborted at 4h 15min on 2026-05-06 before any CONFIRMATION cadence rules existed).

## Headline Numbers

| Metric | iter-v3/013 (single-seed) | iter-v3/018 mean (2-seed) | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | +1.0088 | **+0.3788** | -0.630 (62% reduction) |
| OOS monthly Sharpe | +2.6970 | **+0.3869** | -2.310 (86% reduction) |
| OOS MaxDD (best) | 12.47% | 27.74% | +15.27pp |
| LDO OOS WR | 80% (10 trades) | 31.2% (16 trades) | -49pp |
| Top OOS conc | LDO 65.65% | TRX 66.08% (seed 42) | symbol shifted |
| DSR | 0.0 | **0.0** | unchanged (structural) |
| PSR | 1.0 | **0.9936** | -0.0064 |
| PBO mean / max | 0.1075 / 1.00 | **0.0892 / 1.00** | mean improved |
| n_eff | 7 | **25** | +18 |

## What Worked

- **Methodology of the multi-seed run itself is clean.** All 12 standard methodology checks PASS: look-ahead audit, embargo width (REQUIRED_GAP=66 = (21+1)×3), IC correlation, ADF stationarity (all 13 features stationary at end-of-training-window for all 3 symbols), reproducibility stamp, hypothesis-implementation alignment, symbol exclusion, feature isolation, forming-candle filter, library version pinning. The failure is genuine signal weakness, NOT a pipeline defect.
- **Both Pareto seeds positive AND non-dominated.** Gate 10 PASS — seed 42 +0.2343, seed 123 +0.5394. The 13-feature stack has SOME marginal edge OOS at multi-seed scale (+0.39 mean Sharpe), it just doesn't clear the +1.0 floor. This is the methodology bright spot of iter-v3/018: the bootstrap baseline is honest-positive, not honest-zero.
- **PSR PASS at 0.9936.** The probabilistic Sharpe ratio gate is cleared; the +0.39 OOS mean is statistically distinguishable from zero at the 95th percentile.
- **OOS/IS Sharpe ratio passes both seeds individually.** Seed 42 ratio 0.5134 (bare PASS), seed 123 ratio 1.79 (substantial). The mean ~1.02 is a healthy generalization signal — what little IS edge exists, it transfers OOS.
- **TRX is the strongest OOS contributor in BOTH seeds** (+11.97 weighted_pnl seed 42; positive seed 123). Drop-MKR universe decision at iter-v3/013 retained value even at multi-seed. The architectural decision is preserved; only the headline metric is dead.
- **n_eff increased from 7 (single-seed) to 25 (multi-seed).** This is the structural gain of the multi-seed CONFIRMATION methodology: the search-space exploration is more legitimate.

## What Failed

- **Gates 1, 2: IS and OOS Sharpe floors missed by 0.62 and 0.61.** The +1.0 floor is not lift-able by this 13-feature stack at multi-seed scale. The iter-v3/013 single-seed result was a favorable lottery; the underlying expected performance is +0.38 IS / +0.39 OOS.
- **Gate 4: DSR=0.0** vs >0.95 floor. **STRUCTURAL** failure, not a code bug. At n_trials=1500 (50 trials × 5 inner × 3 symbols × 2 outer seeds), López de Prado's E[max_SR] = 3.369; observed annualized Sharpe ≈ 1.7 → DSR formula correctly returns 0.0. The gate as locked is mathematically blocked at v3's current trade volume + Optuna budget. Either (a) reformulate gate to `DSR > 0` (positive deflation), OR (b) reduce CONFIRMATION budget to `--n-trials 20` (cap n_trials_total at ~600). Brief Section 4.2 prediction "DSR in [0.85, 0.99] because n_eff > 10" was incorrect — n_eff doesn't enter the DSR formula directly; what matters is `observed_sr vs E[max_SR]`. Calibration miss.
- **Gate 5 max-aggregator: PBO max=1.0** on TRX/2022-10 and TRX/2023-01 (FTX/LUNA crash regime). 13 cells ≥ 0.4. The mean aggregator (0.0892) PASSES, but the max-aggregator FAILS. Carries forward unchanged from iter-v3/013/012 (TRX/2022-Q4 was already on the audit trail).
- **Gate 7: Top-symbol concentration FAIL.** TRX 66.08% (seed 42), 55.83% (seed 123). Multi-seed averaging did NOT compress concentration; it shifted the dominant symbol from LDO (single-seed lottery) to TRX (consistent across both seeds). Concentration is **structural to the 3-symbol universe**, not a tuning artifact.
- **Gate 8: Bundle OOS trades 102 / 79 — both below the 130 floor per seed.** "Bundle" interpretation is ambiguous; conservative reading (per-seed OOS trades) FAILS. Pooled-deduped reading (sum across seeds = 181) would PASS, but the brief specifies per-bundle.
- **Gate 9: 10-seed validation NOT TRIGGERED** (Gates 1+2 fail decisively). Open question: does the v1/v2 "10-seed pre-MERGE" rule mean (a) 10 outer seeds (contradicts v3's 2-seed cap), (b) the 10 inner models per cell (already satisfied by 2 outer × 5 inner), or (c) a separate low-cost sanity run at `--seeds 10 --n-trials 5`? QR will clarify before next CONFIRMATION attempt.
- **iter-v3/013 single-seed lottery CONFIRMED.** LDO 80% WR / +40.6 weighted_pnl @ iter-v3/013 → 31.2% WR / -10.24 weighted_pnl @ iter-v3/018. The favorable Optuna path that produced the 80% WR at n_trials=10 was not reproduced under fuller search at n_trials=50. **Per-symbol architecture means MKR's removal at iter-v3/013 was independent of LDO's lottery — the drop-MKR decision is preserved as a baseline universe decision (always-on at CONFIRMATION); only the +1.11 OOS Sharpe lift attribution is dead.**
- **Wall-clock 4.54h vs 4h CONFIRMATION HARD CAP** — exceeded by 32 minutes. Brief Calibration A (linear 50× from 6-min baseline ≈ 5h) was closer to reality than Calibration B (calibrated from iter-v3/008 abort ~1.3h). Cap empirically updated to 6h post-iter-v3/018 per `feedback_v3_cadence_discipline.md`.

## Critical Lessons

(a) **`feedback_seed_validation.md` was prescient.** Single-seed CONFIRMATIONs are unreliable. iter-v3/013's +2.6970 OOS Sharpe at one outer seed × n_trials=10 was a favorable lottery; the underlying expected performance is +0.39 OOS. Future CONFIRMATIONs MUST run at minimum 2 outer seeds (already the rule per `feedback_outer_seed_cap_2_v3.md`); 10-seed pre-MERGE concentration validation interpretation needs clarification for v3 (cap-2 rule vs. validation requirement).

(b) **Concentration is structural to a 3-symbol universe.** Multi-seed averaging did NOT compress concentration; it shifted the dominant symbol (LDO → TRX). To address Gate 7, structural changes are needed: either a hard `max_per_symbol_pnl_share = 0.40` portfolio constraint at the aggregation layer, OR universe expansion to 5+ symbols to dilute concentration mechanically. Tuning thresholds inside the 7-primitive risk-gate stack will not fix this.

(c) **DSR threshold at +0.95 is mathematically blocked at v3's current trade volume + n_trials budget.** DSR > 0.95 requires `observed_sr > E[max_SR] = 3.369` at n_trials=1500. This requires either (i) far more IS trades (hundreds), (ii) far fewer Optuna trials (defeats multi-seed validation), or (iii) a fundamentally stronger signal. The gate must be reformulated for v3 — proposal: `DSR > 0` (positive deflation) OR reduce CONFIRMATION budget to `--n-trials 20`. iter-v3/019's brief Section 8 should include this gate-reformulation proposal.

(d) **The 13-feature stack underperforms multi-seed by ~0.6 Sharpe units.** Knob-tuning (saturated per `feedback_axis_saturation_predictor.md`) cannot lift Sharpe by 0.6 units. iter-v3/014-017 axis exploration (ADX, microstructure, XGBoost, meta-labeling) all confirmed: NEW feature families are the unique lever capable of moving the needle. iter-v3/019's first EXPLORATION should target this axis.

(e) **Wall-clock cadence cap empirically updated 4h → 6h.** iter-v3/018 ran 4.54h. The CONFIRMATION cap was set at 4h per `feedback_v3_cadence_discipline.md` after the iter-v3/008 25h-extrapolation abort. Post-iter-v3/018, cap = ceil(4.54 × 1.2) = 5.5h ≈ 6h for safety. Updated across `.claude/commands/quant-iteration-v3.md`, `feedback_v3_cadence_discipline.md`, `feedback_v3_iter018_confirmation_baseline_validation.md`, and `briefs-v3/exploration_catalog.md` banner.

(f) **PROMISING-MECHANICAL ≠ compoundable across iterations.** iter-v3/013's drop-MKR was correctly classified as PROMISING-MECHANICAL (sister to NEGATIVE-no-effect) per `feedback_promising_mechanical_subtype.md`. The bootstrap CONFIRMATION confirmed this: drop-MKR is a baseline universe decision (always-on; trade-roster bit-identical to iter-v3/012 on the 3 retained symbols at single-seed) but the +1.11 OOS lift attribution disappears under multi-seed. Future CONFIRMATIONs must NOT bundle PROMISING-MECHANICAL components as additive "edge ingredients" alongside PROMISING signals.

(g) **Pre-registered probability calibration miss.** P7 (CONFIRMATION-MERGE @ P=35%) failed; P9 (Sharpe floors missed @ P=10%) realized; P6 (DSR < 0.95 @ P=15%) realized but for the wrong reason (predicted because n_eff=10+ would be lower than gate; actual because observed_sr < E[max_SR]). Future briefs should bias predictions toward "single-seed result is a lottery" priors when transitioning EXPLORATION → CONFIRMATION.

## Bootstrap Status

**BASELINE_V3.md established at root** (commit `ef18e1d`) per the user directive 2026-05-07. The bootstrap exception is **ONE-TIME**. Future CONFIRMATIONs (iter-v3/028+ assuming next 10 EXPLORATIONs) must clear ALL 10 gates to update the file. Failed gates from iter-v3/018 are documented as **outstanding constraints** in the BASELINE_V3.md "Failed MERGE Gates" section, with required Sharpe lifts and remediation axes spelled out.

## Recommendations for Next 10 EXPLORATIONs (iter-v3/019-028)

Per Critic FINAL Recommendations (SHA `199cbe4`), pre-committed via new memory rule `feedback_v3_iter019_axis_priorities.md`:

1. **HIGH — NEW feature families (top priority).** 13-feature stack at multi-seed produces +0.39 mean OOS — ~0.6 Sharpe below floor. Knob-tuning saturated (10 EXPLORATIONs done; iter-v3/014 ADX, /015 microstructure, /016 XGBoost, /017 meta-labeling all NEGATIVE). Order-book microstructure variants beyond `tbr_zscore_30`, funding-rate momentum / percentile features (Binance fundingRate API), on-chain proxies (exchange balance flows). Bias toward economically-interpretable features.

2. **HIGH — Concentration architecture.** TRX 66% / 56% OOS structural concentration. Either (a) hard `max_per_symbol_pnl_share = 0.40` portfolio constraint, OR (b) universe expansion to 5+ symbols.

3. **MEDIUM — DSR gate reformulation.** Brief proposes either `DSR > 0` (positive deflation) OR `--n-trials 20`. Process fix.

4. **MEDIUM — TRX/2022-Q4 regime gate.** PBO max=1.0 on FTX/LUNA crash. Either regime-aware TRX gate (kill TRX when BTC_drawdown_30d > 30%), OR Critic-accepted exception clause. **Do NOT remove TRX** (strongest OOS contributor in seed 42, +11.97 weighted_pnl).

5. **LOW — Knob axes** (labeling multipliers, ADX, z-score). Saturated; future briefs Section 2 must include behavioral-effect predictor with falsifier per `feedback_axis_saturation_predictor.md`.

6. **LOW — Universe expansion.** Defer until after one HIGH-priority feature-family axis is proven.

iter-v3/019 first EXPLORATION axis = **NEW feature families** (top priority). The unique lever capable of lifting Sharpe by 0.6 units to clear gates 1+2 floors.

## Cadence Status

**10-EXPLORATION cadence clock RESTARTS at iter-v3/019.** iter-v3/018 was the first v3 CONFIRMATION; cadence count returns to 0 of 10. Next CONFIRMATION earliest = iter-v3/028.

Wall-clock cap empirically updated **4h → 6h** for future CONFIRMATIONs (per Task D of this closeout).

## Reproducibility

- Setup commit SHA: `a595f46`
- Phase 5.5 gate SHA: `98769ce`
- Brief SHA: `5c1b303`
- Engineering report SHA: `00389ec`
- Critic FINAL SHA: `199cbe4`
- BASELINE_V3.md commit SHA: `ef18e1d`
- Reports: `reports-v3/iteration_v3-018/comparison.csv` (primary seed 42 + multi-seed-mean rows), `reports-v3/iteration_v3-018/seed_summary.json` (per-seed multi-seed disaggregation), `reports-v3/iteration_v3-018/pareto_front.csv` (Gate 10 evidence), `reports-v3/iteration_v3-018/dsr.json` (DSR/PBO/PSR), `reports-v3/iteration_v3-018/per_cell_pbo.csv` (TRX/2022-Q4 high-PBO cells)
- Tag: `v0.v3-018` (BOOTSTRAP — first v3 CONFIRMATION; not gates-pass certification)
