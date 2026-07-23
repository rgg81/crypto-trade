"""Role-specific three-slot Monday seasonality held over one full calendar week."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    interval_hours: int = 8
    decision_weekday_utc: int = 0
    decision_hour_utc: int = 8
    adjacent_hours_utc: tuple[int, int] = (0, 16)
    long_lookback_weeks: int = 78
    long_minimum_weeks: int = 39
    short_lookback_weeks: int = 104
    short_minimum_weeks: int = 52
    center_cell_weight: float = 0.50
    adjacent_cell_weight: float = 0.50
    winsor_mad_multiplier: float = 4.0
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.20
    total_gross: float = 0.58
    maximum_symbol_weight: float = 0.04
    maximum_abs_net: float = 0.02


@dataclasses.dataclass(frozen=True)
class SeasonalFeature:
    expected_return: float
    standardized_expected_return: float


PARAMETERS = StrategyParameters()
_FIELDS = ("open_time", "open")


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _scheduled(timestamp: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        timestamp.weekday() == parameters.decision_weekday_utc
        and timestamp.hour == parameters.decision_hour_utc
        and timestamp.minute == 0
        and timestamp.second == 0
        and timestamp.microsecond == 0
    )


def _winsorized(values: np.ndarray, multiplier: float) -> np.ndarray:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(values, ddof=1))
    if not math.isfinite(scale) or scale <= 1e-12:
        return values.copy()
    return np.clip(values, median - multiplier * scale, median + multiplier * scale)


def _weekly_returns(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    hour_utc: int,
    lookback_weeks: int,
    minimum_weeks: int,
    parameters: StrategyParameters,
) -> pd.Series:
    if not set(_FIELDS).issubset(frame.columns):
        return pd.Series(dtype=float)
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    data = frame.loc[times.notna() & (times < decision_time), list(_FIELDS)].copy()
    data["open_time"] = times.loc[data.index]
    data["open"] = pd.to_numeric(data["open"], errors="coerce")
    finite = np.isfinite(data["open"].to_numpy(dtype=float)) & data["open"].gt(0.0)
    data = (
        data.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    calendar = pd.DatetimeIndex(data["open_time"])
    data = data.loc[
        (calendar.weekday == parameters.decision_weekday_utc)
        & (calendar.hour == hour_utc)
    ].tail(lookback_weeks + 1)
    if len(data) < minimum_weeks + 1:
        return pd.Series(dtype=float)
    selected_times = pd.DatetimeIndex(data["open_time"])
    gaps = selected_times[1:] - selected_times[:-1]
    values = data["open"].to_numpy(dtype=float)
    returns = np.diff(np.log(values))
    valid = gaps == pd.Timedelta(days=7)
    result = pd.Series(returns[valid], index=selected_times[1:][valid], dtype=float)
    return result.tail(lookback_weeks)


def _cell_residuals(
    context: DecisionContext,
    *,
    hour_utc: int,
    lookback_weeks: int,
    minimum_weeks: int,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    histories: dict[str, pd.Series] = {}
    decision_time = _utc(context.decision_time)
    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _weekly_returns(
            frame,
            decision_time=decision_time,
            hour_utc=hour_utc,
            lookback_weeks=lookback_weeks,
            minimum_weeks=minimum_weeks,
            parameters=parameters,
        )
        if len(history) >= minimum_weeks:
            histories[symbol] = history
    if len(histories) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    returns = pd.DataFrame(histories, dtype=float).tail(lookback_weeks)
    returns = returns.dropna(axis=1, thresh=minimum_weeks)
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    returns = returns.dropna(axis=0, how="all")
    return returns.sub(returns.median(axis=1, skipna=True), axis=0)


def _cell_statistics(
    residuals: pd.DataFrame,
    *,
    lookback_weeks: int,
    minimum_weeks: int,
    parameters: StrategyParameters,
) -> dict[str, tuple[float, float]]:
    result: dict[str, tuple[float, float]] = {}
    for symbol in sorted(residuals.columns):
        raw = residuals[symbol].dropna().to_numpy(dtype=float)
        if len(raw) < minimum_weeks:
            continue
        values = _winsorized(raw[-lookback_weeks:], parameters.winsor_mad_multiplier)
        mean = float(np.mean(values))
        scale = float(np.std(values, ddof=1))
        if math.isfinite(mean) and math.isfinite(scale) and scale > 1e-12:
            result[symbol] = (mean, scale)
    return result


def _seasonal_features(
    context: DecisionContext,
    *,
    lookback_weeks: int,
    minimum_weeks: int,
    parameters: StrategyParameters,
) -> dict[str, SeasonalFeature]:
    hours = (parameters.decision_hour_utc, *parameters.adjacent_hours_utc)
    statistics: dict[int, dict[str, tuple[float, float]]] = {}
    for hour in hours:
        residuals = _cell_residuals(
            context,
            hour_utc=hour,
            lookback_weeks=lookback_weeks,
            minimum_weeks=minimum_weeks,
            parameters=parameters,
        )
        if residuals.empty:
            return {}
        statistics[hour] = _cell_statistics(
            residuals,
            lookback_weeks=lookback_weeks,
            minimum_weeks=minimum_weeks,
            parameters=parameters,
        )
    symbols = set.intersection(*(set(values) for values in statistics.values()))
    if len(symbols) < parameters.minimum_valid_symbols:
        return {}
    result: dict[str, SeasonalFeature] = {}
    for symbol in sorted(symbols):
        center_mean, center_scale = statistics[parameters.decision_hour_utc][symbol]
        adjacent_mean = math.fsum(
            statistics[hour][symbol][0] for hour in parameters.adjacent_hours_utc
        ) / len(parameters.adjacent_hours_utc)
        expected = (
            parameters.center_cell_weight * center_mean
            + parameters.adjacent_cell_weight * adjacent_mean
        )
        standardized = expected / center_scale
        if math.isfinite(expected) and math.isfinite(standardized):
            result[symbol] = SeasonalFeature(expected, standardized)
    return result


def _portfolio(
    long_features: dict[str, SeasonalFeature],
    short_features: dict[str, SeasonalFeature],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    long_ordered = sorted(
        long_features,
        key=lambda symbol: (long_features[symbol].standardized_expected_return, symbol),
    )
    short_ordered = sorted(
        short_features,
        key=lambda symbol: (short_features[symbol].standardized_expected_return, symbol),
    )
    long_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(long_ordered))),
    )
    short_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(short_ordered))),
    )
    long_count = min(long_count, len(long_ordered) // 2)
    short_count = min(short_count, len(short_ordered) // 2)
    shorts = short_ordered[:short_count]
    longs = [symbol for symbol in reversed(long_ordered) if symbol not in shorts][:long_count]
    if (
        len(longs) < parameters.minimum_positions_per_side
        or len(shorts) < parameters.minimum_positions_per_side
    ):
        return {}
    side_gross = parameters.total_gross / 2.0
    long_weight = side_gross / len(longs)
    short_weight = side_gross / len(shorts)
    if max(long_weight, short_weight) > parameters.maximum_symbol_weight + 1e-12:
        return {}
    target = {symbol: long_weight for symbol in longs}
    target.update({symbol: -short_weight for symbol in shorts})
    gross = math.fsum(abs(weight) for weight in target.values())
    net = math.fsum(target.values())
    if gross > parameters.total_gross + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: target[symbol] for symbol in sorted(target)}


class MondayDualHorizonSeasonality:
    def __init__(self, parameters: StrategyParameters = PARAMETERS):
        self.parameters = parameters

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> dict[str, float] | None:
        del seed
        decision_time = _utc(context.decision_time)
        if not _scheduled(decision_time, self.parameters):
            return None
        long_features = _seasonal_features(
            context,
            lookback_weeks=self.parameters.long_lookback_weeks,
            minimum_weeks=self.parameters.long_minimum_weeks,
            parameters=self.parameters,
        )
        short_features = _seasonal_features(
            context,
            lookback_weeks=self.parameters.short_lookback_weeks,
            minimum_weeks=self.parameters.short_minimum_weeks,
            parameters=self.parameters,
        )
        if not long_features or not short_features:
            return {}
        return _portfolio(long_features, short_features, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return MondayDualHorizonSeasonality()
