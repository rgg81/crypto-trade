"""Perpetual listing-maturation targets for Team 10.

The strategy deliberately reads only transaction-bar ``open_time``.  Prices, returns, volume,
funding, marks, fills, and portfolio state are not signal inputs.  The common evaluator owns all
execution and accounting.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

_DAY = pd.Timedelta(days=1)
_BAR_INTERVAL = pd.Timedelta(hours=8)
_ALLOWED_YOUNG_MAX_DAYS = frozenset({180, 270, 360})
_ALLOWED_CADENCE_DAYS = frozenset({7, 14, 28})
_MECHANISM = "perpetual_listing_maturation"
_LEFT_CENSOR_RULE = "first_open_equals_snapshot_start"


@dataclasses.dataclass(frozen=True)
class ListingMaturationConfig:
    """Fixed, source-auditable parameters for one preregistered grid cell."""

    anchor: pd.Timestamp
    snapshot_start: pd.Timestamp
    young_min_days: int
    young_max_days: int
    mature_min_days: int
    cadence_days: int
    names_per_sleeve: int
    weight_per_name: float
    seed: int

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> ListingMaturationConfig:
        if not isinstance(raw, Mapping):
            raise TypeError("strategy config must be a mapping")
        if _required_int(raw, "schema_version") != 1:
            raise ValueError("unsupported strategy-config schema")
        if raw.get("mechanism") != _MECHANISM:
            raise ValueError("strategy config names the wrong mechanism")
        if raw.get("left_censor_rule") != _LEFT_CENSOR_RULE:
            raise ValueError("strategy config names the wrong left-censor rule")

        config = cls(
            anchor=_required_utc_timestamp(raw, "anchor_utc"),
            snapshot_start=_required_utc_timestamp(raw, "snapshot_start_utc"),
            young_min_days=_required_int(raw, "young_min_days"),
            young_max_days=_required_int(raw, "young_max_days"),
            mature_min_days=_required_int(raw, "mature_min_days"),
            cadence_days=_required_int(raw, "cadence_days"),
            names_per_sleeve=_required_int(raw, "names_per_sleeve"),
            weight_per_name=_required_float(raw, "weight_per_name"),
            seed=_required_int(raw, "seed"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.anchor != self.anchor.floor("D"):
            raise ValueError("schedule anchor must be 00:00 UTC")
        if self.snapshot_start != self.snapshot_start.floor("D"):
            raise ValueError("snapshot start must be 00:00 UTC")
        if self.snapshot_start >= self.anchor:
            raise ValueError("snapshot start must precede the schedule anchor")
        if self.young_min_days != 30:
            raise ValueError("young minimum must remain fixed at 30 days")
        if self.young_max_days not in _ALLOWED_YOUNG_MAX_DAYS:
            raise ValueError("young maximum is outside the preregistered grid")
        if self.mature_min_days != 540:
            raise ValueError("mature minimum must remain fixed at 540 days")
        if self.young_max_days >= self.mature_min_days:
            raise ValueError("young and mature pools must be disjoint")
        if self.cadence_days not in _ALLOWED_CADENCE_DAYS:
            raise ValueError("cadence is outside the preregistered grid")
        if self.names_per_sleeve != 5:
            raise ValueError("each sleeve must remain fixed at five names")
        if not math.isclose(self.weight_per_name, 0.08, rel_tol=0.0, abs_tol=1e-15):
            raise ValueError("per-name weight must remain fixed at 0.08")
        if self.seed != 20260713:
            raise ValueError("strategy seed differs from the tournament seed")


class PerpetualListingMaturationStrategy:
    """Long mature contracts and short the youngest eligible contracts on schedule."""

    def __init__(self, config: ListingMaturationConfig):
        config.validate()
        self.config = config

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float] | None:
        decision_time = _as_utc_timestamp(context.decision_time, "decision_time")
        if seed != self.config.seed:
            raise ValueError("runtime seed differs from frozen strategy seed")
        if not self._is_scheduled(decision_time):
            return None

        eligible = _eligible_symbols(context.eligible_symbols)
        observations: list[tuple[str, float, bool]] = []
        for symbol in eligible:
            first_open = self._first_observable_open(context.bars.get(symbol), decision_time)
            if first_open is None:
                continue
            left_censored = first_open == self.config.snapshot_start
            age_days = float((decision_time - first_open) / _DAY)
            observations.append((symbol, age_days, left_censored))

        young = [
            (symbol, age_days)
            for symbol, age_days, left_censored in observations
            if not left_censored
            and self.config.young_min_days <= age_days <= self.config.young_max_days
        ]
        mature = [
            (symbol, age_days)
            for symbol, age_days, left_censored in observations
            if left_censored or age_days >= self.config.mature_min_days
        ]
        if len(young) < self.config.names_per_sleeve or len(mature) < self.config.names_per_sleeve:
            return {}

        selected_young = sorted(young, key=lambda item: (item[1], item[0]))[
            : self.config.names_per_sleeve
        ]
        selected_mature = sorted(mature, key=lambda item: (-item[1], item[0]))[
            : self.config.names_per_sleeve
        ]

        result = {symbol: self.config.weight_per_name for symbol, _age in selected_mature}
        result.update({symbol: -self.config.weight_per_name for symbol, _age in selected_young})
        return result

    def _is_scheduled(self, decision_time: pd.Timestamp) -> bool:
        if decision_time < self.config.anchor or decision_time != decision_time.floor("D"):
            return False
        elapsed = decision_time - self.config.anchor
        return elapsed % pd.Timedelta(days=self.config.cadence_days) == pd.Timedelta(0)

    def _first_observable_open(
        self, frame: pd.DataFrame | None, decision_time: pd.Timestamp
    ) -> pd.Timestamp | None:
        if not isinstance(frame, pd.DataFrame) or frame.empty or "open_time" not in frame:
            return None
        try:
            timestamps = pd.to_datetime(frame["open_time"], errors="coerce")
        except (TypeError, ValueError, OverflowError):
            return None
        if not isinstance(timestamps.dtype, pd.DatetimeTZDtype):
            return None
        timestamps = timestamps.dt.tz_convert("UTC")
        observable = timestamps[
            timestamps.notna()
            & (timestamps >= self.config.snapshot_start)
            & (timestamps + _BAR_INTERVAL <= decision_time)
        ]
        if observable.empty:
            return None
        first_open = pd.Timestamp(observable.min())
        if pd.isna(first_open) or first_open > decision_time:
            return None
        return first_open


def build_strategy() -> PerpetualListingMaturationStrategy:
    """Build a fresh strategy from the staged fixed config."""
    config_path = Path(__file__).with_name("frozen_config.json")
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return PerpetualListingMaturationStrategy(ListingMaturationConfig.from_mapping(raw))


def _eligible_symbols(raw: Any) -> tuple[str, ...]:
    try:
        symbols = tuple(raw)
    except TypeError as exc:
        raise TypeError("eligible_symbols must be an iterable of strings") from exc
    if any(not isinstance(symbol, str) or not symbol for symbol in symbols):
        raise TypeError("eligible_symbols must contain non-empty strings")
    if len(symbols) != len(set(symbols)):
        raise ValueError("eligible_symbols cannot contain duplicates")
    return symbols


def _as_utc_timestamp(raw: Any, field: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(raw)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{field} must be a finite timestamp") from exc
    if pd.isna(timestamp):
        raise ValueError(f"{field} must be a finite timestamp")
    if timestamp.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _required_utc_timestamp(raw: Mapping[str, Any], field: str) -> pd.Timestamp:
    if field not in raw:
        raise ValueError(f"strategy config is missing {field}")
    return _as_utc_timestamp(raw[field], field)


def _required_int(raw: Mapping[str, Any], field: str) -> int:
    value = raw.get(field)
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field} must be an integer")
    return value


def _required_float(raw: Mapping[str, Any], field: str) -> float:
    value = raw.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result
