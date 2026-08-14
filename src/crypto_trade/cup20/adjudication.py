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

from crypto_trade.cup20.qualification import (
    GateVector,
    compliance_factor,
    evaluate_floors,
    evaluate_holdout_eligibility,
    holdout_compliance_factor,
)
from crypto_trade.cup20.scored_metrics import (
    ASSEMBLED_METRIC_KEYS,
    STAGE_HOLDOUT,
    STAGE_IN_SAMPLE,
    ScoredVector,
    ranking_metrics,
)
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
    stage: str = "in_sample"

    @property
    def qualified(self) -> bool:
        """Every floor met, conjunctively. What the holdout stage decides on."""
        return self.gates.passed

    @property
    def admissible(self) -> bool:
        """Eligible to be ranked -- and STAGE-AWARE, which is not a nicety.

        A4 is an in-sample ruling. The holdout gate vector contains neither integrity key nor
        either substance key, so asking ``GateVector.admissible`` about it returns False for a
        flawless finalist: it would drop every holdout candidate from the population and report a
        perfect book as an integrity failure. The two stages ask different questions and must
        consult different gates.
        """
        if self.stage == "holdout":
            # A7: every finalist is rankable. Integrity was established in-sample -- the holdout
            # observation is a neighbourhood sweep and runs no falsification battery, so there is
            # no integrity verdict to take here and nothing to fail closed on.
            return True
        if self.stage != "in_sample":
            raise ValueError(f"unknown adjudication stage: {self.stage!r}")
        return self.gates.admissible

    @property
    def failures(self) -> tuple[str, ...]:
        return self.gates.failures

    def as_ranked_entry(self) -> RankedEntry:
        """The ranking view of this candidate. Only an admissible candidate has one.

        ``RankedEntry.scored`` carries the 2x ranking inputs rather than the assembled vector,
        because ``rank_entries`` reads its tie-breaks off that mapping and section 7.4 puts every
        one of them at 2x cost. Handing it the assembled vector would tie-break on the 1x
        drawdown while ``G`` scored the 2x one.
        """
        if self.score is None or not self.admissible:
            raise ValueError(
                f"candidate {self.team_id}/{self.candidate_id} is not admissible: "
                f"failed {list(self.gates.admission_failures)}, "
                f"unmeasured {list(self.gates.unmeasured_admission_gates)}; "
                "only admissible candidates are ranked"
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
        """Candidates outside the ranking entirely -- an integrity failure, never a weak result.

        Keyed on ``admissible`` rather than ``qualified`` since A4: a candidate that missed a
        performance floor is ranked, so calling it "rejected" would put the same team in both
        ``ranked`` and ``rejected`` at once. ``admissible`` is stage-aware, so this stays correct
        for a holdout population too.
        """
        return tuple(candidate for candidate in self.candidates if not candidate.admissible)


def _require_assembled_vector(
    scored: Mapping[str, float], *, stage: str, subject: str
) -> ScoredVector:
    """Refuse to adjudicate metrics that cannot prove which stage produced them.

    ``ASSEMBLED_METRIC_KEYS`` checks the SHAPE of a vector and nothing about its origin, so every
    stage produces the same twenty-six keys and a vector from the wrong window passes that check
    untouched. This is the check that closes it: a caller that assembled in-sample metrics --
    correct window, correct folds, correct cost levels, every value finite -- and handed them to
    the holdout adjudicator would otherwise have section 8's five conditions and ``G`` evaluated
    against four years of research data, and nothing anywhere would raise. The wrong-window verdict
    would simply be published.

    A bare ``Mapping`` is refused rather than trusted. It may well be a correct vector, but the
    only thing that makes it usable as evidence is a claim about where it came from, and it makes
    no claim at all -- so the fail-closed direction is to reject it and require the caller to route
    through :func:`~crypto_trade.cup20.scored_metrics.assemble_scored_metrics`, which is the one
    place that knows.
    """
    if not isinstance(scored, ScoredVector):
        raise ValueError(
            f"{subject}: the scored vector carries no provenance, so it cannot be shown to have "
            f"come from the {stage} stage. Assemble it with assemble_scored_metrics(stage="
            f"{stage!r}, ...) rather than building the mapping by hand."
        )
    if scored.provenance.stage != stage:
        raise ValueError(
            f"{subject}: these metrics were assembled for the {scored.provenance.stage!r} stage "
            f"({scored.provenance.describe()}), but they are being adjudicated as {stage!r}"
        )
    return scored


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
    scored = _require_assembled_vector(
        scored, stage=STAGE_IN_SAMPLE, subject=f"candidate {team_id}/{candidate_id}"
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
    # Amendment A4: a missed performance floor costs points, not the tournament. Only an integrity
    # failure -- a result the falsifier reproduces, or a certificate that misdescribes what the book
    # traded -- leaves a candidate unranked, because those say the evidence is not what it claims
    # and no ranking can repair that. The holdout stage below is deliberately NOT changed: it asks
    # whether a book is good enough to deploy, not which book is best, and section 1.1 keeps "no
    # winner" as a permitted outcome there.
    # Only a MEASURED admission failure withholds the score. An unmeasured one -- a sweep cannot
    # decide sign inversion, which is its own material trial -- still gets its indicative G, because
    # that number is what a team reads off its own sweep, and refusing it would make the whole
    # sweep report useless while the falsification trial is still outstanding. It is not rankable
    # either way: `admissible` requires every admission gate measured AND met, and
    # `as_ranked_entry` refuses on that, not on the score.
    if gates.refuted:
        return CandidateAdjudication(
            team_id=team_id,
            candidate_id=candidate_id,
            scored=scored,
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
            f"candidate {team_id}/{candidate_id} is not refuted but its ranking inputs "
            f"are not finite: {non_finite}"
        )
    return CandidateAdjudication(
        team_id=team_id,
        candidate_id=candidate_id,
        scored=scored,
        ranking_inputs=inputs,
        gates=gates,
        # Amendment A5. The floors robustness_score has no term for used to cost nothing at all, so
        # "a miss costs points" was true for six of them and false for thirteen. The factor prices
        # the rest without touching the frozen 58/35/7 weights: a fully compliant book multiplies by
        # 1.0 and is unchanged. Read at BASE cost, per section 7.3's ruling that an unqualified
        # floor is a 1x floor -- the ranking inputs are 2x and these are not ranking inputs.
        score=robustness_score(inputs, drawdown_floor=drawdown_floor)
        * compliance_factor(scored, floors=floors),
    )


def adjudicate_holdout_candidate(
    scored: Mapping[str, float],
    *,
    team_id: str,
    candidate_id: str,
    holdout: Mapping[str, Any],
    trial_adjusted_confidence: float,
    nominated_point_double_cost_return: float,
) -> CandidateAdjudication:
    """Section 8's verdict for one finalist: eligibility first, then ``G`` on holdout metrics.

    The same gate-then-score shape as :func:`adjudicate_candidate`, over section 8's own five
    eligibility conditions rather than section 7.3's eighteen floors, and with the drawdown term
    of ``G`` rebased to the section 8 floor. ``drawdown_floor`` is read from the ``[holdout]``
    table here rather than being an argument the caller has to remember, because at this stage
    there is exactly one right answer and section 8 states it.

    ``scored`` must be assembled over the SEALED window with ``holdout_folds`` -- the fold terms
    of ``G`` are "computed over four 6-month holdout blocks" -- and that is now VERIFIED here
    rather than assumed of the caller. ``assemble_scored_metrics`` enforces that its folds tile the
    window it was handed, which catches holdout folds against the in-sample window; it does not,
    and cannot, catch the in-sample window paired with in-sample folds, because that combination is
    internally consistent and produces a perfectly well-formed vector of the wrong four years.
    :func:`_require_assembled_vector` is what closes it: the stage the vector was assembled for
    travels with the numbers, and a vector assembled as ``in_sample`` is refused here by name.
    """
    missing = sorted(ASSEMBLED_METRIC_KEYS - set(scored))
    if missing:
        raise ValueError(
            f"finalist {team_id}/{candidate_id}: the scored vector is missing {missing}; "
            "it must be an assembled metric vector, whose cost levels are the frozen policy"
        )
    scored = _require_assembled_vector(
        scored, stage=STAGE_HOLDOUT, subject=f"finalist {team_id}/{candidate_id}"
    )
    gates = evaluate_holdout_eligibility(
        scored,
        holdout=holdout,
        nominated_point_double_cost_return=nominated_point_double_cost_return,
    )
    inputs = ranking_metrics(scored, trial_adjusted_confidence=trial_adjusted_confidence)
    # Amendment A7: the holdout RANKS rather than gates. Section 8's six eligibility conditions are
    # still evaluated, still reported and still travel with the verdict -- what changed is that
    # missing one costs points through `compliance_factor` instead of removing a finalist from
    # contention. Every finalist therefore carries a score, and the winner is the highest of them.
    #
    # Recorded prospectively: this was ruled BEFORE the sealed window had been restored, so no
    # holdout number existed when the rule changed. That is the condition section 13 imposes, and
    # it is the whole reason the ruling is admissible at all.
    non_finite = sorted(key for key, value in inputs.items() if not math.isfinite(value))
    if non_finite:
        raise ValueError(
            f"finalist {team_id}/{candidate_id} has non-finite ranking inputs: {non_finite}"
        )
    return CandidateAdjudication(
        team_id=team_id,
        candidate_id=candidate_id,
        scored=scored,
        ranking_inputs=inputs,
        gates=gates,
        score=robustness_score(inputs, drawdown_floor=float(holdout["max_drawdown"]))
        * holdout_compliance_factor(gates),
        stage="holdout",
    )


def adjudicate_population(
    candidates: Sequence[CandidateAdjudication], *, slots: int
) -> Adjudication:
    """Rank the admissible candidates and take the top ``slots`` (amendment A4).

    A missed performance floor costs points and is reported; it no longer removes a candidate from
    the field. Only an integrity failure does. A twenty-two-floor conjunction meant one miss out of
    twenty-two discarded a book entirely -- which is how a candidate positive in all four folds,
    positive on both sleeves and inside every risk limit came to score nothing at all.

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
    passers = {(c.team_id, c.candidate_id): c for c in ordered if c.admissible}
    entries = rank_entries([candidate.as_ranked_entry() for candidate in passers.values()])
    advancing = select_advancing(entries, slots=slots)
    return Adjudication(
        candidates=ordered,
        ranked=tuple(passers[(entry.team_id, entry.candidate_id)] for entry in entries),
        advancing=tuple(passers[(entry.team_id, entry.candidate_id)] for entry in advancing),
    )
