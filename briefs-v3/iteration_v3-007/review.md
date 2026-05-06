# Phase 7.5 Critic Review — iter-v3/007

**Iteration Type**: EXPLORATION (per Brief Section 0.5; first iteration under skill SHA `f0f8b84`)

**OVERALL: EXPLORATION-PROMISING** — IS Sharpe +0.2241 is +0.30 above same-universe iter-v3/003 baseline (-0.0746) and inside the pre-registered [+0.2, +0.8] prediction band; methodology axes (Checks 1, 2, 5, 7, 8, 9, 10, 12) PASS clean; Check 4 is vacuous-PASS under strict subsetting reading; Check 6 is structurally WAIVED by single-seed `--exploration`. Forwarded to iter-v3/008 CONFIRMATION with caveats below.

---

## QR Response Considered

| # | Clarification | QR Position | Critic Disposition |
|---|---|---|---|
| 1 | Check 4 IC redundancy interpretation | Strict reading: vacuous PASS for subsetting iteration | **ACCEPTED** — skill Check 4 specifies "newly-added"; both flagged pairs (`vwap_dev_50 × ema_spread_atr_20 = 0.875`, `vwap_dev_50 × vwap_dev_20 = 0.794`) are carry-forwards from `V3_FEATURE_COLUMNS_FULL` audited in prior iterations. Vacuous PASS is correct under skill text. **However**, see Recommendation 1 — the carry-forward redundancy is a real CONFIRMATION-time risk and must be addressed in iter-v3/008 brief. |
| 2 | Check 6 Pareto under single seed | WAIVED per Section 8 criterion 9 | **ACCEPTED** — Pareto dominance is mathematically undefined on a single point; cross-symbol OOS dispersion (LDO +17.7%, BCH +8.2%, TRX +3.9%, MKR -6.5%) is informative but not Pareto-equivalent. Section 8 criterion 9 explicitly waives multi-seed for EXPLORATION. |
| 3 | EXPLORATION verdict on IS Sharpe = +0.2241 | DISCRETIONARY → EXPLORATION-PROMISING | **ACCEPTED** — Section 4.1 explicitly frames headline metrics as GUIDANCE not GATES for EXPLORATION TYPE; observed +0.22 sits inside the pre-registered [+0.2, +0.8] band; +0.30 absolute improvement vs same-universe baseline is a real direction shift; `--exploration` config is structurally pessimistic (n_trials=10 vs 50, ENSEMBLE_SIZE=1 vs 5) so +0.22 is a floor, not a representative point estimate; cost asymmetry (one CONFIRMATION run vs abandoning a valid de-noising axis) favors PROMISING. **Caveat (firm)**: the iter-v3/008 CONFIRMATION run MUST treat IS Sharpe ≤ +0.5 as mechanical NO-MERGE — this discretionary call buys exactly one CONFIRMATION budget, not a recursive escape hatch. |
| 4 | Stale runtime banner | iter-v3/008 cleanup | **ACCEPTED** — cosmetic-only; code is correct (verifier asserts `n != 14`), only the print statement at `run_baseline_v3.py:1315` and stale comment at `:1305` are wrong. Audit-trail-quality issue, not methodology. iter-v3/008 first commit must parametrize the banner against `len(V3_FEATURE_COLUMNS)` to prevent future drift. |

---

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

The 14 retained features are a strict subset of `V3_FEATURE_COLUMNS_FULL` audited cleanly in iter-v3/001-006. No new features introduced. The infrastructure fix at SHA `849c4a6` (`risk_v3.py:51-66`) modifies the parquet column-load list to include `atr_pct_rank_200` independently of `V3_FEATURE_COLUMNS` — this is a column selection change at the read layer with no temporal ordering implication. The `is_mask` filter at line 71 still restricts the IS feature snapshot to `open_time < OOS_CUTOFF_MS`, so RiskV3Wrapper z-score statistics remain past-only. No look-ahead introduced.

### Check 2 — Embargo Width: PASS

Required gap = `(timeout_candles + 1) × n_symbols = (21 + 1) × 4 = 88`. Pre-flight `_verify_label_leakage_gap()` confirmed `REQUIRED_GAP=88` matches at runtime (run.log:16). `combinatorial_purged_cv` is invoked with per-cell `gap=22` (per-symbol gap = `timeout+1`), summing to 88 across the 4-symbol full universe. Symmetric on both sides of test boundary, per López de Prado convention.

### Check 3 — Multiple-Testing Correction: PASS-METHODOLOGY (informational on edge axis)

**Per Section 0.5 TYPE=EXPLORATION, Check 3 edge axis (DSR/PSR) is informational, NOT BLOCK-triggering.**

Methodology axis:
- **PBO = 0.1419 < 0.4 PASS** (per-cell mean PBO across 173 informative cells; IS-only filter verified)
- **n_eff = 7 > 4 PASS** (per-cell median)
- **frac_positive_paths = 0.60**; path Sharpe q25/q50/q75 = -0.54/+0.12/+1.03 — bimodal but not pathological
- **n_trials = 40 reported** (4 symbols × 10 trials each — consistent with `--exploration` budget)

Edge axis (informational under EXPLORATION):
- DSR = 0.0 (low IS Sharpe + n_trials inflation rounds to float-zero; same root cause as iter-v3/003-006)
- PSR = 0.7932 (below 0.95; consistent with IS Sharpe = +0.22 being statistically distinguishable from zero but not at 95% confidence)

Methodology axis (PBO + n_eff) PASSes cleanly. Edge axis informational only per TYPE=EXPLORATION scope.

### Check 4 — IC Correlation: PASS (vacuous-strict, with carry-forward concern flagged)

Per QR Clarification 1, accepted under STRICT reading: skill Check 4 measures "newly-added" feature redundancy. iter-v3/007 ADDS no features; both flagged pairs (`vwap_dev_50 × ema_spread_atr_20 = 0.875`, `vwap_dev_50 × vwap_dev_20 = 0.794`) are carry-forwards from `V3_FEATURE_COLUMNS_FULL` that survived iter-v3/001-006 reviews. Vacuous PASS is correct under skill text.

**Honest disclosure**: the redundancy WAS masked in earlier IC matrices by the broader 34-feature set. Under colsample=1.0 (every tree split sees ALL features), redundant pairs steal effective gain estimation more aggressively than under colsample<1.0. This is a structural concern for iter-v3/008 CONFIRMATION at colsample-Optuna-sampled — see Recommendation 1.

### Check 5 — ADF Stationarity: PASS

At the IS-end window (2025-03), ALL 14 features × 4 symbols = 56 (sym, feat) cells report `stationary=True` with p-values typically 0.0 to 0.03. The 514 non-stationary cells in the 2,982-row report are concentrated in early months (2020-01 through 2021-Q4) where insufficient training data produced empty/null ADF statistics — these months produced "No split for 2020-XX (insufficient training data)" log entries during walk-forward training, so they are not used for model fitting. Model-fitting window starts at 2022-01 for BCH/TRX, 2022-08 for MKR, 2024-09 for LDO; ADF passes at the relevant windows.

### Check 6 — Pareto Dominance: WAIVED (per QR Clarification 2 + Section 8 criterion 9)

`pareto_front.csv` has 1 row only (single-seed `--exploration --seeds 1` mode):

| seed | OOS Sharpe | OOS MaxDD | Calmar | PBO | n_trades | max_conc% |
|---:|---:|---:|---:|---:|---:|---:|
| 42 | +0.0622 | 48.76% | +0.0741 | 0.1419 | 90 | 84.44% |

Section 8 criterion 9 explicitly states "NO 5-seed or 10-seed runs THIS iteration" — multi-seed Pareto is structurally not in scope. The single-seed row is a degenerate, trivially non-dominated front. Cross-symbol OOS dispersion (LDO +17.7%, BCH +8.2%, TRX +3.9%, MKR -6.5%, BCHUSDT 84.44% concentration in OOS) is INFORMATIVE for iter-v3/008 brief planning but is not a Pareto-equivalent under EXPLORATION rules. Recorded for diary; revisited in iter-v3/008.

### Check 7 — Reproducibility: PASS

Backtest commit SHA `849c4a6` recorded; `92218ef`, `bce50c8`, `a394314` all referenced in engineering report. `feature_columns=list(V3_FEATURE_COLUMNS)` passed explicitly at `run_baseline_v3.py:863` (never `None`). `_derive_ensemble_seeds(outer_seed, size=1)` is deterministic per outer seed. Library versions pinned and recorded (lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, pyarrow 23.0.1, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pytest 9.0.2). Spot-check of OOS trade row 2 (MKRUSDT short, entry 1436.10, exit 1286.73, weight 0.35): gross pnl_pct = (1436.10-1286.73)/1436.10 × 100 = 10.401%; net = 10.401 − 0.10 fee = 10.301%; weighted = 10.301 × 0.35 = 3.6055 — matches recorded exactly.

### Check 8 — Hypothesis-Implementation Alignment: PASS-WITH-NOTE

Brief Section 3.3 specifies the 14-feature top-N subset; `src/crypto_trade/features_v3/__init__.py:118-156` ships exactly this list with `V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N`. Brief Section 3.5 specifies `_verify_feature_columns()` updated from `n != 34` to `n != 14`; `run_baseline_v3.py:191` confirms `if n != 14:`. Brief Section 3.5 #3 specifies `--exploration --seeds 1` invocation; engineering report and `run.log:20` confirm `Seeds: 1, Optuna trials/model: 10`, and Trial 0 parameters do NOT include `colsample_bytree` (confirming `fast_mode=True` hardcoded path active per `optimization.py:206-218`).

The risk_v3 fix at SHA `849c4a6` IS authorized by the brief: Section 3.4 states "atr_pct_rank_200 is DROPPED from V3_FEATURE_COLUMNS_TOP_N but is still computed by the feature pipeline... gate logic reads it directly. Engineer should verify the gate code references the parquet column, NOT the model's training feature list." The brief acknowledged the dependency conceptually; the Engineer found the actual broken code path (`risk_v3.py:_build_lookups()` was reading `*V3_FEATURE_COLUMNS` via parquet `pq.read_table(path, columns=needed)`, which excluded the now-dropped `atr_pct_rank_200`). The fix adds `"atr_pct_rank_200"` to the `needed` list independently. Hypothesis-aligned plumbing, not scope creep.

**Note (cosmetic, per QR Clarification 4)**: `run_baseline_v3.py:1305` has stale comment and `:1315` prints `"feature-cols=34 PASS"` while actual check enforces `n != 14`. iter-v3/008 cleanup. Not methodology.

## Optional Checks

### Check 9 — Symbol Exclusion Enforcement: PASS

`_verify_symbols()` called at `run_baseline_v3.py:1303` against `V3_EXCLUDED_SYMBOLS = {BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR}`. Active models {BCH, MKR, LDO, TRX} are disjoint. No overlap.

### Check 10 — Feature Isolation Enforcement: PASS

`grep "from crypto_trade.features " src/crypto_trade/features_v3/` returns only docstring matches (line 7 of `__init__.py`, line 23 of `fracdiff_v3.py`) — no actual imports.

### Check 11 — Forming-Candle Audit: NOT INSPECTED

Not flagged as critical for this iteration; data-extent confirmation is in engineering report.

### Check 12 — Library Version Pinning: PASS

Engineering report records lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, pyarrow 23.0.1, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pytest 9.0.2 — consistent with brief Section 9.

---

## Recommendations to QR (oriented for iter-v3/008 CONFIRMATION)

1. **iter-v3/008 brief MUST address the carry-forward IC redundancy explicitly in Section 3 or Section 5.** Two pairs above the 0.7 threshold (`vwap_dev_50 × ema_spread_atr_20 = 0.875`, `vwap_dev_50 × vwap_dev_20 = 0.794`) are now MORE consequential under the top-14 retained set than they were in the broader 34-feature set, because (a) the diversity buffer is reduced and (b) CONFIRMATION will sample colsample_bytree via Optuna — at low colsample the redundant pair acts like a single feature with double the chance of being sampled, biasing the ensemble. iter-v3/008 brief should either (i) drop one feature from each redundant pair and document the IC-driven rationale, OR (ii) pre-register a paired-bootstrap CV proof that retaining both is empirically superior on IS data. Do NOT carry the redundancy forward silently — this Critic will flag it as FAIL on iter-v3/008 if it appears in a CONFIRMATION-TYPE iteration without explicit mitigation.

2. **iter-v3/008 CONFIRMATION must apply mechanical Section 8 thresholds without further discretion.** This Round 2 verdict spent the discretionary budget by accepting the QR's reading that +0.22 IS Sharpe is a floor under `--exploration` config rather than a point estimate. iter-v3/008 at full config (`--seeds 5 --n-trials 50`, no `--exploration`) MUST treat IS Sharpe ≤ +0.5 as mechanical NO-MERGE, OOS Sharpe ≤ +1.0 as mechanical NO-MERGE per the CLAUDE.md "Sharpe 1.0 floor" feedback, and PBO ≥ 0.4 as mechanical BLOCK. The discretionary "floor lifts under full config" hypothesis is the falsifiable claim that iter-v3/008 tests; if the floor does not lift, iter-v3/008 NO-MERGE is correct and the de-noising axis is dead. No second discretionary escape hatch.

3. **iter-v3/008 brief Section 4 MUST pre-register a Pareto-equivalent single-iteration metric for the multi-seed run, AND address per-symbol concentration head-on.** Current OOS shows BCHUSDT 84.44% concentration and per-symbol weighted_pnl dispersion from -14.03 (MKR) to +16.46 (LDO). Under CONFIRMATION's 5-seed regime the standard `pareto_front.csv` 5-row analysis applies (Check 6 mechanical), but the cross-symbol concentration is an INDEPENDENT axis that the EXPLORATION rules WAIVED. iter-v3/008 brief should either (i) pre-register a per-symbol max-weighted_pnl-fraction ≤30% as a mechanical merge gate, OR (ii) explicitly justify why MKR's negative contribution is acceptable in a 4-symbol portfolio (e.g., diversification benefit, regime-coverage value). Do NOT bring iter-v3/008 to me with MKR -14% PnL and no ex-ante story — that is a Check 8 hypothesis-faking risk on the next iteration.

---

**OVERALL: EXPLORATION-PROMISING**

iter-v3/008 proceeds as CONFIRMATION on the same top-14 feature subset at `--seeds 5 --n-trials 50` (no `--exploration`). Mechanical Section 8 CONFIRMATION thresholds apply without further discretion. Recommendations 1 and 3 above are pre-conditions for iter-v3/008 brief Phase 5.5 PASS — failure to address them in the brief will trigger Critic CONFIRMATION-BLOCK.
