"""Regime-conditioned mean reversion after extreme settled funding."""

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
    funding_window_days: int = 28
    funding_reference_events: int = 42
    minimum_reference_events: int = 18
    maximum_funding_staleness_hours: float = 16.0
    maximum_abs_funding_rate: float = 0.01
    unwind_minimum_abs_funding_z: float = 0.50
    chop_minimum_abs_funding_z: float = 1.25
    funding_z_cap: float = 4.0
    confirmation_bars: int = 3
    confirmation_score_scale: float = 30.0
    market_days: int = 60
    market_threshold: float = 0.10
    stress_volatility_days: int = 30
    stress_volatility_threshold: float = 0.80
    protected_short_scale: float = 0.0
    unwind_holding_days: int = 3
    chop_holding_days: int = 7
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_valid_symbols: int = 16
    minimum_positions_per_side: int = 4
    selected_fraction_per_side: float = 0.15
    total_gross: float = 0.22
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.11


@dataclasses.dataclass(frozen=True)
class Vintage:
    decision_time: pd.Timestamp
    weights: tuple[tuple[str, float], ...]


_REFERENCE = StrategyParameters()
_BAR_FIELDS = ("open_time", "close", "quote_volume")


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


def _robust_z(value: float, reference: np.ndarray, cap: float) -> float:
    finite = reference[np.isfinite(reference)]
    if not math.isfinite(value) or len(finite) < 3:
        return 0.0
    median = float(np.median(finite))
    scale = 1.4826 * float(np.median(np.abs(finite - median)))
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(finite, ddof=1))
    if not math.isfinite(scale) or scale <= 1e-12:
        return 0.0
    return float(np.clip((value - median) / scale, -cap, cap))


def _funding_extremes(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    funding = context.funding
    required = {"funding_time", "symbol", "funding_rate"}
    if not required.issubset(funding.columns):
        return {}
    decision_time = _utc(context.decision_time)
    start = decision_time - pd.Timedelta(days=parameters.funding_window_days)
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
        group = data.loc[data["symbol"].eq(symbol)].tail(
            parameters.funding_reference_events + 1
        )
        if len(group) < parameters.minimum_reference_events + 1:
            continue
        last_time = pd.Timestamp(group.iloc[-1]["funding_time"])
        staleness = float((decision_time - last_time) / pd.Timedelta(hours=1))
        if staleness > parameters.maximum_funding_staleness_hours:
            continue
        rates = group["funding_rate"].to_numpy(dtype=float)
        funding_z = _robust_z(float(rates[-1]), rates[:-1], parameters.funding_z_cap)
        if math.isfinite(funding_z):
            result[symbol] = funding_z
    return result


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    required_bars: int,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    if not set(_BAR_FIELDS).issubset(frame.columns):
        return pd.DataFrame(columns=_BAR_FIELDS)
    interval = pd.Timedelta(hours=parameters.interval_hours)
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
    result = candidate.loc[:, list(_BAR_FIELDS)].copy()
    if result.empty:
        return pd.DataFrame(columns=_BAR_FIELDS)
    result["open_time"] = times
    result["close"] = pd.to_numeric(result["close"], errors="coerce")
    result["quote_volume"] = pd.to_numeric(result["quote_volume"], errors="coerce")
    values = result[["close", "quote_volume"]].to_numpy(dtype=float)
    finite = (
        np.isfinite(values).all(axis=1)
        & result["close"].gt(0.0).to_numpy(dtype=bool)
        & result["quote_volume"].gt(0.0).to_numpy(dtype=bool)
    )
    result = (
        result.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .tail(required_bars)
        .reset_index(drop=True)
    )
    if len(result) != required_bars:
        return pd.DataFrame(columns=_BAR_FIELDS)
    expected = pd.date_range(end=end, periods=required_bars, freq=interval)
    if not pd.DatetimeIndex(result["open_time"]).equals(expected):
        return pd.DataFrame(columns=_BAR_FIELDS)
    if float(result["quote_volume"].median()) < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=_BAR_FIELDS)
    return result


def _recent_residuals(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    required_bars = parameters.confirmation_bars + 1
    series: dict[str, pd.Series] = {}
    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _complete_history(
            frame,
            decision_time=decision_time,
            required_bars=required_bars,
            parameters=parameters,
        )
        if history.empty:
            continue
        values = np.diff(np.log(history["close"].to_numpy(dtype=float)))
        if np.isfinite(values).all():
            series[symbol] = pd.Series(
                values,
                index=pd.DatetimeIndex(history["open_time"].iloc[1:]),
                dtype=float,
            )
    if len(series) < parameters.minimum_valid_symbols:
        return {}
    returns = pd.DataFrame(series).sort_index().dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return {}
    residuals = returns.sub(returns.median(axis=1, skipna=False), axis=0)
    return {
        symbol: float(residuals[symbol].sum())
        for symbol in sorted(residuals.columns)
    }


def _market_state(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> tuple[str, bool]:
    frame = context.bars.get("BTCUSDT")
    if frame is None:
        return ("chop", False)
    bars_per_day = 24 // parameters.interval_hours
    required_bars = (
        max(parameters.market_days, parameters.stress_volatility_days) * bars_per_day
        + 1
    )
    history = _complete_history(
        frame,
        decision_time=_utc(context.decision_time),
        required_bars=required_bars,
        parameters=parameters,
    )
    if history.empty:
        return ("chop", False)
    closes = history["close"].to_numpy(dtype=float)
    market_return = float(closes[-1] / closes[0] - 1.0)
    daily_closes = closes[::bars_per_day]
    required_daily_closes = parameters.stress_volatility_days + 1
    if len(daily_closes) < required_daily_closes:
        return ("chop", False)
    stress_closes = daily_closes[-required_daily_closes:]
    daily_returns = np.diff(stress_closes) / stress_closes[:-1]
    annualized_volatility = float(
        np.std(daily_returns, ddof=1) * math.sqrt(365.0)
    )
    is_stress = bool(
        math.isfinite(annualized_volatility)
        and annualized_volatility > parameters.stress_volatility_threshold
    )
    if market_return > parameters.market_threshold:
        return ("bull", is_stress)
    if market_return < -parameters.market_threshold:
        return ("bear", is_stress)
    return ("chop", is_stress)


def _scores(
    funding: dict[str, float],
    residuals: dict[str, float],
    *,
    mode: str,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for symbol in sorted(set(funding) & set(residuals)):
        funding_z = funding[symbol]
        if mode == "extreme":
            if abs(funding_z) >= parameters.chop_minimum_abs_funding_z:
                result[symbol] = -funding_z
            continue
        if abs(funding_z) < parameters.unwind_minimum_abs_funding_z:
            continue
        desired_direction = -math.copysign(1.0, funding_z)
        confirmation = desired_direction * residuals[symbol]
        if confirmation <= 0.0:
            continue
        score = -funding_z * (
            1.0
            + min(
                2.0,
                parameters.confirmation_score_scale * abs(confirmation),
            )
        )
        if math.isfinite(score):
            result[symbol] = score
    return result


def _cohort(
    scores: dict[str, float],
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    desired = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(scores))),
    )
    longs = sorted(
        (symbol for symbol, score in scores.items() if score > 0.0),
        key=lambda symbol: (-scores[symbol], symbol),
    )[:desired]
    shorts = sorted(
        (symbol for symbol, score in scores.items() if score < 0.0),
        key=lambda symbol: (scores[symbol], symbol),
    )[:desired]
    result: dict[str, float] = {}
    side_gross = parameters.total_gross / 2.0
    if len(longs) >= parameters.minimum_positions_per_side:
        weight = side_gross / len(longs)
        if weight <= parameters.maximum_symbol_weight + 1e-12:
            result.update({symbol: weight for symbol in longs})
    if len(shorts) >= parameters.minimum_positions_per_side:
        weight = side_gross / len(shorts)
        if weight <= parameters.maximum_symbol_weight + 1e-12:
            result.update({symbol: -weight for symbol in shorts})
    return {symbol: result[symbol] for symbol in sorted(result)}


def _aggregate(
    vintages: list[Vintage],
    *,
    holding_days: int,
    eligible: set[str],
) -> dict[str, float]:
    totals: dict[str, float] = {}
    for vintage in vintages:
        for symbol, weight in vintage.weights:
            if symbol in eligible:
                totals[symbol] = totals.get(symbol, 0.0) + weight / holding_days
    return {
        symbol: value
        for symbol, value in sorted(totals.items())
        if abs(value) > 1e-15
    }


class FundingCrowdingReversal:
    def __init__(self, parameters: StrategyParameters = _REFERENCE):
        self.parameters = parameters
        self._unwind_vintages: list[Vintage] = []
        self._extreme_vintages: list[Vintage] = []
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
        funding = _funding_extremes(context, parameters=self.parameters)
        residuals = _recent_residuals(context, parameters=self.parameters)
        unwind = _cohort(
            _scores(
                funding,
                residuals,
                mode="unwind",
                parameters=self.parameters,
            ),
            parameters=self.parameters,
        )
        extreme = _cohort(
            _scores(
                funding,
                residuals,
                mode="extreme",
                parameters=self.parameters,
            ),
            parameters=self.parameters,
        )
        unwind_cutoff = decision_time - pd.Timedelta(
            days=self.parameters.unwind_holding_days
        )
        extreme_cutoff = decision_time - pd.Timedelta(
            days=self.parameters.chop_holding_days
        )
        self._unwind_vintages = [
            item for item in self._unwind_vintages if item.decision_time > unwind_cutoff
        ]
        self._extreme_vintages = [
            item for item in self._extreme_vintages if item.decision_time > extreme_cutoff
        ]
        if unwind:
            self._unwind_vintages.append(
                Vintage(decision_time, tuple(sorted(unwind.items())))
            )
        if extreme:
            self._extreme_vintages.append(
                Vintage(decision_time, tuple(sorted(extreme.items())))
            )
        eligible = {str(value) for value in context.eligible_symbols}
        state, is_stress = _market_state(context, parameters=self.parameters)
        if state == "chop":
            target = _aggregate(
                self._extreme_vintages,
                holding_days=self.parameters.chop_holding_days,
                eligible=eligible,
            )
        else:
            target = _aggregate(
                self._unwind_vintages,
                holding_days=self.parameters.unwind_holding_days,
                eligible=eligible,
            )
        if state == "bull" or is_stress:
            target = {
                symbol: weight * self.parameters.protected_short_scale
                if weight < 0.0
                else weight
                for symbol, weight in target.items()
            }
            target = {
                symbol: weight
                for symbol, weight in target.items()
                if abs(weight) > 1e-15
            }
        gross = math.fsum(abs(value) for value in target.values())
        net = math.fsum(target.values())
        if (
            gross > self.parameters.total_gross + 1e-12
            or abs(net) > self.parameters.maximum_abs_net + 1e-12
            or any(
                abs(value) > self.parameters.maximum_symbol_weight + 1e-12
                for value in target.values()
            )
        ):
            target = {}
        self._last_decision_time = decision_time
        self._last_target = dict(target)
        return dict(target)


def build_strategy() -> TargetStrategy:
    return FundingCrowdingReversal()
