"""Team 05 pivot: long-formation reversal in volatile non-mega-cap coins."""

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
    formation_bars: int = 189
    holding_weeks: int = 4
    excluded_liquidity_leaders: int = 5
    volatility_quantile: float = 0.50
    selected_fraction_per_side: float = 0.20
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 3
    total_gross: float = 0.40
    maximum_symbol_weight: float = 0.10
    maximum_abs_net: float = 0.25


@dataclasses.dataclass(frozen=True)
class Vintage:
    decision_time: pd.Timestamp
    weights: tuple[tuple[str, float], ...]


PARAMETERS = StrategyParameters()


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


def _close_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series:
    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_closes = parameters.formation_bars + 1
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_closes,
        freq=interval,
    )
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    data = frame.loc[complete, ["open_time", "close"]].copy()
    data["open_time"] = times.loc[complete]
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    finite = np.isfinite(data["close"].to_numpy(dtype=float)) & data["close"].gt(0.0)
    close = (
        data.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .set_index("open_time")["close"]
        .reindex(expected)
    )
    if len(close) != required_closes or close.isna().any():
        return pd.Series(dtype=float)
    return close.astype(float)


def _cohort(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    ordered_members = tuple(dict.fromkeys(str(value) for value in context.eligible_symbols))
    research_pool = ordered_members[parameters.excluded_liquidity_leaders :]
    formation: dict[str, float] = {}
    volatility: dict[str, float] = {}
    for symbol in research_pool:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        close = _close_history(
            frame,
            decision_time=_utc(context.decision_time),
            parameters=parameters,
        )
        if close.empty:
            continue
        log_returns = np.diff(np.log(close.to_numpy(dtype=float)))
        if len(log_returns) != parameters.formation_bars or not np.isfinite(log_returns).all():
            continue
        sigma = float(np.std(log_returns, ddof=1))
        move = float(np.sum(log_returns))
        if math.isfinite(sigma) and sigma > 0.0 and math.isfinite(move):
            formation[symbol] = move
            volatility[symbol] = sigma
    if len(formation) < parameters.minimum_valid_symbols:
        return {}

    threshold = float(np.quantile(list(volatility.values()), parameters.volatility_quantile))
    volatile = [
        symbol
        for symbol in formation
        if volatility[symbol] >= threshold
    ]
    ordered = sorted(volatile, key=lambda symbol: (formation[symbol], symbol))
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
    return {symbol: result[symbol] for symbol in sorted(result)}


class WeeklyLongFormationReversal:
    def __init__(self, parameters: StrategyParameters = PARAMETERS):
        self.parameters = parameters
        self._vintages: list[Vintage] = []
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
        if not _scheduled(decision_time, self.parameters):
            return None
        if self._last_decision_time is not None:
            if decision_time == self._last_decision_time:
                return dict(self._last_target)
            if decision_time < self._last_decision_time:
                return {}

        cutoff = decision_time - pd.Timedelta(weeks=self.parameters.holding_weeks)
        self._vintages = [item for item in self._vintages if item.decision_time > cutoff]
        cohort = _cohort(context, parameters=self.parameters)
        if cohort:
            self._vintages.append(Vintage(decision_time, tuple(sorted(cohort.items()))))

        eligible = {str(value) for value in context.eligible_symbols}
        totals: dict[str, float] = {}
        for vintage in self._vintages:
            for symbol, weight in vintage.weights:
                if symbol in eligible:
                    totals[symbol] = (
                        totals.get(symbol, 0.0) + weight / self.parameters.holding_weeks
                    )
        target = {
            symbol: weight
            for symbol, weight in sorted(totals.items())
            if abs(weight) > 1e-15
        }
        gross = math.fsum(abs(weight) for weight in target.values())
        net = math.fsum(target.values())
        if (
            gross > self.parameters.total_gross + 1e-12
            or abs(net) > self.parameters.maximum_abs_net + 1e-12
            or any(
                abs(weight) > self.parameters.maximum_symbol_weight + 1e-12
                for weight in target.values()
            )
        ):
            self._vintages.clear()
            target = {}
        self._last_decision_time = decision_time
        self._last_target = dict(target)
        return dict(target)


def build_strategy() -> TargetStrategy:
    return WeeklyLongFormationReversal()
