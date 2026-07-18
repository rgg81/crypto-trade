"""Team 07: causal liquidity-conditioned residual continuation/reversal router."""

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
    recent_move_bars: int = 3
    liquidity_state_bars: int = 63
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.30
    total_gross: float = 0.40
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05
    router_volume_weight: float = 0.35
    router_trade_weight: float = 0.25
    router_impact_weight: float = 0.30
    router_flow_weight: float = 0.10
    state_z_cap: float = 3.0


@dataclasses.dataclass(frozen=True)
class RouterFeature:
    recent_residual_move: float
    quote_volume_state: float
    trade_breadth_state: float
    price_impact_state: float
    flow_confirmation: float
    liquidity_router: float
    routed_expected_return: float


_REFERENCE = StrategyParameters()
_REQUIRED_FIELDS = (
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_quote_volume",
)


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
    if not set(_REQUIRED_FIELDS).issubset(frame.columns):
        return pd.DataFrame(columns=_REQUIRED_FIELDS)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    result = frame.loc[complete, list(_REQUIRED_FIELDS)].copy()
    if result.empty:
        return pd.DataFrame(columns=_REQUIRED_FIELDS)
    result["open_time"] = times.loc[complete]
    numeric_fields = _REQUIRED_FIELDS[1:]
    for field in numeric_fields:
        result[field] = pd.to_numeric(result[field], errors="coerce")
    finite = np.ones(len(result), dtype=bool)
    for field in numeric_fields:
        finite &= np.isfinite(result[field].to_numpy(dtype=float))
    finite &= (
        (result["open"] > 0.0)
        & (result["high"] > 0.0)
        & (result["low"] > 0.0)
        & (result["close"] > 0.0)
        & (result["volume"] > 0.0)
        & (result["quote_volume"] > 0.0)
        & (result["trade_count"] > 0.0)
        & (result["taker_buy_quote_volume"] >= 0.0)
        & (result["taker_buy_quote_volume"] <= result["quote_volume"])
        & (result["high"] >= result["low"])
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
    required_bars = parameters.liquidity_state_bars + parameters.recent_move_bars + 1
    if len(result) < required_bars:
        return pd.DataFrame(columns=_REQUIRED_FIELDS)
    recent = result.tail(required_bars).reset_index(drop=True)
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_bars,
        freq=interval,
    )
    if not pd.DatetimeIndex(recent["open_time"]).equals(expected):
        return pd.DataFrame(columns=_REQUIRED_FIELDS)
    median_quote_volume = float(recent["quote_volume"].median())
    if (
        not math.isfinite(median_quote_volume)
        or median_quote_volume < parameters.minimum_median_quote_volume
    ):
        return pd.DataFrame(columns=_REQUIRED_FIELDS)
    return recent


def _histories_and_residuals(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    decision_time = _utc(context.decision_time)
    histories: dict[str, pd.DataFrame] = {}
    returns: dict[str, pd.Series] = {}
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
            histories[symbol] = history
            returns[symbol] = pd.Series(values, index=index, dtype=float)
    if len(returns) < parameters.minimum_valid_symbols:
        return {}, pd.DataFrame()
    return_frame = pd.DataFrame(returns, dtype=float).sort_index().dropna(axis=1, how="any")
    valid_symbols = tuple(sorted(return_frame.columns))
    if len(valid_symbols) < parameters.minimum_valid_symbols:
        return {}, pd.DataFrame()
    market_return = return_frame.median(axis=1, skipna=False)
    residuals = return_frame.sub(market_return, axis=0)
    return {symbol: histories[symbol] for symbol in valid_symbols}, residuals


def _relative_state(recent_value: float, history: np.ndarray, z_cap: float) -> float:
    median = float(np.median(history))
    mad = float(np.median(np.abs(history - median)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = max(abs(median), 1e-12)
    z_score = float(np.clip((recent_value - median) / scale, -z_cap, z_cap))
    return math.tanh(z_score)


def _smooth_router(
    *,
    quote_volume_state: float,
    trade_breadth_state: float,
    price_impact_state: float,
    flow_confirmation: float,
    parameters: StrategyParameters = _REFERENCE,
) -> float:
    raw = (
        parameters.router_volume_weight * quote_volume_state
        + parameters.router_trade_weight * trade_breadth_state
        - parameters.router_impact_weight * price_impact_state
        + parameters.router_flow_weight * flow_confirmation
    )
    return math.tanh(raw)


def _router_features(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, RouterFeature]:
    histories, residuals = _histories_and_residuals(context, parameters=parameters)
    if residuals.empty:
        return {}
    split = parameters.liquidity_state_bars
    result: dict[str, RouterFeature] = {}
    for symbol in sorted(residuals.columns):
        history = histories[symbol].iloc[1:].reset_index(drop=True)
        state_rows = history.iloc[:split]
        move_rows = history.iloc[split:]
        residual_values = residuals[symbol].to_numpy(dtype=float)
        recent_move = float(np.sum(residual_values[-parameters.recent_move_bars :]))

        state_quote = state_rows["quote_volume"].to_numpy(dtype=float)
        recent_quote = float(move_rows["quote_volume"].mean())
        quote_state = _relative_state(recent_quote, state_quote, parameters.state_z_cap)

        state_trades = state_rows["trade_count"].to_numpy(dtype=float)
        recent_trades = float(move_rows["trade_count"].mean())
        trade_state = _relative_state(recent_trades, state_trades, parameters.state_z_cap)

        ranges = np.log(history["high"].to_numpy(dtype=float) / history["low"].to_numpy(dtype=float))
        normalized_volume = history["quote_volume"].to_numpy(dtype=float) / float(
            np.median(state_quote)
        )
        impact = ranges / np.sqrt(normalized_volume)
        impact_state = _relative_state(
            float(np.mean(impact[-parameters.recent_move_bars :])),
            impact[:split],
            parameters.state_z_cap,
        )

        taker_share = (
            move_rows["taker_buy_quote_volume"].to_numpy(dtype=float)
            / move_rows["quote_volume"].to_numpy(dtype=float)
        )
        move_direction = 1.0 if recent_move > 0.0 else -1.0 if recent_move < 0.0 else 0.0
        flow_confirmation = move_direction * float(np.mean(2.0 * taker_share - 1.0))
        router = _smooth_router(
            quote_volume_state=quote_state,
            trade_breadth_state=trade_state,
            price_impact_state=impact_state,
            flow_confirmation=flow_confirmation,
            parameters=parameters,
        )
        feature = RouterFeature(
            recent_residual_move=recent_move,
            quote_volume_state=quote_state,
            trade_breadth_state=trade_state,
            price_impact_state=impact_state,
            flow_confirmation=flow_confirmation,
            liquidity_router=router,
            routed_expected_return=recent_move * router,
        )
        if all(math.isfinite(value) for value in dataclasses.astuple(feature)):
            result[symbol] = feature
    return result


def _routed_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    features = _router_features(context, parameters=parameters)
    return {
        symbol: feature.routed_expected_return for symbol, feature in sorted(features.items())
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


class LiquidityConditionedResidualRouter:
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
        scores = _routed_scores(context, parameters=self.parameters)
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return LiquidityConditionedResidualRouter()
