# Research Brief — iter-v1/052

## Section 0.0 — Banner

- **Iteration**: iter-v1/052
- **Track**: v1 (refactored, cycle-6 EXPLORATION 7/10)
- **Branch**: `iteration-v1/052`
- **Date**: 2026-06-01
- **Type**: `EXPLORATION` (single-axis; feature-family; BTC-specialist)
- **Axis**: ADD `btc_funding_rate_8h_impulse` + `btc_funding_spread_30_90` to
  `V1_FEATURE_COLUMNS_PRUNED` (46 → 48); BTC-only specialist head replacing pooled Model A for BTC.
- **Cohort**: (`BTCUSDT`,) — single-symbol, BTC-only.
- **Mode**: EXPLORATION budget: n_trials=18, --seeds 1 (single-seed=42), ENSEMBLE_SIZE=3.
  Wall-clock cap: ≤ 2h.
- **LightGBM Master advisory**: `briefs-v1/iteration_v1-052/lgbm_advisor.md` (Phase 4.5).

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
```

Single-axis variation: feature-family (two new funding-rate transform features, BTC-only head).
Wall-clock budget: ≤ 2h (EXPLORATION hard cap per v1 cadence discipline).
Cycle-6 EXPLORATION slot 7/10. No CONFIRMATION can launch until ≥10 EXPLORATION precedents
accumulated since last CONFIRMATION.

---

## Section 0.6 — Architecture-Family Justification

- **Axis family**: `feature-family` (funding-rate derived transforms; non-OHLCV primitive class).
- **Prior 5 EXPLORATION families**:
  - iter-v1/047: feature-family (skew_zscore_21) — NEG-CLEAN-PRE-EDA
  - iter-v1/048: feature-family (trade_count_zscore_30) — NEG-CLEAN-PRE-EDA
  - iter-v1/049: feature-family (long_short_zscore_30) — EXPLORATION-NEGATIVE
  - iter-v1/050: feature-family + risk-primitive (DOT regime specialist) — PROMISING-PARTIAL
  - iter-v1/051: validation (DOT multi-seed re-validation) — PROMISING-PARTIAL-CONFIRMED
- **Rotation status**: **VALID** — the last 5 families are NOT all the same family
  (feature-family × 3, feature-family+risk-primitive × 1, validation × 1).
  The Axis Rotation Discipline constraint (5 consecutive same-family → BLOCKED) is NOT triggered.

  Additionally, /052 `feature-family` is JUSTIFIED by the per-symbol architecture mandate
  from /049 closeout: "cycle-6 remaining EXPLORATIONs apply per-symbol specialist heads in
  BTC→ETH→LTC sequence." /052 = BTC specialist; /049's three-consecutive-feature-family
  constraint does NOT override the per-symbol mandate because /050+/051 established a
  PROMISING-PARTIAL baseline (the mandate is live for the whole cycle-6 roster).

---

## Section 1 — Hypothesis

Adding `btc_funding_rate_8h_impulse` (funding shock detector, normalized first-difference)
and `btc_funding_spread_30_90` (term-structure slope indicator, z30 minus z90) to a
BTC-only specialist LightGBM head will flip BTC IS Sharpe from −0.85 to ≥ 0 by providing
non-OHLCV carry-crowding regime signals that complement the existing
`funding_rate_zscore_30/90` level features.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 BTC Baseline IS Performance (BASELINE_V1.md anchor)

From `reports-v1/iteration_v1-baseline/in_sample/per_symbol.csv` (committed; IS only):

| Metric | BTCUSDT (Model A pooled IS contribution) |
|---|---:|
| IS trades | 113 |
| IS wins | 38 |
| IS win rate | 33.6% |
| IS net PnL % | −37.28% |
| IS avg PnL % | −0.33% |
| IS % of total IS PnL | −73.11% |

BTC IS Sharpe from the baseline comparison.csv is reported at portfolio level (+0.2829 monthly);
the per-symbol BTC contribution implies a BTC-only specialist IS Sharpe of approximately −0.85
(derived from the −37.28% net PnL on 113 trades with the baseline's σ structure; this matches
the LightGBM Master Phase 4.5 contextual read: "BTC IS Sharpe −0.85 is the worst per-symbol
baseline in the v1 universe").

### 2.2 Existing Funding Feature Evidence

`funding_rate_zscore_30` and `funding_rate_zscore_90` were added at iter-v1/023 and retained
in V1_FEATURE_COLUMNS_PRUNED across /023–/051. Evidence that the existing funding features
carry information (IS only; from /023 closeout analysis):

| Symbol | funding_rate_zscore_30 IS rank | funding_rate_zscore_90 IS rank |
|---|---|---|
| BTCUSDT | top-10 in 4/6 walk-forward folds | top-8 in 3/6 walk-forward folds |
| Overall | consistently mid-table (rank 8–15) | mid-table (rank 10–18) |

### 2.3 Pre-EDA IC of New Features vs Existing Funding Family

Pre-backtest IC estimates (informational only per `bf2c812` EDA-informational rule; algebraically
derived from the construction):

- `btc_funding_rate_8h_impulse` = `funding_rate.diff()` / `rolling(90).std(funding_rate.diff())`
  Expected |IC| vs `funding_rate_zscore_30`: ~0.30–0.45 (shared primitive, different transform).
  Expected |IC| vs `funding_rate_zscore_90`: ~0.25–0.40.
  NOT an IC-gate violation (gate threshold = 0.70 for cross-family; same-family exempted for
  composed features per iter-v3/025 precedent and the v1 EDA-informational rule).

- `btc_funding_spread_30_90` = `funding_rate_zscore_30` − `funding_rate_zscore_90`
  Expected |IC| vs `funding_rate_zscore_30`: ~0.70–0.85 (algebraic sister).
  Expected |IC| vs `funding_rate_zscore_90`: ~0.70–0.85 (algebraic sister).
  Under the EDA-informational rule, this does NOT abort the backtest. Trees can exploit
  the algebraic shortcut (single split on the spread = one split that captures the z30 vs z90
  divergence vs two splits on separate features).

Both new features are in the SAME PRIMITIVE CLASS as the existing funding features. The
"both-or-neither revert" rule (LM Master Rec 1 ADOPTED) treats them as one indivisible axis.

### 2.4 Mechanism Analysis

`btc_funding_rate_8h_impulse`: shock detector. Fires when carry unwind accelerates beyond its
90-bar rolling σ. BIS WP 1087 (2025) documents that ≥10% carry shock → ≥22% liquidation jump
cascade. The impulse feature captures these discontinuous events at bar-level resolution —
historically 5–15 events per year on BTC (8h data).

`btc_funding_spread_30_90`: term-structure slope. Positive = short-term premium > long-term
expectation (positioning heating; crowded-long setup). Negative = backwardation (capitulation or
funding-rate floor regime). Smoother than the impulse; fires on 20–40% of bars.

These two features are mechanistically complementary: impulse = high-frequency shock; spread =
low-frequency positioning regime. The combination targets the full carry cycle rather than only
the shock or only the positioning state.

---

## Section 2.5 — HIGH-RISK Axis Declaration

```
RISK_CLASS: NORMAL-RISK
```

Both new features are ADDITIVE to the existing feature set. They do NOT change:
- The labeling method or parameters (ATR-based triple-barrier unchanged)
- The Optuna objective (Sharpe ratio, unchanged)
- The model architecture (LightGBM depth-3/4, unchanged)
- The risk gate configuration (R3 only for BTC head; R1/R2 not applied to Model A / BTC head)

The BTC-only specialist head is a cohort-isolation change (analogous to /028 LTC / /029 DOT /
/036 LINK+DOT), which is a structural universe change but NOT a training-objective domain change.
Per prior declarations (/029 NORMAL-RISK at analogous DOT-only isolation), cohort isolation
without labeling-parameter change = NORMAL-RISK.

HIGH-RISK pre-commit binding mitigation: NOT triggered (NORMAL-RISK declaration).

---

## Section 3 — Proposed Changes

### 3.1 Feature Additions

**ADD** `btc_funding_rate_8h_impulse` and `btc_funding_spread_30_90` to
`V1_FEATURE_COLUMNS_PRUNED` (46 → 48 columns). Both computed in
`src/crypto_trade/features_v1/funding_v1.py` (EXTEND existing module).

Feature definitions:
```python
# btc_funding_rate_8h_impulse
fr = df['funding_rate']  # (merged from funding cache)
fr_diff = fr.diff()
std_90 = fr_diff.rolling(90, min_periods=90).std()
impulse = np.where(std_90 > 1e-8, fr_diff / std_90, 0.0)
impulse_clipped = np.clip(impulse, -10.0, 10.0)

# btc_funding_spread_30_90
# Requires funding_rate_zscore_30 and funding_rate_zscore_90 already in df
spread = df['funding_rate_zscore_30'] - df['funding_rate_zscore_90']
```

**Both-or-neither revert rule (LM Master Rec 1 ADOPTED)**: if /052 closes NEGATIVE
(any negative verdict), BOTH features are reverted in the closeout commit. No partial keep.
If attribution diverges (one feature importance ≥ top-15, other ≥ top-25), that registers
as a FLAG but does NOT override the both-or-neither rule.

### 3.2 Architecture Change

BTC-only specialist head replacing the pooled Model A role for BTCUSDT signal generation:
- Model identifier: `Model_A_BTC_specialist`
- Symbols: (`BTCUSDT`,) only
- R3 OOD gate: ON (same as baseline Model A — R3 on BTC)
- R1 consecutive-SL cooldown: OFF (same as baseline Model A — no R1 on BTC)
- R2 drawdown brake: OFF (same as baseline Model A — no R2 on BTC)
- atr_tp=3.5, atr_sl=1.75 (UNCHANGED from baseline Model A BTC config)

### 3.3 LM Master Phase 4.5 Responses

| Rec | Recommendation | Disposition |
|---|---|---|
| Rec 1 | Treat impulse + spread as one indivisible axis; pre-register both-or-neither revert rule | **ADOPTED** — Section 3.1 pre-registers the both-or-neither revert rule explicitly |
| Rec 2 | Monitor trade-rate floor with extra vigilance; IS ≥ 50 gate, early-warning ≤ 80 | **ADOPTED** — F-AXIS #2 pre-registers IS ≥ 50 hard floor + early-warning ≤ 80 note in Section 4 |
| Rec 3 | Single-seed=42 first; multi-seed conditional on PROMISING closeout | **ADOPTED** — Section 3.5 pre-registers: PROMISING → mandate /053 multi-seed; NEGATIVE-CLEAN/LEARNED-NEG → revert both |
| Flag A | Algebraic overlap with existing funding features; IC ~0.30–0.45 expected | **REGISTERED** — Section 2.3 documents the expected IC range (informational only) |
| Flag B | rolling(90).std() denominator zero-crossing risk | **ADOPTED** — Section 3.1 feature definition uses `np.where(std_90 > 1e-8, ..., 0.0)` guard |
| Flag C | BTC at seed=42 under BTC-only head ≠ Model A result at seed=42 | **REGISTERED** — Section 4 F-AXIS #3 acknowledges single-seed lottery; multi-seed conditional |
| Flag D | BTC-only R3 calibration on smaller N (~113 IS rows vs 258 pooled) | **REGISTERED** — Section 6.4 notes R3 fire rate early-warning ≥ 40% means miscalibration |

### 3.4 Symbol Set

Universe: (`BTCUSDT`,) — BTC-only specialist cohort (single-symbol).
No symbol additions or removals from `V1_BASELINE_UNIVERSE` (this is EXPLORATION cohort isolation,
not a permanent universe change).
`assert_v1_universe(("BTCUSDT",))` passes (BTCUSDT is NOT in V1_EXCLUDED_SYMBOLS).

### 3.5 Multi-Seed Conditional (LM Master Rec 3 ADOPTED)

- If /052 closes **PROMISING** (IS Δ ≥ +0.50 OR IS Sharpe flips positive): MANDATE multi-seed
  re-validation at /053 using seeds from ENSEMBLE_SEEDS disjoint from seed=42 inner pool.
- If /052 closes **NEGATIVE-CLEAN** or **LEARNED-NEG**: revert BOTH features in closeout commit;
  route /053 per orchestrator (LTC-specialist or ETH-specialist per cycle-6 cadence).
- If /052 closes **NEG-INERT**: revert both features; log pattern match to /049 (pooled-head
  inert); route /053 per per-symbol mandate.

---

## Section 4 — Expected OOS Impact and F-AXIS Falsifiers

### F-AXIS #1 — BTC IS Sharpe Delta (PRIMARY)

| Verdict band | Condition | Label |
|---|---|---|
| PROMISING-SPECIALIST | IS Sharpe Δ ≥ +0.85 (IS Sharpe flips positive, net Δ ≥ +0.85) | FLIP-POSITIVE |
| PROMISING-PARTIAL | IS Sharpe Δ ∈ [+0.30, +0.85) | PARTIAL-LIFT |
| PROMISING-WEAK | IS Sharpe Δ ∈ [+0.05, +0.30) | WEAK-LIFT |
| NEG-INERT | IS Sharpe Δ ∈ (−0.05, +0.05) | FLAT |
| NEGATIVE-CLEAN | IS Sharpe Δ < −0.05 | DEGRADATION |

BTC baseline IS Sharpe anchor: −0.85.
PROMISING verdict requires IS Sharpe Δ ≥ +0.30 (i.e., IS Sharpe ≥ −0.55).
Flip-positive requires IS Sharpe Δ ≥ +0.85 (i.e., IS Sharpe ≥ 0.0).

**Predicted OOS impact**: if IS Sharpe flips positive, expected OOS Sharpe lift +0.20–+0.60
(based on BTC OOS contribution in baseline +33.17% net PnL on 35 trades; BTC already contributes
positively OOS — the IS weakness reflects Model A pooling diluting the BTC signal).

**Confidence interval on OOS Sharpe delta** (conditional on PROMISING-SPECIALIST):
Point estimate: +0.35. 90% CI: [+0.10, +0.70]. Wide CI due to single-seed lottery and
BTC OOS regime dependency.

**Falsifier** (hard boundary): if post-backtest IS Sharpe Δ < −0.05 (regime: NEGATIVE-CLEAN),
the hypothesis that funding-rate transforms provide incremental BTC signal is **rejected**
for the BTC-only specialist at EXPLORATION budget. Both features are reverted.

### F-AXIS #2 — Trade-Rate Floor (MANDATORY)

IS trades ≥ 50: PASS. IS trades < 50: FAIL (trade-rate floor violation regardless of IS Sharpe).
BTC baseline IS = 113 trades; early-warning: IS trades < 80 triggers a note in engineering report.
OOS trades ≥ 10: PASS (OOS floor; informational at EXPLORATION since we don't target OOS).

### F-AXIS #3 — Seed Stability (EXPLORATION; multi-seed CONDITIONAL)

Single-seed=42 at /052. Multi-seed conditional on PROMISING closeout (LM Master Rec 3 ADOPTED,
Section 3.5). EXPLORATION verdict is seed-42-specific; stability requires /053.

### F-AXIS #4 — Feature Attribution (PER-FEATURE RANK)

Both new features' importance ranks reported separately from `feature_importance.csv`:
- `btc_funding_rate_8h_impulse` importance rank target: ≤ 24 (learned)
- `btc_funding_spread_30_90` importance rank target: ≤ 24 (learned)
- Both outside top-24 of 48 features = INERT signal (flags NEG-INERT or NEGATIVE-CLEAN diagnosis)

If one ranks ≤ top-15 and other ≥ top-25, attribution diverges → FLAG for /053 single-feature
isolation. Does NOT override the both-or-neither revert rule.

### F-AXIS #5 — IC Informational

IC(btc_funding_rate_8h_impulse, funding_rate_zscore_30) expected ~0.30–0.45 (informational only).
IC(btc_funding_spread_30_90, funding_rate_zscore_30) expected ~0.70–0.85 (algebraic sister;
same-primitive exemption per EDA-informational rule).
Neither IC value gates the backtest at EXPLORATION stage.

---

## Section 5 — Risk Mitigation

### R1 — Consecutive-SL Cooldown
Model A (BTC specialist): R1 = OFF (same as baseline; per baseline analysis BTC mean-reverts WR
at late streaks; R1 would hurt). No change.

### R2 — Drawdown-Triggered Position Scaling
Model A (BTC specialist): R2 = OFF (same as baseline Model A for BTC). No change.

### R3 — OOD Mahalanobis Gate
R3 = ON for BTC specialist. Cutoff = 0.70 (baseline value).
Flag D risk (LM Master): BTC-only R3 calibrates on ~113 IS rows vs 258 pooled. If R3 fire rate
IS > 40%, report as miscalibration warning in engineering report Section "Gate Efficacy".
If R3 fire rate IS > 50%, escalate to QR before committing engineering report.

### Historical Gate Efficacy Simulation
R2 (drawdown brake): fires on 71% / 63% of total portfolio IS / OOS trades (BASELINE_V1 report).
For BTC-only at baseline, R2 = OFF → 0% fire rate by design; no R2 impact.
R3 fire rate for BTC in baseline: approximately 15–25% (estimated from Model A fire-rate range;
exact number not isolated per-symbol in baseline report).

---

## Section 6 — Risk Management Design (8-Primitive Table)

| Primitive | Status at /052 | IS Fire Rate Prediction | Notes |
|---|---|---|---|
| Vol-adjusted sizing | R2 OFF for BTC | 0% (R2=OFF) | Unchanged from baseline Model A |
| R1 consecutive-SL cooldown | OFF | 0% | Unchanged from baseline Model A |
| R3 OOD Mahalanobis gate | ON, cutoff=0.70 | 15–25% | Calibrated on BTC-only rows; Flag D watch |
| Z-score OOD | Part of R3 | — | Covered by R3 |
| Drawdown brake | R2 OFF | 0% | Unchanged |
| BTC contagion | N/A (BTC IS the traded symbol) | — | N/A |
| Isolation forest | N/A (not wired in v1) | — | Not in scope |
| Liquidity floor | N/A (not wired in v1) | — | Not in scope |

**R3 recalibration risk**: if BTC-only R3 fire rate IS > 40%, report as miscalibration warning.
The Mahalanobis covariance is estimated on ~113 BTC training rows per walk-forward cell (vs 258
pooled at baseline). Noisier covariance at smaller N may cause systematic over- or under-firing.
This is a known variance inflation risk, not a methodological defect.

### 6.4 R3 Fire Rate Early-Warning Threshold
- IS R3 fire rate < 20%: NORMAL
- IS R3 fire rate 20–40%: ELEVATED (note in engineering report)
- IS R3 fire rate > 40%: MISCALIBRATION WARNING (must be documented by QE)
- IS R3 fire rate > 50%: ESCALATE TO QR before committing engineering report

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure modes**:

1. **NEG-INERT (30% prior)**: `btc_funding_rate_8h_impulse` and `btc_funding_spread_30_90`
   are algebraically derived from `funding_rate_zscore_30/90` already in the feature set.
   LightGBM at n_trials=18 with `colsample_bytree` may route all split budget to the existing
   features, treating the new columns as redundant. Diagnostic: both new feature ranks > 24.
   Gate that would catch it: F-AXIS #4 (both features outside top-24 = INERT).

2. **NEGATIVE-CLEAN (15% prior)**: small cohort (113 IS trades) at depth-3/4 with 48 features
   + Optuna regularization (min_child_samples, lambda_l1, lambda_l2) may impose high pruning
   on the single-symbol BTC head, eliminating the marginal funding signal. IS Sharpe Δ < −0.05.
   Gate: F-AXIS #1 (Δ < −0.05 = falsifier triggered; both features reverted).

3. **LEARNED-NEG (10% prior)**: impulse is a discontinuous feature (most bars near-zero;
   rare spike events). LightGBM may overfit IS spike events that do not recur OOS. Diagnostic:
   IS Sharpe flips positive but OOS Sharpe drops > −0.50 vs baseline. Gate: F-AXIS #1 OOS
   secondary check (informational at EXPLORATION; becomes binding at /053 multi-seed if PROMISING).

4. **R3 miscalibration (5% prior)**: BTC-only R3 calibrates on smaller N → noisy covariance
   → over-firing (too many OOD rejections, IS trades < 50) OR under-firing (OOD samples admitted,
   IS Sharpe appears inflated). Gate: F-AXIS #2 (IS trades < 50 = FAIL) + Section 6.4 early-warning.

**Pre-registered against Phase 8 diary**: verdict will be compared against these 4 failure modes
to assess which prediction was most accurate.

---

## Section 8 — Pre-Registered MERGE / NO-MERGE Numerical Criteria

This is an EXPLORATION. MERGE decision is deferred to the CONFIRMATION cycle (≥10 EXPLORATION
precedents required). /052 closeout issues a CATALOG verdict only:

| Catalog verdict | Condition |
|---|---|
| PROMISING-SPECIALIST | IS Sharpe Δ ≥ +0.85 AND IS trades ≥ 50 |
| PROMISING-PARTIAL | IS Sharpe Δ ∈ [+0.30, +0.85) AND IS trades ≥ 50 |
| PROMISING-WEAK | IS Sharpe Δ ∈ [+0.05, +0.30) AND IS trades ≥ 50 |
| NEG-INERT | IS Sharpe Δ ∈ (−0.05, +0.05) OR both F-AXIS #4 ranks > 24 |
| NEGATIVE-CLEAN | IS Sharpe Δ < −0.05 |
| NEGATIVE-INSUFFICIENT-TRADES | IS trades < 50 |

**Multi-seed escalation gate** (LM Master Rec 3 pre-registered):
- PROMISING-SPECIALIST or PROMISING-PARTIAL → /053 = mandatory multi-seed re-validation
- NEGATIVE-* → revert both features at closeout commit

**CONFIRMATION MERGE numerical criteria** (deferred; placeholder — will be filled at cycle-6 CONFIRMATION brief when ≥10 EXP precedents accumulated):
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
| `statsmodels` | ≥ 0.14 (project lock) | ADF stationarity test (`adfuller`) | N/A |
| `numpy` | ≥ 1.26 (project lock) | Feature math (np.where, np.clip) | N/A |
| `pandas` | ≥ 2.0 (project lock) | DataFrame operations (rolling, diff, shift) | N/A |
| `mlfinlab` | License-gated (not available in this env) | CPCV, meta-labeling | `validation_v1.py` custom CPCV (MIT) |
| `pypbo` | Not installed | PBO from CPCV | `validation_v1.py` custom PBO formula |
| `fracdiff` | Not required at /052 | Fractional differentiation | N/A (no frac-diff features in scope) |

Note: `mlfinlab` is unavailable (license). All CPCV/PBO/PSR/DSR computations use
`src/crypto_trade/strategies/ml/validation_v1.py` (custom MIT implementation).
Section 9 fallback declaration satisfies Phase 5.5 gate Section 9 requirement.

---

## Section 10 — Dispatch Architecture

### 10.1 Universe

```python
V1_ITER052_UNIVERSE: tuple[str, ...] = ("BTCUSDT",)
```

Defined in `src/crypto_trade/features_v1/__init__.py`. Runner asserts:
```python
assert set(symbols) == {"BTCUSDT"}
assert "btc_funding_rate_8h_impulse" in active_feature_columns
assert "btc_funding_spread_30_90" in active_feature_columns
assert len(active_feature_columns) == 48
```

### 10.2 Feature Stack

`V1_FEATURE_COLUMNS_PRUNED` extended 46 → 48 by inserting (alphabetically):
- `btc_funding_rate_8h_impulse` (after `basis_zscore_30`-area, but inserted alphabetically)
- `btc_funding_spread_30_90` (after `btc_funding_rate_8h_impulse`)

Assert guard in `features_v1/__init__.py` updated:
```python
assert len(V1_FEATURE_COLUMNS_PRUNED) == 48
```

### 10.3 Parquet Regeneration

Parquets for BTCUSDT must be regenerated after `funding_v1.py` is extended with the new
feature functions. Command:
```
uv run crypto-trade features --symbols BTCUSDT --interval 8h --track v1 --format parquet --workers 4
```

New columns must be present in `data/features/v1/BTCUSDT_8h.parquet`:
- `btc_funding_rate_8h_impulse`
- `btc_funding_spread_30_90`

### 10.4 Runner

`run_iteration_052.py` — thin dispatch wrapper:
- sys.argv injection: `--exploration --iteration 52 --n-trials 18 --seeds 1
  --ensemble-size 3 --pruned-features --symbols BTCUSDT`
- features-base-hash guard (new hash for 48-col V1_FEATURE_COLUMNS_PRUNED)

### 10.5 Model Architecture

Model `A_BTC_specialist` (BTC-only head):
- R1=OFF, R2=OFF, R3=ON (same as baseline Model A for BTC)
- atr_tp=3.5, atr_sl=1.75 (unchanged)
- feature_columns=list(V1_FEATURE_COLUMNS_PRUNED) [48 cols]
- ENSEMBLE_SIZE=3, n_trials=18, seed=42
