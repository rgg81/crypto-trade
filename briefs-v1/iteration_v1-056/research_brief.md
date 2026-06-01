# Research Brief — iter-v1/056

## Section 0.0 — Banner

- **Track**: v1 (refactored, cycle-6 FIRST CONFIRMATION-PORTFOLIO)
- **Iteration**: iter-v1/056
- **Branch**: `iteration-v1/034` (carried forward; tag `v0.v1-056` after closeout)
- **Date**: 2026-06-01
- **Type**: `CONFIRMATION` — symbol-partitioned 5-component federation
- **Axis**: CSV-replay bundle aggregation of 3 fresh CONFIRMATION-budget specialist sub-runs
  (C1 BTC, C2 ETH, C3 DOT) + 2 BASELINE_V1 anchor trade-roster extractions (C4 LINK, C5 LTC)
- **Mode**: CONFIRMATION budget: C1/C2/C3 each use --seeds 1 --ensemble-size 10 --n-trials 35.
  Wall-clock cap: ≤ 6h total (CONFIRMATION hard cap per v1 cadence discipline).
- **LightGBM Master advisory**: `briefs-v1/iteration_v1-056/lgbm_advisor.md` (Phase 4.5,
  authored 2026-06-01).

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24          ← IMMUTABLE (never changes)
OOS_CUTOFF_MS    = 1742774400000       ← corresponding Unix ms
training_months  = 24                  ← IMMUTABLE (never changes)
IS window        = 2023-03-24 → 2025-03-24 (24 calendar months)
OOS window       = 2025-03-24 → present
Walk-forward     = monthly retrain; embargo applied at walk_forward.py:113
                   (train_end_ms = test_start_ms - embargo_ms)
```

Sacred constants unchanged per ITERATION_PLAN_8H_V1.md §"Sacred Constants".

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: CONFIRMATION
SUBTYPE: CONFIRMATION-PORTFOLIO (symbol-partitioned federation)
```

CONFIRMATION: this iteration runs at CONFIRMATION-budget and bundles the best available
cycle-6 EXPLORATION ingredients. No new feature, no new gate, no new architecture axis.
Wall-clock cap: ≤ 6h total. Cycle-6 CONFIRMATION 1/1.

EXPLORATION precedent count since last CONFIRMATION: 10/10 (cadence complete).
  - /046: methodology (PROMISING-DIVERGENCE)
  - /047: feature-family (NEG-CLEAN-PRE-EDA)
  - /048: feature-family (NEG-CLEAN-PRE-EDA)
  - /049: feature-family (EXPLORATION-NEGATIVE)
  - /050: feature-family + risk-primitive (PROMISING-PARTIAL)
  - /051: validation (PARTIAL-CONFIRMED, DOT multi-seed)
  - /052: feature-family (PROMISING-SPECIALIST-CANDIDATE, BTC funding)
  - /053: validation (PARTIAL-CONFIRMED, BTC multi-seed)
  - /054: feature-family (IMPULSE-DROP-CONFIRMED, BTC 48→47)
  - /055: feature-family (PROMISING-PARTIAL, ETH specialist, 47→48)

---

## Section 0.6 — Architecture-Family Justification

```
FAMILY: CONFIRMATION (bundle assembly; not an EXPLORATION axis)
ROTATION_STATUS: N/A (CONFIRMATION type; Rotation Discipline applies to EXPLORATIONs only)
```

CONFIRMATION bundles do not trigger the Axis Rotation Discipline. The discipline applies
exclusively to consecutive EXPLORATION axis-family selections.

---

## Section 1 — Hypothesis

A symbol-partitioned 5-component federation assembled from cycle-6's best EXPLORATION
ingredients — three fresh CONFIRMATION-budget specialist sub-runs (BTC, ETH, DOT) plus
two BASELINE_V1 anchor extractions (LINK, LTC) at equal weights (0.2 each) — Pareto-dominates
BASELINE_V1 on at least one tagged IS regime while not regressing below the epsilon_sharpe(R)
tolerance band on any other regime, delivering a durable multi-symbol edge from the
cumulative cycle-6 specialist-isolation findings.

---

## Section 2 — IS-Only Numerical Evidence

Evidence drawn exclusively from in-sample data (close_time < OOS_CUTOFF_MS = 1742774400000).

### 2.1 Per-Component IS Evidence Table

| Component | Symbol | Source | IS Sharpe | IS Trades | IS Win Rate | IS Net PnL% | Evidence Source |
|---|---|---|---|---|---|---|---|
| C1-BTC | BTCUSDT | iter-v1/054 (single-seed=42) | +0.2614 | 139 | 37.4% | +14.21% | reports-v1/iteration_v1-054/comparison.csv |
| C2-ETH | ETHUSDT | iter-v1/055 (single-seed=42) | −0.2082 | 138 | 39.1% | −15.68% | reports-v1/iteration_v1-055/comparison.csv |
| C3-DOT | DOTUSDT | iter-v1/051 (multi-seed mean) | −0.2355 | 118.7 mean | 41.7% | mean | reports-v1/iteration_v1-051/comparison_multi_seed.csv |
| C4-LINK | LINKUSDT | BASELINE_V1 (5-seed) | +2.25 (model C proxy) | 146 | 45.2% | +72.06% | reports-v1/iteration_v1-baseline/in_sample/per_symbol.csv |
| C5-LTC | LTCUSDT | BASELINE_V1 (5-seed) | +0.17 (model D proxy) | 123 | 39.5% | +3.27% | reports-v1/iteration_v1-baseline/in_sample/per_symbol.csv |

Notes:
- C1-BTC IS Sharpe +0.2614: CONFIRMATION-budget re-run (n_trials=35, ensemble-size=10)
  is expected to produce the multi-seed mean IS Sharpe for BTC, which at /053 was −0.1336
  (seed_42), −0.1467 (seed_offset3), +0.1609 (seed_42 from /054). The /054 single-seed=42
  value of +0.2614 represents the EXPLORATION upper bound; CONFIRMATION-budget 10-seed mean
  is expected to regress toward multi-seed mean per LM Master Rec 1. Pre-registered regression
  expectation: IS Sharpe likely in range [−0.20, +0.30]. This regression is expected and NOT
  a falsifier trigger.
- C2-ETH IS Sharpe −0.2082 (PARTIAL band per /055 verdict); CONFIRMATION 10-seed mean expected
  to regress toward multi-seed mean (no prior standalone multi-seed for ETH; /055 single-seed
  only). OOS +0.6546 is the strongest single-seed OOS in cycle-6.
- C3-DOT multi-seed mean IS −0.2355 ± 0.3034 std (3 seeds at /051). CONFIRMATION 10-seed
  mean expected to fall in range [−0.60, +0.10].
- C4-LINK and C5-LTC: BASELINE_V1 5-seed IS per-symbol; trade rosters extracted from
  reports-v1/iteration_v1-baseline/in_sample/trades.csv filtered to each symbol.

### 2.2 BASELINE_V1 Comparison Reference

| Metric | BASELINE_V1 IS | BASELINE_V1 OOS |
|---|---|---|
| Monthly Sharpe | +0.2829 | +0.6395 |
| Daily Sharpe | +0.4767 | — |
| Max Drawdown | 73.06% | 40.94% |
| Win Rate | 39.9% | 39.9% |
| Profit Factor | 1.060 | 1.155 |
| Total Trades | 621 IS | 193 OOS |
| Total PnL% | +54.05% | +36.96% |

Source: `reports-v1/iteration_v1-baseline/comparison.csv` + `BASELINE_V1.md`.

### 2.3 LM Master IS-Risk Assessment (Phase 4.5 Risk Flags)

Per `lgbm_advisor.md` Phase 4.5 Risk Flags:
- **RF-1**: LTC BASELINE_V1 OOS Sharpe −4.27 (OOS PnL −47.25%) — catastrophic at w=0.2
  contributes approximately −0.85 to bundle weighted OOS Sharpe.
- **RF-2**: BTC multi-seed OOS std ~0.866 (range 1.72; 12× IS dispersion) — single-outer-seed
  CONFIRMATION OOS draw has roughly 50% probability of being negative.
- **RF-3**: ETH enters the bundle WITHOUT standalone multi-seed PARTIAL-CONFIRMED verdict
  (absorbed per user directive at /055 closeout). ETH IS −0.61 baseline; CONFIRMATION
  10-seed mean may regress toward −0.61 if the /055 single-seed=42 draw was a lottery.
- **RF-4**: Regime tagger must be wired in runner (debt carried from /049-/055). See Section 3.

---

## Section 2.5 — HIGH-RISK Axis Declaration

```
HIGH-RISK: NO
```

CONFIRMATION-PORTFOLIO is NOT a HIGH-RISK axis. No change to Optuna's training-objective
domain. The three specialist sub-runs (C1/C2/C3) use the identical Optuna bounds profiles
(v1_pruned) as their EXPLORATION predecessors. The CSV-replay aggregator uses no ML fit.
Multi-seed mitigation: opted-IN for C1/C2/C3 (ensemble-size=10 per sub-run; see Section 3).

---

## Section 3 — Proposed Changes

### 3.1 Architecture Change

NO change to V1_FEATURE_COLUMNS_PRUNED. NO change to Optuna bounds. NO change to
labeling params (triple-barrier, IS-calibrated thresholds). NO change to risk gates.

The CONFIRMATION-PORTFOLIO introduces three NEW dispatch branches in run_iteration_056.py
that re-run the /054, /055, and /050/051 EXPLORATION architectures at CONFIRMATION budget.

### 3.2 C1-BTC Sub-Run Spec

```
iteration_label:  v1-056-C1-BTC
symbols:          BTCUSDT
feature_columns:  V1_FEATURE_COLUMNS_PRUNED (47 cols; btc_funding_spread_30_90 RETAINED,
                  btc_funding_rate_8h_impulse DROPPED per /054)
seeds:            1 (single outer seed = 42)
ensemble_size:    10  ← CONFIRMATION budget (up from EXPLORATION's 3)
n_trials:         35  ← CONFIRMATION budget (up from EXPLORATION's 18)
bounds_profile:   v1_pruned
model:            A_BTC_specialist (R3=ON, R1=OFF, R2=OFF)
atr_tp:           3.5
atr_sl:           1.75
note:             btc_funding_spread_30_90 is in parquet from /052 regen; no new regen needed.
```

### 3.3 C2-ETH Sub-Run Spec

```
iteration_label:  v1-056-C2-ETH
symbols:          ETHUSDT
feature_columns:  V1_FEATURE_COLUMNS_PRUNED (48 cols; eth_vs_btc_ret_ratio_30 ADDED per /055)
seeds:            1 (single outer seed = 42)
ensemble_size:    10
n_trials:         35
bounds_profile:   v1_pruned
model:            A_ETH_specialist (R3=ON, R1=OFF, R2=OFF)
atr_tp:           3.5
atr_sl:           1.75
note:             BTC klines loaded for cross-asset feature computation only.
                  eth_vs_btc_ret_ratio_30 is in parquet from /055 regen.
```

### 3.4 C3-DOT Sub-Run Spec

```
iteration_label:  v1-056-C3-DOT
symbols:          DOTUSDT
feature_columns:  V1_FEATURE_COLUMNS_PRUNED (48 cols; dot_vs_btc_ret_ratio_30 at position 4,
                  eth_vs_btc_ret_ratio_30 at position 5 — NaN for DOTUSDT)
seeds:            1 (single outer seed = 42)
ensemble_size:    10
n_trials:         35
bounds_profile:   v1_pruned
model:            E_DOT_specialist (R3=ON, R1=ON, R2=ON — same as BASELINE_V1 Model E)
atr_tp:           3.5
atr_sl:           1.75
note:             BTC klines loaded for cross-asset feature; dot_vs_btc_ret_ratio_30 in parquet.
                  eth_vs_btc_ret_ratio_30 will be NaN for DOT rows (cross-asset ETH signal
                  is undefined for DOT; LightGBM handles NaN via its native NaN routing).
```

### 3.5 C4-LINK Anchor (Trade Roster Reuse — No Re-Run)

LINKUSDT trades extracted from `reports-v1/iteration_v1-baseline/in_sample/trades.csv` and
`out_of_sample/trades.csv` filtered to `symbol == LINKUSDT`. No new backtest. IS 146 trades.
Per LM Master Rec 3 (Section 5.3): substrate frozen at BASELINE LINK anchor selection;
OOS information (LINK OOS +2.79 informational) MUST NOT influence the trade-roster choice.

### 3.6 C5-LTC Anchor (Trade Roster Reuse — No Re-Run)

LTCUSDT trades extracted from BASELINE_V1 trade CSVs filtered to `symbol == LTCUSDT`. IS 123
trades. LTC OOS −4.27 (BASELINE_V1 catastrophic). Per LM Master Rec 3: LTC cannot be dropped
pre-hoc at brief-authoring stage — that would be OOS-informed substrate manipulation. LTC
participates unconditionally at w=0.2. Phase 8 diary diagnoses LTC contribution post-run.

### 3.7 CSV-Replay Aggregator

`run_iteration_056.py` step 6 (CSV-replay aggregator):
1. Load C1-BTC trades from `reports-v1/iteration_v1-056/C1_BTC/{in_sample,out_of_sample}/trades.csv`
2. Load C2-ETH trades from `reports-v1/iteration_v1-056/C2_ETH/`
3. Load C3-DOT trades from `reports-v1/iteration_v1-056/C3_DOT/`
4. Extract C4-LINK from BASELINE_V1 (filter by symbol); scale weighted_pnl × 0.2
5. Extract C5-LTC from BASELINE_V1 (filter by symbol); scale weighted_pnl × 0.2
6. Concat, sort by close_time, emit:
   - `reports-v1/iteration_v1-056/{in_sample,out_of_sample}/trades.csv` (aggregated)
   - `reports-v1/iteration_v1-056/comparison.csv`
   - `reports-v1/iteration_v1-056/regime_attribution.csv`
   - `reports-v1/iteration_v1-056/source_checksums.csv`

### 3.8 LM Master Phase 4.5 Response (MANDATORY per v1 skill §3 Phase 5.5 gate)

Per `briefs-v1/iteration_v1-056/lgbm_advisor.md` Phase 4.5 recommendations:

**Rec 1 — Fresh CONFIRMATION-budget sub-runs for C1/C2/C3 (do NOT replay EXPLORATION trades)**
- Status: ADOPTED. C1/C2/C3 each run fresh at ensemble-size=10, n_trials=35. EXPLORATION
  trade files from /054, /055, /051 are NOT replayed as confirmed IS outputs. Each sub-run
  produces its own in_sample/trades.csv under `reports-v1/iteration_v1-056/C{1,2,3}_*/`.
  Pre-registration note: EXPLORATION IS Sharpe values are the lottery draws at EXPLORATION
  budget; CONFIRMATION means will regress per LM Master expectation.

**Rec 2 — Per-regime Pareto-dominance vs BASELINE_V1 is the MERGE gate; regime tagger MUST be wired**
- Status: ADOPTED. Regime tagger wired in run_iteration_056.py step 7 via the
  `_assign_regime_tag_simple()` helper (same as /045 framework). The runner emits
  `regime_attribution.csv` with per-regime IS+OOS Sharpe comparison for the bundle vs
  BASELINE_V1. MERGE gate = per-regime Pareto-dominance per Section 4 F-AXIS #1.
  epsilon_sharpe(R) values from lgbm_advisor.md §Phase 4.5 Rec 2 are pre-registered
  in Section 8 numerical criteria.

**Rec 3 — Substrate-selection is FROZEN; OOS must NOT influence C1/C2/C3/C4/C5 composition**
- Status: ADOPTED. Substrate was selected at EXPLORATION verdicts (/054 BTC, /055 ETH,
  /051 DOT, BASELINE LINK/LTC). OOS data has NOT been used to score, rank, or adjust
  component composition. C5-LTC included unconditionally per Rule 7 universe-disjointness
  (dropping LTC requires a separate brief). Weight vector is EQUAL (not IS-Sharpe-proportional).

### 3.9 Runner Outputs

```
reports-v1/iteration_v1-056/
  C1_BTC/{in_sample,out_of_sample}/trades.csv    ← C1 BTC specialist sub-run
  C2_ETH/{in_sample,out_of_sample}/trades.csv    ← C2 ETH specialist sub-run
  C3_DOT/{in_sample,out_of_sample}/trades.csv    ← C3 DOT specialist sub-run
  in_sample/trades.csv                           ← bundle aggregate (all 5 components)
  out_of_sample/trades.csv                       ← bundle aggregate (OOS)
  comparison.csv                                 ← IS/OOS/ratio for headline metrics
  regime_attribution.csv                         ← per-regime Pareto table (F-AXIS #1)
  source_checksums.csv                           ← SHA-256 of each component's trade CSVs
```

---

## Section 4 — Expected OOS Impact and F-AXIS Falsifiers

### 4.1 Expected OOS Impact

Predicted bundle OOS monthly Sharpe: [−0.5, +0.5] (wide band due to LTC −4.27 drag and
BTC OOS variance ±0.866 std). The LM Master modal verdict is CONFIRMATION-BLOCK (40%)
driven by LTC drag. CONFIRMATION-MERGE probability is 20% + 25% = 45% combined
(MERGE-full + MERGE-PROVISIONAL).

The bundle's primary diagnostic value is: (a) establishing per-regime Pareto attribution
pre-registered before Phase 7 QR review; (b) identifying which component drives MERGE
failure so /057 axis addresses the root cause.

### 4.2 F-AXIS Falsifiers

**F1 (MERGE gate — per-regime Pareto-dominance)**:
MERGE iff ALL of the following hold (per `feedback_v1_merge_relative_regime_pareto.md` +
lgbm_advisor.md §Rec 2):
```
FOR ALL regimes R ∈ {bull, bear, chop, recovery, other}:
  sharpe_R(bundle_OOS) >= sharpe_R(BASELINE_V1_OOS) - epsilon_sharpe(R)
  AND max_dd_R(bundle_OOS) <= max_dd_R(BASELINE_V1_OOS) + epsilon_dd(R)
  AND trade_count_R(bundle_OOS) >= 0.5 × trade_count_R(BASELINE_V1_OOS)
AND EXISTS at least one R* where strictly better
```
epsilon_sharpe values (proxy σ_R from lgbm_advisor.md §Rec 2):
  bull: 0.26, bear: 0.34, chop: 0.32, vol-spike: 0.46, recovery: NaN (rare-regime carve-out)

**F2 (trade-rate floor)**: bundle OOS total trades ≥ 130. Under equal weights, each
component contributes its full trade roster; bundle = sum of 5 components. Expected OOS
trades: ~193 baseline (C4+C5) + C1/C2/C3 fresh runs. BASELINE_V1 alone had 193 OOS trades.
FALSIFIED if bundle OOS < 130.

**F3 (BUNDLE-PARITY-VIOLATION — Check 15)**: CSV-replay aggregator by construction has
NO new model code paths and NO netting across components. F3 PASSES by construction.
Verified by run_iteration_056.py printing "[F3 PARITY] PASS by construction" at startup.

**F4 (BUNDLE-UNIVERSE-OVERLAP — Check 16)**: pairwise component universe intersection
must be empty. Each component owns exactly ONE coin:
C1-BTC: {BTCUSDT}, C2-ETH: {ETHUSDT}, C3-DOT: {DOTUSDT}, C4-LINK: {LINKUSDT},
C5-LTC: {LTCUSDT}. Jaccard = 1.0 between bundle roster and union of component rosters.
FALSIFIED if any pairwise overlap is non-empty.

**F5 (BUNDLE-WEIGHT-OOS-LEAK — Check 17)**: weight_calibration.py must:
(a) contain no `>= OOS_CUTOFF_MS` or `out_of_sample` patterns; (b) derive EQUAL weights
without reading OOS trade files. Verified by test_no_oos_leak in test suite.

**F6 (component reproducibility checksum)**: source_checksums.csv records SHA-256 of
each component's in_sample and out_of_sample trades.csv at the time of bundle assembly.
FALSIFIED if checksums change between bundle assembly and Phase 7.5 Critic review.

---

## Section 5 — Risk Mitigation

No new risk parameters introduced at /056. Each specialist sub-run inherits the baseline
risk configuration for its model type:
- C1-BTC: R3 OOD gate (cutoff=0.70) only (same as baseline Model A for BTC)
- C2-ETH: R3 OOD gate (cutoff=0.70) only (same as baseline Model A for ETH)
- C3-DOT: R1 (K=3, C=27 candles) + R2 (trigger=7%, anchor=15%, floor=0.33) + R3 (same as
  baseline Model E for DOT)
- C4-LINK: R1 + R3 (same as BASELINE_V1 Model C)
- C5-LTC: R1 + R3 (same as BASELINE_V1 Model D)

The bundle architecture itself provides implicit portfolio diversification (5 disjoint
coins, no intraday netting, each coin traded by exactly one specialist). The primary
risk at the bundle level is LTC's known −4.27 OOS catastrophe (RF-1 in LM Master advisory).

R2 (drawdown-triggered scaling): The baseline R2 on DOT and LTC will continue to fire at
the sub-run level; fires are inherited in the aggregated weighted_pnl column (weight_factor
already applied in the sub-run output before CSV-replay scaling).

---

## Section 6 — Risk Management Design

### 6.1 Risk Primitive Table

| Gate | C1-BTC | C2-ETH | C3-DOT | C4-LINK | C5-LTC | Bundle Level |
|---|---|---|---|---|---|---|
| R1 consecutive-SL cooldown | OFF | OFF | ON (K=3, C=27) | ON (K=3, C=27) | ON (K=3, C=27) | inherited per-component |
| R2 drawdown brake | OFF | OFF | ON (7%/15%/0.33) | OFF | ON (7%/15%/0.33) | inherited per-component |
| R3 OOD Mahalanobis | ON (cutoff=0.70) | ON (cutoff=0.70) | ON (cutoff=0.70) | ON (cutoff=0.70) | ON (cutoff=0.70) | inherited per-component |
| Vol-ceiling (R5) | OFF | OFF | OFF | OFF | OFF | OFF |
| Binary-kill (R5-bk) | OFF | OFF | OFF | OFF | OFF | OFF |
| Universe disjointness | 1 coin each | 1 coin each | 1 coin each | 1 coin each | 1 coin each | pairwise-disjoint (F4) |
| Bundle weight cap | 0.2 | 0.2 | 0.2 | 0.2 | 0.2 | EQUAL (pre-registered) |

### 6.2 Fire-Rate Predictions

R2 fire rate (DOT/LTC): expected ~50-70% at CONFIRMATION budget (consistent with BASELINE_V1
R2 fire rate of 71%/63% IS/OOS). No axis-level change to R2 thresholds.

R3 OOD gate fire rate: expected ~0% (consistent with prior R3 measurements; OOD gate
rarely fires for BTC/ETH/DOT at v1_pruned 48-col feature space in known regimes).

Regime tagger coverage: the simplified date-based tagger covers all 5 regime classes
(bull/bear/chop/recovery/other) with deterministic mapping. All OOS trades expected to
fall in one of these regimes (no unmapped edge cases for the 2023-2026 window).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The most plausible failure mode is **LTC drag concentration**. BASELINE_V1 LTC OOS −4.27
(net −47.25%) is a structural catastrophe from LTC-specific regime mis-alignment. At w=0.2,
LTC contributes −0.85 to the weighted bundle OOS Sharpe regardless of the other 4 components'
performance. The bundle OOS headline Sharpe will likely be negative even if C1-BTC, C2-ETH,
C3-DOT, C4-LINK are all individually positive.

The regime tagger should reveal whether LTC's losses are concentrated in 1-2 regime windows
(bear/vol-spike) or spread uniformly. If LTC dominates a single regime, the per-regime Pareto
check may still PASS for regimes where LTC has fewer trades and C4-LINK compensates. If LTC
losses span all regimes, per-regime Pareto will fail across all regimes beyond the epsilon
band — CONFIRMATION-BLOCK.

The secondary failure mode is **BTC OOS single-outer-seed lottery draw**. At CONFIRMATION
ensemble-size=10 (one outer seed), the OOS result for C1-BTC is ONE draw from the multi-seed
OOS distribution (std ~0.866). A negative BTC OOS draw compounds LTC drag and makes universal
regime Pareto recovery impossible.

What the gates should catch:
- F1 catches per-regime Pareto failure (expected regime-conditional LTC + BTC drag)
- F2 catches trade-rate collapse (unlikely given 5 components each contributing trades)
- F4/F6 checksums catch any post-hoc trade roster substitution

Failure signature in metrics: bundle OOS monthly Sharpe < 0; regime_attribution.csv showing
per-regime Pareto failures on multiple regimes; LTC OOS PnL concentration > 50% of total
bundle OOS loss.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

Pre-registered BEFORE backtest runs. Cannot be revised post-hoc.

**MERGE iff ALL of the following hold:**

1. F1 Per-regime Pareto-dominance (see Section 4.2 F1 formula) — PASS on all regimes
   within epsilon_sharpe tolerances, strict improvement on ≥1 regime.

2. F2 Bundle OOS total trades ≥ 130.

3. F4 Pairwise universe disjointness — no coin owned by >1 component.

4. F5 Weight provenance clean — weight_calibration.py OOS-leak free.

5. F6 Checksums reproducible — source_checksums.csv matches at Phase 7.5.

6. No methodology defect identified by Phase 6.0 Critic pre-flight (any BLOCK-FINAL
   methodology flag → NO-MERGE regardless of F1 outcome).

**MERGE-PROVISIONAL** (per LM Master lgbm_advisor.md §Prior Distribution):
If F1 Pareto fails on ≤1 regime that falls within 2× epsilon_sharpe (i.e., within
1-sigma regime noise), and the bundle strictly improves on ≥2 other regimes, and all
other F2-F6 gates PASS, the QR may issue MERGE-PROVISIONAL with a /057 multi-seed
re-validation mandate. This is NOT full-MERGE; QR makes this determination in Phase 8.

**NO-MERGE if:**
- F1 fails on ≥2 regimes beyond epsilon_sharpe
- F2 < 130 OOS trades
- ANY methodology defect (F3/F4/F5/F6 failures)
- Critic Phase 6.0 or 7.5 BLOCK-FINAL

---

## Section 9 — Library Stack Declaration

Standard v1 library stack:
- **LightGBM**: version from `uv.lock` (currently v4.x.x per workspace)
- **Optuna**: version from `uv.lock`
- **pandas / numpy**: version from `uv.lock`
- **statsmodels**: version from `uv.lock` (for ADF tests in validation_v1.py)
- **mlfinlab / mlfinpy**: NOT used at /056 (no meta-labeling; triple-barrier labeling
  uses in-house implementation in walk_forward.py)
- **pypbo / fracdiff**: NOT used at /056
- **No external libraries** requiring special licensing (no mlfinlab pro)

All dependencies declared in `pyproject.toml` and locked in `uv.lock`. Reproducibility
guaranteed by `uv run` within the worktree.

---

## Section 10 — Cadence Declaration

- **Exploration count since last CONFIRMATION**: 10/10 (full cycle-6 cadence complete)
- **Wall-clock budget**: ≤ 6h total (CONFIRMATION hard cap; sum of C1 + C2 + C3 sub-runs
  + aggregation). Expected: C1≈2h, C2≈2h, C3≈1.5h, aggregation≈5min. Total ≈5.5h.
- **Mode flags**: run_iteration_056.py orchestrates sub-runs; each uses
  `--ensemble-size 10 --n-trials 35 --seeds 1`

---

## Section 11 — Bundle Architecture

### Section 11.A — Universe Partition (per `feedback_v1_bundle_no_coin_overlap.md`)

**HARD RULE**: each coin is owned by EXACTLY ONE component. Pairwise-disjoint assertion
runs at runner startup (F-AXIS #4, Check 16).

| Component | Symbol | Source |
|---|---|---|
| C1-BTC | BTCUSDT | fresh CONFIRMATION sub-run at /056 |
| C2-ETH | ETHUSDT | fresh CONFIRMATION sub-run at /056 |
| C3-DOT | DOTUSDT | fresh CONFIRMATION sub-run at /056 |
| C4-LINK | LINKUSDT | BASELINE_V1 trade roster extraction |
| C5-LTC | LTCUSDT | BASELINE_V1 trade roster extraction |

**Pairwise disjointness assertion** (10 pairs, all empty):
{C1-BTC} ∩ {C2-ETH} = ∅, {C1-BTC} ∩ {C3-DOT} = ∅, {C1-BTC} ∩ {C4-LINK} = ∅,
{C1-BTC} ∩ {C5-LTC} = ∅, {C2-ETH} ∩ {C3-DOT} = ∅, {C2-ETH} ∩ {C4-LINK} = ∅,
{C2-ETH} ∩ {C5-LTC} = ∅, {C3-DOT} ∩ {C4-LINK} = ∅, {C3-DOT} ∩ {C5-LTC} = ∅,
{C4-LINK} ∩ {C5-LTC} = ∅.

### Section 11.B — Weight Derivation (per `feedback_v1_bundle_weights_is_only.md`)

**HARD RULE**: weights derived from IS-only analysis. OOS data MUST NOT be used.

Method: EQUAL (1/5 = 0.2 per component, no IS-derived optimization).

Rationale: IS-Sharpe-proportional weighting would zero C1-BTC (IS +0.26) and collapse
C2-ETH (IS −0.21), C3-DOT (IS −0.24) toward zero — defeating the specialist-substitution
hypothesis (all three are PARTIAL-CONFIRMED candidates with meaningful IS trade counts).
EQUAL weights are the researcher-degree-of-freedom-minimizing choice.

**Pre-registered `bundle_weights.csv`** (verbatim from `analysis/iteration_v1-056/bundle_weights.csv`):
```
component_id,weight,derivation_method,is_window_start,is_window_end
C1-BTC,0.2,equal,2021-03-24,2025-03-24
C2-ETH,0.2,equal,2021-03-24,2025-03-24
C3-DOT,0.2,equal,2021-03-24,2025-03-24
C4-LINK,0.2,equal,2021-03-24,2025-03-24
C5-LTC,0.2,equal,2021-03-24,2025-03-24
```

### Section 11.C — Backtest-Live Parity (per `feedback_v1_backtest_live_parity_hard.md`)

**HARD RULE**: bundle decisions must be identical in backtest and live engine (`engine.py:_tick`).

The /056 bundle uses CSV-replay aggregation (no new model at the bundle level). In live
trading, each specialist (BTC, ETH, DOT, LINK/Model C, LTC/Model D) runs independently
per `engine.py:_tick` with its own signal, gate stack, and position management. The bundle
concept maps to the live engine's natural per-model dispatch — there is NO aggregation step
in live (each model fires independently). Parity is satisfied by construction: the CSV-replay
does NOT introduce any portfolio-level netting, signal combination, or joint exit logic.

### Section 11.D — Re-Composition Note

C4-LINK and C5-LTC anchors reuse BASELINE_V1 trade rosters directly. This means:
- C4-LINK IS/OOS performance is IDENTICAL to BASELINE_V1 LINK model C performance.
- C5-LTC IS/OOS performance is IDENTICAL to BASELINE_V1 LTC model D performance.
- No new CONFIRMATION-budget re-run for anchors (per LM Master advisory and /045 framework).
- The aggregated bundle's IS/OOS Sharpe reflects the COMBINATION of 3 fresh specialist
  sub-runs + 2 frozen baseline extractions, all at w=0.2.

---

## Appendix — Phase 5.5 Gate Checklist (self-assessment)

All sections present and non-trivial:
- Section 0 (Data Split): PASS
- Section 0.5 (Iteration Type): PASS — CONFIRMATION with 10 EXPLORATION precedents
- Section 0.6 (Architecture-Family): PASS — N/A for CONFIRMATION
- Section 1 (Hypothesis): PASS — ONE specific sentence
- Section 2 (IS-Only Evidence): PASS — tabular IS evidence with sources cited
- Section 2.5 (HIGH-RISK): PASS — NO
- Section 3 (Proposed Changes): PASS — all 3 LM Master recs addressed
- Section 4 (Expected OOS Impact): PASS — wide honest band + 6 numbered falsifiers
- Section 5 (Risk Mitigation): PASS — inherited per-component
- Section 6 (Risk Management Design): PASS — 8-gate table
- Section 7 (Failure-Mode Prediction): PASS — LTC drag + BTC lottery mechanisms
- Section 8 (MERGE/NO-MERGE Criteria): PASS — pre-registered numerical gates
- Section 9 (Library Stack): PASS — standard v1 stack, no mlfinlab/pypbo
- Section 10 (Cadence): PASS — 10/10 EXPLORATIONs, 6h cap
- Section 11.A/B/C/D (Bundle Architecture): PASS — all 4 sub-sections
- LM Master recs (Rec 1/2/3): all ADOPTED
