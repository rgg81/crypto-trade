"""Causal baseline for persistent signed taker-aggressor pressure."""

from __future__ import annotations

from typing import Mapping

import numpy as np
import pandas as pd


class SignedVolumePressurePersistence:
    """Trade only pressure whose sign persists across multiple causal views."""

    BAR_HOURS = 8
    FORMATION_DAYS = 30
    FORMATION_BARS = 90
    MINIMUM_VALID_BARS = 72
    PERSISTENCE_BLOCKS = 3
    PERSISTENCE_BLOCK_BARS = 21
    EWM_HALFLIFE_BARS = 12
    BLOCK_WEIGHT = 0.60
    EWM_WEIGHT = 0.40
    MINIMUM_ABSOLUTE_PRESSURE = 0.02
    POSITIONS_PER_SIDE = 3
    SIDE_GROSS = 0.50
    REBALANCE_HOURS = 96

    # Each pair is (total volume, taker-buy volume) in the same units. No
    # price-sign proxy or total-volume surprise is used as an alternative.
    AGGRESSOR_VOLUME_PAIRS = (
        ("base_volume", "taker_buy_base_volume"),
        ("volume", "taker_buy_base_volume"),
        ("base_volume", "taker_buy_volume"),
        ("volume", "taker_buy_volume"),
        ("quote_volume", "taker_buy_quote_volume"),
    )

    def __init__(self) -> None:
        self._last_rebalance_bucket: int | None = None

    @staticmethod
    def _utc_timestamp(value) -> pd.Timestamp:
        timestamp = pd.Timestamp(value)
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")

    @staticmethod
    def _open_times(values: pd.Series) -> pd.Series:
        """Parse datetime-like or common integer exchange timestamps."""
        if pd.api.types.is_numeric_dtype(values.dtype):
            numeric = pd.to_numeric(values, errors="coerce")
            finite = numeric[np.isfinite(numeric)]
            if finite.empty:
                return pd.to_datetime(numeric, utc=True, errors="coerce")
            magnitude = float(finite.abs().median())
            if magnitude >= 1.0e17:
                unit = "ns"
            elif magnitude >= 1.0e14:
                unit = "us"
            elif magnitude >= 1.0e11:
                unit = "ms"
            else:
                unit = "s"
            return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
        return pd.to_datetime(values, utc=True, errors="coerce")

    @classmethod
    def _volume_pair(cls, frame: pd.DataFrame) -> tuple[str, str] | None:
        for total_column, buy_column in cls.AGGRESSOR_VOLUME_PAIRS:
            if total_column in frame.columns and buy_column in frame.columns:
                return total_column, buy_column
        return None

    @classmethod
    def _pressure_score(
        cls, frame: pd.DataFrame, decision_time: pd.Timestamp
    ) -> float | None:
        if "open_time" not in frame.columns:
            return None
        volume_pair = cls._volume_pair(frame)
        if volume_pair is None:
            return None

        total_column, buy_column = volume_pair
        open_times = cls._open_times(frame["open_time"])
        complete_cutoff = decision_time - pd.Timedelta(hours=cls.BAR_HOURS)
        formation_start = decision_time - pd.Timedelta(days=cls.FORMATION_DAYS)
        completed = (open_times <= complete_cutoff) & (open_times >= formation_start)
        if not bool(completed.any()):
            return None

        local = pd.DataFrame(
            {
                "open_time": open_times[completed],
                "total": pd.to_numeric(frame.loc[completed, total_column], errors="coerce"),
                "buy": pd.to_numeric(frame.loc[completed, buy_column], errors="coerce"),
            }
        )
        local = local.dropna().sort_values("open_time", kind="mergesort")
        local = local.drop_duplicates("open_time", keep="last").tail(cls.FORMATION_BARS)

        valid = (
            np.isfinite(local["total"])
            & np.isfinite(local["buy"])
            & (local["total"] > 0.0)
            & (local["buy"] >= 0.0)
            & (local["buy"] <= local["total"])
        )
        local = local.loc[valid]
        if len(local) < cls.MINIMUM_VALID_BARS:
            return None

        # Taker-sell volume is observed total volume less taker-buy volume.
        # Thus (buy - sell) / (buy + sell) is exactly 2*buy/total - 1.
        imbalance = (2.0 * local["buy"] / local["total"] - 1.0).to_numpy(dtype=float)
        required = cls.PERSISTENCE_BLOCKS * cls.PERSISTENCE_BLOCK_BARS
        persistence_window = imbalance[-required:]
        blocks = persistence_window.reshape(
            cls.PERSISTENCE_BLOCKS, cls.PERSISTENCE_BLOCK_BARS
        )
        block_pressure = float(np.median(np.mean(blocks, axis=1)))
        ewm_pressure = float(
            pd.Series(persistence_window)
            .ewm(halflife=cls.EWM_HALFLIFE_BARS, adjust=False)
            .mean()
            .iloc[-1]
        )

        # Disagreement means the pressure is not persistent enough to trade.
        if block_pressure == 0.0 or ewm_pressure == 0.0:
            return 0.0
        if np.sign(block_pressure) != np.sign(ewm_pressure):
            return 0.0
        score = cls.BLOCK_WEIGHT * block_pressure + cls.EWM_WEIGHT * ewm_pressure
        return float(score) if np.isfinite(score) else None

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # The rule is deterministic and requires no random tie-breaking.
        decision_time = self._utc_timestamp(context.decision_time)
        rebalance_nanoseconds = int(pd.Timedelta(hours=self.REBALANCE_HOURS).value)
        bucket = int(decision_time.value // rebalance_nanoseconds)
        if self._last_rebalance_bucket == bucket:
            return None
        self._last_rebalance_bucket = bucket

        scores: dict[str, float] = {}
        for symbol in sorted(set(context.eligible_symbols)):
            frame = context.bars.get(symbol)
            if frame is None or not isinstance(frame, pd.DataFrame):
                continue
            score = self._pressure_score(frame, decision_time)
            if score is not None:
                scores[symbol] = score

        longs = sorted(
            (
                (score, symbol)
                for symbol, score in scores.items()
                if score >= self.MINIMUM_ABSOLUTE_PRESSURE
            ),
            key=lambda item: (-item[0], item[1]),
        )[: self.POSITIONS_PER_SIDE]
        shorts = sorted(
            (
                (score, symbol)
                for symbol, score in scores.items()
                if score <= -self.MINIMUM_ABSOLUTE_PRESSURE
            ),
            key=lambda item: (item[0], item[1]),
        )[: self.POSITIONS_PER_SIDE]

        # Do not turn a cross-sectional pressure test into a directional bet.
        if not longs or not shorts:
            return {}
        long_weight = self.SIDE_GROSS / len(longs)
        short_weight = -self.SIDE_GROSS / len(shorts)
        targets = {symbol: float(long_weight) for _, symbol in longs}
        targets.update({symbol: float(short_weight) for _, symbol in shorts})
        return targets


def build_strategy() -> SignedVolumePressurePersistence:
    return SignedVolumePressurePersistence()
