# Research Brief — iter-v1/053

## Section 0.0 — Banner

- **Iteration**: iter-v1/053
- **Track**: v1 (refactored, cycle-6 EXPLORATION 8/10)
- **Branch**: `iteration-v1/053`
- **Date**: 2026-06-01
- **Type**: `EXPLORATION` (multi-seed re-validation sub-type; no new axis)
- **Axis**: VALIDATION — multi-seed re-validation of iter-v1/052 BTC specialist
  (`btc_funding_rate_8h_impulse` + `btc_funding_spread_30_90`; V1_FEATURE_COLUMNS_PRUNED = 48).
  Mirror of /050 → /051 DOT multi-seed pattern applied to BTC.
- **Cohort**: (`BTCUSDT`,) — BTC-only, unchanged from /052.
- **Mode**: EXPLORATION budget: n_trials=18, --seeds 3 (offsets 0/3/6), ENSEMBLE_SIZE=3.
  Wall-clock cap: ≤ 2h (EXPLORATION hard cap per v1 cadence discipline).
- **LightGBM Master advisory**: `briefs-v1/iteration_v1-053/lgbm_advisor.md` (Phase 4.5).
- **Triggering mandate**: LM Master Rec 3 from `/052` Phase 4.5 FIRES on PROMISING-SPECIALIST-
  CANDIDATE closeout. /053 is mandatory, not discretionary.

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
TYPE: EXPLORATION
SUBTYPE: VALIDATION (multi-seed re-validation)
```

VALIDATION sub-type: no new feature, no new gate, no architecture change. Single-axis variation
is seed selection (3 disjoint outer seeds). Wall-clock budget ≤ 2h per outer seed (EXPLORATION
hard cap). Cycle-6 EXPLORATION slot 8/10. No CONFIRMATION can launch until ≥10 EXPLORATION
precedents accumulated since last CONFIRMATION.

---

## Section 0.6 — Architecture-Family Justification

- **Axis family**: `validation` (multi-seed re-validation sub-type; established at /051 as
  canonical cycle-6 validation mechanism; identical dispatch pattern to /050→/051 DOT).
- **Prior 5 EXPLORATION families**:
  - iter-v1/048: feature-family (trade_count_zscore_30) — NEG-CLEAN-PRE-EDA
  - iter-v1/049: feature-family (long_short_zscore_30) — EXPLORATION-NEGATIVE
  - iter-v1/050: feature-family + risk-primitive (DOT regime specialist) — PROMISING-PARTIAL
  - iter-v1/051: validation (DOT multi-seed re-validation) — PROMISING-PARTIAL-CONFIRMED
  - iter-v1/052: feature-family (BTC specialist, funding transforms) — PROMISING-SPECIALIST-CANDIDATE
- **Rotation status**: **VALID** — prior 5 include feature-family × 3, feature-family+risk-primitive × 1,
  validation × 1. Not all same family. Axis Rotation Discipline constraint NOT triggered.

---

## Section 1 — Hypothesis

Running iter-v1/052's BTC specialist configuration (same features, same model config) at 3
disjoint outer seeds will produce a multi-seed mean IS Sharpe Δ ≥ +0.85 vs the BTC baseline
of −0.85, confirming that the /052 IS Sharpe flip (+0.1609; Δ +1.0109) was signal-mediated
by `btc_funding_spread_30_90` (not a single-seed-42 favorable basin draw) and qualifying
the BTC specialist for the /055 CONFIRMATION-bundle roster.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 /052 Single-Seed IS Anchor (pre-registered starting point)

From `reports-v1/iteration_v1-052/in_sample/comparison.csv` (IS data only; committed):

| Metric | /052 single-seed=42 BTC IS | BTC baseline IS |
|---|---:|---:|
| IS monthly Sharpe | +0.1609 | −0.85 (estimated) |
| IS Sharpe Δ | **+1.0109** | — |
| IS trades | 133 | 113 |
| IS win rate | 39.8% | 33.6% |
| IS MaxDD | 23.37% | — |
| IS net PnL % | +5.83% | −37.28% |

### 2.2 Feature Attribution from /052 (IS feature_importance.csv)

| Feature | /052 IS Importance Rank | Classification |
|---|---|---|
| `btc_funding_spread_30_90` | **4/48** | STRONGLY LEARNED (3× gain vs parent features at ranks 17+26) |
| `btc_funding_rate_8h_impulse` | **38/48** | INERT-BY-IMPORTANCE at n_trials=18 seed=42 |

The IS lift at /052 is dominated by `btc_funding_spread_30_90` (term-structure slope; Category-2
algebraic composition z30−z90). Multi-seed tests whether this rank-4 position is seed-42-specific
or structurally stable across colsample_bytree variation at different inner-ensemble pools.

### 2.3 DOT Multi-Seed Precedent (/051)

The /050→/051 DOT pattern is the canonical multi-seed template for /053:
- /050 single-seed=42: DOT IS Δ +1.1162 (PROMISING-PARTIAL)
- /051 multi-seed mean: DOT IS mean Δ +0.9945 (regression of −0.12; PARTIAL-CONFIRMED)
- /051 basin-lottery spread: max-min = 0.5690 (< 1.0 threshold; PASS)

Expected /053 regression: /052 Δ +1.0109 → /053 mean Δ ~+0.88–+0.92 (similar regression
magnitude, ±0.12). This is within SPECIALIST-CONFIRMED band (≥ +0.85). Wide uncertainty band
because the /052 driver is more concentrated (one rank-4 feature vs DOT's rank-7-to-9 stable
feature).

### 2.4 Mechanism Analysis (IS-only)

`btc_funding_spread_30_90` = `funding_rate_zscore_30` − `funding_rate_zscore_90` is a Category-2
algebraic-sister composed feature. Its rank-4 importance at /052 reflects the PROMISING-FEATURE-
MECHANICAL pattern (per `feedback_v3_promising_feature_mechanical.md` precedent): trees can
exploit the spread with a single split vs two parent splits. This algebraic efficiency is
SEED-INVARIANT — the split-access optimization should persist regardless of which inner-ensemble
seeds are drawn. Therefore, multi-seed should confirm the rank-4 position in 2/3 seeds minimum.

---

## Section 2.5 — HIGH-RISK Axis Declaration

```
RISK_CLASS: NORMAL-RISK
```

VALIDATION sub-axis (seed variation only). No feature changes. No labeling changes. No model
architecture changes. No risk gate changes. Seed variation does NOT change Optuna's training-
objective domain. Per /051 precedent (same classification), VALIDATION = NORMAL-RISK.

HIGH-RISK pre-commit binding mitigation: NOT triggered (NORMAL-RISK).

---

## Section 3 — Proposed Changes

### 3.1 Feature Changes

**NONE.** V1_FEATURE_COLUMNS_PRUNED unchanged at 48 cols. Both features retained from /052:
- `btc_funding_rate_8h_impulse` (rank 38/48 at /052 — INERT, retained per both-or-neither rule)
- `btc_funding_spread_30_90` (rank 4/48 at /052 — STRONGLY LEARNED)

Both-or-neither revert rule (from LM Master Rec 1 at /052) REMAINS BINDING at /053:
- If /053 closes NEG-CLEAN-MULTI-SEED (mean IS Δ < +0.30): REVERT BOTH features.
- If /053 closes SPECIALIST-CONFIRMED or PARTIAL-CONFIRMED: RETAIN BOTH features.
- No partial revert (impulse cannot be dropped while spread is retained) until CONFIRMATION.

### 3.2 Seed Configuration (CHANGES vs /052)

Multi-seed re-validation at 3 disjoint outer seeds:

```
--seeds 3
_OUTER_SEED_OFFSETS = (0, 3, 6)   ← scope-limited monkey-patch in run_iteration_053.py
ENSEMBLE_SIZE = 3                  ← UNCHANGED from /052 (inner ensemble size)
```

Outer seed windows (fully disjoint within ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001, 2002,
3003, 4004, 5005, 6006]):
- offset=0: inner pool [42, 123, 456] — reproduces /052 single-seed result bit-exactly
- offset=3: inner pool [789, 1001, 2002] — first new seed draw
- offset=6: inner pool [3003, 4004, 5005] — second new seed draw

Constraint: offset + ENSEMBLE_SIZE ≤ 10 (run_baseline_v1.py:7382). 0+3=3 ≤ 10 ✓;
3+3=6 ≤ 10 ✓; 6+3=9 ≤ 10 ✓.

### 3.3 Architecture (UNCHANGED from /052)

Model `A_BTC_specialist`:
- Symbols: (`BTCUSDT`,) — BTC-only specialist cohort
- R1: OFF (same as baseline Model A — no R1 on BTC per IS analysis)
- R2: OFF (same as baseline Model A — no R2 on BTC)
- R3: ON (same as baseline Model A — Mahalanobis OOD gate, cutoff=0.70)
- atr_tp=3.5, atr_sl=1.75 (UNCHANGED from /052 and baseline Model A)

### 3.4 LM Master Phase 4.5 Responses (from lgbm_advisor.md)

| Rec | Recommendation | Disposition |
|---|---|---|
| Rec 1 | Keep both-or-neither revert rule; tighten basin-lottery threshold to ≤ 0.5 | **ADOPTED** — Section 3.1 retains both-or-neither; Section 4 F-AXIS #2 pre-registers max-min ≤ 0.5 |
| Rec 2 | Monitor mean IS trade-rate floor ≥ 50; mean OOS ≥ 10 | **ADOPTED** — Section 4 F-AXIS #3 pre-registers mean floor; early-warning at mean < 80 |
| Rec 3 | Monitor spread rank stability across 3 seeds; record per-seed importance | **ADOPTED** — Section 4 F-AXIS #4 records per-seed ranks; engineering report Section required |
| Flag A | /052 OOS −1.38 warning signal | **REGISTERED** — Section 7 failure-mode prediction #4 notes OOS warning |
| Flag B | offset arithmetic must use ENSEMBLE_SIZE=3 exactly | **ADOPTED** — Section 3.2 pins ENSEMBLE_SIZE=3; runner doc verifies arithmetic |
| Flag C | V1_ITER053_UNIVERSE separate from V1_ITER052_UNIVERSE | **ADOPTED** — V1_ITER053_UNIVERSE defined independently in features_v1/__init__.py |

### 3.5 Dispatch Architecture Change

Add `V1_ITER053_UNIVERSE = ("BTCUSDT",)` to `src/crypto_trade/features_v1/__init__.py`.
Add dispatch block `elif iteration_label == "v1-053"` to `run_baseline_v1.py`.
Runner `run_iteration_053.py` injects:
```
sys.argv = ["run_baseline_v1.py", "--exploration", "--iteration", "53",
            "--n-trials", "18", "--seeds", "3", "--ensemble-size", "3",
            "--pruned-features", "--symbols", "BTCUSDT"]
run_baseline_v1._OUTER_SEED_OFFSETS = (0, 3, 6)
```

---

## Section 4 — Expected OOS Impact and F-AXIS Falsifiers

### F-AXIS #1 — Multi-Seed Mean IS Sharpe Delta (PRIMARY)

| Verdict band | Condition | Label |
|---|---|---|
| SPECIALIST-CONFIRMED | Mean IS Δ ≥ +0.85 AND max-min ≤ 0.5 | BTC into /055 roster |
| PARTIAL-CONFIRMED | Mean IS Δ ∈ [+0.30, +0.85) | Consider impulse-drop at /054 |
| NEG-CLEAN-MULTI-SEED | Mean IS Δ < +0.30 | Revert BOTH features |

BTC baseline IS Sharpe anchor: −0.85.
SPECIALIST-CONFIRMED requires mean IS Sharpe ≥ 0.00 (absolute flip-positive mean).

**Predicted OOS impact** (conditional on SPECIALIST-CONFIRMED): if multi-seed confirms
BTC specialist IS Sharpe flip, expected OOS lift is moderate (+0.10–+0.40 monthly Sharpe
vs baseline +0.6637). Wide CI — BTC OOS is already positive in baseline (+33.17% net OOS
PnL; 35 OOS trades). The specialist head may improve OOS BTC PnL distribution at the
CONFIRMATION stage.

**Falsifier** (hard boundary): if multi-seed mean IS Δ < +0.30 (mean IS Sharpe < −0.55),
the hypothesis that the /052 IS flip was signal-mediated is **rejected**; both features
reverted at closeout commit.

### F-AXIS #2 — Basin-Lottery Stability (TIGHTENED from /051)

Max-min spread of per-seed IS Sharpe across 3 outer seeds ≤ 0.5: PASS (tightened from /051's
1.0 threshold per LM Master Rec 1 — concentrated single-driver `btc_funding_spread_30_90`
justifies tighter bound).
Max-min > 0.5: FLAG (note in engineering report; does NOT block SPECIALIST-CONFIRMED verdict
unless max-min indicates genuine lottery-dependence, i.e., one seed strongly positive AND
others strongly negative).

BASIN-LOTTERY declared if: max-min > 0.5 AND any seed IS Sharpe < −0.30 while another > +0.20.
This pattern indicates seed-42 favorable basin specifically, NOT broad signal.

### F-AXIS #3 — Trade-Rate Mean Floor (MANDATORY)

Mean IS trades across 3 seeds ≥ 50: PASS. Mean IS trades < 50: FAIL (regardless of IS Δ).
Mean OOS trades across 3 seeds ≥ 10: PASS. Mean OOS trades < 10: FAIL.
Early-warning: mean IS trades < 80 triggers a note in engineering report.

### F-AXIS #4 — Feature Attribution Stability (INFORMATIONAL)

Per-seed importance rank of `btc_funding_spread_30_90` and `btc_funding_rate_8h_impulse`
recorded in engineering report. Expected:
- `btc_funding_spread_30_90` top-15 in ≥ 2 of 3 seeds: genuine learned signal confirmed
- `btc_funding_rate_8h_impulse` rank > 24 in ≥ 2 of 3 seeds: INERT-by-importance confirmed

If `btc_funding_spread_30_90` falls below rank 20 in ≥ 2 seeds while IS Δ is positive:
FLAG for QR attention (lift may not be feature-mediated at non-42 seeds).

### F-AXIS #5 — Seed=42 Sanity (MANDATORY)

Outer seed offset=0 must reproduce /052 IS Sharpe bit-exactly (+0.1609) OR within ±0.0005
(float reproducibility margin). Divergence indicates offset/seed injection bug. If sanity
check fails, ABORT and escalate to QR.

---

## Section 5 — Risk Mitigation

### R1, R2, R3 (UNCHANGED from /052)

Same as Section 5 in research_brief for /052:
- R1: OFF for BTC specialist
- R2: OFF for BTC specialist
- R3: ON, cutoff=0.70 (calibrated on BTC-only ~133 IS rows per walk-forward cell at /052)

R3 fire rate early-warning from /052: 15–25% expected. If mean R3 fire rate across seeds
deviates substantially from /052's observed rate, note in engineering report.

### Multi-Seed Risk (NEW at /053)

Seed variation does not change the training-objective domain but does introduce inner-
ensemble variance. With ENSEMBLE_SIZE=3, each outer seed run produces 3 LightGBM models
per (symbol, month) cell. The multi-seed mean aggregates 3 × 3 = 9 models per cell
(one dimension of the ENSEMBLE_SEEDS roster per outer seed × 3 inner models).

---

## Section 6 — Risk Management Design (8-Primitive Table)

| Primitive | Status at /053 | IS Fire Rate Prediction | Notes |
|---|---|---|---|
| Vol-adjusted sizing | R2 OFF for BTC | 0% (R2=OFF) | Unchanged from /052 |
| R1 consecutive-SL cooldown | OFF | 0% | Unchanged from /052 |
| R3 OOD Mahalanobis gate | ON, cutoff=0.70 | 15–25% per seed | Same calibration risk as /052 |
| Z-score OOD | Part of R3 | — | Covered by R3 |
| Drawdown brake | R2 OFF | 0% | Unchanged |
| BTC contagion | N/A (BTC IS the traded symbol) | — | N/A |
| Isolation forest | N/A (not wired in v1) | — | Not in scope |
| Liquidity floor | N/A (not wired in v1) | — | Not in scope |

R3 fire rates at /052 (single-seed=42) must be reproduced at offset=0 as a sanity check.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure modes**:

1. **BASIN-LOTTERY (25% prior)**: the /052 IS Δ +1.0109 was produced by seed=42 inner pool
   [42, 123, 456] which happens to allocate more colsample_bytree coverage to
   `btc_funding_spread_30_90`. At non-42 inner pools, colsample_bytree may exclude the spread
   feature in key walk-forward months, producing dramatically lower IS Δ. Diagnostic: per-seed
   IS Sharpe shows high variance (max-min > 0.5); one seed near-zero or negative while another
   is positive. Gate: F-AXIS #2 (basin-lottery declaration if pattern matches).

2. **NEG-CLEAN-MULTI-SEED (20% prior)**: the rank-4 `btc_funding_spread_30_90` importance
   was a PROMISING-FEATURE-MECHANICAL pattern (algebraic sister) at /052. At 3 outer seeds,
   the algebraic shortcut may not consistently improve IS Sharpe because the split-budget
   allocation at depth-3/4 is already captured by the parent features
   (`funding_rate_zscore_30/90`) in non-42 seed configurations. Diagnostic: mean IS Δ < +0.30.
   Gate: F-AXIS #1 (falsifier triggered; revert both features).

3. **PARTIAL-CONFIRMED (20% prior)**: multi-seed mean IS Δ falls into [+0.30, +0.85) because
   the /052 single-seed=42 was slightly favorable basin (analogous to /051 DOT regression of
   −0.12 from /050's +1.1162 to /051's +0.9945). Gate: F-AXIS #1 (PARTIAL-CONFIRMED verdict;
   impulse-drop considered at /054; spread retained).

4. **/052 OOS Warning Propagates (OOS informational)**: the /052 OOS Sharpe was −1.3833 at
   single-seed=42. Even if multi-seed IS confirms SPECIALIST-CONFIRMED, the OOS dispersion
   at 3 seeds may show 2/3 seeds negative OOS. This is an EXPLORATION-budget OOS-variance
   signature — NOT a verdict gate — but must be documented in Phase 8 diary for the QR's
   /055 CONFIRMATION design decision. Gate: none (informational per project discipline).

**Pre-registered against Phase 8 diary**: verdict will be compared against these 4 failure
modes to assess LM Master prior calibration accuracy.

---

## Section 8 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

This is an EXPLORATION (VALIDATION sub-type). MERGE decision deferred to CONFIRMATION cycle.
/053 closeout issues a CATALOG verdict only:

| Catalog verdict | Condition |
|---|---|
| SPECIALIST-CONFIRMED | Mean IS Δ ≥ +0.85 AND max-min ≤ 0.5 AND mean IS trades ≥ 50 |
| BASIN-LOTTERY | Mean IS Δ ≥ +0.85 BUT max-min > 0.5 AND any seed IS Sharpe < −0.30 |
| PARTIAL-CONFIRMED | Mean IS Δ ∈ [+0.30, +0.85) AND mean IS trades ≥ 50 |
| NEG-CLEAN-MULTI-SEED | Mean IS Δ < +0.30 |
| NEG-INSUFFICIENT-TRADES | Mean IS trades < 50 |

**Both-or-neither revert** (binding):
- SPECIALIST-CONFIRMED or PARTIAL-CONFIRMED → RETAIN both features; update /055 roster
- NEG-CLEAN-MULTI-SEED or BASIN-LOTTERY → REVERT both features at closeout commit

**Seed=42 sanity gate** (mandatory pre-verdict):
- Offset=0 IS Sharpe must reproduce /052 ±0.0005. If not: abort, escalate to QR.

**CONFIRMATION MERGE gates** (deferred to /055 CONFIRMATION brief):
- IS monthly Sharpe > 1.0 AND OOS monthly Sharpe > 1.0
- OOS / IS Sharpe ratio ≥ 0.5
- DSR > 0.95, PBO < 0.40, PSR > 0.95
- OOS trades ≥ 130 total, ≥ 10/month
- 10-seed: mean Sharpe > 0, ≥ 7/10 profitable

---

## Section 9 — Library Stack Declaration

| Library | Version | Role | Fallback |
|---|---|---|---|
| `lightgbm` | ≥ 4.0 (project lock) | Primary model | N/A |
| `optuna` | ≥ 3.0 (project lock) | Hyperparameter search | N/A |
| `statsmodels` | ≥ 0.14 (project lock) | ADF stationarity test | N/A |
| `numpy` | ≥ 1.26 (project lock) | Feature math | N/A |
| `pandas` | ≥ 2.0 (project lock) | DataFrame operations | N/A |
| `mlfinlab` | License-gated (not available) | CPCV, meta-labeling | `validation_v1.py` custom CPCV (MIT) |
| `pypbo` | Not installed | PBO from CPCV | `validation_v1.py` custom PBO formula |
| `fracdiff` | Not required at /053 | Fractional differentiation | N/A |

Same library stack as /052. Section 9 satisfies Phase 5.5 gate requirement.

---

## Section 10 — Dispatch Architecture

### 10.1 Universe

```python
V1_ITER053_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
```

Defined INDEPENDENTLY from `V1_ITER052_UNIVERSE` in `src/crypto_trade/features_v1/__init__.py`
(per LM Master Flag C: separate constant allows independent revert/keep decisions).

### 10.2 Feature Stack

`V1_FEATURE_COLUMNS_PRUNED` = 48 cols (UNCHANGED from /052). Both features RETAINED:
- `btc_funding_rate_8h_impulse` (rank 38/48 at /052; INERT-by-importance; retained per both-or-neither)
- `btc_funding_spread_30_90` (rank 4/48 at /052; STRONGLY LEARNED)

No parquet regeneration required — parquets already contain both features from /052 regen.

### 10.3 Runner

`run_iteration_053.py` — thin dispatch wrapper:
- Hardwires: `--exploration --iteration 53 --n-trials 18 --seeds 3 --ensemble-size 3 --pruned-features --symbols BTCUSDT`
- Monkey-patches: `run_baseline_v1._OUTER_SEED_OFFSETS = (0, 3, 6)` (scope-limited to this module)
- Features-base-hash guard: same hash as /052 (V1_FEATURE_COLUMNS_PRUNED = 48 cols, UNCHANGED)

### 10.4 Multi-Seed Output Structure

```
reports-v1/iteration_v1-053/seed_42/          (offset=0 outer seed)
reports-v1/iteration_v1-053/seed_offset3/     (offset=3 outer seed)
reports-v1/iteration_v1-053/seed_offset6/     (offset=6 outer seed)
reports-v1/iteration_v1-053/comparison_multi_seed.csv  (multi-seed aggregate)
reports-v1/iteration_v1-053/run.log
```

### 10.5 Model Architecture (UNCHANGED from /052)

Model `A_BTC_specialist` (BTC-only head):
- R1=OFF, R2=OFF, R3=ON (same as baseline Model A for BTC)
- atr_tp=3.5, atr_sl=1.75 (unchanged)
- feature_columns=list(V1_FEATURE_COLUMNS_PRUNED) [48 cols]
- ENSEMBLE_SIZE=3, n_trials=18
