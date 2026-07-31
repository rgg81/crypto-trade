"""Causal dispersion/breadth recoupling baseline for Team 05."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd
from crypto_trade.tournament import protocol


BAR_HOURS = 8
FORMATION_BARS = 63
STATE_REFERENCE_BARS = 126
STATE_MINIMUM_OBSERVATIONS = 63
MINIMUM_ASSETS = 8
PRIOR_GAP_THRESHOLD = 0.75
MINIMUM_GAP_CONTRACTION = 0.20
CONTRIBUTION_POWER = 2.0
REBALANCE_HOURS = 48
SIDE_GROSS_BUDGET = 0.32
SYMBOL_CAP = 0.08


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _completed_close(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.Series:
    if frame is None or frame.empty or "open_time" not in frame or "close" not in frame:
        return pd.Series(dtype=float)

    raw_times = frame["open_time"]
    if pd.api.types.is_numeric_dtype(raw_times):
        numeric_times = pd.to_numeric(raw_times, errors="coerce")
        finite_times = numeric_times[np.isfinite(numeric_times)]
        unit = "ms" if not finite_times.empty and float(finite_times.abs().median()) > 1.0e11 else "s"
        open_times = pd.to_datetime(numeric_times, unit=unit, utc=True, errors="coerce")
    else:
        open_times = pd.to_datetime(raw_times, utc=True, errors="coerce")

    closes = pd.to_numeric(frame["close"], errors="coerce")
    completed = (
        open_times.notna()
        & closes.notna()
        & np.isfinite(closes)
        & (closes > 0.0)
        & (open_times + pd.Timedelta(hours=BAR_HOURS) <= decision_time)
    )
    if not bool(completed.any()):
        return pd.Series(dtype=float)

    result = pd.Series(
        closes.loc[completed].to_numpy(dtype=float, copy=True),
        index=pd.DatetimeIndex(open_times.loc[completed]),
        dtype=float,
    )
    result = result[~result.index.duplicated(keep="last")]
    return result.sort_index()


def _past_only_zscore(series: pd.Series) -> pd.Series:
    past = series.shift(1).rolling(
        STATE_REFERENCE_BARS,
        min_periods=STATE_MINIMUM_OBSERVATIONS,
    )
    mean = past.mean()
    standard_deviation = past.std(ddof=0)
    valid_scale = standard_deviation.where(standard_deviation > 1.0e-12)
    return (series - mean) / valid_scale


def _capped_proportional(raw: pd.Series, budget: float) -> dict[str, float]:
    positive = raw[(raw > 0.0) & np.isfinite(raw)].astype(float)
    if positive.empty or budget <= 0.0:
        return {}

    remaining = set(str(symbol) for symbol in positive.index)
    values = {str(symbol): float(value) for symbol, value in positive.items()}
    allocation: dict[str, float] = {}
    remaining_budget = min(float(budget), SYMBOL_CAP * len(remaining))

    while remaining and remaining_budget > 1.0e-15:
        denominator = sum(values[symbol] for symbol in remaining)
        if denominator <= 0.0:
            break
        provisional = {
            symbol: remaining_budget * values[symbol] / denominator for symbol in remaining
        }
        capped = [symbol for symbol, weight in provisional.items() if weight >= SYMBOL_CAP]
        if not capped:
            allocation.update(provisional)
            remaining_budget = 0.0
            break
        for symbol in sorted(capped):
            allocation[symbol] = SYMBOL_CAP
            remaining.remove(symbol)
            remaining_budget -= SYMBOL_CAP

    return allocation


class DispersionBreadthRecoupling:
    def target_weights(
        self,
        context: protocol.StrategyContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        del seed
        decision_time = _utc_timestamp(context.decision_time)

        epoch_hours = int(decision_time.timestamp() // 3600)
        if epoch_hours % REBALANCE_HOURS != 0:
            return None

        eligible = tuple(sorted(set(context.eligible_symbols)))
        close_series: dict[str, pd.Series] = {}
        for symbol in eligible:
            series = _completed_close(context.bars.get(symbol), decision_time)
            if len(series) > FORMATION_BARS + STATE_MINIMUM_OBSERVATIONS:
                close_series[symbol] = series

        if len(close_series) < MINIMUM_ASSETS:
            return {}

        closes = pd.concat(close_series, axis=1, join="outer").sort_index()
        formation_returns = np.log(closes / closes.shift(FORMATION_BARS))
        formation_returns = formation_returns.replace([np.inf, -np.inf], np.nan)

        available = formation_returns.notna().sum(axis=1)
        cross_sectional_mean = formation_returns.mean(axis=1)
        deviations = formation_returns.sub(cross_sectional_mean, axis=0)
        dispersion = np.sqrt(deviations.pow(2).sum(axis=1) / available.where(available > 0))
        signed_breadth = np.sign(formation_returns).sum(axis=1) / available.where(available > 0)
        absolute_breadth = signed_breadth.abs()

        dispersion = dispersion.where(available >= MINIMUM_ASSETS)
        absolute_breadth = absolute_breadth.where(available >= MINIMUM_ASSETS)
        gap = _past_only_zscore(dispersion) - _past_only_zscore(absolute_breadth)
        valid_gap = gap.dropna()
        if len(valid_gap) < 2:
            return {}

        previous_time = valid_gap.index[-2]
        current_time = valid_gap.index[-1]
        previous_gap = float(valid_gap.iloc[-2])
        current_gap = float(valid_gap.iloc[-1])
        contracting = previous_gap - current_gap >= MINIMUM_GAP_CONTRACTION
        if previous_gap < PRIOR_GAP_THRESHOLD or current_gap <= 0.0 or not contracting:
            return {}

        current_returns = formation_returns.loc[current_time].dropna()
        if len(current_returns) < MINIMUM_ASSETS:
            return {}
        current_deviation = current_returns - float(current_returns.mean())
        relative_contribution = current_deviation.abs().pow(CONTRIBUTION_POWER)
        below_center = relative_contribution[current_deviation < 0.0]
        above_center = relative_contribution[current_deviation > 0.0]
        if below_center.empty or above_center.empty:
            return {}

        common_budget = min(
            SIDE_GROSS_BUDGET,
            SYMBOL_CAP * len(below_center),
            SYMBOL_CAP * len(above_center),
        )
        long_allocations = _capped_proportional(below_center, common_budget)
        short_allocations = _capped_proportional(above_center, common_budget)

        weights: dict[str, float] = {}
        for symbol, weight in long_allocations.items():
            weights[symbol] = float(weight)
        for symbol, weight in short_allocations.items():
            weights[symbol] = -float(weight)

        if not weights or not all(np.isfinite(weight) for weight in weights.values()):
            return {}
        gross = sum(abs(weight) for weight in weights.values())
        net = sum(weights.values())
        if gross > 0.8 + 1.0e-12 or abs(net) > 0.20 + 1.0e-12:
            return {}
        if any(abs(weight) > SYMBOL_CAP + 1.0e-12 for weight in weights.values()):
            return {}
        return dict(sorted(weights.items()))


def build_strategy() -> DispersionBreadthRecoupling:
    return DispersionBreadthRecoupling()
