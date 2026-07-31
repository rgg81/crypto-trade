"""Causal volume-clock intensity-transition baseline for Team 09."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


BAR_HOURS = 8
NORMALIZATION_BARS = 180
NORMALIZATION_MINIMUM_BARS = 90
FAST_INTENSITY_BARS = 9
SLOW_INTENSITY_BARS = 63
TRANSITION_LAG_BARS = 3
RETURN_BARS = 15
RETURN_VOLATILITY_BARS = 63
ACTIVITY_CLIP = 4.0
TRANSITION_CLIP = 4.0
RETURN_CLIP = 4.0
MAXIMUM_GROSS = 0.8
MAXIMUM_ABSOLUTE_NET = 0.2
MAXIMUM_SYMBOL_WEIGHT = 0.08
REBALANCE_UTC_HOUR = 0


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _completed_bars(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.DataFrame:
    required = {"open_time", "close", "quote_volume", "trade_count"}
    if not required.issubset(frame.columns):
        return pd.DataFrame()

    open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    completed = open_times + pd.Timedelta(hours=BAR_HOURS) <= decision_time
    selected = frame.loc[
        completed, ["open_time", "close", "quote_volume", "trade_count"]
    ].copy()
    if selected.empty:
        return selected

    selected["_open_time"] = open_times.loc[completed]
    selected = (
        selected.sort_values("_open_time")
        .drop_duplicates("_open_time", keep="last")
        .reset_index(drop=True)
    )
    return selected


def _last_finite(series: pd.Series) -> float | None:
    if series.empty:
        return None
    value = float(series.iloc[-1])
    return value if np.isfinite(value) else None


def _signal(frame: pd.DataFrame, decision_time: pd.Timestamp) -> float | None:
    bars = _completed_bars(frame, decision_time)
    minimum_length = max(
        NORMALIZATION_MINIMUM_BARS + SLOW_INTENSITY_BARS + TRANSITION_LAG_BARS,
        RETURN_VOLATILITY_BARS + RETURN_BARS + 1,
    )
    if len(bars) < minimum_length:
        return None

    close = pd.to_numeric(bars["close"], errors="coerce")
    quote_volume = pd.to_numeric(bars["quote_volume"], errors="coerce")
    trade_count = pd.to_numeric(bars["trade_count"], errors="coerce")
    close = close.where((close > 0.0) & np.isfinite(close))
    quote_volume = quote_volume.where((quote_volume > 0.0) & np.isfinite(quote_volume))
    trade_count = trade_count.where((trade_count > 0.0) & np.isfinite(trade_count))

    log_quote_volume = np.log(quote_volume)
    log_trade_count = np.log(trade_count)
    quote_reference = (
        log_quote_volume.rolling(
            NORMALIZATION_BARS, min_periods=NORMALIZATION_MINIMUM_BARS
        )
        .median()
        .shift(1)
    )
    trade_reference = (
        log_trade_count.rolling(
            NORMALIZATION_BARS, min_periods=NORMALIZATION_MINIMUM_BARS
        )
        .median()
        .shift(1)
    )
    relative_activity = 0.5 * (
        (log_quote_volume - quote_reference) + (log_trade_count - trade_reference)
    )
    activity_scale = (
        relative_activity.rolling(
            NORMALIZATION_BARS, min_periods=NORMALIZATION_MINIMUM_BARS
        )
        .std(ddof=0)
        .shift(1)
    )
    activity_scale = activity_scale.where(activity_scale > 1.0e-12)
    intensity = (relative_activity / activity_scale).clip(-ACTIVITY_CLIP, ACTIVITY_CLIP)

    fast_state = intensity.rolling(
        FAST_INTENSITY_BARS, min_periods=FAST_INTENSITY_BARS
    ).mean()
    slow_state = intensity.rolling(
        SLOW_INTENSITY_BARS, min_periods=SLOW_INTENSITY_BARS
    ).mean()
    state_gap = fast_state - slow_state
    transition = state_gap - state_gap.shift(TRANSITION_LAG_BARS)
    transition_scale = (
        transition.rolling(
            NORMALIZATION_BARS, min_periods=NORMALIZATION_MINIMUM_BARS
        )
        .std(ddof=0)
        .shift(1)
    )
    transition_z = (transition / transition_scale.where(transition_scale > 1.0e-12)).clip(
        -TRANSITION_CLIP, TRANSITION_CLIP
    )

    log_return = np.log(close).diff()
    recent_return = log_return.rolling(RETURN_BARS, min_periods=RETURN_BARS).sum()
    return_scale = (
        log_return.rolling(
            RETURN_VOLATILITY_BARS, min_periods=RETURN_VOLATILITY_BARS
        )
        .std(ddof=0)
        .shift(1)
        * np.sqrt(float(RETURN_BARS))
    )
    return_z = (recent_return / return_scale.where(return_scale > 1.0e-12)).clip(
        -RETURN_CLIP, RETURN_CLIP
    )

    transition_value = _last_finite(transition_z)
    return_value = _last_finite(return_z)
    if transition_value is None or return_value is None:
        return None

    score = float(np.tanh(transition_value) * np.tanh(return_value))
    return score if np.isfinite(score) else None


class VolumeClockIntensityTransitionStrategy:
    """Daily long/short ranking of normalized business-time transitions."""

    def target_weights(
        self, context: object, *, seed: int
    ) -> Mapping[str, float] | None:
        del seed
        decision_time = _utc_timestamp(context.decision_time)
        if (
            decision_time.hour != REBALANCE_UTC_HOUR
            or decision_time.minute != 0
            or decision_time.second != 0
        ):
            return None

        symbols = sorted(str(symbol) for symbol in context.eligible_symbols)
        if not symbols:
            return {}

        scores: dict[str, float] = {}
        for symbol in symbols:
            frame = context.bars.get(symbol)
            if not isinstance(frame, pd.DataFrame):
                continue
            score = _signal(frame, decision_time)
            if score is not None:
                scores[symbol] = score

        weights = {symbol: 0.0 for symbol in symbols}
        if len(scores) < 2:
            return weights

        ranked = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
        side_count = len(ranked) // 2
        shorts = ranked[:side_count]
        longs = ranked[-side_count:]
        side_gross = min(
            MAXIMUM_GROSS / 2.0,
            MAXIMUM_SYMBOL_WEIGHT * len(shorts),
            MAXIMUM_SYMBOL_WEIGHT * len(longs),
        )
        long_weight = min(MAXIMUM_SYMBOL_WEIGHT, side_gross / len(longs))
        short_weight = -min(MAXIMUM_SYMBOL_WEIGHT, side_gross / len(shorts))

        for symbol in longs:
            weights[symbol] = float(long_weight)
        for symbol in shorts:
            weights[symbol] = float(short_weight)

        gross = float(sum(abs(weight) for weight in weights.values()))
        net = float(sum(weights.values()))
        if (
            not all(np.isfinite(weight) for weight in weights.values())
            or gross > MAXIMUM_GROSS + 1.0e-12
            or abs(net) > MAXIMUM_ABSOLUTE_NET + 1.0e-12
            or any(
                abs(weight) > MAXIMUM_SYMBOL_WEIGHT + 1.0e-12
                for weight in weights.values()
            )
        ):
            return {symbol: 0.0 for symbol in symbols}
        return weights


def build_strategy() -> VolumeClockIntensityTransitionStrategy:
    return VolumeClockIntensityTransitionStrategy()
