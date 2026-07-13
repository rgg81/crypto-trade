"""Funding Receiver Aftershock target-weight strategy for team-04.

The implementation is deliberately stateless: every decision is reconstructed from the
past-only ``DecisionContext``.  It emits weights only; execution, costs, funding cashflows,
membership enforcement, and PnL remain evaluator-owned.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Collection, Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext

STRATEGY_SEED = 20260713
BAR_INTERVAL = pd.Timedelta(hours=8)
FUNDING_LOOKBACK = pd.Timedelta(days=180)
PRICE_LOOKBACK = pd.Timedelta(days=180)
FUNDING_SAME_HOUR_MINIMUM = 20
FUNDING_ALL_HOUR_MINIMUM = 60
PRICE_SAME_HOUR_MINIMUM = 30
PRICE_ALL_HOUR_MINIMUM = 90
BETA_OBSERVATIONS = 270
BETA_MINIMUM = 120
RESIDUAL_OBSERVATIONS = 90
RESIDUAL_MINIMUM = 60
CROSS_SECTION_MINIMUM = 8
FALLBACK_MARKET_MINIMUM = 10
FUNDING_SCALE_FLOOR = 1e-5
RESIDUAL_SCALE_FLOOR = 5e-4
FUNDING_THRESHOLD = 1.5
RESPONSE_THRESHOLD = 0.25
BETA_GAP_LIMIT = 0.25
BETA_CLIP = 3.0
SCORE_CLIP = 6.0
MAX_PAIRS = 5
SYMBOL_WEIGHT_CAP = 0.08
PAIR_BOOK_BUDGET = 0.40
MARKET_SYMBOL = "BTCUSDT"


@dataclasses.dataclass(frozen=True)
class _TransformedBars:
    """A symbol's past-only UTC-slot-demeaned returns at one decision."""

    history: pd.Series
    response: float


@dataclasses.dataclass(frozen=True)
class _PriceState:
    """Past-only beta and response residual for one funding-matched symbol."""

    beta: float
    response_residual: float
    residual_scale: float


class FundingReceiverAftershock:
    """Exact frozen ``t04-fps-001`` target-weight adapter."""

    def target_weights(self, context: DecisionContext, *, seed: int) -> Mapping[str, float]:
        if seed != STRATEGY_SEED:
            raise ValueError(f"team-04 requires seed {STRATEGY_SEED}")

        decision_time = _utc_timestamp(context.decision_time)
        if decision_time is None:
            return {}
        eligible = tuple(sorted({str(symbol) for symbol in context.eligible_symbols}))
        if len(eligible) < CROSS_SECTION_MINIMUM:
            return {}

        # Every usable event's first wholly subsequent response bar is necessarily [b, t].
        response_open = decision_time - BAR_INTERVAL
        response_symbols = frozenset(
            symbol
            for symbol in eligible
            if _has_usable_response_bar(context.bars.get(symbol), response_open, decision_time)
        )
        if len(response_symbols) < CROSS_SECTION_MINIMUM:
            return {}

        matched_funding = _matched_funding_groups(
            context.funding, eligible, decision_time, response_open
        )
        raw_z = _funding_z_scores_from_groups(matched_funding, response_symbols)
        if len(raw_z) < CROSS_SECTION_MINIMUM:
            return {}
        z_median = float(np.median(np.fromiter(raw_z.values(), dtype=float)))
        funding_scores = {symbol: z_value - z_median for symbol, z_value in raw_z.items()}

        transformed = _prepare_transformed_cross_section(
            context.bars, eligible, response_open, decision_time
        )
        if len(transformed) < CROSS_SECTION_MINIMUM:
            return {}

        market_history: pd.Series | None
        market_response: float | None
        primary_market = transformed.get(MARKET_SYMBOL)
        if primary_market is not None:
            market_history = primary_market.history
            market_response = primary_market.response
        else:
            market_history, market_response = _fallback_market(transformed, response_open)
            if market_history is None or market_response is None:
                return {}

        price_states: dict[str, _PriceState] = {}
        for symbol in sorted(raw_z):
            state = _price_state(
                transformed[symbol], market_history, market_response, response_open
            )
            if state is not None:
                price_states[symbol] = state
        if len(price_states) < CROSS_SECTION_MINIMUM:
            return {}

        residual_median = float(
            np.median(
                np.fromiter(
                    (state.response_residual for state in price_states.values()), dtype=float
                )
            )
        )
        response_scores = {
            symbol: float(
                np.clip(
                    (state.response_residual - residual_median) / state.residual_scale,
                    -SCORE_CLIP,
                    SCORE_CLIP,
                )
            )
            for symbol, state in price_states.items()
        }

        active: dict[str, tuple[int, float, float]] = {}
        funding_by_symbol = {
            symbol: float(group.iloc[-1]["funding_rate"])
            for symbol, group in matched_funding.items()
            if math.isfinite(float(group.iloc[-1]["funding_rate"]))
        }
        for symbol in sorted(price_states):
            funding_rate = funding_by_symbol.get(symbol)
            if funding_rate is None:
                continue
            funding_score = funding_scores[symbol]
            response_score = response_scores[symbol]
            if (
                _sign(funding_score) != _sign(funding_rate)
                or abs(funding_score) < FUNDING_THRESHOLD
                or abs(response_score) < RESPONSE_THRESHOLD
                or funding_score * response_score >= 0.0
            ):
                continue
            direction = -_sign(funding_rate)
            if direction == 0:
                continue
            strength = math.sqrt(abs(funding_score * response_score))
            if math.isfinite(strength):
                active[symbol] = (direction, strength, price_states[symbol].beta)

        selected = _select_pairs(active)
        if len(selected) < 2:
            return {}
        symbol_weight = min(SYMBOL_WEIGHT_CAP, PAIR_BOOK_BUDGET / len(selected))
        weights: dict[str, float] = {}
        for long_symbol, short_symbol in selected:
            weights[long_symbol] = symbol_weight
            weights[short_symbol] = -symbol_weight
        return {symbol: weights[symbol] for symbol in sorted(weights)}


def build_strategy() -> FundingReceiverAftershock:
    """Return a fresh strategy instance for the canonical worker."""

    return FundingReceiverAftershock()


def _utc_timestamp(value: object) -> pd.Timestamp | None:
    try:
        timestamp = pd.Timestamp(value)
    except (TypeError, ValueError):
        return None
    if pd.isna(timestamp):
        return None
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _utc_series(values: pd.Series) -> pd.Series | None:
    """Normalize timestamps while preserving the canonical fast path's existing dtype."""

    try:
        timezone = getattr(values.dtype, "tz", None)
        if timezone is not None:
            return values if str(timezone) == "UTC" else values.dt.tz_convert("UTC")
        if pd.api.types.is_datetime64_dtype(values.dtype):
            return values.dt.tz_localize("UTC")
        return pd.to_datetime(values, utc=True, errors="coerce")
    except (AttributeError, TypeError, ValueError):
        return None


def _sign(value: float) -> int:
    if value > 0.0:
        return 1
    if value < 0.0:
        return -1
    return 0


def _mad(values: np.ndarray) -> float:
    median = float(np.median(values))
    return float(np.median(np.abs(values - median)))


def _prepare_transformed_cross_section(
    bars: Mapping[str, pd.DataFrame],
    eligible: tuple[str, ...],
    response_open: pd.Timestamp,
    decision_time: pd.Timestamp,
) -> dict[str, _TransformedBars]:
    prepared: dict[str, _TransformedBars] = {}
    for symbol in eligible:
        frame = bars.get(symbol)
        if frame is None:
            continue
        transformed = _transform_symbol_bars(frame, response_open, decision_time)
        if transformed is not None:
            prepared[symbol] = transformed
    return prepared


def _has_usable_response_bar(
    frame: pd.DataFrame | None,
    response_open: pd.Timestamp,
    decision_time: pd.Timestamp,
) -> bool:
    if frame is None or not {"open_time", "open", "close"}.issubset(frame.columns):
        return False
    open_times = _utc_series(frame["open_time"])
    if open_times is None:
        return False
    matches = (open_times == response_open) & (open_times + BAR_INTERVAL <= decision_time)
    locations = np.flatnonzero(matches.to_numpy(dtype=bool))
    if len(locations) != 1:
        return False
    row = frame.iloc[int(locations[0])]
    try:
        open_price = float(row["open"])
        close_price = float(row["close"])
    except (TypeError, ValueError):
        return False
    return (
        math.isfinite(open_price)
        and math.isfinite(close_price)
        and open_price > 0.0
        and close_price > 0.0
    )


def _transform_symbol_bars(
    frame: pd.DataFrame,
    response_open: pd.Timestamp,
    decision_time: pd.Timestamp,
) -> _TransformedBars | None:
    if not {"open_time", "open", "close"}.issubset(frame.columns):
        return None
    open_times = _utc_series(frame["open_time"])
    if open_times is None:
        return None
    window_start = response_open - PRICE_LOOKBACK
    # Reapply the information boundary even though the canonical context is already truncated.
    if open_times.notna().all() and open_times.is_monotonic_increasing:
        left = int(open_times.searchsorted(window_start, side="left"))
        right = int(open_times.searchsorted(response_open, side="right"))
        selected_frame = frame.iloc[left:right]
        selected_times = pd.DatetimeIndex(open_times.iloc[left:right])
    else:
        mask = open_times.notna() & (open_times >= window_start) & (open_times <= response_open)
        selected_frame = frame.loc[mask]
        selected_times = pd.DatetimeIndex(open_times.loc[mask])
    completed = selected_times + BAR_INTERVAL <= decision_time
    selected_frame = selected_frame.iloc[np.flatnonzero(completed)]
    selected_times = selected_times[completed]
    if len(selected_times) == 0:
        return None
    if selected_times.duplicated().any():
        return None
    try:
        opens = selected_frame["open"].to_numpy(dtype=float, copy=False)
        closes = selected_frame["close"].to_numpy(dtype=float, copy=False)
    except (TypeError, ValueError):
        return None
    finite = np.isfinite(opens) & np.isfinite(closes) & (opens > 0.0) & (closes > 0.0)
    value_times = selected_times[finite]
    log_returns = np.log(closes[finite] / opens[finite])
    order = np.argsort(value_times.asi8, kind="stable")
    value_times = value_times[order]
    log_returns = log_returns[order]
    response_locations = np.flatnonzero(value_times == response_open)
    if len(response_locations) != 1:
        return None
    history_mask = (value_times < response_open) & (value_times + BAR_INTERVAL <= response_open)
    history_times = value_times[history_mask]
    history_values = log_returns[history_mask]
    if len(history_values) == 0:
        return None

    all_median = (
        float(np.median(history_values)) if len(history_values) >= PRICE_ALL_HOUR_MINIMUM else None
    )
    history_hours = history_times.hour
    baselines = np.full(len(history_values), np.nan, dtype=float)
    hour_baselines: dict[int, float] = {}
    for raw_hour in np.unique(history_hours):
        hour = int(raw_hour)
        hour_mask = history_hours == hour
        if int(hour_mask.sum()) >= PRICE_SAME_HOUR_MINIMUM:
            hour_baseline = float(np.median(history_values[hour_mask]))
        elif all_median is not None:
            hour_baseline = all_median
        else:
            continue
        hour_baselines[hour] = hour_baseline
        baselines[hour_mask] = hour_baseline
    response_baseline = hour_baselines.get(response_open.hour, all_median)
    if response_baseline is None:
        return None
    valid_baseline = np.isfinite(baselines)
    transformed_history = pd.Series(
        history_values[valid_baseline] - baselines[valid_baseline],
        index=history_times[valid_baseline],
        dtype=float,
    )
    if transformed_history.empty:
        return None
    response_value = float(log_returns[response_locations[0]] - response_baseline)
    if not math.isfinite(response_value):
        return None
    return _TransformedBars(history=transformed_history, response=response_value)


def _past_funding(
    funding: pd.DataFrame, eligible: tuple[str, ...], decision_time: pd.Timestamp
) -> pd.DataFrame | None:
    if not {"funding_time", "symbol", "funding_rate"}.issubset(funding.columns):
        return None
    funding_times = _utc_series(funding["funding_time"])
    if funding_times is None:
        return None
    # A matching tau is no more than 16h before t, so this slice still fully contains
    # [tau-180d, tau) while avoiding repeated scans over multi-year context history.
    search_start = decision_time - FUNDING_LOOKBACK - 2 * BAR_INTERVAL
    if funding_times.notna().all() and funding_times.is_monotonic_increasing:
        left = int(funding_times.searchsorted(search_start, side="left"))
        right = int(funding_times.searchsorted(decision_time, side="left"))
        selected = funding.iloc[left:right]
        selected_times = funding_times.iloc[left:right]
    else:
        time_mask = (
            funding_times.notna()
            & (funding_times >= search_start)
            & (funding_times < decision_time)
        )
        selected = funding.loc[time_mask]
        selected_times = funding_times.loc[time_mask]
    symbols = selected["symbol"].astype(str)
    eligible_mask = symbols.isin(eligible)
    past = pd.DataFrame(
        {
            "funding_time": selected_times.loc[eligible_mask],
            "symbol": symbols.loc[eligible_mask],
            "funding_rate": pd.to_numeric(
                selected.loc[eligible_mask, "funding_rate"], errors="coerce"
            ),
        }
    )
    return past.sort_values(["symbol", "funding_time"], kind="mergesort").reset_index(drop=True)


def _matched_funding_groups(
    funding: pd.DataFrame,
    eligible: tuple[str, ...],
    decision_time: pd.Timestamp,
    response_open: pd.Timestamp,
) -> dict[str, pd.DataFrame]:
    past = _past_funding(funding, eligible, decision_time)
    if past is None or past.empty:
        return {}
    matched: dict[str, pd.DataFrame] = {}
    for symbol, group in past.groupby("symbol", sort=True, observed=True):
        group = group.sort_values("funding_time", kind="mergesort")
        latest = group.iloc[-1]
        tau = pd.Timestamp(latest["funding_time"])
        settlement = tau.floor("h")
        # The frozen data contract allows only sub-second settlement jitter.
        if tau - settlement >= pd.Timedelta(seconds=1):
            continue
        next_grid = settlement.ceil("8h")
        if next_grid != response_open or next_grid + BAR_INTERVAL != decision_time:
            # Crucially, do not search backward: a newer unfinished event supersedes a match.
            continue
        matched[str(symbol)] = group
    return matched


def _latest_matched_funding_rates(
    funding: pd.DataFrame,
    eligible: tuple[str, ...],
    decision_time: pd.Timestamp,
    response_open: pd.Timestamp,
) -> dict[str, float]:
    rates: dict[str, float] = {}
    for symbol, group in _matched_funding_groups(
        funding, eligible, decision_time, response_open
    ).items():
        rate = float(group.iloc[-1]["funding_rate"])
        if math.isfinite(rate):
            rates[symbol] = rate
    return rates


def _funding_z_scores(
    funding: pd.DataFrame,
    eligible: tuple[str, ...],
    transformed: Mapping[str, _TransformedBars],
    decision_time: pd.Timestamp,
    response_open: pd.Timestamp,
) -> dict[str, float]:
    matched = _matched_funding_groups(funding, eligible, decision_time, response_open)
    return _funding_z_scores_from_groups(matched, transformed)


def _funding_z_scores_from_groups(
    matched: Mapping[str, pd.DataFrame],
    valid_response_symbols: Collection[str],
) -> dict[str, float]:
    scores: dict[str, float] = {}
    for symbol, group in matched.items():
        if symbol not in valid_response_symbols:
            continue
        funding_times = pd.DatetimeIndex(group["funding_time"])
        try:
            funding_rates = group["funding_rate"].to_numpy(dtype=float, copy=False)
        except (TypeError, ValueError):
            continue
        tau = funding_times[-1]
        funding_rate = float(funding_rates[-1])
        if not math.isfinite(funding_rate):
            continue
        history_mask = (
            (funding_times >= tau - FUNDING_LOOKBACK)
            & (funding_times < tau)
            & np.isfinite(funding_rates)
        )
        history_rates = funding_rates[history_mask]
        history_times = funding_times[history_mask]
        settlement_hour = tau.floor("h").hour
        same_hour = history_rates[history_times.floor("h").hour == settlement_hour]
        if len(same_hour) >= FUNDING_SAME_HOUR_MINIMUM:
            baseline = same_hour
        else:
            if len(history_rates) < FUNDING_ALL_HOUR_MINIMUM:
                continue
            baseline = history_rates
        median = float(np.median(baseline))
        scale = max(1.4826 * _mad(baseline), FUNDING_SCALE_FLOOR)
        z_value = float(np.clip((funding_rate - median) / scale, -SCORE_CLIP, SCORE_CLIP))
        if math.isfinite(z_value):
            scores[symbol] = z_value
    return scores


def _fallback_market(
    transformed: Mapping[str, _TransformedBars], response_open: pd.Timestamp
) -> tuple[pd.Series | None, float | None]:
    histories = pd.concat(
        {symbol: state.history for symbol, state in sorted(transformed.items())}, axis=1
    )
    counts = histories.count(axis=1)
    market_history = histories.median(axis=1, skipna=True)[
        counts >= FALLBACK_MARKET_MINIMUM
    ].sort_index()
    response_values = np.asarray(
        [state.response for _, state in sorted(transformed.items())], dtype=float
    )
    response_values = response_values[np.isfinite(response_values)]
    if len(response_values) < FALLBACK_MARKET_MINIMUM or market_history.empty:
        return None, None
    market_history = market_history.loc[market_history.index < response_open]
    return market_history.astype(float), float(np.median(response_values))


def _price_state(
    symbol: _TransformedBars,
    market_history: pd.Series,
    market_response: float,
    response_open: pd.Timestamp,
) -> _PriceState | None:
    symbol_index = symbol.history.index
    market_index = market_history.index
    if symbol_index.equals(market_index):
        paired_times = symbol_index
        symbol_values = symbol.history.to_numpy(dtype=float, copy=False)
        market_values = market_history.to_numpy(dtype=float, copy=False)
    else:
        paired_times = symbol_index.intersection(market_index, sort=True)
        symbol_locations = symbol_index.get_indexer(paired_times)
        market_locations = market_index.get_indexer(paired_times)
        symbol_values = symbol.history.to_numpy(dtype=float, copy=False)[symbol_locations]
        market_values = market_history.to_numpy(dtype=float, copy=False)[market_locations]
    finite = (
        (paired_times < response_open) & np.isfinite(symbol_values) & np.isfinite(market_values)
    )
    symbol_values = symbol_values[finite][-BETA_OBSERVATIONS:]
    market_values = market_values[finite][-BETA_OBSERVATIONS:]
    if len(symbol_values) < BETA_MINIMUM:
        return None
    market_centered = market_values - float(np.mean(market_values))
    market_variance = float(np.mean(market_centered * market_centered))
    if not math.isfinite(market_variance) or market_variance < 1e-8:
        return None
    symbol_centered = symbol_values - float(np.mean(symbol_values))
    covariance = float(np.mean(symbol_centered * market_centered))
    beta = float(np.clip(covariance / market_variance, -BETA_CLIP, BETA_CLIP))

    residuals = symbol_values - beta * market_values
    residual_window = residuals[-RESIDUAL_OBSERVATIONS:]
    if len(residual_window) < RESIDUAL_MINIMUM:
        return None
    residual_scale = max(1.4826 * _mad(residual_window), RESIDUAL_SCALE_FLOOR)
    response_residual = float(symbol.response - beta * market_response)
    if not all(math.isfinite(value) for value in (beta, residual_scale, response_residual)):
        return None
    return _PriceState(
        beta=beta,
        response_residual=response_residual,
        residual_scale=residual_scale,
    )


def _select_pairs(active: Mapping[str, tuple[int, float, float]]) -> list[tuple[str, str]]:
    longs = sorted(symbol for symbol, (direction, _, _) in active.items() if direction > 0)
    shorts = sorted(symbol for symbol, (direction, _, _) in active.items() if direction < 0)
    candidates: list[tuple[float, float, str, str]] = []
    for long_symbol in longs:
        _, long_strength, long_beta = active[long_symbol]
        for short_symbol in shorts:
            _, short_strength, short_beta = active[short_symbol]
            beta_gap = abs(long_beta - short_beta)
            if beta_gap <= BETA_GAP_LIMIT:
                score = min(long_strength, short_strength) / (1.0 + beta_gap)
                candidates.append((-score, beta_gap, long_symbol, short_symbol))
    candidates.sort()
    used: set[str] = set()
    selected: list[tuple[str, str]] = []
    for _, _, long_symbol, short_symbol in candidates:
        if long_symbol in used or short_symbol in used:
            continue
        selected.append((long_symbol, short_symbol))
        used.update((long_symbol, short_symbol))
        if len(selected) == MAX_PAIRS:
            break
    return selected
