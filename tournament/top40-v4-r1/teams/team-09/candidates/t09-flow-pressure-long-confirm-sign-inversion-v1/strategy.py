"""Team 09 exact sign inversion of the repaired flow-pressure candidate."""

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
    signal_bars: int = 18
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    entry_fraction_per_side: float = 0.20
    retention_fraction_per_side: float = 0.30
    total_gross: float = 0.26
    maximum_symbol_weight: float = 0.025
    maximum_abs_net: float = 0.02
    winsor_z: float = 4.0
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_positive_activity_fraction: float = 0.95
    flow_weight: float = 0.50
    price_weight: float = 0.30
    activity_weight: float = 0.20
    long_divergence_scale: float = 0.10
    short_divergence_scale: float = 0.35


@dataclasses.dataclass(frozen=True)
class PressureFeature:
    flow_pressure: float
    residual_price_pressure: float
    signed_activity_confirmation: float
    flow_price_alignment: float


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


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    required = {
        "open_time",
        "close",
        "quote_volume",
        "trade_count",
        "taker_buy_quote_volume",
    }
    if not required.issubset(frame.columns):
        return pd.DataFrame(columns=sorted(required))
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_bars = parameters.lookback_bars + 1
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_bars,
        freq=interval,
    )
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    data = frame.loc[complete, sorted(required)].copy()
    data["open_time"] = times.loc[complete]
    for column in (
        "close",
        "quote_volume",
        "trade_count",
        "taker_buy_quote_volume",
    ):
        data[column] = pd.to_numeric(data[column], errors="coerce")
    finite = np.isfinite(
        data[["close", "quote_volume", "trade_count", "taker_buy_quote_volume"]].to_numpy(
            dtype=float
        )
    ).all(axis=1)
    data = (
        data.loc[
            finite
            & data["close"].gt(0.0)
            & data["quote_volume"].ge(0.0)
            & data["trade_count"].ge(0.0)
            & data["taker_buy_quote_volume"].ge(0.0)
        ]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .set_index("open_time")
        .reindex(expected)
    )
    if len(data) != required_bars or data.isna().any().any():
        return pd.DataFrame(columns=sorted(required))
    positive_activity = data["quote_volume"].gt(0.0) & data["trade_count"].gt(0.0)
    if float(positive_activity.mean()) < parameters.minimum_positive_activity_fraction:
        return pd.DataFrame(columns=sorted(required))
    median_volume = float(data.loc[positive_activity, "quote_volume"].median())
    if not math.isfinite(median_volume) or median_volume < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=sorted(required))
    data.index.name = "open_time"
    return data.reset_index()


def _robust_standardize(values: np.ndarray, clip: float) -> np.ndarray:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(values))
    if not math.isfinite(scale) or scale <= 1e-12:
        return np.zeros_like(values, dtype=float)
    return np.clip((values - median) / scale, -clip, clip)


def _feature_map(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, PressureFeature]:
    histories: dict[str, pd.DataFrame] = {}
    decision_time = _utc(context.decision_time)
    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _complete_history(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if not history.empty:
            histories[symbol] = history
    if len(histories) < parameters.minimum_valid_symbols:
        return {}

    price_returns: dict[str, pd.Series] = {}
    flow_balances: dict[str, pd.Series] = {}
    activity_surprises: dict[str, pd.Series] = {}
    for symbol, history in histories.items():
        index = pd.DatetimeIndex(history["open_time"].iloc[1:])
        close = history["close"].to_numpy(dtype=float)
        quote = history["quote_volume"].to_numpy(dtype=float)[1:]
        trades = history["trade_count"].to_numpy(dtype=float)[1:]
        taker_quote = history["taker_buy_quote_volume"].to_numpy(dtype=float)[1:]
        flow = np.clip(2.0 * taker_quote / np.maximum(quote, 1e-12) - 1.0, -1.0, 1.0)
        log_quote = np.log1p(quote)
        log_trades = np.log1p(trades)
        activity = 0.5 * (
            _robust_standardize(log_quote, parameters.winsor_z)
            + _robust_standardize(log_trades, parameters.winsor_z)
        )
        price_returns[symbol] = pd.Series(np.diff(np.log(close)), index=index, dtype=float)
        flow_balances[symbol] = pd.Series(flow, index=index, dtype=float)
        activity_surprises[symbol] = pd.Series(activity, index=index, dtype=float)

    returns = pd.DataFrame(price_returns, dtype=float).dropna(axis=1, how="any")
    common = sorted(set(returns.columns) & set(flow_balances) & set(activity_surprises))
    if len(common) < parameters.minimum_valid_symbols:
        return {}
    returns = returns.loc[:, common]
    residual_returns = returns.sub(returns.median(axis=1, skipna=False), axis=0)
    flow_frame = pd.DataFrame({symbol: flow_balances[symbol] for symbol in common})
    residual_flow = flow_frame.sub(flow_frame.median(axis=1, skipna=False), axis=0)

    result: dict[str, PressureFeature] = {}
    for symbol in common:
        price = residual_returns[symbol].to_numpy(dtype=float)
        flow = residual_flow[symbol].to_numpy(dtype=float)
        activity = activity_surprises[symbol].to_numpy(dtype=float)
        trailing_price = price[-parameters.signal_bars :]
        trailing_flow = flow[-parameters.signal_bars :]
        trailing_activity = activity[-parameters.signal_bars :]
        price_scale = max(float(np.std(price, ddof=1)), 1e-6)
        flow_pressure = float(np.mean(trailing_flow))
        price_pressure = float(
            np.sum(trailing_price) / (price_scale * math.sqrt(parameters.signal_bars))
        )
        flow_direction = 1.0 if flow_pressure > 0.0 else -1.0 if flow_pressure < 0.0 else 0.0
        signed_activity = flow_direction * max(float(np.mean(trailing_activity)), 0.0)
        alignment = float(np.mean(np.sign(trailing_flow) * np.sign(trailing_price)))
        feature = PressureFeature(
            flow_pressure=flow_pressure,
            residual_price_pressure=price_pressure,
            signed_activity_confirmation=signed_activity,
            flow_price_alignment=alignment,
        )
        if all(math.isfinite(value) for value in dataclasses.astuple(feature)):
            result[symbol] = feature
    return result


def _centered_ranks(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=lambda symbol: (values[symbol], symbol))
    if len(ordered) <= 1:
        return {symbol: 0.0 for symbol in ordered}
    return {symbol: index / (len(ordered) - 1) - 0.5 for index, symbol in enumerate(ordered)}


def _pressure_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    features = _feature_map(context, parameters=parameters)
    if len(features) < parameters.minimum_valid_symbols:
        return {}
    flow_rank = _centered_ranks(
        {symbol: feature.flow_pressure for symbol, feature in features.items()}
    )
    price_rank = _centered_ranks(
        {symbol: feature.residual_price_pressure for symbol, feature in features.items()}
    )
    activity_rank = _centered_ranks(
        {symbol: feature.signed_activity_confirmation for symbol, feature in features.items()}
    )
    scores: dict[str, float] = {}
    for symbol in sorted(features):
        score = (
            parameters.flow_weight * flow_rank[symbol]
            + parameters.price_weight * price_rank[symbol]
            + parameters.activity_weight * activity_rank[symbol]
        )
        if features[symbol].flow_price_alignment <= 0.0:
            scale = (
                parameters.long_divergence_scale
                if score > 0.0
                else parameters.short_divergence_scale
            )
            score *= scale
        scores[symbol] = score
    return scores


def _select_sides(
    scores: dict[str, float],
    *,
    previous_longs: frozenset[str],
    previous_shorts: frozenset[str],
    parameters: StrategyParameters,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    side_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.entry_fraction_per_side * len(ordered))),
    )
    side_count = min(side_count, len(ordered) // 2)
    outer_count = max(
        side_count,
        int(math.ceil(parameters.retention_fraction_per_side * len(ordered))),
    )
    short_outer = set(ordered[:outer_count])
    long_outer = set(ordered[-outer_count:])
    longs = [symbol for symbol in sorted(previous_longs) if symbol in long_outer]
    shorts = [symbol for symbol in sorted(previous_shorts) if symbol in short_outer]
    for symbol in reversed(ordered):
        if len(longs) >= side_count:
            break
        if symbol not in longs and symbol not in shorts:
            longs.append(symbol)
    for symbol in ordered:
        if len(shorts) >= side_count:
            break
        if symbol not in shorts and symbol not in longs:
            shorts.append(symbol)
    return tuple(sorted(longs)), tuple(sorted(shorts))


def _portfolio(
    longs: tuple[str, ...],
    shorts: tuple[str, ...],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if (
        len(longs) < parameters.minimum_positions_per_side
        or len(shorts) < parameters.minimum_positions_per_side
    ):
        return {}
    side_weight = parameters.total_gross / (2.0 * len(longs))
    if side_weight > parameters.maximum_symbol_weight + 1e-12:
        return {}
    result = {symbol: side_weight for symbol in longs}
    result.update({symbol: -side_weight for symbol in shorts})
    gross = math.fsum(abs(weight) for weight in result.values())
    net = math.fsum(result.values())
    if gross > parameters.total_gross + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class WeeklyFlowPressure:
    def __init__(self, parameters: StrategyParameters = PARAMETERS):
        self.parameters = parameters
        self._longs: frozenset[str] = frozenset()
        self._shorts: frozenset[str] = frozenset()

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
        scores = _pressure_scores(context, parameters=self.parameters)
        if not scores:
            self._longs = frozenset()
            self._shorts = frozenset()
            return {}
        longs, shorts = _select_sides(
            scores,
            previous_longs=self._longs,
            previous_shorts=self._shorts,
            parameters=self.parameters,
        )
        target = _portfolio(longs, shorts, parameters=self.parameters)
        if not target:
            self._longs = frozenset()
            self._shorts = frozenset()
            return {}
        self._longs = frozenset(longs)
        self._shorts = frozenset(shorts)
        return {symbol: -weight for symbol, weight in target.items()}


def build_strategy() -> TargetStrategy:
    return WeeklyFlowPressure()
