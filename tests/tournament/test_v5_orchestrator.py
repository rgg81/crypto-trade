"""Nomination, the sealed bar, and the empty bracket that V4-R9 could not represent."""

from __future__ import annotations

import dataclasses
import inspect

import numpy as np
import pandas as pd
import pytest

from crypto_trade.tournament.v5 import gates, journal, metrics, orchestrator


def _packet(**overrides) -> metrics.MetricPacket:
    base = {
        "days": 360,
        "annualised_return": 0.18,
        "annualised_volatility": 0.11,
        "net_sharpe": 1.2,
        "double_cost_sharpe": 0.9,
        "triple_cost_annualised_return": 0.04,
        "max_drawdown": 0.14,
        "positive_fold_fraction": 0.8,
        "deflated_sharpe_probability": 0.82,
        "deletion_profile_p05_sharpe": 0.55,
        "mean_gross_exposure": 0.6,
        "median_effective_breadth": 12.0,
        "breadth_pass_fraction": 0.93,
        "active_bar_fraction": 0.96,
        "long_exposure_share": 0.5,
        "short_exposure_share": 0.5,
        "risk_unit_capped_fraction": 0.1,
        "annualised_turnover": 22.0,
        "gross_edge_bps_per_turnover": 45.0,
        "cost_share_of_positive_gross": 0.3,
        "top_symbol_gross_pnl_share": 0.19,
        "ruined": False,
    }
    base.update(overrides)
    return metrics.MetricPacket(**base)


def _assessment(*, eligible: bool, stage: str) -> gates.Assessment:
    names = tuple(gates.ALL_GATES)
    values = dict.fromkeys(names, True)
    if not eligible:
        values["effective_breadth"] = False
    enforced = names if stage == gates.SEALED_STAGE else tuple(gates.DEGENERACY_GATES)
    reported = () if stage == gates.SEALED_STAGE else tuple(gates.PERFORMANCE_GATES)
    return gates.Assessment(stage=stage, gates=values, enforced=enforced, reported=reported)


@dataclasses.dataclass(frozen=True)
class _Trial:
    team_id: str
    trial_id: str
    assessment: gates.Assessment

    @property
    def admitted(self) -> bool:
        return self.assessment.eligible


@dataclasses.dataclass(frozen=True)
class _Confirmation:
    team_id: str
    candidate_id: str
    packet: metrics.MetricPacket
    assessment: gates.Assessment

    @property
    def cleared(self) -> bool:
        return self.assessment.eligible


def _confirmed(team: str, robustness: float, *, cleared: bool = True) -> _Confirmation:
    return _Confirmation(
        team_id=team,
        candidate_id="c01",
        packet=_packet(deletion_profile_p05_sharpe=robustness),
        assessment=_assessment(eligible=cleared, stage=gates.SEALED_STAGE),
    )


@pytest.fixture
def journal_path(tmp_path):
    path = tmp_path / "research-journal.jsonl"
    journal.initialize(path)
    return str(path)


# -- the raise that V4-R9 patched into unreachability -------------------------------------------


def test_an_ineligible_candidate_cannot_be_nominated(journal_path):
    trial = _Trial("team-04", "t03", _assessment(eligible=False, stage=gates.DEVELOPMENT_STAGE))

    with pytest.raises(orchestrator.OrchestratorError, match="cannot be nominated"):
        orchestrator.nominate(journal_path, trial, candidate_id="c01")

    assert list(journal.iter_events(journal_path, "nominated")) == []


def test_nominate_has_no_parameter_that_could_suppress_the_raise():
    """The absence of the flag is the guarantee.

    V4-R9's fallback was reached by setting exactly such a flag: ``nominate`` became
    ``if not field_adjustment and not eligible: raise``, ``field_adjustment`` was True, and the
    raise never fired while the config still declared that floors would not be lowered. A test that
    only checked the raise fires today would not have caught that -- so this checks the shape.
    """

    parameters = set(inspect.signature(orchestrator.nominate).parameters)

    assert parameters == {"journal_path", "trial", "candidate_id"}
    for forbidden in ("force", "field_adjustment", "allow_ineligible", "fill_bracket"):
        assert forbidden not in parameters


def test_select_has_no_parameter_that_could_fill_a_bracket():
    """You cannot ask this function to promote an unqualified candidate, because there is no
    argument with which to ask."""

    parameters = set(inspect.signature(orchestrator.select).parameters)

    assert parameters == {"cleared", "daily_returns"}
    for forbidden in ("minimum_count", "fallback", "floors", "lower_floors_to_fill_bracket"):
        assert forbidden not in parameters


def test_an_eligible_candidate_is_journalled(journal_path):
    trial = _Trial("team-04", "t03", _assessment(eligible=True, stage=gates.DEVELOPMENT_STAGE))

    orchestrator.nominate(journal_path, trial, candidate_id="c01")

    records = list(journal.iter_events(journal_path, "nominated"))
    assert len(records) == 1
    assert records[0].payload["team_id"] == "team-04"


def test_a_lane_with_nothing_eligible_retires_plainly(journal_path):
    orchestrator.retire(journal_path, "team-11", reason="no candidate cleared the degeneracy gates")

    records = list(journal.iter_events(journal_path, "retired"))
    assert records[0].payload["reason"].startswith("no candidate")


# -- the empty bracket --------------------------------------------------------------------------


def test_an_empty_field_is_a_valid_outcome_with_no_winner():
    """Untested, this looks like a bug under pressure -- which is how R9 acquired its fallback."""

    selection = orchestrator.select([])

    assert selection.empty
    assert selection.advancing == ()
    assert selection.desks == ()
    assert selection.as_dict()["advancing"] == []


def test_a_field_where_nobody_clears_the_bar_is_also_empty():
    selection = orchestrator.select([_confirmed("team-01", 0.9, cleared=False)])

    assert selection.empty


def test_a_partial_field_advances_without_being_topped_up():
    """Two qualifiers produce two desks, not four. Nothing is promoted to fill the gap."""

    selection = orchestrator.select([_confirmed("team-01", 0.8), _confirmed("team-02", 0.6)])

    assert selection.advancing == ("team-01:c01", "team-02:c01")
    assert len(selection.desks) == 2
    assert all(desk.name != orchestrator.ENSEMBLE_DESK for desk in selection.desks)


# -- ranking and the deliverable ----------------------------------------------------------------


def test_ranking_is_by_sealed_robustness_not_performance():
    """A near-flat book cannot win this the way it won V4-R9's worst-fold Sharpe."""

    flat = _Confirmation(
        team_id="team-flat",
        candidate_id="c01",
        packet=_packet(net_sharpe=2.0, deletion_profile_p05_sharpe=0.02),
        assessment=_assessment(eligible=True, stage=gates.SEALED_STAGE),
    )
    robust = _confirmed("team-robust", 0.71)

    selection = orchestrator.select([flat, robust])

    assert selection.advancing[0] == "team-robust:c01"


def test_the_deliverable_is_three_individuals_and_an_equal_weight_ensemble():
    cleared = [_confirmed(f"team-{n:02d}", 0.9 - 0.1 * n) for n in range(1, 6)]

    selection = orchestrator.select(cleared)

    assert len(selection.desks) == 4
    ensemble = selection.desks[-1]
    assert ensemble.name == orchestrator.ENSEMBLE_DESK
    assert len(ensemble.constituents) == 3
    assert list(ensemble.weights.values()) == pytest.approx([1 / 3] * 3)
    assert sum(ensemble.weights.values()) == pytest.approx(1.0)
    assert ensemble.constituents == selection.advancing[:3]


def test_every_qualifier_is_observed_even_beyond_the_desks():
    """A bar, not a rank cut: five qualifiers all advance, four desks carry them forward."""

    cleared = [_confirmed(f"team-{n:02d}", 0.9 - 0.1 * n) for n in range(1, 6)]

    selection = orchestrator.select(cleared)

    assert len(selection.advancing) == 5
    assert len(selection.ranked) == 5


# -- honesty checks -----------------------------------------------------------------------------


def test_a_promoted_candidate_is_detected():
    """A promoted candidate and a qualified one look identical in a leaderboard."""

    cleared = [_confirmed("team-01", 0.8)]
    tampered = orchestrator.Selection(
        advancing=("team-01:c01", "team-09:c01"),
        ranked=(("team-01:c01", 0.8), ("team-09:c01", 0.7)),
        ties=(),
        desks=(),
    )

    orchestrator.assert_selection_is_honest(orchestrator.select(cleared), cleared)
    with pytest.raises(orchestrator.OrchestratorError, match="without clearing"):
        orchestrator.assert_selection_is_honest(tampered, cleared)


def test_two_indistinguishable_candidates_are_reported_as_tied():
    """Paired, because the market factor largely cancels; marginal standard errors over 2.5 years
    are about 0.63 and would make the rule vacuous."""

    generator = np.random.default_rng(11)
    index = pd.date_range("2024-02-01", periods=400, freq="D", tz="UTC")
    common = generator.normal(0.0005, 0.01, size=400)
    left = pd.Series(common + generator.normal(0, 0.0001, 400), index=index)
    right = pd.Series(common + generator.normal(0, 0.0001, 400), index=index)

    selection = orchestrator.select(
        [_confirmed("team-01", 0.80), _confirmed("team-02", 0.79)],
        daily_returns={"team-01:c01": left, "team-02:c01": right},
    )

    assert selection.ties == (("team-01:c01", "team-02:c01"),)


def test_two_clearly_different_candidates_are_not_tied():
    """Companion: were everything reported tied, the rule would say nothing."""

    generator = np.random.default_rng(12)
    index = pd.date_range("2024-02-01", periods=400, freq="D", tz="UTC")
    left = pd.Series(generator.normal(0.002, 0.005, 400), index=index)
    right = pd.Series(generator.normal(-0.002, 0.005, 400), index=index)

    selection = orchestrator.select(
        [_confirmed("team-01", 0.80), _confirmed("team-02", 0.79)],
        daily_returns={"team-01:c01": left, "team-02:c01": right},
    )

    assert selection.ties == ()


def test_the_field_maximum_under_the_null_is_available_for_reporting():
    """Published beside the leaderboard, never used as a gate."""

    hurdle = orchestrator.expected_field_maximum(15, 0.768)

    assert hurdle > 0.0
    assert hurdle > orchestrator.expected_field_maximum(2, 0.768)


def test_a_null_book_lands_inside_its_own_sign_randomised_band():
    """The label the leaderboard cannot produce on its own."""

    generator = np.random.default_rng(3)
    index = pd.date_range("2024-02-01", periods=900, freq="D", tz="UTC")
    noise = pd.Series(generator.normal(0.0, 0.01, size=900), index=index)

    low, high = orchestrator.sign_randomised_null_band(noise, draws=400)
    observed = orchestrator.statistics.sharpe_ratio(noise, annualised=True)

    assert low < observed < high
