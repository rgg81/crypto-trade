"""T05-AER12-H80-R72-v1 auction-excursion rejection strategy.

The module consumes only the past-only :class:`DecisionContext` supplied by the
common tournament runner and emits signed target weights.  It deliberately has
no data, execution, portfolio-accounting, or filesystem side effects.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from crypto_trade.tournament.protocol import DecisionContext

STRATEGY_NAME = "T05-AER12-H80-R72-v1"
STRATEGY_SEED = 20260713
INTERVAL = pd.Timedelta(hours=8)
BTC_SYMBOL = "BTCUSDT"


@dataclass(frozen=True)
class _CrossSection:
    """Past-only cross-sectional values needed by selection and the QP."""

    frame: pd.DataFrame
    beta_constraint: bool
    funding_constraint: bool


def _as_utc(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _datetime_series(values: pd.Series) -> pd.Series:
    """Parse timestamp columns while also accepting canonical epoch-millisecond rows."""

    timezone = getattr(values.dtype, "tz", None)
    if timezone is not None:
        return values if str(timezone) == "UTC" else values.dt.tz_convert("UTC")
    if pd.api.types.is_datetime64_dtype(values.dtype):
        return values.dt.tz_localize("UTC")
    if pd.api.types.is_numeric_dtype(values.dtype):
        finite = pd.to_numeric(values, errors="coerce")
        magnitude = float(finite.abs().median()) if finite.notna().any() else 0.0
        unit = "ms" if magnitude >= 1.0e11 else "ns"
        return pd.to_datetime(values, utc=True, errors="coerce", unit=unit)
    return pd.to_datetime(values, utc=True, errors="coerce")


def _normalise_symbol_bars(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.DataFrame:
    """Return at most the required trailing history, without changing ``frame``."""

    required = {"open_time", "open", "high", "low", "close", "quote_volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"strategy bars missing columns: {sorted(missing)}")

    # The protocol supplies sorted, already-truncated frames.  A 128-row defensive tail is
    # enough for the 90-slot risk window plus every predecessor, while avoiding a quadratic
    # rescan of multi-year history at every 8h decision.
    columns = ["open_time", "open", "high", "low", "close", "quote_volume"]
    if "close_time" in frame.columns:
        columns.append("close_time")
    work = frame.tail(128).loc[:, columns].copy()
    work["open_time"] = _datetime_series(work["open_time"])
    if work["open_time"].isna().any():
        raise ValueError("strategy bars contain invalid open_time")
    if "close_time" in work.columns:
        work["close_time"] = _datetime_series(work["close_time"])
        if work["close_time"].isna().any():
            raise ValueError("strategy bars contain invalid close_time")
        work = work[work["close_time"] <= decision_time]
    else:
        # ``generate_targets`` defines completion as open_time + interval.  Supporting its
        # minimal neutral schema does not alter the canonical close_time rule.
        work = work[work["open_time"] + INTERVAL <= decision_time]
    work = work[work["open_time"] < decision_time]
    if work["open_time"].duplicated().any():
        raise ValueError("strategy bars contain duplicate open_time rows")
    if not work["open_time"].is_monotonic_increasing:
        work = work.sort_values("open_time", kind="mergesort")
    for column in ("open", "high", "low", "close", "quote_volume"):
        if not pd.api.types.is_numeric_dtype(work[column].dtype):
            work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.set_index("open_time", drop=True)
    work["_present"] = True
    return work


def _scheduled_rows(frame: pd.DataFrame, decision_time: pd.Timestamp, slots: int) -> pd.DataFrame:
    expected = pd.date_range(
        end=decision_time - INTERVAL,
        periods=slots,
        freq=INTERVAL,
        tz="UTC",
    )
    rows = frame.reindex(expected)
    rows["_present"] = rows["_present"].fillna(False).astype(bool)
    return rows


def _adjacent_log_returns(rows: pd.DataFrame) -> np.ndarray:
    close = rows["close"].to_numpy(dtype=float)
    present = rows["_present"].to_numpy(dtype=bool)
    valid = (
        present[1:]
        & present[:-1]
        & np.isfinite(close[1:])
        & np.isfinite(close[:-1])
        & (close[1:] > 0.0)
        & (close[:-1] > 0.0)
    )
    returns = np.full(len(rows) - 1, np.nan, dtype=float)
    returns[valid] = np.log(close[1:][valid] / close[:-1][valid])
    return returns


def _auction_score(rows: pd.DataFrame) -> float | None:
    """Compute A from the final 12 slots of a 13-slot scheduled frame."""

    if len(rows) != 13:
        raise ValueError("auction score requires exactly 13 scheduled rows")
    present = rows["_present"].to_numpy(dtype=bool)
    open_price = rows["open"].to_numpy(dtype=float)
    high = rows["high"].to_numpy(dtype=float)
    low = rows["low"].to_numpy(dtype=float)
    close = rows["close"].to_numpy(dtype=float)

    current_valid = (
        present[1:]
        & np.isfinite(open_price[1:])
        & np.isfinite(high[1:])
        & np.isfinite(low[1:])
        & np.isfinite(close[1:])
        & (open_price[1:] > 0.0)
        & (high[1:] > 0.0)
        & (low[1:] > 0.0)
        & (close[1:] > 0.0)
        & (high[1:] >= np.maximum(open_price[1:], close[1:]))
        & (low[1:] <= np.minimum(open_price[1:], close[1:]))
        & (high[1:] >= low[1:])
    )
    predecessor_valid = present[:-1] & np.isfinite(close[:-1]) & (close[:-1] > 0.0)
    true_range = np.maximum(high[1:], close[:-1]) - np.minimum(low[1:], close[:-1])
    rho = np.divide(
        true_range,
        close[:-1],
        out=np.full(12, np.nan, dtype=float),
        where=predecessor_valid,
    )
    valid = (
        current_valid
        & predecessor_valid
        & np.isfinite(true_range)
        & (true_range > 0.0)
        & np.isfinite(rho)
        & (rho > 1.0e-8)
    )
    q = np.full(12, np.nan, dtype=float)
    if valid.any():
        upper = (high[1:] - np.maximum(open_price[1:], close[1:])) / true_range
        lower = (np.minimum(open_price[1:], close[1:]) - low[1:]) / true_range
        body = (close[1:] - open_price[1:]) / true_range
        difference = lower - upper
        q[valid] = difference[valid] * (1.0 + 0.5 * np.sign(difference[valid]) * body[valid])
    finite = np.isfinite(q)
    if int(finite.sum()) < 9:
        return None
    values = q[finite]
    return float(np.median(values) * abs(np.mean(np.sign(values))))


def _symbol_features(
    rows: pd.DataFrame,
    btc_returns: np.ndarray,
) -> dict[str, float] | None:
    """Calculate all non-funding raw features for one eligible symbol."""

    returns = _adjacent_log_returns(rows.iloc[-64:])
    if len(returns) != 63 or len(btc_returns) != 63:
        return None

    r24_window = returns[-3:]
    r7d_window = returns[-21:]
    if not np.isfinite(r24_window).all() or not np.isfinite(r7d_window).all():
        return None
    r24 = float(r24_window.sum())
    r7d = float(r7d_window.sum())

    vol_valid = np.isfinite(r7d_window)
    if int(vol_valid.sum()) < 18:
        return None
    volatility = float(math.sqrt(1095.0 * np.mean(np.square(r7d_window[vol_valid]))))

    qv_rows = rows.iloc[-21:]
    qv = qv_rows["quote_volume"].to_numpy(dtype=float)
    qv_present = qv_rows["_present"].to_numpy(dtype=bool)
    qv_valid = qv_present & np.isfinite(qv) & (qv >= 0.0)
    if int(qv_valid.sum()) < 18:
        return None
    median_qv = float(np.median(qv[qv_valid]))
    if not math.isfinite(median_qv) or median_qv <= 0.0:
        return None
    log_quote_volume = float(math.log(median_qv))

    aligned = np.isfinite(returns) & np.isfinite(btc_returns)
    if int(aligned.sum()) < 50:
        return None
    symbol_aligned = returns[aligned]
    btc_aligned = btc_returns[aligned]
    symbol_deviation = symbol_aligned - symbol_aligned.mean()
    btc_deviation = btc_aligned - btc_aligned.mean()
    btc_squared_deviation = float(np.mean(np.square(btc_deviation)))
    if not math.isfinite(btc_squared_deviation) or btc_squared_deviation <= 1.0e-12:
        return None
    beta = float(np.sum(symbol_deviation * btc_deviation) / np.sum(np.square(btc_deviation)))

    auction = _auction_score(rows.iloc[-13:])
    if auction is None or not math.isfinite(auction):
        return None
    return {
        "auction": auction,
        "r24": r24,
        "r7d": r7d,
        "volatility": volatility,
        "log_quote_volume": log_quote_volume,
        "beta": beta,
    }


def _robust_z(values: np.ndarray) -> tuple[np.ndarray, float]:
    median = float(np.median(values))
    mad = float(np.median(np.abs(values - median)))
    if mad == 0.0:
        return np.zeros(len(values), dtype=float), mad
    z = np.clip((values - median) / (1.4826 * mad), -3.0, 3.0)
    return np.asarray(z, dtype=float), mad


def _funding_features(
    funding: pd.DataFrame,
    symbols: tuple[str, ...],
    decision_time: pd.Timestamp,
) -> dict[str, tuple[float, float]]:
    output = {symbol: (0.0, 1.0) for symbol in symbols}
    if funding.empty:
        return output
    required = {"symbol", "funding_time", "funding_rate"}
    missing = required - set(funding.columns)
    if missing:
        raise ValueError(f"strategy funding missing columns: {sorted(missing)}")
    # The last 4,096 actual events exceed the theoretical 16h requirement for forty names even
    # at hourly funding, yet keep canonical runtime bounded as history grows.
    frame = funding.tail(4096).loc[:, ["symbol", "funding_time", "funding_rate"]].copy()
    frame["symbol"] = frame["symbol"].astype(str)
    frame["funding_time"] = _datetime_series(frame["funding_time"])
    if frame["funding_time"].isna().any():
        raise ValueError("strategy funding contains invalid funding_time")
    if not pd.api.types.is_numeric_dtype(frame["funding_rate"].dtype):
        frame["funding_rate"] = pd.to_numeric(frame["funding_rate"], errors="coerce")
    frame = frame[frame["symbol"].isin(symbols) & (frame["funding_time"] < decision_time)]
    if frame.duplicated(["symbol", "funding_time"]).any():
        raise ValueError("strategy funding contains duplicate symbol/timestamp rows")
    if frame.empty:
        return output
    frame = frame.sort_values(["funding_time", "symbol"], kind="mergesort")
    latest = frame.groupby("symbol", sort=False, observed=True).tail(1)
    for row in latest.itertuples(index=False):
        age = decision_time - row.funding_time
        rate = float(row.funding_rate)
        if pd.Timedelta(0) <= age <= pd.Timedelta(hours=16) and math.isfinite(rate):
            output[row.symbol] = (rate, 0.0)
    return output


def _stress_value(btc_rows: pd.DataFrame) -> float | None:
    rows = btc_rows.iloc[-90:]
    if len(rows) != 90:
        return None
    high = rows["high"].to_numpy(dtype=float)
    low = rows["low"].to_numpy(dtype=float)
    present = rows["_present"].to_numpy(dtype=bool)
    valid = (
        present & np.isfinite(high) & np.isfinite(low) & (high > 0.0) & (low > 0.0) & (high >= low)
    )
    if int(valid.sum()) < 75:
        return None
    log_range_squared = np.square(np.log(high[valid] / low[valid]))
    return float(math.sqrt(1095.0 / (4.0 * math.log(2.0)) * np.mean(log_range_squared)))


def _next_stress(previous: bool, volatility: float | None) -> bool:
    """Apply the frozen 0.80/0.65 hysteresis, including equality retention."""

    if volatility is None:
        return True
    if volatility > 0.80:
        return True
    if volatility < 0.65:
        return False
    return previous


def _build_cross_section(
    context: DecisionContext,
    normalised: Mapping[str, pd.DataFrame],
) -> _CrossSection | None:
    decision_time = _as_utc(context.decision_time)
    symbols = tuple(sorted(normalised))
    if BTC_SYMBOL not in normalised:
        return None
    btc_rows = _scheduled_rows(normalised[BTC_SYMBOL], decision_time, 64)
    btc_returns = _adjacent_log_returns(btc_rows)
    funding = _funding_features(context.funding, symbols, decision_time)

    records: list[dict[str, float | str]] = []
    for symbol in symbols:
        rows = _scheduled_rows(normalised[symbol], decision_time, 64)
        features = _symbol_features(rows, btc_returns)
        if features is None:
            continue
        funding_rate, funding_missing = funding[symbol]
        records.append(
            {
                "symbol": symbol,
                **features,
                "funding": funding_rate,
                "funding_missing": funding_missing,
            }
        )
    if len(records) < 10:
        return None

    frame = pd.DataFrame.from_records(records).set_index("symbol").sort_index()
    alpha_z, alpha_mad = _robust_z(frame["auction"].to_numpy(dtype=float))
    if alpha_mad == 0.0:
        return None

    nuisance_columns = (
        "r24",
        "r7d",
        "volatility",
        "log_quote_volume",
        "beta",
        "funding",
    )
    nuisance_z: dict[str, np.ndarray] = {}
    nuisance_mad: dict[str, float] = {}
    for column in nuisance_columns:
        nuisance_z[column], nuisance_mad[column] = _robust_z(frame[column].to_numpy(dtype=float))

    design = np.column_stack(
        [
            np.ones(len(frame), dtype=float),
            nuisance_z["r24"],
            nuisance_z["r7d"],
            nuisance_z["volatility"],
            nuisance_z["log_quote_volume"],
            nuisance_z["beta"],
            nuisance_z["funding"],
            frame["funding_missing"].to_numpy(dtype=float),
        ]
    )
    coefficients = np.linalg.pinv(design, rcond=1.0e-10) @ alpha_z
    residual = alpha_z - design @ coefficients
    if not np.isfinite(residual).all():
        return None

    frame["z_beta"] = nuisance_z["beta"]
    frame["z_funding"] = nuisance_z["funding"]
    frame["residual"] = residual
    ordered = sorted(frame.index, key=lambda symbol: (float(frame.at[symbol, "residual"]), symbol))
    percentile = {symbol: rank / (len(ordered) - 1) for rank, symbol in enumerate(ordered)}
    frame["percentile"] = pd.Series(percentile)
    return _CrossSection(
        frame=frame,
        beta_constraint=nuisance_mad["beta"] != 0.0,
        funding_constraint=nuisance_mad["funding"] != 0.0,
    )


def _select_tails(
    frame: pd.DataFrame,
    prior_longs: frozenset[str],
    prior_shorts: frozenset[str],
) -> tuple[frozenset[str], frozenset[str]]:
    percentile = frame["percentile"].to_dict()
    count = len(frame)
    maximum = min(6, max(2, math.ceil(0.15 * count)))

    retained_longs = [
        symbol for symbol in prior_longs if symbol in percentile and percentile[symbol] >= 0.55
    ]
    retained_longs.sort(key=lambda symbol: (-percentile[symbol], symbol))
    longs = retained_longs[:maximum]
    long_entries = [
        symbol for symbol in percentile if symbol not in longs and percentile[symbol] >= 0.80
    ]
    long_entries.sort(key=lambda symbol: (-percentile[symbol], symbol))
    longs.extend(long_entries[: maximum - len(longs)])

    retained_shorts = [
        symbol for symbol in prior_shorts if symbol in percentile and percentile[symbol] <= 0.45
    ]
    retained_shorts.sort(key=lambda symbol: (percentile[symbol], symbol))
    shorts = retained_shorts[:maximum]
    short_entries = [
        symbol for symbol in percentile if symbol not in shorts and percentile[symbol] <= 0.20
    ]
    short_entries.sort(key=lambda symbol: (percentile[symbol], symbol))
    shorts.extend(short_entries[: maximum - len(shorts)])
    return frozenset(longs), frozenset(shorts)


def _attempt_slsqp(
    desired: np.ndarray,
    previous: np.ndarray,
    side: np.ndarray,
    gross_per_side: float,
    factor_rows: tuple[np.ndarray, ...],
) -> np.ndarray | None:
    rows = [np.ones(len(desired), dtype=float), side]
    right_hand_side = [0.0, 2.0 * gross_per_side]
    rows.extend(factor_rows)
    right_hand_side.extend([0.0] * len(factor_rows))
    equality_matrix = np.vstack(rows)
    equality_target = np.asarray(right_hand_side, dtype=float)
    bounds = [(0.0, 0.08) if value > 0.0 else (-0.08, 0.0) for value in side]

    def objective(weights: np.ndarray) -> float:
        return float(
            np.sum(np.square(weights - desired)) + 4.0 * np.sum(np.square(weights - previous))
        )

    def gradient(weights: np.ndarray) -> np.ndarray:
        return 2.0 * (weights - desired) + 8.0 * (weights - previous)

    result = minimize(
        objective,
        desired.copy(),
        method="SLSQP",
        jac=gradient,
        bounds=bounds,
        constraints={
            "type": "eq",
            "fun": lambda weights: equality_matrix @ weights - equality_target,
            "jac": lambda _weights: equality_matrix,
        },
        options={"ftol": 1.0e-12, "maxiter": 500, "disp": False},
    )
    weights = np.asarray(result.x, dtype=float)
    residual = equality_matrix @ weights - equality_target
    if not result.success or not np.isfinite(weights).all():
        return None
    if float(np.max(np.abs(residual))) > 1.0e-8:
        return None
    signed = side * weights
    if (signed < -1.0e-8).any() or (signed > 0.08 + 1.0e-8).any():
        return None
    return weights


def _solve_qp(
    cross_section: _CrossSection,
    longs: frozenset[str],
    shorts: frozenset[str],
    previous_weights: Mapping[str, float],
    stress: bool,
) -> tuple[dict[str, float], int] | None:
    symbols = tuple(sorted(longs | shorts))
    side = np.asarray([1.0 if symbol in longs else -1.0 for symbol in symbols])
    gross_ceiling = 0.36 if stress else 0.72
    gross_per_side = min(
        gross_ceiling / 2.0,
        0.06 * min(len(longs), len(shorts)),
    )
    desired = np.asarray(
        [
            gross_per_side / len(longs) if symbol in longs else -gross_per_side / len(shorts)
            for symbol in symbols
        ],
        dtype=float,
    )
    previous = np.asarray([float(previous_weights.get(symbol, 0.0)) for symbol in symbols])
    beta = cross_section.frame.loc[list(symbols), "z_beta"].to_numpy(dtype=float)
    funding = cross_section.frame.loc[list(symbols), "z_funding"].to_numpy(dtype=float)

    attempts: list[tuple[int, tuple[np.ndarray, ...]]] = []
    level_one: list[np.ndarray] = []
    if cross_section.beta_constraint:
        level_one.append(beta)
    if cross_section.funding_constraint:
        level_one.append(funding)
    attempts.append((1, tuple(level_one)))
    if cross_section.beta_constraint:
        attempts.append((2, (beta,)))
    else:
        attempts.append((2, ()))
    attempts.append((3, ()))

    tried: set[tuple[bytes, ...]] = set()
    for level, factors in attempts:
        signature = tuple(np.asarray(row, dtype="<f8").tobytes() for row in factors)
        if signature in tried:
            continue
        tried.add(signature)
        weights = _attempt_slsqp(desired, previous, side, gross_per_side, factors)
        if weights is None:
            continue
        return (
            {symbol: float(weight) for symbol, weight in zip(symbols, weights, strict=True)},
            level,
        )
    return None


class AuctionExcursionRejectionStrategy:
    """Stateful, deterministic target-weight implementation of the frozen T05 brief."""

    def __init__(self) -> None:
        self._longs: frozenset[str] = frozenset()
        self._shorts: frozenset[str] = frozenset()
        self._previous_weights: dict[str, float] = {}
        self._membership: tuple[str, ...] | None = None
        self._stress = True
        self._last_mapping_time: pd.Timestamp | None = None
        self._last_decision_time: pd.Timestamp | None = None
        self.last_fallback_level: int | None = None
        self.fallback_history: list[tuple[pd.Timestamp, int]] = []

    def _emit_flat(
        self,
        decision_time: pd.Timestamp,
        membership: tuple[str, ...],
        stress: bool,
    ) -> dict[str, float]:
        self._longs = frozenset()
        self._shorts = frozenset()
        self._previous_weights = {}
        self._membership = membership
        self._stress = stress
        self._last_mapping_time = decision_time
        self._last_decision_time = decision_time
        self.last_fallback_level = 4
        self.fallback_history.append((decision_time, 4))
        return {}

    def target_weights(
        self,
        context: DecisionContext,
        *,
        seed: int,
    ) -> Mapping[str, float] | None:
        if int(seed) != STRATEGY_SEED:
            raise ValueError(f"{STRATEGY_NAME} requires seed {STRATEGY_SEED}")
        decision_time = _as_utc(context.decision_time)
        if self._last_decision_time is not None and decision_time <= self._last_decision_time:
            raise ValueError("strategy decision times must be strictly increasing")
        if decision_time != decision_time.floor("h") or decision_time.hour % 8 != 0:
            raise ValueError("strategy decisions must be UTC 8h boundaries")

        membership = tuple(sorted(set(str(symbol) for symbol in context.eligible_symbols)))
        normalised: dict[str, pd.DataFrame] = {}
        for symbol in membership:
            if symbol not in context.bars:
                continue
            normalised[symbol] = _normalise_symbol_bars(context.bars[symbol], decision_time)

        btc_scheduled = (
            _scheduled_rows(normalised[BTC_SYMBOL], decision_time, 90)
            if BTC_SYMBOL in normalised
            else None
        )
        volatility = _stress_value(btc_scheduled) if btc_scheduled is not None else None
        stress = _next_stress(self._stress, volatility)

        cross_section = _build_cross_section(context, normalised)
        if cross_section is None:
            return self._emit_flat(decision_time, membership, stress)
        longs, shorts = _select_tails(cross_section.frame, self._longs, self._shorts)
        if len(longs) < 2 or len(shorts) < 2:
            return self._emit_flat(decision_time, membership, stress)

        selection_changed = longs != self._longs or shorts != self._shorts
        membership_changed = membership != self._membership
        stress_changed = stress != self._stress
        refresh_due = (
            self._last_mapping_time is None
            or decision_time - self._last_mapping_time >= pd.Timedelta(hours=72)
        )
        if not (selection_changed or membership_changed or stress_changed or refresh_due):
            self._last_decision_time = decision_time
            return None

        solution = _solve_qp(
            cross_section,
            longs,
            shorts,
            self._previous_weights,
            stress,
        )
        if solution is None:
            return self._emit_flat(decision_time, membership, stress)
        weights, fallback_level = solution
        if not set(weights).issubset(membership):
            raise RuntimeError("internal error: QP emitted an ineligible symbol")
        values = np.asarray(list(weights.values()), dtype=float)
        if not np.isfinite(values).all():
            raise RuntimeError("internal error: QP emitted non-finite weights")

        self._longs = longs
        self._shorts = shorts
        self._previous_weights = dict(weights)
        self._membership = membership
        self._stress = stress
        self._last_mapping_time = decision_time
        self._last_decision_time = decision_time
        self.last_fallback_level = fallback_level
        self.fallback_history.append((decision_time, fallback_level))
        return weights


def build_strategy() -> AuctionExcursionRejectionStrategy:
    """Return a fresh strategy instance for the canonical worker."""

    return AuctionExcursionRejectionStrategy()
