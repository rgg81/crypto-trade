"""Post-tournament Team 06 family: low-churn own-coin time-series momentum."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    interval_hours: int = 8
    decision_hour_utc: int = 0
    fast_horizon_bars: int = 21
    medium_horizon_bars: int = 42
    slow_horizon_bars: int = 84
    volatility_return_bars: int = 63
    volatility_floor: float = 0.0005
    minimum_valid_symbols: int = 12
    minimum_active_symbols: int = 6
    target_gross: float = 0.48
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.20
    annualized_risk_target: float = 0.30
    minimum_risk_scale: float = 0.20
    rebalance_days: int = 1
    hold_mixed_signal: bool = False
    entry_strength: float = 0.0

    def __post_init__(self) -> None:
        if self.rebalance_days not in {1, 3, 7}:
            raise ValueError("rebalance_days must be one of the preregistered cadences")
        if self.entry_strength not in {0.0, 0.25}:
            raise ValueError("entry_strength is outside the preregistered matrix")


_SCHEDULE_EPOCH = pd.Timestamp("1970-01-05T00:00:00Z")


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    if not (
        decision_time.hour == parameters.decision_hour_utc
        and decision_time.minute == 0
        and decision_time.second == 0
        and decision_time.microsecond == 0
    ):
        return False
    elapsed_days = int((decision_time.normalize() - _SCHEDULE_EPOCH).days)
    return elapsed_days % parameters.rebalance_days == 0


def _log_close_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series:
    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_closes = max(
        parameters.slow_horizon_bars + 1,
        parameters.volatility_return_bars + 1,
    )
    end = decision_time - interval
    start = end - (required_closes - 1) * interval
    raw_times = frame["open_time"]
    if isinstance(raw_times.dtype, pd.DatetimeTZDtype):
        left = int(raw_times.searchsorted(start, side="left"))
        right = int(raw_times.searchsorted(end, side="right"))
        candidate = frame.iloc[left:right]
        times = pd.to_datetime(candidate["open_time"], utc=True, errors="coerce")
    else:
        all_times = pd.to_datetime(raw_times, utc=True, errors="coerce")
        in_window = all_times.notna() & all_times.between(start, end, inclusive="both")
        candidate = frame.loc[in_window]
        times = all_times.loc[in_window]
    if candidate.empty:
        return pd.Series(dtype=float)
    data = candidate.loc[:, ["open_time", "close"]].copy()
    data["open_time"] = times
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    finite = np.isfinite(data["close"].to_numpy(dtype=float)) & (data["close"] > 0.0)
    data = (
        data.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    expected = pd.date_range(end=end, periods=required_closes, freq=interval)
    if len(data) < required_closes:
        return pd.Series(dtype=float)
    closes = data.set_index("open_time")["close"].reindex(expected)
    values = closes.to_numpy(dtype=float)
    if len(values) != required_closes or not np.isfinite(values).all():
        return pd.Series(dtype=float)
    return pd.Series(np.log(values), index=expected, dtype=float)


def _own_coin_signal(
    log_closes: pd.Series,
    *,
    previous_direction: int | None,
    parameters: StrategyParameters,
) -> tuple[int, float, pd.Series] | None:
    values = log_closes.to_numpy(dtype=float)
    horizons = (
        parameters.fast_horizon_bars,
        parameters.medium_horizon_bars,
        parameters.slow_horizon_bars,
    )
    horizon_returns = tuple(
        float(values[-1] - values[-(horizon + 1)]) for horizon in horizons
    )
    if not all(math.isfinite(value) for value in horizon_returns):
        return None
    signs = tuple(1 if value > 0.0 else -1 if value < 0.0 else 0 for value in horizon_returns)
    unanimous = signs[0] if signs[0] != 0 and len(set(signs)) == 1 else None

    returns = pd.Series(np.diff(values), index=log_closes.index[1:], dtype=float)
    volatility = float(returns.iloc[-parameters.volatility_return_bars :].std(ddof=1))
    if not math.isfinite(volatility):
        return None
    volatility = max(volatility, parameters.volatility_floor)

    direction: int | None = None
    if unanimous is not None:
        if parameters.entry_strength <= 0.0:
            direction = unanimous
        else:
            strength = min(
                abs(value) / (volatility * math.sqrt(horizon))
                for value, horizon in zip(horizon_returns, horizons, strict=True)
            )
            if math.isfinite(strength) and strength >= parameters.entry_strength:
                direction = unanimous
    if (
        direction is None
        and parameters.hold_mixed_signal
        and previous_direction in {-1, 1}
        and signs[-1] == previous_direction
        and sum(sign == previous_direction for sign in signs) >= 2
    ):
        direction = previous_direction
    if direction is None:
        return None
    return direction, volatility, returns


def _inverse_volatility_weights(
    signals: dict[str, tuple[int, float, pd.Series]],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    raw = {
        symbol: direction / volatility
        for symbol, (direction, volatility, _returns) in signals.items()
    }
    denominator = math.fsum(abs(value) for value in raw.values())
    if denominator <= 0.0:
        return {}
    scale = parameters.target_gross / denominator
    weights = {
        symbol: math.copysign(
            min(abs(value) * scale, parameters.maximum_symbol_weight), value
        )
        for symbol, value in raw.items()
    }
    long_gross = math.fsum(value for value in weights.values() if value > 0.0)
    short_gross = math.fsum(-value for value in weights.values() if value < 0.0)
    if long_gross - short_gross > parameters.maximum_abs_net:
        allowed_long = short_gross + parameters.maximum_abs_net
        long_scale = allowed_long / long_gross if long_gross > 0.0 else 0.0
        weights = {
            symbol: value * long_scale if value > 0.0 else value
            for symbol, value in weights.items()
        }
    elif short_gross - long_gross > parameters.maximum_abs_net:
        allowed_short = long_gross + parameters.maximum_abs_net
        short_scale = allowed_short / short_gross if short_gross > 0.0 else 0.0
        weights = {
            symbol: value * short_scale if value < 0.0 else value
            for symbol, value in weights.items()
        }
    return weights


def _downward_risk_scale(
    weights: dict[str, float],
    signals: dict[str, tuple[int, float, pd.Series]],
    *,
    parameters: StrategyParameters,
) -> float:
    if not weights:
        return 0.0
    return_frame = pd.DataFrame(
        {
            symbol: signals[symbol][2].iloc[-parameters.volatility_return_bars :]
            for symbol in sorted(weights)
        },
        dtype=float,
    ).dropna()
    if len(return_frame) < parameters.volatility_return_bars:
        return 0.0
    factor_returns = return_frame.mul(pd.Series(weights, dtype=float), axis=1).sum(axis=1)
    annualized = float(
        factor_returns.std(ddof=1)
        * math.sqrt((24.0 / parameters.interval_hours) * 365.0)
    )
    if not math.isfinite(annualized):
        return 0.0
    if annualized <= 1e-12 or annualized <= parameters.annualized_risk_target:
        return 1.0
    return max(
        parameters.minimum_risk_scale,
        min(1.0, parameters.annualized_risk_target / annualized),
    )


def _portfolio(
    signals: dict[str, tuple[int, float, pd.Series]],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if len(signals) < parameters.minimum_active_symbols:
        return {}
    weights = _inverse_volatility_weights(signals, parameters=parameters)
    risk_scale = _downward_risk_scale(weights, signals, parameters=parameters)
    if risk_scale <= 0.0:
        return {}
    result = {
        symbol: value * risk_scale
        for symbol, value in weights.items()
        if abs(value * risk_scale) > 1e-15
    }
    if not result:
        return {}
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > parameters.target_gross + 1e-12 or gross > 0.5 + 1e-12:
        return {}
    if abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    if max(abs(value) for value in result.values()) > parameters.maximum_symbol_weight + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class OwnCoinMomentumResearch:
    def __init__(self, parameters: StrategyParameters):
        self.parameters = parameters
        self._previous_directions: dict[str, int] = {}

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
            self._previous_directions = {}
            return {}

        signals: dict[str, tuple[int, float, pd.Series]] = {}
        for symbol in sorted(histories):
            signal = _own_coin_signal(
                histories[symbol],
                previous_direction=self._previous_directions.get(symbol),
                parameters=self.parameters,
            )
            if signal is not None:
                signals[symbol] = signal
        targets = _portfolio(signals, parameters=self.parameters)
        self._previous_directions = {
            symbol: signals[symbol][0] for symbol in targets if symbol in signals
        }
        return targets


def strategy(parameters: StrategyParameters) -> TargetStrategy:
    return OwnCoinMomentumResearch(parameters)
