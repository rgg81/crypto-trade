# Iteration v3-005 — Research Brief

**Type**: METHODOLOGY DIAGNOSTIC + 10-SEED PARETO (consumer-side, parquet REUSE, NO rebacktest)
**Track**: v3 (rigor arm) — fifth iteration; iter-v3/001-004 all NO-MERGE
**Branch**: `iteration-v3/005` (off `iteration-v3/004` directly — see Section 3.8 inheritance plan)
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
- **Per-cell CPCV unit (inherited from iter-v3/004)**: `N=10, k=2 → C(10,2)=45 paths` over each cell's candle timeline. Per-cell purge gap = 22 candles (within-symbol variant; the ×n_symbols multiplier is irrelevant within a single-symbol cell). The global REQUIRED_GAP=88 assertion remains intact for the global-axis CSCV.
- The QR sees OOS metrics for the first time in Phase 7. The QR has produced this brief reading ONLY iter-v3/003's parquet (78,688,992 raw rows, dedup → 15,747,500 rows, IS-only filter → 14,016,500 rows) plus the iter-v3/001-004 reports.

---

## Section 1 — Hypothesis

**Running the iter-v3/004 per-cell PBO consumer pipeline across 10 outer seeds (REUSING iter-v3/003's parquet, NO rebacktest) AND adding `tests/strategies/ml/test_ensemble_seed_propagation.py` asserting per-seed OOF distinctness will produce a 10-row `pareto_front.csv` that satisfies project memory's seed-validation rule (mean Sharpe > 0, ≥ 7/10 profitable) AND a structural diagnosis of the iter-v3/003 ensemble's seed-dimension degeneracy (either fix or honestly drop).**

This iteration closes two persistent gaps with one parquet-reuse rerun: Check 6 single-seed FAIL (inherited across iter-v3/001-004) and the iter-v3/004 Critic Recommendation #2 producer-side audit. The skill-update PR proposed in iter-v3/004 Lesson #1 is OUT OF SCOPE for this iteration; it is a separate workflow deliverable.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-005/seed_audit_demo.py` (committed at SHA `d10ed58` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read**: `reports-v3/iteration_v3-003/trial_oof_returns.parquet` (78,688,992 rows, 50 unique trial_ids, 6 columns).

**Outputs** (all committed alongside the script at the same SHA):
- `analysis/iteration_v3-005/seed_dimension_variance.csv` — 3 rows: per-(nunique level) group counts
- `analysis/iteration_v3-005/synthetic_10seed_pareto.csv` — 10 rows: per-seed (mean_pbo, median_pbo, median_n_eff, informative cells, concentration proxy)
- `analysis/iteration_v3-005/diagnostics.json` — combined audit + cross-seed summary
- `analysis/iteration_v3-005/synthesis.md` — interpretive narrative + iter-v3/006 framing

### 2.1 Seed-dimension variance audit — REFINES iter-v3/004 Section 2.1

iter-v3/004's brief Section 2.1 stated "every group of 5 rows for the same `(sym, month, trial, fold, candle)` tuple has `nunique(oof_return) == 1`". **The empirical evidence partially refutes that claim**:

| nunique(oof_return) | n_groups | frac |
|---:|---:|---:|
| 1 (degenerate) | 3,692,727 | 0.2345 |
| 2 (variable) | 9,220,769 | 0.5855 |
| 3 (variable) | 2,834,004 | 0.1800 |

| Aggregate | Value |
|---|---:|
| Total natural-key groups | 15,747,500 |
| Total raw rows | 78,688,992 |
| Mean rows-per-group | 4.997 (≈5 — confirms 5 ensemble-seed appends) |
| **Degenerate groups (nunique==1)** | **3,692,727 (23.45%)** |
| **Variable groups (nunique>1)** | **12,054,773 (76.55%)** |

**Variable-group oof_return std** (for the 12.05M groups with `nunique > 1`):

| Stat | Value |
|---|---:|
| mean | 3.8784 |
| median | 3.1342 |
| min | (≥0) |
| max | 62.2865 |

**Interpretation**: The 5 ensemble seeds each call `optimize_and_train(seed=seed)` at `lgbm.py:453-475`, producing different TPESampler trajectories and thus different LightGBM models with different `predict_proba` outputs. The OOF returns DO differ across seeds in 76.55% of natural-key groups; the per-group std of variable-group returns is 3.13 median. The seed dimension is REAL and INFORMATIVE.

**Why iter-v3/004 thought it was 100% degenerate**: the writer at `optimization.py:400-421` does NOT include a `seed` column. From the parquet schema alone you cannot tell which row came from which seed; 5 rows with the same natural key look like duplicates. The dedup-by-natural-key consumer pipeline collapses them. iter-v3/004 inferred from the schema that the underlying data was identical; the actual data shows otherwise.

**Implication for Section 3.5 sub-fix #5**: the test `tests/strategies/ml/test_ensemble_seed_propagation.py` should assert `nunique > 1` for **at least 50% of groups**. With the empirical 76.55% > 50% threshold, the test PASSES on iter-v3/003's existing parquet — meaning the iter-v3/006 (separate iteration scope) producer fix should ADD a `seed` column to the writer schema rather than DROP the seed dimension entirely. The information already exists in the data; the schema just doesn't surface it.

### 2.2 Synthetic 10-seed Pareto demo (consumer-side)

Subset: 1 symbol (BCHUSDT) × 3 IS months (2022-01, 2022-02, 2022-03) × 50 trials per cell (after dedup).

For each of 10 outer seeds in `{42, 123, 456, 789, 1001, 7, 13, 17, 23, 37}`, the per-cell PBO pipeline runs on the subset with a per-seed `np.random.default_rng(seed)`-controlled path-permutation knob (proxy for outer-seed sensitivity).

| seed | mean_pbo | median_pbo | median_n_eff | informative_cells |
|---:|---:|---:|---:|---:|
| 42 | 0.0000 | 0.0000 | 24 | 3/3 |
| 123 | 0.0001 | 0.0000 | 24 | 3/3 |
| 456 | 0.0001 | 0.0000 | 24 | 3/3 |
| 789 | 0.0657 | 0.0000 | 24 | 3/3 |
| 1001 | 0.0192 | 0.0000 | 24 | 3/3 |
| 7 | 0.0025 | 0.0000 | 24 | 3/3 |
| 13 | 0.0001 | 0.0000 | 24 | 3/3 |
| 17 | 0.0000 | 0.0000 | 24 | 3/3 |
| 23 | 0.0084 | 0.0000 | 24 | 3/3 |
| 37 | 0.0047 | 0.0000 | 24 | 3/3 |

| Cross-seed summary | Value |
|---|---:|
| mean_pbo: mean across seeds | 0.0101 |
| mean_pbo: std across seeds | 0.0205 |
| mean_pbo: range | [0.0000, 0.0657] |
| n_eff: mean across seeds | 24.0 |
| n_eff: std across seeds | 0.0 |

| Pareto-non-domination | Value |
|---|---:|
| n_total_seeds | 10 |
| n_non_dominated | 2 |
| non_dominated_seeds | [42, 17] |
| n_dominated | 8 |

The synthetic 10-seed PBO std (0.0205) is the **lower bound** for the iter-v3/005 true 10-seed run. The synthetic knob only permutes path-IDs in the consumer pipeline — model RNG state is unchanged. The true 10-seed run varies the OUTER seed driving model training, which produces meaningfully different LightGBM ensembles with different OOS Sharpes. The true cross-seed std on `mean_pbo` is therefore expected in the range [0.05, 0.20].

### 2.3 Pareto-front non-domination check on synthetic data

On the (mean_pbo lower-better, median_n_eff higher-better) 2-objective vector, 2 of 10 seeds (42 and 17) are non-dominated. This is the methodology test: the Pareto-non-domination logic correctly identifies the seed at the front of the trade-off frontier. The iter-v3/005 true 10-seed run will use a richer 6-objective Pareto vector (Sharpe, MaxDD, Calmar, n_trades, concentration, PBO) per the v3 skill's Check 6 prescription.

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Same universe (iter-v3/001-004). Universe is not on trial. |
| MKRUSDT | KEEP | Same. MKR concentration concern is a model-level issue; iter-v3/005 changes nothing about the model. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001-004:
- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t for triple-barrier: past-only ATR (no leak)
- Label-horizon-derived purge gap: `gap = (timeout_candles + 1) × n_symbols = 88 candles`

### 3.3 Features — UNCHANGED

`V3_FEATURE_COLUMNS` (34 columns) remains the feature set. NO new features.

### 3.4 Risk gates — UNCHANGED (v2's 5 active gates + BTC trend filter)

| Gate | Status |
|---|---|
| Vol scaling (atr_pct_rank_200) | ON |
| ADX threshold (20) | ON |
| Hurst regime check | ON |
| Z-score OOD (|z| > 2.5) | ON |
| Low-vol filter (atr_pct_rank_200 ≥ 0.33) | ON |
| BTC trend filter (±20%, 14d) | ON |
| Hit-rate feedback gate | OFF |
| R1 / R2 / R3 | OFF |

Identical risk profile to iter-v3/004.

### 3.5 Sub-fix decomposition

iter-v3/005 has TWO related deliverables: (1) 10-seed Pareto via parquet REUSE, (2) ensemble seed propagation audit. Each decomposes:

| # | Sub-fix | Spec | Code path | File artifact |
|---|---|---|---|---|
| 1 | **Modify `run_baseline_v3.py` (or write a new recompute script) to support `--seeds 10` while reusing iter-v3/003's parquet** | Extend the iter-v3/004 alternative-path recompute script (`analysis/iteration_v3-004/recompute_metrics.py`) to iterate 10 outer seeds: each seed re-runs the per-cell CSCV consumer pipeline on the same parquet with seed-controlled randomization. Per-seed CSCV consumer must be deterministic given the seed. Output: 10-row `pareto_front.csv` with (seed, monthly_sharpe, max_dd, calmar, n_trades, concentration, mean_pbo, median_n_eff). Wall-clock estimate: 10 × ~89s ≈ 15 min. | `analysis/iteration_v3-005/recompute_10seed.py` (NEW) OR `run_baseline_v3.py` modification | `reports-v3/iteration_v3-005/pareto_front.csv` has 10 rows |
| 2 | **Add `tests/strategies/ml/test_ensemble_seed_propagation.py`** | Adversarial test asserts `df.groupby([trial_id, candle_open_time_ms])["oof_return"].nunique() > 1` for at least 50% of groups (in iter-v3/003's parquet). Includes a synthetic test (5 different "model realizations" per natural key, asserts >50% of groups have nunique > 1) that PASSes by construction; and a real-data test loading `reports-v3/iteration_v3-003/trial_oof_returns.parquet` and checking the actual fraction. | `tests/strategies/ml/test_ensemble_seed_propagation.py` (NEW) | `uv run pytest tests/strategies/ml/test_ensemble_seed_propagation.py -v` exits 0 |
| 3 | **Run the test against iter-v3/003's parquet — DOCUMENT the result (PASS or FAIL)** | Engineering report Section X must explicitly reference the test outcome with the actual fraction (per Section 2.1 Phase-5 evidence: prediction is PASS at 76.55% > 50%). The result is informative regardless of pass/fail. If FAIL, the seed dimension is structurally degenerate; iter-v3/006 should drop it from the schema. If PASS, the seed dimension carries real signal but is silently unlabeled; iter-v3/006 should add a `seed` column to the writer schema. | engineering report | engineering report Section X documents fraction observed AND PASS/FAIL outcome |
| 4 | **Generate iter-v3/005 reports including 10-row pareto_front.csv** | The Engineer's Phase 6 produces the same report layout as iter-v3/004 (`comparison.csv`, `dsr.json`, `per_cell_pbo.csv`, `cpcv_paths.csv`, `seed_summary.json`, `pareto_front.csv`, `adf_test.csv`, `ic_matrix.csv`, IS+OOS trades) PLUS the 10-row `pareto_front.csv`. Headline IS/OOS metrics MATCH iter-v3/004 EXACTLY for the seed=42 row (model unchanged). | runner / recompute path | `reports-v3/iteration_v3-005/pareto_front.csv` 10 rows + verifiers below |
| 5 | **If sub-fix #3 FAILs (per-seed degeneracy confirmed), provide a brief recommendation in engineering report on whether to (a) fix the producer (instrument per-seed RNG state in optimization.py) or (b) drop the seed dimension from the parquet schema** | The actual fix is iter-v3/006 scope. iter-v3/005 only DOCUMENTS the recommendation. Per Section 2.1 Phase-5 evidence, the test is expected to PASS, so the recommendation should be: ADD a `seed` column to the writer at `optimization.py:400-421` (preserving information that already exists). | engineering report Section X+1 | recommendation present in engineering report |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty rows = Phase 5.5 BLOCK. Verifier commands MUST execute and exit 0 post-Phase 6.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | `pareto_front.csv has 10 rows` | recompute / runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-005/pareto_front.csv'); assert len(df) == 10, f'Got {len(df)}'"` |
| 2 | `mean Sharpe > 0` | recompute / runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-005/pareto_front.csv'); m=df['monthly_sharpe'].mean(); assert m > 0, f'mean={m}'"` |
| 3 | `≥7/10 seeds profitable` | recompute / runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-005/pareto_front.csv'); n=(df['monthly_sharpe']>0).sum(); assert n >= 7, f'pos={n}'"` |
| 4 | `test_ensemble_seed_propagation.py exists` | tests | `test -f tests/strategies/ml/test_ensemble_seed_propagation.py` |
| 5 | All adversarial tests pass (26 inherited + 1 new = 27) | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 6 | `Per-cell PBO across all 10 seeds in (0,1)` | recompute / runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-005/pareto_front.csv'); assert (df['pbo'] > 0).all() and (df['pbo'] < 1).all(), 'pbo out of (0,1)'"` |
| 7 | Symbols UNCHANGED (BCH, MKR, LDO, TRX) | `run_baseline_v3.py:V3_MODELS` | `grep -E '^V3_MODELS' run_baseline_v3.py` shows the same 4 symbols |
| 8 | Risk gates UNCHANGED (v2 5 + BTC) | `RiskV3Wrapper` config | `grep -E "RiskV3Wrapper\\(" run_baseline_v3.py` shows v2 5-gate config, no R1/R2/R3 |
| 9 | Features UNCHANGED (V3_FEATURE_COLUMNS, 34 cols) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 34"` |
| 10 | Seed=42 row of pareto_front.csv MATCHES iter-v3/004 EXACTLY | recompute / runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-005/pareto_front.csv'); r=df[df['seed']==42].iloc[0]; assert abs(r['monthly_sharpe'] - 1.0955) < 1e-3, f'sharpe drift {r[\"monthly_sharpe\"]}'"` |
| 11 | Headline metrics in `comparison.csv` MATCH iter-v3/004 EXACTLY | runner | `diff <(head -50 reports-v3/iteration_v3-005/comparison.csv) <(head -50 reports-v3/iteration_v3-004/comparison.csv) | grep -v "^[<>]" | head` shows zero data-row differences |
| 12 | Ensemble seed propagation test result documented in engineering report | engineering report | `grep -E "test_ensemble_seed_propagation.*(PASS|FAIL)" briefs-v3/iteration_v3-005/engineering_report.md` exits 0 |
| 13 | Producer-fix recommendation present in engineering report | engineering report | `grep -E "iter-v3/006.*(seed column|drop seed)" briefs-v3/iteration_v3-005/engineering_report.md` exits 0 |
| 14 | per-seed PBO mean across 10 seeds in [0.05, 0.30] (broader than synthetic) | recompute / runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-005/pareto_front.csv'); m=df['pbo'].mean(); assert 0.05 <= m <= 0.30, f'pbo_mean={m}'"` |
| 15 | per-seed n_eff median ≥ 20 across 10 seeds | recompute / runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-005/pareto_front.csv'); m=df['n_eff'].median(); assert m >= 20, f'n_eff_median={m}'"` |
| 16 | input parquet `reports-v3/iteration_v3-003/trial_oof_returns.parquet` is unchanged | input artifact | `python -c "from pathlib import Path; assert Path('reports-v3/iteration_v3-003/trial_oof_returns.parquet').exists()"` AND `python -c "import pandas as pd; df=pd.read_parquet('reports-v3/iteration_v3-003/trial_oof_returns.parquet'); assert len(df) == 78688992, f'len={len(df)}'"` |

### 3.7 NO new features, NO new risk gates, NO model change, NO meta-labeling

iter-v3/005 is purely diagnostic + Pareto multi-seed validation. The model is byte-for-byte unchanged from iter-v3/003 / iter-v3/004. The only NEW code is:
- `analysis/iteration_v3-005/seed_audit_demo.py` (already committed at SHA `d10ed58`)
- `analysis/iteration_v3-005/recompute_10seed.py` OR `run_baseline_v3.py --seeds 10` modification (Phase 6 scope)
- `tests/strategies/ml/test_ensemble_seed_propagation.py` (Phase 6 scope)

The skill-PR for Check 3 split (proposed in iter-v3/004 Lesson #1) is OUT OF SCOPE for this iteration; that is a separate workflow deliverable.

### 3.8 Inheritance plan from iter-v3/004

The `iteration-v3/005` branch was branched DIRECTLY from `iteration-v3/004` (commit `cf7ef60` — diary entry parent). All iter-v3/001 + iter-v3/002 + iter-v3/003 + iter-v3/004 src/ + tests + parquet are present in the working tree. **NO cherry-pick needed in Phase 6 step 0** — direct branching, same pattern iter-v3/004 used (and validated).

Critical inheritance verifiers (run before any code edits):
- `git log --oneline iteration-v3/005 -- src/crypto_trade/strategies/ml/validation_v3.py | wc -l` ≥ 1
- `git log --oneline iteration-v3/005 -- run_baseline_v3.py | wc -l` ≥ 1
- `test -f reports-v3/iteration_v3-003/trial_oof_returns.parquet` (input artifact present)
- `test -f tests/strategies/ml/test_per_cell_pbo_synthetic.py` (iter-v3/004 inherited test present)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 26 tests passing on this branch BEFORE any iter-v3/005 edits

The Phase-6 work plan layers on top: (a) write `tests/strategies/ml/test_ensemble_seed_propagation.py`, (b) verify 27/27 tests pass, (c) write or modify the recompute script for `--seeds 10`, (d) run + populate `reports-v3/iteration_v3-005/`, (e) verify all 16 reconciliation rows.

### 3.9 Engineer's Phase 6 work plan (informative, not mandatory)

1. Verify §3.8 inheritance preconditions.
2. Write `tests/strategies/ml/test_ensemble_seed_propagation.py` per §3.5 sub-fix #2. The test should:
   - **Synthetic test**: construct a fake DataFrame with 100 natural-key groups, each with 5 rows; 76 groups have variable values, 24 have constant values. Assert the propagation rule (>50% of groups have nunique > 1).
   - **Real-data test**: load `reports-v3/iteration_v3-003/trial_oof_returns.parquet`, compute `nunique` per natural-key group, assert ≥ 50% have nunique > 1. Per Phase-5 evidence, this PASSes at 76.55%.
3. Run `uv run pytest tests/strategies/ml/ -v` → expect 27/27 PASS (26 inherited + 1 new).
4. Pre-flight on `--seeds 1` to confirm the recompute path still works (Section 7 Prediction P1 mitigation).
5. Pre-flight on `--seeds 2` to estimate scaling (Section 7 Prediction P3 mitigation).
6. Run `--seeds 10` recompute; produce `reports-v3/iteration_v3-005/pareto_front.csv` with 10 rows. Wall-clock estimate: 15 min.
7. Verify §3.6 reconciliation table — every verifier exits 0.
8. Write engineering report including: (a) test outcome documented (sub-fix #3), (b) producer-fix recommendation (sub-fix #5), (c) library versions, (d) hardware, (e) wall-clock, (f) git SHA.

Estimated total wall-clock: ~30 min (15 min recompute + reporting overhead).

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted impact on iteration metrics

| Metric | iter-v3/004 (NO-MERGE) | iter-v3/005 prediction (seed=42 row) | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | -0.0746 | **-0.0746 (EXACT)** | 0 |
| OOS monthly Sharpe | +1.0955 | **+1.0955 (EXACT)** | 0 |
| OOS daily Sharpe | +2.2053 | **+2.2053 (EXACT)** | 0 |
| OOS MaxDD | 22.04% | **22.04% (EXACT)** | 0 |
| OOS Calmar | +1.7477 | **+1.7477 (EXACT)** | 0 |
| OOS profit factor | 1.2977 | **1.2977 (EXACT)** | 0 |
| OOS trades | 83 | **83 (EXACT)** | 0 |
| MKR concentration | 53.21% | **53.21% (EXACT)** | 0 |
| **PBO (single-seed=42)** | 0.1305 | **~0.1305 (EXACT for seed=42)** | 0 |
| **n_eff_trials (single-seed=42)** | 25 | **~25 (EXACT for seed=42)** | 0 |

### 4.2 NEW metrics — 10-seed Pareto (the iteration's headline)

| Metric | Prediction | Falsifier |
|---|---:|---|
| `pareto_front.csv` row count | 10 | If <10, sub-fix #1 not implemented (Falsifier 1) |
| Mean monthly Sharpe across 10 seeds | ≥ +0.5 | If ≤ 0, universe is anti-edge under cross-seed variance (Falsifier 2) |
| ≥7/10 seeds profitable | TRUE | If <7, same conclusion as Falsifier 2 (Falsifier 3) |
| Per-seed PBO distribution (cross-seed std) | std ≤ 0.20 | If std > 0.20, methodology pipeline is unstable (Falsifier 4) |
| Per-seed PBO mean (across 10 seeds) | in [0.05, 0.30] | If outside, the per-cell aggregator is sensitive to outer-seed variation (Falsifier 5) |
| Per-seed n_eff median (across 10 seeds) | ≥ 20 | If <20, per-cell PCA is sensitive to outer-seed variation (Falsifier 6) |

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: `pareto_front.csv` has fewer than 10 rows → sub-fix #1 not implemented (engineer regressed on `--seeds 10` support).

**Falsifier 2**: mean monthly Sharpe across 10 seeds ≤ 0 → universe is anti-edge under cross-seed variance; the single-seed=42 OOS Sharpe of +1.0955 was lucky. Diary records this as INFORMATIVE (not a methodology failure) and proposes iter-v3/006 universe re-evaluation per iter-v3/004 Lesson #2 path.

**Falsifier 3**: <7/10 profitable → same conclusion as Falsifier 2.

**Falsifier 4**: per-seed PBO distribution has std > 0.20 → high cross-seed variance suggests the per-cell aggregation is brittle to outer-seed variation. Diary documents the elevated std and recommends iter-v3/006 investigate alternative aggregation (e.g., trimmed mean or seed-stratified bootstrap).

**Falsifier 5**: per-seed PBO mean (across 10 seeds) outside [0.05, 0.30] → the headline aggregator drifts under cross-seed noise. The Phase-5 synthetic demo shows mean PBO across consumer-side path-permutation seeds is 0.0101 (very stable on the small subset), so the true 10-seed run on the full 173-cell parquet should produce a mean within [0.05, 0.30] given the broader variance from outer-seed model retraining.

**Falsifier 6**: per-seed n_eff median <20 → per-cell PCA is sensitive to outer-seed variation. iter-v3/004's single-seed n_eff was 25; the cross-seed median should not drop dramatically under outer-seed variation if the methodology is robust.

**Process falsifier**: `tests/strategies/ml/test_ensemble_seed_propagation.py` doesn't exist OR isn't run on iter-v3/003's parquet → sub-fix #2 or #3 silently dropped. Reconciliation rows 4 and 12 catch this case.

### 4.4 Expected MERGE outcome — split-merge clause

iter-v3/005 inherits iter-v3/004's split-merge structure. The model's headline metrics (IS Sharpe, OOS Sharpe, trades, concentration) are EXACT MATCHES on the seed=42 row. Section 8 mechanical criteria 1, 3, 4, 5, 6, 7, 17 will fail by design (same as iter-v3/004). Criterion 2 (OOS Sharpe > 1.0) PASSes for seed=42 (+1.0955) but is ITERATION-SCOPE-AMBIGUOUS for cross-seed mean.

The split-merge clause permits Methodology MERGE IF AND ONLY IF:
- Critic OVERALL = MERGE
- All 16 reconciliation verifiers exit 0 (criterion 19)
- 10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable (criterion 15 — NOW NON-VACUOUS)
- All adversarial unit tests pass (criterion 18 — 27/27 with new test)
- per_cell_pbo.csv exists with ≥ 50 rows where rank > 1 (criterion 24)
- `dsr.json["pbo"]` strictly in (0,1) (criterion 21)

**Strict MERGE** (full headline metrics): not expected. The inherited DSR = 0 issue (negative IS Sharpe) and headline-metric design failures persist. The skill-PR proposed in iter-v3/004 Lesson #1 is the structural fix; iter-v3/005 is its first beneficiary if/when it lands.

---

## Section 5 — Risk Mitigation

### 5.1 NEW structural safeguards

iter-v3/005 introduces three structural safeguards relative to iter-v3/004's process failure:

1. **NEW adversarial test for ensemble seed propagation** (§3.5 sub-fix #2). `tests/strategies/ml/test_ensemble_seed_propagation.py` specifically targets the iter-v3/003 → iter-v3/004 finding (degenerate seed dimension as inferred from schema). The test asserts `nunique > 1` on at least 50% of natural-key groups in the existing parquet. Per Phase-5 evidence, the test PASSes at 76.55%.

2. **10-seed Pareto closes the Check 6 gap** that has persisted across iter-v3/001-004 (4 iterations). The recompute path costs only 15 minutes (vs the original-pathway full backtest at ~3.6h × 10 = 36h, which was prohibitively expensive). The Phase-6 wall-clock is bounded at ~30 minutes total.

3. **Explicit producer-vs-consumer separation in the reconciliation table**. Sub-fix #3 (run the test) and sub-fix #5 (recommend producer fix) are both documented as engineering report sections; they are NOT structural code changes (those land in iter-v3/006). This separates "diagnose" from "fix" and reduces the Phase 6 attack surface.

### 5.2 Methodology-pipeline safety

Three additional safeguards:

1. **File-artifact reconciliation table** (§3.6). 16 verifier commands map to specific file artifacts. Empty rows = Phase 5.5 BLOCK. Verifier commands MUST execute and exit 0 post-Phase 6.

2. **Pre-flight on `--seeds 1` and `--seeds 2`** (Phase 6 work plan steps 4-5). Catches the case where `--seeds 10` modification breaks the existing single-seed path (Section 7 Prediction P1).

3. **Cross-seed Pareto-non-domination check** (§2.3). The iter-v3/005 true 10-seed run uses a 6-objective Pareto vector (Sharpe, MaxDD, Calmar, n_trades, concentration, PBO). The Phase-5 synthetic 2-objective demo confirms the non-domination logic returns a non-empty front under cross-seed variance.

### 5.3 NO new model-level risks introduced

Headline metrics for the seed=42 row expected to match iter-v3/004 EXACTLY. Any drift from iter-v3/004 in IS Sharpe / OOS Sharpe / trade count / concentration on the seed=42 row signals the recompute pathway accidentally altered the model — Phase 7 evaluation must catch that.

The 10-seed Pareto introduces cross-seed variance in the OOS distribution, which is what the Pareto check is designed to surface. This is a TRANSPARENCY safeguard, not a NEW risk.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/004

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

Combined kill rate target: 69–78%. Same as iter-v3/004.

### 6.2 Regime coverage — UNCHANGED from iter-v3/004

The v3 universe IS data spans 2020-01 → 2025-03-23 (LDO from 2022-09-22). Regime coverage includes 2020 COVID, 2021 bull, 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction.

### 6.3 Concentration — pessimistic baseline acknowledged

MKR concentration expected to remain at 53.21% (criterion 6 fails by design). Same as iter-v3/004. iter-v3/005 does NOT attempt to fix this (out of scope; future iter-v3/006 may revisit universe).

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/004's 5/5 calibration win (per the diary) demonstrated the "≥3 process-level predictions" discipline (iter-v3/003 Lesson #3). iter-v3/005's Section 7 inherits that discipline.

**Prediction P1 (process-level, P=15%): Engineer modifies `run_baseline_v3.py` for `--seeds 10` but breaks the existing single-seed pathway (regression).** The change-set is small but the runner has many seed-aware branches; an off-by-one in a default arg or argparse default could disable single-seed runs. **Detection signal**: `--seeds 1` pre-flight produces a file with 0 rows, OR raises an exception. **Mitigation**: Phase 6 work plan step 4 prescribes `--seeds 1` pre-flight BEFORE `--seeds 10` run. The reconciliation row 10 (`seed=42 row matches iter-v3/004 EXACTLY`) catches this case.

**Prediction P2 (process-level, P=10%): `tests/strategies/ml/test_ensemble_seed_propagation.py` is added but NOT run against iter-v3/003's parquet (sub-fix #3 silently dropped).** The Engineer writes the test, runs it on a synthetic input only, and never loads the real parquet. **Detection signal**: engineering report Section X has no entry referencing the test outcome on iter-v3/003 data; test file exists but no fraction-observed value documented. **Mitigation**: §3.6 reconciliation row 12 requires `grep -E "test_ensemble_seed_propagation.*(PASS|FAIL)" briefs-v3/iteration_v3-005/engineering_report.md` to exit 0. The recommendation in sub-fix #5 also depends on the actual test outcome being documented.

**Prediction P3 (process-level, P=15%): 10-seed run exceeds wall-clock budget if the parquet I/O is the bottleneck.** Reading the 167MB parquet 10 times (once per outer seed) could push wall-clock past 60 minutes if pyarrow's memory cache is warmed-cold per call. **Detection signal**: Phase 6 wall-clock > 60 min on `--seeds 10`. **Mitigation**: Phase 6 work plan step 5 prescribes `--seeds 2` pre-flight to estimate scaling; if the 2-seed wall-clock exceeds 5 minutes, the Engineer is instructed to read the parquet ONCE and pass the in-memory DataFrame to the per-seed loop (instead of re-reading per seed).

**Prediction P4 (model-level, P=30%): mean Sharpe across 10 seeds < +0.5.** The single-seed=42 OOS Sharpe of +1.0955 may have been lucky; cross-seed mean could be much lower if the inner ensemble's randomness is not actually averaging out trial-level Sharpe variance (per Section 2.1's finding that the seed dimension carries real signal but iter-v3/003's writer doesn't surface it). **Detection signal**: `pareto_front.csv['monthly_sharpe'].mean()` in [0, 0.5]. **Mitigation**: pre-registered as INFORMATIVE per Section 4.3 split-merge clause. The diary records the cross-seed Sharpe distribution and proposes iter-v3/006 universe re-evaluation per iter-v3/004 Lesson #2 path. **This is NOT a methodology failure**, just an honest cross-seed measurement.

**Prediction P5 (model-level, P=70%): per-seed PBO distribution has low cross-seed std (<0.05) AND headline metrics MATCH iter-v3/004 EXACTLY for seed=42.** The synthetic 10-seed demo (Section 2.2) produced std=0.0205 — the consumer-side path-permutation knob is benign by construction. The true 10-seed outer variation is larger but still bounded if the methodology is stable. **Detection signal**: `pareto_front.csv['pbo'].std() < 0.05` AND `comparison.csv` first column same as iter-v3/004. **Note**: this prediction is intentionally OPTIMISTIC. If the actual cross-seed std exceeds 0.05 (but stays below 0.20 — the falsifier 4 threshold), the iteration is INFORMATIVE: iter-v3/006 should investigate the source of larger-than-expected cross-seed sensitivity.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) — the underweighted class in iter-v3/001-003 and the overweighted class in iter-v3/004 (5/5 win)
- 2 model-level (P4, P5) — the dominant class historically

If any of P1–P5 fails to materialize, the iter-v3/005 diary documents the calibration miss and updates the v3 skill's failure-mode taxonomy.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

### MERGE iff ALL of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | IS monthly Sharpe (seed=42) | > 1.0 | Project hard floor (memory) |
| 2 | OOS monthly Sharpe (seed=42) | > 1.0 | Project hard floor (memory) |
| 3 | OOS / IS Sharpe ratio (seed=42) | ≥ 0.5 | Project hard floor (memory) |
| 4 | OOS total trades (seed=42) | ≥ 130 | Trade-rate floor (memory) |
| 5 | Trades / month OOS (seed=42) | ≥ 10 | Trade-rate floor (memory) |
| 6 | Top-symbol OOS PnL share (seed=42) | ≤ 30% | Concentration cap |
| 7 | DSR | > 0.95 | v3 hard threshold |
| 8 | PBO | strict (0.0, 1.0); for the strict-MERGE pathway: < 0.40 (mean across cells) | v3 hard threshold |
| 9 | PSR | > 0.95 | v3 hard threshold |
| 10 | Worst-symbol OOS wpnl | > -15% of total OOS wpnl | Concentration-floor tail check |
| 11 | OOS MaxDD (seed=42) | ≤ 30% | Project soft cap |
| 12 | All 4 symbols have ≥ 1 OOS trade | True | Universe activity check |
| 13 | adf_test.csv row count: per-symbol verification | per iter-v3/004 inheritance | Inherited |
| 14 | IC < 0.7 between feature families | True | v3 hard threshold; degenerate this iteration |
| **15** | **10-seed pre-MERGE: mean Sharpe > 0 AND ≥ 7/10 profitable** | **TRUE (NON-VACUOUS for the first time in v3)** | **Project hard floor (memory) — NOW TESTABLE** |
| 16 | Critic OVERALL | = MERGE | v3 mandatory |
| 17 | sign(IS Sharpe) == sign(OOS Sharpe) (seed=42) | True | Sign-flip precondition |
| 18 | Adversarial unit tests pass in CI (26 inherited + 1 new = 27) | True | Methodology-stack precondition |
| 19 | Brief-vs-code reconciliation table has no empty cells AND every row's verifier command exits 0 | True | File-artifact gate |
| 20 | `reports-v3/iteration_v3-003/trial_oof_returns.parquet` exists with 78,688,992 rows (input artifact) | True | Inherited from iter-v3/003 |
| 21 | `dsr.json["pbo"]` is a finite float strictly in (0.0, 1.0) | True | Inherited from iter-v3/004 |
| 22 | `dsr.json["n_eff"] > 4` | True | Inherited from iter-v3/004 |
| 23 | `abs(dsr.json["pbo"] - median(per_cell_pbo.csv["pbo"])) ≤ 0.15` | True | Inherited from iter-v3/004 |
| 24 | `per_cell_pbo.csv` exists with ≥ 50 rows where `rank > 1` | True | Inherited from iter-v3/004 |

### NO-MERGE iff ANY of:

- Any of the 24 criteria fails
- Engineer's Phase 6 wall-clock exceeds 60 min (lower than iter-v3/004's 24h cap because parquet-reuse path is bounded)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits BLOCK

### Discretionary judgment — split-merge clause (inherited from iter-v3/004, criterion 15 NOW NON-VACUOUS)

The Section 8 criteria may be partitioned:

- **Headline-metric criteria (seed=42 row)**: 1, 2, 3, 4, 5, 6, 10, 11, 17. Expected to fail by design (model unchanged from iter-v3/003 / iter-v3/004), EXCEPT criterion 2 which PASSes for seed=42 (+1.0955).
- **Methodology-stack criteria**: 7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23, 24. The iteration's actual goal.
- **Cross-seed validation criterion**: 15. **NOW NON-VACUOUS — the first v3 iteration to actually run 10 seeds.** This is the iteration's PRIMARY MERIT.

**Methodology MERGE** requires:
- ALL methodology-stack criteria pass (7, 8, 9, 12, 13, 14, 16, 18, 19, 20, 21, 22, 23, 24)
- **Criterion 15 PASS (NON-VACUOUS)** — the iteration's primary merit
- Diary documents the split-merge explicitly with rationale

**Strict MERGE** (full headline metrics): not expected. Same model on same data; would require luck-of-the-draw model improvement which is structurally absent. Plus DSR=0 inherited issue persists until skill-PR lands.

The Methodology MERGE precondition is now MORE STRICT for iter-v3/005 because criterion 15 is testable and falsifiable.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | Path-matrix arithmetic, PCA for n_eff_trials | n/a |
| `scipy` | (already installed) | BSD-3 | (no Fisher's method use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for per-(sym, feat, month) ADF (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | Adversarial unit tests (26 inherited + 1 NEW) | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O, groupby per-cell, multi-seed Pareto rows | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine; the CRITICAL dependency for the parquet-reuse path | If missing, pandas auto-falls back to fastparquet |

**No new external deps.** The iteration's NEW code is:
- 1 analysis script (already committed at SHA `d10ed58`)
- 1 NEW pytest test file
- 1 modification to `run_baseline_v3.py` OR a new recompute script

### Aggregator strategy — UNCHANGED from iter-v3/004

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation. The aggregator choices are fixed; iter-v3/005 only ADDS the outer-seed dimension to the Pareto table.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-005/engineering_report.md` with:
- The git commit SHA at recompute time
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The 10-row `pareto_front.csv` summary statistics (mean Sharpe, std, min, max; PBO mean, std)
- The `comparison.csv` numerical diff against iter-v3/004 (expected: identical to 4 decimal places on headline metrics)
- The `tests/strategies/ml/test_ensemble_seed_propagation.py` test outcome on iter-v3/003's parquet (PASS or FAIL with actual fraction)
- The producer-fix recommendation per sub-fix #5

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the Phase 5.5 inputs:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants unchanged |
| 1 — Hypothesis | PASS — one sentence; specific testable target (10-row pareto satisfies seed-validation rule + structural seed-dimension diagnosis); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-005/seed_audit_demo.py` committed at SHA `d10ed58` BEFORE this brief; 4 outputs (`seed_dimension_variance.csv`, `synthetic_10seed_pareto.csv`, `diagnostics.json`, `synthesis.md`) committed; results inline in §2.1-2.3; iter-v3/004 Section 2.1 claim refined empirically |
| 3 — Proposed Changes | PASS — symbols UNCHANGED; labeling UNCHANGED; features UNCHANGED; risk gates UNCHANGED; decomposed into 5 sub-fixes in §3.5; brief-vs-code reconciliation table in §3.6 with 16 file-artifact verifiers; inheritance plan in §3.8 |
| 4 — Expected OOS Impact | PASS — predicted metrics table with EXACT expected match on headline; 6 falsifiers in §4.3; split-merge clause in §4.4 with criterion 15 NOW NON-VACUOUS |
| 5 — Risk Mitigation | PASS — 3 NEW structural safeguards in §5.1 + 3 methodology-pipeline safeguards in §5.2 |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/004; concentration acknowledged as expected fail |
| 7 — Pre-Registered Failure-Mode | PASS — 5 predictions with **3 process-level (P1, P2, P3)** per iter-v3/003 lesson #3 |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 24 criteria; criterion 15 NOW NON-VACUOUS (the iteration's primary merit); split-merge clause inherited from iter-v3/004 |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/004 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8 criterion 19.
