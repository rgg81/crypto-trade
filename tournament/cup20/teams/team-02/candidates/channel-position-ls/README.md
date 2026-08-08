# channel-position-ls

**Lane:** breakout / channel-position (team-02).
**One line:** long the three coins sitting highest inside their own trailing quarter range, short
the three sitting lowest, equally weighted, retargeted once a week on the reconstitution boundary.

## The statement being made

For each eligible member of the point-in-time top-20, form the trailing Donchian channel over
`FORMATION_BARS` 8h bars and read off where the last close sits inside it:

```
u = (close - min(low, FORMATION_BARS)) / (max(high, FORMATION_BARS) - min(low, FORMATION_BARS))
```

`u` is a **location**, not a rate of change. It is bounded, it is invariant to how violent the
move that produced it was, and two coins that both print a new quarter high score identically
however differently they got there. That saturation is the whole point: the quantity being
measured is *how completely a coin has consumed the resting supply inside its own band*, and a
coin that has cleared every seller in its range has cleared them whether it took two weeks or ten.

Why that should pay on the twenty most liquid perpetuals, where the false-break problem is
supposed to be worst: resting liquidity is deepest exactly at the extremes of a well-watched
range, so a coin that is *sitting* at the top of its quarter range is one that has repeatedly
absorbed that supply rather than one that poked through it once. On the other side, each new low
in a multi-week range is a fresh liquidation trigger, and the mechanical flow that follows is what
carries the move. False breaks are real and frequent — they are simply not something the book has
to identify, because it ranks the cross-section rather than betting on a single breach, and a
snap-back removes a coin from the sleeve at the next weekly boundary rather than costing it a stop.

## The book

| | |
|---|---|
| universe | point-in-time top-20 members with an executable open and a fully formed channel |
| score | `u` over `FORMATION_BARS = 252` bars (84 days, one calendar quarter) |
| long sleeve | the `SLEEVE_SIZE = 3` highest `u`, `+1/6` each |
| short sleeve | the `SLEEVE_SIZE = 3` lowest `u`, `-1/6` each |
| gross / net | 1.0 / 0.0 by construction — equal counts, equal weights, both sleeves |
| rebalance | every `REBALANCE_BARS = 21` bars (7 days) at `PHASE_OFFSET = 12`, i.e. Monday 00:00 UTC |
| between rebalances | `None` — quantities are held, no turnover is generated |

`1/6 = 0.1667` sits under the 0.20 per-symbol cap, so the executed weights are the weights the
strategy asked for and the `exposure_caps` block should report no reduction at the requested stage.

`PHASE_OFFSET = 12` is the residue of Monday 00:00 UTC modulo 21 in absolute 8h bar index. It was
chosen so the book retargets on the weekly reconstitution boundary itself and therefore always
trades the universe it has just been handed — not because of what it scored.

## What is deliberately absent

* **No volatility target, no drawdown brake, no stops.** `risk_policy.json` declares nothing. The
  common risk unit sets the book's scale; nothing here is trying to pass a floor by declaring a
  number.
* **No absolute band rule.** "Long anything above 0.85 of its own range" was tested and is much
  worse: it goes long when the whole market is high in its range and short when the whole market
  is low, which is a bet on market direction wearing a channel costume.
* **Two range-structure controls, implemented and frozen off.** `CONTROL_FRESH_BARS` (prefer a
  breach that is actually fresh) and `CONTROL_COMPRESSION` (prefer a coiled range) are the two
  candidate answers to "what separates a break that carries from one that snaps back". Both were
  run and both made the book worse. They are left in the frozen source, set to zero, so the
  ablation is literally the same code with one constant changed.

## Declared neighbourhood

Three coordinates — `FORMATION_BARS`, `REBALANCE_BARS`, `PHASE_OFFSET` — swept above and below the
nominee. `SLEEVE_SIZE` is a fixed structural choice, pinned by the per-symbol exposure cap rather
than tuned; the research certificate records the sleeve-size screen that fixed it.
