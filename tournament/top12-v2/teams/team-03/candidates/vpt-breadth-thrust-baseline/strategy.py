"""Fortnightly volume-participation breadth-thrust baseline for Team 03."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


class VolumeParticipationBreadthThrust:
    """Trade persistent directions confirmed by broad unusual quote-volume activity."""

    _BAR_HOURS = 8
    _HISTORY_DAYS = 90
    _VOLUME_BASELINE_DAYS = 28
    _THRUST_DAYS = 12
    _TREND_DAYS = 28
    _VOLUME_RATIO_THRESHOLD = 1.35
    _MIN_ACTIVE_DAYS = 2
    _MIN_SYMBOLS = 8
    _MIN_BREADTH_FRACTION = 0.50
    _MIN_IMPULSE = 0.25
    _N_PER_SIDE = 3
    _GROSS_TARGET = 1.0

    @staticmethod
    def _utc_timestamp(value) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    @classmethod
    def _symbol_signal(cls, raw, decision_time: pd.Timestamp):
        required = {"open_time", "close", "quote_volume"}
        if raw is None or not required.issubset(raw.columns):
            return None

        frame = raw.loc[:, ["open_time", "close", "quote_volume"]].copy()
        frame["open_time"] = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
        frame["close"] = pd.to_numeric(frame["close"], errors="coerce")
        frame["quote_volume"] = pd.to_numeric(frame["quote_volume"], errors="coerce")
        frame = frame.dropna(subset=["open_time", "close", "quote_volume"])
        frame = frame.loc[
            (frame["open_time"] + pd.Timedelta(hours=cls._BAR_HOURS) <= decision_time)
            & (frame["open_time"] >= decision_time - pd.Timedelta(days=cls._HISTORY_DAYS))
            & (frame["close"] > 0.0)
            & (frame["quote_volume"] >= 0.0)
        ]
        frame = frame.sort_values("open_time").drop_duplicates("open_time", keep="last")
        if frame.empty:
            return None

        frame["day"] = frame["open_time"].dt.floor("D")
        daily = frame.groupby("day", sort=True).agg(
            close=("close", "last"),
            quote_volume=("quote_volume", "sum"),
            bar_count=("close", "size"),
        )
        daily = daily.loc[daily["bar_count"] == 3, ["close", "quote_volume"]]
        required_days = max(cls._VOLUME_BASELINE_DAYS + cls._THRUST_DAYS, cls._TREND_DAYS + 1)
        if len(daily) < required_days:
            return None

        daily["volume_baseline"] = (
            daily["quote_volume"]
            .rolling(cls._VOLUME_BASELINE_DAYS, min_periods=cls._VOLUME_BASELINE_DAYS)
            .median()
            .shift(1)
        )
        daily["volume_ratio"] = daily["quote_volume"] / daily["volume_baseline"]
        daily["direction"] = np.sign(np.log(daily["close"] / daily["close"].shift(1)))

        recent = daily.tail(cls._THRUST_DAYS).copy()
        valid = np.isfinite(recent["volume_ratio"]) & np.isfinite(recent["direction"])
        recent = recent.loc[valid]
        active = recent["volume_ratio"] >= cls._VOLUME_RATIO_THRESHOLD
        active_days = int(active.sum())
        if active_days == 0:
            return {
                "participating": False,
                "confirmed_direction": 0,
                "score": 0.0,
            }

        excess = (recent.loc[active, "volume_ratio"] - 1.0).clip(lower=0.0, upper=2.0)
        denominator = float(excess.sum())
        if not np.isfinite(denominator) or denominator <= 0.0:
            return None
        impulse = float((recent.loc[active, "direction"] * excess).sum() / denominator)

        trend_start = float(daily["close"].iloc[-(cls._TREND_DAYS + 1)])
        trend_end = float(daily["close"].iloc[-1])
        trend_direction = int(np.sign(np.log(trend_end / trend_start)))
        impulse_direction = int(np.sign(impulse))
        participating = active_days >= cls._MIN_ACTIVE_DAYS
        confirmed = (
            impulse_direction
            if participating
            and abs(impulse) >= cls._MIN_IMPULSE
            and impulse_direction == trend_direction
            else 0
        )
        score = abs(impulse) * np.sqrt(float(active_days))
        return {
            "participating": participating,
            "confirmed_direction": confirmed,
            "score": float(score),
        }

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # The rule has no stochastic component.
        decision_time = self._utc_timestamp(context.decision_time)

        # ISO-even Mondays are an immutable, calendar-anchored fortnightly schedule.
        if (
            decision_time.weekday() != 0
            or decision_time.hour != 0
            or decision_time.minute != 0
            or decision_time.second != 0
            or decision_time.isocalendar().week % 2 != 0
        ):
            return None

        records = []
        for symbol in sorted(context.eligible_symbols):
            signal = self._symbol_signal(context.bars.get(symbol), decision_time)
            if signal is not None:
                records.append((symbol, signal))

        if len(records) < self._MIN_SYMBOLS:
            return {}
        participating = sum(int(signal["participating"]) for _, signal in records)
        if participating / len(records) < self._MIN_BREADTH_FRACTION:
            return {}

        longs = sorted(
            ((symbol, signal["score"]) for symbol, signal in records if signal["confirmed_direction"] > 0),
            key=lambda item: (-item[1], item[0]),
        )[: self._N_PER_SIDE]
        shorts = sorted(
            ((symbol, signal["score"]) for symbol, signal in records if signal["confirmed_direction"] < 0),
            key=lambda item: (-item[1], item[0]),
        )[: self._N_PER_SIDE]
        if len(longs) < 2 or len(shorts) < 2:
            return {}

        side_gross = self._GROSS_TARGET / 2.0
        weights = {symbol: side_gross / len(longs) for symbol, _ in longs}
        weights.update({symbol: -side_gross / len(shorts) for symbol, _ in shorts})
        return weights


def build_strategy() -> VolumeParticipationBreadthThrust:
    return VolumeParticipationBreadthThrust()
