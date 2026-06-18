# iter-v1/031 — IS-ONLY Screen Report: Exit-Side Partial-Profit Ladder De-Concentrator

**Critic Path-Forward #1 screen.** Decides whether iter-031 (a deterministic partial-profit ladder on
the EXIT side) is worth a full backtest. IS-ONLY, no backtest, no src/ edits.

- Script: `analysis/ETHUSDT/iteration_v1-031/exit_ladder_screen.py`
- Output: `analysis/ETHUSDT/iteration_v1-031/exit_ladder_screen_output.txt`
- Source roster: `reports-v1/ETHUSDT/iteration_v1-027/in_sample/trades.csv` (82 IS trades)
- Path data: `data/features/ETHUSDT_8h_features.parquet`

## Leak guards (all PASS)
- All 82 trades IS: max `open_time` 1742716799999 < OOS_CUTOFF boundary 1742774400000. PASS.
- Entry alignment verified: `trade.open_time == entry-candle close_time` (100% join) and
  `entry_price == entry-candle close` exactly (max diff 0.0) — entries fill at candle close.
- SL distance `== 1.45 × vol_natr_21` at entry (ratio mean 1.4500, std ~1e-9) — confirms iter-027's
  NATR21 SL. Ladder ATR levels use the **entry-candle ATR14** (known at entry; path walked on
  SUBSEQUENT candles only — no same-bar look-ahead).
- Costs modeled honestly: 0.07%/fill (fee 0.05% + slip 2bps). Entry charged once; **each realized leg
  pays its own exit fill**. A non-runner (1 leg) pays 0.14% == iter-027 single-exit exactly; a 3-leg
  runner pays 0.28% (+0.14% extra turnover). This drag is the cost the screen weighs.

## Comparison table (IS-only)

| book | rows | extra legs | net Σ | monthly Sharpe | win rate | top-2 share (gross \|pnl\|) | top-2 share (net) | HHI \|pnl\| |
|---|---|---|---|---|---|---|---|---|
| **iter-027 single-exit** | 82 | 0 | **+100.82%** | **+0.5690** | 34.1% | +12.58% | +71.40% | 0.0240 |
| 3-leg raw (⅓@1.5, ⅓@3.0) | 148 | 66 | +37.83% | +0.3827 | 63.5% | +5.23% | +63.55% | 0.0098 |
| 3-leg natr (⅓@1.5, ⅓@3.0) | 151 | 69 | +44.44% | +0.4513 | 64.2% | +5.22% | +54.10% | 0.0097 |
| **2-leg raw (½@2.0)** | 119 | 37 | +63.66% | **+0.5627** | 54.6% | +7.33% | +56.65% | 0.0126 |
| 2-leg natr (½@2.0) | 119 | 37 | +58.76% | +0.5216 | 54.6% | +7.38% | +61.37% | 0.0126 |

Runner diagnostic (3-leg raw): 40/82 trades (49%) trigger ≥1 partial; 26/82 (32%) trigger both; the
other 42 are non-runners that behave as the unchanged single-exit.

## Pre-registered PASS criterion (Critic)
(a) REDUCE top-2 share vs iter-027 IS **AND** (b) IS net monthly Sharpe bleed ≤ 0.05.

| variant | top-2 reduced? | Sharpe Δ | bleed ≤ 0.05? | literal verdict |
|---|---|---|---|---|
| 3-leg raw | yes (−7.4pp gross) | −0.1863 | no | NEGATIVE |
| 3-leg natr | yes | −0.1176 | no | NEGATIVE |
| **2-leg raw** | yes (−5.3pp gross) | **−0.0063** | **yes** | **PASS** |
| 2-leg natr | yes | −0.0473 | yes | PASS |

By the literal Critic criterion, the **2-leg variants PASS** and the 3-leg variants are NEGATIVE
(the 3rd leg's extra turnover bleeds Sharpe far past the 0.05 tolerance).

## Verdict: NEGATIVE (mechanistically) — DO NOT backtest. Pivot to Path Forward #2.

The 2-leg literal PASS is a **false positive of the metric**, and the honest read kills it. Three
load-bearing findings:

**1. The Sharpe is preserved only by proportional shrinkage, not by genuine de-concentration.**
The 2-leg-raw monthly series: mean 2.725→1.720 (ratio **0.631**), std 16.590→10.592 (ratio **0.638**).
Mean and std collapse in near-perfect proportion, so the ratio (Sharpe) is mechanically unchanged. A
control confirms it: scaling the **unchanged** baseline book by 0.63× (no ladder, no extra cost) gives
monthly Sharpe **+0.5690 — identical to the baseline**, because Sharpe is scale-invariant. The 2-leg
ladder's +0.5627 is, to within rounding, **just a 0.63× downsize of iter-027** — purchased with extra
turnover and far more execution complexity than simply trading a smaller size. The ladder buys nothing
a `position *= 0.63` wouldn't, and costs more.

**2. The "de-concentration" is dominated by winner-clipping, which is the wrong lever for a
let-winners-run edge.** Delta decomposition (2-leg raw): winners lose −86.03 pct of net (giving up
upside above the ladder level on half the position), losers recover only +48.87 pct. Net Σ falls 37%.
The top baseline winner (+39.20%) becomes +17.70% — the ladder structurally **caps the very
let-winners-run captures that iter-027's edge is built on** (the merged BTC iter-020 / ETH iter-027
design is explicitly low-WR, fat-right-tail). Clipping the right tail to "de-concentrate" amputates the
edge's source. The brief's own falsifier fires: "if net Σ drops materially, NEGATIVE" — it dropped 37%.

**3. The genuine robustness gain is real but negligible.** Jackknife (drop the top winner trade(s),
recompute monthly Sharpe): baseline drop-top1 Δ−0.209, drop-top2 Δ−0.372; 2-leg-raw drop-top1 Δ−0.189,
drop-top2 Δ−0.336. So the ladder does make Sharpe ~0.02–0.04 less single-trade-dependent — but that is
a rounding-level improvement, swamped by the 37% return haircut and the added turnover/slippage and
backtest-engine complexity (multi-fill Orders) it would require. Not worth a full backtest.

**Why this was predictable and is not a surprise.** The OOS concentration in iter-027 is *intrinsic to a
let-winners-run trend design* (BASELINE_V1_ETHUSDT.md caveat #2 records it as a structural property under
the generalization-first gate, not a defect). An exit-side ladder cannot manufacture more independent
winning events — it can only redistribute one winner's PnL across legs of the SAME event, which is
correlated, so monthly-series concentration barely moves while the right tail (the edge) gets clipped.
The de-concentration target was OOS breadth (more independent winning *events*); a within-trade exit
ladder addresses within-trade *path*, the wrong axis.

## Recommendation
**NEGATIVE — do not run the iter-031 backtest.** Pivot to **Path Forward #2 (ensemble-disagreement
abstention)**, which attacks breadth at the ENTRY-selection layer (more/different independent events)
rather than re-slicing the same event's path. Abstention is also exit-/entry-orthogonal to the IS edge
sign in a different way (it removes low-conviction entries rather than re-weighting; needs its own
IS-only screen to confirm it does not invert IS the way iter-030 AGREE_SCALE did).

If a future iteration still wants tail-shape control on this edge, the scale-invariance finding says the
cheaper lever is **vol-target / position-size reduction** (already an R5 primitive), not a partial ladder
— same Sharpe, no extra turnover, no winner-clipping, far simpler.

## (For the record) where a ladder WOULD wire in, had it passed
Not needed (NEGATIVE), recorded so the next QR need not re-derive it. The exit primitive lives in
`src/crypto_trade/backtest.py`: per-candle exit resolution is `check_order()` → `make_result()`, and the
iter-v3/116 `evaluate_order_with_no_confirm()` (same file, ~L1015) is the closest template — it layers a
new exit condition on top of `check_order` and shares one helper across backtest + live for parity.
**Key divergence from no_confirm:** no_confirm REPLACES the single exit; a partial ladder must emit
2–3 `TradeResult` rows from one `Order` (partial fills + residual), which `make_result`/`check_order`
do not support (one Order → one result today). That requires either an Order that tracks a remaining
fraction across candles and yields multiple results, or a position-splitting layer above `check_order` —
a materially larger change than no_confirm, with live-engine parity work (multi-fill reconciliation in
`engine.py:_tick`). Another reason the marginal robustness gain does not justify the build.
