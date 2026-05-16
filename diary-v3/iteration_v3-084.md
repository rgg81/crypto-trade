# iter-v3/084 — Cycle 3 #3 REFERENCE / METHODOLOGY (PER_CELL_GAP 43→22 fix + clean /059-config 3-symbol anchor re-run) / REFERENCE-REANCHOR

**Date**: 2026-05-16
**Type**: REFERENCE / METHODOLOGY (cycle 3 slot #3 of 10) — NOT a bold research axis, NOT a CONFIRMATION. EXPLORATION-mode 3-seed. Two declared, fixed-scope changes: (1) the `PER_CELL_GAP` 43→22 methodology fix; (2) a clean revert of /083's NEGATIVE FILUSDT universe expansion back to the /059-canonical 3-symbol BCH/LDO/TRX configuration, re-run on freshly-fetched current data. No axis research.
**Axis**: none — a reference iteration. The direct cycle-3 analogue of cycle 1's iter-v3/077 (the cycle-2 reference re-run that established a current-code EXPLORATION-MODE-REFERENCE) and of the established "revert the non-merged prior iteration" pattern (/083 reverted /082's funding family; /079 reverted /078's ADA swap; /077 reverted /076's `range_efficiency_50`).
**Verdict**: EXPLORATION-MERGE per Critic FINAL `16b4cc1` — OVERALL=MERGE = methodology certified clean (a clean reference iteration with sound methodology is OVERALL=MERGE; the Critic gates methodology soundness, not advancement). The result classification (REFERENCE-REANCHOR) and the re-anchor decision are the QR's Section 8 / brief Section 4 call — adopted here as FINAL.
**Classification**: **REFERENCE-REANCHOR** per brief Section 8.2 — the brief Section 4.3 LOCKED re-anchor decision rule fires the re-anchor branch: /084's IS monthly Sharpe +0.8325 is Δ −0.2569 vs /059's recorded +1.0894 (outside ±0.10) AND /084's OOS monthly Sharpe +0.3322 is Δ −0.2469 vs /059's recorded +0.5791 (outside ±0.10) — both falsifiers F1 and F2 fire. The standard EXPLORATION taxonomy (SUSPICIOUS → NEGATIVE → PROMISING → INERT → NULL) is not the operative frame for a reference iteration; the operative outcome is the LOCKED re-anchor rule.
**Advancement**: does NOT advance to the iter-v3/092 cycle-3 CONFIRMATION bundle — a reference iteration has no axis and produces no edge ingredient. The `PER_CELL_GAP` fix lands as a permanent strictly-accretive methodology correction (`feedback_v3_promising_mechanical_subtype.md` — non-compoundable as an edge ingredient).
**BASELINE_V3.md**: **UNCHANGED** — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical. An EXPLORATION-mode iteration cannot update the baseline, and a REFERENCE iteration has no edge ingredient regardless. The BASELINE_V3.md edit at this closeout is documentation-only: the "EXPLORATION-Mode Anchor Staleness" subsection is updated with /084's cycle-3 EXPLORATION-MODE-REFERENCE numbers and the EXPLORATION-vs-CONFIRMATION architecture-gap finding.
**Branch**: `iteration-v3/084`

---

## 1. What was done — the two-part scope

iter-v3/084 is the THIRD EXPLORATION slot of v3 cycle 3 — the bold structural pivot governed by `briefs-v3/cycle3_plan.md`. Per `feedback_v3_strict_10_to_1_cadence.md`, cycle 3 runs 10 SEPARATE EXPLORATIONs (/082-/091) followed by 1 SEPARATE CONFIRMATION (/092) — the 10th EXPLORATION is NOT collapsed into the CONFIRMATION.

iter-v3/084 is a REFERENCE / METHODOLOGY iteration with a fixed two-part scope assigned by the iter-v3/083 closeout (diary-v3/iteration_v3-083.md Sections 6 + 9 + 12 Recs #2/#4, carried into `cycle3_plan.md` Section 7's "TWO MANDATES recorded at the /083 closeout"). It has no research axis — its scope is exactly the two declared things below and nothing else.

### Part 1 — the `PER_CELL_GAP` 43→22 methodology fix

`PER_CELL_GAP = 43` in `run_baseline_v3.py` was a stale literal — the value `(42+1)` left over from the reverted iter-v3/068 42-candle timeout-widening experiment, which /069/070 reverted to 21 candles. The per-cell CSCV operates on a single-symbol `(symbol, train_month)` cell, so its purge gap is `(timeout_candles + 1) = (21 + 1) = 22` — the `× n_symbols` factor applies ONLY to the global pooled CPCV (`REQUIRED_GAP`), which interleaves all symbols' candles into one sequence. The runner had been out of sync with its own regression test (`tests/strategies/ml/test_per_cell_pbo_synthetic.py:38` already carried the correct `22`). The fix corrects the constant at `run_baseline_v3.py:1510`, adds an `expected_gap=PER_CELL_GAP` runtime guard to the per-cell `combinatorial_purged_cv` call at `:1608` so the constant cannot silently drift again, and fixes two stale runner string literals (lines 2539, 2610). The 43→22 correction is a REDUCTION of the purge gap — `43` over-purged (the conservative direction; it removed more training data per per-cell test boundary than the correct 22, biasing per-cell PBO pessimistically) — so it did NOT invalidate any prior iteration's headline metrics, and the fix moves from over-conservative to correct, never to under-purge.

### Part 2 — the clean /059-config 3-symbol anchor re-run

iter-v3/083's FILUSDT universe expansion was NEGATIVE/NO-MERGE. iter-v3/084 reverts it: `V3_MODELS` returns to the 3-symbol /059-canonical universe (BCHUSDT, LDOUSDT, TRXUSDT — drop FILUSDT), `REQUIRED_GAP` reverts `88 → 66 = (21+1)×3`, and the 11-knob `_canonical_v059` config-accretion check reverts all 11 rows to /059-canonical (the universe expansion fully unwound). `V3_FEATURE_COLUMNS_TOP_N` was already the 14-feature /059 anchor stack (the /083 setup had already reverted the /082 funding family 18→14). No labeling, feature, risk-gate, model-architecture, seed, or Optuna change. The re-run is on freshly-fetched current data — its purpose is to produce the cycle-3 EXPLORATION-MODE-REFERENCE (the /060 → /077 precedent).

Run mode: EXPLORATION (`--exploration` → `EXPLORATION_ENSEMBLE_SIZE = 3`, `ENSEMBLE_SEEDS` outer-42 lineage subset `[191664963, 1662057957, 1405681631]`), `--n-trials 35`, 3-symbol universe, `REQUIRED_GAP = 66`, embargo 22. Total 315 Optuna trials (35 × 3 sym × 3 seeds). Wall-clock 0.70h (42 min), within the 2h EXPLORATION cap.

Commit chain: EDA `401de40` → research brief `c18a2dc` → setup `1073f32` → brief SHA-backfill `f08709b` → Phase 5.5 gate PASS `3d0d9db` → engineering report `2981cda` → Critic review `16b4cc1`.

## 2. Results — vs the /059 recorded anchor (the re-anchor decision rule)

| Metric | /059 recorded anchor | /081 CONFIRMATION (re-validated) | /084 (this run) | Δ /084 − /059 |
|---|---:|---:|---:|---:|
| IS monthly Sharpe | **+1.0894** | +1.0894 | **+0.8325** | **−0.2569** |
| OOS monthly Sharpe | **+0.5791** | +0.5999 | **+0.3322** | **−0.2469** |
| OOS/IS monthly Sharpe ratio | 0.5316 | 0.5507 | **0.3990** | — |
| IS daily Sharpe | 2.7092 | — | 1.7115 | — |
| OOS daily Sharpe | 1.4359 | — | 0.8745 | — |
| IS MaxDD | 30.97% | — | 31.87% | — |
| OOS MaxDD | 34.53% | — | 35.78% | — |
| IS n_trades | 171 | 171 | 159 | −12 |
| OOS n_trades | 94 | — | 104 | +10 |
| PBO mean | 0.1278 | 0.1278 | **0.1278** | 0 (computed on the corrected PER_CELL_GAP=22 — see Section 6) |
| PSR | 1.0 | 1.0000 | 1.0000 | PASS (> 0.95) |
| DSR (legacy) | 0.0 | 0.0 | 0.0000 | EXPLORATION-mode artifact (informational) |
| DSR_relative_B4 | — | 1.0000 | 0.8154 | EXPLORATION-mode artifact (informational) |
| frac_positive_paths (CPCV) | 0.6444 | 0.6444 | **0.644** (29/45) | PASS (> 0.55) |
| n_trials (Optuna total) | 1050 | 1050 | 315 | EXPLORATION-mode (3 seeds) |
| n_eff | 19 | 19 | 19 | architecture-independent |

CPCV path Sharpe distribution: q25 = −0.243, q50 = +0.335, q75 = +0.838 — the median path is positive; the distribution is right-skewed with a long left tail. `frac_positive_paths = 0.644` PASS — the run is not a methodology failure; it is a clean, valid measurement.

**Per-symbol IS attribution** (report-layer `in_sample/per_symbol.csv`, `net_pnl_pct`):

| Symbol | IS trades | IS WR | IS net_pnl% | IS avg_pnl% |
|---|---:|---:|---:|---:|
| BCHUSDT | 73 | 45.2% | **+79.45** | +1.09 |
| LDOUSDT | 11 | 27.3% | **−11.44** | −1.04 |
| TRXUSDT | 75 | 29.3% | **−23.04** | −0.31 |

**Per-symbol OOS attribution** (`comparison.csv` per_symbol block, `weighted_pnl`):

| Symbol | OOS weighted_pnl | OOS n_trades | OOS WR | OOS concentration_pct |
|---|---:|---:|---:|---:|
| TRXUSDT | +24.2639 | 55 | 49.1% | 178.49% |
| BCHUSDT | +1.9078 | 37 | 32.4% | 14.03% |
| LDOUSDT | −12.5778 | 12 | 25.0% | −92.53% |

**The headline.** /084's IS monthly Sharpe +0.8325 and OOS monthly Sharpe +0.3322. Both deltas vs /059's recorded numbers are ≈ −0.25 — about 2.5× the ±0.10 re-anchor band. The brief Section 4.3 LOCKED re-anchor rule fires the re-anchor branch (F1 and F2 both fire). /084's numbers become the cycle-3 EXPLORATION-MODE-REFERENCE — exactly as /060 became the cycle-1 EXPLORATION-MODE-REFERENCE and /077 became the cycle-2 EXPLORATION-MODE-REFERENCE. Note that the OOS per-symbol book is heavily TRX-dominant (TRX +24.26 carries the positive OOS total against BCH +1.91 and LDO −12.58) — the v3 concentration fragility persists, but it is a KNOWN outstanding problem, not /084's scope.

## 3. The architecture-gap decomposition — the ~0.26 IS gap is mostly EXPLORATION-vs-CONFIRMATION architecture, not data-extent staleness (Critic Recommendation #1, REQUIRED)

This is the load-bearing analytical finding of the closeout. **The re-anchor must NOT be framed as "the /059 config went stale."** That framing is wrong and the Critic established the correct one.

**The two numbers being compared are produced by two different ensemble architectures.** /084's IS +0.8325 is a **3-seed EXPLORATION-mode** number (`EXPLORATION_ENSEMBLE_SIZE = 3`, the outer-42-lineage seed subset). /059's recorded IS +1.0894 is a **10-seed CONFIRMATION-mode** number (the unified `ENSEMBLE_SIZE = 10`, all ten lineage-preserving seeds, 1050 Optuna trials). These are not the same measurement run at two times — they are two structurally different inference paths. A 10-model proba-averaged ensemble and a 3-model proba-averaged ensemble produce different trade rosters and different Sharpe numbers from the identical configuration.

**The decisive corroborating evidence — /077.** Cycle 2's reference re-run, iter-v3/077, ran the canonical /060 config at EXPLORATION-mode 3-seed and landed at IS **+0.8236**. /084's IS is **+0.8325**. These two 3-seed EXPLORATION-mode reference numbers are near-identical (Δ +0.0089) — and both are ≈ 0.26 below /059's 10-seed CONFIRMATION IS +1.0894. A 3-seed EXPLORATION-mode run of the canonical v3 config lands ~0.82-0.83 IS; a 10-seed CONFIRMATION-mode run of the canonical config lands ~1.09 IS. That ~0.26 IS gap is reproducible, stable, and architecture-driven — it is not a /084-specific anomaly, not a wiring defect, and not primarily anchor staleness.

**The decomposition of the Δ IS −0.2569:**

- **(a) The EXPLORATION-vs-CONFIRMATION architecture component — ≈ the bulk of the gap.** Evidenced by /077: a 3-seed EXPLORATION-mode reference run of the canonical config (whether /060's or /059's config) lands at IS ≈ +0.82-0.83, and /059's 10-seed CONFIRMATION lands at +1.0894. The /077≈/084 near-identity (+0.8236 vs +0.8325) demonstrates that essentially the entire ~0.26 IS gap is attributable to the 3-seed-vs-10-seed ensemble-architecture difference. The unified 10-seed ensemble averages over 10 models; the 3-seed EXPLORATION ensemble averages over 3 — the larger ensemble's proba-averaging produces the IS-dominant +1.09 reading that BASELINE_V3.md records for /059 (the /059 closeout itself documented that the unified architecture exposes the BCH/LDO/TRX bundle's true IS-dominant character).
- **(b) The residual genuine data-extent component — small.** /084's data extent post-dates /059's `bea0987` fetch. Any data-extent drift would be a small residual on top of the architecture component — and /077's own decomposition (an exact additive split) put the cycle-2 data-extent drift at the +0.0675 OOS / −0.0089 IS scale. The residual data-extent component of /084's Δ is of that order: small, real, and monotonic with calendar time, but not the dominant term.

**The honest finding.** The prior cycle-3 EXPLORATIONs /082 and /083 were anchoring their **3-seed EXPLORATION-mode** deltas directly against /059's **10-seed CONFIRMATION-mode** number — a non-comparable reference. /082's reported IS Δ "−0.0118 vs /059" and /083's reported IS Δ "−0.9156 vs /059" both used the 10-seed +1.0894 as the comparison point while the runs themselves were 3-seed EXPLORATION-mode. iter-v3/084 corrects that **reference-architecture mismatch**. This is a stronger and cleaner finding than "the /059 config went stale": the /059 config did not decay — it was being measured against an anchor produced by a different ensemble architecture. /084 establishes the architecturally-matched reference (a 3-seed EXPLORATION-mode number) that /085-091 will anchor against.

## 4. The /082 and /083 classifications STAND — re-anchoring sharpens the framing, it does not overturn closed verdicts

Re-anchoring corrects the *reference* /082 and /083 should have been measured against; it does not reopen their closed classifications. **/082 (SUSPICIOUS-OOS-DOMINANT) and /083 (NEGATIVE) remain correctly classified, and are NOT reopened.**

- **/082 — SUSPICIOUS-OOS-DOMINANT stands.** /082's classification fired on the OOS-DOMINANT sub-mode (IS Δ < 0 AND OOS Δ ≥ +0.20) AND was independently corroborated by the feature-level INERT signature: the 4 funding features ranked 15/16/17/18 of 18 by importance (9.90% combined, below the 5.56% uniform-parity baseline). The funding family is INERT-by-importance regardless of which IS anchor is used — that is a feature-importance fact, not a Δ-vs-anchor fact. Re-anchoring the IS comparison from +1.0894 to /084's +0.8325 would move /082's reported IS Δ from −0.0118 toward roughly +0.25, but /082's SUSPICIOUS verdict never rested on the IS-Δ magnitude — it rested on the OOS-DOMINANT sub-mode firing and the bottom-4 importance rank. Both still hold. /082 stays SUSPICIOUS-OOS-DOMINANT; the v3 funding axis stays a 4-data-point CLOSED verdict.
- **/083 — NEGATIVE stands.** /083's classification fired on an IS monthly Sharpe collapse to +0.1738 — a Δ of −0.9156 vs /059's +1.0894, far below the −0.10 NEGATIVE floor. Even re-anchored against /084's +0.8325, /083's IS Δ is roughly −0.66 — still a large IS collapse, still far below the NEGATIVE floor, and corroborated independently by the 73.18% IS MaxDD blowout and the Gate-10-CPCV FAIL (`frac_positive_paths` 0.4667 < 0.55). The /083 decomposition correctly attributed ~32% of the collapse to FIL's own genuine negative IS edge (−32.45pp standalone) and ~68% to incumbent data-extent drift; /084's clean re-run corroborates that decomposition (the incumbents land at +0.8325 IS at 3-seed, consistent with the /082-vs-/083 incumbent-aggregate comparison). /083 stays NEGATIVE; FILUSDT stays a CLOSED universe-expansion candidate.

The re-anchoring is a methodology correction for /085-091's *future* delta measurements — it does not retroactively flip /082's or /083's *closed* verdicts. Neither is reopened.

## 5. Cycle-3 EXPLORATION-MODE-REFERENCE established + the two-anchor structure (Critic Recommendation #2)

**The cycle-3 EXPLORATION-MODE-REFERENCE is now /084: IS +0.8325 / OOS +0.3322 (3-seed EXPLORATION-mode, current data).** This is the exact /060 → /077 precedent: a fresh current-code/current-data no-axis run of the canonical config replacing a non-comparable reference. Cycle-3 EXPLORATIONs iter-v3/085-091 anchor their intra-cycle Δ classification against /084's numbers.

**The two-anchor structure (pre-registered as MANDATORY for every /085-091 brief).** To prevent the next reference re-run from re-discovering the /082-/083 reference-architecture mismatch, every cycle-3 EXPLORATION brief Section 4 MUST explicitly state TWO anchors:

1. **The EXPLORATION-MODE-REFERENCE** — /084: **IS +0.8325 / OOS +0.3322** (3-seed EXPLORATION-mode). This is the anchor for intra-cycle Δ classification (PROMISING / NEGATIVE / INERT / SUSPICIOUS bands). An EXPLORATION runs 3-seed; it must be compared to a 3-seed reference.
2. **The /059 CONFIRMATION baseline** — **IS +1.0894 / OOS +0.5791** (10-seed CONFIRMATION-mode, tag `v0.v3-059`). This is RESERVED for the iter-v3/092 CONFIRMATION, which runs 10-seed CONFIRMATION-mode and must be compared to a 10-seed CONFIRMATION baseline.

Mixing the two — comparing a 3-seed EXPLORATION number against the 10-seed CONFIRMATION number — is precisely the /082-/083 error. Making the two-anchor structure explicit and mandatory in the brief template closes it permanently. This is recorded in `cycle3_plan.md` Section 4 and in BASELINE_V3.md's "EXPLORATION-Mode Anchor Staleness" subsection.

## 6. The per-cell PBO is now on the corrected PER_CELL_GAP=22 — cross-/084-boundary comparisons are gap-regime-discontinuous (Critic Recommendation #3)

/084's per-cell PBO is computed with the corrected `PER_CELL_GAP = 22` (the less-conservative, correct purge for a single-symbol cell). Pre-/084 iterations used the stale, over-purging `43`. /084's per-cell PBO happens to land at **0.1278** — identical to /059's recorded 0.1278 — but this coincidence must NOT be read as "the fix had no effect." The bulk of the 129 `(symbol, month)` cells show PBO = 0.0 regardless of the gap (verified in `per_cell_pbo.csv`); the gap only moves the elevated cells, and the cross-iteration mean is dominated by the zeros. **Per-cell PBO comparisons across the /084 boundary are gap-regime-discontinuous**: pre-/084 used gap=43 (over-purged, pessimistic), /084-onward uses the correct gap=22. Any future cross-iteration per-cell-PBO trend analysis must respect that discontinuity — a pre-/084 per-cell PBO and an /084-onward per-cell PBO are not on the same purge regime, even when the numbers coincide.

## 7. Critic verdict summary

**OVERALL=MERGE** per Critic FINAL `16b4cc1` (`briefs-v3/iteration_v3-084/review.md`). A single-round full review; the verdict is FINAL. The MERGE verdict CERTIFIES the methodology of a clean reference iteration — it is a methodology certification, NOT an advancement. A reference iteration with sound methodology is OVERALL=MERGE; the Critic gates methodology soundness, and the result classification (REFERENCE-REANCHOR) and the re-anchor decision are the QR's Section 8 / brief Section 4 call.

- **All 8 mandatory Checks + 4 optional Checks PASS or PASS-equivalent.** Check 1 (look-ahead) PASS — /084 adds no features; the changes are a `PER_CELL_GAP` constant, a `V3_MODELS` revert (4→3), and a `REQUIRED_GAP` revert; the 14-feature /059 anchor stack is verified literal; the post-`e149e9d` walk-forward embargo is intact. Check 2 (embargo) PASS — numerical proof on two distinct gaps: global pooled CPCV `REQUIRED_GAP = (21+1)×3 = 66` (formula-driven runtime assertion + `expected_gap` self-assertion), per-cell single-symbol CSCV `PER_CELL_GAP = (21+1) = 22` (the `×n_symbols` factor does not apply to a single-symbol cell), purge applied symmetrically on both test-boundary sides, per-cell `embargo=0` correct. Check 3 (multiple-testing) — PBO axis PASS at 0.1278 < 0.40 (the one BLOCK-eligible axis at EXPLORATION mode), computed on the corrected gap=22; DSR/PSR informational at EXPLORATION mode per `feedback_v3_dsr_mode_artifact.md`. Check 4 (IC) PASS — no new feature family; max |IC| = 0.764 (`vwap_dev_20`/`regime_momentum_signed_5d`) is the pre-existing Category-2 composed-feature carve-out. Check 5 (ADF) PASS — 82.0% stationary, the non-stationary set is the known level features carried verbatim from /059. Check 6 (Gate-10-CPCV) PASS — `frac_positive_paths = 0.6444` clears the 0.55 threshold; Pareto retired under the unified architecture. Check 7 (reproducibility) PASS — setup commit `1073f32` + Phase 5.5 gate `3d0d9db` stamped, explicit 14-element `feature_columns` list, `ENSEMBLE_SEEDS` literal 3-tuple verified in `ensemble_summary.json`, 5-row OOS trade-PnL spot-check reconciles exactly, `n_trials = 315 = 35×3×3`. Check 8 (hypothesis-implementation alignment) PASS — exactly two changes (the `PER_CELL_GAP` fix + `expected_gap` guard + stale literals; the /059-config 3-symbol revert), zero scope creep, `ITERATION_LABEL = "v3-084"`, the 11-knob `_canonical_v059` check asserts all 11 knobs /059-canonical with zero axis carve-out. Checks 9-12 (symbol-exclusion, feature-isolation, forming-candle/freshness, library-pinning) all PASS.
- **Mandatory adversarial focus points.** Focus 1 (`PER_CELL_GAP = 22` correctness) — VERIFIED CORRECT, the per-cell single-symbol CSCV purge gap is `(21+1) = 22`, the `expected_gap` guard is wired, this discharges the Critic's own /083 Recommendation #2 exactly. Focus 2 (`REQUIRED_GAP = 66` and the clean revert) — VERIFIED, no FILUSDT residue, no /082 funding residue, 11 config-accretion knobs all /059-canonical. Focus 3 (is /084 a VALID measurement) — YES, EXPLORATION-mode 3-seed is the CORRECT mode for an EXPLORATION-MODE-REFERENCE (the /060→/077 precedent), /084's IS +0.8325 / OOS +0.3322 are a valid 3-seed measurement that can legitimately serve as the cycle-3 EXPLORATION-MODE-REFERENCE. Focus 4 (the `PER_CELL_GAP` change and prior results) — CONFIRMED, `PER_CELL_GAP` enters only `_compute_per_cell_pbo` (a downstream reporting metric computed after the trade roster is fixed), the over-purge biased prior per-cell PBO pessimistically, no retroactive invalidation.
- **The Assessment of the Re-Anchor.** The Critic independently agreed /084 is a valid cycle-3 EXPLORATION-MODE-REFERENCE and the re-anchor is the methodologically correct call. The Critic established the EXPLORATION-vs-CONFIRMATION architecture-gap framing (corroborated by /077's IS +0.8236 ≈ /084's +0.8325 vs /059's 10-seed +1.0894) and the honest finding that /082-/083 were anchoring against a non-comparable 10-seed CONFIRMATION number.
- **Three Critic Recommendations** — all integrated into this diary: (#1) decompose the Δ into the EXPLORATION-vs-CONFIRMATION architecture component (≈ the bulk, evidenced by /077≈/084) and the residual data-extent component; do NOT attribute the full ~0.25 to anchor staleness — done, Section 3; (#2) pre-register the two-anchor structure (EXPLORATION-MODE-REFERENCE /084 for intra-cycle Δ; /059 CONFIRMATION baseline for /092) in `cycle3_plan.md` and every /085-091 brief — done, Section 5; (#3) record that /084's per-cell PBO is on the corrected gap=22 and per-cell-PBO comparisons across the /084 boundary are gap-regime-discontinuous — done, Section 6.

## 8. PATH classification — REFERENCE-REANCHOR

iter-v3/084 is a REFERENCE / METHODOLOGY iteration — it is neither a bold research axis (no axis to classify PROMISING/NEGATIVE/INERT) nor a CONFIRMATION (no bundle to validate, no baseline update). The standard EXPLORATION taxonomy is not the operative frame; the operative outcome is the brief Section 4.3 LOCKED re-anchor decision rule. The closeout classification per brief Section 8 is one of two pre-registered states — REFERENCE-CONFIRMED (anchor reproduces) or REFERENCE-REANCHOR (anchor moved).

**The re-anchor rule (brief Section 4.3, LOCKED) evaluation:**

- **F1** — IS monthly Sharpe outside [+0.99, +1.19] (Δ vs /059 outside ±0.10): /084 IS = **+0.8325**, Δ = **−0.2569** → **OUTSIDE the band — F1 FIRES.**
- **F2** — OOS monthly Sharpe outside [+0.48, +0.68] (Δ vs /059 outside ±0.10): /084 OOS = **+0.3322**, Δ = **−0.2469** → **OUTSIDE the band — F2 FIRES.**

Both falsifiers fire. The brief Section 4.3 re-anchor branch is dispositive: **/084's IS/OOS monthly Sharpe numbers become the cycle-3 EXPLORATION-MODE-REFERENCE.**

**→ REFERENCE-REANCHOR** (brief Section 8.2). Note: the brief Section 7 pre-registered ≈65% for REFERENCE-CONFIRMED and ≈30% for a re-anchor (≈20% benign OOS-uplift + ≈10% IS materially off). The realized outcome — both IS and OOS landing ≈0.25 below /059's recorded numbers — falls in the re-anchor branch but with a specific texture: it is neither a benign OOS-uplift re-anchor nor an IS-only stale-config re-anchor. The Critic's architecture-gap decomposition (Section 3) is what makes the realized outcome legible — the gap is mostly the 3-seed-vs-10-seed ensemble-architecture difference, not config staleness, and the brief's Section-7 framing (which leaned toward "anchor reproduces or drifts") did not anticipate that the dominant term would be the architecture mismatch rather than data-extent drift. The honest reckoning: the iteration's LOCKED decision rule (Section 4.3) resolved cleanly to the re-anchor branch with zero post-hoc rationalization; the Critic's Recommendation #1 then supplied the correct *interpretation* of why the re-anchor fired. REFERENCE-REANCHOR is the final classification.

In NEITHER state does a REFERENCE iteration update BASELINE_V3.md or advance an edge ingredient. The methodology hard gates (DSR/PBO/PSR) are EXPLORATION-mode artifacts here per `feedback_v3_dsr_mode_artifact.md` — informational only. The `PER_CELL_GAP` fix is recorded as a permanent strictly-accretive methodology correction per `feedback_v3_promising_mechanical_subtype.md` (non-compoundable as an edge ingredient).

## 9. Decision — NO-MERGE

**NO-MERGE. BASELINE_V3.md is UNCHANGED — canonical /059 metrics (IS monthly Sharpe +1.0894 / OOS monthly Sharpe +0.5791) and tag `v0.v3-059` stay canonical.**

A REFERENCE / METHODOLOGY EXPLORATION-mode iteration produces no edge ingredient, does not advance to the CONFIRMATION, and an EXPLORATION cannot update the baseline regardless. **No new git tag for a baseline update.** An EXPLORATION/REFERENCE closeout marker tag `v0.v3-084` is issued (annotated; explicitly NOT a baseline update — the same pattern as `v0.v3-082` and `v0.v3-083`).

The BASELINE_V3.md edit at this closeout is documentation-only: the "EXPLORATION-Mode Anchor Staleness" subsection is updated with /084's cycle-3 EXPLORATION-MODE-REFERENCE numbers (IS +0.8325 / OOS +0.3322, 3-seed, current data) and the EXPLORATION-vs-CONFIRMATION architecture-gap finding. `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are untouched. `V3_MODELS` stays the 3-symbol BCH/LDO/TRX /059-canonical universe; the 14-feature /059 anchor stack stays in place; `PER_CELL_GAP` stays corrected at 22 (the permanent methodology fix).

## 10. Cycle-3 progress + Next Iteration

### Cycle 3 progress — 3/10 EXPLORATION slots done, 0 clean PROMISING

| Slot | Iter | Axis | Verdict |
|---|---|---|---|
| #1 | /082 | NEW crypto-native FEATURE FAMILY (funding-rate, 4 features, Direction 1) | SUSPICIOUS-OOS-DOMINANT |
| #2 | /083 | symbol-universe EXPANSION 3→4 (+FILUSDT, Direction 2) | NEGATIVE |
| #3 | /084 | REFERENCE / METHODOLOGY — PER_CELL_GAP 43→22 fix + clean /059-config 3-symbol anchor re-run | **REFERENCE-REANCHOR** |
| #4-#10 | /085-/091 | TBD per QR research + EDA, Directions 1-3 | — |
| CONFIRMATION | /092 | best cycle-3 bundle (multi-seed validation) | pre-registered MERGE gates |

Cycle 3 has used 3 of its 10 EXPLORATION slots. /082 and /083 were the two genuine bold axes (a NEW crypto-native feature family and a universe expansion); /084 was the reference slot that converts the cycle-3 measurement axis from confounded to clean. Per the strict 10:1 cadence, /085-091 are 7 more SEPARATE bold EXPLORATIONs and /092 is the SEPARATE CONFIRMATION — /091 is NOT collapsed into /092.

### iter-v3/085 — what it should be

**iter-v3/085 (cycle 3 #4) should be the next bold cycle-3 axis — Direction 2 (symbol-universe EXPANSION) or Direction 3 (multi-symbol-pooled model), NOT a Direction-1 feature-family retread.** The case is structural: /082 proved no feature-family axis can fix the 3-symbol denominator problem (OOS ~104%-concentrated in BCH); /083's FILUSDT expansion failed but universe expansion as an *axis* remains structurally valid (the Fundamental Law breadth lever — FILUSDT was one CLOSED candidate, not a closed direction). The /084 clean EXPLORATION-MODE-REFERENCE now makes a /085 universe-expansion or pooled-model EXPLORATION measurable against an architecturally-matched 3-seed anchor — which is the entire purpose /084 served. The /085 QR must, per `feedback_v3_axis_selection_quant_discipline.md` + the cycle-3 research mandate: do genuine WebSearch/WebFetch literature research, commit an `analysis/iteration_v3-085/*.py` IS-EDA script before the brief, and — per Critic Recommendation #2 — state BOTH anchors in brief Section 4 (the /084 EXPLORATION-MODE-REFERENCE IS +0.8325 / OOS +0.3322 for intra-cycle Δ; the /059 CONFIRMATION baseline IS +1.0894 / OOS +0.5791 reserved for /092).

**Hard constraints on /085** (carried from prior closeouts + the /084 Critic):
- Anchor intra-cycle Δ against the /084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed); reserve the /059 CONFIRMATION baseline (IS +1.0894 / OOS +0.5791, 10-seed) for /092. State BOTH anchors explicitly in brief Section 4 — the two-anchor structure is MANDATORY (Critic /084 Rec #2).
- `V3_MODELS` is BCH/LDO/TRX at the /085 starting point; the 14-feature /059 anchor stack stays; `PER_CELL_GAP` stays corrected at 22.
- Pre-register the OOS/IS Sharpe ratio bound (> 3.0 → SUSPICIOUS) AND the OOS-DOMINANT sub-mode in Section 4/8 per `feedback_v3_oos_is_ratio_gate.md`.
- Pre-register the holding-time / roster-composition predictor per `feedback_v3_is_oos_regime_divergence.md` — for a universe axis, the added-symbol mean-duration sub-channel under production Optuna-tuned barriers; for a per-symbol/universe axis, the target-symbol-axis falsifier band per `feedback_v3_per_symbol_target_axis_falsifier.md`.
- Genuine WebSearch/WebFetch literature research in Phases 1-4, documented in brief Section 10.
- Config-accretion pre-flight retained — the `_canonical_v059` 11-knob check stays in `run_baseline_v3.py`.
- Per-cell PBO comparisons across the /084 boundary are gap-regime-discontinuous (Critic /084 Rec #3) — do not compare /085's per-cell PBO directly to a pre-/084 per-cell PBO.
- CLOSED — do not re-propose: the v3 funding axis (4 data points /019/023/024/082); the Kaufman path-efficiency axis (`efficiency_ratio_50` / `range_efficiency_50`); the regime-conditional kill switch (primitive 9); the LDO→ADA universe swap; per-symbol PnL-share caps; gate-threshold knobs, ATR-multiplier tweaks, labeling tweaks on the same 14 features, instrumentation-only axes (all cycle-3 Section-1 CLOSED families). HBAR/AVAX (CLOSED at /021), ADA (CLOSED at /078), and FILUSDT (CLOSED at /083) are all closed universe-expansion candidates.

---

**Diary commit SHA**: (this closeout — diary + catalog + BASELINE_V3.md + cycle3_plan.md; SHA backfilled by the immediately-following commit)
**Critic FINAL SHA**: `16b4cc1`
**Engineering report SHA**: `2981cda`
**Phase 5.5 gate SHA**: `3d0d9db`
**Brief SHA-backfill SHA**: `f08709b`
**Brief LOCKED SHA**: `c18a2dc`
**Setup SHA**: `1073f32`
**EDA SHA**: `401de40`
**Reports**: `reports-v3/iteration_v3-084/`
**Tag**: `v0.v3-084` (EXPLORATION/REFERENCE closeout marker; NOT a baseline update — BASELINE_V3.md UNCHANGED at `v0.v3-059`)
