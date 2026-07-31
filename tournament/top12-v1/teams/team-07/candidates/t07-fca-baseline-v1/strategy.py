"""Funding-curve slope/acceleration baseline for Team 07."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


FORMATION_OBSERVATIONS = 21
MINIMUM_SETTLEMENTS = 12
SELECTION_PER_SIDE = 5
TARGET_SIDE_GROSS = 0.40
MAXIMUM_SYMBOL_WEIGHT = 0.08


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _utc_times(values: pd.Series) -> pd.Series:
    numeric = pd.to_numeric(values, errors="coerce")
    usable_numeric = numeric.dropna()
    if len(usable_numeric) == len(values) and len(usable_numeric) > 0:
        magnitude = float(usable_numeric.abs().median())
        if magnitude >= 1.0e14:
            return pd.to_datetime(numeric, unit="us", utc=True, errors="coerce")
        if magnitude >= 1.0e11:
            return pd.to_datetime(numeric, unit="ms", utc=True, errors="coerce")
        if magnitude >= 1.0e9:
            return pd.to_datetime(numeric, unit="s", utc=True, errors="coerce")
    return pd.to_datetime(values, utc=True, errors="coerce")


def _symbol_funding_frame(source: Any, symbol: str) -> pd.DataFrame | None:
    if isinstance(source, pd.DataFrame):
        for symbol_column in ("symbol", "contract", "ticker"):
            if symbol_column in source.columns:
                mask = source[symbol_column].astype(str) == symbol
                return source.loc[mask]
        return None
    if isinstance(source, Mapping):
        frame = source.get(symbol)
        return frame if isinstance(frame, pd.DataFrame) else None
    return None


def _settled_rates(
    source: Any,
    symbol: str,
    decision_time: pd.Timestamp,
) -> np.ndarray | None:
    frame = _symbol_funding_frame(source, symbol)
    if frame is None or frame.empty:
        return None

    time_column = next(
        (
            name
            for name in (
                "funding_time",
                "settlement_time",
                "settle_time",
                "timestamp",
                "time",
                "open_time",
            )
            if name in frame.columns
        ),
        None,
    )
    rate_column = next(
        (
            name
            for name in ("funding_rate", "fundingRate", "rate")
            if name in frame.columns
        ),
        None,
    )
    if time_column is None or rate_column is None:
        return None

    times = _utc_times(frame[time_column])
    rates = pd.to_numeric(frame[rate_column], errors="coerce")
    local = pd.DataFrame({"time": times, "rate": rates})
    local = local.loc[
        local["time"].notna()
        & local["rate"].notna()
        & (local["time"] < decision_time)
    ]
    local = local.sort_values("time").drop_duplicates("time", keep="last")
    if len(local) < MINIMUM_SETTLEMENTS:
        return None

    values = local["rate"].tail(FORMATION_OBSERVATIONS).to_numpy(dtype=float)
    if len(values) < MINIMUM_SETTLEMENTS or not np.isfinite(values).all():
        return None
    return values


def _linear_slope(values: np.ndarray) -> float:
    x = np.arange(len(values), dtype=float)
    x -= x.mean()
    denominator = float(np.dot(x, x))
    if denominator <= 0.0:
        return 0.0
    return float(np.dot(x, values - values.mean()) / denominator)


def _robust_standardize(values: np.ndarray) -> np.ndarray:
    centered = values - np.median(values)
    mad = float(np.median(np.abs(centered)))
    scale = 1.4826 * mad
    if not np.isfinite(scale) or scale <= 1.0e-15:
        scale = float(np.std(values))
    if not np.isfinite(scale) or scale <= 1.0e-15:
        return np.zeros_like(values, dtype=float)
    return centered / scale


def _level_neutral_signal(
    symbols: list[str],
    features: dict[str, tuple[float, float, float]],
) -> dict[str, float]:
    slopes = np.asarray([features[symbol][0] for symbol in symbols], dtype=float)
    accelerations = np.asarray(
        [features[symbol][1] for symbol in symbols],
        dtype=float,
    )
    levels = np.asarray([features[symbol][2] for symbol in symbols], dtype=float)

    derivative_score = (
        0.5 * _robust_standardize(slopes)
        + 0.5 * _robust_standardize(accelerations)
    )
    derivative_score -= derivative_score.mean()
    level_score = _robust_standardize(levels)
    level_score -= level_score.mean()

    level_energy = float(np.dot(level_score, level_score))
    if level_energy > 1.0e-15:
        beta = float(np.dot(derivative_score, level_score) / level_energy)
        derivative_score = derivative_score - beta * level_score
    derivative_score -= derivative_score.mean()

    return {
        symbol: float(score)
        for symbol, score in zip(symbols, derivative_score, strict=True)
        if np.isfinite(score)
    }


class FundingCurveAccelerationStrategy:
    def target_weights(
        self,
        context: Any,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        del seed
        decision_time = _utc_timestamp(context.decision_time)
        if (
            decision_time.hour != 0
            or decision_time.minute != 0
            or decision_time.second != 0
        ):
            return None

        eligible = sorted({str(symbol) for symbol in context.eligible_symbols})
        flat_targets = {symbol: 0.0 for symbol in eligible}
        features: dict[str, tuple[float, float, float]] = {}
        for symbol in eligible:
            values = _settled_rates(context.funding, symbol, decision_time)
            if values is None:
                continue
            slope = _linear_slope(values)
            acceleration = _linear_slope(np.diff(values))
            level = float(values[-1])
            if np.isfinite([slope, acceleration, level]).all():
                features[symbol] = (slope, acceleration, level)

        symbols = sorted(features)
        if len(symbols) < 2:
            return flat_targets
        signal = _level_neutral_signal(symbols, features)
        ranked = sorted(signal, key=lambda symbol: (signal[symbol], symbol))
        names_per_side = min(SELECTION_PER_SIDE, len(ranked) // 2)
        if names_per_side == 0:
            return flat_targets

        side_gross = min(
            TARGET_SIDE_GROSS,
            MAXIMUM_SYMBOL_WEIGHT * names_per_side,
        )
        symbol_weight = side_gross / names_per_side
        for symbol in ranked[:names_per_side]:
            flat_targets[symbol] = -float(symbol_weight)
        for symbol in ranked[-names_per_side:]:
            flat_targets[symbol] = float(symbol_weight)
        return flat_targets


def build_strategy() -> FundingCurveAccelerationStrategy:
    return FundingCurveAccelerationStrategy()
