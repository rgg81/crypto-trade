"""Tests for the composition of the hard floors with the ranking.

Two mutations dominate this file:

* scoring a candidate that failed a floor, or dropping a passer -- the composition existing at
  all is what prevents both, and every ranking assertion here is written so that a driver which
  ranked everything, or nothing, fails;
* handing ``robustness_score`` and ``rank_entries`` the 1x floor values instead of the 2x ranking
  twins. The passing fixture below therefore gives the 1x and 2x values of all three shared
  metrics DELIBERATELY DIFFERENT numbers, so every scoring and tie-break assertion discriminates
  between them. A fixture where ``max_drawdown`` and ``double_cost_max_drawdown`` agreed would
  pass whichever one the driver read.
"""

import dataclasses
import math

import pandas as pd
import pytest

from crypto_trade.cup20.adjudication import (
    CandidateAdjudication,
    adjudicate_candidate,
    adjudicate_holdout_candidate,
    adjudicate_population,
)
from crypto_trade.cup20.config import IS_END, SEALED_END, SEALED_START, load_config
from crypto_trade.cup20.metrics import holdout_folds, is_folds
from crypto_trade.cup20.qualification import GateVector
from crypto_trade.cup20.scored_metrics import (
    ASSEMBLED_METRIC_KEYS,
    STAGE_HOLDOUT,
    STAGE_IN_SAMPLE,
    MetricProvenance,
    ScoredVector,
    ranking_metrics,
)
from crypto_trade.cup20.scoring import robustness_score

IS_START = pd.Timestamp("2020-08-01T00:00:00Z")

# The adjudicators refuse a bare mapping, so every fixture here has to declare which stage it came
# from -- exactly as a real caller does, by routing through `assemble_scored_metrics`. Building the
# provenance directly keeps this file's fixtures hand-written (its whole point is pinning the 1x
# and 2x twins to different values) without reopening the hole those fixtures would otherwise
# drive straight through.


def _vector(metrics, stage=STAGE_IN_SAMPLE):
    if stage == STAGE_HOLDOUT:
        window, folds = (SEALED_START, SEALED_END), holdout_folds(SEALED_START, SEALED_END)
    else:
        window, folds = (IS_START, IS_END), is_folds(IS_START, IS_END)
    return ScoredVector(
        metrics,
        MetricProvenance(stage=stage, window_start=window[0], window_end=window[1], folds=folds),
    )


CONFIG = load_config("tournament/cup20/config.toml").raw
DRAWDOWN_FLOOR = float(CONFIG["floors"]["max_drawdown"])

# The 1x floor values and the 2x ranking values differ on every shared metric, on purpose.
PASSING = {
    # --- section 7.3 floors -----------------------------------------------------------------
    "net_sharpe": 1.20,  # 1x
    "double_cost_sharpe": 0.95,  # 2x
    "triple_cost_sharpe": 0.60,  # 3x
    "annualized_return": 0.18,  # 1x
    "double_cost_annualized_return": 0.14,  # 2x
    "max_drawdown": 0.12,  # 1x
    "annualized_volatility": 0.10,  # 1x
    "positive_quarter_fraction": 0.69,  # 1x
    "positive_fold_count": 4.0,  # 2x
    "worst_fold_sharpe": 0.35,  # 2x
    "annualized_turnover": 14.0,  # 1x
    "gross_edge_bps_per_turnover": 95.0,  # 1x
    "cost_share_of_positive_gross": 0.11,  # 1x
    "top5_day_share": 0.22,  # 1x
    "max_fold_positive_pnl_share": 0.38,  # 1x
    "trade_count": 3100.0,  # 1x
    "long_gross_pnl": 0.22,  # 1x
    "short_gross_pnl": 0.15,  # 1x
    # --- section 7.4 ranking inputs ----------------------------------------------------------
    "median_fold_sharpe": 0.60,  # 2x
    "calmar": 1.10,  # 2x
    "double_cost_max_drawdown": 0.16,  # 2x twin of the 0.12 floor value
    "double_cost_positive_quarter_fraction": 0.56,  # 2x twin of the 0.69 floor value
    "double_cost_annualized_turnover": 16.0,  # 2x twin of the 14.0 floor value
    # --- section 8 holdout eligibility --------------------------------------------------------
    "positive_quarter_count": 7.0,  # 1x
}
CONFIDENCE = 0.97


def _adjudicate(scored=None, *, team_id="team-01", candidate_id="c1", **overrides):
    kwargs = {
        "declared_roles": ("long", "short"),
        "sign_inversion_passes_core": False,
        "neighbourhood_positive_fraction": 0.86,
        "trial_adjusted_confidence": CONFIDENCE,
    }
    metrics = dict(PASSING if scored is None else scored)
    for key, value in overrides.items():
        if key in kwargs:
            kwargs[key] = value
        else:
            metrics[key] = value
    return adjudicate_candidate(
        _vector(metrics),
        team_id=team_id,
        candidate_id=candidate_id,
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        drawdown_floor=DRAWDOWN_FLOOR,
        **kwargs,
    )


def test_the_fixture_gives_the_one_x_and_two_x_twins_different_values():
    # Without this, every cost-level assertion below is satisfied by either reading.
    for floor_key in ("max_drawdown", "positive_quarter_fraction", "annualized_turnover"):
        assert PASSING[floor_key] != PASSING[f"double_cost_{floor_key}"], floor_key


def test_the_fixture_key_set_is_the_assembled_contract():
    assert set(PASSING) == ASSEMBLED_METRIC_KEYS


# --- a verdict carries both halves ------------------------------------------------------------


def test_a_passing_candidate_carries_the_gate_vector_and_a_score():
    verdict = _adjudicate()
    assert verdict.qualified
    assert verdict.failures == ()
    assert verdict.gates.passed
    assert verdict.score == pytest.approx(
        robustness_score(
            ranking_metrics(PASSING, trial_adjusted_confidence=CONFIDENCE),
            drawdown_floor=DRAWDOWN_FLOOR,
        )
    )


_NAMED_FAILURE_CASES = [
    ({"net_sharpe": 0.79}, "net_sharpe"),
    ({"max_drawdown": 0.21}, "max_drawdown"),
    ({"neighbourhood_positive_fraction": 0.69}, "neighbourhood_positive_fraction"),
    ({"trial_adjusted_confidence": 0.89}, "trial_adjusted_confidence"),
]


@pytest.mark.parametrize(("override", "expected_failure"), _NAMED_FAILURE_CASES)
def test_a_failing_candidate_names_its_failure_and_gets_no_score(override, expected_failure):
    verdict = _adjudicate(**override)
    assert not verdict.qualified
    assert expected_failure in verdict.failures
    # A4: the floor is still measured and still named -- it now costs points rather than the
    # tournament, so the candidate keeps a score and stays in the field.
    assert expected_failure in verdict.gates.performance_failures
    assert verdict.admissible
    assert verdict.score is not None


def test_the_parametrised_cases_are_all_performance_floors():
    """Guards the list above: an integrity gate slipped into it would assert the opposite rule."""
    from crypto_trade.cup20.qualification import INTEGRITY_GATES

    cases = {expected for _, expected in _NAMED_FAILURE_CASES}
    assert not cases & INTEGRITY_GATES


def test_a_non_finite_floor_metric_fails_closed_rather_than_passing():
    # `x <= k` is False for NaN, so a naive gate would have to be written to fail; assert the
    # composed path does, rather than trusting the floor module alone.
    verdict = _adjudicate(max_drawdown=math.nan)
    assert not verdict.qualified
    assert "max_drawdown" in verdict.failures
    # Fail-closed survives A4 unchanged: NaN must never read as "floor met". What changes is the
    # consequence -- the miss is priced, not fatal.
    assert verdict.admissible


def test_a_failing_candidate_still_carries_its_scored_vector_for_diagnosis():
    verdict = _adjudicate(net_sharpe=0.10)
    assert verdict.scored["net_sharpe"] == pytest.approx(0.10)
    assert set(verdict.scored) == ASSEMBLED_METRIC_KEYS


# --- the score reads 2x, never the 1x floor values --------------------------------------------


def test_the_score_uses_the_two_x_drawdown_and_quarter_fraction():
    verdict = _adjudicate()
    assert verdict.ranking_inputs["max_drawdown"] == pytest.approx(0.16)
    assert verdict.ranking_inputs["positive_quarter_fraction"] == pytest.approx(0.56)
    # A driver that scored the 1x values would land on a different, better G -- the 1x book has
    # both a shallower drawdown and more positive quarters here.
    one_x_view = dict(
        verdict.ranking_inputs,
        max_drawdown=PASSING["max_drawdown"],
        positive_quarter_fraction=PASSING["positive_quarter_fraction"],
    )
    assert verdict.score != pytest.approx(
        robustness_score(one_x_view, drawdown_floor=DRAWDOWN_FLOOR)
    )
    assert verdict.score < robustness_score(one_x_view, drawdown_floor=DRAWDOWN_FLOOR)


def test_the_holdout_drawdown_floor_can_be_rebased_without_touching_the_floors():
    at_is = _adjudicate()
    rebased = adjudicate_candidate(
        _vector(dict(PASSING)),
        team_id="team-01",
        candidate_id="c1",
        floors=CONFIG["floors"],
        statistics_config=CONFIG["statistics"],
        research_config=CONFIG["research"],
        declared_roles=("long", "short"),
        sign_inversion_passes_core=False,
        neighbourhood_positive_fraction=0.86,
        trial_adjusted_confidence=CONFIDENCE,
        drawdown_floor=float(CONFIG["holdout"]["max_drawdown"]),
    )
    # Same floors, same gate outcome; only the drawdown term of G moves.
    assert rebased.qualified and at_is.qualified
    assert rebased.gates.checks == at_is.gates.checks
    assert rebased.score > at_is.score


def test_the_ranked_entry_carries_the_two_x_view_not_the_assembled_vector():
    entry = _adjudicate().as_ranked_entry()
    assert entry.scored["max_drawdown"] == pytest.approx(PASSING["double_cost_max_drawdown"])
    assert entry.scored["annualized_turnover"] == pytest.approx(
        PASSING["double_cost_annualized_turnover"]
    )


# --- population ranking ----------------------------------------------------------------------


def _population(*specs):
    return [
        _adjudicate(dict(PASSING, **metrics), team_id=team_id, candidate_id=f"{team_id}-c")
        for team_id, metrics in specs
    ]


def test_only_admissible_candidates_are_ranked():
    """A4: a weak book is ranked low; a falsifiable one is not ranked at all."""
    passer = _adjudicate(team_id="team-01")
    weak = _adjudicate(team_id="team-02", net_sharpe=0.10)
    falsified = _adjudicate(team_id="team-03", sign_inversion_passes_core=True)
    result = adjudicate_population([passer, weak, falsified], slots=3)
    assert [c.team_id for c in result.ranked] == ["team-01", "team-02"]
    assert [c.team_id for c in result.rejected] == ["team-03"]
    assert [c.team_id for c in result.candidates] == ["team-01", "team-02", "team-03"]


def test_ranking_is_by_descending_score():
    result = adjudicate_population(
        _population(
            ("team-01", {"worst_fold_sharpe": 0.10}),
            ("team-02", {"worst_fold_sharpe": 0.70}),
            ("team-03", {"worst_fold_sharpe": 0.40}),
        ),
        slots=3,
    )
    assert [c.team_id for c in result.ranked] == ["team-02", "team-03", "team-01"]
    assert result.ranked[0].score > result.ranked[1].score > result.ranked[2].score


def test_the_turnover_tie_break_reads_the_two_x_value():
    # Identical G and identical drawdown and worst fold, so the decision falls to the turnover
    # tie-break -- and the 1x and 2x turnovers are ordered OPPOSITELY between the two teams, so a
    # driver reading the 1x value produces the reverse ranking.
    result = adjudicate_population(
        _population(
            ("team-01", {"annualized_turnover": 9.0, "double_cost_annualized_turnover": 20.0}),
            ("team-02", {"annualized_turnover": 20.0, "double_cost_annualized_turnover": 9.0}),
        ),
        slots=2,
    )
    assert result.ranked[0].score == pytest.approx(result.ranked[1].score)
    assert [c.team_id for c in result.ranked] == ["team-02", "team-01"]


def test_advancing_is_capped_at_the_slot_count():
    result = adjudicate_population(
        _population(
            ("team-01", {"worst_fold_sharpe": 0.10}),
            ("team-02", {"worst_fold_sharpe": 0.70}),
            ("team-03", {"worst_fold_sharpe": 0.40}),
            ("team-04", {"worst_fold_sharpe": 0.55}),
        ),
        slots=int(CONFIG["selection"]["advancing_slots"]),
    )
    assert [c.team_id for c in result.advancing] == ["team-02", "team-04", "team-03"]
    assert len(result.ranked) == 4


def test_an_empty_slot_is_never_backfilled_by_an_integrity_failer():
    """A4 moves the line: floor missers DO fill slots, and a falsifiable result never does."""
    result = adjudicate_population(
        [
            _adjudicate(team_id="team-01"),
            _adjudicate(team_id="team-02", net_sharpe=0.10),
            _adjudicate(team_id="team-03", sign_inversion_passes_core=True),
            _adjudicate(team_id="team-04", declared_roles=("long",)),
        ],
        slots=3,
    )
    assert [c.team_id for c in result.advancing] == ["team-01", "team-02"]


def test_a_population_with_nobody_admissible_advances_nobody():
    """Section 1.1 keeps 'no winner' reachable. A4 narrows what empties the field, not that it can.

    An empty field is still a permitted outcome; it now takes an integrity failure to produce one.
    """
    result = adjudicate_population(
        [
            _adjudicate(team_id="team-01", sign_inversion_passes_core=True),
            _adjudicate(team_id="team-02", declared_roles=("long",)),
        ],
        slots=3,
    )
    assert result.ranked == ()
    assert result.advancing == ()
    assert len(result.rejected) == 2


# --- raise paths, one test each ---------------------------------------------------------------


def test_adjudicating_an_incomplete_metric_vector_raises():
    truncated = {k: v for k, v in PASSING.items() if k != "double_cost_max_drawdown"}
    with pytest.raises(ValueError, match="missing \\['double_cost_max_drawdown'\\]"):
        _adjudicate(truncated)


def test_a_floor_passer_with_a_non_finite_ranking_input_raises():
    # `double_cost_max_drawdown` is gated by NO floor, so a NaN there survives qualification and
    # would otherwise blow up inside the population sort, unattributed.
    with pytest.raises(ValueError, match="team-01/c1 is not refuted"):
        _adjudicate(double_cost_max_drawdown=math.nan)


def test_an_integrity_failer_cannot_be_turned_into_a_ranked_entry():
    verdict = _adjudicate(sign_inversion_passes_core=True)
    with pytest.raises(ValueError, match="only admissible candidates are ranked"):
        verdict.as_ranked_entry()


def test_two_candidates_from_one_team_are_rejected():
    with pytest.raises(ValueError, match="exactly one identity"):
        adjudicate_population(
            [_adjudicate(team_id="team-01", candidate_id="a"), _adjudicate(team_id="team-01")],
            slots=3,
        )


def test_a_non_positive_slot_count_is_rejected():
    with pytest.raises(ValueError, match="slots must be positive"):
        adjudicate_population([_adjudicate()], slots=0)


def test_a_verdict_is_immutable():
    verdict = _adjudicate()
    with pytest.raises(dataclasses.FrozenInstanceError):
        verdict.score = 0.0  # type: ignore[misc]


def test_candidate_adjudication_is_constructible_only_with_every_field():
    with pytest.raises(TypeError):
        CandidateAdjudication(team_id="team-01", candidate_id="c1")  # type: ignore[call-arg]


# --- section 8 holdout eligibility -------------------------------------------------------------
#
# A separate conjunction from section 7.3's, and the mutation this block exists to catch is the
# opposite of the one above: not "read the 2x twin where the 1x floor was meant", but "reuse the
# in-sample gate", which would silently impose thirteen floors section 8 never states and gate the
# drawdown at 0.20 rather than the 0.25 section 8 rebases it to.

HOLDOUT = CONFIG["holdout"]


def _holdout(scored=None, *, nominated=0.11, **overrides):
    metrics = dict(PASSING if scored is None else scored)
    metrics.update(overrides)
    return adjudicate_holdout_candidate(
        _vector(metrics, STAGE_HOLDOUT),
        team_id="team-01",
        candidate_id="c1",
        holdout=HOLDOUT,
        trial_adjusted_confidence=CONFIDENCE,
        nominated_point_double_cost_return=nominated,
    )


def test_the_holdout_fixture_would_be_eligible_before_any_override():
    # Not vacuous: every failure case below has to start from a passing baseline, or "it failed"
    # would say nothing about the override.
    verdict = _holdout()
    assert verdict.qualified
    assert verdict.failures == ()
    assert verdict.score is not None


@pytest.mark.parametrize(
    ("override", "expected_failure"),
    [
        ({"annualized_return": -0.01}, "annualized_return"),
        ({"annualized_return": 0.0}, "annualized_return"),  # zero is not positive
        ({"double_cost_annualized_return": -0.01}, "double_cost_annualized_return"),
        ({"double_cost_sharpe": 0.0}, "double_cost_sharpe"),
        ({"max_drawdown": 0.26}, "max_drawdown"),
        ({"positive_quarter_count": 4.0}, "positive_quarter_count"),
    ],
)
def test_each_section_8_condition_fails_on_its_own(override, expected_failure):
    verdict = _holdout(**override)
    assert not verdict.qualified
    assert verdict.failures == (expected_failure,)
    assert verdict.score is None


def test_the_nominated_point_condition_fails_on_its_own():
    verdict = _holdout(nominated=-0.02)
    assert not verdict.qualified
    assert verdict.failures == ("nominated_point_double_cost_return",)
    assert verdict.score is None


@pytest.mark.parametrize(
    "key",
    [
        "annualized_return",
        "double_cost_annualized_return",
        "double_cost_sharpe",
        "max_drawdown",
        "positive_quarter_count",
    ],
)
def test_a_non_finite_holdout_input_fails_closed(key):
    # No fail-open on NaN: `nan <= 0.25` and `nan >= 5` are both False, and the gate must treat
    # that as a failure rather than as an absence of evidence.
    assert not _holdout(**{key: math.nan}).qualified
    assert _holdout(**{key: math.nan}).failures == (key,)


def test_a_non_finite_nominated_point_return_fails_closed():
    assert _holdout(nominated=math.nan).failures == ("nominated_point_double_cost_return",)


def test_the_drawdown_gate_is_the_section_8_rebase_not_the_in_sample_floor():
    # 0.22 passes section 8's 0.25 and would fail section 7.3's 0.20. Mutation this catches: the
    # holdout gate reading `floors["max_drawdown"]`, or hard-coding 0.20.
    assert float(HOLDOUT["max_drawdown"]) == 0.25
    assert DRAWDOWN_FLOOR == 0.20
    assert _holdout(max_drawdown=0.22).qualified
    assert not _adjudicate(**{"max_drawdown": 0.22}).qualified


def test_the_quarter_gate_reads_the_count_from_the_frozen_holdout_table():
    # "At least 5 of 8 quarters positive" is a COUNT, and the boundary is inclusive.
    assert int(HOLDOUT["minimum_positive_quarters"]) == 5
    assert _holdout(positive_quarter_count=5.0).qualified
    assert not _holdout(positive_quarter_count=4.0).qualified


def test_the_quarter_gate_does_not_read_the_fraction():
    # Mutation this catches: gating `positive_quarter_fraction >= 0.50` (section 7.3's floor)
    # instead of the count. 5 of 8 is 0.625, so a book with 4 positive quarters out of 8 has a
    # 0.50 fraction that PASSES section 7.3 while failing section 8 -- the two gates genuinely
    # disagree on this input, which is what makes reading the wrong one detectable.
    scored = dict(PASSING)
    scored["positive_quarter_fraction"] = 0.50
    scored["positive_quarter_count"] = 4.0
    assert not _holdout(scored).qualified
    assert _adjudicate(scored).gates.checks["positive_quarter_fraction"]


def test_the_holdout_gate_is_not_the_in_sample_gate():
    # A candidate that fails several section 7.3 floors can still be holdout-eligible, because
    # section 8 lists five conditions and not eighteen. Mutation this catches: implementing the
    # holdout by calling `evaluate_floors` with an overridden floors mapping.
    scored = dict(PASSING)
    scored["net_sharpe"] = 0.10  # fails the 0.80 floor
    scored["trade_count"] = 10.0  # fails the 500 floor
    scored["top5_day_share"] = 0.90  # fails the 0.35 floor
    assert not _adjudicate(scored).qualified
    assert _holdout(scored).qualified


def test_the_holdout_score_rebases_the_drawdown_term_to_the_section_8_floor():
    verdict = _holdout()
    expected = robustness_score(
        ranking_metrics(PASSING, trial_adjusted_confidence=CONFIDENCE),
        drawdown_floor=float(HOLDOUT["max_drawdown"]),
    )
    assert verdict.score == pytest.approx(expected)
    # And it is NOT the in-sample rebase, or the assertion above would not discriminate.
    assert verdict.score != pytest.approx(
        robustness_score(
            ranking_metrics(PASSING, trial_adjusted_confidence=CONFIDENCE),
            drawdown_floor=DRAWDOWN_FLOOR,
        )
    )


def test_the_holdout_ranking_inputs_are_still_the_two_x_view():
    verdict = _holdout()
    assert verdict.ranking_inputs["max_drawdown"] == pytest.approx(
        PASSING["double_cost_max_drawdown"]
    )
    assert verdict.ranking_inputs["max_drawdown"] != pytest.approx(PASSING["max_drawdown"])


def test_an_incomplete_vector_is_rejected_by_the_holdout_driver():
    incomplete = {k: v for k, v in PASSING.items() if k != "positive_quarter_count"}
    with pytest.raises(ValueError, match="missing"):
        _holdout(incomplete)


def test_a_holdout_passer_with_a_non_finite_ranking_input_raises():
    # `double_cost_annualized_turnover` is gated by no section 8 condition at all, so a non-finite
    # one reaches the ranking. It must raise here, naming the finalist, rather than deep inside a
    # sort of the whole finalist population.
    with pytest.raises(ValueError, match="not finite"):
        _holdout(double_cost_annualized_turnover=math.inf)


def test_a_missing_holdout_config_key_raises_rather_than_defaulting():
    for missing in ("max_drawdown", "minimum_positive_quarters"):
        partial = {k: v for k, v in HOLDOUT.items() if k != missing}
        with pytest.raises(KeyError):
            adjudicate_holdout_candidate(
                _vector(dict(PASSING), STAGE_HOLDOUT),
                team_id="team-01",
                candidate_id="c1",
                holdout=partial,
                trial_adjusted_confidence=CONFIDENCE,
                nominated_point_double_cost_return=0.11,
            )


def test_a_failing_finalist_still_carries_its_scored_vector_and_gate_vector():
    verdict = _holdout(max_drawdown=0.30)
    assert verdict.scored["max_drawdown"] == 0.30
    assert set(verdict.gates.checks) == {
        "annualized_return",
        "double_cost_annualized_return",
        "double_cost_sharpe",
        "max_drawdown",
        "positive_quarter_count",
        "nominated_point_double_cost_return",
    }


# --- Amendment A4: performance floors cost points; only integrity failures disqualify -----------


def test_a_missed_performance_floor_is_still_ranked():
    """A4's whole point: one miss out of twenty-two no longer discards a book.

    Team 04's residual cross-section was positive in all four folds, positive on both sleeves and
    inside every risk limit, and scored nothing because trial-adjusted confidence came in at 0.839.
    Under A4 that costs it the seven multiplicity points and nothing else.
    """
    verdict = _adjudicate(trial_adjusted_confidence=0.839)
    assert not verdict.qualified
    assert verdict.gates.performance_failures == ("trial_adjusted_confidence",)
    assert verdict.admissible
    assert verdict.score is not None
    assert verdict.as_ranked_entry().score == verdict.score


def test_a_falsifiable_result_is_not_ranked_at_all():
    """Integrity, not performance: the falsifier reproduced the book, so nothing is left to rank."""
    verdict = _adjudicate(sign_inversion_passes_core=True)
    assert not verdict.admissible
    assert verdict.gates.integrity_failures == ("sign_inversion_not_profitable",)
    assert verdict.score is None
    with pytest.raises(ValueError, match="only admissible candidates are ranked"):
        verdict.as_ranked_entry()


def test_a_misdeclared_sleeve_is_not_ranked_at_all():
    """Claiming a sleeve the book never traded is a false certificate, not a weak result."""
    verdict = _adjudicate(declared_roles=("long",))
    assert not verdict.admissible
    assert "declared_roles_match_traded_sides" in verdict.gates.integrity_failures
    assert verdict.score is None


def test_an_unmeasured_integrity_check_is_not_treated_as_passed():
    """Kills the mutation: ``checks.get(name, True)``.

    A sweep cannot decide sign inversion -- it is its own material trial -- so the key can be
    absent. Reading absence as a pass is how a falsification requirement silently stops binding.
    """
    from crypto_trade.cup20.qualification import ADMISSION_GATES, GateVector

    complete = GateVector(checks=dict.fromkeys(ADMISSION_GATES, True))
    assert complete.admissible
    assert complete.integrity_verdict == "passed"

    without = GateVector(
        checks={k: True for k in ADMISSION_GATES if k != "sign_inversion_not_profitable"}
    )
    assert not without.admissible
    assert without.integrity_verdict == "unmeasured"
    # Crucially NOT reported as a failure: nobody ran the battery, so accusing the team of failing
    # it would be a false accusation. Unmeasured and refuted are different states.
    assert without.integrity_failures == ()
    assert not without.refuted
    assert without.unmeasured_admission_gates == ("sign_inversion_not_profitable",)


def test_the_population_ranks_floor_missers_and_drops_only_integrity_failures():
    """The composition A4 actually changes: who is in the field at all."""
    ranked_low = _adjudicate(trial_adjusted_confidence=0.839, team_id="team-04", candidate_id="r")
    clean = _adjudicate(team_id="team-02", candidate_id="c")
    falsified = _adjudicate(sign_inversion_passes_core=True, team_id="team-09", candidate_id="f")

    result = adjudicate_population([clean, ranked_low, falsified], slots=3)
    assert [entry.team_id for entry in result.ranked] == ["team-02", "team-04"]
    assert "team-09" not in [entry.team_id for entry in result.ranked]
    assert clean.score > ranked_low.score  # the seven multiplicity points, and only those


def test_a_flawless_finalist_is_admissible_at_the_holdout_stage():
    """Regression: A4 leaking into the holdout via the shared class.

    The holdout gate vector carries neither integrity key nor either substance key, so asking the
    in-sample question of it answered "inadmissible" for a PERFECT finalist -- dropping every
    finalist from the population and reporting a flawless book as an integrity failure. The two
    stages ask different questions; ``admissible`` has to know which one it is being asked.
    """
    holdout_gates = GateVector(checks={"net_sharpe": True, "max_drawdown": True})
    finalist = CandidateAdjudication(
        team_id="team-02",
        candidate_id="c",
        scored={},
        ranking_inputs={},
        gates=holdout_gates,
        score=53.5,
        stage="holdout",
    )
    assert finalist.admissible
    assert finalist.qualified

    failing = dataclasses.replace(
        finalist, gates=GateVector(checks={"net_sharpe": True, "max_drawdown": False})
    )
    assert not failing.admissible  # conjunctive at the holdout, exactly as before A4

    same_vector_in_sample = dataclasses.replace(finalist, stage="in_sample")
    assert not same_vector_in_sample.admissible  # and the IS question still fails closed


def test_an_unknown_stage_is_refused_rather_than_guessed():
    verdict = CandidateAdjudication(
        team_id="t",
        candidate_id="c",
        scored={},
        ranking_inputs={},
        gates=GateVector(checks={}),
        score=1.0,
        stage="typo",
    )
    with pytest.raises(ValueError, match="unknown adjudication stage"):
        verdict.admissible


def test_an_under_risked_non_trading_book_is_not_ranked():
    """Regression: the defect that inverted the tournament.

    A book that grinds up on a whisper of volatility takes a near-zero drawdown and an
    undefined-Calmar sentinel to a PERFECT ranking score -- measured at G = 100.00, against 70.58
    for the strongest real submission in the field. The volatility floor existed to stop precisely
    this and A4 had removed its teeth while keeping its 35 points of reward. Refusing a book that
    does not trade is not blocking a team; it is declining to rank a non-entry.
    """
    grinder = _adjudicate(annualized_volatility=0.004, trade_count=12.0)
    assert not grinder.admissible
    assert set(grinder.gates.admission_failures) == {"annualized_volatility", "trade_count"}
    assert grinder.score is None
    with pytest.raises(ValueError, match="not admissible"):
        grinder.as_ranked_entry()

    result = adjudicate_population([_adjudicate(team_id="team-02"), grinder], slots=3)
    assert [c.team_id for c in result.ranked] == ["team-02"]


def test_an_unrun_falsification_scores_but_does_not_rank():
    """A sweep cannot decide sign inversion, and the two wrong answers are opposite mistakes.

    Asserting it passed retires the falsification requirement; withholding the score makes every
    sweep report useless while the battery is outstanding. The candidate gets its indicative G and
    is not rankable until the trial exists.
    """
    verdict = _adjudicate(sign_inversion_passes_core=None)
    assert verdict.score is not None  # a team still reads its own G off the sweep
    assert not verdict.gates.refuted
    assert not verdict.admissible
    assert verdict.gates.integrity_verdict == "unmeasured"
    with pytest.raises(ValueError, match="unmeasured"):
        verdict.as_ranked_entry()


def test_ranked_and_rejected_partition_the_population_exactly():
    population = [
        _adjudicate(team_id="team-01"),
        _adjudicate(team_id="team-02", net_sharpe=0.10),
        _adjudicate(team_id="team-03", sign_inversion_passes_core=True),
        _adjudicate(team_id="team-04", annualized_volatility=0.004),
        _adjudicate(team_id="team-05", sign_inversion_passes_core=None),
    ]
    result = adjudicate_population(population, slots=3)
    ranked = {c.team_id for c in result.ranked}
    rejected = {c.team_id for c in result.rejected}
    assert ranked & rejected == set()
    assert ranked | rejected == {c.team_id for c in result.candidates}
