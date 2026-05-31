# iter-v1/042 — EDA Findings (Phase 1)

**Axis**: `model-arch` REPEAT — LightGBM → XGBoost head-to-head library swap.
**Cycle-5 EXPLORATION 9/10** (after /034 NEG-CLEAN, /035 NEG-CAT, /036 PROMISING-CLEAN, /037 PROMISING-CLEAN, /038 NEG-CAT, /039 NEG-CAT, /040 running, /041 in design).
**Prior model-arch v1**: /024 regime-conditional sub-models → NEG-CAT. 2-iter same family acceptable per skill (5+ forbidden).
**Source code touched**: NONE (briefs + analysis only this phase).

---

## 1. XGBoost infrastructure status — ALREADY IMPLEMENTED

Inventory of shipped XGBoost code in this worktree, all from iter-v3/016 (commit `a20c54b`):

| Artifact | Path | LOC | Status |
|---|---|---|---|
| Strategy class | `src/crypto_trade/strategies/ml/xgb.py` | 712 | SHIPPED, library-agnostic on feature_columns + ensemble_seeds |
| Optuna integration | `src/crypto_trade/strategies/ml/optimization_xgb.py` | 396 | SHIPPED, re-exports label helpers from optimization.py |
| Smoke tests | `tests/strategies/ml/test_xgboost_strategy.py` | 219 | PASSES at last v1 HEAD |
| pyproject pin | `pyproject.toml` | — | `xgboost>=2.0,<3.0` (active dep since v3/016) |

**Pinned hyperparameters** (from `optimization_xgb.py:99-113`):

```
tree_method='hist'    # rules out GPU fallback / version drift
grow_policy='depthwise'  # load-bearing architectural difference
n_jobs=1              # determinism with fixed seed
verbosity=0           # silent
random_state=seed
```

**Optuna search space** (XGBoost; 6 hyperparams — 1 less than LightGBM because `num_leaves` is no-op under depthwise):
- `n_estimators ∈ [50, 500]`
- `max_depth ∈ [3, 5]`
- `learning_rate ∈ [0.01, 0.3]` (log)
- `subsample ∈ [0.5, 1.0]`
- `colsample_bytree ∈ [0.3, 1.0]`
- `min_child_weight ∈ [5, 100]`  (replaces LightGBM `min_child_samples`)
- `reg_alpha`, `reg_lambda ∈ [1e-8, 10]` (log)
- `confidence_threshold ∈ [0.50, 0.85]`
- `training_days ∈ [10, 500] step 10`

**v1 wiring needed for Phase 6 (QE work, not QR)**: ONLY the `--model xgboost` CLI dispatch in the v1 runner; XgboostStrategy class is already library-agnostic. Re-validate `tests/strategies/ml/test_xgboost_strategy.py` still passes after dispatch wiring. **NO algorithmic risk** — every algorithmic decision was already vetted in iter-v3/016's Critic FINAL review.

---

## 2. Theoretical architectural delta — LightGBM vs XGBoost (depthwise+hist)

| Axis | LightGBM | XGBoost (pinned) | Bias/variance effect |
|---|---|---|---|
| Tree growth | leaf-wise (best-first) | depth-wise (level-wise) | **depth-wise → LOWER variance per cell** (more conservative); LightGBM leaf-wise greedier on small cells |
| Bin algorithm | histogram + GOSS | histogram (`tree_method='hist'`) | neutral on binning; GOSS gradient sampling absent in XGB → no early-stop on low-gradient rows |
| Class imbalance | `is_unbalance=True` | `scale_pos_weight = n_neg/n_pos` | v1 triple-barrier labels ~symmetric; SMALL effect |
| Optuna search dim | 7 hp | 6 hp (num_leaves dropped) | 1 fewer dim → at n_trials=18, n_eff ~10-12 vs LightGBM's ~9-10 — MORE EFFICIENT search |
| Default leaf cap | num_leaves=31 (~depth 5) | max_depth ∈ [3,5] strict, ≤32 leaves | XGBoost balanced trees grow fewer effective leaves at same depth — modelled bias |
| Determinism | `n_jobs=1 + seed` | `n_jobs=1 + seed` | both deterministic |

**One-sentence summary**: XGBoost's depth-wise growth is a **bias-up / variance-down** swap on the same training cell. The expected sign is regime-dependent: on small noisy cells (v3/016's 5-6k per-sym cells), bias-up is dominant → underfit → NEG. On larger pooled cells (v1's Pool A ~11k pooled BTC+ETH), the variance-down dominates → potential lift.

---

## 3. v1 vs v3/016 regime delta — why the v3 NEG-CAT does not foreclose v1

| Dim | v3/016 (XGB tested here) | v1/042 (XGB to be tested) | Expected XGB sensitivity |
|---|---|---|---|
| Feature count | 13 | **43** | + : depth-wise scales better with feature count; relative XGB advantage SHIFTS up |
| Universe / cohorts | 3 per-symbol | **4 (Pool A pooled + 3 single-sym)** | + : Pool A's 11k bars favor depth-wise's bias/variance tradeoff |
| Candle frequency | 8h | 8h | neutral |
| Optuna budget n_trials | 10 | **18** (+80%) | + : less under-explored; v3/016 n_eff=6 → v1 n_eff~10-12 |
| ENSEMBLE_SIZE | 1 | **3** | + : 3-seed inner average reduces single-trial lottery (the key v3/016 failure mode) |
| Class labels | triple-barrier 8h | triple-barrier 8h EWMA-σ_t | neutral |
| Risk gates | RiskV3Wrapper (7 stack) | R1+R2+R3 baseline (3 stack) | + : v1's softer gates leave more surface for XGB's conservative predictions to express |

**Three of v3/016's failure-mode amplifiers (single-seed inner, n_trials=10, small per-symbol cells) are STRUCTURALLY ATTENUATED in v1.**

---

## 4. Per-cohort capacity analysis

| Cohort | IS bars/cell (~24m) | Per-leaf samples @ 32 leaves | Leaf-wise risk (LGB) | Depth-wise verdict (XGB) |
|---|---|---|---|---|
| Pool A (BTC+ETH pooled) | 11,454 | 358 | LOW | stable: symmetric growth caps per-leaf overfit |
| LINK | 5,727 | 179 | MEDIUM | stable: same as Pool A |
| LTC | 5,727 | 179 | MEDIUM | stable: same |
| DOT | 4,975 | 155 | MEDIUM | stable: same |

**Implication**: Pool A's 358 per-leaf samples easily support depth-wise's symmetric capacity; LINK/LTC/DOT's ~150-180 per-leaf samples are at the THRESHOLD where leaf-wise greediness can over-specialize on noise. XGBoost's depth-wise SHOULD relatively favor the single-sym cohorts. Counter-mechanism: depth-wise's conservatism also flattens FAVORABLE signal — net OOS sign is uncertain.

---

## 5. Predicted F1 band (sums to 1.0)

| Verdict | Weight | Definition | Rationale |
|---|---|---|---|
| **INERT** | **30% MODAL** | OOS Sharpe Δ ∈ [-0.10, +0.10] vs anchor +0.6637 | Library-swap on same data/labels/features often produces ≤0.1 Sharpe Δ when both libraries converge to similar CV-Sharpe basins; v1's amplified n_trials + ENSEMBLE_SIZE smooths the lottery |
| **PROMISING-INERT-FAV** | **25%** | OOS Sharpe Δ ∈ (+0.10, +0.30) | Pool A's 11k bars allow XGB depth-wise to outperform leaf-wise on the pooled cell where LightGBM may over-specialize on BTC vs ETH cross-asset interactions |
| **NEG-CLEAN** | **20%** | OOS Sharpe Δ ∈ [-0.45, -0.10] | v3/016 precedent transfers partially; if depth-wise's underfit dominates we land here |
| **NEG-CAT** | **15%** | OOS Sharpe Δ < -0.45 | v3/016 fired NEG-CAT at -2.53; risk in v1 is HALVED by ENSEMBLE=3 + n_trials=18 but not eliminated |
| **PROMISING-CLEAN** | **10%** | OOS Sharpe Δ > +0.30 | XGB significantly outperforms; LOW prior — published tabular benchmarks (Shwartz-Ziv 2022) show <5% MAE differences between LightGBM and XGBoost on structured data |

**Combined PROMISING (35%) vs Combined NEG (35%) — balanced prior.** This is unusual for a model-arch axis; the balance reflects v1's regime-amplifier mitigation of v3/016's failure modes.

---

## 6. Mechanism rationale — predicted vs LightGBM

XGBoost depth-wise + `tree_method='hist'` is a structurally **more conservative** learner than LightGBM leaf-wise on the same Optuna search space:

1. **Balanced trees** at `max_depth=5` grow symmetrically: each split level adds 2× leaves, capped at 32. LightGBM leaf-wise at `num_leaves=31` may reach 31 leaves at effective depth 4-7 by greedily splitting the highest-gain leaf at each step — this produces **deeper, narrower, more specialized leaves** that fit noise in small cells.

2. **No GOSS gradient sampling** in XGBoost means every row enters every iteration — there is no "early skip" of low-gradient rows that LightGBM uses. On the v1 5-cohort regime, this is mechanically equivalent to a small regularization: low-loss training rows still pull the gradient.

3. **scale_pos_weight** is per-fit recomputed; v1 triple-barrier labels are ~symmetric so this contributes <2% predicted attribution. NOT a load-bearing differential.

4. **Per-leaf samples** at 32 leaves are 358 for Pool A but only ~155-180 for LINK/LTC/DOT. **LightGBM's leaf-wise risks per-leaf overfit on the smaller cohorts** — exactly where iter-v1/038 EDA flagged Optuna's n_eff at 9/18. XGBoost's depth-wise CAPS leaf-specialization → less per-cell overfit but also less per-cell signal extraction.

5. **The basin-migration hypothesis** from /021/022/037/038: LightGBM's IS basin tends to migrate aggressively under small input changes (n_eff=9 pattern; /037 IS contraction; /038 catastrophic basin reshuffle). XGBoost's symmetric growth should produce **smaller basin-to-basin distances** under same Optuna budget → **more stable per-cell trade rosters**. F-AXIS test: Jaccard(XGB roster, LGB roster) > 0.20 supports basin-stability hypothesis.

---

## 7. Top concerns

**C1 — Single-seed basin lottery (PRIMARY).** v3/016 had n_eff=6 at n_trials=10; v1 at n_trials=18 should reach n_eff~10-12 — meaningfully better but not exhaustive. ENSEMBLE_SIZE=3 inner averaging is the structural mitigation. **Monitor**: trial-best Sharpe-vs-final-Sharpe gap per cohort. If gap is large (>0.5 per cell), Optuna under-explored.

**C2 — Trade-count divergence.** XGBoost's depth-wise conservatism translates to fewer high-confidence predictions → fewer trades downstream. **Predicted OOS trade band**: [110, 240] vs anchor 189. Outside this band signals architectural divergence; below 130 hits trade-rate floor (BLOCK).

**C3 — Concentration & MaxDD amplification.** v3/016 produced 4.26× MaxDD inflation (40.62% vs 12.47%). Mechanism: XGBoost's conservative output → fewer trades → per-trade weight concentrates → drawdown amplification. v1's Pool A pooling (BTC+ETH within one model) is a structural diversifier that v3 lacked. **Monitor**: per-cohort PnL concentration. Top-cohort >50% portfolio = catastrophic-amplification fired.

---

## 8. Pre-registered falsifiers for brief Section 4 (handoff to Phase 5)

The brief Section 4 verdict matrix should pre-register:

- **F-AXIS #1 (wiring proof)**: `--model xgboost` dispatch fires per cell; `[iter-v1/042] XGBOOST ACTIVE` banner emitted 100% of cells; xgb.XGBClassifier class assertion in run.log; model_type tag in dsr.json = "xgboost".
- **F-AXIS #2 (trade-rate)**: OOS trades ∈ [110, 240] PASS. Below 130 BLOCK (trade-rate floor). Above 240 informational (XGBoost would be MORE aggressive than LGB — would falsify conservatism mechanism).
- **F-AXIS #3 (Pareto vs anchor)**: F1 OOS Sharpe band per Section 5 table.
- **F-AXIS #4 (basin stability)**: Jaccard(XGB OOS roster, LGB anchor OOS roster) ≥ 0.20 supports basin-stability hypothesis; < 0.10 = BASIN-RELOCATION-ARTIFACT (per /039 pattern, dissolves the mechanism story).
- **F-AXIS #5 (per-cohort attribution)**: per-cohort PnL Δ vs anchor — broadcast IS regression but spare specific cohort = MECHANISM-DIVERGENT pattern (per /037).
- **F-AXIS #6 (importance Spearman)**: feature_importance Spearman ρ(XGB, LGB anchor) — v3/016 saw ρ≈0.56 (importance-divergence prediction confirmed-with-noise-caveat). v1 prediction: ρ ∈ [0.40, 0.75] band.
- **F-AXIS #7 (MaxDD inflation)**: OOS Max DD vs anchor 40.94%. Inflation factor > 1.5× = concentration-amplification fired (per v3/016 4.26× pattern).

---

## 9. Cycle-5 cadence positioning

- EXPLORATION #9/10 (after the 8 previously documented; /040 running parallel).
- Per skill: model-arch family REPEAT (2nd use in v1 history; first since /024). Acceptable.
- HIGH-RISK declaration: LIBRARY SWAP changes Optuna's objective domain (different tree algorithm). v1 rule (per `feedback_v3_promising_mechanical_subtype.md` mode) makes multi-seed OPT-IN. Single-seed acceptable for EXPLORATION; if PROMISING, multi-seed mandatory at CONFIRMATION.
- LM Master Phase 4.5 advisory will be authored separately; my Phase 5 brief MUST respond to its recs.
