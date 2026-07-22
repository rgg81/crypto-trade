"""3-day residual-trend protected settled-funding carry."""

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
    price_return_bars: int = 21
    protection_return_bars: int = 9
    protection_strength: float = 0.85
    market_days: int = 28
    market_threshold: float = 0.05
    dominant_side_fraction: float = 0.72
    holding_days: int = 7
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_valid_symbols: int = 18
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    target_total_gross: float = 0.55
    maximum_symbol_weight: float = 0.05
    maximum_abs_net: float = 0.242
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
        result = float(np.mean(np.clip(finite, median - 4.0 * scale, median + 4.0 * scale)))
    return result if math.isfinite(result) else None


def _funding_features(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
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


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    required_bars: int,
    parameters: StrategyParameters,
    require_volume: bool,
) -> pd.DataFrame:
    required = set(_PRICE_FIELDS if require_volume else _PRICE_FIELDS[:2])
    if not required.issubset(frame.columns):
        return pd.DataFrame(columns=sorted(required))
    interval = pd.Timedelta(hours=parameters.interval_hours)
    columns = list(_PRICE_FIELDS if require_volume else _PRICE_FIELDS[:2])
    bounded = frame.tail(required_bars + 3)
    times = pd.to_datetime(bounded["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    result = bounded.loc[complete, columns].copy()
    result["open_time"] = times.loc[complete]
    result["close"] = pd.to_numeric(result["close"], errors="coerce")
    finite = np.isfinite(result["close"].to_numpy(dtype=float)) & result["close"].gt(0.0)
    if require_volume:
        result["quote_volume"] = pd.to_numeric(result["quote_volume"], errors="coerce")
        finite &= np.isfinite(result["quote_volume"].to_numpy(dtype=float))
        finite &= result["quote_volume"].gt(0.0)
    result = (
        result.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .tail(required_bars)
        .reset_index(drop=True)
    )
    if len(result) != required_bars:
        return pd.DataFrame(columns=columns)
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_bars,
        freq=interval,
    )
    if not pd.DatetimeIndex(result["open_time"]).equals(expected):
        return pd.DataFrame(columns=columns)
    if require_volume and float(result["quote_volume"].median()) < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=columns)
    return result


def _price_states(
    context: DecisionContext,
    symbols: tuple[str, ...],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    series: dict[str, pd.Series] = {}
    required_bars = parameters.price_return_bars + 1
    for symbol in symbols:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _complete_history(
            frame,
            decision_time=decision_time,
            required_bars=required_bars,
            parameters=parameters,
            require_volume=True,
        )
        if history.empty:
            continue
        values = np.diff(np.log(history["close"].to_numpy(dtype=float)))
        if np.isfinite(values).all():
            series[symbol] = pd.Series(values, index=pd.DatetimeIndex(history["open_time"].iloc[1:]))
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


def _market_return(
    context: DecisionContext,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> float | None:
    frame = context.bars.get("BTCUSDT")
    if frame is None:
        return None
    bars_per_day = 24 // parameters.interval_hours
    history = _complete_history(
        frame,
        decision_time=decision_time,
        required_bars=parameters.market_days * bars_per_day + 1,
        parameters=parameters,
        require_volume=False,
    )
    if history.empty:
        return None
    closes = history["close"].to_numpy(dtype=float)
    value = float(math.log(closes[-1] / closes[0]))
    return value if math.isfinite(value) else None


def _cohort(
    funding: dict[str, float],
    price: dict[str, float],
    *,
    market_return: float | None,
    parameters: StrategyParameters,
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
    if market_return is not None and market_return > parameters.market_threshold:
        long_fraction = parameters.dominant_side_fraction
    elif market_return is not None and market_return < -parameters.market_threshold:
        long_fraction = 1.0 - parameters.dominant_side_fraction
    else:
        long_fraction = 0.5
    long_budget = parameters.target_total_gross * long_fraction
    short_budget = parameters.target_total_gross - long_budget
    long_base = long_budget / len(longs)
    short_base = short_budget / len(shorts)
    result = {
        symbol: long_base
        * (1.0 - parameters.protection_strength * math.tanh(max(0.0, -price[symbol])))
        for symbol in longs
    }
    result.update(
        {
            symbol: -short_base
            * (1.0 - parameters.protection_strength * math.tanh(max(0.0, price[symbol])))
            for symbol in shorts
        }
    )
    long_gross = math.fsum(value for value in result.values() if value > 0.0)
    short_gross = -math.fsum(value for value in result.values() if value < 0.0)
    net = long_gross - short_gross
    if net > parameters.maximum_abs_net and long_gross > 0.0:
        scale = (short_gross + parameters.maximum_abs_net) / long_gross
        result = {symbol: (value * scale if value > 0.0 else value) for symbol, value in result.items()}
    elif net < -parameters.maximum_abs_net and short_gross > 0.0:
        scale = (long_gross + parameters.maximum_abs_net) / short_gross
        result = {symbol: (value * scale if value < 0.0 else value) for symbol, value in result.items()}
    expected_carry = math.fsum(-weight * funding[symbol] for symbol, weight in result.items())
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if (
        not math.isfinite(expected_carry)
        or expected_carry <= parameters.minimum_expected_daily_carry
        or gross > parameters.target_total_gross + 1e-12
        or abs(net) > parameters.maximum_abs_net + 1e-12
        or any(abs(value) > parameters.maximum_symbol_weight + 1e-12 for value in result.values())
    ):
        return {}
    return {symbol: result[symbol] for symbol in sorted(result) if abs(result[symbol]) > 1e-15}


class MarketStateFundingCarry:
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
        eligible = {str(value) for value in context.eligible_symbols}
        cutoff = decision_time - pd.Timedelta(days=self.parameters.holding_days)
        surviving: list[Vintage] = []
        for vintage in self._vintages:
            weights = tuple((symbol, weight) for symbol, weight in vintage.weights if symbol in eligible)
            if vintage.decision_time > cutoff and weights:
                surviving.append(Vintage(vintage.decision_time, weights))
        self._vintages = surviving
        funding = _funding_features(context, parameters=self.parameters)
        price = _price_states(context, tuple(sorted(funding)), parameters=self.parameters)
        market_return = _market_return(
            context,
            decision_time=decision_time,
            parameters=self.parameters,
        )
        cohort = _cohort(
            funding,
            price,
            market_return=market_return,
            parameters=self.parameters,
        )
        if cohort:
            self._vintages.append(Vintage(decision_time, tuple(sorted(cohort.items()))))
        totals: dict[str, float] = {}
        for vintage in self._vintages:
            for symbol, weight in vintage.weights:
                totals[symbol] = totals.get(symbol, 0.0) + weight / self.parameters.holding_days
        target = {symbol: value for symbol, value in sorted(totals.items()) if abs(value) > 1e-15}
        gross = math.fsum(abs(value) for value in target.values())
        net = math.fsum(target.values())
        if (
            gross > self.parameters.target_total_gross + 1e-12
            or abs(net) > self.parameters.maximum_abs_net + 1e-12
            or any(abs(value) > self.parameters.maximum_symbol_weight + 1e-12 for value in target.values())
        ):
            self._vintages.clear()
            target = {}
        self._last_decision_time = decision_time
        self._last_target = dict(target)
        return dict(target)


def build_strategy() -> TargetStrategy:
    return MarketStateFundingCarry()
