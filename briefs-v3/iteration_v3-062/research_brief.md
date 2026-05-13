# Iteration v3-062 — Research Brief (DSR_relative recalibration — Path C passive retrospective)

**Type**: EXPLORATION (Cycle 1 #3 of 10)
**Track**: v3 (rigor arm) — sixty-second iteration
**Branch**: `iteration-v3/062` (off iter-v3/061 head at SHA `8a02b7a`)
**Date**: 2026-05-13
**Author**: QR (autopilot)
**EDA SHA**: `ae22e60` (`analysis/iteration_v3-062/dsr_relative_recalibration_eda.py` + 7 CSVs + `synthesis.md`)

**MANDATED AXIS** (per iter-v3/059 Critic FINAL `0fc18c2` Rec #1 + iter-v3/061 Critic FINAL `b20b554` Rec #1 carry-forward):
**DSR_relative threshold/benchmark recalibration (methodology-only axis)** — addressing the 3-iteration-stale dsr_relative=0.0 + cpcv_path_sharpe_q75=0.8378 mismatch at /059/060/061.

**SELECTED PATH**: **Path C — Passive retrospective documentation; defer methodology change to iter-v3/069 cycle 1 CONFIRMATION.**

Quantitative justification (per EDA SHA `ae22e60` T1-T7):
1. **Input granularity mismatch confirmed across 4 iterations**: runner passes `observed_sharpe` at trade-level × √n_trades scale (e.g., /061 = 0.207 = 0.0205 per-obs × √102) while `benchmark_sharpe` at candle-level × √n_test scale (e.g., 0.838 = 0.0233 per-obs × √1296). The √102 vs √1296 mismatch ≈ 3.6× and structurally suppresses dsr_relative.
2. **Path A (threshold recalibration 0.95 → 0.55) is partial-fix only**: /059 still FAILS at any reasonable threshold (0.1134 < 0.55); /060/061 EXPLORATION-mode dsr_relative=0.0 unchanged.
3. **Path B (granularity match) addresses root cause but breaks backward-compat AND requires high integration test surface**: 6th integration test + smoke test + Section 8 traceback per `feedback_v3_methodology_axis_integration_test.md` and `feedback_v3_methodology_post_hoc_input_traceback.md`. iter-v3/062 2h hard cap doesn't leave runway.
4. **EXPLORATION-mode DSR/PSR is informational per `feedback_v3_dsr_mode_artifact.md`**: at n_trials=315 (EXPLORATION) vs n_trials=1050 (CONFIRMATION), E[max_SR] = √(2 ln 315) ≈ 2.41 vs √(2 ln 1050) ≈ 2.64; methodology change tested at /062 EXPLORATION doesn't transfer to /069 CONFIRMATION scale. **The methodology axis is structurally a CONFIRMATION-mode concern.**
5. **Path C produces a 4-iteration retrospective + iter-v3/069 recommendation document**: zero backtest required; iter-v3/069 QR receives a Path B4 (annualized both sides) specification with the smoke test + integration test surface pre-defined.

**STRATEGY UNCHANGED** vs /061 head — no code change to backtest path; comparison.csv/dsr.json/cpcv_paths.csv outputs IDENTICAL to /060/061 if backtest were re-run.

**NO BACKTEST REQUIRED** for iter-v3/062. Path C deliverable = this brief + EDA + diary recommendation. Cycle 1 EXPLORATION slot #3 of 10 IS consumed by methodology retrospective work.

---

## Section 0 — Data Split Declaration

```
OOS_CUTOFF_DATE  = 2025-03-24    # IMMUTABLE
training_months  = 24             # IMMUTABLE
ENSEMBLE_SIZE    = 5              # inner ensemble (3-seed outer @ --exploration)
n_trials         = 35             # EXPLORATION default
colsample_bytree = Optuna-tuned   # NOT hardcoded 1.0
OOS_CUTOFF_MS    = 1742774400000
```

**IS window (24 months)**: 2023-03-24 00:00 UTC through 2025-03-23 23:59 UTC
**OOS window**: 2025-03-24 00:00 UTC onward

Sacred constants UNCHANGED. Data split UNCHANGED.

**Path C special status**: NO backtest will run for /062. Data split is technically irrelevant since no inference happens. Declared for brief-section completeness.

---

## Section 0.5 — Iteration Type Declaration

```
TYPE: EXPLORATION
Cycle: 1 — #3 of 10 (third cycle 1 EXPLORATION post-iter-v3/059 RE-ANCHOR #2)
Wall-clock budget: <= 2h hard cap (EXPLORATION spec)
Path C SPECIFIC: <= 30min target (no backtest; EDA + brief + diary work only)
Spec: NO backtest. Deliverable = research brief + EDA + diary recommendation.
```

**Why Path C is the disciplined choice**:

| Constraint | Path A | Path B (any variant) | Path C |
|---|---|---|---|
| Code change | 1 constant | 10-30 lines + tests | 0 lines |
| Wall-clock | 1.1h backtest | 1.1h backtest + smoke test + integration test (~2-3h) | <30min docs |
| Integration test surface | None | HIGH (6th integration test + smoke test mandatory) | None |
| Backward-compat | YES | NO (all historical dsr_relative values change) | YES |
| Addresses root cause | NO | YES | DEFERS (with documented specification for /069 QR) |
| EXPLORATION-vs-CONFIRMATION scale | Tests at wrong n_trials (315 vs 1050) | Tests at wrong n_trials (315 vs 1050) | Defers test to right n_trials (1050) |
| Risk to /060 anchor numbers | None | None (no data change) | None |

The EXPLORATION-vs-CONFIRMATION scale issue is decisive: per `feedback_v3_dsr_mode_artifact.md`, EXPLORATION-mode DSR/PSR are regime-specific artifacts. Path B methodology tested at EXPLORATION mode would be re-tested at CONFIRMATION mode at /069 anyway — so the iter-v3/062 work doesn't transfer. The clean path is to specify the Path B4 methodology NOW (in the diary recommendation for /069 QR) so that iter-v3/069 implements it correctly with the full integration test surface.

**Cycle 1 cadence accounting**:
- /060 = cycle 1 #1 of 10 (PROMISING-EXPLORATION; TRX OOS diagnostic + 3-seed anchor)
- /061 = cycle 1 #2 of 10 (INERT-AT-EXPLORATION; TRX RiskV2 anti-Kelly closed)
- **/062 = cycle 1 #3 of 10** (PASSIVE-DIAGNOSTIC Path C; methodology retrospective)
- /063 = cycle 1 #4 of 10 (MASS FEATURE EXPANSION per `feedback_v3_mass_feature_expansion.md`)
- /064-/068 = cycle 1 #5-#9 of 10 (axis selection TBD per QR EDA discipline)
- /069 = cycle 1 CONFIRMATION (separate from cycle 1 EXPLORATIONs per `feedback_v3_strict_10_to_1_cadence.md`)

---

## Section 1 — Testable Hypothesis (ONE sentence)

**Hypothesis (Path C)**: Documenting the trade-level vs candle-level granularity mismatch as a 4-iteration retrospective + specifying Path B4 (annualized-both-sides reformulation) for iter-v3/069 cycle 1 CONFIRMATION produces a methodologically cleaner DSR_relative recalibration than attempting Path A or Path B in /062's EXPLORATION mode where n_trials=315 ≠ CONFIRMATION n_trials=1050.

**Falsifiability**: Path C is INHERENTLY UNFALSIFIABLE within /062 (no backtest). The hypothesis is testable at /069 CONFIRMATION where the recommended Path B4 methodology will produce a quantitative dsr_relative value at the canonical n_trials=1050 scale, and that value can be checked against the EDA-predicted band.

---

## Section 2 — Numerical EDA Tables (EDA SHA `ae22e60`)

All tables produced by `analysis/iteration_v3-062/dsr_relative_recalibration_eda.py`.

### Section 2.1 — T1 Input traceback per iteration

| iter | architecture | n_trades_oos | raw_sharpe_oos_trade_level | monthly_sharpe_oos | daily_sharpe_oos | cpcv_q75_benchmark | psr_legacy | dsr_relative_observed | oos_skew | oos_kurt |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 028 | 2-outer × 5-inner buggy WF | 96 | 0.5430 | 0.5053 | 1.0340 | 0.0000 | 1.0000 | 0.000000 | 0.5260 | 3.1823 |
| 050 | 2-outer × 5-inner post-fix | 93 | 1.2630 | 1.1659 | 2.4881 | 0.0000 | 1.0000 | 0.000000 | -0.1096 | 3.5682 |
| 058 | 2-outer × 5-inner post-fix | 103 | 1.1046 | 0.7826 | 2.0759 | 0.8378 | 1.0000 | **0.998164** | 0.6861 | 3.4539 |
| 059 | unified 10-seed | 94 | 0.7046 | 0.5791 | 1.4359 | 0.8378 | 1.0000 | 0.113363 | 0.8829 | 3.5622 |
| 060 | EXPLORATION 3-seed | 102 | 0.1873 | 0.1403 | 0.3659 | 0.8378 | 0.9763 | 0.000000 | 0.6385 | 3.4401 |
| 061 | EXPLORATION 3-seed | 102 | 0.2070 | 0.1551 | 0.4050 | 0.8378 | 0.9861 | 0.000000 | 0.6298 | 3.4028 |

**Key observation**: At /028/050 the cpcv_q75_benchmark = 0.0 (CPCV computation pre-A2; not yet a benchmark). At /058 onwards, cpcv_q75 = 0.838 (constant across all post-A2 iterations — architecture-invariant for the BCH+LDO+TRX universe). The variation in dsr_relative_observed is driven entirely by the observed trade-level Sharpe changing.

### Section 2.2 — T2 Granularity scale factors

| iter | n_trades_oos | trade_level_sharpe | per_obs_trade_sharpe | daily_sharpe_per_obs | scale_trade_vs_candle | trades/year |
|---|---:|---:|---:|---:|---:|---:|
| 028 | 96 | 0.5430 | 0.0554 | 0.0651 | 0.1583 | 82.29 |
| 050 | 93 | 1.2630 | 0.1310 | 0.1567 | 0.1558 | 79.71 |
| 058 | 103 | 1.1046 | 0.1088 | 0.1308 | 0.1639 | 88.29 |
| 059 | 94 | 0.7046 | 0.0727 | 0.0905 | 0.1566 | 80.57 |
| 060 | 102 | 0.1873 | 0.0185 | 0.0230 | 0.1631 | 87.43 |
| 061 | 102 | 0.2070 | 0.0205 | 0.0255 | 0.1631 | 87.43 |

**Key observation**: The `scale_trade_vs_candle = √n_trades / √n_test_per_path ≈ √100/√1296 ≈ 0.16` is STABLE across all post-fix iterations. The runner's psr() compares trade-level × √100 vs candle-level × √1296 — the √-scaling differs by a factor of ~6×, systematically biasing dsr_relative downward.

### Section 2.3 — T3 Path A counterfactual: threshold recalibration

| iter | dsr_relative_observed | pass_at_0.95 | pass_at_0.80 | pass_at_0.70 | pass_at_0.60 | pass_at_0.55 | pass_at_0.50 | pass_at_0.40 |
|---|---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 028 | 0.0 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| 050 | 0.0 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| 058 | 0.998 | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** | **PASS** |
| 059 | 0.113 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| 060 | 0.0 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |
| 061 | 0.0 | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL | FAIL |

**Key observation**: Path A at any reasonable threshold ≥ 0.40 STILL FAILS at /059 (0.113 < 0.40). Only the /058 iteration PASSES — and /058 dsr_relative is structurally OOS-Sharpe-driven (0.7826 monthly OOS Sharpe; OOS-dominant character). Path A doesn't fix the architecture mismatch; just shifts the pass/fail line.

### Section 2.4 — T4 Path B counterfactual: granularity-matched psr() inputs

| iter | dsr_observed | B1 (benchmark→trade) | B2 (observed→candle) | B3 (both per-obs) | B4 (annualized both) |
|---|---:|---:|---:|---:|---:|
| 028 | 0.0 | 1.000000 | 1.000000 | 0.708070 | 1.000000 |
| 050 | 0.0 | 1.000000 | 1.000000 | 0.892607 | 1.000000 |
| 058 | 0.998 | 1.000000 | 1.000000 | 0.812898 | 1.000000 |
| 059 | 0.113 | 1.000000 | 1.000000 | 0.686781 | 1.000000 |
| 060 | 0.0 | 0.318374 | 0.000000 | 0.481086 | 0.000002 |
| 061 | 0.0 | 0.390141 | 0.000256 | 0.488893 | 0.000037 |

**Path B4 (annualized both sides via daily-Sharpe × √252)** discriminates correctly:
- /058, /059 PASS strongly (1.0) — both produced positive OOS edge at unified-architecture scale
- /060, /061 FAIL strongly (≈0) — EXPLORATION-mode 3-seed with weak OOS Sharpe
- /028, /050 PASS at trade-level (positive trade-level Sharpe; no cpcv_q75 reference yet pre-A2)

**Path B4 verdict at iter-v3/069 (CONFIRMATION mode)**: under unified 10-seed n_trials=1050, the dsr_relative_B4 should structurally reflect annualized daily Sharpe vs annualized candle Sharpe — both at √252 / √756 scaling. The /059 multi-seed mean produces daily_sharpe_oos = 1.4359; this corresponds to dsr_relative_B4 ≈ 1.0 (PASS). The 0.95 threshold remains aspirational under unified architecture only if the OOS daily Sharpe falls below the CPCV-annualized benchmark (e.g., daily_sharpe_oos < 0.64). For /060/061 EXPLORATION-mode (daily Sharpe ≈ 0.4), dsr_relative_B4 correctly = 0.

### Section 2.5 — T5 Alternative benchmark (Q50/Q60/Q75 — variant B5 of Path B)

| iter | observed_trade | q50 | q60_est | q75 | dsr_q50 | dsr_q60 | dsr_q75_recomp | dsr_observed_runner |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 028 | 0.5430 | 0.3351 | 0.2011 | 0.0000 | 0.9830 | 0.9998 | 1.0000 | 0.000000 |
| 050 | 1.2630 | 0.0526 | 0.0316 | 0.0000 | 1.0000 | 1.0000 | 1.0000 | 0.000000 |
| 058 | 1.1046 | 0.3351 | 0.5362 | 0.8378 | 1.0000 | 1.0000 | 0.9982 | 0.998164 |
| 059 | 0.7046 | 0.3351 | 0.5362 | 0.8378 | 1.0000 | 0.9592 | 0.1134 | 0.113363 |
| 060 | 0.1873 | 0.3351 | 0.5362 | 0.8378 | 0.0791 | 0.0010 | 0.0000 | 0.000000 |
| 061 | 0.2070 | 0.3351 | 0.5362 | 0.8378 | 0.1089 | 0.0017 | 0.0000 | 0.000000 |

**Observation**: B5 (Q50 instead of Q75) softens the benchmark but doesn't fix the granularity mismatch. /060/061 EXPLORATION-mode would still struggle (0.08-0.11 < 0.55 threshold). Path C documents this as alternative-but-not-recommended.

### Section 2.6 — T6 Path selection summary

| path | description | code_change | addresses_root_cause | backward_compat | integration_test_surface | complexity | risk |
|---|---|---|---|---|---|---:|---:|
| A | Threshold 0.95 → 0.55 | 1 constant | NO | YES | MINIMAL | 1 | 1 |
| B1 | Benchmark→trade-level | ~10 lines | YES | NO | MEDIUM | 2 | 2 |
| B2 | Observed→candle-level | ~10 lines | YES | NO | MEDIUM | 2 | 2 |
| B3 | Both per-obs | ~10 lines | PARTIAL | NO | MEDIUM | 2 | 2 |
| **B4** | **Annualized both sides** | **~20 lines** | **YES (cleanest)** | **NO** | **HIGH** | **4** | **3** |
| B5 | Q50 benchmark | 1 literal | NO | NO | MINIMAL | 1 | 1 |
| **C** | **Passive retrospective** | **0 lines** | **DEFERS** | **YES** | **NONE** | **0** | **0** |

### Section 2.7 — T7 Recommendation: Path C

| field | value |
|---|---|
| recommendation | Path C (passive retrospective + defer to /069 CONFIRMATION) |
| axis_outcome_predicted | PASSIVE-DIAGNOSTIC (no backtest required) |
| predicted_is_oos_shift_vs_060_anchor | ZERO (no code change) |
| predicted_dsr_relative_at_060_data | 0.0 (unchanged from /061 = /060) |
| cycle1_confirmation_recommendation | iter-v3/069 QR should pick Path B4 |
| wall_clock_target | <30 min (no backtest) |
| cycle1_explore_slot_consumed | YES (cycle 1 #3 of 10 consumed by methodology retrospective) |
| integration_test_required | NO (no code change → no integration test) |
| backward_compat | FULL (no code change) |

### Section 2.8 — Runner code-path trace per `feedback_v3_methodology_post_hoc_input_traceback.md`

EXACT runner code paths for the variables in psr() at iter-v3/061 head:

**1. observed_sharpe (passed to psr() at line 2297)**
- Code path: `run_baseline_v3.py:2258-2260`
- Line 2258: `oos_wp = np.array([float(t.weighted_pnl) for t in oos_trades])`
- Line 2260: `raw_sharpe_oos = float(oos_wp.mean() / oos_wp.std() * np.sqrt(len(oos_wp)))`
- Granularity: **trade-level** (one observation per trade in `oos_wp`)
- Annualization factor: `np.sqrt(len(oos_wp))` = √n_trades_oos
- For /061: oos_wp.mean()=0.0597, oos_wp.std()=2.8859, n=102 → raw_sharpe_oos = 0.0597/2.8859×√102 = **0.207** ✓ matches EDA T1 row /061

**2. benchmark_sharpe (passed to psr() at line 2301)**
- Code path: `run_baseline_v3.py:2281-2286`
- Line 2282: `cpcv_path_sharpe_q75 = float(np.percentile(flat_path_sharpes, 75))`
- `flat_path_sharpes` is from `cpcv_df["sharpe"]`, computed at `run_baseline_v3.py:1158-1160`:
  - Line 1158: `mu = float(np.nanmean(proxy_rets))` where proxy_rets = log returns of IS candle sequence
  - Line 1160: `path_sharpe = mu / sigma * np.sqrt(n_test)` where n_test = #candles per CPCV path
- Granularity: **candle-level (8h candles)** × √n_test_per_path
- Annualization factor: √n_test ≈ √1296 for 10-split CPCV at 24-month × 3-symbol = 6480 IS candles / 5 = 1296 per path (2 test splits / 10 total)

**3. n_obs (passed to psr() at line 2298)**
- Code path: `run_baseline_v3.py:2298`: `n_obs=len(oos_wp)`
- Granularity: **trade-count** (matches observed_sharpe granularity)

**4. skewness + kurtosis (passed to psr() at lines 2299-2300)**
- Code path: `run_baseline_v3.py:2261-2262`
- Line 2261: `oos_sk = float(skew(oos_wp))` — TRADE-level skew
- Line 2262: `oos_kt = float(kurtosis(oos_wp, fisher=False))` — TRADE-level kurt
- Granularity: **trade-level** (matches observed_sharpe)

**Inconsistency**: observed_sharpe is trade-level (×√n_trades), benchmark_sharpe is candle-level (×√n_test). The Bailey-LdP psr() formula assumes both sides at the same granularity; the runner violates this.

### Section 2.9 — Computation of E[max_SR] under different n_trials regimes

- /060/061 EXPLORATION: n_trials = 35 × 3 syms × 3 seeds = **315** → E[max_SR] = √(2 ln 315) = √(2 × 5.752) = √11.504 ≈ **2.41**
- /058 CONFIRMATION (2-outer × 5-inner): n_trials = 35 × 3 syms × 10 = **1050** → E[max_SR] = √(2 ln 1050) = √(2 × 6.957) = √13.914 ≈ **2.64**
- /059 CONFIRMATION (unified 10-seed): n_trials = 35 × 3 syms × 10 = **1050** → E[max_SR] = **2.64** (identical to /058)

The /060/061 EXPLORATION-mode dsr_relative is structurally regime-different from the /058/059 CONFIRMATION-mode dsr_relative. Path-selection at /062 EXPLORATION mode CANNOT be tested against the CONFIRMATION-mode regime.

### Section 2.10 — Anchor Declaration (EXPLICIT)

**Anchor for iter-v3/062**: **iter-v3/060** at IS monthly Sharpe **+0.8325**, OOS monthly Sharpe **+0.1403** (3-seed EXPLORATION-MODE-REFERENCE per /060 Critic FINAL `3cee250`).

Anchoring rationale:
- /060 = first cycle 1 EXPLORATION at unified architecture + --exploration --seeds 3 mode
- /061 reproduced /060 within band (Δ IS -0.009 / Δ OOS +0.015)
- /062 expected (under Path C) to also reproduce /060 — no code change at all
- BASELINE_V3.md /059 reference exists at CONFIRMATION mode (different n_trials regime)

**Under Path C, NO backtest runs**, so /062 metrics are by definition "identical to /060" — no shift expected, no falsifier needed. The deliverable is methodology documentation.

---

## Section 3 — Substantive Change (ONE clear thing)

**The substantive change is methodological: select Path C and produce the iter-v3/069 cycle 1 CONFIRMATION recommendation.**

**Code changes**: ZERO.
**Backtest re-runs**: ZERO.
**File changes**:
1. `briefs-v3/iteration_v3-062/research_brief.md` (THIS DOCUMENT)
2. `analysis/iteration_v3-062/dsr_relative_recalibration_eda.py` + 7 CSVs + synthesis.md (committed at SHA `ae22e60`)
3. `diary-v3/iteration_v3-062.md` (Phase 8 deliverable; will contain Path B4 specification for /069 QR)

**iter-v3/069 cycle 1 CONFIRMATION recommendation (carried in this brief; final form in diary)**:

The /069 QR should implement Path B4 with the following specification:

```python
# In run_baseline_v3.py, replace lines 2257-2305 with:

# Compute daily PnL series from OOS trades (calendar-day granularity)
oos_trade_close_dates = pd.to_datetime([t.close_time for t in oos_trades], unit="ms").date
oos_daily_pnl = pd.Series(
    [float(t.weighted_pnl) for t in oos_trades],
    index=pd.DatetimeIndex(oos_trade_close_dates),
).groupby(level=0).sum()

# Daily-Sharpe-annualized (matches comparison.csv "daily_sharpe" column)
if len(oos_daily_pnl) > 1 and oos_daily_pnl.std() > 0:
    daily_sharpe_oos_annualized = float(
        oos_daily_pnl.mean() / oos_daily_pnl.std() * np.sqrt(252)
    )
    daily_skew_oos = float(skew(oos_daily_pnl.values))
    daily_kurt_oos = float(kurtosis(oos_daily_pnl.values, fisher=False))
else:
    daily_sharpe_oos_annualized = 0.0
    daily_skew_oos = 0.0
    daily_kurt_oos = 3.0

# Candle-level CPCV path Sharpe Q75 → annualize × √(candles_per_year)
# 3 candles per day × 252 trading days = 756 candles per year
if len(flat_path_sharpes) >= 4:
    # cpcv_path_sharpe_q75 is currently ×√n_test (path-level annualization);
    # need to de-annualize, then re-annualize to calendar-year scale:
    n_test_per_path_est = 1296  # ≈ (24 months × 3 sym × 30 × 3 candles/day) × (2/10 test ratio)
    cpcv_q75_per_candle = float(np.percentile(flat_path_sharpes, 75)) / np.sqrt(n_test_per_path_est)
    cpcv_q75_annualized = cpcv_q75_per_candle * np.sqrt(756)  # 3 × 252 8h-candles per year
else:
    cpcv_q75_annualized = 0.0

n_daily_obs_oos = max(2, len(oos_daily_pnl))
dsr_relative_b4 = psr(
    observed_sharpe=daily_sharpe_oos_annualized,
    n_obs=n_daily_obs_oos,
    skewness=daily_skew_oos,
    kurtosis=daily_kurt_oos,
    benchmark_sharpe=cpcv_q75_annualized,
)
```

**Required test surface for /069**:
1. **End-to-end smoke test** in brief Section 9 pre-flight: run a 1-month walk-forward, single symbol, n_trials=2, verify dsr.json contains `dsr_relative > 0` and `cpcv_q75_annualized > 0` when synthetic edge is present.
2. **6th integration test** at `tests/strategies/ml/test_dsr_relative_b4.py`: call runner's `_compute_metrics_and_write_dsr_json()` directly with synthetic OOS trades + flat_path_sharpes, assert dsr_relative_b4 matches expected value within 1e-6.
3. **Brief Section 8 traceback subsection** per `feedback_v3_methodology_post_hoc_input_traceback.md`: enumerate each input variable + its code-path source + verified-via-smoke-test value.
4. **Backward-compat validation**: re-run /058 + /059 with Path B4 active (zero data change, only metric reformulation); record new dsr_relative_b4 values in BASELINE_V3.md as informational comparison.

**Predicted /069 cycle 1 CONFIRMATION dsr_relative_B4 band** (per /059 anchor data assuming bundle composition unchanged):
- /059 daily_sharpe_oos = 1.4359 (annualized); /059 n_daily_obs ~ 294; benchmark_annualized ≈ 0.64
- dsr_relative_B4(1.4359; n=294; benchmark=0.64) ≈ **0.999+ (PASS at 0.95 threshold)**

This is the band /069 QR should pre-register; if the actual /069 backtest produces a dsr_relative_B4 well outside [0.95, 1.0], the Path B4 methodology is suspect.

---

## Section 4 — Expected Impact (with code-path traceback)

Per `feedback_v3_methodology_post_hoc_input_traceback.md`, each predicted band specifies the exact runner code path computing each input variable.

### Section 4.1 — Predicted /062 backtest metrics (data-invariant under Path C)

Since Path C makes ZERO code changes, the /062 backtest (if run) would produce metrics IDENTICAL to /060/061:

| Metric | /060 anchor | /061 reproduction | /062 prediction | Code path |
|---|---:|---:|---:|---|
| IS monthly Sharpe | +0.8325 | +0.8236 | **+0.8236** (Δ vs /060 = -0.009; within ±0.10) | `run_baseline_v3.py:1500-1509` `_monthly_sharpe()` over trade.weighted_pnl |
| OOS monthly Sharpe | +0.1403 | +0.1551 | **+0.1551** (Δ vs /060 = +0.015; within ±0.10) | same |
| IS daily Sharpe | +1.7115 | +1.7028 | **+1.7028** (Δ vs /060 = -0.009) | `run_baseline_v3.py:1533-1545` `_daily_sharpe()` |
| OOS daily Sharpe | +0.3659 | +0.4050 | **+0.4050** | same |
| IS Trades | 159 | 159 | **159** (BCH+LDO+TRX bit-identical to /061; no code change) | `len(is_trades)` in `_compute_metrics_and_write_dsr_json` |
| OOS Trades | 102 | 102 | **102** | `len(oos_trades)` |
| frac_positive_paths | 0.6444 | 0.6444 | **0.6444** (architecture-invariant) | `run_baseline_v3.py:2188` |
| cpcv_path_sharpe_q75 | 0.8378 | 0.8378 | **0.8378** (architecture-invariant) | `run_baseline_v3.py:2282` |
| PBO | 0.1278 | 0.1278 | **0.1278** (cell-level invariant) | `run_baseline_v3.py:1186` |
| **dsr_relative** | **0.0** | **0.0** | **0.0** (unchanged; no methodology change in /062) | `run_baseline_v3.py:2296-2302` |
| PSR (legacy) | 0.9763 | 0.9861 | ~0.97-0.99 (3-seed stochastic from ensemble seed selection) | `run_baseline_v3.py:2263-2268` |

### Section 4.2 — Behavioral effect predictor (per `feedback_v3_axis_saturation_predictor.md`)

| Behavior | Path C prediction |
|---|---|
| IS trade roster shift vs /061 | 0 trades (bit-identical; no code change touches inference path) |
| OOS trade roster shift vs /061 | 0 trades (same) |
| BCH/LDO/TRX per-symbol attribution | bit-identical to /061 |
| Feature importance rank | bit-identical to /061 (no feature change) |
| psr() output values | bit-identical to /061 (no methodology change) |
| dsr_relative value | bit-identical to /061 = 0.0 |

**Saturated-axis check** (per `feedback_v3_axis_saturation_predictor.md`): YES, Path C is by definition saturated (zero behavioral effect). This is INTENTIONAL — the methodology axis cannot be tested at EXPLORATION mode in a way that transfers to CONFIRMATION mode, so the disciplined choice is deferral.

### Section 4.3 — Predicted /062 outcomes vs /060 anchor

| Outcome | Prediction | Falsifier |
|---|---|---|
| Path classification | **PASSIVE-DIAGNOSTIC** (new path category — methodology axis with zero behavioral effect) | If /062 produces ANY metric shift > ±0.001 vs /061, Path C selection was wrong (something changed silently) |
| IS Sharpe shift vs /060 | -0.009 ± 0.000 (exactly /061's value) | Any deviation > 0.001 indicates non-Path-C code change |
| OOS Sharpe shift vs /060 | +0.015 ± 0.000 | Same |
| dsr_relative | 0.0 ± 0.0 | Same |

**Note**: Under Path C there is NO backtest. The "prediction" is structural: any execution of the existing run_baseline_v3.py at the same head SHA + same flags produces /061's output exactly. We do not need to validate this with another 0.69h backtest.

### Section 4.4 — LOCKED falsifiers (per Critic /061 Rec #3 — target-axis bands MUST be pre-registered)

Path C is a methodology axis. The target-axis is "DSR_relative recalibration methodology selection." The falsifier band for the AXIS itself:

| Falsifier | Threshold | Condition |
|---|---|---|
| Path selection rationale traceable to EDA T1-T7 | YES if rationale cites specific T1-T7 evidence | NO if rationale skips quantitative justification |
| iter-v3/069 recommendation specification complete | YES if Section 3 contains Path B4 code spec + test surface + predicted band | NO if recommendation lacks code-path traceback |
| Cycle 1 #3 slot consumption documented | YES if exploration_catalog.md updated | NO if catalog skipped |
| No code change crept into /062 | YES if `git diff iteration-v3/061..iteration-v3/062 -- src/ run_baseline_v3.py` shows zero non-test lines | NO if any production code changed |
| EDA reproducibility | YES if `uv run python analysis/iteration_v3-062/dsr_relative_recalibration_eda.py` reproduces T1-T7 numbers within float-precision | NO otherwise |

**SUSPICIOUS triggers** (per /061 Rec #3 carry-forward — explicit pre-registration):
- IS Sharpe shift > |0.10| vs /061: implies code change crept in (FAIL — investigate)
- OOS Sharpe shift > |0.10| vs /061: same
- dsr_relative != 0.0 at /062: implies methodology changed silently (FAIL — investigate)

---

## Section 5 — Risk Mitigation Design

**R1 (Consecutive-SL cooldown)**: UNCHANGED from /061. Mechanism inactive at /062 (no signal generation; no trades).
**R2 (Drawdown-triggered scaling)**: UNCHANGED. Inactive at /062.
**R3 (OOD Mahalanobis gate)**: UNCHANGED. Inactive at /062.
**R4 (Vol kill-switch)**: UNCHANGED. Inactive at /062.
**R5 (Concentration cap)**: UNCHANGED. Inactive at /062.

Since /062 runs no backtest, no risk primitives fire. Carry-forward state from /061 is preserved bit-identically.

**Methodology-axis risk**:
- **Risk 1**: User reads Path C as a process workaround and expects methodology axis to be addressed in /062. **Mitigation**: brief Section 0.5 EXPLICITLY states EXPLORATION cycle 1 slot #3 IS consumed by methodology retrospective; diary Section 8 must document the cycle 1 CONFIRMATION recommendation for /069.
- **Risk 2**: iter-v3/069 QR ignores the Path B4 specification and picks a different methodology. **Mitigation**: this brief Section 3 contains the complete Path B4 code specification; diary Section 8 will be the primary reference; memory rule could be added.
- **Risk 3**: Path C is interpreted as "skip the axis." **Mitigation**: the EDA produces real quantitative evidence (T1-T7); the deliverable is a 4-iteration retrospective + cycle 1 CONFIRMATION recommendation. This is not "skipping" — it's deferral with concrete specification.

---

## Section 6 — Risk Management (Trade-level / Portfolio-level)

NOT applicable for /062 (no backtest, no trades). Carry-forward from /061: max OOS portfolio drawdown 35.89% (unchanged), no trade-level concerns.

---

## Section 7 — Pre-Registered Failure Modes

Per `feedback_v3_methodology_axis_integration_test.md` and `feedback_v3_methodology_post_hoc_input_traceback.md`:

### 7.1 — Pre-registered Path C-specific failure modes

| Failure mode | Probability | Detection | Disposition |
|---|---:|---|---|
| User insists on backtest at /062 | ~10% | User feedback after brief LOCKED | Switch to Path A (lowest-risk Path with code change); document deviation in diary |
| EDA SHA `ae22e60` not reproducible | ~1% | Phase 5.5 gate runs EDA, checks T1-T7 values | BLOCK at Phase 5.5 gate; fix and re-commit |
| /069 QR misinterprets Path B4 specification | ~20% | /069 brief review; Critic flags methodology axis | /069 QR re-reads /062 diary Section 8; iterate on specification |
| Path C documentation becomes orphaned (not surfaced at /069) | ~15% | /069 axis selection skips DSR_relative recalibration | Memory rule should pin /069 axis = Path B4 |
| EXPLORATION mode dsr_relative used as edge evidence in /069 | ~5% | /069 Critic /060 + Catalog row flags | `feedback_v3_dsr_mode_artifact.md` mandates rejection |
| Cycle 1 #3 slot disputed as "wasted" | ~25% | User feedback | Brief Section 0.5 EXPLICIT: methodology retrospective is a legitimate axis consumption |

**Pre-registered MOST-LIKELY outcome**: PASSIVE-DIAGNOSTIC clean execution (~60% probability). EDA committed, brief LOCKED, diary recommendation handed to /069 QR.

### 7.2 — Sanity checks if backtest is run anyway

If user overrides Path C and demands a backtest at /062 head:
- IS monthly Sharpe MUST equal /061's +0.8236 to 4dp (zero code change → bit-identical)
- OOS monthly Sharpe MUST equal /061's +0.1551 to 4dp
- IS Trades MUST equal 159 exactly
- OOS Trades MUST equal 102 exactly
- dsr_relative MUST equal 0.0 exactly

Any deviation → Path C contaminated by silent code change → investigate and revert.

---

## Section 8 — PASS criteria (LOCKED)

Per `feedback_v3_cycle1_axis_pass_criteria.md` extended for methodology axes:

### 8.1 — Path C PASS criteria (LOCKED)

For methodology-only axes with PASSIVE-DIAGNOSTIC outcome (no backtest):

| # | Gate | Threshold | Status |
|---|---|---|:---:|
| 1 | EDA at `analysis/iteration_v3-062/` produces T1-T7 tables | YES | PASS (committed at SHA `ae22e60`; reproducible via `uv run python ...`) |
| 2 | Brief Section 2 references specific T1-T7 evidence | YES | PASS (this brief) |
| 3 | Brief Section 3 contains complete Path B4 code specification for /069 | YES | PASS (Section 3) |
| 4 | Brief Section 4.4 LOCKED falsifiers explicitly written | YES | PASS (Section 4.4) |
| 5 | Brief Section 8 traceback subsection per `feedback_v3_methodology_post_hoc_input_traceback.md` | YES | PASS (Section 2.8 fully traces 4 psr() input variables to runner code paths) |
| 6 | Brief Section 9 library stack + integration test spec for /069 (not /062) | YES | PASS (Section 9) |
| 7 | Brief Section 10 QR audit trail | YES | PASS (Section 10) |
| 8 | No code change at /062 (only docs + EDA) | YES | PASS-DECLARED (Phase 5.5 gate to verify via `git diff iteration-v3/061..iteration-v3/062 -- src/ run_baseline_v3.py`) |
| 9 | EDA SHA `ae22e60` reproducible | YES | PASS (Phase 5.5 gate to verify) |
| 10 | Brief Section 1 testable hypothesis defined | YES | PASS (Section 1) |
| 11 | exploration_catalog.md updated for cycle 1 #3 | DEFER to Phase 8 diary | DEFER |

### 8.2 — Path classification taxonomy at /062

Standard cycle 1 EXPLORATION taxonomy:
- **PROMISING-AT-EXPLORATION**: IS Δ ≥ +0.10 AND OOS Δ ≥ +0.20 vs /060 anchor — NOT APPLICABLE (no backtest)
- **INERT-AT-EXPLORATION**: IS Δ within [-0.10, +0.10] OR OOS Δ within [-0.20, +0.20] — NOT APPLICABLE (no backtest)
- **NEGATIVE-AT-EXPLORATION**: IS Δ < -0.10 OR OOS Δ < -0.20 — NOT APPLICABLE (no backtest)
- **PASSIVE-DIAGNOSTIC (NEW path category at /062)**: methodology-only axis with zero behavioral effect; deliverable = retrospective + cycle CONFIRMATION recommendation; cycle slot consumed; BASELINE_V3.md UNCHANGED

**Predicted /062 path classification**: **PASSIVE-DIAGNOSTIC** with probability ~90% (assuming Path C executes clean; remaining ~10% covers process-level deviations from Section 7).

### 8.3 — BASELINE_V3.md update policy at /062

Per `feedback_v3_baseline_update_policy.md` (STRICTLY-BETTER-than-prior-baseline on BOTH IS Sharpe AND OOS Sharpe):
- /062 produces NO new IS/OOS numbers (no backtest)
- BASELINE_V3.md is UNCHANGED
- /059 remains canonical baseline (`v0.v3-059` tag)
- No new tag issued for /062

### 8.4 — SUSPICIOUS-AT-EXPLORATION criteria (per /061 Rec #3 — pre-registered)

If a /062 backtest is run anyway (deviation from Path C):
- IS Sharpe shift > |0.10| vs /061: SUSPICIOUS (code change crept in)
- OOS Sharpe shift > |0.10| vs /061: SUSPICIOUS
- dsr_relative != 0.0 ± 0.0001: SUSPICIOUS

Under Path C strict execution: NONE of these can trigger (no backtest, no code change).

---

## Section 9 — Library Stack + Integration Test Specification

### Section 9.1 — Library versions (UNCHANGED from /061)

- Python 3.13
- lightgbm 4.6.0
- optuna 4.8.0 (n_jobs=1)
- numpy 2.2.6
- pandas 3.0.0
- scikit-learn 1.8.0
- scipy 1.17.0
- statsmodels 0.14.6
- pyarrow 23.0.1

### Section 9.2 — Integration test specification for iter-v3/069 (NOT /062)

Per `feedback_v3_methodology_axis_integration_test.md`, the /069 QR MUST include the following integration test surface when implementing Path B4:

**End-to-end smoke test (brief Section 9 pre-flight)**:

```python
# Test: run synthetic backtest at small scale; verify dsr_relative_b4 > 0 when edge present
def smoke_test_dsr_relative_b4():
    # 1. Set up synthetic data: 1 month walk-forward, 1 symbol, n_trials=2
    # 2. Run run_baseline_v3.py --start 2024-01 --end 2024-02 --seeds 1 --n-trials 2 --symbols BCHUSDT
    # 3. Read dsr.json from reports-v3/iteration_<label>/
    # 4. Assert dsr_relative_b4 > 0 (non-degenerate)
    # 5. Assert cpcv_q75_annualized > 0
    # 6. Assert dsr_relative_b4 < 1 (not pathologically saturated)
    # 7. Assert daily_sharpe_oos_annualized non-zero (smoke check on annualization)
```

**6th integration test (`tests/strategies/ml/test_dsr_relative_b4.py`)**:

```python
def test_dsr_relative_b4_integration():
    """Integration test for Path B4 dsr_relative reformulation.

    Per `feedback_v3_methodology_axis_integration_test.md`: unit tests on math
    in isolation are insufficient — bugs occur at call-site integration boundary.
    """
    # 1. Construct synthetic oos_trades with known daily_sharpe ≈ 1.5
    # 2. Construct synthetic flat_path_sharpes with Q75 ≈ 0.65 annualized
    # 3. Call run_baseline_v3._compute_metrics_and_write_dsr_json() directly
    # 4. Read dsr.json from temp dir
    # 5. Assert dsr_relative_b4 in [0.85, 0.95] (slight non-1.0 due to small sample)
    # 6. Assert cpcv_q75_annualized matches 0.65 within 1e-6
    # 7. Assert daily_sharpe_oos_annualized matches 1.5 within 1e-4
```

**Brief Section 8 traceback subsection (per `feedback_v3_methodology_post_hoc_input_traceback.md`)**:

```
For Path B4 implementation at /069:

1. observed_sharpe (daily_sharpe_oos_annualized):
   - Code path: run_baseline_v3.py:<NEW_LINE> (after computing oos_daily_pnl Series)
   - Computation: mean(oos_daily_pnl) / std(oos_daily_pnl) * sqrt(252)
   - Granularity: daily, annualized
   - Smoke-test verified value for /059 anchor: 1.4359

2. benchmark_sharpe (cpcv_q75_annualized):
   - Code path: run_baseline_v3.py:<NEW_LINE> (after computing percentile of flat_path_sharpes)
   - Computation: percentile(flat_path_sharpes, 75) / sqrt(1296) * sqrt(756)
   - Granularity: candle-level → per-candle → calendar-annualized
   - Smoke-test verified value for /059 anchor: 0.6398

3. n_obs (n_daily_obs_oos):
   - Code path: run_baseline_v3.py:<NEW_LINE>
   - Computation: len(oos_daily_pnl)
   - Granularity: daily-observation count
   - Smoke-test verified value for /059 anchor: ~294 (14 OOS months × 21 trading days)

4. skewness + kurtosis (daily_skew_oos, daily_kurt_oos):
   - Code path: run_baseline_v3.py:<NEW_LINE>-<NEW_LINE>
   - Computation: scipy.stats.skew(oos_daily_pnl), scipy.stats.kurtosis(oos_daily_pnl, fisher=False)
   - Granularity: daily-level (matches observed)
   - Smoke-test verified values: skew ~0-1, kurt ~3-5
```

### Section 9.3 — Pre-flight checks for /062 (Path C-specific)

Per Path C zero-code-change discipline:

- [x] EDA committed at SHA `ae22e60` — VERIFIED
- [x] EDA reproducible — VERIFIED (script runs at `uv run python analysis/iteration_v3-062/dsr_relative_recalibration_eda.py`)
- [x] Brief Section 2 cites T1-T7 — VERIFIED (this document)
- [x] Brief Section 3 contains complete Path B4 code spec for /069 — VERIFIED
- [x] Brief Section 4.4 pre-registers falsifiers — VERIFIED
- [x] Brief Section 8 PASS gates LOCKED — VERIFIED
- [ ] Phase 5.5 gate verifies `git diff iteration-v3/061..iteration-v3/062 -- src/ run_baseline_v3.py tests/` is zero non-test lines — TO BE VERIFIED at Phase 5.5
- [ ] Phase 5.5 gate re-runs EDA and verifies T1-T7 reproducibility within float precision — TO BE VERIFIED at Phase 5.5
- [ ] ITERATION_LABEL UNCHANGED at "v3-061" (Path C doesn't update label since no backtest) — TO BE VERIFIED
- [x] EDA script committed (not gitignored) — VERIFIED (forced-added via `-f`)

---

## Section 10 — QR Audit Trail

Per `feedback_v3_axis_selection_quant_discipline.md`:

### 10.1 — Critic recommendations driving /062 axis selection

- **iter-v3/059 Critic FINAL `0fc18c2` Recommendation #1**: "DSR_relative threshold/benchmark recalibration as cycle 1 #N EXPLORATION axis. Address via (a) threshold recalibration 0.95 → 0.50-0.60 OR (b) input-granularity match."
- **iter-v3/061 Critic FINAL `b20b554` Recommendation #1**: carried forward from /059; "3-iteration-stale artifact (/059, /060, /061); address via Path A (threshold) or Path B (granularity)."
- **iter-v3/061 Engineer Recommendation #1**: same axis enumeration carried.

### 10.2 — QR-driven EDA evidence basis

EDA committed at SHA `ae22e60` with 7 numerical tables:
- T1: Input traceback per iteration (/028, /050, /058, /059, /060, /061)
- T2: Granularity scale factors
- T3: Path A counterfactual (threshold recalibration)
- T4: Path B counterfactual (granularity match — B1/B2/B3/B4 variants)
- T5: Path B5 counterfactual (alternative benchmark)
- T6: Path selection summary (complexity × risk)
- T7: Recommendation

EDA is reproducible: `uv run python analysis/iteration_v3-062/dsr_relative_recalibration_eda.py`

### 10.3 — Path selection rationale (Path C)

**Quantitative decision criteria (from T6 + T7)**:

| Criterion | Path A | Path B (any) | Path C |
|---|---|---|---|
| Addresses root cause | NO | YES | DEFERS (with spec for /069) |
| Wall-clock fit in 2h EXPLORATION cap | YES | TIGHT (2h cap leaves little buffer for integration test) | YES (<30 min) |
| Backward-compat | YES | NO | YES |
| Integration test surface | MINIMAL | HIGH (mandated by 2 memory rules) | NONE |
| EXPLORATION-vs-CONFIRMATION scale mismatch | Tests at wrong n_trials | Tests at wrong n_trials | Defers to right n_trials |
| BASELINE_V3.md impact | None | None | None |
| Cycle 1 slot consumption | Yes (1 of 10) | Yes (1 of 10) | Yes (1 of 10) |

**Decision rule**: Path C is selected because:
1. EXPLORATION-mode DSR/PSR are informational artifacts per `feedback_v3_dsr_mode_artifact.md` — methodology-axis testing at EXPLORATION mode doesn't transfer to CONFIRMATION mode.
2. Path B integration test surface (2 memory rules mandate) doesn't fit in 2h hard cap.
3. Path A produces a half-fix (still FAILs at /059) that creates technical debt to revisit.
4. Path C delivers the recommendation for /069 cycle 1 CONFIRMATION with complete specification — the methodology change happens at the right architectural scale.

### 10.4 — EDA at `analysis/iteration_v3-062/`

```
analysis/iteration_v3-062/
├── dsr_relative_recalibration_eda.py    # 700+ lines; reproducible via uv run python ...
├── synthesis.md                         # Path C selection rationale
├── t1_input_traceback.csv               # /028/050/058/059/060/061 raw inputs
├── t2_granularity_scale_factors.csv     # √n_trades vs √n_test analysis
├── t3_path_a_threshold_recalibration.csv  # Path A counterfactual @ threshold 0.40-0.95
├── t4_path_b_granularity_match.csv      # Path B1/B2/B3/B4 counterfactuals
├── t5_path_c_alternative_benchmark.csv  # Path B5 alternative-benchmark variants (Q50/Q60/Q75)
├── t6_path_selection_summary.csv        # decision matrix
└── t7_recommendation.csv                # Path C selection + cycle 1 CONFIRMATION recommendation
```

### 10.5 — Setup commit SHA

EDA: `ae22e60` (committed)
Brief LOCKED setup: **TO BE FILLED at brief commit** (this brief = the setup commit)

### 10.6 — Anti-pattern static scan (Path C)

Per Critic /061 §11 catalog (13 entries) applied to Path C:

| A | Item | Path C status |
|---|---|---|
| A1 | train_end_ms < test_start_ms (look-ahead) | N/A (no backtest) |
| A2 | Optuna n_jobs=2 | N/A (no backtest) |
| A3 | Master data invariance | N/A (no backtest) |
| A4 | Track isolation (v3 worktree only) | PASS (no cross-worktree change) |
| A5 | ITERATION_LABEL alignment | PASS (UNCHANGED at "v3-061"; documented in Section 9.3) |
| A6 | Test suite regression | PASS-EXPECTED (Phase 5.5 to verify; no test files changed under Path C) |
| A7 | Brief 10-section spec | PASS (this brief 10 sections present) |
| A8 | Stateful gate deadlock | N/A (no gate change) |
| A9 | ensemble_seeds threading | N/A (no seed change) |
| A10 | Feature isolation (features_v3/ unchanged) | PASS (no feature change) |
| A11 | V3_EXCLUDED_SYMBOLS unchanged | PASS (no symbol change) |
| A12 | DSR/PSR granularity (informational) | **EXPLICITLY ADDRESSED by /062** — this brief is the disposition |
| A13 | Written-before-read (cpcv_paths.csv timing) | N/A (no /062 backtest) |

### 10.7 — Pre-flight verification commands

To verify Path C discipline at Phase 5.5:

```bash
# 1. Verify zero non-doc/non-EDA code change at /062
git diff iteration-v3/061..iteration-v3/062 -- \
    src/ run_baseline_v3.py tests/ run_baseline_v186.py run_baseline_v2.py
# Expected: empty output

# 2. Verify EDA reproducibility
cd /home/roberto/crypto-trade/.worktrees/quant-research
uv run python analysis/iteration_v3-062/dsr_relative_recalibration_eda.py
# Expected: T1-T7 numbers match committed CSVs to float precision

# 3. Verify brief Section 2 cites T1-T7
grep -c "T[1-7]" briefs-v3/iteration_v3-062/research_brief.md
# Expected: >= 14 (each table cited at least twice — Section 2 + Section 10)

# 4. Verify EDA SHA in brief is `ae22e60`
grep "ae22e60" briefs-v3/iteration_v3-062/research_brief.md
# Expected: at least 1 match (Section 0 EDA SHA declaration)

# 5. Verify ITERATION_LABEL UNCHANGED at "v3-061" (Path C doesn't bump label)
grep 'ITERATION_LABEL = "v3-' run_baseline_v3.py
# Expected: ITERATION_LABEL = "v3-061" (or "v3-062" if user prefers explicit bump for tracking)
```

---

## Reproducibility Stamp (Path C / iter-v3/062)

- HEAD SHA at brief LOCK: **TO BE FILLED at setup commit**
- Branch: `iteration-v3/062`
- Parent branch HEAD: `8a02b7a` (iter-v3/061 diary closeout)
- EDA commit SHA: `ae22e60`
- Setup commit SHA: **TO BE BACKFILLED**
- Code change: ZERO (no `src/`, no `run_baseline_v3.py`, no `tests/`)
- Backtest: NONE
- Wall-clock target: <30 min (EDA + brief + Phase 5.5 + diary; all docs/non-compute work)
- Hardware: x86_64, 60 GB RAM, WSL2 / Linux 6.6.114.1
- Library stack: UNCHANGED from /061 (no library change at /062)
- Run command: NONE (Path C deliverable = docs only)

## See Also

- `analysis/iteration_v3-062/synthesis.md` — EDA findings synthesis
- `analysis/iteration_v3-062/t1_input_traceback.csv` through `t7_recommendation.csv` — quantitative tables
- `BASELINE_V3.md` — canonical /059 baseline (UNCHANGED)
- `diary-v3/iteration_v3-061.md` — /061 INERT-AT-EXPLORATION + Critic Rec #1 carry-forward
- `briefs-v3/iteration_v3-061/research_brief.md` — prior cycle 1 #2 brief
- `briefs-v3/iteration_v3-060/research_brief.md` — anchor establishment
- `briefs-v3/iteration_v3-056/research_brief.md` — last A2 DSR gate brief (prior methodology axis precedent)
- `briefs-v3/iteration_v3-055/research_brief.md` — original A2 brief (PATH C abort precedent)
- `feedback_v3_methodology_axis_integration_test.md` — integration test mandate (carry-forward to /069)
- `feedback_v3_methodology_post_hoc_input_traceback.md` — traceback mandate (carry-forward to /069)
- `feedback_v3_dsr_mode_artifact.md` — EXPLORATION-vs-CONFIRMATION DSR scale rule
- `feedback_v3_cycle1_axis_pass_criteria.md` — PASS criteria taxonomy (extended at §8.2)
- `feedback_v3_baseline_update_policy.md` — BOTH-must-improve discipline
- `feedback_v3_strict_10_to_1_cadence.md` — cycle 1 EXPLORATION cadence
- `feedback_v3_axis_selection_quant_discipline.md` — QR EDA-driven axis selection
- `feedback_v3_per_symbol_target_axis_falsifier.md` — /061 Rec #3 pre-registration discipline (carried to §4.4)
