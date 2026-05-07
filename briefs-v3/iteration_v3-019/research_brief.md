# Iteration v3-019 — Research Brief

**Type**: EXPLORATION (FIRST POST-BOOTSTRAP EXPLORATION; cadence #1 of 10 in the new cycle; **STRUCTURAL axis (NOT a gate-threshold knob)** — first NEW feature family with NEW external data source in v3 catalog per `feedback_v3_iter019_axis_priorities.md` LOCKED 2026-05-07 + `feedback_structural_over_knob_exploration.md`)
**Track**: v3 (rigor arm) — nineteenth iteration
**Branch**: `iteration-v3/019` (off `iteration-v3/018` head; analysis commit `95858cb` ships before this brief)
**Date**: 2026-05-07
**Author**: QR (autopilot)

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE (shared across v1, v2, v3)
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 1              # SET BY --exploration
ensemble_seeds   = _derive_ensemble_seeds(outer_seed, size=1)
n_trials         = 10             # SET BY --exploration default
colsample_bytree = 1.0             # HARDCODED by --exploration
OOS_CUTOFF_MS    = 1742774400000   # millisecond representation
```

**Sacred constants UNCHANGED.** The QR sees OOS metrics for the FIRST time in Phase 7. This brief is produced reading ONLY: iter-v3/007–018 briefs / engineering reports / Critic / diaries; iter-v3/019 analysis script `analysis/iteration_v3-019/funding_rate_eda.py` outputs (committed at SHA `95858cb` BEFORE this brief). The analysis script reads ONLY pre-OOS-cutoff data sliced from `data/{BCH,LDO,TRX}USDT/8h.csv` raw klines + `data/funding_rates/<SYM>.csv` (locally-cached from /fapi/v1/fundingRate; the kline match is on candle open_time, past-only by construction) + `data/features_v3/*.parquet` (for IC orthogonality) — no OOS contamination at brief time.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION (FIRST POST-BOOTSTRAP EXPLORATION; cadence clock RESTARTED at iter-v3/018)
Wall-clock budget: < 30 min target / 2h hard cap
Single-axis variation: NEW feature family with NEW external data source — `funding_rate_zscore_30` added (V3_FEATURE_COLUMNS 13 → 14)
Cadence: EXPLORATION #1 of 10 needed before next CONFIRMATION (earliest = iter-v3/028)
Axis category: 1 (NEW feature family — cross-section funding/carry)
ANCHOR: iter-v3/018 BOOTSTRAP baseline (multi-seed mean +0.3788 IS / +0.3869 OOS) — NOT iter-v3/013 single-seed (FALSIFIED at iter-v3/018)
NOT a gate-threshold knob. NOT a feature-pruning variation. NOT a universe change. NOT a labeling change. NOT a model architecture change.
This iteration NEVER updates BASELINE_V3.md.
```

**Justification — STRUCTURAL axis pivot (per `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_structural_over_knob_exploration.md`)**:

After iter-v3/018 BOOTSTRAP CONFIRMATION (Critic FINAL SHA `199cbe4`):
- Multi-seed mean IS Sharpe = +0.3788 (gate 1 floor +1.0 missed by **0.62**)
- Multi-seed mean OOS Sharpe = +0.3869 (gate 2 floor +1.0 missed by **0.61**)
- iter-v3/013 single-seed +1.0088/+2.6970 was formally FALSIFIED (62% IS / 86% OOS reduction)
- 6 of 10 pre-registered MERGE gates FAILED
- Both Pareto seeds positive (Gate 10 PASS — methodology bright spot, not edge)
- The 4 PROMISING components from the prior 10-EXPLORATION cycle (007/010/011/013) are ALREADY cumulatively integrated in the iter-v3/018 baseline; iter-v3/013 falsified means **NO surviving "PROMISING signal" exists to bundle additively**

The locked priority order from `feedback_v3_iter019_axis_priorities.md`:

1. **HIGH — NEW feature families** (top priority — iter-v3/019 first EXPLORATION axis): order-book microstructure beyond `tbr_zscore_30` (CLOSED for re-introduction per iter-v3/015 `feedback_promising_mechanical_subtype.md`-adjacent caveat; same family proven INERT at rank 14/14), funding-rate momentum/percentile features (Binance fundingRate API), on-chain proxy features. Bias toward economically-interpretable features. **Unique lever capable of +0.6 Sharpe lift.**
2. HIGH — Concentration architecture (deferred to iter-v3/020+ for clean per-iteration single-axis discipline)
3. MEDIUM — DSR gate reformulation
4. MEDIUM — TRX/2022-Q4 regime gate
5. LOW — Knob axes (saturated)
6. LOW — Universe expansion (deferred)

**iter-v3/019 first EXPLORATION axis = NEW feature family.** Cannot be renegotiated post-hoc by future Engineer or QR per `feedback_v3_iter019_axis_priorities.md` lock.

**Why funding-rate z-score (over alternatives — order-book microstructure, on-chain, OI delta, basis spread)**:

- **Crypto-native + economically interpretable foundation** (per `feedback_structural_over_knob_exploration.md` Rule #1 axis priority — funding rate is the canonical economic primitive of perpetual-futures markets): Binance Futures funding rate is the periodic settlement payment between long and short holders that anchors the perpetual mark price to spot. Persistent positive funding = leveraged longs paying shorts → mean-reversion / liquidation pressure signal. Per BIS WP 1087 (2025), 10% carry shock → 22% liquidation jump. Mechanism is structural, not statistical.
- **8h cadence aligns EXACTLY with v3 kline boundaries (00/08/16 UTC)**: one funding period = one v3 candle. Feature value at candle close is funding-cycle-aligned, not phase-shifted noise. This is the SAME reason 8h was chosen for v3 in the first place (`Spine §4 Crypto-Native Alpha Sources` "Why 8h Is Special" #1 funding-cycle alignment).
- **Data availability VERIFIED at SHA `95858cb`** (Section 2.1 below): BCH from 2019-12-19 (kline 2020-01-01); LDO from 2022-09-22 (kline same day); TRX from 2020-01-15 (kline same day). 100% kline alignment on all 3 symbols across IS+OOS extent. NO infrastructure gap.
- **Orthogonal axis verified at SHA `95858cb`** (Section 2.3 below): max |IC| vs the 13 V3_FEATURE_COLUMNS = 0.3758 (TRX vs vwap_dev_20) — well below the 0.50 strict brief target and the 0.70 hard gate. Per-symbol max |IC|: BCH 0.2192, LDO 0.2417, TRX 0.3758. The 13 V3 features are price/return/regime/volume-derived; funding rate carries POSITION/LEVERAGE information not present in any existing v3 feature. **Feature is structurally novel — orthogonal information channel.**
- **Why funding-rate z-score over `tbr_zscore_30` family revival**: iter-v3/015's `tbr_zscore_30` failed at rank 14/14 across all 3 symbols (model demonstrably did not learn the feature; same-feature-family failure). Microstructure features same-as-existing-volume failed once; per `feedback_v3_iter019_axis_priorities.md`, microstructure beyond tbr is acceptable but funding rate is recommended FIRST. Funding rate carries information that microstructure cannot — it captures DERIVATIVES MARKET POSITIONING not visible in spot order flow.
- **Why funding-rate over OI delta or basis spread**: data tractability. Funding rate has a single `/fapi/v1/fundingRate` endpoint with per-symbol pagination (1000 per request) — verified at SHA `95858cb` (~7 pages per 6-year symbol). Open Interest has `/fapi/v1/openInterestHist` but only **30-day rolling window** in the public API (insufficient for the 24-month IS training window without complex backfill engineering). Basis spread requires dual-leg data (perp mark + spot index) — adds two fetch paths and reconciliation. Funding rate is the cheapest tractable axis fitting the 2h EXPLORATION wall-clock cap.
- **Single-feature axis discipline**: One new feature added to V3_FEATURE_COLUMNS (13 → 14). Preserves single-axis EXPLORATION discipline per `feedback_structural_over_knob_exploration.md` counter-rule explicit statement (single-axis ≠ single-knob; one new feature is structural single-axis).

After iter-v3/019 the catalog will have: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 (CLOSED) + NEW feature family microstructure × 1 (CLOSED-narrow per iter-v3/015) + NEW model architecture × 1 (CLOSED-at-config per iter-v3/016) + NEW labeling architecture × 1 (PATH C deferred per iter-v3/017) + bootstrap CONFIRMATION × 1 + **NEW feature family with NEW external data source (funding rate) × 1** = 11 unique axis representations after iter-v3/019, **first NEW-external-data-source feature axis in v3 catalog**.

---

## Section 1 — Hypothesis

Adding `funding_rate_zscore_30` (z-score over rolling 30 funding-cycle window of Binance Futures funding rate) as a 14th feature on top of the iter-v3/018 multi-seed BOOTSTRAP baseline (drop-MKR + z=2.0 + ATR 2.0/1.0 + BTC ±15% + ADX=20 + 13 V3_FEATURE_COLUMNS) will produce IS Sharpe lift of **+0.20 (median)** over the iter-v3/018 anchor +0.3788 (predicted IS Sharpe band [+0.45, +0.85]) by giving the LightGBM model a derivatives-market-positioning regime-classifier signal — funding-rate z-score captures persistent leveraged-long/short positioning crowding, structurally orthogonal to the existing 13 features (max |IC| = 0.3758 with vwap_dev_20, well below 0.50 strict brief target) and carrying non-trivial directional rank-IC vs forward returns (TRX 7-bar -0.0485; LDO 7-bar -0.0234; BCH 3-bar -0.0194 — all NEGATIVE-direction = funding-tail mean-reversion signal).

**Mechanism explanation** (why funding rate should add edge): in perpetual-futures markets, the funding rate paid every 8h reflects derivatives-market net positioning. **Persistent positive funding** = leveraged longs paying shorts; the sustained positive carry is empirically associated with mean-reversion pressure as longs unwind during stress (BIS WP 1087, 2025: 10% carry shock → 22% liquidation jump). **Persistent negative funding** = leveraged shorts paying longs; can signal capitulation extreme or sustained bearish positioning whose unwinding produces upside squeezes. Z-scoring over a 30-bar rolling window normalizes per-symbol/per-regime baselines (TRX historically funds higher than BCH; LDO has bipolar episodes around LDO/Lido protocol news) — making the feature scale-invariant and pooled-multi-symbol-friendly per the project's "scale-invariant features" rule.

The mixed-sign rank-IC across symbols and horizons (TRX 7-bar -0.0485, LDO 7-bar -0.0234, BCH 3-bar -0.0194 — all NEGATIVE-direction at the strongest signal point) is NOT a sign-conflict — it is the EXPECTED mean-reversion direction (high funding → low forward return). LightGBM trees split bipolarly without preference; per-symbol architecture lets each model's tree splits learn its own threshold + interaction structure with the existing 13 features (e.g., funding-high AND low-vol = strong mean-reversion; funding-high AND high-vol = noisy fade).

**Direction symmetry**: funding rate is naturally bipolar (positive z = long-leverage crowding, negative z = short-leverage crowding). Per-symbol architecture means each model's LightGBM tree splits bipolarly without forced sign.

---

## Section 2 — IS-Only Numerical Evidence + Behavioral-Effect Predictor

**Analysis script**: `analysis/iteration_v3-019/funding_rate_eda.py` (committed at SHA `95858cb` BEFORE this brief — Phase 5.5 reproducibility requirement).

**Inputs read** (IS window only — pre-OOS_CUTOFF_DATE 2025-03-24):
- `data/funding_rates/{BCH,LDO,TRX}USDT.csv` — locally-cached funding rate data fetched from /fapi/v1/fundingRate (script fetches if cache missing; data/ is gitignored, regenerable from re-run)
- `data/{BCH,LDO,TRX}USDT/8h.csv` — 8h kline data for close prices and open_time alignment
- `data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet` — for IC orthogonality vs 13 V3_FEATURE_COLUMNS

**Outputs** (committed alongside the script at SHA `95858cb`):
- `analysis/iteration_v3-019/funding_eda_coverage.csv` — IS-window coverage per symbol + funding-kline alignment
- `analysis/iteration_v3-019/funding_eda_distribution.csv` — distribution stats (raw + z-score) per symbol
- `analysis/iteration_v3-019/funding_eda_correlation.csv` — Spearman IC vs 13 V3_FEATURE_COLUMNS (39 rows = 3 symbols × 13 cols)
- `analysis/iteration_v3-019/funding_eda_rankic.csv` — Spearman rank-IC vs forward returns (9 rows = 3 syms × 3 horizons)
- `analysis/iteration_v3-019/funding_eda_adf.csv` — ADF stationarity test results
- `analysis/iteration_v3-019/funding_eda_saturation.csv` — saturation predictor anchor
- `analysis/iteration_v3-019/synthesis.md` — narrative + verdict summary

### 2.1 Data availability per symbol (from /fapi/v1/fundingRate, paginated 1000 per request)

| Symbol | Funding rate first available | Kline first available | Funding-kline alignment | Total funding rows |
|---|---|---|---:|---:|
| BCHUSDT | 2019-12-19 16:00 UTC | 2020-01-01 00:00 UTC | **100.00%** | 6993 |
| LDOUSDT | 2022-09-22 08:00 UTC | 2022-09-22 08:00 UTC (same day) | **100.00%** | 3970 |
| TRXUSDT | 2020-01-15 08:00 UTC | 2020-01-15 08:00 UTC (same day) | **100.00%** | 6913 |

**Funding-kline alignment gate PASS** (floor 95% per `feedback_v3_iter019_axis_priorities.md` Section 2.1 prereq). Funding settles at exactly 00/08/16 UTC, identical to v3's 8h kline open_times.

### 2.2 Coverage check (IS window, 2023-03-24 → 2025-03-23)

| Symbol | n_IS_total | n_valid_funding_zscore_30 | coverage_zscore_pct |
|---|---:|---:|---:|
| BCHUSDT | 2193 | 2193 | **100.00** |
| LDOUSDT | 2193 | 2193 | **100.00** |
| TRXUSDT | 2193 | 2193 | **100.00** |

**100% coverage on all 3 symbols** — at IS-window start 2023-03-24, the rolling-30 window uses pre-IS data (funding history extends back to 2019-2022 per symbol).

**Coverage gate PASS** (floor 80%).

### 2.3 Distribution check

Raw funding rate stats (24-month IS window):

| Symbol | mean | median | std | skew | kurt | p01 | p99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| BCHUSDT | -0.000029 | -0.000001 | 0.000205 | -0.89 | 8.40 | -0.000656 | +0.000566 |
| LDOUSDT | +0.000129 | +0.000100 | 0.000151 | +2.99 | 12.91 | -0.000133 | +0.000824 |
| TRXUSDT | +0.000003 | +0.000067 | 0.000194 | -1.10 | 6.14 | -0.000669 | +0.000467 |

Funding rates are heavy-tailed (excess kurt 6-13) and per-symbol asymmetric (BCH/TRX slightly bearish-skewed by negative carry events; LDO bullish-skewed by positive carry). The +0.0001 and -0.0005 floors are visible in the percentiles (Binance uses tiered caps — clamping near +0.0001 for low-volatility regimes is responsible for the spike at the median).

Z-scored funding rate (rolling-30 window):

| Symbol | mean (truncated) | median | p01 | p25 | p75 | p99 |
|---|---:|---:|---:|---:|---:|---:|
| BCHUSDT | (outliers; see distribution.csv) | +0.281 | -4.79 | -0.434 | +0.717 | +3.26 |
| LDOUSDT | (outliers; see distribution.csv) | +0.263 | -6.80 | -0.518 | +0.555 | +3.57 |
| TRXUSDT | (outliers; see distribution.csv) | +0.286 | -4.57 | -0.583 | +0.716 | +2.31 |

**Distribution outlier note (audit-trail discipline)**: a small number of IS bars (1 BCHUSDT, 9 LDOUSDT, 3 TRXUSDT out of 2193 each = 0.05% / 0.41% / 0.14% respectively) have extreme z-scores |z| > 100. Root cause: when Binance clamps funding at +0.0001 for >30 consecutive bars (low-volatility regime; rolling std → 0), z-score = (rate − mean) / 0 → infinity. The IC + rank-IC + ADF tests in §2.4-2.6 are rank-based (Spearman) and immune to outlier magnitudes; results below are robust. **Pre-commit for Phase 6 implementation (Section 3.3 sub-fix #1)**: clip the z-scored output to [-10, 10] in `compute_funding_rate_zscore` to prevent LightGBM training instability from extreme-value rows.

The non-outlier core distribution is well-behaved (p25 ≈ -0.5, p75 ≈ +0.7, p99 ≈ +3.0) — typical for a z-scored series with funding-floor-clamping artifacts at the tails.

### 2.4 ADF stationarity check

| Symbol | feature | ADF stat | ADF p | Pass (p < 0.05) |
|---|---|---:|---:|---|
| BCHUSDT | funding_rate_zscore_30 | -46.82 | 0.0000 | **PASS** |
| LDOUSDT | funding_rate_zscore_30 | -46.89 | 0.0000 | **PASS** |
| TRXUSDT | funding_rate_zscore_30 | -46.82 | 0.0000 | **PASS** |

**ADF gate PASS** (p < 0.05 on all 3 symbols). Z-scored series is structurally stationary by construction (rolling-window mean-zero); the formal test confirms.

### 2.5 Correlation gate (vs 13 V3_FEATURE_COLUMNS)

Per-symbol max |Spearman IC| from `analysis/iteration_v3-019/funding_eda_correlation.csv`:

| Symbol | max abs IC | reached at |
|---|---:|---|
| BCHUSDT | 0.2192 | vwap_dev_20 |
| LDOUSDT | 0.2417 | vwap_dev_20 |
| TRXUSDT | 0.3758 | vwap_dev_20 |

**Overall max |IC| across all (symbol × V3col) pairs: 0.3758** (TRX vs vwap_dev_20)

**IC redundancy hard gate PASS** (threshold 0.70 per BASELINE_V3.md). **IC strict brief target PASS** (threshold 0.50 — well below redundancy gate to ensure feature carries genuinely new information). TRX 0.3758 is the strongest pairwise overlap; the structural similarity (volume/order-flow proxy and funding-rate proxy both capture market-imbalance signals) is intuitive but the magnitude well below 0.50 means the funding feature carries substantial independent information.

Compare to v3 max |IC| in iter-v3/008 audit (0.685, just under 0.70 threshold): the existing 13-feature pairwise ceiling is 0.685; the funding candidate's 0.3758 is well BELOW this ceiling, so adding it does NOT raise the IC ceiling.

### 2.6 Rank-IC vs forward returns (predictive signal)

Per `analysis/iteration_v3-019/funding_eda_rankic.csv`:

| Symbol | horizon_bars | horizon_days | n_pairs | rank_ic_spearman |
|---|---:|---:|---:|---:|
| BCHUSDT | 1 | 0.33 | 2192 | -0.00022 |
| BCHUSDT | 3 | 1.00 | 2190 | -0.01937 |
| BCHUSDT | 7 | 2.33 | 2186 | -0.01033 |
| LDOUSDT | 1 | 0.33 | 2192 | -0.01007 |
| LDOUSDT | 3 | 1.00 | 2190 | -0.02287 |
| LDOUSDT | 7 | 2.33 | 2186 | -0.02342 |
| TRXUSDT | 1 | 0.33 | 2192 | +0.01626 |
| TRXUSDT | 3 | 1.00 | 2190 | -0.02179 |
| TRXUSDT | 7 | 2.33 | 2186 | **-0.04850 (LARGEST)** |

**Non-trivial rank-IC PASS**: max |rank-IC| = 0.0485 (TRX 7-bar). Above the v3 implicit threshold of 0.02 inferred from existing-feature behavior. The TRX 7-bar -0.0485 is roughly 2.3x the 1/√n noise floor (1/√2186 ≈ 0.021) — meaningful directional signal, statistically distinguishable from zero.

**Direction-consistent NEGATIVE-rank-IC across symbols and horizons**: 8 of 9 cells negative-direction. This is the EXPECTED mean-reversion direction (high funding → low forward return); aligns with BIS WP 1087 (2025) carry-shock liquidation pressure mechanism. ONLY TRX 1-bar shows positive-direction (+0.0163, weak), interpretable as the immediate momentum-continuation regime before mean-reversion kicks in at 3-7 bars (1-3 days).

**LightGBM-friendly direction structure**: same-direction rank-IC across symbols means trees can use a uniform threshold for the funding feature's directional split. Easier learn than mixed-sign (which iter-v3/015's tbr_zscore_30 had: BCH +6.5% / LDO -2.7% / TRX +0.4% — three different directions per symbol). Funding rate is a CLEANER signal structure to learn.

### 2.7 Behavioral-effect predictor (per `feedback_axis_saturation_predictor.md`)

Per the rule (added after iter-v3/012's NULL-RESULT trade-roster bit-identity surprise; extended at iter-v3/015 for NEW-feature-axis discipline): brief Section 2 must include explicit estimate of how many IS trades will change in the roster. **Anchor**: iter-v3/018 IS trades = 172 (cumulative across 3 symbols at primary seed 42 = multi-seed mean cumulative).

**Predicted IS trade count behavioral effect**:

| Scenario | Expected IS trade count | Mechanism |
|---|---:|---|
| Lower bound (axis fully propagated, model uses funding feature in trade-restrictive manner) | ~140 | Optuna may converge on shorter-tree models that gate trades more selectively when the new feature drives a new threshold |
| Median (typical NEW-feature behavior in v1/v2 history) | ~165 | Model uses new feature as a partial filter; trade roster shifts ~5-10% |
| Upper bound (axis added but Optuna trees largely use existing 13 features) | ~200 | Model includes the feature but it has moderate importance; trade roster ~iter-v3/018's ~172 baseline |
| **Saturation falsifier band (per `feedback_axis_saturation_predictor.md` ±25%)** | **[129, 215]** | Anchor: iter-v3/018 IS trades 172; band low = 0.75 × 172 = 129; band high = 1.25 × 172 = 215 |

**Counterfactual derivation**: the closest comparable baseline is iter-v3/018 (3-symbol, ADX=20, all-other-gates UNCHANGED, multi-seed mean 172 IS trades cumulative across 3 symbols at primary seed 42 — but iter-v3/019 will run at `--seeds 1`, so the comparison is to iter-v3/013's primary-seed 209 IS trades or iter-v3/018's seed-42 172 cumulative). **The saturation band uses iter-v3/018's seed-42-equivalent 172** (the closest single-seed analog). At `--exploration --seeds 1 --n-trials 10`, Optuna re-optimization variance is bounded ±25% per the iter-v3/015 reference observation (13 → 14 features observed 209 → 205, -1.9% change).

**Falsifier reading**: if observed iter-v3/019 IS trades < 129 OR > 215, the new feature axis behavioral effect exceeded the predicted band — potentially `EXPLORATION-NEGATIVE-no-effect` (if axis was saturated and produced bit-identical roster) or `EXPLORATION-NEGATIVE-failed-axis` (if behavioral change exceeded the predicted band). The lower-bound 129 absorbs Optuna's potential trade-restriction; the upper-bound 215 absorbs Optuna re-optimization variance with a slight cushion.

**SECONDARY behavioral-effect verifier (feature-importance check)**: if `funding_rate_zscore_30` does not appear in the top-10 feature importance ranks across at least 1 of the 3 per-symbol models, the feature was effectively unused — the IS Sharpe delta is not attributable to the new feature, and the catalog row should mark INERT-via-noncontribution (lesson from iter-v3/015 tbr_zscore_30 rank 14/14). The Engineer's Phase 6 report MUST stamp the feature-importance ranking for `funding_rate_zscore_30` on each per-symbol model.

### 2.8 Setup integrity (verified at SHA `95858cb`)

```
data/funding_rates/{BCH,LDO,TRX}USDT.csv extant + non-empty after fetch       PASS (3/3)
data/features_v3/{BCH,LDO,TRX}USDT_8h_features.parquet extant + non-empty     PASS (3/3)
funding-kline alignment >= 95%                                                 PASS (100% all 3 symbols)
funding_eda_coverage.csv produced                                              PASS
funding_eda_distribution.csv produced                                          PASS
funding_eda_correlation.csv produced (39 rows)                                 PASS
funding_eda_rankic.csv produced (9 rows)                                       PASS
funding_eda_adf.csv produced                                                   PASS
funding_eda_saturation.csv produced                                            PASS
synthesis.md produced                                                          PASS
Coverage gate (>= 80% IS valid)                                                PASS (100% all 3 symbols)
IC redundancy hard gate (max |IC| < 0.70)                                      PASS (max 0.3758)
IC strict brief target (max |IC| < 0.50)                                       PASS (max 0.3758)
ADF stationarity gate (p < 0.05)                                               PASS (p ≈ 0 all 3 symbols)
Rank-IC non-trivial (>= 0.02)                                                  PASS (max 0.0485)
```

---

## Section 3 — Proposed Changes

### 3.1 Symbols — UNCHANGED (3-symbol BCH+LDO+TRX from iter-v3/013, baselined at iter-v3/018)

| Symbol | iter-v3/018 status | iter-v3/019 status |
|---|---|---|
| BCHUSDT | KEEP | UNCHANGED |
| LDOUSDT | KEEP | UNCHANGED |
| TRXUSDT | KEEP | UNCHANGED |
| MKRUSDT | DROPPED | UNCHANGED (drop-MKR rule executed at iter-v3/013, retained as baseline universe per BASELINE_V3.md note) |

`set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓

### 3.2 Labeling — UNCHANGED (iter-v3/010 ATR 2.0/1.0)

| Parameter | iter-v3/018 (current) | iter-v3/019 |
|---|---:|---:|
| `atr_tp_multiplier` | 2.0 | UNCHANGED |
| `atr_sl_multiplier` | 1.0 | UNCHANGED |
| Timeout | 21 candles (7d) | UNCHANGED |
| `use_atr_labeling` | True | UNCHANGED |
| Purge gap | 66 (= (21+1)×3) | UNCHANGED |

### 3.3 Features — ADD ONE NEW FEATURE (`funding_rate_zscore_30`); 13 → 14 columns

| Feature column | iter-v3/018 (V3_FEATURE_COLUMNS_TOP_N) | iter-v3/019 (V3_FEATURE_COLUMNS_TOP_N + funding) |
|---|---|---|
| max_dd_window_50 | KEEP | UNCHANGED |
| ema_spread_atr_20 | KEEP | UNCHANGED |
| ret_kurt_50 | KEEP | UNCHANGED |
| ret_skew_200 | KEEP | UNCHANGED |
| range_realized_vol_50 | KEEP | UNCHANGED |
| hurst_diff_100_50 | KEEP | UNCHANGED |
| ret_kurt_200 | KEEP | UNCHANGED |
| hurst_100 | KEEP | UNCHANGED |
| btc_ret_14d | KEEP | UNCHANGED |
| ret_skew_50 | KEEP | UNCHANGED |
| vwap_dev_20 | KEEP | UNCHANGED |
| ret_autocorr_lag1_50 | KEEP | UNCHANGED |
| sym_vs_btc_ret_7d | KEEP | UNCHANGED |
| **funding_rate_zscore_30** | (not present) | **ADDED** (the single new column) |

`len(V3_FEATURE_COLUMNS) == 14` after iter-v3/019. `_verify_feature_columns()` updated to assert `len == 14` and `'funding_rate_zscore_30' in V3_FEATURE_COLUMNS`.

### 3.4 Risk gates — UNCHANGED

| Parameter | iter-v3/018 (current) | iter-v3/019 |
|---|---:|---:|
| `RiskV2Config.zscore_threshold` | 2.0 | UNCHANGED (iter-v3/011) |
| `BTC_TREND_CONFIG.threshold_pct` | 15.0 | UNCHANGED (iter-v3/012) |
| `BTC_TREND_CONFIG.lookback_bars` | 42 (14d) | UNCHANGED |
| `BTC_TREND_CONFIG.enabled` | True | UNCHANGED |
| Vol scaling | enabled | UNCHANGED |
| `adx_threshold` | 20.0 | UNCHANGED (iter-v3/013 baseline) |
| `adx_period` | 14 (default) | UNCHANGED |
| `enable_adx_gate` | True (default) | UNCHANGED |
| Hurst regime check | (0.05, 0.95) | UNCHANGED |
| Low-vol filter | 0.33 | UNCHANGED |
| Hit-rate feedback | DISABLED | UNCHANGED |

### 3.5 Sub-fix decomposition (7-item)

| # | Sub-fix | Spec | Verifier |
|---|---|---|---|
| 1 | **New feature module + fetcher path** in `src/crypto_trade/features_v3/funding_v3.py` | New file. Function `compute_funding_rate_zscore(df, funding_df, window=30)`: takes a kline DataFrame and a funding-rate DataFrame, merges on open_time (with millisecond rounding to 60000 to handle Binance's settlement jitter), computes z-score over rolling 30-bar window with `.shift(1)` past-only discipline (mirroring `analysis/iteration_v3-019/funding_rate_eda.py` reference impl), clips to [-10, 10] to handle funding-floor outliers (Section 2.3 outlier note). Function `add_funding_v3_features(df)`: loads cached funding-rate CSV from `data/funding_rates/<symbol>.csv` (cache-only; no online fetch in production path), calls `compute_funding_rate_zscore`, returns df with `funding_rate_zscore_30` column added. | `python -c "from crypto_trade.features_v3.funding_v3 import add_funding_v3_features; import pandas as pd; df = pd.read_csv('data/BCHUSDT/8h.csv'); df['symbol'] = 'BCHUSDT'; df2 = add_funding_v3_features(df); assert 'funding_rate_zscore_30' in df2.columns and df2['funding_rate_zscore_30'].notna().mean() > 0.95"` exits 0 |
| 2 | **Add funding_v3 group to GROUP_REGISTRY** in `src/crypto_trade/features_v3/__init__.py` | `from crypto_trade.features_v3.funding_v3 import add_funding_v3_features` import + `"funding_v3": add_funding_v3_features,` registry entry | `python -c "from crypto_trade.features_v3 import GROUP_REGISTRY; assert 'funding_v3' in GROUP_REGISTRY"` exits 0 |
| 3 | **Add `funding_rate_zscore_30` to `V3_FEATURE_COLUMNS_TOP_N`** in `src/crypto_trade/features_v3/__init__.py` (append at end; total 14 columns) | One-line addition: `"funding_rate_zscore_30",  # rank 14 — funding/carry (iter-v3/019 NEW external-data-source feature family)` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0 |
| 4 | **Add CLI subcommand `fetch-funding`** in `src/crypto_trade/main.py` (or new module under `src/crypto_trade/funding_fetcher.py`) for paginated `/fapi/v1/fundingRate` fetch with cache | New subcommand reads symbol+start args, calls into the same paginated fetcher used in EDA script (`analysis/iteration_v3-019/funding_rate_eda.py` lines `fetch_funding_rates`), writes to `data/funding_rates/<sym>.csv`. Idempotent (incremental from cache). | `uv run crypto-trade fetch-funding --symbols BCHUSDT,LDOUSDT,TRXUSDT` produces 3 files `data/funding_rates/{BCH,LDO,TRX}USDT.csv` non-empty |
| 5 | **Update `ITERATION_LABEL`** from `"v3-018"` to `"v3-019"` in `run_baseline_v3.py:102` | One-line change | `grep -E 'ITERATION_LABEL.*=.*"v3-019"' run_baseline_v3.py` exits 0 |
| 6 | **Regenerate v3 feature parquets** via `uv run crypto-trade features --symbols BCHUSDT,LDOUSDT,TRXUSDT,MKRUSDT --interval 8h --track v3 --format parquet --workers 4` | Existing CLI command. `add_funding_v3_features` will run as part of GROUP_REGISTRY iteration, producing fresh `data/features_v3/*.parquet` with the new 14-column feature set. MKR is regenerated for completeness even though V3_MODELS excludes it. | `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'funding_rate_zscore_30' in df.columns and df['funding_rate_zscore_30'].notna().mean() > 0.95"` exits 0 (and same check for LDO/TRX) |
| 7 | **Run `--exploration --seeds 1 --n-trials 10`** on the 3-symbol universe with the 14-feature set | Phase 6 invocation: `uv run python run_baseline_v3.py --exploration --seeds 1 --n-trials 10`. Wall-clock target: < 15 min (3-symbol, +1 feature column = +~7% feature-loading), 2h hard cap. | `test -f reports-v3/iteration_v3-019/comparison.csv` |

NO NEW labeling change. NO universe change. NO z-score-gate change. NO BTC-band change. NO ADX change. NO Hurst change. NO low-vol-floor change. NO hit-rate change. The single varied axis vs iter-v3/018 baseline is `+funding_rate_zscore_30` to V3_FEATURE_COLUMNS.

### 3.6 Brief-vs-Code reconciliation table (Phase 5.5 input) — 15 verifiers

Each row maps to a FILE ARTIFACT with an executable verifier command. Empty cells = Phase 5.5 BLOCK.

| # | Sub-fix | Code path | File artifact + verifier |
|---|---|---|---|
| 1 | **`funding_v3.py` module exists with `add_funding_v3_features` + `compute_funding_rate_zscore`** | `src/crypto_trade/features_v3/funding_v3.py` | `python -c "from crypto_trade.features_v3.funding_v3 import add_funding_v3_features, compute_funding_rate_zscore; print('OK')"` exits 0 |
| 2 | **`funding_v3` registered in GROUP_REGISTRY** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import GROUP_REGISTRY; assert 'funding_v3' in GROUP_REGISTRY"` exits 0 |
| 3 | **V3_FEATURE_COLUMNS contains funding_rate_zscore_30 at 14 columns** | `src/crypto_trade/features_v3/__init__.py` | `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0 |
| 4 | **`fetch-funding` CLI subcommand operative** | `src/crypto_trade/main.py` (or new fetcher module) | `uv run crypto-trade fetch-funding --help` exits 0 with usage text |
| 5 | **funding rates cached for 3 symbols** | `data/funding_rates/{BCH,LDO,TRX}USDT.csv` | `python -c "from pathlib import Path; assert all((Path(f'data/funding_rates/{s}USDT.csv')).exists() for s in ['BCH','LDO','TRX'])"` exits 0 |
| 6 | **Per-symbol parquet has funding_rate_zscore_30 with > 95% non-NaN coverage on full series** | `data/features_v3/{BCH,LDO,TRX,MKR}USDT_8h_features.parquet` | `python -c "import pandas as pd; r=[pd.read_parquet(f'data/features_v3/{s}USDT_8h_features.parquet')['funding_rate_zscore_30'].notna().mean() > 0.95 for s in ['BCH','LDO','TRX','MKR']]; assert all(r), r"` exits 0 |
| 7 | **`atr_tp_multiplier=2.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 |
| 8 | **`atr_sl_multiplier=1.0` UNCHANGED (iter-v3/010)** | `run_baseline_v3.py` | `grep -E 'atr_sl_multiplier=1\.0' run_baseline_v3.py` exits 0 |
| 9 | **`zscore_threshold=2.0` UNCHANGED (iter-v3/011)** | `run_baseline_v3.py:897` | `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 |
| 10 | **`adx_threshold=20.0` UNCHANGED (iter-v3/013 baseline)** | `run_baseline_v3.py:898` | `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 |
| 11 | **`BTC_TREND_CONFIG.threshold_pct=15.0` UNCHANGED (iter-v3/012)** | `run_baseline_v3.py:123` | `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 |
| 12 | **`V3_MODELS` has exactly 3 entries; MKR NOT present (inherited iter-v3/013)** | `run_baseline_v3.py` | `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3 and 'MKRUSDT' not in {s for _,s in m.V3_MODELS}"` exits 0 |
| 13 | **`ITERATION_LABEL` updated to `"v3-019"`** | `run_baseline_v3.py:102` | `grep -E 'ITERATION_LABEL.*=.*"v3-019"' run_baseline_v3.py` exits 0 |
| 14 | **Sub-fix #7 produces comparison.csv** | runner | `test -f reports-v3/iteration_v3-019/comparison.csv` |
| 15 | **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in band [129, 215] (anchor iter-v3/018 IS trades 172). PLUS SECONDARY VERIFIER: `funding_rate_zscore_30` appears in feature_importance.csv non-zero for at least 1 of 3 per-symbol models. | comparison.csv + feature_importance.csv | `python -c "import pandas as pd; df=pd.read_csv('reports-v3/iteration_v3-019/comparison.csv'); n=int(df.loc[df['metric']=='n_trades','in_sample'].iloc[0]); assert 129 <= n <= 215, f'IS trades {n} OUTSIDE saturation band [129, 215]'"` exits 0 AND feature-importance non-zero for funding feature on >= 1 of 3 models |

### 3.7 NO labeling/feature-prune/universe/gate-knob changes

iter-v3/019 is a single-axis (NEW feature family with NEW external data source) EXPLORATION. The labeling, model architecture, ATR labeling multipliers, z-score OOD threshold, BTC trend filter band, ADX threshold, low-vol floor, Hurst regime check, hit-rate feedback (disabled), CPCV parameters, and walk-forward window are unchanged from iter-v3/018. The only differences vs iter-v3/018:
- `+funding_rate_zscore_30` in V3_FEATURE_COLUMNS (13 → 14)
- `ITERATION_LABEL` (cosmetic)
- New `compute_funding_rate_zscore` + `add_funding_v3_features` functions in new `features_v3/funding_v3.py` module
- New `funding_v3` entry in `GROUP_REGISTRY`
- New `fetch-funding` CLI subcommand
- `_verify_feature_columns` assertion bump (13 → 14)
- Parquet regeneration to materialize the 14-column feature set

### 3.8 Inheritance from iter-v3/018

The `iteration-v3/019` branch was branched from `iteration-v3/018` head. Inherited commits include all iter-v3/008-018 lineage. Critical inheritance verifiers (run before any code edits in Phase 6):

- `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 13 and 'funding_rate_zscore_30' not in V3_FEATURE_COLUMNS"` exits 0 (BEFORE iter-v3/019 sub-fix #3)
- `grep -E 'atr_tp_multiplier=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/010 value)
- `grep -E 'zscore_threshold=2\.0' run_baseline_v3.py` exits 0 (still iter-v3/011 value)
- `grep -E 'adx_threshold=20\.0' run_baseline_v3.py` exits 0 (still iter-v3/013 baseline)
- `grep -E 'threshold_pct=15\.0' run_baseline_v3.py` exits 0 (still iter-v3/012 value)
- `grep -E 'ITERATION_LABEL.*=.*"v3-018"' run_baseline_v3.py` exits 0 (BEFORE sub-fix #5)
- `python -c "from importlib import import_module; import sys; sys.path.insert(0,'.'); m=import_module('run_baseline_v3'); assert len(m.V3_MODELS)==3"` exits 0 (still iter-v3/013 value)
- AFTER iter-v3/019 sub-fix #3: `python -c "from crypto_trade.features_v3 import V3_FEATURE_COLUMNS; assert len(V3_FEATURE_COLUMNS) == 14 and 'funding_rate_zscore_30' in V3_FEATURE_COLUMNS"` exits 0
- AFTER iter-v3/019 sub-fix #6: `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'funding_rate_zscore_30' in df.columns and df['funding_rate_zscore_30'].notna().mean() > 0.95"` exits 0
- `uv run pytest tests/strategies/ml/ -v` exits 0 with all tests passing

---

## Section 4 — Expected OOS Impact

### 4.1 EXPLORATION → headline metrics are GUIDANCE not GATES

Per Section 0.5 + skill spec at SHA `f0f8b84`, headline metrics are NOT BLOCK-triggering for the Critic on EXPLORATION iterations. The Critic emits `EXPLORATION-PROMISING`, `EXPLORATION-NEGATIVE`, `EXPLORATION-PROMISING-MECHANICAL`, `EXPLORATION-PROMISING-INERT`, `EXPLORATION-NEGATIVE-no-effect`, or `BLOCK` (process). iter-v3/019 NEVER updates BASELINE_V3.md regardless of verdict.

### 4.2 Predicted IS Sharpe range

Anchor: iter-v3/018 BOOTSTRAP baseline IS Sharpe **+0.3788 (multi-seed mean)** / **+0.4563 (seed 42 single)**. iter-v3/019 runs at `--seeds 1 --n-trials 10` (EXPLORATION mode), so the closest-comparable single-seed metric is iter-v3/018 seed 42 = +0.4563.

| Metric | iter-v3/018 (anchor multi-seed) | iter-v3/018 (anchor seed-42 single) | iter-v3/019 prediction (3-symbol, 14-feature, +funding) |
|---|---:|---:|---:|
| IS monthly Sharpe | +0.3788 | +0.4563 | **predicted [+0.45, +0.85] (median +0.58)** = Δ vs multi-seed anchor [+0.07, +0.47] (median +0.20); Δ vs seed-42 single anchor [-0.01, +0.39] |
| IS trades | 172 (multi-seed mean cumul) | 172 (seed 42) | **predicted [129, 215]** (saturation band ±25%) |
| OOS trades | 90.5 (mean) / 102 (seed 42) | 102 (seed 42) | **informational ~75-130** |
| OOS Sharpe | +0.3869 (mean) / +0.2343 (seed 42) | +0.2343 | **informational; high variance because new feature changes both entry-signal surface AND model's regime-classifier dimension** |
| Phase 6 wall-clock | 4.54h | (CONFIRMATION mode) | predicted 8-15 min (3 symbols, 14-column feature set adds ~7% to feature-loading time per training fold, plus parquet regen ~2-3 min separate from runner), hard cap 2h |

The IS prediction band [+0.45, +0.85] (Δ over multi-seed anchor +0.20 median) is calibrated against:
- iter-v3/018 anchor +0.3788 multi-seed mean (gate 1 floor +1.0 missed by 0.62)
- The unique-lever requirement from `feedback_v3_iter019_axis_priorities.md`: "13-feature stack underperforms multi-seed by ~0.6 Sharpe units; need ~+0.6 Sharpe lift to clear gates 1+2 floors" — a +0.6 Sharpe lift in ONE EXPLORATION is unrealistic; spread across the 10 EXPLORATIONs, each step contributes incrementally. Median +0.20 is the proportional share for axis #1 (NEW feature families) given:
  - Funding rate has non-trivial rank-IC (max |IC| 0.0485 at TRX 7-bar, mean-reversion direction)
  - IC orthogonality is excellent (max 0.3758, well below 0.50 strict target)
  - Low-stationarity-issue / well-behaved core distribution
- iter-v3/015 NEW feature family attempt (tbr_zscore_30) produced IS Sharpe Δ -0.36 — the NEW-feature-family axis category has ONE prior calibration point in v3, and it was NEGATIVE-no-effect. Funding rate's structural advantages over tbr (orthogonal data source, same-direction rank-IC across symbols, larger |rank-IC| 0.0485 vs tbr's 0.065 BCH-only) suggest BUT DO NOT GUARANTEE a different outcome.

The band's lower bound +0.45 is set conservatively above iter-v3/018 multi-seed +0.3788 anchor by +0.07; this is enough to exceed it but acknowledges Optuna re-optimization variance can produce minimal-gain outcomes on a 14th feature. The upper bound +0.85 is roughly 2x the anchor — aggressive but bounded; +1.0 lift in a single EXPLORATION would be exceptional and not anticipated. Median +0.58 = (anchor +0.38) + (modest single-axis lift +0.20).

### 4.3 Falsifiers (locked before backtest)

**Falsifier 1**: IS Sharpe < iter-v3/018 multi-seed anchor (+0.3788) → the new feature actively hurt the model OR the axis didn't propagate (overfit on funding_rate_zscore_30 in some regime, or interacted destructively with existing features). Verdict: EXPLORATION-NEGATIVE on feature-family axis (clean). Catalog row marks NO candidate; iter-v3/020+ explores a different axis.

**Falsifier 2 (saturation predictor per `feedback_axis_saturation_predictor.md`)**: IS trade count outside [129, 215] (= [0.75 × 172, 1.25 × 172]) → axis behavioral effect deviates from prediction. If trades < 129 (<-25% reduction): the new feature is heavily restricting trade entries, possibly via a tree split that gates aggressively on funding regime. If trades > 215 (>+25% expansion): the new feature is loosening trade entries OR the axis didn't propagate (V3_FEATURE_COLUMNS reassignment didn't make it to LightGBM). Verdict path: BLOCK if axis didn't propagate (verified via Falsifier 4 secondary check); otherwise EXPLORATION-NEGATIVE-no-effect or NEGATIVE-failed-axis.

**Falsifier 3** (process): Phase 6 wall-clock > 30 min on 3-symbol universe with 14-feature set → unexpected slowdown in feature-loading or parquet regen pipeline. Engineer documents the cause.

**Falsifier 4 (NEW for NEW-feature-axis discipline; iter-v3/015 precedent)**: `funding_rate_zscore_30` does not appear in feature_importance.csv for ANY of the 3 per-symbol models (or appears with importance == 0 on all 3) → the model effectively ignored the new feature; the IS Sharpe delta is not attributable to the new feature (analogous to iter-v3/015 tbr_zscore_30 rank 14/14 INERT). Verdict: EXPLORATION-PROMISING-INERT or NEGATIVE-no-effect (depending on Sharpe direction). Catalog row marks NO candidate.

**Process falsifier**: pre-flight `grep funding_rate_zscore_30 src/crypto_trade/features_v3/__init__.py` exits non-zero, OR `python -c "import pandas as pd; df = pd.read_parquet('data/features_v3/BCHUSDT_8h_features.parquet'); assert 'funding_rate_zscore_30' in df.columns"` exits non-zero, OR `data/funding_rates/<SYM>.csv` not present → setup drift; Phase 6 must not start.

### 4.4 EXPLORATION outcome interpretation (pre-commit catalog framing)

Per `feedback_promising_mechanical_subtype.md` + `feedback_axis_saturation_predictor.md` + iter-v3/015-018 precedent. §4.4 row 5 NEGATIVE-clean condition follows iter-v3/017's update: "either |Δ trades| ≥ 11 OR per-symbol shift > 5".

| Critic verdict | Conditions | Catalog row | Next iteration |
|---|---|---|---|
| `EXPLORATION-PROMISING` | IS Sharpe Δ ≥ +0.10 vs iter-v3/018 multi-seed anchor (i.e., ≥ +0.4788) AND broad-based per-symbol AND IS trades in [129, 215] (Falsifier 2 PASS) AND `funding_rate_zscore_30` in top-10 importance for ≥ 1 model (Falsifier 4 PASS) | "Funding-rate regime-classifier added genuine alpha — broad-based gain" | iter-v3/020 EXPLORATION on a DIFFERENT axis category (NEW model arch / NEW labeling / NEW risk primitive / concentration architecture per `feedback_v3_iter019_axis_priorities.md` HIGH #2) — single-axis discipline preserved |
| `EXPLORATION-PROMISING-INERT` | IS Sharpe within ±0.10 of iter-v3/018 multi-seed anchor (i.e., in [+0.28, +0.48]) AND IS trades in [129, 215] AND `funding_rate_zscore_30` in top-10 importance for ≥ 1 model | "Funding feature added but information overlap with existing features near-saturated" | iter-v3/020 EXPLORATION on a DIFFERENT axis category |
| `EXPLORATION-PROMISING-MECHANICAL` | IS Sharpe up ≥ +0.10 BUT trade-roster bit-identity to iter-v3/018 — UNLIKELY for new-feature axis given non-trivial rank-IC; flagged for completeness | "New feature added without behavioral change — accounting drift" | similar to iter-v3/013 framing |
| `EXPLORATION-NEGATIVE-no-effect` (NULL-RESULT) | IS Sharpe direction wrong (Δ < 0 vs iter-v3/018 multi-seed) AND `funding_rate_zscore_30` importance == 0 across all 3 models (Falsifier 4 fires) | "Model ignored the new feature; saturation pattern (iter-v3/015 precedent)" | iter-v3/020 EXPLORATION on a DIFFERENT axis category — should NOT be another funding-related variant |
| `EXPLORATION-NEGATIVE` (clean) | (IS Sharpe Δ < -0.10 vs iter-v3/018 multi-seed anchor i.e. < +0.2788 AND non-bit-identical roster — using `feedback_promising_mechanical_subtype.md` row 5 condition `\|Δ trades\| ≥ 11 OR per-symbol shift > 5` to confirm non-bit-identity) AND `funding_rate_zscore_30` IS in feature importance (Falsifier 4 PASS) → the model used the new feature but it actively hurt | "Funding z-score destructive — possibly overfit on transient carry regime; mean-reversion signal didn't generalize" | iter-v3/020 EXPLORATION on a DIFFERENT axis category — NOT another carry/funding variant |
| `BLOCK` (process) | Methodology check FAILED, OR Falsifier 2 (saturation, IS trades outside [129, 215]) AND axis didn't propagate (Falsifier 4 fires), OR Falsifier 3 (wall-clock) triggered | (none) | Diary documents, iter-v3/020 fixes the methodology gap |

---

## Section 5 — Risk Mitigation

### 5.1 Cadence-discipline structural safeguards (4 inherited + 4 methodology-specific = 8 total)

iter-v3/019 inherits the cadence-discipline safeguards from skill SHA `d5c9f21` + the saturation-predictor rule + the new structural-axis preference rule + `feedback_v3_iter019_axis_priorities.md` LOCKED:

1. **2h wall-clock hard cap**: Engineer kills Phase 6 if elapsed > 2h. Wall-clock target < 30 min for 3-symbol + 14-feature `--exploration` mode.
2. **Single-axis variation rule** honored (only `+funding_rate_zscore_30` added to V3_FEATURE_COLUMNS; ATR/zscore-OOD/BTC-band/Hurst/low-vol/hit-rate/CPCV byte-for-byte identical to iter-v3/018; no gate threshold tuning; no universe change; no labeling change; no model architecture change). The new fetcher path + new feature module are SUPPORTING infrastructure for the single feature axis, not separate axes.
3. **EXPLORATION never updates BASELINE_V3.md** — outcome (PROMISING / PROMISING-INERT / PROMISING-MECHANICAL / NEGATIVE / NEGATIVE-no-effect / BLOCK) records only in `briefs-v3/exploration_catalog.md` and `diary-v3/iteration_v3-019.md`.
4. **Saturation predictor falsifier** (Section 3.6 row 15 + Section 4.3 Falsifier 2, threshold derived from anchor `iter-v3/018 IS trades = 172` ±25% = [129, 215] per `feedback_axis_saturation_predictor.md`) actively verifies that the new feature axis propagated to the model output AND that behavioral effect is in expected band.

Methodology-specific safeguards (NEW-feature-family with NEW external data source axis):

5. **Feature-importance verifier** (Section 3.6 row 15 secondary): `funding_rate_zscore_30` must appear in feature_importance.csv non-zero for at least 1 of 3 per-symbol models (Falsifier 4). Distinguishes "model used the feature actively" from "model ignored the feature; Sharpe Δ was Optuna re-opt artifact" (the iter-v3/015 INERT pattern).
6. **EDA gate pre-commits** (Section 2): coverage ≥ 80% PASS (100%); IC redundancy < 0.70 hard PASS (0.3758 max); IC strict brief < 0.50 PASS (0.3758 max); ADF stationarity p < 0.05 PASS (p ≈ 0); rank-IC non-trivial PASS (max 0.0485). All five EDA gates passed BEFORE the brief was written; Phase 6 inherits a candidate that is structurally tractable.
7. **Past-only computation discipline**: `compute_funding_rate_zscore` uses `.shift(1)` on rolling stats so bar t z-score uses bars t-30...t-1 only — STRICTLY past-only. Funding rate AT bar t is the rate that just SETTLED at the candle open, knowable from the previous 8h period close (broadcast 5 min before settlement). Critic Check 1 (Look-Ahead) verifier mirrors the EDA reference implementation. **Specific look-ahead audit point**: the funding rate broadcast at time T is the rate FOR the period [T-8h, T] paid AT T. We use the rate AT T at bar t (knowable strictly from period close). The `.shift(1)` on rolling stats further ensures that even rolling-window denominators come from past bars only.
8. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.2 Methodology-pipeline safety (inherited from iter-v3/006-018)

1. **Adversarial unit tests** must PASS before backtest.
2. **File-artifact reconciliation table** (§3.6). 15 verifier commands; empty cells = Phase 5.5 BLOCK.
3. **Pre-flight grep-checks**: `funding_rate_zscore_30` in V3_FEATURE_COLUMNS, parquet has `funding_rate_zscore_30` column, funding-rate cache present at `data/funding_rates/<sym>.csv`. Catches the case where setup edits were silently lost or feature regen was skipped.
4. **Two-round Critic flow**: any methodology issue surfaces before Phase 6 launches.

### 5.3 NEW-feature-axis-specific risks (3 explicit)

1. **Data fetcher reliability**: `/fapi/v1/fundingRate` is a public Binance endpoint with no authentication and no historical-window cap (paginated 1000 per request from any startTime). Verified at SHA `95858cb` working for all 3 symbols. **Mitigation**: fetcher caches to `data/funding_rates/<sym>.csv`; re-runs are incremental from cache; 16h-staleness guard inherited from kline fetcher pattern. **Risk if fetcher fails**: Phase 6 cannot start — but the EDA already cached the data once, so re-runs work even offline. **Falsifier path**: §3.6 row 5 verifies cache files exist before Phase 6 sub-fix #6 (parquet regen).
2. **Look-ahead from funding settlement timing**: The funding rate is SETTLED at candle open (00/08/16 UTC) but BROADCAST 5 minutes before settlement (so traders can react). The rate AT T is fully knowable from the [T-8h, T] period's close. We use the rate at bar t in the numerator (with `.shift(1)` on rolling stats to ensure denominator uses bars t-30...t-1). This is STRICTLY past-only. **Mitigation**: compute_funding_rate_zscore mirrors the EDA reference implementation byte-for-byte (sub-fix #1 verifier checks coverage ≥ 95% which would fail if look-ahead introduced NaN at boundary). **Adversarial test recommendation** (sub-fix #1): unit test that `compute_funding_rate_zscore` produces the same value when given (a) full series, and (b) same series truncated at bar t — past-only guarantee.
3. **Feature redundancy with existing vol-related features**: max |IC| = 0.3758 vs `vwap_dev_20` (the strongest pair) — both volume/order-flow proxies. Although below the 0.50 strict target by a wide margin, the structural similarity may cause LightGBM to exhibit moderate substitution effects (the new feature steals some `colsample_bytree` picks from `vwap_dev_20`). Since `colsample_bytree=1.0` in `--exploration` mode, this is mostly an information-redundancy concern, not a tree-construction concern. **Mitigation**: Falsifier 4 (feature-importance check) catches the case where funding feature is fully substituted by existing features. Funding rate captures POSITION/LEVERAGE information not in vwap_dev_20 (which captures price-volume distribution), so substitution is not expected to be complete.

---

## Section 6 — Risk Management Design

### 6.1 7-primitive table — UNCHANGED (single-feature-axis variation; gates byte-identical to iter-v3/018)

| # | Primitive | Spec | Fire-rate prediction (IS, 3-symbol, 14-feature) | Regime coverage |
|---|---|---|---|---|
| 1 | Vol scaling | `scale = clip(atr_pct_rank_200, 0.3, 1.0)` | Always on; mean scale ≈ 0.6 | High-vol → scale down |
| 2 | ADX gate | trade only when ADX ≥ 20 (iter-v3/013 baseline) | ≈ 60% of bars pass | Trend filter |
| 3 | Hurst regime check | trade only when 0.05 < hurst_100 < 0.95 | ≈ 90% of bars pass | Filters bond-like regimes |
| 4 | Feature z-score OOD | kill if any \|z\| > 2.0 (over **14** features now — slightly higher kill rate due to one more column for OOD computation) | ≈ 26–37% killed (was ~25-35% with 13 cols; minor uplift expected) | Distributional drift |
| 5 | Low-vol filter | trade only when atr_pct_rank_200 ≥ 0.33 | ≈ 67% of bars pass | Filters dead chop |
| 6 | Hit-rate feedback | DISABLED | 0% | Reserved for future tuning |
| 7 | BTC trend alignment | kill alt trade fighting BTC 14d ±15% | ≈ 12–13% killed (inherited iter-v3/012) | Macro flips |

Combined kill rate target: **80–90%** (matches iter-v3/018's range; z-score OOD over 14 cols may slightly tighten). The only primitive whose computation changes is primitive 4 (z-score OOD now over 14 features instead of 13); all others' specs are byte-identical to iter-v3/018.

**Important sub-point**: the new `funding_rate_zscore_30` becomes one of the 14 columns the z-score OOD primitive computes the per-bar kill on. In stress regimes where funding rate spikes (|z| > 2.0), the OOD gate will kill the bar's signal — this is intentional defensive behavior consistent with the existing OOD gate's design (iter-v3/011 z-score 2.0). The funding feature's heavy-tailed distribution (Section 2.3, p99 ~ 3.0) means OOD kills will fire more aggressively in funding-stress regimes (e.g., BTC liquidation cascades where funding hits +0.005 per cycle). This is RISK-AWARE behavior, not an over-restriction.

**Gate orthogonality**: All 7 primitives operate per-(symbol, candle) and are independent. Adding `funding_rate_zscore_30` to V3_FEATURE_COLUMNS expands primitive 4's z-score OOD computation to 14 features (more dimensions to check, slightly tighter kill rate). The other 6 primitives are unaffected by feature-set changes — they operate on candle/symbol-level signals computed independently of the LightGBM model's input features.

### 6.2 Regime coverage — UNCHANGED

3-symbol IS data spans 2023-03-24 → 2025-03-23 — same as iter-v3/018. Regime coverage includes 2023 banking crisis (SVB → BTC +40%/14d), 2024 halving + Trump rally (BTC +48%/30d at peak), 2024-08 yen-carry crash (BTC −25%/14d), 2025 January correction. The 3-symbol portfolio's exposure to these regimes is broadly similar; the new funding-rate feature provides additional regime-classification dimension (high-carry vs low-carry vs negative-carry regimes) WITHIN each of these macro periods. Specifically:

- **2023-Q3 high-funding episode** (BCH retail FOMO, BTC ETF rumor regime): BCH funding spent extended periods at +0.0002 to +0.0005 per cycle — funding_rate_zscore_30 should peak at z ≈ +2 to +3 in this window
- **2024-08 yen-carry unwind**: BTC -25%/14d; perp funding flipped negative as longs stopped out; should show negative-z (z ≈ -2) cluster on all 3 symbols
- **LDO 2024-01-15 protocol news episode**: LDO funding spiked +0.0008 (largest in IS) — z-score should hit +5+ briefly

These regime-locked extreme-z events provide LightGBM training signal for funding-stress trade restriction.

### 6.3 Concentration — informational only under EXPLORATION

iter-v3/018 multi-seed showed TRX 66.08% / 55.83% concentration (gate 7 floor 30% missed). iter-v3/019 OOS concentration may shift either direction depending on whether funding feature reshapes per-symbol trade frequencies. Per `feedback_v3_iter019_axis_priorities.md` HIGH #2, concentration architecture is the iter-v3/020+ axis (deferred for clean per-iteration single-axis discipline). This brief does NOT pre-register a concentration falsifier. Future CONFIRMATION QR will scope the structural concentration issue separately.

---

## Section 7 — Pre-Registered Failure-Mode Prediction (6 predictions calibrated against 10 prior EXPLORATIONs + iter-v3/018 multi-seed evidence)

**Prediction P1 (process, P=10%)**: `funding_rate_zscore_30` column not added to V3_FEATURE_COLUMNS or not propagated to the LightGBM strategy's `feature_columns` argument. Engineer adds the column to the constant but a path-resolution issue in `LightGbmStrategy(feature_columns=list(V3_FEATURE_COLUMNS))` causes runtime to use a stale column list. **Detection signal**: Falsifier 4 (feature-importance check) shows funding feature with importance 0 across all 3 models OR Falsifier 2 (saturation predictor) fires (IS trades outside [129, 215]). **Mitigation**: §3.6 rows 3, 6, 15 verifiers (3 independent signals).

**Prediction P2 (process, P=15%)**: parquet regeneration fails or produces stale parquets (funding_rate_zscore_30 missing or NaN). Most likely cause: `add_funding_v3_features` not called via the v3 features CLI (or called on cached pre-feature data without reading the funding_rates/<sym>.csv). Higher probability than other process risks because this iteration introduces a NEW external data source — first time funding fetcher path is in production code. **Detection signal**: §3.6 row 6 verifier fails — `pd.read_parquet(...)['funding_rate_zscore_30'].notna().mean() > 0.95` returns False. **Mitigation**: pre-flight verifier blocks Phase 6 launch.

**Prediction P3 (process, P=10%)**: wall-clock overshoots the 30-min target due to feature-set expansion (14 cols vs 13 = ~7% more loading per training fold) PLUS the new funding fetcher cold-start cost (~3 min for 3 symbols × 7 pages). 3-symbol universe with 14-feature set should run in 8-15 min after parquet regen + funding cache; cold-start is +3 min. **Detection signal**: engineering report wall-clock minutes. **Mitigation**: 2h hard cap by skill spec.

**Prediction P4 (model, P=40%)**: IS Sharpe lifts to [+0.45, +0.60]; the new funding-rate z-score gives the model a derivatives-positioning regime-classifier signal that complements the existing 13-feature set; PROMISING. The LightGBM model uses the funding feature in tree splits, learning per-symbol mean-reversion patterns (high funding → restrict longs; low funding → permit longs OR consider shorts) consistent with the EDA rank-IC pattern. The 8 of 9 NEGATIVE-direction rank-IC cells signal a coherent mean-reversion edge across the 3 symbols.

**Prediction P5 (model, P=25%)**: IS Sharpe stays in iter-v3/018 multi-seed anchor range [+0.28, +0.48]; the new funding z-score is included in the model but its information overlap with existing features (max |IC| 0.3758 with vwap_dev_20) is enough that the model's tree splits substitute funding for vwap_dev_20 in some contexts without net Sharpe lift; PROMISING-INERT.

**Prediction P6 (model, P=15%)**: IS Sharpe drops below iter-v3/018 multi-seed anchor (-0.10 → < +0.28); the new funding feature introduces noise that the model overfits on in early Optuna trials (the +0.38 IS multi-seed Sharpe of iter-v3/018 was on a stack already calibrated to 13 features; adding a 14th increases the loss-surface dimensionality and Optuna at n_trials=10 may converge to an overfit point); NEGATIVE-clean. iter-v3/020+ would explore a different axis (concentration architecture, NEW model arch, NEW labeling) since the feature axis demonstrated edge-detrimental risk.

**Prediction P7 (model, P=10%)**: IS Sharpe spikes to > +0.85; funding rate provides a structurally novel signal that compounds with existing features for an unexpected lift; PROMISING-strong. This would be the strongest evidence yet that NEW-external-data-source feature axes are higher-impact than gate-knob axes (consistent with `feedback_structural_over_knob_exploration.md` rationale and `feedback_v3_iter019_axis_priorities.md` HIGH #1 designation).

P4 + P5 + P7 sum to 75% (PROMISING-family outcome). P6 sums to 15% (off-distribution outcomes). Process predictions P1-P3 sum to 35% (failure-mode hedging, higher than usual due to NEW external data source).

**Calibration vs prior EXPLORATIONs**:
- 3-consecutive favorable IS overshoot pattern (iter-v3/010, 011, 013) was BROKEN at iter-v3/014 and remained broken through iter-v3/015-017 (4 NEGATIVE-class outcomes in a row). The pattern reset at iter-v3/018 BOOTSTRAP (multi-seed anchor reflects honest weak-but-positive signal); iter-v3/019 uses moderate band consistent with NEW-axis-category variance and the iter-v3/018 anchor reset.
- The NEW-feature-family axis category has ONE prior calibration data point in v3 — iter-v3/015's tbr_zscore_30 was NEGATIVE-no-effect (rank 14/14 INERT). Funding rate's structural advantages (NEW external data source vs SAME-data tbr; same-direction rank-IC across symbols vs mixed-sign tbr; larger |rank-IC| 0.0485 vs tbr's 0.065 BCH-only) suggest BUT DO NOT GUARANTEE a different outcome.
- The QR's prior bands draw on:
  - iter-v3/015 NEW-feature-family axis (Δ -0.36 NEGATIVE-no-effect; same-data-source) — argues for cautious median
  - iter-v3/018 anchor (multi-seed +0.3788 IS) — argues for moderate target above anchor
  - The +0.6 Sharpe lift required to clear gate 1 floor across the 10-EXPLORATION cycle suggests each step contributes +0.06 average; iter-v3/019's median +0.20 is 3x the per-step average (justified for axis #1 which is the unique-lever HIGH-priority axis with NEW external data source bringing genuinely novel information)
- The median +0.58 prediction (Δ +0.20 over multi-seed anchor +0.38) sits between iter-v3/018's +0.38 anchor and iter-v3/013's pre-falsified single-seed +1.01 — appropriately moderate for a single-axis structural change with 1 prior NEGATIVE-no-effect calibration.

---

## Section 8 — Pre-Registered MERGE/NO-MERGE Criteria — 11 EXPLORATION criteria

EXPLORATION never updates BASELINE_V3.md, so traditional MERGE thresholds do not apply. The 11 criteria below pre-register the catalog-row decision and provide unambiguous Critic verdict triggers (per skill spec at SHA `f0f8b84` + `feedback_promising_mechanical_subtype.md` + `feedback_axis_saturation_predictor.md`).

1. **IS Sharpe ≥ iter-v3/018 multi-seed anchor + 0.10 (i.e., ≥ +0.4788)**: catalog row records PROMISING verdict on numerical-axis basis.
2. **IS Sharpe < iter-v3/018 multi-seed anchor (i.e., < +0.3788)**: Falsifier 1 — EXPLORATION-NEGATIVE if non-bit-identical roster, or NEGATIVE-no-effect if axis didn't propagate (Falsifier 4 fires).
3. **IS Sharpe in [+0.3788, +0.4788) (= anchor ± 0.10)**: PROMISING-INERT (inert verdict) — catalog row records INERT.
4. **n_trades ≥ 50 IS, ≥ 50 OOS**: BUNDLE-LEVEL trade-rate floor per `feedback_trade_rate_floor_bundle_level` (informational at EXPLORATION; predicted IS in [129, 215] — well above 50; OOS predicted ~75-130 — ≥50). Bundle (5 outer × 3-4× ensemble) at CONFIRMATION will multiply this 3-4×.
5. **PBO < 0.40 (per-cell mean) AND `n_high_pbo_cells_99 ≤ 4`**: methodology hygiene; both inherited unchanged from iter-v3/018 multi-seed (mean 0.0892; max 1.0 on TRX/2022-Q4 carry-forward — outstanding constraint flagged in BASELINE_V3.md but NOT iter-v3/019's axis to fix). iter-v3/019 expected near-identical PBO unless new feature has unexpected cell-level effect.
6. **IC max abs < 0.70**: per Critic Check 4 — the new feature `funding_rate_zscore_30` has max |IC| 0.3758 vs the existing 13 (verified at SHA `95858cb`); the existing 13-feature pairwise max was 0.685; **after-add expected max |IC| in the 14-feature pairwise matrix remains 0.685** (the new column doesn't create a NEW pair above 0.685 since its max IC is 0.3758, well below 0.685 — IC ceiling unchanged at iter-v3/018's 0.685).
7. **ADF p < 0.05 on 14 V3_FEATURE_COLUMNS** (or stationarity rationale per Section 4 precedent): the 13 inherited features unchanged; the new `funding_rate_zscore_30` is a z-score (rolling-window mean-zero by construction) — ADF p-value is structurally near-zero on z-scored series (verified at SHA `95858cb`: p ≈ 0 all 3 symbols). Engineer's Phase 6 ADF test will confirm.
8. **Reproducibility verifier**: SHAs stamped in engineering report (analysis `95858cb`, runner setup commit, brief commit, Phase 5.5 gate, engineering report).
9. **Pareto dominance**: vacuous under single-seed EXPLORATION (Section 8 criterion 9 waiver inherited from iter-v3/006-018).
10. **Symbol exclusion + feature isolation**: `set({BCH, LDO, TRX}) ∩ V3_EXCLUDED_SYMBOLS = ∅` ✓; `features_v3` does not import `features` (v1) or `features_v2` (v2). The new `funding_v3.py` lives in `features_v3/` (track-isolated); zero new imports from v1/v2.
11. **Behavioral-effect verifier (saturation falsifier per `feedback_axis_saturation_predictor.md` ±25% rule)**: IS trades in **[129, 215]** (= anchor iter-v3/018 IS trades 172 ± 25%). The threshold is DERIVED from §2.7's anchor; not a hardcoded constant. **PLUS SECONDARY VERIFIER (Falsifier 4)**: `funding_rate_zscore_30` appears in feature_importance.csv non-zero for at least 1 of 3 per-symbol models. Critic uses BOTH signals to disambiguate "axis propagated AND model used feature" from "axis added but model ignored it (NULL-RESULT, iter-v3/015 INERT precedent)". Predicted behavioral effect: IS trade count change ≤ 25% from anchor 172 (range [129, 215]).

**Catalog-axis verdicts** map to §4.4 table. The catalog row records the verdict exactly as Critic FINAL emits it.

---

## Section 9 — Library Stack Declaration

**SAME stack as iter-v3/008-018** — no version bumps in iter-v3/019:

```
python = 3.13
lightgbm = 4.6.0
numpy = 2.2.6
pandas = 3.0.0 (or recent compatible; iter-v3/018 stamp shows 3.0.0)
scikit-learn = 1.8.0
pyarrow = 23.0.1 (for parquet I/O)
mlfinpy = 1.4.0 (CPCV; MIT-licensed fork)
pypbo = 0.10.0 (PBO via CSCV)
fracdiff = 0.10.0 (Numba-accelerated; FracdiffStat + ADF auto-d*)
statsmodels = 0.14.6 (adfuller for ADF stationarity)
optuna = 4.8.0
scipy = 1.17.0
httpx = (already used for kline fetcher; reused for funding-rate fetcher)
```

**No package additions or version bumps.** The new `compute_funding_rate_zscore` function uses only `numpy` + `pandas` (already imported in v3 features modules); the new fetcher path uses `httpx` (already used by `BinanceClient`). No new dependencies. The `fetch-funding` CLI subcommand is a new entry point but uses existing stack.

---

## Section 10 — Adversarial Tests (inherited; one new test recommended)

Adversarial test suite at `tests/strategies/ml/` is unchanged. The Engineer SHOULD add one new test in Phase 6 (recommended, not strictly required for EXPLORATION):

- `tests/features_v3/test_funding_v3.py::test_funding_rate_zscore_past_only` — assert `compute_funding_rate_zscore(df, funding_df)` produces NaN for the first 30 rows (rolling window initialization) AND that the value at row N depends only on rows N-30 to N-1 (past-only, .shift(1) verified). Mirror the look-ahead defense in EDA. Plus assert the clip-to-[-10, 10] outlier handling (Section 2.3 outlier note + sub-fix #1 spec).
- `tests/features_v3/test_funding_v3.py::test_funding_rate_kline_alignment` — assert that for each kline open_time aligned to 00/08/16 UTC, the merged funding rate matches the funding-rate CSV's funding_time at that boundary (with millisecond rounding to handle Binance's ~10-15ms jitter).

If Engineer runs out of time (2h cap), the adversarial test addition is deferred to iter-v3/020+ (Critic FINAL note). The runtime correctness is verified via §3.6 row 1 verifier (which runs `add_funding_v3_features` on the full BCH parquet and asserts column presence + coverage).

---

## Section 11 — Catalog Row Pre-Commit (audit-trail discipline)

Per iter-v3/006+ catalog discipline, this brief pre-commits a structural template for the iter-v3/019 catalog row before backtest results are known:

```
| iter-v3/019 | 2026-05-07 | NEW funding feature → +funding_rate_zscore_30 (V3_FEATURE_COLUMNS 13 → 14; NEW external data source) | IS Sharpe Δ TBD vs iter-v3/018 multi-seed +0.3788 | OOS Sharpe TBD (informational) | TBD verdict | TBD candidate? |
```

The catalog row will be filled by the Phase 8 diary entry. The verdict cell maps to §4.4 + §8 criterion 1-3 + 11. The "candidate?" cell maps to whether the next CONFIRMATION-bundling QR should consider iter-v3/019 as a stack ingredient.

**Pre-committed disposition** (cannot be renegotiated post-hoc):
- If verdict = `EXPLORATION-PROMISING` AND `EXPLORATION-PROMISING-INERT` is NOT triggered AND Falsifier 4 (feature-importance check) PASSES: catalog row marked YES candidate (compoundable as a fourth axis-lift in any future CONFIRMATION bundle; first NEW-external-data-source ingredient).
- If verdict = `EXPLORATION-PROMISING-INERT`: catalog row marked NO candidate (axis is orthogonal but information overlap saturates lift; future feature-family axes should test less-correlated features OR more aggressive single-feature-add experiments, OR consider whether funding-rate variants like `funding_rate_pctile_90` would learn differently).
- If verdict = `EXPLORATION-PROMISING-MECHANICAL` (UNLIKELY given non-trivial rank-IC; flagged for completeness): catalog row marked YES with NON-COMPOUNDABLE flag (point decision, like drop-MKR was at iter-v3/013).
- If verdict = `EXPLORATION-NEGATIVE` or `EXPLORATION-NEGATIVE-no-effect`: catalog row marked NO; iter-v3/020 explores a DIFFERENT axis category. Per `feedback_v3_iter019_axis_priorities.md` HIGH #2 (concentration architecture) is the natural next axis. NEXT iteration MUST NOT be another carry/funding variant — single-axis discipline + axis-category-rotation discipline.

**Catalog count after iter-v3/019**: 1 of 10 EXPLORATIONs in the new post-bootstrap cycle; **9 more required** before any CONFIRMATION can launch (earliest = iter-v3/028). Axis coverage after iter-v3/019: features × 2 + labeling × 1 + gate-zscore × 1 + gate-btc-trend × 1 + universe × 1 + gate-adx × 1 (CLOSED) + NEW microstructure feature × 1 (CLOSED-narrow) + NEW model arch × 1 (CLOSED-at-config) + NEW labeling arch × 1 (PATH C) + bootstrap CONFIRMATION × 1 + **NEW external-data-source feature × 1** = 11 unique axis representations after iter-v3/019.

**Forward axis pipeline** (iter-v3/020-028 candidates pre-pre-committed for QR continuity, NOT mandates per `feedback_v3_iter019_axis_priorities.md` LOCKED priority order):
- iter-v3/020 candidates: HIGH-priority axis #2 = concentration architecture (per-symbol `max_per_symbol_pnl_share = 0.40` constraint OR universe expansion to 5+ symbols)
- iter-v3/021+ candidates: depend on iter-v3/019 + iter-v3/020 verdicts; further NEW feature families (Open Interest delta, basis spread, on-chain proxies — each requires its own external data source) only if a fetch+regen workflow is well-established post-iter-v3/019; else MEDIUM priority axes (DSR gate reformulation, TRX/2022-Q4 regime gate)

---

## Final Brief-Authoring Checklist (Phase 5.5 self-check)

- [x] §0 sacred constants UNCHANGED, restated.
- [x] §0.5 EXPLORATION declaration with cadence count (1 of 10 in new post-bootstrap cycle); STRUCTURAL axis declared; explicit "NOT a gate-threshold knob"; references `feedback_v3_iter019_axis_priorities.md` LOCKED + `feedback_structural_over_knob_exploration.md`.
- [x] §1 hypothesis: one sentence, falsifiable; mechanism explanation (funding-rate regime-classifier + LightGBM-friendly same-direction-rank-IC across symbols + per-symbol architecture).
- [x] §2 IS-only numerical evidence with COMMITTED analysis script SHA `95858cb`; coverage 100% / max |IC| 0.3758 / max rank-IC 0.0485 / ADF p ≈ 0 / behavioral-effect predictor with derived saturation band [129, 215] anchored at iter-v3/018 IS trades 172.
- [x] §3 sub-fixes (7-item) with verifier commands; reconciliation table 15 rows; new fetcher path + new feature module pre-committed.
- [x] §4 predicted IS Sharpe band [+0.45, +0.85] median +0.58 (Δ +0.20 over multi-seed anchor +0.3788); 5 catalog framings + falsifiers 1-4 + process locked; §4.4 row 5 condition `|Δ| ≥ 11 OR per-symbol shift > 5` per iter-v3/017 update.
- [x] §5 risk mitigation (4 cadence + 4 methodology + 3 axis-specific risks: data fetcher reliability, look-ahead from settlement timing, feature redundancy with vol features).
- [x] §6 7-primitive table — UNCHANGED (gates byte-identical to iter-v3/018; only z-score OOD computation expands to 14 cols).
- [x] §7 6 failure-mode predictions calibrated against 10 prior EXPLORATIONs + iter-v3/018 multi-seed evidence (process P1-P3 = 35%; model P4-P7 = 90%; higher process probability than usual due to NEW external data source).
- [x] §8 11 EXPLORATION criteria; criterion 11 = saturation falsifier with derived band [129, 215] per `feedback_axis_saturation_predictor.md` + Falsifier 4 secondary feature-importance verifier.
- [x] §9 library stack, no bumps; no new dependencies (httpx already in stack for kline fetcher).
- [x] §10 adversarial tests inherited; two new tests recommended (deferrable).
- [x] §11 catalog row pre-commit + dispositions; forward axis pipeline (iter-v3/020+ candidates per `feedback_v3_iter019_axis_priorities.md` LOCKED priority order).

**Brief authorship complete.** Engineer Phase 5.5 gate is the next step.
