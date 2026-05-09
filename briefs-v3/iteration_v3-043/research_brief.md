# Iteration v3-043 — Research Brief

**Type**: EXPLORATION (Cycle 3 #4 of 10)
**Track**: v3 (rigor arm) — forty-third iteration
**Branch**: `iteration-v3/043` (off iter-v3/042 head)
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
Cycle: 3 — #4 of 10
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; non-exploration inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Two-part axis (atomic revert + single new variation):
  PART A (revert pre-commit): REVERT DEFAULT_ATR_MULTIPLIERS from (1.5, 0.75)
    back to (2.0, 1.0). iter-v3/042 Path C NEGATIVE mandate fires (IS Sharpe
    -0.5941, OOS +2.0752 but IS collapse classifies NEGATIVE due to divergent
    per-symbol TRX drag: TRX -33 OOS wpnl swing at tighter barriers). The
    per-brief Section 8 Path C criterion: OOS < +1.57 was NOT triggered (OOS
    +2.0752 > +1.57), but the engineering report classifies NEGATIVE because
    the IS collapse (-0.5941 vs anchor +0.79) is structurally unsound regardless
    of OOS lift. QR confirms revert per engineering_report.md recommendation.
  PART B (new variation): ADD efficiency_ratio_50 (Kaufman 1995) to
    V3_FEATURE_COLUMNS_TOP_N (14 → 15 features).
    efficiency_ratio_50 = abs(close - close.shift(50)) / sum(abs(close.diff()).rolling(50))
    Orthogonal mechanism to regime_momentum_signed_5d: ER captures MAGNITUDE of
    directional efficiency, while regime_momentum captures DIRECTION of momentum
    conditional on Hurst. ER is always positive [0,1]; regime_momentum can be
    negative.
  V3_ATR_MULTIPLIERS_PER_SYMBOL = {} (empty — REVERTED; all symbols use DEFAULT
    (2.0, 1.0) via fallback).
  V3_FEATURES_PER_SYMBOL = {} (empty — no per-symbol feature overrides).
Predicted classification: PROMISING-HYPOTHESIS (Kaufman ER is a well-known
  regime-quality signal; first exposure to this axis in v3 catalog; modest lift
  predicted given anchor IS +0.79).
```

**Context**: iter-v3/042 EXPLORATION (universal ATR tightening (2.0,1.0) → (1.5,0.75))
produced a NEGATIVE result by IS collapse: IS Sharpe -0.5941 (Δ -1.39 from anchor +0.79)
driven by TRX OOS -33 swing. This confirms the v3 pattern from iter-v3/034: universal
labeling changes have highly divergent per-symbol effects. The revert to (2.0, 1.0) is
required. The single new axis for iter-v3/043 is efficiency_ratio_50 (Kaufman 1995
efficiency ratio), a well-defined formula without EDA prerequisites, stacked as a 15th
feature on the restored 14-feature universal anchor.

---

## Section 1 — Hypothesis

Adding the Kaufman efficiency ratio (ER-50) to the 14-feature universal set provides a
regime-strength signal complementary to regime_momentum_signed_5d's direction-flip
mechanism: ER-50 measures how efficiently price has moved over the past 50 bars
regardless of direction (closer to 1.0 = strong trend, closer to 0.0 = choppy), giving
LightGBM a continuous quality-of-trend input distinct from the binary sign-flip of
regime_momentum_signed_5d, and lifting IS Sharpe toward the iter-v3/040 anchor (+0.79)
by enabling the model to filter low-efficiency mean-reverting noise periods.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — Kaufman Efficiency Ratio Formula and Properties

Source: Kaufman, P.J. (1995), *Smarter Trading*, Chapter 5 (Well-established TA formula;
no committed EDA script required — formula is definitionally correct with known properties).

**Definition**:

```
direction_50[t] = abs(close[t] - close[t-50])     # net price displacement over 50 bars
noise_50[t]     = sum_{k=1}^{50} abs(close[t-k+1] - close[t-k])  # sum of bar-by-bar moves
efficiency_ratio_50[t] = direction_50[t] / (noise_50[t] + 1e-9)
```

**Properties** (analytical; no EDA needed):
- Range: [0, 1] — guaranteed by triangle inequality: |start - end| <= sum of step sizes.
- ER = 1.0: perfectly trending (all bars move in same direction without reversal).
- ER = 0.0: perfectly oscillating (all bar moves cancel, net displacement = 0).
- ER is UNSIGNED: measures quality of trend, not direction. Orthogonal to signed features.
- Warmup: 50-bar rolling window + 1 shift for past-only discipline = NaN for first 51 bars.
  At 8h cadence: 51 bars ≈ 17 calendar days. Well within IS window (2742 bars).

**IC projection against existing features** (analytical):
- vs regime_momentum_signed_5d: low expected IC. ER is unsigned [0,1]; regime_momentum
  is signed (positive in trending, negative in reverting). A trending bar (ER ≈ 1.0) can
  have positive OR negative regime_momentum depending on the direction. Expected |IC| < 0.3.
- vs hurst_100: moderate expected IC. Both capture trend persistence. Hurst is computed
  from R/S scaling (100-bar); ER uses a direct price-path ratio (50-bar). Different
  estimation methods; |IC| expected in [0.2, 0.5].
- vs hurst_diff_100_50: low expected IC. hurst_diff is a CHANGE measure; ER is a level.
- vs ema_spread_atr_20: low expected IC. ema_spread is a momentum proxy (short vs long
  EMA normalized by ATR); ER is a path-efficiency ratio. Expected |IC| < 0.2.

No IC hard-gate violation expected (all pairwise IC projected below 0.70 threshold).
The IC carve-out for Category 2 engineered features does NOT apply here — ER-50 is a
Category 1 indicator (well-established external formula), so the standard IC gate applies.
If post-hoc IC computation by the Critic reveals any pair > 0.70, the feature must be
dropped at iter-v3/044 regardless of IS/OOS outcome.

### 2.2 — Behavioral-Effect Predictor (per `feedback_v3_axis_saturation_predictor.md`)

**Predicted IS trade count delta vs iter-v3/040 anchor**: **< 5% (near-zero)**.

Mechanism: efficiency_ratio_50 is a FILTERING feature — it signals regime quality but does
not directly alter the labeling barrier geometry (unlike ATR multipliers). The IS trade
roster is driven by the label distribution (TP/SL/timeout), which depends only on
ATR multipliers. Since ATR multipliers revert to the iter-v3/040 (2.0, 1.0) defaults,
the IS label distribution is IDENTICAL to iter-v3/040. LightGBM learns which efficiency
levels produce good trades; this may slightly alter signal frequency but cannot change
the label distribution. Expected trade count change: 0-5% relative.

**Falsifier**: if observed |IS trade count change| > 20% relative vs iter-v3/040 anchor,
investigate — a feature added to a previously-stable-roster model cannot produce > 20%
trade-count swing without indicating a data pipeline bug (e.g., wrong parquets, stale
features, incorrect feature_columns list).

### Analysis script

No new committed EDA script is required for this iteration. The Kaufman efficiency ratio
formula is definitionally correct (Kaufman 1995). The ATR revert uses the existing
`analysis/iteration_v3-032/per_symbol_atr_eda.py` (SHA `9834e84`) as supporting IS-only
evidence that (2.0, 1.0) is the validated per-iter-v3/010 default. Prior IC matrix from
`reports-v3/iteration_v3-040/ic_matrix.csv` provides baseline pairwise IC for the 14
existing features.

---

## Section 3 — Proposed Changes

### Sub-fix 1: REVERT DEFAULT_ATR_MULTIPLIERS to (2.0, 1.0)

In `src/crypto_trade/features_v3/__init__.py`, change:

```python
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (1.5, 0.75)
```
→
```python
DEFAULT_ATR_MULTIPLIERS: tuple[float, float] = (2.0, 1.0)
```

Since `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` (empty), ALL symbols fall back to
`DEFAULT_ATR_MULTIPLIERS`. This restores the iter-v3/010–041 validated default universally.
Rationale: iter-v3/042 Path C (by IS collapse convention) fired; revert is mandatory.

### Sub-fix 2: ADD efficiency_ratio_50 to V3_FEATURE_COLUMNS_TOP_N (14 → 15)

In `src/crypto_trade/features_v3/__init__.py`, append `"efficiency_ratio_50"` to the
`V3_FEATURE_COLUMNS_TOP_N` tuple (14 → 15 features). Insert after
`regime_momentum_signed_5d` (last entry):

```python
"efficiency_ratio_50",   # iter-v3/043: Kaufman 1995 regime-quality signal
```

### Sub-fix 3: Implement compute_efficiency_ratio_50 in engineered_v3.py

In `src/crypto_trade/features_v3/engineered_v3.py`, add the new function:

```python
def compute_efficiency_ratio_50(df: pd.DataFrame) -> pd.Series:
    """Kaufman efficiency ratio (1995): direction strength over noise."""
    close = df["close"]
    direction = (close - close.shift(50)).abs()
    volatility = close.diff().abs().rolling(50, min_periods=50).sum()
    er = direction / (volatility + 1e-9)  # NaN-safe
    er = er.shift(1)  # past-only: bar t uses close[t-50..t-1]
    return er.fillna(0.0).clip(0.0, 1.0)
```

Dispatch it from `add_engineered_v3_features` AFTER `compute_regime_momentum_signed_5d`:

```python
df["efficiency_ratio_50"] = compute_efficiency_ratio_50(df)
```

Past-only proof:
- `close.shift(50)`: bar t uses close[t-50]. Past-only.
- `close.diff()`: bar t uses close[t] - close[t-1]. Past-only.
- `.rolling(50)`: sums bars [t-49..t]. Past-only.
- `.shift(1)` applied to ER: bar t's ER value uses close[t-51..t-1] from this shift.
  First valid ER appears at bar 51 (50-bar window + 1 shift). NaN fill: 0.0 (neutral).

### Sub-fix 4: Update _verify_feature_columns assertions in run_baseline_v3.py

Update the function to iter-v3/043 state:
- `len(V3_FEATURE_COLUMNS) == 15` (was 14 at iter-v3/042; adding efficiency_ratio_50)
- `"efficiency_ratio_50" in V3_FEATURE_COLUMNS` (new positive assertion)
- `DEFAULT_ATR_MULTIPLIERS == (2.0, 1.0)` (REVERTED from (1.5, 0.75))
- `V3_ATR_MULTIPLIERS_PER_SYMBOL` EMPTY (unchanged)
- `V3_FEATURES_PER_SYMBOL` EMPTY (unchanged)
- All 4 symbols return 15-feature fallback via `features_for_symbol`
- `atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0)` (REVERTED DEFAULT fallback)
- `atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0)` (REVERTED DEFAULT fallback)
- Negative assertions: tbr_zscore_30, vwap_dev_50, funding families, fracdiff_d05_close
  (universal list), vol_adj_autocorr, cross_asset_divergence_norm all ABSENT (preserved)
- `"regime_momentum_signed_5d" in V3_FEATURE_COLUMNS` (mandate still PRESENT; PASS)
- `"ret_skew_50" in V3_FEATURE_COLUMNS` (PRESENT; PASS)
- `"sym_vs_btc_ret_7d" in V3_FEATURE_COLUMNS` (PRESENT; PASS)

### Sub-fix 5: Update ITERATION_LABEL

In `run_baseline_v3.py`, change:
```python
ITERATION_LABEL = "v3-042"  →  "v3-043"
```

### Bundle state verification (what _verify_feature_columns must assert)

```
V3_FEATURE_COLUMNS_TOP_N: 15 features (14 + efficiency_ratio_50)                     PASS
DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0) (REVERTED from (1.5, 0.75) at iter-v3/042)       PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty)                                             PASS
V3_FEATURES_PER_SYMBOL: {} (empty)                                                    PASS
features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N (15 features)              PASS
features_for_symbol("ALGOUSDT") == V3_FEATURE_COLUMNS_TOP_N (15 features)             PASS
features_for_symbol("LDOUSDT") == V3_FEATURE_COLUMNS_TOP_N (15 features)              PASS
features_for_symbol("TRXUSDT") == V3_FEATURE_COLUMNS_TOP_N (15 features)              PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0) (REVERTED DEFAULT fallback)       PASS
atr_multipliers_for_symbol("BCHUSDT") == (2.0, 1.0) (REVERTED DEFAULT fallback)       PASS
"efficiency_ratio_50" IN V3_FEATURE_COLUMNS_TOP_N (NEW)                               PASS
"regime_momentum_signed_5d" IN V3_FEATURE_COLUMNS_TOP_N (mandate PRESENT)             PASS
"ret_skew_50" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                                   PASS
"sym_vs_btc_ret_7d" IN V3_FEATURE_COLUMNS_TOP_N (PRESENT)                             PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                         PASS
REQUIRED_GAP = 88 = (21+1) × 4                                                        PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+0.79):**
- Predicted band: [+0.50, +1.00]
- Median point estimate: +0.75
- Rationale: ATR reverts to the iter-v3/040 validated default, so the IS label
  distribution is IDENTICAL to iter-v3/040. The single new feature (ER-50) provides
  a regime-quality signal that projects onto training-label alignment: the model
  gains a continuous [0,1] measure of trend efficiency, allowing it to down-weight
  low-efficiency choppy regimes where the existing regime_momentum signal is less
  reliable. Modest IS lift expected; anchor +0.79 is the lower bound of this band.

**OOS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+1.77):**
- Predicted band: [+1.30, +2.00]
- Median point estimate: +1.65
- Rationale: ER-50 is a 15th feature added to the 14-feature validated anchor. OOS
  single-seed variance is ~±0.5 at this portfolio scale. A modest genuine lift from ER-50
  should manifest as OOS >= +1.60. Band is deliberately wide to reflect single-seed noise.

**OOS falsifier (pre-registered)**:
- If OOS Sharpe drops below +1.57 (more than 0.20 below iter-v3/040 anchor): ER-50 does
  not contribute a universal signal; NEGATIVE classification; drop efficiency_ratio_50
  from universal list at iter-v3/044.

**Pathway-A trigger (PROMISING)**:
- IS Sharpe >= +0.89 (>= +0.10 lift over anchor) AND OOS Sharpe >= +1.57.

**Pathway-B trigger (PROMISING-INERT)**:
- IS Sharpe in [+0.50, +0.89] (within ±0.29 of anchor) AND OOS >= +1.57.

**Pathway-C trigger (NEGATIVE)**:
- OOS Sharpe < +1.57 (drops > 0.20 below anchor).
- Action: drop efficiency_ratio_50 from universal list at iter-v3/044.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.
**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward from iter-v3/040.
**R3 (OOD detection)**: zscore_threshold=2.0 unchanged. Feature subspace expands from
14 → 15 features; Mahalanobis covariance space adds one dimension. Expected effect on
OOD firing rate: < 5% relative (one new uncorrelated feature adds minimal joint-space
volume change in 15-D vs 14-D).

**15th feature addition risk**: adding one feature to a 14-feature Optuna-tuned model
shifts the colsample_bytree landscape. With `colsample_bytree` Optuna-tuned (NOT
hardcoded 1.0), the sampler has one more feature to include/exclude per tree. Net effect
on hyperparameter sensitivity: marginal (15 → 14+1 adds one degree of freedom). The
n_trials=35 budget is sufficient for colsample_bytree to stabilize given prior EXPLORATION
data points at this budget.

**IS trade-rate stability**: ATR reverts to (2.0, 1.0); label distribution identical to
iter-v3/040. IS trade count expected within ±5% of iter-v3/040. If deviation > 20%,
investigate parquet freshness (stale features producing incorrect ER-50 values).

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/040 baseline unchanged. No gate parameters
are modified. ATR multipliers revert to (2.0, 1.0); the risk gates are unchanged.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0 | 15-feature space (NEW: +ER-50) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

**Predicted OOD fire rate**: within ±10% of iter-v3/040 baseline. If ER-50 adds a near-zero
IC vs the OOD feature space (expected |IC| < 0.3 vs all existing features), the joint Mahal-
anobis distribution is minimally changed.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (NEGATIVE — ER-50 signal is too slow at 8h cadence)**:
At 50-bar × 8h = 400h = ~17 calendar days, ER-50 captures efficiency over a 2.5-week
window. At 8h cadence, 2.5 weeks of price movement is dominated by crypto market regime
cycles (BTC alt-season pumps, consolidation). The signal may be too slow relative to the
21-candle (7-day) triple-barrier timeout: by the time ER-50 registers an efficient trend,
the trade's outcome is already determined within the 7-day window. LightGBM would learn
to down-weight ER-50 → rank 15/15 → INERT outcome.

**Second plausible failure mode (PROMISING-INERT — ER-50 is redundant with hurst_100)**:
Both ER-50 and hurst_100 measure trend persistence. If their IS IC > 0.50 (moderate
correlation), LightGBM's colsample_bytree may substitute one for the other without
adding net information. Feature importance would show one rising and the other falling;
aggregate IS Sharpe is flat (parsimony-neutral).

**Third plausible failure mode (concentration shift — ER-50 benefits one symbol)**:
ER-50 may be genuinely predictive for TRX (high-volume, lower-volatility) but not BCH/LDO.
If TRX model learns to use ER-50 as a primary split while BCH/LDO do not, OOS PnL
concentration shifts toward TRX. Engineering report Phase 7: per-symbol feature importance
audit of ER-50 rank across all 4 symbols.

**What the gates should catch**:
- Gate 6 (OOD): 15-feature space slightly expands Mahalanobis volume. Firing rate
  expected ±10% vs iter-v3/040 baseline.
- Gate 5 (R2 drawdown): ATR reverts to (2.0, 1.0); IS label distribution restores to
  iter-v3/040 norm. If R2 fires more than at iter-v3/040, investigate.

**Behavioral effect predictor**: predicted IS trade count delta < 5% vs iter-v3/040.
Falsifier: > 20% triggers investigation.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification criteria
(pre-registered before backtest runs):

**PATH A — PROMISING**:
  IS Sharpe >= +0.89 (>= +0.10 lift over iter-v3/040 anchor ~+0.79) AND
  OOS Sharpe >= +1.57 (maintained within -0.20 of iter-v3/040 anchor ~+1.77).
  Classification: PROMISING. ER-50 contributes a universal regime-quality signal.
  Catalog entry: candidate for next CONFIRMATION bundle.

**PATH B — PROMISING-INERT**:
  IS Sharpe in [+0.50, +0.89] (within ±0.29 of anchor) AND OOS Sharpe >= +1.57.
  Classification: PROMISING-INERT. ER-50 is parsimony-neutral; regime-quality signal
  does not improve aggregate IS Sharpe at 50-bar lookback. May retest at ER-20 or
  ER-100 as alternative lookback (separate EXPLORATION required).

**PATH C — NEGATIVE**:
  OOS Sharpe < +1.57 (drops > 0.20 below anchor).
  Classification: NEGATIVE. ER-50 hurts OOS aggregate.
  Action: drop efficiency_ratio_50 from universal list at iter-v3/044.
  Catalog entry: Kaufman ER at 50-bar lookback FALSIFIED for this universe.

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A requires IS >= +0.89 AND OOS >= +1.57
- PATH B requires IS in [+0.50, +0.89] AND OOS >= +1.57
- PATH C requires OOS < +1.57

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/042 / iter-v3/040 / iter-v3/028 reproducibility stamp.
No new libraries introduced. efficiency_ratio_50 uses only pandas built-ins (shift, diff,
abs, rolling, sum, clip, fillna) — no new dependencies.

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
