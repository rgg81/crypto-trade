# Portfolio TradFi — market-neutral L/S Binance TradFi single-company stock perps

## Mission
Build, and then **improve little by little**, a systematic **long/short market-neutral portfolio** over
the universe of Binance `TRADIFI_PERPETUAL` **single-company stock** perpetuals. Medium-frequency
(**daily** rebalance), plain **taker** fees, no HFT, no market-making, no VIP fee tier, no special infra.

The objective is **Sharpe** (risk-adjusted) — not absolute return, not beating buy-and-hold. The book
**must survive all market regimes** (bull / bear / chop): all-weather robustness is a first-class design
target from iter-001, not a painful bolt-on discovered at iter-007 (the metals lesson).

## The philosophy (READ THIS — it is the point)
**Improve little by little.** Each EXPLORATION makes ONE change, measured on the backtest IN-SAMPLE.
A change that helps is kept; one that doesn't informs the next. Negative results narrow the search —
**they do not end it.** We are building a strategy, not looking for reasons to quit. Be rigorous about
overfitting, NOT defeatist about edges.

## Rigor (the gauntlet)
A change is "real" when it survives:
1. **Realistic execution** — signal decided on daily CLOSE[t], rebalanced at next-session OPEN[t+1];
   **taker** fee + slippage per turnover; funding NOT modelled (TradFi perp funding just launched,
   negligible history). Leak-safe: signals past-only.
2. **No-cheat leak control** — leak test asserts BOTH **future-bar AND same-bar** corruption leaves
   past/current decisions bit-identical. (Same-bar leak is the exact class the standard future-only
   test missed and caught in the metals track — baked in from day one here, not discovered later.)
3. **Walk-forward params** — a tunable earns per-period walk-forward selection ONLY if proven
   non-stationary; structural params proven by robustness sweep (all configs positive IS), never
   hindsight-picked. Per-month tuning of ALL params is itself a hidden cheat.
4. **OOS HIDDEN** — `OOS_CUTOFF = 2025-03-24`. EXPLORATIONs scored IS-only. OOS revealed ONLY at a
   CONFIRMATION, via `--confirm`. Mechanically enforced: engine refuses OOS stats without `--confirm`.
5. **All-weather** — IS spans 2010+, including 2020 COVID and 2022 bear. Every iteration scored
   bull / bear / chop; survivable (bounded drawdown) is required, not merely peak-Sharpe.
6. **Benchmarks (at CONFIRMATION)** — beat an equal-weight stock basket and market proxy on
   risk-adjusted terms; report turnover + Sharpe at 1×/2× cost. Net Sharpe is what counts.

**NOT in the gauntlet:** no institutional-capacity liquidity floor, no maker-only fee assumption, no
short-borrow model (we trade the native-short perp — a clean advantage over cash-equity L/S).

## Universe
Self-derived from Binance USDⓈ-M `exchangeInfo`: every symbol with `contractType == "TRADIFI_PERPETUAL"`,
then keep **single-company common stocks / single-company US-listed ADRs**. ~85 names after exclusions.
Universe grows as Binance lists more; re-derived at runtime — never hard-coded.

**Exclude (maintained, version-controlled in `universe_tradfi.py`):**
- ETFs / indices / leveraged / country funds: SPY, QQQ, IWM, TQQQ, SQQQ, SOXL, UVXY, XLE, EWJ, EWY,
  EWZ, EWT, URNM, KORU, STXX (and future ETFs).
- Commodities: NATGAS, CL, BZ, COPPER.
- Metals (portfolio-metals track): XAU, XAG, XPT, XPD.
- Pre-IPO / private synthetics (no real underlying history): ANTHROPIC, OPENAI.

**Point-in-time membership:** a name carries weight only once it has sufficient Dukascopy history and
clears a trailing $-volume / data-availability gate. Recent IPOs enter via ragged starts — never
back-fabricated. Survivorship-safe by construction.

## Data strategy
Binance TradFi perps onboarded 2026 → only months of native history. The 2010+ IS therefore comes from
**Dukascopy daily underlying** OHLC via `dukascopy-node` (free, no key), the proven metals pattern.

- **Backtest (2010+):** `analysis/portfolio/tradfi/ingest_dukascopy_stocks.py` writes
  `data/<TICKER>/1d.csv` in Binance Kline CSV format. Mega-caps from 2010; recent IPOs from listing.
- **Recent / live:** Binance daily-resampled `TRADIFI_PERPETUAL` klines; live venue is the 24/7 perp,
  rebalanced once daily at a fixed UTC time.
- **Known deployment caveat (not a research blocker):** backtest uses underlying-stock prices; live
  trades the perp → a perp-vs-underlying basis reconcile is required before real capital.

## Foundation (build once, reuse every iteration)
- `analysis/portfolio/tradfi/universe_tradfi.py` — `exchangeInfo`-derived PIT universe + exclude sets +
  hard-coded sector map `{ticker: sector}`.
- `analysis/portfolio/tradfi/ingest_dukascopy_stocks.py` — Dukascopy daily ingest + instrument-id map.
- `analysis/portfolio/tradfi/neutralize.py` — dollar / beta / sector neutralizers.
- `analysis/portfolio/tradfi/core_tradfi.py` — daily-bar portfolio engine: per-name signal → target
  weights → next-open rebalance → taker cost on weight change → return series; vol-targeting (~10–15%);
  helpers: monthly Sharpe, per-year/regime breakdown, maxDD, turnover, benchmarks; `--confirm`-gated OOS.
- `analysis/portfolio/tradfi/iter_001_xsmom.py` — dollar-neutral XS-momentum anchor.
- `tests/test_portfolio_tradfi_foundation.py` — future-bar leak, same-bar leak, dollar/beta/sector
  neutrality, cost accounting, PIT/survivorship, OOS-gate enforcement.
- `diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`.

## Roles — AGENT-DRIVEN (every iteration, no exceptions)
The orchestrator coordinates + synthesizes + commits. Every iteration uses the FULL team:
- **quant-researcher** — designs the EXPLORATION (which one change, why; equity-native rationale).
- **quant-engineer / risk-engineer** — implements + runs the backtest (risk-engineer for any
  risk/sizing/neutrality/DD primitive).
- **quant-critic** (read-only) — reviews EVERY result before it is kept; **constructive**, delivering
  both (a) adversarial findings — MANDATORY future-bar + same-bar leak check, selection/survivorship
  bias, walk-forward correctness, cost realism, statistical significance — AND (b) concrete fixes +
  ideas for the next iteration. A change promotes only on a critic PASS; a BLOCK always comes with a
  path forward.

## Cadence
- **EXPLORATION** (≤2h) — one change, scored IS-only + rigor checks that don't need OOS. Logged to
  `diary-portfolio-tradfi/EXPLORATION-NNN.md` with numbers + verdict + critic note.
- **CONFIRMATION** — reveal OOS (via `--confirm`) + full gauntlet; only this (with critic PASS) promotes
  into `BASELINE_TRADFI.md`. Commit every step, including down-corrections.

## NO CHEATING (hard)
- Never tune on OOS; never trim the IS window. Report net (after cost), not gross.
- Never exact-match-join ragged timestamps. Never report a number a critic hasn't cleared.
- If a result looks too good, assume a bug until the critic clears it.
- OOS stats require `--confirm` — the engine is the enforcer, not convention.

## Neutrality roadmap (little by little)
1. **iter-001** — dollar-neutral XS-momentum anchor (IS scored, leak-safe, regime-survivable). DONE.
2. **iter-002** — beta-neutral overlay (neutralize net market-beta exposure).
3. **iter-003** — sector-neutral overlay (dollar/beta within hard-coded sector buckets).
4. Then layer factors one at a time: short-term reversal, low-vol, quality, vol gross-scaling, regime
   filter — each its own EXPLORATION, kept only if it lifts net Sharpe or regime robustness.
5. CONFIRMATION → baseline → repeat.

## Sacred constants
- `OOS_CUTOFF = 2025-03-24` (immutable). **Daily** bars. Signals past-only; fills at next-open.
- Universe = Binance `TRADIFI_PERPETUAL` single-company stocks, point-in-time, no survivorship cherry-pick.
  No ETFs/indices, no commodities, no metals, no pre-IPO synthetics.
- IS window = 2010+ (all-weather tested from iter-001).
- OOS HIDDEN until CONFIRMATION (`--confirm`).

## Run
```
uv run pytest tests/test_portfolio_tradfi_foundation.py -q          # foundation stays green
uv run python analysis/portfolio/tradfi/iter_001_xsmom.py           # IS-only (no --confirm)
uv run python analysis/portfolio/tradfi/iter_001_xsmom.py --confirm # CONFIRMATION — reveals OOS
```
