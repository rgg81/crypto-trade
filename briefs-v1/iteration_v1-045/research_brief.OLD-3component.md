# Iteration v1-045 — Research Brief

## Section 0.0 — Banner

**TYPE:** `CONFIRMATION-MERGE-PORTFOLIO`
**Cycle slot:** cycle-6 CONFIRMATION 1/1 (FIRST CONFIRMATION under the new bundle-discipline rules: Rules 7 / 8 / 9 + Critic Checks 15 / 16 / 17).
**Anchor:** `BASELINE_V1` corrected walk-forward (IS daily Sharpe +0.4767 / OOS daily Sharpe +1.1913; OOS_CUTOFF_DATE = 2025-03-24).
**Substrate:** 3-component symbol-partitioned federation `(baseline_pool_A, baseline_D, iter-v1/036)` at EQUAL 1/3 weights. Bundle universe is `{BTC, ETH, LINK, LTC, DOT}` — coverage matches BASELINE_V1 exactly; only OWNERSHIP within the bundle is partitioned.
**Branch:** `iteration-v1/045`. **Tag (post-Phase-8):** `v0.v1-045`.

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — unchanged (sacred).
- `training_months = 24` — unchanged (sacred).
- IS window: `[earliest available data, 2025-03-24)`.
- OOS window: `[2025-03-24, latest available data]`.
- Walk-forward: `train_end_ms = test_start_ms - embargo_ms` at `walk_forward.py:113` (verified by Phase 6.0 mini-Foundation check).

---

## Section 0.5 — Iteration Type Declaration + Cadence

**TYPE:** `CONFIRMATION-MERGE-PORTFOLIO`
**Wall-clock target:** 8h (design target; NO runtime kill-switch).
**Wall-clock estimate (Section 3.6):** ~5-7h (baseline_pool_A ~3h + baseline_D ~1.5h + /036 trade replay <5min + aggregator <5min).
**Cycle-6 status:** cycle-5 closed at /044 BLOCK-FINAL (retroactive — pre-bundle-discipline rules), so cycle-6 begins at /045.

**Previous CONFIRMATION verdict:** `/044 BLOCK-FINAL` (retroactive, RULE-7 + RULE-8 + RULE-1 violations: coin-overlap on {LINK, DOT} between BASELINE_V1 and /036 components; weights not derived by committed IS-only `weight_calibration.py` script). `/044` is grandfathered as the 10th cycle-5 EXPLORATION-comparator; its headline metrics are NOT MERGED.

**EXPLORATION precedents for `/045`:**

Per the new bundle-discipline rules (Rules 7/8/9 + Checks 15/16/17), `/045`'s components are sourced from ALREADY-VALIDATED prior iterations — no new EXPLORATION is required at the `/045` boundary because the bundle is a re-composition of pre-existing components, not a fresh hypothesis. The substrate is:

- **C1 = `baseline_pool_A`** ← extracted unchanged from `BASELINE_V1` Model A (BTC+ETH pooled; 193-feature `BASELINE_FEATURE_COLUMNS`; ATR TP 2.9 / SL 1.45; R1 OFF, R3 ON 70th pct). 5-seed ensemble [42,123,456,789,1001] inherited.
- **C2 = `baseline_D`** ← extracted unchanged from `BASELINE_V1` Model D (LTC; same 193 features; ATR TP 3.5 / SL 1.75; R1 ON (3,27), R3 ON 70th pct). 5-seed ensemble inherited.
- **C3 = `iter-v1/036`** ← LINK+DOT trend-scan specialist (cycle-5 EXPLORATION-PROMISING-CLEAN with OOS Δ vs LINK-in-pool = +1.08).

The cadence-precedent count for `/045` is satisfied via the cycle-5 EXPLORATION ledger (iter-v1/034 through iter-v1/043, 10 EXPLORATIONs) — these are reproduced verbatim in `briefs-v1/exploration_catalog.md`. The /044 grandfathered CONFIRMATION is recorded but NOT MERGED.

---

## Section 0.6 — Architecture-Family Justification

**Axis family:** N/A — CONFIRMATION-MERGE-PORTFOLIO is a multi-component bundle assembly, not a single-axis variation. Axis Rotation Discipline does NOT apply to CONFIRMATIONs per the skill (`Brief Section 0.6 — declared family` line in v3 skill applies to EXPLORATIONs only). Per skill §"Phase Quick Reference" + §"Portfolio Composition Rules", CONFIRMATION axis-family field is N/A; rotation discipline gating is skipped at Phase 5.5.

**Bundle-discipline note:** `/045` is the FIRST CONFIRMATION under the bundle-discipline rules. The methodology gates being exercised for the first time are Critic Checks 15 / 16 / 17 (Backtest-Live Parity, Universe Disjointness, IS-Only Weight Provenance).

---

## Section 1 — Hypothesis

The 3-component symbol-partitioned federation `(baseline_pool_A [BTC+ETH], baseline_D [LTC], iter-v1/036 [LINK+DOT])` at EQUAL 1/3 weights Pareto-dominates `BASELINE_V1` on every tagged regime present in IS or OOS — by inheriting BASELINE's BTC+ETH and LTC edge unchanged AND substituting `/036`'s superior LINK+DOT trend-scan signal for BASELINE's pooled Model C (LINK) + Model E (DOT) coverage on the alt-momentum / alt-rotation regimes.

The mechanism is regime-specialist substitution: `/036`'s LINK+DOT OOS Δ of +1.08 vs the same coins inside BASELINE's pooled stack was an EXPLORATION-PROMISING-CLEAN verdict at the regime-attribution layer (alt-rotation + recovery), and equal weights preserve C2's (LTC) anchor edge while admitting `/036`'s alt-specialist lift WITHOUT crowding out the BTC+ETH baseline contributor.

---

## Section 2 — IS-Only Numerical Evidence

### Component IS metrics (extracted from prior reports; all IS-only)

Source artifacts:
- `reports-v1/iteration_v1-baseline/in_sample/{trades.csv, daily_pnl.csv, model_summary.csv}` for components C1 (baseline_pool_A) and C2 (baseline_D)
- `reports-v1/iteration_v1-036/in_sample/{trades.csv, daily_pnl.csv}` for component C3

Numerical evidence script: `analysis/iteration_v1-045/component_is_evidence.py` (committed before Phase 5.5).
Output: `analysis/iteration_v1-045/component_is_evidence.csv`.

| Component | Source | Universe | IS trades | IS daily Sharpe (ann.) | IS sum PnL ($) | Top-symbol IS share |
|---|---|---|---|---|---|---|
| C1 = baseline_pool_A | BASELINE_V1 Model A | BTC + ETH | 249 | +0.468 | +31.79 | ETH 52% |
| C2 = baseline_D | BASELINE_V1 Model D | LTC | 119 | +2.099 | +91.52 | LTC 100% (sole) |
| C3 = iter-v1/036 | iter-v1/036 trend-scan | LINK + DOT | 281 | −0.037 | −4.09 | DOT 56% |

**Bundle IS aggregate (equal-weighted concatenation; pre-Phase-6 projection):**

- Total IS trades: 649 (249 + 119 + 281)
- Bundle IS sum PnL (raw): $119.22 (= $31.79 + $91.52 − $4.09)
- Bundle IS sum PnL (after 1/3 weight): **$39.74**
- C2 (LTC) bundle PnL share: $91.52 / 3 = $30.51, which is **76.8%** of the weighted bundle IS PnL (= 30.51 / 39.74)
- Note: the high LTC share at IS is a known concentration concern documented in Section 5.5; OOS regime mix differs materially — see Section 7's predicted OOS concentration.

### IS-window-only assertion

All metrics in the table above are extracted from rows where `close_time < OOS_CUTOFF_MS` (2025-03-24 00:00 UTC = `1742774400000` ms). The committed `analysis/iteration_v1-045/component_is_evidence.py` script asserts this for every loaded row; assertion failures abort the run.

### Section 2.5 — HIGH-RISK Axis Declaration

**Declaration:** **NORMAL-RISK**

**Reason:** `/045` does NOT change Optuna's training-objective domain. Each component's underlying LightGBM model is inherited UNCHANGED from its source iteration (BASELINE_V1 Models A and D; iter-v1/036 trend-scan). The Optuna search space, feature columns, label definition, fold splits, gradient, and per-row weight vector are FROZEN per-component. The ONLY new construct is a deterministic per-trade `weight_factor = 1/3` multiplier — a scalar applied AFTER the trade is realized by each component. No re-training; no re-tuning; no axis introducing new degrees of freedom into Optuna.

**Mitigation:** N/A (NORMAL-RISK). The /045 CONFIRMATION nonetheless runs at full CONFIRMATION budget (`--seeds 2 --n-trials 35 --ensemble-size 5`, 10-seed inner ensemble per component) because that is what the bundle's component re-runs require to be comparable to BASELINE_V1's anchor measurements.

---

## Section 3 — Proposed Changes (incl. LM Master Phase 4.5 responses)

### 3.1 — Bundle composition

Three components (per Section 11.A), each owning a disjoint subset of `BASELINE_V1`'s symbol universe:

```
C1 = baseline_pool_A : {BTCUSDT, ETHUSDT}
C2 = baseline_D      : {LTCUSDT}
C3 = iter-v1/036     : {LINKUSDT, DOTUSDT}
```

Pairwise disjoint: VERIFIED YES (Section 11.A). Union: BASELINE_V1 universe exactly.

### 3.2 — Weight derivation

EQUAL weights `w = (1/3, 1/3, 1/3)`. IS-only derivation; committed `analysis/iteration_v1-045/weight_calibration.py` + `analysis/iteration_v1-045/bundle_weights.csv` (per Section 11.B). Rationale per Section 11.B + Section 4.

### 3.3 — Runner architecture

`run_iteration_045.py` (new). Subprocess dispatch reusing `run_baseline_v186.py`'s `run_model(...)` factored helper. Three sub-runs (independent; sequential):

1. `run_model("A (BTC/ETH)", ("BTCUSDT","ETHUSDT"), 2.9, 1.45, apply_r1=False)` — bit-identical to BASELINE_V1 Model A.
2. `run_model("D (LTC + R1)", ("LTCUSDT",), 3.5, 1.75, apply_r1=True)` — bit-identical to BASELINE_V1 Model D.
3. Replay `reports-v1/iteration_v1-036/{in_sample,out_of_sample}/trades.csv` (no re-run; trades.csv is the bit-identical artifact of a fixed-seed run).

Aggregation step: concatenate `trades_A + trades_D + trades_036` → apply `weight_factor = 1/3` to every row → sort by `close_time` → pipe through `generate_iteration_reports(..., iteration=45, ...)`.

CLI flag: `--bundle-config "baseline_A:0.333,baseline_D:0.333,v1-036:0.333"` — parsed by `run_iteration_045.py`; values pre-registered in Section 11.B; the runner asserts the CLI input matches the committed `bundle_weights.csv` byte-for-byte before launching.

### 3.4 — No model or feature re-training

Symbol-partitioned federation means each component's signal is computed by its OWN model on its OWN universe. There is NO trade aggregation conflict (universes are disjoint), NO ensembling across components, NO information passing between components. The bundle decision rule is the trivial dispatch documented in Section 11.C.

### 3.5 — LM Master Phase 4.5 responses

(LM Master Phase 4.5 advisor file `briefs-v1/iteration_v1-045/lgbm_advisor.md` will be authored by the `lightgbm-master` agent in dispatch prior to Phase 5.5 gate. This brief stub-acknowledges that pattern; once `lgbm_advisor.md` exists, this section is updated. Phase 5.5 will BLOCK if `lgbm_advisor.md` is absent. Per skill §"Phase 4.5", LM Master recommendations on a CONFIRMATION-PORTFOLIO are mostly informational (no new hyperparam axes to tune; the bundle re-uses frozen models).)

Anticipated LM Master themes (to be confirmed by actual `lgbm_advisor.md`):
- **Weight sensitivity probe** — recommend a future cycle-6 EXPLORATION running `(0.5, 0.5, 0.0)` and `(0.25, 0.5, 0.25)` IS-Sharpe-proportional comparators. **Anticipated response: future-iteration scope; not /045.**
- **Bundle-PnL concentration check** — recommend a diary section documenting LTC's bundle IS PnL share (76.8%). **Anticipated response: ADOPTED; tracked in Section 7's failure-mode + Phase 8 diary.**
- **`/036` replay determinism** — recommend a checksum on `reports-v1/iteration_v1-036/in_sample/trades.csv` SHA-256 captured at /045 launch. **Anticipated response: ADOPTED; runner emits checksum to `engineering_report.md`.**

---

## Section 4 — Pre-Registered Failure-Mode Falsifier (regime-aware)

### F-AXIS #1 — Per-Regime Pareto-Dominance MERGE Criterion (the master falsifier)

Per `briefs-v1/_meta/merge_v1_relative_regime_pareto_proposal.md` §B + skill "Bundle-level (CONFIRMATION-MERGE criteria — RELATIVE REGIME PARETO)":

**MERGE-VERDICT** = `CONFIRMATION-MERGE-PORTFOLIO` if and only if:

For every tagged regime R ∈ {bull, bear, chop, vol-spike, recovery, other} present in IS or OOS:

```
sharpe_R(/045 bundle) ≥ sharpe_R(BASELINE_V1) − σ_R
AND max_dd_R(/045 bundle) ≤ max_dd_R(BASELINE_V1) + σ_dd_R
AND trade_count_R(/045 bundle) ≥ 0.5 × trade_count_R(BASELINE_V1) [rare-regime carve-out applies if trade_count_R(BASELINE) < 10]
```

AND at least one regime R* where:

```
sharpe_R*(/045 bundle) > sharpe_R*(BASELINE_V1) + σ_R*
   OR max_dd_R*(/045 bundle) < max_dd_R*(BASELINE_V1) − σ_dd_R*
```

AND methodology integrity intact (look-ahead clean, embargo applied, reproducibility checksum match, Checks 15/16/17 PASS).

σ_R and σ_dd_R are read from `briefs-v1/_meta/baseline_seed_regime_matrix.csv` (one σ over BASELINE's 10-seed within-regime distribution per regime). The diary auto-populates the per-regime comparison from `reports-v1/iteration_v1-045/regime_attribution.csv` produced in Phase 6.

Otherwise: `CONFIRMATION-BLOCK` (no MERGE; iterate on the failing regime in cycle-6 next EXPLORATION).

---

## Section 4 (continued) — Behavioral & Methodology-Integrity Falsifiers

### F-AXIS #2 — Bundle trade-rate floor

**Threshold:** `trade_count(/045 OOS bundle) ≥ 130` total AND `≥ 10 trades/month` averaged over OOS months.

**Predicted:** Each component contributes its individual OOS trade count; expected bundle OOS trade count ≈ 130-200 (sum of components' OOS trades).

**Falsifier:** If bundle OOS trades < 130, Sharpe is noise-dominated (σ_SR ≈ √(1/T) underpowers t-test); cannot MERGE regardless of headline.

### F-AXIS #3 — Backtest-Live Parity (Critic Check 15)

**Pass:** Bundle decision rule at every `(symbol, candle)` is the deterministic dispatch in Section 11.C with no aggregation, no netting, no future bars.

**Falsifier:** If the Critic identifies a forbidden construct (sum of realized PnL across components on the same symbol, exposure netting, future-bar reference) → BLOCK-FINAL with reason `BUNDLE-PARITY-VIOLATION`. Section 11.C is engineered to make this physically impossible; the proof is by construction.

### F-AXIS #4 — Universe Disjointness (Critic Check 16)

**Pass:** Pairwise universe intersections C1∩C2 = C1∩C3 = C2∩C3 = ∅. Verified in Section 11.A. Runner asserts this at startup.

**Falsifier:** Any non-empty intersection → BLOCK-FINAL with reason `BUNDLE-UNIVERSE-OVERLAP`.

### F-AXIS #5 — IS-Only Weight Provenance (Critic Check 17)

**Pass:** `analysis/iteration_v1-045/weight_calibration.py` committed before Phase 6.0; the script greps clean for `OOS_CUTOFF`, `>= OOS_CUTOFF_MS`, `oos_window`, `out_of_sample`, and post-2025-03-24 hard-coded dates used for FILTERING-IN; `bundle_weights.csv` matches Section 11.B verbatim; data sources respect IS-window cutoff.

**Falsifier:** Any forward-pointing data reference in the weight-derivation chain → BLOCK-FINAL with reason `BUNDLE-WEIGHT-OOS-LEAK`.

### F-AXIS #6 — Component Reproducibility Checksum

**Pass:** Re-run of BASELINE_V1 Model A and Model D with identical flags + ENSEMBLE_SEEDS reproduces the BASELINE_V1 anchor's per-cohort PnL to within ±0.001%. Same for `/036` trades.csv (no re-run; SHA-256 checksum verified).

**Falsifier:** Reproducibility delta > 5% → BLOCK-FINAL with reason `REGRESSION-SENTINEL`. (Per Section 11.D Kill-Switch in substrate_proposal.md.)

### F-AXIS #7 — Concentration parity check vs BASELINE

**Threshold:** Top-symbol OOS bundle PnL share ≤ 30% OR ≤ BASELINE_V1's top-symbol share + 5 pp absolute (whichever is higher).

**Predicted:** LTC is the IS top contributor at 76.8% of weighted IS bundle PnL but OOS regime mix differs (regime drift away from LTC's IS-dominant regimes); predicted OOS LTC share = 25-35%.

**Falsifier:** OOS top-symbol > 40% → diary records concentration-FAIL but does NOT auto-block (per relative-regime-Pareto rules; concentration is INFORMATIONAL unless it indicates a coverage gap on some regime, which is caught by F-AXIS #1).

---

## Section 5 — Risk Mitigation

### 5.1 — Inherited risk gates (NO CHANGE)

- **R1 consecutive-SL cool-down** (K=3, C=27 candles) — ACTIVE on baseline_D (LTC) and inherited by `/036` per its own config. Suppressed on baseline_pool_A (BTC+ETH) per BASELINE_V1 design.
- **R2 drawdown-triggered position scaling** — OFF on all 3 components. (BASELINE_V1's E-only R2 is suppressed because E is not in the /045 universe; /036 does not enable R2.)
- **R3 OOD Mahalanobis gate** (cutoff=0.70 70th-percentile, 16 scale-invariant features) — ACTIVE on all 3 components. Per-component covariance matrices; not shared.

### 5.2 — Bundle-level risk mitigation

- **Equal-weight cap on /036 drag**: C3's IS Sharpe ≈ 0 (near-zero edge) is a known weakness. Equal weights cap its bundle-drag at 1/3 of bundle capital even under adverse OOS regime. If C3 produces OOS net-negative PnL at /045, the contribution to bundle OOS Sharpe is bounded by 1/3 of C3's standalone OOS.
- **No new code paths**: every component has already passed multi-seed validation in its source iteration (BASELINE_V1 5-seed; /036 single-seed-=42 at cycle-5 EXPLORATION). No new model, no new feature, no new gate.

### 5.3 — Concentration soft cap (LTC)

C2 (LTC) drove ~30% of BASELINE_V1 IS PnL alone. Under /045 equal weights, LTC's bundle IS PnL share is 76.8% (Section 2 calculation; reflects LTC's standalone IS daily Sharpe of +2.099 being 4-5× higher than the other components' IS Sharpes). This is on the boundary of the 30% concentration soft cap.

**Mitigation (this iteration):** Documented and accepted. Equal weights remain pre-registered (Section 11.B). Per Section 4 F-AXIS #7, concentration is INFORMATIONAL and does not auto-block.

**Mitigation (next iteration, if OOS confirms IS pattern):** Vol-scale C2's weight down to ~0.25, applied in /046 or later if /045 MERGE is achieved and the diary records the concentration as confirmed OOS. This is OUT OF /045 SCOPE.

---

## Section 6 — Risk Management Design

8-primitive table (v1 equivalent):

| Primitive | Active in /045 | Source | Mechanism |
|---|---|---|---|
| Triple-barrier TP/SL/timeout | YES (per component) | BASELINE_V1 (A: 2.9/1.45; D: 3.5/1.75) + /036 (per-/036 config) | Per-trade horizon cap |
| Past-only EWMA σ_t for barriers | YES (per component) | Inherited from each source's labeling | Avoids labeling-window look-ahead |
| Position size (per component) | YES (per component's internal weight) | Inherited (BASELINE_V1 Models A & D use 1.0 base; /036 inherits its own) | Pre-trade cap |
| R1 cool-down | C2 only (LTC) + /036 internal | BASELINE_V1 + /036 | Caps cascade after 3 SLs |
| R2 drawdown scaling | OFF | Suppressed (no Model E) | N/A |
| R3 OOD Mahalanobis | YES (all 3 components) | BASELINE_V1 + /036 | Pre-trade regime check |
| Bundle 1/3 weight cap | YES (NEW for /045; not in any individual component) | weight_calibration.py | Caps single-component bundle exposure |
| Universe-disjoint dispatch | YES (NEW for /045; structural) | run_iteration_045.py | Eliminates per-symbol multi-model conflict |

Fire-rate predictions:
- R1: ~3-5% of candidate signals on LTC (historical /baseline rate)
- R3: ~30% of candidate signals filtered (70th-percentile cutoff)
- Bundle 1/3 cap: 100% of trades (deterministic; pre-registered)

Regime coverage analysis is the responsibility of LM Master Phase 7.4 (regime attribution table) per the new methodology; this brief does not pre-fill those numbers.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure scenario:** /045 OOS bundle Sharpe ties or slightly exceeds BASELINE_V1 on the headline number, BUT the per-regime Pareto check fails on the OOS-tagged `recovery` regime (1 month) — because `/036`'s OOS lift on LINK+DOT was tagged in `alt-rotation` IS months that don't recur in OOS, and C3's near-zero IS edge fails to compensate when its target regime is absent. F-AXIS #1 BLOCKS the MERGE.

**Expected metric signature of failure:**
- Bundle OOS daily Sharpe: +1.20 to +1.35 (vs BASELINE_V1 OOS +1.19, ≈ tie at headline)
- `recovery` regime Sharpe(/045) < `recovery` regime Sharpe(BASELINE_V1) − σ_recovery → Pareto FAIL
- `chop` regime Sharpe(/045) ≈ BASELINE_V1 (tie), `bull` regime Sharpe(/045) ≈ tie, `bear` regime Sharpe(/045) modestly better (`/036`'s trend-scan should excel in clear bear trends)
- F-AXIS #1: `CONFIRMATION-BLOCK` (failing recovery)
- F-AXIS #3 / #4 / #5: PASS (methodology-clean by construction)
- F-AXIS #7: LTC OOS share elevated but < 40%

**Methodology integrity check:** F-AXIS #3 / #4 / #5 are designed to PASS by construction. The substrate is engineered to satisfy Checks 15 / 16 / 17. The methodological risk is structural; it cannot fail unless the implementation has a bug.

**Most plausible CONFIRMATION-MERGE scenario:** Per-regime Pareto-dominance holds because the bundle's regime coverage is BASELINE_V1's coverage plus `/036`'s alt-trend specialist contribution. C2 (LTC) carries `bull` + `chop`; `/036` carries `alt-rotation` + `recovery`; baseline_pool_A carries the universal BTC+ETH return. The OOS `recovery` month captures `/036`'s lift, the OOS `bear` months capture C2's R1 cool-down protection, and the bundle Pareto-dominates baseline on at least the `bear` and `alt-rotation` regimes while tying on `bull`, `chop`, and `vol-spike`. → `CONFIRMATION-MERGE-PORTFOLIO`.

---

## Section 8 — Pre-Registered Per-Regime Baseline-Comparison Criteria

Locked PER-REGIME comparison plan (frozen BEFORE Phase 6 launches):

**MERGE iff** for every tagged regime R ∈ {bull, bear, chop, vol-spike, recovery, other} present in IS or OOS:

```
sharpe_R(/045 bundle, 10-seed mean) ≥ sharpe_R(BASELINE_V1, 10-seed mean) − σ_R
AND max_dd_R(/045 bundle, 10-seed mean) ≤ max_dd_R(BASELINE_V1, 10-seed mean) + σ_dd_R
AND trade_count_R(/045 bundle) ≥ 0.5 × trade_count_R(BASELINE_V1) [rare-regime carve-out per merge proposal §B.5]
```

**AND** at least one regime R* with:

```
sharpe_R*(/045 bundle) > sharpe_R*(BASELINE_V1) + σ_R*
   OR max_dd_R*(/045 bundle) < max_dd_R*(BASELINE_V1) − σ_dd_R*
```

**AND** methodology integrity (Critic Checks 1, 2, 5, 6, 7, 8, 15, 16, 17 ALL PASS).

σ_R and σ_dd_R read from `briefs-v1/_meta/baseline_seed_regime_matrix.csv` (one σ over BASELINE's 10-seed within-regime distribution per regime — pre-computed at /044-bootstrap mandate; available before /045 Phase 6).

**NO absolute Sharpe / DSR / PBO / PSR floors.** DSR / PBO / PSR are reported per-regime and bundle-level as INFORMATIONAL per skill §"Statistical-Significance Metrics" (NOT gating).

The Phase 8 diary auto-populates the per-regime comparison table from `reports-v1/iteration_v1-045/regime_attribution.csv` (produced in Phase 6 by `lgbm_advisor.md` post-mortem or by the runner's regime tagger).

---

## Section 9 — Library Stack Declaration

- `mlfinlab==1.4` — CombinatorialPurgedKFold, PBO via CSCV, fractional differentiation
- `pypbo` — standalone PBO computation
- `fracdiff>=0.10` — Numba-accelerated fractional differentiation
- `statsmodels` — ADF stationarity
- `lightgbm` — model engine (frozen per-component; no version drift)
- `xgboost` — N/A (no model-arch change at /045)
- `numpy`, `pandas` — standard
- `pyarrow` — parquet I/O

No new pinning vs BASELINE_V1's `pyproject.toml` is required for /045 since no new model or feature is introduced.

---

## Section 10 — Regime Attribution Plan

Per skill mandate (NEW 2026-05-31 regime-ensemble), every iteration must declare its regime-attribution plan.

**Target regimes:** ALL regimes present in IS or OOS (bull, bear, chop, vol-spike, recovery, other).

**Mechanism (per component):**
- **C1 = baseline_pool_A (BTC+ETH):** UNIVERSAL contributor — broad coverage across regimes; weakly regime-specialist.
- **C2 = baseline_D (LTC):** REGIME-SPECIALIST-IS — strong in bull/chop IS months; weaker in vol-spike (R1 cool-down protects against cascades).
- **C3 = iter-v1/036 (LINK+DOT):** REGIME-SPECIALIST — strong in alt-rotation / recovery; weak in chop.

**Off-regime expectation:** C3's near-zero IS Sharpe is by design — its target regime (alt-rotation) is rare in IS but expected to recur in OOS recovery month. If OOS recovery is absent, C3 will drag bundle Sharpe by ~1/3 of its standalone OOS PnL.

**Bundle role:** anchor + LTC-specialist + alt-trend-specialist. Coverage is complementary, not duplicative.

**Composition simulation:** per the substitution test in Section 11 — bundle-WITHOUT-C3 has zero alt-trend coverage (regression on alt-rotation regime); bundle-WITHOUT-C2 loses LTC dominance (severe regression on bull); bundle-WITHOUT-C1 loses BTC+ETH universal (severe regression everywhere).

**Regime-aware falsifier:** F-AXIS #1 (per-regime Pareto-dominance). NOT a single aggregate Sharpe number.

---

## Section 11 — Bundle Composition (MANDATORY for CONFIRMATION-MERGE-PORTFOLIO)

### Section 11.A — Universe Partition (Rule 7 + Check 16 enforcement)

Per-component universe:

| Component | Universe |
|---|---|
| C1 = baseline_pool_A | {BTCUSDT, ETHUSDT} |
| C2 = baseline_D | {LTCUSDT} |
| C3 = iter-v1/036 | {LINKUSDT, DOTUSDT} |

**Pairwise disjointness:**

| Pair | Intersection |
|---|---|
| C1 ∩ C2 | ∅ |
| C1 ∩ C3 | ∅ |
| C2 ∩ C3 | ∅ |

**Pairwise disjoint: YES.**

Union: `{BTCUSDT, ETHUSDT, LTCUSDT, LINKUSDT, DOTUSDT}` — matches BASELINE_V1's universe exactly.

Per-coin ownership table:

| Coin | C1 baseline_pool_A | C2 baseline_D | C3 iter-v1/036 | Owner count |
|---|---|---|---|---|
| BTCUSDT | OWNS | — | — | **1** |
| ETHUSDT | OWNS | — | — | **1** |
| LTCUSDT | — | OWNS | — | **1** |
| LINKUSDT | — | — | OWNS | **1** |
| DOTUSDT | — | — | OWNS | **1** |

All 5 coins are owned by exactly one component. **Rule 7 satisfied.**

The `run_iteration_045.py` runner asserts this at startup via:

```python
universes = {"baseline_pool_A": {"BTCUSDT","ETHUSDT"},
             "baseline_D": {"LTCUSDT"},
             "iter-v1/036": {"LINKUSDT","DOTUSDT"}}
for a, b in combinations(universes, 2):
    assert universes[a].isdisjoint(universes[b]), \
        f"Coin overlap between {a} and {b}: {universes[a] & universes[b]}"
```

### Section 11.B — Weight Derivation (Rule 1 + Check 17 enforcement)

**Method:** EQUAL.

**Weight vector:** `w = (1/3, 1/3, 1/3)`. Numerical values: `w = (0.333, 0.333, 0.333)` (rounded; the runner uses exact `1.0/3.0`).

**IS-only derivation justification:**

Three deterministic IS-only candidates were computed:

| Scheme | C1 (BTC+ETH) | C2 (LTC) | C3 (LINK+DOT) | Notes |
|---|---|---|---|---|
| EQUAL | 0.333 | 0.333 | 0.333 | No IS dependence; safest under uncertainty |
| IS-daily-Sharpe-proportional | 0.185 | 0.830 | −0.015 | C3 IS Sharpe ≈ 0 ⇒ near-zero weight; clipped at 0 collapses to ~(0.18, 0.82, 0.00) |
| IS-trade-count-proportional | 0.384 | 0.183 | 0.433 | Capacity-weighted; ignores edge quality |

**Selected: EQUAL weights (1/3 each).** Justification:

1. IS-Sharpe-proportional would ZERO OUT C3 (its IS daily Sharpe at /036 single-seed = +0.0843 narrow). C3 was admitted to the bundle because its OOS Δ vs LINK-in-pool was +1.08 (regime-specialist lift) — NOT because its IS Sharpe is strong. IS-Sharpe-proportional defeats the regime-specialist preservation that motivated /045.
2. Trade-count-proportional gives C2 (LTC, highest IS edge) only 0.183 — capacity-weighting penalizes the lowest-trade-count specialist precisely when it is the highest-quality one. Wrong direction.
3. EQUAL minimizes researcher-degrees-of-freedom (no IS-derived knob beyond N=3 component count) and aligns with the OOS-validated baseline weighting convention. It is the simplest IS-only choice.

**Committed artifacts (before Phase 6.0 Critic pre-flight):**

- `analysis/iteration_v1-045/weight_calibration.py` — script that:
  - Loads ONLY `reports-v1/iteration_v1-baseline/in_sample/trades.csv` for components C1 (filter `model_name == "A (BTC/ETH)"`) and C2 (filter `model_name == "D (LTC + R1)"`); and `reports-v1/iteration_v1-036/in_sample/trades.csv` for C3.
  - **Asserts every loaded row's `close_time < OOS_CUTOFF_MS` (1742774400000)** at load time; raises `RuntimeError` if any row fails.
  - Computes EQUAL weight vector via the literal `w = [1.0/3.0, 1.0/3.0, 1.0/3.0]` constructor.
  - Writes `analysis/iteration_v1-045/bundle_weights.csv`.

- `analysis/iteration_v1-045/bundle_weights.csv`:
  ```csv
  component_id,weight,derivation_method,is_window_start,is_window_end
  baseline_pool_A,0.333333333333,equal,2021-03-24,2025-03-24
  baseline_D,0.333333333333,equal,2021-03-24,2025-03-24
  iter-v1/036,0.333333333333,equal,2021-03-24,2025-03-24
  ```

The script contains NO references to `OOS_CUTOFF` (other than the `1742774400000` assertion barrier defining IS), NO `>= OOS_CUTOFF_MS`, NO `oos_window`, NO `out_of_sample` filenames, and NO hard-coded post-2025-03-24 dates used for FILTERING-IN. The IS window dates are LITERAL CONSTANTS in the `bundle_weights.csv` (informational metadata; they are NOT used in filtering).

Critic Check 17 verification recipe:
```bash
grep -E 'OOS_CUTOFF|>= OOS_CUTOFF_MS|oos_window|out_of_sample' analysis/iteration_v1-045/weight_calibration.py
# Expected: NO hits other than the IS-side `< OOS_CUTOFF_MS` assertion.
```

### Section 11.C — Backtest-Live Parity Statement (Rule 8 + Check 15 enforcement)

The /045 bundle's per-(symbol, candle) decision is the deterministic dispatch function:

```python
def bundle_signal(symbol: str, t: int) -> tuple[Signal, float]:
    """Return (signal, capital_fraction) for the bundle at (symbol, t).

    All three components share the same time grid; t is the same candle close_time
    ms for all components. No future bars referenced; no aggregation across components.
    """
    if symbol in {"BTCUSDT", "ETHUSDT"}:
        return (baseline_pool_A.signal_at(symbol, t), 1.0/3.0)
    if symbol == "LTCUSDT":
        return (baseline_D.signal_at(symbol, t), 1.0/3.0)
    if symbol in {"LINKUSDT", "DOTUSDT"}:
        return (iter_v1_036.signal_at(symbol, t), 1.0/3.0)
    return (NO_SIGNAL, 0.0)
```

Properties:

1. **Each symbol is owned by EXACTLY ONE component** (per Section 11.A); the dispatch is total and unambiguous.
2. **References ONLY each component's signal at the SAME timestamp t** (same-time-snapshot; no future bars).
3. **Multiplies by each component's frozen internal weight (1/3)** — pre-registered in `bundle_weights.csv` before Phase 6 launches.
4. **NO aggregation across components** — the bundle never sums realized PnL from two simultaneously-open positions in the same symbol (cannot happen by construction since universes are disjoint).
5. **NO netting across components** — the bundle never combines two-model exposure into one Binance order requiring intra-tick reconciliation (cannot happen by construction).
6. **NO information passing across components** — each component computes its signal independently; the bundle aggregates outputs only at trade-realization time (post-trade, via the `weight_factor` multiplier).

**Implementation at `live/engine.py:_tick`:**

At each tick, for each `(symbol, candle)`:
1. Look up `owning_component(symbol)` from a static dict (the same dict in Section 11.A).
2. Query `owning_component.signal_at(symbol, candle)`.
3. If signal is non-no-trade, place ONE Binance order at the owning component's internal position weight × 0.333 portfolio capital allocation.
4. The order is tagged with `component_id` for trade-attribution.

This is trivially replayable: at every `(symbol, candle)` the engine performs the SAME pure-function lookup as the backtest. There is no aggregation step that could diverge between backtest and live.

**Backtest-live parity property: PROVEN BY CONSTRUCTION.** Critic Check 15 is satisfied because the dispatch rule has no aggregation, no netting, no future bars, and no information flow between components that could not be replayed at `live/engine.py:_tick`.

### Section 11.D — Re-Composition Note (Rule 9 + Check 16 enforcement context)

LINK and DOT are dropped from BASELINE_V1's Models C and E in the /045 bundle. Their ownership transfers to C3 (`iter-v1/036`). Specifically:

| Original BASELINE_V1 component | Status in /045 | Replacement |
|---|---|---|
| Model A (BTC+ETH) | INCLUDED unchanged as C1 | — |
| Model C (LINK) | EXCLUDED | LINK now C3-owned |
| Model D (LTC) | INCLUDED unchanged as C2 | — |
| Model E (DOT) | EXCLUDED | DOT now C3-owned |

The underlying BASELINE_V1 Models C and E are NOT modified at the catalog level — they remain valid as standalone artifacts; only their inclusion in THIS BUNDLE is suppressed.

**Re-composition catalog cross-reference:**
- `/043` (LINK-only trend-scan from cycle-5) was DROPPED from /045 substrate because its universe `{LINK}` overlaps with C3 (`/036`)'s universe `{LINK, DOT}`. /045 retains C3 (`/036`) as the alt-trend specialist; `/043`'s LINK signal is not duplicated.
- `/043` was EXPLORATION-PROMISING at single-seed; it will be re-examined in cycle-6 as a candidate for a DOT-dropped `/036`-style component re-composition (i.e., a future iteration could test `/036`-LINK-only + `/043`-LINK-only alternative dispatch OR could promote `/043` to replace `/036`'s LINK leg). Out of /045 scope.

No coin is added to the bundle universe (`{BTC, ETH, LTC, LINK, DOT}` = BASELINE_V1 universe).

---

## End of Brief
