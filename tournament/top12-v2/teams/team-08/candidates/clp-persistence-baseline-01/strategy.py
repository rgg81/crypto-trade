"""Team 08 baseline: persistent intrabar close-location pressure."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


LOOKBACK_BARS = 126
MINIMUM_VALID_RANGE_BARS = 100
DECAY_HALFLIFE_BARS = 42.0
BAR_HOURS = 8
MINIMUM_CROSS_SECTION = 6
RELATIVE_RANGE_FLOOR = 1.0e-12
TARGET_GROSS = 1.0


def _utc_timestamp(value) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _open_times_utc(values: pd.Series) -> pd.Series:
    """Parse common timestamp representations without consulting outside state."""
    if pd.api.types.is_numeric_dtype(values):
        numeric = pd.to_numeric(values, errors="coerce")
        finite = numeric[np.isfinite(numeric)]
        if finite.empty:
            return pd.to_datetime(numeric, utc=True, errors="coerce")

        scale = float(np.median(np.abs(finite.to_numpy(dtype=float))))
        if scale >= 1.0e17:
            unit = "ns"
        elif scale >= 1.0e14:
            unit = "us"
        elif scale >= 1.0e11:
            unit = "ms"
        else:
            unit = "s"
        return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")

    return pd.to_datetime(values, utc=True, errors="coerce")


def _symbol_observation(frame: pd.DataFrame, cutoff: pd.Timestamp) -> tuple[float, float] | None:
    required = {"open_time", "high", "low", "close"}
    if frame is None or not required.issubset(frame.columns):
        return None

    work = pd.DataFrame(
        {
            "time": _open_times_utc(frame["open_time"]),
            "high": pd.to_numeric(frame["high"], errors="coerce"),
            "low": pd.to_numeric(frame["low"], errors="coerce"),
            "close": pd.to_numeric(frame["close"], errors="coerce"),
        }
    )
    work = work.loc[work["time"].notna() & (work["time"] <= cutoff)]
    work = work.sort_values("time", kind="mergesort").drop_duplicates("time", keep="last")
    work = work.tail(LOOKBACK_BARS)
    if len(work) < LOOKBACK_BARS:
        return None

    high = work["high"].to_numpy(dtype=float)
    low = work["low"].to_numpy(dtype=float)
    close = work["close"].to_numpy(dtype=float)
    price_range = high - low
    floor = RELATIVE_RANGE_FLOOR * np.maximum(np.abs(close), 1.0)
    valid = (
        np.isfinite(high)
        & np.isfinite(low)
        & np.isfinite(close)
        & (close > 0.0)
        & (price_range > floor)
    )
    if int(valid.sum()) < MINIMUM_VALID_RANGE_BARS:
        return None
    if not np.isfinite(close[[0, -1]]).all() or np.any(close[[0, -1]] <= 0.0):
        return None

    # Map close location in the completed bar's range to [-1, 1].
    close_location = np.zeros(LOOKBACK_BARS, dtype=float)
    close_location[valid] = (
        2.0 * (close[valid] - low[valid]) / price_range[valid] - 1.0
    )
    close_location = np.clip(close_location, -1.0, 1.0)

    age = (LOOKBACK_BARS - 1) - np.arange(LOOKBACK_BARS, dtype=float)
    decay = np.power(0.5, age / DECAY_HALFLIFE_BARS)
    weights = decay[valid]
    values = close_location[valid]
    weight_sum = float(weights.sum())
    if not np.isfinite(weight_sum) or weight_sum <= 0.0:
        return None

    mean_location = float(np.dot(weights, values) / weight_sum)
    sign_balance = float(np.dot(weights, np.sign(values)) / weight_sum)
    persistence_pressure = mean_location * abs(sign_balance)
    formation_return = float(np.log(close[-1] / close[0]))
    if not np.isfinite(persistence_pressure) or not np.isfinite(formation_return):
        return None
    return persistence_pressure, formation_return


class CloseLocationPersistenceStrategy:
    """Weekly rank portfolio driven by return-neutralized auction pressure."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # The construction is deterministic and deliberately needs no randomness.
        decision_time = _utc_timestamp(context.decision_time)

        # Rebalance with the weekly universe boundary; otherwise preserve quantities.
        if (
            decision_time.weekday() != 0
            or decision_time.hour != 0
            or decision_time.minute != 0
            or decision_time.second != 0
            or decision_time.microsecond != 0
            or decision_time.nanosecond != 0
        ):
            return None

        symbols = sorted(str(symbol) for symbol in context.eligible_symbols)
        flat_targets = {symbol: 0.0 for symbol in symbols}
        cutoff = decision_time - pd.Timedelta(hours=BAR_HOURS)

        observations: dict[str, tuple[float, float]] = {}
        for symbol in symbols:
            observation = _symbol_observation(context.bars.get(symbol), cutoff)
            if observation is not None:
                observations[symbol] = observation

        if len(observations) < MINIMUM_CROSS_SECTION:
            return flat_targets

        active = sorted(observations)
        pressure = pd.Series(
            {symbol: observations[symbol][0] for symbol in active}, dtype=float
        )
        formation_return = pd.Series(
            {symbol: observations[symbol][1] for symbol in active}, dtype=float
        )

        # Remove the linear cross-sectional component associated with the rank of
        # close-to-close formation return. This isolates auction-location pressure.
        return_rank = formation_return.rank(method="average")
        return_control = return_rank - float(return_rank.mean())
        pressure_centered = pressure - float(pressure.mean())
        denominator = float(np.dot(return_control, return_control))
        if denominator > 0.0 and np.isfinite(denominator):
            beta = float(np.dot(return_control, pressure_centered) / denominator)
            residual_pressure = pressure_centered - beta * return_control
        else:
            residual_pressure = pressure_centered

        signal_rank = residual_pressure.rank(method="average")
        centered_rank = signal_rank - float(signal_rank.mean())
        long_scores = centered_rank.clip(lower=0.0)
        short_scores = (-centered_rank.clip(upper=0.0))
        long_sum = float(long_scores.sum())
        short_sum = float(short_scores.sum())
        if long_sum <= 0.0 or short_sum <= 0.0:
            return flat_targets

        side_gross = TARGET_GROSS / 2.0
        for symbol in active:
            long_weight = side_gross * float(long_scores[symbol]) / long_sum
            short_weight = side_gross * float(short_scores[symbol]) / short_sum
            flat_targets[symbol] = long_weight - short_weight
        return flat_targets


def build_strategy() -> CloseLocationPersistenceStrategy:
    return CloseLocationPersistenceStrategy()
