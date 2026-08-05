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


def _traded(value: object) -> bool:
    """Whether a side was actually used, judged from its gross PnL rather than from a declaration.

    Anything other than exactly zero counts as traded, NaN included: a side whose PnL could not be
    computed must be gated, never skipped. Exact zero is the only honest signal that a side was
    never touched -- a book that took even one position on a side and closed it at a scratch would
    have to land on 0.0 to the last bit across the whole window.
    """
    return float(value) != 0.0  # type: ignore[arg-type]


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
    # reports, and the declaration is cross-checked against them.
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
    observed = tuple(role for role, value in role_values.items() if _traded(value))
    checks["declared_roles_match_traded_sides"] = set(declared) == set(observed)
    for role in role_values:
        if role in declared or role in observed:
            checks[f"role_{role}_gross_pnl"] = _positive(role_values[role])
    return GateVector(checks=checks)
