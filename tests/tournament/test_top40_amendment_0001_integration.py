from __future__ import annotations

import argparse
import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import pytest

from crypto_trade.tournament import journal_v3, orchestrator_v3, phase0_v3, runner_v3
from crypto_trade.tournament import top40_amendment_0001 as adapter
from crypto_trade.tournament import top40_amendment_0001_integration as integration

ROOT = Path(__file__).parents[2]


def _authority(*, freeze_sha256: str = "a" * 64) -> integration.IntegrationAuthority:
    return integration.IntegrationAuthority(
        freeze_file_sha256=freeze_sha256,
        freeze_commit="e" * 40,
        record_sha256="b" * 64,
        implementation_commit="c" * 40,
        config_sha256="d" * 64,
        parent_phase0_record_sha256=integration.PARENT_PHASE0_RECORD_SHA256,
        activation_journal_head_sha256=integration.ACTIVATION_JOURNAL_HEAD_SHA256,
    )


def test_activation_sentinel_retires_parent_cli_but_preserves_historical_authority() -> None:
    assert integration.ACTIVATION_SENTINEL_PATH in phase0_v3._discover_repository_scope(ROOT)
    with pytest.raises(orchestrator_v3.OrchestratorError, match="Phase-0 verification failed"):
        orchestrator_v3._phase0_authority(ROOT)

    authority = integration._historical_phase0_authority(ROOT)

    assert authority.record_sha256 == integration.PARENT_PHASE0_RECORD_SHA256
    assert authority.scope_file_count == 54
    assert phase0_v3._discover_repository_scope is integration._FROZEN_DISCOVERY


def test_historical_entrypoint_is_a_tombstone_before_any_journal_access() -> None:
    journal = ROOT / orchestrator_v3.LAB_JOURNAL_PATH
    before = journal.read_bytes()

    completed = subprocess.run(
        [sys.executable, str(ROOT / integration.HISTORICAL_ENTRYPOINT_PATH), "status"],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert b"historical organizer entrypoint is retired" in completed.stderr
    assert journal.read_bytes() == before


def test_incident_prefix_and_evidence_commit_remain_exact() -> None:
    journal = integration._journal_boundary(ROOT, require_exact_boundary=False)
    evidence = integration._historical_evidence(ROOT)

    assert journal["event_sequence"] == 2
    assert journal["head_sha256"] == integration.ACTIVATION_JOURNAL_HEAD_SHA256
    assert evidence["commit"] == integration.HISTORICAL_EVIDENCE_COMMIT
    assert [item["path"] for item in evidence["files"]] == list(
        integration.EVIDENCE_PATHS
    )


def test_journal_boundary_accepts_a_normal_pending_post_activation_request(
    tmp_path: Path,
) -> None:
    journal_path = tmp_path / orchestrator_v3.LAB_JOURNAL_PATH
    journal_path.parent.mkdir(parents=True)
    journal_path.write_bytes((ROOT / orchestrator_v3.LAB_JOURNAL_PATH).read_bytes())
    first = dict(journal_v3.replay_journal(journal_path).records[0])
    request_fields = {
        key: first[key]
        for key in (
            "team_id",
            "parent_candidate_id",
            "purpose",
            "source_bundle_sha256",
            "source_archive_path",
            "source_archive_sha256",
            "strategy_sha256",
            "dependency_lock_sha256",
            "config_sha256",
            "risk_policy_sha256",
            "data_authority_sha256",
            "evaluator_sha256",
            "seed",
            "material_parameters",
            "train_window",
            "cost_model",
        )
    }
    state = journal_v3.append_request_accepted(
        journal_path,
        **request_fields,
        run_sequence=2,
        run_id="v3-team04-lab-000002-pending",
        candidate_id="team-04-utc-reference-001-v3-port",
        accepted_at_utc="2026-07-18T17:00:00Z",
        output_path="reports-top40-v3/labs/team-04/v3-team04-lab-000002-pending",
        cumulative_material_trial_count=2,
    )

    boundary = integration._journal_boundary(tmp_path, require_exact_boundary=False)

    assert boundary["head_sha256"] == integration.ACTIVATION_JOURNAL_HEAD_SHA256
    assert len(state.pending_request_sha256s) == 1
    assert state.team_run_sequences == {"team-04": 2}
    assert state.material_trial_counts == {"team-04": 2}


def test_historical_verifier_rejects_any_second_discovery_delta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frozen = integration._FROZEN_DISCOVERY
    monkeypatch.setattr(
        integration,
        "_FROZEN_DISCOVERY",
        lambda root: (*frozen(root), "tournament/top40-v3/UNAUTHORIZED.md"),
    )

    with pytest.raises(
        integration.Amendment0001IntegrationError,
        match="historical scope plus activation sentinel",
    ):
        integration._historical_phase0_authority(ROOT)


def test_runtime_delta_is_private_transactional_and_restored_on_baseexception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority()
    parent_phase0 = phase0_v3.Phase0Authority(
        record_sha256=integration.PARENT_PHASE0_RECORD_SHA256,
        chain_head_sha256="e" * 64,
        scope_head_sha256="f" * 64,
        scope_file_count=54,
    )
    monkeypatch.setattr(integration, "_VERIFY_INTEGRATION", lambda _root: authority)
    monkeypatch.setattr(
        integration,
        "_HISTORICAL_PHASE0_AUTHORITY",
        lambda _root: parent_phase0,
    )
    monkeypatch.setattr(integration, "_verify_amended_runtime_bindings", lambda: None)

    class DeliberateAbort(BaseException):
        pass

    with pytest.raises(DeliberateAbort):
        with integration._activated_runtime(ROOT) as observed:
            assert observed == authority
            assert orchestrator_v3._phase0_authority is integration._amended_phase0_authority
            assert runner_v3._compute_metrics is adapter.compute_metrics_with_utc_bounds
            assert (
                runner_v3._evaluator_authority_sha256
                is integration.evaluator_authority_sha256
            )
            raise DeliberateAbort

    assert orchestrator_v3._phase0_authority is integration._FROZEN_PHASE0_AUTHORITY
    assert runner_v3._compute_metrics is integration._FROZEN_COMPUTE_METRICS
    assert (
        runner_v3._evaluator_authority_sha256
        is integration._FROZEN_EVALUATOR_AUTHORITY
    )
    assert phase0_v3._discover_repository_scope is integration._FROZEN_DISCOVERY


def test_amended_phase0_authority_rejects_calls_without_private_capability() -> None:
    with pytest.raises(
        integration.Amendment0001IntegrationError,
        match="outside the private integration transaction",
    ):
        integration._amended_phase0_authority(ROOT)


def test_preimport_callable_spoof_is_rejected_by_independent_code_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    code = (lambda: None).__code__.replace(
        co_filename=str(Path(runner_v3.__file__).resolve()),
        co_name="_compute_metrics",
    )
    fake = types.FunctionType(code, {})
    fake.__module__ = runner_v3.__name__
    fake.__name__ = "_compute_metrics"
    monkeypatch.setattr(integration, "_FROZEN_COMPUTE_METRICS", fake)

    with pytest.raises(
        integration.Amendment0001IntegrationError,
        match="frozen callable authority is invalid",
    ):
        integration._verify_frozen_runtime_bindings()


def test_preimport_amended_callable_with_copied_globals_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = integration._AMENDED_COMPUTE_METRICS
    fake = types.FunctionType(
        original.__code__,
        dict(original.__globals__),
        name=original.__name__,
    )
    fake.__module__ = adapter.__name__
    monkeypatch.setattr(integration, "_AMENDED_COMPUTE_METRICS", fake)
    monkeypatch.setattr(adapter, "compute_metrics_with_utc_bounds", fake)

    with pytest.raises(
        integration.Amendment0001IntegrationError,
        match="frozen callable authority is invalid",
    ):
        integration._verify_amended_runtime_bindings()


@pytest.mark.parametrize(
    ("name", "message"),
    (
        ("verify_integration", "amended runtime callable globals or module bindings"),
        ("_verify_freeze_commit", "integration verification helper binding changed"),
    ),
)
def test_security_critical_transitive_global_replacement_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    message: str,
) -> None:
    monkeypatch.setattr(integration, name, lambda *_args, **_kwargs: _authority())

    with pytest.raises(integration.Amendment0001IntegrationError, match=message):
        integration._verify_amended_runtime_bindings()


def test_uncommitted_integration_freeze_cannot_activate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        integration,
        "_git",
        lambda *_args, **_kwargs: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=b"", stderr=b""
        ),
    )

    with pytest.raises(
        integration.Amendment0001IntegrationError,
        match="not active until one unique first-add commit exists",
    ):
        integration._verify_freeze_commit(
            ROOT,
            implementation_commit="1" * 40,
            freeze_bytes=b"provisional\n",
        )


def test_runtime_tampering_is_detected_before_parent_bindings_are_restored(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    authority = _authority()
    parent_phase0 = phase0_v3.Phase0Authority(
        record_sha256=integration.PARENT_PHASE0_RECORD_SHA256,
        chain_head_sha256="e" * 64,
        scope_head_sha256="f" * 64,
        scope_file_count=54,
    )
    monkeypatch.setattr(integration, "_VERIFY_INTEGRATION", lambda _root: authority)
    monkeypatch.setattr(
        integration,
        "_HISTORICAL_PHASE0_AUTHORITY",
        lambda _root: parent_phase0,
    )
    monkeypatch.setattr(integration, "_verify_amended_runtime_bindings", lambda: None)

    def coordinated_replacement(*_args: object, **_kwargs: object) -> dict[object, object]:
        return {}

    try:
        with pytest.raises(
            integration.Amendment0001IntegrationError,
            match="runtime bindings changed during delegated command",
        ):
            with integration._activated_runtime(ROOT):
                adapter.compute_metrics_with_utc_bounds = coordinated_replacement
                runner_v3._compute_metrics = coordinated_replacement
    finally:
        adapter.compute_metrics_with_utc_bounds = integration._AMENDED_COMPUTE_METRICS

    assert orchestrator_v3._phase0_authority is integration._FROZEN_PHASE0_AUTHORITY
    assert runner_v3._compute_metrics is integration._FROZEN_COMPUTE_METRICS
    assert (
        runner_v3._evaluator_authority_sha256
        is integration._FROZEN_EVALUATOR_AUTHORITY
    )


def test_composite_evaluator_identity_binds_the_integration_freeze(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(integration, "_VERIFY_INTEGRATION", lambda _root: _authority())
    monkeypatch.setattr(
        integration,
        "_PARENT_EVALUATOR_AUTHORITY",
        lambda _root: "1" * 64,
    )
    first = integration.evaluator_authority_sha256(ROOT)
    monkeypatch.setattr(
        integration,
        "_VERIFY_INTEGRATION",
        lambda _root: _authority(freeze_sha256="2" * 64),
    )
    second = integration.evaluator_authority_sha256(ROOT)

    assert len(first) == 64
    assert first != second


def test_amendment_cli_has_a_closed_command_surface() -> None:
    path = ROOT / integration.ACTIVE_SCRIPT_PATH
    spec = importlib.util.spec_from_file_location("_top40_v3_a0001_cli_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parser = module.build_parser()
    subparsers = next(
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    )

    assert set(subparsers.choices) == {"freeze", "validate", "status", "train"}
