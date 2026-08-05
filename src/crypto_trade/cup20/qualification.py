"""Conjunctive hard floors. Aggregate performance never compensates for a failed floor."""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence
from typing import Any


@dataclasses.dataclass(frozen=True, slots=True)
class GateVector:
    checks: Mapping[str, bool]

    @property
    def passed(self) -> bool:
        return all(self.checks.values())

    @property
    def failures(self) -> tuple[str, ...]:
        return tuple(name for name, ok in self.checks.items() if not ok)


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
    sign_inversion_passes_core: bool,
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
        "sign_inversion_not_profitable": not sign_inversion_passes_core,
    }
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
