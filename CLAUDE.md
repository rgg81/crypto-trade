# crypto-trade

## Build & Run

- `uv sync` — install all dependencies
- `uv run crypto-trade` — run the application (shows status + help)
- `uv run python -m crypto_trade.main` — alternative way to run

## Fetch Kline Data

- `uv run crypto-trade fetch` — fetch all configured symbols/intervals
- `uv run crypto-trade fetch --symbols BTCUSDT,SOLUSDT` — specific symbols
- `uv run crypto-trade fetch --intervals 1h,15m` — specific intervals
- `uv run crypto-trade fetch --start 2024-01-01` — from a specific date
- Re-running `fetch` is incremental — only appends new klines

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
- `main.py` — entry point with argparse subcommands (`fetch`)
- `models.py` — frozen `Kline` dataclass (parses Binance API arrays, serializes to CSV rows)
- `client.py` — `BinanceClient` HTTP client with paginated kline fetching and rate limiting
- `storage.py` — CSV read/write utilities (`csv_path`, `read_last_open_time`, `write_klines`, `read_klines`)
- `fetcher.py` — orchestrates client + storage for incremental fetching
- `tests/` — pytest tests (mirrors source modules: `test_models.py`, `test_client.py`, `test_storage.py`, `test_fetcher.py`, `test_config.py`)
- `data/` — created at runtime, .gitignored; CSV files stored as `data/<SYMBOL>/<interval>.csv`

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
