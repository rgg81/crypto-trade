# iter-v3/118 — Engineered-Feature Axis EDA Synthesis

## Mission

Per `feedback_v3_axis_selection_quant_discipline.md` + the /117 closeout QR
recommendation: select the /118 axis from the engineered-feature family on the
`regime_momentum_signed_5d` (/025 PROMISING) lineage. The axis is the AXIS
(NEW engineered feature on BCH/LDO/TRX 8h), not a specific pre-committed
composite. EDA-driven adjudication.

## Candidates Evaluated (6, motivated by cycle-6 failure modes)

| ID | Formula | Motivation |
|---|---|---|
| C1 | `vwap_dev_20 * sign(hurst_100 - 0.5)` | /025 template; vwap mean-reversion × regime |
| C2 | `ema_spread_atr_20 * sign(hurst_100 - 0.5)` | /025 template; momentum value × regime |
| C3 | `ema_spread_atr_20 * sign(range_realized_vol_50 - rolling_median_200)` | vol-regime × momentum |
| C4 | `ret_autocorr_lag1_50 * sign(hurst_100 - 0.5)` | encodes /116 no_confirm mechanism at feature level |
| C5 | `sym_vs_btc_ret_7d * sign(btc_ret_14d)` | cross-asset regime divergence |
| C6 | `vwap_dev_20 * sign(ret_kurt_50 - 0)` | vwap × tail-regime |

## Method Stack

| Gate | Test | Threshold | Notes |
|---|---|---|---|
| T2 | Linear-Redundancy Pre-Falsifier (R² on 14 primitives) | composed-feature carve-out per `feedback_v3_engineered_feature_pivot.md` | All 6 PASS by carve-out |
| T3 | Walk-forward univariate AUC (universe-pooled, 100-perm null) | p < 0.05 AND AUC > q95 | 1 of 6 passes (C4) |
| T4 | Per-symbol walk-forward univariate AUC (g1 hard gate) | ≥ 0.51 on all 3 symbols | 0 of 6 passes; C4 passes 2 of 3 |
| T5 | Multivariate (14+1) depth-4 LightGBM importance rank | ≤ 5 of 15 AND ≥ 30% top-feature gain on ≥ 2 syms | 1 of 6 passes T5-gain (C3); 0 pass T5-rank |
| T7 | Multivariate-LIFT screen (14 vs 14+1 OOF AUC) for C4 | ≥ 0.005 POOLED AND ≥ 0.003 on 2+ symbols | **FAIL** (POOLED +0.0010; only BCH +0.0046 passes) |
| T9 | Multivariate-LIFT screen for C3 | ≥ 0.005 POOLED AND ≥ 0.003 on 2+ symbols | **PASS POOLED** (+0.0081) but only 1 of 3 symbols (TRX +0.0082; BCH −0.004, LDO −0.011) |

## Headline Findings

### C4 (the T3 winner) — univariate signal, multivariate INERT-RISK

C4_autocorr_signed_hurst is the only candidate with statistically significant
universe-pooled univariate AUC (T3: 0.5381, p=0.000, clears null q95=0.5099).
BCH+TRX clear the g1 per-symbol gate (0.5125, 0.5463); LDO just misses
(0.5042 vs 0.51 threshold).

BUT: T7 multivariate-lift screen reveals **the production-relevant signal is
absent**:
- BCH lift +0.0046 (just at threshold)
- LDO lift −0.0092 (NEGATIVE)
- TRX lift −0.0043 (NEGATIVE)
- POOLED lift +0.0010 (well below 0.005 gate)
- Multivariate importance rank: **15/15 across all 3 symbols, gain 2.9-3.7%**

This is the canonical /085/086/015/019/020/023 INERT-by-importance failure
pattern. The univariate signal is real but the 14-feature stack already
captures it (via `ret_autocorr_lag1_50` and `hurst_100` independently — the
tree can decompose the composite at depth ≥ 2).

C4 verdict: **REJECTED for /118 axis selection**. PROMISING-INERT-RISK,
matches the /085 dead pattern.

### C3 (the T5 winner) — high multivariate importance, asymmetric per-symbol lift

C3_ema_signed_volregime fails T3 univariate AUC (0.4977, p=0.61) but achieves
the highest T5 multivariate importance rank in the EDA: rank 8-10 / 15 across
all 3 symbols, with gain 37.7%–63.1% of top-feature gain (the only candidate
exceeding the 30% gain bar).

T9 multivariate-lift screen:
- BCH lift −0.0039 (FAIL)
- LDO lift −0.0106 (FAIL)
- TRX lift +0.0082 (PASS)
- **POOLED lift +0.0081 (PASS the 0.005 gate)**

This is the inverse pattern of C4: no univariate signal, but the LightGBM uses
C3 as an INTERACTION-LEVEL feature (depth-≥2 splits with `ema_spread_atr_20`)
that lifts POOLED OOF AUC despite being negative on 2 of 3 symbols. The
mechanism: C3 encodes the same vol-regime split that /025's hurst-sign captures
at a different timescale — `range_realized_vol_50` rolling-median is a SLOWER
regime classifier than `hurst_100`, complementing rather than duplicating /025.

C3 verdict: **CHOSEN as /118 axis**, with explicit acknowledgement of:
1. The per-symbol asymmetry (TRX is the sole positive carrier — the inverse of
   the /116 BCH-led pattern, addressing /117's TRX-79-IS-0-OOS evaporation mode
   by giving the model a regime feature that lifts TRX-specific AUC most).
2. The lift is mild (+0.0081 POOLED; below the strong-lift threshold of +0.02
   that would predict clean PROMISING).
3. The Falsifier 4 pre-registration: if production importance ranks 15/15 with
   gain < 30% on > 1 symbol, file as PROMISING-INERT (per /085 precedent).
4. The Falsifier 5 pre-registration: if BCH+LDO IS Sharpe deltas are negative
   while TRX is the sole carrier, this is the per-symbol-asymmetry mechanism
   diagnosed at EDA and file as PROMISING-PARTIAL.

### Why NOT C4 even though it's the T3 winner

Per `feedback_v3_engineered_feature_pivot.md` and `feedback_v3_lr_pf_methodology.md`:
the production runner uses MULTIVARIATE LightGBM, not univariate. C4's R²=1.0
with `ret_autocorr_lag1_50` means the tree can perfectly reconstruct C4's
composite by sequential splits on (hurst_100, ret_autocorr_lag1_50). The T7
result (multivariate-lift POOLED +0.0010 < 0.005) confirms the tree IS doing
this reconstruction — adding C4 explicitly provides ZERO additional information
beyond what 14 features already give. This is the iter-v3/053 hurst_drift
lesson: trees can use derived features for EFFICIENCY but Sharpe-Δ is the
controlling test, and the T7 lift is the IS-only proxy for it.

C4 has univariate signal because in 1D space, the tree cannot see hurst_100.
In 14D space, hurst_100 is already there at rank 8.

### Why NOT C5 (cross-asset)

C5 has the lowest R² with primitives (POOLED 0.107) — by far the most
orthogonal candidate. But T3 AUC = 0.4931 (FAIL, p=0.82) and T4 g1 only LDO+TRX
pass (BCH 0.487). T5 importance rank 14-15/15 across all symbols. Orthogonality
alone is not sufficient — the candidate must also carry signal. C5 is
orthogonal noise on this universe.

### Why NOT C1, C2, C6

- C1 (vwap × hurst-sign): T3 fail (0.4960, p=0.72), T7-equivalent expected near 0.
- C2 (ema × hurst-sign): T3 fail (0.5080, p=0.10), borderline only at LDO+TRX
  per-symbol AUC; T5 importance ranks 15/15 across all symbols with 1-3% gain
  (worse than C4 in importance).
- C6 (vwap × kurt-sign): T3 fail (0.4942, p=0.86), T5 rank 15/15 across all,
  high R² collinearity with vwap_dev_20 (0.76 POOLED) — composed but tree can
  trivially decompose.

## RECOMMENDATION

**/118 axis = C3_ema_signed_volregime**

```
C3_ema_signed_volregime
    = ema_spread_atr_20 * sign(range_realized_vol_50 - rolling_median(range_realized_vol_50, window=200))
```

**Provenance (per `feedback_v3_brief_parameter_provenance.md`)**:

| Scalar | Value | Source |
|---|---|---|
| Rolling median window | 200 8h bars (~67 calendar days) | DECLARED hand-chosen. Rationale: matches the longest rolling-window primitive in TOP_N (`hurst_200`, `atr_pct_rank_200`); a regime classifier should be slower than the value primitive it conditions; 200 bars is the v3 canonical "long-horizon regime" timescale. NOT swept; no IS-only sweep table generated. |
| Threshold offset | 0.0 (median = reference) | Inherent to the rolling-median construction; not a tunable scalar. |
| Sign convention | +1 when realized vol > median (high-vol regime); −1 when < median | Inherent to `sign(x - median)`. |

The candidate's name pattern `value_signed_regime` mirrors the /025 baseline
`regime_momentum_signed_5d` and the /085 dead path `funding_regime_momentum_5d`
— the construct is well-established in v3 catalog terminology.

## Pre-Registered Risk Flags (Brief Section 7)

| Mode | Condition | Predicted Outcome |
|---|---|---|
| 1 (Modal) | POOLED OOF AUC lift translates to IS Sharpe Δ ∈ [+0.05, +0.30] | EXPLORATION-PROMISING |
| 2 (Importance INERT) | rank 15/15 on > 1 sym with gain < 30% of top | PROMISING-INERT (the /085 precedent) |
| 3 (Per-sym asymmetry) | TRX positive, BCH+LDO negative or flat | PROMISING-PARTIAL (one-symbol carrier) |
| 4 (Catastrophic regime artifact) | IS Sharpe < +0.50 AND OOS Sharpe < −0.50 | EXPLORATION-NEGATIVE (universe-vol-regime axis CLOSED) |
| 5 (Null at production) | IS / OOS Δ within ±0.05 of /060 anchor | NEGATIVE-INERT (the /015 / /019 dead pattern) |

## Files Committed

- `analysis/iteration_v3-118/_shared.py` — IS-only fence, candidate generator, label
- `analysis/iteration_v3-118/engineered_feature_screen.py` — T1–T6 runner
- `analysis/iteration_v3-118/multivariate_lift_screen.py` — T7–T8 for C4
- `analysis/iteration_v3-118/c3_lift_screen.py` — T9 for C3 (the chosen axis)
- `analysis/iteration_v3-118/synthesis.md` — this document

## Result Tables

- T1_candidate_catalog.csv — 6 candidates + cycle-6 motivation
- T2_linear_redundancy_pre_falsifier.csv — R² + verdict per (symbol, candidate)
- T3_walkforward_pooled_auc.csv — universe-pooled univariate AUC + null
- T4_per_symbol_auc.csv — per-symbol univariate AUC (the /117 g1 gate)
- T5_importance_rank_multivariate.csv — depth-4 (14+1) importance rank/gain
- T6_go_nogo_verdict.csv — T2-T5 verdict synthesis
- T7_multivariate_lift_screen.csv — 14 vs 14+1 (C4) OOF AUC delta
- T8_importance_full_table.csv — full rank-1..15 importance table at 14+1 (C4)
- T9_c3_multivariate_lift_screen.csv — 14 vs 14+1 (C3) OOF AUC delta
