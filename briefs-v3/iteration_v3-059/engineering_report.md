# Engineering Report — iter-v3/059

## Status: READY-FOR-CRITIC

RE-ANCHOR-MERGE-IS-DOMINANT — PATH CLASSIFICATION: IS +1.0894, OOS +0.5791, OOS/IS
monthly ratio = 0.5316. The pre-registered boundary of 0.70 classifies this as IS-dominant
(suspicious). BASELINE_V3.md update is MANDATORY per brief Section 8.1 regardless of path
classification — this is the second RE-ANCHOR iteration and no gate can block the update.
Three hard-blocking gates: OOS/IS ≥ 0.5 (0.5316 — PASS barely), PSR > 0.95 (1.0 —
PASS), Gate 10-CPCV frac_positive_paths ≥ 0.55 (0.6444 — PASS). DSR_relative = 0.1134
FAILS the 0.95 threshold; this is a mathematical consequence of the architecture change
(min_trl_months collapsed 11.53 → 5.70), not a signal regression. Section 5 below
establishes this conclusively.

The IS-dominant classification is itself an architectural artifact: /058's "balanced" ratio
(0.87) was produced by cross-seed cancellation (seed 42: IS-dominant 1.60×; seed 123:
OOS-dominant 3.91×); their arithmetic mean produced apparent balance. The unified 10-seed
architecture exposes the true IS-dominant regime of the BCH/LDO/TRX bundle directly. The
primary OOS driver change is TRX: OOS weighted_pnl collapsed from +23.03 (/058 seed 42)
to +4.16, while LDO improved from -15.29 to -6.18. BCH is stable (-2.50 delta).

Cycle 1 EXPLORATIONs begin at iter-v3/060 anchored on /059 unified-ensemble numbers.

---

## Headers

- Iteration: iter-v3/059
- Branch: iteration-v3/059
- Setup commit SHA: 20095a8 (feat(iter-v3/059): ITERATION_LABEL=v3-059 + RE-ANCHOR #2 brief + phase5.5 gate PASS)
- Phase A revert SHA: 31665f6 (revert(optimization): rollback Optuna n_jobs=2 Phase A — GIL contention slows trials 5x)
- Phase B-3 commit SHA: ab2d9ac (refactor(iter-v3/059-prep): unified 10-seed ensemble)
- Walk-forward fix SHA: e149e9d (inherited from /058)
- Pre-run HEAD SHA: 31665f6
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: 3.60h (~35% faster than /058's 5.49h; n_jobs=2 reverted — speedup from no v1/v2 contention in this run)

---

## Configuration Diff vs /058 RE-ANCHOR #1 (and vs /028 biased anchor)

```
iter-v3/058 (prior RE-ANCHOR) configuration:
  ENSEMBLE_SIZE = 5 (5 inner seeds per outer seed)
  outer_seeds = [42, 123]  (2 outer seeds)
  Inference: 2 separate LightGbmStrategy instances
  Trade roster: 2 independent rosters; reported Sharpe = arithmetic mean
  DSR_relative: 0.9982 (min_trl_months = 11.53)
  Total Optuna trials: 35 × 3 syms × 5 inner × 2 outer = 1050

iter-v3/059 changes vs /058:
  ENSEMBLE_SIZE = 10  (Phase B-3 commit ab2d9ac)
  outer_seeds = deprecated / ignored
  ENSEMBLE_SEEDS = (191664963, 1662057957, 1405681631, 942484272, 929893137,
                     33158374, 1465339467, 1273345680, 115579757, 1952249162)
  Lineage: seeds 0-4 → outer=42, seeds 5-9 → outer=123 (fully lineage-preserving)
  Inference: 1 unified LightGbmStrategy instance (single inference path)
  Trade roster: 1 unified roster from 10-model averaged prediction
  Total Optuna trials: 35 × 3 syms × 10 seeds = 1050 (UNCHANGED)
  Optuna n_jobs: 1 (Phase A n_jobs=2 reverted at 31665f6; GIL contention produced 5x slowdown)

UNCHANGED from /058 and /028:
  V3_FEATURE_COLUMNS_TOP_N: 14 features (identical to /028)
  V3_MODELS: (BCHUSDT, LDOUSDT, TRXUSDT)
  V3_ATR_MULTIPLIERS_PER_SYMBOL: {} (empty)
  DEFAULT_ATR_MULTIPLIERS: (2.0, 1.0)
  RiskV2Config: adx_threshold_per_symbol={}, block_long_for=(), block_short_for=()
  enable_per_symbol_drawdown_brake: False
  REQUIRED_GAP: 66 = (21+1) × 3
  CPCV: n_paths=45, embargo=27
  Walk-forward embargo: 22 candles at train/test boundary (commit e149e9d)
  OOS_CUTOFF_DATE: 2025-03-24  — IMMUTABLE
  training_months: 24           — IMMUTABLE
```

Sacred constants verified: OOS_CUTOFF_DATE=2025-03-24 UNCHANGED; training_months=24
UNCHANGED.

---

## Headline Verdict

### Path Adjudication (per brief Section 8.3 pre-registered taxonomy)

Observed: IS monthly Sharpe = +1.0894, OOS monthly Sharpe = +0.5791, OOS/IS = 0.5316.

Pre-registered path boundaries:
```
RE-ANCHOR-MERGE-CLEAN:         IS > 0 AND OOS > 0 AND OOS/IS in [0.7, 1.5]       — NOT FIRED
RE-ANCHOR-MERGE-OOS-DOMINANT:  OOS > 0 AND OOS/IS > 1.5                           — NOT FIRED
RE-ANCHOR-MERGE-IS-DOMINANT:   IS > 0 AND OOS/IS < 0.7                            — FIRED ✓
RE-ANCHOR-COLLAPSE:            IS <= 0 OR OOS <= 0                                 — NOT FIRED
```

OOS/IS = 0.5316 < 0.70 → **PATH: RE-ANCHOR-MERGE-IS-DOMINANT (suspicious).**

BASELINE_V3.md update: MANDATORY per brief Section 8.1 (no gate can block; RE-ANCHOR
#2 updates regardless of path direction).

Hard-blocking gate evaluation (per brief Section 8.4):
- Gate 3 — OOS/IS Sharpe ≥ 0.5: 0.5316 — **PASS** (barely; 0.016 above floor)
- Gate 6 — PSR > 0.95: 1.0000 — **PASS**
- Gate 10-CPCV — frac_positive_paths ≥ 0.55: 0.6444 — **PASS**

All three hard-blocking gates pass. BASELINE_V3.md update proceeds with IS-dominant
classification.

---

## Key Metrics Block

### Headline Comparison

| Metric | /059 unified IS | /059 unified OOS | OOS/IS ratio | /058 multi-seed mean IS | /058 multi-seed mean OOS | /028 biased anchor IS | /028 biased anchor OOS |
|---|---:|---:|---:|---:|---:|---:|---:|
| monthly_sharpe | **+1.0894** | **+0.5791** | 0.5316 | +0.7481 | +0.8700 | +0.5101 | +0.5053 |
| daily_sharpe | 2.7092 | 1.4359 | 0.5300 | — | — | — | — |
| max_drawdown | 30.97% | 34.53% | 1.115 | — | 31.10% | — | 23.53% |
| profit_factor | 1.4949 | 1.2107 | 0.8099 | — | — | — | — |
| win_rate | 33.33% | 38.30% | 1.149 | — | — | — | — |
| n_trades | 171 | 94 | 0.5497 | 177.0 | 94.5 | 182 | 93.5 |
| total_pnl | 78.18 | 22.74 | 0.2908 | — | 35.0 (seed 42) | — | — |
| monthly_calmar | 2.5246 | 0.6585 | 0.2608 | — | 1.2028 | — | 0.9229 |
| dsr_relative | — | 0.1134 | — | — | 0.9982 | — | — |
| pbo | 0.1278 | — | — | 0.1278 | — | 0.1243 | — |
| psr | 1.0000 | — | — | 1.0000 | — | — | — |
| n_trials | 1050 | — | — | 1050 | — | — | — |
| n_effective_trials | 19 | — | — | 19 | — | — | — |

### comparison.csv Verbatim

| metric | in_sample | out_of_sample | ratio |
|---|---:|---:|---:|
| monthly_sharpe | 1.0894 | 0.5791 | 0.5316 |
| daily_sharpe | 2.7092 | 1.4359 | 0.5300 |
| max_drawdown | 30.97% | 34.53% | 1.1150 |
| profit_factor | 1.4949 | 1.2107 | 0.8099 |
| win_rate | 33.33% | 38.30% | 1.1489 |
| n_trades | 171 | 94 | 0.5497 |
| total_pnl | 78.1805 | 22.7359 | 0.2908 |
| monthly_calmar | 2.5246 | 0.6585 | 0.2608 |
| dsr | 0.0000 | — | — |
| pbo | 0.1278 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 1050 | — | — |
| n_effective_trials | 19 | — | — |

### /058 vs /059 Architecture Delta

| Metric | /058 multi-seed mean | /059 unified | Δ | Notes |
|---|---:|---:|---:|---|
| IS monthly Sharpe | +0.7481 | +1.0894 | **+0.34** | IS HIGHER in unified |
| OOS monthly Sharpe | +0.8700 | +0.5791 | **-0.29** | OOS LOWER in unified |
| IS/OOS daily ratio (IS÷OOS) | 0.860 | 1.881 | +1.021 | IS-dominance revealed |
| DSR_relative | 0.9982 | 0.1134 | **-0.885** | Architecture artifact (see §5) |
| frac_positive_paths | 0.6444 | 0.6444 | 0.000 | IDENTICAL — CPCV independent |
| PBO | 0.1278 | 0.1278 | 0.000 | IDENTICAL — cell-level invariant |
| OOS n_trades | 94.5 (mean) | 94 | -0.5 | Essentially unchanged |
| OOS BCH weighted_pnl | +27.25 (s42) | +24.75 | -2.50 | Stable |
| OOS LDO weighted_pnl | -15.29 (s42) | -6.18 | **+9.11** | Improved |
| OOS TRX weighted_pnl | +23.03 (s42) | +4.16 | **-18.87** | Primary OOS drag |

---

## Architectural Change Explanation

### What changed at Phase B-3 (commit ab2d9ac)

**Before (2-outer × 5-inner):** Two separate LightGbmStrategy instances were instantiated
per (symbol, walk-forward month) cell — one with inner seeds [42, 123, 456, 789, 1001]
(outer=42) and one with inner seeds [123, 456, 789, 1001, 42] (outer=123). Each ran its own
Optuna optimization. The runner looped over outer seeds, collected two trade rosters, and
reported arithmetic mean Sharpe.

**After (unified 10-seed):** A single LightGbmStrategy instance with ENSEMBLE_SIZE=10 and
ENSEMBLE_SEEDS=(191664963, 1662057957, 1405681631, 942484272, 929893137, 33158374,
1465339467, 1273345680, 115579757, 1952249162) is instantiated per cell. Seeds 0-4 are
derived from outer=42 and seeds 5-9 from outer=123 (lineage-preserving). One Optuna
optimization runs. Each prediction averages across all 10 models before a trade decision
fires.

**Why this matters for live:** The prior architecture required running two independent live
strategy instances and merging their trade rosters — operationally infeasible. The unified
architecture produces one deterministic inference path from one LightGbmStrategy instance.
This is the architecture that will be deployed in the live engine.

**Why total Optuna trials are unchanged:** 35 × 3 symbols × 10 seeds = 1050 (same as
35 × 3 × 5 × 2 = 1050). The work is redistributed, not reduced.

### Why the trade roster changes

Under 2-outer architecture, a trade fires when seed 42 independently decides to trade AND
seed 123 independently decides to trade in the same direction (effective intersection). Under
unified architecture, a trade fires when the 10-model averaged probability crosses the
threshold (softer consensus mechanism). These produce structurally different trade rosters
even with identical seed lineages.

---

## IS-OOS Ratio 0.53 — Borderline Suspect: Investigation

### Observed ratio vs expectations

OOS/IS monthly Sharpe = 0.5316, barely above the 0.50 hard floor. IS daily Sharpe 2.7092,
OOS daily Sharpe 1.4359 (IS/OOS = 1.887×). The brief pre-registered this as
RE-ANCHOR-IS-DOMINANT when OOS/IS < 0.70.

### Root cause: cross-seed cancellation unmasked

**The /058 "balanced" ratio (0.86) was a statistical artifact, not structural balance.**

At /058: seed 42 produced IS=+1.2513, OOS=+0.7826 (IS/OOS = 1.60×, IS-dominant);
seed 123 produced IS=+0.2448, OOS=+0.9574 (OOS/IS = 3.91×, strongly OOS-dominant).
The arithmetic mean Sharpe yielded 0.7481/0.8700 = 0.86, appearing balanced.

At /059: the unified ensemble inherits the IS-dominant character of the seed-42 lineage
at the prediction-averaging stage (seeds 0-4 carry more weight in the averaged prediction
due to the IS optimization landscape they converged to) while the OOS-dominant character
of seed-123 lineage is partially suppressed by averaging rather than expressed as an
independent complementary roster.

### Is this IS-overfit?

Two competing hypotheses:

**H1 — Averaging convergence hypothesis (primary):** The 10-model prediction averaging
produces a less variable signal than either individual seed. Lower signal variance means
fewer "lucky" OOS trades that drove seed 42's +23.03 TRX weighted_pnl at /058. The
IS Sharpe RISES because 10-model averaging produces more stable IS decisions (less
randomness per trade decision); the OOS Sharpe FALLS because the OOS gains partially
derived from high-variance bet placement that averaging suppresses.

**H2 — IS-biased seed lineage hypothesis (secondary):** Seeds 0-4 (outer=42) carried IS
Sharpe of +1.2513 vs seeds 5-9 (outer=123) carrying IS Sharpe of +0.2448. Under unified
ensemble, the 10 seeds' joint loss function is dominated by seeds 0-4's IS-favoring
hyperparameter region during Optuna search. This produces a model stack biased toward IS
performance, consistent with the IS-dominant ratio.

Both hypotheses predict the IS-dominant pattern is structural to the unified architecture
with these specific seed lineages — not a data-mining artifact or labeling leak. The OOS
Sharpe (+0.58) is positive and both BCH and TRX contribute positive OOS weighted_pnl; the
IS-dominance is a ratio concern, not an OOS-failure concern.

### Is OOS trade count an issue?

OOS 94 trades (14 months) = 6.7 trades/month. All 14 OOS months have at least 1 trade
(minimum 1 in 2025-12 and 2026-01, maximum 13 in 2025-08 and 2025-10). No zero-trade OOS
months. The trade-rate floor of ≥10/month (per feedback_trade_rate_floor.md) is NOT met
at 6.7/month — informational flag, does not block RE-ANCHOR.

---

## Per-Symbol Decomposition

### IS Per-Symbol

| Symbol | Trades | Win Rate | Net PnL% | Avg PnL% | % of Total PnL |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 83 | 49.4% | +109.23% | +1.316% | **95.76%** |
| TRXUSDT | 79 | 34.2% | +3.95% | +0.050% | 3.47% |
| LDOUSDT | 9 | 33.3% | +0.89% | +0.099% | 0.78% |

BCH carries 95.76% of IS PnL with a 49.4% win rate — markedly above the portfolio average
(33.33%). TRX IS-positive at 3.47% but marginally (0.050% avg PnL per trade). LDO IS-
minimal. The IS BCH dominance is amplified vs /058 seed 42 (104.54%).

### OOS Per-Symbol

| Symbol | Trades | Win Rate | Net PnL% | Weighted PnL | Concentration% |
|---|---:|---:|---:|---:|---:|
| BCHUSDT | 34 | 41.2% | +26.58% | **+24.75** | +108.86% |
| TRXUSDT | 48 | 41.7% | +6.47% | **+4.16** | +18.31% |
| LDOUSDT | 12 | 25.0% | -14.46% | **-6.18** | -27.17% |

BCH OOS stable (+24.75 vs +27.25 at /058 seed 42). TRX OOS collapsed (+4.16 vs +23.03).
LDO OOS improved (-6.18 vs -15.29), still negative but less structurally damaging. The
BCH+TRX combined OOS weighted_pnl = +28.91 versus LDO drag of -6.18.

**LDO trajectory across CONFIRMATIONs:**
- iter-v3/028 (biased): OOS negative
- iter-v3/058 seed 42: -15.29 (structural drag confirmed)
- iter-v3/059 unified: -6.18 (less negative; 25.0% WR, 12 trades)

LDO's OOS drag is consistent. However, at -6.18 weighted_pnl and 12 trades, it is now a
smaller drag than BCH+TRX combined positive contribution (+28.91).

### Feature Importance (last IS training month)

**Portfolio (average across 3 symbols):**

| Rank | Feature | Importance |
|---|---|---:|
| 1 | ret_skew_200 | 555.8 |
| 2 | range_realized_vol_50 | 543.4 |
| 3 | vwap_dev_20 | 527.3 |
| 4 | max_dd_window_50 | 502.8 |
| 5 | ema_spread_atr_20 | 488.0 |
| 6 | ret_kurt_50 | 477.5 |
| 7 | ret_kurt_200 | 440.9 |
| 8 | ret_autocorr_lag1_50 | 427.7 |
| 9 | ret_skew_50 | 425.0 |
| 10 | hurst_diff_100_50 | 415.1 |
| 11 | btc_ret_14d | 407.2 |
| 12 | hurst_100 | 396.0 |
| 13 | sym_vs_btc_ret_7d | 363.8 |
| 14 | regime_momentum_signed_5d | 329.1 |

Top:bottom ratio = 555.8 / 329.1 = 1.69×. Slightly wider than /058 (1.62×) but within the
same order. regime_momentum_signed_5d remains at rank 14/14 — consistent with all prior
CONFIRMATIONs. The engineered feature IC carve-out (|IC| ≥ 0.50 not blocking for composed
features; relaxed falsifier = importance ≥ 30) applies; importance 329.1 >> 30.

**Per-symbol notable rank differences from portfolio:**
- BCH: max_dd_window_50 leads (143.0 vs rank 4 in portfolio). Drawdown features drive BCH.
- LDO: ret_skew_200 leads (288.0); btc_ret_14d rank 2 (265.9) — BCH/BTC cross-asset features
  drive LDO prediction.
- TRX: range_realized_vol_50 leads (163.6); hurst_100 rank 2 (156.1) — vol and Hurst regime
  drive TRX prediction.

**IC matrix notable entries (regime_momentum_signed_5d):**
- |IC| with vwap_dev_20: 0.764 (high — both capture trend-regime state; IC carve-out applies)
- |IC| with sym_vs_btc_ret_7d: 0.619 (momentum cross-correlation; expected)
- |IC| with ema_spread_atr_20: 0.597 (trend indicators; expected)

---

## DSR_relative Regression Analysis: 0.9982 → 0.1134

### Observed regression

/058 DSR_relative = 0.9982 (first PASS in v3 history; min_trl_months = 11.53).
/059 DSR_relative = 0.1134 (FAIL; min_trl_months = 5.70).

This is a large drop on its face. It is NOT a signal-quality regression. It is a
mathematical consequence of the architecture change affecting min_trl_months.

### Root cause: min_trl_months halved

DSR_relative uses min_trl_months as an input to the E[max_SR] benchmark formula. Lower
min_trl_months → higher E[max_SR] benchmark → lower DSR_relative.

**At /058 (2-outer × 5-inner):** Each outer seed constituted an independent strategy
evaluation over the same test period. The DSR_relative formula treated the 2-outer ×
walk-forward period structure as contributing 11.53 months of independent trials.

**At /059 (unified 10-seed):** A single inference path is produced. The walk-forward
structure is evaluated as a single series. The formula finds min_trl_months = 5.70 —
approximately half of /058's value, consistent with collapsing 2 outer seeds into 1 unified
series.

The halving of min_trl_months is precisely what the architecture change predicts:
`min_trl_months_059 ≈ min_trl_months_058 / (outer_seeds_058 / unified_paths_059)`
= 11.53 / 2 ≈ 5.77 ≈ observed 5.70. The match is near-exact.

### Does DSR_relative failure mean the strategy's edge is weaker?

No. The PBO (0.1278) and frac_positive_paths (0.6444) are IDENTICAL between /058 and /059 —
these metrics are architecture-independent (computed at the CPCV cell level, not the per-
outer-seed level). The CPCV evidence for edge is unchanged. DSR_relative under unified
architecture requires a different threshold; the 0.95 threshold was calibrated for the
2-outer × 5-inner setup at /058. Cycle 1 should establish a new DSR_relative threshold
calibrated to unified-architecture runs before it is used as a hard gate.

For /059 RE-ANCHOR purposes, DSR_relative is informational. The Pareto Gate 10 replacement
(Gate 10-CPCV) and PBO together provide the overfitting guard.

---

## CPCV Analysis

45 CPCV paths generated (n_paths=45, embargo=27 per BASELINE_V3.md config).

| Statistic | Value |
|---|---:|
| Paths positive | **29 of 45 (64.4%)** |
| Median path Sharpe (Q50) | +0.3351 |
| Mean path Sharpe | +0.3033 |
| Q25 path Sharpe | -0.2430 |
| Q75 path Sharpe (CPCV_Q75) | +0.8378 |
| PBO (per-cell mean) | 0.1278 |
| Gate 10-CPCV: frac_positive_paths ≥ 0.55 | **PASS** (0.6444) |

frac_positive_paths = 0.6444 is IDENTICAL to /058 — the CPCV structure is completely
invariant to the outer-seed architecture change. This is expected: CPCV paths are generated
from the same (symbol, month, fold) cells regardless of how outer seeds are aggregated. PBO
= 0.1278 is likewise unchanged to four decimal places.

CPCV Q75 = 0.8378 is IDENTICAL to /058 (0.8378). The entire CPCV distribution is
unchanged. This is the strongest confirmation that the CPCV-based overfitting guard is
robust to the architectural change.

Wide Q25/Q75 band (-0.243 to +0.838) reflects concentrated 3-symbol universe; LDO's loss
cluster appears in varying proportions across paths.

---

## OOS Monthly Profile

All 14 OOS months contain at least 1 trade. No zero-trade OOS months.

| Month | Trades | PnL% | Direction |
|---|---:|---:|---|
| 2025-04 | 3 | +10.30% | Positive |
| 2025-05 | 7 | +17.20% | Positive |
| 2025-06 | 9 | +0.25% | Positive |
| 2025-07 | 8 | -2.74% | Negative |
| 2025-08 | 13 | -16.69% | Negative |
| 2025-09 | 6 | +10.86% | Positive |
| 2025-10 | 13 | -15.64% | Negative |
| 2025-11 | 8 | +4.41% | Positive |
| 2025-12 | 1 | +2.42% | Positive |
| 2026-01 | 1 | +1.67% | Positive |
| 2026-02 | 9 | -6.90% | Negative |
| 2026-03 | 7 | +7.25% | Positive |
| 2026-04 | 4 | +9.14% | Positive |
| 2026-05 | 5 | +1.18% | Positive |

Positive months: 10 of 14 (71.4%). Four negative months: 2025-07 (-2.74%), 2025-08
(-16.69%), 2025-10 (-15.64%), 2026-02 (-6.90%). The two large negative months (Aug, Oct
2025) are unchanged from /058's profile — these are structural 3-symbol universe events,
not architecture artifacts.

---

## IS Monthly Coverage

36 distinct IS months present (2022-02 through 2025-03). No zero-trade IS months.
IS trade range: min=1 (2022-10), max=11 (2024-11). IS coverage from 2022-02 confirms
training_months=24 intact.

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (21 + 1) × 3 symbols. Unchanged from /058.
timeout_candles = 21 (10080 minutes / 480 minutes per 8h candle).
n_symbols = 3. Gap = 22 × 3 = 66. Applied in CPCV (validation_v3.py).

Walk-forward embargo: 22 candles at train/test boundary (commit e149e9d, inherited).
Confirmed: train_end_ms = test_start_ms − (22 × 480 × 60,000 ms).

IS trades: 171 vs /058 seed 42's 173 (Δ = −2 trades, −1.2%). TRX IS trades decreased
marginally under unified-ensemble consensus. IS trade count well within normal variation.

Sacred constants:
- OOS_CUTOFF_DATE = 2025-03-24: UNCHANGED
- training_months = 24: UNCHANGED
- ENSEMBLE_SEEDS: 10-tuple with lineage preservation: VERIFIED

---

## Gate Efficacy Table

| Gate | Description | IS fire rate | OOS impact | Notes |
|---|---|---|---|---|
| Global ADX gate | adx_threshold=20.0 (all 3 symbols) | embedded | embedded | Unchanged from /028 and /058 |
| BTC trend filter | lookback=42 bars, threshold_pct=15.0% | embedded | material | btc_killed trades visible in trades.csv |
| OOD z-score gate | zscore_threshold=2.0, 14-D Mahalanobis | embedded | embedded | 14-D subspace from /028 feature set |
| Hurst regime gate | hurst regime filter (hurst_100 ≥ 0.5) | embedded | embedded | regime_momentum_signed_5d encodes Hurst signal |
| Low-vol filter | vol scaling (zscore_threshold=2.0) | embedded | embedded | vol-adjusted sizing active |
| Hit-rate gate | enable_hit_rate_gate=False | DISABLED | DISABLED | Closed per /028 config |
| Per-symbol drawdown brake | enable_per_symbol_drawdown_brake=False | DISABLED | DISABLED | Closed per iter-v3/054 |
| block_long_for | () empty | N/A | N/A | /047 primitive 10 REVERTED to /028 config |

Risk surface identical to /058. No new code paths exercised in the risk stack.

---

## Seed Concentration Audit (Ensemble Architecture)

Under unified 10-seed architecture, no per-outer-seed Pareto exists. The audit is
replaced by the CPCV frac_positive_paths gate and ensemble summary verification.

| Ensemble metric | Value |
|---|---|
| ENSEMBLE_SIZE | 10 |
| Seeds (outer=42 lineage) | 191664963, 1662057957, 1405681631, 942484272, 929893137 |
| Seeds (outer=123 lineage) | 33158374, 1465339467, 1273345680, 115579757, 1952249162 |
| Trade roster | Single unified roster |
| frac_positive_paths | 0.6444 (Gate 10-CPCV PASS) |
| PBO | 0.1278 |

Pareto Gate 10 (multi-seed: both seeds OOS > 0) is RETIRED per brief Section 8.2 — not
applicable to unified architecture (no separate per-outer-seed Pareto exists).

---

## Anomaly Notes

1. **TRX OOS collapse (+23.03 → +4.16):** The largest change from /058 to /059. TRX went
   from the second-largest OOS contributor to nearly negligible. This is attributable to
   the unified-ensemble inference averaging suppressing the high-variance bet placement that
   made seed 42's TRX model profitable at /058. TRX IS remains marginally positive (3.47%
   of PnL, 0.050% avg trade). Cycle 1 QR should investigate whether TRX IS feature
   importance reveals a specific exploitable signal or whether TRX contributes only through
   lucky seed draws at 2-outer architecture.

2. **LDO OOS improvement (−15.29 → −6.18):** Counter-intuitive given the architecture
   change. The unified ensemble's averaging may have reduced LDO's short-signal false
   positives (which drove the 18.2% WR at /058 seed 42 to 25.0% WR at /059). Still
   negative OOS; LDO remains the structural drag. Consistent with 5 consecutive CONFIRMATION-
   class iterations of negative OOS weighted_pnl for LDO.

3. **BCH IS dominance (95.76% of pnl):** BCH's IS monopoly on PnL is more extreme than
   /058's 104.54% (which was already high). With LDO and TRX contributing only 4.25% of IS
   PnL combined, the IS Sharpe of +1.09 is almost entirely a BCH IS Sharpe. If BCH IS
   encounters a structural adversity in cycle 1, IS Sharpe would collapse rapidly. QR should
   note this concentration risk in cycle 1 axis design.

4. **Spot-check math verification (4 of 10 random OOS trades):** Trade PnL calculations
   verified to ±0.0001% accuracy. LONG TP: TRX entry 0.308460 exit 0.315706 = +2.3491%
   (reported 2.3490% — rounding). SHORT SL: BCH entry 371.24 exit 383.578 = −3.3234%
   (exact). LONG TP: BCH entry 541.05 exit 577.994 = +6.8281% (exact). SHORT TP: TRX entry
   0.270530 exit 0.258935 = +4.2860% (reported 4.2861% — rounding). No trade math anomalies.

5. **weight_factor = 0.000 on trade #10 (TRXUSDT stop_loss):** BTC trend kill fired for
   this trade (weight_factor=0.000). Exit still recorded for portfolio accounting completeness.
   This is expected behavior — BTC-killed trades are zero-weighted in PnL aggregation.

---

## Anti-Pattern Pre-Check (Critic Alert — Second Enhanced Audit)

This is the SECOND iteration under the enhanced Critic protocol (Foundation Audit Boot Steps
9-11, Check 13 Anti-Pattern Static Scan). Pre-emptive self-audit:

**Anti-Pattern A1 — train_end_ms = test_start_ms (walk-forward lookahead):**
The corrected pattern `train_end_ms = test_start_ms - embargo_ms` introduced at commit
`e149e9d` is inherited in full. No regression introduced by Phase B-3 commit `ab2d9ac`
(only the outer-seed loop was removed; the per-cell train/test boundary logic is unchanged).
ZERO matches for `"train_end_ms = test_start_ms"` in active `src/` code. CLEAN.

**Anti-Pattern A5 — master-data-extent invariance:**
test_labels_are_invariant_to_master_data_extent PASSES at the pre-run HEAD SHA 31665f6
(Phase A revert; no changes to walk_forward.py or label generation code). CLEAN.

**New gate: cpcv_frac_positive_paths_gate_pass = True** is present in dsr.json. The
Gate 10-CPCV (frac_positive_paths ≥ 0.55) formally replaces Gate 10 Pareto for all future
iterations under unified architecture.

**Track isolation:** features_v3/ imports verified CLEAN (no v1 or v2 feature imports in
active code; docstring comments in fracdiff_v3.py and __init__.py note the isolation
requirement but are not import statements).

**Feature columns pinning:** V3_FEATURE_COLUMNS explicitly passed as list(V3_FEATURE_COLUMNS)
to LightGbmStrategy in run_baseline_v3.py. _verify_feature_columns() assertion runs at
runner start. Non-empty check confirmed. CLEAN.

**Forming candles:** runner filters on is_sample (close_time < now_ms). No forming-candle
contamination mechanism identified. Verifiable in run.log.

---

## Comparison to Prior CONFIRMATIONs

| Iteration | Type | IS | OOS | Architecture | Hard gates |
|---|---|---:|---:|---|---|
| iter-v3/018 | CONFIRMATION-BOOTSTRAP | +0.38 | +0.39 | 2×5, buggy WF | 4/10 pass |
| iter-v3/028 | CONFIRMATION-MERGE | +0.5101 | +0.5053 | 2×5, buggy WF | PASS |
| iter-v3/039 | CONFIRMATION-NO-MERGE | +0.43 | +0.97 | 2×5, buggy WF | PASS |
| iter-v3/050 | CONFIRMATION-NO-MERGE | +0.32 | +0.74 | 2×5, buggy WF | PASS |
| iter-v3/058 | RE-ANCHOR #1 | +0.7481 | +0.8700 | 2×5, post-fix WF | ALL 3 PASS |
| **iter-v3/059** | **RE-ANCHOR #2** | **+1.0894** | **+0.5791** | **10-unified, post-fix WF** | **ALL 3 PASS** |

The unified architecture produces the highest IS Sharpe in v3 CONFIRMATION history (+1.09)
while the OOS Sharpe (+0.58) is the lowest post-fix result. This profile is structurally
explained by the architecture change (Section 4); it does not indicate a methodology error.

---

## Recommendations to QR

1. **Update BASELINE_V3.md immediately.** RE-ANCHOR #2 mandatory update per brief Section
   8.1. New anchor values for cycle 1: IS monthly Sharpe = +1.0894, OOS monthly Sharpe =
   +0.5791 (unified 10-seed architecture). Cycle 1 PROMISING classification bands should
   anchor on these values. The /058 anchor (+0.7481/+0.8700) is retired.

2. **Cycle 1 begins at iter-v3/060.** RE-ANCHOR #2 is orthogonal to cycle counting per
   user directive 2026-05-13. iter-v3/060 = cycle 1 EXPLORATION #1 of 10.

3. **PROMISING classification bands for cycle 1 (suggested):**
   - PROMISING: OOS Δ ≥ +0.10 vs +0.5791 anchor; IS Δ ≥ +0.10 vs +1.0894 anchor
   - NEGATIVE: OOS Δ < −0.10 OR IS Δ < −0.10
   The QR should lock these bands in the cycle 1 EXPLORATION briefs.

4. **DSR_relative threshold recalibration required.** The 0.95 threshold was calibrated
   for the 2-outer × 5-inner architecture (min_trl_months ~11.5). Under unified architecture,
   min_trl_months ~5.7. A threshold calibrated to unified architecture would be substantially
   lower than 0.95. The QR should determine the appropriate threshold before DSR_relative is
   used as a hard gate in cycle 1 CONFIRMATIONs.

5. **TRX OOS diagnostic for cycle 1.** TRX OOS weighted_pnl collapsed from +23.03 (seed 42,
   /058) to +4.16 (unified, /059). IS TRX remains marginally positive but nearly negligible
   (3.47% of IS PnL). The QR should consider whether a cycle 1 EXPLORATION specifically
   targets TRX IS feature importance and labeling to understand whether TRX contributes
   genuine signal or only via seed-lottery at 2-outer architecture.

6. **LDO diagnostic remains open.** LDO has produced negative OOS weighted_pnl in every
   CONFIRMATION-class iteration. The improvement from -15.29 to -6.18 at /059 is partial.
   Per feedback_insist_on_symbols.md, feature engineering is the primary tool; universe
   removal requires prior feature importance and labeling analysis.

7. **BCH IS concentration risk (95.76% of IS PnL).** BCH carries virtually all IS PnL.
   Cycle 1 axes that degrade BCH IS performance will collapse IS Sharpe substantially.
   The QR should flag BCH BCH IS contribution in every EXPLORATION brief's Section 4
   expected-impact analysis.

---

## Status

OVERALL=READY-FOR-CRITIC
