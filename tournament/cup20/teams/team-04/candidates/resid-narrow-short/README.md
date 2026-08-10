# resid-narrow-short

`baseline-thirds` with two changes, both aimed at floors the baseline failed on trial #30
(`role_short_gross_pnl = -0.045`, `worst_fold_sharpe = -1.07`).

* the short sleeve is narrowed from a third to a fifth of the cross-section (7 long / 4 short on
  a 20-name universe). Measured in-sample, a diversified short third of this universe does not
  fall in absolute terms over a window in which the equal-weight index roughly tripled, and
  `short_gross_pnl > 0` is a hard floor about absolute decline, not about spread. Concentrating
  the short sleeve on the deepest residual losers is the only lever on it that stays inside a
  cross-sectional mandate.
* the cadence lengthens from 21 to 24 bars, which buys turnover headroom under the 25x floor that
  the baseline cleared by 0.109.

Same signal, same causal beta, same risk policy: flat.
