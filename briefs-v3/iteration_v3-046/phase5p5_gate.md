# Phase 5.5 Gate — iter-v3/046 (QR EDA-driven per-symbol ATR widening for BCH)

OVERALL: PASS

## Brief and Setup Commit Lineage

- QR EDA SHA `d86b1f9` — `analysis/iteration_v3-046/bch_trx_bottleneck_diagnosis.py` + outputs
  (`bch_trx_diagnosis.csv`, `synthesis.md`, `candidate_axes_ranking.md`).
- Brief SHA `6704488` — research brief (this iteration, single revision; no orchestrator-pick
  predecessor per `feedback_v3_axis_selection_quant_discipline.md`).
- Setup commit SHA: TO BE FILLED post-setup-commit (Engineer responsibility).
- This gate authored against committed brief.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS
  windows in absolute dates stated (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS),
  OOS_CUTOFF_MS=1742774400000 declared. Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #7 of 10, wall-clock
  <= 2h, spec `--seeds 1` LightGBM. Single axis clearly enumerated: per-symbol ATR widening
  for BCHUSDT only (V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] = (2.0, 1.5); ALGOUSDT and
  LDOUSDT entries UNCHANGED at (2.0, 1.5) from iter-v3/044+045). Net feature count 14 stated.
  Predicted classification probabilities (PROMISING 45%, INERT 25%, MECHANICAL 15%,
  NEGATIVE 15%) with rationale.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: widening BCHUSDT's SL multiplier
  from 1.0×ATR to 1.5×ATR (TP unchanged) reduces BCH's high IS+OOS SL rate (IS 59.6% / OOS
  60.5%; SL:TP 1.93 stable across both windows) by giving trades 50% more drawdown headroom.
  Mechanism named (per-symbol mechanical adjustment, mirrors iter-v3/044 PROMISING ALGO ATR
  + iter-v3/045 STRONGEST PROMISING LDO ATR mechanisms — third application).
  Falsifier implied by Path C threshold (BCH OOS PnL < 0%).
- Section 2 (IS-Only Evidence): PASS — Numerical tables from committed analysis script
  SHA `d86b1f9`:
  - 2.1: Per-symbol IS contribution table @ iter-v3/045 (LDO/BCH/TRX/ALGO).
  - 2.2: BCH direction asymmetry IS+OOS table (LONG/SHORT/TOTAL); BCH LONG IS = -25.07% (toxic).
  - 2.3: BCH exit-composition stability table (no IS→OOS regime shift; SL:TP 1.93 stable).
  - 2.4: Distinction from iter-v3/039 IS-divergence pattern (BCH is structurally different).
  - 2.5: Counterfactual BCH IS lift estimate (+0.10 to +0.18 IS Sharpe; +0.20 to +0.25 if
    aggressive lift like ALGO at iter-v3/044).
  - 2.6: Counterfactual BCH OOS lift estimate (+0.05 to +0.15 OOS Sharpe).
  - 2.7: Why NOT TRX per-symbol ATR (TRX OOS SL:TP=0.96 already < IS — would HURT OOS).
  - 2.8: Why NOT BCH/TRX direction filter (architectural novelty — high-risk in EXPLORATION).
  - 2.9: Why ALGO ATR REVERT was REJECTED (FALSIFIED initial hypothesis: ALGO ATR (2.0, 1.5)
    IMPROVED ALGO IS by +23.61pp vs iter-v3/043 default).
  - 2.10: BCH per-symbol importance distribution (regime+volatility+mean-reversion top-3).
  - 2.11: Predicted behavioral effect (BCH IS trade count -10% to +5%; portfolio ±2%).
  No category-matching. All numbers traceable to `bch_trx_diagnosis.csv` or trades.csv.
- Section 3 (Proposed Changes): PASS — 6 sub-fixes enumerated:
  - Sub-fix 1: ADD V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] = (2.0, 1.5).
  - Sub-fix 2: Update _verify_feature_columns assertions (specific assertions enumerated).
  - Sub-fix 3: Update tests/features_v3/test_atr_multipliers_for_symbol.py (5 tests).
  - Sub-fix 4: Update V3_ATR_MULTIPLIERS_PER_SYMBOL docstring with iter-v3/046 entry.
  - Sub-fix 5: Update ITERATION_LABEL = "v3-046".
  - Sub-fix 6: Update _verify_feature_columns docstring iter-v3/045 → iter-v3/046.
  Bundle state verification table present with 19 assertions.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS [+0.80, +1.00]
  median +0.85 to +0.90; OOS [+3.50, +3.85] median +3.55 to +3.70). Rationale derives
  quantitative estimates from sub-section 2.5/2.6 counterfactuals (6-9 SL→TP redirections
  × +11pp PnL swing per trade on IS; +5-14pp on OOS). Pre-registered classification paths
  (PATH A PROMISING / PATH B-INERT / PATH B-MECHANICAL / PATH C NEGATIVE) with locked
  thresholds.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. IS-calibrated
  thresholds carry forward from iter-v3/045 baseline unchanged. BCH ATR widening risk
  explicitly diagnosed (wider SL = larger losing trade extremes; falsifier predicates
  trigger Pathway-C). **3-symbol stacking risk** (ALGO + LDO + BCH per-symbol ATR)
  explicitly enumerated with iter-v3/039 multi-seed precedent reference. Distinguishes BCH
  symmetric mechanism from LDO asymmetric mechanism. IS trade-rate stability addressed with
  bounded prediction (±20% BCH, ±2% portfolio). Cross-symbol contagion bounded (<3%
  portfolio-level effect).
- Section 6 (Risk Management Design): PASS — 7-primitive table with config, enabled/disabled
  status for each gate. OOD fire-rate prediction bounded (±2% vs iter-v3/045; no feature
  subspace change since universal list stays at 14). Regime coverage noted across 4 symbols.
- Section 7 (Failure-Mode Prediction): PASS — Five forward-looking failure-mode paragraphs:
  (1) PROMISING (clean IS+OOS lift) at 45% probability — most plausible
  (2) PROMISING-INERT (modest BCH impact) at 25% probability,
  (3) PROMISING-MECHANICAL (bit-identical BCH trades; Falsifier 1) at 15% probability,
  (4) NEGATIVE-BCH-deepens (wider SL increases loss per trade) at 10% probability,
  (5) NEGATIVE-architecture-bug (LDO/TRX/ALGO drift; Falsifier 2) at <5% probability.
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
  (analysis/iteration_v3-046/bch_trx_bottleneck_diagnosis.py SHA `d86b1f9`), 6-bullet rationale
  for QR EDA findings (incl ALGO REVERT axis falsification finding), 5-candidate ranking
  summary, no-orchestrator-pick statement (per iter-v3/044 onward discipline), QR-driven
  selection rationale, brief committed BEFORE setup commit.
- Section 11 (Catalog-Row Pre-Commit): PASS — 5 outcomes pre-registered (PROMISING-clean,
  PROMISING-INERT, PROMISING-MECHANICAL, NEGATIVE-BCH-deepens, NEGATIVE-architecture-bug,
  NEGATIVE-stacking-suspect).

## One-Variable Check

Single primary variable: ADD `V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] = (2.0, 1.5)`
alongside the existing `ALGOUSDT` (iter-v3/044) and `LDOUSDT` (iter-v3/045) entries. The
ALGOUSDT and LDOUSDT entries are UNCHANGED (no perturbation to iter-v3/044 or iter-v3/045
axes). The DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) is UNCHANGED. V3_FEATURE_COLUMNS_TOP_N is
UNCHANGED at 14. V3_FEATURES_PER_SYMBOL is UNCHANGED at empty. All other aspects of the
bundle (V3_MODELS, REQUIRED_GAP, risk gates, library stack) are bit-identical to iter-v3/045.
PASS.

## Track Isolation

Not run here (Engineering Phase 6 check). Will be verified in pre-flight.

## Forbidden-Direction Check

The brief explicitly verifies it is NOT a forbidden direction:
- iter-v3/032 forbidden direction was LDO (1.5, 0.75) — TIGHTER barriers, multi-seed-FALSIFIED
  at iter-v3/039.
- iter-v3/046 proposes BCH (2.0, 1.5) — WIDER barriers, mirror of iter-v3/044 ALGO + iter-v3/045
  LDO PROMISING patterns.
- BCH has never had a per-symbol ATR customization in v3 history. No prior failure direction
  exists for BCH at the per-symbol-ATR axis.
- Memory rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md` is HONORED: iter-v3/046 is a
  cycle 3 per-symbol-ATR addition AT THE LABELING LAYER ONLY, not in the iter-v3/035 bundle
  rejected at iter-v3/039. The mechanism (wider SL) is symmetric to iter-v3/044 ALGO and
  iter-v3/045 LDO PROMISINGs.

PASS — no forbidden direction; mechanism mirrors 2 prior PROMISING precedents.

## Stacking Discipline Check

This is the THIRD per-symbol ATR customization (after iter-v3/044 ALGO + iter-v3/045 LDO).
The brief Section 5 explicitly addresses stacking risk:
- iter-v3/039 multi-seed broke IS with feature+label stacking (BCH-fracdiff + LDO-(1.5,0.75)).
- iter-v3/045 (2 per-symbol ATR customizations) did NOT replicate iter-v3/039 IS-divergence
  pattern at single-seed (iter-v3/045 IS Sharpe +0.7459 was the highest single-seed in v3).
- iter-v3/046 stacks 3 per-symbol ATR customizations — all LABEL-LAYER ONLY, all wider-SL,
  same mechanism. Architecturally homogeneous (vs iter-v3/039's mixed feature+label stack).
- BCH IS=OOS SL:TP=1.93 stable means BCH's wider-SL helps IS AND OOS symmetrically (vs LDO's
  asymmetric IS-strong/OOS-strong pattern). This REDUCES the IS-divergence risk for BCH
  specifically.
- Section 11 pre-commits NEGATIVE-stacking-suspect catalog row if bundle OOS Sharpe Δ < -0.20
  OR bundle IS Sharpe Δ < -0.10. The pre-commit prevents post-hoc rationalization if
  stacking risk materializes.

PASS — stacking risk explicitly modeled; mechanism homogeneity reduces risk vs iter-v3/039;
falsifier pre-registered.

## ALGO REVERT Falsification Check

The brief Section 2.9 documents that the QR EDA falsified the initial hypothesis that ALGO
ATR (2.0, 1.5) might have hurt ALGO IS:
- ALGO IS @ iter-v3/043 (default ATR (2.0, 1.0)): -57.66% net_pnl, 28.1% WR
- ALGO IS @ iter-v3/045 (per-symbol ATR (2.0, 1.5)): -34.05% net_pnl, 39.6% WR
- Δ IS net_pnl: +23.61pp (IMPROVED, not regressed)
- ALGO ATR REVERT axis REJECTED — would hurt BOTH IS (-23pp) and OOS (-49 swing)

The QR's willingness to falsify own initial hypothesis through EDA is the methodological
hallmark of `feedback_v3_axis_selection_quant_discipline.md`. PASS.

## Gate Decision

All 11 sections (10 mandatory + Section 11 pre-commit) PRESENT and PASS. One-variable check
PASS. QR audit trail section PRESENT. Forbidden-direction check PASS. Stacking discipline
check PASS. ALGO REVERT falsification PASS. OVERALL=PASS. Phase 6 may proceed after setup
commit lands.
