"""Causal shrunk UTC-weekday seasonality baseline for Team 11."""

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
    lookback_return_bars: int = 546
    minimum_target_cell_observations: int = 20
    cell_prior_observations: int = 26
    weekday_prior_weight: float = 0.45
    utc_slot_prior_weight: float = 0.35
    unconditional_prior_weight: float = 0.20
    winsor_mad_multiplier: float = 4.0
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    entry_fraction_per_side: float = 0.20
    retention_fraction_per_side: float = 0.30
    total_gross: float = 0.24
    maximum_symbol_weight: float = 0.02
    maximum_abs_net: float = 0.02


@dataclasses.dataclass(frozen=True)
class SeasonalFeature:
    shrunk_expected_return: float
    standardized_expected_return: float
    target_cell_observations: int


PARAMETERS = StrategyParameters()


def _utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_scheduled(decision_time: pd.Timestamp, parameters: StrategyParameters) -> bool:
    return bool(
        decision_time.weekday() == parameters.decision_weekday_utc
        and decision_time.hour == parameters.decision_hour_utc
        and decision_time.minute == 0
        and decision_time.second == 0
        and decision_time.microsecond == 0
    )


def _open_to_open_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series:
    if not {"open_time", "open"}.issubset(frame.columns):
        return pd.Series(dtype=float)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_opens = parameters.lookback_return_bars + 1
    expected = pd.date_range(
        end=decision_time - interval,
        periods=required_opens,
        freq=interval,
    )
    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    complete = times.notna() & ((times + interval) <= decision_time)
    data = frame.loc[complete, ["open_time", "open"]].copy()
    data["open_time"] = times.loc[complete]
    data["open"] = pd.to_numeric(data["open"], errors="coerce")
    finite = np.isfinite(data["open"].to_numpy(dtype=float)) & data["open"].gt(0.0)
    opens = (
        data.loc[finite]
        .sort_values("open_time", kind="mergesort")
        .drop_duplicates("open_time", keep="last")
        .set_index("open_time")["open"]
        .reindex(expected)
    )
    if len(opens) != required_opens or opens.isna().any():
        return pd.Series(dtype=float)
    values = opens.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        return pd.Series(dtype=float)
    return pd.Series(
        np.diff(np.log(values)),
        index=expected[:-1],
        dtype=float,
    )


def _residual_returns(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> pd.DataFrame:
    decision_time = _utc(context.decision_time)
    histories: dict[str, pd.Series] = {}
    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        history = _open_to_open_history(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if not history.empty:
            histories[symbol] = history
    if len(histories) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    returns = pd.DataFrame(histories, dtype=float).dropna(axis=1, how="any")
    if len(returns.columns) < parameters.minimum_valid_symbols:
        return pd.DataFrame()
    return returns.sub(returns.median(axis=1, skipna=False), axis=0)


def _winsorized(values: np.ndarray, multiplier: float) -> np.ndarray:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= 1e-12:
        scale = float(np.std(values))
    if not math.isfinite(scale) or scale <= 1e-12:
        return values.copy()
    return np.clip(values, median - multiplier * scale, median + multiplier * scale)


def _seasonal_features(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, SeasonalFeature]:
    residuals = _residual_returns(context, parameters=parameters)
    if residuals.empty:
        return {}
    index = pd.DatetimeIndex(residuals.index)
    target_cell = (index.weekday == parameters.decision_weekday_utc) & (
        index.hour == parameters.decision_hour_utc
    )
    target_weekday = index.weekday == parameters.decision_weekday_utc
    target_slot = index.hour == parameters.decision_hour_utc
    if int(np.count_nonzero(target_cell)) < parameters.minimum_target_cell_observations:
        return {}

    result: dict[str, SeasonalFeature] = {}
    for symbol in sorted(residuals.columns):
        raw = residuals[symbol].to_numpy(dtype=float)
        values = _winsorized(raw, parameters.winsor_mad_multiplier)
        cell_values = values[target_cell]
        weekday_values = values[target_weekday]
        slot_values = values[target_slot]
        if len(cell_values) < parameters.minimum_target_cell_observations:
            continue
        cell_mean = float(np.mean(cell_values))
        prior = (
            parameters.weekday_prior_weight * float(np.mean(weekday_values))
            + parameters.utc_slot_prior_weight * float(np.mean(slot_values))
            + parameters.unconditional_prior_weight * float(np.mean(values))
        )
        reliability = len(cell_values) / (len(cell_values) + parameters.cell_prior_observations)
        expected = reliability * cell_mean + (1.0 - reliability) * prior
        scale = max(float(np.std(values, ddof=1)), 1e-6)
        feature = SeasonalFeature(
            shrunk_expected_return=expected,
            standardized_expected_return=expected / scale,
            target_cell_observations=len(cell_values),
        )
        if all(math.isfinite(value) for value in dataclasses.astuple(feature)):
            result[symbol] = feature
    return result


def _select_sides(
    features: dict[str, SeasonalFeature],
    *,
    previous_longs: frozenset[str],
    previous_shorts: frozenset[str],
    parameters: StrategyParameters,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ordered = sorted(
        features,
        key=lambda symbol: (features[symbol].standardized_expected_return, symbol),
    )
    side_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.entry_fraction_per_side * len(ordered))),
    )
    side_count = min(side_count, len(ordered) // 2)
    outer_count = max(
        side_count,
        int(math.ceil(parameters.retention_fraction_per_side * len(ordered))),
    )
    short_outer = {
        symbol for symbol in ordered[:outer_count] if features[symbol].shrunk_expected_return < 0.0
    }
    long_outer = {
        symbol for symbol in ordered[-outer_count:] if features[symbol].shrunk_expected_return > 0.0
    }
    longs = [symbol for symbol in sorted(previous_longs) if symbol in long_outer]
    shorts = [symbol for symbol in sorted(previous_shorts) if symbol in short_outer]
    for symbol in reversed(ordered):
        if len(longs) >= side_count:
            break
        if (
            features[symbol].shrunk_expected_return > 0.0
            and symbol not in longs
            and symbol not in shorts
        ):
            longs.append(symbol)
    for symbol in ordered:
        if len(shorts) >= side_count:
            break
        if (
            features[symbol].shrunk_expected_return < 0.0
            and symbol not in shorts
            and symbol not in longs
        ):
            shorts.append(symbol)
    return tuple(sorted(longs)), tuple(sorted(shorts))


def _portfolio(
    longs: tuple[str, ...],
    shorts: tuple[str, ...],
    *,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if (
        len(longs) < parameters.minimum_positions_per_side
        or len(shorts) < parameters.minimum_positions_per_side
    ):
        return {}
    side_gross = parameters.total_gross / 2.0
    long_weight = side_gross / len(longs)
    short_weight = side_gross / len(shorts)
    if max(long_weight, short_weight) > parameters.maximum_symbol_weight + 1e-12:
        return {}
    result = {symbol: long_weight for symbol in longs}
    result.update({symbol: -short_weight for symbol in shorts})
    gross = math.fsum(abs(weight) for weight in result.values())
    net = math.fsum(result.values())
    if gross > parameters.total_gross + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class ShrunkUtcWeekdaySeasonality:
    def __init__(self, parameters: StrategyParameters = PARAMETERS):
        self.parameters = parameters
        self._longs: frozenset[str] = frozenset()
        self._shorts: frozenset[str] = frozenset()

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> dict[str, float] | None:
        del seed
        decision_time = _utc(context.decision_time)
        if not _is_scheduled(decision_time, self.parameters):
            # The forecast is for exactly the Monday 00:00-08:00 UTC cell. Explicitly target
            # cash at the next and all other boundaries rather than carrying it into unmodeled
            # calendar cells under the protocol's hold-on-None semantics.
            return {}
        features = _seasonal_features(context, parameters=self.parameters)
        if not features:
            self._longs = frozenset()
            self._shorts = frozenset()
            return {}
        longs, shorts = _select_sides(
            features,
            previous_longs=self._longs,
            previous_shorts=self._shorts,
            parameters=self.parameters,
        )
        target = _portfolio(longs, shorts, parameters=self.parameters)
        if not target:
            self._longs = frozenset()
            self._shorts = frozenset()
            return {}
        self._longs = frozenset(longs)
        self._shorts = frozenset(shorts)
        return target


def build_strategy() -> TargetStrategy:
    return ShrunkUtcWeekdaySeasonality()
