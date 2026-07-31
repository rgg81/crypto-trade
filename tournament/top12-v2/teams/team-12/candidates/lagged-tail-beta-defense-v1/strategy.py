"""Lagged tail-concentration defensive rotation for Team 12."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import numpy as np
import pandas as pd


class LaggedTailBetaDefense:
    """Weekly, market-neutral rotation toward resilient downside exposures."""

    FORMATION_DAYS = 84
    MIN_HISTORY_DAYS = 56
    MIN_CROSS_SECTION = 8
    MIN_DOWNSIDE_OBSERVATIONS = 12
    CONCENTRATION_SMOOTHING_DAYS = 21
    CONCENTRATION_MIN_OBSERVATIONS = 5
    REGIME_RANK_DAYS = 42
    SIGNAL_LAG_DAYS = 1
    CONCENTRATION_WEIGHT_FLOOR = 0.25
    RETURN_CLIP_MAD_MULTIPLE = 4.0
    TAIL_QUANTILE = 0.25
    DOWNSIDE_BETA_WEIGHT = 0.70
    TAIL_LOADING_WEIGHT = 0.30
    WEIGHT_CAP_QUANTILE = 0.90
    MIN_GROSS = 0.55
    MAX_GROSS = 0.80
    SLEEVE_SIZE = 5
    RANK_TILT_STRENGTH = 0.15
    MAX_ABSOLUTE_WEIGHT = 0.15
    REBALANCE_WEEKDAY_UTC = 0
    REBALANCE_HOUR_UTC = 0

    def target_weights(
        self, context: Any, *, seed: int
    ) -> Mapping[str, float] | None:
        """Return Monday targets using only bars complete by the boundary."""
        del seed  # The strategy has no stochastic branch.

        boundary = self._utc_timestamp(context.decision_time)
        if (
            boundary.weekday() != self.REBALANCE_WEEKDAY_UTC
            or boundary.hour != self.REBALANCE_HOUR_UTC
            or boundary.minute != 0
        ):
            return None

        symbols = sorted({str(symbol) for symbol in context.eligible_symbols})
        flat = {symbol: 0.0 for symbol in symbols}
        if len(symbols) < self.MIN_CROSS_SECTION:
            return flat

        daily_closes: dict[str, pd.Series] = {}
        for symbol in symbols:
            frame = context.bars.get(symbol)
            series = self._completed_daily_closes(frame, boundary)
            if series is not None:
                daily_closes[symbol] = series

        if len(daily_closes) < self.MIN_CROSS_SECTION:
            return flat

        closes = pd.concat(daily_closes, axis=1).sort_index()
        closes = closes.loc[~closes.index.duplicated(keep="last")]
        if closes.empty:
            return flat

        full_days = pd.date_range(closes.index.min(), closes.index.max(), freq="D", tz="UTC")
        closes = closes.reindex(full_days).tail(self.FORMATION_DAYS + 1)
        returns = closes.pct_change(fill_method=None).tail(self.FORMATION_DAYS)
        if len(returns) < self.MIN_HISTORY_DAYS:
            return flat

        returns = self._cross_sectionally_clip(returns)
        valid_count = returns.notna().sum(axis=1)
        usable_days = valid_count >= self.MIN_CROSS_SECTION
        returns = returns.where(usable_days, np.nan)

        market_return = returns.median(axis=1, skipna=True)
        losses = (-returns).clip(lower=0.0)
        total_loss = losses.sum(axis=1, min_count=1)
        loss_share = losses.div(total_loss.replace(0.0, np.nan), axis=0)
        hhi = loss_share.pow(2).sum(axis=1, min_count=1)
        equal_share_hhi = 1.0 / valid_count.replace(0, np.nan)
        concentration = (
            (hhi - equal_share_hhi) / (1.0 - equal_share_hhi)
        ).clip(lower=0.0, upper=1.0)
        concentration = concentration.where((market_return < 0.0) & usable_days)

        lagged_concentration = concentration.shift(self.SIGNAL_LAG_DAYS)
        lagged_state = lagged_concentration.rolling(
            self.CONCENTRATION_SMOOTHING_DAYS,
            min_periods=self.CONCENTRATION_MIN_OBSERVATIONS,
        ).mean()

        downside_magnitude = (-market_return).clip(lower=0.0)
        state_weight = self.CONCENTRATION_WEIGHT_FLOOR + (
            1.0 - self.CONCENTRATION_WEIGHT_FLOOR
        ) * lagged_state
        observation_weight = downside_magnitude * state_weight
        positive_weights = observation_weight[observation_weight > 0.0]
        if len(positive_weights) < self.MIN_DOWNSIDE_OBSERVATIONS:
            return flat
        weight_cap = positive_weights.quantile(self.WEIGHT_CAP_QUANTILE)
        observation_weight = observation_weight.clip(upper=weight_cap).fillna(0.0)

        tail_cutoff = returns.quantile(self.TAIL_QUANTILE, axis=1)
        tail_hit = returns.le(tail_cutoff, axis=0).astype(float).where(returns.notna())

        downside_beta: dict[str, float] = {}
        tail_loading: dict[str, float] = {}
        for symbol in sorted(returns.columns):
            asset_return = returns[symbol]
            valid = asset_return.notna() & market_return.notna() & (observation_weight > 0.0)
            if int(valid.sum()) < self.MIN_DOWNSIDE_OBSERVATIONS:
                continue

            weight = observation_weight.loc[valid]
            market = market_return.loc[valid]
            asset = asset_return.loc[valid]
            denominator = float((weight * market.pow(2)).sum())
            if not np.isfinite(denominator) or denominator <= 0.0:
                continue

            beta = float((weight * market * asset).sum() / denominator)
            hit_rate = float((weight * tail_hit.loc[valid, symbol]).sum() / weight.sum())
            if np.isfinite(beta) and np.isfinite(hit_rate):
                downside_beta[symbol] = beta
                tail_loading[symbol] = hit_rate

        if len(downside_beta) < self.MIN_CROSS_SECTION:
            return flat

        beta_rank = self._deterministic_percentile_rank(pd.Series(downside_beta))
        tail_rank = self._deterministic_percentile_rank(pd.Series(tail_loading))
        fragility = (
            self.DOWNSIDE_BETA_WEIGHT * beta_rank
            + self.TAIL_LOADING_WEIGHT * tail_rank
        )
        fragility = fragility.replace([np.inf, -np.inf], np.nan).dropna()
        if len(fragility) < self.MIN_CROSS_SECTION:
            return flat

        latest_state = lagged_state.iloc[-1]
        state_history = lagged_state.dropna().tail(self.REGIME_RANK_DAYS)
        if state_history.empty or not np.isfinite(latest_state):
            return flat
        current_state = float(latest_state)
        state_percentile = float((state_history <= current_state).mean())
        gross = self.MIN_GROSS + (self.MAX_GROSS - self.MIN_GROSS) * state_percentile

        ordered = sorted(fragility.index, key=lambda symbol: (fragility[symbol], symbol))
        sleeve_size = min(self.SLEEVE_SIZE, len(ordered) // 2)
        if sleeve_size < 3:
            return flat
        long_symbols = ordered[:sleeve_size]
        short_symbols = ordered[-sleeve_size:]

        long_quality = fragility.loc[long_symbols].max() - fragility.loc[long_symbols]
        short_quality = fragility.loc[short_symbols] - fragility.loc[short_symbols].min()
        long_weights = self._sleeve_weights(long_quality, gross / 2.0)
        short_weights = self._sleeve_weights(short_quality, gross / 2.0)

        targets = dict(flat)
        for symbol, weight in long_weights.items():
            targets[symbol] = float(weight)
        for symbol, weight in short_weights.items():
            targets[symbol] = float(-weight)

        if not all(np.isfinite(weight) for weight in targets.values()):
            return flat
        return targets

    @staticmethod
    def _utc_timestamp(value: Any) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    @classmethod
    def _completed_daily_closes(
        cls, frame: Any, boundary: pd.Timestamp
    ) -> pd.Series | None:
        if frame is None or not isinstance(frame, pd.DataFrame):
            return None
        if "open_time" not in frame.columns or "close" not in frame.columns:
            return None

        data = frame.loc[:, ["open_time", "close"]].copy()
        raw_time = data["open_time"]
        if pd.api.types.is_numeric_dtype(raw_time):
            numeric = pd.to_numeric(raw_time, errors="coerce")
            finite = numeric[np.isfinite(numeric)]
            if finite.empty:
                return None
            magnitude = float(finite.abs().median())
            if magnitude >= 1.0e17:
                unit = "ns"
            elif magnitude >= 1.0e14:
                unit = "us"
            elif magnitude >= 1.0e11:
                unit = "ms"
            else:
                unit = "s"
            open_time = pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
        else:
            open_time = pd.to_datetime(raw_time, utc=True, errors="coerce")

        close = pd.to_numeric(data["close"], errors="coerce")
        completed = (open_time + pd.Timedelta(hours=8)) <= boundary
        valid = completed & open_time.notna() & close.notna() & (close > 0.0)
        if not bool(valid.any()):
            return None

        observations = pd.DataFrame(
            {"open_time": open_time.loc[valid], "close": close.loc[valid]}
        ).sort_values("open_time")
        observations = observations.drop_duplicates("open_time", keep="last")
        observations["day"] = observations["open_time"].dt.floor("D")
        daily = observations.groupby("day", sort=True)["close"].last().astype(float)
        return daily if len(daily) >= cls.MIN_HISTORY_DAYS + 1 else None

    @classmethod
    def _cross_sectionally_clip(cls, returns: pd.DataFrame) -> pd.DataFrame:
        median = returns.median(axis=1, skipna=True)
        absolute_deviation = returns.sub(median, axis=0).abs()
        mad = absolute_deviation.median(axis=1, skipna=True)
        robust_scale = 1.4826 * mad
        lower = median - cls.RETURN_CLIP_MAD_MULTIPLE * robust_scale
        upper = median + cls.RETURN_CLIP_MAD_MULTIPLE * robust_scale
        clipped = returns.clip(lower=lower, upper=upper, axis=0)
        return clipped.replace([np.inf, -np.inf], np.nan)

    @staticmethod
    def _deterministic_percentile_rank(values: pd.Series) -> pd.Series:
        ordered = sorted(values.index, key=lambda symbol: (float(values[symbol]), symbol))
        denominator = max(1, len(ordered) - 1)
        return pd.Series(
            {symbol: position / denominator for position, symbol in enumerate(ordered)},
            dtype=float,
        )

    @classmethod
    def _sleeve_weights(cls, quality: pd.Series, budget: float) -> pd.Series:
        count = len(quality)
        if count == 0 or budget <= 0.0:
            return pd.Series(dtype=float)
        total_quality = float(quality.sum())
        if total_quality > 0.0:
            quality_share = quality / total_quality
        else:
            quality_share = pd.Series(1.0 / count, index=quality.index, dtype=float)
        share = (1.0 - cls.RANK_TILT_STRENGTH) / count + cls.RANK_TILT_STRENGTH * quality_share
        weights = budget * share
        return weights.clip(upper=cls.MAX_ABSOLUTE_WEIGHT)


def build_strategy() -> LaggedTailBetaDefense:
    """Build a fresh deterministic strategy instance."""
    return LaggedTailBetaDefense()
