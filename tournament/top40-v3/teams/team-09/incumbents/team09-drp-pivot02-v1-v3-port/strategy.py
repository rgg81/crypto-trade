"""Team09 pivot-02: defensive residual persistence with embedded crash exclusion.

Both earlier Team09 mechanisms failed catastrophically while requesting 0.90 gross; pivot-01
became insolvent.  Pivot-02 therefore uses one invariant cross-sectional mechanism rather than
another market-state router: persistent
relative leaders are held long and persistent relative laggards short, but only after the most
crash-fragile names are removed from both sleeves.  Remaining positions are shrunk directly by
the captured safety-adjusted score.  The construction rebalances every 72 hours, requests at most
0.20 gross at its center, and never scales a sleeve upward to restore a gross target.

Crash exclusion, score shrinkage, breadth, gross, and symbol caps are part of the alpha/portfolio
construction itself.  They do not inspect portfolio state and are not an optional risk overlay.
Amendment 0006 is the upstream native-crypto universe authority; ticker text and the mere presence
of a Binance perpetual listing are deliberately not treated as eligibility evidence here.
"""

from __future__ import annotations

import dataclasses
import math
import numbers
from collections.abc import Mapping

import numpy as np
import pandas as pd

from score_adapter_identity import score_boundary

FAMILY_ID = "team09-defensive-residual-persistence-v1"
CANDIDATE_ID = "team09-drp-pivot02-v1"
SCORE_ADAPTER_ID = "top40-v3-candidate-local-declared-score-boundary-v1"
SCORE_CAPTURE_BOUNDARY = "candidate-declared-post-transform-pre-selection-weight-cap-risk"
_EPOCH_ANCHOR = pd.Timestamp("1970-01-01T00:00:00Z")
_MINIMUM_SCORE_MULTIPLIER = 0.35


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    """Complete deterministic pivot-02 parameterization."""

    interval_hours: int = 8
    rebalance_every_bars: int = 9
    persistence_block_count: int = 3
    persistence_block_bars: int = 90
    fragility_bars: int = 90
    minimum_cross_section: int = 20
    fragility_exclusion_quantile: float = 0.80
    downside_semideviation_weight: float = 0.40
    jump_risk_weight: float = 0.35
    drawdown_weight: float = 0.25
    fragility_shrink_strength: float = 0.60
    minimum_symbols_per_side: int = 6
    maximum_symbols_per_side: int = 8
    target_side_gross: float = 0.10
    maximum_symbol_weight: float = 0.015
    expected_seed: int = 20260718

    def validate(self) -> None:
        integer_fields = (
            self.interval_hours,
            self.rebalance_every_bars,
            self.persistence_block_count,
            self.persistence_block_bars,
            self.fragility_bars,
            self.minimum_cross_section,
            self.minimum_symbols_per_side,
            self.maximum_symbols_per_side,
            self.expected_seed,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, numbers.Integral)
            for value in integer_fields
        ):
            raise ValueError("hours, bar counts, symbol counts, and seed must be integers")
        numeric_fields = (
            self.fragility_exclusion_quantile,
            self.downside_semideviation_weight,
            self.jump_risk_weight,
            self.drawdown_weight,
            self.fragility_shrink_strength,
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
        if self.rebalance_every_bars < 2:
            raise ValueError("rebalance_every_bars must make the construction slower than one bar")
        if self.persistence_block_count < 2 or self.persistence_block_bars < 3:
            raise ValueError("persistence history requires at least two blocks of three bars")
        history_bars = self.persistence_block_count * self.persistence_block_bars
        if not 3 <= self.fragility_bars <= history_bars:
            raise ValueError("fragility_bars must fit inside the persistence history")
        if self.minimum_symbols_per_side < 1:
            raise ValueError("minimum_symbols_per_side must be positive")
        if self.maximum_symbols_per_side < self.minimum_symbols_per_side:
            raise ValueError("maximum_symbols_per_side is below the minimum")
        if self.minimum_cross_section < 2 * self.minimum_symbols_per_side:
            raise ValueError("minimum_cross_section cannot support both required sleeves")
        if not 0.5 < self.fragility_exclusion_quantile < 1.0:
            raise ValueError("fragility_exclusion_quantile must be in (0.5, 1)")
        minimum_safe_count = (
            math.floor(self.fragility_exclusion_quantile * (self.minimum_cross_section - 1)) + 1
        )
        if minimum_safe_count < 2 * self.minimum_symbols_per_side:
            raise ValueError("fragility exclusion cannot leave both required sleeves")
        fragility_weights = (
            self.downside_semideviation_weight,
            self.jump_risk_weight,
            self.drawdown_weight,
        )
        if any(weight < 0 for weight in fragility_weights) or not math.isclose(
            sum(fragility_weights), 1.0, rel_tol=0.0, abs_tol=1e-12
        ):
            raise ValueError("fragility weights must be nonnegative and sum to one")
        if not 0.0 <= self.fragility_shrink_strength <= 1.0:
            raise ValueError("fragility_shrink_strength must be in [0, 1]")
        if not 0.0 < self.target_side_gross <= 0.15:
            raise ValueError("target_side_gross must be in (0, 0.15]")
        if not 0.0 < self.maximum_symbol_weight <= 0.02:
            raise ValueError("maximum_symbol_weight must be in (0, 0.02]")
        if self.target_side_gross / self.maximum_symbols_per_side > self.maximum_symbol_weight:
            raise ValueError("maximum_symbol_weight is below the structural base allocation")
        if self.expected_seed < 0:
            raise ValueError("expected_seed must be nonnegative")


@dataclasses.dataclass(frozen=True)
class _PriceFeatures:
    log_returns: np.ndarray
    downside_semideviation: float
    maximum_absolute_return: float
    maximum_drawdown: float


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
        return {str(symbol): 0.0 for symbol in values}
    ordered = pd.Series(
        {str(symbol): float(values[symbol]) for symbol in sorted(values)}, dtype=float
    )
    ranks = ordered.rank(method="average")
    centered = 2.0 * (ranks - 1.0) / (len(ordered) - 1.0) - 1.0
    return {str(symbol): float(value) for symbol, value in centered.items()}


def _unit_ranks(values: Mapping[str, float]) -> dict[str, float]:
    if len(values) < 2:
        return {str(symbol): 0.5 for symbol in values}
    ordered = pd.Series(
        {str(symbol): float(values[symbol]) for symbol in sorted(values)}, dtype=float
    )
    ranks = ordered.rank(method="average")
    unit = (ranks - 1.0) / (len(ordered) - 1.0)
    return {str(symbol): float(value) for symbol, value in unit.items()}


def _capture_scores(scores: dict[str, float], *, expected_keys: frozenset[str]) -> dict[str, float]:
    """Capture the one operative A5 object on every scheduled decision path."""
    if type(scores) is not dict or any(
        type(symbol) is not str or type(value) is not float or not math.isfinite(value)
        for symbol, value in scores.items()
    ):
        raise TypeError("declared score boundary requires a finite built-in dict[str, float]")
    captured_scores = score_boundary(scores)
    if captured_scores is not scores:
        raise ValueError("declared score boundary changed score object identity")
    if type(captured_scores) is not dict or frozenset(captured_scores) != expected_keys:
        raise ValueError("declared score boundary changed exact score keys")
    if any(
        type(symbol) is not str or type(value) is not float or not math.isfinite(value)
        for symbol, value in captured_scores.items()
    ):
        raise TypeError("declared score boundary returned invalid score values")
    return captured_scores


class DefensiveResidualPersistenceStrategy:
    """Build a slow, low-gross, crash-screened relative-persistence book."""

    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()
        self.config.validate()

    @property
    def _interval(self) -> pd.Timedelta:
        return pd.Timedelta(hours=self.config.interval_hours)

    @property
    def _history_bars(self) -> int:
        return self.config.persistence_block_count * self.config.persistence_block_bars

    def _decision_index(self, decision_time: pd.Timestamp) -> int:
        elapsed = decision_time - _EPOCH_ANCHOR
        if elapsed < pd.Timedelta(0):
            raise ValueError("decision_time precedes the frozen schedule anchor")
        quotient = elapsed / self._interval
        if not float(quotient).is_integer():
            raise ValueError("decision_time does not lie on the exact eight-hour grid")
        return int(quotient)

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
        if "symbol" in frame.columns and not frame["symbol"].eq(symbol).all():
            raise ValueError(f"{symbol} bars contain a mismatched symbol")
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
        required_rows = self._history_bars + 1
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
        recent_returns = log_returns[-self.config.fragility_bars :]
        downside = np.minimum(recent_returns, 0.0)
        downside_semideviation = float(np.sqrt(np.mean(np.square(downside))))
        maximum_absolute_return = float(np.max(np.abs(recent_returns)))
        recent_prices = log_prices[-(self.config.fragility_bars + 1) :]
        running_peak = np.maximum.accumulate(recent_prices)
        maximum_drawdown = float(np.max(1.0 - np.exp(recent_prices - running_peak)))
        return _PriceFeatures(
            log_returns=log_returns,
            downside_semideviation=downside_semideviation,
            maximum_absolute_return=maximum_absolute_return,
            maximum_drawdown=maximum_drawdown,
        )

    def _transformed_scores(
        self, features: Mapping[str, _PriceFeatures], symbols: list[str]
    ) -> dict[str, float]:
        downside_rank = _unit_ranks(
            {symbol: features[symbol].downside_semideviation for symbol in symbols}
        )
        jump_rank = _unit_ranks(
            {symbol: features[symbol].maximum_absolute_return for symbol in symbols}
        )
        drawdown_rank = _unit_ranks(
            {symbol: features[symbol].maximum_drawdown for symbol in symbols}
        )
        fragility_composite = {
            symbol: self.config.downside_semideviation_weight * downside_rank[symbol]
            + self.config.jump_risk_weight * jump_rank[symbol]
            + self.config.drawdown_weight * drawdown_rank[symbol]
            for symbol in symbols
        }
        fragility_percentile = _unit_ranks(fragility_composite)
        safe_symbols = [
            symbol
            for symbol in symbols
            if fragility_percentile[symbol] <= self.config.fragility_exclusion_quantile
        ]
        if len(safe_symbols) < 2 * self.config.minimum_symbols_per_side:
            return {str(symbol): 0.0 for symbol in symbols}

        return_matrix = np.column_stack([features[symbol].log_returns for symbol in symbols])
        market_returns = np.median(return_matrix, axis=1)
        residual_returns = return_matrix - market_returns[:, np.newaxis]
        block_ranks: list[dict[str, float]] = []
        for block_index in range(self.config.persistence_block_count):
            start = block_index * self.config.persistence_block_bars
            stop = start + self.config.persistence_block_bars
            block_ranks.append(
                _centered_ranks(
                    {
                        symbol: float(residual_returns[start:stop, column].sum())
                        for column, symbol in enumerate(symbols)
                    }
                )
            )
        persistence: dict[str, float] = {}
        for symbol in safe_symbols:
            values = [ranks[symbol] for ranks in block_ranks]
            average = float(np.mean(values))
            if average == 0.0:
                persistence[symbol] = 0.0
                continue
            direction = 1.0 if average > 0.0 else -1.0
            agreement = sum(direction * value > 0.0 for value in values) / len(values)
            persistence[symbol] = average * (0.5 + 0.5 * agreement)
        desirability = _centered_ranks(persistence)

        scores = {str(symbol): 0.0 for symbol in symbols}
        for symbol in safe_symbols:
            direction = (
                1.0 if desirability[symbol] > 0.0 else -1.0 if desirability[symbol] < 0.0 else 0.0
            )
            if direction == 0.0:
                continue
            safety = 1.0 - (self.config.fragility_shrink_strength * fragility_percentile[symbol])
            conviction = abs(desirability[symbol])
            magnitude = _MINIMUM_SCORE_MULTIPLIER + (
                (1.0 - _MINIMUM_SCORE_MULTIPLIER) * conviction * safety
            )
            scores[str(symbol)] = float(direction * magnitude)
        return scores

    def _score_shrunk_side(
        self,
        candidates: list[tuple[float, str]],
        *,
        direction: float,
    ) -> dict[str, float]:
        base_weight = self.config.target_side_gross / self.config.maximum_symbols_per_side
        result: dict[str, float] = {}
        for magnitude, symbol in candidates[: self.config.maximum_symbols_per_side]:
            multiplier = min(1.0, max(0.0, float(magnitude)))
            amount = min(self.config.maximum_symbol_weight, base_weight * multiplier)
            if amount > 0.0:
                result[symbol] = float(direction * amount)
        return result

    def target_weights(self, context: object, *, seed: int) -> Mapping[str, float] | None:
        if (
            isinstance(seed, bool)
            or not isinstance(seed, numbers.Integral)
            or seed != self.config.expected_seed
        ):
            raise ValueError("strategy seed differs from the frozen seed")
        decision_time = _utc_timestamp(getattr(context, "decision_time"), "decision_time")
        if self._decision_index(decision_time) % self.config.rebalance_every_bars:
            return None
        raw_eligible = tuple(getattr(context, "eligible_symbols"))
        if any(type(symbol) is not str for symbol in raw_eligible):
            raise TypeError("eligible_symbols must contain built-in strings")
        if len(raw_eligible) != len(set(raw_eligible)):
            raise ValueError("eligible_symbols contains duplicates")
        eligible = frozenset(raw_eligible)
        raw_bars = getattr(context, "bars")
        if not isinstance(raw_bars, Mapping):
            raise TypeError("bars must be a symbol-to-dataframe mapping")
        if any(type(symbol) is not str for symbol in raw_bars):
            raise TypeError("bar mapping keys must be built-in strings")
        if frozenset(raw_bars) != eligible:
            raise ValueError("bar context must match the eligible-symbol set exactly")
        features: dict[str, _PriceFeatures] = {}
        for symbol in sorted(eligible):
            value = self._price_features(
                raw_bars[symbol], decision_time=decision_time, symbol=symbol
            )
            if value is not None:
                features[symbol] = value
        valid_symbols = sorted(features)
        if len(valid_symbols) < self.config.minimum_cross_section:
            return _capture_scores({}, expected_keys=frozenset())
        scores = self._transformed_scores(features, valid_symbols)

        # This is the one operative A5 object: crash exclusion is encoded as exact zero and score
        # magnitude already contains persistence conviction and fragility shrinkage.  No sleeve
        # selection, position weight, cap, pairing, or optional risk action has occurred yet.
        expected_score_keys = frozenset(valid_symbols)
        captured_scores = _capture_scores(scores, expected_keys=expected_score_keys)

        long_candidates = [
            (float(score), symbol) for symbol, score in captured_scores.items() if score > 0.0
        ]
        short_candidates = [
            (float(-score), symbol) for symbol, score in captured_scores.items() if score < 0.0
        ]
        long_candidates.sort(key=lambda item: (-item[0], item[1]))
        short_candidates.sort(key=lambda item: (-item[0], item[1]))
        if (
            len(long_candidates) < self.config.minimum_symbols_per_side
            or len(short_candidates) < self.config.minimum_symbols_per_side
        ):
            return {}
        longs = self._score_shrunk_side(long_candidates, direction=1.0)
        shorts = self._score_shrunk_side(short_candidates, direction=-1.0)
        long_gross = sum(longs.values())
        short_gross = -sum(shorts.values())
        paired_gross = min(long_gross, short_gross)
        if paired_gross <= np.finfo(float).eps:
            return {}
        if long_gross > paired_gross:
            scale = paired_gross / long_gross
            longs = {symbol: float(weight * scale) for symbol, weight in longs.items()}
        if short_gross > paired_gross:
            scale = paired_gross / short_gross
            shorts = {symbol: float(weight * scale) for symbol, weight in shorts.items()}
        result = {**longs, **shorts}
        if any(abs(weight) > self.config.maximum_symbol_weight for weight in result.values()):
            raise ValueError("score-shrunk construction exceeded its frozen symbol cap")
        return result


def build_strategy() -> DefensiveResidualPersistenceStrategy:
    return DefensiveResidualPersistenceStrategy(StrategyConfig())
