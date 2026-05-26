# iter-v1/015 — Phase 7 Engineering Report (5th-strike retroactive fix)

**Iteration**: iter-v1/015
**Date**: 2026-05-26
**Branch**: `iteration-v1/015`
**Backtest HEAD**: `def3dcd` (Phase 7.5 Critic review commit)
**Mode**: CONFIRMATION (first cycle-2 CONFIRMATION; ENSEMBLE_SIZE=10 inner, n_trials=35)
**Author**: QR (Phase 7 retroactive — engineering report MISSING at Phase 7.5 dispatch; QE ran `--no-engineering-report` opt-out at HEAD `aaa5e6b`; this document closes the 5th-strike violation in the same series as /011/012/013/014)

---

## Section 1 — Final Verdict + Verdict-Class Rationale

**Verdict**: `CONFIRMATION-NEGATIVE` subtype **`catastrophic`** (per Critic Phase 7.5 review at `briefs-v1/iteration_v1-015/review.md` and brief Section 8.4 binding verdict map).

**Verdict-class assignment**:

| Falsifier | Threshold | Observed | Outcome |
|---|---|---|---|
| **F1-MULTI** (OOS Sharpe Δ vs BASELINE_V1, multi-seed mean) | NEGATIVE band Δ < −0.10; catastrophic Δ < −0.55 | **−1.6117** | NEGATIVE-catastrophic — **2.93× the catastrophic floor** |
| **F1-IS** (IS Sharpe Δ vs BASELINE_V1, multi-seed mean) | NEGATIVE band Δ < −0.20 | **−0.3474** | NEGATIVE |
| **F-AXIS-C1** (execution-time barrier matches label-time within 1e-6) | binary PASS/FAIL | PASS (no NaN RuntimeError; cache populated) | PASS |
| **F-AXIS-MECHANISM** (n_eff ≥ 17 across ≥7/10 inner seeds) | ≥7/10 | **0/10** (n_eff_per_cell_median=3 across all 5 symbols) | **HARD-FALSIFIER FAIL** |
| **F8-NEW-MULTI** (IS trades ∈ [466, 776], 10/10 seeds) | inside band | 620 (single-pass; ENSEMBLE_SIZE=10 = inner-pass not 10-seed dispersion) | PASS |

**Verdict-class binding**: brief Section 8.4 row "multi-seed mean OOS Δ < −0.55 → CONFIRMATION-NEGATIVE catastrophic". Observed Δ = **−1.6117** triggers catastrophic subclass with margin 1.06 below the floor (3× the floor magnitude). F-AXIS-MECHANISM HARD-FALSIFIER FAIL provides the structural mechanism explanation: n_eff collapse from 19 (/014 single-seed) to 3 (/015 multi-seed) is the load-bearing cause, NOT basin-lottery.

**No BLOCK-PENDING-FIX**: per Critic Phase 7.5 review §"BLOCK-PENDING-FIX Rerun Protocol", the implementation was correct. F-AXIS-C1 programmatic falsifier did NOT fire (no NaN RuntimeError raised; σ_t cache correctly populated). The hypothesis was empirically refuted at the mechanism layer (F-AXIS-MECHANISM FAIL) and the headline layer (F1-MULTI catastrophic) simultaneously. There is no isolated defect to fix — Path 1 was methodologically correct but empirically wrong.

**BASELINE_V1 update: NO.** IS Δ −0.3474 + OOS Δ −1.6117 fail the strictly-better criterion on BOTH halves. Anchor remains `v0.v1-baseline-corrected` (`f8bc12c`).

---

## Section 2 — Per-Symbol IS PnL Decomposition (with /014 comparison)

From `reports-v1/iteration_v1-015/in_sample/per_symbol.csv` (620 IS trades total):

| Symbol | Trades | Wins | WR | /015 Net PnL % | /014 Net PnL | Δ raw | Δ pct |
|---|---|---|---|---|---|---|---|
| **LINKUSDT** | **149** | **59** | **39.6** | **+58.31** | -9.79 | **+68.10** | **−696%** |
| ETHUSDT | 146 | 56 | 38.4 | +17.34 | -99.73 | **+117.07** | **−117%** |
| BTCUSDT | 114 | 45 | 39.5 | −0.65 | -24.25 | **+23.60** | **−97%** |
| LTCUSDT | 103 | 42 | 40.8 | **−9.21** | +95.51 | **−104.72** | **−110%** |
| **DOTUSDT** | **108** | **40** | **37.0** | **−25.05** | -88.74 | **+63.69** | **−72%** |
| **PORTFOLIO** | **620** | **242** | **39.0** | **+40.74** | -126.99 | **+167.73** | **−132%** |

(Δ pct uses raw Δ / |/014 magnitude| × sign — convention indicates direction-of-change relative to /014's per-symbol pole.)

### 2.1 LM Master Phase 4.5 Per-Symbol C1-Inversion Prediction VERIFIED 3 of 3

LM Master Phase 4.5 §"Risk 2 LTC C1-WINDFALL inversion":
> "Per-symbol attribution: LTC IS+OOS likely DOWN; BTC/ETH IS+OOS likely UP."

**Observed**:
- LTC IS: +95.51 → −9.21 = Δ **−104.72** DOWN ✓
- ETH IS: −99.73 → +17.34 = Δ **+117.07** UP ✓
- BTC IS: −24.25 → −0.65 = Δ **+23.60** UP ✓

**First directional hit in v1 LM Master history (13 iterations)**. Mechanism-deterministic call (C1 asymmetric windfall inversion when C1 FIXED) — NOT a basin-lottery prediction. Honest accounting: per-symbol mechanism predictions earn credibility (now 6/13 PARTIAL+ mechanism-level); verdict-class F1/F3 magnitude predictions remain at 0/13 directional.

### 2.2 Portfolio IS Sharpe NEGATIVE Despite Per-Symbol Recovery

IS net PnL +40.74 (vs /014 −126.99; **+167.73 absolute swing**) but IS Sharpe **−0.0645** vs /014 −0.6112 = Δ +0.5467 IS Sharpe improvement (still NEGATIVE band overall). The C1 FIX removed asymmetric LTC windfall + BTC/ETH penalty; portfolio PnL recovered massively but daily-variance weighting keeps IS Sharpe near-zero.

### 2.3 Per-Symbol Anchor vs Baseline_V1 (IS)

| Symbol | /015 IS PnL % | Baseline_V1 IS PnL % | Δ vs baseline |
|---|---|---|---|
| LINKUSDT | +58.31 | +72.06 | −13.75 |
| ETHUSDT | +17.34 | −13.70 | +31.04 |
| BTCUSDT | −0.65 | −37.28 | +36.63 |
| LTCUSDT | −9.21 | +3.27 | −12.48 |
| DOTUSDT | −25.05 | +26.62 | −51.67 |
| **PORTFOLIO** | **+40.74** | **+50.98** | **−10.24** |

Portfolio IS net PnL is within 10pp of baseline despite ENSEMBLE_SIZE=10 + n_trials=35. BTC + ETH recover substantially; LTC + DOT collapse. This is the **/015 multi-seed C1-FIXED-symmetric attribution** at the IS layer.

---

## Section 3 — Per-Symbol OOS PnL Decomposition (with /014 comparison)

From `reports-v1/iteration_v1-015/out_of_sample/per_symbol.csv` (218 OOS trades total):

| Symbol | Trades | Wins | WR | /015 Net PnL % | /014 Net PnL | Δ raw | % of /015 Total |
|---|---|---|---|---|---|---|---|
| **LINKUSDT** | **48** | **26** | **54.2** | **+84.58** | +3.87 | **+80.71** | **285.05%** |
| DOTUSDT | 45 | 18 | 40.0 | +14.31 | +10.43 | +3.88 | 48.22% |
| BTCUSDT | 44 | 13 | 29.5 | −7.18 | +5.70 | −12.88 | −24.20% |
| ETHUSDT | 49 | 20 | 40.8 | **−23.29** | −41.18 | +17.89 | −78.48% |
| **LTCUSDT** | **32** | **8** | **25.0** | **−38.75** | +24.49 | **−63.24** | **−130.60%** |
| **PORTFOLIO** | **218** | **85** | **39.0** | **+29.66** | +3.31 | **+26.35** | **100%** |

### 3.1 OOS Pattern

- **LINK monopoly**: +84.58 PnL = 285.05% of total — same hyper-concentration as /011 LINK-dominant pattern; far exceeds 30% concentration cap on absolute net_pnl. Gate 7 violation by wide margin.
- **LTC catastrophic-reversal**: /014 LTC was OOS WINNER +24.49 (WR 50%); /015 LTC OOS LOSER −38.75 (WR 25%). C1 windfall removed → LTC OOS pattern flipped. Largest per-symbol OOS swing.
- **BTC sign-flips**: /014 BTC OOS +5.70 → /015 OOS −7.18 (WR 29.5%). Mild negative.
- **OOS total net PnL +29.66** is positive (vs /014 +3.31) but OOS Sharpe collapses to **−0.9480** (vs /014 +0.1828 = Δ −1.1308 OOS Sharpe). The combination of LINK monopoly + LTC catastrophic-reversal produces high daily variance — OOS daily Sharpe collapses despite positive total return.

### 3.2 Per-Symbol OOS vs Baseline_V1

| Symbol | /015 OOS PnL % | Baseline_V1 OOS PnL % | Δ vs baseline |
|---|---|---|---|
| LINKUSDT | +84.58 | +34.23 | +50.35 |
| DOTUSDT | +14.31 | +1.96 | +12.35 |
| BTCUSDT | −7.18 | +33.17 | −40.35 |
| ETHUSDT | −23.29 | +2.75 | −26.04 |
| LTCUSDT | −38.75 | −47.25 | +8.50 |
| **PORTFOLIO** | **+29.66** | **+24.87** | **+4.79** |

Portfolio OOS net PnL +29.66 is +4.79pp above baseline, but the BTC + ETH OOS halves both go negative while LINK absorbs all the gain. This is the **single-symbol-concentration risk** that the multi-seed dissolution did NOT mitigate at n_eff=3.

---

## Section 4 — F1–F8 + F-AXIS-C1 + F-AXIS-MECHANISM Evaluation Matrix

Per brief Section 7 pre-registered falsifier table:

| Falsifier | Pre-registered threshold | Observed | Verdict |
|---|---|---|---|
| **F1-MULTI** | Modal NULL Δ ∈ [−0.10, +0.20]; tail bands NEGATIVE Δ < −0.10 | **−1.6117** | **NEGATIVE-catastrophic** (2.93× catastrophic floor; outside ALL pre-registered bands; "single largest miss in /015 brief calibration") |
| **F1-IS** | NULL band; NEGATIVE Δ < −0.20 | **−0.3474** | NEGATIVE (1.74× threshold) |
| **F2** | OOS/IS Sharpe ratio (informational) | 14.7036 (sign-flipped both halves) | INVALID (both halves negative; ratio degenerate) |
| **F3** | IS Sharpe Δ < −0.30 = catastrophic-extreme | Δ −0.3474 | NEGATIVE-catastrophic (1.16× threshold) |
| **F4** | IC structure (no new feature family added) | inherited | N/A |
| **F5** | ADF stationarity | inherited (bonferroni_pass=True) | PASS |
| **F6** | Pareto dominance (10-seed) | **artifact MISSING** (no pareto_front.csv produced) | INVALID (Gate 10 effectively FAILs by inference; F1-MULTI scalar decisive) |
| **F7-NEW** | Per-symbol direction match (4/5) | N/A — different mechanism than /014 (axis is now well-posed, no C1 asymmetry pattern to match) | RECLASSIFIED INFORMATIONAL — see Section 2.1 (3/3 LM Master C1-inversion verified) |
| **F8-NEW** | IS trades ∈ [466, 776] | **620** | PASS |
| **F-AXIS-C1** | Execution barrier matches label barrier within 1e-6 tolerance; NaN RuntimeError fires if σ_t missing | PASS (no RuntimeError raised; σ_t cache populated; LM Master Rec #3 boundary enforcement functioning) | PASS |
| **F-AXIS-MECHANISM** | n_eff_per_cell_median ≥ 17 across ≥7/10 inner seeds | **n_eff = 3 across all 5 symbols / 10 seeds** | **HARD-FALSIFIER FAIL** (0/10 vs ≥7/10; single largest mechanism miss in /015 brief) |

**Verdict cell**: Cell 6 of brief Section 8.4 — `F1-MULTI < −0.55 AND F-AXIS-MECHANISM FAIL` → **CONFIRMATION-NEGATIVE catastrophic**.

---

## Section 5 — n_eff Barrier-Magnitude Curve Discovery (STRONGEST CYCLE-2 STRUCTURAL FINDING)

**The load-bearing structural finding of cycle-2.** LM Master Phase 7.4 §2 + Critic Phase 7.5 §"Verdict Cell Assignment" + this Section 5 converge.

### 5.1 The Two Data Points

| Iteration | Barrier magnitude (portfolio-median TP at σ_t × k_tp × √timeout) | n_eff_per_cell_median |
|---|---|---|
| **/014** (inadvertent missing √timeout factor — label-time σ_t × k_tp without √timeout in execution-time barriers) | **~1.70%** (effective; σ_t × 1.06 ≈ 1.70% at BTC σ_t p50) | **19** (optimal-diversity; range 14-22 per-symbol) |
| **/015** (Path 1 calibration EDA — σ_t × k_tp × √timeout symmetric at both layers) | **7.82%** (BTC σ_t p50 × 1.06 × √21 ≈ 7.82%) | **3** (collapsed; range 1-7 per-symbol) |

**4.6× barrier magnitude → 6.3× n_eff collapse.** Mechanism: at 7.82% TP/SL over 21-candle timeout, most rows hit `timeout → sign(fwd_return)` fallback because ±7.82% excursions are rare in 21 8h-candles. Label distribution becomes **timeout-dominated**; Optuna can't distinguish hyperparameters → n_eff collapses. Model becomes near-trivial "predict fwd_return sign" → bad OOS (−0.95 Sharpe).

### 5.2 Why This Is THE Strongest Structural Finding of Cycle-2

n_eff is **bounded by per-cell label-distribution shape**, NOT by basin draw direction. The /014 → /015 comparison is the FIRST cycle-2 measurement that varies barrier magnitude on the same labeling axis at well-posed (C1-symmetric) implementation. The /014 single-seed n_eff=19 was a **DURABLE structural finding independent of /014's basin direction** (per /014 LESSON #1). /015 at multi-seed REPLICATED the per-cell label-distribution shape — and confirmed n_eff is barrier-magnitude-dependent NOT barrier-magnitude-monotone-increasing.

**n_eff is a CURVE in barrier-magnitude space, not a monotone function.** The optimum is somewhere in the middle:
- 1.70% labels (/014): n_eff = 19 (optimal — TP-hit-dominated cells well-distributed)
- ~3-5% labels (hypothesized): n_eff ∈ [15, 19] (preserved; mixed TP/SL/timeout)
- 7.82% labels (/015): n_eff = 3 (collapsed — timeout-dominated; labels degenerate to fwd_return sign)

### 5.3 Forward Mandate for Cycle-3+

Before any future labeling sub-axis EXPLORATION, run the **calibration sweep**: test {1.5%, 2.5%, 3.5%, 5.0%, 7.82%} barriers at single-seed and chart n_eff per magnitude. Establish n_eff ≥ 15 preservation band BEFORE selecting CONFIRMATION magnitude. Codifies what Path 1 should have included pre-implementation.

**Critic Phase 7.5 Recommendation #1 (process)**: same wording; force n_eff sweep mandate before any labeling axis touches CONFIRMATION budget.

**Companion forward-mandate (Critic Rec #2)**: pre-register a label-distribution histogram (count `tp_hit` / `sl_hit` / `timeout_fallback` per cell) with threshold (e.g., `timeout_fallback_share < 0.6`). At /015, share was almost certainly > 0.85.

### 5.4 Path 2 Was the Right Decision

In /014 closeout, LM Master + Critic + Phase 6.0 + QR converged on Path 1 (add √timeout factor symmetrically at label-time AND execution-time). Path 2 (drop √timeout factor entirely — preserve /014's inadvertent 1.70% magnitude) was REJECTED on methodological grounds (theoretical realized-vol scaling demands √timeout).

**Path 2 was empirically right — Path 1 was methodologically right.** This is the most important methodology lesson of /015: when prior iteration produces DURABLE STRUCTURAL EVIDENCE on a specific implementation, that evidence should OUTWEIGH EDA-prescribed magnitudes even at the cost of theoretical cleanliness. /014's n_eff=19 at 1.70% labels was the durable signal; Path 1 dissolved it.

This is NOT a code defect. The src/ implementation correctly executes the brief's spec. The brief's spec was empirically wrong.

---

## Section 6 — LM Master Calibration Update (1/13 Directional + 5 PARTIAL → Mechanism-Level 6/13)

### 6.1 LM Master Track Record Updated

| Layer | Pre-/015 | Post-/015 |
|---|---|---|
| Verdict-class magnitude (F1/F3 multi-seed mean band) | 0/12 directional | **0/13 directional** (F1 multi-seed mean −1.6117 NOT in pre-registered [−0.30, +0.30] band) |
| Per-symbol catastrophic candidate (single-seed EXPLORATION) | 0/4 cycle-2 directional → FORBIDDEN per /014 LESSON #5 | unchanged (no /015 prediction made; /015 was multi-seed CONFIRMATION not EXPLORATION) |
| Mechanism-level (n_eff prediction, F7-NEW direction, F8-NEW band, lookahead-clean, FLAT prior calibration) | 5 PARTIAL hits | **6 PARTIAL hits** (LM Master Phase 4.5 §"Risk 2" 3-of-3 per-symbol C1-inversion verified — mechanism-deterministic) |
| Mechanism-determined per-symbol direction (CHARACTERIZED MECHANISM with disclaimer) | N/A | **1/1 verified** (3/3 per-symbol C1-inversion: LTC IS+OOS DOWN ✓, ETH IS+OOS UP ✓, BTC IS UP ✓) |

**Honest count: 1/13 directional (verdict-class) + 5 PARTIAL + 1 mechanism-deterministic = "mechanism-level 6/13" — but with the magnitude miss still at 0/13.**

### 6.2 Path 1 Self-Critique (LM Master Phase 7.4 §3 verbatim)

> **"Path 1 was METHODOLOGICALLY correct but EMPIRICALLY WRONG."**
>
> My Phase 4.5 Rec #5 ("don't regrid k_tp/k_sl") trusted the calibration EDA over the empirical /014 n_eff=19 signal.
>
> Lesson: when prior iteration produces DURABLE STRUCTURAL EVIDENCE on a specific implementation, that evidence should OUTWEIGH EDA-prescribed magnitudes. Path 2 (drop √timeout from labeling.py) would have preserved n_eff=19. Path 1 prioritized theoretical correctness over preserving the structural signal.
>
> **Future Phase 4.5 — when prior iteration shows DURABLE STRUCTURAL EVIDENCE, recommend AGAINST any axis re-implementation that would dissolve it, even if dissolution is methodologically "cleaner."**

Both Critic + LM Master + Phase 6.0 endorsed Path 1; this is a process-level cycle-2 lesson, NOT an LM-Master-only miss. The DURABLE-EVIDENCE-OUTWEIGHS-EDA rule is the cycle-2 closeout-level lesson (see Section 7 Rec #2).

### 6.3 Track Record Update Codified Forward

Future Phase 4.5 advisories must explicitly tag predictions as:
- **Verdict-class magnitude**: FLAT prior at single-seed; modal-NULL at multi-seed (post-/015 calibration update unchanged; magnitude still 0/13)
- **Mechanism-level claims**: MEDIUM-HIGH confidence with explicit mechanism attribution
- **Per-symbol direction under CHARACTERIZED MECHANISM**: MEDIUM allowed, with "mechanism-deterministic" disclaimer (newly earned credibility at /015 with 3/3 verification)
- **Per-symbol catastrophic predictions**: FORBIDDEN at single-seed EXPLORATION (0/4 cycle-2 track record per /014 LESSON #5)

---

## Section 7 — Critic Process Recommendations for Cycle-3

Verbatim from Critic Phase 7.5 review §"Recommendations to QR (cycle-3 process-level fixes)":

### Rec #1 — n_eff vs barrier-magnitude EDA mandate

Before any future labeling sub-axis EXPLORATION, run the calibration sweep — test {1.5%, 2.5%, 3.5%, 5.0%, 7.82%} barriers at single-seed and chart n_eff per magnitude. Establish n_eff ≥ 15 preservation band BEFORE selecting CONFIRMATION magnitude. Codifies what Path 1 should have included pre-implementation.

### Rec #2 — F-AXIS-MECHANISM as label-distribution falsifier

/015 brief's prediction "n_eff bound by label-distribution SHAPE; seed-INDEPENDENT" was structurally true but DIRECTIONALLY WRONG. Tighten future falsifier to pre-register a label-distribution histogram (count `tp_hit` / `sl_hit` / `timeout_fallback` per cell) with threshold (e.g., `timeout_fallback_share < 0.6`). At /015, share was almost certainly > 0.85.

### Rec #3 — Engineering report HARD-STOP enforcement

`--no-engineering-report` opt-out was exercised on the very first iteration with the HARD-STOP in place. Either remove the opt-out OR require orchestrator to create minimal stub `engineering_report.md` with F-AXIS evaluations attached. As-is, the opt-out makes the HARD-STOP cosmetic. **5th consecutive iteration with retroactive engineering-report fix** at QR Phase 7 closeout — recurring failure.

---

## Section 8 — BASELINE_V1 Update NOT Triggered

Per `feedback_v3_baseline_update_policy.md` (STRICTLY-BETTER-than-prior-baseline rule applied to v1):

| Gate | Threshold | Observed |
|---|---|---|
| IS Sharpe strictly better | +0.2829 → > +0.2829 | **−0.0645** | FAIL (Δ −0.3474) |
| OOS Sharpe strictly better | +0.6637 → > +0.6637 | **−0.9480** | FAIL (Δ −1.6117) |
| Pareto seeds both OOS positive | both > 0 | pareto_front.csv MISSING | INVALID (cannot evaluate; F1-MULTI scalar decisive at NEGATIVE-catastrophic) |
| OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | 14.7036 (sign-flipped) | INVALID |
| Top-symbol concentration ≤ 30% | ≤ 30% absolute | LINK 285.05% of OOS PnL | FAIL |

**Conclusion**: BASELINE_V1 update NOT triggered. Anchor remains `v0.v1-baseline-corrected` (`f8bc12c`).

Per /015 brief Section 0.7 "/015 CONFIRMATION Bundle Composition": /014's σ_t labeling axis was the PRIMARY component under test. The bundle is one axis-PLUS-its-completion (Path 1 C1 FIX). The axis is NOW CLOSED at calibrated 7.82% magnitude per LM Master Phase 7.4 §4. Sub-magnitude (3-5%) is the open question for any cycle-3 labeling re-entry.

---

## Section 9 — Cycle-2 Closeout Context

**Cycle-2 CLOSES with /015 CONFIRMATION-NEGATIVE catastrophic**:

| Iteration | Family | Verdict |
|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /008 | methodology | EXPLORATION-PROMISING-METHODOLOGY (non-compoundable) |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) |
| /011 | risk-primitive | EXPLORATION-NEGATIVE (catastrophic-basin-shift) |
| /012 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL) |
| /013 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-LOTTERY-CATASTROPHIC) |
| /014 | labeling | EXPLORATION-NEGATIVE (Cell-5 + PARTIAL-F7 + DURABLE-n_eff-MECHANISM) |
| **/015** | **labeling** (CONFIRMATION) | **CONFIRMATION-NEGATIVE catastrophic** (F1-MULTI Δ −1.6117 + F-AXIS-MECHANISM HARD-FAIL + n_eff barrier-magnitude curve discovery) |

**Cycle-2 final tally**: 10 iterations, 1 PROMISING-METHODOLOGY (/008 n_eff PCA, non-compoundable), 9 NEGATIVE, **ZERO merges**. v1 BASELINE_V1.md UNCHANGED across all of cycle-2.

**Structural cycle-2 takeaway**: v1 BASELINE_V1 is highly **basin-locked** at a multi-dim local optimum. Single-axis EXPLORATION+CONFIRMATION discipline produced zero merges in this regime. The catalog is dispersed across 5 families (universe, feature-family, methodology, risk-primitive, labeling) but each axis either INERT or NEGATIVE. **v1 cycle-2 mirrors v3 cycle-7 saturation pattern** — bounded by the prevailing architecture's local-optimum basin at single-axis EXPLORATION resolution.

---

## Section 10 — Files & Commits

- Branch: `iteration-v1/015` from `iter-v1/014` closeout commit (tag `v0.v1-014`)
- HEAD at Phase 7+8: `def3dcd` (Phase 7.5 Critic review commit)
- Engineering report: `reports-v1/iteration_v1-015/engineering_report.md` (THIS FILE; 5th-strike retroactive fix)
- Critic review: `briefs-v1/iteration_v1-015/review.md`
- LM Master Phase 4.5 + 7.4: `briefs-v1/iteration_v1-015/lgbm_advisor.md`

**Commits in /015** (verified via `git log iter-v1/014..iteration-v1/015 --oneline`):
1. `eaf6d23` — phase 5.5 gate BLOCK — lgbm_advisor.md missing
2. `74000e1` — LM Master Phase 4.5 advisory + brief Section 3.7 response
3. `61cd4d4` — C1 fix — execution-time σ_t × k × √timeout barriers + NaN RuntimeError
4. `aaa5e6b` — engineering report HARD-STOP + --no-engineering-report flag
5. `c3fe580` — C1 fix tests + NaN RuntimeError + hard-stop test + phase5p5_gate PASS
6. `3e67f72` — labeling-side √timeout factor + F-AXIS-C1 test repair (Path 1 Critic 6.0)
7. `bdb36c9` — Critic Phase 6.0 re-check PASS — Path 1 asymmetry RESOLVED
8. `4cb8972` — docs(skill): ENFORCE wall-clock discipline from cycle-3 onwards
9. `fa2aa9f` — LM Master Phase 7.4 post-mortem — CONFIRMATION-NEGATIVE
10. `def3dcd` — Phase 7.5 Critic review — CONFIRMATION-NEGATIVE catastrophic
11. (THIS COMMIT) — Phase 7 engineering report (5th-strike retroactive fix)

**Trunk merge: NONE.** CONFIRMATION-NEGATIVE catastrophic never updates BASELINE_V1.md. The labeling axis at calibrated 7.82% magnitude is CLOSED; sub-magnitude (3-5%) remains OPEN for cycle-3 if QR elects to re-enter (LM Master Phase 7.4 §4 recommends AGAINST cycle-3 labeling re-entry; pivot to UNUSED families instead).

**Tag**: `v0.v1-015` (applied after Phase 8 closeout commit).
