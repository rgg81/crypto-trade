"""The floor vector: two integrity checks that disqualify, and nineteen that cost points.

Before amendment A4 every check here was a conjunctive hard floor, and one miss out of twenty-two
discarded a candidate entirely. That is how a book positive in all four folds, positive on both
sleeves and inside every risk limit came to be ranked nowhere at all. A4 keeps every floor measured
and reported, and makes advancement depend on the ranking score instead -- except for the two checks
in ``INTEGRITY_GATES``, which are not claims about quality but about whether the evidence means what
the certificate says. Those still disqualify, because no score can repair a false claim.

The holdout stage does not follow A4. There the floors remain conjunctive and hard, because that
stage asks whether a book is good enough to deploy rather than which book is best, and section 1.1
keeps "no winner" as a permitted answer.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any

# Amendment A4 sorts the gate vector into three classes rather than two.
#
# SUBSTANCE -- is there a book here at all? These do not ask whether a strategy is good; they ask
# whether it traded. A4 demoted them with the rest and an adversarial review found the consequence
# immediately: an under-risked book that grinds up on a whisper of volatility takes a near-zero
# drawdown and an undefined-Calmar sentinel straight to a PERFECT ranking score, beating every real
# submission in the field. The volatility floor's own comment had said exactly this -- it exists "to
# disqualify an under-risked book instead of rewarding it with an unearned drawdown advantage" --
# and removing its teeth while keeping its 35 points of reward inverted the tournament. Refusing a
# book that does not trade is not blocking a team; it is declining to rank a non-entry.
SUBSTANCE_GATES = frozenset(
    {
        "annualized_volatility",
        "trade_count",
    }
)

# INTEGRITY -- does the evidence mean what the certificate says? No ranking repairs a false claim.
#
#   sign_inversion_not_profitable      inverting the signal also clears the core floors, so the
#                                      result is an artifact of the harness rather than of the
#                                      stated mechanism -- there is nothing here to rank.
#   declared_roles_match_traded_sides  the certificate claims a sleeve the book never traded, or
#                                      hides one it did.
INTEGRITY_GATES = frozenset(
    {
        "sign_inversion_not_profitable",
        "declared_roles_match_traded_sides",
    }
)

# PERFORMANCE -- everything else. Measured, reported, and priced by the ranking score rather than
# vetoed. The blindness scan, the source scan, the section 5.1 coordinate rule, the A1 inertness
# rule and the A3 volatility-target ban are hard for the integrity reason and live outside this
# function.
ADMISSION_GATES = SUBSTANCE_GATES | INTEGRITY_GATES


@dataclasses.dataclass(frozen=True, slots=True)
class GateVector:
    checks: Mapping[str, bool]

    @property
    def passed(self) -> bool:
        """Every floor met, conjunctively. What the holdout stage still decides on."""
        return all(self.checks.values())

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(name for name, ok in self.checks.items() if not ok)

    def _admission_verdict(self, gates: frozenset[str]) -> str:
        """``"failed"`` beats ``"unmeasured"`` beats ``"passed"`` -- worst news wins.

        The three-way answer exists because "we measured this and it failed" and "nobody has
        measured this yet" must not collapse into one another. A sweep cannot decide sign
        inversion -- that is its own material trial -- so a candidate scored off a sweep alone is
        genuinely UNMEASURED, and it would be a false accusation to report it as having failed a
        falsification it never ran. It is equally wrong to let it advance as though it had passed.
        """
        present = {name: self.checks[name] for name in gates if name in self.checks}
        if any(not ok for ok in present.values()):
            return "failed"
        if gates - set(present):
            return "unmeasured"
        return "passed"

    @property
    def integrity_verdict(self) -> str:
        return self._admission_verdict(INTEGRITY_GATES)

    @property
    def substance_verdict(self) -> str:
        return self._admission_verdict(SUBSTANCE_GATES)

    @property
    def admissible(self) -> bool:
        """Eligible to be RANKED: every admission gate measured and met.

        Deliberately not consulted by the holdout path, whose gate vector contains none of these
        keys -- see ``CandidateAdjudication.admissible``, which is stage-aware.
        """
        return self.integrity_verdict == "passed" and self.substance_verdict == "passed"

    @property
    def refuted(self) -> bool:
        """An admission gate was measured and FAILED, as opposed to never having been measured."""
        return "failed" in (self.integrity_verdict, self.substance_verdict)

    @property
    def admission_failures(self) -> tuple[str, ...]:
        """Admission gates measured and failed. Never includes one that was merely unmeasured."""
        return tuple(
            name
            for name in sorted(ADMISSION_GATES)
            if name in self.checks and not self.checks[name]
        )

    @property
    def unmeasured_admission_gates(self) -> tuple[str, ...]:
        return tuple(sorted(ADMISSION_GATES - set(self.checks)))

    @property
    def integrity_failures(self) -> tuple[str, ...]:
        """Integrity gates measured and failed. Reported separately from substance."""
        return tuple(
            name
            for name in sorted(INTEGRITY_GATES)
            if name in self.checks and not self.checks[name]
        )

    @property
    def performance_failures(self) -> tuple[str, ...]:
        """Floors missed that cost points rather than admission."""
        return tuple(name for name in self.failures if name not in ADMISSION_GATES)


def _finite(value: object) -> float:
    number = float(value)  # type: ignore[arg-type]
    return number if math.isfinite(number) else math.nan


def _at_least(value: object, floor: float) -> bool:
    number = _finite(value)
    return math.isfinite(number) and number >= floor


def _at_most(value: object, ceiling: float) -> bool:
    number = _finite(value)
    return math.isfinite(number) and number <= ceiling


def _positive(value: object) -> bool:
    number = _finite(value)
    return math.isfinite(number) and number > 0.0


# A side counts as traded only when its gross PnL is at least this fraction of the book's TOTAL
# gross activity (|long| + |short|). Relative, never absolute: the threshold has to mean the same
# thing for a book earning 0.02 and one earning 20.
#
# The number is chosen to sit as far as possible from BOTH mistakes it can make, on a log scale:
#
#   ~1e-10 relative -- the largest magnitude dust can plausibly reach. Two sources, and they happen
#   to agree: floating-point accumulation error over the ~3e5 bar-symbol terms summed across the
#   in-sample window is about N * 2.2e-16 ~ 1e-10 of the running magnitude; and a single position
#   at the smallest weight the evaluator treats as real (1e-12, its own tolerance) held for one bar
#   through an ordinary move contributes about the same against a unit-gross book.
#
#   ~1e-2 relative -- the smallest sleeve that could change any reported number at the precision
#   the charter states policy in. Every ratio floor is written to two decimals (0.80, 0.50, 0.20,
#   0.30, 0.35, 0.60, 0.70, 0.90), so a sleeve below a percent of gross activity cannot move a
#   verdict, and there is correspondingly nothing for a team to gain by hiding one.
#
# 1e-6 is the geometric midpoint: four orders of magnitude of headroom above anything numerical,
# and four below anything a team could hide a real sleeve behind. A threshold with that much margin
# on both sides is set by the physics of the two failure modes rather than by taste, which is the
# property that matters -- this decides a HARD FLOOR, and a team disqualified by it on a rounding
# artifact would have a fair grievance.
_MATERIAL_SIDE_FRACTION = 1e-6


def _material_sides(role_values: Mapping[str, object]) -> tuple[str, ...]:
    """Which sides the book actually traded, judged from gross PnL rather than from a declaration.

    Materiality, not mere non-zero-ness. Nothing upstream filters dust -- ``normalise_unit_gross``
    only divides by gross, and the evaluator treats any target above 1e-12 as real -- so a long-only
    book that emitted a single -1e-9 weight at one boundary in four years really does carry a
    nanoscale short, with a real (and sign-random) PnL attached. Under a ``!= 0.0`` rule that book
    collected TWO hard-floor failures: a coin-flip on ``role_short_gross_pnl``, and a
    ``declared_roles_match_traded_sides`` mismatch that fired even when the dust sleeve happened to
    be profitable, because the check compares sets rather than signs. That is a false accusation
    manufactured out of a rounding artifact -- the same class closed twice in
    ``verify_neighbourhood_coordinates``.

    A non-finite side is ALWAYS material and can never be dismissed as dust: it cannot be shown
    small, so it must be gated (where ``_positive`` then fails it). It is also excluded from the
    total, so one unusable side cannot drag the other below the threshold.
    """
    magnitudes = {role: abs(_finite(value)) for role, value in role_values.items()}
    total = sum(value for value in magnitudes.values() if math.isfinite(value))
    return tuple(
        role
        for role, magnitude in magnitudes.items()
        if not math.isfinite(magnitude) or magnitude > _MATERIAL_SIDE_FRACTION * total
    )


def evaluate_floors(
    scored: Mapping[str, float],
    *,
    floors: Mapping[str, Any],
    statistics_config: Mapping[str, Any],
    research_config: Mapping[str, Any],
    declared_roles: Sequence[str],
    sign_inversion_passes_core: bool | None,
    neighbourhood_positive_fraction: float,
    trial_adjusted_confidence: float,
) -> GateVector:
    """Evaluate every hard floor. A missing key raises; a non-finite value fails.

    ``declared_roles`` is treated as a claim to be checked, not as a fact: the gated roles are
    derived from which sides the book actually traded (non-zero gross PnL), and a declaration that
    disagrees fails its own gate. See the role block at the end of this function.
    """
    checks: dict[str, bool] = {
        "net_sharpe": _at_least(scored["net_sharpe"], float(floors["net_sharpe"])),
        "double_cost_sharpe": _at_least(
            scored["double_cost_sharpe"], float(floors["double_cost_sharpe"])
        ),
        "triple_cost_sharpe": _positive(scored["triple_cost_sharpe"]),
        "annualized_return": _positive(scored["annualized_return"]),
        "double_cost_annualized_return": _positive(scored["double_cost_annualized_return"]),
        "max_drawdown": _at_most(scored["max_drawdown"], float(floors["max_drawdown"])),
        # The evaluator is unlevered, so the common risk unit cannot scale a very-low-volatility
        # book up to the 10% target. This floor disqualifies an under-risked book instead of
        # rewarding it with an unearned drawdown advantage.
        "annualized_volatility": _at_least(
            scored["annualized_volatility"], float(floors["minimum_realized_volatility"])
        ),
        "positive_quarter_fraction": _at_least(
            scored["positive_quarter_fraction"], float(floors["positive_quarter_fraction"])
        ),
        "positive_fold_count": _at_least(
            scored["positive_fold_count"], float(floors["minimum_positive_folds"])
        ),
        "worst_fold_sharpe": _at_least(
            scored["worst_fold_sharpe"], float(floors["worst_fold_sharpe"])
        ),
        "annualized_turnover": _at_most(
            scored["annualized_turnover"], float(floors["max_annualized_turnover"])
        ),
        "gross_edge_bps_per_turnover": _at_least(
            scored["gross_edge_bps_per_turnover"],
            float(floors["min_gross_edge_bps_per_turnover"]),
        ),
        "cost_share_of_positive_gross": _at_most(
            scored["cost_share_of_positive_gross"],
            float(floors["max_cost_share_of_positive_gross"]),
        ),
        "top5_day_share": _at_most(scored["top5_day_share"], float(floors["max_top5_day_share"])),
        "max_fold_positive_pnl_share": _at_most(
            scored["max_fold_positive_pnl_share"],
            float(floors["max_fold_share_of_positive_pnl"]),
        ),
        "trade_count": _at_least(scored["trade_count"], float(floors["minimum_trades"])),
        "neighbourhood_positive_fraction": _at_least(
            neighbourhood_positive_fraction,
            float(research_config["neighbourhood_positive_fraction"]),
        ),
        "trial_adjusted_confidence": _at_least(
            trial_adjusted_confidence,
            float(statistics_config["minimum_trial_adjusted_confidence"]),
        ),
    }
    # ``None`` means the falsification battery has not been run for this candidate. The key is then
    # OMITTED rather than set, because a hard-coded ``False`` here reads as "the inversion did not
    # pass, so the gate is met" -- which is a measurement nobody took. Under A4 this gate is one of
    # the few that can still remove a candidate from the field, so asserting it from a default
    # would silently retire the falsification requirement altogether.
    if sign_inversion_passes_core is not None:
        checks["sign_inversion_not_profitable"] = not sign_inversion_passes_core
    # Touch every role metric so a missing key still raises, whether or not its role is declared.
    role_values = {
        "long": scored["long_gross_pnl"],
        "short": scored["short_gross_pnl"],
    }
    # A declaration is a claim, and until now it was an unchecked one: `declared_roles` arrived as
    # input and nothing bound it to what the book actually did. A long/short candidate whose short
    # sleeve lost money could declare ("long",) and the short-PnL floor would simply never be
    # evaluated -- opting out of a hard floor by describing itself differently. The roles are
    # therefore DERIVED from behaviour, using the long/short gross PnL `window_metrics` already
    # reports, and the declaration is cross-checked against them. "Traded" means MATERIALLY traded
    # -- see `_material_sides`, which exists so that dust cannot manufacture a disqualification.
    #
    # Both halves are needed, and neither subsumes the other:
    #   - gating the UNION of declared and observed means an undeclared but traded side is still
    #     gated (closes the dodge), and a declared side that came out exactly zero is still gated
    #     rather than silently dropped;
    #   - the separate agreement check catches the mis-declaration itself, in either direction --
    #     claiming a sleeve that was never traded is as much a false research certificate as hiding
    #     one that was.
    # A subscript, not `.get`, so an unrecognised role name still raises loudly rather than
    # quietly never gating anything.
    declared = tuple(dict.fromkeys(declared_roles))
    for role in declared:
        if role not in role_values:
            raise KeyError(f"unrecognised declared role: {role!r}")
    observed = _material_sides(role_values)
    checks["declared_roles_match_traded_sides"] = set(declared) == set(observed)
    for role in role_values:
        if role in declared or role in observed:
            checks[f"role_{role}_gross_pnl"] = _positive(role_values[role])
    return GateVector(checks=checks)


def evaluate_holdout_eligibility(
    scored: Mapping[str, float],
    *,
    holdout: Mapping[str, Any],
    nominated_point_double_cost_return: float,
) -> GateVector:
    """Charter section 8's winner eligibility, each row at the cost level section 8 names.

    A separate, shorter conjunction than :func:`evaluate_floors` -- section 8 lists five
    conditions, not the eighteen of section 7.3 -- so it gets its own function rather than a
    reconfigured call into the in-sample one. Sharing the in-sample gate with an overridden floors
    mapping would have quietly imported thirteen floors section 8 never states.

    Cost levels, under section 7.3's ruling that an unqualified floor is base cost:

    * ``annualized_return`` **1x** and ``double_cost_annualized_return`` **2x** -- section 8 says
      "base and 2x-cost annualised return > 0" on its face;
    * ``double_cost_sharpe`` **2x** -- "2x-cost Sharpe > 0" on its face;
    * ``max_drawdown`` **1x** -- unqualified, so base: whether the real book was survivable is a
      question about the real book;
    * ``positive_quarter_count`` **1x** -- unqualified, so base;
    * the nominated point's own **2x** return -- "the nominated point itself has positive 2x-cost
      return", the one input that is not a neighbourhood median.

    ``holdout`` is the config's ``[holdout]`` table: ``max_drawdown`` (0.25, the section 8 rebase
    of the 0.20 in-sample floor) and ``minimum_positive_quarters`` (5). Both are read from it
    rather than hard-coded, so the frozen contract governs, and both are subscripted rather than
    ``.get``-ed so a missing key raises instead of defaulting into a weaker gate.
    """
    return GateVector(
        checks={
            "annualized_return": _positive(scored["annualized_return"]),
            "double_cost_annualized_return": _positive(scored["double_cost_annualized_return"]),
            "double_cost_sharpe": _positive(scored["double_cost_sharpe"]),
            "max_drawdown": _at_most(scored["max_drawdown"], float(holdout["max_drawdown"])),
            "positive_quarter_count": _at_least(
                scored["positive_quarter_count"], float(holdout["minimum_positive_quarters"])
            ),
            "nominated_point_double_cost_return": _positive(nominated_point_double_cost_return),
        }
    )


# --- amendment A5: grading the floors the ranking score does not price -------------------------

# (gate name) -> (scored metric key, comparison, floors-table key or None for a bare "> 0")
#
# Only the floors that ``robustness_score`` has NO term for. The six it does price are excluded so
# that a single miss is not charged twice, and the two substance and two integrity gates are
# excluded because they decide admission rather than points.
#
# This table restates thresholds that ``evaluate_floors`` also reads, and a second copy that drifts
# from the first is exactly the defect class this build has closed repeatedly. It is guarded by a
# test that asserts, floor by floor, that a credit of 1.0 here agrees with a True there for the same
# metric vector -- so a divergence fails the suite rather than silently mis-scoring a team.
UNPRICED_FLOOR_SPECS: dict[str, tuple[str, str, str | None]] = {
    "net_sharpe": ("net_sharpe", ">=", "net_sharpe"),
    "double_cost_sharpe": ("double_cost_sharpe", ">=", "double_cost_sharpe"),
    "triple_cost_sharpe": ("triple_cost_sharpe", ">", None),
    "annualized_return": ("annualized_return", ">", None),
    "double_cost_annualized_return": ("double_cost_annualized_return", ">", None),
    "positive_fold_count": ("positive_fold_count", ">=", "minimum_positive_folds"),
    "annualized_turnover": ("annualized_turnover", "<=", "max_annualized_turnover"),
    "gross_edge_bps_per_turnover": (
        "gross_edge_bps_per_turnover",
        ">=",
        "min_gross_edge_bps_per_turnover",
    ),
    "cost_share_of_positive_gross": (
        "cost_share_of_positive_gross",
        "<=",
        "max_cost_share_of_positive_gross",
    ),
    "top5_day_share": ("top5_day_share", "<=", "max_top5_day_share"),
    "max_fold_positive_pnl_share": (
        "max_fold_positive_pnl_share",
        "<=",
        "max_fold_share_of_positive_pnl",
    ),
    "role_long_gross_pnl": ("long_gross_pnl", ">", None),
    "role_short_gross_pnl": ("short_gross_pnl", ">", None),
}


def _floor_credit(value: float, threshold: float, comparison: str) -> float:
    """Graded credit in ``[0, 1]`` for one floor, from that floor's own frozen threshold.

    Meeting the floor earns full credit. Missing it earns credit falling linearly with the
    *relative* shortfall, so a book 10% past a ceiling keeps 0.9 and one at twice the ceiling keeps
    nothing. Relative rather than absolute because these thresholds are stated in units that share
    no scale -- 25x turnover, 40 bps of edge, a 0.3 cost share.

    A bare ``> 0`` gate has no scale to grade against: zero has no percentage. Those are binary,
    which is honest about the fact that the charter states no magnitude for them.
    """
    number = _finite(value)
    if math.isnan(number):
        return 0.0
    met = {
        ">=": number >= threshold,
        "<=": number <= threshold,
        ">": number > threshold,
    }[comparison]
    if met:
        return 1.0
    if threshold == 0.0:
        return 0.0
    shortfall = abs(number - threshold) / abs(threshold)
    return max(0.0, 1.0 - shortfall)


def floor_credits(scored: Mapping[str, float], *, floors: Mapping[str, Any]) -> dict[str, float]:
    """One graded credit per floor the ranking score does not price."""
    credits: dict[str, float] = {}
    for gate, (metric, comparison, floor_key) in UNPRICED_FLOOR_SPECS.items():
        threshold = 0.0 if floor_key is None else float(floors[floor_key])
        credits[gate] = _floor_credit(scored[metric], threshold, comparison)
    return credits


def compliance_factor(scored: Mapping[str, float], *, floors: Mapping[str, Any]) -> float:
    """Mean credit across the unpriced floors, in ``[0, 1]``. Multiplies the ranking score (A5).

    Multiplicative, not additive, and that is the whole design. An additive block would need a
    weight for the block itself, and any weight chosen now is chosen knowing which team it helps --
    the one thing that would make this a way of picking a winner rather than of ranking one. A
    factor needs no such number: it preserves the frozen 58/35/7 relative weights exactly, leaves a
    fully compliant book's score untouched, and makes missing a floor cost something instead of
    nothing. Equal weight per floor for the same reason -- ranking them would be judgement, and
    there is no evidence to base it on that was not gathered after the results were in.
    """
    credits = floor_credits(scored, floors=floors)
    if not credits:
        return 1.0
    return sum(credits.values()) / len(credits)
