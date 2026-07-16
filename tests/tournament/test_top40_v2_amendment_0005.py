"""Focused policy tests for the draft Amendment 0005 gate."""

from __future__ import annotations

import inspect
import os

import pytest

from crypto_trade.tournament import amendment_0005_v2 as amendment
from crypto_trade.tournament import development_score_diagnostics_v5 as diagnostics


def _request() -> diagnostics.DevelopmentScoreDiagnosticRequest:
    sha = "a" * 64
    commit = "b" * 40
    return diagnostics.DevelopmentScoreDiagnosticRequest(
        diagnostic_id="development-score-team-04-candidate-04",
        team_id="team-04",
        family_id="family-04",
        candidate_id="candidate-04",
        registration_input_path="reports-top40-v2/team-04/registration-inputs/candidate-04.json",
        registration_sha256=sha,
        registration_commit=commit,
        strategy_sha256=sha,
        risk_policy_sha256=sha,
        source_bundle_sha256=sha,
        candidate_seed=1,
        config_sha256=sha,
        score_manifest_path="tournament/top40-v2/teams/team-04/score-adapters/candidate-04.json",
        score_manifest_sha256=sha,
        score_manifest_commit=commit,
        semantic_coupling_review_path="tournament/top40-v2/teams/team-04/score-adapters/candidate-04.semantic-coupling-review.json",
        semantic_coupling_review_sha256=sha,
        semantic_coupling_review_commit=commit,
        snapshot_manifest_path="data/snapshot.json",
        snapshot_manifest_sha256=sha,
        development_target_path="reports-top40-v2/team-04/development-runs/candidate-04/targets.parquet",
        development_target_sha256=sha,
        runner_record_path="reports-top40-v2/team-04/qualification-attempts/candidate-04.runner-record.json",
        runner_record_sha256=sha,
        reservation_sha256=sha,
    )


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
    assert paths["result_path"] == f"{paths['evidence_dir']}/terminal-result.json"
    assert all("private" not in value and "final" not in value for value in paths.values())


def test_reservation_is_nonmaterial_and_has_no_caller_stage_or_path() -> None:
    authority = {"team_id": "team-04", "candidate_id": "candidate-04"}
    reservation = amendment._reservation_core(authority, "2026-07-16T00:00:00Z")
    assert reservation["stage"] == "development"
    assert reservation["non_material"] is True
    assert reservation["charges_team_trial_budget"] is False
    assert "requested_stage" not in reservation
    assert "requested_output_path" not in reservation


def test_internal_engine_has_no_caller_selected_output() -> None:
    assert "output_dir" not in inspect.signature(
        diagnostics.run_development_score_diagnostic
    ).parameters
    assert "output_dir" not in inspect.signature(
        diagnostics.run_reserved_development_score_diagnostic
    ).parameters


def test_private_staging_capability_is_derived_and_rejects_traversal(tmp_path) -> None:
    request = _request()
    capability = diagnostics.stage_diagnostic_artifacts(tmp_path, request, {})
    assert capability["staging_path"].startswith(
        "reports-top40-v2/team-04/development-score-diagnostics/.candidate-04."
    )
    assert os.stat(tmp_path / capability["staging_path"]).st_mode & 0o077 == 0
    forged = dict(capability, staging_path="../escape")
    with pytest.raises(ValueError, match="internally derived"):
        diagnostics.validate_staged_artifacts(
            tmp_path, request, forged, completed=False
        )


def test_staging_rejects_symlink_ancestor(tmp_path) -> None:
    (tmp_path / "outside").mkdir()
    (tmp_path / "reports-top40-v2").symlink_to(tmp_path / "outside", target_is_directory=True)
    with pytest.raises(ValueError, match="ancestor"):
        diagnostics.stage_diagnostic_artifacts(tmp_path, _request(), {})


def test_all_captured_a1_helpers_are_identity_bound() -> None:
    assert set(diagnostics.frozen_science_helper_bindings()) == {
        "_materialize_team_tree", "_target_frame_from_bytes", "_targets_exact",
        "_scores_exact", "_target_digest", "_score_digest", "_snapshot_hashes",
        "_parquet_bytes", "_indexed_targets",
    }
    diagnostics.verify_frozen_science_helper_identities()


def test_scope_incident_is_part_of_frozen_implementation_set() -> None:
    assert "tournament/top40-v2/amendments/0005/DRAFT-SCOPE-INCIDENT.md" in (
        amendment.IMPLEMENTATION_FILE_PATHS
    )
