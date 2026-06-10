# Phase 7.5 Critic Review — iter-v1/086

OVERALL: SPECIALIST-NEGATIVE — subtype NEGATIVE-PROBE-INCONSISTENT; IS −0.3044 / OOS −0.5967, both merge floors fail, structure-probe false-pass confirmed (NOT a code defect).

## Iteration Type
SPECIALIST single-coin cohort ("TRBUSDT",), SYMBOL axis, STOCK 48-col stack, NO new features. No baseline update on the table regardless of outcome. Verdict forced by artifacts (IS −0.30 < +0.00 F2/F4 floor) — single-pass, no Round 2.

## Per-Check Status
- **Check 1 Look-Ahead: PASS.** Foundation clean; `walk_forward.py:113` embargo (`train_end_ms = test_start_ms - embargo_ms`) intact. Labeling σ_t past-only EWMA. 4 regression tests present. No new features = empty look-ahead surface. Empirical: last IS trade close 2025-03-26, first OOS open 2025-03-27 (one 8h boundary), OOS_CUTOFF_MS unchanged.
- **Check 2 Embargo: PASS.** 21+1 candles single-symbol; boundary purge embargo-aware.
- **Check 3 Multiple-Testing: INFORMATIONAL/MOOT.** DSR/PSR informational at single-outer-seed SPECIALIST; both windows negative → no correction can rescue. n_eff=1 correct.
- **Check 4 IC: INFORMATIONAL.** Zero new features. F5a DIVERSIFIER-DEGENERATE confirmed (5/10 top features shared bundle basis; MACD r5, ADX r9 below the shared funding block) — MOOT for seat (negative standalone).
- **Check 5 ADF: INFORMATIONAL.** No new features.
- **Check 6 Pareto: N/A.** Single-outer-seed; `cross_seed_sharpe_std=0.000` is DEGENERATE (1 outer seed), explicitly NOT read as robustness PASS.
- **Check 7 Reproducibility: PASS.** Runner 5da75fa8; feature_columns pinned (48, asserted); inner seeds literal range(42,92). Trade-math spot-check reconciles.
- **Check 8 Hypothesis-Alignment: PASS.** Only src/ change = `V1_ITER086_UNIVERSE=("TRBUSDT",)`; NO V1_ITER086_FEATURE_COLUMNS; risk config matches brief; cohort-isolation assert present; guard test exists. No scope creep.
- **Check 13 Anti-Pattern Scan: PASS.** A1-A7/A12/A13 clean; fresh optuna.create_study per seed; static universe literal.
- **Check 14 Axis Family: PASS.** per-cohort-specialization-TRB matches src/; rotation VALID (TRB ∉ prior 5).

## Architectural Note — `--seeds 1` framing
The eng report's "actual: 1-seed=42" is misleading-but-not-wrong. `--seeds 1` sets the OUTER loop only; `lgbm.py:1080` hardwires `specialist_seeds = V1_SPECIALIST_SEEDS` (all 50, 42..91) independent of it. **The 50-inner-seed variance control DID execute.** cross_seed_std=0.000 is degenerate because there is 1 OUTER seed, NOT because one model trained. NOT a config defect; run matches brief spec. (Flag eng-report wording for diary: should read "1 OUTER × 50 inner.")

## No-Cheating Verification — CLEAN
1. Listing-shock INCLUDED not trimmed: first IS trade 2022-09-07 weight_factor=1.0 (R5 cold-start); 2022-09 = −38.43% drags result DOWN (anti-cheating direction). No start_time trim.
2. Probe genuinely did not reproduce (not a defect): same 48-col hash b81176f8, same ATR label, same seed=42. **CORRECTION to eng report + LM 7.4: the claim "ONLY n_trials moves" is FALSE.** The probe (probe_TRBUSDT.py:244-246) runs `ood_enabled=False` + `bounds_profile="v1_pruned"`; the full runs `ood_enabled=True` + `bounds_profile="v1_specialist"` (lgbm.py:1159). THREE confounds probe→full: n_trials (10→30), OOD (OFF→ON), bounds (pruned→specialist). Does not change the verdict but is load-bearing for the GATE-2 reform.
3. cross_seed_std=0.000 degenerate, explicitly NOT a robustness PASS.

## GATE-2 Reform Assessment — pass-side INVALIDATED
The /085 GATE-2 reject-side is 2/2 (CRV, UNI). The pass-side now has 1 test (TRB +0.493 → full −0.30) and it FALSE-PASSED by Δ−0.80 → pass-side predictive value is zero-confirmed.
- **LM 7.4's "same-budget n_trials=30 probe eliminates bias by construction" is INCORRECT** given the OOD + bounds confounds. A corrected probe must match ALL THREE: **n_trials=30 AND ood_enabled=True AND bounds_profile="v1_specialist"** (= full specialist config at single-inner-seed=42, single-outer-seed). Only then is the residual gap pure 50-inner-seed averaging.
- Threshold-haircut (≥+0.80) REJECTED as primary: a single threshold on a 2-point bias sample (Δ−0.46, Δ−0.80) is too noisy.
- ENDORSE the in-fold/walk-forward gap as a hard GATE-2 SECONDARY (mean per-fold best in-fold objective − realized walk-forward IS > ~0.3 → noise-dominated; would have caught UNI + TRB) + a training_days ≥120d floor for single-symbol stock-stack mines (26/46 folds <120d = noise-exploitation channel).
- **Corrected GATE-2 PRIMARY:** config-matched probe (n_trials=30 + OOD ON + v1_specialist bounds) single-inner-seed=42, threshold ≥+0.30. Keep n_trials=10 as an advisory pre-pre-screen only. Retire the current pass-side before any further fresh-alt mine.

## Recommendations to QR
1. Retire the n_trials=10 GATE-2 PRIMARY pass-side; replace with the config-matched probe (close ALL three confounds — n_trials, OOD, bounds — not n_trials alone). The queued BNB/XRP mines MUST use the amended config-matched probe.
2. Promote the in-fold/walk-forward optimism gap to a hard pre-flight check + training_days ≥120d floor.
3. Reporting nits: (a) "1 OUTER × 50 inner" wording; (b) reconcile the two DSR conventions (comparison.csv corrected-Sharpe-space vs dsr.json probability-space).

## Path Forward (MANDATORY — NEGATIVE-class)
Campaign now 0/6 fresh-alt mines (ATOM, ICP, FIL, CRV, UNI, TRB); shared signature = cheap-probe positive that doesn't survive the full budget on a noisy single-symbol surface. NO multi-seed CONFIRMATION (directive). Prior-5 families all per-cohort-specialization; proposing 3 from NEW families:
1. **R5 listing-window-guard primitive (R5-LWG)** — *risk-primitive*. Dropping the un-vol-targeted first-45-day listing window flips TRB cumulative IS PnL −25.24% → +13.19% (Δ+38.43; 15.7% of |IS PnL| from <3% of period). Skip-or-0.5×-weight first 45 candles post-listing until VT history matures. Testable on the EXISTING failed roster (TRB/UNI/FIL) — isolates cold-start drag vs no-edge.
2. **GATE-INV probe-inversion diagnostic** — *methodology-instrument*. Batch-run the config-matched n_trials=30 probe AND the cheap n_trials=10 probe across the failed roster (FIL/CRV/UNI/TRB) to characterize the probe→full bias at n>2; converts the 2-point estimate into a calibrated curve. Cheap (minutes each); de-risks the BNB/XRP queue before spending 6h runs.
3. **W-DECAY time-decay sample weighting** — *labeling/sample-weighting*. Root cause was training_days collapsing to median 95d as Optuna chases short-window noise-fit. Exponential recency-weighting (AFML Ch. 4) keeps the full 24-month window (removes the short-window collapse incentive) while emphasizing recent regime. Testable on TRB's existing data.

Queued user-directed BNB/XRP universe-expansion mines remain valid but MUST gate on the AMENDED config-matched probe.

OVERALL=SPECIALIST-NEGATIVE
