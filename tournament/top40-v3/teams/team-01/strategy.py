"""Team 01: causal weekday-residual seasonality baseline."""

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
    same_weekday_occurrences: int = 13
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    total_gross: float = 0.48
    maximum_symbol_weight: float = 0.03
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
    """Return finite bars whose complete interval is known at the decision."""

    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.DataFrame(columns=["open_time", "close"])
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    if not bool(complete.any()):
        return pd.DataFrame(columns=["open_time", "close"])
    result = frame.loc[complete, ["open_time", "close"]].copy()
    result["open_time"] = times.loc[complete]
    result["close"] = pd.to_numeric(result["close"], errors="coerce")
    finite = np.isfinite(result["close"].to_numpy(dtype=float)) & (result["close"] > 0.0)
    result = result.loc[finite]
    if result.empty:
        return pd.DataFrame(columns=["open_time", "close"])
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


def _daily_returns(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series:
    """Build exact UTC-day close-to-close log returns from complete 8-hour triplets."""

    interval = pd.Timedelta(hours=parameters.interval_hours)
    bars = _completed_bars(frame, decision_time=decision_time, interval=interval)
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
            # The close at day 16:00 completes the return from day 00:00 through day 24:00.
            returns[day] = value
    if not returns:
        return pd.Series(dtype=float)
    return pd.Series(returns, dtype=float).sort_index()


def _weekday_scores(
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
        daily = _daily_returns(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if not daily.empty:
            histories[symbol] = daily
    if len(histories) < parameters.minimum_valid_symbols:
        return {}

    returns = pd.DataFrame(histories, dtype=float).sort_index()
    residuals = returns.sub(returns.median(axis=1, skipna=True), axis=0)
    target_weekday = decision_time.weekday()
    scores: dict[str, float] = {}
    for symbol in sorted(histories):
        series = residuals[symbol]
        same_weekday = series.loc[series.index.weekday == target_weekday].dropna()
        if len(same_weekday) < parameters.same_weekday_occurrences:
            continue
        value = float(same_weekday.iloc[-parameters.same_weekday_occurrences :].mean())
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

    shorts = ordered[:side_count]
    longs = ordered[-side_count:]
    side_gross = parameters.total_gross / 2.0
    weight = side_gross / side_count
    if weight > parameters.maximum_symbol_weight + 1e-12:
        return {}

    result = {symbol: -weight for symbol in shorts}
    result.update({symbol: weight for symbol in longs})
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > parameters.total_gross + 1e-12:
        return {}
    if abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class WeekdayResidualSeasonality:
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
        scores = _weekday_scores(context, parameters=self.parameters)
        return _portfolio(scores, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return WeekdayResidualSeasonality()
