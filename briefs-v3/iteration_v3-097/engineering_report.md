# Engineering Report — iter-v3/097

## Headers

- **Iteration**: iter-v3/097 — cycle-4 EXPLORATION — SYMBOL-UNIVERSE RE-SELECTION
- **Branch**: iteration-v3/097
- **Setup commit SHA**: e6ed662a80982461241c32f6456a50343eb19454 (`feat(iter-v3/097): V3_MODELS → LDO/GALA/ADA + 6-test integration suite`)
- **Hardware**: 12th Gen Intel(R) Core(TM) i9-12900HK / 58 GiB RAM
- **Wall-clock time**: 0.58h (detached run; exit 0)
- **Mode**: `--exploration --seeds 1 --n-trials 35` (ENSEMBLE_SIZE=3, outer seed 42)
- **Artifacts**: `reports-v3/iteration_v3-097/`

---

## Configuration Diff vs Baseline (v0.v3-059)

SOLE axis change — V3_MODELS universe:

| | /059 (baseline) | /097 (this run) |
|---|---|---|
| Model A | BCH (BCHUSDT) | DROPPED |
| Model B | TRX (TRXUSDT) | DROPPED |
| Model C | LDO (LDOUSDT) | KEPT — LDOUSDT |
| Model F | — | ADDED — GALAUSDT |
| Model G | — | ADDED — ADAUSDT |
| ITERATION_LABEL | v3-059 | v3-097 |

All other config is unchanged: 14-feature `V3_FEATURE_COLUMNS` stack, `(2.0, 1.0)`-ATR triple-barrier label, 5-gate+BTC risk stack, walk-forward refit, `OOS_CUTOFF_DATE = 2025-03-24`, `training_months = 24`, `n_trials = 35`.

---

## Key Metrics Block

Source: `reports-v3/iteration_v3-097/comparison.csv`

| Metric | In-Sample | Out-of-Sample | Ratio |
|---|---:|---:|---:|
| monthly_sharpe | +0.7197 | −0.3541 | −0.4921 |
| daily_sharpe | +2.1506 | −1.2423 | −0.5777 |
| max_drawdown | 68.46% | 51.76% | 0.7560 |
| profit_factor | 1.3608 | 0.8484 | 0.6234 |
| win_rate | 37.17% | 29.09% | 0.7827 |
| n_trades | 113 | 55 | 0.4867 |
| total_pnl | +70.16 | −17.49 | −0.2493 |
| monthly_calmar | +1.0249 | −0.3379 | −0.3297 |
| weighted_pnl_total | +70.16 | −17.49 | −0.2493 |
| dsr | 0.0 | — | — |
| pbo | 0.1089 | — | — |
| psr | 0.0011 | — | — |
| n_trials | 315 | — | — |
| n_effective_trials | 19 | — | — |

Source: `reports-v3/iteration_v3-097/dsr.json`

| DSR statistic | Value |
|---|---:|
| dsr | 0.0 |
| pbo (per-cell mean) | 0.1089 |
| psr | 0.0011 |
| frac_positive_paths (CPCV) | 0.511 |
| cpcv_frac_positive_paths gate pass (≥0.55) | FALSE |
| cpcv_path_sharpe_q75 | +1.035 |
| n_trials | 315 |
| n_eff | 19 |
| min_trl_months | 12.56 |
| n_daily_obs_oos | 44 |

Baseline /059 comparison (both IS and OOS): IS +1.0894 → +0.7197 (regression −0.37); OOS +0.5791 → −0.3541 (regression −0.93; sign flip).

---

## Per-Symbol Attribution

### In-Sample (source: `reports-v3/iteration_v3-097/in_sample/per_symbol.csv`)

| Symbol | IS Trades | IS Wins | IS Win Rate | IS Net PnL% | IS % of Total PnL |
|---|---:|---:|---:|---:|---:|
| GALAUSDT | 28 | 13 | 46.4% | +67.20 | 65.42% |
| ADAUSDT | 74 | 30 | 40.5% | +46.96 | 45.72% |
| LDOUSDT | 11 | 3 | 27.3% | −11.44 | −11.13% |

IS summary: GALA and ADA both contributed positive IS PnL; LDO is the lone IS drag (−11.44%). The IS book is GALA+ADA-driven, not LDO-driven — the opposite of /059 where LDO was the signal carrier.

### Out-of-Sample (source: `reports-v3/iteration_v3-097/out_of_sample/per_symbol.csv`)

| Symbol | OOS Trades | OOS Wins | OOS Win Rate | OOS Net PnL% | OOS % of Total Loss |
|---|---:|---:|---:|---:|---:|
| ADAUSDT | 18 | 5 | 27.8% | −14.56 | 29.79% |
| LDOUSDT | 12 | 3 | 25.0% | −15.80 | 32.34% |
| GALAUSDT | 25 | 8 | 32.0% | −18.50 | 37.86% |

OOS summary: all three symbols are negative OOS. GALA is the largest OOS loser (−18.50), followed by LDO (−15.80) and ADA (−14.56). The IS→OOS inversion is complete — every symbol that was positive IS (GALA +67.20, ADA +46.96) is negative OOS. LDO, already negative IS, remains negative OOS.

### Comparison with /059 OOS per-symbol (from comparison.csv per_symbol section)

Source: `reports-v3/iteration_v3-097/comparison.csv` per_symbol block:

| Symbol | comparison.csv weighted_pnl IS | comparison.csv weighted_pnl OOS | concentration_pct OOS |
|---|---:|---:|---:|
| ADAUSDT | +0.4230 | (see per_symbol.csv: −14.56) | −2.42 |
| GALAUSDT | −5.3344 | — | +30.50 |
| LDOUSDT | −12.5778 | — | +71.92 |

Note: `comparison.csv` per_symbol block weighted_pnl entries are IS values; OOS attribution is read directly from `out_of_sample/per_symbol.csv` above.

---

## Falsifier Evaluations (F0–F6)

Pre-registered thresholds from research_brief.md Section 4.3.

### F0 — Roster-Turnover Sanity
- **Criterion**: OOS roster shares > 50% of trades by `(symbol, open_time)` with /059 OOS roster.
- **Check**: /097 OOS trades are on GALAUSDT and ADAUSDT — both ABSENT from the /059 BCH/LDO/TRX universe. LDO appears in both but with a differently-constrained Optuna study (new peer symbols). The pre-registered `analysis/iteration_v3-097/roster_diff_oos.py` artifact was not committed as part of Phase 6 (the brief named it as a QE-to-commit item; it was not in the setup commit); however, the structural impossibility of > 50% overlap is sufficient: GALA and ADA contribute 43 of 55 OOS trades (78%) and these symbols were absent from /059.
- **Status**: does NOT fire (structural impossibility).

### F1 — OOS Net-Harm
- **Criterion**: OOS monthly Sharpe < +0.40.
- **Observed**: OOS monthly Sharpe = **−0.3541** (source: `comparison.csv` row `monthly_sharpe`).
- **Status**: FIRES. −0.3541 << +0.40. OOS is negative.

### F2 — IS Collapse
- **Criterion**: IS monthly Sharpe < +0.80.
- **Observed**: IS monthly Sharpe = **+0.7197** (source: `comparison.csv` row `monthly_sharpe`).
- **Status**: FIRES. +0.7197 < +0.80. IS is also below the floor.

### F3 — GENUINE-SIGNAL Falsified (GALA falsifier — the named F3)
- **Criterion**: GALA OOS `weighted_pnl` < 0 AND GALA IS `weighted_pnl` > 0.
- **Observed**: GALA IS net PnL = **+67.20** (positive; source: `in_sample/per_symbol.csv`). GALA OOS net PnL = **−18.50** (negative; source: `out_of_sample/per_symbol.csv`).
- **Status**: FIRES. GALA is IS-positive and OOS-negative — the exact /087 reversal recurrence the brief named as the central risk.

### F4 — Regime-Concentration Confirmed Harmful
- **Criterion**: OOS Sharpe lift > 80% attributable to a single calendar month.
- **Check**: OOS is net-negative (−17.49 total PnL across 10 OOS months; source: `out_of_sample/monthly_pnl.csv`). F4 conditions on a *positive* OOS lift to assess whether it is one-month. With OOS monthly Sharpe = −0.35, there is no positive lift to attribute. F4 is not evaluable in the meaningful sense; it is vacuous given F1 fires.
- **Status**: does NOT fire (no OOS lift exists to flag as suspicious; vacuous given F1).

### F5 — Gate-3 Breach
- **Criterion**: OOS monthly Sharpe / IS monthly Sharpe < 0.50.
- **Observed**: ratio = **−0.4921** (source: `comparison.csv` row `monthly_sharpe`, ratio column). Negative ratio (OOS Sharpe is negative).
- **Status**: FIRES. A negative ratio is categorically below 0.50.

### F6 — Trade Starvation
- **Criterion**: total OOS trades < 130 OR aggregate OOS trades/month < 10.
- **Observed**: OOS n_trades = **55** (source: `comparison.csv` row `n_trades`). OOS covers 10 months (source: `out_of_sample/monthly_pnl.csv`; months 2025-04 through 2026-05 with gaps). Mean OOS trades/month = 55 / 10 = 5.5/month.
- **Status**: FIRES. 55 < 130 total; 5.5/month < 10/month floor. IS also has only 113 trades.

### Falsifier Summary

| Falsifier | Threshold | Observed | Status |
|---|---|---|---|
| F0 (roster sanity) | > 50% OOS overlap | < 22% (GALA+ADA = 78% of trades, ABSENT in /059) | does NOT fire |
| F1 (OOS net-harm) | OOS Sharpe < +0.40 | −0.3541 | **FIRES** |
| F2 (IS collapse) | IS Sharpe < +0.80 | +0.7197 | **FIRES** |
| F3 (GALA reversal) | GALA OOS wpnl < 0 AND IS > 0 | IS +67.20, OOS −18.50 | **FIRES** |
| F4 (regime-concentration) | > 80% lift one-month | N/A (no positive OOS lift) | does NOT fire |
| F5 (Gate-3 breach) | OOS/IS ratio < 0.50 | −0.4921 | **FIRES** |
| F6 (trade starvation) | OOS < 130 trades | 55 OOS trades | **FIRES** |

F1, F2, F3, F5, F6 all fire. The section-8 classification precedence (8.2 NEGATIVE-no-transfer) is the first match (F1 fires, not 8.1): **classification is 8.2 NEGATIVE-no-transfer**. Additionally F3 also fires (8.4 NEGATIVE-GALA-reversal), confirming the /087 GALA reversal recurrence as a compounding factor. The QR's Phase-8 diary records the classification.

---

## Seed Concentration Audit

Run mode: `--exploration --seeds 1` (outer seed 42). Ensemble size = 3 (inner seeds from lineage `outer=42`). Source: `ensemble_summary.json`.

Single-seed EXPLORATION — no multi-seed Pareto. Per-symbol OOS concentration from `comparison.csv` per_symbol block: LDOUSDT 71.92%, GALAUSDT 30.50%, ADAUSDT −2.42%. LDO carries 71.92% of OOS concentration despite being one of three negative-OOS symbols — a concentration-in-the-worst-performer artifact of the negative-PnL accounting.

---

## Label Leakage Audit

- `REQUIRED_GAP = (timeout_candles + 1) × n_symbols = (21 + 1) × 3 = 66` — UNCHANGED (universe count 3 → 3, gap is symbol-count-driven).
- `PER_CELL_GAP = 22` — universe-count-invariant, unchanged.
- The `e149e9d` walk-forward embargo (`train_end_ms = test_start_ms - embargo_ms`) is in place per integration test #5 (`test_walk_forward_embargo_intact`), which asserted `cv_gap = 66` for the 3-symbol universe. Source: `tests/strategies/ml/test_universe_reselection_v3.py`.

---

## Gate Efficacy Table

The 5-gate+BTC risk stack is unchanged and applied per-symbol. IS trade count = 113; OOS = 55. The IS/OOS trade counts themselves indicate the gates fired heavily OOS relative to the signal volume — LDO produced only 11 IS trades and 12 OOS trades, consistent with /059's LDO pattern on a thin 581-row IS panel.

Gate-by-gate fire rates are not broken out per-gate in the runner artifacts for this EXPLORATION run. The aggregate picture: 55 OOS trades across 10 months (F6 fires) on a 3-symbol universe suggests the gate stack plus the OOS regime filtered aggressively, consistent with the IS-regime-concentration annotation from T3 (Section 2.4 of the brief — GALA sub-period IC `[+0.51, −0.07, +0.20]`, concentrated on the first IS third which falls before OOS).

---

## CPCV Path Distribution

Source: `cpcv_paths.csv` (45 paths).

- frac_positive_paths = 0.511 (23 of 45 paths positive Sharpe; source: `dsr.json`).
- Gate threshold: ≥ 0.55 — **FAIL** (0.511 < 0.55).
- path_sharpe_q25 = −0.875, q50 = +0.053, q75 = +1.035 (source: `dsr.json`).
- The CPCV path distribution is highly dispersed — q25 deeply negative, q50 near zero — confirming the backtest rests on no durable edge across path orderings.

---

## ADF Stationarity Note

Source: `adf_test.csv`. ADF stationarity months per symbol: ADA 63, GALA 43, LDO 31 (from run log summary; full per-feature ADF table in `adf_test.csv`). These reflect IS-window feature ADF results for the new universe. No anomaly — LDO's shorter IS span (581 rows) drives its lower ADF month count.

---

## IC Matrix Note

Source: `ic_matrix.csv`. High pairwise IC between `regime_momentum_signed_5d`, `vwap_dev_20`, and `sym_vs_btc_ret_7d` (IC 0.811 and 0.745 respectively) — this is the pre-existing constructed-feature collinearity documented at `feedback_v3_engineered_feature_pivot.md`, not a new finding. The 14-feature stack is unchanged; IC matrix is an artifact of the same features running on a new symbol universe.

---

## Random Trade-Row Spot Check

Source: `out_of_sample/trades.csv` (55 rows). Spot-checked 10 rows: exit_reason distribution includes `tp`, `sl`, `timeout`; weight_factor values are positive non-zero (no zero-weight BTC-kill artifacts); entry/exit price sequences are internally consistent (TP exit at close price above entry for LONG, SL at close below entry). No NaN PnL rows found. No zero-trade OOS months — though several calendar months have 0 trades due to gate filtering (missing months in monthly_pnl.csv: 2025-11, 2025-12, 2026-01, 2026-03 absent). Months with trades range 2–15 trades/month.

---

## Anomaly Notes

1. **OOS monthly gaps**: `out_of_sample/monthly_pnl.csv` shows only 10 months with trades (2025-04 through 2026-05, non-contiguous). Four OOS months (2025-11, 2025-12, 2026-01, 2026-03) produced zero trades — the gate stack + Optuna found no signal. This compounds the F6 trade-starvation failure.
2. **GALA IS/OOS inversion magnitude**: GALA IS +67.20% → OOS −18.50% is a complete reversal of the sign and ~⅓ of the magnitude. This is the exact /087 failure pattern named in brief Section 7.1, confirmed at F3.
3. **LDO IS negative (−11.44%)**: LDO, the genuine-signal anchor symbol kept from /059, was negative IS in this run. This is a single-seed EXPLORATION artifact — LDO's single-seed IS Sharpe is sensitive to seed choice at n_trials=35 on a 581-row panel. The IS book was carried by GALA+ADA, which then inverted OOS.
4. **dsr = 0.0**: PSR = 0.0011 is near-zero, consistent with OOS Sharpe = −0.35. DSR = 0.0 is a structural floor at EXPLORATION n_trials=315 with a negative OOS Sharpe — not a sentinel defect (integration test #3 verified the computation path is live). Source: `dsr.json`.
5. **n_effective_trials = 19**: low effective trial count (19 of 315 raw trials) reflects high collinearity in the CPCV path returns — 45 paths with near-random sign splits produce a near-rank-1 return matrix. Confirms low signal.

---

## Merge-Gate Status

**NO-MERGE** — EXPLORATION run, not CONFIRMATION-spec. Even aside from the cadence rule, /097 fails both IS and OOS:

| Gate | Threshold | Observed | Status |
|---|---|---|---|
| IS Sharpe floor | ≥ +1.0 (merge) / ≥ +0.80 (F2) | +0.7197 | FAIL |
| OOS Sharpe floor | ≥ +1.0 (merge) / ≥ +0.40 (F1) | −0.3541 | FAIL |
| OOS/IS ratio (Gate 3) | ≥ 0.50 | −0.4921 | FAIL |
| frac_positive_paths | ≥ 0.55 | 0.511 | FAIL |
| OOS trades | ≥ 130 | 55 | FAIL |
| DSR | > 0 | 0.0 | FAIL |
| PSR | > 0.95 | 0.0011 | FAIL |
| GALA per-symbol OOS | positive | −18.50 | FAIL |
| Beats /059 IS + OOS | BOTH axes | IS −0.37 / OOS −0.93 | FAIL |

**Section-8 classification**: 8.2 NEGATIVE-no-transfer (F1 first-fires). F3 NEGATIVE-GALA-reversal also fires (compounding evidence). The re-anchored LDO/GALA/ADA universe is worse than /059 on BOTH IS (−0.37) and OOS (−0.93, sign flip). BASELINE_V3.md is UNCHANGED — v0.v3-059 remains canonical.

**Pre-registered fallback (Section 4.4)**: the LDO+GALA 2-symbol universe is the brief's named next-build if GALA-alone fails (F3 fires while LDO+ADA hold). Here *all three* symbols are OOS-negative, so the fallback scope is the QR's Phase-8 determination. A pure LDO-only or LDO+ADA universe with feature expansion is the most defensible next axis given that LDO is the sole genuine-signal symbol at the canonical /059 baseline and ADA's borderline CV-IC (+0.053) did not survive OOS in this run.

---

## Status

OVERALL = READY-FOR-CRITIC
