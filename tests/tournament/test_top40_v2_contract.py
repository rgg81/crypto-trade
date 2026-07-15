from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest

from crypto_trade.tournament.layout import TOP40_V2_LAYOUT, TournamentLayout
from crypto_trade.tournament.top40_v2 import (
    TEAM_IDS,
    _validate_config,
    all_teams_terminal_for_qualification,
    finalist_team_ids,
    load_config,
    new_run_state,
    validate_run_state,
)


def _config():
    root = Path(__file__).parents[2]
    return load_config(root / "tournament/top40-v2/config.toml")


def test_v2_layout_is_separate_from_v1():
    assert TOP40_V2_LAYOUT.tournament_root == "tournament/top40-v2"
    assert TOP40_V2_LAYOUT.reports_root == "reports-top40-v2"
    assert TOP40_V2_LAYOUT.team_root("team-10").endswith("teams/team-10")
    with pytest.raises(ValueError, match="unknown tournament team"):
        TOP40_V2_LAYOUT.team_root("team-11")


def test_layout_rejects_path_traversal():
    with pytest.raises(ValueError, match="safe repository-relative"):
        TournamentLayout(
            name="bad-layout",
            branch="bad-layout",
            tournament_root="../escape",
            reports_root="reports-bad",
            orchestrator_script="scripts/bad.py",
            contract_source="src/bad.py",
            team_ids=TEAM_IDS,
        )


def test_config_enforces_zero_oos_views_and_hard_qualification():
    config = _config()
    weakened = deepcopy(config.raw)
    weakened["research_budget"]["maximum_final_oos_views_per_team"] = 1
    with pytest.raises(ValueError, match="research budgets"):
        _validate_config(weakened, TOP40_V2_LAYOUT)

    weakened = deepcopy(config.raw)
    weakened["qualification"]["development"]["minimum_net_sharpe"] = 0.1
    with pytest.raises(ValueError, match="cannot be weaker"):
        _validate_config(weakened, TOP40_V2_LAYOUT)


def test_new_state_tracks_ten_entrants_without_fabricating_finalists():
    config = _config()
    state = new_run_state(config, created_at_utc="2026-07-15T12:00:00+00:00")
    validate_run_state(state, config)

    assert state["phase"] == "phase0_pending"
    assert len(state["teams"]) == 10
    assert finalist_team_ids(state) == ()
    assert not all_teams_terminal_for_qualification(state)


def test_finalist_cohort_uses_only_qualified_teams_and_dnfs_remain_unscored():
    config = _config()
    state = new_run_state(config, created_at_utc="2026-07-15T12:00:00+00:00")
    for team_id in TEAM_IDS:
        team = state["teams"][team_id]
        if team_id in {"team-01", "team-07"}:
            team["status"] = "qualified"
            team["private_attempts"] = 1
            team["private_result"] = {"passed": True}
        else:
            team["status"] = "dnf"
            team["dnf"] = {"reason": "did not qualify"}

    validate_run_state(state, config)
    assert all_teams_terminal_for_qualification(state)
    assert finalist_team_ids(state) == ("team-01", "team-07")
