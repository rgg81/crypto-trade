from __future__ import annotations

import dataclasses
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import pytest

from crypto_trade.tournament import amended_orchestrator_v2 as amended_orchestrator
from crypto_trade.tournament import amendment_integrity_v2 as integrity
from crypto_trade.tournament import amendment_v2 as amendment
from crypto_trade.tournament import score_diagnostics_v2 as score_diagnostics
from crypto_trade.tournament.layout import TOP40_V2_LAYOUT
from crypto_trade.tournament.research_v2 import (
    JournalState,
    ResearchPolicy,
    build_trial_registration,
    build_trial_result,
    plan_genesis,
    plan_registration_append,
    plan_result_append,
    validate_journal_bytes,
)
from crypto_trade.tournament.top40_v2 import (
    PHASE0_FROZEN_FILES,
    TEAM_IDS,
    LoadedV2Config,
    load_config,
    new_run_state,
    validate_run_state,
)

REPOSITORY = Path(__file__).parents[2]
CANDIDATE_ID = "synthetic-candidate-001"
STATE_CREATED = "2026-07-19T06:00:00Z"
COMMON_COMMIT_TIME = "2026-07-19T07:00:00+00:00"
PHASE0_FROZEN_TIME = "2026-07-19T08:00:00Z"
PHASE0_COMMIT_TIME = "2026-07-19T12:30:00+00:00"
IMPLEMENTATION_COMMIT_TIME = "2026-07-19T13:00:00+00:00"
HOLD_START = "2026-07-19T14:00:00Z"
NOTICE_COMMIT_TIME = "2026-07-19T15:00:00+00:00"
NOW = datetime(2026, 7, 19, 16, 0, tzinfo=UTC)


@dataclasses.dataclass(frozen=True)
class SyntheticTournament:
    root: Path
    config: LoadedV2Config
    journal: JournalState
    phase0_bytes: bytes
    legacy_state_bytes: bytes
    notice_bytes: bytes
    implementation_commit: str
    target_path: str
    target_bytes: bytes
    runner_path: str
    runner_bytes: bytes

    @staticmethod
    def clock() -> datetime:
        return NOW


def _json_bytes(value: object) -> bytes:
    return json.dumps(value, allow_nan=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _copy(root: Path, relative: str) -> None:
    source = REPOSITORY / relative
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _git(
    root: Path,
    *arguments: str,
    env: Mapping[str, str] | None = None,
) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        env=None if env is None else {**os.environ, **env},
    )
    if process.returncode:
        raise AssertionError(
            f"git {' '.join(arguments)} failed ({process.returncode}): {process.stderr}"
        )
    return process.stdout.strip()


def _commit(root: Path, message: str, timestamp: str, paths: Sequence[str]) -> str:
    _git(root, "add", "-f", "--", *paths)
    commit_env = {
        "GIT_AUTHOR_DATE": timestamp,
        "GIT_COMMITTER_DATE": timestamp,
    }
    _git(root, "commit", "--no-gpg-sign", "-m", message, env=commit_env)
    return _git(root, "rev-parse", "HEAD")


def _policy(config: LoadedV2Config) -> ResearchPolicy:
    budget = config.raw["research_budget"]
    return ResearchPolicy(
        tournament_id=TOP40_V2_LAYOUT.name,
        team_ids=TEAM_IDS,
        maximum_material_configurations_per_team=int(
            budget["maximum_material_configurations_per_team"]
        ),
        maximum_cpu_hours_per_team=float(budget["maximum_cpu_hours_per_team"]),
        maximum_wall_clock_hours_per_team=float(budget["maximum_wall_clock_hours_per_team"]),
    )


def _build_tournament(
    root: Path,
    *,
    canonical_manifest: bool = True,
    common_file_mismatch: bool = False,
    phase0_parent_gap: bool = False,
    notice_parent_gap: bool = False,
    notice_legacy_sha256: str | None = None,
    hold_start: str = HOLD_START,
    notice_commit_time: str = NOTICE_COMMIT_TIME,
) -> SyntheticTournament:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-b", TOP40_V2_LAYOUT.branch)
    _git(root, "config", "user.name", "Top40 V2 test organizer")
    _git(root, "config", "user.email", "top40-v2-test@example.invalid")

    for relative in PHASE0_FROZEN_FILES:
        _copy(root, relative)
    manifest_path = "tournament/top40/data_manifest.json"
    manifest = json.loads((REPOSITORY / manifest_path).read_text(encoding="utf-8"))
    manifest_bytes = (
        _json_bytes(manifest)
        if canonical_manifest
        else json.dumps(manifest, allow_nan=False, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    )
    _write(root / manifest_path, manifest_bytes)

    mismatch_path = PHASE0_FROZEN_FILES[0]
    mismatch_bytes = (root / mismatch_path).read_bytes()
    if common_file_mismatch:
        _write(root / mismatch_path, mismatch_bytes + b"\n")
    common_commit = _commit(
        root,
        "Synthetic common Phase-0 freeze",
        COMMON_COMMIT_TIME,
        (*PHASE0_FROZEN_FILES, manifest_path),
    )
    if common_file_mismatch:
        _write(root / mismatch_path, mismatch_bytes)

    if phase0_parent_gap:
        _write(root / "phase0-parent-gap.txt", b"synthetic ancestry gap\n")
        _commit(
            root,
            "Insert invalid Phase-0 parent gap",
            "2026-07-19T07:30:00+00:00",
            ("phase0-parent-gap.txt",),
        )

    config = load_config(root / TOP40_V2_LAYOUT.config_path)
    policy = _policy(config)
    genesis = plan_genesis(timestamp_utc="2026-07-19T10:00:00Z", policy=policy)
    journal_bytes = genesis.replacement_journal_bytes
    ledger_bytes = b""
    registration = build_trial_registration(
        timestamp_utc="2026-07-19T11:00:00Z",
        team_id="team-01",
        family_id="synthetic-family-001",
        candidate_id=CANDIDATE_ID,
        strategy_sha256="1" * 64,
        source_bundle_sha256="2" * 64,
        risk_config_sha256="3" * 64,
        config_sha256=config.sha256,
        parameters={"lookback": 21},
        seed=2026080101,
        thesis="Synthetic candidate with no market-data dependency.",
        falsifier="Reject when the deterministic fixture says so.",
    )
    registration_plan = plan_registration_append(
        journal_bytes,
        registration,
        ledger_bytes,
        policy=policy,
    )
    journal_bytes = registration_plan.replacement_journal_bytes
    assert registration_plan.replacement_team_ledger_bytes is not None
    ledger_bytes = registration_plan.replacement_team_ledger_bytes

    target_path = (
        f"{TOP40_V2_LAYOUT.report_root('team-01')}/development-runs/"
        f"{CANDIDATE_ID}/targets.parquet"
    )
    runner_path = (
        f"{TOP40_V2_LAYOUT.report_root('team-01')}/qualification-attempts/"
        f"{CANDIDATE_ID}.runner-record.json"
    )
    target_bytes = b"date,net_return\n2026-01-01,0.001\n"
    runner_bytes = _json_bytes(
        {
            "candidate_id": CANDIDATE_ID,
            "runner_seed": config.raw["research_budget"]["strategy_seed"],
            "synthetic": True,
        }
    )
    _write(root / target_path, target_bytes)
    _write(root / runner_path, runner_bytes)
    result = build_trial_result(
        timestamp_utc="2026-07-19T12:00:00Z",
        team_id="team-01",
        family_id="synthetic-family-001",
        candidate_id=CANDIDATE_ID,
        registration_sha256=_sha256(registration),
        status="completed",
        failure_reason=None,
        artifact_hashes={
            target_path: _sha256(target_bytes),
            runner_path: _sha256(runner_bytes),
        },
        metrics_summary={"synthetic_only": True},
        cpu_hours=0.25,
        wall_clock_hours=0.5,
    )
    result_plan = plan_result_append(
        journal_bytes,
        result,
        ledger_bytes,
        policy=policy,
    )
    journal_bytes = result_plan.replacement_journal_bytes
    assert result_plan.replacement_team_ledger_bytes is not None
    ledger_bytes = result_plan.replacement_team_ledger_bytes
    journal = validate_journal_bytes(journal_bytes, policy)
    _write(root / TOP40_V2_LAYOUT.organizer_journal_path, journal_bytes)
    ledger_paths = tuple(
        f"{TOP40_V2_LAYOUT.team_root(team_id)}/experiments.jsonl"
        for team_id in TEAM_IDS
    )
    for team_id, ledger_path in zip(TEAM_IDS, ledger_paths, strict=True):
        _write(root / ledger_path, ledger_bytes if team_id == "team-01" else b"")

    frozen_hashes = {
        relative: _sha256((root / relative).read_bytes()) for relative in PHASE0_FROZEN_FILES
    }
    phase0 = {
        "schema_version": 2,
        "frozen_at_utc": PHASE0_FROZEN_TIME,
        "branch": TOP40_V2_LAYOUT.branch,
        "common_freeze_commit": common_commit,
        "config_sha256": config.sha256,
        "shared_snapshot_manifest_path": manifest_path,
        "shared_snapshot_manifest_sha256": _sha256(manifest_bytes),
        "frozen_files": frozen_hashes,
    }
    phase0_bytes = _json_bytes(phase0)
    _write(root / TOP40_V2_LAYOUT.phase0_freeze_path, phase0_bytes)

    state = new_run_state(config, created_at_utc=STATE_CREATED)
    state["phase"] = "research"
    state["phase0"] = {
        "path": TOP40_V2_LAYOUT.phase0_freeze_path,
        "sha256": _sha256(phase0_bytes),
    }
    state["research_journal"] = {
        "path": TOP40_V2_LAYOUT.organizer_journal_path,
        "genesis_sha256": journal.genesis_sha256,
        "head_sha256": journal.head_sha256,
        "record_count": len(journal.records),
    }
    for team in state["teams"].values():
        team["status"] = "researching"
    state["teams"]["team-01"]["trial_count"] = 1
    validate_run_state(state, config)
    legacy_state_bytes = _json_bytes(state)
    _write(root / TOP40_V2_LAYOUT.state_path, legacy_state_bytes)
    _commit(
        root,
        "Record synthetic Phase-0 authority",
        PHASE0_COMMIT_TIME,
        (
            TOP40_V2_LAYOUT.phase0_freeze_path,
            TOP40_V2_LAYOUT.state_path,
            TOP40_V2_LAYOUT.organizer_journal_path,
            target_path,
            runner_path,
            *ledger_paths,
        ),
    )

    for relative in amendment.AMENDMENT_FILE_PATHS:
        _copy(root, relative)
    implementation_commit = _commit(
        root,
        "Add amendment 0001 lifecycle scaffold",
        IMPLEMENTATION_COMMIT_TIME,
        amendment.AMENDMENT_FILE_PATHS,
    )

    if notice_parent_gap:
        _write(root / "notice-parent-gap.txt", b"synthetic notice ancestry gap\n")
        _commit(
            root,
            "Insert invalid notice parent gap",
            "2026-07-19T14:30:00+00:00",
            ("notice-parent-gap.txt",),
        )

    notice = {
        "schema_version": 1,
        "amendment_id": amendment.AMENDMENT_ID,
        "notice_status": "administrative_hold",
        "phase0_freeze_path": TOP40_V2_LAYOUT.phase0_freeze_path,
        "phase0_freeze_sha256": _sha256(phase0_bytes),
        "legacy_state_sha256": notice_legacy_sha256 or _sha256(legacy_state_bytes),
        "research_journal_path": TOP40_V2_LAYOUT.organizer_journal_path,
        "research_journal_head_sha256": journal.head_sha256,
        "research_journal_record_count": len(journal.records),
        "research_journal_latest_timestamp_utc": journal.last_timestamp_utc,
        "hold_started_at_utc": hold_start,
        "hold_reason": "Pause result-bearing work for an organizer-only diagnostic review.",
    }
    notice_bytes = _json_bytes(notice)
    _write(root / amendment.HOLD_NOTICE_PATH, notice_bytes)
    _commit(
        root,
        "Publish organizer-authored amendment hold notice",
        notice_commit_time,
        (amendment.HOLD_NOTICE_PATH,),
    )
    return SyntheticTournament(
        root=root,
        config=config,
        journal=journal,
        phase0_bytes=phase0_bytes,
        legacy_state_bytes=legacy_state_bytes,
        notice_bytes=notice_bytes,
        implementation_commit=implementation_commit,
        target_path=target_path,
        target_bytes=target_bytes,
        runner_path=runner_path,
        runner_bytes=runner_bytes,
    )


@pytest.fixture
def tournament(tmp_path: Path) -> SyntheticTournament:
    return _build_tournament(tmp_path)


def _activate(tournament: SyntheticTournament) -> Mapping[str, object]:
    return amendment.activate_amendment_draft(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )


def _freeze_synthetic_amendment(tournament: SyntheticTournament) -> Mapping[str, object]:
    _activate(tournament)
    _commit(
        tournament.root,
        "Commit synthetic amendment draft",
        "2026-07-19T15:10:00+00:00",
        (
            amendment.AMENDMENT_DRAFT_PATH,
            amendment.AMENDMENT_CHAIN_PATH,
            amendment.ORGANIZER_AUDIT_PATH,
            TOP40_V2_LAYOUT.state_path,
        ),
    )
    material = amendment.integration_review_material(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )
    manifest = material["integration_manifest"]
    assert isinstance(manifest, Mapping)
    review = {
        "schema_version": 1,
        "amendment_id": amendment.AMENDMENT_ID,
        "decision": "approve",
        "decision_scope": material["decision_scope"],
        "decision_data": {
            "reviewed_exact_implementation_bytes": True,
            "reviewed_required_backfills": True,
            "approved_private_numeric_disclosure_boundary": True,
            "approved_hold_toll_and_resume": True,
        },
        "authorized_by": "synthetic test organizer",
        "reviewed_at_utc": "2026-07-19T15:20:00Z",
        "draft_sha256": manifest["draft_sha256"],
        "phase0_freeze_sha256": manifest["phase0_freeze_sha256"],
        "amendment_files": manifest["amendment_files"],
        "integration_manifest_path": amendment.INTEGRATION_MANIFEST_PATH,
        "integration_manifest_sha256": material["integration_manifest_sha256"],
        "required_backfills": material["required_backfills"],
        "score_calculation_implemented": True,
        "notes": "Synthetic review of exact lifecycle and integration bytes.",
    }
    _write(tournament.root / amendment.AMENDMENT_REVIEW_PATH, _json_bytes(review))
    _commit(
        tournament.root,
        "Commit synthetic amendment review",
        "2026-07-19T15:30:00+00:00",
        (amendment.AMENDMENT_REVIEW_PATH,),
    )
    freeze = amendment.freeze_amendment(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )
    _commit(
        tournament.root,
        "Commit synthetic amendment freeze",
        "2026-07-19T16:00:00+00:00",
        (
            amendment.INTEGRATION_MANIFEST_PATH,
            amendment.AMENDMENT_FREEZE_PATH,
            amendment.AMENDMENT_CHAIN_PATH,
            TOP40_V2_LAYOUT.state_path,
        ),
    )
    return freeze


def _state_bytes(tournament: SyntheticTournament) -> bytes:
    return (tournament.root / TOP40_V2_LAYOUT.state_path).read_bytes()


def _state(tournament: SyntheticTournament) -> dict[str, object]:
    return json.loads(_state_bytes(tournament))


def test_legacy_status_runs_full_phase0_verification(tournament: SyntheticTournament) -> None:
    status = amendment.amendment_status(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )
    assert status["state_schema"] == "legacy-v2"
    assert status["lifecycle_status"] == "not_activated"
    assert status["post_draft_operations_enabled"] is False

    frozen_path = tournament.root / PHASE0_FROZEN_FILES[0]
    original = frozen_path.read_bytes()
    frozen_path.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="Phase-0 frozen file changed"):
        amendment.amendment_status(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )
    frozen_path.write_bytes(original)

    _git(tournament.root, "switch", "-c", "wrong-branch")
    with pytest.raises(ValueError, match="current branch must be"):
        amendment.amendment_status(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )
    _git(tournament.root, "switch", TOP40_V2_LAYOUT.branch)


def test_canonical_script_guard_allows_exact_legacy_schema_two(
    tournament: SyntheticTournament,
) -> None:
    process = subprocess.run(
        [
            sys.executable,
            str(tournament.root / TOP40_V2_LAYOUT.orchestrator_script),
            "validate-config",
        ],
        cwd=tournament.root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert process.returncode == 0, process.stderr
    assert json.loads(process.stdout)["valid"] is True


def test_phase0_rejects_common_commit_byte_mismatch(tmp_path: Path) -> None:
    run = _build_tournament(tmp_path, common_file_mismatch=True)
    with pytest.raises(ValueError, match="differs from common commit"):
        amendment.amendment_status(run.root, run.config, clock=run.clock)


def test_phase0_rejects_noncanonical_manifest(tmp_path: Path) -> None:
    run = _build_tournament(tmp_path, canonical_manifest=False)
    with pytest.raises(ValueError, match="manifest is not canonical JSON"):
        amendment.amendment_status(run.root, run.config, clock=run.clock)


def test_phase0_rejects_non_direct_record_parent(tmp_path: Path) -> None:
    run = _build_tournament(tmp_path, phase0_parent_gap=True)
    with pytest.raises(ValueError, match="wrong direct parent"):
        amendment.amendment_status(run.root, run.config, clock=run.clock)


def test_phase0_rejects_modified_record_history(tournament: SyntheticTournament) -> None:
    path = tournament.root / TOP40_V2_LAYOUT.phase0_freeze_path
    phase0 = json.loads(path.read_text(encoding="utf-8"))
    phase0["frozen_at_utc"] = "2026-07-19T08:01:00Z"
    replacement = _json_bytes(phase0)
    path.write_bytes(replacement)
    state_path = tournament.root / TOP40_V2_LAYOUT.state_path
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["phase0"]["sha256"] = _sha256(replacement)
    state_path.write_bytes(_json_bytes(state))
    _commit(
        tournament.root,
        "Illegally revise Phase-0 record",
        "2026-07-19T15:30:00+00:00",
        (TOP40_V2_LAYOUT.phase0_freeze_path, TOP40_V2_LAYOUT.state_path),
    )
    with pytest.raises(ValueError, match="uniquely first-added and never modified"):
        amendment.amendment_status(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )


def test_phase0_rejects_future_commit_chronology(tournament: SyntheticTournament) -> None:
    def early_clock() -> datetime:
        return datetime(2026, 7, 19, 12, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="chronology is invalid or future-dated"):
        amendment.amendment_status(
            tournament.root,
            tournament.config,
            clock=early_clock,
        )


def test_activation_derives_hold_only_from_committed_notice(
    tournament: SyntheticTournament,
) -> None:
    signature = inspect.signature(amendment.activate_amendment_draft)
    assert set(signature.parameters) == {"root", "config", "clock"}
    draft = _activate(tournament)
    state = amendment.read_amended_state(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )
    notice = json.loads(tournament.notice_bytes)
    assert draft["hold_started_at_utc"] == notice["hold_started_at_utc"]
    assert draft["hold_reason"] == notice["hold_reason"]
    assert draft["claims_frozen"] is False
    assert state["schema_version"] == 3
    assert state["administrative_hold"]["active"] is True
    assert state["legacy_state_sha256"] == _sha256(tournament.legacy_state_bytes)
    assert state["legacy_projection_sha256"] == _sha256(tournament.legacy_state_bytes)
    assert (tournament.root / TOP40_V2_LAYOUT.phase0_freeze_path).read_bytes() == (
        tournament.phase0_bytes
    )
    with pytest.raises(ValueError, match="invalid schema"):
        validate_run_state(state, tournament.config)


def test_activation_rejects_notice_authority_and_chronology(tmp_path: Path) -> None:
    wrong_binding = _build_tournament(tmp_path / "wrong-binding", notice_legacy_sha256="f" * 64)
    with pytest.raises(ValueError, match="notice differs from activation baselines"):
        _activate(wrong_binding)

    wrong_parent = _build_tournament(tmp_path / "wrong-parent", notice_parent_gap=True)
    with pytest.raises(ValueError, match="wrong direct parent"):
        _activate(wrong_parent)

    future = _build_tournament(
        tmp_path / "future",
        hold_start="2026-07-19T17:00:00Z",
        notice_commit_time="2026-07-19T18:00:00+00:00",
    )
    with pytest.raises(ValueError, match="cannot be future-dated|cannot be in the future"):
        _activate(future)


def test_activation_rejects_notice_or_implementation_revisions(
    tournament: SyntheticTournament,
) -> None:
    notice_path = tournament.root / amendment.HOLD_NOTICE_PATH
    notice = json.loads(notice_path.read_text(encoding="utf-8"))
    notice["hold_reason"] = "A revised reason is forbidden after first publication."
    notice_path.write_bytes(_json_bytes(notice))
    _commit(
        tournament.root,
        "Illegally revise hold notice",
        "2026-07-19T15:30:00+00:00",
        (amendment.HOLD_NOTICE_PATH,),
    )
    with pytest.raises(ValueError, match="uniquely first-added and never modified"):
        _activate(tournament)


def test_activation_rejects_revised_implementation(tmp_path: Path) -> None:
    run = _build_tournament(tmp_path)
    implementation_path = run.root / amendment.AMENDMENT_ROOT / "AMENDMENT-DRAFT.md"
    implementation_path.write_bytes(implementation_path.read_bytes() + b"\n")
    _commit(
        run.root,
        "Illegally revise amendment implementation",
        "2026-07-19T15:30:00+00:00",
        ((implementation_path.relative_to(run.root).as_posix()),),
    )
    with pytest.raises(ValueError, match="uniquely first-added and never modified"):
        _activate(run)


def test_active_hold_rejects_any_legacy_projection_mutation(
    tournament: SyntheticTournament,
) -> None:
    _activate(tournament)
    state_path = tournament.root / TOP40_V2_LAYOUT.state_path
    state = json.loads(state_path.read_text(encoding="utf-8"))
    state["teams"]["team-02"]["status"] = "pending_phase0"
    projection = amendment._legacy_projection(state)
    changed_sha = _sha256(_json_bytes(projection))
    state["legacy_projection_sha256"] = changed_sha
    state["legacy_state_sha256"] = changed_sha
    state_path.write_bytes(_json_bytes(state))
    with pytest.raises(ValueError, match="notice differs from activation baselines"):
        amendment.read_amended_state(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )


def test_draft_fails_closed_until_reviewed_integration_freeze(
    tournament: SyntheticTournament,
) -> None:
    _activate(tournament)
    tracked = (
        TOP40_V2_LAYOUT.state_path,
        amendment.AMENDMENT_DRAFT_PATH,
        amendment.AMENDMENT_CHAIN_PATH,
        amendment.ORGANIZER_AUDIT_PATH,
    )
    before = {relative: (tournament.root / relative).read_bytes() for relative in tracked}
    with pytest.raises(ValueError):
        amendment.freeze_amendment(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )
    with pytest.raises(ValueError, match="reviewed, hash-bound"):
        amendment.reserve_diagnostic_backfill(
            tournament.root,
            tournament.config,
            diagnostic_id="diagnostic-001",
            team_id="team-01",
            candidate_id=CANDIDATE_ID,
            clock=tournament.clock,
        )
    with pytest.raises(ValueError, match="reviewed, hash-bound"):
        amendment.run_diagnostic_backfill(
            tournament.root,
            tournament.config,
            diagnostic_id="diagnostic-001",
            clock=tournament.clock,
        )
    with pytest.raises(ValueError, match="reviewed, hash-bound"):
        amendment.resume_amendment_hold(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )
    assert {relative: (tournament.root / relative).read_bytes() for relative in tracked} == before
    assert not (tournament.root / amendment.AMENDMENT_FREEZE_PATH).exists()
    assert not (tournament.root / amendment.INTEGRATION_MANIFEST_PATH).exists()


def test_full_freeze_backfill_resume_and_real_amended_legacy_transition(
    tournament: SyntheticTournament,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        amendment,
        "REQUIRED_BACKFILL_CANDIDATES",
        (("team-01", CANDIDATE_ID),),
    )
    freeze = _freeze_synthetic_amendment(tournament)
    assert freeze["score_calculation_implemented"] is True

    # Every direct frozen command is guarded on schema 3, including old output-path and force-reset
    # bypasses that do not read run state themselves.
    legacy_state_before = _state_bytes(tournament)
    legacy = subprocess.run(
        [
            sys.executable,
            str(tournament.root / TOP40_V2_LAYOUT.orchestrator_script),
            "close-qualification",
        ],
        cwd=tournament.root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert legacy.returncode == 2
    assert "direct frozen entrypoint is disabled" in legacy.stderr
    assert _state_bytes(tournament) == legacy_state_before
    output_bypass = subprocess.run(
        [
            sys.executable,
            str(tournament.root / TOP40_V2_LAYOUT.orchestrator_script),
            "validate-config",
            "--json-out",
            str(tournament.root / TOP40_V2_LAYOUT.state_path),
        ],
        cwd=tournament.root,
        check=False,
        capture_output=True,
        text=True,
    )
    assert output_bypass.returncode == 2
    assert "direct frozen entrypoint is disabled" in output_bypass.stderr
    assert _state_bytes(tournament) == legacy_state_before

    diagnostic_id = amendment._required_diagnostic_id("team-01", CANDIDATE_ID)
    reservation = amendment.reserve_diagnostic_backfill(
        tournament.root,
        tournament.config,
        diagnostic_id=diagnostic_id,
        team_id="team-01",
        candidate_id=CANDIDATE_ID,
        clock=tournament.clock,
    )

    def trusted_runner(
        *,
        root: Path,
        reservation: Mapping[str, object],
        private_output_dir: Path,
    ) -> Mapping[str, object]:
        assert root == tournament.root.resolve()
        summary = {
            "schema_version": 1,
            "diagnostic_id": diagnostic_id,
            "reservation_sha256": reservation["record_sha256"],
            "status": "completed",
            "replay": {
                "replay_targets_identical": True,
                "replay_scores_identical": True,
                "canonical_targets_replay_1_exact": True,
                "canonical_targets_replay_2_exact": True,
            },
            "score_ic": {
                "pooled_ic": 0.05,
                "fold_ics": [0.01, 0.02, 0.03, 0.04, -0.01, -0.02],
                "daily_ic_count": 6,
                "fold_daily_ic_counts": [1, 1, 1, 1, 1, 1],
            },
        }
        for name in amendment.REQUIRED_PRIVATE_ARTIFACT_NAMES:
            payload = _json_bytes(summary) if name == "diagnostic-summary.json" else name.encode()
            integrity.atomic_write_bytes(private_output_dir / name, payload, mode=0o600)
        return {
            "status": "completed",
            "failure_reason": None,
            "organizer_cpu_hours": 0.125,
            "organizer_wall_clock_hours": 0.25,
        }

    monkeypatch.setattr(
        score_diagnostics,
        "run_reserved_score_diagnostic",
        trusted_runner,
    )
    result = amendment.run_diagnostic_backfill(
        tournament.root,
        tournament.config,
        diagnostic_id=diagnostic_id,
        clock=tournament.clock,
    )
    assert result["payload"]["reservation_sha256"] == reservation["record_sha256"]
    assert result["payload"]["diagnostic_outcomes"]["score_ic_gate_passed"] is True

    resumed = amendment.resume_amendment_hold(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )
    assert resumed["hold_duration_microseconds"] == 2 * 60 * 60 * 1_000_000
    state = amendment.read_amended_state(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )
    assert state["administrative_hold"]["active"] is False

    family_input = tournament.root / "team02-family.json"
    family = {
        "schema_version": 1,
        "team_id": "team-02",
        "family_id": "synthetic-team02-family-v1",
        "parent_family_id": None,
        "registered_at_utc": "2026-07-19T16:00:00Z",
        "mechanism": "A causal synthetic mechanism used only for adapter integration testing.",
        "economic_thesis": "The synthetic fixture should survive a schema-3 legacy transition.",
        "falsifier": "Reject if the exact state and family-ledger transaction is not atomic.",
        "selection_metric": "Use the only preregistered synthetic cell.",
        "risk_policy_plan": "Apply no material risk overlay in this synthetic test.",
        "expected_regime_roles": {
            "bull": "Synthetic long sleeve role.",
            "bear": "Synthetic short sleeve role.",
            "chop": "Synthetic balanced role.",
            "stress": "Synthetic defensive role.",
            "long_sleeve": "Synthetic long contribution.",
            "short_sleeve": "Synthetic short contribution.",
        },
        "parameter_ranges": {"lookback_days": [7, 14]},
    }
    _write(family_input, _json_bytes(family))

    monkeypatch.setattr(
        amended_orchestrator,
        "read_amended_state",
        lambda root, config: amendment.read_amended_state(
            root, config, clock=tournament.clock
        ),
    )
    monkeypatch.setattr(
        amended_orchestrator,
        "read_amendment_aware_legacy_state",
        lambda root, config, *, operation: amendment.read_amendment_aware_legacy_state(
            root,
            config,
            operation=operation,
            clock=tournament.clock,
        ),
    )

    @contextmanager
    def synthetic_legacy_edit(
        root: Path,
        config: LoadedV2Config,
        *,
        operation: str,
        staged_changes: list[integrity.TransactionChange],
    ) -> Iterator[dict[str, object]]:
        with amendment.amendment_aware_legacy_state_edit(
            root,
            config,
            operation=operation,
            staged_changes=staged_changes,
            clock=tournament.clock,
        ) as projection:
            yield projection

    monkeypatch.setattr(
        amended_orchestrator,
        "amendment_aware_legacy_state_edit",
        synthetic_legacy_edit,
    )
    monkeypatch.chdir(tournament.root)
    assert amended_orchestrator.run(
        ["register-family", "team-02", str(family_input)]
    ) == 0
    capsys.readouterr()
    transitioned = amendment.read_amended_state(
        tournament.root,
        tournament.config,
        clock=tournament.clock,
    )
    assert transitioned["schema_version"] == 3
    assert transitioned["teams"]["team-02"]["family_count"] == 1
    assert transitioned["teams"]["team-02"]["active_family_id"] == family["family_id"]
    family_ledger = tournament.root / TOP40_V2_LAYOUT.team_root("team-02") / "families.jsonl"
    assert json.loads(family_ledger.read_text(encoding="utf-8")) == family


def test_hold_blocks_result_operations_but_allows_reads(
    tournament: SyntheticTournament,
) -> None:
    _activate(tournament)
    state = _state(tournament)
    for operation in amendment.RESULT_BEARING_OPERATIONS:
        with pytest.raises(ValueError, match="administrative hold"):
            amendment.assert_operation_permitted(state, operation)
    for operation in amendment.READ_ONLY_OPERATIONS:
        amendment.assert_operation_permitted(state, operation)


def test_public_reads_take_the_state_lock(
    tournament: SyntheticTournament,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[Path] = []
    original = amendment._state_lock

    @contextmanager
    def counted(root: Path) -> Iterator[None]:
        calls.append(root)
        with original(root):
            yield

    monkeypatch.setattr(amendment, "_state_lock", counted)
    amendment.amendment_status(tournament.root, tournament.config, clock=tournament.clock)
    assert calls == [tournament.root.resolve()]
    _activate(tournament)
    calls.clear()
    amendment.read_amended_state(tournament.root, tournament.config, clock=tournament.clock)
    assert calls == [tournament.root.resolve()]


def test_canonical_development_binding_includes_result_and_runner(
    tournament: SyntheticTournament,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = dataclasses.replace(
        amendment.CURRENT_INTEGRATION_BOUNDARY,
        development_target_filename="targets.parquet",
        required_private_artifact_names=("metrics.json", "returns.csv"),
    )
    monkeypatch.setattr(amendment, "CURRENT_INTEGRATION_BOUNDARY", boundary)
    bindings = amendment._canonical_development_bindings(
        tournament.root,
        tournament.journal,
        "team-01",
        CANDIDATE_ID,
    )
    assert bindings["development_target_path"] == tournament.target_path
    assert bindings["development_target_sha256"] == _sha256(tournament.target_bytes)
    assert bindings["runner_record_path"] == tournament.runner_path
    assert bindings["runner_record_sha256"] == _sha256(tournament.runner_bytes)
    result_record = next(
        record for record in tournament.journal.records if record["event_type"] == "trial_result"
    )
    assert bindings["trial_result_record_sha256"] == result_record["record_sha256"]
    assert "target_path" not in inspect.signature(amendment.reserve_diagnostic_backfill).parameters

    target = tournament.root / tournament.target_path
    target.write_bytes(tournament.target_bytes + b"tamper")
    with pytest.raises(ValueError, match="differs from completed result artifact hashes"):
        amendment._canonical_development_bindings(
            tournament.root,
            tournament.journal,
            "team-01",
            CANDIDATE_ID,
        )


def _reservation_payload(
    tournament: SyntheticTournament,
    *,
    diagnostic_id: str,
) -> dict[str, object]:
    accounting = tournament.journal.teams["team-01"]
    registration = accounting.registrations[CANDIDATE_ID]
    development = amendment._canonical_development_bindings(
        tournament.root,
        tournament.journal,
        "team-01",
        CANDIDATE_ID,
    )
    phase0 = json.loads(tournament.phase0_bytes)
    freeze_sha = "f" * 64
    identity = {
        "diagnostic_kind": amendment.DIAGNOSTIC_KIND,
        "team_id": "team-01",
        "candidate_id": CANDIDATE_ID,
        "amendment_freeze_sha256": freeze_sha,
    }
    return {
        "diagnostic_id": diagnostic_id,
        "diagnostic_kind": amendment.DIAGNOSTIC_KIND,
        "team_id": "team-01",
        "candidate_id": CANDIDATE_ID,
        "candidate_registration_sha256": accounting.registration_sha256[CANDIDATE_ID],
        "strategy_sha256": registration["strategy_sha256"],
        "source_bundle_sha256": registration["source_bundle_sha256"],
        "risk_policy_sha256": registration["risk_config_sha256"],
        "config_sha256": tournament.config.sha256,
        "candidate_seed": registration["seed"],
        "runner_seed": tournament.config.raw["research_budget"]["strategy_seed"],
        "snapshot_manifest_path": phase0["shared_snapshot_manifest_path"],
        "snapshot_manifest_sha256": phase0["shared_snapshot_manifest_sha256"],
        **development,
        "amendment_freeze_sha256": freeze_sha,
        "reservation_key_sha256": _sha256(amendment._canonical_json_bytes(identity)),
        "non_material": True,
        "charges_team_trial_budget": False,
    }


def test_audit_allows_only_one_reservation_per_candidate(
    tournament: SyntheticTournament,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    boundary = dataclasses.replace(
        amendment.CURRENT_INTEGRATION_BOUNDARY,
        development_target_filename="targets.parquet",
        required_private_artifact_names=("metrics.json", "returns.csv"),
    )
    monkeypatch.setattr(amendment, "CURRENT_INTEGRATION_BOUNDARY", boundary)
    _activate(tournament)
    audit_bytes = (tournament.root / amendment.ORGANIZER_AUDIT_PATH).read_bytes()
    first, _state_after_first, _event = amendment._append_audit(
        audit_bytes,
        event_type="diagnostic_backfill_reserved",
        timestamp_utc="2026-07-19T14:10:00Z",
        payload=_reservation_payload(tournament, diagnostic_id="diagnostic-001"),
    )
    with pytest.raises(ValueError, match="reservation is not one-shot"):
        amendment._append_audit(
            first,
            event_type="diagnostic_backfill_reserved",
            timestamp_utc="2026-07-19T14:20:00Z",
            payload=_reservation_payload(tournament, diagnostic_id="diagnostic-002"),
        )


def test_private_artifacts_are_exact_owner_only_git_path_files(
    tournament: SyntheticTournament,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    required = ("metrics.json", "returns.csv")
    directory = integrity.private_artifact_directory(
        tournament.root,
        "team-01",
        "diagnostic-001",
        create=True,
    )
    payloads = {"metrics.json": b"{}\n", "returns.csv": b"date,return\n"}
    for name, payload in payloads.items():
        integrity.atomic_write_bytes(directory / name, payload)
    hashes = {name: _sha256(payload) for name, payload in payloads.items()}
    artifacts = integrity.validate_private_artifacts(
        tournament.root,
        "team-01",
        "diagnostic-001",
        hashes,
        required,
    )
    git_dir = Path(_git(tournament.root, "rev-parse", "--absolute-git-dir")).resolve()
    assert all(artifact.path.is_relative_to(git_dir) for artifact in artifacts)
    assert _git(tournament.root, "status", "--porcelain", "--untracked-files=all") == ""

    integrity.atomic_write_bytes(directory / "extra.txt", b"extra")
    with pytest.raises(ValueError, match="exactly required artifacts"):
        integrity.validate_private_artifacts(
            tournament.root,
            "team-01",
            "diagnostic-001",
            hashes,
            required,
        )
    (directory / "extra.txt").unlink()

    (directory / "metrics.json").chmod(0o644)
    with pytest.raises(ValueError, match="permissions must be 600"):
        integrity.validate_private_artifacts(
            tournament.root,
            "team-01",
            "diagnostic-001",
            hashes,
            required,
        )
    (directory / "metrics.json").chmod(0o600)

    source = directory.parent / "hardlink-source"
    integrity.atomic_write_bytes(source, payloads["metrics.json"])
    (directory / "metrics.json").unlink()
    os.link(source, directory / "metrics.json")
    with pytest.raises(ValueError, match="must not be hard-linked"):
        integrity.validate_private_artifacts(
            tournament.root,
            "team-01",
            "diagnostic-001",
            hashes,
            required,
        )
    (directory / "metrics.json").unlink()
    source.unlink()
    integrity.atomic_write_bytes(directory / "metrics.json", payloads["metrics.json"])

    monkeypatch.setattr(integrity, "MAX_PRIVATE_RESULT_BYTES", 5)
    with pytest.raises(ValueError, match="total size ceiling"):
        integrity.validate_private_artifacts(
            tournament.root,
            "team-01",
            "diagnostic-001",
            hashes,
            required,
        )
    monkeypatch.setattr(integrity, "MAX_PRIVATE_RESULT_BYTES", 64 * 1024 * 1024)
    monkeypatch.setattr(integrity, "MAX_PRIVATE_ARTIFACT_BYTES", 2)
    with pytest.raises(ValueError, match="size ceiling"):
        integrity.validate_private_artifacts(
            tournament.root,
            "team-01",
            "diagnostic-001",
            hashes,
            required,
        )


def test_private_artifact_symlink_is_rejected(tournament: SyntheticTournament) -> None:
    directory = integrity.private_artifact_directory(
        tournament.root,
        "team-01",
        "diagnostic-002",
        create=True,
    )
    source = directory.parent / "source.json"
    integrity.atomic_write_bytes(source, b"{}\n")
    os.symlink(source, directory / "metrics.json")
    with pytest.raises(ValueError, match="missing or unsafe"):
        integrity.validate_private_artifacts(
            tournament.root,
            "team-01",
            "diagnostic-002",
            {"metrics.json": _sha256(b"{}\n")},
            ("metrics.json",),
        )


def test_lifecycle_derives_only_boolean_outcomes_from_exact_private_summary(
    tournament: SyntheticTournament,
) -> None:
    diagnostic_id = "diagnostic-derived-outcomes"
    reservation_sha = "a" * 64
    directory = integrity.private_artifact_directory(
        tournament.root,
        "team-01",
        diagnostic_id,
        create=True,
    )
    summary = {
        "schema_version": 1,
        "diagnostic_id": diagnostic_id,
        "reservation_sha256": reservation_sha,
        "status": "completed",
        "replay": {
            "replay_targets_identical": True,
            "replay_scores_identical": True,
            "canonical_targets_replay_1_exact": True,
            "canonical_targets_replay_2_exact": True,
        },
        "score_ic": {
            "pooled_ic": 0.02,
            "fold_ics": [0.01, 0.02, -0.01, 0.03, 0.04, None],
            "daily_ic_count": 18,
            "fold_daily_ic_counts": [3, 4, 4, 3, 4, 0],
        },
    }
    for name in amendment.REQUIRED_PRIVATE_ARTIFACT_NAMES:
        payload = _json_bytes(summary) if name == "diagnostic-summary.json" else name.encode()
        path = directory / name
        path.write_bytes(payload)
        path.chmod(0o600)
    hashes, outcomes = amendment._completed_diagnostic_evidence(
        tournament.root,
        {
            "record_sha256": reservation_sha,
            "payload": {"team_id": "team-01", "diagnostic_id": diagnostic_id},
        },
    )
    assert set(hashes) == set(amendment.REQUIRED_PRIVATE_ARTIFACT_NAMES)
    assert outcomes == {
        "canonical_targets_exact": True,
        "deterministic_replays_passed": True,
        "four_of_six_fold_ics_positive": True,
        "pooled_ic_positive": True,
        "score_ic_gate_passed": True,
    }


def test_read_rejects_symlinked_chain(tournament: SyntheticTournament) -> None:
    _activate(tournament)
    chain_path = tournament.root / amendment.AMENDMENT_CHAIN_PATH
    external = tournament.root / "external-chain.jsonl"
    external.write_bytes(chain_path.read_bytes())
    chain_path.unlink()
    os.symlink(external, chain_path)
    with pytest.raises(ValueError, match="missing or unsafe"):
        amendment.read_amended_state(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )


def test_amended_read_rejects_divergent_team_trial_ledger(
    tournament: SyntheticTournament,
) -> None:
    _activate(tournament)
    ledger = (
        tournament.root
        / TOP40_V2_LAYOUT.team_root("team-01")
        / "experiments.jsonl"
    )
    ledger.write_bytes(ledger.read_bytes() + b"{}\n")
    with pytest.raises(ValueError, match="ledger diverges"):
        amendment.read_amended_state(
            tournament.root,
            tournament.config,
            clock=tournament.clock,
        )


def test_current_research_journal_must_extend_exact_hold_baseline(
    tournament: SyntheticTournament,
) -> None:
    baseline = {
        "path": TOP40_V2_LAYOUT.organizer_journal_path,
        "genesis_sha256": tournament.journal.genesis_sha256,
        "head_sha256": tournament.journal.head_sha256,
        "record_count": len(tournament.journal.records),
        "latest_timestamp_utc": tournament.journal.last_timestamp_utc,
    }
    amendment._validate_baseline_research_prefix(tournament.journal, baseline)
    divergent = dataclasses.replace(tournament.journal, genesis_sha256="f" * 64)
    with pytest.raises(ValueError, match="exact extension"):
        amendment._validate_baseline_research_prefix(divergent, baseline)


def test_legacy_staging_rejects_team_source_mutation(
    tournament: SyntheticTournament,
) -> None:
    source = tournament.root / TOP40_V2_LAYOUT.team_root("team-01") / "strategy.py"
    with pytest.raises(ValueError, match="protected or outside outputs"):
        amendment._validate_staged_legacy_changes(
            tournament.root,
            [integrity.TransactionChange(source, None, b"malicious replacement\n")],
        )


def test_chain_records_bind_the_explicit_parent(tournament: SyntheticTournament) -> None:
    _activate(tournament)
    chain_bytes = (tournament.root / amendment.AMENDMENT_CHAIN_PATH).read_bytes()
    chain = amendment.validate_amendment_chain_bytes(chain_bytes)
    replacement, extended, event = amendment._append_chain(
        chain_bytes,
        event_type="amendment_frozen",
        timestamp_utc="2026-07-19T15:30:00Z",
        payload={
            "draft_sha256": _sha256(
                (tournament.root / amendment.AMENDMENT_DRAFT_PATH).read_bytes()
            ),
            "freeze_path": amendment.AMENDMENT_FREEZE_PATH,
            "freeze_sha256": "f" * 64,
            "amendment_commit": tournament.implementation_commit,
            "review_sha256": "e" * 64,
            "integration_manifest_sha256": "d" * 64,
            "score_calculation_implemented": True,
        },
    )
    assert event["previous_record_sha256"] == chain.head_sha256
    assert extended.records[-1]["previous_record_sha256"] == chain.head_sha256
    lines = replacement.splitlines()
    tampered = json.loads(lines[-1])
    tampered["previous_record_sha256"] = "0" * 64
    tampered["record_sha256"] = amendment._record_sha256(tampered)
    lines[-1] = amendment._canonical_json_bytes(tampered)
    with pytest.raises(ValueError, match="envelope is invalid"):
        amendment.validate_amendment_chain_bytes(b"\n".join(lines) + b"\n")


def test_public_read_recovers_partially_published_wal(
    tournament: SyntheticTournament,
) -> None:
    existing = tournament.root / "wal-existing.txt"
    missing = tournament.root / "wal-new.txt"
    existing.write_bytes(b"before")
    changes = (
        integrity.TransactionChange(existing, b"before", b"after"),
        integrity.TransactionChange(missing, None, b"new"),
    )
    intent = integrity.prepare_transaction_intent(tournament.root, changes)
    integrity.atomic_write_bytes(existing, b"after")
    assert intent.exists()
    amendment.amendment_status(tournament.root, tournament.config, clock=tournament.clock)
    assert existing.read_bytes() == b"before"
    assert not missing.exists()
    assert not intent.exists()


def test_transaction_exception_rolls_back_all_outputs(
    tournament: SyntheticTournament,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    existing = tournament.root / "publish-existing.txt"
    missing = tournament.root / "publish-new.txt"
    existing.write_bytes(b"before")
    changes = (
        integrity.TransactionChange(existing, b"before", b"after"),
        integrity.TransactionChange(missing, None, b"new"),
    )
    original = integrity.atomic_write_bytes

    def fail_second(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
        if path == missing and payload == b"new":
            raise OSError("synthetic second-output crash")
        original(path, payload, mode=mode)

    monkeypatch.setattr(integrity, "atomic_write_bytes", fail_second)
    with pytest.raises(OSError, match="second-output crash"):
        integrity.publish_transaction(tournament.root, changes)
    assert existing.read_bytes() == b"before"
    assert not missing.exists()
    assert not integrity.git_path(tournament.root, integrity.TRANSACTION_WAL_GIT_PATH).exists()


def test_transaction_fsyncs_outputs_and_intent_directory(
    tournament: SyntheticTournament,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target = tournament.root / "fsync-target.txt"
    calls: list[Path] = []
    original = integrity.fsync_directory

    def counted(path: Path) -> None:
        calls.append(path)
        original(path)

    monkeypatch.setattr(integrity, "fsync_directory", counted)
    integrity.publish_transaction(
        tournament.root,
        (integrity.TransactionChange(target, None, b"durable"),),
    )
    intent_parent = integrity.git_path(
        tournament.root,
        integrity.TRANSACTION_WAL_GIT_PATH,
    ).parent
    assert target.read_bytes() == b"durable"
    assert target.parent in calls
    assert intent_parent in calls


def test_transaction_recovery_rejects_divergent_output(
    tournament: SyntheticTournament,
) -> None:
    target = tournament.root / "divergent.txt"
    target.write_bytes(b"before")
    changes = (integrity.TransactionChange(target, b"before", b"after"),)
    intent = integrity.prepare_transaction_intent(tournament.root, changes)
    integrity.atomic_write_bytes(target, b"neither")
    with pytest.raises(ValueError, match="divergent amendment transaction output"):
        integrity.recover_transaction(tournament.root)
    assert intent.exists()


def test_transaction_rejects_symlink_output(tournament: SyntheticTournament) -> None:
    target = tournament.root / "transaction-real.txt"
    link = tournament.root / "transaction-link.txt"
    target.write_bytes(b"before")
    os.symlink(target, link)
    with pytest.raises(ValueError, match="regular, single-link file"):
        integrity.prepare_transaction_intent(
            tournament.root,
            (integrity.TransactionChange(link, b"before", b"after"),),
        )


@pytest.mark.parametrize(
    ("value", "lower", "message"),
    (
        ("2026-07-19T13:59:59Z", HOLD_START, "cannot precede"),
        ("2026-07-19T16:00:01Z", HOLD_START, "cannot be in the future"),
    ),
)
def test_bounded_timestamp_rejects_backdating_and_future(
    value: str,
    lower: str,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        integrity.bounded_event_time(
            value,
            "test event",
            lower_bounds=(("lower authority", lower),),
            clock=SyntheticTournament.clock,
        )


def test_cli_and_schemas_expose_only_trusted_lifecycle_inputs(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    script = REPOSITORY / "scripts/top40_v2_amendment_0001.py"
    spec = importlib.util.spec_from_file_location("top40_v2_amendment_cli_test", script)
    assert spec is not None and spec.loader is not None
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    parser = cli.build_parser()
    assert parser.parse_args(["draft-amendment"]).command == "draft-amendment"
    assert parser.parse_args(["freeze-amendment"]).command == "freeze-amendment"
    assert parser.parse_args(
        ["run-diagnostic-backfill", "score-ic-team-01-rdf-ref-001"]
    ).command == "run-diagnostic-backfill"
    for forbidden in (
        ["draft-amendment", "--hold-reason", "caller supplied"],
        ["draft-amendment", "--started-at-utc", HOLD_START],
        ["status", "--json-out", "status.json"],
        ["resume-amendment", "--resumed-at-utc", HOLD_START],
        ["reserve-diagnostic-backfill", "request.json", "--reserved-at-utc", HOLD_START],
        ["record-diagnostic-backfill", "caller-result.json"],
    ):
        with pytest.raises(SystemExit):
            parser.parse_args(forbidden)
    cli._emit({"stdout_only": True})
    assert json.loads(capsys.readouterr().out) == {"stdout_only": True}
    invalid_request = tmp_path / "numeric-reservation.json"
    invalid_request.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "diagnostic_id": 7,
                "team_id": "team-01",
                "candidate_id": 9,
            }
        ),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="identifiers must be strings"):
        cli._reservation_input(str(invalid_request))

    template_root = REPOSITORY / amendment.AMENDMENT_ROOT / "templates"
    schemas = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(template_root.glob("*.schema.json"))
    }
    assert set(schemas) == {
        "amendment-review.schema.json",
        "hold-notice.schema.json",
        "integration-manifest.schema.json",
        "diagnostic-backfill-reservation.schema.json",
        "diagnostic-backfill-result.schema.json",
    }
    assert all(schema["additionalProperties"] is False for schema in schemas.values())
    reservation = schemas["diagnostic-backfill-reservation.schema.json"]
    assert "target_path" not in reservation["properties"]
    result = schemas["diagnostic-backfill-result.schema.json"]
    assert "score" not in result["properties"]
    assert "diagnostic_outcomes" in result["properties"]
    assert "schema_version" not in result["properties"]
    integration = schemas["integration-manifest.schema.json"]
    assert integration["properties"]["score_calculation_implemented"]["const"] is True
    assert (
        integration["properties"]["diagnostic_engine"]["properties"]
        ["development_target_filename"]["const"]
        == "targets.parquet"
    )
    integration_files = set(
        integration["$defs"]["amendment_files"]["propertyNames"]["enum"]
    )
    diagnostic_files = set(
        integration["properties"]["diagnostic_engine"]["properties"]["files"]
        ["propertyNames"]["enum"]
    )
    orchestrator_files = set(
        integration["properties"]["amended_orchestrator"]["properties"]["files"]
        ["propertyNames"]["enum"]
    )
    assert integration_files == set(amendment.AMENDMENT_FILE_PATHS)
    assert diagnostic_files == set(amendment.DIAGNOSTIC_ENGINE_FILE_PATHS)
    assert orchestrator_files == set(amendment.AMENDED_ORCHESTRATOR_FILE_PATHS)
    assert integration["properties"]["required_backfills"]["items"] is False
    review_paths = set(
        review_path
        for review_path in schemas["amendment-review.schema.json"]["$defs"]["amendment_files"][
            "required"
        ]
    )
    assert review_paths == set(amendment.AMENDMENT_FILE_PATHS)
    assert amendment.CURRENT_INTEGRATION_BOUNDARY.edit_adapter_api == (
        "amendment_aware_legacy_state_edit"
    )
    assert amendment.CURRENT_INTEGRATION_BOUNDARY.read_adapter_api == (
        "read_amendment_aware_legacy_state"
    )
    assert not (REPOSITORY / amendment.HOLD_NOTICE_PATH).exists()


def test_docs_bind_trusted_scoring_and_post_resume_orchestration() -> None:
    draft_doc = (REPOSITORY / amendment.AMENDMENT_ROOT / "AMENDMENT-DRAFT.md").read_text(
        encoding="utf-8"
    )
    assert "IMPLEMENTED — HOLD NOTICE AND ORGANIZER REVIEW STILL REQUIRED" in draft_doc
    assert "run-diagnostic-backfill" in draft_doc
    assert "amendment_aware_legacy_state_edit" in draft_doc
    assert "authorized_by" in draft_doc
    assert amendment.DEVELOPMENT_TARGET_FILENAME == "targets.parquet"
