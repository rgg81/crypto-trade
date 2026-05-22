# iter-v3/092 — Cycle-3 CONFIRMATION — the MULTI-SEED CONFIRMATION-GRADE VERDICT on the cross-sectional `LGBMRanker` line / CONFIRMATION-NO-MERGE (filed as BLOCKED) / Critic Phase-7.5 OVERALL=BLOCK

**Date**: 2026-05-18
**Type**: CONFIRMATION (cycle-3 CONFIRMATION — the iteration that follows the /082-091 10-EXPLORATION cadence; a multi-seed CONFIRMATION-grade closing verdict on the cross-sectional `LGBMRanker` momentum-rank line — `--seeds 2` outer {42,123} × `ENSEMBLE_SIZE=5` inner = 10 models/cell, `n_trials=35`).
**Verdict**: **Critic Phase-7.5 OVERALL = BLOCK** — `briefs-v3/iteration_v3-092/review.md`, committed `1140143`. The Critic was NOT re-run; the BLOCK verdict is FINAL.
**Classification**: **CONFIRMATION-NO-MERGE** (brief Section 8.2) — filed as **BLOCKED**. G1 (IS multi-seed-mean monthly Sharpe +0.0885 vs the +1.0 floor) and G2 (OOS +0.3194 vs the +1.0 floor) both FAIL by an order of magnitude; G4/G5/G6 (DSR/PBO/PSR) FAIL as hardcoded EXPLORATION-era placeholders, never computed — the BLOCKING defect.
**Decision**: **NO-MERGE.** The cross-sectional `LGBMRanker` momentum-rank line is **substantively closed** as a route to a merge-grade book — but /092 is filed BLOCKED, not as a clean CONFIRMATION-NO-MERGE, because three of its ten CONFIRMATION gates were never built.
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), tag `v0.v3-059`. A BLOCKED CONFIRMATION never updates the baseline; a CONFIRMATION-NO-MERGE never updates it regardless.
**Branch**: `iteration-v3/092`

---

## 1. What was done — a multi-seed CONFIRMATION-grade closing verdict on the cross-sectional line

iter-v3/092 is the **cycle-3 CONFIRMATION**. Cycle 3 (iter-v3/082-091, ten EXPLORATIONs) produced **zero clean PROMISING results** — there is no edge bundle to confirm. So /092's role, exactly as the /091 closeout recommended (`diary-v3/iteration_v3-091.md` Section 9.2) and the /091 Critic mandated (`review.md` Recommendation 2), is a **multi-seed CONFIRMATION-grade closing verdict** on v3's most substantial cycle-3 effort: the four-iteration cross-sectional `LGBMRanker` re-architecture (/088-091, all single-seed=42).

The single build: take the cross-sectional `LGBMRanker` architecture in its **best-faith form** — `score_mode="trained"`, the corrected-/091-horizon-EDA-best H=21 (the /089 H=3 incumbent is the trained ranker's *worst* horizon — `H1_horizon_grid.csv`), the 13-feature stack, the /089 cost-aware quintile long-short construction, the corrected /091 embargo — and run it **multi-seed** at the v3 CONFIRMATION spec: `--seeds 2` (outer seeds {42, 123}), `ENSEMBLE_SIZE=5` inner per outer seed (5-model arithmetic-mean score ensemble), `n_trials=35` → 10 models/cell, 350 total Optuna trials. The only Phase-6 build delta was **multi-seed support for the cross-sectional runner**, which the runner did not previously have (the /088-091 cross-sectional runs were all single-seed=42, `ensemble_size=1`).

The honest pre-registered expected outcome (brief Section 7, Section 8) was **CONFIRMATION-NO-MERGE** at ≈95% — the IS evidence (the best-faith trained-ranker form reaches only M2 single-seed IS net monthly Sharpe +0.0944, an order of magnitude below the +1.0 floor) pointed firmly sub-floor. /092 was never an edge hunt; it was the rigorous, lottery-robust *close* the four single-seed cross-sectional iterations owed before cycle 4.

---

## 2. Results — multi-seed mean IS +0.0885 / OOS +0.3194 — sub-floor by an order of magnitude

The multi-seed-aggregate book (the genuine mean of the two correctly-computed per-seed books — Critic Item 1 traced the entire multi-seed path and verified the aggregate arithmetic is sound):

| Metric | In-Sample (multi-seed mean) | Out-of-Sample (multi-seed mean) | OOS/IS ratio |
|---|---:|---:|---:|
| **Monthly Sharpe (net)** | **+0.0885** | **+0.3194** | **3.61** |
| Monthly Sharpe (gross) | +0.1537 | +0.3473 | 2.26 |
| OOS rank-IC (mean) | — | +0.0358 | — |
| Turnover/bar (IS) | 0.0243 | — | — |
| frac_positive_paths (mean) | 0.578 | — | — |
| n_seeds / n_trials_total | 2 / 350 | — | — |

Per-seed breakdown (source: `ensemble_summary.json`, `seed_*/comparison.csv`):

| Metric | Seed 42 | Seed 123 | Multi-seed mean |
|---|---:|---:|---:|
| IS monthly Sharpe (net) | +0.0169 | +0.1602 | +0.0885 |
| OOS monthly Sharpe (net) | +0.4328 | +0.2060 | +0.3194 |
| OOS/IS ratio (net) | **25.63** | 1.29 | 3.61 |
| frac_positive_paths | 0.489 | 0.667 | 0.578 |
| OOS net positive | true | true | — |

**The headline read.** The multi-seed mean IS monthly Sharpe is **+0.0885** and the OOS monthly Sharpe is **+0.3194** — both an order of magnitude below the +1.0 absolute merge floors (G1, G2). This is not a marginal shortfall; it is a decisive, pre-registered outcome. The brief Section 2.4 pre-registered it exactly: "A best-faith IS net monthly Sharpe of +0.0944 cannot, on any honest reading, produce an OOS multi-seed mean clearing the +1.0 OOS floor." The observed multi-seed IS +0.0885 is consistent with and slightly below the pre-registered EDA's best-faith single-seed +0.0944 — multi-seed averaging tightened the IS book rather than boosting it, exactly as expected.

**The OOS +0.3194 is a SUSPICIOUS-ratio lottery artifact, NOT durable edge.** The aggregate OOS/IS ratio 3.61 exceeds the v3 SUSPICIOUS heuristic of 3.0. It is driven *entirely* by seed 42 (IS +0.0169 ≈ 0, OOS +0.4328, ratio 25.63) against a comparatively healthy seed 123 (IS +0.1602, OOS +0.2060, ratio 1.29). A near-flat IS book makes any modest OOS positive produce an extreme ratio; seed 42's `frac_positive_paths` is 0.489 (sub-0.5, IS-weak) — the textbook single-seed-lottery signature (`feedback_v3_engineered_features_dont_stack.md`; the /091 reference-book pattern). The first positive-OOS-net cross-sectional book in the /088-092 line sits on a near-flat IS book and reflects one seed drawing a favorable OOS window — it must NOT be presented as a durable edge. The brief Section 7 named this scenario at ≈10% ("one or both outer seeds draw a lucky OOS window") and it is the realized pattern at the 2-outer-seed level.

OOS rank-IC is +0.0358 (mean; seed 42 +0.0382, seed 123 +0.0333) — consistent with the /088-091 line's +0.03 to +0.04 range. The signal transfer (rank-IC) is real and stable; the signal is simply too faint to overcome trading costs at the OOS book level. G9 PASS while G2 FAIL — the architecture has genuine but un-monetizable predictive content.

---

## 3. The honest cross-sectional-line verdict — NO-MERGE on reproducible G1/G2

**The substantive verdict on the cross-sectional `LGBMRanker` momentum-rank line is NO-MERGE, and it is not in doubt.** /092's G1/G2 — IS multi-seed-mean monthly Sharpe +0.0885 and OOS +0.3194 against the +1.0 floors — are reproducible runner artifacts (the Critic Item 1 verified the aggregate `comparison.csv` `monthly_sharpe` arithmetic to the float — IS = (0.016889620540854328 + 0.1601684410336085)/2 = 0.08852903078; OOS = (0.4328433881583013 + 0.20603061801945707)/2 = 0.3194370030). They fail the floors by an order of magnitude. The Critic was explicit: this verdict "is real and reproducible and would, on its own, cleanly close the line."

The five-iteration cross-sectional ledger, stated plainly (carried from `diary-v3/iteration_v3-091.md` Section 6, now extended with the /092 multi-seed close):

| Iter | Type | OOS net monthly Sharpe | Classification | What it established |
|---|---|---:|---|---|
| /088 | RE-ARCHITECTURE | −0.5418 | ARCHITECTURE-PARTIAL | v3's first genuine OOS signal transfer (rank-IC +0.043, t ≈ 4.6); the BOOK lost |
| /089 | CORRECTED build | −0.0985 | CONSTRUCTION-PARTIAL | a +0.44 lift — but MECHANICAL (sign fix + turnover cut; drag removal, not edge) |
| /090 | feature expansion | −0.0770 | FEATURE-EXPANSION-FALSIFIED [Critic BLOCK] | first genuine edge attempt — FAILED; OOS gross fell |
| /091 | scoring function | −0.0995 | CONSTRUCTION-FALSIFIED | second genuine edge attempt (model-free score) — FAILED; OOS gross net-negative |
| **/092** | **CONFIRMATION** | **+0.3194** (multi-seed mean — lottery-driven) | **CONFIRMATION-NO-MERGE (BLOCKED)** | **the multi-seed close: IS +0.09 / OOS +0.32 sub-floor by 10×; OOS positivity is a seed-42 lottery artifact** |

The line produced a genuine but faint OOS rank-IC (+0.03 to +0.04) — real signal transfer, worth recording — but across four single-seed iterations it never produced a net-positive OOS *book*, the two genuine edge attempts both failed, and the /092 multi-seed close confirms the best-faith trained-ranker form reaches only IS +0.09 / OOS +0.32 — far short of merge grade. On honest, lottery-robust evidence the **cross-sectional `LGBMRanker` momentum-rank architecture is closed as a route to a merge-grade book.** The `cross_sectional.py` infrastructure is RETAINED as code (a working, audited, reusable cross-sectional engine); the momentum-rank *strategy* on it is closed.

This is the verdict /092 was dispatched to deliver, and it delivers it on reproducible G1/G2. The BLOCK (Section 4) does not reverse this verdict — it is a CONFIRMATION-artifact-completeness defect, not a verdict reversal.

---

## 4. The Critic's BLOCK — DSR/PBO/PSR were never computed (the /090 defect class recurring)

**Critic FINAL `1140143` (`briefs-v3/iteration_v3-092/review.md`): OVERALL=BLOCK.** The BLOCK is filed honestly here: Items 1-3 PASS, Item 4 is the BLOCKING defect.

- **Item 1 — the NEW multi-seed code: PASS.** The Critic traced the entire multi-seed path — the outer-seed loop over {42, 123} (`run_cross_sectional_v3.py:1132-1146`), the `_derive_ensemble_seeds` copy (character-for-character identical to `run_baseline_v3.py:119-128`, the integration test re-derives and asserts equality), the 5-model inner ensemble (five distinct `LGBMRanker` objects), the raw-score arithmetic-mean averaging, and the aggregate-mean arithmetic (verified to the float). The multi-seed headline IS +0.0885 / OOS +0.3194 is the **genuine mean of two correctly-computed per-seed books.** No bug in the multi-seed code.
- **Item 2 — the embargo fix at H=21: PASS.** `embargo_ms = (XS_HORIZON+1)·interval_ms` = 22 × 28,800,000 = 633,600,000 ms ≈ 7.33 days; the CPCV row-gap `XS_REQUIRED_GAP = 484` is triple-asserted; the bugged `XS_REQUIRED_GAP·interval_ms` form is absent. The /091 Phase-5.5-BLOCK fix is present and load-bearing at H=21.
- **Item 3 — the gross-Sharpe runner artifact: PASS.** `gross_monthly_sharpe` is a genuine reproducible artifact via the shared `_monthly_sharpe(sub, pnl_col)` helper; the aggregate re-means it correctly.
- **Item 4 — DSR/PBO/PSR at a CONFIRMATION: NOT RESOLVED — the BLOCK.** The DSR/PBO/PSR gates (G4/G5/G6) are **hardcoded EXPLORATION-era `0.0`/`NaN` literals** in `run_cross_sectional_v3.py` — `dsr=0.0`, `psr=0.0`, `n_eff=0` are literal constants (per-seed lines 601-607; aggregate lines 945-952); `pbo` is `float("nan")` hardcoded. The per-seed code carries the verbatim comment `# not applicable for cross-sectional path at EXPLORATION` — the smoking gun. **They were never computed.** The /092 setup commit `a6217d3`, whose entire job per brief Section 4.3 was to upgrade the EXPLORATION-era runner to CONFIRMATION spec, did NOT build the CONFIRMATION-grade multiple-testing machinery. The canonical v3 helpers `validation_v3.psr` (line 508) and `deflated_sharpe_ratio_v3` (line 428) **exist and were never imported or called** — the runner imports only `combinatorial_purged_cv` from `validation_v3`. The brief's escape clause ("structurally not computable, e.g. too few OOS months → honest sentinel + FAIL") does not apply: the OOS book has **15 monthly observations** — exactly the PSR input brief Section 4.3 names — and `n_trials=350` is a valid DSR trial count. The gate was computable and was not computed.

The engineering report's "Note on DSR/PBO/PSR" compounds the defect: it narrates the hardcoded zeros as if computed — "the cross-sectional book at 350 trials/cell produces n_eff=0 effective trials, meaning the signal is too faint... PBO=NaN means the CPCV path structure did not produce a valid PBO estimate... These are honest sentinel values per Section 4.3." Every clause is a post-hoc rationalization of a literal constant. `n_eff=0` is `"n_eff": 0` hardcoded on line 951, not a PCA-on-trial-returns computation; DSR=0.0 is `"dsr": 0.0` on line 946, not a deflation result. **This is a false provenance.**

This is the **/090 BLOCK defect class recurring at /092**: a CONFIRMATION-gate-determining artifact presented as a genuine runner output when it is not. At /090 the defect was a hand-computed `gross_monthly_sharpe` with a mathematically-impossible /089 anchor feeding falsifier F3. At /092 it is three hardcoded gate constants narrated as computations in the engineering report's Gate Evaluation table. The defect is in the verdict-determining artifact set, so it BLOCKs — even though the G1/G2 verdict it sits beside is sound.

---

## 5. The Critic's three Recommendations — each integrated

The Critic closed with three process-level Recommendations for the corrected re-run / next iteration. All three are integrated into this closeout:

**Recommendation 1 — Build the CONFIRMATION-grade DSR/PBO/PSR machinery into the cross-sectional runner.** INTEGRATED — recorded as a **hard, pre-registered build requirement for cycle 4's eventual CONFIRMATION runner** (Section 7). The cross-sectional runner must import and call `validation_v3.psr` and `deflated_sharpe_ratio_v3` on the multi-seed-aggregate OOS monthly-return series, and the QE must document the exact SR granularity fed to `psr()` per `feedback_v3_methodology_post_hoc_input_traceback.md`. `deflated_sharpe_ratio_v3` is documented (lines 463-468) to handle a faint-or-negative SR without clamping — its docstring explicitly warns "the runner must not override its return value with 0.0", and the /092 runner did exactly that override. For PBO: if a genuine 2D-path-matrix PBO is structurally unavailable, the brief's escape clause must be followed *literally* — an honest sentinel emitted *after* the attempt with an explicit structural-reason note, recorded as FAIL — NOT a pre-existing `float("nan")` constant.

**Recommendation 2 — Add a `dsr.json` integration test to the cross-sectional multi-seed test suite.** INTEGRATED — recorded as the **structural fix** (Section 6) and as a **hard requirement for cycle 4's CONFIRMATION runner** (Section 7). The four /092 integration tests cover seed derivation, inner-ensemble distinctness, score-averaging, and aggregate-mean arithmetic — but **none asserts anything about `dsr.json`**. A test asserting the aggregate `dsr.json` `dsr`/`psr` are finite computed values (not `0.0` literals) and that `pbo` is either a genuine fraction or an explicitly-noted structural sentinel would have caught this defect at Phase 6. This is the `feedback_v3_methodology_axis_integration_test.md` discipline applied to the gate that was actually un-tested.

**Recommendation 3 — The engineering report must never narrate a hardcoded constant as a computed result.** INTEGRATED — recorded as a closeout standing rule. Per the /090 closeout and `feedback_v3_methodology_post_hoc_input_traceback.md`, every classification-driving number in an engineering report must be a reproducible runner artifact with a stated code path. A future report stating any DSR/PBO/PSR value must cite the `validation_v3` call-site that produced it, or — for a genuine sentinel — state plainly "hardcoded sentinel, not computed, because [structural reason]; gate recorded FAIL." The corrected DSR/PBO/PSR numbers, when computed on this faint book, will still FAIL the >0.95 / <0.4 thresholds — but as honest computations, not placeholders.

---

## 6. Process lesson — why the /090 defect class recurred at /092, and the structural fix

This is the load-bearing process finding of the /092 closeout, and the QR owns it explicitly.

**The /090 BLOCK defect class recurred at /092 despite the /091 Critic's Recommendation #1** ("falsifier-driving numbers must be reproducible runner artifacts" — written specifically to prevent this recurrence). Why did it recur?

The honest root cause is a **gap in the gate structure, not a lapse in diligence**:

1. **The /091 Critic's Recommendation #1 was addressed "to QR".** It was integrated into the /091 closeout diary and the /092 brief — and the /092 brief *did* honour it: brief Section 4.3 explicitly mandated "/092 is a CONFIRMATION, not an EXPLORATION — so DSR/PBO/PSR are computed for real and are MERGE gates", named the exact `validation_v3` helpers, specified the 15-month OOS PSR input, and even pre-registered the escape clause. **The brief was correct.** The QR's Phase-5 work did not fail.

2. **The defect is a QE Phase-6 implementation gap.** The /092 setup commit `a6217d3` built the multi-seed loop, the inner ensemble, the score-averaging, the per-seed and aggregate reports, and four integration tests — but did **not** build the Section-4.3-mandated DSR/PBO/PSR machinery. It left the EXPLORATION-era hardcoded `0.0`/`NaN` literals in place. Brief Section 4.3 was a load-bearing build item that the Phase-6 build silently omitted.

3. **There is no structural gate that catches "did the QE implement Section 4.3."** The Phase 5.5 gate verifies the *brief* — and the brief was correct, so the Phase 5.5 gate (rightly) passed it. The Phase 5.5 gate does not — and structurally cannot — verify the Phase-6 *build*, because the build does not exist yet when the Phase 5.5 gate runs. The four integration tests the /092 build *did* ship verify what the runner *does* compute (seed derivation, ensemble, aggregate arithmetic) — but **none asserts anything about `dsr.json`**, so the build-completeness gap on the gate machinery shipped untested. The defect fell into the seam between "the brief is verified at Phase 5.5" and "the build is reviewed only at Phase 7.5" — by which point the backtest has already run and the wasted ~4h is sunk.

**The structural fix is the Critic's Recommendation #2 — a `dsr.json` integration test.** A test in `tests/strategies/ml/test_cross_sectional.py` asserting the aggregate `dsr.json` `dsr`/`psr` fields are finite computed values (not `0.0` literals) and that `pbo` is a genuine fraction or an explicitly-noted structural sentinel converts "did the QE implement the DSR/PBO/PSR build item" from an un-checked Phase-6 narrative into a Phase-6 test-suite assertion that fails the build *before* the backtest runs. This is the only durable fix: a process Recommendation addressed "to QR" cannot catch a QE implementation gap; only a test in the build can. **Recorded as a hard, pre-registered requirement for cycle 4's CONFIRMATION runner (Section 7)** so the /090→/092 defect class cannot recur a third time.

---

## 7. THE KEY FORWARD DECISION — close the line on G1/G2; do NOT burn an iteration on a verdict-neutral re-run

The v3 rule states a methodology root-cause BLOCK becomes a NEW iteration with new brief, new code, new backtest. The question this closeout must resolve head-on: does the cross-sectional line require a **corrected-CONFIRMATION re-run** — a redundant ~4h multi-seed backtest purely to compute the DSR/PBO/PSR gates — OR is /092's reproducible G1/G2 NO-MERGE sufficient to close the line, with the DSR/PBO/PSR runner-fix carried forward as a mandatory build requirement for cycle 4's CONFIRMATION runner?

**DECISION: close the cross-sectional `LGBMRanker` line on /092's reproducible G1/G2 NO-MERGE. Do NOT commission a corrected-CONFIRMATION re-run.** The reasoning, weighed explicitly:

1. **The line's verdict is not in doubt — the Critic confirmed it.** The Critic stated, unambiguously, that the G1/G2 verdict (IS +0.0885 / OOS +0.3194 vs the +1.0 floors) "is real and reproducible and would, on its own, cleanly close the line." The BLOCK is a *CONFIRMATION-artifact-completeness* defect, not a verdict reversal. The substantive question — does the cross-sectional momentum-rank line reach a merge-grade book — is answered: NO, on lottery-robust multi-seed evidence, by an order of magnitude.

2. **A corrected re-run produces zero new information about the line's fate.** The Critic itself predicts the corrected DSR/PBO/PSR, computed on this faint book, "will still FAIL the >0.95 / <0.4 thresholds." A re-run would spend ~4h of compute and an iteration slot to convert three FAIL-by-placeholder gates into three FAIL-by-honest-computation gates. The CONFIRMATION-NO-MERGE verdict is *identical* either way — G1/G2 already fail decisively, and CONFIRMATION-MERGE requires the conjunction G1∧...∧G10. The re-run changes the *provenance* of three already-failing gates; it changes nothing about the line.

3. **The v3 "BLOCK → new iteration" rule's spirit is satisfied without a re-run.** The rule exists to prevent a selection-bias re-Critic — re-running a BLOCKED iteration hoping for a better verdict. That risk is absent here: /092 stays BLOCKED regardless, the line stays NO-MERGE regardless, and no re-run can produce a MERGE. There is no verdict to game. The rule's intent — no laundering of a BLOCKED result into a clean one — is honoured by *filing /092 as BLOCKED* (Section 8) and stating plainly that the close rests on G1/G2 and that G4/G5/G6 were never computed. An honest BLOCKED-CONFIRMATION record is not self-deception.

4. **The standing user directive against marginal / time-wasting moves (`feedback_v3_bold_research_mandate.md`) is decisive.** A ~4h backtest that the Critic has *pre-confirmed* cannot change the verdict, run purely to re-label three gates' failure mode, is the definition of a verdict-neutral time-sink. v3's mission is bold research and relentless honest execution — not redundant ceremony. Cycle 4's derivatives-microstructure re-architecture is the high-EV use of the next iteration slot; a corrected /092 re-run is the low-EV use.

5. **The defect is genuinely a build-completeness gap, and the right place to fix it is where it will next matter.** The DSR/PBO/PSR machinery was never needed by the cross-sectional runner before /092 (the /088-091 runs were EXPLORATIONs, where DSR/PSR FAILs are informational per `feedback_v3_dsr_mode_artifact.md`). It will next matter at **cycle 4's eventual CONFIRMATION** — which will run on a different (derivatives-microstructure) runner. Carrying the fix forward as a hard, pre-registered cycle-4-CONFIRMATION build requirement fixes it exactly where it next bites, with no wasted compute on a settled question.

**Therefore — the cross-sectional `LGBMRanker` momentum-rank line is CLOSED, substantively, on /092's reproducible G1/G2 NO-MERGE.** /092 is filed as a BLOCKED CONFIRMATION (Section 8): the substantive verdict (NO-MERGE) is recorded, and the artifact-completeness defect (G4/G5/G6 never computed) is recorded with equal plainness. No corrected re-run is commissioned.

**The DSR/PBO/PSR runner-fix + the `dsr.json` integration test are carried forward as a HARD, PRE-REGISTERED requirement for cycle 4's eventual CONFIRMATION runner** — not as a redundant re-run of a settled question. Concretely, cycle 4's CONFIRMATION runner (whatever runner the derivatives-microstructure architecture produces) MUST, before its CONFIRMATION backtest:
- (a) **import and call** `validation_v3.psr` and `validation_v3.deflated_sharpe_ratio_v3` on the multi-seed-aggregate OOS monthly-return series — genuine CONFIRMATION-grade computations, no hardcoded `0.0`/`NaN` literals (Critic Rec #1);
- (b) ship a **`dsr.json` integration test** asserting the aggregate `dsr.json` `dsr`/`psr` are finite computed values and `pbo` is a genuine fraction or an explicitly-noted structural sentinel (Critic Rec #2);
- (c) the QE engineering report must cite the exact `validation_v3` call-site and SR granularity for every DSR/PBO/PSR number (Critic Rec #3, `feedback_v3_methodology_post_hoc_input_traceback.md`).

This pre-registration is the structural guarantee that the /090→/092 defect class cannot recur a third time.

---

## 8. Phase 7 failure-mode-prediction check (brief Section 7)

The brief Section 7 pre-registered the outcome distribution. Did /092 land where the brief predicted?

- **≈70% modal** — "CONFIRMATION-NO-MERGE, the multi-seed verdict cleanly closes the line": OOS multi-seed-mean monthly Sharpe roughly [−0.20, +0.30], IS roughly [−0.05, +0.25], OOS rank-IC faintly positive (G9 passes), G1/G2 fail decisively.
- **≈15%** — CONFIRMATION-NO-MERGE, net-negative both windows.
- **≈10%** — "CONFIRMATION-NO-MERGE, but one or both outer seeds draw a lucky OOS window... the multi-seed mean is dragged up by one seed but G10 and/or the +1.0 floors still fail."
- **≈5%** — against expectation, CONFIRMATION-MERGE.

**The realized outcome is a blend of the ≈70% modal path and the ≈10% lucky-draw path.** The headline verdict is the ≈70% modal: CONFIRMATION-NO-MERGE, G1/G2 fail decisively, OOS rank-IC faintly positive (G9 PASS) — the multi-seed close of the line. The IS multi-seed mean +0.0885 lands inside the brief's predicted [−0.05, +0.25] IS band. **But the OOS mechanism is the ≈10% lucky-draw path**: the OOS multi-seed mean +0.3194 is at the top of the brief's [−0.20, +0.30] modal band and is *driven by* seed 42's lucky OOS draw (IS ≈ 0, OOS +0.4328, ratio 25.63) — exactly the "one outer seed draws a lucky OOS window, the mean is dragged up but the floors still fail" scenario the brief named at ≈10%.

**Calibration verdict — CLEAN.** The brief did not just predict the headline verdict (CONFIRMATION-NO-MERGE) — it pre-registered the *exact mechanism* that produced the OOS number, including the seed-42 lucky-draw signature, the sub-0.5 `frac_positive_paths`, and the explicit instruction that this "does not change the CONFIRMATION-NO-MERGE verdict" and "must not be rationalized post-hoc." The realized OOS +0.3194 is a textbook instance of the brief's ≈10% named path nested inside the ≈70% modal verdict. The brief's failure-mode prediction was forthright and accurate. The one thing the brief Section 7 did NOT predict is the BLOCK — but the BLOCK is an artifact-completeness defect in the Phase-6 *build*, not an outcome of the *strategy*; brief Section 7 predicts strategy outcomes, and brief Section 8.3 (CONFIRMATION-INCONCLUSIVE) anticipated only a build that "did not reach a runnable two-outer-seed backtest" — which is not what happened (the build ran; it omitted the gate machinery). The Section-7 calibration on the strategy outcome is clean; the build-completeness defect is the Section-6 process lesson, integral to this closeout.

---

## 9. Decision

**NO-MERGE. Critic Phase-7.5 OVERALL = BLOCK** (`briefs-v3/iteration_v3-092/review.md`, FINAL `1140143`; the Critic was NOT re-run — the BLOCK is FINAL). iter-v3/092 classified **CONFIRMATION-NO-MERGE (brief Section 8.2), filed as BLOCKED.** The CONFIRMATION-MERGE conjunction G1∧G2∧G4∧G5∧G6 fails: G1 (IS multi-seed-mean monthly Sharpe +0.0885 vs the +1.0 floor) and G2 (OOS +0.3194 vs the +1.0 floor) FAIL by an order of magnitude on reproducible runner artifacts; G4/G5/G6 (DSR/PBO/PSR) FAIL as hardcoded EXPLORATION-era `0.0`/`NaN` placeholders that were never computed — the BLOCKING defect.

**The honest cross-sectional-line verdict is NO-MERGE, and it is not in doubt.** /092's G1/G2 are reproducible and decisive — the cross-sectional `LGBMRanker` momentum-rank line, in its best-faith form (H=21, 10 models/cell, corrected embargo), multi-seed-validated, reaches IS +0.09 / OOS +0.32 — far short of merge grade. The OOS +0.32 is a SUSPICIOUS-ratio lottery artifact (aggregate OOS/IS 3.61, driven by seed 42's IS ≈ 0 / OOS +0.43 divergence), NOT durable edge. Across five iterations (/088 −0.54 → /089 −0.10 → /090 −0.08 → /091 −0.10 → /092 multi-seed close) the line produced v3's first genuine OOS signal transfer (rank-IC +0.03 to +0.04) but never a merge-grade book. **The cross-sectional `LGBMRanker` momentum-rank architecture is substantively CLOSED as a route to a merge-grade book.** `cross_sectional.py` is RETAINED as code (a working, audited, reusable cross-sectional engine); the momentum-rank strategy on it is closed.

The BLOCK is a **CONFIRMATION-artifact-completeness defect, not a verdict reversal**: three of /092's ten CONFIRMATION gates were never built, and the engineering report narrated the placeholders as computed (false provenance) — the /090 BLOCK defect class recurring. The process lesson (Section 6): the /090-defect class recurred because the /091 Critic's Recommendation #1 was addressed "to QR" while this defect is a QE Phase-6 implementation gap; the Phase 5.5 gate verifies the brief (which was correct), not the Phase-6 build; and the four shipped integration tests assert nothing about `dsr.json`. The structural fix is the Critic's Recommendation #2 — a `dsr.json` integration test that fails the build before the backtest runs.

**THE KEY FORWARD DECISION (Section 7): the cross-sectional line is CLOSED on /092's reproducible G1/G2 NO-MERGE; NO corrected-CONFIRMATION re-run is commissioned.** A re-run would burn ~4h of compute and an iteration slot to convert three FAIL-by-placeholder gates into three FAIL-by-honest-computation gates — the Critic itself pre-confirms the corrected DSR/PBO/PSR "will still FAIL the thresholds," so the CONFIRMATION-NO-MERGE verdict is identical either way. The v3 "BLOCK → new iteration" rule's spirit (no selection-bias re-Critic) is satisfied: /092 stays BLOCKED regardless, no re-run can produce a MERGE, and the close is recorded honestly (G1/G2 reproducible; G4/G5/G6 never computed). The standing directive against marginal moves (`feedback_v3_bold_research_mandate.md`) is decisive — a verdict-neutral re-run is a time-sink. **The DSR/PBO/PSR runner-fix + the `dsr.json` integration test are carried forward as a HARD, PRE-REGISTERED requirement for cycle 4's eventual CONFIRMATION runner** (Section 7 (a)/(b)/(c)) — the structural guarantee the /090→/092 defect class cannot recur a third time.

**BASELINE_V3.md is UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791), tag `v0.v3-059`. A BLOCKED CONFIRMATION never updates the baseline; a CONFIRMATION-NO-MERGE never updates it regardless. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched — the QR saw OOS for the first time in Phase 7.

**iter-v3/092 CLOSES CYCLE 3.** The cycle-3 CONFIRMATION slot is filled; the /082-091 10-EXPLORATION cadence + the /092 CONFIRMATION complete cycle 3. The cycle-3 retrospective stands as the /091 closeout recorded it: zero clean PROMISING results across all 10 EXPLORATIONs; both architectures v3 has explored — per-symbol absolute-barrier LightGBM (/082-087) and cross-sectional momentum-rank `LGBMRanker` (/088-092) — are tapped out as routes to a merge-grade book.

**THE FORWARD PLAN — CYCLE 4 opens at iter-v3/093 with the derivatives-microstructure re-architecture.** Cycle 4 is a genuine RE-ARCHITECTURE into a new signal class — **Candidate A, the derivatives-microstructure state-conditioning architecture** (a funding-rate / open-interest / liquidation regime model), the only candidate that attacks the structural fact uniting every v3 failure: *every prior v3 architecture predicted from price-derived features only*. The cycle-4 prep memo (`briefs-v3/cycle4_prep_memo.md`, committed with this closeout) resolved the critical de-risking question — **the data is available**: funding rates already fetched (25 symbols, 2019/2020→2026), perp-spot basis already fetched (23 symbols), open interest + long/short ratios fetchable from data.binance.vision's `metrics` archive (verified full v3-window coverage; the prerequisite is a small `fetch-oi` CLI subcommand at /093 setup). The /093 QR formalizes the /093 brief from the prep memo, with a derivatives-data EDA committed before the brief per `feedback_v3_axis_selection_quant_discipline.md`, and frames the brief around **regime AVOIDANCE, not carry collection** (the crypto carry trade turned negative in 2025 — a naive long-carry book would be backtested on its graveyard). **Cycle 4's CONFIRMATION runner MUST carry genuine CONFIRMATION-grade DSR/PBO/PSR (Critic Rec #1) + a `dsr.json` integration test (Critic Rec #2) — a hard, pre-registered requirement (Section 7).** Candidate B (crypto statistical arbitrage, zero new data) and Candidate C (regime-switching TSMOM) are recorded fallbacks.

A separate QR evaluation memo on the user's "custom-made features per symbol" idea (`briefs-v3/per_symbol_features_user_idea_memo.md`, committed with this closeout) records: the literal idea is a NO (per-symbol LightGBM gain-importance rankings are highly concordant across BCH/LDO/TRX — mean pairwise Spearman ρ = +0.839 — the shared feature set is already near-optimal per-symbol; univariate "divergence" is fully explained by sample noise); a QUALIFIED YES, LOW priority, for symbol-conditional features inside a pooled cross-sectional ranker. The memo persists into cycle 4 for the /093 QR.

A CONFIRMATION closeout marker tag `v0.v3-092` is issued (annotated; NOT a baseline update — the `v0.v3-082`…`v0.v3-091` pattern; BASELINE_V3.md UNCHANGED at `v0.v3-059`).

---

**Commit chain:**
- Setup SHA: `a6217d3` — `ITERATION_LABEL "v3-092"`; `CONFIRMATION_OUTER_SEEDS = (42, 123)`; the `--seeds` count argument; the multi-seed outer-seed loop + 5-model inner ensemble + score-averaging + per-seed and aggregate reports + `ensemble_summary.json` + the 2-seed Pareto boolean + four integration tests. (Did NOT build the Section-4.3 DSR/PBO/PSR machinery — the Item-4 BLOCK defect.)
- Brief SHA: `briefs-v3/iteration_v3-092/research_brief.md` — the multi-seed CONFIRMATION-grade closing-verdict brief; brief Section 11 SHA backfill `2b996fd`.
- Phase 5.5 gate SHA: `1236e3c` (PASS — the QE independent Phase-5.5 gate; verified the brief, which was correct).
- Engineering report SHA: `briefs-v3/iteration_v3-092/engineering_report.md` + backtest results (multi-seed mean IS +0.0885 / OOS +0.3194).
- Critic FINAL SHA: `1140143` — `briefs-v3/iteration_v3-092/review.md` — **OVERALL=BLOCK** (Items 1-3 PASS; Item 4 — DSR/PBO/PSR hardcoded EXPLORATION-era placeholders, never computed — the BLOCK; 3 Recommendations).
- Diary + catalog + memos SHA: this closeout — `docs(iter-v3/092): closeout diary + catalog + cycle-3 close — CONFIRMATION-NO-MERGE (BLOCKED) / Critic OVERALL=BLOCK`.
- **Reports**: `reports-v3/iteration_v3-092/` (the multi-seed aggregate) + `reports-v3/iteration_v3-092/seed_42/` + `reports-v3/iteration_v3-092/seed_123/` (the per-outer-seed reports).
- **Tag**: `v0.v3-092` (CONFIRMATION closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`).
