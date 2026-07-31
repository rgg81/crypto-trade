"""Downside-tail dependence and contagion baseline for Team 12."""

from __future__ import annotations

from datetime import timedelta
from typing import Mapping

import numpy as np
import pandas as pd


class DownsideTailContagionStrategy:
    """Weekly relative-resilience versus relative-fragility allocation."""

    def __init__(self) -> None:
        self._last_rebalance_time: pd.Timestamp | None = None

    def target_weights(
        self, context, *, seed: int
    ) -> Mapping[str, float] | None:
        """Return a capped, market-neutral target from completed bars only."""
        _ = seed
        decision_time = pd.Timestamp(context.decision_time)
        if decision_time.tzinfo is None:
            decision_time = decision_time.tz_localize("UTC")
        else:
            decision_time = decision_time.tz_convert("UTC")

        if (
            self._last_rebalance_time is not None
            and decision_time < self._last_rebalance_time + timedelta(days=7)
        ):
            return None
        self._last_rebalance_time = decision_time

        eligible = sorted({str(symbol) for symbol in context.eligible_symbols})
        if not eligible:
            return {}

        completion_cutoff = decision_time - timedelta(hours=8)
        symbol_returns: dict[str, pd.Series] = {}
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None or "open_time" not in frame or "close" not in frame:
                continue

            open_times = pd.to_datetime(
                frame["open_time"], errors="coerce", utc=True
            )
            closes = pd.to_numeric(frame["close"], errors="coerce")
            usable = (
                open_times.notna()
                & closes.notna()
                & np.isfinite(closes)
                & (closes > 0.0)
                & (open_times <= completion_cutoff)
            )
            if int(usable.sum()) < 121:
                continue

            completed_closes = pd.Series(
                closes.loc[usable].to_numpy(dtype=float),
                index=open_times.loc[usable],
                dtype=float,
            )
            completed_closes = (
                completed_closes.groupby(level=0).last().sort_index().tail(253)
            )
            returns = (
                completed_closes.pct_change(fill_method=None)
                .replace([np.inf, -np.inf], np.nan)
                .dropna()
                .tail(252)
            )
            if len(returns) >= 120:
                symbol_returns[symbol] = returns

        if len(symbol_returns) < 6:
            return {}

        returns_frame = (
            pd.concat(symbol_returns, axis=1, join="outer")
            .sort_index()
            .tail(252)
        )
        minimum_cross_section = max(3, int(np.ceil(len(symbol_returns) / 2.0)))
        valid_cross_section = returns_frame.notna().sum(axis=1) >= minimum_cross_section
        market_proxy = returns_frame.median(axis=1, skipna=True).where(
            valid_cross_section
        )
        market_proxy = market_proxy.dropna()
        if len(market_proxy) < 120:
            return {}

        market_tail_cutoff = float(market_proxy.quantile(0.15))
        market_tail_times = market_proxy.index[market_proxy <= market_tail_cutoff]
        if len(market_tail_times) < 12:
            return {}

        excess_co_crash: dict[str, float] = {}
        tail_amplification: dict[str, float] = {}
        for symbol in sorted(symbol_returns):
            asset = returns_frame[symbol].dropna()
            if len(asset) < 120:
                continue

            asset_tail_cutoff = float(asset.quantile(0.15))
            unconditional_tail_rate = float((asset <= asset_tail_cutoff).mean())
            asset_on_market_tail = asset.reindex(market_tail_times).dropna()
            if len(asset_on_market_tail) < 12:
                continue

            conditional_tail_rate = float(
                (asset_on_market_tail <= asset_tail_cutoff).mean()
            )
            unconditional_downside = float((-asset.clip(upper=0.0)).mean())
            conditional_downside = float(
                (-asset_on_market_tail.clip(upper=0.0)).mean()
            )
            if (
                not np.isfinite(unconditional_downside)
                or unconditional_downside <= 1.0e-12
            ):
                continue

            co_crash = conditional_tail_rate - unconditional_tail_rate
            amplification = conditional_downside / unconditional_downside
            if np.isfinite(co_crash) and np.isfinite(amplification):
                excess_co_crash[symbol] = co_crash
                tail_amplification[symbol] = amplification

        if len(excess_co_crash) < 6:
            return {}

        co_crash_rank = pd.Series(excess_co_crash, dtype=float).rank(
            method="average", pct=True
        )
        amplification_rank = pd.Series(tail_amplification, dtype=float).rank(
            method="average", pct=True
        )
        fragility = 0.65 * co_crash_rank + 0.35 * amplification_rank
        ordered = sorted(
            fragility.index,
            key=lambda symbol: (float(fragility.loc[symbol]), symbol),
        )

        names_per_side = min(5, len(ordered) // 2)
        if names_per_side < 1:
            return {}
        resilience_longs = ordered[:names_per_side]
        fragility_shorts = ordered[-names_per_side:]

        targets = {symbol: 0.0 for symbol in eligible}
        for symbol in resilience_longs:
            targets[symbol] = 0.08
        for symbol in fragility_shorts:
            targets[symbol] = -0.08

        gross = float(sum(abs(weight) for weight in targets.values()))
        net = float(sum(targets.values()))
        if (
            any(not np.isfinite(weight) for weight in targets.values())
            or gross > 0.8000000001
            or abs(net) > 0.2000000001
            or any(abs(weight) > 0.0800000001 for weight in targets.values())
        ):
            return {}
        return targets


def build_strategy():
    """Construct a fresh strategy instance."""
    return DownsideTailContagionStrategy()
