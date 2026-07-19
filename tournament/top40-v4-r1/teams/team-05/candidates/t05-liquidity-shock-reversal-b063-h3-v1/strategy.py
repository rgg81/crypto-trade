"""Team 05 baseline: fixed-sign reversal after a confirmed liquidity shock."""

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
    reference_bars: int = 63
    shock_bars: int = 3
    pretrend_bars: int = 21
    holding_days: int = 3
    minimum_median_quote_volume: float = 1_000_000.0
    minimum_valid_symbols: int = 20
    minimum_positions_per_side: int = 6
    selected_fraction_per_side: float = 0.20
    total_gross: float = 0.30
    maximum_symbol_weight: float = 0.025
    maximum_abs_net: float = 0.05
    z_score_cap: float = 4.0


@dataclasses.dataclass(frozen=True)
class Vintage:
    decision_time: pd.Timestamp
    weights: tuple[tuple[str, float], ...]


_REFERENCE = StrategyParameters()
_FIELDS = (
    "open_time",
    "close",
    "quote_volume",
    "trade_count",
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


def _complete_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    if not set(_FIELDS).issubset(frame.columns):
        return pd.DataFrame(columns=_FIELDS)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_bars = parameters.reference_bars + parameters.shock_bars + 1
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
    result = candidate.loc[:, list(_FIELDS)].copy()
    if result.empty:
        return pd.DataFrame(columns=_FIELDS)
    result["open_time"] = times
    for field in _FIELDS[1:]:
        result[field] = pd.to_numeric(result[field], errors="coerce")
    finite = np.ones(len(result), dtype=bool)
    for field in _FIELDS[1:]:
        finite &= np.isfinite(result[field].to_numpy(dtype=float))
    finite &= (
        (result["close"] > 0.0)
        & (result["quote_volume"] > 0.0)
        & (result["trade_count"] > 0.0)
        & (result["taker_buy_quote_volume"] >= 0.0)
        & (result["taker_buy_quote_volume"] <= result["quote_volume"])
    )
    result = (
        result.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
    )
    if len(result) < required_bars:
        return pd.DataFrame(columns=_FIELDS)
    recent = result.tail(required_bars).reset_index(drop=True)
    expected = pd.date_range(end=end, periods=required_bars, freq=interval)
    if not pd.DatetimeIndex(recent["open_time"]).equals(expected):
        return pd.DataFrame(columns=_FIELDS)
    if float(recent["quote_volume"].median()) < parameters.minimum_median_quote_volume:
        return pd.DataFrame(columns=_FIELDS)
    return recent


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


def _scores(
    context: DecisionContext,
    *,
    parameters: StrategyParameters = _REFERENCE,
) -> dict[str, float]:
    decision_time = _utc(context.decision_time)
    histories: dict[str, pd.DataFrame] = {}
    return_series: dict[str, pd.Series] = {}
    for symbol in sorted({str(value) for value in context.eligible_symbols}):
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
            return_series[symbol] = pd.Series(values, index=index, dtype=float)
    if len(return_series) < parameters.minimum_valid_symbols:
        return {}
    returns = pd.DataFrame(return_series).sort_index().dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return {}
    residuals = returns.sub(returns.median(axis=1, skipna=False), axis=0)
    result: dict[str, float] = {}
    for symbol in sorted(residuals.columns):
        residual = residuals[symbol].to_numpy(dtype=float)
        reference = residual[: parameters.reference_bars]
        recent = residual[-parameters.shock_bars :]
        reference_moves = (
            pd.Series(reference).rolling(parameters.shock_bars).sum().dropna().to_numpy(dtype=float)
        )
        recent_move = float(np.sum(recent))
        move_z = _robust_z(recent_move, reference_moves, parameters.z_score_cap)
        if abs(move_z) <= 1e-12:
            continue

        rows = histories[symbol].iloc[1:].reset_index(drop=True)
        baseline = rows.iloc[: parameters.reference_bars]
        shock = rows.iloc[-parameters.shock_bars :]
        volume_z = _robust_z(
            float(np.log(shock["quote_volume"].mean())),
            np.log(baseline["quote_volume"].to_numpy(dtype=float)),
            parameters.z_score_cap,
        )
        trade_z = _robust_z(
            float(np.log(shock["trade_count"].mean())),
            np.log(baseline["trade_count"].to_numpy(dtype=float)),
            parameters.z_score_cap,
        )
        taker_pressure = float(
            np.mean(
                2.0
                * shock["taker_buy_quote_volume"].to_numpy(dtype=float)
                / shock["quote_volume"].to_numpy(dtype=float)
                - 1.0
            )
        )
        direction = math.copysign(1.0, recent_move)
        activity = min(2.0, max(0.0, 0.5 * (volume_z + trade_z)))
        flow_confirmation = min(1.0, max(0.0, 2.0 * direction * taker_pressure))
        pretrend = float(np.sum(reference[-parameters.pretrend_bars :]))
        reference_scale = max(float(np.std(reference, ddof=1)), 1e-12)
        pretrend_z = pretrend / (reference_scale * math.sqrt(parameters.pretrend_bars))
        persistence_discount = 1.0 / (1.0 + max(0.0, direction * pretrend_z))
        score = -move_z * activity * flow_confirmation * persistence_discount
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


class LiquidityShockReversal:
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
        cohort = _cohort(_scores(context, parameters=self.parameters), parameters=self.parameters)
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
    return LiquidityShockReversal()
