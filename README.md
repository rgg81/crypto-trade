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
uv run crypto-trade
```

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run ruff format .
```
