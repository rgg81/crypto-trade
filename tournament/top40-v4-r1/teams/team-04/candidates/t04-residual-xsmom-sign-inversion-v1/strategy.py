"""Exact target-sign inversion of Team 04 residual momentum."""

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
    beta_clip: float = 2.5
    rebalance_weekday: int = 0
    rebalance_hour_utc: int = 0
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    total_gross: float = 0.44
    minimum_side_gross: float = 0.18
    maximum_side_gross: float = 0.26
    maximum_symbol_weight: float = 0.04
    maximum_abs_net: float = 0.1


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
) -> tuple[dict[str, float], dict[str, float]]:
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
        return {}, {}

    return_matrix = pd.DataFrame(histories, dtype=float).sort_index()
    return_matrix = return_matrix.dropna(axis=1, how="any")
    if len(return_matrix.columns) < parameters.minimum_valid_symbols:
        return {}, {}
    market = return_matrix.median(axis=1)
    market_centered = market - float(market.mean())
    denominator = float(np.dot(market_centered, market_centered))
    if not math.isfinite(denominator) or denominator <= 1e-12:
        return {}, {}

    scores: dict[str, float] = {}
    betas: dict[str, float] = {}
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
            betas[symbol] = beta
    return scores, betas


def _side_gross(
    longs: list[str],
    shorts: list[str],
    betas: dict[str, float],
    *,
    parameters: StrategyParameters,
) -> tuple[float, float]:
    long_beta = float(np.mean([betas[symbol] for symbol in longs]))
    short_beta = float(np.mean([betas[symbol] for symbol in shorts]))
    long_gross = parameters.total_gross / 2.0
    if long_beta > 0.05 and short_beta > 0.05:
        long_gross = parameters.total_gross * short_beta / (long_beta + short_beta)
        long_gross = float(
            np.clip(
                long_gross,
                parameters.minimum_side_gross,
                parameters.maximum_side_gross,
            )
        )
    return long_gross, parameters.total_gross - long_gross


def _portfolio(
    scores: dict[str, float],
    betas: dict[str, float],
    *,
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
    shorts = ordered[:side_count]
    longs = ordered[-side_count:]
    long_gross, short_gross = _side_gross(
        longs,
        shorts,
        betas,
        parameters=parameters,
    )
    long_weight = long_gross / side_count
    short_weight = short_gross / side_count
    if max(long_weight, short_weight) > parameters.maximum_symbol_weight:
        return {}
    if abs(long_gross - short_gross) > parameters.maximum_abs_net:
        return {}
    targets = {symbol: -short_weight for symbol in shorts}
    targets.update({symbol: long_weight for symbol in longs})
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
        scores, betas = _residual_scores(context, parameters=self.parameters)
        targets = _portfolio(scores, betas, parameters=self.parameters)
        return {symbol: -weight for symbol, weight in targets.items()}


def build_strategy() -> TargetStrategy:
    return MarketResidualCrossSectionalMomentum()
