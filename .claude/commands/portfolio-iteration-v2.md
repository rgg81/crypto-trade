# Portfolio Iteration v2 — systematic LONG/SHORT rank-21–40 ("next-20") crypto perp portfolio

## Mission
Build, and then **improve little by little**, a systematic **long/short rank-21–40 (ex-stablecoin)
perpetual-futures portfolio** on Binance Futures — the liquid mid-cap cohort *just below* the top-20
that the v1 skill (`portfolio-iteration`) trades. Medium-frequency (8h candle decisions, daily/weekly
effective rebalance), plain **taker** fees **+ slippage**, no HFT, no market-making, no VIP tier.

This is the sister track to v1. Same machinery, **different universe scope**, and two methodological
upgrades forced by the v1 leak audit (`diary-portfolio-v2/AUDIT_portfolio_v1.md`):
survivorship-safe point-in-time universe construction, and a slippage-inclusive cost model.

**Why 21–40 can win where v1 lost.** v1's edge collapsed to *trend + a small carry tilt*;
**cross-sectional momentum was rejected on the top-20** (EXPLORATION-002) because BTC/ETH-dominated
mega-caps are too few and too efficient to supply cross-sectional dispersion. The rank-21–40 cohort
(INJ, UNI, AAVE, OP, TIA, SEI, WIF, ICP, HBAR, XMR, …) is the textbook home of XS-momentum: more
names, richer dispersion, stronger retail-driven trend persistence. The cost is thinner liquidity
(cohort daily $-vol median ~$40–100M vs ~$200–400M for the top-20) — which is exactly why the
slippage upgrade is mandatory here.

## The philosophy (READ THIS — it is the point)
**Improve little by little.** Each EXPLORATION makes ONE change, measured on the backtest. A change
that helps gets kept; one that doesn't informs the next. Negative results narrow the search — they do
not end it. Be rigorous about overfitting, NOT defeatist about edges.

## Rigor (v1 gauntlet + the two audit fixes)
A change is "real" when it survives:
1. **Realistic execution** — signal on candle CLOSE[t], rebalanced at OPEN[t+1], held; **taker fee +
   liquidity-scaled slippage** per turnover; **funding** paid/earned on perp holds. Leak-safe (signals
   past-only; keep the future→past corruption test green).
2. **Survivorship-safe point-in-time universe** *(audit fix #1)* — the candidate pool is the FULL
   ex-stable USDT-perp set including delisted names, with per-bar **seasoning** (a coin is eligible at
   t only if it has ≥`SEASON` trailing candles AS OF t) and the rank-band `(20,40]` computed among
   seasoned coins. NO lifetime/MIN_HISTORY snapshot filter. Delisted coins stay in the panel through
   their last real candle (positions close at last price). Diagnostic: eligible-coin count per year
   must GROW toward 2026 (a flat count proves snapshot bias).
3. **Slippage-inclusive cost** *(audit fix #2)* — `net = pnl + funding − (taker + slip)·Σ|Δw|`,
   `slip` liquidity-scaled per coin (thinner ⇒ more bps). Report Sharpe at 1×/2× taker AND 1×/2× slip.
   The deployed number is the slippage-inclusive one, never the slippage-free upper bound.
4. **Walk-forward params** — any tunable (λ, thresholds) selected per-period on PAST data; structural
   params proven by robustness sweep (all configs positive), never per-month-overfit.
5. **OOS holdout** — `OOS_CUTOFF = 2025-03-24`. **OOS is hidden during EXPLORATION** (print IS + the
   walk-forward-stitched metric only); revealed ONCE at CONFIRMATION *(audit fix #4)*. Judge per-year
   robustness, don't over-react to one window.
6. **Multiple-testing honesty** *(audit fix #3)* — at CONFIRMATION, deflate OOS Sharpe with an
   exposure-honest `N_eff` (cluster/PCA the cross-config OOS return matrix), NOT a hand-set trial
   count. Keep a running ledger of configs whose OOS was viewed program-wide.
7. **Benchmarks** — beat buy-and-hold BTC AND an equal-weight rank-21–40 basket on risk-adjusted
   terms; AND beat the **de-inflated v1** (v1 stack re-run on the same corrected PIT universe).

## Foundation (build once, reuse every iteration)
- `analysis/portfolio_v2/engine_v2.py` — consolidated, parametrized backtest engine: `run_book(coins,
  rank_lo, rank_hi, season, slip_bps_fn)` → trend+carry (walk-forward λ) → inverse-vol → gross-norm →
  lag → hysteresis band → eligibility-exit → renorm → vol-target → net (taker+slippage+funding).
  Reduces to v1 bit-for-bit in v1-compat mode (parity gate).
- `analysis/portfolio_v2/universe_v2.py` — `load_pool_pit()` (survivorship-safe), `load_pool_v1compat()`
  (parity only), `eligibility(rank_lo, rank_hi, season)`, `candidate_count_per_year`.
- `analysis/portfolio_v2/parity_check.py` — engine_v2(v1-compat) == iter_021 K=2 to <1e-9 (linchpin).
- `tests/test_portfolio_v2.py` — rank-band, seasoning, PIT-delisting, slippage, leak (future
  perturbation), dollar-neutrality, past-only eligibility.
- Data on disk via `pf_data/<SYM>/8h.csv` + `pf_data/funding_rates/<SYM>.csv` (8h candles — sacred).

## Three canonical configs
- **PARITY** — `load_pool_v1compat()`, `(0,20]`, season=None, slip=0 → reproduces v1 iter_021 K=2.
- **v1-honest (de-inflated benchmark)** — `load_pool_pit()`, `(0,20]`, season=168, default slip.
- **v2-anchor** — `load_pool_pit()`, `(20,40]`, season=168, default slip. ← the v2 starting baseline.

## Roles — AGENT-DRIVEN (do NOT work solo; use the full team EVERY iteration)
- **quant-researcher** — designs the EXPLORATION (the one change, crypto-native rationale).
- **quant-engineer / risk-engineer** — implements + runs the backtest.
- **quant-critic** (read-only, CONSTRUCTIVE) — reviews EVERY result: (a) adversarial findings incl. the
  MANDATORY data-leak corruption test + the survivorship-direction test + slippage-realism check +
  selection-bias/N_eff; (b) concrete fixes + the next idea. No promotion without a critic PASS; every
  BLOCK carries a path forward.

## Cadence
- **EXPLORATION** — one change, scored on the backtest + the non-OOS rigor checks (OOS hidden). Logged
  to `diary-portfolio-v2/EXPLORATION-NNN.md` with numbers + verdict + critic note.
- **CONFIRMATION** — reveal OOS + full gauntlet + N_eff-deflated Sharpe; only this (with a critic PASS)
  promotes a change to the baseline. Commit every step honestly, incl. down-corrections.

## NO CHEATING (hard)
- Never reintroduce the lifetime/MIN_HISTORY survivorship snapshot. Universe membership is PIT.
- Never report a slippage-free number as deployable. Never reveal OOS at EXPLORATION stage.
- A param earns per-month walk-forward tuning ONLY if proven non-stationary; structural params get a
  robustness sweep. Never exact-match-join jittery funding timestamps. Refresh stale data. Report
  DOWN-corrections openly. If a result looks too good, assume a bug until the critic clears it.

## CURRENT BASELINE (2026-06-23, iter-v2-001…009) — see `diary-portfolio-v2/BASELINE_PORTFOLIO_V2.md`
**Dollar-neutral cross-sectional momentum, rank 21–40, 8h: XS-mom 5-way ensemble {42,63,84,126,168} via
`run_book_from_signal` + risk layer (TARGET_VOL=0.006, MAX_LEV=2.0).** OOS **+1.37** (2× taker +1.03),
OOS maxDD −16%, turn 0.157, fixed-parameter, leak-safe. The ported top-20 trend stack (the anchor) is
OOS-dead (−0.01) on this cohort — this is "win where v1 lost." PSR(>0)=0.94, DSR≈0.83 (XS-family) /
0.37 (all-classes) → real but MODERATE deflated significance; strong candidate, not a certainty.

**Dead paths (closed):** fixed-γ trend+XS blend (/002), L2 cross-sectional ML (/003), BTC-beta-residual
momentum (/004), factor-momentum routing (/005), weekly/monthly rebalance (/006), funding-fade sleeve
(/009). "Combine trend+XS-mom" axis family closed; carry regime-faded.

## Roadmap
1. **iter-v2-001…009 — DONE.** Anchor (OOS-dead) → XS-mom edge found (/006) → risk layer (/007) →
   ensemble robustness (/008) → funding rejected (/009). Baseline established (above).
2. **Open items before real capital:** exact-weight-hold confirmation backtest; R2 live full-seasoning
   gate (warmup non-neutrality); monitor the 2026 sub-window + the DSR (carry-style fade risk).
3. **Next EXPLORATIONs** (each one change, kept only if it lifts slippage-inclusive net Sharpe vs the
   ensemble baseline, judged on IS+LATE then ONE OOS reveal, deflation tracked): short-term cross-
   sectional reversal (different signal class); dispersion-conditional gross; vol-scaled ranks;
   universe-band sensitivity (21–50 vs 16–40). CONFIRMATION → baseline → repeat.

## Sacred constants
- `OOS_CUTOFF = 2025-03-24` (immutable). 8h candles. Signals past-only; fills at open[t+1].
- Universe = rank-21–40 by trailing-90 mean $-volume, ex-stablecoins, **point-in-time + seasoned**,
  delisting-inclusive. `RANK_LO=20, RANK_HI=40, SEASON=168`.
- Cost = taker (0.0005/side) + liquidity-scaled slippage. Report net, not gross. Never tune on OOS.

## Run
```
export PATH="$HOME/.local/bin:$PATH"
uv run pytest tests/test_portfolio_v2.py -q                 # foundation stays green
uv run python analysis/portfolio_v2/parity_check.py          # v1-compat parity gate (<1e-9)
uv run python analysis/portfolio_v2/iter_v2_001_anchor.py    # current iteration
```
