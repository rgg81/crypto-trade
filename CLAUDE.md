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

### `seed-live-db` + `live` — Initialize live engine from backtest CSVs

**These two commands MUST be run together (in this order) when starting a live engine that needs to reproduce backtest results.** Running `live` without first seeding produces a cold engine with empty R1/R2/VT/cooldown state — it will diverge from the backtest until catch-up has rebuilt enough history (~1-3 months).

**Step 1 — seed the DB from backtest trade CSVs:**

```
uv run crypto-trade seed-live-db \
  --v1-trades reports/iteration_186/in_sample/trades.csv \
  --v1-trades reports/iteration_186/out_of_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/in_sample/trades.csv \
  --v2-trades reports-v2/iteration_v2-069/out_of_sample/trades.csv \
  --as-of 2026-01-27 \
  --track both \
  --db data/dry_run.db
```

What it does:
- Inserts pre-cutoff backtest trades as `status='closed'` so `_rebuild_risk_state` / `_rebuild_vt_history` reproduce backtest R2/VT exactly.
- Trades that span `--as-of` (open before, close after) are inserted as `status='open'` with `entry_order_id='SEEDED'` and full intended-exit info; the engine closes them deterministically during catch-up at the seeded `exit_time`.
- Skips trades that opened after `--as-of` — the engine catch-up replay produces them.
- Drops zero-`weight_factor` rows (BTC-killed v2 trades).
- Sets per-(model, symbol) `cooldown_<model>_<symbol>` engine_state keys.
- Use `--db data/dry_run.db` for dry-run; `--db data/live.db` for real-money.

**Step 2 — launch the engine with matching `--catch-up-from`:**

```
uv run crypto-trade live --track both --catch-up-from 2026-01-27
```

**The `--catch-up-from` date MUST equal the seeder's `--as-of`.** Otherwise catch-up either re-creates trades the seeder already inserted (duplicates) or skips trades the seeder didn't seed (gap).

Choosing the date:
- Recent (e.g. 1-3 months back): fast catch-up (~30-60 min for 90 days) but R2 cum/peak may not have its all-time peak in state if peak was set earlier.
- OOS cutoff (`2025-03-24`): full backtest reproduction, near-empty catch-up, engine boots into poll loop in seconds, perfect R2 parity.
- Add `--live` to enable real trading (default is dry-run).

**Verification — `scripts/reconcile_full_oos.py`:**

```
uv run python scripts/reconcile_full_oos.py --db data/dry_run.db
```

Compares closed trades in the DB against backtest CSVs across full OOS / March 2026 / April 2026 windows, field-by-field on TRADE_COLS. Pass criterion: zero divergences except known data-extent artifacts (trades the backtest CSV marks `end_of_data` may close as `timeout` in live since live data extends past the CSV).

### Testnet workflow — `live --testnet`

Run the engine against the Binance Futures testnet (https://testnet.binancefuture.com) for an end-to-end smoke test of the auth integration before pointing at production. Testnet has its own API keys, balances, and matching engine; klines stay on production so `--catch-up-from` and feature regen see the full historical OHLCV the backtest used.

**Generate testnet keys:**

1. Visit https://testnet.binancefuture.com and sign in (separate from binance.com).
2. Create an API key + secret on the testnet console.
3. Export them in the shell that will run the engine:

```
export BINANCE_API_KEY=<testnet-key>
export BINANCE_API_SECRET=<testnet-secret>
```

**Optional — point at a non-default testnet host:**

```
export BINANCE_AUTH_BASE_URL=https://staging.binancefuture.com
```

When unset, `--testnet` defaults to `https://testnet.binancefuture.com`.

**Run:**

```
uv run crypto-trade live --testnet --track both --catch-up-from 2026-01-27
```

What happens:
- Banner reads `[live] Starting baseline v186 [LIVE — TESTNET]`.
- Signed calls (`place_market_order`, `place_stop_market_order`, `place_take_profit_market_order`, `get_order`, `set_leverage`, `get_positions`, `cancel_order`) hit testnet.
- Kline fetches stay on `https://fapi.binance.com` so catch-up replay sees full historical data.
- DB lives at `data/testnet.db`; trade log at `data/testnet_trades.csv`. Neither overlaps with `data/live.db` / `data/dry_run.db` or their CSVs.
- `--testnet` forces live trading. Combining `--testnet` with empty credentials errors and exits — no silent dry-run fallback.
- If `BINANCE_AUTH_BASE_URL` is set to anything other than `settings.base_url`, the engine prints `[live] AUTH endpoint OVERRIDE: <url>` so an `.env`-set staging URL can never quietly route prod orders to staging.

**Resuming after Ctrl-C:** the testnet DB persists. Re-running `live --testnet --catch-up-from <same-date>` resumes from where the engine left off — open trades reconciled against testnet, paper rows skipped via `is_paper_trade` guards.

**Cleanup:** `rm data/testnet.db data/testnet_trades.csv` between unrelated smoke tests for a fresh state.

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
