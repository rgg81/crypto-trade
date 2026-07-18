"""Team 10: causal three-slot residual response model.

The model estimates how an asset's market-residual return in one completed
eight-hour bar predicts its residual return in the next bar.  The response
slope for the UTC slot that starts at the decision time is shrunk toward a
fixed blend of the asset's pooled slope and a robust cross-coin slot prior,
then applied to the latest completed residual move.  Both forecast sleeves
must clear their declared share of round-trip costs.  All observations are
strictly earlier than the decision timestamp.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import numpy as np
import pandas as pd

from crypto_trade.tournament.protocol import DecisionContext, TargetStrategy


@dataclass(frozen=True)
class StrategyParameters:
    bar_hours: int = 8
    utc_slots: tuple[int, ...] = (0, 8, 16)
    reference_weeks: int = 26
    lookback_return_bars: int = 26 * 7 * 3
    minimum_symbols: int = 20
    minimum_pooled_pairs: int = 300
    minimum_slot_pairs: int = 80
    minimum_slot_pool_symbols: int = 20
    shrinkage_prior_observations: int = 104
    asset_pooled_prior_weight: float = 0.50
    slope_clip: float = 0.75
    selection_fraction: float = 0.25
    minimum_positions_per_side: int = 8
    gross_per_side: float = 0.20
    maximum_symbol_weight: float = 0.03
    maximum_absolute_net: float = 0.05
    fee_bps_per_side: float = 5.0
    slippage_bps_per_side: float = 2.5
    round_trip_cost_multiple: float = 1.0


PARAMETERS = StrategyParameters()


def _normalise_timestamp(value: object) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _is_decision_boundary(decision_time: pd.Timestamp, params: StrategyParameters) -> bool:
    return (
        decision_time.hour in params.utc_slots
        and decision_time.minute == 0
        and decision_time.second == 0
        and decision_time.microsecond == 0
    )


def _completed_close_history(
    frame: pd.DataFrame,
    decision_time: pd.Timestamp,
    params: StrategyParameters,
) -> pd.Series | None:
    """Return an exact, contiguous close history ending one bar before decision."""

    if not {"open_time", "close"}.issubset(frame.columns):
        return None

    local = frame.loc[:, ["open_time", "close"]].copy()
    local["open_time"] = pd.to_datetime(local["open_time"], utc=True, errors="coerce")
    local["close"] = pd.to_numeric(local["close"], errors="coerce")
    local = local.dropna(subset=["open_time", "close"])
    local = local.loc[
        (local["open_time"] + pd.Timedelta(hours=params.bar_hours) <= decision_time)
        & np.isfinite(local["close"])
        & (local["close"] > 0.0)
    ]
    if local.empty:
        return None

    # A repeated timestamp is ambiguous and must not be resolved using row order.
    if local["open_time"].duplicated(keep=False).any():
        return None

    required_closes = params.lookback_return_bars + 2
    expected_end = decision_time - pd.Timedelta(hours=params.bar_hours)
    expected_index = pd.date_range(
        end=expected_end,
        periods=required_closes,
        freq=pd.Timedelta(hours=params.bar_hours),
        tz="UTC",
    )
    close = local.set_index("open_time")["close"].reindex(expected_index)
    if close.isna().any() or not np.isfinite(close.to_numpy(dtype=float)).all():
        return None
    return close.astype(float)


def _residual_return_frame(
    context: DecisionContext,
    decision_time: pd.Timestamp,
    params: StrategyParameters = PARAMETERS,
) -> pd.DataFrame:
    """Build synchronous residual returns for the exact eligible universe."""

    returns: dict[str, pd.Series] = {}
    for symbol in sorted(set(context.eligible_symbols)):
        frame = context.bars.get(symbol)
        if frame is None:
            continue
        close = _completed_close_history(frame, decision_time, params)
        if close is None:
            continue
        values = np.diff(np.log(close.to_numpy(dtype=float)))
        returns[symbol] = pd.Series(values, index=close.index[1:], dtype=float)

    if len(returns) < params.minimum_symbols:
        return pd.DataFrame(dtype=float)

    return_frame = pd.DataFrame(returns).sort_index(axis=1)
    if return_frame.isna().any().any():
        return pd.DataFrame(dtype=float)

    market_move = return_frame.median(axis=1)
    residual = return_frame.sub(market_move, axis=0)
    expected_latest = decision_time - pd.Timedelta(hours=params.bar_hours)
    if residual.empty or residual.index[-1] != expected_latest:
        return pd.DataFrame(dtype=float)
    return residual


def _linear_response_slope(lag: pd.Series, response: pd.Series) -> float | None:
    x = lag.to_numpy(dtype=float)
    y = response.to_numpy(dtype=float)
    finite = np.isfinite(x) & np.isfinite(y)
    x = x[finite]
    y = y[finite]
    if x.size < 2:
        return None

    x_centered = x - float(np.mean(x))
    y_centered = y - float(np.mean(y))
    denominator = float(np.dot(x_centered, x_centered))
    if denominator <= 1.0e-14:
        return None
    return float(np.dot(x_centered, y_centered) / denominator)


def _response_slope_components(
    residual_returns: pd.Series,
    target_slot: int,
    decision_time: pd.Timestamp,
    params: StrategyParameters = PARAMETERS,
) -> tuple[float, float, int] | None:
    """Return clipped asset-pooled/slot slopes and the target-slot count."""

    history = residual_returns.loc[residual_returns.index < decision_time].tail(
        params.lookback_return_bars + 1
    )
    pairs = pd.DataFrame(
        {
            "lag": history.shift(1),
            "response": history,
        }
    ).dropna()
    if len(pairs) < params.minimum_pooled_pairs:
        return None

    pooled = _linear_response_slope(pairs["lag"], pairs["response"])
    slot_pairs = pairs.loc[pairs.index.hour == target_slot]
    if pooled is None or len(slot_pairs) < params.minimum_slot_pairs:
        return None
    slot = _linear_response_slope(slot_pairs["lag"], slot_pairs["response"])
    if slot is None:
        return None

    return (
        float(np.clip(pooled, -params.slope_clip, params.slope_clip)),
        float(np.clip(slot, -params.slope_clip, params.slope_clip)),
        len(slot_pairs),
    )


def _robust_cross_coin_slot_prior(
    residual_returns: pd.DataFrame,
    target_slot: int,
    decision_time: pd.Timestamp,
    params: StrategyParameters = PARAMETERS,
) -> float | None:
    """Equal-coin median of causal target-slot slopes; no coin dominates by volatility."""

    slopes: list[float] = []
    for symbol in sorted(residual_returns.columns):
        components = _response_slope_components(
            residual_returns[symbol],
            target_slot,
            decision_time,
            params,
        )
        if components is not None:
            slopes.append(components[1])
    if len(slopes) < params.minimum_slot_pool_symbols:
        return None
    prior = float(np.median(np.asarray(slopes, dtype=float)))
    if not np.isfinite(prior):
        return None
    return float(np.clip(prior, -params.slope_clip, params.slope_clip))


def _shrunk_response_slope(
    residual_returns: pd.Series,
    target_slot: int,
    decision_time: pd.Timestamp,
    params: StrategyParameters = PARAMETERS,
    *,
    cross_coin_slot_prior: float | None = None,
) -> float | None:
    """Estimate a target-slot lag/response slope using completed pairs only."""

    components = _response_slope_components(
        residual_returns,
        target_slot,
        decision_time,
        params,
    )
    if components is None:
        return None
    pooled, slot, slot_observations = components
    if cross_coin_slot_prior is None:
        prior = pooled
    else:
        prior = (
            params.asset_pooled_prior_weight * pooled
            + (1.0 - params.asset_pooled_prior_weight) * cross_coin_slot_prior
        )
    weight = slot_observations / (
        slot_observations + params.shrinkage_prior_observations
    )
    shrunk = weight * slot + (1.0 - weight) * prior
    return float(np.clip(shrunk, -params.slope_clip, params.slope_clip))


def _response_scores(
    residual_returns: pd.DataFrame,
    decision_time: pd.Timestamp,
    params: StrategyParameters = PARAMETERS,
) -> dict[str, float]:
    if residual_returns.empty:
        return {}

    expected_latest = decision_time - pd.Timedelta(hours=params.bar_hours)
    if residual_returns.index[-1] != expected_latest:
        return {}

    slot_prior = _robust_cross_coin_slot_prior(
        residual_returns,
        decision_time.hour,
        decision_time,
        params,
    )
    if slot_prior is None:
        return {}

    scores: dict[str, float] = {}
    for symbol in sorted(residual_returns.columns):
        series = residual_returns[symbol]
        slope = _shrunk_response_slope(
            series,
            decision_time.hour,
            decision_time,
            params,
            cross_coin_slot_prior=slot_prior,
        )
        latest_move = float(series.iloc[-1])
        if slope is None or not np.isfinite(latest_move):
            continue
        score = slope * latest_move
        if np.isfinite(score):
            scores[symbol] = float(score)
    return scores


def _neutral_portfolio(
    scores: Mapping[str, float],
    params: StrategyParameters = PARAMETERS,
) -> dict[str, float]:
    clean = {
        str(symbol): float(score)
        for symbol, score in scores.items()
        if np.isfinite(float(score))
    }
    if len(clean) < params.minimum_symbols:
        return {}

    ordered = sorted(clean.items(), key=lambda item: (item[1], item[0]))
    desired_side_count = max(
        params.minimum_positions_per_side,
        int(np.floor(params.selection_fraction * len(ordered))),
    )

    # Every admitted coin must forecast its own complete enter/exit cost.  For equal-gross
    # sleeves this also makes the long-minus-short spread clear twice that per-coin cost.
    round_trip_cost = (
        2.0
        * (params.fee_bps_per_side + params.slippage_bps_per_side)
        * 1.0e-4
        * params.round_trip_cost_multiple
    )
    directional_hurdle = round_trip_cost
    short_candidates = [
        symbol for symbol, score in ordered if score <= -directional_hurdle
    ]
    long_candidates = [
        symbol for symbol, score in reversed(ordered) if score >= directional_hurdle
    ]
    side_count = min(
        desired_side_count,
        len(ordered) // 2,
        len(short_candidates),
        len(long_candidates),
    )
    if side_count < params.minimum_positions_per_side:
        return {}

    short_symbols = short_candidates[:side_count]
    long_symbols = long_candidates[:side_count]
    average_short_forecast = float(np.mean([clean[s] for s in short_symbols]))
    average_long_forecast = float(np.mean([clean[s] for s in long_symbols]))
    if average_long_forecast - average_short_forecast < 2.0 * round_trip_cost:
        return {}

    side_weight = params.gross_per_side / side_count
    if side_weight > params.maximum_symbol_weight + 1.0e-12:
        return {}

    target = {symbol: -side_weight for symbol in short_symbols}
    target.update({symbol: side_weight for symbol in long_symbols})
    gross = sum(abs(weight) for weight in target.values())
    net = sum(target.values())
    if gross > 0.50 + 1.0e-12 or abs(net) > params.maximum_absolute_net + 1.0e-12:
        return {}
    return {symbol: target[symbol] for symbol in sorted(target)}


class Strategy(TargetStrategy):
    """Causal residual-response strategy for the three eight-hour UTC slots."""

    def target_weights(
        self, context: DecisionContext, *, seed: int
    ) -> dict[str, float] | None:
        del seed  # The estimator and all tie-breaking are deterministic.
        decision_time = _normalise_timestamp(context.decision_time)
        if not _is_decision_boundary(decision_time, PARAMETERS):
            return None

        residual = _residual_return_frame(context, decision_time, PARAMETERS)
        scores = _response_scores(residual, decision_time, PARAMETERS)
        return _neutral_portfolio(scores, PARAMETERS)


def build_strategy() -> Strategy:
    return Strategy()
