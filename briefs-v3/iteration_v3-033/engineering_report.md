# Engineering Report — iter-v3/033

## Status: READY-FOR-CRITIC

Wall-clock 0.43h (26 min). NEGATIVE — VET dragged portfolio (-19.23 OOS, 27.8% WR).

## Hypothesis-Implementation Alignment

ADD VETUSDT to V3_MODELS (4→5); REQUIRED_GAP 88→110; ITERATION_LABEL=v3-033. KEEP regime_momentum_signed_5d, LDO ATR (1.5, 0.75), V3_FEATURE_COLUMNS=14.

## Headline Metrics

| Metric | Value | vs iter-v3/032 anchor (+0.2360/+1.9338) |
|--------|-------|------------------------------------------|
| IS monthly Sharpe | +0.1147 | Δ -0.12 |
| OOS monthly Sharpe | +1.6096 | Δ -0.32 |
| Bundle OOS trades | **147** | +18 (cleared 130 floor) |
| IS Trades | 337 | +81 |
| OOS MaxDD | 27.25% | similar |
| IS MaxDD | 60.08% | +10.8pp (worst-yet in v3) |

## Per-Symbol OOS

| Symbol | weighted_pnl | Trades | WR | vs iter-v3/032 |
|--------|--------------|--------|-----|----------------|
| TRX | +29.24 | 46 | 52.2% | bit-identical |
| ALGO | +20.87 | 25 | 40.0% | bit-identical |
| BCH | +10.75 | 38 | 39.5% | bit-identical |
| LDO | +3.98 | 20 | 35.0% | bit-identical |
| **VET** | **-19.23** | 18 | **27.8%** | new — DRAG |

VET dragged -19.23 (drives total OOS down from sum of other 4 = 64.84 to 45.61). VET 27.8% WR is structurally bad.

## Hypothesis FALSIFIED — Methodology Refinement Needed

The iter-v3/029 ALGO success (+20.87 OOS) suggested per-symbol-feature-signature alignment was the key methodology. iter-v3/033 VET failure shows alignment is NECESSARY but NOT SUFFICIENT:
- ALGO alignment_score 0.4642 → success (+20.87 OOS, 40% WR)
- VET alignment_score 0.5176 → failure (-19.23 OOS, 27.8% WR)

Higher alignment did NOT predict better performance. VET has different return regime that EDA couldn't capture.

**Methodology lesson**: feature-signature alignment is a NECESSARY filter but cannot replace empirical out-of-sample backtest validation. Symbol expansion remains a high-risk axis.

## §4.4 Classification

PATH B (NEGATIVE-DILUTION) fires: VET drags -19.23 OOS PnL. Verdict: **EXPLORATION-NEGATIVE** (clean).

## Recommendations

iter-v3/034: DROP VET (revert V3_MODELS 5→4; REQUIRED_GAP 110→88) + ADD `fracdiff_d05_close` (López de Prado AFML Ch. 5 fractional differentiation at d=0.5; preserves memory while making stationary; ENGINEERED feature mandated in v3 skill iter-v3/001 scope but never implemented).

Rationale:
- IS Sharpe is the bottleneck (+0.24 at iter-v3/032; needs +0.76 to clear +1.0 floor)
- Different engineered feature with NEW MECHANISM (fracdiff = memory preservation) tests stacking compatibility
- iter-v3/026 (vol_adj_autocorr stacking on regime_momentum) failed at 3-symbol universe; 4-symbol + LDO ATR may have different stacking dynamics
- Fracdiff is from the v3 skill's original methodology spec (iter-v3/001 deferred it)

V3_FEATURE_COLUMNS 14 → 15. Single-axis: ADD fracdiff. Predicted PATH A if IS lift; PATH B if INERT (rank 14/15+); PATH C if regime_momentum gets crowded out.

Status: READY-FOR-CRITIC.
