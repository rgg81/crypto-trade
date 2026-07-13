"""Asymmetric Liquidity Replenishment target-weight strategy.

The implementation is deliberately stateless.  At each weekly decision it rebuilds every
rolling quantity from the past-only ``DecisionContext`` supplied by the tournament runner.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd

_EIGHT_HOURS = pd.Timedelta(hours=8)
_BTC_SYMBOL = "BTCUSDT"


@dataclasses.dataclass(frozen=True)
class _Config:
    seed: int = 20260713
    horizon: int = 6
    slope_window: int = 189
    volume_threshold: float = 1.0
    funding_penalty: float = 0.25
    beta_lookback: int = 126
    beta_minimum: int = 84
    beta_clip: float = 3.0
    beta_variance_floor: float = 1e-12
    volume_lookback: int = 63
    volume_minimum: int = 42
    volume_scale_floor: float = 0.10
    volume_clip: float = 4.0
    slope_ridge: float = 0.10
    slope_minimum_events: int = 6
    slope_denominator_floor: float = 0.25
    momentum_lookback: int = 60
    momentum_lag_bars: int = 3
    volatility_lookback: int = 63
    volatility_minimum: int = 42
    liquidity_lookback: int = 63
    tail_lookback: int = 126
    tail_minimum: int = 84
    funding_lookback_days: int = 21
    funding_minimum_events: int = 14
    funding_minimum_span_days: int = 14
    capacity_bars: int = 3
    capacity_minimum_quote_volume: float = 15_000_000.0
    minimum_names: int = 16
    sleeve_names: int = 8
    sleeve_gross: float = 0.40
    symbol_cap: float = 0.075
    risk_floor: float = 0.005


@dataclasses.dataclass(frozen=True)
class _Features:
    buy_slope: float
    sell_slope: float
    beta: float
    momentum: float
    volatility: float
    liquidity: float
    long_tail_risk: float
    short_tail_risk: float


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError("decision_time must be a valid timestamp")
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_weekly_decision(timestamp: pd.Timestamp) -> bool:
    return timestamp.weekday() == 0 and timestamp == timestamp.floor("D")


def _consecutive_run_lengths(valid: np.ndarray) -> np.ndarray:
    lengths = np.zeros(len(valid), dtype=np.int64)
    run = 0
    for index, is_valid in enumerate(valid):
        run = run + 1 if bool(is_valid) else 0
        lengths[index] = run
    return lengths


def _bars_on_grid(
    frame: pd.DataFrame,
    *,
    symbol: str,
    decision_time: pd.Timestamp,
    grid: pd.DatetimeIndex,
) -> tuple[np.ndarray, np.ndarray, np.ndarray] | None:
    required = {"open_time", "close", "quote_volume", "taker_buy_quote_volume"}
    if not isinstance(frame, pd.DataFrame) or not required.issubset(frame.columns):
        return None

    open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    close_times = open_times + _EIGHT_HOURS
    past = open_times.notna() & (close_times <= decision_time) & close_times.isin(grid)
    if not bool(past.any()):
        return None

    columns = ["close", "quote_volume", "taker_buy_quote_volume"]
    work = frame.loc[past, columns].copy()
    work.index = pd.DatetimeIndex(close_times.loc[past])
    if work.index.duplicated().any():
        return None
    if "symbol" in frame.columns:
        observed_symbols = frame.loc[past, "symbol"].astype(str)
        if not observed_symbols.eq(symbol).all():
            return None

    for column in columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.sort_index(kind="mergesort").reindex(grid)
    return (
        work["close"].to_numpy(dtype=np.float64),
        work["quote_volume"].to_numpy(dtype=np.float64),
        work["taker_buy_quote_volume"].to_numpy(dtype=np.float64),
    )


def _log_returns(close: np.ndarray) -> np.ndarray:
    result = np.full(len(close), np.nan, dtype=np.float64)
    valid_close = np.isfinite(close) & (close > 0.0)
    paired = valid_close[1:] & valid_close[:-1]
    if paired.any():
        current = np.log(close[1:][paired])
        previous = np.log(close[:-1][paired])
        values = current - previous
        finite = np.isfinite(values)
        indices = np.flatnonzero(paired) + 1
        result[indices[finite]] = values[finite]
    return result


def _rolling_residuals(
    returns: np.ndarray,
    btc_returns: np.ndarray,
    config: _Config,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    paired = np.isfinite(returns) & np.isfinite(btc_returns)
    runs = _consecutive_run_lengths(paired)
    beta = np.full(len(returns), np.nan, dtype=np.float64)
    residual = np.full(len(returns), np.nan, dtype=np.float64)

    safe_asset = np.where(paired, returns, 0.0)
    safe_btc = np.where(paired, btc_returns, 0.0)
    prefix_asset = np.concatenate(([0.0], np.cumsum(safe_asset, dtype=np.float64)))
    prefix_btc = np.concatenate(([0.0], np.cumsum(safe_btc, dtype=np.float64)))
    prefix_cross = np.concatenate(([0.0], np.cumsum(safe_asset * safe_btc, dtype=np.float64)))
    prefix_btc_square = np.concatenate(([0.0], np.cumsum(safe_btc * safe_btc, dtype=np.float64)))

    for index in range(1, len(returns)):
        if not paired[index]:
            continue
        available = int(runs[index - 1])
        observations = min(config.beta_lookback, available)
        if observations < config.beta_minimum:
            continue
        start = index - observations
        end = index
        asset_sum = prefix_asset[end] - prefix_asset[start]
        btc_sum = prefix_btc[end] - prefix_btc[start]
        cross_sum = prefix_cross[end] - prefix_cross[start]
        btc_square_sum = prefix_btc_square[end] - prefix_btc_square[start]
        divisor = float(observations - 1)
        covariance = (cross_sum - asset_sum * btc_sum / observations) / divisor
        variance = (btc_square_sum - btc_sum * btc_sum / observations) / divisor
        if (
            not math.isfinite(covariance)
            or not math.isfinite(variance)
            or variance <= config.beta_variance_floor
        ):
            continue
        value = float(np.clip(covariance / variance, -config.beta_clip, config.beta_clip))
        innovation = float(returns[index] - value * btc_returns[index])
        if math.isfinite(value) and math.isfinite(innovation):
            beta[index] = value
            residual[index] = innovation
    return beta, residual, paired


def _event_slopes(
    quote_volume: np.ndarray,
    taker_buy_quote_volume: np.ndarray,
    residual: np.ndarray,
    config: _Config,
) -> tuple[float, float] | None:
    log_volume = np.full(len(quote_volume), np.nan, dtype=np.float64)
    valid_volume = np.isfinite(quote_volume) & (quote_volume > 0.0)
    log_volume[valid_volume] = np.log(quote_volume[valid_volume])
    volume_runs = _consecutive_run_lengths(np.isfinite(log_volume))
    last = len(quote_volume) - 1
    first_candidate = max(0, last - config.slope_window)

    positive: list[tuple[float, float, float]] = []
    negative: list[tuple[float, float, float]] = []
    for index in range(first_candidate, last):
        label_end = index + config.horizon
        if label_end > last:
            continue
        label = residual[index + 1 : label_end + 1]
        if len(label) != config.horizon or not np.isfinite(label).all():
            continue
        if not valid_volume[index] or not math.isfinite(taker_buy_quote_volume[index]):
            continue
        available = int(volume_runs[index - 1]) if index else 0
        observations = min(config.volume_lookback, available)
        if observations < config.volume_minimum:
            continue
        baseline = log_volume[index - observations : index]
        median = float(np.median(baseline))
        mad = float(np.median(np.abs(baseline - median)))
        scale = max(1.4826 * mad, config.volume_scale_floor)
        abnormal = float(
            np.clip((log_volume[index] - median) / scale, -config.volume_clip, config.volume_clip)
        )
        imbalance = float(
            np.clip(
                2.0 * taker_buy_quote_volume[index] / quote_volume[index] - 1.0,
                -1.0,
                1.0,
            )
        )
        if not math.isfinite(abnormal) or not math.isfinite(imbalance):
            continue
        event_value = imbalance * max(abnormal - config.volume_threshold, 0.0)
        if event_value == 0.0:
            continue
        age_bars = last - index
        weight = 2.0 ** (-2.0 * age_bars / config.slope_window)
        response = float(math.fsum(float(value) for value in label))
        record = (weight, event_value, response)
        (positive if event_value > 0.0 else negative).append(record)

    def fit(records: list[tuple[float, float, float]]) -> float | None:
        if len(records) < config.slope_minimum_events:
            return None
        weight_sum = math.fsum(weight for weight, _, _ in records)
        weighted_square_sum = math.fsum(weight * value * value for weight, value, _ in records)
        if (
            not math.isfinite(weight_sum)
            or weight_sum <= 0.0
            or not math.isfinite(weighted_square_sum)
            or weighted_square_sum <= 0.0
        ):
            return None
        rms = math.sqrt(weighted_square_sum / weight_sum)
        if not math.isfinite(rms) or rms <= 0.0:
            return None
        normalized = [(weight, value / rms, response) for weight, value, response in records]
        denominator = math.fsum(weight * value * value for weight, value, _ in normalized)
        if not math.isfinite(denominator) or denominator <= config.slope_denominator_floor:
            return None
        numerator = math.fsum(weight * value * response for weight, value, response in normalized)
        fitted = numerator / (denominator + config.slope_ridge)
        return float(fitted) if math.isfinite(fitted) else None

    buy_slope = fit(positive)
    sell_slope = fit(negative)
    if buy_slope is None or sell_slope is None:
        return None
    return buy_slope, sell_slope


def _symbol_features(
    arrays: tuple[np.ndarray, np.ndarray, np.ndarray],
    btc_returns: np.ndarray,
    config: _Config,
) -> _Features | None:
    close, quote_volume, taker_buy_quote_volume = arrays
    last = len(close) - 1

    capacity = quote_volume[last - config.capacity_bars + 1 : last + 1]
    if (
        len(capacity) != config.capacity_bars
        or not np.isfinite(capacity).all()
        or (capacity < 0.0).any()
        or float(math.fsum(float(value) for value in capacity))
        < config.capacity_minimum_quote_volume
    ):
        return None

    returns = _log_returns(close)
    beta, residual, paired = _rolling_residuals(returns, btc_returns, config)
    if not math.isfinite(beta[last]):
        return None

    momentum_start = last - (config.momentum_lag_bars + config.momentum_lookback - 1)
    momentum_end = last - config.momentum_lag_bars + 1
    momentum_values = residual[momentum_start:momentum_end]
    if len(momentum_values) != config.momentum_lookback or not np.isfinite(momentum_values).all():
        return None
    momentum = float(math.fsum(float(value) for value in momentum_values))

    paired_runs = _consecutive_run_lengths(paired)
    volatility_observations = min(config.volatility_lookback, int(paired_runs[last]))
    if volatility_observations < config.volatility_minimum:
        return None
    volatility_values = returns[last - volatility_observations + 1 : last + 1]
    volatility = float(np.std(volatility_values, ddof=1))

    liquidity_values = quote_volume[last - config.liquidity_lookback + 1 : last + 1]
    if (
        len(liquidity_values) != config.liquidity_lookback
        or not np.isfinite(liquidity_values).all()
        or (liquidity_values <= 0.0).any()
    ):
        return None
    liquidity = float(np.log(np.median(liquidity_values)))

    residual_runs = _consecutive_run_lengths(np.isfinite(residual))
    tail_observations = min(config.tail_lookback, int(residual_runs[last]))
    if tail_observations < config.tail_minimum:
        return None
    tail = residual[last - tail_observations + 1 : last + 1]
    q05 = float(np.quantile(tail, 0.05, method="linear"))
    q95 = float(np.quantile(tail, 0.95, method="linear"))
    lower = tail[tail <= q05]
    upper = tail[tail >= q95]
    if not len(lower) or not len(upper):
        return None
    long_tail_risk = -float(np.mean(lower))
    short_tail_risk = float(np.mean(upper))

    slopes = _event_slopes(quote_volume, taker_buy_quote_volume, residual, config)
    values = (
        beta[last],
        momentum,
        volatility,
        liquidity,
        long_tail_risk,
        short_tail_risk,
    )
    if slopes is None or not all(math.isfinite(float(value)) for value in values):
        return None
    return _Features(
        buy_slope=slopes[0],
        sell_slope=slopes[1],
        beta=float(beta[last]),
        momentum=momentum,
        volatility=volatility,
        liquidity=liquidity,
        long_tail_risk=long_tail_risk,
        short_tail_risk=short_tail_risk,
    )


def _ordinal_rank(values: Mapping[str, float]) -> dict[str, float]:
    finite = {
        str(symbol): float(value) for symbol, value in values.items() if math.isfinite(float(value))
    }
    if len(finite) < 2:
        return {}
    ordered = sorted(finite, key=lambda symbol: (finite[symbol], symbol))
    denominator = len(ordered) - 1
    return {symbol: 2.0 * index / denominator - 1.0 for index, symbol in enumerate(ordered)}


def _funding_sums(
    funding: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    symbols: set[str],
    config: _Config,
) -> dict[str, float] | None:
    required = {"funding_time", "symbol", "funding_rate"}
    if not isinstance(funding, pd.DataFrame) or not required.issubset(funding.columns):
        return {}
    times = pd.to_datetime(funding["funding_time"], utc=True, errors="coerce")
    start = decision_time - pd.Timedelta(days=config.funding_lookback_days)
    in_window = times.notna() & (times >= start) & (times < decision_time)
    work = funding.loc[in_window, ["symbol", "funding_rate"]].copy()
    work["funding_time"] = pd.DatetimeIndex(times.loc[in_window])
    work["symbol"] = work["symbol"].astype(str)
    if work.duplicated(["symbol", "funding_time"]).any():
        return None
    work = work[work["symbol"].isin(symbols)]
    work["funding_rate"] = pd.to_numeric(work["funding_rate"], errors="coerce")

    result: dict[str, float] = {}
    for symbol in sorted(symbols):
        rows = work[work["symbol"] == symbol]
        rates = rows["funding_rate"].to_numpy(dtype=np.float64)
        if len(rows) < config.funding_minimum_events or not np.isfinite(rates).all():
            continue
        span = rows["funding_time"].max() - rows["funding_time"].min()
        if span < pd.Timedelta(days=config.funding_minimum_span_days):
            continue
        value = float(math.fsum(float(rate) for rate in rates))
        if math.isfinite(value):
            result[symbol] = value
    return result


def _neutralized_scores(
    features: Mapping[str, _Features],
    funding: Mapping[str, float],
    config: _Config,
) -> dict[str, float]:
    slope_symbols = sorted(features)
    if len(slope_symbols) < config.minimum_names:
        return {}
    buy_rank = _ordinal_rank({symbol: features[symbol].buy_slope for symbol in slope_symbols})
    sell_rank = _ordinal_rank({symbol: features[symbol].sell_slope for symbol in slope_symbols})
    if not buy_rank or not sell_rank:
        return {}
    alpha = {symbol: 0.5 * (buy_rank[symbol] - sell_rank[symbol]) for symbol in slope_symbols}

    beta_rank = _ordinal_rank({symbol: features[symbol].beta for symbol in slope_symbols})
    momentum_rank = _ordinal_rank({symbol: features[symbol].momentum for symbol in slope_symbols})
    volatility_rank = _ordinal_rank(
        {symbol: features[symbol].volatility for symbol in slope_symbols}
    )
    liquidity_rank = _ordinal_rank({symbol: features[symbol].liquidity for symbol in slope_symbols})
    if not all((beta_rank, momentum_rank, volatility_rank, liquidity_rank)):
        return {}

    ordered = slope_symbols
    design = np.asarray(
        [
            [
                1.0,
                beta_rank[symbol],
                momentum_rank[symbol],
                volatility_rank[symbol],
                liquidity_rank[symbol],
            ]
            for symbol in ordered
        ],
        dtype=np.float64,
    )
    response = np.asarray([alpha[symbol] for symbol in ordered], dtype=np.float64)
    penalty = np.diag(np.asarray([0.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float64))
    try:
        inverse = np.linalg.inv(design.T @ design + penalty)
    except np.linalg.LinAlgError:
        return {}
    residual_alpha = response - design @ inverse @ design.T @ response
    if not np.isfinite(residual_alpha).all():
        return {}
    neutral = {symbol: float(value) for symbol, value in zip(ordered, residual_alpha, strict=True)}

    final_symbols = sorted(set(neutral).intersection(funding))
    if len(final_symbols) < config.minimum_names:
        return {}
    neutral_rank = _ordinal_rank({symbol: neutral[symbol] for symbol in final_symbols})
    funding_rank = _ordinal_rank({symbol: funding[symbol] for symbol in final_symbols})
    return {
        symbol: neutral_rank[symbol] - config.funding_penalty * funding_rank[symbol]
        for symbol in final_symbols
    }


def _water_fill(
    risks: Mapping[str, float],
    *,
    gross: float,
    cap: float,
) -> dict[str, float] | None:
    active = sorted(risks)
    if not active or len(active) * cap < gross:
        return None
    allocations: dict[str, float] = {}
    remaining = float(gross)
    while active:
        inverse_risk = {symbol: 1.0 / risks[symbol] for symbol in active}
        total_inverse = math.fsum(inverse_risk.values())
        if not math.isfinite(total_inverse) or total_inverse <= 0.0:
            return None
        proposed = {symbol: remaining * inverse_risk[symbol] / total_inverse for symbol in active}
        capped = [symbol for symbol in active if proposed[symbol] > cap]
        if not capped:
            allocations.update(proposed)
            remaining = 0.0
            active = []
            break
        for symbol in capped:
            allocations[symbol] = cap
            remaining -= cap
        active = [symbol for symbol in active if symbol not in set(capped)]

    if active or remaining > 1e-12:
        return None
    delta = gross - math.fsum(allocations.values())
    if delta != 0.0:
        if delta > 0.0:
            candidates = sorted(
                allocations,
                key=lambda symbol: (-(cap - allocations[symbol]), symbol),
            )
        else:
            candidates = sorted(allocations, key=lambda symbol: (-allocations[symbol], symbol))
        allocations[candidates[0]] += delta
    if any(
        not math.isfinite(value) or value < 0.0 or value > cap + 1e-12
        for value in allocations.values()
    ):
        return None
    return allocations


class AsymmetricLiquidityReplenishment:
    """Emit the preregistered weekly signed target weights."""

    def __init__(self, config: _Config):
        self._config = config

    def target_weights(
        self,
        context: Any,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        decision_time = _utc_timestamp(context.decision_time)
        if not _is_weekly_decision(decision_time):
            return None
        if seed != self._config.seed:
            raise ValueError(f"strategy seed must be {self._config.seed}")

        eligible = tuple(str(symbol) for symbol in context.eligible_symbols)
        if len(eligible) != len(set(eligible)):
            return {}
        eligible_non_btc = sorted(symbol for symbol in eligible if symbol != _BTC_SYMBOL)
        if len(eligible_non_btc) < self._config.minimum_names or _BTC_SYMBOL not in context.bars:
            return {}

        history_bars = self._config.slope_window + self._config.beta_lookback + 1
        grid = pd.date_range(
            end=decision_time,
            periods=history_bars + 1,
            freq=_EIGHT_HOURS,
        )
        btc_arrays = _bars_on_grid(
            context.bars[_BTC_SYMBOL],
            symbol=_BTC_SYMBOL,
            decision_time=decision_time,
            grid=grid,
        )
        if btc_arrays is None:
            return {}
        btc_returns = _log_returns(btc_arrays[0])

        features: dict[str, _Features] = {}
        for symbol in eligible_non_btc:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            arrays = _bars_on_grid(
                frame,
                symbol=symbol,
                decision_time=decision_time,
                grid=grid,
            )
            if arrays is None:
                continue
            values = _symbol_features(arrays, btc_returns, self._config)
            if values is not None:
                features[symbol] = values
        if len(features) < self._config.minimum_names:
            return {}

        funding = _funding_sums(
            context.funding,
            decision_time=decision_time,
            symbols=set(features),
            config=self._config,
        )
        if funding is None:
            return {}
        scores = _neutralized_scores(features, funding, self._config)
        if len(scores) < self._config.minimum_names:
            return {}

        ordered = sorted(scores, key=lambda symbol: (scores[symbol], symbol))
        shorts = ordered[: self._config.sleeve_names]
        longs = ordered[-self._config.sleeve_names :]
        if len(shorts) != self._config.sleeve_names or len(longs) != self._config.sleeve_names:
            return {}

        long_raw = {symbol: features[symbol].long_tail_risk for symbol in longs}
        short_raw = {symbol: features[symbol].short_tail_risk for symbol in shorts}
        long_median = float(np.median(list(long_raw.values())))
        short_median = float(np.median(list(short_raw.values())))
        long_risks = {
            symbol: max(value, self._config.risk_floor, 0.5 * long_median)
            for symbol, value in long_raw.items()
        }
        short_risks = {
            symbol: max(value, self._config.risk_floor, 0.5 * short_median)
            for symbol, value in short_raw.items()
        }
        if not all(
            math.isfinite(value) and value > 0.0
            for value in (*long_risks.values(), *short_risks.values())
        ):
            return {}

        long_weights = _water_fill(
            long_risks,
            gross=self._config.sleeve_gross,
            cap=self._config.symbol_cap,
        )
        short_weights = _water_fill(
            short_risks,
            gross=self._config.sleeve_gross,
            cap=self._config.symbol_cap,
        )
        if long_weights is None or short_weights is None:
            return {}

        targets = {
            symbol: long_weights.get(symbol, 0.0) - short_weights.get(symbol, 0.0)
            for symbol in sorted(set(long_weights).union(short_weights))
        }
        gross = math.fsum(abs(value) for value in targets.values())
        net = math.fsum(targets.values())
        if (
            not all(math.isfinite(value) for value in targets.values())
            or abs(gross - 2.0 * self._config.sleeve_gross) > 1e-12
            or abs(net) > 1e-12
            or any(abs(value) > self._config.symbol_cap + 1e-12 for value in targets.values())
            or not set(targets).issubset(set(eligible))
        ):
            return {}
        return targets


def build_strategy() -> AsymmetricLiquidityReplenishment:
    """Return one fresh instance of the frozen ``t01-alr-002`` champion."""

    return AsymmetricLiquidityReplenishment(
        _Config(
            horizon=6,
            slope_window=189,
            volume_threshold=1.0,
            funding_penalty=0.25,
        )
    )
