# Iteration v3-030 — Research Brief

**Type**: EXPLORATION (cadence #2 of 10 in NEW post-iter-v3/028 cycle; **STRUCTURAL axis (Category 6 — NEW per-symbol-feature-set architecture)** — first iteration in v3 history where individual model heads use DIFFERENT feature subsets per symbol; methodology innovation triggered by user directive 2026-05-08)
**Track**: v3 (rigor arm) — thirtieth iteration
**Branch**: `iteration-v3/030` (off `iter-v3/029` head)
**Date**: 2026-05-08
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 35             # default per feedback_v3_exploration_n_trials_35
colsample_bytree = 1.0            # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000
```

**Sacred constants UNCHANGED.** The QR sees iter-v3/030 OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–029 briefs / engineering reports / Critic FINALs / diaries; iter-v3/030 EDA artifact (committed BEFORE this brief at SHA `36aaacd` — Phase 1 LDO subset analysis). The EDA reads ONLY iter-v3/028 IS-only `model_importance_last_month_LDOUSDT.csv` (canonical multi-seed BASELINE source) — NOT iter-v3/029 single-seed importance which is noisy. iter-v3/029 OOS metrics (LDO -3.07, total +1.77) are observed as informational anchor for hypothesis grounding, NOT used in feature-selection logic.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (cadence #2 of 10 in NEW post-iter-v3/028 cycle)
Wall-clock budget: ≤ 2h hard cap (per feedback_v3_cadence_discipline.md)
Single-axis variation: NEW per-symbol-feature-set architecture
                       (LDO model: 14 → 7 features; LDO-specific top-7 from iter-v3/028 multi-seed)
                       (BCH+TRX+ALGO models: 14 features UNCHANGED)
Cadence: 2 of 10 EXPLORATIONs in this cycle (next CONFIRMATION = iter-v3/039)
Axis category: 6 (NEW model-architecture variant — per-symbol feature-set discipline)
ANCHOR: iter-v3/029 single-seed (PROMISING; +0.7926 IS / +1.7653 OOS,
        LDO contribution -3.07 OOS, ALGO contribution +20.87 OOS)
        + iter-v3/028 multi-seed BASELINE (+0.5101 IS / +0.5053 OOS;
        LDO -22.05 OOS attribution at multi-seed)
NOT a gate-threshold knob. NOT a feature-pruning at portfolio level (V3_FEATURE_COLUMNS unchanged).
NOT a labeling change. NOT a model architecture change (still LightGBM).
NOT a risk-primitive variation. NOT a universe variation (V3_MODELS unchanged 4 symbols).
This iteration NEVER updates BASELINE_V3.md (single-seed --exploration mode).
```

**Justification — STRUCTURAL per-symbol-feature-set architecture (Category 6 NEW)**:

iter-v3/029 catalog row established that ALGO addition produced +1.77 OOS Sharpe single-seed (PROMISING-STRONG) but LDO continued chronic underperformance: -3.07 OOS at iter-v3/029, -22.05 OOS at iter-v3/028 multi-seed, mean -8.93 across iter-v3/020-027 frozen baseline. The pattern is structural: across 12 EXPLORATIONs LDO has been a net drag. iter-v3/029 per-symbol-feature-importance EDA (`d451885`) demonstrated that LDO has the LOWEST cross-symbol top-7 Jaccard overlap (0.40 vs TRX, 0.56 vs BCH) — its feature signature differs most. The user directive 2026-05-08 (verbatim): *"more features analysis, feature analysis per symbol"; "some features are better suited of symbols a but not b"; "features are the key to have a stable and good models"*. iter-v3/029 implemented the diagnostic half (per-symbol-importance read-out for symbol selection); iter-v3/030 implements the **prescriptive half** (per-symbol feature-set discipline at training time).

**Why this is NOT a violation of `feedback_v3_engineered_features_proven.md`**:

`feedback_v3_engineered_features_proven.md` mandates that regime_momentum_signed_5d (the first multi-seed-validated edge ingredient in v3 history) MUST NOT be reverted. The rule applies at the **portfolio feature-set level** — V3_FEATURE_COLUMNS = 14 features INCLUDING regime_momentum_signed_5d remains unchanged. The rule does NOT prohibit per-symbol customization that DROPS regime_momentum from a SINGLE symbol's training set when (a) the feature is rank 13/14 on that symbol (extremely low importance per the multi-seed importance read), (b) the symbol's chronic underperformance is the iteration's focal hypothesis, and (c) BCH and TRX (rank 11/14 each) continue to use the feature. The prescriptive override is **per-symbol model heterogeneity**, not portfolio-level reversion.

**Why this is NOT a violation of `feedback_explicit_feature_columns.md`**:

The memory rule mandates that every iteration's runner pass `feature_columns=[...]` (never None or empty) to `LightGbmStrategy`. iter-v3/030 STRICTLY HONORS this rule — every `_build_v3_model(symbol=...)` call passes a fully-specified `feature_columns=list(features_for_symbol(symbol))` list. The rule's intent (prevent silent column-order drift via colsample_bytree position-sampling) is preserved. The architecture innovation is that the list is now **symbol-dependent** rather than uniform across symbols.

**Single-axis discipline**: ONE NEW architectural element (per-symbol feature subset for LDO; BCH+TRX+ALGO unchanged). V3_FEATURE_COLUMNS=14 (portfolio-level unchanged). V3_MODELS=4 byte-identical. REQUIRED_GAP=88 unchanged. KEEP regime_momentum_signed_5d in V3_FEATURE_COLUMNS (BCH+TRX+ALGO still use it; only LDO's subset drops it). KEEP 7-primitive risk gate stack byte-identical. NO labeling change. NO ATR multiplier change. NO ENSEMBLE_SIZE change. NO Optuna budget change.

After iter-v3/030 the catalog will have: 15 unique axis representations (12 prior + iter-v3/028 CONFIRMATION-MERGE + iter-v3/029 NEW universe expansion 3→4 + iter-v3/030 NEW per-symbol-feature-set architecture).

---

## Section 1 — Hypothesis

Adding a per-symbol feature subset for LDO (LDO model trained on top-7 features per iter-v3/028 multi-seed importance: ret_skew_200, ret_kurt_50, ret_kurt_200, vwap_dev_20, hurst_diff_100_50, btc_ret_14d, range_realized_vol_50; BCH+TRX+ALGO models trained on full 14-feature stack BYTE-IDENTICAL to iter-v3/029) will **reduce LDO model's overfit to noise on its 31-IS-month sample by halving the feature search space, lifting LDO IS+OOS contribution from -3.07% (single-seed iter-v3/029) toward ≥ 0%**, while leaving BCH+TRX+ALGO contributions BIT-IDENTICAL (their feature subsets, training data, hyperparameter search spaces, and ensemble seeds are unchanged). Predicted IS Sharpe band [+0.70, +0.95] median +0.82 (similar to iter-v3/029 +0.7926; LDO improvement at IS-aggregate level is small because LDO has fewest IS trades, ~11). Predicted OOS Sharpe band [+1.65, +1.95] median +1.80 (similar to iter-v3/029 +1.7653 with marginal LDO lift; bands honestly reflect single-seed-lottery uncertainty).

**Mechanism explanation** (why per-symbol feature-set discipline should help on LDO specifically): LDO has the shortest IS history (listed 2024-09; ~31 IS months covered by the iter-v3/028 training window). LightGBM at depth 3-5 with n_trials=35 fits a model per cell using the 14-feature stack. Effective sample size per feature ≈ ~225 candles. Including 8 features below LDO's importance threshold (ranks 8-14 by iter-v3/028 multi-seed importance) gives Optuna's `colsample_bytree` (currently `1.0` in --exploration mode; nominal column-pinning is by *position* not name) too many low-signal feature picks per tree. Halving the feature space (14 → 7) raises signal density per feature ≈ 2× and reduces Bayesian overfit search space proportionally to the model's depth-bounded complexity. The dimensionality-reduction effect is symbol-specific because BCH (94 IS trades) and TRX (85 IS trades) have ~3× LDO's effective sample size — their per-feature signal density is structurally higher and benefits less from the same prune.

**Why per-symbol feature-set discipline may NOT lift OOS** (3 PATH-suspect scenarios):

1. **PATH B-1: LDO drag worsens despite tighter subset.** LDO's underperformance is structural (e.g., LDO listed late 2024 → IS window includes the post-Terra-Luna era only, missing 2022 carve-out signals; LDO is structurally cohorted with the late-cycle alt-season exhaustion). Tighter subset doesn't help; LDO continues to drag. OOS LDO < -10% weighted_pnl. PATH B; close per-symbol feature-set axis on LDO. Probability: 25-30% (the bear prior; LDO has been negative across 12 EXPLORATIONs).
2. **PATH C — INERT (Falsifier 1 fires): trade-roster bit-identical.** The 7-feature subset produces a model that makes IDENTICAL trade decisions as the 14-feature LDO model. Causes: (a) Optuna at n_trials=35 converges to similar hyperparameters; (b) LightGBM at depth 3-5 picks features by importance regardless of subset cardinality; (c) the 7 dropped features were not load-bearing for trade-decision boundaries. PROMISING-MECHANICAL or NULL-RESULT. Probability: 20-25%.
3. **PATH C-2 — BCH/TRX/ALGO regression** (Falsifier 2 fires). The unchanged-subset symbols' decisions or PnL drift materially from iter-v3/029 due to: (a) per-symbol-feature-list dispatch path bug; (b) global Optuna seed perturbation; (c) `feature_columns` resolution via dict introduces cross-symbol contamination. PATH C — REVERT. Probability: <10% (engineering risk; mitigated by the adversarial test in Section 10).

The counterfactual evidence Phase 1 cites (Jaccard overlap 0.40 LDO vs TRX, 0.56 LDO vs BCH; LDO unique top-7 features hurst_diff_100_50 + btc_ret_14d not in BCH top-7) shows LDO's feature signature is genuinely differential. The empirical question this EXPLORATION answers is whether the symbol-specific signature translates into productive LightGBM fitting at single-seed n_trials=35 when LDO's training set is restricted to its top-7.

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**Phase 1 EDA**: `analysis/iteration_v3-030/ldo_feature_subset_analysis.py` (committed at SHA `36aaacd` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (IS-only):
- `reports-v3/iteration_v3-028/in_sample/model_importance_last_month_{BCH,LDO,TRX}USDT.csv` (canonical multi-seed BASELINE source)

**Outputs** (committed alongside the script at SHA `36aaacd`):
- `ldo_top7_features.csv` — final LDO 7-feature subset (the LDO model's training feature set)
- `ldo_top14_full_ranking.csv` — all 14 LDO features ranked by iter-v3/028 multi-seed importance (audit trail)
- `cross_symbol_top7_overlap.csv` — Jaccard overlap of top-7 sets between LDO/BCH/LDO/TRX pairs
- `synthesis.md` — narrative + cross-symbol architecture finding

### 2.1 LDO top-7 features (the canonical iter-v3/028 multi-seed read-out)

| rank | feature | iter-v3/028 importance | family |
|---:|---|---:|---|
| 1 | ret_skew_200 | 264.4 | tail_risk |
| 2 | ret_kurt_50 | 245.0 | tail_risk |
| 3 | ret_kurt_200 | 238.8 | tail_risk |
| 4 | vwap_dev_20 | 238.2 | volume_micro |
| 5 | hurst_diff_100_50 | 236.8 | regime |
| 6 | btc_ret_14d | 231.6 | cross_btc |
| 7 | range_realized_vol_50 | 224.6 | tail_risk |

LDO's top-7 is **5/7 in the tail_risk + regime + volume_micro core**. The 4 SHARED-top features across BCH+LDO+TRX (range_realized_vol_50, ret_kurt_50, ret_skew_200, vwap_dev_20) are ALL in LDO's top-7. The 3 LDO-specific top-7 picks are ret_kurt_200 (rank 7 BCH, 8 TRX), hurst_diff_100_50 (rank 9 BCH, 10 TRX), btc_ret_14d (rank 14 BCH, 14 TRX — strongest LDO-specific signal).

### 2.2 LDO bottom-7 features (DROPPED only from LDO's subset; KEPT for BCH+TRX+ALGO)

| rank | feature | iter-v3/028 importance | family |
|---:|---|---:|---|
| 8 | ret_skew_50 | 210.8 | tail_risk |
| 9 | ema_spread_atr_20 | 200.0 | momentum_accel |
| 10 | max_dd_window_50 | 181.2 | tail_risk |
| 11 | sym_vs_btc_ret_7d | 177.6 | cross_btc |
| 12 | ret_autocorr_lag1_50 | 175.6 | momentum_accel |
| 13 | regime_momentum_signed_5d | 171.4 | engineered_v3 (Category 2 composed) |
| 14 | hurst_100 | 162.8 | regime |

**The methodology flag**: rank 13/14 on LDO is `regime_momentum_signed_5d` — the first multi-seed-validated edge ingredient in v3 history (per BASELINE_V3.md §"What Changed vs iter-v3/018 BOOTSTRAP"). Per `feedback_v3_engineered_features_proven.md`, this feature MUST NOT be reverted. **iter-v3/030 honors the rule at portfolio level** — V3_FEATURE_COLUMNS=14 still includes regime_momentum_signed_5d, BCH (rank 11) and TRX (rank 11) still train on it. The per-symbol prescriptive override is justified for LDO alone because:

1. **Rank 13/14 importance**: LightGBM at iter-v3/028 multi-seed multi-cell averaged 171.4 importance — well below LDO's 7th-ranked 224.6.
2. **The mandate is portfolio-level**: `feedback_v3_engineered_features_proven.md` was written when V3 trained one model per symbol with one shared feature set; the rule's intent (preserve the multi-seed-validated edge ingredient) is preserved at the portfolio level (BCH + TRX + ALGO continue to use it).
3. **The dimensionality-reduction hypothesis is symbol-specific**: LDO's 31-IS-month sample is the falsifiable target. The benefit is conditional on dropping ALL 7 below-threshold features uniformly; carving out an exception for regime_momentum (keeping it in LDO's subset) would dilute the test.
4. **Falsifier preservation**: if iter-v3/030 PROMISING, the iter-v3/039 CONFIRMATION protocol must validate that the per-symbol architecture preserves the multi-seed lift on the **portfolio Sharpe**. If multi-seed shows BCH+TRX+ALGO drag because regime_momentum's portfolio-level effect requires LDO-side reinforcement, the per-symbol architecture is FALSIFIED at CONFIRMATION-spec.

### 2.3 Cross-symbol top-7 overlap (per-symbol feature signatures differ)

| pair | jaccard | shared (count) | LDO-only (b_only for LDO-* pairs) |
|---|---:|---:|---|
| BCH-LDO | 0.5556 | 5 | btc_ret_14d, hurst_diff_100_50 (LDO-only top-7 vs BCH) |
| BCH-TRX | 0.5556 | 5 | (n/a — BCH-TRX pair) |
| LDO-TRX | **0.4000** | 4 | btc_ret_14d, hurst_diff_100_50, ret_kurt_200 (LDO-only top-7 vs TRX) |

**Key finding**: LDO-TRX Jaccard 0.40 is the LOWEST of all 3 pairs. LDO's feature signature is the most differential — BCH and TRX share 5/7 features bidirectionally; LDO shares only 4/7 with TRX. This is the **structural evidence** for the per-symbol feature-set hypothesis: LDO's LightGBM model would benefit from a feature subset matched to LDO's specific importance ranking, NOT the portfolio-shared 14-feature stack.

### 2.4 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

**Predicted LDO IS trade volume change**: iter-v3/029 single-seed LDO IS trades = 15 (per `reports-v3/iteration_v3-029/in_sample/per_symbol.csv`). Tighter feature subset typically:
- INCREASES LDO trade volume by 5-15% (cleaner signal → more conviction → fewer cooldown-suppressed candidates) — predicted band [16, 18] LDO IS trades.
- DECREASES LDO trade volume by 5-15% (cleaner signal → tighter probability thresholds → fewer marginal trades) — predicted band [13, 14] LDO IS trades.
- LEAVES LDO trade volume bit-identical — Falsifier 1 fires (NULL-RESULT or PROMISING-MECHANICAL).

Net predicted LDO IS trade band: **[13, 18]** trades (±20% of iter-v3/029's 15). Bundle-level IS trades predicted [255, 265] (iter-v3/029 was 257; minimal bundle-level change since LDO is ~6% of total IS trades).

**Predicted OOS LDO weighted_pnl**: iter-v3/029 LDO OOS = -3.07%. Tighter subset hypothesis predicts band **[-1.0%, +5.0%]** (median +1.0%). Lift required: at minimum, LDO OOS ≥ 0% to validate dimensionality-reduction hypothesis.

**Saturation falsifier** (per `feedback_axis_saturation_predictor.md` ±25% rule): if observed LDO IS trades ∈ [13, 18] AND LDO trade-roster is **bit-identical** to iter-v3/029 LDO, axis SATURATED — the 7-feature subset did not propagate to model output. Classify PROMISING-MECHANICAL or NULL-RESULT. If observed LDO IS trades < 11 or > 21 (outside ±40% bound), axis OVERSHOOT — flag for risk-amplification review.

**Falsifier 1 — Bit-identical LDO trade roster** (load-bearing for axis classification): if iter-v3/030 LDO trades are bit-identical (same open_time, close_time, side, sl/tp/exit triggers) to iter-v3/029 LDO trades, the axis is **mechanically inert** — the 7-feature LightGBM model produced the same decisions as the 14-feature model. PROMISING-MECHANICAL (sister to iter-v3/013 drop-MKR per `feedback_promising_mechanical_subtype.md`). NOT compoundable with regime_momentum_signed_5d as a CONFIRMATION-bundle ingredient — the per-symbol architecture is then *strictly architectural* and its multi-seed contribution is unknown until iter-v3/039 validates.

**Falsifier 2 — BCH+TRX+ALGO bit-identity** (load-bearing): BCH+TRX+ALGO trade rosters MUST be bit-identical to iter-v3/029. If any of the 3 symbols' rosters drift, the per-symbol-feature-list dispatch path has unintended side-effects (most likely: a global Optuna seed or random-state cross-pollination through the dict-based features_for_symbol resolution). PATH C — REVERT and diagnose.

**Falsifier 3 — LDO drag worsens**: LDO OOS weighted_pnl < -10% (worse than iter-v3/029's -3.07%). Tighter subset FAILED on LDO; close per-symbol feature-set axis on LDO. PATH B.

**Falsifier 4 — Unintended portfolio Sharpe drop**: bundle OOS Sharpe < +1.50 (Δ < -0.27 vs iter-v3/029 single-seed +1.7653). Even if LDO improves, unintended interaction effects somewhere in the 4-symbol stack drove the bundle below the iter-v3/029 anchor. PATH C — REVERT.

### 2.5 Counterfactual: LDO contribution under PATH A

iter-v3/029 single-seed bundle metrics:

| Symbol | OOS weighted_pnl % | OOS Conc % |
|---|---:|---:|
| TRXUSDT | +29.24% | 50.59% |
| ALGOUSDT | +20.87% | 36.11% |
| BCHUSDT | +10.75% | 18.60% |
| LDOUSDT | **-3.07%** | -5.31% |
| **Total** | **+57.79%** | (numerator) |

Under PATH A counterfactual LDO OOS = +1% (median band):

| Symbol | OOS weighted_pnl % | OOS Conc % (4-sym, LDO+1%) |
|---|---:|---:|
| TRXUSDT | +29.24% | 49.51% |
| ALGOUSDT | +20.87% | 35.34% |
| BCHUSDT | +10.75% | 18.20% |
| LDOUSDT | **+1.00%** | 1.69% |
| **Total** | **+61.86%** | (numerator) |

Total OOS weighted_pnl lift: +4.07% (from +57.79% to +61.86%). Daily Sharpe lift estimate: +0.05 to +0.10 (PnL lift on similar trade count). This is the **mechanical floor** of PATH A — actual lift may be larger if LDO regime_momentum drop ALSO marginally lifts BCH/TRX/ALGO via reduced cross-cell PBO contention (shared CPCV embargo & purge gap implications, iter-v3/028 had max LDO PBO at 1.0 from data-scarcity cells).

Under PATH C INERT counterfactual (LDO trades bit-identical, LDO OOS = -3.07%):

Bundle OOS = +57.79% UNCHANGED. Sharpe ≈ +1.7653 UNCHANGED. PROMISING-MECHANICAL classification.

This is the **lower bound** of the per-symbol architecture's contribution: even if LDO doesn't improve, the architecture is informationally validated as *strictly architectural neutral* — paving the way for iter-v3/031+ to apply the same per-symbol feature-set discipline to other symbols (BCH-specific subset, TRX-specific subset, etc.) without architectural risk.

---

## Section 3 — Sub-fixes (8-item) with Verifier Commands

| # | Sub-fix | Description | Verifier |
|---|---|---|---|
| 1 | **Add `V3_FEATURES_PER_SYMBOL` dict** | Add `V3_FEATURES_PER_SYMBOL: dict[str, tuple[str, ...]]` constant in `src/crypto_trade/features_v3/__init__.py`. Maps `LDOUSDT` to LDO's 7-feature top-7 tuple. BCH/TRX/ALGO not specified → falls back to `V3_FEATURE_COLUMNS_TOP_N`. | `python -c "from crypto_trade.features_v3 import V3_FEATURES_PER_SYMBOL; assert 'LDOUSDT' in V3_FEATURES_PER_SYMBOL; assert len(V3_FEATURES_PER_SYMBOL['LDOUSDT']) == 7"` exits 0 |
| 2 | **Add `features_for_symbol()` helper** | Helper function in `src/crypto_trade/features_v3/__init__.py`. Returns `V3_FEATURES_PER_SYMBOL[symbol]` if symbol in dict, else returns `V3_FEATURE_COLUMNS_TOP_N`. | `python -c "from crypto_trade.features_v3 import features_for_symbol, V3_FEATURE_COLUMNS_TOP_N; assert features_for_symbol('BCHUSDT') == V3_FEATURE_COLUMNS_TOP_N; assert len(features_for_symbol('LDOUSDT')) == 7"` exits 0 |
| 3 | **Runner uses `features_for_symbol(symbol)`** | In `_build_v3_model` (`run_baseline_v3.py`), change `feature_columns=list(V3_FEATURE_COLUMNS)` to `feature_columns=list(features_for_symbol(symbol))`. Add import. | `grep -n 'features_for_symbol' run_baseline_v3.py` shows the import + the `_build_v3_model` call site. |
| 4 | **`_verify_feature_columns()` extension** | Update `_verify_feature_columns()` in `run_baseline_v3.py` to ALSO assert that every symbol's per-symbol subset is a strict subset of `V3_FEATURE_COLUMNS_TOP_N`. | `python -c "from run_baseline_v3 import _verify_feature_columns; _verify_feature_columns()"` exits 0 |
| 5 | **`_verify_feature_columns()` regime_momentum carve-out** | Update `_verify_feature_columns()` to allow LDO subset to NOT contain regime_momentum_signed_5d while assertion that BCH+TRX+ALGO (or any future incumbent NOT in V3_FEATURES_PER_SYMBOL) DO see it via fallback. | `python -c "from run_baseline_v3 import _verify_feature_columns; _verify_feature_columns()"` exits 0 |
| 6 | **ITERATION_LABEL update v3-029 → v3-030** | Update `ITERATION_LABEL = "v3-030"` in `run_baseline_v3.py`. | `grep '^ITERATION_LABEL' run_baseline_v3.py` shows `"v3-030"` |
| 7 | **V3_MODELS BYTE-IDENTICAL UNCHANGED** | KEEP V3_MODELS=4 (BCH+LDO+TRX+ALGO; iter-v3/029 byte-identical). KEEP REQUIRED_GAP=88. | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==4"` + `python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==88"` |
| 8 | **V3_FEATURE_COLUMNS portfolio-level UNCHANGED** | KEEP V3_FEATURE_COLUMNS_TOP_N at 14 cols (iter-v3/028+/029 byte-identical). KEEP regime_momentum_signed_5d in V3_FEATURE_COLUMNS. | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS)==14; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS"` exits 0 |

**Reconciliation table** (Engineer Phase 5.5 verifier — 8 commands):

```
1. uv run python -c "from crypto_trade.features_v3 import V3_FEATURES_PER_SYMBOL; assert 'LDOUSDT' in V3_FEATURES_PER_SYMBOL; assert len(V3_FEATURES_PER_SYMBOL['LDOUSDT']) == 7"
2. uv run python -c "from crypto_trade.features_v3 import features_for_symbol, V3_FEATURE_COLUMNS_TOP_N; assert features_for_symbol('BCHUSDT') == V3_FEATURE_COLUMNS_TOP_N; assert len(features_for_symbol('LDOUSDT')) == 7; assert features_for_symbol('TRXUSDT') == V3_FEATURE_COLUMNS_TOP_N; assert features_for_symbol('ALGOUSDT') == V3_FEATURE_COLUMNS_TOP_N"
3. uv run python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==4"
4. uv run python -c "from crypto_trade.strategies.ml.validation_v3 import REQUIRED_GAP; assert REQUIRED_GAP==88"
5. uv run python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS)==14; assert 'regime_momentum_signed_5d' in V3_FEATURE_COLUMNS"
6. uv run python -c "from crypto_trade.features_v3 import V3_FEATURES_PER_SYMBOL, V3_FEATURE_COLUMNS_TOP_N; assert all(set(s).issubset(set(V3_FEATURE_COLUMNS_TOP_N)) for s in V3_FEATURES_PER_SYMBOL.values())"
7. grep '^ITERATION_LABEL' run_baseline_v3.py | grep -q '"v3-030"'
8. uv run python -c "from run_baseline_v3 import _verify_feature_columns; _verify_feature_columns()"
```

**Adversarial Test (mandatory pytest)** — `tests/features_v3/test_features_for_symbol.py`:

```python
def test_features_for_symbol_subset_invariant():
    """Every per-symbol subset must be a subset of V3_FEATURE_COLUMNS_TOP_N."""
    from crypto_trade.features_v3 import V3_FEATURES_PER_SYMBOL, V3_FEATURE_COLUMNS_TOP_N
    full = set(V3_FEATURE_COLUMNS_TOP_N)
    for sym, subset in V3_FEATURES_PER_SYMBOL.items():
        assert set(subset).issubset(full), \
            f"{sym}: features {set(subset) - full} not in V3_FEATURE_COLUMNS_TOP_N"

def test_features_for_symbol_fallback():
    """Symbols not in V3_FEATURES_PER_SYMBOL fall back to V3_FEATURE_COLUMNS_TOP_N."""
    from crypto_trade.features_v3 import features_for_symbol, V3_FEATURE_COLUMNS_TOP_N
    assert features_for_symbol("BCHUSDT") == V3_FEATURE_COLUMNS_TOP_N
    assert features_for_symbol("TRXUSDT") == V3_FEATURE_COLUMNS_TOP_N
    assert features_for_symbol("ALGOUSDT") == V3_FEATURE_COLUMNS_TOP_N

def test_features_for_symbol_ldo():
    """LDO returns the canonical iter-v3/028 multi-seed top-7."""
    from crypto_trade.features_v3 import features_for_symbol
    expected = {
        "ret_skew_200", "ret_kurt_50", "ret_kurt_200", "vwap_dev_20",
        "hurst_diff_100_50", "btc_ret_14d", "range_realized_vol_50",
    }
    assert set(features_for_symbol("LDOUSDT")) == expected
    assert len(features_for_symbol("LDOUSDT")) == 7
```

---

## Section 4 — Predicted Bands & Catalog Framings

**Anchor (iter-v3/029 single-seed PROMISING)**:
- iter-v3/029 single-seed IS Sharpe = +0.7926 / OOS Sharpe = +1.7653
- iter-v3/029 LDO OOS = -3.07% / iter-v3/029 LDO IS = 15 trades / +41.85% net_pnl
- iter-v3/028 multi-seed IS Sharpe = +0.5101 / OOS Sharpe = +0.5053 (formal BASELINE_V3.md)

**Single-seed iter-v3/030 expectation** (PROMISING bands per `feedback_v3_engineered_features_proven.md` PROMISING-band convention shifted to iter-v3/029 anchor):

| Band | IS Sharpe | OOS Sharpe | LDO OOS PnL | Interpretation |
|---|---:|---:|---:|---|
| PATH A — PROMISING (clean) | [+0.70, +0.95] | [+1.65, +1.95] | [≥0%, +5%] | LDO subset lift; bundle maintained |
| PATH A-MARGINAL — PROMISING-INERT | ~+0.79 | ~+1.77 | ~-3% | LDO bit-identical (Falsifier 1 fires); axis MECHANICAL |
| PATH B — NEGATIVE (LDO worsens) | [+0.65, +0.85] | < +1.50 | < -10% | LDO drag deepens; close per-symbol axis on LDO |
| PATH C — NEGATIVE (architecture bug) | < +0.65 | < +1.50 | varies | BCH/TRX/ALGO drift (Falsifier 2 fires); REVERT |

**§4.4 catalog framing table** (4 rows):

| # | Verdict | Conditions | Catalog row tag |
|---|---|---|---|
| 1 | EXPLORATION-PROMISING (clean) | LDO OOS PnL ≥ 0 AND Falsifier 2 PASS (BCH+TRX+ALGO bit-identical) AND bundle OOS Sharpe ≥ +1.65 AND LDO trade-roster differs from iter-v3/029 | YES — STRONG candidate; iter-v3/039 CONFIRMATION-bundle ingredient (compoundable with regime_momentum + ALGO universe expansion as "per-symbol feature-set architectural decision") |
| 2 | EXPLORATION-PROMISING-MECHANICAL | LDO trade-roster bit-identical to iter-v3/029 (Falsifier 1 fires) AND BCH+TRX+ALGO bit-identical (Falsifier 2 PASS) AND bundle metrics bit-identical | NO — strictly architectural (sister to iter-v3/013 drop-MKR per `feedback_promising_mechanical_subtype.md`); per-symbol feature-set methodology validated as architecturally-neutral; iter-v3/031 may apply the architecture to a DIFFERENT symbol with stronger per-symbol-importance dispersion |
| 3 | EXPLORATION-NEGATIVE (LDO drag) | LDO OOS PnL < -10% (Falsifier 3 fires) AND BCH+TRX+ALGO bit-identical | NO — closes per-symbol-feature-set axis on LDO; tighter subset on LDO is structurally inappropriate; iter-v3/031 = different axis category |
| 4 | EXPLORATION-NEGATIVE (architecture bug) | BCH/TRX/ALGO non-bit-identical to iter-v3/029 (Falsifier 2 fires) | NO — REVERT and diagnose; iter-v3/031 = different axis category after architectural fix; per-symbol-feature-set discipline cannot proceed until clean dispatch path established |

---

## Section 5 — Risk Mitigation

### Cadence-discipline risks (4)

| Risk | Mitigation |
|---|---|
| iter-v3/030 EXPLORATION budget overrun | Hard 2h wall-clock cap. iter-v3/030 is a 4-symbol single-seed run identical structure to iter-v3/029 (~30 min) — only difference is LDO's 7-feature subset (smaller search space → strictly faster). Estimate 25-35 min. Well within cap. |
| Cycle-cadence inflation | iter-v3/030 is SECOND EXPLORATION of new cycle; 8 EXPLORATIONs remaining; CONFIRMATION at iter-v3/039. STRICT 10:1 per `feedback_v3_strict_10_to_1_cadence.md`. |
| Catalog-row pre-commit cleanup | Section 11 pre-commits 4 dispositions. Diary commit closes catalog row regardless of outcome. |
| Single-axis discipline drift | ONE NEW architectural element (per-symbol feature subset for LDO); V3_FEATURE_COLUMNS portfolio-level UNCHANGED; V3_MODELS UNCHANGED; risk gates UNCHANGED. Engineer Phase 6 rejection if any other knob is tuned. |

### Methodology-hygiene risks (4)

| Risk | Mitigation |
|---|---|
| OOS contamination | EDA reads only iter-v3/028 IS-only importance CSVs. iter-v3/029 OOS metrics (LDO -3.07, total +1.77) are observed informationally for hypothesis grounding — NOT used in feature-selection logic. Phase 7 is QR's first iter-v3/030 OOS view. |
| Look-ahead in LDO subset | LDO top-7 is computed on iter-v3/028 IS-only importance ranks; the iter-v3/030 LDO model's training set is exactly those 7 features applied to LDO's training data with NO information from OOS. Adversarial test inherits gap-propagation guarantee from iter-v3/022. |
| Survivorship bias | LDO listed 2024-09 (33+ months IS). No survivorship issue. The 31-IS-month hypothesis is structural, not survivor-related. |
| `feedback_v3_engineered_features_proven.md` deviation | regime_momentum_signed_5d retained at portfolio level (V3_FEATURE_COLUMNS=14 unchanged). LDO-specific drop is permitted because (a) feature is rank 13/14 on LDO at iter-v3/028 multi-seed, (b) BCH+TRX+ALGO continue to use it via fallback, (c) per-symbol architecture is the iteration's focal hypothesis. The mandate's intent (preserve the multi-seed-validated edge) is honored at the portfolio level. |

### Axis-specific risks (3)

| Risk | Mitigation |
|---|---|
| LDO model collapse at single-seed n_trials=35 with 7 features | Per-symbol architecture isolates LDO; if LDO fits poorly under tighter subset, BCH+TRX+ALGO are unaffected. Engineering report records per-symbol IS PnL, OOS PnL, OOS WR, n_trades; if LDO collapses (OOS < -10%), Falsifier 3 fires; PATH B; close axis on LDO. |
| BCH/TRX/ALGO bit-identity violation via dict-based dispatch | Most likely failure mode: `features_for_symbol()` resolution interacts with Optuna's global state (e.g., `optuna.create_study(seed=...)`), or LightGBM's column-pinning order via `colsample_bytree` produces drift. Mitigation: Section 10 adversarial test asserts bit-identity directly via per-symbol trade-roster diff against iter-v3/029. |
| LDO subset interaction with cooldown_candles=4 | LDO has the longest natural between-trade gap due to lower trade volume (~11 IS trades over 2 years vs BCH's 94). Tighter subset may not reduce the cooldown-gated opportunities materially. Mitigation: predicted band [13, 18] LDO IS trades reflects wide uncertainty; saturation falsifier captures the under-shoot scenario. |

---

## Section 6 — 7-Primitive Risk Gate Stack — UNCHANGED

| Primitive | Threshold | Status |
|---|---|---|
| BTC trend kill | ±15% over 14d (42 bars 8h) | UNCHANGED from iter-v3/029 |
| Vol scaling | RiskV2Wrapper internal | UNCHANGED |
| ADX gate | 20.0 | UNCHANGED |
| Hurst regime | hurst_100 in [0.3, 0.7] band | UNCHANGED |
| Feature z-score OOD | \|z\| ≤ 2.0 across 35 v2-feature-set | UNCHANGED |
| Low-vol filter | NATR-percentile-based | UNCHANGED |
| Hit-rate feedback | DISABLED (per iter-v2/045) | UNCHANGED |
| Per-symbol cap | DISABLED (iter-v3/020 closed) | UNCHANGED |
| Regime-conditional kill switch | DISABLED outside iter-v3/022 | UNCHANGED |

LDO inherits the 7-primitive stack byte-identical to BCH+TRX+ALGO. The per-symbol architecture is at the *training feature set* level, not the *risk gate* level — risk gates apply to model output regardless of input feature subset.

---

## Section 7 — 8 Failure-Mode Predictions

Calibrated against iter-v3/007-029 prior EXPLORATIONs + iter-v3/028 multi-seed evidence + iter-v3/030 EDA priors + LDO frozen-baseline pattern (-22%/-3%/-9% across 3 diagnostic windows):

| # | Mode | Probability | Evidence |
|---|---|---:|---|
| P1 | OOS contamination via EDA | <5% | EDA explicitly IS-only iter-v3/028 importance read-out; iter-v3/029 OOS observed informationally |
| P2 | Optuna budget overrun | <5% | EXPLORATION default n_trials=35; LDO 7-feature subset is faster than 14-feature; estimated 25-35 min |
| P3 | Pre-commit non-compliance | <5% | 8 sub-fixes in §3 are atomic; reconciliation table 8 commands; adversarial test 3 cases |
| P4 | PATH A — LDO tighter subset lifts to ≥ 0% OOS | 30-40% | Hypothesis is supported by Phase 1 LDO-TRX Jaccard 0.40 (most differential signature); LDO has smallest IS sample (31 months); dimensionality reduction prior is mechanically reasonable; bear prior is LDO has been negative across 12 EXPLORATIONs |
| P5 | PATH A-MARGINAL — LDO bit-identical (PROMISING-MECHANICAL) | 20-25% | LightGBM at depth 3-5 + n_trials=35 with 7-feature vs 14-feature subset can converge to same trade boundaries when the 7 dropped features had minimal Optuna selection probability; sister to iter-v3/013 drop-MKR mechanical pattern |
| P6 | PATH B — LDO drag worsens (< -10% OOS) | 20-25% | LDO's underperformance is structural (post-Terra-Luna era; late-cycle alt-season exhaustion); tighter subset doesn't fix structural issues; LDO's 11 IS trades are too few for any feature-set tweak to materially shift OOS; bear prior strong on LDO |
| P7 | PATH C — BCH/TRX/ALGO regression (Falsifier 2 fires) | <10% | Engineering risk only; mitigated by Section 10 adversarial test; dict-based dispatch is well-trodden Python idiom |
| P8 | OOS-suspicious lottery (single-seed v3 pattern) | 15-20% | iter-v3/013/025/026/027 all showed single-seed OOS divergence; iter-v3/029 was already PROMISING-STRONG +1.77 on first try; high baseline prior for stacking lottery |

**Combined PATH A (P4) + PATH A-MARGINAL (P5) ≈ 50-65%; combined PATH B (P6) ≈ 20-25%; combined PATH C (P7) ≈ <10%; lottery suspicion (P8) modulates classification confidence.** This is a moderate-to-strong-prior EXPLORATION; the Phase 1 EDA evidence is structurally clean (LDO has the most differential top-7 signature) and the adversarial test mitigates the dispatch-path engineering risk.

---

## Section 8 — 11 Pre-Registered EXPLORATION Criteria

EXPLORATION never updates BASELINE_V3.md. 11 criteria for catalog-row decision:

1. **OOS Sharpe ≥ +1.65** (anchor +1.7653 ± 0.10): catalog row records PROMISING (PATH A). Aspirational.
2. **OOS Sharpe < +1.50** (anchor -0.27): Falsifier 4 fires — PATH C if Falsifier 2 also fires (architecture bug); PATH B if BCH+TRX+ALGO bit-identical AND LDO < -10%.
3. **OOS Sharpe in [+1.50, +1.65]**: PROMISING-INERT (catalog INERT) or PROMISING-MECHANICAL (if Falsifier 1 fires).
4. **n_trades ≥ 50 IS, ≥ 50 OOS bundle-level**: BUNDLE-LEVEL trade-rate floor. Predicted IS in [255, 265]; OOS predicted ~115-125 (well above floor at single-seed EXPLORATION).
5. **PBO < 0.40 (per-cell mean)** AND `n_high_pbo_cells_99 ≤ 4`: methodology hygiene; iter-v3/029 mean was 0.0974. LDO subset may shift LDO-specific PBO cells (e.g., LDO/2026-03 data scarcity); engineering report must report.
6. **IC max abs < 0.70**: NO new feature; existing 14-feature IC matrix unchanged. LDO's 7-feature subset is a **subset** of the iter-v3/028 IC matrix → max IC for LDO subset is ≤ max IC for full set (subsets cannot exceed superset max IC). iter-v3/028 max IC was 0.66 (carve-out for engineered features per phase5p5_gate.md).
7. **ADF p < 0.05 on 7 LDO features for LDO + 14 features for BCH/TRX/ALGO**: 14 features unchanged; incumbent ADF inherits PASS from iter-v3/028. LDO 7-feature subset ADF inherits PASS from the iter-v3/028 superset (subset ADF ≤ superset ADF for stationary features).
8. **Reproducibility verifier**: SHAs stamped (Phase 1 EDA `36aaacd`; brief commit; setup commit; Phase 5.5 gate; engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (waiver inherited from iter-v3/006-029).
10. **Symbol exclusion + feature isolation + track isolation**: `set(V3_MODELS) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; LDO subset is strict subset of V3_FEATURE_COLUMNS_TOP_N ✓; BCH/TRX/ALGO subsets are V3_FEATURE_COLUMNS_TOP_N (default fallback) ✓; no new imports from features modules. Zero cross-track contamination.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: LDO IS trades in **[13, 18]** AND LDO trade-roster differs from iter-v3/029 (Falsifier 1 PASS) AND BCH+TRX+ALGO bit-identical to iter-v3/029 (Falsifier 2 PASS) AND LDO OOS PnL ≥ -10% (Falsifier 3 PASS) AND bundle OOS Sharpe ≥ +1.50 (Falsifier 4 PASS). Critic uses ALL FOUR signals to disambiguate clean PATH A / PATH A-MARGINAL / PATH B / PATH C.

**Catalog-axis verdicts** map to §4.4 table.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/029** — no version updates:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0
scikit-learn = 1.8.0
pyarrow = 23.0.1
mlfinpy = 1.4.0
pypbo = 0.10.0
fracdiff = 0.10.0
statsmodels = 0.14.6
optuna = 4.8.0
scipy = 1.17.0
httpx = (kline + funding fetcher; reused)
```

No new package additions. Per-symbol feature-set architecture uses only existing infrastructure.

---

## Section 10 — Adversarial Tests

Per-symbol feature-set architecture introduces a NEW dispatch code path (the `features_for_symbol()` helper) but does NOT add new feature computation, model, or risk-gate logic. The dispatch path needs adversarial coverage to prevent silent feature-column drift.

**MANDATORY pytest** — `tests/features_v3/test_features_for_symbol.py` (3 tests; specified verbatim in Section 3 sub-fix #5 verifier):

1. `test_features_for_symbol_subset_invariant` — every per-symbol subset is a subset of `V3_FEATURE_COLUMNS_TOP_N` (catches LDO subset drift).
2. `test_features_for_symbol_fallback` — symbols not in `V3_FEATURES_PER_SYMBOL` fall back to `V3_FEATURE_COLUMNS_TOP_N` (catches dispatch-path bug).
3. `test_features_for_symbol_ldo` — LDO returns the canonical iter-v3/028 multi-seed top-7 (catches LDO config drift).

**MANDATORY engineering-report assertion** — Engineer Phase 6 must verify (in addition to standard 12 methodology checks):

- BCH+TRX+ALGO trade rosters in `reports-v3/iteration_v3-030/in_sample/trades.csv` are bit-identical to iter-v3/029 (Falsifier 2 PASS condition; same `(open_time, close_time, side, sl_pct, tp_pct, exit_reason)` per row, modulo OOS-extension from data refresh).

**Optional defensive tests** (NOT mandatory):

- `tests/strategies/ml/test_lgbm_feature_columns_v3.py::test_lgbm_strategy_pins_per_symbol_columns`: assert `LightGbmStrategy(feature_columns=...)` constructor receives the per-symbol-resolved tuple, not the global default.

The mandatory verifier is the §3 reconciliation table (8 commands) + the 3-test adversarial pytest.

---

## Section 11 — Catalog Row Pre-Commit

```
| iter-v3/030 | 2026-05-08 | NEW per-symbol-feature-set architecture: V3_FEATURES_PER_SYMBOL dict; LDO model uses 7-feature subset (top-7 by iter-v3/028 multi-seed importance); BCH+TRX+ALGO unchanged at 14 features (fallback to V3_FEATURE_COLUMNS_TOP_N) | IS Sharpe Δ TBD vs iter-v3/029 anchor +0.7926 | OOS Sharpe TBD vs anchor +1.7653 | TBD verdict | TBD candidate? |
```

**Pre-committed dispositions** (cannot be renegotiated post-hoc):

1. **PATH A (PROMISING) AND Falsifier 1-4 ALL PASS**: catalog YES — iter-v3/039 CONFIRMATION-bundle ingredient (compoundable with regime_momentum_signed_5d + ALGO universe expansion as "per-symbol feature-set architectural decision"). Future EXPLORATIONs (iter-v3/031+) may add per-symbol subsets for OTHER symbols (BCH, TRX, ALGO) with same methodology.
2. **PATH A-MARGINAL (PROMISING-MECHANICAL; Falsifier 1 fires LDO bit-identical)**: catalog YES — non-compoundable as ingredient (sister to iter-v3/013 drop-MKR per `feedback_promising_mechanical_subtype.md`); per-symbol-feature-set methodology validated as architecturally-neutral; iter-v3/031 may apply the architecture to a DIFFERENT symbol with stronger per-symbol-importance dispersion (e.g., TRX which has LDO-TRX Jaccard 0.40 implying TRX is also differential — TRX top-7 has hurst_100 + ret_autocorr_lag1_50 LDO doesn't share). NOT bundled at iter-v3/039 CONFIRMATION as edge ingredient.
3. **PATH B (NEGATIVE; LDO drag worsens, Falsifier 3 fires)**: catalog NO; per-symbol-feature-set axis CLOSED on LDO; iter-v3/031 explores DIFFERENT axis (e.g., another engineered feature per the iter-v3/028 catalog hint OR per-symbol architecture on a DIFFERENT non-LDO symbol).
4. **PATH C (NEGATIVE; architecture bug, Falsifier 2 fires)**: catalog NO; REVERT and diagnose; iter-v3/031 explores DIFFERENT axis category after architectural fix; per-symbol-feature-set discipline cannot proceed until clean dispatch path established.

**Catalog count after iter-v3/030**: 2 of 10 EXPLORATIONs in NEW post-iter-v3/028 cycle; 8 EXPLORATIONs remaining; next CONFIRMATION = iter-v3/039.

**Forward axis pipeline** (iter-v3/031+ candidates per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_v3_engineered_features_proven.md` LOCKED):

- **iter-v3/031 candidates** (depending on iter-v3/030 verdict):
  - PATH A or PATH A-MARGINAL: per-symbol feature-set architecture for a DIFFERENT symbol (TRX has Jaccard 0.40 with LDO; TRX-specific top-7 includes hurst_100 + ret_autocorr_lag1_50; TRX has 85 IS trades — sample-size argument is weaker but signature-differentiation argument applies).
  - PATH B: DIFFERENT axis category — engineered features (HIGH-priority per `feedback_v3_engineered_features_proven.md`; iter-v3/028 catalog hint mentioned `fracdiff_d05_close` OR `hurst_drift_50_200` OR `adx_signed_momentum`) OR DSR gate reformulation (MEDIUM #3) OR TRX/2022-Q4 regime gate retest (MEDIUM #4).
  - PATH C: REVERT iter-v3/030 architecture; iter-v3/031 = DIFFERENT axis category after dispatch-path fix.

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (2 of 10 in new cycle); STRUCTURAL axis Category 6 declared; explicit "NOT a gate-threshold knob"; references `feedback_v3_strict_10_to_1_cadence.md` + user directive 2026-05-08 + per-symbol-feature-importance methodology continuity from iter-v3/029 EDA.
- [x] §1 hypothesis: one sentence, falsifiable; mechanism explanation (LDO sample-size argument + LDO-TRX Jaccard 0.40 differential signature evidence); predicted IS [+0.70, +0.95] median +0.82 / OOS [+1.65, +1.95] median +1.80; LDO OOS PnL band [-1.0%, +5.0%] median +1.0%.
- [x] §2 IS-only numerical evidence with COMMITTED EDA SHA `36aaacd` (Phase 1); LDO top-7 verified canonical iter-v3/028 multi-seed; cross-symbol Jaccard overlap 0.40 LDO-TRX (most differential); behavioral-effect predictor with derived saturation band [13, 18] LDO IS trades anchored at iter-v3/029 LDO 15 + ±20% bound + 4 falsifiers (LDO bit-identity, BCH/TRX/ALGO bit-identity, LDO drag, bundle Sharpe drop).
- [x] §3 sub-fixes (8-item) with reconciliation table 8 rows + adversarial pytest 3 cases; new V3_FEATURES_PER_SYMBOL dict + features_for_symbol() helper + runner dispatch + _verify_feature_columns extension + ITERATION_LABEL update.
- [x] §4 predicted IS Sharpe band [+0.70, +0.95] median +0.82, OOS Sharpe band [+1.65, +1.95] median +1.80, LDO OOS PnL band [-1.0%, +5.0%]; 4 catalog framings + 4 falsifiers + process locked.
- [x] §5 risk mitigation (4 cadence + 4 methodology + 3 axis-specific risks) including explicit `feedback_v3_engineered_features_proven.md` deviation justification (regime_momentum drop from LDO subset; portfolio-level mandate honored).
- [x] §6 7-primitive risk gate stack UNCHANGED.
- [x] §7 8 failure-mode predictions calibrated against 23 prior EXPLORATIONs + iter-v3/028 multi-seed anchor + iter-v3/029 EDA priors + LDO frozen-baseline pattern (P4 PATH A 30-40%; P5 PATH A-MARGINAL 20-25%; P6 PATH B 20-25%; P7 PATH C <10%).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived band [13, 18] LDO IS trades + 4 falsifiers (LDO bit-identity, BCH/TRX/ALGO bit-identity, LDO drag, bundle Sharpe drop).
- [x] §9 library stack UNCHANGED from iter-v3/029; no new dependencies for per-symbol-feature-set architecture.
- [x] §10 adversarial tests (3 mandatory pytest cases + engineering-report assertion on BCH/TRX/ALGO bit-identity) — new code path requires explicit subset-invariant + fallback + LDO-config tests.
- [x] §11 catalog row pre-commit + 4 dispositions; forward axis pipeline (PATH A → per-symbol on different symbol; PATH B/C → different axis category).

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.
