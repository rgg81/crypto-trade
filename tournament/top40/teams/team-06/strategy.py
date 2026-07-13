"""T06-HWDS-001: hierarchical weekday differential seasonality.

The canonical evaluator supplies a freshly truncated :class:`DecisionContext`.  This module uses
only completed 8-hour transaction candles from that context and emits signed target weights.  It
does not model execution, costs, funding, membership, or PnL; those remain evaluator concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

STRATEGY_SEED: Final = 20260713
BTC_SYMBOL: Final = "BTCUSDT"
WEEKDAY_LOOKBACK_DAYS: Final = 52 * 7
WEEKDAY_HALF_LIFE: Final = 13.0
MIN_WEEKDAY_OBSERVATIONS: Final = 26
BETA_LOOKBACK_DAYS: Final = 60
MIN_BETA_OBSERVATIONS: Final = 45
COVARIATE_LOOKBACK_DAYS: Final = 20
MIN_COVARIATE_OBSERVATIONS: Final = 18
RIDGE_PENALTY: Final = 1.0
MIN_VALID_NAMES: Final = 10
K_CAP: Final = 8
GROSS_CAP: Final = 0.80
SYMBOL_CAP: Final = 0.09
VOLATILITY_FLOOR: Final = 0.01
VOLATILITY_THROTTLE: Final = 0.04
SPREAD_RAMP_START: Final = 0.003
SPREAD_RAMP_WIDTH: Final = 0.003


@dataclass(frozen=True)
class _DailyHistory:
    """Past-only daily return and completed-date quote-volume series."""

    returns: pd.Series
    quote_volume: pd.Series
    last_boundary_time: pd.Timestamp | None
    last_boundary_close: float | None


@dataclass(frozen=True)
class _SeasonalEstimate:
    """Unpooled weekday forecast and its estimation variance."""

    beta: float
    mean: float
    variance_of_mean: float


@dataclass(frozen=True)
class _CachedHistory:
    """Chronological cache containing only rows already exposed by the evaluator."""

    decision_time: pd.Timestamp
    row_count: int
    history: _DailyHistory


class HierarchicalWeekdayDifferentialSeasonality:
    """Daily HWDS target generator frozen by the team-06 research brief."""

    def __init__(self) -> None:
        self._history_cache: dict[str, _CachedHistory] = {}

    def target_weights(self, context: DecisionContext, *, seed: int) -> dict[str, float] | None:
        """Return a midnight target mapping and hold quantities at intraday decisions."""

        if int(seed) != STRATEGY_SEED:
            raise ValueError(f"T06-HWDS-001 requires seed {STRATEGY_SEED}")
        decision_time = _as_utc(context.decision_time)
        if decision_time != decision_time.floor("D"):
            return None

        eligible = tuple(sorted({str(symbol) for symbol in context.eligible_symbols}))
        if BTC_SYMBOL not in eligible:
            return {}

        histories: dict[str, _DailyHistory] = {}
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            histories[symbol] = self._history(symbol, frame, decision_time)

        btc_history = histories.get(BTC_SYMBOL)
        if btc_history is None:
            return {}

        seasonal: dict[str, _SeasonalEstimate] = {}
        for symbol in eligible:
            history = histories.get(symbol)
            if history is None:
                continue
            estimate = _seasonal_estimate(
                history.returns,
                btc_history.returns,
                decision_time,
            )
            if estimate is not None:
                seasonal[symbol] = estimate
        valid_inputs: list[tuple[str, _SeasonalEstimate, tuple[float, float, float]]] = []
        for symbol in sorted(seasonal):
            covariates = _covariates(histories[symbol], decision_time)
            if covariates is not None:
                valid_inputs.append((symbol, seasonal[symbol], covariates))
        if len(valid_inputs) < MIN_VALID_NAMES:
            return {}

        raw_means = np.asarray([estimate.mean for _, estimate, _ in valid_inputs], dtype=np.float64)
        estimation_variances = np.asarray(
            [estimate.variance_of_mean for _, estimate, _ in valid_inputs],
            dtype=np.float64,
        )
        population_mean = float(np.mean(raw_means))
        between_variance = max(
            float(np.var(raw_means, ddof=0)) - float(np.mean(estimation_variances)),
            0.0,
        )

        rows: list[tuple[str, float, float, float, float, float]] = []
        for symbol, estimate, covariates in valid_inputs:
            momentum, volatility, log_liquidity = covariates
            denominator = between_variance + estimate.variance_of_mean
            reliability = between_variance / denominator if denominator > 0.0 else 0.0
            pooled = population_mean + reliability * (estimate.mean - population_mean)
            rows.append(
                (
                    symbol,
                    pooled,
                    estimate.beta,
                    momentum,
                    volatility,
                    log_liquidity,
                )
            )

        symbols = [row[0] for row in rows]
        response = np.asarray([row[1] for row in rows], dtype=np.float64)
        raw_features = np.asarray([row[2:] for row in rows], dtype=np.float64)
        feature_matrix = np.column_stack(
            [
                np.ones(len(rows), dtype=np.float64),
                *(_robust_cross_section(raw_features[:, index]) for index in range(4)),
            ]
        )
        penalty = np.diag([0.0, RIDGE_PENALTY, RIDGE_PENALTY, RIDGE_PENALTY, RIDGE_PENALTY])
        coefficients = np.linalg.solve(
            feature_matrix.T @ feature_matrix + penalty,
            feature_matrix.T @ response,
        )
        residuals = response - feature_matrix @ coefficients
        if not np.isfinite(residuals).all():
            return {}

        signals = {symbol: float(value) for symbol, value in zip(symbols, residuals, strict=True)}
        count = len(symbols)
        selection_count = min(K_CAP, max(5, int(np.floor(0.20 * count))))
        ranked = sorted(symbols, key=lambda symbol: (signals[symbol], symbol))
        bottom = ranked[:selection_count]
        top = ranked[-selection_count:]

        spread = float(
            np.median([signals[symbol] for symbol in top])
            - np.median([signals[symbol] for symbol in bottom])
        )
        dispersion_haircut = float(
            np.clip(
                (spread - SPREAD_RAMP_START) / SPREAD_RAMP_WIDTH,
                0.0,
                1.0,
            )
        )
        volatility_by_symbol = {row[0]: float(row[4]) for row in rows}
        cross_sectional_median_volatility = float(
            np.median([volatility_by_symbol[symbol] for symbol in symbols])
        )
        volatility_throttle = (
            1.0
            if cross_sectional_median_volatility <= 0.0
            else min(1.0, VOLATILITY_THROTTLE / cross_sectional_median_volatility)
        )
        gross = GROSS_CAP * dispersion_haircut * volatility_throttle
        if not np.isfinite(gross) or gross <= 0.0:
            return {}

        sleeve_target = gross / 2.0
        long_weights = _allocate_sleeve(top, volatility_by_symbol, sleeve_target)
        short_weights = _allocate_sleeve(bottom, volatility_by_symbol, sleeve_target)
        targets = {symbol: float(long_weights[symbol]) for symbol in sorted(long_weights)}
        targets.update({symbol: -float(short_weights[symbol]) for symbol in sorted(short_weights)})
        if any(symbol not in eligible for symbol in targets):
            raise RuntimeError("internal error: ineligible target")
        values = np.asarray(list(targets.values()), dtype=np.float64)
        if not np.isfinite(values).all():
            raise RuntimeError("internal error: non-finite target")
        return targets

    def _history(
        self, symbol: str, frame: pd.DataFrame, decision_time: pd.Timestamp
    ) -> _DailyHistory:
        """Update a daily cache only across a consecutive, append-only decision boundary."""

        cached = self._history_cache.get(symbol)
        consecutive = (
            cached is not None
            and decision_time == cached.decision_time + pd.Timedelta(days=1)
            and len(frame) >= cached.row_count
        )
        if consecutive:
            history = _advance_history(cached.history, frame, decision_time)
        else:
            history = _daily_history(frame, decision_time)
        self._history_cache[symbol] = _CachedHistory(
            decision_time=decision_time,
            row_count=len(frame),
            history=history,
        )
        return history


def _as_utc(value: pd.Timestamp) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


def _daily_history(frame: pd.DataFrame, decision_time: pd.Timestamp) -> _DailyHistory:
    """Derive daily boundary returns and full-date quote volume without looking past ``t``."""

    required = {"open_time", "close", "quote_volume"}
    if not required.issubset(frame.columns):
        return _empty_history()
    # At an 8-hour cadence there can be at most three rows per UTC date.  This bounded tail
    # contains the complete 52-week requirement and avoids rescanning multi-year frames.
    maximum_required_rows = (WEEKDAY_LOOKBACK_DAYS + 2) * 3
    open_times = frame["open_time"]
    if (
        pd.api.types.is_datetime64_any_dtype(open_times.dtype)
        and open_times.is_monotonic_increasing
    ):
        timestamps = pd.DatetimeIndex(open_times)
        stop = int(timestamps.searchsorted(decision_time - pd.Timedelta(hours=8), side="right"))
        start = max(0, stop - maximum_required_rows)
        bounded = frame.iloc[start:stop]
    else:
        bounded = frame
    work = bounded.loc[:, ["open_time", "close", "quote_volume"]].copy()
    work["open_time"] = pd.to_datetime(work["open_time"], utc=True, errors="coerce")
    work = work[work["open_time"].notna()]
    work["close_time"] = work["open_time"] + pd.Timedelta(hours=8)
    # Filtering by availability precedes numeric conversion, so malformed unseen values cannot
    # influence a decision even if this helper is exercised outside the canonical truncator.
    work = work[
        (work["close_time"] <= decision_time)
        & (work["close_time"] >= decision_time - pd.Timedelta(days=WEEKDAY_LOOKBACK_DAYS + 2))
    ]
    if work.empty:
        return _empty_history()

    closes = pd.to_numeric(work["close"], errors="coerce")
    close_valid = np.isfinite(closes.to_numpy()) & (closes.to_numpy() > 0.0)
    boundary = work.loc[close_valid, ["close_time"]].copy()
    boundary["close"] = closes.loc[close_valid].to_numpy(dtype=np.float64)
    boundary = boundary[
        (boundary["close_time"].dt.hour == 0)
        & (boundary["close_time"].dt.minute == 0)
        & (boundary["close_time"].dt.second == 0)
        & (boundary["close_time"].dt.microsecond == 0)
    ].sort_values("close_time", kind="mergesort")
    boundary = boundary[~boundary["close_time"].duplicated(keep=False)]
    last_boundary_time: pd.Timestamp | None = None
    last_boundary_close: float | None = None
    if not boundary.empty:
        last_boundary_time = pd.Timestamp(boundary["close_time"].iloc[-1])
        last_boundary_close = float(boundary["close"].iloc[-1])
    if len(boundary) >= 2:
        close_times = pd.DatetimeIndex(boundary["close_time"])
        close_values = boundary["close"].to_numpy(dtype=np.float64)
        adjacent = (close_times[1:] - close_times[:-1]) == pd.Timedelta(days=1)
        return_values = np.log(close_values[1:] / close_values[:-1])
        returns = pd.Series(
            return_values[adjacent],
            index=close_times[:-1][adjacent],
            dtype=np.float64,
        )
    else:
        returns = _empty_series()

    volume = pd.to_numeric(work["quote_volume"], errors="coerce")
    volume_valid = np.isfinite(volume.to_numpy()) & (volume.to_numpy() >= 0.0)
    daily = work.loc[volume_valid, ["open_time"]].copy()
    daily["quote_volume"] = volume.loc[volume_valid].to_numpy(dtype=np.float64)
    daily["date"] = daily["open_time"].dt.floor("D")
    daily["hour"] = daily["open_time"].dt.hour
    daily = daily[
        (daily["date"] >= decision_time - pd.Timedelta(days=COVARIATE_LOOKBACK_DAYS))
        & (daily["date"] < decision_time)
        & daily["hour"].isin((0, 8, 16))
        & (daily["open_time"].dt.minute == 0)
        & (daily["open_time"].dt.second == 0)
        & (daily["open_time"].dt.microsecond == 0)
    ]
    if daily.empty:
        daily_volume = _empty_series()
    else:
        grouped = daily.groupby("date", sort=True, observed=True).agg(
            quote_volume=("quote_volume", "sum"),
            rows=("open_time", "size"),
            distinct_times=("open_time", "nunique"),
            distinct_hours=("hour", "nunique"),
        )
        grouped = grouped[
            (grouped["rows"] == 3)
            & (grouped["distinct_times"] == 3)
            & (grouped["distinct_hours"] == 3)
            & (grouped["quote_volume"] > 0.0)
        ]
        daily_volume = grouped["quote_volume"].astype(np.float64)
        daily_volume.index = pd.DatetimeIndex(daily_volume.index)
    return _DailyHistory(
        returns=returns.sort_index(),
        quote_volume=daily_volume.sort_index(),
        last_boundary_time=last_boundary_time,
        last_boundary_close=last_boundary_close,
    )


def _advance_history(
    previous: _DailyHistory,
    frame: pd.DataFrame,
    decision_time: pd.Timestamp,
) -> _DailyHistory:
    """Append one completed UTC date without repeating rolling pandas group-bys."""

    required = {"open_time", "close", "quote_volume"}
    if not required.issubset(frame.columns):
        return previous
    recent = frame.tail(3).loc[:, ["open_time", "close", "quote_volume"]].copy()
    recent["open_time"] = pd.to_datetime(recent["open_time"], utc=True, errors="coerce")
    recent = recent[recent["open_time"].notna()]
    recent["close"] = pd.to_numeric(recent["close"], errors="coerce")
    recent["quote_volume"] = pd.to_numeric(recent["quote_volume"], errors="coerce")

    current_boundary = recent[recent["open_time"] == decision_time - pd.Timedelta(hours=8)]
    current_close: float | None = None
    if len(current_boundary) == 1:
        candidate = float(current_boundary["close"].iloc[0])
        if np.isfinite(candidate) and candidate > 0.0:
            current_close = candidate

    returns = previous.returns
    return_time = decision_time - pd.Timedelta(days=1)
    if (
        current_close is not None
        and previous.last_boundary_time == return_time
        and previous.last_boundary_close is not None
    ):
        new_return = pd.Series(
            [np.log(current_close / previous.last_boundary_close)],
            index=pd.DatetimeIndex([return_time]),
            dtype=np.float64,
        )
        returns = pd.concat([returns, new_return])
    returns = returns[~returns.index.duplicated(keep="last")]
    returns = returns[
        (returns.index >= decision_time - pd.Timedelta(days=WEEKDAY_LOOKBACK_DAYS))
        & (returns.index < decision_time)
    ].sort_index()
    quote_volume = previous.quote_volume
    volume_date = decision_time - pd.Timedelta(days=1)
    completed = recent[
        recent["open_time"].isin([volume_date + pd.Timedelta(hours=hour) for hour in (0, 8, 16)])
    ]
    if (
        len(completed) == 3
        and completed["open_time"].nunique() == 3
        and np.isfinite(completed["quote_volume"].to_numpy(dtype=np.float64)).all()
        and (completed["quote_volume"] >= 0.0).all()
    ):
        total_volume = float(completed["quote_volume"].sum())
        if total_volume > 0.0:
            new_volume = pd.Series(
                [total_volume],
                index=pd.DatetimeIndex([volume_date]),
                dtype=np.float64,
            )
            quote_volume = pd.concat([quote_volume, new_volume])
    quote_volume = quote_volume[~quote_volume.index.duplicated(keep="last")]
    quote_volume = quote_volume[
        (quote_volume.index >= decision_time - pd.Timedelta(days=COVARIATE_LOOKBACK_DAYS))
        & (quote_volume.index < decision_time)
    ].sort_index()
    return _DailyHistory(
        returns=returns,
        quote_volume=quote_volume,
        last_boundary_time=(
            decision_time if current_close is not None else previous.last_boundary_time
        ),
        last_boundary_close=(
            current_close if current_close is not None else previous.last_boundary_close
        ),
    )


def _empty_history() -> _DailyHistory:
    return _DailyHistory(
        returns=_empty_series(),
        quote_volume=_empty_series(),
        last_boundary_time=None,
        last_boundary_close=None,
    )


def _empty_series() -> pd.Series:
    return pd.Series(index=pd.DatetimeIndex([], tz="UTC"), dtype=np.float64)


def _seasonal_estimate(
    asset_returns: pd.Series,
    btc_returns: pd.Series,
    decision_time: pd.Timestamp,
) -> _SeasonalEstimate | None:
    beta_start = decision_time - pd.Timedelta(days=BETA_LOOKBACK_DAYS)
    beta_pairs = pd.concat(
        [asset_returns.rename("asset"), btc_returns.rename("btc")], axis=1, join="inner"
    ).dropna()
    beta_pairs = beta_pairs[(beta_pairs.index >= beta_start) & (beta_pairs.index < decision_time)]
    if len(beta_pairs) < MIN_BETA_OBSERVATIONS:
        return None
    asset_values = beta_pairs["asset"].to_numpy(dtype=np.float64)
    btc_values = beta_pairs["btc"].to_numpy(dtype=np.float64)
    btc_centered = btc_values - float(np.mean(btc_values))
    denominator = float(btc_centered @ btc_centered)
    if denominator <= 0.0 or not np.isfinite(denominator):
        return None
    asset_centered = asset_values - float(np.mean(asset_values))
    beta = float((asset_centered @ btc_centered) / denominator)
    if not np.isfinite(beta):
        return None

    weekday_pairs = pd.concat(
        [asset_returns.rename("asset"), btc_returns.rename("btc")], axis=1, join="inner"
    ).dropna()
    weekday_pairs = weekday_pairs[
        (weekday_pairs.index >= decision_time - pd.Timedelta(days=WEEKDAY_LOOKBACK_DAYS))
        & (weekday_pairs.index <= decision_time - pd.Timedelta(days=1))
        & (weekday_pairs.index.weekday == decision_time.weekday())
    ].sort_index()
    if len(weekday_pairs) < MIN_WEEKDAY_OBSERVATIONS:
        return None
    residuals = weekday_pairs["asset"].to_numpy(dtype=np.float64) - beta * weekday_pairs[
        "btc"
    ].to_numpy(dtype=np.float64)
    ages = np.arange(len(residuals) - 1, -1, -1, dtype=np.float64)
    weights = np.power(2.0, -ages / WEEKDAY_HALF_LIFE)
    weight_sum = float(np.sum(weights))
    weight_square_sum = float(weights @ weights)
    mean = float(weights @ residuals / weight_sum)
    variance_denominator = weight_sum - weight_square_sum / weight_sum
    if variance_denominator <= 0.0:
        return None
    sample_variance = float(weights @ np.square(residuals - mean) / variance_denominator)
    effective_count = weight_sum * weight_sum / weight_square_sum
    variance_of_mean = max(sample_variance, 0.0) / effective_count
    if not np.isfinite(mean) or not np.isfinite(variance_of_mean):
        return None
    return _SeasonalEstimate(beta=beta, mean=mean, variance_of_mean=variance_of_mean)


def _covariates(
    history: _DailyHistory, decision_time: pd.Timestamp
) -> tuple[float, float, float] | None:
    start = decision_time - pd.Timedelta(days=COVARIATE_LOOKBACK_DAYS)
    returns = history.returns[
        (history.returns.index >= start) & (history.returns.index < decision_time)
    ]
    volumes = history.quote_volume[
        (history.quote_volume.index >= start) & (history.quote_volume.index < decision_time)
    ]
    if len(returns) < MIN_COVARIATE_OBSERVATIONS or len(volumes) < MIN_COVARIATE_OBSERVATIONS:
        return None
    return_values = returns.to_numpy(dtype=np.float64)
    volume_values = volumes.to_numpy(dtype=np.float64)
    if not np.isfinite(return_values).all() or not np.isfinite(volume_values).all():
        return None
    median_volume = float(np.median(volume_values))
    if median_volume <= 0.0:
        return None
    momentum = float(np.sum(return_values))
    volatility = float(np.std(return_values, ddof=1))
    log_liquidity = float(np.log(median_volume))
    if not np.isfinite([momentum, volatility, log_liquidity]).all():
        return None
    return momentum, volatility, log_liquidity


def _robust_cross_section(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=np.float64)
    median = float(np.median(values))
    median_absolute_deviation = float(np.median(np.abs(values - median)))
    scale = 1.4826 * median_absolute_deviation
    if scale == 0.0:
        scale = float(np.std(values, ddof=0))
    if scale == 0.0:
        return np.zeros_like(values)
    return np.clip((values - median) / scale, -5.0, 5.0)


def _allocate_sleeve(
    symbols: list[str],
    volatility_by_symbol: dict[str, float],
    target: float,
) -> dict[str, float]:
    """Inverse-volatility water fill with a deterministic per-name cap."""

    ordered = sorted(symbols)
    if not ordered or target <= 0.0:
        return {symbol: 0.0 for symbol in ordered}
    if target > len(ordered) * SYMBOL_CAP + 1e-12:
        raise ValueError("sleeve target exceeds aggregate symbol capacity")
    inverse_volatility = {
        symbol: 1.0 / max(float(volatility_by_symbol[symbol]), VOLATILITY_FLOOR)
        for symbol in ordered
    }
    allocation = {symbol: 0.0 for symbol in ordered}
    active = ordered.copy()
    remaining = float(target)
    while active:
        denominator = float(sum(inverse_volatility[symbol] for symbol in active))
        provisional = {
            symbol: remaining * inverse_volatility[symbol] / denominator for symbol in active
        }
        capped = [symbol for symbol in active if provisional[symbol] > SYMBOL_CAP]
        if not capped:
            for symbol in active:
                allocation[symbol] = provisional[symbol]
            remaining = 0.0
            break
        for symbol in capped:
            allocation[symbol] = SYMBOL_CAP
            remaining -= SYMBOL_CAP
        active = [symbol for symbol in active if symbol not in set(capped)]
    if abs(remaining) > 1e-12:
        raise RuntimeError("unable to allocate complete sleeve")
    # Remove the last few ulps of summation drift while preserving the cap and symbol order.
    difference = target - float(sum(allocation.values()))
    if difference != 0.0:
        for symbol in ordered:
            candidate = allocation[symbol] + difference
            if -1e-15 <= candidate <= SYMBOL_CAP + 1e-15:
                allocation[symbol] = min(SYMBOL_CAP, max(0.0, candidate))
                break
    return allocation


def build_strategy() -> HierarchicalWeekdayDifferentialSeasonality:
    """Return one fresh frozen T06-HWDS-001 strategy instance."""

    return HierarchicalWeekdayDifferentialSeasonality()
