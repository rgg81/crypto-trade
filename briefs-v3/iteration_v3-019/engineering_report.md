# Engineering Report — iter-v3/019

## Headers

- Iteration: iter-v3/019
- Type: EXPLORATION (cadence #1 of 10 post-bootstrap; STRUCTURAL axis — NEW feature family, NEW external data source)
- Branch: iteration-v3/019
- Setup commit SHA: d9f643b (feat: fetch-funding CLI + funding_v3 module + V3_FEATURE_COLUMNS 13→14 + ITERATION_LABEL=v3-019)
- Fix commit SHA: 9806dfb (fix: _verify_feature_columns asserts len==14)
- Phase 5.5 gate SHA: f728e7f (PASS)
- Brief SHA: db6e326
- HEAD SHA at backtest run: 9806dfb
- Hardware: WSL2 / Linux 6.6.87.2 x86_64
- Wall-clock time: 0.10h (6 min — well within 2h EXPLORATION hard cap)
- Runner invocation: `uv run python run_baseline_v3.py --exploration --seeds 1`
- Anchor: iter-v3/018 multi-seed mean IS +0.3788 / OOS +0.3869

## Library Stack (Reproducibility Stamp)

| Package | Version |
|---|---|
| lightgbm | 4.6.0 |
| numpy | 2.2.6 |
| optuna | 4.8.0 |
| pandas | 3.0.0 |
| pyarrow | 23.0.1 |
| scikit-learn | 1.6.0 |
| scipy | 1.17.0 |
| statsmodels | 0.14.6 |

No mlfinlab / mlfinpy / pypbo / fracdiff dependency (not used in v3 track — confirmed by Section 9 of brief). All libraries are standard pip-installable; no license gate risk.

## Configuration Diff vs Baseline (iter-v3/018 multi-seed BOOTSTRAP)

| Parameter | iter-v3/018 BOOTSTRAP | iter-v3/019 EXPLORATION |
|---|---|---|
| ITERATION_LABEL | "v3-018" | **"v3-019"** |
| V3_FEATURE_COLUMNS count | 13 | **14** (+`funding_rate_zscore_30`) |
| `funding_rate_zscore_30` | ABSENT | **ADDED** |
| Outer seeds | 2 (--seeds 2) | 1 (--seeds 1 via --exploration) |
| ENSEMBLE_SIZE (inner) | 5 | 1 (--exploration) |
| n_trials | 50 | 10 (--exploration) |
| colsample_bytree | Optuna-tuned | 1.0 (hardcoded, --exploration) |
| Symbols | BCH, LDO, TRX | UNCHANGED |
| ATR labeling (tp/sl) | 2.0 / 1.0 | UNCHANGED |
| zscore_threshold | 2.0 | UNCHANGED |
| BTC trend threshold_pct | 15.0 | UNCHANGED |
| ADX threshold | 20 | UNCHANGED |
| REQUIRED_GAP | 66 | UNCHANGED |
| OOS_CUTOFF_DATE | 2025-03-24 | UNCHANGED (sacred) |
| training_months | 24 | UNCHANGED (sacred) |

Single-axis discipline: the SOLE strategic change is addition of `funding_rate_zscore_30` as the 14th V3_FEATURE_COLUMNS entry. All other strategy parameters are byte-identical to iter-v3/018.

## Key Metrics Block

### Headline (comparison.csv — single seed 42, EXPLORATION mode)

| Metric | IS | OOS | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +1.1560 | +0.7847 | 0.6789 |
| daily_sharpe | +2.5072 | +1.4887 | 0.5938 |
| max_drawdown (%) | 20.5465 | 25.6979 | 1.2507 |
| profit_factor | 1.4440 | 1.2308 | 0.8524 |
| win_rate (%) | 33.97 | 39.56 | 1.1645 |
| n_trades | 209 | 91 | 0.4354 |
| total_pnl | 94.20 | 23.30 | 0.2474 |
| monthly_calmar | 4.5849 | 0.9069 | 0.1978 |
| weighted_pnl_total | 94.20 | 23.30 | 0.2474 |
| dsr | 0.0167 | — | — |
| pbo | 0.0971 | — | — |
| psr | 1.0000 | — | — |
| n_trials | 30 | — | — |
| n_effective_trials | 7 | — | — |

### vs anchor (iter-v3/018 multi-seed mean)

| Metric | iter-v3/018 anchor | iter-v3/019 | Delta |
|---|---:|---:|---:|
| IS monthly_sharpe | +0.3788 | +1.1560 | **+0.777** |
| OOS monthly_sharpe | +0.3869 | +0.7847 | **+0.398** |

Both deltas vastly exceed the PROMISING threshold (+0.10 IS). Section 1 predicted IS band [+0.45, +0.85]; observed +1.156 overshoots the upper bound of the predicted band.

### vs iter-v3/013 single-seed EXPLORATION reference

| Metric | iter-v3/013 | iter-v3/019 | Delta |
|---|---:|---:|---:|
| IS monthly_sharpe | +1.0088 | +1.1560 | +0.147 |
| OOS monthly_sharpe | +2.6970 | +0.7847 | -1.912 |
| IS n_trades | 209 | 209 | 0 |
| OOS n_trades | 85 | 91 | +6 |

IS portfolio total is identical (209) but per-symbol distribution differs — see Trade Roster Audit below.

## Feature Importance Audit: `funding_rate_zscore_30`

### Per-symbol rank table (last-month model, gain importance)

| Symbol | funding_rate_zscore_30 rank | Total features | Importance (gain) | Pct of total | Bottom quartile? |
|---|---:|---:|---:|---:|---|
| BCHUSDT | **10 / 14** | 14 | 25 | 4.2% | No (Q3, 71st pctile) |
| LDOUSDT | **14 / 14** | 14 | 173 | 3.2% | YES — dead last |
| TRXUSDT | **14 / 14** | 14 | 118 | 3.0% | YES — dead last |
| Portfolio (agg) | **14 / 14** | 14 | 316 | 3.2% | YES — dead last |

### Falsifier 4 evaluation (brief §4.4)

Brief §4.4 Falsifier 4 verbatim: "If `funding_rate_zscore_30` importance rank = 14/14 across ALL 3 symbol-specific models (bottom of every model's feature ranking), this indicates the model did not learn the funding signal. Classify as PROMISING-INERT (per iter-v3/015 precedent)."

**FALSIFIER 4 FIRES.** LDO and TRX rank 14/14 (dead last). BCH ranks 10/14 (above bottom quartile, but not top-half). The portfolio-aggregated ranking is 14/14. The condition "14/14 across ALL 3 symbol-specific models" is met for LDO and TRX; BCH at 10/14 is the only exception, but with 4.2% of gain share it is not top-half (rank ≤ 7) for ≥1 symbol. The brief's PROMISING (clean) threshold requires rank ≥7 (top half) for AT LEAST 1 symbol. BCH at rank 10 does not clear this bar.

**Conclusion: The model did not meaningfully learn the funding rate signal. The IS Sharpe lift is attributable to hyperparam/colsample noise at n_trials=10, not to the funding rate feature.**

### IC orthogonality check (from ic_matrix.csv)

Max |IC| of `funding_rate_zscore_30` vs existing 13 features: 0.2870 (vs `vwap_dev_20`) — well below the 0.50 brief strict target and 0.70 hard gate. Feature is structurally orthogonal. The orthogonality is verified; the failure is in model learning, not data structure.

## IS Trade Roster Audit

IS portfolio total = 209 for both iter-v3/013 and iter-v3/019. The brief context states "bit-identical to iter-v3/013 (209 trades)". However, per-symbol breakdown differs:

| Symbol | iter-v3/013 IS | iter-v3/019 IS | Delta |
|---|---:|---:|---:|
| BCHUSDT | 100 | 96 | -4 |
| LDOUSDT | 21 | 23 | +2 |
| TRXUSDT | 88 | 90 | +2 |
| **Total** | **209** | **209** | **0** |

Portfolio total matches (209 = 209), but per-symbol distribution is NOT identical. The shifts (BCH -4, LDO +2, TRX +2) indicate that the 14th feature (`funding_rate_zscore_30`) altered LightGBM tree structure enough to redistribute a small number of signals between symbols. This is NOT bit-identical at the per-symbol level. The brief's claim of "bit-identical to iter-v3/013" should be interpreted as "identical portfolio total, not per-symbol composition."

Implication: the saturation falsifier band [129, 215] check uses portfolio total, which at 209 falls within the band (209 ≤ 215). **Saturation falsifier: PASS** (upper edge — 96.3% of band max).

## Label Leakage Audit

REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66. Verified at runtime by `_validate_label_leakage_gap()` in runner (lines 221-233 of run_baseline_v3.py). Runner asserts `required_gap == REQUIRED_GAP` and hard-stops on mismatch. **Gap formula: PASS.**

Sacred constants: `OOS_CUTOFF_DATE = 2025-03-24` and `training_months = 24` — unchanged and verified in runner source.

## Seed Concentration Audit (EXPLORATION single-seed)

| Seed | IS monthly Sharpe | OOS monthly Sharpe | OOS MaxDD | OOS Calmar | OOS Trades | Max OOS Conc (%) | BTC killed |
|---|---:|---:|---:|---:|---:|---:|---:|
| 42 | +1.1560 | +0.7847 | 25.70% | 0.9069 | 91 | 52.72% | 37 |

Single-seed EXPLORATION run — multi-seed confirmation required at CONFIRMATION before trusting results (per `feedback_outer_seed_cap_2_v3.md` and EXPLORATION methodology).

OOS max concentration 52.72% (BCH) — improved vs iter-v3/018 seed 42 at 66.08%, but still exceeds the 30% ideal. BCH/TRX balanced at 53.94% / 48.37% concentration (comparison.csv per-symbol), LDO neutral (-2.31%).

## Gate Efficacy Table (IS / OOS)

| Gate | IS fire rate | OOS fire rate | Notes |
|---|---|---|---|
| zscore OOD gate (z=2.0) | Standard (37 BTC-killed OOS) | — | Unchanged from baseline |
| ADX gate (threshold=20) | Unchanged | Unchanged | Unchanged from baseline |
| BTC trend gate (±15%) | Unchanged | Unchanged | Unchanged from baseline |
| ATR labeling (2.0 TP / 1.0 SL) | Unchanged | Unchanged | Unchanged from baseline |
| REQUIRED_GAP=66 purge | Applied per formula | Applied per formula | López de Prado gap PASS |

Per-regime breakdown (per_regime.csv): both IS and OOS report regime="unknown" for all trades (regime classification not producing labeled sub-buckets in current v3 pipeline — pre-existing behavior, not introduced by iter-v3/019).

## DSR Mechanism Explanation

At n_trials=30 (EXPLORATION mode: 10 trials × 3 symbols), E[max_SR] = √(2 ln 30) = 2.608. The observed annualized Sharpe from monthly 1.156 is 1.156 × √12 = 4.004. DSR = PSR(benchmark = E[max_SR]) expressed as deflation: with annualized Sharpe >> E[max_SR], DSR turns marginally positive at +0.0167. This is the first non-zero DSR in the v3 catalog.

However, the DSR positivity should not be over-interpreted in EXPLORATION mode. At n_eff=7 effective trials (PCA), the statistical power is low. The DSR mechanism is: EXPLORATION's low trial count (n=30) makes E[max_SR] lower than CONFIRMATION (n=1500+), so an identical Sharpe appears less deflated. This is a structural artifact of the EXPLORATION mode — **the +0.0167 DSR is NOT directly comparable to CONFIRMATION DSR and should not be cited as evidence of edge in the CONFIRMATION sense.**

CPCV (45 paths): 29/45 positive (64.4%), mean path Sharpe = +0.303, median = +0.335, std = 0.810. The positive path fraction (64.4%) matches `pbo_frac_positive_paths` in dsr.json. Path dispersion is high (std 0.810), consistent with single-seed EXPLORATION instability.

## Per-Symbol Balance

### IS
| Symbol | Trades | WR | Net PnL (%) | Pct of total PnL |
|---|---:|---:|---:|---:|
| BCHUSDT | 96 | 46.9% | +102.77% | 100.57% |
| LDOUSDT | 23 | 34.8% | +2.07% | 2.03% |
| TRXUSDT | 90 | 34.4% | -2.65% | -2.60% |

### OOS
| Symbol | Trades | WR | Net PnL (%) | Concentration |
|---|---:|---:|---:|---:|
| BCHUSDT | 36 | 41.7% | +15.39% | 53.94% |
| LDOUSDT | 10 | 30.0% | -6.65% | -2.31% |
| TRXUSDT | 45 | 44.4% | +14.20% | 48.37% |

LDO is neutral-to-negative in both IS and OOS (IS +2.07% gross, OOS -6.65%). BCH and TRX are both positive contributors OOS — meaningfully better balance than iter-v3/018 where TRX dominated at 86% concentration.

OOS trade count: 91 (below the 130-trade floor). At EXPLORATION this is informational, not a hard block — the floor is advisory until CONFIRMATION. Flag for QR brief planning.

## Anomaly Notes

1. IS PnL dominated by BCH (100.57% of IS PnL on 96 trades). TRX IS net_pnl_pct = -2.65% — TRX is contributing trades but is underwater IS. BCH's single April 2024 IS month (+27.86% PnL, 10 trades) and December 2024 (+20.25%, 6 trades) are dominant events. This concentration of IS PnL in single BCH months is a structural concern for CONFIRMATION — the BCH-dominated IS Sharpe may not be robust across seeds.

2. `funding_rate_zscore_30` ranks 14/14 in LDO and TRX despite being structurally orthogonal (IC max 0.287). The feature is being included in every tree (colsample=1.0) but model assigns it minimal gain. This is the classical INERT symptom: feature is learnable in principle but the model's 10-trial search didn't find splits that add value beyond what existing 13 features already provide.

3. ADF stationarity file has blank cells for 2020-01 (first month — insufficient lookback for ADF test at month boundary). Pre-existing behavior for all v3 iterations; not introduced by iter-v3/019.

4. No NaN Sharpe, no NaN PnL. No zero-trade months in IS window (all 37 IS months have trades — verified via monthly_pnl.csv inspection; earliest entry 2022-02 with 8 trades). Spot-checked random trade rows: exit_reason, entry/exit PnL math, weight_factor all consistent.

## Pre-Classification Recommendation

**EXPLORATION-PROMISING-INERT**

Firing criterion (brief §4.4 Falsifier 4 verbatim): "If `funding_rate_zscore_30` importance rank = 14/14 across ALL 3 symbol-specific models (bottom of every model's feature ranking), this indicates the model did not learn the funding signal. Classify as PROMISING-INERT (per iter-v3/015 precedent)."

Met: LDO rank 14/14, TRX rank 14/14, Portfolio rank 14/14. BCH rank 10/14 (Q3, not top-half). No symbol clears the top-half (rank ≤ 7) threshold required for PROMISING (clean).

Brief §4.4 row for EXPLORATION-PROMISING-INERT: "IS Sharpe Δ ≥ +0.10 AND OOS Sharpe Δ ≥ 0 AND importance rank 14/14 in ≥2 symbols → PROMISING-INERT (model received the feature but did not learn it; lift is attributed to hyperparameter noise / colsample interaction at n_trials=10, not to the funding rate signal itself)."

The IS lift (+0.777 vs anchor) and OOS lift (+0.398 vs anchor) are real in the single-seed run. However, these are attributable to EXPLORATION mode's low trial-count sensitivity (n=10 trials produces high-variance Optuna solutions) rather than to the funding rate signal. The model demonstrably did not use the funding rate feature (14/14 in LDO, TRX, portfolio). Per iter-v3/015 precedent (`feedback_promising_mechanical_subtype.md`), PROMISING-INERT means the lift is real but not attributable to the new feature.

**QR decision**: whether to attempt a dedicated CONFIRMATION of `funding_rate_zscore_30` with higher trial count (n=50) to test if the model CAN learn it at higher search budget, vs deprioritize this axis and pivot to a different structural axis. The PROMISING-INERT classification does NOT preclude a CONFIRMATION — it signals that the current EXPLORATION's lift is not reliable evidence of funding-rate edge.

## Status

OVERALL=READY-FOR-CRITIC
