"""The roster constraints that keep fifteen lanes from becoming one experiment run fifteen times."""

from __future__ import annotations

import dataclasses

import pytest

from crypto_trade.tournament.v5 import lanes
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT


def test_the_roster_matches_the_layout():
    assert tuple(entry.team_id for entry in lanes.LANES) == TOP40_V5_LAYOUT.team_ids


def test_the_shipped_roster_satisfies_its_own_invariants():
    lanes.assert_lane_invariants()


# -- each invariant must actually flip -----------------------------------------------------------
# A constraint that cannot fail is not a constraint. Every check below breaks the roster in the
# specific way the invariant exists to catch, and asserts it is caught.


def _roster_with(**changes) -> tuple[lanes.Lane, ...]:
    """The real roster with one lane replaced, so a mutation varies exactly one thing."""

    team_id = changes.pop("team_id")
    return tuple(
        dataclasses.replace(entry, **changes) if entry.team_id == team_id else entry
        for entry in lanes.LANES
    )


def test_a_second_taker_flow_lane_is_refused():
    """The direct structural fix for convergence: V4-R9's fifteen open lanes produced four of five
    finalists on this one signal."""

    doubled = _roster_with(team_id="team-11", rations=lanes.RATIONED_SIGNAL)

    with pytest.raises(lanes.LaneError, match="rationed to exactly one lane"):
        lanes.assert_lane_invariants(doubled)


def test_removing_the_taker_flow_ration_is_also_refused():
    """Both directions. Zero rationed lanes means the signal is unclaimed, not that it is safe."""

    unclaimed = _roster_with(team_id="team-10", rations=None)

    with pytest.raises(lanes.LaneError, match="rationed to exactly one lane"):
        lanes.assert_lane_invariants(unclaimed)


def test_a_field_with_no_directional_lane_is_refused():
    neutral = _roster_with(team_id="team-14", directional=False)

    with pytest.raises(lanes.LaneError, match="mandated directional"):
        lanes.assert_lane_invariants(neutral)


def test_a_second_directional_lane_is_refused():
    doubled = _roster_with(team_id="team-08", directional=True)

    with pytest.raises(lanes.LaneError, match="mandated directional"):
        lanes.assert_lane_invariants(doubled)


def test_a_lane_without_a_falsifier_is_refused():
    """A mandate that cannot be wrong is not a mandate."""

    unfalsifiable = _roster_with(team_id="team-06", falsifier="   ")

    with pytest.raises(lanes.LaneError, match="no falsifier"):
        lanes.assert_lane_invariants(unfalsifiable)


def test_two_lanes_sharing_a_seed_is_refused():
    shared = _roster_with(team_id="team-09", seed="timeseries_momentum")

    with pytest.raises(lanes.LaneError, match="share an organizer seed"):
        lanes.assert_lane_invariants(shared)


def test_a_roster_that_is_not_fifteen_lanes_is_refused():
    with pytest.raises(lanes.LaneError, match="fifteen lanes"):
        lanes.assert_lane_invariants(lanes.LANES[:14])


def test_a_roster_collapsed_onto_one_family_is_refused():
    collapsed = tuple(
        dataclasses.replace(entry, family="time-series trend") for entry in lanes.LANES
    )

    with pytest.raises(lanes.LaneError, match="collapsed"):
        lanes.assert_lane_invariants(collapsed)


# -- what a lane is told -------------------------------------------------------------------------


def test_a_brief_names_the_family_and_the_falsifier():
    brief = lanes.lane("team-04").brief()

    assert "residual cross-sectional momentum" in brief
    assert "cross-sectional mispricing" in brief
    assert "market factor" in brief
    assert "unmodified organizer seed" in brief


def test_only_the_rationed_lane_is_told_it_holds_the_ration():
    assert lanes.RATIONED_SIGNAL in lanes.lane("team-10").brief()
    assert lanes.RATIONED_SIGNAL not in lanes.lane("team-11").brief()


def test_only_the_directional_lane_is_told_to_run_net():
    assert "non-zero net" in lanes.lane("team-14").brief()
    assert "non-zero net" not in lanes.lane("team-03").brief()


def test_no_brief_mentions_another_lane():
    """A lane learns its own mandate and nothing about the field."""

    for entry in lanes.LANES:
        brief = entry.brief()
        others = {other.team_id for other in lanes.LANES} - {entry.team_id}
        assert not (others & set(brief.split()))


def test_no_brief_states_an_expected_sign_or_a_parameter():
    """The mandate names a family, never a parameter, an implementation or an expected sign.

    A mandate that says "short high funding" has already done the team's research and collapses
    fifteen independent searches into one organizer opinion repeated fifteen times.
    """

    forbidden = ("lookback=", "threshold=", "window=", "should be positive", "should be negative")
    for entry in lanes.LANES:
        brief = entry.brief().lower()
        for token in forbidden:
            assert token not in brief, f"{entry.team_id} brief leaks {token!r}"


def test_an_unknown_lane_is_refused():
    with pytest.raises(lanes.LaneError, match="unknown lane"):
        lanes.lane("team-99")
