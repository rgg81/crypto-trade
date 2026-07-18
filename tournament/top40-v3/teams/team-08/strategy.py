"""Team 08: canonical market-neutral multi-horizon residual momentum baseline."""

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
    medium_horizon_bars: int = 63
    slow_horizon_bars: int = 126
    fast_weight: float = 0.40
    medium_weight: float = 0.35
    slow_weight: float = 0.25
    consensus_weight: float = 0.20
    volatility_floor: float = 1e-6
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_positive_volume_fraction: float = 0.90
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.30
    total_gross: float = 0.44
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05


@dataclasses.dataclass(frozen=True)
class MomentumFeature:
    fast_scaled_momentum: float
    medium_scaled_momentum: float
    slow_scaled_momentum: float
    sign_consensus: float


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


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    required = {"open_time", "close", "quote_volume"}
    if not required.issubset(frame.columns):
        return pd.DataFrame(columns=sorted(required))
    interval = pd.Timedelta(hours=parameters.interval_hours)
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    result = frame.loc[complete, ["open_time", "close", "quote_volume"]].copy()
    if result.empty:
        return pd.DataFrame(columns=sorted(required))
    result["open_time"] = times.loc[complete]
    result["close"] = pd.to_numeric(result["close"], errors="coerce")
    result["quote_volume"] = pd.to_numeric(result["quote_volume"], errors="coerce")
    finite = (
        np.isfinite(result["close"].to_numpy(dtype=float))
        & (result["close"] > 0.0)
        & np.isfinite(result["quote_volume"].to_numpy(dtype=float))
        & (result["quote_volume"] >= 0.0)
    )
    result = result.loc[finite]
    aligned = (
        result["open_time"].dt.minute.eq(0)
        & result["open_time"].dt.second.eq(0)
        & result["open_time"].dt.microsecond.eq(0)
        & result["open_time"].dt.hour.mod(parameters.interval_hours).eq(0)
    )
    result = (
        result.loc[aligned]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    required_bars = parameters.slow_horizon_bars + 1
    if len(result) < required_bars:
        return pd.DataFrame(columns=sorted(required))
    recent = result.tail(required_bars).reset_index(drop=True)
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_bars,
        freq=interval,
    )
    if not pd.DatetimeIndex(recent["open_time"]).equals(expected):
        return pd.DataFrame(columns=sorted(required))
    positive_volume = recent["quote_volume"] > 0.0
    if float(positive_volume.mean()) < parameters.minimum_positive_volume_fraction:
        return pd.DataFrame(columns=sorted(required))
    median_volume = float(recent.loc[positive_volume, "quote_volume"].median())
    if not math.isfinite(median_volume) or median_volume < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=sorted(required))
    return recent


def _residual_returns(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    decision_time = _utc(context.decision_time)
    histories: dict[str, pd.Series] = {}
    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _complete_history(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if history.empty:
            continue
        values = np.diff(np.log(history["close"].to_numpy(dtype=float)))
        index = pd.DatetimeIndex(history["open_time"].iloc[1:])
        if len(values) == parameters.slow_horizon_bars and np.isfinite(values).all():
            histories[symbol] = pd.Series(values, index=index, dtype=float)
    if len(histories) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    returns = pd.DataFrame(histories, dtype=float).sort_index().dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    market_return = returns.median(axis=1, skipna=False)
    return returns.sub(market_return, axis=0)


def _scaled_momentum(values: np.ndarray, horizon: int, volatility_floor: float) -> float:
    trailing = values[-horizon:]
    volatility = max(float(np.std(values, ddof=1)), volatility_floor)
    return float(np.sum(trailing) / (volatility * math.sqrt(horizon)))


def _momentum_features(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, MomentumFeature]:
    residuals = _residual_returns(context, parameters=parameters)
    if residuals.empty:
        return {}
    result: dict[str, MomentumFeature] = {}
    for symbol in sorted(residuals.columns):
        values = residuals[symbol].to_numpy(dtype=float)
        fast = _scaled_momentum(
            values,
            parameters.fast_horizon_bars,
            parameters.volatility_floor,
        )
        medium = _scaled_momentum(
            values,
            parameters.medium_horizon_bars,
            parameters.volatility_floor,
        )
        slow = _scaled_momentum(
            values,
            parameters.slow_horizon_bars,
            parameters.volatility_floor,
        )
        signs = tuple(1.0 if value > 0.0 else -1.0 if value < 0.0 else 0.0 for value in (fast, medium, slow))
        feature = MomentumFeature(
            fast_scaled_momentum=fast,
            medium_scaled_momentum=medium,
            slow_scaled_momentum=slow,
            sign_consensus=math.fsum(signs) / 3.0,
        )
        if all(math.isfinite(value) for value in dataclasses.astuple(feature)):
            result[symbol] = feature
    return result


def _percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    ordered_values = sorted(set(values.values()))
    if len(ordered_values) == 1:
        return {symbol: 0.5 for symbol in values}
    rank_by_value = {
        value: index / (len(ordered_values) - 1) for index, value in enumerate(ordered_values)
    }
    return {symbol: rank_by_value[value] for symbol, value in values.items()}


def _momentum_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    features = _momentum_features(context, parameters=parameters)
    if len(features) < parameters.minimum_valid_symbols:
        return {}
    fast_rank = _percentile_ranks(
        {symbol: value.fast_scaled_momentum for symbol, value in features.items()}
    )
    medium_rank = _percentile_ranks(
        {symbol: value.medium_scaled_momentum for symbol, value in features.items()}
    )
    slow_rank = _percentile_ranks(
        {symbol: value.slow_scaled_momentum for symbol, value in features.items()}
    )
    return {
        symbol: (
            parameters.fast_weight * (fast_rank[symbol] - 0.5)
            + parameters.medium_weight * (medium_rank[symbol] - 0.5)
            + parameters.slow_weight * (slow_rank[symbol] - 0.5)
            + parameters.consensus_weight * features[symbol].sign_consensus
        )
        for symbol in sorted(features)
    }


def _portfolio(
    scores: dict[str, float],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if len(scores) < parameters.minimum_valid_symbols:
        return {}
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    side_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(ordered))),
    )
    side_count = min(side_count, len(ordered) // 2)
    if side_count < parameters.minimum_positions_per_side:
        return {}
    shorts = ordered[:side_count]
    longs = ordered[-side_count:]
    weight = parameters.total_gross / (2.0 * side_count)
    if weight > parameters.maximum_symbol_weight + 1e-12:
        return {}
    result = {symbol: -weight for symbol in shorts}
    result.update({symbol: weight for symbol in longs})
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > min(parameters.total_gross, 0.5) + 1e-12:
        return {}
    if abs(net) > min(parameters.maximum_abs_net, 1e-12):
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class MultiHorizonResidualMomentum:
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
        scores = _momentum_scores(context, parameters=self.parameters)
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return MultiHorizonResidualMomentum()
