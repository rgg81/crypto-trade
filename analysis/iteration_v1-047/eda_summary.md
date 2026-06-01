# EDA — iter-v1/047 Pre-launch Checks

Feature under test: `skew_zscore_21`
Algebraic sister (LM concern): `stat_skew_20`
IS cutoff: `OOS_CUTOFF_MS = 1742774400000` (2025-03-24)

## Gate Summary

| Gate | Status | Criterion |
|------|--------|-----------|
| F4 ADF stationarity | **PASS** | all 5 p < 0.05 |
| F5 IC orthogonality | **FAIL** | max |IC| < 0.50 |
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

Max |IC|: **0.8132** vs `stat_skew_20`
|IC| vs `stat_skew_20` (algebraic sister): **0.8132**

### Top-10 |IC| with skew_zscore_21

| Rank | Feature | |Pearson IC| | Note |
|------|---------|------------|------|
| 1 | `stat_skew_20` | 0.8132 | ALGEBRAIC SISTER |
| 2 | `trend_minus_di_14` | 0.3928 |  |
| 3 | `mom_rsi_14` | 0.3873 |  |
| 4 | `trend_plus_di_14` | 0.3729 |  |
| 5 | `interact_rsi_x_adx` | 0.3646 |  |
| 6 | `trend_ema_cross_5_12` | 0.3227 |  |
| 7 | `regime_momentum_signed_5d` | 0.3190 |  |
| 8 | `interact_rsi_x_natr` | 0.3137 |  |
| 9 | `trend_supertrend_14_3` | 0.3003 |  |
| 10 | `mom_roc_10` | 0.2873 |  |

## Distribution Stats — skew_zscore_21 (IS-only)

| Symbol | N | Mean | Std | Q25 | Median | Q75 | Min | Max |
|--------|---|------|-----|-----|--------|-----|-----|-----|
| BTCUSDT | 5617 | 0.0148 | 1.1313 | -0.7740 | 0.0017 | 0.7629 | -4.5515 | 3.8953 |
| ETHUSDT | 5617 | -0.0021 | 1.1752 | -0.7334 | -0.0167 | 0.8263 | -5.0427 | 5.4524 |
| LINKUSDT | 5568 | -0.0165 | 1.1607 | -0.7279 | 0.0036 | 0.7498 | -5.5713 | 6.2215 |
| LTCUSDT | 5577 | -0.0384 | 1.1673 | -0.8103 | 0.0153 | 0.7907 | -5.0785 | 4.6723 |
| DOTUSDT | 4915 | 0.0010 | 1.1529 | -0.7593 | 0.0257 | 0.7892 | -5.7329 | 4.3009 |

## VERDICT

> **ABORT PRE-LAUNCH**: max |IC| = 0.8132 >= 0.60. skew_zscore_21 is nearly collinear with an existing feature. QR must review before backtest launch.
