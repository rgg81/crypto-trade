# carry-iteration EXPLORATION-002/003 + CRITIC — agent-team improvement pass on the walk-forward baseline

Baseline: bias-free walk-forward carry (`carry_walkforward.walkforward_book`), net IS +1.15 / OOS
+0.96 / DD −37%, positive every year. Three agents ran in parallel to improve it.

## quant-critic — HONESTY VERDICT: **BLOCK** (on deployability, NOT on the math)
- **Walk-forward is LEAK-FREE + bias-free (PASS).** Empirically: corrupting ALL rows ≥ OOS_CUTOFF
  leaves the IS net bit-identical (max|diff| 3.5e-18) and IS weights exactly unchanged; divergence
  begins exactly 2 candles early (the legitimate open.shift(-2)/shift(-1) hold footprint), so
  GAP_CANDLES=3 is a sufficient embargo. Engine + walk-forward are honest + bit-reproducible. 10/10 tests.
- **BLOCKER = REALIZABILITY.** The baseline uses NO liquidity floor, and the carry premium lives
  ENTIRELY in coins you can't trade at size. A realistic floor INVERTS the net OOS:
  no floor +1.76 → $5M **−0.11** → $20M **−0.64** (DD −77%) → $50M **−0.72** (DD −86%).
  funding-only stays + (real income) but the deployable NET edge vanishes under any tradeable floor.
- Survivorship (delisted coins absent from disk) = optimistic but documented caveat, not a leak.
  "funding-only Sharpe +6.6" = a diagnostic, not the realizable Sharpe (overstates ~6×).

## quant-researcher — short-leg enhancements: mostly NEGATIVE; 1 keeper; pivot the leg
- Decomposition (IS): LONG leg = price HERO **+309%**; SHORT leg = drag (−54% price) but biggest
  income (**+94% funding**). The short price-loss and funding-income are the SAME crowded-long
  position; the drag is DIFFUSE alt-beta (worst 1% candles = 12% of loss), not an avoidable tail.
- Axis 1 name-picking NEGATIVE (funding-z catastrophic; momentum guards worse). **KEEPER: funding-
  PERSISTENCE ranking** = equal Sharpe (+1.37) at **15% lower turnover** → better cost realizability.
- Axis 2 beta marginal/neg; Axis 3 alt-rally brake = return/risk rebalance, no alpha.
- → short-leg axis EXHAUSTED; **pivot to the LONG leg** (the +309% engine, untouched).

## risk-engineer — the −37% DD is INTRINSIC, resists all controls
- per-coin cap: full DD unchanged; inverse-vol: DD TRAP (−67%); dd-brake@floor0: over-brakes to flat;
  **beta-hedge BTC/ETH KILLS OOS (+0.96→+0.09)** → the squeeze is NOT market beta, it's idiosyncratic;
  vol-ceiling p75 (best): −37%→−35% only, at OOS +0.96→+0.74. (b)+(a) inverse-vol+cap lifts OOS to
  +1.40 but DD −62% (return/risk trade, not a DD cut). The squeeze == the income → can't cheaply remove.

## SYNTHESIS — the honest state
The carry **methodology is clean** (critic: no leak, no bias, walk-forward sound) — but the
**deployable edge is capacity-killed**: under any realistic liquidity floor the net OOS goes
negative, because the premium is concentrated in untradeable illiquid coins. The DD is intrinsic and
the short-leg squeeze is the same trade as the income, so neither improves cheaply. Net: the broad
short-high-funding carry is a REAL signal but **NOT deployable at size as built**.

## Verdict & next
- EXPLORATION-002 (DD) / 003 (enh): EXPLORATION-NEGATIVE — improvement axes on the SHORT side are
  exhausted; DD is intrinsic.
- Funding-persistence ranking = the one strictly-accretive keeper (cost realizability).
- The real open lever = the **LONG leg** (+309% IS price hero, untouched) — is a long-tilted /
  long-only-of-low-funding-LIQUID-majors book capacity-friendly AND positive net? That is the next
  EXPLORATION, and it directly targets the critic's realizability blocker (longs can be the liquid majors).
- Deploy decision (#168): as-is, NOT deployable at size. Re-baseline the headline WITH a liquidity
  floor (honest number is ≤ 0 net under $5M) before any deploy talk.
