# Phase 7.5 Critic Review — iter-v3/128 — PRELIMINARY

(NO OVERALL line in Round 1.)

## Iteration Type (from Brief Section 0.5)
TYPE: EXPLORATION (cycle-7 slot 7 of 10; WILD axis class; HIGH-RISK posture pre-declared)

## Per-Check Status

**Check 1 (Look-Ahead)**: PASS. Zero new features. /058 walk-forward fix preserved. Trade math verified.

**Check 2 (Embargo Width)**: PASS. REQUIRED_GAP cardinality override 66→132 = (21+1)×6 correctly derived; runner override path + CPCV pass-through verified.

**Check 3 (Multiple-Testing)**: SPLIT — DSR/PSR informational; PBO 0.0992 PASS; **frac_positive_paths 0.4444 FAIL** at < 0.55 floor. CPCV distribution bimodal (regime-asymmetric strategy fingerprint). Informational at EXPLORATION; would be hard BLOCK at /132 CONFIRMATION.

**Check 4 (IC)**: PASS (carry-forward; no new features).

**Check 5 (ADF)**: PASS. T6 EDA G3 reports all 6 symbols stationary p ≤ 5.6e-22. No new stationarity surface.

**Check 6 (Pareto)**: N/A (single-seed EXPLORATION).

**Check 7 (Reproducibility)**: PASS with anomaly carry-forward note — run.log missing from `reports-v3/iteration_v3-128/`, 4th recurrence after /124/125/127. Gate stats inferred from trade-roster; not blocking but should address before CONFIRMATION-class runs.

**Check 8 (Hypothesis-Implementation)**: PASS. All 5 brief Section 3 changes bit-clean. No scope creep.

## Falsifier Adjudication

Section 8 first-match-wins locked at brief commit. Apply to observed:

| Criterion | Threshold | Observed | Fires? |
|---|---|---|---|
| **1 — NEGATIVE-catastrophic** | IS < +0.91 OR OOS < +0.67 | **IS = −0.4219 < 0.91** | **YES — FIRST MATCH** |
| 6 — SUSPICIOUS-OOS-DOMINANT | F3 dissociation > 0.50 | 2.77 (5.5× threshold) but PRE-EMPTED by C1 | Pre-empted |

**Engineer's mechanical verdict NEGATIVE-catastrophic CORRECTLY applied.**

F5 per-symbol cascade: 5/6 IS-negative — FIRES with large margin. ALGOUSDT IS LONG-direction WR 7.1% across 28 trades (-118.89 cumulative) is systematic signal-quality failure across full IS window, NOT regime-localized.

F3 IS-OOS dissociation = 2.77 (5.5× threshold) — largest in v3 history.

F6 (EDA-vs-runner methodology-fix validation): **INDETERMINATE** — Engineer didn't explicitly evaluate per-symbol production walk-forward AUC at end-of-IS vs EDA T4 2025-Q1 slice AUC. The rolling-endpoint methodology fix's PRIMARY validation gate is unadjudicated.

F7 top-symbol concentration: ICPUSDT 28.45% < 40% → PASS.

## "REGIME-MISMATCH" Reclassification — REJECTED

Engineer raised whether /128 warrants new classification ("EXPLORATION-REGIME-MISMATCH" with deferred-merge-pending-IS-update). REJECTED on methodology grounds:

1. Section 8 decision tree is LOCKED at brief commit time per `feedback_v3_axis_saturation_predictor.md` + `feedback_v3_lr_pf_methodology.md`. Adding a 10th classification after observing outcome is the post-hoc reclassification anti-pattern.

2. IS catastrophe is NOT cleanly regime-localized. ALGOUSDT IS WR 25.0% across 64 trades spanning 2020-2025 is NOT a single-regime artifact. If IS catastrophe were regime-localized, ALGO would show high WR in 2022 and 2024 bull months — it does not. The "bear-chop" framing fits portfolio-monthly distribution but does NOT explain ALGO's full-window LONG-direction failure.

3. "Deferred-merge-pending-IS-update" has no precedent in established cadence rules. v3 OOS_CUTOFF_DATE=2025-03-24 is sacred. Deferral operationally relies on the cutoff being movable.

4. /127 Optuna-trajectory-shift finding GENERALIZES: V3_MODELS replacement RE-TRAINS Optuna; resulting model is structurally different even if architecture bit-identical. /128 IS catastrophe is consistent with this — same methodology channel as /127 brake, just universe-substitution as the constraint.

5. OOS record is real but single-regime-favorable (2025-2026 altcoin bull). This is exactly the F3 SUSPICIOUS-OOS-DOMINANT pattern decision-tree's first-match-wins logic PRE-EMPTS at Criterion 1 by IS leg failing first. Decision tree DESIGNED to prevent exactly this: OOS record single-regime-dependent without IS validation.

The OOS record + broad-based + trade-rate-floor-cleared are real positive signals, BUT they are not sufficient on their own to override the IS catastrophe per pre-registered methodology. REGIME-MISMATCH would be post-hoc rule change.

## Clarifications Requested from QR

1. **F6 EDA-vs-runner alignment**: methodology-fix primary validation gate NOT explicitly evaluated by Engineer. Please supply per-symbol production walk-forward AUC at end-of-IS (or last 3 walk-forward months as proxy) for comparison against EDA T4 2025-Q1 slice AUC values (ATOM 0.520, RUNE 0.522, AVAX 0.514, HBAR 0.459, ICP 0.446, ALGO 0.522). If methodology-fix is NOT validated by F6, the cycle-7 methodology block established at /126 (3-occurrence pattern) extends to the rolling-endpoint variant.

2. **REGIME-MISMATCH reclassification**: per Critic analysis above, REJECTED on post-hoc rule change grounds. Does QR agree, or does QR have counter-argument that REGIME-MISMATCH is pre-implicit class inadvertently omitted from Section 8?

3. **/132 CONFIRMATION pathway**: if broad-based OOS lift is real signal (per Diagnostic 1 PASS), is QR contemplating future CONFIRMATION on changed universe + EARLIER OOS_CUTOFF_DATE (e.g., 2024-06-01) to test whether L1-altcoin recovery edge is genuinely transferable, OR is QR position that 9/9 universe-substitution NEGATIVE base rate closes the universe-axis definitively?

4. **Optuna-trajectory-shift channel extension**: does QR position /128 as additional evidence for /127's Optuna-trajectory-shift finding (extending to universe-axis), or as distinct failure mode (regime-asymmetry in feature learning)? The distinction informs whether /129+ briefs must include closed-loop Optuna-re-training simulators as pre-flight gate even for non-RISK-PRIMITIVE axes.
