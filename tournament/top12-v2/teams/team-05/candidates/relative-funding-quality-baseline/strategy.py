"""Relative settled-funding carry baseline for Team 05."""

from __future__ import annotations

from collections.abc import Mapping as MappingABC
from itertools import combinations
from typing import Mapping

import numpy as np
import pandas as pd


FUNDING_FORMATION_ROWS = 42 * 3
MIN_FUNDING_ROWS = 24 * 3
SLOW_HALF_LIFE_ROWS = 21 * 3
FAST_HALF_LIFE_ROWS = 7 * 3
CURRENT_DISPERSION_ROWS = 3 * 3
PRICE_QUALITY_BARS = 28 * 3
MIN_PRICE_BARS = 20 * 3
MIN_SYMBOLS = 8
POOL_NAMES_PER_SIDE = 4
HELD_NAMES_PER_SIDE = 3
MIN_PERSISTENCE = 0.60
MAX_ABSOLUTE_PRICE_MOVE = 0.50
MAX_ABSOLUTE_BETA = 2.0
MAX_PORTFOLIO_BETA_GAP = 0.35
MIN_DISPERSION_RATIO = 0.75
FULL_DISPERSION_RATIO = 1.50


def _utc_timestamp(value) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _parse_times(values: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(values.dtype):
        numeric = pd.to_numeric(values, errors="coerce")
        finite = numeric[np.isfinite(numeric)]
        if finite.empty:
            return pd.to_datetime(values, utc=True, errors="coerce")
        magnitude = float(finite.abs().median())
        if magnitude >= 1e17:
            unit = "ns"
        elif magnitude >= 1e14:
            unit = "us"
        elif magnitude >= 1e11:
            unit = "ms"
        else:
            unit = "s"
        return pd.to_datetime(numeric, unit=unit, utc=True, errors="coerce")
    return pd.to_datetime(values, utc=True, errors="coerce")


def _first_column(frame: pd.DataFrame, names: tuple[str, ...]) -> str | None:
    for name in names:
        if name in frame.columns:
            return name
    return None


def _symbol_funding_frame(funding, symbol: str) -> pd.DataFrame | None:
    if isinstance(funding, pd.DataFrame):
        symbol_column = _first_column(
            funding, ("symbol", "contract", "instrument", "ticker")
        )
        if symbol_column is None:
            return None
        symbol_values = funding[symbol_column].astype(str)
        return funding.loc[symbol_values == symbol]
    if isinstance(funding, MappingABC):
        frame = funding.get(symbol)
        if isinstance(frame, pd.DataFrame):
            return frame
    return None


def _settled_funding_series(funding, symbol: str, decision_time: pd.Timestamp):
    frame = _symbol_funding_frame(funding, symbol)
    if frame is None or frame.empty:
        return None
    time_column = _first_column(
        frame,
        (
            "funding_time",
            "fundingTime",
            "settlement_time",
            "settle_time",
            "time",
        ),
    )
    rate_column = _first_column(frame, ("funding_rate", "fundingRate", "rate"))
    if time_column is None or rate_column is None:
        return None

    funding_time = _parse_times(frame[time_column])
    funding_rate = pd.to_numeric(frame[rate_column], errors="coerce")
    usable = pd.DataFrame({"time": funding_time, "rate": funding_rate})
    # Settlement at the decision instant is excluded: only strictly prior rows qualify.
    usable = usable.loc[
        usable["time"].notna()
        & usable["rate"].notna()
        & np.isfinite(usable["rate"])
        & (usable["time"] < decision_time)
    ]
    if usable.empty:
        return None
    usable = usable.sort_values("time", kind="mergesort")
    usable = usable.drop_duplicates("time", keep="last")
    series = usable.set_index("time")["rate"].tail(FUNDING_FORMATION_ROWS)
    if len(series) < MIN_FUNDING_ROWS:
        return None
    return series


def _completed_price_returns(
    frame: pd.DataFrame, decision_time: pd.Timestamp
) -> pd.Series | None:
    if not isinstance(frame, pd.DataFrame):
        return None
    if "open_time" not in frame.columns or "close" not in frame.columns:
        return None
    open_time = _parse_times(frame["open_time"])
    close = pd.to_numeric(frame["close"], errors="coerce")
    completed_cutoff = decision_time - pd.Timedelta(hours=8)
    usable = pd.DataFrame({"time": open_time, "close": close})
    usable = usable.loc[
        usable["time"].notna()
        & usable["close"].notna()
        & np.isfinite(usable["close"])
        & (usable["close"] > 0.0)
        & (usable["time"] <= completed_cutoff)
    ]
    if usable.empty:
        return None
    usable = usable.sort_values("time", kind="mergesort")
    usable = usable.drop_duplicates("time", keep="last")
    log_close = np.log(usable.set_index("time")["close"])
    returns = log_close.diff().replace([np.inf, -np.inf], np.nan).dropna()
    if len(returns) < MIN_PRICE_BARS:
        return None
    return returns.tail(PRICE_QUALITY_BARS)


def _decay_weights(length: int, half_life: int) -> np.ndarray:
    ages = np.arange(length - 1, -1, -1, dtype=float)
    return np.exp(np.log(0.5) * ages / float(half_life))


def _weighted_average(values: np.ndarray, weights: np.ndarray) -> float:
    valid = np.isfinite(values) & np.isfinite(weights)
    if not valid.any():
        return float("nan")
    denominator = float(weights[valid].sum())
    if denominator <= 0.0:
        return float("nan")
    return float(np.dot(values[valid], weights[valid]) / denominator)


def _funding_forecasts(relative_funding: pd.DataFrame):
    slow_weights = _decay_weights(len(relative_funding), SLOW_HALF_LIFE_ROWS)
    fast_weights = _decay_weights(len(relative_funding), FAST_HALF_LIFE_ROWS)
    forecast: dict[str, float] = {}
    persistence: dict[str, float] = {}

    for symbol in relative_funding.columns:
        values = relative_funding[symbol].to_numpy(dtype=float)
        valid = np.isfinite(values)
        if int(valid.sum()) < MIN_FUNDING_ROWS:
            continue
        slow = _weighted_average(values[valid], slow_weights[valid])
        fast = _weighted_average(values[valid], fast_weights[valid])
        if not np.isfinite(slow) or not np.isfinite(fast) or slow == 0.0:
            continue
        if slow * fast <= 0.0:
            continue
        direction = 1.0 if slow > 0.0 else -1.0
        agreeing = (direction * values[valid]) > 0.0
        agreement = _weighted_average(agreeing.astype(float), slow_weights[valid])
        if np.isfinite(agreement) and agreement >= MIN_PERSISTENCE:
            forecast[symbol] = slow
            persistence[symbol] = agreement
    return pd.Series(forecast, dtype=float), pd.Series(persistence, dtype=float)


def _price_quality_metrics(price_returns: pd.DataFrame):
    row_minimum = max(6, int(np.ceil(0.60 * len(price_returns.columns))))
    price_returns = price_returns.loc[price_returns.notna().sum(axis=1) >= row_minimum]
    if len(price_returns) < MIN_PRICE_BARS:
        return {}, {}
    market_return = price_returns.median(axis=1, skipna=True)
    betas: dict[str, float] = {}
    absolute_moves: dict[str, float] = {}

    for symbol in price_returns.columns:
        aligned = pd.concat(
            [price_returns[symbol].rename("asset"), market_return.rename("market")],
            axis=1,
            join="inner",
        ).dropna()
        if len(aligned) < MIN_PRICE_BARS:
            continue
        market = aligned["market"].to_numpy(dtype=float)
        asset = aligned["asset"].to_numpy(dtype=float)
        market_centered = market - float(market.mean())
        asset_centered = asset - float(asset.mean())
        denominator = float(np.dot(market_centered, market_centered))
        if denominator <= 1e-16:
            continue
        beta = float(np.dot(asset_centered, market_centered) / denominator)
        absolute_move = abs(float(asset.sum()))
        if np.isfinite(beta) and np.isfinite(absolute_move):
            betas[symbol] = beta
            absolute_moves[symbol] = absolute_move
    return betas, absolute_moves


def _choose_price_neutral_book(
    forecast: pd.Series, persistence: pd.Series, betas: dict[str, float], moves: dict[str, float]
):
    qualified = [
        symbol
        for symbol in forecast.index
        if symbol in betas
        and symbol in moves
        and abs(betas[symbol]) <= MAX_ABSOLUTE_BETA
        and moves[symbol] <= MAX_ABSOLUTE_PRICE_MOVE
        and persistence.get(symbol, 0.0) >= MIN_PERSISTENCE
    ]
    long_rank = sorted(
        (symbol for symbol in qualified if forecast[symbol] < 0.0),
        key=lambda symbol: (float(forecast[symbol]), symbol),
    )
    short_rank = sorted(
        (symbol for symbol in qualified if forecast[symbol] > 0.0),
        key=lambda symbol: (-float(forecast[symbol]), symbol),
    )
    long_pool = long_rank[:POOL_NAMES_PER_SIDE]
    short_pool = short_rank[:POOL_NAMES_PER_SIDE]
    if len(long_pool) < HELD_NAMES_PER_SIDE or len(short_pool) < HELD_NAMES_PER_SIDE:
        return None

    feasible = []
    for long_names in combinations(long_pool, HELD_NAMES_PER_SIDE):
        for short_names in combinations(short_pool, HELD_NAMES_PER_SIDE):
            long_beta = float(np.mean([betas[symbol] for symbol in long_names]))
            short_beta = float(np.mean([betas[symbol] for symbol in short_names]))
            beta_gap = abs(long_beta - short_beta)
            if beta_gap > MAX_PORTFOLIO_BETA_GAP:
                continue
            carry_spread = float(
                np.mean([forecast[symbol] for symbol in short_names])
                - np.mean([forecast[symbol] for symbol in long_names])
            )
            if carry_spread <= 0.0:
                continue
            # Price only defines feasibility. Among feasible books, settled-funding
            # carry is the optimization objective and deterministic symbol order ties.
            key = (-carry_spread, beta_gap, tuple(long_names), tuple(short_names))
            feasible.append((key, tuple(long_names), tuple(short_names)))
    if not feasible:
        return None
    feasible.sort(key=lambda item: item[0])
    _, long_names, short_names = feasible[0]
    return long_names, short_names


class RelativeFundingQualityStrategy:
    """Receive a persistent relative funding spread when dispersion is wide."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed
        decision_time = _utc_timestamp(context.decision_time)
        if (
            decision_time.weekday() != 0
            or decision_time.hour != 0
            or decision_time.minute != 0
            or decision_time.second != 0
        ):
            return None

        eligible = sorted({str(symbol) for symbol in context.eligible_symbols})
        if len(eligible) < MIN_SYMBOLS:
            return {}

        funding_columns: list[pd.Series] = []
        for symbol in eligible:
            series = _settled_funding_series(context.funding, symbol, decision_time)
            if series is not None:
                funding_columns.append(series.rename(symbol))
        if len(funding_columns) < MIN_SYMBOLS:
            return {}

        funding = pd.concat(funding_columns, axis=1, join="outer").sort_index()
        funding = funding.tail(FUNDING_FORMATION_ROWS)
        row_minimum = max(6, int(np.ceil(0.60 * len(funding_columns))))
        funding = funding.loc[funding.notna().sum(axis=1) >= row_minimum]
        if len(funding) < MIN_FUNDING_ROWS:
            return {}

        cross_median = funding.median(axis=1, skipna=True)
        relative_funding = funding.sub(cross_median, axis=0)
        dispersion = relative_funding.abs().median(axis=1, skipna=True).dropna()
        if len(dispersion) < MIN_FUNDING_ROWS:
            return {}
        normal_dispersion = float(dispersion.median())
        current_dispersion = float(dispersion.tail(CURRENT_DISPERSION_ROWS).median())
        if normal_dispersion <= 1e-12 or not np.isfinite(current_dispersion):
            return {}
        dispersion_ratio = current_dispersion / normal_dispersion
        if dispersion_ratio < MIN_DISPERSION_RATIO:
            return {}

        forecast, persistence = _funding_forecasts(relative_funding)
        if len(forecast) < MIN_SYMBOLS:
            return {}

        price_columns: list[pd.Series] = []
        for symbol in forecast.index:
            frame = context.bars.get(str(symbol))
            returns = _completed_price_returns(frame, decision_time)
            if returns is not None:
                price_columns.append(returns.rename(str(symbol)))
        if len(price_columns) < MIN_SYMBOLS:
            return {}
        price_returns = pd.concat(price_columns, axis=1, join="outer").sort_index()
        price_returns = price_returns.tail(PRICE_QUALITY_BARS)
        betas, moves = _price_quality_metrics(price_returns)
        selected = _choose_price_neutral_book(forecast, persistence, betas, moves)
        if selected is None:
            return {}
        long_names, short_names = selected

        activation = float(
            np.clip(
                (dispersion_ratio - MIN_DISPERSION_RATIO)
                / (FULL_DISPERSION_RATIO - MIN_DISPERSION_RATIO),
                0.0,
                1.0,
            )
        )
        gross_exposure = 0.50 + 0.50 * activation
        weight_per_name = gross_exposure / (2.0 * HELD_NAMES_PER_SIDE)
        targets = {symbol: 0.0 for symbol in eligible}
        for symbol in long_names:
            targets[str(symbol)] = float(weight_per_name)
        for symbol in short_names:
            targets[str(symbol)] = float(-weight_per_name)
        return targets


def build_strategy() -> RelativeFundingQualityStrategy:
    return RelativeFundingQualityStrategy()
