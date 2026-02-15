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

# Fetch kline (candlestick) data from Binance Futures
uv run crypto-trade fetch

# Fetch specific symbols and intervals from a start date
uv run crypto-trade fetch --symbols BTCUSDT,SOLUSDT --intervals 1h,15m --start 2024-01-01

# Re-run to incrementally update (only appends new klines)
uv run crypto-trade fetch
```

Kline data is saved as CSV files under `data/<SYMBOL>/<interval>.csv`.

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
| `RATE_LIMIT_PAUSE` | Seconds between paginated requests | `0.25` |

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```
