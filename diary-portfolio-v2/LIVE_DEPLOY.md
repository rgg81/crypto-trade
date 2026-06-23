# v2 LIVE DEPLOYMENT (Binance testnet) — record + the universe-contamination fix

**Deployed:** 2026-06-23, rank-21–40 dollar-neutral XS-mom 5-way ensemble + risk layer, on Binance
**testnet** (fake money — full integration smoke before real money). FULLY ISOLATED from the live v1
engine. Mirrors the v1 setup via a `strategy_module` DI seam.

## The stack (all in the quant-portfolio worktree)
- `src/crypto_trade/portfolio_v2/strategy_v2.py` — live weight engine, parity-by-construction (deployed
  weight = last row of `held_w × scale` from `run_book_from_signal`, risk layer TARGET_VOL=0.006/MAX_LEV=2.0).
- `src/crypto_trade/portfolio/engine.py` — added a back-compatible `strategy_module` param (v1 default).
- `run_portfolio_v2_testnet.py` — equity $4k, lev 1x, db `data/portfolio_v2_testnet.db`, DRY-RUN default
  (`--live-testnet` to trade). Log `logs/portfolio_v2_testnet.log`.
- Creds: `~/.binance_testnet_v2_env` (SEPARATE v2 testnet account, $5k faucet). NEVER in the repo.
- Data: isolated `data/` (copied from the shared snapshot; the engine refreshes its own copy).
- Gates passed pre-launch: LIVE-PARITY max|Δ|=0.0, parity_check 1.041e-16, 16/16 tests, sane dry-run plan.

## CRITICAL FIX — universe contamination caught at the FIRST live order
The first cold-start entry surfaced 4 order errors; 2 were a real strategy-validity defect:
```
INTCUSDT/CRCLUSDT  -4411 "sign TradFi-Perps agreement"  ← tokenized STOCKS (Intel/Circle)
OPNUSDT            -1121 "Invalid symbol"               ← testnet-only (valid on production)
SIRENUSDT          -4131  PERCENT_PRICE filter          ← testnet thin-liquidity (fills on production)
```
**The v2 universe was picking up NON-COIN perps** — Binance lists tokenized stocks (EQUITY: INTC, CRCL,
AMZN, COIN, MSTR, NVDA, TSLA, GOOGL, SPY…), commodities (XAU/XAG/COPPER), index baskets (BTCDOM, DEFI),
and pre-market/pre-IPO tokens, all as `…USDT` perps. They ranked into the 21-40 band by volume — **INTC
was the LARGEST position** (+$380). A crypto cross-sectional momentum strategy must not trade these
(different dynamics, TradFi agreements, special filters). 31 non-COIN symbols polluted the pool: stocks
(recent, ~400 candles → hit the OOS) AND BTCDOM/DEFI indices (5485/6376 candles → present throughout).

**FIX:** `universe_v2.NON_COIN_PERPS` — exclude every symbol with Binance `underlyingType != COIN`
(47 symbols), applied to `load_pool_pit` ONLY (`load_pool_v1compat` untouched → v1 parity gate intact).
Regenerate from exchangeInfo when listings change.

## Re-validation — the edge SURVIVES crypto-only (de-inflated, still strong)
| ensemble baseline | OOS | 2025 | 2026 | 2×-taker | turn |
|---|---|---|---|---|---|
| contaminated (stock-perps) | +1.37 | +1.61 | +0.84 | +1.03 | 0.157 |
| **CRYPTO-ONLY (corrected)** | **+1.16** | +1.58 | +0.62 | **+0.90** | 0.156 |

Stock-perps inflated OOS by ~+0.21 (mostly 2026, where they listed). The core crypto edge is real and
cost-robust: **OOS +1.16, +0.90 at 2× taker, both sub-windows positive, IS +0.45, LATE +1.46.** v2 stays
a valid baseline — honestly de-inflated. (Live-parity re-verified at 0.0 on the clean universe; the
clean cold-start plan is stock-perp-free: BCH/ASTER/PUMP/JTO/SYN/UNI…, gross 0.457.)

## Testnet-specific execution notes (NOT strategy faults; expected to vanish on production)
- A few COIN names per rebalance can't fill on testnet only: `-1121 Invalid symbol` (listed on production
  but not testnet), `-4140 invalid status for opening`, `-4131 PERCENT_PRICE` (testnet's thin book).

## PAPER-FALLBACK (added 2026-06-23) — keeps the testnet book faithful to the strategy
`PortfolioConfig.paper_untradeable=True` (v2 runner; OFF for v1 + production). When a real order fails
with a testnet-untradeable code (`-1121/-4131/-4140/-4411/-4061/-4046`), the engine adds that symbol to
a persisted PAPER set (`engine_state["portfolio_paper"]`) and tracks its target weight there instead of
dropping the leg. Mechanism: `run_once` merges the paper-held weights into the `current` book, so the
strategy holds its FULL intended 20-name book — no MISSING drift, no net tilt from un-placed legs — while
the venue holds only the real legs. Each untradeable symbol errors at most ONCE (then it's papered, never
retried). `errors` drops to ~0; the log shows `papered=N` + `PAPER-FALLBACK <sym>` lines. The paper
positions are simulated (not on the exchange), so the healthcheck's EXCHANGE position count stays at the
real legs; the STRATEGY's book (real + paper) matches the target. **Turn it OFF for the production cutover**
— there, every COIN fills, so a MISSING leg would be a REAL alert, not something to paper over.

## Real-money readiness follow-ups (before swapping testnet→production)
1. Refresh `NON_COIN_PERPS` from production exchangeInfo (testnet ≠ production listing set).
2. Optional engine hardening: skip symbols not `TRADING`-status in exchangeInfo pre-order (silence -1121).
3. Update BASELINE_PORTFOLIO_V2 headline to the crypto-only +1.16; re-run the combined v1+v2 estimate.
4. Tighten monitor cadence + run the pre-flight before the production cutover.
