"""Team 03: causal residual positive-jump and skew anti-euphoria baseline."""

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
    lookback_bars: int = 126
    winsor_mad_multiplier: float = 4.0
    jump_mad_threshold: float = 1.25
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_positive_volume_fraction: float = 0.90
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.30
    total_gross: float = 0.40
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05
    jump_variance_weight: float = 0.35
    positive_tail_share_weight: float = 0.25
    residual_skew_weight: float = 0.25
    tail_breadth_weight: float = 0.15


@dataclasses.dataclass(frozen=True)
class AntiEuphoriaFeature:
    positive_jump_variance: float
    positive_tail_share: float
    residual_skew: float
    positive_tail_breadth: float


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
        log_prices = np.log(history["close"].to_numpy(dtype=float))
        values = np.diff(log_prices)
        index = pd.DatetimeIndex(history["open_time"].iloc[1:])
        if len(values) == parameters.lookback_bars and np.isfinite(values).all():
            histories[symbol] = pd.Series(values, index=index, dtype=float)
    if len(histories) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    returns = pd.DataFrame(histories, dtype=float).sort_index()
    returns = returns.dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    market_return = returns.median(axis=1, skipna=False)
    return returns.sub(market_return, axis=0)


def _robust_clip(values: np.ndarray, multiplier: float) -> tuple[np.ndarray, float, float]:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(values))
    if not math.isfinite(scale) or scale <= 1e-12:
        return values.copy(), median, 0.0
    return np.clip(values, median - multiplier * scale, median + multiplier * scale), median, scale


def _anti_euphoria_components(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, AntiEuphoriaFeature]:
    residuals = _residual_returns(context, parameters=parameters)
    if residuals.empty:
        return {}
    result: dict[str, AntiEuphoriaFeature] = {}
    for symbol in sorted(residuals.columns):
        raw = residuals[symbol].to_numpy(dtype=float)
        clipped, median, scale = _robust_clip(raw, parameters.winsor_mad_multiplier)
        centered = clipped - float(np.mean(clipped))
        standard_deviation = float(np.sqrt(np.mean(np.square(centered))))
        residual_skew = (
            float(np.mean(np.power(centered / standard_deviation, 3.0)))
            if standard_deviation > 1e-12
            else 0.0
        )
        jump_threshold = max(0.0, median + parameters.jump_mad_threshold * scale)
        positive_jumps = clipped > jump_threshold
        positive_jump_variance = float(
            np.mean(np.where(positive_jumps, np.square(clipped), 0.0))
        )
        total_variance = float(np.mean(np.square(clipped)))
        positive_tail_share = positive_jump_variance / total_variance if total_variance > 0 else 0.0
        feature = AntiEuphoriaFeature(
            positive_jump_variance=positive_jump_variance,
            positive_tail_share=positive_tail_share,
            residual_skew=residual_skew,
            positive_tail_breadth=float(np.mean(positive_jumps)),
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


def _anti_euphoria_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    components = _anti_euphoria_components(context, parameters=parameters)
    if len(components) < parameters.minimum_valid_symbols:
        return {}
    jump_rank = _percentile_ranks(
        {symbol: value.positive_jump_variance for symbol, value in components.items()}
    )
    share_rank = _percentile_ranks(
        {symbol: value.positive_tail_share for symbol, value in components.items()}
    )
    skew_rank = _percentile_ranks(
        {symbol: value.residual_skew for symbol, value in components.items()}
    )
    breadth_rank = _percentile_ranks(
        {symbol: value.positive_tail_breadth for symbol, value in components.items()}
    )
    return {
        symbol: (
            parameters.jump_variance_weight * jump_rank[symbol]
            + parameters.positive_tail_share_weight * share_rank[symbol]
            + parameters.residual_skew_weight * skew_rank[symbol]
            + parameters.tail_breadth_weight * breadth_rank[symbol]
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
    longs = ordered[:side_count]
    shorts = ordered[-side_count:]
    weight = parameters.total_gross / (2.0 * side_count)
    if weight > parameters.maximum_symbol_weight + 1e-12:
        return {}
    result = {symbol: weight for symbol in longs}
    result.update({symbol: -weight for symbol in shorts})
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > min(parameters.total_gross, 0.5) + 1e-12:
        return {}
    if abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class ResidualAntiEuphoria:
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
        scores = _anti_euphoria_scores(context, parameters=self.parameters)
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return ResidualAntiEuphoria()
