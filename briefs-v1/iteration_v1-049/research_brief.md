# Iteration v1-049 — Research Brief

## Section 0.0 — Banner

- **Track**: v1 (refactored)
- **Iteration**: iter-v1/049
- **Type**: `EXPLORATION` (cycle-6 EXPLORATION 4/10)
- **Axis family**: `feature-family` (NON-KLINE-CLASS defense post-/048 NEG-CLEAN-PRE-EDA at |IC|=0.9063 vs `vol_volume_rel_20`)
- **Axis varied**: ADD `long_short_zscore_30` (rolling 30-bar z-score of `sum_toptrader_long_short_ratio`, an account-level positioning sentiment primitive ALREADY FETCHED at 8h cadence into `data/open_interest/<SYMBOL>/8h.csv` by `fetch-oi`) to `V1_FEATURE_COLUMNS_PRUNED` (44 → 45)
- **Anchor**: BASELINE_V1 (commit `f8bc12c`); IS daily Sharpe **+0.4767** / OOS daily Sharpe **+1.1913**
- **Prior verdict context**: /046 PROMISING-DIVERGENCE (methodology axis); /047 NEG-CLEAN-PRE-EDA — `skew_zscore_21` ABORTED pre-launch at F5 |IC|=0.81 vs `stat_skew_20` (algebraic-sister); /048 NEG-CLEAN-PRE-EDA — `trade_count_zscore_30` ABORTED pre-launch at F5' |IC|=0.9063 vs `vol_volume_rel_20` (empirical co-movement — number_of_trades is empirically tied to the volume cluster). /049 escalates the defense from "UNUSED kline primitive" to **non-kline data class entirely** — top-trader long/short account ratio is positioning sentiment via account-level census, NOT derivable from OHLCV/funding/OI numerically.
- **Mode**: EXPLORATION budget (n_trials=18, --seeds 1, ENSEMBLE_SIZE=3; wall-clock cap ≤ 2.5h)

**KEY DATA INFRASTRUCTURE FINDING (load-bearing)**: the `fetch-oi` subcommand introduced at iter-v3/093 ALREADY FETCHES `count_toptrader_long_short_ratio` AND `sum_toptrader_long_short_ratio` at native 8h granularity into `data/open_interest/<SYMBOL>/8h.csv` (schema confirmed: `open_time, sum_open_interest, sum_open_interest_value, count_toptrader_long_short_ratio, sum_toptrader_long_short_ratio, count_long_short_ratio, sum_taker_long_short_vol_ratio`). The data is FETCHED, CACHED, and UNUSED by any existing v1/v2/v3 feature module — verified by `grep -rn "long_short\|topLong" src/crypto_trade/features_v1/ src/crypto_trade/features/` returning empty. **No new fetcher, no new CLI subcommand, no new historical-depth probe needed.** The brief reduces to a feature-only addition (dispatch module + V1_FEATURE_COLUMNS_PRUNED insert + tests). This finding supersedes the pre-brief outline's §6 (fetcher requirements), §7 (depth verification), §10 (backup axis), and §11's fetcher/download budget items.

---

## Section 0 — Data Split Declaration

- `OOS_CUTOFF_MS = 1742774400000` (2025-03-24 UTC) — **IMMUTABLE** (`src/crypto_trade/config.py`).
- `training_months = 24` — **IMMUTABLE**.
- IS window: data start ... 2025-03-24 (strictly less-than `OOS_CUTOFF_MS`).
- OOS window: 2025-03-24 ... data end. Forensic only at /049 (EXPLORATION budget).
- Symbol universe: `V1_BASELINE_UNIVERSE = (BTC, ETH, LINK, LTC, DOT)`. Unchanged.
- All Phase 5 EDA in this brief uses **IS-only** data, sliced via the `open_time < OOS_CUTOFF_MS` predicate against per-symbol parquet files in `/home/roberto/crypto-trade/.worktrees/quant-research/data/`. Phase 6 backtest sees IS for training/Optuna and OOS for forensic comparison only.

---

## Section 0.5 — Iteration Type Declaration + Cadence

- **Type**: EXPLORATION (NOT CONFIRMATION).
- **Cycle slot**: cycle-6 EXPLORATION **4/10**. /046 was 1/10 (methodology axis PROMISING-DIVERGENCE), /047 was 2/10 (feature-family ABORT-PRE-EDA at F5 algebraic-sister), /048 was 3/10 (feature-family ABORT-PRE-EDA at F5' empirical-correlation).
- **Cadence**: v1 EXPLORATION default `n_trials=18`, `--seeds 1`, `ENSEMBLE_SIZE=3`, wall-clock cap **2h** (HARD); total iteration budget incl. EDA + closeout **≤ 2.5h**.
- **Cadence rule**: `briefs-v1/exploration_catalog.md` row appended at closeout; CONFIRMATION-bundling decision deferred to /050+ pending /049 outcome.
- **Recent cycle-6 + late-cycle-5 cadence** (last 5):
  - iter-v1/048 (2026-06-01): feature-family axis (`trade_count_zscore_30`) — NEG-CLEAN-PRE-EDA (F5' ABORT at |IC|=0.9063)
  - iter-v1/047 (2026-06-01): feature-family axis (`skew_zscore_21`) — NEG-CLEAN-PRE-EDA (F5 ABORT at |IC|=0.8132)
  - iter-v1/046 (2026-06-01): methodology axis (IS-only re-solve) — PROMISING-DIVERGENCE
  - iter-v1/045 (2026-06-01): bundle-substrate axis (CONFIRMATION-MERGE-PORTFOLIO ALT_1) — BLOCK-FINAL
  - iter-v1/043 (2026-05-31): per-cohort-specialization × labeling (LINK trend-scan)
- /047 + /048's ABORT-PRE-EDAs count toward the cycle-budget (slots 2/10 + 3/10) but provide **no feature-content overlap** with /049's positioning-sentiment primitive — /049 is a third feature-family attempt with a structurally NEW data class.
- **Three-consecutive-feature-family-axis discipline**: if /049 ABORTs or NEG-CLEAN, /050 MUST rotate to a different family per axis-rotation discipline (model-arch, labeling, or risk-primitive). Three consecutive feature-family attempts of cycle-6 mark the family saturated at v1's current scope.

---

## Section 0.6 — Architecture-Family Justification (v1-only Axis Rotation Discipline)

| Iter | Date | Axis family |
|---|---|---|
| iter-v1/043 | 2026-05-31 | per-cohort-specialization × labeling |
| iter-v1/045 | 2026-06-01 | bundle-substrate |
| iter-v1/046 | 2026-06-01 | methodology |
| iter-v1/047 | 2026-06-01 | feature-family |
| iter-v1/048 | 2026-06-01 | feature-family |

- **Axis family this iter**: `feature-family`
- **Rotation status**: **VALID with constraint** — although /047 + /048 are also `feature-family`, both ABORTED at F5/F5' PRE-EDA with **zero backtest compute spent** and **zero feature-content overlap** with the /049 primitive. The pre-EDA-ABORT classification means no Optuna signal was generated from /047 or /048 to inform /049. The prior 3 families (per-cohort × labeling, bundle-substrate, methodology) span 3 distinct families; together with /047 + /048's content-null feature-family slots, rotation is intact for /049 — BUT cycle-6 will have spent 3 of 10 slots on feature-family axis ABORT-eligible work. **Constraint registered**: if /049 also routes to NEG-CLEAN-PRE-EDA or NEG-CLEAN, /050 MUST rotate to a structurally different axis family. Three consecutive feature-family NEG verdicts mark the family saturated at v1's current single-seed EXPLORATION budget — this is the cycle-6 mandate.
- **One-sentence rationale**: /047 NEG-CLEAN-PRE-EDA demonstrated transforms of already-used primitives risk algebraic-sister collisions (skew_zscore_21 vs stat_skew_20 at |IC|=0.81); /048 NEG-CLEAN-PRE-EDA demonstrated even an UNUSED kline primitive (number_of_trades) is empirically tied to the volume cluster (|IC|=0.9063 vs vol_volume_rel_20); /049 escalates to a **non-kline data class entirely** — `sum_toptrader_long_short_ratio` from `topLongShortPositionRatio` (top-trader notional positioning aggregation) is structurally orthogonal to OHLCV/funding/OI by primitive class, since it is computed by the exchange from per-account net position direction aggregation — completely independent of price/volume/range/funding/OI numerics.
- **What this is NOT**: not a SWAP (additive 44 → 45; if F1 fails, the feature retires to `V1_RETIRED_FEATURE_COLUMNS`); not a novel composition operator; not an off-the-shelf indicator; not requiring new data infrastructure (data already cached at 8h cadence in `data/open_interest/<SYMBOL>/8h.csv`).

---

## Section 1 — Hypothesis

A scale-invariant **top-trader long/short positioning z-score over a 30-bar (10-day) window** — `long_short_zscore_30` — derived from `sum_toptrader_long_short_ratio` (an account-NOTIONAL positioning sentiment primitive already cached at 8h cadence in `data/open_interest/<SYMBOL>/8h.csv`, untouched by any existing v1 feature module), captures POSITIONING SENTIMENT REGIME SHIFTS (top-trader bullish→bearish transitions, capitulation extremes, contrarian fade signals) STRUCTURALLY ORTHOGONAL to the V1_FEATURE_COLUMNS_PRUNED 44-feature space (all 44 functions of {OHLCV, funding_rate, open_interest, calendar}), and produces both (a) **top-15 importance at the portfolio-aggregated level** AND (b) **IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767** (i.e., observed IS daily Sharpe ≥ +0.5267).

**Implicit prediction**: F1 PASS prior ~13-17% (per LM Master Phase 4.5 conjunction estimate adjusted for the available-primitive — `sum_toptrader_long_short_ratio` not `topLongShortAccountRatio`); F1 FAIL prior ~83-87%; the modal outcome is **NEGATIVE-no-effect at ~35% prior** (LM Master). The hypothesis is genuinely uncertain — positioning sentiment is structurally orthogonal at the primitive level (account-aggregated NOTIONAL is genuinely a different data class from OHLCV/funding/OI/calendar) but may correlate empirically with funding_rate_zscore at modest magnitude given both encode "leveraged sentiment" — F5' IC sweep is the empirical arbiter.

---

## Section 2 — IS-Only Numerical Evidence

Phase 5 EDA produces 7 committed artifacts in `analysis/iteration_v1-049/`. Pre-launch F4 (ADF stationarity) and F5' (IC orthogonality — **TIGHTENED**, third consecutive codification: < 0.30 IDEAL / [0.30, 0.60) DOCUMENT / ≥ 0.60 ABORT) gates evaluated from these.

### 2.1 — Feature definition (verbatim, IS-only computation)

```python
# Per-symbol; computed independently for each of BTC/ETH/LINK/LTC/DOT.
# Inputs: df has column ['long_short_ratio'] (joined from data/open_interest/<SYMBOL>/8h.csv,
# column sum_toptrader_long_short_ratio, native 8h cadence, NO aggregation needed).
# Output: df['long_short_zscore_30']
lsr = df["long_short_ratio"].astype(float)
lsr_mean_30 = lsr.rolling(window=30, min_periods=30).mean()
lsr_std_30 = lsr.rolling(window=30, min_periods=30).std()
df["long_short_zscore_30"] = (lsr - lsr_mean_30) / lsr_std_30
```

**Past-only invariant**: `lsr[t]` at time t uses only the closed 8h bar at t (since `sum_toptrader_long_short_ratio` is the exchange snapshot AS OF that 8h close, already published before the next 8h bar opens); `lsr_mean_30[t]` and `lsr_std_30[t]` use the 30 closed bars ending at t inclusive (t-29 ... t). Decision at candle `t+1` uses `long_short_zscore_30[t]`. **No look-ahead** — verified by `tests/test_iteration_v1_049.py::test_past_only`.

**Warmup**: first 29 candles per symbol are NaN (min_periods=30). At 8h cadence ≈ 10 calendar days. All v1 symbols have ≥ 1.5 years of OI history (BTCUSDT 2020-09 onward per `data/open_interest/BTCUSDT/8h.csv` first row `1598918400000` = 2020-09-01); warmup is the only NaN region within the IS-available envelope.

**Scale-invariance by construction**: z-score normalization removes the unit; output is dimensionless. Magnitudes are bounded approximately to [-3, +3] under near-Gaussian assumptions; regime-shift bursts can exceed (Section 2.4 distribution_stats per symbol quantifies).

**Window-choice anchor**: 30-bar (10-day at 8h) parallels `funding_rate_zscore_30` / `oi_delta_30_z90` window conventions in V1_FEATURE_COLUMNS_PRUNED — same primary-window cadence for cross-feature timescale consistency. (Window-convention parallel ONLY — those two features use funding_rate and open_interest primitives respectively, neither of which is the top-trader long/short ratio. **No algebraic-sister concern by construction.**)

**LM Master Rec 2 forensic-only window context**: brief deliverables Section 9 add `long_short_zscore_14` (5-day, retail-burst timescale) and `long_short_zscore_60` (20-day, macro positioning timescale) to `ic_orthogonality_full_44.csv` as forensic rows ONLY — they are NOT in V1_FEATURE_COLUMNS_PRUNED and NOT in V1_FEATURE_COLUMNS. Purpose: cycle-7 follow-on telemetry if /049 PROMISING. Adds < 5 min to pre-EDA compute.

### 2.2 — Data-availability per symbol (pre-EDA, replaces outline §7 historical depth probe)

The OI cache file `data/open_interest/<SYMBOL>/8h.csv` is the data source; `sum_toptrader_long_short_ratio` is column-4. Per-symbol availability is determined by the `fetch-oi` cache extent — already populated for v1's 5-cohort universe per prior iterations using OI features.

Pre-launch artifact (Section 9 deliverable): `analysis/iteration_v1-049/long_short_availability_per_symbol.csv`. Schema: `symbol, earliest_ts_ms, earliest_date_utc, latest_ts_ms, latest_date_utc, n_records, n_nan_after_warmup, scenario_label`.

Expected outcomes (anchored to OI cache extent + Binance OI-archive launch date):

| symbol | earliest_date (expected) | latest_date | scenario |
|---|---|---|---|
| BTCUSDT | 2020-09-01 | data extent end | S1: full IS coverage from 2020-09 (~4.5 years pre-OOS_CUTOFF) |
| ETHUSDT | 2020-09-01 | data extent end | S1 |
| LINKUSDT | 2020-09-01 (or later) | data extent end | S1 or S2 (per-symbol verification) |
| LTCUSDT | 2020-09-01 (or later) | data extent end | S1 or S2 |
| DOTUSDT | 2020-10-01 (DOT listing) | data extent end | S1 or S2 |

**Decision rule per outline §7 scenarios** (carried over with relaxed labels since data is cached, not fetched):
- **S1 — Full IS coverage** (earliest ≤ 2021-03-24): proceed; standard /049 flow.
- **S2 — Partial IS coverage** (12-36 months pre-OOS_CUTOFF): proceed with DOCUMENTATION in `comparison.csv` and per-cohort availability-restricted IS Sharpe reporting. LightGBM handles NaN via histogram-binning (routes to dominant child); skip-month logic in the runner already manages high-NaN months.
- **S3 — Insufficient coverage** (< 12 months pre-OOS_CUTOFF for any symbol): per LM Master Phase 4.5 risk-flag 5, pivot to S3 backup axis `funding_rate_momentum_30 = fr - fr.shift(30)`. Brief re-anchored with full F5'-fresh evaluation.

Given the OI cache start date is `2020-09-01` for BTC/ETH (~4.5 years pre-OOS_CUTOFF), and assuming similar extent for LINK/LTC/DOT (verified at Phase 5 EDA), the expected scenario is **S1** for all 5 symbols. The pre-EDA artifact `long_short_availability_per_symbol.csv` is the explicit decision input.

### 2.3 — `analysis/iteration_v1-049/adf_stationarity_per_symbol.csv` (F4 input)

Pre-EDA estimate (refined post-EDA before Phase 6 launch). Schema: `symbol, n_obs, adf_stat, adf_pvalue, lag_used, pass_at_005`.

Expected outcomes (anchored to the bounded-CLT properties of a z-normalized account-ratio series + V1_FEATURE_COLUMNS_PRUNED stationarity-invariant pattern):

| symbol | n_obs (IS) | adf_stat (expected) | adf_pvalue (expected) | pass @ 0.05 |
|---|---:|---:|---:|---|
| BTCUSDT | ~3000 (from 2020-09) | ≈ -15 to -25 | < 1e-15 | PASS |
| ETHUSDT | ~3000 | ≈ -15 to -25 | < 1e-15 | PASS |
| LINKUSDT | ~2800-3000 | ≈ -15 to -25 | < 1e-15 | PASS |
| LTCUSDT | ~2800-3000 | ≈ -15 to -25 | < 1e-15 | PASS |
| DOTUSDT | ~2700-2900 | ≈ -15 to -25 | < 1e-15 | PASS |

Rationale: a 30-bar rolling z-score of a strictly-positive ratio series has near-perfect local stationarity by construction. Local normalization absorbs cycle-scale drift (halving + ETF + macro non-stationarity is >> 10 days). The only source of non-stationarity would be a structural break in `sum_toptrader_long_short_ratio` aggregation methodology — none documented in Binance OI API changelogs in the IS window. **Expected 5/5 PASS** — F4 invariant preserved.

### 2.4 — `analysis/iteration_v1-049/distribution_stats_per_symbol.csv`

Schema: `symbol, mean, std, skew, kurtosis, p05, p25, p50, p75, p95`. Empirical confirmation of z-score normalization (target mean ≈ 0, std ≈ 1).

| symbol | mean (expected) | std (expected) | skew (expected) | kurtosis (expected) | p05 (expected) | p95 (expected) |
|---|---:|---:|---:|---:|---:|---:|
| BTCUSDT | ≈ 0.00 | ≈ 1.00 | ≈ +0.2 to +0.8 | ≈ 1 to 3 | ≈ -1.6 | ≈ +1.7 |
| ETHUSDT | ≈ 0.00 | ≈ 1.00 | ≈ +0.3 to +0.9 | ≈ 1 to 3 | ≈ -1.5 | ≈ +1.8 |
| LINKUSDT | ≈ 0.00 | ≈ 1.00 | ≈ +0.4 to +1.0 | ≈ 1 to 4 | ≈ -1.5 | ≈ +1.9 |
| LTCUSDT | ≈ 0.00 | ≈ 1.00 | ≈ +0.4 to +1.0 | ≈ 1 to 4 | ≈ -1.5 | ≈ +1.9 |
| DOTUSDT | ≈ 0.00 | ≈ 1.00 | ≈ +0.5 to +1.2 | ≈ 1 to 4 | ≈ -1.4 | ≈ +2.0 |

Positive-skew expectation: top-trader positioning ratios exhibit right-skew during euphoria phases (sudden long-stacking by top accounts during rally extensions) and left-skew compression during liquidation cascades (rapid net-short flip). The 30-bar window captures within-regime variance but not the regime mean drift; tails are expected modest, not extreme.

Deviation > 0.1 from mean=0 or > 0.15 from std=1 → INVESTIGATE. Deviation > 0.2 → ABORT pre-launch.

### 2.5 — `analysis/iteration_v1-049/ic_orthogonality_sentiment_class.csv` (F5' input — special-attention pairs)

Pre-EDA pairwise Pearson IC (lag-0, pooled across 5 symbols, sample-weighted by per-symbol IS row count). The 8 highest-conjectured-correlation existing features (sentiment-class + leverage-flow proxies):

| existing feature | family | LM Master predicted |IC| | F5' band classification |
|---|---|---:|---|
| `funding_rate_zscore_30` | funding (sentiment proxy: notional imbalance + perp arb) | **0.28** | IDEAL/DOCUMENT borderline |
| `funding_rate_zscore_90` | funding (longer horizon) | 0.22 | IDEAL |
| `oi_delta_30_z90` | leverage-flow z-score | 0.10-0.25 | IDEAL |
| `cross_btc_ret_5` | BTC short-cadence return | 0.18 | IDEAL |
| `cross_btc_ret_20` | BTC mid-cadence return | 0.18 | IDEAL |
| `mom_rsi_14` | momentum oscillator (overbought/oversold) | 0.10-0.25 | IDEAL |
| `mr_pct_from_high_20` | mean-reversion extreme | 0.10-0.20 | IDEAL |
| `vol_taker_buy_ratio` | taker-flow ratio | 0.10-0.20 | IDEAL |

**Critical pair**: `funding_rate_zscore_30` is the closest empirical correlate per LM Master Phase 4.5 prediction (both encode "leveraged sentiment" but mechanically distinct: funding moves with NOTIONAL imbalance + perp arb activity; account-ratio moves with COUNT × per-account NOTIONAL of top traders). Point estimate **|IC| = 0.28**; 80% band **[0.18, 0.42]**. This sits at the **F5' IDEAL/DOCUMENT borderline**. Pre-EDA F5' IC sweep against the full 44 features is the load-bearing diagnostic.

### 2.6 — `analysis/iteration_v1-049/ic_orthogonality_full_44.csv` (F5' input — full sweep)

44 rows; one per V1_FEATURE_COLUMNS_PRUNED feature. The **max |IC| over all 44 rows** is the F5' gate input.

Expected: max |IC| ∈ [0.18, 0.42] vs `funding_rate_zscore_30` (LM modal); second-highest |IC| ≈ 0.22 vs `funding_rate_zscore_90`; all remaining 42 pairs |IC| < 0.30.

**Hard-zero correlation candidates by construction**: cal_dow_norm, cal_hour_norm (no positioning content); interact_* features (functions of bar-internal OHLCV+volume — different primitive class).

**LM Master Rec 2 forensic-only addition**: 2 extra rows for `long_short_zscore_14` and `long_short_zscore_60` IC vs `long_short_zscore_30` (NOT against V1_FEATURE_COLUMNS_PRUNED — they are forensic-only sister-window variants for cycle-7 telemetry if /049 PROMISING; carries no /049 verdict weight).

### 2.7 — `analysis/iteration_v1-049/f4_f5_gate_outcomes.md` (PASS/FAIL documentation)

Single markdown file with quoted critical values + decision:

- **F4 decision**: PASS / INVESTIGATE / ABORT based on the 5-row ADF outcomes.
- **F5' decision**: PASS (max |IC| < 0.30) / DOCUMENT (max |IC| ∈ [0.30, 0.60)) / **ABORT-PRE-LAUNCH (max |IC| ≥ 0.60)**.
- **Quoted critical values**: max |IC| numeric value + identifying feature; ADF p-value per symbol.
- **Routing**: PASS/DOCUMENT → proceed to Phase 6; ABORT → /049 closes as NEG-CLEAN-PRE-EDA, /050 brief opens with axis-family rotation (NOT another feature-family — three-consecutive-feature-family ABORT/NEG saturation rule).

### 2.8 — Verifier-source IS-window assertion

```python
# All Section 2 EDA scripts include this assertion before any compute:
from crypto_trade.config import OOS_CUTOFF_MS
df_is = df[df["open_time"] < OOS_CUTOFF_MS].copy()
assert df_is["open_time"].max() < OOS_CUTOFF_MS, "IS-window violation"
# Scripts pass --is-only and refuse to read out_of_sample/ paths
```

No OOS data touched. Section 9 lists the 7 deliverables verbatim.

---

## Section 2.5 — HIGH-RISK Axis Declaration (v1-only)

**Declaration**: **NORMAL-RISK**.

**Reason**: This is a feature-ADDITION iteration. The Optuna training objective (`sharpe`) is UNCHANGED. The training window (24 months) is UNCHANGED. The symbol universe (5-cohort BTC/ETH/LINK/LTC/DOT) is UNCHANGED. The model architecture (4-model LightGBM ensemble, A/C/D/E) is UNCHANGED. Only the `feature_columns` argument expands from 44 → 45. The HIGH-RISK criterion (axis changes Optuna's training-objective domain) explicitly enumerates feature-set REPLACEMENT, not feature ADDITION. Feature addition does not change Optuna's objective; it expands its input space by 1 dimension.

**Mitigation (NORMAL-RISK; informational)**: F4 ADF + F5' IC (TIGHTENED, third consecutive codification: <0.30/[0.30,0.60)/≥0.60) pre-launch gates protect against pathological additions (non-stationary feature OR high-IC duplicate). If F4 or F5' hard-fails pre-launch, the brief is REVISED before Phase 6 dispatch — no backtest runs on a feature that violates the V1_FEATURE_COLUMNS_PRUNED stationarity-or-orthogonality invariants. The /047 + /048 NEG-CLEAN-PRE-EDA precedents demonstrate this gate works (F5/F5' fired pre-launch on skew_zscore_21 + trade_count_zscore_30).

**Multi-seed disposition**: single-seed (--seeds 1) per EXPLORATION default. If /049 PROMISING, /050 multi-seed-validates. The single-seed under-reading risk flagged by LM Master Phase 4.5 Rec 1 secondary (importance rank ~10-15 ranks below true value at EXPLORATION budget IF |IC| with `funding_rate_zscore_30` ∈ [0.30, 0.50]) is documented in Section 7 priors but does NOT escalate to HIGH-RISK — /049 is feature-ADDITION not feature-REPLACEMENT.

---

## Section 3 — Proposed Changes

**Key infrastructure finding**: the `fetch-oi` subcommand (introduced at iter-v3/093) already fetches `sum_toptrader_long_short_ratio` at native 8h cadence into `data/open_interest/<SYMBOL>/8h.csv`. **No new fetcher, no new CLI subcommand, no new 4h→8h aggregation logic, no new historical-depth probe are required.** The brief reduces to a feature-only addition.

### 3.1 — `src/crypto_trade/features_v1/positioning_v1.py` (NEW module)

**New file**: `/home/roberto/crypto-trade/.worktrees/quant-research/src/crypto_trade/features_v1/positioning_v1.py`

Mirrors the v1 track-isolation pattern established by `funding_v1.py`, `open_interest_v1.py`, `basis_v1.py`, `composed_v1.py`, `statistical_v1.py`, `microstructure_v1.py` (the last one retired-but-kept-on-disk after /048). Houses the top-trader positioning z-score independently — keeps it semantically separate from the open-interest delta family (which lives in `open_interest_v1.py` using `sum_open_interest`, NOT `sum_toptrader_long_short_ratio`).

Exports (skeleton — full implementation at Phase 6 Engineering dispatch):

```python
# src/crypto_trade/features_v1/positioning_v1.py

"""v1 top-trader positioning-sentiment features — iter-v1/049 (feature-family EXPLORATION cycle-6 4/10).

Track-isolated: ZERO imports from crypto_trade.features_v2 or crypto_trade.features_v3.

Feature exported:
  - ``long_short_zscore_30``: rolling-30bar z-score of ``sum_toptrader_long_short_ratio``.

NON-KLINE-CLASS defense: ``sum_toptrader_long_short_ratio`` is a top-trader account-NOTIONAL
positioning aggregation primitive computed by the exchange from per-account net position
direction. Structurally orthogonal to {OHLCV, funding_rate, open_interest, calendar}
primitive classes spanned by V1_FEATURE_COLUMNS_PRUNED's 44 features. Defends against the
/047 NEG-CLEAN-PRE-EDA algebraic-sister failure mode (|IC|=0.81 vs stat_skew_20) AND the
/048 NEG-CLEAN-PRE-EDA empirical-co-movement failure mode (|IC|=0.91 vs vol_volume_rel_20).

Data source:
    ``data/open_interest/<SYMBOL>/8h.csv`` — column ``sum_toptrader_long_short_ratio``,
    native 8h cadence, populated by ``uv run crypto-trade fetch-oi --symbols ... --intervals 8h``.

Past-only discipline verified by tests/test_iteration_v1_049.py::test_past_only.
ADF stationarity per-symbol verified by Section 2.3 EDA artifact.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

LSR_ZSCORE_WINDOW: int = 30  # 10-day window at 8h cadence
LSR_ZSCORE_CLIP: float = 10.0  # safety clip (mirrors open_interest_v1 convention)

_DEFAULT_DATA_DIR: Path = Path("data")


def compute_long_short_zscore(
    lsr_series: pd.Series, window: int = LSR_ZSCORE_WINDOW, zscore_clip: float = LSR_ZSCORE_CLIP
) -> pd.Series:
    """Compute past-only rolling 30-bar z-score from raw long/short-ratio series.

    Past-only: at bar t, the mean/std use bars (t-29 ... t-1) NOT bar t itself
    (via shift(1) before rolling stats). Decision at t+1 consumes z[t].
    """
    s = lsr_series.astype(float)
    s_shifted = s.shift(1)
    rmean = s_shifted.rolling(window=window, min_periods=window).mean()
    rstd = s_shifted.rolling(window=window, min_periods=window).std(ddof=1)
    zscore = (s - rmean) / rstd.replace(0, np.nan)
    return zscore.clip(-zscore_clip, zscore_clip)


def add_positioning_v1_features(
    df: pd.DataFrame, data_dir: Path | str = _DEFAULT_DATA_DIR, window: int = LSR_ZSCORE_WINDOW
) -> pd.DataFrame:
    """Load cached OI long/short-ratio for df's symbol and add long_short_zscore_30 column.

    Mirrors open_interest_v1.add_oi_delta_v1_features merge-key pattern:
        - df must contain 'symbol' and 'open_time' (ms int) columns
        - Reads data_dir/open_interest/<SYMBOL>/8h.csv (column sum_toptrader_long_short_ratio)
        - LEFT MERGE on _lsr_merge_key (int64 of open_time); drop merge key after
        - NEVER silently fills NaN (raises FileNotFoundError per /024 dispatch-defect lesson)
    """
    data_dir = Path(data_dir)
    if "symbol" not in df.columns:
        raise KeyError("df must contain a 'symbol' column for positioning_v1 feature group.")
    symbol = df["symbol"].iloc[0]
    lsr_path = data_dir / "open_interest" / symbol / "8h.csv"
    if not lsr_path.exists():
        raise FileNotFoundError(
            f"OI cache not found: {lsr_path}. "
            f"Run: uv run crypto-trade fetch-oi --symbols {symbol} --intervals 8h"
        )
    oi_df = pd.read_csv(lsr_path)
    if len(oi_df) == 0:
        df = df.copy()
        df["long_short_zscore_30"] = np.nan
        return df

    # Merge OI long-short-ratio into kline frame on open_time (mirrors open_interest_v1)
    df = df.copy()
    df["_lsr_merge_key"] = df["open_time"].astype("int64")
    lsr_df = oi_df[["open_time", "sum_toptrader_long_short_ratio"]].copy()
    lsr_df["_lsr_merge_key"] = lsr_df["open_time"].astype("int64")
    merged = df.merge(
        lsr_df[["_lsr_merge_key", "sum_toptrader_long_short_ratio"]],
        on="_lsr_merge_key",
        how="left",
    ).drop(columns=["_lsr_merge_key"])
    merged.index = df.index
    df = df.drop(columns=["_lsr_merge_key"])
    df["long_short_ratio"] = merged["sum_toptrader_long_short_ratio"]

    df["long_short_zscore_30"] = compute_long_short_zscore(
        df["long_short_ratio"], window=window
    )
    # Drop the intermediate ratio column to avoid polluting V1_FEATURE_COLUMNS
    df = df.drop(columns=["long_short_ratio"])
    return df


__all__ = [
    "LSR_ZSCORE_WINDOW",
    "LSR_ZSCORE_CLIP",
    "compute_long_short_zscore",
    "add_positioning_v1_features",
]
```

### 3.2 — `src/crypto_trade/features_v1/__init__.py` (modify)

**File**: `/home/roberto/crypto-trade/.worktrees/quant-research/src/crypto_trade/features_v1/__init__.py`

Changes:

1. **ADD** `long_short_zscore_30` to `V1_FEATURE_COLUMNS_PRUNED`. Alphabetical insertion places it between `interact_stoch_x_adx` (ends "...adx") and `mom_macd_hist_12_26_9` (begins "mom..."):

```python
    "interact_stoch_x_adx",
    "long_short_zscore_30",  # iter-v1/049: NEW — rolling z-score of sum_toptrader_long_short_ratio (NON-KLINE-CLASS top-trader positioning sentiment)
    "mom_macd_hist_12_26_9",
```

2. **UPDATE** the count assertion + comment:

```python
# iter-v1/049: extended 44 → 45 by adding long_short_zscore_30 (rolling-30bar
#              z-score of sum_toptrader_long_short_ratio from data/open_interest/
#              <SYMBOL>/8h.csv; NON-KLINE-CLASS top-trader positioning sentiment
#              defense post-/048 NEG-CLEAN-PRE-EDA; cycle-6 feature-family
#              EXPLORATION 4/10).
assert len(V1_FEATURE_COLUMNS_PRUNED) == 45, (
    f"V1_FEATURE_COLUMNS_PRUNED must have exactly 45 features; got {len(V1_FEATURE_COLUMNS_PRUNED)}"
)
```

3. **V1_FEATURE_COLUMNS** (193-col superset): UNCHANGED — `long_short_zscore_30` lives in the parquet via the new `positioning_v1` group registry but is NOT in V1_FEATURE_COLUMNS (which mirrors legacy `BASELINE_FEATURE_COLUMNS`). The runner pins `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)`.

4. **V1_OOD_FEATURE_COLUMNS**: UNCHANGED. Adding the new feature to the Mahalanobis subset would be a second axis change in the same iteration — deferred to /050+ if /049 PROMISING.

### 3.3 — `src/crypto_trade/features/__init__.py` (modify; new group registration)

**File**: `/home/roberto/crypto-trade/.worktrees/quant-research/src/crypto_trade/features/__init__.py`

Register the new `positioning_v1` group (mirrors `funding_v1` / `open_interest_v1` / `basis_v1` / `composed_v1` / `statistical_v1` patterns):

```python
# After existing _register calls:
from crypto_trade.features_v1.positioning_v1 import (  # noqa: E402
    add_positioning_v1_features as _add_positioning_v1_features,
)
_register("positioning_v1", _add_positioning_v1_features)  # iter-v1/049
```

### 3.4 — Fetcher path declaration (LOAD-BEARING SPECIFICATION)

**Fetcher**: NO new fetcher module. The existing `_cmd_fetch_oi` in `src/crypto_trade/main.py:1406` (subcommand `fetch-oi`, introduced at iter-v3/093) already populates the `sum_toptrader_long_short_ratio` column at 8h granularity in `data/open_interest/<SYMBOL>/8h.csv`.

**Data extent verification command** (NOT a fetcher invocation — verification only):

```bash
# Verify cache extent for all 5 v1 symbols (one-time pre-EDA probe):
for SYM in BTCUSDT ETHUSDT LINKUSDT LTCUSDT DOTUSDT; do
    echo "=== $SYM ==="
    head -2 "data/open_interest/$SYM/8h.csv"
    tail -1 "data/open_interest/$SYM/8h.csv"
    wc -l "data/open_interest/$SYM/8h.csv"
done
```

**Top-up fetch command** (if Phase 5 verification finds the cache is stale beyond the latest 8h boundary):

```bash
uv run crypto-trade fetch-oi \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --intervals 8h
```

Incremental: re-running appends only new rows. Idempotent.

**Feature module**: `src/crypto_trade/features_v1/positioning_v1.py` (per Section 3.1; reads from `data/open_interest/<SYMBOL>/8h.csv`; LEFT MERGE on `open_time` int64 with kline frame; mirrors `open_interest_v1.add_oi_delta_v1_features` merge-key pattern).

### 3.5 — Parquet regen command (LOAD-BEARING SPECIFICATION)

**Partial regen** (preferred — recomputes ONLY the new `long_short_zscore_30` column and writes to each symbol's v1 parquet, merging with existing columns; runtime < 1 minute across all 5 symbols):

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --track v1 \
  --format parquet \
  --workers 4 \
  --groups positioning_v1
```

**Fallback full regen** (if registry dispatch requires re-running all groups; runtime ~25-30 min):

```bash
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --interval 8h \
  --track v1 \
  --format parquet \
  --workers 4
```

Engineering chooses the partial-regen path for /049 to keep wall-clock tight. If `--groups positioning_v1` is rejected at CLI parse time (group not yet recognized), full regen is used.

### 3.6 — Runner invocation (LOAD-BEARING SPECIFICATION)

Runner is the iteration-specific wrapper `run_iteration_049.py`, which is a thin dispatch
layer around `run_baseline_v1.main()` (the refactored v1 runner).  It hardwires all
EXPLORATION-mode arguments and enforces the features-base-hash guard (LM Master Phase 4.5
Rec 1 CRITICAL ADD) at startup.

```bash
uv run python run_iteration_049.py
```

Equivalent effective invocation (what the wrapper injects into `sys.argv`):

```bash
uv run python run_baseline_v1.py \
  --exploration \
  --iteration 49 \
  --n-trials 18 \
  --seeds 1 \
  --ensemble-size 3 \
  --pruned-features
```

**Feature-column source-of-truth**: `run_iteration_049.py` imports `V1_FEATURE_COLUMNS_PRUNED`
directly from `src/crypto_trade/features_v1/__init__.py` (45 columns after the /049 source
change).  The `--pruned-features` flag tells `run_baseline_v1` to use the same import path.
No JSON file is needed — the import is the single source of truth.

**Pre-registered `--features-base-hash`** (LM Master Phase 4.5 Rec 1 CRITICAL ADD): the
wrapper verifies SHA-256 of `V1_FEATURE_COLUMNS_PRUNED` (sorted) against the pre-registered
value `a2e36f6ab3790b95e9555a0699e72bf13180063f9ec74cb406644a18b02fa93e` at startup and
aborts if it does not match.  Pass `--check-hash` to inspect without launching the backtest.
Critic Check 17 verifies no defensive Optuna HP-bound tweaks slipped in alongside the feature ADD.

Output paths:
- `reports-v1/iteration_v1-049/in_sample/` — IS trades + per-month equity + Optuna trial logs
- `reports-v1/iteration_v1-049/out_of_sample/` — OOS trades + per-month equity
- `reports-v1/iteration_v1-049/comparison.csv` — IS/OOS daily Sharpe/Sortino/MaxDD/WR/PF/trade-count vs BASELINE_V1
- `reports-v1/iteration_v1-049/feature_importance.csv` — `long_short_zscore_30` rank per cohort (A/C/D/E) + portfolio-level gain-weighted aggregate
- `reports-v1/iteration_v1-049/run.log` — Optuna trial-by-trial log

### 3.7 — Tests (new file)

**File**: `/home/roberto/crypto-trade/.worktrees/quant-research/tests/test_iteration_v1_049.py`

```python
"""Tests for iter-v1/049: long_short_zscore_30 feature dispatch."""
import numpy as np
import pandas as pd
import pytest
from crypto_trade.features_v1.positioning_v1 import compute_long_short_zscore
from crypto_trade.features_v1 import V1_FEATURE_COLUMNS_PRUNED


def test_v1_pruned_has_45_features():
    assert len(V1_FEATURE_COLUMNS_PRUNED) == 45
    assert "long_short_zscore_30" in V1_FEATURE_COLUMNS_PRUNED


def test_past_only():
    """long_short_zscore_30[t] does not use long_short_ratio[t+k] for any k > 0."""
    rng = np.random.default_rng(42)
    base = (1.0 + 0.5 * rng.standard_normal(300)).cumsum() / 100 + 1.0  # strictly positive
    df1 = pd.Series(base.copy())
    z1 = compute_long_short_zscore(df1)
    df2 = pd.Series(base.copy())
    df2.iloc[-1] = base[-1] * 100  # perturb FINAL bar only
    z2 = compute_long_short_zscore(df2)
    pd.testing.assert_series_equal(z1.iloc[:-1], z2.iloc[:-1], check_names=False)


def test_warmup_nan():
    """First 30 bars are NaN (shift(1) + min_periods=30 on rolling stats)."""
    rng = np.random.default_rng(42)
    base = (1.0 + 0.5 * rng.standard_normal(200)).cumsum() / 100 + 1.0
    z = compute_long_short_zscore(pd.Series(base))
    assert z.iloc[:30].isna().all()
    assert z.iloc[31:].notna().any()


def test_zscore_normalization_approximate():
    """Post-warmup mean ≈ 0, std ≈ 1 across long series."""
    rng = np.random.default_rng(42)
    base = (1.0 + 0.3 * rng.standard_normal(5000)) + 1.0  # IID positive
    z = compute_long_short_zscore(pd.Series(base))
    post = z.iloc[40:].dropna()
    assert abs(post.mean()) < 0.2, f"mean drift: {post.mean()}"
    assert 0.7 < post.std() < 1.5, f"std drift: {post.std()}"


def test_sum_toptrader_long_short_ratio_column_read():
    """Module reads sum_toptrader_long_short_ratio column (Critic Check: OI-CSV wiring)."""
    import inspect
    from crypto_trade.features_v1 import positioning_v1
    src = inspect.getsource(positioning_v1)
    assert "sum_toptrader_long_short_ratio" in src


def test_track_isolation():
    """Module does not import from features_v2 or features_v3."""
    import inspect
    from crypto_trade.features_v1 import positioning_v1
    src = inspect.getsource(positioning_v1)
    assert "features_v2" not in src
    assert "features_v3" not in src


def test_zscore_clip_bounded():
    """Output respects LSR_ZSCORE_CLIP=10.0 bounds."""
    from crypto_trade.features_v1.positioning_v1 import LSR_ZSCORE_CLIP
    rng = np.random.default_rng(42)
    base = (1.0 + 5.0 * rng.standard_normal(500)).cumsum() / 10 + 100  # high-variance positive
    z = compute_long_short_zscore(pd.Series(base))
    assert z.dropna().abs().max() <= LSR_ZSCORE_CLIP + 1e-9
```

### 3.8 — LM Master Phase 4.5 response map

LM Master Phase 4.5 advisor (`briefs-v1/iteration_v1-049/lgbm_advisor.md`) issued 3 recommendations + Pre-EDA |IC| prediction + 8 risk flags. Brief response map:

| # | LM Master recommendation | Adoption status | Brief reference |
|---|---|---|---|
| **Rec 1** | **Keep Optuna search space FROZEN for the +1 feature ADD; pre-register `--features-base-hash` audit.** No widening of `colsample_bytree`, `feature_fraction`, `lambda_l1`, `num_leaves`, `learning_rate`, `min_data_in_leaf`, or trial budget (n_trials=18, single-seed=42, ENSEMBLE_SIZE=3). 1/44 → 1/45 dimensionality shift is sub-noise at n_trials=18. | **ADOPTED** | Section 3.6 — runner uses standard EXPLORATION dispatch; no HP-bound tweaks. Section 6.7 R-NEW pre-registers Critic Check 17 verification of frozen search-space via `--features-base-hash` SHA256 of `V1_FEATURE_COLUMNS_PRUNED`. |
| Rec 1 secondary | At single-seed=42 + n_trials=18 EXPLORATION, if F5' IC vs `funding_rate_zscore_30` returns max \|IC\| ∈ [0.30, 0.50], expect rank under-read; NEG-INERT at EXPLORATION ≠ verdict at multi-seed CONFIRMATION. Pre-register NEG-INERT routes to 1-shot CONFIRMATION retry IF F1 partial-pass (rank ≤ 18 OR Sharpe Δ ≥ +0.03 but not both). | **ADOPTED with Section 7 disclosure** — Section 7.1 priors NEG-INERT band explicitly cites single-seed under-reading; Section 8.1 verdict subtype routing pre-registers that NEG-INERT routes to a 1-shot CONFIRMATION retry IF F1 partial-pass. |
| **Rec 2** | **Window choice — 30-bar is DEFENSIBLE; do NOT sweep alternatives. Pre-EDA must report 14-bar + 60-bar IC table as forensic context.** Hardcode `window=30` in module; add 2 forensic-only rows to `ic_orthogonality_full_44.csv` for `long_short_zscore_14` (5-day retail-burst timescale) and `long_short_zscore_60` (20-day macro positioning timescale). | **ADOPTED** | Section 2.1 anchors `window=30`; Section 3.1 module hardcodes `LSR_ZSCORE_WINDOW=30`. Section 2.6 IC table includes 2 forensic-only rows for 14-bar and 60-bar variants (NOT in V1_FEATURE_COLUMNS_PRUNED). Section 9 deliverable includes forensic rows. Adds < 5 min pre-EDA compute. |
| **Rec 3** | **Per-cohort importance prediction** (out of 45): BTC 18-28, ETH 16-26, LINK 10-20 (most-likely cohort to surface single-cohort PROMISING), LTC 22-35 (weakest), DOT 12-22. Portfolio-level rank prediction 17-25; F1 dual-gate conjunction prior ~13-17%. Cross-cohort dispersion is itself diagnostic. | **ADOPTED with Section 7 + Section 9 mandate** — Section 7.4 reports per-cohort prediction band; Section 9.2 Engineering report mandates per-cohort `feature_importance.csv` rows for A/C/D/E + portfolio-aggregated rank as the load-bearing artifact for Phase 7.4 LM Master post-mortem. |
| LM Master Pre-EDA \|IC\| prediction | max \|IC\| = 0.28 point; 80% band [0.18, 0.42]; modal landing IDEAL/DOCUMENT borderline. Distribution: <0.30 IDEAL ~55%, [0.30,0.50] DOCUMENT-low ~30%, [0.50,0.60) DOCUMENT-high ~10%, ≥0.60 ABORT ~5%. | **ACKNOWLEDGED — empirical IC arbitrates** — Section 2.5 documents the prediction; Section 2.6 IC sweep is the empirical arbiter. Section 4 F5' band routes the actual observed value at gate-evaluation time. |
| LM Master Risk Flag 1 | HP defensive-widening risk. | **MITIGATED** — Section 3.6 `--features-base-hash` + Critic Check 17. |
| LM Master Risk Flag 2 | F5' borderline IC single-seed under-reading. | **DISCLOSED in Section 7.1 + 8.1**. |
| LM Master Risk Flag 3 | v1/034 basis_zscore_30 LEARNED-NEG precedent (closest base-rate). | **CITED in Section 7.1 priors**. |
| LM Master Risk Flag 4 | iter-v3/019 funding_rate_zscore_30 PROMISING-INERT precedent (rank 14/14). | **CITED in Section 7.1 priors**. |
| LM Master Risk Flag 5 | Partial-depth (S2) honesty mandate. | **ADOPTED** — Section 2.2 + R9 in Section 6. |
| LM Master Risk Flag 6 | 4h→8h aggregation lookahead. | **MOOT** — data IS native 8h cadence per OI cache; NO 4h→8h aggregation is performed. The `fetch-oi` writes the 8h-aligned `sum_toptrader_long_short_ratio` directly. (Outline §6.2 aggregation logic supersedes itself.) |
| LM Master Risk Flag 7 | Backup axis (S3) F5' risk. | **MITIGATED** — given OI cache start 2020-09 ≥ 2021-03-24 IS-cutoff by ~7 months, S1 is expected; S3 backup unlikely to fire. |
| LM Master Risk Flag 8 | Three-consecutive-feature-family axis risk. | **REGISTERED in Section 0.6** — /050 axis rotation mandatory if /049 NEG-anything. |

**Pre-emptive responses** to potential additional recommendations:

| Anticipated recommendation (not raised by Phase 4.5 advisor) | Pre-emptive response |
|---|---|
| Add SHAP cluster check at Phase 6 to confirm `long_short_zscore_30` is non-redundant with `funding_rate_zscore_30` | **ADOPT if Phase 4.5 raises in Phase 7.4 post-mortem** — Engineering report Section 9 already mandates per-cohort feature_importance.csv; SHAP pairwise dispersion can be added in Phase 7.4 if needed. |
| Add `count_toptrader_long_short_ratio` as a companion feature | **REJECTED PRE-EMPTIVELY** — `sum_toptrader_long_short_ratio` and `count_toptrader_long_short_ratio` are algebraic-sister primitives (notional vs count aggregation of the same top-trader set; expected |IC| ≥ 0.85). Single-feature-at-a-time discipline. /050 considers only after /049 PROMISING. |
| Add `count_long_short_ratio` (global retail-skewed) as companion | **REJECTED PRE-EMPTIVELY** — same primitive class (positioning ratio); pick ONE per iter. |
| SWAP `funding_rate_zscore_30` for `long_short_zscore_30` | **REJECTED PRE-EMPTIVELY** — /049 must isolate the ADD effect. If F1 PASS + F5' borderline IC, /050 considers head-to-head SWAP. |
| Raise ENSEMBLE_SIZE from 3 to 5 | **REJECTED** — ENSEMBLE_SIZE=3 is the v1 EXPLORATION default; raising = budget change orthogonal to the feature-axis. |
| Replace LightGBM head with XGBoost | **REJECTED** — model-arch axis; /042 already closed that book. |

### 3.9 — Wall-clock budget summary

| Phase | Wall-clock | Notes |
|---|---|---|
| Pre-EDA Section 2 deliverables (committed scripts + CSVs) | 10-15 min | pandas rolling + ADF + IC on IS-only data; pure pandas (no scipy.stats for the feature itself; ADF uses statsmodels) |
| Cache extent verification (one-time data probe per Section 3.4) | < 2 min | head/tail/wc on 5 OI CSV files |
| OI cache top-up (if stale; per Section 3.4) | ≤ 5 min | incremental `fetch-oi` — only appends new rows |
| Feature regen (`--groups positioning_v1` partial) | < 1 min | O(N) rolling on 5 symbols × ~3000 candles |
| Optuna backtest (4 cohorts × monthly retrain × 18 trials × 1 seed × ENSEMBLE_SIZE=3) | ≤ 2h | EXPLORATION default per v1; +1 feature dim adds ~2.2% search-space (45 vs 44 columns), no trial-count change |
| Reports + comparison.csv + diary + closeout | 15-20 min | standard /034-/048 cadence |
| **Total** | **≤ 2.5h** | Wall-clock cap 2h HARD on backtest; total 2.5h HARD |

If backtest exceeds 2h at the 80% wall-clock mark, abort and triage. /049 is EXPLORATION; signal extraction should not exceed EXPLORATION budget.

**Budget reduced** from pre-brief outline §11's 3.0h to 2.5h: data fetcher implementation (30-45 min) + 4h historical data download (20-40 min) eliminated, since OI cache + sum_toptrader_long_short_ratio data already exists.

---

## Section 4 — Pre-Registered Failure-Mode Falsifiers (F1 through F5')

### F1 — Master falsifier (DUAL CONDITION: importance + Sharpe)

**Claim**: `long_short_zscore_30` ranks in **TOP-15 of 45** features by mean-gain importance at the portfolio-aggregated level (gain-weighted average across Models A/C/D/E, weighted by per-model IS trade count) AND IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767 (i.e., observed IS daily Sharpe ≥ +0.5267).

**Why dual gate**:
- **Importance without Sharpe lift** → LightGBM uses the feature mechanically without gaining net signal. iter-v3/019 `funding_rate_zscore_30` PROMISING-INERT precedent (rank 14/14 at LDO+TRX+Portfolio; <2% gain contribution; catastrophic OOS at higher budget).
- **Sharpe lift without importance** → the lift is attributable to Optuna basin-lottery noise on the existing 44 features, NOT the new feature. The new feature is a passenger; the lift would happen even without it.

The dual gate prevents both false-positive patterns. Lifted from v3 `engineered_features_proven` precedent (iter-v3/025 regime_momentum_signed_5d: 51% top importance AND IS +0.50 / OOS +0.84 — dual evidence is the standard).

**LM Master Phase 4.5 conjunction prior**: rank ≤ 15 portfolio ≈ 22%; IS Sharpe Δ ≥ +0.05 ≈ 25%; CONJUNCTION ≈ 13-17%.

**Status**: MASTER falsifier. F1 PASS → PROMISING (subtype determined by F2/F5'). F1 FAIL (either or both fail) → routed to F2 subtype.

### F2 — IS Sharpe Δ band (PROMISING-CLEAN vs NEG-INERT vs NEG-CLEAN)

**Claim**: 3-band classification:

| IS daily Sharpe Δ vs BASELINE_V1 (+0.4767) | Verdict subtype |
|---|---|
| ≥ +0.05 | **PROMISING-CLEAN** (if F5' PASS strict with max \|IC\| < 0.30) OR **PROMISING-WITH-CORRELATED-PRIMITIVE** (if F5' DOCUMENT band with max \|IC\| ∈ [0.30, 0.60)) |
| -0.05 < Δ < +0.05 | **NEG-INERT** — feature is tied to baseline within noise; informational drop. Inventory ground-truth: top-trader positioning sentiment is informationally subsumed by funding-rate + cross-BTC return features at v1's EXPLORATION Optuna budget. Retire `long_short_zscore_30` to V1_RETIRED_FEATURE_COLUMNS. |
| ≤ -0.05 | **NEG-CLEAN** — feature actively harms IS. v3 `inert_features_at_higher_budget` analogue. Retire + new feedback rule candidate. |

**Interpretation if FAIL into NEG-INERT**: file `long_short_zscore_30` under V1_RETIRED_FEATURE_COLUMNS (like basis_zscore_30 at /040, skew_zscore_21 at /047, trade_count_zscore_30 at /048). Document in diary that top-trader positioning sentiment is informationally subsumed by the funding-rate family + cross-BTC returns at v1's EXPLORATION Optuna budget. **NEG-INERT routes to 1-shot CONFIRMATION retry IF F1 partial-pass** (rank ≤ 18 OR Sharpe Δ ≥ +0.03 but not both) per LM Master Rec 1 secondary single-seed under-reading disclosure.

**Interpretation if FAIL into NEG-CLEAN**: same routing + new feedback rule "non-kline-class positioning sentiment features are NOT additive at v1's 18-trial EXPLORATION budget"; confirmation pending /050+ if the rule needs co-evidence.

### F3 — OOS Δ (forensic-only; NOT a verdict gate)

**Claim**: OOS daily Sharpe Δ vs BASELINE_V1 (+1.1913) is REPORTED in comparison.csv but is NOT a /049 success criterion. /046 PROMISING-DIVERGENCE established that OOS-aware selection is a leak path; /049 preserves discipline.

**Status**: Forensic only. **Critic Phase 7.5 CANNOT cite OOS Sharpe Δ < +0.05 as a /049 failure mode.** OOS is logged for /050+ priors and for the eventual CONFIRMATION run if /049 routes to PROMISING.

### F4 — ADF Stationarity (PRE-LAUNCH gate)

**Claim**: `long_short_zscore_30` is stationary across all 5 v1 symbols (BTC/ETH/LINK/LTC/DOT) at the IS-window upper bound — ADF p-value < 0.05 with `regression='c'`, `maxlag=10`. Evaluated PRE-LAUNCH from `analysis/iteration_v1-049/adf_stationarity_per_symbol.csv` (Section 2.3).

**Outcomes**:
- 5/5 PASS → V1_FEATURE_COLUMNS_PRUNED stationarity invariant preserved (44/44 → 45/45). Brief notes the property in Section 9. **Proceed to launch.**
- 4/5 PASS → INVESTIGATE the failing symbol. If borderline (p ∈ [0.05, 0.10]), document and proceed with explicit caveat. If hard fail (p > 0.10), redesign the 30-bar window for that symbol OR mask that symbol's column to NaN.
- ≤ 3/5 PASS → ABORT pre-launch.

**Rationale**: A 30-bar rolling z-score of a strictly-positive account-ratio series has near-perfect local stationarity by construction. Expected 5/5 PASS at ADF p-value < 1e-15.

### F5' — IC Orthogonality (PRE-LAUNCH gate — TIGHTENED, third consecutive codification)

**Claim**: Max absolute pairwise Pearson IC (lag-0, pooled across 5 symbols, sample-weighted by per-symbol IS row count) of `long_short_zscore_30` vs ALL 44 features in V1_FEATURE_COLUMNS_PRUNED is **below the F5' band threshold**. Evaluated PRE-LAUNCH from `analysis/iteration_v1-049/ic_orthogonality_full_44.csv` (Section 2.6).

**F5' bands (TIGHTENED; third consecutive codification: /047 set 0.50 PASS, /048 tightened to 0.30 PASS, /049 inherits identically)**:

| max |IC| | F5' status | Action |
|---|---|---|
| **< 0.30** | **PASS** — orthogonal | Proceed to launch as PROMISING-CLEAN-eligible |
| **[0.30, 0.60)** | **DOCUMENT** | Proceed to launch but Section 8 routes to PROMISING-WITH-CORRELATED-PRIMITIVE subtype if F1 PASS |
| **≥ 0.60** | **ABORT-PRE-LAUNCH** | Same handling as /047 + /048 NEG-CLEAN-PRE-EDA — feature retired pre-launch; /050 pivots axis family per three-consecutive saturation rule |

**Special-attention features** (Section 2.5 IC table covers explicitly):

- `funding_rate_zscore_30` — closest empirical correlate. LM Master point estimate |IC| = 0.28.
- `funding_rate_zscore_90` — longer-horizon funding z-score. Predicted |IC| ≈ 0.22.
- `oi_delta_30_z90` — leverage-flow proxy (different transform of OI primitive). Predicted |IC| 0.10-0.25.
- `cross_btc_ret_5` / `cross_btc_ret_20` — BTC short/mid-cadence returns (positioning lead-lag). Predicted |IC| 0.18.
- `mom_rsi_14` — overbought/oversold (extreme-positioning correlate). Predicted |IC| 0.10-0.25.
- `mr_pct_from_high_20` — mean-reversion extreme. Predicted |IC| 0.10-0.20.
- `vol_taker_buy_ratio` — directional flow proxy. Predicted |IC| 0.10-0.20.

**Rationale for tightened 0.30 PASS / 0.60 ABORT band** (inherited identically from /048): even mid-range 0.30-0.60 |IC| risks PROMISING-WITH-CORRELATED-PRIMITIVE classification rather than CLEAN; a feature whose primitive is non-kline-class but whose values are 0.40-correlated with `funding_rate_zscore_30` is functionally a transform of that existing feature for tree-split purposes. The 0.30 PASS threshold ensures CLEAN status is reserved for genuinely orthogonal additions. **ABORT trigger stays at ≥ 0.60.**

**Why the tightened band is even more load-bearing at /049 than /048**: this is the THIRD consecutive feature-family iter with F5'/F5 protective gate. Two consecutive ABORTs (/047 algebraic-sister at 0.81, /048 empirical-correlation at 0.91) demonstrate that gates do fire. /049 has the structurally cleanest data-class story but the empirical IC arbitrates.

### Falsifier summary table

| F-AXIS | Type | Phase | Gate | Failure routes to |
|---|---|---|---|---|
| F1 | Master (dual) | Phase 7 | Top-15 importance AND IS Δ ≥ +0.05 | F2 subtype routing |
| F2 | IS Sharpe band | Phase 7 | -0.05 < Δ < +0.05 OR Δ ≤ -0.05 | NEG-INERT / NEG-CLEAN retire |
| F3 | OOS (forensic only) | Phase 7 | No gate (informational) | Logged in diary; not a verdict gate |
| F4 | ADF stationarity | Phase 5 (pre-launch) | 5/5 PASS @ p < 0.05 | INVESTIGATE / REDESIGN / ABORT pre-launch |
| F5' | IC orthogonality TIGHTENED | Phase 5 (pre-launch) | max \|IC\| < 0.30 PASS; [0.30, 0.60) DOCUMENT; ≥ 0.60 ABORT | ABORT-PRE-LAUNCH if ≥ 0.60 |

---

## Section 5 — Methodology Integrity

### 5.1 — Look-ahead audit

- Feature definition uses **past-only** rolling windows with `shift(1)` before rolling stats (mirrors `open_interest_v1.compute_oi_delta_zscore`); verified by `test_iteration_v1_049::test_past_only`.
- Decision at candle `t+1` consumes `long_short_zscore_30[t]` (the bar-close value at t, where `lsr_mean_30[t]` and `lsr_std_30[t]` use bars ending at t-1 inclusive due to `shift(1)`).
- No CSV-level peek at OOS data during EDA: `assert df['open_time'].max() < OOS_CUTOFF_MS` in every Section 2 script.
- **NO 4h→8h aggregation performed** — data is native 8h cadence in `data/open_interest/<SYMBOL>/8h.csv`. (Outline §6.2 aggregation logic is moot.)
- **LM Master Risk Flag 6** (4h→8h aggregation lookahead): MOOT — no aggregation. Critic Phase 7.5 verifies via `grep -n "4h\|aggregate" src/crypto_trade/features_v1/positioning_v1.py` returning no semantic aggregation logic.

### 5.2 — Embargo / purge

- v1 walk-forward CV `walk_forward.py:113` is `train_end_ms = test_start_ms - embargo_ms` (the fixed-2026-05-12 implementation). /049 inherits this — no change.
- The new feature does NOT introduce a new max-label-horizon parameter. Inherited triple-barrier label parameters (atr_tp / atr_sl per BASELINE_V1) are UNCHANGED. Embargo budget unchanged.

### 5.3 — DSR / PSR / PBO

- EXPLORATION mode: DSR / PSR are STRUCTURAL ARTIFACTS at n_trials=18, --seeds 1 (per v3 `dsr_mode_artifact` rule — EXPLORATION-mode DSR / PSR are INFORMATIONAL ONLY, not MERGE gates). Reported in `comparison.csv` for forensic continuity but NOT cited as edge-significance evidence.
- CONFIRMATION-mode DSR > 0.95 gate evaluation deferred to /050+ if /049 PROMISING.
- PBO via CSCV: standard v1 walk-forward emits PBO; reported informationally. PBO < 0.4 is MERGE-time gate; EXPLORATION informational.

### 5.4 — Regime attribution

- Section 10 covers per-regime IS/OOS PnL attribution (bull / bear / chop / vol-spike / recovery / other tagger). Standard v1 `regime_attribution.csv` emission via `run_baseline_v186.py`.

### 5.5 — Reproducibility checksum

- Engineering report emits SHA256 of `feature_columns.json` + `V1_FEATURE_COLUMNS_PRUNED` source-of-truth (LM Master Rec 1 CRITICAL ADD: `--features-base-hash`). Catalogued in `briefs-v1/exploration_catalog.md` row.

### 5.6 — Hypothesis-implementation alignment (Critic Check 8 equivalent)

- Hypothesis: ADD `long_short_zscore_30` to `V1_FEATURE_COLUMNS_PRUNED` (44 → 45) using the `sum_toptrader_long_short_ratio` column from `data/open_interest/<SYMBOL>/8h.csv`.
- Implementation: `git diff main` over `src/crypto_trade/features_v1/__init__.py`, `src/crypto_trade/features_v1/positioning_v1.py` (NEW), `src/crypto_trade/features/__init__.py`, `tests/test_iteration_v1_049.py` (NEW). The diff must show exactly: NEW file `positioning_v1.py` reading `sum_toptrader_long_short_ratio` + INSERT one line in V1_FEATURE_COLUMNS_PRUNED + count assertion 44 → 45 + register `positioning_v1` group in features registry + new tests. **NO modifications to `main.py` or fetchers** — data is already cached.
- No OTHER axis changes (no risk-gate modification, no labeling change, no universe modification, no model architecture change, no Optuna HP-bound change). Critic Phase 6.0 + Phase 7.5 verifies via diff.

### 5.7 — Critic Check 14 (axis-family match-to-diff)

- Declared axis family: `feature-family`.
- Source diff must show: feature addition only (positioning_v1.py NEW + V1_FEATURE_COLUMNS_PRUNED insert + features registry register + tests). No labeling diff, no risk-primitive diff, no universe diff, no model-arch diff, no Optuna HP-bound diff (Rec 1 CRITICAL ADD verification). No `main.py` diff (no fetcher work).
- Critic Phase 7.5 Check 14 verifies declared family matches actual diff. PASS expected.

---

## Section 6 — Risk Mitigation

### 6.1 — Inherited BASELINE_V1 risk gates (NO CHANGE)

- **R1 (Consecutive-SL Cooldown)**: K=3, C=27 candles. Applies to Models C/D/E. Model A unchanged.
- **R2 (Drawdown-triggered Position Scaling)**: Applies only to Model E; floor 0.33, trigger 7% per-model DD.
- **R3 (OOD Mahalanobis Gate)**: 70th-percentile cutoff; 16 scale-invariant features per `V1_OOD_FEATURE_COLUMNS`. **NOT EXTENDED to long_short_zscore_30**; second axis change at the same iteration.

### 6.2 — F4/F5' pre-launch protective gates (R-NEW for /049; TIGHTENED, third consecutive codification)

- F4 ADF stationarity gate: PRE-LAUNCH. ≤3/5 PASS → ABORT pre-launch. Protects V1_FEATURE_COLUMNS_PRUNED stationarity invariant.
- F5' IC orthogonality gate: PRE-LAUNCH **TIGHTENED**: max \|IC\| < 0.30 PASS / [0.30, 0.60) DOCUMENT / ≥ 0.60 ABORT. Protects feature-surface orthogonality invariant. /049 inherits the 0.30 PASS threshold from /048 (codified from /047 + /048 lessons).

### 6.3 — NEG-CLEAN routing if active harm

- F2's NEG-CLEAN band (Δ ≤ -0.05) triggers: (a) retire `long_short_zscore_30` to V1_RETIRED_FEATURE_COLUMNS; (b) candidate new feedback rule "non-kline-class positioning sentiment z-scores are NOT additive at v1's 18-trial EXPLORATION budget"; (c) document in diary's `Lessons` section.

### 6.4 — Wall-clock kill switch

- Phase 6 backtest > 2h wall-clock → abort and triage. EXPLORATION budget HARD cap.

### 6.5 — IS-calibrated thresholds with simulated effect

- F1 importance threshold (TOP-15 of 45): consistent with /045 mean-gain audit (top-15 captures 70-80% of total gain). Simulated effect: if `long_short_zscore_30` ranks 16+ AND IS Δ < +0.05, NEG-INERT routing prevents adding a passenger feature.
- F2 IS Sharpe lift floor (+0.05): calibrated against /034-/043 EXPLORATION verdicts (PROMISING-CLEAN posted IS Δ in [+0.05, +0.15]). +0.05 is the meaningful-signal-above-noise threshold.
- F5' tightening to 0.30: codified from /047 + /048 NEG-CLEAN-PRE-EDA lessons — even mid-range 0.30-0.60 |IC| risks PROMISING-WITH-CORRELATED-PRIMITIVE classification, not CLEAN.

### 6.6 — Concentration cap

- BASELINE_V1 concentration governed at per-symbol level by R1 cool-down; 30%-of-OOS-PnL cap is a MERGE-time gate, not EXPLORATION. /049 inherits BASELINE_V1's concentration profile unchanged. Top-symbol concentration reported in `comparison.csv` for forensic continuity.

### 6.7 — Critic Check 17 frozen-search-space verification (LM Master Rec 1 CRITICAL ADD)

- Runner emits SHA256 of `V1_FEATURE_COLUMNS_PRUNED` source at invocation (`--features-base-hash`).
- Critic Phase 7.5 Check 17 verifies: (a) hash matches the committed value; (b) `git diff main src/crypto_trade/strategies/ml/lgbm.py src/crypto_trade/runners/` shows no Optuna HP-bound modifications (colsample_bytree, feature_fraction, lambda_l1 unchanged).
- Pre-empts defensive search-space widening that would compound the axis.

### 6.8 — NEW for /049: data-source operational risk

- OI cache (`data/open_interest/<SYMBOL>/8h.csv`) is the data source for `sum_toptrader_long_short_ratio`. Cache extent verified at Phase 5 EDA (`long_short_availability_per_symbol.csv`).
- Critic Phase 6.0 pre-flight checks the 5 OI cache files exist and have non-zero row counts before launching Phase 6.
- Top-up via `fetch-oi --intervals 8h` (idempotent; <5 min) if cache is stale beyond the latest 8h boundary.

### 6.9 — NEW for /049: partial-depth honesty (LM Master Risk Flag 5)

- Brief Section 2.2 reports per-symbol availability dates in `long_short_availability_per_symbol.csv`. F1/F2 evaluated on FULL-IS-window numbers (the eval lens v1 catalog uses).
- If S2 (partial coverage for any symbol), `comparison.csv` adds a forensic row: availability-restricted IS Sharpe per-cohort + portfolio. NOT alternative-success criteria; informational only.
- LightGBM handles NaN via histogram-binning (routes to dominant child); runner's skip-month logic excludes months where >50% of a symbol's feature values are NaN.

---

## Section 7 — Pre-Registered Failure-Mode Prediction

### 7.1 Verdict band priors

LM Master Phase 4.5 priors (8 verdict bands) anchored as ground-truth; QR Section 7.1 routes them into the 6 Phase-7-verdict bands /049 will report:

| Outcome | Prior (anchored to LM Phase 4.5) | Reasoning |
|---|---:|---|
| **PROMISING-CLEAN** (F1 PASS AND F5' PASS strict <0.30) | **8-12%** | LM Master's |IC| < 0.30 IDEAL probability ~55%; conditional on F1 dual-gate PASS (~13-17% per LM Rec 3 conjunction) the joint is ~8-12%. Non-kline-class structural advantage gives higher prior than /048's 5-10%. |
| **PROMISING-WITH-CORRELATED-PRIMITIVE** (F1 PASS but F5' DOCUMENT band |IC| ∈ [0.30, 0.60)) | **5-9%** | This is the secondary PROMISING outcome — top-trader positioning plausibly carries signal but empirical IC with `funding_rate_zscore_30` is moderate. LM Master DOCUMENT-zone probability ~40%; F1 conjunction lowers to ~5-9%. Lower than /048's PROMISING-WITH-CORRELATED because data class is more genuinely orthogonal. |
| **NEG-INERT** (IS Δ ∈ (-0.05, +0.05); rank may exceed 15) | **35-40%** (MODAL) | LM Master modal NEGATIVE-no-effect 35%. Closest base-rate precedents: iter-v3/019 funding_rate_zscore_30 INERT rank 14/14; v1/034 basis_zscore_30 LEARNED-NEG; v1/023 funding_rate_zscore_30 INERT; v1/025 oi_delta_30_z90 INERT (now mid-table). Three v1 NEW-primitive z-score precedents all went modal-NEG; base-rate prior is binding. Single-seed=42 + n_trials=18 also under-reads moderately-correlated features. |
| **NEG-CLEAN** (IS Δ ≤ -0.05; active OOS-side regression possible) | **12-18%** | LM Master LEARNED-NEG 9% (active harm subset). v1/034 basis_zscore_30 LEARNED-NEG precedent is closest analog (-0.27 OOS Δ, 5/5 symbols OOS-negative). v3 `inert_features_at_higher_budget` rule analogue. IC 0.30-0.50 with funding-z could divert splits AWAY from genuinely orthogonal features. |
| **NEG-CLEAN-PRE-EDA** (F5' ABORT max \|IC\| ≥ 0.60) | **4-7%** | LOWER than /048's empirical 5-10%: non-kline-class structural advantage. LM Master ≥0.60 ABORT probability ~5%. Risk remains if BTC top-trader positioning post-CME-spot-ETF era empirically tracks `funding_rate_zscore_30` more tightly than expected (institutional arb rebalancing). |
| **BLOCK-PENDING-FIX** (F4 stationarity fail, OR src/ defect at Critic Phase 7.5) | **5-8%** | F4 pre-EDA catches stationarity defect. Critic Phase 7.5 may find a defect in dispatch (NaN handling at 30-candle warmup boundary, OI-CSV column-pin defect in feature dispatcher, track-isolation grep, merge-key int64 cast mismatch). Single-rerun discipline applies. |

Sum ≈ 100% (modulo band overlap).

### 7.2 Most plausible failure scenario

**NEG-INERT (35-40% prior)** is the modal failure mode: funding-rate features (`funding_rate_zscore_30`, `funding_rate_zscore_90`) + OI features (`oi_delta_30_z90`) + cross-BTC return features (`cross_btc_ret_*`) collectively span ~12-15% of LightGBM's split-budget in BASELINE_V1; the residual signal in `long_short_zscore_30` after that allocation is small. Trees may already extract positioning-sentiment signal combinatorially through depth-2 paths over funding + OI + cross-BTC features.

Sub-scenario: `long_short_zscore_30` ranks 17-28 (mid-table importance) AND IS Sharpe Δ ∈ [0.00, +0.04]. Feature mechanically used but not carrying incremental signal — passenger usage. /049 closeout routes to NEG-INERT. Per LM Master Rec 1 secondary, single-seed=42 + n_trials=18 may under-read the true value by 10-15 ranks; if partial-pass (rank ≤ 18 OR Sharpe Δ ≥ +0.03 but not both), Section 8.1 routes to 1-shot CONFIRMATION retry rather than immediate retire.

### 7.3 Expected metric signature

| Metric | PROMISING-CLEAN | PROMISING-WITH-CORRELATED-PRIMITIVE | NEG-INERT | NEG-CLEAN |
|---|---:|---:|---:|---:|
| Importance rank (portfolio) | ≤ 15 | ≤ 15 | 16-30 | 30-45 or 1-5 (rank doesn't disambiguate) |
| IS daily Sharpe (vs +0.4767 baseline) | +0.52 to +0.65 | +0.52 to +0.62 | +0.45 to +0.51 | +0.30 to +0.43 |
| OOS daily Sharpe (forensic) | +1.10 to +1.45 | +1.05 to +1.40 | +1.05 to +1.25 | +0.50 to +1.05 |
| max \|IC\| at F5' | < 0.30 | ∈ [0.30, 0.60) | varies | varies |
| Top-symbol concentration | unchanged (~32-38%) | unchanged | unchanged | unchanged |
| Trade count (IS / OOS) | within ±10% baseline | within ±10% baseline | within ±5% | within ±5% |

OOS signature highly noisy; ranges illustrative. Verdict determined by IS metrics + F1 importance + F5' band only (per F3 forensic-only discipline).

### 7.4 Per-cohort importance prediction (LM Master Rec 3)

LM Master Phase 4.5 Rec 3 predicted per-cohort importance ranges that Section 9.2 Engineering report must verify:

| Cohort | LM predicted rank (out of 45) | Mechanism |
|---|---|---|
| BTC | 18-28 | Top-100 BTC traders are institutionally diluted (CME-spot-ETF arbitrage rebalancing); positioning z-score amplitude is dampened by passive flow. Mid-band; expect rank ~22. |
| ETH | 16-26 | Similar to BTC with more retail residual; ETF-effect smaller post-2024-05. Mid-band; expect rank ~20. |
| LINK | 10-20 | Mid-cap alt; top-trader positioning carries strongest signal here because passive/institutional flow is minimal. **Most likely cohort to surface a single-cohort PROMISING.** Expect rank ~14. |
| LTC | 22-35 | "Background symbol" pattern (same as /047 Rec 3, /048 Rec 3). LTC's positioning data has lowest volume of the 5 cohorts; expect rank ~28. **Weakest cohort.** |
| DOT | 12-22 | Smallest-cap of 5; highest retail FOMO sensitivity; positioning z-score should differentiate quiet→burst transitions cleanly. Expect rank ~16. |
| **Portfolio aggregate** | **17-25 (INERT-leaning but not bottom-quintile)** | LM Master Rec 3 point estimate; dispersion range 10-35, std-of-rank ~7 |

**Cross-cohort dispersion is itself diagnostic** (LM Rec 3): wide dispersion (range 10-35) means cohort-conditional positioning signal (real but not pooled-additive); tight cluster (all ~22) means mechanical noise allocation (NEG-INERT confirmed). Phase 7.4 LM Master post-mortem will compare actual per-cohort ranks against this prediction band.

---

## Section 8 — Pre-Registered Comparison Criteria

### 8.1 — Verdict subtypes (EXPLORATION verdict band)

EXPLORATION verdict at /049 closeout is one of:

1. **PROMISING-CLEAN** — F1 PASS (top-15 importance AND IS Δ ≥ +0.05); F5' PASS strict (max \|IC\| < 0.30). Feature retained in V1_FEATURE_COLUMNS_PRUNED; /050 considers SECOND positioning-class feature (e.g., `count_toptrader_long_short_ratio_zscore_30`, `count_long_short_ratio_zscore_30` global retail, or 14-bar / 60-bar window variant per LM Master Rec 2 forensic context) to test additivity OR multi-seed CONFIRMATION budget.
2. **PROMISING-WITH-CORRELATED-PRIMITIVE** — F1 PASS but F5' DOCUMENT band (|IC| ∈ [0.30, 0.60), typically vs `funding_rate_zscore_30`). Feature retained in V1_FEATURE_COLUMNS_PRUNED; /050 considers head-to-head SWAP test (DROP `funding_rate_zscore_30`, KEEP `long_short_zscore_30`) at multi-seed CONFIRMATION budget. Per `feedback_v3_promising_feature_mechanical.md`, this subtype is **non-compoundable as signal source** — bundled at CONFIRMATION as "strictly accretive component decision" not "new edge ingredient".
3. **NEG-INERT (standard)** — IS Δ ∈ (-0.05, +0.05) AND rank > 18 AND Sharpe Δ < +0.03. Feature retired to V1_RETIRED_FEATURE_COLUMNS. Diary documents inventory ground-truth update.
4. **NEG-INERT (partial-pass; single-seed under-read)** — IS Δ ∈ (-0.05, +0.05) AND (rank ≤ 18 OR Sharpe Δ ∈ [+0.03, +0.05]). Per LM Master Rec 1 secondary disclosure, /050 routes to 1-shot multi-seed CONFIRMATION retry to disambiguate single-seed lottery from true INERT. If 5-seed CONFIRMATION confirms INERT, retire; if 5-seed CONFIRMATION reveals PROMISING signal, escalate.
5. **NEG-CLEAN** — IS Δ ≤ -0.05; feature actively harms IS. Feature retired + candidate new feedback rule "non-kline-class positioning sentiment z-scores are NOT additive at v1's 18-trial EXPLORATION budget"; confirmation pending /050+.
6. **NEG-CLEAN-PRE-EDA** — F5' ABORT (max \|IC\| ≥ 0.60). No backtest runs. Feature reverted in V1_FEATURE_COLUMNS_PRUNED. /050 MUST rotate axis family (three-consecutive feature-family NEG saturation rule).
7. **BLOCK-PENDING-FIX** — F4 stationarity fail, OR src/ defect at Critic Phase 7.5. Single-rerun discipline: one cycle to address the defect, then verdict can only be PASS or BLOCK-FINAL.

### 8.2 — Comparison vs BASELINE_V1 (the anchor; not vs /046 IS-only substrate, /047 ABORT, or /048 ABORT)

| Metric | BASELINE_V1 anchor | /049 PROMISING threshold | /049 NEG threshold |
|---|---:|---:|---:|
| IS daily Sharpe | +0.4767 | ≥ +0.5267 (Δ ≥ +0.05) | -0.05 < Δ < +0.05 → NEG-INERT; ≤ -0.05 → NEG-CLEAN |
| OOS daily Sharpe (forensic) | +1.1913 | reported only; not a gate | reported only; not a gate |
| Top-symbol concentration (OOS) | ~32-38% (DOT-heavy by design) | unchanged | unchanged |
| Trade count (IS / OOS) | per BASELINE_V1 | within ±10% (no sudden trade-count compression) | reported |
| `long_short_zscore_30` importance rank (portfolio) | n/a | ≤ 15 (F1) | 16+ → routed to F2 subtype |
| max \|IC\| at F5' | n/a | < 0.30 (PROMISING-CLEAN) or [0.30, 0.60) (PROMISING-WITH-CORRELATED-PRIMITIVE) | ≥ 0.60 → ABORT-PRE-LAUNCH |

**Critical**: comparison is vs BASELINE_V1 ONLY (per the v1 anchor convention). /046 IS-only substrate (PROMISING-DIVERGENCE), /047 NEG-CLEAN-PRE-EDA, and /048 NEG-CLEAN-PRE-EDA are NOT comparison anchors at /049 — they are forensic-only context.

---

## Section 9 — Library Stack Declaration

### 9.1 Required code artifacts (committed BEFORE Phase 6 backtest launch)

1. `analysis/iteration_v1-049/long_short_zscore_30_definition.py` — verbatim pandas formula committed; minimal unit test confirming the formula matches Section 2.1 verbatim.
2. `analysis/iteration_v1-049/long_short_availability_per_symbol.csv` — per-symbol availability dates from OI cache (replaces outline §7 historical-depth probe; reads `data/open_interest/<SYMBOL>/8h.csv` extents directly). 5 rows.
3. `analysis/iteration_v1-049/adf_stationarity_per_symbol.csv` — F4 input; 5 rows; columns `symbol, n_obs, adf_stat, adf_pvalue, lag_used, pass_at_005`.
4. `analysis/iteration_v1-049/distribution_stats_per_symbol.csv` — 5 rows × 10 cols (`symbol, mean, std, skew, kurtosis, p05, p25, p50, p75, p95`).
5. `analysis/iteration_v1-049/ic_orthogonality_sentiment_class.csv` — 8 rows × 3 cols (`feature, ic, n_pair`); high-conjecture pairs only (funding-z + OI-delta + cross-BTC + RSI + mr_pct + taker-buy).
6. `analysis/iteration_v1-049/ic_orthogonality_full_44.csv` — 44 rows × 3 cols (full V1_FEATURE_COLUMNS_PRUNED sweep) + 2 forensic-only rows for `long_short_zscore_14` and `long_short_zscore_60` IC vs the 30-bar variant (LM Master Rec 2 forensic context). **max(\|IC\|) over the 44 V1_FEATURE_COLUMNS_PRUNED rows is the F5' gate input** (forensic rows excluded from F5' gate evaluation).
7. `analysis/iteration_v1-049/f4_f5_gate_outcomes.md` — pass/fail per gate with quoted critical values + decision (proceed / document / abort).
8. `analysis/iteration_v1-049/feature_columns.json` — committed JSON list of 45 feature names; pinned in the runner invocation per Section 3.6.

### 9.2 Required engineering artifacts (post-Phase 6 backtest)

9. `reports-v1/iteration_v1-049/comparison.csv` — IS / OOS daily Sharpe / Sortino / MaxDD / WR / PF / trade count vs BASELINE_V1. If S2 partial-depth, includes availability-restricted IS Sharpe rows (LM Master Risk Flag 5).
10. `reports-v1/iteration_v1-049/feature_importance.csv` — `long_short_zscore_30` rank **per cohort (A/C/D/E)** AND portfolio-level gain-weighted aggregate (LM Master Rec 3 cross-cohort dispersion verification).
11. `reports-v1/iteration_v1-049/regime_attribution.csv` — per-regime IS/OOS PnL attribution.
12. `reports-v1/iteration_v1-049/integration_smoke_test.md` — confirms (a) `len(V1_FEATURE_COLUMNS_PRUNED) == 45`; (b) runner pins explicit 45-element list; (c) `tests/test_iteration_v1_049.py` passes; (d) track-isolation grep returns empty; (e) `pytest tests/` all passes; (f) `--features-base-hash` SHA256 matches expected (LM Rec 1 CRITICAL ADD); (g) `sum_toptrader_long_short_ratio` OI-CSV column read confirmed from feature dispatcher; (h) `data/open_interest/<SYM>/8h.csv` extent verified for all 5 v1 symbols.

### 9.3 Library / framework pinning

- pandas / numpy version inherited from `pyproject.toml` lockfile (no scipy.stats requirement for the feature itself — pure pandas rolling).
- statsmodels for ADF (`statsmodels.tsa.stattools.adfuller`) at Section 2.3.
- LightGBM version inherited (no upgrade at /049).
- **NO new dependencies** (no `httpx`-driven fetcher work; OI cache already populated).

### 9.4 Test path

`/home/roberto/crypto-trade/.worktrees/quant-research/tests/test_iteration_v1_049.py` — Section 3.7 above (7 tests: feature count 45, past-only, warmup NaN, z-score normalization, sum_toptrader_long_short_ratio column read, track isolation, zscore clip bounded).

---

## Section 10 — Regime Attribution Plan

### 10.1 Per-regime IS Sharpe table (Phase 6 output)

Per the v1 `regime_attribution.csv` schema. Reported regimes: bull, bear, chop, vol-spike, recovery, other.

| Regime | IS sample (target) | Cand IS Sharpe (target) | Cand IS Trades (target) | Baseline IS Sharpe | IS Δ vs baseline | Comment |
|---|---|---:|---:|---:|---:|---|
| bull | IS | ≥ -0.35 + 0.05 = -0.30 | ~50-65 | -0.35 | ≥ +0.05 (PROMISING IF improves) | Top-trader positioning extreme-long signals euphoria in bull regimes — contrarian fade signal |
| bear | IS | ≥ +0.15 + 0.05 = +0.20 | ~200-230 | +0.15 | ≥ +0.05 | Capitulation detection in bear regimes — extreme-short positioning signals exhaustion |
| chop | IS | ≥ +0.23 + 0.00 = +0.23 | ~220-240 | +0.23 | ≥ 0 (neutral OK) | Chop regimes have low |positioning z|; z-score should not move signals heavily |
| vol-spike | IS | n/a (tagger limitation) | 0 | n/a | n/a | Regime never tagged at IS — tagger artifact |
| recovery | IS | ≥ +0.28 + 0.05 = +0.33 | ~100-130 | +0.28 | ≥ +0.05 | Recovery regimes: positioning shifts from cap/short to neutral; z-crossing should fire |
| other | OOS | n/a (most OOS regimes collapse to "other" per /046 finding) | varies | n/a | n/a | Regime tagger OOS-degenerate documented in /046 |

**Critical**: per-regime IS metrics are FORENSIC; the verdict gate is F1 (master) + F2 (band). Per-regime Pareto-relaxed test is the /045 multi-regime convention and applies at CONFIRMATION, not EXPLORATION.

### 10.2 Specialist-mechanism classification (per /041 closeout convention)

Pre-EDA conjecture for /049's specialist mechanism:

- **Type**: hypothesized **type-A IS-strong** (positioning sentiment is most informative for trade-direction selection in IS regimes with extreme |z|; OOS transferability uncertain given post-CME-spot-ETF regime change).
- **Risk facet**: **Sharpe-maximizer** (the new feature targets cleaner trade-direction at IS; not a DD-minimizer or Sortino-shaper primary purpose).
- **Regime profile**: hypothesized to most help in **bear + recovery** (capitulation-event positioning extremes) and **bull** (contrarian fade at extreme-long positioning). Chop / vol-spike unclear.
- **Cohort profile (LM Master Rec 3 prediction)**: LINK > DOT > ETH > BTC > LTC. Mid-cap symbols (LINK, DOT) expected to surface signal first due to less institutionally-diluted top-trader census.

Updated post-EDA in diary.

### 10.3 Regime attribution emission

`run_baseline_v186.py` emits `regime_attribution.csv` automatically. Engineering report Section 9 references this file's path explicitly.

---

## End of Brief

**Phase 5 author**: QR (Phase 5).
**Date**: 2026-06-01.
**Status**: AUTHORED — awaiting Phase 5.5 gate verification (axis rotation valid, LM Master responses addressed, F4/F5' pre-launch gates pre-registered) + Phase 6.0 Critic pre-flight (axis-family match, track isolation, src/ diff bounded, frozen Optuna search-space verification, OI cache extent verified).

**Phase 5.5 gate checklist** (operator):
- [ ] Section 0.6 axis-rotation declared VALID with constraint (this brief: YES — `feature-family` 3rd consecutive but content-null prior 2 — registered constraint for /050)
- [ ] Section 2.5 HIGH-RISK declaration explicit (this brief: NORMAL-RISK + reason)
- [ ] Section 3.8 LM Master responses populated (this brief: YES — Rec 1 ADOPTED + secondary disclosure ADOPTED + Rec 2 ADOPTED + Rec 3 ADOPTED + all 8 Risk Flags addressed)
- [ ] Section 4 falsifiers pre-registered with numeric thresholds (this brief: YES — F1-F5'; F5' TIGHTENED to 0.30 PASS / 0.60 ABORT third consecutive codification)
- [ ] Section 9 deliverables committed BEFORE Phase 6 launch (this brief: 8 pre-Phase-6 artifacts enumerated)
- [ ] Section 5.6 hypothesis-implementation alignment specifiable as a `git diff` (this brief: YES — see Section 5.7; NO `main.py` diff because no fetcher work)

**Phase 6.0 Critic pre-flight checklist**:
- [ ] Track isolation grep returns empty for both `features_v2` and `features_v3` imports in `src/crypto_trade/features_v1/positioning_v1.py`
- [ ] `tests/test_iteration_v1_049.py` passes locally before backtest launch (7 tests)
- [ ] `V1_FEATURE_COLUMNS_PRUNED` count assertion updated 44 → 45
- [ ] `feature_columns.json` SHA256 matches `list(V1_FEATURE_COLUMNS_PRUNED)` at HEAD
- [ ] F4 ADF artifact 5/5 PASS (or 4/5 with documented investigation; ≤ 3/5 → ABORT pre-launch)
- [ ] F5' IC orthogonality artifact max \|IC\| < 0.60 (and < 0.30 for CLEAN routing; ≥ 0.60 → ABORT pre-launch)
- [ ] LM Master Rec 1 CRITICAL ADD: `--features-base-hash` SHA256 emitted at runner invocation; no Optuna HP-bound diff in `src/crypto_trade/strategies/ml/lgbm.py` / `runners/`
- [ ] `sum_toptrader_long_short_ratio` OI-CSV column read verified by `test_iteration_v1_049::test_sum_toptrader_long_short_ratio_column_read`
- [ ] OI cache extent verified for all 5 symbols (`long_short_availability_per_symbol.csv` row count = 5; earliest_ts_ms < OOS_CUTOFF_MS for each symbol)
- [ ] No `main.py` diff (no fetcher work; data already cached) — verified by `git diff --stat main src/crypto_trade/main.py` returning empty

If any pre-launch gate fails → brief revised before Phase 6 dispatch; no backtest runs on a pathological feature addition.
