# Phase 7.5 Critic Review — iter-v3/010 — PRELIMINARY

**Iteration Type**: EXPLORATION (catalog row #3 since last CONFIRMATION; non-features axis = labeling, per Critic FINAL Rec 1 of iter-v3/009)
**Mode**: Round 1 — PRELIMINARY (NO OVERALL verdict)
**Code SHA**: `b55086a` | Brief SHA: `fdb17b1` | Phase 5.5 Gate SHA: `5a227c7` | Analysis SHA: `80332c1`

---

## Per-Check Status

### Check 1 — Look-Ahead Audit: PASS

ZERO new feature code. The single behavior change is the labeling barrier multipliers (`atr_tp_multiplier=2.0`, `atr_sl_multiplier=1.0`) at `run_baseline_v3.py:862-863`. Verified the labeling chain:

- `LightGbmStrategy._load_atr_for_master()` (`lgbm.py:249-282`) loads `natr_21_raw` per (symbol, open_time) via parquet `searchsorted` lookup. The helper `natr_21_raw` at `regime_v3.py:135` is `100.0 * _atr(high, low, close, period=21) / close` — a **trailing 21-period ATR** computed from past OHLC at index `t`. No future contamination at the entry decision.
- `label_trades()` (`labeling.py:212-261`) takes `atr = float(atr_values[idx])` AT entry, then scans **forward only** (`for j_pos in range(pos + 1, len(sym_idx))`) until barrier hit or timeout. The TP/SL distances are set at entry from `atr * tp_pct` / `atr * sl_pct`; the multipliers (2.0, 1.0) cannot create look-ahead because they multiply a past-only quantity.
- The IS/OOS boundary is preserved (`OOS_CUTOFF_MS=1742774400000` immutable; runner respects).

The IS Sharpe lift is NOT explained by a leakage mechanism in this audit — it would have to come from feature exploitation of the new label distribution, which is the legitimate question for Clarification 1 below.

### Check 2 — Embargo Width: PASS

Required gap = `(timeout_candles + 1) × n_symbols = (21+1) × 4 = 88`. Engineering report quotes runtime banner `Label-leakage gap: ... = 88 [matches REQUIRED_GAP=88] PASS`. Inner per-symbol fold gap = 22 rows × 184h, validated against TRXUSDT fold list (folds 0-4 each show 22-row gap). Timeout is UNCHANGED from iter-v3/009 (10080 minutes = 21 candles), so the inherited gap remains valid after the labeling-multiplier change. The barrier-distance shrinkage to 1.0×ATR/2.0×ATR cannot reduce the **temporal** width of overlapping forward windows — the timeout, not the multiplier, is what determines purge requirement. PASS.

### Check 3 — Multiple-Testing Correction: METHODOLOGY-PASS / EDGE-INFORMATIONAL

Per TYPE=EXPLORATION, methodology axis (PBO + n_eff) enforced; edge axis (DSR/PSR) is informational only.

- **PBO (per-cell mean) = 0.10770** — well below 0.40 threshold. Slight improvement vs iter-v3/009's 0.1145.
- **PBO `frac_positive_paths = 0.600`** from 45 return-proxy paths; **path Sharpe q25=-0.5366, q50=+0.1175, q75=+1.0278** — wide IQR but median > 0.
- **n_eff (per-cell median) = 7**; sensible.
- **n_trials = 40** (10 trials × 4 symbols, single-seed exploration). Matches budget.
- **DSR = 0.0** and **PSR = 1.0** — well-documented exploration-mode artifact (DSR collapses at single-seed; PSR saturates). EDGE axis is INFORMATIONAL per cadence rule and brief Section 8.

Methodology axis: PASS.

Note: 4 per-cell PBO values exceed 0.9 (BCH/2024-10 = 0.9868, TRX/2025-10 = 1.0, TRX/2025-11 = 1.0, MKR/2025-04 = 0.9952, MKR/2025-07 = 0.9914), indicating select cells where rank-IS-best correlates with rank-OOS-worst. Mean aggregator dilutes; this does not flip the headline number, but may merit Clarification.

### Check 4 — IC Correlation: PASS

`ic_matrix.csv` is a 13×13 symmetric matrix. Max off-diagonal `|IC|` values audited:

- `max_dd_window_50 × range_realized_vol_50` = -0.660
- `vwap_dev_20 × ema_spread_atr_20` = +0.547
- `ret_skew_200 × ret_kurt_200` = +0.593
- `ema_spread_atr_20 × btc_ret_14d` = +0.508
- `ema_spread_atr_20 × sym_vs_btc_ret_7d` = +0.507

ZERO pairs at or above the 0.70 threshold. The 13-feature subset inherited from iter-v3/008 (with `vwap_dev_50` previously dropped) keeps redundancy under threshold. No new families introduced this iteration — feature axis byte-for-byte unchanged. PASS.

### Check 5 — ADF Stationarity: WARN (carry-forward, no regression)

`adf_test.csv`: 2769 cells. The 2020-01 row has all NaN p-values (insufficient data for ADF on first month — expected behavior). Spot-check of 2020-02 / 2020-03 BCH cells shows p-values > 0.05 for max_dd_window_50, hurst_100, ret_skew_200 (persistent series by construction) — same per-month low-T artifact as iter-v3/007/009. Engineer report cites 82.3% stationary across all cells. Walk-forward retraining + ADF-as-monitoring (not gate) waiver from iter-v3/004 stands; feature set unchanged from iter-v3/009 means structurally same ADF profile. WARN carry-forward, no regression introduced.

### Check 6 — Pareto Dominance: WAIVED (single-seed exploration)

`pareto_front.csv` has exactly 1 row (seed=42, monthly_sharpe=1.8122, max_drawdown=15.08%, calmar=4.0179, pbo=0.1077, n_trades=109, max_concentration=52.51%). Per Section 8 criterion 9 of the brief and the cadence rule (`--seeds 1` for EXPLORATION), the 10-seed Pareto frontier comparison is structurally vacuous. WAIVED.

For record: `max_concentration_pct = 52.51%` (BCH-driven) exceeds the 35% per-symbol cap that would apply at CONFIRMATION; informational under EXPLORATION per brief Section 6.3.

### Check 7 — Reproducibility: PASS

- Code SHA stamped: `b55086a` in engineering report header.
- `ITERATION_LABEL = "v3-010"` confirmed at `run_baseline_v3.py:99`.
- `feature_columns` explicit via `V3_FEATURE_COLUMNS` (13-tuple, hardcoded literal at `features_v3/__init__.py:118-139`).
- `_verify_feature_columns()` at `run_baseline_v3.py:181-203` raises if `len != 13` OR `'vwap_dev_50' in V3_FEATURE_COLUMNS`. The docstring is **partially** parametrized — line 182 now uses `f"...iter-{ITERATION_LABEL}"` per Clarification 3 from iter-v3/009. However the runtime exception strings at lines 192-194 and 198-199 still reference hardcoded `iter-v3/008` and `Critic FINAL SHA a544621` literals (these are exception messages, not the docstring proper; cosmetic, non-blocking).
- Trade-row spot-check (random, OOS): MKRUSDT LONG entry=1067.7, exit=1200.0559, weight=0.67, manual recomputation: `(1200.0559 - 1067.7) / 1067.7 * 100 = +12.396%`, fee 0.1% → `+12.296%` net. CSV reports `12.2964`. Match. Sign and direction-multiplier correct. Spot-check 2 of 3 (MKRUSDT SHORT entry=1436.1, exit=1487.6081): `(1487.6081 - 1436.1) / 1436.1 * (-1) * 100 = -3.587%`, fee 0.1% → `-3.687%`. CSV reports `-3.6867`. Match.
- Library versions stamped (numpy 2.2.6, scipy 1.17.0, statsmodels 0.14.6, scikit-learn 1.8.0, lightgbm 4.6.0, pandas 3.0.0, pyarrow 23.0.1, pytest 9.0.2). Stack identical to iter-v3/009.

### Check 8 — Hypothesis-Implementation Alignment: PASS

Brief Section 1: tighten ATR multipliers from `(tp=2.9, sl=1.45)` to `(tp=2.0, sl=1.0)`, same 2:1 ratio, expect IS Sharpe ≥ +0.10 (Falsifier 1). Code change at `run_baseline_v3.py:862-863` literally implements this and only this; ITERATION_LABEL is `v3-010`; docstring partially parametrized per Critic Rec 3 (lines 182). The 13-feature set, risk gates, CPCV (10-fold, 2-test, gap=88), training_months=24, OOS_CUTOFF_DATE are ALL byte-for-byte unchanged from iter-v3/009. Single-axis (labeling) variation respected. Hypothesis testable via pre-registered IS Sharpe band [-0.20, +0.40] with median +0.10. Falsifier 1 NOT triggered (IS = +0.5683 >> +0.10), Falsifier 2 NOT triggered (IS trades 357 > 267), Falsifier 3 NOT triggered (7 min < 30 min target).

The actual IS Sharpe (+0.5683) **overshoots the predicted upper bound (+0.40)** by 0.17 — the QR's own brief Section 7 calibration discipline classifies this as a calibration miss (the same way iter-v3/009's IS undershoot was a miss). Engineer noted this in the report. The OOS Sharpe (+1.8122) and IS lift (7× vs iter-v3/009) on a multiplier change with no new model code is a striking result that warrants probing — but probing is for QR via Clarifications, not BLOCK at Check 8.

### Check 9 — Symbol Exclusion Enforcement: PASS

`run_baseline_v3.py:151-158` (`_verify_symbols`) raises if `set(symbols) & set(V3_EXCLUDED_SYMBOLS)` is non-empty. V3_EXCLUDED_SYMBOLS is the {BTC, ETH, LINK, LTC, DOT, BNB, SOL, XRP, DOGE, NEAR} set — disjoint from iter-v3/010's {BCH, MKR, LDO, TRX} universe. Engineering report confirms 4/4 active models in run.log.

### Check 10 — Feature Isolation Enforcement: PASS

`_verify_track_isolation()` invokes grep against forbidden imports in `src/crypto_trade/features_v3/`. ZERO new files added in iter-v3/010 commits. Inherited isolation guarantee unchanged.

### Check 11 — Forming-Candle Audit: PASS (no change)

Same data-staleness guard inherited from iter-v3/007 (`_verify_data_freshness`, `max_lag_hours=16.0`). Per-cell PBO data extends through 2026-05 retrain month (BCH 2026-05 has 616 candles, consistent with rolling 24-month training window from 2024-05). No forming-candle anomaly identified.

### Check 12 — Library Version Pinning: PASS

Engineering report stamps versions matching iter-v3/009 exactly: lightgbm 4.6.0, numpy 2.2.6, pandas 3.0.0, pyarrow 23.0.1, pytest 9.0.2, scikit-learn 1.8.0, scipy 1.17.0, statsmodels 0.14.6. No new external deps per brief Section 9. PASS.

---

## Striking-Result Forensic Notes (for QR awareness, not BLOCK conditions)

The IS Sharpe lift from `+0.0802` (iter-v3/009) → `+0.5683` (iter-v3/010) is **+0.488 absolute, ~7× multiplicative**, on a single-axis labeling-multiplier change with zero feature/model/risk-gate code change. This is the largest Δ on a single-axis EXPLORATION since the v3 track started. Mechanisms hypothesized in the request (a/b/c) are all defensible; the question is which one(s) drove it.

1. **Trade-rate scaling alignment**: Brief predicted 1.45× IS trade scaling (267 → 387 expected); actual is 1.34× (267 → 357). Within Brownian-approximation noise; the QR's pre-registration was honest.

2. **Per-symbol IS direction is uniform-positive 3/4**: BCH +16.02, LDO +56.69, TRX +19.49, MKR -32.37. The IS Sharpe lift is broad-based at the per-symbol level (not driven by one outlier symbol like iter-v3/009's LDO), but MKR is still the dominant IS drag (-32.4% on 101 trades, 32.7% WR). MKR's structural problem persists.

3. **Exit-mix shift**: with 33.7% more trades but the same 7-day timeout, the average trade-duration must have shortened — TP and SL hits faster, fewer timeouts. This is the mechanism (c) outlined in the request, and matches the structural intent of the multiplier change.

4. **OOS BCH 57.17% concentration is in the same family as iter-v3/007's 84% BCH concentration**: the v3 universe under EXPLORATION single-seed routinely produces ~50%+ symbol concentration. iter-v3/010 is no worse than iter-v3/007 on this axis; iter-v3/009's LDO 98.6% concentration was the outlier.

5. **PBO improved slightly** from 0.1145 → 0.1077, so the **selection-bias-adjusted edge has not deteriorated** on the methodology axis — this rules out the simple "trial-pool overfit" explanation. However 4 per-cell PBOs ≥ 0.99 (TRX/2025-10, TRX/2025-11, MKR/2025-04, MKR/2025-07) bear noting; the mean aggregator dilutes them but the cells are real.

6. **BCH OOS WR = 47.1% on 34 trades** with +1.04% avg PnL is plausibly genuine edge or BCH-tape-specific lottery. Bootstrap CI on 47.1% WR over 34 trades is wide [≈ 30-65%, depending on test], so the per-symbol point estimate alone is not decisive.

---

## Clarifications Requested from QR

These questions are NOT speculation — they are the questions Round 2 needs answered to assign final verdict (EXPLORATION-PROMISING / EXPLORATION-NEGATIVE / BLOCK).

### Clarification 1 — Mechanism attribution for the IS Sharpe overshoot

The brief Section 7 calibration-miss doctrine requires diary documentation of overshoots (P4 prediction band was [+0.10, +0.30]; actual +0.5683 exceeds upper bound by +0.27). Engineering report acknowledged the miss. **Question for QR: which of the three mechanisms outlined in the request is best supported by the IS data — (a) the (2.9, 1.45) calibration was hiding model edge; (b) (2.0, 1.0) tunes a regime-specific feature exploit narrowly; (c) tighter labels reduce label noise so features find real momentum more cleanly?** Specifically: would the QR run a no-code analysis script (similar to `analysis/iteration_v3-010/atr_multiplier_demo.py`) on the iter-v3/010 IS trades that breaks down per-symbol IS Sharpe by exit type (TP vs SL vs timeout) — to test whether the lift is dominantly from (c) faster TP hits, or (b) better directional selection at smaller magnitudes? The catalog row should ideally cite the dominant mechanism so the next CONFIRMATION-bundle can decide whether to inherit (2.0, 1.0) or scan further (e.g., (1.5, 0.75) or (2.5, 1.25)).

### Clarification 2 — MKR structural failure across three iterations

iter-v3/007 MKR OOS: -6.5%; iter-v3/009 MKR OOS: -13.1%; iter-v3/010 MKR OOS: -10.6% (29.4% WR on 17 trades). MKR is now the only OOS-negative symbol in iter-v3/010 and the worst OOS WR by ~10 percentage points. Brief Section 0 cadence rules require single-axis EXPLORATION, but iter-v3/010 chose labeling specifically to **change the model targets** for ALL symbols including MKR. The new labels did NOT fix MKR. **Question for QR: should MKR's structural failure across three consecutive EXPLORATION iterations trigger a per-symbol diagnostic before the next labeling/feature/gate axis is explored, or is the catalog discipline sufficient to register the pattern and continue?** Specifically, if iter-v3/011's axis is risk-gate threshold and MKR remains a 30%-WR drag, does the QR have a pre-committed plan for when per-symbol exclusion becomes a candidate (vs. the project memory rule `feedback_insist_on_symbols`)?

### Clarification 3 — OOS trade-rate floor implications for downstream CONFIRMATION

iter-v3/010 OOS = 109 trades over ~13.5 months = **8.07 trades/month**, vs. project memory's `feedback_trade_rate_floor` requirement of **10 trades/month AND 130 total**. Both are missed. iter-v3/009 was 87 OOS / ~6.4/month (worse). The direction is improving but neither EXPLORATION row clears the floor. **Question for QR: at the upcoming CONFIRMATION (after 7 more EXPLORATIONs), how does the trade-rate floor apply when the EXPLORATION evidence base is uniformly below floor?** Specifically: (a) does the floor relax at CONFIRMATION because 5-seed × full ensemble multiplies signal density, or (b) must the CONFIRMATION-bundling EXPLORATIONs each clear the floor to be eligible for inclusion, or (c) does the floor get satisfied at the **bundle** level rather than per-row? Pre-committing this rule now (before Round 2 of iter-v3/010) prevents the next CONFIRMATION QR from constructing a post-hoc floor-relaxation rationalization.

### Clarification 4 — Per-cell PBO outliers above 0.9

`per_cell_pbo.csv` shows 5 cells with PBO ≥ 0.9: TRX/2025-10 = 1.0, TRX/2025-11 = 1.0, MKR/2024-10 = 0.9204, MKR/2025-04 = 0.9952, MKR/2025-07 = 0.9914, BCH/2024-10 = 0.9868. These are cells where IS-best ranks anti-correlate with OOS performance. **Question for QR: are these PBO=1.0 cells a known characteristic of the per-cell aggregator at small n_eff (≤ 6 in TRX 2025-10/11), or do they signal structural instability in those specific (symbol, train_month) combinations that the cross-cell mean is masking?** If the latter, a Clarification-4-driven follow-up: should the catalog row for iter-v3/010 record `n_high_pbo_cells = 5/175` so future CONFIRMATION QRs can decide whether to weight evidence by `1 - max_per_cell_pbo` rather than `1 - mean_pbo`?
