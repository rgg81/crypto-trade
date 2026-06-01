# EDA — iter-v1/049 Pre-launch Checks

Feature under test: `long_short_zscore_30`
Axis: feature-family — NON-KLINE-CLASS defense, top-trader positioning sentiment (cycle-6 EXPLORATION 4/10)
IS cutoff: `OOS_CUTOFF_MS = 1742774400000` (2025-03-24)

**F5 thresholds TIGHTENED for iter-v1/049** (third consecutive codification): PASS < 0.30 (IDEAL) | DOCUMENT [0.30, 0.60) | ABORT >= 0.60

## Gate Summary

| Gate | Status | Criterion |
|------|--------|-----------|
| F4 ADF stationarity | **PASS** | all 5 symbols p < 0.05 |
| F5 IC orthogonality | **PASS** (IDEAL) | max |IC| = 0.2505 vs `cal_hour_norm` |
| F5 ABORT trigger | OK | max |IC| >= 0.6 |

## F4 — ADF Stationarity (per symbol, IS-only)

| Symbol | ADF p-value | Status |
|--------|-------------|--------|
| BTCUSDT | 1.082194e-25 | PASS |
| ETHUSDT | 3.407127e-19 | PASS |
| LINKUSDT | 6.529617e-18 | PASS |
| LTCUSDT | 5.998094e-19 | PASS |
| DOTUSDT | 7.551123e-18 | PASS |

## F5 — IC Orthogonality (Pearson, pooled IS)

Max |IC|: **0.2505** vs `cal_hour_norm`

PASS threshold: < 0.3  |  DOCUMENT band: [0.3, 0.6)  |  ABORT threshold: >= 0.6

### Top-15 |IC| with `long_short_zscore_30`

| Rank | Feature | |Pearson IC| | Note |
|------|---------|------------|------|
| 1 | `cal_hour_norm` | 0.2505 |  |
| 2 | `funding_rate_zscore_90` | 0.2221 |  |
| 3 | `trend_minus_di_14` | 0.2063 |  |
| 4 | `mom_rsi_14` | 0.2039 |  |
| 5 | `trend_ema_cross_5_12` | 0.1997 |  |
| 6 | `interact_rsi_x_adx` | 0.1976 |  |
| 7 | `funding_rate_zscore_30` | 0.1955 |  |
| 8 | `regime_momentum_signed_5d` | 0.1928 |  |
| 9 | `trend_plus_di_14` | 0.1899 |  |
| 10 | `interact_rsi_x_natr` | 0.1883 |  |
| 11 | `mom_stoch_d_14` | 0.1830 |  |
| 12 | `mom_roc_10` | 0.1757 |  |
| 13 | `vol_mfi_14` | 0.1753 |  |
| 14 | `interact_stoch_x_adx` | 0.1730 |  |
| 15 | `mom_stoch_k_14` | 0.1723 |  |

## Distribution Stats — `long_short_zscore_30` (IS-only)

| Symbol | N | Mean | Std | Skew | Kurt | P05 | P95 | Min | Max |
|--------|---|------|-----|------|------|-----|-----|-----|-----|
| BTCUSDT | 4195 | -0.0311 | 1.2057 | 0.0408 | 0.9281 | -1.7558 | 1.8473 | -5.2421 | 5.2947 |
| ETHUSDT | 2765 | 0.0850 | 1.2109 | -0.0969 | 0.6814 | -1.7132 | 1.8473 | -5.2323 | 5.2947 |
| LINKUSDT | 2765 | 0.1692 | 1.2373 | -0.0403 | 0.1623 | -1.5150 | 2.0600 | -5.1933 | 5.2947 |
| LTCUSDT | 3215 | 0.0997 | 1.1606 | -0.0252 | 0.8566 | -1.5286 | 1.9524 | -5.1089 | 5.2947 |
| DOTUSDT | 2765 | 0.1307 | 1.2401 | -0.0544 | 0.3047 | -1.6273 | 2.0785 | -5.2810 | 5.2947 |

## VERDICT

> **PASS** (F4 + F5 both clear): max |IC| = 0.2505 < 0.3 (IDEAL). Proceed to backtest launch. PROMISING-CLEAN-eligible.
