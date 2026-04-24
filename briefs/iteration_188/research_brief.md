# Iteration 188 — R1 on Model A (rejected)

**Date**: 2026-04-22
**Type**: EXPLOITATION (post-hoc risk-mitigation test)
**Baseline**: v0.186
**Decision**: NO-MERGE

## Motivation

v0.186 has R1 (consecutive-SL cool-down) active on Models C, D, E but not on
Model A. A prior design note (iter 173) called out that Model A's BTC/ETH
trades showed mean-reverting WR at late streaks, suggesting R1 might hurt —
but we never actually simulated it in the v0.186 context. Now that R3 changed
the trade landscape, it's worth checking again.

## Method

Post-hoc simulation from `reports/iteration_186/` (v0.186 trades). Apply R1
per-symbol (matching `backtest.py` behavior) to the Model A (BTC+ETH) trade
stream. Sweep K ∈ {2, 3, 4}, C ∈ {9, 18, 27, 36} candles (9 ≈ 3 days).
Keep LINK/LTC/DOT trades unchanged and recompute portfolio metrics.

## Result (per-symbol R1 on Model A only)

```
baseline (no R1 on A): IS Sharpe +1.440, OOS Sharpe +1.737, OOS MaxDD 29.31%

 K   C | IS Sharpe  IS DD  IS n | OOS Sharpe OOS DD OOS n
 2   9 |    +1.469  56.70%   587 |    +1.782  29.31%   208
 2  27 |    +1.402  57.00%   547 |    +1.812  22.84%   194
 2  36 |    +1.348  55.85%   537 |    +1.898  22.84%   194
 3  27 |    +1.372  54.80%   572 |    +1.768  29.09%   200
 4  27 |    +1.377  55.95%   589 |    +1.743  28.40%   206
```

## Finding

R1 on Model A consistently trades IS Sharpe for OOS Sharpe:

- **Best IS Sharpe at K=2/C=9: +1.469** (baseline +1.44, +0.029). OOS gain
  is only +0.045 — noise level.
- **Best OOS at K=2/C=36: +1.898** (+0.161 gain), but IS Sharpe drops to
  +1.348 (−0.092 from baseline). That's 8% IS degradation to gain 9% OOS
  — a classic overfitting signature when the filter was hand-picked.
- All K/C settings show IS Sharpe declining or flat; none improve both IS
  AND OOS by a meaningful margin.

The skill prohibits picking R1 parameters that optimize OOS when IS worsens
("NEVER tune parameters on OOS data"). The IS-calibrated choice (K=2, C=9)
produces a +0.045 OOS gain that is within seed noise.

## Why R1 hurts Model A where it helps C/D/E

LINK/LTC/DOT are single-symbol models with clustered SL streaks during
regime shifts (e.g. DOT's 2022 bleed). R1 truncates the damage.

Model A is pooled BTC+ETH with **mean-reverting WR at streak length ≥ 3**
— when BTC or ETH has a run of SLs, the next trade is disproportionately
likely to hit TP. Blocking trades during a streak forfeits this
mean-reversion edge.

This was the finding from iter 173's bucket analysis. v0.186's R3 filter
didn't change this fundamental property of Model A's prediction stream.

## Decision

NO-MERGE. Model A keeps R1 disabled. v0.186 stands as baseline.

## Exploration/Exploitation Tracker

Window (178-188): [E, E, X, E, X, E, X, X, X, X, **X**] → **4E/7X**.
Heavy exploitation leg after the strong R3 result.

## Next Iteration Ideas

- **Iter 189**: Per-symbol OOD cutoffs. Compute separate Mahalanobis
  thresholds for BTC/ETH/LINK/LTC/DOT. BTC's low WR (32.6% OOS) suggests
  a tighter cutoff might help, while LINK's healthy 50% WR suggests
  loosening. Post-hoc fast.
- **Iter 190**: Alpha improvement via cross-asset features. Add
  `btc_30d_return` and `btc_realized_vol_30d` to LINK/LTC/DOT feature
  sets. Might lift altcoin models by exposing them to market-wide
  regime info. Full backtest (~5h).
- **Iter 191**: Revisit ETH-only Model A. Post-hoc in iter 187 suggested
  pool-training helps BTC+ETH, but a dedicated ETH-only retrain might
  find different hyperparameters. If OOS Sharpe climbs, drop BTC from
  training too.
