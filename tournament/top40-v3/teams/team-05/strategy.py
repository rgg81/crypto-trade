"""Team 05: weekly causal dynamic-cointegration convergence baseline."""

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
    formation_bars: int = 252
    correlation_return_bars: int = 126
    neighbors_per_symbol: int = 2
    minimum_correlation: float = 0.65
    minimum_valid_symbols: int = 8
    beta_minimum: float = 0.25
    beta_maximum: float = 4.0
    ar1_minimum: float = 0.10
    ar1_maximum: float = 0.985
    minimum_half_life_bars: float = 1.0
    maximum_half_life_bars: float = 42.0
    minimum_zero_crossings: int = 6
    spread_scale_bars: int = 63
    entry_z: float = 1.50
    maximum_abs_z: float = 5.0
    minimum_active_per_side: int = 2
    target_side_gross: float = 0.20
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05


_REFERENCE = StrategyParameters()


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
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    interval = pd.Timedelta(hours=parameters.interval_hours)
    complete = times.notna() & ((times + interval) <= decision_time)
    if not bool(complete.any()):
        return pd.Series(dtype=float)
    data = frame.loc[complete, ["open_time", "close"]].copy()
    data["open_time"] = times.loc[complete]
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    finite = np.isfinite(data["close"].to_numpy(dtype=float)) & (data["close"] > 0.0)
    data = (
        data.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    expected = pd.date_range(
        end=decision_time - interval,
        periods=parameters.formation_bars,
        freq=interval,
    )
    if len(data) < parameters.formation_bars:
        return pd.Series(dtype=float)
    closes = data.set_index("open_time")["close"].reindex(expected)
    values = closes.to_numpy(dtype=float)
    if len(values) != parameters.formation_bars or not np.isfinite(values).all():
        return pd.Series(dtype=float)
    return pd.Series(np.log(values), index=expected, dtype=float)


def _candidate_graph(
    histories: dict[str, pd.Series],
    *,
    parameters: StrategyParameters,
) -> tuple[tuple[str, str], ...]:
    symbols = sorted(histories)
    correlations: dict[tuple[str, str], float] = {}
    required_closes = parameters.correlation_return_bars + 1
    for left_index, left in enumerate(symbols):
        left_values = histories[left].to_numpy(dtype=float)[-required_closes:]
        left_returns = np.diff(left_values)
        if float(np.std(left_returns)) <= 1e-12:
            continue
        for right in symbols[left_index + 1 :]:
            right_values = histories[right].to_numpy(dtype=float)[-required_closes:]
            right_returns = np.diff(right_values)
            if float(np.std(right_returns)) <= 1e-12:
                continue
            correlation = float(np.corrcoef(left_returns, right_returns)[0, 1])
            if math.isfinite(correlation):
                correlations[(left, right)] = correlation

    pairs: set[tuple[str, str]] = set()
    for symbol in symbols:
        candidates: list[tuple[float, str]] = []
        for other in symbols:
            if other == symbol:
                continue
            pair = tuple(sorted((symbol, other)))
            correlation = correlations.get(pair)
            if correlation is None or correlation < parameters.minimum_correlation:
                continue
            candidates.append((correlation, other))
        candidates.sort(key=lambda item: (-item[0], item[1]))
        for _, other in candidates[: parameters.neighbors_per_symbol]:
            pairs.add(tuple(sorted((symbol, other))))
    return tuple(sorted(pairs))


def _pair_convergence_signal(
    left_log: pd.Series,
    right_log: pd.Series,
    *,
    parameters: StrategyParameters,
) -> tuple[float, float] | None:
    """Return the signed left-leg conviction and its causal hedge ratio."""

    left = left_log.to_numpy(dtype=float)
    right = right_log.to_numpy(dtype=float)
    if len(left) != parameters.formation_bars or len(right) != parameters.formation_bars:
        return None

    # Fit without the latest close. The final residual is therefore a true one-step dislocation
    # relative to a hedge relationship estimated solely from preceding completed bars.
    y_train = left[:-1]
    x_train = right[:-1]
    x_centered = x_train - float(np.mean(x_train))
    denominator = float(np.dot(x_centered, x_centered))
    if not math.isfinite(denominator) or denominator <= 1e-12:
        return None
    beta = float(np.dot(x_centered, y_train - float(np.mean(y_train))) / denominator)
    if (
        not math.isfinite(beta)
        or beta < parameters.beta_minimum
        or beta > parameters.beta_maximum
    ):
        return None
    intercept = float(np.mean(y_train) - beta * np.mean(x_train))
    residuals = y_train - (intercept + beta * x_train)
    if len(residuals) <= parameters.spread_scale_bars + 2:
        return None

    lagged = residuals[:-1]
    leading = residuals[1:]
    lagged_centered = lagged - float(np.mean(lagged))
    ar_denominator = float(np.dot(lagged_centered, lagged_centered))
    if ar_denominator <= 1e-14:
        return None
    rho = float(
        np.dot(lagged_centered, leading - float(np.mean(leading))) / ar_denominator
    )
    if (
        not math.isfinite(rho)
        or rho <= parameters.ar1_minimum
        or rho >= parameters.ar1_maximum
    ):
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
    scale_mean = float(np.mean(scale_window))
    scale = float(np.std(scale_window, ddof=1))
    if not math.isfinite(scale) or scale <= 1e-8:
        return None
    current_residual = float(left[-1] - (intercept + beta * right[-1]))
    z_score = (current_residual - scale_mean) / scale
    if not math.isfinite(z_score) or abs(z_score) < parameters.entry_z:
        return None
    # A correctly beta-hedged spread can make a real dislocation look more extreme because
    # common-factor variance has been removed.  Treat maximum_abs_z as the preregistered
    # winsorization bound for sizing, not as an inverted admission rule that discards the
    # strongest convergence observations. Structural-break exits remain organizer-owned risk
    # controls; formation still requires causal stationarity, half-life and crossing evidence.
    sizing_z = min(abs(z_score), parameters.maximum_abs_z)
    magnitude = min(sizing_z - parameters.entry_z, 2.0)
    # Positive residual means the left coin is rich: short left and buy right.
    return -math.copysign(magnitude, z_score), beta


def _aggregate_pair_signals(
    histories: dict[str, pd.Series],
    pairs: tuple[tuple[str, str], ...],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    aggregate = {symbol: 0.0 for symbol in histories}
    for left, right in pairs:
        pair_signal = _pair_convergence_signal(
            histories[left],
            histories[right],
            parameters=parameters,
        )
        if pair_signal is None:
            continue
        left_conviction, beta = pair_signal
        # The fitted spread is left - beta * right.  Normalize each pair to unit
        # gross before aggregation so beta changes the hedge-leg dollars without
        # allowing a large beta alone to manufacture more portfolio conviction.
        pair_gross_normalizer = 1.0 + beta
        left_leg = left_conviction / pair_gross_normalizer
        right_leg = -beta * left_conviction / pair_gross_normalizer
        aggregate[left] += left_leg
        aggregate[right] += right_leg
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
    longs = sorted(symbol for symbol, value in aggregate.items() if value > 0.0)
    shorts = sorted(symbol for symbol, value in aggregate.items() if value < 0.0)
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

    # One conviction unit maps to one symbol cap.  Crucially, every constraint is
    # enforced with the same downscale: relative signal magnitude, overlap and the
    # fitted beta hedge survive portfolio construction instead of being replaced
    # by equal-weight long and short baskets.
    conviction_scale = parameters.maximum_symbol_weight
    scale_limits = [
        conviction_scale,
        (2.0 * parameters.target_side_gross) / raw_gross,
        parameters.maximum_symbol_weight / maximum_raw_weight,
    ]
    if abs(raw_net) > 1e-12:
        scale_limits.append(parameters.maximum_abs_net / abs(raw_net))
    scale = min(scale_limits)
    if not math.isfinite(scale) or scale <= 0.0:
        return {}
    result = {
        symbol: value * scale
        for symbol, value in aggregate.items()
        if abs(value * scale) > 1e-12
    }
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if (
        gross > (2.0 * parameters.target_side_gross) + 1e-12
        or gross > 0.5 + 1e-12
        or abs(net) > parameters.maximum_abs_net + 1e-12
    ):
        return {}
    if max(abs(value) for value in result.values()) > parameters.maximum_symbol_weight + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class DynamicCointegrationConvergence:
    def __init__(self, parameters: StrategyParameters = _REFERENCE):
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
        eligible = tuple(sorted({str(symbol) for symbol in context.eligible_symbols}))
        histories: dict[str, pd.Series] = {}
        for symbol in eligible:
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
        aggregate = _aggregate_pair_signals(histories, pairs, parameters=self.parameters)
        return _portfolio(aggregate, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return DynamicCointegrationConvergence()
