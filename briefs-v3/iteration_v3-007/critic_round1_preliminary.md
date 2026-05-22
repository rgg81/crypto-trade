# Phase 7.5 Critic Review — iter-v3/007 — PRELIMINARY

**Iteration Type**: EXPLORATION (per Brief Section 0.5; first iteration under skill SHA `f0f8b84`)

**Scope reminder**: Per Section 0.5, Checks 1, 2, 4, 5, 6, 8 are scored with full enforcement. Check 3 edge axis (DSR/PSR) is INFORMATIONAL only, NOT BLOCK-triggering. Verdict will resolve to `EXPLORATION-PROMISING` or `EXPLORATION-NEGATIVE` in Round 2.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

The 14 retained features are a strict subset of `V3_FEATURE_COLUMNS_FULL` audited cleanly in iter-v3/001-006 (Critic chain confirmed each iteration). No new features introduced. The infrastructure fix at SHA `849c4a6` (`risk_v3.py:51-66`) modifies the parquet column-load list to include `atr_pct_rank_200` independently of `V3_FEATURE_COLUMNS` — this is a *column selection* change at the read layer with no temporal ordering implication. The `is_mask` filter at line 71 still restricts the IS feature snapshot to `open_time < OOS_CUTOFF_MS`, so RiskV3Wrapper z-score statistics remain past-only. No look-ahead introduced.

### Check 2 — Embargo Width: PASS

Required gap = `(timeout_candles + 1) × n_symbols = (21 + 1) × 4 = 88`. Pre-flight verifier `_verify_label_leakage_gap()` confirmed `REQUIRED_GAP=88` matches at runtime (run.log:16). `combinatorial_purged_cv` is invoked with `gap=PER_CELL_GAP=22` per-cell (per-symbol gap = `timeout+1`; symmetric), summing to 88 across the 4-symbol full universe. Symmetric on both sides of test boundary, per López de Prado convention.

### Check 3 — Multiple-Testing Correction: PASS-METHODOLOGY (informational on edge axis)

**Per Section 0.5 TYPE=EXPLORATION, Check 3 edge axis (DSR/PSR) is informational, NOT BLOCK-triggering.**

Methodology axis:
- **PBO = 0.1419 < 0.4 PASS** (per-cell mean PBO across 173 informative cells, audit trail in `per_cell_pbo.csv`, IS-only filter verified at `run_baseline_v3.py:676`).
- **n_eff = 7 > 4 PASS** (per-cell median).
- **frac_positive_paths = 0.60** (per `dsr.json`); path Sharpe q25/q50/q75 = -0.54/+0.12/+1.03 — bimodal but not pathological.
- **n_trials = 40 reported** (across 4 symbols × 10 trials each = 40 total — consistent with the `--exploration` budget; `--n-trials 10 × n_symbols 4`).

Edge axis (informational under EXPLORATION):
- **DSR = 0.0** (same root cause as iter-v3/003-006: low IS Sharpe + n_trials inflation rounds DSR to float-zero).
- **PSR = 0.7932** (below 0.95 threshold; consistent with IS Sharpe = +0.22 being statistically distinguishable from zero but not at 95% confidence).

The methodology axis (PBO + n_eff) PASSes cleanly. Edge axis informational only.

### Check 4 — IC Correlation: CONCERN (clarification candidate)

`ic_matrix.csv` shows TWO pairs in the retained 14 with `|IC_pearson| > 0.7`:

| Pair | IC | Threshold | Status |
|---|---:|---:|---|
| `vwap_dev_50` × `ema_spread_atr_20` | **0.875** | 0.7 | EXCEEDED |
| `vwap_dev_50` × `vwap_dev_20` | **0.794** | 0.7 | EXCEEDED |

Three other pairs are >0.5 but below threshold (`max_dd_window_50` × `range_realized_vol_50` = -0.660; `vwap_dev_50` × `sym_vs_btc_ret_7d` = 0.527; `ema_spread_atr_20` × `vwap_dev_20` = 0.547).

The skill's Check 4 specifies redundancy detection between **"newly-added"** feature families. iter-v3/007's hypothesis is feature *subsetting*, not addition — these pairs were already in `V3_FEATURE_COLUMNS_FULL` and survived prior iter-v3/001-006 reviews (where the broader 34-feature set diluted the redundancy signal). After dropping 20 less-important features, the retained set has *less feature diversity to absorb* the redundant pairs.

This is a Round 1 clarification candidate — see Clarifications section below.

### Check 5 — ADF Stationarity: PASS

At the IS-end window (2025-03), ALL 14 features × 4 symbols = 56 (sym, feat) cells report `stationary=True` with p-values typically 0.0 to 0.03. Verified via direct grep of `adf_test.csv`. The 514 non-stationary cells in the 2,982-row report are concentrated in early months (2020-01 through 2021-Q4) where insufficient training data produced empty/null ADF statistics — these months also produced "No split for 2020-XX (insufficient training data)" log entries during walk-forward training, so they are not used for model fitting. The model-fitting window starts at 2022-01 for BCH/TRX, 2022-08 for MKR, 2024-09 for LDO; ADF passes at the relevant windows.

### Check 6 — Pareto Dominance: WAIVED (clarification candidate)

`pareto_front.csv` has 1 row only (single-seed `--exploration --seeds 1` mode):

| seed | OOS Sharpe | OOS MaxDD | Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.0622 | 48.76 | +0.0741 | 0.1419 | 90 | 84.44 |

Pareto dominance analysis requires ≥2 seeds to determine non-dominance. Section 8 criterion 9 explicitly states "NO 5-seed or 10-seed runs THIS iteration" — the multi-seed test is structurally not in scope. The single-seed row is a degenerate Pareto front (trivially non-dominated).

This is a clarification candidate — see Clarifications section below.

### Check 7 — Reproducibility: PASS

- Backtest commit SHA `849c4a6` recorded; `92218ef`, `bce50c8`, `a394314` all referenced in engineering report.
- `feature_columns=list(V3_FEATURE_COLUMNS)` passed explicitly at `run_baseline_v3.py:863` (never `None`).
- `_derive_ensemble_seeds(outer_seed, size=1)` is deterministic per outer seed.
- Library versions pinned and recorded (lightgbm 4.6.0, numpy 2.2.6, etc.).
- Spot-check of OOS trade row 2 (MKRUSDT short, entry 1436.10, exit 1286.73, weight 0.35): gross pnl_pct = (1436.10-1286.73)/1436.10 × 100 = 10.401%; net = 10.401 − 0.10 fee = 10.301%; weighted = 10.301 × 0.35 = 3.6055 — matches recorded exactly.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-NOTE

Brief Section 3.3 specifies the 14-feature top-N subset; `src/crypto_trade/features_v3/__init__.py:118-156` ships exactly this list with `V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N`. Brief Section 3.5 specifies `_verify_feature_columns()` updated from `n != 34` to `n != 14`; `run_baseline_v3.py:191` confirms `if n != 14:`. Brief Section 3.5 #3 specifies `--exploration --seeds 1` invocation; engineering report and `run.log:20` confirm `Seeds: 1, Optuna trials/model: 10`, and Trial 0 parameters do NOT include `colsample_bytree` (confirming `fast_mode=True` hardcoded path active, per `optimization.py:206-218`).

The risk_v3 fix at SHA `849c4a6` IS authorized by the brief: Section 3.4 states explicitly "atr_pct_rank_200 is DROPPED from V3_FEATURE_COLUMNS_TOP_N but is still computed by the feature pipeline... gate logic reads it directly. Engineer should verify the gate code references the parquet column, NOT the model's training feature list." Section 6.1 reinforces this. The brief acknowledged the dependency conceptually; the Engineer found the actual broken code path (`risk_v3.py:_build_lookups()` was reading `*V3_FEATURE_COLUMNS` via parquet `pq.read_table(path, columns=needed)`, which excluded the now-dropped `atr_pct_rank_200`). The fix adds `"atr_pct_rank_200"` to the `needed` list independently. This is hypothesis-aligned plumbing, not scope creep.

**Note (cosmetic, not a fail)**: `run_baseline_v3.py:1305` has stale comment `# asserts len == 34`, and the pre-flight banner at `run_baseline_v3.py:1315` prints `"feature-cols=34 PASS"` — but the actual check enforces `n != 14`. The runtime banner LIES while the verifier CORRECT. See Clarifications.

## Optional Checks

### Check 9 — Symbol Exclusion Enforcement: PASS

`_verify_symbols()` called at `run_baseline_v3.py:1303` against `V3_EXCLUDED_SYMBOLS = {BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR}`. Active models {BCH, MKR, LDO, TRX} are disjoint. No overlap.

### Check 10 — Feature Isolation Enforcement: PASS

`grep "from crypto_trade.features " src/crypto_trade/features_v3/` returns only docstring matches (line 7 of `__init__.py`, line 23 of `fracdiff_v3.py`) — no actual imports.

### Check 11 — Forming-Candle Audit: NOT INSPECTED

(Not flagged as critical for this iteration; data-extent confirmation is in engineering report.)

### Check 12 — Library Version Pinning: PASS

Engineering report records lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, pyarrow 23.0.1, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pytest 9.0.2 — consistent with brief Section 9.

## Clarifications Requested from QR

1. **Check 4 IC redundancy interpretation under EXPLORATION-by-subsetting.** The IC matrix shows two pairs above the 0.7 threshold: `vwap_dev_50 × ema_spread_atr_20 = 0.875` and `vwap_dev_50 × vwap_dev_20 = 0.794`. Both pairs were present (and unmeasured) in `V3_FEATURE_COLUMNS_FULL` during iter-v3/001-006. Strict reading of skill Check 4 says "newly-added feature families" → vacuous PASS for subsetting. Adversarial reading says "the retained set is the *active* feature set under test, and redundancy among retained features degrades effective LightGBM diversity even more under colsample=1.0 (every tree sees ALL features) than under colsample<1.0" → this would be FAIL. Which interpretation does the brief endorse? If adversarial, does the brief still rate the iteration as EXPLORATION-PROMISING/NEGATIVE *despite* the redundancy, or does this become a downstream BLOCK trigger? Specifically: was the redundancy structure of the retained 14 considered when picking N=14 vs N=10 in the analysis script (`summary.json` shows N=10 as a stricter alternative)?

2. **Check 6 Pareto dominance under single-seed EXPLORATION.** `pareto_front.csv` has 1 row by design (Section 8 criterion 9 explicitly waives multi-seed). Skill Check 6 cannot resolve PASS/FAIL on dominance with 1 row — it can only resolve "WAIVED by EXPLORATION TYPE". Does the brief consider this WAIVED (no Critic action) or does the EXPLORATION verdict require a separate Pareto-equivalent (e.g., per-symbol weighted_pnl variance, OOS Sharpe consistency across symbols)? The OOS per-symbol breakdown (LDO +17.7%, BCH +8.2%, TRX +3.9%, MKR -6.5%) shows wide dispersion; under CONFIRMATION rules, MKR's negative contribution would weight against MERGE.

3. **EXPLORATION-PROMISING vs EXPLORATION-NEGATIVE on IS Sharpe = +0.2241.** Brief Section 4.1 states "headline metrics are GUIDANCE not GATES" and Section 4.2 predicts IS Sharpe range [+0.2, +0.8] with median +0.5. Observed +0.2241 sits at the bottom of the predicted range — *inside* the band but BELOW the +0.5 median target. Brief Section 8 EXPLORATION-PROMISING criterion 7 names "Critic OVERALL = `EXPLORATION-PROMISING`" and Section 8's verdict-interpretation table maps:
   - "IS Sharpe > +0.5 with no methodology FAILs" → EXPLORATION-PROMISING
   - "IS Sharpe ≤ +0.5 (or < 0) with no methodology FAILs" → EXPLORATION-NEGATIVE
   
   By Section 8's mechanical mapping, IS = +0.2241 < +0.5 → **EXPLORATION-NEGATIVE**. But the *direction* of improvement (+0.2241 vs iter-v3/003 baseline -0.0746 on the same 4-symbol universe) is positive, and IS Sharpe is below threshold *partly because* `--exploration` mode at `n_trials=10, ENSEMBLE_SIZE=1` introduces meaningful variance reduction not present in CONFIRMATION-config. Does the brief endorse the strict mechanical reading (NEGATIVE)? Or does the QR want the Round 2 verdict to invoke discretion ("subset shows positive direction; recommend CONFIRMATION at N=10 per the alternative analysis with full ensemble + n_trials=50 to test if the +0.22 floor lifts")? The Round 2 verdict label is determined by this answer.

4. **Stale runtime banner (cosmetic)**. `run_baseline_v3.py:1305` comment and line 1315 print message both reference `34` features but the actual verifier checks `n != 14` and the run shipped 14 features. Engineer's run.log line 24 also prints `feature-cols=34 PASS`. Code is correct; print is wrong. Is this worth requiring an Engineer follow-up patch (clean up stale messages) before the iter-v3/007 diary writes, or accepted as an iter-v3/008 cleanup item? Not a methodology issue — just an audit-trail-quality issue (a future reader could be misled).
