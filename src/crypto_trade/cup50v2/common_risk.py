"""The common risk unit: one organizer-owned scale, applied identically to every lane.

Teams own the *shape* of a book and the organizer owns its *size*.  Without that split, drawdown
comparisons across lanes measure who chose to trade smallest rather than who timed regimes well.

CUP-50 scaled by the realised volatility of the book's own past gross returns over ninety days.
That is a measure of a position the strategy no longer holds: its winner sat flat for half of every
window and then concentrated into a handful of names, so the realised series it was scaled by
described neither state, and the book ran at 23% annualised against a 10% target.  Here the scalar
prices the book that is about to be held, from an exponentially weighted covariance of the names in
it, using only bars that closed before the decision.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

if TYPE_CHECKING:  # pragma: no cover - import cycle guard, replay imports this module
    from crypto_trade.cup50v2.replay import ExecutionConfig

BARS_PER_YEAR = 365 * 24 / 8


def _close_panel(bars: pd.DataFrame) -> pd.DataFrame:
    required = {"open_time", "close_time", "symbol", "close"}
    missing = required - set(bars)
    if missing:
        raise ValueError(f"risk unit bars are missing columns: {sorted(missing)}")
    frame = bars.loc[:, ["open_time", "close_time", "symbol", "close"]].copy()
    for column in ("open_time", "close_time"):
        times = pd.DatetimeIndex(pd.to_datetime(frame[column], utc=True))
        if times.tz is None:
            raise ValueError("risk unit bars must carry timezone-aware UTC times")
        frame[column] = times
    panel = frame.pivot_table(
        index="open_time", columns="symbol", values="close", aggfunc="last"
    ).sort_index()
    closes = frame.groupby("open_time", sort=True)["close_time"].max()
    return panel, closes


def _ewma_covariance(window: np.ndarray, halflife: float) -> np.ndarray:
    """Exponentially weighted covariance about the exponentially weighted mean."""
    length = window.shape[0]
    ages = np.arange(length - 1, -1, -1, dtype=float)
    weights = 0.5 ** (ages / halflife)
    total = float(weights.sum())
    mean = (weights[:, None] * window).sum(axis=0) / total
    centred = window - mean
    return (centred * weights[:, None]).T @ centred / total


def exante_risk_scalars(
    targets: pd.DataFrame,
    *,
    bars: pd.DataFrame,
    config: ExecutionConfig,
) -> pd.Series:
    """Return one scale per decision, sizing the intended book to the common volatility target.

    The scalar multiplies the raw targets before the evaluator's caps, so a book the unit wants to
    grow can still only reach the declared gross, symbol and participation ceilings.
    """
    from crypto_trade.cup50v2.replay import REBALANCE_COLUMN

    decisions = pd.DatetimeIndex(targets.index)
    if decisions.tz is None:
        raise ValueError("target decisions must be timezone-aware UTC")
    if config.risk_minimum_scale > config.risk_maximum_scale:
        raise ValueError("risk scalar band is inverted")

    symbols = [column for column in targets.columns if column != REBALANCE_COLUMN]
    explicit = (
        targets[REBALANCE_COLUMN].astype(bool)
        if REBALANCE_COLUMN in targets
        else pd.Series(True, index=decisions)
    )
    panel, close_times = _close_panel(bars)
    returns = panel.pct_change()
    open_times = pd.DatetimeIndex(panel.index)
    # A return row is usable only when the bar it closes on has already closed; the panel is keyed
    # by open time, so the row's own close time is what decides.
    usable_close = pd.DatetimeIndex(close_times.reindex(open_times).to_numpy())

    window_bars = int(config.risk_window_bars)
    halflife = float(config.risk_halflife_bars)
    minimum_bars = int(config.risk_minimum_symbol_bars)

    scalars: list[float] = []
    for position, decision in enumerate(decisions):
        weights = targets.iloc[position]
        held = {
            str(symbol): float(weights[symbol])
            for symbol in symbols
            if symbol in panel.columns and float(weights.get(symbol, 0.0)) != 0.0
        }
        if not bool(explicit.iloc[position]) or not held:
            scalars.append(1.0)
            continue
        stop = int(usable_close.searchsorted(decision, side="left"))
        window = returns.iloc[max(0, stop - window_bars) : stop]
        names = sorted(held)
        vector = np.array([held[name] for name in names], dtype=float)
        block = window.reindex(columns=names)
        counts = block.notna().sum(axis=0).to_numpy()
        qualified = counts >= minimum_bars
        if not qualified.any():
            scalars.append(1.0)
            continue
        covariance = np.zeros((len(names), len(names)), dtype=float)
        observed = block.loc[:, qualified].to_numpy(dtype=float)
        observed = np.nan_to_num(observed, nan=0.0, posinf=0.0, neginf=0.0)
        estimated = _ewma_covariance(observed, halflife)
        index = np.flatnonzero(qualified)
        covariance[np.ix_(index, index)] = estimated
        if not qualified.all():
            # A name too new to estimate is priced at the median variance of the book's other
            # names with no covariance credit, rather than being treated as riskless.
            fallback = float(np.median(np.diag(estimated)))
            for missing in np.flatnonzero(~qualified):
                covariance[missing, missing] = fallback
        variance = float(vector @ covariance @ vector)
        annualized = math.sqrt(max(variance, 0.0) * BARS_PER_YEAR)
        if not math.isfinite(annualized) or annualized <= 0.0:
            scalars.append(config.risk_maximum_scale)
            continue
        scalars.append(
            min(
                config.risk_maximum_scale,
                max(config.risk_minimum_scale, config.risk_target / annualized),
            )
        )
    return pd.Series(scalars, index=decisions, dtype=float)
