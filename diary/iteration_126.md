# Iteration 126 Diary

**Date**: 2026-04-03
**Type**: EXPLORATION (Model C: LINK standalone screening)
**Model Track**: LINK standalone (single-model)
**Decision**: **NO-MERGE** — standalone screening iteration, but LINK PASSES Gate 3 clearly. Strongest Model C candidate.

## Hypothesis

LINK has fundamentally different dynamics (oracle infrastructure, DeFi dependency) than L1 alts (SOL/AVAX). Testing standalone with ATR labeling 3.5x/1.75x.

## Results — LINK vs Previous Alt Screenings

| Metric | SOL static (123) | SOL ATR (124) | SOL+AVAX (125) | **LINK ATR (126)** |
|--------|-------------------|---------------|----------------|---------------------|
| IS Sharpe | +0.055 | +0.162 | +1.244 | **+0.450** |
| IS WR | 40.6% | 42.6% | 48.7% | **43.2%** |
| IS Trades | 155 | 141 | 234 | **183** |
| IS Net PnL | +9.5% | +31.2% | +274.5% | **+100.5%** |
| OOS Sharpe | -0.12 | +0.47 | -1.57 | **+1.20** |
| OOS WR | 35.4% | 46.9% | 33.0% | **52.4%** |
| OOS Trades | 48 | 32 | 94 | **42** |
| IS/OOS ratio | -2.19 | 2.92 | -1.26 | **2.66** |

## Gate 3 Assessment

| Criterion | Threshold | Result | Status |
|-----------|-----------|--------|--------|
| IS Sharpe > 0 | > 0 | **+0.450** | **PASS** (clear, 3x SOL) |
| IS WR > 33.3% | > 33.3% | 43.2% | **PASS** |
| IS Trades ≥ 100 | ≥ 100 | 183 | **PASS** |

**Gate 3: CLEAR PASS.** LINK is the strongest standalone alt model we've tested.

## Key Findings

1. **LINK has genuine signal.** IS Sharpe +0.45 with 183 trades over 30+ IS months is not noise. IS Net PnL +100.5% is substantial. This is the first alt that shows meaningful standalone profitability.

2. **OOS is encouraging.** OOS Sharpe +1.20 with 52.4% WR is strong. But only 42 trades is thin — need more OOS data or cross-validation to confirm. The IS/OOS ratio of 2.66 (OOS better than IS) is suspicious but could indicate LINK's recent OOS period was favorable.

3. **IS MaxDD 150% is concerning.** Deep IS drawdowns suggest the model has volatile periods. OOS MaxDD 42.3% is much better — possibly because OOS is shorter (11 months vs 30+ IS months).

4. **LINK vs SOL: different signal quality.** SOL's marginal IS +0.16 required ATR labeling just to be positive. LINK's +0.45 is naturally stronger — LINK's price action is more predictable for the model.

5. **OOS trade count (42) is below 50 minimum.** For portfolio inclusion, we'd need more trades. Adding cross-asset features (xbtc_*) or a paired symbol might help.

## What LINK Needs Next

1. **Feature pruning** — 185 features with ~2,750 annual training samples is ratio ~15. Pruning to 45 features (like the meme model) would make ratio ~61. This worked dramatically for meme (OOS doubled from +0.29 to +0.66).

2. **Cross-asset features** — Add xbtc_return_1, xbtc_return_5, xbtc_natr_14 to capture BTC lead-lag. This is free information that should help.

3. **More OOS trades** — 42 is thin. Lowering confidence threshold or adding a paired symbol (e.g., LINK+UNI for DeFi infra) could boost trade count.

## Label Leakage Audit

CV gap = 22 (22 candles × 1 symbol). Correct.

## lgbm.py Code Review

No code changes. LINK auto-discovery found 185 features, same as other alts.

## Gap Quantification

IS WR 43.2%, OOS WR 52.4%. IS PF 1.15, OOS PF 1.45. The model makes money in both periods. IS is weaker because it includes the difficult 2022 bear market.

## Exploration/Exploitation Tracker

Last 10 iterations: [E, X, E, X, X, E, E, E, E, **E**] (iters 117-126)
Exploration rate: 8/10 = 80%

## Research Checklist

- **B** (symbols): LINK standalone Gate 3 screening — CLEAR PASS

## Next Iteration Ideas

**LINK is the first viable Model C candidate. Next steps should exploit this discovery.**

1. **LINK with pruned features** (EXPLOITATION, single-model) — Prune 185→45 features using the meme model's proven approach. This doubled meme OOS Sharpe. Should strengthen LINK's already-positive signal and reduce IS MaxDD.

2. **LINK with cross-asset features** (EXPLOITATION, single-model) — Add xbtc_* features. BTC leads LINK by ~1 candle. This adds genuinely new information.

3. **LINK+UNI pooled DeFi model** (EXPLORATION, single-model) — Pool LINK with UNI for a DeFi infra model. Both are oracle/DEX infrastructure. Unlike SOL+AVAX (which were too correlated), LINK and UNI have different dynamics — test whether pooling helps.

4. **Three-model portfolio test** (MILESTONE, combined run) — Once LINK is refined (feature pruning + cross-asset), run Models A (BTC/ETH) + B (DOGE/SHIB) + C (LINK). This is the rare portfolio milestone run. Only do this after LINK standalone is optimized.
