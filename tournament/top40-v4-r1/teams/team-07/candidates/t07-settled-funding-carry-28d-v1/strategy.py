"""Team 07 baseline: settled funding carry with continuous price protection."""

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
    short_funding_window_days: int = 7
    long_funding_window_days: int = 28
    short_window_weight: float = 0.60
    long_window_weight: float = 0.40
    maximum_funding_staleness_hours: float = 16.0
    maximum_abs_funding_rate: float = 0.01
    minimum_event_coverage: float = 0.60
    price_return_bars: int = 9
    protection_return_bars: int = 3
    protection_strength: float = 0.40
    holding_days: int = 3
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_valid_symbols: int = 18
    minimum_positions_per_side: int = 6
    selected_fraction_per_side: float = 0.20
    target_side_gross: float = 0.14
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05
    minimum_expected_daily_carry: float = 1e-10


@dataclasses.dataclass(frozen=True)
class Vintage:
    decision_time: pd.Timestamp
    weights: tuple[tuple[str, float], ...]


_REFERENCE = StrategyParameters()
_PRICE_FIELDS = ("open_time", "close", "quote_volume")


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _scheduled(timestamp: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        timestamp.hour == parameters.decision_hour_utc
        and timestamp.minute == 0
        and timestamp.second == 0
        and timestamp.microsecond == 0
    )


def _robust_location(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    if len(finite) < 3:
        return None
    median = float(np.median(finite))
    scale = 1.4826 * float(np.median(np.abs(finite - median)))
    if not math.isfinite(scale) or scale <= 1e-15:
        result = median
    else:
        clipped = np.clip(finite, median - 4.0 * scale, median + 4.0 * scale)
        result = float(np.mean(clipped))
    return result if math.isfinite(result) else None


def _funding_features(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    funding = context.funding
    required = {"funding_time", "symbol", "funding_rate"}
    if not required.issubset(funding.columns):
        return {}
    decision_time = _utc(context.decision_time)
    start = decision_time - pd.Timedelta(days=parameters.long_funding_window_days)
    raw_times = funding["funding_time"]
    if isinstance(raw_times.dtype, pd.DatetimeTZDtype) and raw_times.is_monotonic_increasing:
        left = int(raw_times.searchsorted(start, side="left"))
        right = int(raw_times.searchsorted(decision_time, side="left"))
        candidate = funding.iloc[left:right]
        times = pd.to_datetime(candidate["funding_time"], utc=True, errors="coerce")
    else:
        all_times = pd.to_datetime(raw_times, utc=True, errors="coerce")
        mask = all_times.notna() & (all_times >= start) & (all_times < decision_time)
        candidate = funding.loc[mask]
        times = all_times.loc[mask]
    data = candidate.loc[:, ["funding_time", "symbol", "funding_rate"]].copy()
    if data.empty:
        return {}
    data["funding_time"] = times
    data["symbol"] = data["symbol"].astype(str)
    data["funding_rate"] = pd.to_numeric(data["funding_rate"], errors="coerce")
    eligible = {str(value) for value in context.eligible_symbols}
    finite = np.isfinite(data["funding_rate"].to_numpy(dtype=float))
    data = data.loc[
        finite
        & data["symbol"].isin(eligible)
        & data["funding_rate"].abs().le(parameters.maximum_abs_funding_rate)
    ]
    data = (
        data.sort_values(["symbol", "funding_time"], kind="mergesort")
        .drop_duplicates(["symbol", "funding_time"], keep="last")
        .reset_index(drop=True)
    )
    result: dict[str, float] = {}
    for symbol in sorted(eligible):
        group = data.loc[data["symbol"].eq(symbol)].sort_values("funding_time")
        if len(group) < 4:
            continue
        last_time = pd.Timestamp(group.iloc[-1]["funding_time"])
        staleness = float((decision_time - last_time) / pd.Timedelta(hours=1))
        if staleness > parameters.maximum_funding_staleness_hours:
            continue
        gaps = group["funding_time"].diff().dropna() / pd.Timedelta(hours=1)
        gap_values = gaps.to_numpy(dtype=float)
        gap_values = gap_values[np.isfinite(gap_values) & (gap_values > 0.0)]
        if len(gap_values) < 2:
            continue
        interval_hours = float(np.median(gap_values))
        if not math.isfinite(interval_hours) or not 1.0 <= interval_hours <= 24.0:
            continue
        short_start = decision_time - pd.Timedelta(days=parameters.short_funding_window_days)
        short = group.loc[group["funding_time"] >= short_start, "funding_rate"].to_numpy(
            dtype=float
        )
        long = group["funding_rate"].to_numpy(dtype=float)
        expected_short = parameters.short_funding_window_days * 24.0 / interval_hours
        expected_long = parameters.long_funding_window_days * 24.0 / interval_hours
        if (
            len(short) < parameters.minimum_event_coverage * expected_short
            or len(long) < parameters.minimum_event_coverage * expected_long
        ):
            continue
        short_location = _robust_location(short)
        long_location = _robust_location(long)
        if short_location is None or long_location is None:
            continue
        daily_rate = (24.0 / interval_hours) * (
            parameters.short_window_weight * short_location
            + parameters.long_window_weight * long_location
        )
        if math.isfinite(daily_rate):
            result[symbol] = daily_rate
    return result


def _complete_price_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    if not set(_PRICE_FIELDS).issubset(frame.columns):
        return pd.DataFrame(columns=_PRICE_FIELDS)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_bars = parameters.price_return_bars + 1
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
    result = candidate.loc[:, list(_PRICE_FIELDS)].copy()
    if result.empty:
        return pd.DataFrame(columns=_PRICE_FIELDS)
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
        return pd.DataFrame(columns=_PRICE_FIELDS)
    recent = result.tail(required_bars).reset_index(drop=True)
    expected = pd.date_range(end=end, periods=required_bars, freq=interval)
    if not pd.DatetimeIndex(recent["open_time"]).equals(expected):
        return pd.DataFrame(columns=_PRICE_FIELDS)
    if float(recent["quote_volume"].median()) < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=_PRICE_FIELDS)
    return recent


def _price_states(
    context: DecisionContext,
    symbols: tuple[str, ...],
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    series: dict[str, pd.Series] = {}
    for symbol in symbols:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _complete_price_history(
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
    residuals = returns.sub(returns.median(axis=1, skipna=False), axis=0)
    result: dict[str, float] = {}
    for symbol in sorted(residuals.columns):
        values = residuals[symbol].to_numpy(dtype=float)
        scale = max(float(np.std(values, ddof=1)), 1e-12)
        state = float(
            np.sum(values[-parameters.protection_return_bars :])
            / (scale * math.sqrt(parameters.protection_return_bars))
        )
        if math.isfinite(state):
            result[symbol] = float(np.clip(state, -4.0, 4.0))
    return result


def _cohort(
    funding: dict[str, float],
    price: dict[str, float],
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    common = sorted(set(funding) & set(price))
    if len(common) < parameters.minimum_valid_symbols:
        return {}
    side_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(common))),
    )
    side_count = min(side_count, len(common) // 2)
    if side_count < parameters.minimum_positions_per_side:
        return {}
    ordered = sorted(common, key=lambda symbol: (funding[symbol], symbol))
    longs = ordered[:side_count]
    shorts = ordered[-side_count:]
    long_multiplier = {
        symbol: 1.0 - parameters.protection_strength * math.tanh(max(0.0, -price[symbol]))
        for symbol in longs
    }
    short_multiplier = {
        symbol: 1.0 - parameters.protection_strength * math.tanh(max(0.0, price[symbol]))
        for symbol in shorts
    }
    long_total = math.fsum(long_multiplier.values())
    short_total = math.fsum(short_multiplier.values())
    if long_total <= 0.0 or short_total <= 0.0:
        return {}
    result = {
        symbol: parameters.target_side_gross * long_multiplier[symbol] / long_total
        for symbol in longs
    }
    result.update(
        {
            symbol: -parameters.target_side_gross * short_multiplier[symbol] / short_total
            for symbol in shorts
        }
    )
    expected_carry = math.fsum(-weight * funding[symbol] for symbol, weight in result.items())
    if (
        not math.isfinite(expected_carry)
        or expected_carry <= parameters.minimum_expected_daily_carry
    ):
        return {}
    if any(abs(weight) > parameters.maximum_symbol_weight + 1e-12 for weight in result.values()):
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class SettledFundingCarry:
    def __init__(self, parameters: StrategyParameters = _REFERENCE):
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
        funding = _funding_features(context, parameters=self.parameters)
        price = _price_states(context, tuple(sorted(funding)), parameters=self.parameters)
        cohort = _cohort(funding, price, parameters=self.parameters)
        cutoff = decision_time - pd.Timedelta(days=self.parameters.holding_days)
        self._vintages = [item for item in self._vintages if item.decision_time > cutoff]
        if cohort:
            self._vintages.append(Vintage(decision_time, tuple(sorted(cohort.items()))))
        eligible = {str(value) for value in context.eligible_symbols}
        totals: dict[str, float] = {}
        for vintage in self._vintages:
            for symbol, weight in vintage.weights:
                if symbol in eligible:
                    totals[symbol] = totals.get(symbol, 0.0) + weight / self.parameters.holding_days
        target = {symbol: value for symbol, value in sorted(totals.items()) if abs(value) > 1e-15}
        gross = math.fsum(abs(value) for value in target.values())
        net = math.fsum(target.values())
        if (
            gross > 2.0 * self.parameters.target_side_gross + 1e-12
            or abs(net) > self.parameters.maximum_abs_net + 1e-12
            or any(
                abs(value) > self.parameters.maximum_symbol_weight + 1e-12
                for value in target.values()
            )
        ):
            self._vintages.clear()
            target = {}
        self._last_decision_time = decision_time
        self._last_target = dict(target)
        return dict(target)


def build_strategy() -> TargetStrategy:
    return SettledFundingCarry()
