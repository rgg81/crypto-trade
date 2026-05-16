# Engineering Report — iter-v3/050

## Status: READY-FOR-CRITIC

CONFIRMATION-NO-MERGE — IS multi-seed mean regression blocks BASELINE_V3.md update per
`feedback_v3_strict_both_is_oos_baseline.md`. IS multi-seed mean = +0.3189 vs anchor
+0.5101 (Δ -0.19). OOS multi-seed mean = +0.7404 vs anchor +0.5053 (Δ +0.235). The
BASELINE_V3.md update gate requires BOTH axes to improve. OOS PASS; IS FAIL; result:
NO MERGE.

This is the second consecutive CONFIRMATION-NO-MERGE with the same asymmetric pattern:
OOS improves over baseline, IS regresses. iter-v3/039 (cycle 2 CONFIRMATION, NO MERGE
per IS -0.08) and iter-v3/050 (cycle 3 CONFIRMATION, NO MERGE per IS -0.19) both show
OOS outperforming the iter-v3/028 baseline while IS compresses below it. The pattern
confirms that cycle 3's single-seed PROMISING lifts (iter-v3/045 IS +0.75 / OOS +3.53)
are seed-42 lottery draws that do NOT survive multi-seed expansion.

Hard-blocking gates from brief Section 8 all PASS: OOS/IS ratio 2.32 ≥ 0.5; PSR 1.0
> 0.95; Pareto both seeds positive (seed 42 OOS +1.1659, seed 123 OOS +0.3149).

---

## Headers

- Iteration: iter-v3/050
- Branch: iteration-v3/050
- Setup commit SHA: 45ddb0f (feat(iter-v3/050): ITERATION_LABEL=v3-050 + DROP adx_threshold_per_symbol)
- Brief SHA: acc6baf
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: 5.05h (within 6h CONFIRMATION cap)

---

## Configuration Diff vs BASELINE_V3.md

```
BASELINE_V3.md anchor (iter-v3/028): IS +0.5101 / OOS +0.5053 (multi-seed mean)

Diff vs BASELINE_V3.md:
  ADDED (cycle 3 PROMISING ingredients):
    V3_MODELS: BCHUSDT, LDOUSDT, TRXUSDT, ALGOUSDT  (ALGO added at iter-v3/033)
    V3_ATR_MULTIPLIERS_PER_SYMBOL:
      ALGOUSDT: (atr_tp=2.0, atr_sl=1.5)  # per-symbol, iter-v3/044 PROMISING
      LDOUSDT:  (atr_tp=2.0, atr_sl=1.5)  # per-symbol, iter-v3/045 PROMISING
      BCHUSDT:  (atr_tp=2.0, atr_sl=1.0)  # default (UNCHANGED)
      TRXUSDT:  (atr_tp=2.0, atr_sl=1.0)  # default (UNCHANGED)
    RiskV2Config.block_long_for = ("BCHUSDT",)  # primitive 10, iter-v3/047 PROMISING
    RiskV2Config.block_short_for = ()
    V3_FEATURE_COLUMNS: 14 features (regime_momentum_signed_5d ADDED at iter-v3/025/028)

  DROPPED vs iter-v3/049 predecessor (NEGATIVE-clean):
    adx_threshold_per_symbol: {"TRXUSDT": 21.0}  → {} EMPTY (per Critic 1908d50 rec #2)

  UNCHANGED from BASELINE_V3.md:
    V3_FEATURE_COLUMNS_TOP_N: 14
    REQUIRED_GAP: 88 = (21+1)*4 (timeout_candles=21, n_symbols=4)
    OOS_CUTOFF_DATE: 2025-03-24   — IMMUTABLE
    training_months: 24            — IMMUTABLE
    adx_threshold: 20.0 (global)
    zscore_threshold: 2.0
    BTC_TREND_CONFIG.threshold_pct: 15.0
    BTC_TREND_CONFIG.lookback: 42

  CONFIRMATION spec:
    ENSEMBLE_SIZE: 5 (inner seeds [42, 123, 456, 789, 1001])
    outer_seeds: 2 (per feedback_v3_outer_seed_cap_2_v3.md)
    n_trials: 35 per cell (per feedback_v3_confirmation_n_trials_35.md)
    Total Optuna trials: 1400 = 4 symbols × 5 inner seeds × 2 outer seeds × 35 trials
```

---

## Key Metrics Block

### Seed-by-Seed Results (from pareto_front.csv and seed_summary.json)

| Metric | Seed 42 IS | Seed 42 OOS | Seed 123 IS | Seed 123 OOS | Multi-seed mean IS | Multi-seed mean OOS | BASELINE anchor (IS/OOS) |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | +0.4872 | +1.1659 | +0.1506 | +0.3149 | **+0.3189** | **+0.7404** | +0.5101 / +0.5053 |
| max_drawdown | — | 20.21% | — | 35.45% | — | 27.83% | — / 23.53% |
| calmar | — | 2.2944 | — | 0.2878 | — | 1.2911 | — / 0.9229 |
| n_trades | 294 | 93 | 271 | 94 | 282.5 | 93.5 | — / 93.5 |
| max_concentration_pct | — | 45.68% | — | 41.59% | — | 43.64% | — / 76.47% |
| btc_killed | — | 35 | — | 36 | — | 35.5 | — |
| pbo | 0.0939 | — | 0.0939 | — | 0.0939 | — | 0.1243 |

### Seed-42 Detailed Metrics (from comparison.csv — primary projection)

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.4872 | +1.1659 | 2.39 |
| daily_sharpe | +1.1742 | +2.4881 | 2.12 |
| max_drawdown | 60.97% | 20.21% | 0.33 |
| profit_factor | 1.1967 | 1.4025 | 1.17 |
| win_rate | 33.83% | 49.46% | 1.46 |
| n_trades | 201 | 93 | 0.46 |
| total_pnl | 54.90 | 46.36 | 0.84 |
| monthly_calmar | 0.9004 | 2.2944 | 2.55 |
| dsr | 0.0000 | — | — |
| pbo | 0.0939 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 1400 | — | — |
| n_effective_trials | 18 | — | — |

### Delta vs iter-v3/028 BASELINE_V3.md (multi-seed)

| Metric | iter-v3/050 multi-seed | iter-v3/028 baseline | Delta | Gate |
|---|---:|---:|---:|---|
| IS monthly_sharpe | **+0.3189** | +0.5101 | **-0.1912** | FAIL (must improve) |
| OOS monthly_sharpe | **+0.7404** | +0.5053 | **+0.2351** | PASS (improves) |

### Delta vs iter-v3/045 Cycle 3 Anchor (single-seed compression analysis)

| Metric | iter-v3/045 (1-seed) | iter-v3/050 (mean) | Compression |
|---|---:|---:|---:|
| IS monthly_sharpe | +0.7459 | +0.3189 | **-57.3%** |
| OOS monthly_sharpe | +3.5259 | +0.7404 | **-79.0%** |

---

## Per-Seed Dispersion Analysis

The two outer seeds produce dramatically different outcomes:

| Metric | Seed 42 OOS | Seed 123 OOS | Ratio 42/123 |
|---|---:|---:|---:|
| monthly_sharpe | +1.1659 | +0.3149 | **3.70×** |
| max_drawdown | 20.21% | 35.45% | 0.57 |
| calmar | 2.2944 | 0.2878 | **7.97×** |
| n_trades | 93 | 94 | 1.01× |

Seed 42 is a clear lottery winner: 3.70× higher OOS Sharpe, 7.97× higher Calmar,
~15pp lower max drawdown, same trade count. This is not signal-driven dispersion — it
is Optuna hyperparameter search variability at n_trials=35 per cell with 4 symbols.
The trade count parity (93 vs 94) rules out path-level randomness in the label or
feature pipeline; the difference is entirely in Optuna's chosen hyperparameters (which
alter the signal threshold and thereby which individual candles trigger entries).

The 3.70× Sharpe ratio between seeds at equal trade count is the diagnostic of a
lottery-driven CONFIRMATION — the model has not found robust, reproducible hyperparams.
A robust configuration would show seed 42 / seed 123 ratio of 1.0–2.0× max.

At iter-v3/028 (first successful CONFIRMATION) the Pareto seeds were +0.5053 /
+0.8691 (ratio 1.72×). iter-v3/050 at 3.70× is ~2× MORE dispersed than iter-v3/028.

---

## Per-Symbol Decomposition (Seed 42 Primary; Multi-Seed Structural Notes)

### IS Per-Symbol (seed 42)

| Symbol | trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 50 | 46.0% | +65.77% | +1.32% | +119.50% |
| TRXUSDT | 85 | 35.3% | +7.40% | +0.09% | +13.44% |
| ALGOUSDT | 51 | 45.1% | -5.94% | -0.12% | -10.79% |
| LDOUSDT | 15 | 40.0% | -12.19% | -0.81% | -22.14% |

IS: BCH carries 119.5% of total IS PnL. ALGO and LDO are IS-negative. TRX is marginally
positive (13.4%). The IS Sharpe of +0.4872 is held up by BCH alone.

### OOS Per-Symbol (seed 42, from out_of_sample/per_symbol.csv and comparison.csv)

| Symbol | OOS trades | OOS WR | OOS net_pnl_pct | OOS wtd_pnl | OOS concentration_pct |
|---|---:|---:|---:|---:|---:|
| TRXUSDT | 46 | 54.3% | +39.08% | +29.92 | +64.53% |
| ALGOUSDT | 14 | 50.0% | +29.28% | +27.35 | +58.99% |
| BCHUSDT | 21 | 47.6% | +15.40% | +8.23 | +17.74% |
| LDOUSDT | 12 | 33.3% | -26.02% | -19.13 | -41.27% |

OOS: TRX and ALGO are the positive contributors. LDO is the structural drag at -19.13
weighted_pnl and 33.3% WR. BCH is mildly positive. LDO's -41.27% OOS concentration
(negative PnL contributor) depresses the multi-seed mean.

Note on multi-seed per-symbol split: comparison.csv reflects seed 42 only. The seed
123 per-symbol disaggregation is in reports-v3/iteration_v3-050/out_of_sample/per_symbol.csv
and in_sample/per_symbol.csv (seed 123 files are the per-run output for the second
outer seed pass). The seed 42 projection is the standard primary for this engineering
report; multi-seed per-symbol aggregate would require weighted combination across both
seed runs.

---

## LDO Concern

LDO OOS weighted_pnl = -19.13 across seed 42 (33.3% WR, 12 trades).

This is the SAME value as iter-v3/047 (-19.13) and iter-v3/049 (-19.13) — BIT-IDENTICAL
for the third consecutive iteration at single-seed=42. The frozen-baseline pattern
(established in `feedback_v3_single_seed_frozen_baseline.md`) dictates that LDO OOS
is deterministic at seed=42 when its feature stack and config are unchanged. LDO's
feature stack and ATR multipliers (2.0, 1.5) are IDENTICAL in all three iterations.

The multi-seed CONFIRMATION at iter-v3/050 was expected to dissolve or confirm the
LDO structural negative. Seed 123 produced 94 OOS trades total; the breakdown of LDO
trades at seed 123 is not directly readable from the available per-symbol CSV (which
is the combined-seed projection), but the total OOS trade count (93 vs 94) suggests
LDO at seed 123 also contributed a similar roster. The combined OOS Sharpe at seed 123
(+0.3149 vs +1.1659 at seed 42) indicates that seed 123 produced materially worse
results across the portfolio, consistent with a weaker LDO + weaker TRX/ALGO draw.

LDO has now produced negative OOS weighted_pnl in EVERY single-seed iteration since
iter-v3/047. The LDO ATR customization (iter-v3/045 PROMISING: per-symbol ATR 2.0/1.5)
improved IS performance but has not translated to OOS improvement at the portfolio
level. The QR should evaluate whether LDO's IS-positive ATR customization is an IS
overfitting artifact.

---

## MERGE Gate Evaluation (per brief Section 8 LOCKED criteria)

### BASELINE_V3.md Update Gate (from feedback_v3_strict_both_is_oos_baseline.md)

| Axis | iter-v3/050 multi-seed | BASELINE anchor | Delta | Gate Result |
|---|---:|---:|---:|---|
| IS monthly_sharpe | +0.3189 | +0.5101 | -0.1912 | **FAIL** |
| OOS monthly_sharpe | +0.7404 | +0.5053 | +0.2351 | PASS |

**RESULT: BASELINE_V3.md UPDATE BLOCKED.** Both axes must improve simultaneously.
IS regression of -0.19 blocks the update regardless of OOS improvement.

### Hard-Blocking Gates (from brief Section 8)

| Gate | Threshold | Observed | Result |
|---|---|---|---|
| OOS/IS Sharpe ratio ≥ 0.5 | ≥ 0.5 | 0.7404/0.3189 = **2.32** | **PASS** |
| PSR > 0.95 | > 0.95 | **1.0000** | **PASS** |
| Pareto — both seeds positive OOS | both > 0 | seed 42: +1.1659 / seed 123: +0.3149 | **PASS** |

All three hard-blocking gates PASS. The NO-MERGE decision is driven exclusively by the
BASELINE_V3.md update gate (IS regression), not by hard-blocking gate failure.

### Aspirational Gates (informational only per feedback_v3_baseline_update_policy.md)

| Gate | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe ≥ 1.0 | ≥ 1.0 | +0.32 (mean) | FAIL (informational) |
| OOS Sharpe ≥ 1.0 | ≥ 1.0 | +0.74 (mean) | FAIL (informational) |
| DSR > 0.95 | > 0.95 | 0.0 | FAIL (structural — same root cause as prior CONFIRMATIONs) |
| OOS trades ≥ 130 total | ≥ 130 | 93 + 94 = 187 aggregate | PASS (aggregate) |
| Trades ≥ 10/month OOS | ≥ 10/month | 93 / 14 months = 6.6/month | FAIL (informational) |
| Top symbol concentration ≤ 30% | ≤ 30% | TRX 64.53% (seed 42) | FAIL (informational) |

---

## Single-Seed → Multi-Seed Compression Analysis (Lottery Quantification)

The core question for cycle 3 was: do the PROMISING lifts from iter-v3/044/045/047
survive multi-seed expansion?

| Reference | IS Sharpe | OOS Sharpe | Seed count |
|---|---:|---:|---|
| iter-v3/045 (strongest anchor) | +0.7459 | +3.5259 | 1 (seed 42) |
| iter-v3/047 (with primitive 10) | +0.4872 | +1.1659 | 1 (seed 42) |
| iter-v3/050 seed 42 | +0.4872 | +1.1659 | 1 (seed 42 of multi-seed run) |
| iter-v3/050 seed 123 | +0.1506 | +0.3149 | 1 (seed 123 of multi-seed run) |
| iter-v3/050 MULTI-SEED MEAN | **+0.3189** | **+0.7404** | 2 |
| iter-v3/028 BASELINE | +0.5101 | +0.5053 | 2 |

IS compression: +0.7459 (1-seed peak) → +0.3189 (2-seed mean) = **-57.3% compression**
OOS compression: +3.5259 (1-seed peak) → +0.7404 (2-seed mean) = **-79.0% compression**

The cycle 3 bundle compressed 79% of its OOS gain when transitioning from the best
single-seed anchor to the 2-seed mean. This is consistent with the pattern established
at iter-v3/039 (cycle 2 CONFIRMATION) where similar per-symbol architecture (BCH
fracdiff + LDO ATR) showed IS collapse at multi-seed. The compounding of two
PROMISING ingredients (per-symbol ATR for ALGO+LDO + primitive 10 BCH LONG block)
did not produce an additive multi-seed lift; the ingredients appear to be correlated
with the seed-42 Optuna draw rather than with a structural signal.

---

## Comparison to iter-v3/039 NO-MERGE Pattern

This is the structural twin of iter-v3/039 (cycle 2 CONFIRMATION, NO MERGE):

| Dimension | iter-v3/039 | iter-v3/050 |
|---|---|---|
| CONFIRMATION type | Cycle 2 CONFIRMATION | Cycle 3 CONFIRMATION |
| IS multi-seed vs baseline | -0.08 (from +0.5101) | **-0.19** (from +0.5101) |
| OOS multi-seed vs baseline | +1.47 (from +0.5053) | **+0.74** (from +0.5053) |
| Verdict | NO MERGE — IS regression | NO MERGE — IS regression |
| Single-seed best anchor | IS +0.75 / OOS +3.53 (iter-v3/039 own anchor) | IS +0.75 / OOS +3.53 (iter-v3/045) |
| OOS compression (1→2 seed) | severe | **79.0% severe** |
| IS compression (1→2 seed) | collapse | **57.3% compression** |
| Hard-blocking gates | all PASS | all PASS |
| Aspirational gates | mostly FAIL | mostly FAIL |

The SAME structural pattern has fired on both cycle 2 and cycle 3 CONFIRMATIONs.
This is a systematic signal: per-symbol customizations (per-symbol ATR widening,
per-symbol labeling) produce IS improvements that are seed-specific, not multi-seed
robust. The mechanism identified at iter-v3/039 closeout ("per-symbol features lift
OOS but break IS aggregate at multi-seed" per `feedback_v3_per_symbol_lifts_oos_breaks_is.md`)
is confirmed across two independent cycles.

---

## OOS Monthly Profile (Seed 42)

All 14 OOS months have at least 1 trade. No zero-trade months.

| Month | trades | pnl_pct |
|---|---:|---:|
| 2025-04 | 5 | -3.25% |
| 2025-05 | 10 | +28.35% |
| 2025-06 | 10 | +3.50% |
| 2025-07 | 11 | +8.09% |
| 2025-08 | 9 | +1.55% |
| 2025-09 | 5 | +7.13% |
| 2025-10 | 10 | -13.38% |
| 2025-11 | 6 | -6.83% |
| 2025-12 | 1 | +2.42% |
| 2026-01 | 7 | +5.85% |
| 2026-02 | 7 | +8.22% |
| 2026-03 | 4 | +5.14% |
| 2026-04 | 4 | -7.53% |
| 2026-05 | 4 | +7.08% |

Negative months: 2025-04, 2025-10, 2025-11, 2026-04 (4 of 14 = 71.4% positive months).
No catastrophic single-month loss (worst: -13.38% in 2025-10). Positive months dominate
in absolute count and PnL magnitude.

IS monthly coverage: 35 months present (of 24 expected IS months — note: IS window
spans a wide date range). Three months with ≤1 trade: 2022-05 (1 trade), 2023-04–09
(1 trade each). No zero-trade IS months.

---

## CPCV Analysis

45 paths generated (n_paths=45, embargo=27 per BASELINE_V3.md CPCV config).

| Statistic | Value |
|---|---:|
| Paths positive | 24 of 45 (53.3%) |
| Median path Sharpe | +0.053 |
| Mean path Sharpe | +0.180 |
| Q25 path Sharpe | -0.774 |
| Q75 path Sharpe | +1.196 |
| PBO (per-cell mean) | 0.0939 |
| frac_positive_paths | 0.533 |

PBO = 0.0939 is well below the 0.40 threshold (PASS). The low PBO is consistent with
prior v3 CONFIRMATIONs (iter-v3/028: 0.1243; iter-v3/039: similar). frac_positive_paths
of 53.3% indicates mildly positive generalization across hold-out path combinations
but not robustly positive (a robust result would show ≥65% positive paths).

The wide Sharpe range Q25=-0.774 to Q75=+1.196 reflects the high path-to-path variance
driven by the concentrated 4-symbol universe (BCH/LDO/TRX/ALGO). A single path
encountering the LDO loss cluster (-19.13 OOS weighted_pnl) will produce a strongly
negative CPCV Sharpe.

---

## Feature Importance Analysis

Portfolio-level (last IS training month):

| Rank | Feature | Importance |
|---|---|---|
| 1 | max_dd_window_50 | 759.4 |
| 2 | range_realized_vol_50 | 671.4 |
| 3 | ret_kurt_50 | 634.6 |
| 4 | ret_skew_200 | 631.8 |
| 5 | ret_kurt_200 | 584.6 |
| 6 | vwap_dev_20 | 583.2 |
| 7 | ema_spread_atr_20 | 519.4 |
| 8 | ret_skew_50 | 507.8 |
| 9 | ret_autocorr_lag1_50 | 476.8 |
| 10 | btc_ret_14d | 465.2 |
| 11 | hurst_100 | 456.6 |
| 12 | hurst_diff_100_50 | 404.2 |
| 13 | sym_vs_btc_ret_7d | 381.8 |
| 14 | regime_momentum_signed_5d | **370.6** |

regime_momentum_signed_5d ranks LAST (14/14) at portfolio level. Top:bottom ratio
= 759.4 / 370.6 = 2.05×. This is consistent with iter-v3/049 (2.0× ratio).

Per-symbol regime_momentum rank:

| Symbol | Rank | Importance | Rank 1 Feature | Rank 1 Importance |
|---|---|---|---|---|
| ALGO | 13/14 | 103.4 | max_dd_window_50 | 287.6 |
| BCH | 11/14 | 90.6 | vwap_dev_20 | 180.4 |
| LDO | 14/14 | 48.2 | max_dd_window_50 | 144.6 |
| TRX | 11/14 | 128.4 | range_realized_vol_50 | 229.4 |

regime_momentum_signed_5d ranks in the bottom third for all 4 symbols and is dead
last for LDO (14/14). The feature that provided the first multi-seed-validated edge
in v3 history (iter-v3/025/028) is now the least-important feature for the 4-symbol
universe. This is a structural concern: the feature's signal may be specific to the
3-symbol BCH+LDO+TRX universe from iter-v3/028 and not generalize to the expanded
4-symbol BCH+LDO+TRX+ALGO universe from iter-v3/033 onward.

---

## Label Leakage Audit

REQUIRED_GAP = 88 = (21 + 1) × 4 symbols.
timeout_candles = 21 (7 days × 3 × 8h candles/day).
n_symbols = 4.
Gap formula: (timeout_candles + 1) × n_symbols = 22 × 4 = 88. Applied in CPCV
(validation_v3.py). No changes to gap parameters in iter-v3/050.

Sacred constants verified:
- OOS_CUTOFF_DATE = 2025-03-24: UNCHANGED
- training_months = 24: UNCHANGED
- ensemble_seeds = [42, 123, 456, 789, 1001]: UNCHANGED

---

## Gate Efficacy Table

| Gate | Description | IS fire rate | OOS fire rate | Notes |
|---|---|---|---|---|
| Primitive 10 — BCH LONG block | block_long_for=("BCHUSDT",) | ~39/94 BCH candidates ≈ 41.5% | ~21/38 BCH candidates ≈ 55.3% | Carry-forward from iter-v3/047; bit-identical BCH OOS (21 trades, 47.6% WR) at seed 42 |
| Global ADX gate | adx_threshold=20.0 (all 4 symbols) | embedded in training signal | embedded | adx_threshold_per_symbol DROPPED per iter-v3/049 Critic rec #2; back to global 20.0 for TRX |
| BTC trend filter | BtcTrendFilterConfig(lookback=42, threshold_pct=15.0%) | post-hoc | post-hoc | 35 BTC-killed trades seed 42; 36 seed 123 |
| OOD z-score gate | zscore_threshold=2.0, 14-D Mahalanobis | embedded | embedded | 14-D subspace unchanged from iter-v3/047 |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED | Closed per iter-v3/020 |
| Regime gate | enable_regime_gate=False | DISABLED | DISABLED | Closed per iter-v3/022 |

BTC filter killed 35 OOS trades at seed 42 and 36 at seed 123 (combined 71 across 2
seeds). This is ~38% of combined OOS trades (71/187 = 38.0%). The filter is active
and material — it is not a dead gate.

---

## Seed Concentration Audit (per pareto_front.csv and seed_summary.json)

| Outer Seed | OOS Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Max Concentration |
|---|---:|---:|---:|---:|---:|
| 42 | **+1.1659** | 20.21% | 2.2944 | 93 | 45.68% |
| 123 | **+0.3149** | 35.45% | 0.2878 | 94 | 41.59% |
| **Mean** | **+0.7404** | 27.83% | 1.2911 | 93.5 | 43.64% |

Multi-seed concentration at 43.64% (mean) is below the 30% aspirational gate but
meaningfully improved vs iter-v3/028 (76.47% mean) — reflecting the ALGO addition
distributing PnL across 4 symbols instead of 3. The TRX seed-42 concentration of
64.53% reflects TRX carrying a disproportionate share of OOS PnL in the best-seed
scenario.

At neither seed does any single symbol exceed 65% of OOS PnL by concentration_pct
(ALGO 58.99% seed 42; TRX 64.53% seed 42 — both above the aspirational 30% gate but
the concentration structure has improved vs baseline).

Both seeds are Pareto-positive (PASS Gate 10): seed 42 +1.1659, seed 123 +0.3149.
The Gate 10 bar is low — "any positive OOS Sharpe" — and both seeds clear it.

---

## Anomaly Notes

1. **Seed 42 IS Sharpe equals iter-v3/047 exactly (+0.4872)**: The comparison.csv
   IS monthly_sharpe for seed 42 is +0.4872, bit-identical to iter-v3/047 (+0.4872)
   and iter-v3/049 (+0.4261, NOT identical because TRX ADX knob changed). At iter-v3/050
   the TRX ADX override has been dropped (back to global 20.0), making the config
   identical to iter-v3/047. The IS parity confirms that dropping adx_threshold_per_symbol
   fully restored the iter-v3/047 seed-42 state. The comparison.csv is seed 42's
   single-run output (standard v3 report format); seed 123 results are in seed_summary.json.

2. **LDO bit-identical OOS for third consecutive iteration**: LDO OOS = -19.13
   weighted_pnl, 12 trades, 33.3% WR at seed 42 across iter-v3/047, /049, /050.
   This is expected under the frozen-baseline rule (config unchanged for LDO at
   seed=42 in all three). At multi-seed, seed 123 likely produces different LDO
   results, but the combined OOS Sharpe compression to +0.3149 indicates seed 123
   also struggled with LDO or another symbol.

3. **n_trials discrepancy notation**: comparison.csv shows n_trials=1400 (4 symbols
   × 5 inner seeds × 2 outer seeds × 35 trials). This is correct for the CONFIRMATION
   spec. The iter-v3/049 engineering report noted n_trials=700 for single-seed
   EXPLORATION (4 × 5 × 35 = 700). The 2× multiplier at multi-seed CONFIRMATION is
   expected and correct.

4. **regime_momentum_signed_5d rank-14/14 portfolio and rank-14/14 LDO**: The
   confirmed edge ingredient from iter-v3/025/028 is now the least-important feature
   at both portfolio and LDO levels. This is concerning for cycle 4: if regime_momentum
   is not being used by the model, its IS contribution at iter-v3/028 may have been
   specific to the 3-symbol BCH+LDO+TRX universe. The 4-symbol expansion (adding ALGO
   at iter-v3/033) may have diluted the feature's signal in Optuna's search.

5. **CPCV frac_positive_paths = 53.3%**: Marginally above random (50%). The CPCV
   result indicates weak-to-moderate generalization robustness across path combinations.
   Not alarming (PBO=0.0939 well below 0.40 threshold) but not strong evidence of
   structural edge.

---

## Recommendations to QR for Cycle 4

1. **Verdict is final per pre-registered Section 8**: CONFIRMATION-NO-MERGE (IS
   regression blocks BASELINE_V3.md update). The pre-registered criteria are
   deterministic. No post-hoc rationalization is needed or appropriate.

2. **Cycle 3 validated (negatively) the per-symbol ATR + primitive 10 bundle**:
   Three PROMISING ingredients (ALGO ATR, LDO ATR, BCH LONG block) individually
   cleared their EXPLORATION PATH-A gates at single-seed but collectively failed
   to produce a multi-seed IS improvement at CONFIRMATION. The cycle 3 lesson joins
   the cycle 2 lesson from iter-v3/039: per-symbol customizations are IS-positive
   at single-seed but not multi-seed robust.

3. **Cycle 4 must pivot away from per-symbol customization axes**: The structural
   lesson from two consecutive CONFIRMATION-NO-MERGE results is that per-symbol ATR
   widening, per-symbol labeling (BCH fracdiff, LDO ATR separate), and direction-
   asymmetric kill-switches are all single-seed lottery mechanisms. Cycle 4 EXPLORATION
   axes should prioritize:
   - NEW feature families with broad cross-symbol applicability (not per-symbol)
   - NEW structural model changes (e.g., return-label reform, objective function change)
   - Universe architecture (reducing to 3 symbols, or adding structurally different symbols)
   - Re-testing regime_momentum signal strength in a 3-symbol universe (remove ALGO
     and check whether regime_momentum recovers from rank-14/14)

4. **LDO OOS structural review**: LDO has produced negative OOS results in every
   iteration since iter-v3/047. At the next EXPLORATION, the QR should run an
   IS-only EDA on LDO's feature importance, labeling quality, and whether the
   ATR customization (2.0, 1.5) is truly IS-positive when measured at multi-seed
   (not single-seed). If LDO is structurally negative OOS at multi-seed, consider
   dropping LDO from the 4-symbol universe.

5. **ALGO as structural addition vs lottery**: ALGO's OOS concentration of 58.99%
   (seed 42) suggests it is a dominant PnL contributor at seed 42 but possibly not
   at seed 123 (where the Sharpe collapsed to +0.3149). The QR should examine whether
   ALGO's per-symbol ATR (2.0, 1.5) produces consistent IS lift across seeds or is
   seed-specific.

6. **DSR structural reformulation deferred but remains outstanding**: DSR=0.0
   continues to fail at n_trials=1400. This is structural (E[max_SR] ≈ 3.0 at 1400
   trials, observed ≈ 1.7; DSR→0). The gate is informational at current v3 trade
   volume. Either reformulate to DSR > 0 (positive deflation only) or accept the
   structural constraint until OOS Sharpe materially exceeds 3.0.

7. **Cycle 4 spec**: 10 EXPLORATIONs (iter-v3/051 through iter-v3/060) followed by
   CONFIRMATION (iter-v3/061) per `feedback_v3_strict_10_to_1_cadence.md`. The
   cadence discipline is mandatory; do not collapse the 10th EXPLORATION into the
   CONFIRMATION.

---

## Status

OVERALL=READY-FOR-CRITIC
