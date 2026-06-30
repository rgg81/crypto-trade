# portfolio-tradfi — design spec

**Date:** 2026-06-30
**Branch / worktree:** `portfolio-tradfi` (off `quant-research`), `.worktrees/portfolio-tradfi`
**Status:** approved design → implementation planning

A new systematic trading track: a **market-neutral long/short portfolio of Binance TradFi
single-company stock perpetuals**, iterated little-by-little to a real, improving net Sharpe that
survives every market regime. Fourth track after crypto v1 (`portfolio-iteration`), v2, and metals
(`portfolio-metals`). Built as a user-invocable skill, agent-driven, OOS hidden until confirmation.

## 1. Mission

Build and then **improve little by little** a systematic **long/short market-neutral portfolio** over
the universe of Binance `TRADIFI_PERPETUAL` **single-company stock** perps. Medium-frequency (daily
rebalance), plain **taker** fees, no HFT / market-making / VIP tier / special infra. The objective is
**Sharpe** (risk-adjusted), not absolute return and not beating buy-and-hold. The book **must be
survivable in all market regimes** (bull / bear / chop) — all-weather robustness is a first-class
design target, not a late discovery.

## 2. The philosophy (the point)

**Improve little by little.** Each EXPLORATION makes ONE change, measured on the backtest IN-SAMPLE.
A change that helps is kept; one that doesn't informs the next. Negative results narrow the search —
they do not end it. Be rigorous about overfitting, NOT defeatist about edges.

## 3. Locked decisions (from brainstorming 2026-06-30)

| Decision | Choice | Rationale |
|---|---|---|
| Bar cadence | **Daily** | US equities trade ~6.5h/day; 8h-clock bars are a forced fit that manufactures partial-bar / overnight artifacts. Daily is the honest equity analog of the crypto 8h cadence. |
| Universe | **All Binance `TRADIFI_PERPETUAL` single-company stocks**, self-derived from `exchangeInfo`, point-in-time | User: "all we have listed in Binance … the tradfi perpetual contracts." Real companies only — no indices/ETFs, no commodities, no metals, no pre-IPO synthetics. |
| Neutrality target | **Beta + sector-neutral** (layered: dollar → beta → sector) | Equities carry strong market-beta and sector structure crypto lacks; neutralizing both is the equity-native upgrade over the crypto dollar-neutral-only book and directly serves "succeed in all markets." |
| Sector map | **Hard-coded maintained dict** (for now) | User: "let's make this hard code for now." Static `{ticker: sector}` table over the ~85 names; revisit a data source later. |
| IS window | **2010+** (incl. 2020 COVID + 2022 bear) | All-weather tested from iter-001; fixes the metals mistake of finding bear-fragility at iter-007. |
| OOS | **`OOS_CUTOFF = 2025-03-24`**, HIDDEN until CONFIRMATION | Cross-track parity. **Critical user rule:** judge IS-only; reveal OOS only at a confirmation, at the end. |
| Funding | **Not modelled** | TradFi perp funding just launched, ~no history. User: "ignore funding rates for now no data." |
| Metric | **Sharpe** | Risk-adjusted. Not absolute return, not B&H. |

## 4. Universe definition (self-updating)

Derive at runtime from Binance USDⓈ-M `exchangeInfo`: every symbol with
`contractType == "TRADIFI_PERPETUAL"`, then keep **single-company common stocks / single-company
US-listed ADRs** by applying a maintained classifier. Roster as of 2026-06-30: 110 TradFi perps →
~85 stocks after exclusions. The universe **grows** as Binance lists more; the foundation re-derives
it rather than hard-coding the list.

**Exclude sets (maintained, version-controlled):**
- **ETFs / indices / leveraged / country funds:** SPY, QQQ, IWM, TQQQ, SQQQ, SOXL, UVXY, XLE, EWJ,
  EWY, EWZ, EWT, URNM, KORU, STXX (and future ETFs).
- **Commodities:** NATGAS, CL, BZ, COPPER.
- **Metals (owned by `portfolio-metals`):** XAU, XAG, XPT, XPD.
- **Pre-IPO / private synthetics (no real underlying history):** ANTHROPIC, OPENAI.

**Point-in-time membership:** a name carries weight only once it has sufficient Dukascopy history and
clears a trailing $-volume / data-availability gate. Recent IPOs (HOOD, RIVN, CRWV, CRCL, ASTS …) enter
via ragged starts — never back-fabricated. Survivorship-safe by construction.

## 5. Data strategy

Every TradFi perp onboarded in 2026 (earliest TSLA 2026-01-28) → Binance has only ~months of native
history. The 2010+ backtest history therefore comes from the **Dukascopy underlying stock** feed, the
proven metals pattern.

- **Backtest history (2010+):** Dukascopy daily underlying OHLC per name via `dukascopy-node`
  (free, no key). `analysis/portfolio/tradfi/ingest_dukascopy_stocks.py`, forked from the metals
  `ingest_dukascopy.py`. Resample to daily UTC; write `data/<TICKER>/1d.csv` in the Kline CSV format
  under the **Binance** ticker so backtest↔live keys match.
- **Recent / live:** Binance daily-resampled `TRADIFI_PERPETUAL` klines; live venue is the Binance
  24/7 perp, rebalanced once daily at a fixed UTC time.
- **Instrument-id map:** maintained `{BinanceTicker: (dukascopy_id, earliest_start)}` dict; Dukascopy
  per-name history depth audited and recorded point-in-time (mega-caps 2010+, recent IPOs from listing).
- **Known deployment caveat (not a research blocker):** backtest uses underlying-stock prices; live
  trades the perp → a perp-vs-underlying **basis reconcile** is required before real capital (same
  open item the metals track carries).

## 6. Construction & factors

- **Anchor (iter-001):** dollar-neutral cross-sectional momentum (rank long winners / short losers),
  vol-targeted (~10–15%), leverage-capped. Equity-native factors only — XS-momentum (12-1m),
  short-term reversal, low-vol, quality — **not** crypto factors.
- **iter-002:** layer **beta-neutral** — neutralize net market-beta exposure (hedge the market factor).
- **iter-003:** layer **sector-neutral** — dollar/beta neutrality enforced *within* sector buckets from
  the hard-coded sector map.
- Each layer is its own EXPLORATION, kept only if it lifts IS net Sharpe and/or improves regime
  robustness without washing the edge.
- **No short-borrow modelling** — we trade the native-short perp, a clean advantage over cash-equity
  L/S. Cost ≈ 6 bps/side (taker + slippage; verify TradFi fee tier) + report Sharpe at 1×/2× cost.

## 7. Rigor (the gauntlet)

1. **Realistic execution** — signal decided on daily CLOSE[t], rebalanced at next session OPEN[t+1],
   held; taker fee + slippage on turnover. Leak-safe (signals past-only).
2. **No-cheat leak control** — leak test asserts both **future-bar AND same-bar** corruption leaves
   past/current decisions bit-identical, from iter-001. (The same-bar leak is the exact class the
   standard future-only test missed and reconciliation caught in metals.) Reconciliation harness from
   day one.
3. **Walk-forward params** — a tunable earns per-period walk-forward selection ONLY if proven
   non-stationary; structural params proven by robustness sweep (all configs positive IS), never
   hindsight-picked across the whole sample. Per-month tuning of all params is itself a hidden cheat.
4. **OOS holdout — HIDDEN** — `OOS_CUTOFF = 2025-03-24`. EXPLORATIONs are scored IN-SAMPLE only. OOS is
   revealed ONLY at a CONFIRMATION, at the end. Mechanically enforced: the engine refuses to emit OOS
   stats without an explicit `--confirm` flag (discipline → mechanism — an improvement over prior
   tracks where it was convention).
5. **All-weather** — IS spans 2020 COVID + 2022 bear; every iteration scored bull / bear / chop and
   required survivable (bounded drawdown), not merely peak-Sharpe.
6. **Benchmarks (at CONFIRMATION)** — beat an equal-weight stock basket and a market proxy on
   risk-adjusted terms; report turnover + cost-stress. Net Sharpe is what counts.

## 8. Roles — agent-driven, every iteration

The orchestrator coordinates + synthesizes + commits. Every iteration uses the full team:
- **quant-researcher** — designs the EXPLORATION (which one change, why; equity-native rationale).
- **quant-engineer / risk-engineer** — implements + runs the backtest (risk-engineer for any
  risk/sizing/neutrality/DD primitive).
- **quant-critic** (read-only) — reviews EVERY result before it is kept; **constructive**, delivering
  both adversarial findings (MANDATORY future-bar + same-bar leak check, selection/survivorship bias,
  walk-forward correctness, cost realism, significance) AND concrete fixes + next-iteration ideas. A
  change promotes only on a critic PASS; a BLOCK always comes with a path forward.

## 9. Cadence

- **EXPLORATION** (≤2h) — one change, scored on the backtest + the rigor checks that don't need OOS.
  Logged to `diary-portfolio-tradfi/EXPLORATION-NNN.md` with numbers + verdict + critic note.
- **CONFIRMATION** — reveal OOS + full gauntlet; only this (with a critic PASS) promotes a change into
  the baseline (`BASELINE_TRADFI.md`). Commit every step with the honest result, incl. down-corrections.

## 10. Deliverables / foundation (build once, reuse)

- **Skill:** `.claude/commands/portfolio-tradfi.md` (this track's user-invocable workflow).
- **Universe:** `analysis/portfolio/tradfi/universe_tradfi.py` — `exchangeInfo`-derived PIT universe +
  maintained exclude sets + hard-coded sector map; leak-safe panel/vol-target core (reuse metals
  `net_from_raw`, `panels`, `vol_target`).
- **Data:** `analysis/portfolio/tradfi/ingest_dukascopy_stocks.py` — Dukascopy daily ingest (fork of
  metals ingest) + instrument-id map.
- **Neutralization:** `analysis/portfolio/tradfi/neutralize.py` — dollar / beta / sector neutralizers.
- **Engine:** daily-bar portfolio backtest (reuse/adapt `analysis/portfolio` engine): per-name signal →
  target weights → next-open rebalance → hold → taker cost on weight change → portfolio return series;
  portfolio vol-targeting; helpers (monthly Sharpe, per-year/regime breakdown, maxDD, turnover,
  benchmarks); `--confirm`-gated OOS.
- **Tests:** `tests/test_portfolio_tradfi_foundation.py` — future-bar leak, **same-bar leak**,
  dollar/beta/sector neutrality, cost accounting, PIT/survivorship, OOS-gate enforcement.
- **Diary / baseline:** `diary-portfolio-tradfi/`, `BASELINE_TRADFI.md`.

## 11. Sacred constants

- `OOS_CUTOFF = 2025-03-24` (immutable). **Daily** bars. Signals past-only; fills at next-open.
- Never tune on OOS; never trim the IS window. Report net (after cost), not gross.
- Universe = Binance `TRADIFI_PERPETUAL` single-company stocks, point-in-time, no survivorship
  cherry-pick. No indices/ETFs, no commodities, no metals, no pre-IPO synthetics.
- OOS HIDDEN until a CONFIRMATION.

## 12. How this skill improves on its predecessors

1. **Self-updating universe** from `exchangeInfo` (vs crypto's hard-coded top-20).
2. **Mechanically-enforced OOS hiding** (`--confirm` gate) — discipline becomes mechanism.
3. **Same-bar leak test from iter-001** — bakes in the bug class that cost the metals track a
   withdrawn iteration.
4. **Beta + sector neutralization** — equity-native robustness crypto never needed.
5. **All-weather required from iter-001** — multi-regime IS, not a late painful bear-test bolt-on.
6. **No short-borrow complexity** — native-short perp removes an entire cash-equity cost/locate model.

## 13. Roadmap

1. **Foundation** — universe + ingest + daily engine + neutralizers + tests green.
2. **iter-001** — dollar-neutral XS-momentum anchor: validate it nets positive IS after costs,
   leak-safe (future + same-bar), survivable across regimes. Anchor.
3. **iter-002** — beta-neutral overlay. **iter-003** — sector-neutral overlay.
4. Then layer factors one at a time (short-term reversal, low-vol, quality, regime/vol gross-scaling),
   each its own EXPLORATION, kept only if it lifts net Sharpe or regime robustness.
5. CONFIRMATION → baseline → repeat.
