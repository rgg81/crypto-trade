# Live deploy — Phase 2a/2b: perp ingest + basis/funding reconcile (GATING)

**Date:** 2026-07-01
**Scope:** Ingest the Binance TradFi single-stock perps for the iter-016 deployed book, then answer
the gating question — **does perp-return + funding track the Yahoo total-return the book was
validated on?** This gates whether the paper engine gets built next.

**New files (analysis/ is gitignored → `git add -f`):**
- `analysis/portfolio/tradfi/perp_map_tradfi.py` — Task A: SECTOR_MAP key → live perp symbol.
- `analysis/portfolio/tradfi/ingest_perp_tradfi.py` — Task B: daily perp klines + funding ingest.
- `analysis/portfolio/tradfi/reconcile_basis_tradfi.py` — Task C: the gating reconcile.
- `tests/test_tradfi_basis_reconcile.py` — 9 unit tests (funding sign, binning, ms-robustness…).

**Data stores (gitignored, regenerable):** `data_live_tradfi/<PERP>/1d.csv` (perp daily klines,
mirrors the metals `data_live_metals/` separation — never touches the Yahoo bars in `data/<KEY>/`);
`data/funding_rates/<PERP>.csv` (via shared `crypto_trade.portfolio.funding.refresh_funding`).

---

## Task A — perp symbol map (verified empirically vs live exchangeInfo)

All **69/69** SECTOR_MAP keys resolve to a live `TRADIFI_PERPETUAL` contract. In every case the perp
`symbol` **equals the key** (`stem(KEY) == baseAsset`), because the Yahoo store was already named with
Binance's perp convention — including Binance-specific tickers (`PAYP`=PayPal, `BRKB`=Berkshire-B,
`V`=Visa). **UNMAPPED: NONE.** Static snapshot `PERP_SYMBOL_MAP` matches live-resolve (no drift).
Onboard dates span **2026-01-28 (TSLA, earliest)** → **2026-06-22** (many June IPOs).

## Task B — ingest extents

69/69 symbols ingested: **3,642 daily bars, 11,327 funding rows**. Bars end 2026-06-30 (forming
2026-07-01 candle dropped); funding through 2026-07-01. Per-name history is ragged by onboard date:
TSLA 154 bars (from 2026-01-28), HOOD/INTC 149, AMZN/COIN/CRCL/MSTR/PLTR 142 (from 2026-02-09), down
to the 2026-06-22 IPOs (ALAB/CIEN/KLAC/LRCX/SMCI/SONY) with ~9 bars. Funding is 3×/day (8h).

---

## Task C — the gating reconcile (perp window 2026-01-28 → 2026-06-29, 105 trading days)

Return convention = open-to-open forward `ret_fwd` (identical to the backtest book), perp opens
reindexed onto the Yahoo trading-day grid (Fri→Mon spans the weekend on both legs). Funding aligned
to the same holding window; **long realized = perp_ret − f_daily** (f>0 ⇒ long pays).

### C.1 Per-name tracking (43 reliable names ≥ 20 common days; ex-pathological)
- **|gap| WITHOUT funding:** mean 245 bps, median 166 bps (raw perp price vs Yahoo TR).
- **|gap| WITH funding:** mean 405 bps, median 262 bps.
- **Funding does NOT close the gap — it WIDENS it by ~160 bps.** These are low/no-dividend growth/
  tech names and the single-stock perps trade at a persistent **retail LONG premium** (median
  annualized funding on longs **+9.0%/yr**), so funding is an **extra carry cost**, NOT the
  dividend/carry bridge the hypothesis expected. The "funding closes the dividend gap" story does not
  apply to this universe.
- **Daily corr(realized perp, Yahoo):** mean 0.750, median 0.769, min 0.524.
- **Annualized tracking error:** mean 48.6%, median 43.9% per name — inflated by the **00:00-UTC perp
  open vs US-session Yahoo open non-synchronicity** (24/7 perp vs 6.5h cash session). This is
  idiosyncratic and **diversifies away at the book level** (see C.2).
- **PATHOLOGICAL: `PAYPUSDT`.** corr 0.19, cum perp −35.6% vs Yahoo −0.01% (gap −3,564 bps). The
  Yahoo "PAYP" underlying sits at ~$40–51 (roughly flat) while the Binance PAYP perp is ~$12–24 and
  collapsing — **they are not the same instrument** (a ticker mismap between the Yahoo stem and the
  Binance perp underlying). **EXCLUDE PAYP from deployment until the mapping is fixed.**

### C.2 Book-level — LIVE net (perp+funding) vs BACKTEST net (Yahoo-TR), same weights/window/cost
- **cumulative LIVE−RECON gap = −85 bps** over ~5 months (LIVE +8.65% vs RECON +9.50% on the same
  tradeable names).
- **daily tracking error (annualized) = 5.8%** — an order of magnitude tighter than the per-name TE,
  confirming the non-synchronous-open noise nets out across the 69-name book.
- **corr(LIVE, RECON) = 0.70**; perp-window Sharpe **LIVE +2.60 vs RECON +3.00** (tracking-stream
  Sharpes over the live window — NOT an IS/OOS strategy metric).
- **Coverage caveat:** mean perp coverage of the book's gross was only **34%** early (many perps not
  yet listed) rising to **100% now**. The book-of-record (all 69 Yahoo names) returned +20.46% vs the
  tradeable-subset RECON +9.50% — that gap is a **data-availability artifact, not a basis problem**,
  and disappears now that all perps are live.

### C.3 Net funding drag on the L/S book (annualized, on book NAV)
- gross **LONG-leg funding P&L = −1.47%/yr** (longs pay the premium).
- gross **SHORT-leg funding P&L = +0.75%/yr** (shorts collect it).
- **NET funding = −0.72%/yr** (gross funding turned over 6.32%/yr). Because the book is ~market-
  neutral L/S, **68% of the gross funding nets across legs** — the residual is a modest ~0.7%/yr real
  cost that must be budgeted into live P&L.

---

## VERDICT — DEPLOYABLE (with two required actions)

**Perp + funding reproduces the Yahoo-TR book at the whole-book level** — cum gap −85 bps over 5 mo,
5.8%/yr tracking error, corr 0.70, Sharpe 2.6 vs 3.0. The per-name basis is noisy (non-synchronous
opens) but diversifies away in the 69-name book. Required actions before/at deploy:
1. **Budget the funding carry** as a real cost (~−0.7%/yr net on the L/S book; −1.5%/yr gross on the
   long leg). It is NOT a dividend bridge — do not assume it cancels.
2. **EXCLUDE `PAYPUSDT`** until the Yahoo↔perp mapping defect is investigated/fixed (perp is a
   different instrument from the "PAYP" Yahoo series).
Plus: the clean whole-book reconcile is only fully representative **now** that perp coverage = 100%;
re-run this reconcile after a few more weeks of full-coverage live data before scaling size.

**Constraints honored:** `OOS_CUTOFF = 2025-03-24` untouched (perp window is entirely post-cutoff, a
live-forward reconcile — no IS/OOS strategy Sharpe computed/revealed); no existing iter_*/core/bridge
file or Yahoo `data/<KEY>/1d.csv` modified; tests in a new file; ruff clean; data not committed.
