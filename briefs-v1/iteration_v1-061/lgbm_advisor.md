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


---

# LightGBM Master Advisor — iter-v1/061 — Phase 7.4 (Post-Mortem)

## Context Read

- Iteration outcome (from `reports-v1/iteration_v1-061/comparison.csv`):
  - **IS Sharpe: −0.8260** (n_trades=224, win_rate=36.2%, MaxDD=55.35%)
  - **OOS Sharpe: −0.0689** (n_trades=82, win_rate=39.0%, MaxDD=8.73%)
  - IS/OOS ratio: 0.0834 (IS catastrophically worse than OOS — inverted from typical overfit pattern)
  - **Bit-exact reproducibility CONFIRMED**: Run-1 IS = Run-2 IS = −0.8260 (basin_diagnostics v1.cross_seed_sharpe_std = 0.0; v3.roster_jaccard FAIL at 0.035 = independent issue, see below)
- Engineering report claim: pipeline produces bit-identical IS Sharpe across consecutive runs at `n_trials=1, seeds=1, subsample=colsample=1.0, deterministic=True, num_threads=1`.
- Brief Section 1 hypothesis (H1): pipeline is reproducible AND IS Sharpe lands in central-tendency band.

## Predictions vs Actual — Honest Accounting

| Metric | Predicted | Predicted band | Actual | Verdict |
|---|---|---|---|---|
| IS Sharpe | **+0.08** | [−0.10, +0.20] (60% prob); [−0.20, +0.30] (90% prob) | **−0.826** | **MISS BY −0.91; FAR BELOW any pre-registered band** |
| OOS Sharpe | −0.70 | [−1.20, −0.20] (~85% confidence) | **−0.069** | **MISS BY +0.63; ABOVE the upper band** |
| Reproducibility | bit-identical | hard prediction | bit-identical Run-1 ≡ Run-2 | **HIT — single correct call** |

**This is a catastrophic prediction miss on the headline IS axis.** I called central-tendency around 0; the model produced −0.826, which is **further from 0 than ANY single BTC-only specialist EXPLORATION in v1 history** (/053 mean −0.04, /054 +0.26, /058 mean −0.28, /059 −0.16). My 60% band [−0.10, +0.20] does not contain the outcome; my 90% band [−0.20, +0.30] does not contain the outcome. The "favorable basin" frame I anchored on was wrong: the basin distribution is wider on the LEFT than the catalog suggested, and the central-tendency HPs I recommended landed in the unfavorable tail.

The OOS miss (predicted −0.70, observed −0.069) is the OPPOSITE direction — I overestimated OOS pain. The model degraded LESS from IS to OOS than the BTC-only catalog pattern predicted; in fact IS was worse than OOS, which is the inverted pattern. Combined, both misses point to the same diagnosis (below).

## Basin-Lottery Diagnosis

Applying the user's pre-committed diagnostic map to (IS=−0.826, reproducible):

- IS ≥ +0.20 + reproducible → OPTUNA-LOTTERY-SOURCE  ❌ (does not apply; IS is far negative)
- IS ∈ [−0.10, +0.20] + reproducible → SAMPLE-SIZE-NOISE-FLOOR  ❌ (does not apply; IS is far below floor)
- **IS << −0.10 + reproducible → DEEPER-ARCHITECTURE-OR-DATA-ISSUE  ✅ FIRES**
- NOT reproducible → HIDDEN-RANDOMNESS-BUG  ❌ (ruled out by bit-identity)

**VERDICT: DEEPER-ARCHITECTURE-OR-DATA-ISSUE.**

What this means concretely: my Phase 4.5 central-tendency HP recipe — `n_estimators=300, max_depth=4, num_leaves=31, learning_rate=0.05, min_child_samples=50, reg_alpha=0.1, reg_lambda=0.1` — when paired with the 48-feature BTC-only training stack at single deterministic fit, does NOT recover any signal. The model is fitting noise plus structural anti-signal. Reproducibility eliminates the hypothesis "the catalog spread was hidden randomness"; it confirms the catalog spread (/053 spread 0.31, /058 spread 0.90) is REAL basin-lottery from Optuna stochastic search, AND my central-tendency HP recipe sits in the unfavorable tail of that lottery distribution rather than its expected value. The Optuna lottery's expected value is NOT central-tendency-HP-Sharpe — those are different statistics.

## Feature Importance Triage

From `reports-v1/iteration_v1-061/in_sample/feature_importance_Model_A_BTC_specialist_061.csv` (48 features, last-month gain):

### Top-3 dominance audit

| Rank | Feature | Gain | % of top-10 gain |
|---|---|---|---|
| 1 | `vol_atr_14` | 14,217.66 | 16.4% |
| 2 | `trend_aroon_osc_50` | 13,205.52 | 15.2% |
| 3 | `stat_autocorr_lag5` | 8,441.91 | 9.7% |

Top-3 cumulative gain ≈ **41% of top-10** (out of 48 features). For a deterministic single-trial fit at 48 features and ~4,400 training rows per retrain, this is a **narrow basin** — three features carry the model. None of these are the iteration's banner feature (`basis_zscore_30` does not appear in this importance CSV — it was promoted as a 48th feature but the runner's `feature_importance_Model_A_BTC_specialist_061.csv` only shows the cohort the runner trained on; `basis_zscore_30` is missing here entirely, which is itself a finding the Critic should verify).

### Dead-weight (rank 47-48 = zero importance)

| Feature | Mean gain | Rank | Verdict |
|---|---|---|---|
| `dot_vs_btc_ret_ratio_30` | 0.0 | 47 | DROP — pure dead weight (LightGBM produced 0 splits) |
| `eth_vs_btc_ret_ratio_30` | 0.0 | 48 | DROP — pure dead weight (LightGBM produced 0 splits) |

Per `feedback_v3_inert_features_at_higher_budget.md`, INERT features at higher Optuna budget actively HARM OOS by enlarging the search space. Here at `n_trials=1` they cannot harm via Optuna (no search), but they still consume column-fraction budget at `colsample_bytree=1.0` and dilute the gain-attribution audit. **Hard recommendation: drop both for next iteration.**

### Missing-from-importance flag

**`basis_zscore_30`** (the iteration's nominal headline feature, committed in `1be3bd1`) does not appear in `feature_importance_Model_A_BTC_specialist_061.csv`. Two possible reasons:
1. The runner trained on a different feature roster than the brief specified, OR
2. The feature was passed but produced 0 splits across all months (importance entry suppressed), OR
3. The CSV column-set is filtered to BTC-cohort specialist's actual training features and `basis_zscore_30` was excluded by some filter.

This is a **forensic ambiguity** the Critic should resolve in Check 4 / Check 8 (data pipeline integrity).

## Hyperparameter Stability — N/A by Construction

`n_trials=1` means zero Optuna trial-history exists. The trial-history stability table I usually produce is empty: there is exactly ONE fit per `(symbol, month)` cell with hardcoded HPs. The cross-seed-variance basin diagnostic CSV confirms: `std_sharpe = 0.0` (only because `n_outer_seeds=1` — std of one number is zero, not a stability claim). The basin diagnostic v1 PASS verdict is **trivially-PASS by construction**, not evidence the model is stable across seeds.

## Gain Concentration Audit

Top-10 captures ~64,360 gain; top-48 captures ~94,800 gain. Top-10 is **~68% of total**. Bottom-20 features (rank 29-48) contribute < 15% of total gain. This is a **moderate-concentration profile**, consistent with a real ML model that's NOT memorizing — but the IS Sharpe is still −0.826, which means the top-10 features are providing strong-signal-to-WRONG-direction. The model is confidently making BAD predictions, not splitting on noise. This is the worst flavor of deterministic-fit-fail: not "model couldn't learn" but "model learned an anti-edge".

## Suspicious Patterns

1. **IS << OOS (inverted-overfit pattern).** IS Sharpe −0.826 with OOS Sharpe −0.069. Normal overfit produces high IS / low OOS. Inverted-overfit (low IS / higher OOS) typically signals: (a) the IS window contains a regime the model fits poorly while OOS happens to contain a regime closer to the model's bias, OR (b) sample-size effects (IS has 224 trades, OOS has 82 — OOS noise floor is wider, masking small effects). The IS MaxDD 55.35% vs OOS MaxDD 8.73% is the dominant signal here: IS contains a ~6× larger drawdown event the model couldn't avoid. The OOS window happens not to contain that event.

2. **v3 basin-diagnostic roster_jaccard FAIL = 0.035** (between iter-061 OOS trade roster and the baseline's BTC OOS roster). Only 4 of 82 OOS trades overlap with the v0.v1-baseline's BTC OOS trade set (114 trades union). This means **the BTC-only specialist trades a fundamentally different roster** than the pooled Model A in baseline — confirming the BTC-only specialist is NOT a "narrow specialist of Model A" but a **structurally different model**. This is independent confirmation that BTC-only-specialist architecture is not a simple extraction from the pooled-baseline edge; it's a separate experiment with separate edge claims (and at this HP recipe, those claims fail).

3. **Per-regime degenerate output.** `per_regime.csv` shows ONE regime row ("unknown") with all 224 IS trades. Regime tagging produced zero non-unknown rows — either the regime classifier wasn't run, or all trades fell into a single regime bucket. The Critic should flag this for Check 6 (regime-conditional robustness) — without regime stratification, we cannot test whether the model fails uniformly or in a specific regime.

4. **`basis_zscore_30` absence from importance CSV** (per §Feature Importance Triage above). If the headline feature isn't in the model, the iteration didn't test what the brief said it would test.

## What This Iteration Confirms / Refutes About Prior LM Master Advisory

**Confirmed:**
- ✅ The pipeline IS bit-deterministic at the specified HP/seed/threading recipe. Run-1 IS = Run-2 IS = −0.826 exactly. The "Other Randomness Sources" §11-list I produced was correct in identifying threading + Optuna + class-balance as the surfaces to seal, and the brief sealed them. **The single hit in my Phase 4.5 was the reproducibility prediction (HIGH confidence call, validated).**

**Refuted (HARD):**
- ❌ My IS prediction +0.08 missed by −0.91. The central-tendency-HP frame was structurally wrong: choosing "modal best across /054 trials" does NOT produce expected-value IS Sharpe. /054 Trial 15 was a basin-favorable DRAW — its HPs (lr=0.27, leaves=57, min_child=89, reg_alpha=0.28) are co-adapted to a favorable basin; picking the "average" of best+second-best is NOT the average of all draws (which is what central-tendency should reflect). I conflated "modal best HPs" with "expected-value HPs" — these are different. The correct anchor for central-tendency would have been the BTC-only catalog MEAN IS Sharpe (/053 −0.04, /054 +0.26, /058 −0.28, /059 −0.16; mean ≈ −0.06) — which actually is closer to where the user's question lives. My prediction was 14 standard errors off (using catalog spread 0.31 from /053 as σ).
- ❌ My OOS prediction −0.70 missed by +0.63. I anchored to BTC-only specialist OOS pattern [−1.30, −0.40]; observed −0.069 sits ABOVE that band. The OOS window in 2025-04 to 2026-06 happens to be milder for the BTC-only specialist's mistakes than the IS window 2023-03 to 2025-03.
- ❌ The 60% probability mass I placed on [−0.10, +0.20] IS was incorrect calibration. A better-calibrated prior would have placed ~30% mass on IS << −0.50 (matching /058 multi-seed worst-case spread).

**Track record after Phase 4.5 → 7.4 cycle:** 1 hit (reproducibility), 2 hard misses (IS magnitude, OOS magnitude). My calibration credibility for BTC-only specialist single-deterministic-fit predictions should be discounted accordingly in the next QR-LM exchange.

## Hyperparameter Tuning Recommendations for Next Iteration

Given the DEEPER-ARCHITECTURE-OR-DATA-ISSUE diagnosis, knob-tuning LightGBM HPs is NOT the next correct axis. The recommendations below are conditional on the QR choosing to continue the BTC-only-specialist arc; if the QR pivots away from BTC-only (to pooled-architecture or to multi-symbol-cohort), most of these are moot.

### 1. **Drop 2 INERT features (`dot_vs_btc_ret_ratio_30`, `eth_vs_btc_ret_ratio_30`) — 48 → 46 columns**
- **What**: literal removal from V1_FEATURE_COLUMNS for BTC specialist cohort
- **Mechanism**: both have 0.0 gain across the entire training history (LightGBM produced zero splits). Per `feedback_v3_inert_features_at_higher_budget.md`, these add dimensional-curse penalty without contributing signal. At higher Optuna budget they would actively harm.
- **Risk**: minimal; pure dead weight removal.

### 2. **Replicate /054's exact best HPs (Trial 15)** as a separate diagnostic cell
- **What**: hardcode `n_estimators=332, lr=0.266, max_depth=4, num_leaves=57, min_child_samples=89, reg_alpha=0.28, subsample=0.985, colsample_bytree=0.888` (which were /054's discovered best per the brief's HP audit)
- **Mechanism**: this isolates "is the basin actually there at /054's chosen HPs?" — separately from "is the central-tendency HP basin a noise floor?". Together with /061 (central-tendency = −0.826) this gives 2 reads of the basin distribution: one from the catalog's favorable-end and one from the central-tendency-low-tail. The spread between them estimates the basin's mode-vs-mean distance.
- **Risk**: HARKing concern if reported as a banner result — but reported as a DIAGNOSTIC paired with /061, it's exactly what /061 was supposed to do but didn't (single-draw inference). Frame: "/061 sampled the central-tendency tail; /062 samples the catalog-best tail; together they bracket the basin distribution."

### 3. **Run a 10-seed Monte Carlo sweep at /054's exact best HPs** (proper basin distribution measurement)
- **What**: 10 independent random_state values (0..9) × hardcoded /054-Trial-15 HPs × single n_trials=1 fit per seed = 10 IS Sharpe reads
- **Mechanism**: this is the experiment I recommended in my Phase 4.5 closing note. Estimates the 5th/50th/95th percentile of IS Sharpe at the basin-favorable HP region. Tells the user definitively whether /054's +0.26 was a draw from a Sharpe>0 distribution or a tail-sample from a Sharpe≈0 distribution.
- **Risk**: cost ~10× /061's wall-clock; cycle-7 budget impact ~30 min at single-cell config; acceptable for a clarity-resolving diagnostic.

### 4. **Investigate `basis_zscore_30` absence from importance CSV** (forensic)
- **What**: read `run.log` or `engineering_report.md` to confirm `basis_zscore_30` was passed to the model
- **Mechanism**: if the brief's headline feature wasn't actually in the training set, the iteration didn't test what it said it would. Critic should flag this in Check 4 (data pipeline) and Check 8 (claim/code alignment).
- **Risk**: pure forensic; no model change.

### 5. **Stop trying to extract edge from BTC-only-specialist at this stack** (architectural recommendation)
- **What**: pivot the next cycle-7 EXPLORATION away from BTC-only single-symbol training
- **Mechanism**: 6 BTC-only-specialist EXPLORATIONs (/053, /054, /057, /058, /059, /061) span IS Sharpe [−0.83, +0.26] across single-seed reads — a spread of 1.09. The catalog now contains enough data to declare: **BTC-only-specialist edge, if any, is below the single-seed detection floor at 24-month-rolling × 48-feature × LightGBM defaults**. Continuing to tune HPs within this architecture is knob-trap territory (see `feedback_adx_axis_asymmetric_v3.md` for v3 precedent). Per `feedback_v3_structural_over_knob_exploration.md`, the next axis should be structural: pooled-architecture, multi-symbol cohort, or feature-family shift — NOT another BTC-only-specialist HP tweak.
- **Risk**: closing an axis the user might want to keep open; documented here so the QR can override if the user explicitly extends.

## Closing Note for Critic (Phase 7.5)

Three items deserve Critic attention regardless of axis verdict:

1. **`basis_zscore_30` provenance.** The brief promotes it as the iteration's banner feature; the importance CSV does not list it. Check 8 (claim/code alignment) should resolve whether the feature was actually in the training set. If absent, the iteration's nominal hypothesis was not tested.

2. **Bit-identical reproducibility is the ONLY validated H1 sub-claim.** The user's prediction-map says reproducibility → "pipeline is honest". This was confirmed. But the IS magnitude prediction was off by −0.91. The iteration's PROCEDURAL claim (zero hidden randomness) is supported; the iteration's SUBSTANTIVE claim (central-tendency Sharpe is meaningful) is refuted. The Critic verdict should distinguish these.

3. **Per-regime CSV degenerate ("unknown" row only).** Check 6 (regime-conditional robustness) should flag that regime classification produced zero non-unknown rows — either the classifier wasn't applied, or all 224 IS trades fell in a single regime bucket. Either way, regime-stratified robustness cannot be evaluated for this iteration.

I am NOT recommending a verdict; the Critic 8-check authority is independent. I AM flagging that my Phase 4.5 IS-magnitude prediction missed catastrophically, which the Critic should consider in their review of whether the brief's pre-registered HP recipe was appropriate.
