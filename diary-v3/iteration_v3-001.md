# Iteration v3-001 — Diary

## Decision: NO-MERGE

Critic OVERALL=BLOCK. Catastrophic hypothesis-implementation misalignment (4 of the brief's central architectural promises — M1+M2 meta-labeling, R1/R2/R3 risk gates, per-month auto-d* fracdiff, per-(feature,month) ADF — were not shipped) stacked on top of 5 mechanical Section 8 failures (IS Sharpe -0.0746 < 1.0, OOS/IS ratio -14.68 < 0.5, OOS trades 83 < 130, trades/month 5.9 < 10, MKR concentration 53.21% > 35%) and broken multiple-testing instrumentation (PBO=0 is a code bug, DSR=0 is a degenerate output of a negative-IS-Sharpe input, n_eff_trials=1 is a tautology). The headline OOS monthly Sharpe of +1.0955 is a regime-luck artifact, not validated edge — see "What Failed" §6 for the per-symbol sign-flip evidence.

## What Worked

The QR-side of the iteration was sound and produced reusable artifacts:

- **Phase 5.5 gate PASSED 10/10.** The brief's structure held up (all 10 mandatory sections, IS-only numerical evidence committed at SHA 73fdc8d before the brief, falsifiers pre-registered, library stack declared with mlfinlab→mlfinpy fallback documented, 16 mechanical MERGE criteria locked).
- **Symbol selection rationale held up.** None of the 4 v3 symbols failed Gate 1 (data quality) or Gate 2 (return regime). Within-universe Pearson correlation 0.33–0.51 (`v3_universe_correlation.csv`) is comparable to v2's 0.40–0.55 profile and well below the 0.85 redundancy threshold. Cross-track diversification (`v3_universe_cross_track_correlation.csv`) lands BCH/MKR/LDO/TRX at 0.56–0.73 vs BTC and 0.47–0.55 vs SOL — TRX is the strongest diversifier (lowest mean correlation).
- **Headline OOS metric is positive in form.** OOS monthly Sharpe = +1.0955, OOS daily Sharpe = +2.2053, OOS MaxDD = 22.04% (passes the ≤30% gate), OOS Calmar = +1.7477, OOS profit factor = 1.30 (`comparison.csv`). On paper this clears the OOS Sharpe > 1.0 floor and the MaxDD ≤ 30% gate.
- **2 of 4 symbols are genuinely positive OOS.** TRXUSDT +12.35 wpnl (30 trades, 53.3% WR), LDOUSDT +14.12 wpnl (13 trades, 38.5% WR) — both kept their IS sign (`q1_is_oos_per_symbol.csv`). TRX in particular performed as the brief predicted: highest µ/σ in IS (0.598) and highest OOS WR (53.3%). The v2 dead-paths catalog's "TRX failed in v2" entry was caused by IS-only Sharpe screening, not by the symbol — the v3 Gate 1+2+sector framework correctly rehabilitated it.
- **Risk gates fired at v2-comparable rates.** Combined kill rate 69–78% across the 4 symbols (`engineering_report.md` Gate Efficacy Table). BTC contagion filter killed 23/308 trades (7.5%) — consistent with v2's iter-v2/019 baseline.

## What Failed

Six interlocking failures, ranked from process-level (most expensive to fix) to mechanical:

**1. Phase 6 implementation gap — 4 of the brief's central architectural promises absent from the code.** The Critic's Check 8 documents this in detail (`review.md` §Check 8):
- **Meta-labeling M1+M2** (brief §3.6, the iteration's headline change): `run_baseline_v3.py:320-337` builds `m1 = LightGbmStrategy(...)` only, wrapped in `RiskV3Wrapper`. No M2. No `meta_label.py` module exists. The headline "meta-labeling baseline" never made it into the codebase.
- **Auto-d\* fracdiff** (brief §3.4): `features_v3/fracdiff_v3.py:153-154` uses `_fracdiff_series(log_close, 0.4, window)` — fixed `d=0.4`, identical to v2. The function `compute_fracdiff_stat` exists but is never called by the runner. Feature columns were renamed from `_d04` to `_dstat` while the values stayed v2. This is worse than not implementing it — it falsely advertises ADF-driven d* in the column name.
- **R1/R2/R3 risk gates** (brief §5.1–5.3): `RiskV3Wrapper` provides only the v2 5-gate set. Brief §5 explicitly mandated K=3 consecutive-SL cooldown (R1), 7% per-model DD scaling (R2), and 0.70-percentile Mahalanobis (R3) on all 4 symbols. None loaded.
- **CPCV scope mismatch** (brief §3.6): brief mandated CPCV on the 24-month training window (model-selection robustness statistic). Reality: `_compute_cpcv_paths` runs on the realized IS trade sequence (trade-distribution stability statistic). Different statistic, different inputs, different interpretation.

The Phase 5.5 gate verified brief completeness but does not verify brief-vs-code alignment — that's why a 10/10 PASS at Phase 5.5 didn't catch this. The Critic's Recommendation #1 (brief-vs-code reconciliation table as Phase 5.5 input) is the right structural fix.

**2. PBO=0 is a code bug, not a clearance.** `validation_v3.pbo_from_cpcv` lines 153-207 compares `metrics[best_global_idx] < oos_median`. Since `best_global_idx` is by construction the argmax over IS, and the path Sharpes range -1.83 to +1.20, the IS-best (+1.20) is structurally above the OOS-half median. Hence count of "overfits" = 0 → PBO = 0. The López de Prado CSCV requires comparing the IS-best's *OOS* performance (the same path's metric in the OOS half) — but in this implementation each path has only one metric (no IS/OOS-half split per path), so the test is structurally undefined. The reported PBO 0.0000 is an artifact, not evidence of robustness.

**3. Embargo silently rescaled 88→11 in CPCV.** Brief §3.2 specifies `gap = (timeout_candles + 1) × n_symbols = 88`. Reality: `run_baseline_v3.py:381` passes `gap=min(CPCV_GAP, n_trades // (CPCV_N_SPLITS * 2)) = min(88, 11) = 11` trade indices to `combinatorial_purged_cv`. Two different gap scales (22 in LightGBM CV, 11 in CPCV) are undocumented; the comment "scale gap for IS trade count" implies the author didn't realize 88 was already in candles. Silent rescaling breaks the brief's reproducibility contract.

**4. ADF averaged across symbols, not per-(feature, month).** Brief §3.4 + §8 criterion 13 mandates "ADF p < 0.05 on every feature at every retraining month." `adf_test.csv` reports per-feature averages across all 4 symbols (no per-month, no per-symbol). The averaging masked LDOUSDT `cusum_reset_count_200` p=0.0707 (non-stationary in pre-flight per `engineering_report.md:179`); the averaged report shows it at p=0.0178 (clearing the threshold). Averaging p-values across symbols is statistically invalid; per-month was silently dropped.

**5. Five Section 8 mechanical failures (criteria 1, 3, 4, 5, 6).** All locked before backtest:
- IS monthly Sharpe = -0.0746 (< 1.0 — FAIL by 1.07)
- OOS/IS Sharpe ratio = -14.68 (< 0.5 — FAIL by sign)
- OOS total trades = 83 (< 130 — FAIL by 47)
- Trades/month OOS = 5.9 (< 10 — FAIL by 4.1)
- Top-symbol OOS PnL share = 53.21% MKRUSDT (> 35% — FAIL by 18.21pp)

Plus criterion 7-9 (DSR/PBO/PSR) are degenerate (Critic Check 3), criterion 13 (ADF per-month) was not implemented (Check 5), and criterion 15 (10-seed sweep) was not run (Check 6 — only seed 42 in `pareto_front.csv`, vacuity not demonstrated).

**6. The OOS positive Sharpe is a regime artifact, not validated edge.** Per `q1_is_oos_per_symbol.csv` (Phase 7 diagnostic), MKR sign-flipped completely (IS -123.09 wpnl @ 23.3% WR → OOS +20.50 wpnl @ 46.7% WR) and BCH sign-flipped (IS +41.92 → OOS -8.44). `q4_is_yearly_per_symbol.csv` shows MKR's 2024 IS damage = -96.05 wpnl (out of -29.94 total IS for 2024) — the model overfit a loss-making 2024 short-MKR pattern that happened to invert in OOS. `q2_mkr_oos_attribution.csv` shows MKR's OOS is dominated by 3 short trades on May 19, Jun 13, Jun 22 2025 (all `take_profit`, all coinciding with the post-Sky-rebrand MKR-token decline) — top 1 trade = 71.3% of MKR's OOS wpnl. CPCV path matrix confirms: 21/45 paths positive (46.7% — barely above coin-flip), mean -0.175, median -0.096 (`cpcv_paths.csv`). The headline +1.0955 is a regime-flip artifact masquerading as edge, exactly as the Critic flagged.

## Critic Review Summary

| Check | Status | Why |
|---|---|---|
| 1 (Look-Ahead) | WARN | `RiskV3Wrapper._build_lookups` snapshots IS-window-wide stats once; OOS uses stats that include late-IS data. v2-inherited convention; brief never re-justified for v3. |
| 2 (Embargo) | FAIL | CPCV gap silently rescaled 88→11; LightGBM CV uses 22; two scales, one undocumented. |
| 3 (DSR/PBO/PSR) | FAIL | DSR=0 (degenerate from neg IS Sharpe); PBO=0 (code bug — best_global_idx tautology); PSR=1.0 (no discriminating power); n_eff_trials=1 (tautology). None cleared via legitimate computation. |
| 4 (IC) | PASS | Informational; no new feature families this iteration; existing v2 family redundancies pre-exist iter-v2/069 pruning. |
| 5 (ADF) | FAIL | Averaged across symbols, not per-(feature, month); LDO `cusum_reset_count_200` pre-flight p=0.0707 hidden by averaging. |
| 6 (Pareto) | FAIL | Only seed 42 in `pareto_front.csv` — Engineer launched with `--seeds 1`; the iter-v2/069 vacuity argument was assumed, not verified. |
| 7 (Reproducibility) | WARN | Silent gap rescaling breaks the brief's "gap=88" contract; n_eff=1 is a computational tautology, not data-driven. |
| 8 (Hypothesis-Implementation Alignment) | FAIL | Meta-labeling M1+M2, auto-d* fracdiff, R1/R2/R3, and CPCV scope all promised but not implemented. The iteration's central architectural changes were silently dropped. |
| **OVERALL** | **BLOCK** | One Check 8 FAIL alone is structural; combined with FAILs on 2, 3, 5, 6 there is no path to MERGE. |

## Pareto Position (chosen seed)

`pareto_front.csv` contains exactly one row (seed 42). The 10-seed sweep mandated by Section 8 criterion 15 was not run; the Engineer launched with `--seeds 1`. The Pareto-dominance check is therefore undefined.

| seed | OOS monthly Sharpe | OOS MaxDD | OOS Calmar | PBO | n_trades OOS | max symbol concentration |
|---|---:|---:|---:|---:|---:|---:|
| 42 | +1.0955 | 22.04% | +1.7477 | 0.0000 | 83 | 43.64% |

The brief's discretionary clause permitted single-seed merge "if criterion 15 is structurally vacuous (the iter-v2/069 finding repeats)." That vacuity must be empirically demonstrated, not assumed. With single-seed only, the Pareto front cannot be computed and the assumption stands unverified — Check 6 = FAIL on omission.

(Note: the seed_summary.json reports `max_concentration_pct = 43.64`, computed unweighted across all 4 symbols; the per_symbol.csv reports MKR at 53.21% as a share of total weighted PnL. Both are valid views; the 53.21% is the Section 8 criterion 6 measurement.)

## ADF Stationarity Report

`adf_test.csv` reports 34/34 features passing p < 0.05 in averaged-across-symbols form. Per-feature minimums:
- `mom_accel_5_20`: ADF -63.86, p=0.0 (most stationary)
- `cusum_reset_count_200`: ADF -4.13, p=0.0178 (lowest pass margin in averaged form)
- `fracdiff_logclose_dstat`: ADF -4.21, p=0.0072

The averaged report masks the per-symbol pre-flight result that `cusum_reset_count_200` for LDOUSDT was p=0.0707 — non-stationary on that single symbol. Averaging p-values across symbols is statistically invalid (Fisher's combined-p method or per-symbol verification is the right approach). The brief's "per (feature, month)" mandate was not implemented at all — the runner runs ADF once per (feature, symbol) on the entire IS window and averages across symbols.

## Pre-Registered Failure-Mode vs Reality

The brief's Section 7 made three explicit failure-mode predictions. None matched the actual failure mode:

**Prediction 1: M2 over-fits to a tiny minority class → PBO catches it.** Predicted: single-path Sharpe +1.5–+1.8, CPCV median 15–25% lower (+1.1–+1.5), PBO 0.30–0.45. **Reality:** M2 was never built. PBO is broken by code bug. Both halves of the prediction failed because the architecture wasn't shipped — not because the prediction was wrong about M2's behavior.

**Prediction 2: LDO's narrower IS regime coverage produces seed-unstable OOS predictions; vol-targeting saves total PnL.** **Reality:** 10-seed sweep was not run; can't verify seed instability. LDO's IS contribution was actually positive (+46.67 wpnl over 17 trades, +51.9% net PnL, the strongest IS symbol per `in_sample/per_symbol.csv`); LDO's OOS was a weaker positive (+14.12 wpnl, 38.5% WR) — the IS regime gap did not manifest as the predicted seed instability. The prediction was off on the symbol — the actual problem was MKR, not LDO.

**Prediction 3: TRX retreads its v2 iter-v2/066 dead-path failure; CPCV's 45-path variance catches it.** **Reality:** TRX did NOT retread v2's failure — it was the second-strongest OOS contributor (+12.35 wpnl, 53.3% WR, 30 trades — the highest trade count of any symbol). The v3 Gate 1+2+sector framework correctly rehabilitated TRX; the v2 dead-path was a methodology artifact, not a TRX-specific signal failure.

**Match assessment: NONE of the 3 pre-registered failure modes happened as predicted. This is a major calibration miss.** The actual failure was process-level (Engineer didn't implement what the brief required), which the QR's Section 7 did not anticipate at all. Section 7 implicitly assumed implementation fidelity — "if the methodology stack is built, here's how it could fail" — but the iteration failed before reaching that question.

The lesson is meta-research: future v3 brief Section 7s must include at least one process-level failure mode prediction (e.g., "library install fails," "engineer drops a feature for compute budget reasons," "code-vs-brief drift"), not only model-behavior predictions. The brief assumed the QE's faithfulness as a prior; the brief should treat it as a probability.

## Lessons

Five generalizable takeaways for future v3 iterations:

1. **Phase 5.5 gate verifies brief completeness but not brief-vs-code alignment.** The gate passing 10/10 didn't prevent 4 architectural promises from being silently dropped during Phase 6. The Critic's Recommendation #1 — a "Brief-vs-Code reconciliation table" filled in by the Engineer row-by-row before running the backtest — is the right structural fix. Each Section 3 promise gets a `code path implementing this` cell; empty cells = the iteration cannot proceed to Phase 7. Promote this to a Phase 5.5 gate input (Engineer pre-flight requirement).

2. **iter-v3/001's "single iteration shipping methodology stack + universe + meta-labeling + auto-d* fracdiff + ADF + CPCV" was too ambitious for one iteration.** The v3 skill's framing ("largest single iteration in project history") proved correct, but the execution risk wasn't priced in — 7505s of compute burned to discover that 4 of 7 promised changes never made it to code. Future v3 iterations should split methodology features over multiple iterations. The right sequence (proposed below in Next Iteration Ideas) is iter-v3/002 = CPCV+PBO+PSR with adversarial unit tests, iter-v3/003 = meta-labeling, iter-v3/004 = auto-d* fracdiff, and so on. One-variable-at-a-time was already the rule from iter-v3/002 onward; iter-v3/001 was the explicit exception, and the exception bit.

3. **PBO and DSR need adversarial unit tests against known-overfit synthetics.** The Critic's Recommendation #2 makes this concrete: write a `test_pbo_overfit_synthetic.py` that generates 45 path Sharpes from a known-overfit distribution (e.g., random IS with regime-flipped OOS) and asserts PBO ∈ [0.4, 0.6]. The current PBO returns 0 on a strategy the engineering report itself admits is "near-random IS performance" — that's a structural code bug, not a borderline case. DSR needs the same coverage with negative-IS inputs (current behavior: silent clamp to 0, which masks the underlying methodology failure).

4. **IS-negative / OOS-positive sign inversions should be a hard merge precondition.** The Critic's Recommendation #3 codifies this as `sign(IS_Sharpe) == sign(OOS_Sharpe)` is a hard gate. iter-v3/001's IS=-0.07 / OOS=+1.10 split should never have reached the Critic — it's the regime-flip signature for which the OOS positive metric is statistically indistinguishable from luck. Adding this gate to brief Section 8's mechanical criteria (and to the Critic's Check 3 logic) prevents the entire class of failure that iter-v3/001 produced even when methodology stack works.

5. **First entry to v3 dead-paths catalog (NOT the universe — the specific stack).** Per the orchestrator's hard rule, BCH/MKR/LDO/TRX is NOT on the v3 dead-paths catalog; the symbol selection rationale held up and 2 of 4 symbols (TRX, LDO) were genuinely OOS-positive. The dead-path entry is the specific full-stack attempt:

   - **iter-v3/001 — universe (BCH+MKR+LDO+TRX) attempted as a single-iteration shipment of v2 5-gate + R3 + meta-labeling + auto-d* fracdiff + CPCV(N=10,k=2) + PBO + PSR.** NO-MERGE due to Phase 6 implementation gaps (4 of 7 architectural promises silently dropped) + PBO/DSR computation bugs + IS-OOS sign inversion masking regime luck. The universe is not invalidated — only this specific full-stack attempt. The MKR/BCH sign-flip pattern is also not on the dead-paths list per se, but is the concrete trigger for Lesson #4's regime-mismatch precondition.

## Next Iteration Ideas

Five proposals for iter-v3/002 onward, ranked by expected impact on closing the iteration-process holes that iter-v3/001 exposed:

**1. iter-v3/002 — "Fix the methodology stack first." [HIGHEST PRIORITY]**
RE-implement CPCV / PBO / PSR with proper unit tests against known-overfit synthetics. Same universe (BCH+MKR+LDO+TRX). Same risk gates as v2. NO meta-labeling (defer to iter-v3/003). NO auto-d* fracdiff (defer to iter-v3/004). The single brief-locked deliverable: CPCV/PBO/PSR that produce believable numbers on the same trade history.

Falsifier: PBO computed on iter-v3/001's data should land near 0.5 (chance baseline for a near-random strategy with regime-flipped OOS), not 0. Adversarial unit tests in `tests/strategies/ml/test_pbo_overfit_synthetic.py` must pass before Engineer's Phase 6 starts. If the new PBO returns ≈0.5 on iter-v3/001's CPCV path matrix, the methodology stack is correct and we have a trustworthy baseline to build on. If it returns 0 or 1, the bug is still there.

**2. iter-v3/003 — "Add meta-labeling on validated stack." [SECOND PRIORITY]**
Once iter-v3/002's methodology stack is proven, add the M1+M2 architecture. Same universe. Pre-registered hypothesis: meta-labeling improves OOS Sharpe by ≥0.3 by filtering low-confidence M1 signals; trade count drops 20–40% vs M1-alone. Engineer's Phase 5.5 gate must include a brief-vs-code reconciliation table (Recommendation #1) showing both `meta_label.py` exists and the runner builds an M2 instance. If reconciliation fails, BLOCK at 5.5.

Falsifier: if OOS trade count drops below 10/month even with universe expansion, meta-labeling is killing too much signal — regress to M1-only and treat M2 as iter-v3/006+ scope.

**3. iter-v3/004 — "Universe re-evaluation if iter-v3/002+003 still missed."**
Triggered only if iter-v3/002 OOS Sharpe is still < 1.0 with the validated stack. Re-run `analysis/iteration_v3-001/symbol_universe.py` on a wider candidate set (12-18 symbols not in V3_EXCLUDED_SYMBOLS), with the additional gate: `sign(IS_Sharpe) == sign(OOS_Sharpe)` over a held-out OOS-like 2024 sub-window (NOT the real OOS, which stays sealed). Pick 4 symbols where universe-level IS Sharpe > 0 — eliminating the iter-v3/001 sign-flip pattern at universe-selection time.

Falsifier: if no 4-symbol combination passes the IS-positive constraint while clearing the existing Gate 1+2+sector criteria, the v3 universe-pool is structurally exhausted of edge — pivot to iter-v3/005 (auto-d*) or iter-v3/006 (crypto-native features) without re-touching the universe.

**4. iter-v3/005 — "Auto-d* fracdiff with per-(feature, month) ADF."**
Only after iter-v3/002's methodology stack + iter-v3/003's meta-labeling work. Implement `FracdiffStat` for real (not the iter-v3/001 fake), with per-(feature, month) ADF tracking per the original brief mandate. Engineer's brief-vs-code reconciliation table must include rows for: (a) `compute_fracdiff_stat` is called by the runner (not just defined), (b) ADF runs per (feature, month) and produces an N_features × N_months matrix in `adf_test.csv`, (c) per-month d* is persisted and reused at predict-time. Falsifier: if d* > 0.6 on more than 50% of (feature, month) cells, the existing v2 fixed-d=0.4 was approximately right and auto-d* doesn't pay for its complexity — accept iter-v2/069's choice and move on.

**5. Skill-level meta-iteration: update the v3 skill itself.** This is META-iteration work; submit as a separate skill PR (not a per-iteration v3 deliverable). Three updates per the Critic's Recommendations:
   - **#1: Brief-vs-Code reconciliation table as Phase 5.5 gate input.** Add a section to `quant-iteration-v3.md` requiring the Engineer to fill row-by-row before backtest. Empty rows → Phase 6 cannot start.
   - **#2: Adversarial unit tests for PBO/DSR mandatory before any v3 iteration uses them.** Add to the v3 skill's "Library Dependency Plan" section: `tests/strategies/ml/test_pbo_overfit_synthetic.py` and `tests/strategies/ml/test_dsr_negative_is.py` must pass in CI before ANY v3 iteration runs.
   - **#3: Regime-mismatch precondition.** Add `sign(IS_Sharpe) == sign(OOS_Sharpe)` to the v3 hard merge gates list in the skill's "Sacred Constants" section. Critic's Check 3 logic gets the new sub-check.

The skill update is the highest-impact change because it affects every future v3 iteration; iter-v3/002's specific re-implementation is its first beneficiary.
