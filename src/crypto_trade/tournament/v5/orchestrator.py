"""Nomination, the sealed bar, and selection -- with no way to fill an empty bracket.

This is where V4-R9 actually failed, and the failure is worth stating precisely because the fix is
shaped by it. Two independent defects compounded:

**The eligibility raise was patched into unreachability.** ``nominate`` was changed to
``if not field_adjustment and not eligible: raise``, and ``field_adjustment`` was ``True`` for that
edition -- so the raise never fired. Meanwhile the config declared
``lower_floors_to_fill_bracket = false`` and the contract validator dutifully confirmed it. The
promise was validated; the code had been patched to break it.

**The fallback ranked by worst-fold Sharpe**, which rewards inactivity. A book running 3.7% mean
gross exposure and 1.39x annual turnover, failing thirteen of twenty-two gates, scored exactly 0.000
and ranked first. That is not a bug in the fallback -- it is the ranking key working as written.

Three structural choices follow, and each is a shape rather than a rule:

* :func:`nominate` raises **unconditionally** when a candidate is not eligible. There is no
  parameter that suppresses it, so there is nothing for a later edit to set to ``True``.
* :func:`select` takes no minimum count, no fallback list and no floor. An empty field is
  ``advancing=()`` and the type permits it. You cannot ask this function to fill a bracket, because
  there is no argument with which to ask.
* Ranking is by **robustness on sealed data** -- the contiguous block-deletion fifth percentile --
  which a near-flat book cannot win: deleting any thirty days of a book that barely trades leaves a
  Sharpe near zero, not a high one.

Qualification is a **bar, not a rank cut**. Every candidate clearing the development gates is
observed on the sealed blocks; every candidate clearing the sealed bar is observed on the historical
window. No top-N cut precedes either stage, which is what keeps the sealed data a bar rather than a
competition and leaves the field's null distribution estimable.
"""

from __future__ import annotations

import dataclasses
import math
from collections.abc import Mapping, Sequence

import numpy as np
import pandas as pd

from crypto_trade.tournament.v5 import journal, statistics
from crypto_trade.tournament.v5.runner import DevelopmentTrial, SealedConfirmation

# The deliverable: the top three individual candidates plus an equal-weight ensemble of those three.
DESK_INDIVIDUAL_COUNT = 3
ENSEMBLE_DESK = "ensemble-eq3"

# Two candidates are tied when the confidence interval of their *paired* daily-return difference
# contains zero. Paired, because the market factor largely cancels; marginal standard errors over
# 2.5 years are about 0.63 and would make the rule vacuous.
TIE_CONFIDENCE = 0.90


class OrchestratorError(RuntimeError):
    """An action the edition does not permit, or a state it does not represent."""


def nominate(
    journal_path: str,
    trial: DevelopmentTrial,
    *,
    candidate_id: str,
) -> None:
    """Record a nomination. Raises if the candidate is not eligible.

    Unconditionally. There is no ``force``, no ``field_adjustment``, no ``allow_ineligible`` -- the
    absence of such a parameter is the guarantee, because V4-R9's fallback was reached by setting
    exactly such a flag and the resulting run had no valid winner.
    """

    if not trial.admitted:
        raise OrchestratorError(
            f"{trial.team_id} candidate {candidate_id} failed enforced gates "
            f"{list(trial.assessment.failures())} and cannot be nominated"
        )
    journal.append(
        journal_path,
        "nominated",
        {
            "team_id": trial.team_id,
            "candidate_id": candidate_id,
            "trial_id": trial.trial_id,
            "gates": dict(trial.assessment.gates),
        },
    )


def retire(journal_path: str, team_id: str, *, reason: str) -> None:
    """A lane that produced nothing eligible retires, and says so.

    Retirement is a normal outcome, recorded plainly. A team with no eligible candidate is not a
    problem to be worked around at selection time.
    """

    journal.append(journal_path, "retired", {"team_id": team_id, "reason": reason})


@dataclasses.dataclass(frozen=True, slots=True)
class Desk:
    """A forward paper desk. Four of these carry the result."""

    name: str
    constituents: tuple[str, ...]
    weights: Mapping[str, float]


@dataclasses.dataclass(frozen=True, slots=True)
class Selection:
    """The outcome of selection, including the outcome where nobody advances."""

    advancing: tuple[str, ...]
    ranked: tuple[tuple[str, float], ...]
    ties: tuple[tuple[str, str], ...]
    desks: tuple[Desk, ...]

    @property
    def empty(self) -> bool:
        return not self.advancing

    def as_dict(self) -> dict[str, object]:
        return {
            "advancing": list(self.advancing),
            "ranked": [{"candidate": name, "robustness": value} for name, value in self.ranked],
            "ties": [list(pair) for pair in self.ties],
            "desks": [
                {"name": desk.name, "constituents": list(desk.constituents)} for desk in self.desks
            ],
            "empty": self.empty,
        }


def _paired_difference_contains_zero(
    left: pd.Series, right: pd.Series, *, confidence: float = TIE_CONFIDENCE
) -> bool:
    """Whether two candidates are statistically indistinguishable.

    On the *paired* daily difference. Over 2.5 years the standard error of a Sharpe is about 0.63,
    so comparing marginal estimates would declare almost everything tied; pairing cancels the common
    market factor and leaves the part that actually differs.
    """

    aligned = pd.concat([left, right], axis=1, join="inner").dropna()
    if len(aligned) < 30:
        return True
    difference = aligned.iloc[:, 0] - aligned.iloc[:, 1]
    deviation = float(difference.std(ddof=1))
    if deviation <= 0.0:
        return True
    standard_error = deviation / math.sqrt(len(difference))
    critical = statistics.normal_quantile(0.5 + confidence / 2.0)
    margin = critical * standard_error
    return abs(float(difference.mean())) <= margin


def select(
    cleared: Sequence[SealedConfirmation],
    *,
    daily_returns: Mapping[str, pd.Series] | None = None,
) -> Selection:
    """Rank the candidates that cleared the sealed bar, and form the four desks.

    Note the signature. There is no minimum count, no fallback pool, no floor to relax and no
    ``fill_bracket``. An empty ``cleared`` produces ``advancing=()`` and no desks at all, which is
    a supported terminal state rather than an error -- ``test_an_empty_field_is_a_valid_outcome``
    exists precisely so the path is exercised, because in V4-R9 it was untested, looked like a bug
    under pressure, and acquired a fallback.
    """

    qualified = [confirmation for confirmation in cleared if confirmation.cleared]
    if not qualified:
        return Selection(advancing=(), ranked=(), ties=(), desks=())

    # Robustness, not performance: the block-deletion fifth percentile. A near-flat book cannot win
    # this the way it wins a worst-fold Sharpe -- deleting any month of a book that barely trades
    # leaves a Sharpe near zero rather than a high one.
    ranked = sorted(
        (
            (f"{item.team_id}:{item.candidate_id}", item.packet.deletion_profile_p05_sharpe)
            for item in qualified
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )
    advancing = tuple(name for name, _ in ranked)

    ties: list[tuple[str, str]] = []
    if daily_returns:
        for index in range(len(ranked) - 1):
            left, right = ranked[index][0], ranked[index + 1][0]
            if left in daily_returns and right in daily_returns:
                if _paired_difference_contains_zero(daily_returns[left], daily_returns[right]):
                    ties.append((left, right))

    top = advancing[:DESK_INDIVIDUAL_COUNT]
    desks = [Desk(name=name, constituents=(name,), weights={name: 1.0}) for name in top]
    if len(top) == DESK_INDIVIDUAL_COUNT:
        # Equal weights, not risk parity: three constituents and nothing to tune. If two land in the
        # same economic family that is a finding the release reports, not something to substitute
        # around.
        share = 1.0 / DESK_INDIVIDUAL_COUNT
        desks.append(
            Desk(name=ENSEMBLE_DESK, constituents=top, weights={name: share for name in top})
        )

    return Selection(
        advancing=advancing, ranked=tuple(ranked), ties=tuple(ties), desks=tuple(desks)
    )


def freeze_selection(journal_path: str, selection: Selection) -> None:
    """Bind the selection into the journal before anything reads it as a result."""

    journal.append(journal_path, "selection_frozen", selection.as_dict())


def expected_field_maximum(trial_count: int, dispersion: float) -> float:
    """The Sharpe a field of this size produces under the null, published beside the leaderboard.

    Reported, never gated. Fifteen teams each submitting their best does bias the field maximum
    upward, and a reader is entitled to price that. Using it as a bar is a different matter: at a
    360-day window a genuinely good book yields p-values around 0.15-0.30, and a false-discovery
    correction across fifteen nominees selects roughly half a team. That is V4-R2's unpassable gate
    in a new costume, and this edition declines to repeat it.
    """

    return statistics.expected_maximum_sharpe(trial_count, dispersion)


def assert_selection_is_honest(selection: Selection, cleared: Sequence[SealedConfirmation]) -> None:
    """Nothing advanced that did not clear the bar on its own evidence.

    The check exists because the failure it catches is invisible in the output: a promoted candidate
    and a qualified one look identical in a leaderboard.
    """

    qualified = {f"{item.team_id}:{item.candidate_id}" for item in cleared if item.cleared}
    promoted = set(selection.advancing) - qualified
    if promoted:
        raise OrchestratorError(
            f"candidates advanced without clearing the sealed bar: {sorted(promoted)}"
        )
    if len(selection.desks) > DESK_INDIVIDUAL_COUNT + 1:
        raise OrchestratorError(f"selection produced {len(selection.desks)} desks; at most four")


def sign_randomised_null_band(
    returns: pd.Series, *, draws: int = 2000, seed: int = 20260826
) -> tuple[float, float]:
    """The central 80% Sharpe band of sign-randomised replays of a candidate's own returns.

    Run after release. A candidate whose historical Sharpe falls inside this band is labelled
    ``indistinguishable-from-null``, which is a statement the leaderboard cannot make on its own.
    """

    values = returns.to_numpy(dtype=float)
    if values.size < 30:
        raise OrchestratorError("too few observations for a null band")
    generator = np.random.default_rng(seed)
    sharpes = [
        statistics.sharpe_ratio(
            values * generator.choice((-1.0, 1.0), size=values.size), annualised=True
        )
        for _ in range(draws)
    ]
    return float(np.percentile(sharpes, 10)), float(np.percentile(sharpes, 90))


__all__ = [
    "DESK_INDIVIDUAL_COUNT",
    "ENSEMBLE_DESK",
    "TIE_CONFIDENCE",
    "Desk",
    "OrchestratorError",
    "Selection",
    "assert_selection_is_honest",
    "expected_field_maximum",
    "freeze_selection",
    "nominate",
    "retire",
    "select",
    "sign_randomised_null_band",
]
