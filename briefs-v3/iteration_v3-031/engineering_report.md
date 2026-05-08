# Engineering Report — iter-v3/031

## Status: READY-FOR-CRITIC

Wall-clock 0.28h (17 min). NEGATIVE-MECHANICAL-INVERTED — drop-LDO hurt both IS (-0.51) and OOS (-0.17).

## Hypothesis FALSIFIED

Predicted: drop-LDO removes -3.07 OOS drag mechanically (per iter-v3/013 drop-MKR PROMISING-MECHANICAL precedent). Expected IS [+0.85, +1.05] / OOS [+1.85, +2.10].

Observed: IS +0.28 (Δ -0.51 vs anchor +0.79); OOS +1.60 (Δ -0.17). Both axes WORSE not better.

Mechanism analysis:
- LDO IS contribution at iter-v3/029: +40.03 weighted_pnl (positive — LDO actually fit IS aggregate well)
- LDO OOS contribution at iter-v3/029: -3.07 weighted_pnl (small negative)
- Net effect of dropping LDO: -40.03 IS (large loss), +3.07 OOS (small gain). Sharpe collapses on IS axis.

**Critical lesson**: chronic OOS-negative ≠ "should be dropped" if symbol contributes positive IS. The iter-v3/013 drop-MKR precedent only transfers when the chronic-negative symbol is BOTH IS-negative AND OOS-negative (true drag both ways). MKR was -23% IS / -25% OOS. LDO is +40% IS / -3% OOS — a different pattern (IS-overfit, not drag).

## Headline Metrics

| Metric | Value | vs iter-v3/029 anchor (+0.7926/+1.7653) |
|--------|-------|------------------------------------------|
| IS monthly Sharpe | +0.2778 | Δ -0.51 |
| OOS monthly Sharpe | +1.5991 | Δ -0.17 |
| IS Trades | 242 | -15 (LDO removed) |
| OOS Trades | 109 | -11 (LDO removed) |
| IS MaxDD | 47.38% | +12.66pp (worse — IS profile less smooth) |
| OOS MaxDD | 21.52% | -2.33pp (slight improvement) |
| DSR | 0.0 | EXPLORATION artifact |
| PBO mean | 0.0957 | PASS |
| PSR | 1.0 | EXPLORATION saturation |
| n_eff | 19 | consistent |

## Per-Symbol — BCH/TRX/ALGO bit-identical to iter-v3/029

| Symbol | weighted_pnl OOS | Trades | WR | vs iter-v3/029 |
|--------|------------------|--------|-----|----------------|
| TRX | +29.24 | 46 | 52.2% | bit-identical |
| ALGO | +20.87 | 25 | 40.0% | bit-identical |
| BCH | +10.75 | 38 | 39.5% | bit-identical |

Per-symbol Optuna independence confirmed. The result is a clean mechanical experiment.

## §4.4 Classification

PATH C fires on IS axis (Δ -0.51 ≪ -0.10). Verdict: **EXPLORATION-NEGATIVE (clean — counter-intuitive)**.

The "drop chronically-negative-symbol" heuristic FAILED because LDO is IS-positive / OOS-mildly-negative, not a true drag. Methodology lesson encoded.

## Recommendations

iter-v3/032 axis options:

1. **RESTORE LDO + per-symbol ATR multipliers**: address LDO's regime mismatch at LABELING layer (different ATR multipliers for LDO than BCH/TRX/ALGO). LDO has different volatility profile; ATR(2.0, 1.0) might not fit. Single-axis: per-symbol labeling parameters.

2. **RESTORE LDO + try different engineered feature**: a feature that LDO uses (e.g., btc_ret_14d which LDO ranks 6 vs others 14). Compose: `btc_funding_zscore_30 × sym_vs_btc_ret_7d` or similar.

3. **RESTORE LDO + feature selection at portfolio level**: drop the bottom-2 importance features universally (parsimony). 14 → 12 features. Tests whether the 14-feature stack has noise features.

Critic prior: **option 1 (per-symbol ATR multipliers)**. Direct response to user's "features per symbol" directive extended to LABELING. Tests whether LDO's regime mismatch is at the label level rather than feature level. New code path but architecturally similar to V3_FEATURES_PER_SYMBOL.

Status: READY-FOR-CRITIC.
