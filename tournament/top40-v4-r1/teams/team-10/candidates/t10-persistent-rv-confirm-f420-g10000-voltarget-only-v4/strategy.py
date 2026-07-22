"""Volatility-only convergence-confirmed relative value for Team 10."""

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
    decision_hour_utc: int = 0
    formation_bars: int = 420
    correlation_return_bars: int = 126
    neighbors_per_symbol: int = 2
    minimum_correlation: float = 0.72
    minimum_prior_correlation: float = 0.50
    minimum_valid_symbols: int = 20
    beta_minimum: float = 0.30
    beta_maximum: float = 3.00
    ar1_minimum: float = 0.20
    ar1_maximum: float = 0.977
    minimum_half_life_bars: float = 2.0
    maximum_half_life_bars: float = 30.0
    minimum_zero_crossings: int = 8
    spread_scale_bars: int = 84
    entry_z: float = 1.75
    maximum_sizing_z: float = 4.0
    unconfirmed_scale: float = 0.25
    minimum_active_per_side: int = 3
    total_gross: float = 1.00
    maximum_symbol_weight: float = 1.0 / 12.0
    maximum_abs_net: float = 1.0 / 12.0


PARAMETERS = StrategyParameters()


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        decision_time.weekday() == parameters.decision_weekday_utc
        and decision_time.hour == parameters.decision_hour_utc
        and decision_time.minute == 0
        and decision_time.second == 0
        and decision_time.microsecond == 0
    )


def _log_close_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series:
    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    expected = pd.date_range(
        end=decision_time - interval,
        periods=parameters.formation_bars,
        freq=interval,
    )
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    data = frame.loc[complete, ["open_time", "close"]].copy()
    data["open_time"] = times.loc[complete]
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    finite = np.isfinite(data["close"].to_numpy(dtype=float)) & data["close"].gt(0.0)
    close = (
        data.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .set_index("open_time")["close"]
        .reindex(expected)
    )
    if len(close) != parameters.formation_bars or close.isna().any():
        return pd.Series(dtype=float)
    values = close.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        return pd.Series(dtype=float)
    return pd.Series(np.log(values), index=expected, dtype=float)


def _candidate_graph(
    histories: dict[str, pd.Series],
    *,
    parameters: StrategyParameters,
) -> tuple[tuple[str, str], ...]:
    symbols = sorted(histories)
    correlations: dict[tuple[str, str], tuple[float, float]] = {}
    window = parameters.correlation_return_bars
    for left_index, left in enumerate(symbols):
        left_returns = np.diff(histories[left].to_numpy(dtype=float))
        left_recent = left_returns[-window:]
        left_prior = left_returns[-2 * window : -window]
        if (
            len(left_recent) != window
            or len(left_prior) != window
            or float(np.std(left_recent)) <= 1e-12
            or float(np.std(left_prior)) <= 1e-12
        ):
            continue
        for right in symbols[left_index + 1 :]:
            right_returns = np.diff(histories[right].to_numpy(dtype=float))
            right_recent = right_returns[-window:]
            right_prior = right_returns[-2 * window : -window]
            if (
                len(right_recent) != window
                or len(right_prior) != window
                or float(np.std(right_recent)) <= 1e-12
                or float(np.std(right_prior)) <= 1e-12
            ):
                continue
            recent_correlation = float(np.corrcoef(left_recent, right_recent)[0, 1])
            prior_correlation = float(np.corrcoef(left_prior, right_prior)[0, 1])
            if math.isfinite(recent_correlation) and math.isfinite(prior_correlation):
                correlations[(left, right)] = (recent_correlation, prior_correlation)

    pairs: set[tuple[str, str]] = set()
    for symbol in symbols:
        neighbors: list[tuple[float, float, str]] = []
        for other in symbols:
            if other == symbol:
                continue
            pair = tuple(sorted((symbol, other)))
            pair_correlations = correlations.get(pair)
            if pair_correlations is None:
                continue
            recent_correlation, prior_correlation = pair_correlations
            if (
                recent_correlation >= parameters.minimum_correlation
                and prior_correlation >= parameters.minimum_prior_correlation
            ):
                neighbors.append(
                    (min(recent_correlation, prior_correlation), recent_correlation, other)
                )
        neighbors.sort(key=lambda item: (-item[0], -item[1], item[2]))
        for _weak_correlation, _recent_correlation, other in neighbors[
            : parameters.neighbors_per_symbol
        ]:
            pairs.add(tuple(sorted((symbol, other))))
    return tuple(sorted(pairs))


def _linear_fit(y: np.ndarray, x: np.ndarray) -> tuple[float, float] | None:
    x_centered = x - float(np.mean(x))
    denominator = float(np.dot(x_centered, x_centered))
    if not math.isfinite(denominator) or denominator <= 1e-12:
        return None
    beta = float(np.dot(x_centered, y - float(np.mean(y))) / denominator)
    intercept = float(np.mean(y) - beta * np.mean(x))
    if not math.isfinite(beta) or not math.isfinite(intercept):
        return None
    return intercept, beta


def _pair_signal(
    left_log: pd.Series,
    right_log: pd.Series,
    *,
    parameters: StrategyParameters,
) -> tuple[float, float] | None:
    left = left_log.to_numpy(dtype=float)
    right = right_log.to_numpy(dtype=float)
    if len(left) != parameters.formation_bars or len(right) != parameters.formation_bars:
        return None
    fitted = _linear_fit(left[:-1], right[:-1])
    if fitted is None:
        return None
    intercept, beta = fitted
    if beta < parameters.beta_minimum or beta > parameters.beta_maximum:
        return None
    residuals = left[:-1] - (intercept + beta * right[:-1])
    if len(residuals) <= parameters.spread_scale_bars + 2:
        return None

    lagged = residuals[:-1]
    leading = residuals[1:]
    ar_fit = _linear_fit(leading, lagged)
    if ar_fit is None:
        return None
    _ar_intercept, rho = ar_fit
    if rho <= parameters.ar1_minimum or rho >= parameters.ar1_maximum:
        return None
    half_life = -math.log(2.0) / math.log(rho)
    if (
        not math.isfinite(half_life)
        or half_life < parameters.minimum_half_life_bars
        or half_life > parameters.maximum_half_life_bars
    ):
        return None
    centered = residuals - float(np.mean(residuals))
    crossings = int(np.count_nonzero(centered[:-1] * centered[1:] <= 0.0))
    if crossings < parameters.minimum_zero_crossings:
        return None

    scale_window = residuals[-parameters.spread_scale_bars :]
    center = float(np.median(scale_window))
    mad = float(np.median(np.abs(scale_window - center)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 1e-8:
        scale = float(np.std(scale_window, ddof=1))
    if not math.isfinite(scale) or scale <= 1e-8:
        return None
    current = float(left[-1] - (intercept + beta * right[-1]))
    z_score = (current - center) / scale
    if not math.isfinite(z_score) or abs(z_score) < parameters.entry_z:
        return None
    previous = float(left[-2] - (intercept + beta * right[-2]))
    current_deviation = current - center
    previous_deviation = previous - center
    confirmed = bool(
        math.isfinite(previous_deviation)
        and current_deviation * previous_deviation > 0.0
        and abs(current_deviation) < abs(previous_deviation)
    )
    capped = min(abs(z_score), parameters.maximum_sizing_z)
    conviction = min(capped - parameters.entry_z, 1.5)
    if not confirmed:
        conviction *= parameters.unconfirmed_scale
    return -math.copysign(conviction, z_score), beta


def _aggregate_signals(
    histories: dict[str, pd.Series],
    pairs: tuple[tuple[str, str], ...],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    aggregate = {symbol: 0.0 for symbol in histories}
    for left, right in pairs:
        signal = _pair_signal(histories[left], histories[right], parameters=parameters)
        if signal is None:
            continue
        left_conviction, beta = signal
        normalizer = 1.0 + beta
        aggregate[left] += left_conviction / normalizer
        aggregate[right] -= beta * left_conviction / normalizer
    return {
        symbol: value
        for symbol, value in aggregate.items()
        if math.isfinite(value) and abs(value) > 1e-12
    }


def _portfolio(
    aggregate: dict[str, float],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    longs = [symbol for symbol, value in aggregate.items() if value > 0.0]
    shorts = [symbol for symbol, value in aggregate.items() if value < 0.0]
    if (
        len(longs) < parameters.minimum_active_per_side
        or len(shorts) < parameters.minimum_active_per_side
    ):
        return {}
    raw_gross = math.fsum(abs(value) for value in aggregate.values())
    raw_net = math.fsum(aggregate.values())
    maximum_raw_weight = max(abs(value) for value in aggregate.values())
    if raw_gross <= 1e-12 or maximum_raw_weight <= 1e-12:
        return {}
    scale_limits = [
        parameters.total_gross / raw_gross,
        parameters.maximum_symbol_weight / maximum_raw_weight,
    ]
    if abs(raw_net) > 1e-12:
        scale_limits.append(parameters.maximum_abs_net / abs(raw_net))
    scale = min(scale_limits)
    if not math.isfinite(scale) or scale <= 0.0:
        return {}
    result = {
        symbol: value * scale for symbol, value in aggregate.items() if abs(value * scale) > 1e-12
    }
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > parameters.total_gross + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    if max(abs(value) for value in result.values()) > parameters.maximum_symbol_weight + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class DynamicRelativeValue:
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
        if not _is_scheduled(decision_time, self.parameters):
            return None
        histories: dict[str, pd.Series] = {}
        for symbol in sorted({str(value) for value in context.eligible_symbols}):
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            history = _log_close_history(
                frame,
                decision_time=decision_time,
                parameters=self.parameters,
            )
            if not history.empty:
                histories[symbol] = history
        if len(histories) < self.parameters.minimum_valid_symbols:
            return {}
        pairs = _candidate_graph(histories, parameters=self.parameters)
        if not pairs:
            return {}
        aggregate = _aggregate_signals(histories, pairs, parameters=self.parameters)
        return _portfolio(aggregate, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return DynamicRelativeValue()
