"""Causal implementation of team-01's residual-drift/funding family.

The strategy is intentionally stateless.  Every transform is rebuilt from the past-only
``DecisionContext`` supplied at a boundary.  Execution, positions, costs, funding cashflows,
membership exits, and risk controls remain organizer-owned.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

_BAR_INTERVAL = pd.Timedelta(hours=8)
_BTC_SYMBOL = "BTCUSDT"
_CANONICAL_RUNTIME_SEED = 20260801
_EPSILON = 1.0e-12


def _is_grid_value(value: float, lower: float, upper: float, step: float) -> bool:
    if not math.isfinite(float(value)) or value < lower - _EPSILON or value > upper + _EPSILON:
        return False
    units = (value - lower) / step
    return abs(units - round(units)) <= 1.0e-9


@dataclasses.dataclass(frozen=True)
class StrategyParameters:
    """One preregistered material cell from the team-01 family."""

    residual_lookback_days: int
    skip_days: int
    path_efficiency_exponent: float
    rank_tail_fraction: float
    direction_tilt_delta: float
    beta_lookback_days: int = 30
    minimum_paired_returns: int = 72
    funding_lookback_days: int = 7
    minimum_funding_events: int = 14
    funding_penalty: float = 0.35
    direction_lookback_days: int = 60
    direction_return_scale: float = 0.20
    total_gross: float = 0.80
    per_symbol_cap: float = 0.09
    minimum_valid_symbols: int = 24
    minimum_names_per_side: int = 6

    def __post_init__(self) -> None:
        if self.residual_lookback_days not in {7, 14, 21, 28, 35}:
            raise ValueError("residual lookback is outside the registered domain")
        if self.skip_days not in {1, 3}:
            raise ValueError("skip is outside the registered domain")
        if self.path_efficiency_exponent not in {0.5, 1.0}:
            raise ValueError("path exponent is outside the registered domain")
        if not _is_grid_value(self.rank_tail_fraction, 0.15, 0.35, 0.05):
            raise ValueError("tail fraction is outside the registered domain")
        if self.direction_tilt_delta not in {0.05, 0.075, 0.10}:
            raise ValueError("direction tilt is outside the registered domain")
        fixed_values = {
            "beta_lookback_days": (self.beta_lookback_days, 30),
            "minimum_paired_returns": (self.minimum_paired_returns, 72),
            "funding_lookback_days": (self.funding_lookback_days, 7),
            "minimum_funding_events": (self.minimum_funding_events, 14),
            "funding_penalty": (self.funding_penalty, 0.35),
            "direction_lookback_days": (self.direction_lookback_days, 60),
            "direction_return_scale": (self.direction_return_scale, 0.20),
            "total_gross": (self.total_gross, 0.80),
            "per_symbol_cap": (self.per_symbol_cap, 0.09),
            "minimum_valid_symbols": (self.minimum_valid_symbols, 24),
            "minimum_names_per_side": (self.minimum_names_per_side, 6),
        }
        for name, (actual, expected) in fixed_values.items():
            if actual != expected:
                raise ValueError(f"{name} differs from the preregistered fixed value")


REFERENCE_PARAMETERS = StrategyParameters(
    residual_lookback_days=21,
    skip_days=3,
    path_efficiency_exponent=1.0,
    rank_tail_fraction=0.25,
    direction_tilt_delta=0.075,
)


@dataclasses.dataclass(frozen=True)
class _SymbolSignal:
    symbol: str
    drift: float
    funding: float
    residual_volatility: float


class ResidualDriftFundingStrategy:
    """BTC-residual, path-efficient, medium-horizon continuation strategy."""

    def __init__(self, parameters: StrategyParameters) -> None:
        self._parameters = parameters

    def target_weights(
        self, context: Any, *, seed: int
    ) -> Mapping[str, float] | None:
        if int(seed) != _CANONICAL_RUNTIME_SEED:
            raise ValueError("team-01 requires canonical runtime seed 20260801")

        decision_time = _utc_timestamp(getattr(context, "decision_time", None))
        if decision_time is None:
            return {}
        if (
            decision_time.hour != 0
            or decision_time.minute != 0
            or decision_time.second != 0
            or decision_time.microsecond != 0
            or decision_time.nanosecond != 0
        ):
            return None

        eligible = _eligible_symbols(getattr(context, "eligible_symbols", ()))
        if eligible is None or _BTC_SYMBOL not in eligible:
            return {}
        bars = getattr(context, "bars", None)
        funding = getattr(context, "funding", None)
        if not isinstance(bars, Mapping) or not isinstance(funding, pd.DataFrame):
            return {}

        btc_history = _closed_history(bars.get(_BTC_SYMBOL), decision_time)
        if btc_history is None:
            return {}
        btc_closes, btc_returns = btc_history

        parameters = self._parameters
        funding_pressures = _funding_pressures(
            funding,
            eligible=eligible,
            decision_time=decision_time,
            lookback_days=parameters.funding_lookback_days,
            minimum_events=parameters.minimum_funding_events,
        )
        if funding_pressures is None:
            return {}

        signals: list[_SymbolSignal] = []
        for symbol in eligible:
            if symbol == _BTC_SYMBOL:
                continue
            funding_pressure = funding_pressures.get(symbol)
            if funding_pressure is None:
                continue
            history = _closed_history(bars.get(symbol), decision_time)
            if history is None:
                continue
            _, symbol_returns = history
            signal = self._symbol_signal(
                symbol,
                symbol_returns=symbol_returns,
                btc_returns=btc_returns,
                funding_pressure=funding_pressure,
                decision_time=decision_time,
            )
            if signal is not None:
                signals.append(signal)

        if len(signals) < parameters.minimum_valid_symbols:
            return {}

        drift_z = _robust_z([signal.drift for signal in signals])
        funding_z = _robust_z([signal.funding for signal in signals])
        if drift_z is None or funding_z is None:
            return {}

        combined_scores = _combine_scores(
            drift_z,
            funding_z,
            penalty=parameters.funding_penalty,
        )
        if combined_scores is None:
            return {}
        scored: list[tuple[str, float, float]] = []
        for signal, score in zip(signals, combined_scores, strict=True):
            scored.append((signal.symbol, float(score), signal.residual_volatility))

        selected_tails = _select_signed_tails(
            scored,
            tail_fraction=parameters.rank_tail_fraction,
            minimum_names_per_side=parameters.minimum_names_per_side,
        )
        if selected_tails is None:
            return {}
        short_tail, long_tail = selected_tails

        direction = _btc_direction(
            btc_closes,
            decision_time=decision_time,
            lookback_days=parameters.direction_lookback_days,
            scale=parameters.direction_return_scale,
        )
        long_gross = parameters.total_gross / 2.0 + parameters.direction_tilt_delta * direction
        short_gross = parameters.total_gross / 2.0 - parameters.direction_tilt_delta * direction

        long_weights = _inverse_volatility_sleeve(
            long_tail,
            gross=long_gross,
            cap=parameters.per_symbol_cap,
        )
        short_weights = _inverse_volatility_sleeve(
            short_tail,
            gross=short_gross,
            cap=parameters.per_symbol_cap,
        )
        if long_weights is None or short_weights is None:
            return {}

        targets = dict(long_weights)
        targets.update({symbol: -weight for symbol, weight in short_weights.items()})
        if not _valid_targets(
            targets,
            eligible=eligible,
            expected_gross=parameters.total_gross,
            maximum_abs_net=2.0 * parameters.direction_tilt_delta,
            symbol_cap=parameters.per_symbol_cap,
        ):
            return {}
        return targets

    def _symbol_signal(
        self,
        symbol: str,
        *,
        symbol_returns: pd.Series,
        btc_returns: pd.Series,
        funding_pressure: float,
        decision_time: pd.Timestamp,
    ) -> _SymbolSignal | None:
        parameters = self._parameters
        beta_times = pd.date_range(
            end=decision_time,
            periods=3 * parameters.beta_lookback_days,
            freq=_BAR_INTERVAL,
        )
        symbol_beta = symbol_returns.reindex(beta_times).to_numpy(dtype=float)
        btc_beta = btc_returns.reindex(beta_times).to_numpy(dtype=float)
        paired = np.isfinite(symbol_beta) & np.isfinite(btc_beta)
        if int(paired.sum()) < parameters.minimum_paired_returns:
            return None
        x = btc_beta[paired]
        y = symbol_beta[paired]
        centered_x = x - float(np.mean(x))
        centered_y = y - float(np.mean(y))
        btc_variance = float(np.mean(centered_x * centered_x))
        if not math.isfinite(btc_variance) or btc_variance <= _EPSILON:
            return None
        covariance = float(np.mean(centered_x * centered_y))
        beta = covariance / btc_variance
        beta = float(np.clip(beta, -1.0, 3.0))

        drift_end = decision_time - pd.Timedelta(days=parameters.skip_days)
        drift_times = pd.date_range(
            end=drift_end,
            periods=3 * parameters.residual_lookback_days,
            freq=_BAR_INTERVAL,
        )
        symbol_drift = symbol_returns.reindex(drift_times).to_numpy(dtype=float)
        btc_drift = btc_returns.reindex(drift_times).to_numpy(dtype=float)
        if not np.isfinite(symbol_drift).all() or not np.isfinite(btc_drift).all():
            return None
        residuals = symbol_drift - beta * btc_drift
        if not np.isfinite(residuals).all() or residuals.size < 2:
            return None
        residual_sum = float(np.sum(residuals))
        residual_volatility = float(np.std(residuals, ddof=1))
        if not math.isfinite(residual_volatility) or residual_volatility <= _EPSILON:
            return None
        path_length = float(np.sum(np.abs(residuals)))
        if not math.isfinite(path_length) or path_length <= 1.0e-8:
            return None
        standardized = residual_sum / max(
            residual_volatility * math.sqrt(float(residuals.size)), 1.0e-8
        )
        efficiency = abs(residual_sum) / max(path_length, 1.0e-8)
        drift = standardized * efficiency**parameters.path_efficiency_exponent
        if not math.isfinite(drift):
            return None

        return _SymbolSignal(
            symbol=symbol,
            drift=float(drift),
            funding=funding_pressure,
            residual_volatility=residual_volatility,
        )


def _utc_timestamp(value: Any) -> pd.Timestamp | None:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError):
        return None
    if timestamp is pd.NaT or timestamp.tzinfo is None:
        return None
    try:
        return timestamp.tz_convert("UTC")
    except (TypeError, ValueError):
        return None


def _eligible_symbols(value: Any) -> tuple[str, ...] | None:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return None
    symbols = tuple(value)
    if any(not isinstance(symbol, str) or not symbol for symbol in symbols):
        return None
    if len(symbols) != len(set(symbols)):
        return None
    return symbols


def _closed_history(
    frame: Any, decision_time: pd.Timestamp
) -> tuple[pd.Series, pd.Series] | None:
    if not isinstance(frame, pd.DataFrame) or not {"open_time", "close"}.issubset(frame.columns):
        return None
    raw_times = frame["open_time"]
    try:
        times = pd.to_datetime(raw_times, errors="coerce")
    except (TypeError, ValueError):
        return None
    if not isinstance(times.dtype, pd.DatetimeTZDtype):
        return None
    times = times.dt.tz_convert("UTC")
    closed_mask = times + _BAR_INTERVAL <= decision_time
    closed_times = times.loc[closed_mask]
    if closed_times.empty or closed_times.isna().any():
        return None
    if closed_times.duplicated().any() or not closed_times.is_monotonic_increasing:
        return None
    closes = pd.to_numeric(frame.loc[closed_mask, "close"], errors="coerce").astype(float)
    close_values = closes.to_numpy(dtype=float)
    if not np.isfinite(close_values).all() or (close_values <= 0.0).any():
        return None

    close_index = pd.DatetimeIndex(closed_times + _BAR_INTERVAL)
    close_series = pd.Series(close_values, index=close_index, dtype=float)
    log_prices = np.log(close_series)
    spacing = close_series.index.to_series().diff()
    returns = log_prices.diff()
    returns.loc[spacing != _BAR_INTERVAL] = np.nan
    return close_series, returns.dropna()


def _funding_pressures(
    funding: pd.DataFrame,
    *,
    eligible: Sequence[str],
    decision_time: pd.Timestamp,
    lookback_days: int,
    minimum_events: int,
) -> dict[str, float] | None:
    required = {"symbol", "funding_time", "funding_rate"}
    if not required.issubset(funding.columns):
        return None
    eligible_assets = set(eligible) - {_BTC_SYMBOL}
    subset = funding.loc[
        funding["symbol"].isin(eligible_assets),
        ["symbol", "funding_time", "funding_rate"],
    ]
    if subset.empty:
        return {}
    try:
        times = pd.to_datetime(subset["funding_time"], errors="coerce")
    except (TypeError, ValueError):
        return None
    if not isinstance(times.dtype, pd.DatetimeTZDtype):
        return None
    times = times.dt.tz_convert("UTC")
    lower = decision_time - pd.Timedelta(days=lookback_days)
    usable_mask = (times >= lower) & (times < decision_time)
    usable = subset.loc[usable_mask, ["symbol", "funding_rate"]].copy()
    usable["funding_time"] = times.loc[usable_mask]
    usable["funding_rate"] = pd.to_numeric(usable["funding_rate"], errors="coerce")

    result: dict[str, float] = {}
    for symbol, rows in usable.groupby("symbol", sort=False):
        if rows["funding_time"].duplicated().any() or len(rows) < minimum_events:
            continue
        rates = rows["funding_rate"].to_numpy(dtype=float)
        if not np.isfinite(rates).all():
            continue
        pressure = float(np.sum(rates))
        if math.isfinite(pressure):
            result[str(symbol)] = pressure
    return result


def _robust_z(values: Sequence[float]) -> np.ndarray | None:
    array = np.asarray(values, dtype=float)
    if array.ndim != 1 or array.size == 0 or not np.isfinite(array).all():
        return None
    median = float(np.median(array))
    mad = float(np.median(np.abs(array - median)))
    scale = 1.4826 * mad
    if not math.isfinite(scale) or scale <= _EPSILON:
        return None
    return np.clip((array - median) / scale, -3.0, 3.0)


def _combine_scores(
    drift_z: Sequence[float], funding_z: Sequence[float], *, penalty: float
) -> np.ndarray | None:
    drift = np.asarray(drift_z, dtype=float)
    funding = np.asarray(funding_z, dtype=float)
    if (
        drift.ndim != 1
        or funding.ndim != 1
        or drift.shape != funding.shape
        or not np.isfinite(drift).all()
        or not np.isfinite(funding).all()
        or not math.isfinite(penalty)
    ):
        return None
    scores = drift - penalty * funding
    return scores if np.isfinite(scores).all() else None


def _select_signed_tails(
    scored: Sequence[tuple[str, float, float]],
    *,
    tail_fraction: float,
    minimum_names_per_side: int,
) -> tuple[list[tuple[str, float, float]], list[tuple[str, float, float]]] | None:
    ordered = sorted(scored, key=lambda item: (item[1], item[0]))
    names_per_side = max(
        minimum_names_per_side,
        math.floor(tail_fraction * len(ordered)),
    )
    if 2 * names_per_side > len(ordered):
        return None
    short_tail = ordered[:names_per_side]
    long_tail = ordered[-names_per_side:]
    if any(score >= 0.0 for _, score, _ in short_tail):
        return None
    if any(score <= 0.0 for _, score, _ in long_tail):
        return None
    return short_tail, long_tail


def _btc_direction(
    closes: pd.Series,
    *,
    decision_time: pd.Timestamp,
    lookback_days: int,
    scale: float,
) -> float:
    past_time = decision_time - pd.Timedelta(days=lookback_days)
    if decision_time not in closes.index or past_time not in closes.index:
        return 0.0
    latest = float(closes.loc[decision_time])
    past = float(closes.loc[past_time])
    if not math.isfinite(latest) or not math.isfinite(past) or latest <= 0.0 or past <= 0.0:
        return 0.0
    return float(np.clip(math.log(latest / past) / scale, -1.0, 1.0))


def _inverse_volatility_sleeve(
    tail: Sequence[tuple[str, float, float]],
    *,
    gross: float,
    cap: float,
) -> dict[str, float] | None:
    symbols = [symbol for symbol, _, _ in tail]
    volatilities = np.asarray([volatility for _, _, volatility in tail], dtype=float)
    if not np.isfinite(volatilities).all() or (volatilities <= _EPSILON).any():
        return None
    inverse = 1.0 / volatilities
    lower, upper = np.quantile(inverse, [0.20, 0.80], method="linear")
    winsorized = np.clip(inverse, lower, upper)
    total = float(np.sum(winsorized))
    if not math.isfinite(total) or total <= _EPSILON:
        return None
    initial = winsorized / total * gross
    projected = _project_capped_simplex(initial, total=gross, cap=cap)
    if projected is None:
        return None
    return {symbol: float(weight) for symbol, weight in zip(symbols, projected, strict=True)}


def _project_capped_simplex(
    values: np.ndarray, *, total: float, cap: float
) -> np.ndarray | None:
    array = np.asarray(values, dtype=float)
    if (
        array.ndim != 1
        or array.size == 0
        or not np.isfinite(array).all()
        or not math.isfinite(total)
        or not math.isfinite(cap)
        or total <= 0.0
        or cap <= 0.0
        or total > array.size * cap + 1.0e-12
    ):
        return None

    lower = float(np.min(array) - cap)
    upper = float(np.max(array))
    for _ in range(100):
        midpoint = (lower + upper) / 2.0
        candidate_sum = float(np.clip(array - midpoint, 0.0, cap).sum())
        if candidate_sum > total:
            lower = midpoint
        else:
            upper = midpoint
    projected = np.clip(array - upper, 0.0, cap)
    residual = total - float(projected.sum())
    if abs(residual) > 1.0e-13:
        for index in range(projected.size):
            if residual > 0.0:
                adjustment = min(residual, cap - projected[index])
            else:
                adjustment = max(residual, -projected[index])
            projected[index] += adjustment
            residual -= adjustment
            if abs(residual) <= 1.0e-13:
                break
    if abs(total - float(projected.sum())) > 1.0e-10:
        return None
    if (projected < -1.0e-12).any() or (projected > cap + 1.0e-12).any():
        return None
    return projected


def _valid_targets(
    targets: Mapping[str, float],
    *,
    eligible: Sequence[str],
    expected_gross: float,
    maximum_abs_net: float,
    symbol_cap: float,
) -> bool:
    if not targets or not set(targets).issubset(set(eligible)):
        return False
    values = np.asarray(list(targets.values()), dtype=float)
    if not np.isfinite(values).all():
        return False
    if not (values > 0.0).any() or not (values < 0.0).any():
        return False
    gross = float(np.sum(np.abs(values)))
    net = float(np.sum(values))
    return (
        abs(gross - expected_gross) <= 1.0e-10
        and abs(net) <= maximum_abs_net + 1.0e-10
        and float(np.max(np.abs(values))) <= symbol_cap + 1.0e-12
    )


def build_strategy() -> ResidualDriftFundingStrategy:
    """Return a fresh rdf-core-h21-k3-g10 strategy instance for the canonical worker."""

    return ResidualDriftFundingStrategy(REFERENCE_PARAMETERS)
