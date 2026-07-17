"""Team09 pivot-01: conditional carry-unwind and downside-fragility routing.

The initial funding-crowding unwind performed well in bull and chop but failed decisively in bear
conditions.  In broad crypto selloffs, very low funding can identify distressed falling knives,
while high relative funding can belong to resilient contracts.  Pivot-01 therefore routes a
causally detected broad decline to a different economic mechanism: long relative resilience and
short downside fragility.  Outside that state it retains the confirmed funding-crowding unwind.

This is a signal/mechanism pivot, not a risk overlay.  Both routes use the same balanced gross,
symbol cap, daily schedule, no-control policy, and central execution contract.

Amendment 0006 is the upstream native-crypto universe authority.  This strategy consumes only its
eligible-symbol context and deliberately does not infer eligibility from ticker text or from the
mere existence of a Binance perpetual listing.
"""

from __future__ import annotations

import dataclasses
import math
import numbers
from collections.abc import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

FAMILY_ID = "team09-conditional-carry-fragility-v1"
CANDIDATE_ID = "team09-ccf-pivot01-v1"
SCORE_ADAPTER_ID = "top40-v2-declared-score-boundary-v1"
SCORE_CAPTURE_BOUNDARY = "candidate-declared-post-transform-pre-selection-weight-cap-risk"
_PASSING_SCORE_MAGNITUDE = 2.0


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    """Complete deterministic pivot-01 parameterization."""

    interval_hours: int = 8
    rebalance_hour_utc: int = 0
    funding_lookback_hours: int = 168
    minimum_funding_events: int = 12
    funding_half_life_hours: float = 72.0
    funding_rate_floor: float = 1e-7
    funding_persistence_weight: float = 0.5
    maximum_funding_age_hours: int = 16
    normal_confirmation_bars: int = 9
    fragility_bars: int = 63
    bear_trend_bars: int = 21
    minimum_down_market_bars: int = 6
    minimum_cross_section: int = 12
    bear_market_return_threshold: float = -0.04
    bear_negative_breadth_threshold: float = 0.65
    normal_crowding_threshold: float = 0.30
    normal_confirmation_threshold: float = 0.10
    bear_score_threshold: float = 0.35
    bear_relative_trend_weight: float = 0.45
    bear_downside_resilience_weight: float = 0.35
    bear_drawdown_resilience_weight: float = 0.20
    minimum_symbols_per_side: int = 4
    maximum_symbols_per_side: int = 6
    target_side_gross: float = 0.45
    maximum_symbol_weight: float = 0.09
    expected_seed: int = 20260801

    def validate(self) -> None:
        integer_fields = (
            self.interval_hours,
            self.rebalance_hour_utc,
            self.funding_lookback_hours,
            self.minimum_funding_events,
            self.maximum_funding_age_hours,
            self.normal_confirmation_bars,
            self.fragility_bars,
            self.bear_trend_bars,
            self.minimum_down_market_bars,
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
            self.bear_market_return_threshold,
            self.bear_negative_breadth_threshold,
            self.normal_crowding_threshold,
            self.normal_confirmation_threshold,
            self.bear_score_threshold,
            self.bear_relative_trend_weight,
            self.bear_downside_resilience_weight,
            self.bear_drawdown_resilience_weight,
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
        if (
            not 2
            <= self.minimum_funding_events
            <= (self.funding_lookback_hours // self.interval_hours)
        ):
            raise ValueError("minimum_funding_events is infeasible for the funding lookback")
        if self.funding_half_life_hours <= 0 or self.funding_rate_floor <= 0:
            raise ValueError("funding decay and floor must be positive")
        if not 0 <= self.funding_persistence_weight <= 1:
            raise ValueError("funding_persistence_weight must be in [0, 1]")
        if (
            not self.interval_hours
            <= self.maximum_funding_age_hours
            <= (self.funding_lookback_hours)
        ):
            raise ValueError("maximum_funding_age_hours is outside the funding window")
        if self.normal_confirmation_bars < 2:
            raise ValueError("normal_confirmation_bars must be at least two")
        if self.bear_trend_bars < 2:
            raise ValueError("bear_trend_bars must be at least two")
        if self.fragility_bars < max(self.normal_confirmation_bars, self.bear_trend_bars):
            raise ValueError("fragility_bars must cover both signal horizons")
        if not 2 <= self.minimum_down_market_bars <= self.fragility_bars:
            raise ValueError("minimum_down_market_bars is infeasible")
        if self.minimum_cross_section < 2 * self.minimum_symbols_per_side:
            raise ValueError("minimum_cross_section cannot support both required sleeves")
        if not -1 < self.bear_market_return_threshold < 0:
            raise ValueError("bear_market_return_threshold must be in (-1, 0)")
        unit_interval = (
            self.bear_negative_breadth_threshold,
            self.normal_crowding_threshold,
            self.normal_confirmation_threshold,
            self.bear_score_threshold,
        )
        if any(not 0 <= value <= 1 for value in unit_interval):
            raise ValueError("breadth and score thresholds must be in [0, 1]")
        route_weights = (
            self.bear_relative_trend_weight,
            self.bear_downside_resilience_weight,
            self.bear_drawdown_resilience_weight,
        )
        if any(weight < 0 for weight in route_weights) or not math.isclose(
            sum(route_weights), 1.0, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("bear-route weights must be nonnegative and sum to one")
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
            raise ValueError("expected_seed must be nonnegative")


@dataclasses.dataclass(frozen=True)
class _PriceFeatures:
    normal_confirmation: float
    bear_horizon_return: float
    maximum_drawdown: float
    log_returns: np.ndarray


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
    remaining = float(gross)
    active = [(symbol, float(magnitude)) for magnitude, symbol in candidates]
    allocations: dict[str, float] = {}
    while active and remaining > np.finfo(float).eps:
        total_strength = sum(strength for _symbol, strength in active)
        if total_strength <= 0 or not math.isfinite(total_strength):
            raise ValueError("captured side scores cannot support allocation")
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
        raise ValueError("captured scores could not satisfy gross allocation")
    return allocations


class ConditionalCarryFragilityStrategy:
    """Route normal markets to carry unwind and broad declines to fragility sorting."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()
        self.config.validate()

    @property
    def _interval(self) -> pd.Timedelta:
        return pd.Timedelta(hours=self.config.interval_hours)

    def _price_features(
        self,
        frame: pd.DataFrame,
        *,
        decision_time: pd.Timestamp,
        symbol: str,
    ) -> _PriceFeatures | None:
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
            raise ValueError(f"{symbol} bars contain unavailable information")
        closes = pd.to_numeric(frame["close"], errors="coerce").to_numpy(dtype=float)
        if not np.isfinite(closes).all() or (closes <= 0).any():
            raise ValueError(f"{symbol} bars contain invalid close prices")
        ordered = pd.DataFrame({"open_time": timestamps, "close": closes}).sort_values("open_time")
        required_rows = self.config.fragility_bars + 1
        if len(ordered) < required_rows:
            return None
        tail = ordered.iloc[-required_rows:]
        if pd.Timestamp(tail["open_time"].iloc[-1]) != decision_time - self._interval:
            return None
        differences = pd.DatetimeIndex(tail["open_time"]).to_series().diff().iloc[1:]
        if not differences.eq(self._interval).all():
            return None
        log_prices = np.log(tail["close"].to_numpy(dtype=float))
        log_returns = np.diff(log_prices)
        realized_scale = float(np.sqrt(np.mean(np.square(log_returns))))
        confirmation_move = float(
            log_prices[-1] - log_prices[-1 - self.config.normal_confirmation_bars]
        )
        normal_confirmation = (
            0.0
            if realized_scale <= np.finfo(float).eps
            else confirmation_move
            / (realized_scale * math.sqrt(self.config.normal_confirmation_bars))
        )
        bear_horizon_return = float(log_prices[-1] - log_prices[-1 - self.config.bear_trend_bars])
        running_peak = np.maximum.accumulate(log_prices)
        maximum_drawdown = float(np.max(1.0 - np.exp(log_prices - running_peak)))
        return _PriceFeatures(
            normal_confirmation=float(normal_confirmation),
            bear_horizon_return=bear_horizon_return,
            maximum_drawdown=maximum_drawdown,
            log_returns=log_returns,
        )

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
        pressure: dict[str, float] = {}
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

    def _bear_route_scores(
        self,
        features: Mapping[str, _PriceFeatures],
        symbols: list[str],
        market_returns: np.ndarray,
        market_horizon_return: float,
    ) -> dict[str, float]:
        down_mask = market_returns < 0
        market_down = market_returns[down_mask]
        denominator = float(np.dot(market_down, market_down))
        downside_beta: dict[str, float] = {}
        for symbol in symbols:
            symbol_down = features[symbol].log_returns[down_mask]
            downside_beta[symbol] = (
                0.0
                if down_mask.sum() < self.config.minimum_down_market_bars
                or denominator <= np.finfo(float).eps
                else float(np.dot(symbol_down, market_down) / denominator)
            )
        relative_trend_rank = _centered_ranks(
            {
                symbol: features[symbol].bear_horizon_return - market_horizon_return
                for symbol in symbols
            }
        )
        downside_resilience_rank = _centered_ranks(
            {symbol: -downside_beta[symbol] for symbol in symbols}
        )
        drawdown_resilience_rank = _centered_ranks(
            {symbol: -features[symbol].maximum_drawdown for symbol in symbols}
        )
        composite = {
            symbol: self.config.bear_relative_trend_weight * relative_trend_rank[symbol]
            + self.config.bear_downside_resilience_weight * downside_resilience_rank[symbol]
            + self.config.bear_drawdown_resilience_weight * drawdown_resilience_rank[symbol]
            for symbol in symbols
        }
        ranked = _centered_ranks(composite)
        scores: dict[str, float] = {}
        for symbol in symbols:
            desirability = float(ranked[symbol])
            direction = 1.0 if desirability > 0 else -1.0 if desirability < 0 else 0.0
            margin = abs(desirability) - self.config.bear_score_threshold
            scores[str(symbol)] = float(
                0.0 if direction == 0.0 else direction * (_PASSING_SCORE_MAGNITUDE + margin)
            )
        return scores

    def _normal_route_scores(
        self,
        features: Mapping[str, _PriceFeatures],
        funding: Mapping[str, float],
        symbols: list[str],
    ) -> dict[str, float]:
        funding_rank = _centered_ranks({symbol: funding[symbol] for symbol in symbols})
        confirmation_rank = _centered_ranks(
            {symbol: features[symbol].normal_confirmation for symbol in symbols}
        )
        scores: dict[str, float] = {}
        for symbol in symbols:
            crowding = float(funding_rank[symbol])
            direction = -1.0 if crowding > 0 else 1.0 if crowding < 0 else 0.0
            aligned_confirmation = direction * float(confirmation_rank[symbol])
            margin = min(
                abs(crowding) - self.config.normal_crowding_threshold,
                aligned_confirmation - self.config.normal_confirmation_threshold,
            )
            scores[str(symbol)] = float(
                0.0 if direction == 0.0 else direction * (_PASSING_SCORE_MAGNITUDE + margin)
            )
        return scores

    def target_weights(self, context: object, *, seed: int) -> Mapping[str, float] | None:
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
        features: dict[str, _PriceFeatures] = {}
        for symbol in sorted(eligible):
            value = self._price_features(
                raw_bars[symbol], decision_time=decision_time, symbol=symbol
            )
            if value is not None:
                features[symbol] = value
        funding = self._funding_pressure(
            getattr(context, "funding"), decision_time=decision_time, eligible=eligible
        )
        valid_symbols = sorted(set(features) & set(funding))
        if len(valid_symbols) < self.config.minimum_cross_section:
            return {}
        return_matrix = np.column_stack([features[symbol].log_returns for symbol in valid_symbols])
        market_returns = np.median(return_matrix, axis=1)
        market_horizon_return = float(market_returns[-self.config.bear_trend_bars :].sum())
        negative_breadth = float(
            np.mean([features[symbol].bear_horizon_return < 0 for symbol in valid_symbols])
        )
        bear_route = (
            market_horizon_return <= self.config.bear_market_return_threshold
            and negative_breadth >= self.config.bear_negative_breadth_threshold
        )
        scores = (
            self._bear_route_scores(features, valid_symbols, market_returns, market_horizon_return)
            if bear_route
            else self._normal_route_scores(features, funding, valid_symbols)
        )

        # The routed, fully transformed signed long-desirability dictionary is the one declared
        # A5 score object.  No threshold filtering, side selection, weight cap, or risk action has
        # occurred before this single identity boundary.
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
        paired_gross = min(
            self.config.target_side_gross,
            len(selected_longs) * self.config.maximum_symbol_weight,
            len(selected_shorts) * self.config.maximum_symbol_weight,
        )
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


def build_strategy() -> ConditionalCarryFragilityStrategy:
    return ConditionalCarryFragilityStrategy(StrategyConfig())
