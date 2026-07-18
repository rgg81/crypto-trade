# Team 05 pivot-02 — Liquidity Depth Migration

This is Team 05's final permitted mechanism pivot. It is prospective and unregistered; no LDM
performance result exists.

Pivot-01 UDCC was solvent and positive overall but failed its noncompensatory center: net Sharpe
0.558394 was below 0.75, only two regimes had positive Sharpe, and the worst regime was -0.408613.
Its fixed rules prohibited controls, neighbors, sign flips, and same-family replacement.

LDM is genuinely different. It compares median unsigned `log(high / low)` range per
contemporaneous cross-sectional quote-volume share over a 105-bar baseline and a disjoint 21-bar
recent window. Improving depth ranks long and deteriorating depth ranks short. No return direction,
close location, taker imbalance, funding, beta, residual shock, trend, reversal, volatility rank,
diffusion, or lead-lag feature enters the score.

Only `team05-ldm-pivot02-core-v1` with the byte-exact no-control policy is authorized. It must pass
every gate in `qualification_thresholds.json`. Failure makes Team 05 DNF immediately; no control,
ablation, parameter neighbor, sign flip, same-family replacement, or further pivot may run.

The universe comes only from Amendment 0006 organizer membership and therefore contains native
crypto assets, excluding stablecoin bases and all TradFi, metals, commodities, and indexes even
when exchange-listed as perpetuals. Amendments 0005–0007 are active. Amendment 0008 is historical
CRTR-only authority. No private or OOS data may be accessed before formal development qualification.
