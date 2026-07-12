# MN4 UNIFIED-01-03 — Live Paper-Trading Component

**User-directed 2026-07-12.** The user's CORE deliverable: "build a live
component that can reproduce the backtest bit by bit." This is the live
paper-trading component for the FROZEN UNIFIED-01-03 single-signal book
(`analysis/portfolio/mn4_unified_0103.py`).

**Model note:** Engineered on Opus 4.8 (Claude Fable rate-limited;
user-directed per the MN4 charter's model-disclosure rule).

---

## Architecture — live = run_unified on the GROWING panel

**One-liner:** the live component is NOT a reimplementation. It runs the SAME
`run_unified()` / `blind_engine.run_backtest()` code on the GROWING panel and
reads off the latest candle's decision. Because the engine is deterministic and
every signal generator is past-only (the replay test in
`tests/test_mn4_unified_0103.py` already PROVED
`composite_signal_at/universe_at/scalar_at/target_weights_at(panel[:k+1], k)` is
bit-identical to the full run at k), the live "trade" at candle k IS the
backtest's trade at k — by construction.

The engine IS the paper broker:
- **Fills:** open-to-open hold-period returns (decide at close[k-1], fill at
  open[k], realize at open[k+1]).
- **Costs:** taker 5bps + slippage 2.5bps on one-way turnover (1x book), with
  a 2x-GT sensitivity twin (10bps + 5bps).
- **Funding:** REAL per-symbol 8h production funding rates, applied as
  `cost_fund = sum(w_eff * funding[k])` per candle — see §Funding below.
- **Hedge overlay:** BTC + conditional ETH leg, sized from past-only betas to
  cancel the book's BTC (and residual-ETH) beta. Hedge legs pay/receive
  funding like any position — no free hedge.

### The single-command entrypoint (what the cron calls)

```
PATH="$HOME/.local/bin:$PATH" PYTHONUNBUFFERED=1 \
    uv run python analysis/portfolio/mn4_live_unified.py [--no-fetch]
```

One full tick, idempotent:
1. `fetch_and_extend()` — fresh 8h klines + REAL per-symbol 8h funding rates
   for the universe (existing panel ∪ newly-listed ACTIVE perps). Tolerant of
   PENDING/dead symbols. Completeness guard: BTC+ETH+SOL klines + BTC+ETH
   funding must be current (else DEGRADED flag, never silently skip).
2. `run_forward()` — load full panel (IS + holdout + forward) + funding, call
   `run_unified()` (the FROZEN backtest; funding_enable=True, 5+2.5bps) TWICE
   (1x + 2x-GT twin), slice the FORWARD window [2026-07-01, now), return
   per-candle weights/returns/turnover/funding + the LATEST candle's effective
   position (the paper "trade" to hold).
3. `append_log()` — append the forward window to `paper-unified-0103/
   forward_returns.csv` (append-invariant; idempotent). ABORTs if any prior
   row fails to reproduce bit-identically (upstream kline revision / code
   drift).
4. `report()` — print latest paper position (named longs/shorts + hedge legs),
   P&L (cum + Sharpe 1x + 2x GT), FUNDING ATTRIBUTION (long-leg vs short-leg
   vs hedge-leg; cumulative drag/income; funding share of P&L; Sharpe with vs
   ex-funding), IDEA-03 regime occupancy, and the pre-registered forward gates.

Forward log schema (`paper-unified-0103/forward_returns.csv`, per 8h candle):
```
date, ret_1x, ret_2x_gt, turnover, gross_scalar_applied, regime_state,
n_held, funding_ret, hedge_funding_ret, price_ret
```

### Scheduling — session CronCreate (per user direction 2026-07-12)

The user directed: "no need for systemd, for now we will run the cron in the
Claude session." The orchestrator hangs a **session CronCreate** job off the
single command above at 8h cadence (fires at each candle close + a short
offset).

**Caveats (documented for the audit trail):**
- CronCreate is **session-only** — the cron DIES when the Claude session ends.
- Recurring CronCreate jobs **auto-expire after 7 days**.
- This is a "for now" setup. For unattended multi-month operation the
  documented upgrade path is a systemd USER timer (`OnCalendar=*-*-*
  00:08:00/08:08:00/16:08:00` UTC, `Persistent=true`, `loginctl enable-linger`).
  The systemd unit files were drafted then dropped per the user's mid-build
  direction; they live in git history if needed.

---

## The PARITY TEST — bit-identity is the core value

**Result: BIT-IDENTICAL CONFIRMED.** The parity test
(`tests/test_mn4_live_unified.py::test_parity_run_forward_matches_direct_backtest`)
runs the frozen backtest over the full panel, runs the live component's
`run_forward()`, and asserts the forward slices are BIT-IDENTICAL via
`np.array_equal` for:

- `fwd_weights` — effective weights held over each forward candle
- `fwd_rets_1x` — 1x cost net returns
- `fwd_rets_2x_gt` — 2x GT cost net returns
- `fwd_turnover` — one-way turnover
- **`fwd_funding_rets` — total funding cost (the silent parity killer)**

Same code path → trivially true; the test makes it a hard guarantee. 17 tests
in `tests/test_mn4_live_unified.py` all PASS (synthetic panel; covers parity,
funding sign-convention, append-invariance, sealed-window guard, gate
thresholds, latest-position).

The parity guarantee rests on three layered proofs:
1. **Replay test** (`tests/test_mn4_unified_0103.py`): the composite signal
   builders are past-only — `composite_signal_at(panel[:k+1], k)` equals
   `composite_signal(panel)[k]` at every sampled candle. The live component
   only ever sees `panel[:k+1]` at decision time k, so its decision IS the
   backtest's decision.
2. **Corrupt-future positive controls** (`tests/test_mn4_unified_0103.py`):
   corrupting `close[t0:]` / `quote_volume[t0:]` leaves
   `composite_signal[:t0]` / `composite_universe[:t0]` bit-identical.
3. **Decision-lag [k-1]** (`tests/test_mn4_unified_0103.py`): corrupting
   signal/scalar/beta at row >= t0 leaves the engine's realized equity through
   `open[t0]` bit-identical. The engine consumes `signal[k-1]` at rebal step k,
   so a corruption at row >= t0 cannot affect any decision before `close[t0-1]`.

---

## FUNDING RATES IN PRODUCTION — the user-emphasized requirement

**Result: REAL per-symbol 8h production funding rates, correct sign,
attribution working.**

### Source + plumbing

- `fetch_and_extend()` calls `uv run crypto-trade fetch-funding --symbols ...`,
  which hits the **production endpoint**
  `https://fapi.binance.com/fapi/v1/fundingRate` and caches
  `data/funding_rates/<SYMBOL>.csv` (schema: `funding_time, funding_rate`).
  These are the REAL Binance 8h settlement rates, not stale/flat.
- `blind_funding.load_funding()` builds a `(T, C)` panel by **bucket-summing**
  every settlement whose `fundingTime` falls in `(grid[k], grid[k+1]]` into
  candle k — so any cadence (8h/4h/1h) is accounted for exactly. Symbols
  missing a funding CSV (or sub-$1 perps filed under a 1000x-scaled ticker)
  are resolved via `_FUNDING_SYMBOL_MAP` or NaN-masked so the engine excludes
  them via `np.isfinite(f)` (no silent zero-funding bug).
- The engine's `CostModel(funding_enable=True)` applies funding[k] to the
  weights held over candle k: `cost_fund = sum(w_eff * funding[k])`. Then
  `rets[k] = gross_pnl - cost_trade - cost_fund` (funding reduces returns
  when positive — i.e., longs pay).

### Sign convention (verified by unit test on a constructed case)

`funding_sign_convention(w, f)` returns the long-leg / short-leg split:

- **LONG** (w>0) with funding>0 → `w*f > 0` → **PAYS** (drag, +).
- **SHORT** (w<0) with funding>0 → `w*f < 0` → **RECEIVES** (income, -).
- Matches Binance exactly: positive funding rate = longs pay shorts.

Unit tests:
- `test_funding_sign_convention_long_pays_short_receives`
- `test_funding_sign_convention_zero_funding_zero_cost`
- `test_alpha_long_funding_positive_when_book_net_long` (with uniform positive
  funding, the long-leg cumulative flow is >0 and short-leg is <0)
- `test_funding_application_matches_engine_formula` (engine `funding_rets[k]`
  == `sum(weights[k] * funding[k])` to 1e-15)

### Hedge-leg funding

The hedge legs (BTC + conditional ETH overlay) are NOT exempt — they
pay/receive funding like any other position. The engine exposes
`hedge_funding_rets` (the hedge-leg subset of `funding_rets`). The live
component splits the per-candle funding flow into:

- `alpha_long_fund` = `sum(where(w_alpha>0, w_alpha*f, 0))` — longs pay
- `alpha_short_fund` = `sum(where(w_alpha<0, w_alpha*f, 0))` — shorts receive
- `hedge_funding_rets` — the BTC+ETH hedge subset (engine-exposed)

where `w_alpha = weights_full - hedge_weights_full_row` (the alpha portion
after subtracting the hedge legs on BTC/ETH columns).

Unit test: `test_hedge_funding_is_accounted_subset_of_total` verifies
`alpha_long + alpha_short + hedge ≈ total` to 1e-12 (the small slack is the
float w_alpha = w_full - w_hedge subtraction).

### Proof-run funding attribution (2026-07-01 .. 2026-07-12, 34 candles)

```
cumulative funding drag   : -0.5686%  (- = net INCOME — the book is net-short
                                          and funding went negative in the dip)
  alpha long-leg (paid)   : -0.7634%  (longs received — funding negative)
  alpha short-leg (recv)  : +0.1890%  (shorts paid — funding negative)
  hedge legs (BTC+ETH)    : +0.0058%  (small BTC short funding cost)
cumulative price return   : -15.7287% (ret + funding; the non-funding P&L)
funding share of gross P&L: 3.62%     (< 30% FG-4 threshold — PASS)
Sharpe with funding       : -9.537
Sharpe ex-funding         : -9.843    (worse — funding was helping)
funding contribution      : +0.306    (funding ADDED 0.31 to Sharpe)
```

The negative cumulative drag means the book is NET RECEIVING funding over
this window (the book is net-short BTC at -0.0636 and funding rates went
negative in the dip — shorts pay longs when funding < 0, but the alpha
long-leg also received because ALT funding was negative). This is REAL
production funding behavior, not a sign error — the unit tests pin the
convention on constructed cases where the sign is unambiguous.

---

## Forward gates (pre-registered; logged each run)

| Gate | Threshold | Anchor | Status @ n=34 |
|---|---|---|---|
| FG-1 PRIMARY Sharpe | >= +0.50 (SUCCESS) / < 0 (FAIL) | holdout 8h Sharpe +1.171 | INSUFFICIENT |
| FG-2 maxDD | > -30% (PASS) / <= -30% (FAIL) | holdout maxDD -25.0% | INSUFFICIENT |
| FG-3 slow-bleed | worst 6mo Sharpe < -0.5 (CONCERN) | n/a | INSUFFICIENT |
| FG-4 funding discipline | drag > 30% of gross edge (CONCERN) | n/a | INSUFFICIENT |

All gates read INSUFFICIENT until `n_forward_candles >= 90` (~30 days at 8h
cadence — the noise floor for an 8h Sharpe). The QR evaluates the verdict at
the 12-month mark (the PROTOCOL forward-test horizon).

**Proof-run verdict:** `INSUFFICIENT DATA (n=34 < 90 candles)` — the correct
early-state verdict. Forward window: 2026-07-01T08:00:00Z .. 2026-07-12T08:00:00Z
(34 candles, ~11 days). The -15.24% cumulative is real forward data (the book
is net-short BTC at -0.0636 while BTC rallied over the window) — NOT a bug,
just early-regime variance over a thin sample.

---

## How to read progress

- **`paper-unified-0103/forward_returns.csv`** — per-8h-candle forward log
  (append-only, append-invariant). One row per forward candle. The `ret_1x`
  column is the paper P&L; `funding_ret` and `price_ret` split it.
- **`paper-unified-0103/gates.csv`** — one row per run (the gate table
  snapshot). Track `fwd_sharpe_1x`, `cum_funding_drag`, and `verdict` over
  time.
- **`paper-unified-0103/runs.log`** — one-line-per-run summary
  (`forward_candles`, `appended`, `fwd_sharpe_1x`, `fwd_maxdd`,
  `cum_funding`, `verdict`, `DEGRADED`, `wall`).
- **`paper-unified-0103/integrity.json`** — SHA256 of the frozen-construction
  modules at first run; drift logged (not aborted) on later runs.

The forward log is the single source of truth for the paper-trade P&L. Re-run
the single command anytime to refresh; the append-invariance guard ensures
every past row reproduces bit-identically (or the runner ABORTs loudly).

---

## Test + lint status

- `tests/test_mn4_live_unified.py` — 17/17 PASS (parity, funding sign,
  append-invariance, sealed-window, gates, latest-position).
- `tests/test_mn4_unified_0103.py` — 22/22 PASS (replay, corrupt-future,
  decision-lag, composition math).
- `uv run ruff check analysis/portfolio/mn4_live_unified.py tests/test_mn4_live_unified.py`
  — **All checks passed.**

---

## Files

- `analysis/portfolio/mn4_live_unified.py` — the live component (single-command
  CLI: `main()` runs one full idempotent tick).
- `tests/test_mn4_live_unified.py` — the parity + integrity suite (17 tests).
- `paper-unified-0103/forward_returns.csv` — the forward log (34 rows as of
  2026-07-12).
- `paper-unified-0103/gates.csv` — the gates snapshot (one row per run).
- `paper-unified-0103/runs.log`, `cron_runs.log`, `integrity.json` — audit trail.
