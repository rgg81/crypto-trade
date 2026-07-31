"""Causal cross-sectional drawdown recovery-asymmetry baseline."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


PEAK_LOOKBACK_BARS = 252
RECOVERY_WINDOW_BARS = 36
CONFIRMATION_WINDOW_BARS = 12
MIN_HISTORY_BARS = 252
REBALANCE_WEEKDAY = 0
REBALANCE_HOUR_UTC = 0
DEPTH_FLOOR = 0.03
LONG_RECOVERY_MIN = 0.012
LONG_CONFIRMATION_MIN = 0.004
LONG_TROUGH_LIFT_MIN = 0.015
SHORT_RECOVERY_MAX = -0.008
SHORT_CONFIRMATION_MAX = -0.003
SHORT_TROUGH_GAP_MAX = 0.012
MAX_NAMES_PER_SIDE = 3
MIN_NAMES_PER_SIDE = 2
TARGET_GROSS = 1.0


def _as_utc(values: pd.Series) -> pd.Series:
    """Parse datetime-like or common epoch-valued open times as UTC."""
    if pd.api.types.is_numeric_dtype(values):
        numeric = pd.to_numeric(values, errors="coerce")
        finite = numeric[np.isfinite(numeric)]
        if finite.empty:
            return pd.to_datetime(values, utc=True, errors="coerce")
        scale = float(np.nanmedian(np.abs(finite.to_numpy(dtype=float))))
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


def _decision_time_utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _window_change_slope(values: np.ndarray) -> float:
    """OLS slope expressed as fitted total change across the supplied window."""
    if values.size < 2 or not np.isfinite(values).all():
        return float("nan")
    x = np.arange(values.size, dtype=float)
    centered_x = x - x.mean()
    denominator = float(np.dot(centered_x, centered_x))
    if denominator <= 0.0:
        return float("nan")
    slope_per_bar = float(np.dot(centered_x, values - values.mean()) / denominator)
    return slope_per_bar * float(values.size - 1)


def _completed_closes(frame: pd.DataFrame, decision_time: pd.Timestamp) -> np.ndarray:
    if frame is None or "open_time" not in frame.columns or "close" not in frame.columns:
        return np.asarray([], dtype=float)

    local = frame.loc[:, ["open_time", "close"]].copy()
    local["open_time"] = _as_utc(local["open_time"])
    local["close"] = pd.to_numeric(local["close"], errors="coerce")
    local = local.dropna(subset=["open_time", "close"])
    local = local[np.isfinite(local["close"]) & (local["close"] > 0.0)]
    local = local[local["open_time"] + pd.Timedelta(hours=8) <= decision_time]
    local = local.sort_values("open_time").drop_duplicates("open_time", keep="last")
    if len(local) < MIN_HISTORY_BARS:
        return np.asarray([], dtype=float)
    return local["close"].to_numpy(dtype=float)[-PEAK_LOOKBACK_BARS:]


def _geometry(closes: np.ndarray) -> dict[str, float] | None:
    if closes.size < MIN_HISTORY_BARS or not np.isfinite(closes).all():
        return None

    peak = float(np.max(closes))
    if not np.isfinite(peak) or peak <= 0.0:
        return None

    drawdown_path = closes / peak - 1.0
    current_drawdown = float(drawdown_path[-1])
    depth = max(0.0, -current_drawdown)

    peak_locations = np.flatnonzero(closes >= peak * (1.0 - 1.0e-12))
    if peak_locations.size == 0:
        return None
    duration = float((closes.size - 1) - int(peak_locations[-1]))
    duration_fraction = duration / float(closes.size - 1)

    recovery_path = drawdown_path[-RECOVERY_WINDOW_BARS:]
    confirmation_path = drawdown_path[-CONFIRMATION_WINDOW_BARS:]
    recovery_slope = _window_change_slope(recovery_path)
    confirmation_slope = _window_change_slope(confirmation_path)
    trough_gap = float(current_drawdown - np.min(recovery_path))

    if not np.isfinite([recovery_slope, confirmation_slope, trough_gap]).all():
        return None
    return {
        "depth": depth,
        "duration": duration_fraction,
        "recovery_slope": recovery_slope,
        "confirmation_slope": confirmation_slope,
        "trough_gap": max(0.0, trough_gap),
    }


class DrawdownRecoveryAsymmetryStrategy:
    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        # The strategy is intentionally deterministic; seed is accepted for API parity.
        _ = seed
        decision_time = _decision_time_utc(context.decision_time)
        if (
            decision_time.weekday() != REBALANCE_WEEKDAY
            or decision_time.hour != REBALANCE_HOUR_UTC
            or decision_time.minute != 0
        ):
            return None

        rows: list[dict[str, float | str]] = []
        for symbol in sorted(str(item) for item in context.eligible_symbols):
            frame = context.bars.get(symbol)
            closes = _completed_closes(frame, decision_time)
            metrics = _geometry(closes)
            if metrics is not None:
                rows.append({"symbol": symbol, **metrics})

        if len(rows) < 2 * MIN_NAMES_PER_SIDE:
            return {}

        cross_section = pd.DataFrame(rows).set_index("symbol").sort_index()
        for column in ("depth", "duration", "recovery_slope", "trough_gap"):
            cross_section[f"{column}_rank"] = cross_section[column].rank(
                method="average", pct=True
            )

        # Depth and duration alter conviction only inside recovery-defined states.
        cross_section["long_score"] = (
            0.55 * cross_section["recovery_slope_rank"]
            + 0.20 * cross_section["trough_gap_rank"]
            + 0.15 * cross_section["depth_rank"]
            + 0.10 * cross_section["duration_rank"]
        )
        cross_section["short_score"] = (
            0.55 * (1.0 - cross_section["recovery_slope_rank"])
            + 0.15 * (1.0 - cross_section["trough_gap_rank"])
            + 0.20 * cross_section["depth_rank"]
            + 0.10 * cross_section["duration_rank"]
        )

        long_pool = cross_section[
            (cross_section["depth"] >= DEPTH_FLOOR)
            & (cross_section["recovery_slope"] >= LONG_RECOVERY_MIN)
            & (cross_section["confirmation_slope"] >= LONG_CONFIRMATION_MIN)
            & (cross_section["trough_gap"] >= LONG_TROUGH_LIFT_MIN)
        ]
        short_pool = cross_section[
            (cross_section["depth"] >= DEPTH_FLOOR)
            & (cross_section["recovery_slope"] <= SHORT_RECOVERY_MAX)
            & (cross_section["confirmation_slope"] <= SHORT_CONFIRMATION_MAX)
            & (cross_section["trough_gap"] <= SHORT_TROUGH_GAP_MAX)
        ]

        longs = sorted(
            long_pool.index,
            key=lambda symbol: (-float(long_pool.at[symbol, "long_score"]), symbol),
        )[:MAX_NAMES_PER_SIDE]
        shorts = sorted(
            short_pool.index,
            key=lambda symbol: (-float(short_pool.at[symbol, "short_score"]), symbol),
        )[:MAX_NAMES_PER_SIDE]
        if len(longs) < MIN_NAMES_PER_SIDE or len(shorts) < MIN_NAMES_PER_SIDE:
            return {}

        side_gross = TARGET_GROSS / 2.0
        weights = {symbol: side_gross / len(longs) for symbol in longs}
        weights.update({symbol: -side_gross / len(shorts) for symbol in shorts})
        return weights


def build_strategy() -> DrawdownRecoveryAsymmetryStrategy:
    return DrawdownRecoveryAsymmetryStrategy()
