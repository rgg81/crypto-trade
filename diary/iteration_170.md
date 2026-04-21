# Iteration 170 Diary

**Date**: 2026-04-22
**Type**: EXPLORATION (AAVE Gate 3 screen — DeFi sector)
**Decision**: **NO-MERGE (EARLY STOP)** — AAVE fails year-1; 4-of-5 recent candidates rejected

## Gate 3 scorecard for AAVE

| Criterion | Threshold | Actual | Pass |
|---|---|---|:-:|
| IS Sharpe | > 0 | +0.06 | ✓ barely |
| IS WR | > 33.3% | 35.7% | ✓ |
| IS trades | ≥ 100 | 14 | ✗ |
| Year-1 PnL | ≥ 0 | −17.8% | ✗ |

## Candidate screening summary (5 iterations)

| Candidate | Sector | Iter | Year-1 PnL | IS Sharpe @ stop | Elapsed | Outcome |
|---|---|---:|---:|---:|---:|---|
| AVAX | L1 smart-contract | 164 | −34.6% | −1.84 | 9 min | Rejected |
| LTC | Payments L1 | 165 | > 0 (no stop) | +0.60 | 99 min | **Accepted** |
| ATOM | L1 smart-contract | 167 | −7.1% | −0.89 | 19 min | Rejected |
| DOT | L1 smart-contract | 168 | −14.0% | +0.54 | 11 min | Rejected |
| AAVE | DeFi blue-chip | 170 | −17.8% | +0.06 | 7 min | Rejected |

**LTC is the lone success across 5 sector-diverse candidates.** The failure mode isn't about sector (AAVE is DeFi, not L1), it's about the 2022 bear regime interacting poorly with our training window. Only LTC had a 2022 that the model could learn through.

Total compute for all 5 screens: 145 minutes with fail-fast, vs. ~450 minutes without. Fail-fast protocol is doing its job.

## Why candidate screening is hitting a wall

- 2022 was a post-FTX bear market. Most alts dumped hard and stayed decorrelated from their pre-bear behaviour.
- Our training window is 24 months — the first year of predictions (2022) therefore trains on 2020–2021 (bull) and predicts 2022 (bear). Regime mismatch.
- LTC uniquely survived because its 2022 dynamics were closer to its pre-2022 dynamics (payments narrative, not "speculative alt L1/DeFi").
- No amount of candidate screening at the same config will overcome a structural regime mismatch.

## Concentration constraint still unresolved

Baseline v0.165 has LINK at 77.5% of OOS PnL. Four failed candidate additions mean the portfolio stays at 4 symbols with LINK dominating. Concentration needs a structural intervention, not more candidates.

## Research Checklist

- **B — Symbol Universe (AAVE)**: Gate 3 failed. 4-of-5 candidates rejected at this config.
- **E — Comparative pattern**: documented above.

## Exploration/Exploitation Tracker

Window (161-170): [E, E, E, E, E, X, E, E, E, E] → **9E / 1X**, 90% E. The last 5 iterations have all been EXPLORATION and 4/5 of them are NO-MERGE EARLY STOPs. Time to rebalance hard.

## Lessons Learned

1. **Five candidate screens, one success.** Continuing to screen without changing the config is a losing strategy. LTC's success is clearly the outlier.
2. **Concentration needs a different tool.** Adding more models isn't working. Next lever: position-sizing cap at the portfolio layer.
3. **The screening fail-fast protocol is invaluable.** 145 minutes for 5 definitive rejections is massively better than 450 minutes of full runs.

## Next Iteration Ideas

### 1. Iter 171 (EXPLOITATION, PRIORITY) — Portfolio-level concentration cap

Code change in `BacktestConfig` / backtest engine to add `max_symbol_pnl_share: float = 0.30`. When a symbol's cumulative OOS-window weighted PnL reaches 30% of the portfolio total, clip subsequent trades' weight_factor on that symbol. The remaining trade budget reallocates (by equal-weight default) to other symbols.

Test by re-running the A+C+LTC portfolio with the cap active. Expected: LINK's PnL share drops from 77.5% to ~30%, aggregate PnL drops but Sharpe may improve if LINK's clipped trades were in high-variance drawdowns.

Tag: EXPLOITATION (infrastructure change, not a new model or feature set).

### 2. Iter 172 (EXPLOITATION) — If iter 171 works, formalise the rule and update baseline

If the capped portfolio still passes both Sharpe floors (IS > 1.0, OOS > 1.0) and reduces LINK share to acceptable, merge. BASELINE.md gets a new "position cap" parameter.

### 3. Iter 173+ (deferred) — Structural regime handling

Rather than screening more candidates, consider adding regime features (BTC dominance trend, VIX-proxy for crypto) so the model learns TO be different in bear markets. This is a multi-iteration EXPLORATION track; premature without first fixing the concentration issue.

### 4. Do NOT screen more candidates at this config

The evidence is conclusive: the screening approach has exhausted useful information at the current config. Further candidate screens are dead compute until something structural changes.

## lgbm.py Code Review

No changes this iteration. Pending cleanup item from iter 166 (dead `self.seed` parameter) was already resolved in commit `f6d3c7a`.
