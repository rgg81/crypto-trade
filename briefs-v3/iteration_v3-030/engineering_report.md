# Engineering Report — iter-v3/030

## Status: READY-FOR-CRITIC

Wall-clock 0.32h (19 min). NEGATIVE result — per-symbol feature subset for LDO did NOT help; LDO got worse.

## Hypothesis-Implementation Alignment

ADD V3_FEATURES_PER_SYMBOL dict + features_for_symbol helper. LDO gets 7-feature subset (top-7 from iter-v3/028 multi-seed). BCH+TRX+ALGO unchanged (14 features). ITERATION_LABEL=v3-030.

## Reproducibility Stamps

Setup `54d9075`, gate `5a661fc`, brief `5ea6099`, analysis `36aaacd`.

## Headline Metrics

| Metric | Value | vs iter-v3/029 ref (+0.7926/+1.7653) |
|--------|-------|--------------------------------------|
| IS monthly Sharpe | **+0.0469** | Δ -0.75 (collapse) |
| OOS monthly Sharpe | **+1.0611** | Δ -0.70 |
| IS MaxDD | **70.55%** | worst-ever in v3 (+35.8pp from anchor) |
| OOS MaxDD | 25.18% | similar |
| IS Trades | 265 | +8 |
| OOS Trades | 124 | +4 |

## Per-Symbol OOS — LDO got WORSE

| Symbol | weighted_pnl | Trades | WR | vs iter-v3/029 |
|--------|--------------|--------|-----|----------------|
| TRX | +29.24 | 46 | 52.2% | **bit-identical** |
| ALGO | +20.87 | 25 | 40.0% | **bit-identical** |
| BCH | +10.75 | 38 | 39.5% | **bit-identical** |
| LDO | **-29.99** | 15 | **26.7%** | **WORSE** (-26.92 vs -3.07) |

BCH/TRX/ALGO frozen baseline confirmed (only LDO config changed; only LDO trajectory changed).

## Hypothesis FALSIFIED

The hypothesis was: "LDO trained on 14 features overfits noise on small training sample → tighter 7-feature subset reduces overfit → LDO contribution lifts."

Observation: LDO with 7 features performs WORSE (-29.99 vs -3.07 OOS PnL), with MORE trades (15 vs 11) at LOWER WR (26.7% vs 36.4%).

Interpretation: the 7-feature subset gave Optuna fewer dimensions to find IS-fit configurations, but this caused the model to lock onto IS-noise patterns that produced more aggressive trade signals, resulting in MORE bad trades. The IS Sharpe collapse to 0.05 with 70% IS MaxDD is the smoking gun — IS overfit is WORSE not better with fewer features.

LDO is a STRUCTURAL problem (small training sample 31 IS months, different return regime than BCH/TRX/ALGO), not an overfit-from-too-many-features problem. Feature reduction doesn't address structural mismatch.

## §4.4 Classification

PATH C fires: IS Δ -0.75 ≪ -0.10 threshold. The 22× IS/OOS daily Sharpe ratio is the same suspicious-OOS pattern as iter-v3/026/027 — OOS lift is single-seed lottery on top of broken IS.

**Verdict: EXPLORATION-NEGATIVE (clean)**.

## Critical Conclusion

**LDO must be addressed structurally, not feature-engineered.** Two paths:

1. **Drop LDO** (iter-v3/013 PROMISING-MECHANICAL precedent — drop chronically-underperforming symbol). Mechanical lift expected.

2. **LDO-specific labeling** (different ATR multipliers tuned to LDO's volatility regime). More complex; addresses the regime mismatch hypothesis.

Critic prior: **option 1 (drop LDO)** for iter-v3/031. Mechanical, clean, validated by iter-v3/013 precedent. Drop-MKR worked the same way (chronic OOS-negative across 5+ iterations → universe shrink → +1.11 OOS lift mechanically).

LDO trajectory:
- iter-v3/018 multi-seed: -22.05 OOS (21.4% WR, 14 trades)
- iter-v3/020-027 single-seed frozen: -8.93 OOS (38.5% WR, 13 trades)  
- iter-v3/029 with ALGO: -3.07 OOS (36.4% WR, 11 trades)
- iter-v3/030 with 7-feat subset: -29.99 OOS (26.7% WR, 15 trades)

LDO is **9 of 9** OOS-negative across 9 consecutive iterations. The MKR threshold (5 consecutive) was crossed long ago. Drop-LDO is overdue.

## Recommendations

iter-v3/031 axis: **DROP LDOUSDT** from V3_MODELS.
- V3_MODELS: 4 → 3 (BCH+TRX+ALGO)
- REQUIRED_GAP: 88 → 66
- KEEP V3_FEATURE_COLUMNS=14 (with regime_momentum)
- KEEP V3_FEATURES_PER_SYMBOL dict but only LDO entry — irrelevant since LDO dropped (or remove the dict entirely for cleanliness)
- Predicted: BCH/TRX/ALGO trades bit-identical to iter-v3/029; portfolio totals shift by +29.99 mechanical (LDO drag removed)
- Expected OOS Sharpe: ~iter-v3/029 (+1.77) preserved or slightly lifted by removing LDO drag

Status: READY-FOR-CRITIC.
