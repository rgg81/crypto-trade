from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from crypto_trade.tournament.top40 import ValidationIssue

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/top40_invalid_team_amendment.py"
SPEC = importlib.util.spec_from_file_location("_test_top40_amendment", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
amendment = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = amendment
SPEC.loader.exec_module(amendment)


def _authorized_issues() -> tuple[ValidationIssue, ...]:
    return (
        ValidationIssue(
            "long_and_short_enabled",
            "hard compliance check failed: long_and_short_enabled",
        ),
        ValidationIssue(
            "long_and_short_enabled",
            "public_oos long realized exposure is immaterial: active_fraction=0.038813, "
            "mean=0.007052",
        ),
        ValidationIssue(
            "long_and_short_enabled",
            "public_oos short realized exposure is immaterial: active_fraction=0.038813, "
            "mean=0.007052",
        ),
    )


def _pre_amendment_state() -> dict[str, object]:
    teams = {
        team_id: {"canonical_run": "complete", "marker": team_id}
        for team_id in amendment.base.TEAM_IDS
    }
    teams[amendment.INVALID_TEAM_ID] = {
        "canonical_run": "failed",
        "canonical_failure_type": "ValueError",
        "canonical_finished_at_utc": "2026-07-15T12:00:00+00:00",
        "marker": amendment.INVALID_TEAM_ID,
    }
    return {"schema_version": 1, "phase": "cohort_frozen", "teams": teams}


def _mechanical_record() -> dict[str, object]:
    return {
        "status": "invalid",
        "amendment_id": amendment.AMENDMENT_ID,
        "amendment_path": amendment.AMENDMENT_PATH,
        "recorded_at_utc": "2026-07-15T12:01:00+00:00",
        "canonical_output_sha256": "a" * 64,
        "validation_issues": [
            {"code": issue.code, "message": issue.message} for issue in _authorized_issues()
        ],
    }


def test_authorized_issue_set_is_exact_and_narrow() -> None:
    amendment._validate_authorized_issue_set(_authorized_issues())
    with pytest.raises(ValueError, match="unexpected issues"):
        amendment._validate_authorized_issue_set(_authorized_issues()[:2])
    with pytest.raises(ValueError, match="unexpected issues"):
        amendment._validate_authorized_issue_set(
            _authorized_issues() + (ValidationIssue("future_data", "unrelated integrity fault"),)
        )
    altered = list(_authorized_issues())
    altered[1] = ValidationIssue(
        "long_and_short_enabled",
        altered[1].message.replace("0.038813", "0.038814"),
    )
    with pytest.raises(ValueError, match="differs|incomplete"):
        amendment._validate_authorized_issue_set(tuple(altered))


def test_exposure_failure_requires_exact_separate_messages() -> None:
    exposure = _authorized_issues()[1:]
    amendment._validate_exposure_failure(exposure)
    merged = ValidationIssue(
        "long_and_short_enabled",
        f"{exposure[0].message}; {exposure[1].message}",
    )
    with pytest.raises(ValueError, match="unexpected canonical issues"):
        amendment._validate_exposure_failure((merged,))


def test_authorized_submission_delta_is_exact_and_nonmutating() -> None:
    original = {
        "team_id": "team-04",
        "compliance": {"long_and_short_enabled": True, "closed_data_only": True},
        "nested": {"unchanged": [1, 2, 3]},
    }
    before = deepcopy(original)
    observed = amendment._authorized_submission_payload(original)
    expected = deepcopy(original)
    expected["compliance"]["long_and_short_enabled"] = False
    assert observed == expected
    assert original == before
    with pytest.raises(ValueError, match="stale true exposure assertion"):
        amendment._authorized_submission_payload(expected)


def test_prepared_state_adds_only_mechanical_validity() -> None:
    original = _pre_amendment_state()
    before = deepcopy(original)
    record = _mechanical_record()
    observed = amendment._prepared_state_payload(original, record)
    expected = deepcopy(original)
    expected["teams"]["team-04"]["mechanical_validity"] = record
    assert observed == expected
    assert original == before
    with pytest.raises(ValueError, match="one-shot amendment preparation"):
        amendment._prepared_state_payload(observed, record)


def test_objective_state_is_exact_authorized_transition() -> None:
    prelock = amendment._prepared_state_payload(_pre_amendment_state(), _mechanical_record())
    objective = {
        "locked_at_utc": "2026-07-15T12:02:00+00:00",
        "cohort_sha256": "b" * 64,
        "schema_version": 2,
    }
    observed = amendment._objective_state_payload(prelock, objective, "a" * 64)
    expected = deepcopy(prelock)
    team = expected["teams"]["team-04"]
    team["canonical_run"] = "complete"
    team.pop("canonical_failure_type")
    team["canonical_output_sha256"] = "a" * 64
    team["canonical_completed_via_amendment_at_utc"] = objective["locked_at_utc"]
    expected["phase"] = "objective_locked"
    expected["objective_lock"] = {
        "path": amendment.OBJECTIVE_LOCK_PATH,
        "sha256": hashlib.sha256(amendment._normalized_json_bytes(objective)).hexdigest(),
        "cohort_sha256": objective["cohort_sha256"],
        "locked_at_utc": objective["locked_at_utc"],
    }
    assert observed == expected
    assert prelock["phase"] == "cohort_frozen"


def test_amendment_excludes_only_team_04() -> None:
    assert amendment.INVALID_TEAM_ID == "team-04"
    assert set(amendment.VALID_TEAM_IDS) == set(amendment.base.TEAM_IDS) - {"team-04"}
    assert len(amendment.VALID_TEAM_IDS) == 9


def test_original_orchestrator_still_matches_phase0_hash() -> None:
    phase0 = json.loads((ROOT / "tournament/top40/phase0_freeze.json").read_text())
    observed = hashlib.sha256((ROOT / "scripts/top40_tournament.py").read_bytes()).hexdigest()
    assert observed == phase0["orchestrator_sha256"]


def test_amendment_changes_only_derived_record_paths() -> None:
    assert set(amendment.AMENDMENT_CHANGED_PATHS) == {
        "tournament/top40/organizer_amendment_01.json",
        "tournament/top40/teams/team-04/submission.json",
        "tournament/top40/run_state.json",
    }


def test_scope_thresholds_and_delegated_commands_are_closed_sets() -> None:
    assert amendment.UNCHANGED_THRESHOLDS == {
        "minimum_side_exposure": 0.01,
        "minimum_side_active_bar_fraction": 0.05,
        "minimum_mean_side_exposure": 0.005,
        "minimum_side_executed_notional_usdt": 1000.0,
    }
    assert amendment.DELEGATED_COMMANDS == {
        "validate",
        "lock-critic",
        "lock-critic-confirmations",
        "lock-user-ballot",
        "score",
        "freeze-winner",
        "verify-winner-freeze",
    }


def test_wrapper_rejects_early_frozen_commands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", [str(SCRIPT), "finalize-team", "team-05"])
    with pytest.raises(ValueError, match="delegates only later commands"):
        amendment.main()


def test_patch_targets_are_exact() -> None:
    originals = (
        amendment.base._locked_cohort,
        amendment.base._verify_objective_lock,
        amendment.base._critic_eliminates_every_mechanical_team,
    )
    try:
        amendment._patch_frozen_orchestrator()
        assert amendment.base._locked_cohort is amendment._amended_locked_cohort
        assert amendment.base._verify_objective_lock is amendment._amended_verify_objective_lock
        assert (
            amendment.base._critic_eliminates_every_mechanical_team
            is amendment._amended_critic_eliminates_every_mechanical_team
        )
    finally:
        (
            amendment.base._locked_cohort,
            amendment.base._verify_objective_lock,
            amendment.base._critic_eliminates_every_mechanical_team,
        ) = originals
