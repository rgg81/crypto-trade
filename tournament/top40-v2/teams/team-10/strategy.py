"""Team 10 pivot-01: defensive volume-anchor convergence.

The strategy is a slow, market-neutral relative-value mechanism.  It trades moderate deviations
from a causal volume-weighted price anchor only inside a crash-quarantined cohort, changes sleeves
at most once per 24 hours, and retains incumbents inside a rank buffer.  Amendment 0006 supplies
the eligible pure-crypto universe; ticker text is never an eligibility feature.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

_SCHEDULE_ANCHOR = pd.Timestamp("1970-01-01T00:00:00Z")


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    """Complete material configuration for defensive anchor convergence."""

    interval_hours: int = 8
    decision_interval_hours: int = 24
    anchor_horizon_bars: int = 63
    volatility_horizon_bars: int = 42
    tail_horizon_bars: int = 21
    confirmation_horizon_bars: int = 9
    minimum_cross_section: int = 14
    minimum_scored_symbols: int = 12
    selection_count_per_side: int = 4
    retention_rank_buffer: int = 2
    gross_exposure: float = 0.20
    maximum_symbol_weight: float = 0.03
    maximum_abs_one_bar_return: float = 0.20
    maximum_abs_tail_return: float = 0.35
    maximum_window_drawdown: float = 0.45
    maximum_log_price_range: float = 0.70
    maximum_annualized_volatility: float = 1.50
    maximum_abs_anchor_dislocation: float = 0.15
    minimum_positive_volume_fraction: float = 0.80
    confirmation_weight: float = 0.25
    volume_weighted_anchor: bool = True
    tail_quarantine_enabled: bool = True
    robust_z_clip: float = 4.0
    minimum_score_spread: float = 0.75
    minimum_selected_abs_score: float = 0.25

    def validate(self) -> None:
        integer_fields = (
            self.interval_hours,
            self.decision_interval_hours,
            self.anchor_horizon_bars,
            self.volatility_horizon_bars,
            self.tail_horizon_bars,
            self.confirmation_horizon_bars,
            self.minimum_cross_section,
            self.minimum_scored_symbols,
            self.selection_count_per_side,
        )
        if any(type(value) is not int or value <= 0 for value in integer_fields):
            raise ValueError("integer configuration fields must be positive")
        if self.decision_interval_hours % self.interval_hours:
            raise ValueError("decision interval must be a multiple of the bar interval")
        if not (
            self.confirmation_horizon_bars
            < self.tail_horizon_bars
            < self.volatility_horizon_bars
            < self.anchor_horizon_bars
        ):
            raise ValueError("feature horizons must be strictly increasing")
        if self.minimum_scored_symbols < 2 * self.selection_count_per_side:
            raise ValueError("minimum scored symbols cannot permit overlapping sleeves")
        if type(self.retention_rank_buffer) is not int or self.retention_rank_buffer < 0:
            raise ValueError("retention rank buffer must be a nonnegative integer")
        if not 0.0 < self.gross_exposure <= 1.0:
            raise ValueError("gross exposure must be inside (0, 1]")
        if not 0.0 < self.maximum_symbol_weight <= 0.10:
            raise ValueError("maximum symbol weight must be inside (0, 0.10]")
        requested_weight = self.gross_exposure / (2 * self.selection_count_per_side)
        if requested_weight > self.maximum_symbol_weight:
            raise ValueError("selection count cannot implement the requested gross exposure")
        unit_interval_fields = (
            self.maximum_abs_one_bar_return,
            self.maximum_abs_tail_return,
            self.maximum_window_drawdown,
            self.maximum_abs_anchor_dislocation,
            self.minimum_positive_volume_fraction,
        )
        if any(not 0.0 < value < 1.0 for value in unit_interval_fields):
            raise ValueError(
                "return, drawdown, dislocation, and volume thresholds must be in (0, 1)"
            )
        positive_fields = (
            self.maximum_log_price_range,
            self.maximum_annualized_volatility,
            self.robust_z_clip,
            self.minimum_score_spread,
            self.minimum_selected_abs_score,
        )
        if any(not math.isfinite(value) or value <= 0.0 for value in positive_fields):
            raise ValueError("scale and score thresholds must be positive and finite")
        if not math.isfinite(self.confirmation_weight) or self.confirmation_weight < 0.0:
            raise ValueError("confirmation weight must be finite and nonnegative")
        if (
            type(self.volume_weighted_anchor) is not bool
            or type(self.tail_quarantine_enabled) is not bool
        ):
            raise ValueError("anchor and quarantine switches must be Boolean")


class DefensiveAnchorConvergence:
    """Stateful daily sleeve selector with causal tail quarantine and rank retention."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()
        self.config.validate()
        self._long_symbols: tuple[str, ...] = ()
        self._short_symbols: tuple[str, ...] = ()

    def target_weights(self, context: Any, *, seed: int) -> Mapping[str, float] | None:
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        decision_time = _utc_timestamp(context.decision_time)
        if not _is_scheduled(decision_time, self.config.decision_interval_hours):
            return None
        eligible = tuple(context.eligible_symbols)
        if any(type(symbol) is not str or not symbol for symbol in eligible):
            raise ValueError("eligible symbols must be nonempty strings")
        if len(eligible) != len(set(eligible)):
            raise ValueError("eligible symbols must be unique")

        interval = pd.Timedelta(hours=self.config.interval_hours)
        histories: dict[str, pd.DataFrame] = {}
        returns_by_symbol: dict[str, pd.Series] = {}
        for symbol in sorted(eligible):
            raw_frame = context.bars.get(symbol)
            if raw_frame is None:
                continue
            history = _closed_history(raw_frame, decision_time, interval)
            if history.empty or history.index[-1] != decision_time:
                continue
            histories[symbol] = history
            returns_by_symbol[symbol] = _adjacent_log_returns(history["close"], interval)
        if len(returns_by_symbol) < self.config.minimum_cross_section:
            return self._capture_empty_and_flat()

        return_matrix = pd.concat(returns_by_symbol, axis=1).sort_index()
        return_matrix.columns = list(returns_by_symbol)
        breadth = return_matrix.notna().sum(axis=1)
        market_return = return_matrix.median(axis=1, skipna=True).where(
            breadth >= self.config.minimum_cross_section
        )

        expected_close_times = pd.date_range(
            end=decision_time,
            periods=self.config.anchor_horizon_bars + 1,
            freq=interval,
        )
        expected_return_times = expected_close_times[1:]
        raw_features: dict[str, tuple[float, float]] = {}
        for symbol in sorted(histories):
            window = histories[symbol].reindex(expected_close_times)
            if window.isna().any().any():
                continue
            log_returns = returns_by_symbol[symbol].reindex(expected_return_times)
            common = market_return.reindex(expected_return_times)
            if log_returns.isna().any() or common.isna().any():
                continue
            prices = window["close"].to_numpy(dtype=float)
            quote_volume = window["quote_volume"].to_numpy(dtype=float)
            raw_return_values = log_returns.to_numpy(dtype=float)
            if self.config.tail_quarantine_enabled and not self._passes_tail_quarantine(
                prices, quote_volume, raw_return_values
            ):
                continue
            residual_returns = raw_return_values - common.to_numpy(dtype=float)
            anchor_prices = prices[1:]
            anchor_volume = (
                quote_volume[1:]
                if self.config.volume_weighted_anchor
                else np.ones_like(quote_volume[1:])
            )
            volume_sum = float(anchor_volume.sum())
            if volume_sum <= np.finfo(float).eps:
                continue
            log_anchor = float(np.dot(np.log(anchor_prices), anchor_volume) / volume_sum)
            anchor_distance = float(np.log(anchor_prices[-1]) - log_anchor)
            confirmation = _studentized_sum(
                residual_returns[-self.config.confirmation_horizon_bars :]
            )
            raw_features[symbol] = (anchor_distance, confirmation)
        if len(raw_features) < self.config.minimum_scored_symbols:
            return self._capture_empty_and_flat()

        features = pd.DataFrame.from_dict(
            raw_features,
            orient="index",
            columns=("anchor_distance", "confirmation"),
        ).sort_index()
        residual_distance = features["anchor_distance"] - float(
            features["anchor_distance"].median()
        )
        moderate = residual_distance.abs() <= self.config.maximum_abs_anchor_dislocation
        features = features.loc[moderate]
        residual_distance = residual_distance.loc[moderate]
        if len(features) < self.config.minimum_scored_symbols:
            return self._capture_empty_and_flat()

        distance_z = _robust_cross_sectional_z(
            residual_distance,
            self.config.robust_z_clip,
        )
        confirmation_z = _robust_cross_sectional_z(
            features["confirmation"],
            self.config.robust_z_clip,
        )
        transformed_scores = -distance_z + self.config.confirmation_weight * confirmation_z
        if not np.isfinite(transformed_scores.to_numpy(dtype=float)).all():
            raise ValueError("non-finite anchor-convergence score")
        scores = {
            str(symbol): float(transformed_scores[symbol])
            for symbol in sorted(transformed_scores.index)
        }
        captured_scores = _capture_scores(scores, expected_symbols=frozenset(features.index))
        if max(captured_scores.values()) - min(captured_scores.values()) < (
            self.config.minimum_score_spread
        ):
            return self._flat()

        long_symbols = _select_with_retention(
            captured_scores,
            previous=self._long_symbols,
            count=self.config.selection_count_per_side,
            buffer=self.config.retention_rank_buffer,
            descending=True,
            minimum_abs_score=self.config.minimum_selected_abs_score,
        )
        short_symbols = _select_with_retention(
            captured_scores,
            previous=self._short_symbols,
            count=self.config.selection_count_per_side,
            buffer=self.config.retention_rank_buffer,
            descending=False,
            minimum_abs_score=self.config.minimum_selected_abs_score,
        )
        if len(long_symbols) != self.config.selection_count_per_side or len(short_symbols) != (
            self.config.selection_count_per_side
        ):
            return self._flat()
        if set(long_symbols) & set(short_symbols):
            raise ValueError("long and short sleeves overlap")
        if long_symbols == self._long_symbols and short_symbols == self._short_symbols:
            return None

        self._long_symbols = long_symbols
        self._short_symbols = short_symbols
        symbol_weight = self.config.gross_exposure / (2 * self.config.selection_count_per_side)
        weights = {symbol: symbol_weight for symbol in long_symbols}
        weights.update({symbol: -symbol_weight for symbol in short_symbols})
        _validate_output(weights, eligible, self.config)
        return weights

    def _passes_tail_quarantine(
        self,
        prices: np.ndarray,
        quote_volume: np.ndarray,
        log_returns: np.ndarray,
    ) -> bool:
        if not (
            np.isfinite(prices).all()
            and np.isfinite(quote_volume).all()
            and np.isfinite(log_returns).all()
        ):
            return False
        if (prices <= 0.0).any() or (quote_volume < 0.0).any():
            return False
        positive_volume_fraction = float(np.mean(quote_volume > 0.0))
        if positive_volume_fraction < self.config.minimum_positive_volume_fraction:
            return False
        simple_returns = np.expm1(log_returns)
        if float(np.abs(simple_returns).max()) > self.config.maximum_abs_one_bar_return:
            return False
        tail_return = abs(float(np.expm1(log_returns[-self.config.tail_horizon_bars :].sum())))
        if tail_return > self.config.maximum_abs_tail_return:
            return False
        running_peak = np.maximum.accumulate(prices)
        maximum_drawdown = float(np.max(1.0 - prices / running_peak))
        if maximum_drawdown > self.config.maximum_window_drawdown:
            return False
        log_range = float(np.log(prices.max()) - np.log(prices.min()))
        if log_range > self.config.maximum_log_price_range:
            return False
        volatility_window = log_returns[-self.config.volatility_horizon_bars :]
        annualized_volatility = float(volatility_window.std(ddof=0) * math.sqrt(3 * 365))
        return annualized_volatility <= self.config.maximum_annualized_volatility

    def _flat(self) -> dict[str, float]:
        self._long_symbols = ()
        self._short_symbols = ()
        return {}

    def _capture_empty_and_flat(self) -> dict[str, float]:
        scores: dict[str, float] = {}
        _capture_scores(scores, expected_symbols=frozenset())
        return self._flat()


def _is_scheduled(decision_time: pd.Timestamp, decision_interval_hours: int) -> bool:
    elapsed = decision_time - _SCHEDULE_ANCHOR
    return elapsed >= pd.Timedelta(0) and elapsed % pd.Timedelta(hours=decision_interval_hours) == (
        pd.Timedelta(0)
    )


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("decision_time must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _closed_history(
    frame: pd.DataFrame,
    decision_time: pd.Timestamp,
    interval: pd.Timedelta,
) -> pd.DataFrame:
    required = {"open_time", "close", "quote_volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"bar frame missing columns: {sorted(missing)}")
    open_times = pd.to_datetime(frame["open_time"], utc=True, errors="raise")
    closed_mask = open_times + interval <= decision_time
    if not bool(closed_mask.any()):
        return pd.DataFrame(columns=("close", "quote_volume"), dtype=float)
    closed = pd.DataFrame(
        {
            "close_time": open_times.loc[closed_mask] + interval,
            "close": pd.to_numeric(frame.loc[closed_mask, "close"], errors="raise"),
            "quote_volume": pd.to_numeric(frame.loc[closed_mask, "quote_volume"], errors="raise"),
        }
    )
    if closed["close_time"].duplicated().any():
        raise ValueError("duplicate closed-bar timestamp")
    closed = closed.sort_values("close_time").set_index("close_time")
    values = closed[["close", "quote_volume"]].to_numpy(dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("past close and quote volume must be finite")
    if (closed["close"] <= 0.0).any() or (closed["quote_volume"] < 0.0).any():
        raise ValueError("past close must be positive and quote volume nonnegative")
    return closed


def _adjacent_log_returns(prices: pd.Series, interval: pd.Timedelta) -> pd.Series:
    returns = np.log(prices).diff()
    adjacency = prices.index.to_series().diff().eq(interval).to_numpy()
    returns.iloc[~adjacency] = np.nan
    return returns


def _studentized_sum(values: np.ndarray) -> float:
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("confirmation window must be finite and one dimensional")
    energy = float(np.sqrt(np.square(values).sum()))
    if energy <= np.finfo(float).eps:
        return 0.0
    return float(values.sum() / energy)


def _robust_cross_sectional_z(values: pd.Series, clip: float) -> pd.Series:
    median = float(values.median())
    absolute_deviation = (values - median).abs()
    scale = 1.4826 * float(absolute_deviation.median())
    if not math.isfinite(scale) or scale <= np.finfo(float).eps:
        scale = float(values.std(ddof=0))
    if not math.isfinite(scale) or scale <= np.finfo(float).eps:
        return pd.Series(0.0, index=values.index, dtype=float)
    return ((values - median) / scale).clip(lower=-clip, upper=clip)


def _select_with_retention(
    scores: dict[str, float],
    *,
    previous: tuple[str, ...],
    count: int,
    buffer: int,
    descending: bool,
    minimum_abs_score: float,
) -> tuple[str, ...]:
    if descending:
        ranked = sorted(scores, key=lambda symbol: (-scores[symbol], symbol))
        ranked = [symbol for symbol in ranked if scores[symbol] >= minimum_abs_score]
    else:
        ranked = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
        ranked = [symbol for symbol in ranked if scores[symbol] <= -minimum_abs_score]
    retention_pool = frozenset(ranked[: count + buffer])
    selected = [symbol for symbol in previous if symbol in retention_pool]
    for symbol in ranked:
        if symbol not in selected:
            selected.append(symbol)
        if len(selected) == count:
            break
    return tuple(selected)


def _validate_boundary_scores(
    scores: dict[str, float],
    *,
    expected_symbols: frozenset[str],
) -> None:
    if type(scores) is not dict:
        raise TypeError("score_boundary must return the built-in score dict")
    if frozenset(scores) != expected_symbols:
        raise ValueError("score_boundary changed the scored-symbol set")
    if any(type(symbol) is not str or not symbol for symbol in scores):
        raise ValueError("score_boundary returned an invalid symbol")
    if any(type(value) is not float for value in scores.values()):
        raise TypeError("score_boundary returned a non-built-in-float score")
    if not np.isfinite(np.asarray(tuple(scores.values()), dtype=float)).all():
        raise ValueError("score_boundary returned a non-finite score")


def _capture_scores(
    scores: dict[str, float],
    *,
    expected_symbols: frozenset[str],
) -> dict[str, float]:
    captured_scores = score_boundary(scores)
    if captured_scores is not scores:
        raise TypeError("score_boundary must return its exact input object")
    _validate_boundary_scores(captured_scores, expected_symbols=expected_symbols)
    return captured_scores


def _validate_output(
    weights: Mapping[str, float],
    eligible: tuple[str, ...],
    config: StrategyConfig,
) -> None:
    if set(weights) - set(eligible):
        raise ValueError("target contains a symbol outside the eligible universe")
    values = np.asarray(tuple(weights.values()), dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("target contains a non-finite weight")
    if (np.abs(values) > config.maximum_symbol_weight + 1e-12).any():
        raise ValueError("target exceeds the per-symbol cap")
    if float(np.abs(values).sum()) > config.gross_exposure + 1e-12:
        raise ValueError("target exceeds configured gross exposure")
    if abs(float(values.sum())) > 1e-12:
        raise ValueError("target sleeves must be dollar balanced")


def build_strategy() -> DefensiveAnchorConvergence:
    """Canonical tournament entrypoint for pivot-01."""
    return DefensiveAnchorConvergence()
