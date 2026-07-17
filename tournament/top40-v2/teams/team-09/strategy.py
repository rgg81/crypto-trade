"""Team09 funding-crowding dislocation strategy.

The rule is deliberately small and causal.  A relative funding-rate extreme identifies a
potentially crowded side of the perpetual market.  The strategy acts only after cross-sectional
price performance confirms that the crowded side has started to unwind.  Positive relative
funding pressure plus weak relative price therefore creates a short candidate; negative relative
funding pressure plus strong relative price creates a long candidate.

All inputs are past-only ``DecisionContext`` data.  The evaluator, not this module, owns fills,
funding cashflows, costs, membership exits, risk controls, and exposure enforcement.
"""

from __future__ import annotations

import dataclasses
import math
import numbers
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

SCORE_ADAPTER_ID = "top40-v2-declared-score-boundary-v1"
SCORE_CAPTURE_BOUNDARY = "candidate-declared-post-transform-pre-selection-weight-cap-risk"
_PASSING_SCORE_MAGNITUDE = 2.0


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    """Complete deterministic parameterization mirrored by ``frozen_config.json``."""

    interval_hours: int = 8
    rebalance_hour_utc: int = 0
    funding_lookback_hours: int = 168
    minimum_funding_events: int = 12
    funding_half_life_hours: float = 72.0
    funding_rate_floor: float = 1e-7
    funding_persistence_weight: float = 0.5
    maximum_funding_age_hours: int = 16
    confirmation_bars: int = 9
    volatility_bars: int = 63
    minimum_cross_section: int = 12
    crowding_threshold: float = 0.30
    confirmation_threshold: float = 0.10
    minimum_symbols_per_side: int = 4
    maximum_symbols_per_side: int = 6
    target_side_gross: float = 0.45
    maximum_symbol_weight: float = 0.09
    expected_seed: int = 20260801

    def validate(self) -> None:
        """Reject ambiguous, infeasible, or evaluator-incompatible parameters."""

        integer_fields = (
            self.interval_hours,
            self.rebalance_hour_utc,
            self.funding_lookback_hours,
            self.minimum_funding_events,
            self.maximum_funding_age_hours,
            self.confirmation_bars,
            self.volatility_bars,
            self.minimum_cross_section,
            self.minimum_symbols_per_side,
            self.maximum_symbols_per_side,
            self.expected_seed,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, numbers.Integral)
            for value in integer_fields
        ):
            raise ValueError("bar counts, hours, cross-section counts, and seed must be integers")
        numeric_fields = (
            self.funding_half_life_hours,
            self.funding_rate_floor,
            self.funding_persistence_weight,
            self.crowding_threshold,
            self.confirmation_threshold,
            self.target_side_gross,
            self.maximum_symbol_weight,
        )
        if any(
            isinstance(value, bool)
            or not isinstance(value, numbers.Real)
            or not math.isfinite(float(value))
            for value in numeric_fields
        ):
            raise ValueError("continuous strategy parameters must be finite real numbers")
        if self.interval_hours <= 0 or 24 % self.interval_hours:
            raise ValueError("interval_hours must be a positive divisor of 24")
        if not 0 <= self.rebalance_hour_utc < 24:
            raise ValueError("rebalance_hour_utc must be in [0, 24)")
        if self.rebalance_hour_utc % self.interval_hours:
            raise ValueError("rebalance_hour_utc must lie on an interval boundary")
        if self.funding_lookback_hours < self.interval_hours:
            raise ValueError("funding_lookback_hours is shorter than one interval")
        if self.funding_lookback_hours % self.interval_hours:
            raise ValueError("funding_lookback_hours must contain complete funding intervals")
        if self.minimum_funding_events < 2:
            raise ValueError("minimum_funding_events must be at least two")
        if self.minimum_funding_events > self.funding_lookback_hours // self.interval_hours:
            raise ValueError("minimum_funding_events exceeds the lookback's available slots")
        if self.funding_half_life_hours <= 0 or self.funding_rate_floor <= 0:
            raise ValueError("funding decay and floor must be positive")
        if not 0 <= self.funding_persistence_weight <= 1:
            raise ValueError("funding_persistence_weight must be in [0, 1]")
        if self.maximum_funding_age_hours < self.interval_hours:
            raise ValueError("maximum_funding_age_hours must cover at least one interval")
        if self.maximum_funding_age_hours > self.funding_lookback_hours:
            raise ValueError("maximum_funding_age_hours cannot exceed the funding lookback")
        if self.confirmation_bars < 2:
            raise ValueError("confirmation_bars must be at least two")
        if self.volatility_bars < self.confirmation_bars:
            raise ValueError("volatility_bars cannot be shorter than confirmation_bars")
        if self.minimum_cross_section < 2 * self.minimum_symbols_per_side:
            raise ValueError("minimum_cross_section cannot support both required sleeves")
        if not 0 <= self.crowding_threshold <= 1:
            raise ValueError("crowding_threshold must be in [0, 1]")
        if not 0 <= self.confirmation_threshold <= 1:
            raise ValueError("confirmation_threshold must be in [0, 1]")
        if self.minimum_symbols_per_side < 1:
            raise ValueError("minimum_symbols_per_side must be positive")
        if self.maximum_symbols_per_side < self.minimum_symbols_per_side:
            raise ValueError("maximum_symbols_per_side is below the minimum")
        if not 0 < self.target_side_gross <= 0.5:
            raise ValueError("target_side_gross must be in (0, 0.5]")
        if not 0 < self.maximum_symbol_weight <= 0.10:
            raise ValueError("maximum_symbol_weight must be in (0, 0.10]")
        if self.target_side_gross > (self.maximum_symbols_per_side * self.maximum_symbol_weight):
            raise ValueError("maximum_symbols_per_side cannot fund target_side_gross")
        if self.expected_seed < 0:
            raise ValueError("expected_seed must be a nonnegative integer")


def _utc_timestamp(value: object, label: str) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if pd.isna(timestamp):
        raise ValueError(f"{label} is not a timestamp")
    if timestamp.tzinfo is None:
        timestamp = timestamp.tz_localize("UTC")
    else:
        timestamp = timestamp.tz_convert("UTC")
    return timestamp


def _centered_ranks(values: Mapping[str, float]) -> dict[str, float]:
    """Return average-tie percentile ranks in [-1, 1], independent of input ordering."""

    if len(values) < 2:
        return {symbol: 0.0 for symbol in values}
    ordered = pd.Series({symbol: values[symbol] for symbol in sorted(values)}, dtype=float)
    ranks = ordered.rank(method="average")
    centered = 2.0 * (ranks - 1.0) / (len(ordered) - 1.0) - 1.0
    return {str(symbol): float(value) for symbol, value in centered.items()}


def _allocate_capped_side(
    candidates: list[tuple[float, str]],
    *,
    gross: float,
    maximum_symbol_weight: float,
    direction: float,
) -> dict[str, float]:
    """Allocate gross proportionally to captured score magnitudes with a hard symbol cap."""

    remaining = float(gross)
    active = [(symbol, float(magnitude)) for magnitude, symbol in candidates]
    allocations: dict[str, float] = {}
    while active and remaining > np.finfo(float).eps:
        total_strength = sum(strength for _symbol, strength in active)
        if total_strength <= 0 or not math.isfinite(total_strength):
            raise ValueError("captured side scores cannot support finite positive allocation")
        capped: list[tuple[str, float]] = []
        uncapped: list[tuple[str, float]] = []
        for symbol, strength in active:
            proposed = remaining * strength / total_strength
            if proposed >= maximum_symbol_weight:
                capped.append((symbol, maximum_symbol_weight))
            else:
                uncapped.append((symbol, proposed))
        if not capped:
            for symbol, proposed in uncapped:
                allocations[symbol] = direction * float(proposed)
            remaining = 0.0
            break
        for symbol, amount in capped:
            allocations[symbol] = direction * float(amount)
            remaining -= amount
        capped_symbols = {symbol for symbol, _amount in capped}
        active = [item for item in active if item[0] not in capped_symbols]
    if remaining > 1e-12:
        raise ValueError("captured side scores could not satisfy the frozen gross allocation")
    return allocations


class FundingCrowdingStrategy:
    """Cross-sectional funding-crowding unwind with relative-price confirmation."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()
        self.config.validate()

    @property
    def _interval(self) -> pd.Timedelta:
        return pd.Timedelta(hours=self.config.interval_hours)

    def _price_confirmation(
        self,
        frame: pd.DataFrame,
        *,
        decision_time: pd.Timestamp,
        symbol: str,
    ) -> float | None:
        required = {"open_time", "close"}
        if not isinstance(frame, pd.DataFrame) or not required.issubset(frame.columns):
            raise ValueError(f"{symbol} bars lack required columns")
        if frame.empty:
            return None

        timestamps = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
        if timestamps.isna().any():
            raise ValueError(f"{symbol} bars contain invalid timestamps")
        if timestamps.duplicated().any():
            raise ValueError(f"{symbol} bars contain duplicate timestamps")
        if ((timestamps + self._interval) > decision_time).any():
            raise ValueError(f"{symbol} bars contain information unavailable at decision time")

        closes = pd.to_numeric(frame["close"], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(closes).all() or (closes <= 0).any():
            raise ValueError(f"{symbol} bars contain invalid close prices")

        ordered = pd.DataFrame({"open_time": timestamps, "close": closes}).sort_values("open_time")
        required_rows = self.config.volatility_bars + 1
        if len(ordered) < required_rows:
            return None
        tail = ordered.iloc[-required_rows:]
        expected_last = decision_time - self._interval
        if pd.Timestamp(tail["open_time"].iloc[-1]) != expected_last:
            return None
        differences = pd.DatetimeIndex(tail["open_time"]).to_series().diff().iloc[1:]
        if not differences.eq(self._interval).all():
            return None

        log_prices = np.log(tail["close"].to_numpy(dtype=float))
        log_returns = np.diff(log_prices)
        realized_scale = float(np.sqrt(np.mean(np.square(log_returns))))
        momentum = float(log_prices[-1] - log_prices[-1 - self.config.confirmation_bars])
        if realized_scale <= np.finfo(float).eps:
            return 0.0
        denominator = realized_scale * math.sqrt(self.config.confirmation_bars)
        return momentum / denominator

    def _funding_pressure(
        self,
        funding: pd.DataFrame,
        *,
        decision_time: pd.Timestamp,
        eligible: frozenset[str],
    ) -> dict[str, float]:
        required = {"funding_time", "symbol", "funding_rate"}
        if not isinstance(funding, pd.DataFrame) or not required.issubset(funding.columns):
            raise ValueError("funding context lacks required columns")
        if funding.empty:
            return {}

        times = pd.to_datetime(funding["funding_time"], utc=True, errors="coerce")
        symbols = funding["symbol"].astype(str)
        rates = pd.to_numeric(funding["funding_rate"], errors="coerce").to_numpy(dtype=float)
        if times.isna().any() or not np.isfinite(rates).all():
            raise ValueError("funding context contains invalid values")
        if (times >= decision_time).any():
            raise ValueError("funding context contains a non-past event")
        if not set(symbols).issubset(eligible):
            raise ValueError("funding context contains an ineligible symbol")

        normalized = pd.DataFrame(
            {"funding_time": times, "symbol": symbols.to_numpy(), "funding_rate": rates}
        )
        if normalized.duplicated(["funding_time", "symbol"]).any():
            raise ValueError("funding context contains duplicate symbol events")

        lookback = pd.Timedelta(hours=self.config.funding_lookback_hours)
        recent = normalized[
            (normalized["funding_time"] >= decision_time - lookback)
            & (normalized["funding_time"] < decision_time)
        ]
        pressure: dict[str, float] = {}
        log_two = math.log(2.0)
        slot_ages = np.arange(
            self.config.interval_hours,
            self.config.funding_lookback_hours + 1,
            self.config.interval_hours,
            dtype=float,
        )
        slot_normalizer = float(
            np.exp(-log_two * slot_ages / self.config.funding_half_life_hours).sum()
        )
        for symbol, group in recent.groupby("symbol", observed=True, sort=True):
            ordered = group.sort_values("funding_time")
            if len(ordered) < self.config.minimum_funding_events:
                continue
            latest = pd.Timestamp(ordered["funding_time"].iloc[-1])
            latest_age = (decision_time - latest) / pd.Timedelta(hours=1)
            if latest_age > self.config.maximum_funding_age_hours:
                continue
            ages = (
                (decision_time - pd.DatetimeIndex(ordered["funding_time"])) / pd.Timedelta(hours=1)
            ).to_numpy(dtype=float)
            weights = np.exp(-log_two * ages / self.config.funding_half_life_hours)
            observed_rates = ordered["funding_rate"].to_numpy(dtype=float)
            decayed_carry = float(np.dot(weights, observed_rates) / slot_normalizer)
            absolute_mass = float(np.dot(weights, np.abs(observed_rates)))
            persistence = abs(float(np.dot(weights, observed_rates))) / (
                absolute_mass + self.config.funding_rate_floor
            )
            persistence = min(1.0, max(0.0, persistence))
            pressure[str(symbol)] = decayed_carry * (
                1.0 + self.config.funding_persistence_weight * persistence
            )
        return pressure

    def target_weights(self, context: object, *, seed: int) -> Mapping[str, float] | None:
        """Return balanced signed targets, explicit flat, or ``None`` between daily reviews."""

        if (
            isinstance(seed, bool)
            or not isinstance(seed, numbers.Integral)
            or seed != self.config.expected_seed
        ):
            raise ValueError("strategy seed differs from the frozen seed")
        decision_time = _utc_timestamp(getattr(context, "decision_time"), "decision_time")
        if decision_time.minute or decision_time.second or decision_time.microsecond:
            raise ValueError("decision_time must lie on an exact hourly boundary")
        if decision_time.hour != self.config.rebalance_hour_utc:
            return None

        raw_eligible = tuple(str(symbol) for symbol in getattr(context, "eligible_symbols"))
        if len(raw_eligible) != len(set(raw_eligible)):
            raise ValueError("eligible_symbols contains duplicates")
        eligible = frozenset(raw_eligible)
        raw_bars = getattr(context, "bars")
        if not isinstance(raw_bars, Mapping):
            raise TypeError("bars must be a symbol-to-dataframe mapping")
        if {str(symbol) for symbol in raw_bars} != eligible:
            raise ValueError("bar context must match the eligible-symbol set exactly")

        price_raw: dict[str, float] = {}
        for symbol in sorted(eligible):
            statistic = self._price_confirmation(
                raw_bars[symbol], decision_time=decision_time, symbol=symbol
            )
            if statistic is not None and math.isfinite(statistic):
                price_raw[symbol] = statistic

        funding_raw = self._funding_pressure(
            getattr(context, "funding"),
            decision_time=decision_time,
            eligible=eligible,
        )
        valid_symbols = sorted(set(price_raw) & set(funding_raw))
        if len(valid_symbols) < self.config.minimum_cross_section:
            return {}

        funding_ranks = _centered_ranks({symbol: funding_raw[symbol] for symbol in valid_symbols})
        price_ranks = _centered_ranks({symbol: price_raw[symbol] for symbol in valid_symbols})

        # This is the single declared A5 score object.  Positive values mean long desirability;
        # negative values mean short desirability.  The offset keeps direction stable over the
        # complete rank domain, while magnitude 2.0 is exactly the joint crowding/confirmation
        # pass boundary.  No threshold filtering, side selection, weight cap, or risk action has
        # occurred at this capture boundary.
        scores: dict[str, float] = {}
        for symbol in valid_symbols:
            crowding = float(funding_ranks[symbol])
            desired_direction = -1.0 if crowding > 0 else 1.0 if crowding < 0 else 0.0
            confirmation = desired_direction * float(price_ranks[symbol])
            if desired_direction == 0.0:
                score = 0.0
            else:
                joint_margin = min(
                    abs(crowding) - self.config.crowding_threshold,
                    confirmation - self.config.confirmation_threshold,
                )
                score = desired_direction * (_PASSING_SCORE_MAGNITUDE + joint_margin)
            scores[str(symbol)] = float(score)

        if type(scores) is not dict or any(
            type(symbol) is not str or type(value) is not float or not math.isfinite(value)
            for symbol, value in scores.items()
        ):
            raise TypeError("declared score boundary requires a finite built-in dict[str, float]")
        expected_score_keys = frozenset(valid_symbols)
        captured_scores = score_boundary(scores)
        if captured_scores is not scores:
            raise ValueError("declared score boundary changed score object identity")
        if type(captured_scores) is not dict or frozenset(captured_scores) != expected_score_keys:
            raise ValueError("declared score boundary changed exact score keys")
        if any(
            type(symbol) is not str or type(value) is not float or not math.isfinite(value)
            for symbol, value in captured_scores.items()
        ):
            raise TypeError("declared score boundary returned invalid score values")

        long_candidates: list[tuple[float, str]] = []
        short_candidates: list[tuple[float, str]] = []
        for symbol in sorted(captured_scores):
            captured_score = captured_scores[symbol]
            if abs(captured_score) < _PASSING_SCORE_MAGNITUDE:
                continue
            candidate = (abs(captured_score), symbol)
            if captured_score > 0:
                long_candidates.append(candidate)
            elif captured_score < 0:
                short_candidates.append(candidate)

        long_candidates.sort(key=lambda item: (-item[0], item[1]))
        short_candidates.sort(key=lambda item: (-item[0], item[1]))
        if (
            len(long_candidates) < self.config.minimum_symbols_per_side
            or len(short_candidates) < self.config.minimum_symbols_per_side
        ):
            return {}
        selected_longs = long_candidates[: self.config.maximum_symbols_per_side]
        selected_shorts = short_candidates[: self.config.maximum_symbols_per_side]

        long_gross = min(
            self.config.target_side_gross,
            len(selected_longs) * self.config.maximum_symbol_weight,
        )
        short_gross = min(
            self.config.target_side_gross,
            len(selected_shorts) * self.config.maximum_symbol_weight,
        )
        # Equal gross on both sides is a mechanism constraint, not an estimated hedge ratio.
        paired_gross = min(long_gross, short_gross)
        result = _allocate_capped_side(
            selected_longs,
            gross=paired_gross,
            maximum_symbol_weight=self.config.maximum_symbol_weight,
            direction=1.0,
        )
        result.update(
            _allocate_capped_side(
                selected_shorts,
                gross=paired_gross,
                maximum_symbol_weight=self.config.maximum_symbol_weight,
                direction=-1.0,
            )
        )
        return result


def build_strategy() -> FundingCrowdingStrategy:
    """Canonical no-I/O factory required by the organizer worker."""

    return FundingCrowdingStrategy(StrategyConfig())
