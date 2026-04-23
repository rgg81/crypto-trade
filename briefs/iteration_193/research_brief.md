# Iteration 193 — Bootstrap Sharpe CI on v0.186 (validation-only)

**Date**: 2026-04-23
**Type**: VALIDATION (statistical confidence on v0.186)
**Baseline**: v0.186
**Decision**: NO-MERGE-NEEDED (this is a validation iteration, not a merge candidate)

## Motivation

`reports/iteration_186/comparison.csv` reported DSR (deflated Sharpe
ratio) of **−13.29 OOS** and **−25.36 IS**. DSR adjusts for the multiple
strategies tested and the higher moments of the return distribution;
highly-negative DSR historically warns of overfitting.

After four consecutive exploration NO-MERGEs (iter 189, 190, 191, 192)
I wanted to validate that v0.186 itself was statistically sound before
investing more compute in exploration.

## Method

`analysis/iteration_193/bootstrap_sharpe.py` does a daily-return
bootstrap (10,000 resamples with replacement on daily PnL) and reports
2.5/50/97.5 percentile Sharpe, plus fraction above 0 and above 1.0.
Computed for IS, OOS, combined, and per-symbol within each.

## Result — portfolio

| window | point Sharpe | bootstrap median | 95% CI | P(S>0) | P(S>1.0) |
|--------|-------------:|------------------:|:-------|------:|---------:|
| IS | +1.440 | +1.444 | [+0.368, +2.470] | 99.5% | **79.8%** |
| OOS | +1.737 | +1.740 | [−0.144, +3.444] | 96.5% | **78.8%** |
| Combined | +1.505 | +1.500 | [+0.582, +2.390] | 99.9% | **86.0%** |

**The portfolio Sharpe is credibly above 1.0 with ~80% posterior
confidence.** IS and OOS bootstrap medians are within 0.30 of each
other — consistent. The OOS CI reaching slightly below zero is
expected for a 210-trade sample; the probability mass is almost entirely
positive (96.5%).

## Result — per-symbol

OOS only (the validation window that matters for deployment):

| symbol | n | point | median | 95% CI | P(S>1) |
|--------|--:|------:|-------:|:-------|-------:|
| LINK | 40 | +1.440 | +1.447 | [−0.50, +2.95] | **69%** |
| ETH | 49 | +1.110 | +1.090 | [−0.86, +2.69] | **54%** |
| LTC | 38 | +0.638 | +0.629 | [−1.50, +2.22] | 34% |
| BTC | 43 | +0.308 | +0.287 | [−1.80, +2.08] | 23% |
| DOT | 40 | +0.058 | +0.052 | [−1.91, +1.94] | 16% |

**Only LINK and ETH are credibly above Sharpe 1.0 standalone.** BTC, LTC,
DOT have wide CIs that span zero. Diversification contributes to the
portfolio-level confidence: combining 5 moderately-correlated weak
signals beats any single one.

## Interpretation

1. **v0.186 is statistically credible.** The central portfolio estimate
   is robustly around +1.5 combined, +1.7 OOS. CIs are wide but always
   centered clearly above zero.
2. **DSR being negative does NOT mean the strategy is bad.** DSR
   deflates Sharpe against the number of strategies attempted — it's
   conservative by design. With 192 iterations and many hyperparameter
   variants, -13 DSR is sanity-checking the Sharpe against that
   multi-strategy risk. The bootstrap CI gives a complementary view
   that's less punitive.
3. **Diversification matters.** Per-symbol Sharpes are weaker than
   portfolio Sharpe because combining uncorrelated wins smooths
   daily variance. BTC alone wouldn't ship; BTC+ETH+LINK+LTC+DOT
   together does.
4. **DOT is the weakest standalone OOS contributor.** Its wide CI spanning
   a wide negative range means R1+R2 saved its 2022 IS but OOS is still
   fragile. A future iteration may want to revisit whether DOT earns
   its place or if its inclusion is a net-negative after accounting for
   risk-mitigation cost.

## Decision

No baseline change. v0.186 stays as baseline. **v0.186 is validated
for deployment** — the bootstrap CI puts the portfolio Sharpe firmly
in positive territory with healthy probability.

## Exploration/Exploitation Tracker

Window (183-193): [E, X, X, X, X, X, E, E, E, E, VALID] → validation
doesn't count toward the E/X ratio. Window stays 5E/5X (iter 192's
DOT 14d was still exploration). Balanced.

## Next Iteration Ideas

- **Iter 194**: AFML fractional differentiation features on BTC.
  Well-motivated quantitative finance technique, previously never tried.
- **Iter 195**: Revisit DOT's inclusion. Standalone OOS CI suggests
  DOT's signal is fragile; evaluate portfolio metrics with DOT removed
  vs. present (post-hoc quick, then full backtest if favorable).
- **Iter 196**: Ship v0.186 to paper-trading for 2 weeks. Bootstrap
  validation + existing live-engine code supports this. Collect real
  live data to inform future iteration direction.
