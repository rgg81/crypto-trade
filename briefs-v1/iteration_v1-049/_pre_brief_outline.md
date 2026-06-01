# iter-v1/049 — Pre-Brief Outline

**Status:** Pre-brief outline authored. Synthesizes /047 NEG-CLEAN-PRE-EDA closeout (skew_zscore_21 ABORTED at F5 |IC|=0.81 vs `stat_skew_20`) + /048 NEG-CLEAN-PRE-EDA closeout (trade_count_zscore_30 ABORTED at F5' |IC|=0.91 vs `vol_volume_rel_20` empirical correlation). **The decisive lesson from /047 + /048**: v1 internal-kline feature space is empirically DENSE — even the only kline-primitive UNTOUCHED by V1_FEATURE_COLUMNS_PRUNED (`number_of_trades`) failed the F5' orthogonality gate due to empirical co-movement with volume z-scores. **The NEW feature MUST be derived from a NON-KLINE data source.**

**TYPE:** `EXPLORATION` (cycle-6 EXPLORATION 4/10).

**Cycle slot:** cycle-6 EXPLORATION 4/10. /046 (1/10 methodology PROMISING-DIVERGENCE), /047 (2/10 feature-family NEG-CLEAN-PRE-EDA at F5 algebraic-sister), /048 (3/10 feature-family NEG-CLEAN-PRE-EDA at F5' empirical-correlation), /049 IS the **third feature-family attempt of cycle-6** but pivots to **POSITIONING SENTIMENT data sourced from Binance Futures `/futures/data/topLongShortAccountRatio`** — structurally non-OHLCV, non-volume, non-microstructure-event-count.

---

## 1. Hypothesis (one-sentence)

A scale-invariant **top-trader long/short account ratio z-score over a 30-bar (10-day) window** — `long_short_zscore_30` — derived from the Binance Futures `topLongShortAccountRatio` REST endpoint (positioning sentiment via account-level long vs short aggregation), captures POSITIONING SENTIMENT REGIME SHIFTS (top-trader bullish→bearish transitions, capitulation extremes, contrarian fade signals) STRUCTURALLY ORTHOGONAL to the V1_FEATURE_COLUMNS_PRUNED 44-feature space (all 44 are kline-OHLCV-derived OR funding/OI-derived), and produces both (a) **top-15 importance at the portfolio level** AND (b) **IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 (+0.4767)**, demonstrating that top-trader positioning sentiment is an unexploited edge axis in v1's pooled-and-per-symbol Optuna search.

---

## 2. Chosen Feature

### `long_short_zscore_30` — z-score of `longShortRatio` over 30-bar (10-day) window

**Verbatim pandas formula (per-symbol, computed independently for each of BTC/ETH/LINK/LTC/DOT):**

```python
# Inputs: df has column ['long_short_ratio'] (joined from data/long_short_ratio/<SYMBOL>/8h.csv,
# aggregated from 4h API native cadence → 8h via mean of 2 consecutive 4h records).
# Output: df['long_short_zscore_30']
lsr = df['long_short_ratio'].astype(float)
lsr_mean_30 = lsr.rolling(window=30, min_periods=30).mean()
lsr_std_30 = lsr.rolling(window=30, min_periods=30).std()
df['long_short_zscore_30'] = (lsr - lsr_mean_30) / lsr_std_30
```

**Data source:** `GET https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol={SYMBOL}&period=4h`.

- Response array element: `{symbol, longAccount, longShortRatio, shortAccount, timestamp}`.
- `longShortRatio` ∈ (0, ∞); bullish positioning > 1.0, bearish < 1.0 (top trader account-count aggregation, NOT notional).
- API native cadence: 4h (8h NOT supported by endpoint).
- Per-symbol historical depth: ~30 days max per request; 500-record cap means MUST paginate via `startTime`/`endTime` for the full IS window 2021-03-24 → 2025-03-24 (5 years).
- **CRITICAL DATA-AVAILABILITY ASSUMPTION:** historical depth ≥ 12 months (ideally full 5-year IS window). **Verified at Phase 4.5 implementation, before Phase 5 brief.** See §13 below for the verification protocol and backup-axis pivot if depth insufficient.

**8h aggregation rule:** at 8h candle close `t`, aggregate the two 4h `longShortRatio` records with timestamps in `[t-8h, t)` via simple mean. If only 1 record available in window (missing data), forward-fill from prior 8h bar and tag a `data_quality_flag = stale_8h`. ≥2 consecutive stale flags → emit NaN for that 8h candle.

**Properties:**
- **Past-only construction.** The 4h `longShortRatio` record at `timestamp = t` is the snapshot AS OF that 4h close (already published before the next 4h bar opens); 8h aggregation at candle-close `t` uses only records with `timestamp < t`; rolling z-score at `t` uses 30 closed 8h bars ending at `t`. Decision at candle `t+1` uses `long_short_zscore_30[t]` — no look-ahead. Lag ≥1 8h bar verified at integration test.
- `min_periods=30` → first ~30 candles per symbol are NaN (~10 days warmup at 8h cadence).
- **Scale-invariant by construction** — z-score normalization is dimensionless.
- Window choice (30-bar / 10-day at 8h) anchors to `oi_delta_30_z90` / `funding_rate_zscore_30` — same primary-window cadence for cross-feature timescale consistency. (Window-convention parallel only; primitive is fundamentally different — `topLongShortAccountRatio` is positioning sentiment, NOT a kline field nor a funding/OI primitive.)

---

## 3. Rationale for Choice (vs alternatives)

The /048 ABORT taught that even the UNUSED kline primitive (`number_of_trades`) empirically co-moves with `vol_volume_rel_20` at |IC|=0.91. **The defense must escalate from "unused primitive" to "non-kline primitive entirely."**

Candidate non-kline data sources on Binance Futures:

| Option | Data source | Primitive class | Algebraic-sister to v1's 44 | Empirical-IC risk |
|---|---|---|---|---|
| **A: long_short_zscore_30** | `/futures/data/topLongShortAccountRatio` | Account-count positioning sentiment | NONE (positioning ≠ OHLCV ≠ funding ≠ OI) | Expected max \|IC\| < 0.20 (different data class entirely) |
| B: long_short_position_zscore_30 | `/futures/data/topLongShortPositionRatio` | Account-NOTIONAL positioning | NONE | Plausibly correlated with account-ratio variant; should not be tested in same iter |
| C: global_long_short_zscore_30 | `/futures/data/globalLongShortAccountRatio` | Retail-skewed account positioning | NONE | Same data class as A; sister to A within iter — pick one |
| D: taker_long_short_volume_zscore_30 | `/futures/data/takerlongshortRatio` | Taker FLOW ratio (volume side imbalance) | LOW — taker flow is volume-class adjacent; closer to `vol_taker_buy_ratio` | EXPECTED max \|IC\| ∈ [0.35, 0.65] vs vol_taker_buy_ratio (sister-of-different-window) |
| E: open_interest_velocity_30 (NEW formulation) | derived from open_interest primitive | Same primitive class as `oi_delta_30_z90` | MEDIUM — different transform of same primitive | EXPECTED max \|IC\| ∈ [0.30, 0.70] vs `oi_delta_30_z90` |
| F: funding_rate_change_30 | derived from funding_rate primitive | Same as funding_rate_zscore_30 | MEDIUM — different transform of same primitive | EXPECTED max \|IC\| ∈ [0.40, 0.75] vs `funding_rate_zscore_30` |

**Why A wins:** /047's lesson (algebraic-sister at |IC|=0.81) + /048's lesson (empirical co-movement at |IC|=0.91) both point at the same root cause: **the chosen feature shares its primitive class with existing v1 features.** Option A is the only candidate whose primitive class — **top-trader account-level positioning sentiment** — has ZERO representation in V1_FEATURE_COLUMNS_PRUNED. Options D/E/F all share primitive-class with at least one existing feature group. Options B/C share data class with A but should not be co-tested with A (one positioning-sentiment feature per iter; if A succeeds, B/C are candidates for /050+).

**The chosen feature uses ONE primitive of a class that does NOT appear ANYWHERE in V1_FEATURE_COLUMNS_PRUNED.** This is the structurally cleanest non-kline choice.

---

## 4. Orthogonality Rationale — What `long_short_zscore_30` CANNOT Correlate With By Construction

**By construction:**

1. **All 44 V1 features are functions of {OHLCV, funding_rate, open_interest, calendar}.** `longShortRatio` is computed by the exchange from per-account net position direction aggregation — completely independent of price/volume/range/funding/OI.
2. **Empirical correlation possible (NOT algebraic):** top-trader long positioning may correlate WEAKLY with realized returns (bullish positioning during uptrends) but the relationship is non-stationary and weak across symbols (BTC top traders are less reactive than alt-coin top traders per industry studies).

**Closest empirical-correlation candidates** (NOT algebraic sisters, weak couplers):

- `cross_btc_ret_*` family — if BTC top-trader positioning shifts ahead of price moves, the z-score may carry early-warning content correlated with realized BTC returns. Expected max |IC| ~ 0.10–0.25.
- `funding_rate_zscore_30` — top-trader positioning and funding rate are BOTH sentiment proxies but mechanically different (funding rate is mark-vs-index basis; long/short ratio is account-direction census). Expected max |IC| ~ 0.10–0.30.
- `mom_rsi_*` / `mr_zscore_*` — if extreme positioning correlates with overbought/oversold regimes. Expected max |IC| ~ 0.05–0.25.
- `oi_delta_30_z90` — OI changes encode aggregate leverage flow; account-ratio shifts encode directional consensus. Different signals; expected max |IC| ~ 0.05–0.25.

**Hard-zero correlation candidates by construction:** calendar features (cal_dow_norm, cal_hour_norm — no positioning content).

**Pre-registered F5' gate:** max |IC| < 0.30 IDEAL / ∈ [0.30, 0.60) ACCEPTABLE (document) / ≥ 0.60 ABORT-PRE-LAUNCH. **Tightened identically to /048's F5'** — the lesson is now codified at two consecutive ABORTs.

---

## 5. Falsifier Preview (F1–F5')

### F1 — Master (LightGBM importance — DUAL CONDITION)

**Claim:** `long_short_zscore_30` ranks TOP-15 of 45 features by mean-gain importance at the portfolio-aggregated level (averaged across Models A/C/D/E, weighted by per-model trade count) AND IS daily Sharpe Δ ≥ +0.05 vs BASELINE_V1 +0.4767 (i.e., observed IS daily Sharpe ≥ +0.5267).

**Rationale:** Either condition alone is insufficient:
- Importance without Sharpe lift → PROMISING-INERT (mechanical split allocation without net edge — iter-v3/019 pattern).
- Sharpe lift without importance → Optuna basin-lottery noise on existing 44 features, NOT the new feature.

Dual gate → PROMISING (sub-classified by F2/F3) on PASS; escalate on FAIL.

### F2 — IS Sharpe Δ Direction (clean PROMISING vs NEG-CLEAN)

**Claim:** IS daily Sharpe Δ vs BASELINE_V1 +0.4767:

| IS Δ band | Verdict subtype |
|---|---|
| ≥ +0.05 | PROMISING-CLEAN (if F5' PASS with max \|IC\| < 0.30) or PROMISING-WITH-CORRELATED-PRIMITIVE (if max \|IC\| ∈ [0.30, 0.60)) |
| -0.05 < Δ < +0.05 | NEG-INERT (feature is benign; tied to baseline within noise) |
| ≤ -0.05 | NEG-CLEAN (actively harms IS — iter-v3/023 inert-features-at-higher-budget pattern; positioning sentiment carries no incremental edge AND steals split-budget) |

### F3 — OOS Δ (forensic-only, per /046+/047+/048 discipline)

**Claim:** OOS daily Sharpe Δ vs BASELINE_V1 +1.1913 — REPORTED in comparison.csv but NOT a /049 success criterion. OOS-aware selection is a leak path; /049 preserves /046's discipline.

### F4 — ADF Stationarity (pre-EDA gate)

**Claim:** `long_short_zscore_30` is stationary across all 5 v1 symbols at the IS-window upper bound — ADF p-value < 0.05 with `regression='c'`, `maxlag=10`. VERIFIED in IS-only pre-EDA BEFORE backtest launch.

**Interpretation:**
- 5/5 PASS → V1_FEATURE_COLUMNS_PRUNED stationarity invariant preserved.
- 4/5 PASS → INVESTIGATE; borderline (p ∈ [0.05, 0.10]) document and proceed; hard fail (p > 0.10) redesign window or NaN-mask that symbol.
- ≤3/5 PASS → ABORT pre-launch.

**Rationale:** Account-ratio is intrinsically positive; its z-score over a 30-bar window standardizes by local mean+std and should be stationary in standard regimes. Halving / bull-bear regime non-stationarity unlikely to bite at 10-day window — local normalization absorbs slow drift.

### F5' — IC Orthogonality vs Existing 44 Features (TIGHTENED — second consecutive codification)

**Claim:** Max absolute pairwise Pearson IC of `long_short_zscore_30` vs ALL 44 features in V1_FEATURE_COLUMNS_PRUNED is BELOW the F5' band threshold — measured on IS-only data, pooled across all 5 symbols (sample-weighted by per-symbol IS row count).

**F5' bands:**

| max \|IC\| | F5' status | Action |
|---|---|---|
| < 0.30 | PASS — orthogonal | Proceed to launch as PROMISING-CLEAN-eligible |
| [0.30, 0.60) | DOCUMENT | Proceed to launch; Section 2 flags offending pair; PROMISING-WITH-CORRELATED-PRIMITIVE subtype if F1 PASS |
| ≥ 0.60 | **ABORT-PRE-LAUNCH** | NEG-CLEAN-PRE-EDA route — feature retired pre-launch; QR pivots |

**Special-attention features (Section 5 IC pre-EDA must explicitly list):**

- `funding_rate_zscore_30/90` — both sentiment-class proxies; theoretical weak coupling.
- `cross_btc_ret_*` — positioning often shifts with BTC trend.
- `mom_rsi_*` / `mr_zscore_*` — overbought/oversold may correlate with positioning extremes.
- `oi_delta_30_z90` — leverage-flow proxy, related but mechanically distinct.

**Rationale:** Two consecutive ABORTs (/047 algebraic-sister, /048 empirical-correlation) demonstrate that this gate is load-bearing. /049 inherits the tightened band identically.

---

## 6. Data Fetcher Requirements (NEW — per non-kline data source)

This iter adds a **new data fetcher and storage path** to v1 — first time in cycle-6. Phase 4.5 implementation work BEFORE Phase 5 brief:

### 6.1 Fetcher module — `src/crypto_trade/long_short_fetcher.py`

```python
# Skeleton (Phase 6 implementation):
def fetch_long_short_ratio(
    symbol: str,
    start_ms: int,
    end_ms: int,
    period: str = "4h",  # API only supports 5m/15m/30m/1h/2h/4h/6h/12h/1d; 8h NOT supported
    out_dir: Path = Path("data/long_short_ratio"),
) -> int:
    """
    Paginate /futures/data/topLongShortAccountRatio across the [start_ms, end_ms] window,
    storing rows in data/long_short_ratio/<SYMBOL>/4h.csv with schema:
        timestamp_ms, long_account, long_short_ratio, short_account
    Pagination: 500 records/request → ~83 days/request at 4h. Loop until end_ms reached.
    Rate limit: same Binance Futures public-endpoint pool (~2400 weight / 1 min); pause 0.25s between calls.
    Incremental: reads existing CSV last timestamp, appends from there.
    """
```

### 6.2 8h aggregation module — `src/crypto_trade/features_v1/long_short.py`

```python
def aggregate_4h_to_8h(symbol: str) -> pd.DataFrame:
    """
    Read data/long_short_ratio/<SYMBOL>/4h.csv;
    aggregate 2 consecutive 4h records → 1 8h record via mean;
    align to 8h kline boundaries (00, 08, 16 UTC).
    Output: data/long_short_ratio/<SYMBOL>/8h.csv with schema:
        timestamp_ms, long_short_ratio_8h, n_records_in_window, data_quality_flag
    """

def compute_long_short_zscore_30(df_8h: pd.DataFrame) -> pd.Series:
    """Rolling 30-bar z-score over long_short_ratio_8h."""
```

### 6.3 CLI integration — `src/crypto_trade/main.py`

```bash
uv run crypto-trade fetch-long-short \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT \
  --start 2021-03-24 --end 2026-06-01
```

### 6.4 Feature dispatch integration

In `features_v1/__init__.py`:
- Read `data/long_short_ratio/<SYMBOL>/8h.csv` via `read_long_short_8h(symbol)`.
- LEFT JOIN on kline DataFrame by `open_time` → `long_short_ratio` column.
- Compute `long_short_zscore_30` per Section 2 formula.
- Add to `V1_FEATURE_COLUMNS_PRUNED` (44 → 45).

### 6.5 Test gap

- `tests/test_long_short_fetcher.py` — pagination loop coverage; rate-limit pause; idempotent re-run; CSV schema.
- `tests/test_long_short_aggregation.py` — 4h → 8h aggregation correctness; stale-flag handling; NaN propagation.
- `tests/test_long_short_feature.py` — past-only verification; NaN-mask warmup; ADF dummy validation; join correctness against synthetic kline parquet.

---

## 7. Per-Symbol Historical Depth Assumption — VERIFY PRE-IMPL (LOAD-BEARING)

**The single load-bearing pre-implementation check.** If `topLongShortAccountRatio` historical depth is shallower than the IS window 2021-03-24 → 2025-03-24, the feature can only contribute to a PROPER SUBSET of the IS window. Three possible scenarios:

| Scenario | Available depth | Disposition |
|---|---|---|
| **S1 — Full depth (≥ 2021-03-24 for all 5 symbols)** | 5 years all symbols | Proceed with `long_short_zscore_30` as primary feature. Standard /049 flow. |
| **S2 — Partial depth (12-36 months for all 5 symbols)** | e.g., earliest 2023 | The feature is NaN for IS pre-availability years. Optuna training-window LightGBM handles NaN via histogram-binning; LightGBM does NOT REJECT samples with NaN in a feature column — it routes NaN to the dominant child at each split, partially preserving signal contribution after the feature becomes available. **Proceed with documentation: brief Section 2 reports per-symbol availability dates; comparison.csv must record both (a) full-IS-window IS Sharpe and (b) availability-restricted IS Sharpe (IS subset from earliest-availability-date forward) for direct attribution.** |
| **S3 — Insufficient depth (< 12 months for any symbol)** | e.g., only OOS coverage | **PIVOT to backup axis `funding_rate_momentum_30`** per §10. /049 brief is then re-anchored on the backup axis with a different feature, formula, and orthogonality story. |

**Verification protocol (Phase 4.5, BEFORE Phase 5 brief):**

```bash
# One-time historical-depth probe per symbol:
for SYM in BTCUSDT ETHUSDT LINKUSDT LTCUSDT DOTUSDT; do
    curl -s "https://fapi.binance.com/futures/data/topLongShortAccountRatio?symbol=${SYM}&period=4h&limit=500" \
      | jq '.[0].timestamp, .[-1].timestamp' > /tmp/depth_check_${SYM}.txt
done
# Then attempt a backward-paginated request with startTime = 2021-03-24 ms; observe whether the endpoint
# returns the requested historical window or truncates to most-recent records.
```

**Decision rule:** if ALL 5 symbols return data from ≥ 2024-03-24 → proceed (S2). If ANY symbol returns < 12 months of history → pivot to S3 backup axis.

**Why S2 (partial depth) is acceptable:** the feature does NOT need full IS-window depth to demonstrate edge contribution. If the feature contributes positively to the LATTER PART of IS (after availability date), that is direct evidence the feature carries signal in v1's training regime. The downside is reduced IS sample size for the feature — Optuna may give it less importance weight than if it were available for the full 5 years. Brief Section 2 must report restricted-IS-window numbers honestly to inform the F1/F2 evaluation.

---

## 8. Pre-EDA Outputs (Section 9 deliverables)

`analysis/iteration_v1-049/` script + CSV deliverables PRE-BACKTEST:

1. **`long_short_zscore_30_definition.py`** — verbatim pandas formula (§2 above) committed before launch.
2. **`historical_depth_per_symbol.csv`** — per symbol: earliest available 4h `timestamp`, total records available, in years. Schema: `symbol, earliest_ts_ms, earliest_date_utc, n_records, years_available, scenario_label`. 5 rows. **This file is the §7 decision input.**
3. **`adf_stationarity_per_symbol.csv`** — ADF p-value per symbol × `long_short_zscore_30` (over IS-restricted-to-available-window). Schema: `symbol, n_obs, adf_stat, adf_pvalue, lag_used, pass_at_005`. 5 rows.
4. **`distribution_stats_per_symbol.csv`** — IS-only distribution stats (over availability-restricted window): mean, std, skew, kurtosis, 5/25/50/75/95 percentile of `long_short_zscore_30`. 5 rows × 9 cols.
5. **`ic_orthogonality_sentiment_class.csv`** — Pearson IC of `long_short_zscore_30` vs the 6 conjectured weak-coupler features (funding_rate_zscore_30, funding_rate_zscore_90, cross_btc_ret_5, cross_btc_ret_20, mom_rsi_14, oi_delta_30_z90). 6 rows × 3 cols.
6. **`ic_orthogonality_full_44.csv`** — Pearson IC of `long_short_zscore_30` vs ALL 44 V1_FEATURE_COLUMNS_PRUNED features. 44 rows × 2 cols. **Max |IC| from this file is the F5' gate input.**
7. **`f4_f5_gate_outcomes.md`** — explicit PASS/FAIL gate documentation with quoted critical values.

All 7 outputs MUST be committed BEFORE Phase 6 backtest launch. F4 and F5' gates evaluated from these files.

---

## 9. Risk Plan (Section 6 of full brief)

**R1 (importance-rank robustness):** F1's TOP-15-of-45 portfolio-level threshold unchanged from /047+/048.

**R2 (IS Sharpe lift floor +0.05):** unchanged from /047+/048.

**R3 (NEG-CLEAN routing if active harm):** F2 NEG-CLEAN band → RETIRE `long_short_zscore_30` to V1_RETIRED_FEATURE_COLUMNS at /049 closeout. Feedback rule candidate: "non-kline cross-asset positioning sentiment features are NOT additive at v1's 18-trial EXPLORATION budget."

**R4 (ADF stationarity gate F4 PRE-LAUNCH):** if F4 fails 2+ symbols, REVISE brief before Phase 6 launch.

**R5' (IC orthogonality gate F5' PRE-LAUNCH — TIGHTENED):** if max |IC| ≥ 0.60, ABORT-PRE-LAUNCH (NEG-CLEAN-PRE-EDA — third consecutive if it fires). If max |IC| ∈ [0.30, 0.60), DOCUMENT and proceed with PROMISING-WITH-CORRELATED-PRIMITIVE eligibility flagged.

**R6 (BASELINE_V1 risk-stack unchanged):** /049 inherits BASELINE_V1's risk stack unchanged. New feature added to V1_FEATURE_COLUMNS_PRUNED but NOT V1_OOD_FEATURE_COLUMNS.

**R7 (NORMAL-RISK declaration — Section 2.5):** Feature ADDITION; Optuna training objective UNCHANGED; training window UNCHANGED; symbol universe UNCHANGED; model architecture UNCHANGED. **NORMAL-RISK** per v1 HIGH-RISK criterion definition.

**R8 (NEW for /049 — data-source operational risk):** Binance public endpoint rate limits (~2400 weight/min), occasional 429 throttling, occasional gaps in historical data (especially LTC/DOT pre-2022). Fetcher implements 0.25s pause + exponential backoff + idempotent re-run; storage CSV is checked for `n_records` per month to detect missing-data periods.

**R9 (NEW for /049 — partial-depth honesty):** brief Section 2 must report BOTH full-IS-window IS Sharpe AND availability-restricted IS Sharpe. F1/F2 evaluated on the FULL-window numbers (the eval lens v1 catalog uses) — the availability-restricted numbers are forensic context, NOT alternative-success criteria.

---

## 10. Backup Axis — `funding_rate_momentum_30` (Activated IF S3)

If §7 verification finds **<12 months historical depth on any of the 5 symbols**, /049 pivots to a backup axis using a primitive class already represented in V1_FEATURE_COLUMNS_PRUNED but with a DIFFERENT TRANSFORM than the existing z-score.

### 10.1 Backup feature — `funding_rate_momentum_30`

**Formula:**
```python
fr = df['funding_rate']
df['funding_rate_momentum_30'] = fr - fr.shift(30)
```

Difference (level shift) over 30 bars, NOT z-score normalization.

### 10.2 Orthogonality story for backup

- `funding_rate_zscore_30` already exists; the new feature uses the SAME primitive but a DIFFERENT operation: **directional momentum/velocity** vs **statistical centering**.
- Expected |IC| with `funding_rate_zscore_30`: empirically these are NOT algebraic sisters (one is `(x - mean)/std`, other is `x - x.shift(30)` — share the `x` series but at different lag relationships). Plausible empirical |IC| ∈ [0.40, 0.70].
- **F5' RISK FOR BACKUP IS NON-TRIVIAL.** Backup is the SECOND-TIER candidate precisely because it uses an existing primitive. If primary (long_short) is unavailable, /049 runs the backup KNOWING the F5' gate may fire — and that NEG-CLEAN-PRE-EDA-BACKUP is a plausible outcome.

### 10.3 Why backup is NOT the primary

If the long_short data depth check passes (≥12 months on all 5 symbols), the primary is STRUCTURALLY CLEANER (non-kline-class) and has higher expected F5' PASS probability than the backup (same-primitive-class). The backup is the operational-fallback, NOT the design-preferred choice.

---

## 11. Wall-Clock Budget

**Total: ≤ 3.0h** (raised from /048's 2.5h to accommodate fetcher implementation and data download).

| Phase | Wall-clock | Notes |
|---|---|---|
| §7 historical-depth verification (5 API calls + manual review) | 5-10 min | Decision: S1/S2/S3 routing |
| Fetcher + aggregator implementation (Phase 4.5) | 30-45 min | `long_short_fetcher.py` + `features_v1/long_short.py` + 3 test files |
| 4h historical data download (5 symbols, paginated, ~83 days/page) | 20-40 min | depends on depth; 5 yrs × 5 syms × ~22 pages = 110 API calls + rate-limit pauses |
| Pre-EDA §8 deliverables (ADF + IC sweep + dist stats + depth report) | 15-20 min | scipy rolling + ADF + IC matrix |
| Feature regen (V1_FEATURE_COLUMNS_PRUNED + long_short_zscore_30) | ~30 min | `crypto-trade features --track v1 --workers 4` |
| Optuna backtest (5 cohorts × monthly retrain × 18 trials × 3 EXPLORATION seeds × ENSEMBLE_SIZE=3) | ≤ 2h | EXPLORATION default per v1 |
| Reports + comparison.csv + diary + closeout | 15-20 min | standard cadence |

**Wall-clock cap:** 3.0h HARD. If F4 or F5' fails pre-launch, the iteration is RESOLVED at the EDA stage (NEG-CLEAN-PRE-EDA — third consecutive if it fires) and /050 pre-brief authored. Cycle-6 axis-rotation discipline at /050 will mandate a DIFFERENT axis family (since /046/047/048/049 are all axis: feature-family — three are NEG-CLEAN-PRE-EDA and /046 was methodology) — likely model-arch or labeling.

---

## 12. Pre-EDA Anticipated F1/F2/F4/F5' Outcome Distribution

| Outcome | Prior | Reasoning |
|---|---|---|
| **PROMISING-CLEAN** (F1 PASS + F5' max \|IC\| < 0.30) | 20-30% | Non-kline-class primitive has HIGHER F5' PASS prior than /047 (algebraic sister) or /048 (empirical co-movement). Positioning sentiment data is genuinely structurally different. F1 PASS is the harder gate — top-trader positioning may carry edge but its v1-incremental contribution depends on whether existing 44 features already span sentiment regimes. |
| **PROMISING-WITH-CORRELATED-PRIMITIVE** (F1 PASS + F5' max \|IC\| ∈ [0.30, 0.60)) | 15-25% | Funding_rate_zscore is the closest empirical correlate; if positioning lead-lags funding by 1-3 bars at 8h cadence, |IC| may reach 0.40-0.55. PROMISING-WITH-CORRELATED-PRIMITIVE is the second-modal PROMISING branch. |
| **NEG-INERT** (IS Δ ∈ (-0.05, +0.05); rank possibly > 15) | 25-35% | Top-trader positioning sentiment may be MORE noisy than literature suggests — Binance top-100 traders are not a uniform proxy for institutional flow. Feature may add no incremental edge at 18-trial EXPLORATION budget. MODAL outcome alongside NEG-CLEAN. |
| **NEG-CLEAN** (IS Δ ≤ -0.05) | 10-20% | Same v3 inert-features-at-higher-budget pattern as /048: weak feature with moderate IC steals split-budget from genuinely orthogonal features. |
| **NEG-CLEAN-PRE-EDA (F5' ABORT max \|IC\| ≥ 0.60)** | 5-10% | LOWER than /048's 5-10% prior because the data class is genuinely different from any existing v1 feature. Risk remains if positioning correlates with funding_rate_zscore_30 at unexpected magnitude. |
| **BLOCK-PENDING-FIX** (src/ code defect at Critic Phase 7.5; F4 hard fail; OR §7 S3 pivot to backup ALSO ABORTs) | 10-15% | NEW data infrastructure adds defect surface (fetcher pagination bug, join key mismatch, 8h aggregation boundary error). F4 catches stationarity defect. F5' catches IC defect. §7 backup-axis pivot is an additional contingency. |

These priors hardened in Phase 5 brief Section 7 after pre-EDA + historical-depth verification.

---

## 13. Section Pre-Fills for Phase 5 Brief

| Brief section | Pre-filled content |
|---|---|
| 0.0 — Banner | EXPLORATION; cycle-6 4/10; axis `feature-family`; anchor BASELINE_V1; NON-KLINE-CLASS defense post-/048 |
| 0.5 — Type + Cadence | EXPLORATION; cycle-6 4/10 (after /046 1/10 methodology PROMISING-DIVERGENCE, /047 2/10 feature-family ABORT-PRE-EDA, /048 3/10 feature-family ABORT-PRE-EDA); cycle-5+6 precedents cited |
| 0.6 — Axis family + rotation | `feature-family`; VALID — prior 5 EXPLORATIONs span (/043 per-cohort×labeling, /045 bundle-substrate, /046 methodology, /047 feature-family, /048 feature-family); three consecutive feature-family attempts is the cycle-6 mandate per Critic Path Forward; if /049 ABORTs or NEG-CLEAN, /050 MUST rotate to model-arch or labeling per axis-rotation discipline |
| 1 — Hypothesis | §1 verbatim |
| 2 — IS-only Numerical Evidence | EDA tables from §8 deliverables: historical depth per symbol, ADF, distribution stats, IC vs sentiment-class + full-44; max \|IC\| value; F4/F5' pre-launch gate outcomes; availability-restricted vs full-IS IS Sharpe (per R9) |
| 2.5 — HIGH-RISK | NORMAL-RISK per §9 R7 |
| 3 — Proposed Changes + LM Master | (a) `src/crypto_trade/long_short_fetcher.py` — NEW fetcher module per §6.1, (b) `src/crypto_trade/features_v1/long_short.py` — NEW aggregator+feature module per §6.2, (c) `src/crypto_trade/main.py` — NEW `fetch-long-short` CLI subcommand per §6.3, (d) `src/crypto_trade/features_v1/__init__.py` — add `long_short_zscore_30` to V1_FEATURE_COLUMNS_PRUNED (44→45), join logic, (e) `data/long_short_ratio/<SYMBOL>/{4h,8h}.csv` — NEW storage path, (f) `tests/test_long_short_*.py` — 3 NEW test files per §6.5, (g) `run_iteration_049.py` — runner with `feature_columns=list(V1_FEATURE_COLUMNS_PRUNED)`. LM Master Phase 4.5 invocation: feature-family axis — LM Master typically returns 2-4 HP recommendations + 1-2 feature ideas; brief Section 3 must address each. |
| 4 — Falsifier | F1–F5' from §5 verbatim |
| 5 — Wall-clock | ≤ 3.0h — §11 |
| 6 — Risk Mitigation | R1–R9 from §9 (R8 + R9 are NEW for /049) |
| 7 — Pre-registered Failure-Mode Prediction | §12 priors, refined after pre-EDA + depth verification |
| 8 — MERGE/NO-MERGE | EXPLORATION verdict only (PROMISING-CLEAN / PROMISING-WITH-CORRELATED-PRIMITIVE / NEG-INERT / NEG-CLEAN / NEG-CLEAN-PRE-EDA / BLOCK-PENDING-FIX); NO MERGE at /049 by EXPLORATION budget convention |
| 9 — Smoke test | Engineering report MUST emit (a) historical depth per symbol, (b) ADF table 5/5 pass, (c) distribution stats per symbol, (d) IC sweep sentiment-class + full-44, (e) F4/F5' gate outcomes, (f) long_short_zscore_30 importance rank at portfolio + per-cohort, (g) IS Δ + OOS Δ comparison.csv, (h) availability-restricted vs full-IS attribution, (i) integration test confirming fetcher → 4h CSV → 8h aggregation → feature join → kline pin |

---

## 14. Honesty Discipline

Per THE PRIME DIRECTIVE: this outline does NOT pre-judge the outcome. The EDA designs the experiment; the experiment resolves what the EDA cannot.

- **PROMISING** branches authorize NO MERGE at /049; multi-seed CONFIRMATION at /049+1 cycle slot is required.
- **NEG-INERT** is one of two MODAL priors — substantive inventory finding documenting that top-trader positioning sentiment is NOT additive at v1's EXPLORATION budget.
- **NEG-CLEAN** documents active harm; triggers RETIRE + feedback rule "non-kline-class positioning sentiment features NOT additive at v1 EXPLORATION budget."
- **NEG-CLEAN-PRE-EDA** would be the THIRD CONSECUTIVE pre-EDA ABORT and a strong signal that cycle-6 feature-family axis is saturated; /050 MUST rotate to a different family (model-arch, labeling, risk-primitive).
- **BLOCK-PENDING-FIX** is the only true process-failure path — src/ defect or F4 hard fail — corrected with one re-run cycle per v1 single-rerun discipline. NEW data infrastructure makes BLOCK marginally more likely than /048 (data fetcher pagination, 8h-aggregation boundary edge cases).
- **§7 S3 backup pivot** is operationally a brief re-anchor; if backup ALSO ABORTs at F5' (plausible given its same-primitive class), /049 is the strongest possible saturation signal for the entire feature-family axis at v1's current scope.

---

## 15. /049 Disposition Recommendation

**Recommendation:** RUN. The non-kline-class defense is the cleanest possible response to /048's lesson; the hypothesis is genuinely uncertain (F1 PASS combined PROMISING prior ~35-55%; NEG-modal prior ~35-55%); F4/F5' pre-launch gates protect against pathological feature additions BEFORE backtest compute is spent; §7 depth verification protects against unworkable data.

**Sequencing:**
- /049 strictly precedes /050.
- If /049 PROMISING-anything, /050 either deepens with multi-seed CONFIRMATION (rare at EXPLORATION budget) OR considers a SECOND non-kline-class feature (e.g., `taker_long_short_volume_zscore_30` from `/futures/data/takerlongshortRatio` OR `open_interest_velocity` from a different OI transform).
- If /049 NEG-anything or NEG-CLEAN-PRE-EDA, /050 MUST rotate to a different axis family (model-arch, labeling, risk-primitive) per axis-rotation discipline — three consecutive feature-family attempts mark the family saturated at v1's current scope.

---

*End of /049 pre-brief outline.*
