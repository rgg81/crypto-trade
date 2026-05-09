# Phase 5.5 Gate — iter-v3/044 (REWRITTEN per QR EDA discipline)

OVERALL: PASS

## Brief and Setup Commit Lineage

- Original brief SHA `2cd41fc` — orchestrator's ad-hoc 3d variant (SUPERSEDED).
- Original setup commit SHA `1f56c72` — implemented 3d variant (REVERTED at SHA `7f3be39`).
- Original Phase 5.5 gate SHA `39c8099` (SUPERSEDED by this gate).
- QR EDA SHA `eff841e` — `analysis/iteration_v3-044/cycle3_is_diagnosis.py` + outputs.
- Rewritten brief SHA `9f8797f` — QR EDA-driven axis (per-symbol ATR for ALGO).
- Rewritten setup commit SHA `7f3be39` — REVERT 3d universal + ADD per-symbol ATR for ALGO.
- This gate (rewritten): authored against rewritten brief.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS windows in absolute dates stated (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS), OOS_CUTOFF_MS=1742774400000 declared. Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #5 of 10, wall-clock <= 2h, spec `--seeds 1` LightGBM. Single axis clearly enumerated: per-symbol ATR widening for ALGOUSDT only (V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5)). Net feature count 14 stated. Predicted classification probabilities (PROMISING 40%, INERT 35%, NEGATIVE 25%) with rationale.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: widening ALGOUSDT's SL multiplier from 1.0×ATR to 1.5×ATR (TP unchanged) reduces SL hit rate on ALGO long trades — single largest IS attribution loss bucket — by giving bear-trend longs more breathing room without changing entry signal. Mechanism named (per-symbol mechanical adjustment, mirrors iter-v3/032 LDO ATR success). Falsifier implied by Path C threshold (IS < +0.65 OR OOS < +1.40).
- Section 2 (IS-Only Evidence): PASS — Numerical tables from committed analysis script SHA `eff841e`:
  - 2.1: Direction-asymmetric per-symbol IS bottleneck table (8 symbol×direction buckets ranked).
  - 2.2: ALGO LONG SL/TP exit asymmetry (27/6 = 4.5:1; mean SL -5.24%, TP +18.41%).
  - 2.3: Market context (ALGO -34.62% OOS bear).
  - 2.4: Why NOT regime_momentum_signed_3d (does not discriminate ALGO LONG WR; ranks 14/14 in ALGO model).
  - 2.5: Predicted behavioral effect (5–15% IS trade reduction; specific per-bucket predictions).
  No category-matching. All numbers traceable to `is_constraint_analysis.csv` or trades.csv.
- Section 3 (Proposed Changes): PASS — 6 sub-fixes enumerated:
  - Sub-fix 1: REVERT efficiency_ratio_50 (carried forward from iter-v3/043 disaster).
  - Sub-fix 2: REVERT regime_momentum_signed_3d universal addition (NEW — orchestrator pick superseded).
  - Sub-fix 3: ADD V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5).
  - Sub-fix 4: Update _verify_feature_columns assertions (12 specific assertions enumerated).
  - Sub-fix 5: Update tests (15 test renames/updates; 97 tests pass at SHA `7f3be39`).
  - Sub-fix 6: Update ITERATION_LABEL (already set).
  Bundle state verification table present with 18 assertions.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS [+0.65, +1.05] median +0.85–0.95; OOS [+1.40, +2.10] median +1.75). Rationale derives quantitative estimates from sub-section 2.5 prediction (5–9 SL→TP redirections × +11.36 PnL swing per trade = +25–45 portfolio PnL lift). Three classification paths (PROMISING/PROMISING-INERT/NEGATIVE) with locked thresholds.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. IS-calibrated thresholds carry forward from iter-v3/040 baseline unchanged. ALGO ATR widening risk explicitly diagnosed (wider SL = larger losing trade extremes; falsifier predicates trigger Pathway-C). IS trade-rate stability addressed with bounded prediction (±15% ALGO, ±5% portfolio). Cross-symbol contagion bounded (<5% portfolio-level effect).
- Section 6 (Risk Management Design): PASS — 7-primitive table with config, enabled/disabled status for each gate. OOD fire-rate prediction bounded (±2% vs iter-v3/040; no feature subspace change since universal list stays at 14). Regime coverage noted across 4 symbols.
- Section 7 (Failure-Mode Prediction): PASS — Three forward-looking failure-mode paragraphs: (1) wider SL increases loss per trade without raising WR (most plausible NEGATIVE), (2) PROMISING-INERT via minimal IS impact, (3) cross-symbol drag from R2 brake recalibration. Diagnostic indicators stated. What gates should catch noted.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Pre-registered EXPLORATION outcome classification (PATH A PROMISING / PATH B PROMISING-INERT / PATH C NEGATIVE) with numerical thresholds. Locked before backtest with explicit no-post-hoc-renegotiation statement. Non-applicable MERGE criteria correctly noted (EXPLORATION spec).
- Section 9 (Library Stack): PASS — All 8 library versions pinned. No new libraries introduced. Per-symbol ATR is config-only change (no new feature implementations dispatched). No license risk. No fallbacks needed.
- Section 10 (QR Audit Trail): PASS (NEW required section per `feedback_v3_axis_selection_quant_discipline.md`) — EDA basis cited (analysis/iteration_v3-044/cycle3_is_diagnosis.py SHA `eff841e`), original orchestrator pick disclosed (3d variant), QR-driven replacement disclosed (per-symbol ATR for ALGO), setup commit SHA cited (`7f3be39`), Phase 5.5 verification requirement stated (numerical evidence committed BEFORE setup commit).

## One-Variable Check

Single primary variable: V3_ATR_MULTIPLIERS_PER_SYMBOL["ALGOUSDT"] = (2.0, 1.5).
The efficiency_ratio_50 REVERT is a pre-condition restoration (removing iter-v3/043's
DISASTROUS addition; already applied at code level before any iter-v3/044 work).
The regime_momentum_signed_3d UNIVERSAL ADDITION REVERT is also a pre-condition
restoration (removing the orchestrator's ad-hoc setup commit `1f56c72` that was
SUPERSEDED by QR EDA — same classification as prior reverts of orchestrator picks).
ITERATION_LABEL update is cosmetic. PASS.

## Track Isolation

Not run here (Engineering Phase 6 check). Will be verified in pre-flight.

## Gate Decision

All 10 mandatory sections PRESENT and PASS. One-variable check PASS. QR audit trail
section (NEW required per process-discipline directive) PRESENT. OVERALL=PASS.
Phase 6 may proceed.
