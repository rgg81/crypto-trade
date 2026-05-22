# Iteration v3-076 — Research Brief

CYCLE 2 EXPLORATION #6 of 10 — NEW sign-invariant trend-efficiency feature
`range_efficiency_50` (a feature-internal IS-regime discriminator the model
learns).

---

## Section 0 — Data Split Declaration

- OOS_CUTOFF_DATE: **2025-03-24** (unchanged — IMMUTABLE; `src/crypto_trade/config.py`)
- training_months: **24** (unchanged — IMMUTABLE)
- IS window: **[2022-02-XX, 2025-03-24)** — earliest /060 IS month is 2022-02;
  the IS window spans the 2022 bear, 2023 chop, the 2024 bull, and the
  2024-Q4/2025-Q1 deceleration. The IS bear/chop sub-period is 2022-09 → 2023-12.
- OOS window: **[2025-03-24, 2026-05-XX)** — latest /060 OOS month is 2026-05; a
  persistent BCH/LDO/TRX uptrend.
- ENSEMBLE_SIZE: **3** (EXPLORATION mode — `--exploration` →
  `EXPLORATION_ENSEMBLE_SIZE`).
- ENSEMBLE_SEEDS: outer=42 lineage subset `[191664963, 1662057957, 1405681631]`.
- start_time: UNCHANGED — the backtest runs from the earliest available data. No
  date trimming (`feedback_no_cheating.md`).

---

## Section 0.5 — Iteration Type Declaration

**TYPE = EXPLORATION** (cycle 2 #6 of 10).

- Axis: **a NEW universal feature — `range_efficiency_50`** — added to
  `V3_FEATURE_COLUMNS` as the 15th feature. A NEW engineered feature (the
  structural-axis category per `feedback_v3_structural_over_knob_exploration.md`
  — a NEW feature family is the top-priority structural axis, NOT a gate knob).
  QR-chosen per `feedback_v3_axis_selection_quant_discipline.md` with committed
  EDA backing (`analysis/iteration_v3-076/axis_selection_eda.py`, SHA `40b6e66`).
- Run mode: `--exploration` (3-seed, outer=42 lineage), `--n-trials 35`,
  3-symbol universe (BCH/LDO/TRX), REQUIRED_GAP=66, embargo 22. Total 315 Optuna
  trials.
- Wall-clock budget: **≤ 1.0h** (estimate 0.6–0.9h; /071/072/073/074/075 all ran
  0.65–0.70h; this axis adds one feature column to a 14→15 feature stack — a
  feature-add is comparable in cost to /063's per-feature expansion runs, well
  under the 2h EXPLORATION cap).
- This is **NOT** a PASSIVE-DIAGNOSTIC. There is one substantive code change
  (the new feature) and a backtest is run.

Cadence note: this is an EXPLORATION; it consumes cycle-2 slot #6 of 10. The
cycle-2 CONFIRMATION is iter-v3/081 or later (`feedback_v3_strict_10_to_1_cadence.md`
— do NOT collapse the 10th EXPLORATION into the CONFIRMATION). Cycle 2 so far:
/071 SUSPICIOUS-OOS-DOMINANT, /072 NEGATIVE, /073 SUSPICIOUS-OOS-DOMINANT, /074
INERT-AT-EXPLORATION, /075 INERT-AT-EXPLORATION — **0/5 clean PROMISING.**

---

## Section 1 — Hypothesis

Adding `range_efficiency_50` — a SIGN-INVARIANT trend-efficiency feature
(Kaufman-style unsigned path efficiency at 50 bars: `|close[t] - close[t-50]| /
sum(|close diffs|, 50)`) — to `V3_FEATURE_COLUMNS` lifts IS monthly Sharpe by
giving the LightGBM model a feature-internal discriminator of the IS bear/chop
drag: the feature is informative WITHIN IS bear/chop (it separates winning from
losing IS-bear/chop trades, EDA T2 AUC 0.657) yet its value distribution does
NOT flip between the IS bear/chop window and the OOS uptrend window (EDA T3
regime-sign |corr| 0.010), so the model can down-weight the choppy-grind drag
WITHOUT the IS-up/OOS-down 1:1 trade-off that /075 demonstrated is structural to
any discriminator whose sign IS the IS/OOS regime axis.

---

## Section 2 — IS-Only Numerical Evidence

- Script: `analysis/iteration_v3-076/axis_selection_eda.py` (committed, SHA `40b6e66`)
- Outputs: `analysis/iteration_v3-076/` — `T0_anchor_values.csv`,
  `T1_regime_stratification.csv`, `T2_candidate_discrimination.csv`,
  `T3_regime_sign_correlation.csv`, `T4_holding_time_predictor.csv`,
  `T5_behavioral_predictor.csv`, `T6_per_symbol_is_discipline.csv`,
  `T7_ic_matrix.csv`, `axis_selection_summary.csv`, `synthesis.md`

The EDA runs NO backtest — every table is descriptive arithmetic on the
committed /060 trade roster and the v3 feature parquets. IS tables use IS-window
data only (open_time < OOS_CUTOFF_MS). The feature is computed past-only (a
50-bar rolling window then a strict `.shift(1)` — see Section 3.1).

### 2.1 T1 — IS/OOS regime-stratified diagnostic (the drag to lift)

The /060 anchor's monthly PnL split into three regime sub-periods (re-derives the
/074 PART 1 + /075 T1 finding):

| Regime | Months | Monthly Sharpe | Mean monthly PnL% | % positive months | Trades | Win rate |
|---|---:|---:|---:|---:|---:|---:|
| IS bear/chop (2022-09→2023-12) | 19 | **-0.2193** | -0.3618 | 26.3% | 77 | 26.0% |
| IS bull (2024-01→2025-03) | 15 | **+1.8504** | +3.9176 | 53.3% | 82 | 36.6% |
| OOS uptrend (2025-03→2026-05) | 14 | **+0.1403** | +0.3928 | 50.0% | 102 | 39.2% |

**Finding.** The IS bear/chop sub-period is the structural drag — monthly Sharpe
−0.2193, only 26.3% of months positive, **26.0% win rate**, total wpnl −6.87.
The IS bull sub-period carries the entire IS edge (+1.85). This is the drag the
Critic /075 Rec #3 mandate requires /076 to lift — but WITHOUT the IS-up/OOS-down
trade-off /075 hit.

### 2.2 T2 — Candidate-feature within-IS-bear/chop discrimination (the feature choice)

The EDA evaluated FOUR sign-invariant candidate features (all computable from
existing parquet primitives — zero parquet-regen at the EDA stage). The
discrimination metric is the rank-based AUC of the feature value (read at each
trade's signal bar) separating winning from losing IS-bear/chop trades —
**IS-only**:

| Candidate | IS-bear/chop AUC | IS-bull AUC | LONG AUC | SHORT AUC | \|corr w/ direction\| |
|---|---:|---:|---:|---:|---:|
| C1 range_compression_ratio (bb_width_pct_rank_100) | 0.5224 | 0.5128 | 0.5809 | 0.5073 | 0.1482 |
| **C2 range_efficiency_50** (unsigned Kaufman path eff.) | **0.6570** | 0.5487 | 0.5809 | **0.6854** | 0.1147 |
| C3 abs_ret_autocorr_50 (\|ret_autocorr_lag1_50\|) | 0.5588 | 0.5686 | 0.6324 | 0.5208 | 0.0679 |
| C4 realized_vol_pct_rank (atr_pct_rank_200) | 0.5162 | 0.5176 | 0.6140 | 0.5260 | 0.0884 |

**Finding.** `range_efficiency_50` (C2) has by far the strongest within-IS-
bear/chop discrimination — AUC **0.657**, vs C3 0.559, C1 0.522, C4 0.516. Three
properties make it the clean pick:

1. **It discriminates the SHORT-trade drag.** 52 of the 77 IS-bear/chop trades
   are SHORT, and only 12 of those 52 won (23% WR) — SHORT trades ARE the
   bear/chop drag. `range_efficiency_50`'s SHORT-trade AUC is **0.685** (its
   strongest sub-population). The feature carries exactly the signal that
   separates the bleeding sub-population.
2. **It is NOT directional-in-disguise.** Within IS bear/chop, |corr(feature,
   trade direction)| = **0.115** — near-zero. The feature discriminates on BOTH
   LONG (AUC 0.581) and SHORT (0.685) trades. Its discrimination is a
   trade-QUALITY signal (clean move vs choppy grind), not a hidden direction
   signal.
3. **It is informative in the IS-bull sub-period too** (AUC 0.549) — so it is
   not a bear-only artifact; the model can use it across regimes.

### 2.3 T3 — REGIME-SIGN-CORRELATION test (the Critic /075 Rec #3 mandate)

**This is the DECISIVE table — the pre-registered IS-only analysis the Critic
/075 Rec #3 binding mandate requires.** /075's finding (its diary Section 3): a
discriminator whose SIGN flips between the IS bear/chop window and the OOS
uptrend window is OOS-costly *by construction* — de-rating "the IS regime" also
de-rates "the OOS regime", because v3's IS window is bear-tagged and the OOS
window is bull-tagged on the SAME axis. /075's BTC-trend classifier (close <
SMA) is exactly such a discriminator: its value is +1 bull / −1 bear, and that
sign IS the IS/OOS regime axis.

T3 tests, per candidate feature, whether the feature is a monotone proxy for the
IS-vs-OOS regime axis. The regime indicator is the **IS/OOS CALENDAR LABEL** (1
for trades in the IS bear/chop window, 0 for trades in the OOS window) — a
calendar fact fixed by OOS_CUTOFF_DATE, **NOT an OOS performance metric**. No OOS
PnL / OOS Sharpe / OOS counterfactual is used (Section 10.1 — no-OOS-tuning
disclosure).

| Candidate | feat mean IS-bear/chop | feat mean OOS-uptrend | std mean gap | **\|regime-sign corr\|** | below 0.35 ceiling |
|---|---:|---:|---:|---:|:---:|
| C1 range_compression_ratio | 0.6316 | 0.6569 | -0.0897 | 0.0444 | YES |
| **C2 range_efficiency_50** | 0.1686 | 0.1708 | **-0.0202** | **0.0100** | **YES** |
| C3 abs_ret_autocorr_50 | 0.0991 | 0.1118 | -0.1501 | 0.0743 | YES |
| C4 realized_vol_pct_rank | 0.7304 | 0.7005 | 0.1463 | 0.0724 | YES |

**Finding — the chosen feature BREAKS the /075 tension.** `range_efficiency_50`
has |regime-sign corr| = **0.010** — almost exactly zero, and far below the
a-priori 0.35 ceiling (the data-free threshold above which a feature is too
close to a directional-regime proxy to escape the /075 trap). Its mean value is
**0.1686 in IS bear/chop and 0.1708 in OOS uptrend** — a standardized mean gap
of −0.0202, i.e. the feature's value distribution is statistically the SAME
across the two windows.

The mechanism, stated explicitly: a feature that measures HOW price is moving
(efficient directional move vs choppy grind) — NOT WHICH WAY — is not a
directional-regime proxy, because a choppy low-efficiency grind exists in BOTH a
bear market and a bull market, and a clean efficient move exists in BOTH. So a
model that learns "this is a dangerous choppy moment, trade smaller / skip" from
IS bear/chop bars does NOT thereby learn "suppress OOS-uptrend trades" — because
the OOS uptrend is not uniformly tagged by the feature; the OOS uptrend has its
own mix of efficient and choppy bars. **This is the structural difference from
the /075 macro classifier**: /075's classifier de-rated the IS and OOS regimes
together because its discriminating signal WAS the regime sign; `range_efficiency_50`'s
discriminating signal is regime-orthogonal (|corr| 0.010), so the model's IS
bear/chop learning does not transfer as an OOS-uptrend suppression.

This is the Critic /075 Rec #3 mandate — a committed IS-only (plus calendar-
label) analysis pre-registering that the chosen mechanism discriminates IS
bear/chop from OOS uptrend WITHOUT a feature whose sign is regime-correlated that
way — satisfied.

### 2.4 T6 — Per-symbol IS-axis discipline

`range_efficiency_50` is a UNIVERSAL feature (added to `V3_FEATURE_COLUMNS` — all
3 symbols' models receive it). Per-symbol within-IS-bear/chop discrimination AUC:

| Symbol | n IS bear/chop trades | discrimination AUC | carries signal |
|---|---:|---:|:---:|
| BCHUSDT | 44 | **0.6973** | YES |
| LDOUSDT | 0 | n/a | n/a (no IS bear/chop trades) |
| TRXUSDT | 33 | **0.5549** | YES |

**Finding.** Both symbols that HAVE IS bear/chop trades on the /060 roster — BCH
(AUC 0.697) and TRX (AUC 0.555) — carry signal (AUC ≥ 0.55). LDO has 0 IS
bear/chop trades on the /060 roster (LDO is a later-listed symbol; all 11 LDO IS
trades are in the bull sub-period) so its per-symbol bear/chop AUC is undefined —
recorded n/a, NOT a FAIL; LDO's model still receives the universal feature. Per
`feedback_v3_per_symbol_lifts_oos_breaks_is.md`, a UNIVERSAL feature is the
PREFERRED axis type precisely because all symbols see the same logic — it
preserves the IS aggregate by construction (Section 4.2 expands the per-symbol
IS-axis discipline).

### 2.5 T7 — IC matrix vs the 14 BASELINE_V3 features (INFORMATIONAL)

Pooled-across-symbols IS-window Pearson IC of `range_efficiency_50` vs each of
the 14 BASELINE_V3 features. Per `feedback_v3_engineered_feature_pivot.md`, for
a derived/composed feature the standard |IC| < 0.70 hard gate is INFORMATIONAL;
the binding gate is feature importance ≥ 30 in the LightGBM output for ≥1 symbol.
The top IC rows:

| Baseline feature | pooled IC | \|IC\| |
|---|---:|---:|
| sym_vs_btc_ret_7d | +0.2061 | 0.2061 |
| ema_spread_atr_20 | +0.1347 | 0.1544 |
| range_realized_vol_50 | +0.1538 | 0.1538 |
| regime_momentum_signed_5d | +0.1426 | 0.1426 |
| vwap_dev_20 | +0.1419 | 0.1419 |

**Finding.** Max |IC| = **0.206** — comfortably below the 0.70 threshold, and
materially lower than v3's prior engineered features (regime_momentum_signed_5d
hit 0.887 with vwap_dev_20). `range_efficiency_50` is genuinely orthogonal to the
existing 14-feature stack — it carries information the model cannot reconstruct
from the current features, and it does not steal `colsample_bytree` picks from a
near-duplicate.

### 2.6 Holding-time-effect predictor (T4) — MANDATED by `feedback_v3_is_oos_regime_divergence.md`

| Split | baseline roster n | baseline mean dur (candles) | baseline median dur | predicted mean-dur Δ | falsifier mean-dur Δ |
|---|---:|---:|---:|---:|---:|
| IS | 159 | 6.3145 | 4.0 | ~0 | +1.0 |
| OOS | 102 | 6.4608 | 4.5 | ~0 | +1.0 |

**A FEATURE has NO duration-extension mechanism.** Unlike the /065/071/073
holding-time-extension axes (a wider SL lets trades ride longer; a meta-label M2
veto removes early stop-outs; a per-symbol barrier rebalance shifts the
TP/SL arms), a new feature cannot widen a barrier or veto an early stop-out. The
trade roster changes ONLY through the LightGBM model re-learning its split
structure with the extra column. The predicted kept-roster mean/median duration
delta is **~0** — NOT mechanically forced to exactly 0 (the model re-learning
can shift WHICH trades are taken, so a small incidental duration drift is
possible), but the feature has NO holding-time-extension mechanism. Per
`feedback_v3_is_oos_regime_divergence.md`, an axis with a ~0 predicted duration
change does NOT load the IS/OOS regime factor. **Falsifier: if the /076 backtest
shows the kept-roster mean trade duration shifts by > +1.0 candle vs the /060
roster, the feature is behaving like a holding-time-extension axis and the
Critic must flag it.**

### 2.7 Anchor declaration

The cycle-2 EXPLORATION anchor is **iter-v3/060 EXPLORATION-MODE-REFERENCE**
(`feedback_v3_cycle1_axis_pass_criteria.md`), byte-exact from
`reports-v3/iteration_v3-060/comparison.csv`:

| Anchor metric | Value | Source |
|---|---:|---|
| IS monthly Sharpe | **+0.8325** | comparison.csv:2 in_sample |
| OOS monthly Sharpe | **+0.1403** | comparison.csv:2 out_of_sample |
| IS daily Sharpe | +1.7115 | comparison.csv:3 in_sample |
| OOS daily Sharpe | +0.3659 | comparison.csv:3 out_of_sample |
| IS n_trades | 159 | comparison.csv:7 in_sample |
| OOS n_trades | 102 | comparison.csv:7 out_of_sample |
| frac_positive_paths (CPCV) | 0.6444 | dsr.json / cpcv_paths.csv (CPCV invariant) |

With /075's Primitive 12 REVERTED (Section 3), /076 starts from the /060 baseline
state plus the single new feature.

---

## Section 3 — Proposed Changes

**ONE substantive axis change** (the new feature `range_efficiency_50`) plus ONE
mandatory revert (the /075 leftover — Primitive 12). Per `feedback_no_cheating.md`
anti-drift discipline, /075's Primitive 12 axis — INERT-AT-EXPLORATION, did NOT
advance — must not silently carry into /076. The revert restores the /060
baseline state; it is a revert, not a second axis.

- **Symbols:** UNCHANGED — BCH/LDO/TRX. V3_EXCLUDED_SYMBOLS check: none of
  BCH/LDO/TRX is in V3_EXCLUDED_SYMBOLS. PASS.
- **Labeling:** UNCHANGED — `DEFAULT_ATR_MULTIPLIERS = (2.0, 1.0)`,
  `V3_ATR_MULTIPLIERS_PER_SYMBOL = {}`, `label_mode="triple_barrier"`, 21-candle
  (10080-min) timeout. No labeling change.
- **Features — NEW:** add `range_efficiency_50` to `V3_FEATURE_COLUMNS_TOP_N` as
  the 15th universal feature. Detailed in 3.1.
- **Risk gates — REVERT /075:** `enable_regime_size_scalar=True` → **`False`**;
  `regime_size_scalar_symbols=("LDOUSDT","TRXUSDT")` → **`()`**. This restores the
  /060 baseline risk-gate stack (Primitive 12 OFF). `regime_size_scalar_value`
  and `regime_size_ma_window` may stay as inert defaults — they have no effect
  when `enable_regime_size_scalar=False`.
- **Model / risk primitives:** UNCHANGED — the LightGBM model, the 5-gate +
  BTC-trend risk stack, and all other primitives (8 OFF, 9 OFF, 10 OFF, 11 OFF)
  are exactly the /060 baseline.

### 3.1 The NEW feature `range_efficiency_50` — exact code changes

`range_efficiency_50` is a Category-2 derived feature in the v3-specific
`crypto_trade.features_v3` package — v1 and v2 are NOT perturbed (track
isolation; no import from `crypto_trade.features` or `features_v2`).

1. **`src/crypto_trade/features_v3/engineered_v3.py`** — add a NEW function
   `compute_range_efficiency_50(df) -> pd.DataFrame`:
   - Construction: `path = |close[t] - close[t-50]|`;
     `noise = sum(|close.diff()|, 50)`;
     `er = (path / (noise + 1e-9)).clip(0.0, 1.0)`; then `er.shift(1)` so bar t's
     value uses `close[t-51 .. t-1]` only; then `.fillna(0.0)` on the first 51
     warm-up bars (neutral 0.0 = maximally choppy / no efficiency).
   - Output range [0, 1]. Past-only by construction (the `.shift(1)` after the
     50-bar rolling window guarantees bar t never observes `close[t]`).
   - **The function docstring MUST disclose** that this is the same Kaufman
     path-efficiency math as the dead-code `compute_efficiency_ratio_50`, that
     `efficiency_ratio_50` was DISASTROUS-NEGATIVE at iter-v3/043, and that
     `range_efficiency_50` is its re-evaluation under
     `feedback_v3_walkforward_lookahead_bug.md` with a different ROLE (a
     regime-quality conditioning feature alongside 14 directional features, NOT a
     standalone directional signal) — see Section 10.2.
2. **`src/crypto_trade/features_v3/engineered_v3.py`** — dispatch the new
   function in `add_engineered_v3_features(df)` (append `df =
   compute_range_efficiency_50(df)`), and add `"compute_range_efficiency_50"` to
   `__all__`.
3. **`src/crypto_trade/features_v3/__init__.py`** — add `"range_efficiency_50"`
   to `V3_FEATURE_COLUMNS_TOP_N` (15th entry). `V3_FEATURE_COLUMNS` is the alias
   of `V3_FEATURE_COLUMNS_TOP_N`, so it automatically becomes 15 features. Update
   the `V3_FEATURE_COLUMNS_TOP_N` docstring to record the /076 addition.
4. **`run_baseline_v3.py`** — in `_build_v3_model`'s `RiskV2Config(...)`:
   - REVERT /075: `enable_regime_size_scalar=True → False`;
     `regime_size_scalar_symbols=("LDOUSDT","TRXUSDT") → ()`.
     (`regime_size_scalar_value=0.50`, `regime_size_ma_window=270` may stay as
     inert defaults — no effect when `enable_regime_size_scalar=False`.)
5. **`run_baseline_v3.py`** — `_verify_feature_columns` pre-flight:
   - Change the feature-count assertion from `!= 14` to `!= 15`; update the
     message and the summary `print` to reflect the 15-feature set (14
     BASELINE_V3 + `range_efficiency_50`).
   - Change the per-symbol `features_for_symbol(sym)` count check from `!= 14` to
     `!= 15`.
   - ADD an assertion that `range_efficiency_50 IS in V3_FEATURE_COLUMNS` (the
     /076 axis is present).
   - REMOVE the four /075 Primitive-12 assertions
     (`enable_regime_size_scalar is True`, `regime_size_scalar_symbols ==
     ("LDOUSDT","TRXUSDT")`, `regime_size_scalar_value == 0.50`,
     `regime_size_ma_window == 270`) and REPLACE with a single
     `enable_regime_size_scalar is False` assertion (the /076 baseline-restore
     state) plus `regime_size_scalar_symbols == ()`.
   - The `efficiency_ratio_50 NOT in V3_FEATURE_COLUMNS` assertion STAYS (the
     literal banned name is still banned; `range_efficiency_50` is a distinct
     name). NOTE the assertion message already says the SIGNED variant
     `trend_efficiency_signed` is allowed — extend the comment to note
     `range_efficiency_50` is a separately-named re-evaluation.
6. **`run_baseline_v3.py`** — `ITERATION_LABEL` bumped `"v3-075"` → `"v3-076"`.
7. **`tests/`** —
   - UPDATE `tests/strategies/ml/test_v3_feature_count.py`: the count assertion
     14 → 15; add `range_efficiency_50` to the expected-present set;
     `efficiency_ratio_50` STAYS in the prohibited set (the literal banned name);
     `range_efficiency_50` must NOT be in the prohibited set.
   - ADD `tests/features_v3/test_range_efficiency_50.py` (a NEW test file):
     assert (a) `compute_range_efficiency_50` appends a `range_efficiency_50`
     column in [0, 1]; (b) the feature is past-only (appending future bars does
     not change the value at t — the `.shift(1)` contract); (c) warm-up bars are
     0.0; (d) `add_engineered_v3_features` dispatches it; (e) a clean efficient
     up-trend ramp yields a high value and a sawtooth chop yields a low value
     (the discrimination mechanism).
   - The existing `tests/strategies/ml/test_regime_size_scalar.py` is UNCHANGED
     and stays GREEN — Primitive 12's `RiskV2Config` fields remain DEFINED (they
     just default OFF); the test exercises the primitive's mechanics, not the
     runner's enablement (the same pattern as `test_regime_gate.py` when /075
     reverted Primitive 9). The runner-enablement revert is verified by the
     `_verify_feature_columns` `enable_regime_size_scalar is False` assertion.
   - The existing `tests/features_v3/test_engineered_v3.py` is UNCHANGED — it
     tests the existing engineered features; `compute_range_efficiency_50` gets
     its own NEW test file (the same pattern /048's `test_vol_normalized_ret_5d.py`
     and /053's `test_hurst_drift_50_200_universal.py` followed).

ZERO change to labeling code, the model, the risk-gate cascade logic, or the
walk-forward harness. The axis is purely a NEW feature column the model trains on.

**Single-axis discipline.** The brief declares exactly TWO changes: (1) the NEW
feature `range_efficiency_50` (the single primary axis), (2) the mandatory
Primitive-12 revert (a baseline-restore, not a second varied axis).
`block_long_for=()` / `block_short_for=()` stay reverted (primitive 10 OFF, per
/051). `enable_per_symbol_drawdown_brake=False` (primitive 11 OFF, per /054).
`enable_per_symbol_cap=False` (primitive 8 OFF, per /020). `enable_regime_gate=False`
(primitive 9 OFF, /075 baseline). No scope creep. No same-family feature
stacking (`feedback_v3_engineered_features_dont_stack.md` — ONE new feature,
tested ALONE).

---

## Section 4 — Expected OOS Impact

### 4.1 Predicted bands (cycle-2 axis-PASS criteria, anchored on /060)

A NEW feature is harder to predict precisely than a post-gate scalar — the
trade-roster change is mediated by the model re-learning, not a deterministic
re-weighting. The bands below are mechanism-derived and deliberately wide.

- **Predicted IS monthly Sharpe Δ vs /060: +0.10 to +0.30** (CI **[0.00, +0.45]**,
  centred **~+0.15**). The mechanism: the feature carries within-IS-bear/chop
  discriminating signal (T2 AUC 0.657, SHORT-trade AUC 0.685) — it gives the
  model a column to split on that separates the bleeding 23%-WR SHORT chop
  trades from the rest. If the model uses it (T7 max |IC| 0.206 confirms it is
  not redundant), IS bear/chop performance lifts and the IS aggregate rises. The
  band's lower bound touches 0.00 because a single-feature add at single-seed
  n_trials=35 can also be INERT (the model may not allocate enough splits to a
  15th feature — the v3 engineered-feature graveyard, Section 7, shows this is a
  real mode).
- **Predicted OOS monthly Sharpe Δ vs /060: ~0, mechanism-neutral, band
  [-0.15, +0.20].** This is the KEY prediction and the load-bearing difference
  from /075. The mechanism: T3 shows `range_efficiency_50`'s value distribution
  is statistically the SAME across IS bear/chop and OOS uptrend (|regime-sign
  corr| 0.010). A model that learns "down-weight choppy-grind moments" from the
  feature does NOT thereby suppress the OOS uptrend, because the feature does
  not tag the OOS uptrend as a whole — the OOS uptrend has its own efficient and
  choppy bars. So unlike /075 (where the IS lift mechanically forced an OOS
  cost), /076's OOS effect is NOT pinned to the sign of the IS effect: it is
  whatever the within-OOS-window discrimination of the feature is worth, plus
  EXPLORATION-mode 3-seed variance. The EDA does NOT compute a per-feature OOS
  counterfactual (no OOS-tuning, Section 10.1) — the band is mechanism-derived,
  centred on 0 because the feature is regime-orthogonal.
- **Predicted frac_positive_paths:** ≈ 0.6444 ± 0.05 (CPCV is largely
  architecture-invariant; a single new feature shifts the per-cell model but the
  CPCV path construction stays close).
- **Falsifier (IS):** if **IS monthly Sharpe Δ < -0.10** vs /060 (IS Sharpe <
  +0.7325), the feature actively HARMS the IS aggregate — the
  `feedback_v3_inert_features_at_higher_budget.md` failure mode (an unhelpful
  feature lets Optuna overfit IS noise). The axis is NEGATIVE on the IS axis.
- **Falsifier (OOS):** if **OOS monthly Sharpe Δ < -0.20** vs /060 (OOS Sharpe <
  -0.0597), the feature is NEGATIVE on the OOS axis — the mechanism prediction
  (regime-orthogonal, OOS-neutral) is wrong and the feature is degrading OOS.
- **Falsifier (importance):** if `range_efficiency_50`'s mean LightGBM importance
  is rank 15/15 (last) for ALL 3 symbols, the model is not learning the feature
  — INERT via the rank-14/14 INERT pattern of /015/019. The brief Section 8
  taxonomy classifies this INERT.

### 4.2 BCH IS sensitivity + per-symbol IS-axis discipline

`range_efficiency_50` is a UNIVERSAL feature — every symbol's model receives it.
Per `feedback_v3_cycle1_axis_pass_criteria.md` (BCH carries the v3 IS edge —
176.68% of /060 IS PnL) the brief must project BCH IS sensitivity:

- BCH's within-IS-bear/chop discrimination AUC for the feature is **0.697** (T6)
  — the strongest of the 3 symbols. The feature carries genuine signal for the
  IS-edge-carrier symbol, so adding it should HELP or be NEUTRAL for BCH IS, not
  hurt it.
- Per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`: per-symbol customizations
  lift OOS but break IS aggregate; UNIVERSAL changes are PREFERRED because all
  symbols see the same logic and the IS aggregate is preserved by construction.
  `range_efficiency_50` is universal — there is no per-symbol customization, no
  per-symbol search-space asymmetry. The IS-axis-discipline risk that rule
  describes does not apply to a universal feature add. The honest caveat: the
  feature's IS value is validated here at single-seed EXPLORATION; if /076 is
  PROMISING, the cycle-2 CONFIRMATION must re-validate the feature preserves IS
  Sharpe at 10-seed mode before bundling.

### 4.3 Holding-time-effect predictor (mandated by `feedback_v3_is_oos_regime_divergence.md`)

**Predicted mean/median trade-duration change: ~0** (NOT mechanically exact 0 —
the model re-learning can shift WHICH trades are taken — but the feature has NO
duration-extension mechanism: it cannot widen a barrier or veto an early
stop-out, unlike the SL/meta-label/barrier family). A new feature is
holding-time-ORTHOGONAL by mechanism. Per the regime-divergence rule, a ~0
duration change does NOT load the IS/OOS regime factor. **This is the
load-bearing reason `range_efficiency_50` cannot be a 4th holding-time-extension
axis** — unlike /065/071/073, it has no mechanism to lengthen the kept roster.

Falsifier (Section 4.1, T4): if the /076 backtest shows the kept-roster mean
trade duration shifts by **> +1.0 candle** vs the /060 roster, the feature is
behaving like a holding-time-extension axis and the Critic must flag it.

### 4.4 Behavioral-effect predictor (mandated by `feedback_v3_axis_saturation_predictor.md`)

A FEATURE is not a post-gate scalar — it cannot give an exact trade-level count
the way a SIZE de-rate can. The EDA T5 estimate is a STRUCTURAL PROXY for the
roster-change scale: the new feature most plausibly changes the model's decision
on the trades where the feature sits in its informative tail at the signal bar.
T5 measures the IS + OOS trades whose `range_efficiency_50` value is in the lower
OR upper tercile of the IS-bear/chop feature distribution (the regions where T2
shows the feature discriminates):

- **IS trades in the feature's informative tail:** **106 of 159** (66.7%).
- **OOS trades in the feature's informative tail:** **68 of 102** (66.7%).
- This is a PROXY for how much of the roster the feature could influence — it is
  NOT a prediction that 106 IS trades change. The exact roster delta vs /060 is
  measured by the Phase 6 backtest.

**Behavioral-effect prediction (the falsifiable claim):** the new feature changes
the IS trade roster vs /060 by **at least 5 and at most ~60 trades** (a feature
add at single-seed n_trials=35 typically perturbs a moderate fraction of the
roster — /063's single-feature adds shifted IS trade counts by ~10–40; the band
is wide because a 15th feature's roster effect is model-mediated). **Falsifier:
if the /076 IS trade roster is BIT-IDENTICAL to /060 (zero trades changed), the
feature was not learned at all — the model allocated it zero splits — and the
axis is NULL-RESULT (Section 8.5).** The /060 → /076 trade-roster diff and the
`range_efficiency_50` LightGBM importance rank are the discriminating signals the
Critic checks.

The trade-rate floor is not at structural risk: a feature add does not
mechanically delete trades — it re-shapes the model's decisions; IS/OOS trade
counts will be CLOSE to /060 (159 IS / 102 OOS), not collapsed.

### 4.5 OOS/IS ratio SUSPICIOUS pre-registration (mandated by `feedback_v3_oos_is_ratio_gate.md`)

**Pre-registered SUSPICIOUS gate: if the /076 OOS/IS monthly Sharpe ratio > 3.0,
the axis is classified SUSPICIOUS regardless of absolute OOS Sharpe magnitude.**
The canonical definition is the within-iteration `comparison.csv` `monthly_sharpe`
ratio column (the value the Section 8 SUSPICIOUS classifier consumes — no
alternative ratio construction is introduced, per the /074 Critic Rec #1
standardization). The gate fires unconditionally per the memory rule.

`range_efficiency_50` is predicted NOT to trip the ratio gate, by mechanism: (a)
the holding-time-effect predictor (Section 4.3) shows ~0 duration change, so the
IS/OOS regime-divergence factor — the usual driver of an inflated OOS/IS ratio —
is not loaded; (b) T3 shows the feature is regime-orthogonal (|regime-sign corr|
0.010), so it is structurally incapable of producing the IS-collapse + OOS-soar
signature of /071/073 (those axes' discriminating signal WAS the regime axis;
this feature's is not). The predicted IS Δ is positive (+0.10 to +0.30) and the
predicted OOS Δ is ~0 — so the OOS/IS ratio is predicted to move toward a healthy
[0.5, 2.0] band (or stay near /060's 0.17 if IS rises and OOS holds), NOT toward
3.0. But the gate is pre-registered and binding: if /076 returns OOS/IS > 3.0,
the axis is SUSPICIOUS and does NOT advance, even though the mechanism analysis
rules it out.

---

## Section 5 — Risk Mitigation

This iteration's axis is a NEW model FEATURE, not a risk primitive. The
mitigation discussion is about whether the feature is correctly bounded,
look-ahead-free, and cannot silently degrade the strategy.

- **Past-only discipline.** `range_efficiency_50` is computed with a 50-bar
  rolling window followed by a strict `.shift(1)`, so bar t's feature value uses
  only `close[t-51 .. t-1]` — the signal bar's own close is excluded. Appending
  future bars does not change the value at t. This is the EXACT past-only
  contract of the existing `compute_efficiency_ratio_50` (and `compute_trend_efficiency_signed`),
  both of which were verified past-only by the Critic at prior iterations. The
  NEW `tests/features_v3/test_range_efficiency_50.py` re-asserts the past-only
  property adversarially. The walk-forward embargo (22 candles) + REQUIRED_GAP
  (66) are unchanged — the feature does not change the label horizon or symbol
  count.
- **IS-only and a-priori parameters.** PARAMETER 1 (which candidate feature) is
  chosen by `_pick_feature(t2, t3)` on IS-only AUC + the calendar IS/OOS-label
  regime-sign correlation — no OOS performance metric (Section 10.1). PARAMETER 2
  (the 50-bar window) is a-priori — reusing the window of the dead-code
  `compute_efficiency_ratio_50` so the feature is computable with one parquet
  regen; no window SWEEP, no fit. Every parameter has an IS-only or a-priori
  derivation; none is OOS-tuned.
- **Simulated historical IS effect.** Section 2.2 (T2) is the simulated
  historical IS evidence: on the /060 IS bear/chop roster, `range_efficiency_50`
  separates winning from losing trades with AUC 0.657. Section 2.4 (T6) confirms
  the discrimination holds per-symbol for BCH and TRX. The IS effect on the
  headline Sharpe is mechanism-predicted (a lift — Section 4.1), NOT a counter-
  factual number — a feature's headline effect is model-mediated and can only be
  measured by the backtest, not pre-computed.
- **Bounded output.** The feature is bounded to [0, 1] by the `.clip(0.0, 1.0)`
  — it cannot produce an outlier that destabilizes the tree splits. Warm-up bars
  are 0.0 (neutral — maximally choppy). The blast radius of a misfire is one
  feature column the model may or may not split on; the feature cannot change
  trade direction, SL/TP, or position size directly (it is a model input, not a
  risk gate).
- **Orthogonality.** T7 max |IC| 0.206 — the feature is not a near-duplicate of
  an existing feature, so it does not waste `colsample_bytree` picks on redundant
  variance (the `feedback_v3` lesson that adding a feature correlated to existing
  ones is harmful).
- **Trade-rate preserved.** A feature add does not mechanically delete trades
  (Section 4.4) — the IS/OOS trade counts stay CLOSE to /060.
- **Failure-stop.** Section 4.1 falsifiers: IS Δ < −0.10 → NEGATIVE-IS; OOS Δ <
  −0.20 → NEGATIVE-OOS; importance rank 15/15 all 3 symbols → INERT. Section 4.3
  falsifier: kept-roster mean duration shift > +1.0 candle → holding-time
  violation flag. Section 4.4 falsifier: IS roster bit-identical to /060 →
  NULL-RESULT. Section 4.5 falsifier: OOS/IS > 3.0 → SUSPICIOUS.

---

## Section 6 — Risk Management Design

The v3 risk gate stack. /076 reverts Primitive 12 (BTC-trend-regime position-SIZE
de-rate scalar) to OFF and makes NO other risk-primitive change — the /076 axis
is a model feature, not a risk primitive. The stack is exactly the /060 baseline.

| # | Primitive | /076 state | Fire-rate prediction |
|---|---|---|---|
| 1 | Feature z-score OOD (z>2.0) | ON, unchanged | baseline |
| 2 | Hurst regime check | ON, unchanged | baseline |
| 3 | ADX gate (ADX>20) | ON, unchanged | baseline |
| 4 | Low-vol filter (bottom-third ATR) | ON, unchanged | baseline |
| 5 | Vol-adjusted sizing (TRX floor 0.5) | ON, unchanged | baseline |
| 8 | Per-symbol PnL cap | OFF (closed /020) | n/a |
| 9 | Regime-conditional kill switch | OFF (/075 baseline) | n/a |
| 10 | Direction-asymmetric kill switch | OFF (reverted /051) | n/a |
| 11 | Per-symbol drawdown brake | OFF (closed /054) | n/a |
| 12 | BTC-trend-regime position-SIZE de-rate scalar | **OFF (REVERTED from /075)** | n/a — /075 baseline-restore |

**Regime coverage analysis.** The /076 axis adds NO new risk primitive — it adds
a model FEATURE. The risk-management novelty is upstream of the gate stack: the
new feature gives the LightGBM model itself a within-regime discriminator, so the
model's PREDICTIONS in bear/chop months improve before any gate sees them. This
is the structurally-correct response to the /075 finding — rather than a
post-gate macro classifier (which de-rates IS and OOS together), the
discrimination is moved INTO the model via a regime-orthogonal feature, where the
model can condition on it WITHOUT a global directional sign. Primitive 12 stays
DEFINED in `RiskV2Config` (the fields are not deleted) but DISABLED — its
mechanics remain test-covered by `test_regime_size_scalar.py`; it is catalogued
in the EXPLORATION ledger as a single-data-point INERT result, available for
future re-examination but not a Dead Idea.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

**Most plausible outcome (probability ≈ 40%): INERT-AT-EXPLORATION.** The most
common fate of a single NEW feature added at single-seed n_trials=35 is that the
model allocates it too few splits to move the headline metrics — the rank-14/14
INERT pattern that /015 (microstructure) and /019 (funding rate) both hit, and
the `feedback_v3_inert_features_at_higher_budget.md` mode. The feature carries
genuine IS-only signal (T2 AUC 0.657), but at single-seed n_trials=35 the Optuna
TPE sampler and `colsample_bytree` may simply not surface it into a 15-feature
stack. The metric signature: IS Δ within [−0.10, +0.10], OOS Δ within
[−0.20, +0.20], `range_efficiency_50` importance rank in the bottom third for
most symbols. Per the Section 8 disjunctive classifier, that lands INERT.

**Second outcome (probability ≈ 30%): PROMISING-AT-EXPLORATION.** The feature is
used by the model (T7 confirms it is orthogonal — not a redundant pick), it lifts
IS bear/chop discrimination, IS Δ clears +0.10, AND — the load-bearing claim —
because the feature is regime-orthogonal (T3 |regime-sign corr| 0.010) the OOS
effect is NOT pinned negative the way /075's was; if the within-OOS-window
discrimination is positive, OOS Δ also clears +0.20 and the axis is the first
clean PROMISING of cycle 2. This is the outcome the EDA's mechanism analysis
points to, but it is weighted below INERT because surfacing a 15th feature at
single-seed n_trials=35 is genuinely uncertain (the engineered-feature graveyard
is the honest prior).

**Third outcome (probability ≈ 22%): NEGATIVE-AT-EXPLORATION.** Two sub-modes:
(a) NEGATIVE-IS — the feature is unhelpful and lets Optuna overfit IS noise, IS Δ
< −0.10 (the `feedback_v3_inert_features_at_higher_budget.md` mode in its
harmful form — though at n_trials=35, not the 35-vs-10 contrast that rule
describes); (b) NEGATIVE-OOS — the feature degrades OOS, OOS Δ < −0.20. Weighted
22% honestly: the v3 engineered-feature graveyard (vol_adj_autocorr /026
catastrophic, efficiency_ratio_50 /043 disastrous, hurst_drift_50_200 /053
PARKED, vol_normalized_ret_5d /049 PATH-C) shows a NEW feature can actively harm.
The mechanism mitigant: `range_efficiency_50` is genuinely orthogonal (T7 |IC|
0.206) and genuinely discriminating (T2 AUC 0.657) — properties most of the
graveyard features lacked — but a single-seed result is lottery-prone.

**Tail outcome (probability ≈ 5%): NULL-RESULT.** The /076 IS trade roster is
bit-identical to /060 — the model allocated `range_efficiency_50` zero splits and
the feature had literally no effect. Near-impossible given the feature is
orthogonal and discriminating, but recorded as the strict NULL-RESULT mode.

**SUSPICIOUS is weighted ≈ 3% (near-ruled-out).** The SUSPICIOUS-OOS-DOMINANT
sub-mode requires an IS-collapse + OOS-soar; the holding-time predictor (Section
4.3) shows ~0 duration change so the regime-divergence factor is not loaded, and
T3 shows the feature is regime-orthogonal — it is structurally unable to produce
the /071/073 signature. The OOS/IS ratio gate (> 3.0) is pre-registered and
binding regardless.

**What the gates should catch.** The discriminating signals: (a) the IS/OOS
Sharpe deltas vs /060; (b) `range_efficiency_50`'s LightGBM importance rank in
`model_importance_last_month_*.csv` — bottom-third for all 3 symbols → INERT;
(c) the /060 → /076 trade-roster diff — zero changes → NULL-RESULT; (d) the
kept-roster duration vs /060 — > +1.0 candle shift → holding-time flag;
(e) the OOS/IS monthly Sharpe ratio — > 3.0 → SUSPICIOUS.

Process predictions: P1 — wall-clock under the 1.0h budget (≈ 90% confidence;
/071-075 all 0.65-0.70h; a feature add costs one extra column in feature regen +
training, comparable). P2 — the new pre-flight assertions (count 14→15,
`range_efficiency_50` present, Primitive-12 revert) pass on the first Phase 5.5
gate run (≈ 70%; /073 hit 4 stale assertions and /074 hit a stale ATR assertion —
a stale-assertion BLOCK is a real ≈ 30% risk; the QE must update the count
assertions, the Primitive-12 assertions, and `test_v3_feature_count.py` in the
SAME setup commit). P3 — the parquet regen for the 3 symbols completes cleanly
and the new column is non-NaN past the 51-bar warm-up (≈ 90%).

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Numerical Criteria (LOCKED)

This is an EXPLORATION; it cannot MERGE and cannot update BASELINE_V3.md
(`feedback_v3_cadence_discipline.md` — only a CONFIRMATION-MERGE updates the
baseline). Section 8 LOCKs the axis-classification taxonomy per
`feedback_v3_cycle1_axis_pass_criteria.md` cycle-2 thresholds. The classifier is
evaluated in this DISJUNCTIVE ORDER (SUSPICIOUS → NULL-RESULT → NEGATIVE →
PROMISING → INERT) — established /071/073/074/075 precedence. The first matching
classification is canonical.

All deltas are vs the iter-v3/060 EXPLORATION-mode anchor (IS +0.8325 /
OOS +0.1403). The OOS/IS ratio is the within-iteration `comparison.csv`
`monthly_sharpe` ratio column (the canonical definition — no alternative
construction).

**8.1 — PROMISING-AT-EXPLORATION** (all four conjuncts required):
- IS monthly Sharpe Δ ≥ **+0.10** vs /060 (i.e. IS Sharpe ≥ +0.9325), AND
- OOS monthly Sharpe Δ ≥ **+0.20** vs /060 (i.e. OOS Sharpe ≥ +0.3403), AND
- frac_positive_paths ≥ **0.50**, AND
- no Critic methodology FAIL (13 checks + §11 anti-pattern scan).

**8.2 — NEGATIVE-AT-EXPLORATION** (disjunctive OR — either gate fails):
- IS monthly Sharpe Δ < **-0.10** vs /060 (IS Sharpe < +0.7325), OR
- OOS monthly Sharpe Δ < **-0.20** vs /060 (OOS Sharpe < -0.0597).

**8.3 — INERT-AT-EXPLORATION:**
- IS monthly Sharpe Δ within **[-0.10, +0.10]** vs /060, OR OOS monthly Sharpe Δ
  within **[-0.20, +0.20]** vs /060 (the noise band), AND not SUSPICIOUS, AND not
  NEGATIVE, AND not PROMISING. (The Section 7 ≈40%-probability mode lands here:
  the feature carries IS-only signal but the model under-allocates it at
  single-seed n_trials=35, so a shift lands inside a noise band.)

**8.4 — SUSPICIOUS** (disjunctive — fires on EITHER ground; SUSPICIOUS takes
classification PRECEDENCE over NEGATIVE and INERT when concurrent, per the
/071/073 precedence rule, with NO magnitude qualifier):
- **OOS/IS monthly Sharpe ratio > 3.0** (`feedback_v3_oos_is_ratio_gate.md` —
  fires unconditionally regardless of absolute OOS Sharpe), OR
- **SUSPICIOUS-OOS-DOMINANT sub-mode:** IS shift < 0 AND OOS shift ≥ +0.20, OR
- **holding-time-orthogonality violation:** the /076 kept-roster mean trade
  duration shifts by > +1.0 candle vs the /060 roster (Section 4.3 falsifier) —
  a new feature has no duration-extension mechanism, so a > +1.0-candle shift
  signals the feature is unexpectedly acting like a holding-time-extension axis
  and the result must be treated as SUSPICIOUS.

**8.5 — NULL-RESULT:** the /076 IS trade roster is BIT-IDENTICAL to /060 (zero
trades changed) — the model allocated `range_efficiency_50` zero splits and the
feature produced no behavioral effect. (Distinct from INERT: INERT means the
feature changed the roster but the headline shift landed in a noise band;
NULL-RESULT means literally zero roster change.)

**Evaluation order:** SUSPICIOUS (8.4) → NULL-RESULT (8.5) → NEGATIVE (8.2) →
PROMISING (8.1) → INERT (8.3). First match is canonical.

A PROMISING-AT-EXPLORATION outcome carries the axis forward to the cycle-2
CONFIRMATION (iter-v3/081 or later) as a candidate ingredient; it is NOT a MERGE
signal in itself. An INERT / NEGATIVE / SUSPICIOUS / NULL-RESULT outcome does NOT
advance and does NOT update BASELINE_V3.md.

---

## Section 9 — Library Stack Declaration

No new library is introduced. `compute_range_efficiency_50` uses only `numpy` and
`pandas` (already pinned). Versions in effect (per the /059 baseline
reproducibility stamp):

- lightgbm: 4.6.0
- optuna: 4.8.0
- numpy: 2.2.6
- pandas: 3.0.0
- scikit-learn: 1.8.0
- scipy: 1.17.0
- statsmodels: 0.14.6 (ADF — Critic Check 5; the new feature is added to the ADF
  scan and is expected to pass — a path-efficiency ratio bounded to [0,1] is
  stationary by construction)
- pyarrow: 23.0.1
- mlfinlab / pypbo / fracdiff: not invoked by this axis (the feature is
  pure-numpy; CPCV/PBO/PSR reporting is unchanged from /060).

Walk-forward harness: the embargo (22 candles) + REQUIRED_GAP (66) are unchanged
— the new feature changes neither the label horizon nor the symbol count. The
walk-forward fix (`train_end_ms = test_start_ms - embargo_ms`,
`compute_embargo_candles(10080,480)=22`) is intact and untouched.

### 9.1 Integration test (methodology-axis discipline)

`range_efficiency_50` is a feature axis, not a methodology-reporting axis, so the
`feedback_v3_methodology_axis_integration_test.md` mandate (end-to-end smoke test
for axes that add computed fields to dsr.json/comparison.csv) does not strictly
apply — the feature adds no field to the methodology reports. The NEW
`tests/features_v3/test_range_efficiency_50.py` includes an integration-style
assertion: `add_engineered_v3_features` on a synthetic OHLC frame appends the
`range_efficiency_50` column with values in [0, 1] — exercising the
GROUP_REGISTRY dispatch path, not just the math function in isolation. Phase 6's
feature-parquet regen for BCH/LDO/TRX is the full end-to-end exercise (the new
column appears in each symbol's parquet and is passed to LightGBM via the
explicit `feature_columns` list).

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`, the /076 axis was selected
by the QR with committed EDA backing, NOT by an orchestrator ad-hoc pick.

### 10.1 — Per-parameter selection-function disclosure (Critic /075 Rec #2)

Critic /075 FINAL `2211927` Rec #2 mandates that every EDA select each design
parameter via a function whose inputs are demonstrably IS-only or a-priori, and
that the brief/EDA state, per parameter, the exact selection function and its
input columns. The /076 EDA does this in its module docstring; reproduced here:

- **PARAMETER 1 — WHICH candidate feature (C1 / C2 / C3 / C4).**
  Selection function: `_pick_feature(t2, t3)` in the EDA `main()`.
  Inputs: T2 column `is_bearchop_discrimination_auc` (IS-only — the rank-AUC of
  the feature separating winning vs losing IS-bear/chop trades) AND T3 column
  `regime_sign_abs_corr` (the |point-biserial correlation| between the feature's
  per-trade value and the IS/OOS regime indicator).
  Rule: among candidates whose `regime_sign_abs_corr` < 0.35 (the a-priori
  data-free ceiling), pick the one with the highest IS-only
  `is_bearchop_discrimination_auc`. Outcome: `C2_range_efficiency_50` (all 4
  candidates cleared the 0.35 ceiling; C2 had the top IS-only AUC of 0.657).
  **No OOS metric used:** T3's regime indicator is the IS/OOS CALENDAR LABEL
  (fixed by OOS_CUTOFF_DATE — a calendar fact), NOT an OOS PnL / OOS Sharpe /
  OOS counterfactual. A repository-wide grep of the /076 EDA source for
  `oos_delta` / `oos_monthly_sharpe` / `oos_is_ratio` returns ZERO matches in
  executable code (the 3 string matches are docstring text explaining what is
  NOT computed).
- **PARAMETER 2 — the feature's lookback window.**
  Selection function: a-priori constant. The window is 50 bars — the window of
  the dead-code `compute_efficiency_ratio_50` that `range_efficiency_50`
  re-evaluates. No window SWEEP, no fit to IS or OOS. Reusing the existing
  primitive's window length is also an engineering a-priori (it keeps the
  feature computable with one parquet regen).
- **A-priori constant — the 0.35 regime-sign-corr ceiling.** A data-free
  threshold: a feature whose value correlates > 0.35 in absolute terms with the
  bull/bear regime axis is too close to a directional-regime proxy to escape the
  /075 trap. It is not fitted to any data.

This iteration's first EDA pass had NO OOS-tuning defect — unlike /075's first
pass, the /076 EDA was written to the corrected template from the start: no
per-candidate OOS counterfactual is computed; T3 uses only the calendar IS/OOS
label; the per-parameter block above is in the EDA docstring.

### 10.2 — Re-evaluation justification: `range_efficiency_50` vs the /043 `efficiency_ratio_50` ban

`range_efficiency_50` uses the SAME Kaufman path-efficiency MATH as the feature
`efficiency_ratio_50`, which was **DISASTROUS-NEGATIVE at iter-v3/043** (IS
−0.8445 / OOS −0.8990; all 4 symbols broken) and is on the BASELINE_V3.md "BANNED
features" list, with a `run_baseline_v3.py` pre-flight assertion banning the
literal name `efficiency_ratio_50`. Re-introducing this math requires explicit
justification — given here in full, transparently:

1. **The re-evaluation is rule-sanctioned.** `feedback_v3_walkforward_lookahead_bug.md`
   states that all v3 iterations PRE-`e149e9d` (the walk-forward fix) are
   INVALIDATED and that cycle-3 EXPLORATION verdicts (iter-v3/029–/057, which
   includes /043) are "eligible for re-evaluation as part of the post-fix
   axis-rethink rule." /043's verdict was produced under the BUGGY walk-forward;
   it does not automatically transfer to the post-fix landscape.

2. **The UNIVERSE is different.** /043 ran a 4-symbol universe that INCLUDED
   ALGO — the direction-asymmetric bottleneck symbol (`feedback_v3_axis_selection_quant_discipline.md`
   records ALGO LONG as the single largest IS attribution loss of that era).
   /076 runs the post-bootstrap 3-symbol universe BCH/LDO/TRX — ALGO is in
   V3_EXCLUDED_SYMBOLS-equivalent territory (dropped). A feature that broke a
   universe containing ALGO is not thereby disqualified for a universe without
   it.

3. **The ROLE is different — and this is the decisive point.** /043 used the
   unsigned ER as a STANDALONE feature whose docstring-recorded failure mode was
   "treats trending-up and trending-down markets identically" — i.e. it was
   expected to carry DIRECTIONAL information and could not (a sign-invariant
   feature cannot pick trade direction; /063's `trend_efficiency_signed` added
   the sign back precisely for that reason). /076 adds `range_efficiency_50` as
   the **15th feature alongside 14 features that already carry direction**
   (`regime_momentum_signed_5d`, `btc_ret_14d`, `ema_spread_atr_20`,
   `sym_vs_btc_ret_7d`, …). Its job is NOT to provide direction — the 14 existing
   features do that — its job is to be a regime-QUALITY conditioning feature: it
   tells the model "is this a clean efficient move or a choppy grind." The /076
   EDA's T2 confirms this is exactly the role the feature can play: it
   discriminates winning from losing IS-bear/chop trades (AUC 0.657) on BOTH
   LONG and SHORT trades (|corr with direction| 0.115 — it is NOT directional),
   which is a trade-QUALITY signal, not a directional one. The /043 failure mode
   (sign-invariance breaks a standalone directional signal) is the very property
   /076 WANTS — it is what makes the feature regime-orthogonal (T3 |regime-sign
   corr| 0.010) and lets it escape the /075 IS-up/OOS-down trap.

4. **The naming is honest, not evasive.** The feature is named `range_efficiency_50`,
   NOT `efficiency_ratio_50`, so the literal-name pre-flight ban stays
   meaningful and is not silently circumvented. The new function's docstring,
   this Section 10.2, the EDA module docstring, and the setup commit message all
   disclose explicitly that the math is the same as `efficiency_ratio_50` and
   that this is a deliberate, rule-sanctioned re-evaluation. The precedent for a
   same-family-different-role feature with a new name is /063's
   `trend_efficiency_signed` (the signed variant of the same /043 ER, added with
   a new name and a different mechanism).

5. **The honest risk.** Section 7 weights NEGATIVE at ≈22% precisely because the
   engineered-feature graveyard — including this feature's /043 ancestor — is
   real. The re-evaluation is justified by the EDA evidence (strong IS-only
   discrimination, clean regime-orthogonality, low IC) and the rule, but it is a
   single-seed EXPLORATION and the result could still be NEGATIVE. The Section 8
   falsifiers (IS Δ < −0.10, OOS Δ < −0.20, importance rank 15/15) are the
   pre-registered stops, and the /043 history is exactly why the brief does not
   over-claim a PROMISING outcome (PROMISING weighted 30%, below INERT's 40%).

### 10.3 — Orchestrator framing and the axis decision

- **Orchestrator framing:** the orchestrator carried the Critic /075 Rec #3 HARD
  MANDATE (break the IS-up/OOS-down tension; the suggested direction is a
  feature-internal IS-regime discriminator the model learns) and named three
  candidate families (a feature-internal discriminator; a re-scoped meta-labeling
  M2 on signal quality; a dedicated IS bear/chop sub-period attribution axis).
  The orchestrator did NOT pre-commit a specific axis.
- **The QR axis decision:** the QR ran the EDA and selected the feature-internal-
  discriminator family (the Critic's HIGHEST-priority direction). Within that
  family, the EDA itself drove the data-derived design parameter: it evaluated
  FOUR sign-invariant candidate features and picked `range_efficiency_50` via the
  `_pick_feature(t2, t3)` IS-only + calendar-label selection function (Section
  10.1). The 50-bar window is a-priori (Section 10.1 PARAMETER 2).
- **Why NOT the alternative candidate families:**
  - **A re-scoped meta-labeling M2** (Critic candidate #2) was NOT selected. A
    meta-labeling M2 that filters trades risks re-triggering the holding-time-
    extension trap (the /071 M2 veto removed early stop-outs, lengthening the
    kept roster — SUSPICIOUS). The Critic's own framing requires the M2 to be
    "verified holding-time-orthogonal at brief stage" — a meta-label that filters
    on signal quality is HARD to prove holding-time-orthogonal a priori (a
    quality filter that vetoes weak trades will, on average, veto the
    shorter-held quick stop-outs). A feature is unambiguously holding-time-
    orthogonal (it has no veto mechanism — Section 4.3). The feature-internal
    discriminator is the cleaner, lower-risk realization of the same
    Critic-mandate intent (discrimination the MODEL learns, not a post-gate
    classifier).
  - **A dedicated IS bear/chop sub-period attribution axis** (Critic candidate
    #3) — the /076 EDA's T1 + T2 + T3 ARE that attribution (T1 stratifies the IS
    window; T2 decomposes which feature discriminates the bear/chop drag; T3
    characterizes the regime-coupling). A pure-attribution iteration would be a
    PASSIVE-DIAGNOSTIC with no backtest; /076 instead ACTS on the attribution's
    finding (a sign-invariant feature discriminates the drag) with a concrete
    feature.

### 10.4 — Reproducibility stamp

- **EDA SHA:** `40b6e66` — `analysis/iteration_v3-076/axis_selection_eda.py`
  (T0–T7: anchor, regime stratification, candidate-feature within-IS
  discrimination, regime-sign-correlation test, holding-time predictor,
  behavioral-effect predictor, per-symbol IS discipline, IC matrix).
- **Brief SHA:** `ed7b27b` — `briefs-v3/iteration_v3-076/research_brief.md`
  (this file; all 11 sections — 0, 0.5, 1-10).
- **Setup commit SHA:** `79a62b0` — `setup(iter-v3/076): NEW feature
  range_efficiency_50 + revert /075 Primitive 12`. The setup commit makes the
  Section 3 / 3.1 code changes: the new `compute_range_efficiency_50` + dispatch
  + `__all__` in `engineered_v3.py`; the 15th-feature addition to
  `V3_FEATURE_COLUMNS_TOP_N`; the /075 Primitive-12 revert
  (`enable_regime_size_scalar` True→False) in `run_baseline_v3.py`; the
  `_verify_feature_columns` count assertions (14→15) + the
  `range_efficiency_50`-present assertion + the Primitive-12 assertion
  replacement; `ITERATION_LABEL` → "v3-076"; the NEW
  `tests/features_v3/test_range_efficiency_50.py` (6 tests); the feature-count
  assertion updates (14→15) in `test_v3_feature_count.py`,
  `test_features_for_symbol.py`, and the 3 `*_universal.py` feature tests; and
  the stale-test fix in `test_cpcv_embargo_assert.py` (N_SYMBOLS 4→3,
  CORRECT_GAP 88→66 — a pre-existing failure since the iter-v3/069
  universe-expansion closeout). Verification: ruff clean on all modified files;
  `tests/features_v3/` + `tests/strategies/ml/` 345 passed / 3 skipped; runner
  `_verify_feature_columns(ensemble_size=3)` pre-flight PASS.
- **Phase 5.5 gate SHA:** _(set by the QE at the Phase 5.5 gate commit)._

**Per-symbol IS-axis discipline** (`feedback_v3_per_symbol_lifts_oos_breaks_is.md`):
`range_efficiency_50` is a UNIVERSAL feature — there is NO per-symbol
customization. The memory rule's anti-pattern (per-symbol customizations lift OOS
but break IS aggregate) does not apply: a universal feature is the PREFERRED
axis type because all 3 symbols' models see the same column and the IS aggregate
is preserved by construction. T6 (Section 2.4) confirms the feature carries
within-IS-bear/chop signal for the symbols that trade the drag regime (BCH AUC
0.697, TRX AUC 0.555). The honest caveat: the feature's IS value is validated
here at single-seed EXPLORATION; if /076 is PROMISING, the cycle-2 CONFIRMATION
must re-validate that the feature preserves IS Sharpe at 10-seed mode before
bundling.
