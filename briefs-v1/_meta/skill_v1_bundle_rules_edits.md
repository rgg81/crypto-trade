# Skill v1 — Bundle Discipline Rules — Line-Level Edits

**Status**: Synthesis of the QR-rules draft, QR-substrate-045 proposal, the Critic adversarial pass, and the LM Master substrate validation. Authored 2026-05-31 after the iter-v1/038 candidate veto exposed three gaps in the v1 skill: ad-hoc weight derivation, undeclared coin overlap, and backtest-only aggregation rules that cannot be replayed at `live/engine.py:_tick`.

This file specifies line-level CURRENT → PROPOSED edits to `.claude/commands/quant-iteration-v1.md`. Each edit is locally applied; the underlying rules and their rationale live in `skill_v1_bundle_rules_draft.md`.

---

## EDIT 1 — Append to "Methodology Gates (HARD; PRESERVED)" list

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: lines 224-231 (the existing bulleted gates list under "Methodology Gates (HARD; PRESERVED)")

**CURRENT** (lines 224-231):
```markdown
- **No look-ahead** (Critic Check 1)
- **Embargo applied** at every walk-forward fold boundary (Critic Check 2)
- **CV gap correct** = `(timeout_candles + 1) × n_symbols`
- **Reproducibility checksum match** — same flags + HEAD → same outputs (Critic Check 7)
- **No OOS tuning** — researcher discipline (Critic Check 8)
- **Feature-column pinning** — V1_FEATURE_COLUMNS_PRUNED enforced
- **Forming-candle drop** — `fetcher.py: if k.close_time < now_ms`
- **ADF stationarity** — features have unit-root rejection where declared (Critic Check 5)
```

**PROPOSED** — append three NEW bullets at the end of the list (preserve existing 8 bullets verbatim):
```markdown
- **Backtest-Live Parity** — bundle composition method must produce IDENTICAL trade decisions in backtest and at `live/engine.py:_tick`, using only same-time-snapshot per-component signals + each component's own internal sizing weight (Critic Check 15 — CONFIRMATION-PORTFOLIO only)
- **No Coin Overlap Across Bundle Components** — in a bundle, each coin is owned by EXACTLY ONE component (universe partition is pairwise-disjoint) (Critic Check 16 — CONFIRMATION-PORTFOLIO only)
- **IS-Only Weight Calibration** — bundle weights derived from IS-window data only by a committed `analysis/iteration_v1-NNN/weight_calibration.py`; weights pre-registered in brief Section 11 BEFORE Phase 6 launches; no OOS metric appears in the derivation chain (Critic Check 17 — CONFIRMATION-PORTFOLIO only)
```

---

## EDIT 2 — Append to "Portfolio Composition Rules" section

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: lines 966-973 (the existing 6 numbered rules under "### Portfolio Composition Rules (`CONFIRMATION-MERGE-PORTFOLIO` only)")

**CURRENT** (line 968 is rule 1):
```markdown
1. **Weights:** components combined via stacking, regime-conditional dispatch, or weighted ensemble. Weights must be DETERMINISTIC (no in-sample tuning of weights on OOS). UNCHANGED.
```

**PROPOSED** — REPLACE rule 1 with strengthened version, then APPEND rules 7, 8, 9 at the end:

```markdown
1. **Weights (HARD, IS-ONLY):** bundle weights are derived from IS-only data by a committed `analysis/iteration_v1-NNN/weight_calibration.py` and pre-registered in brief Section 11 BEFORE Phase 6 launches. Acceptable derivation methods (QR picks one and documents): EQUAL (`w_i = 1/N`); IS-Sharpe-proportional (`w_i = SR_IS_i / Σ SR_IS_j`, clipped at 0); IS-inverse-variance (`w_i ∝ 1/σ_IS_i`); IS-risk-parity; OR an explicitly-documented QR derivation. The script writes `bundle_weights.csv` with columns `[component_id, weight, derivation_method, is_window_start, is_window_end]`. NO OOS METRIC may appear in the script's data loads or computations. Enforcement: Critic Check 17 (CONFIRMATION-PORTFOLIO only).
```

**APPEND** rules 7, 8, 9 (preserve existing 2-6 verbatim):

```markdown
7. **No Coin Overlap (HARD):** in any bundle, NO single coin may appear in the universe of two or more component models. Each coin is owned by EXACTLY ONE component. Brief Section 11 MUST enumerate per-component universes and assert pairwise disjointness explicitly, plus document any re-composition decision (which coin was dropped from which component to admit the overlapping candidate). Enforcement: Critic Check 16 (CONFIRMATION-PORTFOLIO only).
8. **Backtest-Live Parity (HARD):** every bundle composition method MUST produce IDENTICAL trade decisions in backtest and live. The per-(symbol, candle) decision must be a deterministic function of (a) each component's signal at the SAME timestamp t (same-time-snapshot only), (b) each component's INTERNAL position-size weight (frozen pre-Phase 6 per rule 1), (c) static bundle configuration (universe assignment, dispatch rule). Forbidden constructs: summing realized PnL of simultaneously-open positions across two models in the same symbol; "net" exposure of two models in the same symbol netted into one Binance order; ANY rule referencing future bars relative to the decision candle. Enforcement: Critic Check 15 (CONFIRMATION-PORTFOLIO only).
9. **Section 11 mandatory sub-blocks:** brief Section 11 MUST contain — Universe Partition (per-component universes + `Pairwise disjoint: YES` assertion + union); Weight Derivation (method + script path + `bundle_weights.csv` quote + IS-only assertion); Backtest-Live Parity Statement (one-paragraph proof the decision rule is replayable at `live/engine.py:_tick`); Re-Composition Note (which coin was dropped from which component, with catalog cross-reference). Phase 5.5 gate BLOCKS on missing sub-block (cheap structural check); Phase 7.5 Critic Checks 15/16/17 BLOCK on substantive violation (semantic check).
```

---

## EDIT 3 — Section 11 Bundle Composition template

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: lines 1298-1310 (the existing "Section 11 — Bundle Composition (CONFIRMATION-only)" template)

**CURRENT** (lines 1298-1310):
```markdown
## Section 11 — Bundle Composition (CONFIRMATION-only)

For CONFIRMATION iterations of TYPE = `CONFIRMATION-PORTFOLIO`, declare:

- **Components included** (from prior EXPLORATIONs):
  - iter-v1/NNN-a: <regime role> — <one-sentence summary>
  - iter-v1/NNN-b: <regime role> — <one-sentence summary>
- **Composition method:** stacking / ensembling / regime-conditional dispatch / weighted average / other (specify)
- **Regime coverage table:** every tagged regime; which component(s) cover it; bundle-attributed Sharpe per regime
- **Pairwise OOS correlation table:** all component pairs; reject bundle if any pair > 0.70
- **Component substitution test:** for each component, predict bundle OOS Sharpe WITHOUT that component
- **Bundle-level OOS/IS prediction:** explicit prediction of the composite OOS/IS ratio (this IS the bundle gate)
```

**PROPOSED** — REPLACE entire block with extended version (preserve existing bullets, add 4 new mandatory sub-blocks):

```markdown
## Section 11 — Bundle Composition (CONFIRMATION-only)

For CONFIRMATION iterations of TYPE = `CONFIRMATION-PORTFOLIO`, declare ALL of the following sub-blocks. Phase 5.5 BLOCKS if any sub-block is missing; Phase 7.5 Critic Checks 15/16/17 BLOCK on substantive violations.

- **Components included** (from prior EXPLORATIONs):
  - iter-v1/NNN-a: <regime role> — <one-sentence summary>
  - iter-v1/NNN-b: <regime role> — <one-sentence summary>
- **Composition method:** stacking / ensembling / regime-conditional dispatch / weighted average / other (specify)
- **Regime coverage table:** every tagged regime; which component(s) cover it; bundle-attributed Sharpe per regime
- **Pairwise OOS correlation table:** all component pairs; reject bundle if any pair > 0.70 (subject to correlation justification per rule 3)
- **Component substitution test:** for each component, predict bundle OOS Sharpe WITHOUT that component
- **Bundle-level OOS/IS prediction:** explicit prediction of the composite OOS/IS ratio (this IS the bundle gate)

### 11.A — Universe Partition (HARD, Rule 7)

```markdown
- Component A (iter-v1/NNN-a): {SYMBOLS}
- Component B (iter-v1/NNN-b): {SYMBOLS}
- Component C (iter-v1/NNN-c): {SYMBOLS}
- Pairwise disjoint: YES  (A ∩ B = A ∩ C = B ∩ C = {})
- Union: {ALL SYMBOLS}
```

If any pair is non-disjoint → BLOCK at Phase 5.5 (cheap) AND Critic Check 16 (deep).

### 11.B — Weight Derivation (HARD, Rule 1)

- **Method**: equal / IS-Sharpe-proportional / IS-inverse-variance / IS-risk-parity / other (specify)
- **Script**: `analysis/iteration_v1-NNN/weight_calibration.py` (committed before Phase 6.0 Critic pre-flight)
- **Artifact**: `analysis/iteration_v1-NNN/bundle_weights.csv` (committed before Phase 6.0)
- **Quote** (verbatim from `bundle_weights.csv`):

```csv
component_id,weight,derivation_method,is_window_start,is_window_end
<...>,<...>,<...>,<...>,<...>
```

- **IS-only assertion**: "Every loaded timestamp satisfies `close_time < OOS_CUTOFF_MS`. No reference to `out_of_sample`, `>= OOS_CUTOFF_MS`, or post-2025-03-24 dates used to filter IN appears in `weight_calibration.py`." (Critic Check 17 greps the script for these patterns.)

### 11.C — Backtest-Live Parity Statement (HARD, Rule 8)

One paragraph: prove the bundle's per-(symbol, candle) decision is a pure function of `(symbol, t) → owning_component.signal_at(symbol, t)` and is implementable at `live/engine.py:_tick` using only same-time-snapshot signals plus each component's frozen internal weight. State explicitly that no path requires post-trade aggregation, netting, or future-bar reference. (Critic Check 15 reads this statement and traces it through the runner code.)

### 11.D — Re-Composition Note (Rule 7 escape valve)

If a component coin was dropped to satisfy Rule 7: which component, which coin, the resulting per-component metrics under the re-composition (rerun the smaller component without that coin and document IS Sharpe / OOS Sharpe / n_trades), and the catalog row that anchors the re-composed component. If no coin was dropped: state "no re-composition required (candidates were natively disjoint)".
```

---

## EDIT 4 — Phase 7.5 Critic checks 15, 16, 17 definitions

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: lines 846-852 (the existing v1-only Critic Check 14 — Axis Family Validation definition)

**CURRENT** (line 846):
```markdown
**1. New Check 14 — Axis Family Validation (v1-only).** Critic verifies axis family declared in brief Section 0.6 matches actual axis varied in src/ diff + reports.
```

**PROPOSED** — APPEND three new check definitions immediately after the Check 14 block (preserve Check 14 verbatim):

```markdown
**5. New Check 15 — Backtest-Live Parity (v1-only, CONFIRMATION-PORTFOLIO-only).** Critic verifies that the bundle's per-(symbol, candle) decision rule is a deterministic function of same-time-snapshot per-component signals + each component's frozen internal weight + static bundle config. The Critic traces the runner code's bundle aggregation step and asserts it is implementable at `live/engine.py:_tick`. Forbidden constructs (each → BLOCK-FINAL with reason `BUNDLE-PARITY-VIOLATION`): summing realized PnL across two models holding open positions in the same symbol; netting two-model exposure into a single Binance order requiring intra-tick reconciliation; any rule referencing future bars relative to the decision candle. EXPLORATION single-component iterations are EXEMPT — single component is trivially live-replayable.

**6. New Check 16 — Universe Disjointness (v1-only, CONFIRMATION-PORTFOLIO-only).** Critic computes pairwise universe intersections across all bundle components declared in brief Section 11.A. Any non-empty intersection → BLOCK-FINAL with reason `BUNDLE-UNIVERSE-OVERLAP`. Phase 5.5 also pre-checks Section 11.A for the `Pairwise disjoint: YES` assertion (cheap structural catch); Phase 7.5 Check 16 verifies the actual symbols match the runner's per-component universe (semantic catch). EXPLORATION single-component iterations EXEMPT.

**7. New Check 17 — Bundle Weight IS-Only Provenance (v1-only, CONFIRMATION-PORTFOLIO-only).** Critic verifies (a) `analysis/iteration_v1-NNN/weight_calibration.py` exists and is committed before Phase 6.0; (b) the script greps clean for `OOS_CUTOFF`, `>= OOS_CUTOFF_MS`, `oos_window`, `out_of_sample`, or hard-coded post-2025-03-24 dates used for filtering-IN (any forward-pointing reference → BLOCK-FINAL); (c) `bundle_weights.csv` matches brief Section 11.B verbatim; (d) each loaded data source in the script respects the IS-window cutoff. Any failure → BLOCK-FINAL with reason `BUNDLE-WEIGHT-OOS-LEAK`. EXPLORATION single-component iterations EXEMPT.
```

---

## EDIT 5 — Phase 7.5 dispatch prompt update

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: line 1448 (the `prompt:` string in the Critic Phase 7.5 dispatch block)

**CURRENT** (line 1448):
```
  prompt: "[Phase 7.5] [track: v1] Run Phase 7.5 adversarial review for iter-v1/NNN. Branch: iteration-v1/NNN. Report dir: reports-v1/iteration_v1-NNN. Brief dir: briefs-v1/iteration_v1-NNN. Read lgbm_advisor.md (both Phase 4.5 and Phase 7.4 sections) as supplemental input. Run all 8 mandatory checks + Check 14 (Axis Family Validation, v1-only) + optional 9-12. Emit review.md content as final message text with OVERALL ∈ {EXPLORATION-PROMISING, EXPLORATION-NEGATIVE, CONFIRMATION-MERGE, BLOCK-PENDING-FIX, BLOCK-FINAL}. **PATH FORWARD section MANDATORY on every BLOCK verdict.**"
```

**PROPOSED**:
```
  prompt: "[Phase 7.5] [track: v1] Run Phase 7.5 adversarial review for iter-v1/NNN. Branch: iteration-v1/NNN. Report dir: reports-v1/iteration_v1-NNN. Brief dir: briefs-v1/iteration_v1-NNN. Read lgbm_advisor.md (both Phase 4.5 and Phase 7.4 sections) as supplemental input. Run all 8 mandatory checks + Check 14 (Axis Family Validation, v1-only) + Check 15 (Backtest-Live Parity, CONFIRMATION-PORTFOLIO-only) + Check 16 (Universe Disjointness, CONFIRMATION-PORTFOLIO-only) + Check 17 (Bundle Weight IS-Only Provenance, CONFIRMATION-PORTFOLIO-only) + optional 9-12. Emit review.md content as final message text with OVERALL ∈ {EXPLORATION-PROMISING, EXPLORATION-NEGATIVE, CONFIRMATION-MERGE, CONFIRMATION-MERGE-PORTFOLIO, BLOCK-PENDING-FIX, BLOCK-FINAL}. BLOCK-FINAL reasons include: BUNDLE-PARITY-VIOLATION, BUNDLE-UNIVERSE-OVERLAP, BUNDLE-WEIGHT-OOS-LEAK. **PATH FORWARD section MANDATORY on every BLOCK verdict.**"
```

---

## EDIT 6 — Phase 8 diary Critic Review Summary block

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: lines 1337-1350 (the diary "Critic Review Summary" block)

**CURRENT** (lines 1349-1350):
```markdown
- Check 14 (Axis Family Validation): PASS / FAIL (v1-only)
- OVERALL: UNIVERSAL | REGIME-SPECIALIST-IS | REGIME-SPECIALIST-OOS | TAIL-CONTROL | EXPLORATION-PROMISING | EXPLORATION-NEGATIVE / TRUE-NEG | LEARNED-NEG | NEGATIVE-no-effect | CONFIRMATION-MERGE | CONFIRMATION-MERGE-PORTFOLIO | BLOCK-PENDING-FIX → final | BLOCK-FINAL | WALK-FORWARD-LEAKAGE
```

**PROPOSED** — INSERT three new lines after Check 14, REPLACE the OVERALL enumeration:

```markdown
- Check 14 (Axis Family Validation): PASS / FAIL (v1-only)
- Check 15 (Backtest-Live Parity): PASS / FAIL / N/A  (v1-only, CONFIRMATION-PORTFOLIO-only)
- Check 16 (Universe Disjointness): PASS / FAIL / N/A  (v1-only, CONFIRMATION-PORTFOLIO-only)
- Check 17 (Bundle Weight IS-Only Provenance): PASS / FAIL / N/A  (v1-only, CONFIRMATION-PORTFOLIO-only)
- OVERALL: UNIVERSAL | REGIME-SPECIALIST-IS | REGIME-SPECIALIST-OOS | TAIL-CONTROL | EXPLORATION-PROMISING | EXPLORATION-NEGATIVE / TRUE-NEG | LEARNED-NEG | NEGATIVE-no-effect | CONFIRMATION-MERGE | CONFIRMATION-MERGE-PORTFOLIO | BLOCK-PENDING-FIX → final | BLOCK-FINAL | WALK-FORWARD-LEAKAGE | BUNDLE-PARITY-VIOLATION | BUNDLE-UNIVERSE-OVERLAP | BUNDLE-WEIGHT-OOS-LEAK
```

---

## EDIT 7 — Phase 5.5 gate pre-checks (Section 11 sub-blocks)

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: lines ~643-658 (the Phase 5.5 gate's CONFIRMATION cadence verification block, near "Section 11 — Bundle Composition (CONFIRMATION-PORTFOLIO only)")

**CURRENT** (line 643):
```markdown
- **Section 11 — Bundle Composition** (CONFIRMATION-PORTFOLIO only). Components included + composition method + regime coverage table + pairwise correlation table + component substitution test + bundle-level OOS/IS prediction.
```

**PROPOSED** — REPLACE with extended set of mandatory sub-blocks:
```markdown
- **Section 11 — Bundle Composition** (CONFIRMATION-PORTFOLIO only). Components included + composition method + regime coverage table + pairwise correlation table + component substitution test + bundle-level OOS/IS prediction PLUS the four HARD sub-blocks:
  - **11.A — Universe Partition** with `Pairwise disjoint: YES` assertion. BLOCK if missing OR if `Pairwise disjoint: NO` is declared (Rule 7).
  - **11.B — Weight Derivation** with committed `analysis/iteration_v1-NNN/weight_calibration.py` + `analysis/iteration_v1-NNN/bundle_weights.csv` + IS-only assertion. BLOCK if any artifact missing (Rule 1). Phase 5.5 also greps `weight_calibration.py` for the patterns Check 17 enforces (cheap pre-screen; deep semantic check is Phase 7.5).
  - **11.C — Backtest-Live Parity Statement**. BLOCK if missing (Rule 8).
  - **11.D — Re-Composition Note**. BLOCK if missing (state "no re-composition required" if none was needed).
```

---

## EDIT 8 — Key Reminders additions

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: lines 1500-1525 (the "## Key Reminders — v1 (Refactored)" block)

**PROPOSED** — INSERT three new bullets between the existing MERGE Principle bullet (line 1513) and the v1-universe bullet (line 1514):

```markdown
- **Bundle weights are IS-only by HARD gate.** Every CONFIRMATION-PORTFOLIO bundle pre-registers a deterministic weight derivation in brief Section 11.B, computed by a committed `analysis/iteration_v1-NNN/weight_calibration.py` script that reads ONLY IS-window data. Any OOS reference in the derivation chain → BLOCK-FINAL `BUNDLE-WEIGHT-OOS-LEAK` at Phase 7.5 Critic Check 17.
- **No coin overlap across bundle components.** In a bundle, every coin is owned by EXACTLY ONE component. Brief Section 11.A enumerates per-component universes and asserts `Pairwise disjoint: YES`. Overlap → BLOCK-FINAL `BUNDLE-UNIVERSE-OVERLAP` at Phase 7.5 Critic Check 16 (or earlier at Phase 5.5 structural pre-check).
- **Backtest-live parity is HARD for bundles.** Every CONFIRMATION-PORTFOLIO bundle's composition method MUST produce IDENTICAL trade decisions in backtest and at `live/engine.py:_tick`. Section 11.C states the parity proof; aggregation rules referring to post-trade information (summed realized PnL across two models on the same symbol, etc.) → BLOCK-FINAL `BUNDLE-PARITY-VIOLATION` at Phase 7.5 Critic Check 15.
```

---

## EDIT 9 — Anti-Pattern catalog additions (A15, A16, A17)

**File**: `.claude/commands/quant-iteration-v1.md`
**Locate**: anti-pattern catalog (referenced from line 722, the Phase 6.0 mini-Check 13 description)

**PROPOSED** — wherever A1-A14 are catalogued, APPEND:

```markdown
- **A15 — Cross-Model Symbol Overlap In Bundle**: any CONFIRMATION-PORTFOLIO brief where Section 11.A enumerates two components that share at least one coin in their universes. Static scan during Phase 5.5 + Phase 6.0 mini-Check 13.
- **A16 — Bundle Weight Computed Post-OOS**: any commit to `analysis/iteration_v1-NNN/weight_calibration.py` AFTER the first commit to `reports-v1/iteration_v1-NNN/out_of_sample/`. Static scan during Phase 6.0 + Phase 7.5 Check 17.
- **A17 — Bundle Aggregation Requires Post-Trade Information**: any brief Section 11 method description containing "sum of realized PnL", "net position across models", "ex-post correlation-adjusted weight", or equivalent post-trade-information phrasing. Static scan during Phase 6.0 mini-Check 13.
```

(Note: existing catalog uses A14 for dead-feed data per `feedback_a14_dead_feed_data.md`. New entries start at A15.)

---

## Effectivity

Effective for iter-v1/045 and forward. iter-v1/044 (the current CONFIRMATION-PORTFOLIO in flight) is the LAST iteration NOT subject to Checks 15/16/17. Its merge decision is handled under the pre-existing Portfolio Composition Rules; if a Critic verdict on /044 surfaces a coin-overlap / weight-leak / parity issue post-hoc, the diary records it as "grandfathered under pre-2026-05-31 rules" and the iteration is NO-MERGE on the SUBSTANTIVE concern, not on the absent Check.

iter-v1/045 is the FIRST iteration designed under the new rules and serves as the reference implementation.
