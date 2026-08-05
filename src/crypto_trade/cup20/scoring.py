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


def robustness_score(scored: Mapping[str, float], *, drawdown_floor: float) -> float:
    """Compute ``G`` in ``[0, 100]`` from the neighbourhood-median metric vector."""
    if drawdown_floor <= 0:
        raise ValueError("drawdown_floor must be positive")
    drawdown_span = drawdown_floor - 0.05
    if drawdown_span <= 0:
        raise ValueError("drawdown_floor must exceed the 0.05 full-credit level")
    return (
        30.0 * _clamp((float(scored["worst_fold_sharpe"]) + 0.25) / 1.00)
        + 20.0 * _clamp((float(scored["median_fold_sharpe"]) - 0.25) / 0.75)
        + 20.0 * _clamp((drawdown_floor - float(scored["max_drawdown"])) / drawdown_span)
        + 15.0 * _clamp(float(scored["calmar"]) / 1.50)
        + 8.0 * _clamp((float(scored["positive_quarter_fraction"]) - 0.50) / 0.375)
        + 7.0 * _clamp((float(scored["trial_adjusted_confidence"]) - 0.90) / 0.10)
    )


def rank_entries(entries: Sequence[RankedEntry]) -> tuple[RankedEntry, ...]:
    """Descending score, then lower drawdown, higher worst fold, lower turnover, team id."""
    return tuple(
        sorted(
            entries,
            key=lambda entry: (
                -entry.score,
                float(entry.scored["max_drawdown"]),
                -float(entry.scored["worst_fold_sharpe"]),
                float(entry.scored["annualized_turnover"]),
                entry.team_id,
            ),
        )
    )


def select_advancing(entries: Sequence[RankedEntry], *, slots: int) -> tuple[RankedEntry, ...]:
    """Advance at most ``slots`` qualifiers. An empty slot is never backfilled."""
    if slots < 1:
        raise ValueError("slots must be positive")
    return rank_entries(entries)[:slots]
