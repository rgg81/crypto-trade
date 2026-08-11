# cascade-breadth-01

Team 05, lane `short-horizon-liquidity-shock-reversal`. **Nominated candidate.**

## The book in one paragraph

At every 8h boundary the strategy looks at the bar that closed one boundary ago and counts how many
point-in-time members printed a close-to-close return at or below `SHOCK_Z` trailing standard
deviations, where the deviation is measured over the previous `LOOKBACK_BARS` bars **strictly
before** the bar being judged. If at least `MIN_BREADTH` members did so in that same bar, the book
treats it as a liquidation cascade rather than as news, goes equal-weight long the `BASKET_NAMES`
eligible members that fell furthest on that bar, returns `None` for the remaining `HOLD_BARS`
boundaries — which holds quantities and costs no turnover — and then emits `{}` to flatten. It is
flat between episodes and does not re-enter while positioned. About 44 episodes a year.

## Why simultaneity is the conditioner

Information arrives at one asset. A margin engine unwinds correlated collateral across the whole
book at once. So the thing that distinguishes a forced move from an informed one, at bar
resolution, is not how big it was but how many names it happened to at the same time.

That is not a story; it is what the trials measured. On this universe a large single-name move
**continues** rather than reverting, and the ablation that reverses on return magnitude alone
(`baseline-plain-reversal`, journal #48) earned 22.3 bps per unit of turnover, was positive in two
folds of four, drew down 24.3% and returned a 3×-cost Sharpe of 0.01. Requiring the same move in
several names at once, changing nothing else, earned 42.6 bps per unit of turnover, was positive in
four folds of four, drew down 19.1% and returned a 3×-cost Sharpe of 0.54.

## Why the timing is what it is

From an event study over the in-sample window, the mean open-to-open return of a qualifying name
runs: bar +1 about flat, bar +2 **+61 bp** (t = 4.3), bar +3 **+99 bp** (t = 7.6), bar +4 flat,
bars +5 and +6 negative. The forced selling completes in the bar after the shock and the repayment
lands in the two bars after that. `ENTRY_DELAY = 1` skips the first, `HOLD_BARS = 3` covers the
repayment and stops before the drift back. Neither number was read off a Sharpe surface.

## What it deliberately does not do

- **No short sleeve.** Shorting after an up shock lost at every horizon from 8h to 72h, at every
  threshold, and under every conditioning tried. Declared roles are `long` only.
- **No trade-count gate.** It was the first design's third condition and it subtracted; the
  constant survives at its disabled value so the source records the decision.
- **No declared risk control.** Both instruments the schema offers are contraindicated here: a
  drawdown brake is pro-cyclical against a book whose opportunities *are* drawdown events, and a
  position stop cuts the best cases — the deeper a cascade name is under water after one held bar,
  the larger its subsequent bounce (+564 bp after a first bar below −10%, against +80 bp after a
  flat one). `volatility_target.enabled` is `false` (charter §6, amendment A3).

## Declared parameters

| Name | Value | Role |
|---|---:|---|
| `SHOCK_Z` | -2.0 | how far a member's move must outrun its own scale (**neighbourhood coordinate**) |
| `BASKET_NAMES` | 8 | how many of the deepest fallers the basket holds (**neighbourhood coordinate**) |
| `LOOKBACK_BARS` | 60 | the window "its own recent scale" is measured over (**neighbourhood coordinate**) |
| `MIN_BREADTH` | 2 | simultaneous shocked members that make it a cascade |
| `ENTRY_DELAY` | 1 | boundaries waited so the forced selling completes before the entry |
| `HOLD_BARS` | 3 | boundaries held, covering the measured repayment window |
| `FLOW_SPIKE` | 0.0 | disabled trade-count gate, retained so the source records the decision |

## Provenance

The behaviour frozen here was first scored at journal sequence **#49**, under the candidate id
`ablate-flow-signature`, because it was born as an ablation of the first design's trade-count gate
and the ablation turned out to be the better book. `cascade-breadth-01` carries the identical
constant table and the identical class and function bodies — verified by AST comparison after
stripping docstrings — with the documentation rewritten so the frozen source says what it does, and
with `neighbourhood.json` added. The declared sweep re-measures the nominee point on these exact
bytes.
