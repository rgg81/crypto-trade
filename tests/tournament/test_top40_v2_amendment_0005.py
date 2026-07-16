"""Focused policy tests for the draft Amendment 0005 gate."""

from __future__ import annotations

import pytest

from crypto_trade.tournament import amendment_0005_v2 as amendment


def test_team03_and_earlier_teams_are_structurally_excluded() -> None:
    with pytest.raises(amendment.Amendment0005Error, match="Team04"):
        amendment._candidate_paths("team-03", "candidate")
    assert amendment.ELIGIBLE_TEAMS == (
        "team-04",
        "team-05",
        "team-06",
        "team-07",
        "team-08",
        "team-09",
        "team-10",
    )


def test_paths_are_derived_and_development_only() -> None:
    paths = amendment._candidate_paths("team-04", "candidate-04")
    assert paths["development_target_path"].endswith(
        "/development-runs/candidate-04/targets.parquet"
    )
    assert paths["evidence_dir"].endswith(
        "/development-score-diagnostics/candidate-04"
    )
    assert all("private" not in value and "final" not in value for value in paths.values())


def test_reservation_is_nonmaterial_and_has_no_caller_stage_or_path() -> None:
    authority = {"team_id": "team-04", "candidate_id": "candidate-04"}
    reservation = amendment._reservation_core(authority, "2026-07-16T00:00:00Z")
    assert reservation["stage"] == "development"
    assert reservation["non_material"] is True
    assert reservation["charges_team_trial_budget"] is False
    assert "requested_stage" not in reservation
    assert "requested_output_path" not in reservation
