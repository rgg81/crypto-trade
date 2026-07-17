"""Team 10 residual trend/reversion regime ensemble.

The strategy consumes only past-closed 8-hour candles supplied through the neutral tournament
protocol.  Amendment 0006 is the upstream universe authority; this module intentionally does not
try to infer asset type from a ticker.  Funding is not a feature of this family.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

_ENSEMBLE_MODES = frozenset({"adaptive", "equal_blend", "reversion_only", "trend_only"})


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    """Complete material configuration for the preregistered family."""

    interval_hours: int = 8
    fast_horizon_bars: int = 6
    medium_horizon_bars: int = 18
    slow_horizon_bars: int = 63
    regime_horizon_bars: int = 63
    efficiency_lower: float = 0.12
    efficiency_upper: float = 0.32
    trend_medium_weight: float = 0.40
    minimum_cross_section: int = 12
    minimum_scored_symbols: int = 16
    selection_count_per_side: int = 5
    gross_exposure: float = 0.80
    maximum_symbol_weight: float = 0.10
    robust_z_clip: float = 4.0
    minimum_score_spread: float = 0.50
    residualize: bool = True
    ensemble_mode: str = "adaptive"

    def validate(self) -> None:
        if self.interval_hours <= 0:
            raise ValueError("interval_hours must be positive")
        horizons = (
            self.fast_horizon_bars,
            self.medium_horizon_bars,
            self.slow_horizon_bars,
            self.regime_horizon_bars,
        )
        if any(type(value) is not int or value < 2 for value in horizons):
            raise ValueError("all horizons must be integers of at least two bars")
        if not self.fast_horizon_bars < self.medium_horizon_bars < self.slow_horizon_bars:
            raise ValueError("signal horizons must be strictly increasing")
        if not 0.0 <= self.efficiency_lower < self.efficiency_upper <= 1.0:
            raise ValueError("efficiency thresholds must be ordered inside [0, 1]")
        if not 0.0 <= self.trend_medium_weight <= 1.0:
            raise ValueError("trend_medium_weight must be inside [0, 1]")
        if type(self.selection_count_per_side) is not int or self.selection_count_per_side < 1:
            raise ValueError("selection_count_per_side must be a positive integer")
        if type(self.minimum_cross_section) is not int or self.minimum_cross_section < 3:
            raise ValueError("minimum_cross_section must be an integer of at least three")
        if type(self.minimum_scored_symbols) is not int:
            raise ValueError("minimum_scored_symbols must be an integer")
        if self.minimum_scored_symbols < 2 * self.selection_count_per_side:
            raise ValueError("minimum_scored_symbols cannot permit overlapping sleeves")
        if not 0.0 < self.gross_exposure <= 1.0:
            raise ValueError("gross_exposure must be inside (0, 1]")
        if not 0.0 < self.maximum_symbol_weight <= 0.10:
            raise ValueError("maximum_symbol_weight must be inside (0, 0.10]")
        requested_weight = self.gross_exposure / (2 * self.selection_count_per_side)
        if requested_weight > self.maximum_symbol_weight:
            raise ValueError("selection count cannot implement the requested gross exposure")
        if not math.isfinite(self.robust_z_clip) or self.robust_z_clip <= 0.0:
            raise ValueError("robust_z_clip must be positive and finite")
        if not math.isfinite(self.minimum_score_spread) or self.minimum_score_spread < 0.0:
            raise ValueError("minimum_score_spread must be finite and nonnegative")
        if type(self.residualize) is not bool:
            raise ValueError("residualize must be Boolean")
        if self.ensemble_mode not in _ENSEMBLE_MODES:
            raise ValueError(f"ensemble_mode must be one of {sorted(_ENSEMBLE_MODES)}")


class ResidualTrendReversionEnsemble:
    """Deterministic, balanced long/short strategy using only causal close returns."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()
        self.config.validate()

    def target_weights(self, context: Any, *, seed: int) -> Mapping[str, float]:
        """Return an explicit balanced rebalance or an explicit request for a flat book."""
        if type(seed) is not int or seed < 0:
            raise ValueError("seed must be a nonnegative integer")
        decision_time = _utc_timestamp(context.decision_time)
        eligible = tuple(context.eligible_symbols)
        if any(type(symbol) is not str or not symbol for symbol in eligible):
            raise ValueError("eligible symbols must be nonempty strings")
        if len(eligible) != len(set(eligible)):
            raise ValueError("eligible symbols must be unique")

        interval = pd.Timedelta(hours=self.config.interval_hours)
        returns_by_symbol: dict[str, pd.Series] = {}
        for symbol in sorted(eligible):
            raw_frame = context.bars.get(symbol)
            if raw_frame is None:
                continue
            returns = _closed_log_returns(raw_frame, decision_time, interval)
            if returns.empty or returns.index[-1] != decision_time:
                continue
            returns_by_symbol[symbol] = returns

        if len(returns_by_symbol) < self.config.minimum_cross_section:
            return {}
        return_matrix = pd.concat(returns_by_symbol, axis=1).sort_index()
        return_matrix.columns = list(returns_by_symbol)
        breadth = return_matrix.notna().sum(axis=1)
        market = return_matrix.median(axis=1, skipna=True).where(
            breadth >= self.config.minimum_cross_section
        )
        residuals = return_matrix.sub(market, axis=0) if self.config.residualize else return_matrix

        required_signal_bars = self.config.slow_horizon_bars
        expected_signal_index = pd.date_range(
            end=decision_time,
            periods=required_signal_bars,
            freq=interval,
        )
        factor_rows: dict[str, tuple[float, float, float]] = {}
        for symbol in sorted(returns_by_symbol):
            window = residuals[symbol].reindex(expected_signal_index)
            if window.isna().any():
                continue
            values = window.to_numpy(dtype=float)
            factor_rows[symbol] = (
                _studentized_sum(values[-self.config.fast_horizon_bars :]),
                _studentized_sum(values[-self.config.medium_horizon_bars :]),
                _studentized_sum(values),
            )
        if len(factor_rows) < self.config.minimum_scored_symbols:
            return {}

        factors = pd.DataFrame.from_dict(
            factor_rows,
            orient="index",
            columns=("fast", "medium", "slow"),
        ).sort_index()
        fast_z = _robust_cross_sectional_z(factors["fast"], self.config.robust_z_clip)
        medium_z = _robust_cross_sectional_z(factors["medium"], self.config.robust_z_clip)
        slow_z = _robust_cross_sectional_z(factors["slow"], self.config.robust_z_clip)
        trend_score = (
            self.config.trend_medium_weight * medium_z
            + (1.0 - self.config.trend_medium_weight) * slow_z
        )
        reversion_score = -fast_z

        trend_share = self._trend_share(market, decision_time, interval)
        if trend_share is None:
            return {}
        if self.config.ensemble_mode == "trend_only":
            trend_share = 1.0
        elif self.config.ensemble_mode == "reversion_only":
            trend_share = 0.0
        elif self.config.ensemble_mode == "equal_blend":
            trend_share = 0.5
        transformed_scores = trend_share * trend_score + (1.0 - trend_share) * reversion_score
        if not np.isfinite(transformed_scores.to_numpy(dtype=float)).all():
            raise ValueError("non-finite ensemble score")
        scores = {
            str(symbol): float(transformed_scores[symbol])
            for symbol in sorted(transformed_scores.index)
        }
        captured_scores = score_boundary(scores)
        if captured_scores is not scores:
            raise TypeError("score_boundary must return its exact input object")
        _validate_boundary_scores(captured_scores, expected_symbols=frozenset(factor_rows))
        score_values = tuple(captured_scores.values())
        if max(score_values) - min(score_values) < self.config.minimum_score_spread:
            return {}

        count = self.config.selection_count_per_side
        long_symbols = sorted(
            captured_scores,
            key=lambda symbol: (-captured_scores[symbol], symbol),
        )[:count]
        short_symbols = sorted(
            captured_scores,
            key=lambda symbol: (captured_scores[symbol], symbol),
        )[:count]
        if set(long_symbols) & set(short_symbols):
            raise ValueError("long and short sleeves overlap")
        symbol_weight = self.config.gross_exposure / (2.0 * count)
        weights = {symbol: symbol_weight for symbol in long_symbols}
        weights.update({symbol: -symbol_weight for symbol in short_symbols})
        _validate_output(weights, eligible, self.config)
        return weights

    def _trend_share(
        self,
        market: pd.Series,
        decision_time: pd.Timestamp,
        interval: pd.Timedelta,
    ) -> float | None:
        expected = pd.date_range(
            end=decision_time,
            periods=self.config.regime_horizon_bars,
            freq=interval,
        )
        window = market.reindex(expected)
        if window.isna().any():
            return None
        values = window.to_numpy(dtype=float)
        travelled = float(np.abs(values).sum())
        if travelled <= np.finfo(float).eps:
            return 0.0
        efficiency = abs(float(values.sum())) / travelled
        share = (efficiency - self.config.efficiency_lower) / (
            self.config.efficiency_upper - self.config.efficiency_lower
        )
        return float(np.clip(share, 0.0, 1.0))


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        raise ValueError("decision_time must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _closed_log_returns(
    frame: pd.DataFrame,
    decision_time: pd.Timestamp,
    interval: pd.Timedelta,
) -> pd.Series:
    required = {"open_time", "close"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"bar frame missing columns: {sorted(missing)}")
    open_times = pd.to_datetime(frame["open_time"], utc=True, errors="raise")
    closed_mask = open_times + interval <= decision_time
    if not bool(closed_mask.any()):
        return pd.Series(dtype=float)
    closed = pd.DataFrame(
        {
            "close_time": open_times.loc[closed_mask] + interval,
            "close": pd.to_numeric(frame.loc[closed_mask, "close"], errors="raise"),
        }
    )
    if closed["close_time"].duplicated().any():
        raise ValueError("duplicate closed-bar timestamp")
    close_values = closed["close"].to_numpy(dtype=float)
    if not np.isfinite(close_values).all() or (close_values <= 0.0).any():
        raise ValueError("past close prices must be positive and finite")
    closed = closed.sort_values("close_time")
    prices = pd.Series(
        closed["close"].to_numpy(dtype=float),
        index=pd.DatetimeIndex(closed["close_time"]),
        dtype=float,
    )
    returns = np.log(prices).diff()
    adjacency = prices.index.to_series().diff().eq(interval).to_numpy()
    returns.iloc[~adjacency] = np.nan
    return returns


def _studentized_sum(values: np.ndarray) -> float:
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("signal window must be a finite one-dimensional array")
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


def _validate_output(
    weights: Mapping[str, float],
    eligible: tuple[str, ...],
    config: StrategyConfig,
) -> None:
    if set(weights) - set(eligible):
        raise ValueError("target contains a symbol outside the eligible universe")
    values = np.asarray(list(weights.values()), dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("target contains a non-finite weight")
    if (np.abs(values) > config.maximum_symbol_weight + 1e-12).any():
        raise ValueError("target exceeds the per-symbol cap")
    if float(np.abs(values).sum()) > config.gross_exposure + 1e-12:
        raise ValueError("target exceeds configured gross exposure")
    if abs(float(values.sum())) > 1e-12:
        raise ValueError("target sleeves must be dollar balanced")


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
    values = np.asarray(tuple(scores.values()), dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("score_boundary returned a non-finite score")


def build_strategy() -> ResidualTrendReversionEnsemble:
    """Canonical tournament entrypoint."""
    return ResidualTrendReversionEnsemble()
