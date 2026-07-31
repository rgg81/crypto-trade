"""Transparent baseline for asymmetric compression-to-expansion transitions."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


BAR_HOURS = 8
FORMATION_BARS = 126
COMPRESSION_BARS = 36
REBALANCE_BARS = 6
LONG_HOLDING_BARS = 12
SHORT_HOLDING_BARS = 6

COMPRESSION_MEDIAN_RATIO_MAX = 0.68
COMPRESSION_UPPER_QUARTILE_RATIO_MAX = 0.82

UP_EXPANSION_MULTIPLE = 1.75
UP_CLOSE_LOCATION_MIN = 0.72
UP_BODY_EFFICIENCY_MIN = 0.42

DOWN_EXPANSION_MULTIPLE = 2.10
DOWN_CLOSE_LOCATION_MAX = 0.18
DOWN_BODY_EFFICIENCY_MIN = 0.55

MAX_SYMBOL_WEIGHT = 0.08
MAX_GROSS = 0.80
MAX_ABS_NET = 0.20
TWO_SIDED_BUDGET = 0.36
ONE_SIDED_BUDGET = 0.20


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _completed_prices(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.DataFrame:
    required = ("open_time", "open", "high", "low", "close")
    if frame is None or any(column not in frame.columns for column in required):
        return pd.DataFrame(columns=required)

    prices = frame.loc[:, required].copy()
    prices["open_time"] = pd.to_datetime(prices["open_time"], utc=True, errors="coerce")
    completion_time = prices["open_time"] + pd.Timedelta(hours=BAR_HOURS)
    prices = prices.loc[completion_time <= decision_time]

    for column in ("open", "high", "low", "close"):
        prices[column] = pd.to_numeric(prices[column], errors="coerce")

    prices = prices.replace([np.inf, -np.inf], np.nan).dropna()
    prices = prices.sort_values("open_time").drop_duplicates("open_time", keep="last")
    valid = (
        (prices["open"] > 0.0)
        & (prices["high"] > 0.0)
        & (prices["low"] > 0.0)
        & (prices["close"] > 0.0)
        & (prices["high"] >= prices[["open", "close", "low"]].max(axis=1))
        & (prices["low"] <= prices[["open", "close", "high"]].min(axis=1))
    )
    return prices.loc[valid].reset_index(drop=True)


def _normalized_true_ranges(prices: pd.DataFrame) -> np.ndarray:
    high = prices["high"].to_numpy(dtype=float)
    low = prices["low"].to_numpy(dtype=float)
    close = prices["close"].to_numpy(dtype=float)
    previous_close = np.roll(close, 1)
    previous_close[0] = close[0]
    raw_range = np.maximum.reduce(
        (high - low, np.abs(high - previous_close), np.abs(low - previous_close))
    )
    denominator = np.maximum(previous_close, np.finfo(float).tiny)
    return raw_range / denominator


def _most_recent_transition_score(prices: pd.DataFrame) -> float:
    minimum_rows = FORMATION_BARS + 1
    if len(prices) < minimum_rows:
        return 0.0

    ranges = _normalized_true_ranges(prices)
    open_prices = prices["open"].to_numpy(dtype=float)
    high = prices["high"].to_numpy(dtype=float)
    low = prices["low"].to_numpy(dtype=float)
    close = prices["close"].to_numpy(dtype=float)
    first_event = max(FORMATION_BARS, len(prices) - LONG_HOLDING_BARS)

    for event_index in range(len(prices) - 1, first_event - 1, -1):
        compression = ranges[event_index - COMPRESSION_BARS : event_index]
        reference = ranges[event_index - FORMATION_BARS : event_index - COMPRESSION_BARS]
        compression_median = float(np.median(compression))
        reference_median = float(np.median(reference))
        if (
            not np.isfinite(compression_median)
            or not np.isfinite(reference_median)
            or compression_median <= 0.0
            or reference_median <= 0.0
        ):
            continue

        median_ratio = compression_median / reference_median
        upper_quartile_ratio = float(np.quantile(compression, 0.75)) / reference_median
        if (
            median_ratio > COMPRESSION_MEDIAN_RATIO_MAX
            or upper_quartile_ratio > COMPRESSION_UPPER_QUARTILE_RATIO_MAX
        ):
            continue

        current_range = high[event_index] - low[event_index]
        if current_range <= 0.0:
            continue
        expansion_multiple = ranges[event_index] / compression_median
        close_location = (close[event_index] - low[event_index]) / current_range
        body_efficiency = abs(close[event_index] - open_prices[event_index]) / current_range
        compression_high = float(np.max(high[event_index - COMPRESSION_BARS : event_index]))
        compression_low = float(np.min(low[event_index - COMPRESSION_BARS : event_index]))
        compression_midpoint = 0.5 * (compression_high + compression_low)
        age = len(prices) - 1 - event_index
        compression_strength = max(0.0, 1.0 - median_ratio)

        upward_release = (
            close[event_index] > open_prices[event_index]
            and close[event_index] > compression_midpoint
            and expansion_multiple >= UP_EXPANSION_MULTIPLE
            and close_location >= UP_CLOSE_LOCATION_MIN
            and body_efficiency >= UP_BODY_EFFICIENCY_MIN
        )
        if upward_release and age < LONG_HOLDING_BARS:
            decay = 1.0 - age / LONG_HOLDING_BARS
            confirmation = (
                1.0
                + 0.35 * (expansion_multiple / UP_EXPANSION_MULTIPLE - 1.0)
                + 0.25 * (close_location - UP_CLOSE_LOCATION_MIN)
                + 0.20 * body_efficiency
            )
            return float(decay * compression_strength * confirmation)

        downward_release = (
            close[event_index] < open_prices[event_index]
            and close[event_index] < compression_midpoint
            and expansion_multiple >= DOWN_EXPANSION_MULTIPLE
            and close_location <= DOWN_CLOSE_LOCATION_MAX
            and body_efficiency >= DOWN_BODY_EFFICIENCY_MIN
        )
        if downward_release and age < SHORT_HOLDING_BARS:
            decay = 1.0 - age / SHORT_HOLDING_BARS
            confirmation = (
                1.0
                + 0.35 * (expansion_multiple / DOWN_EXPANSION_MULTIPLE - 1.0)
                + 0.25 * (DOWN_CLOSE_LOCATION_MAX - close_location)
                + 0.20 * body_efficiency
            )
            return float(-decay * compression_strength * confirmation)

    return 0.0


def _allocate_side(scores: Mapping[str, float], budget: float) -> dict[str, float]:
    if not scores or budget <= 0.0:
        return {}
    denominator = float(sum(abs(score) for score in scores.values()))
    if not np.isfinite(denominator) or denominator <= 0.0:
        return {}
    return {
        symbol: float(np.clip(budget * score / denominator, -MAX_SYMBOL_WEIGHT, MAX_SYMBOL_WEIGHT))
        for symbol, score in scores.items()
    }


def _bounded_targets(scores: Mapping[str, float]) -> dict[str, float]:
    longs = {symbol: score for symbol, score in scores.items() if score > 0.0}
    shorts = {symbol: score for symbol, score in scores.items() if score < 0.0}
    if longs and shorts:
        targets = _allocate_side(longs, TWO_SIDED_BUDGET)
        targets.update(_allocate_side(shorts, TWO_SIDED_BUDGET))
    else:
        targets = _allocate_side(longs or shorts, ONE_SIDED_BUDGET)

    targets = {
        symbol: float(weight)
        for symbol, weight in targets.items()
        if np.isfinite(weight) and abs(weight) > 0.0
    }
    gross = float(sum(abs(weight) for weight in targets.values()))
    net = float(sum(targets.values()))
    scale = 1.0
    if gross > MAX_GROSS:
        scale = min(scale, MAX_GROSS / gross)
    if abs(net) > MAX_ABS_NET:
        scale = min(scale, MAX_ABS_NET / abs(net))
    if scale < 1.0:
        targets = {symbol: float(weight * scale) for symbol, weight in targets.items()}
    return targets


class CompressionExpansionAsymmetry:
    def target_weights(self, context, *, seed: int):
        del seed
        decision_time = _utc_timestamp(context.decision_time)
        last_rebalance = getattr(self, "_last_rebalance", None)
        minimum_interval = pd.Timedelta(hours=BAR_HOURS * REBALANCE_BARS)
        if last_rebalance is not None and decision_time < last_rebalance + minimum_interval:
            return None

        self._last_rebalance = decision_time
        scores: dict[str, float] = {}
        for symbol in sorted(context.eligible_symbols):
            if symbol not in context.bars:
                continue
            prices = _completed_prices(context.bars[symbol], decision_time)
            score = _most_recent_transition_score(prices)
            if np.isfinite(score) and score != 0.0:
                scores[symbol] = float(score)
        return _bounded_targets(scores)


def build_strategy():
    strategy = CompressionExpansionAsymmetry()
    strategy._last_rebalance = None
    return strategy
