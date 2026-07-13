"""Team-07 T07-SRMB-118 slow residual-momentum breadth strategy.

The strategy emits only signed target weights. Membership, fills, costs, funding,
participation, exposure enforcement, and PnL remain organizer-owned.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    """Fixed, source-auditable handoff for organizer-advanced trial 118."""

    candidate_id: str
    strategy_seed: int
    factor_symbol: str
    interval_hours: int
    coefficient_window_returns: int
    formation_returns: int
    skip_returns: int
    names_per_sleeve: int
    per_symbol_weight: float
    breadth_lower: float
    breadth_upper: float
    outside_breadth_multiplier: float
    beta_denominator_floor: float
    residual_rms_floor: float
    minimum_scorable_non_factor_names: int

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> StrategyConfig:
        strategy = payload.get("strategy")
        if not isinstance(strategy, Mapping):
            raise ValueError("frozen_config.json requires a strategy object")
        config = cls(
            candidate_id=str(payload["candidate_id"]),
            strategy_seed=int(payload["strategy_seed"]),
            factor_symbol=str(strategy["factor_symbol"]),
            interval_hours=int(strategy["interval_hours"]),
            coefficient_window_returns=int(strategy["coefficient_window_returns"]),
            formation_returns=int(strategy["formation_returns"]),
            skip_returns=int(strategy["skip_returns"]),
            names_per_sleeve=int(strategy["names_per_sleeve"]),
            per_symbol_weight=float(strategy["per_symbol_weight"]),
            breadth_lower=float(strategy["breadth_lower"]),
            breadth_upper=float(strategy["breadth_upper"]),
            outside_breadth_multiplier=float(strategy["outside_breadth_multiplier"]),
            beta_denominator_floor=float(strategy["beta_denominator_floor"]),
            residual_rms_floor=float(strategy["residual_rms_floor"]),
            minimum_scorable_non_factor_names=int(
                strategy["minimum_scorable_non_factor_names"]
            ),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.candidate_id != "T07-SRMB-118":
            raise ValueError("unexpected Team-07 candidate")
        if self.strategy_seed != 20260713:
            raise ValueError("unexpected Team-07 strategy seed")
        if self.factor_symbol != "BTCUSDT" or self.interval_hours != 8:
            raise ValueError("unexpected factor or bar interval")
        if (
            self.coefficient_window_returns != 189
            or self.formation_returns != 63
            or self.skip_returns != 21
        ):
            raise ValueError("unexpected SRM-B windows")
        if not 0 < self.formation_returns <= self.coefficient_window_returns:
            raise ValueError("formation window must fit inside the coefficient window")
        if self.names_per_sleeve != 6:
            raise ValueError("unexpected names-per-sleeve setting")
        if self.minimum_scorable_non_factor_names != 2 * self.names_per_sleeve:
            raise ValueError("minimum breadth must support disjoint sleeves")
        if not math.isclose(self.per_symbol_weight, 0.05, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("unexpected per-symbol weight")
        if not (
            math.isclose(self.breadth_lower, 0.20, rel_tol=0.0, abs_tol=1e-15)
            and math.isclose(self.breadth_upper, 0.80, rel_tol=0.0, abs_tol=1e-15)
            and math.isclose(
                self.outside_breadth_multiplier, 0.0, rel_tol=0.0, abs_tol=1e-15
            )
        ):
            raise ValueError("unexpected breadth brake")
        if self.beta_denominator_floor != 1e-12 or self.residual_rms_floor != 1e-8:
            raise ValueError("unexpected numerical fault thresholds")
        gross = 2.0 * self.names_per_sleeve * self.per_symbol_weight
        if not math.isclose(gross, 0.60, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("unexpected gross exposure")


@dataclasses.dataclass(frozen=True)
class _AssetScore:
    symbol: str
    score: float
    recent_positive: bool


class SlowResidualMomentumBreadthStrategy:
    """Exact past-only implementation of organizer-advanced T07-SRMB-118."""

    def __init__(self, config: StrategyConfig):
        self.config = config
        self._interval = pd.Timedelta(hours=config.interval_hours)
        self._return_count = config.coefficient_window_returns + config.skip_returns
        self._close_count = self._return_count + 1

    def target_weights(
        self, context: Any, *, seed: int
    ) -> Mapping[str, float] | None:
        if seed != self.config.strategy_seed:
            raise ValueError("Team-07 strategy seed differs from the frozen seed")
        decision_time = _as_utc_timestamp(context.decision_time)
        if decision_time.weekday() != 0 or decision_time != decision_time.floor("D"):
            return None

        eligible = tuple(str(symbol) for symbol in context.eligible_symbols)
        if len(eligible) != len(set(eligible)):
            raise ValueError("eligible_symbols contains duplicates")
        eligible_set = set(eligible)
        if self.config.factor_symbol not in eligible_set:
            return {}

        factor_frame = context.bars.get(self.config.factor_symbol)
        factor_closes = self._closed_tail(
            factor_frame,
            symbol=self.config.factor_symbol,
            decision_time=decision_time,
        )
        if factor_closes is None:
            return {}
        factor_returns = np.diff(np.log(factor_closes))
        if not np.isfinite(factor_returns).all():
            return {}

        scores: list[_AssetScore] = []
        for symbol in sorted(eligible_set - {self.config.factor_symbol}):
            closes = self._closed_tail(
                context.bars.get(symbol),
                symbol=symbol,
                decision_time=decision_time,
            )
            if closes is None:
                continue
            asset_returns = np.diff(np.log(closes))
            score = self._residual_score(asset_returns, factor_returns)
            if score is None:
                continue
            recent_sum = float(asset_returns[-self.config.skip_returns :].sum())
            if not math.isfinite(recent_sum):
                continue
            scores.append(
                _AssetScore(
                    symbol=symbol,
                    score=score,
                    recent_positive=recent_sum > 0.0,
                )
            )

        if len(scores) < self.config.minimum_scorable_non_factor_names:
            return {}
        breadth = sum(item.recent_positive for item in scores) / len(scores)
        if not self.config.breadth_lower <= breadth <= self.config.breadth_upper:
            # Trial 118 fixed the outside multiplier at zero, so this is an explicit flatten.
            return {}

        long_rank = sorted(scores, key=lambda item: (-item.score, item.symbol))
        longs = long_rank[: self.config.names_per_sleeve]
        long_symbols = {item.symbol for item in longs}
        short_rank = sorted(scores, key=lambda item: (item.score, item.symbol))
        shorts = [item for item in short_rank if item.symbol not in long_symbols][
            : self.config.names_per_sleeve
        ]
        if len(shorts) != self.config.names_per_sleeve:
            return {}

        weights = {item.symbol: self.config.per_symbol_weight for item in longs}
        weights.update({item.symbol: -self.config.per_symbol_weight for item in shorts})
        return weights

    def _closed_tail(
        self,
        frame: pd.DataFrame | None,
        *,
        symbol: str,
        decision_time: pd.Timestamp,
    ) -> np.ndarray | None:
        if frame is None or not isinstance(frame, pd.DataFrame):
            return None
        if not {"open_time", "close"}.issubset(frame.columns):
            return None
        open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
        closed_mask = open_times.notna() & ((open_times + self._interval) <= decision_time)
        history = frame.loc[closed_mask, ["open_time", "close"]].copy()
        history["open_time"] = open_times.loc[closed_mask]
        if "symbol" in frame.columns:
            symbols = frame.loc[closed_mask, "symbol"].astype(str)
            if not symbols.eq(symbol).all():
                return None
        history = history.sort_values("open_time", kind="mergesort")
        if history["open_time"].duplicated().any() or len(history) < self._close_count:
            return None
        history = history.tail(self._close_count)
        expected = pd.date_range(
            end=decision_time - self._interval,
            periods=self._close_count,
            freq=self._interval,
        )
        observed = pd.DatetimeIndex(history["open_time"])
        if not observed.equals(expected):
            return None
        closes = pd.to_numeric(history["close"], errors="coerce").to_numpy(
            dtype=np.float64,
            copy=True,
        )
        if not np.isfinite(closes).all() or np.any(closes <= 0.0):
            return None
        return closes

    def _residual_score(
        self, asset_returns: np.ndarray, factor_returns: np.ndarray
    ) -> float | None:
        if len(asset_returns) != self._return_count or len(factor_returns) != self._return_count:
            return None
        window = self.config.coefficient_window_returns
        formation = self.config.formation_returns
        x = factor_returns[:window]
        y = asset_returns[:window]
        if not np.isfinite(x).all() or not np.isfinite(y).all():
            return None
        x_mean = float(x.mean())
        y_mean = float(y.mean())
        x_centered = x - x_mean
        denominator = float(np.dot(x_centered, x_centered))
        if not math.isfinite(denominator) or denominator <= self.config.beta_denominator_floor:
            return None
        beta = float(np.dot(x_centered, y - y_mean) / denominator)
        alpha = y_mean - beta * x_mean
        residuals = y - alpha - beta * x
        residual_sum_squares = float(np.dot(residuals, residuals))
        degrees_of_freedom = window - 2
        if degrees_of_freedom <= 0 or not math.isfinite(residual_sum_squares):
            return None
        residual_rms = math.sqrt(residual_sum_squares / degrees_of_freedom)
        if not math.isfinite(residual_rms) or residual_rms <= self.config.residual_rms_floor:
            return None
        score = float(residuals[-formation:].sum() / (residual_rms * math.sqrt(formation)))
        return score if math.isfinite(score) else None


def _as_utc_timestamp(value: Any) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError("decision_time is invalid")
    return timestamp.tz_localize("UTC") if timestamp.tzinfo is None else timestamp.tz_convert("UTC")


def _load_frozen_config() -> StrategyConfig:
    path = Path(__file__).with_name("frozen_config.json")
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, Mapping):
        raise ValueError("frozen_config.json root must be an object")
    if payload.get("qr_accepted") is not False:
        raise ValueError("T07-SRMB-118 must not be represented as QR-accepted")
    if payload.get("advancement") != "organizer_advanced_despite_QR_falsifier":
        raise ValueError("unexpected Team-07 advancement disposition")
    return StrategyConfig.from_mapping(payload)


def build_strategy() -> SlowResidualMomentumBreadthStrategy:
    """Return one fresh, deterministic strategy instance for the canonical worker."""

    return SlowResidualMomentumBreadthStrategy(_load_frozen_config())
