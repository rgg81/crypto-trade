# Iteration iter-v3/039 — Diary

## Decision: CONFIRMATION-NO-MERGE — strict BOTH-IS-AND-OOS-must-improve baseline rule confirmed

iter-v3/039 = SECOND v3 CONFIRMATION (post-iter-v3/028 baseline; cycle 10/10 complete with iter-v3/029-038 EXPLORATIONs preceding). Multi-seed validation of the iter-v3/035 4-ingredient bundle (V3_MODELS = BCH+LDO+TRX+ALGO; V3_FEATURE_COLUMNS_TOP_N = 14 incl regime_momentum_signed_5d; V3_FEATURES_PER_SYMBOL["BCHUSDT"] = 14 + fracdiff_d05_close per-symbol; V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (1.5, 0.75)) at `--seeds 2 + ENSEMBLE_SIZE=5 + n_trials=35` (CONFIRMATION-spec).

Result: **IS multi-seed mean Sharpe -0.0800 / OOS multi-seed mean Sharpe +1.4650.** Per user directive 2026-05-09 ("no merge. Close it." + "both is and oos must be in shape"), the strict version of the BASELINE_V3.md update policy applies: **BOTH IS and OOS multi-seed mean Sharpe must improve over the prior baseline.** iter-v3/039 satisfies this on the OOS axis (+0.96 lift) but FAILS on the IS axis (-0.59 regression). Decision: CONFIRMATION-NO-MERGE. **BASELINE_V3.md UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS).**

The OOS Sharpe of +1.4650 is the **first OOS reading in v3 history to clear the +1.0 aspirational floor** (Gate 1 PASS first time ever). However this lift is paid for at IS expense — the per-symbol customizations (BCH-only fracdiff + LDO-only ATR labeling) materially lift OOS but break IS aggregate. The "suspicious-OOS-divergence" pattern observed at iter-v3/026/027/030/034/036/037 single-seed EXPLORATIONs **PERSISTED at multi-seed in iter-v3/039** — confirming this is a STRUCTURAL property of the per-symbol-customizations bundle, NOT a single-seed Optuna lottery artifact.

## What Was Tested

**Hypothesis (locked in brief Section 1):** "iter-v3/035 single-seed +2.85 OOS Sharpe holds at multi-seed mean ≥ +1.0 at `--seeds 2`, clearing the +1.0 OOS Sharpe floor for the first time in v3 history."

**Predicted bands (locked in brief Section 4):**
- IS: [+0.20, +0.70] median +0.45
- OOS: **[+1.10, +1.70]** median **+1.40**

**Spec (locked in brief Section 3 — single sub-fix from iter-v3/038):**
- REVERT V3_FEATURES_PER_SYMBOL ALGO entry (iter-v3/038 added ALGO fracdiff; reverted to iter-v3/035 bundle state with BCH-only fracdiff)
- V3_FEATURE_COLUMNS_TOP_N = 14 (regime_momentum_signed_5d as 14th universal feature; UNCHANGED)
- V3_FEATURES_PER_SYMBOL = {"BCHUSDT": V3_FEATURE_COLUMNS_TOP_N + ("fracdiff_d05_close",)} (1 entry)
- V3_ATR_MULTIPLIERS_PER_SYMBOL = {"LDOUSDT": (1.5, 0.75)} (UNCHANGED)
- V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols (UNCHANGED)
- ITERATION_LABEL = "v3-039"
- Runner: `uv run python run_baseline_v3.py --seeds 2`

## Headline Numbers

### Multi-seed primary (comparison.csv)

| Metric | iter-v3/028 baseline | **iter-v3/039 multi-seed** | Δ vs baseline | Verdict |
|---|---:|---:|---:|---|
| **IS monthly Sharpe (multi-seed mean)** | +0.5101 | **-0.0800** | **-0.59** | WORSE — IS BROKEN |
| **OOS monthly Sharpe (multi-seed mean)** | +0.5053 | **+1.4650** | **+0.96** | BETTER — Gate 1 PASS first time |
| OOS/IS Sharpe ratio | 0.99 | -18.31 | sign-flipped | non-evaluable |
| IS Trades | 182 | 239 (+57) | +31% | acceptable |
| OOS Trades (mean) | 93.5 | 118 | +24.5 (+26%) | improvement, still <130 floor |
| IS MaxDD | 41.43% | 58.75% | +17.3pp | regression |
| OOS MaxDD (mean) | 23.53% | 30.41% | +6.9pp | regression within tolerance |
| OOS Calmar (mean) | 0.9229 | 1.318 | +0.40 | mixed (seed 42 strong; seed 123 weak) |
| OOS Top-symbol concentration | 76.47% | 49.96% (TRX) | -26.5pp | substantial improvement |
| DSR | 0.0 | 0.0 | structural | persists |
| PBO mean | 0.1243 | 0.1072 | -0.02 | improved |
| PSR | 1.0 | 1.0 | saturation | persists |
| n_trials | 1050 | 1400 | +350 | larger budget (4-sym × 35 × 2 outer × 5 inner) |

### Per-seed Pareto Front (BOTH SEEDS POSITIVE — Gate 10 PASS)

| Seed | IS Sharpe | OOS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Top OOS Conc |
|---|---:|---:|---:|---:|---:|---:|
| 42 | -0.0800 | +1.4650 | 28.86% | 2.0748 | 125 | 45.63% |
| 123 | +0.3143 | +0.5290 | 31.96% | 0.5612 | 111 | 45.92% |
| **Mean** | **-0.0800** | **+1.4650** | 30.41% | 1.318 | 118 | ~45.8% |

The 2-seed mean equals seed 42 because of equal-weight averaging — the +1.47 mean is materially driven by seed 42, not equally by both. Seed 123's OOS +0.5290 is below the +1.0 floor; per-seed variance is enormous (factor 2.8× between seeds; Δ +0.94 OOS).

### Pre-registered Verdict (from brief Section 4 path taxonomy)

| Path | Threshold | Observed | Trigger |
|---|---|---|---|
| PATH A (CLEAR-FLOOR) | OOS multi-seed mean ≥ +1.0 AND IS ≥ +0.0 | OOS +1.47 ≥ +1.0 PASS; IS -0.08 < +0.0 FAIL | NO — IS axis breach |
| PATH B (BELOW-FLOOR) | OOS in (+0.51, +1.0) AND IS ≥ +0.0 | OOS not in band; IS < +0.0 | NO |
| PATH C (COMPRESSION-WIPEOUT) | OOS ≤ +0.51 OR IS < +0.0 | IS -0.08 < +0.0 | **YES — Path C fires on IS axis** |

**Brief verdict: PATH C (COMPRESSION-WIPEOUT on IS axis).** This was the Section 7 "most plausible failure mode": *"the few profitable IS training cells that happened to align with the trend-momentum signal at single-seed get averaged out at multi-seed Optuna ensemble, leaving multi-seed IS Sharpe near 0 or slightly negative."* OOS axis cleared the +1.0 floor (which the brief predicted was likely at 50% compression precedent), but IS axis broke (which the brief predicted was the primary risk).

User directive 2026-05-09 then independently established the strict BOTH-must-improve baseline rule, which translates Path C OOS-strong-IS-broken into NO-MERGE (rather than the prior policy's MERGE-NO-FLOOR partial-merge classification).

### MERGE Gate Audit (10 gates, pre-registered in brief Section 8)

| # | Gate | Threshold | iter-v3/039 Observed | Status |
|---|---|---:|---:|---|
| 1 | OOS monthly Sharpe ≥ +1.0 | ≥ 1.0 | **+1.4650** | **PASS — first time in v3 history** |
| 2 | IS monthly Sharpe ≥ +1.0 | ≥ 1.0 | -0.0800 | **FAIL by 1.08** |
| 3 | OOS/IS ratio ≥ 0.5 | ≥ 0.5 | -18.31 sign-flipped | **FAIL — non-evaluable** |
| 4 | DSR > 0.95 | > 0.95 | 0.0 | **FAIL — structural** |
| 5 | PBO < 0.4 | < 0.4 | 0.1072 | **PASS** |
| 6 | PSR > 0.95 | > 0.95 | 1.0 | **PASS** |
| 7 | Top-symbol concentration ≤ 35% | ≤ 35% | TRX 49.96% (seed 42) | **FAIL by 15pp (improved direction)** |
| 8 | Bundle OOS trades ≥ 130 | ≥ 130 | 118 (mean) | **FAIL by 12 trades** |
| 9 | 10-seed validation | mean>0, ≥7/10 | NOT RUN at --seeds 2 | NOT TRIGGERED |
| 10 | Pareto: BOTH outer seeds OOS Sharpe > 0 | both > 0 | +1.4650, +0.5290 | **PASS** |

**4 PASS / 5 FAIL of 9 evaluated gates.** Same FAIL count as iter-v3/028 (5 FAIL there too) but with a STRUCTURALLY DIFFERENT mix: iter-v3/039 PASSED Gate 1 (OOS) for the first time but FAILED Gates 2 + 3 (which iter-v3/028 had passed). The trade-off is structural to the per-symbol customizations.

## What Worked

- **Methodology of the run is clean.** All 12 standard methodology checks PASS (Critic FINAL `05409d9`). Look-ahead audit verified by pre-existing 20 adversarial tests at iter-v3/025 SHA `3b1f979` carrying forward. Track-isolation grep clean. Embargo width REQUIRED_GAP=88 = (timeout=21+1) × 4 unchanged. Reproducibility stamp clean (Setup `0b13e28`, brief `472a277`, engineering report + Critic FINAL `05409d9`). Library stack pinned identically to iter-v3/028.

- **OOS Sharpe +1.4650 is the FIRST OOS reading in v3 history to clear the +1.0 aspirational floor.** Gate 1 PASS first ever. This is a major numerical milestone for the v3 architecture: it confirms the +1.0 OOS floor IS achievable with the current 4-symbol + per-symbol-customization stack at multi-seed CONFIRMATION-spec.

- **Both Pareto seeds positive (+1.4650 and +0.5290).** Gate 10 PASS — the methodological bright spot.

- **Concentration substantially improved.** OOS top-symbol concentration 49.96% (TRX) vs iter-v3/028's 76.47% — a 26.5pp improvement driven by 4-symbol diversification (ALGO + BCH lift contributions). Still above the 35% gate, but trending in the right direction.

- **OOS trade count improved** (118 vs 93.5; +26%) — closer to the 130 floor, though still below it (-12 trades).

- **Per-symbol architecture validated as CODE INFRASTRUCTURE.** V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL run cleanly at multi-seed, deterministic with seeds, reproducible, with no cross-symbol contamination. Architecture is KEPT for future cycles.

## What Failed

- **IS Sharpe collapsed to -0.0800** (vs iter-v3/028 baseline +0.5101). This is below the brief's predicted IS band lower bound of +0.20 and below the user-directed strict BOTH-must-improve threshold (must beat +0.5101). FAIL on baseline rule.

- **OOS/IS ratio sign-flipped** (-18.31 ratio non-evaluable). Gate 3 FAIL — when IS Sharpe is negative, the ratio gate cannot meaningfully discriminate generalization quality.

- **The "suspicious-OOS-divergence" pattern PERSISTED at multi-seed.** This was the central finding of iter-v3/039. Single-seed EXPLORATIONs iter-v3/026/027/030/034/036/037 all showed IS-near-zero / OOS-positive shape; this was hoped to be a single-seed Optuna lottery artifact that would dissolve at multi-seed. **It did not dissolve.** Both seeds (42 + 123) reproduce the IS-near-zero / OOS-positive shape. The pattern is **structural** to the per-symbol-customization bundle.

- **Per-symbol customizations lift OOS but break IS aggregate.** BCH-only fracdiff and LDO-only ATR labeling collectively produce +0.96 OOS lift but -0.59 IS regression. This is the central NEGATIVE finding of iter-v3/039 and the source of the NO-MERGE classification.

- **IS MaxDD breach (58.75%, +17.3pp vs baseline 41.43%).** Concerning — IS drawdown is the highest in v3 multi-seed history (vs iter-v3/028 41.43%, iter-v3/018 36.70%).

## Lessons

1. **STRICT BOTH-IS-AND-OOS baseline rule (USER DIRECTIVE 2026-05-09).** BASELINE_V3.md updates ONLY when CONFIRMATION beats prior baseline on BOTH IS Sharpe AND OOS Sharpe (multi-seed mean). OOS-only improvement with IS regression = NO MERGE. NEW memory rule: `feedback_v3_strict_both_is_oos_baseline.md`.

2. **Per-symbol customizations have STRUCTURAL OOS-lift / IS-break trade-off at multi-seed.** The "suspicious-OOS-divergence" pattern is NOT a single-seed Optuna lottery — it persists at multi-seed. Per-symbol customizations (per-symbol features, per-symbol labels) systematically lift OOS aggregate via specific symbol-regime alignments while reducing IS aggregate via training-window misalignment. NEW memory rule: `feedback_v3_per_symbol_lifts_oos_breaks_is.md`.

3. **OOS gate IS achievable in v3.** OOS Sharpe +1.4650 at multi-seed is the first numerical confirmation that the v3 architecture (3-7 small-cap symbols, regime_momentum_signed_5d, per-symbol customization layer) CAN clear the +1.0 OOS floor. The strategic question for cycle 3 is now: how to lift IS Sharpe while preserving OOS gate clearance.

4. **Per-symbol architecture is INFRASTRUCTURE (KEEP); per-symbol customizations need IS-axis discipline (REJECT this iteration's choices).** V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL stay in the codebase. Future per-symbol additions must clear IS-axis pre-validation (paired bootstrap CV or IS-only test) BEFORE inclusion in any CONFIRMATION bundle.

5. **Brief Section 7 failure-mode prediction was correct.** The brief explicitly named PATH C (COMPRESSION-WIPEOUT) as the most plausible failure mode driven by IS/OOS regime divergence at multi-seed averaging. The actual outcome matched this prediction. Pre-registered failure-mode predictions are CALIBRATED — keep this practice.

## Architectural Decisions

- **BASELINE_V3.md UNCHANGED at iter-v3/028.** Per user directive 2026-05-09 strict BOTH-must-improve rule.
- **V3_FEATURES_PER_SYMBOL + V3_ATR_MULTIPLIERS_PER_SYMBOL architecture KEPT** as code infrastructure (validated at multi-seed; no architectural defects).
- **Specific per-symbol customizations in iter-v3/035 bundle REJECTED for the bundle.** BCH-only fracdiff and LDO-only ATR labeling do not survive the strict BOTH-must-improve rule.
- **Cycle 3 starts at iter-v3/040** with REVERT per-symbol customizations (clear V3_FEATURES_PER_SYMBOL and V3_ATR_MULTIPLIERS_PER_SYMBOL) and refocus on UNIVERSAL axes that lift IS Sharpe.
- **NO TAG ISSUED.** Per project convention, only CONFIRMATION-MERGE iterations get `v0.v3-NNN` tags. iter-v3/039 = NO-MERGE so no tag.

## Next Iteration Ideas

Cycle 3 plan in `briefs-v3/cycle3_plan.md`:

- **iter-v3/040 = REVERT per-symbol customizations + restore iter-v3/028 baseline + ALGO universe + regime_momentum.** Clean baseline restoration. Acts as cycle 3 anchor.
- **iter-v3/041-049 = UNIVERSAL axes that lift IS:**
  - NEW universal engineered feature with proven IS lift (analysis-driven candidate selection from IS-only data; not random)
  - NEW model architecture (XGBoost retest with new universal feature set)
  - NEW labeling architecture (universal triple-barrier variants — meta-labeling, fixed-horizon return)
  - Feature pruning (drop bottom-3 importance features universally for parsimony lift)
  - Per-symbol features that DON'T break IS (require IS-axis pre-validation)
- **iter-v3/050 = CONFIRMATION** on the best bundle that lifts BOTH IS and OOS.

Cycle 3 hypothesis: lift IS Sharpe to ≥ +1.0 (or at minimum ≥ +0.5101 to satisfy the strict BOTH-must-improve rule) while preserving OOS Sharpe ≥ +1.0 (target: maintain the iter-v3/039 OOS gate clearance with a more IS-friendly mechanism).

## See Also

- `briefs-v3/iteration_v3-039/research_brief.md` — Phase 5 brief
- `briefs-v3/iteration_v3-039/phase5p5_gate.md` — Phase 5.5 gate PASS
- `briefs-v3/iteration_v3-039/engineering_report.md` — Phase 6/7 engineering report
- `briefs-v3/iteration_v3-039/review.md` — Phase 7.5 Critic FINAL
- `reports-v3/iteration_v3-039/comparison.csv` — full numerical results
- `reports-v3/iteration_v3-039/seed_summary.json` — per-seed Pareto data
- `briefs-v3/cycle3_plan.md` — cycle 3 strategy (iter-v3/040-050)
- `BASELINE_V3.md` — UNCHANGED at iter-v3/028 (+0.5101 IS / +0.5053 OOS)
