"""The network and the evaluation surface must never be held by the same process.

V5 adds a networked scouting phase so teams can research the professional literature. That
introduces a combination earlier editions never had: a process with both internet access and a
filesystem inside the tournament. These tests assert the separation that makes it safe, including
the specific mount that would break it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from crypto_trade.tournament.v5 import isolation
from crypto_trade.tournament.v5.layout import TOP40_V5_LAYOUT

ROOT = "/srv/tournament"
TEAM = "team-07"
TEAM_ROOT = TOP40_V5_LAYOUT.team_root(TEAM)
KIT_ROOT = TOP40_V5_LAYOUT.team_kit_root
TOOLCHAIN = "/opt/codex"

FORBIDDEN = (
    "data/top40/snapshot-v3",
    "reports-top40-v5",
    "tournament/top40-v5/private",
    ".git",
)


def _scouting() -> isolation.PermissionProfile:
    return isolation.scouting_profile(ROOT, TEAM_ROOT, KIT_ROOT, toolchain_root=TOOLCHAIN)


def _offline() -> isolation.PermissionProfile:
    return isolation.offline_profile(ROOT, TEAM_ROOT, KIT_ROOT, toolchain_root=TOOLCHAIN)


# -- the separation ---------------------------------------------------------------------------


def test_the_scouting_phase_has_the_network() -> None:
    profile = _scouting()
    assert profile.network_enabled
    assert profile.web_search
    assert isolation._WEB_SEARCH_CAPABILITY not in profile.disabled_capabilities


def test_the_research_phase_does_not() -> None:
    profile = _offline()
    assert not profile.network_enabled
    assert not profile.web_search
    assert isolation._WEB_SEARCH_CAPABILITY in profile.disabled_capabilities


@pytest.mark.parametrize("surface", isolation.EVALUATION_SURFACE)
def test_the_networked_phase_cannot_reach_any_evaluation_surface(surface: str) -> None:
    """The exfiltration channel this design exists to close.

    feedback/ holds lane-local evaluation results. A networked process able to read it could carry
    them out, whatever anyone intended.
    """

    profile = _scouting()
    lane = f"{ROOT}/{TEAM_ROOT}/{surface}"
    assert not any(isolation._covers(mounted, Path(lane)) for mounted in profile.filesystem)


def test_the_networked_phase_may_write_only_its_own_scratch_directory() -> None:
    """It cannot author executable source or a broker request."""

    assert _scouting().writable() == (f"{ROOT}/{TEAM_ROOT}/scouting",)


def test_the_research_phase_reaches_the_whole_lane() -> None:
    """It needs feedback/ to do its job -- which is exactly why it has no network."""

    readable = _offline().readable()
    assert f"{ROOT}/{TEAM_ROOT}" in readable


def test_the_two_phases_share_no_write_surface() -> None:
    isolation.assert_phases_are_separated(_scouting(), _offline())


def test_a_networked_research_phase_is_refused() -> None:
    """Mutation: the separation must be enforced, not merely arranged."""

    broken = isolation.PermissionProfile(
        name="broken",
        phase="research",
        filesystem=_offline().filesystem,
        network_enabled=True,
        web_search=True,
        disabled_capabilities=_offline().disabled_capabilities,
    )
    with pytest.raises(isolation.IsolationError, match="outside the scouting phase"):
        isolation.assert_profile_invariants(broken, root=ROOT, team_root=TEAM_ROOT)


def test_mounting_the_lane_root_while_networked_is_refused() -> None:
    """The single most likely regression: someone 'simplifies' scouting to mount the lane."""

    profile = _scouting()
    widened = isolation.PermissionProfile(
        name=profile.name,
        phase=profile.phase,
        filesystem={**profile.filesystem, f"{ROOT}/{TEAM_ROOT}": isolation.READ},
        network_enabled=True,
        web_search=True,
        disabled_capabilities=profile.disabled_capabilities,
    )
    with pytest.raises(isolation.IsolationError, match="feedback"):
        isolation.assert_profile_invariants(widened, root=ROOT, team_root=TEAM_ROOT)


def test_a_scouting_phase_without_the_network_is_refused() -> None:
    """'Safe' by disabling the phase is not safe, it is broken."""

    profile = _scouting()
    muted = isolation.PermissionProfile(
        name=profile.name,
        phase=profile.phase,
        filesystem=profile.filesystem,
        network_enabled=False,
        web_search=False,
        disabled_capabilities=profile.disabled_capabilities,
    )
    with pytest.raises(isolation.IsolationError, match="cannot do its job"):
        isolation.assert_phases_are_separated(muted, _offline())


# -- what neither phase may reach --------------------------------------------------------------


@pytest.mark.parametrize("profile_name", ["scouting", "offline"])
def test_neither_phase_can_reach_market_data_or_results(profile_name: str) -> None:
    profile = _scouting() if profile_name == "scouting" else _offline()
    isolation.assert_profile_invariants(
        profile, root=ROOT, team_root=TEAM_ROOT, forbidden_roots=FORBIDDEN
    )


def test_a_profile_reaching_the_snapshot_is_refused() -> None:
    profile = _offline()
    leaky = isolation.PermissionProfile(
        name=profile.name,
        phase=profile.phase,
        filesystem={**profile.filesystem, f"{ROOT}/data/top40/snapshot-v3": isolation.READ},
        network_enabled=False,
        web_search=False,
        disabled_capabilities=profile.disabled_capabilities,
    )
    with pytest.raises(isolation.IsolationError, match="forbidden root"):
        isolation.assert_profile_invariants(
            leaky, root=ROOT, team_root=TEAM_ROOT, forbidden_roots=FORBIDDEN
        )


def test_writing_outside_the_lane_is_refused() -> None:
    profile = _offline()
    leaky = isolation.PermissionProfile(
        name=profile.name,
        phase=profile.phase,
        filesystem={**profile.filesystem, f"{ROOT}/tournament/top40-v5/private": isolation.WRITE},
        network_enabled=False,
        web_search=False,
        disabled_capabilities=profile.disabled_capabilities,
    )
    with pytest.raises(isolation.IsolationError, match="write outside its own lane"):
        isolation.assert_profile_invariants(leaky, root=ROOT, team_root=TEAM_ROOT)


def test_a_profile_that_re_enables_a_disabled_capability_is_refused() -> None:
    profile = _offline()
    permissive = isolation.PermissionProfile(
        name=profile.name,
        phase=profile.phase,
        filesystem=profile.filesystem,
        network_enabled=False,
        web_search=False,
        disabled_capabilities=("apps",),
    )
    with pytest.raises(isolation.IsolationError, match="leaves capabilities enabled"):
        isolation.assert_profile_invariants(permissive, root=ROOT, team_root=TEAM_ROOT)


def test_a_lane_cannot_reach_a_peer_lane() -> None:
    peer = TOP40_V5_LAYOUT.team_root("team-08")
    for profile in (_scouting(), _offline()):
        isolation.assert_profile_invariants(
            profile, root=ROOT, team_root=TEAM_ROOT, forbidden_roots=(peer,)
        )


# -- rendering ---------------------------------------------------------------------------------


def test_codex_arguments_carry_the_network_setting_of_their_profile() -> None:
    offline = " ".join(isolation.codex_arguments(_offline()))
    scouting = " ".join(isolation.codex_arguments(_scouting()))
    assert "network.enabled=false" in offline
    assert "network.enabled=true" in scouting


def test_codex_arguments_disable_every_declared_capability() -> None:
    arguments = isolation.codex_arguments(_offline())
    disabled = {arguments[index + 1] for index, item in enumerate(arguments) if item == "--disable"}
    assert disabled == set(_offline().disabled_capabilities)


def test_web_search_is_disabled_offline_and_permitted_while_scouting() -> None:
    offline = isolation.codex_arguments(_offline())
    scouting = isolation.codex_arguments(_scouting())
    assert "standalone_web_search" in offline
    assert "standalone_web_search" not in scouting


def test_the_profile_hash_changes_when_the_surface_changes() -> None:
    """The launch receipt binds this hash; a silent widening must not preserve it."""

    profile = _scouting()
    widened = isolation.PermissionProfile(
        name=profile.name,
        phase=profile.phase,
        filesystem={**profile.filesystem, f"{ROOT}/elsewhere": isolation.READ},
        network_enabled=profile.network_enabled,
        web_search=profile.web_search,
        disabled_capabilities=profile.disabled_capabilities,
    )
    assert profile.sha256() != widened.sha256()


def test_the_profile_hash_is_stable_across_calls() -> None:
    assert _scouting().sha256() == _scouting().sha256()


def test_each_phase_declares_the_probes_it_must_pass() -> None:
    """A networked phase has a different thing to prove than an offline one."""

    scouting = isolation.expected_probe_keys(_scouting())
    offline = isolation.expected_probe_keys(_offline())
    assert "network_allowed" in scouting
    assert "evaluation_surface_denied" in scouting
    assert "network_denied" in offline
    assert "network_allowed" not in offline
