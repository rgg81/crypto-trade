---
iteration: iter-v1/015
date: 2026-05-26
verdict: CONFIRMATION-NEGATIVE
subtype: catastrophic
axis_family: labeling
cadence_position: cycle-2 CONFIRMATION (1 of 1; cycle-2 closes here)
anchor: v0.v1-baseline-corrected (BASELINE_V1.md commit f8bc12c) — UNCHANGED
merge_decision: NO-MERGE (CONFIRMATION-NEGATIVE catastrophic; F1-MULTI Δ -1.6117 (2.93× catastrophic floor) + F1-IS Δ -0.3474 + F-AXIS-MECHANISM HARD-FALSIFIER FAIL (n_eff=3 vs ≥17); BASELINE_V1 update NOT triggered)
---

# Iteration iter-v1/015 — Diary

## Decision: NO-MERGE

CONFIRMATION-NEGATIVE catastrophic. Cycle-2 CLOSES NO-MERGE across 10 iterations (1 PROMISING-METHODOLOGY non-compoundable + 9 NEGATIVE + 0 merges). v1 BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`).

## One-Line Outcome

At v1 CONFIRMATION budget (n_trials=35 + ENSEMBLE_SIZE=10 + V1_FEATURE_COLUMNS_PRUNED + Path 1 C1 FIX) the past-only EWMA σ_t × k × √timeout symmetric labeling at 7.82% portfolio-median barrier magnitude produced **IS Sharpe −0.0645** (Δ **−0.3474** NEGATIVE) + **OOS Sharpe −0.9480** (Δ **−1.6117** catastrophic; 2.93× the −0.55 floor; **worst OOS in cycle-2**) + **n_eff COLLAPSED 19 → 3** across all 5 per-symbol cells + **F-AXIS-MECHANISM HARD-FALSIFIER FAIL** (0/10 vs ≥7/10) + **F-AXIS-C1 PASS** (no NaN RuntimeError; cache populated) + **LM Master FIRST DIRECTIONAL HIT in v1 history** (3/3 per-symbol C1-inversion verified — mechanism-deterministic call) — labeling axis CLOSED at calibrated 7.82% magnitude; cycle-2 closes NO-MERGE.

## What Worked

### LM Master Phase 4.5 §"Risk 2" per-symbol C1-inversion prediction VERIFIED 3 of 3

Prior IS PnL → /015 IS PnL Δ:
- LTC: +95.51 → −9.21 = Δ **−104.72** DOWN ✓ (matches "LTC IS+OOS likely DOWN")
- ETH: −99.73 → +17.34 = Δ **+117.07** UP ✓ (matches "BTC/ETH IS+OOS likely UP")
- BTC: −24.25 → −0.65 = Δ **+23.60** UP ✓ (matches "BTC/ETH IS+OOS likely UP")

**FIRST DIRECTIONAL HIT in 13 v1 iterations**. Honest distinction (Phase 7.4 §1): mechanism-deterministic call (C1 asymmetric windfall inversion when C1 FIXED), NOT a basin-lottery prediction. The C1 FIX removed the LTC windfall + BTC/ETH penalty asymmetry; per-symbol IS PnL shifted exactly as the mechanism predicted. Verdict-class magnitude F1/F3 calls remain at 0/13 directional — magnitude was a different layer than direction.

### IS net PnL recovered +167.73pp vs /014

Portfolio IS net PnL +40.74 vs /014 −126.99 = **+167.73 absolute swing**. The C1 FIX (symmetric σ_t × k × √timeout at both label-time AND execution-time) removed the asymmetric LTC windfall + BTC/ETH penalty pattern. Per-symbol IS halves recovered exactly as predicted. **Mechanism is real.**

### F-AXIS-C1 PASS (axis-completion verified)

Brief Section 7's programmatic F-AXIS-C1 falsifier "execution-time barrier matches label-time within 1e-6 tolerance" PASSED. No NaN RuntimeError fired (LM Master Rec #3 boundary enforcement functioning). σ_t cache `_month_sigma` correctly populated at boundary candles. The Path 1 C1 FIX implementation is structurally correct. The labeling axis was finally well-posed.

### F8-NEW PASS (trade count band)

620 IS trades ∈ [466, 776]. Trade-count band held at multi-seed.

### Mechanism-level credibility ledger advanced

LM Master Phase 7.4 §1 honest count:
- Mechanism-level: **6 PARTIAL+ of 13 predictions** (now includes /015 3/3 per-symbol C1-inversion + prior 5 PARTIAL hits: lookahead-clean, F8-NEW band, F7-NEW direction, n_eff prediction, FLAT prior calibration)
- Verdict-class magnitude: **0 / 13 directional** (F1-MULTI Δ −1.6117 NOT in pre-registered [−0.30, +0.30] band; magnitude miss continues)

Mechanism-level claims earn credibility under "CHARACTERIZED MECHANISM with disclaimer". Magnitude calls remain FLAT.

## What Failed

### F1-MULTI catastrophic (Δ −1.6117; 2.93× the catastrophic floor)

OOS Sharpe collapsed from baseline +0.6637 to /015 −0.9480 = **largest single-iteration OOS drop in cycle-2 catalog**. Falls outside the pre-registered prior band [−0.30, +0.30] entirely (3× the NEGATIVE-catastrophic boundary). The hypothesis "C1 FIX produces multi-seed mean OOS within [−0.30, +0.30]" was empirically refuted by orders of magnitude.

### F-AXIS-MECHANISM HARD-FALSIFIER FAIL (n_eff = 3 across all cells; predicted ≥17 at ≥7/10)

LM Master Phase 4.5 Rec #4: "F-AXIS-MECHANISM at >95% PASS — n_eff is bound by label-distribution SHAPE; seed-INDEPENDENT." Observed: n_eff_per_cell_median = 3 across BTC=4, DOT=3, ETH=4, LINK=3, LTC=3 — **6.3× drop from /014's 19**, **0/10 seeds at threshold**. Single largest miss in LM Master credibility-stake ledger.

**Mechanism**: 7.82% TP/SL over 21-candle timeout → most rows hit `timeout → sign(fwd_return)` fallback because ±7.82% excursions are rare in 21 8h-candles. Label distribution becomes **timeout-dominated**; Optuna can't distinguish hyperparameters → n_eff collapses. Model becomes near-trivial "predict fwd_return sign" → bad OOS.

### Path 1 was methodologically correct but empirically wrong

Critic + LM Master + Phase 6.0 + QR all endorsed Path 1 (add √timeout factor symmetrically at label-time AND execution-time) over Path 2 (drop √timeout — preserve /014's inadvertent 1.70% magnitude). Path 2 was the empirically right answer; Path 1 was the methodologically right answer. **DURABLE structural evidence (/014's n_eff=19 at 1.70% labels) SHOULD have outweighed EDA-prescribed magnitudes.** This is the cycle-2-closeout-level methodology lesson, NOT an LM-Master-only miss.

### LINK monopoly OOS concentration violation

LINK OOS +84.58 PnL = 285.05% of total OOS PnL. Gate 7 (top-symbol ≤ 30% absolute) FAIL by wide margin. The multi-seed dissolution did NOT mitigate single-symbol concentration at n_eff=3 (Optuna selects on noise, picks the lucky symbol).

### LTC catastrophic-reversal (the C1 windfall removed; the OOS pattern flipped)

/014 LTC OOS WINNER +24.49 (WR 50%) → /015 LTC OOS LOSER −38.75 (WR 25%) = Δ −63.24 — the **single largest per-symbol OOS swing**. C1 windfall removal worked exactly as predicted at the mechanism layer, but the portfolio combinator (LINK monopoly + LTC reversal + BTC/ETH negative) produced a high-daily-variance regime → OOS daily Sharpe collapsed despite +29.66 OOS net PnL.

## LM Master Advisory Tracking

- **Phase 4.5 confidence**: MEDIUM-HIGH on mechanism; LOW on verdict-class magnitude (per closing note: "55% NULL / 20% PROMISING / 25% NEGATIVE; P(STRICT BASELINE update) ≈ 7% unconditional")
- **Phase 4.5 recommendations** (7 total):
  - Rec #1 (Keep n_trials=35; do NOT bump to 50) — **ADOPTED** ✓
  - Rec #2 (ADD per-seed median Δ ≥ 0 robustness sub-gate) — ADOPTED as Pareto gate (Gate 10)
  - Rec #3 (C1 FIX boundary: explicit RuntimeError on σ_t=NaN) — **ADOPTED** (functioning at runtime ✓)
  - Rec #4 (F-AXIS-MECHANISM at >95% PASS) — **REFUTED at runtime** (0/10 vs ≥7/10; gross miss — n_eff CURVE not monotone)
  - Rec #5 (timeout_candles=21, √21≈4.58 calibration sound; DO NOT REGRID k_tp/k_sl) — **METHODOLOGICALLY CORRECT, EMPIRICALLY WRONG** (Path 1 self-critique §3)
  - Rec #6 (P(STRICT BASELINE update) ≈ 7% unconditional) — CONSISTENT with outcome (observed 0% — within NULL/NEGATIVE prior band)
  - Rec #7 (refined predictions: F1-MULTI band tightened to [−0.25, +0.25]) — REFUTED (observed Δ −1.6117 outside ALL bands)
- **Phase 7.4 post-mortem highlights** (verbatim from `briefs-v1/iteration_v1-015/lgbm_advisor.md` §1-8):
  - 3-of-3 per-symbol IS prediction VERIFIED — **FIRST DIRECTIONAL HIT in v1 history**; mechanism-deterministic, NOT basin-lottery
  - n_eff is a **CURVE in barrier-magnitude space** (1.70% → 19; 7.82% → 3) — **strongest structural finding of cycle-2**
  - Path 1 was methodologically correct but empirically wrong — DURABLE-EVIDENCE-OUTWEIGHS-EDA cycle-2 lesson
  - Track record: 1/13 directional + 5 PARTIAL (mechanism-level 6/13); honest credibility-stake unchanged at FLAT verdict-class prior
  - Labeling axis PARTIALLY CLOSED — closed at 7.82% magnitude; OPEN at 3-5% sub-magnitude midway (cycle-3 only if QR re-enters via n_eff sweep protocol)
  - Cycle-2 retrospective: v1 BASELINE highly basin-locked at multi-dim local optimum; single-axis EXPLORATION+CONFIRMATION discipline produced zero merges this cycle — analogous to v3 cycle-7 saturation pattern

## Critic Review Summary (briefs-v1/iteration_v1-015/review.md, HEAD def3dcd)

- Check 1 (Look-Ahead): PASS — `walk_forward.py:113` carries `train_end_ms = test_start_ms - embargo_ms`; σ_t pipeline past-only via EWMA `.shift(1)`; C1 closure complete
- Check 2 (Embargo): PASS — REQUIRED_GAP = 110 (22 × 5 symbols); centralized helper
- Check 3 (DSR/PBO/PSR): FAIL (binding at CONFIRMATION) — DSR_IS=−87.69, DSR_OOS=−38.77 (FAIL by orders of magnitude); PSR_monthly_vs_0 IS=0.450 / OOS=0.118 (FAIL both halves at 0.95); n_eff_per_cell_median=3 across all symbols (6.3× drop from /014)
- Check 4 (IC): PASS — no new feature family; baseline IC inherited
- Check 5 (ADF): PASS (with forward-mandate on n_eff=3 label-distribution stationarity)
- Check 6 (Pareto): N/A — `pareto_front.csv` MISSING; Gate 10 cannot be evaluated; F1-MULTI scalar decisive
- Check 7 (Reproducibility): WARN — engineering_report.md ran with `--no-engineering-report` opt-out at QE Phase 6 (5th-strike retroactive fix at Phase 7); spot-checks PASS; explicit `feature_columns=active_feature_columns` wiring
- Check 8 (Hypothesis-Implementation Alignment): PASS for registered hypothesis — implementation correctly executed brief spec; **hypothesis was empirically wrong**
- Check 13 (Anti-Patterns): PASS — A1/A2/A3/A4-A11/A12/A13/A14 all clean
- Check 14 (Axis Family): PASS — `labeling` declared; src/ diff exclusively in labeling.py + lgbm.py σ_t paths
- **OVERALL: CONFIRMATION-NEGATIVE catastrophic**

## Path Forward (from Critic Phase 7.5 review §"Path Forward")

Verbatim from `briefs-v1/iteration_v1-015/review.md`:

> Prior 5 EXPLORATION families: risk-primitive ×2 (/010, /011), methodology-substrate-test ×2 (/012, /013), labeling (/014). EXCLUDED from cycle-3 first 5 EXPLORATIONs per rotation discipline.

### Cycle-3 axis #1 — Sample-weighting by past-realized vol (`sample-weighting` NEW family)

López de Prado AFML Ch. 4: weight-by-uniqueness OR weight-by-realized-vol. Replace `abs(labeled_pnl)` sample weighting with weights inversely proportional to 30-day realized vol. **Wall-clock fit**: V1_FEATURE_COLUMNS_PRUNED at 193, ENSEMBLE_SIZE=3, n_trials=20, full 5-symbol universe → ≈ 1.5-1.8h (2h cap achievable). **Mechanism**: directly addresses /015's mechanism finding (timeout-dominated cells dominate loss surface; weighting these down should restore n_eff diversification at any barrier magnitude).

### Cycle-3 axis #2 — XGBoost head-to-head (`model-arch` UNUSED in v1 cycle-2)

Depth-wise growth (XGBoost) vs leaf-wise (LightGBM) on v1's 193-feature pruned stack. **Wall-clock fit**: keep V1_FEATURE_COLUMNS_PRUNED, ENSEMBLE_SIZE=3, n_trials=20, single-symbol-pair Model-A only (BTC+ETH pooled) — halves wall-clock; ≈ 1.5h. **Mechanism**: substrate-test on model-arch family at single-seed lottery resolution.

### Cycle-3 axis #3 — Universe expansion to 7-symbol with per-symbol drawdown brake (`universe` UNUSED in v1 since /006)

Add 2 symbols (SOLUSDT, NEARUSDT, or AVAXUSDT from V1_EXCLUDED_SYMBOLS) + per-symbol drawdown brake (NOT proportional cap — v3/020 closed that family). Brake fires hard-off when per-symbol cumulative drawdown crosses −X%; resets at calendar-month boundary (avoids /054-style deadlock). **Wall-clock fit**: 7 symbols × ENSEMBLE_SIZE=3 × n_trials=20 ≈ 2.0h; compress to 6 if tight. **Mechanism**: denominator expansion attenuates LINK-monopoly-of-OOS-PnL pattern; brake provides time-based escape.

Each axis from UNUSED family; each includes explicit wall-clock fit per NEW discipline (skill `4cb8972`). QR's first cycle-3 brief should EDA-justify one and propose remaining two as alternates per Section 11 template. (Per `feedback_v1_n_eff_barrier_magnitude_curve.md` — see Lessons #1 — any cycle-3 labeling sub-axis re-entry is BLOCKED until the n_eff sweep mandate is exercised.)

## Axis Rotation Status (v1-only)

- **This iter's family**: `labeling` (CONFIRMATION-spec, NOT new EXPLORATION rotation eligible)
- **Prior 5 EXPLORATION families**: `risk-primitive` (/010), `risk-primitive` (/011), `methodology-substrate-test` (/012), `methodology-substrate-test` (/013), `labeling` (/014)
- **Rotation honored**: YES — /015 is CONFIRMATION position by HIGH-RISK pre-commit (rotation discipline applies to EXPLORATION sequence only)
- **Cumulative same-family count**: N/A at CONFIRMATION
- **Cycle-3 first 5 EXPLORATION families MUST exclude**: `labeling`, `methodology-substrate-test`, `risk-primitive` (the prior 5 from cycle-2)

## Pre-Registered Failure-Mode vs Reality

From brief Section 7:
> "Predicted failure mode (P=25% NEGATIVE): multi-seed dissolution + C1 FIX could expose that σ_t labels at 7.82% portfolio-median barriers and 21-candle timeout still produce structurally-different label distributions vs baseline ATR-based labels. Per-row label degeneracy or single-symbol monopoly at multi-seed would manifest as: (a) n_eff PRESERVED ≥17 (mechanism intact, but variance not edge), (b) some per-symbol negative attribution beyond modal NULL band."

**Actual**: failure mode was **different layer** than predicted.
- **Predicted**: per-symbol negative attribution within modal NULL band
- **Actual**: **n_eff COLLAPSED 19→3** (predicted "PRESERVED ≥17"); F-AXIS-MECHANISM HARD-FALSIFIER FAIL; label distribution became timeout-dominated (`timeout_fallback_share > 0.85` estimated)

**Match**: NO. The predicted failure mode missed the load-bearing mechanism by directionally inverting it. n_eff was predicted to be "seed-independent" (true) but barrier-magnitude-monotone-increasing (false — n_eff is a CURVE in barrier-magnitude space). This is the strongest mechanism-finding of cycle-2; it is the precise gap that allowed Path 1 to be methodologically correct but empirically wrong.

## 5 LESSONS for v1 Cycle-2 Catalog + Cycle-3 Forward Discipline

### LESSON #1: n_eff is a CURVE in barrier-magnitude space, not a monotone function — strongest cycle-2 structural finding

The load-bearing structural finding of cycle-2. Two well-posed data points:
- **/014 at 1.70% labels** (inadvertent missing √timeout factor; effective barrier ≈ σ_t × k_tp without √timeout multiplier): **n_eff = 19** (optimal-diversity; range 14-22 per-symbol)
- **/015 at 7.82% labels** (Path 1 calibration EDA magnitude; σ_t × k_tp × √timeout symmetric): **n_eff = 3** (collapsed; range 1-7 per-symbol)

**4.6× barrier magnitude → 6.3× n_eff collapse via timeout-fallback dominance.** Mechanism: at 7.82% TP/SL over 21-candle timeout, most rows hit `timeout → sign(fwd_return)` fallback because ±7.82% excursions are rare in 21 8h-candles. Label distribution becomes timeout-dominated; Optuna can't distinguish hyperparameters → n_eff collapses.

**Optimum likely in 3-5% middle range** — at 1.70% labels TP-hit-dominated cells already well-distributed; at 5% labels mixed TP/SL/timeout distribution should preserve n_eff ≥ 15. The n_eff barrier-magnitude curve is **NEW structural finding** independently durable — codified into the project memory at `feedback_v1_n_eff_barrier_magnitude_curve.md`.

**Forward mandate (Critic Phase 7.5 Rec #1)**: before any future labeling sub-axis EXPLORATION, run the n_eff calibration sweep — test {1.5%, 2.5%, 3.5%, 5.0%, 7.82%} barriers at single-seed and chart n_eff per magnitude. Establish n_eff ≥ 15 preservation band BEFORE selecting CONFIRMATION magnitude.

### LESSON #2: First directional hit in 13 iterations was mechanism-deterministic, NOT basin-lottery — FLAT priors remain for verdict-class

LM Master Phase 4.5 §"Risk 2" per-symbol C1-inversion prediction verified 3/3 (LTC IS+OOS DOWN ✓, ETH IS+OOS UP ✓, BTC IS UP ✓). This is the **FIRST DIRECTIONAL HIT in 13 v1 iterations**. However:
- The call was **mechanism-deterministic** — C1 asymmetric windfall inversion mechanically reverses when C1 FIXED. Not a basin-lottery prediction.
- 3-of-3 in 1 iteration does NOT statistically reverse 0-for-12 verdict-class magnitude track record (N=1 directional after 12 FLATS is well within prior FLAT-prior uncertainty).
- **Direction does NOT translate to magnitude** — F1 multi-seed mean −1.6117 was NOT in predicted [−0.30, +0.30] band (magnitude miss continues).

**Track record (honest)**: 1/13 directional + 5 PARTIAL = mechanism-level 6/13. Verdict-class F1/F3 magnitude predictions remain 0/13 directional. **Future Phase 4.5 advisories MAY offer mechanism-deterministic per-symbol direction calls** (MEDIUM-HIGH confidence with "mechanism-deterministic" disclaimer) but verdict-class magnitude stays FLAT at single-seed; modal-NULL at multi-seed.

### LESSON #3: Path 1 was methodologically correct but empirically wrong — DURABLE-EVIDENCE-OUTWEIGHS-EDA cycle-2 lesson

Critic + LM Master + Phase 6.0 + QR all endorsed Path 1 (add √timeout factor symmetrically at label-time AND execution-time) over Path 2 (drop √timeout — preserve /014's inadvertent 1.70% magnitude). Path 1 was theoretically clean (realized-vol scaling demands √timeout). Path 2 was theoretically unclean (asymmetric implementation). **Path 2 was empirically right.**

**Lesson**: when prior iteration produces DURABLE STRUCTURAL EVIDENCE on a specific implementation (/014's n_eff=19 was the durable structural signal), that evidence should OUTWEIGH EDA-prescribed magnitudes even at the cost of theoretical cleanliness. This is the **cycle-2-closeout-level methodology lesson**, NOT an LM-Master-only miss — Critic + LM Master + Phase 6.0 all converged on Path 1 over Path 2.

**Future practice**: brief Section 2 (EDA evidence) MUST explicitly tag "DURABLE STRUCTURAL EVIDENCE from prior iteration" claims; brief Section 3 (Proposed Changes) MUST address any axis re-implementation that would dissolve such evidence with explicit dissolution-risk reasoning. Critic Phase 6.0 verifies the dissolution-risk reasoning is present and acceptable.

### LESSON #4: Cycle-2 closed NO-MERGE across 10 iterations — v1 BASELINE_V1 is highly basin-locked at multi-dim local optimum

10 iterations spanning 5 axis families (universe, feature-family, methodology, risk-primitive, labeling, methodology-substrate-test, hyperparameter-region):
- 1 PROMISING-METHODOLOGY (/008 n_eff PCA, **non-compoundable** as measurement substrate)
- 9 NEGATIVE
- **0 merges**
- BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected`

Single-axis EXPLORATION+CONFIRMATION discipline produced zero merges in this regime. The catalog is dispersed (no axis monoculture) but each axis at its single-axis resolution is either INERT or NEGATIVE within v1's basin.

**v1 cycle-2 mirrors v3 cycle-7 saturation pattern** (cf. `feedback_v3_cycle7_terminal_finding.md`): bounded by the prevailing architecture's local-optimum basin at single-axis EXPLORATION resolution. **The basin is the binding constraint, NOT the axis selection.** Cycle-3 should consider multi-axis composition OR explicit basin-escape mechanisms (universe expansion + sample-weighting bundled at the CONFIRMATION layer is one candidate) OR pivot to NEW UNUSED families with explicit single-axis isolation first.

### LESSON #5: Wall-clock discipline NOW ENFORCED from cycle-3 onwards — /015 was the last user-authorized exception

Skill update at commit `4cb8972` (`docs(skill): ENFORCE wall-clock discipline from cycle-3 onwards`) codifies QR responsibility to compress (n_trials, features, candles, symbols) to fit the 2h EXPLORATION cap and 6h CONFIRMATION cap (per `feedback_v1_wall_clock_discipline_enforced.md`).

User directive 2026-05-25 (verbatim at skill `4cb8972`):
> "The QR should choose a combination of symbols, features, candles, Optuna iterations to fit in the exploration (3 seeds) and the confirmation (10 seeds). That's non negotiable from now on."

**/015 was the last user-authorized exception** (used ENSEMBLE_SIZE=10 + n_trials=35 + V1_FEATURE_COLUMNS_PRUNED at full universe and ran ≈ 10h). Cycle-3 EXPLORATIONs MUST compress to fit 2h; CONFIRMATIONs MUST fit 6h. Future briefs include a wall-clock estimation row in Section 0.2 + an explicit dimension-trade table in Section 10. Critic Phase 6.0 validates the wall-clock estimate against the 2h/6h caps.

## Cycle-2 Retrospective

| Iteration | Family | Verdict | Edge ingredient? |
|---|---|---|---|
| /006 | universe | EXPLORATION-NEGATIVE (DEGENERATE_PREDICTOR) | NO |
| /007 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) | NO |
| **/008** | **methodology** | **EXPLORATION-PROMISING-METHODOLOGY** (n_eff PCA per-cell median) | NO (non-compoundable measurement substrate) |
| /009 | feature-family | EXPLORATION-NEGATIVE (NEGATIVE-NEGATIVE compound) | NO |
| /010 | risk-primitive | EXPLORATION-NEGATIVE (PROMISING-INERT-with-IS-basin-shift) | NO |
| /011 | risk-primitive (binary-kill) | EXPLORATION-NEGATIVE (catastrophic-basin-shift) | NO |
| /012 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-INHERITANCE-WITH-MECHANICAL-CLEANUP-PARTIAL) | NO |
| /013 | methodology-substrate-test | EXPLORATION-NEGATIVE (BASIN-LOTTERY-CATASTROPHIC) | NO |
| /014 | labeling | EXPLORATION-NEGATIVE (Cell-5 + PARTIAL-F7 + DURABLE-n_eff-MECHANISM) | NO (DURABLE n_eff=19 mechanism finding inherited by /015 design) |
| **/015** | **labeling** (CONFIRMATION) | **CONFIRMATION-NEGATIVE catastrophic** | NO (axis CLOSED at 7.82% magnitude; n_eff barrier-magnitude curve = strongest structural finding) |

**Cycle-2 verdict distribution after /015**: 0 pure PROMISING / 1 PROMISING-METHODOLOGY non-compoundable (/008) / 9 NEGATIVE / 1 CONFIRMATION-NEGATIVE catastrophic — **0 edge ingredients merged**. v1 BASELINE_V1.md UNCHANGED.

**Cycle-2 structural contributions** (carry forward as DURABLE evidence to cycle-3+ but NOT as merged edge ingredients):
1. **/008 n_eff PCA per-cell median** — measurement substrate; non-compoundable; informs all v1 brief Section 7 F-AXIS-MECHANISM falsifiers
2. **/015 n_eff barrier-magnitude curve** — NEW structural finding; informs all future labeling axis design (n_eff sweep mandate before CONFIRMATION; optimum in 3-5% middle); codified into `feedback_v1_n_eff_barrier_magnitude_curve.md`

**Cycle-2 dead-paths** (do not retry without new evidence):
- ATR-multiplier per-leg asymmetry (/004 ETH SL-noise-floor death; absolute SL distance < 1.5× NATR_p50 red line)
- Per-leg differentiated Optuna bounds (/005 F2 ρ STRUCTURAL-locked at 0.95; v1-analog of v3 cycle-7 terminal finding applied earlier)
- σ_t labeling at 7.82% portfolio-median magnitude (/015 n_eff collapse; timeout-fallback dominance)
- Methodology-substrate-test family (3 consecutive /012/013/015 effectively NEGATIVE; basin-substrate properties at single-seed are not the binding lever)

## Next Iteration Ideas (cycle-3 first EXPLORATION)

Ranked by expected impact within the NEW 2h EXPLORATION wall-clock cap (skill `4cb8972`):

1. **Sample-weighting by past-realized vol** (`sample-weighting` NEW family) — LM Master Phase 7.4 §7 Priority 3 + Critic Phase 7.5 Path Forward #1; AFML Ch. 4 grounding; directly addresses /015's timeout-fallback dominance via weighting timeout cells down. **Wall-clock fit**: V1_FEATURE_COLUMNS_PRUNED, ENSEMBLE_SIZE=3, n_trials=20, full 5-symbol universe → ≈ 1.5-1.8h.

2. **Universe expansion to 7-symbol with per-symbol drawdown brake** (`universe` UNUSED since /006) — LM Master Phase 7.4 §7 Priority 1 + Critic Phase 7.5 Path Forward #3; denominator expansion attenuates LINK-monopoly OOS pattern. **Wall-clock fit**: 7 symbols × ENSEMBLE_SIZE=3 × n_trials=20 ≈ 2.0h. Add SOL or NEAR or AVAX (V1_EXCLUDED_SYMBOLS). Per-symbol drawdown brake (NOT proportional cap — v3/020 closed that for v3).

3. **XGBoost head-to-head** (`model-arch` UNUSED in v1 cycle-2) — LM Master Phase 7.4 §7 Priority 2 + Critic Phase 7.5 Path Forward #2; depth-wise (XGBoost) vs leaf-wise (LightGBM) on v1's PRUNED stack. **Wall-clock fit**: single-symbol-pair Model-A only (BTC+ETH pooled), n_trials=20, ENSEMBLE_SIZE=3 → ≈ 1.5h.

All three from UNUSED families; rotation discipline respected. Cycle-3 first EXPLORATION QR EDA-justifies one and proposes remaining two as alternates per Section 11 template under NEW 2h wall-clock discipline.

## Files & Commits on Branch

- Branch: `iteration-v1/015` from `iter-v1/014` closeout commit (tag `v0.v1-014`)
- HEAD at Phase 7 closeout (commit #1 in this Phase 7+8 closeout): `17ab95e`
- HEAD at Phase 8 closeout (THIS COMMIT): TBD

Key commits in /015:
- `eaf6d23` — Phase 5.5 gate BLOCK — lgbm_advisor.md missing
- `74000e1` — LM Master Phase 4.5 advisory + brief Section 3.7 response
- `61cd4d4` — feat(iter-v1/015): C1 fix — execution-time σ_t × k × √timeout + NaN RuntimeError
- `aaa5e6b` — feat(iter-v1/015): engineering report HARD-STOP + --no-engineering-report flag (5th-strike defect surface — opt-out exercised)
- `c3fe580` — test(iter-v1/015): C1 fix tests + NaN RuntimeError + hard-stop test + phase5p5_gate PASS
- `3e67f72` — fix(iter-v1/015): labeling-side √timeout factor + F-AXIS-C1 test repair (Path 1 Critic 6.0)
- `bdb36c9` — docs(iter-v1/015): Critic Phase 6.0 re-check PASS — Path 1 asymmetry RESOLVED
- `4cb8972` — docs(skill): ENFORCE wall-clock discipline from cycle-3 onwards
- (Backtest dispatched; comparison.csv + reports artifacts in `reports-v1/iteration_v1-015/`)
- `fa2aa9f` — docs(iter-v1/015): LM Master Phase 7.4 post-mortem — CONFIRMATION-NEGATIVE
- `def3dcd` — docs(iter-v1/015): Phase 7.5 Critic review — CONFIRMATION-NEGATIVE catastrophic
- `17ab95e` — docs(iter-v1/015): QR Phase 7 evaluation + engineering report (5th-strike fix)
- (THIS COMMIT) — Phase 8 diary + catalog + cycle-2 closeout + n_eff barrier-magnitude curve memory

**Trunk merge**: NONE. CONFIRMATION-NEGATIVE catastrophic never updates BASELINE_V1.md. The σ_t labeling axis is CLOSED at calibrated 7.82% magnitude; OPEN at 3-5% sub-magnitude only IF cycle-3 elects to re-enter via the n_eff sweep mandate (Critic Phase 7.5 Rec #1).

**Tag**: `v0.v1-015` (applied after this Phase 8 closeout commit).
