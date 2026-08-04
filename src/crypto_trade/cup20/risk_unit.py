"""Causal common risk unit.

Every submission is scaled toward one ex-ante volatility target so that drawdown comparisons
measure tail behaviour and regime timing rather than who chose to trade smallest. The scalar is
derived from the *unscaled* book's gross returns, which removes any circularity between the scalar
and the costs it induces.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN


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
    """Gross-return volatility scalars, using only rows strictly before each decision."""
    if target_annualized_volatility <= 0:
        raise ValueError("target_annualized_volatility must be positive")
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
        # Strictly earlier rows only. Conservative under either return-stamping convention.
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


def apply_risk_scalars(targets: pd.DataFrame, scalars: pd.Series) -> pd.DataFrame:
    """Multiply every weight column by its boundary scalar, preserving the instruction column."""
    if not targets.index.equals(scalars.index):
        raise ValueError("risk scalars must be indexed by exactly the target decision times")
    scaled = targets.copy()
    weight_columns = [column for column in scaled.columns if column != REBALANCE_INSTRUCTION_COLUMN]
    scaled[weight_columns] = scaled[weight_columns].mul(scalars.astype(float), axis=0)
    return scaled
