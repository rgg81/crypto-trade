"""Transparent organizer amendment for one mechanically invalid Top40 entrant.

This wrapper leaves the Phase-0 evaluator, scorer, charter, thresholds, and frozen
``top40_tournament.py`` bytes unchanged.  It records the already-observed Team 04
two-sided-exposure failure, creates an objective lock that retains Team 04 as an
invalid audited entrant, and delegates later lock/scoring commands to the frozen
orchestrator with amendment-aware cohort verification.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path

from crypto_trade.tournament.top40 import (
    OBJECTIVE_LOCK_PATH,
    PHASE0_FREEZE_PATH,
    RUN_STATE_PATH,
    Submission,
    ValidationIssue,
    load_submission,
    score_tournament,
    validate_submission,
    verify_canonical_artifacts,
)

_FROZEN_ORCHESTRATOR_PATH = Path(__file__).with_name("top40_tournament.py")
_SPEC = importlib.util.spec_from_file_location(
    "_frozen_top40_tournament", _FROZEN_ORCHESTRATOR_PATH
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError("cannot load the frozen Top40 orchestrator")
base = importlib.util.module_from_spec(_SPEC)
sys.modules[_SPEC.name] = base
_SPEC.loader.exec_module(base)

AMENDMENT_ID = "organizer-amendment-01-invalid-team-04"
AMENDMENT_PATH = "tournament/top40/organizer_amendment_01.json"
AMENDMENT_TOOL_PATH = "scripts/top40_invalid_team_amendment.py"
INVALID_TEAM_ID = "team-04"
VALID_TEAM_IDS = tuple(team_id for team_id in base.TEAM_IDS if team_id != INVALID_TEAM_ID)
TEAM_SUBMISSION_PATH = f"tournament/top40/teams/{INVALID_TEAM_ID}/submission.json"
AMENDMENT_CHANGED_PATHS = (
    AMENDMENT_PATH,
    TEAM_SUBMISSION_PATH,
    RUN_STATE_PATH,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_object(path: Path, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def _issue_payload(issues: Sequence[ValidationIssue]) -> list[dict[str, str]]:
    return [{"code": issue.code, "message": issue.message} for issue in issues]


def _validate_exposure_failure(issues: Sequence[ValidationIssue]) -> None:
    payload = _issue_payload(issues)
    if len(payload) != 2 or any(item["code"] != "long_and_short_enabled" for item in payload):
        raise ValueError(f"Team 04 has unexpected canonical issues: {payload}")
    messages = {item["message"] for item in payload}
    required_fragments = {
        "public_oos long realized exposure is immaterial",
        "public_oos short realized exposure is immaterial",
    }
    if not all(any(fragment in message for message in messages) for fragment in required_fragments):
        raise ValueError(f"Team 04 exposure failure differs from the authorized case: {payload}")


def _validate_authorized_issue_set(issues: Sequence[ValidationIssue]) -> None:
    payload = _issue_payload(issues)
    if len(payload) != 3 or any(item["code"] != "long_and_short_enabled" for item in payload):
        raise ValueError(f"Team 04 amendment has unexpected issues: {payload}")
    messages = {item["message"] for item in payload}
    required_fragments = {
        "hard compliance check failed: long_and_short_enabled",
        "public_oos long realized exposure is immaterial",
        "public_oos short realized exposure is immaterial",
    }
    if not all(any(fragment in message for message in messages) for fragment in required_fragments):
        raise ValueError(f"Team 04 amendment issue set is incomplete: {payload}")


def _mechanical_issues(submission: Submission, root: Path) -> tuple[ValidationIssue, ...]:
    return validate_submission(submission) + verify_canonical_artifacts(submission, root=root)


def _require_clean_head(root: Path) -> str:
    status = subprocess.run(
        ["git", "status", "--porcelain=v1"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if status:
        raise ValueError(f"amendment operation requires a clean Git HEAD; dirty paths: {status}")
    return base._head_commit(root)


def _require_new_amendment_path(root: Path) -> None:
    path = root / AMENDMENT_PATH
    history = subprocess.run(
        ["git", "log", "--format=%H", "--", AMENDMENT_PATH],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    tracked = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "--", AMENDMENT_PATH],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if path.exists() or path.is_symlink() or history or tracked.returncode == 0:
        raise ValueError("organizer amendment record is single-shot and must be a new path")


def _prepare_amendment() -> int:
    root = Path.cwd().resolve()
    base._require_phase0(root)
    pre_head = _require_clean_head(root)
    _require_new_amendment_path(root)
    state = base._read_state(root)
    teams = state.get("teams")
    if state.get("phase") != "cohort_frozen" or not isinstance(teams, dict):
        raise ValueError("amendment preparation requires the cohort_frozen phase")
    invalid_state = teams.get(INVALID_TEAM_ID)
    if not isinstance(invalid_state, dict) or invalid_state.get("canonical_run") != "failed":
        raise ValueError("Team 04 must retain its recorded failed finalization before amendment")
    if any(
        not isinstance(teams.get(team_id), dict)
        or teams[team_id].get("canonical_run") != "complete"
        for team_id in VALID_TEAM_IDS
    ):
        raise ValueError("all nine mechanically valid teams must finalize before the amendment")
    if invalid_state.get("canonical_failure_type") != "ValueError":
        raise ValueError("Team 04 failure type differs from the canonical validation failure")

    submission_path = root / TEAM_SUBMISSION_PATH
    original_submission_sha256 = _sha256(submission_path)
    original = load_submission(submission_path)
    if original.team_id != INVALID_TEAM_ID or validate_submission(original):
        raise ValueError("Team 04 pre-amendment submission is structurally malformed")
    exposure_issues = verify_canonical_artifacts(original, root=root)
    _validate_exposure_failure(exposure_issues)
    canonical_output_sha256 = base._canonical_output_sha256(root, original)

    raw = _json_object(submission_path, "Team 04 submission")
    compliance = raw.get("compliance")
    if not isinstance(compliance, dict) or compliance.get("long_and_short_enabled") is not True:
        raise ValueError("Team 04 submission does not contain the stale true exposure assertion")
    compliance["long_and_short_enabled"] = False
    base._atomic_write_json(submission_path, raw)
    amended = load_submission(submission_path)
    amendment_issues = _mechanical_issues(amended, root)
    _validate_authorized_issue_set(amendment_issues)

    timestamp = datetime.now(UTC).isoformat()
    mechanical_record: dict[str, object] = {
        "status": "invalid",
        "amendment_id": AMENDMENT_ID,
        "amendment_path": AMENDMENT_PATH,
        "recorded_at_utc": timestamp,
        "canonical_output_sha256": canonical_output_sha256,
        "validation_issues": _issue_payload(amendment_issues),
    }
    phase0_path = root / PHASE0_FREEZE_PATH
    phase0 = _json_object(phase0_path, "Phase-0 freeze")
    tool_path = root / AMENDMENT_TOOL_PATH
    if base._git_file_bytes(root, pre_head, AMENDMENT_TOOL_PATH) != tool_path.read_bytes():
        raise ValueError("amendment tool is not clean at the pre-amendment commit")
    amendment = {
        "schema_version": 1,
        "amendment_id": AMENDMENT_ID,
        "authorized_by": "organizer-user",
        "authorization_text": "yes, go ahead",
        "authorized_scope": (
            "Keep every frozen strategy, threshold, evaluator, scorer, charter, and original "
            "orchestrator unchanged; retain Team 04 as an invalid audited entrant and rank the "
            "remaining mechanically valid teams."
        ),
        "recorded_at_utc": timestamp,
        "pre_amendment_head_commit": pre_head,
        "phase0_freeze_sha256": _sha256(phase0_path),
        "original_orchestrator_sha256": phase0["orchestrator_sha256"],
        "amendment_tool_path": AMENDMENT_TOOL_PATH,
        "amendment_tool_sha256": _sha256(tool_path),
        "invalid_team_id": INVALID_TEAM_ID,
        "valid_team_ids": list(VALID_TEAM_IDS),
        "unchanged_thresholds": {
            "minimum_side_exposure": 0.01,
            "minimum_side_active_bar_fraction": 0.05,
            "minimum_mean_side_exposure": 0.005,
            "minimum_side_executed_notional_usdt": 1000.0,
        },
        "original_submission_sha256": original_submission_sha256,
        "amended_submission_sha256": _sha256(submission_path),
        "artifact_manifest_path": amended.artifacts["artifact_manifest"],
        "artifact_manifest_file_sha256": _sha256(root / amended.artifacts["artifact_manifest"]),
        "artifact_manifest_sha256": amended.artifact_manifest_sha256,
        "canonical_output_sha256": canonical_output_sha256,
        "validation_issues": _issue_payload(amendment_issues),
        "changed_paths": list(AMENDMENT_CHANGED_PATHS),
        "mechanical_validity_state": mechanical_record,
    }
    base._atomic_write_json(root / AMENDMENT_PATH, amendment)
    with base._edit_run_state(root) as locked:
        current = locked.get("teams", {}).get(INVALID_TEAM_ID)
        if (
            locked.get("phase") != "cohort_frozen"
            or not isinstance(current, dict)
            or current != invalid_state
        ):
            raise ValueError("tournament state changed during amendment preparation")
        current["mechanical_validity"] = mechanical_record
    print(f"prepared {AMENDMENT_ID}; commit exactly {', '.join(AMENDMENT_CHANGED_PATHS)}")
    return 0


def _amendment_record_commit(root: Path, amendment: Mapping[str, object]) -> str:
    pre_head = amendment.get("pre_amendment_head_commit")
    if not isinstance(pre_head, str):
        raise ValueError("amendment pre-head binding is malformed")
    record_commit = base._unique_first_add_commit(
        root,
        AMENDMENT_PATH,
        expected_parent=pre_head,
        label="organizer amendment",
    )
    changed = subprocess.run(
        ["git", "diff-tree", "--no-commit-id", "--name-only", "-r", record_commit],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if set(changed) != set(AMENDMENT_CHANGED_PATHS):
        raise ValueError(f"amendment commit changed unexpected paths: {sorted(changed)}")
    return record_commit


def _verify_amendment(root: Path) -> tuple[dict[str, object], str]:
    amendment_path = root / AMENDMENT_PATH
    amendment = _json_object(amendment_path, "organizer amendment")
    expected_keys = {
        "schema_version",
        "amendment_id",
        "authorized_by",
        "authorization_text",
        "authorized_scope",
        "recorded_at_utc",
        "pre_amendment_head_commit",
        "phase0_freeze_sha256",
        "original_orchestrator_sha256",
        "amendment_tool_path",
        "amendment_tool_sha256",
        "invalid_team_id",
        "valid_team_ids",
        "unchanged_thresholds",
        "original_submission_sha256",
        "amended_submission_sha256",
        "artifact_manifest_path",
        "artifact_manifest_file_sha256",
        "artifact_manifest_sha256",
        "canonical_output_sha256",
        "validation_issues",
        "changed_paths",
        "mechanical_validity_state",
    }
    if (
        set(amendment) != expected_keys
        or amendment["schema_version"] != 1
        or amendment["amendment_id"] != AMENDMENT_ID
        or amendment["authorized_by"] != "organizer-user"
        or amendment["authorization_text"] != "yes, go ahead"
        or amendment["invalid_team_id"] != INVALID_TEAM_ID
        or amendment["valid_team_ids"] != list(VALID_TEAM_IDS)
        or amendment["changed_paths"] != list(AMENDMENT_CHANGED_PATHS)
    ):
        raise ValueError("organizer amendment schema or authorization binding is invalid")
    base._utc_timestamp(amendment["recorded_at_utc"], "amendment.recorded_at_utc")
    phase0_path = root / PHASE0_FREEZE_PATH
    phase0 = _json_object(phase0_path, "Phase-0 freeze")
    tool_path = root / AMENDMENT_TOOL_PATH
    if (
        amendment["phase0_freeze_sha256"] != _sha256(phase0_path)
        or amendment["original_orchestrator_sha256"] != phase0.get("orchestrator_sha256")
        or amendment["amendment_tool_path"] != AMENDMENT_TOOL_PATH
        or amendment["amendment_tool_sha256"] != _sha256(tool_path)
    ):
        raise ValueError("amendment no longer matches Phase-0 or its organizer tool")
    pre_head = amendment["pre_amendment_head_commit"]
    if (
        not isinstance(pre_head, str)
        or base._git_file_bytes(root, pre_head, AMENDMENT_TOOL_PATH) != tool_path.read_bytes()
    ):
        raise ValueError("amendment tool differs from its pre-amendment committed bytes")
    original_submission = base._git_file_bytes(root, pre_head, TEAM_SUBMISSION_PATH)
    if amendment["original_submission_sha256"] != hashlib.sha256(original_submission).hexdigest():
        raise ValueError("amendment original-submission binding differs from its pre-head bytes")
    record_commit = _amendment_record_commit(root, amendment)

    submission_path = root / TEAM_SUBMISSION_PATH
    if (
        base._git_file_bytes(root, record_commit, TEAM_SUBMISSION_PATH)
        != submission_path.read_bytes()
    ):
        raise ValueError("Team 04 amended submission changed after the amendment commit")
    submission = load_submission(submission_path)
    if (
        amendment["amended_submission_sha256"] != _sha256(submission_path)
        or amendment["artifact_manifest_path"] != submission.artifacts["artifact_manifest"]
        or amendment["artifact_manifest_file_sha256"]
        != _sha256(root / submission.artifacts["artifact_manifest"])
        or amendment["artifact_manifest_sha256"] != submission.artifact_manifest_sha256
        or amendment["canonical_output_sha256"] != base._canonical_output_sha256(root, submission)
    ):
        raise ValueError("Team 04 amended submission or canonical outputs changed")
    issues = _mechanical_issues(submission, root)
    _validate_authorized_issue_set(issues)
    if amendment["validation_issues"] != _issue_payload(issues):
        raise ValueError("amendment issue binding differs from live Team 04 evidence")
    state = base._read_state(root)
    team_state = state.get("teams", {}).get(INVALID_TEAM_ID)
    if (
        not isinstance(team_state, dict)
        or team_state.get("mechanical_validity") != amendment["mechanical_validity_state"]
    ):
        raise ValueError("run_state differs from the organizer amendment")
    return amendment, record_commit


def _submission_integrity_issues(
    root: Path, submission: Submission, *, require_complete_state: bool
) -> tuple[ValidationIssue, ...]:
    if require_complete_state:
        return base._submission_preflight_issues(submission, root)
    state = base._read_state(root)
    team_state = state.get("teams", {}).get(submission.team_id)
    champion = team_state.get("champion") if isinstance(team_state, dict) else None
    if (
        not isinstance(team_state, dict)
        or not isinstance(champion, dict)
        or champion.get("freeze_commit") != submission.freeze_commit
        or champion.get("strategy_name") != submission.strategy_name
        or champion.get("strategy_sha256") != submission.strategy_sha256
    ):
        return (ValidationIssue("run_state", "Team 04 champion identity binding failed"),)
    try:
        base._validate_team_freeze_inputs(
            root, submission.team_id, submission.freeze_commit, team_state
        )
    except ValueError as exc:
        return (ValidationIssue("team_freeze", str(exc)),)
    return ()


def _load_amended_cohort(root: Path, *, prelock: bool) -> list[Submission]:
    amendment, _record_commit = _verify_amendment(root)
    submissions: list[Submission] = []
    for team_id in base.TEAM_IDS:
        submission_path = root / f"tournament/top40/teams/{team_id}/submission.json"
        submission = load_submission(submission_path)
        if submission.team_id != team_id:
            raise ValueError(f"canonical submission path is impersonated for {team_id}")
        mechanical = _mechanical_issues(submission, root)
        integrity = _submission_integrity_issues(
            root,
            submission,
            require_complete_state=not (prelock and team_id == INVALID_TEAM_ID),
        )
        if integrity:
            detail = "; ".join(f"{issue.code}: {issue.message}" for issue in integrity)
            raise ValueError(f"{team_id} integrity verification failed: {detail}")
        if team_id == INVALID_TEAM_ID:
            _validate_authorized_issue_set(mechanical)
            if amendment["validation_issues"] != _issue_payload(mechanical):
                raise ValueError("Team 04 issues differ from the amendment record")
        elif mechanical:
            detail = "; ".join(f"{issue.code}: {issue.message}" for issue in mechanical)
            raise ValueError(f"{team_id} must remain mechanically valid: {detail}")
        submissions.append(submission)
    scores = score_tournament(submissions)
    valid = {score.team_id for score in scores if score.valid}
    invalid = {score.team_id for score in scores if not score.valid}
    if valid != set(VALID_TEAM_IDS) or invalid != {INVALID_TEAM_ID}:
        raise ValueError(
            "amended scorer did not produce exactly nine valid teams and Team 04 invalid"
        )
    return submissions


def _team_bindings(
    root: Path,
    state: Mapping[str, object],
    submissions: Sequence[Submission],
    *,
    invalid_output_sha256: str | None = None,
) -> list[dict[str, object]]:
    scores = {score.team_id: score for score in score_tournament(submissions)}
    teams_state = state.get("teams")
    if not isinstance(teams_state, dict):
        raise ValueError("run_state teams are malformed")
    bindings: list[dict[str, object]] = []
    for submission in sorted(submissions, key=lambda item: item.team_id):
        team_state = teams_state.get(submission.team_id)
        if not isinstance(team_state, dict):
            raise ValueError(f"missing run_state entry for {submission.team_id}")
        output_sha = (
            invalid_output_sha256
            if submission.team_id == INVALID_TEAM_ID and invalid_output_sha256 is not None
            else team_state.get("canonical_output_sha256")
        )
        if not isinstance(output_sha, str) or output_sha != base._canonical_output_sha256(
            root, submission
        ):
            raise ValueError(f"canonical output hash differs for {submission.team_id}")
        mechanical = _mechanical_issues(submission, root)
        score = scores[submission.team_id]
        submission_path = root / f"tournament/top40/teams/{submission.team_id}/submission.json"
        artifact_path = root / submission.artifacts["artifact_manifest"]
        bindings.append(
            {
                "team_id": submission.team_id,
                "freeze_commit": submission.freeze_commit,
                "submission_path": submission_path.relative_to(root).as_posix(),
                "submission_sha256": _sha256(submission_path),
                "artifact_manifest_path": submission.artifacts["artifact_manifest"],
                "artifact_manifest_file_sha256": _sha256(artifact_path),
                "artifact_manifest_sha256": submission.artifact_manifest_sha256,
                "canonical_output_sha256": output_sha,
                "mechanically_valid": not mechanical,
                "validation_issues": _issue_payload(mechanical),
                "automatic_score": score.automatic_score,
                "objective_rank": score.objective_rank,
            }
        )
    return bindings


def _lock_objective() -> int:
    root = Path.cwd().resolve()
    base._require_phase0(root)
    prelock_head = _require_clean_head(root)
    amendment, amendment_record_commit = _verify_amendment(root)
    if prelock_head != amendment_record_commit:
        raise ValueError("objective lock must directly follow the committed amendment record")
    state = base._read_state(root)
    teams = state.get("teams")
    if state.get("phase") != "cohort_frozen" or not isinstance(teams, dict):
        raise ValueError("amended objective lock requires the cohort_frozen phase")
    if (root / OBJECTIVE_LOCK_PATH).exists() or (root / OBJECTIVE_LOCK_PATH).is_symlink():
        raise ValueError("objective lock is single-shot and already exists")
    if any(teams[team_id].get("canonical_run") != "complete" for team_id in VALID_TEAM_IDS):
        raise ValueError("all nine valid teams must have complete canonical runs")
    invalid_state = teams.get(INVALID_TEAM_ID)
    if not isinstance(invalid_state, dict) or invalid_state.get("canonical_run") != "failed":
        raise ValueError("Team 04 must still show the recorded canonical validation failure")
    submissions = _load_amended_cohort(root, prelock=True)
    invalid_output_sha = amendment["canonical_output_sha256"]
    if not isinstance(invalid_output_sha, str):
        raise ValueError("amendment canonical-output binding is malformed")
    bindings = _team_bindings(
        root,
        state,
        submissions,
        invalid_output_sha256=invalid_output_sha,
    )

    phase0_path = root / PHASE0_FREEZE_PATH
    phase0 = _json_object(phase0_path, "Phase-0 freeze")
    phase0_record_commit = base._unique_first_add_commit(
        root,
        PHASE0_FREEZE_PATH,
        expected_parent=phase0["common_freeze_commit"],
        label="Phase-0 freeze",
    )
    locked_at = datetime.now(UTC).isoformat()
    payload = {
        "schema_version": 2,
        "locked_at_utc": locked_at,
        "prelock_head_commit": prelock_head,
        "phase0_record_commit": phase0_record_commit,
        "phase0_freeze_sha256": _sha256(phase0_path),
        "common_freeze_commit": phase0["common_freeze_commit"],
        "data_manifest_sha256": phase0["data_manifest_sha256"],
        "evaluator_sha256": phase0["evaluator_sha256"],
        "config_sha256": phase0["config_sha256"],
        "amendment_id": AMENDMENT_ID,
        "amendment_path": AMENDMENT_PATH,
        "amendment_sha256": _sha256(root / AMENDMENT_PATH),
        "amendment_record_commit": amendment_record_commit,
        "amendment_tool_path": AMENDMENT_TOOL_PATH,
        "amendment_tool_sha256": _sha256(root / AMENDMENT_TOOL_PATH),
        "mechanically_valid_team_ids": list(VALID_TEAM_IDS),
        "cohort_sha256": base._cohort_sha256(submissions),
        "teams": bindings,
    }
    with base._edit_run_state(root) as locked:
        if locked != state or locked.get("phase") != "cohort_frozen":
            raise ValueError("tournament state changed before amended objective locking")
        current = locked["teams"][INVALID_TEAM_ID]
        current["canonical_run"] = "complete"
        current["canonical_output_sha256"] = invalid_output_sha
        current["canonical_completed_via_amendment_at_utc"] = locked_at
        current.pop("canonical_failure_type", None)
        if not all(
            locked["teams"][team_id].get("canonical_run") == "complete" for team_id in base.TEAM_IDS
        ):
            raise ValueError("amended objective lock still lacks a completed canonical cohort")
        base._atomic_write_json(root / OBJECTIVE_LOCK_PATH, payload)
        locked["phase"] = "objective_locked"
        locked["objective_lock"] = {
            "path": OBJECTIVE_LOCK_PATH,
            "sha256": _sha256(root / OBJECTIVE_LOCK_PATH),
            "cohort_sha256": payload["cohort_sha256"],
            "locked_at_utc": locked_at,
        }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def _amended_locked_cohort(root: Path) -> list[Submission]:
    return _load_amended_cohort(root, prelock=False)


def _amended_verify_objective_lock(
    root: Path, state: Mapping[str, object]
) -> tuple[list[Submission], dict[str, object], str]:
    allowed_phases = {
        "objective_locked",
        "critic_locked",
        "dq_confirmed",
        "user_locked",
        "paper_frozen",
    }
    if state.get("phase") not in allowed_phases:
        raise ValueError("amended objective verification requires an objective-or-later phase")
    lock_path = root / OBJECTIVE_LOCK_PATH
    lock = _json_object(lock_path, "amended objective lock")
    expected_keys = {
        "schema_version",
        "locked_at_utc",
        "prelock_head_commit",
        "phase0_record_commit",
        "phase0_freeze_sha256",
        "common_freeze_commit",
        "data_manifest_sha256",
        "evaluator_sha256",
        "config_sha256",
        "amendment_id",
        "amendment_path",
        "amendment_sha256",
        "amendment_record_commit",
        "amendment_tool_path",
        "amendment_tool_sha256",
        "mechanically_valid_team_ids",
        "cohort_sha256",
        "teams",
    }
    if set(lock) != expected_keys or lock["schema_version"] != 2:
        raise ValueError("amended objective lock has an invalid schema")
    base._utc_timestamp(lock["locked_at_utc"], "objective_lock.locked_at_utc")
    record = state.get("objective_lock")
    lock_sha = _sha256(lock_path)
    if not isinstance(record, dict) or (
        record.get("path") != OBJECTIVE_LOCK_PATH
        or record.get("sha256") != lock_sha
        or record.get("cohort_sha256") != lock["cohort_sha256"]
        or record.get("locked_at_utc") != lock["locked_at_utc"]
    ):
        raise ValueError("run_state differs from the amended objective lock")
    prelock_head = lock["prelock_head_commit"]
    if not isinstance(prelock_head, str):
        raise ValueError("amended objective prelock commit is invalid")
    objective_record_commit = base._unique_first_add_commit(
        root,
        OBJECTIVE_LOCK_PATH,
        expected_parent=prelock_head,
        label="amended objective lock",
    )
    objective_changed = subprocess.run(
        [
            "git",
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            objective_record_commit,
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if set(objective_changed) != {OBJECTIVE_LOCK_PATH, RUN_STATE_PATH}:
        raise ValueError(
            f"amended objective-lock commit changed unexpected paths: {sorted(objective_changed)}"
        )
    amendment, amendment_record_commit = _verify_amendment(root)
    if (
        prelock_head != amendment_record_commit
        or lock["amendment_id"] != AMENDMENT_ID
        or lock["amendment_path"] != AMENDMENT_PATH
        or lock["amendment_sha256"] != _sha256(root / AMENDMENT_PATH)
        or lock["amendment_record_commit"] != amendment_record_commit
        or lock["amendment_tool_path"] != AMENDMENT_TOOL_PATH
        or lock["amendment_tool_sha256"] != _sha256(root / AMENDMENT_TOOL_PATH)
        or lock["mechanically_valid_team_ids"] != list(VALID_TEAM_IDS)
    ):
        raise ValueError("objective lock differs from its organizer amendment")
    if amendment["canonical_output_sha256"] != state["teams"][INVALID_TEAM_ID].get(
        "canonical_output_sha256"
    ):
        raise ValueError("Team 04 state differs from the amendment output binding")

    phase0_path = root / PHASE0_FREEZE_PATH
    phase0 = _json_object(phase0_path, "Phase-0 freeze")
    phase0_record_commit = base._unique_first_add_commit(
        root,
        PHASE0_FREEZE_PATH,
        expected_parent=phase0["common_freeze_commit"],
        label="Phase-0 freeze",
    )
    phase0_bindings = {
        "phase0_record_commit": phase0_record_commit,
        "phase0_freeze_sha256": _sha256(phase0_path),
        "common_freeze_commit": phase0["common_freeze_commit"],
        "data_manifest_sha256": phase0["data_manifest_sha256"],
        "evaluator_sha256": phase0["evaluator_sha256"],
        "config_sha256": phase0["config_sha256"],
    }
    if any(lock[field] != value for field, value in phase0_bindings.items()):
        raise ValueError("amended objective lock Phase-0 binding changed")
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", phase0_record_commit, prelock_head],
        cwd=root,
        check=False,
        capture_output=True,
    )
    if ancestry.returncode != 0:
        raise ValueError("amended objective lock does not descend from Phase-0")

    submissions = _amended_locked_cohort(root)
    expected_bindings = _team_bindings(root, state, submissions)
    if (
        lock["cohort_sha256"] != base._cohort_sha256(submissions)
        or lock["teams"] != expected_bindings
    ):
        raise ValueError("amended objective lock differs from live submissions/artifacts/scores")
    return submissions, lock, objective_record_commit


def _amended_critic_eliminates_every_mechanical_team(
    _mechanically_valid: set[str],
    critic_issues: Mapping[str, Sequence[ValidationIssue]],
) -> bool:
    mechanically_valid = set(VALID_TEAM_IDS)
    return all(critic_issues.get(team_id) for team_id in mechanically_valid)


def _patch_frozen_orchestrator() -> None:
    base._locked_cohort = _amended_locked_cohort
    base._verify_objective_lock = _amended_verify_objective_lock
    base._critic_eliminates_every_mechanical_team = _amended_critic_eliminates_every_mechanical_team


def _print_help() -> None:
    print(
        "usage: top40_invalid_team_amendment.py "
        "{prepare-amendment,lock-objective,<frozen-command>} ...\n\n"
        "prepare-amendment  record Team 04's authorized mechanical invalidity\n"
        "lock-objective     create the nine-valid-team amended objective lock\n"
        "<frozen-command>   delegate a later frozen command with amended verification"
    )


def main() -> int:
    command = sys.argv[1] if len(sys.argv) > 1 else None
    if command in {None, "-h", "--help"}:
        _print_help()
        return 0
    if command == "prepare-amendment":
        if len(sys.argv) != 2:
            raise ValueError("prepare-amendment accepts no additional arguments")
        return _prepare_amendment()
    if command == "lock-objective":
        if len(sys.argv) != 2:
            raise ValueError("lock-objective accepts no additional arguments")
        return _lock_objective()
    _patch_frozen_orchestrator()
    return base.main()


if __name__ == "__main__":
    raise SystemExit(main())
