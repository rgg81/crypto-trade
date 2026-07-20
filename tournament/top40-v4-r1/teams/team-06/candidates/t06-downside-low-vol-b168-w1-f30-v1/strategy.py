"""Team 06 long-lookback, broad-sleeve downside-risk neighborhood point."""

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
    lookback_bars: int = 168
    downside_weight: float = 0.45
    idiosyncratic_volatility_weight: float = 0.35
    drawdown_weight: float = 0.20
    maximum_abs_beta: float = 2.5
    minimum_market_variance: float = 1e-12
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.30
    total_gross: float = 0.36
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05


@dataclasses.dataclass(frozen=True)
class RiskFeature:
    downside_semivariance: float
    idiosyncratic_volatility: float
    residual_drawdown: float
    market_beta: float


_REFERENCE = StrategyParameters()
_FIELDS = ("open_time", "close", "quote_volume")


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


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    if not set(_FIELDS).issubset(frame.columns):
        return pd.DataFrame(columns=_FIELDS)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_bars = parameters.lookback_bars + 1
    end = decision_time - interval
    start = end - (required_bars - 1) * interval
    raw_times = frame["open_time"]
    if isinstance(raw_times.dtype, pd.DatetimeTZDtype):
        left = int(raw_times.searchsorted(start, side="left"))
        right = int(raw_times.searchsorted(end, side="right"))
        candidate = frame.iloc[left:right]
        times = pd.to_datetime(candidate["open_time"], utc=True, errors="coerce")
    else:
        all_times = pd.to_datetime(raw_times, utc=True, errors="coerce")
        mask = all_times.notna() & all_times.between(start, end, inclusive="both")
        candidate = frame.loc[mask]
        times = all_times.loc[mask]
    result = candidate.loc[:, list(_FIELDS)].copy()
    if result.empty:
        return pd.DataFrame(columns=_FIELDS)
    result["open_time"] = times
    result["close"] = pd.to_numeric(result["close"], errors="coerce")
    result["quote_volume"] = pd.to_numeric(result["quote_volume"], errors="coerce")
    finite = (
        np.isfinite(result["close"].to_numpy(dtype=float))
        & (result["close"] > 0.0)
        & np.isfinite(result["quote_volume"].to_numpy(dtype=float))
        & (result["quote_volume"] > 0.0)
    )
    result = (
        result.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    if len(result) < required_bars:
        return pd.DataFrame(columns=_FIELDS)
    recent = result.tail(required_bars).reset_index(drop=True)
    expected = pd.date_range(end=end, periods=required_bars, freq=interval)
    if not pd.DatetimeIndex(recent["open_time"]).equals(expected):
        return pd.DataFrame(columns=_FIELDS)
    if float(recent["quote_volume"].median()) < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=_FIELDS)
    return recent


def _features(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, RiskFeature]:
    decision_time = _utc(context.decision_time)
    series: dict[str, pd.Series] = {}
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
        if np.isfinite(values).all():
            series[symbol] = pd.Series(values, index=index, dtype=float)
    if len(series) < parameters.minimum_valid_symbols:
        return {}
    returns = pd.DataFrame(series).sort_index().dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return {}
    market = returns.median(axis=1, skipna=False).to_numpy(dtype=float)
    centered_market = market - float(np.mean(market))
    market_sum_squares = float(np.dot(centered_market, centered_market))
    market_variance = market_sum_squares / len(centered_market)
    if not math.isfinite(market_variance) or market_variance <= parameters.minimum_market_variance:
        return {}

    result: dict[str, RiskFeature] = {}
    for symbol in sorted(returns.columns):
        asset = returns[symbol].to_numpy(dtype=float)
        centered_asset = asset - float(np.mean(asset))
        beta = float(np.dot(centered_asset, centered_market) / market_sum_squares)
        beta = float(np.clip(beta, -parameters.maximum_abs_beta, parameters.maximum_abs_beta))
        residual = asset - beta * market
        residual -= float(np.median(residual))
        cumulative = np.cumsum(residual)
        drawdown = float(np.max(np.maximum.accumulate(cumulative) - cumulative))
        feature = RiskFeature(
            downside_semivariance=float(np.mean(np.square(np.minimum(residual, 0.0)))),
            idiosyncratic_volatility=float(np.std(residual, ddof=1)),
            residual_drawdown=drawdown,
            market_beta=beta,
        )
        if all(math.isfinite(value) for value in dataclasses.astuple(feature)):
            result[symbol] = feature
    return result


def _ranks(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(set(values.values()))
    if len(ordered) <= 1:
        return {symbol: 0.5 for symbol in values}
    by_value = {value: index / (len(ordered) - 1) for index, value in enumerate(ordered)}
    return {symbol: by_value[value] for symbol, value in values.items()}


def _scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    features = _features(context, parameters=parameters)
    if len(features) < parameters.minimum_valid_symbols:
        return {}
    downside = _ranks(
        {symbol: feature.downside_semivariance for symbol, feature in features.items()}
    )
    volatility = _ranks(
        {symbol: feature.idiosyncratic_volatility for symbol, feature in features.items()}
    )
    drawdown = _ranks({symbol: feature.residual_drawdown for symbol, feature in features.items()})
    raw = {
        symbol: -(
            parameters.downside_weight * downside[symbol]
            + parameters.idiosyncratic_volatility_weight * volatility[symbol]
            + parameters.drawdown_weight * drawdown[symbol]
        )
        for symbol in sorted(features)
    }

    symbols = sorted(raw)
    beta_values = np.array([features[symbol].market_beta for symbol in symbols], dtype=float)
    score_values = np.array([raw[symbol] for symbol in symbols], dtype=float)
    centered_beta = beta_values - float(np.mean(beta_values))
    centered_score = score_values - float(np.mean(score_values))
    denominator = float(np.dot(centered_beta, centered_beta))
    slope = (
        0.0 if denominator <= 1e-12 else float(np.dot(centered_score, centered_beta) / denominator)
    )
    return {
        symbol: float(raw[symbol] - slope * centered_beta[index])
        for index, symbol in enumerate(symbols)
    }


def _portfolio(
    scores: dict[str, float],
    *,
    parameters: StrategyParameters = _REFERENCE,
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
    weight = parameters.total_gross / (2.0 * side_count)
    if weight > parameters.maximum_symbol_weight + 1e-12:
        return {}
    shorts = ordered[:side_count]
    longs = ordered[-side_count:]
    result = {symbol: -weight for symbol in shorts}
    result.update({symbol: weight for symbol in longs})
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > parameters.total_gross + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class DownsideLowVolatility:
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
        if not _scheduled(decision_time, self.parameters):
            return None
        return _portfolio(_scores(context, parameters=self.parameters), parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return DownsideLowVolatility()
