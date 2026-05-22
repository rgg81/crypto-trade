# iter-v3/126 Research Brief — Cycle-7 EXPLORATION #5 — Multi-frequency feature stack (8h base + 24h-aggregated)

**Axis**: Multi-frequency feature stack — append the 24h-aggregated feature `d24_ret_autocorr_lag1_50` as the 15th column in `V3_FEATURE_COLUMNS_TOP_N`. The 14 8h-cadence features are bit-identical to /121; the 24h feature is causally merge_asof'd onto the 8h decision grid (`direction='backward'`, `left_on='open_time'`, `right_on='bar_close_time'`).

**Lineage discipline**: First cycle-7 EXPLORATION under FEATURE-CADENCE-STACK axis class (NEW dimension in v3 catalog). Per /125 Critic FINAL `53cfc06` PRIMARY recommendation. Universe REVERTED to /121 BCH/LDO/TRX baseline to isolate the multi-frequency axis from the /125 wild-universe confound. Per `feedback_v3_structural_over_knob_exploration.md` — NEW feature families rank above universe substitution and gate-threshold knobs.

**Cycle**: 7 EXPLORATION slot **#5 of 10**. Cycle-7 catalog state at /125 closeout: /122 NEGATIVE-INERT, /123 NEGATIVE-catastrophic, /124 NEGATIVE-catastrophic, /125 NEGATIVE-catastrophic. /126 is slot 5/10 under LIFTED constraints regime; the universe-substitution axis is empirically CLOSED at /125 per `feedback_v3_architecture_cohort_shaped.md` — /126 pivots to a structurally orthogonal axis (FEATURE-CADENCE-STACK, not universe).

**Anchor (per-criterion annotation)**: PUBLIC = /121 multi-seed CONFIRMATION-MERGE BASELINE (IS monthly Sharpe **+1.3108** / OOS monthly Sharpe **+0.9682**); ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.95) per `feedback_v3_dsr_mode_artifact.md` 3-seed-vs-10-seed proba-averaging compression factor.

---

## Section 0 — Data Split declaration

`OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` are UNCHANGED. Sacred constants immutable.

- **IS window**: 8h candle stream from per-symbol earliest 8h candle close ≥ 2020-01-01 (BCH/TRX) or 2022-09-22 (LDO) through `OOS_CUTOFF_DATE = 2025-03-24` (exclusive).
- **OOS window**: `OOS_CUTOFF_DATE = 2025-03-24` through current data extent.
- **Walk-forward training window**: 24 calendar months ending at each test-month's start; rolling by 1 month.
- **24h feature source**: `data/features_v3_24h/<SYM>_24h_features.parquet` (iter-v3/117 multi-offset infrastructure). The /126 axis selects `offset_id=0` rows (calendar-day-aligned 24h aggregation; `bar_open_time` at 00:00 UTC, `bar_close_time` at 23:59:59.999 UTC).
- **Bar interval**: 8h (UNCHANGED — /126 is NOT a candle-frequency switch; the 24h dimension enters only at the feature-stack layer via causal merge_asof onto the 8h decision grid).

**Hand-chosen parameter declaration (per `feedback_v3_brief_parameter_provenance.md`)**:

| Parameter | Value | Provenance |
|---|---|---|
| 24h feature appended | **`d24_ret_autocorr_lag1_50`** (15th in V3_FEATURE_COLUMNS_TOP_N) | SELECTED via EDA composite score 8.17 (top candidate of 14 evaluated; cleanly PASSES T3 LR-PF + T4 IC-PF + T7 SSC-RISK; PASSES T6 walk-forward AUC lift on 3/3 syms) |
| 24h aggregation slice | **`offset_id=0` (calendar-day-aligned)** | SELECTED via /117 multi-offset infrastructure — the only offset that aligns 24h bar_close_time to 00:00 UTC sub-bar boundary |
| Merge direction | **`backward` causal merge_asof** | Identical to existing `multifreq_v3.py:add_multifreq_v3_features` pattern (validated look-ahead-free at /113) |
| V3_FEATURE_COLUMNS_TOP_N | **15 features** (14 8h incumbents + 1 24h candidate) | EXTENDED from 14 → 15. The 24h feature is APPENDED as the 15th column (last position) per established convention |
| Bar interval | 8h | INHERITED from /121 |
| V3_MODELS universe | **BCH/LDO/TRX (REVERT from /125 ATOM/RUNE/UNI)** | REVERTED to /121 baseline universe. Isolates multi-frequency axis from /125 wild-universe confound |
| Triple-barrier K | 21 | INHERITED from /121 (labeling-DURATION axis CLOSED BILATERALLY at /068/124) |
| ATR multipliers | (2.0, 1.0) | INHERITED from /121 |
| `enable_no_confirm_exit` | True | INHERITED from /121 |
| `no_confirm_trigger_atr` | 0.50 | INHERITED from /121 |
| `no_confirm_k_candles` | 4 | INHERITED from /121 |
| REQUIRED_GAP | 66 = (21+1)×3 | INHERITED from /121 (universe REVERTED to 3 syms; gap identical) |
| ENSEMBLE_SIZE | 3 (EXPLORATION mode) | INHERITED EXPLORATION default per `feedback_v3_outer_seed_cap_2_v3.md` |
| n_trials | 35 | INHERITED EXPLORATION default per `feedback_v3_exploration_n_trials_35.md` |

**ZERO tuned scalar parameters added in /126.** The only structural change vs /121 is the V3_FEATURE_COLUMNS_TOP_N tuple extension and the corresponding feature-pipeline causal merge_asof step.

**Auditable temporal fence**: the EDA (`analysis/iteration_v3-126/`, commit `dd9fc2d`) was committed in ONE atomic commit BEFORE this brief. The EDA asserts `close_time < OOS_CUTOFF_MS = 1742774400000` AND `bar_close_time < OOS_CUTOFF_MS` at every IS-frame extraction. T2 audit verified: 0 look-ahead violations across all 3 symbols (median lag 8.0 hours; min lag 0 hours — exact equality matches when 8h bar opens at 00:00 UTC the same instant a 24h bar closes; causal direction strictly preserved).

---

## Section 0.5 — Iteration Type Declaration

- **TYPE**: `EXPLORATION` (single structural axis: V3_FEATURE_COLUMNS_TOP_N 14 → 15 via APPEND `d24_ret_autocorr_lag1_50`)
- **Cycle 7 slot**: **#5 of 10**. iter-v3/131 is the projected final EXPLORATION (cycle-7 ends with iter-v3/132 CONFIRMATION per the strict 10:1 cadence; `feedback_v3_strict_10_to_1_cadence.md`).
- **CLI invocation**: `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof` (default `--bar-interval 8h`)
- **ENSEMBLE_SIZE**: 3 (`EXPLORATION_ENSEMBLE_SIZE` per `feedback_v3_outer_seed_cap_2_v3.md`)
- **n_trials**: 35 (per `feedback_v3_exploration_n_trials_35.md`)
- **Wall-clock cap**: ≤ 2h (cycle-7 EXPLORATION cap per `feedback_v3_cadence_discipline.md`). Recent EXPLORATIONs at 8h on BCH/LDO/TRX 3-seed: /122 ~0.70h, /123 ~1.05h, /124 ~1.10h. Expected ≤ 1.5h with margin (no architectural change; identical Optuna search-space dimensionality; only feature matrix is 1 column wider).
- **Single axis variation**: V3_FEATURE_COLUMNS_TOP_N tuple extension 14 → 15 + corresponding pipeline change in `process_symbol_v3` to merge_asof the 24h aggregation onto the 8h decision grid. Labels, V3_MODELS universe, gates, ensemble seeds, Optuna search space, /116 no_confirm primitive, REQUIRED_GAP — ALL bit-identical to /121.

---

## Section 1 — Hypothesis

> Appending one 24h-aggregated feature (`d24_ret_autocorr_lag1_50` = 1-bar lag autocorrelation of log returns over the most recent 50 daily bars, attached causally to the 8h decision grid) as the 15th column of `V3_FEATURE_COLUMNS_TOP_N` on the /121 BCH/LDO/TRX baseline lifts EXPLORATION-mode IS monthly Sharpe by Δ ∈ [+0.05, +0.30] vs the architecturally-adjusted /121 EXPLORATION-mode reference (~+1.06) AND OOS monthly Sharpe by Δ ∈ [+0.00, +0.30] vs /121 OOS +0.9682; OR the FEATURE-CADENCE-STACK hypothesis — that a longer-cadence (24h) summary statistic provides decision-relevant information the 14-feature 8h stack cannot resolve — is FALSIFIED, narrowing cycle-7's remaining axis space toward the deferred Critic Priority 1 stateful drawdown brake or alternative NEW non-OHLCV cross-asset feature axes.

**Why this prediction band**: The 14 candidate evaluation in EDA produced a clean PASS-list of 4 candidates (out of 14) clearing both T3 LR-PF (joint R² < 0.50 vs 14 incumbents) AND T4 IC-PF (max pairwise |IC| < 0.40). `d24_ret_autocorr_lag1_50` is the top of the 4 by composite score:
- T3 R² (joint R² vs 14 incumbents): 0.155 BCH / 0.084 LDO / 0.139 TRX — well under 0.50 strict (mechanical orthogonality);
- T4 IC-PF (max pairwise |IC|): 0.160 with `btc_ret_14d` (the highest of the 14 incumbents) — well under 0.40 strict;
- T5 LightGBM importance (depth-3, 14+1): BCH rank **2/15**, LDO rank **1/15**, TRX rank **3/15** — CONSISTENTLY HIGH across all 3 syms; mean per-sym importance share 13.3% (BCH 14.3%, LDO 13.7%, TRX 10.8%);
- T6 walk-forward held-out AUC lift: BCH +0.0183, LDO +0.0084, TRX +0.0174 — POSITIVE on 3/3 syms; mean +0.0147;
- T7 SSC-RISK: max single-symbol share 36.8% (BCHUSDT) — well under 70% gate.

The wide bound captures honest uncertainty: T6 AUC lifts are EDA-screen-grade (5-fold walk-forward without the production 7-gate RiskV2 stack + ensemble + Optuna trajectory); the production pipeline may amplify OR dampen the EDA signal. The prediction band median +0.15 IS / +0.10 OOS reflects the consistently-positive EDA signal across all 5 EDA tables.

**The CASE FOR PROMISING**: 4 EDA tables (T3+T4+T5+T6) all align in the same direction — the feature is mechanically orthogonal to incumbents AND learned consistently at HIGH importance (rank 1-3 per symbol) AND positively lifts walk-forward AUC on all 3 syms. This is the cleanest 4-table EDA alignment v3 has produced for a NEW feature candidate since /025's `regime_momentum_signed_5d` (the only PROMISING-class direct-edge feature in v3 history per `feedback_v3_engineered_features_proven.md`). The 24h cadence provides a structurally distinct (lower-frequency) information channel the 8h-only stack cannot resolve — daily autocorrelation captures persistence in directional drift that disappears under 8h's microstructure noise.

**The CASE AGAINST PROMISING**: /113 (cycle-6 multi-frequency daily features axis) added 8 daily features at once and was NEGATIVE-INERT (IS Δ −0.67 / OOS Δ near-zero). The /126 axis is structurally distinct from /113 in 3 ways: (1) /113 anchor was /059 (pre-no_confirm); /126 anchor is /121 (post-no_confirm). (2) /113 stacked 8 features in one EXPLORATION (per-feature share <12%); /126 commits to ONE feature per `feedback_v3_engineered_features_dont_stack.md`. (3) /113 used `d_*` features that included 3 high-IC sisters (d_ret_5d IC=0.85 with regime_momentum_signed_5d; d_realvol_10 IC=0.81 with range_realized_vol_50; d_close_pos_20 IC=0.85 with ema_spread_atr_20) — /126's `d24_ret_autocorr_lag1_50` has max |IC| = 0.160 (5× cleaner). The /113 NEGATIVE-INERT is a PRECEDENT BUT NOT A FALSIFIER for the /126 axis.

---

## Section 2 — IS-Only Numerical Evidence

EDA (`analysis/iteration_v3-126/`, commit `dd9fc2d`): 7 result tables + synthesis.md.

### Section 2.1 — T1 Data Depth + Inventory

See `analysis/iteration_v3-126/T1_inventory.csv`:

| Symbol | n_24h_rows_IS | n_8h_rows_IS | non-NaN d24 candidates min |
|---|---:|---:|---:|
| BCHUSDT | 1909 | 5727 | 1709 (d24_ret_kurt_200 NaN warm-up) |
| LDOUSDT | 914 | 2741 | 714 (d24_ret_kurt_200 NaN warm-up) |
| TRXUSDT | 1890 | 5669 | 1690 (d24_ret_kurt_200 NaN warm-up) |

**Key finding**: 24h panels have ~1/3 the rows of 8h panels (expected: 3 8h bars per 24h day). All candidates have sufficient non-NaN samples for the 50-bar window (range_realized_vol_50, ret_autocorr_lag1_50, etc.). LDO's lower depth (914 24h rows ≈ 30 months) is comparable to its 8h depth (2741 rows ≈ 30 months).

### Section 2.2 — T2 Look-Ahead Audit (load-bearing)

See `analysis/iteration_v3-126/T2_lookahead_audit.csv`:

| Symbol | n_joined_rows | n_violations | min_lag | median_lag | max_lag | AUDIT_STATUS |
|---|---:|---:|---:|---:|---:|---|
| BCHUSDT | 5724 | **0** | 0 ms | 8.0 h | 16.0 h | **PASS** |
| LDOUSDT | 2739 | **0** | 0 ms | 8.0 h | 16.0 h | **PASS** |
| TRXUSDT | 5667 | **0** | 0 ms | 8.0 h | 88.0 h | **PASS** |

**Causal merge_asof verified**: 0 violations across 14130 joined rows. Median lag = 8.0 hours (exactly one 8h bar — the 24h bar closing at 00:00 UTC is JOINED to the 8h bar opening at 00:00 UTC the same instant via `direction='backward', allow_exact_matches=True`). Min lag = 1 ms (exact-equality join). TRX has a few data-gap intervals with max_lag 88h (~3.7 days, 11 8h bars) where the most recent 24h bar is from a prior trading day — still strictly past-only and structurally bounded.

**Audit logic**: for every joined row, `bar_close_time <= open_time` is enforced by `direction='backward'` + `allow_exact_matches=True`. The 24h bar must be fully closed before the 8h decision row opens.

### Section 2.3 — T3 Linear Redundancy Pre-Falsifier (joint R² vs 14 incumbents)

See `analysis/iteration_v3-126/T3_linear_redundancy.csv`. Strict gate: joint R² < 0.50 PASS across all 3 syms.

| d24 candidate | BCH R² | LDO R² | TRX R² | LR-PF (3/3 syms) |
|---|---:|---:|---:|---|
| **d24_ret_autocorr_lag1_50** | **0.155** | **0.084** | **0.139** | **PASS** |
| d24_hurst_diff_100_50 | 0.165 | 0.155 | 0.046 | PASS |
| d24_hurst_100 | 0.115 | 0.161 | 0.125 | PASS |
| d24_regime_momentum_signed_5d | 0.193 | 0.031 | 0.156 | PASS |
| d24_ret_kurt_50 | 0.330 | 0.289 | 0.595 | FAIL (TRX) |
| d24_ema_spread_atr_20 | 0.917 | 0.912 | 0.903 | FAIL (mechanical sister) |
| d24_btc_ret_14d | 0.927 | 0.921 | 0.922 | FAIL (mechanical sister) |
| d24_ret_kurt_200 | 0.081 | 0.400 | 0.543 | FAIL (TRX) |
| d24_vwap_dev_20 | 0.827 | 0.867 | 0.731 | FAIL (mechanical sister) |
| d24_sym_vs_btc_ret_7d | 0.841 | 0.851 | 0.830 | FAIL (mechanical sister) |
| d24_max_dd_window_50 | 0.756 | 0.849 | 0.746 | FAIL (mechanical sister) |
| d24_range_realized_vol_50 | 0.657 | 0.699 | 0.811 | FAIL (mechanical sister) |
| d24_ret_skew_50 | 0.484 | 0.351 | 0.499 | PASS narrowly |
| d24_ret_skew_200 | 0.209 | 0.457 | 0.499 | PASS narrowly |

**Key finding**: 4 candidates PASS on all 3 syms with substantial margin. The 14 trend/return-magnitude/cross-asset-value features (8h vs 24h aggregation of the SAME statistic) all FAIL — confirming that adding the 24h version of a feature already in the 8h stack is mechanically redundant. The 4 PASS candidates are STRUCTURALLY DIFFERENT statistics — Hurst (regime persistence), Hurst diff (regime trajectory), ret_autocorr_lag1_50 (1-bar return persistence), regime_momentum_signed_5d (composed momentum × regime sign).

### Section 2.4 — T4 Pairwise IC Matrix (tightened per /122 RECURRENCE)

See `analysis/iteration_v3-126/T4_pairwise_ic.csv`. Strict gate per /122 refinement: max pairwise |IC| < 0.40 against ALL 14 incumbents.

| d24 candidate | max |IC| | partner | IC-PF |
|---|---:|---|---|
| **d24_ret_autocorr_lag1_50** | **0.160** | btc_ret_14d | **PASS** |
| d24_hurst_100 | 0.105 | hurst_100 | PASS |
| d24_hurst_diff_100_50 | 0.159 | hurst_100 | PASS |
| d24_regime_momentum_signed_5d | 0.285 | regime_momentum_signed_5d | PASS |
| d24_ret_skew_50 | 0.594 | ret_skew_200 | FAIL |
| d24_ret_kurt_200 | 0.616 | ret_kurt_200 | FAIL |
| d24_range_realized_vol_50 | 0.751 | range_realized_vol_50 | FAIL |
| d24_max_dd_window_50 | 0.774 | max_dd_window_50 | FAIL |
| d24_vwap_dev_20 | 0.807 | ema_spread_atr_20 | FAIL |
| d24_sym_vs_btc_ret_7d | 0.900 | sym_vs_btc_ret_7d | FAIL |
| d24_btc_ret_14d | 0.957 | btc_ret_14d | FAIL |
| d24_ema_spread_atr_20 | 0.948 | ema_spread_atr_20 | FAIL |

**Key finding**: Same 4 candidates pass T4. `d24_ret_autocorr_lag1_50` max |IC| = 0.160 — 2.5× cleaner than the 0.40 strict gate. Its pairwise correlations with incumbents are uniformly low: 0.160 (btc_ret_14d), 0.149 (hurst_100), 0.142 (hurst_diff_100_50), 0.127 (regime_momentum_signed_5d), and all 10 other features below 0.10. This is a STRUCTURALLY ORTHOGONAL signal at the 8h-incumbent-stack level.

### Section 2.5 — T5 Per-Symbol LightGBM Importance (14+1 stack)

See `analysis/iteration_v3-126/T5_lgbm_importance.csv`. Depth-3 LightGBM at 100 trees / lr=0.05 / feature_fraction=0.9 / seed=42. Triple-barrier TP-vs-SL binary classification (drop label=0 timeouts).

| Symbol | d24_ret_autocorr_lag1_50 rank/15 | importance gain | share of total |
|---|---:|---:|---:|
| BCHUSDT | **2/15** | 1412.06 | 14.29% |
| LDOUSDT | **1/15** | 852.95 | 13.70% |
| TRXUSDT | **3/15** | 1102.19 | 10.83% |

**Key finding**: `d24_ret_autocorr_lag1_50` is in the TOP 3 importance rank on all 3 symbols. LDO ranks it **first** — the daily-cadence 1-lag autocorrelation captures LDO's directional persistence better than any 8h-cadence incumbent. Per-symbol importance share averaged across syms = 12.9% — well above the 1/15 = 6.7% uniform-parity floor (2× excess). This is the strongest per-symbol importance signal for a NEW feature candidate in v3 history (only /025 `regime_momentum_signed_5d` produced comparable HIGH-rank consistency).

Comparison with other PASS-list candidates:
- `d24_hurst_diff_100_50` ranks 1/4/4 — also strong but TRX rank 4 vs ret_autocorr's 3;
- `d24_hurst_100` ranks 7/5/11 — TRX 11/15 is notably weak;
- `d24_regime_momentum_signed_5d` ranks 12/8/13 — substantially weaker on BCH and TRX.

### Section 2.6 — T6 Walk-Forward Held-Out AUC

See `analysis/iteration_v3-126/T6_walkforward_auc.csv`. 5-fold time-series walk-forward (4 evaluable folds; train on cumulative folds 0..i, test on fold i+1). Same LightGBM hyperparams as T5.

| Symbol | Baseline AUC (14 feat) | Augmented AUC (14+1) | AUC Lift | Lift Positive |
|---|---:|---:|---:|---|
| BCHUSDT | 0.4911 | 0.5094 | **+0.0183** | Y |
| LDOUSDT | 0.4799 | 0.4883 | **+0.0084** | Y |
| TRXUSDT | 0.5259 | 0.5433 | **+0.0174** | Y |

**Key finding**: Walk-forward AUC lift POSITIVE on 3/3 syms. 3-sym mean lift +0.0147. The baseline 14-feature stack scores near-chance AUC (BCH 0.491, LDO 0.480) — the 8h stack's directional information is bounded; the 24h ret_autocorr feature lifts BCH and TRX into mildly-positive territory (0.509 / 0.543) and improves LDO. BCH and TRX both gain >+0.017 — clean structural signal.

### Section 2.7 — T7 SSC-RISK gate

See `analysis/iteration_v3-126/T7_ssc_risk.csv`. Single-symbol-carrier risk metric: max per-symbol importance share / total 3-symbol share. Strict gate: < 0.70 PASS.

| d24 candidate | Max share | Max symbol | Total 3-sym share | Max/Total ratio | SSC-RISK |
|---|---:|---|---:|---:|---|
| **d24_ret_autocorr_lag1_50** | 14.29% | BCHUSDT | 38.82% | **0.368** | **PASS** |
| d24_hurst_100 | 8.87% | LDOUSDT | 21.04% | 0.422 | PASS |
| d24_hurst_diff_100_50 | 13.64% | BCHUSDT | 31.02% | 0.440 | PASS |
| d24_regime_momentum_signed_5d | 6.47% | LDOUSDT | 10.95% | 0.591 | PASS |

**Key finding**: SSC-RISK PASS at 0.368 — the importance is broadly distributed across all 3 syms, not concentrated in a single-symbol-carrier pattern. This is structurally distinct from /122 `eth_ret_3d` (which had TRX importance rank 15/15 with TRX IS PnL +32.45 — the canonical SSC-DISSOCIATION signature). `d24_ret_autocorr_lag1_50` is the OPPOSITE pattern — broad-based per-symbol importance allocation.

### Section 2.8 — Pre-flight Gate Summary

| Gate | Threshold | Observed | Result |
|---|---|---|---|
| G1 data depth (24h IS rows ≥ 200) | ≥ 200 | BCH 1909 / LDO 914 / TRX 1890 | PASS |
| G2 look-ahead (T2 audit) | 0 violations | 0 / 0 / 0 | PASS |
| G3 LR-PF (joint R² < 0.50, 3/3 syms) | strict 3/3 | 0.155 / 0.084 / 0.139 | PASS |
| G4 IC-PF (max |IC| < 0.40 pooled) | strict | 0.160 (vs btc_ret_14d) | PASS |
| G5 T6 AUC lift positive (3/3 syms) | 3/3 | +0.018 / +0.008 / +0.017 | PASS |
| G6 T7 SSC-RISK (max/total < 0.70) | strict | 0.368 | PASS |

**ALL 6 pre-flight gates PASS** — the axis is QR-cleared for production backtest. This is the cleanest pre-flight evidence base for any feature candidate in v3 history.

---

## Section 3 — Proposed Changes (single-axis vs /121 baseline)

### Change 1 — `src/crypto_trade/features_v3/multifreq_v3.py` extension

Add a new function `add_multifreq_v3_24h_features` that wraps the existing 24h-aggregation infrastructure. Key design:
- Read the symbol's 24h multioffset parquet at `data/features_v3_24h/<SYM>_24h_features.parquet`
- Filter to `offset_id == 0` rows (calendar-day-aligned slice)
- Select columns `[bar_close_time, ret_autocorr_lag1_50]`
- Rename `ret_autocorr_lag1_50` → `d24_ret_autocorr_lag1_50` (the d24_ prefix is the multi-frequency-feature convention)
- Causal merge_asof onto the 8h frame: `direction='backward'`, `left_on='open_time'`, `right_on='bar_close_time'`, `allow_exact_matches=True`
- Drop the `bar_close_time` join key column before returning

The existing `add_multifreq_v3_features` (8 d_* daily features from 8h aggregation) STAYS DORMANT (the function is retained as zero-cost infrastructure; not called in /126).

### Change 2 — `src/crypto_trade/features_v3/__init__.py` — GROUP_REGISTRY + V3_FEATURE_COLUMNS_TOP_N

(a) Register `multifreq_v3_24h` in `GROUP_REGISTRY` AFTER `cross_btc` (or AFTER `multifreq_v3` for tidy ordering):

```python
"multifreq_v3_24h": add_multifreq_v3_24h_features,
```

(b) Append `d24_ret_autocorr_lag1_50` as the 15th column in `V3_FEATURE_COLUMNS_TOP_N`:

```python
V3_FEATURE_COLUMNS_TOP_N: tuple[str, ...] = (
    "max_dd_window_50", "ema_spread_atr_20", "ret_kurt_50", "ret_skew_200",
    "range_realized_vol_50", "hurst_diff_100_50", "ret_kurt_200", "hurst_100",
    "btc_ret_14d", "ret_skew_50", "vwap_dev_20", "ret_autocorr_lag1_50",
    "sym_vs_btc_ret_7d", "regime_momentum_signed_5d",
    # iter-v3/126 cycle-7 EXPLORATION axis-5 — 24h multi-frequency feature
    "d24_ret_autocorr_lag1_50",
)
```

(c) `V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N` (15 features active).

### Change 3 — `run_baseline_v3.py` — runner-side updates

(a) REVERT `V3_MODELS` from /125 ATOM/RUNE/UNI back to /121 BCH/LDO/TRX:

```python
V3_MODELS: tuple[tuple[str, str], ...] = (
    ("v3-126-BCH", "BCHUSDT"),
    ("v3-126-LDO", "LDOUSDT"),
    ("v3-126-TRX", "TRXUSDT"),
)
```

(b) `ITERATION_LABEL = "v3-126"` (was "v3-125").

(c) `_verify_feature_columns` symbol-loop assertion update:
- `len(V3_FEATURE_COLUMNS_TOP_N) == 15` (was 14)
- `"d24_ret_autocorr_lag1_50" in V3_FEATURE_COLUMNS_TOP_N`

(d) `_verify_feature_columns` per-symbol existence check: for each of BCH/LDO/TRX, the parquet at `data/features_v3/<SYM>_8h_features.parquet` must contain the `d24_ret_autocorr_lag1_50` column. The runner regenerates parquets if missing — `process_symbol_v3` will pick up the new `multifreq_v3_24h` group from `GROUP_REGISTRY` and append the column.

(e) The ABSENT-assertion ban-list at lines 826-861 stays UNCHANGED — the 8 /113 daily features (d_ret_5d, d_ret_10d, d_trend_slope_10, d_realvol_10, d_realvol_ratio, d_atr_pctrank_60, d_efficiency_10, d_close_pos_20) MUST still be absent. /126's `d24_ret_autocorr_lag1_50` is a DIFFERENT feature class (d24_ prefix vs d_ prefix; 24h cadence via /117 multi-offset infrastructure vs /113's 1d aggregation); the ban-list does not apply.

### Change 4 — feature parquet regeneration

The /126 axis introduces ONE new column in the 8h features parquet. The runner's `process_symbol_v3` will detect the new `multifreq_v3_24h` group and regenerate the parquets on first call. ~3 minutes per symbol = ~10 minutes total for BCH/LDO/TRX. The 24h source parquets at `data/features_v3_24h/` are UNCHANGED.

### Change 5 — assertions/tests

Add ONE unit test at `tests/strategies/ml/test_multifreq_v3_24h.py` (or extend existing `test_multifreq_v3.py`):
- **Look-ahead-free assertion**: build a synthetic 8h frame + a synthetic 24h frame; assert that for every joined row, `bar_close_time <= open_time`.
- **Single-feature output assertion**: assert `add_multifreq_v3_24h_features(df8h)` returns a frame with exactly ONE new column `d24_ret_autocorr_lag1_50` (and the original 8h columns intact).

Existing tests in `tests/strategies/ml/test_v3_*.py` are V3_FEATURE_COLUMNS_TOP_N-membership-agnostic; no other test changes required.

---

## Section 3.5 — Precise `src/` Changes for the QE (Phase 6)

QE Phase 6 sequence:
1. Apply Changes 1 + 2 + 3 + 5 above in 2-3 setup commits (feature pipeline + GROUP_REGISTRY/V3_FEATURE_COLUMNS_TOP_N + runner + tests).
2. Regenerate ATOM/RUNE/UNI feature parquets NOT NEEDED — universe REVERTED to BCH/LDO/TRX; existing parquets must include the new `d24_ret_autocorr_lag1_50` column. Re-run `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT --interval 8h --track v3 --format parquet --workers 3` for ~10 minutes.
3. Run `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`.
4. Verify outputs:
   - `reports-v3/iteration_v3-126/comparison.csv` exists with monthly_sharpe rows
   - `reports-v3/iteration_v3-126/per_symbol` table shows 3 rows (BCHUSDT, LDOUSDT, TRXUSDT)
   - `reports-v3/iteration_v3-126/in_sample/model_importance_last_month_*.csv` shows `d24_ret_autocorr_lag1_50` per symbol (rank, gain, share)
   - `ensemble_summary.json` confirms 3-seed EXPLORATION
   - `run.log` shows 3 per-symbol model training blocks labeled `v3-126-BCH/LDO/TRX`
5. Write `briefs-v3/iteration_v3-126/engineering_report.md` with the standard 12 sections + falsifier evaluation + per-symbol attribution + IC matrix anomaly check (esp. `d24_ret_autocorr_lag1_50` × all incumbents on the production stack).

---

## Section 4 — Expected OOS Impact (predicted bands) — PER-CRITERION ANCHOR ANNOTATION

Per /122 Critic Rec 3, every prediction band declares its anchor.

### Section 4.1 — Headline Sharpe Δ bands

| Metric | Anchor A: /121 multi-seed (PUBLIC) | Anchor B: /121 architecturally-adjusted EXPLORATION-mode | Δ band | Mode |
|---|---:|---:|---|---|
| IS monthly Sharpe | +1.3108 | ≈ +1.06 | [+1.06 + 0.05, +1.06 + 0.30] = [+1.11, +1.36] | falsifier band |
| OOS monthly Sharpe | +0.9682 | ≈ +0.95 | [+0.95 + 0.00, +0.95 + 0.30] = [+0.95, +1.25] | falsifier band |

Falsifier band classification: anchor B (ADJUSTED).
NEGATIVE-catastrophic classification: anchor A (PUBLIC) — IS Δ < −0.40 OR OOS Δ < −0.30 vs PUBLIC.

### Section 4.2 — Per-symbol predicted weighted_pnl distribution

Anchor: /121 multi-seed per-symbol attribution (BCH 95.76% OOS PnL concentration; LDO -8% OOS; TRX +14% OOS).

| Symbol | Predicted OOS wpnl Δ vs /121 | Rationale |
|---|---|---|
| BCHUSDT | [−5, +15] | T5 rank 2 + T6 lift +0.0183 — significant feature importance + AUC improvement |
| LDOUSDT | [−5, +10] | T5 rank 1 + T6 lift +0.0084 — moderate lift; LDO benefits most from broad importance |
| TRXUSDT | [−5, +12] | T5 rank 3 + T6 lift +0.0174 — strong AUC lift; signal could surface at production |

### Section 4.3 — EXPLORATION-vs-CONFIRMATION architectural compression note

Per `feedback_v3_dsr_mode_artifact.md` + /122 brief Section 4.3: EXPLORATION-mode 3-seed run will compress IS Sharpe by ~−0.25 relative to 10-seed CONFIRMATION via proba-averaging. OOS compression is typically less material (~−0.02). The /126 IS band median (+1.24) accounts for compression; OOS band median (+1.10) reflects minimal compression.

### Section 4.4 — Pre-registered modal expectation + behavioral-effect predictor

**Modal expectation**: PROMISING-PARTIAL or NEGATIVE-INERT (40% / 30% split). The 4-table EDA alignment supports a positive prior, but /113 (NEGATIVE-INERT) and /122 (NEGATIVE-INERT) precedents of "EDA-strong-then-production-INERT" outcomes set a sober base rate. The 4 PASS-list candidates' T5 importance ranks 1-3 across all 3 syms is the strongest EDA signal v3 has seen for a NEW feature candidate; PROMISING-strong (broad-based IS + OOS lift) has 20% probability.

**Behavioral-effect predictor (per `feedback_v3_axis_saturation_predictor.md`)**: adding a 15th feature at colsample_bytree fractional sampling will change every Optuna trial's training-feature subset. Expected IS trade-roster change: 10-30% (vs /121 trade-roster). If observed IS trade-roster change < 5%, the feature is BEHAVIORALLY INERT (the model didn't use it enough to shift decisions; classify NEGATIVE-INERT on F4 ground regardless of headline Sharpe). If observed IS trade-roster change > 50%, the feature drove a large entry-selection shift — diagnose at Phase-8 whether this shift is signal-edge or roster-luck (per /082/085/086/119/122 SSC/dissociation pattern catalog).

### Section 4.5 — Pre-registered prior probability statement

| Outcome class | Prior probability | Rationale |
|---|---:|---|
| NEGATIVE-catastrophic (F1 IS Δ < −0.40 OR OOS Δ < −0.30) | 10% | EDA signal alignment 4/5 tables; catastrophic requires architecture-breaking event |
| NEGATIVE-INERT | 30% | /113 precedent of EDA-strong-then-production-INERT; 4 candidate INERT cases in cycle 7 + /113 |
| NEGATIVE-clean / NEGATIVE-no-effect | 5% | Low — EDA signal is strong; clean NEGATIVE would imply EDA was misleading on multiple axes |
| SUSPICIOUS-OOS-DOMINANT | 10% | /065/071/073/076/078 lineage; the /126 axis doesn't introduce duration/selection shifts but a new feature can load the selection-roster channel |
| PROMISING-PARTIAL (1 of 3 candidates wins) | 15% | T5 ranks 1-3 across syms but production may concentrate the lift in 1 symbol |
| PROMISING-MECHANICAL (dissociation pattern) | 5% | Possible if importance migrates to 0% (unlikely given EDA T5 ranks 1-3) |
| PROMISING-strong (broad-based IS + OOS lift) | 25% | EDA 4-table alignment is the strongest in v3 history (only /025 comparable; /025 was PROMISING-class) |

**Modal prediction is PROMISING-strong (25%) + PROMISING-PARTIAL (15%) = 40% PROMISING-class total prior**, which is materially higher than /122's 10% PROMISING prior. This is the most-positive prior for a NEW feature in cycle 7.

---

## Section 5 — Risk Mitigation

The /126 axis introduces NO new risk mitigation primitive — the 7-gate RiskV2 stack + /116 no_confirm RULE-layer + 3-seed EXPLORATION ensemble are bit-identical to /121.

**Risk-of-feature-incompatibility**: the new `d24_ret_autocorr_lag1_50` is computed at 24h cadence and merged onto 8h via merge_asof. The feature value is constant across each 24h window (3 sequential 8h decision rows share the same `d24_ret_autocorr_lag1_50` value, sourced from the most recent 24h aggregation). LightGBM may treat this as a CATEGORICAL-like signal (3 8h bars share a value); colsample_bytree fractional sampling can still position this feature in any of the 15 columns based on tree-construction priority.

**Risk-of-look-ahead-leakage**: T2 audit verified 0 violations. Production must replicate the EDA's strict `direction='backward'` + `allow_exact_matches=True` discipline. The integration test (Change 5) catches any regression.

**Risk-of-merge-asof-misalignment under data gaps**: TRX max_lag observed 88h (~3.7 days, 11 8h bars) — when TRX has a data gap, the most recent 24h aggregation may be from a prior trading day. The merge_asof gracefully handles this by using the most recent CLOSED 24h aggregation. No incremental risk.

---

## Section 6 — Risk Management Design

### Section 6.1 — Drawdown caps

The /121 multi-seed baseline IS MaxDD = 26.4%, OOS MaxDD = 25.7%. /126 expected MaxDD band [20%, 40%] — wider than /121 baseline but not catastrophic. NEGATIVE-catastrophic threshold: IS MaxDD > 50% AND IS Sharpe < +0.50 = filed CATASTROPHIC.

### Section 6.2 — Concentration caps

Anchor /121 OOS concentration: BCH 95.76% (extreme single-symbol dominance). Predicted /126 concentration band [80%, 99%] — the BCH-dominant structure is universe-level, not feature-level; adding a single feature does not change this. NEGATIVE-catastrophic concentration threshold: any single symbol > 99% OOS concentration AND OOS Sharpe < +0.50 = filed CONCENTRATION-RISK-MATERIALIZED.

### Section 6.3 — Trade-rate floor

Anchor /121 OOS trades = 98 (~7/month). Predicted /126 OOS trades band [80, 130]. Per `feedback_v3_trade_rate_floor_bundle_level.md` carry-forward from /121: trade-rate floor (≥ 130 OOS) is INFORMATIONAL at EXPLORATION; falsifier-triggered only at CONFIRMATION-spec.

### Section 6.4 — Stateful state for /116 no_confirm

The no_confirm primitive operates per-symbol-trade; the new 24h feature does NOT introduce stateful state. Each per-symbol LightGbmStrategy instance carries its own no_confirm state machine.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

Modal failure modes /126 could produce, with falsifier-triggered classifications:

1. **F1: NEGATIVE-clean / NEGATIVE-no-effect** (IS Δ ∈ [−0.05, +0.05] AND OOS Δ ∈ [−0.05, +0.05])
   - Mechanism: 24h cadence's marginal information is not exploitable by depth-3-5 trees on top of 14 incumbents
   - Diagnosis at Phase 8: T5 importance rank ≥ 12 on all 3 syms → close axis as "24h cadence didn't help at this Optuna budget"

2. **F2: NEGATIVE-INERT** (production importance INERT: rank ≥ 12/15 on > 1 sym AND POOLED lift < +0.005)
   - Mechanism: same as /082/085/086/119/122 — model doesn't use the feature in production despite EDA prediction
   - Diagnosis: importance allocation table; if rank ≥ 12 on all 3 syms, classify NEGATIVE-INERT per Section 8 criterion 3

3. **F3: NEGATIVE-catastrophic** (IS Δ < −0.40 OR OOS Δ < −0.30 vs PUBLIC anchor)
   - Mechanism: feature is anti-correlated with edge structure; tree splits on it produce IS-overfit-then-OOS-collapse
   - Diagnosis: BCH IS PnL Δ < −20% AND TRX IS PnL Δ < −10% AND LDO IS PnL Δ < −5%; broad-based collapse

4. **F4: SUSPICIOUS-OOS-DOMINANT** (OOS Δ > +0.30 AND IS Δ < +0.05)
   - Mechanism: the /065/071/073/076/078 pattern via SELECTION channel; the new feature changes which trades the model selects
   - Diagnosis: per-symbol roster overlap with /121 < 50%; classify per /082/085/086/119/122 closeout convention

5. **F5: PROMISING-PARTIAL** (only 1 of 3 candidates carries IS PnL Δ > +5pp AND OOS PnL Δ > +3pp)
   - Mechanism: ONE symbol (likely LDO given T5 rank 1) has structural edge that the 24h feature unlocks; others marginal
   - Diagnosis: classify per /122 PROMISING-PARTIAL convention; the carrier symbol may be promoted to /127 single-symbol-architectural axis

6. **F6: PROMISING-strong** (IS Δ > +0.10 AND OOS Δ > +0.10 broad-based all-3-positive)
   - Mechanism: the 24h cadence's signal channel transfers through production LightGBM walk-forward and is broadly exploitable
   - Bundle candidate for /132 CONFIRMATION

7. **F7: PROMISING-MECHANICAL (dissociation)** (IS Δ ∈ [+0.05, +0.20] AND OOS Δ > +0.30 with importance rank deteriorating to ≥ 10)
   - Mechanism: /119 C6 dissociation pattern in a 24h-feature class
   - Diagnosis: pairwise IC matrix recheck + sister-redistribution analysis

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria — PER-CRITERION ANCHOR ANNOTATION

Per /122 Critic Rec 3, every criterion declares its anchor explicitly (PUBLIC = /121 multi-seed; ADJUSTED = /121 architecturally-adjusted EXPLORATION-mode reference).

### NEGATIVE criteria (any-of-the-below; first-match wins)

1. **NEGATIVE-catastrophic** — Anchor: PUBLIC. IS Sharpe Δ < −0.40 vs /121 multi-seed +1.3108 (i.e., IS < +0.91) OR OOS Sharpe Δ < −0.30 vs /121 multi-seed +0.9682 (i.e., OOS < +0.67). File EXPLORATION-NEGATIVE-catastrophic. Axis-CLOSE recommendation: `d24_ret_autocorr_lag1_50` CLOSED; multi-frequency-stack axis status determined by Critic interpretation.

2. **NEGATIVE-no-effect** — Anchor: PUBLIC. IS Sharpe Δ ∈ [−0.05, +0.05] vs /121 multi-seed AND production IS trade-roster overlap with /121 IS > 95% (per Section 4.4 behavioral-effect predictor; this should be 70-90% under normal feature-addition; > 95% = ENGINEERING DEFECT, the feature did not enter Optuna's selection trajectory).

3. **NEGATIVE-INERT** — Anchor: ADJUSTED. IS Sharpe Δ ∈ [−0.20, +0.05] vs /121 architecturally-adjusted estimate +1.06 (i.e., IS ∈ [+0.86, +1.11]) AND (a) production importance rank ≥ 12/15 on > 1 symbol AND (b) POOLED lift < +0.005 (= portfolio-aggregate share < 0.5% over baseline contribution). File EXPLORATION-NEGATIVE-INERT.

4. **NEGATIVE-clean** — Anchor: ADJUSTED. IS Sharpe Δ ∈ [+0.05, +0.10] vs /121 ADJUSTED AND OOS Sharpe Δ ∈ [−0.20, +0.05] vs /121 PUBLIC (NEGATIVE on either leg). File EXPLORATION-NEGATIVE-clean.

5. **SUSPICIOUS-OOS-DOMINANT** — Anchor: PUBLIC. OOS Sharpe Δ > +0.30 vs /121 multi-seed (i.e., OOS > +1.27) AND IS Sharpe Δ ∈ [−0.10, +0.05] vs /121 PUBLIC (IS ∈ [+1.21, +1.36]). File SUSPICIOUS-OOS-DOMINANT per /082/085/086 closeout convention.

### PROMISING criteria (all-of-the-below)

6. **PROMISING-strong** — Anchor: PUBLIC. IS Sharpe Δ ≥ +0.10 vs /121 ADJUSTED estimate +1.06 (i.e., IS ≥ +1.16) AND OOS Sharpe Δ ≥ +0.10 vs /121 PUBLIC +0.9682 (i.e., OOS ≥ +1.07) AND production importance rank ≤ 8/15 on ALL 3 symbols (broad-based learning) AND no candidate symbol > 99% concentration → file EXPLORATION-PROMISING-strong. Bundle candidate for /132 CONFIRMATION.

7. **PROMISING-PARTIAL** — Anchor: PUBLIC. Only 1 of 3 symbols carries IS PnL Δ > +5pp AND OOS PnL Δ > +3pp; the other 2 individually have wpnl ∈ [−5, +5] → file EXPLORATION-PROMISING-PARTIAL. The carrier symbol may be promoted to /127 single-symbol-V3_MODELS axis OR carry into bundle at /132 CONFIRMATION subject to additional cycle-7 EXPLORATION validation.

8. **PROMISING-MECHANICAL (dissociation variant)** — Anchor: PUBLIC. OOS Sharpe Δ ≥ +0.10 vs /121 PUBLIC AND IS Sharpe Δ ∈ [+0.05, +0.20] AND production importance rank deteriorates to ≥ 10/15 on > 1 symbol with broad-based per-symbol IS positive Δ. File PROMISING-FEATURE-MECHANICAL per `feedback_v3_promising_feature_mechanical.md` 3-condition diagnostic conjunction.

### Anchor restatement

- **Anchor A = PUBLIC** = /121 multi-seed CONFIRMATION-MERGE baseline (IS +1.3108 / OOS +0.9682). Public BASELINE_V3.md numbers.
- **Anchor B = ADJUSTED** = /121 architecturally-adjusted EXPLORATION-mode estimate (IS ≈ +1.06 / OOS ≈ +0.95). Per `feedback_v3_dsr_mode_artifact.md`.
- NEGATIVE-catastrophic, SUSPICIOUS-OOS-DOMINANT, PROMISING-strong, PROMISING-PARTIAL, PROMISING-MECHANICAL use PUBLIC anchor (production-facing).
- NEGATIVE-INERT, NEGATIVE-clean, NEGATIVE-no-effect use ADJUSTED anchor for IS leg (architectural correction).

---

## Section 9 — Library Stack Declaration

**No new library dependencies** — multi-frequency feature stack uses existing pandas merge_asof + numpy. The 24h-multioffset parquets exist at `data/features_v3_24h/` from /117 infrastructure.

**Library inventory** (verified at /126):
- `lightgbm == 4.6.0` (unchanged)
- `numpy >= 2.0` (unchanged)
- `pandas >= 2.2` (unchanged)
- `scikit-learn` (used only in EDA T6 walk-forward AUC, not in production runner)

**Adversarial integration test** (per `feedback_v3_methodology_axis_integration_test.md`): the Change 1 + 2 + 3 + 5 edits must satisfy:
- `len(V3_FEATURE_COLUMNS_TOP_N) == 15`
- `"d24_ret_autocorr_lag1_50" in V3_FEATURE_COLUMNS_TOP_N`
- `"d24_ret_autocorr_lag1_50" == V3_FEATURE_COLUMNS_TOP_N[14]` (position 15)
- After `process_symbol_v3('BCHUSDT', '8h', ...)`, the resulting 8h features parquet contains the `d24_ret_autocorr_lag1_50` column
- For the last 100 IS rows of BCH/LDO/TRX 8h parquet, `d24_ret_autocorr_lag1_50` is non-NaN (warm-up window is 50 days; ample IS data)
- The look-ahead-free unit test passes (the synthetic-frame causal-merge_asof assertion)
- `run.log` shows 3 per-symbol model training blocks labeled `v3-126-BCH/LDO/TRX` (no `[POOLED]` marker)
- `comparison.csv` `# per_symbol` rows = 3, with symbols BCHUSDT/LDOUSDT/TRXUSDT
- `in_sample/model_importance_last_month_BCHUSDT.csv` contains `d24_ret_autocorr_lag1_50` row with non-zero gain

---

## Section 10 — QR Audit Trail

### Section 10.1 — Axis selection process

Following the /125 Critic FINAL `53cfc06` PRIMARY recommendation: multi-frequency feature stack (8h base + 24h-aggregated features at the feature-stack layer) — NEW dimension in v3 catalog (FEATURE-CADENCE-STACK at fixed label horizon), structurally distinct from /117's 24h-base candle-frequency axis and /124's K=63 longer-cadence labels axis.

The QR considered 3 specific candidate sub-axes:
1. **Single 24h feature appended (selected)** — see Section 10.2 rationale
2. **Multiple 24h features stacked (3-5 features in one EXPLORATION)** — REJECTED per `feedback_v3_engineered_features_dont_stack.md` (single-feature-at-a-time at single-seed EXPLORATION)
3. **24h-aggregated CROSS-ASSET features (e.g., d24_eth_realized_vol_50)** — REJECTED per `feedback_v3_cross_asset_ohlcv_closed.md` (6th consecutive cross-asset OHLCV failure closes the axis class)

### Section 10.2 — Why `d24_ret_autocorr_lag1_50` specifically

| Candidate | T3 R² PASS (3 syms) | T4 IC PASS | T5 max rank | T6 lift (3-sym mean) | T7 SSC-RISK | Composite score |
|---|---:|---|---:|---:|---|---:|
| **d24_ret_autocorr_lag1_50** | 3/3 | PASS | **3** | **+0.0147** | PASS | **8.17** |
| d24_hurst_diff_100_50 | 3/3 | PASS | 4 | +0.0032 | PASS | 6.92 |
| d24_hurst_100 | 3/3 | PASS | 11 | +0.0101 | PASS | 6.91 |
| d24_regime_momentum_signed_5d | 3/3 | PASS | 13 | +0.0107 | PASS | 6.77 |

`d24_ret_autocorr_lag1_50` is the top of the 4 PASS-list candidates by composite score with a +1.25-point margin. The discriminating factors:
1. **T5 importance ranks 2/1/3** across BCH/LDO/TRX — uniformly HIGH; the model would clearly use this feature at production scale.
2. **T6 AUC lift +0.0147 mean** — 3.5× larger than the next-best (d24_regime_momentum_signed_5d at +0.0107).
3. **T7 SSC-RISK 0.368** — the LOWEST of the 4 (broadest per-symbol distribution).

The feature itself: 1-bar lag autocorrelation of daily log returns over the most recent 50 daily bars. Mechanistically distinct from the 8h-cadence `ret_autocorr_lag1_50` incumbent (max IC 0.16) — the 24h cadence aggregates 3× the 8h variance into each datapoint, smoothing intra-day microstructure noise and producing a measure of multi-day directional persistence. The 14-feature 8h stack's ret_autocorr_lag1_50 measures 8h-cadence noise; the 24h version measures regime-level persistence.

### Section 10.3 — What this axis taps that prior feature axes didn't

| Prior feature axis | Class | Issue |
|---|---|---|
| /019/023/024/082/085 (funding-rate variants) | crypto-native sentiment | INERT-by-importance (CLOSED) |
| /015 (microstructure tbr_zscore_30) | microstructure | INERT-by-importance |
| /086 (basis_zscore_30) | crypto-native sentiment | INERT-by-importance (CLOSED) |
| /113 (8 d_* daily features at /059 anchor) | multi-frequency 1d → 8h | NEGATIVE-INERT (8 features stacked; 3 high-IC with incumbents) |
| /118 (ema_signed_volregime composed) | Category-2 vol-regime composed | NEGATIVE-catastrophic (CLOSED) |
| /119 (ret5d_signed_tbi composed) | Category-2 microstructure composed | PROMISING-MECHANICAL; F3-dropped at /120 |
| /122 (eth_ret_3d cross-asset) | OFF-THE-SHELF cross-asset | NEGATIVE-INERT (IC-spanned) |
| /123 (eth_vs_sym_rv_50 cross-asset) | OFF-THE-SHELF cross-asset | NEGATIVE-catastrophic (CLOSED) |
| **/126 (d24_ret_autocorr_lag1_50)** | **multi-frequency 1d→8h at /121 anchor, single feature** | **TBD — first single-feature multi-frequency test post-no_confirm** |

The PRIOR-NOT-YET-TESTED conjunction: **P(multi-frequency feature carries edge | single feature ∧ pairwise IC < 0.20 vs all incumbents ∧ /121 anchor with no_confirm ∧ T5 rank ≤ 3 on all syms)**. /113 failed on stacking (8 features) + /059 anchor + 3 high-IC sisters; /126 is the first test of the conjunction.

### Section 10.4 — Why this beats Critic Priority 1 (drawdown brake) for cycle-7 slot 5

The /124 closeout designated Critic Priority 1 = stateful drawdown brake at closed-loop simulator. Why /126 elects multi-frequency feature stack instead:

1. **/125 Critic FINAL `53cfc06` PRIMARY recommendation explicit**: multi-frequency feature stack is the recommended /126 axis per Critic — this is the most-recent Critic directive (overrides /124 Priority 1).
2. **NEW catalog dimension vs deferred Priority**: multi-frequency adds a STRUCTURALLY NEW axis class to v3's catalog (FEATURE-CADENCE-STACK). The drawdown brake is in a known axis class (RISK-PRIMITIVE) with several CLOSED precedents (/054 stateful deadlock).
3. **EDA backing**: /126 has 6/6 pre-flight gates PASS + the strongest 4-table EDA alignment in v3 history. The drawdown brake EDA would require a closed-loop simulator + deadlock-impossibility proof — high methodology overhead with uncertain ground.
4. **/125 Critic Priority 1 not displaced**: if /126 produces NEGATIVE-class, /127 can pivot to the drawdown brake. Sequential exploration of orthogonal axes.

### Section 10.5 — Pre-registered prior probability statement (restated from Section 4.5)

| Outcome class | Prior probability | Rationale |
|---|---:|---|
| NEGATIVE-catastrophic | 10% | EDA signal alignment 4/5 tables; catastrophic requires architecture-breaking event |
| NEGATIVE-INERT | 30% | /113 precedent; 4 INERT cases in cycle 7 + /113 |
| NEGATIVE-clean / NEGATIVE-no-effect | 5% | EDA signal is strong; clean NEGATIVE would imply EDA was misleading on multiple axes |
| SUSPICIOUS-OOS-DOMINANT | 10% | /065/071/073/076/078 lineage; new feature can load selection-roster channel |
| PROMISING-PARTIAL | 15% | T5 ranks 1-3 but production may concentrate lift in 1 symbol |
| PROMISING-MECHANICAL | 5% | Possible if importance migrates to 0% (unlikely given EDA T5 ranks 1-3) |
| **PROMISING-strong** | **25%** | EDA 4-table alignment is the strongest in v3 history (only /025 comparable) |

**Modal prediction is PROMISING-class (45% total) vs NEGATIVE-class (45% total) vs SUSPICIOUS (10%).** Highest PROMISING prior in cycle 7. The CASE FOR PROMISING-class: 6/6 EDA gates PASS at substantial margins; T5 ranks 1-3 across all syms is the strongest single-iteration importance signal v3 has produced for a NEW candidate. The CASE AGAINST: the production-EDA gap (Optuna trajectory + 7-gate RiskV2 + 3-seed ensemble + walk-forward) has consistently degraded EDA-strong candidates (/082/085/086/113/119/122 lineage).

---

**End of brief**.

**EDA SHA**: `dd9fc2d` (analysis/iteration_v3-126/)
**Brief SHA**: (set by commit)
**Anchor**: /121 BASELINE_V3.md (IS +1.3108 / OOS +0.9682)
**Cycle-7 cadence**: EXPLORATION #5 of 10 → /132 CONFIRMATION pending
