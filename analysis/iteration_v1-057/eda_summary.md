# EDA — iter-v1/057 Pre-launch Checks

Feature under test: `ltc_vs_btc_ret_ratio_30`
Axis: feature-family — LTC-only specialist cross-asset idiosyncratic return vs BTC 30d z-scored (cycle-7 EXPLORATION 1/N)
IS cutoff: `OOS_CUTOFF_MS = 1742774400000` (2025-03-24)
Symbol scope: `LTCUSDT` only (LTC-only specialist feature)

**NOTE (rule bf2c812): EDA values are INFORMATIONAL. No ABORT trigger on any threshold. Artifact existence is the Phase 5.5 requirement.**

## Check Summary (Informational)

| Check | Result | Value | Note |
|-------|--------|-------|------|
| ADF stationarity (LTCUSDT) | PASS (informational) | p=0.000000e+00 | No block on result |
| IC max |Pearson| | informational | 0.0797 vs `trend_adx_14` | All values reported |
| Std check (>0.5) | ok | 1.1101 | LM Master Rec 1 — informational |
| Clip events (|z|>=9.9) | informational | 0 | LM Master Rec 1 load-bearing check |

## ADF Stationarity — `ltc_vs_btc_ret_ratio_30` (LTCUSDT IS-only)

| Symbol | ADF p-value | Stationary (p<0.05) | Note |
|--------|-------------|---------------------|------|
| LTCUSDT | 0.000000e+00 | YES | INFORMATIONAL |

## IC Orthogonality — `ltc_vs_btc_ret_ratio_30` vs 48 peer features (LTCUSDT IS)

Max |IC|: **0.0797** vs `trend_adx_14` (INFORMATIONAL — no ABORT trigger)

Informational thresholds: clean < 0.3 | document >= 0.6

### Top-15 |IC|

| Rank | Feature | |Pearson IC| | Band |
|------|---------|------------|------|
| 1 | `trend_adx_14` | 0.0797 | clean |
| 2 | `mom_macd_hist_12_26_9` | 0.0671 | clean |
| 3 | `mom_roc_10` | 0.0491 | clean |
| 4 | `mr_pct_from_low_20` | 0.0452 | clean |
| 5 | `vol_bb_bandwidth_20` | 0.0446 | clean |
| 6 | `interact_rsi_x_natr` | 0.0443 | clean |
| 7 | `trend_ema_cross_5_12` | 0.0440 | clean |
| 8 | `trend_aroon_osc_50` | 0.0437 | clean |
| 9 | `regime_momentum_signed_5d` | 0.0432 | clean |
| 10 | `stat_return_5` | 0.0424 | clean |
| 11 | `mom_rsi_14` | 0.0421 | clean |
| 12 | `mom_macd_line_12_26_9` | 0.0421 | clean |
| 13 | `mom_stoch_k_14` | 0.0400 | clean |
| 14 | `interact_stoch_x_adx` | 0.0393 | clean |
| 15 | `trend_aroon_osc_14` | 0.0380 | clean |

## Distribution Stats — `ltc_vs_btc_ret_ratio_30` (LTCUSDT IS-only)

| Symbol | N | Mean | Std | Skew | Kurt | P05 | Median | P95 | Min | Max | Clip(>=9.9) |
|--------|---|------|-----|------|------|-----|--------|-----|-----|-----|-------------|
| LTCUSDT | 5568 | 0.0091 | 1.1101 | -0.3534 | 6.1296 | -1.9028 | 0.0076 | 1.8195 | -7.2093 | 6.6095 | 0 |

## VERDICT

> **INFORMATIONAL ONLY** (rule bf2c812): EDA artifact committed for Phase 5.5 compliance. Values do not block Phase 6 launch. ADF p=0.0000e+00 (stationary). Max |IC| = 0.0797 vs `trend_adx_14`.
