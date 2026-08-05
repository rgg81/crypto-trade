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

import pytest

from crypto_trade.cup20.adjudication import (
    CandidateAdjudication,
    adjudicate_candidate,
    adjudicate_population,
)
from crypto_trade.cup20.config import load_config
from crypto_trade.cup20.scored_metrics import ASSEMBLED_METRIC_KEYS, ranking_metrics
from crypto_trade.cup20.scoring import robustness_score

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
        metrics,
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


@pytest.mark.parametrize(
    ("override", "expected_failure"),
    [
        ({"net_sharpe": 0.79}, "net_sharpe"),
        ({"max_drawdown": 0.21}, "max_drawdown"),
        ({"trade_count": 499.0}, "trade_count"),
        ({"sign_inversion_passes_core": True}, "sign_inversion_not_profitable"),
        ({"neighbourhood_positive_fraction": 0.69}, "neighbourhood_positive_fraction"),
        ({"trial_adjusted_confidence": 0.89}, "trial_adjusted_confidence"),
    ],
)
def test_a_failing_candidate_names_its_failure_and_gets_no_score(override, expected_failure):
    verdict = _adjudicate(**override)
    assert not verdict.qualified
    assert expected_failure in verdict.failures
    # None, not 0.0: section 7.4's G is a ranking score, and attaching a number to a
    # disqualified candidate invites the comparison the floors exist to forbid.
    assert verdict.score is None


def test_a_non_finite_floor_metric_fails_closed_rather_than_passing():
    # `x <= k` is False for NaN, so a naive gate would have to be written to fail; assert the
    # composed path does, rather than trusting the floor module alone.
    verdict = _adjudicate(max_drawdown=math.nan)
    assert not verdict.qualified
    assert "max_drawdown" in verdict.failures
    assert verdict.score is None


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
        dict(PASSING),
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


def test_only_floor_passers_are_ranked():
    passer = _adjudicate(team_id="team-01")
    failer = _adjudicate(team_id="team-02", net_sharpe=0.10)
    result = adjudicate_population([passer, failer], slots=3)
    assert [c.team_id for c in result.ranked] == ["team-01"]
    assert [c.team_id for c in result.rejected] == ["team-02"]
    assert [c.team_id for c in result.candidates] == ["team-01", "team-02"]


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


def test_an_empty_slot_is_never_backfilled_by_a_floor_failer():
    result = adjudicate_population(
        [
            _adjudicate(team_id="team-01"),
            _adjudicate(team_id="team-02", net_sharpe=0.10),
            _adjudicate(team_id="team-03", trade_count=10.0),
        ],
        slots=3,
    )
    assert [c.team_id for c in result.advancing] == ["team-01"]


def test_a_population_with_no_qualifiers_advances_nobody():
    result = adjudicate_population(
        [
            _adjudicate(team_id="team-01", net_sharpe=0.10),
            _adjudicate(team_id="team-02", max_drawdown=0.90),
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
    with pytest.raises(ValueError, match="team-01/c1 passed every floor"):
        _adjudicate(double_cost_max_drawdown=math.nan)


def test_a_failing_candidate_cannot_be_turned_into_a_ranked_entry():
    verdict = _adjudicate(net_sharpe=0.10)
    with pytest.raises(ValueError, match="only floor-passers are ranked"):
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
