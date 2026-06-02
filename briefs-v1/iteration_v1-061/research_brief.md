# iter-v1/061 — Research Brief

**Iteration**: iter-v1/061
**Date**: 2026-06-02
**TYPE**: EXPLORATION
**Cycle**: 7, EXP 4/N
**Branch**: `iteration-v1/061`
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

- **OOS_CUTOFF_DATE**: `2025-03-24` (IMMUTABLE — never changes)
- **training_months**: `24` (IMMUTABLE — never changes)
- **IS window**: 2023-03-24 → 2025-03-24 (24 months)
- **OOS window**: 2025-03-24 → present

These constants are encoded in `src/crypto_trade/config.py` and `OOS_CUTOFF_MS`. The runner
does NOT change them. Reproduction from any date within the OOS window produces bit-identical
IS metrics and monotonically-extended OOS metrics.

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: EXPLORATION
- **Cadence**: cycle-7 EXPLORATION 4/N (after /059 model-architecture, /060 methodology,
  /061 = first cycle-7 methodology-substrate-test / zero-randomness diagnostic axis).
- **Wall-clock budget**: < 2h (EXPLORATION cap; enforced by single-seed=1 + n_trials=1 +
  BTC-only cohort. Estimate: ~5–15 min for a single BTC-only cell at n_trials=1.)
- **No kill-switch** (per cycle-5+ discipline; overrun impossible at single cell config).

---

## Section 0.6 — Architecture-Family Justification

- **Axis family**: `methodology` (zero-randomness diagnostic; pipeline reproducibility test)
- **Prior 5 EXPLORATION families** (catalog rows /054-/060):
  - iter-v1/054: `feature-family` (impulse-drop BTC specialist)
  - iter-v1/055: `feature-family` (ETH cross-asset return ratio)
  - iter-v1/057: `feature-family` (LTC cross-asset return ratio; BASIN-LOTTERY)
  - iter-v1/058: `feature-family` (BTC OI 5-bar delta; BASIN-LOTTERY)
  - iter-v1/059: `model-architecture` (Pool+Route validation)
  - iter-v1/060: `methodology` (multi-seed Pool+Route disambiguation)
- **Rotation status**: VALID — `methodology` REPEAT is the 2nd methodology EXPLORATION in
  the last 5 (not monoculture; 5 distinct families across /054-/060: feature-family×4,
  model-architecture×1, methodology×1). The methodology family covers structurally orthogonal
  axes; zero-randomness diagnostic is categorically distinct from /060's multi-seed
  disambiguation (different pipeline property tested).

---

## Section 1 — Hypothesis

**H1 (PRIMARY)**: BTC-only LightGBM training with ALL sources of randomness eliminated
(n_trials=1, seeds=1, subsample=1.0, colsample_bytree=1.0, bagging_freq=0, deterministic=True,
num_threads=1, is_unbalance=False) produces a **bit-exactly reproducible** IS Sharpe across
consecutive runs, confirming the pipeline has zero hidden randomness at these HPs. The LM
Master predicts IS Sharpe ≈ +0.08 (band [−0.10, +0.20]).

**H1a (mechanism)**: Prior BTC-only EXPLORATION variance (spread 0.90 at /058, spread 0.31 at
/053) is attributable to Optuna's stochastic basin-hopping + subsampling variance. Removing
both reveals the deterministic loss surface for the 48-col PRUNED stack at the LM Master's
central-tendency HPs.

**H1b (comparison)**: BTC-only specialist history at single-seed=42:
- /054 (18 trials, subsample≈0.99): IS +0.2614 (favorable basin draw)
- /053 (3-seed mean, 18 trials): IS mean −0.04 (spread 0.31)
- /058 (3-seed mean, 18 trials): IS mean −0.28 (spread 0.90 — catalog record)
- /059 (pool, single-seed, 18 trials): IS −0.16 (Pool+Route architecture, informational)
- LM Master prediction for /061: IS **+0.08** (band [−0.10, +0.20], 60% probability)

The reproducibility property IS the primary deliverable, not the IS Sharpe magnitude.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v1-061/btc_zero_randomness_eda.py` (committed).

Evidence collected from existing backtest artifacts and LM Master Phase 4.5 advisory:

| Source | BTC IS Sharpe | n_trials | subsample | colsample | seeds |
|---|---|---|---|---|---|
| /053 offset0 (seed=42) | +0.1609 | 18 | 0.88 | 0.72 | 1 |
| /053 3-seed mean | −0.04 | 18 | varied | varied | 3 |
| /054 single-seed=42 | +0.2614 | 18 | 0.985 | 0.888 | 1 |
| /058 3-seed mean | −0.28 | 18 | varied | varied | 3 |
| LM Master /061 prediction | +0.08 | 1 | 1.0 | 1.0 | 1 |

**Key evidence**: The /053 and /058 multi-seed spreads (0.31 and 0.90 respectively) demonstrate
that IS Sharpe at BTC-only specialist is dominated by basin-lottery variance under Optuna+subsampling.
Stripping ALL randomness produces a single deterministic read. The LM Master's 60% modal prediction
([−0.10, +0.20] band) covers the range between /053 mean (−0.04) and /054 single-seed (+0.26).

**Reproducibility evidence**: LM Master `lgbm_advisor.md` §"Other Randomness Sources to Eliminate"
enumerates 10 randomness sources; the runner explicitly addresses all 10 via hardcoded HPs +
`deterministic=True` + `num_threads=1` + `is_unbalance=False` + `force_col_wise=True`.

---

## Section 2.5 — HIGH-RISK Axis Declaration

**RISK**: NORMAL-RISK

The zero-randomness diagnostic does NOT change the Optuna training-objective domain:
- The labeling function is unchanged (triple-barrier, EWMA-σ_t, /014 C1-fixed)
- The feature set is unchanged (V1_FEATURE_COLUMNS_PRUNED, 48 cols)
- The training data is unchanged (BTC IS window 2023-03-24 → 2025-03-24)
- The objective is unchanged (Sharpe, n_trials=1 = single deterministic trial)

NORMAL-RISK: changing `subsample`, `colsample_bytree`, `bagging_freq`, `is_unbalance`,
`num_threads`, and `deterministic` are inference-time and regularization parameters that
affect the MODEL WEIGHTS but NOT the Optuna training-objective domain (the domain is defined
by the label distribution + feature space, which is unchanged). The pre-commit tripwire is
NOT armed for this axis.

---

## Section 3 — Proposed Changes

### Section 3.1 — Hardcoded HP Dict (COMPLETE; LM Master Phase 4.5 ADOPTED VERBATIM)

```python
HARDCODED_LGBM_PARAMS_061 = {
    # Tree complexity
    "n_estimators":        300,
    "max_depth":           4,
    "num_leaves":          31,
    "min_child_samples":   50,
    "min_split_gain":      0,

    # Learning rate + boosting
    "learning_rate":       0.05,
    "boosting_type":       "gbdt",

    # Subsampling DISABLED (user spec + LM Master §"Randomness Sources" #1)
    "subsample":           1,
    "subsample_freq":      0,
    "bagging_freq":        0,
    "bagging_fraction":    1,
    "colsample_bytree":    1,
    "feature_fraction":    1,

    # Regularization
    "reg_alpha":           0.1,
    "reg_lambda":          0.1,

    # Determinism (LM Master §"Randomness Sources" #2, #3)
    "random_state":        42,
    "deterministic":       True,
    "force_col_wise":      True,
    "num_threads":         1,

    # Objective + class handling (LM Master §"Randomness Sources" #1)
    "objective":           "binary",
    "is_unbalance":        False,
    "class_weight":        None,
    "scale_pos_weight":    1,

    # Misc
    "verbosity":           -1,
    "metric":              "binary_logloss",

    # Training schedule (runner-level; NOT LightGBM params)
    "confidence_threshold": 0.7,
    "training_days":        360,
    "training_months":      24,
    "n_trials":             1,
    "cv_splits":            5,
    "cv_gap":               42,
}
```

LM Master Phase 4.5 recommendations and disposition:
- **Rec 1 (central-tendency HPs)**: ADOPTED — n_estimators=300, max_depth=4, num_leaves=31,
  learning_rate=0.05, min_child_samples=50, reg_alpha=0.1, reg_lambda=0.1.
- **Rec 2 (subsampling DISABLED)**: ADOPTED — subsample=1.0, colsample_bytree=1.0,
  bagging_freq=0, subsample_freq=0, feature_fraction=1.0, bagging_fraction=1.0 (all aliases
  set explicitly for safety).
- **Rec 3 (determinism flags)**: ADOPTED — deterministic=True, num_threads=1, force_col_wise=True,
  random_state=42.
- **Rec 4 (is_unbalance=False)**: ADOPTED — eliminates month-varying implicit scale_pos_weight.
- **Rec 5 (n_trials=1 + bypass Optuna or enqueue_trial)**: ADOPTED — n_trials=1 passed to
  runner; HP override injected via `study.enqueue_trial()` monkey-patch (see Section 3.2).
- **Rec 6 (confidence_threshold=0.70)**: ADOPTED — median of /054's best-trial range.
- **Rec 7 (training_days=360)**: ADOPTED — 12-month rolling window (cleaner regime split
  than /054's best-trial 260 days).
- **Rec 8 (reproducibility check mandate)**: ADOPTED — F1 falsifier is bit-exact reproducibility.
- **Rec 9 (R3 OOD disabled)**: ADOPTED — R3 gate disabled to eliminate covariance-inversion
  non-determinism as a randomness surface (LM Master §"Other Randomness Sources" #9).

### Section 3.2 — Monkey-Patch Mechanism

The runner (`run_iteration_061.py`) monkey-patches `optimize_and_train` in
`src/crypto_trade/strategies/ml/optimization.py` **before** calling
`run_baseline_v1.main()`. Specifically:

```python
import run_baseline_v1 as _rbv1
import crypto_trade.strategies.ml.optimization as _opt

_original_optimize = _opt.optimize_and_train

def _fixed_hp_optimize(train_features, train_labels, all_columns, long_pnls, short_pnls,
                        n_trials, cv_splits, seed, verbose=0, **kwargs):
    """Drop-in replacement for optimize_and_train that injects hardcoded HPs via enqueue_trial."""
    import optuna
    from crypto_trade.strategies.ml.optimization import _objective

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.set_user_attr("fast_mode", False)
    study.set_user_attr("optuna_objective", "sharpe")

    # Inject hardcoded HPs — enqueue_trial forces the single trial to use these values.
    study.enqueue_trial({
        "confidence_threshold": HARDCODED_LGBM_PARAMS_061["confidence_threshold"],
        "training_days":        HARDCODED_LGBM_PARAMS_061["training_days"],
        "n_estimators":         HARDCODED_LGBM_PARAMS_061["n_estimators"],
        "max_depth":            HARDCODED_LGBM_PARAMS_061["max_depth"],
        "num_leaves":           HARDCODED_LGBM_PARAMS_061["num_leaves"],
        "learning_rate":        HARDCODED_LGBM_PARAMS_061["learning_rate"],
        "subsample":            HARDCODED_LGBM_PARAMS_061["subsample"],
        "colsample_bytree":     HARDCODED_LGBM_PARAMS_061["colsample_bytree"],
        "min_child_samples":    HARDCODED_LGBM_PARAMS_061["min_child_samples"],
        "reg_alpha":            HARDCODED_LGBM_PARAMS_061["reg_alpha"],
        "reg_lambda":           HARDCODED_LGBM_PARAMS_061["reg_lambda"],
    })
    study.optimize(lambda trial: _objective(trial, ...), n_trials=1)
    # Return best model trained with hardcoded HPs
    ...
```

The dispatch branch in `run_baseline_v1.py` (`elif iteration_label == "v1-061"`) also
asserts `subsample=1.0`, `colsample_bytree=1.0`, and `bagging_freq=0` after training
by reading back the model's `get_params()` dict and asserting each value.

### Section 3.3 — Architecture

- **Cohort**: BTCUSDT only (single-symbol head; mirrors /054 dispatch)
- **Features**: V1_FEATURE_COLUMNS_PRUNED (48 cols; UNCHANGED — no feature add/drop)
- **R1**: OFF (same as baseline Model A — no R1 on BTC)
- **R2**: OFF (same as baseline Model A — no R2 on BTC)
- **R3**: OFF (LM Master §"Other Randomness Sources" #9: OOD Mahalanobis disabled to
  eliminate covariance-inversion non-determinism; also removes the gating randomness surface)
- **atr_tp=3.5**, **atr_sl=1.75** (UNCHANGED from /052-/054 BTC specialist convention)
- **n_trials=1**, **seeds=1** (zero-randomness experiment spec)
- **ENSEMBLE_SIZE=1** (single inner model; no ensemble averaging)

### Section 3.4 — No Changes Required

- No new features added or removed from V1_FEATURE_COLUMNS_PRUNED
- No parquet regeneration required (48-col stack is current)
- No src/ changes to `features_v1/` required
- Only src/ changes: new `elif iteration_label == "v1-061"` branch in `run_baseline_v1.py`

---

## Section 4 — Expected OOS Impact (F-AXIS Verdict Framework)

This is a **diagnostic EXPLORATION**, not a performance-optimization EXPLORATION.
The verdict is determined by reproducibility, not IS Sharpe magnitude.

### F-AXIS #1 — MANDATORY: Bit-Exact Reproducibility (PRIMARY VERDICT GATE)

Run the backtest TWICE with identical inputs. Compare IS Sharpe to 8 decimal places.

| Outcome | Interpretation | Action |
|---|---|---|
| IS Sharpe identical (bit-exact) across 2 runs | **REPRODUCIBLE** — pipeline is deterministic at these HPs | Record F1=PASS; proceed to F2 diagnostic |
| IS Sharpe differs across runs | **HIDDEN-RANDOMNESS-BUG** — pipeline has undiscovered non-determinism | Hard BLOCK; investigate LM Master §"Other Randomness Sources" #1-#10 |

F1 = HIDDEN-RANDOMNESS-BUG if the IS Sharpe differs beyond float rounding (< 1e-8).

### F-AXIS #2 — IS Sharpe vs LM Master Prediction (DIAGNOSTIC; NOT verdict-capping)

Compare observed IS Sharpe to LM Master prediction (+0.08, band [−0.10, +0.20]).

| IS Sharpe | Interpretation | Sub-verdict |
|---|---|---|
| ≥ +0.20 (above band) | OPTUNA-LOTTERY-SOURCE: the basin was always there; Optuna's search WAS the lottery | Confirmed /054's +0.26 was basin-favorable, not noise |
| [−0.10, +0.20] (in band) | NOISE-FLOOR-CONFIRMED: BTC-only head produces ~0 Sharpe in expectation | /054 was a basin-lottery draw; multi-seed mean ≈ 0 is the true signal level |
| << −0.10 (below band) | ARCHITECTURE-DATA-ISSUE: 48-col stack has no edge at single deterministic HP draw | Consider pruning feature stack or abandoning BTC-only specialist |
| NOT bit-exact reproducible | HIDDEN-RANDOMNESS-BUG: pipeline forensics required | Escalate to Phase 5.5 BLOCK |

**LM Master distance metric**: log(|observed − 0.08| + 0.01) — documents calibration distance
in engineering report Section 7 for future LM Master prior refinement.

### F-AXIS #3 — Pre-Registered Diagnostic Falsifier

The diagnostic IS FALSIFIED if:
- F1 = HIDDEN-RANDOMNESS-BUG (non-reproducible across 2 consecutive runs)
- IS trades = 0 (architecture failure — model never fires)

The diagnostic is NOT falsified by any specific IS Sharpe value (the LM Master band is
a prediction, not a gate).

### Section 4.5 — Pre-Registered MERGE/NO-MERGE Criteria (Pre-MERGE §8)

This is a **diagnostic EXPLORATION**, NOT a merge candidate.
MERGE criteria: N/A — methodology iterations are never direct MERGE candidates.

OOS metrics are INFORMATIONAL ONLY per `feedback_v3_dsr_mode_artifact.md` analog.
Verdict is fully determined by F1 reproducibility.

---

## Section 5 — Risk Mitigation

R1/R2/R3 disposition (per Section 3.3):
- **R1**: OFF (same as baseline Model A — BTC has mean-reverting WR at late streaks)
- **R2**: OFF (same as baseline Model A)
- **R3**: OFF (LM Master §"Other Randomness Sources" #9 — disabled to eliminate
  covariance-inversion non-determinism from the experiment)

No new risk primitives introduced or modified. The diagnostic axis explicitly tests the
model training layer; risk-gate settings are fixed to BTC specialist convention.

IS-calibrated thresholds: N/A (no threshold changes).
Simulated effect on prior iterations: N/A (methodology-only axis).

---

## Section 6 — Risk Management Design

8-primitive table (baseline convention; all unchanged from BTC specialist /052-/054):

| Primitive | Status | Setting |
|---|---|---|
| Vol-adjusted sizing (R5 VT) | ACTIVE | vt_target_vol=0.3, vt_lookback_days=45 |
| ADX gate | NOT ACTIVE in v1 (closed axis) | N/A |
| Hurst regime | NOT ACTIVE in v1 | N/A |
| Z-score OOD (R3) | **DISABLED** (/061 specific; LM Master rec) | off for diagnostic |
| Drawdown brake (R2) | OFF | same as /052-/054 BTC specialist |
| BTC contagion (R1) | OFF | same as /052-/054 BTC specialist |
| Isolation forest | NOT ACTIVE in v1 | N/A |
| Liquidity floor | ACTIVE via vol targeting | vt_min_scale=0.33 |

Fire-rate predictions: R3 OFF → 0 OOD rejections (by design). Vol targeting fires as usual
(unchanged from BTC specialist baseline).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The most plausible failure mode is **HIDDEN-RANDOMNESS-BUG** (F1=FAIL): the IS Sharpe
differs between two consecutive identical runs. This would indicate a randomness source
NOT covered by the 10 items in the LM Master advisory. Most likely culprits at BTC-only
single-cell scale:
1. LightGBM thread non-determinism despite `num_threads=1` — if the LightGBM version
   uses an internal thread pool that bypasses `num_threads`.
2. Pandas index alignment non-determinism in feature assembly — if any feature computation
   uses `pd.merge` with duplicate index values.
3. Triple-barrier label tie-breaking on the same candle — `lgbm.py` tie-break rule not
   documented as deterministic.

If HIDDEN-RANDOMNESS-BUG fires, the engineering report must include the IS Sharpe from
both runs and identify which LM Master source #1-#10 was NOT eliminated. This will block
/061 CLOSE until the source is identified and fixed.

The second failure mode is IS trades = 0 (confidence_threshold=0.70 too aggressive for
this HP draw, never generating a trade). This would be an ARCHITECTURE-DATA-ISSUE variant
requiring threshold lowering to confirm the model trains at all.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria

**NOT A MERGE CANDIDATE** — methodology diagnostic iterations never directly update BASELINE_V1.

Pre-registered verdict criteria:
- **REPRODUCIBLE**: F1=PASS (bit-exact IS Sharpe across 2 consecutive runs)
  - Sub-verdict: OPTUNA-LOTTERY-SOURCE (IS ≥ +0.20) / NOISE-FLOOR-CONFIRMED ([−0.10,+0.20]) /
    ARCHITECTURE-DATA-ISSUE (< −0.10) per Section 4 F-AXIS #2
- **HIDDEN-RANDOMNESS-BUG**: F1=FAIL (IS Sharpe differs across runs)
  - Action: pipeline forensics; block cycle-7 until source identified

No absolute Sharpe, DSR, or PBO gate applies. MERGE criteria are N/A.

---

## Section 9 — Library Stack Declaration

| Library | Version | Notes |
|---|---|---|
| lightgbm | pinned in pyproject.toml | Must support `deterministic=True`, `force_col_wise=True`, `num_threads=1` flags |
| optuna | pinned in pyproject.toml | `study.enqueue_trial()` API (available since Optuna 2.5) |
| pandas | pinned in pyproject.toml | `pd.__version__` checked at runner start; must be deterministic for index alignment |
| numpy | pinned in pyproject.toml | NumPy random seeding audited per LM Master §"Randomness Sources" #8 |
| mlfinlab | NOT USED — base v1 pipeline only | |
| pypbo | NOT USED at EXPLORATION budget | |

Fallbacks: none needed. All libraries are available in the standard `uv sync` environment.
LightGBM `deterministic=True` flag requires LightGBM ≥ 3.3.0 (available in the pinned env).
