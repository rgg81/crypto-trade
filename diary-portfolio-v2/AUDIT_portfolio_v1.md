# Adversarial leak audit — `portfolio-iteration` (v1, top-20 L/S)

Max-effort multi-agent audit (22 agents, ~1.8M tokens): recon → 6 leakage dimensions
(timing, universe, walk-forward, funding/cost, multiple-testing, band/eligibility) → every
candidate finding independently re-verified by a second `quant-critic`. 14 candidate findings,
**6 confirmed**, 1 uncertain.

## What is clean (verified, not just claimed)
- **Signal timing / look-ahead** — clean. Trend `sign(close/close.shift(h)-1)`, liquidity rank
  `qv.rolling(90).mean().shift(1)`, `rvol`, vol-target scale all past-only; weights `.shift(1)`
  lagged; the only forward shift is `ret_fwd = open.shift(-1)/open-1`, the realized return the
  *already-lagged* weight earns (correct close[t]→open[t+1] fill). iter_021 ships an explicit
  future→past corruption test that passes bit-identically (max|Δ| = 0 before cutoff).
- **Funding join** — the old ~28% inflation bug (exact-match on jittery timestamps) is fixed:
  nearest-match within 4h tolerance, correct sign (longs pay positive funding), `fund.shift(-1)`
  applied to the held candle. Low residual risk only if a funding update is >4h late.
- **Hysteresis band + eligibility-exit + gross renorm** — path-dependent on strictly past state;
  renorm drift ≈ 1e-15; no forward peek.

## Confirmed issues (in priority order for v2)

### 1. Universe survivorship / look-ahead — **HIGH** (the big one)
`analysis/portfolio/iter_002_top20.py:37-51`. `load_universe()` globs the **2026 on-disk** coin set
and keeps a coin only if `len(k) >= MIN_HISTORY=2190` (~2y of *total lifetime* history). The
candidate pool is fixed **once** for the entire 2020–2026 backtest.
- A coin that listed and delisted in <2y is excluded from **every** historical candle's top-20 —
  even candles where it was genuinely liquid and tradeable (e.g. `ANCUSDT` / Anchor, 201 candles,
  dropped; Terra-era names). Requiring ≥2y of history for a 2022 decision implicitly requires
  survival into 2024+ → a post-decision fact gates membership = future→past flow.
- Direction: excluded names are disproportionately **failed alts whose terminal collapse** a
  trend/long book would have been hurt by → survivor pool's realized returns biased **upward** →
  inflates the headline IS/OOS Sharpe and the +1271% net.
- **Bounded** (not full cherry-pick): the within-pool PIT volume rank is leak-safe, and some
  zombies (TOMO, BLZ) *are* retained — so it's "under-inclusive of short-lived names," not winner
  selection. Severity graded high→low across the three independent reports.
- **Process integrity:** the skill (line 92, "point-in-time, no survivorship cherry-pick") and
  diaries (EXPLORATION-012:120, 016:25, "zero survivorship") are **materially false**; EXPLORATION-017
  mis-classifies the filter as a benign "data-provenance decision."
- **Fix:** point-in-time pool. Load **all** ex-stable USDT perps incl. delisted; admit a coin at
  candle t iff it has ≥ (lookback) trailing candles available **as of t** (per-bar seasoning), keep
  delisted coins through their actual last trade (post-delist cells NaN → ineligible → position
  closes at last price). Add a survivorship-direction test; print candidate count per year (should
  grow toward 2026 — a flat count proves the snapshot bias).

### 2. Slippage absent from the deployed cost model — **HIGH**
`iter_021:143`, `iter_020:186`, `iter_004:62`, `iter_002:98`. The skill mandates "taker fee **+
slippage** per turnover," but every P&L path charges only `COST_SIDE=0.0005` taker — a repo-wide
grep for slippage/spread/impact returns **zero** cost terms. The promoted number is the
slippage-free backtest; the 2× column is a stress, never the headline. Strategy is cost-sensitive
(OOS +1.66→+1.17 at 2× taker, ~0.49 give-back). **Matters more for v2:** rank 21–40 is thinner than
the top-20, so a flat "deep/liquid" assumption is weaker on the marginal names.
- **Fix:** add a per-side slippage term, **liquidity-scaled** (thinner coin ⇒ higher bps), so
  `net = pnl + funding − (taker + slip)·Σ|Δw|`. Re-evaluate promotion at the slippage-inclusive
  Sharpe. Until then treat promoted OOS as an upper bound.

### 3. Multiple-testing under-correction — **MEDIUM**
`iter_018_confirm.py:57-61`. The lone DSR correction deflates for `N_TRIALS=14`, but the same frozen
16-month OOS window was scored across **>100** configs program-wide (iter_013 ~22 grid cells, iter_019
~31, iter_020 ~10, iter_021 6, iter_012 ~24, …). DSR is anti-conservative. Mitigated: that run's
verdict was already HOLD at N=14, and intra-family correlation means true `N_eff` is between 14 and
100. **Fix:** exposure-honest `N_eff` (PCA/cluster the cross-config OOS return matrix); sweep DSR over
N ∈ {14, 50, 100}.

### 4. OOS repeatedly viewed across iterations — **LOW / not a leak** (uncertain)
OOS column printed at every EXPLORATION despite the skill's "evaluate OOS once per confirmation."
Program-level OOS-hygiene/multiple-testing concern, **not** a data leak (no future→past flow), with
strong mitigants (carry tilt re-earned by honest walk-forward λ; robustness sweeps; fail-closed gates;
iter_012 rejected despite a tempting OOS). **Fix:** suppress OOS in EXPLORATION diaries, reveal only
at CONFIRMATION, attach a deflated-Sharpe.

## Where v1 "lost" (trajectory of 21 iterations)
Survived: **trend + carry tilt (walk-forward λ)** + hysteresis band + eligibility-exit. Rejected:
**cross-sectional momentum on the top-20** (002), short-term reversal (008), per-coin caps (009),
magnitude-vs-sign (010), liquidation-fade (011), funding-acceleration (016), perp-spot basis (017),
regime gross-overlay (019); taker-flow real but corner-weight, never promoted (013/018 HOLD, DSR 0.73).
Edge concentrated in the thin 2020–21 illiquid era (partly survivorship-inflated). maxDD −22/−23%.
Cost-sensitive.

## Implications for v2 (rank 21–40)
1. **Build survivorship-safe from candle one** (fix #1) — the rank-21–40 PIT pool must come from the
   full delisting-inclusive set with per-bar seasoning, not a 2026 survivor snapshot.
2. **Slippage-inclusive, liquidity-scaled cost** (fix #2) — mandatory given the thinner cohort.
3. **Cross-sectional momentum is the prime "win where it lost" axis** — it failed on the efficient
   BTC/ETH-heavy top-20 but mid-caps (21–40) have far richer cross-sectional dispersion; this is the
   textbook place XS-mom works.
4. **Honest accounting** (fixes #3/#4) — N_eff at confirmation; OOS hidden until confirmation.
5. For a fair comparison, also re-run the **v1 stack on the corrected universe** so v2 is benchmarked
   against an honest (de-inflated) v1, not the survivorship-inflated headline.
