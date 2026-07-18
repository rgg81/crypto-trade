"""Team 04: compensated downside risk net of positive-jump lottery risk."""

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
    lookback_bars: int = 126
    winsor_mad_multiplier: float = 5.0
    positive_jump_mad_threshold: float = 1.50
    maximum_abs_beta: float = 2.5
    minimum_market_variance: float = 1e-12
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_positive_volume_fraction: float = 0.90
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.30
    downside_rank_weight: float = 1.0
    lottery_rank_weight: float = 0.75
    total_gross: float = 0.36
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05


@dataclasses.dataclass(frozen=True)
class RiskDecompositionFeature:
    downside_semivariance: float
    positive_jump_variance: float
    total_residual_variance: float
    market_beta: float


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
    required_bars = parameters.lookback_bars + 1
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


def _return_matrix(
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
        log_prices = np.log(history["close"].to_numpy(dtype=float))
        values = np.diff(log_prices)
        index = pd.DatetimeIndex(history["open_time"].iloc[1:])
        if len(values) == parameters.lookback_bars and np.isfinite(values).all():
            histories[symbol] = pd.Series(values, index=index, dtype=float)
    if len(histories) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    returns = pd.DataFrame(histories, dtype=float).sort_index().dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    return returns


def _robust_clip(values: np.ndarray, multiplier: float) -> tuple[np.ndarray, float]:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(values))
    if not math.isfinite(scale) or scale <= 1e-12:
        return values.copy(), 0.0
    return np.clip(values, median - multiplier * scale, median + multiplier * scale), scale


def _risk_decomposition_components(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, RiskDecompositionFeature]:
    returns = _return_matrix(context, parameters=parameters)
    if returns.empty:
        return {}
    market = returns.median(axis=1, skipna=False).to_numpy(dtype=float)
    centered_market = market - float(np.mean(market))
    market_sum_squares = float(np.dot(centered_market, centered_market))
    market_variance = market_sum_squares / len(centered_market)
    if not math.isfinite(market_variance) or market_variance <= parameters.minimum_market_variance:
        return {}

    result: dict[str, RiskDecompositionFeature] = {}
    for symbol in sorted(returns.columns):
        asset = returns[symbol].to_numpy(dtype=float)
        centered_asset = asset - float(np.mean(asset))
        beta = float(np.dot(centered_asset, centered_market) / market_sum_squares)
        beta = float(np.clip(beta, -parameters.maximum_abs_beta, parameters.maximum_abs_beta))
        residual = asset - beta * market
        residual = residual - float(np.median(residual))
        clipped, scale = _robust_clip(residual, parameters.winsor_mad_multiplier)
        downside_semivariance = float(np.mean(np.square(np.minimum(clipped, 0.0))))
        jump_threshold = max(0.0, parameters.positive_jump_mad_threshold * scale)
        positive_jump_variance = float(
            np.mean(np.where(clipped > jump_threshold, np.square(clipped), 0.0))
        )
        feature = RiskDecompositionFeature(
            downside_semivariance=downside_semivariance,
            positive_jump_variance=positive_jump_variance,
            total_residual_variance=float(np.mean(np.square(clipped))),
            market_beta=beta,
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


def _risk_decomposition_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    components = _risk_decomposition_components(context, parameters=parameters)
    if len(components) < parameters.minimum_valid_symbols:
        return {}
    downside_rank = _percentile_ranks(
        {symbol: value.downside_semivariance for symbol, value in components.items()}
    )
    lottery_rank = _percentile_ranks(
        {symbol: value.positive_jump_variance for symbol, value in components.items()}
    )
    return {
        symbol: (
            parameters.downside_rank_weight * downside_rank[symbol]
            - parameters.lottery_rank_weight * lottery_rank[symbol]
        )
        for symbol in sorted(components)
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
    if abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class DownsideNetLotteryRisk:
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
        scores = _risk_decomposition_scores(context, parameters=self.parameters)
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return DownsideNetLotteryRisk()
