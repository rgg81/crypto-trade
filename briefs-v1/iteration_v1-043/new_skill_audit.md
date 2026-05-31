# iter-v1/043 — New-Skill Audit (Pre-Draft vs 2026-05-31 Reframes)

**Date:** 2026-05-31
**Auditor:** QR (Opus 4.7)
**Brief commit audited:** `9d82f36` (authored BEFORE skill walkforward-reframe + relative-regime-Pareto adoption)
**Skill version:** `.claude/commands/quant-iteration-v1.md` (2026-05-31 — 20 edits across walk-forward reframe + relative-regime-Pareto merge framework)

---

## A — Per-Requirement Audit Table

| # | NEW-SKILL Requirement | Source | Status | Evidence |
|---|---|---|---|---|
| 1 | **Section 10 — Regime Attribution Plan (MANDATORY)**: target regime(s) + mechanism + off-regime expectation + bundle role + composition simulation + regime-aware falsifier | skill line 642; `regime_ensemble_methodology.md` §5 (QR) | **NEEDS-UPDATE** | Brief Section 10 = "Anti-Cheating Self-Check" (mis-numbered). NO regime-attribution plan section anywhere. Cycle-5 ended pre-reframe — was not authored. |
| 2 | **Section 8 — Pre-Registered Per-Regime Baseline-Comparison Criteria** (Pareto sharpe_R / max_dd_R / trade_count_R; NO absolute floors) | skill line 640; merge-proposal §H9 | **NEEDS-UPDATE** | Brief Section 11.6 keeps "ABSOLUTE MERGE GATES: IS Sharpe > 1.0 AND OOS > 1.0 AND OOS/IS ≥ 0.5 AND OOS trades ≥ 130 AND DSR > 0.95 AND PBO < 0.40 AND PSR > 0.95 AND top-symbol ≤ 30%". Exact opposite of relative-regime-Pareto. |
| 3 | **Section 4 falsifier — regime-aware** (cite target-regime Sharpe Δ within σ_R, NOT bundle OOS Sharpe Δ alone) | skill line 644; `regime_ensemble_methodology.md` §5 (QR) | **NEEDS-UPDATE** | Section 2 F-AXIS #1 verdict band entirely bundle-OOS-Sharpe-Δ-vs-/036; no per-regime decomposition (bull / chop / vol-spike / recovery). No target-regime declaration. |
| 4 | **9-band regime-aware verdict matrix**: UNIVERSAL / REGIME-SPECIALIST-IS / REGIME-SPECIALIST-OOS / TAIL-CONTROL / EXPLORATION-PROMISING / TRUE-NEG / NEGATIVE-no-effect / LEARNED-NEG / WALK-FORWARD-LEAKAGE | reframe-proposal §EDIT-4; `regime_ensemble_methodology.md` §4.2 | **NEEDS-UPDATE** | Section 2 uses old PROMISING-LINK-LOAD-BEARING / PROMISING-INERT-FAV / PAIRING-PARTIAL / LINK-DEPENDS-ON-DOT / NEG-CAT bands. Bespoke; not the canonical 9-band. No REGIME-SPECIALIST or TAIL-CONTROL band considered. |
| 5 | **Methodology gates HARD; DSR/PBO/PSR INFORMATIONAL** (no auto-block on DSR < 0.95 etc.) | skill lines 220–233, 325–335; merge-proposal §D | **NEEDS-UPDATE** | Section 11.6 cites DSR > 0.95, PBO < 0.40, PSR > 0.95 as hard MERGE gates for /044 (the gates DEMOTED to INFORMATIONAL by the reframe). |
| 6 | **Walk-forward semantics in brief Section 0.5** (IS/OOS = researcher-honesty, not classical train/test) | skill lines 145–199; `regime_ensemble_methodology.md` §2 | **NEEDS-UPDATE** | Brief Section 0.5 is "Iteration Type / Cadence / Wall-Clock". No walk-forward-semantics clarification. Brief still implicitly treats OOS as a held-out generalization oracle (Section 11.6 absolute-MERGE OOS Sharpe floor). |
| 7a | **Section 11 — LM Master Response Map** (per-recommendation adopted/modified/rejected) | skill lines 605–614 (/039-lessons) | **SATISFIES** | Section 11 LM Master Response Map present; 5-row substitute-prior table addresses adjacent-LM signals (advisor file absent at brief-authoring per Section 11 note — but lgbm_advisor.md DOES exist; minor mismatch). Format compliant with skill. |
| 7b | **Section 11.5 — Pre-Registered Failure-Mode Prediction** | skill line 639 | **SATISFIES** | Section 11.5 present; modal failure narrative + 5 falsifier triggers explicit. |
| 7c | **Section 11.6 — Locked Numerical MERGE/NO-MERGE Thresholds** | skill line 640 | **PARTIAL** | Section 11.6 present with thresholds, BUT the thresholds themselves violate requirement #2 + #5 (still absolute/Sharpe-floor-based). FORMAT satisfies; CONTENT contradicts reframe. |
| 7d | **Section 11.7 — Library Stack Declaration** | skill line 641 | **SATISFIES** | Section 11.7 present and explicit. |
| 8 | **HIGH-RISK / NORMAL-RISK declaration** (Section 2.5) | skill lines 463–492 | **SATISFIES** | Section 2.5 NORMAL-RISK declared with mechanism rationale + single-seed budget justified. |
| 9 | **Axis Rotation Discipline** (Section 0.6) | skill lines 423–459 | **SATISFIES** | Section 0.6 present with prior-5 family table, rotation status VALID, REPEAT-COMBO load-bearing justification. |
| 10 | **Wall-clock estimate Section 3.6 with 5-step scaling** | skill lines 384–390 | **SATISFIES** | Section 3.6 + Section 6 present; 5-step scaling derivation explicit. |
| 11 | **Anti-cheating self-check** | skill lines 123–142 | **SATISFIES** | Section 10 (mis-numbered as anti-cheat) present. |
| 12 | **Phase 6 deliverable `regime_attribution.csv`** awareness | merge-proposal §I.2; skill line 240 | **NEEDS-UPDATE** | No reference in brief to regime_attribution.csv schema or how /043's reports will populate it. |

**Score:** 7 SATISFY, 7 NEED-UPDATE (counting 7a/b/c/d as 4 sub-items; 11.6 counted as PARTIAL = NEEDS-UPDATE for content reframe).

---

## B — Specific Sections to Rewrite + Text Changes

### B.1 — ADD a new Section 10 — Regime Attribution Plan (re-number existing Section 10 → 10-Antichest as 10.5 or 12)

New Section 10 must declare:

```markdown
## Section 10 — Regime Attribution Plan

- **Target regime(s)**: LINK-trend-scan is hypothesized to be a load-bearing
  contributor in {bull-2025-Q3 (LINK +54% in 2025-08), recovery-2025-Q4
  (+39.7% in 2025-11)}. Off-regime (chop-2025-Q2 −23.5% / −16.1%) expected
  to drag.
- **Mechanism**: trend-scanning labels (Wald-t on slope, grid 5/8/13/21)
  detect persistent directional moves; LINK alone exposes the unbuffered
  return distribution σ_monthly=20.41%.
- **Off-regime expectation**: chop-regime months (2025-04/05/07; 2026-03)
  produce negative LINK PnL by mechanism; DOT diversification absent here.
- **Bundle role**: REGIME-SPECIALIST-IS bull/recovery candidate for /044
  bundle if F-AXIS #1 lands Δ ≥ 0 in bull regime AND off-regime drag bounded
  by /036's LINK leg.
- **Composition simulation**: if /043 PROMISING-CLEAN, simulate /044 bundle
  = /043-LINK-trend-scan + /036-LINK+DOT (overlap study) + /037-Sortino-5coh
  on IS regime-tag grid.
- **Regime-aware falsifier**: target-regime (bull 2025-08, recovery 2025-11)
  Sharpe Δ vs /036 LINK-leg subset (intrinsic) WITHIN ±0.30 ⇒ mechanism
  preserved; outside ⇒ basin lottery / mechanism degradation.
```

### B.2 — REWRITE Section 11.6 — Pre-Registered Per-Regime Baseline-Comparison Criteria

REPLACE the absolute-floor MERGE block with per-regime Pareto:

```markdown
## Section 11.6 — Pre-Registered Per-Regime Baseline-Comparison Criteria

/043 is EXPLORATION — no direct MERGE. /044 CONFIRMATION evaluation will be
per-regime Pareto vs current BASELINE_V1 anchor (read from
`briefs-v1/_meta/baseline_seed_regime_matrix.csv`):

MERGE iff:
  FOR EVERY tagged regime R present in IS or OOS:
    sharpe_R(candidate) ≥ sharpe_R(baseline) − σ_R
    AND max_dd_R(candidate) ≤ max_dd_R(baseline) + σ_dd_R
    AND trade_count_R(candidate) ≥ 0.5 × trade_count_R(baseline)
  AND EXISTS R* :
    sharpe_R*(candidate) > sharpe_R*(baseline) + σ_R*
       OR max_dd_R*(candidate) < max_dd_R*(baseline) − σ_dd_R*
  AND methodology integrity intact (Critic Checks 1, 2, 5, 7, 8, ADF)

DSR / PBO / PSR are INFORMATIONAL (reported per-regime); not auto-block gates.

NO absolute Sharpe / OOS-trade / concentration floors at /044 evaluation.
```

Strike from the brief: `IS Sharpe > 1.0 AND OOS Sharpe > 1.0 AND OOS/IS ratio ≥ 0.5 AND OOS trades ≥ 130 AND DSR > 0.95 AND PBO < 0.40 AND PSR > 0.95 AND top-symbol concentration ≤ 30%` (all 8 of these are now INFORMATIONAL or replaced by per-regime σ-relative bands).

### B.3 — REWRITE Section 2 F-AXIS #1 verdict bands

Map the existing 5-band bespoke matrix onto the canonical 9-band regime-aware:

| Bespoke (current) | Canonical 9-band (new) |
|---|---|
| PROMISING-LINK-LOAD-BEARING (Δ ≥ 0) | UNIVERSAL or REGIME-SPECIALIST-IS (depends on per-regime decomposition) |
| PROMISING-INERT-FAV (Δ ∈ [−0.35, 0)) | EXPLORATION-PROMISING |
| PAIRING-PARTIAL (Δ ∈ [−0.90, −0.35)) | REGIME-SPECIALIST-IS (if bull/recovery preserved) OR NEGATIVE-no-effect (if all regimes drag) |
| LINK-DEPENDS-ON-DOT (Δ ∈ [−1.30, −0.90)) | LEARNED-NEG (mechanism degraded by cohort removal) |
| NEG-CAT (Δ < −1.30) | TRUE-NEG / EXPLORATION-NEGATIVE |

Add per-regime Sharpe Δ rows to F-AXIS #1 verdict matrix (bull, chop, recovery, vol-spike). Require diary Phase 8 to populate from `reports-v1/iteration_v1-043/regime_attribution.csv`.

### B.4 — Add Section 0.5 walk-forward-semantics clarification

INSERT 1 paragraph after the cadence-position table:

```markdown
**Walk-forward semantics**: IS (pre-2025-03-24) and OOS (post-2025-03-24)
both undergo the SAME monthly train-predict mechanic with embargo at every
fold boundary. OOS is NOT a held-out test set; it is the researcher-honesty
window. /043 is a REGIME-SPECIALIST diagnostic, not a generalization claim
— the OOS Sharpe band [+0.83, +1.53] is one realization of /036's OOS
regime mix, NOT a universal-predictor validation.
```

### B.5 — Note Phase 6 `regime_attribution.csv` deliverable

In Section 3.7 step-sequence, add:

```markdown
9. QE Phase 6 deliverable: `reports-v1/iteration_v1-043/regime_attribution.csv`
   per schema `regime_tag, in_sample, candidate_sharpe, candidate_max_dd,
   candidate_trade_count, baseline_sharpe, baseline_max_dd, baseline_trade_count`
   for /043 vs /036 LINK-leg (the substrate baseline) AND vs BASELINE_V1.
```

### B.6 — Reframe Section 11 LM Master Response Map note

The brief states `lgbm_advisor.md` is absent at brief-authoring. The file DOES exist at `briefs-v1/iteration_v1-043/lgbm_advisor.md`. Update Section 11 with the per-recommendation response map to the actual LM Master deliverable (5 items + /044 routing table). The substitute-prior synthesis becomes informational secondary.

---

## C — Axis Appropriateness Under New Framework (LINK-only Trend-Scan)

The axis itself **REMAINS APPROPRIATE** under the regime-ensemble framework — arguably MORE appropriate than under the pre-reframe schema.

**Specific alignment:**

1. **Regime-specialist alignment.** LINK-only trend-scan is a textbook REGIME-SPECIALIST candidate per `regime_ensemble_methodology.md` §3 — single-symbol, single-label-mode, predictable bull/recovery concentration (EDA §3 monthly distribution: 2025-08 +54%, 2025-11 +39.7%, 2025-04/05 drag). Exactly the profile the bundle wants as a bull-regime contributor.

2. **/044 bundle composition.** Under the new framework, /044-A's substrate decision is no longer "LINK-only OR LINK+DOT" (the brief's binary framing) but "what is each component's bundle role?" — LINK-only specialist + DOT-as-diversifier + Sortino-5coh chop-handler could ALL be /044 components if regime-attribution shows distinct regime coverage. The brief's Section 8 routing-tree is too binary; under the reframe, the LINK-only result should be evaluated as a CANDIDATE bundle component, not as a wholesale substrate replacement.

3. **Falsifier still useful.** The Section 2 verdict bands still resolve a meaningful question (does LINK alone carry /036's lift) — they just need to be re-mapped to the 9-band canonical AND decomposed by regime tag (bull, chop, recovery).

4. **Risk concern.** The brief's "ABSOLUTE MERGE GATES" block in Section 11.6 will need to be struck on the /044 forward-routing language. The /044 CONFIRMATION QR (next iteration) reads /043's brief — if /043 still cites the old gates, /044 may carry the contradiction forward.

**Bottom line on axis appropriateness:** LINK-only trend-scan IS a regime-specialist candidate aligned with /044 bundle composition; the AXIS is appropriate, but the BRIEF's evaluation framework + MERGE gates + verdict bands must be reframed before /044 reads it as input.

---

## D — Recommended Path Forward

**Option 1 (minimal):** Author `new_skill_audit.md` (this file) + `addendum.md` covering B.1 (Section 10), B.2 (Section 11.6 rewrite), B.3 (verdict bands re-map), B.4 (walk-forward clarification). Brief itself remains immutable (the iteration is in flight / closeout). Phase 7.5 Critic reads brief + addendum.

**Option 2 (full rewrite):** Re-author `research_brief.md` v2 with all reframes baked in. Higher fidelity but risks anti-cheating concern (brief amended post-Phase 5.5 gate; /043 backtest may already be running).

**Recommendation:** OPTION 1. Phase 7.5 Critic reads addendum alongside brief; Phase 8 diary applies regime-attribution lens to actual results.

---

**END OF AUDIT**
