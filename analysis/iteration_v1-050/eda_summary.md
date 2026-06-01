# EDA — iter-v1/050 Pre-launch Checks

Feature under test: `dot_vs_btc_ret_ratio_30`
Axis: feature-family — DOT-only specialist cross-asset idiosyncratic return vs BTC 30d z-scored (cycle-6 EXPLORATION 5/10)
IS cutoff: `OOS_CUTOFF_MS = 1742774400000` (2025-03-24)
Symbol scope: `DOTUSDT` only (DOT-only specialist feature)

**NOTE (rule bf2c812): EDA values are INFORMATIONAL. No ABORT trigger on any threshold. Artifact existence is the Phase 5.5 requirement.**

## Check Summary (Informational)

| Check | Result | Value | Note |
|-------|--------|-------|------|
| ADF stationarity (DOTUSDT) | PASS (informational) | p=0.000000e+00 | No block on result |
| IC max |Pearson| | informational | 0.1246 vs `trend_adx_14` | All values reported |

## ADF Stationarity — `dot_vs_btc_ret_ratio_30` (DOTUSDT IS-only)

| Symbol | ADF p-value | Stationary (p<0.05) | Note |
|--------|-------------|---------------------|------|
| DOTUSDT | 0.000000e+00 | YES | INFORMATIONAL |

## IC Orthogonality — `dot_vs_btc_ret_ratio_30` vs 45 peer features (DOTUSDT IS)

Max |IC|: **0.1246** vs `trend_adx_14` (INFORMATIONAL — no ABORT trigger)

Informational thresholds: clean < 0.3 | document >= 0.6

### Top-15 |IC|

| Rank | Feature | |Pearson IC| | Band |
|------|---------|------------|------|
| 1 | `trend_adx_14` | 0.1246 | clean |
| 2 | `vol_bb_bandwidth_20` | 0.0844 | clean |
| 3 | `interact_natr_x_adx` | 0.0795 | clean |
| 4 | `vol_range_spike_72` | 0.0566 | clean |
| 5 | `oi_delta_30_z90` | 0.0547 | clean |
| 6 | `mr_pct_from_high_20` | 0.0532 | clean |
| 7 | `mr_pct_from_low_20` | 0.0446 | clean |
| 8 | `vol_natr_14` | 0.0425 | clean |
| 9 | `mom_roc_10` | 0.0388 | clean |
| 10 | `stat_autocorr_lag5` | 0.0365 | clean |
| 11 | `trend_aroon_osc_50` | 0.0340 | clean |
| 12 | `interact_ret1_x_ret3` | 0.0339 | clean |
| 13 | `vol_range_spike_24` | 0.0324 | clean |
| 14 | `trend_supertrend_14_3` | 0.0267 | clean |
| 15 | `trend_minus_di_14` | 0.0255 | clean |

## Distribution Stats — `dot_vs_btc_ret_ratio_30` (DOTUSDT IS-only)

| Symbol | N | Mean | Std | Skew | Kurt | P05 | Median | P95 | Min | Max |
|--------|---|------|-----|------|------|-----|--------|-----|-----|-----|
| DOTUSDT | 4906 | 0.0130 | 1.1066 | -0.3908 | 4.6351 | -1.8606 | 0.0200 | 1.8927 | -6.9578 | 5.8901 |

## VERDICT

> **INFORMATIONAL ONLY** (rule bf2c812): EDA artifact committed for Phase 5.5 compliance. Values do not block Phase 6 launch. ADF p=0.0000e+00 (stationary). Max |IC| = 0.1246 vs `trend_adx_14`.
