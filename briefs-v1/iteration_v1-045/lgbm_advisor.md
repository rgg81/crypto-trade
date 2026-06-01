# LightGBM Master Advisor — iter-v1/045 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1
- Baseline: BASELINE_V1 (iter-v1/186 anchor, 9-symbol full stack with R1/R2/R3 brakes)
- /045 architecture: 3-component symbol-partitioned federation under Rule 7 — C1={BTC,ETH}, C2={LTC}, C3={LINK,DOT}, equal 1/3 weights
- Prior /044 closeout: aggregator's active-weight renormalization confirms single-active components → weight × 1.0 under symbol-partitioning

## Symbol-Partitioning Validity (ML Perspective)

Each component's LightGBM trains on its OWN universe walk-forward — C1 pools BTC+ETH (joint training, ~2× row count, cross-symbol regularization), C2 trains LTC-alone (single-cohort, narrower regime coverage), C3 pools LINK+DOT (joint, /044-multi-seed-validated). **Zero cross-component data leakage** by construction: disjoint symbol universes mean disjoint training matrices. Each component's `_train_for_month` is independent. This is structurally clean — no aggregation-induced overfitting risk that an Optuna joint-search would create.

## Top 3 Recommendations

### 1. Lock per-component Optuna budget at /044 sub-run levels — DO NOT re-tune
Each component's HP region was found via independent walk-forward at /044 (C1 from baseline sub-run, C3 from /036 multi-seed). Re-running Optuna at /045 with the federated objective WOULD be a leakage path (joint loss surface ≠ symbol-partitioned ground truth). **Recommendation**: each component re-uses its /044 best-trial HPs verbatim per `(symbol, month)` cell. /045 is a wiring iteration, not a search iteration. **Confidence: HIGH**.

### 2. Watch C2 (LTC-only) trade-count floor at multi-seed
LTC-alone training has 1/2 the rows of C1/C3 joint pools and historically a narrower trade-rate at the BASELINE_V1 risk-gate threshold. Multi-seed mean OOS trade count for C2 must clear ≥10/month or the 1/3 weight bleeds dead capital. Flag for QE: log per-component `oos_trades/month` separately in `comparison.csv`. If C2 < 10/month OOS, equal-weight is structurally wrong — consider falsifier F1 carve-out for C2-light regimes. **Confidence: MEDIUM**.

### 3. Verify F4 trade-roster Jaccard = 1.0 at engineering report
Under true symbol-partitioning, the bundle's trade roster is EXACTLY the union of component rosters (no overlap by symbol-disjointness). If Jaccard < 1.0, there's a wiring bug — either a component is firing on the wrong symbol, or the aggregator is double-counting. This is the cheapest sanity check in the iteration. **Confidence: HIGH** that the test fires correctly; the question is whether wiring is correct.

## Feature Importance Risk Flags

- **C1 (BTC+ETH joint)**: BTC and ETH have correlated feature distributions (especially funding_z, basis_z). Joint training may produce a model where BTC features rank 1-3 and ETH features rank 8-14 — effectively a BTC-dominant model that uses ETH as a noisy second cohort. Engineering report should split feature importance by training symbol within the joint pool — if ETH importance is rank-14/14 conditional on BTC, C1 is structurally a BTC-only model and weight 1/3 is over-allocated.

- **C3 (LINK+DOT joint)**: /036 was the original sub-run; /044 multi-seed validation should already have surfaced the per-symbol importance balance. Re-confirm at /045 that LINK and DOT are both pulling weight (neither rank-14/14).

- **C2 (LTC alone)**: single-cohort training means feature importance is unambiguous. Watch for `min_data_in_leaf` saturation — if LTC's training matrix is small enough that Optuna's `min_data_in_leaf ∈ [20, 500]` upper bound is binding, the model is regularizing into a near-constant prediction.

## Saturation Risks to Flag

The biggest risk is NOT modeling — it's **C2's LTC-only narrow regime coverage**. LTC has historically been chop-heavy in stretches of 2023-2024 (per project diary). If OOS lands in an LTC chop regime, C2 contributes ~zero PnL but absorbs 1/3 of capital. Equal weights are IS-only justified per substrate proposal, but the IS justification assumes LTC's OOS regime distribution matches IS — which is a strong assumption for single-symbol cohorts. Pareto-by-regime evaluation (F1) is the right mitigation; ensure regime_catalog.md regimes are represented in OOS.

Second risk: **C1 giving up per-symbol R1 brakes**. BASELINE_V1 runs R1 per-symbol (consecutive-SL streak cooldown). Under /045, if C1's R1 is applied at the pool level rather than per-symbol, BTC and ETH share a brake — meaning a BTC SL-streak would also halt ETH. Verify per-component risk gates preserve symbol-granular R1 if that's the BASELINE_V1 behavior.

## What I Did NOT Recommend, and Why

- **Do NOT re-tune Optuna jointly at /045**: would re-introduce the leakage federation is designed to avoid (see Rec 1).
- **Do NOT propose new features for /045**: this is a wiring iteration; feature axes should land at /046+ once /045 establishes the federation works.
- **Do NOT IS-tune weights away from 1/3**: equal-weight is the cleanest null hypothesis for the federation; deviating before /045 confirms the wiring is IS-overfit.

## Prior Distribution (per substrate proposal §6)

- UNIVERSAL: 5%
- REGIME-SPECIALIST-IS: 25%
- REGIME-SPECIALIST-OOS: 15%
- TAIL-CONTROL: 10%
- **EXPLORATION-PROMISING: 30% (MODAL)** — federation Pareto-better-or-equal on most regimes, not strictly dominant
- TRUE-NEG: 10%
- LEARNED-NEG: 5%

The 30% PROMISING modal reflects the architectural cleanness of symbol-partitioning (no leakage path) combined with the constraint that /045 is a wiring iteration, not an edge-discovery iteration. Tail risk concentrated in LTC-only C2 if OOS lands in chop.

## Closing Note

**Confidence: MEDIUM**. Substrate is viable — symbol-partitioning is structurally sound and the equal-weight rationale under active-weight renormalization is mathematically correct. The iteration's success hinges on (a) C2's multi-seed trade-count clearing the floor and (b) F4 Jaccard=1.0 verifying clean wiring. If both hold, EXPLORATION-PROMISING is the right expectation. If C2 collapses on OOS regime mismatch, the iteration is salvageable by re-running with C2 weight reduced — but that's an IS→OOS tune that the next QR should avoid.

**Single most important thing the QR should NOT ignore**: F4 trade-roster Jaccard verification at the engineering report. It's the cheapest validity proof and the most informative if it fails.
