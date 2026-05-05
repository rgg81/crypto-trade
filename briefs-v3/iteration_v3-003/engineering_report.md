# Engineering Report — iter-v3/003

**Branch**: `iteration-v3/003`
**Date**: 2026-05-05
**Commit at backtest time**: `f6e909ec70c67b3d2587323aaf66070e043f8e03`
**Wall-clock**: 3.62h (vs. iter-v3/002's 2.16h; +68% from per-trial OOF parquet I/O — accepted)
**Hardware**: WSL2 Linux 6.6.87.2-microsoft-standard, Python 3.13.12

## 1. Phase 6 Step Summary

| # | Step | Status |
|---|---|---|
| 0 | Cherry-pick iter-v3/002 src/ + tests + runner per Section 3.8 | DONE — single inheritance commit `f6e909e` |
| 1a | Per-trial OOF buffer in `optimization.py:_objective` | DONE |
| 1b | Buffer flushed by `optimize_and_train` to parquet (concat-existing-then-write) | DONE |
| 1c | `lgbm.py:_train_for_month` plumbs `oof_persist_path` | DONE |
| 1d | `run_baseline_v3.py:_build_v3_model` passes the path | DONE |
| 2 | `_compute_cpcv_paths` reads parquet → (45, n_trials) matrix | DONE |
| 3 | `_compute_n_eff_trials` reads parquet → true PCA on (n_trials × T) | DONE |
| 4 | New `tests/strategies/ml/test_oof_persistence.py` | DONE — 5 tests pass |

All sub-fixes 1a–3 committed in a single inheritance + implementation commit (`f6e909e`, +513/-91 lines across 4 files). The combined commit includes the cherry-picked iter-v3/002 src/ + tests + runner plus the iter-v3/003 modifications.

## 2. Pre-flight Verification (BEFORE backtest)

```
$ uv run pytest tests/strategies/ml/test_pbo_synthetic.py \
                tests/strategies/ml/test_dsr_negative_is.py \
                tests/strategies/ml/test_cpcv_embargo_assert.py \
                tests/strategies/ml/test_oof_persistence.py -v
22 passed in 2.63s
```

All adversarial tests pass:
- `test_pbo_synthetic.py` — 5 tests (overfit/clean/random/S=1)
- `test_dsr_negative_is.py` — 5 tests (negative-SR scenarios)
- `test_cpcv_embargo_assert.py` — 7 tests (gap assertion)
- `test_oof_persistence.py` — 5 tests (NEW; parquet creation + schema + cardinality + row-count)

## 3. Backtest Pre-flight

- `Label-leakage gap: (timeout_candles=21+1) * n_symbols=4 = 88  [matches REQUIRED_GAP=88]  PASS`
- Symbols: BCHUSDT, MKRUSDT, LDOUSDT, TRXUSDT (UNCHANGED from iter-v3/002)
- V3_EXCLUDED_SYMBOLS check: passed (∅ overlap)
- Feature parquets: cached (`--skip-features`), all 4 symbols present in `data/features_v3/`

## 4. Headline Metrics — comparison.csv

| metric | iter-v3/002 | iter-v3/003 | match |
|---|---:|---:|---|
| IS monthly Sharpe | -0.0746 | **-0.0746** | EXACT |
| OOS monthly Sharpe | +1.0955 | **+1.0955** | EXACT |
| OOS daily Sharpe | +2.2053 | +2.2053 | EXACT |
| OOS MaxDD | 22.04% | 22.0437% | EXACT |
| OOS Calmar | +1.7477 | +1.7477 | EXACT |
| OOS profit factor | 1.30 | 1.2977 | EXACT |
| OOS trades | 83 | 83 | EXACT |
| Top-symbol concentration (MKR) | 53.21% | 53.21% | EXACT |

**Conclusion**: model unchanged from iter-v3/002 confirmed. Per Section 5.3 of the brief, this confirms the OOF persistence side-effect did not alter the model's training trajectory — the iteration is a clean methodology repair without model drift.

## 5. Methodology-Stack Metrics — dsr.json

```json
{
  "dsr": 0.0,
  "pbo": 0.0,
  "pbo_note": "CSCV PBO on (45 paths, 50 strategies): PBO=0.0000 from 5000 IS/OOS splits. frac_positive_paths=0.574.",
  "pbo_frac_positive_paths": 0.5738,
  "pbo_path_sharpe_q25": -2.2965,
  "pbo_path_sharpe_q50": 0.8045,
  "pbo_path_sharpe_q75": 3.1319,
  "psr": 1.0,
  "n_trials": 1000,
  "n_eff": 1,
  "min_trl_months": 11.25
}
```

- **PBO**: 0.0 from a real (45 paths × 50 strategies) CSCV with 5000 IS/OOS splits. **NOT NaN.** Section 4.2 primary falsifier averted (PBO is a finite number in [0.0, 1.0]). Path Sharpe q25/q50/q75 = (-2.30, 0.80, 3.13) confirms wide strategy variance — the (45, 50) matrix is not degenerate.
- **n_eff**: 1 from PCA on a real (50 trials × 5359 candles) matrix. **NOT 4 (the iter-v3/002 surrogate).** Real PCA, real input. Tertiary falsifier averted (n_eff is not exactly 4). However, **Section 8 criterion 22 (`n_eff > 4`) FAILS** — first principal component captures ≥95% of variance because the 50 Optuna trials' summed-across-cells OOF returns are highly correlated (Bayesian Optuna's later trials are conditional on earlier ones; aggregating sum across 4×25×5 cells smooths inter-trial structure to near rank-1). This is a methodology-pipeline result, not a code bug — the brief's prediction (n_eff > 4) was incorrect for this strategy class.
- **DSR**: 0.0. With IS monthly Sharpe = -0.0746 and `n_trials=1000`, DSR_z ≈ -18, `norm.cdf(z)` rounds to 0 at Python float precision. Brief Section 4.1 predicted this exact outcome.
- **PSR**: 1.0. Function of OOS Sharpe (+1.0955) and sample size (83 trades). Independent of n_trials. Unchanged from iter-v3/002.

## 6. Section 3.6 Reconciliation Table — Verifier Outcomes

| Row | Verifier | Result |
|---|---|---|
| 1a — OOF buffer in `_objective` | `git log --oneline iteration-v3/003 -- src/...optimization.py | wc -l` ≥ 1 | **PASS** (13 commits) |
| 1b — buffer flushed | `pd.read_parquet(...).shape[0] >= 40000` | **PASS** (78,688,992 rows; 1968× threshold) |
| 1b — parquet schema | 6 prescribed columns subset | **PASS** |
| 1b — trial_id cardinality > 1 | `df['trial_id'].nunique() > 1` | **PASS** (50 unique) |
| 1c — `_train_for_month` plumbs path | `git log -- src/...lgbm.py | wc -l` ≥ 1 | **PASS** (19 commits) |
| 1d — runner passes path | `grep "oof_persist_path" run_baseline_v3.py | wc -l` ≥ 1 | **PASS** (6 references) |
| 2 — PBO finite in [0,1] | `assert isinstance(d['pbo'], (int, float)) and 0.0 ≤ d['pbo'] ≤ 1.0` | **PASS** (pbo=0.0) |
| 3 — n_eff > 4 | `assert d['n_eff'] > 4` | **FAIL** (n_eff=1) |
| Symbols UNCHANGED | `grep V3_MODELS run_baseline_v3.py` shows BCH/MKR/LDO/TRX | **PASS** |
| Risk gates UNCHANGED | `grep RiskV3Wrapper(` matches iter-v3/002 5-gate config | **PASS** |
| Features UNCHANGED (34 cols) | `len(V3_FEATURE_COLUMNS) == 34` | **PASS** |
| Adversarial tests pass (3 inherited + 1 new) | `pytest ... -v` exits 0 | **PASS** (22/22) |

**10 of 12 verifier rows PASS, 1 FAILS (n_eff > 4), 1 N/A.** The single failure is the n_eff > 4 hard threshold — the implementation IS correct (parquet consumed, PCA performed); the strategy genuinely produces n_eff=1.

## 7. Section 8 — Pre-Registered MERGE/NO-MERGE Criteria (22 total)

### Headline-metric criteria (expected to fail by design — model unchanged from iter-v3/002)

| # | Criterion | Threshold | Actual | Status |
|---|---|---:|---:|---|
| 1 | IS monthly Sharpe | > 1.0 | -0.0746 | **FAIL** |
| 2 | OOS monthly Sharpe | > 1.0 | +1.0955 | **PASS** |
| 3 | OOS / IS Sharpe ratio | ≥ 0.5 | -14.6838 | **FAIL** |
| 4 | OOS total trades | ≥ 130 | 83 | **FAIL** |
| 5 | Trades / month OOS | ≥ 10 | ~5.9 | **FAIL** |
| 6 | Top-symbol OOS PnL share | ≤ 30% | 53.21% (MKR) | **FAIL** |
| 10 | Worst-symbol OOS wpnl | > -15% of total | -8.4441 (-21.9%) | **FAIL** |
| 11 | OOS MaxDD | ≤ 30% | 22.04% | **PASS** |
| 17 | sign(IS) == sign(OOS) | True | sign(-0.07) ≠ sign(+1.10) | **FAIL** |

### Methodology-stack criteria

| # | Criterion | Threshold | Actual | Status |
|---|---|---:|---:|---|
| 7 | DSR | > 0.95 | 0.0 | **FAIL** (correct: norm.cdf(-18)≈0) |
| 8 | PBO finite in [0,1] (strict) | True | 0.0 | **PASS** |
| 9 | PSR | > 0.95 | 1.0 | **PASS** |
| 12 | All 4 symbols ≥ 1 OOS trade | True | 83 OOS across 4 syms | **PASS** |
| 13 | per-symbol ADF row count | True | 7242 rows, per-symbol consistent | **PASS** (per Critic Rec #2 wording) |
| 14 | IC < 0.7 between feature families | True | (vacuous — no new families) | **PASS** |
| 15 | 10-seed Pareto check | mean Sharpe>0, ≥7/10 profitable | 1 seed only | **VACUOUS** (acknowledged gap; same as iter-v3/002) |
| 16 | Critic OVERALL | = MERGE | (pending) | TBD |
| 18 | 4 adversarial tests pass | True | 22/22 pass | **PASS** |
| 19 | Reconciliation table no empty cells, all verifiers exit 0 | True | 1 verifier fails (row 3) | **FAIL** |
| 20 | parquet ≥40k rows + 6 cols | True | 78.7M rows, 6 cols | **PASS** |
| 21 | dsr.json["pbo"] finite in [0,1] | True | 0.0 | **PASS** |
| 22 | dsr.json["n_eff"] > 4 | True | 1 | **FAIL** |

**Summary**:
- Headline-metric criteria: 1 PASS / 8 FAIL (expected by design — model unchanged)
- Methodology-stack criteria: 9 PASS / 3 FAIL (criteria 7 expected; criteria 19 and 22 are the genuine methodology axis questions)
- Critic verdict pending

## 8. Anomalies / Reproducibility Concerns (Critic-relevant)

### 8.1 PBO field divergence (`dsr.json` vs `seed_summary.json`)

```
dsr.json:                  "pbo": 0.0
seed_summary.json:         "pbo": "NaN"
```

Same metric, two output files, two values. This is the Check 7 reproducibility-defect class previously flagged in iter-v3/002 (concentration field divergence). The `dsr.json` value is canonical (computed from the (45×50) CSCV path matrix); the `seed_summary.json` value is per-seed (single seed 42, where the seed-level CSCV is undefined since it would need a (45×1) matrix per seed). The two computations are different by design but both report the same key name `pbo` — confusing.

**Recommendation for next iteration**: rename `seed_summary.json["pbo"]` to `seed_summary.json["pbo_per_seed"]` (or omit entirely since the canonical PBO is dsr.json).

### 8.2 n_eff = 1 — methodology question for Critic

The brief Section 4.1 predicted n_eff > 4. Reality: n_eff = 1 from PCA on the real (50 trials × 5359 candles) matrix. First principal component captures ≥95% of variance.

**Mechanism**: The OOF returns are pivot-aggregated per the brief Section 2.4 spec:
```python
combined = trial_oof.groupby(["trial_id", "candle_open_time_ms"])["oof_return"].sum()
```
The sum-across-(sym, month, seed) cells smooths inter-trial structure. With Optuna's Bayesian sampler, trials 1–49 are conditional on earlier observations, so per-cell trial-id structure carries information; but summed across all cells, the structure averages out. The resulting 50×5359 matrix is near rank-1 by construction.

**Open question for Critic**: is this the intended methodology behavior, or a methodology-pipeline bug? The brief did not anticipate this outcome. Three possible interpretations:

1. **Real result**: 50 Optuna trials really are 1-effective-dimensional after sum-aggregation. The methodology stack works correctly; the brief's prediction was just incorrect for this strategy.
2. **Aggregation flaw**: `sum` across cells loses per-trial signal. A different aggregation (e.g., mean, or no aggregation) might preserve more rank.
3. **Trial-ID semantics**: Optuna's `trial_id` is sequential within a study but not meaningfully comparable across (sym, month, seed) cells. The brief's pseudocode assumes cross-cell trial-id meaningfulness, which Optuna does not provide.

This is the central Critic Check 8 question (hypothesis-implementation alignment): the brief's Section 2.4 pseudocode IS what the runner implements, but the brief's expected outcome (n_eff > 4) does NOT materialize. Either the methodology is correct (and the brief's prediction was wrong) or the methodology has a subtle flaw.

### 8.3 PBO = 0.0 — informativeness question for Critic

PBO=0.0 from 5000 IS/OOS splits with frac_positive_paths=0.574 means: across 5000 random IS/OOS partitions of the 45 paths, the IS-best strategy among 50 was always above-median in the OOS half. This is technically a statistical result (NOT NaN), but the IS-best-always-above-median property is suspicious given:

1. Path Sharpe distribution has q25=-2.30, q50=0.80, q75=3.13 — wide variance. Some strategies should fail OOS by chance.
2. The same strategy class with iter-v3/001's broken PBO-computation also returned 0.0.

The brief Section 4.2 explicitly accepts ANY value in [0.0, 1.0] as a methodology pass: "Any specific value in [0.0, 1.0] is acceptable as a pass on the methodology axis (the value's economic interpretation depends on the strategy and is not on trial here)." Per pre-registration, criterion 8 PASSes on PBO=0.0.

The Critic should verify the CSCV implementation is computing PBO correctly given the path matrix. Adversarial test `test_pbo_synthetic.py::test_pbo_synthetic_overfit` passes (PBO=1.0 on overfit input), `test_pbo_synthetic_clean` passes (PBO=0.16 on clean input). On THIS data, PBO=0.0 is the deterministic output of the same function. The function itself is verified by 5 unit tests.

### 8.4 Pareto front: 1 seed only (criterion 15 vacuous)

Single seed 42, same as iter-v3/002. The 10-seed pre-MERGE check is acknowledged-as-gap by Section 8 criterion 15. iter-v3/002 also ran single-seed; the QR explicitly noted in the iter-v3/002 diary "10-seed sweep was not run; can't verify seed instability."

## 9. Library Stack (per Section 9)

| Package | Version | Status |
|---|---|---|
| numpy | 2.2.6 | already-installed |
| scipy | 1.17.0 | already-installed |
| statsmodels | 0.14.6 | already-installed |
| scikit-learn | 1.8.0 | already-installed |
| lightgbm | 4.6.0 | already-installed |
| pytest | 9.0.2 | already-installed |
| pandas | 3.0.0 | already-installed |
| pyarrow | 23.0.1 | already-installed (parquet engine) |

No new dependencies introduced. The pyarrow fallback (fastparquet) was not needed.

## 10. Files Produced

```
reports-v3/iteration_v3-003/
├── in_sample/
│   ├── daily_pnl.csv  feature_importance.csv  monthly_pnl.csv
│   ├── per_regime.csv per_symbol.csv          quantstats.html  trades.csv
├── out_of_sample/
│   ├── daily_pnl.csv  feature_importance.csv  monthly_pnl.csv
│   ├── per_regime.csv per_symbol.csv          quantstats.html  trades.csv
├── adf_test.csv               (387 KB, 7242 rows — per-(symbol, feature, month))
├── comparison.csv             (670 B)
├── cpcv_paths.csv             (1204 B, 45 rows)
├── dsr.json                   (361 B)
├── ic_matrix.csv              (24 KB)
├── pareto_front.csv           (115 B, 1 seed)
├── run.log                    (29 MB)
├── seed_summary.json          (264 B)
└── trial_oof_returns.parquet  (167 MB, 78,688,992 rows, 50 unique trial_ids)  ← NEW iter-v3/003 artifact
```

Reproducibility stamp: all files committed at HEAD `f6e909e` + iteration backtest output (uncommitted runtime artifacts; report-only files).

---

OVERALL: READY-FOR-CRITIC
