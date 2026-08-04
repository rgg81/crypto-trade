"""Two-pass candidate evaluation: unscaled book, then common risk unit at 1x/2x/3x cost.

A team strategy returns only signed target weights through the narrow ``TargetStrategy``
protocol; it never sees fills, prices, costs, or PnL. Scoring a candidate then goes:

1. Generate raw targets by streaming a past-only ``DecisionContext`` to the strategy at every
   decision boundary (:func:`crypto_trade.tournament.engine_v2.generate_targets`).
2. Normalise each explicit rebalance row to unit gross, preserving relative sizing and net
   exposure (:func:`normalise_unit_gross`).
3. Evaluate that unscaled book once, at ordinary (1x) cost. This pass exists only to measure the
   book's own volatility -- its result is exposed as ``CandidateRun.unscaled`` and is never itself
   one of the scored cost levels.
4. Derive the common risk-unit scalars from pass 1's *gross* returns (``price_pnl + funding_pnl``,
   never ``net_return``): using net here would make the scalar a function of the very costs it
   goes on to scale, which is exactly the circularity Task 4's risk unit was built to avoid.
5. Apply the scalars and re-evaluate at every requested cost multiplier (1, 2, 3 by default).
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

import pandas as pd

from crypto_trade.cup20.risk_unit import apply_risk_scalars, common_risk_scalars
from crypto_trade.cup20.snapshot import Snapshot
from crypto_trade.tournament.engine_v2 import (
    EvaluationResult,
    EvaluatorConfig,
    evaluate_targets,
    generate_targets,
)
from crypto_trade.tournament.protocol import REBALANCE_INSTRUCTION_COLUMN, TargetStrategy
from crypto_trade.tournament.risk_policy import RiskPolicy


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateRun:
    """Every artifact from one strategy's two-pass evaluation against one snapshot."""

    targets: pd.DataFrame
    scaled_targets: pd.DataFrame
    risk_scalars: pd.Series
    unscaled: EvaluationResult
    results: dict[int, EvaluationResult]


def decision_grid(
    start: pd.Timestamp, end: pd.Timestamp, *, interval_hours: int = 8
) -> tuple[pd.Timestamp, ...]:
    """Half-open ``[start, end)`` grid of UTC decision boundaries."""
    start_utc = pd.Timestamp(start).tz_convert("UTC")
    end_utc = pd.Timestamp(end).tz_convert("UTC")
    if start_utc >= end_utc:
        # A half-open [start, end) interval is empty whenever start does not come strictly
        # before end. pd.date_range's own inclusive="left" does not enforce this at the
        # degenerate start == end point -- empirically it keeps that single coincident boundary
        # rather than dropping it -- so this guard is required, not merely defensive. start > end
        # was already handled correctly by pd.date_range itself; this also covers that case
        # explicitly so both "no room in the interval" cases share one clear code path.
        return ()
    times = pd.date_range(start_utc, end_utc, freq=f"{interval_hours}h", inclusive="left")
    return tuple(times)


def normalise_unit_gross(targets: pd.DataFrame) -> pd.DataFrame:
    """Rescale every explicit rebalance row to unit gross, preserving net exposure and signs."""
    result = targets.copy()
    weight_columns = [c for c in result.columns if c != REBALANCE_INSTRUCTION_COLUMN]
    if not weight_columns:
        return result
    gross = result[weight_columns].abs().sum(axis=1)
    divisor = gross.where(gross > 0.0, 1.0)
    result[weight_columns] = result[weight_columns].div(divisor, axis=0)
    return result


def evaluator_config(raw: Mapping[str, Any]) -> EvaluatorConfig:
    """Build the evaluator configuration from the frozen ``[execution]`` table.

    ``EvaluatorConfig``'s own defaults (``max_abs_net_exposure=0.25``, ``max_symbol_exposure=0.10``)
    are quarter-net footguns for CUP-20, where several team mandates are directional and would
    otherwise be silently capped. Every CUP-20 caller must build the evaluator config through this
    function -- never bare ``EvaluatorConfig()`` -- so the frozen policy values govern evaluation.
    """
    return EvaluatorConfig(
        interval_hours=int(raw["interval_hours"]),
        initial_equity=float(raw["initial_equity"]),
        taker_fee_bps_per_side=float(raw["taker_fee_bps_per_side"]),
        slippage_bps_per_side=float(raw["slippage_bps_per_side"]),
        max_gross_exposure=float(raw["max_gross_exposure"]),
        max_abs_net_exposure=float(raw["max_abs_net_exposure"]),
        max_symbol_exposure=float(raw["max_symbol_exposure"]),
        max_bar_participation=float(raw["max_bar_participation"]),
    )


def _validate_decision_times(decision_times: Sequence[pd.Timestamp]) -> None:
    """Enforce what ``common_risk_scalars`` deliberately leaves to its caller: a total order.

    ``crypto_trade.cup20.risk_unit`` documents that it trusts ``decision_times`` to already be
    sorted and duplicate-free; Task 4's review deferred that enforcement here. A scrambled or
    duplicated schedule would otherwise reach the risk unit silently -- ``generate_targets``
    itself re-sorts before building the target frame, so a caller mistake here would not surface
    as a crash downstream, just a scalar series keyed off an order the caller never intended.

    Also rejects an empty sequence outright. ``decision_grid(start, end)`` returns one whenever
    ``start > end`` (a caller mistake such as swapping IS/OOS boundaries), and without this guard
    that would otherwise pass every check below vacuously (an empty list is trivially "sorted" and
    "duplicate-free"), only to blow up several calls later as an opaque ``KeyError`` when
    ``run_candidate`` indexes the unscaled book's columnless return frame.
    """
    if len(decision_times) == 0:
        raise ValueError(
            "decision_times must not be empty (decision_grid(start, end) returns an empty grid "
            "whenever start > end)"
        )
    parsed = [pd.Timestamp(t) for t in decision_times]
    if parsed != sorted(parsed):
        raise ValueError("decision_times must be sorted ascending")
    if len(set(parsed)) != len(parsed):
        raise ValueError("decision_times must not contain duplicate timestamps")


def _validate_return_cadence(index: pd.Index, interval_hours: int) -> None:
    """Enforce the other invariant ``common_risk_scalars`` leaves to its caller.

    ``common_risk_scalars`` annualises realised volatility purely from the ``interval_hours`` it
    is told; it has no independent way to notice that the return series it was actually given is
    spaced differently. Such a mismatch would silently misannualise the risk unit rather than
    raise, so this runner checks the unscaled book's real row spacing before deriving the scalar.
    """
    times = pd.DatetimeIndex(index)
    if len(times) < 2:
        return
    expected = pd.Timedelta(hours=interval_hours)
    deltas = times[1:] - times[:-1]
    mismatched = deltas[deltas != expected]
    if len(mismatched):
        raise ValueError(
            f"unscaled return series cadence does not match interval_hours={interval_hours} "
            f"(expected {expected} between consecutive rows, found {mismatched[0]})"
        )


def run_candidate(
    strategy: TargetStrategy,
    snapshot: Snapshot,
    *,
    decision_times: Sequence[pd.Timestamp],
    seed: int,
    config: EvaluatorConfig,
    risk_unit: Mapping[str, float],
    cost_multipliers: Sequence[int] = (1, 2, 3),
    risk_policy: RiskPolicy | None = None,
) -> CandidateRun:
    """Generate targets, derive the common risk unit, then score at every cost multiplier."""
    _validate_decision_times(decision_times)
    raw_targets = generate_targets(
        strategy,
        snapshot.bars,
        snapshot.funding,
        snapshot.membership,
        decision_times,
        seed=seed,
        interval_hours=config.interval_hours,
    )
    targets = normalise_unit_gross(raw_targets)

    unscaled = evaluate_targets(
        snapshot.bars,
        snapshot.funding,
        snapshot.membership,
        targets,
        mark_prices=snapshot.mark_prices,
        config=config,
        cost_multiplier=1.0,
        risk_policy=risk_policy,
    )
    _validate_return_cadence(unscaled.returns.index, config.interval_hours)
    # Gross, never net -- see the module docstring and Task 4's report for why. ``net_return``
    # already has fees and slippage subtracted; scaling the book from a scalar derived off its
    # own costs would be circular.
    gross_returns = unscaled.returns["price_pnl"] + unscaled.returns["funding_pnl"]
    scalars = common_risk_scalars(
        gross_returns,
        list(targets.index),
        target_annualized_volatility=float(risk_unit["target_annualized_volatility"]),
        lookback_days=int(risk_unit["lookback_days"]),
        interval_hours=config.interval_hours,
        minimum_scale=float(risk_unit.get("minimum_scale", 0.20)),
        maximum_scale=float(risk_unit.get("maximum_scale", 3.0)),
    )
    scaled_targets = apply_risk_scalars(targets, scalars)

    results = {
        int(multiplier): evaluate_targets(
            snapshot.bars,
            snapshot.funding,
            snapshot.membership,
            scaled_targets,
            mark_prices=snapshot.mark_prices,
            config=config,
            cost_multiplier=float(multiplier),
            risk_policy=risk_policy,
        )
        for multiplier in cost_multipliers
    }
    return CandidateRun(
        targets=targets,
        scaled_targets=scaled_targets,
        risk_scalars=scalars,
        unscaled=unscaled,
        results=results,
    )
