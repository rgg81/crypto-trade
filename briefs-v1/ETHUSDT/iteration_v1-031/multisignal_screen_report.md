# iter-v1/031 — IS-ONLY Screen Report: Multi-Signal ENTRY-LAYER De-Concentrator

**The 4th (and most structural) de-concentration lever.** Decides whether adding de-correlated
deterministic ENTRY signals (Donchian-55, TSMOM-42/21) as INDEPENDENT entry sources is worth a full
backtest. IS-ONLY, no backtest, no `src/` edits.

- Script: `analysis/ETHUSDT/iteration_v1-031/multisignal_entry_screen.py`
- Output: `analysis/ETHUSDT/iteration_v1-031/multisignal_entry_screen.csv` + `..._output.txt`
- Primitives reused verbatim: `analysis/ETHUSDT/iteration_v1-030/multispeed_breadth.py` (`sma_sign`,
  `donchian_breakout_sign`, `tsmom_sign`) + `_common.py` (load/leak-guard/forward-return/concentration).
- Roster anchor for the cadence proxy: `reports-v1/ETHUSDT/iteration_v1-027/in_sample/trades.csv`.

## Verdict: NEGATIVE — do NOT backtest. This closes the obvious structural de-concentration lever.

The de-correlated entry signals ARE independently profitable on ETH IS and DO fire on different
candles than the trend — but combining them as ADDITIVE independent entries **inverts the IS edge**
(combined per-trade Sharpe **−0.29** vs TREND-alone **+0.38**; net **−122%** vs **+153%**). The only
combination rule that preserves IS Sharpe is a **confirmation FILTER**, which REDUCES events — the
opposite of de-concentration. De-concentration of the iter-027 design family via a multi-signal entry
layer is intractable. **Recommend consolidating iter-027 as the ETH ceiling (like BTC iter-020).**

## Leak guards (all PASS)
- Every entry `open_time < OOS_CUTOFF` (1742774400000); horizon-safe via `drop_horizon_crossing_oos`
  (an entry's 14d label `close[t+42]` must stay strictly inside IS). Latest entry across all streams =
  2025-03-09 (TSMOM21) → label ends 2025-03-23, before the 2025-03-24 wall. Assert fires.
- IS frame: 5685 horizon-safe candles, 2020-01-01 .. 2025-03-09. Direction primitives are
  deterministic / parameter-free / past-only (`.shift(1)`), reused verbatim from iter-030.

## Roster-structure finding (fixes the proxy — load-bearing)
The iter-027 IS roster is **82 entries across only 15 same-direction regimes** (avg 5.47 entries PER
regime; median 45-candle ≈ 14d spacing). iter-027 does NOT fire once per trend flip — the LightGBM head
**re-enters a fresh 14d position roughly every time the previous 14d hold closes** while the conviction
gate still passes. A naive "one event per signal flip" proxy under-counts the TREND book to a degenerate
2 events. The screen therefore uses **regime-anchored non-overlapping re-entry**: at each signal's regime
onset, open a 14d position and re-enter every 42 candles within that regime (one position at a time);
a flip resets the clock. This reproduces the ~82-entry cadence AND lets each signal's entries land on
DIFFERENT candles (the independence the premise needs). The SAME rule is applied to every stream.

## 1. Standalone IS profitability (regime-anchored, 14d hold, net of cost)

| stream | events | win rate | per-trade Sharpe (ann) | net Σ | top-2 share (gross \|pnl\|) | HHI |
|---|---|---|---|---|---|---|
| **TREND sma200 gated q40** (incumbent) | 116 | 55.2% | **+0.3837** | +152.9% | 0.0729 | 0.0155 |
| TREND sma200 ungated | 254 | 49.6% | +0.1444 | +117.1% | 0.0311 | 0.0067 |
| DON55 | 393 | 49.6% | +0.0622 | +88.8% | 0.0405 | 0.0055 |
| TSMOM42 | 401 | 49.9% | +0.1669 | +221.6% | 0.0243 | 0.0044 |
| TSMOM21 | 585 | 49.4% | +0.0116 | +24.2% | 0.0249 | 0.0033 |

**Are Donchian/TSMOM independently profitable on ETH IS? YES — but weakly.** All three are net-positive
with positive per-trade Sharpe (DON55 +0.06, TSMOM42 +0.17, TSMOM21 +0.01). Crucially, every independent
stream's per-trade Sharpe is **far below the gated TREND incumbent's +0.38** — they are diffuse, low-edge
event sources (49–50% WR, many more chop entries). This is the seed of the NEGATIVE: their independent
events are low-edge, so ADDING them dilutes.

## 2. Independence (premise check — PASS)
Event-candle Jaccard is near-zero (TREND vs DON55 = 0.026; TREND vs TSMOM21 = 0.019; inter-stream
0.06–0.09). The streams fire on **genuinely different candles** — the premise's de-correlation holds at
the timing level (same-week overlap 0.7–0.9 reflects shared macro regimes, but the candle-level entries
are distinct). So the failure below is NOT "they're secretly the same signal"; it is that the extra
independent events are net-dilutive.

## 3. COMBINED book vs TREND-alone (all rules non-overlapping single-symbol, 14d, net)

| rule | events | win rate | per-trade Sharpe | net Σ | top-2 gross | verdict role |
|---|---|---|---|---|---|---|
| **TREND-alone (gated q40)** | 116 | 55.2% | **+0.3837** | +152.9% | 0.0729 | baseline |
| **COMBINED equal-union** (TREND+DON+TS42+TS21) | 125 | 41.6% | **−0.2909** | **−121.9%** | 0.0628 | the additive-breadth test → **FAILS** |
| VarA conviction-priority union | 116 | 53.5% | +0.5095 | +201.5% | 0.0746 | TREND prioritized → only +10 indep events |
| VarB trend-cadence + 3-of-4 agree FILTER | 107 | 53.3% | +0.7082 | +254.6% | 0.0787 | a FILTER (reduces events) — not breadth |
| VarC trend-cadence + majority-vote DIR | 116 | 54.3% | +0.4451 | +177.2% | 0.0729 | re-votes direction — not breadth |

**Variant A source attribution:** of 116 non-overlapping slots, TREND keeps 106 and the independent
streams contribute only 4+3+3 = 10. Once TREND is prioritized, the independent streams are crowded out by
the 14d non-overlap and add almost no breadth (116 events, same as baseline).

## Pre-registered PASS criterion (on the ADDITIVE equal-union book)
(a) MORE events than TREND-alone, AND (b) LOWER top-2 share, AND (c) per-trade Sharpe ≥ 0 and ≥
TREND-alone − 0.05, AND (upstream) the included streams are standalone-profitable.

| criterion | result | pass? |
|---|---|---|
| (a) more events | 116 → 125 | ✅ |
| (b) lower top-2 (gross) | 0.0729 → 0.0628 | ✅ |
| (c) Sharpe ≥ 0 and bleed ≤ 0.05 | +0.3837 → **−0.2909** | ❌ (inverts) |
| (upstream) streams profitable | DON55/TSMOM42/TSMOM21 all > 0 | ✅ |

**Criterion (c) fails decisively → NEGATIVE.** The combined book de-concentrates (a, b pass) but at the
cost of inverting the edge — exactly the trap the screen was designed to catch.

## Why this fails — the mechanism (does the combination de-concentrate WITHOUT diluting IS? NO)
1. **The additive union is dominated by weak entries.** The independent streams fire 393/401/585 times
   vs TREND's 116, mostly on chop candles (49–50% WR). Under single-symbol non-overlap, whichever
   candidate comes first in time opens the position; the high-count weak streams "win the race" and crowd
   out TREND's high-conviction gated entries. The 116 strong TREND entries collapse to ~106 in the union,
   replaced by ~19 low-edge independent entries → win rate 55%→42%, Sharpe +0.38→−0.29, net +153%→−122%.
2. **De-concentration and edge move in OPPOSITE directions here.** The only thing that lowers top-2 share
   is adding MORE, MORE-DIFFUSE events — but those events are precisely the low-edge ones. You cannot get
   breadth without importing the dilution; the two are mechanically coupled for this signal family.
3. **The signals only help as CONFIRMATION, not as breadth.** Variant B (keep a TREND entry only if ≥3/4
   signals agree) lifts Sharpe to **+0.71** — the de-correlated families carry real *directional*
   information. But confirmation REDUCES events (116→107), the opposite of de-concentration, and does
   nothing for OOS breadth. The information in DON/TSMOM is a *filter* on TREND, never an additive
   independent edge strong enough to widen the book.

This is the same root lesson as the prior three failures, now confirmed at the entry-supply level:
**OOS concentration is intrinsic to the low-WR let-winners-run design.** Three earlier levers re-sliced/
modulated/vetoed the SAME events (meta-label veto, AGREE_SCALE, exit ladder); this 4th lever tried to
ADD independent events — and the only independent events available on ETH are too weak to widen the book
without inverting the edge. Breadth and edge are coupled; you cannot have one without losing the other.

## Proxy-fidelity caveat (pre-registered, per iter-030 Critic rec #1)
This per-candle deterministic proxy does NOT model the LightGBM entry-timing/sizing layer or the
per-month gate. It is a FEASIBILITY screen of the SIGNAL combination, not a backtest prediction. A PASS
would have meant "worth a backtest", NOT a both-positive guarantee (the AGREE_SCALE EDA passed its proxy
yet the backtest inverted IS). Here the proxy returns a **clean, robust NEGATIVE**: the additive
combination inverts IS in the proxy itself, and the only edge-preserving rule (confirmation filter) is
not a de-concentration mechanism by construction. The NEGATIVE does not depend on backtest-layer
subtleties — it is visible in the signal combination's raw forward-return economics.

## Recommendation
**NEGATIVE — do not run an iter-031 multi-signal-entry backtest.** This closes the obvious structural
de-concentration lever for the ETH let-winners-run design. Four de-concentration approaches across four
different families have now failed:

| iter | lever | family | failure |
|---|---|---|---|
| 028/029 | meta-label M2 veto | model-arch | K=20 lottery-collapse |
| 030 | AGREE_SCALE entry-conviction | labeling/conviction | inverted IS (cut chop-regime winners) |
| 031a | exit-side partial ladder | execution/exit | re-slices one winner; 0.63× downsize, clips right tail |
| 031b (this) | multi-signal additive entry | feature/entry-supply | inverts IS; breadth ⊥ edge coupled |

**Consolidate iter-027 (IS +0.6336 / OOS +0.0560) as the ETH ceiling**, mirroring the BTC iter-020
decision (BASELINE_V1_ETHUSDT caveat #2 already records the OOS concentration as an *intrinsic structural
property* of the let-winners-run design, not a defect under the generalization-first gate). The thin OOS
is the price of a deterministic, both-positive, K=20-confirmed edge; trying to broaden it has now been
shown to either invert IS or merely downsize.

### If the campaign still wants to pursue ETH robustness, pivot the AXIS (not the de-concentration goal):
- **Direction-robustness K=5 screen** (BASELINE next-step #2): swap `trend_state_symbol`→BTC (cross-asset
  regime) or SMA window 100/300 — tests the one deterministic primitive the edge rests on. This is a
  *robustness* axis, not a *breadth* axis, and does not fight the intrinsic concentration.
- **Genuine multi-outer-seed validation** of iter-027 (BASELINE next-step #3; the basin diagnostic is
  vacuous at outer-seeds=1). Quantifies how fragile the thin OOS actually is rather than trying to fix it.
- **Variant B as a confirmation refinement of iter-027** (NOT a de-concentrator): a 3-of-4 deterministic
  agreement *gate* on top of the existing conviction gate lifted the IS proxy Sharpe to +0.71. This is an
  edge-strengthening / entry-quality axis, not de-concentration — and it would need its own IS-only screen
  modeled on the LightGBM-signaled candles (the iter-030 lesson: confirmation that re-ranks model entries
  can still invert IS). Worth noting as a candidate, but it does NOT address the user's broad-OOS mandate.

The user's specific de-concentration mandate (a BROAD, robust OOS for ETH) is, on this evidence,
**intractable for the iter-027 design family**. The honest finding is that broadening the OOS requires a
*different edge*, not a modification of this one.
