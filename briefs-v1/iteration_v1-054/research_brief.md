# Research Brief — iter-v1/054

## Section 0.0 — Banner

- **Iteration**: iter-v1/054
- **Track**: v1 (refactored, cycle-6 EXPLORATION 9/10)
- **Branch**: `iteration-v1/054`
- **Date**: 2026-06-01
- **Type**: `EXPLORATION` (feature-pruning sub-axis; impulse-drop attribution test)
- **Axis**: DROP `btc_funding_rate_8h_impulse` from V1_FEATURE_COLUMNS_PRUNED (48 → 47 cols);
  KEEP `btc_funding_spread_30_90`. Tests whether spread-alone delivers ≥ 95% of the /052
  single-seed IS lift (+0.1609). Cohort: BTCUSDT only (unchanged from /052-/053).
- **Mode**: EXPLORATION budget: n_trials=18, --seeds 1 (single-seed=42), ENSEMBLE_SIZE=3.
  Wall-clock cap: ≤ 2h (EXPLORATION hard cap per v1 cadence discipline).
- **LightGBM Master advisory**: `briefs-v1/iteration_v1-054/lgbm_advisor.md` (Phase 4.5).
- **Triggering mandate**: /053 PARTIAL-CONFIRMED closes at mean IS Δ +0.8102 in the PARTIAL
  band [+0.30, +0.85), with `btc_funding_rate_8h_impulse` rank > 30 in 3/3 seeds (INERT
  multi-seed confirmed). /053 LM Master Rec 1 conditional FIRES: PARTIAL-CONFIRMED verdict
  triggers the impulse-drop revaluation at /054. Mandatory, not discretionary.

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
SUBTYPE: FEATURE-PRUNING (impulse-drop attribution test; no new axis)
```

FEATURE-PRUNING sub-type: removes one INERT feature (`btc_funding_rate_8h_impulse`) from
V1_FEATURE_COLUMNS_PRUNED. No new feature, no new gate, no architecture change. Single-seed=42
EXPLORATION budget (n_trials=18, ENSEMBLE_SIZE=3). Wall-clock cap ≤ 2h. Cycle-6 EXPLORATION
slot 9/10.

---

## Section 0.6 — Architecture-Family Justification

- **Axis family**: `feature-family` (feature-pruning sub-axis; established at iter-v1/040 as
  the DROP-INERT mechanism; same family as the ADD axis — both manipulate V1_FEATURE_COLUMNS_PRUNED).
- **Prior 5 EXPLORATION families**:
  - iter-v1/049: feature-family (long_short_zscore_30 ADD) — EXPLORATION-NEGATIVE
  - iter-v1/050: feature-family + risk-primitive (DOT specialist ADD) — PROMISING-PARTIAL
  - iter-v1/051: validation (DOT multi-seed re-validation) — PROMISING-PARTIAL-CONFIRMED
  - iter-v1/052: feature-family (BTC specialist; impulse + spread ADD) — PROMISING-SPECIALIST-CANDIDATE
  - iter-v1/053: validation (BTC multi-seed re-validation) — PARTIAL-CONFIRMED
- **Rotation status**: **VALID** — prior 5 include feature-family × 2, feature-family+risk-primitive × 1,
  validation × 2. Not all same family. Axis Rotation Discipline constraint NOT triggered.

---

## Section 1 — Hypothesis

Dropping `btc_funding_rate_8h_impulse` from V1_FEATURE_COLUMNS_PRUNED (48 → 47 cols) while
retaining `btc_funding_spread_30_90` will produce a single-seed=42 IS Sharpe ≥ +0.16 (within
±0.05 of /052's both-feature single-seed IS Sharpe), confirming that impulse contributes
0-5% genuine signal at the 8h BTC specialist cadence and enabling permanent impulse removal
from the BTC specialist feature stack.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 /053 Multi-Seed Attribution Summary (pre-registered baseline)

From `reports-v1/iteration_v1-053/` (IS data only; committed):

| Metric | seed=42 (offset=0) | seed_offset3 | seed_offset6 | Mean |
|---|---:|---:|---:|---:|
| IS Sharpe | +0.1609 | -0.1467 | -0.1336 | -0.0398 |
| IS trades | ~133 | ~137 | ~140 | 136.7 |
| Spread rank (4-10 expected) | 4 | ~4-10 | ~4-10 | 4-10 |
| Impulse rank (>30 expected) | 38 | >30 | >30 | >30 |

Key finding: `btc_funding_rate_8h_impulse` rank > 30 in ALL 3 seeds. Multi-seed INERT confirmed.
`btc_funding_spread_30_90` rank 4-10 in ALL 3 seeds. Spread IS structurally stable.

### 2.2 Attribution Mechanism: Why Impulse Is Inert at 8h BTC Cadence

`btc_funding_rate_8h_impulse` = diff(funding_rate[t]) / rolling(90).std(diff(funding_rate)[t]).
The impulse captures the shock magnitude relative to recent funding-rate volatility. At the 8h
BTC cadence, funding-rate shocks are very rare events (extreme funding spikes occur 1-3× per
month at BTC; the 90-bar rolling std normalizer smooths the denominator). The resulting signal
fires fewer than 5-10% of bars above the ±2σ detection threshold, producing sparse on/off
signal at 8h cadence — LightGBM trees at depth 3-5 with n_trials=18 cannot productively route
this sparse signal class. This is structurally analogous to the v3 `cross_asset_ohlcv` INERT
pattern: low base-rate signals that fire rarely have insufficient training examples per
walk-forward cell to exceed the NaN-to-signal threshold at n_trials=18.

Evidence from /052-/053:
- Impulse IS importance: rank 38/48 (single-seed=42), >30/48 (offset=3), >30/48 (offset=6).
- Impulse gain: consistently < 2% of total gain allocation across 3 seeds (vs spread 10-15%).
- Per LM Master /054 Phase 4.5 Rec 1: dropping one INERT rank-30+ feature from 48 → 47 cols
  should NOT materially change IS Sharpe at n_trials=18 with colsample_bytree in [0.5, 1.0].

### 2.3 Committed Analysis Script

**Analysis script**: `analysis/iteration_v1-054/attribution_impulse_drop.py` (to be committed
alongside this brief before Phase 6.0 pre-flight).

The script reads:
- `reports-v1/iteration_v1-053/seed_42/in_sample/feature_importance.csv`
- `reports-v1/iteration_v1-052/in_sample/feature_importance.csv`

And produces:
- Impulse importance rank per seed at /053 (confirms >30/48 across all 3 seeds)
- Spread importance rank per seed at /053 (confirms 4-10/48 across all 3 seeds)
- Cumulative gain for impulse across /052 and /053 seed=42 (expected < 2%)
- Predicted post-drop spread rank at /054 (expected 3-7/47 per LM Master Rec 3)

---

## Section 2.5 — HIGH-RISK Axis Declaration

```
RISK_CLASS: NORMAL-RISK
```

Feature-pruning (DROP one INERT feature) does NOT change Optuna's training-objective domain.
The loss surface evaluated at each Optuna trial is the SAME function (Sharpe of IS returns)
evaluated on a 47-col feature subset vs a 48-col feature subset. Removing one rank-38+ INERT
feature is a monotone-negligible change to the feature space.

Precedent: iter-v1/040 dropped `basis_zscore_30` (3-consecutive INERT) from 44 → 44 (SWAP).
This drop was classified NORMAL-RISK at Phase 5.5. /054 is a pure DROP (no simultaneous ADD),
making it even simpler.

HIGH-RISK pre-commit binding mitigation: NOT triggered (NORMAL-RISK).

---

## Section 3 — Proposed Changes

### 3.1 Feature Changes (PRIMARY CHANGE)

**DROP**: `btc_funding_rate_8h_impulse` from `V1_FEATURE_COLUMNS_PRUNED` (48 → 47 cols).
**KEEP**: `btc_funding_spread_30_90` (rank 4-10 STABLE multi-seed; primary IS contributor).

Implementation in `src/crypto_trade/features_v1/__init__.py`:
- Remove `"btc_funding_rate_8h_impulse"` from the `V1_FEATURE_COLUMNS_PRUNED` tuple.
- Update the assert from `len(...) == 48` to `len(...) == 47`.
- Update the comment block to document the /054 DROP.

**Do NOT remove** `compute_btc_funding_rate_8h_impulse` from `funding_v1.py`. The feature
computation code is preserved for the IMPULSE-DROP-DEGRADES restore path at /055. The parquet
generated by `add_funding_v1_extended_features` will still contain the `btc_funding_rate_8h_impulse`
column (the runner simply does not pass it to LightGBM's `feature_columns` argument).

Both-or-neither rule status after /054:
- IMPULSE-DROP-CONFIRMED (spread IS ≥ +0.16): impulse permanently removed; spread stands alone.
- IMPULSE-DROP-MARGINAL (IS ∈ [0, +0.16)): retain spread; document for /055 CONFIRMATION.
- IMPULSE-DROP-DEGRADES (IS < 0): restore impulse; both features re-enter /055 at 48-col stack.

### 3.2 Seed Configuration (UNCHANGED from single-seed=42 template)

```
--seeds 1
ENSEMBLE_SIZE = 3
_OUTER_SEED_OFFSETS = default (no patch needed for single-seed runs)
```

Single-seed=42 (inner pool [42, 123, 456]) — identical to /052 seed configuration. This
enables bit-exact comparison of spread-only IS Sharpe vs /052's both-feature IS Sharpe +0.1609.

### 3.3 Architecture (UNCHANGED from /052-/053)

Model `A_BTC_specialist`:
- Symbols: (`BTCUSDT`,) — BTC-only specialist cohort
- R1: OFF (same as baseline Model A — no R1 on BTC per IS analysis)
- R2: OFF (same as baseline Model A — no R2 on BTC)
- R3: ON (same as baseline Model A — Mahalanobis OOD gate, cutoff=0.70)
- atr_tp=3.5, atr_sl=1.75 (UNCHANGED from /052-/053)
- n_trials=18, ENSEMBLE_SIZE=3 (EXPLORATION standard)

### 3.4 LM Master Phase 4.5 Responses (from lgbm_advisor.md)

| Rec | Recommendation | Disposition |
|---|---|---|
| Rec 1 | Primary falsifier: spread IS ≥ +0.16 (≈ /052 IS within ±0.05) = IMPULSE-DROP-CONFIRMED | **ADOPTED** — Brief Section 4 F-AXIS #1 pre-registers these exact thresholds |
| Rec 2 | Trade-rate floor: IS ≥ 50 trades mandatory; anomaly note if IS < 100 | **ADOPTED** — Brief Section 4 F-AXIS #2 pre-registers hard floor + anomaly threshold |
| Rec 3 | Spread importance rank should LIFT (or hold) to 3-7/47 after impulse removal | **ADOPTED** — Brief Section 4 F-AXIS #3 records post-drop spread rank as informational |
| Flag A | Preserve `compute_btc_funding_rate_8h_impulse` in funding_v1.py (don't delete code) | **ADOPTED** — Section 3.1 explicitly states code is NOT removed; test verifies |
| Flag B | Parquet regen required (BTCUSDT only; 47-col subset validation) | **ADOPTED** — Section 3.1 notes parquet regen step; engineering report documents it |

### 3.5 Dispatch Architecture

Add `V1_ITER054_UNIVERSE = ("BTCUSDT",)` to `src/crypto_trade/features_v1/__init__.py`.
Add dispatch block `elif iteration_label == "v1-054"` to `run_baseline_v1.py`.
Runner `run_iteration_054.py` injects:
```
sys.argv = ["run_baseline_v1.py", "--exploration", "--iteration", "54",
            "--n-trials", "18", "--seeds", "1", "--ensemble-size", "3",
            "--pruned-features", "--symbols", "BTCUSDT"]
```
No `_OUTER_SEED_OFFSETS` patch needed (single-seed default).

---

## Section 4 — Expected OOS Impact and F-AXIS Falsifiers

### F-AXIS #1 — Spread-Only IS Sharpe vs /052 Anchor (PRIMARY)

Reference point: /052 single-seed=42 IS Sharpe = +0.1609 (both features: impulse + spread).
New baseline for comparison: spread-only IS Sharpe at seed=42.

| Verdict | Condition | Label | Action |
|---|---|---|---|
| IMPULSE-DROP-CONFIRMED | Spread IS ≥ +0.16 (within ±0.05 of /052) | Impulse contributes 0-5% | Permanently remove impulse; BTC → 47-col stack |
| IMPULSE-DROP-MARGINAL | Spread IS ∈ [0, +0.16) | Both features partial | Retain spread; document for /055 CONFIRMATION |
| IMPULSE-DROP-DEGRADES | Spread IS < 0 | Impulse was load-bearing | Restore impulse; both features → /055 at 48 cols |

**BTC baseline IS Sharpe anchor**: −0.85 (established at /052).
**Falsifier (hard)**:
- If spread-only IS Sharpe < 0 (IMPULSE-DROP-DEGRADES), hypothesis rejected — impulse had genuine
  contribution to IS lift at seed=42. Restore impulse; document interaction effect.
- If spread-only IS Sharpe ≥ +0.16, hypothesis confirmed — impulse is genuinely redundant;
  impulse is permanently removed from V1_FEATURE_COLUMNS_PRUNED.

**Predicted OOS impact** (conditional on IMPULSE-DROP-CONFIRMED): if IS confirms spread-alone
delivers the /052 IS lift, the /055 CONFIRMATION will run with 47-col stack. OOS impact at
/055 is not predictable from this single-seed EXPLORATION — OOS variance at single-seed is
12× IS variance for BTC specialist (per /053 observation). OOS at /054 is informational only.

### F-AXIS #2 — Trade-Rate Floor (MANDATORY)

IS trades ≥ 50: PASS (hard floor; must not regress from /052's 133 IS trades).
OOS trades ≥ 10: PASS.
Anomaly note: if IS trades < 100 (25% regression from /052-/053 mean of ~133), log in
engineering report. A large trade-count regression could indicate the impulse was contributing
to entry-gating behavior despite low importance rank.

### F-AXIS #3 — Spread Importance Rank Post-Drop (INFORMATIONAL)

After dropping impulse (47 cols), spread rank expected 3-7/47 (tighter than /052's 4-10/48 range;
LM Master Rec 3 prediction). Record actual rank in engineering report.

If spread rank falls below 15/47 while IS Sharpe is positive: FLAG in engineering report for QR.
This F-AXIS is informational only — does NOT override F-AXIS #1 primary verdict.

---

## Section 5 — Risk Mitigation

### R1, R2, R3 (UNCHANGED from /052-/053)

- R1: OFF for BTC specialist
- R2: OFF for BTC specialist
- R3: ON, cutoff=0.70 (calibrated on BTC-only IS walk-forward at /052)

R3 fire rate expected: 15-25% per /052 baseline. If fire rate deviates significantly from /052
at seed=42, note in engineering report.

### Feature-Drop Risk (NEW at /054)

Dropping one INERT feature creates a negligible loss-surface perturbation at n_trials=18. The
colsample_bytree position shift (impulse was at index 0; all other features shift down by one)
does NOT change any feature's mathematical content. The LM Master classifies this NORMAL-RISK.

No multi-seed mitigation required (NORMAL-RISK). Single-seed=42 is the EXPLORATION standard.

---

## Section 6 — Risk Management Design (8-Primitive Table)

| Primitive | Status at /054 | IS Fire Rate Prediction | Notes |
|---|---|---|---|
| Vol-adjusted sizing | R2 OFF for BTC | 0% (R2=OFF) | Unchanged from /052-/053 |
| R1 consecutive-SL cooldown | OFF | 0% | Unchanged from /052-/053 |
| R3 OOD Mahalanobis gate | ON, cutoff=0.70 | 15-25% | Same calibration as /052 seed=42 |
| Z-score OOD | Part of R3 | — | Covered by R3 |
| Drawdown brake | R2 OFF | 0% | Unchanged |
| BTC contagion | N/A (BTC IS the traded symbol) | — | N/A |
| Isolation forest | N/A (not wired in v1) | — | Not in scope |
| Liquidity floor | N/A (not wired in v1) | — | Not in scope |

No gate changes at /054. All gates identical to /052-/053 configuration.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure modes**:

1. **IMPULSE-DROP-MARGINAL (35% prior per LM Master)**: the /052 single-seed=42 IS Sharpe (+0.16)
   was a combined contribution from BOTH features even though impulse ranked 38/48 (INERT-by-
   importance). At n_trials=18 with colsample_bytree sampling, the impulse may have contributed
   a small but non-zero marginal IS signal that drops the Sharpe to the [0, +0.16) range.
   Diagnostic: spread IS ∈ [0, +0.16); trade-rate stable ≥ 100. Gate: F-AXIS #1 verdict
   IMPULSE-DROP-MARGINAL; both features documented for /055 CONFIRMATION.

2. **IMPULSE-DROP-DEGRADES (15% prior per LM Master)**: at seed=42 specifically, the impulse
   feature and spread feature have a subtle interaction effect at depth 3-5 LightGBM trees.
   Removing impulse changes the IS PnL distribution in a way that drops IS Sharpe below 0
   even though impulse had negligible individual importance. This is the "interaction trap"
   where two features jointly create a decision region that neither creates alone.
   Diagnostic: spread IS < 0. Gate: F-AXIS #1 falsifier triggers IMPULSE-DROP-DEGRADES; restore
   impulse; both features enter /055 at 48-col stack.

3. **IMPULSE-DROP-CONFIRMED-BUT-OOS-NEGATIVE (informational)**: spread IS ≥ +0.16 (F-AXIS #1
   PASS) but OOS at single-seed=42 still strongly negative (analogous to /052's OOS -1.38). This
   pattern would be EXPECTED given the 12× IS/OOS variance ratio for BTC specialist at
   EXPLORATION budget (/053 observation). Gate: none (OOS informational per project discipline).
   QR must note in Phase 8 diary that /055 CONFIRMATION is the resolution for OOS variance.

4. **SPREAD RANK REGRESSION (informational)**: spread drops from rank 4/48 to rank 10+/47 after
   impulse removal. This would indicate the colsample_bytree lottery at seed=42 was slightly less
   favorable to spread at 47 cols than at 48 cols. Gate: F-AXIS #3 FLAG if rank > 15/47; does NOT
   override F-AXIS #1 primary verdict.

**Pre-registered against Phase 8 diary**: outcomes will be compared against these 4 failure modes.

---

## Section 8 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

This is an EXPLORATION (FEATURE-PRUNING sub-type). MERGE decision deferred to CONFIRMATION.
/054 closeout issues a CATALOG verdict only:

| Catalog verdict | Condition | Action |
|---|---|---|
| IMPULSE-DROP-CONFIRMED | Spread IS ≥ +0.16 AND IS trades ≥ 50 | Impulse permanently removed; V1_FEATURE_COLUMNS_PRUNED = 47 at /055+ |
| IMPULSE-DROP-MARGINAL | Spread IS ∈ [0, +0.16) AND IS trades ≥ 50 | Retain both; /055 CONFIRMATION with 48-col stack |
| IMPULSE-DROP-DEGRADES | Spread IS < 0 OR IS trades < 50 | Restore impulse; /055 CONFIRMATION with 48-col stack |

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
| `fracdiff` | Not required at /054 | Fractional differentiation | N/A |

Same library stack as /052-/053. Section 9 satisfies Phase 5.5 gate requirement.

---

## Section 10 — Dispatch Architecture

### 10.1 Universe

```python
V1_ITER054_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
```

Defined INDEPENDENTLY from `V1_ITER052_UNIVERSE` and `V1_ITER053_UNIVERSE` in
`src/crypto_trade/features_v1/__init__.py`.

### 10.2 Feature Stack

`V1_FEATURE_COLUMNS_PRUNED` = 47 cols (DROP `btc_funding_rate_8h_impulse` from 48-col set):
- `btc_funding_rate_8h_impulse` — **REMOVED** (rank >30/48 in 3/3 seeds at /053; INERT confirmed)
- `btc_funding_spread_30_90` — **RETAINED** (rank 4-10/48 in 3/3 seeds at /053; STABLE confirmed)

All other 46 features unchanged.

Parquet regen required: BTCUSDT only.
```
uv run crypto-trade features --symbols BTCUSDT --interval 8h --track v1 --format parquet --workers 4
```

### 10.3 Runner

`run_iteration_054.py` — thin dispatch wrapper:
- Hardwires: `--exploration --iteration 54 --n-trials 18 --seeds 1 --ensemble-size 3 --pruned-features --symbols BTCUSDT`
- Features-base-hash: new 47-col hash (differs from /052-/053 48-col hash).

### 10.4 Model Architecture (UNCHANGED from /052-/053)

Model `A_BTC_specialist` (BTC-only head):
- R1=OFF, R2=OFF, R3=ON (same as baseline Model A for BTC)
- atr_tp=3.5, atr_sl=1.75 (unchanged)
- feature_columns=list(V1_FEATURE_COLUMNS_PRUNED) [47 cols]
- ENSEMBLE_SIZE=3, n_trials=18
