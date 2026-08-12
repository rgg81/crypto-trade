from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from crypto_trade.tournament import journal_v3, phase0_v3
from crypto_trade.tournament import orchestrator_v3 as organizer
from crypto_trade.tournament.qualification_v3 import CandidateIdentity
from crypto_trade.tournament.top40_v3 import LoadedV3Config


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _config(root: Path) -> LoadedV3Config:
    path = root / organizer.CONFIG_PATH
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture activated config\n")
    return LoadedV3Config(
        path=path,
        sha256=_sha256(path.read_bytes()),
        raw={
            "labs": {"strategy_seed": 20260718},
            "universe": {
                "a6_authority": {
                    "audit_report_sha256": "9" * 64,
                    "data_manifest_sha256": "8" * 64,
                }
            },
            "validation": {
                "maximum_opening_probes_per_team": 3,
                "maximum_comeback_probes_per_eligible_team": 2,
                "maximum_total_probes_when_comeback_triggers": 5,
            },
        },
    )


def _phase0(digit: str = "1") -> phase0_v3.Phase0Authority:
    return phase0_v3.Phase0Authority(
        record_sha256=digit * 64,
        chain_head_sha256="2" * 64,
        scope_head_sha256="3" * 64,
        scope_file_count=40,
    )


def _candidate(**changes: object) -> organizer.CandidateAuthority:
    values: dict[str, object] = {
        "team_id": "team-01",
        "entrypoint": "tournament/top40-v3/teams/team-01/strategy.py",
        "candidate_id": "candidate-001",
        "parent_candidate_id": None,
        "purpose": "fixture train laboratory",
        "material_parameters": {"lookback_days": 20},
        "seed": 20260718,
        "candidate_config_path": (
            "tournament/top40-v3/teams/team-01/frozen_config.json"
        ),
        "risk_policy_path": "tournament/top40-v3/teams/team-01/risk_policy.json",
        "candidate_config_sha256": "0" * 64,
        "tournament_config_sha256": "4" * 64,
        "source_bundle_sha256": "5" * 64,
        "source_archive_path": (
            "reports-top40-v3/source-archives/sha256/" + "c" * 64 + ".json"
        ),
        "source_archive_sha256": "c" * 64,
        "strategy_sha256": "6" * 64,
        "dependency_lock_sha256": "7" * 64,
        "risk_policy_sha256": "a" * 64,
        "data_authority_sha256": "8" * 64,
        "evaluator_sha256": "b" * 64,
        "pure_crypto_report_sha256": "9" * 64,
    }
    values.update(changes)
    return organizer.CandidateAuthority(**values)


def _journal_root(root: Path) -> None:
    journal_path = root / organizer.LAB_JOURNAL_PATH
    journal_path.parent.mkdir(parents=True, exist_ok=True)
    journal_path.write_bytes(b"")


def _patch_train_authorities(
    monkeypatch: pytest.MonkeyPatch,
    root: Path,
    candidate: organizer.CandidateAuthority,
    *,
    coach_events: list[str] | None = None,
) -> LoadedV3Config:
    config = _config(root)
    _journal_root(root)
    monkeypatch.setattr(organizer, "_load_active_config", lambda _root: config)
    monkeypatch.setattr(organizer, "_phase0_authority", lambda _root: _phase0())
    monkeypatch.setattr(
        organizer,
        "_reconcile_state",
        lambda *_args, **_kwargs: {"phase": "lab_open"},
    )
    monkeypatch.setattr(
        organizer,
        "_derive_candidate_authority",
        lambda *_args, **_kwargs: candidate,
    )

    def build_packet(_result: object, identity: CandidateIdentity) -> dict[str, object]:
        if coach_events is not None:
            coach_events.append("coach")
        assert type(identity) is CandidateIdentity
        assert identity.candidate_id == candidate.candidate_id
        return {
            "schema_version": "fixture-coaching-v1",
            "stage": "train",
            "training_assessment": {"status": "GREEN"},
        }

    monkeypatch.setattr(organizer.coaching_v3, "build_training_metric_packet", build_packet)
    monkeypatch.setattr(
        organizer.coaching_v3,
        "canonical_packet_bytes",
        lambda packet: organizer._canonical_json_bytes(packet),
    )
    monkeypatch.setattr(
        organizer.coaching_v3,
        "packet_sha256",
        lambda packet: _sha256(organizer._canonical_json_bytes(packet)),
    )
    return config


def _runner_result(
    root: Path,
    candidate: organizer.CandidateAuthority,
    output_path: str,
) -> SimpleNamespace:
    artifact_path = f"{output_path}/daily_returns.csv"
    artifact = root / artifact_path
    artifact.parent.mkdir(parents=True)
    artifact.write_bytes(b"date,net_return\n2020-02-03,0.01\n")
    digest = _sha256(artifact.read_bytes())
    return SimpleNamespace(
        stage="train",
        team_id=candidate.team_id,
        entrypoint=candidate.entrypoint,
        seed=candidate.seed,
        data_manifest_sha256=candidate.data_authority_sha256,
        config_sha256=candidate.tournament_config_sha256,
        strategy_sha256=candidate.strategy_sha256,
        risk_policy_sha256=candidate.risk_policy_sha256,
        source_bundle_sha256=candidate.source_bundle_sha256,
        dependency_lock_sha256=candidate.dependency_lock_sha256,
        evaluator_sha256=candidate.evaluator_sha256,
        pure_crypto_report_sha256=candidate.pure_crypto_report_sha256,
        output_dir=output_path,
        artifacts={"daily_returns": artifact_path},
        artifact_sha256={"daily_returns": digest},
        artifact_sizes={"daily_returns": artifact.stat().st_size},
        scored_window=SimpleNamespace(
            metrics=SimpleNamespace(net_sharpe=1.0, annualized_return=0.2)
        ),
        double_cost_sharpe=0.6,
        organizer_fields=lambda: {"fixture_runner_result": True},
    )


def test_phase0_runs_tests_before_freeze_and_writes_fresh_authorities(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    (root / "tournament/top40-v3").mkdir(parents=True)
    config = _config(root)
    events: list[str] = []
    entries = ({"entry_sha256": "a" * 64},)
    monkeypatch.setattr(organizer, "_load_active_config", lambda _root: config)
    monkeypatch.setattr(phase0_v3, "build_scope_entries", lambda _root: entries)

    def targeted(_root: Path) -> tuple[int, bytes]:
        assert not (root / phase0_v3.PHASE0_RECORD_PATH).exists()
        events.append("tests")
        return 12, b"12 passed in 0.10s\n"

    monkeypatch.setattr(organizer, "_run_targeted_tests", targeted)
    monkeypatch.setattr(
        organizer.pure_crypto_universe_v6,
        "audit_report_bytes",
        lambda _root: b"{}\n",
    )
    monkeypatch.setattr(phase0_v3, "create_targeted_test_evidence", lambda **_kwargs: {})
    monkeypatch.setattr(
        phase0_v3,
        "create_phase0_record",
        lambda *_args, **_kwargs: {"record_sha256": "b" * 64},
    )

    def write_record(_root: Path, _record: object) -> Path:
        events.append("record")
        path = root / phase0_v3.PHASE0_RECORD_PATH
        path.write_bytes(phase0_v3.pretty_json_bytes(_record))
        return path

    monkeypatch.setattr(phase0_v3, "write_phase0_record", write_record)
    monkeypatch.setattr(
        organizer,
        "_project_state",
        lambda *_args, **_kwargs: {"phase": "lab_open"},
    )

    result = organizer.phase0_freeze(root)

    assert events == ["tests", "record"]
    assert result["phase"] == "lab_open"
    assert (root / organizer.PHASE0_TEST_OUTPUT_PATH).read_bytes().startswith(b"12 passed")
    assert (root / organizer.LAB_JOURNAL_PATH).read_bytes() == b""
    assert (root / organizer.RUN_STATE_PATH).exists()


def test_phase0_partial_failure_rolls_back_only_new_authority_files(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    (root / "tournament/top40-v3").mkdir(parents=True)
    config = _config(root)
    monkeypatch.setattr(organizer, "_load_active_config", lambda _root: config)
    monkeypatch.setattr(
        phase0_v3,
        "build_scope_entries",
        lambda _root: ({"entry_sha256": "a" * 64},),
    )
    monkeypatch.setattr(
        organizer,
        "_run_targeted_tests",
        lambda _root: (12, b"12 passed in 0.10s\n"),
    )
    monkeypatch.setattr(
        organizer.pure_crypto_universe_v6,
        "audit_report_bytes",
        lambda _root: b"{}\n",
    )
    monkeypatch.setattr(phase0_v3, "create_targeted_test_evidence", lambda **_kwargs: {})
    monkeypatch.setattr(
        phase0_v3,
        "create_phase0_record",
        lambda *_args, **_kwargs: {"record_sha256": "b" * 64},
    )

    def write_record(_root: Path, _record: object) -> Path:
        path = root / phase0_v3.PHASE0_RECORD_PATH
        path.write_bytes(phase0_v3.pretty_json_bytes(_record))
        return path

    monkeypatch.setattr(phase0_v3, "write_phase0_record", write_record)
    monkeypatch.setattr(
        organizer,
        "_project_state",
        lambda *_args, **_kwargs: {"phase": "lab_open"},
    )
    original_write = organizer._write_new_file

    def fail_state(
        root_path: Path,
        relative: str,
        payload: bytes,
        *,
        mode: int,
    ) -> Path:
        if relative == organizer.RUN_STATE_PATH:
            raise OSError("simulated state persistence failure")
        return original_write(root_path, relative, payload, mode=mode)

    monkeypatch.setattr(organizer, "_write_new_file", fail_state)

    with pytest.raises(organizer.OrchestratorError, match="transaction failed"):
        organizer.phase0_freeze(root)
    for relative in (
        phase0_v3.PHASE0_RECORD_PATH,
        organizer.PHASE0_TEST_OUTPUT_PATH,
        organizer.LAB_JOURNAL_PATH,
        organizer.RUN_STATE_PATH,
    ):
        assert not (root / relative).exists()


def test_verified_uncommitted_phase0_prefix_is_cleaned_for_reboot_retry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    (root / "tournament/top40-v3").mkdir(parents=True)
    config = _config(root)
    (root / organizer.DIAGNOSTIC_RUBRIC_PATH).write_bytes(b"fixture rubric\n")
    output = b"12 passed in 0.10s\n"
    record = {"record_sha256": "b" * 64}
    record_file_sha256 = _sha256(phase0_v3.pretty_json_bytes(record))
    empty = journal_v3.replay_journal_bytes(b"")
    state = organizer._project_state(
        root,
        config,
        empty,
        created_at_utc="2026-07-18T12:00:00Z",
        lock_hash_overrides={"infrastructure": record_file_sha256},
    )
    (root / organizer.PHASE0_TEST_OUTPUT_PATH).write_bytes(output)
    (root / organizer.LAB_JOURNAL_PATH).write_bytes(b"")
    (root / organizer.RUN_STATE_PATH).write_bytes(organizer._pretty_json_bytes(state))
    monkeypatch.setattr(
        phase0_v3,
        "build_scope_entries",
        lambda _root: ({"entry_sha256": "a" * 64},),
    )
    monkeypatch.setattr(phase0_v3, "create_targeted_test_evidence", lambda **_kwargs: {})
    monkeypatch.setattr(
        organizer.pure_crypto_universe_v6,
        "audit_report_bytes",
        lambda _root: b"{}\n",
    )
    monkeypatch.setattr(
        phase0_v3,
        "create_phase0_record",
        lambda *_args, **_kwargs: record,
    )

    organizer._cleanup_uncommitted_phase0_prefix(root, config)

    for relative in (
        organizer.PHASE0_TEST_OUTPUT_PATH,
        organizer.LAB_JOURNAL_PATH,
        organizer.RUN_STATE_PATH,
    ):
        assert not (root / relative).exists()


@pytest.mark.parametrize(
    "prefix",
    [
        (organizer.PHASE0_TEST_OUTPUT_PATH,),
        (organizer.PHASE0_TEST_OUTPUT_PATH, organizer.LAB_JOURNAL_PATH),
    ],
)
def test_verified_short_uncommitted_phase0_prefix_is_cleaned_for_reboot_retry(
    tmp_path: Path,
    prefix: tuple[str, ...],
) -> None:
    root = tmp_path / "repo"
    (root / "tournament/top40-v3").mkdir(parents=True)
    payloads = {
        organizer.PHASE0_TEST_OUTPUT_PATH: b"12 passed in 0.10s\n",
        organizer.LAB_JOURNAL_PATH: b"",
    }
    for relative in prefix:
        (root / relative).write_bytes(payloads[relative])

    organizer._cleanup_uncommitted_phase0_prefix(root, _config(root))

    for relative in prefix:
        assert not (root / relative).exists()


@pytest.mark.parametrize(
    "present",
    [
        (organizer.LAB_JOURNAL_PATH,),
        (organizer.RUN_STATE_PATH,),
        (organizer.PHASE0_TEST_OUTPUT_PATH, organizer.RUN_STATE_PATH),
        (organizer.LAB_JOURNAL_PATH, organizer.RUN_STATE_PATH),
    ],
)
def test_non_prefix_uncommitted_phase0_files_require_review(
    tmp_path: Path,
    present: tuple[str, ...],
) -> None:
    root = tmp_path / "repo"
    (root / "tournament/top40-v3").mkdir(parents=True)
    for relative in present:
        (root / relative).write_bytes(b"fixture")

    with pytest.raises(organizer.OrchestratorError, match="non-prefix"):
        organizer._cleanup_uncommitted_phase0_prefix(root, _config(root))

    for relative in present:
        assert (root / relative).read_bytes() == b"fixture"


def test_targeted_test_command_is_exact_sequential_and_parses_passed_count(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, ...]] = []

    def run(command: object, **kwargs: object) -> SimpleNamespace:
        calls.append((command, kwargs))
        return SimpleNamespace(returncode=0, stdout=b"37 passed, 1 warning in 1.25s\n")

    monkeypatch.setattr(organizer.subprocess, "run", run)
    count, output = organizer._run_targeted_tests(tmp_path)

    assert count == 37
    assert output.startswith(b"37 passed")
    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command == list(phase0_v3.TARGETED_TEST_COMMAND)
    assert kwargs["cwd"] == tmp_path
    assert kwargs["stderr"] is organizer.subprocess.STDOUT


def test_train_journals_request_before_runner_and_terminal_before_disclosure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    candidate = _candidate()
    events: list[str] = []
    _patch_train_authorities(monkeypatch, root, candidate, coach_events=events)

    def run(root_path: Path, selected: object, output_path: str) -> SimpleNamespace:
        replay = journal_v3.replay_journal(root / organizer.LAB_JOURNAL_PATH)
        assert len(replay.pending_request_sha256s) == 1
        events.append("runner")
        return _runner_result(root_path, selected, output_path)

    monkeypatch.setattr(organizer, "_run_trusted_train", run)
    original_terminal = organizer._append_terminal

    def terminal(*args: object, **kwargs: object) -> journal_v3.JournalState:
        events.append("terminal")
        return original_terminal(*args, **kwargs)

    monkeypatch.setattr(organizer, "_append_terminal", terminal)

    response = organizer.train(root, candidate.team_id, candidate.entrypoint)

    replay = journal_v3.replay_journal(root / organizer.LAB_JOURNAL_PATH)
    assert [record["event_type"] for record in replay.records] == [
        "request_accepted",
        "succeeded",
    ]
    assert events == ["runner", "coach", "terminal"]
    assert replay.pending_request_sha256s == ()
    assert response["metric_packet"]["training_assessment"]["status"] == "GREEN"
    metric_path = next(
        path
        for path in replay.records[-1]["artifact_hashes"]
        if path.endswith("metric_packet.json")
    )
    metric_bytes = (root / metric_path).read_bytes()
    assert _sha256(metric_bytes) == replay.records[-1]["metric_packet_sha256"]


def test_train_failure_is_terminally_accounted_without_coaching_disclosure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    candidate = _candidate()
    coach_events: list[str] = []
    _patch_train_authorities(monkeypatch, root, candidate, coach_events=coach_events)
    monkeypatch.setattr(
        organizer,
        "_run_trusted_train",
        lambda *_args: (_ for _ in ()).throw(RuntimeError("strategy exploded")),
    )

    with pytest.raises(organizer.OrchestratorError, match="strategy exploded"):
        organizer.train(root, candidate.team_id, candidate.entrypoint)

    replay = journal_v3.replay_journal(root / organizer.LAB_JOURNAL_PATH)
    assert [record["event_type"] for record in replay.records] == [
        "request_accepted",
        "failed",
    ]
    failure = replay.records[-1]
    assert failure["failure_reason"].endswith("strategy exploded")
    assert failure["cpu_seconds"] >= 0.0
    assert failure["wall_seconds"] >= 0.0
    assert failure["metric_packet_sha256"] is None
    assert coach_events == []


def _request_kwargs(candidate: organizer.CandidateAuthority) -> dict[str, object]:
    return {
        "team_id": candidate.team_id,
        "run_sequence": 1,
        "run_id": "v3-team01-old-run-000001",
        "candidate_id": candidate.candidate_id,
        "parent_candidate_id": candidate.parent_candidate_id,
        "purpose": candidate.purpose,
        "accepted_at_utc": "2026-07-18T12:00:00Z",
        "source_bundle_sha256": candidate.source_bundle_sha256,
        "source_archive_path": candidate.source_archive_path,
        "source_archive_sha256": candidate.source_archive_sha256,
        "strategy_sha256": candidate.strategy_sha256,
        "dependency_lock_sha256": candidate.dependency_lock_sha256,
        "config_sha256": candidate.tournament_config_sha256,
        "risk_policy_sha256": candidate.risk_policy_sha256,
        "data_authority_sha256": candidate.data_authority_sha256,
        "evaluator_sha256": candidate.evaluator_sha256,
        "seed": candidate.seed,
        "material_parameters": dict(candidate.material_parameters),
        "train_window": dict(journal_v3.FROZEN_TRAIN_WINDOW),
        "cost_model": dict(journal_v3.FROZEN_COST_MODEL),
        "output_path": "reports-top40-v3/labs/team-01/v3-team01-old-run-000001",
        "cumulative_material_trial_count": 1,
    }


def test_restart_recovery_aborts_pending_then_uses_new_run_id_and_preserves_orphan(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    candidate = _candidate()
    _patch_train_authorities(monkeypatch, root, candidate)
    journal_v3.append_request_accepted(
        root / organizer.LAB_JOURNAL_PATH,
        **_request_kwargs(candidate),
    )
    orphan = root / "reports-top40-v3/labs/team-01/v3-team01-old-run-000001/orphan.txt"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("preserve for audit\n", encoding="utf-8")
    monkeypatch.setattr(
        organizer,
        "_run_trusted_train",
        lambda root_path, selected, output: _runner_result(root_path, selected, output),
    )

    organizer.train(root, candidate.team_id, candidate.entrypoint)

    replay = journal_v3.replay_journal(root / organizer.LAB_JOURNAL_PATH)
    assert [record["event_type"] for record in replay.records] == [
        "request_accepted",
        "aborted",
        "request_accepted",
        "succeeded",
    ]
    assert "restart recovery" in replay.records[1]["failure_reason"]
    assert "unavailable and recorded as zero" in replay.records[1]["failure_reason"]
    orphan_relative = orphan.relative_to(root).as_posix()
    assert replay.records[1]["artifact_hashes"] == {
        orphan_relative: _sha256(orphan.read_bytes())
    }
    assert replay.records[1]["cpu_seconds"] == 0.0
    assert replay.records[1]["wall_seconds"] == 0.0
    assert replay.records[2]["run_id"] != replay.records[0]["run_id"]
    assert replay.records[2]["run_sequence"] == 2
    assert orphan.read_text(encoding="utf-8") == "preserve for audit\n"


def test_phase0_and_candidate_config_drift_fail_closed_and_are_accounted(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "phase-drift"
    root.mkdir()
    candidate = _candidate()
    _patch_train_authorities(monkeypatch, root, candidate)
    authorities = iter((_phase0("1"), _phase0("f")))
    monkeypatch.setattr(organizer, "_phase0_authority", lambda _root: next(authorities))
    with pytest.raises(organizer.OrchestratorError, match="Phase-0 authority changed"):
        organizer.train(root, candidate.team_id, candidate.entrypoint)
    assert (root / organizer.LAB_JOURNAL_PATH).read_bytes() == b""

    root = tmp_path / "config-drift"
    root.mkdir()
    _patch_train_authorities(monkeypatch, root, candidate)
    changed = dataclasses.replace(candidate, candidate_config_sha256="e" * 64)
    candidates = iter((candidate, changed))
    monkeypatch.setattr(
        organizer,
        "_derive_candidate_authority",
        lambda *_args, **_kwargs: next(candidates),
    )
    monkeypatch.setattr(
        organizer,
        "_run_trusted_train",
        lambda root_path, selected, output: _runner_result(root_path, selected, output),
    )
    with pytest.raises(organizer.OrchestratorError, match="candidate inputs changed"):
        organizer.train(root, candidate.team_id, candidate.entrypoint)
    replay = journal_v3.replay_journal(root / organizer.LAB_JOURNAL_PATH)
    assert replay.records[-1]["event_type"] == "failed"
    assert replay.pending_request_sha256s == ()


def test_incumbent_entrypoint_binds_adjacent_config_and_risk_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "repo"
    root.mkdir()
    config = _config(root)
    manifest = root / organizer.DATA_MANIFEST_PATH
    manifest.parent.mkdir(parents=True)
    manifest.write_bytes(b"fixture manifest\n")
    config.raw["universe"]["a6_authority"]["data_manifest_sha256"] = _sha256(
        manifest.read_bytes()
    )
    (root / organizer.DEPENDENCY_LOCK_PATH).write_bytes(b"fixture lock\n")
    candidate_root = (
        root
        / "tournament/top40-v3/teams/team-04/incumbents/"
        "team-04-utc-reference-001-v3-port"
    )
    candidate_root.mkdir(parents=True)
    entrypoint = candidate_root / "strategy.py"
    entrypoint.write_text("def build_strategy(): ...\n", encoding="utf-8")
    risk = candidate_root / "risk_policy.json"
    risk.write_text('{"policy":"adjacent"}\n', encoding="utf-8")
    frozen = {
        "schema_version": 1,
        "team_id": "team-04",
        "candidate_id": "team-04-utc-reference-001-v3-port",
        "seed": 20260718,
        "implementation": {"entrypoint": "strategy.py"},
        "risk_policy": {"path": "risk_policy.json"},
        "parameters": {"lookback": 42},
        "v2_parent": {"candidate_id": "team-04-utc-reference-001"},
    }
    (candidate_root / "frozen_config.json").write_text(
        json.dumps(frozen),
        encoding="utf-8",
    )
    relative = entrypoint.relative_to(root).as_posix()
    monkeypatch.setattr(
        organizer.runner_v3,
        "_evaluator_authority_sha256",
        lambda _root: "b" * 64,
    )

    authority = organizer._derive_candidate_authority(
        root,
        config,
        "team-04",
        relative,
        "incumbent comparison",
    )

    assert authority.candidate_id == frozen["candidate_id"]
    assert authority.parent_candidate_id == "team-04-utc-reference-001"
    assert authority.source_archive_path.startswith(
        "reports-top40-v3/source-archives/sha256/"
    )
    assert len(authority.source_archive_sha256) == 64
    assert authority.risk_policy_sha256 == _sha256(risk.read_bytes())

    frozen.pop("v2_parent")
    frozen["v3_parent"] = {"candidate_id": "team-04-previous-v3"}
    (candidate_root / "frozen_config.json").write_text(
        json.dumps(frozen), encoding="utf-8"
    )
    v3_child = organizer._derive_candidate_authority(
        root, config, "team-04", relative, "V3 challenger comparison"
    )
    assert v3_child.parent_candidate_id == "team-04-previous-v3"

    capture_source_bundle = organizer.runner_v3.capture_source_bundle
    monkeypatch.setattr(
        organizer.runner_v3,
        "capture_source_bundle",
        lambda *_args: (_ for _ in ()).throw(
            organizer.runner_v3.StrategySandboxError("unsafe candidate byte")
        ),
    )
    with pytest.raises(organizer.OrchestratorError, match="authority derivation failed"):
        organizer._derive_candidate_authority(
            root, config, "team-04", relative, "sandbox normalization"
        )
    monkeypatch.setattr(
        organizer.runner_v3, "capture_source_bundle", capture_source_bundle
    )

    risk.unlink()
    top_level_risk = root / "tournament/top40-v3/teams/team-04/risk_policy.json"
    top_level_risk.parent.mkdir(parents=True, exist_ok=True)
    top_level_risk.write_text('{"policy":"wrong"}\n', encoding="utf-8")
    with pytest.raises(organizer.OrchestratorError, match="required file is missing"):
        organizer._derive_candidate_authority(
            root,
            config,
            "team-04",
            relative,
            "incumbent comparison",
        )


def test_global_lock_and_cli_expose_only_four_unsealed_commands(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "tournament/top40-v3").mkdir(parents=True)
    with organizer._result_command_lock(root):
        with pytest.raises(organizer.ResultCommandBusyError):
            organizer.status(root)

    parser = organizer.build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )
    assert set(subparsers.choices) == {"validate", "phase0-freeze", "status", "train"}
    for forbidden in ("validation", "private", "final", "final-oos"):
        with pytest.raises(SystemExit):
            parser.parse_args([forbidden])


def test_stale_run_state_is_rebuilt_from_canonical_journal_counts(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    (root / "tournament/top40-v3").mkdir(parents=True)
    config = _config(root)
    (root / phase0_v3.PHASE0_RECORD_PATH).write_bytes(b"phase0\n")
    (root / organizer.DIAGNOSTIC_RUBRIC_PATH).write_bytes(b"rubric\n")
    empty = journal_v3.replay_journal_bytes(b"")
    stale = organizer._project_state(
        root,
        config,
        empty,
        created_at_utc="2026-07-18T12:00:00Z",
    )
    state_path = root / organizer.RUN_STATE_PATH
    state_path.write_bytes(organizer._pretty_json_bytes(stale))
    recovered_journal = journal_v3.JournalState(
        records=(),
        head_sha256=journal_v3.GENESIS_SHA256,
        pending_request_sha256s=(),
        terminal_request_sha256s=(),
        team_run_sequences={"team-01": 2},
        material_trial_counts={"team-01": 2},
    )

    projected = organizer._reconcile_state(root, config, recovered_journal)

    assert projected["teams"]["team-01"]["lab_run_count"] == 2
    assert projected["teams"]["team-01"]["material_trial_count"] == 2
    assert json.loads(state_path.read_bytes())["teams"]["team-01"]["lab_run_count"] == 2
