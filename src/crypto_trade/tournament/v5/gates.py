"""Qualification gates for Top-40 V5.

The dominant infrastructure defect in this repository is a gate that exists, passes its own unit
test, and gates nothing. Ten instances appeared in a single prior edition. V4-R1 declared
``neighborhood_stability`` non-negotiable in its charter and it read **false on all three
advancing finalists**, because it was evaluated per-run rather than at nomination. V4-R2 validated
``lower_floors_to_fill_bracket = false`` in its contract while the code had been patched so the
eligibility raise never fired.

Three structural choices here make that class of defect harder to reproduce than to avoid:

* every input arrives on :class:`SelectionEvidence`, a frozen dataclass with **no defaults**, so
  omitting a piece of evidence is a ``TypeError`` rather than a silent ``False``;
* each gate is a named predicate in one table, so "the set of gates" is enumerable and a
  meta-test can break each input in turn and demand that exactly that gate flips;
* gates are separated by what they can *conclude*. Degeneracy gates say a book is not a portfolio
  and stay hard. Performance gates say a book was not good enough, and on development -- where
  every prior edition's floors admitted zero of ninety-four measured trials -- they are reported
  rather than enforced.

**Where the search penalty belongs.** ``deflated_sharpe_probability`` must be computed with a trial
count that matches the data it is measured on, and the two stages differ:

* on **development**, a team selected its nominee from twelve trials on that very data, so the
  deflation benchmark uses the team's full journalled trial count. That is what makes a development
  Sharpe an honest statement about a search rather than about an edge.
* on the **sealed blocks**, the trial count is **one**. The search happened on visible data the
  sealed blocks never saw, so holding them out is already the correction; deflating again would
  charge the same search twice. Measured, the double count cost power at a true Sharpe of 1.0
  0.70 -> 0.24 while barely moving the false-positive rate.

Deflation on sealed data would be right if all twelve candidates were scored there and the best
kept. They are not: each team submits one frozen nominee.

**Why the sealed stage is a screen and not the decision.** At 360 days the standard error of an
annualised Sharpe is about 1.0, so a genuinely good book still produces weak evidence. Any
field-wide correction applied here empties the bracket -- simulated across fifteen nominees with
five real teams at Sharpe 1.0, Benjamini-Hochberg at q=0.10 selects 0.5 teams. The 2.5-year
historical window has a standard error of 0.63 and is where candidates are actually ranked; the
sealed stage exists to stop that window being spent on books that are degenerate, cost-annihilated
or negative. Field multiplicity is *reported* beside the leaderboard, never used as a gate.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping

DEVELOPMENT_STAGE = "development"
SEALED_STAGE = "sealed"

# Trial count for the deflation benchmark when evidence comes from the sealed blocks. The search
# ran on visible data these blocks never saw, so the selection bias is already removed by holding
# them out; a count above one charges the same search a second time.
SEALED_TRIAL_COUNT = 1


class GateError(ValueError):
    """Raised when a gate is asked to judge evidence it was not given."""


@dataclasses.dataclass(frozen=True, slots=True)
class SelectionEvidence:
    """Everything a disposition depends on, with no default anywhere.

    V4's ``assess_is`` took ``neighborhood_passed: bool = False``. A caller that forgot it got a
    silent failure rather than an error, and the gate reported false on every finalist that
    advanced. A dataclass without defaults turns that into a ``TypeError`` at the call site.
    """

    # -- structural: is this a portfolio at all -------------------------------------------
    mean_gross_exposure: float
    median_effective_breadth: float
    breadth_pass_fraction: float
    active_bar_fraction: float
    long_exposure_share: float
    short_exposure_share: float
    realized_annual_volatility: float
    risk_unit_capped_fraction: float
    ruined: bool

    # -- economic: does it survive its own costs ------------------------------------------
    annualised_turnover: float
    gross_edge_bps_per_turnover: float
    cost_share_of_positive_gross: float
    triple_cost_annualised_return: float

    # -- performance ------------------------------------------------------------------------
    net_sharpe: float
    double_cost_sharpe: float
    max_drawdown: float
    positive_fold_fraction: float
    deflated_sharpe_probability: float

    # -- concentration ----------------------------------------------------------------------
    top_symbol_gross_pnl_share: float
    deletion_profile_p05_sharpe: float

    # -- process ------------------------------------------------------------------------------
    accepted_trials: int
    source_review_passed: bool
    invariance_suite_passed: bool

    def __post_init__(self) -> None:
        if self.accepted_trials < 0:
            raise GateError("accepted_trials cannot be negative")
        for name in ("breadth_pass_fraction", "active_bar_fraction", "positive_fold_fraction"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise GateError(f"{name} must be a fraction in [0, 1]")


@dataclasses.dataclass(frozen=True, slots=True)
class GateThresholds:
    """Every number a disposition turns on.

    Deliberately unset at import: these are calibrated on development data and frozen before any
    sealed row is opened. Inheriting V4-R2's values is not the safe default it looks like -- its
    full floor set, its core four, and even the looser V3-extension set each admitted **zero** of
    the ninety-four measured trials.
    """

    minimum_mean_gross_exposure: float
    minimum_median_effective_breadth: float
    minimum_breadth_pass_fraction: float
    minimum_active_bar_fraction: float
    minimum_side_exposure_share: float
    volatility_band: tuple[float, float]
    maximum_risk_unit_capped_fraction: float
    minimum_annualised_turnover: float
    maximum_annualised_turnover: float
    minimum_gross_edge_bps_per_turnover: float
    maximum_cost_share_of_positive_gross: float
    minimum_positive_fold_fraction: float
    minimum_deflated_sharpe_probability: float
    maximum_vol_normalised_drawdown: float
    maximum_top_symbol_gross_pnl_share: float
    minimum_deletion_profile_p05_sharpe: float
    minimum_accepted_trials: int
    volatility_reference: float = 0.10


Predicate = Callable[[SelectionEvidence, GateThresholds], bool]


def _vol_normalised_drawdown(evidence: SelectionEvidence, thresholds: GateThresholds) -> float:
    """Drawdown restated at a common risk unit.

    A raw drawdown cap across a field whose realized volatility spans 7.3% to 20.2% caps book
    size, not risk-adjusted quality: normalised to a 10% unit, V4-R9's least-risky finalist goes
    from 20.0% to 27.4% -- worst in the field -- and its winner from 19.4% to 9.6%.
    """

    volatility = float(evidence.realized_annual_volatility)
    if volatility <= 0.0:
        return float("inf")
    return float(evidence.max_drawdown) * (thresholds.volatility_reference / volatility)


# A book that fails one of these is not a portfolio. These stay hard at every stage.
DEGENERACY_GATES: Mapping[str, Predicate] = {
    "not_ruined": lambda e, t: not e.ruined,
    "mean_gross_exposure": lambda e, t: e.mean_gross_exposure >= t.minimum_mean_gross_exposure,
    "effective_breadth": (
        lambda e, t: e.median_effective_breadth >= t.minimum_median_effective_breadth
    ),
    "breadth_persistence": (
        lambda e, t: e.breadth_pass_fraction >= t.minimum_breadth_pass_fraction
    ),
    "participation": lambda e, t: e.active_bar_fraction >= t.minimum_active_bar_fraction,
    # Measured on exposure, not P&L. V4-R2 required the long side to have *made money*, which is a
    # performance test wearing a structure test's clothes and left 27 of 94 trials one-sided.
    "both_sides_used": lambda e, t: (
        min(e.long_exposure_share, e.short_exposure_share) >= t.minimum_side_exposure_share
    ),
    "risk_unit_attained": (
        lambda e, t: t.volatility_band[0] <= e.realized_annual_volatility <= t.volatility_band[1]
    ),
    "risk_unit_not_permanently_capped": (
        lambda e, t: e.risk_unit_capped_fraction <= t.maximum_risk_unit_capped_fraction
    ),
    "turnover_floor": lambda e, t: e.annualised_turnover >= t.minimum_annualised_turnover,
    "source_review": lambda e, t: e.source_review_passed,
    "causal_invariance": lambda e, t: e.invariance_suite_passed,
    "research_budget": lambda e, t: e.accepted_trials >= t.minimum_accepted_trials,
}

# Cost survival. A book that cannot pay its own costs is not a marginal candidate: prior editions
# measured a best-in-field 2x Sharpe of 0.567, one finalist whose costs were 556% of positive
# gross P&L, and a whole edition with no lane profitable at 3x.
COST_GATES: Mapping[str, Predicate] = {
    "turnover_ceiling": lambda e, t: e.annualised_turnover <= t.maximum_annualised_turnover,
    "gross_edge_density": (
        lambda e, t: e.gross_edge_bps_per_turnover >= t.minimum_gross_edge_bps_per_turnover
    ),
    "cost_share": (
        lambda e, t: e.cost_share_of_positive_gross <= t.maximum_cost_share_of_positive_gross
    ),
    "survives_triple_cost": lambda e, t: e.triple_cost_annualised_return > 0.0,
}

# Performance and robustness. Reported on development, enforced on the sealed blocks.
PERFORMANCE_GATES: Mapping[str, Predicate] = {
    "fold_breadth": lambda e, t: e.positive_fold_fraction >= t.minimum_positive_fold_fraction,
    "deflated_sharpe": (
        lambda e, t: e.deflated_sharpe_probability >= t.minimum_deflated_sharpe_probability
    ),
    "vol_normalised_drawdown": (
        lambda e, t: _vol_normalised_drawdown(e, t) <= t.maximum_vol_normalised_drawdown
    ),
    "symbol_concentration": (
        lambda e, t: e.top_symbol_gross_pnl_share <= t.maximum_top_symbol_gross_pnl_share
    ),
    "deletion_robustness": (
        lambda e, t: e.deletion_profile_p05_sharpe >= t.minimum_deletion_profile_p05_sharpe
    ),
}

ALL_GATES: Mapping[str, Predicate] = {**DEGENERACY_GATES, **COST_GATES, **PERFORMANCE_GATES}


@dataclasses.dataclass(frozen=True, slots=True)
class Assessment:
    stage: str
    gates: Mapping[str, bool]
    enforced: tuple[str, ...]
    reported: tuple[str, ...]

    @property
    def eligible(self) -> bool:
        return all(self.gates[name] for name in self.enforced)

    def failures(self) -> tuple[str, ...]:
        return tuple(name for name in self.enforced if not self.gates[name])

    def as_dict(self) -> dict[str, object]:
        return {
            "stage": self.stage,
            "eligible": self.eligible,
            "gates": dict(self.gates),
            "enforced": list(self.enforced),
            "reported_only": list(self.reported),
            "failures": list(self.failures()),
        }


def assess(evidence: SelectionEvidence, thresholds: GateThresholds, *, stage: str) -> Assessment:
    """Evaluate every gate, and enforce the subset this stage is entitled to enforce.

    Development enforces structure and cost but only *reports* performance. Twelve feedback-driven
    trials make a development Sharpe a statement about a search, not about an edge: the V4-R9
    field's within-team trial dispersion implies a null hurdle above its best observed trial.
    The sealed blocks were never optimised against, so that is where performance is decided.
    """

    if stage not in {DEVELOPMENT_STAGE, SEALED_STAGE}:
        raise GateError(f"unknown selection stage: {stage}")
    gates = {name: bool(predicate(evidence, thresholds)) for name, predicate in ALL_GATES.items()}
    if stage == DEVELOPMENT_STAGE:
        enforced = tuple(DEGENERACY_GATES) + tuple(COST_GATES)
        reported = tuple(PERFORMANCE_GATES)
    else:
        enforced = tuple(ALL_GATES)
        reported = ()
    return Assessment(stage=stage, gates=gates, enforced=enforced, reported=reported)


__all__ = [
    "ALL_GATES",
    "COST_GATES",
    "DEGENERACY_GATES",
    "DEVELOPMENT_STAGE",
    "PERFORMANCE_GATES",
    "SEALED_STAGE",
    "Assessment",
    "GateError",
    "GateThresholds",
    "SelectionEvidence",
    "assess",
]
