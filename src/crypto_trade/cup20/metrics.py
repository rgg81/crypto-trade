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

# The charter defines a trade as "one non-zero executed symbol/boundary fill after evaluator
# netting", and `trade_count` gates a hard floor of 500. So this is an ALLOWLIST of the event types
# that ARE a fill, enumerated by reading every event-emitting site in
# `crypto_trade.tournament.engine_v2`, not a denylist of the ones that are not. The nine event types
# the evaluator emits, and why each is in or out:
#
#   trade                    IN   the ordinary rebalance fill
#   risk_reduction           IN   a real execution: the central exposure-cap pass trims a position
#                                 at the bar open, and pays fee and slippage for it
#   forced_exit              IN   a real execution: delisting or terminal liquidation at the last
#                                 executable price, likewise paying fee and slippage
#   risk_policy_action       IN   a real execution: the declared risk policy's own stop-out, timeout
#                                 or gross-scale fill, with quantity, price, notional, fee and
#                                 slippage all populated from policy_filled_notional
#   mark_to_market           OUT  bookkeeping. Emitted once per HELD symbol per bar with a non-zero
#                                 notional, so it counts position-bars, not executions
#   funding                  OUT  a funding settlement, not an order
#   risk_policy_block        OUT  an order the policy REFUSED; nothing was executed
#   conservative_settlement  OUT  a 100% haircut written off against a delisting residual that could
#                                 not be traded out of; zero fee, zero slippage, no counterparty
#   unresolved_residual      OUT  a terminal position that could not be exited at all
#
# A denylist is what produced the defect being fixed here: `event_type != "funding"` counted every
# mark_to_market row, so on the organiser's own battery fixture the count read 7,904 against 3,472
# real fills, and over the real in-sample window mark-to-market alone yields roughly 87,000 against
# a floor of 500 -- any continuously-invested book cleared the floor about 170x over no matter how
# rarely it actually traded. An allowlist also fails in the safe direction as the evaluator grows: a
# new bookkeeping event type is excluded until someone deliberately adds it here.
EXECUTED_EVENT_TYPES: frozenset[str] = frozenset(
    {"trade", "risk_reduction", "forced_exit", "risk_policy_action"}
)


@dataclasses.dataclass(frozen=True, slots=True)
class WindowMetrics:
    net_sharpe: float
    annualized_return: float
    annualized_volatility: float
    max_drawdown: float
    calmar: float
    positive_quarter_fraction: float
    # The COUNT behind the fraction, reported alongside it because charter section 8 states its
    # holdout floor as "at least 5 of 8 quarters positive" -- a count, not a ratio. Deriving the
    # count from the fraction would need the denominator, and the only honest denominator is the
    # number of calendar quarters this book actually produced returns in. A caller assuming eight
    # (the sealed window's nominal length) would silently mis-gate a book that traded in seven.
    positive_quarter_count: int
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

    The curve is anchored at the initial capital (1.0) BEFORE any return has occurred, not just
    at the first post-return equity value. Without that anchor, a drawdown whose peak IS the
    starting capital (the very first return is already negative) is measured against a peak that
    already reflects that loss, understating it -- e.g. returns [-0.30, +0.50, -0.10] have a true
    peak-to-trough of 0.30 (from inception), not 0.10 (from the post-first-return high of 0.70).
    A drawdown whose peak is reached mid-series is unaffected by this anchor either way.

    Compounded equity reaching zero or below is total ruin, reported as the 1.0 (100%) ceiling
    rather than through the peak-to-trough ratio: at equity == 0 the ratio is a 0/0 division
    (NaN); at equity < 0 it is arithmetically defined but dishonest, since a negative running
    peak inverts the ratio's sign and can report a SMALLER number than an ordinary drawdown (a
    book that lost more than everything must never score better than one that merely lost a lot).
    Ruin is checked before any division runs, so this never raises a RuntimeWarning either. (The
    inception anchor alone would already keep the running peak at or above 1.0 for the exact-
    ruin case, avoiding the 0/0 division; it does NOT avoid the negative-equity case, where the
    ratio is well-defined but wrong, so the explicit ruin check stays regardless.)
    """
    values = series.dropna().to_numpy(dtype=float)
    if values.size == 0:
        return 0.0
    equity = np.concatenate(([1.0], np.cumprod(1.0 + values)))
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
    positive_quarters = int((quarters > 0.0).sum())
    positive_quarter_fraction = positive_quarters / len(quarters) if len(quarters) else 0.0

    gross_bar = frame["price_pnl"].astype(float) + frame["funding_pnl"].astype(float)
    total_turnover = float(frame["turnover"].astype(float).sum())
    gross_total = float(gross_bar.sum())
    positive_gross = float(gross_bar.clip(lower=0.0).sum())
    costs = float(frame["fees"].astype(float).sum() + frame["slippage"].astype(float).sum())

    absolute_daily = daily.abs()
    top5 = float(absolute_daily.nlargest(5).sum())
    absolute_total = float(absolute_daily.sum())

    # A missing `event_type` column counts ZERO, not everything. Without it there is no way to tell
    # a fill from a mark-to-market row, and this number gates a hard floor -- the unknown case must
    # fail the floor rather than clear it. The evaluator always emits the column alongside
    # `notional`; the two are written by the same dict literals.
    columns = result.events.columns
    if result.events.empty or "notional" not in columns or "event_type" not in columns:
        trade_count = 0
    else:
        notional = result.events["notional"].fillna(0.0).astype(float)
        executed = result.events["event_type"].isin(EXECUTED_EVENT_TYPES)
        trade_count = int(((notional.abs() > 0.0) & executed).sum())

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
        positive_quarter_count=positive_quarters,
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
