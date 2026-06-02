# LightGBM Master Advisor — iter-v1/061 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1
- Baseline: `v0.v1-baseline-corrected` (`f8bc12c`) — portfolio IS +0.2829 / OOS +0.6637 (5-model, 5-seed); BTC pooled (Model A) IS **−0.85** / OOS +3.41
- BTC-specialist anchors: /054 single-seed=42 spread-only 47 cols **IS +0.2614 / OOS −0.84** (favorable basin); /053 BTC 3-seed mean **IS −0.04 / OOS −0.60** (spread 0.31); /058 BTC OI 3-seed mean **IS −0.28 / OOS −0.60** (spread 0.90 — largest catalog record); /059 pool single-seed **IS −0.16**
- QR axis: **strip ALL randomness** — n_trials=1, --seeds 1, subsample=colsample=1.0, bagging_freq=0, hardcoded HPs, BTC-only 48-col stack (basis_zscore_30 added). Diagnostic: does the IS Sharpe collapse, stabilize at the noise floor, or reveal a hidden real edge?

## My Honest Predictions

**IS Sharpe: +0.08** (most likely band [−0.05, +0.20])
**OOS Sharpe: −0.70** (most likely band [−1.20, −0.20])

Reasoning, stripped of hedging:

1. **Without Optuna search**, the model loses the implicit "lottery-pull-toward-favorable-basin" that /054's +0.26 enjoyed. /054 ran 18 trials and picked the IS-CV best (trial 4: n_est=190, depth=4, leaves=41, lr=0.019, subsample=0.985, colsample=0.888, min_child=96, reg_alpha=1.13). That selection itself was a one-step optimization over noise. With n_trials=1 + hardcoded HPs, you're sampling ONCE from the same distribution that produced /058's per-seed reads of [−0.37, +0.22, −0.68].
2. **Without subsampling** (bagging + colsample=1.0), you've removed the only stochastic regularizer LightGBM has at the model level once `random_state` is fixed. The model becomes deterministic given the data + HPs, which is the experiment's point — but it also means OOS variance compresses around the IS-fit, and that fit is to a single 24-month BTC training window with ~330 samples/month (24 × 8h-candle months × ~90 trades = noisy).
3. **BTC single-symbol training set is tiny.** ~5,200 8h candles total over the IS window (2022-03 to 2025-03). With monthly retrain and 24-month rolling, each retrain sees ~4,400 rows after triple-barrier label filtering. At 48 features, the curse of dimensionality is real — a fully-grown tree with leaves=63, subsample=1.0, colsample=1.0 will memorize the training noise. Expect IS Sharpe close to /053 multi-seed mean −0.04 unless your hardcoded HPs accidentally hit /054's favorable region.
4. **OOS regression pattern is the dominant signal.** /053, /054, /058, /059 all show BTC OOS ∈ [−1.30, −0.40] regardless of IS outcome. BTC's 2025-03-onward OOS regime is structurally hostile to the BTC-only specialist head (despite baseline's +3.41 OOS, which came from the **pooled** Model A — BTC+ETH together, NOT BTC alone). My OOS prediction is anchored to the BTC-only specialist's empirical OOS distribution, not the pooled-model OOS.

## Diagnostic Verdict Map (my read of likely outcomes)

| IS observed | Reproducibility | Diagnostic |
|---|---|---|
| ≥ +0.20 + reproducible | (low prob, ~15%) | Optuna+subsampling was the lottery; the basin was always there. BTC has real edge that hardcoded HPs accidentally hit. **Action: re-run with 3 different hardcoded HP draws — confirm not lucky.** |
| ∈ [−0.10, +0.20] + reproducible | (highest prob, ~60%) | BTC is at noise floor. Deterministic training reveals BTC-only specialist head produces ~0 Sharpe in expectation; /054's +0.26 was a basin-favorable draw of Optuna's stochastic search. **Action: BTC-only specialist concept is mechanically valid but edge is below detection at single-seed 48-feature 24-month window.** |
| << −0.10 + reproducible | (~20%) | BTC has NO edge at this stack/architecture. Data is mostly noise; the 48-feature stack adds dimensionality without signal. **Action: prune feature stack aggressively (target 8–12), OR abandon BTC-only specialist for a pooled architecture.** |
| NOT reproducible across re-runs | (~5%) | Hidden randomness — likely `is_unbalance=True` interacting with class proportions, or `force_col_wise=None` LightGBM thread non-determinism. **Action: pipeline forensics; check §"Other Randomness Sources" below.** |

I am most confident in the [−0.10, +0.20] outcome (~60%). The hardcoded-HP-no-subsampling configuration is structurally closer to /053's multi-seed mean than to /054's single-seed favorable basin, because eliminating subsampling does NOT replicate Optuna's basin-hopping — it just freezes one trajectory.

## Recommended Hardcoded HP Values (sensible-defaults; replicating /054's favorable basin posture WITHOUT actually being /054's exact HPs)

Anchor strategy: pick HPs that are **central-tendency** of /054 Trial-15 (best) and Trial-11 (second-best), regularization-favoring, depth-shallow. NOT /054's exact best — that would be HARKing on a single-seed read.

```python
HARDCODED_LGBM_PARAMS = {
    # Tree complexity — depth-shallow, leaves moderate
    "n_estimators":        300,        # /054 best=332 (T15), median across all trials ≈ 280
    "max_depth":           4,          # /054 best=4 dominant; depth-4 is the modal best across months
    "num_leaves":          31,         # 2^4 - 1 = balanced binary; well under the 63 cap
    "min_child_samples":   50,         # /054 best=89; 50 is regularization-conservative central tendency
    "min_split_gain":      0.0,        # LightGBM default; no explicit gain floor

    # Learning rate + boosting
    "learning_rate":       0.05,       # /054 best=0.266 was high-lr+early-stop; 0.05 is conventional safe
    "boosting_type":       "gbdt",     # classical GBDT (NOT dart/goss — those add stochasticity)

    # Subsampling (HARDCODE-OFF per user spec — disables ALL row/col randomness)
    "subsample":           1.0,        # no row subsampling
    "subsample_freq":      0,          # disabled
    "bagging_freq":        0,          # alias of subsample_freq; explicit 0 for safety
    "bagging_fraction":    1.0,        # alias of subsample; explicit 1.0 for safety
    "colsample_bytree":    1.0,        # no column subsampling
    "feature_fraction":    1.0,        # alias of colsample_bytree; explicit 1.0 for safety

    # Regularization — moderate L2 (matches /054 best reg_alpha=0.28)
    "reg_alpha":           0.1,        # L1 — light sparsity prior
    "reg_lambda":          0.1,        # L2 — light smoothness prior

    # Determinism + reproducibility
    "random_state":        42,         # FIXED
    "deterministic":       True,       # CRITICAL — forces LightGBM to skip non-deterministic micro-optimizations
    "force_col_wise":      True,       # avoids row/col mode auto-choice (which can flip across runs)
    "num_threads":         1,          # CRITICAL — multi-threading introduces float-summation order non-determinism

    # Objective + class handling
    "objective":           "binary",   # matches v1 lgbm.py default
    "is_unbalance":        False,      # ⚠️ DISABLE — see "Other Randomness Sources" #1
    "class_weight":        None,       # explicit; no auto-balancing
    "scale_pos_weight":    1.0,        # neutral

    # Misc
    "verbosity":           -1,
    "metric":              "binary_logloss",
}

# Triple-barrier / training schedule (these are runner-level, NOT LightGBM params)
HARDCODED_TRAINING_CONFIG = {
    "confidence_threshold": 0.70,      # /054 best ranged 0.55-0.83; 0.70 is median
    "training_days":        360,       # /054 best=260; 360 = 12-month rolling (cleaner regime split)
    "training_months":      24,        # FIXED per project policy
    "n_trials":             1,         # USER SPEC
    "cv_splits":            5,         # internal CV unchanged (deterministic given seed)
    "cv_gap":               42,        # 8h embargo for triple-barrier 7d horizon
}
```

**Why I deviated from /054's best HPs**: HARKing on /054 Trial 15 would import basin-favorability into the "no randomness" experiment, contaminating the diagnostic. Use central tendency. If you want a "best-case" comparison, run a SECOND configuration with /054's exact best HPs as a separate diagnostic cell — but DO NOT report that as the headline.

## Other Randomness Sources to Eliminate (this is the load-bearing section)

You said "ALL randomness sources eliminated". The Optuna+subsampling+seed list is the obvious surface. Hidden sources that WILL bite you:

1. **`is_unbalance=True`** (current v1 default per `optimization.py:320`). This re-weights the loss function based on the **observed** class proportion in the training window. As training data shifts month-to-month, the implicit `scale_pos_weight` changes — even with HPs hardcoded. SET `is_unbalance=False`, `class_weight=None`, `scale_pos_weight=1.0`. The unbalance handling MUST be deterministic and identical across cells.

2. **LightGBM multi-threading float non-determinism.** Default `num_threads=-1` (all cores) introduces non-determinism in tree split-gain summation due to thread-execution-order-dependent floating-point summation. SET `num_threads=1`. This will roughly 4-8× the wall-clock; that's the price of full determinism. The `deterministic=True` flag alone does NOT cover this without `num_threads=1`.

3. **Optuna `TPESampler` warm-start state.** At n_trials=1, Optuna still uses TPESampler with its default seed (which becomes the random_state from `random_state=42`). But TPESampler's internal numpy RNG can interact with multiprocessing if `study.optimize(n_jobs>1)`. SET `n_jobs=1` in the Optuna call. Alternative cleaner approach: BYPASS Optuna entirely at n_trials=1 — just call the LightGBM training directly with hardcoded HPs. Saves 1 layer of randomness surface.

4. **Triple-barrier label horizon timestamp rounding.** Look at `labeling.py` (or wherever triple-barrier lives) — label timeout in minutes vs candle-aligned timestamps can have ±1 candle off-by-one drift if rounding mode changes. Verify label generation is bit-identical across two consecutive runs (hash the labels CSV).

5. **`compute_embargo_candles` × interval_ms boundary arithmetic.** The /058 walk-forward fix at `walk_forward.py:113` does `train_end_ms = test_start_ms - embargo_ms`. If `embargo_ms` is computed from `compute_embargo_candles()` which reads `label_timeout_minutes / interval_minutes` — verify integer division mode and rounding behavior is deterministic.

6. **Feature-pipeline cache invalidation.** If `features_v1/__init__.py` reads from a cached parquet, and the parquet was generated under a different feature-set version, you can get silent drift. Verify the 48-col stack is regenerated from raw klines for this run (delete `features-v1/BTCUSDT_8h.parquet` first; trust `--regenerate-features` if the runner supports it).

7. **`pandas` series-vs-dataframe index alignment.** Pandas does index-aware arithmetic. If any feature primitive uses `.values` inconsistently across pandas versions, alignment can shift one row. Check `pd.__version__` is pinned in `pyproject.toml`.

8. **NumPy random seeding for any feature normalization step.** Z-score normalization can use a `np.random.seed` if any feature uses bootstrap-based statistics. Audit `features_v1/` for any `np.random` calls.

9. **OOD Mahalanobis gate's covariance inversion.** R3 gate computes Σ⁻¹ on training data; matrix inversion via `np.linalg.pinv` can have numerical non-determinism near singular matrices. For a /061 minimalist experiment, **disable R3** (R1/R2 already off per BTC specialist config). The gate's deterministic re-fit on training data adds another randomness surface for marginal value at single-symbol.

10. **`triple_barrier_labels.py` tie-breaking when TP and SL hit on the same candle.** Verify the tie-break rule is documented and deterministic (e.g., "TP wins" or "first by index"). Triple-barrier label tie-breaks have caused silent drift in v3 cycle-5.

## Methodology Opinion

**Frankly, I think this experiment will produce a value but won't resolve the question the user is asking.** The user's frustration appears to be: "is BTC-only specialist a real signal or a basin-hopping artifact?" Stripping randomness answers a different question: "what is the value of a single deterministic LightGBM fit on this data?" The two are related but distinct.

The cleaner experiment for the actual question is: **/054's exact HPs replayed across 10 seeds × 10 outer offsets** = 100 independent reads, then take the 5th/50th/95th percentiles of IS Sharpe. That tells you the FULL basin distribution. n_trials=1 with hardcoded HPs gives you ONE draw from that distribution, and one draw is one draw — you cannot tell from a single observation whether the basin distribution is wide-and-centered-on-0 (matching /058) or narrow-and-centered-on-+0.20 (matching /054).

**That said**, the user's experiment IS valuable for ONE specific diagnostic: if IS Sharpe is reproducible across re-runs (bit-identical), it proves the pipeline has zero hidden randomness AT THESE HPs. That's a foundational requirement before doing multi-seed re-analysis of /054. So I support running /061 — but the actionable result is the **reproducibility check across 3 consecutive identical runs**, not the IS Sharpe value itself.

**Recommendation to QR**: run /061 as specified, but ALSO commit a `briefs-v1/iteration_v1-061/reproducibility_check.py` script that runs the same config 3× consecutively and asserts bit-identical IS Sharpe. The diagnostic value is in the IDENTITY of the 3 reads, not their value.

## What I Did NOT Recommend, and Why

- I did NOT recommend importing /054's exact best HPs (Trial 15: lr=0.27, leaves=57, depth=4, min_child=89, reg_alpha=0.28). HARKing contamination — that would smuggle basin-favorability into the "no randomness" frame and confound the diagnostic.
- I did NOT recommend dropping features (48 → smaller). The user explicitly fixed the feature stack at 48; my role is to advise on the LightGBM frame around it, not re-litigate the QR's feature decision.
- I did NOT recommend changing `training_months=24` (FIXED per project policy per `feedback_training_window.md`).
- I did NOT recommend enabling DART or GOSS boosting — both add stochasticity that defeats the experiment's purpose.

## Closing Note

**Confidence: MEDIUM-LOW (~55%)** that this experiment will resolve the user's question. **Confidence: HIGH (~90%)** that IS Sharpe lands in [−0.10, +0.20]. **Confidence: HIGH (~85%)** that OOS Sharpe is negative.

The single most important thing the QR should NOT ignore: **run the reproducibility check.** A single n_trials=1 read at a single seed is one observation from a distribution we already know has spread 0.90 (per /058). The DIAGNOSTIC value is whether the pipeline produces bit-identical output across consecutive runs at fixed HPs — which proves zero hidden randomness — NOT whether that bit-identical IS Sharpe happens to be +0.05 or +0.15.

If the user wants to know whether BTC has real edge, the answer requires a 10-seed × 5-HP-grid Monte Carlo sweep (50 reads → empirical CDF of IS Sharpe). One read isn't enough. But one read with a reproducibility certificate IS enough to know the pipeline is honest. That's a worthwhile foundational result.

