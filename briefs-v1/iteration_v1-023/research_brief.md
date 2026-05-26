# iter-v1/023 — Research Brief (Phases 2-5)

**Branch**: `iteration-v1/023` from `iteration-v1/022` HEAD `08ef3c6` (tag `v0.v1-022`).

**Anchor**: `v0.v1-baseline-corrected` (`BASELINE_V1.md` commit `f8bc12c`). Portfolio IS Sharpe **+0.2829** / OOS Sharpe **+0.6637** / OOS trades 189 / 5-sym universe / 4 models (A, C, D, E). Portfolio comparison.csv "sharpe" semantics = monthly daily-annualized.

**Track**: v1 (refactored 2026-05-23). 13 phases. LightGBM Master + Critic.

**Iteration type**: EXPLORATION (cycle-3 #8 of 10).

---

## Section 0 — Position in cycle / pivot context

### 0.1 Cycle-3 cadence position

- Cycle-3 EXPLORATION #8 of 10 (CONFIRMATION earliest at /027).
- Prior cycle-3 EXPLORATIONs: /016 sample-weighting NEGATIVE-catastrophic; /017 universe NEGATIVE-anti-direction-INERT; /018 per-cohort-LINK PROMISING-INERT-favorable; /019 per-cohort-ETH+gate PROMISING; /020 per-cohort-BTC NEGATIVE-CATASTROPHIC; /021 methodology-pivot PROMISING-METHODOLOGY non-compoundable; /022 per-cohort-LTC NEGATIVE-CATASTROPHIC.
- Cycle-3 ledger thus far: 2 PROMISING (/018 LINK, /019 ETH+gate) + 1 PROMISING-METHODOLOGY (/021) + 2 NEGATIVE clean (/016/017) + 2 NEGATIVE-CATASTROPHIC (/020/022) + 0 merges.

### 0.2 Convergent axis-rotation routing

Per Critic Phase 7.5 review.md §"Path Forward" + LM Master Phase 7.4 §5 STRONGEST recommendation + QR Phase 7 evaluation §6 CONVERGENT routing, /023 axis = **funding-rate z-score feature family**, family `feature-family`. 3-way CONVERGENT routing (Critic + LM Master + QR — first triple-consensus axis selection in cycle-3).

Per-cohort axis SATURATED for ASYMMETRIC_ROTATION cohorts at n=2 (BTC /020 + LTC /022). Per /022 NEW memory `feedback_v1_per_cohort_saturation_asymmetric_rotation.md`: future per-cohort axes target POSITIVE_EVERYWHERE or counter-trend-symmetric cohorts only; ASYMMETRIC_ROTATION cohorts go IN POOL.

/023 also satisfies the structural-over-knob pivot mandate (`feedback_v3_structural_over_knob_exploration.md` adopted by v1): NEW feature families > NEW model arch > NEW labeling > NEW risk primitive > universe > gate knobs. NEW feature families NOT touched in cycle-3 to date (cycle-2 had /007 + /009 feature-family axes both NEGATIVE-compound; cycle-3 first feature-family attempt).

### 0.3 Anchor-frame BINDING (locked at /022 closeout)

Per /022 Critic Rec #3 ELEVATED to BINDING: F1 frame = comparison.csv "sharpe" semantics (daily-annualized monthly Sharpe per `_compute_daily_sharpe()` runner code path). Baseline anchor pre-computed:

| Metric | Anchor value | Source |
|---|---|---|
| **F1 OOS Sharpe Δ anchor** | **+0.6637** (portfolio daily-annualized monthly) | `reports-v1/iteration_v1-baseline/comparison.csv` "sharpe" row, out_of_sample column |
| F3 IS Sharpe Δ anchor | +0.2829 | comparison.csv "sharpe" row, in_sample column |
| OOS total trades anchor | 189 | comparison.csv "total_trades" row, out_of_sample column |
| IS total trades anchor | 621 | comparison.csv "total_trades" row, in_sample column |

Predicted /023 deltas measure F1 ⇔ daily-annualized monthly Sharpe vs +0.6637 anchor.

### 0.4 v3 prior — load-bearing structural verdict (4-data-point catalog)

The v3 funding axis is a **4-data-point STRUCTURAL VERDICT — ALL NEGATIVE/INERT-by-importance**. From `analysis/iteration_v1-023/funding_v3_prior_assessment.csv` (commit `c3f4551`):

| v3 iter | Axis | Optuna budget | Verdict | Failure mode |
|---|---|---|---|---|
| iter-v3/019 | per-sym z30 (14th feature) | n_trials=10, --seeds 1 | PROMISING-INERT | Importance rank 14/14 (LDO+TRX+Portfolio); BCH rank 10/14 |
| iter-v3/023 | same z30 at higher budget | n_trials=35, --seeds 1 | NEGATIVE clean (OOS Δ -1.07) | INERT feature actively HARMS at higher Optuna budget (`feedback_v3_inert_features_at_higher_budget.md`) |
| iter-v3/024 | btc_funding broadcast (cross-asset) | n_trials=35, --seeds 1 | NEGATIVE clean (OOS Δ -1.20) | BTC funding rank 14/14 BCH+LDO+Portfolio (cross-asset variant inherits same INERT pattern) |
| iter-v3/082 | 4-feature FAMILY (sign-persist, momentum, accel, divergence) | n_trials=35, --seeds 3 | SUSPICIOUS-OOS-DOMINANT | 4 features rank 15/16/17/18 of 18; combined 9.90% gain share (below uniform-parity 5.56% per feature) |

**v3 cycle-3 finding (codified `feedback_v3_cross_asset_ohlcv_closed.md`)**: pure OHLCV-derived ETH/BTC primitives at any window or transform CONSIDERED EXHAUSTED for the v3 BCH/LDO/TRX universe. Funding-rate is non-OHLCV (separate data source) so it survives the cross-asset OHLCV closure — but the funding-specific v3 verdict still holds at 4 data points.

**v1 STRUCTURAL DIFFERENCES** (load-bearing for verdict-class priors):

| Dimension | v3 setup (failed) | v1 setup (/023) | Mitigation force |
|---|---|---|---|
| Optuna n_trials | 10 (/019) → 35 (/023+) | **18 at EXPLORATION** | n_trials=10 INERT-pattern threshold cleared; 35 above also tested INERT |
| Outer seeds | --seeds 1 (/019/023/024); --seeds 3 (/082) | **--seeds 1 EXPLORATION** | Same as v3 INERT cases (no mitigation) |
| Ensemble size | ENSEMBLE_SIZE=3 | **ENSEMBLE_SIZE=3** | Same |
| Universe | 3-symbol BCH+LDO+TRX (per-symbol models) | **5-symbol BTC+ETH+LINK+LTC+DOT (4 models incl. POOL Model A)** | **2× training rows in pool Model A** (BTC+ETH joint loss); 5-symbol universe provides 67% more cohorts to interact across |
| Model architecture | per-symbol single-cohort 3 models | **4 models (A pool + C/D/E single-symbol)** | Pool Model A is the v3-untested architecture variant — joint BTC+ETH loss surface gives funding-rate feature 2× training data |
| Feature count | 14 (post /019); 18 (post /082) | **40 (PRUNED) → 42 (post /023)** | LightGBM `colsample_bytree` samples by position; larger feature column count dilutes a NEW feature's selection probability — but v1's 40-col pruned set selects more aggressively than v3's 14-col set; SAME risk |
| Historical data depth | 2021-mid+ for LDO/TRX (~2.5y IS); ~3y for BCH | **2020-01+ for BTC/ETH/LINK/LTC**, 2020-08+ for DOT (~4-5y IS) | Funding starts at kline-inception for all 5 v1 symbols (`funding_availability.csv` — 0-day lag); 5675-5727 IS bars per symbol vs ~3000 for v3 |

**Structural hypothesis for v1 difference**: pool Model A's joint loss surface over BTC+ETH may capture funding-rate signal via cross-cohort splits (LightGBM can use `funding × symbol-dummy` interactions when 2 symbols pooled with sufficient data; v3's per-symbol models architecturally cannot). The v1 4-model architecture is a fundamentally different test platform from v3's 3 per-symbol models. If v1 inherits the v3 INERT pattern → it's a feature-level structural verdict (LightGBM doesn't learn funding signal across pooling differences); if v1 differs → pool Model A is the architectural lever, supports future axis where Model C/D/E may also rebalance training across pooled cohorts.

### 0.5 Cadence ledger summary

Cycle-3 EXPLORATION position: **#8 of 10**. Remaining slots: /024 + /025 + (optional sanity /026) before /027 CONFIRMATION earliest.

### 0.6 Architecture-Family Justification (v1-only)

- **Axis family**: `feature-family` (NEW 15th family — first NEW feature-family axis in cycle-3; family `feature-family` last used at cycle-2 /007 NEGATIVE-NEGATIVE-compound and /009 NEGATIVE-NEGATIVE-compound).
- **Prior 5 EXPLORATION families** (going INTO /023): per-cohort-specialization-LINK (/018), per-cohort-specialization-ETH (/019), per-cohort-specialization-BTC (/020), methodology-pivot (/021), per-cohort-specialization-LTC (/022).
- **Rotation status**: VALID — `feature-family` is in NONE of the prior 5 (different from per-cohort-specialization-X AND methodology-pivot). Also mandated per per-cohort saturation rule.
- **One-sentence rationale**: 3-way CONVERGENT routing (Critic + LM Master + QR) selects funding-rate z-score as PRIMARY following per-cohort axis SATURATION + structural-over-knob pivot mandate + NEW signal source untested in v1.

### 0.7 Wall-clock estimate

- Baseline 5-seed full ENSEMBLE = 7h 0m
- /023 single-seed ENSEMBLE_SIZE=3 + 2 NEW feature columns + V1_FEATURE_COLUMNS_PRUNED 42-col base
- Estimate: **35-45 min** (5-symbol pool + 2 NEW features needs feature-parquet recomputation for funding-rate columns; full backtest ~25-30 min)
- HARD CAP 2h (cycle-3 EXPLORATION discipline `4cb8972`)

---

## Section 1 — Hypothesis

**H_AXIS**: Adding 2 funding-rate z-score features (`funding_rate_zscore_30` 10-day window + `funding_rate_zscore_90` 30-day window) to V1_FEATURE_COLUMNS_PRUNED (40 → 42) at v1's pool Model A + single-symbol Model C/D/E architecture **encodes positioning-crowding signal that the model can learn via cross-cohort splits in pool Model A** (untested in v3's per-symbol architecture), differentiating /023 from v3's 4-data-point INERT verdict.

**Mechanism story** (basin-level per /021 H2 REFUTATION binding):
- Funding-rate z-score is a **new exogenous signal source** capturing perpetual-futures positioning crowding (BIS WP 1087 2025: 10% carry shock → 22% liquidation jump).
- In pool Model A's joint BTC+ETH loss surface, LightGBM trees may use `funding × symbol-dummy` splits at sufficient depth (max_depth interaction with the funding-z-score axis encodes "BTC's funding stress is different from ETH's funding stress at the same nominal z-value"); per-symbol models lack this lever.
- Single-symbol Model C/D/E will load funding-rate at lower importance, but the ORACLE EDA (Section 2) shows IS-anchored mechanism support: negative funding band z30∈[-2,-1] is the HIGHEST EDGE BAND (47% WR, +78.55% net PnL across 68 trades — 11.0% of IS trades but 154% of total IS net PnL).
- The signal is universal across 4 of 5 symbols (LTC outlier with -12.08% in negative band, but offset by +39.61% in positive band).

**Specific mechanism prediction**: in IS, the model conditions trade timing on funding-rate regime; OOS effect depends on whether the regime distribution holds. The +78.55% net PnL concentration in negative funding band on baseline trades represents an IS-anchored prior that is mechanistically distinct from any v1 feature already in V1_FEATURE_COLUMNS_PRUNED (IC < 0.44 across all 5 symbols and all top-5 features).

**Direction of expected lift**: positive F1 OOS Sharpe Δ if the model learns the regime conditioning; INERT verdict if importance rank reproduces v3 pattern; negative if Optuna overfit at higher Optuna budget pattern.

**ORACLE EDA caveat (LM Master §2 DOWNGRADE, 2026-05-27)**: the +78.55% IS net PnL in z30 ∈ [-2, -1] band is **descriptively valid but NOT a quantitative predictor of /023 OOS Sharpe Δ**. Per /022 BTC + LTC Jaccard 0.10/0.09 vs baseline pool roster, single-axis feature additions produce ~90% NEW trade rosters under single-seed retraining (basin relocation). The IS-anchored mechanism (negative funding band = short-crowded mean-reversion setup) is causal and roster-agnostic, but the **specific +78.55% PnL share will NOT reproduce** in the /023 retrained trade roster. Per-symbol texture also matters: DOT extreme-negative band is only 4 trades (sparse), and LTC negative-band shows -12.08% in counter-direction — the +78.55% is BTC+LINK+DOT-dominated, NOT universal. Section 2.7 expands. Hypothesis is interpreted as **mechanism support** NOT **outcome forecast**.

---

## Section 2 — IS-only Evidence (numerical tables from committed analysis)

### 2.1 Funding-rate data availability

From `analysis/iteration_v1-023/funding_availability.csv` (commit `c3f4551`):

| Symbol | Kline rows | Funding rows | Kline start | Funding start | Funding lag |
|---|---|---|---|---|---|
| BTCUSDT | 7012 | 7326 | 2020-01-01 | 2019-09-10 | **0 days** |
| ETHUSDT | 7013 | 7094 | 2020-01-01 | 2019-11-27 | **0 days** |
| LINKUSDT | 6964 | 6941 | 2020-01-17 | 2020-01-17 | **0 days** |
| LTCUSDT | 6973 | 6965 | 2020-01-09 | 2020-01-09 | **0 days** |
| DOTUSDT | 6311 | 6293 | 2020-08-22 | 2020-08-20 | **0 days** |

All 5 v1 universe symbols have funding cache from kline inception (zero lag). Funding extends to 2026-05-18 (matches kline coverage modulo trailing forming-candle period).

### 2.2 IS-only z-score distribution

From `analysis/iteration_v1-023/funding_distribution.csv`:

| Symbol | IS bars | Raw mean | Raw std | Raw skew | Raw kurt | z30 std | z30 \|z\|>2 % | z90 std | z90 \|z\|>2 % | z30 at clip |
|---|---|---|---|---|---|---|---|---|---|---|
| BTCUSDT | 5727 | 0.000128 | 0.000232 | 2.94 | 25.65 | 1.462 | 7.83% | 1.256 | 7.13% | 0.60% |
| ETHUSDT | 5727 | 0.000154 | 0.000302 | 2.97 | 32.59 | 1.443 | 8.08% | 1.316 | 7.57% | 0.45% |
| LINKUSDT | 5678 | 0.000149 | 0.000384 | 2.32 | 32.18 | 1.525 | 8.27% | 1.329 | 7.75% | 0.65% |
| LTCUSDT | 5687 | 0.000164 | 0.000327 | 3.17 | 31.11 | 1.514 | 8.93% | 1.321 | 8.29% | 0.60% |
| DOTUSDT | 5025 | 0.000101 | 0.000366 | 3.64 | 21.06 | 1.494 | 9.31% | 1.283 | 7.25% | 0.50% |

**Properties**:
- Raw funding is mildly right-skewed (longs pay shorts on net; mean ~0.01-0.02% per 8h cycle).
- Heavy positive tails (kurt 21-33) — common for perpetual-futures funding.
- No clamping at Binance's +0.0001 floor (raw_at_clamp_floor_pct = 0.0% for all symbols).
- z30 std slightly > 1.0 (1.44-1.53) — past-only window normalization preserves some residual fat-tail variance.
- z30 |z|>2 events fire 7.8-9.3% of bars; |z|>3 events 3.7-4.3% — non-trivial extreme regime coverage.
- z30 at-clip rate 0.45-0.65% — small fraction touched ±10 clip; outliers exist but rare.
- z90 (90-bar / 30-day window) is smoother (std 1.26-1.33) with similar extreme rate.

### 2.3 IC vs existing V1_FEATURE_COLUMNS_PRUNED top features (Critic Check 4)

From `analysis/iteration_v1-023/funding_zscore_ic.csv`:

| Comparison | BTC | ETH | LINK | LTC | DOT | Max \|IC\| |
|---|---|---|---|---|---|---|
| z30 vs vol_atr_14 | -0.064 | -0.051 | -0.084 | -0.077 | -0.089 | 0.089 |
| z30 vs trend_aroon_osc_50 | +0.135 | +0.132 | +0.037 | +0.067 | +0.090 | 0.135 |
| z30 vs stat_autocorr_lag5 | +0.046 | +0.030 | +0.003 | -0.028 | +0.020 | 0.046 |
| z30 vs stat_kurtosis_20 | +0.030 | +0.024 | -0.008 | -0.014 | -0.030 | 0.030 |
| z30 vs mom_macd_line_12_26_9 | +0.259 | +0.222 | +0.225 | +0.279 | +0.255 | 0.279 |
| z90 vs trend_aroon_osc_50 | +0.336 | +0.316 | +0.237 | +0.285 | +0.312 | 0.336 |
| z90 vs mom_macd_line_12_26_9 | +0.403 | +0.368 | +0.375 | **+0.438** | +0.419 | **0.438** |

**Critic Check 4 verdict**: **ALL 25 IC values pass < 0.7 threshold**. Highest IC observed is LTC z90 vs mom_macd_line_12_26_9 at +0.4384 — well below 0.7 cutoff. Z90 IC consistently higher than Z30 (smoother features pair with momentum trends more naturally). NEW family acceptance criterion clears.

### 2.4 z30 regime distribution (IS-only)

From `analysis/iteration_v1-023/funding_regime.csv`:

| z30 band | BTC share | ETH share | LINK share | LTC share | DOT share | Mean |
|---|---|---|---|---|---|---|
| Extreme negative (z<-2) | 4.08% | 4.33% | 5.00% | 4.60% | 5.25% | 4.65% |
| Negative (-2 to -1) | 11.14% | 10.82% | 8.23% | 9.14% | 8.90% | 9.65% |
| Neutral (-1 to +1) | 70.12% | 71.09% | 76.48% | 72.87% | 72.22% | 72.55% |
| Positive (+1 to +2) | 10.91% | 10.02% | 7.01% | 9.07% | 9.57% | 9.32% |
| Extreme positive (z>2) | 3.74% | 3.75% | 3.27% | 4.33% | 4.06% | 3.83% |

Symmetric distribution across all 5 symbols. ~73% of bars in neutral [-1,1], ~9% each in moderate negative/positive, ~4% each in extreme tails. Extreme positive slightly rarer than extreme negative (3.83% vs 4.65%).

### 2.5 ORACLE EDA — baseline IS trades by z30 band

From `analysis/iteration_v1-023/funding_oracle_band_attribution.csv` (caveat: ORACLE EDA descriptive only — see Section 2.7):

| z30 band | N trades | Win rate | Mean PnL % | Sum PnL % | % of total IS PnL |
|---|---|---|---|---|---|
| Extreme negative (z<-2) | 36 | 38.9% | +0.17% | **+6.04%** | +12% |
| **Negative (-2 to -1)** | **68** | **47.1%** | **+1.16%** | **+78.55%** | **+154%** |
| Neutral (-1 to +1) | 438 | 39.3% | -0.11% | **-47.25%** | -93% |
| Positive (+1 to +2) | 62 | 37.1% | +0.09% | +5.52% | +11% |
| Extreme positive (z>2) | 11 | 45.5% | +1.20% | +13.25% | +26% |

**Key finding**: the negative funding band z30 ∈ [-2, -1] is the HIGHEST EDGE BAND — only 11.0% of IS trades but **154% of total IS net PnL** (denominator-small framing because the total is +50.98% so a single 78.55% positive band drives the metric).

**Mechanism interpretation**: extreme negative funding signals short-crowded markets (shorts paying longs heavily); trades entering after sustained heavy short-funding tend to capture the mean-reversion / short-squeeze upside.

Neutral band (70% of trades) is NET NEGATIVE: -47.25% net PnL across 438 trades. Without funding-regime conditioning, the model is fighting against the structurally negative-EV majority regime.

### 2.6 ORACLE EDA — direction × band attribution

From `analysis/iteration_v1-023/funding_oracle_direction_attribution.csv`:

| z30 band | Direction | N trades | Win rate | Mean PnL % | Sum PnL % |
|---|---|---|---|---|---|
| Extreme negative (z<-2) | longs | 20 | 25.0% | -1.64% | **-32.86%** |
| Extreme negative (z<-2) | **shorts** | 16 | 56.3% | +2.43% | **+38.90%** |
| Negative (-2 to -1) | longs | 43 | 44.2% | +0.99% | +42.37% |
| Negative (-2 to -1) | shorts | 25 | 52.0% | +1.45% | +36.18% |
| Neutral (-1 to +1) | longs | 231 | 42.0% | +0.28% | +65.18% |
| Neutral (-1 to +1) | shorts | 207 | 36.2% | -0.54% | **-112.43%** |
| Positive (+1 to +2) | longs | 35 | 40.0% | +1.20% | +42.03% |
| Positive (+1 to +2) | shorts | 27 | 33.3% | -1.35% | **-36.51%** |
| Extreme positive (z>2) | longs | 2 | 50.0% | +0.74% | +1.48% |
| Extreme positive (z>2) | shorts | 9 | 44.4% | +1.31% | +11.77% |

**Direction effect**:
- In extreme negative funding (z<-2): **sign-flip pattern** — longs -32.86% (catastrophic) vs shorts +38.90% (profitable). 56% short WR vs 25% long WR. Mechanism: extreme short-funding = crowded shorts about to capitulate = better odds going long, NOT short (so model's IS shorts ride the squeeze).
- In neutral band: longs profitable (+65.18%) but shorts catastrophic (-112.43%); shorts are most of the drag.
- In positive funding (+1 to +2): longs +42.03%, shorts -36.51% — pattern continues, longs preferred when funding is positive.

The model would learn this signed regime conditioning if it captures funding-z-score × direction interactions. This is a multi-modal signal NOT fully encoded by existing momentum/volatility features (IC test in Section 2.3 confirms low correlation).

### 2.7 ORACLE EDA caveat (load-bearing per `feedback_v3_oracle_eda_validity.md`)

**ORACLE EDA is descriptively valid because the funding feature is STATELESS** (no signal-emission state propagation). It does NOT predict /023 trade-roster outcome because adding the feature to V1_FEATURE_COLUMNS_PRUNED retrains LightGBM and the basin will relocate. Per /022 BTC + LTC Jaccard 0.084-0.10 vs baseline pool roster, single-axis features can produce ~90% new rosters under single-seed retraining.

The ORACLE EDA shows **IS-anchored mechanism support** (negative funding band is high-edge for baseline trades) — it does NOT anchor a quantitative OOS Sharpe Δ prediction. The /023 trade roster from V1_FEATURE_COLUMNS_PRUNED + 2 NEW funding features at single-seed=42 n_trials=18 will differ. The MECHANISM is causal (negative funding regime = short-crowded mean-reversion setup) — the model operates on whatever roster the basin produces.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

**Declaration**: **HIGH-RISK**.

**Reason**: NEW data source (funding-rate cache from external endpoint, NOT OHLCV-derived); feature engineering changes Optuna's training-objective domain (V1_FEATURE_COLUMNS_PRUNED 40 → 42; `colsample_bytree` selection probability redistributes); 4-data-point v3 NEGATIVE precedent makes verdict-class outcome non-trivially uncertain.

**Mitigation** (HIGH-RISK opt-in per v1 rules): NO multi-seed validation opt-in for /023 EXPLORATION (single-seed=42 EXPLORATION default for axis isolation). RATIONALE for skipping multi-seed mitigation:
- /023 is #8 of 10 cycle-3 EXPLORATIONs; multi-seed would consume ~2.5h CONFIRMATION-spec budget, exceeding 2h EXPLORATION HARD CAP.
- Per v1 rule: "if 3+ HIGH-RISK single-seed EXPLORATIONs produce >1σ negative deltas, the next HIGH-RISK iteration becomes mandatorily multi-seed". cycle-3 HIGH-RISK lineage: /014 labeling HIGH-RISK (negative); /015 labeling HIGH-RISK CONFIRMATION (catastrophic). 2 HIGH-RISK with 1σ-negative deltas so far in cycle-3 — NOT yet 3+. /023 is the 3rd cycle-3 HIGH-RISK at single-seed budget; if NEG-CAT, next HIGH-RISK in /024+ becomes mandatorily multi-seed.
- v3 prior INERT pattern at single-seed is the binding empirical base — multi-seed at /023 EXPLORATION would not address importance-rank INERT failure mode (multi-seed reduces variance, doesn't change rank).

**Pre-commit**: if /023 verdict ∈ {PROMISING, PROMISING-INERT-FAVORABLE} → /024 considers funding-family variants (multi-channel construction per v3/082 inspiration). If /023 verdict = INERT-BY-IMPORTANCE → axis CLOSED for cycle-3, /024 pivots to per-cohort drawdown brake (Path Forward #2) or open-interest (different feature family). If /023 = NEG-CAT → mandatory multi-seed at next HIGH-RISK iteration.

---

## Section 3 — Proposed Changes

### 3.1 New code module

**NEW file**: `src/crypto_trade/features_v1/funding_v1.py`. Implements:
- `compute_funding_rate_zscore(kline_df, funding_df, window=30, clip=10.0)`: past-only rolling z-score (`.shift(1)`-lagged window, identical math to `features_v3/funding_v3.py:compute_funding_rate_zscore` modulo column naming).
- `compute_funding_rate_zscore_90(kline_df, funding_df, window=90, clip=10.0)`: 90-bar window variant.
- `add_funding_v1_features(df, data_dir="data", windows=(30, 90), clip=10.0)`: reads `data/funding_rates/<SYMBOL>.csv` (existing infrastructure from v3/019) and appends `funding_rate_zscore_30` + `funding_rate_zscore_90` columns.

**Track-isolation discipline**: ZERO imports from `crypto_trade.features_v2` or `crypto_trade.features_v3`. The funding math is copied (not imported) to maintain v1↔v3 isolation per `.claude/commands/quant-iteration-v1.md` §"Track isolation enforced at runtime".

### 3.2 V1_FEATURE_COLUMNS_PRUNED extension

**Modify** `src/crypto_trade/features_v1/__init__.py`:
- Add 2 NEW columns to `V1_FEATURE_COLUMNS_PRUNED` (alphabetical insertion):
  - `funding_rate_zscore_30` (insert at position 0 alphabetically before "interact_natr_x_adx" — actually after "cal_hour_norm" since "f" < "i")
  - `funding_rate_zscore_90`
- Update sanity guard assertion: `len(V1_FEATURE_COLUMNS_PRUNED) == 42`.

**NEW count**: 40 → 42 columns.

### 3.3 Runner wiring (run_baseline_v1.py)

**Modify** `run_baseline_v1.py`:
- In `_load_features_for_train`(or equivalent feature-load path), after reading per-symbol parquet, call `add_funding_v1_features(df)` to append the 2 NEW columns.
- Verification step: assert `funding_rate_zscore_30` + `funding_rate_zscore_90` present in feature dataframe before training; assert non-null rate >95% (after burn-in for first 30-90 bars).

**No risk-primitive changes** (R1/R2/R3 unchanged). No labeling changes. No symbol changes. Pure feature-family addition.

### 3.4 LM Master Phase 4.5 Responses

LM Master advisory `briefs-v1/iteration_v1-023/lgbm_advisor.md` was dispatched at Phase 4.5 and provides 8 recommendations across §1-§8. QR response below; **all 8 ADOPTED**.

| LM rec | Topic | QR action | Brief sections updated |
|---|---|---|---|
| §1 | v3 axis closure DOES NOT BIND v1 literally (non-OHLCV funding survives /124 closure) but v3's 4-data-point funding catalog transfers as empirical prior | **ADOPT — no brief change** | Section 0.4 already cites the 4-data-point catalog; LM Master §1 reinforces the load-bearing transfer |
| §2 | ORACLE EDA +78.55% DOWNGRADED as quantitative predictor per /022 basin-relocation lesson (Jaccard 0.10/0.09 = ~90% new roster) | **ADOPT** | Section 1 caveat appended; Section 2.7 Section 2 hypothesis interpretation strengthened |
| §3 | Recalibrate verdict priors **12/8/52/18/8/2** (LM Master) vs QR 15/10/45/15/10/5 — v3 4-point precedent dominant + colsample lottery 42-col less likely than 40-col | **ADOPT** | Section 5.1 priors REPLACED 15/10/45/15/10/5 → **12/8/52/18/8/2** |
| §4 | F-AXIS #1 STRENGTHEN with gain-share check (CRITICAL): rank-only insufficient per v3/082 evidence; tighten INERT to BOTH rank ≥ 32/42 on ≥ 3 cohorts AND family combined gain share < 4.0%; PROMISING-clean to rank ≤ 14/42 on ≥ 2 cohorts AND combined gain share ≥ 4.0% | **ADOPT** | Section 4.2 F-AXIS #1 falsifier table REWRITTEN with rank + gain-share dual gate; per-cohort gap-share data per cohort mandated as Critic Phase 7.5 watch item |
| §5 | n_eff_per_cell band tighten lower [4, 10] → **[5, 10]** (pool A 2× rows raises floor) | **ADOPT** | Section 4.2 F-AXIS-MECHANISM #3 band updated; Section 8 row format inherits |
| §6 | /024+ verdict-conditional pre-staging: PROMISING → funding family expansion ONE AT A TIME (per `feedback_v3_engineered_features_dont_stack.md` SAME-FAMILY); INERT modal → per-cohort drawdown brake; NEG-CAT → multi-seed HIGH-RISK + open-interest delta | **ADOPT** | Section 11.7 NEW staging matrix; Section 11.1/11.3/11.5 cross-referenced |
| §7 | Most important point: v1 pool Model A architectural advantage probably not large enough to break v3 4-data-point precedent at single-seed n_trials=18; verdict will diagnose feature-family limitation vs model-architecture-conditional signal | **ADOPT — no brief change** | Section 5 modal INERT 52% reflects this; Section 6.1/6.2 + Section 11.3 capture the diagnostic |
| §8 | /027 bundle composition: if PROMISING, funding-family contributes ~+0.20 to bundle Σ; realistic target +1.30-1.50 with correlation drag | **ADOPT** | Section 11.6 updated (note: 11.6 below RENAMED to "bundle composition impact" sub-row to disambiguate from /011 n_eff degenerate row, which moves to 11.8) |

**Track-record context**: LM Master entering /023 with H1 directional 2/3 + methodology 2/2 (per advisory §"Context Read"). At /022 LM Master predicted CAT-tail upweighting which fired; /023 LM Master MODE shift INERT 45% → 52% adopted in line with `feedback_iteration_quality.md` deference to LM Master tail-class re-weighting when ≥ 5pp.

**No LM Master recommendation REJECTED.** No MODIFIED beyond Section 5 + Section 4.2 numeric updates. Brief Section 3 (feature implementation) and Section 9 (no new deps) inherit LM Master §1 / §4 / §5 / §6 / §8 without code changes — implementation is unchanged (2 features funding_rate_zscore_30 + funding_rate_zscore_90). Single-seed=42 + n_trials=18 + ENSEMBLE_SIZE=3 + V1_FEATURE_COLUMNS_PRUNED 42 cols UNCHANGED.

**Phase 5.5 gate**: this section satisfies the "brief must address each LM Master recommendation" rule. Each rec is explicitly cited and either ADOPTED (with brief section traceability) or NOT MODIFIED (justified in-place). No REJECTED items.

---

## Section 4 — Falsifiers

### 4.1 Primary falsifiers (Sharpe-Δ)

| Falsifier | Threshold | Decision Tier |
|---|---|---|
| **F1 OOS Sharpe Δ vs anchor +0.6637** | ≥ +0.10 | PROMISING |
| F1 OOS Sharpe Δ | [-0.55, +0.10) | INERT or PROMISING-INERT depending on mechanism |
| F1 OOS Sharpe Δ | ≤ -0.55 | NEGATIVE-CATASTROPHIC |
| F3 IS Sharpe Δ vs anchor +0.2829 | ≥ +0.10 | IS-positive; sign-consistent if F1 also positive |
| F3 IS Sharpe Δ | ≤ -0.30 | IS-catastrophic; reject regardless of OOS |

### 4.2 F-AXIS-MECHANISM falsifiers (mechanism integrity)

**F-AXIS-MECHANISM #1 — Feature importance rank + family gain-share (DUAL GATE)** (load-bearing per v3 prior; LM Master §4 STRENGTHENED 2026-05-27):

Per LM Master §4 CRITICAL recommendation: rank-only insufficient because v3/082 4-feature family ranked mid (15-18 of 18) but combined gain share 9.90% (per-feature 2.475% < uniform-parity 5.56%) — load-bearing INERT diagnostic. v1 uniform-parity at 42 cols = 2.38%; 2-feature family combined uniform-parity threshold = 4.76%. **Strict per-cohort gain-share data is mandatory pre-Phase 7.5 deliverable.**

Per LM Master §4 thresholds:

| Outcome class | RANK gate | GAIN-SHARE gate | Required cohort coverage |
|---|---|---|---|
| **INERT-by-importance** (axis CLOSED) | rank ≥ 32/42 (bottom-quartile) | family combined < 4.0% gain share | ≥ 3 of 5 cohorts |
| **PROMISING-clean** (bundleable) | rank ≤ 14/42 (top-third) | family combined ≥ 4.0% gain share | ≥ 2 of 5 cohorts |
| **PROMISING-INERT-PARTIAL** | rank 15-31/42 mid-table | family combined 1.5-4.0% | any cohort coverage; downgrade to PROMISING-INERT-FAVORABLE if F1 ≥ +0.10 |
| **NEGATIVE classifier-misclassification** | any | any | F1 Sharpe alone dominates (Section 4.1) |

**Per-cohort gap-share data per cohort** is a MANDATORY Critic Phase 7.5 watch item — `feature_importance.csv` per (model, symbol) must include `gain_share` column (LightGBM split-importance / sum × 100); aggregated as `funding_family_gain_share_per_cohort.csv` deliverable in Phase 6 engineering report. Without per-cohort gain-share data, F-AXIS #1 classifier cannot fire → Critic BLOCK.

**Old QR threshold (rank-only)**: rank ≤ 14/42 ≥ 2 cohorts → PROMISING. **DEPRECATED 2026-05-27 per LM Master §4 / §9.**

**F-AXIS-MECHANISM #2 — Trade count**:
- IS trade count ∈ [500, 750] (baseline 621 ± 20%): expected if feature addition does NOT dramatically reshape trade emission rate.
- OOS trade count ∈ [140, 240] (baseline 189 ± 25%): same.
- OUTSIDE either band → trade-rate destabilization; flag for diary inspection.

**F-AXIS-MECHANISM #3 — n_eff_per_cell** (per /008 methodology substrate; LM Master §5 TIGHTENED 2026-05-27):
- Expected band: **[5, 10]** (LM Master modal at ~8). Pool Model A 2× rows raises lower floor from QR's initial 4 to LM Master's 5.
- < 5 → label-collapse; ≥ 12 → over-dispersed.

**F-AXIS-MECHANISM #4 — IC with existing features** (Critic Check 4 BINDING):
- Already pre-verified in Section 2.3: ALL 25 IC values < 0.7 threshold. POST-/023 check: re-verify with full 40-feature comparison (not just top-5) — Critic Phase 7.5 may compute full IC matrix.
- Threshold: any |IC| > 0.7 in 42-col matrix → re-evaluate; otherwise PASS.

### 4.3 Composite verdict matrix (Section 8 row format)

See Section 8.

---

## Section 5 — Predicted Verdict Priors

### 5.1 Verdict priors — LM Master Phase 4.5 RECALIBRATED (BINDING)

Per LM Master Phase 4.5 §3 (advisory `briefs-v1/iteration_v1-023/lgbm_advisor.md`), QR's initial priors 15/10/45/15/10/5 RECALIBRATED to **12/8/52/18/8/2** at Phase 4.5 closeout. The shifts: PROMISING −3pp (v3 4-point precedent dominant), PROMISING-INERT-FAV −2pp (colsample lottery on 42-col surface less likely than 40-col), **INERT +7pp** (v3/019 + /082 importance-rank evidence stronger), NEGATIVE clean +3pp (v3/023 INERT-at-higher-budget pattern at n_trials=18 mid-zone), NEGATIVE-CAT −2pp (NEW input lower CAT risk than gate per /020/022 base rate), PROMISING-METHOD −3pp (feature-family axis NOT methodology by construction).

| Verdict class | QR initial | **LM Master RECALIBRATED (BINDING)** | Rationale |
|---|---|---|---|
| **PROMISING (F1 Δ ≥ +0.10 + F-AXIS #1 PROMISING-clean)** | 15% | **12%** | Mechanism IS-anchored (ORACLE EDA +78.55%); v1 pool Model A architectural difference vs v3; downweighted by v3 4-data-point precedent |
| **PROMISING-INERT-FAVORABLE (F1 Δ ≥ +0.10 + F-AXIS #1 NOT PROMISING-clean)** | 10% | **8%** | Lift attributable to colsample noise; 42-col surface less lottery-prone than 40-col |
| **INERT (F1 Δ ∈ [-0.30, +0.10) + F-AXIS #1 INERT)** | 45% | **52% (MODAL)** | v3 4-data-point precedent dominant; INERT-by-importance most likely modal; v3/019 + /082 importance-rank evidence dominant |
| **NEGATIVE clean (F1 Δ ∈ [-0.55, -0.30))** | 15% | **18%** | v3/023 pattern at higher Optuna budget; n_trials=18 mid-zone above v3 INERT-threshold 10 + below v3/023 active-harm 35 — non-trivial risk |
| **NEGATIVE-CATASTROPHIC (F1 Δ ≤ -0.55)** | 10% | **8%** | Tail; NEW input feature lower CAT risk than gate primitives (/020/022 base rate); pool Model A still risk |
| **PROMISING-METHODOLOGY (substrate finding)** | 5% | **2%** | NEW feature family is NOT methodology axis by construction |

**Total**: 100%. **Modal: INERT at 52%** (LM Master shift +7pp vs QR initial); PROMISING tail compressed to 20% combined (was 25%). Per `feedback_iteration_quality.md` LM Master deference rule at ≥ 5pp tail-class re-weighting, QR ADOPTS LM Master priors as BINDING for Section 8 row pre-registration.

**Mass-shifting catalysts already fired** at LM Master Phase 4.5 (Section 5.2 sub-rules redundant; preserved for audit):
- LM Master §4 mandates F-AXIS #1 gain-share check; without it, /023 verdict mis-classification risk ~15pp per LM Master §9. Section 4.2 below codifies the dual gate.
- LM Master §5 n_eff band [5, 10] tightens QR's [4, 10] lower bound — Section 4.2 F-AXIS-MECHANISM #3 updated.

### 5.2 Mass-shifting catalysts (will adjust at LM Master Phase 4.5)

- If LM Master predicts importance rank for funding_z30 ≥ rank 30/42 → shift INERT mass +10pp (toward 55%).
- If LM Master notes that "pool Model A's joint loss surface gives funding a 2× training data advantage NOT available in v3" → shift PROMISING mass +5pp (toward 20%).
- If LM Master recommends a SECOND funding-family feature (e.g. funding_sign_persist_9 from v3/082) → re-scope to "funding family" not "funding single z-score"; brief revision.

---

## Section 6 — Failure Modes

### 6.1 Mode A: INERT-by-importance (modal — 45% prior)

**Pattern**: funding_rate_zscore_30 ranks bottom-quartile (38-42/42) across 4+ of 5 cohorts. F1 OOS Sharpe Δ flat (-0.30 to +0.10). Indistinguishable from baseline + 2 noise columns.

**Diagnostic**: F-AXIS-MECHANISM #1 fails. v3 pattern reproduces in v1.

**Implication for cycle-3**: funding-rate axis CLOSED for cycle-3 (re-attempt at /027 CONFIRMATION budget WOULD provide multi-seed validation but only worth running if PROMISING-INERT-PARTIAL at /023).

**Path Forward**: /024 pivots to per-cohort drawdown brake (Path Forward #2) OR open-interest delta (different feature family, sister NEW family).

### 6.2 Mode B: NEGATIVE clean / NEGATIVE-CATASTROPHIC

**Pattern**: F1 OOS Sharpe Δ ∈ [-0.55, -0.30) clean OR ≤ -0.55 catastrophic. May coincide with importance rank mid-table (15-30/42) — feature partially learned but Optuna overfits IS to noise.

**Diagnostic**: v3/023 pattern (INERT feature actively HARMS at higher Optuna budget) replicated; /023 EXPLORATION-mode budget (n_trials=18) above v3's n_trials=10 threshold but possibly still in the "feature dilutes useful colsample picks" regime.

**Implication for cycle-3**: If catastrophic, /024 becomes mandatory multi-seed HIGH-RISK iteration (3+ cycle-3 HIGH-RISK rule). If clean, axis CLOSED for cycle-3, pivot to /024 alternatives.

### 6.3 Mode C: PROMISING clean (15% prior — IS-anchored mechanism vindicated)

**Pattern**: F1 OOS Sharpe Δ ≥ +0.10 (≥ +0.7637 OOS Sharpe absolute). F-AXIS-MECHANISM #1 importance rank ≤ 14/42 on ≥ 2 cohorts. n_eff_per_cell ∈ [4, 10]. IS Sharpe Δ ≥ +0.10.

**Diagnostic**: pool Model A's joint loss surface learns funding-rate signal where v3's per-symbol models could not. The ORACLE EDA mechanism (negative funding band = short-crowded mean-reversion) instantiates at the retrained roster.

**Implication for cycle-3**: funding-rate single z-score AXIS PROMISING for /027 CONFIRMATION substrate. /024 explores funding-FAMILY variants (sign-persist, momentum, accel from v3/082 inspiration; multi-channel construction).

### 6.4 Mode D: PROMISING-INERT-FAVORABLE (10% prior)

**Pattern**: F1 OOS Sharpe Δ ≥ +0.10 BUT F-AXIS-MECHANISM #1 importance rank ≥ 15/42 — lift not attributable to feature (Optuna lottery on 42-col surface).

**Diagnostic**: same as v3/019 PROMISING-INERT pattern. Lift is real but unsignaled.

**Implication for cycle-3**: NON-COMPOUNDABLE to /027 bundle (lift not mechanism-attributable). Catalog as PROMISING-INERT-FAVORABLE; /024 advances to NEW axis family.

### 6.5 Mode E: Sample-size-too-small (n_eff < 4)

**Pattern**: Funding-z-score feature creates label-collapse — too many bars in extreme regime tail relative to label horizon. n_eff_per_cell < 4.

**Diagnostic**: extreme funding bars (|z|>2) are ~8% of total, sufficient density. Mode E is low-probability tail (< 5%).

---

## Section 7 — Pre-registered failure-mode predictions

### 7.1 LM Master Phase 4.5 will adjudicate

LM Master Phase 4.5 will produce its own verdict-class priors at `briefs-v1/iteration_v1-023/lgbm_advisor.md`. QR will adopt LM Master priors over Section 5 if LM Master Negative-tail upweighting is > 5pp (per /022 finding: LM Master tail upweighting reliably directionally correct on non-POSITIVE_EVERYWHERE priors at single-seed EXPLORATION).

### 7.2 Pre-committed verdict-mass-shifting rules

- IF LM Master predicts importance rank for funding_z30 ≥ rank 30/42 on ≥ 3 cohorts → QR adopts LM Master's INERT prior. If LM Master INERT prior is ≥ 50% → QR Section 5 INERT prior shifts to LM Master's value.
- IF LM Master predicts pool Model A architectural lever differential (z30 effective rank shifts ≥ 10 positions between Model A and per-symbol Model C/D/E) → QR maintains pre-LM 15% PROMISING prior; otherwise compresses PROMISING to 8-10%.
- IF LM Master proposes adding a SECOND funding feature beyond z30+z90 (e.g. funding_sign_persist_9) → brief revision (Section 3 + 4), pre-Phase 5.5 gate.

---

## Section 8 — MERGE/NO-MERGE Verdict Matrix

| Row | F1 OOS Sharpe Δ | F3 IS Sharpe Δ | F-AXIS #1 (rank + gain-share) | n_eff | Verdict |
|---|---|---|---|---|---|
| 1 | ≥ +0.10 | ≥ +0.10 | rank ≤ 14/42 + gain-share ≥ 4.0% on ≥ 2 cohorts | 5-10 | **PROMISING (clean)** — /027 bundle candidate |
| 2 | ≥ +0.10 | ≥ +0.10 | rank ≥ 15/42 all cohorts OR gain-share < 4.0% all cohorts | 5-10 | PROMISING-INERT-FAVORABLE — NOT bundleable, catalog only |
| 3 | ≥ +0.10 | ≥ +0.10 | rank 15-31/42 mid-table + gain-share 1.5-4.0% | 5-10 | PROMISING-INERT-PARTIAL — investigate at /024, NOT bundle |
| 4 | ≥ +0.10 | ∈ [-0.10, +0.10) | any | 5-10 | PROMISING-WEAK — sign-consistent but IS noise |
| 5 | ∈ [-0.10, +0.10) | any | rank ≥ 32/42 on ≥ 3 cohorts + gain-share < 4.0% | 5-10 | **INERT-by-importance** — v3 4-data-point precedent reproduces; axis CLOSED for cycle-3 |
| 6 | ∈ [-0.55, -0.10) | any | any | 5-10 | NEGATIVE clean — axis CLOSED |
| 7 | ≤ -0.55 | any | any | 5-10 | **NEGATIVE-CATASTROPHIC** — 3rd cycle-3 HIGH-RISK NEG-CAT → next HIGH-RISK mandatorily multi-seed |
| 8 | any | ≤ -0.30 | any | 5-10 | IS-catastrophic — reject regardless of OOS |
| 9 | any | any | any | < 5 OR ≥ 12 | n_eff degenerate — methodology issue, separate diary section |
| 10 | any | any | any (matters) | any | If F-AXIS #4 IC > 0.7 anywhere → Critic Check 4 FAIL → BLOCK |

**NO-MERGE if** Row 5, 6, 7, 8, 9, OR 10 fires. **MERGE candidate to /027 bundle if** Row 1 fires (clean PROMISING).

---

## Section 9 — Library Stack

- `pandas>=2.0` — DataFrame ops (existing)
- `numpy>=1.24` — z-score math (existing)
- No NEW external dependencies for funding-rate features.
- Funding-rate fetch CLI (`uv run crypto-trade fetch-funding`) already exists from v3/019 (`main.py:340-369`).
- Funding cache exists in `data/funding_rates/` for all 5 v1 universe symbols (verified Section 2.1).
- Existing test suite under `tests/features_v3/test_funding_v3.py` validates math; v1 module can copy test patterns (NEW `tests/features_v1/test_funding_v1.py`).

---

## Section 10 — Run Protocol

### 10.1 Pre-Phase 6 gates

- Phase 5.5 gate (Engineer): verifies brief sections 0.5/0.6/2.5/3.4 present; verifies LM Master integration; verifies cadence + axis rotation rules.
- Phase 6.0 pre-flight (Critic): mini-checks brief look-ahead (compute_funding_rate_zscore IS .shift(1)-lagged); src/ diff anti-pattern static scan; walk_forward.py:113 regression check; cadence + axis sanity.

### 10.2 Engineering dispatch parameters

- Single-seed EXPLORATION: `--seed 42`, `--n-trials 18`, `ENSEMBLE_SIZE=3`, V1_FEATURE_COLUMNS_PRUNED 42 cols.
- Universe: full V1_BASELINE_UNIVERSE (BTC, ETH, LINK, LTC, DOT). Pool Model A + single-symbol Model C/D/E.
- No HIGH-RISK multi-seed validation opt-in (per Section 2.5 — single-seed for axis isolation).

### 10.3 Kill criteria

- Wall-clock > 90 min → engineer SIGTERM the backtest; document in engineering_report.md.
- Feature pipeline failure (funding cache missing, parquet write fail) → BLOCK; no F-AXIS-MECHANISM evaluation.
- IS Sharpe Δ ≤ -0.50 mid-run (after Model A complete but before C/D/E) → engineer pause, request QR brief revision before committing C/D/E compute.

### 10.4 Engineering report — BINDING contract (4th cycle-3 incident at /022)

**Per /022 Critic FINAL Recommendation #1 (CARRY-FORWARD from /020/021) BINDING**:

> Engineering-report contract — codify NON-RETROSPECTIVE-FORGIVENESS at orchestrator dispatch level.

This brief LOAD-BEARINGLY pre-commits: **NO Phase 7.5 Critic dispatch without `reports-v1/iteration_v1-023/engineering_report.md` present**. The brief's pre-commit alone is insufficient — incident rate of 4/4 cycle-3 iterations confirms brief-level contracts cannot enforce. The orchestrator-layer fix is in scope for skill maintainer (NOT QR scope this iteration), but this brief encodes the load-bearing constraint:

**Phase 7.5 dispatch precondition**: `[ -f reports-v1/iteration_v1-023/engineering_report.md ]` MUST be true. If absent at Phase 7.5 dispatch → orchestrator MUST emit BLOCK-PENDING-FIX automatically without Critic intervention. QR will write the retrospective engineering_report.md if needed (per /022 BLOCK-PENDING-FIX precedent).

**Pre-commit content**: engineering_report.md must document:
1. Implementation summary (NEW src/crypto_trade/features_v1/funding_v1.py + V1_FEATURE_COLUMNS_PRUNED 40→42 + runner wiring)
2. Backtest configuration (single-seed=42, ENSEMBLE_SIZE=3, n_trials=18, V1_FEATURE_COLUMNS_PRUNED 42 cols, V1_BASELINE_UNIVERSE 5 sym)
3. Wall-clock + per-model timing breakdown
4. F-AXIS-MECHANISM #1-4 measurement values + thresholds
5. ALL test commands run + outputs (tests/features_v1/test_funding_v1.py)
6. Anomaly notes (if any) + reproduce command

### 10.5 Test suite additions

- `tests/features_v1/test_funding_v1.py` (NEW):
  - Verify past-only invariant (z-score at t uses ONLY rates t-30…t-1)
  - Verify alignment (kline open_time / funding_time round-to-minute correctly)
  - Verify clip (|z| ≤ 10 enforced)
  - Verify burn-in (first 30 bars NaN for z30, first 90 bars NaN for z90)
- Integration test: full feature load with V1_FEATURE_COLUMNS_PRUNED 42-col extension produces expected schema.

### 10.6 Reproduce command

```
uv run python run_baseline_v1.py \
  --pruned-features \
  --feature-add funding_v1 \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --n-trials 18 \
  --exploration \
  --seeds 1 \
  --seed 42 \
  --output-dir reports-v1/iteration_v1-023/
```

(Engineer to confirm CLI flag names against `run_baseline_v1.py:argparse` at Phase 6 dispatch.)

---

## Section 11 — Conditional Roadmap (/024+)

### 11.1 If /023 = PROMISING (clean)

**/024 priority**: funding-FAMILY expansion (multi-channel construction per v3/082 inspiration). Test funding_sign_persist_9, funding_momentum_3 as ADDITIONAL features (total 42 → 44). Brief Section 0.6 axis family `feature-family` (NEW REPEAT).

**/025**: pre-CONFIRMATION sanity (final EXPLORATION) — Layer B determinism re-verification at /027 multi-seed config; final brief Section 11.7 routing matrix verification.

**/026**: (optional flexibility slot for unexpected mechanism finding from /024).

**/027 CONFIRMATION**: bundle = pool baseline + LINK specialist + ETH+gate specialist + **funding-rate z-score family** as 3rd alpha-enhancement component. Bundle target +1.30-1.50 OOS Sharpe under multi-seed correlation drag.

### 11.2 If /023 = PROMISING-INERT-FAVORABLE

**/024 priority**: open-interest delta (different feature family, sister NEW family) — funding-rate axis is "lift without mechanism" so cannot bundle to /027; advance to fresh NEW feature family. OR pivot to per-cohort drawdown brake (Path Forward #2 from /022).

**/027 substrate UNCHANGED** vs /022 post-state (pool + LINK + ETH+gate; no /023 contribution).

### 11.3 If /023 = INERT (modal)

**/024 priority**: per-cohort drawdown brake (Path Forward #2 from /022 Critic) — family `risk-primitive`; STATEFUL → MANDATORY deadlock-impossibility proof per A8 catalog + iter-v3/054 lesson.

**/027 substrate UNCHANGED** vs /022 post-state.

### 11.4 If /023 = NEGATIVE clean

Same as 11.3. Axis CLOSED for cycle-3.

### 11.5 If /023 = NEGATIVE-CATASTROPHIC

**Mandatory multi-seed HIGH-RISK** at /024 (3rd cycle-3 HIGH-RISK NEG-CAT rule). /024 likely STILL HIGH-RISK at multi-seed (drawdown brake = risk-primitive change; open-interest = NEW feature family). Brief Section 2.5 must declare multi-seed mitigation BINDING.

### 11.6 /027 bundle composition impact (LM Master §8 ADOPT, 2026-05-27)

Per LM Master §8 advisory:

**IF /023 = PROMISING (clean)**: funding-family becomes 3rd alpha-enhancement component to /027 bundle:
- Baseline pool + LINK specialist (/018) + ETH+gate specialist (/019) ≈ Σ +1.30 OOS Sharpe nominal
- Funding-family /023 contribution **+0.20 OOS Sharpe estimate** (LM Master §8 anchor; subject to correlation drag)
- **Realistic bundle target: +1.30 to +1.50 OOS Sharpe under multi-seed correlation drag**
- **Pre-validation requirement**: cross-correlation of /023 funding-family signals with /018 LINK + /019 ETH+gate signals must be ρ < 0.40 at multi-seed pre-bundle (LM Master §8 BINDING). If ρ ≥ 0.40, funding-family is correlation-redundant → drop from /027 bundle.

**IF /023 = PROMISING-INERT-FAVORABLE or INERT or NEGATIVE clean**: /027 bundle UNCHANGED at +1.20-1.50 OOS Sharpe target (pool + LINK + ETH+gate only; no /023 contribution; correlation-drag estimate from /018 + /019 joint multi-seed).

**IF /023 = NEGATIVE-CATASTROPHIC**: /027 bundle UNCHANGED at +1.20-1.50; AND /024 mandatory multi-seed HIGH-RISK kicks in (Section 11.5).

### 11.7 LM Master /024 staging matrix (LM Master §6 ADOPT, 2026-05-27)

Per LM Master §6 verdict-conditional pre-staging:

| /023 verdict | LM Master /024 axis | Family | Mode | Justification |
|---|---|---|---|---|
| **PROMISING (clean)** | Funding-FAMILY expansion ONE AT A TIME (sign-persist, momentum) | `feature-family` (NEW REPEAT) | single-seed=42, ENSEMBLE_SIZE=3, n_trials=18 | Per `feedback_v3_engineered_features_dont_stack.md` SAME-FAMILY rule (2026-05-11 ITER-V3/052 Critic `34e7c2f`); stack 2 z-windows + 1 NEW = 3 funding-family features max; stacking experiments deferred to /027 multi-seed |
| **PROMISING-INERT-FAVORABLE** | Open-interest delta (NEW sister non-OHLCV family) | `feature-family` | single-seed=42 EXPLORATION | Funding axis is "lift without mechanism" → NOT bundleable; advance to fresh NEW feature family OR pivot to per-cohort drawdown brake |
| **INERT (modal 52%)** | Per-cohort drawdown brake | `risk-primitive` | single-seed=42 EXPLORATION; **mandatory deadlock-impossibility proof** per A8 catalog + iter-v3/054 lesson | LM Master §6 explicit; Critic /022 Path Forward #2 |
| **NEGATIVE clean (18%)** | Per-cohort drawdown brake OR open-interest delta family | `risk-primitive` OR `feature-family` | single-seed=42 EXPLORATION | LM Master §6 explicit; advance to fresh NEW family |
| **NEGATIVE-CATASTROPHIC (8%)** | Open-interest delta family at MULTI-SEED | `feature-family` | **MANDATORY multi-seed HIGH-RISK** (3rd cycle-3 NEG-CAT triggers forward mandate per Section 11.5) | LM Master §6 explicit; concurrent with 3+ cycle-3 HIGH-RISK rule |

**Decision binding**: /024 brief Section 0.6 (Architecture-Family Justification) MUST cite this matrix and the /023 verdict that triggered the row.

### 11.8 If /023 = sample-size-too-small (n_eff < 5)

Methodology issue (NOT a mechanism finding). /024 advances to /024's original menu (NOT funding-related); /023 catalogued as NEGATIVE n_eff-degenerate. Investigate label-horizon × funding-regime interaction in separate analysis. (Lower bound was 4 in QR initial; tightened to **5** per LM Master §5 + Section 4.2 F-AXIS-MECHANISM #3 update.)

### 11.9 DOT pre-classification (Critic /022 Rec mandatory before any further per-cohort axis)

Per /022 NEW memory: if /023 PROMISING or PROMISING-INERT-FAVORABLE AND /024 routes back to per-cohort axis (e.g. DOT-only specialist), DOT prior class MUST be pre-classified using the same `_classify_LTC()`-style framework. Pre-classified at /023 closeout (post-Phase 7 evaluation) for /024 readiness:

**Pre-task for /024 IF per-cohort routing returns**: DOT prior class evaluation via `analysis/iteration_v1-024/dot_prior_class.py` mirroring /022's LTC classification script. NOT in /023 scope.

---

## Section 12 — Roll-back Protocol

### 12.1 Code roll-back

- `src/crypto_trade/features_v1/funding_v1.py` is NEW module — roll-back = file deletion + V1_FEATURE_COLUMNS_PRUNED revert to 40-col list.
- Backward-compatible additive infrastructure (no breaking changes to existing V1_FEATURE_COLUMNS_PRUNED).
- The fetch-funding CLI subcommand stays (it was added at v3/019 + the cache files exist; no need to remove).

### 12.2 Data roll-back

- No data files modified (read-only access to `data/funding_rates/*.csv`).
- No kline files modified.

### 12.3 BASELINE_V1.md roll-back

- BASELINE_V1.md UNCHANGED at `v0.v1-baseline-corrected` (`f8bc12c`) regardless of /023 verdict.
- Only CONFIRMATION-MERGE updates BASELINE_V1.md (per `feedback_v3_baseline_update_policy.md` adopted by v1).
- EXPLORATION verdicts (PROMISING / NEGATIVE / INERT) do NOT update baseline.

### 12.4 Tag roll-back

- `v0.v1-023` tag applied at Phase 8 closeout regardless of verdict (catalog marker).
- BASELINE_V1.md tag UNCHANGED.

---

## Section 13 — Self-check template

Brief authoring discipline (pre-Phase 5.5 gate):

- [x] Section 0.5 Iteration Type declared (EXPLORATION cycle-3 #8 of 10)
- [x] Section 0.6 Axis-Family declared + prior 5 listed + rotation status VALID
- [x] Section 0.7 Wall-clock estimate (35-45 min)
- [x] Section 1 Hypothesis with mechanism story at basin-level (per /021 H2 REFUTATION binding)
- [x] Section 2 IS-only numerical evidence from committed analysis (analysis/iteration_v1-023/ at commit c3f4551)
- [x] Section 2.5 HIGH-RISK declaration + mitigation (single-seed OPT-IN with pre-commit)
- [x] Section 3 Proposed Changes (NEW module + V1_FEATURE_COLUMNS_PRUNED 40→42 + runner wiring)
- [x] Section 3.4 LM Master Phase 4.5 responses (8 ADOPTED, 0 REJECTED; 2026-05-27)
- [x] Section 4 Falsifiers (F1, F3 + F-AXIS-MECHANISM #1-4); F-AXIS #1 DUAL GATE rank + gain-share (LM Master §4); n_eff band [5, 10] (LM Master §5)
- [x] Section 5 Predicted verdict priors RECALIBRATED 12/8/52/18/8/2 (LM Master §3 BINDING; modal INERT 52%)
- [x] Section 6 Failure modes (A-E catalogued)
- [x] Section 7 Pre-registered failure-mode predictions + LM Master adjudication
- [x] Section 8 MERGE/NO-MERGE verdict matrix (10 rows)
- [x] Section 9 Library stack (no new deps)
- [x] Section 10 Run protocol + engineering_report BINDING contract (per /022 Critic Rec #1 CARRY-FORWARD)
- [x] Section 11 Conditional /024+ roadmap (9 sub-branches; 11.6 /027 bundle + 11.7 LM Master /024 staging matrix added)
- [x] Section 12 Roll-back protocol
- [x] Section 13 Self-check (this section)

### 13.1 v3 prior addressed head-on?

YES — Section 0.4 cites 4-data-point v3 NEGATIVE/INERT verdict catalog with per-iteration failure modes; Section 0.4 structural-difference table identifies pool Model A architecture as the v1 ↔ v3 lever; Section 5 priors set **modal INERT at 52%** (LM Master RECALIBRATED, was QR initial 45%) reflecting v3 prior dominance; Section 11.3 INERT-modal Path Forward pivots cleanly to /024 alternatives per LM Master §6 staging matrix.

### 13.2 ORACLE EDA caveat acknowledged?

YES — Section 1 caveat ADDED at LM Master §2 ADOPT (2026-05-27) downgrading ORACLE EDA +78.55% as quantitative predictor; Section 2.7 already noted descriptive validity caveat (mechanism causal not roster-specific); /022 BTC + LTC Jaccard 0.084-0.10 single-axis basin-relocation precedent cited in BOTH sections.

### 13.3 Anchor-frame BINDING locked?

YES — Section 0.3 lists portfolio comparison.csv "sharpe" semantics (daily-annualized monthly) anchor = +0.6637; all F1 predictions reference this single source. Per /022 Critic Rec #3 ELEVATED to BINDING.

### 13.4 Engineering-report contract LOAD-BEARING?

YES — Section 10.4 explicitly cites /022 Critic FINAL Rec #1 BINDING; brief encodes orchestrator-level expectation; pre-commit document content list provided.

### 13.5 LM Master Phase 4.5 integration complete?

YES — Section 3.4 populated 2026-05-27 with 8 LM Master recommendations + QR responses (all ADOPTED, 0 REJECTED). Brief Section 5 priors RECALIBRATED 15/10/45/15/10/5 → 12/8/52/18/8/2 (LM Master §3). Section 4.2 F-AXIS #1 falsifier DUAL GATE rank + gain-share (LM Master §4 CRITICAL). Section 4.2 F-AXIS-MECHANISM #3 n_eff band [5, 10] (LM Master §5). Section 1 ORACLE EDA caveat (LM Master §2). Section 11.6 /027 bundle composition (LM Master §8). Section 11.7 LM Master /024 staging matrix (LM Master §6). Per-cohort gain-share data mandated as Critic Phase 7.5 watch item (LM Master §4 final point). Phase 5.5 gate "brief must address each LM Master recommendation" SATISFIED.

---

**Brief authored by QR Phase 5 at iter-v1/023 startup. Section 3.4 amended 2026-05-27 with LM Master Phase 4.5 responses (all 8 ADOPTED). Anchor: `v0.v1-baseline-corrected` (`f8bc12c`). Cycle-3 EXPLORATION #8/10. Axis family `feature-family` (NEW; 3-way CONVERGENT routing). HIGH-RISK declared single-seed mitigation. Modal predicted verdict: INERT (LM Master RECALIBRATED to 52%) per v3 4-data-point precedent dominance.**

**Next phase**: Phase 5.5 Engineer gate → Phase 6 implementation + backtest.
