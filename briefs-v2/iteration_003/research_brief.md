# Iteration v2/003 Research Brief

**Type**: EXPLOITATION (single-symbol ATR multiplier specialization)
**Track**: v2 — diversification arm
**Parent baseline**: iter-v2/002 (OOS Sharpe +1.17, weighted, seed 42)
**Date**: 2026-04-13
**Researcher**: QR

## Section 0: Data Split

```
OOS_CUTOFF_DATE = 2025-03-24    ← FIXED. NEVER CHANGES. NOT NEGOTIABLE.
```

## Motivation

iter-v2/002 established the first v2 baseline (OOS Sharpe +1.17) but with
a known concentration caveat: XRP drove 74% of signed OOS PnL because
DOGE was a −9.33% drag. The iter-v2/002 diary flagged the DOGE fix as
Priority 1:

> "Specialize DOGE ATR multipliers to something wider than 2.9/1.45. Meme
> coins have larger NATR and need more breathing room. Try 4.0/2.0 or
> 5.0/2.5 on DOGE only (Model E). Keep SOL and XRP on 2.9/1.45."

iter-v2/003 implements option 1: **DOGE ATR multipliers widened from 2.9/1.45
to 4.0/2.0**, SOL and XRP unchanged. This is a per-model parameter change
— the runner now stores `(atr_tp, atr_sl)` per V2_MODELS entry and passes
them through `_build_model`.

## Hypothesis

Wider TP/SL barriers on DOGE (38% wider than 2.9/1.45) should give DOGE's
meme-dynamics more breathing room, reducing the 60% SL rate seen in
iter-v2/002 and raising DOGE's per-trade expectancy from negative toward
zero or positive. The concentration caveat flagged in iter-v2/002 would
mechanically improve as DOGE's weighted PnL moves toward non-negative.

Quantitative prediction (pre-registered):

- DOGE OOS raw PnL: from −24.02% → ≥ 0% (ideally +5 to +20%)
- DOGE OOS WR: from 38.3% → ≥ 40%
- DOGE OOS SL rate: from 60% → ~45%
- Overall weighted OOS Sharpe: ≥ +1.17 (baseline level, since DOGE stops
  being a drag and the other two symbols are unchanged)
- Signed concentration (XRP share of signed PnL): from 74% → ≤ 65%
- v2-v1 correlation: essentially unchanged (DOGE is still in the portfolio)

## Failure-mode prediction (pre-registered)

Most likely way to fail: **the wider barriers improve IS DOGE performance
but don't generalize to OOS** — classic IS-overfit pattern. If that happens,
DOGE IS raw PnL would rise significantly (e.g., +56% → +80%+) while DOGE
OOS would stay negative or get worse. The signal would be a DOGE IS WR
jump of +5pp or more with flat/worse OOS WR.

The v1 skill explicitly warns about this pattern (§Labeling Analysis
C.5): "Timeout sensitivity: do NOT change by less than 2x. Iter 116
proved that reducing timeout from 7d to 5d caused IS Sharpe +1.71 while
OOS collapsed to −0.04." The DOGE multiplier change is not a timeout
change, but the principle applies to small parameter changes that shift
label distributions.

## Configuration (one variable changed from iter-v2/002)

| Setting | iter-v2/002 | iter-v2/003 | Changed? |
|---|---|---|---|
| DOGE ATR multipliers | 2.9 / 1.45 | **4.0 / 2.0** | **Yes** |
| SOL ATR multipliers | 2.9 / 1.45 | 2.9 / 1.45 | — |
| XRP ATR multipliers | 2.9 / 1.45 | 2.9 / 1.45 | — |
| Features, Optuna trials, gates, seed | Same | Same | — |
| `RiskV2Wrapper._vol_scale` | inverted (iter-v2/002) | inverted | — |

## Success Criteria (inherits iter-v2/002 baseline)

Primary: OOS Sharpe > +1.17 (current v2 baseline).

Hard constraints (all must pass):

- ≥ 7/10 seeds profitable
- OOS PF > 1.1
- OOS trades ≥ 50
- No single symbol > 50% of OOS PnL (no override allowed — override was
  one-time for iter-v2/002)
- DSR > +1.0 (tighter than iter-v2/001 relaxed level because we have a
  baseline now)
- v2-v1 OOS correlation < 0.80
- IS/OOS Sharpe ratio > 0.5

## Section 6: Risk Management Design

### 6.1 Active primitives
Unchanged from iter-v2/002. Same four MVP gates. Same `_vol_scale` formula.

### 6.2 Expected fire rates
Unchanged from iter-v2/002. The DOGE multiplier change affects labeling
(TP/SL barrier placement) not gate firing.

### 6.3 Pre-registered failure-mode prediction
"The most likely way iter-v2/003 fails is IS-overfitting: DOGE IS raw
PnL jumps substantially (e.g., +55.97% → +80%+) while DOGE OOS stays
negative or worsens. The signal would be a DOGE IS WR rise of +5pp or
more with flat/worse OOS WR."

### 6.4-6.5
Unchanged from iter-v2/002.
