# Data Engineering — Project Guide

You are working on data engineering code for the **crypto-trade** project. Follow these conventions and patterns.

## Setup

Install the adaptive dependency group (pandas + optuna):

```
uv sync --group adaptive
```

## Conventions for DE Code

- **pandas** for all tabular data manipulation (matches the notebook style)
- **optuna** for any hyperparameter / threshold optimization
- **float** over Decimal — DE code uses float64; only the core backtest engine uses Decimal
- **Lazy imports** — `import pandas as pd` inside functions, not at module top level, so the module always loads even without the `adaptive` group installed
- Small, standalone functions with docstrings — each function does one thing
- Type hints on all function signatures
- Frozen dataclasses for result / config objects

## Reference: Adaptive Range Spike Filter

The canonical example of DE-style code in this project is:

**`src/crypto_trade/strategies/filters/adaptive_range_spike_filter.py`**

It demonstrates the standard pipeline pattern:

| Function | Purpose |
|---|---|
| `history_to_dataframe(history)` | Kline list → pandas DataFrame (bridge between backtest engine and pandas) |
| `compute_range_spike(df, window)` | DataFrame → Series of spike values (notebook formula) |
| `count_signals_per_month(spikes, threshold, cpm)` | Series + threshold → monthly signal rate |
| `find_best_threshold(spikes, target, ...)` | Series + target → optimal threshold via optuna |

Each function is independently testable. Reuse these when extending the filter or building new ones.

## Key Reusable Functions

```python
from crypto_trade.strategies.filters.adaptive_range_spike_filter import (
    history_to_dataframe,    # list[Kline] → pd.DataFrame
    compute_range_spike,     # pd.DataFrame → pd.Series
    count_signals_per_month, # pd.Series, float, float → float
    find_best_threshold,     # pd.Series, float, ... → float (optuna)
)
```

## Strategy Protocol

All strategies (including filters) implement:

```python
class Strategy(Protocol):
    def on_kline(self, symbol: str, kline: Kline, history: list[Kline]) -> Signal: ...
```

Filters wrap an inner strategy: `Filter(inner=some_strategy)`. The `on_kline` hot path should use plain float math (no pandas) for performance.

## Testing Patterns

Tests live in `tests/test_*.py`. For pandas/optuna code:

- Use `_kline()` helper to create test Kline objects
- Use `_generate_history(n, base_range, spike_indices, spike_range)` for synthetic data
- Use `AlwaysBuy` stub as inner strategy
- Test each standalone function in its own class (`TestHistoryToDataframe`, etc.)
- For optuna: use `max_trials=20` in tests for speed; assert results within a reasonable range rather than exact values
- For pandas: verify dtypes, column names, edge cases (empty, NaN)

## File Locations

| File | Purpose |
|---|---|
| `src/crypto_trade/strategies/filters/` | Filter strategies (range spike, volume, adaptive) |
| `src/crypto_trade/strategies/` | Strategy registry and helpers |
| `src/crypto_trade/backtest_models.py` | Strategy Protocol, Signal, BacktestConfig |
| `src/crypto_trade/models.py` | Kline dataclass |
| `src/crypto_trade/indicators.py` | Pure indicator functions (sma, ema, rsi, etc.) |
| `tests/` | All tests |

## Dependency Management

- Core app: `httpx` only (no pandas)
- DE / adaptive features: `uv sync --group adaptive` (pandas + optuna)
- Notebooks: `uv sync --group notebook` (pandas + numpy + scipy + matplotlib + ...)
- Always use lazy imports in strategy/filter modules so registration works without optional deps
