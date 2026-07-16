# Post-result review: Team 02 FIR reference 001

## Decision

**Stop `team-02-funding-inventory-relaxation-v1` and record Team 02 DNF.** The exact final-pivot
no-control reference has a completed, profitable aggregate record, but it fails the preregistered
all-regime core: its published bear Sharpe is `-1.0155758613712025`. That is below the frozen
worst-regime floor of `-0.25` and, for the completed zero-risk-free net-return series, implies a
negative mean bear return. The exact compounded bear return was not serialized, but its sign is
enough to trigger the registered requirement that bull, bear, and chop return each be positive.

FIR's global stop says that a failed reference ends every diagnostic, parameter, neighbor, and
risk observation. This is Team 02's second and final mechanism pivot. Remaining trial, CPU, and
wall-clock capacity cannot override the falsifier, and risk controls cannot manufacture the missing
bear core. The candidate is not eligible for a private-qualifier ticket.

## Exact runner evidence

The candidate completed the visible window `[2020-02-03, 2023-07-01)` with the registered seed
`20260801` and fully disabled policy `team-02-fir-reference-no-control`.

| Metric | Gate | Observed | Result |
| --- | ---: | ---: | --- |
| Net Sharpe | `>= 0.75` | `1.2742743402942744` | pass |
| Annualized return | `> 0` | `0.1131956023912728` | pass |
| Calmar | `>= 0.40` | `1.3765628606630103` | pass |
| Maximum drawdown | `<= 0.30` | `0.08223060902337076` | pass |
| Doubled-cost Sharpe | `>= 0.35` | `1.0698731207752976` | pass |
| Positive-quarter fraction | `>= 0.55` | `0.5714285714285714` (`8/14`) | pass |
| Positive-Sharpe regimes | `>= 3` | `3` | pass |
| Worst-regime Sharpe | `>= -0.25` | bear, `-1.0155758613712025` | **fail** |

The runner's regime Sharpes are bull `1.9272882271946317`, bear
`-1.0155758613712025`, chop `0.8611137173031981`, and stress
`2.2542068737080267`. Thus three regimes have positive Sharpe, but the non-compensatory worst-regime
gate fails by `0.7655758613712025` Sharpe units. Strong bull, chop, and stress observations cannot
offset it.

The runner also reports net-Sharpe 95% interval
`[0.11449754601163036, 2.4341102967333046]` and doubled-cost-Sharpe 95% interval
`[-0.10030111749929538, 2.227980350349412]`. These are context, not substitutes for the failed
regime gate.

## Chronological fold evidence

Read-only compounding of the candidate's hash-bound daily return artifact inside Team 02's six
predeclared end-exclusive intervals gives:

| Fold | Interval | Days | Net return | Sequential PnL (USDT) | Sign |
| --- | --- | ---: | ---: | ---: | --- |
| 1 | `[2020-02-03, 2020-09-01)` | 211 | `0.015537221653829869` | `1553.7221653829911` | positive |
| 2 | `[2020-09-01, 2021-04-01)` | 212 | `0.16237363162959029` | `16489.646673495648` | positive |
| 3 | `[2021-04-01, 2021-11-01)` | 214 | `0.18262924628142208` | `21558.171479564306` | positive |
| 4 | `[2021-11-01, 2022-06-01)` | 212 | `0.025887986262197016` | `3614.002757945389` | positive |
| 5 | `[2022-06-01, 2023-01-01)` | 214 | `-0.0041559243401081414` | `-595.1929613529646` | negative |
| 6 | `[2023-01-01, 2023-07-01)` | 181 | `0.01051861902543938` | `1500.1691281348467` | positive |

The local fold diagnostic is `5/6` profitable and clears the `>=4` return-count condition. It is
not a centrally generated qualification record: no six-fold hash-bound walk-forward manifest or
fold-model declaration exists in Team 02's artifacts. The playbook explicitly says that slices of
one full-period result are not, by themselves, proof of declared OOF construction. This limitation
does not soften the bear failure.

## Funding, sleeves, and causal interpretation

Reconciliation of the bar-return components against prior-bar equity produces ending equity
`144120.51924317062` USDT and net PnL `44120.519243170464` USDT. The components are:

| Component | USDT |
| --- | ---: |
| Price PnL | `33981.86741224241` |
| Realized funding PnL | `18272.07559470852` |
| Fees | `-5422.282509187051` |
| Slippage | `-2711.1412545935254` |
| Net | `44120.519243170464` |

Funding PnL is positive in every chronological fold: `204.10424037263232`,
`4684.10112097439`, `2276.720193798502`, `5086.067479125398`,
`3518.7922929115184`, and `2502.2902675261075` USDT. Aggregate funding PnL and the softer
four-of-six funding expectation therefore pass. The observed failure is not absence of carry; it is
failure to turn that carry construction into the required bear portfolio behavior.

Both sleeves are materially present. Using the frozen `0.01` activity threshold, each sleeve is
active on `3150/3732 = 0.8440514469453376` bars. Mean long and short gross exposures are
`0.16815086264219517` and `0.1667696275517433`, both above `0.01`. The first rebalance from flat
executes `18000.19615851095` USDT across six long names and `17999.202746876792` USDT across six
short names, conservatively clearing each `1000` USDT notional floor.

The runner does not publish long-bull, short-bear, or combined-chop net return. Those role gates are
unestablished rather than fabricated. They cannot rescue the candidate because the combined bear
regime has already failed a separate hard condition.

## Remaining visible gates

No trial-adjusted probability of positive Sharpe is published, so the `>=0.90` multiplicity gate is
unestablished. None of the eight preregistered neighbors was run, leaving profitable-neighbor
fraction (`>=0.70`) and neighbor median Sharpe (`>=0.50`) unestablished. The reference falsifier
forbids running them now.

A transparent local concentration check gives positive-fold PnL concentration
`21558.171479564306 / 44715.71220452318 = 0.4821162498980304` and positive-quarter concentration
`15864.953021231544 / 57323.049764311 = 0.27676393852842374`. Taking the larger gives
`0.4821162498980304`, above the visible `0.40` ceiling. The organizer has not published the central
scalar or its exact reduction definition, so this is recorded as a local diagnostic failure rather
than represented as official qualification evidence.

Accordingly, the reference passes the headline aggregate, cost, drawdown, fold-count, quarter,
funding, sleeve-activity, and sleeve-notional checks. It fails the registered bear core and the
exact published worst-regime floor; other mandatory multiplicity, neighborhood, role, OOF-manifest,
and official concentration evidence is absent. Qualification requires every gate, so there is no
eligible champion.

## Falsifier and budget accounting

The registered reference falsifier passes completion/solvency, positive annualized return, positive
net and doubled-cost Sharpe, positive funding PnL, drawdown at most 30%, and at least four profitable
folds. It fails the positive bull/bear/chop condition through bear. Long-bull and short-bear role
values remain unpublished, but no second failure is needed to stop.

Four material configurations have been consumed in total. Their recorded usage is
`0.9014440241291666` CPU hours and `0.9006860905658283` wall-clock hours. The global ledger would
otherwise leave 76 configurations, while FIR's staged plan would leave 28 of its 29 observations.
Both formal pivots are consumed, leaving zero. Unused capacity is not permission to violate the
final-pivot global stop.

## Disposition and integrity boundary

Do not run FIR's level-only, relaxation-only, no-volatility-filter, sign-flip, coarse parameter,
neighbor, or risk-factorial cells. Do not lower gross, alter the side budgets, add a volatility
target or drawdown brake, consume the private ticket, or rename the mechanism. Record the honest
negative result and Team 02 DNF through the separately authorized organizer lifecycle when
appropriate.

This review used read-only inspection of Team 02's own runner, registration, journal, and
development artifacts plus public Top40 V2 rules. It did not run a strategy, test, tournament CLI,
evaluator, or Git command; inspect private/final OOS or another team's result; alter source,
strategy, risk policy, journals, or lifecycle state; or fabricate missing official evidence.
