"""Funding/price disagreement repair baseline for Team 02."""

from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np
import pandas as pd


FORMATION_DAYS = 21
FUNDING_LOOKBACK_DAYS = 14
MINIMUM_FUNDING_OBSERVATIONS = 21
MINIMUM_ABSOLUTE_LOG_RETURN = 0.03
RETURN_SATURATION_SCALE = 0.12
MINIMUM_FUNDING_SCALE = 1.0e-6
MINIMUM_FUNDING_STRENGTH = 0.50
MINIMUM_NAMES_PER_SIDE = 2
MAXIMUM_NAMES_PER_SIDE = 3
TARGET_GROSS_EXPOSURE = 1.0


def _as_utc(value) -> pd.Timestamp:
    timestamp = pd.Timestamp(value)
    if timestamp.tzinfo is None:
        return timestamp.tz_localize("UTC")
    return timestamp.tz_convert("UTC")


def _completed_closes(frame: pd.DataFrame, decision_time: pd.Timestamp) -> pd.Series:
    """Return a time-indexed copy containing bars complete by the boundary."""
    if not isinstance(frame, pd.DataFrame) or not {"open_time", "close"}.issubset(frame.columns):
        return pd.Series(dtype=float)

    times = pd.to_datetime(frame["open_time"], utc=True, errors="coerce")
    closes = pd.to_numeric(frame["close"], errors="coerce")
    complete_by = decision_time - pd.Timedelta(hours=8)
    valid = times.notna() & closes.notna() & (closes > 0.0) & (times <= complete_by)
    if not bool(valid.any()):
        return pd.Series(dtype=float)

    result = pd.Series(
        closes.loc[valid].to_numpy(dtype=float, copy=True),
        index=pd.DatetimeIndex(times.loc[valid]),
        dtype=float,
    )
    return result.loc[~result.index.duplicated(keep="last")].sort_index()


def _price_displacement(frame: pd.DataFrame, decision_time: pd.Timestamp) -> float | None:
    closes = _completed_closes(frame, decision_time)
    if closes.empty:
        return None

    latest_time = closes.index[-1]
    formation_boundary = latest_time - pd.Timedelta(days=FORMATION_DAYS)
    anchors = closes.loc[closes.index <= formation_boundary]
    if anchors.empty:
        return None

    displacement = math.log(float(closes.iloc[-1]) / float(anchors.iloc[-1]))
    return displacement if math.isfinite(displacement) else None


def _funding_frame(funding, symbol: str) -> pd.DataFrame | None:
    """Accept either per-symbol frames or one frame carrying a symbol column."""
    if isinstance(funding, Mapping):
        frame = funding.get(symbol)
        return frame if isinstance(frame, pd.DataFrame) else None
    if not isinstance(funding, pd.DataFrame):
        return None

    symbol_column = next(
        (name for name in ("symbol", "contract", "ticker") if name in funding.columns),
        None,
    )
    if symbol_column is None:
        return None
    return funding.loc[funding[symbol_column].astype(str) == symbol]


def _mean_lagged_funding(funding, symbol: str, decision_time: pd.Timestamp) -> float | None:
    frame = _funding_frame(funding, symbol)
    if frame is None or frame.empty:
        return None

    time_column = next(
        (
            name
            for name in ("funding_time", "settled_time", "time", "timestamp")
            if name in frame.columns
        ),
        None,
    )
    rate_column = next(
        (name for name in ("funding_rate", "rate", "fundingRate") if name in frame.columns),
        None,
    )
    if time_column is None or rate_column is None:
        return None

    times = pd.to_datetime(frame[time_column], utc=True, errors="coerce")
    rates = pd.to_numeric(frame[rate_column], errors="coerce")
    start = decision_time - pd.Timedelta(days=FUNDING_LOOKBACK_DAYS)
    valid = times.notna() & rates.notna() & (times >= start) & (times < decision_time)
    clean = rates.loc[valid].astype(float)
    if len(clean) < MINIMUM_FUNDING_OBSERVATIONS:
        return None

    pressure = float(clean.mean())
    return pressure if math.isfinite(pressure) else None


class FundingPriceDislocationRepair:
    """Fade price displacement only when lagged funding points the other way."""

    def target_weights(self, context, *, seed: int) -> Mapping[str, float] | None:
        del seed  # The rule is deterministic and needs no random tie-breaking.
        decision_time = _as_utc(context.decision_time)

        # Weekly formation minimizes churn and aligns with the universe boundary.
        if not (
            decision_time.weekday() == 0
            and decision_time.hour == 0
            and decision_time.minute == 0
        ):
            return None

        observations: dict[str, tuple[float, float]] = {}
        for symbol in sorted(str(item) for item in context.eligible_symbols):
            bars = context.bars.get(symbol)
            displacement = _price_displacement(bars, decision_time)
            pressure = _mean_lagged_funding(context.funding, symbol, decision_time)
            if displacement is None or pressure is None:
                continue
            observations[symbol] = (displacement, pressure)

        if not observations:
            return {}

        funding_scale = max(
            float(np.median([abs(item[1]) for item in observations.values()])),
            MINIMUM_FUNDING_SCALE,
        )

        scores: dict[str, float] = {}
        for symbol, (displacement, pressure) in observations.items():
            funding_strength = abs(pressure) / funding_scale
            disagreement = displacement * pressure < 0.0
            if (
                not disagreement
                or abs(displacement) < MINIMUM_ABSOLUTE_LOG_RETURN
                or funding_strength < MINIMUM_FUNDING_STRENGTH
            ):
                continue

            bounded_return = math.tanh(abs(displacement) / RETURN_SATURATION_SCALE)
            bounded_funding = math.tanh(funding_strength)
            scores[symbol] = -math.copysign(
                bounded_return * bounded_funding,
                displacement,
            )

        longs = sorted(
            ((symbol, score) for symbol, score in scores.items() if score > 0.0),
            key=lambda item: (-item[1], item[0]),
        )[:MAXIMUM_NAMES_PER_SIDE]
        shorts = sorted(
            ((symbol, score) for symbol, score in scores.items() if score < 0.0),
            key=lambda item: (item[1], item[0]),
        )[:MAXIMUM_NAMES_PER_SIDE]

        # A complete two-sided state is required; otherwise the strategy is flat.
        if len(longs) < MINIMUM_NAMES_PER_SIDE or len(shorts) < MINIMUM_NAMES_PER_SIDE:
            return {}

        side_gross = TARGET_GROSS_EXPOSURE / 2.0
        long_weight = side_gross / len(longs)
        short_weight = -side_gross / len(shorts)
        weights = {symbol: long_weight for symbol, _ in longs}
        weights.update({symbol: short_weight for symbol, _ in shorts})
        return weights


def build_strategy() -> FundingPriceDislocationRepair:
    return FundingPriceDislocationRepair()
