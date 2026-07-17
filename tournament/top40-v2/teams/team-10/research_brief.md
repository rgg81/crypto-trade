# Team 10 final pivot-02 research brief — funding-pressure transfer and unwind

Status: **prospective, unregistered, unevaluated**

Both earlier families are terminal. The initial no-control residual trend/reversion candidate became
insolvent before metrics. Pivot-01 restored solvency but falsified its convergence thesis: annualized
return was `-0.09328445205038527`, Sharpe `-1.86846407399797`, doubled-cost Sharpe
`-2.436836526128816`, Calmar `-0.30631265956122306`, maximum drawdown
`0.3045399827222629`, and positive-quarter fraction `0.14285714285714285`. Every reported regime
Sharpe was negative: bull `-1.5124282333375314`, bear `-2.200607191286561`, chop
`-3.0617769845946468`, and stress `-1.5413188398402713`. Its `9581` trades and worse doubled-cost
result also show that daily rank churn magnified a pervasive alpha failure. This is not an isolated
regime, scale, or control problem, so neither a sign flip nor a risk overlay is defensible.

## Final mechanism

Pivot-02 uses a new economic input: paid funding imbalance. At the weekly Unix-epoch-anchored
decision, it admits only exact, non-extreme price histories and strictly past, nonstale funding events
from the prior 14 days. Funding pressure is cumulative transfer plus a frozen persistence term.
Persistent positive funding represents costly crowded longs, so it receives a low expected price
return score; low or negative pressure receives a high score. The exact negative robust z-score is
captured once by A5 before score filtering, selection, retention, sizing, caps, or organizer risk.

Four lowest-pressure contracts are held long and four highest-pressure contracts short at `0.015`
each. The book is `0.12` gross, zero net, changes at most weekly, retains incumbents within two extra
ranks, and returns hold when sleeves are unchanged. The lower gross and weekly cadence are intrinsic
to the transfer mechanism, not a control applied to either failed signal.

## Universe and regime roles

Only organizer-qualified native crypto base assets may enter. Stablecoin bases and tokenized or
synthetic TradFi securities, commodities, metals, and indexes remain excluded even if Binance lists
them as perpetual contracts. A stable quote/collateral currency does not turn a native crypto base
asset into a stablecoin. Amendment 0006 metadata is the only classifier; ticker-name heuristics are
forbidden.

- Bull: the long sleeve owns low-cost, low-crowding or negatively funded contracts and targets
  under-owned participation or short covering.
- Bear: the short sleeve holds highly positive-funded crowded longs, receives funding, and targets
  unwind.
- Chop: the balanced book targets recurring funding transfer and cross-sectional crowding
  normalization.
- Stress: exact data admissibility, weekly cadence, `0.12` gross, and zero net are frozen portfolio
  construction; no central risk control is active.

Every return, cost, A5, fold, quarter, drawdown, Calmar, regime, role, and sleeve threshold is
non-compensatory. This is the second and final pivot. Controls, ablations, and neighbors are
forbidden; core failure is DNF. Official stability thresholds are preserved and not waived, so Team
10 also cannot self-claim qualification without organizer-authorized stability evidence.
