"""Funding-Price Elasticity Gap target generator for Top-40 team 09.

The central tournament evaluator owns fills, costs, funding cashflows, risk enforcement, and PnL.
This module consumes only the past-only ``DecisionContext`` and emits signed target weights.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

HORIZON = pd.Timedelta(hours=72)
BAR_INTERVAL = pd.Timedelta(hours=8)
NORMALISATION_DAYS = 60
MINIMUM_VALID_HISTORY = 48
MINIMUM_CROSS_SECTION = 20
MINIMUM_SLOPES = 20
MINIMUM_DISTINCT_PRICE_Z = 5
MINIMUM_DISPERSION_HISTORY = 60
PRICE_SCALE_FLOOR = 0.10
FUNDING_SCALE_FLOOR = 1e-7
PRICE_DENOMINATOR_FLOOR = 1e-6
VOLATILITY_FLOOR = 1e-6
ROBUST_SCALE = 1.4826
ZSCORE_LIMIT = 4.0
SLOPE_DENOMINATOR_FLOOR = 1e-12
SYMBOL_WEIGHT_CAP = 0.08
EXPECTED_SEED = 20260713


@dataclasses.dataclass(frozen=True, slots=True)
class FPEGConfig:
    """The four preregistered research dimensions plus one pending semantic binding."""

    q: float
    gross_max: float
    volatility_days: int
    dispersion_lookback: int
    dispersion_history_includes_current: bool
    seed: int = EXPECTED_SEED

    def validate(self) -> None:
        if self.q not in {0.25, 0.30}:
            raise ValueError("q must be one of the preregistered values")
        if self.gross_max not in {0.60, 0.80}:
            raise ValueError("gross_max must be one of the preregistered values")
        if self.volatility_days not in {15, 30, 45}:
            raise ValueError("volatility_days must be one of the preregistered values")
        if self.dispersion_lookback not in {90, 180, 270}:
            raise ValueError("dispersion_lookback must be one of the preregistered values")
        if not isinstance(self.dispersion_history_includes_current, bool):
            raise TypeError("dispersion_history_includes_current must be Boolean")
        if self.seed != EXPECTED_SEED:
            raise ValueError("strategy seed differs from the preregistered seed")


@dataclasses.dataclass(frozen=True, slots=True)
class _SymbolObservation:
    symbol: str
    z_price: float
    z_funding: float
    sigma: float


@dataclasses.dataclass(frozen=True, slots=True)
class _ResidualObservation:
    symbol: str
    residual: float
    sigma: float


def _utc_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _closed_price_series(
    frame: pd.DataFrame,
    *,
    decision_time: pd.Timestamp,
    earliest_needed: pd.Timestamp,
) -> pd.Series | None:
    """Return close prices indexed by bar end, ignoring anything not closed by the decision."""

    if not {"open_time", "close"}.issubset(frame.columns):
        return None
    try:
        open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    except (TypeError, ValueError):
        return None
    end_times = open_times + BAR_INTERVAL
    relevant = (end_times <= decision_time) & (end_times >= earliest_needed)
    selected = frame.loc[relevant, ["close"]].copy()
    selected.index = pd.DatetimeIndex(end_times[relevant])
    if selected.index.hasnans or selected.index.duplicated().any():
        return None
    try:
        close = pd.to_numeric(selected["close"], errors="raise").astype(float)
    except (TypeError, ValueError):
        return None
    values = close.to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values <= 0.0).any():
        return None
    return close.sort_index()


def _exact_price_feature(close: pd.Series, decision_time: pd.Timestamp) -> float | None:
    grid = pd.date_range(decision_time - HORIZON, decision_time, freq=BAR_INTERVAL)
    values = close.reindex(grid).to_numpy(dtype=float)
    if len(values) != 10 or not np.isfinite(values).all() or (values <= 0.0).any():
        return None
    adjacent = np.diff(np.log(values))
    denominator = max(float(np.sqrt(np.dot(adjacent, adjacent))), PRICE_DENOMINATOR_FLOOR)
    value = float(math.log(values[-1] / values[0]) / denominator)
    return value if math.isfinite(value) else None


def _volatility(
    close: pd.Series,
    decision_time: pd.Timestamp,
    *,
    lookback_days: int,
) -> float | None:
    expected_returns = lookback_days * 3
    grid = pd.date_range(
        decision_time - pd.Timedelta(days=lookback_days),
        decision_time,
        freq=BAR_INTERVAL,
    )
    values = close.reindex(grid).to_numpy(dtype=float)
    valid = np.isfinite(values) & (values > 0.0)
    adjacent_valid = valid[:-1] & valid[1:]
    if int(adjacent_valid.sum()) < math.ceil(0.80 * expected_returns):
        return None
    log_values = np.full(len(values), np.nan, dtype=float)
    log_values[valid] = np.log(values[valid])
    returns = np.diff(log_values)[adjacent_valid]
    if len(returns) < 2:
        return None
    sigma = max(float(np.std(returns, ddof=1)), VOLATILITY_FLOOR)
    return sigma if math.isfinite(sigma) else None


def _funding_series(
    funding: pd.DataFrame,
    *,
    symbol: str,
    decision_time: pd.Timestamp,
) -> pd.Series | None:
    required = {"funding_time", "symbol", "funding_rate"}
    if not required.issubset(funding.columns):
        return None
    rows = funding.loc[funding["symbol"].astype(str).eq(symbol), ["funding_time", "funding_rate"]]
    try:
        times = pd.to_datetime(rows["funding_time"], utc=True, errors="coerce")
    except (TypeError, ValueError):
        return None
    # Future rows are outside the feature's information set and cannot affect validation.
    past = times < decision_time
    rows = rows.loc[past, ["funding_rate"]].copy()
    rows.index = pd.DatetimeIndex(times[past])
    if rows.index.hasnans or rows.index.duplicated().any():
        return None
    try:
        rates = pd.to_numeric(rows["funding_rate"], errors="raise").astype(float)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(rates.to_numpy(dtype=float)).all():
        return None
    return rates.sort_index()


def _funding_feature(rates: pd.Series, decision_time: pd.Timestamp) -> float | None:
    if rates.empty:
        return None
    strictly_past = rates.loc[rates.index < decision_time]
    if strictly_past.empty:
        return None
    window = strictly_past.loc[
        (strictly_past.index >= decision_time - HORIZON)
        & (strictly_past.index < decision_time)
    ]
    if window.empty:
        # The empty window is zero only after an actual funding event had already been observed.
        if strictly_past.index.min() >= decision_time:
            return None
        return 0.0
    value = float(window.sum())
    return value if math.isfinite(value) else None


def _robust_z(current: float, history: Sequence[float], *, floor: float) -> float | None:
    values = np.asarray(history, dtype=float)
    if len(values) < MINIMUM_VALID_HISTORY or not np.isfinite(values).all():
        return None
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    scale = max(ROBUST_SCALE * mad, floor)
    value = float(np.clip((current - median) / scale, -ZSCORE_LIMIT, ZSCORE_LIMIT))
    return value if math.isfinite(value) else None


def _theil_sen(
    observations: Sequence[_SymbolObservation],
) -> tuple[float, float, list[_ResidualObservation]] | None:
    ordered = sorted(observations, key=lambda item: item.symbol)
    distinct = len({item.z_price for item in ordered})
    if distinct < MINIMUM_DISTINCT_PRICE_Z:
        return None
    slopes: list[float] = []
    for index, left in enumerate(ordered):
        for right in ordered[index + 1 :]:
            delta_price = right.z_price - left.z_price
            if abs(delta_price) <= SLOPE_DENOMINATOR_FLOOR:
                continue
            slope = (right.z_funding - left.z_funding) / delta_price
            if math.isfinite(slope):
                slopes.append(float(slope))
    if len(slopes) < MINIMUM_SLOPES:
        return None
    slope = float(np.median(np.asarray(slopes, dtype=float)))
    intercept = float(
        np.median(
            np.asarray(
                [item.z_funding - slope * item.z_price for item in ordered],
                dtype=float,
            )
        )
    )
    residuals = [
        _ResidualObservation(
            symbol=item.symbol,
            residual=float(item.z_funding - intercept - slope * item.z_price),
            sigma=item.sigma,
        )
        for item in ordered
    ]
    if not math.isfinite(slope) or not math.isfinite(intercept):
        return None
    if any(not math.isfinite(item.residual) for item in residuals):
        return None
    return slope, intercept, residuals


def _nearest_rank(values: Sequence[float], probability: float) -> float:
    ordered = sorted(float(value) for value in values)
    if not ordered:
        raise ValueError("nearest-rank percentile requires at least one value")
    index = math.ceil(probability * len(ordered)) - 1
    return ordered[index]


def _allocate_sleeve(
    selected: Sequence[_ResidualObservation],
    *,
    sleeve_gross: float,
) -> dict[str, float] | None:
    """Inverse-volatility allocation with deterministic iterative cap redistribution."""

    if not selected or sleeve_gross < 0.0:
        return None
    ordered = sorted(selected, key=lambda item: item.symbol)
    if sleeve_gross > SYMBOL_WEIGHT_CAP * len(ordered) + 1e-12:
        return None
    inverse_volatility = {
        item.symbol: 1.0 / item.sigma
        for item in ordered
        if math.isfinite(item.sigma) and item.sigma > 0.0
    }
    if len(inverse_volatility) != len(ordered):
        return None
    remaining = set(inverse_volatility)
    weights: dict[str, float] = {}
    gross_left = float(sleeve_gross)
    while remaining:
        base_sum = math.fsum(inverse_volatility[symbol] for symbol in sorted(remaining))
        if not math.isfinite(base_sum) or base_sum <= 0.0:
            return None
        tentative = {
            symbol: gross_left * inverse_volatility[symbol] / base_sum
            for symbol in sorted(remaining)
        }
        capped = [
            symbol
            for symbol in sorted(remaining)
            if tentative[symbol] > SYMBOL_WEIGHT_CAP + 1e-15
        ]
        if not capped:
            weights.update(tentative)
            gross_left = 0.0
            break
        for symbol in capped:
            weights[symbol] = SYMBOL_WEIGHT_CAP
            remaining.remove(symbol)
            gross_left -= SYMBOL_WEIGHT_CAP
        if gross_left < -1e-12:
            return None
        if gross_left <= 1e-15:
            weights.update({symbol: 0.0 for symbol in remaining})
            gross_left = 0.0
            break
    if abs(math.fsum(weights.values()) - sleeve_gross) > 1e-10:
        return None
    if any(value < -1e-15 or value > SYMBOL_WEIGHT_CAP + 1e-12 for value in weights.values()):
        return None
    return weights


class FPEGStrategy:
    """Stateful, deterministic daily FPEG target strategy."""

    def __init__(self, config: FPEGConfig):
        config.validate()
        self.config = config
        self._pair_cache: dict[tuple[str, pd.Timestamp], tuple[float, float]] = {}
        self._dispersion_history: list[tuple[pd.Timestamp, float]] = []
        self._last_daily_decision: pd.Timestamp | None = None

    def _pair(
        self,
        symbol: str,
        decision_time: pd.Timestamp,
        close: pd.Series,
        rates: pd.Series,
    ) -> tuple[float, float] | None:
        key = (symbol, decision_time)
        cached = self._pair_cache.get(key)
        if cached is not None:
            return cached
        price = _exact_price_feature(close, decision_time)
        funding = _funding_feature(rates, decision_time)
        if price is None or funding is None:
            return None
        pair = (price, funding)
        self._pair_cache[key] = pair
        return pair

    def _observation(
        self,
        symbol: str,
        decision_time: pd.Timestamp,
        close: pd.Series,
        rates: pd.Series,
    ) -> _SymbolObservation | None:
        current = self._pair(symbol, decision_time, close, rates)
        if current is None:
            return None
        prior_pairs: list[tuple[float, float]] = []
        for days_ago in range(NORMALISATION_DAYS, 0, -1):
            prior_time = decision_time - pd.Timedelta(days=days_ago)
            pair = self._pair(symbol, prior_time, close, rates)
            if pair is not None:
                prior_pairs.append(pair)
        if len(prior_pairs) < MINIMUM_VALID_HISTORY:
            return None
        z_price = _robust_z(
            current[0],
            [pair[0] for pair in prior_pairs],
            floor=PRICE_SCALE_FLOOR,
        )
        z_funding = _robust_z(
            current[1],
            [pair[1] for pair in prior_pairs],
            floor=FUNDING_SCALE_FLOOR,
        )
        sigma = _volatility(
            close,
            decision_time,
            lookback_days=self.config.volatility_days,
        )
        if z_price is None or z_funding is None or sigma is None:
            return None
        return _SymbolObservation(symbol, z_price, z_funding, sigma)

    def _gross_for_dispersion(self, dispersion: float) -> float:
        prior_values = [value for _, value in self._dispersion_history]
        ranking_values = list(prior_values)
        if self.config.dispersion_history_includes_current:
            ranking_values.append(dispersion)
        if len(ranking_values) < MINIMUM_DISPERSION_HISTORY:
            return 0.5 * self.config.gross_max
        recent = ranking_values[-self.config.dispersion_lookback :]
        lower = _nearest_rank(recent, 0.33)
        upper = _nearest_rank(recent, 0.67)
        if dispersion < lower:
            return 0.5 * self.config.gross_max
        if dispersion < upper:
            return 0.75 * self.config.gross_max
        return self.config.gross_max

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        if seed != self.config.seed:
            raise ValueError("runtime seed differs from frozen FPEG seed")
        decision_time = _utc_timestamp(context.decision_time)
        if decision_time.minute or decision_time.second or decision_time.microsecond:
            return None
        if decision_time.hour in {8, 16}:
            return None
        if decision_time.hour != 0:
            return None
        if self._last_daily_decision is not None and decision_time <= self._last_daily_decision:
            raise ValueError("daily decision times must be strictly increasing")
        self._last_daily_decision = decision_time

        eligible = tuple(sorted({str(symbol) for symbol in context.eligible_symbols}))
        if len(eligible) < MINIMUM_CROSS_SECTION:
            return {}
        earliest_needed = decision_time - pd.Timedelta(days=max(63, self.config.volatility_days))
        observations: list[_SymbolObservation] = []
        for symbol in eligible:
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            close = _closed_price_series(
                frame,
                decision_time=decision_time,
                earliest_needed=earliest_needed,
            )
            if close is None:
                continue
            rates = _funding_series(
                context.funding,
                symbol=symbol,
                decision_time=decision_time,
            )
            if rates is None:
                continue
            observation = self._observation(symbol, decision_time, close, rates)
            if observation is not None:
                observations.append(observation)
        if len(observations) < MINIMUM_CROSS_SECTION:
            return {}

        fit = _theil_sen(observations)
        if fit is None:
            return {}
        _, _, residuals = fit
        residual_values = np.asarray([item.residual for item in residuals], dtype=float)
        residual_median = float(np.median(residual_values))
        dispersion = float(
            ROBUST_SCALE * np.median(np.abs(residual_values - residual_median))
        )
        if not math.isfinite(dispersion):
            return {}
        gross = self._gross_for_dispersion(dispersion)

        count = len(residuals)
        k = max(5, math.floor(self.config.q * count))
        if 2 * k > count:
            return {}
        ordered = sorted(residuals, key=lambda item: (item.residual, item.symbol))
        long_selected = ordered[:k]
        short_selected = ordered[-k:]
        long_weights = _allocate_sleeve(long_selected, sleeve_gross=gross / 2.0)
        short_weights = _allocate_sleeve(short_selected, sleeve_gross=gross / 2.0)

        # A valid D observation is stored online even if a later allocation feasibility gate fails.
        self._dispersion_history.append((decision_time, dispersion))
        if long_weights is None or short_weights is None:
            return {}
        targets = {symbol: 0.0 for symbol in eligible}
        for symbol, weight in long_weights.items():
            targets[symbol] = float(weight)
        for symbol, weight in short_weights.items():
            targets[symbol] = float(-weight)
        values = np.asarray(list(targets.values()), dtype=float)
        if not np.isfinite(values).all():
            return {}
        if float(np.abs(values).sum()) > 0.80 + 1e-10:
            return {}
        if abs(float(values.sum())) > 1e-10:
            return {}
        if float(np.abs(values).max(initial=0.0)) > SYMBOL_WEIGHT_CAP + 1e-10:
            return {}
        return targets


def _load_selected_config(path: Path) -> FPEGConfig:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise TypeError("frozen_config.json must contain a JSON object")
    selected = payload.get("selected_parameters")
    if not isinstance(selected, dict):
        raise ValueError("frozen_config.json has no QR-selected parameter cell")
    config = FPEGConfig(
        q=float(selected["q"]),
        gross_max=float(selected["gross_max"]),
        volatility_days=int(selected["volatility_days"]),
        dispersion_lookback=int(selected["dispersion_lookback"]),
        dispersion_history_includes_current=selected["dispersion_history_includes_current"],
        seed=int(payload["seeds"]["strategy"]),
    )
    config.validate()
    return config


def build_strategy() -> FPEGStrategy:
    """Build one fresh strategy from the QR-selected, text-auditable config."""

    config_path = Path(__file__).with_name("frozen_config.json")
    return FPEGStrategy(_load_selected_config(config_path))
