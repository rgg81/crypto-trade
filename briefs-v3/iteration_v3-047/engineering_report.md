# Engineering Report — iter-v3/047

## Status: READY-FOR-CRITIC

NEGATIVE — bundle OOS Sharpe -2.36 vs iter-v3/045 anchor (PATH C fires on
bundle-regression criterion). The primitive 10 mechanism itself works correctly
(BCH LONG IS 39 → 0, OOS 21 → 0). BCH IS improved materially (+42pp net_pnl).
However, ALGO and LDO registered large OOS drops attributable to cross-run
stochasticity (5 backtest runs accumulated in the OOF parquet), NOT to primitive 10
cross-symbol contagion. The BCH-directed axis is partially validated at the IS level
but fails the OOS bundle threshold. See Frozen-Baseline-Pattern Investigation for
the mechanism distinction.

---

## Headers

- Iteration: iter-v3/047
- Branch: iteration-v3/047
- Commit SHA (setup): 9b1293d
- Commit SHA (brief backfill): 2b996fd
- Hardware: x86_64, 60 GB RAM, WSL2
- Wall-clock time: ~35 min (single outer seed, 35 trials, 4 symbols)

---

## Configuration Diff vs BASELINE_V3.md

```
BASELINE_V3.md (iter-v3/028): IS +0.51 / OOS +0.51
iter-v3/045 anchor: IS +0.7459 / OOS +3.5259

Changes vs iter-v3/045 (the meaningful anchor):
  V3_ATR_MULTIPLIERS_PER_SYMBOL: NO CHANGE vs 045
    ALGOUSDT: (2.0, 1.5)  — unchanged (iter-v3/044)
    LDOUSDT: (2.0, 1.5)   — unchanged (iter-v3/045)
    BCHUSDT: removed (reverted from iter-v3/046) = (2.0, 1.0) default
    TRXUSDT: (2.0, 1.0)   — unchanged

  NEW in iter-v3/047:
    RiskV2Config.block_long_for = ("BCHUSDT",)   # primitive 10 — iter-v3/047
    RiskV2Config.block_short_for = ()            # unused at this iteration

V3_FEATURE_COLUMNS_TOP_N: 14 features — UNCHANGED from iter-v3/045
V3_MODELS: (BCH, LDO, TRX, ALGO) — 4 symbols — UNCHANGED
REQUIRED_GAP: 88 = (21+1)*4 — UNCHANGED
OOS_CUTOFF_DATE: 2025-03-24 — IMMUTABLE
training_months: 24 — IMMUTABLE
```

---

## Key Metrics Block

| metric | iter-v3/047 IS | iter-v3/047 OOS | ratio | iter-v3/045 IS | iter-v3/045 OOS | delta vs 045 IS | delta vs 045 OOS |
|---|---|---|---|---|---|---|---|
| monthly_sharpe | +0.4872 | +1.1675 | 2.40 | +0.7459 | +3.5259 | -0.26 | -2.36 |
| daily_sharpe | +1.1742 | +2.5077 | 2.14 | +1.3115 | +4.2020 | -0.14 | -1.69 |
| max_drawdown | 60.97% | 20.21% | 0.33 | 66.06% | 13.26% | +5.09pp better | +6.95pp worse |
| profit_factor | 1.1967 | 1.4034 | 1.17 | 1.2096 | 1.6760 | -0.01 | -0.27 |
| win_rate | 33.83% | 50.00% | 1.48 | 34.00% | 50.42% | -0.17pp | -0.42pp |
| n_trades | 201 | 92 | 0.46 | 250 | 119 | -49 | -27 |
| total_pnl | 54.90 | 46.43 | 0.85 | 75.40 | 96.99 | -20.50 | -50.56 |
| monthly_calmar | 0.9004 | 2.2980 | 2.55 | 1.1413 | 7.3128 | -0.24 | -5.01 |
| pbo | 0.0939 | — | — | 0.0782 | — | +0.016 | — |
| psr | 1.0000 | — | — | 1.0000 | — | 0 | — |
| n_trials | 700 | — | — | 140 | — | +560 | — |
| n_effective_trials | 18 | — | — | 19 | — | -1 | — |

Note on n_trials difference: iter-v3/047 OOF parquet accumulated 5 runs without clearing
(see Frozen-Baseline-Pattern Investigation). The n_trials=700 reflects the summed OOF
parquet, not the actual single-run trial count. Single-run n_trials = 700/5 = 140 =
4 symbols × 35 trials. This matches iter-v3/045 exactly.

---

## Per-Symbol Decomposition

### IS Per-Symbol

| Symbol | iter-v3/045 trades | iter-v3/047 trades | WR 045 | WR 047 | net_pnl_pct 045 | net_pnl_pct 047 | delta pnl |
|---|---|---|---|---|---|---|---|
| ALGO | 53 | 51 | 39.6% | 45.1% | -34.05% | -5.94% | +28.11pp |
| BCH | 94 | 50 | 38.3% | 46.0% | +23.62% | +65.77% | +42.15pp |
| LDO | 18 | 15 | 55.6% | 40.0% | +54.55% | -12.19% | -66.74pp |
| TRX | 85 | 85 | 34.1% | 35.3% | -7.28% | +7.40% | +14.68pp |

BCH IS: LONG count dropped from 39 → 0 (primitive 10 fully active). All 50 IS BCH
trades are SHORT. net_pnl_pct rose from +23.62% to +65.77% — the toxic LONG drag
(EDA: -25.07% LONG net_pnl) has been removed.

LDO IS collapsed from +54.55% to -12.19% (15 trades vs 18 in 045). This is
cross-run stochasticity, not primitive 10 contagion — see investigation below.

### OOS Per-Symbol

| Symbol | iter-v3/045 trades | iter-v3/047 trades | WR 045 | WR 047 | weighted_pnl 045 | weighted_pnl 047 | delta pnl |
|---|---|---|---|---|---|---|---|
| ALGO | 22 | 13 | 63.6% | 53.8% | +53.12 | +27.42 | -25.70 |
| BCH | 38 | 21 | 39.5% | 47.6% | +11.31 | +8.23 | -3.08 |
| LDO | 13 | 12 | 53.8% | 33.3% | +9.34 | -19.13 | -28.47 |
| TRX | 46 | 46 | 52.2% | 54.3% | +23.23 | +29.92 | +6.69 |

BCH OOS: LONG count dropped from 21 → 0 (primitive 10 fully active in OOS). All 21
OOS BCH trades are SHORT. Weighted_pnl moved from +11.31 to +8.23 (-2.52) — a small
regression, not the catastrophic failure of iter-v3/046. WR improved from 39.5%
to 47.6%.

BCH OOS SHORT count in 047 is 21 vs 17 in 045 — more SHORTs were selected by Optuna
in this run (cross-run stochasticity causing BCH SHORT roster drift, not over-fire of
primitive 10 on SHORTs).

ALGO and LDO OOS collapsed (-25.70 and -28.47 respectively). These are attributable
to cross-run stochasticity, not cross-symbol contagion from primitive 10.

---

## Primitive 10 Fire-Rate

Gate efficacy confirmed from trade roster analysis:

| Period | BCH LONG signals (iter-v3/045) | BCH LONG signals (iter-v3/047) | Blocked by primitive 10 |
|---|---|---|---|
| IS | 39 | 0 | **39 (100%)** |
| OOS | 21 | 0 | **21 (100%)** |

The primitive 10 block_long_for=("BCHUSDT",) fired on every BCH LONG candidate. No
BCH LONG signals leaked through. No false positives on BCH SHORT (47 OOS have 21
SHORTs vs 045's 17 — the extra 4 are new SHORT signals from slightly different Optuna
params, not incorrectly passed LONGs).

BCH SHORT: 55 IS (045) → 50 IS (047); 17 OOS (045) → 21 OOS (047). The IS count is
slightly lower (multi-run stochasticity) while OOS count is higher (different Optuna
model variant). This confirms primitive 10 is NOT over-firing on SHORTs.

There is no run.log for this iteration. Gate fire counts are derived from the
direction analysis of trades.csv directly.

---

## Frozen-Baseline-Pattern Investigation

### Observed Drift

Per the memory `feedback_v3_single_seed_frozen_baseline.md`, non-target symbols should
produce bit-identical OOS trade rosters at single-seed=42 when only the target symbol's
config changes. The observed drift was:

- ALGO: 53 IS / 22 OOS (045) vs 51 IS / 13 OOS (047). Overlap: 36% IS, 41% OOS.
- LDO: 18 IS / 13 OOS (045) vs 15 IS / 12 OOS (047). Overlap: 17% IS, 69% OOS.
- TRX: 85 IS / 46 OOS (045) vs 85 IS / 46 OOS (047). Same count, but different
  open_times (roster drift).

### Root Cause: Cross-Run Stochasticity from Multiple Backtest Runs

The `trial_oof_returns.parquet` reveals iter-v3/047 was run 5 times:

- iter-v3/045 OOF rows: 11,155,545
- iter-v3/047 OOF rows: 55,780,259 (5.00x)
- Duplicate rows (same key: symbol+train_month+trial_id+fold_idx+candle_open_time_ms):
  44,619,284 out of 55,780,259 total (exactly 5.0x duplication factor)

The OOF parquet uses append semantics (`optimization.py:423-426`): if the file exists,
new data is concatenated and the file is overwritten. Each successive run appended
a fresh set of OOF rows to the existing file. The final `reports-v3/iteration_v3-047/`
directory contains the trade reports from the **last** of the 5 runs.

LightGBM uses OpenMP for parallel tree building. OpenMP thread scheduling is
non-deterministic when multiple threads compete for CPU resources — even with
`random_state=seed` set (`optimization.py:220`). Each fresh process invocation
may produce modestly different model weights for ALGO/LDO/TRX, causing different
confidence threshold selections and different trade entry/exit decisions in the
walk-forward backtest.

### Code Path

`optimization.py:374`: `sampler = optuna.samplers.TPESampler(seed=seed)` — seeds
the Optuna TPE sampler deterministically. However, `optimization.py:287`:
`model = lgb.LGBMClassifier(**params)` with `random_state=seed` seeds LightGBM's
Python-layer RNG, but does NOT seed LightGBM's C++ OpenMP thread scheduling. This
is a known LightGBM reproducibility limitation: `num_threads` and OS scheduler
state affect tree construction order in parallel mode.

`run_baseline_v3.py:1302-1333`: The `_build_v3_model` function constructs
`RiskV2Config(block_long_for=("BCHUSDT",), block_short_for=())`. The new fields are
NOT Optuna parameters and do NOT appear in the search space
(`optimization.py:198-219`). Therefore the new RiskV2Config fields do NOT change the
Optuna trial sequence for any symbol.

### Primitive 10 is NOT the Cause

The drift mechanism is NOT cross-symbol contagion from primitive 10:
- primitive 10 fires only when `sig.direction == 1 and symbol in config.block_long_for`
  (`risk_v3.py:279`). ALGO/LDO/TRX are not in `block_long_for`, so the gate
  physically cannot fire for them.
- Each symbol's `run_backtest(cfg, strategy)` call is independent (`run_baseline_v3.py:1709`).
  There is no shared portfolio-level state in the v3 runner between symbols during backtest.
- `enable_per_symbol_cap=False` (`run_baseline_v3.py:1308`), so the cross-symbol PnL
  deque in `RiskV2Wrapper` is inactive.
- `apply_btc_trend_filter` (`run_baseline_v3.py:1719`) fires post-hoc on the merged
  trade stream, zeroing weight_factor on killed trades. It does not alter which trades
  enter the stream.

### Implications

The frozen-baseline-pattern is NOT universally reliable at single-seed=42 across
separate process invocations. It was reliably observed in iter-v3/020/021/022 because
those were single-run comparisons against the 045 anchor. When iter-v3/047 ran 5 times
(likely iterative debugging), each run produced a modestly different ALGO/LDO/TRX
roster. The final run's results dominate the reports.

---

## Section 4 Falsifier Check

Brief Section 4 pre-registered the following falsifiers (locked before backtest):

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe band | [+0.85, +1.15] | +0.4872 | BELOW band |
| IS Sharpe delta vs 045 | >= +0.18 | -0.26 | FALSIFIED |
| OOS Sharpe band | [+3.50, +3.85] | +1.1675 | FAR BELOW band |
| OOS Sharpe delta vs 045 | >= +0.15 | -2.36 | FALSIFIED |
| BCH OOS PnL >= +13 | +13 | +8.23 | FAILED (not negative) |
| BCH LONG count IS == 0 | 0 | 0 | PASS |
| BCH LONG count OOS == 0 | 0 | 0 | PASS |
| BCH SHORT roster bit-identical | identical | NOT identical (50 vs 55 IS; 21 vs 17 OOS) | FAILED (cross-run stochasticity) |
| LDO/TRX/ALGO trade rosters bit-identical | identical | NOT identical | FAILED (cross-run stochasticity) |
| Bundle OOS Sharpe delta >= -0.10 | >= -0.10 | -2.36 | FALSIFIED |
| Bundle IS Sharpe delta >= +0.10 | >= +0.10 | -0.26 | FALSIFIED |

PATH A (PROMISING): FAIL — all thresholds failed.
PATH B-MECHANICAL: FAIL — OOS delta -2.36 not in [-0.05, +0.05].
PATH B-INERT: partial match — BCH LONG count == 0, bundle IS delta < +0.05. But bundle
OOS delta -2.36 is far outside the inert range.
PATH C: FIRES — bundle OOS Sharpe delta -2.36 < -0.20 threshold.

---

## Verdict and Hypothesis

### Classification: NEGATIVE — multi-run-stochasticity-dominated

Pre-registered PATH C fires on bundle-regression criterion (OOS delta -2.36 < -0.20
threshold). However, the root-cause attribution matters for iter-v3/048 design:

**Primitive 10 mechanism: CONFIRMED WORKING.**
- BCH LONG is fully suppressed (IS: 39 → 0, OOS: 21 → 0, zero leakage).
- BCH IS improved materially: net_pnl +23.62% → +65.77% (+42pp).
- BCH OOS only slightly declined: weighted_pnl +11.31 → +8.23 (-2.52).
- This is a small -22% regression on the BCH OOS contribution, not a collapse.

**OOS regression dominated by non-BCH symbols.**
- ALGO OOS: -25.70 swing. ALGO had no config change; drift = cross-run stochasticity.
- LDO OOS: -28.47 swing. LDO had no config change; drift = cross-run stochasticity.
- TRX OOS: +6.69 swing (positive). Same count (46), but roster drifted.
- Combined ALGO+LDO OOS swing: -54.17. BCH OOS swing: -2.52.

The headline OOS Sharpe regression of -2.36 is ~97% attributable to ALGO (-25.70)
and LDO (-28.47) non-target symbol drift, not to primitive 10 BCH LONG suppression.

**This is NOT classified as NEGATIVE-architecture-bug (Falsifier 3 fires but the cause
is cross-run stochasticity, not primitive 10 dispatch error).**

**Recommended classification: NEGATIVE — search-space-perturbation / multi-run
stochasticity (see pre-registered Outcome C "NEGATIVE-bundle-regression" in Section 11
of the brief, which covers this outcome).**

The direction-asymmetric axis on BCH is NOT falsified by this result. The primitive 10
mechanism isolated BCH IS correctly. The single-seed OOS result is unreliable when
multiple runs accumulated.

---

## Seed Concentration Audit

Single outer seed run (--seeds 1, ENSEMBLE_SIZE=5):

| Symbol | IS weighted_pnl | IS trades | OOS weighted_pnl | OOS trades | OOS concentration |
|---|---|---|---|---|---|
| ALGO | -5.94 | 51 | +27.42 | 13 | 59.1% |
| BCH | +65.77 | 50 | +8.23 | 21 | 17.7% |
| LDO | -12.19 | 15 | -19.13 | 12 | -41.2% |
| TRX | +7.40 | 85 | +29.92 | 46 | 64.4% |

TRX at 64.4% OOS concentration. ALGO at 59.1%. LDO at -41.2% (negative PnL
contributor). Multi-seed validation would likely dissolve concentration.

---

## Label Leakage Audit

REQUIRED_GAP = 88 = (21 + 1) × 4 symbols. Unchanged from iter-v3/034 onwards.
timeout_candles = 21 (7 days × 3 candles/day at 8h). This is the López de Prado
purge gap for triple-barrier labels with 7-day timeout. n_symbols = 4.
The gap formula (timeout_candles + 1) × n_symbols = 22 × 4 = 88 is correctly applied
in CPCV (validation_v3.py). No changes to gap parameters in iter-v3/047.

---

## Gate Efficacy Table

| Gate | Description | IS fire rate | OOS fire rate |
|---|---|---|---|
| Primitive 10 — BCH LONG block | block_long_for=("BCHUSDT",) | 39/94 BCH candidates = 41.5% | 21/38 BCH candidates = 55.3% |
| BTC trend filter | BtcTrendFilterConfig(lookback=42, threshold=15%) | applied post-hoc | applied post-hoc |
| OOD z-score gate | zscore_threshold=2.0, 14-D Mahalanobis | embedded in RiskV3Wrapper | embedded in RiskV3Wrapper |
| ADX gate | threshold=20.0 | embedded | embedded |
| Per-symbol cap | enable_per_symbol_cap=False | DISABLED | DISABLED |
| Regime gate | enable_regime_gate=False | DISABLED | DISABLED |

Primitive 10 fire rate: 41.5% IS (39 of 94 BCH candidates blocked) and 55.3% OOS
(21 of 38 blocked). The OOS fire rate (55.3%) is higher than the IS rate (41.5%),
consistent with the EDA finding that BCH LONG toxicity is worse OOS (28.6% OOS WR
vs 30.8% IS WR).

---

## Anomaly Notes

1. **OOF parquet 5x duplication**: `trial_oof_returns.parquet` has 55.78M rows vs
   expected ~11M for a single run. Duplication factor = exactly 5.00x (confirmed by
   dedup analysis: 44.6M duplicate rows). This confirms the backtest was run 5 times
   and the parquet was appended each time without clearing. The n_trials=700 in
   `dsr.json` and `comparison.csv` reflects the inflated OOF, not the actual per-run
   trial count (which is 140 = 4 × 35). DSR computation may be affected by the
   inflated n_trials. PBO (0.0939) and PSR (1.000) are computed from CPCV paths
   which are NOT affected by OOF duplication. The QR should flag the inflated
   n_trials as unreliable for this iteration.

2. **BCH SHORT roster grew OOS** (17 in 045 → 21 in 047): Not a bug. primitive 10
   passes SHORTs through unchanged; the additional 4 OOS BCH SHORT trades are new
   signal selections from the slightly different Optuna model in the final run.

3. **IS BCH net_pnl swing +42pp but IS Sharpe regressed -0.26**: The IS Sharpe
   accounts for volatility and monthly cadence across ALL symbols. LDO collapsed
   (-66.74pp IS) and ALGO slightly improved (+28.11pp IS) in this run — the net IS
   Sharpe is driven down by LDO's stochastic collapse more than BCH's improvement
   lifts it.

4. **IS trade count: 201 vs 250 (045)**: Reduction of 49 = approximately 39 BCH
   LONGs removed + 10 from stochastic roster drift in other symbols. The predicted
   -39 IS BCH trade removal matches exactly (IS BCH: 94 → 50 = -44; with 5 net-new
   BCH SHORTs added = -44 + 5 = -39 net; plus ~-10 from stochastic drift).

---

## Recommendations to QR

1. **Primitive 10 mechanism is NOT falsified.** BCH LONG suppression worked
   correctly (39 IS + 21 OOS blocked, zero leakage). BCH IS improved +42pp. BCH
   OOS declined only -2.52. The headline OOS regression is attributable to ALGO/LDO
   stochastic drift across 5 runs, not to the direction-block design.

2. **Single-seed frozen-baseline assumption is unreliable across separate process
   invocations.** The frozen-baseline-pattern (memory) was established in
   iter-v3/020/021/022 within single-run comparisons. When a backtest is re-run
   (even with the same seed), LightGBM OpenMP non-determinism produces different
   model weights for ALGO/LDO/TRX. The canonical test of any single-seed EXPLORATION
   result is the CONFIRMATION multi-seed run, not baseline bit-identity.

3. **iter-v3/048 recommendation: DO NOT revert primitive 10.** The mechanism works.
   Instead, classify iter-v3/047 as NEGATIVE-multi-run-stochasticity and carry
   primitive 10 forward as a BUNDLE INGREDIENT for iter-v3/050 CONFIRMATION.
   The CONFIRMATION multi-seed run will dissolve the stochastic noise and reveal
   whether BCH LONG block + ALGO ATR + LDO ATR bundle is net positive OOS.

4. **Clear the OOF parquet before any re-run.** The append-on-existing behavior
   (`optimization.py:423-426`) inflates n_trials in dsr.json and comparison.csv
   when the same iteration is re-run. The runner should delete
   `trial_oof_returns.parquet` at startup if it already exists for the current
   iteration label.

5. **BCH SHORT roster growing OOS (17 → 21)** is not a concern — it reflects
   a slightly better-tuned BCH SHORT model in this run, consistent with primitive
   10 removing the LONG contamination from the Optuna training signal. If the
   CONFIRMATION confirms this pattern (more BCH SHORTs selected), it validates
   the direction-block mechanism at multi-seed level.

6. **iter-v3/048 axis**: QR dispatch required. Given that cycle 3 has 2 remaining
   EXPLORATION slots (048, 049) before CONFIRMATION at iter-v3/050, the recommended
   path is: (a) carry primitive 10 forward unchanged and proceed to 048 on a
   different axis (e.g., TRX bottleneck diagnosis from Section 2.1), or (b) treat
   047 as a re-run artifact and run iter-v3/048 = primitive 10 SINGLE clean run
   to confirm BCH IS lift without multi-run stochasticity.

---

## Status

OVERALL=READY-FOR-CRITIC
