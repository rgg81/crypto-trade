# v2 Foundation brief — survivorship-safe, parametrized portfolio engine

**Workspace:** `/home/roberto/crypto-trade/.worktrees/quant-portfolio/` (branch `quant-portfolio`).
**Data:** read klines via `pf_data/<SYM>/8h.csv` and funding via `pf_data/funding_rates/<SYM>.csv`
(symlink → the full shared dataset: 667 klines, 644 funding files). Do NOT use `data/` (sparse here).
**v1 reference code (read-only):** `analysis/portfolio/iter_002_top20.py`, `iter_004_funding.py`,
`iter_005_wf_lambda.py`, `iter_020_hysteresis.py`, `iter_021_eligexit.py`. The full v1 baseline-v3
deployed book = trend+carry (walk-forward λ) → inverse-vol → gross-norm → lag → hysteresis band
(δ=0.010 SNAP) → eligibility-exit (K=2) → renorm → vol-target. Reproduce its math EXACTLY.

This foundation is driven by the leak audit in `diary-portfolio-v2/AUDIT_portfolio_v1.md`. It fixes the
two HIGH findings (universe survivorship; missing slippage) and parametrizes the universe rank band so
the SAME engine runs v1 (top-20) and v2 (rank 21–40).

## Deliverables (TDD — write the fast unit tests FIRST, then implement to green)
1. `analysis/portfolio_v2/__init__.py`
2. `analysis/portfolio_v2/universe_v2.py` — universe loaders + PIT eligibility.
3. `analysis/portfolio_v2/engine_v2.py` — consolidated, parametrized backtest engine.
4. `tests/test_portfolio_v2.py` — fast synthetic-panel unit tests (below).
5. `analysis/portfolio_v2/parity_check.py` — slow full-universe parity gate vs iter_021 K=2.

## Exact v1 constants (must match for parity)
`HORIZONS=[21,42,84,168]`, `VOL_WIN=84`, `LIQ_WIN=90`, `MIN_HISTORY=2190`, `TOP_N=20`,
`PORT_VOL_WIN=84`, `TARGET_VOL=0.01`, `MAX_LEV=3.0`, `COST_SIDE=0.0005`, `M_FUND=9`,
`TRAIN_MONTHS=24`, `GAP_CANDLES=3`, `LAM_GRID=[0.0,0.1,0.25,0.4]`, band `DELTA=0.010` SNAP, `K_EXIT=2`.
STABLE regex: `(USDC|BUSD|FDUSD|TUSD|USD1|DAI|USDP|EUR|USTC|FRAX|PAXG|XUSD|USDE)`. OOS_CUTOFF=2025-03-24.

## universe_v2.py
- `load_pool_v1compat()` → EXACTLY v1's `iter_002.load_universe`: glob `pf_data/*USDT/8h.csv`, ex-stable,
  ascii, drop coins with `len < MIN_HISTORY`, dedup `open_time`, index sorted. (Used only for parity +
  the v1 numbers reproduction.)
- `load_pool_pit()` → the survivorship-safe pool: glob `pf_data/*USDT/8h.csv`, ex-stable, ascii, **NO
  lifetime filter** (load every coin regardless of total length; a coin with <SEASON history just never
  becomes eligible). Keep each coin's full on-disk history incl. its terminal/delist candles.
- `eligibility(coins, rank_lo, rank_hi, season)` → bool DataFrame, past-only:
  - `liq = qv.rolling(LIQ_WIN).mean().shift(1)`  (datetime index, ms→datetime as v1).
  - if `season` is None/0 → **v1-compat**: `rank = liq.rank(axis=1, ascending=False)`; `elig =
    (rank > rank_lo) & (rank <= rank_hi)` (v1: lo=0, hi=20 → `rank<=20`, identical).
  - if `season` set (e.g. 168) → **PIT**: `seasoned = close.notna().shift(1).rolling(season).sum() ==
    season` (≥season trailing non-NaN closes strictly before t); `rank = liq.where(seasoned).rank(...)`;
    `elig = seasoned & (rank > rank_lo) & (rank <= rank_hi)`. Coins not seasoned get NaN rank → excluded
    from BOTH the traded set and the rank denominator (so young coins can't steal a slot pre-signal).
- Add `candidate_count_per_year(coins, season)` diagnostic (eligible-coin count per year; must GROW
  toward 2026 under PIT — a flat count would prove residual snapshot bias).

## engine_v2.py — `run_book(coins, *, rank_lo, rank_hi, season, slip_bps_fn) -> dict`
Reproduce the v1 pipeline (iter_004 signals → iter_005 walk-forward λ stitch → iter_020/021 band +
eligibility-exit → renorm → vol-target), with TWO parametrizations:
1. eligibility from `universe_v2.eligibility(...)` (rank band + seasoning), replacing the hardcoded
   `rank<=TOP_N` everywhere it appears (build_books, eligibility_mask).
2. cost term: `cost[t] = Σ_c |Δw[c,t]| · (COST_SIDE + slip_side[c,t])` where `slip_side[c,t] =
   slip_bps_fn(dvol_M[c,t]) / 1e4`, `dvol_M = liq·3/1e6` (daily $-vol in millions, past-only).
   `slip_bps_fn=None` (or →0) MUST reduce the cost to v1's `COST_SIDE·Σ|Δw|` bit-for-bit.
Default slippage model (config-overridable, monotone, liquidity-scaled, conservative for thin coins):
`slip_side_bps(dvol_M) = clip(1.0 + 20.0/max(dvol_M, 1e-6), 1.0, 10.0)`  →  ~1.1bp @ $200M,
~1.5bp @ $40M (rank 21–40 median), ~5bp @ $5M. Expose `SLIP_A=1.0, SLIP_B=20.0, SLIP_FLOOR=1.0,
SLIP_CAP=10.0` as module constants; also support a `cost_mult` taker stress and a `slip_mult` slip stress.
Return `{net, target_w, picks, turnover, avg_positions, tickets, ...}` and IS/OOS via v1's `msharpe`.

Three canonical configs the run scripts will use:
- **PARITY:** `load_pool_v1compat()`, `rank_lo=0, rank_hi=20, season=None, slip=0` → == iter_021 K=2.
- **v1-honest (de-inflated benchmark):** `load_pool_pit()`, `rank_lo=0, rank_hi=20, season=168, slip=default`.
- **v2-anchor:** `load_pool_pit()`, `rank_lo=20, rank_hi=40, season=168, slip=default`.

## tests/test_portfolio_v2.py (FAST, synthetic panels — write these FIRST)
1. `test_rank_band_selects_2140` — synthetic 50-coin liquidity panel, constant ranks; assert
   `(20,40]` selects exactly the coins ranked 21–40 and `(0,20]` the top-20.
2. `test_seasoning_gates_young_coin` — a coin with <season history is ineligible; becomes eligible the
   candle after it crosses `season` trailing candles; verify it's excluded from the rank denominator
   before then (an else-rank-21 coin is eligible in its place).
3. `test_pit_pool_keeps_delisted_through_last_candle` — synthetic coin that ends mid-sample is present
   (eligible if seasoned+ranked) during its life and NaN/ineligible after its last candle; position
   closes (weight→0) at/after last available price, no forward fill.
4. `test_slippage_zero_reduces_to_taker` — with `slip=0`, engine cost per candle == `COST_SIDE·Σ|Δw|`.
5. `test_slippage_monotone_and_thin_pays_more` — slip cost increases with turnover and a thinner coin
   (lower dvol) incurs a strictly higher per-unit slip than a thicker one; capped at SLIP_CAP.
6. `test_leak_safety_future_perturbation` — build a small panel, run; then corrupt ALL inputs
   (open/close/qv/funding) for candles ≥ a cutoff; re-run; assert target_w AND net for candles BEFORE
   the cutoff are bit-identical (max|Δ|==0). (Mirrors iter_021's corruption gate.)
7. `test_dollar_neutrality_balanced_signal` — with a sign-balanced synthetic trend, per-candle gross
   long ≈ gross short within tolerance pre-vol-target (document any intended net tilt).
8. `test_eligibility_is_past_only` — eligibility[t] depends only on data ≤ t-1 (shift(1)); perturbing
   close/qv at exactly t does not change elig[t].

## parity_check.py (SLOW, full universe — the linchpin)
Load `load_pool_v1compat()`. Run `engine_v2.run_book(rank_lo=0, rank_hi=20, season=None, slip=0)`.
Independently compute iter_021 K=2 net (`h20.build_books`→`h20.canonical_book`→`ee.eligibility_mask`
→`ee.eligexit_net(K=2)`). Inner-align; assert `max|Δ| < 1e-9` and equal length; print PASS/FAIL +
IS/OOS for both. This proves the consolidated engine is a faithful port before any correction is judged.

## Rules
- Past-only everywhere; no OOS tuning; report net (after taker+slippage+funding). Keep the v1 corruption
  -test discipline. Run `uv run ruff check` + `uv run pytest tests/test_portfolio_v2.py -q`. Do NOT run
  the slow full backtests as part of unit tests; the orchestrator runs parity_check.py + the configs
  separately. Report exact commands + any parity diff.
