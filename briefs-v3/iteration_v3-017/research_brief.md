# Iteration v3-017 — Research Brief

**Type**: EXPLORATION (TENTH and FINAL EXPLORATION before first v3 CONFIRMATION; MANDATORY NEW labeling architecture per `feedback_v3_iter017_metalabeling_mandate.md` FIRED at iter-v3/016 Critic FINAL)
**Track**: v3 (rigor arm) — seventeenth iteration
**Branch**: `iteration-v3/017` (off `iteration-v3/016` head; EDA commit `d47163b` ships before this brief)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 10             # SET BY --exploration default (per M1 + per M2)
colsample_bytree = 1.0             # HARDCODED by --exploration (M1 path; M2 inherits)
OOS_CUTOFF_MS    = 1742774400000   # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–016 briefs / engineering reports / Critic / diaries; iter-v3/017 EDA script `analysis/iteration_v3-017/metalabeling_eda.py` outputs (committed at SHA `d47163b` BEFORE this brief). The EDA reads ONLY iter-v3/013's IS roster (already disclosed) for M2 positive-class prior calibration — generates no new OOS information.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (NEW labeling architecture, MANDATORY per pre-committed rule)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW labeling architecture (Category 3 — meta-labeling per López de Prado AFML Ch. 3)
Cadence: EXPLORATION #10 of 10 (FINAL; after this iteration regardless of verdict, first v3 CONFIRMATION can launch)
This iteration NEVER updates BASELINE_V3.md.
Pre-committed: this axis is FORCED by feedback_v3_iter017_metalabeling_mandate.md (FIRED at iter-v3/016). Cannot be renegotiated.
References: feedback_v3_iter017_metalabeling_mandate.md, feedback_structural_over_knob_exploration.md, feedback_axis_saturation_predictor.md
```

**Justification**: Per `feedback_v3_iter017_metalabeling_mandate.md` (FIRED at iter-v3/016 Critic FINAL): iter-v3/017 MUST be a NEW labeling architecture single-axis EXPLORATION. Per `feedback_structural_over_knob_exploration.md` axis priority order, NEW labeling architecture (Category 3) is the unique untested top-priority category. Triple-barrier label has been fixed since iter-v3/001; only ATR multipliers were tuned at iter-v3/010 (knob-tuning, not architecture). Meta-labeling per AFML Ch. 3 is preferred over fixed-horizon return labels because:
1. **Structural compoundability**: M1+M2 architecture does NOT invalidate the existing 13-feature stack — M2 changes how features are used, not what they are.
2. **AFML Ch. 3 framework is well-trodden**: lower implementation surprise.
3. **Probabilistic confidence score**: M2's posterior naturally produces a confidence signal usable for fractional Kelly position sizing in future CONFIRMATION (foundation, not used in this EXPLORATION).

After this iteration the catalog has 9 unique axis representations: features × 2 (007, 009) + labeling × 1 (010) + gate-zscore × 1 (011) + gate-btc-trend × 1 (012) + universe × 1 (013) + gate-adx × 1 CLOSED (014) + NEW feature family × 1 (015) + NEW model architecture × 1 CLOSED-AT-CONFIG (016) + **NEW labeling architecture × 1 (017)**, satisfying the v3 cadence rule and unblocking first CONFIRMATION launch.

---

## Section 1 — Hypothesis

Adding a meta-labeling secondary classifier (M2) on top of the existing M1 (LightGbmStrategy on V3_FEATURE_COLUMNS, triple-barrier labels) will improve IS Sharpe by structurally filtering out low-confidence M1 predictions: M2 predicts "did this M1-positive prediction reach TP within timeout?" using the same 13 features plus M1's prediction probability, and trades fire only when M2 confidence ≥ 0.5.

**Mechanism (López de Prado AFML Ch. 3)**: Triple-barrier labels create a binary direction signal that is noise-heavy at ~36% IS WR (iter-v3/013 baseline). M2's job is precision (filter false-positives), not direction. Because M2 is trained on M1-positive bars only with labels = "TP-first", M2 sees a 33.97% positive-class prior (per EDA §2.1) and can learn the difference between "M1 says go and price actually walks to TP" versus "M1 says go but price walks to SL or stalls into timeout." If M2 learns generalizable confidence, IS Sharpe lifts via per-trade economics improvement that compensates for the reduced trade count.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-017/metalabeling_eda.py` (committed at SHA `d47163b` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (already-disclosed iter-v3/013 IS trade roster; M2 prior calibration only — no new OOS information generated):
- `reports-v3/iteration_v3-013/in_sample/trades.csv` — 209 IS trade rows (every row is an M1-positive prediction)

**Outputs** (committed alongside the script at SHA `d47163b`):
- `analysis/iteration_v3-017/m2_label_distribution.csv` — M2 positive-class prior overall + per-symbol
- `analysis/iteration_v3-017/exit_reason_breakdown.csv` — TP/SL/timeout exit reason breakdown
- `analysis/iteration_v3-017/synthesis.md` — narrative + M2 label generation pseudocode + saturation band

### 2.1 M2 architecture mathematical specification

Let $X_t \in \mathbb{R}^{13}$ be the V3_FEATURE_COLUMNS vector at candle $t$. M1 is the existing primary model:

$$\text{M1}: X_t \to (\hat{p}^{\text{long}}_t, \hat{p}^{\text{short}}_t), \quad \text{direction}_t = \arg\max(\hat{p}^{\text{long}}_t, \hat{p}^{\text{short}}_t)$$

M1 fires a positive prediction (a candidate trade) at $t$ iff $\max(\hat{p}^{\text{long}}_t, \hat{p}^{\text{short}}_t) \geq \tau_{\text{M1}}$ where $\tau_{\text{M1}}$ is M1's Optuna-tuned confidence threshold. The set of M1-positive bars $\mathcal{T}^{\text{M1+}} = \{t : \max(\hat{p}_t) \geq \tau_{\text{M1}}\}$.

For each $t \in \mathcal{T}^{\text{M1+}}$, the triple-barrier outcome on the M1-predicted direction yields a binary M2 label:

$$y^{\text{M2}}_t = \begin{cases} 1 & \text{if M1's direction at } t \text{ closes at TP barrier first within timeout} \\ 0 & \text{if SL barrier hits first OR timeout closes the position} \end{cases}$$

M2's input features at $t$:

$$Z_t = (X_t, \max(\hat{p}^{\text{long}}_t, \hat{p}^{\text{short}}_t)) \in \mathbb{R}^{14}$$

M2 is `lgb.LGBMClassifier(objective='binary', is_unbalance=True)` with the same Optuna search space as M1. M2 prediction:

$$\text{M2}: Z_t \to \hat{p}^{\text{TP}}_t \in [0, 1]$$

Final trading rule:

$$\text{trade}(t) = \mathbb{1}\{t \in \mathcal{T}^{\text{M1+}}\} \cdot \mathbb{1}\{\hat{p}^{\text{TP}}_t \geq 0.5\}$$

with direction inherited from M1 and TP/SL barriers inherited from iter-v3/013's ATR(2.0/1.0) labeling. The threshold $0.5$ is the standard binary-classification Bayes-optimal cutoff and is **NOT tuned** (would introduce a second axis; brief stays single-axis on architecture).

### 2.2 M2 label distribution on iter-v3/013 IS roster (positive-class prior calibration)

| Scope | N M1-positive bars | N M2=1 (TP hit) | M2 positive-class rate |
|---|---:|---:|---:|
| **Overall** | **209** | **71** | **33.97%** |
| BCHUSDT | 100 | 35 | 35.00% |
| LDOUSDT | 21 | 9 | 42.86% |
| TRXUSDT | 88 | 27 | 30.68% |

**Calibration**: M2 positive-class prior ≈ **33.97%** overall — consistent with iter-v3/013's IS WR ~36% (slightly below WR because TP rate counts only TP-barrier hits, while WR includes timeouts that closed positive). Per-symbol prior ranges from 30.68% (TRX) to 42.86% (LDO) — moderate heterogeneity. M2 should learn a useful generalizing signal (the gap between symbols is informative; M2 can use M1 confidence + features to distinguish high-prior from low-prior bars).

The 33.97% prior is favorable for a binary classifier: it is sufficiently far from 50/50 that `is_unbalance=True` matters (LightGBM upweights the minority TP class to balance gradient updates), but not so extreme that the classifier degenerates to "predict 0 always" (which would give ~66% accuracy but zero precision on the 1-class).

### 2.3 Exit reason breakdown (full)

| Scope | N | take_profit | stop_loss | timeout | TP % | SL % | Timeout % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Overall | 209 | 71 | 124 | 14 | 33.97 | 59.33 | 6.70 |
| BCHUSDT | 100 | 35 | 55 | 10 | 35.00 | 55.00 | 10.00 |
| LDOUSDT | 21 | 9 | 11 | 1 | 42.86 | 52.38 | 4.76 |
| TRXUSDT | 88 | 27 | 58 | 3 | 30.68 | 65.91 | 3.41 |

Note: 124/209 = 59.33% of M1-positive trades hit SL — M2 should be highly motivated to filter these, but only insofar as M1's SL-hits are predictable from features. If SL-hits are randomly distributed across the M1-positive bars (which is the null hypothesis under "M1 has no precision-residual signal"), M2 will not learn anything useful and PATH B (NEGATIVE-no-effect) fires.

### 2.4 M2 label generation pseudocode (training-time integration)

At each walk-forward month split:

```python
# Step 1: train M1 (existing pipeline, unchanged)
m1_model = optimize_and_train(feat_train, y_M1, ...)

# Step 2: M1 inference on training window to get positive-prediction set
m1_proba = m1_model.predict_proba(feat_train)  # [n, 2]
m1_pred = np.argmax(m1_proba, axis=1)          # 0=short, 1=long
m1_confidence = m1_proba.max(axis=1)
m1_positive_mask = m1_confidence >= m1.confidence_threshold

# Step 3: M2 labels — read triple-barrier outcomes from labeler's long_pnls/short_pnls
# (already computed by label_trades(); we just bucket by direction & TP-hit)
m2_labels = np.zeros(n, dtype=int)
for i in np.where(m1_positive_mask)[0]:
    direction = +1 if m1_pred[i] == 1 else -1
    outcome_pnl = long_pnls[i] if direction == +1 else short_pnls[i]
    # M2=1 iff TP barrier hit (long_pnl ≈ tp_pnl_pct - fee, short_pnl ≈ tp_pnl_pct - fee).
    # Use a tolerance; tp_pnl_pct - fee ≈ tp_pct - 0.1.
    m2_labels[i] = 1 if outcome_pnl >= (tp_pnl_pct - fee_pct - 0.5) else 0

# Step 4: M2 features — V3 features + M1's confidence as 14th feature
m2_features = np.zeros((n, 14), dtype=np.float64)
m2_features[m1_positive_mask, :13] = feat_train[m1_positive_mask]
m2_features[m1_positive_mask, 13] = m1_confidence[m1_positive_mask]

# Step 5: train M2 on M1-positive subset only (M2 sees no M1-negative bars)
m2_train_idx = np.where(m1_positive_mask)[0]
m2_model = optimize_and_train_m2(
    m2_features[m2_train_idx],
    m2_labels[m2_train_idx],
    ... # same Optuna search space as M1
)
```

At prediction time:

```python
def get_signal_metalabeled(symbol, open_time):
    m1_signal = m1.get_signal(symbol, open_time)
    if m1_signal is NO_SIGNAL:
        return NO_SIGNAL
    feat = lookup_features(symbol, open_time)         # 13-vector
    m2_input = np.concatenate([feat, [m1.last_confidence]])  # 14-vector
    m2_proba = m2_model.predict_proba(m2_input.reshape(1, -1))[0]
    if m2_proba[1] < 0.5:
        return NO_SIGNAL                               # M2 vetoes M1
    return m1_signal                                   # M2 trusts M1 → trade
```

### 2.5 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md` + Critic Clar 4 of iter-v3/016 NEW tighter band)

| Metric | Predicted iter-v3/017 | Source |
|---|---:|---|
| IS trade count plausible band | **[120, 180]** | EDA synthesis.md — M2 filters 30-50% of M1-positive bars at threshold 0.5 |
| **Saturation band [iter-v3/013 baseline ± 25%]** | **[157, 261]** | per Critic Clar 4 of iter-v3/016 |
| **Saturation falsifier — lower bound** | **observed IS ≥ 157 → BLOCK** (M2 didn't propagate; filter too lenient or wiring bug) | §4.4 falsifier 2 |
| **Saturation falsifier — upper bound** | **observed IS > 261 → BLOCK** (architecturally impossible; M2 generated more trades than M1, wiring bug) | §4.4 falsifier 3 |
| OOS trade count predicted | ~50-90 (M2 filters proportionally) | counterfactual |
| Per-symbol shift expected direction | NEGATIVE only (M2 filters; should NOT increase any symbol's count) | Clar 1 of iter-v3/016 |

**Interpretive note**: The [120, 180] predicted band is BELOW the [157, 261] saturation lower bound — this is EXPECTED and DESIRED behavior for meta-labeling. M2 filters by design. The saturation falsifier fires if observed IS ≥ 157 because that means M2 is functionally inactive (or it filters fewer than 25% of M1-positive bars, which would be a symptom of M2 trusting nearly every M1 signal — a NULL-RESULT pattern analogous to iter-v3/012's NEGATIVE-no-effect).

### 2.6 Setup integrity (verified at SHA `d47163b`)

```
reports-v3/iteration_v3-013/in_sample/trades.csv extant + non-empty   PASS (210 rows incl. header)
m2_label_distribution.csv produced                                    PASS
exit_reason_breakdown.csv produced                                    PASS
synthesis.md produced                                                  PASS
M2 positive-class prior overall: 33.97% (71/209)                      VERIFIED
Per-symbol prior range: [30.68%, 42.86%]                              VERIFIED
Saturation band [iter-v3/013 ± 25%]: [157, 261]                       VERIFIED
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (BCH+LDO+TRX, inherited from iter-v3/013)

| Symbol | iter-v3/016 | iter-v3/017 | Rationale |
|---|---|---|---|
| BCHUSDT | KEEP | KEEP | iter-v3/013 baseline universe |
| LDOUSDT | KEEP | KEEP | iter-v3/013 baseline universe |
| TRXUSDT | KEEP | KEEP | iter-v3/013 baseline universe |

### 3.2 Labeling — CHANGED ARCHITECTURE (M1+M2 meta-labeling on top of iter-v3/013's triple-barrier)

| Parameter | iter-v3/016 | iter-v3/017 |
|---|---:|---:|
| **Primary model labeling (M1)** | triple-barrier ATR(2.0, 1.0), timeout=21 | **UNCHANGED — M1 inherits iter-v3/013's labeling** |
| `atr_tp_multiplier` | 2.0 | **2.0 (UNCHANGED)** |
| `atr_sl_multiplier` | 1.0 | **1.0 (UNCHANGED)** |
| Timeout | 21 candles | **UNCHANGED** |
| `use_atr_labeling` | True | **UNCHANGED** |
| **Secondary model (M2) — NEW** | ABSENT | **`MetaLabelingStrategy` wrapping LightGbmStrategy as M1** |
| M2 label | n/a | **`y^M2 = 1 if M1-direction trade hits TP barrier first; 0 if SL or timeout`** |
| M2 features | n/a | **V3_FEATURE_COLUMNS + M1's confidence (13 + 1 = 14 features)** |
| M2 architecture | n/a | **`LGBMClassifier(objective='binary', is_unbalance=True)`** |
| M2 confidence threshold | n/a | **0.5 (binary-classification Bayes-optimal; NOT tuned to keep single-axis)** |
| M2 Optuna search space | n/a | **Same as M1 (n_estimators, max_depth, num_leaves, learning_rate, subsample, colsample_bytree, min_child_samples, reg_alpha, reg_lambda) + confidence_threshold pinned at 0.5** |
| M2 n_trials | n/a | **10 (matches M1 EXPLORATION budget; per Critic Clar 5 risk)** |
| M2 inner ensemble seeds | n/a | **`_derive_ensemble_seeds(outer_seed, size=1)` — same single-seed pattern as M1 EXPLORATION** |

### 3.3 Features — UNCHANGED (M1 still uses 13; M2 uses 14 = 13 + M1 confidence)

```python
V3_FEATURE_COLUMNS = (
    "max_dd_window_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)  # length = 13, vwap_dev_50 dropped (inherited from iter-v3/009/010/011/012/013/014/015/016)
```

NO V3_FEATURE_COLUMNS changes. M2 uses these same 13 features plus M1's prediction probability as a 14th feature; the 14th is computed at training time and is NOT added to V3_FEATURE_COLUMNS (M2's input space is internal to MetaLabelingStrategy).

### 3.4 Risk gates — UNCHANGED (all 7 v2 primitives + BTC trend filter inherited)

| Parameter | iter-v3/016 | iter-v3/017 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | **2.0 (UNCHANGED)** |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | **15.0 (UNCHANGED)** |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| ADX threshold | 20 | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

The 7 risk primitives apply at the M1 layer (gating M1's predict() before any signal fires); M2 is a precision filter applied AFTER risk gates pass, so an M1+M2-positive prediction means "all 7 gates green AND M1 confidence ≥ τ_M1 AND M2 confidence ≥ 0.5."

### 3.5 Sub-fix decomposition (single-axis: NEW labeling architecture)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **Implement `MetaLabelingStrategy` class** at `src/crypto_trade/strategies/ml/metalabeling.py` | New module wrapping `LightGbmStrategy` as inner M1 + maintaining a list of `lgb.LGBMClassifier` M2 models per ensemble seed; same `Strategy` Protocol as `LightGbmStrategy` (compute_features / get_signal / skip) | `python -c "from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy; assert MetaLabelingStrategy is not None"` exits 0 |
| 2 | **Modify `_train_for_month` semantics**: train M1 first, then generate M2 labels by reading `long_pnls`/`short_pnls` from the existing labeler, train M2 on M1-positive subset | Inside `MetaLabelingStrategy._train_for_month`: (a) call `self._m1._train_for_month(month_str)`; (b) build M2 labels per §2.4 pseudocode; (c) train M2 LGBMClassifier with same Optuna budget; (d) store M2 model in `self._m2_models` list | `MetaLabelingStrategy._train_for_month` produces non-empty `_m2_models` after a single training call on synthetic data |
| 3 | **Modify `get_signal` semantics**: M1 predicts → if M1 fires AND M1 confidence ≥ τ_M1, M2 predicts → trade only if M2 confidence ≥ 0.5 | `MetaLabelingStrategy.get_signal(symbol, open_time)`: (a) `m1_sig = self._m1.get_signal(...)`; (b) if `m1_sig is NO_SIGNAL`, return NO_SIGNAL; (c) compute M2 input = features + M1 confidence; (d) if M2 confidence < 0.5, return NO_SIGNAL; (e) else return `m1_sig` | smoke test: instance returns NO_SIGNAL when M2 vetoes M1 |
| 4 | **M2 Optuna integration**: re-use `optimize_and_train` from `optimization.py` with `confidence_threshold` pinned to 0.5 (since it's not tuned for M2) — single-axis discipline | New helper `_train_m2_classifier(features, labels, weights, ...)` in `metalabeling.py` that calls `optimize_and_train` with M2 hyperparams; OR direct call to `lgb.LGBMClassifier` with default tuned Optuna search but `confidence_threshold` fixed at 0.5 | Optuna study completes with n_trials=10 in <60s on synthetic data |
| 5 | **Apply pre-commit fixes 1-6** (per `feedback_v3_iter017_metalabeling_mandate.md` + Critic Clar 1, 3, 4 of iter-v3/016): see §3.6 (a)-(f) | Multi-line edits | Section 3.6 verifiers exit 0 |
| 6 | **Add `--model {lgbm,xgboost,metalabeling}` CLI flag** — default still `lgbm` | Modify `argparse` choices in `run_baseline_v3.py` line 1334-1345 to add `metalabeling` as a third choice; in `_build_v3_model`, route to `MetaLabelingStrategy` when `model_type == "metalabeling"` | `grep -E '"metalabeling"' run_baseline_v3.py` exits 0; `--model metalabeling --help` doesn't error |
| 7 | **Unit tests** for M2: smoke test (instance creation, training on synthetic data, prediction returns either signal or NO_SIGNAL) + label-generation correctness (M2 label = 1 iff long_pnl ≥ tp_threshold for long M1 prediction) | New `tests/strategies/ml/test_metalabeling.py` with at least: (a) smoke test, (b) M2 label generation correctness, (c) prediction-time M2 veto correctly returns NO_SIGNAL | `uv run pytest tests/strategies/ml/test_metalabeling.py -v` exits 0 |
| 8 | **Run-log verifier**: pre-flight + sub-fix verification + the 15-row reconciliation table from §3.6 | All 15 rows of §3.6 exit 0; engineering report records verifier outputs | §3.6 reconciliation pass |

NO new feature additions. NO universe change. NO risk-gate threshold change.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK. Apply pre-commits per `feedback_v3_iter017_metalabeling_mandate.md` (cannot be renegotiated).

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | V3_FEATURE_COLUMNS unchanged at 13 features (inherited) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | `atr_tp_multiplier=2.0` UNCHANGED (M1 inherits iter-v3/010 labeling) | `run_baseline_v3.py` ATR mult line | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 3 | `atr_sl_multiplier=1.0` UNCHANGED | `run_baseline_v3.py` ATR mult line | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 4 | `zscore_threshold=2.0` UNCHANGED | `run_baseline_v3.py` zscore line | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 5 | `BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED | `run_baseline_v3.py` line 121 | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 6 | `V3_MODELS` has exactly 3 entries; MKR not present | `run_baseline_v3.py` lines 105-110 | `python -c "from importlib import import_module; import sys; sys.path.insert(0, '.'); m = import_module('run_baseline_v3'); assert len(m.V3_MODELS) == 3 and 'MKRUSDT' not in {s for _, s in m.V3_MODELS}, m.V3_MODELS"` exits 0 |
| 7 | `REQUIRED_GAP == 66` UNCHANGED | `src/crypto_trade/strategies/ml/validation_v3.py` | `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP == 66"` exits 0 |
| 8 | **Pre-commit (a) — ITERATION_LABEL = "v3-017"** | `run_baseline_v3.py` line 99 | `grep -E 'ITERATION_LABEL.*=.*"v3-017"' run_baseline_v3.py` exits 0 |
| 9 | **Pre-commit (b) — Default `--model lgbm` restored** | `run_baseline_v3.py` line ~1337 | `python -c "import argparse; import run_baseline_v3 as m; p = argparse.ArgumentParser(); [a for a in m.__dict__ if 'parser' in a]" || true; grep -E 'default=\"lgbm\"' run_baseline_v3.py` exits 0 |
| 10 | **Pre-commit (c) — `--model metalabeling` choice added** | `run_baseline_v3.py` argparse choices | `grep -E '\"metalabeling\"' run_baseline_v3.py` exits 0 |
| 11 | **Pre-commit (d) — `_write_feature_importance` aggregates across all walk-forward months OR drops OOS CSV byte-duplication** (per Critic Clar 3 of iter-v3/016) | `run_baseline_v3.py` lines 1117-1196 | EITHER (Option A) `_train_for_month` accumulates per-month importances + writes aggregated CSV → `python -c "from pathlib import Path; assert (Path('reports-v3/iteration_v3-017/in_sample/feature_importance.csv').exists() or Path('reports-v3/iteration_v3-017/in_sample/model_importance.csv').exists())"` exits 0 OR (Option B) drop OOS importance CSV byte-duplication, single `model_importance.csv` per split → `test ! -f reports-v3/iteration_v3-017/out_of_sample/feature_importance.csv` exits 0 (provided OOS dir doesn't have it) |
| 12 | **Pre-commit (e) — Saturation falsifier band tightened to [iter-v3/013 ± 25%] = [157, 261]** | brief §2.5 + §4.4 row 5 | brief Section 2.5 documents `[157, 261]`; brief Section 4.4 row 5 references the saturation band correctly |
| 13 | **Pre-commit (f) — §4.4 row 5 condition update**: "either |Δ trades| ≥ 11 OR per-symbol shift > 5 trades on any symbol" (per Critic Clar 1 of iter-v3/016) | brief §4.4 row 5 | brief Section 4.4 row 5 includes this exact phrasing |
| 14 | **MetaLabelingStrategy implementation extant** | `src/crypto_trade/strategies/ml/metalabeling.py` | `python -c "from crypto_trade.strategies.ml.metalabeling import MetaLabelingStrategy; s = MetaLabelingStrategy.__name__; assert s == 'MetaLabelingStrategy'"` exits 0 |
| 15 | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md`)**: IS trade count in [80, 156] (M2 propagated and filtered) | `comparison.csv` post-Phase-6 | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-017/comparison.csv'); n = df.loc[df['metric']=='n_trades','in_sample'].iloc[0]; assert 80 <= int(n) <= 156, f'IS trades {n} outside expected [80, 156] meta-labeling band'"` exits 0 |

### 3.7 Inheritance from iter-v3/016

The `iteration-v3/017` branch was branched from `iteration-v3/016` head. Inherited commits include:

- `bce50c8 feat(iter-v3/007): --exploration mode` (CLI flag plumbing)
- `92218ef feat(iter-v3/007): top-14 V3_FEATURE_COLUMNS subset`
- `849c4a6 fix(iter-v3/007): risk_v3 always loads atr_pct_rank_200 from parquet`
- `56b8f8b feat(iter-v3/008): drop vwap_dev_50 (14→13 features)`
- `b55086a feat(iter-v3/010): ATR multipliers (2.9,1.45)→(2.0,1.0)`
- `17d01ab feat(iter-v3/011): z-score OOD threshold 2.5 → 2.0`
- `93891a3 feat(iter-v3/012): BTC trend band 0.20 → 0.15`
- `<iter-v3/013 SHA> feat(iter-v3/013): drop MKR universe (4→3 symbols)`
- `<iter-v3/014 SHA> feat(iter-v3/014): ADX threshold 20 → 25 (REVERTED at iter-v3/015)`
- `<iter-v3/015 SHA> feat(iter-v3/015): tbr_zscore_30 added (REVERTED at iter-v3/016)`
- `<iter-v3/016 SHA> feat(iter-v3/016): XGBoost --model flag + xgb.py module`
- `d47163b feat(iter-v3/017): metalabeling_eda — M1+M2 label distribution analysis` (this brief's evidence)

Critical inheritance verifiers (run before any code edits in Phase 6):
- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'vwap_dev_50' not in V3_FEATURE_COLUMNS"` exits 0
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- `grep -E '"MKRUSDT"' run_baseline_v3.py` exits 1 (MKR removed at iter-v3/013)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE`, `EXPLORATION-NEGATIVE-no-effect`, `EXPLORATION-NEGATIVE-over-filter`, or `BLOCK` (process). iter-v3/017 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/013 (M1-only baseline) | iter-v3/017 prediction (M1 + M2 meta-labeling at threshold 0.5) |
|---|---:|---:|
| IS monthly Sharpe | +1.0088 | **predicted [+0.80, +1.40] with median +1.10** |
| IS trades | 209 | **predicted [120, 180]** (M2 filters 30-50% of M1-positive bars) |
| OOS trades | 85 | **predicted [50, 90]** (M2 filters proportionally; floor caveat under EXPLORATION) |
| Phase 6 wall-clock | ~6 min | predicted ~9-12 min (M1 ~6 min + M2 ~3-6 min, 2h hard cap) |

The prediction band [+0.80, +1.40] is calibrated against iter-v3/013's +1.0088 baseline with **+10% upside from filtering**:
- Lower bound +0.80: M2 filters proportionally to base rate (33.97%) and per-trade economics improve ~10% — net Sharpe slightly down because trade-count drop is steeper than per-trade improvement.
- Median +1.10: M2 learns useful precision signal — 50% of M1-positive bars filtered, retained bars have ~50% TP-hit rate (vs 33.97% baseline), per-trade economics improve enough to compensate.
- Upper bound +1.40: M2 learns highly precise filter — 60% of M1-positive bars filtered, retained bars have ~65% TP-hit rate, per-trade economics improve substantially.

The 3 consecutive favorable IS calibration overshoots from iter-v3/010, /011, /013 (per iter-v3/013 caveats §4) suggest behavior-changing axes have wider PROMISING distributions than QR's prior bands; the +1.40 upper bound is +30% wider than a naive midpoint to account for this calibration history.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < +0.40 → meta-labeling fails to filter usefully OR M2 over-filters and removes too many positive-PnL trades. Verdict: EXPLORATION-NEGATIVE on labeling-architecture axis. Catalog this finding; iter-v3/018+ revisits at different M2 threshold or different M2 feature set.

**Falsifier 2 (saturation lower-bound, per `feedback_axis_saturation_predictor.md`)**: IS trade count ≥ 157 → M2 trusts nearly every M1 signal (filter too lenient OR wiring bug). Verdict: BLOCK (process) OR EXPLORATION-NEGATIVE-no-effect (depending on whether trade roster is bit-identical to iter-v3/013).

**Falsifier 3 (saturation upper-bound)**: IS trade count > 261 → M2 generated more trades than M1 baseline (architecturally impossible; wiring bug). Verdict: BLOCK (process); engineer documents.

**Falsifier 4 (over-filter)**: IS trade count < 80 → M2 filters too aggressively (positive class too restrictive at threshold 0.5). Verdict: EXPLORATION-NEGATIVE-over-filter; catalog as new subtype.

**Falsifier 5 (per-symbol direction check, per Critic Clar 1 of iter-v3/016)**: any symbol's IS trade count INCREASES vs iter-v3/013 baseline (BCH > 100 OR LDO > 21 OR TRX > 88). Verdict: BLOCK (process; M2 is subtractive by design — it filters M1-positive bars, never adds new ones).

**Process falsifier**: pre-flight `len(V3_MODELS) == 3` returns False OR `REQUIRED_GAP == 66` returns False OR `MetaLabelingStrategy` import fails OR `--model metalabeling` not in argparse choices → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

**Per Critic Clar 1 of iter-v3/016** — row 5 condition reads "either |Δ trades| ≥ 11 OR per-symbol shift > 5 trades on any symbol" (catches opposite-direction per-symbol shifts).

| # | Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|---|
| 1 | `EXPLORATION-PROMISING` | IS Sharpe ≥ +1.10 (≥+0.10 vs iter-v3/013 +1.0088) AND IS trade count in [80, 156] (M2 propagated and filtered) AND no per-symbol IS count INCREASE vs iter-v3/013 | "Meta-labeling adds compoundable precision filter" | First v3 CONFIRMATION (cadence 10/10 reached); bundling QR includes meta-labeling as ingredient |
| 2 | `EXPLORATION-PROMISING-INERT` | IS Sharpe in [+0.91, +1.10] AND trade count in [80, 156] AND no per-symbol IS count INCREASE | "Meta-labeling axis-orthogonal to current edge — neither helps nor hurts" | First v3 CONFIRMATION; bundling QR may exclude meta-labeling but does not bundle as new ingredient |
| 3 | `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT subtype) | IS trade count ≥ 157 AND IS roster bit-identical to iter-v3/013 baseline (M2 not propagating) | "M2 layer wired but functionally inactive at threshold 0.5 (NULL-RESULT, M2 trusts every M1 signal)" | First v3 CONFIRMATION; bundling QR excludes meta-labeling architecture |
| 4 | `EXPLORATION-NEGATIVE-over-filter` (new subtype) | IS trade count < 80 (over-filter) AND IS Sharpe < +0.91 OR OOS Sharpe < +0.50 | "M2 over-filters; positive-class threshold 0.5 too aggressive for IS sample" | First v3 CONFIRMATION; bundling QR considers M2 architecture only at higher threshold (e.g., 0.4) — but threshold tuning would be a NEW knob axis at iter-v3/018+ |
| 5 | `EXPLORATION-NEGATIVE` (clean) | IS Sharpe Δ < -0.10 (i.e., < +0.91 vs +1.0088 baseline) AND **either \|Δ trades\| ≥ 11 OR per-symbol shift > 5 trades on any symbol** AND axis propagated (saturation falsifier PASS at IS trade count in [80, 156]) | "Meta-labeling architecture closed at the tested configuration (threshold 0.5 + 14-feature M2 input + same Optuna budget)" | First v3 CONFIRMATION; bundling QR excludes meta-labeling architecture |
| 6 | `BLOCK` (process) | Methodology check FAILED, OR Falsifier 2 (saturation lower) triggered, OR Falsifier 3 (saturation upper) triggered, OR Falsifier 5 (per-symbol increase) triggered | (none) | Diary documents; iter-v3/018 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (4 items)

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h. M2 adds ~50% to M1 training time on a smaller positive-class subset; total ~9-12 min target.
2. **Single-axis variation rule honored**: only the labeling architecture (M1+M2 meta-labeling) changes. Features, universe, all 7 risk gates, ATR labeling multipliers, M1 architecture (LightGBM), CPCV parameters, walk-forward window all byte-for-byte identical to iter-v3/013/016.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / PROMISING-INERT / NEGATIVE / NEGATIVE-no-effect / NEGATIVE-over-filter / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-017.md`.
4. **Saturation predictor falsifier (per `feedback_axis_saturation_predictor.md`)**: Section 3.6 row 15 actively verifies IS trade count in [80, 156] (M2 propagated AND filtered, NOT NULL-RESULT, NOT over-filter).

### 5.2 Methodology-pipeline safety (4 items, inherited from iter-v3/006-016)

1. **Adversarial unit tests** must PASS before backtest (`uv run pytest tests/strategies/ml/ -v`).
2. **File-artifact reconciliation table** (§3.6). 15 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len + name check** on `V3_MODELS` and `REQUIRED_GAP`: catches the case where inherited setup was silently lost during a rebase.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 Axis-specific risks (3 items, NEW for iter-v3/017)

1. **M2 over-filtering risk**: at threshold 0.5, M2 may filter > 50% of M1-positive bars and reduce trade count below 80 — analogous to over-restrictive ADX (iter-v3/014). Mitigation: §4.3 falsifier 4 + per-symbol direction check (falsifier 5). Threshold 0.5 is the standard binary-classification cutoff and is NOT tuned this iteration to keep single-axis discipline; if over-filter materializes, iter-v3/018 may consider threshold 0.4 as a knob-tuning axis (lowest priority per `feedback_structural_over_knob_exploration.md`).
2. **M2 underfitting at threshold 0.5 (NULL-RESULT pattern)**: M2 may produce confidence scores tightly clustered around the prior 33.97% with no separation between true-positives and false-positives — every M1-positive bar gets M2 confidence < 0.5 (over-filter) OR every M1-positive bar gets M2 confidence > 0.5 (under-filter / NULL-RESULT). Mitigation: §4.3 falsifier 2 + 4 + EDA §2.2 per-symbol prior heterogeneity (30.68% to 42.86%) suggests M2 has discriminating signal across symbols.
3. **M2 hyperparam search budget too small at n_trials=10**: matches M1's EXPLORATION budget but may be insufficient for M2 to converge under a smaller training subset (n_M1-positive ≈ 70-100 per training month vs ~200-300 for M1's full training set). Mitigation: M2's smaller training set means each Optuna trial is faster (~30s vs ~1min for M1); 10 trials gives `n_eff` ~5-7 by Optuna convergence math, enough to surface a stable hyperparam region. CONFIRMATION-bundling QR may increase M2 trial budget to 50 if PROMISING.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — UNCHANGED, all primitive thresholds inherited from iter-v3/016

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol, M1-layer) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 | ≈ 25-35% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12-13% killed | Macro flips |

Combined kill rate target: **80-90%** (M1 layer — same as iter-v3/013/016). The new M2 filter is ADDITIVE on top of these gates: M2 sees only the bars where all 7 gates passed AND M1 confidence ≥ τ_M1; M2's job is precision-residual filtering, not kill rate.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and are independent of M2. M2 is a layered filter applied AFTER M1's gated prediction, so the 7-gate kill rate is unchanged from iter-v3/016.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2022-09-24 → 2025-03-23 — same as iter-v3/013-016. Regime coverage includes 2022 LUNA/FTX, 2023 banking (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/013 OOS showed 65.65% LDO concentration. iter-v3/017 OOS concentration cannot be predicted before backtest because M2 filtering may shift the per-symbol mix asymmetrically (LDO has higher M2 prior at 42.86% vs TRX at 30.68% — M2 may KEEP more LDO trades than TRX, pushing concentration HIGHER, OR M2 may filter LDO's lottery-flag wins disproportionately, pushing concentration LOWER). Concentration is NOT a gate for iter-v3/017 per TYPE=EXPLORATION; informational only.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Prediction P1 (process, P=10%)**: MetaLabelingStrategy import fails OR M2 training raises exception OR `--model metalabeling` not wired correctly. **Detection signal**: §3.6 row 14 + adversarial test failures + Phase 6 stdout shows ImportError or AttributeError. **Mitigation**: §3.6 rows 14, 9, 10 + §3.5 sub-fix #7 (smoke test).

**Prediction P2 (process, P=5%)**: M2 generates labels but model never converges (Optuna trials all return -10.0 sentinel value because training set is too small). M2 output defaults to "always positive" — equivalent to NULL-RESULT but for a different reason. **Detection signal**: §3.6 row 15 falsifier 2 fires (IS trade count ≥ 157). **Mitigation**: M2 fallback to "trust M1" if training fails; engineer documents.

**Prediction P3 (process, P=5%)**: per-symbol IS trade count INCREASES vs iter-v3/013 baseline (BCH > 100 OR LDO > 21 OR TRX > 88). M2 is structurally subtractive — never adds new trades. An increase implies a wiring bug (M2 inverted, or M1's positive-prediction set is mistakenly larger). **Detection signal**: §4.3 falsifier 5. **Mitigation**: §3.6 row 15 + per-symbol comparison in engineering report.

**Prediction P4 (model, P=35%)**: IS Sharpe ≥ +1.10 (≥+0.10 vs iter-v3/013) — meta-labeling learns useful precision signal; M2 filters 40-50% of M1-positive bars; retained bars have ~50%+ TP-hit rate; per-trade economics improve enough to compensate for trade-count drop. EXPLORATION-PROMISING. The strategy's edge gains a structurally compoundable precision filter.

**Prediction P5 (model, P=35%)**: IS Sharpe in [+0.91, +1.10] — M2-orthogonal to M1's edge; the 33.97% prior is too uniform across the M1-positive bars for M2 to discriminate. Trade count drops to ~150 but per-trade economics unchanged. EXPLORATION-PROMISING-INERT or EXPLORATION-NEGATIVE-no-effect (depending on saturation falsifier).

**Prediction P6 (model, P=15%)**: IS Sharpe < +0.91 — M2 over-filters or filters the wrong trades (e.g., M2 keeps high-confidence M1 bars that happen to be SL-prone in IS). EXPLORATION-NEGATIVE or EXPLORATION-NEGATIVE-over-filter. Catalog this finding; iter-v3/018 may revisit M2 architecture.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline.
- 3 model-level (P4, P5, P6) covering PROMISING / PROMISING-INERT-or-NULL / NEGATIVE-or-over-filter.
- Per the iter-v3/010 + /011 + /013 calibration history (3 favorable IS overshoots on behavior-changing axes), priors slightly favor PROMISING (35%); per iter-v3/012 + /014 + /015 + /016 calibration history (4 NEGATIVE/NULL outcomes on the last 4 EXPLORATIONs), the prior on NEGATIVE-or-NULL is also high. Net 70% probability of either PROMISING or PROMISING-INERT, 30% NEGATIVE-or-over-filter; the bimodal split reflects honest uncertainty about whether AFML Ch. 3's claims generalize from equities to crypto futures at 8h cadence on 209 IS samples.

Summary: **EXPLORATION-PROMISING pathway probability ≈ 35%** (P4); EXPLORATION-PROMISING-INERT-or-NULL ≈ 35% (P5); EXPLORATION-NEGATIVE-or-over-filter ≈ 15% (P6); process abort ≈ 20% (P1+P2+P3).

If any prediction fails to materialize, the iter-v3/017 diary documents the calibration miss.

---

## Section 8 — Pre-Registered EXPLORATION Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/017 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0) are NOT in scope. Critic emits one of: `EXPLORATION-PROMISING`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE-no-effect`, `EXPLORATION-NEGATIVE-over-filter`, `EXPLORATION-NEGATIVE`, or `BLOCK`.

### EXPLORATION-PROMISING iff ALL 11 of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE | §0.5 |
| 2 | Single-axis variation only (NEW labeling architecture: M1+M2 meta-labeling) | TRUE | §3.7 |
| 3 | Wall-clock < 2h (target < 30 min) | TRUE | §3.6 |
| 4 | `--exploration --seeds 1 --n-trials 10 --model metalabeling` used | TRUE | §3.5 sub-fix #6 |
| 5 | All adversarial tests pass | TRUE | §3.6 |
| 6 | `V3_MODELS` has 3 entries; MKR not present | TRUE | §3.6 row 6 |
| 7 | `REQUIRED_GAP == 66` confirmed at runtime | TRUE | §3.6 row 7 |
| 8 | `comparison.csv` produced (basic headline metrics) | TRUE | §3.6 |
| 9 | Critic OVERALL = `EXPLORATION-PROMISING` (NOT INERT, NOT NULL, NOT NEGATIVE, NOT BLOCK) | enum | Phase 7.5 |
| 10 | NO 5-seed or CONFIRMATION-style runs | TRUE (vacuous; --seeds 1) | §3.7 |
| 11 | **Behavioral-effect verifier passes (IS trade count in [80, 156])** | TRUE | §3.6 row 15 |

### EXPLORATION-PROMISING-INERT iff:

- Criteria 1-8, 10, 11 PASS BUT Critic OVERALL = `EXPLORATION-PROMISING-INERT` (because IS Sharpe in [+0.91, +1.10], i.e., axis-orthogonal to current edge)

### EXPLORATION-NEGATIVE-no-effect iff:

- Criteria 1-8, 10 PASS BUT IS trade count ≥ 157 AND IS roster bit-identical to iter-v3/013 baseline (M2 layer wired but functionally inactive)

### EXPLORATION-NEGATIVE-over-filter iff:

- Criteria 1-8, 10 PASS BUT IS trade count < 80 AND (IS Sharpe < +0.91 OR OOS Sharpe < +0.50)

### EXPLORATION-NEGATIVE (clean) iff:

- Criteria 1-8, 10, 11 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (because IS Sharpe < +0.91 AND **either |Δ trades| ≥ 11 OR per-symbol shift > 5 trades on any symbol** AND axis propagated cleanly per saturation falsifier PASS)

### BLOCK (process) iff ANY of:

- Criteria 1-8, 10 fail (process-level)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK
- Wall-clock exceeds 2h hard cap
- Falsifier 3 (saturation upper-bound: IS trades > 261) triggered
- Falsifier 5 (per-symbol increase: BCH > 100 OR LDO > 21 OR TRX > 88) triggered

### Discretionary judgment — EXPLORATION pathway

iter-v3/017 has NO MERGE pathway because the iteration TYPE is EXPLORATION. The "MERGE pathway" is `EXPLORATION-PROMISING` or `EXPLORATION-PROMISING-INERT`, both of which are forward-pointers: they add one row to the catalog and complete the 10/10 EXPLORATION quota. **iter-v3/017 NEVER updates BASELINE_V3.md.**

After iter-v3/017 completes regardless of verdict, **first v3 CONFIRMATION can launch.** PROMISING-class candidates accumulated to date: iter-v3/007 (top-14 → top-13 features), iter-v3/010 (labeling ATR 2.0/1.0), iter-v3/011 (z-score OOD 2.0), iter-v3/013 (drop-MKR universe; PROMISING-MECHANICAL → strictly accretive baseline component); iter-v3/017 will add a 5th potential ingredient if PROMISING.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for seed derivation; M2 array math | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged); M2 inherits | n/a |
| `lightgbm` | (already installed) | MIT | M1 (LightGbmStrategy) + **M2 (LGBMClassifier; binary objective + is_unbalance=True)** — single dependency for both layers | n/a |
| `xgboost` | `>=2.0,<3.0` | Apache-2.0 | inherited from iter-v3/016 (--model xgboost opt-in); NOT used at iter-v3/017 (default --model lgbm restored) | n/a |
| `pytest` | (already installed) | MIT | adversarial tests | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O + analysis script CSV loading | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | n/a |

**No new external deps.** Same stack as iter-v3/006-016; M2 reuses existing LightGBM infrastructure (binary classification, Optuna integration, Bayes-optimal threshold). XGBoost remains as iter-v3/016 carry-over (opt-in via `--model xgboost`).

The iteration's NEW code is:
- 1 EDA script + 3 outputs (committed at SHA `d47163b`)
- 1 NEW module `src/crypto_trade/strategies/ml/metalabeling.py` (~150 lines: MetaLabelingStrategy class)
- ~30 line edits in `run_baseline_v3.py` (argparse choices + `_build_v3_model` routing + ITERATION_LABEL + `_write_feature_importance` aggregation fix per Critic Clar 3)
- 1 NEW pytest test file `tests/strategies/ml/test_metalabeling.py` (~60 lines: smoke + label generation + veto correctness)
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-017/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `d47163b` EDA + the new sub-fix SHAs)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|xgboost|pytest|pandas|pyarrow)"`
- The full 13-feature list as actually trained on by M1 (sanity check against §3.3)
- The runtime `V3_MODELS` (sanity check against §3.5 sub-fix; 3 entries, no MKR)
- The runtime `REQUIRED_GAP` (66)
- The `comparison.csv` IS / OOS monthly Sharpe values
- The total IS trade count (must be in [80, 156] per Falsifier 2 + 4)
- Per-symbol IS trade count comparison vs iter-v3/013 (Falsifier 5: each must be ≤ baseline)
- The MetaLabelingStrategy import smoke check
- The wall-clock minutes total (must be < 120; target < 30)
- The adversarial test outcome (PASS expected)
- The `--exploration --seeds 1 --n-trials 10 --model metalabeling` activation banner from `run.log`
- The runner invocation literal (proof of `--exploration --seeds 1 --n-trials 10 --model metalabeling`)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the new behavioral-effect predictor (Section 2):

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=1 / colsample=1.0 / n_trials=10 SET BY --exploration |
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; cadence catalog reference (10/10 FINAL); explicit "NEVER updates BASELINE_V3.md"; NEW labeling architecture-axis MANDATED by `feedback_v3_iter017_metalabeling_mandate.md` (FIRED at iter-v3/016) |
| 1 — Hypothesis | PASS — one sentence with mechanism (M2 precision filter on M1's positive predictions); testable target IS Sharpe ≥ +1.10 (Falsifier 1 at +0.40); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-017/metalabeling_eda.py` committed at SHA `d47163b` BEFORE this brief; M2 architecture math + label distribution (33.97% overall, 30.68%-42.86% per-symbol) + label generation pseudocode + saturation falsifier with NEW tighter band [157, 261] per Critic Clar 4 of iter-v3/016 |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; M1 labeling UNCHANGED; M2 NEW (binary classifier on M1-positive subset); features UNCHANGED at 13; all gates UNCHANGED; sub-fix decomposition with reconciliation table 15 verifiers; inheritance plan §3.7 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.80, +1.40] median +1.10; 5 falsifiers (incl. saturation lower 157 + upper 261 + per-symbol direction check from Clar 1 of iter-v3/016) + 1 process falsifier in §4.3; pre-commit catalog framing 6 rows in §4.4 (incl. NEW NEGATIVE-over-filter subtype + NULL-RESULT subtype) |
| 5 — Risk Mitigation | PASS — 4 cadence-discipline structural safeguards + 4 methodology-pipeline safeguards + 3 axis-specific risks (M2 over-filter, M2 underfit at 0.5, M2 trial budget at n_trials=10) |
| 6 — Risk Management Design | PASS — 7-primitive table inherited; M2 is precision filter ON TOP of 7-gate kill rate, gate orthogonality preserved |
| 7 — Pre-Registered Failure-Mode | PASS — 6 predictions with **3 process-level (P1, P2, P3)**; calibrated PROMISING+PROMISING-INERT prior at ~70%, NEGATIVE-or-over-filter at 15%, process at 20% |
| 8 — Pre-Registered EXPLORATION Criteria | PASS — 11 EXPLORATION criteria including **criterion 11: Behavioral-effect verifier passes (IS trades in [80, 156])**; PROMISING / PROMISING-INERT / NEGATIVE-no-effect / NEGATIVE-over-filter / NEGATIVE / BLOCK pathways; explicit "NEVER updates BASELINE_V3.md"; first v3 CONFIRMATION launches after this iteration |
| 9 — Library Stack | PASS — no new deps; M2 reuses LightGBM infrastructure; aggregator strategy unchanged from iter-v3/006-016 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8. Note that Section 3.6 row 11 (pre-commit (d) — `_write_feature_importance` aggregation fix), row 14 (`MetaLabelingStrategy` extant), and row 15 (behavioral-effect verifier IS trade count in [80, 156]) are critical NEW gates; row 15 implements the saturation predictor falsifier per `feedback_axis_saturation_predictor.md` with the NEW tighter band [157, 261] per Critic Clar 4 of iter-v3/016.
