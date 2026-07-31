"""Causal correlation/dispersion regime allocator for Team 07."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


BAR_HOURS = 8
REBALANCE_WEEKDAY = 0
REBALANCE_HOUR_UTC = 0
MIN_SYMBOLS = 6
MIN_COMMON_RETURNS = 168
CORRELATION_LOOKBACK_BARS = 126
DISPERSION_FAST_BARS = 21
DISPERSION_SLOW_BARS = 126
REGIME_LAG_BARS = 1
SIGNAL_LOOKBACK_BARS = 42
SIGNAL_SKIP_BARS = 2
TREND_LOOKBACK_BARS = 63

CORRELATION_GATE_LOW = 0.25
CORRELATION_GATE_HIGH = 0.60
DISPERSION_GATE_LOW = 0.90
DISPERSION_GATE_HIGH = 1.50
COMPRESSION_GATE_LOW = 0.70
COMPRESSION_GATE_HIGH = 1.05

MAX_RELATIVE_VALUE_GROSS = 0.72
MAX_DIRECTIONAL_NET = 0.18
TREND_TANH_SCALE = 1.50
MIN_BETA = 0.25
MAX_BETA = 2.00
MAX_ABSOLUTE_WEIGHT = 0.16


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _open_times_utc(values: pd.Series) -> pd.DatetimeIndex:
    """Parse textual or epoch open times without assuming an epoch unit."""
    if pd.api.types.is_numeric_dtype(values.dtype):
        numeric = pd.to_numeric(values, errors="coerce")
        finite = numeric[np.isfinite(numeric)]
        if finite.empty:
            return pd.DatetimeIndex(pd.to_datetime(values, utc=True, errors="coerce"))
        magnitude = float(np.nanmedian(np.abs(finite.to_numpy(dtype=float))))
        if magnitude >= 1.0e17:
            unit = "ns"
        elif magnitude >= 1.0e14:
            unit = "us"
        elif magnitude >= 1.0e11:
            unit = "ms"
        else:
            unit = "s"
        parsed = pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
    else:
        parsed = pd.to_datetime(values, utc=True, errors="coerce")
    return pd.DatetimeIndex(parsed)


def _completed_closes(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.Series:
    if not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)

    local = frame.loc[:, ["open_time", "close"]].copy()
    open_times = _open_times_utc(local["open_time"])
    closes = pd.to_numeric(local["close"], errors="coerce").to_numpy(dtype=float)
    complete = open_times + pd.Timedelta(hours=BAR_HOURS) <= decision_time
    valid = complete & open_times.notna() & np.isfinite(closes) & (closes > 0.0)
    if not np.any(valid):
        return pd.Series(dtype=float)

    series = pd.Series(closes[valid], index=open_times[valid], dtype=float)
    return series.groupby(level=0).last().sort_index()


def _linear_gate(value: float, low: float, high: float) -> float:
    return float(np.clip((value - low) / (high - low), 0.0, 1.0))


class CorrelationDispersionRegimeStrategy:
    """Allocate between residual reversal, a small common tilt, and cash."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        # The formula is deterministic; seed is accepted only to satisfy the neutral API.
        _ = seed
        decision_time = _utc_timestamp(context.decision_time)
        if (
            decision_time.weekday() != REBALANCE_WEEKDAY
            or decision_time.hour != REBALANCE_HOUR_UTC
            or decision_time.minute != 0
            or decision_time.second != 0
        ):
            return None

        eligible = sorted(set(context.eligible_symbols))
        flat = {symbol: 0.0 for symbol in eligible}
        if len(eligible) < MIN_SYMBOLS:
            return flat

        close_series: dict[str, pd.Series] = {}
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            closes = _completed_closes(frame, decision_time)
            if not closes.empty:
                close_series[symbol] = closes

        if len(close_series) < MIN_SYMBOLS:
            return flat

        closes = pd.concat(close_series, axis=1).sort_index()
        log_returns = np.log(closes).diff().replace([np.inf, -np.inf], np.nan)
        sufficiently_observed = log_returns.notna().sum() >= MIN_COMMON_RETURNS
        log_returns = log_returns.loc[:, sufficiently_observed]
        if log_returns.shape[1] < MIN_SYMBOLS:
            return flat

        # A common-time panel prevents unequal missing-bar histories from driving ranks.
        returns = log_returns.dropna(how="any").tail(MIN_COMMON_RETURNS)
        if len(returns) < MIN_COMMON_RETURNS or returns.shape[1] < MIN_SYMBOLS:
            return flat

        market_returns = returns.median(axis=1)
        lagged = returns.iloc[:-REGIME_LAG_BARS]
        correlation_window = lagged.tail(CORRELATION_LOOKBACK_BARS)
        correlation_matrix = correlation_window.corr()
        upper = correlation_matrix.to_numpy(dtype=float)[
            np.triu_indices(correlation_matrix.shape[0], k=1)
        ]
        finite_correlations = upper[np.isfinite(upper)]
        if finite_correlations.size == 0:
            return flat
        median_correlation = float(np.median(finite_correlations))

        centered = lagged.sub(lagged.median(axis=1), axis=0).abs()
        dispersion = centered.median(axis=1)
        fast_dispersion = float(dispersion.tail(DISPERSION_FAST_BARS).median())
        slow_start = -(DISPERSION_FAST_BARS + DISPERSION_SLOW_BARS)
        slow_end = -DISPERSION_FAST_BARS
        slow_dispersion = float(dispersion.iloc[slow_start:slow_end].median())
        if not np.isfinite(slow_dispersion) or slow_dispersion <= 0.0:
            return flat
        dispersion_ratio = fast_dispersion / slow_dispersion

        correlation_gate = _linear_gate(
            median_correlation, CORRELATION_GATE_LOW, CORRELATION_GATE_HIGH
        )
        dispersion_gate = _linear_gate(
            dispersion_ratio, DISPERSION_GATE_LOW, DISPERSION_GATE_HIGH
        )
        relative_value_gross = (
            MAX_RELATIVE_VALUE_GROSS * correlation_gate * dispersion_gate
        )

        market_correlation_window = market_returns.loc[correlation_window.index]
        market_centered = market_correlation_window - market_correlation_window.mean()
        market_variance = float(np.dot(market_centered, market_centered))
        if not np.isfinite(market_variance) or market_variance <= 1.0e-12:
            return flat
        asset_centered = correlation_window - correlation_window.mean(axis=0)
        betas = asset_centered.mul(market_centered, axis=0).sum(axis=0) / market_variance
        betas = betas.clip(lower=MIN_BETA, upper=MAX_BETA)

        signal_end = -SIGNAL_SKIP_BARS
        signal_start = -(SIGNAL_LOOKBACK_BARS + SIGNAL_SKIP_BARS)
        signal_returns = returns.iloc[signal_start:signal_end]
        signal_market = market_returns.loc[signal_returns.index]
        residuals = signal_returns.sub(signal_market, axis=0).sub(
            signal_market.to_numpy()[:, None] * (betas.to_numpy() - 1.0), axis=1
        )
        residual_scale = residuals.std(axis=0, ddof=1) * np.sqrt(SIGNAL_LOOKBACK_BARS)
        standardized_dislocation = residuals.sum(axis=0) / residual_scale
        reversal_score = (-standardized_dislocation).replace([np.inf, -np.inf], np.nan).dropna()
        if len(reversal_score) < MIN_SYMBOLS:
            return flat

        percentile = reversal_score.rank(method="average", pct=True)
        centered_rank = percentile - percentile.mean()
        score_norm = float(centered_rank.abs().sum())
        if not np.isfinite(score_norm) or score_norm <= 1.0e-12:
            relative_value = centered_rank * 0.0
        else:
            relative_value = centered_rank * (relative_value_gross / score_norm)

        compression_gate = _linear_gate(
            COMPRESSION_GATE_HIGH - dispersion_ratio,
            0.0,
            COMPRESSION_GATE_HIGH - COMPRESSION_GATE_LOW,
        )
        trend_returns = market_returns.iloc[-(TREND_LOOKBACK_BARS + REGIME_LAG_BARS) : -REGIME_LAG_BARS]
        trend_sum = float(trend_returns.sum())
        trend_scale = float(trend_returns.std(ddof=1) * np.sqrt(TREND_LOOKBACK_BARS))
        if np.isfinite(trend_scale) and trend_scale > 1.0e-12:
            trend_signal = float(np.tanh((trend_sum / trend_scale) / TREND_TANH_SCALE))
        else:
            trend_signal = 0.0
        directional_net = (
            MAX_DIRECTIONAL_NET * correlation_gate * compression_gate * trend_signal
        )
        directional_each = directional_net / len(reversal_score)

        targets = flat.copy()
        for symbol in reversal_score.index:
            combined = float(relative_value.loc[symbol] + directional_each)
            targets[symbol] = float(
                np.clip(combined, -MAX_ABSOLUTE_WEIGHT, MAX_ABSOLUTE_WEIGHT)
            )
        return targets


def build_strategy() -> CorrelationDispersionRegimeStrategy:
    return CorrelationDispersionRegimeStrategy()
