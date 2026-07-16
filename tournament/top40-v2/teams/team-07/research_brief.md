# Team 07 pivot 02: two-tape relative-rank durability

Status: statically authored and organizer-validated as a prospective no-control mechanism pivot;
unregistered and unevaluated.

## Why the first pivot family is terminal

The exact no-control `t07-market-state-relative-ensemble-v1-base` result was approximately flat
before costs and negative after them. Net Sharpe was +0.0153, annualized return was -0.97%,
doubled-cost Sharpe was -0.4928, maximum drawdown was 25.43%, and only half of quarters were
positive. Bull Sharpe was +0.2193, but bear and chop Sharpe were -0.7394 and -0.6013. It generated
15,763 trades. The core therefore failed ordinary-return, doubled-cost, bear, chop, quarter, and
robustness requirements. Its controls, neighbors, and ablations cannot repair that evidence.

## New mechanism

This pivot removes the failed common directional state, residual momentum/reversal blend, funding
carry, and 48-hour construction. For each of 126 completed 8-hour returns, it rank-transforms every
eligible coin against the same point-in-time pure-crypto cross-section. These same-bar ranks measure
relative leadership without relying on return scale, beta estimates, or a fitted market model.

The median cross-sectional return classifies each completed bar as common-market up or down. For
each coin, the strategy separately averages its ranks on up-tape and down-tape bars. Same-sign tape
means receive the signed smaller magnitude, so a long forecast must have held up during both market
directions and a short forecast must have lagged during both. Opposite-sign tape means are shrunk to
15% of their average. The strategy also computes mean rank in three non-overlapping 42-bar blocks;
their median is a temporal durability estimate. A fixed 70/30 tape/block combination is multiplied
by squared sign agreement and divided by tape-plus-block dispersion. The final scores are
cross-sectionally rank-transformed once more.

The returned A5 dictionary alone selects the highest and lowest one-fifth, with at least eight
coins per side. The book is exactly dollar neutral, has 0.36 gross, caps each coin at 0.025, and
rebalances every 21 bars (seven days). The slower horizon is part of the alpha construction and
directly targets the failed parent's doubled-cost weakness; no turnover control or other risk
overlay is enabled.

## Expected regime roles

- Bull: longs are coins that consistently outranked peers on both market-up and market-down bars;
  shorts are persistent relative laggards. There is no positive market beta requirement.
- Bear: the same dollar-neutral relative ranking seeks coins resilient on down bars and shorts
  coins that lag even when the common tape is already weak.
- Chop: agreement across three 42-bar blocks suppresses one-window winners and one-bar reversal
  noise; broad neutral sleeves avoid depending on market direction.
- Stress: per-bar ranks, the smaller-magnitude cross-tape core, broad sleeves, low gross, and coin
  caps reduce outlier and beta concentration, while profitability remains an empirical gate.

## Causal and universe boundary

The strategy accepts exactly 127 completed close observations at exact 8-hour opens to form 126
returns. It uses only `bars.open_time`, `bars.close`, the decision time, and the organizer-supplied
point-in-time eligible-symbol list. Funding, current executable open, bar high/low, volume,
auxiliary data, positions, fills, equity, PnL, drawdown, evaluator actions, private data, and future
rows are unused. Amendment 0006 remains the only pure-crypto universe authority; Team 07 performs
no symbol classification.

## Falsifier and tournament discipline

Reject this family unless net Sharpe is at least `0.75`, annualized return is positive, Calmar is
at least `0.40`, maximum drawdown is at most `0.30`, doubled-cost Sharpe is at least `0.35`,
doubled-cost return is positive, and trial-adjusted probability positive is at least `0.90`. Also
require at least four profitable folds, positive-quarter fraction at least `0.55`, worst-regime
Sharpe at least `-0.25`, at least three positive regime Sharpes, positive bull/bear/chop returns and
Sharpes, positive long-bull, short-bear, and combined-chop attribution, active sleeves, complete A5
coverage and IC gates, and positive-PnL concentration at most `0.40`. No subthreshold core is
eligible for controls, neighbors, diagnostics, or submission. Failure of this second/final pivot
means Team 07 is DNF.
