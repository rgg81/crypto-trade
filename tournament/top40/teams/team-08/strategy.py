"""Persistent Carry Dispersion Harvest target-weight adapter for team-08."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from crypto_trade.tournament.protocol import DecisionContext

_ANCHOR = pd.Timestamp(year=2020, month=2, day=3, tz="UTC")
_DECISION_STEP = pd.Timedelta(hours=72)
_BAR_INTERVAL = pd.Timedelta(hours=8)
_EWM_WINDOW = pd.Timedelta(days=84)
_COVERAGE_WINDOW = pd.Timedelta(days=28)
_MIN_COVERAGE_AGE = pd.Timedelta(days=21)
_MAX_LATEST_AGE = pd.Timedelta(hours=24)
_HALF_LIVES_DAYS = (7.0, 28.0)
_MIN_FUNDING_EVENTS = 42
_MIN_FUNDING_HOURS = 504.0
_MAX_FUNDING_INTERVAL_HOURS = 24.0
_MIN_CONTIGUOUS_RETURNS = 168
_BETA_RETURN_ENDPOINTS = 252
_MIN_BETA_PAIRS = 189
_SD_FLOOR = 1.0e-12
_BTC_VARIANCE_FLOOR = 1.0e-16
_DISPLACEMENT_LIMIT = 2.5
_VOL_ACCELERATION_LIMIT = 2.0
_SLEEVE_TARGET_COUNT = 10
_MAX_BUFFER = 4
_MAX_SLEEVE_COUNT = 15
_POSITION_CAP = 0.1875
_SLEEVE_GROSS = 0.40
_SLSQP_FTOL = 1.0e-12
_SLSQP_MAXITER = 500
_BOUND_TOLERANCE = 1.0e-10
_EQUALITY_TOLERANCE = 1.0e-9


@dataclass(frozen=True)
class _PriceFeatures:
    returns: np.ndarray
    sigma_28d: float


@dataclass(frozen=True)
class _Candidate:
    score: float
    beta: float
    sigma: float


@dataclass(frozen=True)
class _SleeveGeometry:
    symbols: tuple[str, ...]
    beta: np.ndarray
    base: np.ndarray
    minimum: np.ndarray
    maximum: np.ndarray
    low_beta: float
    high_beta: float


def _as_utc(value: object) -> pd.Timestamp | None:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if pd.isna(timestamp):
        return None
    try:
        if timestamp.tzinfo is None:
            return timestamp.tz_localize("UTC")
        return timestamp.tz_convert("UTC")
    except (TypeError, ValueError, OverflowError):
        return None


def _is_scheduled(timestamp: pd.Timestamp) -> bool:
    delta = timestamp - _ANCHOR
    return delta >= pd.Timedelta(0) and delta.value % _DECISION_STEP.value == 0


def _numeric(values: pd.Series) -> np.ndarray:
    return pd.to_numeric(values, errors="coerce").to_numpy(dtype=np.float64, copy=True)


def _price_features(
    frame: pd.DataFrame,
    decision_time: pd.Timestamp,
    *,
    require_btc: bool,
) -> _PriceFeatures | None:
    if not isinstance(frame, pd.DataFrame) or not {"open_time", "close"}.issubset(frame.columns):
        return None
    try:
        open_times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    except (TypeError, ValueError, OverflowError):
        return None
    if open_times.isna().any():
        return None
    close_endpoints = open_times + _BAR_INTERVAL
    visible = close_endpoints <= decision_time
    relevant_start = decision_time - _BETA_RETURN_ENDPOINTS * _BAR_INTERVAL
    relevant = visible & (close_endpoints >= relevant_start)
    relevant_times = pd.DatetimeIndex(open_times[relevant])
    if relevant_times.duplicated().any() or not relevant_times.is_monotonic_increasing:
        return None

    relevant_endpoints = pd.DatetimeIndex(close_endpoints[relevant])
    close_values = _numeric(frame.loc[relevant, "close"])
    closes = pd.Series(close_values, index=relevant_endpoints, dtype=np.float64)
    schedule = pd.date_range(
        decision_time - _BETA_RETURN_ENDPOINTS * _BAR_INTERVAL,
        decision_time,
        freq=_BAR_INTERVAL,
        tz="UTC",
    )
    scheduled_closes = closes.reindex(schedule).to_numpy(dtype=np.float64, copy=True)
    contiguous_closes = scheduled_closes[-(_MIN_CONTIGUOUS_RETURNS + 1) :]
    if (
        len(contiguous_closes) != _MIN_CONTIGUOUS_RETURNS + 1
        or not np.isfinite(contiguous_closes).all()
        or np.any(contiguous_closes <= 0.0)
    ):
        return None

    log_closes = np.full_like(scheduled_closes, np.nan, dtype=np.float64)
    finite_positive = np.isfinite(scheduled_closes) & (scheduled_closes > 0.0)
    log_closes[finite_positive] = np.log(scheduled_closes[finite_positive])
    returns = np.diff(log_closes)
    last_168 = returns[-168:]
    if not np.isfinite(last_168).all():
        return None

    sigma_168 = float(np.std(last_168, ddof=1))
    sigma_84 = float(np.std(returns[-84:], ddof=1))
    sigma_21 = float(np.std(returns[-21:], ddof=1))
    used_sigmas = np.asarray((sigma_168, sigma_84, sigma_21), dtype=np.float64)
    if not np.isfinite(used_sigmas).all() or np.any(used_sigmas <= _SD_FLOOR):
        return None

    displacement = abs(float(np.sum(returns[-42:]))) / (sigma_168 * math.sqrt(42.0))
    acceleration = sigma_21 / sigma_84
    if not math.isfinite(displacement) or not math.isfinite(acceleration):
        return None
    if not require_btc and (
        displacement >= _DISPLACEMENT_LIMIT or acceleration >= _VOL_ACCELERATION_LIMIT
    ):
        return None
    return _PriceFeatures(returns=returns, sigma_28d=sigma_84)


def _funding_score(
    funding: pd.DataFrame,
    symbol: str,
    decision_time: pd.Timestamp,
) -> float | None:
    required = {"symbol", "funding_time", "funding_rate"}
    if not isinstance(funding, pd.DataFrame) or not required.issubset(funding.columns):
        return None
    raw = funding.loc[funding["symbol"].astype(str) == symbol]
    if raw.empty:
        return None
    try:
        times = pd.to_datetime(raw["funding_time"], utc=True, errors="coerce")
    except (TypeError, ValueError, OverflowError):
        return None
    if times.isna().any():
        return None
    past_mask = times < decision_time
    if not past_mask.any():
        return None
    past_times = pd.DatetimeIndex(times[past_mask])
    if past_times.duplicated().any() or not past_times.is_monotonic_increasing:
        return None
    rates = _numeric(raw.loc[past_mask, "funding_rate"])
    if len(rates) != len(past_times):
        return None

    intervals = np.full(len(past_times), np.nan, dtype=np.float64)
    if len(past_times) > 1:
        intervals[1:] = (past_times[1:] - past_times[:-1]).total_seconds().to_numpy(
            dtype=np.float64
        ) / 3600.0
    window_mask = past_times >= decision_time - _EWM_WINDOW
    if not window_mask.any():
        return None
    window_times = past_times[window_mask]
    window_rates = rates[window_mask]
    window_intervals = intervals[window_mask]
    if (
        not np.isfinite(window_rates).all()
        or not np.isfinite(window_intervals).all()
        or np.any(window_intervals <= 0.0)
    ):
        return None

    coverage_mask = window_times >= decision_time - _COVERAGE_WINDOW
    coverage_times = window_times[coverage_mask]
    coverage_rates = window_rates[coverage_mask]
    coverage_intervals = window_intervals[coverage_mask]
    if len(coverage_times) < _MIN_FUNDING_EVENTS:
        return None
    if (
        not np.isfinite(coverage_rates).all()
        or not np.isfinite(coverage_intervals).all()
        or np.any(coverage_intervals <= 0.0)
        or np.any(coverage_intervals > _MAX_FUNDING_INTERVAL_HOURS)
        or float(np.sum(coverage_intervals)) < _MIN_FUNDING_HOURS
    ):
        return None
    oldest_age = decision_time - coverage_times[0]
    newest_age = decision_time - coverage_times[-1]
    if oldest_age < _MIN_COVERAGE_AGE or newest_age > _MAX_LATEST_AGE:
        return None

    ages_hours = (decision_time - window_times).total_seconds().to_numpy() / 3600.0
    carries: list[float] = []
    for half_life_days in _HALF_LIVES_DAYS:
        weights = np.exp2(-ages_hours / (24.0 * half_life_days))
        denominator = float(np.dot(weights, window_intervals))
        numerator = float(np.dot(weights, window_rates))
        carry = 24.0 * numerator / denominator if denominator > 0.0 else math.nan
        if not math.isfinite(carry):
            return None
        carries.append(carry)

    coverage_ages_hours = (decision_time - coverage_times).total_seconds().to_numpy() / 3600.0
    persistence_weights = np.exp2(-coverage_ages_hours / (24.0 * 28.0))
    persistence_durations = persistence_weights * coverage_intervals
    persistence_denominator = float(np.sum(persistence_durations))
    if not math.isfinite(persistence_denominator) or persistence_denominator <= 0.0:
        return None
    persistence = float(
        np.dot(persistence_durations, np.sign(coverage_rates)) / persistence_denominator
    )
    carry_7, carry_28 = carries
    if carry_7 * carry_28 <= 0.0:
        return 0.0
    shrink = max(0.0, (abs(persistence) - 0.25) / 0.75)
    score = math.copysign(min(abs(carry_7), abs(carry_28)), carry_28) * shrink
    return score if math.isfinite(score) else None


def _beta(symbol_returns: np.ndarray, btc_returns: np.ndarray) -> float | None:
    paired = np.isfinite(symbol_returns) & np.isfinite(btc_returns)
    if int(np.count_nonzero(paired)) < _MIN_BETA_PAIRS:
        return None
    symbol_values = symbol_returns[paired]
    btc_values = btc_returns[paired]
    btc_variance = float(np.var(btc_values, ddof=1))
    if not math.isfinite(btc_variance) or btc_variance <= _BTC_VARIANCE_FLOOR:
        return None
    covariance = float(np.cov(symbol_values, btc_values, ddof=1)[0, 1])
    if not math.isfinite(covariance):
        return None
    return float(np.clip(covariance / btc_variance, -0.5, 3.0))


def _extreme_allocation(beta: np.ndarray, symbols: tuple[str, ...], *, reverse: bool) -> np.ndarray:
    order = sorted(
        range(len(symbols)),
        key=lambda index: ((-beta[index]) if reverse else beta[index], symbols[index]),
    )
    allocation = np.zeros(len(symbols), dtype=np.float64)
    remaining = 1.0
    for index in order:
        amount = min(_POSITION_CAP, remaining)
        allocation[index] = amount
        remaining -= amount
        if remaining <= 0.0:
            break
    return allocation


def _geometry(symbols: set[str], candidates: Mapping[str, _Candidate]) -> _SleeveGeometry | None:
    lexical = tuple(sorted(symbols))
    if not lexical:
        return None
    beta = np.asarray([candidates[symbol].beta for symbol in lexical], dtype=np.float64)
    sigma = np.asarray([candidates[symbol].sigma for symbol in lexical], dtype=np.float64)
    inverse_sigma = 1.0 / sigma
    normalizer = float(np.sum(inverse_sigma))
    if (
        not np.isfinite(beta).all()
        or not np.isfinite(inverse_sigma).all()
        or not math.isfinite(normalizer)
        or normalizer <= 0.0
    ):
        return None
    base = inverse_sigma / normalizer
    minimum = _extreme_allocation(beta, lexical, reverse=False)
    maximum = _extreme_allocation(beta, lexical, reverse=True)
    if abs(float(np.sum(minimum)) - 1.0) > _EQUALITY_TOLERANCE:
        return None
    if abs(float(np.sum(maximum)) - 1.0) > _EQUALITY_TOLERANCE:
        return None
    low_beta = float(np.dot(minimum, beta))
    high_beta = float(np.dot(maximum, beta))
    if not all(math.isfinite(value) for value in (low_beta, high_beta)):
        return None
    return _SleeveGeometry(
        symbols=lexical,
        beta=beta,
        base=base,
        minimum=minimum,
        maximum=maximum,
        low_beta=low_beta,
        high_beta=high_beta,
    )


def _project(geometry: _SleeveGeometry, beta_target: float) -> np.ndarray | None:
    width = geometry.high_beta - geometry.low_beta
    if width == 0.0:
        initial = geometry.minimum.copy()
    else:
        interpolation = (beta_target - geometry.low_beta) / width
        initial = (1.0 - interpolation) * geometry.minimum + interpolation * geometry.maximum
    ones = np.ones(len(geometry.symbols), dtype=np.float64)
    result = minimize(
        lambda values: 0.5 * float(np.dot(values - geometry.base, values - geometry.base)),
        initial,
        jac=lambda values: values - geometry.base,
        method="SLSQP",
        bounds=[(0.0, _POSITION_CAP)] * len(geometry.symbols),
        constraints=(
            {
                "type": "eq",
                "fun": lambda values: float(np.sum(values) - 1.0),
                "jac": lambda _values: ones,
            },
            {
                "type": "eq",
                "fun": lambda values: float(np.dot(values, geometry.beta) - beta_target),
                "jac": lambda _values: geometry.beta,
            },
        ),
        options={"ftol": _SLSQP_FTOL, "maxiter": _SLSQP_MAXITER, "disp": False},
    )
    values = np.asarray(result.x, dtype=np.float64)
    if not result.success or values.shape != geometry.base.shape or not np.isfinite(values).all():
        return None
    lower_violation = max(0.0, -float(np.min(values)))
    upper_violation = max(0.0, float(np.max(values)) - _POSITION_CAP)
    if max(lower_violation, upper_violation) > _BOUND_TOLERANCE:
        return None
    if abs(float(np.sum(values)) - 1.0) > _EQUALITY_TOLERANCE:
        return None
    if abs(float(np.dot(values, geometry.beta)) - beta_target) > _EQUALITY_TOLERANCE:
        return None
    return values


def _solve_sleeves(
    longs: set[str],
    shorts: set[str],
    candidates: Mapping[str, _Candidate],
) -> dict[str, float] | None:
    long_geometry = _geometry(longs, candidates)
    short_geometry = _geometry(shorts, candidates)
    if long_geometry is None or short_geometry is None:
        return None
    intersection_low = max(long_geometry.low_beta, short_geometry.low_beta)
    intersection_high = min(long_geometry.high_beta, short_geometry.high_beta)
    if intersection_low > intersection_high:
        return None
    long_base_beta = float(np.dot(long_geometry.base, long_geometry.beta))
    short_base_beta = float(np.dot(short_geometry.base, short_geometry.beta))
    beta_target = float(
        np.clip((long_base_beta + short_base_beta) / 2.0, intersection_low, intersection_high)
    )
    long_weights = _project(long_geometry, beta_target)
    short_weights = _project(short_geometry, beta_target)
    if long_weights is None or short_weights is None:
        return None
    output = {
        symbol: float(_SLEEVE_GROSS * weight)
        for symbol, weight in zip(long_geometry.symbols, long_weights, strict=True)
    }
    output.update(
        {
            symbol: float(-_SLEEVE_GROSS * weight)
            for symbol, weight in zip(short_geometry.symbols, short_weights, strict=True)
        }
    )
    values = np.asarray(list(output.values()), dtype=np.float64)
    if not np.isfinite(values).all():
        return None
    if abs(float(np.sum(values))) > _SLEEVE_GROSS * _EQUALITY_TOLERANCE * 2.0:
        return None
    if float(np.max(np.abs(values))) > _SLEEVE_GROSS * _POSITION_CAP + _BOUND_TOLERANCE:
        return None
    return dict(sorted(output.items()))


class PersistentCarryDispersionHarvest:
    """Stateful buffered selector emitting only finite signed target weights."""

    def __init__(self) -> None:
        self._longs: tuple[str, ...] = ()
        self._shorts: tuple[str, ...] = ()

    def _flatten(self) -> dict[str, float]:
        self._longs = ()
        self._shorts = ()
        return {}

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        del seed
        decision_time = _as_utc(context.decision_time)
        if decision_time is None:
            return self._flatten()
        if not _is_scheduled(decision_time):
            return None

        eligible = tuple(str(symbol) for symbol in context.eligible_symbols)
        if len(eligible) != len(set(eligible)) or "BTCUSDT" not in context.bars:
            return self._flatten()
        btc_features = _price_features(context.bars["BTCUSDT"], decision_time, require_btc=True)
        if btc_features is None:
            return self._flatten()
        finite_btc = btc_features.returns[np.isfinite(btc_features.returns)]
        if (
            len(finite_btc) < _MIN_BETA_PAIRS
            or float(np.var(finite_btc, ddof=1)) <= _BTC_VARIANCE_FLOOR
        ):
            return self._flatten()

        candidates: dict[str, _Candidate] = {}
        for symbol in sorted(set(eligible)):
            frame = context.bars.get(symbol)
            if frame is None:
                continue
            # BTC's clean returns are the shared beta benchmark, but BTC remains an ordinary
            # candidate for the per-symbol displacement/acceleration vetoes.
            price = _price_features(frame, decision_time, require_btc=False)
            if price is None:
                continue
            beta = _beta(price.returns, btc_features.returns)
            if beta is None:
                continue
            score = _funding_score(context.funding, symbol, decision_time)
            if score is None:
                continue
            candidates[symbol] = _Candidate(score=score, beta=beta, sigma=price.sigma_28d)

        ranked = sorted(candidates, key=lambda symbol: (candidates[symbol].score, symbol))
        count = len(ranked)
        if count < 2 * _SLEEVE_TARGET_COUNT:
            return self._flatten()
        rank = {symbol: index for index, symbol in enumerate(ranked, start=1)}
        buffer = min(_MAX_BUFFER, max(0, count // 2 - _SLEEVE_TARGET_COUNT))
        retained_longs = sorted(
            (
                symbol
                for symbol in self._longs
                if symbol in rank and rank[symbol] <= _SLEEVE_TARGET_COUNT + buffer
            ),
            key=lambda symbol: (rank[symbol], symbol),
        )[:_SLEEVE_TARGET_COUNT]
        retained_shorts = sorted(
            (
                symbol
                for symbol in self._shorts
                if symbol in rank and rank[symbol] >= count - _SLEEVE_TARGET_COUNT - buffer + 1
            ),
            key=lambda symbol: (-rank[symbol], symbol),
        )[:_SLEEVE_TARGET_COUNT]
        longs = set(retained_longs)
        shorts = set(retained_shorts)
        for symbol in ranked:
            if len(longs) >= _SLEEVE_TARGET_COUNT:
                break
            if symbol not in shorts:
                longs.add(symbol)
        for symbol in reversed(ranked):
            if len(shorts) >= _SLEEVE_TARGET_COUNT:
                break
            if symbol not in longs:
                shorts.add(symbol)
        if len(longs) != _SLEEVE_TARGET_COUNT or len(shorts) != _SLEEVE_TARGET_COUNT:
            return self._flatten()

        maximum_count = min(_MAX_SLEEVE_COUNT, count // 2)
        for sleeve_count in range(_SLEEVE_TARGET_COUNT, maximum_count + 1):
            solved = _solve_sleeves(longs, shorts, candidates)
            if solved is not None:
                self._longs = tuple(sorted(longs))
                self._shorts = tuple(sorted(shorts))
                return solved
            if sleeve_count == maximum_count:
                break
            used = longs | shorts
            next_long = next((symbol for symbol in ranked if symbol not in used), None)
            if next_long is None:
                break
            longs.add(next_long)
            used = longs | shorts
            next_short = next((symbol for symbol in reversed(ranked) if symbol not in used), None)
            if next_short is None:
                longs.remove(next_long)
                break
            shorts.add(next_short)
        return self._flatten()


def build_strategy() -> PersistentCarryDispersionHarvest:
    """Return a fresh, empty-state strategy instance for the canonical worker."""

    return PersistentCarryDispersionHarvest()
