"""Two-pass candidate evaluation: unscaled book, then common risk unit at 1x/2x/3x cost.

A team strategy returns only signed target weights through the narrow ``TargetStrategy``
protocol; it never sees fills, prices, costs, or PnL. Scoring a candidate then goes:

1. Generate raw targets by streaming a past-only ``DecisionContext`` to the strategy at every
   decision boundary (:func:`crypto_trade.tournament.engine_v2.generate_targets`).
2. Normalise each explicit rebalance row to unit gross, preserving relative sizing and net
   exposure (:func:`normalise_unit_gross`). That normalised book is what the team *requested*.
3. Apply the section 4 exposure caps to the requested book (:func:`apply_exposure_caps`), and
   evaluate the result once, at ordinary (1x) cost. This pass exists only to measure the book's own
   volatility -- its result is exposed as ``CandidateRun.unscaled`` and is never itself one of the
   scored cost levels.
4. Derive the common risk-unit scalars from pass 1's *gross* returns (``price_pnl + funding_pnl``,
   never ``net_return``): using net here would make the scalar a function of the very costs it
   goes on to scale, which is exactly the circularity Task 4's risk unit was built to avoid.
5. Apply the scalars, apply the section 4 exposure caps a second time -- ``s_t`` reaches 3.0, so
   one application cannot hold -- and re-evaluate at every requested cost multiplier (1, 2, 3).

Both cap applications are recorded, per boundary, as an :class:`ExposureCapTrim`, and both trims
travel into the released packet. A team whose book was reduced can see that its intended weights
were not its executed ones, and by how much; see :func:`exposure_cap_trim`.

Where the declared risk policy sits in that order is charter section 6, and it is worth stating
plainly because the two passes make it easy to misread. The policy runs INSIDE the evaluator, in
BOTH passes, and in each pass it fires off THAT pass's own book: its equity path, its realised
return history, its entry prices and its holding ages. Pass 1 is a reference book whose only job
is to produce ``sigma_t``; pass 2 is the executed book. A policy is therefore evaluated against
the book it actually governs, which is the only book whose drawdown, volatility and position ages
exist. See section 6 for why this cannot be reorganised into "apply the policy once, then scale
its output": three of the six declarable primitives (position stops, time stops and the turnover
limit, plus the cooldown blocks the first two arm) are order-level vetoes and partial fills over
carried quantities, not weights, and 98% of a sparse candidate's policy fills land on boundaries
that have no target row at all.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
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

STAGE_REQUESTED = "requested"
"""The team's own book: unit-gross normalised weights, before any organiser scaling."""

STAGE_EXECUTED = "executed"
"""The organiser's book: ``s_t x`` the reference weights, which is what pass 2 is given."""

CAP_STAGES = (STAGE_REQUESTED, STAGE_EXECUTED)

CAP_NAMES = ("gross", "net", "symbol")
"""The three section 4 caps, in the order a tie between them is resolved for reporting."""

_CAP_TOLERANCE = 1e-12
"""Absolute slack before a cap is treated as breached, so float noise cannot manufacture a trim.

Not decoration. ``normalise_unit_gross`` divides by the row's own absolute sum, and for a
**20-name equal-weight book** -- the exact shape of a CUP-20 universe-wide candidate -- the
renormalised weights sum to ``1.0000000000000002``, two ULP above the 1.0 gross cap. Under a strict
``>`` comparison every such boundary would be recorded as trimmed and rescaled by ``1 - 2e-16``,
which is a lie in the packet ("this book was reduced at 4383 of 4383 boundaries") for no change in
behaviour anyone can observe.

Chosen at 1e-12 rather than matching ``_validate_weight_limits``'s own 1e-10: a row that passes
through here untrimmed is then at most ``ceiling + 1e-12``, which is well inside the evaluator's
1e-10 acceptance, so the two can never disagree about whether a book is admissible.
"""


@dataclasses.dataclass(frozen=True, slots=True)
class ExposureCapTrim:
    """What the section 4 caps did to one book, boundary by boundary.

    Trimming a team's book silently would be its own kind of dishonesty, so every reduction is
    recorded rather than merely performed. ``scale`` is the uniform per-boundary factor that was
    applied (1.0 where nothing bound); ``binding_cap`` names which of ``gross``/``net``/``symbol``
    produced it, or ``""``; ``rebalance`` marks the rows carrying an explicit target, which are the
    only rows the evaluator acts on and therefore the only ones :meth:`summary` counts.
    """

    stage: str
    scale: pd.Series
    binding_cap: pd.Series
    rebalance: pd.Series

    @property
    def trimmed(self) -> pd.Index:
        """The explicit-target boundaries this book was actually reduced at."""
        return self.scale.index[self._trimmed_mask()]

    def _trimmed_mask(self) -> np.ndarray:
        acted = self.rebalance.to_numpy(dtype=bool)
        return acted & (self.scale.to_numpy(dtype=float) < 1.0)

    def summary(self) -> dict[str, Any]:
        """A JSON-safe digest of the reduction, for the released packet.

        Every value is finite by construction -- ``build_packet`` serialises with
        ``allow_nan=False`` -- so the "nothing was trimmed" case reports scales of 1.0 rather than
        the ``NaN`` an empty median would produce.
        """
        trimmed = self._trimmed_mask()
        scales = self.scale.to_numpy(dtype=float)[trimmed]
        binding = self.binding_cap.to_numpy()
        acted = int(self.rebalance.to_numpy(dtype=bool).sum())
        return {
            "stage": self.stage,
            "boundaries": acted,
            "trimmed_boundaries": int(trimmed.sum()),
            "trimmed_fraction": float(trimmed.sum() / acted) if acted else 0.0,
            "minimum_scale": float(scales.min()) if scales.size else 1.0,
            "median_scale": float(np.median(scales)) if scales.size else 1.0,
            "binding_cap_counts": {
                name: int(((binding == name) & trimmed).sum()) for name in CAP_NAMES
            },
        }


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateRun:
    """Every artifact from one strategy's two-pass evaluation against one snapshot.

    ``requested_targets`` are the unit-gross normalised weights exactly as the team expressed them
    (charter section 6 step 1). ``targets`` are those weights with the section 4 caps applied, which
    is the reference book pass 1 evaluates. ``scaled_targets`` are the EXECUTED weights of section 6
    step 4 -- ``s_t x targets``, capped again -- which is what pass 2 is given. ``requested_trim``
    and ``executed_trim`` record what each cap application did.
    """

    requested_targets: pd.DataFrame
    targets: pd.DataFrame
    scaled_targets: pd.DataFrame
    requested_trim: ExposureCapTrim
    executed_trim: ExposureCapTrim
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


def _cap_scale(
    targets: pd.DataFrame, config: EvaluatorConfig
) -> tuple[list[str], pd.Series, pd.Series]:
    """The one uniform per-row reduction factor, and which cap produced it.

    Shared by :func:`apply_exposure_caps` and :func:`exposure_cap_trim` so the trim a team is shown
    is by construction the trim that was applied, not a second computation that could drift.
    """
    weight_columns = [c for c in targets.columns if c != REBALANCE_INSTRUCTION_COLUMN]
    index = targets.index
    if not weight_columns:
        return (
            [],
            pd.Series(1.0, index=index, dtype=float),
            pd.Series("", index=index, dtype=object),
        )
    values = targets[weight_columns].to_numpy(dtype=float)
    # A non-finite weight has no defensible cap scale -- ``inf / inf`` is NaN and NaN compares
    # False against every bound, so it would sail through the caps untouched and only surface as
    # the evaluator's own non-finite-target raise, one pass later and without saying which row.
    if not np.isfinite(values).all():
        raise ValueError("target weights contain non-finite values; cannot apply exposure caps")

    # ``weight_columns`` is non-empty here, so ``values`` always has at least one column and the
    # row-wise max below is always defined (a zero-ROW frame is fine: every reduction is empty).
    magnitudes = {
        "gross": np.abs(values).sum(axis=1),
        "net": np.abs(values.sum(axis=1)),
        "symbol": np.abs(values).max(axis=1),
    }
    ceilings = {
        "gross": config.max_gross_exposure,
        "net": config.max_abs_net_exposure,
        "symbol": config.max_symbol_exposure,
    }
    scale = np.ones(len(values))
    binding = np.full(len(values), "", dtype=object)
    for name in CAP_NAMES:
        magnitude, ceiling = magnitudes[name], ceilings[name]
        breached = magnitude > ceiling + _CAP_TOLERANCE
        if not breached.any():
            continue
        candidate = np.ones(len(values))
        candidate[breached] = ceiling / magnitude[breached]
        # Strict ``<``: on an exact tie the earlier cap in ``CAP_NAMES`` keeps the attribution.
        # Which name is reported is cosmetic; the scale is the same either way.
        binding[candidate < scale] = name
        scale = np.minimum(scale, candidate)
    return (
        weight_columns,
        pd.Series(scale, index=index, dtype=float),
        pd.Series(binding, index=index, dtype=object),
    )


def apply_exposure_caps(targets: pd.DataFrame, config: EvaluatorConfig) -> pd.DataFrame:
    """Scale each row down until it satisfies the section 4 gross, net and per-symbol caps.

    Charter section 4 states the caps are **applied**, not enforced by rejection. Nothing was
    applying them. ``evaluate_targets`` does not cap a target row -- ``_validate_weight_limits``
    REJECTS one -- so two ordinary book shapes could not be evaluated at all:

    * ``s_t x`` a unit-gross book raised ``gross exposure ... exceeds cap`` at the first boundary
      where ``s_t > 1``. ``s_t = clamp(0.10 / sigma_t, 0.20, 3.0)`` exceeds 1 for any book whose
      trailing 90-day gross volatility sits under the 10% target; on a plain equal-weight long book
      over 400 days it exceeded 1 at 559 of 1199 boundaries and reached 2.11.
    * a book concentrated in fewer than five names raised ``symbol exposure ... exceeds cap`` in
      pass 1, before the risk unit even existed: four equal names at unit gross is 0.25 each
      against a 0.20 cap.

    Section 6's own low-volatility paragraph shows the crash was never intended: it reasons about
    what happens when the scalar "cannot take a very-low-volatility book *up* past unit gross", and
    concludes that the run is scored and then disqualified by the 0.06 realised-volatility floor --
    which requires the run to COMPLETE. The same holds for concentration: a cross-sectional book on
    a 20-name universe concentrates whenever its filter is selective, and rejecting it would make
    the tournament silently forbid a whole shape of strategy.

    **Reduces only, never redistributes.** The trimmed weight is not pushed onto the other names.
    A four-name book capped at 0.20 each runs at 0.80 gross rather than being renormalised back to
    1.0, because which names a book is in and in what proportion is the strategy's expressed intent
    and the organiser does not own it. Redistribution would also be an evasion surface: it can
    RAISE a weight above what the team asked for, so a team could reach a shape it was not allowed
    to request. One uniform scale cannot -- the executed book is always a positive multiple of the
    requested one, so no reachable shape is added and the cap binds by reduction rather than by
    exception. A row already inside every cap is returned untouched.

    **Applied twice, at both ends of the common risk unit.** See :func:`run_candidate`: once is not
    enough in either direction. Capping only after ``s_t`` leaves pass 1 to reject a concentrated
    book; capping only before it leaves ``s_t`` (up to 3.0) to push the executed book back over.
    The operation is reduction-only and idempotent, so applying it at both points cannot lever
    anything up.
    """
    result = targets.copy()
    weight_columns, scale, _ = _cap_scale(targets, config)
    if not weight_columns:
        return result
    result[weight_columns] = targets[weight_columns].mul(scale, axis=0)
    return result


def exposure_cap_trim(
    targets: pd.DataFrame, config: EvaluatorConfig, *, stage: str
) -> ExposureCapTrim:
    """Record what :func:`apply_exposure_caps` would do to ``targets``, without doing it.

    The disclosure half of the caps. A team that is trimmed must be able to tell that its intended
    weights were not its executed ones, and the organiser must be able to see how far a candidate
    was reduced before comparing it with one that was not.
    """
    if stage not in CAP_STAGES:
        raise ValueError(f"stage must be one of {list(CAP_STAGES)}, got {stage!r}")
    _, scale, binding = _cap_scale(targets, config)
    if REBALANCE_INSTRUCTION_COLUMN in targets.columns:
        rebalance = targets[REBALANCE_INSTRUCTION_COLUMN].astype(bool)
    else:
        # No instruction column means every row is an explicit target (the hand-built frames in
        # the tests, and any caller normalising a plain weight matrix).
        rebalance = pd.Series(True, index=targets.index, dtype=bool)
    return ExposureCapTrim(stage=stage, scale=scale, binding_cap=binding, rebalance=rebalance)


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
    """Generate targets, derive the common risk unit, then score at every cost multiplier.

    **Where the caps are applied, and why it is both ends rather than one.** Charter section 4 puts
    them "after the common risk unit", which is necessary and not sufficient:

    * the reference pass evaluates the team's own normalised book, and ``_validate_weight_limits``
      raises on it, so a concentrated book dies BEFORE any ``s_t`` exists. Capping only afterwards
      does not rescue it.
    * ``s_t`` reaches 3.0, so a book capped before the risk unit is over the caps again after it.

    Capping the reference book does not tilt the risk unit, because the risk unit is scale-
    invariant: a uniform trim ``c`` scales the reference book's gross returns by ``c``, so
    ``sigma_t`` scales by ``c`` and ``s_t = 0.10 / sigma_t`` by ``1/c``. The product ``s_t x c`` is
    unchanged, so the executed book is what it would have been had the trim happened only at the
    second application -- except that it is now a book pass 1 could actually evaluate. That holds
    exactly while ``s_t`` is strictly inside its ``[0.20, 3.0]`` clamp; at either end the clamp
    binds and the trim is not fully undone, which is what a clamp is for.
    """
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
    requested_targets = normalise_unit_gross(raw_targets)
    requested_trim = exposure_cap_trim(requested_targets, config, stage=STAGE_REQUESTED)
    targets = apply_exposure_caps(requested_targets, config)

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
    # Section 6 step 4: "Executed weights = s_t x reference weights, reduced until the section 4
    # caps hold." The participation cap is the evaluator's; the exposure caps are these.
    scaled = apply_risk_scalars(targets, scalars)
    executed_trim = exposure_cap_trim(scaled, config, stage=STAGE_EXECUTED)
    scaled_targets = apply_exposure_caps(scaled, config)

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
        requested_targets=requested_targets,
        targets=targets,
        scaled_targets=scaled_targets,
        requested_trim=requested_trim,
        executed_trim=executed_trim,
        risk_scalars=scalars,
        unscaled=unscaled,
        results=results,
    )
