"""Team07 causal cross-sectional shock-diffusion strategy.

The organizer supplies only closed bars and past funding rows.  This module never reads files,
uses the network, or observes evaluator state.  Orders, fills, costs, funding cashflows, risk
actions, and eligibility are exclusively organizer owned.
"""

from __future__ import annotations

import dataclasses
import math
from typing import Any

import numpy as np
import pandas as pd


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    seed: int = 20260801
    interval_hours: int = 8
    rebalance_every_bars: int = 3
    lookback_bars: int = 189
    minimum_observations: int = 126
    liquidity_lookback_bars: int = 90
    leader_fraction: float = 0.20
    minimum_leaders: int = 4
    minimum_universe: int = 16
    diffusion_multiplier: float = 1.0
    idiosyncratic_reversion: float = 0.12
    funding_carry_multiplier: float = 6.0
    funding_lookback_events: int = 21
    shock_winsor_sigma: float = 2.5
    trend_bars: int = 126
    trend_z_scale: float = 2.0
    gross_target: float = 0.80
    maximum_directional_net: float = 0.16
    minimum_names_per_side: int = 6
    maximum_symbol_weight: float = 0.09

    def validate(self) -> None:
        positive_windows = (
            self.interval_hours,
            self.rebalance_every_bars,
            self.lookback_bars,
            self.minimum_observations,
            self.liquidity_lookback_bars,
            self.minimum_leaders,
            self.minimum_universe,
            self.funding_lookback_events,
            self.trend_bars,
            self.minimum_names_per_side,
        )
        if any(value <= 0 for value in positive_windows):
            raise ValueError("window, cross-section, and cadence values must be positive")
        if self.lookback_bars < self.minimum_observations + 1:
            raise ValueError("lookback must exceed minimum observations")
        if not self.minimum_observations <= self.trend_bars <= self.lookback_bars:
            raise ValueError("trend window must cover minimum observations within lookback")
        if self.liquidity_lookback_bars > self.lookback_bars:
            raise ValueError("liquidity lookback cannot exceed the return lookback")
        if not 0 < self.leader_fraction <= 0.5:
            raise ValueError("leader_fraction must be in (0, 0.5]")
        if (
            self.diffusion_multiplier < 0
            or self.idiosyncratic_reversion < 0
            or self.funding_carry_multiplier < 0
        ):
            raise ValueError("signal multipliers cannot be negative")
        if self.shock_winsor_sigma <= 0 or self.trend_z_scale <= 0:
            raise ValueError("shock and trend scales must be positive")
        if self.minimum_leaders < 2 or self.minimum_universe < 2 * self.minimum_names_per_side:
            raise ValueError("cross-section minimums cannot support two sleeves")
        if not 0 < self.gross_target <= 1:
            raise ValueError("gross_target must be in (0, 1]")
        if not 0 <= self.maximum_directional_net <= 0.25:
            raise ValueError("directional net cap must be in [0, 0.25]")
        if not 0 < self.maximum_symbol_weight <= 0.10:
            raise ValueError("symbol cap must be in (0, 0.10]")


class ShockDiffusionStrategy:
    """Estimate delayed reactions to a liquid leader basket and trade the propagation gap."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()
        self.config.validate()

    def target_weights(self, context: Any, *, seed: int) -> dict[str, float] | None:
        cfg = self.config
        if seed != cfg.seed:
            raise ValueError("strategy seed differs from the frozen Team07 seed")
        decision_time = _utc_timestamp(context.decision_time)
        if not _is_rebalance_boundary(decision_time, cfg):
            return None

        eligible = tuple(str(symbol) for symbol in context.eligible_symbols)
        if len(eligible) != len(set(eligible)):
            raise ValueError("eligible symbol sequence contains duplicates")
        if set(context.bars) != set(eligible):
            raise ValueError("bar context must exactly match the eligible symbol set")
        if len(eligible) < cfg.minimum_universe:
            return {}

        returns_by_symbol: dict[str, pd.Series] = {}
        liquidity: dict[str, float] = {}
        for symbol in sorted(eligible):
            returns, median_liquidity = _closed_returns_and_liquidity(
                context.bars[symbol], decision_time, cfg
            )
            if int(returns.notna().sum()) >= cfg.minimum_observations:
                returns_by_symbol[symbol] = returns
                liquidity[symbol] = median_liquidity
        if len(returns_by_symbol) < cfg.minimum_universe:
            return {}

        return_frame = pd.concat(returns_by_symbol, axis=1).sort_index().tail(cfg.lookback_bars + 2)
        valid_symbols = sorted(
            symbol
            for symbol in returns_by_symbol
            if int(return_frame[symbol].notna().sum()) >= cfg.minimum_observations
            and math.isfinite(liquidity[symbol])
            and liquidity[symbol] > 0
        )
        if len(valid_symbols) < cfg.minimum_universe:
            return {}

        leader_count = max(
            cfg.minimum_leaders,
            int(math.ceil(cfg.leader_fraction * len(valid_symbols))),
        )
        leaders = tuple(
            sorted(valid_symbols, key=lambda symbol: (-liquidity[symbol], symbol))[:leader_count]
        )
        leader_frame = return_frame.loc[:, list(leaders)]
        minimum_leader_rows = max(2, int(math.ceil(len(leaders) / 2)))
        leader_market = leader_frame.mean(axis=1, skipna=True).where(
            leader_frame.notna().sum(axis=1) >= minimum_leader_rows
        )
        leader_market = leader_market.dropna()
        if len(leader_market) < cfg.minimum_observations + 1:
            return {}

        latest_market_time = pd.Timestamp(leader_market.index[-1])
        expected_latest_time = decision_time - pd.Timedelta(hours=cfg.interval_hours)
        if latest_market_time != expected_latest_time:
            return {}
        market_volatility = float(leader_market.tail(cfg.lookback_bars).std(ddof=1))
        if not math.isfinite(market_volatility) or market_volatility <= 1e-8:
            return {}
        latest_shock = float(leader_market.iloc[-1])
        shock_limit = cfg.shock_winsor_sigma * market_volatility
        latest_shock = float(np.clip(latest_shock, -shock_limit, shock_limit))

        funding_carry = _past_funding_carry(
            context.funding,
            decision_time,
            set(eligible),
            cfg.funding_lookback_events,
        )
        raw_scores: dict[str, float] = {}
        for symbol in valid_symbols:
            local_market = _leave_one_out_market(return_frame, leaders, symbol, leader_market)
            estimate = _diffusion_estimate(
                return_frame[symbol],
                local_market,
                latest_market_time,
                cfg,
            )
            if estimate is None:
                continue
            lag_beta, reliability, residual_now, residual_volatility = estimate
            diffusion_forecast = (
                cfg.diffusion_multiplier * lag_beta * latest_shock * (0.25 + 0.75 * reliability)
            )
            reversion_forecast = -cfg.idiosyncratic_reversion * residual_now
            carry_forecast = -cfg.funding_carry_multiplier * funding_carry.get(symbol, 0.0)
            score = (diffusion_forecast + reversion_forecast + carry_forecast) / residual_volatility
            if math.isfinite(score):
                raw_scores[symbol] = float(score)

        if len(raw_scores) < cfg.minimum_universe:
            return {}
        score_series = pd.Series(raw_scores, dtype=float).sort_index()
        if float(score_series.max() - score_series.min()) <= 1e-12:
            return {}
        ranks = score_series.rank(method="average")
        normalized_scores = 2.0 * (ranks - 1.0) / (len(ranks) - 1.0) - 1.0

        trend = leader_market.tail(cfg.trend_bars)
        if len(trend) < cfg.minimum_observations:
            return {}
        trend_volatility = float(trend.std(ddof=1))
        trend_z = 0.0
        if math.isfinite(trend_volatility) and trend_volatility > 1e-8:
            trend_z = float(trend.sum()) / (trend_volatility * math.sqrt(len(trend)))
        directional_net = cfg.maximum_directional_net * math.tanh(trend_z / cfg.trend_z_scale)
        long_gross = 0.5 * (cfg.gross_target + directional_net)
        short_gross = 0.5 * (cfg.gross_target - directional_net)

        selection_count = max(
            cfg.minimum_names_per_side,
            int(math.ceil(max(long_gross, short_gross) / cfg.maximum_symbol_weight)),
        )
        if 2 * selection_count > len(normalized_scores):
            return {}
        ordered = sorted(
            normalized_scores.index,
            key=lambda symbol: (float(normalized_scores[symbol]), symbol),
        )
        short_names = tuple(ordered[:selection_count])
        long_names = tuple(reversed(ordered[-selection_count:]))
        long_strength = {
            symbol: 1.0 + max(0.0, float(normalized_scores[symbol])) for symbol in long_names
        }
        short_strength = {
            symbol: 1.0 + max(0.0, -float(normalized_scores[symbol])) for symbol in short_names
        }
        long_weights = _capped_allocation(long_strength, long_gross, cfg.maximum_symbol_weight)
        short_weights = _capped_allocation(short_strength, short_gross, cfg.maximum_symbol_weight)
        targets = {symbol: weight for symbol, weight in long_weights.items()}
        targets.update({symbol: -weight for symbol, weight in short_weights.items()})
        _validate_targets(targets, set(eligible), cfg)
        return targets


def _utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    if pd.isna(timestamp):
        raise ValueError("decision timestamp is invalid")
    return timestamp


def _is_rebalance_boundary(timestamp: pd.Timestamp, cfg: StrategyConfig) -> bool:
    bar_number = int(timestamp.value // pd.Timedelta(hours=cfg.interval_hours).value)
    return bar_number % cfg.rebalance_every_bars == 0


def _closed_returns_and_liquidity(
    raw_frame: pd.DataFrame,
    decision_time: pd.Timestamp,
    cfg: StrategyConfig,
) -> tuple[pd.Series, float]:
    required = {"open_time", "close", "quote_volume"}
    missing = required - set(raw_frame.columns)
    if missing:
        raise ValueError(f"bar frame misses required columns: {sorted(missing)}")
    frame = raw_frame.loc[:, ["open_time", "close", "quote_volume"]].copy()
    frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
    frame["quote_volume"] = pd.to_numeric(frame["quote_volume"], errors="coerce")
    if frame.isna().any().any():
        raise ValueError("bar frame contains invalid or missing required values")
    if frame["open_time"].duplicated().any():
        raise ValueError("bar frame contains duplicate timestamps")
    close_boundary = frame["open_time"] + pd.Timedelta(hours=cfg.interval_hours)
    if (close_boundary > decision_time).any():
        raise ValueError("bar frame contains a candle not closed by the decision boundary")
    numeric = frame[["close", "quote_volume"]].to_numpy(dtype=float)
    if not np.isfinite(numeric).all():
        raise ValueError("bar frame contains non-finite values")
    if (frame["close"] <= 0).any() or (frame["quote_volume"] < 0).any():
        raise ValueError("bar close must be positive and quote volume nonnegative")
    frame = frame.sort_values("open_time")
    open_times = pd.DatetimeIndex(frame["open_time"])
    log_close = pd.Series(
        np.log(frame["close"].to_numpy(dtype=float)),
        index=open_times,
        dtype=float,
    )
    exact_adjacency = open_times.to_series().diff().eq(pd.Timedelta(hours=cfg.interval_hours))
    returns = log_close.diff().where(exact_adjacency.to_numpy()).tail(cfg.lookback_bars + 2)
    liquidity = float(frame["quote_volume"].tail(cfg.liquidity_lookback_bars).median())
    return returns, liquidity


def _leave_one_out_market(
    returns: pd.DataFrame,
    leaders: tuple[str, ...],
    symbol: str,
    default_market: pd.Series,
) -> pd.Series:
    if symbol not in leaders or len(leaders) <= 2:
        return default_market
    columns = [leader for leader in leaders if leader != symbol]
    local = returns.loc[:, columns]
    minimum_rows = max(2, int(math.ceil(len(columns) / 2)))
    return local.mean(axis=1, skipna=True).where(local.notna().sum(axis=1) >= minimum_rows)


def _diffusion_estimate(
    asset_returns: pd.Series,
    market_returns: pd.Series,
    latest_market_time: pd.Timestamp,
    cfg: StrategyConfig,
) -> tuple[float, float, float, float] | None:
    aligned = pd.concat(
        [asset_returns.rename("asset"), market_returns.rename("market")], axis=1
    ).dropna()
    aligned = aligned.tail(cfg.lookback_bars + 1)
    if len(aligned) < cfg.minimum_observations + 1:
        return None
    if pd.Timestamp(aligned.index[-1]) != latest_market_time:
        return None
    asset = aligned["asset"].to_numpy(dtype=float)
    market = aligned["market"].to_numpy(dtype=float)
    market_centered = market - market.mean()
    market_variance = float(np.mean(market_centered * market_centered))
    if not math.isfinite(market_variance) or market_variance <= 1e-10:
        return None
    asset_centered = asset - asset.mean()
    contemporaneous_beta = float(np.mean(asset_centered * market_centered) / market_variance)
    contemporaneous_beta = float(np.clip(contemporaneous_beta, -1.0, 4.0))
    residual = asset_centered - contemporaneous_beta * market_centered

    market_by_time = pd.Series(market_centered, index=aligned.index, dtype=float)
    residual_by_time = pd.Series(residual, index=aligned.index, dtype=float)
    lag_times = residual_by_time.index - pd.Timedelta(hours=cfg.interval_hours)
    lag_x = market_by_time.reindex(lag_times).to_numpy(dtype=float)
    lag_y = residual_by_time.to_numpy(dtype=float)
    exact_pairs = np.isfinite(lag_x) & np.isfinite(lag_y)
    if int(exact_pairs.sum()) < cfg.minimum_observations:
        return None
    lag_x = lag_x[exact_pairs]
    lag_y = lag_y[exact_pairs]
    lag_x = lag_x - lag_x.mean()
    lag_y = lag_y - lag_y.mean()
    lag_variance = float(np.mean(lag_x * lag_x))
    residual_variance = float(np.mean(lag_y * lag_y))
    if lag_variance <= 1e-10 or residual_variance <= 1e-10:
        return None
    lag_covariance = float(np.mean(lag_x * lag_y))
    raw_lag_beta = lag_covariance / lag_variance
    lag_correlation = lag_covariance / math.sqrt(lag_variance * residual_variance)
    lag_beta = float(np.clip(raw_lag_beta, 0.0, 3.0))
    reliability = float(np.clip(lag_correlation, 0.0, 1.0))
    residual_volatility = float(np.std(residual, ddof=1))
    if not math.isfinite(residual_volatility) or residual_volatility <= 1e-8:
        return None
    return lag_beta, reliability, float(residual[-1]), residual_volatility


def _past_funding_carry(
    raw_funding: pd.DataFrame,
    decision_time: pd.Timestamp,
    eligible: set[str],
    lookback_events: int,
) -> dict[str, float]:
    if raw_funding.empty:
        return {}
    required = {"funding_time", "symbol", "funding_rate"}
    missing = required - set(raw_funding.columns)
    if missing:
        raise ValueError(f"funding frame misses required columns: {sorted(missing)}")
    frame = raw_funding.loc[:, ["funding_time", "symbol", "funding_rate"]].copy()
    frame["funding_time"] = pd.to_datetime(frame["funding_time"], utc=True, errors="coerce")
    frame["funding_rate"] = pd.to_numeric(frame["funding_rate"], errors="coerce")
    if frame[["funding_time", "funding_rate"]].isna().any().any():
        raise ValueError("funding frame contains invalid required values")
    if (frame["funding_time"] >= decision_time).any():
        raise ValueError("funding frame contains a row unavailable at decision time")
    rates = frame["funding_rate"].to_numpy(dtype=float)
    if not np.isfinite(rates).all():
        raise ValueError("funding frame contains a non-finite rate")
    carry: dict[str, float] = {}
    for raw_symbol, group in frame.groupby("symbol", observed=True, sort=False):
        symbol = str(raw_symbol)
        if symbol not in eligible:
            raise ValueError("funding context contains a symbol outside the eligible set")
        recent = group.sort_values("funding_time")["funding_rate"].tail(lookback_events)
        if len(recent):
            carry[symbol] = float(recent.mean())
    return carry


def _capped_allocation(
    strengths: dict[str, float], budget: float, maximum_weight: float
) -> dict[str, float]:
    if budget < -1e-12 or budget > len(strengths) * maximum_weight + 1e-12:
        raise ValueError("side budget cannot be allocated under the symbol cap")
    allocation: dict[str, float] = {}
    remaining = dict(strengths)
    remaining_budget = float(budget)
    while remaining:
        total_strength = sum(remaining.values())
        if not math.isfinite(total_strength) or total_strength <= 0:
            raise ValueError("allocation strengths must be finite and positive")
        proposed = {
            symbol: remaining_budget * strength / total_strength
            for symbol, strength in remaining.items()
        }
        capped = sorted(symbol for symbol, weight in proposed.items() if weight > maximum_weight)
        if not capped:
            allocation.update(proposed)
            break
        for symbol in capped:
            allocation[symbol] = maximum_weight
            remaining_budget -= maximum_weight
            del remaining[symbol]
    return allocation


def _validate_targets(targets: dict[str, float], eligible: set[str], cfg: StrategyConfig) -> None:
    if not set(targets).issubset(eligible):
        raise RuntimeError("internal target construction emitted an ineligible symbol")
    values = np.asarray(list(targets.values()), dtype=float)
    if not np.isfinite(values).all():
        raise RuntimeError("internal target construction emitted a non-finite weight")
    if len(values) and float(np.max(np.abs(values))) > cfg.maximum_symbol_weight + 1e-10:
        raise RuntimeError("internal target construction exceeded the symbol cap")
    if float(np.abs(values).sum()) > cfg.gross_target + 1e-9:
        raise RuntimeError("internal target construction exceeded the gross target")
    if abs(float(values.sum())) > cfg.maximum_directional_net + 1e-9:
        raise RuntimeError("internal target construction exceeded the net target")
    if not any(weight > 0 for weight in targets.values()):
        raise RuntimeError("internal target construction omitted the long sleeve")
    if not any(weight < 0 for weight in targets.values()):
        raise RuntimeError("internal target construction omitted the short sleeve")


def build_strategy() -> ShockDiffusionStrategy:
    """Canonical organizer entrypoint."""

    return ShockDiffusionStrategy()
