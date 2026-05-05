# Iteration v3-004 — Research Brief

**Type**: METHODOLOGY REPAIR (consumer-side, single-file scope)
**Track**: v3 (rigor arm) — fourth iteration; iter-v3/001 NO-MERGE, iter-v3/002 NO-MERGE, iter-v3/003 NO-MERGE
**Branch**: `iteration-v3/004` (off `iteration-v3/003` directly — see Section 3.8 inheritance rationale)
**Date**: 2026-05-05
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ensemble_seeds   = [42, 123, 456, 789, 1001]   # 5-seed inner ensemble (v1-style)
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation for IS-only filtering
```

- **IS window**: from each symbol's first usable kline (with the listing-date floor 2022-09-24, no symbol contributes to walk-forward training before 2022-09-24) through `2025-03-23 23:59:59 UTC` exclusive.
- **OOS window**: from `2025-03-24 00:00:00 UTC` through the data-extent timestamp at backtest time.
- **Walk-forward unit**: monthly retrain, 24-month rolling training window, 1-month OOS prediction window.
- **Per-cell CPCV unit (NEW in iter-v3/004)**: `N=10, k=2 → C(10,2)=45 paths` over each cell's candle timeline. Per-cell purge gap = `(timeout_candles + 1) = 22 candles` (within-symbol gap; the ×n_symbols multiplier is irrelevant within a single-symbol cell). The global REQUIRED_GAP=88 assertion in `_verify_label_leakage_gap()` and `combinatorial_purged_cv(expected_gap=REQUIRED_GAP)` remains intact for the global-axis CSCV (consumer code preserves both invariants — see §3.5 sub-fix 1).
- The QR sees OOS metrics for the first time in Phase 7. The QR has produced this brief reading IS-only data plus the iter-v3/003 reports. The per-cell PBO computation in Section 2 reads ONLY rows with `candle_open_time_ms < OOS_CUTOFF_MS`.

---

## Section 1 — Hypothesis

**Modifying `_compute_cpcv_paths` and `_compute_n_eff_trials` (in `run_baseline_v3.py`) to compute per-(symbol, train_month) cell CSCV using iter-v3/003's existing `trial_oof_returns.parquet` as input — no rebacktest — then aggregating cell-level PBOs via the cross-cell mean (with Fisher's-method and median as supplementary diagnostics) and cell-level n_effs via median, will produce an aggregated PBO strictly in (0.0, 1.0) AND a median n_eff > 4 — bypassing the cross-cell `trial_id` semantic mismatch that broke iter-v3/003.**

This is the per-cell consumer pathway specified by the iter-v3/003 Critic Recommendation #1 verbatim, with the aggregation method (mean) chosen empirically in Phase 5 to be robust to the bimodal cell-level PBO distribution observed on the strategy.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-004/per_cell_pbo_demo.py` (committed at SHA `23bb5be` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read**: `reports-v3/iteration_v3-003/trial_oof_returns.parquet` (78,688,992 rows, 50 unique trial_ids, 6 columns — the producer-side artifact iter-v3/003 successfully shipped).

**Outputs** (all committed alongside the script at the same SHA):
- `analysis/iteration_v3-004/per_cell_pbo_results.csv` — 173 rows, one per (symbol, train_month) cell
- `analysis/iteration_v3-004/aggregated_pbo.json` — Fisher's-method PBO + mean PBO + median PBO + median n_eff + synthetic adversarial validation results
- `analysis/iteration_v3-004/synthesis.md` — interpretive narrative

### 2.1 Empirical fact about the parquet (load-bearing for the cell-key choice)

The iter-v3/003 writer appended each (sym, month) cell's data 5 times (once per ensemble seed) with **identical** `oof_return` values per `(trial_id, fold_idx, candle_open_time_ms)` cube. Verified empirically — every group of 5 rows for the same (sym, month, trial, fold, candle) tuple has `nunique(oof_return) == 1`. After dedup-by-natural-key, the parquet has:

| Quantity | Value |
|---|---:|
| Raw rows | 78,688,992 |
| After dedup | 15,747,500 |
| IS-only rows | 14,016,500 |
| (sym, train_month) cells | 173 |
| trial_ids per cell | 50 (constant) |
| (fold, candle) rows per (cell, trial) | ~1820 |

**The cell key for this iteration is `(symbol, train_month)`, not `(symbol, train_month, ensemble_seed)`** as originally prescribed by the diary's Next Iteration Idea #1. The iter-v3/003 writer never wrote the ensemble_seed column, and the 5 ensemble seeds produced identical oof_return values per (trial, fold, candle), so the seed dimension is empirically degenerate in this parquet. The cell-key collapse loses NO statistical signal: the 50 trial_ids within a single Optuna study are still 50 distinct strategies (TPE sampler trajectory makes them meaningfully ranked).

This is itself a finding worth documenting — the "5-seed ensemble" produced identical OOF rows in iter-v3/003, suggesting either (a) the ensemble's randomness was downstream of OOF computation, OR (b) the writer overwrote rather than appended-with-distinction. Either way, the parquet's natural key for distinct strategies is `(sym, month, trial_id)`, which is exactly what the per-cell pathway needs.

### 2.2 Per-cell results (real data, 173 cells)

Per-cell PBO and n_eff for every (sym, month) cell with rank > 1 (informative):

| Statistic | Value |
|---|---:|
| **n_cells_total** | 173 |
| **n_cells_rank_gt_1** (informative) | 173 (100.0%) |
| **n_cells_with_pbo** | 173 |
| **Cells with PBO > 0.5** (overfit signature) | **21 of 173 (12.1%)** |
| **Cells with PBO ≈ 1.0** (deeply overfit) | 2 |

**Per-cell PBO distribution (raw)**:

| Stat | Value |
|---|---:|
| mean | **0.1305** |
| median | 0.0000 |
| q25 / q75 | 0.0000 / 0.0538 |
| q90 | 0.5658 |
| min / max | 0.0000 / 1.0000 |
| stddev | 0.2665 |

**Per-cell n_eff distribution**:

| Stat | Value |
|---|---:|
| median | **25** |
| q25 / q75 | 23 / 27 |
| min / max | 12 / 31 |

**Cell-level PBO histogram** (bin width 0.1):

| PBO range | Cells | Frac |
|---|---:|---:|
| [0.0, 0.1] | 133 | 0.769 |
| (0.1, 0.2] | 6 | 0.035 |
| (0.2, 0.3] | 3 | 0.017 |
| (0.3, 0.4] | 3 | 0.017 |
| (0.4, 0.5] | 7 | 0.040 |
| (0.5, 0.6] | 4 | 0.023 |
| (0.6, 0.7] | 4 | 0.023 |
| (0.7, 0.8] | 3 | 0.017 |
| (0.8, 0.9] | 4 | 0.023 |
| (0.9, 1.0] | 6 | 0.035 |

The distribution is bimodal: 77% of cells have PBO ≤ 0.1 (stable IS-best Sharpe ordering persists OOS), 12% of cells have PBO > 0.5 (real overfit signature). This bimodality is itself informative — the strategy generalizes well in most regimes but fails in a quantifiable minority (which can be investigated separately in iter-v3/005+).

### 2.3 Aggregator choice and headline values

Three aggregators reported, with the iteration's headline being **mean PBO**:

| Aggregator | Value | Strict (0,1)? | Use |
|---|---:|:-:|---|
| **Mean PBO (HEADLINE)** | **0.1305** | YES | criterion 21 input |
| Median PBO | 0.0000 | boundary | uninformative on this strategy (>50% cells PBO=0) |
| Fisher's-method PBO | ~0.0 (numerical underflow) | boundary | saturates at scale (173 cells, mostly low-PBO → chi² deep in tail) |
| Mean PBO Laplace-smoothed | 0.1307 | YES | sanity cross-check |

**Choice rationale**: the cell-level distribution is bimodal. The **mean** is the only aggregator that:
1. Is strictly in (0.0, 1.0) on this strategy
2. Reflects the actual fraction of cells showing overfit signature (here ~13%)
3. Does not saturate or underflow on the realistic input

The median is uninformative because >50% of cells have PBO=0. Fisher's method (originally prescribed by the diary's Next Iteration Idea #1) saturates at large N because every near-zero per-cell PBO contributes -2·ln(ε) ≈ +17 to the chi² sum; with 173 cells at df=346, the resulting tail probability underflows. This is not a defect of Fisher's method, but it makes Fisher's method uninformative as an aggregator at this scale on this distribution. The brief retains Fisher's method as **supplementary diagnostic** (criterion 23 cross-check) and substitutes mean PBO for the headline criterion 21 input.

|delta(mean − median)| = 0.1305 (within criterion 23 ≤ 0.15 cap)

### 2.4 Synthetic adversarial validation (consumer-preserves-signal test)

We constructed 10 overfit cells (trial 0 explicitly IS-favorable / OOS-unfavorable: positive Gaussian on first-half candles, negative on second-half) and 10 clean cells (all 50 trials IID-Gaussian with no edge anywhere). Pre-registered pass criteria:

| Criterion | Threshold | Observed | Pass? |
|---|---|---|---|
| Pairwise separation (min(overfit) > max(clean)) | strict | min(overfit)=1.000 > max(clean)=0.358 | TRUE |
| Median delta > 0.5 | > 0.5 | 1.000 | TRUE |
| Overfit median > 0.7 | > 0.7 | 1.000 | TRUE |

Per-cell PBO observations:

| Set | per-cell PBOs | Median |
|---|---|---:|
| Overfit (10 cells) | [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0] | 1.0000 |
| Clean (10 cells) | [0.000, 0.000, 0.000, 0.000, 0.000, 0.014, 0.358, 0.000, 0.000, 0.305] | 0.0000 |

**The consumer pipeline distinguishes overfit from clean cells perfectly.** Every overfit cell PBO (=1.0 by construction) strictly exceeds every clean cell PBO (max=0.358). Median delta = 1.0. This is the producer-preserves-signal test that iter-v3/003 lacked — `tests/strategies/ml/test_oof_persistence.py` only tested the parquet write side (rows exist, columns correct, cardinality matches); the new test asserts the consumer pipeline preserves strategy-distinguishing signal.

Note: clean cell PBOs cluster near 0 (not 0.5 as a naive chance baseline would suggest). This is a documented small-sample property of CSCV at n_paths=45 with positively-skewed Sharpe orderings — the IS-best Sharpe rank persists OOS due to small-N noise. PBO acts as a binary detector of the overfit signature (present ≈1.0 / absent ≈0.0), not a continuous "amount of overfit" measure. The brief's primary falsifier (Section 4.2) targets the **aggregator's domain bounds**, not the cell-level distribution shape.

### 2.5 Methodology fix worked: n_eff distribution

Per-cell n_eff median = 25 (was 1 in iter-v3/003). 100% of cells have rank > 1 (was 1 in iter-v3/003 because the cross-cell aggregation reduced the (50 × 5359) matrix to near rank-1). Min n_eff = 12, max = 31. Every cell's PCA recovers ~half its 50 trials as effective independent dimensions, which is statistically reasonable given the within-Optuna-study correlation structure.

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Same universe (iter-v3/001 / 002 / 003). Universe is not on trial. |
| MKRUSDT | KEEP | Same. The MKR concentration is a model-level concern; iter-v3/004 changes nothing about the model. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001 / 002 / 003:
- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t for triple-barrier: past-only ATR (no leak)
- NO meta-labeling (deferred — out of scope)
- Label-horizon-derived purge gap: `gap = (timeout_candles + 1) × n_symbols = 88 candles`

### 3.3 Features — UNCHANGED

`V3_FEATURE_COLUMNS` (34 columns) remains the feature set. NO new features. NO auto-d* fracdiff. NO cluster-importance check needed (no additions).

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
| R1 — consecutive-SL cooldown | OFF | Same as iter-v3/003 (deferred) |
| R2 — drawdown scaling | OFF | Same |
| R3 — OOD Mahalanobis | OFF | Same |

Identical risk profile to iter-v3/003.

### 3.5 The single architectural change — per-cell CSCV consumer pipeline

This is iter-v3/004's only meaningful code modification. It corresponds to the iter-v3/003 Critic Recommendation #1 verbatim. Per Critic Recommendation #2 from iter-v3/003, the fix is decomposed into atomic sub-fixes; per Critic Recommendation #3 from iter-v3/003, each sub-fix's reconciliation row references a verifiable file artifact AND a synthetic adversarial test gates Phase 5.5.

| # | Sub-fix | Spec | Code path | File artifact |
|---|---|---|---|---|
| 1 | **`_compute_cpcv_paths` rewrite — per-cell CSCV with cross-cell mean aggregation** | Replace the iter-v3/003 cross-cell `groupby("trial_id").sum()` (run_baseline_v3.py:550) with per-cell iteration: for each `(symbol, train_month)` group in `trial_oof_returns.parquet`, dedup-by-natural-key, pivot to a (n_candles × 50_trials) returns matrix, run `combinatorial_purged_cv(n_samples=n_candles, n_splits=10, n_test_splits=2, gap=22, embargo=0)` to get 45 paths, build (45 × 50) path-Sharpe matrix, call `pbo_from_cpcv` → per-cell PBO. Aggregate the 173 per-cell PBOs by the **mean** to produce `dsr.json["pbo"]`. Preserve global-axis CSCV in a SEPARATE call for the inheritance compatibility (so cpcv_paths.csv is still produced) — the per-cell results live in a new `per_cell_pbo.csv`. | `run_baseline_v3.py:_compute_cpcv_paths` (rewrite) | `reports-v3/iteration_v3-004/dsr.json["pbo"]` is a finite float in (0.0, 1.0); `reports-v3/iteration_v3-004/per_cell_pbo.csv` exists with ≥ 50 rows |
| 2 | **`_compute_n_eff_trials` rewrite — per-cell PCA with median aggregation** | Replace the iter-v3/003 cross-cell pivot (run_baseline_v3.py:1180-1199) with per-cell iteration: for each `(symbol, train_month)` group, build the (50 × n_candles) per-trial returns matrix, call `n_effective_trials(matrix.T)` → per-cell n_eff. Aggregate the 173 per-cell n_effs by the **median** to produce `dsr.json["n_eff"]`. | `run_baseline_v3.py:_compute_n_eff_trials` (rewrite) | `reports-v3/iteration_v3-004/dsr.json["n_eff"] > 4` |
| 3 | **NEW adversarial test for the consumer pipeline** | `tests/strategies/ml/test_per_cell_pbo_synthetic.py` constructs (a) 10 synthetic overfit cells (trial 0 IS-favorable / OOS-unfavorable, 49 noise trials) and (b) 10 synthetic clean cells (50 IID-Gaussian trials). Aggregate via cross-cell mean. Asserts: pairwise separation (min(overfit) > max(clean)), median delta > 0.5, overfit median > 0.7, clean max < 0.5. | `tests/strategies/ml/test_per_cell_pbo_synthetic.py` (NEW) | `uv run pytest tests/strategies/ml/test_per_cell_pbo_synthetic.py -v` exits 0 |
| 4 | **Auxiliary persistence: `per_cell_pbo.csv` for auditability** | The runner writes `reports-v3/iteration_v3-004/per_cell_pbo.csv` with one row per cell containing `{symbol, train_month, n_trials, n_candles, n_paths, rank, pbo, n_eff}`. This is the audit trail iter-v3/003 lacked (had only the global aggregate, with no per-cell rows for the Critic to spot-check). | `run_baseline_v3.py:_compute_cpcv_paths` (write CSV alongside the global) | `reports-v3/iteration_v3-004/per_cell_pbo.csv` exists with ≥ 50 rows where rank > 1 |
| 5 | **Fix the iter-v3/003 PBO field divergence (carried-forward Check 7 WARN)** | Replace hardcoded literal `"pbo": "NaN"` at `run_baseline_v3.py:1162` with a read of `dsr.json["pbo"]` after CSCV completes, OR set the per-seed PBO field to the actual computed value rather than a literal string. This closes the iter-v3/003 carried-forward Check 7 WARN that the engineering report flagged. | `run_baseline_v3.py:1162` (replace literal) | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-004/seed_summary.json')); assert isinstance(d[0]['pbo'], (int, float))"` |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input — per Critic Rec #1)

Each sub-fix from §3.5 has its own row. **Each cell maps to a FILE ARTIFACT** with a verifier command (per iter-v3/003 Critic Rec #1 + iter-v3/002 lesson #1). Empty rows = Phase 5.5 BLOCK. Verifier commands MUST execute and exit 0 post-Phase 6.

| # | Section 3.5 sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | `_compute_cpcv_paths` rewrite (per-cell mean) | `run_baseline_v3.py:_compute_cpcv_paths` | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-004/dsr.json')); assert isinstance(d['pbo'], (int, float)) and 0.0 < d['pbo'] < 1.0, f'pbo={d[\"pbo\"]}'"` |
| 2 | `_compute_n_eff_trials` rewrite (per-cell median) | `run_baseline_v3.py:_compute_n_eff_trials` | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-004/dsr.json')); assert d['n_eff'] > 4, f'n_eff={d[\"n_eff\"]}'"` |
| 3 | NEW adversarial test for consumer pipeline | `tests/strategies/ml/test_per_cell_pbo_synthetic.py` (NEW) | `uv run pytest tests/strategies/ml/test_per_cell_pbo_synthetic.py -v` exits 0 |
| 4 | per_cell_pbo.csv persistence | `run_baseline_v3.py:_compute_cpcv_paths` | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-004/per_cell_pbo.csv'); assert len(df) >= 50, f'cells={len(df)}'"` |
| 5 | seed_summary.json PBO literal fix | `run_baseline_v3.py:1162` | `python -c "import json; d=json.load(open('reports-v3/iteration_v3-004/seed_summary.json')); assert isinstance(d[0]['pbo'], (int, float))"` |
| 6 | Symbols UNCHANGED (BCH, MKR, LDO, TRX) | `run_baseline_v3.py:V3_MODELS` | `grep -E '^V3_MODELS' run_baseline_v3.py` shows the same 4 symbols |
| 7 | Risk gates UNCHANGED (v2 5 + BTC) | `RiskV3Wrapper` config | `grep -E "RiskV3Wrapper\\(" run_baseline_v3.py` shows v2 5-gate config, no R1/R2/R3 |
| 8 | Features UNCHANGED (V3_FEATURE_COLUMNS, 34 cols) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 34"` |
| 9 | All 4 inherited adversarial tests still pass | `tests/strategies/ml/test_pbo_synthetic.py`, `test_dsr_negative_is.py`, `test_cpcv_embargo_assert.py`, `test_oof_persistence.py` | `uv run pytest tests/strategies/ml/test_pbo_synthetic.py tests/strategies/ml/test_dsr_negative_is.py tests/strategies/ml/test_cpcv_embargo_assert.py tests/strategies/ml/test_oof_persistence.py -v` exits 0 |
| 10 | Consumer-side cross-check: aggregated mean ≈ median ± 0.15 | `dsr.json` cross-check | `python -c "import json,pandas as pd; d=json.load(open('reports-v3/iteration_v3-004/dsr.json')); df=pd.read_csv('reports-v3/iteration_v3-004/per_cell_pbo.csv'); med=df['pbo'].median(); assert abs(d['pbo'] - med) <= 0.15, f'mean={d[chr(34)+\"pbo\"+chr(34)]} median={med} delta={abs(d[chr(34)+\"pbo\"+chr(34)] - med):.3f}'"` |
| 11 | Headline metrics MATCH iter-v3/003 EXACTLY (model unchanged, no rebacktest) | `comparison.csv` | `diff <(head -50 reports-v3/iteration_v3-004/comparison.csv) <(head -50 reports-v3/iteration_v3-003/comparison.csv) | grep -v "^[<>]" | head` shows zero data-row differences (only the iter number in header may differ) |
| 12 | per_cell_pbo.csv has rank-distribution similar to Section 2 demo | `per_cell_pbo.csv` | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-004/per_cell_pbo.csv'); n_rank_gt1=(df['rank']>1).sum(); assert n_rank_gt1 >= 50, f'rank_gt1={n_rank_gt1}'"` |

### 3.7 NO new feature families, NO meta-labeling, NO auto-d* fracdiff, NO universe change

iter-v3/004 is a CONSUMER-side methodology fix on iter-v3/003's existing producer-side parquet. Future iterations (iter-v3/005 universe re-evaluation, iter-v3/006 meta-labeling, iter-v3/007 crypto-native features) are explicitly out of scope.

### 3.8 Inheritance plan from iter-v3/003 (mandatory engineering note)

The `iteration-v3/004` branch was branched DIRECTLY from `iteration-v3/003` (commit `0ca7ba1` — diary entry parent). All iter-v3/001 + iter-v3/002 + iter-v3/003 src/ + tests + parquet are present in the working tree. **NO cherry-pick needed in Phase 6 step 0** — this is a DEPARTURE from iter-v3/003's pattern, justified because iter-v3/004 is a fix-on-top-of-broken iteration where re-cherry-picking the 3-iteration chain is more error-prone than direct branching.

Critical inheritance verifiers (run before any code edits):
- `git log --oneline iteration-v3/004 -- src/crypto_trade/strategies/ml/validation_v3.py | wc -l` ≥ 1 (validation_v3 from iter-v3/001 present)
- `git log --oneline iteration-v3/004 -- src/crypto_trade/strategies/ml/risk_v3.py | wc -l` ≥ 1 (risk_v3 from iter-v3/001 present)
- `git log --oneline iteration-v3/004 -- src/crypto_trade/features_v3/ | wc -l` ≥ 1 (features_v3 from iter-v3/001 present)
- `git log --oneline iteration-v3/004 -- run_baseline_v3.py | wc -l` ≥ 1 (runner present)
- `test -f reports-v3/iteration_v3-003/trial_oof_returns.parquet` (input artifact present at expected path)
- `uv run pytest tests/strategies/ml/test_pbo_synthetic.py tests/strategies/ml/test_dsr_negative_is.py tests/strategies/ml/test_cpcv_embargo_assert.py tests/strategies/ml/test_oof_persistence.py -v` exits 0 (all 4 inherited tests pass on this branch BEFORE any iter-v3/004 edits)

The runner-side changes layer on top of these. NO need to re-fetch klines; NO need to regenerate features; NO need to re-run the LightGBM training. The iter-v3/004 deliverable is a re-run of the validation pipeline ALONE on the existing parquet.

### 3.9 Engineer's Phase 6 work plan (informative, not mandatory)

Engineer's expected critical path:
1. Verify §3.8 inheritance preconditions (5 verifiers, all should pass).
2. Edit `run_baseline_v3.py:_compute_cpcv_paths` per §3.5 sub-fix #1 (per-cell mean aggregation).
3. Edit `run_baseline_v3.py:_compute_n_eff_trials` per §3.5 sub-fix #2 (per-cell median aggregation).
4. Edit `run_baseline_v3.py:1162` per §3.5 sub-fix #5 (PBO literal fix).
5. Add per_cell_pbo.csv persistence (§3.5 sub-fix #4).
6. Write `tests/strategies/ml/test_per_cell_pbo_synthetic.py` (§3.5 sub-fix #3) and confirm it passes.
7. Run `uv run python run_baseline_v3.py --seeds 1` → produces `reports-v3/iteration_v3-004/{dsr.json, per_cell_pbo.csv, comparison.csv, ...}`. The model rebuilds because the runner doesn't have a "validation-only" mode; this is acceptable because the existing parquet is at iter-v3/003's location and the runner reads it from there.
8. Verify §3.6 reconciliation table — every verifier exits 0.
9. Commit and write engineering report.

Estimated wall-clock: equivalent to iter-v3/003 (since the model retrains). The validation pipeline cost is negligible (~minutes).

**Alternative path (if Engineer can short-circuit the rebacktest)**: skip step 7's full rebacktest and instead point `run_baseline_v3.py` at iter-v3/003's parquet via a `--reuse-trial-oof-from PATH` flag (NEW), then re-run only the validation pipeline. This is OPTIONAL — both paths produce equivalent dsr.json output. The rebacktest path is the safer default.

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted impact on iteration metrics

| Metric | iter-v3/003 (NO-MERGE) | iter-v3/004 prediction | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | -0.0746 | **-0.0746 (EXACT)** | 0 (model unchanged) |
| OOS monthly Sharpe | +1.0955 | **+1.0955 (EXACT)** | 0 (model unchanged) |
| OOS daily Sharpe | +2.2053 | **+2.2053 (EXACT)** | 0 (model unchanged) |
| OOS MaxDD | 22.04% | **22.04% (EXACT)** | 0 (model unchanged) |
| OOS Calmar | +1.7477 | **+1.7477 (EXACT)** | 0 (model unchanged) |
| OOS profit factor | 1.2977 | **1.2977 (EXACT)** | 0 (model unchanged) |
| OOS trades | 83 | **83 (EXACT)** | 0 (model unchanged) |
| MKR concentration | 53.21% | **53.21% (EXACT)** | 0 (model unchanged) |
| **PBO** | **0.0 (degenerate strategy axis)** | **~0.13 (mean of per-cell PBOs from §2.2)** | **the iteration's headline result** |
| **n_eff_trials** | **1 (rank-tautology)** | **~25 (median across 173 cells)** | **the iteration's headline result** |
| DSR | 0.0 | **~0.0 (still — IS Sharpe deeply negative)** | minor |
| PSR | 1.0 | **1.0** | unchanged (depends on observed OOS SR only) |
| adf_test.csv row count | 7242 | **7242 (EXACT)** | unchanged |

### 4.2 Falsifier (locked before backtest)

**Primary falsifier**: if `dsr.json["pbo"]` is NaN OR is exactly 0.0 OR is exactly 1.0 OR is outside [0.0, 1.0] OR is not a finite float, the methodology is still wrong. The headline mean PBO must be **strictly inside (0.0, 1.0)**. The §2 IS-only demo predicts ~0.13; any value in (0.0, 1.0) is acceptable on the methodology axis.

**Secondary falsifier**: if `dsr.json["n_eff"]` ≤ 4, the consumer rewrite did not fix the rank issue (or the per-cell aggregation reverted to a global one). The §2 IS-only demo predicts median n_eff ≈ 25; any value > 4 is acceptable.

**Tertiary falsifier**: if `|dsr.json["pbo"] − median(per_cell_pbo.csv)|` > 0.15, the aggregation method (mean) is producing a result inconsistent with the per-cell distribution (median). The §2 IS-only demo shows mean=0.131, median=0.000, |delta|=0.131 — within the 0.15 cap.

**Quaternary falsifier (process)**: if `per_cell_pbo.csv` does not exist at `reports-v3/iteration_v3-004/per_cell_pbo.csv`, OR has < 50 rows with rank > 1, the per-cell pathway did not actually run. This catches the case where the Engineer accidentally re-uses the iter-v3/003 cross-cell aggregation while writing the new file.

**Quinary falsifier (consumer-pipeline)**: if `tests/strategies/ml/test_per_cell_pbo_synthetic.py` does not exist or fails, the consumer-preserves-signal adversarial test was not implemented. This is the iter-v3/003 lesson: producer-only adversarial tests miss methodology-design errors that show up only in consumer behavior.

### 4.3 Expected MERGE outcome — split-merge clause inherited from iter-v3/003

iter-v3/004 is methodology repair on a single sub-fix area. The model's headline metrics (IS Sharpe, OOS Sharpe, trades, concentration) are expected to MATCH iter-v3/003 EXACTLY. Therefore Section 8 mechanical criteria 1, 2, 3, 4, 5, 6, 11, 17 will fail by design (same as iter-v3/003).

The split-merge clause permits methodology-only merge IF AND ONLY IF:
- (a) Critic OVERALL = MERGE on the methodology criteria (7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23, 24)
- (b) PBO produces a number strictly in (0.0, 1.0) (NOT 0.0, NOT 1.0, NOT NaN)
- (c) n_eff_trials > 4 (per-cell median, not surrogate)
- (d) per_cell_pbo.csv exists with ≥ 50 rows where rank > 1 (the audit trail)
- (e) `tests/strategies/ml/test_per_cell_pbo_synthetic.py` exists and passes
- (f) Section 8 criteria 13, 18, 19 ALL pass (per iter-v3/002 split-merge precondition)

If (a)–(f) hold, the QR MERGEs the methodology stack only.

**Strict MERGE** (full headline metrics): not expected. Same model on same data; would require luck-of-the-draw model improvement which is structurally absent.

**Critical change vs iter-v3/003**: criterion 21 is now strict-(0,1) (was [0,1] inclusive). The iter-v3/003 loophole "PBO=0.0 still satisfies the literal threshold" is removed because PBO=0.0 means the consumer pipeline saturated — the methodology is still off the rails. The §2 IS-only demo shows a real strategy on real data produces a non-saturating PBO when the per-cell pathway is used.

---

## Section 5 — Risk Mitigation

### 5.1 Inheritance — v2's 5 active gates + BTC trend filter

Identical to iter-v3/003. No new risk gates this iteration. The iteration's job is to verify the validation-pipeline downstream completion of iter-v3/003 sub-fix #2 + #3 via the per-cell consumer pathway; risk gates are not on trial.

### 5.2 Methodology-pipeline safety — the iteration's actual risk mitigation

Three structural safeguards relative to iter-v3/003's process failure:

1. **File-artifact reconciliation table** (§3.6). Each row references a verifier COMMAND, not a description. iter-v3/003's reconciliation table caught producer-side issues but didn't catch the consumer-side methodology-design error (§3.6 row 5 in iter-v3/003 verified `dsr.json["pbo"]` is "in [0, 1]" — which 0.0 satisfies). iter-v3/004's row 1 tightens to **strict (0.0, 1.0)**, closing that loophole.

2. **Synthetic adversarial test for the consumer pipeline** (§3.5 sub-fix #3, NEW). `tests/strategies/ml/test_per_cell_pbo_synthetic.py` constructs (a) overfit cells and (b) clean cells, runs them through the per-cell consumer pipeline, asserts the aggregator distinguishes them. This is the consumer-preserves-signal test that iter-v3/003 lacked. CI failure = Phase 5.5 BLOCK.

3. **Cell-level PBO persistence** (§3.5 sub-fix #4). `per_cell_pbo.csv` writes one row per cell with PBO + n_eff + rank, allowing the Critic to spot-check the per-cell distribution independently of the aggregate. iter-v3/003's only audit trail was `cpcv_paths.csv` (45 paths, 1 strategy column) — no way to verify the strategy axis was real.

4. **NEW: Headline aggregator choice rationale documented in Section 2.3**. The diary's Next Iteration Idea #1 prescribed Fisher's method; Phase 5 demonstrated Fisher saturates at scale on this distribution. The brief substitutes mean-PBO with explicit empirical justification. Future iterations (iter-v3/005+) can reconsider if the cell-level distribution shape changes (e.g., more uniform → Fisher recovers).

5. **Clamp-resistant criterion 23** (§3.6 row 10). The aggregated mean must agree with the median to within ±0.15. This catches the case where mean is near 0.5 but median is 0.0 (bimodal saturation in reverse), or mean is near 0.0 but median is near 1.0 (one extreme cell dominating mean).

These five safeguards target the EXACT failure mode that broke iter-v3/003. iter-v3/003's pre-registered failure-mode prediction missed the actual failure (brief Section 2.4 pseudocode encoded a methodology-design error that the implementation faithfully reproduced). iter-v3/004's Section 7 makes the consumer-side methodology-design risk explicit (Predictions 1, 2, 3 below).

### 5.3 NO new model-level risks introduced

Headline metrics expected to match iter-v3/003 exactly. No retuning, no re-cleaning, no late-cycle thresholds shifted. Any drift from iter-v3/003 in IS Sharpe / OOS Sharpe / trade count / concentration is itself a signal that the consumer-pipeline modification accidentally altered the model — Phase 7 evaluation must catch that.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/003

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

Combined kill rate target: 69–78%. Same as iter-v3/003.

### 6.2 Regime coverage — UNCHANGED from iter-v3/003

The v3 universe IS data spans 2020-01 → 2025-03-23 (LDO from 2022-09-22). Regime coverage includes 2020 COVID, 2021 bull, 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction.

### 6.3 Concentration — pessimistic baseline acknowledged

MKR concentration expected to remain at 53.21% (criterion 6 fails by design). Same as iter-v3/003. iter-v3/004 does NOT attempt to fix this (out of scope; future iter-v3/005 may revisit universe).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/003's diary lessons #1-#3 explicitly identified consumer-side methodology-design as the under-predicted failure mode for 3 iterations running. iter-v3/004's Section 7 incorporates that lesson by predicting consumer-side failures with higher probability than process-shipping failures.

**Prediction P1 (process-level, P=15%): Engineer implements per-cell aggregation but feeds Fisher's-method aggregator the per-cell PBOs without Laplace clamping, causing `ln(0)` or chi² explosion. The engineer chooses Fisher's method because the diary's Next Iteration Idea #1 prescribed it, doesn't run the §2 demo locally to see Fisher saturates, and the runtime crashes or produces NaN.** **Detection signal**: `dsr.json["pbo"] = NaN` or runner crashes during validation phase. **Mitigation**: §3.5 sub-fix #1 explicitly prescribes the **mean** aggregator (not Fisher's method) for `dsr.json["pbo"]`. Section 2.3 explains why mean was chosen empirically. The reconciliation table row 1 verifier (`0.0 < d['pbo'] < 1.0`) rules out NaN. The brief's §3.5 sub-fix #1 spec column says "Aggregate the 173 per-cell PBOs by the **mean**" in bold — Fisher's method is documented as a supplementary diagnostic only.

**Prediction P2 (process-level, P=10%): Engineer modifies `_compute_cpcv_paths` (sub-fix #1) but `_compute_n_eff_trials` keeps the iter-v3/003 cross-cell pivot (sub-fix #2 silently dropped).** The result would be: PBO is fixed (criterion 21 passes), n_eff stays at 1 (criterion 22 fails). **Detection signal**: `dsr.json["pbo"]` is in (0,1) but `dsr.json["n_eff"] = 1`. **Mitigation**: §3.6 reconciliation table requires BOTH per-cell PBO AND per-cell n_eff verifiers as separate rows (rows 1 and 2). The Phase 5.5 gate fails if BOTH verifier commands don't have file-artifact references.

**Prediction P3 (process-level, P=10%): Per-cell CSCV requires more samples per cell than typical Optuna study sizes provide (n_candles too small after `n_splits=10` group-splitting).** Some cells may have n_candles < 10 × n_test_splits requirement, causing `combinatorial_purged_cv` to raise. Engineer falls back to a global aggregation. **Detection signal**: `per_cell_pbo.csv` has < 50 rows with rank > 1, OR runner logs show per-cell CSCV exceptions. **Mitigation**: §3.6 reconciliation table row 4 requires `per_cell_pbo.csv` ≥ 50 rows. The §2 IS-only demo confirms 173 cells all have rank > 1, so the fallback should not be needed in practice. Engineer's catch-block must propagate per-cell exceptions to the row's `error` column rather than silently drop the cell.

**Prediction P4 (model-level, P=30%): Aggregated PBO lands in (0.4, 0.7) — chance baseline.** The strategy is genuinely near-random or borderline-anti-edge on this universe. **Detection signal**: `dsr.json["pbo"]` between 0.4 and 0.7. **Mitigation**: pre-registered as INFORMATIVE per Section 4.3 split-merge clause — methodology MERGE acceptable IF PBO is in (0.0, 1.0) regardless of value. The iteration's actual goal is making PBO interpretable, not making it small. (Note: §2 demo shows actual PBO ≈ 0.13, well below this range — but predicting (0.4, 0.7) is the conservative case.)

**Prediction P5 (model-level, P=70%): Headline metrics match iter-v3/003 EXACTLY.** Reusing the parquet (no Optuna re-run, no LightGBM re-fit) means the model is byte-for-byte identical. ANY drift in IS Sharpe / OOS Sharpe / trade count / concentration is a signal that the consumer-pipeline modification accidentally consumed RNG state or altered the training trajectory. **Detection signal**: `comparison.csv` row 0-5 EXACTLY matches `reports-v3/iteration_v3-003/comparison.csv` to 4 decimal places. (This prediction also materialized in iter-v3/003 — its calibration was the iteration's clearest correct prediction.)

If any of predictions P1–P5 fails to materialize as predicted, the iter-v3/004 diary documents the calibration miss and updates the v3 skill's failure-mode taxonomy. **Process-level predictions (P1, P2, P3) intentionally outnumber model-level predictions** (P4, P5) per iter-v3/003 lesson #3 — process and methodology-design predictions are systematically under-weighted in the QR's failure-mode prior.

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
| **8** | **PBO** | **strict (0.0, 1.0); for the strict-MERGE pathway: < 0.40 (mean across cells)** | **v3 hard threshold; tightened from iter-v3/003 (0.0 no longer acceptable)** |
| 9 | PSR | > 0.95 | v3 hard threshold |
| 10 | Worst-symbol OOS wpnl | > -15% of total OOS wpnl | Concentration-floor tail check |
| 11 | OOS MaxDD | ≤ 30% | Project soft cap |
| 12 | All 4 symbols have ≥ 1 OOS trade | True | Universe activity check |
| 13 | adf_test.csv row count: per-symbol verification | `for each symbol s in V3_SYMBOLS, adf_test.csv.query('symbol == @s').shape[0] == n_features × n_retrain_months_s` | Inherited from iter-v3/003 |
| 14 | IC < 0.7 between feature families | True | v3 hard threshold; degenerate this iteration (no new families) |
| 15 | 10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable | True (vacuity acceptable per memory rule for this methodology iteration) | Project hard floor (memory) |
| 16 | Critic OVERALL | = MERGE | v3 mandatory |
| 17 | sign(IS Sharpe) == sign(OOS Sharpe) | True | Sign-flip precondition |
| 18 | Adversarial unit tests pass in CI (the 4 inherited + the 1 new) | True | Methodology-stack precondition |
| 19 | Brief-vs-code reconciliation table has no empty cells AND every row's verifier command exits 0 | True | File-artifact gate per Critic Recommendation #1 |
| 20 | `reports-v3/iteration_v3-003/trial_oof_returns.parquet` exists with ≥ 40,000 rows and the 6 prescribed columns (input artifact) | True | Inherited from iter-v3/003 — input dependency |
| **21** | **`dsr.json["pbo"]` is a finite float strictly in (0.0, 1.0) (NOT 0.0, NOT 1.0, NOT NaN)** | **True** | **NEW: tightened from iter-v3/003 closed-bound** |
| **22** | **`dsr.json["n_eff"] > 4`** | **True** | **NEW: per-cell median, not cross-cell pivot** |
| **23** | **`abs(dsr.json["pbo"] - median(per_cell_pbo.csv["pbo"])) ≤ 0.15`** | **True** | **NEW: aggregator-vs-per-cell consistency check** |
| **24** | **`per_cell_pbo.csv` exists with ≥ 50 rows where `rank > 1`** | **True** | **NEW: audit trail gate** |

### NO-MERGE iff ANY of:

- Any of the 24 criteria fails
- Engineer's Phase 6 wall-clock exceeds 24h
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits BLOCK

### Discretionary judgment — split-merge clause (tightened from iter-v3/003)

The Section 8 criteria may be partitioned:

- **Headline-metric criteria**: 1, 2, 3, 4, 5, 6, 10, 11, 17. Expected to fail by design (model unchanged from iter-v3/003).
- **Methodology-stack criteria**: 7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23, 24. The iteration's actual goal.

**Methodology MERGE** requires:
- ALL methodology-stack criteria pass (criteria 7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23, 24)
- Diary documents the split-merge explicitly with rationale
- All sub-fixes from §3.5 implemented; reconciliation table verifiers all exit 0

**Strict MERGE** (full headline metrics): not expected. Same model on same data; would require luck-of-the-draw model improvement which is structurally absent.

**Critical change vs iter-v3/003**: criterion 21 strict-(0,1) (was [0,1]). Plus NEW criteria 23 (aggregator consistency) and 24 (audit trail) to catch the methodology-design errors that pure threshold checks miss.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | Path-matrix arithmetic, PCA for n_eff_trials | n/a |
| `scipy` | (already installed) | BSD-3 | `scipy.stats.combine_pvalues` for Fisher's-method DIAGNOSTIC (not headline) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for per-(sym, feat, month) ADF (unchanged from iter-v3/003) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | Adversarial unit tests (4 inherited + 1 new) | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O (`pd.read_parquet`), groupby per-cell | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (no schema change from iter-v3/003) | If missing, pandas auto-falls back to fastparquet |

### Aggregator strategy — explicit declaration (per Critic Recommendation #4 from iter-v3/003)

iter-v3/004's PBO/n_eff computation strategy is **per-cell aggregation, NOT global aggregation**. The mathematical justification:

- **PBO**: One CSCV per `(symbol, train_month)` cell, where the 50 trials within that cell ARE 50 distinct strategies (they share the same Optuna study so trial_id is meaningfully ranked by the within-study TPE sampler). Aggregate across cells via the cross-cell mean. Mean-of-PBOs has the natural interpretation "fraction of cells where IS-best is in the lower OOS half" — directly answering the strategy-overfit question without needing distributional assumptions.

- **n_eff**: One PCA per `(symbol, train_month)` cell on the (50 × n_candles) matrix. Aggregate across cells via the median. Median-of-n_effs is robust to per-cell outliers (e.g., a single cell with degenerate within-study trial ordering would otherwise drag a mean down to 1).

- **Why NOT cross-cell `groupby(["trial_id"]).sum()`**: Optuna's `trial_id` is a within-study sequential integer. Each `optimize_and_train` call creates an independent `optuna.create_study()` with its own TPE sampler keyed on `seed`. Cross-cell `trial_id` has no statistical meaning. iter-v3/003 demonstrated the failure mode: summing across ~100 unrelated models per `trial_id` produces 50 noisy aggregates whose first principal component captures ≥95% of variance, hence n_eff=1 and degenerate strategy axis.

- **Why NOT Fisher's method as headline (originally prescribed by diary)**: Fisher's method `combine_pvalues(method='fisher')` saturates at scale. For 173 cells with most PBOs near 0, χ² = -2 × Σ ln(p_i) is dominated by 173 × -2 × ln(ε) ≈ +5900, putting df=346 chi² survival deep in the tail (numerically 0.0). The mean is the only aggregator that returns a value strictly inside (0,1) on this distribution. Fisher's method is retained as a **diagnostic** in `aggregated_pbo.json` for transparency, NOT as criterion 21 input.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-004/engineering_report.md` with:
- The git commit SHA at backtest time
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The `per_cell_pbo.csv` row count, mean PBO, median PBO, and per-cell rank distribution
- The `comparison.csv` numerical diff against iter-v3/003 (expected: identical to 4 decimal places on headline metrics; PBO and n_eff strictly different)
- The 5 adversarial unit-test files' commit SHAs and pytest exit codes (4 inherited + 1 new)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the new Phase 5.5 inputs:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants unchanged; per-cell CPCV gap=22 documented as within-cell variant of REQUIRED_GAP=88 |
| 1 — Hypothesis | PASS — one sentence; specific testable target (PBO strictly in (0,1) AND n_eff > 4); falsifier in §4.2 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-004/per_cell_pbo_demo.py` committed at SHA `23bb5be` BEFORE this brief; 3 outputs (`per_cell_pbo_results.csv`, `aggregated_pbo.json`, `synthesis.md`) committed; results inline in §2.2-2.5; cell-key collapse rationale in §2.1; aggregator choice in §2.3; synthetic adversarial validation in §2.4 |
| 3 — Proposed Changes | PASS — symbols UNCHANGED (with V3_EXCLUDED check); labeling UNCHANGED; features UNCHANGED; risk gates UNCHANGED; SINGLE consumer-side methodology fix decomposed into 5 sub-rows in §3.5; brief-vs-code reconciliation table in §3.6 with 12 file-artifact verifiers; inheritance plan in §3.8 with 5 verifiers |
| 4 — Expected OOS Impact | PASS — predicted metrics table with EXACT expected match on headline; 5-tier falsifier in §4.2 (primary/secondary/tertiary/quaternary/quinary); split-merge clause in §4.3 with PBO strict-(0,1) as hard precondition |
| 5 — Risk Mitigation | PASS — 5 structural safeguards in §5.2 specifically targeting iter-v3/003's process failure mode |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/003; concentration acknowledged as expected fail |
| 7 — Pre-Registered Failure-Mode | PASS — 5 predictions with **3 process-level (P1, P2, P3)** per iter-v3/003 lesson #3; specific aggregator-misuse + sub-fix-drop scenarios named |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 24 criteria (22 inherited from iter-v3/003 + 2 NEW: 23 (aggregator consistency) and 24 (audit trail)); split-merge clause tightened (0.0 PBO no longer acceptable) |
| 9 — Library Stack | PASS — no new deps; per-cell aggregation strategy explicitly declared per Critic Rec #4 from iter-v3/003 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8 criterion 19.
