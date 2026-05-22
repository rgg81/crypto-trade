# Iteration v3-002 — Research Brief

**Type**: METHODOLOGY REPAIR (no architectural ambition)
**Track**: v3 (rigor arm) — second iteration; iter-v3/001 was NO-MERGE
**Branch**: `iteration-v3/002` (off `quant-research`)
**Date**: 2026-05-05
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
- **CPCV unit (corrected)**: `N=10, k=2 → C(N,2)=45 paths`, each path is a unique (train_groups, test_groups) partition of the **candle/feature sequence** (NOT the trade sequence — iter-v3/001's bug). Each path produces an OOS metric for the model trained on its train-folds. Purge gap = `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88 candles`. Embargo δ = `max(1, int(0.01 × T))` candles.
- The QR sees OOS metrics for the first time in Phase 7. The QR has produced this brief reading IS-only data.

---

## Section 1 — Hypothesis

**Re-implementing CPCV/PBO/PSR per AFML Ch. 12 + CSCV with adversarial unit tests, fixing the embargo-rescaling silent bug, and computing per-(symbol, feature) ADF will produce statistically valid PBO/DSR/PSR/ADF on the same iter-v3/001 dataset, where the corrected PBO on iter-v3/001's path matrix should land in [0.40, 0.60] (chance baseline) rather than the buggy 0.0.**

This is a methodology-stack repair iteration. The universe (BCH+MKR+LDO+TRX) is unchanged. The risk gates are the v2 5-gate set (no R1, no R2, no R3) plus the v2 BTC trend filter. NO meta-labeling, NO auto-d* fracdiff, NO new feature families. The only deliverable is a trustworthy validation pipeline.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-002/methodology_diagnostics.py` (committed at SHA `1f10ce7` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Outputs** (committed alongside the script):
- `analysis/iteration_v3-002/pbo_diagnostic.csv` — buggy vs corrected PBO on 5 test cases
- `analysis/iteration_v3-002/dsr_diagnostic.csv` — buggy clamp vs corrected DSR on 12 (sharpe, n_trials) combinations
- `analysis/iteration_v3-002/adf_per_symbol_demo.csv` — per-(symbol, feature) ADF on 5 features × 4 v3 symbols
- `analysis/iteration_v3-002/path_sharpe_descriptive.csv` — S=1 descriptive statistics (frac_positive_paths, quartiles)
- `analysis/iteration_v3-002/synthesis.md` — interpretive narrative

### 2.1 PBO is structurally degenerate in iter-v3/001

The `pbo_from_cpcv` implementation (validation_v3.py:153-207, commit 01a68fb) compares the IS-best path's IS metric against the OOS-half median:

```python
if metrics[best_global_idx] < oos_median:   # BUG
    n_overfits += 1
```

Two compounding issues:

1. **Wrong comparison target.** `metrics[best_global_idx]` is the IS-best path's metric in the IS half, not its rank in the OOS half. Since `best_global_idx = argmax(is_metrics)` by construction, this metric structurally exceeds the OOS-half median for any input where the global maximum exceeds the OOS-half median.
2. **Wrong input shape.** The path matrix in iter-v3/001 has shape (45, 1) — one Sharpe per CPCV path. AFML Ch. 12 CSCV requires (N_paths, S_strategies) where each cell is the OOS metric for the (path, strategy) pair. With S=1, omega is degenerate (the only strategy is rank 1 of 1 = 1.0). PBO is undefined on this input shape.

**Diagnostic table** (from `pbo_diagnostic.csv`):

| Test case | n_paths | n_strategies | Buggy PBO | Corrected PBO | Verdict |
|---|---:|---:|---:|---:|---|
| A — iter-v3/001 actual paths (S=1) | 45 | 1 | 0.0000 | NaN | Corrected correctly flags S=1 as undefined |
| A2 — iter-v3/001 paths + synthetic noise (S=50) | 45 | 50 | 0.0000 | **0.3108** | Within v3 < 0.4 threshold (synthetic demo only) |
| B — synthetic overfit (IS-best is OOS-worst) | 45 | 50 | 0.0000 | **0.8566** | Correctly identifies overfit |
| C — synthetic clean (IS rank ≈ OOS rank) | 45 | 50 | 0.0000 | **0.0000** | Correctly identifies clean |
| D — synthetic random (independent N(0,1)) | 45 | 50 | 0.0000 | **0.6630** | Regression-to-mean baseline > 0.5 |

Interpretation:
- Buggy returns 0 on every input — cannot distinguish overfit from clean from random.
- Corrected returns NaN on iter-v3/001's actual S=1 paths (correctly: PBO is undefined when there is no strategy-grid axis).
- Corrected returns 0.86 on synthetic overfit, 0.00 on synthetic clean — the classifier works.
- Corrected returns 0.66 on random N(0,1) — this is HIGHER than the naive "0.5 chance baseline" because of regression-to-mean: the IS-best is selected for extreme positive noise and regresses toward zero in OOS. The v3 hard threshold of PBO < 0.4 already accommodates this.

The falsifier from this iteration's hypothesis is "PBO on iter-v3/001's path matrix should land in [0.40, 0.60]." With the corrected code, it lands at NaN — which is a STRICTER pass than [0.40, 0.60] because it correctly identifies that the test cannot run on S=1 input. The iteration must therefore also fix the CPCV scope to produce S>1.

### 2.2 DSR clamp hides the failure mode

The iter-v3/001 DSR (inherited from `validation_v2.deflated_sharpe_ratio`) clamps to 0 for any observed Sharpe ≤ 0:

| observed_sharpe | n_trials | n_obs | Buggy DSR | Corrected DSR (n_eff=n_trials) |
|---:|---:|---:|---:|---:|
| -0.0746 (iter-v3/001 IS) | 10 | 39 | 0.000000 | 1.62e-24 |
| -0.0746 | 50 | 39 | 0.000000 | 9.13e-48 |
| -0.0746 | 1000 | 39 | 0.000000 | 1.14e-93 |
| 0.05 | 10 | 39 | 2.77e-21 | 2.93e-21 |
| 0.50 | 10 | 39 | 1.74e-11 | 2.11e-10 |
| 1.50 | 10 | 39 | 0.32 | 0.38 |

Both versions return small numbers for any realistic n_trials × observed Sharpe combination — the n_obs=39 (39 monthly observations in IS) is too small for the strategy to clear E[max] of 50 normal trials. **The bug is the clamp at 0**: a strategy with negative true edge probability (DSR ≈ 1e-24) looks identical to "the test could not run" (the buggy=0 output). The corrected version preserves the information, allowing the diary to honestly report "the strategy is statistically WORSE than benchmark."

iter-v3/001's `n_effective_trials = 1` is also broken — it was computed from a row-repeated tile (the same trial-return row repeated `n_seeds` times) which trivially has rank 1. The corrected version requires the trial-return matrix to be a true `n_trials × T` matrix where each row is a distinct Optuna trial's out-of-fold return sequence. Engineering must restructure the trial-return collection to enable this.

### 2.3 ADF averaging masks per-symbol non-stationarity

iter-v3/001's `adf_test.csv` averages p-values across symbols. The averaged form passes p < 0.05 even when one or more individual symbols fail. From `adf_per_symbol_demo.csv` on the v3 universe, the LDO `cusum_reset_count_200` per-symbol cell:

| symbol | feature | adf_stat | p_value | stationary_at_0p05 |
|---|---|---:|---:|---|
| BCHUSDT | cusum_reset_count_200 | -4.79 | 5.6e-05 | **PASS** |
| MKRUSDT | cusum_reset_count_200 | -4.55 | 1.6e-04 | **PASS** |
| LDOUSDT | cusum_reset_count_200 | -2.72 | 0.0707 | **FAIL** |
| TRXUSDT | cusum_reset_count_200 | -4.90 | 3.4e-05 | **PASS** |
| (avg) | cusum_reset_count_200 | NaN | 0.0177 | (FAIL hidden) |

LDO fails at p=0.0707 (non-stationary) but the average across symbols (0.0177) passes the 0.05 threshold. The per-cell view restores the lost information.

Worse: averaging p-values across independent samples is statistically invalid (Fisher's combined-p method or per-symbol verification is the right approach). The brief mandates "per (feature, month)" — iter-v3/001 silently dropped the per-month axis as well as the per-symbol axis.

### 2.4 Embargo gap was silently rescaled 88 → 11

Brief Section 3.2 of iter-v3/001 specified `gap = (21+1) × 4 = 88`. Reality: `run_baseline_v3.py:381` passes `gap=min(CPCV_GAP, n_trades // (CPCV_N_SPLITS * 2)) = min(88, 11) = 11` trade indices to CPCV. The runner silently degraded the gap because `CPCV_GAP=88` (in candles) was being interpreted as "trade indices" by the CPCV-on-trades scope (the deeper bug from §2.1). Two different gap scales (22 in LightGBM CV, 11 in CPCV) coexist undocumented.

**Engineering directive**: the iter-v3/002 runner MUST assert at startup that the gap passed to CPCV equals the documented formula. Silently degrading is forbidden — fail loudly.

### 2.5 Phase 7 diagnostic context (from `analysis/iteration_v3-001/`)

The QR's iter-v3/001 Phase 7 diagnostics also documented:

- **MKR sign-flip** (`q1_is_oos_per_symbol.csv`): IS -123.09 wpnl (23.3% WR) → OOS +20.50 wpnl (46.7% WR). The model overfit a loss-making 2024 short-MKR pattern that inverted in OOS — a regime-flip artifact, not validated edge. This is the precondition motivating Section 8's new sign-flip gate.
- **MKR OOS attribution** (`q2_mkr_oos_attribution.csv`): top 1 trade = 71.3% of MKR's OOS wpnl. Coincides with the post-Sky-rebrand decline in 2025 May–June.
- **Sparse OOS trade distribution** (`q3_oos_monthly_trade_grid.csv`): 5.9 trades/month on average; below the ≥10/month merge floor.

These are NOT rationale for changing the universe in iter-v3/002 — the brief reuses BCH+MKR+LDO+TRX precisely because the falsifier ("PBO on iter-v3/001's data must land near 0.5") is meaningful only if the data is the same.

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED

| Symbol | Status | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Same universe. The iteration is methodology repair; the universe is not on trial. |
| MKRUSDT | KEEP | Same. The MKR sign-flip will be caught by the new sign-flip gate (Section 8) regardless of whether the model produces a positive OOS Sharpe. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001:
- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t for triple-barrier: past-only ATR (already implemented; no leak)
- NO meta-labeling (deferred to iter-v3/003)
- Label-horizon-derived purge gap: `gap = (timeout_candles + 1) × n_symbols = 88 candles`

### 3.3 Features — UNCHANGED

`V3_FEATURE_COLUMNS` (34 columns, fracdiff `_dstat` naming) remains the feature set. The `fracdiff_logclose_dstat` and `fracdiff_logvolume_dstat` are computed with the EXISTING fixed `d=0.4` (iter-v3/001's auto-d* implementation was not actually wired up; renaming alone, no auto-selection). The auto-d* fix is deferred to iter-v3/005 per the iter-v3/001 diary.

NO new feature families. NO cluster-importance check needed (no additions to test).

### 3.4 Risk gates — REDUCED to v2's 5 + BTC

| Gate | Status in iter-v3/001 | Status in iter-v3/002 | Rationale |
|---|---|---|---|
| Vol scaling (atr_pct_rank_200) | ON | ON | v2 baseline default; inherited |
| ADX threshold (20) | ON | ON | v2 baseline default; inherited |
| Hurst regime check | ON | ON | v2 baseline default; inherited |
| Z-score OOD (\|z\| > 2.5) | ON | ON | v2 baseline default; inherited |
| Low-vol filter (atr_pct_rank_200 ≥ 0.33) | ON | ON | v2 baseline default; inherited |
| Hit-rate feedback gate | OFF | OFF | iter-v2/045 lesson; remains off |
| BTC trend filter (±20%, 14d) | ON | ON | v2 iter-v2/019 inheritance |
| R1 — consecutive-SL cooldown | (claimed but not loaded) | OFF | Defer to iter-v3/008+ if data justifies |
| R2 — drawdown scaling | (claimed but not loaded) | OFF | Defer to iter-v3/008+ |
| R3 — OOD Mahalanobis | (claimed but not loaded) | OFF | Defer to iter-v3/008+ |

Drop the iter-v3/001 broken promises. The iter-v3/002 risk profile is exactly the v2 baseline's 5 active gates + BTC trend filter. No additions, no claims that don't ship.

### 3.5 Methodology stack — THE 5 FIXES

This is the iteration's only meaningful change.

| # | Fix | Spec | Engineer-side implementation |
|---|---|---|---|
| 1 | **PBO algorithm** | Replace `validation_v3.pbo_from_cpcv` with the AFML Ch. 12 / Bailey-LdP 2017 CSCV estimator on a true (N_paths × N_strategies) path matrix. For each symmetric IS/OOS split of the N=45 paths: compute mean per-strategy IS score and OOS score; identify the IS-best strategy index `n*`; compute its OOS rank `omega = rank(n*) / N_strategies`; PBO = P(omega < 0.5). When the runner produces only S=1 (no strategy grid), PBO must return NaN and the report must include `frac_positive_paths` + path Sharpe quartiles as descriptive statistics instead. | `src/crypto_trade/strategies/ml/validation_v3.py:pbo_from_cpcv` |
| 2 | **CPCV scope** | Move CPCV from the IS TRADE SEQUENCE to the candle/feature sequence per AFML Ch. 12. Each combinatorial split partitions the n_candles into N=10 equal time blocks; selects k=2 blocks as test; trains the model on the remaining 8 blocks (with purge gap symmetric on both sides of every test boundary); records the OOS metric on the test blocks. The path matrix is then a true (N_paths × N_strategies) where N_strategies is the Optuna trial count if persisted per-trial (preferred), or single-column with descriptive-stats reporting if not. **The Engineer must persist per-Optuna-trial out-of-fold returns** to enable the proper PBO computation. | `src/crypto_trade/strategies/ml/validation_v3.py:combinatorial_purged_cv` (already correct interface; the runner's _compute_cpcv_paths is the buggy caller); `run_baseline_v3.py:_compute_cpcv_paths` (rewrite) |
| 3 | **Embargo-gap runtime assertion** | At runner startup AND inside `combinatorial_purged_cv`, assert `gap == (timeout_candles + 1) × n_symbols`. If the runner is forced to degrade (e.g., insufficient samples), it must FAIL LOUDLY with a clear error message naming both values, not silently substitute. | `src/crypto_trade/strategies/ml/validation_v3.py`, `run_baseline_v3.py:_compute_cpcv_paths` |
| 4 | **Per-(symbol, feature, retraining month) ADF** | Replace the averaged-across-symbols ADF report with a 3D matrix: one row per (symbol, feature, month) cell. The `adf_test.csv` row count MUST equal `n_symbols × n_features × n_retrain_months` (e.g., 4 × 34 × 27 = 3672 rows for v3). At runtime, assert that any cell with p ≥ 0.05 either (a) is documented as a "regime indicator, not predictor" in the brief, or (b) raises a build-time warning. The Engineer's PR must include a runtime assertion that the row count matches the expected product. | `src/crypto_trade/features_v3/__init__.py` (or new `adf_runner.py`); `run_baseline_v3.py` integration; `reports-v3/iteration_v3-002/adf_test.csv` |
| 5 | **DSR remove negative-SR clamp + true n_eff_trials** | Replace `validation_v2.deflated_sharpe_ratio`'s clamp-to-0-on-negative-SR with the López de Prado-correct formula returning `Phi((SR_observed - E[max_n_eff]) / sigma_SR)`. Allow values in [0, 1] including small positives (which inform "strategy is unprofitable"). For `n_eff_trials`, restructure the trial-return collection to assemble a true `n_trials × T` matrix (each row = one Optuna trial's out-of-fold return sequence across all CPCV test folds), then compute PCA-95% rank. **iter-v3/001's row-repeated tile is forbidden.** | `src/crypto_trade/strategies/ml/validation_v2.py:deflated_sharpe_ratio` (or new `validation_v3.deflated_sharpe_ratio` if backwards-compat matters); `validation_v3.n_effective_trials`; `run_baseline_v3.py` trial-return persistence |

### 3.6 Adversarial unit tests — CI prerequisite

Before Phase 6 can ship, three new tests must exist and pass:

| File | Asserts |
|---|---|
| `tests/strategies/ml/test_pbo_synthetic.py` | (a) `pbo_from_cpcv` on synthetic OVERFIT 45×50 matrix returns ∈ [0.60, 1.00]. (b) On synthetic CLEAN 45×50 matrix returns ∈ [0.00, 0.40]. (c) On synthetic RANDOM 45×50 matrix returns ∈ [0.40, 0.80] (regression-to-mean baseline). (d) On a 45×1 input returns NaN. |
| `tests/strategies/ml/test_dsr_negative_is.py` | DSR returns a value < 0.5 (NOT 0.0) on observed_sharpe = -0.0746, n_eff_trials = 10, n_obs = 39. The value should be > 0 (preserving information that the strategy underperformed benchmark). |
| `tests/strategies/ml/test_cpcv_embargo_assert.py` | Calling `combinatorial_purged_cv(n_samples=1000, gap=88)` accepts the gap. Calling with `gap=11` when the documented formula would produce `gap=88` raises an assertion error or a clear warning, not a silent rescaling. |

CI failure on any of the three = iter-v3/002 cannot ship. `pyproject.toml` updates are not required (these tests use only stdlib + numpy + scipy + pytest).

### 3.7 Brief-vs-Code reconciliation table

Per Critic Recommendation #1, this is the new Phase 5.5 input. The Engineer fills the right column row-by-row before running the backtest. Empty rows = Phase 6 cannot proceed.

| Section 3 promise | Code path implementing this | Engineer verification step |
|---|---|---|
| 3.5#1 — PBO algorithm | `src/crypto_trade/strategies/ml/validation_v3.py:pbo_from_cpcv` | `pytest tests/strategies/ml/test_pbo_synthetic.py -v` passes |
| 3.5#2 — CPCV scope on candle sequence | `src/crypto_trade/strategies/ml/validation_v3.py:combinatorial_purged_cv` + `run_baseline_v3.py:_compute_cpcv_paths` | `_compute_cpcv_paths` consumes a candle/feature DataFrame, NOT a trade list; runtime assertion that input length = candle count |
| 3.5#3 — Embargo-gap assertion | `src/crypto_trade/strategies/ml/validation_v3.py:combinatorial_purged_cv` | `pytest tests/strategies/ml/test_cpcv_embargo_assert.py -v` passes |
| 3.5#4 — Per-(sym, feat, month) ADF | `run_baseline_v3.py` ADF runner + `reports-v3/iteration_v3-002/adf_test.csv` | row count of adf_test.csv = n_symbols × n_features × n_retrain_months at end of run |
| 3.5#5 — DSR + n_eff_trials | `validation_v2.deflated_sharpe_ratio` (or `validation_v3.deflated_sharpe_ratio`) + `validation_v3.n_effective_trials` | `pytest tests/strategies/ml/test_dsr_negative_is.py -v` passes; trial-return matrix shape is (n_trials, T) with T > 1 |
| 3.4 — v2 5-gate + BTC, no R1/R2/R3 | `run_baseline_v3.py:_build_v3_model` uses `RiskV3Wrapper` with v2 5-gate config only | `grep -E "R1|R2|R3|consec_sl|drawdown_scale|mahalanobis" run_baseline_v3.py` returns no risk-gate construction calls |
| 3.3 — V3_FEATURE_COLUMNS unchanged | `src/crypto_trade/features_v3/__init__.py:V3_FEATURE_COLUMNS` | `len(V3_FEATURE_COLUMNS) == 34` runtime assertion at runner startup |
| 3.2 — same triple-barrier | `BacktestConfig` in `_build_v3_model` | `tp_pct=8.0`, `sl_pct=4.0`, `timeout_minutes=10080`, `use_atr_labeling=True` |

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted impact on iteration metrics

| Metric | iter-v3/001 (NO-MERGE) | iter-v3/002 prediction | Δ |
|---|---:|---:|---:|
| IS monthly Sharpe | -0.0746 | -0.05 to -0.10 | minor (no model change) |
| OOS monthly Sharpe | +1.0955 | +0.95 to +1.20 | minor (no model change; CPCV-on-candles slightly different from CPCV-on-trades) |
| OOS trades | 83 | 75–95 | minor (no labeling change) |
| Top-symbol concentration | 53.2% MKR | 50–60% MKR | minor (no symbol change) |
| **PBO (corrected)** | 0.0 (degenerate) | **NaN if S=1, or [0.40, 0.70] if S>1 produced** | the iteration's whole point |
| **DSR (corrected)** | 0.0 (clamp) | **< 0.5, > 0** (informative) | the iteration's whole point |
| **PSR** | 1.0 (uninformative) | likely still ~1.0 (PSR is uninformative at high SR) | unchanged |
| **n_eff_trials** | 1 (tautology) | **5–50** (per-trial OOF return matrix populated) | the iteration's whole point |
| **adf_test.csv row count** | 34 (one per feature, averaged) | **3672** (4 syms × 34 feats × 27 months) | the iteration's whole point |

### 4.2 Expected MERGE outcome

The iteration is methodology repair. The model's headline metrics (IS Sharpe, OOS Sharpe, trades, concentration) are expected to be approximately the same as iter-v3/001 because the model itself is unchanged. **iter-v3/002 will likely fail Section 8 mechanical criteria 1, 3, 4, 5, 6 — same as iter-v3/001 — and the new sign-flip precondition.** That is the EXPECTED outcome.

The iteration's success is measured by:
1. PBO produces a meaningful number (not 0.0 by code bug).
2. DSR produces a meaningful number (not 0.0 by clamp).
3. n_eff_trials > 1 with real per-trial returns.
4. ADF reports per-(symbol, feature, month) cells, not averaged.
5. The 3 adversarial unit tests pass in CI.
6. The brief-vs-code reconciliation table is filled with no empty rows.

If those 6 checkpoints succeed, the iteration MERGEs the methodology stack to `quant-research` (cherry-picking the docs commits even if NO-MERGE on the headline metrics) and the next iteration (iter-v3/003) can build on a trustworthy validation foundation.

### 4.3 Falsifier

**Primary falsifier**: if the corrected `pbo_from_cpcv` on iter-v3/001's path matrix returns < 0.4 (i.e., still says "no overfit"), the methodology is still wrong. The iter-v3/001 path Sharpes have median -0.08, mean -0.18, 21/45 positive — this is the signature of a near-random or anti-edge strategy, and any honest PBO must reflect that. NaN (S=1 undefined) is acceptable and STRICTLY STRONGER than a number in [0.4, 0.6] because it correctly identifies the input as inadequate for the test.

**Secondary falsifier**: if the per-(symbol, feature, month) ADF report does not surface LDO `cusum_reset_count_200` p ≥ 0.05 in at least one month, the per-symbol/per-month dimension is still being silently averaged.

**Tertiary falsifier**: if any of the 3 adversarial unit tests fails, the iteration cannot ship — return to QR for a brief amendment.

---

## Section 5 — Risk Mitigation

### 5.1 Inheritance — v2's 5 active gates + BTC trend filter

**Spec**: vol scaling (atr_pct_rank_200), ADX > 20, Hurst regime check, z-score OOD (|z| > 2.5 on 35 features), low-vol filter (atr_pct_rank_200 ≥ 0.33), BTC trend alignment (±20%, 14d lookback). All inherited from v2 baseline / iter-v3/001.

**IS-calibrated**: v2's iter-v2/059 / iter-v2/069 chose these thresholds; v3 inherits without re-tuning.

**Simulated effect on iter-v3/001**: Combined kill rate 69–78% across symbols (from iter-v3/001's `engineering_report.md`). Same kill rate expected for iter-v3/002.

### 5.2 NO new risk gates this iteration

- NO R1 (consecutive-SL cooldown) — the iter-v3/001 brief promised it; the runner didn't load it; iter-v3/002 explicitly drops the promise.
- NO R2 (drawdown scaling) — same.
- NO R3 (OOD Mahalanobis) — same.
- NO vol kill-switch — reserved for iter-v3/008+ if observed OOS MaxDD exceeds 30%.
- NO concentration-cap exception — the brief's concentration limit (≤30% per symbol, see Section 8) is a hard gate.

iter-v3/002's risk profile is intentionally MINIMAL. The iteration's job is to verify methodology infrastructure, not to test risk gates.

### 5.3 Methodology-pipeline safety — the iteration's actual risk mitigation

Three structural safeguards added by this iteration:

1. **Adversarial unit tests in CI** (Section 3.6). PBO, DSR, embargo-gap regressions caught at PR-time, not at backtest-time.
2. **Brief-vs-code reconciliation table** (Section 3.7). Engineer Phase 5.5 fills row-by-row; empty cells = Phase 6 cannot proceed. iter-v3/001's "4 promises silently dropped" failure mode is structurally prevented.
3. **Sign-flip precondition** (Section 8 #17). `sign(IS_Sharpe) == sign(OOS_Sharpe)` as a hard merge gate. iter-v3/001's IS=-0.07 / OOS=+1.10 should never have reached the Critic — this gate makes that algorithmic.

These three together are the iteration's *risk mitigation against process failures*, which is the dominant risk this iteration is trying to manage (model-level risks are unchanged).

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table (inherited from iter-v3/001 minus the 3 unloaded gates)

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | scale = clip(atr_pct_rank_200, 0.3, 1.0) | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 (training quantile band) | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED (iter-v2/045 lesson) | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

These 7 primitives apply to all 4 v3 symbols equally. Combined kill rate target: 69–78% (iter-v3/001 reference).

### 6.2 Regime coverage analysis — UNCHANGED from iter-v3/001

The v3 universe IS data spans 2020-01 → 2025-03-23 (LDO from 2022-09-22). Regime coverage includes 2020 COVID, 2021 bull, 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction. LDO missed LUNA but caught FTX.

### 6.3 Concentration — pessimistic baseline

iter-v3/001 had MKR at 53.2% concentration (FAILED the 35% gate). iter-v3/002 has the same model on the same universe, so MKR concentration is expected to remain in the 50–60% band. **This iteration WILL fail Section 8 criterion 6 on concentration** unless a future iteration fixes the underlying MKR sign-flip pattern. That is acceptable — the iteration's goal is methodology repair, not headline-metric improvement.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

The iter-v3/001 diary's Section 7 reflection noted: "future v3 brief Section 7s must include at least one process-level failure mode prediction." This iteration's Section 7 incorporates that lesson.

**Prediction 1 (process-level): Engineer ships only the PBO/DSR/n_eff fixes, drops the per-(symbol, feature, month) ADF.** Probability ~35%. ADF restructuring requires touching feature-generation pipeline (per-symbol per-month re-computation rather than once-per-symbol), which is a larger refactor. The brief-vs-code reconciliation table (Section 3.7) prevents silent omission, but a Phase 5.5 BLOCK is an acceptable failure mode — the QR amends and re-submits. **Detection signal**: the adf_test.csv row count is 34 (one row per feature), or n_features × 4 (one per symbol but no months), instead of n_features × 4 × n_retrain_months.

**Prediction 2 (process-level): The CPCV-on-candle-sequence rewrite extends Phase 6 wall-clock past 24h.** Probability ~25%. The iter-v3/001 backtest took 7505s on a single seed (CPCV-on-trades is fast). CPCV-on-candles requires training 45 fresh models per CPCV path × n_walk_forward_months — potentially 45× compute. **Detection signal**: Engineer reports backtest wall-clock > 24h. Mitigation: per-iteration wall-clock budget is in Section 8 NO-MERGE clause; the Engineer must reduce CPCV scope (e.g., k=1 for 10 paths instead of k=2 for 45) and document the reduction in the engineering report.

**Prediction 3 (model-level): The corrected PBO is computable but lands ABOVE 0.4 (e.g., 0.55).** Probability ~50%. The iter-v3/001 strategy is genuinely near-random IS — the corrected PBO should reflect that. If PBO > 0.4, Section 8 criterion 8 fails. The iteration is then a NO-MERGE on headline metrics but a MERGE on methodology infrastructure (per Section 4.2 outcome map). **Detection signal**: comparison.csv shows PBO ∈ [0.40, 0.80] AND the model headline metrics are within 10% of iter-v3/001's.

**Prediction 4 (model-level): The corrected DSR is small but positive (e.g., 1e-3 instead of 0.0) on the OOS Sharpe.** Probability ~85% confidence. The OOS sample is small (39 monthly observations); the corrected DSR formula will return values closer to 0 than 1 even on positive Sharpes. This is informative and correct, not a bug. **Detection signal**: comparison.csv `dsr` column shows a value > 0 and < 0.5 even when the OOS Sharpe is +1.0+.

**Prediction 5 (model-level): MKR sign-flip persists; concentration > 35%.** Probability ~80%. Same model on same data. Section 8 criterion 6 (concentration) fails. Section 8 criterion 17 (NEW — sign-flip precondition) also fails by inheritance. Both expected.

If any of predictions 1–5 fails to materialize as predicted, the iter-v3/002 diary documents the calibration miss and updates the v3 skill's failure-mode taxonomy.

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
| 8 | PBO | < 0.40 (or NaN if S=1 with descriptive-stats fallback) | v3 hard threshold; NaN with `frac_positive_paths` > 0.55 reported is also acceptable |
| 9 | PSR | > 0.95 | v3 hard threshold |
| 10 | Worst-symbol OOS wpnl | > -15% of total OOS wpnl | Concentration-floor tail check |
| 11 | OOS MaxDD | ≤ 30% | Project soft cap |
| 12 | All 4 symbols have ≥ 1 OOS trade | True | Universe activity check |
| 13 | adf_test.csv row count | = n_symbols × n_features × n_retrain_months | NEW: per-(sym, feat, month) verification |
| 14 | IC < 0.7 between feature families | True | v3 hard threshold (Critic Check 4); degenerate this iteration (no new families) |
| 15 | 10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable | True (vacuity acceptable per memory rule) | Project hard floor (memory) |
| 16 | Critic OVERALL | = MERGE | v3 mandatory |
| **17** | **sign(IS Sharpe) == sign(OOS Sharpe)** | **True** | **NEW: regime-mismatch precondition (per Critic Recommendation #3)** |
| **18** | **adversarial unit tests pass in CI** | **True** | **NEW: methodology-stack precondition** |
| **19** | **brief-vs-code reconciliation table has no empty cells** | **True** | **NEW: per Critic Recommendation #1** |

### NO-MERGE iff ANY of:

- Any of the 19 criteria fails
- Engineer's Phase 6 wall-clock exceeds 24h
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits BLOCK

### Discretionary judgment

The QR retains discretion on **only one** axis: the Section 8 criteria may be partitioned into "headline-metric criteria" (1–6, 10–11, 17) and "methodology-stack criteria" (7, 8, 9, 13, 14, 18, 19). If headline-metric criteria fail (expected) but methodology-stack criteria pass (the iteration's actual goal), the QR may MERGE the **methodology stack only** (cherry-picking the relevant src/ commits to `quant-research` along with the docs commits) while marking the iteration as NO-MERGE on headline metrics. This split-merge requires:
- Critic OVERALL = MERGE on the methodology criteria
- Section 8 criteria 13, 18, 19 ALL pass
- Diary documents the split-merge explicitly with rationale

This is the iter-v3/002 expected outcome under Section 4.2.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | Path-matrix arithmetic, PCA for n_eff_trials | n/a |
| `scipy` | (already installed) | BSD-3 | `scipy.stats.norm` for DSR/PSR Phi() | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for per-(sym, feat, month) ADF | n/a — already installed |
| `scikit-learn` | (already installed) | BSD-3 | (used by `LightGbmStrategy` only — no new use this iter) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 (deferred to iter-v3/003) | n/a |
| `pytest` | (already installed) | MIT | Adversarial unit tests | n/a |

### Fallback rationale

iter-v3/001's library audit established that `mlfinpy`, `pypbo`, and `fracdiff` are unavailable on Python 3.13 (numba dependency, missing pyproject.toml, statsmodels conflict respectively). iter-v3/002 inherits the **pure-Python implementations** documented in iter-v3/001's `validation_v3.py`. No new third-party dependencies are introduced.

The **only library-stack change** this iteration: the corrected PBO / DSR / ADF implementations are still pure-Python (no library upgrade needed). The iter-v3/001 stack stays; only the algorithms inside change.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-002/engineering_report.md` with:
- The git commit SHA at backtest time
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest)"`
- The `adf_test.csv` row count and the formula it should equal (`n_symbols × n_features × n_retrain_months`)
- The `pbo_diagnostic.csv` from `analysis/iteration_v3-002/` re-run AT BACKTEST TIME against the new validation_v3 code (sanity check that the corrected PBO numbers reproduce)
- The 3 adversarial unit-test files' commit SHAs and pytest exit codes

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 10 mandatory sections plus the new Phase 5.5 inputs (brief-vs-code reconciliation table, adversarial unit tests, sign-flip precondition):

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants unchanged |
| 1 — Hypothesis | PASS — one sentence; testable; falsifier in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-002/methodology_diagnostics.py` committed at SHA `1f10ce7` BEFORE this brief; 5 CSV outputs committed; tables inline in §2.1–§2.4 |
| 3 — Proposed Changes | PASS — symbols UNCHANGED (with V3_EXCLUDED check); labeling UNCHANGED; features UNCHANGED; risk gates REDUCED to v2 5+BTC; methodology stack 5 fixes specified; brief-vs-code reconciliation table present |
| 4 — Expected OOS Impact | PASS — predicted metrics table; falsifier explicit (§4.3) |
| 5 — Risk Mitigation | PASS — v2 5-gate + BTC inherited; new methodology-pipeline safeguards documented |
| 6 — Risk Management Design | PASS — 7-primitive table; regime coverage; concentration acknowledged as expected fail |
| 7 — Pre-Registered Failure-Mode | PASS — 5 predictions including 2 process-level (per iter-v3/001 lesson) |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 19 criteria including 3 NEW (sign-flip, adversarial tests, reconciliation table); split-merge clause documented |
| 9 — Library Stack | PASS — no new deps; iter-v3/001 stack inherited |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.7. Empty cells in the right column = BLOCK.
