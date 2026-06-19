---
name: carry-iteration
description: >
  Market-neutral FUNDING-CARRY research/iteration track. The one durable edge found across the
  whole strategy search: short the highest-funding coins / long the lowest, dollar-neutral, on a
  REALISTIC execution engine. Use whenever the user mentions: carry, funding carry, market-neutral,
  cross-sectional carry, broad_carry, pair_engine, pair carry, carry iteration, carry drawdown,
  carry skill, or asks to iterate / improve / deploy the market-neutral carry book.
model: opus
---

# Carry Iteration — market-neutral funding-carry track

## Mission
After trend, single-coin LightGBM, cross-sectional momentum and pair-momentum all FAILED the
anti-hype gauntlet, the **broad cross-sectional funding carry** is the one durable, structural,
regime-robust edge. Crowded longs pay shorts every 8h; we harvest that spread dollar-neutral so
price is hedged. The income is OBSERVED, not predicted — that is why it generalizes where price
prediction did not.

**Verified baseline (realistic engine, 40 funding coins, M=9, FRAC=0.25):** net IS Sharpe +1.35 /
OOS +2.61, positive EVERY year 2020-2026; funding-only IS +4.42 / OOS +5.29 (IS monthly t=+10.12).
Open weakness = **-32% drawdown** (short-squeeze price tail) — the active research axis.

## Foundation (the code; all on the realistic engine, all tested)
- `analysis/pair_engine.py` — REALISTIC execution: decide close[t] → fill open[t+1] → hold candle
  t+1; real 8h funding settlement; 0.07%/side cost (fee 0.1% rt + 2bps/side slip = live-engine
  convention); strict no-look-ahead. Tests: `tests/test_pair_engine.py` (6).
- `analysis/broad_carry.py` — the canonical strategy: `build_book()` → net + (price,funding,cost)
  decomposition + per-coin weights; `evaluate()` → the gauntlet. Tests: `tests/test_broad_carry.py` (4).
- `analysis/carry_broad_vs_pairs.py` — broad-vs-selected head-to-head (broad wins OOS 4×).
- `analysis/funding_carry_pit.py` / `_tail.py` / `_sensitivity.py` — point-in-time, tail/squeeze,
  parameter-robustness checks.

## The anti-hype gauntlet (a change is "real" ONLY if it clears ALL of these)
1. **Realistic engine** — next-bar-open fills + real funding + per-leg cost. NEVER the close-to-close
   proxy (it flattered the search 13/20 → realistic 9/20). This is non-negotiable.
2. **IS-only selection / IS-only weights** — never select coins/pairs/params on OOS (the bundle
   selection-bias lesson). EXPLORATION ranks on IS; CONFIRMATION reveals OOS once.
3. **Non-overlapping significance** — funding-only monthly t-stat (overlapping t-stats are inflated
   ~√N; a t=5 mirage collapsed to 0.3 on independent samples).
4. **Regime robustness** — net positive across a MAJORITY of calendar years, not one lucky slice.
5. **Null** — beat a sign-shuffled / random-ranking null; beat buy-and-hold.
6. **Realizability** — report maxDD + cost-stress (1×/2×/4×) + capacity (position vs trailing
   volume). The backtest Sharpe is OPTIMISTIC; deploy on the discounted number.

## Iteration cadence
- **EXPLORATION** — one change at a time (a new signal, a DD control, a universe/param tweak),
  scored IS-only + the gauntlet checks that don't need OOS. Cheap, frequent.
- **CONFIRMATION** — reveal OOS + full gauntlet (regime, null, tail, cost). Only a CONFIRMATION
  promotes a change into the baseline `broad_carry.py` defaults.
- Commit each step with the honest result (including negatives). No silent caps.

## Sacred constants / no-cheating
- `OOS_CUTOFF = 2025-03-24` (immutable). Cost = 0.07%/side (live-engine convention).
- All signals past-only (`<= close[t]`); fills at `open[t+1]`. Leak-tested.
- Never tune on OOS; never trim the window; report DD + realizability, not just Sharpe.

## Run
```
uv run pytest tests/test_pair_engine.py tests/test_broad_carry.py -q   # foundation must stay green
uv run python analysis/broad_carry.py                                  # baseline gauntlet
uv run python analysis/carry_broad_vs_pairs.py                         # broad vs selected
```

## Open axes (priority)
1. **Reduce the -32% drawdown** WITHOUT killing the carry: per-coin weight caps, gross-exposure /
   vol-target ceiling, drawdown brake, wider FRAC, exclude extreme-funding squeeze magnets.
2. Capacity/squeeze realizability → realizable-Sharpe estimate.
3. Engine integration (live market-neutral carry book) — user green-light required.
