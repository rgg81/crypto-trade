"""Causal weekly three-signal regime ensemble baseline for Team 12."""

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
    lookback_return_bars: int = 252
    momentum_bars: int = 63
    reversal_bars: int = 6
    downside_bars: int = 126
    regime_lag_bars: int = 3
    btc_direction_bars: int = 180
    btc_volatility_bars: int = 90
    bull_return_threshold: float = 0.10
    bear_return_threshold: float = -0.10
    stress_annualized_volatility: float = 0.80
    minimum_valid_symbols: int = 24
    minimum_positions_per_side: int = 8
    entry_fraction_per_side: float = 0.20
    retention_fraction_per_side: float = 0.30
    bull_total_gross: float = 0.30
    bear_total_gross: float = 0.22
    chop_total_gross: float = 0.26
    stress_total_gross: float = 0.16
    maximum_symbol_weight: float = 0.025
    maximum_abs_net: float = 0.02


@dataclasses.dataclass(frozen=True)
class ComponentFeature:
    residual_momentum: float
    short_reversal: float
    downside_resilience: float


PARAMETERS = StrategyParameters()

REGIME_WEIGHTS: dict[str, tuple[float, float, float]] = {
    "bull": (0.55, 0.10, 0.35),
    "bear": (0.15, 0.30, 0.55),
    "chop": (0.25, 0.40, 0.35),
    "stress": (0.10, 0.25, 0.65),
}


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


def _close_history(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    parameters: StrategyParameters,
) -> pd.Series:
    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)
    interval = pd.Timedelta(hours=parameters.interval_hours)
    required_closes = parameters.lookback_return_bars + 1
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
    values = close.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        return pd.Series(dtype=float)
    return pd.Series(values, index=expected, dtype=float)


def _histories(
    context: DecisionContext,
    *,
    parameters: StrategyParameters,
) -> dict[str, pd.Series]:
    decision_time = _utc(context.decision_time)
    result: dict[str, pd.Series] = {}
    for symbol in sorted({str(value) for value in context.eligible_symbols}):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        close = _close_history(
            frame,
            decision_time=decision_time,
            parameters=parameters,
        )
        if not close.empty:
            result[symbol] = close
    return result


def _return_frames(
    histories: dict[str, pd.Series],
    *,
    parameters: StrategyParameters,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    returns = {
        symbol: pd.Series(
            np.diff(np.log(close.to_numpy(dtype=float))),
            index=close.index[1:],
            dtype=float,
        )
        for symbol, close in histories.items()
    }
    frame = pd.DataFrame(returns, dtype=float).dropna(axis=1, how="any")
    if len(frame.columns) < parameters.minimum_valid_symbols:
        return pd.DataFrame(), pd.DataFrame()
    residual = frame.sub(frame.median(axis=1, skipna=False), axis=0)
    return frame, residual


def _component_features(
    residual_returns: pd.DataFrame,
    *,
    parameters: StrategyParameters,
) -> dict[str, ComponentFeature]:
    if residual_returns.empty:
        return {}
    result: dict[str, ComponentFeature] = {}
    for symbol in sorted(residual_returns.columns):
        values = residual_returns[symbol].to_numpy(dtype=float)
        scale = max(float(np.std(values, ddof=1)), 1e-6)
        momentum = float(
            np.sum(values[-parameters.momentum_bars :])
            / (scale * math.sqrt(parameters.momentum_bars))
        )
        reversal = float(
            -np.sum(values[-parameters.reversal_bars :])
            / (scale * math.sqrt(parameters.reversal_bars))
        )
        downside_window = values[-parameters.downside_bars :]
        downside = float(np.mean(np.square(np.minimum(downside_window, 0.0))))
        resilience = -downside / max(scale * scale, 1e-12)
        feature = ComponentFeature(
            residual_momentum=momentum,
            short_reversal=reversal,
            downside_resilience=resilience,
        )
        if all(math.isfinite(value) for value in dataclasses.astuple(feature)):
            result[symbol] = feature
    return result


def _centered_ranks(values: dict[str, float]) -> dict[str, float]:
    ordered = sorted(values, key=lambda symbol: (values[symbol], symbol))
    if len(ordered) <= 1:
        return {symbol: 0.0 for symbol in ordered}
    return {symbol: index / (len(ordered) - 1) - 0.5 for index, symbol in enumerate(ordered)}


def _btc_regime(
    raw_returns: pd.DataFrame,
    *,
    parameters: StrategyParameters,
) -> str | None:
    if "BTCUSDT" not in raw_returns.columns:
        return None
    btc = raw_returns["BTCUSDT"].to_numpy(dtype=float)
    needed = max(parameters.btc_direction_bars, parameters.btc_volatility_bars)
    if len(btc) < needed + parameters.regime_lag_bars:
        return None
    known = btc[: -parameters.regime_lag_bars]
    direction = float(np.expm1(np.sum(known[-parameters.btc_direction_bars :])))
    annualized_volatility = float(
        np.std(known[-parameters.btc_volatility_bars :], ddof=1) * math.sqrt(3.0 * 365.0)
    )
    if not math.isfinite(direction) or not math.isfinite(annualized_volatility):
        return None
    if annualized_volatility >= parameters.stress_annualized_volatility:
        return "stress"
    if direction >= parameters.bull_return_threshold:
        return "bull"
    if direction <= parameters.bear_return_threshold:
        return "bear"
    return "chop"


def _ensemble_scores(
    features: dict[str, ComponentFeature],
    *,
    regime: str,
) -> dict[str, float]:
    if regime not in REGIME_WEIGHTS or not features:
        return {}
    momentum_rank = _centered_ranks(
        {symbol: feature.residual_momentum for symbol, feature in features.items()}
    )
    reversal_rank = _centered_ranks(
        {symbol: feature.short_reversal for symbol, feature in features.items()}
    )
    resilience_rank = _centered_ranks(
        {symbol: feature.downside_resilience for symbol, feature in features.items()}
    )
    momentum_weight, reversal_weight, resilience_weight = REGIME_WEIGHTS[regime]
    return {
        symbol: (
            momentum_weight * momentum_rank[symbol]
            + reversal_weight * reversal_rank[symbol]
            + resilience_weight * resilience_rank[symbol]
        )
        for symbol in sorted(features)
    }


def _select_sides(
    scores: dict[str, float],
    *,
    previous_longs: frozenset[str],
    previous_shorts: frozenset[str],
    parameters: StrategyParameters,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
    side_count = max(
        parameters.minimum_positions_per_side,
        int(math.floor(parameters.entry_fraction_per_side * len(ordered))),
    )
    side_count = min(side_count, len(ordered) // 2)
    outer_count = max(
        side_count,
        int(math.ceil(parameters.retention_fraction_per_side * len(ordered))),
    )
    short_outer = set(ordered[:outer_count])
    long_outer = set(ordered[-outer_count:])
    longs = [symbol for symbol in sorted(previous_longs) if symbol in long_outer]
    shorts = [symbol for symbol in sorted(previous_shorts) if symbol in short_outer]
    for symbol in reversed(ordered):
        if len(longs) >= side_count:
            break
        if symbol not in longs and symbol not in shorts:
            longs.append(symbol)
    for symbol in ordered:
        if len(shorts) >= side_count:
            break
        if symbol not in shorts and symbol not in longs:
            shorts.append(symbol)
    return tuple(sorted(longs)), tuple(sorted(shorts))


def _gross_for_regime(regime: str, parameters: StrategyParameters) -> float:
    return {
        "bull": parameters.bull_total_gross,
        "bear": parameters.bear_total_gross,
        "chop": parameters.chop_total_gross,
        "stress": parameters.stress_total_gross,
    }[regime]


def _portfolio(
    longs: tuple[str, ...],
    shorts: tuple[str, ...],
    *,
    regime: str,
    parameters: StrategyParameters,
) -> dict[str, float]:
    if (
        len(longs) < parameters.minimum_positions_per_side
        or len(shorts) < parameters.minimum_positions_per_side
    ):
        return {}
    total_gross = _gross_for_regime(regime, parameters)
    side_gross = total_gross / 2.0
    long_weight = side_gross / len(longs)
    short_weight = side_gross / len(shorts)
    if max(long_weight, short_weight) > parameters.maximum_symbol_weight + 1e-12:
        return {}
    result = {symbol: long_weight for symbol in longs}
    result.update({symbol: -short_weight for symbol in shorts})
    gross = math.fsum(abs(weight) for weight in result.values())
    net = math.fsum(result.values())
    if gross > total_gross + 1e-12 or abs(net) > parameters.maximum_abs_net + 1e-12:
        return {}
    return {symbol: result[symbol] for symbol in sorted(result)}


class WeeklyRegimeEnsemble:
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
            return None
        histories = _histories(context, parameters=self.parameters)
        raw_returns, residual_returns = _return_frames(
            histories,
            parameters=self.parameters,
        )
        regime = _btc_regime(raw_returns, parameters=self.parameters)
        features = _component_features(
            residual_returns,
            parameters=self.parameters,
        )
        if regime is None or len(features) < self.parameters.minimum_valid_symbols:
            self._longs = frozenset()
            self._shorts = frozenset()
            return {}
        scores = _ensemble_scores(features, regime=regime)
        longs, shorts = _select_sides(
            scores,
            previous_longs=self._longs,
            previous_shorts=self._shorts,
            parameters=self.parameters,
        )
        target = _portfolio(
            longs,
            shorts,
            regime=regime,
            parameters=self.parameters,
        )
        if not target:
            self._longs = frozenset()
            self._shorts = frozenset()
            return {}
        self._longs = frozenset(longs)
        self._shorts = frozenset(shorts)
        return target


def build_strategy() -> TargetStrategy:
    return WeeklyRegimeEnsemble()
