# iter-v3/118 — Cycle-6 EXPLORATION slot #9 — NEW engineered-feature axis (Category-2 composed: `ema_signed_volregime` = `ema_spread_atr_20 × sign(range_realized_vol_50 − rolling_median_200)`) — FILED EXPLORATION-NEGATIVE catastrophic. The Section-8 Criterion 1a (IS Sharpe Δ < −0.20 vs /060 anchor) fires DECISIVELY: IS monthly Sharpe **+0.3782** vs /060 anchor **+0.8325** → Δ IS = **−0.4543** (2.27× the −0.20 threshold); OOS monthly Sharpe **−0.1501** vs /060 anchor **+0.1403** → Δ OOS = **−0.2904**. The brief Section 4 modal band ([+0.05, +0.30] IS Δ; [+0.05, +0.25] OOS Δ) FALSIFIED on both axes; the brief Section 4 explicit-falsifier band (OOS Δ < −0.50 AND IS Δ < −0.20) does NOT fire on the OOS leg, so the verdict route is Section-8 Criterion 1a (IS catastrophic) NOT the symmetric two-sided falsifier. The EDA T9 per-symbol multivariate-lift prediction (TRX +0.0082 sole positive carrier; BCH −0.0039 and LDO −0.0106) INVERTED at production: BCH emerged as the sole IS positive carrier (+52.61% net PnL at 42.7% WR) while TRX collapsed (−5.49% net at 32.9% WR) and LDO catastrophically failed (−13.80% net at 26.7% WR). The Section-7 Mode 3 (PROMISING-PARTIAL TRX-led, 20% prior) was the QR's closest modal prediction; it correctly anticipated per-symbol asymmetry but misidentified the carrier symbol — diagnostic of single-seed-lottery + multivariate-interaction-cancellation at n_trials=35, 15-dim Optuna scale (per `feedback_v3_inert_features_at_higher_budget.md` observed in reverse: WEAK-multivariate-lift feature REDIRECTS attention to a different per-symbol carrier at higher-than-screen budget). C3 portfolio importance rank **6/15** at 7.1% of top — NOT fully INERT (TRX rank 1/15), but below the /025 PROMISING-feature benchmark (rank ≤ 5, gain ≥ 30% of top). Critic FINAL `80caafd` — single Critic round + one QR-response round (4 clarifications); all 8 checks evaluated; OVERALL=EXPLORATION-NEGATIVE catastrophic; the broader `value × sign(vol-regime-classifier)` Category-2 composed-feature lineage is CLOSED on the BCH/LDO/TRX universe at single-seed n_trials=35 EXPLORATION budget by QR Round-2 + Critic concurrence (the Critic's broader-closure lean adopted by QR).

**Date**: 2026-05-20
**Type**: EXPLORATION (cycle-6 slot #9 of 10; iter-v3/119 is the 10th and final EXPLORATION slot; iter-v3/120 is the mandatory cycle-6 CONFIRMATION) — ran a full Phase 1–8 (EDA + brief + Phase-5.5 Engineer gate + backtest + Critic preliminary + QR response + Critic FINAL), classified at Phase 7.5.
**Verdict**: **EXPLORATION-NEGATIVE catastrophic.** The C3 composed-feature hypothesis (a vol-regime-conditioned ema-spread composite at the slower ~67-day regime timescale lifts the universe-aggregate IS monthly Sharpe materially above the /060 anchor at +0.8325) is FALSIFIED at production scale on the BCH/LDO/TRX cohort. Section-8 Criterion 1a fires immediately on the first-match-wins ladder (IS Sharpe Δ catastrophic). The brief Section 4 modal band miss is −0.50+ on the IS axis. The /025 PROMISING-feature benchmark (the only prior successful engineered-feature precedent in v3) is NOT cleared — C3's portfolio rank 6/15 misses the rank ≤ 5 target by one position AND C3's 7.1% of leading-feature importance is below the 30% of top threshold the /025 baseline cleared on all 3 symbols at the EDA's depth-4 LightGBM screen.
**Decision**: **NO-MERGE.** BASELINE_V3.md UNCHANGED — canonical **`v0.v3-059`** (IS monthly Sharpe **+1.0894** / OOS monthly Sharpe **+0.5791**, 10-seed CONFIRMATION). An EXPLORATION never updates BASELINE_V3.md regardless of outcome (the BASELINE update policy is restricted to CONFIRMATION verdicts that STRICTLY BEAT prior baseline on BOTH IS and OOS Sharpe; an EXPLORATION-NEGATIVE catastrophic cannot advance to the /120 CONFIRMATION bundle as a signal-discovery ingredient). `v0.v3-118` is a closeout marker only.
**Branch**: `iteration-v3/118`

---

## 1. Setup — the axis (brief reference)

iter-v3/118 advances to the **NEW engineered-feature family axis** per the /117 closeout Recommendation 1 (the only LIVE feature axis remaining in the cycle-6 menu after the candle-frequency closure at /117). The cycle-6 axis menu state at /117 closeout:

| Cycle-6 axis | Status at end of /117 | State at end of /118 |
|---|---|---|
| Universe / symbol selection | CLOSED at /110, /111 NEGATIVE | unchanged — CLOSED |
| Pooled-vs-per-symbol architecture | CLOSED at /112 NEGATIVE | unchanged — CLOSED |
| Multi-frequency features on 8h | CLOSED at /113 NEGATIVE | unchanged — CLOSED |
| Risk management (R-layer) | CLOSED at /114 NEGATIVE | unchanged — CLOSED |
| Labeling architecture | CLOSED at /115 NEGATIVE | unchanged — CLOSED |
| Exit-layer / trade-construction | PROMISING-MECHANICAL at /116 (no_confirm) | unchanged — bundled at /120 single-component |
| Candle frequency | CLOSED at /117 catastrophic NEGATIVE | unchanged — CLOSED |
| NEW engineered feature family at 8h | LIVE per /117 § 8.1 | NARROW `value × sign(vol-regime-classifier)` CLOSED at /118; other engineered lineages remain LIVE |
| Per-symbol XGBoost-with-categorical | LIVE per /117 § 8.1 (with imbalance-magnitude caveat) | unchanged (DEFER — claim ground removed by /117 candle-frequency closure) |

The chosen /118 candidate (the EDA's top-pick from a 6-candidate screen) is the C3 composed feature:

```
C3 = ema_signed_volregime = ema_spread_atr_20 × sign(range_realized_vol_50 − rolling_median(range_realized_vol_50, 200))
```

This is on the `regime_momentum_signed_5d` (/025 PROMISING) algebraic-form lineage — a Category-2 composed feature (value × regime-sign multiplied through a 2-state sign function), structurally equivalent in form to the /025 baseline-stack feature but with a STRUCTURALLY DIFFERENT regime classifier (vol-regime via rolling-median split, not hurst-regime via 0.5 threshold).

**Brief reference**: `briefs-v3/iteration_v3-118/research_brief.md`, commit `26dd346`. Hand-chosen design parameters declared per `feedback_v3_brief_parameter_provenance.md` Section 0:
- Rolling-median window = **200 8h bars** (~67 calendar days). Rationale: matches the longest rolling-window primitive in TOP_N (`hurst_200`, `atr_pct_rank_200`); a regime classifier should be slower than the value primitive it conditions; 200 bars is the v3 canonical "long-horizon regime" timescale. NOT swept; no IS-only sweep table generated.
- Threshold offset = **0.0** (median = reference). Inherent to the rolling-median construction; not a tunable scalar.
- Sign convention = **+1 if realized_vol > median (high-vol regime); −1 if < median**. Inherent to `sign(x − median)`.
- Primitive lookbacks INHERITED from V3_FEATURE_COLUMNS_TOP_N (the 14-feature anchor): `ema_spread_atr_20` = 20-bar EMA span / 14-bar ATR scaling; `range_realized_vol_50` = 50-bar rolling std on `log(high/low)`.

**EDA reference**: committed at SHA `60a45e8` (`analysis/iteration_v3-118/`, 9 result tables T1–T9 + synthesis) BEFORE the brief per `feedback_v3_axis_selection_quant_discipline.md` and the auditable temporal fence. The EDA returned a GO verdict: C3 was the BEST candidate in the 6-candidate screen on the production-relevant T9 POOLED multivariate-lift criterion (+0.0081 vs the closest competitor C4 at +0.0010 — an 8× edge per `feedback_v3_engineered_features_proven.md`), AND the only candidate clearing the T5 multivariate-importance gain ≥ 30% bar on all 3 symbols (depth-4 LightGBM screen at ranks 8–10 with gain 38–63%), AND clearing the T2 Linear-Redundancy Pre-Falsifier (R²=0.196 vs primitives, max|corr|=0.21 — clean PASS with no carve-out needed). The EDA's per-symbol T9 lifts (BCH −0.0039; LDO −0.0106; TRX +0.0082) were pre-registered as the per-symbol asymmetry signature — and used to pre-register Section-7 Mode 3 (PROMISING-PARTIAL TRX-led).

**Auditable temporal fence**: every script in `analysis/iteration_v3-118/` asserts `close_time < OOS_CUTOFF_MS = 1742774400000`; 0 OOS-leaked rows across BCH (5483/0), LDO (2497/0), TRX (5425/0).

**Pre-registered Section 4 explicit falsifier** (modal band miss → catastrophic): OOS Δ < −0.50 AND IS Δ < −0.20 → FALSIFIED. The observed IS Δ = −0.4543 < −0.20 (catastrophic); the observed OOS Δ = −0.2904 > −0.50 (catastrophic IS leg fires; OOS leg misses). The Section-8 first-match-wins Criterion 1a (IS Δ < −0.20 alone) fires immediately — the verdict does NOT require the symmetric two-sided falsifier.

---

## 2. Implementation — setup commits, engineering commit, tests

Sequenced setup chain (3 commits before backtest), then 1 engineering report commit and 3 Critic-cycle commits:

| SHA | Type | Description |
|---|---|---|
| `60a45e8` | analysis | engineered-feature axis EDA (9 tables T1-T9 + synthesis; 6-candidate screen → top pick C3) |
| `26dd346` | docs | research brief — 10 sections; Section 3.5 enumerates 6 implementation changes + Change 0 advisory |
| `602c60f` | docs | Phase 5.5 Engineer gate PASS (`phase5p5_gate.md`) |
| `0ac25c8` | feat | C3_ema_signed_volregime composed feature + runner setup (the substantive code change — `src/crypto_trade/features_v3/engineered_v3.py:778-831` `compute_ema_signed_volregime` + `V3_FEATURE_COLUMNS_TOP_N` 14→15 + `n != 15` guard + parquet regen + unit test + integration test + ITERATION_LABEL/MODEL_SPECS housekeeping) |
| `e086a32` | analysis | engineering report + backtest results (`reports-v3/iteration_v3-118/`) |
| `edaaeed` | docs | QR response to Critic preliminary (4 clarifications) |
| `80caafd` | docs | Critic FINAL review — EXPLORATION-NEGATIVE catastrophic |

**Code summary (commit `0ac25c8`)**:
- `src/crypto_trade/features_v3/engineered_v3.py:778-831`: NEW function `compute_ema_signed_volregime(df, ema_spread_window=20, atr_window=14, rv_window=50, median_window=200) -> pd.Series`. Past-only by construction (trailing rolling-median on `range_realized_vol_50`; reuses past-only `ema_spread_atr_20` and `range_realized_vol_50` primitives). GROUP_REGISTRY ordering in `features_v3/__init__.py:71-119` places `momentum_accel` and `tail_risk` BEFORE `engineered_v3` so dependencies are satisfied without dispatch-order leakage.
- `src/crypto_trade/features_v3/__init__.py`: `V3_FEATURE_COLUMNS_TOP_N` extended 14 → 15 (adds `"ema_signed_volregime"` as 15th element AFTER `regime_momentum_signed_5d` per brief spec at line 213).
- `run_baseline_v3.py`: feature-count guard updated `n != 14` → `n != 15` at line 432-440; ITERATION_LABEL="v3-118" at line 131; MODEL_SPECS prefixed "v3-118-" at lines 198-200; accretion guard entry `("REQUIRED_GAP", REQUIRED_GAP, 66)` unchanged (8h single-frequency baseline).
- Parquet regeneration: BCH/LDO/TRX/BTC 8h parquets regenerated with `ema_signed_volregime` column (15th) present and non-NaN on last 100 IS rows.
- `tests/test_engineered_v3_features.py` (extended): `test_compute_ema_signed_volregime_past_only` adversarial test on 250-bar synthetic panel — confirms past-only invariant.
- `tests/test_run_baseline_v3_integration.py` (extended): integration test asserts (1) `V3_FEATURE_COLUMNS` includes `ema_signed_volregime`; (2) parquet column non-NaN on last 100 IS rows; (3) runner's `n_features == 15` guard fires correctly; (4) past-only unit test passes.

**Knobs UNCHANGED vs /059-canonical** (verified against accretion guard output in run.log):
V3_MODELS = BCH/LDO/TRX; REQUIRED_GAP = 66; label_mode = triple_barrier; ATR multipliers = (2.0, 1.0); zscore_threshold = 2.0; adx_threshold = 20.0; enable_no_confirm_exit = False (REVERTED from /116); enable_per_symbol_drawdown_brake = False; ENSEMBLE_SIZE = 3 (EXPLORATION-mode); n_trials = 35; bar-interval = 8h (default; /117 24h-multi-offset machinery present but dormant).

**Wall-clock**: 0.72h (well under the 2h cycle-6 EXPLORATION cap). Hardware: WSL2 Linux x86_64.

**Sacred constants verified**: `OOS_CUTOFF_DATE = 2025-03-24` UNCHANGED, `training_months = 24` UNCHANGED.

---

## 3. Results — Phase 7 OOS evaluation (first look)

This is the QR's first look at the iter-v3/118 OOS reports.

### 3.1 Headline metrics (`reports-v3/iteration_v3-118/comparison.csv`)

| Metric | In-Sample | Out-of-Sample | OOS/IS ratio |
|---|---:|---:|---:|
| **monthly_sharpe** | **+0.3782** | **−0.1501** | −0.3968 |
| daily_sharpe | +0.8336 | −0.3471 | −0.4163 |
| max_drawdown | 43.91% | 28.91% | 0.6584 |
| profit_factor | 1.1264 | 0.9580 | 0.8505 |
| win_rate | 32.97% | 39.22% | 1.1895 |
| n_trades | 182 | 102 | 0.5604 |
| total_pnl | +27.13% | −5.51% | −0.2030 |
| monthly_calmar | +0.6179 | −0.1905 | −0.3083 |
| weighted_pnl_total | +27.13% | −5.51% | −0.2030 |

vs the /060 EXPLORATION-mode anchor (IS +0.8325 / OOS +0.1403):
- **IS Δ = −0.4543** (catastrophic — 2.27× the Criterion 1a NEGATIVE-catastrophic threshold of −0.20)
- **OOS Δ = −0.2904** (catastrophic-tier negative — exceeds the modal lower bound at −0.05 by ~6× but does NOT reach the Section-4 −0.50 floor)

vs the /059 CONFIRMATION canonical baseline (IS +1.0894 / OOS +0.5791):
- IS Δ = −0.7112; OOS Δ = −0.7292 — large negative regression on both axes.

### 3.2 Statistical significance block

| Metric | /118 Value | Gate threshold | Gate status |
|---|---|---|---|
| DSR | 0.0000 | > 0.95 | FAIL |
| PBO | 0.0885 | < 0.40 | PASS |
| PSR | 0.0482 | > 0.95 | FAIL |
| frac_positive_paths | 0.6444 (29/45) | ≥ 0.55 | PASS |
| n_trials | 315 | — | — |
| n_effective_trials | 19 | — | — |
| CPCV path Sharpe Q25 / Q50 / Q75 | −0.2430 / +0.3351 / +0.8378 | — | — |

Per `feedback_v3_dsr_mode_artifact.md`, DSR=0.0/PSR=0.0482 at EXPLORATION-mode (n_trials=315, E[max_SR]≈2.6) are regime-specific artifacts NOT comparable to CONFIRMATION-mode (n_trials=1500+, E[max_SR]≈3.4). For TYPE=EXPLORATION, Check 3 DSR/PSR FAILs are informational only — only the PBO axis is BLOCK-triggering, and PBO PASSES decisively. The verdict-determinative BLOCK is Section-8 Criterion 1a, not Check 3.

### 3.3 Per-symbol IS attribution (`reports-v3/iteration_v3-118/in_sample/per_symbol.csv`)

| Symbol | Trades | WR | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 82 | 42.7% | **+52.61%** | +0.64% | **+157.91%** |
| TRXUSDT | 85 | 32.9% | −5.49% | −0.06% | −16.48% |
| LDOUSDT | 15 | 26.7% | −13.80% | −0.92% | −41.43% |

### 3.4 Per-symbol OOS attribution (`reports-v3/iteration_v3-118/out_of_sample/per_symbol.csv`)

| Symbol | Trades | WR | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|
| TRXUSDT | 42 | 50.0% | +22.00% | +0.52% | −244.02% |
| BCHUSDT | 45 | 37.8% | +2.18% | +0.05% | −24.18% |
| LDOUSDT | 15 | 20.0% | **−33.20%** | −2.21% | **+368.20%** |

### 3.5 C3 feature importance ranks (`reports-v3/iteration_v3-118/in_sample/model_importance_last_month_*.csv`)

**Portfolio (aggregated across BCH/LDO/TRX, last walk-forward month)** — full top-15 ranking:

| Rank | Feature | Importance | Share (%) |
|---|---|---:|---:|
| 1 | max_dd_window_50 | 535.7 | 9.7 |
| 2 | ret_skew_200 | 515.0 | 9.3 |
| 3 | range_realized_vol_50 | 496.0 | 9.0 |
| 4 | vwap_dev_20 | 428.0 | 7.8 |
| 5 | ret_kurt_50 | 423.7 | 7.7 |
| **6** | **ema_signed_volregime (C3)** | **390.3** | **7.1** |
| 7 | hurst_100 | 364.7 | 6.6 |
| 8 | ret_kurt_200 | 364.0 | 6.6 |
| 9 | ret_skew_50 | 354.7 | 6.4 |
| 10 | hurst_diff_100_50 | 333.7 | 6.0 |
| 14 | regime_momentum_signed_5d | 227.7 | 4.1 |
| 15 | sym_vs_btc_ret_7d | 188.0 | 3.4 |

**C3 per-symbol rank (last month)**:
- BCH: rank 11/15 (importance 56.7, 4.5% of top)
- LDO: rank 13/15 (importance 128.7 — higher raw but 13th by rank)
- TRX: rank **1/15** (importance 205.0 — top feature for TRX; consistent with EDA T9 TRX-led lift but did NOT translate to TRX IS positive PnL)

### 3.6 IC matrix and ADF (`reports-v3/iteration_v3-118/ic_matrix.csv`, `adf_test.csv`)

- C3's max |IC| with any existing feature = **0.2119** (with `sym_vs_btc_ret_7d`) — well below 0.70 threshold. EDA T2 R²=0.196 (max|corr|=0.21 POOLED) reproduces in production at max|IC|=0.21. C3 introduces NO new collinearity risk.
- The one pre-existing high-IC pair (`vwap_dev_20 × regime_momentum_signed_5d` at 0.7642) is unchanged from /059/060 baseline — confirmed not worsened by C3 addition.
- ADF: 2355 rows total; 1941 (82.4%) stationary at p<0.05; C3 has 157 rows, 138 (87.9%) stationary — above portfolio mean. At IS-end month 2025-03, C3 decisively stationary across all 3 symbols (BCH ADF=−7.22 p=0.0; LDO ADF=−7.76 p=0.0; TRX ADF=−6.32 p=0.0). The `sign(.)` regime composition produces a bounded ±1 multiplier applied to bounded `ema_spread_atr_20` — structurally guarantees stationarity once warmed up.

### 3.7 OOS-trade-rate

OOS trades = 102 across 14 OOS months ≈ 7.3 trades/month — below the v3 informational trade-rate floor (≥10 trades/month OOS) but EXPLORATION mode does not enforce the floor. No zero-trade months in OOS (verified from `out_of_sample/trades.csv`).

---

## 4. Critic Review Summary (Phase 7.5)

Critic FINAL at commit `80caafd` — single Critic preliminary round + one QR response round (4 clarifications); all 8 checks evaluated.

### 4.1 Per-Check status

| # | Check | Status | Diagnostic |
|---|---|---|---|
| 1 | Look-Ahead Audit | **PASS** | `compute_ema_signed_volregime` at `engineered_v3.py:778-831` past-only by construction. Trailing rolling-median window on `range_realized_vol_50` (consumes only bars t−199..t at bar t). Both upstream primitives audited at source as past-only (`tail_risk_v3.py:42` for rv_50; `momentum_accel_v3.py:57` for ema_spread). GROUP_REGISTRY ordering satisfies dependencies without dispatch-order leakage. Phase 5.5 gate confirmed 0 OOS-leaked rows (BCH 5483/0, LDO 2497/0, TRX 5425/0). |
| 2 | Embargo Width | **PASS** | REQUIRED_GAP = 66 = (21+1)×3 for 8h single-frequency with 21-bar triple-barrier timeout and 3-symbol universe. Verified at runner accretion guard at `run_baseline_v3.py:1095`. The /117 panel-aware CV-gap defect (conditional on multi-offset architecture) is dormant — /118 uses single-frequency 8h. The /058 walk-forward lookahead-bias FIX (commit `e149e9d`) carrying `train_end_ms = test_start_ms - embargo_ms` verified present in `walk_forward.py:113`. |
| 3 | Multiple-Testing Correction | **FAIL (informational for EXPLORATION)** | DSR=0.0 / PSR=0.0482 — EXPLORATION-mode structural artifacts. PBO=0.0885 PASS; frac_positive_paths=0.6444 PASS. Per `feedback_v3_dsr_mode_artifact.md`, DSR/PSR axis FAILs are informational only for TYPE=EXPLORATION. The verdict-determinative BLOCK is Section-8 Criterion 1a, not Check 3. |
| 4 | IC Correlation | **PASS** | ic_matrix.csv is 15×15. C3's max |IC| = 0.2119 with sym_vs_btc_ret_7d (well below 0.70). C3's IC with the value primitive `ema_spread_atr_20` = 0.068 (the low value despite shared primitive confirms `sign(.)` carries the bulk of variance, not the primitive). EDA T2 R²=0.196 reproduces in production at max|IC|=0.21. No new collinearity risk. |
| 5 | ADF Stationarity | **PASS** | 2355 rows; 82.4% stationary at p<0.05. C3 at 87.9% stationary — above mean. Early-window NaN ADF rows are during the 200+50-bar C3 warm-up period (NaN-by-design). At IS-end month 2025-03, C3 decisively stationary across all 3 symbols. |
| 6 | Pareto Dominance | **N/A** | Single-seed EXPLORATION mode (3 outer seeds via EXPLORATION_ENSEMBLE_SIZE=3 = ENSEMBLE_SEEDS[0:3], the unified seed-42 lineage). Pareto-dominance check applies only to CONFIRMATION-mode 10-seed validation. Pareto evaluation deferred to /120 CONFIRMATION. |
| 7 | Reproducibility | **PASS** | Commit SHA `0ac25c8` stamped in engineering report Section 1 and matches `git rev-parse HEAD`. `feature_columns` explicitly the 15-element `V3_FEATURE_COLUMNS_TOP_N` enforced by `n != 15` guard. ENSEMBLE_SEEDS literal tuple at runner line 103. Trade arithmetic spot-check on OOS trades verified consistent. Integration test PASS. |
| 8 | Hypothesis-Implementation Alignment | **PASS (minor doc-string lag noted)** | All 6 brief Section 3.5 changes + Change 0 advisory delivered per engineering report. Runner pre-flight assertion at `run_baseline_v3.py:2929-2947` still contains cosmetic string "iter-v3/117" in its error messages — documentation lag, not a logic defect; the assertion still validates `enable_no_confirm_exit is False`, `no_confirm_trigger_atr == 0.50`, and `no_confirm_k_candles == 4` (all PASSING). No scope creep, no hypothesis-faking. |

### 4.2 OVERALL line

OVERALL: **EXPLORATION-NEGATIVE catastrophic** — Section-8 Criterion 1a fires decisively (IS Sharpe Δ −0.4543 vs /060 anchor, 2.27× the −0.20 threshold).

### 4.3 QR Round-2 STAND BY VERDICT

QR's Round-2 position was a clean concession on the EXPLORATION-NEGATIVE catastrophic classification with no contestation of any of the 8 PRELIMINARY check statuses. The 4 clarifications received substantive Critic-CONCURRED answers:

1. **Axis closure scope** → QR adopts the Critic's broader-closure lean: the entire `value × sign(vol-regime-classifier)` Category-2 composed-feature lineage is CLOSED on the BCH/LDO/TRX universe at single-seed n_trials=35 EXPLORATION budget, not only the specific C3 = ema_spread × sign(rv_50 − rolling_median_200) composite. The variants the Critic flagged as potentially LIVE within the narrow lineage (rolling-median-100, expanding-median, alternate vol estimators, alternate value primitives) would all parametrize the same algebraic form against the same production loss surface that just produced the inversion; retrying within the narrow lineage at single-seed EXPLORATION budget would be expected to produce another instance of the inversion against a different per-symbol carrier. Reopening requires either (a) multi-seed CONFIRMATION-budget validation OR (b) a different regime-classifier family.

2. **Mode 3 inversion mechanism** → QR identifies it as PRIMARILY single-seed-lottery + multivariate-interaction-cancellation per `feedback_v3_inert_features_at_higher_budget.md` (observed in reverse direction: WEAK-multivariate-lift feature REDIRECTS attention to a different per-symbol carrier at 15-dim Optuna scale), with a secondary intrinsic-property channel from C3's slow ~67-day regime classifier × fast ~6-day value primitive product geometry. QR explicitly does NOT recommend a separate multi-seed C3 experiment (expectation: would ATTENUATE inversion but stay NEGATIVE; ~5h CONFIRMATION cost to confirm what mechanistic reasoning already establishes). Critic CONCURRED — NO-RECOMMENDATION on a separate multi-seed C3 experiment is methodologically tight.

3. **/119 axis recommendation** → QR commits to OPTION (a) ANOTHER engineered-feature lineage on STRUCTURALLY DIFFERENT primitives, with explicit reasoning rejecting (b) per-symbol XGBoost-with-categorical (the high-imbalance claim ground was removed when /117 closed candle-frequency at 8h) and (c) out-of-the-box (too vague to commit at /118 closeout). QR proposed ≥4 candidates from 2+ orthogonal categories (volume, cross-asset BTC, tail/higher-moment regime, microstructure) AND a NEW EDA gate: Single-Symbol-Carrier RISK pre-Falsifier if T9 per-symbol asymmetry > 2× POOLED magnitude. Critic CONCURRED — this is the right axis pivot AND the new SSC-RISK gate is a direct learning from /118's failure mode.

4. **/120 CONFIRMATION composition** → QR confirmed /120 is VALID as a single-component CONFIRMATION of /116 no_confirm vs /059 canonical, citing iter-v3/018 precedent (single-component validation of /013 drop-MKR; FAILED at multi-seed — methodologically clean closeout regardless). /119 NEGATIVE outcome does NOT block /120 from running with /116 alone; /119 PROMISING would simply add a second component. Critic CONCURRED — iter-v3/018 single-component CONFIRMATION precedent is valid and four-cell decision tree produces meaningful cycle-6 closeout in all branches.

---

## 5. Failure-Mode Analysis — per-symbol role-reversal, single-seed-lottery + multivariate-interaction-cancellation diagnostic

### 5.1 Per-symbol role-reversal vs EDA T9 prediction

The EDA T9 per-symbol multivariate-lift was the controlling production-relevance signal in the 6-candidate screen (per `feedback_v3_engineered_features_proven.md`'s observation that ENGINEERED features outperform off-the-shelf indicators with 51% top importance share). For C3:

| Symbol | EDA T9 multivariate-lift | Pre-registered Mode 3 prediction | Production IS net_pnl_pct | Production IS WR |
|---|---:|---|---:|---:|
| BCH | **−0.0039** | NEGATIVE PnL Δ < −1.0% predicted | **+52.61%** | 42.7% |
| LDO | **−0.0106** | NEGATIVE PnL Δ < −1.0% predicted | **−13.80%** | 26.7% |
| TRX | **+0.0082** | POSITIVE carrier (PnL Δ ≥ +2.0%) | **−5.49%** | 32.9% |
| POOLED | +0.0081 | IS Sharpe Δ ∈ [+0.05, +0.30] modal | IS Sharpe Δ = **−0.4543** | — |

The EDA correctly identified per-symbol asymmetry but MIS-IDENTIFIED the carrier symbol. BCH (predicted negative) emerged as the sole IS positive carrier. TRX (predicted positive) was the largest IS negative (with the highest C3 importance rank — 1/15). LDO (predicted negative) realized as predicted but at catastrophic magnitude. The cross-symbol role-reversal between BCH and TRX is the diagnostic signature.

### 5.2 Single-seed-lottery + multivariate-interaction-cancellation diagnostic

The diagnostic mechanism (per `feedback_v3_inert_features_at_higher_budget.md` observed in reverse direction):
- The EDA's T9 multivariate-lift was measured by a depth-4 single-tree LightGBM at n_trials=35 in 14+1 feature space — a structurally different optimizer than the production walk-forward Optuna at depth 3-5 ensembled over 3 seeds × 105 walk-forward training-month rebuilds.
- At production scale, Optuna's 15-dim search at n_trials=35 single-seed lands on a TRX-favorable hyperparameter point that maximizes C3's allocation to TRX (importance rank 1/15 at 205.0 = the single largest TRX importance) at the cost of TRX's incumbent 14-feature edge.
- The collapse magnitude (IS Sharpe Δ = −0.4543) is DISPROPORTIONATE to C3's 7.1% portfolio importance share — the signature of a feature corrupting the gradient-boosting loss surface, not just adding noise. C3 is a SLOW (~67-day) regime indicator × FAST (~6-day) value primitive — within the 21-bar triple-barrier horizon, the regime classifier rarely flips, so C3 is dominated by the value-primitive variance during long stretches where regime sign is stable. This means C3 carries information LARGELY ALREADY ENCODED in `ema_spread_atr_20` + `range_realized_vol_50` independently when the model sits at depth ≥ 2 — exactly the iter-v3/053 hurst_drift_50_200 mechanism (`feedback_v3_lr_pf_methodology.md`: "trees can use derived features for EFFICIENCY without that allocation reflecting NEW signal").

### 5.3 /025 PROMISING benchmark fail (rank ≤ 5, gain ≥ 30% of top)

C3 was the only EDA candidate clearing the /025 PROMISING-feature benchmark (rank 8-10/15, gain 38-63% of top) at the depth-4 LightGBM screen. At production walk-forward LightGBM:

- C3 portfolio rank = **6/15** (misses ≤ 5 target by 1 position)
- C3 portfolio share = **7.1% of top** (well below 30% threshold; would require ~160 importance vs top-feature's 535.7 to clear 30%)

The EDA's depth-4 single-tree screen at 14+1 feature space gave a different distribution than the production runner's portfolio aggregate. The /025 PROMISING benchmark MUST be met at PRODUCTION scale, not at EDA scale, to count as a PROMISING-feature precedent. C3 does not clear.

### 5.4 Importance NOT zero — diagnostic of corruption not silence

Unlike the /085/086 "rank 14/15, near-zero gain" dead pattern, C3 IS allocated importance (rank 6/15 portfolio, rank 1/15 TRX). The failure mechanism is NOT at the importance-allocation layer (the model uses C3) but at the multivariate-interaction layer (C3's allocation corrupts existing incumbents' signal allocation). This is structurally different from the v3 INERT-feature dead patterns (iter-v3/015 tbr_zscore_30; iter-v3/019 funding_rate_zscore_30; iter-v3/024 btc_funding_rate_zscore_30) where the feature ranked 14/14 or 15/15 — those were silent failures of model uptake. /118 is a noisy failure of multivariate-interaction. The mechanism class is new in v3 history and warrants explicit documentation.

### 5.5 Frozen-baseline cross-symbol regression check

Per `feedback_v3_single_seed_frozen_baseline.md` (iter-v3/020/021/022): single-seed=42 EXPLORATION produces bit-identical rosters for non-target symbols across consecutive iterations. However, /118 adds C3 to ALL THREE symbols (BCH, LDO, TRX simultaneously) — there are no "non-target" symbols frozen at /060 baseline. The per-symbol importance table shows C3 at rank 1 for TRX, rank 11 for BCH, rank 13 for LDO — three different hyperparameter solutions. The frozen-baseline pattern does NOT apply here because all three symbols received C3 and ran Optuna independently with a shared seed lineage. The cross-symbol divergence reflects genuine per-symbol hyperparameter sensitivity to C3, not a frozen-baseline artifact.

---

## 6. Closure Scope — broader `value × sign(vol-regime-classifier)` Category-2 lineage CLOSED at /118

Per QR Round-2 Clarification 1 + Critic concurrence (`80caafd`):

**The broader `value × sign(vol-regime-classifier)` Category-2 composed-feature lineage is CLOSED on the BCH/LDO/TRX universe at single-seed n_trials=35 EXPLORATION budget.**

This is broader than the narrow C3 specific (median window 200, vol estimator range-realized, value primitive ema-spread). The variants the Critic flagged as potentially LIVE within the narrow lineage — rolling-median-100, expanding-median, alternate vol estimators (Parkinson, Garman-Klass, Rogers-Satchell), alternate value primitives (RSI-spread, MACD-histogram-spread, bb-position) — would all parametrize the same algebraic form against the same production loss surface that just produced the inversion. The argument for re-trying within the narrow lineage would require a NEW mechanism to dissolve the inversion. The Critic's third diagnostic names the inversion as a STRUCTURAL property of the single-seed + 15-dim-Optuna combination, not a property of the specific median window or value primitive. Retrying within the narrow lineage at single-seed EXPLORATION budget would be expected to produce another instance of the inversion against a different per-symbol carrier — i.e., information-theoretic ZERO marginal value.

**Closed at /118 catalog level**: the entire `value × sign(vol-regime-classifier)` Category-2 composite family, at single-seed EXPLORATION budget on the BCH/LDO/TRX universe.

**Still LIVE within the broader engineered-feature axis**: composite families on STRUCTURALLY DIFFERENT regime classifiers (e.g., realized-skew sign, MACD-histogram sign, ATR-percentile-rank sign, autocorrelation sign at different lags) AND composite families on STRUCTURALLY DIFFERENT value primitives that are themselves orthogonal to the EMA-spread family (e.g., volume-based primitives, microstructure primitives, cross-asset primitives). The /025 PROMISING precedent — `regime_momentum_signed_5d = ret_5d × sign(hurst_100 − 0.5)` — used hurst as the regime classifier (NOT vol; vol-regime is what /118 just closed). The hurst-regime branch has the /025 precedent and is occupied. Other regime-classifier families remain unexplored.

**Future re-opening of the narrow `value × sign(vol-regime-classifier)` lineage requires either**:
(i) multi-seed CONFIRMATION-budget validation (≥10-seed unified ensemble at n_trials=50+) — the expectation per QR Clarification 2 is that the inversion would ATTENUATE but the IS Sharpe Δ would stay NEGATIVE; not worth the ~5h CONFIRMATION budget on closure-already-supported evidence, OR
(ii) a different regime-classifier family on a different problem (a different universe, a different label estimand, etc.) — a candidate for cycles beyond cycle-6.

The Critic noted **C3 code defect retention KEEP** — `compute_ema_signed_volregime` STAYS in `engineered_v3.py` AS-IS (code-museum value; preserves implementation in case the lineage is ever re-opened under a different protocol). HOWEVER C3 MUST NOT be in `V3_FEATURE_COLUMNS_TOP_N` for /119 onward — the /119 setup-commit MUST REVERT `V3_FEATURE_COLUMNS_TOP_N` from 15 elements back to 14 (drop `ema_signed_volregime`). The /119 runner `n != 15` guard reverts to `n != 14`.

---

## 7. Catalog entry

Per Critic Recommendation 4 + the standard schema, appended to `briefs-v3/exploration_catalog.md`:

```
| iter-v3/118 | 2026-05-20 | NEW engineered-feature lineage (Category-2 composed: ema_spread × sign(vol-regime-classifier)) | −0.4543 | −0.2904 | EXPLORATION-NEGATIVE catastrophic | NO |
```

**Cycle-6 catalog state (after /118)**:
- 8 NEGATIVE: /110 (label-confound), /111 (clean), /112 (pooled architecture), /113 (multi-frequency on 8h), /114 (risk management with Check-1 FAIL), /115 (coherent horizon-exit labeling), /117 (24h-multi-offset catastrophic), **/118 (Category-2 vol-regime composed-feature catastrophic)**
- 1 PROMISING-MECHANICAL: /116 (no_confirm early-exit primitive — strictly-accretive component decision for the /120 CONFIRMATION bundle)
- 1 EXPLORATION slot remaining: /119
- /120 = mandatory cycle-6 CONFIRMATION

---

## 8. Next Iteration Ideas — /119 axis recommendation + /120 CONFIRMATION setup

Cycle 6 has 1 EXPLORATION slot remaining (/119) before the mandatory /120 CONFIRMATION. Per QR Round-2 Clarification 3 + Critic concurrence, the /119 axis is COMMITTED at /118 closeout.

### 8.1 The /119 axis: NEW engineered-feature lineage on STRUCTURALLY DIFFERENT primitives

**Mandate**: per Critic Recommendation 1 + QR Clarification 3, /119 runs another engineered-feature EXPLORATION drawn from the orthogonal-primitive list (the LIVE branches within the broader engineered-feature axis after /118's narrow-lineage closure). The /119 QR makes the specific candidate selection under `feedback_v3_axis_selection_quant_discipline.md` (EDA-driven discipline, committed `analysis/iteration_v3-119/*.py` BEFORE the brief).

**Four LIVE candidate categories (≥4 candidates from 2+ orthogonal categories)**:

| Category | Primitive examples | Composite candidate forms (illustrative — /119 QR adjudicates exact form) |
|---|---|---|
| **(i) Volume-based primitives** | OBV, MFI (Money Flow Index), CMF (Chaikin Money Flow), volume-weighted ema-spread | `obv_zscore_50 × sign(volume_pctchg_10)`; `mfi_14 × sign(close − vwap_20)`; `cmf_14 × sign(volume_zscore_50)` |
| **(ii) Cross-asset BTC primitives** | BTC-correlation regime, sym/BTC ratio momentum, BTC-funding alignment | `sym_vs_btc_ret_14d × sign(btc_ret_30d)`; `btc_corr_50 × sign(btc_realized_vol_30 − rolling_mean_200)`; `sym_funding_zscore × sign(btc_funding_zscore)` (subject to funding-rate data availability) |
| **(iii) Tail / higher-moment regime classifiers** | ret_skew, ret_kurt, max_dd_window | `ret_5d × sign(ret_skew_50)`; `ema_spread_20 × sign(ret_kurt_50 − rolling_median_200)`; `vwap_dev_20 × sign(max_dd_window_50 − rolling_quantile_75)` |
| **(iv) Microstructure-derived primitives** | range_realized_vol-vs-OHLC vol ratio, body/range ratio, gap ratio | `body_range_ratio × sign(range_realized_vol_50 − atr_pct_rank_200)`; `gap_ratio × sign(volume_zscore_50)` |

**Specific recommendation for /119 QR seed-EDA**: prioritize candidates from category (i) volume-based and category (iii) tail/higher-moment, on the following grounds:

- Category (ii) cross-asset BTC has the strongest prior empirical history in v3 (the existing `sym_vs_btc_ret_7d` feature in V3_FEATURE_COLUMNS_TOP_N), but the cross-asset composed-feature space was explored at iter-v3/019 (`funding_rate_zscore_30`), iter-v3/023 (funding retest), iter-v3/024 (`btc_funding_rate_zscore_30`) — all NEGATIVE on the importance INERT pattern. Cross-asset funding-rate composites are largely a dead branch; cross-asset BTC-regime composites without funding (e.g., btc_corr × btc_ret_regime) remain LIVE but are arguably a tighter prior space than (i) or (iii).
- Category (iv) microstructure is high-novelty (limited v3 history) but data availability is constrained (no L2 / order-book in v3 inventory); a microstructure-derived primitive must compose from OHLC-derivable quantities only.
- Categories (i) and (iii) are both first-time-in-cycle-6 territories with concrete primitive sets available in the V3 feature inventory (OBV, MFI, CMF features are computable from OHLCV; ret_skew, ret_kurt, max_dd_window are existing V3 primitives).

**New EDA gate /119 must include**: per QR Clarification 3 + Critic concurrence — the **Single-Symbol-Carrier RISK pre-Falsifier**. If the EDA's T9 per-symbol asymmetry exceeds 2× the POOLED magnitude (i.e., a single-symbol carrier dominates the POOLED signal — the /118 mechanism), file the candidate as **Single-Symbol-Carrier-RISK** and tighten the Section-4 Falsifier band accordingly. The /118 T9 per-symbol asymmetry signature was POOLED=+0.0081 but max-single-symbol |lift|=+0.0082 (TRX) — the asymmetry-to-pooled ratio was ~1.01× POOLED magnitude (just under the 2× threshold the new gate would set; in retrospect, a tighter gate would have caught /118 as Single-Symbol-Carrier-RISK). The /119 EDA should pre-register the 2× threshold and apply it explicitly.

**Closure-scope rejections for /119**: The /119 EDA MUST REJECT (a) any candidate using `sign(realized_vol − vol_threshold)` as the regime sign factor (per /118 broader-closure scope); (b) the /025 hurst-regime branch (occupied by `regime_momentum_signed_5d`); (c) any retry of the /015 (tbr_zscore_30), /019 (funding_rate_zscore_30), /023 (funding retest), /024 (btc_funding_rate_zscore_30) dead-paths. The /119 candidate must be a genuinely NEW lineage.

### 8.2 /120 CONFIRMATION setup: SINGLE-COMPONENT validation of /116 no_confirm vs /059 canonical at 10-seed

Per Critic Recommendation 2 + QR Clarification 4: /120 is a SINGLE-COMPONENT CONFIRMATION of the /116 no_confirm early-exit primitive against the /059 canonical baseline, at full unified 10-seed ensemble (ENSEMBLE_SIZE=5 inner × outer_seeds=2 = 10 models per cell per the v3 CONFIRMATION envelope; n_trials=35).

**Pre-registered /120 specs** (per Critic Recommendation 2 + the iter-v3/018 single-component CONFIRMATION precedent — single-component validation of /013 drop-MKR; FAILED at multi-seed, methodologically clean closeout regardless):

- **IS Sharpe band**: accommodating /116's regime-cost. /116 produced IS=+0.6246 (vs /059 IS=+1.0894) — an IS Sharpe decrement of −0.4648. The CONFIRMATION IS NEGATIVE floor should accept this regime-cost as part of the no_confirm mechanical bargain: **IS NEGATIVE floor at /059 IS − 0.50 = +0.59** (rather than the standard /059 IS − 0.10 = +0.99), since /116's mechanical cascade is expected to bear an IS cost that may NOT be a CONFIRMATION-FAIL signal. The CONFIRMATION question is whether the slot-freeing OOS cascade survives at multi-seed.
- **OOS Sharpe band**: must clear /059 OOS = +0.5791. /116 produced OOS=+1.1089 (Δ +0.5298 at 3-seed EXPLORATION). The CONFIRMATION OOS PASS gate is OOS ≥ +0.6791 (/059 OOS + 0.10), with the multi-seed mean.
- **Multi-seed cascade-attribution falsifier** (per /116 Critic Recommendation 3): if at 10-seed the per-symbol OOS net_pnl_pct Δ vs /059 is NOT broad-based positive across ≥ 2 of 3 symbols, RECLASSIFY as PROMISING-FALSIFIED-AT-CONFIRMATION (the no_confirm OOS lift dissolves at multi-seed; the cascade channel was a 3-seed-mode lottery).
- **Bundle composition** branches on /119 outcome:
  - If /119 is PROMISING (engineered-feature or other LIVE axis with positive IS+OOS Δ at single-seed EXPLORATION), /120 bundles BOTH /116 no_confirm AND the /119 result, with the caveat that mechanical and signal-discovery ingredients have different multi-seed-validation criteria per `feedback_promising_mechanical_subtype.md`.
  - If /119 is NEGATIVE, /120 bundles ONLY /116 no_confirm — the iter-v3/018 single-component CONFIRMATION precedent applies. Single-component validation is canonical, NOT a degenerate CONFIRMATION.

### 8.3 Cycle-6 closeout decision tree (post-/119 + /120)

| Branch | /119 outcome | /120 outcome | BASELINE_V3.md decision |
|---|---|---|---|
| 1 | PROMISING | /116 confirms + /119 confirms | UPDATE — both ingredients merge |
| 2 | NEGATIVE | /116 confirms at multi-seed | UPDATE — single-component no_confirm primitive merges |
| 3 | PROMISING | /116 does NOT confirm + /119 confirms | UPDATE — /119 finding only |
| 4 | NEGATIVE | /116 does NOT confirm at multi-seed | UNCHANGED — cycle 6 closes NO-MERGE; /116's apparent OOS lift dissolves at multi-seed (same dissolution as iter-v3/013 → /018) |

All four branches produce a meaningful cycle-6 closeout. The /119 axis search does NOT need to find another LIVE bundle candidate as a hard requirement — but if /119 succeeds, it adds the second cell of the decision tree's left branch.

---

## 9. Closeout

- **Verdict**: EXPLORATION-NEGATIVE catastrophic — Section-8 Criterion 1a fires (IS Sharpe Δ −0.4543 vs /060 anchor, 2.27× the −0.20 threshold).
- **Failure mechanism**: per-symbol role-reversal vs EDA T9 prediction (BCH ↔ TRX carrier flip); single-seed-lottery + multivariate-interaction-cancellation at n_trials=35 (15-dim Optuna scale); /025 PROMISING benchmark fail (rank 6/15 portfolio at 7.1% of top, vs ≤ 5 / ≥ 30%); importance NOT zero (corruption-class failure, not silent-failure-class).
- **Closure scope**: broader `value × sign(vol-regime-classifier)` Category-2 composed-feature lineage CLOSED on the BCH/LDO/TRX universe at single-seed n_trials=35 EXPLORATION budget. Narrower vol-classifier specifics (median window, vol estimator) subsumed by the broader closure. Reopening requires either (a) multi-seed CONFIRMATION-budget validation OR (b) a different regime-classifier family.
- **Code defect retention**: KEEP `compute_ema_signed_volregime` function in `engineered_v3.py` AS-IS (code-museum value); REMOVE from `V3_FEATURE_COLUMNS_TOP_N` at /119 setup-commit (15 → 14 elements; `n != 15` guard reverts to `n != 14`).
- **Decision**: NO-MERGE. BASELINE_V3.md UNCHANGED at `v0.v3-059`. Catalog updated. `v0.v3-118` tagged as closeout marker only.
- **/119 axis recommendation**: NEW engineered-feature lineage on STRUCTURALLY DIFFERENT primitives (per Critic Rec 1 + QR Clarification 3). Priority categories: (i) volume-based primitives (OBV/MFI/CMF-derived), (iii) tail/higher-moment regime classifiers (skew-sign, kurt-percentile-band). With NEW Single-Symbol-Carrier-RISK pre-Falsifier gate (2× threshold). The /119 QR adjudicates specific candidate via committed `analysis/iteration_v3-119/*.py` BEFORE the brief.
- **/120 CONFIRMATION setup**: SINGLE-COMPONENT validation of /116 no_confirm vs /059 canonical at full 10-seed ensemble (per Critic Rec 2 + iter-v3/018 precedent), with IS NEGATIVE floor relaxed to /059 IS − 0.50 = +0.59 to accommodate /116's regime-cost. Multi-seed cascade-attribution falsifier (≥ 2/3 symbols broad-based positive). Bundle composition branches on /119 outcome.
- **Cycle 6 state**: 8 NEGATIVE / 1 PROMISING-MECHANICAL / 1 EXPLORATION slot remaining (/119) / 1 CONFIRMATION (/120).

See `briefs-v3/iteration_v3-118/research_brief.md`, `briefs-v3/iteration_v3-118/phase5p5_gate.md`, `briefs-v3/iteration_v3-118/engineering_report.md`, `briefs-v3/iteration_v3-118/review_preliminary.md`, `briefs-v3/iteration_v3-118/qr_response.md`, `briefs-v3/iteration_v3-118/review.md`, `reports-v3/iteration_v3-118/`, and `briefs-v3/exploration_catalog.md` for full artifacts.
