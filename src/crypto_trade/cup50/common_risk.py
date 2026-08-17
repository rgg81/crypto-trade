"""Causal common risk unit owned by the immutable CUP-50 namespace."""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd


def common_risk_scalars(
    gross_returns: pd.Series,
    decision_times: Sequence[pd.Timestamp],
    *,
    target_annualized_volatility: float = 0.10,
    lookback_days: int = 90,
    interval_hours: int = 8,
    minimum_scale: float = 0.20,
    maximum_scale: float = 3.0,
) -> pd.Series:
    """Return gross-volatility scalars using rows strictly before each decision."""
    if not math.isfinite(target_annualized_volatility) or target_annualized_volatility <= 0:
        raise ValueError("target_annualized_volatility must be a positive finite number")
    if not 0 < minimum_scale <= maximum_scale:
        raise ValueError("scale band must satisfy 0 < minimum_scale <= maximum_scale")
    bars_per_year = 365 * 24 / interval_hours
    required = max(2, math.ceil(lookback_days * 24 / interval_hours))

    history = gross_returns.sort_index()
    times = pd.DatetimeIndex(history.index)
    if times.tz is None:
        raise ValueError("gross_returns index must be timezone-aware UTC")
    values = history.to_numpy(dtype=float)

    scalars: list[float] = []
    index: list[pd.Timestamp] = []
    for raw_time in decision_times:
        decision = pd.Timestamp(raw_time)
        if decision.tzinfo is None:
            raise ValueError("decision_times must be timezone-aware UTC")
        stop = int(times.searchsorted(decision, side="left"))
        index.append(decision)
        if stop < required:
            scalars.append(1.0)
            continue
        window = values[stop - required : stop]
        if not np.isfinite(window).all():
            raise ValueError("gross returns contain non-finite values")
        realized = float(np.std(window, ddof=1)) * math.sqrt(bars_per_year)
        if realized <= 0.0:
            scalars.append(maximum_scale)
            continue
        scalars.append(
            min(maximum_scale, max(minimum_scale, target_annualized_volatility / realized))
        )
    return pd.Series(scalars, index=pd.DatetimeIndex(index), dtype=float)
