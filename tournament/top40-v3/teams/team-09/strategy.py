"""Team 09: settled-timestamp funding carry with a continuous crash overlay."""

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
    funding_window_short_days: int = 7
    funding_window_medium_days: int = 14
    funding_window_long_days: int = 28
    maximum_funding_staleness_hours: float = 12.0
    minimum_interval_hours: float = 1.0
    maximum_interval_hours: float = 24.0
    maximum_gap_multiple: float = 2.5
    minimum_event_coverage: float = 0.75
    maximum_abs_funding_rate: float = 0.01
    short_window_weight: float = 0.50
    medium_window_weight: float = 0.30
    long_window_weight: float = 0.20
    price_return_bars: int = 9
    short_weakness_three_bar_scale: float = 0.04
    short_weakness_nine_bar_scale: float = 0.08
    short_crowding_overlay_strength: float = 0.50
    long_collapse_three_bar_scale: float = 0.05
    long_collapse_nine_bar_scale: float = 0.08
    long_collapse_maximum_discount: float = 0.25
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 8
    selected_fraction_per_side: float = 0.25
    target_side_gross: float = 0.16
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05
    minimum_expected_daily_carry: float = 1e-10


@dataclasses.dataclass(frozen=True)
class FundingFeature:
    expected_rate_per_day: float
    score_pressure: float
    persistence: float
    inferred_interval_hours: float


@dataclasses.dataclass(frozen=True)
class PriceState:
    residual_three_bar: float
    residual_nine_bar: float


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


def _robust_location(values: np.ndarray) -> float | None:
    finite = values[np.isfinite(values)]
    if len(finite) == 0:
        return None
    median = float(np.median(finite))
    mad = float(np.median(np.abs(finite - median)))
    if not math.isfinite(median) or not math.isfinite(mad):
        return None
    if mad <= 1e-15:
        return median
    scale = 1.4826 * mad
    clipped = np.clip(finite, median - 4.0 * scale, median + 4.0 * scale)
    result = float(np.mean(clipped))
    return result if math.isfinite(result) else None


def _funding_features(
    funding: pd.DataFrame,
    *,
    eligible_symbols: tuple[str, ...],
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> dict[str, FundingFeature]:
    required = {"funding_time", "symbol", "funding_rate"}
    if not required.issubset(funding.columns):
        return {}
    times = pd.to_datetime(funding["funding_time"], utc=True, errors="coerce")
    symbols = funding["symbol"].astype(str)
    eligible = set(eligible_symbols)
    # Availability is strict. A funding event timestamped at the decision belongs to carried
    # position accounting and cannot enter this decision's forecast.
    available = times.notna() & (times < decision_time) & symbols.isin(eligible)
    if not bool(available.any()):
        return {}
    data = funding.loc[available, ["funding_time", "symbol", "funding_rate"]].copy()
    data["funding_time"] = times.loc[available]
    data["symbol"] = symbols.loc[available]
    data["funding_rate"] = pd.to_numeric(data["funding_rate"], errors="coerce")
    finite = np.isfinite(data["funding_rate"].to_numpy(dtype=float))
    data = data.loc[
        finite
        & data["funding_rate"].abs().le(parameters.maximum_abs_funding_rate)
        & data["funding_time"].dt.minute.eq(0)
        & data["funding_time"].dt.second.eq(0)
    ]
    data = (
        data.sort_values(["symbol", "funding_time"], kind="mergesort")
        .drop_duplicates(["symbol", "funding_time"], keep="last")
        .reset_index(drop=True)
    )

    result: dict[str, FundingFeature] = {}
    windows = (
        (parameters.funding_window_short_days, parameters.short_window_weight),
        (parameters.funding_window_medium_days, parameters.medium_window_weight),
        (parameters.funding_window_long_days, parameters.long_window_weight),
    )
    for symbol in eligible_symbols:
        group = data.loc[data["symbol"].eq(symbol)].sort_values("funding_time")
        if len(group) < 3:
            continue
        last_time = pd.Timestamp(group.iloc[-1]["funding_time"])
        staleness_hours = float((decision_time - last_time) / pd.Timedelta(hours=1))
        if staleness_hours > parameters.maximum_funding_staleness_hours:
            continue

        long_start = decision_time - pd.Timedelta(days=parameters.funding_window_long_days)
        recent = group.loc[group["funding_time"] >= long_start]
        gaps = recent["funding_time"].diff().dropna() / pd.Timedelta(hours=1)
        gap_values = gaps.to_numpy(dtype=float)
        gap_values = gap_values[np.isfinite(gap_values) & (gap_values > 0.0)]
        if len(gap_values) < 2:
            continue
        inferred_interval = float(np.median(gap_values))
        if (
            not math.isfinite(inferred_interval)
            or inferred_interval < parameters.minimum_interval_hours
            or inferred_interval > parameters.maximum_interval_hours
            or float(np.max(gap_values)) > parameters.maximum_gap_multiple * inferred_interval
        ):
            continue

        estimates: list[tuple[float, float]] = []
        complete = True
        for days, weight in windows:
            start = decision_time - pd.Timedelta(days=days)
            window = group.loc[group["funding_time"] >= start, "funding_rate"]
            expected_events = days * 24.0 / inferred_interval
            if len(window) < math.ceil(parameters.minimum_event_coverage * expected_events):
                complete = False
                break
            location = _robust_location(window.to_numpy(dtype=float))
            if location is None:
                complete = False
                break
            estimates.append((location * 24.0 / inferred_interval, weight))
        if not complete:
            continue
        expected_rate_per_day = math.fsum(value * weight for value, weight in estimates)
        if not math.isfinite(expected_rate_per_day) or abs(expected_rate_per_day) <= 1e-15:
            continue

        recent_rates = recent["funding_rate"].to_numpy(dtype=float)
        if expected_rate_per_day > 0.0:
            persistence = float(np.mean(recent_rates > 0.0))
        else:
            persistence = float(np.mean(recent_rates < 0.0))
        score_pressure = expected_rate_per_day * (0.5 + 0.5 * persistence)
        result[symbol] = FundingFeature(
            expected_rate_per_day=expected_rate_per_day,
            score_pressure=score_pressure,
            persistence=persistence,
            inferred_interval_hours=inferred_interval,
        )
    return result


def _completed_log_returns(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series:
    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    interval = pd.Timedelta(hours=parameters.interval_hours)
    complete = times.notna() & ((times + interval) <= decision_time)
    if not bool(complete.any()):
        return pd.Series(dtype=float)
    data = frame.loc[complete, ["open_time", "close"]].copy()
    data["open_time"] = times.loc[complete]
    data["close"] = pd.to_numeric(data["close"], errors="coerce")
    finite = np.isfinite(data["close"].to_numpy(dtype=float)) & (data["close"] > 0.0)
    data = (
        data.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    required_closes = parameters.price_return_bars + 1
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_closes,
        freq=interval,
    )
    if len(data) < required_closes:
        return pd.Series(dtype=float)
    closes = data.set_index("open_time")["close"].reindex(expected)
    values = closes.to_numpy(dtype=float)
    if len(values) != required_closes or not np.isfinite(values).all():
        return pd.Series(dtype=float)
    return pd.Series(np.diff(np.log(values)), index=expected[1:], dtype=float)


def _price_states(
    context: DecisionContext,
    *,
    symbols: tuple[str, ...],
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> dict[str, PriceState]:
    returns: dict[str, pd.Series] = {}
    for symbol in symbols:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        series = _completed_log_returns(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if not series.empty:
            returns[symbol] = series
    if len(returns) < parameters.minimum_valid_symbols:
        return {}
    frame = pd.DataFrame(returns, dtype=float).sort_index()
    residuals = frame.sub(frame.median(axis=1, skipna=True), axis=0)
    result: dict[str, PriceState] = {}
    for symbol in sorted(returns):
        series = residuals[symbol].dropna()
        if len(series) != parameters.price_return_bars:
            continue
        three = float(series.iloc[-3:].sum())
        nine = float(series.sum())
        if math.isfinite(three) and math.isfinite(nine):
            result[symbol] = PriceState(
                residual_three_bar=three,
                residual_nine_bar=nine,
            )
    return result


def _portfolio(
    funding: dict[str, FundingFeature],
    price: dict[str, PriceState],
    *,
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

    low_to_high = sorted(
        common,
        key=lambda symbol: (funding[symbol].score_pressure, symbol),
    )
    # Carry determines membership and sign. Price never has an all-or-nothing admission vote:
    # completed residual returns only tilt the size of positions already selected by funding.
    short_pool = [
        symbol
        for symbol in reversed(low_to_high)
        if funding[symbol].expected_rate_per_day > 0.0
    ]
    if len(short_pool) < side_count:
        return {}
    shorts = short_pool[:side_count]
    short_set = set(shorts)
    longs = [symbol for symbol in low_to_high if symbol not in short_set][:side_count]
    if len(longs) < side_count:
        return {}

    short_rates = [funding[symbol].expected_rate_per_day for symbol in shorts]
    minimum_short_rate = min(short_rates)
    maximum_short_rate = max(short_rates)
    rate_span = maximum_short_rate - minimum_short_rate

    long_multipliers: dict[str, float] = {}
    for symbol in longs:
        state = price[symbol]
        three_bar_collapse = float(
            np.clip(
                -state.residual_three_bar / parameters.long_collapse_three_bar_scale,
                0.0,
                1.0,
            )
        )
        nine_bar_collapse = float(
            np.clip(
                -state.residual_nine_bar / parameters.long_collapse_nine_bar_scale,
                0.0,
                1.0,
            )
        )
        collapse = 0.5 * (three_bar_collapse + nine_bar_collapse)
        long_multipliers[symbol] = (
            1.0 - parameters.long_collapse_maximum_discount * collapse
        )

    short_multipliers: dict[str, float] = {}
    for symbol in shorts:
        state = price[symbol]
        three_bar_weakness = float(
            np.clip(
                -state.residual_three_bar / parameters.short_weakness_three_bar_scale,
                0.0,
                1.0,
            )
        )
        nine_bar_weakness = float(
            np.clip(
                -state.residual_nine_bar / parameters.short_weakness_nine_bar_scale,
                0.0,
                1.0,
            )
        )
        weakness = 0.5 * (three_bar_weakness + nine_bar_weakness)
        if rate_span > 1e-15:
            crowding = (
                funding[symbol].expected_rate_per_day - minimum_short_rate
            ) / rate_span
        else:
            crowding = 1.0
        short_multipliers[symbol] = 1.0 + (
            parameters.short_crowding_overlay_strength * crowding * weakness
        )

    long_total = math.fsum(long_multipliers.values())
    short_total = math.fsum(short_multipliers.values())
    if long_total <= 0.0 or short_total <= 0.0:
        return {}
    result = {
        symbol: parameters.target_side_gross * long_multipliers[symbol] / long_total
        for symbol in longs
    }
    result.update(
        {
            symbol: -parameters.target_side_gross
            * short_multipliers[symbol]
            / short_total
            for symbol in shorts
        }
    )
    if max(abs(value) for value in result.values()) > (
        parameters.maximum_symbol_weight + 1e-12
    ):
        return {}
    expected_carry = math.fsum(
        -weight_value * funding[symbol].expected_rate_per_day
        for symbol, weight_value in result.items()
    )
    if (
        not math.isfinite(expected_carry)
        or expected_carry <= parameters.minimum_expected_daily_carry
    ):
        return {}
    gross = math.fsum(abs(value) for value in result.values())
    net = math.fsum(result.values())
    if gross > 0.5 + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class SettledFundingCarry:
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
        eligible = tuple(sorted({str(symbol) for symbol in context.eligible_symbols}))
        funding = _funding_features(
            context.funding,
            eligible_symbols=eligible,
            decision_time=decision_time,
            parameters=self.parameters,
        )
        if len(funding) < self.parameters.minimum_valid_symbols:
            return {}
        price = _price_states(
            context,
            symbols=tuple(sorted(funding)),
            decision_time=decision_time,
            parameters=self.parameters,
        )
        return _portfolio(funding, price, parameters=self.parameters)


def build_strategy() -> TargetStrategy:
    return SettledFundingCarry()
