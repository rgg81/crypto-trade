"""Team 08 baseline: confirmed price unwind after an extreme settled funding event."""

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
    minimum_abs_funding_z: float = 1.25
    funding_z_cap: float = 4.0
    price_reference_bars: int = 21
    confirmation_bars: int = 3
    price_confirmation_weight: float = 0.65
    flow_confirmation_weight: float = 0.35
    holding_days: int = 3
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_valid_symbols: int = 16
    minimum_positions_per_side: int = 4
    selected_fraction_per_side: float = 0.15
    total_gross: float = 0.24
    maximum_symbol_weight: float = 0.03
    maximum_abs_net: float = 0.05


@dataclasses.dataclass(frozen=True)
class ConfirmationState:
    price_z: float
    flow_z: float


@dataclasses.dataclass(frozen=True)
class Vintage:
    decision_time: pd.Timestamp
    weights: tuple[tuple[str, float], ...]


_REFERENCE = StrategyParameters()
_BAR_FIELDS = (
    "open_time",
    "close",
    "quote_volume",
    "taker_buy_quote_volume",
)


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
        group = data.loc[data["symbol"].eq(symbol)].sort_values("funding_time")
        group = group.tail(parameters.funding_reference_events + 1)
        if len(group) < parameters.minimum_reference_events + 1:
            continue
        last_time = pd.Timestamp(group.iloc[-1]["funding_time"])
        staleness = float((decision_time - last_time) / pd.Timedelta(hours=1))
        if staleness > parameters.maximum_funding_staleness_hours:
            continue
        rates = group["funding_rate"].to_numpy(dtype=float)
        reference = rates[:-1]
        funding_z = _robust_z(float(rates[-1]), reference, parameters.funding_z_cap)
        if math.isfinite(funding_z):
            result[symbol] = funding_z
    return result


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    if not set(_BAR_FIELDS).issubset(frame.columns):
        return pd.DataFrame(columns=_BAR_FIELDS)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_bars = parameters.price_reference_bars + parameters.confirmation_bars + 1
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
    for field in _BAR_FIELDS[1:]:
        result[field] = pd.to_numeric(result[field], errors="coerce")
    finite = np.ones(len(result), dtype=bool)
    for field in _BAR_FIELDS[1:]:
        finite &= np.isfinite(result[field].to_numpy(dtype=float))
    finite &= (
        (result["close"] > 0.0)
        & (result["quote_volume"] > 0.0)
        & (result["taker_buy_quote_volume"] >= 0.0)
        & (result["taker_buy_quote_volume"] <= result["quote_volume"])
    )
    result = (
        result.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    if len(result) < required_bars:
        return pd.DataFrame(columns=_BAR_FIELDS)
    recent = result.tail(required_bars).reset_index(drop=True)
    expected = pd.date_range(end=end, periods=required_bars, freq=interval)
    if not pd.DatetimeIndex(recent["open_time"]).equals(expected):
        return pd.DataFrame(columns=_BAR_FIELDS)
    if float(recent["quote_volume"].median()) < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=_BAR_FIELDS)
    return recent


def _confirmation_states(
    context: DecisionContext,
    symbols: tuple[str, ...],
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, ConfirmationState]:
    decision_time = _utc(context.decision_time)
    histories: dict[str, pd.DataFrame] = {}
    series: dict[str, pd.Series] = {}
    for symbol in symbols:
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _complete_history(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if history.empty:
            continue
        values = np.diff(np.log(history["close"].to_numpy(dtype=float)))
        index = pd.DatetimeIndex(history["open_time"].iloc[1:])
        if np.isfinite(values).all():
            histories[symbol] = history
            series[symbol] = pd.Series(values, index=index, dtype=float)
    if len(series) < parameters.minimum_valid_symbols:
        return {}
    returns = pd.DataFrame(series).sort_index().dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return {}
    residuals = returns.sub(returns.median(axis=1, skipna=False), axis=0)
    result: dict[str, ConfirmationState] = {}
    for symbol in sorted(residuals.columns):
        residual = residuals[symbol].to_numpy(dtype=float)
        reference = residual[: parameters.price_reference_bars]
        recent = residual[-parameters.confirmation_bars :]
        reference_moves = (
            pd.Series(reference)
            .rolling(parameters.confirmation_bars)
            .sum()
            .dropna()
            .to_numpy(dtype=float)
        )
        price_z = _robust_z(float(np.sum(recent)), reference_moves, 4.0)

        rows = histories[symbol].iloc[1:].reset_index(drop=True)
        taker_pressure = (
            2.0
            * rows["taker_buy_quote_volume"].to_numpy(dtype=float)
            / rows["quote_volume"].to_numpy(dtype=float)
            - 1.0
        )
        flow_z = _robust_z(
            float(np.mean(taker_pressure[-parameters.confirmation_bars :])),
            taker_pressure[: parameters.price_reference_bars],
            4.0,
        )
        state = ConfirmationState(price_z=price_z, flow_z=flow_z)
        if all(math.isfinite(value) for value in dataclasses.astuple(state)):
            result[symbol] = state
    return result


def _scores(
    funding: dict[str, float],
    states: dict[str, ConfirmationState],
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    result: dict[str, float] = {}
    for symbol in sorted(set(funding) & set(states)):
        funding_z = funding[symbol]
        if abs(funding_z) < parameters.minimum_abs_funding_z:
            continue
        desired_direction = -math.copysign(1.0, funding_z)
        state = states[symbol]
        confirmation = (
            parameters.price_confirmation_weight * desired_direction * state.price_z
            + parameters.flow_confirmation_weight * desired_direction * state.flow_z
        )
        if confirmation <= 0.0:
            continue
        score = -funding_z * min(2.0, confirmation)
        if math.isfinite(score) and abs(score) > 1e-12:
            result[symbol] = score
    return result


def _cohort(
    scores: dict[str, float],
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    longs = sorted(
        (symbol for symbol, score in scores.items() if score > 0.0),
        key=lambda symbol: (-scores[symbol], symbol),
    )
    shorts = sorted(
        (symbol for symbol, score in scores.items() if score < 0.0),
        key=lambda symbol: (scores[symbol], symbol),
    )
    desired = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.selected_fraction_per_side * len(scores))),
    )
    side_count = min(desired, len(longs), len(shorts))
    if side_count < parameters.minimum_positions_per_side:
        return {}
    weight = parameters.total_gross / (2.0 * side_count)
    if weight > parameters.maximum_symbol_weight + 1e-12:
        return {}
    result = {symbol: weight for symbol in longs[:side_count]}
    result.update({symbol: -weight for symbol in shorts[:side_count]})
    return {symbol: result[symbol] for symbol in sorted(result)}


class FundingCrowdingReversal:
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
        funding = _funding_extremes(context, parameters=self.parameters)
        states = _confirmation_states(context, tuple(sorted(funding)), parameters=self.parameters)
        cohort = _cohort(
            _scores(funding, states, parameters=self.parameters),
            parameters=self.parameters,
        )
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
            gross > self.parameters.total_gross + 1e-12
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
    return FundingCrowdingReversal()
