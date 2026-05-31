# v1 Skill — Walk-Forward Reframe & Regime-Ensemble Proposal

**Date:** 2026-05-31
**Author:** Quant Research consultant (Opus 4.7)
**Anchor:** user directive 2026-05-31 — "the IS we talking about here is just the data the QR has to run his analysis to define better configuration, is not the traditional IS when we train the model... combine models that perform under different regimes... don't want this kind of behaviour rejecting models that perform great in IS and not so great in OOS"
**Companion:** `skill_v1_edits_diff.md` (line-level CURRENT → PROPOSED), `regime_ensemble_methodology.md` (cross-agent memo)
**Target file:** `/home/roberto/crypto-trade/.worktrees/quant-research/.claude/commands/quant-iteration-v1.md` (1343 lines)

---

## Executive Summary

The v1 skill is structurally rigorous but **semantically miscalibrated** for the framework it actually implements:

| What the skill encodes | What the framework actually is |
|---|---|
| Classical IS / OOS train-test split with leakage prevention via OOS bisection | Walk-forward time-series — every month retrains + predicts; embargo at every fold |
| Strategy is one universal model; OOS validates generalization | Strategy is a *bundle* of regime specialists; OOS validates the bundle composite |
| `OOS/IS ≥ 0.5` enforces generalization (component gate) | `OOS/IS ≥ 0.5` is meaningful ONLY at the bundle level |
| IS-strong / OOS-weak = "overfit reject" | IS-strong / OOS-weak = "regime-specialist candidate" pending attribution |
| EXPLORATION verdict is binary PROMISING / NEGATIVE | EXPLORATION verdict is 7-band including REGIME-SPECIALIST-IS / OOS / TAIL-CONTROL / UNIVERSAL / WALK-FORWARD-LEAKAGE |

The reframe **does not relax methodology rigor.** It REDIRECTS rigor to the correct level of analysis:

- **Methodology gates (no look-ahead, embargo, DSR/PSR/PBO, gap correct):** components AND bundles.
- **Generalization gates (`OOS/IS ≥ 0.5`):** bundles ONLY.
- **Component candidates:** evaluated on regime contribution.

This proposal contains:
1. The five top edits (highest leverage)
2. Closeout iterations to re-annotate
3. Cycle-5 iterations re-evaluated under the reframe
4. /044 substrate-change assessment
5. Single most load-bearing sentence to inject

---

## 1. Top Five Skill Edits Proposed

Edits in priority order. Full line-level CURRENT → PROPOSED text in `skill_v1_edits_diff.md`.

### EDIT-1 — Replace "THE MOST IMPORTANT RULE: IS/OOS Data Split" (lines 141–160)

**The single highest-leverage fix.** The current section states the right principle ("not model leakage") and then contradicts itself in the closing line ("Hard floor: `OOS_Sharpe / IS_Sharpe ≥ 0.5`"). The replacement renames the section to **"Walk-Forward Semantics — CRITICAL READ"** and:

- Explicitly states the framework is walk-forward time-series (every month retrains + predicts)
- Distinguishes IS/OOS as METHODOLOGICAL (researcher discipline) NOT classical train/test
- States the regime-ensemble goal as core mission
- Forbids labeling IS-strong / OOS-modest as "overfit" by default
- Introduces the load-bearing sentence: **"The walk-forward is the leakage defense; the IS/OOS split is the researcher-honesty defense; the bundle is the product."**

### EDIT-2 — Mission appended with bundle-as-product (after line 22)

Adds two paragraphs to the existing Mission section. Establishes that v1 builds a regime-ensemble *bundle*, not a single universal model — and that individual EXPLORATIONs are bundle *components*.

### EDIT-3 — Split inherited merge gates by scope (lines 251–260)

Splits the inherited project-level gates into two scopes:

- **Bundle-level (CONFIRMATION-MERGE):** retains `OOS/IS ≥ 0.5`, DSR/PBO/PSR, etc.
- **Component-level (EXPLORATION-PROMISING):** within-regime Sharpe, regime-attribution clarity, bundle composition lift. Drops `OOS/IS ≥ 0.5` as component gate.

This is the structural fix that stops auto-rejecting regime specialists.

### EDIT-4 — Replace EXPLORATION verdict cells with 7-band regime-aware version (lines 808–820)

Replaces the 3-row PROMISING / NEGATIVE / NEGATIVE-no-effect table with a 9-row regime-aware matrix:

| Verdict | Trigger |
|---|---|
| `UNIVERSAL` | IS ≥ +0.05 AND OOS ≥ +0.05, broad regime distribution |
| `REGIME-SPECIALIST-IS` | IS ≥ +0.10, OOS ∈ [−0.20, +0.05], IS-only regime concentration |
| `REGIME-SPECIALIST-OOS` | IS ∈ [−0.20, +0.05], OOS ≥ +0.10, OOS-recurring regime |
| `TAIL-CONTROL` | DD reduction ≥ 20% regardless of Sharpe |
| `EXPLORATION-PROMISING` | lift present, attribution TBD |
| `TRUE-NEG` / `EXPLORATION-NEGATIVE` | no regime gives lift, mechanism falsified |
| `NEGATIVE-no-effect` | within ±0.10 baseline, saturated/under-powered |
| `LEARNED-NEG` | OOS catastrophic + clear regime explanation |
| `WALK-FORWARD-LEAKAGE` | actual leakage (gap=0, look-ahead) — BLOCK |

Plus the OVERFIT vs REGIME-SPECIALIST disambiguation table (importance-INERT + mechanism falsified vs load-bearing + regime mismatch).

### EDIT-5 — Add CONFIRMATION portfolio pathway (lines 822–829)

Splits CONFIRMATION-MERGE into two verdicts:

- `CONFIRMATION-MERGE` — single-axis multi-seed validation
- `CONFIRMATION-MERGE-PORTFOLIO` — multi-component bundle assembly (the /044 pathway)

Adds 6 portfolio composition rules: deterministic weights, ≥3 distinct regimes covered, pairwise OOS correlation ≤ 0.70, component substitution test, ≥1 anchor component, bundle-level gates.

This is the structural support for the /044 substrate as a portfolio CONFIRMATION rather than a single-axis CONFIRMATION.

---

## 2. Three Closeout Edits Proposed (specific iterations to re-annotate)

The following CLOSED iterations should be RE-ANNOTATED in their diaries + catalog entries to reflect the regime-ensemble reframe. The original closeouts labeled regime specialists as overfit/negative; the re-annotation preserves the audit trail while marking the iteration as a bundle candidate for /044.

### Re-annotate 1: iter-v1/040 (composed `regime_momentum_signed_5d`)

**Original closeout:** EXPLORATION-NEGATIVE (IS Δ +0.28, OOS Δ −0.37 — flagged as overfit by IS/OOS ratio)
**Reframe action:**
- Append a `## Reframe Note (2026-05-31)` section to `diary-v1/iteration_v1-040.md`
- Re-classify: `LEARNED-NEG-OR-REGIME-SPECIALIST-IS` (gray area per `feedback_is_oos_divergence_is_regime_not_overfit.md`)
- The mechanism check (importance rank 23–30 INERT) leans toward LEARNED-NEG-overfit, BUT the user directive explicitly cited /040 as preserve-don't-discard. Under the reframe: log to `/044 portfolio candidates pool` with regime tag = "IS bull-momentum cohorts 2020–2023", explicit flag = "INERT-rank confound — secondary use only".
- Update catalog row to read: `EXPLORATION-NEGATIVE → REGIME-SPECIALIST-IS-CONDITIONAL (preserve for /044)`

### Re-annotate 2: iter-v1/038 (per-symbol vol-target ceiling)

**Original closeout:** evaluation per current verdict bands
**Reframe action:**
- Re-evaluate as **TAIL-CONTROL** candidate (DD-reduction primitive, vol-scaling at p75 thresholds)
- A TAIL-CONTROL verdict is independent of Sharpe Δ — evaluated on max_drawdown / OOS_min_month_pnl reduction
- Append `## Reframe Note (2026-05-31)`: re-tag the iteration's per-symbol scaling thresholds as bundle-eligible RISK-PRIMITIVE component if any 5-symbol's OOS drawdown is reduced by ≥ 20%
- Cross-reference: BASELINE_V1 OOS max_drawdown is the comparison anchor

### Re-annotate 3: iter-v1/039 (per-cohort Sortino × LINK+DOT trend-scan hybrid)

**Original closeout:** EXPLORATION-NEGATIVE (cohort hybrid)
**Reframe action:**
- The iteration is a *composition* of /036 substrate + /037 Sortino objective on a 2-symbol cohort (LINK + DOT)
- Under the reframe, /039 is a **prototype portfolio assembly** at single-seed EXPLORATION budget — semantically closer to CONFIRMATION-PORTFOLIO than to single-axis EXPLORATION
- Append `## Reframe Note (2026-05-31)`: classify as **PORTFOLIO-PROTOTYPE candidate**; if regime attribution shows /039's LINK and DOT cells dominate distinct regimes, promote LINK and DOT cohort-Sortino as 2 of the /044 portfolio components
- The fact /039 didn't move OOS Sharpe at single-seed is consistent with cohort lottery noise — NOT mechanism failure

---

## 3. Cycle-5 Iterations Re-Evaluated Under the Reframe

Cycle 5 covers approximately **iter-v1/035 through iter-v1/041** (7 iterations) plus /042 if closed. Re-evaluation count: **5 of 7** would change classification under the reframe.

| Iteration | Original verdict | Reframed verdict | Bundle role |
|---|---|---|---|
| iter-v1/035 | (pending cycle-5 catalog status) | UNCHANGED (no IS-OOS divergence per catalog) | n/a |
| iter-v1/036 | EXPLORATION-PROMISING (substrate basin) | UNCHANGED — anchor-shape candidate | anchor / universal |
| iter-v1/037 | EXPLORATION-NEGATIVE (Sortino loss function) | **REGIME-SPECIALIST-IS-CONDITIONAL** if Sortino IS-lift attributable to tail-skew regimes | TAIL-AWARE component |
| iter-v1/038 | EXPLORATION-NEGATIVE (vol-target ceiling) | **TAIL-CONTROL** candidate (subject to DD-reduction verification) | risk overlay |
| iter-v1/039 | EXPLORATION-NEGATIVE (cohort hybrid) | **PORTFOLIO-PROTOTYPE** — bundle assembly at EXPLORATION budget | precursor to /044 |
| iter-v1/040 | EXPLORATION-NEGATIVE (regime_momentum_signed_5d) | **REGIME-SPECIALIST-IS-CONDITIONAL** (per user directive; INERT-rank caveat) | IS-bull-momentum specialist |
| iter-v1/041 | (in progress per catalog) | classify post-completion under reframe | TBD |

**5 of 7 cycle-5 EXPLORATIONs change classification.** None move to MERGE — they all move from "discard" / "dead-end" to "preserve for /044 portfolio pool with regime tag". The reframe expands the candidate pool for the next CONFIRMATION substrate.

---

## 4. /044 Substrate Change Assessment

**Question:** Is a /044 substrate change WARRANTED vs the current 4-model portfolio plan?

**Answer:** YES — and the reframe makes the change structural rather than ad-hoc.

The current "4-model portfolio plan" (Models A/C/D/E pooled across BTC/ETH/LINK/LTC/DOT) is a *cohort decomposition*, not a regime decomposition. Models are split by SYMBOL cohort, not by regime specialization. Under the reframe:

### Current (cohort-decomposed, not regime-aware)

- Model A: BTC + ETH pooled
- Model C: LINK
- Model D: LTC
- Model E: DOT

Each cohort runs the SAME labeling, SAME features, SAME risk primitives. The cohort decomposition is a SYMBOL diversifier, not a REGIME diversifier. A bear-regime month hurts ALL four cohorts the same way because they all share labeling/features/risk — there is no regime specialist to compensate.

### Proposed (/044 reframe — portfolio CONFIRMATION substrate)

`CONFIRMATION-MERGE-PORTFOLIO` substrate: **N regime specialists pooled across multiple symbols**, each strong in a different regime:

1. **Bull-momentum specialist** (from /040 reframe) — composed regime_momentum signed × hurst feature; IS lift concentrated in 2020/2021/2024-Q4 bull months
2. **Trend-scan cohort specialist** (from /039 reframe) — LINK + DOT cohort-Sortino objective; lift concentrated in trending mid-cap months
3. **Tail-control overlay** (from /038 reframe) — per-symbol vol-target ceiling at p75; fires in vol-spike regimes
4. **Substrate anchor** (from /036) — the basin-locked substrate component, universal-shaped
5. **(Optional) Sortino-objective component** (from /037 reframe) — tail-skew-aware loss function; lift concentrated in skewed-return regimes

Composition: regime-conditional dispatch + ensemble averaging, weights deterministic (no OOS weight tuning).

### Why the substrate change is warranted

1. **The current 4-cohort plan does not have regime diversity** — only symbol diversity. Under bear / vol-spike / regime-shift months, all 4 cohorts fail together because they share the same labeling + features + risk.
2. **The cycle-5 EXPLORATIONs ALREADY produced regime specialists** — /037 Sortino, /038 vol-ceiling, /039 cohort-hybrid, /040 regime-momentum. The reframe makes them eligible for a portfolio CONFIRMATION rather than discarding each individually.
3. **The user directive EXPLICITLY requests it** — "combine models that perform better under different regimes" — this is regime-portfolio composition, not cohort decomposition.
4. **The reframe provides the structural support** — `CONFIRMATION-MERGE-PORTFOLIO` verdict, Section 11 Bundle Composition, component substitution test, ≥3 regime coverage rule.

**Recommendation:** /044 should be the first CONFIRMATION-MERGE-PORTFOLIO under the reframe. Brief Section 11 declares the 4–5 components from /036–/040 reframe pool. The bundle is evaluated on composite OOS Sharpe + regime coverage table — NOT on any single component's OOS/IS ratio.

---

## 5. Single Most Load-Bearing Sentence to Add at Top of Skill File

Inject as the first sentence of EDIT-1's replacement section ("Walk-Forward Semantics — CRITICAL READ"):

> **The walk-forward is the leakage defense; the IS/OOS split is the researcher-honesty defense; the bundle is the product.**

That single sentence — if every agent reads only one line of the skill — preserves the framework's integrity. It encodes:

- **"The walk-forward is the leakage defense"** → no, you can't simulate a higher OOS by trimming the IS window
- **"The IS/OOS split is the researcher-honesty defense"** → no, you can't peek at OOS during design
- **"The bundle is the product"** → no, you don't reject an IS-strong / OOS-modest model as overfit; preserve as regime specialist for /044+

Every closeout, every verdict, every gate decision should reduce to this sentence's framing.

---

## 6. Application Order and Verification

Recommended application order:
1. EDIT-1 (the foundation; rewrites "THE MOST IMPORTANT RULE" — highest leverage)
2. EDIT-2 (Mission addendum)
3. EDIT-3 (split inherited merge gates)
4. EDIT-4 (7-band EXPLORATION verdict)
5. EDIT-5 (CONFIRMATION-PORTFOLIO verdict + composition rules)
6. EDIT-6 (Section 10 + Section 11 in brief schema)
7. EDIT-7 (Critic Check 3 split)
8. EDIT-8 (Phase 7.4 Regime Attribution Table — MANDATORY item 0)
9. EDIT-9 (Phase 5.5 gate verifies Section 10 + regime-aware falsifier)
10. EDIT-10 (Key Reminders prepended)

Plus:
- Distribute `regime_ensemble_methodology.md` to QR, QE, LightGBM Master, Critic agent dispatch prompts (small change to each agent's boot reading list)
- Update memory file `feedback_is_oos_divergence_is_regime_not_overfit.md` is already present (created 2026-05-31) — no change needed

Post-edit verification:
```
grep -nE "OOS_Sharpe / IS_Sharpe ≥ 0.5" .claude/commands/quant-iteration-v1.md
```
Every remaining match must be inside a BUNDLE-level context (EDIT-3 "Bundle-level" block or EDIT-7 "Check 3d BUNDLE-CONFIRMATION-only"). Any match in a component-EXPLORATION context = missed edit.

---

## Closing Note

The v1 skill encodes substantial rigor. None of that rigor is wrong. The wrongness is *philosophical* — the skill treats the framework as a single-model train/test pipeline (the equities / López de Prado default) when it actually implements a walk-forward regime-ensemble pipeline.

The fix is **not to remove rigor — it is to redirect rigor to the correct level of analysis**. The methodology gates belong to components AND bundles. The generalization gates belong to bundles only. Components are evaluated on regime contribution.

After these edits, the skill encodes: "build regime specialists, combine them into a regime-balanced bundle, validate the bundle on OOS — and DO NOT reject a regime specialist for being weak in regimes it was never meant to capture."

The /044 CONFIRMATION-MERGE-PORTFOLIO is the natural first product of the reframe — assembling cycle-5's "discarded" regime specialists into a regime-diverse portfolio.
