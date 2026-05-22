# Iteration v3-041 — Research Brief

**Type**: EXPLORATION (Cycle 3 #2 of 10)
**Track**: v3 (rigor arm) — forty-first iteration
**Branch**: `iteration-v3/041` (off iter-v3/040 head)
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
Cycle: 3 — #2 of 10
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Spec: uv run python run_baseline_v3.py --seeds 1
  - ENSEMBLE_SIZE=5 (auto; non-exploration inner ensemble)
  - n_trials=35 (default)
  - colsample_bytree Optuna-tunable (NOT hardcoded 1.0)
  - outer_seeds=1 (EXPLORATION-spec)
Single axis: UNIVERSAL FEATURE PRUNING — drop the 3 lowest-importance features
  from V3_FEATURE_COLUMNS_TOP_N (14 → 11). All other config (4 symbols, ATR
  defaults, gates, n_trials) UNCHANGED from iter-v3/040 anchor.
Predicted classification: PROMISING (IS lift) or PROMISING-INERT (parsimony neutral)
```

**Context**: iter-v3/040 reproduced the iter-v3/029 single-seed cycle 3 anchor
(IS Sharpe ~+0.79 / OOS ~+1.77) bit-identically by clearing all per-symbol
customizations. iter-v3/041 starts cycle 3 axis exploration with the most
information-theoretic axis available: drop the lowest-information features.
If LightGBM importance signals reflect actual edge, dropping bottom-importance
features should leave OOS edge intact while reducing the Optuna search space
(fewer features = fewer colsample_bytree noise picks, less hyperparameter
overfitting risk per Bailey-LdP DSR framework).

---

## Section 1 — Hypothesis

Dropping the 3 lowest-importance features (`regime_momentum_signed_5d`,
`sym_vs_btc_ret_7d`, `ret_skew_50`) from V3_FEATURE_COLUMNS_TOP_N (14 → 11) lifts
IS Sharpe toward +1.0 by reducing Optuna search-space noise (fewer
colsample_bytree picks land on low-signal features) and maintains OOS Sharpe at
or near the iter-v3/029/040 anchor (~+1.77) because removed features carry only
17.6% of total LightGBM split-importance and contribute marginal generalizable
edge.

---

## Section 2 — IS-Only Numerical Evidence

### 2.1 — iter-v3/028 Multi-Seed Portfolio Importance (canonical source)

From `reports-v3/iteration_v3-028/in_sample/model_importance_last_month_portfolio.csv`
(committed; per task spec the canonical multi-seed baseline). Full 14-feature
ranking with KEEP/DROP action:

| rank_desc | feature | importance | pct_of_top | action |
|---:|---|---:|---:|---|
| 1  | range_realized_vol_50      | 604.4 | 100.00 | KEEP |
| 2  | vwap_dev_20                | 586.0 |  96.96 | KEEP |
| 3  | ret_skew_200               | 571.4 |  94.54 | KEEP |
| 4  | ret_kurt_50                | 564.4 |  93.38 | KEEP |
| 5  | max_dd_window_50           | 508.4 |  84.12 | KEEP |
| 6  | ret_kurt_200               | 507.2 |  83.92 | KEEP |
| 7  | ema_spread_atr_20          | 496.4 |  82.13 | KEEP |
| 8  | hurst_diff_100_50          | 490.6 |  81.17 | KEEP |
| 9  | ret_autocorr_lag1_50       | 459.0 |  75.94 | KEEP |
| 10 | btc_ret_14d                | 427.0 |  70.65 | KEEP |
| 11 | hurst_100                  | 421.0 |  69.66 | KEEP |
| 12 | **ret_skew_50**            | **412.8** | **68.30** | **DROP** |
| 13 | **sym_vs_btc_ret_7d**      | **398.0** | **65.85** | **DROP** |
| 14 | **regime_momentum_signed_5d** | **390.4** | **64.59** | **DROP** |

Combined dropped importance: 1201.2 / 6837.0 = **17.6% of total split count**.
Combined kept importance: 5635.8 / 6837.0 = **82.4%**.

### 2.2 — Cross-Verification Against iter-v3/040 Single-Seed Anchor

From `reports-v3/iteration_v3-040/in_sample/model_importance_last_month_portfolio.csv`
(cycle 3 anchor — same 14 features as iter-v3/028, single-seed):

| rank_desc | feature | importance | iter-v3/028 rank |
|---:|---|---:|---:|
| 14 | regime_momentum_signed_5d  | 454.0 | 14 (BOTH BOTTOM) |
| 13 | ret_autocorr_lag1_50       | 577.0 |  9 |
| 12 | sym_vs_btc_ret_7d          | 606.0 | 13 (BOTH BOTTOM) |

Bottom-3 concordance: 2/3 features agree (`regime_momentum_signed_5d` and
`sym_vs_btc_ret_7d`). The third position diverges: iter-v3/028 has `ret_skew_50`
at rank 12; iter-v3/040 has `ret_autocorr_lag1_50` at rank 13. Per the task spec,
iter-v3/028 (multi-seed) is the canonical source — `ret_skew_50` is the third
drop candidate.

`regime_momentum_signed_5d` is rank 14 in BOTH rankings — strongest evidence that
the engineered feature established at iter-v3/025 (per
`feedback_v3_engineered_features_proven.md`) does not retain measured importance
in the post-revert iter-v3/028 / iter-v3/040 4-symbol context. The
MUST-be-present mandate from iter-v3/025 is being revisited via this EXPLORATION
axis, which is methodologically valid: EXPLORATIONs can falsify any prior
assumption (that is their purpose). If iter-v3/041 IS Sharpe regresses below
iter-v3/040 anchor, the mandate is upheld; if IS lifts, the mandate is falsified.

### 2.3 — Behavioral-Effect Predictor (per `feedback_v3_axis_saturation_predictor.md`)

Predicted IS trade count delta vs iter-v3/040 anchor: **-3% to +5%**.

Mechanism: LightGBM split-count is approximately proportional to feature importance.
Dropping 3 features whose combined importance is 17.6% of total redirects ~17.6%
of decision splits to the remaining 11 features. The model continues to make
similar TP/SL crossings; trade frequency stays within ±5%.

Iter-v3/040 IS trade count baseline (from `reports-v3/iteration_v3-040/in_sample/per_symbol.csv`):
will be confirmed in Phase 7 evaluation.

**Falsifier (per `feedback_v3_axis_saturation_predictor.md`)**: if observed
|IS trade delta| > 30 trades vs iter-v3/040 anchor, this exceeds the predicted
band and triggers axis-saturation diagnostic (the change is doing more than
expected — investigate whether feature removal caused unexpected gate firing
shifts, e.g., OOD distribution drift or hit-rate gate changes).

### Analysis script

`analysis/iteration_v3-041/bottom3_features_eda.py` (committed SHA `c2e2712`).
IS-only ranking script with KEEP/DROP manifest. Cross-checks both iter-v3/028
multi-seed and iter-v3/040 single-seed importance CSVs. Outputs
`iter028_importance_with_actions.csv` (committed in same SHA).

---

## Section 3 — Proposed Changes

### Sub-fix 1: Update `V3_FEATURE_COLUMNS_TOP_N` (drop bottom-3)

In `src/crypto_trade/features_v3/__init__.py`, remove three entries from the
14-feature universal tuple (the 3 lowest by iter-v3/028 portfolio importance):

```python
# DROPPED at iter-v3/041 (universal feature pruning EXPLORATION):
#   - "ret_skew_50"               (rank 12, importance 412.8 — bottom-3)
#   - "sym_vs_btc_ret_7d"         (rank 13, importance 398.0 — bottom-3)
#   - "regime_momentum_signed_5d" (rank 14, importance 390.4 — bottom-3)
# Combined importance 17.6% of total. Per analysis/iteration_v3-041/bottom3_features_eda.py
# (SHA c2e2712). The universal list shrinks 14 → 11 features.
```

The remaining 11 features:

```
max_dd_window_50, ema_spread_atr_20, ret_kurt_50, ret_skew_200,
range_realized_vol_50, hurst_diff_100_50, ret_kurt_200, hurst_100,
btc_ret_14d, vwap_dev_20, ret_autocorr_lag1_50
```

### Sub-fix 2: Update `_verify_feature_columns` in `run_baseline_v3.py`

Rewrite assertions to iter-v3/041 state:
- `len(V3_FEATURE_COLUMNS) == 11` (was 14)
- `"ret_skew_50" not in V3_FEATURE_COLUMNS` (newly dropped — explicit assertion)
- `"sym_vs_btc_ret_7d" not in V3_FEATURE_COLUMNS` (newly dropped)
- `"regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS` (newly dropped — mandate
  REVOKED at iter-v3/041 per universal-pruning EXPLORATION axis)
- All 4 symbols (BCH/LDO/TRX/ALGO) return 11-feature fallback
- `V3_FEATURES_PER_SYMBOL` remains EMPTY (unchanged from iter-v3/040)
- `V3_ATR_MULTIPLIERS_PER_SYMBOL` remains EMPTY (unchanged)
- LDO ATR multiplier remains (2.0, 1.0) default
- All prior negative assertions (tbr_zscore_30, vwap_dev_50, funding family, fracdiff,
  vol_adj_autocorr, cross_asset_divergence_norm) PRESERVED

The previous assertion:
```python
if "regime_momentum_signed_5d" not in V3_FEATURE_COLUMNS:
    raise RuntimeError(...)
```
is INVERTED at iter-v3/041 to:
```python
if "regime_momentum_signed_5d" in V3_FEATURE_COLUMNS:
    raise RuntimeError(...)
```

### Sub-fix 3: Update ITERATION_LABEL

In `run_baseline_v3.py`, change:
```python
ITERATION_LABEL = "v3-040"  →  "v3-041"
```

### Sub-fix 4: Adversarial Test Update

Rewrite `tests/features_v3/test_features_for_symbol.py` for the 11-feature stack:
- `test_universal_list_is_11`: `len(V3_FEATURE_COLUMNS_TOP_N) == 11`
- `test_ret_skew_50_not_in_universal_list`: `"ret_skew_50" not in TOP_N`
- `test_sym_vs_btc_ret_7d_not_in_universal_list`: `"sym_vs_btc_ret_7d" not in TOP_N`
- `test_regime_momentum_not_in_universal_list`: `"regime_momentum_signed_5d" not in TOP_N`
- `test_bch_fallback_11`: `len(features_for_symbol("BCHUSDT")) == 11`
- `test_algo_fallback_11`: `len(features_for_symbol("ALGOUSDT")) == 11`
- `test_ldo_fallback_11`: `len(features_for_symbol("LDOUSDT")) == 11`
- `test_trx_fallback_11`: `len(features_for_symbol("TRXUSDT")) == 11`
- All other unchanged (V3_FEATURES_PER_SYMBOL empty; V3_ATR_MULTIPLIERS_PER_SYMBOL empty;
  LDO ATR default; fracdiff/cross_asset_divergence/vol_adj_autocorr absent from TOP_N)

### Sub-fix 5: Document the dropped features

Inline tuple comments in `features_v3/__init__.py` will record the iter-v3/041 drop
rationale, importance numbers, and the source script SHA, matching the historical
documentation pattern (iter-v3/008 vwap_dev_50 drop, iter-v3/016 tbr_zscore_30 drop, etc.).

### Bundle state verification (what `_verify_feature_columns` must assert after sub-fixes)

```
V3_FEATURE_COLUMNS_TOP_N: 11 features                                         PASS
V3_FEATURES_PER_SYMBOL: {} (empty — unchanged from iter-v3/040)                PASS
V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty — unchanged)                          PASS
features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N (11 features)       PASS
features_for_symbol("ALGOUSDT") == V3_FEATURE_COLUMNS_TOP_N (11 features)      PASS
features_for_symbol("LDOUSDT") == V3_FEATURE_COLUMNS_TOP_N (11 features)       PASS
features_for_symbol("TRXUSDT") == V3_FEATURE_COLUMNS_TOP_N (11 features)       PASS
atr_multipliers_for_symbol("LDOUSDT") == (2.0, 1.0)                            PASS
"regime_momentum_signed_5d" NOT in V3_FEATURE_COLUMNS_TOP_N (NEW; mandate revoked) PASS
"sym_vs_btc_ret_7d" NOT in V3_FEATURE_COLUMNS_TOP_N (NEW)                      PASS
"ret_skew_50" NOT in V3_FEATURE_COLUMNS_TOP_N (NEW)                            PASS
V3_MODELS = (BCH, LDO, TRX, ALGO) — 4 symbols                                  PASS
REQUIRED_GAP = 88 = (21+1) × 4                                                 PASS
```

---

## Section 4 — Expected OOS Impact

**IS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+0.79):**
- Predicted band: [+0.85, +1.15]
- Median point estimate: +1.00
- Rationale: Pruning 17.6% of split-importance forces remaining 82.4% of useful
  signal into 11 columns. Reduced colsample_bytree noise from low-signal columns
  → tighter Optuna trial-to-trial variance → higher mean IS Sharpe within band.
  Lift size (~+0.21) bounded by the realistic limit of "removing 17.6% noise"
  in a 35-trial Optuna search.

**OOS Sharpe prediction (single-seed, vs iter-v3/040 single-seed anchor ~+1.77):**
- Predicted band: [+1.50, +2.00]
- Median point estimate: +1.75
- Rationale: 11 features still cover 82.4% of split-importance — generalizable
  edge preserved. OOS variance unchanged within ±0.25.

**OOS falsifier (pre-registered)**:
- If OOS Sharpe drops > 0.20 below iter-v3/040 anchor (i.e., OOS < +1.55):
  the dropped features carried real signal that did not show in IS importance
  ranking. Revert the prune; the bottom-3 signal exists despite low
  split-frequency (possibly via deep-tree interactions iter-v3/041's depth-3-5
  tree budget cannot capture).

**Pathway-A trigger (PROMISING)**:
- IS Sharpe lift ≥ +0.10 (i.e., IS >= +0.89) AND OOS maintained (>= +1.55).
- Classification: PROMISING — pruning is a cycle 3 main edge ingredient. Bundle
  candidate for next CONFIRMATION.

**Pathway-B trigger (PROMISING-INERT)**:
- IS Sharpe within ±0.10 of iter-v3/040 anchor (IS in [+0.69, +0.89]) AND
  OOS maintained (>= +1.55).
- Classification: PROMISING-INERT — pruning is parsimony-neutral. The 14-feature
  set is not over-determined; the 11-feature set is not under-determined. Cycle 3
  catalog entry: pruning has no measurable effect on this model architecture.

**Pathway-C trigger (NEGATIVE)**:
- OOS Sharpe drops > 0.20 below anchor (OOS < +1.55).
- Classification: NEGATIVE — pruning destroyed real signal. Revert the prune.
  Catalog entry: bottom-3 by importance carry signal not captured by importance
  rank; importance-based pruning is FALSIFIED for this model.

---

## Section 5 — Risk Mitigation

**R1 (cooldown)**: unchanged. Cooldown=2 candles post-trade per symbol.
**R2 (drawdown scaling)**: unchanged. R2 gate parameters carried forward.
**R3 (OOD detection)**: zscore_threshold=2.0 unchanged.

**OOD distribution shift risk**: removing `regime_momentum_signed_5d`,
`sym_vs_btc_ret_7d`, and `ret_skew_50` changes the 11-feature Mahalanobis
covariance vs the prior 14-feature one. R3 gate will fire on a different
feature subspace. Expected effect: comparable OOD firing rate (the dropped
features are low-importance and contribute marginal Mahalanobis variance).
If R3 firing rate at iter-v3/041 vs iter-v3/040 differs by >50% (relative),
investigate whether the prune induced an unexpected covariance regime shift.

**Concentration risk**: dropping `regime_momentum_signed_5d` removes the
engineered cross-asset feature that may have been anchoring TRX or LDO model
edge per iter-v3/025 evidence. Expected per-symbol PnL distribution shift bounded
within ±10% (still well under the 30% concentration floor). If any symbol
exceeds 50% of OOS PnL, escalate as a concentration alert.

**Mandate-revocation risk**: `feedback_v3_engineered_features_proven.md` mandated
KEEP `regime_momentum_signed_5d` since iter-v3/025. iter-v3/041 EXPLORATION
revisits this mandate. If results are PROMISING-INERT or PROMISING (Pathway A/B),
the mandate is empirically falsified at the iter-v3/040 4-symbol anchor and a
subsequent CONFIRMATION can either (a) validate the mandate revocation if multi-
seed lift holds, or (b) reinstate the mandate if multi-seed reveals lift was
single-seed lottery. If Pathway-C (NEGATIVE), the mandate is upheld and
`regime_momentum_signed_5d` is restored at iter-v3/042.

---

## Section 6 — Risk Management Design (7-Primitive Gate Table)

All 7 risk gates carried forward from iter-v3/040 baseline unchanged. No gate
parameters are modified in this EXPLORATION.

| Gate | Type | Parameter | Change |
|---|---|---|---|
| 1 — BTC trend | BtcTrendFilterConfig | lookback=42, threshold=15% | None |
| 2 — Hit rate | HitRateGateConfig | window=20, sl_threshold=0.65 | DISABLED (unchanged) |
| 3 — ADX gate | ADX regime filter | threshold=20 (v3 default) | None |
| 4 — Hurst regime | hurst_100 > 0.5 gate | implicit feature; STILL PRESENT | None |
| 5 — Drawdown brake | R2 cumulative | per-model PnL tracking | None |
| 6 — OOD gate | Mahalanobis z-score | zscore_threshold=2.0 | Feature subspace 14→11 (NOTE) |
| 7 — Liquidity floor | NATR floor | NATR >= 0.5% | None |

NOTE on Gate 6: the OOD Mahalanobis distance is computed over the input feature
columns — the column count drops 14 → 11 at iter-v3/041 but the gate threshold
(z-score = 2.0) is unchanged. Empirical firing rate may shift modestly per the
Section 5 OOD risk note.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible failure mode (PROMISING-INERT)**:
The 17.6% importance drop is too small to materially change Optuna trial outcomes
within a 35-trial budget at single-seed. IS Sharpe stays within ±0.10 of
iter-v3/040 anchor; OOS unchanged. Cycle 3 records pruning as parsimony-neutral.

**Second plausible failure mode (NEGATIVE-real-signal-loss)**:
`regime_momentum_signed_5d` carried genuine signal at iter-v3/025 (OOS +0.84
attributable lift) that does not show up in iter-v3/028 importance ranking
because:
- importance ranks features by split count, not by depth/leaf-level information
  gain
- engineered features that fire deep in the tree have low split count but may
  drive accurate end-of-tree predictions
If OOS drops > 0.20, this hypothesis is confirmed and the mandate stands.

**Third plausible failure mode (PROMISING-FALSE-LIFT)**:
IS Sharpe lifts ≥ +0.10 BUT OOS does not (single-seed lottery — 1 outer seed
with 35 trials × 11 features fits the IS noise tighter). Caught at next
CONFIRMATION via 5-inner-seed × 2-outer-seed multi-seed validation.

**What the gates should catch**:
- Gate 6 (OOD): firing rate changes > 50% relative trigger Section 5 alert.
- Gate 5 (R2 drawdown): if per-model PnL trajectory shifts unexpectedly, R2 brake
  fires earlier.

**Behavioral effect predictor**: predicted IS trade count delta -3% to +5%
vs iter-v3/040. Falsifier: if observed |IS trade delta| > 30 trades, escalate.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is an EXPLORATION iteration. MERGE gates do NOT apply. Classification
criteria (pre-registered before backtest runs):

**PATH A — PROMISING**:
  IS Sharpe lift >= +0.10 vs iter-v3/040 anchor (IS >= +0.89) AND
  OOS Sharpe maintained (>= +1.55).
  Classification: PROMISING. Pruning is a cycle 3 main edge ingredient.
  Catalog entry: candidate for next CONFIRMATION (iter-v3/042 or later).

**PATH B — PROMISING-INERT**:
  IS Sharpe within [-0.10, +0.10] of iter-v3/040 anchor (IS in [+0.69, +0.89])
  AND OOS Sharpe maintained (>= +1.55).
  Classification: PROMISING-INERT. Pruning is parsimony-neutral.
  Catalog entry: 14 vs 11 feature counts have no measurable effect at this scale.

**PATH C — NEGATIVE**:
  OOS Sharpe drops > 0.20 below iter-v3/040 anchor (OOS < +1.55).
  Classification: NEGATIVE — pruning dropped real signal.
  Catalog entry: importance-based pruning FALSIFIED for this model.
  Action: revert the prune at iter-v3/042; restore `regime_momentum_signed_5d`
  per the upheld feedback_v3_engineered_features_proven.md mandate.

**Pre-registered classification thresholds (locked before backtest)**:
- PATH A requires IS lift >= +0.10 AND OOS >= +1.55
- PATH B requires |IS delta| ≤ 0.10 AND OOS >= +1.55
- PATH C requires OOS < +1.55

These thresholds are LOCKED and cannot be post-hoc renegotiated.

---

## Section 9 — Library Stack Declaration

All versions identical to iter-v3/040 / iter-v3/039 / iter-v3/028 reproducibility stamp:

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
| pytest | 9.0.2 | pyproject.toml dev dep |

**fracdiff (PyPI package)**: UNAVAILABLE. Pure-numpy inline implementation
`compute_fracdiff_d05_close` in `src/crypto_trade/features_v3/engineered_v3.py`
preserved as dead code (column still computed in parquets at iter-v3/041 but
NOT a model input — same as iter-v3/040). No new library dependencies.
