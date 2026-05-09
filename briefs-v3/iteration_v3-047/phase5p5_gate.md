# Phase 5.5 Gate — iter-v3/047 (REVERT iter-v3/046 BCH ATR + QR-driven BCH LONG signal filter / primitive 10)

OVERALL: PASS

## Brief and Setup Commit Lineage

- Pre-commit REVERT SHA `f5f0fd6` — REVERT iter-v3/046 BCH ATR per Critic FINAL
  `5dae6d6` recommendation. V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] removed; state =
  iter-v3/045 config.
- QR EDA SHA `695fc8e` — `analysis/iteration_v3-047/bch_direction_diagnosis.py` +
  outputs (`bch_diagnosis.csv`, `synthesis.md`, `candidate_axes_ranking.md`).
- Brief SHA `3541997` — research brief (this iteration, single revision; REVERT
  mandated by orchestrator + Critic FINAL).
- Setup commit SHA `9b1293d` — feat(iter-v3/047): primitive 10 (direction-asymmetric
  kill switch) wiring + block_long_for=("BCHUSDT",) dispatch.
- This gate authored against committed brief.

## Per-Section Status

- Section 0 (Data Split): PASS — OOS_CUTOFF_DATE=2025-03-24, training_months=24, IS/OOS
  windows in absolute dates stated (2023-03-24 through 2025-03-23 IS; 2025-03-24+ OOS),
  OOS_CUTOFF_MS=1742774400000 declared. Sacred constants UNCHANGED.
- Section 0.5 (Iteration Type): PASS — TYPE=EXPLORATION, Cycle 3 #8 of 10, wall-clock
  <= 2h, spec `--seeds 1` LightGBM. Two coupled changes (REVERT failed mechanism +
  apply NEW correct mechanism for SAME bottleneck) clearly enumerated:
  (a) PRE-COMMIT REVERT V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] removed — already
      executed at SHA `f5f0fd6`.
  (b) NEW AXIS primitive 10 (direction-asymmetric kill switch) with
      block_long_for=("BCHUSDT",) — to be set at setup commit.
  Predicted classification probabilities (PROMISING 45%, MECHANICAL 20%, INERT 10%,
  NEGATIVE 20%, architecture-bug <5%) with rationale.
- Section 1 (Hypothesis): PASS — ONE sentence. Specific: primitive 10 with
  block_long_for=("BCHUSDT",) suppresses ALL BCH LONG candidate signals, removing the
  known IS+OOS LONG-toxic block. Mechanism named (direction-asymmetric signal filter at
  the wrapper layer). Quantitative expected effect: BCH IS net_pnl +23.62% → ~+48.69%;
  BCH OOS net_pnl +10.75 → ~+15-20; bundle IS Sharpe lift +0.20 to +0.35; bundle OOS
  Sharpe lift +0.05 to +0.20. Falsifier implied by Path C threshold (BCH OOS PnL < 0%).
- Section 2 (IS-Only Evidence): PASS — Numerical tables from committed analysis script
  SHA `695fc8e`:
  - 2.1: Per-symbol IS contribution table @ iter-v3/045 (LDO/BCH/TRX/ALGO).
  - 2.2: BCH direction asymmetry IS+OOS table (LONG/SHORT/TOTAL); BCH LONG IS = -25.07%
    (toxic) reproduces iter-v3/046 EDA finding.
  - 2.3: BCH per-direction exit composition (LONG SL rate 64% vs SHORT 56%; LONG TP 23%
    vs SHORT 36%) — direct evidence the LONG-side fails at higher SL rate + lower TP rate.
  - 2.4: NAIVE bundle counterfactual — blocking BCH LONG lifts bundle weighted_pnl
    +18.68 IS + +4.24 OOS; estimated bundle Sharpe lift +0.18 IS + +0.15 OOS first-order.
  - 2.5: Per-month LONG-vs-SHORT temporal stability — LONG-toxic across 2022-11,
    2023-12, 2024-12 (worst months); persistent across regimes.
  - 2.6: Reproducibility iter-v3/045 (default ATR) vs iter-v3/046 (wider SL) —
    LONG-toxic pattern reproducible; NOT an ATR-config artifact (validates direction-
    asymmetric mechanism over ATR-based mechanism).
  - 2.7: BCH model importance for context (no feature change at iter-v3/047).
  - 2.8: Why NOT per-direction ATR (Candidate 2) — architectural complexity + no EDA support.
  - 2.9: Why NOT BCH LONG threshold tightening (Candidate 3) — Optuna-tunable hyperparameter.
  - 2.10: Why NOT BCH LONG-only feature subset (Candidate 4) — VERY HIGH complexity.
  - 2.11: Predicted behavioral effect (BCH IS trade count -41%; bundle -16%; falsifier
    triggered if BCH-specific < -25% OR > -50%).
  No category-matching. All numbers traceable to `bch_diagnosis.csv` Tables 01-06 or
  `model_importance_last_month_BCHUSDT.csv`.
- Section 3 (Proposed Changes): PASS — 7 sub-fixes enumerated:
  - Sub-fix 1: ADD block_long_for + block_short_for fields to RiskV2Config (default empty).
  - Sub-fix 2: ADD direction_block_fires counter to GateStats.
  - Sub-fix 3: WIRE primitive 10 into RiskV3Wrapper.get_signal AFTER inner inference +
    extend gate_stats_summary.
  - Sub-fix 4: ADD 7 adversarial tests (test_direction_block_primitive_10.py).
  - Sub-fix 5: SET block_long_for=("BCHUSDT",) in v3 runner _build_v3_model.
  - Sub-fix 6: ADD _verify_feature_columns assertion for primitive 10 dispatch.
  - Sub-fix 7: PRE-COMMIT REVERT (already executed at SHA `f5f0fd6`).
  Bundle state verification table present with 21 assertions.
- Section 4 (Expected OOS Impact): PASS — Predicted bands tabulated (IS [+0.85, +1.15]
  median +0.92 to +0.97; OOS [+3.50, +3.85] median +3.60 to +3.70). Rationale derives
  quantitative estimates from sub-section 2.4 NAIVE counterfactual. Pre-registered
  classification paths (PATH A PROMISING / PATH B-MECHANICAL / PATH B-INERT / PATH C
  with sub-types) with locked thresholds.
- Section 5 (Risk Mitigation): PASS — R1/R2/R3 explicitly addressed. IS-calibrated
  thresholds carry forward from iter-v3/045 baseline unchanged. **Primitive 10 dispatch
  risk** explicitly diagnosed (7-test adversarial suite Sub-fix 4 verifies LONG/SHORT/
  no-block/NO_SIGNAL/counter/symmetric/summary). **Cross-symbol contagion risk**
  explicitly enumerated (only fires for BCH; Falsifier 3 catches drift). **Risk-budget
  redistribution risk** explicitly enumerated (BCH LONG block frees risk capacity for
  other symbols; Falsifier 3 catches drift). **IS trade-rate stability** addressed with
  bounded prediction (-41% BCH; -16% bundle). **Adversarial-tests regression risk**
  addressed (all 27 related tests PASS at setup commit).
- Section 6 (Risk Management Design): PASS — 8-primitive table (was 7) with config,
  enabled/disabled status for each gate. **Primitive 10 ADDED with predicted fire
  rate** (~41% of BCH candidate signals based on iter-v3/045 LONG ratio). OOD fire-rate
  prediction bounded (±2% vs iter-v3/045; no feature subspace change).
- Section 7 (Failure-Mode Prediction): PASS — Five forward-looking failure-mode paragraphs:
  (1) PROMISING (clean IS+OOS lift) at 45% probability — most plausible
  (2) NEGATIVE-redistribution (risk-budget freed for cross-symbol toxic trades) at 20%,
  (3) PROMISING-MECHANICAL (bit-identical accounting cleanup) at 20% probability,
  (4) PROMISING-INERT (partial dispatch or breakeven LONGs) at 10% probability,
  (5) NEGATIVE-architecture-bug (primitive 10 dispatch drift) at <5% probability.
  Diagnostic indicators stated. What gates should catch noted.
- Section 8 (MERGE/NO-MERGE Criteria): PASS — Pre-registered EXPLORATION outcome
  classification (PATH A PROMISING / PATH B-MECHANICAL / PATH B-INERT / PATH C with
  sub-types) with numerical thresholds. Locked before backtest with explicit no-post-
  hoc-renegotiation statement. Non-applicable MERGE criteria correctly noted (EXPLORATION spec).
- Section 9 (Library Stack): PASS — All 8 library versions pinned. No new libraries
  introduced. Primitive 10 is config + 5-line code change (no new dispatched features).
- Section 10 (QR Audit Trail): PASS (NEW required section per
  `feedback_v3_axis_selection_quant_discipline.md`) — EDA basis cited
  (analysis/iteration_v3-047/bch_direction_diagnosis.py SHA `695fc8e`), 6-bullet
  rationale for QR EDA findings, 4-candidate ranking summary, orchestrator REVERT
  mandate honored at pre-commit, QR-driven NEW-axis selection rationale, brief
  committed AFTER pre-commit + EDA.
- Section 11 (Catalog-Row Pre-Commit): PASS — 5 outcomes pre-registered (PROMISING-clean,
  PROMISING-MECHANICAL, PROMISING-INERT, NEGATIVE-BCH-deepens, NEGATIVE-architecture-bug,
  NEGATIVE-redistribution).

## One-Variable Check

Single primary variable at iter-v3/047: ADD primitive 10 wiring + set
`block_long_for=("BCHUSDT",)` in the v3 runner's RiskV2Config init. The PRE-COMMIT
REVERT (V3_ATR_MULTIPLIERS_PER_SYMBOL["BCHUSDT"] removed) is a SEPARATE coupled change
that returns the labeling layer to iter-v3/045 state — this is necessary because
iter-v3/046's BCH (2.0, 1.5) was a NEGATIVE result that must be undone before the new
axis is tested cleanly.

Other axes UNCHANGED:
- ALGOUSDT and LDOUSDT per-symbol ATR entries UNCHANGED at (2.0, 1.5) (carried forward
  from iter-v3/044/045).
- DEFAULT_ATR_MULTIPLIERS UNCHANGED at (2.0, 1.0).
- V3_FEATURE_COLUMNS_TOP_N UNCHANGED at 14 features.
- V3_FEATURES_PER_SYMBOL UNCHANGED at empty.
- Risk gate parameters (zscore_threshold, adx_threshold, BTC trend filter, etc.)
  UNCHANGED.
- Library stack UNCHANGED.

The two coupled changes (REVERT iter-v3/046 + apply primitive 10) form a SINGLE
COHERENT axis: addressing BCH's known direction-asymmetric bottleneck after the
mirror-mechanism axis was falsified. State after coupled changes = iter-v3/045
labeling-layer config + iter-v3/047 NEW gate-layer mechanism.

PASS.

## Track Isolation

Not run here (Engineering Phase 6 check). Will be verified in pre-flight. Note:
primitive 10 is in `RiskV2Config` (v2 module) but USAGE is gated through the v3 wrapper
(`RiskV3Wrapper.get_signal`). The default empty `block_long_for=()` preserves v1/v2
behavior on the v2 wrapper. Track isolation grep tests (no v1/v2 imports in
features_v3) UNCHANGED.

## Forbidden-Direction Check

The brief explicitly verifies primitive 10 is NOT a forbidden direction:
- iter-v3/032 forbidden direction was LDO (1.5, 0.75) — TIGHTER ATR barriers,
  multi-seed-FALSIFIED at iter-v3/039.
- iter-v3/046 forbidden direction was BCH (2.0, 1.5) — WIDER ATR barriers, NEGATIVE
  at iter-v3/046 (mirror mechanism doesn't transfer to stable-SL:TP symbols).
- iter-v3/047 NEW axis is a SIGNAL-FILTER layer (downstream of model inference),
  ARCHITECTURALLY DISTINCT from any prior labeling-layer attempt. The mechanism is
  fundamentally different — it does not change BCH's barrier geometry; it suppresses
  candidate signals before they become trades.
- BCH has never had a direction-asymmetric primitive in v3 history. No prior failure
  direction exists for BCH at the signal-filter layer.
- Memory rule `feedback_v3_per_symbol_lifts_oos_breaks_is.md` is HONORED: iter-v3/047
  primitive 10 is NOT a per-symbol feature/labeling customization that re-introduces
  the iter-v3/035 4-ingredient bundle. The mechanism is a SYMBOL-SPECIFIC GATE-LAYER
  customization, architecturally distinct from per-symbol features or per-symbol
  labeling.

PASS — no forbidden direction; mechanism is architecturally novel for v3 and EDA-supported.

## Stacking Discipline Check

This iteration STACKS primitive 10 BCH LONG block on top of:
- ALGOUSDT per-symbol ATR (2.0, 1.5) — iter-v3/044 PROMISING.
- LDOUSDT per-symbol ATR (2.0, 1.5) — iter-v3/045 STRONGEST PROMISING.

Stacking risk:
- ALGO + LDO per-symbol ATR are LABELING-LAYER (barrier geometry).
- iter-v3/047 primitive 10 is SIGNAL-FILTER LAYER (post-inference gate).
- The two layers are ARCHITECTURALLY DISTINCT — they cannot interact via shared state
  (per-symbol ATR sets the trade's exit barriers; primitive 10 decides whether the trade
  fires at all). Stacking via different layers is the cleanest decoupling possible.
- Section 11 pre-commits NEGATIVE-redistribution catalog row if bundle OOS Sharpe Δ
  < -0.20 OR bundle IS Sharpe Δ < -0.10. The pre-commit prevents post-hoc
  rationalization if stacking risk materializes.
- iter-v3/046 multi-seed-stacking risk on the LABELING LAYER (3 per-symbol ATR
  customizations) was the WRONG path. iter-v3/047 stacks on a DIFFERENT LAYER —
  fundamentally different stacking topology.

PASS — stacking risk explicitly modeled; layer-decoupling reduces risk vs iter-v3/046
labeling-layer stack; falsifier pre-registered.

## Adversarial-Tests Status

7 primitive 10 adversarial tests in `tests/strategies/ml/test_direction_block_primitive_10.py`:
1. test_primitive_10_block_long_for_bch — PASS
2. test_primitive_10_other_symbol_not_blocked — PASS
3. test_primitive_10_default_no_block — PASS
4. test_primitive_10_no_signal_passes_through — PASS
5. test_primitive_10_counter_increments — PASS
6. test_primitive_10_block_short_for_symmetry — PASS
7. test_primitive_10_summary_field_present — PASS

5 ATR-multipliers tests in `tests/features_v3/test_atr_multipliers_for_symbol.py`
(reverted state — iter-v3/047):
1. test_atr_multipliers_default — PASS
2. test_atr_multipliers_bch_default_fallback — PASS (REVERTED — was *_widened at iter-v3/046)
3. test_atr_multipliers_trx_default_fallback — PASS
4. test_v3_atr_multipliers_per_symbol_has_algo_and_ldo — PASS (REVERTED — was *_algo_ldo_bch)
5. test_atr_multipliers_runner_dispatch — PASS

7 regime-gate (primitive 9) regression tests in `tests/strategies/ml/test_regime_gate.py`:
ALL PASS (no regression in primitive 9 from primitive 10 addition).

8 per-symbol-cap (primitive 8) regression tests in `tests/strategies/ml/test_per_symbol_cap.py`:
ALL PASS (no regression in primitive 8 from primitive 10 addition).

Total adversarial tests passing: 27/27 (7 primitive 10 + 5 ATR + 7 regime gate + 8 per-symbol cap).

PASS.

## REVERT Honoring Check

The orchestrator's REVERT mandate (from Critic FINAL `5dae6d6` of iter-v3/046 +
orchestrator dispatch) was executed at the PRE-COMMIT (SHA `f5f0fd6`):
- BCHUSDT entry REMOVED from V3_ATR_MULTIPLIERS_PER_SYMBOL.
- run_baseline_v3.py _verify_feature_columns updated to assert 2 entries (ALGO + LDO),
  BCH NOT in dict, BCH falls back to (2.0, 1.0) DEFAULT.
- ITERATION_LABEL = "v3-047".
- 5 adversarial pytest tests in test_atr_multipliers_for_symbol.py rewritten for
  iter-v3/047 expectations (BCH default fallback; 2 per-symbol entries) — all PASS.

The pre-commit landed BEFORE the QR EDA + brief, satisfying the orchestrator's
constraint that REVERT is mandatory and non-negotiable. The Critic FINAL `5dae6d6`
recommendation ("REVERT BCH ATR + dispatch QR for BCH direction-asymmetric axis") was
honored EXACTLY.

PASS.

## Gate Decision

All 11 sections (10 mandatory + Section 11 pre-commit) PRESENT and PASS. One-variable
check PASS. QR audit trail section PRESENT. Forbidden-direction check PASS. Stacking
discipline check PASS. Adversarial-tests status 27/27 PASS. REVERT honoring check PASS.
OVERALL=PASS. Phase 6 may proceed after setup commit lands.
