"""Team 02: causal seven-day residual low-MAX anti-lottery baseline."""

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
    max_lookback_days: int = 7
    liquidity_history_bars: int = 90
    minimum_positive_volume_fraction: float = 0.90
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    long_side_gross: float = 0.20
    short_side_gross: float = 0.16
    maximum_symbol_weight: float = 0.03
    high_max_short_symbol_cap: float = 0.02
    maximum_abs_net: float = 0.05


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


def _completed_bars(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    interval: pd.Timedelta,
) -> pd.DataFrame:
    required = {"open_time", "close", "quote_volume"}
    if not required.issubset(frame.columns):
        return pd.DataFrame(columns=sorted(required))
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    if not bool(complete.any()):
        return pd.DataFrame(columns=sorted(required))
    result = frame.loc[complete, ["open_time", "close", "quote_volume"]].copy()
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
    if result.empty:
        return pd.DataFrame(columns=sorted(required))
    aligned = (
        result["open_time"].dt.minute.eq(0)
        & result["open_time"].dt.second.eq(0)
        & result["open_time"].dt.microsecond.eq(0)
        & result["open_time"].dt.hour.mod(8).eq(0)
    )
    return (
        result.loc[aligned]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .reset_index(drop=True)
    )


def _liquid_complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    interval = pd.Timedelta(hours=parameters.interval_hours)
    bars = _completed_bars(frame, decision_time=decision_time, interval=interval)
    if len(bars) < parameters.liquidity_history_bars:
        return pd.DataFrame(columns=["open_time", "close", "quote_volume"])
    expected = pd.date_range(
        end=decision_time - interval,
        periods=parameters.liquidity_history_bars,
        freq=interval,
    )
    recent = bars.tail(parameters.liquidity_history_bars)
    if not pd.DatetimeIndex(recent["open_time"]).equals(expected):
        return pd.DataFrame(columns=["open_time", "close", "quote_volume"])
    positive_fraction = float((recent["quote_volume"] > 0.0).mean())
    positive = recent.loc[recent["quote_volume"] > 0.0, "quote_volume"]
    if (
        positive_fraction < parameters.minimum_positive_volume_fraction
        or positive.empty
        or not math.isfinite(float(positive.median()))
        or float(positive.median()) <= 0.0
    ):
        return pd.DataFrame(columns=["open_time", "close", "quote_volume"])
    return bars


def _daily_returns(bars: pd.DataFrame) -> pd.Series:
    if bars.empty:
        return pd.Series(dtype=float)
    bars = bars.assign(day=bars["open_time"].dt.floor("D"))
    daily_closes: list[tuple[pd.Timestamp, float]] = []
    for day, group in bars.groupby("day", sort=True, observed=True):
        if len(group) != 3 or set(group["open_time"].dt.hour.tolist()) != {0, 8, 16}:
            continue
        close_row = group.loc[group["open_time"].dt.hour.eq(16)]
        if len(close_row) != 1:
            continue
        daily_closes.append((pd.Timestamp(day), float(close_row.iloc[0]["close"])))

    returns: dict[pd.Timestamp, float] = {}
    for (previous_day, previous_close), (day, close) in zip(
        daily_closes, daily_closes[1:], strict=False
    ):
        if day - previous_day != pd.Timedelta(days=1):
            continue
        value = math.log(close / previous_close)
        if math.isfinite(value):
            returns[day] = value
    if not returns:
        return pd.Series(dtype=float)
    return pd.Series(returns, dtype=float).sort_index()


def _max_scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    eligible = tuple(sorted({str(symbol) for symbol in context.eligible_symbols}))
    histories: dict[str, pd.Series] = {}
    for symbol in eligible:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        complete = _liquid_complete_history(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        daily = _daily_returns(complete)
        if not daily.empty:
            histories[symbol] = daily
    if len(histories) < parameters.minimum_valid_symbols:
        return {}

    returns = pd.DataFrame(histories, dtype=float).sort_index()
    residuals = returns.sub(returns.median(axis=1, skipna=True), axis=0)
    target_days = pd.date_range(
        end=decision_time.floor("D") - pd.Timedelta(days=1),
        periods=parameters.max_lookback_days,
        freq="D",
    )
    scores: dict[str, float] = {}
    for symbol in sorted(histories):
        window = residuals[symbol].reindex(target_days)
        values = window.to_numpy(dtype=float)
        if len(values) != parameters.max_lookback_days or not np.isfinite(values).all():
            continue
        value = float(np.max(values))
        if math.isfinite(value):
            scores[symbol] = value
    return scores


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

    # Low-MAX names are long. The high-MAX short sleeve is deliberately smaller and has a
    # stricter per-name cap because lottery winners can continue squeezing.
    longs = ordered[:side_count]
    shorts = ordered[-side_count:]
    long_weight = parameters.long_side_gross / side_count
    short_weight = parameters.short_side_gross / side_count
    if long_weight > parameters.maximum_symbol_weight + 1e-12:
        return {}
    if short_weight > parameters.high_max_short_symbol_cap + 1e-12:
        return {}

    result = {symbol: long_weight for symbol in longs}
    result.update({symbol: -short_weight for symbol in shorts})
    gross_limit = parameters.long_side_gross + parameters.short_side_gross
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > gross_limit + 1e-12 or gross > 0.5 + 1e-12:
        return {}
    if abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class ResidualLowMax:
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
        scores = _max_scores(context, parameters=self.parameters)
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return ResidualLowMax()
