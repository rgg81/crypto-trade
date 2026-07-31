"""Causal liquidity-shock impact-persistence baseline for Team 06."""

from __future__ import annotations

import math
from typing import Mapping

import numpy as np
import pandas as pd


class BroadShockRetentionStrategy:
    """Trade lagged impact that survives broad, persistent liquidity shocks."""

    BAR_HOURS = 8
    REBALANCE_BARS = 9
    BASELINE_BARS = 42
    EVENT_BARS = 2
    POST_BARS = 3
    EVENT_SCAN_BARS = 18
    QUOTE_SHOCK_RATIO = 1.50
    EVENT_TRADE_RATIO = 1.25
    POST_QUOTE_RATIO = 1.10
    POST_TRADE_RATIO = 1.05
    MAX_TICKET_RATIO = 1.75
    MIN_ABS_IMPACT = 0.005
    MIN_RETENTION = 0.35
    RECENCY_HALF_LIFE_BARS = 6.0
    VOLATILITY_LOOKBACK_BARS = 60
    VOLATILITY_FLOOR_PER_BAR = 0.005
    MAX_ASSETS_PER_SIDE = 3
    MIN_ASSETS_PER_SIDE = 2
    WEIGHT_PER_ASSET = 0.15
    SCHEDULE_ANCHOR = pd.Timestamp("1970-01-05 00:00:00", tz="UTC")

    @staticmethod
    def _utc_timestamp(value: object) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    @staticmethod
    def _find_column(frame: pd.DataFrame, names: tuple[str, ...]) -> str | None:
        for name in names:
            if name in frame.columns:
                return name
        return None

    def _is_rebalance(self, decision_time: pd.Timestamp) -> bool:
        elapsed = (decision_time - self.SCHEDULE_ANCHOR).total_seconds()
        bar_number = math.floor(elapsed / (self.BAR_HOURS * 3600))
        return bar_number % self.REBALANCE_BARS == 0

    def _completed_frame(
        self, frame: pd.DataFrame, decision_time: pd.Timestamp
    ) -> pd.DataFrame | None:
        time_column = self._find_column(frame, ("open_time",))
        quote_column = self._find_column(
            frame, ("quote_volume", "quote_asset_volume")
        )
        trades_column = self._find_column(
            frame, ("trade_count", "number_of_trades", "trades")
        )
        open_column = self._find_column(frame, ("open",))
        close_column = self._find_column(frame, ("close",))
        required = (
            time_column,
            quote_column,
            trades_column,
            open_column,
            close_column,
        )
        if any(column is None for column in required):
            return None

        open_times = pd.to_datetime(frame[time_column], utc=True, errors="coerce")
        completion_cutoff = decision_time - pd.Timedelta(hours=self.BAR_HOURS)
        completed = frame.loc[open_times <= completion_cutoff].copy()
        if completed.empty:
            return None

        completed["_open_time"] = open_times.loc[completed.index]
        completed = completed.sort_values("_open_time", kind="mergesort")
        completed = completed.drop_duplicates("_open_time", keep="last")
        completed = completed.loc[
            :, ["_open_time", open_column, close_column, quote_column, trades_column]
        ]
        completed.columns = ["open_time", "open", "close", "quote", "trades"]
        for column in ("open", "close", "quote", "trades"):
            completed[column] = pd.to_numeric(completed[column], errors="coerce")
        completed = completed.replace([np.inf, -np.inf], np.nan).dropna()
        completed = completed.loc[
            (completed["open"] > 0.0)
            & (completed["close"] > 0.0)
            & (completed["quote"] > 0.0)
            & (completed["trades"] > 0.0)
        ]
        return completed.reset_index(drop=True)

    def _symbol_score(self, frame: pd.DataFrame) -> float | None:
        minimum_bars = (
            self.BASELINE_BARS
            + self.EVENT_BARS
            + self.POST_BARS
            + self.EVENT_SCAN_BARS
        )
        if len(frame) < minimum_bars:
            return None

        opens = frame["open"].to_numpy(dtype=float)
        closes = frame["close"].to_numpy(dtype=float)
        quotes = frame["quote"].to_numpy(dtype=float)
        trades = frame["trades"].to_numpy(dtype=float)
        last_index = len(frame) - 1
        latest_event_end = last_index - self.POST_BARS
        earliest_event_end = max(
            self.BASELINE_BARS + self.EVENT_BARS - 1,
            latest_event_end - self.EVENT_SCAN_BARS + 1,
        )

        score = 0.0
        qualifying_events = 0
        for event_end in range(earliest_event_end, latest_event_end + 1):
            event_start = event_end - self.EVENT_BARS + 1
            baseline_start = event_start - self.BASELINE_BARS
            baseline_quotes = quotes[baseline_start:event_start]
            baseline_trades = trades[baseline_start:event_start]
            event_slice = slice(event_start, event_end + 1)
            post_slice = slice(event_end + 1, event_end + self.POST_BARS + 1)

            baseline_quote = float(np.median(baseline_quotes))
            baseline_trade = float(np.median(baseline_trades))
            baseline_ticket = float(np.median(baseline_quotes / baseline_trades))
            event_quote = float(np.mean(quotes[event_slice]))
            event_trade = float(np.mean(trades[event_slice]))
            post_quote = float(np.median(quotes[post_slice]))
            post_trade = float(np.median(trades[post_slice]))
            event_ticket = event_quote / event_trade

            quote_ratio = event_quote / baseline_quote
            event_trade_ratio = event_trade / baseline_trade
            post_quote_ratio = post_quote / baseline_quote
            post_trade_ratio = post_trade / baseline_trade
            ticket_ratio = event_ticket / baseline_ticket
            if (
                quote_ratio < self.QUOTE_SHOCK_RATIO
                or event_trade_ratio < self.EVENT_TRADE_RATIO
                or post_quote_ratio < self.POST_QUOTE_RATIO
                or post_trade_ratio < self.POST_TRADE_RATIO
                or ticket_ratio > self.MAX_TICKET_RATIO
            ):
                continue

            event_impact = math.log(closes[event_end] / opens[event_start])
            if abs(event_impact) < self.MIN_ABS_IMPACT:
                continue
            post_end = event_end + self.POST_BARS
            retained_impact = math.log(closes[post_end] / opens[event_start])
            direction = 1.0 if event_impact > 0.0 else -1.0
            retention = direction * retained_impact / abs(event_impact)
            if retention < self.MIN_RETENTION:
                continue

            shock_strength = math.log(quote_ratio / self.QUOTE_SHOCK_RATIO) + 1.0
            breadth_strength = min(
                math.log(event_trade_ratio / self.EVENT_TRADE_RATIO) + 1.0,
                math.log(post_trade_ratio / self.POST_TRADE_RATIO) + 1.0,
            )
            persistence_strength = min(retention, 1.50) / 1.50
            liquidity_strength = math.log(post_quote_ratio / self.POST_QUOTE_RATIO) + 1.0
            age = last_index - post_end
            recency_weight = 0.5 ** (age / self.RECENCY_HALF_LIFE_BARS)
            score += (
                direction
                * abs(event_impact)
                * shock_strength
                * breadth_strength
                * persistence_strength
                * liquidity_strength
                * recency_weight
            )
            qualifying_events += 1

        if qualifying_events == 0:
            return None

        close_lookback = closes[-(self.VOLATILITY_LOOKBACK_BARS + 1) :]
        log_returns = np.diff(np.log(close_lookback))
        volatility = float(np.std(log_returns, ddof=1))
        if not math.isfinite(volatility):
            return None
        return score / max(volatility, self.VOLATILITY_FLOOR_PER_BAR)

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # The formula is deterministic and does not require random tie-breaking.
        decision_time = self._utc_timestamp(context.decision_time)
        if not self._is_rebalance(decision_time):
            return None

        scores: dict[str, float] = {}
        for symbol in sorted(context.eligible_symbols):
            if symbol not in context.bars:
                continue
            completed = self._completed_frame(context.bars[symbol], decision_time)
            if completed is None:
                continue
            score = self._symbol_score(completed)
            if score is not None and math.isfinite(score) and score != 0.0:
                scores[symbol] = score

        longs = sorted(
            ((symbol, score) for symbol, score in scores.items() if score > 0.0),
            key=lambda item: (-item[1], item[0]),
        )[: self.MAX_ASSETS_PER_SIDE]
        shorts = sorted(
            ((symbol, score) for symbol, score in scores.items() if score < 0.0),
            key=lambda item: (item[1], item[0]),
        )[: self.MAX_ASSETS_PER_SIDE]
        matched_count = min(len(longs), len(shorts))
        if matched_count < self.MIN_ASSETS_PER_SIDE:
            return {}

        targets: dict[str, float] = {}
        for symbol, _ in longs[:matched_count]:
            targets[symbol] = self.WEIGHT_PER_ASSET
        for symbol, _ in shorts[:matched_count]:
            targets[symbol] = -self.WEIGHT_PER_ASSET
        return targets


def build_strategy() -> BroadShockRetentionStrategy:
    """Return a clean strategy instance for the tournament runner."""

    return BroadShockRetentionStrategy()
