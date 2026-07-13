"""Frozen team-03 Residual Tail Asymmetry target strategy.

The strategy consumes only closed transaction-bar ``close`` prices, the point-in-time
``eligible_symbols`` sequence, and the UTC decision calendar.  Execution, funding, costs,
participation, and membership exits remain entirely evaluator-owned.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

SEED = 20260713
INTERVAL = pd.Timedelta(hours=8)
LOOKBACK = pd.Timedelta(days=112)
MOMENTUM_LOOKBACK = pd.Timedelta(days=28)

TAIL_THRESHOLD = 2.0
TAIL_BLEND = 0.75
WINDOWS = (84, 168, 336)
SLEEVE_SIZE = 6
HYSTERESIS_BUFFER = 3
VOLATILITY_TARGET = 0.30

MIN_FACTOR_OBSERVATIONS = 252
FACTOR_VARIANCE_FLOOR = 1e-10
ROBUST_SCALE_FLOOR = 1e-6
OLS_CLIP_MULTIPLIER = 6.0
Z_CLIP = 8.0
TAIL_DENOMINATOR_FLOOR = 0.05
TAIL_COUNT_SMOOTHING = 2.0
RIDGE_PENALTY = 1.0

SLEEVE_GROSS = 0.42
ALPHA_SYMBOL_CAP = 0.08
HEDGE_GROSS_CAP = 0.08
MIN_FALLBACK_HEDGE_BETA = 0.5
MIN_COVARIANCE_ROWS = 68
COVARIANCE_WINDOW = 84
COVARIANCE_CLIP_MAD = 8.0
ANNUALIZATION_PERIODS = 1095.0


@dataclass(frozen=True)
class _FeatureRow:
    tail_score: float
    beta: float
    momentum: float
    idio_scale: float


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_monday_midnight(timestamp: pd.Timestamp) -> bool:
    return timestamp.weekday() == 0 and timestamp == timestamp.floor("D")


def _empty_returns() -> pd.Series:
    return pd.Series(dtype=float, index=pd.DatetimeIndex([], tz="UTC"))


def _closed_adjacent_returns(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.Series:
    """Return at most 336 exact-adjacent, closed 8h log returns.

    Only the timestamp column is inspected before the past-only cutoff is located.  Price columns
    in appended future rows therefore cannot influence a prior decision.
    """

    if not isinstance(frame, pd.DataFrame) or not {"open_time", "close"}.issubset(frame.columns):
        return _empty_returns()
    if frame.empty:
        return _empty_returns()

    try:
        open_times = pd.DatetimeIndex(pd.to_datetime(frame["open_time"], utc=True, errors="raise"))
    except (TypeError, ValueError):
        return _empty_returns()
    if open_times.hasnans or not open_times.is_monotonic_increasing:
        return _empty_returns()

    last_closed_open = decision_time - INTERVAL
    stop = int(open_times.searchsorted(last_closed_open, side="right"))
    # 337 closes are sufficient to form the maximum 336 returns.  Taking the tail only after
    # finding the cutoff also gives append/corrupt-future invariance.
    start = max(0, stop - (max(WINDOWS) + 1))
    if stop - start < 2:
        return _empty_returns()

    recent_times = open_times[start:stop]
    # Pandas may preserve parquet timestamps at microsecond resolution.  Normalize explicitly
    # before comparing with the nanosecond-valued Timedelta constant.
    times_ns = recent_times.to_numpy(dtype="datetime64[ns]").astype(np.int64, copy=False)
    if np.any(np.diff(times_ns) <= 0):
        return _empty_returns()
    try:
        closes = pd.to_numeric(frame["close"].iloc[start:stop], errors="coerce").to_numpy(
            dtype=float, copy=False
        )
    except (TypeError, ValueError):
        return _empty_returns()

    adjacent = np.diff(times_ns) == int(INTERVAL.value)
    valid_prices = (
        np.isfinite(closes[1:])
        & np.isfinite(closes[:-1])
        & (closes[1:] > 0.0)
        & (closes[:-1] > 0.0)
    )
    valid = adjacent & valid_prices
    if not bool(valid.any()):
        return _empty_returns()

    values = np.log(closes[1:][valid] / closes[:-1][valid])
    close_times = recent_times[1:][valid] + INTERVAL
    return pd.Series(values, index=close_times, dtype=float).sort_index()


def _scaled_mad(values: np.ndarray) -> tuple[float, float]:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    return median, max(1.4826 * mad, ROBUST_SCALE_FLOOR)


def _feature_row(
    asset_returns: pd.Series,
    factor_returns: pd.Series,
    decision_time: pd.Timestamp,
) -> _FeatureRow | None:
    lower = decision_time - LOOKBACK
    paired = pd.concat(
        [asset_returns.rename("asset"), factor_returns.rename("factor")],
        axis=1,
        join="inner",
    )
    paired = paired[(paired.index > lower) & (paired.index <= decision_time)].tail(max(WINDOWS))
    paired = paired.dropna()
    if len(paired) < MIN_FACTOR_OBSERVATIONS:
        return None

    asset = paired["asset"].to_numpy(dtype=float, copy=False)
    factor = paired["factor"].to_numpy(dtype=float, copy=False)
    if not np.isfinite(asset).all() or not np.isfinite(factor).all():
        return None

    asset_median, asset_scale = _scaled_mad(asset)
    factor_median, factor_scale = _scaled_mad(factor)
    clipped_asset = np.clip(
        asset,
        asset_median - OLS_CLIP_MULTIPLIER * asset_scale,
        asset_median + OLS_CLIP_MULTIPLIER * asset_scale,
    )
    clipped_factor = np.clip(
        factor,
        factor_median - OLS_CLIP_MULTIPLIER * factor_scale,
        factor_median + OLS_CLIP_MULTIPLIER * factor_scale,
    )
    factor_centered = clipped_factor - float(np.mean(clipped_factor))
    factor_variance = float(np.mean(factor_centered * factor_centered))
    if not math.isfinite(factor_variance) or factor_variance < FACTOR_VARIANCE_FLOOR:
        return None

    asset_mean = float(np.mean(clipped_asset))
    factor_mean = float(np.mean(clipped_factor))
    beta = float(
        np.sum(factor_centered * (clipped_asset - asset_mean))
        / np.sum(factor_centered * factor_centered)
    )
    alpha = asset_mean - beta * factor_mean
    if not math.isfinite(alpha) or not math.isfinite(beta):
        return None

    residual = asset - alpha - beta * factor
    residual_median, idio_scale = _scaled_mad(residual)
    z = np.clip((residual - residual_median) / idio_scale, -Z_CLIP, Z_CLIP)

    window_scores: list[float] = []
    paired_times = paired.index
    for window in WINDOWS:
        window_lower = decision_time - window * INTERVAL
        mask = (paired_times > window_lower) & (paired_times <= decision_time)
        window_z = z[np.asarray(mask)]
        if len(window_z) < math.ceil(0.8 * window):
            return None
        positive_excess = np.maximum(window_z - TAIL_THRESHOLD, 0.0)
        negative_excess = np.maximum(-window_z - TAIL_THRESHOLD, 0.0)
        positive_tail = float(np.mean(positive_excess * positive_excess))
        negative_tail = float(np.mean(negative_excess * negative_excess))
        asymmetry = (positive_tail - negative_tail) / (
            positive_tail + negative_tail + TAIL_DENOMINATOR_FLOOR
        )
        positive_count = int(np.count_nonzero(window_z > TAIL_THRESHOLD))
        negative_count = int(np.count_nonzero(window_z < -TAIL_THRESHOLD))
        frequency = (positive_count - negative_count) / (
            positive_count + negative_count + TAIL_COUNT_SMOOTHING
        )
        window_scores.append(TAIL_BLEND * asymmetry + (1.0 - TAIL_BLEND) * frequency)

    momentum_lower = decision_time - MOMENTUM_LOOKBACK
    momentum_returns = asset_returns[
        (asset_returns.index > momentum_lower) & (asset_returns.index <= decision_time)
    ]
    if len(momentum_returns) != 84:
        return None
    momentum = float(momentum_returns.sum())
    tail_score = -float(np.mean(window_scores))
    if not all(math.isfinite(value) for value in (tail_score, beta, momentum, idio_scale)):
        return None
    return _FeatureRow(
        tail_score=tail_score,
        beta=beta,
        momentum=momentum,
        idio_scale=idio_scale,
    )


def _average_tie_rank(values: np.ndarray) -> np.ndarray:
    """Map average-tie ranks to [-1, 1], with constants mapped exactly to zero."""

    values = np.asarray(values, dtype=float)
    count = len(values)
    if count == 0:
        return values.copy()
    if not np.isfinite(values).all():
        raise ValueError("rank input must be finite")
    if count == 1 or bool(np.all(values == values[0])):
        return np.zeros(count, dtype=float)

    order = np.argsort(values, kind="mergesort")
    raw_ranks = np.empty(count, dtype=float)
    start = 0
    while start < count:
        end = start + 1
        while end < count and values[order[end]] == values[order[start]]:
            end += 1
        # Zero-based average position, converted to the usual one-based average rank.
        average_rank = 0.5 * (start + end - 1) + 1.0
        raw_ranks[order[start:end]] = average_rank
        start = end
    return -1.0 + 2.0 * (raw_ranks - 1.0) / (count - 1.0)


def _residual_scores(features: Mapping[str, _FeatureRow]) -> dict[str, float] | None:
    symbols = sorted(features)
    if not symbols:
        return None
    tail_rank = _average_tie_rank(
        np.asarray([features[symbol].tail_score for symbol in symbols], dtype=float)
    )
    beta_rank = _average_tie_rank(
        np.asarray([features[symbol].beta for symbol in symbols], dtype=float)
    )
    momentum_rank = _average_tie_rank(
        np.asarray([features[symbol].momentum for symbol in symbols], dtype=float)
    )
    log_scale_rank = _average_tie_rank(
        np.log(np.asarray([features[symbol].idio_scale for symbol in symbols], dtype=float))
    )
    design = np.column_stack(
        [np.ones(len(symbols), dtype=float), beta_rank, momentum_rank, log_scale_rank]
    )
    penalty = np.diag([0.0, RIDGE_PENALTY, RIDGE_PENALTY, RIDGE_PENALTY])
    try:
        coefficients = np.linalg.solve(design.T @ design + penalty, design.T @ tail_rank)
    except np.linalg.LinAlgError:
        return None
    residual = tail_rank - design @ coefficients
    if not np.isfinite(residual).all():
        return None
    ranked_residual = _average_tie_rank(residual)
    return {symbol: float(ranked_residual[index]) for index, symbol in enumerate(symbols)}


def _water_fill(
    symbols: Sequence[str], strengths: Mapping[str, float], gross: float, cap: float
) -> dict[str, float] | None:
    """Deterministically allocate proportional weights subject to a per-name cap."""

    active = sorted(str(symbol) for symbol in symbols)
    if not active or gross < 0.0 or cap <= 0.0 or len(active) * cap + 1e-15 < gross:
        return None
    allocation: dict[str, float] = {}
    remaining = float(gross)
    while active:
        total_strength = float(sum(strengths[symbol] for symbol in active))
        if not math.isfinite(total_strength) or total_strength <= 0.0:
            return None
        proposals = {
            symbol: remaining * float(strengths[symbol]) / total_strength for symbol in active
        }
        capped = [symbol for symbol in active if proposals[symbol] > cap]
        if not capped:
            allocation.update(proposals)
            remaining = 0.0
            break
        for symbol in capped:
            allocation[symbol] = cap
            remaining -= cap
        capped_set = set(capped)
        active = [symbol for symbol in active if symbol not in capped_set]

    rounding_gap = gross - float(sum(allocation.values()))
    if abs(rounding_gap) > 1e-14:
        return None
    if rounding_gap != 0.0:
        for symbol in sorted(allocation):
            adjusted = allocation[symbol] + rounding_gap
            if -1e-15 <= adjusted <= cap + 1e-15:
                allocation[symbol] = min(cap, max(0.0, adjusted))
                break
    if not all(
        math.isfinite(value) and -1e-15 <= value <= cap + 1e-15 for value in allocation.values()
    ):
        return None
    return allocation


def _covariance_scale(
    raw_weights: Mapping[str, float],
    returns_by_symbol: Mapping[str, pd.Series],
    decision_time: pd.Timestamp,
) -> float | None:
    symbols = sorted(symbol for symbol, weight in raw_weights.items() if weight != 0.0)
    if not symbols:
        return None
    timestamps = pd.date_range(end=decision_time, periods=COVARIANCE_WINDOW, freq="8h")
    matrix = pd.DataFrame(
        {symbol: returns_by_symbol[symbol].reindex(timestamps) for symbol in symbols},
        index=timestamps,
    ).dropna(axis=0, how="any")
    if len(matrix) < MIN_COVARIANCE_ROWS:
        return None

    observations = matrix.to_numpy(dtype=float, copy=True)
    if not np.isfinite(observations).all():
        return None
    for column in range(observations.shape[1]):
        values = observations[:, column]
        median = float(np.median(values))
        mad = float(np.median(np.abs(values - median)))
        observations[:, column] = np.clip(
            values,
            median - COVARIANCE_CLIP_MAD * mad,
            median + COVARIANCE_CLIP_MAD * mad,
        )

    sample_covariance = np.asarray(np.cov(observations, rowvar=False, ddof=1), dtype=float)
    sample_covariance = np.atleast_2d(sample_covariance)
    if sample_covariance.shape != (len(symbols), len(symbols)):
        return None
    covariance = 0.5 * sample_covariance + 0.5 * np.diag(np.diag(sample_covariance))
    if not np.isfinite(covariance).all() or not np.allclose(
        covariance, covariance.T, rtol=0.0, atol=1e-14
    ):
        return None
    if bool(np.any(np.diag(covariance) < -1e-15)):
        return None

    weight_vector = np.asarray([raw_weights[symbol] for symbol in symbols], dtype=float)
    variance = float(weight_vector @ covariance @ weight_vector)
    if not math.isfinite(variance) or variance < -1e-15:
        return None
    variance = max(0.0, variance)
    if variance == 0.0:
        return 1.0
    annualized_volatility = math.sqrt(ANNUALIZATION_PERIODS * variance)
    if not math.isfinite(annualized_volatility) or annualized_volatility <= 0.0:
        return None
    return min(1.0, VOLATILITY_TARGET / annualized_volatility)


class ResidualTailAsymmetryStrategy:
    """Stateful weekly target generator; state contains sleeve incumbents only."""

    def __init__(self) -> None:
        self._long_incumbents: tuple[str, ...] = ()
        self._short_incumbents: tuple[str, ...] = ()

    def _flat(self) -> dict[str, float]:
        self._long_incumbents = ()
        self._short_incumbents = ()
        return {}

    def target_weights(self, context: object, *, seed: int) -> Mapping[str, float] | None:
        if seed != SEED:
            raise ValueError(f"team-03 strategy requires seed {SEED}")
        decision_time = _utc_timestamp(getattr(context, "decision_time"))
        if not _is_monday_midnight(decision_time):
            return None

        raw_eligible = tuple(str(symbol) for symbol in getattr(context, "eligible_symbols"))
        if len(raw_eligible) != len(set(raw_eligible)):
            return self._flat()
        eligible = tuple(sorted(raw_eligible))
        eligible_set = set(eligible)
        if not eligible:
            return self._flat()
        bars = getattr(context, "bars")
        if not isinstance(bars, Mapping) or set(str(symbol) for symbol in bars) != eligible_set:
            return self._flat()

        returns_by_symbol = {
            symbol: _closed_adjacent_returns(bars[symbol], decision_time) for symbol in eligible
        }
        return_frame = pd.concat(returns_by_symbol, axis=1).sort_index()
        lower = decision_time - LOOKBACK
        return_frame = return_frame[
            (return_frame.index > lower) & (return_frame.index <= decision_time)
        ]

        factor_mode = "median"
        factor_returns: pd.Series | None = None
        if "BTCUSDT" in eligible_set:
            btc_returns = returns_by_symbol["BTCUSDT"]
            btc_returns = btc_returns[
                (btc_returns.index > lower) & (btc_returns.index <= decision_time)
            ].tail(max(WINDOWS))
            if len(btc_returns) >= MIN_FACTOR_OBSERVATIONS:
                factor_mode = "btc"
                factor_returns = btc_returns

        if factor_returns is None:
            required_at_timestamp = max(5, math.ceil(len(eligible) / 2.0))
            observation_count = return_frame.notna().sum(axis=1)
            factor_returns = return_frame.median(axis=1, skipna=True)[
                observation_count >= required_at_timestamp
            ].dropna()
            factor_returns = factor_returns.tail(max(WINDOWS))
            if len(factor_returns) < MIN_FACTOR_OBSERVATIONS:
                return self._flat()

        feature_symbols = [
            symbol for symbol in eligible if factor_mode == "median" or symbol != "BTCUSDT"
        ]
        features: dict[str, _FeatureRow] = {}
        for symbol in feature_symbols:
            row = _feature_row(returns_by_symbol[symbol], factor_returns, decision_time)
            if row is not None:
                features[symbol] = row

        fallback_hedge: str | None = None
        if factor_mode == "median":
            if not features:
                return self._flat()
            fallback_hedge = min(
                features,
                key=lambda symbol: (-features[symbol].beta, symbol),
            )
            if features[fallback_hedge].beta < MIN_FALLBACK_HEDGE_BETA:
                return self._flat()

        scores = _residual_scores(features)
        if scores is None:
            return self._flat()

        excluded = {"BTCUSDT"}
        if fallback_hedge is not None:
            excluded.add(fallback_hedge)
        alpha_candidates = sorted(symbol for symbol in scores if symbol not in excluded)
        if len(alpha_candidates) < 2 * (SLEEVE_SIZE + HYSTERESIS_BUFFER):
            return self._flat()

        long_order = sorted(alpha_candidates, key=lambda symbol: (-scores[symbol], symbol))
        short_order = sorted(alpha_candidates, key=lambda symbol: (scores[symbol], symbol))
        long_keep = set(long_order[: SLEEVE_SIZE + HYSTERESIS_BUFFER])
        short_keep = set(short_order[: SLEEVE_SIZE + HYSTERESIS_BUFFER])
        longs = [
            symbol
            for symbol in long_order
            if symbol in self._long_incumbents and symbol in long_keep
        ][:SLEEVE_SIZE]
        shorts = [
            symbol
            for symbol in short_order
            if symbol in self._short_incumbents and symbol in short_keep
        ][:SLEEVE_SIZE]
        for symbol in long_order:
            if len(longs) >= SLEEVE_SIZE:
                break
            if symbol not in longs:
                longs.append(symbol)
        for symbol in short_order:
            if len(shorts) >= SLEEVE_SIZE:
                break
            if symbol not in shorts:
                shorts.append(symbol)
        if len(longs) != SLEEVE_SIZE or len(shorts) != SLEEVE_SIZE or set(longs) & set(shorts):
            return self._flat()

        inverse_scales = {symbol: 1.0 / features[symbol].idio_scale for symbol in alpha_candidates}
        inverse_scale_median = float(np.median(list(inverse_scales.values())))
        if not math.isfinite(inverse_scale_median) or inverse_scale_median <= 0.0:
            return self._flat()
        strengths = {
            symbol: min(
                2.0 * inverse_scale_median,
                max(0.5 * inverse_scale_median, inverse_scales[symbol]),
            )
            for symbol in alpha_candidates
        }
        long_weights = _water_fill(longs, strengths, SLEEVE_GROSS, ALPHA_SYMBOL_CAP)
        short_weights = _water_fill(shorts, strengths, SLEEVE_GROSS, ALPHA_SYMBOL_CAP)
        if long_weights is None or short_weights is None:
            return self._flat()

        alpha_weights = dict(long_weights)
        alpha_weights.update({symbol: -weight for symbol, weight in short_weights.items()})
        alpha_beta = float(
            sum(weight * features[symbol].beta for symbol, weight in alpha_weights.items())
        )
        hedge_symbol = "BTCUSDT" if factor_mode == "btc" else fallback_hedge
        if hedge_symbol is None or hedge_symbol not in eligible_set:
            return self._flat()
        hedge_beta = 1.0 if factor_mode == "btc" else features[hedge_symbol].beta
        if not math.isfinite(alpha_beta) or not math.isfinite(hedge_beta) or hedge_beta == 0.0:
            return self._flat()

        alpha_scale = (
            1.0
            if alpha_beta == 0.0
            else min(1.0, HEDGE_GROSS_CAP * abs(hedge_beta) / abs(alpha_beta))
        )
        raw_weights = {symbol: alpha_scale * weight for symbol, weight in alpha_weights.items()}
        hedge_weight = -alpha_scale * alpha_beta / hedge_beta
        if hedge_weight != 0.0:
            raw_weights[hedge_symbol] = hedge_weight
        if not all(math.isfinite(weight) for weight in raw_weights.values()):
            return self._flat()

        covariance_scale = _covariance_scale(raw_weights, returns_by_symbol, decision_time)
        if covariance_scale is None:
            return self._flat()
        final_weights = {
            symbol: float(weight * covariance_scale)
            for symbol, weight in raw_weights.items()
            if weight != 0.0
        }
        if (
            not all(
                symbol in eligible_set and math.isfinite(weight)
                for symbol, weight in final_weights.items()
            )
            or sum(abs(weight) for weight in final_weights.values()) > 0.92 + 1e-12
            or abs(sum(final_weights.values())) > 0.08 + 1e-12
            or any(abs(weight) > 0.08 + 1e-12 for weight in final_weights.values())
        ):
            return self._flat()

        self._long_incumbents = tuple(longs)
        self._short_incumbents = tuple(shorts)
        return final_weights


def build_strategy() -> ResidualTailAsymmetryStrategy:
    """Return one fresh frozen team-03 strategy instance."""

    return ResidualTailAsymmetryStrategy()
