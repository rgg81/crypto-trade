"""Turning an evaluation into the two metric views and the gate evidence.

The sealed design rests on one property: **a team's feedback packet must be a function of visible
days only.** The evaluator runs the whole development window continuously, because carried
positions, funding accrual and forced exits are path-dependent and cannot be skipped. The split is
therefore an operation on the scoring index, and the risk is that it is done in one place and
forgotten in another.

Two things guard against that. The visible and sealed summaries take *disjoint index arguments* and
neither can see the other's rows, so a packet cannot accidentally include a sealed day. And
``test_v5_metrics`` perturbs sealed-block returns arbitrarily and asserts the team packet's bytes do
not move -- a filter can be forgotten once, but that test fails the moment it is.

Everything a gate reads is computed here rather than declared, so a candidate fails on its own
numbers.
"""

from __future__ import annotations

import dataclasses
import json
import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.v5 import statistics as stats
from crypto_trade.tournament.v5.gates import SEALED_TRIAL_COUNT, SelectionEvidence

ANNUALISATION_DAYS = 365.0


class MetricsError(ValueError):
    """Raised when a summary is requested on evidence that cannot support it."""


def daily_returns(returns: pd.DataFrame) -> pd.Series:
    """Compound bar returns into calendar days.

    Daily rather than per-bar throughout: a Sharpe computed on 8h bars and one computed on days
    are different numbers, and every threshold in this edition is stated in daily-annualised terms.
    """

    if "net_return" not in returns.columns:
        raise MetricsError("evaluation returns must carry net_return")
    series = pd.Series(returns["net_return"].to_numpy(dtype=float), index=returns.index)
    return (1.0 + series).resample("1D").prod() - 1.0


def _drawdown(series: pd.Series) -> float:
    if series.empty:
        return 0.0
    equity = (1.0 + series).cumprod()
    return float((1.0 - equity / equity.cummax()).max())


def _fold_fraction(series: pd.Series, folds: int) -> float:
    if len(series) < folds:
        raise MetricsError("too few observations to form the declared folds")
    chunks = np.array_split(series.to_numpy(dtype=float), folds)
    return float(np.mean([chunk.sum() > 0.0 for chunk in chunks]))


def deletion_profile_p05(series: pd.Series, *, block_days: int = 30) -> float:
    """Fifth percentile of the annualised Sharpe surviving every contiguous deletion.

    Subsumes "remove the best month", which only inspects calendar-aligned windows and therefore
    cannot find the worst one unless it happens to start on a month boundary. A percentile rather
    than the minimum, because over hundreds of overlapping windows the minimum is an extreme-value
    statistic and would rank whichever candidate contained the unluckiest month.
    """

    values = series.to_numpy(dtype=float)
    if values.size <= block_days + 2:
        raise MetricsError("series too short for a deletion profile")
    survivors = [
        stats.sharpe_ratio(np.delete(values, slice(start, start + block_days)), annualised=True)
        for start in range(values.size - block_days)
    ]
    return float(np.percentile(survivors, 5))


@dataclasses.dataclass(frozen=True, slots=True)
class MetricPacket:
    """The disclosure-safe summary of one scored window."""

    days: int
    annualised_return: float
    annualised_volatility: float
    net_sharpe: float
    double_cost_sharpe: float
    triple_cost_annualised_return: float
    max_drawdown: float
    positive_fold_fraction: float
    deflated_sharpe_probability: float
    deletion_profile_p05_sharpe: float
    mean_gross_exposure: float
    median_effective_breadth: float
    breadth_pass_fraction: float
    active_bar_fraction: float
    long_exposure_share: float
    short_exposure_share: float
    risk_unit_capped_fraction: float
    annualised_turnover: float
    gross_edge_bps_per_turnover: float
    cost_share_of_positive_gross: float
    top_symbol_gross_pnl_share: float
    ruined: bool

    def as_dict(self) -> dict[str, object]:
        return dataclasses.asdict(self)

    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"))


def _exposure_shares(returns: pd.DataFrame) -> tuple[float, float]:
    """Long and short share of total gross exposure-days.

    Measured on exposure rather than P&L. V4-R2 required the long side to have *made money*, which
    is a performance test wearing a structure test's clothes, and left 27 of 94 trials structurally
    one-sided while nominally passing a "both sides used" gate.
    """

    long_days = float(returns["long_exposure"].sum())
    short_days = float(returns["short_exposure"].sum())
    total = long_days + short_days
    if total <= 0.0:
        return 0.0, 0.0
    return long_days / total, short_days / total


def _top_symbol_share(events: pd.DataFrame) -> float:
    if events.empty or "symbol" not in events.columns:
        return 0.0
    trades = events[events["event_type"].isin({"trade", "forced_exit"})]
    if trades.empty:
        return 0.0
    magnitude = trades.groupby("symbol")["notional"].apply(lambda column: column.abs().sum())
    total = float(magnitude.sum())
    if total <= 0.0:
        return 0.0
    return float(magnitude.max() / total)


def summarize(
    result,  # type: ignore[no-untyped-def]
    index: pd.DatetimeIndex,
    *,
    double_cost_returns: pd.Series,
    triple_cost_returns: pd.Series,
    trial_count: int,
    trial_sharpe_dispersion: float,
    folds: int = 5,
    breadth_floor: float = 6.0,
    deletion_block_days: int = 30,
) -> MetricPacket:
    """Summarise exactly the days in ``index`` and nothing else.

    The index is an argument rather than a filter applied inside, so a caller cannot accidentally
    summarise a window it was not handed.
    """

    if len(index) == 0:
        raise MetricsError("cannot summarise an empty window")
    bars = result.returns.loc[result.returns.index.floor("D").isin(index)]
    if bars.empty:
        raise MetricsError("no evaluated bars fall inside the requested window")

    # Resampling spans the gaps a sealed carve leaves behind, so restrict back to the requested
    # days. Without this the visible packet silently carries sealed dates as zero-return days,
    # which both dilutes its statistics and makes the two windows overlap.
    daily = daily_returns(bars)
    daily = daily.loc[daily.index.isin(index)]
    if daily.empty:
        raise MetricsError("no scored days fall inside the requested window")
    double_daily = double_cost_returns.loc[double_cost_returns.index.isin(daily.index)]
    triple_daily = triple_cost_returns.loc[triple_cost_returns.index.isin(daily.index)]

    variance = stats.annualised_to_period_variance(trial_sharpe_dispersion)
    deflated = stats.deflated_sharpe_ratio(
        daily, trial_count=trial_count, trial_sharpe_variance=variance
    )

    breadth = bars["submitted_effective_breadth"].dropna()
    gross = bars["submitted_gross_exposure"].dropna()
    active = bars["gross_exposure"] > 0.05
    turnover = float(bars["turnover"].sum())
    years = max(len(daily) / ANNUALISATION_DAYS, 1e-9)
    gross_pnl = float(bars["price_pnl"].sum() + bars["funding_pnl"].sum())
    costs = float(bars["fees"].sum() + bars["slippage"].sum())
    positive_gross = max(gross_pnl, 1e-12)
    long_share, short_share = _exposure_shares(bars)

    return MetricPacket(
        days=int(len(daily)),
        annualised_return=float((1.0 + daily).prod() ** (1.0 / years) - 1.0),
        annualised_volatility=float(daily.std(ddof=1) * math.sqrt(ANNUALISATION_DAYS)),
        net_sharpe=stats.sharpe_ratio(daily, annualised=True),
        double_cost_sharpe=stats.sharpe_ratio(double_daily, annualised=True)
        if len(double_daily) > 1
        else 0.0,
        triple_cost_annualised_return=float((1.0 + triple_daily).prod() ** (1.0 / years) - 1.0)
        if len(triple_daily) > 1
        else 0.0,
        max_drawdown=_drawdown(daily),
        positive_fold_fraction=_fold_fraction(daily, folds),
        deflated_sharpe_probability=deflated.probability,
        deletion_profile_p05_sharpe=deletion_profile_p05(daily, block_days=deletion_block_days),
        mean_gross_exposure=float(gross.mean()) if len(gross) else 0.0,
        median_effective_breadth=float(breadth.median()) if len(breadth) else 0.0,
        breadth_pass_fraction=float((breadth >= breadth_floor).mean()) if len(breadth) else 0.0,
        active_bar_fraction=float(active.mean()),
        long_exposure_share=long_share,
        short_exposure_share=short_share,
        risk_unit_capped_fraction=float(
            bars["risk_unit_binding"]
            .isin({"max_scale", "gross_cap", "symbol_cap", "net_cap"})
            .mean()
        ),
        annualised_turnover=turnover / years,
        gross_edge_bps_per_turnover=(gross_pnl / turnover * 10_000.0) if turnover > 0 else 0.0,
        cost_share_of_positive_gross=costs / positive_gross,
        top_symbol_gross_pnl_share=_top_symbol_share(result.events),
        ruined=result.ruined_at is not None,
    )


def evidence_from_packet(
    packet: MetricPacket,
    *,
    accepted_trials: int,
    source_review_passed: bool,
    invariance_suite_passed: bool,
) -> SelectionEvidence:
    """Assemble gate evidence. Every statistical field comes from the packet, never a caller."""

    return SelectionEvidence(
        mean_gross_exposure=packet.mean_gross_exposure,
        median_effective_breadth=packet.median_effective_breadth,
        breadth_pass_fraction=packet.breadth_pass_fraction,
        active_bar_fraction=packet.active_bar_fraction,
        long_exposure_share=packet.long_exposure_share,
        short_exposure_share=packet.short_exposure_share,
        realized_annual_volatility=packet.annualised_volatility,
        risk_unit_capped_fraction=packet.risk_unit_capped_fraction,
        ruined=packet.ruined,
        annualised_turnover=packet.annualised_turnover,
        gross_edge_bps_per_turnover=packet.gross_edge_bps_per_turnover,
        cost_share_of_positive_gross=packet.cost_share_of_positive_gross,
        triple_cost_annualised_return=packet.triple_cost_annualised_return,
        net_sharpe=packet.net_sharpe,
        double_cost_sharpe=packet.double_cost_sharpe,
        max_drawdown=packet.max_drawdown,
        positive_fold_fraction=packet.positive_fold_fraction,
        deflated_sharpe_probability=packet.deflated_sharpe_probability,
        top_symbol_gross_pnl_share=packet.top_symbol_gross_pnl_share,
        deletion_profile_p05_sharpe=packet.deletion_profile_p05_sharpe,
        accepted_trials=accepted_trials,
        source_review_passed=source_review_passed,
        invariance_suite_passed=invariance_suite_passed,
    )


def team_feedback(packet: MetricPacket, allowed: Sequence[str]) -> Mapping[str, object]:
    """Project a packet down to the fields a team is entitled to see.

    An allowlist rather than a denylist. A field added to the packet later is withheld by default,
    which is the correct direction for a disclosure boundary: forgetting to allow something costs a
    team information, forgetting to deny it costs the edition its blindness.
    """

    payload = packet.as_dict()
    unknown = [name for name in allowed if name not in payload]
    if unknown:
        raise MetricsError(f"feedback allowlist names fields the packet does not have: {unknown}")
    return {name: payload[name] for name in sorted(allowed)}


# Sealed evidence carries a trial count of one; see gates.SEALED_TRIAL_COUNT for why.
SEALED_TRIALS = SEALED_TRIAL_COUNT


__all__ = [
    "ANNUALISATION_DAYS",
    "SEALED_TRIALS",
    "MetricPacket",
    "MetricsError",
    "daily_returns",
    "deletion_profile_p05",
    "evidence_from_packet",
    "summarize",
    "team_feedback",
]
