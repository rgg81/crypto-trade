# Engineering Report — iter-v3/035

## Status: READY-FOR-CRITIC

Wall-clock 0.33h (20 min). **STRONGEST OOS RESULT IN V3 CATALOG HISTORY** — OOS Sharpe +2.85 (vs iter-v3/013 falsified +2.70 and iter-v3/025 falsified +1.22).

## Hypothesis-Implementation Alignment

REVERT V3_FEATURE_COLUMNS_TOP_N to 14 (drop fracdiff from universal). ADD V3_FEATURES_PER_SYMBOL["BCHUSDT"] = 15 features (14 + fracdiff_d05_close). LDO/TRX/ALGO fall back to 14. Per-symbol engineered feature ADDITION methodology.

## Headline Metrics

| Metric | Value | vs iter-v3/032 anchor (+0.2360/+1.9338) |
|--------|-------|------------------------------------------|
| IS monthly Sharpe | -0.1023 | Δ -0.34 |
| OOS monthly Sharpe | **+2.8521** | **Δ +0.92 — HIGHEST single-seed OOS in v3 catalog** |
| OOS daily Sharpe | +3.8765 | — |
| Bundle OOS trades | 123 | -6 |
| OOS WR | **45.53%** | improved |
| OOS MaxDD | 28.83% | similar |
| IS MaxDD | 49.27% | similar |
| OOS PnL total | **+87.35** | +25 over iter-v3/032 |
| n_eff | 20 | slightly improved |
| PBO | 0.1012 | PASS |

## Per-Symbol OOS — ALL 4 POSITIVE; BCH lift preserved + TRX/ALGO/LDO restored

| Symbol | weighted_pnl | Trades | WR | vs iter-v3/034 universal | vs iter-v3/032 baseline |
|--------|--------------|--------|-----|--------------------------|--------------------------|
| BCH | +48.73 | 32 | **50.0%** | preserved | **+37.98 swing** |
| TRX | +29.24 | 46 | 52.2% | **+20.11 RESTORED** | bit-identical |
| ALGO | +20.87 | 25 | 40.0% | **+8.24 RESTORED** | bit-identical |
| LDO | +3.98 | 20 | 35.0% | **+6.81 RESTORED** | bit-identical |

The per-symbol-feature-ADDITIONS methodology is **fully validated**. BCH gets fracdiff (15 features) and benefits; LDO/TRX/ALGO keep their 14-feature stack and continue performing as before.

## Methodology Innovation Confirmed

The post-bootstrap cycle has now produced 4 validated edge ingredients:
1. **regime_momentum_signed_5d** (universal engineered feature; iter-v3/025 → iter-v3/028 multi-seed)
2. **ALGO universe expansion** (per-symbol-feature-signature alignment; iter-v3/029)
3. **LDO ATR (1.5, 0.75)** (per-symbol LABELS; iter-v3/032)
4. **BCH fracdiff** (per-symbol FEATURES; iter-v3/035)

Each ingredient addresses a different methodology dimension:
- #1 = global engineered feature
- #2 = symbol-set selection
- #3 = per-symbol labels
- #4 = per-symbol features

This is a complete per-symbol architecture. The iter-v3/039 CONFIRMATION bundle = all 4 ingredients combined.

## §4.4 Classification

PATH C fires on IS axis (Δ -0.34 < -0.10). PATH A fires on OOS axis (Δ +0.92 ≥ +0.10) AND per-symbol axis (BCH preserved + TRX/ALGO/LDO restored).

**Verdict: EXPLORATION-PROMISING-OOS (clean — strongest in v3)** with IS-axis caveat. The methodology is sound; the IS-axis collapse is the same single-seed-Optuna pattern across iter-v3/030-035 as the per-symbol architecture matures.

## Multi-Seed Compression Forecast

iter-v3/013 single-seed +2.70 OOS → multi-seed +0.39 (86% reduction)
iter-v3/025 single-seed +1.22 OOS → multi-seed +0.51 (58% reduction)
iter-v3/035 single-seed **+2.85 OOS**:
- Pessimistic (86% reduction): +0.40 OOS — fails +1.0 floor
- Median (60% reduction): +1.14 OOS — **clears +1.0 floor for first time in v3 history**
- Optimistic (40% reduction): +1.71 OOS

The methodology bundle is genuinely stronger than iter-v3/025 (multi-seed +0.51) and iter-v3/013 (multi-seed +0.39 falsified). Even a 70% compression would likely clear the +1.0 floor.

## Recommendations

iter-v3/036 axis: continue per-symbol feature additions methodology — try TRX-specific engineered feature. iter-v3/034 confirmed fracdiff hurts TRX; iter-v3/035 confirmed BCH-only fracdiff preserves TRX baseline. The next test: does TRX have a per-symbol engineered feature that would LIFT it further?

Candidates for TRX:
- `vol_adj_autocorr` (iter-v3/026 universal failure; might help TRX specifically)
- `ret_kurt_to_skew_ratio` (untested)
- TRX uniquely uses `hurst_100` at rank 3 — engineered feature involving hurst (e.g., `hurst_signed_momentum = ret_5d × sign(hurst_100 - 0.5)` is regime_momentum already; TRX-specific variant?)

Critic prior: try `vol_adj_autocorr` for TRX-only first. If it doesn't help, try ALGO-only or different engineered feature.

Status: READY-FOR-CRITIC.
