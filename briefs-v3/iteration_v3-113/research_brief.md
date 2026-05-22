# iter-v3/113 — Research Brief — Multi-Frequency Feature Engineering (coarser 1d daily features added to the 8h model)

**Cycle-6 EXPLORATION slot #4 of 10** (iter-v3/120 is the mandatory cycle-6 CONFIRMATION).
**Branch:** `iteration-v3/113`.
**Axis:** cycle-6 axis-menu item 3 — multi-frequency feature engineering (`project_v3_cycle6_axis_menu.md`).

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_DATE = 2025-03-24` — **UNCHANGED**, IMMUTABLE.
- `training_months = 24` — **UNCHANGED**, IMMUTABLE.
- **IS window:** earliest data per symbol → 2025-03-23 (BCH from 2020-01-01, TRX from 2020-01-15, LDO from 2022-09-22).
- **OOS window:** 2025-03-24 → present (~2026-05-19).
- The walk-forward backtest runs on ALL data as one continuous process; the reporting layer splits trades at `OOS_CUTOFF_DATE` into `in_sample/` and `out_of_sample/`. The QR saw OOS for the first time never — all Phase 1-5 EDA is strictly IS-only (`analysis/iteration_v3-113/_shared.py` asserts `close_time < OOS_CUTOFF_MS` per symbol and on the assembled frame).

---

## Section 0.5 — Iteration Type Declaration

**TYPE: EXPLORATION.**

- **Run command:** `uv run python run_baseline_v3.py --exploration --n-trials 35 --clean-oof`
- **Config:** `--exploration` flag → ENSEMBLE_SIZE=3, single outer-seed lineage (seeds 191664963, 1662057957, 1405681631 — the outer=42 lineage), `colsample_bytree` Optuna-tuned, `--n-trials 35` (the v3 EXPLORATION default per `feedback_v3_exploration_n_trials_35.md`).
- **Wall-clock budget: HARD CAP 2h.** The /112 pooled EXPLORATION ran 0.43h and the /111 universe EXPLORATION ran 1.09h, both at this config on the BCH/LDO/TRX universe; adding 8 feature columns to a 3-symbol per-symbol architecture changes wall-clock negligibly. 2h cap is comfortable.
- **Single-axis discipline:** the ONE axis varied vs the /059 canonical baseline is the **feature set** — `V3_FEATURE_COLUMNS` grows from the 14-feature 8h-only anchor to 22 (the 14 anchor features + 8 new coarser-frequency daily features). The universe (BCH/LDO/TRX), the `triple_barrier` label (2:1 ATR, 21-candle timeout), the LightGBM architecture, the 7-gate RiskV2 stack, the ensemble seeds, and the data window are all held /059-identical. This is genuinely single-axis and genuinely structural (a NEW representation), per the `feedback_structural_over_knob_exploration.md` counter-rule ("single-axis ≠ single-knob").
- **Type justification:** EXPLORATION is correct — this is a single-axis test of a NEW feature representation, not a bundle of prior PROMISING components. No CONFIRMATION precedent is required for an EXPLORATION. iter-v3/120 remains the mandatory cycle-6 CONFIRMATION.

---

## Section 1 — Hypothesis

**Adding a family of coarser-frequency (1-day / daily) features — computed on daily bars aggregated look-ahead-free from the 8h candles and causally as-of-joined onto the 8h decision grid — to the 8h model's 14-feature stack lifts OOS monthly Sharpe, because the daily representation smooths the 8h microstructure noise that the /105→/109 chain proved the 8h-only representation cannot see directional signal through, and the EDA confirms the daily feature family carries permutation-validated standalone predictive signal (pooled daily-only held-out AUC 0.5275, p=0.0 vs its no-signal null) that the 14-feature 8h stack does not already supply.**

---

## Section 2 — IS-Only Numerical Evidence

All evidence produced by the committed EDA `analysis/iteration_v3-113/` (EDA SHA `ebd84e2`): `_shared.py` (the /059-faithful IS-only triple-barrier labeler + the daily-aggregation + daily-feature builder), `multifreq_gating_eda.py` (T1–T8), `orthogonal_subset_annex.py` (T9–T12). Strictly IS-only — every script's loader asserts `close_time < OOS_CUTOFF_MS` (2025-03-24). Walk-forward-faithful per `feedback_v3_eda_walkforward_faithful.md`: held-out AUC is measured on 5 expanding-window walk-forward folds inside the IS window with a 22-candle embargo purged before each test fold — NOT the full IS panel as one block.

### 2.1 The axis design — why daily (coarser), and how it is look-ahead-free

The v3 8h candles open at exactly **00, 08, 16 UTC** — three per UTC day (verified: all three symbols, `open hours [0, 8, 16]`). A 1-day bar is therefore an **exact, look-ahead-free aggregation** of three consecutive 8h candles: `open` = first 8h open, `high` = max 8h high, `low` = min 8h low, `close` = last 8h close, `volume` = sum. No new data is fetched — the daily bars are built from the 8h candles the runner already loads. The daily features are attached to each 8h decision row by a **causal backward `merge_asof`** keyed on `daily.day_close ≤ 8h.open_time`: the 8h model deciding at `open_time` t may use only daily bars whose final 8h sub-candle closed at or before t. This is the cleanest possible multi-frequency design — zero new data dependency, zero sub-bar alignment ambiguity, a trivially-auditable look-ahead surface.

The 8 candidate daily features span three mechanism groups (full definitions in `_shared.py:_add_daily_features`): **trend/momentum** (`d_ret_5d`, `d_ret_10d`, `d_trend_slope_10`), **volatility regime** (`d_realvol_10`, `d_realvol_ratio`, `d_atr_pctrank_60`), **path efficiency** (`d_efficiency_10`, `d_close_pos_20`). All scale-invariant, all strictly past-only (no centered windows).

### 2.2 T5 — the headline: the daily representation carries permutation-validated standalone signal

`T5_daily_only_signal.csv` — a LightGBM trained on the **8 daily features ALONE** (no 8h features), pooled walk-forward held-out AUC, vs its own 100-shuffle permutation null:

| Model | Observed held-out AUC | Null q50 | Null q95 | Permutation p-value | Clears q95? |
|---|---:|---:|---:|---:|:--:|
| **daily-ONLY pooled** | **0.5275** | 0.4997 | 0.5093 | **0.00** | **YES** |

**This is the single most important number in the brief.** The daily-only stack's held-out AUC (0.5275) clears its no-signal permutation q95 (0.5093) decisively — permutation p-value 0.00 (zero of 100 label-shuffles reached 0.5275). This is **the first non-spurious feature→label directional signal measured anywhere in v3's diagnostic chain since the /109 terminal 8h-representation null** (where the 8h 14-feature stack scored AUC 0.497 at the no-signal q50, p=0.64). The coarser bar frequency is a genuinely different signal-to-noise regime — exactly as the /109 diary §3 anticipated. The daily representation sees structure the 8h representation cannot.

### 2.3 T1 / T3 — the combined 8h+daily stack: per-symbol and pooled

`T1_walkforward_auc.csv` — walk-forward held-out AUC, the 14-feature 8h-only stack vs the 22-feature 8h+daily-8 stack:

| Symbol | n_rows | n_folds | AUC 8h-only | AUC 8h+daily | AUC lift |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 5,544 | 5 | 0.4983 | 0.4931 | **−0.0052** |
| LDOUSDT | 2,559 | 5 | 0.4801 | 0.5083 | **+0.0281** |
| TRXUSDT | 5,487 | 5 | 0.4518 | 0.4657 | **+0.0139** |
| **POOLED** | 13,590 | 5 | 0.4889 | 0.5015 | **+0.0126** |

The combined stack lifts pooled held-out AUC +0.0126 and lifts 2 of 3 symbols (LDO strongest at +0.0281, TRX +0.0139; BCH marginally negative −0.0052). The 8h-only AUCs sit at-or-below 0.50 — the /109 null, re-confirmed. The combined stack pulls the pooled number above 0.50 for the first time.

### 2.4 T4 / T10 — the stacking caveat: the combined stack does NOT clear its permutation null

`T4_permutation_null.csv` and `T10_ortho_permutation_null.csv` — the permutation null applied to the **combined** stacks:

| Stack | Observed pooled AUC | Null q95 | Permutation p-value | Clears q95? |
|---|---:|---:|---:|:--:|
| 8h + daily-8 (full) | 0.5015 | 0.5088 | 0.39 | **NO** |
| 8h + daily-orthogonal-4 | 0.4982 | 0.5102 | 0.54 | **NO** |

**This is the honest caveat and it is reported up front.** While the daily features carry signal *standalone* (T5), the *combined* 8h+daily stack — full-8 or orthogonal-4 — does NOT clear its own permutation q95. Mechanism: the daily signal is real but small in absolute magnitude (AUC ~0.5275, a 2.75-point edge over chance), and the 14-feature 8h stack is the dominant component the combined model fits. The daily signal is genuine but does not survive concatenation into a model dominated by the larger, near-noise 8h stack. **This is why the EDA verdict is SHARPENED-GO, not a clean GO** (Section 2.8).

### 2.5 T7 — the IC redundancy structure (Critic Check 4 input)

`T7_ic_redundancy.csv` — each daily feature's correlation against the closest-mechanism 8h feature and its max |IC| against the whole 8h stack:

| Daily feature | Nearest 8h feature | IC vs nearest | Max \|IC\| vs 8h stack | Max-IC partner | Redundant (\|IC\|>0.70)? |
|---|---|---:|---:|---|:--:|
| d_ret_5d | regime_momentum_signed_5d | 0.849 | 0.849 | regime_momentum_signed_5d | **YES** |
| d_ret_10d | regime_momentum_signed_5d | 0.596 | 0.773 | ema_spread_atr_20 | **YES** |
| d_realvol_10 | range_realized_vol_50 | 0.806 | 0.806 | range_realized_vol_50 | **YES** |
| d_close_pos_20 | vwap_dev_20 | 0.555 | 0.849 | ema_spread_atr_20 | **YES** |
| d_trend_slope_10 | ema_spread_atr_20 | 0.052 | 0.052 | ema_spread_atr_20 | no |
| d_realvol_ratio | range_realized_vol_50 | −0.010 | 0.178 | sym_vs_btc_ret_7d | no |
| d_atr_pctrank_60 | range_realized_vol_50 | 0.211 | 0.211 | range_realized_vol_50 | no |
| d_efficiency_10 | hurst_100 | 0.078 | 0.111 | ema_spread_atr_20 | no |

Four of eight daily features are mechanically redundant with the 8h stack (|IC| > 0.70). This is **expected and not disqualifying**: a daily return and an 8h-derived momentum feature measure the same *mechanism* (trend) at a different *frequency*. Per `feedback_v3_engineered_feature_pivot.md`, the strict |IC| < 0.70 family gate has a documented carve-out for features that are mechanically related but encode a different construction of the same primitive — and a multi-frequency feature is precisely the "different frequency of the same mechanism" case. The four orthogonal daily features (`d_trend_slope_10`, `d_realvol_ratio`, `d_atr_pctrank_60`, `d_efficiency_10`, all max |IC| < 0.30) are the genuinely-new carriers. **Section 4.4 pre-registers the QR's position for the Critic on this.**

### 2.6 T9 / T11 — the orthogonal-4 subset was tested and did NOT cleanly improve on the full-8

The natural hypothesis from T7 — "prune the 4 redundant daily features, keep only the 4 orthogonal ones, and the combined stack will recover its permutation-null clearance" — was tested directly in the annex:

| Stack | Pooled AUC | Clears perm q95? | Per-symbol gated-tail lift (T8/T11) |
|---|---:|:--:|---|
| 8h + daily-8 (full) | 0.5015 | NO (p=0.39) | BCH **+0.0285**, LDO **+0.0195**, TRX **+0.0121**, pooled +0.0306 — **all positive** |
| 8h + daily-orthogonal-4 | 0.4982 | NO (p=0.54) | BCH −0.0052, LDO −0.0307, TRX −0.0076, pooled +0.0362 — **per-symbol negative** |

Pruning to the orthogonal-4 did **not** recover the combined-null clearance — and it **inverted the per-symbol gated-tail hit-rate lift** (the production proxy) from positive-on-all-3-symbols (full-8) to negative-on-all-3-symbols (orthogonal-4). The orthogonal-4 verdict is SHARPENED-GO (2/4). **There is no EDA basis to prefer the smaller set** — the 4 "redundant" features, while IC-correlated, evidently still contribute to the per-symbol gated-tail behaviour. This directly informs the Section 3 design decision: ship the **full 8 daily features**, not a pruned subset.

### 2.7 T8 — gated-tail hit rate (the production proxy): the full-8 stack lifts ALL three symbols

`T8_gated_tail_hit_rate.csv` — directional hit rate in the top-decile-confidence tail of the OOF predictions (the v3 7-gate stack only trades high-confidence signals, so this is the closest IS proxy to the production book):

| Symbol | Gated hit 8h-only | Gated hit 8h+daily-8 | Gated-tail lift |
|---|---:|---:|---:|
| BCHUSDT | 0.4715 | 0.5000 | **+0.0285** |
| LDOUSDT | 0.4903 | 0.5097 | **+0.0195** |
| TRXUSDT | 0.4591 | 0.4712 | **+0.0121** |
| **POOLED** | 0.4528 | 0.4835 | **+0.0306** |

The full-8 daily family lifts the gated-tail hit rate on **all three symbols and pooled** — including BCH, whose plain held-out AUC lift (T1) was marginally negative. In the confident tail — where the production gates actually let trades through — the daily features help everywhere. This is the most production-relevant table in the EDA and it is uniformly positive for the full-8 stack.

### 2.8 T2 — the aggregate verdict

`T2_go_nogo_verdict.csv`: the GO/NO-GO across 4 criteria — C1 pooled AUC lift > 0 (**True**, +0.0126), C2 combined stack clears permutation q95 (**False**), C3 ≥2 of 3 symbols lift (**True**, LDO+TRX), C4 pooled gated-tail lift > 0 (**True**, +0.0306). **3 of 4 criteria cleared → verdict GO** (the script's threshold; ≥3 = GO). Read together with T4 — the one failed criterion is the combined-stack permutation null — the honest reading is a **SHARPENED-GO**: a real, permutation-validated signal exists in the daily representation (T5, decisive), the full-8 family lifts the production proxy on every symbol (T8), but the combined-stack edge is small and does not itself clear a permutation null. Per **THE PRIME DIRECTIVE**, a SHARPENED-GO is not a stop — the EDA designed the sharpest experiment it can and the Phase-6 backtest is the decisive test of whether the daily signal converts to OOS Sharpe through the full production Optuna + 7-gate pipeline. The EDA's role was to find the signal (T5 did) and shape the expected-impact interval (Section 4 does, weighting the combined-stack caveat).

---

## Section 3 — Proposed Changes

### 3.1 Summary of the single axis

`V3_FEATURE_COLUMNS` grows from the **14-feature 8h-only anchor** to **22 features** = the 14 anchor features + **8 new coarser-frequency daily features**: `d_ret_5d`, `d_ret_10d`, `d_trend_slope_10`, `d_realvol_10`, `d_realvol_ratio`, `d_atr_pctrank_60`, `d_efficiency_10`, `d_close_pos_20`. Nothing else changes vs /059.

**Why the full 8 and not the orthogonal-4 subset:** Section 2.6 — the orthogonal-4 subset was tested in the EDA annex and did NOT clear the combined-null any better than the full-8, AND it inverted the per-symbol gated-tail hit-rate lift from positive-on-all-3 (full-8, T8) to negative-on-all-3 (orthogonal-4, T11). The EDA tested the pruning hypothesis and did not confirm it; there is no EDA basis to ship the smaller set. The full-8 family is shipped and production Optuna (`n_trials=35`, a larger search than the EDA's fixed 120-tree LightGBM, with Optuna-tuned `colsample_bytree`) allocates split capacity across the 22 columns.

- **Labeling:** UNCHANGED. `label_mode="triple_barrier"`, ATR multipliers (atr_tp=2.0, atr_sl=1.0), 21-candle (10080-min) timeout, `natr_21_raw` ATR column, fee 0.1%. `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}` (empty).
- **Symbols:** UNCHANGED. `V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT)` — the canonical /059 universe. No symbol added or removed. `V3_EXCLUDED_SYMBOLS` unchanged (the 8 daily features are derived from the v3 symbols' own 8h candles — no new symbol is touched).
- **Features:** `V3_FEATURE_COLUMNS` 14 → 22 (the 8 daily features added). This is the SOLE axis.
- **Risk gates:** UNCHANGED. The 7-gate RiskV2 stack, `RiskV2Config` (zscore_threshold=2.0, adx_threshold=20.0, BTC_TREND_CONFIG.threshold_pct=15.0, per-symbol drawdown brake disabled, regime gate disabled, per-symbol cap disabled) — all /059-identical.
- **Walk-forward / CPCV / embargo:** UNCHANGED. `REQUIRED_GAP = 66 = (21+1) × 3` (the /111/112 state — 3-symbol universe). The walk-forward embargo fix (`e149e9d`, 22 candles, `train_end_ms = test_start_ms − embargo_ms`) inherited unchanged.

### 3.2 Configuration Diff vs /059 canonical baseline

| Knob | /059 canonical | iter-v3/113 | Changed? |
|---|---|---|:--:|
| `V3_FEATURE_COLUMNS` | 14 (8h-only anchor) | **22** (14 anchor + 8 daily) | **YES — the SOLE axis** |
| `V3_MODELS` | BCH/LDO/TRX | BCH/LDO/TRX | no |
| `label_mode` | `triple_barrier` | `triple_barrier` | no |
| ATR multipliers | (2.0, 1.0) | (2.0, 1.0) | no |
| Triple-barrier timeout | 21 candles | 21 candles | no |
| `REQUIRED_GAP` | 66 | 66 | no |
| Walk-forward embargo | 22 candles (`e149e9d`) | 22 candles | no |
| 7-gate RiskV2 stack | as /059 | as /059 | no |
| `RiskV2Config` | as /059 | as /059 | no |
| ENSEMBLE_SIZE (EXPLORATION) | n/a (EXPLORATION=3) | 3 | EXPLORATION default |
| `n_trials` | 35 | 35 | no |
| `ITERATION_LABEL` | `"v3-112"` | **`"v3-113"`** | YES (mechanical) |

Exactly ONE substantive knob changes: `V3_FEATURE_COLUMNS` (14 → 22). `ITERATION_LABEL` is the mechanical per-iteration bump. This is the cleanest single-axis EXPLORATION possible.

### 3.3 vs /112 (the immediately-prior iteration)

iter-v3/112 ran a POOLED model architecture on the same universe and closed EXPLORATION-NEGATIVE; its only `src/` changes were the pooled-collapse logic, a universe revert, and `REQUIRED_GAP` 88→66. iter-v3/113 **reverts the /112 pooled architecture back to per-symbol** (the /059-canonical architecture) — the runner trains three separate `LightGbmStrategy` instances, one per symbol, as it has for all iterations except /112. `REQUIRED_GAP` stays at 66 (already correct from /112). The CRV/AAVE/GRT/ADA probe-symbol sweep from /110-112 is not re-run.

### 3.5 — Precise `src/` Changes for the QE (Phase 6)

The QE implements exactly the following. **No scope creep** — every change below maps to the single feature-set axis.

**(1) New feature module — `src/crypto_trade/features_v3/multifreq_v3.py`.**

A new track-isolated module (NO imports from `crypto_trade.features` or `crypto_trade.features_v2` — the Phase-6 grep check must stay empty). It exposes `add_multifreq_v3_features(df: pd.DataFrame) -> pd.DataFrame` following the established v3 feature-module signature (cf. `technical_v3.py`, `cross_btc_v3.py`): takes one symbol's 8h DataFrame, returns a copy with the 8 daily feature columns appended. The implementation is **a direct port of the committed EDA's `analysis/iteration_v3-113/_shared.py` functions `_aggregate_to_daily` + `_add_daily_features` + the causal `merge_asof`** — the QE copies that logic verbatim into the module so the production feature is bit-identical to the EDA-validated feature. The three steps inside `add_multifreq_v3_features`:
  - **(a) Aggregate** the input 8h frame to daily bars: `day_open = (open_time // 86_400_000) * 86_400_000`, group by `day_open`, take `open`=first / `high`=max / `low`=min / `close`=last / `volume`=sum / `day_close`=last `close_time` / `n_8h`=group size. (Verbatim from `_shared.py:_aggregate_to_daily`.)
  - **(b) Compute** the 8 daily features on the daily bars — `d_ret_5d`, `d_ret_10d`, `d_trend_slope_10`, `d_realvol_10`, `d_realvol_ratio`, `d_atr_pctrank_60`, `d_efficiency_10`, `d_close_pos_20`. (Verbatim from `_shared.py:_add_daily_features` — the exact rolling-window definitions; all strictly past-only.)
  - **(c) Causal `merge_asof`** the 8 daily columns onto the 8h frame: `pd.merge_asof(df_8h, daily[["day_close"] + DAILY_FEATURES], left_on="open_time", right_on="day_close", direction="backward", allow_exact_matches=True)`. The `day_close ≤ open_time` direction guarantees the daily bar is fully closed before the 8h decision candle opens — the look-ahead-free alignment.
The module preserves the `had_open_time_index` reset/restore guard that `cross_btc_v3.py` uses (handle the case where `df` is indexed by `open_time`). Drop the `day_close` join-key column before returning so only the 8 feature columns are added.

**(2) Register the module in `GROUP_REGISTRY`** (`src/crypto_trade/features_v3/__init__.py`). Add `"multifreq_v3": add_multifreq_v3_features` to the dict. **Ordering: no dependency** — the daily features are computed from raw OHLCV only, so the group can be registered anywhere; place it after `cross_btc` for tidiness. Add the import at the top of `__init__.py`.

**(3) Extend `V3_FEATURE_COLUMNS_TOP_N`** (`src/crypto_trade/features_v3/__init__.py`) from the 14-feature anchor to 22 by appending the 8 daily feature names **in this exact order**: `d_ret_5d`, `d_ret_10d`, `d_trend_slope_10`, `d_realvol_10`, `d_realvol_ratio`, `d_atr_pctrank_60`, `d_efficiency_10`, `d_close_pos_20`. `V3_FEATURE_COLUMNS = V3_FEATURE_COLUMNS_TOP_N` (the alias) propagates automatically. Update the module docstring's feature-count history line. **The runner must pass `feature_columns=list(V3_FEATURE_COLUMNS)` (22 elements) to every `LightGbmStrategy`** — never `None`, never auto-discovered (`feedback_v3_explicit_feature_columns`). The runner's `_verify_feature_columns` assertion count, if it hardcodes 14, must be updated to 22.

**(4) `ITERATION_LABEL`** in `run_baseline_v3.py` line 131: `"v3-112"` → `"v3-113"`.

**(5) Revert /112's pooled architecture to per-symbol.** iter-v3/112 added pooled-collapse logic in `_run_single_seed`. iter-v3/113 runs the **per-symbol** architecture (the /059 canonical). The QE ensures the runner builds three separate `LightGbmStrategy` instances (one per `V3_MODELS` entry) — i.e. the `_is_pooled` path is NOT taken. The cleanest implementation: `V3_MODELS = (BCHUSDT, LDOUSDT, TRXUSDT)` with three distinct labels (not the `"v3-pooled"` sentinel), so `_is_pooled = len(set(_labels)) == 1` evaluates False. If /112's pooled-collapse code is left in place as dormant infrastructure that is acceptable (zero revert cost) as long as the per-symbol path is the one executed — confirm via `run.log` ("MODEL ... [POOLED ...]" must NOT appear; three per-symbol model blocks must).

**(6) No new data fetch.** The daily features are aggregated from the existing `data/<SYMBOL>/8h.csv` candles. The QE does **not** fetch 1h/4h/1d data — the design is deliberately built so no new-interval data is required. (This also keeps the feature-parquet regeneration a single `--skip-features`-off run on the existing 8h CSVs.)

**(7) Feature parquet regeneration.** The QE regenerates the 3 v3 feature parquets (`data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet`) so the 8 new columns are present, then runs the backtest. The pre-flight staleness + forming-candle checks (`fetcher.py` drops `close_time >= now_ms`) are inherited unchanged.

**(8) `ABSENT`-assertion list — no change needed.** The 8 new daily feature names are not on any runner `ABSENT`-ban list (those bans cover `adx_14`, `alpha032`, the basis family, the funding family, etc.). The new names are clean. The QE does NOT add the 8 daily features to any ban list — they are the iteration's payload.

**Test coverage the QE adds:** a `tests/` unit test for `add_multifreq_v3_features` asserting (a) the 8 columns are appended, (b) **the past-only property** — appending future 8h rows to the input frame does not change any daily feature value at an earlier row (the adversarial look-ahead test, mirroring the `technical_v3` ADX past-only test), (c) the `merge_asof` aligns each 8h row to a daily bar whose `day_close ≤ open_time`.

---

## Section 4 — Expected OOS Impact

**Anchor: the /060 EXPLORATION-mode reference — IS monthly Sharpe +0.8325 / OOS monthly Sharpe +0.1403** (per `feedback_v3_cycle1_axis_pass_criteria.md`; cycle-6 EXPLORATIONs anchor on /060, the 3-seed EXPLORATION-mode reference, NOT /059's 10-seed CONFIRMATION). All deltas below are vs /060.

### 4.1 Point estimate and interval

- **OOS monthly Sharpe — point estimate: +0.30** (Δ +0.16 vs /060). **80% interval: [−0.25, +0.85]** (Δ interval [−0.39, +0.71]).
- **IS monthly Sharpe — point estimate: +0.90** (Δ +0.07 vs /060). **80% interval: [+0.35, +1.25]**.

The interval is **deliberately wide and centered only modestly positive**, weighting the EDA's combined-stack caveat heavily, per the iter-v3/112 Lesson 2 (an aggregate-NO-GO / per-symbol-conditional-GO EDA must have its predicted interval weighted toward the caveat). Here the structure is the inverse-but-analogous: the daily family has a *decisive standalone* signal (T5) but the *combined* stack does not clear its permutation null (T4). The point estimate is positive (the standalone signal + the all-3-symbol gated-tail lift in T8 are real evidence) but only modestly so, and the interval's lower bound is comfortably negative because the combined-stack edge is small enough that the production Optuna + 7-gate pipeline could wash or invert it.

### 4.2 BCH IS sensitivity (mandatory per `feedback_v3_cycle1_axis_pass_criteria.md` / /059 Critic Rec #3)

BCH carries **95.76% of /059's IS PnL** — any axis that degrades BCH IS contribution risks collapsing the headline IS Sharpe. The EDA's BCH-specific signals: BCH's plain held-out AUC lift (T1) is marginally **negative** (−0.0052) — the daily features do not improve BCH's raw AUC. BUT BCH's **gated-tail hit rate** (T8, the production proxy) **lifts +0.0285** — the largest per-symbol gated-tail lift of the three. **Prediction:** BCH IS contribution is approximately preserved or modestly improved — the daily features add value to BCH specifically in the confident tail where the gates trade, while leaving BCH's bulk-AUC roughly flat. The IS-sensitivity risk is **LOW-to-MODERATE**: this axis does not selectively help LDO/TRX at BCH's expense (T8 lifts all three); the failure mode is a uniform wash, not a BCH-specific collapse. If BCH IS PnL share falls materially below 90% in the result, that is a flag — but the EDA does not predict it.

### 4.3 Behavioral-effect predictor (mandatory per `feedback_v3_axis_saturation_predictor.md`)

**Explicit trade-count prediction:** adding 8 features to the model changes which candles clear the confidence gates, so the IS and OOS trade rosters **will shift** — this is not a saturated axis. Estimate: **IS trade count changes by 10–35% of the roster** (the daily features re-rank confidence on roughly a third of the bars near the gate threshold; the gated-tail hit-rate lift in T8 is direct evidence the confident-tail composition changes). **OOS trades: predicted 75–130** (the /059 OOS roster was 94 trades; the /060 EXPLORATION-mode roster is comparable; an 8-feature addition does not drastically change the gate-pass rate, so the OOS roster stays in the same order of magnitude). **Falsifier on saturation:** if the IS trade roster changes by **< 8%** vs the /060 roster, the axis is behaviorally inert (the daily features were not actually consulted by the gates) and the iteration is filed INERT regardless of the Sharpe — Section 7 Mode 3.

### 4.4 Pre-registered QR position for the Critic — the T7 IC redundancy (Check 4)

The EDA's T7 shows 4 of 8 daily features have |IC| > 0.70 with the 8h stack. **The QR's pre-registered position:** this is **expected and within the documented `feedback_v3_engineered_feature_pivot.md` carve-out**. That rule established that the strict |IC| < 0.70 family gate is inapplicable to features that are mechanically related to their primitives by construction — and a multi-frequency feature (a *daily* return vs an *8h*-derived momentum feature) is exactly the "different construction of the same mechanism" case the carve-out covers: the daily feature is a coarser-grid measurement of the same trend/vol primitive, and the IC correlation is a mechanical consequence of measuring the same thing at a different frequency, NOT evidence of redundancy that should block the iteration. The genuinely-new content is the *frequency* — and T5 proves the daily family as a whole carries permutation-validated signal the 8h stack does not supply (the decisive evidence that the daily representation is not redundant in aggregate). The QR requests the Critic score Check 4 with the carve-out applied; the 4 high-IC daily features are retained because (Section 2.6) the EDA tested dropping them and the drop inverted the per-symbol gated-tail lift.

### 4.5 Falsifier

The hypothesis is **rejected** (EXPLORATION-NEGATIVE) if **OOS monthly Sharpe Δ vs /060 < −0.20** (OOS monthly Sharpe < −0.06) — i.e. the daily-feature axis materially degrades OOS. The hypothesis is **INERT** if the IS trade roster changes by < 8% (Section 4.3) or if both IS Δ ∈ [−0.10, +0.10] AND OOS Δ ∈ [−0.20, +0.20] (the /060 noise band).

---

## Section 5 — Risk Mitigation

iter-v3/113 changes **only the feature set**; it adds no new risk primitive and modifies no existing one. The /059 7-gate RiskV2 stack is inherited verbatim. The risk-relevant analysis for a feature-set change:

- **R-feature-1 — look-ahead containment.** The single largest risk of a multi-frequency feature is a look-ahead leak through the cross-frequency alignment. **Mitigation (design-level, IS-calibrated):** the daily bars are an *exact aggregation* of the 8h candles (the 8h candles open at 00/08/16 UTC — verified) so there is no interpolation; the `merge_asof` direction `day_close ≤ open_time` guarantees the daily bar is fully closed before the 8h decision candle opens; the QE adds an adversarial past-only unit test (Section 3.5(8)). Simulated historical effect: the EDA's held-out AUC was measured under exactly this causal join on the IS walk-forward and produced AUC ≤ 0.5275 — a leak would have inflated it far above 0.53. The EDA's own modest AUC is evidence the alignment is leak-free.
- **R-feature-2 — colsample dilution.** Adding 8 features (4 IC-redundant) could let Optuna overfit IS noise (the `feedback_v3_inert_features_at_higher_budget.md` mechanism). **Mitigation:** this is an EXPLORATION at `n_trials=35` (the controlled budget), single-axis; the Critic's Check 3 (informational at EXPLORATION) and the Section 8 falsifiers catch a wash; the redundancy is a known, pre-registered quantity (Section 4.4), not a surprise.
- **R-feature-3 — the 7-gate stack as the live risk floor.** The 7 inherited gates (BTC trend kill, vol scaling, ADX, Hurst regime, feature z-score OOD, low-vol filter, hit-rate-disabled) continue to bound position-taking. The feature z-score OOD gate operates on the feature vector — **note for the QE:** the OOD gate's feature subset is /059-fixed and does NOT include the 8 new daily features (the OOD gate is not re-specified this iteration); the daily features enter the model but not the OOD gate, which is the conservative choice (no new OOD surface).

No new IS-calibrated threshold is introduced because no new gate is introduced. The feature-set axis is risk-neutral by construction.

---

## Section 6 — Risk Management Design

The 7-primitive RiskV2 stack, inherited /059-identical:

| # | Primitive | /059 setting | iter-v3/113 | Fire-rate expectation |
|---|---|---|---|---|
| 1 | BTC trend kill | threshold_pct=15.0, 14d lookback | unchanged | as /059 |
| 2 | Vol scaling | ATR-percentile position scaling | unchanged | as /059 |
| 3 | ADX gate | adx_threshold=20.0 | unchanged | as /059 |
| 4 | Hurst regime | regime gate disabled (iter-v3/022) | unchanged (disabled) | n/a |
| 5 | Feature z-score OOD | zscore_threshold=2.0, /059-fixed feature subset | unchanged (subset does NOT include the 8 new daily features) | as /059 |
| 6 | Low-vol filter | active | unchanged | as /059 |
| 7 | Hit-rate gate | disabled | unchanged (disabled) | n/a |
| — | Per-symbol drawdown brake | disabled (iter-v3/054) | unchanged (disabled) | n/a |
| — | Per-symbol PnL cap | disabled (iter-v3/020) | unchanged (disabled) | n/a |

**Regime coverage:** the daily features are themselves partly regime indicators (`d_realvol_ratio`, `d_atr_pctrank_60`, `d_efficiency_10` encode daily vol-regime and trend-regime state) — they may *improve* the model's implicit regime awareness without any change to the explicit gate stack. No gate fire-rate is expected to change materially, because the gates' inputs are /059-fixed; only the model's signal changes. The trade-count shift predicted in Section 4.3 is driven by the model re-ranking confidence, not by gate fire-rate changes.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**The single most plausible OOS failure mode (Mode 1): the daily signal washes out in the combined stack.** The EDA already exposed this — T5 shows the daily family carries decisive *standalone* signal, but T4 shows the *combined* 8h+daily stack does NOT clear its permutation null (p=0.39). The most plausible OOS outcome is that the small daily edge, concatenated into a 22-feature model whose 14-feature 8h component is near-noise (8h-only AUC ≈ 0.49, the /109 null), gets diluted: production Optuna at `n_trials=35` allocates `colsample_bytree` across 22 columns, the daily features are sampled but their thin 2.75-AUC-point edge does not survive into a robust trade-selection rule, and the OOS book lands flat — OOS monthly Sharpe Δ vs /060 in the [−0.20, +0.20] noise band, the iteration filed INERT-AT-EXPLORATION. In metrics this looks like: OOS monthly Sharpe near /060's +0.14, the gated-tail hit-rate lift visible in IS (T8 was uniformly positive) but too small to move the OOS Sharpe, the IS trade roster shifting (the daily features ARE consulted — Mode 3 does not fire) but the net effect washing. This is the modal outcome and the Section 4.1 interval is centered to reflect it (point estimate only +0.30, lower bound −0.25).

**Mode 2 — the per-symbol AUC heterogeneity inverts BCH.** T1 shows BCH's plain held-out AUC lift is marginally negative (−0.0052) while LDO/TRX are positive. If the daily features genuinely hurt BCH's signal — and BCH carries 95.76% of /059's IS PnL — the headline IS Sharpe could collapse even though the pooled AUC and the gated-tail proxy were positive. The mitigant: T8's BCH gated-tail lift is +0.0285 (the largest of the three), so the EDA's most production-relevant BCH signal is *positive*. Mode 2 fires if the result shows BCH IS PnL share materially below 90% AND IS monthly Sharpe below the +0.35 interval floor.

**Mode 3 — behavioral inertia.** The daily features are added but the production gates never consult them — the IS trade roster changes by < 8% vs /060. This would mean the 22-feature model's confidence ranking near the gate threshold is materially identical to the 14-feature model's. Section 4.3 pre-registers this falsifier; if it fires the iteration is INERT regardless of Sharpe. Considered low-probability — T8's gated-tail composition demonstrably changed in the EDA — but pre-registered per `feedback_v3_axis_saturation_predictor.md`.

The gates that should catch a failure: the Section 8 pre-registered IS/OOS Δ thresholds, the trade-roster-change falsifier, and the Critic's Check 8 (Hypothesis-Implementation Alignment — verifying the 22-feature stack genuinely ran and the daily features are bit-identical to the EDA's). Phase 8 will verify each mode against the actual outcome.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria

This is a **TYPE=EXPLORATION** iteration. Per the v3 skill, an EXPLORATION never updates `BASELINE_V3.md` regardless of outcome — the Critic emits `EXPLORATION-PROMISING` or `EXPLORATION-NEGATIVE`. The criteria below are LOCKED before the backtest and classify the iteration. Anchor: the **/060 EXPLORATION-mode reference (IS +0.8325 / OOS +0.1403)**, per `feedback_v3_cycle1_axis_pass_criteria.md`.

**PROMISING-AT-EXPLORATION (the axis carries forward as a candidate for the iter-v3/120 cycle-6 CONFIRMATION) — ALL of:**
- **C1.** IS monthly Sharpe Δ ≥ **+0.10** vs /060 (i.e. IS monthly Sharpe ≥ **+0.9325**).
- **C2.** OOS monthly Sharpe Δ ≥ **+0.20** vs /060 (i.e. OOS monthly Sharpe ≥ **+0.3403**).
- **C3.** `frac_positive_paths` (CPCV) ≥ **0.50** (the relaxed EXPLORATION threshold).
- **C4.** No methodology FAIL — Critic Checks 1, 2, 4, 5, 6, 8 all PASS (Check 3 informational at EXPLORATION budget per `feedback_v3_dsr_mode_artifact.md`); the T7 IC redundancy is scored under the Section 4.4 carve-out.
- **C5.** Aggregate OOS trades ≥ **75** (the EXPLORATION-level read of the bundle-level trade-rate floor — full ≥130 enforcement is the iter-v3/120 CONFIRMATION's bar per `feedback_v3_trade_rate_floor_bundle_level.md`).

**INERT-AT-EXPLORATION** — IS Δ ∈ [−0.10, +0.10] vs /060 OR OOS Δ ∈ [−0.20, +0.20] vs /060 (the 3-seed noise band) — **OR** the IS trade roster changes by < 8% vs /060 (Section 4.3 behavioral falsifier).

**NEGATIVE-AT-EXPLORATION** — IS monthly Sharpe Δ < **−0.10** vs /060 OR OOS monthly Sharpe Δ < **−0.20** vs /060.

**SUSPICIOUS** — IS/OOS daily-Sharpe ratio outside [0.5, 2.0] (per the /060 Critic adjudication and `feedback_v3_oos_is_ratio_gate.md`); adjudicated by the Critic.

**Honest pre-registration note:** given the EDA's SHARPENED-GO (the combined stack does not clear its permutation null, Section 2.4), the **modal pre-registered outcome is INERT-AT-EXPLORATION** (Section 7 Mode 1) — the daily signal is real but small and most plausibly washes in the combined production stack. PROMISING is the upside case (the standalone signal + the all-3-symbol gated-tail lift convert through the pipeline). Pre-registering the modal outcome as INERT, not PROMISING, eliminates post-hoc rationalization — if the iteration lands INERT that is the EDA's caveat confirmed, and if it lands PROMISING the daily representation has genuinely beaten the 8h saturation.

---

## Section 9 — Library Stack Declaration

No new library is introduced. The iteration uses the v3-pinned stack already in `pyproject.toml` / `uv.lock`:

- `lightgbm 4.6.0` — the model.
- `optuna 4.8.0` — hyperparameter search (`n_trials=35`).
- `numpy 2.2.6`, `pandas 3.0.0` — the daily-aggregation + `merge_asof` + rolling-window feature math (all stdlib-pandas operations; no new dependency).
- `scikit-learn 1.8.0` — `roc_auc_score` in the EDA only (not in the runner).
- `statsmodels 0.14.6` — ADF testing in the runner (`reports-v3/.../adf_test.csv`).
- `scipy 1.17.0`, `pyarrow 23.0.1` — inherited.
- CPCV / PBO / PSR — `validation_v3.py` (in-repo, no external lib for these; `pypbo`/`mlfinlab` are declared infrastructure but the v3 implementations are in-repo).

The EDA (`analysis/iteration_v3-113/`) uses `lightgbm`, `numpy`, `pandas`, `scikit-learn` only — all already installed. No fallback was needed.

---

## Section 10 — QR Audit Trail

The cycle-6 axis for this slot was recommended by the iter-v3/112 diary Section 9 ("Next Iteration Ideas") and the orchestrator's dispatch: **menu item 3 — multi-frequency feature engineering**. This is a QR-led, EDA-backed axis selection per `feedback_v3_axis_selection_quant_discipline.md` — the QR designed the specific experiment (coarser 1d daily features, derived look-ahead-free by aggregating the existing 8h candles, 8 candidate features across trend/vol/efficiency mechanisms) and produced the committed IS-only EDA (`analysis/iteration_v3-113/`, EDA SHA `ebd84e2`) BEFORE this brief. The orchestrator's suggestion ("multi-frequency feature engineering") was the menu category; the QR's EDA chose the concrete design (coarser-not-finer, the specific 8-feature family, the causal as-of-join) and supplies all of Section 2's numerical tables. No orchestrator pick was superseded — the QR's design is the original design. The EDA returned a SHARPENED-GO; per THE PRIME DIRECTIVE the iteration proceeds to a brief + Phase-6 backtest (the EDA designs the experiment, it does not terminate the iteration).

---

### Commit chain (filled by the orchestrator)

- EDA: `analysis/iteration_v3-113/` — EDA SHA `ebd84e2` (`analysis(iter-v3/113): multi-frequency feature gating EDA`). 3 scripts (`_shared.py`, `multifreq_gating_eda.py`, `orthogonal_subset_annex.py`) + 12 result tables T1–T12.
- Brief: `briefs-v3/iteration_v3-113/research_brief.md` — this file (`docs(iter-v3/113): research brief`).
- Setup commit / Phase 5.5 gate / code SHA / engineering report / Critic review / diary: filled by the QE / Critic / QR in later phases.
