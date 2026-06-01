# EDA — iter-v1/048 Pre-launch Checks

Feature under test: `trade_count_zscore_30`
Axis: microstructure — UNUSED-primitive defense (cycle-6 feature-family EXPLORATION 3/10)
IS cutoff: `OOS_CUTOFF_MS = 1742774400000` (2025-03-24)

**F5 thresholds TIGHTENED for iter-v1/048**: PASS < 0.30 | WARN [0.30, 0.60) | ABORT >= 0.60

## Gate Summary

| Gate | Status | Criterion |
|------|--------|-----------|
| F4 ADF stationarity | **PASS** | all 5 p < 0.05 |
| F5 IC orthogonality | **ABORT** | max |IC| < 0.30 (tightened) |
| F5 ABORT trigger    | **ABORT** | max |IC| >= 0.60 |

## F4 — ADF Stationarity (per symbol, IS-only)

| Symbol | ADF p-value | Status |
|--------|-------------|--------|
| BTCUSDT | 0.000000 | PASS |
| ETHUSDT | 0.000000 | PASS |
| LINKUSDT | 0.000000 | PASS |
| LTCUSDT | 0.000000 | PASS |
| DOTUSDT | 0.000000 | PASS |

## F5 — IC Orthogonality (Pearson, pooled IS)

Max |IC|: **0.9063** vs `vol_volume_rel_20`

PASS threshold: < 0.3  |  ABORT threshold: >= 0.6

### Top-10 |IC| with trade_count_zscore_30

| Rank | Feature | |Pearson IC| | Note |
|------|---------|------------|------|
| 1 | `vol_volume_rel_20` | 0.9063 | ABORT_TRIGGER |
| 2 | `vol_range_spike_24` | 0.7908 | ABORT_TRIGGER |
| 3 | `vol_range_spike_72` | 0.7322 | ABORT_TRIGGER |
| 4 | `vol_volume_pctchg_5` | 0.6662 | ABORT_TRIGGER |
| 5 | `interact_ret1_x_ret3` | 0.3181 | WARN |
| 6 | `cal_dow_norm` | 0.2530 |  |
| 7 | `trend_plus_di_14` | 0.2300 |  |
| 8 | `mr_pct_from_low_20` | 0.1431 |  |
| 9 | `vol_natr_14` | 0.1367 |  |
| 10 | `vol_bb_bandwidth_20` | 0.1324 |  |

## Distribution Stats — trade_count_zscore_30 (IS-only)

| Symbol | N | Mean | Std | Q25 | Median | Q75 | Min | Max |
|--------|---|------|-----|-----|--------|-----|-----|-----|
| BTCUSDT | 5698 | -0.0007 | 1.0357 | -0.7476 | -0.2386 | 0.5158 | -1.9950 | 4.7284 |
| ETHUSDT | 5698 | 0.0152 | 1.0624 | -0.7482 | -0.2213 | 0.5396 | -2.0457 | 4.9251 |
| LINKUSDT | 5649 | 0.0069 | 1.0905 | -0.7657 | -0.2596 | 0.5223 | -2.3699 | 5.0649 |
| LTCUSDT | 5658 | 0.0133 | 1.0862 | -0.7507 | -0.2392 | 0.5383 | -2.5873 | 5.0963 |
| DOTUSDT | 4996 | -0.0031 | 1.0720 | -0.7429 | -0.2669 | 0.4592 | -2.2142 | 4.9689 |

## VERDICT

> **ABORT PRE-LAUNCH**: max |IC| = 0.9063 >= 0.6. `trade_count_zscore_30` is highly collinear with `vol_volume_rel_20`. QR must review before backtest launch.
