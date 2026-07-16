"""Focused policy tests for the draft Amendment 0005 gate."""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urljoin

import pytest

from crypto_trade.tournament import amendment_0005_v2 as amendment
from crypto_trade.tournament import development_score_diagnostics_v5 as diagnostics
from crypto_trade.tournament import runner_v2
from crypto_trade.tournament import score_diagnostic_compat_v2 as compatibility
from crypto_trade.tournament.amendment_integrity_v2 import pretty_json_bytes, sha256_bytes
from crypto_trade.tournament.top40_v2 import LoadedV2Config

ROOT = Path(__file__).resolve().parents[2]


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
        executable_source_manifest_path="tournament/top40-v2/teams/team-04/score-adapters/candidate-04.executable-source-manifest.json",
        executable_source_manifest_sha256=sha,
        executable_source_manifest_commit=commit,
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


def _install_exact_a2(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    *,
    changed_after: bool = False,
) -> tuple[LoadedV2Config, dict[str, Any]]:
    config = LoadedV2Config(tmp_path / "config.toml", "a" * 64, {})
    state = {"schema_version": 3, "state_schema": "top40-v2-amendment-aware-state-v1"}
    before = pretty_json_bytes(state)
    after = pretty_json_bytes({**state, "changed": True}) if changed_after else before
    snapshots = iter(
        [
            compatibility._StateSnapshot(before, sha256_bytes(before)),
            compatibility._StateSnapshot(after, sha256_bytes(after)),
        ]
    )
    monkeypatch.setattr(compatibility, "_load_canonical_config", lambda _root: config)
    monkeypatch.setattr(
        compatibility,
        "_read_exact_schema3_state",
        lambda _root, _config, *, amended_validator: next(snapshots),
    )
    monkeypatch.setattr(
        compatibility.amendment_v2,
        "validate_amended_run_state",
        lambda _state, _config: None,
    )
    return config, state


def _reservation() -> tuple[dict[str, Any], dict[str, str]]:
    sha = "a" * 64
    commit = "b" * 40
    paths = dict(amendment._candidate_paths("team-04", "candidate-04"))
    authority: dict[str, Any] = {key: sha for key in amendment._AUTHORITY_KEYS}
    authority.update(
        {
            "team_id": "team-04",
            "family_id": "family-04",
            "candidate_id": "candidate-04",
            "registration_input_path": paths["registration_input_path"],
            "score_manifest_path": paths["score_manifest_path"],
            "executable_source_manifest_path": paths["executable_source_manifest_path"],
            "semantic_coupling_review_path": paths["semantic_coupling_review_path"],
            "development_target_path": paths["development_target_path"],
            "runner_record_path": paths["runner_record_path"],
            "registration_commit": commit,
            "score_manifest_commit": commit,
            "executable_source_manifest_commit": commit,
            "semantic_coupling_review_commit": commit,
            "amendment_freeze_commit": commit,
            "candidate_seed": 1,
            "registration_event_sequence": 26,
            "trial_result_event_sequence": 27,
            "research_journal_record_count": 27,
        }
    )
    core = amendment._reservation_core(authority, "2026-07-16T00:00:00Z")
    return {**core, "reservation_sha256": sha256_bytes(pretty_json_bytes(core))}, paths


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
    assert paths["evidence_dir"].endswith("/development-score-diagnostics/candidate-04")
    assert paths["result_path"] == f"{paths['evidence_dir']}/terminal-result.json"
    assert paths["executable_source_manifest_path"].endswith(
        "/candidate-04.executable-source-manifest.json"
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


def test_internal_engine_has_no_caller_selected_output() -> None:
    assert (
        "output_dir"
        not in inspect.signature(diagnostics.run_development_score_diagnostic).parameters
    )
    assert (
        "output_dir"
        not in inspect.signature(diagnostics.run_reserved_development_score_diagnostic).parameters
    )


def test_private_staging_capability_is_derived_and_rejects_traversal(tmp_path) -> None:
    request = _request()
    capability = diagnostics.stage_diagnostic_artifacts(tmp_path, request, {})
    assert capability["staging_path"].startswith(
        "reports-top40-v2/team-04/development-score-diagnostics/.candidate-04."
    )
    assert os.stat(tmp_path / capability["staging_path"]).st_mode & 0o077 == 0
    forged = dict(capability, staging_path="../escape")
    with pytest.raises(ValueError, match="internally derived"):
        diagnostics.validate_staged_artifacts(tmp_path, request, forged, completed=False)


def test_staging_rejects_symlink_ancestor(tmp_path) -> None:
    (tmp_path / "outside").mkdir()
    (tmp_path / "reports-top40-v2").symlink_to(tmp_path / "outside", target_is_directory=True)
    with pytest.raises(ValueError, match="ancestor"):
        diagnostics.stage_diagnostic_artifacts(tmp_path, _request(), {})


def test_all_captured_a1_helpers_are_identity_bound() -> None:
    assert set(diagnostics.frozen_science_helper_bindings()) == {
        "_materialize_team_tree",
        "_target_frame_from_bytes",
        "_targets_exact",
        "_scores_exact",
        "_target_digest",
        "_score_digest",
        "_snapshot_hashes",
        "_parquet_bytes",
        "_indexed_targets",
    }
    diagnostics.verify_frozen_science_helper_identities()


def test_scope_incident_is_part_of_frozen_implementation_set() -> None:
    assert "tournament/top40-v2/amendments/0005/DRAFT-SCOPE-INCIDENT.md" in (
        amendment.IMPLEMENTATION_FILE_PATHS
    )


def test_real_active_a6_parent_and_pure_crypto_audit_are_bound() -> None:
    amendment.verify_parent_authorities(ROOT)
    report = amendment._verified_pure_crypto_audit(ROOT)
    assert len(report) == amendment.A6_CANONICAL_AUDIT_SIZE
    assert sha256_bytes(report) == amendment.A6_CANONICAL_AUDIT_SHA256


@pytest.mark.parametrize("status", ["completed", "failed"])
def test_exact_frozen_a2_atomic_lifecycle_and_idempotent_retry(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    status: str,
) -> None:
    config, state = _install_exact_a2(monkeypatch, tmp_path)
    reservation, paths = _reservation()
    request = amendment._request(reservation)
    statistics = {"development_pearson": 0.25, "qualification_gate": False}

    def frozen_runner(
        *, root: Path, request: diagnostics.DevelopmentScoreDiagnosticRequest, staged_artifact_sink
    ) -> dict[str, object]:
        runner_v2.tournament_contract.validate_run_state(state, config)
        artifacts: dict[str, bytes] = {}
        if status == "completed":
            artifacts = {name: b"artifact" for name in diagnostics.REQUIRED_ARTIFACT_NAMES}
            artifacts["diagnostic-summary.json"] = pretty_json_bytes(
                {
                    "reservation_sha256": request.reservation_sha256,
                    "executable_source_manifest_sha256": (
                        request.executable_source_manifest_sha256
                    ),
                    "semantic_coupling_review_sha256": request.semantic_coupling_review_sha256,
                    "statistics": statistics,
                }
            )
        capability = diagnostics.stage_diagnostic_artifacts(root, request, artifacts)
        staged_artifact_sink(capability)
        return {
            "status": status,
            "failure_reason": None if status == "completed" else "expected failure",
            "organizer_cpu_hours": 0.0,
            "organizer_wall_clock_hours": 0.0,
        }

    monkeypatch.setattr(diagnostics, "run_reserved_development_score_diagnostic", frozen_runner)
    outcome, capability = amendment._run_through_frozen_a2(tmp_path, request)
    assert set(outcome) == {
        "status",
        "failure_reason",
        "organizer_cpu_hours",
        "organizer_wall_clock_hours",
    }
    stage, artifact_hashes = diagnostics.validate_staged_artifacts(
        tmp_path, request, capability, completed=status == "completed"
    )
    authority = {key: reservation[key] for key in amendment._AUTHORITY_KEYS}
    core = {
        "schema_version": 1,
        "event_type": "development_score_diagnostic_recorded",
        "diagnostic_kind": diagnostics.DIAGNOSTIC_KIND,
        "diagnostic_id": reservation["diagnostic_id"],
        "stage": "development",
        "team_id": "team-04",
        "candidate_id": "candidate-04",
        "reservation_sha256": reservation["reservation_sha256"],
        "authority_sha256": sha256_bytes(pretty_json_bytes(authority)),
        "executable_source_manifest_sha256": reservation["executable_source_manifest_sha256"],
        "semantic_coupling_review_sha256": reservation["semantic_coupling_review_sha256"],
        "status": status,
        "failure_reason": outcome["failure_reason"],
        "organizer_cpu_hours": 0.0,
        "organizer_wall_clock_hours": 0.0,
        "artifact_hashes": dict(artifact_hashes),
        "statistics": statistics if status == "completed" else None,
        "declared_score_diagnostic_only": True,
        "non_material": True,
        "charges_team_trial_budget": False,
        "automatic_qualification_gate": False,
    }
    result = {**core, "result_sha256": sha256_bytes(pretty_json_bytes(core))}
    amendment.atomic_write_bytes(
        stage / amendment.TERMINAL_RESULT_NAME, pretty_json_bytes(result), mode=0o600
    )
    destination = tmp_path / paths["evidence_dir"]
    assert amendment._rename_directory_noreplace(stage, destination) is True
    first = amendment._load_existing_transaction(tmp_path, paths, reservation)
    second = amendment._load_existing_transaction(tmp_path, paths, reservation)
    assert first == second == result


def test_exact_frozen_a2_rejection_cleans_private_staging(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    config, state = _install_exact_a2(monkeypatch, tmp_path, changed_after=True)
    reservation, paths = _reservation()
    request = amendment._request(reservation)

    def frozen_runner(*, root: Path, request, staged_artifact_sink) -> dict[str, object]:
        runner_v2.tournament_contract.validate_run_state(state, config)
        staged_artifact_sink(diagnostics.stage_diagnostic_artifacts(root, request, {}))
        return {
            "status": "failed",
            "failure_reason": "expected failure",
            "organizer_cpu_hours": 0.0,
            "organizer_wall_clock_hours": 0.0,
        }

    monkeypatch.setattr(diagnostics, "run_reserved_development_score_diagnostic", frozen_runner)
    with pytest.raises(compatibility.ScoreDiagnosticCompatibilityError, match="state changed"):
        amendment._run_through_frozen_a2(tmp_path, request)
    parent = (tmp_path / paths["evidence_dir"]).parent
    assert not [path for path in parent.iterdir() if path.name.endswith(".staged")]


def test_noreplace_publication_never_replaces_a_raced_destination(tmp_path: Path) -> None:
    parent = tmp_path / "evidence"
    parent.mkdir()
    stage = parent / ".candidate.staged"
    stage.mkdir(mode=0o700)
    destination = parent / "candidate"
    destination.mkdir()
    (destination / "sentinel").write_bytes(b"original")
    assert amendment._rename_directory_noreplace(stage, destination) is False
    assert (destination / "sentinel").read_bytes() == b"original"
    assert stage.is_dir()


def _schema_refs(value: object):
    if isinstance(value, dict):
        if isinstance(value.get("$ref"), str):
            yield value["$ref"]
        for nested in value.values():
            yield from _schema_refs(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _schema_refs(nested)


def _resolve_schema_ref(
    registry: dict[str, dict[str, Any]], base_uri: str, reference: str
) -> object:
    document_uri, fragment = urldefrag(urljoin(base_uri, reference))
    target: object = registry[document_uri]
    if fragment:
        if not fragment.startswith("/"):
            raise AssertionError(f"unsupported non-pointer schema fragment: {fragment}")
        for raw_part in fragment[1:].split("/"):
            part = raw_part.replace("~1", "/").replace("~0", "~")
            assert isinstance(target, dict) and part in target
            target = target[part]
    return target


def test_all_schemas_resolve_with_an_explicit_draft_2020_12_registry() -> None:
    root = Path(__file__).resolve().parents[2]
    template_root = root / "tournament/top40-v2/amendments/0005/templates"
    schemas = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(template_root.glob("*.schema.json"))
    }
    registry = {schema["$id"]: schema for schema in schemas.values()}
    assert len(registry) == len(schemas)
    resolved: list[tuple[str, str, object]] = []
    for name, schema in schemas.items():
        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"].startswith(
            "https://crypto-trade.invalid/schemas/top40-v2/amendments/0005/"
        )
        for reference in _schema_refs(schema):
            target = _resolve_schema_ref(registry, schema["$id"], reference)
            assert isinstance(target, dict)
            resolved.append((name, reference, target))
    assert any(
        name == "amendment-freeze.schema.json"
        and reference.startswith(
            "https://crypto-trade.invalid/schemas/top40-v2/amendments/0005/"
            "amendment-review.schema.json#"
        )
        for name, reference, _target in resolved
    )
