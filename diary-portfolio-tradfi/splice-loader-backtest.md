# splice-loader-backtest — leak-safe Yahoo→perp SPLICED data loader (build + verify)

**Date:** 2026-07-02 · **Scope: BACKTEST-FIRST.** Loader + leak/IS-bit-identical proofs ONLY. Live
engine + its DB (`data/tradfi_paper.db*`, `data/tradfi_equity.csv`, `logs/tradfi_paper.log`) UNTOUCHED
(engine running). No confirmed iter script modified. Wiring the spliced loader into the live desk is a
later step, GATED by these proofs.

## The problem
The confirmed iter-016 backtest reads Yahoo total-return daily bars (`data/<SYM>/1d.csv`, US
trading-day calendar, ~252/yr, 2010→2026). The live desk fills on Binance TradFi perps
(`data_live_tradfi/<SYM>/1d.csv`, 24/7 incl. weekend bars). Signal (Yahoo) ≠ execution (perp) on the
same recent day → a ~179 bps single-day parity gap. Fix: splice so the RECENT period computes the
signal on the perp actually traded; Yahoo only for the deep history the perp lacks. The perp is 24/7
(e.g. TSLA overlap 155 perp bars vs 107 Yahoo) so a raw splice would inject calendar-day-vs-trading-day
density contamination — the splice MUST resample the perp onto the Yahoo trading-day grid.

## What was built (NEW files only)
- `analysis/portfolio/tradfi/splice_loader.py` — `load_tradfi_spliced(universe, data_dir, live_data_dir)`,
  same output shape as `core_tradfi.load_tradfi`. Per name: inner-join the perp onto the Yahoo
  trading-day `open_time` index (weekend/holiday perp bars DROPPED, their move folds into the adjacent
  trading-day return); boundary `d` = first aligned perp bar (PIT inception); return-chain re-base per
  OHLC field `x`: `spliced_x[t<d]=yahoo_x`, `spliced_x[d]=yahoo_x[d]` (exact anchor),
  `spliced_x[t>d]=yahoo_x[d]·perp_x[t]/perp_x[d]`. Each field anchors on its OWN past-only `d`-value so
  the first spliced return at d+1 is a PURE perp return and there is no Yahoo→perp level jump. Names with
  no perp / <2 aligned bars → pure Yahoo.
- `analysis/portfolio/tradfi/splice_verify.py` — the 5-check GATE (`run()` + CLI report).
- `tests/test_tradfi_splice.py` — 5 synthetic (data-independent) + 5 real-data gate asserts (10 total).

## Verification results (ALL PASS — 69 names, 69 spliced, earliest inception d=2026-01-28)
1. **IS BIT-IDENTICAL (hard gate):** `max|Δ close| = 0.0`, `max|Δ return| = 0.0` for every name over all
   bars `< d`. Earliest inception 2026-01-28 is AFTER `OOS_CUTOFF=2025-03-24` → the ENTIRE IS window is
   `< d` → the spliced IS is bit-for-bit the pure-Yahoo IS. The splice cannot have altered the baseline.
2. **iter-016 IS metrics unchanged:** deployed net@1x / net@2x / gross, pure-Yahoo → spliced →
   confirmed all identical: **+0.7291 / +0.5822 / +0.8754** (== confirmed +0.729/+0.582/+0.875).
3. **Calendar:** no weekend bars (dayofweek<5 all bars); bars/yr 250–252 throughout (2022:251, 2023:250,
   2024:252, 2025:250, 2026:124 partial) — no density jump at the boundary.
4. **Boundary cleanliness:** `max|spliced_close[d]−yahoo_close[d]| = 0.0` (anchor exact);
   `max|spliced d+1 return − perp[d+1]/perp[d]| = 2.2e-16` (pure perp return to float-eps).
5. **Leak self-check:** truncating inputs to `≤ as_of` and re-splicing reproduces the full panel's
   `≤ as_of` rows bit-for-bit (`max|Δ| = 0.0`) at as_of ∈ {2026-02-15, 2026-04-15, 2026-06-01}.

## Recent-2026-tail effect (INFORMATIONAL only — OOS already revealed at +3.02; no new headline OOS)
On the OOS window the deployed net@1x moves +2.858 → +2.878 (Δ +0.021) and gross +2.906 → +2.926
(Δ +0.020) when the recent tail's signal is computed on the traded perp instead of Yahoo. Tiny, as
expected (perp tracks the underlying closely; the splice only swaps the instrument for the ~5-month tail).

## Tests
`uv run pytest tests/test_tradfi_splice.py -q` → **10 passed**. `uv run ruff check` on all three new
files → clean.

## Gate outcome
The IS-bit-identical + leak proofs are airtight (exact 0.0, not tolerance-based, because pre-inception
rows are literally untouched). This CLEARS the loader to be wired into the live bridge / desk as the
NEXT step. This step touched neither the live engine, its DB, nor any confirmed iter script.
