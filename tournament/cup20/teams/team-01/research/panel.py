"""Team-01 shared research panel: the exact past-only view the runner streams, as arrays.

NOT a scorer. Nothing here computes an equity curve, a Sharpe, a drawdown, a cost or a fill.
It builds the (boundary x symbol) price/eligibility panel so that signal statistics -- information
coefficients, hit rates, sign persistence, weight-change rates -- can be measured on exactly the
rows the organiser's runner would have shown the strategy. Every performance number team-01 acts
on comes from ``scripts/cup20_evaluate.py``.

Timing convention, matched to ``crypto_trade.tournament.engine_v2``:

* at boundary ``t`` the strategy sees bars whose close time is ``<= t``; the newest such bar has
  ``open_time == t - 8h``, so its ``close`` is the freshest price available, call it ``P[t]``;
* a target decided at ``t`` fills at the open of the bar stamped ``t``, ``O[t]``, and earns the
  open-to-open return ``O[t+1] / O[t] - 1``.

So ``P`` is the signal panel (shifted one bar forward off ``close``) and ``O`` is the execution
panel, and neither ever reads a row the strategy could not have seen.
"""

from __future__ import annotations

import dataclasses

import numpy as np
import pandas as pd

from crypto_trade.cup20.config import IS_END, load_config
from crypto_trade.cup20.runner import decision_grid
from crypto_trade.cup20.snapshot import load_snapshot, resolve_is_start
from crypto_trade.tournament.data import eligible_at

CONFIG = load_config("tournament/cup20/config.toml").raw
BARS_PER_DAY = 3

FOLD_EDGES = ("2021-08-01", "2022-08-01", "2023-08-01")


@dataclasses.dataclass(frozen=True)
class Panel:
    grid: pd.DatetimeIndex
    symbols: list[str]
    signal_price: np.ndarray  # P[t, i]: newest close visible at boundary t
    exec_open: np.ndarray  # O[t, i]: open of the bar stamped t (the fill price)
    eligible: np.ndarray  # bool [t, i]

    def fold_of_boundary(self) -> np.ndarray:
        edges = [pd.Timestamp(e, tz="UTC") for e in FOLD_EDGES]
        out = np.zeros(len(self.grid), dtype=int)
        for edge in edges:
            out += (self.grid >= edge).astype(int)
        return out


def build_panel() -> Panel:
    snapshot = load_snapshot(CONFIG["data"]["is_root"])
    bars = snapshot.bars
    membership = snapshot.membership
    is_start = resolve_is_start(membership, target_size=int(CONFIG["universe"]["target_size"]))
    grid = pd.DatetimeIndex(decision_grid(is_start, IS_END, interval_hours=8))

    close = bars.pivot(index="open_time", columns="symbol", values="close").sort_index()
    opens = bars.pivot(index="open_time", columns="symbol", values="open").sort_index()
    symbols = sorted(close.columns)
    close = close[symbols]
    opens = opens[symbols]

    # P[t] is the close of the bar opening at t - 8h == the last bar closed by t.
    signal_price = close.shift(1).reindex(grid).to_numpy(dtype=float)
    exec_open = opens.reindex(grid).to_numpy(dtype=float)

    index_of = {s: i for i, s in enumerate(symbols)}
    has_open = ~np.isnan(exec_open)
    eligible = np.zeros_like(has_open, dtype=bool)
    for row, t in enumerate(grid):
        for symbol in eligible_at(membership, t):
            column = index_of.get(symbol)
            if column is not None and has_open[row, column]:
                eligible[row, column] = True
    return Panel(
        grid=grid,
        symbols=symbols,
        signal_price=signal_price,
        exec_open=exec_open,
        eligible=eligible,
    )


def log_returns(price: np.ndarray) -> np.ndarray:
    """Per-bar log returns of a [t, i] price panel; first row is NaN."""
    with np.errstate(divide="ignore", invalid="ignore"):
        out = np.log(price[1:] / price[:-1])
    return np.vstack([np.full((1, price.shape[1]), np.nan), out])


def rolling_sum(values: np.ndarray, window: int) -> np.ndarray:
    """Trailing sum over ``window`` rows, NaN until the window is full (NaN-propagating)."""
    frame = pd.DataFrame(values)
    return frame.rolling(window, min_periods=window).sum().to_numpy(dtype=float)


def rolling_std(values: np.ndarray, window: int) -> np.ndarray:
    frame = pd.DataFrame(values)
    return frame.rolling(window, min_periods=window).std(ddof=1).to_numpy(dtype=float)


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 30:
        return float("nan")
    xr = pd.Series(x[mask]).rank().to_numpy()
    yr = pd.Series(y[mask]).rank().to_numpy()
    return float(np.corrcoef(xr, yr)[0, 1])


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    mask = np.isfinite(x) & np.isfinite(y)
    if mask.sum() < 30:
        return float("nan")
    return float(np.corrcoef(x[mask], y[mask])[0, 1])
