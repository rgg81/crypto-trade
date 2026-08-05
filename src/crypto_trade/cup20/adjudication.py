"""Compose the hard floors with the ranking: gate first, then rank only what survived.

Section 7.3 disqualifies and section 7.4 orders, and nothing in either module knew about the
other -- ``evaluate_floors`` returned a ``GateVector`` nobody consulted before scoring, and
``robustness_score`` would happily score a candidate that had failed six floors. This module is
the composition, and it keeps the two verdicts attached to each other: a
:class:`CandidateAdjudication` always carries the gate vector, so a rejection can be read as
"failed ``max_drawdown`` and ``trade_count``" rather than as a bare absence from the leaderboard.

``score`` is ``None`` for a candidate that failed a floor -- not zero. Section 7.4 says ``G`` "is
a ranking score, not an additional veto", and the converse holds as well: a number attached to a
disqualified candidate invites exactly the comparison the floors exist to forbid.
"""

from __future__ import annotations

import dataclasses
import math
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

from crypto_trade.cup20.qualification import GateVector, evaluate_floors
from crypto_trade.cup20.scored_metrics import ASSEMBLED_METRIC_KEYS, ranking_metrics
from crypto_trade.cup20.scoring import (
    RankedEntry,
    rank_entries,
    robustness_score,
    select_advancing,
)


@dataclasses.dataclass(frozen=True, slots=True)
class CandidateAdjudication:
    """One candidate's complete verdict: what it scored, what it passed, and where it ranks."""

    team_id: str
    candidate_id: str
    scored: Mapping[str, float]
    ranking_inputs: Mapping[str, float]
    gates: GateVector
    score: float | None

    @property
    def qualified(self) -> bool:
        return self.gates.passed

    @property
    def failures(self) -> tuple[str, ...]:
        return self.gates.failures

    def as_ranked_entry(self) -> RankedEntry:
        """The ranking view of this candidate. Only a floor-passer has one.

        ``RankedEntry.scored`` carries the 2x ranking inputs rather than the assembled vector,
        because ``rank_entries`` reads its tie-breaks off that mapping and section 7.4 puts every
        one of them at 2x cost. Handing it the assembled vector would tie-break on the 1x
        drawdown while ``G`` scored the 2x one.
        """
        if self.score is None:
            raise ValueError(
                f"candidate {self.team_id}/{self.candidate_id} failed "
                f"{list(self.failures)}; only floor-passers are ranked"
            )
        return RankedEntry(
            team_id=self.team_id,
            candidate_id=self.candidate_id,
            score=self.score,
            scored=self.ranking_inputs,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class Adjudication:
    """The whole population's verdict, in one object."""

    candidates: tuple[CandidateAdjudication, ...]
    ranked: tuple[CandidateAdjudication, ...]
    advancing: tuple[CandidateAdjudication, ...]

    @property
    def rejected(self) -> tuple[CandidateAdjudication, ...]:
        return tuple(candidate for candidate in self.candidates if not candidate.qualified)


def adjudicate_candidate(
    scored: Mapping[str, float],
    *,
    team_id: str,
    candidate_id: str,
    floors: Mapping[str, Any],
    statistics_config: Mapping[str, Any],
    research_config: Mapping[str, Any],
    declared_roles: Sequence[str],
    sign_inversion_passes_core: bool,
    neighbourhood_positive_fraction: float,
    trial_adjusted_confidence: float,
    drawdown_floor: float,
) -> CandidateAdjudication:
    """Gate one candidate on the floors, then score it only if it passed.

    ``scored`` is the neighbourhood-median assembled vector (see
    :func:`crypto_trade.cup20.scored_metrics.assemble_scored_metrics` and
    :func:`~crypto_trade.cup20.scored_metrics.neighbourhood_median`).

    ``drawdown_floor`` is passed explicitly rather than read out of ``floors`` because the holdout
    rebases that one term to 0.25 (section 8) while every other input keeps its section 7.3
    meaning; a caller that silently inherited ``floors["max_drawdown"]`` would score the holdout
    on the in-sample scale without anything saying so.
    """
    missing = sorted(ASSEMBLED_METRIC_KEYS - set(scored))
    if missing:
        raise ValueError(
            f"candidate {team_id}/{candidate_id}: the scored vector is missing {missing}; "
            "it must be an assembled metric vector, whose cost levels are the frozen policy"
        )
    gates = evaluate_floors(
        scored,
        floors=floors,
        statistics_config=statistics_config,
        research_config=research_config,
        declared_roles=declared_roles,
        sign_inversion_passes_core=sign_inversion_passes_core,
        neighbourhood_positive_fraction=neighbourhood_positive_fraction,
        trial_adjusted_confidence=trial_adjusted_confidence,
    )
    inputs = ranking_metrics(scored, trial_adjusted_confidence=trial_adjusted_confidence)
    if not gates.passed:
        return CandidateAdjudication(
            team_id=team_id,
            candidate_id=candidate_id,
            scored=dict(scored),
            ranking_inputs=inputs,
            gates=gates,
            score=None,
        )
    # A ranking input can be non-finite while every floor passed, because two of the three 2x
    # ranking twins (`double_cost_max_drawdown`, `double_cost_positive_quarter_fraction`,
    # `double_cost_annualized_turnover`) are gated by no floor at all. Left alone, that surfaces
    # much later as a ValueError from `_finite_tie_break` in the middle of sorting the whole
    # population -- an unattributed failure of the ranking rather than a named failure of one
    # candidate. It is an organiser-side fault either way, so it raises rather than becoming a
    # verdict, but it raises HERE, naming the team, the candidate and the metric.
    non_finite = sorted(key for key, value in inputs.items() if not math.isfinite(value))
    if non_finite:
        raise ValueError(
            f"candidate {team_id}/{candidate_id} passed every floor but its ranking inputs "
            f"are not finite: {non_finite}"
        )
    return CandidateAdjudication(
        team_id=team_id,
        candidate_id=candidate_id,
        scored=dict(scored),
        ranking_inputs=inputs,
        gates=gates,
        score=robustness_score(inputs, drawdown_floor=drawdown_floor),
    )


def adjudicate_population(
    candidates: Sequence[CandidateAdjudication], *, slots: int
) -> Adjudication:
    """Rank the floor-passers and take the top ``slots``. A failed candidate is never ranked.

    Duplicate team ids are rejected. Section 7.5 gives each team exactly one nominated identity,
    and section 7.4's final tie-break is the team id -- with two entries sharing one, the
    tie-break chain can be exhausted with the order still undecided, and the result would fall
    back to input order. ``rank_entries`` documents that the ranking must be a total order with no
    dependence on input sequence; this is what makes that true of a population rather than only of
    a pair.
    """
    ordered = tuple(candidates)
    counts = Counter(candidate.team_id for candidate in ordered)
    duplicates = sorted(team_id for team_id, count in counts.items() if count > 1)
    if duplicates:
        raise ValueError(
            f"each team nominates exactly one identity; these appear more than once: {duplicates}"
        )
    passers = {(c.team_id, c.candidate_id): c for c in ordered if c.qualified}
    entries = rank_entries([candidate.as_ranked_entry() for candidate in passers.values()])
    advancing = select_advancing(entries, slots=slots)
    return Adjudication(
        candidates=ordered,
        ranked=tuple(passers[(entry.team_id, entry.candidate_id)] for entry in entries),
        advancing=tuple(passers[(entry.team_id, entry.candidate_id)] for entry in advancing),
    )
