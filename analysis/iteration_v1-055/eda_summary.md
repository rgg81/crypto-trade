# EDA — iter-v1/055 Pre-launch Checks

Feature under test: `eth_vs_btc_ret_ratio_30`
Axis: feature-family — ETH-only specialist cross-asset idiosyncratic return vs BTC 30d z-scored (cycle-6 EXPLORATION 10/10 FINAL)
IS cutoff: `OOS_CUTOFF_MS = 1742774400000` (2025-03-24)
Symbol scope: `ETHUSDT` only (ETH-only specialist feature)

**NOTE (rule bf2c812): EDA values are INFORMATIONAL. No ABORT trigger on any threshold. Artifact existence is the Phase 5.5 requirement.**

## Check Summary (Informational)

| Check | Result | Value | Note |
|-------|--------|-------|------|
| ADF stationarity (ETHUSDT) | PASS (informational) | p=0.000000e+00 | No block on result |
| IC max |Pearson| | informational | 0.1017 vs `trend_adx_14` | All values reported |
| Std check (>0.5) | ok | 1.1177 | LM Master Rec 1 — informational |
| Clip events (|z|>=9.9) | informational | 0 | LM Master Rec 1 load-bearing check |

## ADF Stationarity — `eth_vs_btc_ret_ratio_30` (ETHUSDT IS-only)

| Symbol | ADF p-value | Stationary (p<0.05) | Note |
|--------|-------------|---------------------|------|
| ETHUSDT | 0.000000e+00 | YES | INFORMATIONAL |

## IC Orthogonality — `eth_vs_btc_ret_ratio_30` vs 47 peer features (ETHUSDT IS)

Max |IC|: **0.1017** vs `trend_adx_14` (INFORMATIONAL — no ABORT trigger)

Informational thresholds: clean < 0.3 | document >= 0.6

### Top-15 |IC|

| Rank | Feature | |Pearson IC| | Band |
|------|---------|------------|------|
| 1 | `trend_adx_14` | 0.1017 | clean |
| 2 | `vol_bb_bandwidth_20` | 0.0909 | clean |
| 3 | `mr_pct_from_low_20` | 0.0803 | clean |
| 4 | `interact_natr_x_adx` | 0.0625 | clean |
| 5 | `interact_stoch_x_adx` | 0.0623 | clean |
| 6 | `mom_roc_10` | 0.0600 | clean |
| 7 | `interact_rsi_x_adx` | 0.0598 | clean |
| 8 | `mom_rsi_14` | 0.0595 | clean |
| 9 | `trend_plus_di_14` | 0.0575 | clean |
| 10 | `regime_momentum_signed_5d` | 0.0547 | clean |
| 11 | `mr_rsi_extreme_14` | 0.0547 | clean |
| 12 | `vol_cmf_14` | 0.0546 | clean |
| 13 | `mom_stoch_d_14` | 0.0499 | clean |
| 14 | `vol_mfi_14` | 0.0499 | clean |
| 15 | `trend_ema_cross_5_12` | 0.0484 | clean |

## Distribution Stats — `eth_vs_btc_ret_ratio_30` (ETHUSDT IS-only)

| Symbol | N | Mean | Std | Skew | Kurt | P05 | Median | P95 | Min | Max | Clip(>=9.9) |
|--------|---|------|-----|------|------|-----|--------|-----|-----|-----|-------------|
| ETHUSDT | 5608 | 0.0168 | 1.1177 | -0.2497 | 7.8209 | -1.5933 | 0.0037 | 1.9207 | -8.0874 | 7.5355 | 0 |

## VERDICT

> **INFORMATIONAL ONLY** (rule bf2c812): EDA artifact committed for Phase 5.5 compliance. Values do not block Phase 6 launch. ADF p=0.0000e+00 (stationary). Max |IC| = 0.1017 vs `trend_adx_14`.
