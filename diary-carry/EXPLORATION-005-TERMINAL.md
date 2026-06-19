# carry-iteration EXPLORATION-005 + TERMINAL VERDICT — per-coin beta-neutral harvest; carry-as-alpha CLOSED

**Axis:** the last untried honest form — remove market beta PROPERLY (per-coin, time-varying,
past-only rolling beta vs BTC; hedge the book's net beta in BTC) and ask whether the real,
regime-stable funding INCOME survives as a clean beta-neutral edge. Code: `analysis/carry_beta_neutral.py`.

## Result
| | dollar-neutral (raw) | per-coin BETA-NEUTRAL |
|---|---|---|
| no floor | IS +1.38 / OOS +1.04 | IS +1.24 / OOS **+0.43** |
| $5M floor | IS +1.19 / OOS −1.03 | IS +1.16 / OOS **−0.79** |

median |portfolio beta| was only 0.06–0.12 — the dollar-neutral book was ALREADY ~beta-neutral, so
hedging removes only a small residual and slightly LOWERS the no-floor OOS (+1.04→+0.43: part of the
no-floor edge WAS that residual beta). At tradeable size ($5M), beta-neutral OOS is **−0.79** — still
negative.

## TERMINAL VERDICT — broad funding carry is NOT a deployable scalable alpha (axis CLOSED)
Across the FULL gauntlet — realistic engine, walk-forward (bias-free), 572-coin survivorship-clean
universe, capacity floors, per-leg, alpha-vs-beta, and now proper per-coin beta-neutralization — the
broad cross-sectional funding carry does NOT survive as a clean, capacity-respecting, beta-neutral
positive-OOS edge:
- Funding INCOME is real + regime-stable (OOS funding-only Sharpe ~+6.6) — but mechanically
  inseparable from the price/squeeze exposure that carries it.
- That price exposure is alt-BETA (no funding-selection alpha over long/short-ALL, EXPLORATION-004),
  concentrated in ILLIQUID coins (a liquidity floor inverts net OOS, critic), and the residual is not
  rescued by proper beta-hedging (this run).
- The early +0.96/+2.61 headlines were survivorship + un-hedged alt-beta + illiquid-coin premium.

The METHODOLOGY stayed clean throughout (critic: leak-free, bias-free, bit-reproducible). The EDGE
is what failed — honestly, under scrutiny, not by a bug. Deploy (#168): **NO.**

## What remains genuinely honest (NOT the cross-sectional perp-perp carry)
The funding income's CLEAN, capturable cousin is the **cash-and-carry / spot-perp basis**: hold SPOT,
short the PERP, collect funding with the price leg hedged 1:1 by spot (no squeeze, no beta, capacity =
spot liquidity). That is the textbook way to harvest funding and is the ONLY remaining honest version —
but it needs SPOT data (fetch-spot) which we have not prepared broadly. That is the recommended next
direction; the perp-perp cross-sectional carry axis is closed.
