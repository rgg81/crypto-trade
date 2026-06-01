# Phase 7.5 Critic Review — iter-v1/045

OVERALL: BLOCK-FINAL — substrate-selection prudence (NOT a Check 15/16/17 failure; wiring PASS by construction)

## Iteration Type (from Brief Section 0.5)
TYPE: CONFIRMATION-MERGE-PORTFOLIO (second attempt; first wiring-PASS bundle under bundle-discipline Rules 7/8/9 + Critic Checks 15/16/17)

## Round
Round 1 (single-round Critic review — no BLOCK-PENDING-FIX path; BLOCK is on substrate-validation prudence, not a code defect)

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS
CSV-replay aggregator operates on frozen component trade CSVs (pre-computed; no Optuna re-fit, no LightGBM re-training). `run_iteration_045.py` sorts by open_time and multiplies each row's PnL by 0.2 weight constant — deterministic concat with no forward-bar references. Each component CSV was produced by its source iteration runner under standard `walk_forward.py:113` embargo (`train_end_ms = test_start_ms - embargo_ms`). Foundation regression suite present. No look-ahead path.

### Check 2 — Embargo Width: PASS
Aggregator does not re-fit; inherits embargo from each component's source iteration. Each component (v1-012, v1-042, v1-011, v1-040, v1-031) used the standard `(timeout_candles + 1) × n_symbols` purge requirement. Brief Section 2 documents source iteration configs; all predate the lookahead-bug fix but are evaluated at single-seed=42 (not re-fit here). No new embargo computation at bundle level.

### Check 3a — DSR/PSR per-regime + bundle: INFORMATIONAL
Bundle `reports-v1/iteration_v1-045/comparison.csv` includes standard headline metrics. DSR/PBO/PSR at bundle level are not required for CONFIRMATION-MERGE-PORTFOLIO under CSV-replay aggregator (no Optuna trial population). Informational.

### Check 3b — PBO bundle-level: INFORMATIONAL
Same as 3a. Not a BLOCK at this iteration type.

### Check 3c — Regime Attribution Clarity: PASS (internal consistency ±0.03)
`reports-v1/iteration_v1-045/regime_attribution.csv` shows IS trade-weighted regime Sharpe = 0.373 vs comparison.csv monthly Sharpe 0.387 (Δ +0.014 ≤ 0.03); OOS = 0.461 vs 0.432 (Δ +0.029 ≤ 0.03). Internal consistency PASS.

Regime-coverage caveat (load-bearing for the BLOCK): 196/199 (98.5%) of OOS trades land in regime tag "other". OOS bear/chop/recovery/vol-spike have ZERO bundle trades. F-AXIS #1's per-regime Pareto-dominance has limited discriminative power on the OOS window. This is a CONCERN, not a BLOCK trigger.

### Check 3d — Bundle-level per-regime Pareto-dominance: PASS (informational; BLOCK fires pre-Pareto on prudence)
Bundle IS Sharpe +1.9879 vs baseline +0.4761: IS regimes 5/5 Pareto-better (bull +0.99 / bear +0.13 / chop +0.15 / recovery +0.12 / other 0). Bundle OOS Sharpe +3.4851 vs baseline +1.1415: OOS "other" Pareto-dominates (+0.47 vs baseline +0.14). Per-coin 5/5 Pareto-dominate on ≥1 window; 3/5 on both. F-AXIS #1 would PASS at single-seed. The BLOCK fires BEFORE this — pre-Pareto on substrate-selection prudence — making this informational.

### Check 4 — Feature IC Matrix: N/A
CSV-replay aggregator — no feature engineering at bundle level. Each component uses its source iteration feature columns; no new feature additions at /045.

### Check 5 — ADF Stationarity: N/A
Same as Check 4.

### Check 6 — Multi-Seed Pareto (seed concentration audit): BLOCK-RELEVANT (primary block reason #1)
All 5 components (v1-012, v1-042, v1-011, v1-040, v1-031) were sourced from their respective source iterations at SINGLE-SEED=42. No multi-seed validation exists for any component at the point of /045 bundle assembly. Per `feedback_seed_validation.md` and `feedback_seed_parity_on_model_change.md`: **no MERGE without multi-seed validation**. C-BTC (v1-012) has only 19 OOS trades (σ_SR ≈ √(1/19) ≈ 0.23); the observed OOS Sharpe +6.10 is consistent with a genuine specialist OR a single-seed basin lottery. The 5× single-seed=42 inheritance compounds federation-level lottery exposure — each component independently rolled seed=42 during its source Optuna search. **This is the primary prudence BLOCK reason.**

### Check 7 — Reproducibility: PASS
`reports-v1/iteration_v1-045/source_checksums.csv` emitted with 10 SHA-256s (5 components × 2 windows: IS + OOS). Aggregator `run_iteration_045.py` verified deterministic at commit `addb4e4`: given the same 10 input CSVs, output metrics are bit-reproducible. Component substitution analysis (LOO) confirms expected LOO deltas: C-LINK drop LOO Δ −0.58 (largest), C-BTC drop LOO Δ −0.30, C-LTC drop LOO Δ +0.14 (mild positive), C-ETH drop LOO Δ −0.11, C-DOT drop LOO Δ −0.22. LOO behavior is mathematically consistent — bundle is NOT a baseline-collapse artifact (contrast with /044). PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS
Brief Section 11.A declares symbol-partitioned federation; brief Section 11.C describes pure dispatch lookup `OWNING_COMPONENT[symbol]` with no aggregation, no netting. Runner implementation: concat 5 component CSVs, multiply each row's PnL by 0.2, sort by open_time. This is EXACTLY the pure-dispatch-at-unit-weight with 1/5 dilution described. Aggregator does NOT hold simultaneous positions in the same symbol (each symbol owned by exactly one component). Hypothesis-implementation match. PASS.

### Check 14 — Axis Family Validation: PASS
Brief Section 0.5 declares `CONFIRMATION-MERGE-PORTFOLIO`. Brief Section 0.6 correctly declares Axis Rotation Discipline EXEMPT for CONFIRMATION-PORTFOLIO type. Per skill §"Phase Quick Reference": CONFIRMATION-PORTFOLIO bundles existing per-coin specialists; axis family rotation discipline does not apply. PASS.

### Check 15 — Backtest-Live Parity: PASS (by construction)
5-component symbol-partitioned federation with pairwise disjoint universes — each symbol owned by EXACTLY ONE component. At `live/engine.py:_tick`, `OWNING_COMPONENT[symbol]` lookup dispatches to the single owning component; no simultaneous multi-component positions in the same symbol arise. Active-weight renormalization at subset-silent cells degenerates to 1.0 × single_component_pnl — mathematically identical to pure dispatch with no aggregation. The parity-violation that BLOCKed /044 (proportional renormalization requiring multi-component simultaneous LINK positions) CANNOT arise here because LINK is exclusively owned by C-LINK (v1-011). **Rule 8 SATISFIED by construction.** PASS.

### Check 16 — Universe Disjointness (Rule 7): PASS (by construction)
10 pairwise universe intersections verified:
- C-BTC {BTC} ∩ C-ETH {ETH} = ∅
- C-BTC {BTC} ∩ C-LINK {LINK} = ∅
- C-BTC {BTC} ∩ C-LTC {LTC} = ∅
- C-BTC {BTC} ∩ C-DOT {DOT} = ∅
- C-ETH {ETH} ∩ C-LINK {LINK} = ∅
- C-ETH {ETH} ∩ C-LTC {LTC} = ∅
- C-ETH {ETH} ∩ C-DOT {DOT} = ∅
- C-LINK {LINK} ∩ C-LTC {LTC} = ∅
- C-LINK {LINK} ∩ C-DOT {DOT} = ∅
- C-LTC {LTC} ∩ C-DOT {DOT} = ∅

Bundle trade-roster Jaccard = 1.0 vs union of post-filter component rosters (per engineering report). Bundle universe = BASELINE_V1 universe exactly {BTC, ETH, LINK, LTC, DOT}. **Rule 7 SATISFIED by construction.** PASS.

### Check 17 — Bundle Weight IS-Only Provenance: PASS
`bundle_weights.csv` contains literal constants 0.2 (equal 1/5 weights) for all 5 components. `analysis/iteration_v1-045/weight_calibration.py` committed to git; greps clean for any OOS data references. Brief Section 11.B specifies the CSV verbatim; byte-match confirmed by engineering report. **Rule 9 SATISFIED.** PASS.

## Per-Regime Pareto-Dominance Summary (Informational — BLOCK fires pre-Pareto)

| Regime | Baseline IS Sharpe | Bundle IS Sharpe | Δ IS | Baseline OOS Sharpe | Bundle OOS Sharpe | Δ OOS | Status |
|---|---:|---:|---:|---:|---:|---:|---|
| bull | −0.35 | +0.6442 | +0.99 | −0.47 | 0.0 (4 trades) | +0.47 | Pareto-better IS; OOS sparse |
| bear | +0.14 | +0.2714 | +0.13 | — | 0.0 (0 trades) | — | IS Pareto-better; OOS absent |
| chop | +0.24 | +0.3861 | +0.15 | — | 0.0 (0 trades) | — | IS Pareto-better; OOS absent |
| recovery | +0.28 | +0.4019 | +0.12 | — | 0.0 (0 trades) | — | IS Pareto-better; OOS absent |
| other | — | 0.0 (0 IS trades) | — | +0.14 | +0.4700 | +0.33 | OOS Pareto-better |

5/5 IS regimes Pareto-better; OOS "other" Pareto-dominate. OOS regime caveat: 98.5% of OOS trades in "other" — regime classifier power low for OOS F-AXIS #1 discrimination.

## Component Substitution (LOO) Summary

| Dropped component | Δ Bundle IS daily Sharpe | Δ Bundle OOS daily Sharpe |
|---|---:|---:|
| C-BTC (v1-012) | — | −0.30 (bundle OOS ≈ +1.73 without BTC) |
| C-ETH (v1-042) | — | −0.11 (bundle OOS ≈ +1.91 without ETH) |
| C-LINK (v1-011) | — | −0.58 (bundle OOS ≈ +1.44 — largest sensitivity) |
| C-LTC (v1-040) | — | +0.14 (C-LTC mild drag on OOS; LTC IS-dominant) |
| C-DOT (v1-031) | — | −0.22 (bundle OOS ≈ +1.80 without DOT) |

LOO behavior consistent with genuine multi-component composition (contrast with /044 where ALL LOO Δ = 0.0, proving aggregator collapse to baseline). /045 bundle IS a genuine composition; the BLOCK is NOT about null-mechanism — it is about single-seed=42 substrate-validation prudence.

## Primary BLOCK Reasons

### Reason 1: 5× single-seed=42 inheritance (BLOCK — prudence)
Each component (v1-012 / v1-042 / v1-011 / v1-040 / v1-031) was sourced from a source iteration run at single-seed=42. The bundle headline +3.49 OOS inherits 5 independent seed-lottery exposures — one per component. Per `feedback_seed_validation.md`: MERGE requires multi-seed validation with mean Sharpe > 0 AND ≥7/10 profitable seeds. That standard has not been met for ANY of the 5 components at the specific (iteration, config, hyperparameter-region) used here. C-BTC (v1-012) is the most exposed: 19 OOS trades, σ_SR ≈ 0.23, observed Sharpe +6.10 — consistent with either a genuine specialist or a single-seed basin lottery that dissolves at other seeds.

### Reason 2: Workflow w0qpo136q OOS-aware specialist selection (BLOCK — prudence)
The partition-solve workflow `w0qpo136q` that produced ALT_1 (this substrate) READ each candidate component's OOS Sharpe during the optimization (per QR brief Section 2 acknowledgment). This constitutes **post-hoc OOS-aware specialist selection**: the partition solve maximized per-coin OOS Sharpe subject to disjointness constraints. The resulting bundle headline +3.49 OOS is structurally inflated because the selection process OPTIMIZED for OOS outcome. Expected discount at honest multi-seed re-evaluation: 30-50%. Expected honest multi-seed mean OOS Δ: +1.2 to +1.6 (still strong, but not the +2.34 the catalog would record if MERGEd as-is).

### Reason 3: C-BTC 19-trade σ_SR fragility (BLOCK — prudence)
C-BTC (v1-012) contributes 21% of OOS PnL from 19 OOS trades. σ_SR ≈ √(1/19) ≈ 0.23 — an extremely wide credible interval. The basin lottery hypothesis cannot be rejected from this evidence alone. ALT_2 (BTC=v1-023, 58 OOS trades, σ_SR ≈ 0.13, OOS Sharpe +2.87) is pre-registered as a fallback if /046 multi-seed reveals v1-012's 5-seed mean OOS Sharpe < +2.0.

## What Passes

- **Checks 15/16/17** (bundle-discipline wiring checks): ALL PASS by construction.
- **Jaccard = 1.0** vs union of post-filter component rosters.
- **Source checksums**: 10 SHA-256s committed in `source_checksums.csv`.
- **Deterministic CSV-replay**: aggregator is bit-reproducible.
- **Hypothesis-implementation alignment**: federation dispatch = pure lookup, no netting.
- **Trade-rate floor**: 199 OOS trades > 130 floor.
- **IS Sharpe floor**: bundle IS +1.99 > 1.0 floor.
- **OOS Sharpe floor**: bundle OOS +3.49 > 1.0 floor.
- **IS-only weight provenance**: `weight_calibration.py` IS-clean.

## No BLOCK-PENDING-FIX Path

The BLOCK is on substrate-validation prudence — 5× single-seed=42 inheritance + OOS-aware specialist selection bias. These are NOT code defects fixable by a code patch. The BLOCK cannot be resolved by a BLOCK-PENDING-FIX round of /045. The fix is the /046 multi-seed re-run of each component at 5-10 seeds. /045 closes as a historical artifact: the first wiring-PASS CONFIRMATION-MERGE-PORTFOLIO in v1 history.

## Path Forward

1. **/046 = MULTI-SEED RE-VALIDATION of /045 ALT_1 substrate (MANDATORY).** Re-run each of 5 components (v1-012, v1-042, v1-011, v1-040, v1-031) at 5-10 seeds under their source-iteration configs; re-aggregate via /045's CSV-replay aggregator. Pass gates: bundle 5-seed mean OOS Sharpe > +1.0 AND ≥7/10 profitable seeds per component AND Pareto-better-or-equal vs BASELINE_V1 on every tagged regime within σ_R. If PASS → BASELINE_V1.md UPDATED at /046 closeout to the 5-component federation.

2. **/047 (conditional on /046 BTC failure)** = ALT_2 sensitivity probe (BTC=v1-023 swap). Fires if /046 reveals BTC=v1-012's 5-seed mean OOS Sharpe < +2.0. Pre-registered: IS +2.23 / OOS +2.87 (from workflow `w0qpo136q` ALT_2 row).

3. **/048+ = NEW feature family** post-multi-seed-baseline. Axis Rotation Discipline requires departing from cycle-5's exhausted feature-family and labeling axes. Candidates: (a) on-chain feature family (LM Master Rec #7 modal), (b) microstructure order-flow, (c) cross-asset macro-regime.

## BASELINE_V1.md Disposition

UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`). Tag `v0.v1-045` is a historical artifact (BLOCK-FINAL on prudence; wiring PASS; MERGE deferred to /046).
