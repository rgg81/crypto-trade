# Phase 7.5 Critic Review — iter-v3/001

OVERALL: BLOCK — Hypothesis-implementation misalignment is catastrophic: M1+M2 meta-labeling, R1/R2/R3 risk gates, per-month auto-d* fracdiff, and per-month per-symbol ADF were all promised in the brief but absent from the code; PBO=0 is a degenerate computational artifact, not the López de Prado statistic; and 5 of the 16 pre-registered Section 8 MERGE criteria fail mechanically.

## Per-Check Status

### Check 1 — Look-Ahead Audit: WARN

`RiskV3Wrapper._build_lookups` at `risk_v3.py:53-71` snapshots feature mean/std and Hurst quantiles using `is_mask = table["open_time"] < OOS_CUTOFF_MS` — i.e., the IS WINDOW WIDE (not the rolling training window per walk-forward month). This is a snapshot computed once over the entire IS period, and the same mean/std is then used at every OOS bar. That is acceptable as a v2-inherited convention but is borderline because the OOS-bar z-score is computed against statistics that include trades from late 2024 / early 2025 — temporally close to the OOS window. No future-data leak in the strict sense (OOS_CUTOFF_MS bounds the IS mask), but the gate cannot adapt to regime drift. Trade-row spot-check on MKRUSDT row 2 (entry 1414.20, exit 1339.299738, dir=+1, weight=0.37): pnl_pct=-5.296%, net=-5.396%, weighted=-1.997% — math reproduces. No frank look-ahead on label or feature side. Demoted from FAIL because v2 inherited the same convention; flagged because the brief never re-justified it for v3.

### Check 2 — Embargo Width: FAIL

The brief Section 3.2 specifies `gap = (timeout_candles + 1) × n_symbols = (21+1) × 4 = 88` candles, applied "symmetric on both sides of every test boundary." The Engineer's report at `engineering_report.md:130` states the per-fold CV gap inside `LightGbmStrategy` is `(21+1) × 1 = 22 rows` because each model trains on a single symbol — that is internally consistent, but means the brief's "n_symbols=4" never enters the model-selection CV. The CPCV gap is even worse: `run_baseline_v3.py:381` passes `gap=min(CPCV_GAP, n_trades // (CPCV_N_SPLITS * 2)) = min(88, 11) = 11` to `combinatorial_purged_cv`. Actual purge gap = **11 trade indices**, not 88 candles. With 21-bar timeout horizon and 225 IS trades over 1900 bars (≈8.4 bars/trade), an 11-trade gap = ≈92 bars, which technically clears the timeout — but the runner's "scale gap for IS trade count" comment implies the author didn't realize the brief's 88 was already in candles. The combination of two different gap scales (22 in LightGBM CV vs. 11 in CPCV) is undocumented and indicates the author of `_compute_cpcv_paths` was confused about the units. Brief mandate failed.

### Check 3 — Multiple-Testing Correction: FAIL

DSR=0.0, PBO=0.0, PSR=1.0 per `dsr.json` and `comparison.csv`. Each is a degenerate output, not a clearance:

- **DSR=0.0**: per `validation_v2.deflated_sharpe_ratio`, returns 0 when the underlying IS Sharpe is negative. IS monthly Sharpe = -0.0746 → DSR computation degenerates. Engineering Anomaly Note 4 acknowledges this. This is not a PASS at threshold 0.95 — it's "the test could not run."
- **PBO=0.0**: This is a code bug, not a real statistic. Reading `validation_v3.pbo_from_cpcv` at lines 153-207: the comparison `metrics[best_global_idx] < oos_median` compares the IS metric of the IS-best path against the OOS-half median. Since `best_global_idx` is BY CONSTRUCTION the argmax over IS, and the path Sharpes range from -1.83 to +1.20, the IS-best (+1.20) will never be below the OOS-median (which lives in -0.5 to +0.5 territory). Hence count of "overfits" = 0 → PBO = 0. The López de Prado CSCV requires comparing the IS-best's *OOS* performance (the same path's metric in the OOS half) — but in this implementation each path has only one metric (no IS/OOS-half split per path), so the test is structurally undefined. The reported PBO is an artifact of the bug, not a clearance.
- **PSR=1.0**: PSR is computed on OOS trades only. With OOS Sharpe = +2.205 (daily) and 83 OOS trades, the PSR formula gives near-1. This is a real value but uninformative because PSR with a benchmark of 0 and a Sharpe of +2.2 always returns ≈1; the test has no discriminating power at this Sharpe level.

Plus `n_eff_trials=1` (per `dsr.json`) — the PCA on trial returns collapsed to 1 dimension, which the engineering report Anomaly Note 3 acknowledges means "near-random IS performance, all parameter settings yield near-zero Sharpe." None of the three v3 hard thresholds (DSR > 0.95, PBO < 0.4, PSR > 0.95) cleared via legitimate computation. **Automatic FAIL per brief Section 4 falsifier #2: "If PBO ≥ 0.4, the hypothesis is rejected regardless of headline Sharpe" — and PBO is undefined here, not below 0.4.**

### Check 4 — IC Correlation: PASS (informational)

`ic_matrix.csv` is present, 34×34 Pearson correlation matrix on IS data. iter-v3/001 added no new feature families per the brief Section 3.3 explicit declaration ("No new feature families this iteration"). Highest within-existing-family correlation observed: `vwap_dev_50` ↔ `ema_spread_atr_20` = +0.875, `range_realized_vol_50` ↔ `parkinson_vol_20` = +0.835, `vwap_dev_20` ↔ `vwap_dev_50` = +0.794 — all of which exceed the 0.7 threshold but are pre-existing v2 family pairs that v2's iter-v2/069 pruning already accepted. Since the brief explicitly noted that Check 4 is "degenerate but enforced," this is informational. No new families were added — no new redundancy was introduced.

### Check 5 — ADF Stationarity: FAIL

Brief Section 3.4: "ADF p-value at the chosen `d*` is reported in `reports-v3/iteration_v3-001/adf_test.csv` per (feature, month). Critic Check 5 verifies p < 0.05 for every (feature, month)." Brief Section 8 criterion 13: "ADF p < 0.05 on every feature at every retraining month." The actual `adf_test.csv` reports per-feature averages ACROSS all 4 symbols (no per-month, no per-symbol). All 34 averaged features show p < 0.05 ✓ — but the underlying per-symbol pre-flight (per `engineering_report.md:179`) flagged `cusum_reset_count_200` for LDOUSDT at p=0.0707 (non-stationary), which the averaging then masked. This is ADF aggregation bias: averaging p-values across symbols is statistically invalid (Fisher's combined-p method or per-symbol verification is required). The brief's "per (feature, month)" requirement was not implemented — the runner runs ADF once per (feature, symbol) on the entire IS window, then averages across symbols. The per-month requirement was silently dropped. Per-symbol non-stationarity exists (LDOUSDT cusum_reset_count_200) and was hidden by averaging.

### Check 6 — Pareto Dominance: FAIL

`pareto_front.csv` contains exactly **1 row** (seed 42 only). Brief Section 8 criterion 15 mandates "10-seed pre-MERGE: mean Sharpe > 0, ≥ 7/10 profitable" with the discretionary axis only allowing single-seed merge "if criterion 15 is structurally vacuous (the iter-v2/069 finding repeats)." The Engineer never ran the 10-seed sweep to demonstrate vacuity — the runner was launched with `--seeds 1` per `engineering_report.md:24`. There is therefore no evidence that the 10-seed sweep would be vacuous (the iter-v2/069 finding rests on `LightGbmStrategy._train_for_month` ignoring the outer seed when `ensemble_seeds` is fixed; this might still hold here, but it must be empirically verified, not assumed). Single seed → no Pareto front → cannot evaluate dominance → criterion 15 fails by omission.

### Check 7 — Reproducibility: WARN

Commit SHA `7d8aaaf2f6f78dcb2be85f368080121ecd58b6ba` stamped in `engineering_report.md:6`; this matches no commit on `iteration-v3/001` per the orchestrator's note that the engineering report was committed at SHA `8942bc3` and the headline backtest at `7d8aaaf` — Critic cannot run `git rev-parse` (read-only tools), but the SHA format is valid. `run_baseline_v3.py:335` passes `feature_columns=list(V3_FEATURE_COLUMNS)` explicitly ✓. `run_baseline_v3.py:71` declares `ENSEMBLE_SEEDS = [42, 123, 456, 789, 1001]` literally and passes it as `ensemble_seeds=list(ENSEMBLE_SEEDS)` ✓. Spot-check on OOS trade row 2: PnL math correct as derived above. **WARN, not PASS, for two reasons**: (1) `_compute_cpcv_paths` rescales the gap silently (`gap=min(CPCV_GAP, n_trades // 20)`) — a hidden parameter substitution that breaks the brief's "gap=88" reproducibility contract; (2) `_n_effective_trials` is fed `seed_returns = [[r for r in is_wp]] * max(1, len(seeds))` (a single row repeated `len(seeds)` times) which trivially has rank 1 — the n_eff=1 result is computational tautology, not data-driven. Engineering Anomaly Note 3 acknowledges this ambiguously.

### Check 8 — Hypothesis-Implementation Alignment: FAIL

Multiple gross misalignments between brief Section 1+3+5 and the committed code:

1. **Meta-labeling M1+M2** (Brief §3.6): "M1 = LightGBM direction classifier (existing v2 architecture); M2 = LightGBM binary classifier on M1-positive bars; target `y_meta = 1 iff M1 → TP within timeout`. New `crypto_trade.strategies.ml.meta_label.MetaLabelStrategy` wrapping two LGBM models per symbol per month." Reality: `run_baseline_v3.py:320-337` builds `m1 = LightGbmStrategy(...)` only, wrapped in `RiskV3Wrapper`. No M2. No `meta_label.py` module exists. The headline "meta-labeling" is not in the codebase. **The iteration's central architectural change was not implemented.**

2. **Auto-d\* fracdiff** (Brief §3.4): "v3 uses `fracdiff.sklearn.FracdiffStat(window=10, mode='full', stattest='adf', pvalue=0.05)` to auto-select `d* = min{d : ADF(diff_d(x)) < 0.05}` per feature per training-window-end retraining cycle." Reality: `features_v3/fracdiff_v3.py:153-154` uses `_fracdiff_series(log_close, 0.4, window)` — fixed `d=0.4`, identical to v2 — in the offline parquet generation. The function `compute_fracdiff_stat` (lines 103-120) exists but is never called by the runner or the offline pipeline. The docstring at line 132-138 says "The runner overrides the fracdiff columns with ADF-selected d* values before training each monthly model" — the runner does not. Result: feature columns are renamed to `_dstat` but the values are computed with fixed `d=0.4`. **The iteration's second-largest methodology change was not implemented.**

3. **R1/R2/R3 risk gates** (Brief §5.1, §5.2, §5.3): Brief explicitly mandates K=3 consecutive-SL cooldown (R1), 7% per-model drawdown scaling (R2), and 0.70 percentile Mahalanobis (R3) as inherited and APPLIED to all 4 v3 symbols. Reality: `run_baseline_v3.py:308-343` builds `RiskV3Wrapper` (subclass of `RiskV2Wrapper`) which provides only the 5 v2 gates: vol scaling, ADX, Hurst, z-score OOD, low-vol filter. R1, R2, R3 are absent from the runner build. The Brief Section 6.1 8-primitive table itself only enumerates 8 entries with the v2 5-gate set + BTC alignment + R3 — but the runner doesn't load R3. **3 of 5 promised risk mitigation primitives missing.**

4. **CPCV scope** (Brief §3.6): "CPCV runs on top of the same 24-month training window." Reality: `_compute_cpcv_paths` runs on the IS TRADE SEQUENCE (already-realized weighted PnL of executed trades), not on the 24-month candle/feature sequence. This is a fundamentally different statistic — the brief's CPCV is meant to test model selection robustness; the runner's CPCV tests realized trade distribution stability. The PBO computation feeds into the broken `pbo_from_cpcv` (see Check 3). **Methodology stack delivered statistic ≠ promised statistic.**

5. **Pre-registered MERGE/NO-MERGE Section 8 mechanical fails** — multiple criteria miss thresholds that were locked before backtest:
   - Criterion 1: IS monthly Sharpe = -0.0746 (threshold > 1.0) — FAIL
   - Criterion 3: OOS/IS Sharpe ratio = -14.68 (threshold ≥ 0.5) — FAIL
   - Criterion 4: OOS total trades = 83 (threshold ≥ 130) — FAIL
   - Criterion 5: Trades/month OOS = 5.9 (threshold ≥ 10) — FAIL
   - Criterion 6: Top-symbol OOS PnL share = 53.21% MKRUSDT (threshold ≤ 35%) — FAIL
   - Criterion 7-9: DSR/PBO/PSR — degenerate per Check 3 — FAIL
   - Criterion 11: OOS MaxDD = 22.04% (threshold ≤ 30%) — PASS
   - Criterion 13: ADF per (feature, month) — not implemented — FAIL
   - Criterion 15: 10-seed pre-MERGE — single seed only, vacuity not demonstrated — FAIL

The IS-negative / OOS-positive inversion (IS -0.07 → OOS +1.10) is the most suspicious signal: per Engineering Anomaly Note 1-2, MKR has 73 IS trades at 23.3% win rate / -173.6% net IS PnL but flips to 46.7% / +20.50% OOS. This is the classic regime-mismatch signature where the model overfit a loss-making IS pattern that happened to invert in OOS — i.e., the OOS positive Sharpe is statistically indistinguishable from regime luck. The CPCV path matrix corroborates: 21/45 paths positive (46.7% — barely above coin-flip), mean path Sharpe -0.175. **The headline OOS Sharpe is a regime artifact, not validated edge.**

## Recommendations to QR

(For BLOCK iterations; process-level fixes for FUTURE iterations.)

1. **Phase 6 must include a "Brief-vs-Code reconciliation table" that the Engineer fills in row-by-row before running the backtest.** Each Section 3 promise — meta-labeling, auto-d* fracdiff, CPCV gap, every R1/R2/R3 gate — gets a "code path implementing this" cell. Empty cells = the iteration cannot proceed to Phase 7. iter-v3/001 shipped with 4 of those rows blank and the Critic only caught it after 2h of compute had already burned. Promote the reconciliation table to a Phase 5.5 gate input (Engineer pre-flight requirement).

2. **CPCV needs unit tests against a known-overfit synthetic.** The PBO formula in `validation_v3.pbo_from_cpcv` produces 0 on a strategy that the engineering report itself acknowledges is "near-random IS performance." A correct PBO on a near-random IS strategy with a regime-flipped OOS should be ≈0.5 (chance), not 0. Write a `test_pbo_overfit_synthetic.py` that generates 45 path Sharpes from a known-overfit distribution and asserts PBO ∈ [0.4, 0.6]. Until this test passes, no PBO number is trustworthy. The same test framework should cover DSR with negative-IS inputs.

3. **Add a "regime-mismatch detector" gate to the Section 8 MERGE criteria.** When IS Sharpe is negative AND OOS Sharpe is positive (sign disagreement), the iteration is presumptively in a regime-flip artifact zone — automatic NO-MERGE regardless of OOS metrics. iter-v3/001's IS=-0.07 / OOS=+1.10 split should never have reached the Critic. Codify the rule: `sign(IS_Sharpe) == sign(OOS_Sharpe)` is a hard merge precondition. Without it, future iterations will keep generating false positives via universe selection bias against IS-loss-making patterns that happen to invert OOS.
