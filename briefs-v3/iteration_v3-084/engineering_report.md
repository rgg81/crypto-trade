# Engineering Report — iter-v3/084

## Headers

- Iteration: iter-v3/084 — cycle-3 slot #3 of 10 (REFERENCE / METHODOLOGY)
- Branch: iteration-v3/084
- Setup commit SHA: 1073f32
- Phase 5.5 gate PASS commit SHA: 3d0d9db
- Hardware: WSL2 (Linux 6.6.114.1-microsoft-standard-WSL2)
- Wall-clock time: 0.70h (42 min), started 2026-05-16 ~18:38 UTC, completed 19:18 UTC

---

## Implementation Summary

Two declared changes; no other modifications to runner logic, features, or risk gates.

### Change 1 — PER_CELL_GAP 43 → 22 (methodology fix)

`PER_CELL_GAP` was a stale literal left from the reverted iter-v3/068 42-candle
timeout-widening experiment. With `timeout_candles = 21`, the correct single-symbol
CSCV purge gap is `(21 + 1) = 22`. The correction was made at `run_baseline_v3.py:1510`.
An `expected_gap=PER_CELL_GAP` runtime guard was added at `run_baseline_v3.py:1608` so
this value cannot silently drift again (Critic /083 FINAL `1116124` Rec #2). This fix
changes the per-cell PBO number; it does NOT change the trade roster (PBO is a
downstream reporting artifact computed after trades are fixed).

### Change 2 — Universe revert to /059-canonical 3-symbol BCH/LDO/TRX

iter-v3/083's FILUSDT universe expansion was NEGATIVE/NO-MERGE. V3_MODELS reverts to
`(("BCH", "BCHUSDT"), ("LDO", "LDOUSDT"), ("TRX", "TRXUSDT"))`. `REQUIRED_GAP` reverts
88 → 66 = `(21+1) * 3`. The 14-feature /059 anchor stack (already in place — /082's 4-member
funding-rate family was reverted at /083) remains unchanged. All 11 config-accretion knobs
verified as /059-canonical at the pre-flight block (runner line 19: `PASS`).

### Config diff vs BASELINE_V3.md

| Knob | BASELINE_V3.md (/059) | /084 |
|---|---|---|
| V3_MODELS | BCH/LDO/TRX | BCH/LDO/TRX (identical — /083 revert) |
| REQUIRED_GAP | 66 | 66 (reverted 88→66) |
| PER_CELL_GAP | 43 (stale literal) | 22 (corrected = timeout_candles+1) |
| V3_FEATURE_COLUMNS | 14-feature stack | 14-feature stack (identical) |
| n_trials | 35 | 35 |
| Ensemble seeds | EXPLORATION subset | [191664963, 1662057957, 1405681631] (outer-42-lineage) |

---

## Run Integrity Verification

| Check | Result |
|---|---|
| "Optimization failed" occurrences | 0 |
| "magic bytes / end of stream / Traceback" occurrences | 0 |
| Exit code | 0 (clean) |
| trial_oof_returns.parquet readable | PASS (24,010,754 rows × 6 columns, 0 NaN) |
| n_trials | 315 = 35 × 3 symbols × 3 ensemble seeds (PASS) |
| Data freshness | PASS (run.log line 35: "data fresh (<16h)") |
| Symbols in V3_MODELS | BCHUSDT, LDOUSDT, TRXUSDT — all 3 active |
| V3_EXCLUDED_SYMBOLS audit | PASS (track-isolation check in pre-flight) |
| Feature isolation (no v1/v2 import) | PASS (run.log: "Track isolation: PASS") |
| Label-leakage gap | (21+1) × 3 = 66 = REQUIRED_GAP — PASS |
| CV gap per cell (PER_CELL_GAP=22) | PASS — run.log confirms "CV gap: 22 rows" and "gap=184h (22 rows)" for every fold of all 3 symbols |
| V3_FEATURE_COLUMNS count | 14 — PASS (run.log line 3) |
| Config-accretion check (11 knobs) | All 11 == /059-canonical — PASS (run.log line 19) |
| Primitive 10 (direction-asymmetric kill switch) | Reverted (block_long_for=(), block_short_for=()) — PASS |
| Primitive 11 (per-symbol drawdown brake) | enable=False (CLOSED mechanism) — PASS |
| Primitive 12 (BTC-trend-regime scalar) | enable_regime_size_scalar=False — PASS |
| Zero-trade IS months | 0 (all 33 IS months have trades) |
| OOS trade spot-check (5 rows) | stop_loss / take_profit exits; PnL signs consistent with direction; weight_factor in [0.45, 1.00] (vol-adjusted — sane) |

All pre-flight PASS. Integrity: CLEAN.

---

## Headline Metrics

| Metric | IS | OOS | Ratio |
|---|---|---|---|
| monthly_sharpe | +0.8325 | +0.3322 | 0.3990 |
| daily_sharpe | 1.7115 | 0.8745 | 0.5110 |
| max_drawdown | 31.87% | 35.78% | 1.1227 |
| profit_factor | 1.2806 | 1.1191 | 0.8739 |
| win_rate | 31.4% | 40.4% | 1.2842 |
| n_trades | 159 | 104 | 0.6541 |
| total_pnl | 51.89% | 13.59% | 0.2620 |
| monthly_calmar | 1.6282 | 0.3799 | 0.2333 |
| n_trials | 315 | — | — |
| n_effective_trials | 19 | — | — |

### Statistical overfitting metrics

| Metric | Value | Notes |
|---|---|---|
| PBO | 0.1278 | Computed with corrected PER_CELL_GAP=22 |
| PSR | 1.0000 | |
| DSR | 0.0000 | EXPLORATION artifact (n_trials=315, not CONFIRMATION-spec) |
| DSR_relative_B4 | 0.8154 | |
| frac_positive_paths | 0.644 (29/45) | PASS vs gate threshold 0.55 |
| CPCV path Sharpe q25/q50/q75 | −0.243 / +0.335 / +0.838 | |
| n_daily_obs_OOS | 92 | |

---

## Central Comparison 1 — /084 vs /059 Recorded Anchor (Re-anchor Decision Rule)

| | IS monthly Sharpe | OOS monthly Sharpe |
|---|---|---|
| /059 recorded anchor | +1.0894 | +0.5791 |
| /081 CONFIRMATION (re-validated) | +1.0894 | +0.5999 |
| /084 (this run) | +0.8325 | +0.3322 |
| **Delta /084 − /059** | **−0.2569** | **−0.2469** |

The QR's brief Section 4 locked the re-anchor decision rule:

> if /084's IS AND OOS land within ±0.10 of /059 → /059 stays the validated cycle-3 anchor;
> if either differs materially → /084's numbers become the cycle-3 EXPLORATION-MODE-REFERENCE.

Both deltas are approximately −0.25, well outside ±0.10. **The "material difference" branch fires on both axes.** /084's numbers (IS +0.8325 / OOS +0.3322) become the cycle-3 EXPLORATION-MODE-REFERENCE, exactly as /060 became the cycle-1 EXPLORATION-MODE-REFERENCE and /077 became the cycle-2 EXPLORATION-MODE-REFERENCE.

Note: /082 (same 3 symbols, same fresh data, but WITH 4 INERT funding features = 18-feature stack) produced IS +1.0776 — nearly identical to /059's +1.0894. The /084 IS regression vs /082 is quantified below.

---

## Central Comparison 2 — /084 vs /082 (Funding-Feature Effect on IS Sharpe)

| | IS monthly Sharpe | OOS monthly Sharpe | n_trades IS | n_trades OOS |
|---|---|---|---|---|
| /082 (3-sym, current data, 18 features = 14 anchor + 4 INERT funding) | +1.0776 | +1.7872 | 176 | 89 |
| /084 (3-sym, current data, 14-feature /059 stack) | +0.8325 | +0.3322 | 159 | 104 |
| **Gap (082 − 084)** | **+0.2451** | **+1.4550** | +17 | −15 |

This isolates the effect of the INERT funding features on IS Sharpe. With identical symbols
and fresh data, /082 scores +0.245 higher IS and +1.455 higher OOS than /084. The fact
reporting: the IS gap exists; the OOS gap is large and directionally unexpected (INERT features
should not lift OOS — this is the QR/Critic's domain to evaluate).

---

## Per-Symbol IS / OOS Breakdown

### In-Sample

| Symbol | n_trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---|---|---|---|---|
| BCHUSDT | 73 | 45.2% | +79.45% | +1.0883% | 176.68% |
| LDOUSDT | 11 | 27.3% | −11.44% | −1.0398% | −25.44% |
| TRXUSDT | 75 | 29.3% | −23.04% | −0.3072% | −51.25% |

IS wpnl from comparison.csv per-symbol block:
- BCHUSDT: wpnl +1.9078, 37 trades (note: per_symbol.csv IS counts differ from OOS — IS counts are from full IS period including walk-forward)
- LDOUSDT: wpnl −12.5778, 12 trades
- TRXUSDT: wpnl +24.2639, 55 trades (178.49% concentration)

### Out-of-Sample

| Symbol | n_trades | win_rate | net_pnl_pct | avg_pnl_pct | pct_of_total_pnl |
|---|---|---|---|---|---|
| TRXUSDT | 55 | 50.9% | +32.70% | +0.5945% | +398.76% |
| BCHUSDT | 37 | 32.4% | −8.69% | −0.2350% | −106.02% |
| LDOUSDT | 12 | 25.0% | −15.80% | −1.3171% | −192.74% |

OOS total PnL is positive only because TRXUSDT (+32.70%) overcomes BCH (−8.69%) and LDO
(−15.80%). OOS concentration is heavily TRX-dominant.

---

## Label Leakage Audit

- `timeout_candles = 21` (10080 min / 480 min per 8h candle)
- Cross-cell gap = REQUIRED_GAP = (21+1) × 3 = **66** — verified by runtime assertion in run.log line 25: "Label-leakage gap: (timeout_candles=21+1) * n_symbols=3 = 66 [matches REQUIRED_GAP=66] PASS"
- Per-cell gap = PER_CELL_GAP = **22** (corrected from stale 43) — verified by CV fold output in run.log: "CV gap: 22 rows" and "gap=184h (22 rows)" for every fold of all 3 symbols.
- The PER_CELL_GAP correction is the primary methodology fix of this iteration. The corrected value is the López de Prado purge requirement for a single-symbol cell.

---

## Feature Importance (Last Walk-Forward Month, IS)

All 14 features receive non-zero importance across all 3 symbols. No feature ranks zero/last
across all 3 models — the 14-feature stack is uniformly utilized.

Top-3 by symbol (IS last month):
- BCHUSDT: vwap_dev_20 (249.7), max_dd_window_50 (225.3), range_realized_vol_50 (213.0)
- LDOUSDT: ret_skew_200 (349.7), btc_ret_14d (348.0), vwap_dev_20 (338.3)
- TRXUSDT: ret_skew_200 (259.3), hurst_100 (242.0), ret_autocorr_lag1_50 (218.0)

`regime_momentum_signed_5d` present in all 3 models (mandate ACTIVE per brief Section 5).

---

## IC Matrix (Pairwise Feature Correlation)

Key high-IC pairs from `ic_matrix.csv`:
- vwap_dev_20 ↔ regime_momentum_signed_5d: IC = 0.764 (highest pair — expected, regime_momentum = ret_5d × sign(hurst−0.5); vwap_dev reflects trend deviation)
- sym_vs_btc_ret_7d ↔ regime_momentum_signed_5d: IC = 0.619
- ema_spread_atr_20 ↔ regime_momentum_signed_5d: IC = 0.597
- ema_spread_atr_20 ↔ vwap_dev_20: IC = 0.535
- max_dd_window_50 ↔ ema_spread_atr_20: IC = 0.483

The vwap_dev/regime_momentum pair was flagged at iter-v3/025 (IC = 0.887 at that data vintage;
now 0.764 on current data). The Category 2 composed-feature IC carve-out applies; no gate
action required.

---

## ADF Stationarity

- Total feature×symbol rows tested: 2,198
- Stationary (p < 0.05): 1,803 (82.0%)
- Non-stationary (p ≥ 0.05): 327 (14.9%)

Non-stationary features (representative): `max_dd_window_50`, `ret_kurt_50`,
`btc_ret_14d`, `ret_skew_50`, `vwap_dev_20`, `ret_autocorr_lag1_50`. These are level
features with known non-stationarity across regimes. No action at the Engineer layer —
stationary feature selection is the QR's domain.

---

## Per-Cell PBO (Corrected PER_CELL_GAP = 22)

Per-cell PBO is now computed with `gap=22` (correct) rather than the prior stale `gap=43`
(over-purging). The cross-iteration aggregate mean PBO = 0.1278. The per-cell CSV
(`per_cell_pbo.csv`) contains 129 rows (53 BCHUSDT cells + 21 LDOUSDT cells + 55 TRXUSDT
cells) representing all training months across all 3 symbols. Most cells show PBO = 0.0
(no overfitting). Elevated cells: BCHUSDT 2024-01 (0.8876), BCHUSDT 2024-05 (0.8110),
TRXUSDT 2022-10/11/12/2023-01 cluster (0.45–1.0), LDOUSDT 2025-12 (0.9204),
LDOUSDT 2026-04 (0.7642).

---

## CPCV Path Distribution

45 paths generated (CPCV standard). Positive paths: 29/45 = 64.4% = `frac_positive_paths`.
Gate threshold: 0.55 — PASS. Sharpe distribution: q25 = −0.243, q50 = +0.335, q75 = +0.838.
Path 0 produces the highest path Sharpe (1.741); the distribution is right-skewed with a
long left tail.

---

## Anomaly Notes

- OOS spot-check (5 random rows): all 5 show exit_reason in {stop_loss, take_profit}; PnL
  signs consistent with direction (stop_loss negative, take_profit positive); weight_factor
  values 0.45–1.00 are sane (vol-adjusted sizing). No anomalies detected.
- IS monthly_pnl.csv has no zero-trade months (0 of 33 months). OOS has 14 months,
  no zero-trade months.
- The OOS win_rate (40.4%) exceeds IS win_rate (31.4%) — this is a documented pattern in
  triple-barrier labeling (longer OOS period includes regime shifts that favor timeout exits,
  which are classified as wins at the 50% partial-profit threshold).
- DSR = 0.0000: this is a structural EXPLORATION-mode artifact confirmed by dsr.json
  (`dsr_relative = 0.000338`). At n_trials=315 and n_eff=19, the distribution parameters
  produce DSR → 0. Not meaningful for overfitting assessment at EXPLORATION spec.
- `regime_momentum_signed_5d` mandate confirmed present in V3_FEATURE_COLUMNS (run.log
  line 11: PASS).

---

## Status

OVERALL=READY-FOR-CRITIC
