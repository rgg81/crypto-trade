"""Transparent directed cross-coin weekly response-delay baseline."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


BAR_HOURS = 8
CALIBRATION_WEEKS = 20
MINIMUM_PAIR_OBSERVATIONS = 12
MINIMUM_LAG_CORRELATION = 0.15
MINIMUM_DIRECTIONAL_EDGE = 0.05
SHOCK_Z_THRESHOLD = 0.75
UNDERRESPONSE_RATIO = 0.50
OVERSHOOT_RATIO = 1.25
OVERSHOOT_SCALE = 0.50
MAXIMUM_PAIRS = 4
MAXIMUM_SNAPSHOT_STALENESS_HOURS = 12
REBALANCE_DAYS = 7
TARGET_GROSS = 0.48
MAXIMUM_SYMBOL_WEIGHT = 0.08


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _weekly_prices(
    frame: pd.DataFrame,
    cutoffs: pd.DatetimeIndex,
    decision_time: pd.Timestamp,
) -> np.ndarray:
    """Return causal as-of closes at fixed cutoffs, or NaN for stale snapshots."""
    if "open_time" not in frame.columns or "close" not in frame.columns:
        return np.full(len(cutoffs), np.nan, dtype=float)

    open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    completion_times = open_times + pd.Timedelta(hours=BAR_HOURS)
    closes = pd.to_numeric(frame["close"], errors="coerce")

    # This mask is the explicit completed-8h-bar gate.
    valid = (
        completion_times.notna()
        & (completion_times <= decision_time)
        & np.isfinite(closes.to_numpy(dtype=float, na_value=np.nan))
        & (closes > 0.0)
    )
    if not bool(valid.any()):
        return np.full(len(cutoffs), np.nan, dtype=float)

    history = pd.DataFrame(
        {
            "completion_time": completion_times.loc[valid],
            "close": closes.loc[valid].astype(float),
        }
    )
    history = history.sort_values("completion_time", kind="mergesort")
    history = history.drop_duplicates("completion_time", keep="last")

    times_ns = history["completion_time"].astype("int64").to_numpy()
    closes_np = history["close"].to_numpy(dtype=float)
    cutoff_ns = cutoffs.astype("int64").to_numpy()
    locations = np.searchsorted(times_ns, cutoff_ns, side="right") - 1

    result = np.full(len(cutoffs), np.nan, dtype=float)
    available = locations >= 0
    result[available] = closes_np[locations[available]]

    selected_times = np.full(len(cutoffs), np.iinfo(np.int64).min, dtype=np.int64)
    selected_times[available] = times_ns[locations[available]]
    maximum_age_ns = int(
        pd.Timedelta(hours=MAXIMUM_SNAPSHOT_STALENESS_HOURS).value
    )
    stale = (~available) | ((cutoff_ns - selected_times) > maximum_age_ns)
    result[stale] = np.nan
    return result


def _correlation(left: np.ndarray, right: np.ndarray) -> tuple[float, int]:
    valid = np.isfinite(left) & np.isfinite(right)
    observations = int(valid.sum())
    if observations < MINIMUM_PAIR_OBSERVATIONS:
        return np.nan, observations
    x = left[valid]
    y = right[valid]
    x_std = float(np.std(x, ddof=1))
    y_std = float(np.std(y, ddof=1))
    if x_std <= 1.0e-12 or y_std <= 1.0e-12:
        return np.nan, observations
    return float(np.corrcoef(x, y)[0, 1]), observations


def _zscore_latest(values: np.ndarray) -> float:
    history = values[:-1]
    history = history[np.isfinite(history)]
    latest = float(values[-1])
    if len(history) < MINIMUM_PAIR_OBSERVATIONS or not np.isfinite(latest):
        return np.nan
    scale = float(np.std(history, ddof=1))
    if scale <= 1.0e-12:
        return np.nan
    return (latest - float(np.mean(history))) / scale


def _bounded_weights(
    symbols: list[str],
    raw_signals: Mapping[str, float],
) -> dict[str, float]:
    raw = np.array([float(raw_signals.get(symbol, 0.0)) for symbol in symbols])
    raw[~np.isfinite(raw)] = 0.0
    if not np.any(np.abs(raw) > 1.0e-12):
        return {}

    # Centering is only an exposure control; directed pair scores create raw_signals.
    weights = raw - float(np.mean(raw))
    gross = float(np.sum(np.abs(weights)))
    if gross <= 1.0e-12:
        return {}
    weights *= TARGET_GROSS / gross

    largest = float(np.max(np.abs(weights)))
    if largest > MAXIMUM_SYMBOL_WEIGHT:
        weights *= MAXIMUM_SYMBOL_WEIGHT / largest

    # Scaling preserves zero net. A final defensive scale enforces every hard cap.
    gross = float(np.sum(np.abs(weights)))
    net = float(np.sum(weights))
    scale = min(
        1.0,
        0.8 / gross if gross > 0.0 else 1.0,
        0.20 / abs(net) if abs(net) > 0.0 else 1.0,
        MAXIMUM_SYMBOL_WEIGHT / float(np.max(np.abs(weights))),
    )
    weights *= scale
    return {
        symbol: float(weight)
        for symbol, weight in zip(symbols, weights)
        if np.isfinite(weight) and abs(weight) > 1.0e-12
    }


class DirectedWeeklyResponseDelay:
    def target_weights(
        self,
        context: object,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        del seed  # The baseline is deterministic without random tie-breaking.
        decision_time = _utc_timestamp(context.decision_time)
        last_rebalance = getattr(self, "_last_rebalance", None)
        if (
            last_rebalance is not None
            and decision_time - last_rebalance
            < pd.Timedelta(days=REBALANCE_DAYS)
        ):
            return None
        self._last_rebalance = decision_time

        symbols = sorted({str(symbol) for symbol in context.eligible_symbols})
        if len(symbols) < 2:
            return {}

        # Twenty completed weekly returns plus one reserved current shock require
        # twenty-two causal price snapshots.
        snapshot_count = CALIBRATION_WEEKS + 2
        cutoffs = pd.DatetimeIndex(
            [
                decision_time - pd.Timedelta(days=REBALANCE_DAYS * offset)
                for offset in range(snapshot_count - 1, -1, -1)
            ]
        )
        prices = np.column_stack(
            [
                _weekly_prices(context.bars.get(symbol), cutoffs, decision_time)
                if context.bars.get(symbol) is not None
                else np.full(snapshot_count, np.nan, dtype=float)
                for symbol in symbols
            ]
        )
        with np.errstate(divide="ignore", invalid="ignore"):
            weekly_returns = prices[1:] / prices[:-1] - 1.0
        weekly_returns[~np.isfinite(weekly_returns)] = np.nan

        historical = weekly_returns[:-1]
        current = weekly_returns[-1]
        zscores = np.array(
            [_zscore_latest(weekly_returns[:, index]) for index in range(len(symbols))]
        )

        pairs: list[tuple[float, str, str, int, int]] = []
        for leader_index, leader in enumerate(symbols):
            for follower_index, follower in enumerate(symbols):
                if leader_index == follower_index:
                    continue
                forward, observations = _correlation(
                    historical[:-1, leader_index],
                    historical[1:, follower_index],
                )
                reverse, _ = _correlation(
                    historical[:-1, follower_index],
                    historical[1:, leader_index],
                )
                if not np.isfinite(forward) or not np.isfinite(reverse):
                    continue
                directional_edge = forward - reverse
                if (
                    observations >= MINIMUM_PAIR_OBSERVATIONS
                    and forward >= MINIMUM_LAG_CORRELATION
                    and directional_edge >= MINIMUM_DIRECTIONAL_EDGE
                ):
                    pairs.append(
                        (
                            float(forward + directional_edge),
                            leader,
                            follower,
                            leader_index,
                            follower_index,
                        )
                    )

        # Highest directed score wins; symbols provide deterministic tie-breaking.
        pairs.sort(key=lambda item: (-item[0], item[1], item[2]))
        chosen_followers: set[str] = set()
        raw_signals: dict[str, float] = {}
        for score, _, follower, leader_index, follower_index in pairs:
            if follower in chosen_followers:
                continue
            leader_z = float(zscores[leader_index])
            follower_z = float(zscores[follower_index])
            if (
                not np.isfinite(leader_z)
                or not np.isfinite(follower_z)
                or abs(leader_z) < SHOCK_Z_THRESHOLD
            ):
                continue

            if (
                np.sign(follower_z) == np.sign(leader_z)
                and abs(follower_z) > OVERSHOOT_RATIO * abs(leader_z)
            ):
                signal = -OVERSHOOT_SCALE * score * follower_z
            elif (
                np.sign(follower_z) != np.sign(leader_z)
                or abs(follower_z) < UNDERRESPONSE_RATIO * abs(leader_z)
            ):
                signal = score * leader_z
            else:
                continue

            if np.isfinite(signal) and abs(signal) > 1.0e-12:
                raw_signals[follower] = float(signal)
                chosen_followers.add(follower)
            if len(chosen_followers) >= MAXIMUM_PAIRS:
                break

        return _bounded_weights(symbols, raw_signals)


def build_strategy() -> DirectedWeeklyResponseDelay:
    return DirectedWeeklyResponseDelay()
