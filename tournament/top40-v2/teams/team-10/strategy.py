"""Team 10 final pivot-02: funding-pressure transfer and unwind.

The strategy ranks the organizer-authorized native-crypto universe by strictly past funding
pressure.  Persistent positive funding is a costly crowded-long condition and therefore receives a
lower expected price-return score; persistent negative funding receives a higher score.  Four
low-pressure contracts are held long and four high-pressure contracts short on a weekly schedule.

Universe classification is deliberately outside this module.  Amendment 0006 supplies membership
containing native crypto assets only and excludes stablecoin bases plus tokenized or synthetic
TradFi securities, commodities, metals, and indexes.  The strategy never guesses asset class from
ticker text.
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
    """Complete material configuration for the final funding-pressure mechanism."""

    interval_hours: int = 8
    decision_interval_hours: int = 168
    price_history_bars: int = 64
    volatility_horizon_bars: int = 42
    tail_horizon_bars: int = 21
    funding_lookback_days: int = 14
    minimum_funding_events: int = 12
    recent_funding_events: int = 3
    maximum_funding_staleness_hours: int = 24
    minimum_cross_section: int = 12
    minimum_scored_symbols: int = 10
    selection_count_per_side: int = 4
    retention_rank_buffer: int = 2
    gross_exposure: float = 0.12
    maximum_symbol_weight: float = 0.02
    maximum_abs_one_bar_return: float = 0.20
    maximum_abs_tail_return: float = 0.35
    maximum_window_drawdown: float = 0.45
    maximum_log_price_range: float = 0.70
    maximum_annualized_volatility: float = 1.50
    maximum_abs_funding_rate: float = 0.01
    minimum_positive_volume_fraction: float = 0.80
    funding_persistence_weight: float = 0.30
    robust_z_clip: float = 4.0
    minimum_score_spread: float = 0.75
    minimum_selected_abs_score: float = 0.25

    def validate(self) -> None:
        integer_fields = (
            self.interval_hours,
            self.decision_interval_hours,
            self.price_history_bars,
            self.volatility_horizon_bars,
            self.tail_horizon_bars,
            self.funding_lookback_days,
            self.minimum_funding_events,
            self.recent_funding_events,
            self.maximum_funding_staleness_hours,
            self.minimum_cross_section,
            self.minimum_scored_symbols,
            self.selection_count_per_side,
        )
        if any(type(value) is not int or value <= 0 for value in integer_fields):
            raise ValueError("integer configuration fields must be positive")
        if self.decision_interval_hours % self.interval_hours:
            raise ValueError("decision interval must be a multiple of the bar interval")
        if not (self.tail_horizon_bars < self.volatility_horizon_bars < self.price_history_bars):
            raise ValueError("price quarantine horizons must be strictly increasing")
        if self.recent_funding_events > self.minimum_funding_events:
            raise ValueError("recent funding events cannot exceed the minimum event count")
        if self.maximum_funding_staleness_hours > 24 * self.funding_lookback_days:
            raise ValueError("funding staleness cannot exceed the funding lookback")
        if self.minimum_cross_section < self.minimum_scored_symbols:
            raise ValueError("minimum cross section cannot be below minimum scored symbols")
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
            self.minimum_positive_volume_fraction,
        )
        if any(not 0.0 < value < 1.0 for value in unit_interval_fields):
            raise ValueError("return, drawdown, and volume thresholds must be in (0, 1)")
        positive_fields = (
            self.maximum_log_price_range,
            self.maximum_annualized_volatility,
            self.maximum_abs_funding_rate,
            self.robust_z_clip,
            self.minimum_score_spread,
            self.minimum_selected_abs_score,
        )
        if any(not math.isfinite(value) or value <= 0.0 for value in positive_fields):
            raise ValueError("scale and score thresholds must be positive and finite")
        if (
            not math.isfinite(self.funding_persistence_weight)
            or self.funding_persistence_weight < 0.0
        ):
            raise ValueError("funding persistence weight must be finite and nonnegative")


class FundingPressureUnwind:
    """Stateful weekly selector for a balanced funding-pressure transfer book."""

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
        expected_close_times = pd.date_range(
            end=decision_time,
            periods=self.config.price_history_bars,
            freq=interval,
        )
        price_admissible: set[str] = set()
        for symbol in sorted(eligible):
            raw_frame = context.bars.get(symbol)
            if raw_frame is None:
                continue
            history = _closed_history(raw_frame, decision_time, interval)
            if history.empty or history.index[-1] != decision_time:
                continue
            window = history.reindex(expected_close_times)
            if window.isna().any().any():
                continue
            prices = window["close"].to_numpy(dtype=float)
            quote_volume = window["quote_volume"].to_numpy(dtype=float)
            if _passes_price_admissibility(prices, quote_volume, self.config):
                price_admissible.add(symbol)
        if len(price_admissible) < self.config.minimum_cross_section:
            return self._capture_empty_and_flat()

        funding = _closed_funding(
            getattr(context, "funding", None),
            decision_time=decision_time,
            lookback=pd.Timedelta(days=self.config.funding_lookback_days),
        )
        pressure_by_symbol: dict[str, float] = {}
        for symbol in sorted(price_admissible):
            rows = funding.loc[funding["symbol"] == symbol]
            if len(rows) < self.config.minimum_funding_events:
                continue
            if decision_time - rows["funding_time"].iloc[-1] > pd.Timedelta(
                hours=self.config.maximum_funding_staleness_hours
            ):
                continue
            rates = rows["funding_rate"].to_numpy(dtype=float)
            if float(np.abs(rates).max()) > self.config.maximum_abs_funding_rate:
                continue
            sign_balance = float(np.sign(rates).mean())
            recent_sign_balance = float(np.sign(rates[-self.config.recent_funding_events :]).mean())
            absolute_transfer = float(np.abs(rates).sum())
            cumulative_transfer = float(rates.sum())
            persistent_transfer = (
                0.5 * sign_balance + 0.5 * recent_sign_balance
            ) * absolute_transfer
            pressure = cumulative_transfer + (
                self.config.funding_persistence_weight * persistent_transfer
            )
            if math.isfinite(pressure):
                pressure_by_symbol[symbol] = pressure
        if len(pressure_by_symbol) < self.config.minimum_scored_symbols:
            return self._capture_empty_and_flat()

        funding_pressure = pd.Series(pressure_by_symbol, dtype=float).sort_index()
        pressure_z = _robust_cross_sectional_z(
            funding_pressure,
            self.config.robust_z_clip,
        )
        transformed_scores = -pressure_z
        if not np.isfinite(transformed_scores.to_numpy(dtype=float)).all():
            raise ValueError("non-finite funding-pressure score")
        scores = {
            str(symbol): float(transformed_scores[symbol])
            for symbol in sorted(transformed_scores.index)
        }
        captured_scores = _capture_scores(
            scores,
            expected_symbols=frozenset(pressure_by_symbol),
        )
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


def _closed_funding(
    frame: Any,
    *,
    decision_time: pd.Timestamp,
    lookback: pd.Timedelta,
) -> pd.DataFrame:
    columns = ("funding_time", "symbol", "funding_rate")
    if frame is None:
        return pd.DataFrame(columns=columns)
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("funding input must be a pandas DataFrame")
    missing = set(columns) - set(frame.columns)
    if missing:
        raise ValueError(f"funding frame missing columns: {sorted(missing)}")
    funding_times = pd.to_datetime(frame["funding_time"], utc=True, errors="raise")
    usable_mask = (funding_times < decision_time) & (funding_times >= decision_time - lookback)
    if not bool(usable_mask.any()):
        return pd.DataFrame(columns=columns)
    closed = pd.DataFrame(
        {
            "funding_time": funding_times.loc[usable_mask],
            "symbol": frame.loc[usable_mask, "symbol"],
            "funding_rate": pd.to_numeric(
                frame.loc[usable_mask, "funding_rate"],
                errors="raise",
            ),
        }
    )
    if any(type(symbol) is not str or not symbol for symbol in closed["symbol"]):
        raise ValueError("past funding symbols must be nonempty strings")
    if closed.duplicated(subset=["symbol", "funding_time"]).any():
        raise ValueError("duplicate funding event for symbol and timestamp")
    rates = closed["funding_rate"].to_numpy(dtype=float)
    if not np.isfinite(rates).all():
        raise ValueError("past funding rates must be finite")
    return closed.sort_values(["symbol", "funding_time"]).reset_index(drop=True)


def _passes_price_admissibility(
    prices: np.ndarray,
    quote_volume: np.ndarray,
    config: StrategyConfig,
) -> bool:
    if not np.isfinite(prices).all() or not np.isfinite(quote_volume).all():
        return False
    if (prices <= 0.0).any() or (quote_volume < 0.0).any():
        return False
    if float(np.mean(quote_volume > 0.0)) < config.minimum_positive_volume_fraction:
        return False
    log_returns = np.diff(np.log(prices))
    simple_returns = np.expm1(log_returns)
    if float(np.abs(simple_returns).max()) > config.maximum_abs_one_bar_return:
        return False
    tail_return = abs(float(np.expm1(log_returns[-config.tail_horizon_bars :].sum())))
    if tail_return > config.maximum_abs_tail_return:
        return False
    running_peak = np.maximum.accumulate(prices)
    maximum_drawdown = float(np.max(1.0 - prices / running_peak))
    if maximum_drawdown > config.maximum_window_drawdown:
        return False
    log_range = float(np.log(prices.max()) - np.log(prices.min()))
    if log_range > config.maximum_log_price_range:
        return False
    volatility_window = log_returns[-config.volatility_horizon_bars :]
    annualized_volatility = float(volatility_window.std(ddof=0) * math.sqrt(3 * 365))
    return annualized_volatility <= config.maximum_annualized_volatility


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


def build_strategy() -> FundingPressureUnwind:
    """Canonical tournament entrypoint for final pivot-02."""
    return FundingPressureUnwind()
