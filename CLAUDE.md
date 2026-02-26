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

- `uv run crypto-trade bulk --symbols BTCUSDT,ETHUSDT --intervals 1m,5m` — specific symbols
- `uv run crypto-trade bulk --all --intervals 1m,5m` — all symbols (including delisted)
- `uv run crypto-trade bulk --symbols BTCUSDT --intervals 1m --api-backfill` — bulk + fill current month via API
- Downloads monthly ZIP archives — much faster than API for historical data
- Incremental: re-running skips already-downloaded months

### `backtest` — Run strategy backtests

- `uv run crypto-trade backtest --list` — list all available strategies
- `uv run crypto-trade backtest --strategy momentum --symbols BTCUSDT --interval 5m` — basic run
- `uv run crypto-trade backtest --strategy rsi_bb --symbols BTCUSDT --interval 5m --range-spike-filter` — with notebook volatility filter
- `uv run crypto-trade backtest --strategy mean_reversion --symbols BTCUSDT,ETHUSDT --interval 5m --start 2024-01-01 --end 2024-12-31` — date range
- `uv run crypto-trade backtest --strategy momentum --symbols BTCUSDT --interval 5m --stop-loss 2.0 --take-profit 3.0 --timeout 120 --fee 0.1` — custom SL/TP/timeout/fee
- `uv run crypto-trade backtest --strategy mean_reversion --symbols BTCUSDT --interval 5m --params lookback=30,multiplier=3.0` — custom strategy params
- `--range-spike-filter` and `--volume-filter` can be combined with any strategy
- Strategies: `momentum`, `mean_reversion`, `wick_rejection`, `inside_bar`, `gap_fill`, `consecutive_reversal`, `rsi_bb`, `bb_squeeze`

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

- **Best filter**: `range_spike_48` (4h rolling window on 5m candles), threshold ~5.85
- Triggered candles have **6.7x larger absolute returns** than average (2.28% vs 0.34%)
- Forward fluctuation of 0.043 (avg 4.3% movement over next 2h after trigger)
- ~600 signals/month across 118 symbols on 5m candles
- `range_spike = (high - low) / open / rolling_mean(range_ratio, window=48)`

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
