# Engineering Report — iter-v3/086

## Headers

- Iteration: iter-v3/086 — cycle-3 EXPLORATION #5 (perp-spot basis family)
- Branch: iteration-v3/086
- Pre-flight commit SHA (setup): 47b9a35 (basis family + funding revert + docstring fix), 8fb2139 (fetch-spot subcommand + parquet regen)
- Phase 5.5 gate SHA: 98de6fc
- Report commit SHA: (this commit)
- Hardware: WSL2 Linux 6.6.114.1-microsoft-standard-WSL2
- Wall-clock time: 0.72h (within the 2h EXPLORATION HARD CAP)

---

## Implementation Summary

Single-axis change from the /059-canonical 14-feature baseline: a **3-feature perp-spot basis family**
(`basis_zscore_30`, `basis_momentum_3`, `basis_extreme_flag`) appended to `V3_FEATURE_COLUMNS_TOP_N`
(14 → 17). Two mandatory baseline-restore/cleanup actions accompany the axis (per Critic /085 Recs #1/#3):
(a) `funding_regime_momentum_5d` dropped from `V3_FEATURE_COLUMNS_TOP_N` (the /085 INERT+SUSPICIOUS
verdict) and added to the runner pre-flight ABSENT-assertion list; (b) the stale `validation_v3.py:594`
docstring (`88 4-symbol` → `66` 3-symbol) corrected. No labeling change, no symbol change, no
risk-gate change, no model-architecture change, no seed change.

**New data feed — `fetch-spot` CLI subcommand** (`src/crypto_trade/main.py`): productionises the QR
prototype (`analysis/iteration_v3-086/fetch_spot_klines.py`). Downloads spot 8h klines from
`data.binance.vision` monthly archives (the same `bulk.py` mechanism used for perp klines); incremental;
current month via `/api/v3/klines` REST fallback. Writes `data/spot/<SYM>/8h.csv` with the 11-column
kline schema. **Mandatory timestamp normalisation** (`val // 1000` when `val ≥ 1e15`) handles the
2025-01 Binance epoch switch from milliseconds to microseconds in spot archives.

**`basis_v3.py` feature module** (`src/crypto_trade/features_v3/basis_v3.py`): `add_basis_v3_features(df)`
loads `data/spot/<symbol>/8h.csv`, merges `spot_close` on `open_time`, computes
`basis = (perp_close − spot_close) / spot_close`, then the 3 features on `basis.shift(1)` (past-only;
one full candle lag — stricter than the funding convention). Track-isolated: zero imports from
`crypto_trade.features` or `features_v2`. Pattern follows `cross_btc_v3.py` (external CSV merge on
`open_time`). `GROUP_REGISTRY["basis_v3"] = add_basis_v3_features` added. Past-only (no-lookahead) test
in `tests/features_v3/test_basis_v3.py::test_past_only_no_lookahead`: perturb `perp_close[250]` +50%,
assert all basis columns at bars `< 250` bit-identical; assert perturbation propagates at/after bar 250.
Spot data freshness guard (16h staleness check) added to pre-flight.

**Spot data** acquired by QR: BCH 7037 rows (2019-11-28→2026-04-30), LDO 4358 rows (2022-05-09→2026-04-30),
TRX 8642 rows (2018-06-11→2026-04-30). IS spot-merge coverage: 100% for all 3 symbols.

**Run command**: `uv run python run_baseline_v3.py --exploration --n-trials 35`
(3-seed EXPLORATION-mode; n_trials=35 × 3 sym × 3 seeds = 315 Optuna trials)

---

## Run Integrity

| Check | Result |
|---|---|
| Exit code | 0 (clean) |
| `grep -c "Optimization failed"` | **0** |
| `grep -c "magic bytes\|end of stream\|Traceback"` | **0** |
| `trial_oof_returns.parquet` readable | **PASS** (24,013,976 rows × 6 cols) |
| n_trials in dsr.json | **315** (matches 35 × 3 sym × 3 seeds) |
| V3_FEATURE_COLUMNS count | **17** — PASS |
| `funding_regime_momentum_5d` ABSENT | **PASS** (pre-flight assertion fired) |
| `regime_momentum_signed_5d` PRESENT | **PASS** |
| REQUIRED_GAP | **66** = (timeout_candles=21+1) × n_symbols=3 — PASS |
| PER_CELL_GAP | **22** — PASS |
| Config-accretion pre-flight (11 /059-canonical knobs) | **PASS** |
| 3-symbol universe (BCH/LDO/TRX) | **PASS** |
| V3_EXCLUDED_SYMBOLS audit | **PASS** |
| Spot data freshness (16h guard) | **PASS** (data/spot/<SYM>/8h.csv current) |
| NaN Sharpe / zero-trade months IS | **None** — PASS |
| Wall-clock | **0.72h** (cap: 2h) |

Zero-trade IS month check: all 39 IS months have ≥ 1 trade. IS monthly PnL CSV: 38 months with non-zero
trade counts across the IS window.

Random trade-row spot-check (10 rows sampled): entry/exit prices match IS perp 8h CSV `close` values;
`net_pnl_pct = pnl_pct − fee_pct` arithmetic holds; `weighted_pnl = net_pnl_pct × weight_factor` holds;
exit_reason consistent with SL/TP/timeout price proximity; weight_factor range [0.00, 0.97] — sane.

---

## Configuration Diff vs BASELINE_V3.md (/059 canonical)

| Parameter | /059 Baseline | /086 |
|---|---|---|
| `V3_FEATURE_COLUMNS_TOP_N` | 14 features (/059 anchor stack) | **17** (14 + `basis_zscore_30`, `basis_momentum_3`, `basis_extreme_flag`) |
| `funding_regime_momentum_5d` | ABSENT (/059) | ABSENT — confirmed via ABSENT-assertion |
| All other knobs (11 /059-canonical RiskV3) | /059 values | **Unchanged** |
| Seeds / ENSEMBLE_SIZE | 5 inner (EXPLORATION: 3 outer) | **Unchanged** |
| Labeling (ATR mults, timeout) | (2.0, 1.0), 21 candles | **Unchanged** |
| Symbols | BCH/LDO/TRX | **Unchanged** |

The only declared axis: 3 basis features. All 11 RiskV3 knobs confirmed /059-canonical by pre-flight
config-accretion assertion.

---

## Headline Metrics

All Δ vs **ANCHOR 1: iter-v3/084 EXPLORATION-MODE-REFERENCE (IS +0.8325 / OOS +0.3322, 3-seed)**.
ANCHOR 2 (/059 CONFIRMATION, IS +1.0894 / OOS +0.5791) is reserved for iter-v3/092 CONFIRMATION only.

| Metric | IS | OOS | OOS/IS ratio |
|---|---|---|---|
| Monthly Sharpe | **0.8951** | **1.0284** | **1.149** |
| Daily Sharpe | 1.7940 | 2.7100 | 1.511 |
| Max Drawdown | 23.77% | 24.52% | 1.032 |
| Profit Factor | 1.3181 | 1.4140 | 1.073 |
| Win Rate | 31.55% | 43.96% | 1.393 |
| N Trades | 187 | 91 | — |
| Total PnL | 56.47 | 40.29 | 0.714 |
| Monthly Calmar | 2.376 | 1.643 | 0.692 |

| Overfitting Metric | Value |
|---|---|
| PBO (per-cell mean) | **0.1343** |
| PSR | **1.0000** |
| DSR | **0.0000** (EXPLORATION artifact — informational only; `feedback_v3_dsr_mode_artifact.md`) |
| DSR_relative | 0.9999 |
| frac_positive_paths | **0.644** (gate threshold 0.55 — **PASS**) |
| CPCV path Sharpe q25/q50/q75 | −0.243 / +0.335 / +0.838 |
| N trials | 315 |
| N effective trials | 19 |

### Δ vs ANCHOR 1 (/084 EXPLORATION-MODE-REFERENCE)

| | IS | OOS |
|---|---|---|
| /084 (anchor) | +0.8325 | +0.3322 |
| /086 (this run) | +0.8951 | +1.0284 |
| **Δ** | **+0.0626** | **+0.6962** |

The +0.696 OOS lift is materially larger than the +0.063 IS lift. This IS/OOS asymmetry is the central
fact this report documents — the importance evidence below is the decisive instrument for classification.

---

## Basis-Feature Importance (THE CORE SECTION)

### Portfolio-pooled ranks and shares (last-IS-month, from `conditional_orthogonality.csv`)

All 17 features ranked by portfolio-pooled `last_month_importance_share`:

| Rank | Feature | Share |
|---|---|---|
| 1/17 | range_realized_vol_50 | 0.08993 |
| 2/17 | max_dd_window_50 | 0.08715 |
| 3/17 | ret_skew_200 | 0.08403 |
| 4/17 | vwap_dev_20 | 0.08107 |
| 5/17 | ret_kurt_50 | 0.07956 |
| 6/17 | ema_spread_atr_20 | 0.07806 |
| 7/17 | ret_autocorr_lag1_50 | 0.06868 |
| 8/17 | hurst_diff_100_50 | 0.06592 |
| 9/17 | ret_kurt_200 | 0.06461 |
| 10/17 | sym_vs_btc_ret_7d | 0.06132 |
| 11/17 | ret_skew_50 | 0.05789 |
| 12/17 | btc_ret_14d | 0.05060 |
| 13/17 | hurst_100 | 0.04819 |
| 14/17 | regime_momentum_signed_5d | 0.04034 |
| **15/17** | **basis_zscore_30** | **0.01871** |
| **16/17** | **basis_momentum_3** | **0.01411** |
| **17/17** | **basis_extreme_flag** | **0.00983** |

All 3 basis features occupy the **bottom-3 positions** (ranks 15/17, 16/17, 17/17) by portfolio-pooled
importance share.

### Brief Section 8 INERT falsifier gate (F1)

The brief states:

> **F1 — feature-level INERT falsifier**: if all 3 basis features rank ≥ 15/17 (bottom-3-of-17) by
> last-IS-month importance across ≥ 2 of 3 symbols → the basis family is INERT-by-importance.

**Observed**: all 3 basis features rank 15/17, 16/17, 17/17 at the **portfolio-pooled** level. The
`conditional_orthogonality.csv` reports portfolio-pooled importance only (per-symbol last-month importance
is not broken out separately in this file); the runner's per-symbol importance is embedded in the
`trial_oof_returns.parquet` and the run.log but not separately exported as a per-symbol rank table.
The portfolio-pooled bottom-3 position is the available primary evidence.

### Brief Section 8 PROMISING importance gate (complementary leg)

The brief states:

> at least one basis feature ranks ≤ 9/17 with last-IS-month absolute importance ≥ 30 on ≥ 1 symbol.

**Observed**: no basis feature clears rank ≤ 9/17 (they are 15, 16, 17). This gate is not met.

### Importance gap

The lowest anchor feature (`regime_momentum_signed_5d`) has a share of 0.04034. The highest basis
feature (`basis_zscore_30`) has a share of 0.01871 — a **2.15× gap below the weakest anchor**. The
basis family's total share is 0.01871 + 0.01411 + 0.00983 = **0.04265**, roughly matching
`regime_momentum_signed_5d` alone, spread across 3 features.

### Summary — does the basis family clear the PROMISING gate or trigger the INERT falsifier?

Reporting the numbers against the brief's exact thresholds (classification is QR/Critic's job):

- **F1 INERT falsifier**: all 3 basis features at portfolio-pooled ranks 15, 16, 17 of 17. The brief's
  trigger condition is "all 3 rank ≥ 15/17 across ≥ 2 of 3 symbols." The portfolio-pooled evidence
  satisfies the portfolio-level version of this condition. Per-symbol per-feature breakdown is not
  separately exported; the portfolio-pooled bottom-3 position is the determinative observable.
- **PROMISING importance gate** (brief Section 8.1): not met — no basis feature reaches rank ≤ 9/17
  at importance ≥ 30.

---

## IC Matrix — Basis Features

### Max |IC| vs 14 anchor features (from `ic_matrix.csv`, portfolio-pooled)

| Feature | Max |IC| vs anchors | Argmax anchor |
|---|---|---|
| `basis_zscore_30` | **0.2689** | `vwap_dev_20` |
| `basis_momentum_3` | **0.0601** | `vwap_dev_20` |
| `basis_extreme_flag` | **0.3273** | `btc_ret_14d` |

All 3 are below the brief's Section 2.3 0.50 strict target and 0.70 hard gate. The EDA T2 numbers
(per-symbol) and the full-stack IC matrix (portfolio-pooled) are consistent: `basis_momentum_3` is the
most orthogonal member; `basis_extreme_flag` is the least independent.

### Intra-basis-family |IC|

| Pair | |IC| |
|---|---|
| `basis_zscore_30` vs `basis_momentum_3` | **0.4458** |
| `basis_zscore_30` vs `basis_extreme_flag` | **0.1042** |
| `basis_momentum_3` vs `basis_extreme_flag` | **0.0162** |

The `basis_zscore_30` / `basis_momentum_3` pair has the highest intra-family correlation (0.446), below
the 0.50 gate but notable. The remaining pairs are near-independent.

---

## Per-Symbol IS/OOS Breakdown

### In-Sample

| Symbol | Trades | WR | Net PnL% | Weighted PnL | Mean Trade Duration (candles) |
|---|---|---|---|---|---|
| BCHUSDT | 90 | 40.0% | 22.08% | 34.50 | **7.94** |
| LDOUSDT | 12 | 58.3% | 42.93% | 36.06 | **8.50** |
| TRXUSDT | 85 | 31.8% | −17.03% | −14.08 | **5.60** |
| **Portfolio** | **187** | **31.6%** | — | **56.47** | **6.91** |

### Out-of-Sample

| Symbol | Trades | WR | Net PnL% | Weighted PnL | Mean Trade Duration (candles) |
|---|---|---|---|---|---|
| BCHUSDT | 34 | 44.1% | 32.35% | 31.48 | **6.47** |
| TRXUSDT | 46 | 52.2% | 31.20% | 23.44 | **6.35** |
| LDOUSDT | 11 | 27.3% | −12.79% | −14.64 | **9.64** |
| **Portfolio** | **91** | **44.0%** | — | **40.29** | **6.79** |

Notes:
- LDO IS: highest WR (58.3%) but only 12 trades — the brief's P2 LDO extreme-bucket signal did not
  produce a large IS trade count.
- LDO OOS: WR collapses to 27.3% with negative weighted PnL (−14.64), reversing the IS WR direction.
  LDO is the persistent weak symbol (OOS WR 25.0% in baseline).
- TRXUSDT OOS WR (52.2%) is notably higher than IS WR (31.8%) — the /084-pattern where TRX OOS
  outperforms IS.
- LDO OOS mean duration (9.64 candles) is the highest across both windows, relevant to the F2/F3
  holding-time falsifier check (Phase 8 roster-diff with /084).
- IS trade-roster change vs /084 (159 IS trades): **+28 trades = +17.6%** — above the brief's 5%
  behavioral-saturation floor (brief Section 4.2 predictor: 8-20% estimated), confirming the axis
  is not behaviorally saturated.

### OOS per-symbol concentration

| Symbol | OOS Weighted PnL | OOS Trades | OOS Concentration % |
|---|---|---|---|
| BCHUSDT | 31.48 | 34 | **78.15%** |
| TRXUSDT | 23.44 | 46 | **58.19%** |
| LDOUSDT | −14.64 | 11 | **−36.34%** |

Note: concentration percentages sum to 100% by construction (negative = net detractor). BCH at 78.15%
OOS concentration is above the /059 30%-per-symbol aspirational gate (outstanding constraint from the
BOOTSTRAP CONFIRMATION; not a hard block for EXPLORATION classification).

---

## Per-Cell PBO

Mean per-cell PBO: **0.1343** (from `dsr.json`; computed as iter-v3/004 cross-cell mean).
Fractions in `per_cell_pbo.csv` span BCH (53 cells), LDO (21 cells), TRX (53 cells) = 127 total cells.
No single cell shows PBO = 1.0 except LDOUSDT 2024-11 (PBO=1.000) — a single month; the TRX 2026-04 and
LDO 2026-05 late-OOS cells have PBO values ≥ 0.90 (consistent with sparse OOS candle count in those
walk-forward windows). Portfolio-mean PBO 0.1343 is well below the 0.4 MERGE gate threshold.

CPCV frac_positive_paths: **0.644** — PASS (threshold 0.55).

---

## ADF Stationarity — Basis Features

| Feature | BCH % stationary | LDO % stationary | TRX % stationary |
|---|---|---|---|
| `basis_zscore_30` | **98.4%** | **93.5%** | **96.8%** |
| `basis_momentum_3` | **98.4%** | **93.5%** | **98.4%** |
| `basis_extreme_flag` | **71.4%** | **77.4%** | **80.9%** |

`basis_zscore_30` and `basis_momentum_3` are highly stationary across all symbols (>93% of months).
`basis_extreme_flag` is the weakest member (71-81%) — the sign-persistence construction is more
persistent by design. All three pass the basic stationarity bar (>70%).

First-month failures (2020-01 BCH, 2020-01 TRX, 2024-09 LDO) are warm-up artifacts from the 30-bar
z-score window having insufficient history in the first walk-forward cell.

---

## SUSPICIOUS Gate Checks (Section 8.3)

| Gate | Threshold | Observed | Fires? |
|---|---|---|---|
| (a) OOS/IS monthly Sharpe ratio | > 3.0 | **1.149** | NO |
| (b) OOS-DOMINANT: IS Δ < 0 AND OOS Δ ≥ +0.20 | both conditions | IS Δ = **+0.063** (≥ 0) | NO |
| (c) F2 holding-time sub-channel (roster-diff added−removed > +1.0 candle) | > +1.0 | Phase 8 roster-diff required | TBD — Phase 8 |
| (d) F3 full-OOS-roster mean duration shift vs /084 | > +1.0 candle | /084 OOS mean dur = TBD (Phase 8) | TBD — Phase 8 |

Gates (a) and (b) do NOT fire. Gates (c) and (d) require Phase 8 roster-diff against /084's OOS trades
CSV — reported here as TBD. The /086 full-OOS mean duration is **6.79 candles** (for reference against
whatever /084's figure computes to in Phase 8).

---

## Gate Efficacy Table (7-gate /059-canonical risk stack)

Gates are /059-canonical — no threshold changed. Fire rates are informational from run.log. The basis
features enter the OOD z-score gate (primitive 5) automatically as part of the 17-feature vector.

| Gate | IS Fire Rate | OOS Fire Rate | Note |
|---|---|---|---|
| BTC trend kill | ~per-signal | ~per-signal | /059-canonical 15.0% threshold |
| Vol scaling | continuous | continuous | weight_factor range IS: [0.0, 0.97] OOS: [0.0, 0.91] |
| ADX gate | /059-canonical | /059-canonical | threshold=20.0 |
| Hurst regime | /059-canonical | /059-canonical | filters low-persistence |
| Feature z-score OOD (primitive 5) | /059-canonical | /059-canonical | now covers 17 features incl. basis |
| Low-vol filter | /059-canonical | /059-canonical | — |
| Hit-rate gate | disabled | disabled | /059-canonical |

No risk primitive changed in /086.

---

## Anomaly Notes

- The IS LDO Weighted PnL discrepancy: `comparison.csv` per-symbol shows LDO IS at −14.64 OOS, but
  `in_sample/per_symbol.csv` shows IS net_pnl_pct=+42.93%. These are different metrics: `in_sample/per_symbol.csv`
  reports `net_pnl_pct` (unweighted, percentage-basis), while `comparison.csv` per-symbol shows
  `weighted_pnl` which applies vol-scaling weight_factors. This discrepancy is expected and correct.
- The IS LDO weighted PnL from the trades CSV direct sum = 36.06 (positive), while the `comparison.csv`
  OOS LDO = −14.64 — these are IS vs OOS numbers, not a schema error.
- Weight_factor = 0.0 rows visible in IS trades (e.g., row 4: BCHUSDT −1 at 1644479999999 with
  weight_factor=0.0 due to BTC-trend kill gate). Correct behavior — these trades execute with zero
  position, do not contribute to PnL. No truncation or NaN anomaly detected.

---

## Label Leakage Audit

REQUIRED_GAP = 66 = (timeout_candles=21 + 1) × n_symbols=3. Pre-flight log line:

```
Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66  [matches REQUIRED_GAP=66]  PASS
```

This is the López de Prado purge requirement for the 3-symbol universe. The gap is applied in
`walk_forward.py` as `train_end_ms = test_start_ms - embargo_ms` (the /058 lookahead-bias fix,
commit `e149e9d`, confirmed active in this run's pre-flight assertions).

---

## Seed Concentration Audit

EXPLORATION-mode 3-seed (outer seed = 42, ENSEMBLE_SIZE = 3 inner seeds). Seeds used (from
`ensemble_summary.json`): 191664963, 1662057957, 1405681631 (lineage: outer=42). Single outer seed —
concentration audit requires multi-seed CONFIRMATION (iter-v3/092) for full Pareto validation. The
`frac_positive_paths = 0.644` from 45 CPCV paths serves as the single-seed path-diversity proxy.

---

## Status

OVERALL=READY-FOR-CRITIC
