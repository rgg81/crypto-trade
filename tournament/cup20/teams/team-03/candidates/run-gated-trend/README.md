# run-gated-trend

Momentum that is only allowed to take size when the path that produced it has the run structure
of a trend rather than of a random walk that happened to end up somewhere.

## What it does, at one decision boundary

1. **Cadence.** The 8h UTC grid is indexed from the epoch. If `index % REBALANCE_EVERY !=
   REBALANCE_PHASE % REBALANCE_EVERY` the strategy returns `None` and the evaluator holds
   quantities. On a rebalance boundary it emits signed target weights.
2. **Direction.** For every eligible symbol and every one of the last `SMOOTH_BARS` bars, the net
   log displacement over the preceding `FORMATION_BARS` bars gives a direction.
3. **The gate.** Over the same window, count the bars whose own step agreed with that direction and
   standardise the count against a coin-flip null,
   `z = (2 * agreeing_fraction - 1) * sqrt(FORMATION_BARS)`.
   The name is admitted at that bar only if `z >= PERSISTENCE_Z_FLOOR`; otherwise it contributes
   zero. This is the mechanism. Everything else is a control.
4. **Size within the admitted set.** `direction / sigma`, where sigma is the standard deviation of
   the same window's steps, so the admitted names carry comparable risk rather than comparable
   notional.
5. **Overlapping tranches.** Each historical bar's admitted cross-section is normalised to unit
   gross and the target is the mean over the last `SMOOTH_BARS` of them. A name admitted on 30 of
   the last 33 bars carries roughly six times the weight of one admitted on 5 of 33 — the gate
   sizes, it does not only select — and at most one tranche of the book can re-form per bar, which
   is what brings turnover and cost density inside their floors.
6. **Net-exposure damping.** `NET_EXPOSURE_DAMPING` times the book's average weight is subtracted
   from every live name. The book keeps most of its directional tilt; this trims the part of it
   that is a one-way bet on the whole universe rather than on the names the gate chose.

## Parameters

| Constant | Value | Role |
|---|---:|---|
| `FORMATION_BARS` | 15 | formation window (5 days) — neighbourhood coordinate |
| `PERSISTENCE_Z_FLOOR` | 1.10 | run-structure admission threshold — neighbourhood coordinate |
| `SMOOTH_BARS` | 33 | overlapping tranches / holding horizon (11 days) — neighbourhood coordinate |
| `NET_EXPOSURE_DAMPING` | 0.45 | net-exposure control — neighbourhood coordinate |
| `REBALANCE_PHASE` | 1 | phase offset of the cadence — neighbourhood coordinate |
| `REBALANCE_EVERY` | 3 | rebalance cadence (24h) — neighbourhood coordinate |

## The declared neighbourhood

`neighbourhood.json` declares all six material parameters as coordinates and a **one-at-a-time
star**: the nominee plus exactly one point above and one point below on each coordinate, 13 points
in total, which is the `max(7, 2k+1)` minimum for `k = 6` on the nose. Every point differs from the
nominee in exactly one coordinate, so no side of any axis is padded and no corner is chosen — the
design has no free parameter left to lean on the median with.

Two of the six need a word about why their variations are the size they are.

`PERSISTENCE_Z_FLOOR` is compared against a **quantised** statistic. With `FORMATION_BARS = 15` the
agreeing-bar count is an integer, so `z` can only take the values `(2k - 15)/sqrt(15)`: 0.775 at
k = 9, 1.291 at k = 10, 1.807 at k = 11. Every threshold in `(0.775, 1.291]` therefore selects the
identical set of bars and produces a **byte-identical book**. The nominee's 1.10 sits in that cell,
and so would the 5%-material variations 1.045 and 1.155 — both of which would be inert points under
charter §7.2 as amended, voiding the sweep. The declared variations are 0.70 (admits k ≥ 9) and 1.40
(admits k ≥ 11): each lands in a different quantisation cell from the nominee and from each other.

`REBALANCE_PHASE` is declared at 0 and 2, which with `REBALANCE_EVERY = 3` is the **exhaustive** set
of phase offsets. Charter §9.1 requires the phase swept for any cadence longer than one bar, and at
this cadence the sweep is complete rather than sampled.

## Roles

Long and short. The gate is symmetric and the book runs both sleeves at every boundary; the
short sleeve is smaller and its gross PnL is materially smaller than the long sleeve's, which is
disclosed in the certificate as the candidate's thinnest hard floor.

## What is deliberately absent

No execution view, no cost view, no equity view — the protocol exposes none of them. No fitted
model, no stored artefact: every number is recomputed from the past-only rows in the context. No
declared volatility target and no declared drawdown brake; `risk_policy.json` is explicitly flat,
so nothing here reaches a floor through the declared policy.
