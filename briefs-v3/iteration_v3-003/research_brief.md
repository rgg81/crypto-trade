# Iteration v3-003 — Research Brief

**Type**: METHODOLOGY REPAIR (single-file scope)
**Track**: v3 (rigor arm) — third iteration; iter-v3/001 NO-MERGE, iter-v3/002 NO-MERGE
**Branch**: `iteration-v3/003` (off `quant-research`, branched before iter-v3/002 code commits — see Section 9 inheritance note)
**Date**: 2026-05-04
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ensemble_seeds   = [42, 123, 456, 789, 1001]   # 5-seed inner ensemble (v1-style)
```

- **IS window**: from each symbol's first usable kline (with the listing-date floor 2022-09-24, no symbol contributes to walk-forward training before 2022-09-24) through `2025-03-23 23:59:59 UTC` exclusive.
- **OOS window**: from `2025-03-24 00:00:00 UTC` through the data-extent timestamp at backtest time.
- **Walk-forward unit**: monthly retrain, 24-month rolling training window, 1-month OOS prediction window.
- **CPCV unit (inherited from iter-v3/002, unchanged)**: `N=10, k=2 → C(N,2)=45 paths` over the IS-window candle/feature sequence. Purge gap = `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88 candles`. Embargo δ = `max(1, int(0.01 × T))` candles. The `combinatorial_purged_cv(expected_gap=REQUIRED_GAP)` runtime assertion remains the gap guarantee.
- The QR sees OOS metrics for the first time in Phase 7. The QR has produced this brief reading IS-only data plus the iter-v3/002 dsr.json / cpcv_paths.csv / comparison.csv (all committed before this brief, all IS-derived).

---

## Section 1 — Hypothesis

**Modifying `LightGbmStrategy._train_for_month` (in `src/crypto_trade/strategies/ml/lgbm.py`) to persist per-Optuna-trial out-of-fold returns to `reports-v3/iteration_v3-003/trial_oof_returns.parquet`, and rebuilding `_compute_cpcv_paths` to consume that parquet, will produce a `(N_paths × N_strategies)` path matrix with shape `(45, 50)` and cause `pbo_from_cpcv` to return a number in `[0.0, 1.0]` (any number — not NaN).**

This is iter-v3/002 sub-fix #2b (per-Optuna-trial OOF persistence) shipped as a standalone iteration. The headline metrics will match iter-v3/002 EXACTLY because the model is unchanged — only its trial-level OOF logging is added.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-003/pbo_strategy_axis_demo.py` (committed at SHA `9294855` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read**: `reports-v3/iteration_v3-002/cpcv_paths.csv` (45 IS-window CPCV path Sharpes from iter-v3/002, base = +0.257 mean, 1.188 std, 60% positive) — already committed.

**Outputs** (committed alongside the script at the same SHA):
- `analysis/iteration_v3-003/pbo_strategy_axis.csv` — PBO at S in {1, 5, 25, 50, 100} across 3 regimes
- `analysis/iteration_v3-003/persistence_schema.csv` — 6-column spec for `trial_oof_returns.parquet`
- `analysis/iteration_v3-003/synthesis.md` — interpretive narrative

### 2.1 PBO behavior on iter-v3/002's actual S=1 input vs synthetic S>1 expansions

| Regime | S | PBO | Verdict |
|---|---:|---:|---|
| **iter-v3/002 actual paths (no replication)** | **1** | **NaN** | **CURRENT iter-v3/002 STATE — methodology-killer FAIL** |
| iter-v3/002 actual replicated S times (tiling) | 5 | 0.7808 | replica-degenerate (every "strategy" identical → IS-best is never anti-correlated with OOS) |
| iter-v3/002 actual replicated S times (tiling) | 50 | 0.7808 | same — saturates, replication adds no information |
| Near-overfit synthetic (strategy 0 anti-correlated by construction) | 5 | 1.0000 | correctly identifies overfit |
| Near-overfit synthetic | 50 | 1.0000 | same |
| Near-clean IID at empirical (μ, σ) of base paths | 5 | 0.163 | small-S optimism |
| Near-clean IID | 25 | 0.5598 | regression-to-mean baseline |
| Near-clean IID | 50 | 0.7948 | hard to beat OOS-half median at this σ |
| Near-clean IID | 100 | 0.6770 | converges below 0.8 |

Three load-bearing inferences:

1. **Top row exactly reproduces the current state.** PBO=NaN on iter-v3/002's (45, 1) input is what `reports-v3/iteration_v3-002/dsr.json` reports (`"pbo": null`). Critic Check 3 flagged this as the methodology-killer FAIL; iter-v3/003's job is to make this number exist.

2. **Tiling the iter-v3/002 column 50 times is the easy mistake to avoid.** It produces S=50 but PBO=0.78 by replica-degeneracy (every "strategy" is the same path). The persistence schema mandates DISTINCT trial_ids with INDEPENDENT OOF returns, structurally preventing this failure mode.

3. **The near-clean and near-overfit cases bracket what a real iter-v3/003 PBO will look like.** When the lgbm.py modification lands and a real (45, 50) matrix exists, PBO will land somewhere in (0.0, 1.0) — not NaN, not 0.0 by tiling. The number itself is the methodology-validated answer; it is INFORMATIVE regardless of whether it falls in the "good" (<0.4), "chance" (~0.5), or "overfit" (>0.6) zone.

### 2.2 The `LightGbmStrategy._train_for_month` modification surface

Verified by `git show iteration-v3/002:src/crypto_trade/strategies/ml/lgbm.py` — the function is at lines 279-477. The Optuna optimization is delegated to `optimize_and_train` (optimization.py:270-386), which wraps `study.optimize(_objective, ...)` (optimization.py:140-267).

The `_objective` function ALREADY iterates `for fold_k, (train_idx, val_idx) in enumerate(tscv.split(...))` and computes per-fold predictions at line 244-258:

```python
y_proba = model.predict_proba(feat_val)
sharpe = compute_sharpe_with_threshold(
    y_proba, long_pnls[val_idx], short_pnls[val_idx],
    confidence_threshold, ternary=ternary,
)
sharpes.append(sharpe)
```

The OOF returns are IN SCOPE here. iter-v3/003's modification adds ONE persistence side-effect to the objective: append `(trial_id, symbol, train_month, fold_idx, candle_open_time_ms, oof_return)` rows to a buffer per (trial, fold), and after `study.optimize()` returns, flush the buffer to a parquet file.

### 2.3 Volume budget for `trial_oof_returns.parquet`

| Axis | Cardinality |
|---|---:|
| n_optuna_trials per (symbol, month) | 50 |
| n_cv_folds per trial | 5 |
| ~n_test_candles per fold | ~20 |
| n_(symbol, month) cells over IS | 4 syms × ~25 months = ~100 |
| **Estimated rows** | **~500,000** |
| 6 columns × ~8 bytes | ~24 MB on disk |

Negligible compared to the iter-v3/002 backtest wall-clock of 2.16h.

### 2.4 Path matrix construction (consumer side)

```python
# Pseudocode for the rewritten _compute_cpcv_paths
trial_oof = pd.read_parquet(report_dir / "trial_oof_returns.parquet")
n_trials = trial_oof["trial_id"].nunique()  # ≈ 50 × 5 ensemble seeds × 25 months × 4 symbols
combined = (trial_oof
    .groupby(["trial_id", "candle_open_time_ms"])["oof_return"]
    .sum())
splits = combinatorial_purged_cv(n_samples=n_candles, ...)
mat = np.zeros((len(splits), n_trials))
for path_id, (_, test_idx) in enumerate(splits):
    test_candles = candle_timeline[test_idx]
    for trial in range(n_trials):
        path_returns = combined.loc[trial].reindex(test_candles).fillna(0).to_numpy()
        mat[path_id, trial] = mu / sigma sharpe of path_returns
```

The path matrix becomes shape `(45, n_trials)` — exactly the input type CSCV expects.

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Same universe (iter-v3/001 / iter-v3/002). Universe is not on trial. |
| MKRUSDT | KEEP | Same. The MKR sign-flip is a model-level concern; iter-v3/003 changes nothing about the model. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001 / iter-v3/002:
- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t for triple-barrier: past-only ATR (no leak)
- NO meta-labeling (deferred — out of scope)
- Label-horizon-derived purge gap: `gap = (timeout_candles + 1) × n_symbols = 88 candles`

### 3.3 Features — UNCHANGED

`V3_FEATURE_COLUMNS` (34 columns, fracdiff `_dstat` naming with fixed d=0.4) remains the feature set. NO new features. NO auto-d* fracdiff. NO cluster-importance check needed (no additions).

### 3.4 Risk gates — UNCHANGED (v2's 5 active gates + BTC trend filter)

| Gate | Status | Rationale |
|---|---|---|
| Vol scaling (atr_pct_rank_200) | ON | Inherited |
| ADX threshold (20) | ON | Inherited |
| Hurst regime check | ON | Inherited |
| Z-score OOD (\|z\| > 2.5) | ON | Inherited |
| Low-vol filter (atr_pct_rank_200 ≥ 0.33) | ON | Inherited |
| Hit-rate feedback gate | OFF | iter-v2/045 lesson |
| BTC trend filter (±20%, 14d) | ON | iter-v2/019 inheritance |
| R1 — consecutive-SL cooldown | OFF | Same as iter-v3/002 (deferred) |
| R2 — drawdown scaling | OFF | Same |
| R3 — OOD Mahalanobis | OFF | Same |

Identical risk profile to iter-v3/002.

### 3.5 The single architectural change — per-Optuna-trial OOF return persistence

This is iter-v3/003's only meaningful code modification. It corresponds to iter-v3/002 fix #2 sub-fix B (which was silently dropped) plus the consequent fix #5 substrate. Per Critic Recommendation #3, the fix is decomposed into atomic sub-fixes; per Critic Recommendation #1, each sub-fix's reconciliation row references a verifiable file artifact.

| # | Sub-fix | Spec | Code path | File artifact |
|---|---|---|---|---|
| 1a | **Per-trial OOF buffer in `_objective`** | Inside the per-fold loop in `optimization.py:_objective` (lines 211-258), capture `(trial_id, fold_k, val_idx → candle_open_time_ms, val_idx → oof_return)` for every (trial, fold). The OOF return at index `i` in `val_idx` is `compute_per_candle_pnl(y_proba[i], long_pnls[val_idx[i]], short_pnls[val_idx[i]], confidence_threshold, ternary)` — i.e., decompose `compute_sharpe_with_threshold` to expose the per-candle PnL pre-aggregation. | `src/crypto_trade/strategies/ml/optimization.py:_objective` (modify) | Trial buffer accumulates as a list of dicts; not yet persisted. |
| 1b | **Buffer flushed by `optimize_and_train`** | After `study.optimize(...)` returns, `optimize_and_train` aggregates the per-trial buffer for this (symbol, month, ensemble_seed) and writes to disk. | `src/crypto_trade/strategies/ml/optimization.py:optimize_and_train` (modify; new `oof_persist_path` kwarg) | append to `reports-v3/iteration_v3-003/trial_oof_returns.parquet` |
| 1c | **`_train_for_month` plumbs the persist path** | `LightGbmStrategy._train_for_month` (lgbm.py:279-477) constructs `oof_persist_path = self._oof_persist_path` (a new instance attribute set at construction time by the runner) and passes it to `optimize_and_train` per ensemble seed. | `src/crypto_trade/strategies/ml/lgbm.py:_train_for_month` (modify) + `LightGbmStrategy.__init__` (add `oof_persist_path` kwarg, default None) | Strategy instance carries the path. |
| 1d | **Runner passes the path to LightGbmStrategy** | `run_baseline_v3.py:_build_v3_model` builds `LightGbmStrategy(...)` with `oof_persist_path=REPORTS_DIR / "iteration_v3-003" / "trial_oof_returns.parquet"`. | `run_baseline_v3.py:_build_v3_model` (modify) | Path is set per model. |
| 2 | **`_compute_cpcv_paths` reads the parquet, builds (N_paths, S_strategies)** | Replace the current S=1 path-matrix construction (run_baseline_v3.py:448-568) with the consumer pseudocode in §2.4. The matrix shape becomes `(45, n_unique_trials)`. | `run_baseline_v3.py:_compute_cpcv_paths` (rewrite) | `path_metric_matrix.shape[1] > 1` at runtime |
| 3 | **`_compute_n_eff_trials` reads the parquet, builds true (n_trials × T) matrix** | Replace the current per-(symbol, month) zero-padded surrogate (run_baseline_v3.py:1180-1199) with: `mat = trial_oof.pivot_table(index="trial_id", columns="candle_open_time_ms", values="oof_return", fill_value=0).to_numpy()`. Pass to `n_effective_trials`. | `run_baseline_v3.py:_compute_n_eff_trials` (rewrite) | `n_eff > 4` (almost certainly; the surrogate value of 4 was suspiciously equal to n_symbols) |

**File artifacts produced (verifier commands)**:

| Artifact | Verifier |
|---|---|
| `reports-v3/iteration_v3-003/trial_oof_returns.parquet` exists | `python -c "import pandas as pd; df=pd.read_parquet('reports-v3/iteration_v3-003/trial_oof_returns.parquet'); assert df.shape[0] >= 40000, f'Got {df.shape[0]} rows; expected >= 40000 (50 trials × 5 folds × ≥20 candles × ≥80 (sym,month) cells)'"` |
| Parquet schema correct | `python -c "import pandas as pd; df=pd.read_parquet('reports-v3/iteration_v3-003/trial_oof_returns.parquet'); cols={'trial_id','symbol','train_month','fold_idx','candle_open_time_ms','oof_return'}; assert cols.issubset(df.columns), f'Missing: {cols - set(df.columns)}'"` |
| trial_id has > 1 unique value | `python -c "import pandas as pd; df=pd.read_parquet('reports-v3/iteration_v3-003/trial_oof_returns.parquet'); n=df['trial_id'].nunique(); assert n > 1, f'Got n_unique trial_id = {n}'"` |
| `dsr.json["pbo"]` is a number, not None | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-003/dsr.json')); assert d['pbo'] is not None and 0.0 <= d['pbo'] <= 1.0, f'pbo={d[chr(34)+chr(112)+chr(98)+chr(111)+chr(34)]}'"` |
| `cpcv_paths.csv` present | `test -f reports-v3/iteration_v3-003/cpcv_paths.csv` |
| `n_eff_trials > 4` (the iter-v3/002 surrogate value) | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-003/dsr.json')); assert d['n_eff'] > 4, f'n_eff={d[chr(34)+chr(110)+chr(95)+chr(101)+chr(102)+chr(102)+chr(34)]}'"` |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input — per Critic Rec #1)

Each sub-fix from §3.5 has its own row. **Each cell maps to a FILE ARTIFACT** with a verifier command (per Critic Recommendation #1). Empty rows = Phase 5.5 BLOCK.

| Section 3.5 sub-fix | Code path | File artifact + verifier |
|---|---|---|
| 1a — per-trial OOF buffer in `_objective` | `src/crypto_trade/strategies/ml/optimization.py:_objective` | (process artifact: `git diff iteration-v3/002 iteration-v3/003 -- src/crypto_trade/strategies/ml/optimization.py` shows additions to `_objective` for OOF buffering; verifier `git log --oneline iteration-v3/003 -- src/crypto_trade/strategies/ml/optimization.py | wc -l` ≥ 1) |
| 1b — buffer flushed by `optimize_and_train` | `src/crypto_trade/strategies/ml/optimization.py:optimize_and_train` | `reports-v3/iteration_v3-003/trial_oof_returns.parquet` exists with ≥ 40,000 rows (`python -c "import pandas as pd; assert pd.read_parquet('reports-v3/iteration_v3-003/trial_oof_returns.parquet').shape[0] >= 40000"`) |
| 1c — `_train_for_month` plumbs persist path | `src/crypto_trade/strategies/ml/lgbm.py:_train_for_month` + `LightGbmStrategy.__init__` | (process: `git diff iteration-v3/002 iteration-v3/003 -- src/crypto_trade/strategies/ml/lgbm.py` shows `oof_persist_path` param) |
| 1d — runner passes path | `run_baseline_v3.py:_build_v3_model` | `grep -n "oof_persist_path" run_baseline_v3.py` returns ≥ 1 line |
| 2 — `_compute_cpcv_paths` reads parquet | `run_baseline_v3.py:_compute_cpcv_paths` | `dsr.json["pbo"]` is a number in [0, 1], not None: `python -c "import json; d=json.load(open('reports-v3/iteration_v3-003/dsr.json')); assert isinstance(d['pbo'], (int, float)) and 0.0 <= d['pbo'] <= 1.0"` |
| 3 — `_compute_n_eff_trials` reads parquet | `run_baseline_v3.py:_compute_n_eff_trials` | `dsr.json["n_eff"] > 4`: `python -c "import json; d=json.load(open('reports-v3/iteration_v3-003/dsr.json')); assert d['n_eff'] > 4"` |
| Symbols UNCHANGED (BCH, MKR, LDO, TRX) | `run_baseline_v3.py:V3_MODELS` | `grep -E '^V3_MODELS' run_baseline_v3.py` shows the same 4 symbols |
| Risk gates UNCHANGED (v2 5 + BTC) | `RiskV3Wrapper` config | `grep -E "RiskV3Wrapper\\(" run_baseline_v3.py` shows v2 5-gate config, no R1/R2/R3 |
| Features UNCHANGED (V3_FEATURE_COLUMNS, 34 cols) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 34"` |
| Adversarial unit tests inherited from iter-v3/002 still pass | `tests/strategies/ml/test_pbo_synthetic.py`, `test_dsr_negative_is.py`, `test_cpcv_embargo_assert.py` | `uv run pytest tests/strategies/ml/test_pbo_synthetic.py tests/strategies/ml/test_dsr_negative_is.py tests/strategies/ml/test_cpcv_embargo_assert.py -v` exits 0 |
| (NEW) Adversarial test for OOF persistence | `tests/strategies/ml/test_oof_persistence.py` | Test asserts: (a) calling `optimize_and_train` with `oof_persist_path` set creates the parquet, (b) parquet has the 6 prescribed columns, (c) `trial_id` cardinality equals `n_trials`, (d) per-trial row count ≈ `cv_splits × ~val_set_size` (within ±20%). |

### 3.7 NO new feature families, NO meta-labeling, NO auto-d* fracdiff

The iter-v3/002 dead-paths catalog (diary entry 5, second entry) explicitly listed iter-v3/002 as "methodology repair without `LightGbmStrategy` modification" and its successor as "per-trial OOF persistence in `lgbm.py`". iter-v3/003 ships ONLY that single architectural change. Future iterations (iter-v3/004 universe re-evaluation, iter-v3/005 meta-labeling, iter-v3/006 crypto-native features) are explicitly out of scope.

### 3.8 Inheritance plan from iter-v3/002 (mandatory engineering note)

The `iteration-v3/003` branch was branched from `quant-research` BEFORE iter-v3/002's code commits landed. As a result, the working tree on `iteration-v3/003` is MISSING:
- `run_baseline_v3.py`
- `src/crypto_trade/features_v3/` (entire package)
- `src/crypto_trade/strategies/ml/risk_v3.py`
- `src/crypto_trade/strategies/ml/validation_v3.py`
- `tests/strategies/ml/__init__.py`, `test_pbo_synthetic.py`, `test_dsr_negative_is.py`, `test_cpcv_embargo_assert.py`

**Phase 6 step 0** (BEFORE any new modification): the Engineer must `git cherry-pick` or `git checkout iteration-v3/002 -- <files>` to bring the iter-v3/002 src/ + tests + runner into the iter-v3/003 branch. The relevant commit is `267bb1d feat(iter-v3/002): methodology fixes — PBO/CSCV/DSR/ADF/embargo + adversarial tests` and `01a68fb feat(iter-v3/001): features_v3 package + validation_v3 (CPCV/PBO/PSR/fracdiff)`. After that, iter-v3/003's lgbm.py / optimization.py / run_baseline_v3.py modifications layer on top.

The verifier commands in §3.6 row 10 ("Adversarial unit tests inherited from iter-v3/002 still pass") will fail until this cherry-pick lands.

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted impact on iteration metrics

| Metric | iter-v3/002 (NO-MERGE) | iter-v3/003 prediction | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | -0.0746 | **-0.0746 (EXACT)** | 0 (model unchanged) |
| OOS monthly Sharpe | +1.0955 | **+1.0955 (EXACT)** | 0 (model unchanged) |
| OOS trades | 83 | **83 (EXACT)** | 0 (model unchanged) |
| Top-symbol concentration | 53.21% MKR | **53.21% MKR (EXACT)** | 0 (model unchanged) |
| **PBO** | **NaN (S=1)** | **a number in (0.0, 1.0) — value to be observed** | **the iteration's whole point** |
| **n_eff_trials** | 4 (zero-padded surrogate) | **> 4 (true PCA on per-trial OOF matrix)** | **the iteration's whole point** |
| **DSR** | 0.0 (numerically correct) | **0.0 (still — the IS Sharpe is deeply negative; with corrected n_eff it could shift slightly but the `norm.cdf(z)` at z ≈ -18 still rounds to 0)** | minor (algorithm same; n_eff input changes) |
| **PSR** | 1.0 | **1.0** | unchanged (depends on observed OOS SR only) |
| **adf_test.csv row count** | 7242 | **7242 (EXACT)** | unchanged (ADF runner unmodified) |

### 4.2 Falsifier (locked before backtest)

**Primary falsifier**: if the corrected `pbo_from_cpcv` on iter-v3/003's path matrix returns `NaN` or returns a value outside `[0.0, 1.0]`, the methodology is still wrong. Any specific value in `[0.0, 1.0]` is acceptable as a pass on the methodology axis (the value's economic interpretation depends on the strategy and is not on trial here).

**Secondary falsifier**: if `reports-v3/iteration_v3-003/trial_oof_returns.parquet` does not exist post-Phase 6, OR the parquet has shape with `df["trial_id"].nunique() <= 1`, OR row count `< 40,000`, sub-fix #2 was not implemented (same root failure as iter-v3/002 fix #2b).

**Tertiary falsifier**: if `dsr.json["n_eff"]` is exactly 4 (matching the iter-v3/002 surrogate value), sub-fix #3 was not implemented or did not consume the new parquet.

### 4.3 Expected MERGE outcome — split-merge clause inherited from iter-v3/002

iter-v3/003 is methodology repair on a single sub-fix. The model's headline metrics (IS Sharpe, OOS Sharpe, trades, concentration) are expected to MATCH iter-v3/002 EXACTLY. Therefore Section 8 mechanical criteria 1, 2, 3, 4, 5, 6, 11, 17 will fail by design (same as iter-v3/002).

The split-merge clause permits methodology-only merge IF AND ONLY IF:
- (a) Critic OVERALL = MERGE on the methodology criteria (7, 8, 9, 13, 14, 18, 19)
- (b) PBO produces a number in `[0.0, 1.0]` (NOT NaN — Section 8 criterion 8 strict reading)
- (c) n_eff_trials uses real per-trial returns (NOT a surrogate — Section 8 criterion via `dsr.json["n_eff"] > 4`)
- (d) `trial_oof_returns.parquet` exists with ≥ 40,000 rows and the 6 prescribed columns
- (e) Section 8 criteria 13, 18, 19 ALL pass (per iter-v3/002 split-merge precondition)

If (a)–(e) hold, the QR MERGEs the methodology stack only (cherry-picking the relevant src/ + test commits along with docs commits). Headline-metric criteria 1-6, 11, 17 expected to fail by design.

The iter-v3/002 lesson #3 explicitly cautioned: "don't write split-merge clauses that depend on methodology criteria all passing if the methodology fix is risky". iter-v3/003 inherits that lesson by REQUIRING (b), (c), (d) — the three new file-artifact gates — to be hard preconditions. NaN PBO is NOT acceptable in iter-v3/003 (the loophole that allowed iter-v3/002 to ship is closed).

---

## Section 5 — Risk Mitigation

### 5.1 Inheritance — v2's 5 active gates + BTC trend filter

Identical to iter-v3/002. No new risk gates this iteration. The iteration's job is to verify the validation-pipeline upstream completion of iter-v3/002 fix #2 sub-fix B; risk gates are not on trial.

### 5.2 Methodology-pipeline safety — the iteration's actual risk mitigation

Three structural safeguards relative to iter-v3/002's process failure:

1. **File-artifact reconciliation table** (Section 3.6). Each row references a verifier COMMAND, not a description. iter-v3/002's reconciliation cell text "_compute_cpcv_paths consumes a candle/feature DataFrame, NOT a trade list" was true on its own axis but hid sub-fix #2b's omission. iter-v3/003's reconciliation cells point to `trial_oof_returns.parquet` existence + shape + non-empty trial_id cardinality. The cells cannot be filled with prose; the command must execute and exit 0 post-Phase 6.

2. **Adversarial test for OOF persistence** (new, see §3.6 row 11). `tests/strategies/ml/test_oof_persistence.py` asserts the parquet schema and per-trial row count ratios. CI failure = Phase 5.5 BLOCK.

3. **Split-merge clause tightened** (§4.3). NaN PBO is NO LONGER acceptable for the methodology MERGE — iter-v3/002's split-merge clause permitted "NaN with descriptive-stats fallback" because it was designed for the case where S>1 was structurally impossible. iter-v3/003 requires S>1 by Section 3.5 sub-fix #2; therefore NaN now means the sub-fix didn't ship.

These three safeguards target the EXACT failure mode that broke iter-v3/002. iter-v3/002's pre-registered failure-mode prediction missed this (it predicted "Engineer drops per-(sym, feat, month) ADF" and "CPCV-on-candle-sequence wall-clock > 24h" — neither materialized; the actual failure was "Engineer ships fixes in `validation_v3.py`/`run_baseline_v3.py`/`risk_v3.py`/tests but does NOT touch lgbm.py"). iter-v3/003's Section 7 makes the per-source-file shipping risk explicit (Prediction 1).

### 5.3 NO new model-level risks introduced

Headline metrics expected to match iter-v3/002 exactly. No retuning, no re-cleaning, no late-cycle thresholds shifted. Any drift from iter-v3/002 in IS Sharpe / OOS Sharpe / trade count / concentration is itself a signal that the lgbm.py modification accidentally altered the model — Phase 7 evaluation must catch that.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/002

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |
| 8 | (placeholder for future) | — | — | Reserved for iter-v3/008+ |

Combined kill rate target: 69–78%. Same as iter-v3/002.

### 6.2 Regime coverage — UNCHANGED from iter-v3/002

The v3 universe IS data spans 2020-01 → 2025-03-23 (LDO from 2022-09-22). Regime coverage includes 2020 COVID, 2021 bull, 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction.

### 6.3 Concentration — pessimistic baseline acknowledged

MKR concentration expected to remain at 53.21% (criterion 6 fails by design). Same as iter-v3/002. iter-v3/003 does NOT attempt to fix this (out of scope; future iteration iter-v3/004 may revisit universe).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/002's diary lesson #4 noted: "future v3 brief Section 7s should explicitly enumerate per-source-file fixes". iter-v3/003's Section 7 incorporates that lesson.

**Prediction 1 (process-level, P=15%): Engineer fails to cherry-pick iter-v3/002's src/ inheritance per §3.8.** The branch base is BEFORE iter-v3/002's code commits, so iter-v3/003's code modifications layer on a missing foundation. **Detection signal**: `git diff iteration-v3/003 iteration-v3/002 -- src/crypto_trade/strategies/ml/` returns the iter-v3/002 deletions reversed. Mitigation: §3.8 makes the inheritance step explicit; the verifier commands in §3.6 will all fail until the cherry-pick runs.

**Prediction 2 (process-level, P=10%): Engineer modifies `optimize_and_train` and `_train_for_month` correctly but the runner does not pass `oof_persist_path` to `LightGbmStrategy(...)`.** The result would be: parquet not created, PBO=NaN persists, exact same iter-v3/002 outcome. **Detection signal**: `reports-v3/iteration_v3-003/trial_oof_returns.parquet` does not exist; verifier in §3.6 row 1b fails. The Phase 5.5 reconciliation table catches this if the Engineer fills row 1d ("runner passes path") with a file artifact pointer rather than a description.

**Prediction 3 (model-level, P=20%): Engineer modifies `compute_sharpe_with_threshold` decomposition incorrectly and per-candle OOF returns don't reflect trade-level PnL.** The reported `oof_return` would be miscalculated. **Detection signal**: a parquet with the right shape but PBO converges to extremes (0 or 1) outside the synthetic-cases bracket from §2.1, OR the new `test_oof_persistence.py` assertion on per-trial row count fails. Mitigation: the new adversarial test asserts row-count ratios; the Critic's Check 8 (hypothesis-implementation alignment) would catch egregious miscomputation.

**Prediction 4 (model-level, P=30%): PBO lands in [0.5, 0.9].** Given the iter-v3/001 / iter-v3/002 path Sharpes have median +0.118, mean +0.257, only 60% positive (with high variance), and the model is fundamentally a near-random / borderline-anti-edge strategy on this universe, the methodology-validated PBO should reflect that. PBO in this range would CORRECTLY identify the strategy as overfit-to-near-random (which is what we already suspect from iter-v3/002's path Sharpe distribution). This is INFORMATIVE; methodology MERGE is still on the table per §4.3 (b) ("a number in [0, 1]"). It would also crystallize the need for iter-v3/004 (universe re-evaluation).

**Prediction 5 (model-level, P=70%): Headline metrics match iter-v3/002 EXACTLY.** The lgbm.py modification adds a side-effect (writing rows to a buffer) that does not alter model fitting or prediction. If headline metrics drift (e.g., IS Sharpe shifts to -0.0744 instead of -0.0746), it indicates the modification had subtle stateful side effects (e.g., RNG consumption) that need investigation. **Detection signal**: `comparison.csv` `monthly_sharpe` row matches iter-v3/002's `comparison.csv` to 4 decimal places.

If any of predictions 1–5 fails to materialize as predicted, the iter-v3/003 diary documents the calibration miss and updates the v3 skill's failure-mode taxonomy.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

### MERGE iff ALL of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | IS monthly Sharpe | > 1.0 | Project hard floor (memory) |
| 2 | OOS monthly Sharpe | > 1.0 | Project hard floor (memory) |
| 3 | OOS / IS Sharpe ratio | ≥ 0.5 | Project hard floor (memory) |
| 4 | OOS total trades | ≥ 130 | Trade-rate floor (memory) |
| 5 | Trades / month OOS | ≥ 10 | Trade-rate floor (memory) |
| 6 | Top-symbol OOS PnL share | ≤ 30% | Concentration cap (project default) |
| 7 | DSR | > 0.95 | v3 hard threshold |
| **8** | **PBO** | **A number in [0.0, 1.0] — NOT NaN. Threshold-version: < 0.40 for the strict-MERGE pathway; in (0.0, 1.0) for the methodology-MERGE pathway.** | **v3 hard threshold; tightened from iter-v3/002 (NaN no longer acceptable)** |
| 9 | PSR | > 0.95 | v3 hard threshold |
| 10 | Worst-symbol OOS wpnl | > -15% of total OOS wpnl | Concentration-floor tail check |
| 11 | OOS MaxDD | ≤ 30% | Project soft cap |
| 12 | All 4 symbols have ≥ 1 OOS trade | True | Universe activity check |
| 13 | adf_test.csv row count: per-symbol verification | `for each symbol s in V3_SYMBOLS, adf_test.csv.query('symbol == @s').shape[0] == n_features × n_retrain_months_s` | NEW — replaces iter-v3/002 ill-posed formula per Critic Recommendation #2 |
| 14 | IC < 0.7 between feature families | True | v3 hard threshold; degenerate this iteration (no new families) |
| 15 | 10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable | True (vacuity acceptable per memory rule for this methodology iteration) | Project hard floor (memory) |
| 16 | Critic OVERALL | = MERGE | v3 mandatory |
| 17 | sign(IS Sharpe) == sign(OOS Sharpe) | True | Sign-flip precondition (inherited from iter-v3/002) |
| 18 | Adversarial unit tests pass in CI (the 3 inherited + the 1 new) | True | Methodology-stack precondition |
| 19 | Brief-vs-code reconciliation table has no empty cells AND every row's verifier command exits 0 | True | NEW: file-artifact gate per Critic Recommendation #1 |
| **20** | **`reports-v3/iteration_v3-003/trial_oof_returns.parquet` exists with ≥ 40,000 rows and the 6 prescribed columns** | **True** | **NEW: the file-artifact gate that iter-v3/002 lacked** |
| **21** | **`dsr.json["pbo"]` is a finite float in [0.0, 1.0]** | **True** | **NEW: explicit PBO file-existence assertion** |
| **22** | **`dsr.json["n_eff"] > 4`** | **True** | **NEW: explicit n_eff non-surrogate assertion** |

### NO-MERGE iff ANY of:

- Any of the 22 criteria fails
- Engineer's Phase 6 wall-clock exceeds 24h
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits BLOCK

### Discretionary judgment — split-merge clause (tightened from iter-v3/002)

The Section 8 criteria may be partitioned:

- **Headline-metric criteria**: 1, 2, 3, 4, 5, 6, 10, 11, 17. Expected to fail by design (model unchanged from iter-v3/002).
- **Methodology-stack criteria**: 7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22. The iteration's actual goal.

**Methodology MERGE** requires:
- ALL methodology-stack criteria pass (criteria 7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22)
- Diary documents the split-merge explicitly with rationale
- Cherry-picked code: iter-v3/002 inheritance + iter-v3/003 lgbm.py / optimization.py / run_baseline_v3.py modifications + new test file

**Strict MERGE** (full headline metrics): not expected. Same model on same data; would require luck-of-the-draw model improvement which is structurally absent.

**Critical change vs iter-v3/002**: Criterion 8 strict reading is "PBO is a finite number in [0.0, 1.0], NOT NaN". The iter-v3/002 loophole "NaN with descriptive-stats fallback is acceptable" is REMOVED for iter-v3/003 because the iteration's central deliverable is precisely to make PBO non-NaN. Criteria 20, 21, 22 codify this with explicit file-artifact verifiers.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | Path-matrix arithmetic, PCA for n_eff_trials | n/a |
| `scipy` | (already installed) | BSD-3 | `scipy.stats.norm` for DSR/PSR Phi() | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for per-(sym, feat, month) ADF (unchanged from iter-v3/002) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | Adversarial unit tests (3 inherited + 1 new) | n/a |
| **`pyarrow` or `fastparquet`** | (already installed via pandas) | Apache-2 / BSD-3 | **NEW: `pd.DataFrame.to_parquet` for `trial_oof_returns.parquet`** | If `pyarrow` missing, fall back to `fastparquet`; if both fail, fall back to `df.to_csv` and rename file extension to `.csv` (the runner's reader uses `pd.read_parquet` which auto-detects engine — adapt accordingly) |

### Fallback rationale

iter-v3/003 inherits iter-v3/002's pure-Python implementations of CPCV/PBO/PSR/DSR/ADF. No NEW third-party dependencies. The only library-stack change is the parquet writer for the new `trial_oof_returns.parquet` artifact — pandas' built-in `to_parquet` uses `pyarrow` by default, which is already installed (verified via `git show iteration-v3/002:pyproject.toml | grep -E "pyarrow|fastparquet"` if needed; pandas 2.x installs pyarrow as default).

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-003/engineering_report.md` with:
- The git commit SHA at backtest time
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The `trial_oof_returns.parquet` row count, unique trial_id count, and per-(symbol, train_month) row distribution
- The `comparison.csv` numerical diff against iter-v3/002 (expected: identical to 4 decimal places on headline metrics; PBO and n_eff strictly different)
- The 4 adversarial unit-test files' commit SHAs and pytest exit codes (3 inherited + 1 new)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the new Phase 5.5 inputs (file-artifact reconciliation table per Critic Rec #1, per-sub-fix decomposition per Critic Rec #3, and the inheritance plan per §3.8):

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants unchanged; iter-v3/002 CPCV config inherited |
| 1 — Hypothesis | PASS — one sentence; specific testable target ("S=1 → S=50, NaN → number"); falsifier in §4.2 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-003/pbo_strategy_axis_demo.py` committed at SHA `9294855` BEFORE this brief; 3 outputs (`pbo_strategy_axis.csv`, `persistence_schema.csv`, `synthesis.md`) committed; results inline in §2.1; persistence schema in §2.2-2.4 |
| 3 — Proposed Changes | PASS — symbols UNCHANGED (with V3_EXCLUDED check); labeling UNCHANGED; features UNCHANGED; risk gates UNCHANGED; SINGLE methodology fix decomposed into 6 sub-rows in §3.5; brief-vs-code reconciliation table in §3.6 with file-artifact verifiers (per Critic Rec #1); inheritance plan in §3.8 |
| 4 — Expected OOS Impact | PASS — predicted metrics table with EXACT expected match on headline; 3-tier falsifier in §4.2; split-merge clause in §4.3 with PBO non-NaN as hard precondition |
| 5 — Risk Mitigation | PASS — 3 structural safeguards in §5.2 specifically targeting iter-v3/002's process failure mode |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/002; concentration acknowledged as expected fail |
| 7 — Pre-Registered Failure-Mode | PASS — 5 predictions including 3 process-level (Predictions 1, 2, 3) per iter-v3/002 lesson; specific per-source-file mention as iter-v3/002 lesson #4 mandated |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 22 criteria (19 inherited + 3 NEW: 20, 21, 22 for file-artifact gates); split-merge clause tightened (NaN PBO no longer acceptable) |
| 9 — Library Stack | PASS — no new deps; pyarrow/fastparquet fallback documented |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8 criterion 19.
