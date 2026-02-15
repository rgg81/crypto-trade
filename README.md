# crypto-trade

Binance Futures USD crypto trading bot.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

## Setup

```bash
# Clone the repo
git clone <repo-url> && cd crypto-trade

# Install dependencies (creates venv automatically)
uv sync

# Copy and fill in your API keys
cp .env.example .env
```

## Usage

```bash
# Show status and help
uv run crypto-trade
```

Kline data is saved as CSV files under `data/<SYMBOL>/<interval>.csv`.

### Fetch klines via API

Fetch kline (candlestick) data from the Binance Futures REST API. Supports incremental updates — re-running only appends new klines.

```bash
# Fetch configured symbols/intervals
uv run crypto-trade fetch

# Fetch specific symbols and intervals from a start date
uv run crypto-trade fetch --symbols BTCUSDT,SOLUSDT --intervals 1h,15m --start 2024-01-01

# Fetch all active perpetual symbols from exchange info
uv run crypto-trade fetch --all
```

### Bulk download from data.binance.vision

Download historical kline data in bulk from Binance's public data repository. Uses monthly ZIP archives — much faster than the REST API for large-scale downloads. Incremental: re-running skips already-downloaded months.

```bash
# Download specific symbols
uv run crypto-trade bulk --symbols BTCUSDT,ETHUSDT --intervals 1m,5m

# Download ALL symbols (including delisted) from data.binance.vision
uv run crypto-trade bulk --all --intervals 1m,5m

# Bulk download + backfill current incomplete month via API
uv run crypto-trade bulk --symbols BTCUSDT --intervals 1m --api-backfill
```

### Discover symbols

List all available Binance Futures perpetual symbols, including delisted ones from the public data archive.

```bash
# List from both API and data.binance.vision (default)
uv run crypto-trade symbols

# List only active symbols from the API
uv run crypto-trade symbols --source api

# List all symbols from data.binance.vision (includes delisted)
uv run crypto-trade symbols --source vision
```

## Configuration

Settings are loaded from environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `BINANCE_API_KEY` | Binance API key | `""` |
| `BINANCE_API_SECRET` | Binance API secret | `""` |
| `BINANCE_BASE_URL` | Futures API base URL | `https://fapi.binance.com` |
| `DATA_DIR` | Directory for CSV storage | `data` |
| `SYMBOLS` | Comma-separated trading pairs | `BTCUSDT,ETHUSDT` |
| `INTERVALS` | Comma-separated kline intervals | `1h` |
| `KLINE_LIMIT` | Max klines per API request | `1500` |
| `RATE_LIMIT_PAUSE` | Seconds between paginated API requests | `0.25` |
| `DATA_VISION_BASE` | Base URL for bulk data downloads | `https://data.binance.vision` |
| `BULK_RATE_PAUSE` | Seconds between bulk archive downloads | `0.1` |

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```
