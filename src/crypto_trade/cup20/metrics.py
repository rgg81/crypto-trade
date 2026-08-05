"""Deterministic window metrics, chronological folds and concentration diagnostics."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.engine_v2 import EvaluationResult

DAYS_PER_YEAR = 365.0
Fold = tuple[str, pd.Timestamp, pd.Timestamp]

# Every metric this module reports MUST be finite. These values are ranked, compared against hard
# floors, and serialised into a hash-chained release artifact, and none of those three consumers
# handles an infinity correctly: the ranking clamp would score a perfect drawdown profile at zero,
# and json.dumps would emit the non-standard "Infinity" token into a published, hashed packet.
UNDEFINED_CALMAR = 1_000.0  # drawdown is zero and return positive: unbounded, reported as capped
UNDEFINED_COST_SHARE = 1.0  # no positive gross PnL at all: reported as costs consuming everything


@dataclasses.dataclass(frozen=True, slots=True)
class WindowMetrics:
    net_sharpe: float
    annualized_return: float
    annualized_volatility: float
    max_drawdown: float
    calmar: float
    positive_quarter_fraction: float
    annualized_turnover: float
    gross_edge_bps_per_turnover: float
    cost_share_of_positive_gross: float
    top5_day_share: float
    long_gross_pnl: float
    short_gross_pnl: float
    trade_count: int

    def as_dict(self) -> dict[str, float]:
        return {field.name: getattr(self, field.name) for field in dataclasses.fields(self)}


def daily_returns(result: EvaluationResult) -> pd.Series:
    """Compound bar net returns within each UTC calendar day."""
    if result.returns.empty:
        return pd.Series(dtype=float)
    net = result.returns["net_return"].astype(float)
    index = pd.DatetimeIndex(net.index).tz_convert("UTC")
    grouped = (1.0 + net).groupby(index.normalize()).prod() - 1.0
    grouped.index = pd.DatetimeIndex(grouped.index)
    return grouped.sort_index()


# is_folds keeps F2-F4 as fixed 12-month blocks anchored to is_end; only F1 may absorb a
# shortfall. A window at or below this floor would force F1 to zero width, producing a fold that
# can never be positive (sharpe() of an empty slice is 0.0) and permanently capping
# positive_fold_count two folds below the true count regardless of strategy quality.
MINIMUM_IS_WINDOW = pd.DateOffset(years=3)


def is_folds(is_start: pd.Timestamp, is_end: pd.Timestamp) -> tuple[Fold, ...]:
    """Four 12-month blocks anchored backward from the IS cutoff; F1 absorbs any shortfall."""
    start = pd.Timestamp(is_start).tz_convert("UTC")
    end = pd.Timestamp(is_end).tz_convert("UTC")
    if start >= end - MINIMUM_IS_WINDOW:
        raise ValueError(
            f"IS window is only {end - start} (from {start} to {end}); is_folds requires "
            f"strictly more than {MINIMUM_IS_WINDOW} so F1 keeps positive width on top of the "
            "fixed 3-year F2-F4 block"
        )
    interior = [end - pd.DateOffset(years=years) for years in (3, 2, 1)]
    bounds = [start, *(max(edge, start) for edge in interior), end]
    return tuple(
        (f"F{index + 1}", bounds[index], bounds[index + 1]) for index in range(len(bounds) - 1)
    )


# holdout_folds keeps H1-H3 as fixed 6-month blocks from start; only H4 may absorb a shortfall
# against the true end. A window at or below this floor would force H4 to zero width or invert it
# (start after end), corrupting the reported fold boundaries.
MINIMUM_HOLDOUT_WINDOW = pd.DateOffset(months=18)


def holdout_folds(start: pd.Timestamp, end: pd.Timestamp) -> tuple[Fold, ...]:
    """Four 6-month blocks across the sealed window."""
    start = pd.Timestamp(start).tz_convert("UTC")
    end = pd.Timestamp(end).tz_convert("UTC")
    if end <= start + MINIMUM_HOLDOUT_WINDOW:
        raise ValueError(
            f"holdout window is only {end - start} (from {start} to {end}); holdout_folds "
            f"requires strictly more than {MINIMUM_HOLDOUT_WINDOW} so H4 keeps positive width"
        )
    edges = [start + pd.DateOffset(months=6 * step) for step in range(5)]
    edges[-1] = end
    return tuple((f"H{index + 1}", edges[index], edges[index + 1]) for index in range(4))


def sharpe(series: pd.Series) -> float:
    """Annualised Sharpe of a daily return series; zero variance yields zero, never NaN."""
    values = series.dropna().to_numpy(dtype=float)
    if values.size < 2:
        return 0.0
    deviation = float(np.std(values, ddof=1))
    if deviation <= 0.0:
        return 0.0
    return float(np.mean(values)) / deviation * math.sqrt(DAYS_PER_YEAR)


def max_drawdown(series: pd.Series) -> float:
    """Maximum peak-to-trough decline of the compounded curve, as a non-negative magnitude.

    Compounded equity reaching zero or below is total ruin, reported as the 1.0 (100%) ceiling
    rather than through the peak-to-trough ratio: at equity == 0 the ratio is a 0/0 division
    (NaN); at equity < 0 it is arithmetically defined but dishonest, since a negative running
    peak inverts the ratio's sign and can report a SMALLER number than an ordinary drawdown (a
    book that lost more than everything must never score better than one that merely lost a lot).
    Ruin is checked before any division runs, so this never raises a RuntimeWarning either.
    """
    values = series.dropna().to_numpy(dtype=float)
    if values.size == 0:
        return 0.0
    equity = np.cumprod(1.0 + values)
    if np.any(equity <= 0.0):
        return 1.0
    peaks = np.maximum.accumulate(equity)
    return float(np.max(1.0 - equity / peaks))


def window_metrics(result: EvaluationResult) -> WindowMetrics:
    """Every scalar the floors and the ranking score consume."""
    daily = daily_returns(result)
    frame = result.returns
    days = max(len(daily), 1)
    years = days / DAYS_PER_YEAR

    total_growth = float(np.prod(1.0 + daily.to_numpy(dtype=float))) if len(daily) else 1.0
    annualized_return = total_growth ** (1.0 / years) - 1.0 if total_growth > 0 else -1.0
    drawdown = max_drawdown(daily)
    if drawdown <= 0.0:
        calmar = UNDEFINED_CALMAR if annualized_return > 0.0 else 0.0
    else:
        calmar = annualized_return / drawdown

    naive_index = pd.DatetimeIndex(daily.index).tz_convert("UTC").tz_localize(None)
    quarters = (1.0 + daily).groupby(naive_index.to_period("Q")).prod() - 1.0
    positive_quarter_fraction = (
        float((quarters > 0.0).sum()) / len(quarters) if len(quarters) else 0.0
    )

    gross_bar = frame["price_pnl"].astype(float) + frame["funding_pnl"].astype(float)
    total_turnover = float(frame["turnover"].astype(float).sum())
    gross_total = float(gross_bar.sum())
    positive_gross = float(gross_bar.clip(lower=0.0).sum())
    costs = float(frame["fees"].astype(float).sum() + frame["slippage"].astype(float).sum())

    absolute_daily = daily.abs()
    top5 = float(absolute_daily.nlargest(5).sum())
    absolute_total = float(absolute_daily.sum())

    if result.events.empty or "notional" not in result.events.columns:
        trade_count = 0
    else:
        notional = result.events["notional"].fillna(0.0).astype(float)
        types = result.events.get("event_type", pd.Series("trade", index=result.events.index))
        trade_count = int(((notional.abs() > 0.0) & (types != "funding")).sum())

    return WindowMetrics(
        net_sharpe=sharpe(daily),
        annualized_return=annualized_return,
        annualized_volatility=(
            float(np.std(daily.to_numpy(dtype=float), ddof=1)) * math.sqrt(DAYS_PER_YEAR)
            if len(daily) > 1
            else 0.0
        ),
        max_drawdown=drawdown,
        calmar=calmar,
        positive_quarter_fraction=positive_quarter_fraction,
        annualized_turnover=total_turnover / years if years > 0 else 0.0,
        gross_edge_bps_per_turnover=(
            gross_total / total_turnover * 10_000.0 if total_turnover > 0 else 0.0
        ),
        cost_share_of_positive_gross=(
            costs / positive_gross if positive_gross > 0 else UNDEFINED_COST_SHARE
        ),
        top5_day_share=(top5 / absolute_total if absolute_total > 0 else 0.0),
        long_gross_pnl=float(
            frame["long_price_pnl"].astype(float).sum()
            + frame["long_funding_pnl"].astype(float).sum()
        ),
        short_gross_pnl=float(
            frame["short_price_pnl"].astype(float).sum()
            + frame["short_funding_pnl"].astype(float).sum()
        ),
        trade_count=trade_count,
    )


def fold_sharpes(result: EvaluationResult, folds: Sequence[Fold]) -> dict[str, float]:
    """Annualised Sharpe within every named fold."""
    daily = daily_returns(result)
    return {
        name: sharpe(daily[(daily.index >= start) & (daily.index < end)])
        for name, start, end in folds
    }


def fold_positive_pnl_shares(result: EvaluationResult, folds: Sequence[Fold]) -> dict[str, float]:
    """Share of total positive arithmetic daily PnL contributed by each fold."""
    daily = daily_returns(result)
    positive = daily.clip(lower=0.0)
    total = float(positive.sum())
    if total <= 0.0:
        return {name: 0.0 for name, _, _ in folds}
    return {
        name: float(positive[(positive.index >= start) & (positive.index < end)].sum()) / total
        for name, start, end in folds
    }
