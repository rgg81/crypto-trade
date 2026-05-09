# Iteration v3-044 — Research Brief

**Type**: EXPLORATION (Cycle 3 #5 of 10)
**Track**: v3 (rigor arm) — forty-fourth iteration
**Branch**: `iteration-v3/044` (off iter-v3/043 head)
**Date**: 2026-05-09
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # single outer seed (EXPLORATION-spec)
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. The QR sees OOS metrics for the FIRST time in Phase 7.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 3 — #5 of 10
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Two-part axis (atomic revert + single new variation):
  PART A (revert pre-commit): efficiency_ratio_50 already DROPPED at code level
    (iter-v3/043 DISASTROUS NEGATIVE: IS -0.8445 / OOS -0.8990; all 4 symbols broken).
    V3_FEATURE_COLUMNS_TOP_N is currently 14 (ER dropped). This brief formalizes the revert.
  PART B (new variation): ADD regime_momentum_signed_3d to V3_FEATURE_COLUMNS_TOP_N (14 → 15).
    regime_momentum_signed_3d = ret_3d * sign(hurst_100 - 0.5)
    where ret_3d = (close.shift(1) / close.shift(4) - 1.0) — past-only 3-bar return.
    3-bar variant of the proven regime_momentum_signed_5d mechanism (sign-flip on Hurst).
    Different horizon: 3 bars x 8h = 24h (1 calendar day) vs 5d (15 bars x 8h = 5 days).
  V3_MODELS = 4 (BCH, LDO, TRX, ALGO) — UNCHANGED.
  REQUIRED_GAP = 88 = (21+1)*4 — UNCHANGED.
  V3_FEATURES_PER_SYMBOL = {} (empty — UNCHANGED).
  V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty — UNCHANGED).
  DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0) — UNCHANGED.
Net: V3_FEATURE_COLUMNS_TOP_N = 15 features (13 original + regime_momentum_signed_5d +
  regime_momentum_signed_3d).
Predicted classification: PROMISING (3d variant shares proven sign-flip mechanism with 5d;
  different lookback adds complementary short-horizon signal; lower-risk axis than new feature
  families; IC between 3d and 5d variants expected moderate, not redundant given horizon difference).
```

**Context**: iter-v3/043 EXPLORATION (Kaufman efficiency_ratio_50 addition) produced a DISASTROUS
NEGATIVE result (IS -0.8445 / OOS -0.8990; all 4 symbols broken). The revert is mandatory and
already applied at code level. The single new axis for iter-v3/044 is regime_momentum_signed_3d,
a 3-bar variant of the proven regime_momentum_signed_5d mechanism. This builds on a validated
signal family rather than introducing an entirely new feature class, reducing the risk of another
disastrous result while exploring whether a shorter-horizon regime momentum complements the
existing 5-day variant.

---

## Section 1 — Hypothesis

Adding a 3-bar variant of the proven regime_momentum_signed_5d mechanism captures shorter-horizon
(1-day) regime persistence that the 5-bar (5-day) variant misses, complementing rather than
substituting for the existing signal, and lifting IS Sharpe marginally above the iter-v3/040
anchor (+0.79) by giving LightGBM a two-horizon view of momentum-regime interaction.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Prior Art: regime_momentum_signed_5d IS Success

regime_momentum_signed_5d was introduced at iter-v3/025 and confirmed as the first
multi-seed-validated edge ingredient in v3 history (iter-v3/028 CONFIRMATION-MERGE):

| Metric | iter-v3/028 (with 5d) | iter-v3/018 (without) | Attributed lift |
|--------|-----------------------:|----------------------:|----------------:|
| IS monthly Sharpe | +0.5101 | +0.3788 | +0.1313 |
| OOS monthly Sharpe | +0.5053 | +0.3869 | +0.1184 |
| OOS MaxDD | 23.53% | 28.47% | -4.94pp |
| OOS Calmar | 0.9229 | 0.4629 | +0.46 |

Source: `BASELINE_V3.md` section "What Changed vs iter-v3/018 BOOTSTRAP" (committed).

Feature importance at iter-v3/025 portfolio level: regime_momentum_signed_5d rank 1, importance
51% of portfolio split importance. Source: `briefs-v3/iteration_v3-025/engineering_report.md`.

### 2.2 — 3-bar vs 5-bar Mechanism

Construction of regime_momentum_signed_3d vs regime_momentum_signed_5d:

```
regime_momentum_signed_5d: ret_5d = log(close) - log(close.shift(15))  # 15 bars = 5 days
regime_momentum_signed_3d: ret_3d = close.shift(1)/close.shift(4) - 1  # 3 bars = 1 day
```

Both apply the SAME sign-flip: multiply by sign(hurst_100 - 0.5). The key difference is
the return lookback: 5-day captures weekly momentum cycle; 3-bar (1-day) captures intraday-to-overnight persistence.

**Expected pairwise IC (3d vs 5d)**: moderate, not redundant. Both use the same hurst_100
sign-flip and the same return-based numerator. IC expected in [0.40, 0.70]. This is within
the IC gate threshold (< 0.70) for non-Category-2 features, but as a Category 2 composed
feature the standard IC carve-out applies (Category 2 features share variance with source
primitives by construction). If IC(3d, 5d) > 0.70, this is EXPECTED for composed features
sharing the Hurst sign-flip — the IC carve-out still applies.

**Behavioral-effect predictor** (per `feedback_v3_axis_saturation_predictor.md`):

Predicted IS trade count delta vs iter-v3/040 anchor: **< 5% (near-zero)**.

Mechanism: regime_momentum_signed_3d is a FILTERING feature — it signals short-horizon regime
quality but does not alter the labeling barrier geometry (ATR multipliers unchanged). The IS
trade roster depends only on the label distribution (TP/SL/timeout from ATR multipliers), which
is IDENTICAL to iter-v3/040. LightGBM learns which regime-momentum combinations produce good
trades; this may slightly alter signal frequency but cannot change the label distribution.

Falsifier: if observed |IS trade count change| > 20% relative vs iter-v3/040 anchor,
investigate — this magnitude cannot arise from a pure feature addition without a data
pipeline bug (stale parquets, incorrect feature_columns, label leakage).

### Analysis Script

No new committed EDA script is required. Evidence basis:
- regime_momentum_signed_5d IS/OOS lift: `BASELINE_V3.md` (committed, IS-only fold data).
- Feature importance rank: `briefs-v3/iteration_v3-025/engineering_report.md` (committed).
- IC analysis: `reports-v3/iteration_v3-040/ic_matrix.csv` (14-feature baseline IC matrix,
  IS-fold data only; the 3d variant's IC vs 5d variant will be computed by the Engineer
  and audited by the Critic at Phase 7.5).

---

## Section 3 — Proposed Changes

### Sub-fix 1: REVERT efficiency_ratio_50 (already applied at code level)

V3_FEATURE_COLUMNS_TOP_N currently has 14 features (ER already dropped from iter-v3/043
DISASTROUS NEGATIVE). compute_efficiency_ratio_50 retained as dead code in engineered_v3.py;
NOT dispatched from add_engineered_v3_features. This brief formalizes the revert already in code.

### Sub-fix 2: ADD regime_momentum_signed_3d to V3_FEATURE_COLUMNS_TOP_N (14 → 15)

In `src/crypto_trade/features_v3/__init__.py`, append `"regime_momentum_signed_3d"` to
V3_FEATURE_COLUMNS_TOP_N after `"regime_momentum_signed_5d"`:

```python
"regime_momentum_signed_3d",   # iter-v3/044: 3-bar variant of proven sign-flip mechanism
```

### Sub-fix 3: Implement compute_regime_momentum_signed_3d in engineered_v3.py

In `src/crypto_trade/features_v3/engineered_v3.py`, add:

```python
def compute_regime_momentum_signed_3d(df: pd.DataFrame) -> pd.Series:
    """3-bar variant of regime_momentum_signed_5d (sign-flip on hurst regime)."""
    close = df["close"]
    ret_3d = (close.shift(1) / close.shift(4) - 1.0)  # past-only, 3-bar return
    hurst = df["hurst_100"]  # already past-only by construction
    regime_sign = np.sign(hurst.shift(1) - 0.5)
    return (ret_3d * regime_sign).fillna(0.0)
```

Dispatch it from `add_engineered_v3_features` AFTER `compute_regime_momentum_signed_5d`.

**Past-only proof**:
- `close.shift(1)`: bar t uses close[t-1]. Past-only.
- `close.shift(4)`: bar t uses close[t-4]. Past-only.
- `hurst_100` is computed past-only by `add_regime_v3_features` (100-bar trailing R/S).
- `hurst.shift(1)`: bar t uses hurst_100[t-1]. Past-only.
- NaN warmup: first 100 bars have NaN hurst_100 (100-bar window); first 4 bars have NaN
  from close.shift(4). Combined: first 100 bars are NaN before fillna.
- fillna(0.0): NaN warmup filled to neutral (no regime signal).

### Sub-fix 4: Update _verify_feature_columns in run_baseline_v3.py

Update assertions for iter-v3/044 state:
- `len(V3_FEATURE_COLUMNS) == 15` (was 14; adding regime_momentum_signed_3d)
- `"regime_momentum_signed_3d" in V3_FEATURE_COLUMNS` (new positive assertion)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS` (mandate still PRESENT)
- `"efficiency_ratio_50" not in V3_FEATURE_COLUMNS` (ABSENT — DISASTROUS NEGATIVE)
- All 4 symbols return 15-feature fallback via `features_for_symbol`
- Update per-symbol loop assertion from `len(sym_feats) != 14` → `len(sym_feats) != 15`

### Sub-fix 5: Update ITERATION_LABEL

In `run_baseline_v3.py`, verify (already set):
```python
ITERATION_LABEL = "v3-044"
```

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 15 features (14 restored + regime_momentum_signed_3d)    PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)                                                  PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty)                                            PASS
V3_FEATURES_PER_SYMBOL: {} (empty)                                                   PASS
features_for_symbol("BCHUSDT") == 15 features (V3_FEATURE_COLUMNS_TOP_N fallback)   PASS
features_for_symbol("ALGOUSDT") == 15 features (fallback)                            PASS
features_for_symbol("LDOUSDT") == 15 features (fallback)                             PASS
features_for_symbol("TRXUSDT") == 15 features (fallback)                             PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)           PASS
"regime_momentum_signed_3d" IN V3_FEATURE_COLUMNS_TOP_N (NEW)                       PASS
"efficiency_ratio_50" NOT IN V3_FEATURE_COLUMNS_TOP_N (ABSENT — DISASTROUS NEGATIVE)PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                 PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                           PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                       PASS
REQUIRED_GAP = 88 = (21+1) x 4                                                       PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+0.79):**
- Predicted band: [+0.55, +1.05]
- Median point estimate: +0.80
- Rationale: The 5d variant contributes ~+0.13 IS Sharpe (iter-v3/028 attribution). A 3d variant
  at a different horizon should add complementary information rather than redundancy. The IS
  label distribution is IDENTICAL to iter-v3/040 (ATR multipliers unchanged). Modest IS lift
  expected from the additional two-horizon view.

**OOS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+1.77):**
- Predicted band: [+1.50, +2.10]
- Median point estimate: +1.80
- Rationale: OOS single-seed variance is ~±0.5 at this portfolio scale. If 3d variant adds
  complementary signal, OOS >= +1.60 is plausible. Band is deliberately wide to reflect
  single-seed noise.

**OOS falsifier (pre-registered)**:
- If OOS Sharpe drops below +1.55 (more than 0.22 below iter-v3/040 anchor): the 3-bar
  variant does not contribute universal signal; NEGATIVE classification; drop
  regime_momentum_signed_3d from universal list at iter-v3/045.

**Pathway-A trigger (PROMISING)**:
- IS Sharpe >= +0.89 (>= +0.10 lift over anchor) AND OOS Sharpe >= +1.55.

**Pathway-B trigger (PROMISING-INERT)**:
- IS Sharpe in [+0.55, +0.89] (within ±0.24 of anchor) AND OOS >= +1.55.

**Pathway-C trigger (NEGATIVE)**:
- OOS Sharpe < +1.55 (drops > 0.22 below anchor).
- Action: drop regime_momentum_signed_3d from universal list at iter-v3/045.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.
**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from iter-v3/040.
**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace expands from
14 → 15 features; Mahalanobis covariance space adds one dimension. Expected effect on OOD
firing rate: < 5% relative (one new correlated feature in 15-D adds minimal joint-space
volume change relative to the 14-D baseline).

**15th feature addition risk**: adding one composed feature to a 14-feature Optuna-tuned model
shifts the colsample_bytree landscape marginally. The n_trials=35 budget is sufficient for
colsample_bytree to stabilize given prior EXPLORATION data points at this budget.

**IS trade-rate stability**: ATR multipliers unchanged; label distribution identical to
iter-v3/040. IS trade count expected within ±5% of iter-v3/040. If deviation > 20%,
investigate parquet freshness (stale features, incorrect feature_columns list).

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/040 baseline unchanged.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0 | 15-feature space (NEW: +3d variant) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

**Predicted OOD fire rate**: within ±10% of iter-v3/040 baseline. regime_momentum_signed_3d
shares the hurst_100 sign-flip source primitive with regime_momentum_signed_5d; their IC is
expected moderate [0.40, 0.70]. The Mahalanobis volume expansion from adding a moderately
correlated feature is bounded by the existing dimensionality.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (NEGATIVE — 3d variant is REDUNDANT with 5d at 8h cadence)**:
At 3 bars x 8h = 24h, the 3-bar return window is very short relative to the 21-candle
(7-day) triple-barrier timeout. The 5d variant (15 bars = 5 days) is already within the
timeout window. The 3d return may contain mostly noise at 8h cadence (crypto markets
exhibit high intraday mean-reversion noise at 1-day horizons). If LightGBM treats 3d and 5d
as substitutes (IC too high), it may rotate between them without adding net information.
The feature importance would show 3d rank ~14/15 and 5d unchanged, with IS Sharpe flat.

**Second plausible failure mode (PROMISING-INERT — parsimony-neutral)**:
If the 3d and 5d variants are orthogonal enough that LightGBM learns both (using different
split conditions), but the 3d variant contributes limited marginal information beyond 5d,
IS Sharpe may improve only marginally (< +0.10 lift). Classification: PROMISING-INERT.
The variant would be retained for potential CONFIRMATION bundle inclusion but should not
be used standalone.

**Third plausible failure mode (concentration shift)**:
If regime_momentum_signed_3d is predictive only for TRX (shortest-horizon momentum
structure in the universe), the 3d variant may concentrate OOS PnL attribution further
toward TRX. Engineering report: per-symbol feature importance audit of 3d rank across
all 4 symbols.

**What the gates should catch**:
- Gate 6 (OOD): 15-feature Mahalanobis space. Firing rate expected ±10% vs iter-v3/040.
- Gate 5 (R2 drawdown): ATR unchanged; IS label distribution restores to iter-v3/040 norm.

**Behavioral effect predictor**: predicted IS trade count delta < 5% vs iter-v3/040.
Falsifier: > 20% triggers investigation.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING**:
  IS Sharpe >= +0.89 (>= +0.10 lift over iter-v3/040 anchor ~+0.79) AND
  OOS Sharpe >= +1.55 (maintained within -0.22 of iter-v3/040 anchor ~+1.77).
  Classification: PROMISING. regime_momentum_signed_3d contributes universal signal.
  Catalog entry: candidate for next CONFIRMATION bundle.

**PATH B — PROMISING-INERT**:
  IS Sharpe in [+0.55, +0.89] (within ±0.24 of anchor) AND OOS Sharpe >= +1.55.
  Classification: PROMISING-INERT. 3-bar variant is parsimony-neutral; short-horizon
  regime momentum does not improve aggregate IS Sharpe materially. May pair with other
  ingredients in CONFIRMATION bundle as a zero-cost addition.

**PATH C — NEGATIVE**:
  OOS Sharpe < +1.55 (drops > 0.22 below anchor).
  Classification: NEGATIVE. 3-bar variant hurts OOS aggregate.
  Action: drop regime_momentum_signed_3d from universal list at iter-v3/045.
  Catalog entry: Kaufman 3-bar sign-flip FALSIFIED for this universe.

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A requires IS >= +0.89 AND OOS >= +1.55
- PATH B requires IS in [+0.55, +0.89] AND OOS >= +1.55
- PATH C requires OOS < +1.55

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/043 / iter-v3/040 / iter-v3/028 reproducibility stamp.
No new libraries introduced. regime_momentum_signed_3d uses only pandas built-ins (shift,
sign, fillna) and numpy (sign) — no new dependencies.

| Package | Version | Source |
|---|---|---|
| lightgbm | 4.6.0 | pyproject.toml pinned |
| numpy | 2.2.6 | pyproject.toml pinned |
| optuna | 4.8.0 | pyproject.toml pinned |
| pandas | 3.0.0 | pyproject.toml pinned |
| pyarrow | 23.0.1 | pyproject.toml pinned |
| scikit-learn | 1.8.0 | pyproject.toml pinned |
| scipy | 1.17.0 | pyproject.toml pinned |
| statsmodels | 0.14.6 | pyproject.toml pinned |

**No mlfinlab/mlfinpy/pypbo/fracdiff dependencies.** v3 uses scipy + statsmodels
for all statistical tests (ADF, PBO, DSR, PSR). fracdiff (the package) is NOT used;
v3's FracdiffStat uses the custom implementation in `features_v3/fracdiff_v3.py`.
No library-unavailability fallbacks apply.
