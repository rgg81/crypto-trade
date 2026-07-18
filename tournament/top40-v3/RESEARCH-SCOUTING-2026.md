# Top40 V3 research scouting note — July 2026

The organizer searched recent primary research before Phase 0. This note records what can be
tested with the frozen V3 fields and, just as importantly, what cannot. A paper is a hypothesis
source, not evidence that our implementation will survive costs or sealed validation.

## Actionable findings

1. **Price-volume structure deserves a first-class challenger.** Cao, Luo, Cheng, and Dong's
   2026 working paper, [Anatomy of Cryptocurrency Perpetual Futures Returns](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6365329),
   reports a broad predictor study in which basis and price-volume structure explain many sorted
   perpetual-return predictors. V3 cannot reproduce their basis factor, but its frozen OHLC,
   quote volume, trade count, and taker-flow fields can test the price-volume branch. Team 07's
   liquidity router is therefore an active priority, not a decorative novelty.

2. **Funding is a feedback mechanism with tail risk, not free yield.** Zhang's 2026 working
   paper, [Funding Rate Mechanism in Perpetual Futures](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6185958),
   models funding interval, caps, clamps, constrained arbitrage, and crisis jumps. Team 09 must
   infer interval changes only from settled events, cap anomalous observations, require positive
   expected whole-book carry, and keep an explicit crowding-loss control.

3. **The crash warning in carry is economically meaningful.** The October 2025 revision of the
   BIS working paper [Crypto carry](https://www.bis.org/publ/work1087.htm) links large carry to
   leveraged trend chasing and scarce arbitrage capital and documents that high carry predicts
   future crashes. This supports testing Team 09's narrowly defined price-weakness confirmation;
   it does not license spot data, options data, or a synthetic basis that V3 does not possess.

4. **Perpetual-basis convergence remains a reserve mechanism.** Gornall, Rinaldi, and Xiao's
   2025 paper [Perpetual Futures and Basis Risk](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5036933)
   and the 2025 revision of [Fundamentals of Perpetual Futures](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4301150)
   strengthen the case for constrained-arbitrage basis models. The current snapshot has no
   survivorship-safe spot leg or historical premium-index series, so V3 records this idea but
   does not fabricate the missing data.

## Orchestrator response

- Every new academic mechanism begins as a challenger, never as an automatic nominee.
- Exact V2 core-passing implementations are audited as incumbent champions. A team may retain a
  compatible incumbent, improve it, or replace it only after the challenger wins on logged
  training evidence and remains positive at doubled costs.
- Research proceeds baseline -> sign inversion -> horizon/holding grid -> neutralization ->
  controls -> local-neighborhood check. Red variants are killed; amber variants receive a
  specific repair; green variants may spend a sealed-validation probe.
- No paper, model complexity, or novelty bonus compensates for negative train or validation
  performance.

## Data-feasibility boundary

| Research object | V3 status | Reason |
|---|---|---|
| Price-volume/liquidity routing | active | causal frozen transaction bars contain the fields |
| Settled funding carry | active | actual funding events and marks are frozen |
| Cross-sectional and time-series momentum | active | point-in-time membership and closes are frozen |
| Dynamic two-coin convergence | active | common completed price histories are frozen |
| Spot-perpetual basis or premium index | reserve only | no approved historical spot/premium series |
| Open interest, liquidations, order book, options | forbidden in V3 | absent from the frozen data authority |
| TradFi, metals, indexes, stablecoins | forbidden | outside the A6 native-crypto universe |
