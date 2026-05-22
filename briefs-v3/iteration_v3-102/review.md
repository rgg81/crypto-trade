# Phase 7.5 Critic Review — iter-v3/102

OVERALL: MERGE

(MERGE = methodology clears all 8 mandatory + 4 optional checks. This is NOT a verdict on the iteration's edge or classification — the brief's falsifier F2 "IS monthly Sharpe < +0.60" fires at observed IS +0.3993, which is the QR's Phase-8 NEGATIVE call. The Critic verdict is solely the methodology BLOCK/MERGE gate, and no look-ahead or methodology defect was found.)

## Iteration Type (from Brief Section 0.5)

TYPE: EXPLORATION (cycle-5 slot #2). Per `feedback_v3_dsr_mode_artifact.md`, in EXPLORATION mode (3-seed, n_trials=35) the Check 3 edge axes (DSR, PSR) are INFORMATIONAL ONLY — they are regime-specific artifacts of the small trial count and are not BLOCK-triggering. The PBO axis of Check 3 remains a real gate. All other checks are scored at full enforcement.

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

This is the priority check, given the SUSPICIOUS IS-collapse (+0.3993) / OOS-spike (+1.5458) divergence. I traced `compute_alpha032` (`src/crypto_trade/features_v3/formulaic_v3.py:105-157`) line by line and ruled out look-ahead as the cause of the OOS spike. Every operation is strictly past-only:

- `vwap = quote_volume / volume` (line 143) — a per-bar ratio of two bar-`t` columns; known at bar `t` close, which is the decision time for bar `t+1`. This is the legitimate bar-close case, not look-ahead.
- `_ts_sum(close, 7)` (line 146 → line 88) — `rolling(7, min_periods=7).sum()`. Window ends at bar `t`; `min_periods == window`, so no partial window.
- `close.shift(5)` (line 151) — `delay(close, 5)`, a strict backward lag (positive shift = past).
- `_ts_corr(vwap, close_lag5, 230)` (line 152 → line 97) — `rolling(230, min_periods=230).corr()`. **Critical for the boundary-leak concern:** `min_periods` equals the full window length 230, so no partial window straddling a train/test boundary is ever admitted — the feature is NaN until 230 valid past bars exist. There is no centered window, no full-series `.mean()/.std()/.rank()`, no `bfill`/back-fill anywhere.
- `_scale_ts(x, 100)` (lines 148, 153 → lines 82-83) — `x.abs().rolling(100, min_periods=100).mean()`, then `s / denom.replace(0.0, np.nan)`. The `replace(0.0, np.nan)` is a forward-safe degenerate-denominator guard (produces NaN, never fills from the future).

The QE's `test_hard_causality` (`tests/features_v3/test_formulaic_v3.py:87-132`) is genuine AND sufficient: it removes 50 future bars (600 → 550) and asserts bit-identity over the 550-bar overlap. The overlap region contains bars 334-549 which are fully-computed non-NaN values exercising the complete 230-bar correlation window + 5-bar lag + 100-bar `scale_ts` — `max_abs_diff = 0.0`. The independent T3 adversarial audit (`alpha_ic_eda.py:274-314`, `T3_past_only_audit.csv`) confirms `alpha032` across all 3 symbols: `max_abs_diff_overlap = 0.0`, `nan_pattern_mismatch = 0`. The IS-collapse/OOS-spike divergence is therefore an overfitting / OOS-regime-luck signature, NOT a leak — and that is a QR Phase-8 classification matter (the brief's SUSPICIOUS criterion), not a methodology BLOCK. No look-ahead found.

### Check 2 — Embargo Width: PASS

The labeling config is `label_timeout_minutes = 10080`, `candle_minutes = 480` → `timeout_candles = 10080/480 = 21`. Required gap = `(timeout_candles + 1) × n_symbols = 22 × 3 = 66`. The runner computes `compute_embargo_candles(10080, 480) = 22` and `cv_gap = 22 × 3 = 66` (engineering report lines 74-76; brief Section 0 line 28: "CPCV n_paths=45, embargo=27, REQUIRED_GAP=66"). Actual gap = required gap = 66; symmetric application inherited from the `e149e9d` walk-forward fix (`train_end_ms = test_start_ms - embargo_ms`). The CPCV in `cpcv_paths.csv` shows 45 distinct paths with genuine Sharpe dispersion (1.741, 0.026, -0.440, 0.618, ...) — not degenerate. PASS.

### Check 3 — Multiple-Testing Correction: PARTIAL (PBO axis PASS; DSR/PSR axes informational for EXPLORATION)

Verified the DSR/PBO/PSR are genuinely computed, NOT the iter-v3/090/092 hardcoded-placeholder defect. `run_baseline_v3.py:2884` calls `deflated_sharpe_ratio_v3(observed_sr, num_trials, backtest_length, skewness, kurtosis)`; `:2913` calls `psr(...)`; `_compute_per_cell_pbo` (`:1622-1800`) iterates 173 per-cell CSCV matrices through `pbo_from_cpcv`. `per_cell_pbo.csv` confirms 113 real per-cell PBO rows with genuine dispersion (0.0, 0.0372, 0.4266, 1.0, 0.1778, ...) — computed, not stamped.

- **PBO = 0.1276** (`dsr.json`, per-cell cross-cell mean) — clears the < 0.40 threshold. This is the BLOCK-triggering axis of Check 3 and it PASSES. `frac_positive_paths = 0.6444` clears the 0.55 gate.
- **DSR = 0.0** and **PSR = 1.0** — these are the known EXPLORATION-mode artifacts. `n_trials = 315` (= 35 trials × 3 ensemble seeds × 3 symbols), confirming the 3-seed EXPLORATION budget. Per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are STRUCTURAL ARTIFACTS of the low trial count and are INFORMATIONAL ONLY — not BLOCK-triggering. DSR=0.0 here does not indicate overfitting; it indicates the small-`n_trials` regime. `n_eff = 19` is sensible (well above the n_eff<10 high-correlation flag).

No BLOCK from Check 3 — the only BLOCK-eligible axis (PBO) clears comfortably.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` (the Engineer's required output, present) gives `alpha032`'s pairwise IC vs all 14 incumbents. Maximum `|IC|` is **0.4927** with `vwap_dev_20` (row `alpha032`, col `vwap_dev_20`: -0.4927119). Second-highest is **0.3456** with `regime_momentum_signed_5d` (-0.3456337). Both are below the v3 family gate of 0.70. The EDA-reported max (T5: 0.466 vs `vwap_dev_20`) is consistent with the runner's IC matrix (-0.4927) — the small delta is the EDA's IS-window-only vs the runner's combined-panel computation, both well under threshold. `alpha032` is not redundant; the negative correlation with the two vwap/momentum incumbents is the expected partial-variance overlap, not a duplication. PASS.

### Check 5 — ADF Stationarity: PASS

`alpha032` is a NEW feature, so it must be ADF-stationary at the end of the training window. The training window ends at `OOS_CUTOFF_DATE = 2025-03-24`; the relevant rows in `adf_test.csv` are the `2025-03` month per symbol: BCHUSDT `p_value = 0.0` (stationary True), LDOUSDT `p_value = 5e-06` (True), TRXUSDT `p_value = 1e-06` (True). All 3/3 symbols are ADF-stationary (p < 0.05) at the training-window terminus. This corroborates the EDA's T9 (`T9_alpha032_adf.csv`: BCH p≈0, LDO p=0.0409, TRX p≈0). The early-history non-stationary months (e.g. BCH `2020-08` p=0.234) are warm-up-period artifacts, not training-terminus failures, and `alpha032` is stationary by construction (`scale_ts` bounds the feature; 230-bar correlation ∈ [-1,1]; 7-bar SMA gap mean-reverts). No regime-indicator carve-out needed or invoked. PASS.

### Check 6 — Pareto Dominance: PASS (N/A — single-seed-lineage EXPLORATION)

`pareto_front.csv` does not exist in `reports-v3/iteration_v3-102/` — correctly, because this is a 3-seed EXPLORATION run (`ensemble_summary.json`: `mode=exploration`, `ensemble_size=3`, all three ensemble seeds share `lineage=outer=42`), not a 10-seed CONFIRMATION Pareto validation. The Pareto-dominance check is a CONFIRMATION-stage gate; per the v3 two-tier evaluation (`feedback_v3_cycle1_axis_pass_criteria.md`), an EXPLORATION axis is judged against the /060 3-seed anchor and any PROMISING result must re-validate at CONFIRMATION where the 10-seed Pareto front is built. There is no chosen-seed-dominance defect to flag at the EXPLORATION stage. PASS (not applicable at this stage; no anomaly).

### Check 7 — Reproducibility: PASS

Four reproducibility properties verified:
1. **Commit SHA stamped** — engineering report stamps Phase 5.5 gate SHA `bc2a30a` and Phase 6 setup SHA `556c345`; `ITERATION_LABEL = "v3-102"` (`run_baseline_v3.py:131`).
2. **Explicit feature columns** — `run_baseline_v3.py:1862` passes `feature_columns=list(features_for_symbol(symbol))`; `features_for_symbol` (`features_v3/__init__.py:463-486`) returns `V3_FEATURE_COLUMNS_TOP_N` (the explicit 15-tuple). No `None`, no auto-discovery. `_verify_feature_columns` (`:413-422`) hard-asserts `"alpha032" in V3_FEATURE_COLUMNS` and `len == 15`.
3. **Ensemble seeds literal** — `ENSEMBLE_SEEDS` is hardcoded (`:99-102`); `_derive_ensemble_seeds(42, 5)` documented verbatim; `ensemble_summary.json` records the three EXPLORATION seeds `[191664963, 1662057957, 1405681631]` (outer=42 lineage). Deterministic.
4. **Trade-PnL spot check** — 3 random `out_of_sample/trades.csv` rows re-computed: row 1 (BCH short, entry 303.870, exit 282.100779, weight 0.33): `(303.870 - 282.100779)/303.870 × 100 = 7.1640%` → net `7.0640` → weighted `7.0640 × 0.33 = 2.3311` ✓; row 5 (BCH short, entry 365.790, exit 377.871508, stop_loss, weight 0.49): `(365.790 - 377.871508)/365.790 × 100 = -3.3029%` → net `-3.4029` → weighted `-3.4029 × 0.49 = -1.6674` ✓; row 3 (TRX short, entry 0.253000, exit 0.243110, weight 0.40): `(0.253 - 0.243110)/0.253 × 100 = 3.9091%` → net `3.8091` → weighted `1.5237` ✓. Sign convention, fee, and weighting all correct; no off-by-one. PASS.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1 hypothesis: "the v3 14-feature stack lacks a vwap/price lead-lag term composed with a fast mean-reversion gap; WorldQuant Alpha#32 is exactly that composition." Brief Section 3 spec: new module `formulaic_v3.py` with `compute_alpha032`, `GROUP_REGISTRY` entry `formulaic_v3`, `alpha032` as the 15th `V3_FEATURE_COLUMNS_TOP_N` element, `_verify_feature_columns` count → 15, `ITERATION_LABEL` → `v3-102`.

Implementation matches exactly:
- `formulaic_v3.py:105` `compute_alpha032` computes `scale_ts(sma7 − close, 100) + 20 × scale_ts(corr(vwap, close.shift(5), 230), 100)` — the verbatim Kakushadze Alpha#32 per-symbol port.
- `features_v3/__init__.py:113` registers `"formulaic_v3": add_formulaic_v3_features`; `:288` appends `"alpha032"` as the 15th `V3_FEATURE_COLUMNS_TOP_N` element after `regime_momentum_signed_5d`.
- `run_baseline_v3.py:413-422` `_verify_feature_columns` asserts `"alpha032" in V3_FEATURE_COLUMNS` and `len == 15`; `:131` `ITERATION_LABEL = "v3-102"`.

No scope creep: the 14 incumbents are bit-identical to /059; `V3_MODELS` (BCH/LDO/TRX), ATR multipliers (2.0/1.0), 21-candle timeout, `RiskV2Config` 7-gate stack, CPCV/embargo all unchanged. `comparison.csv` `n_trials = 315` = 35 × 3 × 3 confirms the 3-seed EXPLORATION spec. The single declared variable is the single implemented variable. No hypothesis-faking. PASS.

## Optional Checks 9-12

### Check 9 — Symbol Exclusion Enforcement: PASS

`run_baseline_v3.py:237-241` computes `overlap = set(symbols) & set(V3_EXCLUDED_SYMBOLS)` and asserts disjointness; `:650-659` re-asserts `V3_MODELS ∩ V3_EXCLUDED_SYMBOLS = ∅`. `V3_EXCLUDED_SYMBOLS` (`features_v3/__init__.py:489-505`) contains all v1/v2 symbols + MKR; BCH/LDO/TRX are disjoint. Engineering report pre-flight check 8 confirms PASS.

### Check 10 — Feature Isolation Enforcement: PASS

`formulaic_v3.py` imports only `numpy` and `pandas` (lines 60-61) — no `from crypto_trade.features` (v1) or `from crypto_trade.features_v2` (v2). The module docstring documents the track-isolation grep contract (lines 32-39); engineering report pre-flight check 3 confirms 0 matches. Cross-track isolation intact.

### Check 11 — Forming-Candle Audit: PASS (with note)

`compute_alpha032` does not reference `close_time` and operates only on `close`/`quote_volume`/`volume` — the feature math itself carries no forming-candle exposure. Engineering report (line 62) states "no re-fetch performed; CSVs from prior fetch with standard filter" and data-freshness is 6.4h (< 16h). The forming-candle concern is a data-layer matter handled by the standard fetch filter; no anomaly at the feature level. NOTE for the QR: the engineering report did not run an explicit tail-row `close_time` check on the regenerated parquets — a low-severity gap, recorded as a recommendation, not a BLOCK.

### Check 12 — Library Version Pinning: PASS

`pyproject.toml` declares `lightgbm>=4.0`, `optuna>=3.0`, `numpy>=2.0`, `pandas>=2.2`, `scikit-learn>=1.8,<1.9`, `scipy>=1.14`, `statsmodels>=0.14.6`, `pyarrow>=18.0`. Brief Section 9 declares the resolved pins (lightgbm 4.6.0, optuna 4.8.0, numpy 2.2.6, pandas 3.0.0, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6, pyarrow 23.0.1) — all consistent with the constraint ranges and inherited unchanged from /059. No new library introduced (`compute_alpha032` uses only numpy + pandas rolling). PASS.

## Recommendations to QR

These are items for the cycle-5 CONFIRMATION brief (if /102 advances) and process notes — NOT a "fix this iteration" list. The Critic verdict is MERGE on methodology; the iteration's classification (the brief's F2 IS-collapse falsifier fires at IS +0.3993 < +0.60) is the QR's Phase-8 NEGATIVE call.

1. **Document the IS-collapse explicitly in the diary, separating it from look-ahead.** The IS +0.3993 / OOS +1.5458 divergence (monthly Sharpe ratio 3.87) is the canonical overfitting/regime-luck signature, and the Critic has independently ruled out look-ahead (Check 1 PASS — `compute_alpha032` is strictly past-only; T3 + `test_hard_causality` genuine). Note that the brief's Section 8 SUSPICIOUS criterion is keyed to the *daily* Sharpe ratio outside [0.2, 5] — observed daily ratio is 3.796 (inside the band), so the daily-ratio SUSPICIOUS gate does NOT fire; the F2 IS-collapse falsifier (NEGATIVE) is what fires. The diary should make the F2-vs-daily-ratio distinction explicit so the classification is unambiguous.

2. **Record WorldQuant Alpha#32 in BASELINE_V3.md Dead Ideas with the specific failure mode.** alpha032 is the basket horse-race winner (T6 dShACC rank 1/18) yet still collapses IS at the multi-seed backtest — this is direct evidence that a held-out-tail single-classifier accuracy proxy with a CI straddling zero ([−0.0085, +0.0399]) does not predict the multi-seed Optuna IS fit. The Dead Ideas entry should name this so a future iteration does not re-port another thin formulaic alpha on the same horse-race evidence standard.

3. **For the next methodology-bearing EXPLORATION, add an explicit tail-row `close_time` audit to the engineering pre-flight.** Check 11 passed on the feature math, but the engineering report did not show an explicit "tail-row `close_time` not in the future" check on the regenerated `data/features_v3/*.parquet` files. A one-line assertion on the parquet tail would close the residual forming-candle gap at zero cost.
