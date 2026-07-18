"""Team 02: causal high-MAX attention persistence with seven daily vintages."""

from __future__ import annotations

import dataclasses
import math
from collections import deque

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
    vintage_count: int = 7
    tape_short_days: int = 7
    tape_long_days: int = 28
    directional_large_side_gross: float = 0.20
    directional_small_side_gross: float = 0.16
    neutral_side_gross: float = 0.18
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.04


@dataclasses.dataclass(frozen=True)
class Vintage:
    decision_time: pd.Timestamp
    weights: tuple[tuple[str, float], ...]


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
    # Only the fixed liquidity window and a possible incomplete daily triplet can affect the
    # seven-day MAX score. Bounding the input avoids rebuilding irrelevant expanding history at
    # every daily decision while preserving every return and liquidity observation used below.
    maximum_input_bars = parameters.liquidity_history_bars + (24 // parameters.interval_hours)
    bars = _completed_bars(
        frame.tail(maximum_input_bars),
        decision_time=decision_time,
        interval=interval,
    )
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
    return recent.reset_index(drop=True)


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


def _max_scores_and_tape_state(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> tuple[dict[str, float], str]:
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
        return {}, "neutral"

    returns = pd.DataFrame(histories, dtype=float).sort_index()
    market_return = returns.median(axis=1, skipna=True)
    market_days = pd.date_range(
        end=decision_time.floor("D") - pd.Timedelta(days=1),
        periods=parameters.tape_long_days,
        freq="D",
    )
    market_window = market_return.reindex(market_days)
    market_breadth = returns.notna().sum(axis=1).reindex(market_days)
    if (
        not np.isfinite(market_window.to_numpy(dtype=float)).all()
        or (market_breadth < parameters.minimum_valid_symbols).any()
    ):
        return {}, "neutral"

    short_tape = float(market_window.tail(parameters.tape_short_days).sum())
    long_tape = float(market_window.sum())
    if short_tape > 0.0 and long_tape > 0.0:
        tape_state = "bull"
    elif short_tape < 0.0 and long_tape < 0.0:
        tape_state = "bear"
    else:
        tape_state = "neutral"

    residuals = returns.sub(market_return, axis=0)
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
    return scores, tape_state


def _routed_side_gross(
    tape_state: str,
    *,
    parameters: StrategyParameters,
) -> tuple[float, float]:
    if tape_state == "bull":
        return parameters.directional_large_side_gross, parameters.directional_small_side_gross
    if tape_state == "bear":
        return parameters.directional_small_side_gross, parameters.directional_large_side_gross
    return parameters.neutral_side_gross, parameters.neutral_side_gross


def _portfolio(
    scores: dict[str, float],
    *,
    tape_state: str,
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

    # Trial 1 falsified the anti-lottery sign. Trial 2 admits the pivot: high-MAX names are the
    # attention-persistence long sleeve and low-MAX names are the short sleeve.
    shorts = ordered[:side_count]
    longs = ordered[-side_count:]
    long_gross, short_gross = _routed_side_gross(tape_state, parameters=parameters)
    long_weight = long_gross / side_count
    short_weight = short_gross / side_count
    if long_weight > parameters.maximum_symbol_weight + 1e-12:
        return {}
    if short_weight > parameters.maximum_symbol_weight + 1e-12:
        return {}

    result = {symbol: long_weight for symbol in longs}
    result.update({symbol: -short_weight for symbol in shorts})
    gross_limit = long_gross + short_gross
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > gross_limit + 1e-12 or gross > 0.5 + 1e-12:
        return {}
    if abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


def _aggregate_vintages(
    vintages: tuple[Vintage, ...],
    *,
    eligible_symbols: frozenset[str],
    divisor: int,
) -> dict[str, float]:
    totals: dict[str, float] = {}
    for vintage in vintages:
        for symbol, weight in vintage.weights:
            if symbol in eligible_symbols:
                totals[symbol] = totals.get(symbol, 0.0) + weight / divisor
    return {
        symbol: value
        for symbol, value in sorted(totals.items())
        if abs(value) > 1e-15
    }


class HighMaxVintageRouter:
    def __init__(self, parameters: StrategyParameters = _REFERENCE):
        self.parameters = parameters
        self._vintages: deque[Vintage] = deque()
        self._last_decision_time: pd.Timestamp | None = None
        self._last_target: dict[str, float] = {}

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
        if self._last_decision_time is not None:
            if decision_time == self._last_decision_time:
                return dict(self._last_target)
            if decision_time < self._last_decision_time:
                return {}

        scores, tape_state = _max_scores_and_tape_state(context, parameters=self.parameters)
        cohort = _portfolio(scores, tape_state=tape_state, parameters=self.parameters)
        self._vintages.append(
            Vintage(
                decision_time=decision_time,
                weights=tuple(sorted(cohort.items())),
            )
        )
        expiry = decision_time - pd.Timedelta(days=self.parameters.vintage_count)
        while self._vintages and self._vintages[0].decision_time <= expiry:
            self._vintages.popleft()

        target = _aggregate_vintages(
            tuple(self._vintages),
            eligible_symbols=frozenset(str(value) for value in context.eligible_symbols),
            divisor=self.parameters.vintage_count,
        )
        self._last_decision_time = decision_time
        self._last_target = target
        return dict(target)


def build_strategy() -> TargetStrategy:
    return HighMaxVintageRouter()
