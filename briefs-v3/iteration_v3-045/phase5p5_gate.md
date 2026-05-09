# Phase 5.5 Gate — iter-v3/045 (QR EDA-driven per-symbol ATR widening for LDO)

OVERALL: PASS

## Brief and Setup Commit Lineage

- QR EDA SHA `ed949fe` — `analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py` + outputs
  (`ldo_diagnosis.csv`, `synthesis.md`, `candidate_axes_ranking.md`).
- Brief SHA `4e2f699` — research brief (this iteration, single revision; no orchestrator-pick
  predecessor per `feedback_v3_axis_selection_quant_discipline.md`).
- Setup commit SHA `a6961a4` — feat(iter-v3/045): per-symbol ATR widening for LDOUSDT (2.0, 1.5).
- This gate authored against committed brief.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS
  windows in absolute dates stated (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS),
  OOS_CUTOFF_MS=1742774400000 declared. Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #6 of 10, wall-clock
  <= 2h, spec `--seeds 1` LightGBM. Single axis clearly enumerated: per-symbol ATR widening
  for LDOUSDT only (V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5); ALGOUSDT entry
  UNCHANGED at (2.0, 1.5) from iter-v3/044). Net feature count 14 stated. Predicted
  classification probabilities (PROMISING 35%, INERT 40%, NEGATIVE 25%) with rationale.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: widening LDOUSDT's SL multiplier
  from 1.0×ATR to 1.5×ATR (TP unchanged) reduces SL hit rate on LDO trades — IS→OOS
  exit-composition shift (SL:TP 1.14 → 2.33; SL rate 53.3% → 63.6%) as the binding
  constraint — by giving trades 50% more drawdown headroom under regime-shifted volatility.
  Mechanism named (per-symbol mechanical adjustment, mirrors iter-v3/044 PROMISING ALGO ATR
  mechanism). Falsifier implied by Path C threshold (LDO OOS PnL < -10%).
- Section 2 (IS-Only Evidence): PASS — Numerical tables from committed analysis script
  SHA `ed949fe`:
  - 2.1: LDO direction asymmetry IS+OOS table (LONG/SHORT/TOTAL).
  - 2.2: LDO IS→OOS exit composition shift table (the binding constraint).
  - 2.3: LDO regime mismatch carry-forward (natr 1.35× peer median, per iter-v3/032 EDA).
  - 2.4: Counterfactual LDO OOS lift estimate (+0.05 to +0.10 Sharpe at median band).
  - 2.5: LDO per-symbol importance distribution (FLAT 190-347).
  - 2.6: Why NOT iter-v3/032 LDO ATR (1.5, 0.75) — multi-seed-FALSIFIED at iter-v3/039;
    forbidden direction; this is OPPOSITE (wider not tighter).
  - 2.7: Predicted behavioral effect (LDO IS trade count -10% to +20%; portfolio ±2%).
  No category-matching. All numbers traceable to `ldo_diagnosis.csv` or trades.csv.
- Section 3 (Proposed Changes): PASS — 6 sub-fixes enumerated:
  - Sub-fix 1: ADD V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5).
  - Sub-fix 2: Update _verify_feature_columns assertions (specific assertions enumerated).
  - Sub-fix 3: Update tests/features_v3/test_atr_multipliers_for_symbol.py (5 tests).
  - Sub-fix 4: Update V3_ATR_MULTIPLIERS_PER_SYMBOL docstring with iter-v3/045 entry.
  - Sub-fix 5: Update ITERATION_LABEL = "v3-045".
  - Sub-fix 6: Update _verify_feature_columns docstring iter-v3/044 → iter-v3/045.
  Bundle state verification table present with 19 assertions.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS [+0.70, +1.00]
  median +0.80 to +0.90; OOS [iter-v3/044 OOS, iter-v3/044 OOS + 0.20] median
  iter-v3/044 + 0.05 to +0.10). Rationale derives quantitative estimates from sub-section
  2.4 counterfactual (1-3 SL→TP redirections × +6-9 PnL swing per trade). Pre-registered
  classification paths (PATH A PROMISING / PATH B-INERT / PATH B-MECHANICAL / PATH C
  NEGATIVE) with locked thresholds.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. IS-calibrated
  thresholds carry forward from iter-v3/044 baseline unchanged. LDO ATR widening risk
  explicitly diagnosed (wider SL = larger losing trade extremes; falsifier predicates
  trigger Pathway-C). **Stacking risk** (2 per-symbol ATR customizations: ALGO + LDO)
  explicitly enumerated with iter-v3/039 multi-seed precedent reference. IS trade-rate
  stability addressed with bounded prediction (±20% LDO, ±2% portfolio). Cross-symbol
  contagion bounded (<3% portfolio-level effect).
- Section 6 (Risk Management Design): PASS — 7-primitive table with config, enabled/disabled
  status for each gate. OOD fire-rate prediction bounded (±2% vs iter-v3/044; no feature
  subspace change since universal list stays at 14). Regime coverage noted across 4 symbols.
- Section 7 (Failure-Mode Prediction): PASS — Four forward-looking failure-mode paragraphs:
  (1) PROMISING-INERT via minimal LDO impact (most plausible at single-seed),
  (2) PROMISING-MECHANICAL via bit-identical LDO trades (Falsifier 1),
  (3) NEGATIVE-LDO-deepens (wider SL increases loss per trade without raising WR),
  (4) NEGATIVE-architecture-bug (BCH/TRX/ALGO drift; Falsifier 2).
  Diagnostic indicators stated. What gates should catch noted.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Pre-registered EXPLORATION outcome
  classification (PATH A PROMISING / PATH B-INERT / PATH B-MECHANICAL / PATH C with sub-types)
  with numerical thresholds. Locked before backtest with explicit no-post-hoc-renegotiation
  statement. Non-applicable MERGE criteria correctly noted (EXPLORATION spec).
- Section 9 (Library Stack): PASS — All 8 library versions pinned. No new libraries
  introduced. Per-symbol ATR is config-only change (no new feature implementations
  dispatched). No license risk. No fallbacks needed.
- Section 10 (QR Audit Trail): PASS (NEW required section per
  `feedback_v3_axis_selection_quant_discipline.md`) — EDA basis cited
  (analysis/iteration_v3-045/ldo_bottleneck_diagnosis.py SHA `ed949fe`), 7-bullet rationale
  for QR EDA findings, 5-candidate ranking summary, no-orchestrator-pick statement (per
  iter-v3/044 onward discipline), QR-driven selection rationale, brief committed BEFORE
  setup commit.
- Section 11 (Catalog-Row Pre-Commit): PASS — 5 outcomes pre-registered (PROMISING-clean,
  PROMISING-INERT, PROMISING-MECHANICAL, NEGATIVE-LDO-deepens, NEGATIVE-architecture-bug,
  NEGATIVE-stacking-suspect).

## One-Variable Check

Single primary variable: ADD `V3_ATR_MULTIPLIERS_PER_SYMBOL["LDOUSDT"] = (2.0, 1.5)`
alongside the existing `ALGOUSDT` entry from iter-v3/044. The ALGOUSDT entry is UNCHANGED
(no perturbation to iter-v3/044 axis). The DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) is
UNCHANGED. V3_FEATURE_COLUMNS_TOP_N is UNCHANGED at 14. V3_FEATURES_PER_SYMBOL is UNCHANGED
at empty. All other aspects of the bundle (V3_MODELS, REQUIRED_GAP, risk gates, library
stack) are bit-identical to iter-v3/044. PASS.

## Track Isolation

Not run here (Engineering Phase 6 check). Will be verified in pre-flight.

## Forbidden-Direction Check

The brief explicitly verifies it is NOT proposing iter-v3/032 LDO ATR (1.5, 0.75):
- Brief Section 2.6 explicitly cites iter-v3/039 multi-seed FALSIFICATION of (1.5, 0.75).
- Section 3 Sub-fix 1 specifies (2.0, 1.5) — wider SL, NOT tighter.
- The iter-v3/045 direction is OPPOSITE to iter-v3/032: TP unchanged at 2.0×ATR (vs 1.5×ATR
  in iter-v3/032); SL widened to 1.5×ATR (vs 0.75×ATR in iter-v3/032).
- Memory rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md` is HONORED: iter-v3/045 is a
  cycle 3 per-symbol-ATR addition AT THE LABELING LAYER ONLY, not in the iter-v3/035 bundle
  rejected at iter-v3/039. The mechanism (wider SL) is symmetric to iter-v3/044 ALGO PROMISING.

PASS — no forbidden direction; OPPOSITE direction; mirror of proven mechanism.

## Stacking Discipline Check

This is the SECOND per-symbol ATR customization (after iter-v3/044 ALGO). The brief Section
5 explicitly addresses stacking risk:
- iter-v3/039 multi-seed broke IS with feature+label stacking (BCH-fracdiff + LDO-(1.5,0.75)).
- iter-v3/045 stacks ALGO-(2.0,1.5) + LDO-(2.0,1.5) — both LABEL-LAYER ONLY, both wider-SL,
  same mechanism. Architecturally cleaner than iter-v3/039.
- Section 11 pre-commits NEGATIVE-stacking-suspect catalog row if bundle OOS Sharpe Δ < -0.20.
  The pre-commit prevents post-hoc rationalization if stacking risk materializes.

PASS — stacking risk explicitly modeled; falsifier pre-registered.

## Gate Decision

All 11 sections (10 mandatory + Section 11 pre-commit) PRESENT and PASS. One-variable check
PASS. QR audit trail section PRESENT. Forbidden-direction check PASS. Stacking discipline
check PASS. OVERALL=PASS. Phase 6 may proceed after setup commit lands.
