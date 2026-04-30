# crypto-trade

## Build & Run

- `uv sync` — install all dependencies
- `uv run crypto-trade` — run the application (shows status + help)
- `uv run python -m crypto_trade.main` — alternative way to run

## CLI Subcommands

### `fetch` — Fetch klines via REST API

- `uv run crypto-trade fetch` — fetch all configured symbols/intervals
- `uv run crypto-trade fetch --symbols BTCUSDT,SOLUSDT` — specific symbols
- `uv run crypto-trade fetch --intervals 1h,15m` — specific intervals
- `uv run crypto-trade fetch --start 2024-01-01` — from a specific date
- `uv run crypto-trade fetch --all` — all active perpetual symbols from exchange info
- Re-running `fetch` is incremental — only appends new klines

### `bulk` — Bulk download from data.binance.vision

- `uv run crypto-trade bulk --symbols BTCUSDT,ETHUSDT --intervals 1m,15m` — specific symbols
- `uv run crypto-trade bulk --all --intervals 1m,15m` — all symbols (including delisted)
- `uv run crypto-trade bulk --symbols BTCUSDT --intervals 1m --api-backfill` — bulk + fill current month via API
- Downloads monthly ZIP archives — much faster than API for historical data
- Incremental: re-running skips already-downloaded months

### `backtest` — Run strategy backtests

- `uv run crypto-trade backtest --list` — list all available strategies
- `uv run crypto-trade backtest --strategy momentum --symbols BTCUSDT --interval 15m` — basic run
- `uv run crypto-trade backtest --strategy rsi_bb --symbols BTCUSDT --interval 15m --range-spike-filter` — with notebook volatility filter
- `uv run crypto-trade backtest --strategy mean_reversion --symbols BTCUSDT,ETHUSDT --interval 15m --start 2024-01-01 --end 2024-12-31` — date range
- `uv run crypto-trade backtest --strategy momentum --symbols BTCUSDT --interval 15m --stop-loss 2.0 --take-profit 3.0 --timeout 120 --fee 0.1` — custom SL/TP/timeout/fee
- `uv run crypto-trade backtest --strategy mean_reversion --symbols BTCUSDT --interval 15m --params lookback=30,multiplier=3.0` — custom strategy params
- `uv run crypto-trade backtest --strategy momentum --symbols BTCUSDT --interval 15m --report` — generate quantstats HTML tearsheet (auto-named)
- `uv run crypto-trade backtest --strategy momentum --symbols BTCUSDT --interval 15m --report my_report.html` — custom output path
- `--range-spike-filter` and `--volume-filter` can be combined with any strategy
- Strategies: `momentum`, `mean_reversion`, `wick_rejection`, `inside_bar`, `gap_fill`, `consecutive_reversal`, `rsi_bb`, `bb_squeeze`

### `seed-live-db` — Import backtest trades to recover R1/R2/VT/cooldown state

The live engine rebuilds risk state on startup by replaying every closed trade in its DB:

- `_rebuild_vt_history()` → per-symbol daily PnL for vol targeting (45-day rolling).
- `_rebuild_risk_state()` → R1 per-symbol consecutive-SL streak + cooldown_until, R2 per-model cumulative weighted PnL + running peak.
- R3 (OOD Mahalanobis) is **not DB-backed** — it's recomputed from each model's training-window stats at training time, so nothing to seed.

If the DB is empty, the engine starts cold (no SL streaks, no R2 peak, no VT history) and diverges from the backtest until catch-up has rebuilt ~1–3 months of history. To avoid this, seed the DB from the most recent backtest trade CSVs before launching.

```
uv run crypto-trade seed-live-db \
  --db data/<target>.db \
  --track both \
  --v1-trades reports/iteration_186/in_sample/trades.csv \
  --v1-trades reports/iteration_186/out_of_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/in_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/out_of_sample/trades.csv \
  [--as-of YYYY-MM-DD]
```

Target DB must match what the engine opens at startup (resolution priority `testnet > dry_run > live`, see `engine.py:241-246`):
- `data/dry_run.db` → `live` (no flags) or `live --dry-run`
- `data/testnet.db` → `live --testnet`
- `data/live.db` → `live --live`

Behavior:
- Inserts trades that closed before `--as-of` as `status='closed'` so `_rebuild_*` reproduce backtest R1/R2/VT/cooldown exactly.
- Trades that span `--as-of` (open before, close after) become `status='open'` with `entry_order_id='SEEDED'` + full intended-exit info; the engine's catch-up loop closes them deterministically at the seeded `exit_time`.
- Skips trades that opened after `--as-of` — the engine's catch-up replay re-creates them from candles + signals.
- Drops zero-`weight_factor` rows (BTC-killed v2 trades).
- Sets per-`(model, symbol)` `cooldown_<model>_<symbol>` engine_state keys.
- Without `--as-of`: seeds everything up to the CSV end-of-data; trades still open at end-of-data become `status='open'`.

Pair the seeder's `--as-of` with the engine's `--catch-up-from <same-date>` so the two cover the full timeline without gaps or duplicates.

### Testnet workflow — end-to-end

Run the engine against the Binance Futures testnet (https://testnet.binancefuture.com) as a full smoke test of the auth integration before pointing at production. Testnet has its own API keys, balances, and matching engine; klines stay on production so feature regen and catch-up see the full historical OHLCV the backtest used.

**Step 1 — get testnet credentials.** Visit https://testnet.binancefuture.com, sign in (separate from binance.com), create an API key + secret. Add them to the shell or `.env`:

```
export BINANCE_API_KEY=<testnet-key>
export BINANCE_API_SECRET=<testnet-secret>
# Optional — override the testnet host (default https://testnet.binancefuture.com):
# export BINANCE_AUTH_BASE_URL=https://staging.binancefuture.com
```

`--testnet` requires non-empty credentials — the engine errors out (no silent dry-run fallback). The production base URL stays as `BINANCE_BASE_URL` so kline fetches still hit production.

**Step 2 — refresh klines and features.** The engine has a 16h staleness guard.

```
uv run crypto-trade fetch \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT,DOGEUSDT,SOLUSDT,XRPUSDT,NEARUSDT \
  --intervals 8h
uv run crypto-trade features \
  --symbols BTCUSDT,ETHUSDT,LINKUSDT,LTCUSDT,DOTUSDT,DOGEUSDT,SOLUSDT,XRPUSDT,NEARUSDT \
  --interval 8h --track v1 --format parquet --workers 4
uv run crypto-trade features \
  --symbols BTCUSDT,DOGEUSDT,SOLUSDT,XRPUSDT,NEARUSDT \
  --interval 8h --track v2 --format parquet --workers 4
```

**Step 3 — reproduce the backtest** (skip if you already have fresh CSVs in `reports/iteration_186/` and `reports-v2/iteration_v2-069/`):

```
uv run python run_baseline_v186.py    # ~10h
uv run python run_baseline_v2.py      # ~5h, single seed
```

**Step 4 — seed the testnet DB** from the freshly-generated CSVs. `--as-of` is optional; omitting it seeds everything up to data extent, which is the simplest setup for a brand-new testnet run:

```
uv run crypto-trade seed-live-db \
  --db data/testnet.db \
  --track both \
  --v1-trades reports/iteration_186/in_sample/trades.csv \
  --v1-trades reports/iteration_186/out_of_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/in_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/out_of_sample/trades.csv
```

Verify with `sqlite3 data/testnet.db "select status, count(*) from trades group by status;"`.

**Step 5 — launch on testnet.** Default 90-day catch-up is fine when the seeder covered everything; otherwise pass `--catch-up-from <day-after-last-seeded-close>` to bound the replay precisely.

```
uv run crypto-trade live --testnet --track both --amount 100 --leverage 1
```

What you should see at startup:
- Banner: `[live] AUTH endpoint OVERRIDE: https://testnet.binancefuture.com`.
- `[live] Rebuilt VT history: <N> daily PnL entries across <M> symbols`.
- `[live] Rebuilt risk state: <K> R1 cooldowns armed, R2 cum PnL by model = {…}`.
- Per-model warmup + per-month LightGBM training (~hours on a fresh-month start; mid-month restarts skip retrain).
- `[live] Entering poll loop (every 60s)`.

What goes where:
- Signed calls (`place_market_order`, `place_stop_market_order`, `place_take_profit_market_order`, `get_order`, `set_leverage`, `get_positions`, `cancel_order`) → testnet.
- Kline fetches → production (`https://fapi.binance.com`).
- DB → `data/testnet.db`. Trade log → `data/testnet_trades.csv`. Neither overlaps with `data/live.db` / `data/dry_run.db`.
- `--testnet` forces live trading (sets `dry_run=False`); seeded-DB carry-over trades are still tagged paper via `is_paper_trade` and exit on candle SL/TP without sending Binance orders (fix `dba16ec`).

**Step 6 — resume / clean up.**
- Ctrl-C is safe; DB persists. Re-running with the same flags resumes — open trades reconcile against testnet, paper rows skip the exchange.
- Reset to a fresh state with `rm data/testnet.db data/testnet_trades.csv`.

**Going to production:** swap `--testnet` for `--live`, swap testnet keys for production keys, seed `data/live.db` instead. Same recipe otherwise.

**Verification — `scripts/reconcile_full_oos.py`:**

```
uv run python scripts/reconcile_full_oos.py --db data/testnet.db
```

Field-by-field compare of closed trades in the DB against backtest CSVs across full OOS / March 2026 / April 2026 windows. Pass criterion: zero divergences except known data-extent artifacts (trades the backtest CSV marks `end_of_data` may close as `timeout` in live since live data extends past the CSV).

### `symbols` — Discover available symbols

- `uv run crypto-trade symbols` — list from both API and data.binance.vision
- `uv run crypto-trade symbols --source api` — active symbols only
- `uv run crypto-trade symbols --source vision` — all symbols including delisted

## Test

- `uv run pytest` — run all tests
- `uv run pytest tests/test_config.py` — run a single test file
- `uv run pytest -k test_name` — run a specific test

## Lint & Format

- `uv run ruff check .` — lint
- `uv run ruff check . --fix` — lint with auto-fix
- `uv run ruff format .` — format code

## Architecture

- **src layout**: all source code lives under `src/crypto_trade/`
- `config.py` — loads settings from environment variables
- `main.py` — entry point with argparse subcommands (`fetch`, `bulk`, `symbols`, `backtest`)
- `models.py` — frozen `Kline` dataclass (parses Binance API arrays and CSV rows, serializes to CSV)
- `client.py` — `BinanceClient` HTTP client with paginated kline fetching and rate limiting
- `storage.py` — CSV read/write utilities (`csv_path`, `read_last_open_time`, `write_klines`, `read_klines`)
- `fetcher.py` — orchestrates client + storage for incremental API fetching
- `discovery.py` — symbol discovery from exchange info API and data.binance.vision S3 bucket
- `bulk.py` — bulk download engine (monthly ZIP archives, retry, dedup, progress reporting)
- `indicators.py` — pure indicator functions (sma, ema, rsi, bollinger_bands, atr, stddev, true_range)
- `backtest.py` — backtest engine (runs strategies against historical kline data)
- `backtest_models.py` — Strategy Protocol, Signal, BacktestConfig, Order, TradeResult, DailyPnL
- `backtest_report.py` — BacktestSummary, `summarize()`, `aggregate_daily_pnl()`
- `strategies/` — trading strategy framework:
  - `__init__.py` — registry, kline helpers (closes/highs/lows/opens/volumes), `get_strategy()`, `list_strategies()`
  - `filters/range_spike_filter.py` — notebook-derived volatility trigger (range_spike >= threshold)
  - `filters/volume_filter.py` — volume spike confirmation wrapper
  - `price_action/momentum.py` — trend continuation (N candles same direction)
  - `price_action/mean_reversion.py` — extreme candle reversal (body > K * avg body)
  - `price_action/wick_rejection.py` — wick > K * body -> trade rejection direction
  - `price_action/inside_bar.py` — inside bar breakout
  - `price_action/gap_fill.py` — gap/imbalance fill
  - `price_action/consecutive_reversal.py` — N+ same-direction candles -> reversal
  - `indicator/rsi_bb.py` — RSI + Bollinger Bands mean reversion
  - `indicator/bb_squeeze.py` — Bollinger Band squeeze breakout
- `tests/` — pytest tests (mirrors source modules)
- `data/` — created at runtime, .gitignored; CSV files stored as `data/<SYMBOL>/<interval>.csv`
- `notebooks/` — Jupyter analysis notebooks:
  - `threshold_analysis.ipynb` — single 50/50 split threshold evaluation (7 metrics, 3 criteria)
  - `threshold_cv.ipynb` — time-series CV threshold evaluation (25 metrics = 6 bases × 4 windows + price_move, 5 criteria incl. forward fluctuation at 50% weight)

## Notebook Findings

Core approach: **detect high-volatility moments using `range_spike`** (candle range normalized by rolling mean), then trade them.

- **Best filter**: `range_spike_16` (4h rolling window on 15m candles), threshold ~5.85
- Triggered candles have **6.7x larger absolute returns** than average (2.28% vs 0.34%)
- Forward fluctuation of 0.043 (avg 4.3% movement over next 2h after trigger)
- ~600 signals/month across 118 symbols on 15m candles
- `range_spike = (high - low) / open / rolling_mean(range_ratio, window=16)`

Strategies decide **direction and timing** when a volatile moment occurs. The `range_spike` threshold acts as a composable filter wrapping any strategy.

## Conventions

- Python 3.13+, type hints encouraged
- Ruff for linting and formatting (line-length=100)
- Frozen dataclasses for configuration/value objects
- Prices stored as strings to preserve Binance's exact decimal precision
- Environment variables for secrets (never commit `.env`)
- httpx for HTTP requests (no full Binance SDK)
- stdlib csv for file I/O (no pandas dependency)

## Configuration

Settings loaded from env vars (see `.env.example`):

| Field | Env Var | Default |
|-------|---------|---------|
| `binance_api_key` | `BINANCE_API_KEY` | `""` |
| `binance_api_secret` | `BINANCE_API_SECRET` | `""` |
| `base_url` | `BINANCE_BASE_URL` | `https://fapi.binance.com` |
| `data_dir` | `DATA_DIR` | `data` |
| `symbols` | `SYMBOLS` | `BTCUSDT,ETHUSDT` |
| `intervals` | `INTERVALS` | `1h` |
| `kline_limit` | `KLINE_LIMIT` | `1500` |
| `rate_limit_pause` | `RATE_LIMIT_PAUSE` | `0.25` |
| `data_vision_base` | `DATA_VISION_BASE` | `https://data.binance.vision` |
| `bulk_rate_pause` | `BULK_RATE_PAUSE` | `0.1` |
