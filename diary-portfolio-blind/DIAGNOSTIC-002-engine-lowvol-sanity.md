# DIAGNOSTIC-002 — foundation engine built + low-vol L/S sanity (IS, funding OFF)

**Date:** 2026-07-09  **Phase:** foundation build + first costed sanity (pre-EXPLORATION)
**Scripts:** `analysis/portfolio/blind_universe.py`, `analysis/portfolio/blind_engine.py`,
`analysis/portfolio/blind_sanity_lowvol.py`, `tests/test_blind_engine.py`

## Foundation (signal-agnostic — reused every iteration; built blind from first principles)
- `blind_universe.py` — loads all coins aligned on the BTC 8h grid; PIT top-20 by trailing
  30-candle $-volume, ex-stablecoins; IS mask.
- `blind_engine.py` — realistic-cost L/S backtest: rank-based **dollar-neutral** target weights
  (sum w=0, sum|w|=gross) → decide at close[t] → **fill at open[t+1]** → hold open[t+1]→open[t+2]
  → **taker fee + slippage on one-way turnover** → **funding on perp legs** (asof, optional) →
  optional portfolio vol-target → Sharpe / maxDD / turnover / per-year / vs B&H-BTC.
- Leak-safe by construction (signal past-only; 1-candle decision/fill lag).
- **Tests: 5/5 green** incl. the mandatory leak check (corrupt ALL inputs from a cutoff forward
  → every past decision bit-identical), dollar-neutrality, cost-monotonicity, zero-signal.

## Low-vol L/S sanity — IS-only, funding OFF (3 rebal cadences, gross 1.0)
B&H BTC IS baseline: **Sharpe +1.07, ann +60%** (2020→2025-03 is a strong bull window).

| rebal | Sharpe | ann | maxDD | turn/yr | 2020 | 2021 | 2022 | 2023 | 2024 | 2025Q1 |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| 1 | −0.45 | −27% | −94% | 236x | −1.55 | **−3.37** | +1.30 | −0.54 | +1.11 | +2.03 |
| 3 | −0.07 | −13% | −83% | 148x | −1.18 | −1.99 | +1.44 | −0.09 | +0.57 | +2.75 |
| 6 | +0.14 | −4% | −77% | 108x | −0.36 | −1.86 | +1.46 | +0.22 | +0.83 | +1.94 |

gross leverage stays ~1.0 (max 1.0–1.6, no drift bug) → the −94% maxDD is **real regime exposure**,
not an accounting artifact.

## Findings

1. **Naive low-vol dollar-neutral L/S is REGIME-FRAGILE.** Annihilated in the 2020–2021 mania
   (meme/ICO/degen super-cycle where the highest-vol lottery coins mooned → short book destroyed),
   profitable in calmer/bear years (2022, 2024, 2025). Fails the brief's robustness constraint
   standalone. This is economically sensible: low-vol premium exists but gets crushed when retail
   mania drives lottery coins parabolic.
2. **CRITICAL methodological insight — rank-IC ≠ L/S P&L in skewed crypto cross-sections.**
   DIAGNOSTIC-001 showed vol_low rank-IC **positive every year incl. 2020 (+.038) / 2021 (+.068)**,
   yet the L/S Sharpe is deeply negative those years. Cause: rank-IC is median-based and robust to
   magnitude, but equal-dollar **shorting the highest-vol decile incurs fat right-tail risk** (the
   coins that 10–100×). Positive monotone association coexists with negative extreme-tail P&L.
   **Lesson: future signal screens must also report top-decile-vs-bottom-decile MEAN spread
   (not just rank-IC) to catch skew traps.**
3. **Universe is very churny:** 289 distinct members over IS (394 full-sample). Volume-rank entry
   correlates with pumping → adverse selection (a coin spikes into the top-20, gets shorted at the
   top). Reducing churn (hysteresis, or **OI-based ranking** — see below) is a lever.
4. **Turnover is high** (108–236x/yr) even for "slow" low-vol — rank weights jiggle each candle.

## Data discovery (amends the brief)
`fetch-oi` pulls **historical open-interest from data.binance.vision daily archives** → 8h. The
brief's "OI not available (Binance keeps ~30d)" applies only to the LIVE API; the archive has full
history. → A later EXPLORATION can use **true top-20-by-OI** (less adverse-selected than volume).

## Funding ON — resolves the caveat (result: funding is a NET DRAG, not a rescue)
Fetched funding for all 394 union symbols (100% IS-slot coverage); leak-safe **bucket-sum** of
all settlements per hold window (`blind_funding.py`, correct for any cadence). Mean funding/8h by
year: 2020 +0.0018%, **2021 +0.0112%** (mania), 2022 −0.0027%, 2023 +0.0019%, 2024 +0.0075%,
2025 −0.0060%.

Hypothesis was that 2021's high positive funding (shorts earn) would soften the mania loss.
**Wrong:**

| rebal=6 | Sharpe | 2021 | 2022 | 2023 | 2025Q1 |
|---|--:|--:|--:|--:|--:|
| funding OFF | +0.14 | −1.86 | +1.46 | +0.22 | +1.94 |
| funding ON | **−0.18** | −1.83 | **+0.94** | **−0.61** | **+1.35** |

Why: the book is long-low-vol / short-high-vol. Funding is **pro-cyclical to the short pain** —
barely dents the mania loss (2021 −1.86→−1.83) but **erodes the good years** because in bear/calm
regimes (2022, 2025) funding goes *negative* and the short leg pays it (2022 +1.46→+0.94,
2025 +1.94→+1.35). The short book's funding income doesn't concentrate where the price pain is.
Sign convention verified (short w<0 × positive funding → gain). **Naive low-vol L/S is not viable
even with proper funding — the short-side tail risk + regime exposure dominate.**

## Verdict → EXPLORATION-001 (re-framed)
The hypothesis is no longer "low-vol works" but: **low-vol's cross-sectional IC is real but the
naive L/S is destroyed by (a) short-side tail risk in mania and (b) high/adverse-selected turnover.**
EXPLORATION-001 (full agent team: QR designs, QE+risk-engineer implement, Critic reviews) tests ONE
change to address the regime fragility — candidates: tail-risk-capped shorts (don't short extreme-
vol lottery names; cap position contribution), a mania regime gate, or a low-vol long-tilt vs a
risk-managed short. Pre-register MERGE/NO-MERGE criteria before any OOS reveal. Funding ON.
