# BRIEF — deploy the v2 baseline live on testnet (mirror the v1 portfolio engine)

Reproduce the v1 live portfolio setup for the **v2 baseline** (rank-21–40 dollar-neutral XS-mom 5-way
ensemble + risk layer), FULLY ISOLATED from the running v1 engine. Parity-by-construction is the hard
requirement: the live target weights must equal the backtest's deployed book for the upcoming candle.

**Workspace:** `/home/roberto/crypto-trade/.worktrees/quant-portfolio/` (branch quant-portfolio).
`export PATH="$HOME/.local/bin:$PATH"`. **DO NOT touch** the quant-research worktree (v1 is LIVE there).

## Reference (read first)
- v1 live executor: `src/crypto_trade/portfolio/engine.py` (`PortfolioEngine`, `PortfolioConfig`) +
  `src/crypto_trade/portfolio/strategy.py` (the interface the engine calls) +
  `.worktrees/quant-research/run_portfolio_testnet.py` (the runner, $4k/1x). Read all three.
- v2 backtest: `analysis/portfolio_v2/engine_v2.py` (`run_book_from_signal`, `_xsmom`, `build_panel`,
  `vol_target`), `universe_v2.py` (`load_pool_pit`, `eligibility`, `DATA_GLOB`), and the baseline spec
  in `diary-portfolio-v2/BASELINE_PORTFOLIO_V2.md`.

## The v2 deployed-weight definition (PARITY-CRITICAL — get this exactly right)
The live target per coin for the HOLD candle = **the last row of `held_w × scale`** from the v2 pipeline
run with the RISK LAYER on:
- signal = XS-mom 5-way ensemble: `mean over L∈{42,63,84,126,168} of unit-L1-normalized
  _xsmom(close, elig, L)`, then unit-L1 normalize the mean (exactly as `iter_v2_008_ensemble.py`).
- run `engine_v2.run_book_from_signal(coins, signal, rank_lo=20, rank_hi=40, season=168,
  slip_bps_fn=default_slip_bps)` **with `engine_v2.TARGET_VOL=0.006` and `engine_v2.MAX_LEV=2.0`**
  (the frozen risk layer) — set these module globals before the call.
- the deployed book = `result["held_w"].mul(result["scale"], axis=0)` (vol-targeted, banded book —
  the same `w × scale` pattern v1's `strategy._deployed_weights` returns). The LIVE target = its LAST ROW.
- `coins` must end at the HOLD candle (include the just-opened forming candle's open via the
  close-proxy), identical to v1's `forming_from_close` / `append_forming`. Recompute from FULL history
  each tick (the band/eligexit/vol-target path-dependence is reproduced from data, as in v1).

## Deliverables (quant-portfolio worktree only)
1. **Make the v2 data paths configurable** (so live reads the fresh fetched `data/`, parity reads `pf_data`):
   - `universe_v2.DATA_GLOB` is already a module const — keep default `"pf_data/*USDT/8h.csv"`.
   - Add a module-level funding dir to `engine_v2` (e.g. `FUNDING_DIR = "pf_data/funding_rates"`) and make
     `_load_funding` read `f"{FUNDING_DIR}/{sym}.csv"`. Default unchanged (parity-safe).
   - `strategy_v2` flips both to the live `data/` dir at import for the live process.
2. **`src/crypto_trade/portfolio_v2/__init__.py`** + **`src/crypto_trade/portfolio_v2/strategy_v2.py`** —
   mirror v1 `strategy.py`'s interface so it's a drop-in for the engine:
   - `DELTA = 0.010`
   - `candidate_symbols()` → ex-stable ascii USDT-perp symbols from the live data dir (mirror v1).
   - `load_universe()` → `universe_v2.load_pool_pit()` reading the live data dir.
   - `forming_from_close(coins)` / `append_forming(coins, forming_opens)` → same close-proxy forming-candle
     logic as v1 `strategy.py` (8h step; next-open ≈ last close).
   - `next_target_weights(coins, delta=DELTA)` → compute the deployed book per the PARITY-CRITICAL section;
     return `{sym: float(weight) for non-trivial}` + `"_meta": {as_of, gross, n_positions}`. The weights
     are the vol-targeted banded positions (gross ≈ scale ≈ 0.3–0.6 after the de-lever).
3. **Engine dependency-injection** — in THIS worktree's `src/crypto_trade/portfolio/engine.py`, add a
   `strategy_module` param to `PortfolioEngine.__init__` (default = the v1 `strategy` import, fully
   back-compatible) and replace the module-level `strategy.X` calls in `compute_plan` / `refresh_data`
   with `self.strat.X`. Minimal diff; v1 behavior unchanged when the param is omitted.
4. **`run_portfolio_v2_testnet.py`** (worktree root) — mirror `run_portfolio_testnet.py`:
   `equity_usd=4000, leverage=1.0, dry_run=<arg>, testnet=True, db_path="data/portfolio_v2_testnet.db",
   poll_interval_seconds=60`, `delta=0.010`, and pass `strategy_module=strategy_v2` to the engine. Accept
   a `--dry-run` CLI flag (default dry-run TRUE for the first smoke test; real when omitted... no — default
   dry-run TRUE, require `--live-testnet` to actually place orders, so a bare run never trades by accident).
5. **`analysis/portfolio_v2/parity_live_check.py`** — the GATE: load `pf_data` (the backtest snapshot),
   compute (a) `strategy_v2.next_target_weights` on that snapshot and (b) the backtest
   `run_book_from_signal(... risk layer ...)` deployed-book last row, and assert per-coin
   `max|Δweight| < 1e-9`. Print PASS/FAIL + the top legs. This proves the live wrapper reproduces the
   backtest before any order.

## Verify (paste real output) — but DO NOT launch the real-order engine (orchestrator does that)
- `ruff` clean; `uv run pytest tests/test_portfolio_v2.py -q` still 16/16 (engine_v2 funding-dir change
  must not perturb parity_check — run `analysis/portfolio_v2/parity_check.py`, still 1.041e-16).
- `uv run python analysis/portfolio_v2/parity_live_check.py` → PASS (<1e-9).
- A DRY-RUN single tick: `run_portfolio_v2_testnet.py` in dry-run mode does ONE `run_once` and prints a
  sane rebalance plan (≈ a dollar-neutral book of ~20 names, gross ~0.3–0.6×equity), no orders. (You may
  need to fetch data first — `uv run crypto-trade fetch` is fine, OR symlink/point the live data dir at
  pf_data for the dry smoke; note which you did.)

REPORT: files written, ruff/pytest/parity_check/parity_live_check results, the dry-run plan output, and
the exact command to launch real testnet orders. Do NOT place real orders. Do NOT modify the
quant-research worktree or v1 files.
