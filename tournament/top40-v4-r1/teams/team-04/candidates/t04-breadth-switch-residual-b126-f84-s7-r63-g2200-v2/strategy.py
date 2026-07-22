"""Crypto-breadth-switched residual momentum for Team 04."""

from __future__ import annotations

import dataclasses
import math

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    interval_hours: int = 8
    beta_lookback_days: int = 126
    formation_days: int = 84
    skip_days: int = 7
    breadth_days: int = 63
    breadth_threshold: float = 0.5
    beta_clip: float = 2.5
    rebalance_weekday: int = 0
    rebalance_hour_utc: int = 0
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    total_gross: float = 0.22
    maximum_symbol_weight: float = 0.04
    maximum_abs_net: float = 0.24


_REFERENCE = StrategyParameters()


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        decision_time.weekday() == parameters.rebalance_weekday
        and decision_time.hour == parameters.rebalance_hour_utc
        and decision_time.minute == 0
        and decision_time.second == 0
        and decision_time.microsecond == 0
    )


def _complete_returns(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    required_bars: int,
    interval: pd.Timedelta,
) -> pd.Series:
    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)
    bounded = frame.tail(required_bars + 3)
    times = pd.to_datetime(bounded["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    history = bounded.loc[complete, ["open_time", "close"]].copy()
    history["open_time"] = times.loc[complete]
    history["close"] = pd.to_numeric(history["close"], errors="coerce")
    finite = np.isfinite(history["close"].to_numpy(dtype=float)) & history["close"].gt(0.0)
    history = (
        history.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .tail(required_bars)
        .reset_index(drop=True)
    )
    if len(history) != required_bars:
        return pd.Series(dtype=float)
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_bars,
        freq=interval,
    )
    if not pd.DatetimeIndex(history["open_time"]).equals(expected):
        return pd.Series(dtype=float)
    closes = history["close"].to_numpy(dtype=float)
    values = np.diff(np.log(closes))
    return pd.Series(values, index=pd.DatetimeIndex(history["open_time"].iloc[1:]), dtype=float)


def _residual_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> tuple[dict[str, float], float | None]:
    decision_time = _utc(context.decision_time)
    bars_per_day = 24 // parameters.interval_hours
    beta_bars = parameters.beta_lookback_days * bars_per_day
    formation_bars = parameters.formation_days * bars_per_day
    skip_bars = parameters.skip_days * bars_per_day
    required_bars = beta_bars + 1
    interval = pd.Timedelta(hours=parameters.interval_hours)
    histories: dict[str, pd.Series] = {}

    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        returns = _complete_returns(
            frame,
            decision_time=decision_time,
            required_bars=required_bars,
            interval=interval,
        )
        if len(returns) == beta_bars:
            histories[symbol] = returns
    if len(histories) < parameters.minimum_valid_symbols:
        return {}, None

    return_matrix = pd.DataFrame(histories, dtype=float).sort_index()
    return_matrix = return_matrix.dropna(axis=1, how="any")
    if len(return_matrix.columns) < parameters.minimum_valid_symbols:
        return {}, None
    breadth_bars = parameters.breadth_days * bars_per_day
    if breadth_bars > len(return_matrix):
        return {}, None
    positive_breadth = float(
        np.mean(return_matrix.iloc[-breadth_bars:].sum(axis=0) > 0.0)
    )
    market = return_matrix.median(axis=1)
    market_centered = market - float(market.mean())
    denominator = float(np.dot(market_centered, market_centered))
    if not math.isfinite(denominator) or denominator <= 1e-12:
        return {}, None

    scores: dict[str, float] = {}
    for symbol in sorted(return_matrix.columns):
        asset = return_matrix[symbol]
        asset_centered = asset - float(asset.mean())
        beta = float(np.dot(asset_centered, market_centered) / denominator)
        beta = float(np.clip(beta, -parameters.beta_clip, parameters.beta_clip))
        residual = asset - beta * market
        if skip_bars:
            window = residual.iloc[-formation_bars - skip_bars : -skip_bars]
        else:
            window = residual.iloc[-formation_bars:]
        values = window.to_numpy(dtype=float)
        realized = float(np.std(values, ddof=1))
        if len(values) != formation_bars or not math.isfinite(realized) or realized <= 1e-8:
            continue
        score = float(np.sum(values) / (realized * math.sqrt(formation_bars)))
        if math.isfinite(score):
            scores[symbol] = score
    return scores, positive_breadth


def _portfolio(
    scores: dict[str, float],
    *,
    regime_side: int,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if len(scores) < parameters.minimum_valid_symbols:
        return {}
    values = tuple(scores.values())
    if max(values) - min(values) <= 1e-12:
        return {}
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    side_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(ordered))),
    )
    side_count = min(side_count, len(ordered) // 2)
    if side_count < parameters.minimum_positions_per_side:
        return {}
    selected = ordered[-side_count:] if regime_side > 0 else ordered[:side_count]
    symbol_weight = parameters.total_gross / side_count
    if symbol_weight > parameters.maximum_symbol_weight:
        return {}
    if parameters.total_gross > parameters.maximum_abs_net:
        return {}
    targets = {
        symbol: symbol_weight if regime_side > 0 else -symbol_weight
        for symbol in selected
    }
    return {symbol: targets[symbol] for symbol in sorted(targets)}


class MarketResidualCrossSectionalMomentum:
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
        scores, positive_breadth = _residual_scores(
            context,
            parameters=self.parameters,
        )
        if positive_breadth is None:
            return {}
        regime_side = 1 if positive_breadth >= self.parameters.breadth_threshold else -1
        return _portfolio(
            scores,
            regime_side=regime_side,
            parameters=self.parameters,
        )


def build_strategy() -> TargetStrategy:
    return MarketResidualCrossSectionalMomentum()
