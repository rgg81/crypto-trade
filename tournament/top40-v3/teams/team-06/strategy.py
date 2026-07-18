"""Team 06: pure own-coin multi-horizon time-series momentum baseline."""

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
    # Team 06 is the tournament's deliberately directional trend sleeve.  It uses the
    # organizer's conservative 0.20 sub-limit rather than forcing a market-neutral 0.05 book;
    # the other nine mechanisms remain relative-value or tightly neutral strategies.
    maximum_abs_net: float = 0.20
    annualized_risk_target: float = 0.30
    minimum_risk_scale: float = 0.20


_REFERENCE = StrategyParameters()


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        decision_time.hour == parameters.decision_hour_utc
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
    required_closes = max(
        parameters.slow_horizon_bars + 1,
        parameters.volatility_return_bars + 1,
    )
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_closes,
        freq=interval,
    )
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
    parameters: StrategyParameters,
) -> tuple[int, float, pd.Series] | None:
    values = log_closes.to_numpy(dtype=float)
    horizons = (
        parameters.fast_horizon_bars,
        parameters.medium_horizon_bars,
        parameters.slow_horizon_bars,
    )
    horizon_returns = [float(values[-1] - values[-(horizon + 1)]) for horizon in horizons]
    if not all(math.isfinite(value) for value in horizon_returns):
        return None
    if all(value > 0.0 for value in horizon_returns):
        direction = 1
    elif all(value < 0.0 for value in horizon_returns):
        direction = -1
    else:
        return None

    returns = pd.Series(
        np.diff(values),
        index=log_closes.index[1:],
        dtype=float,
    )
    volatility = float(
        returns.iloc[-parameters.volatility_return_bars :].std(ddof=1)
    )
    if not math.isfinite(volatility):
        return None
    return direction, max(volatility, parameters.volatility_floor), returns


def _inverse_volatility_weights(
    signals: dict[str, tuple[int, float, pd.Series]],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    raw = {
        symbol: direction / volatility
        for symbol, (direction, volatility, _) in signals.items()
    }
    denominator = math.fsum(abs(value) for value in raw.values())
    if denominator <= 0.0:
        return {}
    scale = parameters.target_gross / denominator
    weights = {
        symbol: math.copysign(
            min(abs(value) * scale, parameters.maximum_symbol_weight),
            value,
        )
        for symbol, value in raw.items()
    }

    # Preserve every own-coin direction while proportionally shrinking only the larger sleeve
    # until the portfolio satisfies the directional-net cap.
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
    factor_returns = return_frame.mul(
        pd.Series(weights, dtype=float),
        axis=1,
    ).sum(axis=1)
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


class OwnCoinMomentumConsensus:
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

        signals: dict[str, tuple[int, float, pd.Series]] = {}
        for symbol in sorted(histories):
            signal = _own_coin_signal(histories[symbol], parameters=self.parameters)
            if signal is not None:
                signals[symbol] = signal
        return _portfolio(signals, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return OwnCoinMomentumConsensus()
