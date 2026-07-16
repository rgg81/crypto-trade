"""Team 08 volatility-release and cross-sectional-dispersion strategy.

The implementation is deliberately self-contained because the tournament worker copies the team
source bundle into a clean process.  It consumes only closed 8-hour bars supplied through the
public ``DecisionContext`` contract.  It never prices fills, reads files, or uses private state.

On each scheduled construction, one finite built-in score dictionary crosses the organizer's
public A5 identity boundary after the complete VDR transform and before selection, sizing, caps,
or organizer risk.  The exact returned dictionary is the sole signal object used to construct the
portfolio.
"""

from __future__ import annotations

import dataclasses
import math
import numbers
import re
from collections.abc import Mapping, Sequence
from typing import Any

import candidate_variant
import numpy as np
import pandas as pd

from crypto_trade.tournament.score_adapter_protocol_v5 import score_boundary

_SYMBOL_PATTERN = re.compile(r"[A-Z0-9]+USDT")
_BAR_INTERVAL = pd.Timedelta(hours=8)
_REQUIRED_COLUMNS = frozenset({"open_time", "symbol", "close", "quote_volume"})

ACTIVE_FAMILY_ID = "volatility-dispersion-release-v1"
ACTIVE_CANDIDATE_ID = "vdr-core-candidate-001"
MATERIALIZED_CANDIDATE_OVERRIDES: dict[str, dict[str, object]] = {
    ACTIVE_CANDIDATE_ID: {},
}


@dataclasses.dataclass(frozen=True)
class StrategyConfig:
    """Frozen prospective parameters for the first Team 08 candidate."""

    fast_vol_bars: int = 9
    slow_vol_bars: int = 63
    dispersion_lookback_bars: int = 42
    direction_bars: int = 3
    compression_ratio_floor: float = 0.35
    compression_ratio_ceiling: float = 0.86
    expansion_z_floor: float = 1.15
    expansion_z_cap: float = 2.75
    dispersion_fade_ceiling: float = 0.92
    dispersion_continuation_floor: float = 1.22
    minimum_cross_section: int = 12
    minimum_side_positions: int = 5
    side_fraction: float = 0.22
    gross_target: float = 0.80
    maximum_symbol_weight: float = 0.09
    minimum_signal_strength: float = 0.025
    rebalance_hour_utc: int = 0

    def __post_init__(self) -> None:
        integer_fields = (
            self.fast_vol_bars,
            self.slow_vol_bars,
            self.dispersion_lookback_bars,
            self.direction_bars,
            self.minimum_cross_section,
            self.minimum_side_positions,
            self.rebalance_hour_utc,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, numbers.Integral)
            for value in integer_fields
        ):
            raise ValueError("bar counts, position counts, and rebalance hour must be integers")
        if not 2 <= self.fast_vol_bars < self.slow_vol_bars:
            raise ValueError("fast_vol_bars must be at least 2 and below slow_vol_bars")
        if self.dispersion_lookback_bars < 3 or self.direction_bars < 1:
            raise ValueError("dispersion and direction lookbacks must be positive")
        if not 0 < self.compression_ratio_floor < self.compression_ratio_ceiling:
            raise ValueError("compression thresholds must be strictly increasing")
        if not 0 < self.expansion_z_floor < self.expansion_z_cap:
            raise ValueError("expansion thresholds must be strictly increasing")
        if not 0 < self.dispersion_fade_ceiling < self.dispersion_continuation_floor:
            raise ValueError("dispersion thresholds must be strictly increasing")
        if self.minimum_cross_section < 2 * self.minimum_side_positions:
            raise ValueError("cross section cannot support the requested two sleeves")
        if not 0 < self.side_fraction < 0.5:
            raise ValueError("side_fraction must be in (0, 0.5)")
        if not 0 < self.gross_target <= 1:
            raise ValueError("gross_target must be in (0, 1]")
        if not 0 < self.maximum_symbol_weight <= 0.10:
            raise ValueError("maximum_symbol_weight must be in (0, 0.10]")
        if self.gross_target / 2 > self.minimum_side_positions * self.maximum_symbol_weight:
            raise ValueError("minimum side count cannot carry its exposure below the symbol cap")
        if not 0 <= self.minimum_signal_strength < 1:
            raise ValueError("minimum_signal_strength must be in [0, 1)")
        if not 0 <= self.rebalance_hour_utc <= 23:
            raise ValueError("rebalance_hour_utc must be an integer UTC hour")


DEFAULT_CONFIG = StrategyConfig()


def _utc_timestamp(value: Any, label: str) -> pd.Timestamp:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a timestamp") from exc
    if timestamp.tzinfo is None:
        raise ValueError(f"{label} must be timezone-aware")
    return timestamp.tz_convert("UTC")


def _utc_index(values: Any, label: str) -> pd.DatetimeIndex:
    try:
        index = pd.DatetimeIndex(values)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must contain timestamps") from exc
    if index.tz is None:
        raise ValueError(f"{label} must be timezone-aware")
    index = index.tz_convert("UTC")
    if index.hasnans:
        raise ValueError(f"{label} cannot contain missing timestamps")
    return index


def _validate_context(
    context: Any,
) -> tuple[pd.Timestamp, tuple[str, ...], dict[str, pd.DataFrame]]:
    """Validate the complete supplied boundary before any signal decision.

    Rejecting, rather than trimming, a future or malformed row ensures that direct calls cannot
    turn an unauthorized context into an apparently valid prediction.
    """

    decision_time = _utc_timestamp(context.decision_time, "decision_time")
    raw_eligible = context.eligible_symbols
    if isinstance(raw_eligible, (str, bytes)) or not isinstance(raw_eligible, Sequence):
        raise TypeError("eligible_symbols must be a sequence")
    eligible = tuple(str(symbol) for symbol in raw_eligible)
    if len(eligible) != len(set(eligible)):
        raise ValueError("eligible_symbols cannot contain duplicates")
    for symbol in eligible:
        if _SYMBOL_PATTERN.fullmatch(symbol) is None:
            raise ValueError(f"invalid eligible symbol syntax: {symbol!r}")

    if not isinstance(context.bars, Mapping):
        raise TypeError("bars must be a symbol mapping")
    if set(context.bars) != set(eligible):
        raise ValueError("bars keys must exactly match the point-in-time eligible set")
    if not isinstance(context.auxiliary, Mapping) or context.auxiliary:
        raise ValueError("Team 08 does not accept auxiliary data")

    validated: dict[str, pd.DataFrame] = {}
    for symbol in sorted(eligible):
        frame = context.bars[symbol]
        if not isinstance(frame, pd.DataFrame):
            raise TypeError(f"bars[{symbol}] must be a DataFrame")
        missing = _REQUIRED_COLUMNS - set(frame.columns)
        if missing:
            raise ValueError(f"bars[{symbol}] is missing columns: {sorted(missing)}")
        if frame.empty:
            raise ValueError(f"bars[{symbol}] cannot be empty")

        times = _utc_index(frame["open_time"], f"bars[{symbol}].open_time")
        if not times.is_monotonic_increasing or times.has_duplicates:
            raise ValueError(f"bars[{symbol}] timestamps must be strictly increasing")
        if bool(np.any(times + _BAR_INTERVAL > decision_time)):
            raise ValueError(f"bars[{symbol}] contains an unclosed or future bar")
        if not frame["symbol"].astype(str).eq(symbol).all():
            raise ValueError(f"bars[{symbol}] contains a different symbol")

        close = pd.to_numeric(frame["close"], errors="coerce").to_numpy(dtype=float)
        quote_volume = pd.to_numeric(frame["quote_volume"], errors="coerce").to_numpy(dtype=float)
        if not bool(np.isfinite(close).all()) or bool(np.any(close <= 0)):
            raise ValueError(f"bars[{symbol}].close must be finite and positive")
        if not bool(np.isfinite(quote_volume).all()) or bool(np.any(quote_volume < 0)):
            raise ValueError(f"bars[{symbol}].quote_volume must be finite and nonnegative")

        clean = pd.DataFrame(
            {
                "open_time": times,
                "close": close,
                "quote_volume": quote_volume,
            }
        )
        validated[symbol] = clean

    funding = context.funding
    if not isinstance(funding, pd.DataFrame):
        raise TypeError("funding must be a DataFrame")
    if not funding.empty:
        if not {"funding_time", "symbol"}.issubset(funding.columns):
            raise ValueError("nonempty funding data requires funding_time and symbol")
        funding_times = _utc_index(funding["funding_time"], "funding.funding_time")
        if bool(np.any(funding_times >= decision_time)):
            raise ValueError("funding contains a row that was not strictly past")
        if not funding["symbol"].astype(str).isin(eligible).all():
            raise ValueError("funding contains a symbol outside the eligible set")

    return decision_time, eligible, validated


def _contiguous_tail(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the latest strictly 8-hour contiguous suffix."""

    times = pd.DatetimeIndex(frame["open_time"])
    start = len(frame) - 1
    while start > 0 and times[start] - times[start - 1] == _BAR_INTERVAL:
        start -= 1
    return frame.iloc[start:].reset_index(drop=True)


def _return_matrix(
    histories: Mapping[str, pd.DataFrame],
    *,
    decision_time: pd.Timestamp,
    config: StrategyConfig,
) -> pd.DataFrame:
    required_returns = max(
        config.slow_vol_bars + 1,
        config.dispersion_lookback_bars + 1,
        config.direction_bars + 1,
    )
    by_symbol: dict[str, pd.Series] = {}
    for symbol in sorted(histories):
        tail = _contiguous_tail(histories[symbol])
        if len(tail) < required_returns + 1:
            continue
        if pd.Timestamp(tail["open_time"].iloc[-1]) + _BAR_INTERVAL != decision_time:
            continue
        if float(tail["quote_volume"].iloc[-config.slow_vol_bars :].median()) <= 0:
            continue
        close = tail["close"].to_numpy(dtype=float)
        returns = np.diff(np.log(close))
        close_times = pd.DatetimeIndex(tail["open_time"].iloc[1:]) + _BAR_INTERVAL
        by_symbol[symbol] = pd.Series(returns, index=close_times, name=symbol)

    if len(by_symbol) < config.minimum_cross_section:
        return pd.DataFrame()
    matrix = pd.concat(by_symbol.values(), axis=1, join="inner").sort_index()
    matrix = matrix.iloc[-required_returns:]
    if len(matrix) < required_returns or matrix.index[-1] != decision_time:
        return pd.DataFrame()
    if not bool(np.isfinite(matrix.to_numpy(dtype=float)).all()):
        raise ValueError("return matrix is not finite")
    return matrix


def _continuation_mix(residuals: pd.DataFrame, config: StrategyConfig) -> float:
    dispersion = residuals.abs().median(axis=1)
    baseline = float(dispersion.iloc[-config.dispersion_lookback_bars - 1 : -1].median())
    current = float(dispersion.iloc[-1])
    if not math.isfinite(baseline) or not math.isfinite(current):
        raise ValueError("cross-sectional dispersion is not finite")
    scale = max(baseline, 1e-12)
    ratio = current / scale
    return float(
        np.clip(
            (ratio - config.dispersion_fade_ceiling)
            / (config.dispersion_continuation_floor - config.dispersion_fade_ceiling),
            0.0,
            1.0,
        )
    )


def _raw_scores(matrix: pd.DataFrame, config: StrategyConfig) -> pd.Series:
    market_component = matrix.median(axis=1)
    residuals = matrix.sub(market_component, axis=0)
    continuation_mix = _continuation_mix(residuals, config)
    scores: dict[str, float] = {}

    for symbol in sorted(residuals.columns):
        series = residuals[symbol]
        prior = series.iloc[:-1]
        fast_vol = float(prior.iloc[-config.fast_vol_bars :].std(ddof=1))
        slow_vol = float(prior.iloc[-config.slow_vol_bars :].std(ddof=1))
        if not math.isfinite(fast_vol) or not math.isfinite(slow_vol) or slow_vol <= 1e-12:
            continue
        fast_scale = max(fast_vol, 1e-12)
        compression_ratio = fast_vol / slow_vol
        # Compression is an eligibility condition, not merely a zero-valued feature.  Keeping an
        # inactive name at score zero would let cross-sectional median centering move it away from
        # zero and potentially select it.  Exclude it before any centering or ranking instead.
        if compression_ratio >= config.compression_ratio_ceiling:
            continue
        compression_strength = float(
            np.clip(
                (config.compression_ratio_ceiling - compression_ratio)
                / (config.compression_ratio_ceiling - config.compression_ratio_floor),
                0.0,
                1.0,
            )
        )
        latest = float(series.iloc[-1])
        shock_z = abs(latest) / fast_scale
        expansion_strength = float(
            np.clip(
                (shock_z - config.expansion_z_floor)
                / (config.expansion_z_cap - config.expansion_z_floor),
                0.0,
                1.0,
            )
        )
        direction_z = float(
            series.iloc[-config.direction_bars :].sum()
            / (fast_scale * math.sqrt(config.direction_bars))
        )
        continuation = math.tanh(direction_z) * compression_strength * expansion_strength
        failed_release = float(np.clip(shock_z / config.expansion_z_floor, 0.0, 1.0)) * (
            1.0 - expansion_strength
        )
        convergence = -math.tanh(latest / fast_scale) * compression_strength * failed_release
        scores[symbol] = continuation_mix * continuation + (1.0 - continuation_mix) * convergence

    if len(scores) < config.minimum_cross_section:
        return pd.Series(dtype=float)
    raw = pd.Series(scores, dtype=float).sort_index()
    centered = raw - float(raw.median())
    maximum = float(centered.abs().max())
    if not math.isfinite(maximum) or maximum <= 1e-12:
        return pd.Series(dtype=float)
    return centered / maximum


def _capped_allocation(
    conviction: Mapping[str, float], *, budget: float, cap: float
) -> dict[str, float]:
    """Allocate a side budget proportionally, with deterministic water-filling."""

    active = {symbol: abs(float(value)) for symbol, value in conviction.items()}
    if not active or len(active) * cap + 1e-12 < budget:
        return {}
    allocation: dict[str, float] = {}
    remaining_budget = budget
    while active:
        total = sum(active.values())
        if total <= 0:
            return {}
        proposed = {symbol: remaining_budget * value / total for symbol, value in active.items()}
        capped = sorted(symbol for symbol, weight in proposed.items() if weight > cap)
        if not capped:
            allocation.update(proposed)
            break
        for symbol in capped:
            allocation[symbol] = cap
            remaining_budget -= cap
            del active[symbol]
        if remaining_budget < -1e-12:
            return {}
    if abs(sum(allocation.values()) - budget) > 1e-10:
        return {}
    return allocation


def _portfolio(scores: pd.Series, config: StrategyConfig) -> dict[str, float]:
    positive = scores[scores >= config.minimum_signal_strength].sort_values(
        ascending=False, kind="mergesort"
    )
    negative = scores[scores <= -config.minimum_signal_strength].sort_values(
        ascending=True, kind="mergesort"
    )
    side_count = max(
        config.minimum_side_positions,
        int(math.floor(len(scores) * config.side_fraction)),
    )
    side_count = min(side_count, len(scores) // 2)
    if len(positive) < side_count or len(negative) < side_count:
        return {}

    long_scores = positive.iloc[:side_count].to_dict()
    short_scores = negative.iloc[:side_count].to_dict()
    side_budget = config.gross_target / 2.0
    long_allocation = _capped_allocation(
        long_scores, budget=side_budget, cap=config.maximum_symbol_weight
    )
    short_allocation = _capped_allocation(
        short_scores, budget=side_budget, cap=config.maximum_symbol_weight
    )
    if not long_allocation or not short_allocation:
        return {}
    weights = {symbol: weight for symbol, weight in long_allocation.items()}
    weights.update({symbol: -weight for symbol, weight in short_allocation.items()})
    return {symbol: float(weights[symbol]) for symbol in sorted(weights)}


class VolatilityDispersionReleaseStrategy:
    """Daily two-mode volatility-release portfolio."""

    def __init__(self, config: StrategyConfig = DEFAULT_CONFIG) -> None:
        self.config = config

    @staticmethod
    def _validate_seed(seed: int) -> None:
        if isinstance(seed, bool) or not isinstance(seed, numbers.Integral) or int(seed) < 0:
            raise ValueError("seed must be a nonnegative integer")

    @staticmethod
    def _apply_public_score_boundary(scores: dict[str, float]) -> dict[str, float]:
        """Capture one exact operative ranking dictionary through the public A5 hook."""

        if type(scores) is not dict or list(scores) != sorted(scores):
            raise ValueError("score boundary input must be a sorted built-in dictionary")
        if any(
            type(symbol) is not str or type(value) is not float or not math.isfinite(value)
            for symbol, value in scores.items()
        ):
            raise ValueError("score boundary input must contain finite built-in str/float pairs")
        input_scores = scores
        expected_items = tuple(scores.items())
        scores = score_boundary(scores)
        if scores is not input_scores:
            raise ValueError("score_boundary must return its exact input dictionary")
        if (
            type(scores) is not dict
            or tuple(scores.items()) != expected_items
            or any(
                type(symbol) is not str or type(value) is not float or not math.isfinite(value)
                for symbol, value in scores.items()
            )
        ):
            raise ValueError("score_boundary returned invalid or mutated scores")
        return scores

    def preconstruction_scores(
        self, context: Any, *, seed: int
    ) -> dict[str, float] | None:
        """Return final scheduled VDR ranks before selection, sizing, caps, or risk."""

        self._validate_seed(seed)
        decision_time, _, histories = _validate_context(context)
        if (
            decision_time.hour != self.config.rebalance_hour_utc
            or decision_time.minute
            or decision_time.second
            or decision_time.microsecond
        ):
            return None
        matrix = _return_matrix(
            histories,
            decision_time=decision_time,
            config=self.config,
        )
        scores = pd.Series(dtype=float) if matrix.empty else _raw_scores(matrix, self.config)
        final_scores = {
            str(symbol): float(value) for symbol, value in scores.sort_index().items()
        }
        return self._apply_public_score_boundary(final_scores)

    def target_weights(self, context: Any, *, seed: int) -> Mapping[str, float] | None:
        scores = self.preconstruction_scores(context, seed=seed)
        if scores is None:
            return None
        if not scores:
            return {}
        weights = _portfolio(pd.Series(scores, dtype=float), self.config)
        if any(not math.isfinite(weight) for weight in weights.values()):
            raise ValueError("constructed portfolio contains a non-finite weight")
        return weights


def build_strategy() -> VolatilityDispersionReleaseStrategy:
    """Canonical clean-worker factory for the exact materialized candidate."""

    candidate_id = candidate_variant.ACTIVE_CANDIDATE_ID
    overrides = candidate_variant.ACTIVE_OVERRIDES
    expected = MATERIALIZED_CANDIDATE_OVERRIDES.get(candidate_id)
    if candidate_id != ACTIVE_CANDIDATE_ID or expected is None:
        raise ValueError(f"unknown materialized candidate identifier: {candidate_id}")
    if type(overrides) is not dict or overrides != expected:
        raise ValueError(f"active overrides do not match the declaration for {candidate_id}")
    return VolatilityDispersionReleaseStrategy(dataclasses.replace(DEFAULT_CONFIG, **overrides))
