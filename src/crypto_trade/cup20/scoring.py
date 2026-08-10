"""Generalisation-shaped ranking score.

Fifty-eight of one hundred points reward consistency across chronological folds, thirty-five
reward drawdown control, and seven reward multiplicity honesty. The score ranks; it never vetoes.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence


def _clamp(value: float) -> float:
    """Clamp a normalised score component to ``[0, 1]``.

    Every component is oriented so that larger is better, so a positive infinity means "as good
    as this term can be" and must earn full credit, not zero. NaN and negative infinity earn
    nothing. Metrics are expected to be finite by the time they arrive here — this is
    defence in depth, not a licence for upstream to emit infinities.
    """
    if math.isnan(value):
        return 0.0
    if value == math.inf:
        return 1.0
    if value == -math.inf:
        return 0.0
    return min(1.0, max(0.0, value))


@dataclasses.dataclass(frozen=True, slots=True)
class RankedEntry:
    team_id: str
    candidate_id: str
    score: float
    scored: Mapping[str, float]


def _decaying(normalised: float) -> float:
    """``_clamp`` for a term that must keep ordering books after it stops earning credit.

    ``_clamp`` floors at zero, which makes the term blind past its own threshold: a book at 21%
    drawdown and one at 95% both scored exactly 41.789, and a worst fold of -0.26 scored the same
    as -40.0. A ranking that cannot order two books is not ranking them -- it hands the decision to
    whatever tie-break happens to run next, and only when the other terms happen to agree exactly.

    Above the threshold the value is unchanged, so every score measured under the earlier formula
    for a compliant book still stands. Below it the term decays hyperbolically into ``(-1, 0)``:
    strictly decreasing forever, never reaching -1, so an arbitrarily bad book always ranks below a
    merely bad one and no single term can swamp the other five.
    """
    if math.isnan(normalised):
        return 0.0
    if normalised == math.inf:
        return 1.0
    if normalised >= 0.0:
        return min(1.0, normalised)
    if normalised == -math.inf:
        return -1.0
    shortfall = -normalised
    return -shortfall / (shortfall + 1.0)


def robustness_score(scored: Mapping[str, float], *, drawdown_floor: float) -> float:
    """Compute ``G`` from the neighbourhood-median metric vector.

    Bounded above by 100 and, since amendment A5's decaying tails, unbounded below by a finite
    limit of -100 -- a book worse than every threshold on every term. Only the ordering matters.
    """
    if drawdown_floor <= 0:
        raise ValueError("drawdown_floor must be positive")
    drawdown_span = drawdown_floor - 0.05
    if drawdown_span <= 0:
        raise ValueError("drawdown_floor must exceed the 0.05 full-credit level")
    return (
        30.0 * _decaying((float(scored["worst_fold_sharpe"]) + 0.25) / 1.00)
        + 20.0 * _decaying((float(scored["median_fold_sharpe"]) - 0.25) / 0.75)
        + 20.0 * _decaying((drawdown_floor - float(scored["max_drawdown"])) / drawdown_span)
        + 15.0 * _decaying(float(scored["calmar"]) / 1.50)
        + 8.0 * _decaying((float(scored["positive_quarter_fraction"]) - 0.50) / 0.375)
        + 7.0 * _decaying((float(scored["trial_adjusted_confidence"]) - 0.90) / 0.10)
    )


def _finite_tie_break(entry: RankedEntry, field: str) -> float:
    """Read a tie-break metric, failing loudly rather than sorting on it if it isn't finite.

    Unlike the six ``robustness_score`` components, a tie-break metric is never routed through
    ``_clamp``: it is a raw comparison key, and NaN in particular is not a total order (``nan <
    x`` and ``x < nan`` are both False), so it can silently make the resulting ranking depend on
    input order — the ranking must be a total order with no dependence on input sequence, no
    exception carved out for "upstream should have filtered this." Rather than invent a NaN/
    ``+inf``/``-inf`` ordering policy across three differently-oriented fields, this fails
    closed the same way ``qualification.py`` does for the hard floors: a non-finite value fails.
    """
    value = float(entry.scored[field])
    if not math.isfinite(value):
        raise ValueError(
            f"team {entry.team_id!r}: tie-break metric {field!r} is not finite: {value!r}"
        )
    return value


def rank_entries(entries: Sequence[RankedEntry]) -> tuple[RankedEntry, ...]:
    """Descending score, then lower drawdown, higher worst fold, lower turnover, team id."""
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.score,
                _finite_tie_break(entry, "max_drawdown"),
                -_finite_tie_break(entry, "worst_fold_sharpe"),
                _finite_tie_break(entry, "annualized_turnover"),
                entry.team_id,
            ),
        )
    )


def select_advancing(entries: Sequence[RankedEntry], *, slots: int) -> tuple[RankedEntry, ...]:
    """Advance at most ``slots`` qualifiers. An empty slot is never backfilled."""
    if slots < 1:
        raise ValueError("slots must be positive")
    return rank_entries(entries)[:slots]
