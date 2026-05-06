# Iteration v3-007 — Research Brief

**Type**: EXPLORATION (FIRST exploration-mode iteration in v3 history; first iteration under the new Iteration Type Declaration skill at SHA `f0f8b84`)
**Track**: v3 (rigor arm) — seventh iteration; iter-v3/001-006 all NO-MERGE
**Branch**: `iteration-v3/007` (off `iteration-v3/006` head; one new code commit at SHA `bce50c8` adds the `--exploration` flag; one analysis commit at SHA `a394314` ships the Phase 1 evidence)
**Date**: 2026-05-06
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration (override of default 5)
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
                                  # single inner seed per outer seed,
                                  # derived from numpy.random.default_rng(outer_seed)
n_trials         = 10             # SET BY --exploration default
colsample_bytree = 1.0            # HARDCODED by --exploration --fast_mode flag
                                  # (every tree split sees ALL features)
OOS_CUTOFF_MS    = 1742774400000  # millisecond representation for IS-only filtering
```

- **Sacred constants UNCHANGED**: `OOS_CUTOFF_DATE`, `training_months`. The `--exploration` flag at SHA `bce50c8` does NOT touch either.
- **IS window**: from each symbol's first usable kline (with the listing-date floor 2022-09-24) through `2025-03-23 23:59:59 UTC` exclusive.
- **OOS window**: from `2025-03-24 00:00:00 UTC` through the data-extent timestamp at backtest time.
- **Walk-forward unit**: monthly retrain, 24-month rolling training window, 1-month OOS prediction window — UNCHANGED.
- The QR sees OOS metrics for the first time in Phase 7. This brief is produced reading ONLY: SHA `bce50c8` (`run_baseline_v3.py` `--exploration` flag), SHA `f0f8b84` (skill update with Section 0.5 spec), SHA `a394314` (Phase 1 analysis script + outputs), the iter-v3/006 brief / engineering report / Critic review / diary, and `reports-v3/iteration_v3-006/in_sample/feature_importance.csv` + `reports-v3/iteration_v3-003/in_sample/feature_importance.csv`.

---

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION**

**Justification**: Per user direction 2026-05-06, iter-v3/007 is the FIRST EXPLORATION iteration in v3 history. It tests the new `--exploration` mode (colsample=1.0, ENSEMBLE_SIZE=1, n_trials=10, ~25-30x faster than production) on a feature variation hypothesis (top-14 of 34 features chosen by mean importance rank). Goal: find a configuration with IS Sharpe > +0.5 using a cheap config (~30-60 min wall-clock) BEFORE committing to expensive CONFIRMATION runs. Per skill spec at SHA `f0f8b84`, Critic scores Checks 1, 2, 4, 5, 6, 8 with full enforcement; Check 3 edge axis (DSR/PSR) is informational only, NOT BLOCK-triggering for this TYPE. Critic emits `EXPLORATION-PROMISING` (signal found, propose CONFIRMATION iter-v3/008) or `EXPLORATION-NEGATIVE` (no signal, propose next-axis iter-v3/008).

---

## Section 1 — Hypothesis

Reducing `V3_FEATURE_COLUMNS` from 34 to the top-14 by mean importance rank across iter-v3/006 (BCH-only seed=42 n_trials=10) and iter-v3/003 (full 4-symbol universe seed=42 n_trials=50), running on the full v3 universe (BCH+MKR+LDO+TRX) with `--exploration` (colsample=1.0, ENSEMBLE_SIZE=1, n_trials=10), will produce IS monthly Sharpe > +0.5 (vs iter-v3/006's BCH-only single-seed IS Sharpe = +0.4051 and iter-v3/003's full-universe single-seed IS Sharpe = -0.0746) by removing features that contribute near-zero gain on TWO independent IS runs and therefore dilute the LightGBM training signal — under colsample=1.0, every tree split sees all features, so low-importance features waste a constant fraction of every node's gain estimate.

---

## Section 2 — IS-Only Numerical Evidence

**Analysis script**: `analysis/iteration_v3-007/feature_importance_topN_demo.py` (committed at SHA `a394314` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read**:
- `reports-v3/iteration_v3-006/in_sample/feature_importance.csv` — BCH-only, seed=42, n_trials=10, V3_FEATURE_COLUMNS (34 cols).
- `reports-v3/iteration_v3-003/in_sample/feature_importance.csv` — full 4-symbol universe (BCH+MKR+LDO+TRX), seed=42, n_trials=50, V3_FEATURE_COLUMNS (34 cols).

Both source CSVs are computed inside the walk-forward training loop on candles with `close_time < OOS_CUTOFF_DATE = 2025-03-24`. No OOS contact at any step of this analysis. Pure ranking + selection on existing committed reports.

**Outputs** (all committed alongside the script at SHA `a394314`):
- `analysis/iteration_v3-007/top_n_features.csv` — 34 rows × 12 columns (feature, mean_rank, rank_006, rank_003, imp_006, imp_003, near_zero flags, in_top_N flags)
- `analysis/iteration_v3-007/summary.json` — chosen N=14, selected features list, dropped features list, alternative N=10 + N=20 lists
- `analysis/iteration_v3-007/synthesis.md` — interpretive narrative

### 2.1 Top-14 features (selected for `V3_FEATURE_COLUMNS_TOP_N`)

Sorted by mean rank (ascending = best). Lower rank = more important.

| rank | feature | rank_006 | rank_003 | imp_006 | imp_003 |
|---:|---|---:|---:|---:|---:|
| 1 | `max_dd_window_50` | 4 | 1 | 128.4 | 113.2 |
| 2 | `vwap_dev_50` | 2 | 3 | 136.2 | 101.8 |
| 3 | `ema_spread_atr_20` | 1 | 5 | 151.0 | 84.0 |
| 4 | `ret_kurt_50` | 6 | 4 | 126.2 | 86.8 |
| 5 | `ret_skew_200` | 8 | 2 | 117.4 | 105.8 |
| 6 | `range_realized_vol_50` | 7 | 6 | 124.0 | 82.2 |
| 7 | `hurst_diff_100_50` | 3 | 20 | 134.0 | 41.2 |
| 8 | `ret_kurt_200` | 14 | 9 | 107.0 | 69.8 |
| 9 | `hurst_100` | 12 | 11 | 108.8 | 64.6 |
| 10 | `btc_ret_14d` | 13 | 12 | 107.4 | 63.4 |
| 11 | `ret_skew_50` | 10 | 15 | 112.8 | 50.2 |
| 12 | `vwap_dev_20` | 5 | 21 | 127.8 | 40.4 |
| 13 | `ret_autocorr_lag1_50` | 20 | 7 | 98.2 | 80.0 |
| 14 | `sym_vs_btc_ret_7d` | 16 | 13 | 106.0 | 60.4 |

Group coverage of the top-14:
- regime: 2 (`hurst_diff_100_50`, `hurst_100`)
- tail_risk: 6 (`max_dd_window_50`, `ret_skew_200`, `ret_skew_50`, `ret_kurt_50`, `ret_kurt_200`, `range_realized_vol_50`)
- momentum_accel: 3 (`ema_spread_atr_20`, `ret_autocorr_lag1_50`, ... — `ret_autocorr_lag5_50` dropped)
- volume_micro: 2 (`vwap_dev_50`, `vwap_dev_20`)
- cross_btc: 2 (`btc_ret_14d`, `sym_vs_btc_ret_7d`)
- price_efficient_vol: 0 (BOTH `parkinson_vol_20` and `parkinson_gk_ratio_20` drop out)
- fracdiff: 0 (BOTH `fracdiff_logclose_dstat` and `fracdiff_logvolume_dstat` drop out)
- microstructure_v3: 0 (`hl_range_ratio_20` drops; the entire group's only feature is dropped)

The top-14 spans 5 of the 8 v3 feature groups. Three groups are completely removed: price_efficient_vol, fracdiff, microstructure_v3.

### 2.2 Dropped 20 features (rank > 14)

| rank | feature | rank_006 | rank_003 | imp_006 | imp_003 | near_zero_count |
|---:|---|---:|---:|---:|---:|---:|
| 15 | `volume_cv_50` | 19 | 10 | 104.6 | 69.2 | 0 |
| 16 | `fracdiff_logclose_dstat` | 11 | 19 | 112.8 | 43.2 | 0 |
| 17 | `parkinson_gk_ratio_20` | 9 | 22 | 116.0 | 38.2 | 0 |
| 18 | `obv_slope_50` | 18 | 14 | 104.8 | 51.2 | 0 |
| 19 | `volume_mom_ratio_20` | 24 | 8 | 85.2 | 71.8 | 0 |
| 20 | `mom_accel_20_100` | 17 | 18 | 105.2 | 47.2 | 0 |
| 21 | `btc_vol_14d` | 21 | 16 | 91.8 | 49.8 | 0 |
| 22 | `ret_autocorr_lag5_50` | 15 | 23 | 106.8 | 36.0 | 0 |
| 23 | `ret_skew_100` | 25 | 17 | 82.0 | 49.6 | 0 |
| 24 | `hurst_200` | 22 | 26 | 88.8 | 17.6 | 0 |
| 25 | `bb_width_pct_rank_100` | 26 | 25 | 80.2 | 18.4 | 0 |
| 26 | `btc_ret_7d` | 23 | 29 | 87.0 | 13.6 | 0 |
| 27 | `parkinson_vol_20` | 30 | 24 | 71.0 | 18.6 | 0 |
| 28 | `btc_ret_3d` | 28 | 28 | 74.8 | 13.6 | 0 |
| 29 | `fracdiff_logvolume_dstat` | 27 | 33 | 77.4 | 3.2 | 1 |
| 30 | `cusum_reset_count_200` | 34 | 27 | 37.6 | 14.2 | 0 |
| 31 | `hl_range_ratio_20` | 29 | 34 | 73.2 | 2.8 | 1 |
| 32 | `atr_pct_rank_500` | 32 | 31 | 47.2 | 12.0 | 0 |
| 33 | `mom_accel_5_20` | 31 | 32 | 69.6 | 11.0 | 0 |
| 34 | `atr_pct_rank_200` | 33 | 30 | 44.2 | 12.4 | 0 |

Two features (`fracdiff_logvolume_dstat`, `hl_range_ratio_20`) are near-zero in iter-v3/003 (imp_003 < 5% of run max). The remaining 18 are not near-zero in either run individually but rank consistently low.

### 2.3 Selection criterion summary

- Heuristic: mean rank across two independent IS runs (BCH-only n_trials=10 and full-universe n_trials=50). Lower rank = more important.
- Natural break at rank 14: the rank-15 feature (`volume_cv_50`) ranks 10 in iter-v3/003 (top-third) but 19 in iter-v3/006 (bottom-half), suggesting it is universe-dependent rather than universally signal-bearing. The rank-14 feature (`sym_vs_btc_ret_7d`) ranks 13 and 16 — symmetric. The break is methodologically defensible.
- Alternative N=10 would drop `ret_skew_50`, `vwap_dev_20`, `ret_autocorr_lag1_50`, `sym_vs_btc_ret_7d`, all of which are top-15 in at least one run. Top-14 is more conservative.
- Alternative N=20 would re-introduce 6 features (`volume_cv_50`, `fracdiff_logclose_dstat`, `parkinson_gk_ratio_20`, `obv_slope_50`, `volume_mom_ratio_20`, `mom_accel_20_100`) with mixed evidence. Less defensible than N=14.

### 2.4 Implication for Phase 6

Replacing `V3_FEATURE_COLUMNS` (34 features) with the 14-feature subset above is a single, atomic, value-aligned change. Combined with `--exploration` mode, this is the cheapest possible test of "does removing the bottom-20 features improve IS Sharpe?". A negative result (IS Sharpe < +0.4) is informative — it means the bottom-20 features carry meaningful (if individually small) signal, and CONFIRMATION should test a different feature axis (e.g., feature ADDITIONS, not subsetting). A positive result (IS Sharpe > +0.5) triggers iter-v3/008 CONFIRMATION at full ensemble + n_trials=50.

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (full v3 universe)

| Symbol | Status (iter-v3/007) | Rationale |
|---|---|---|
| BCHUSDT | KEEP | Full v3 universe per user direction "use all dataset". |
| MKRUSDT | KEEP | Same. |
| LDOUSDT | KEEP | Same. |
| TRXUSDT | KEEP | Same. |

`set({BCH, MKR, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED

Inherited from iter-v3/001-006:
- Triple-barrier with ATR-scaled barriers: `tp = 2.9 × NATR_21`, `sl = 1.45 × NATR_21`
- Timeout: 7 days = 21 candles at 8h
- σ_t for triple-barrier: past-only ATR (no leak)
- Label-horizon-derived purge gap: `gap = (timeout_candles + 1) × n_symbols = 22 × 4 = 88`. With full universe (`n_symbols=4`), `REQUIRED_GAP=88` is the existing constant — UNCHANGED.

### 3.3 Features — REDUCED from 34 to 14

The feature set used by Phase 6 backtest:

```python
V3_FEATURE_COLUMNS_TOP_N = (
    # Top 14 by mean rank across iter-v3/003 + iter-v3/006 IS feature_importance
    "max_dd_window_50",
    "vwap_dev_50",
    "ema_spread_atr_20",
    "ret_kurt_50",
    "ret_skew_200",
    "range_realized_vol_50",
    "hurst_diff_100_50",
    "ret_kurt_200",
    "hurst_100",
    "btc_ret_14d",
    "ret_skew_50",
    "vwap_dev_20",
    "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d",
)  # length = 14
```

Engineer modifies `src/crypto_trade/features_v3/__init__.py` to add the new constant, AND updates `_verify_feature_columns()` in `run_baseline_v3.py` to assert `len(V3_FEATURE_COLUMNS) == 14` (the temporary iter-v3/007 length; the original `n != 34` assertion would fail). The runner must pass `feature_columns=list(V3_FEATURE_COLUMNS)` to LightGbmStrategy unchanged at line 854 — only the LIST CONTENTS change.

DROPPED 20 features (these strings must NOT appear in V3_FEATURE_COLUMNS during iter-v3/007):

```
volume_cv_50, fracdiff_logclose_dstat, parkinson_gk_ratio_20, obv_slope_50,
volume_mom_ratio_20, mom_accel_20_100, btc_vol_14d, ret_autocorr_lag5_50,
ret_skew_100, hurst_200, bb_width_pct_rank_100, btc_ret_7d, parkinson_vol_20,
btc_ret_3d, fracdiff_logvolume_dstat, cusum_reset_count_200, hl_range_ratio_20,
atr_pct_rank_500, mom_accel_5_20, atr_pct_rank_200
```

Note: this is a TEMPORARY iter-v3/007 modification. iter-v3/008 will choose whether to keep top-14 or revert based on the EXPLORATION outcome. Engineer should structure the change so iter-v3/008 can revert via `git revert` or by editing back to 34.

### 3.4 Risk gates — UNCHANGED (v2's 5 active gates + BTC trend filter)

| Gate | Status |
|---|---|
| Vol scaling (atr_pct_rank_200) | ON |
| ADX threshold (20) | ON |
| Hurst regime check | ON |
| Z-score OOD (\|z\| > 2.5) | ON |
| Low-vol filter (atr_pct_rank_200 ≥ 0.33) | ON |
| BTC trend filter (±20%, 14d) | ON |
| Hit-rate feedback gate | OFF |
| R1 / R2 / R3 | OFF |

**Note**: The vol scaling, low-vol filter, and z-score OOD gates compute on FEATURES that may or may not appear in V3_FEATURE_COLUMNS_TOP_N. Specifically:
- `atr_pct_rank_200` is DROPPED from V3_FEATURE_COLUMNS_TOP_N but is still computed by the feature pipeline (it's in the parquet) and the gate logic reads it directly. Engineer should verify the gate code references the parquet column, NOT the model's training feature list. iter-v3/006 ran with the same risk gates; this is not a new risk surface.

### 3.5 Sub-fix decomposition

iter-v3/007 has THREE atomic deliverables. Each is a Phase-6 commit that the QE owns.

| # | Sub-fix | Spec | Status / verifier |
|---|---|---|---|
| 1 | **Add `V3_FEATURE_COLUMNS_TOP_N` constant** | `src/crypto_trade/features_v3/__init__.py`: add a new 14-tuple constant alongside `V3_FEATURE_COLUMNS`. Engineer can either temporarily REASSIGN `V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N` for iter-v3/007 (cleanest) OR add a CLI flag `--features-top-n N` to `run_baseline_v3.py` (more complex). Prefer reassignment — it keeps the Phase 6 invocation simple and matches the iter-v3/006 BCH-only-via-V3_MODELS-edit pattern. | Verifier: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14, f'len={len(V3_FEATURE_COLUMNS)}'"`. |
| 2 | **Update `_verify_feature_columns()`** in `run_baseline_v3.py:181-189` from `n != 34` to `n != 14` for iter-v3/007 only | One-line change: `if n != 14:`. Engineer can make this a one-liner OR parametrize via a constant. | Verifier: pre-flight prints `V3_FEATURE_COLUMNS: 14 columns  PASS`. |
| 3 | **Run `--exploration --seeds 1`** on full 4-symbol universe at full IS window | Phase-6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1` (no `--symbols` flag → all 4 V3_MODELS). The `--exploration` flag at SHA `bce50c8` automatically sets `ENSEMBLE_SIZE=1`, `colsample_bytree=1.0`, and `n_trials=10` (default for exploration). Wall-clock target: < 60 min. | Verifier: `test -f reports-v3/iteration_v3-007/comparison.csv` AND `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-007/comparison.csv'); print(df.iloc[0])"`. |

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input)

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK. Verifier commands MUST execute and exit 0 post-Phase 6.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | Sub-fix #1 (V3_FEATURE_COLUMNS reduced) | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14, f'len={len(V3_FEATURE_COLUMNS)}'"` exits 0 |
| 2 | Sub-fix #2 (_verify_feature_columns updated) | `run_baseline_v3.py:181-189` | grep `n != 14` matches in `_verify_feature_columns`; pre-flight log line shows `V3_FEATURE_COLUMNS: 14 columns  PASS` |
| 3 | Sub-fix #3 (`--exploration --seeds 1`) produces comparison.csv | runner | `test -f reports-v3/iteration_v3-007/comparison.csv` |
| 4 | Sub-fix #3 produces non-zero monthly_sharpe in IS | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-007/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert float(ms) != 0, f'IS sharpe is zero: {ms}'"` exits 0 |
| 5 | **EXPLORATION central test**: IS monthly Sharpe > 0 (signal exists at all) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-007/comparison.csv'); ms = df.loc[df['metric']=='monthly_sharpe','in_sample'].iloc[0]; assert float(ms) > 0, f'IS sharpe non-positive: {ms}'"` exits 0 |
| 6 | `pareto_front.csv` has ≥1 row (single-seed exploration) | runner | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-007/pareto_front.csv'); assert len(df) >= 1, f'rows={len(df)}'"` exits 0 |
| 7 | All 35 adversarial tests pass | tests | `uv run pytest tests/strategies/ml/ -v` exits 0 |
| 8 | Wall-clock ceiling: total Phase 6 runtime < 60 min | engineering report | `python -c "import json; d=json.load(open('briefs-v3/iteration_v3-007/engineering_report_summary.json')); assert d['wall_clock_minutes'] < 60, f'minutes={d[\"wall_clock_minutes\"]}'"` exits 0 |
| 9 | Full v3 universe used (4 symbols, no --symbols filter) | runner invocation log | `grep -E "Active models: 4/4" reports-v3/iteration_v3-007/run.log` exits 0 |
| 10 | `--exploration` flag was active in the run | runner invocation log | `grep -E "exploration|colsample.*1\.0|ENSEMBLE_SIZE.*1" reports-v3/iteration_v3-007/run.log` exits 0 |

### 3.7 NO new features added, NO meta-labeling, NO universe change beyond what's specified

iter-v3/007 is purely a feature-subsetting EXPLORATION iteration. The model architecture, label scheme, risk gates, CPCV parameters, and walk-forward window are byte-for-byte unchanged from iter-v3/006. The ONLY structural changes:

1. `V3_FEATURE_COLUMNS` is reassigned from the 34-feature tuple to the 14-feature top-N tuple (sub-fix #1).
2. `_verify_feature_columns()` asserts `n != 14` instead of `n != 34` (sub-fix #2).
3. The runner is invoked with `--exploration` (sub-fix #3) which hardcodes `ENSEMBLE_SIZE=1`, `colsample_bytree=1.0`, and defaults `n_trials=10`.

NO meta-labeling. NO universe change. NO new risk gates. NO new features.

The graduated EXPLORATION-then-CONFIRMATION rollout is explicit:
- **iter-v3/007 (THIS)**: `--exploration --seeds 1` on full 4-symbol universe at top-14 features. ~30-60 min. EXPLORATION test of "does feature subsetting produce IS Sharpe > +0.5?".
- **iter-v3/008 (NEXT, conditional)**: depends on iter-v3/007 Critic verdict.
  - If `EXPLORATION-PROMISING`: CONFIRMATION run at `--seeds 5 --n-trials 50` (NO --exploration), full universe, top-14 features. Wall-clock 6-12h. Tests if the EXPLORATION signal survives full ensemble + n_trials.
  - If `EXPLORATION-NEGATIVE`: next-axis EXPLORATION (NOT same axis re-test) — e.g., feature ADDITIONS instead of subsetting, OR labeling-axis EXPLORATION (timeout=14 vs 21).

### 3.8 Inheritance plan from iter-v3/006

The `iteration-v3/007` branch was branched from `iteration-v3/006` head. Two new code commits already shipped:

- `bce50c8 feat(iter-v3/007): --exploration mode (colsample=1.0, ENSEMBLE_SIZE=1, n_trials=10)` (the runner CLI flag + internal plumbing)
- `f0f8b84 feat(skill-v3): add Iteration Type Declaration + iterative two-round Critic` (the skill spec at SHA — adds Section 0.5 spec and the EXPLORATION-PROMISING / EXPLORATION-NEGATIVE verdict labels)
- `a394314 feat(iter-v3/007): top-N feature importance analysis` (this brief's Section 2 evidence)

iter-v3/006's seed-plumbing fix at SHA `9314db4` is carried over via the branching. The `_derive_ensemble_seeds(outer_seed, size=1)` call is what `--exploration` uses (size=1 for single inner model).

Critical inheritance verifiers (run before any code edits in Phase 6):
- `git log --oneline iteration-v3/007 -- run_baseline_v3.py | wc -l` ≥ 2 (iter-v3/006 SHA `9314db4` + iter-v3/007 SHA `bce50c8`)
- `test -f tests/strategies/ml/test_outer_seed_propagation.py` (iter-v3/006 inherited)
- `test -f tests/strategies/ml/test_per_cell_pbo_synthetic.py` (iter-v3/004 inherited)
- `test -f tests/strategies/ml/test_ensemble_seed_propagation.py` (iter-v3/005 inherited)
- `uv run pytest tests/strategies/ml/ -v` exits 0 with 35/35 PASS

### 3.9 Engineer's Phase 6 work plan (informative, not mandatory)

1. Verify §3.8 inheritance preconditions (35/35 tests PASS at HEAD).
2. Implement sub-fix #1: edit `src/crypto_trade/features_v3/__init__.py`. Either reassign `V3_FEATURE_COLUMNS` to the new 14-tuple (cleanest; matches iter-v3/006 BCH-only-via-V3_MODELS pattern) OR introduce a new `V3_FEATURE_COLUMNS_TOP_N` and reassign at runtime via the runner. PREFER reassignment.
3. Implement sub-fix #2: edit `run_baseline_v3.py:184` from `if n != 34:` to `if n != 14:`. Update the corresponding error message and pre-flight print.
4. Pre-flight: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; print(len(V3_FEATURE_COLUMNS))"` returns 14.
5. Pre-flight: `uv run pytest tests/strategies/ml/ -v` returns 35/35 PASS.
6. Run sub-fix #3: `time uv run python run_baseline_v3.py --exploration --seeds 1`. Wall-clock estimate: 30-60 min.
7. Persist outputs to `reports-v3/iteration_v3-007/`. Note the `run.log` should include `[features] V3_FEATURE_COLUMNS: 14 columns  PASS` and the `--exploration` activation banner.
8. Verify §3.6 reconciliation table — every verifier exits 0.
9. Write `engineering_report.md` + `engineering_report_summary.json` including: (a) wall-clock minutes, (b) trade counts (IS / OOS), (c) per-symbol monthly_sharpe / weighted_pnl, (d) git SHAs (`bce50c8` for `--exploration`, `a394314` for analysis, plus the new sub-fix #1+#2 SHA), (e) hardware, (f) library versions, (g) the 14 feature names actually used (sanity check against §3.3).

Estimated total wall-clock: ~30-60 min (full universe at `--exploration`'s `ENSEMBLE_SIZE=1, n_trials=10`).

---

## Section 4 — Expected OOS Impact

### 4.1 Per TYPE=EXPLORATION, headline metrics are GUIDANCE not GATES

iter-v3/007 is an EXPLORATION iteration. Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics (DSR, PSR, Sharpe thresholds) are NOT BLOCK-triggering for the Critic. The Critic instead emits `EXPLORATION-PROMISING` or `EXPLORATION-NEGATIVE` based on whether the IS Sharpe is in the "signal-found" range (>+0.5) or not.

### 4.2 Predicted IS Sharpe range

| Metric | iter-v3/006 BCH-only (n_trials=10, seed=42) | iter-v3/003 full universe (n_trials=50, seed=42) | iter-v3/007 prediction |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.4051 | -0.0746 | **predicted [+0.2, +0.8] with median +0.5** |
| OOS monthly Sharpe | -0.0010 | +1.0955 | informational; not a gate |
| Phase 6 wall-clock | 0.34h (BCH-only, n_trials=10) | ~3.6h (full universe, n_trials=50, ENSEMBLE_SIZE=5) | predicted < 1h |

The IS Sharpe predicted range [+0.2, +0.8] is wider than iter-v3/006's BCH-only +0.4 because:
1. The full universe is 4 symbols (more cross-symbol noise) but also more total trade-volume to learn from.
2. `--exploration` uses `ENSEMBLE_SIZE=1` (single inner model, no ensemble averaging), increasing per-seed variance vs iter-v3/006's `ENSEMBLE_SIZE=5` BCH-only run.
3. The top-14 feature set may amplify or dampen signal — both directions are plausible from the IS-only evidence in Section 2.

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS monthly Sharpe < 0 → top-14 feature subset removed essential signal; the mean-rank selection criterion is unreliable as a de-noising heuristic. Diary records the negative result; iter-v3/008 EXPLORATION tries a different feature axis (e.g., feature ADDITIONS, not subsetting).

**Falsifier 2**: IS monthly Sharpe > 0 BUT OOS monthly Sharpe < -0.5 (severe IS-OOS mismatch) → severe overfitting; the EXPLORATION signal is a researcher-induced artifact. iter-v3/008 CONFIRMATION at full ensemble + n_trials would not help (the mismatch would replicate); iter-v3/008 should try a different feature axis instead.

**Falsifier 3**: Phase 6 wall-clock > 90 min → `--exploration` mode is not as fast as documented (claimed ~25-30x faster than production); engineer documents the cause and the next iteration scopes down further (e.g., 1 symbol or 6-month sub-window).

**Falsifier 4**: `comparison.csv` shows 0 IS trades or 0 OOS trades → risk gates over-killed signal; the top-14 subset broke a gate (e.g., a vol-scaling input feature was dropped in a non-cosmetic way). Diary documents the gate-feature dependency.

**Process falsifier**: pre-flight `len(V3_FEATURE_COLUMNS) == 14` returns False → sub-fix #1 not implemented; Phase 6 must not start.

### 4.4 Expected EXPLORATION outcome

iter-v3/007 PASSES the EXPLORATION gate (Critic emits `EXPLORATION-PROMISING`) if and only if:

1. All 10 reconciliation table verifiers exit 0
2. IS monthly Sharpe > 0 (signal exists at all)
3. Wall-clock < 60 min
4. 35/35 adversarial tests pass
5. Critic OVERALL = `EXPLORATION-PROMISING`

The DSR / PSR / OOS Sharpe headline-metric questions are NOT in scope for iter-v3/007's MERGE evaluation. They belong to iter-v3/008 (CONFIRMATION).

---

## Section 5 — Risk Mitigation

### 5.1 NEW structural safeguards

iter-v3/007 introduces three structural safeguards:

1. **`--exploration` mode hardcodes `colsample_bytree=1.0`**. This minimizes per-seed feature-subsampling variance. Single-seed result is representative — a CONFIRMATION run at 5 seeds + full Optuna search space would shift the Optuna hyperparameter trajectory but not the underlying feature-set effect.
2. **TYPE=EXPLORATION declaration** (Section 0.5). Critic does NOT BLOCK on Check 3 edge axis (DSR/PSR), avoiding the iter-v3/004/005/006 false-block pattern where methodology iterations were blocked by edge thresholds that were structurally unaddressable.
3. **Wall-clock cap (60 min)**. Engineer aborts the run if elapsed time exceeds 60 min and reports the cause; iter-v3/008 EXPLORATION re-scopes (1 symbol or 6-month window).

### 5.2 Methodology-pipeline safety

Three additional safeguards (inherited from iter-v3/006):

1. **35 adversarial unit tests** (29 inherited + 6 new at SHA `9314db4`) must PASS before backtest. Engineer's pre-flight verifies.
2. **File-artifact reconciliation table** (§3.6). 10 verifier commands map to specific file artifacts. Empty cells = Phase 5.5 BLOCK.
3. **Pre-flight len-check on V3_FEATURE_COLUMNS**: catches the case where sub-fix #1 silently regresses (e.g., reassignment lost during a merge or rebase). Engineer prints the actual len before backtest.

### 5.3 NO new model-level risks introduced

The iter-v3/007 changes:
- Reduce the feature set (fewer features = less risk of look-ahead from any one feature; the dropped 20 features were ALL in the existing `V3_FEATURE_COLUMNS` and have already passed iter-v3/006's Critic Check 1 audit).
- Use `ENSEMBLE_SIZE=1` (single inner model) — increases per-seed variance, but the Critic Check 8 (hypothesis alignment) explicitly accommodates this.
- Use `n_trials=10` (vs production 50) — Optuna explores less; same risk as iter-v3/006's BCH-only run that used n_trials=10.

The only NEW dimension is the feature SUBSET. All 14 chosen features have passed prior Critic look-ahead audits. The 20 dropped features cannot introduce a new look-ahead risk by their absence.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — IDENTICAL TO iter-v3/006

| # | Primitive | Spec | Fire-rate prediction (IS) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX > 20 | ≈ 60% of bars pass | Trending only |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.5 | ≈ 5–8% killed | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±20% | ≈ 7–8% killed | Macro flips |

Combined kill rate target: 69–78%. SAME as iter-v3/006.

**Important**: Primitives 1, 4, 5 reference features (`atr_pct_rank_200`, the z-score-OOD-feature-set, and `atr_pct_rank_200` again) that are DROPPED from `V3_FEATURE_COLUMNS_TOP_N`. This does NOT affect the gates because:
- Gates read from the parquet feature DataFrame (where all 34 features remain computed by the feature pipeline) — NOT from the model's `feature_columns` argument.
- The model's `feature_columns` only controls which features the LightGBM trains on. Risk gates are independent.
- Engineer must verify in Phase 6 step 4 pre-flight: print the gate's input column references and confirm none is being read from the model-feature-columns argument.

### 6.2 Regime coverage — UNCHANGED

The full v3 universe IS data spans 2022-09-24 → 2025-03-23. Regime coverage includes 2022 LUNA/FTX, 2023 banking, 2024 halving + Trump rally, 2025 January correction.

### 6.3 Concentration — multi-symbol full universe

Full v3 universe (4 symbols) means the concentration cap (≤30% of OOS PnL per symbol) is meaningful again. iter-v3/003's full-universe single-seed result showed MKR concentration = 53.21% (above 30%), so concentration could fail again here. Per Section 8 (TYPE=EXPLORATION), concentration is NOT a gate for this iteration — the Critic flags it but does not BLOCK on it.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

iter-v3/004's 5/5 calibration win and iter-v3/006's 5/5 calibration win demonstrated the "≥3 process-level predictions" discipline. iter-v3/007's Section 7 inherits that discipline.

**Prediction P1 (process-level, P=15%): top-N feature subset breaks at the runner level (wrong column names, missing imports).** The reassignment of `V3_FEATURE_COLUMNS` to a 14-tuple may trip downstream code that hardcodes 34 (e.g., the `_verify_feature_columns()` itself, OR any test fixture that asserts 34). **Detection signal**: pre-flight `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14"` raises OR `_verify_feature_columns()` raises. **Mitigation**: Phase 6 work plan step 4 explicitly checks both. If the check fails, sub-fix #1 or #2 is incomplete; Phase 6 must abort.

**Prediction P2 (process-level, P=10%): `--exploration` flag has hidden dependency on `ENSEMBLE_SIZE=5` logic somewhere downstream.** The flag's plumbing at SHA `bce50c8` only modifies the `optimize_and_train` invocation. If any downstream code (e.g., `min_trl_months` computation, `n_trials_total` aggregation, the per-cell PBO loop) hardcodes `ENSEMBLE_SIZE=5` in a denominator or assertion, the run will crash mid-backtest. **Detection signal**: Phase 6 step 5 (35/35 tests) PASSES but step 6 (the actual backtest) raises a `ValueError` or `ZeroDivisionError`. **Mitigation**: pre-flight `uv run pytest tests/strategies/ml/ -v` must include test coverage for `ensemble_size=1`. If tests pass but backtest fails, Engineer reports the specific code line and iter-v3/008 EXPLORATION re-scopes.

**Prediction P3 (process-level, P=15%): wall-clock overshoots 60 min on full v3 universe (4 symbols) at exploration config.** The `--exploration` claim of 25-30x speedup is from `ENSEMBLE_SIZE=1` (5x) × `n_trials=10` (5x from the default 50) = 25x. But Optuna trial selection (TPE) is NOT linear in n_trials — at low n_trials the TPE prior dominates and trial generation is fast, but parquet I/O and per-cell PBO computation are NOT scaled by `--exploration`. Worst-case full-universe wall-clock could be 30 min to 2h. **Detection signal**: total Phase 6 wall-clock > 60 min on full universe. **Mitigation**: Engineer aborts at 90 min and reports the cause (likely parquet I/O or per-cell PBO). iter-v3/008 EXPLORATION re-scopes (e.g., 1 symbol).

**Prediction P4 (model-level, P=30%): IS Sharpe stays in [-0.1, +0.4] range — the top-14 feature subset doesn't help.** The bottom-20 features may carry small but meaningful signal that, in aggregate, the LightGBM was using to refine its decision boundary. Removing them could leave the model with insufficient feature diversity to fit the IS data well. **Pre-registered**: this is INFORMATIVE; iter-v3/008 EXPLORATION tries a different feature axis (e.g., feature ADDITIONS, not subsetting). EXPLORATION-NEGATIVE verdict is correct here.

**Prediction P5 (model-level, P=70%): IS Sharpe shifts modestly — say from iter-v3/003's full-universe -0.0746 baseline to a positive value in [+0.4, +0.7] range.** The top-14 selection is exactly the de-noising heuristic predicted to help under colsample=1.0. Combined with the full-universe (more total training data than BCH-only iter-v3/006), the IS Sharpe should land somewhere between iter-v3/006's BCH-only +0.4 and a top-end of +0.7 if the de-noising is effective. **Pre-registered as expected outcome**; CONFIRMATION iter-v3/008 follows at `--seeds 5 --n-trials 50`.

The predictions are intentionally Bayesian-calibrated:
- 3 process-level (P1, P2, P3) per iter-v3/003 lesson #3 discipline (validated 5/5 in iter-v3/004 and iter-v3/006)
- 2 model-level (P4, P5) per the historical class

If any of P1–P5 fails to materialize, the iter-v3/007 diary documents the calibration miss.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

**These thresholds are LOCKED before backtest. Phase 7 evaluation applies them mechanically.**

iter-v3/007 is an **EXPLORATION iteration** per Section 0.5. Headline-metric criteria from CONFIRMATION iterations (DSR > 0.95, PSR > 0.95, OOS Sharpe > 1.0, etc.) are NOT in scope. Critic emits `EXPLORATION-PROMISING` or `EXPLORATION-NEGATIVE` based on the EXPLORATION criteria below.

### EXPLORATION-PROMISING iff ALL of the following are true:

| # | Criterion | Threshold | Source |
|---|---|---:|---|
| 1 | TYPE=EXPLORATION declared in Section 0.5 | TRUE (verified at brief-time) | §0.5 |
| 2 | `--exploration` flag used in runner invocation | TRUE | §3.5 #3, §3.6 row 10 |
| 3 | Wall-clock < 60 min | TRUE | §3.6 row 8 |
| 4 | 35/35 adversarial tests pass | TRUE | §3.6 row 7 |
| 5 | `V3_FEATURE_COLUMNS` reduced to 14 (verified via len check) | TRUE | §3.6 rows 1+2 |
| 6 | `pareto_front.csv` has ≥1 row | TRUE | §3.6 row 6 |
| 7 | Critic OVERALL = `EXPLORATION-PROMISING` (NOT BLOCK or NEGATIVE) | TRUE | v3 mandatory; depends on EXPLORATION methodology axes 8 + IS Sharpe signal |
| 8 | Methodology axes (Critic Checks 1, 2, 4, 5, 6, 8) all PASS or WARN (no FAIL) | TRUE | Critic enforces |
| 9 | NO 5-seed or 10-seed runs THIS iteration | TRUE (vacuous; --seeds 1) | §3.7 |
| 10 | Reconciliation table no empty cells, all 10 verifiers exit 0 | TRUE | §3.6 |

### EXPLORATION-NEGATIVE iff:

- All criteria 1-6, 8, 9, 10 PASS BUT Critic OVERALL = `EXPLORATION-NEGATIVE` (criterion 7 fails because IS Sharpe < 0 and Critic deems the EXPLORATION axis unpromising)

### NO-MERGE-PROCESS iff ANY of:

- Engineer's Phase 6 wall-clock exceeds 90 min (above the 60-min cap)
- Phase 5.5 gate emits BLOCK
- Phase 7.5 Critic emits explicit BLOCK (NOT NEGATIVE — BLOCK indicates a process-level failure beyond the EXPLORATION axes)
- Any of criteria 1-6, 8, 9, 10 fails

### EXPLORATION outcome interpretation

| Critic verdict | Meaning | Next iteration |
|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe > +0.5 with no methodology FAILs | iter-v3/008 CONFIRMATION at `--seeds 5 --n-trials 50` (NO --exploration) on the SAME feature subset |
| `EXPLORATION-NEGATIVE` | IS Sharpe ≤ +0.5 (or < 0) with no methodology FAILs | iter-v3/008 EXPLORATION on a DIFFERENT axis (e.g., feature ADDITIONS, labeling timeout) |
| `BLOCK` (process-level) | A methodology check FAILED unexpectedly (e.g., look-ahead introduced via gate-feature interaction) | Diary documents, iter-v3/008 fixes the methodology gap and retries |

### Discretionary judgment — EXPLORATION pathway

iter-v3/007 has NO split-merge clause because the iteration scope IS EXPLORATION. The MERGE pathway is `EXPLORATION-PROMISING` (which is NOT a MERGE — it's a forward-pointer to iter-v3/008 CONFIRMATION; per skill spec at SHA `f0f8b84`, no actual MERGE happens at the EXPLORATION level).

**iter-v3/007 cannot MERGE with full headline metrics — that is by design.** It validates whether the top-14 feature subset is worth a CONFIRMATION run.

---

## Section 9 — Library Stack Declaration

| Package | Version pinned | License | Usage | Fallback if install fails |
|---|---|---|---|---|
| `numpy` | (already installed) | BSD-3 | `np.random.default_rng` for `_derive_ensemble_seeds`; column-array math | n/a |
| `scipy` | (already installed) | BSD-3 | (no use this iteration) | n/a |
| `statsmodels` | (already installed) | BSD-3 | `tsa.stattools.adfuller` for per-(sym, feat, month) ADF (unchanged) | n/a |
| `scikit-learn` | (already installed) | BSD-3 | `TimeSeriesSplit` in `_objective` (unchanged) | n/a |
| `lightgbm` | (already installed) | MIT | M1 only — no M2 | n/a |
| `pytest` | (already installed) | MIT | Adversarial unit tests (29 inherited + 6 new = 35) | n/a |
| `pandas` | (already installed) | BSD-3 | Parquet I/O (unchanged) | n/a |
| `pyarrow` | (already installed via pandas) | Apache-2 | Parquet engine (unchanged) | If missing, pandas auto-falls back to fastparquet |

**No new external deps.** The iteration's NEW code is:
- 1 analysis script + 3 output artifacts (already committed at SHA `a394314`)
- 1 sub-fix #1 edit to `src/crypto_trade/features_v3/__init__.py` (Engineer ships in Phase 6)
- 1 sub-fix #2 edit to `run_baseline_v3.py` (Engineer ships in Phase 6)
- 0 new pytest test files (all test plumbing inherited)
- 0 modifications to per-cell PBO / DSR / PSR / ADF code paths

### Aggregator strategy — UNCHANGED from iter-v3/006

Per-cell PBO with cross-cell mean aggregation. Per-cell n_eff with cross-cell median aggregation. The aggregator choices are fixed; iter-v3/007 only validates that feature-subsetting produces an IS Sharpe shift consistent with the de-noising hypothesis.

### Reproducibility stamp

The Engineer's Phase 6 writes `briefs-v3/iteration_v3-007/engineering_report.md` with:
- The git commit SHAs at backtest time (expected: `bce50c8` `--exploration` flag + `a394314` analysis + the new sub-fix #1+#2 SHA)
- Output of `uv pip list | grep -E "(numpy|scipy|statsmodels|scikit-learn|lightgbm|pytest|pandas|pyarrow)"`
- The full 14-feature list as actually trained on (sanity check against §3.3)
- The `comparison.csv` IS / OOS monthly Sharpe values
- The wall-clock minutes total
- The `tests/strategies/ml/test_outer_seed_propagation.py` and `test_per_cell_pbo_synthetic.py` and `test_ensemble_seed_propagation.py` test outcomes (all PASS expected)
- The `--exploration` activation banner from `run.log` (proof the flag was active)

---

## Appendix — Phase 5.5 Gate Self-Check

The QR has self-verified all 11 mandatory sections plus the Phase 5.5 inputs:

| Section | Status |
|---|---|
| 0 — Data Split | PASS — sacred constants UNCHANGED; ENSEMBLE_SIZE=1 / colsample=1.0 / n_trials=10 SET BY --exploration; documented |
| 0.5 — Iteration Type Declaration | PASS — TYPE: EXPLORATION declared; justification 1 paragraph; references skill SHA `f0f8b84` |
| 1 — Hypothesis | PASS — one sentence; specific testable target (IS Sharpe > +0.5); falsifiers in §4.3 |
| 2 — IS-Only Numerical Evidence | PASS — `analysis/iteration_v3-007/feature_importance_topN_demo.py` committed at SHA `a394314` BEFORE this brief; 3 outputs committed; results inline in §2.1-2.4 |
| 3 — Proposed Changes | PASS — symbols UNCHANGED full v3 universe; labeling UNCHANGED; features REDUCED 34 → 14 with explicit dropped list; risk gates UNCHANGED; decomposed into 3 sub-fixes in §3.5; brief-vs-code reconciliation table in §3.6 with 10 file-artifact verifiers; inheritance plan in §3.8 |
| 4 — Expected OOS Impact | PASS — predicted IS Sharpe range [+0.2, +0.8]; 4 falsifiers in §4.3; EXPLORATION pathway in §4.4 |
| 5 — Risk Mitigation | PASS — 3 NEW structural safeguards in §5.1 + 3 methodology-pipeline safeguards in §5.2 |
| 6 — Risk Management Design | PASS — 7-primitive table identical to iter-v3/006; gate-vs-feature-column independence verified §6.1 |
| 7 — Pre-Registered Failure-Mode | PASS — 5 predictions with **3 process-level (P1, P2, P3)** per iter-v3/003 lesson #3 |
| 8 — Pre-Registered MERGE/NO-MERGE | PASS — 10 EXPLORATION criteria; EXPLORATION-PROMISING vs EXPLORATION-NEGATIVE pathways; CONFIRMATION metrics EXPLICITLY DEFERRED to iter-v3/008 |
| 9 — Library Stack | PASS — no new deps; aggregator strategy unchanged from iter-v3/006 |

Engineer: please run Phase 5.5 gate verification against the brief-vs-code reconciliation table in Section 3.6. Empty cells in the right column = BLOCK. Verifier commands that do NOT execute and exit 0 post-Phase 6 = NO-MERGE per Section 8.
