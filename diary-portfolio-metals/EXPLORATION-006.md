# EXPLORATION-006 — Ideation panel + 6-candidate bake-off + ML → FRONTIER (airtight)

**Track:** metals portfolio. **Date:** 2026-06-25. User directive: "try a bit more, ask the agents for
ideas, ML can be a good try."
**Verdict:** ⛔ **FRONTIER CONFIRMED (airtight)** — Critic CONCURS. 6 candidates tested, ALL negative;
**0 new sleeves; ML NULL (fair).** Book stays the 4-sleeve iter-004 at **IS +0.641**. OOS hidden.

## What we did
Asked a 3-agent ideation panel (macro/flow, microstructure/statistical, portfolio-construction/ML
lenses) for bold untried law-compliant ideas, then bake-off-tested the best 5 + the user-requested ML
synthesis. Net 6bps/side, IS-only, leak-safe, parity-correct (`book_head + δ·gn(new) → ONE
net_from_raw`), both pre-registered falsifiers (gold/silver deep-history lift>0; IS half-split no
sign-invert). Bar to beat: combined ≥ +0.701.

## The 6 candidates — all NEGATIVE, distinct failure mechanisms tiling the space
| # | Candidate | Mechanism | Best combined lift | Why it died |
|---|---|---|---|---|
| A | XS-COT dispersion | rank metals by MM-z, demean, $-neutral | +0.037 | degenerate at 2-name deep history; 4-metal lift post-2022/OOS-adjacent; fails both falsifiers |
| B | Residual reversion (PCA/common-factor-removed) | trade idiosyncratic residual | −0.176 | real but ~1-bar fast (gross +0.2) → **cost-killed** at any turnover ≥ book (the structural law) |
| C | NY-session slow tilt | standing weekly-updated NY-bar long-tilt | −0.009 | NY premium real (gold t=3.84) but **anchor-collinear** (residual Sharpe 0.00) |
| D | Gold-silver COT pair-spread | z_gold − z_silver, $-neutral pair | ≤+0.001 | **identical to A's deep core (corr +1.0000)**; gold/silver MM co-driven → relative crowding is noise |
| E | Commercial-vs-MM divergence | hedger-vs-spec disagreement spread | +0.059 | **corr +0.892 to the iter-004 COT sleeve = redundant** (mirror-break is magnitude=no-op); fails falsifiers |
| ML | depth-2 monotone LightGBM | XS-rank target on 7 sleeve-state features, WF+purge+embargo | −0.039..−0.077 | **≤ ridge null at every δ → nonlinearity INERT**; book +0.985 self-correlated → ML rediscovers linear weights |

## The conclusion — the binding constraint is the DATA CLASS, not the modelling
Every candidate is a re-transform of the same **4-metal 8h OHLCV + weekly COT** (managed-money +
producer/merchant cohorts). The +0.641 book has extracted the affordable, time-stable LINEAR edge from
it. The distinct failures tile the space: A/D = relative-crowding degenerate at 2-name deep history;
B = residual reversion cost-killed; C = session premium anchor-collinear; E = commercial cohort is the
OI-mirror of MM (redundant); ML = nonlinearity inert on a near-optimal linear book. This is the SECOND
independent frontier confirmation (iter-005 = non-price axis exhausted at COT; iter-006 = new signals +
ML exhausted). To break it requires a genuinely EXOGENOUS, low-turnover data class — not another
transform of the 4-metal price/COT panel.

## ML verdict — NULL, and FAIR (Critic-verified, since the user specifically asked)
The Critic forensically verified the ML gate was NOT rigged: the +0.06 bar was the same every candidate
faced (ML failed by a wide negative margin, not a hair); the target (cross-sectional rank of forward
return) is the correct generous XS target; depth-2 monotone is anti-overfit not starvation (the **ridge
null controls for it — LightGBM ≤ ridge at every δ is dispositive that nonlinearity is inert**);
walk-forward is leak-safe (expanding, quarterly refit, 2-candle purge+embargo > the 1-candle label
horizon, IS-only). The ceiling isn't model capacity — it's cross-sectional shape in the data, which the
diagnostic measured directly (common-factor variance share 0.64). **A legitimate, well-instrumented NULL
— the linear sum is near-optimal for these signals.**

## Critic note (CONCUR — frontier + ML-null sound)
Harness parity-verified (single net_from_raw, leak-safe, honest reporting surface — not an artifact
hiding edges). A/B/C/D/E each correctly killed (degeneracy / cost-law / anchor-collinearity /
A-identity / redundancy). The two candidates the Critic flagged as "not cleanly run" (D pair-spread,
E commercial-divergence) were then run → both NEGATIVE, closing the in-scope frontier airtight.

## Path forward — the disciplined call is CONFIRMATION
There is **no net-positive, orthogonal, time-stable new sleeve to confirm**. The honest closeout of this
cycle is a **CONFIRMATION = multi-seed / OOS re-validation of the existing +0.641 4-sleeve book itself**
(no new ingredient): reveal the held-out OOS (2025-03-24+) under the same engine, check the two
falsifiers hold OOS, full gauntlet (per-year, cost-stress, benchmarks, DSR-deflation). **This is the
user's "show OOS only at the end" call.** Breaking scope (metals-perp funding/basis — but Binance perps
are ~5mo old = thin + user said don't focus on funding; cross-asset macro — but real-rates/DXY decoupled
post-2022 = OOS trap; copper universe expansion — breaks Binance live-parity) all carry material caveats
and would need user sign-off.

## Files
- `analysis/portfolio/metals/iter_006_ml_diag.py` (committed IS-only diagnostic: sleeve-state feature
  panels + common-factor-share measurement). No new sleeve. Bake-off harness was scratch (not committed).
