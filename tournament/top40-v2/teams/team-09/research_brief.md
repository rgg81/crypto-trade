# Team09 research brief — confirmed funding-crowding unwind

Status: **prospective, unregistered, unevaluated**

## Question and mechanism

Does a persistent cross-sectional funding extreme become tradable after price begins moving against
the crowded side? Funding is the observable transfer price between long and short perpetual
inventory. High relative funding suggests crowded longs; low relative funding suggests crowded
shorts. Crowding can persist, so Team09 does not trade the funding rank alone. It waits for causal,
contiguous past-close relative performance to confirm an unwind:

- long: low relative funding plus positive relative-price confirmation;
- short: high relative funding plus negative relative-price confirmation; and
- flat: too little cross-sectional history or fewer than four qualifying symbols on either side.

The center rebalances once daily at 00:00 UTC. It uses seven days of strictly past funding events,
a three-day price-confirmation horizon, and a 21-day volatility scale. Cross-sectional average-tie
ranks avoid a fitted distribution. The selected long and short sleeves receive equal gross
exposure; no learned beta or hedge ratio is used. Each symbol remains below the evaluator's 10%
cap, total gross stays below one, and net target exposure is zero.

## Why it could span market conditions

In bull conditions, underfunded relative leaders should support the long sleeve while crowded
laggards remain eligible shorts. In bear conditions, high-relative-funding laggards should support
the short sleeve while the balanced long sleeve limits directional beta. In chop, relative funding
transfer and crowd unwinds—not market direction—are the proposed return source. During stress,
breadth can disappear and the signal must request flat rather than manufacture a weak sleeve.
Organizer-owned volatility targeting, drawdown brakes, a close-confirmed position stop, and a
turnover limit are separate prospective risk-policy hypotheses.

These are hypotheses, not performance claims. Positive net return in bull, bear, and chop; long
bull attribution; short bear attribution; combined chop attribution; both sleeves' materiality;
and every common stability/cost gate are required evidence.

## Causal discipline

At decision time `t`, the newest price candle opens at `t-8h` and closes at `t`. A symbol is
excluded unless its entire required tail is exactly contiguous at eight-hour spacing. Funding
uses only events with `funding_time < t`, a bounded trailing window, a minimum event count, and a
maximum age. No future row is ignored silently: a future bar or non-past funding event fails
closed. Under-history or stale individual symbols are excluded without aborting the remaining
eligible cross-section.

The strategy has no supervised labels, fitted coefficients, date-to-target table, filesystem
access, network access, external model, or stochastic state. Cross-sectional ranks and portfolio
weights are recomputed from the supplied past-only context in sorted symbol order.

## Falsifiers and decisions

The mechanism is falsified if any of the following remains true after the preregistered trials:

- stitched chronological evidence fails any frozen development gate;
- any of bull, bear, or chop has nonpositive net return;
- the long sleeve is not positive in bull or the short sleeve is not positive in bear;
- the joint rule does not improve meaningfully over funding-only and price-only ablations;
- fewer than 70% of preregistered neighbors are profitable, neighbor median Sharpe is below 0.50,
  or positive PnL concentration exceeds 0.40;
- doubled-cost Sharpe is below 0.35 or risk controls only cosmetically suppress volatility; or
- the apparent result is concentrated in one fold, quarter, regime, side, or symbol.

A failed center leads to a documented ablation decision or a genuine mechanism pivot within the
common cumulative budget. A negative or otherwise unqualified IS result is never frozen as a
submission. If no family passes every gate by the budget/deadline, Team09 records DNF.

## Prospective trial allocation

The planned material allocation is 31 configurations, leaving 49 of the common 80 for documented
follow-up or at most two mechanism pivots:

- 1 center mechanism;
- 6 mechanism/control ablations in `ablations.json`;
- 10 two-sided parameter neighbors in `parameter_neighborhood.json`;
- 6 declarative risk policies, each producing paired base/doubled-cost panels in one run; and
- 8 confirmatory reruns or preregistered simplifications selected only after a written review.

The 31 count does not grant permission to batch or inspect results before registration. Every
material configuration must be registered through the active Amendment-0006 entrypoint before
its result is read. The six risk policies count as six, not twelve: base and doubled costs are
paired outputs of the same organizer run.

## Selection rule

Selection is non-compensatory. First require every centrally derived development, regime, sleeve,
stability, concentration, and doubled-cost gate. Among passers only, compare the lower of base and
doubled-cost Sharpe, then the worst fold/regime Sharpe, then simplicity and turnover. A high
aggregate Sharpe cannot compensate for a failed gate, and a relative rank cannot advance a
non-passer.

No private ticket may be consumed until source, complete executable dependency manifest,
parameters, seed, risk policy, trial journal head, OOF declarations, neighborhood, provenance,
and centrally derived positive development evidence are frozen under the then-active lifecycle
authority. Private failure is terminal DNF. Final OOS is not a research view.
