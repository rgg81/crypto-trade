# LightGBM Master Advisor — iter-v1/042 — Phase 4.5 (Pre-Design)

## Context Read
- Track: v1. Anchor: BASELINE_V1 (`v0.v1-baseline-corrected`, IS +0.2829 / OOS +0.6637).
- /042 axis: MODEL-ARCH XGBoost head-to-head vs LightGBM on V1_FEATURE_COLUMNS_PRUNED (44 cols), 5-cohort, n_trials=18, ENSEMBLE_SIZE=3, single-seed=42.
- Prior model-arch precedent: iter-v1/024 (regime sub-models) ≠ library swap; iter-v3/016 XGBoost on 13-col stack = NEGATIVE-clean at n_trials=10.
- Iteration rationale: /038 LM Master Rec 3 (this iteration's seed) — MODEL family last touched cycle-1 /003; 39+ iter rotation gap.

## 1. XGBoost Hyperparameter Analogues (Optuna search-space mapping)

| LightGBM (current) | XGBoost equivalent | Recommended /042 bound |
|---|---|---|
| `num_leaves ∈ [16, 63]` | NO equivalent — controlled via `max_depth` + `min_child_weight` | `max_depth ∈ [3, 5]` (tightened from LGBM-equiv [3,7]) |
| `min_data_in_leaf ∈ [20, 200]` | `min_child_weight ∈ [1, 20]` | `min_child_weight ∈ [3, 15]` |
| `learning_rate ∈ [0.01, 0.1]` | `eta` (alias `learning_rate`) | identical |
| `feature_fraction ∈ [0.5, 1.0]` | `colsample_bytree` | identical |
| `bagging_fraction ∈ [0.5, 1.0]` | `subsample` | identical |
| `lambda_l1` / `lambda_l2` | `reg_alpha` / `reg_lambda` | identical |
| `min_gain_to_split` | `gamma ∈ [0, 0.5]` | identical |
| n/a (leaf-wise growth) | `tree_method='hist'` + `grow_policy='depthwise'` | LOCK depthwise — single-axis isolation vs LightGBM's leaf-wise |

XGBoost level-wise on depth-3-5 gives ~8-32 effective leaves — **structurally NARROWER than LightGBM's [16, 63]**. For 5-cohort × monthly cell (~150-500 trades), this is the right capacity floor; do NOT extend to depth 6-7 (overfit risk + wall-clock blow-up).

## 2. Wall-Clock Viability — CRITICAL

LightGBM /038 ran ~50 min at n_trials=18 / ENSEMBLE=3 / 5-cohort. XGBoost CPU `hist` is empirically **2-3× slower** at equivalent params on this data scale. Predicted /042 wall-clock: **90-120 min**, with tail risk to 150 min if Optuna selects `max_depth=5` + `subsample=1.0` regions.

**Recommendation: enforce `max_depth ∈ [3, 5]` (NOT [3, 7]) + `tree_method='hist'` (NOT 'exact') + `n_jobs=-1`.** This keeps the run inside the v1 EXPLORATION 2h soft cap. Brief Section 7 must specify the cap and a hard kill at 110 min.

## 3. Optuna Trial-Budget Adequacy

n_trials=18 on XGBoost's 8-dim search space (max_depth, min_child_weight, eta, gamma, subsample, colsample_bytree, reg_alpha, reg_lambda) is **TIGHT**. LightGBM has been at `n_effective_trials = 9` for 2 consecutive iterations (/037, /038) on the same budget — XGBoost's different basin geometry will likely surface a similar saturation at **n_effective ~ 10-12**. Per-cell variance will be HIGHER than LightGBM at this budget — flag for Phase 7.4 trial-stability audit.

## 4. F-AXIS Falsifier Set (recommended)

- **F2 (WIRING, load-bearing)**: runner banner prints `[xgboost]` not `[lgbm]` for all 4 models; `import xgboost; xgboost.__version__` logged at start; first per-cell save shows XGB native model file format (`.json` or `.ubj`), not LightGBM `.txt`. ZERO accidental fallback to `LightGbmStrategy`.
- **F3 (BASIN MIGRATION)**: Jaccard(OOS_trade_roster_XGB, OOS_trade_roster_LGBM_baseline) ∈ [0.20, 0.60]. Below 0.20 = different model entirely (suspect); above 0.60 = effectively no change (suspect mis-wiring). Load-bearing.
- **F4 (OOS Sharpe Δ band)**: PROMISING-CLEAN ≥ +0.10 / PROMISING-INERT-FAV [+0.02, +0.10] / INERT-NO-EFFECT [-0.05, +0.02] / NEG-CLEAN [-0.30, -0.05] / NEG-CAT < -0.30.
- **F5 (WALL-CLOCK)**: hard kill at 110 min; if total runtime > 100 min flag for /043 brief Section 0 ("XGBoost wall-clock disqualifies it from CONFIRMATION budget regardless of OOS outcome").

## 5. Prior Distribution (Phase 4.5 forecast)

| Subtype | Prior | Rationale |
|---|---|---|
| PROMISING-CLEAN (Δ ≥ +0.10) | **8%** | v3/016 NEG precedent caps optimism; v1 stack is 3× wider feature set + 2× cohort pool — non-zero residual chance XGB's conservatism (level-wise + `min_child_weight`) helps the small per-cell training cells. |
| PROMISING-INERT-FAV ([+0.02, +0.10]) | **22%** | Library swap on saturated rank-1-5 feature stack (5-iter held-identical) → most likely modest lift if any. |
| INERT-NO-EFFECT ([-0.05, +0.02]) | **35% MODAL** | Saturated feature/loss surface; XGB and LGBM converge on similar basins on this 44-col stack when n_trials=18 = both algorithms find the same dominant ridge. Most-likely outcome. |
| NEG-CLEAN ([-0.30, -0.05]) | **22%** | v3/016 precedent; XGB at n_trials=18 may underfit depth-5 cap vs LGBM leaf-wise at num_leaves=63. |
| NEG-CATASTROPHIC (< -0.30) | **13%** | Wall-clock blow-up forces hard-kill mid-run → partial models → OOS catastrophe. Non-negligible per F5 risk. |

**Combined PROMISING 30% / Combined NEG 35% / INERT 35%.** Skewed slightly NEGATIVE-SIGN — the modal mass is INERT-NO-EFFECT (35%), and NEG outweighs PROMISING by 5pp.

## 6. Saturation Risks to Flag

- **Rank 1-5 feature identity has held for 5 iterations** (/034-/038): `vol_atr_14`, `trend_aroon_osc_50`, `stat_autocorr_lag5`, `oi_delta_30_z90`, `trend_adx_14`. Library swap will NOT surface new features — both XGB and LGBM rank these same primitives via gain. If /042 surfaces the same top-5 in `feature_importance.csv` (likely > 80% probability), the model-arch family is co-saturated with the feature family. This is the most important post-mortem signal.
- **`n_effective_trials = 9` recurrence** is the load-bearing instability flag from /037-/038. Expect XGB to fall in the [10, 12] range; if it falls below 9, n_trials=18 is structurally inadequate for **both** libraries and the issue is the budget, not the architecture.
- **basis_zscore_30 INERT recurrence**: per /038 Rec 1, this feature has been rank ≥15 for 4 consecutive iterations. If /042 keeps it in V1_FEATURE_COLUMNS_PRUNED, XGBoost will inherit the noise. QR should drop it in the brief; LM Master flagged in /038 but it was kept.

## 7. What I Did NOT Recommend, and Why

- **CatBoost as 3-way comparison**: out of scope per single-axis isolation; adds wall-clock + scaffolding risk for marginal additional information. Defer to /044 if /042 INERT.
- **`grow_policy='lossguide'`** (XGBoost leaf-wise mimic): WOULD give head-to-head parity on leaf shape but DEFEATS the experiment — the axis is "different library, same architectural philosophy", and lossguide collapses that distinction. LOCK depthwise.
- **Raising n_trials to 35 for the XGBoost arm**: changes 2 axes simultaneously (library + budget). Keep n_trials=18 to isolate the library axis; expect higher trial-stability variance and flag in Phase 7.4.

## 8. Closing Note

**MEDIUM-LOW confidence in PROMISING outcome (30%).** Modal expectation is INERT-NO-EFFECT (35%) — the v1 feature stack has been at the same rank-1-5 surface for 5 iterations and library swap rarely surfaces new structure without new features. The single most important thing the QR should NOT ignore: **wall-clock F5 is load-bearing at 110-min hard-kill**. If /042 exits cleanly at INERT, the MODEL-ARCH family closes at v1 (both v3/016 + v1/042 NEG-or-INERT = 2-iter recurrence across tracks → axis-closed) and the /044 substrate must pivot to FEATURE-ENGINEERING (composed features per /038 Rec 1) or LABELING (per /038 Rec 2).

---

# Report-Back (≤250 words)

**3 strongest recommendations**:
1. **TIGHTEN `max_depth ∈ [3, 5]`** (not [3, 7]) + LOCK `tree_method='hist'` + `grow_policy='depthwise'`. Single-axis isolation requires structural difference from LightGBM's leaf-wise; depth-5 ceiling caps wall-clock and matches the 150-500 trades/cell capacity floor.
2. **Hard-enforce F5 wall-clock kill at 110 min**. XGBoost CPU is empirically 2-3× slower than LightGBM at equivalent params; /038 ran ~50 min so /042 projects 90-120 min, with tail to 150 min. Brief Section 7 must specify the kill threshold AND a /043 routing note that wall-clock blow-up disqualifies XGB from CONFIRMATION regardless of OOS outcome.
3. **F2 WIRING falsifier is load-bearing**: banner prints `[xgboost]`, `xgboost.__version__` logged, per-cell model artifact is XGB native format. Library swap iterations have a non-trivial silent-fallback risk; treat F2 as Critic Check 1 mandatory.

**Prior distribution**: PROMISING-CLEAN 8% / PROMISING-INERT-FAV 22% / **INERT-NO-EFFECT 35% MODAL** / NEG-CLEAN 22% / NEG-CAT 13%. Combined PROMISING 30% / combined NEG 35%. Slightly NEG-skewed mid-band.

**Wall-clock viability**: BORDERLINE. 90-120 min projected with 13% tail risk to NEG-CAT from hard-kill. Manageable with the tightened max_depth bound; UNMANAGEABLE if QR keeps [3, 7].

**/044 substrate forecast**: If /042 INERT-or-NEG (70% prior combined), MODEL-ARCH family closes at v1 (v3/016 + v1/042 = cross-track 2-iter recurrence) and /044 must pivot to FEATURE-ENGINEERING (composed features per /038 Rec 1) — the rank-1-5 feature identity has been frozen 5 iterations, both libraries inherit the saturation.

---

**File path**: `/home/roberto/crypto-trade/.worktrees/quant-research/briefs-v1/iteration_v1-042/lgbm_advisor.md` (to be created — directory does not yet exist; orchestrator persists this content there).
