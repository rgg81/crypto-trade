"""Causal calendar-boundary flow-reversal baseline for team-10."""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np
import pandas as pd


FORMATION_BARS = 9
REFERENCE_BARS = 81
PRE_BOUNDARY_HOURS = 24
POST_BOUNDARY_HOURS = 48
CONFIRMATION_Z = 0.75
NAMES_PER_SIDE = 3
TARGET_GROSS = 0.80


def _as_utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _open_times_utc(values: pd.Series) -> pd.Series:
    """Convert datetime-like or conventional epoch open times to UTC."""
    numeric = pd.to_numeric(values, errors="coerce")
    finite = numeric[np.isfinite(numeric.to_numpy(dtype=float, na_value=np.nan))]
    if len(finite) == len(values) and len(finite) > 0:
        magnitude = float(np.median(np.abs(finite.to_numpy(dtype=float))))
        if magnitude >= 1.0e17:
            unit = "ns"
        elif magnitude >= 1.0e14:
            unit = "us"
        elif magnitude >= 1.0e11:
            unit = "ms"
        else:
            unit = "s"
        return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
    return pd.to_datetime(values, utc=True, errors="coerce")


def _flow_columns(frame: pd.DataFrame) -> tuple[str, str] | None:
    candidates = (
        ("taker_buy_quote_volume", "quote_volume"),
        ("taker_buy_base_volume", "base_volume"),
        ("taker_buy_volume", "base_volume"),
        ("taker_buy_base_volume", "volume"),
        ("taker_buy_base_asset_volume", "volume"),
        ("taker_buy_quote_asset_volume", "quote_asset_volume"),
    )
    for buy_column, total_column in candidates:
        if buy_column in frame.columns and total_column in frame.columns:
            return buy_column, total_column
    return None


def _robust_scale(values: np.ndarray) -> float:
    median = float(np.median(values))
    mad_scale = 1.4826 * float(np.median(np.abs(values - median)))
    standard = float(np.std(values, ddof=1)) if values.size > 1 else 0.0
    return max(mad_scale, standard * 0.50, 1.0e-8)


def _symbol_pressure(
    frame: pd.DataFrame, decision_time: pd.Timestamp
) -> tuple[float, float] | None:
    if "open_time" not in frame.columns or "close" not in frame.columns:
        return None
    flow_columns = _flow_columns(frame)
    if flow_columns is None:
        return None

    open_times = _open_times_utc(frame["open_time"])
    completed_mask = (open_times + pd.Timedelta(hours=8)) <= decision_time
    completed_positions = np.flatnonzero(completed_mask.fillna(False).to_numpy())
    required_rows = REFERENCE_BARS + FORMATION_BARS + 1
    if completed_positions.size < required_rows:
        return None

    completed_times = open_times.iloc[completed_positions]
    sort_order = np.argsort(completed_times.astype("int64").to_numpy(), kind="stable")
    positions = completed_positions[sort_order][-required_rows:]
    rows = frame.iloc[positions]

    closes = pd.to_numeric(rows["close"], errors="coerce").to_numpy(dtype=float)
    buy_column, total_column = flow_columns
    taker_buy = pd.to_numeric(rows[buy_column], errors="coerce").to_numpy(dtype=float)
    total_volume = pd.to_numeric(rows[total_column], errors="coerce").to_numpy(dtype=float)
    if (
        not np.all(np.isfinite(closes))
        or not np.all(np.isfinite(taker_buy))
        or not np.all(np.isfinite(total_volume))
        or np.any(closes <= 0.0)
        or np.any(total_volume <= 0.0)
    ):
        return None

    log_prices = np.log(closes)
    returns = np.diff(log_prices)
    historical_returns = returns[-(REFERENCE_BARS + FORMATION_BARS) : -FORMATION_BARS]
    recent_return = float(log_prices[-1] - log_prices[-1 - FORMATION_BARS])
    return_scale = max(
        float(np.std(historical_returns, ddof=1)) * math.sqrt(FORMATION_BARS),
        1.0e-8,
    )
    price_z = float(np.clip(recent_return / return_scale, -5.0, 5.0))

    bar_imbalance = np.clip(2.0 * taker_buy / total_volume - 1.0, -1.0, 1.0)
    historical_flow = bar_imbalance[-(REFERENCE_BARS + FORMATION_BARS) : -FORMATION_BARS]
    recent_flow = bar_imbalance[-FORMATION_BARS:]
    flow_surprise = float(np.mean(recent_flow) - np.median(historical_flow))
    flow_scale = _robust_scale(historical_flow) / math.sqrt(FORMATION_BARS)
    flow_z = float(np.clip(flow_surprise / flow_scale, -5.0, 5.0))
    return price_z, flow_z


class CalendarBoundaryFlowReversal:
    """Fade confirmed one-sided flow only around a recurring month change."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed
        decision_time = _as_utc_timestamp(context.decision_time)
        month_start = decision_time.normalize().replace(day=1)
        next_month_start = month_start + pd.offsets.MonthBegin(1)
        hours_after_start = (decision_time - month_start).total_seconds() / 3600.0
        hours_before_next = (next_month_start - decision_time).total_seconds() / 3600.0
        in_boundary_window = (
            hours_after_start < POST_BOUNDARY_HOURS
            or 0.0 < hours_before_next <= PRE_BOUNDARY_HOURS
        )
        if not in_boundary_window:
            return {}

        confirmed: list[tuple[str, float]] = []
        for symbol in sorted(set(context.eligible_symbols)):
            frame = context.bars.get(symbol)
            if frame is None or len(frame) == 0:
                continue
            state = _symbol_pressure(frame, decision_time)
            if state is None:
                continue
            price_z, flow_z = state
            if (
                abs(price_z) < CONFIRMATION_Z
                or abs(flow_z) < CONFIRMATION_Z
                or price_z * flow_z <= 0.0
            ):
                continue
            pressure = 0.50 * (price_z + flow_z)
            if math.isfinite(pressure):
                confirmed.append((symbol, pressure))

        long_candidates = sorted(
            ((symbol, pressure) for symbol, pressure in confirmed if pressure < 0.0),
            key=lambda item: (item[1], item[0]),
        )[:NAMES_PER_SIDE]
        short_candidates = sorted(
            ((symbol, pressure) for symbol, pressure in confirmed if pressure > 0.0),
            key=lambda item: (-item[1], item[0]),
        )[:NAMES_PER_SIDE]
        if len(long_candidates) < 2 or len(short_candidates) < 2:
            return {}

        side_gross = TARGET_GROSS / 2.0
        long_weight = side_gross / len(long_candidates)
        short_weight = -side_gross / len(short_candidates)
        weights = {symbol: long_weight for symbol, _ in long_candidates}
        weights.update({symbol: short_weight for symbol, _ in short_candidates})
        return {symbol: weights[symbol] for symbol in sorted(weights)}


def build_strategy() -> CalendarBoundaryFlowReversal:
    return CalendarBoundaryFlowReversal()
