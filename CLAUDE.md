# crypto-trade

## Build & Run

- `uv sync` — install all dependencies
- `uv run crypto-trade` — run the application
- `uv run python -m crypto_trade.main` — alternative way to run

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
- `main.py` — application entry point
- `tests/` — pytest tests

## Conventions

- Python 3.13+, type hints encouraged
- Ruff for linting and formatting (line-length=100)
- Frozen dataclasses for configuration/value objects
- Environment variables for secrets (never commit `.env`)
