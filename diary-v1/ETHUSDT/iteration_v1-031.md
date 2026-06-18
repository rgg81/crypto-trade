# Diary — iter-v1/031 (ETHUSDT) — DIAGNOSIS (research-only, 2 IS screens) — CAMPAIGN-CLOSING (ETH de-concentration is INTRACTABLE for the proven design family)

**Axis:** two IS-only de-concentration feasibility screens (no backtest), to find a lever that BROADENS
the iter-027 OOS (user mandate: succeed where BTC couldn't = a broad, robust OOS) WITHOUT the failure
modes of iter-028/029 (M2 veto K=20 lottery) and iter-030 (AGREE_SCALE IS inversion). Screened on
iter-027's realized roster + ETH IS forward-return economics.

**Outcome: BOTH NEGATIVE. The ETH OOS concentration is INTRINSIC to the low-WR let-winners-run design;
broadening it is intractable for this design family. iter-027 is the ETH breadth CEILING (like BTC iter-020).**

## Screen A — EXIT-side partial-profit ladder (execution/exit-primitive) → NEGATIVE
Convert each 14d capture into 2-3 realized sub-trades (⅓ at +1.5/+3 ATR, rest to exit). It cannot invert
IS (entries unchanged) — but it also cannot help:
- 3-leg bleeds IS Sharpe +0.57→+0.38 (Δ −0.19); 2-leg "passes" the literal ≤0.05 criterion (Δ −0.006)
  but is a METRIC FALSE POSITIVE: a control scaling the unchanged iter-027 book by 0.63× gives the
  identical Sharpe (Sharpe is scale-invariant) — the 2-leg ladder ≈ a 0.63× position downsize bought
  with extra turnover + multi-fill engine complexity. Net Σ falls 37%; the right tail (the let-winners-run
  edge) is amputated.
- **Root mechanism:** an exit ladder re-slices ONE winner's path into CORRELATED legs — it cannot create
  more INDEPENDENT winning events, so monthly-series concentration barely moves while the edge bleeds.

## Screen B — MULTI-SIGNAL entry combination (entry-signal / Carver-AQR multi-rule) → NEGATIVE
Add de-correlated deterministic entry signals (Donchian-55 breakout, TSMOM-21/42) as INDEPENDENT entry
sources to create more independent events:
- The signals ARE genuinely independent in timing (TREND-vs-each event-candle Jaccard 0.02-0.03 — the
  de-correlation premise holds) and each is net-positive standalone — BUT WEAK: per-trade Sharpe DON55
  +0.06 / TSMOM42 +0.17 / TSMOM21 +0.01, all far below the gated TREND incumbent +0.38.
- The additive union DE-CONCENTRATES (top-2 0.073→0.063, events 116→125) but INVERTS THE IS EDGE
  (Sharpe +0.38→−0.29, net +153%→−122%, WR 55%→42%): under single-symbol non-overlap the high-count
  weak streams win the race to open positions and CROWD OUT TREND's high-conviction gated entries.
  Breadth and edge move in OPPOSITE directions for this signal family.
- The only edge-preserving use of DON/TSMOM is as a CONFIRMATION FILTER (≥3/4 agree → Sharpe +0.71) —
  which REDUCES events (116→107), the opposite of de-concentration. No rule both adds breadth AND
  preserves edge.

## CAMPAIGN-CLOSING: ETH de-concentration is COMPREHENSIVELY EXHAUSTED (4 families)
| family | iteration | mechanism | failure |
|---|---|---|---|
| model-arch (veto) | /028-/029 | M2 meta-labeling veto | K=5 OOS was a K=20 basin-lottery (+0.21→+0.04) |
| labeling/conviction | /030 | AGREE_SCALE entry-conv modulation | inverts IS (de-correlates from the model's overfit entry edge) |
| execution (exit) | /031-A | partial-profit ladder | re-slices one winner; clips the right tail; ≈ 0.63× downsize |
| entry-signal | /031-B | multi-signal entry combination | de-correlated signals too WEAK; crowd out TREND; invert IS |

**Root cause (mechanistically grounded, 4×):** OOS breadth = MORE INDEPENDENT WINNING EVENTS. Every
within-structure mechanism (veto / modulate / re-slice / add-weak-signals) operates on the SAME
~82-IS/~32-OOS trend-capture event set and cannot manufacture independent events without either
diluting the edge or amputating the right tail. **The thin, concentrated OOS is the structural PRICE of
a deterministic, both-positive, K=20-confirmed let-winners-run edge.** iter-027 (IS +0.6336 / OOS
+0.0560) STANDS as the ETH breadth CEILING — exactly parallel to BTC iter-020.

## The honest strategic fork (surfaced to the user)
Breadth is intractable for the PROVEN let-winners-run trend family — NOT necessarily for ETH. A genuinely
BROAD ETH OOS would require a DIFFERENT EDGE (a new strategy family — shorter-horizon/higher-frequency,
mean-reversion, or microstructure — that produces many independent events), which is a bigger creative
bet than a single-axis tweak. Three forward paths:
1. **Different edge for breadth** (ambitious, user's "succeed where BTC couldn't" intent): build a new
   ETH strategy family with intrinsically more independent events (e.g. shorter-horizon momentum, or a
   mean-reversion edge on the funding/liquidation microstructure). Big bet; fresh design.
2. **Accept iter-027 as the ETH ceiling** (parallel to BTC iter-020): the both-positive SIGN is the
   durable claim; thin OOS is intrinsic. Consolidate and move to the next coin.
3. **Pivot breadth → robustness** (the BASELINE's own Critic next-steps #2/#3, don't fight the intrinsic
   concentration): direction-robustness K=5 swap (trend_state_symbol→BTC, or SMA 100/300); genuine
   multi-outer-seed validation of iter-027.

**OOS-vigilance:** both screens were IS-only (cutoff-asserted, leak-guarded); the proxy-fidelity caveat
(per-candle deterministic ≠ backtest) is recorded but the NEGATIVE is robust to it — the IS inversions
are visible in the raw forward-return economics, not a backtest-layer subtlety.

**Methodology working:** 2 cheap IS-only screens saved 2 full backtests (~1.5-2h compute) by killing the
exit-ladder and multi-signal axes pre-backtest. The de-concentration mandate received an exhaustive,
honest test across 4 mechanism families before the intractability conclusion — not a premature give-up.
