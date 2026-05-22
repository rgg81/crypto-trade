# Engineering Report — iter-v3/118

## Headers

- Iteration: iter-v3/118
- Branch: iteration-v3/118
- Commit SHA: 0ac25c8a4c2daf6c95d6847c1a18a8dc0393b9cf
- Hardware: x86_64, 20 vCPU, 58 GB RAM (WSL2)
- Wall-clock time: 0:43:12 (0.72h — within the 2h EXPLORATION cap)

---

## 1. Setup Verification

| Check | Result |
|---|---|
| Branch | `iteration-v3/118` CONFIRMED |
| HEAD SHA | `0ac25c8` (feat commit: add ema_signed_volregime + runner setup) |
| Brief SHA | `26dd346` (docs: research brief) |
| EDA SHA | `60a45e8` (analysis: 6-candidate screen, committed BEFORE brief) |
| Phase 5.5 gate SHA | `602c60f` — OVERALL=PASS |
| Ruff clean (features_v3/, run_baseline_v3.py) | CLEAN — 84 pre-existing E501 errors in old_runners/scripts, none in /118 code paths |
| v1 feature import audit | CLEAN — `grep -r "from crypto_trade.features " src/crypto_trade/features_v3/` returns zero matches (docstring mentions only) |
| V3_EXCLUDED_SYMBOLS | PASS — runner asserts `set(V3_MODELS) ∩ set(V3_EXCLUDED_SYMBOLS) = ∅` at pre-flight; BCH/LDO/TRX all disjoint |
| Feature parquet regen | Executed before backtest: BCH/LDO/TRX/BTC 8h parquets regenerated with `ema_signed_volregime` column (15th) present |
| n_features guard | Runner enforces `n == 15` at line 432-440; fires correctly |
| ITERATION_LABEL | `"v3-118"` (updated from v3-117 per gate advisory note) |
| MODEL_SPECS | `("v3-118-BCH", "BCHUSDT"), ("v3-118-LDO", "LDOUSDT"), ("v3-118-TRX", "TRXUSDT")` |
| /116 no_confirm | REVERTED — `enable_no_confirm_exit=False` in runner at all 3 surfaces (model builder, accretion guard, pre-flight assertion) |
| /117 24h machinery | DORMANT — `multioffset_24h.py` present but `--bar-interval` defaults 8h; no 24h dispatch |
| Integration test (Change 6) | PASS — V3_FEATURE_COLUMNS includes `ema_signed_volregime`; parquet column non-NaN on last 100 IS rows verified; n_features==15 guard fires; past-only unit test passes |

---

## 2. Implementation Summary

Brief Section 3.5 specified 6 changes. Delivered:

| Change | Specified | Delivered |
|---|---|---|
| Change 0 (advisory) | ITERATION_LABEL + MODEL_SPECS update | DONE — v3-117 → v3-118 |
| Change 1 | `compute_ema_signed_volregime` in `engineered_v3.py` | DONE — function matches brief docstring exactly |
| Change 2 | `ema_signed_volregime` as 15th element of `V3_FEATURE_COLUMNS_TOP_N` | DONE — placed after `regime_momentum_signed_5d` |
| Change 3 | Runner feature-count guard: `n != 14` → `n != 15` | DONE — error string updated with /118 commentary |
| Change 4 | Parquet regeneration for BCH/LDO/TRX/BTC 8h | DONE — column present, non-NaN on IS rows |
| Change 5 | Unit test `test_compute_ema_signed_volregime_past_only` | DONE — past-only invariant verified on 250-bar synthetic panel |
| Change 6 | Adversarial integration test | DONE — 4 assertions at runtime call-site |

**Knobs UNCHANGED vs /059-canonical** (verified against accretion guard output in run.log):
- V3_MODELS = BCH/LDO/TRX; REQUIRED_GAP = 66; label_mode = triple_barrier; ATR = (2.0, 1.0); zscore_threshold = 2.0; adx_threshold = 20.0; enable_no_confirm_exit = False; enable_per_symbol_drawdown_brake = False; ENSEMBLE_SIZE = 3 (EXPLORATION-mode)

---

## 3. Key Metrics Table

### Headline comparison

| Metric | /118 IS | /118 OOS | /118 ratio | /060 IS | /060 OOS | /118 Δ IS | /118 Δ OOS |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | 0.3782 | -0.1501 | -0.3968 | 0.8325 | 0.1403 | **-0.4543** | **-0.2904** |
| daily_sharpe | 0.8336 | -0.3471 | -0.4163 | 1.7115 | 0.3659 | -0.8779 | -0.7130 |
| max_drawdown (%) | 43.91 | 28.91 | 0.6584 | 31.87 | 35.78 | +12.04 | -6.87 |
| profit_factor | 1.1264 | 0.9580 | 0.8505 | 1.2806 | 1.0482 | -0.1542 | -0.0902 |
| win_rate (%) | 32.97 | 39.22 | 1.1895 | — | — | — | — |
| n_trades | 182 | 102 | 0.5604 | — | — | — | — |
| total_pnl (%) | 27.13 | -5.51 | -0.2030 | — | — | — | — |
| monthly_calmar | 0.6179 | -0.1905 | -0.3083 | — | — | — | — |
| weighted_pnl_total | 27.13 | -5.51 | -0.2030 | — | — | — | — |

### Statistical significance block

| Metric | /118 Value | Gate threshold | Gate status |
|---|---|---|---|
| DSR | 0.0000 | > 0.95 | FAIL |
| PBO | 0.0885 | < 0.40 | PASS |
| PSR | 0.0482 | > 0.95 | FAIL |
| frac_positive_paths | 0.644 (29/45) | ≥ 0.55 | PASS |
| n_trials | 315 | — | — |
| n_effective_trials (n_eff) | 19 | — | — |
| CPCV Q25 Sharpe | -0.2430 | — | — |
| CPCV Q50 Sharpe | 0.3351 | — | — |
| CPCV Q75 Sharpe | 0.8378 | — | — |

### Secondary comparison vs /059 canonical baseline

| Metric | /118 IS | /059 IS | /118 OOS | /059 OOS |
|---|---:|---:|---:|---:|
| monthly_sharpe | 0.3782 | 1.0894 | -0.1501 | 0.5791 |

---

## 4. Per-Symbol IS Attribution

Source: `reports-v3/iteration_v3-118/in_sample/per_symbol.csv`

| Symbol | Trades | WR (%) | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 82 | 42.7 | +52.61 | +0.64 | 157.91% |
| TRXUSDT | 85 | 32.9 | -5.49 | -0.06 | -16.48% |
| LDOUSDT | 15 | 26.7 | -13.80 | -0.92 | -41.43% |

**Mode 3 PROMISING-PARTIAL hypothesis assessment (IS)**:

The brief pre-registered Mode 3 as: TRX IS PnL Δ ≥ +2.0% AND (BCH IS PnL Δ < −1.0% OR LDO IS PnL Δ < −1.0%), based on the EDA T9 per-symbol multivariate-lift asymmetry (TRX +0.0082; BCH −0.0039; LDO −0.0106 — TRX was the sole positive carrier).

**Observed IS outcome**: The asymmetry INVERTED. BCH is the large positive carrier (+52.61%, 42.7% WR), while TRX is the largest NEGATIVE symbol (−5.49%, only 32.9% WR) and LDO is also deeply negative (−13.80%, 26.7% WR). This is the OPPOSITE of the Mode 3 prediction — the EDA's per-symbol T9 lift did not transfer to production IS. BCH was predicted negative in EDA (−0.0039 lift) but emerged as the sole survivor; TRX was predicted positive (+0.0082) but collapsed. This cross-symbol role-reversal is a diagnostic flag for multivariate-interaction cancellation at production scale (the "production-scale INERT" pattern from /023 / /086).

The portfolio IS aggregate (0.3782) is pulled down by TRX + LDO dragging despite BCH's strong result.

---

## 5. Per-Symbol OOS Attribution

Source: `reports-v3/iteration_v3-118/out_of_sample/per_symbol.csv`

| Symbol | Trades | WR (%) | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---:|---:|---:|---:|---:|
| TRXUSDT | 42 | 50.0 | +22.00 | +0.52 | -244.02% |
| BCHUSDT | 45 | 37.8 | +2.18 | +0.05 | -24.18% |
| LDOUSDT | 15 | 20.0 | -33.20 | -2.21 | +368.20% |

**Mode 3 prediction vs OOS**:

OOS shows further role-reversal: TRX recovers to positive (+22.00% net, 50% WR) which partially aligns with the EDA Mode 3 positive-carrier prediction, but BCH also recovers to mild positive (+2.18%), and LDO catastrophically fails (−33.20%, 20% WR, 368% negative concentration). The negative portfolio OOS Sharpe (−0.1501) is entirely driven by LDO's catastrophic OOS PnL drag — LDO contributes +368% of the total OOS loss despite being only 15 trades. The concentration_pct of +531.44% for LDO in the OOS comparison.csv section confirms LDO is the single failure point.

Mode 3 did NOT fire — the TRX-positive-carrier signal did not cleanly materialize either. What materialized is a single-symbol catastrophic drawdown in LDO, which overwhelms any TRX/BCH positive contribution.

---

## 6. C3 Feature Importance

Source: `reports-v3/iteration_v3-118/in_sample/model_importance_last_month_portfolio.csv` (portfolio aggregate).

**Portfolio (aggregated across BCH/LDO/TRX, last walk-forward month)**:

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
| ... | ... | ... | ... |
| 14 | regime_momentum_signed_5d | 227.7 | 4.1 |
| 15 | sym_vs_btc_ret_7d | 188.0 | 3.4 |

**Per-symbol rank (last month)**:
- BCH: rank 11/15 (importance 56.7, 4.5% of top)
- LDO: rank 13/15 (importance 128.7 — higher raw but 14th by rank)
- TRX: rank **1/15** (importance 205.0 — top feature for TRX, consistent with EDA T9 TRX-led lift)

**vs /025 benchmark** (rank ≤ 5, gain ≥ 30% of top):

Portfolio rank = **6/15** (misses the rank ≤ 5 target by 1 position). Portfolio share = 7.1% of top-feature's importance — well below the 30% of top threshold (would require ~160 importance vs top-feature's 535.7 to clear 30%). The EDA T5 comparison (rank 8-10/15, gain 38-63% of top — all 3 symbols clearing 30% bar) used a depth-4 LightGBM at n_trials=35 in 14+1 feature space; production runner's portfolio aggregate shows a different distribution. The TRX rank-1 result is consistent with EDA's TRX being the carrier, but BCH (rank 11) and LDO (rank 13) are clearly below the EDA-predicted 8-10 range.

**Conclusion**: C3 is NOT fully INERT (portfolio rank 6, TRX rank 1 — importance allocated, not zero), but it is below the /025 PROMISING benchmark thresholds (rank ≤ 5, ≥ 30% of top). Mode 2 (PROMISING-INERT condition: "rank ≥ 13/15 on > 1 symbol AND gain < 30%") does NOT fully fire because BCH is rank 11 (not ≥ 13) and TRX is rank 1 — but BCH and LDO are both well below 30% of top.

---

## 7. IC Matrix Check

Source: `reports-v3/iteration_v3-118/ic_matrix.csv`

**Pre-existing high-IC pair confirmed**:
- `vwap_dev_20 × regime_momentum_signed_5d`: **0.7642** (expected per /059 annotation — the algebraic-identity pairing established at /025; both features share `vwap_dev_20` primitive)

**C3 (`ema_signed_volregime`) NEW pairs > 0.70**: **NONE**. C3's maximum absolute IC with any existing feature is 0.2119 (`sym_vs_btc_ret_7d`), well below the 0.70 threshold. The EDA T2 R²=0.196 (max|corr|=0.21 POOLED) is confirmed reproduced in production. C3 introduces no new collinearity risk.

**The one pre-existing pair** (`vwap_dev_20 × regime_momentum_signed_5d` at 0.7642) is unchanged from /059 / /060 baselines — confirmed not worsened by C3 addition.

---

## 8. ADF Stationarity

Source: `reports-v3/iteration_v3-118/adf_test.csv`

- Total rows: 2355
- Stationary rows (p < 0.05): **1941** (82.4%)
- C3 (`ema_signed_volregime`) rows: 157
- C3 stationary rows: **138** (87.9%)

C3 is stationary at 87.9% of tested months across all 3 symbols — above the portfolio mean (82.4%). The vol-regime sign composition does not introduce non-stationarity; the rolling-median construction produces a bounded ±1 multiplier applied to the bounded `ema_spread_atr_20` primitive.

---

## 9. Section-8 First-Match-Wins Verdict

Applying the pre-registered criteria in order:

**Criterion 1 — NEGATIVE-catastrophic** (IS Sharpe Δ < −0.20 vs /060 OR OOS Sharpe Δ < −0.50 vs /060):
- IS Sharpe Δ = 0.3782 − 0.8325 = **−0.4543** → below −0.20 threshold → **FIRES**

Criterion 1a (IS Sharpe Δ < −0.20) fires immediately. No further criteria need to be evaluated under first-match-wins.

**Section 8 mechanical verdict: EXPLORATION-NEGATIVE (Criterion 1a — catastrophic IS collapse)**.

The axis-closure recommendation in Criterion 1 reads: "vol-regime composite axis CLOSED at /118 (orthogonal classifier didn't lift)." This is the Engineer's mechanical reading; QR adjudicates whether the axis is fully closed or whether a sub-variant remains viable at /119.

---

## 10. Section-7 Mode Assessment

Applying Mode definitions in first-match-wins order:

**Mode 4 (Catastrophic regime artifact)** condition: IS Sharpe Δ < −0.20 AND OOS Sharpe Δ < −0.50.
- IS Δ = −0.4543 (below −0.20): YES
- OOS Δ = −0.2904 (−0.1501 − 0.1403): OOS Δ = −0.2904 — does NOT reach −0.50 → Mode 4 OOS leg DOES NOT FIRE

**Mode 5 (Null at production)** condition: IS Sharpe Δ ∈ [−0.05, +0.05] AND common-trade fraction with /060 > 95%:
- IS Δ = −0.4543 — outside [−0.05, +0.05] → Mode 5 DOES NOT FIRE

**Mode 3 (PROMISING-PARTIAL)** condition: TRX IS PnL Δ ≥ +2.0% AND (BCH or LDO IS PnL Δ < −1.0%):
- TRX IS PnL = −5.49% — TRX IS PnL is NEGATIVE, not ≥ +2.0% → Mode 3 DOES NOT FIRE

**Mode 2 (Importance INERT)** condition: rank ≥ 13/15 on > 1 symbol AND gain < 30%:
- BCH rank = 11/15 (not ≥ 13); TRX rank = 1/15 (not ≥ 13) → Mode 2 formal condition DOES NOT FIRE

**Mode 1 (success)** condition: IS Δ ∈ [+0.05, +0.30] AND OOS Δ ∈ [+0.05, +0.25]:
- IS Δ = −0.4543 — DOES NOT FIRE

**None of the Modes 1–5 fire on their exact conditions**, but IS Δ = −0.4543 is decisively below every PROMISING threshold. The closest is a variant of Mode 4 (IS leg fires at −0.4543, OOS leg misses at −0.2904 vs the −0.50 gate) combined with a variant of Mode 3 (per-symbol asymmetry materialized but in the opposite direction — BCH positive, TRX negative, LDO catastrophic — rather than the EDA-predicted TRX-positive, BCH/LDO-negative pattern).

**QR calibration**: Mode 3 (20% prior) was the closest modal prediction to what occurred (per-symbol asymmetry). The EDA correctly identified asymmetry but misidentified the carrier symbol. Mode 4 (10% prior, IS < −0.20) fires on the IS leg. The actual outcome is a Mode-4/Mode-3 hybrid: IS catastrophic collapse (−0.4543) with an inverted per-symbol pattern vs prediction.

---

## 11. Failure Mechanism Trace

### 11a. Importance level

C3 is NOT fully INERT at the production level. Portfolio rank 6/15 with 7.1% importance share, TRX rank 1/15 — C3 was allocated and used by the model. The /025 PROMISING benchmark (rank ≤ 5, ≥ 30% of top) is NOT met at portfolio level. However, importance is not zero — this is not the /085/086 "rank 14/15, near-zero gain" dead pattern. The failure is NOT at the importance-allocation layer.

### 11b. Harmful interaction at multivariate level

The more likely failure mechanism is that C3 DISRUPTED the incumbent features' learned signal. The portfolio IS Sharpe collapsed from 0.8325 to 0.3782 (−0.4543 Δ), while C3 carries only 7.1% importance — the collapse is disproportionate to C3's allocated share. This signature — large IS Sharpe collapse with modest-but-nonzero importance for the new feature — is consistent with C3 corrupting the gradient-boosting loss surface: by adding a correlated-but-noisier variant of `ema_spread_atr_20` at the ~67-day regime timescale, C3 may have caused Optuna to find hyperparameters that are locally optimal for the 15-feature space but suboptimal for the 14 incumbents' signal. The C3 rolling-median window of 200 bars shares the same primitive (`ema_spread_atr_20`) as feature rank 12 — a partial-redundancy regime at intermediate R²=0.196 can disrupt tree-splitting in a depth-limited LightGBM more than a fully-orthogonal or fully-redundant feature.

### 11c. Per-symbol pattern

The failure is NOT uniform — it is asymmetric. BCH emerged as the IS positive carrier (+52.61% net PnL, rank 11 importance), while TRX (EDA's predicted carrier) collapsed (−5.49% net, rank 1 importance for C3 but 32.9% WR). This cross-symbol role-reversal (BCH and TRX swap direction from EDA to production) means the n_trials=35 single-seed Optuna search found a TRX hyperparameter configuration that overcalibrated C3's TRX signal, at the cost of the existing IS signal for TRX. BCH, whose C3 lift was negative in EDA (−0.0039), paradoxically emerged positive — likely because BCH's hyperparameter search was not disrupted by C3 in the same way.

### 11d. Frozen-baseline cross-symbol regression check

Per `feedback_v3_single_seed_frozen_baseline.md` (iter-v3/020/021/022): single-seed=42 EXPLORATION produces bit-identical rosters for non-target symbols across consecutive iterations. However, /118 adds C3 to ALL THREE symbols (BCH, LDO, TRX simultaneously) — there are no "non-target" symbols frozen at /060 baseline. The per-symbol importance table shows C3 at rank 1 for TRX, rank 11 for BCH, rank 13 for LDO — three different hyperparameter solutions. The frozen-baseline pattern does NOT apply here because all three symbols received the C3 column and ran Optuna independently with a shared seed lineage. The cross-symbol divergence reflects genuine per-symbol hyperparameter sensitivity to C3, not a frozen-baseline artifact.

---

## 12. Gate Efficacy Table

The 7-gate RiskV2 stack is unchanged. Regime column in per_regime.csv shows all trades as "unknown" (the v3 regime classifier produces a single bucket for this run configuration). Gate efficacy at production scale is not individually decomposable from the per_regime.csv in this output; the gates fired at their configured thresholds (ADX 20.0, zscore 2.0, etc.) without change from /060.

---

## 13. Label Leakage Audit

- REQUIRED_GAP = 66 = (21+1) × 3 (timeout_candles=21, n_symbols=3) — unchanged from /059-canonical
- Walk-forward embargo: `train_end_ms = test_start_ms - embargo_ms` per the /058 RE-ANCHOR fix (commit `e149e9d`) — verified present in `walk_forward.py:113`
- The gap of 66 bars corresponds to the López de Prado purge requirement for 3-symbol triple-barrier labels with 21-candle timeout. No deviation from /059-canonical.

---

## 14. Trade Spot-Check

Checked 3 random OOS trades (seed 777):
- LDOUSDT short: entry 1.0989, exit 1.1596, pnl_pct −5.5278%, exit_reason stop_loss, weight_factor 0.89 — math consistent (short caught upward move, loss as expected)
- BCHUSDT long: entry 475.84, exit 513.65, pnl_pct +7.9456%, exit_reason take_profit, weight_factor 0.86 — math consistent (long TP hit)
- TRXUSDT long: entry 0.32789, exit 0.34077, pnl_pct +3.9292%, exit_reason take_profit, weight_factor 0.99 — math consistent

No anomalies. exit_reason, weight_factor, and pnl math are internally consistent across all 3 sampled trades.

OOS monthly trade counts: no zero-trade months in OOS (minimum 2 trades in Dec-2025 and Jan-2026; all other months 3–13 trades).

---

## 15. Configuration Diff vs BASELINE_V3.md (/059 canonical)

Single axis only:

```
V3_FEATURE_COLUMNS_TOP_N: 14 → 15
  + "ema_signed_volregime"  # [iter-v3/118]: C3 composed = ema_spread_atr_20 × sign(range_realized_vol_50 - rolling_median_200)

ITERATION_LABEL: "v3-118"
MODEL_SPECS: ("v3-118-BCH", ...), ("v3-118-LDO", ...), ("v3-118-TRX", ...)
```

All other knobs bit-identical to /059-canonical (verified against accretion-guard output).

---

## Status

**Section 8 mechanical classification**: EXPLORATION-NEGATIVE — Criterion 1a fires (IS Sharpe Δ = −0.4543 < −0.20 vs /060 anchor). Axis-close recommendation: vol-regime composite (orthogonal vol-median classifier) closed at /118. Engineer's mechanical read; QR adjudicates /119 axis.

OVERALL=READY-FOR-CRITIC
